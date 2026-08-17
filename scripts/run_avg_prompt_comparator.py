"""Average-prompt comparator arm for frozen C2b TEST cells.

Stage-1/2 contract:
* no DEV prompt or alpha selection;
* candidate prompt set is the frozen authored 16-prompt JSONL per axis;
* primary comparator is the per-TEST-item mean over the 16 candidate outcomes;
* secondary comparators are drop-DEV-best and worst-prompt lower bound;
* paired steer-minus-average uses the same item-cluster bootstrap, Bonferroni
  CI, delta, and coherence gate as the frozen best-prompt arm.
"""

from __future__ import annotations

import argparse
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

from cognitive_console.experiments import adjudicate_c2b as adj
from cognitive_console.experiments.adjudicate_c2b import (
    AxisAdjSpec,
    BackendOutcomeSampler,
    CheckpointStore,
    ProgressTracker,
    RunContext,
)
from cognitive_console.lineage import git_commit, new_experiment_id, utcnow
from cognitive_console.ops.disk_guard import check_disk_budget, default_guard_paths
from cognitive_console.registry import ExperimentRecord, ExperimentRegistry
from cognitive_console.config import config_hash
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


def _parse_axis_float(values: Optional[List[str]]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for raw in values or []:
        if "=" not in raw:
            raise SystemExit(f"expected axis=value, got {raw!r}")
        axis, value = raw.split("=", 1)
        out[str(axis)] = float(value)
    return out


def _load_frozen_sources(path: Path) -> Dict[str, Dict[str, object]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    out: Dict[str, Dict[str, object]] = {}
    for row in data.get("axes", []):
        axis = str(row.get("axis"))
        dev = row.get("dev_selection", {}) or {}
        per_item_steer = row.get("per_item_steer")
        if not isinstance(per_item_steer, list):
            raise ValueError(f"{path}: axis {axis} has no per_item_steer array")
        out[axis] = {
            "frozen_alpha": float(dev["frozen_alpha"]),
            "best_prompt_id": str(dev.get("best_prompt_id")),
            "best_prompt_text": str(dev.get("best_prompt_text")),
            "per_item_steer": [float(x) for x in per_item_steer],
            "coherence_ok": bool(row.get("coherence_ok")),
            "test_steer_degeneracy": row.get("test_steer_degeneracy"),
            "test_baseline_degeneracy": row.get("test_baseline_degeneracy"),
            "reference_steer_mean": float(np.mean([float(x) for x in per_item_steer])),
            "layer": int(row.get("layer", 1)),
            "n_test": int(row.get("n_test", len(per_item_steer))),
        }
    return out


def _prompt_only_specs(axes: List[str], use_fixture: bool, n_items: Optional[int],
                       n_strong: int, layer_by_axis: Optional[Dict[str, int]] = None
                       ) -> List[AxisAdjSpec]:
    neutral = c1.load_neutral_prompts()[0]
    specs: List[AxisAdjSpec] = []
    for axis in axes:
        items = c2b.load_axis_items(axis, use_fixture, n_items)
        specs.append(AxisAdjSpec(
            axis=axis,
            items=items,
            strong_prompts=c2b.build_strong_prompts(axis, n_strong),
            neutral_prompt=neutral,
            # Prompt-only candidate cells use alpha=0, and the sampler suppresses
            # the steering hook for alpha=0; this vector is intentionally unused.
            direction=np.ones(1),
            layer=int((layer_by_axis or {}).get(axis, 1)),
        ))
    return specs


def _synthetic_sampler_factory(use_fixture: bool, n_items: Optional[int],
                               collector: Optional[c2b.TranscriptCollector] = None):
    def factory(axis: str):
        items = c2b.load_axis_items(axis, use_fixture, n_items)
        backend = SyntheticC2bTaskBackend(axis, items, prompt_gain=0.4,
                                          alpha_gain=0.1, threshold=0.5)
        sampler_cls = c2b.TranscriptBackendOutcomeSampler if collector else BackendOutcomeSampler
        kwargs = {"transcript_collector": collector} if collector else {}
        return sampler_cls(backend, do_sample=False, **kwargs)
    return factory


def _hf_prompt_sampler_factory(model: str, revision: Optional[str], max_new_tokens: int,
                               temperature: float, seed: int, batch_size: int,
                               collector: Optional[c2b.TranscriptCollector] = None):
    from cognitive_console.steering.generate import SteeredHFBackend
    device, dtype = p0._pick_device(), p0._pick_dtype()
    backend = SteeredHFBackend(model, device=device, dtype=dtype, seed=seed,
                               revision=revision)

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


def _planned_prompt_generations(specs: List[AxisAdjSpec], *, k: int,
                                dev_fraction: float = adj.DEV_FRACTION,
                                include_generated_steering: bool = False) -> Dict[str, int]:
    per_axis: Dict[str, int] = {}
    for spec in specs:
        _, n_test = adj._split_sizes(len(spec.items), dev_fraction=dev_fraction)
        steering_cells = 2 if include_generated_steering else 0
        per_axis[spec.axis] = int(n_test * (len(spec.strong_prompts) + steering_cells) * k)
    return per_axis


def _write_candidate_set(specs: List[AxisAdjSpec], out_dir: Path) -> Path:
    path = out_dir / "avg_prompt_candidate_set.jsonl"
    with open(path, "w", encoding="utf-8") as fh:
        for spec in specs:
            for pid, text in spec.strong_prompts:
                fh.write(json.dumps({
                    "axis": spec.axis,
                    "prompt_id": str(pid),
                    "text": str(text),
                }, ensure_ascii=False) + "\n")
    return path


def _write_outcome_long(results: List[adj.AvgPromptComparatorAxisResult],
                        out_dir: Path) -> Path:
    path = out_dir / "avg_prompt_candidate_outcomes.jsonl"
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
        bucket["format_compliance_rate"] = 1.0 - (int(bucket["parse_failures"]) / n)
    return {
        "available": True,
        "source": _rel(Path(transcript_root)),
        "candidate_prompt_samples": len(rows),
        "by_axis": by_axis,
    }


def _write_results(results: List[adj.AvgPromptComparatorAxisResult], out_dir: Path,
                   meta: Dict[str, object], transcript_root: Optional[Path]) -> Path:
    candidate_set = _write_candidate_set(meta["specs"], out_dir)  # type: ignore[index]
    outcomes_long = _write_outcome_long(results, out_dir)
    payload = {
        **{k: v for k, v in meta.items() if k != "specs"},
        "format_compliance": _format_compliance(transcript_root),
        "artifacts": {
            "candidate_set": _rel(candidate_set),
            "candidate_outcomes_long": _rel(outcomes_long),
            "transcripts": None if transcript_root is None else _rel(transcript_root),
        },
        "axes": [r.to_row() for r in results],
    }
    path = out_dir / "avg_prompt_comparator_results.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Average-Prompt Comparator Arm",
        "",
        f"- generated_at: `{payload.get('generated_at')}`",
        f"- backend: `{payload.get('backend')}` model: `{payload.get('model')}`",
        f"- valid_for_paper: **{payload.get('valid_for_paper')}**",
        f"- steering_source: `{payload.get('steering_source')}`",
        "",
        "| axis | frozen α | n_test | primary mean(d) | primary CI | primary pass | drop-best mean(d) | worst mean(d) |",
        "|---|---:|---:|---:|---|---|---:|---:|",
    ]
    for res in results:
        p = res.primary_avg16
        d = res.secondary_drop_best15
        w = res.secondary_worst_prompt
        lines.append(
            f"| {res.axis} | {res.frozen_alpha:g} | {res.n_test} | "
            f"{float(p['mean_diff']):+.4f} | [{float(p['ci_lo']):+.4f}, {float(p['ci_hi']):+.4f}] | "
            f"{'YES' if p['passed'] else 'no'} | {float(d['mean_diff']):+.4f} | "
            f"{float(w['mean_diff']):+.4f} |"
        )
    (out_dir / "avg_prompt_comparator_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _register(out_dir: Path, result_path: Path, payload_meta: Dict[str, object],
              results: List[adj.AvgPromptComparatorAxisResult], seed: int) -> str:
    reg = ExperimentRegistry(str(out_dir / "experiment-registry.yaml"))
    cfg = {
        "kind": "avg_prompt_comparator",
        "model": payload_meta.get("model"),
        "model_revision": payload_meta.get("model_revision"),
        "steering_method": payload_meta.get("steering_method"),
        "axes": [r.axis for r in results],
        "seed": seed,
        "frozen_params": adj.frozen_params_dict(),
        "primary": "per-item 16-candidate prompt mean",
    }
    cfg_hash = config_hash(cfg)
    exp_id = new_experiment_id(reg, "avg-prompt-comparator", cfg_hash)
    rec = ExperimentRecord(
        experiment_id=exp_id,
        hypothesis_id="H-AVG-PROMPT",
        claim_ids=["C2b"],
        type="diagnostic",
        status="done",
        code_commit=git_commit(str(_REPO)),
        dirty_tree=False,
        config_hash=cfg_hash,
        model=str(payload_meta.get("model")),
        dataset="data/c2b_tasks/* + data/strongest_prompts/*.jsonl",
        seed=seed,
        hardware=str(payload_meta.get("hardware")),
        started_at=str(payload_meta.get("started_at")),
        ended_at=utcnow(),
        exit_code=0,
        summary_metrics={
            r.axis: {
                "frozen_alpha": r.frozen_alpha,
                "primary_mean_diff": r.primary_avg16["mean_diff"],
                "primary_ci": [r.primary_avg16["ci_lo"], r.primary_avg16["ci_hi"]],
                "primary_passed": r.primary_avg16["passed"],
            }
            for r in results
        },
        artifacts=[_rel(result_path)],
        valid_for_paper=False,
        validation_notes=(
            "Average-prompt comparator Stage-1/2 artifact. Frozen protocol, but "
            "valid_for_paper remains false until Manager Stage-2 GO, full run, and audit."
        ),
    )
    reg.append(rec)
    return exp_id


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Run average-prompt comparator arm")
    ap.add_argument("--backend", choices=["synthetic", "hf"], default="synthetic")
    ap.add_argument("--model", default=DEFAULT_QWEN_MODEL)
    ap.add_argument("--model-revision", default=FROZEN_QWEN_REVISION)
    ap.add_argument("--steering-method", choices=["caa", "iti"], default="caa")
    ap.add_argument("--axes", nargs="*", default=["uncertainty_awareness"])
    ap.add_argument("--seed", type=int, default=20260723)
    ap.add_argument("--n-items", type=int, default=None)
    ap.add_argument("--n-strong", type=int, default=16)
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
    ap.add_argument("--steering-source", choices=["frozen-result", "generate"], default="frozen-result")
    ap.add_argument("--frozen-result", default=None,
                    help="frozen best-prompt result JSON with per_item_steer arrays")
    ap.add_argument("--frozen-alpha", action="append", default=[],
                    help="axis=alpha fallback/override; no selection is performed")
    ap.add_argument("--validity-tolerance", type=float, default=0.01,
                    help="absolute tolerance for regenerated steering mean vs frozen source")
    ap.add_argument("--out-dir", default=None)
    return ap


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    axes = list(args.axes)
    if args.bootstrap_b < 10000 and not args.allow_underpowered:
        raise SystemExit(
            f"[avg-prompt] FATAL: --bootstrap-b {args.bootstrap_b} < frozen 10000; "
            "use --allow-underpowered only for smoke/debug"
        )

    out_dir = Path(args.out_dir) if args.out_dir else (
        _REPO / "results" / f"avg_prompt_comparator_{args.backend}_{date.today().isoformat()}"
    )
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    started_at = utcnow()
    t0 = time.time()

    frozen_sources: Dict[str, Dict[str, object]] = {}
    if args.frozen_result:
        frozen_sources = _load_frozen_sources(Path(args.frozen_result))
    frozen_alpha_cli = _parse_axis_float(args.frozen_alpha)
    layer_by_axis = {
        axis: int(src.get("layer", 1))
        for axis, src in frozen_sources.items()
    }

    if args.backend == "synthetic":
        use_fixture = True
        specs = c2b.build_specs_synthetic(axes, use_fixture, args.n_items, args.n_strong)
        model = "synthetic-offline"
        hardware = "cpu-offline"
        collector = c2b.TranscriptCollector(out_dir, model, args.steering_method, "synthetic") \
            if args.save_transcripts else None
        sampler_for_axis = _synthetic_sampler_factory(use_fixture, args.n_items, collector)
    else:
        model = args.model
        guard_paths = default_guard_paths(args.hf_home, args.venv)
        usage0 = check_disk_budget(guard_paths, args.disk_budget_gb, args.disk_ceiling_gb)
        print(f"[avg-prompt] disk pre-run: {usage0.message}", flush=True)
        if args.steering_source == "frozen-result":
            specs = _prompt_only_specs(axes, False, args.n_items, args.n_strong, layer_by_axis)
            collector = c2b.TranscriptCollector(out_dir, model, args.steering_method, "hf") \
                if args.save_transcripts else None
            sampler_for_axis = _hf_prompt_sampler_factory(
                model, args.model_revision, args.max_new_tokens, args.temperature,
                args.seed, args.batch_size, collector)
        else:
            specs, hf_meta = c2b.build_specs_hf(
                axes, model, False, args.n_items, args.n_strong, 28,
                args.seed, out_dir, args.steering_method,
                model_revision=args.model_revision)
            layer_by_axis.update({
                axis: int(row["chosen_layer"])
                for axis, row in hf_meta.get("c1_layer_info", {}).items()
            })
            collector = c2b.TranscriptCollector(out_dir, model, args.steering_method, "hf") \
                if args.save_transcripts else None
            sampler_for_axis = c2b.hf_sampler_factory(
                model, args.max_new_tokens, args.temperature, args.seed,
                args.batch_size, collector, hf_meta.get("alpha_scale_by_axis"),
                model_revision=args.model_revision)
        hardware = f"{p0._pick_device()}-{p0._pick_dtype()}"

    per_axis_plan = _planned_prompt_generations(
        specs, k=adj.K_SAMPLES,
        include_generated_steering=args.steering_source == "generate")
    total_plan = sum(per_axis_plan.values())
    print(f"[avg-prompt] planned candidate generations: {per_axis_plan} TOTAL={total_plan}", flush=True)
    print("[avg-prompt] Stage-1/2 guard: no prompt or alpha selection; no frozen result overwrite.", flush=True)

    fingerprint_payload = {
        "seed": args.seed, "backend": args.backend, "model": model,
        "model_revision": args.model_revision if args.backend == "hf" else None,
        "steering_method": args.steering_method, "axes": axes,
        "n_items": args.n_items, "n_strong": args.n_strong,
        "max_new_tokens": args.max_new_tokens, "temperature": args.temperature,
        "batch_size": args.batch_size, "bootstrap_b": args.bootstrap_b,
        "steering_source": args.steering_source,
        "frozen_result": args.frozen_result,
    }
    fp = config_hash(fingerprint_payload).replace("sha256:", "")[:16]
    checkpoint = c2b.TranscriptCheckpointStore(
        out_dir / "checkpoints", fp, seed=args.seed, fresh=args.fresh,
        collector=collector,
    )
    ctx = RunContext(checkpoint=checkpoint, progress=ProgressTracker(total_plan))

    results: List[adj.AvgPromptComparatorAxisResult] = []
    try:
        for spec in specs:
            src = frozen_sources.get(spec.axis, {})
            if spec.axis in frozen_alpha_cli:
                frozen_alpha = frozen_alpha_cli[spec.axis]
            elif "frozen_alpha" in src:
                frozen_alpha = float(src["frozen_alpha"])
            else:
                raise SystemExit(f"[avg-prompt] missing frozen alpha for axis {spec.axis}")
            if args.steering_source == "frozen-result":
                if not src:
                    raise SystemExit(f"[avg-prompt] missing frozen-result axis row for {spec.axis}")
                per_item_steer = src["per_item_steer"]
                steering_label = f"committed:{args.frozen_result}"
            else:
                per_item_steer = None
                steering_label = "same-run-regenerated"
            results.append(adj.avg_prompt_comparator_axis(
                sampler_for_axis(spec.axis),
                spec,
                frozen_alpha=frozen_alpha,
                per_item_steer=per_item_steer,  # type: ignore[arg-type]
                steering_source=steering_label,
                best_prompt_id=src.get("best_prompt_id"),
                coherence_ok=bool(src.get("coherence_ok", True)),
                test_steer_degeneracy=src.get("test_steer_degeneracy"),
                test_baseline_degeneracy=src.get("test_baseline_degeneracy"),
                reference_steer_mean=src.get("reference_steer_mean"),
                validity_tolerance=args.validity_tolerance,
                k=adj.K_SAMPLES,
                bootstrap_b=args.bootstrap_b,
                ci_level=adj.BONFERRONI_CI_LEVEL,
                delta=adj.DELTA,
                seed=args.seed,
                ctx=ctx,
            ))
    finally:
        checkpoint.close()

    transcript_root = collector.write_all(out_dir, None) if False else None
    # TranscriptCollector.write_all expects a best-prompt report for paired TEST
    # files. For this comparator, the per-cell files are already grouped in the
    # collector; write them through a lightweight synthetic report shim is not
    # needed, so call the private cell writer directly and keep the format local.
    if collector is not None:
        transcript_root = out_dir / "transcripts"
        transcript_root.mkdir(parents=True, exist_ok=True)
        collector._write_cell_files(transcript_root, {})  # observational side-output
        print(f"[avg-prompt] transcripts: {_rel(transcript_root)}", flush=True)

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
        "primary_comparator": "per-item mean over 16 frozen candidate prompts",
        "secondary_comparators": ["drop-best-15 per-item mean", "worst-prompt lower bound"],
        "steering_source": args.steering_source,
        "protocol_frozen": True,
        "run_type": "diagnostic" if args.allow_underpowered else "confirmatory-ready",
        "valid_for_paper": False,
        "generation_accounting": {"candidate_prompt": {"per_axis": per_axis_plan, "total": total_plan}},
        "hardware": hardware,
        "platform": platform.platform(),
        "wall_clock_seconds": round(wall, 2),
        "specs": specs,
    }
    result_path = _write_results(results, out_dir, meta, transcript_root)
    exp_id = _register(out_dir, result_path, meta, results, args.seed)
    print(f"[avg-prompt] wrote {_rel(result_path)} (exp {exp_id}) wall={wall:.1f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
