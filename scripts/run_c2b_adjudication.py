"""C2b QUALIFIED adjudication runner — FROZEN instrument (prereg §4/§5).

Runs the pre-registered, three-tier C2b behavioral-gap adjudication:
DEV/TEST split -> DEV-frozen best-of-16 prompt + coherence-gated α -> TEST paired
per-item diffs -> paired ITEM-cluster bootstrap (B≥10000, Bonferroni CI 1−0.05/3)
-> per-axis pass (CI excludes 0 AND mean(d)≥δ=0.05 AND coherence ≤1.5×) ->
three-tier verdict (STRONG_GO / CONDITIONAL_GO / KILL_PLAN_D). Conflict cells are
SECONDARY/descriptive only.

Two backends (model-independent core):
* ``--backend synthetic`` — offline, no torch: exercises the WHOLE pipeline on the
  bundled fixtures with ``SyntheticC2bTaskBackend`` and produces a real verdict
  artifact. This is the CPU smoke that proves the pipeline end-to-end.
* ``--backend hf`` — real ``SteeredHFBackend`` (CPU/1.5B smoke or A800/7B). Re-
  derives the C1 chosen non-degenerate layer per axis + the CAA unit direction at
  that layer on the RUN's model (never hardcoded), reuses the disk guard, and runs
  the adjudication with sampled (k=5) generation.

EVERYTHING is EXPLORATORY until the A800 7B run: valid_for_paper=false, honest
wall-clock, numbers only from computed artifacts. See RUN_ON_A800.md §Adjudication.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cognitive_console.eval import c2b_tasks
from cognitive_console.experiments import adjudicate_c2b as adj
from cognitive_console.experiments.adjudicate_c2b import (
    AxisAdjSpec, BackendOutcomeSampler,
)
from cognitive_console.steering.generate import SyntheticC2bTaskBackend
from cognitive_console.config import config_hash
from cognitive_console.registry import ExperimentRecord, ExperimentRegistry
from cognitive_console.lineage import git_commit, new_experiment_id, utcnow
from cognitive_console.manifest import ArtifactManifest, write_manifest
from cognitive_console.ops.disk_guard import check_disk_budget, default_guard_paths

from scripts import run_c1_facade as c1
from scripts import run_gpu_phase0 as p0

# The three FROZEN axes (focus DROPPED per prereg §1.6).
ADJ_AXES = ["deliberation", "skepticism", "uncertainty_awareness"]
DEFAULT_MODEL = "Qwen/Qwen2.5-7B-Instruct"
SMOKE_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
DEFAULT_N_STRONG = 16  # best-of-16 authored prompts (prereg §4)


def _rel(path: Path) -> str:
    p = Path(path).resolve()
    try:
        return str(p.relative_to(_REPO)).replace("\\", "/")
    except ValueError:
        return str(p).replace("\\", "/")


# --------------------------------------------------------------------------- #
# Spec construction
# --------------------------------------------------------------------------- #
def load_axis_items(axis: str, use_fixture: bool, n_items: Optional[int]) -> List[Dict]:
    task = c2b_tasks.load_c2b_task(axis, use_fixture=use_fixture)
    items = list(task.items)
    if n_items is not None:
        items = items[:n_items]
    return items


def build_strong_prompts(axis: str, n_strong: int) -> List:
    strong = c1.load_strongest_prompts(axis)
    return list(zip(strong.ids, strong.texts))[:n_strong]


def build_specs_synthetic(axes: List[str], use_fixture: bool,
                          n_items: Optional[int], n_strong: int) -> List[AxisAdjSpec]:
    """Offline specs — direction/layer are placeholders the synthetic backend ignores."""
    specs = []
    neutral = c1.load_neutral_prompts()[0]
    for axis in axes:
        items = load_axis_items(axis, use_fixture, n_items)
        specs.append(AxisAdjSpec(
            axis=axis, items=items, strong_prompts=build_strong_prompts(axis, n_strong),
            neutral_prompt=neutral, direction=np.ones(8), layer=3,
        ))
    return specs


def build_specs_hf(axes: List[str], model: str, use_fixture: bool,
                   n_items: Optional[int], n_strong: int, n_extraction: int,
                   seed: int, out_dir: Path) -> (List[AxisAdjSpec], Dict):  # noqa
    """Real specs: RE-DERIVE the C1 chosen non-degenerate layer + CAA unit direction
    per axis on THIS model (prereg §2; never hardcoded). Reuses run_c1_facade +
    run_gpu_phase0._extract_direction."""
    from cognitive_console.activations.provider import HFActivationProvider

    device, dtype = p0._pick_device(), p0._pick_dtype()
    c1_out = out_dir / "c1"
    c1_payload = c1.run(
        model=model, axes=axes, scan_step=2, n_extraction=n_extraction, seed=seed,
        n_null=2000, out_dir=c1_out, ram_floor_mb=0.0, device=device, dtype=dtype,
    )
    c1_by_axis = {r["axis"]: r for r in c1_payload["axes"]}

    provider = HFActivationProvider(model, device=device, dtype=dtype,
                                    cache_dir=str(c1_out / "activations" / "cache"))
    neutral = c1.load_neutral_prompts()[0]
    specs = []
    layer_info = {}
    for axis in axes:
        row = c1_by_axis.get(axis, {})
        layer = int(row.get("chosen_layer", max(1, provider.available_layers()[-1] // 2)))
        direction = p0._extract_direction(provider, axis, layer, n_extraction, seed)
        items = load_axis_items(axis, use_fixture, n_items)
        specs.append(AxisAdjSpec(
            axis=axis, items=items, strong_prompts=build_strong_prompts(axis, n_strong),
            neutral_prompt=neutral, direction=direction, layer=layer,
        ))
        layer_info[axis] = {"chosen_layer": layer,
                            "stable_layer_found": row.get("stable_layer_found")}
    return specs, {"c1_layer_info": layer_info, "model": model}


# --------------------------------------------------------------------------- #
# Samplers
# --------------------------------------------------------------------------- #
def synthetic_sampler_factory(use_fixture: bool, n_items: Optional[int]):
    def factory(axis: str):
        items = load_axis_items(axis, use_fixture, n_items)
        backend = SyntheticC2bTaskBackend(axis, items, prompt_gain=0.4,
                                          alpha_gain=0.1, threshold=0.5)
        return BackendOutcomeSampler(backend, do_sample=False)
    return factory


def hf_sampler_factory(model: str, max_new_tokens: int, temperature: float, seed: int):
    from cognitive_console.steering.generate import SteeredHFBackend
    device, dtype = p0._pick_device(), p0._pick_dtype()
    backend = SteeredHFBackend(model, device=device, dtype=dtype, seed=seed)

    def factory(axis: str):
        return BackendOutcomeSampler(backend, max_new_tokens=max_new_tokens,
                                     do_sample=True, temperature=temperature, seed=seed)
    return factory


# --------------------------------------------------------------------------- #
# Output + registration
# --------------------------------------------------------------------------- #
def write_results(report: adj.AdjudicationReport, out_dir: Path, meta: Dict) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = report.to_dict()
    payload.update(meta)
    json_path = out_dir / "c2b_adjudication_results.json"
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)

    lines: List[str] = []
    lines.append("# C2b QUALIFIED Adjudication — FROZEN instrument (prereg §4/§5)\n")
    lines.append(f"- verdict: **{report.verdict}**")
    lines.append(f"- model: `{meta.get('model')}`   backend: `{meta.get('backend')}`   "
                 f"valid_for_paper: **{meta.get('valid_for_paper')}**")
    lines.append(f"- run_type: **{meta.get('run_type')}**   "
                 f"bootstrap_B: {report.frozen_params['bootstrap_b']}   "
                 f"CI level: {report.frozen_params['bonferroni_ci_level']:.5f} (Bonferroni 1−0.05/3)")
    lines.append(f"- δ = {report.frozen_params['delta']}   α grid: {report.frozen_params['alpha_grid']}")
    lines.append("")
    lines.append("| axis | layer | frozen α | best prompt | n_dev | n_test | mean(d) | CI | coherence | PASS |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in report.axis_results:
        ds = r.dev_selection
        ci = "n/a" if r.mean_diff != r.mean_diff else f"[{r.ci_lo:+.3f}, {r.ci_hi:+.3f}]"
        md = "n/a" if r.mean_diff != r.mean_diff else f"{r.mean_diff:+.3f}"
        lines.append(
            f"| {r.axis} | {r.layer} | {ds.get('frozen_alpha')} | "
            f"{ds.get('best_prompt_id')} | {r.n_dev} | {r.n_test} | {md} | {ci} | "
            f"{'ok' if r.coherence_ok else 'FAIL'} | {'YES' if r.passed else 'no'} |")
    lines.append("")
    n_pass = sum(1 for v in report.axis_passes.values() if v)
    lines.append(f"- axes passing (Bonferroni): **{n_pass}/3** -> **{report.verdict}**")
    if report.verdict == adj.VERDICT_CONDITIONAL_GO:
        lines.append("- CONDITIONAL_GO: a pre-registered single-axis REPLICATION on fresh "
                     "items (new DEV/TEST draw, new seed) is REQUIRED before any claim (prereg §4).")
    lines.append("")
    lines.append("## Conflict cells (SECONDARY / descriptive only — NOT part of the verdict)\n")
    lines.append("| axis | opposite α | mean conflict outcome | mean prompt-pole | latent drags down? |")
    lines.append("|---|---|---|---|---|")
    for r in report.axis_results:
        cf = r.conflict
        if "mean_conflict_outcome" in cf:
            lines.append(f"| {r.axis} | {cf['alpha_opposite']} | "
                         f"{cf['mean_conflict_outcome']:.3f} | {cf['mean_prompt_pole_outcome']:.3f} | "
                         f"{cf['latent_drags_down']} |")
    summary_path = out_dir / "c2b_adjudication_summary.md"
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return json_path


def register(report: adj.AdjudicationReport, out_dir: Path, json_path: Path,
             meta: Dict, seed: int) -> str:
    reg_path = out_dir / "experiment-registry.yaml"
    registry = ExperimentRegistry(str(reg_path))
    cfg = {
        "kind": "c2b_qualified_adjudication",
        "model": meta.get("model"),
        "backend": meta.get("backend"),
        "axes": [r.axis for r in report.axis_results],
        "frozen_params": report.frozen_params,
        "seed": seed,
        "torch_seed": seed,  # base torch seed; per-(item,sample) seeds derived from it
    }
    cfg_hash = config_hash(cfg)
    summary_metrics = {
        r.axis: {
            "layer": r.layer,
            "frozen_alpha": r.dev_selection.get("frozen_alpha"),
            "mean_diff": r.mean_diff,
            "ci_lo": r.ci_lo, "ci_hi": r.ci_hi, "ci_level": r.ci_level,
            "coherence_ok": r.coherence_ok,
            "passed": r.passed,
        }
        for r in report.axis_results
    }
    summary_metrics["_verdict"] = report.verdict
    summary_metrics["_axis_passes"] = report.axis_passes
    summary_metrics["_torch_seed"] = seed

    valid_for_paper = bool(meta.get("valid_for_paper", False))
    run_type = str(meta.get("run_type", "exploratory"))
    exp_id = new_experiment_id(registry, "c2b-adj", cfg_hash)
    record = ExperimentRecord(
        experiment_id=exp_id, hypothesis_id="H2", claim_ids=["C2b"],
        type=run_type, status="done", code_commit=git_commit(str(_REPO)),
        config_hash=cfg_hash, model=str(meta.get("model")),
        dataset="data/c2b_tasks/* (fixtures) or deferred real loaders",
        seed=seed, hardware=str(meta.get("hardware")),
        started_at=meta.get("started_at"), ended_at=utcnow(), exit_code=0,
        summary_metrics=summary_metrics, artifacts=[_rel(json_path)],
        valid_for_paper=valid_for_paper,
        validation_notes=(
            "C2b QUALIFIED adjudication implementing FROZEN prereg §4/§5 "
            "(paired ITEM-cluster bootstrap B>=10000, Bonferroni CI 1-0.05/3, "
            "delta=0.05, coherence<=1.5x, three-tier verdict). "
            + ("EXPLORATORY until the A800 7B run (valid_for_paper=false); this run "
               "is a " + run_type + " on " + str(meta.get("backend")) + ".")
        ),
    )
    registry.append(record)
    manifest = ArtifactManifest(
        artifact_id="c2b-qualified-adjudication-table", supports_claims=["C2b"],
        source_experiments=[exp_id], aggregation_script="scripts/run_c2b_adjudication.py",
        aggregation_commit=git_commit(str(_REPO)), output_file=_rel(json_path),
        raw_data_hash=c1._sha256_file(json_path), last_verified=utcnow(), verdict="pending",
    )
    write_manifest(str(out_dir / "c2b_adjudication_table.manifest.yaml"), manifest)
    return exp_id


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="C2b QUALIFIED adjudication (FROZEN prereg §4/§5)")
    ap.add_argument("--backend", choices=["synthetic", "hf"], default="synthetic",
                    help="synthetic = offline no-torch pipeline smoke; hf = real model")
    ap.add_argument("--model", default=None,
                    help="HF model id (default: 7B for hf; ignored for synthetic)")
    ap.add_argument("--axes", nargs="*", default=ADJ_AXES)
    ap.add_argument("--use-fixture", action="store_true",
                    help="use the bundled OFFLINE task fixtures (default for synthetic; "
                         "also the CPU/1.5B smoke). Omit on the A800 for the real loaders.")
    ap.add_argument("--n-items", type=int, default=None,
                    help="cap items/axis (default: all fixture items, or frozen N for real)")
    ap.add_argument("--n-strong", type=int, default=DEFAULT_N_STRONG)
    ap.add_argument("--n-extraction", type=int, default=28)
    ap.add_argument("--bootstrap-b", type=int, default=adj.BOOTSTRAP_B)
    ap.add_argument("--allow-underpowered", action="store_true",
                    help="permit --bootstrap-b < frozen 10000 (prereg §5). OFF by "
                         "default: the confirmatory run HARD-FAILS if underpowered.")
    ap.add_argument("--max-new-tokens", type=int, default=256)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--seed", type=int, default=20260723)
    ap.add_argument("--disk-budget-gb", type=float, default=60.0)
    ap.add_argument("--disk-ceiling-gb", type=float, default=70.0)
    ap.add_argument("--hf-home", default=None)
    ap.add_argument("--venv", default=None)
    ap.add_argument("--out-dir", default=None)
    return ap


def main(argv: Optional[List[str]] = None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)
    axes = list(args.axes)

    if args.bootstrap_b < 10000:
        if not args.allow_underpowered:
            raise SystemExit(
                f"[c2b-adj] FATAL: --bootstrap-b {args.bootstrap_b} < frozen 10000 "
                f"(prereg §5). The confirmatory run requires B>=10000. Pass "
                f"--allow-underpowered to override for a smoke/debug run only.")
        print(f"[c2b-adj] WARNING: --bootstrap-b {args.bootstrap_b} < frozen 10000 "
              f"(prereg §5) but --allow-underpowered was passed; NOT valid for the "
              f"confirmatory adjudication.", flush=True)

    out_dir = Path(args.out_dir) if args.out_dir else (
        _REPO / "results" / f"c2b_adjudication_{args.backend}_{date.today().isoformat()}")
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    t_start = time.time()
    started_at = utcnow()

    if args.backend == "synthetic":
        use_fixture = True  # synthetic backend only makes sense on the offline fixtures
        specs = build_specs_synthetic(axes, use_fixture, args.n_items, args.n_strong)
        sampler_for_axis = synthetic_sampler_factory(use_fixture, args.n_items)
        model = "synthetic-offline"
        hardware = "cpu-offline"
        meta_extra: Dict = {"backend": "synthetic",
                            "note": "offline no-torch pipeline smoke on fixtures"}
    else:
        model = args.model or DEFAULT_MODEL
        guard_paths = default_guard_paths(args.hf_home, args.venv)
        usage0 = check_disk_budget(guard_paths, args.disk_budget_gb, args.disk_ceiling_gb)
        print(f"[c2b-adj] disk pre-run: {usage0.message}", flush=True)
        specs, hf_meta = build_specs_hf(
            axes, model, args.use_fixture, args.n_items, args.n_strong,
            args.n_extraction, args.seed, out_dir)
        # abort before spending on generation if the model download blew the budget
        usage_mid = check_disk_budget(guard_paths, args.disk_budget_gb,
                                      args.disk_ceiling_gb, raise_on_over=True)
        print(f"[c2b-adj] disk post-C1 (model loaded): {usage_mid.message}", flush=True)
        sampler_for_axis = hf_sampler_factory(model, args.max_new_tokens,
                                              args.temperature, args.seed)
        hardware = f"{p0._pick_device()}-{p0._pick_dtype()}"
        meta_extra = {"backend": "hf", **hf_meta}

    report = adj.adjudicate(
        sampler_for_axis, specs, k=adj.K_SAMPLES, alpha_grid=adj.ALPHA_GRID,
        bootstrap_b=args.bootstrap_b, ci_level=adj.BONFERRONI_CI_LEVEL,
        delta=adj.DELTA, coherence_max_ratio=adj.COHERENCE_MAX_RATIO,
        dev_fraction=adj.DEV_FRACTION, seed=args.seed)

    wall = time.time() - t_start
    meta = {
        "model": model, "hardware": hardware, "run_type": "exploratory",
        "valid_for_paper": False, "protocol_frozen": True,
        "prereg": "docs/ledgers/prereg-c2b-adjudication.md (FROZEN 2026-07-23)",
        "started_at": started_at, "generated_at": utcnow(),
        "wall_clock_seconds": round(wall, 2), "platform": platform.platform(),
        "use_fixture": bool(args.use_fixture) or args.backend == "synthetic",
        **meta_extra,
    }
    json_path = write_results(report, out_dir, meta)
    exp_id = register(report, out_dir, json_path, meta, args.seed)

    if args.backend == "hf":
        guard_paths = default_guard_paths(args.hf_home, args.venv)
        usage1 = check_disk_budget(guard_paths, args.disk_budget_gb,
                                   args.disk_ceiling_gb, raise_on_over=False)
        print(f"[c2b-adj] disk post-run: {usage1.message}", flush=True)

    print(f"\n[c2b-adj] VERDICT: {report.verdict}  "
          f"(axes passing: {sum(1 for v in report.axis_passes.values() if v)}/3)", flush=True)
    print(f"[c2b-adj] wrote {_rel(json_path)}  (exp {exp_id})  wall={wall:.1f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
