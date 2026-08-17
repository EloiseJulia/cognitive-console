"""Simulated-novice prompt comparator arm for frozen C2b TEST cells.

Exploratory bridge only: valid_for_paper=false because the human anchor
calibration gate has not passed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cognitive_console.config import config_hash
from cognitive_console.experiments import adjudicate_c2b as adj
from cognitive_console.experiments.adjudicate_c2b import AxisAdjSpec, BackendOutcomeSampler, ProgressTracker, RunContext
from cognitive_console.lineage import git_commit, new_experiment_id, utcnow
from cognitive_console.ops.disk_guard import check_disk_budget, default_guard_paths
from cognitive_console.registry import ExperimentRecord, ExperimentRegistry
from cognitive_console.steering.generate import SyntheticC2bTaskBackend

from scripts import run_c1_facade as c1
from scripts import run_c2b_adjudication as c2b
from scripts import run_gpu_phase0 as p0

DEFAULT_QWEN_MODEL = "Qwen/Qwen2.5-7B-Instruct"
FROZEN_QWEN_REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"


def _rel(path: Path) -> str:
    p = Path(path).resolve()
    try:
        return str(p.relative_to(_REPO)).replace("\\", "/")
    except ValueError:
        return str(p).replace("\\", "/")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def _load_prompt_set(path: Path, axes: List[str]) -> Dict[str, List[tuple[str, str]]]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("valid_for_paper") is not False:
        raise ValueError("novice prompt set must carry valid_for_paper=false")
    out: Dict[str, List[tuple[str, str]]] = {}
    for axis in axes:
        rows = doc.get("axes", {}).get(axis)
        if not isinstance(rows, list) or not rows:
            raise ValueError(f"{path}: missing novice prompts for {axis}")
        out[axis] = [(str(r["prompt_id"]), str(r["text"])) for r in rows]
    return out


def _load_frozen_sources(path: Path) -> Dict[str, Dict[str, object]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    out: Dict[str, Dict[str, object]] = {}
    for row in data.get("axes", []):
        axis = str(row["axis"])
        dev = row.get("dev_selection", {}) or {}
        out[axis] = {
            "frozen_alpha": float(dev["frozen_alpha"]),
            "best_prompt_id": str(dev.get("best_prompt_id")),
            "best_prompt_text": str(dev.get("best_prompt_text")),
            "per_item_steer": [float(x) for x in row["per_item_steer"]],
            "per_item_prompt": [float(x) for x in row["per_item_prompt"]],
            "coherence_ok": bool(row.get("coherence_ok")),
            "test_steer_degeneracy": row.get("test_steer_degeneracy"),
            "test_baseline_degeneracy": row.get("test_baseline_degeneracy"),
            "reference_steer_mean": float(np.mean([float(x) for x in row["per_item_steer"]])),
            "layer": int(row.get("layer", 1)),
            "n_test": int(row.get("n_test", len(row["per_item_steer"]))),
        }
    return out


def _apply_delib512_override(src: Dict[str, object], path: Optional[Path]) -> None:
    if path is None:
        return
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("axis") != "deliberation" or int(doc.get("max_new_tokens")) < 512:
        raise ValueError(f"{path}: not a deliberation 512-token repair artifact")
    src["per_item_steer"] = [float(x) for x in doc["per_item_steer_512"]]
    src["reference_steer_mean"] = float(np.mean(src["per_item_steer"]))
    src["coherence_ok"] = bool(doc.get("coherence", {}).get("coherence_ok"))
    src["test_steer_degeneracy"] = doc.get("coherence", {}).get("test_steer_degeneracy")
    src["test_baseline_degeneracy"] = doc.get("coherence", {}).get("test_baseline_degeneracy")
    src["best_prompt_512"] = [float(x) for x in doc.get("comparators", {}).get("best_prompt_512", [])]
    src["delib512_source"] = str(path)


def _prompt_only_specs(axes: List[str], prompts: Dict[str, List[tuple[str, str]]],
                       n_items: Optional[int], layer_by_axis: Dict[str, int]) -> List[AxisAdjSpec]:
    neutral = c1.load_neutral_prompts()[0]
    specs: List[AxisAdjSpec] = []
    for axis in axes:
        specs.append(AxisAdjSpec(
            axis=axis,
            items=c2b.load_axis_items(axis, False, n_items),
            strong_prompts=prompts[axis],
            neutral_prompt=neutral,
            direction=np.ones(1),
            layer=int(layer_by_axis.get(axis, 1)),
        ))
    return specs


def _hf_prompt_sampler_factory(model: str, revision: Optional[str], max_new_tokens: int,
                               temperature: float, seed: int, batch_size: int,
                               collector: Optional[c2b.TranscriptCollector] = None):
    from cognitive_console.steering.generate import SteeredHFBackend
    device, dtype = p0._pick_device(), p0._pick_dtype()
    backend = SteeredHFBackend(model, device=device, dtype=dtype, seed=seed, revision=revision)

    def factory(axis: str):
        sampler_cls = c2b.TranscriptBackendOutcomeSampler if collector else BackendOutcomeSampler
        kwargs = {"transcript_collector": collector} if collector else {}
        return sampler_cls(
            backend,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=temperature,
            seed=seed,
            batch_size=batch_size,
            **kwargs,
        )
    return factory


def _synthetic_sampler_factory(n_items: Optional[int], collector: Optional[c2b.TranscriptCollector] = None):
    def factory(axis: str):
        items = c2b.load_axis_items(axis, True, n_items)
        backend = SyntheticC2bTaskBackend(axis, items, prompt_gain=0.4, alpha_gain=0.1, threshold=0.5)
        sampler_cls = c2b.TranscriptBackendOutcomeSampler if collector else BackendOutcomeSampler
        kwargs = {"transcript_collector": collector} if collector else {}
        return sampler_cls(backend, do_sample=False, **kwargs)
    return factory


def _planned_generations(specs: List[AxisAdjSpec]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for spec in specs:
        _, n_test = adj._split_sizes(len(spec.items), dev_fraction=adj.DEV_FRACTION)
        out[spec.axis] = int(n_test * len(spec.strong_prompts) * adj.K_SAMPLES)
    return out


def _comparator_minus_best(res: adj.AvgPromptComparatorAxisResult, src: Dict[str, object],
                           *, seed: int, bootstrap_b: int) -> Dict[str, object]:
    novice = np.asarray(res.primary_avg16["per_item_comparator"], dtype=float)
    if res.axis == "deliberation" and src.get("best_prompt_512"):
        best = np.asarray(src["best_prompt_512"], dtype=float)
        name = "novice_mean_minus_best_prompt_512"
    else:
        best = np.asarray(src["per_item_prompt"], dtype=float)
        name = "novice_mean_minus_frozen_best_prompt"
    if novice.shape != best.shape:
        raise ValueError(f"{res.axis}: novice length {novice.shape[0]} != best length {best.shape[0]}")
    diff = novice - best
    ci = adj.cluster_bootstrap_ci(diff, b=int(bootstrap_b), ci_level=adj.BONFERRONI_CI_LEVEL, seed=int(seed), cluster=True)
    return {
        "name": name,
        "mean_diff": ci.point,
        "ci_lo": ci.ci_lo,
        "ci_hi": ci.ci_hi,
        "ci_level": ci.ci_level,
        "bootstrap_b": int(bootstrap_b),
        "per_item_diff": [float(x) for x in diff],
        "note": "diagnostic novice-prompt mean minus frozen best-prompt analogue; not a pass/fail contrast",
    }


def _format_compliance(transcript_root: Optional[Path]) -> Dict[str, object]:
    if transcript_root is None:
        return {"available": False, "note": "transcripts disabled"}
    rows = []
    for path in Path(transcript_root).glob("*test_avg_prompt_candidate*.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    by_axis: Dict[str, Dict[str, int]] = {}
    for row in rows:
        axis = str(row.get("axis"))
        parse = row.get("parse") or {}
        bucket = by_axis.setdefault(axis, {"samples": 0, "parse_failures": 0})
        bucket["samples"] += 1
        bucket["parse_failures"] += int(bool(parse.get("axis_parse_failed")))
    for bucket in by_axis.values():
        n = max(1, int(bucket["samples"]))
        bucket["format_compliance_rate"] = 1.0 - int(bucket["parse_failures"]) / n
    return {"available": True, "source": _rel(transcript_root), "candidate_prompt_samples": len(rows), "by_axis": by_axis}


def _write_candidate_set(results: List[adj.AvgPromptComparatorAxisResult], out_dir: Path) -> Path:
    path = out_dir / "novice_prompt_candidate_set.jsonl"
    with open(path, "w", encoding="utf-8") as fh:
        for res in results:
            for pid in res.candidate_prompt_ids:
                fh.write(json.dumps({
                    "axis": res.axis,
                    "prompt_id": pid,
                    "text": next((p for p in res.descriptive.get("novice_prompts", []) if p["prompt_id"] == pid), {}).get("text"),
                }, ensure_ascii=False) + "\n")
    return path


def _write_outcome_long(results: List[adj.AvgPromptComparatorAxisResult], out_dir: Path) -> Path:
    path = out_dir / "novice_prompt_candidate_outcomes.jsonl"
    with open(path, "w", encoding="utf-8") as fh:
        for res in results:
            for item_idx, item_id in enumerate(res.test_item_ids):
                for prompt_id in res.candidate_prompt_ids:
                    fh.write(json.dumps({
                        "axis": res.axis,
                        "item_id": item_id,
                        "prompt_id": prompt_id,
                        "item_outcome": float(res.candidate_outcomes_by_prompt[prompt_id][item_idx]),
                    }, ensure_ascii=False) + "\n")
    return path


def _write_results(results: List[adj.AvgPromptComparatorAxisResult], out_dir: Path,
                   meta: Dict[str, object], transcript_root: Optional[Path]) -> Path:
    cand = _write_candidate_set(results, out_dir)
    outcomes = _write_outcome_long(results, out_dir)
    payload = {
        **meta,
        "format_compliance": _format_compliance(transcript_root),
        "artifacts": {
            "candidate_set": _rel(cand),
            "candidate_outcomes_long": _rel(outcomes),
            "transcripts": None if transcript_root is None else _rel(transcript_root),
        },
        "axes": [r.to_row() for r in results],
    }
    path = out_dir / "novice_prompt_comparator_results.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# Simulated-Novice Prompt Comparator Arm",
        "",
        "- valid_for_paper: **False**",
        "- anchor calibration gate: **NOT passed; exploratory only**",
        f"- model: `{meta.get('model')}` backend: `{meta.get('backend')}`",
        f"- steering_source: `{meta.get('steering_source')}`",
        "",
        "| axis | frozen α | n_test | steer−novice mean(d) | 98.33% CI | coherence | pass/invalid | novice−best analogue |",
        "|---|---:|---:|---:|---|---|---|---:|",
    ]
    for res in results:
        p = res.primary_avg16
        nb = res.descriptive["novice_minus_best_prompt"]
        coherence = "ok" if p["coherence_ok"] else "FAIL"
        verdict = "invalid/coherence_failed" if not p["coherence_ok"] else ("YES" if p["passed"] else "no")
        lines.append(
            f"| {res.axis} | {res.frozen_alpha:g} | {res.n_test} | "
            f"{float(p['mean_diff']):+.4f} | [{float(p['ci_lo']):+.4f}, {float(p['ci_hi']):+.4f}] | "
            f"{coherence} | {verdict} | {float(nb['mean_diff']):+.4f} |"
        )
    (out_dir / "novice_prompt_comparator_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _register(out_dir: Path, result_path: Path, meta: Dict[str, object],
              results: List[adj.AvgPromptComparatorAxisResult], seed: int) -> str:
    reg = ExperimentRegistry(str(out_dir / "experiment-registry.yaml"))
    cfg = {
        "kind": "simulated_novice_prompt_comparator",
        "model": meta.get("model"),
        "model_revision": meta.get("model_revision"),
        "method": meta.get("steering_method"),
        "axes": [r.axis for r in results],
        "seed": seed,
        "prompt_set_hash": meta.get("prompt_set_sha256"),
        "frozen_params": adj.frozen_params_dict(),
        "primary": "steer minus per-item mean over generated novice-style prompts",
        "valid_for_paper": False,
    }
    cfg_hash = config_hash(cfg)
    exp_id = new_experiment_id(reg, "novice-prompt-comparator", cfg_hash)
    rec = ExperimentRecord(
        experiment_id=exp_id,
        hypothesis_id="H-SIM-NOVICE-BRIDGE",
        claim_ids=["C2b"],
        type="exploratory",
        status="done",
        code_commit=git_commit(str(_REPO)),
        dirty_tree=False,
        config_hash=cfg_hash,
        data_hash=str(meta.get("prompt_set_sha256")),
        model=str(meta.get("model")),
        dataset=str(meta.get("dataset")),
        seed=seed,
        hardware=str(meta.get("hardware")),
        started_at=str(meta.get("started_at")),
        ended_at=utcnow(),
        exit_code=0,
        summary_metrics={
            r.axis: {
                "frozen_alpha": r.frozen_alpha,
                "steer_minus_novice_mean_diff": r.primary_avg16["mean_diff"],
                "ci_9833": [r.primary_avg16["ci_lo"], r.primary_avg16["ci_hi"]],
                "coherence_ok": r.primary_avg16["coherence_ok"],
                "passed": r.primary_avg16["passed"],
                "novice_minus_best_mean": r.descriptive["novice_minus_best_prompt"]["mean_diff"],
            }
            for r in results
        },
        artifacts=[_rel(result_path)],
        valid_for_paper=False,
        validation_notes=(
            "Exploratory simulated-novice prompt comparator. Anchor calibration gate NOT passed; "
            "threat: AI-generated novice prompts are not validated against real novices."
        ),
    )
    reg.append(rec)
    return exp_id


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["synthetic", "hf"], default="hf")
    ap.add_argument("--model", default=DEFAULT_QWEN_MODEL)
    ap.add_argument("--model-revision", default=FROZEN_QWEN_REVISION)
    ap.add_argument("--steering-method", choices=["caa", "iti"], default="caa")
    ap.add_argument("--axes", nargs="*", default=["deliberation", "skepticism", "uncertainty_awareness"])
    ap.add_argument("--prompt-set", required=True)
    ap.add_argument("--frozen-result", required=True)
    ap.add_argument("--delib-512-repair", default=None)
    ap.add_argument("--seed", type=int, default=20260723)
    ap.add_argument("--n-items", type=int, default=None)
    ap.add_argument("--bootstrap-b", type=int, default=adj.BOOTSTRAP_B)
    ap.add_argument("--allow-underpowered", action="store_true")
    ap.add_argument("--max-new-tokens", type=int, default=64)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--hf-home", default=None)
    ap.add_argument("--venv", default=None)
    ap.add_argument("--disk-budget-gb", type=float, default=60.0)
    ap.add_argument("--disk-ceiling-gb", type=float, default=70.0)
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--save-transcripts", action=argparse.BooleanOptionalAction, default=True)
    ap.add_argument("--out-dir", default=None)
    return ap


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    axes = list(args.axes)
    if "deliberation" in axes and int(args.max_new_tokens) < 512:
        raise SystemExit("[novice] FATAL: deliberation requires --max-new-tokens >= 512")
    if args.bootstrap_b < 10000 and not args.allow_underpowered:
        raise SystemExit("[novice] FATAL: bootstrap_b < frozen 10000")

    out_dir = Path(args.out_dir) if args.out_dir else (
        _REPO / "results" / f"novice_prompt_comparator_{args.backend}_{date.today().isoformat()}"
    )
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    started_at = utcnow()
    t0 = time.time()

    prompt_set_path = Path(args.prompt_set)
    prompts = _load_prompt_set(prompt_set_path, axes)
    frozen_sources = _load_frozen_sources(Path(args.frozen_result))
    delib_repair_path = Path(args.delib_512_repair) if args.delib_512_repair else None
    if "deliberation" in axes:
        _apply_delib512_override(frozen_sources["deliberation"], delib_repair_path)
    layer_by_axis = {axis: int(src.get("layer", 1)) for axis, src in frozen_sources.items()}

    specs = _prompt_only_specs(axes, prompts, args.n_items, layer_by_axis)
    if args.backend == "synthetic":
        model = "synthetic-offline"
        hardware = "cpu-offline"
        collector = c2b.TranscriptCollector(out_dir, model, args.steering_method, "synthetic") if args.save_transcripts else None
        sampler_for_axis = _synthetic_sampler_factory(args.n_items, collector)
    else:
        model = args.model
        usage0 = check_disk_budget(default_guard_paths(args.hf_home, args.venv), args.disk_budget_gb, args.disk_ceiling_gb)
        print(f"[novice] disk pre-run: {usage0.message}", flush=True)
        collector = c2b.TranscriptCollector(out_dir, model, args.steering_method, "hf") if args.save_transcripts else None
        sampler_for_axis = _hf_prompt_sampler_factory(model, args.model_revision, args.max_new_tokens, args.temperature, args.seed, args.batch_size, collector)
        hardware = f"{p0._pick_device()}-{p0._pick_dtype()}"

    per_axis_plan = _planned_generations(specs)
    print(f"[novice] planned candidate generations: {per_axis_plan} TOTAL={sum(per_axis_plan.values())}", flush=True)
    print("[novice] exploratory-only; no alpha/prompt reselection; frozen records read-only.", flush=True)

    fp = config_hash({
        "kind": "novice_prompt_comparator",
        "seed": args.seed,
        "backend": args.backend,
        "model": model,
        "model_revision": args.model_revision if args.backend == "hf" else None,
        "steering_method": args.steering_method,
        "axes": axes,
        "prompt_set_sha256": _sha256(prompt_set_path),
        "frozen_result_sha256": _sha256(Path(args.frozen_result)),
        "delib_512_repair_sha256": None if delib_repair_path is None else _sha256(delib_repair_path),
        "max_new_tokens": args.max_new_tokens,
        "temperature": args.temperature,
        "batch_size": args.batch_size,
        "bootstrap_b": args.bootstrap_b,
    }).replace("sha256:", "")[:16]
    checkpoint = c2b.TranscriptCheckpointStore(out_dir / "checkpoints", fp, seed=args.seed, fresh=args.fresh, collector=collector)
    ctx = RunContext(checkpoint=checkpoint, progress=ProgressTracker(sum(per_axis_plan.values())))

    results: List[adj.AvgPromptComparatorAxisResult] = []
    try:
        for spec in specs:
            src = frozen_sources[spec.axis]
            axis_result = adj.avg_prompt_comparator_axis(
                sampler_for_axis(spec.axis),
                spec,
                frozen_alpha=float(src["frozen_alpha"]),
                per_item_steer=src["per_item_steer"],  # type: ignore[arg-type]
                steering_source=f"committed:{args.frozen_result}" + (f";delib512:{args.delib_512_repair}" if spec.axis == "deliberation" and args.delib_512_repair else ""),
                best_prompt_id=None,
                coherence_ok=bool(src.get("coherence_ok", True)),
                test_steer_degeneracy=src.get("test_steer_degeneracy"),
                test_baseline_degeneracy=src.get("test_baseline_degeneracy"),
                reference_steer_mean=src.get("reference_steer_mean"),
                validity_tolerance=0.0,
                k=adj.K_SAMPLES,
                bootstrap_b=args.bootstrap_b,
                ci_level=adj.BONFERRONI_CI_LEVEL,
                delta=adj.DELTA,
                seed=args.seed,
                ctx=ctx,
            )
            axis_result.descriptive["primary_comparator"] = "per-TEST-item mean over generated novice-style prompts"
            axis_result.descriptive["novice_prompts"] = [
                {"prompt_id": pid, "text": text} for pid, text in prompts[spec.axis]
            ]
            axis_result.descriptive["novice_minus_best_prompt"] = _comparator_minus_best(
                axis_result, src, seed=args.seed, bootstrap_b=args.bootstrap_b
            )
            axis_result.descriptive["anchor_calibration_gate"] = "NOT passed; exploratory only"
            results.append(axis_result)
    finally:
        checkpoint.close()

    transcript_root = None
    if collector is not None:
        transcript_root = out_dir / "transcripts"
        transcript_root.mkdir(parents=True, exist_ok=True)
        collector._write_cell_files(transcript_root, {})
        print(f"[novice] transcripts: {_rel(transcript_root)}", flush=True)

    wall = time.time() - t0
    meta = {
        "generated_at": utcnow(),
        "started_at": started_at,
        "backend": args.backend,
        "model": model,
        "model_revision": args.model_revision if args.backend == "hf" else None,
        "steering_method": args.steering_method,
        "seed": args.seed,
        "frozen_params": adj.frozen_params_dict(),
        "primary_comparator": "per-item mean over generated novice-style prompts",
        "steering_source": "frozen-result with optional deliberation 512-token repair",
        "protocol_frozen": True,
        "run_type": "exploratory_bridge",
        "valid_for_paper": False,
        "anchor_calibration_gate": "NOT passed; exploratory only",
        "threat": "AI-generated novice prompts are not validated against real novices.",
        "dataset": "OpenAssistant/oasst1 Apache-2.0 few-shot style anchors; data/c2b_tasks/* TEST items",
        "prompt_set": _rel(prompt_set_path),
        "prompt_set_sha256": _sha256(prompt_set_path),
        "frozen_result": _rel(Path(args.frozen_result)),
        "frozen_result_sha256": _sha256(Path(args.frozen_result)),
        "delib_512_repair": None if delib_repair_path is None else _rel(delib_repair_path),
        "delib_512_repair_sha256": None if delib_repair_path is None else _sha256(delib_repair_path),
        "generation_accounting": {"candidate_prompt": {"per_axis": per_axis_plan, "total": sum(per_axis_plan.values())}},
        "hardware": hardware,
        "platform": platform.platform(),
        "wall_clock_seconds": round(wall, 2),
    }
    result_path = _write_results(results, out_dir, meta, transcript_root)
    exp_id = _register(out_dir, result_path, meta, results, args.seed)
    print(f"[novice] wrote {_rel(result_path)} (exp {exp_id}) wall={wall:.1f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
