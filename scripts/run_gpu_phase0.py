"""Unified GPU Phase-0 runner: C1 facade + C2b behavioral reachability (EXPLORATORY).

Designed for a borrowed A800 session that must be PURE COMPUTE (D-0020): no live
debugging. Everything here is implemented + CPU-smoke-tested offline first; on the
A800 it just runs. Default model is Qwen2.5-7B-Instruct (Apache-2.0, ungated);
override with --model for the CPU/1.5B smoke.

Pipeline
--------
1. DISK GUARD — measure HF_HOME + venv against a budget (default 60 GB, hard
   ceiling 70 GB) BEFORE the run, AFTER the model is loaded (between C1 and C2b),
   and AFTER C2b; the post-load and post-run checks ABORT if the footprint is
   at/over the ceiling so the borrowed box's disk is never blown.
2. C1 FACADE — reuse scripts.run_c1_facade.run (same-origin facade_ratio + CI),
   written under <out>/c1/.
3. C2b REACHABILITY — for each axis, extract the CAA direction at C1's chosen
   layer, then run the prompt-ceiling / steer-only / conflict harness with a real
   SteeredHFBackend and the automatic behavioral proxies. Does latent steering
   reach a behavioral region beyond the bounded prompt ceiling?

Everything is EXPLORATORY: valid_for_paper=false, protocol NOT frozen, honest
wall-clock. Results are small JSON + a markdown summary + registry rows.
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

from cognitive_console.activations.provider import HFActivationProvider
from cognitive_console.steering.extract import mean_difference_vector
from cognitive_console.steering.generate import SteeredHFBackend, unit_vector
from cognitive_console.experiments.reachability import AxisSteerSpec, run_c2b_axis
from cognitive_console.experiments.behavior import behavior_score
from cognitive_console.ops.disk_guard import check_disk_budget, default_guard_paths
from cognitive_console.config import config_hash
from cognitive_console.registry import ExperimentRecord, ExperimentRegistry
from cognitive_console.lineage import git_commit, new_experiment_id, utcnow
from cognitive_console.manifest import ArtifactManifest, write_manifest

from scripts import run_c1_facade as c1

DEFAULT_MODEL = "Qwen/Qwen2.5-7B-Instruct"
DEFAULT_AXES = ["deliberation", "skepticism", "uncertainty_awareness", "focus"]

# The FULL authored strong-prompt set per axis (data/strongest_prompts/*.jsonl).
# The prompt ceiling is best-of these static, human-authored prompts — NOT OPRO —
# so it is a conservative UNDER-estimate of true bounded-prompt reach.
DEFAULT_N_STRONG = 16

# Prominent honesty caveat (from the merge-blocking audit) carried on the combined
# summary + registry so no downstream reader can over-read the exploratory C2b numbers.
C2B_HONESTY_CAVEAT = (
    "C2b uses crude lexical/length proxies that share a basis with the steering "
    "direction; these numbers are an EXPLORATORY lexical-shift signal ONLY and "
    "CANNOT support a 'latent reaches beyond the bounded-prompt ceiling' claim "
    "without an orthogonal non-lexical proxy + variance estimate. "
    "focus/deliberation are length-confounded; focus is untrustworthy. Single "
    "greedy sample per cell — do not over-read small margins."
)


def _is_unstable_axis(stable_layer_found: object) -> bool:
    """True unless C1 explicitly confirmed a stable layer for this axis.

    Treats both an explicit ``False`` (e.g. focus at 1.5B) and an unknown/None
    (no C1, unconfirmed) as unstable, so a degenerate axis is never silently
    steered and counted in a headline claim.
    """
    return stable_layer_found is not True


def _c2b_aggregate(axis_rows: List[Dict[str, object]]) -> Dict[str, object]:
    """Headline aggregate that EXCLUDES axes on an unstable/unconfirmed C1 layer."""
    stable = [r for r in axis_rows if not r.get("c2b_on_unstable_layer")]
    return {
        "n_axes": len(axis_rows),
        "n_axes_on_unstable_layer": int(
            sum(1 for r in axis_rows if r.get("c2b_on_unstable_layer"))
        ),
        "n_axes_counted_for_headline": len(stable),
        "n_axes_steer_beyond_prompt_ceiling": int(
            sum(1 for r in stable if r.get("reaches_beyond_prompt_ceiling"))
        ),
        "headline_excludes_unstable": True,
        "headline_note": (
            "'axes where steer reaches beyond ceiling' EXCLUDES axes with "
            "c2b_on_unstable_layer=true (unstable/unconfirmed C1 layer); those "
            "axes are still recorded but never counted in the headline."
        ),
    }


def _rel(path: Path) -> str:
    """Repo-relative POSIX path if under the repo, else the absolute path."""
    p = Path(path).resolve()
    try:
        return str(p.relative_to(_REPO)).replace("\\", "/")
    except ValueError:
        return str(p).replace("\\", "/")


def _extract_direction(provider: HFActivationProvider, axis: str, layer: int,
                       n_extraction: int, seed: int) -> np.ndarray:
    """Unit CAA direction for `axis` at `layer` (extraction split only, warm cache)."""
    pairs = c1.load_axis_pairs(axis)
    split = c1.make_split(list(pairs.pos.keys()), n_extraction=n_extraction, seed=seed)
    ext_pos = [pairs.pos[p] for p in split.extraction_ids]
    ext_neg = [pairs.neg[p] for p in split.extraction_ids]
    pos_acts = provider.get_activations(ext_pos, layer).astype(np.float64)
    neg_acts = provider.get_activations(ext_neg, layer).astype(np.float64)
    return unit_vector(mean_difference_vector(pos_acts, neg_acts))


def run_c2b(
    model: str,
    axes: List[str],
    c1_payload: Dict[str, object],
    cache_dir: Path,
    alphas: List[float],
    n_strong: int,
    max_new_tokens: int,
    n_extraction: int,
    seed: int,
) -> Dict[str, object]:
    """Run the C2b reachability harness for every axis on the real model."""
    provider = HFActivationProvider(model, device=_pick_device(), dtype="float32",
                                    cache_dir=str(cache_dir))
    gen = SteeredHFBackend(model, device=provider.device, dtype=_pick_dtype())

    c1_by_axis = {r["axis"]: r for r in c1_payload["axes"]}  # type: ignore[index]
    neutral = c1.load_neutral_prompts()[0]

    axis_rows: List[Dict[str, object]] = []
    for axis in axes:
        t0 = time.time()
        c1_row = c1_by_axis.get(axis, {})
        layer = int(c1_row.get("chosen_layer", max(1, provider.available_layers()[-1] // 2)))
        direction = _extract_direction(provider, axis, layer, n_extraction, seed)

        strong = c1.load_strongest_prompts(axis)
        strong_prompts = list(zip(strong.ids, strong.texts))[:n_strong]
        spec = AxisSteerSpec(
            axis=axis, direction=direction, layer=layer,
            strong_prompts=strong_prompts, neutral_prompt=neutral,
        )
        res = run_c2b_axis(gen, spec, alphas=alphas, max_new_tokens=max_new_tokens,
                           scorer=behavior_score)
        row = res.to_row()
        row["c1_chosen_layer"] = layer
        stable = c1_row.get("stable_layer_found")
        row["c1_stable_layer_found"] = stable
        row["c2b_on_unstable_layer"] = _is_unstable_axis(stable)
        axis_rows.append(row)
        print(f"[c2b] axis={axis:<24} layer={layer:>3} "
              f"prompt_ceiling={res.prompt_ceiling:.3f} steer_max={res.steer_only_max:.3f} "
              f"beyond={res.reaches_beyond_prompt_ceiling} "
              f"unstable_layer={row['c2b_on_unstable_layer']} ({time.time()-t0:.1f}s)",
              flush=True)

    return {
        "kind": "c2b_reachability_pilot",
        "type": "EXPLORATORY",
        "valid_for_paper": False,
        "protocol_frozen": False,
        "model": model,
        "alphas": alphas,
        "n_strong": n_strong,
        "max_new_tokens": max_new_tokens,
        "neutral_prompt": neutral,
        "prompt_ceiling_label": (
            f"prompt ceiling = best-of-{n_strong} static authored prompts, NOT OPRO "
            "— an UNDER-estimate of true prompt reach (conservative for the C2b "
            "comparison)"
        ),
        "c2b_honesty_caveat": C2B_HONESTY_CAVEAT,
        "behavior_proxy_note": (
            "Behavior measured by CRUDE lexical proxies (experiments.behavior), NOT "
            "validated instruments. EXPLORATORY — no frozen verdict."
        ),
        "axes": axis_rows,
        "aggregate": _c2b_aggregate(axis_rows),
    }


def _pick_device() -> str:
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return "cpu"


def _pick_dtype() -> str:
    return "float16" if _pick_device() == "cuda" else "float32"


def _write_c2b(payload: Dict[str, object], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "c2b_reachability_results.json"
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)

    lines: List[str] = []
    lines.append("# C2b Behavioral Reachability Pilot — EXPLORATORY (protocol NOT frozen)\n")
    lines.append(f"- model: `{payload['model']}`")
    lines.append(f"- alphas: {payload['alphas']}   n_strong: {payload['n_strong']}   "
                 f"max_new_tokens: {payload['max_new_tokens']}")
    lines.append(f"- valid_for_paper: **{payload['valid_for_paper']}**")
    lines.append(f"- prompt ceiling definition: {payload['prompt_ceiling_label']}")
    lines.append(f"- {payload['behavior_proxy_note']}")
    lines.append("")
    lines.append(f"> **HONESTY CAVEAT (audit):** {payload['c2b_honesty_caveat']}")
    lines.append("")
    lines.append("## Does latent steering reach behavior BEYOND the bounded prompt ceiling?\n")
    lines.append("| axis | layer | prompt ceiling | steer-only max | beyond? | margin | unstable layer? | conflict winner (max α) |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for r in payload["axes"]:  # type: ignore[index]
        conf = r["conflict"][-1] if r["conflict"] else {}
        lines.append(
            f"| {r['axis']} | {r['layer']} | {r['prompt_ceiling']:.3f} | "
            f"{r['steer_only_max']:.3f} | "
            f"{'YES' if r['reaches_beyond_prompt_ceiling'] else 'no'} | "
            f"{r['beyond_margin']:+.3f} | "
            f"{'UNSTABLE' if r.get('c2b_on_unstable_layer') else 'ok'} | "
            f"{conf.get('winner', '—')} |"
        )
    agg = payload["aggregate"]  # type: ignore[index]
    lines.append("")
    lines.append(f"- axes where steer reaches beyond the prompt ceiling: "
                 f"{agg['n_axes_steer_beyond_prompt_ceiling']}/{agg['n_axes_counted_for_headline']} "
                 f"(headline EXCLUDES {agg['n_axes_on_unstable_layer']} axis/axes on an "
                 f"unstable C1 layer; {agg['n_axes']} axes total)")
    lines.append(f"- {agg['headline_note']}")
    lines.append("")
    lines.append("## Conflict landings (prompt UP vs latent steer DOWN)\n")
    lines.append("| axis | α | prompt pole | steer pole | behavior | landing (raw) | winner |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in payload["axes"]:  # type: ignore[index]
        for c in r["conflict"]:
            lines.append(
                f"| {r['axis']} | {c['alpha']} | {c['prompt_pole']:.3f} | "
                f"{c['steer_pole']:.3f} | {c['behavior']:.3f} | "
                f"{c['landing_fraction_raw']:.3f} | {c['winner']} |"
            )
    summary_path = out_dir / "c2b_reachability_summary.md"
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return json_path


def _register_c2b(payload: Dict[str, object], out_dir: Path, json_path: Path,
                  seed: int, hardware: str) -> str:
    reg_path = out_dir / "experiment-registry.yaml"
    registry = ExperimentRegistry(str(reg_path))
    cfg = {
        "kind": "c2b_reachability_pilot",
        "model": payload["model"],
        "axes": [r["axis"] for r in payload["axes"]],  # type: ignore[index]
        "alphas": payload["alphas"],
        "n_strong": payload["n_strong"],
        "max_new_tokens": payload["max_new_tokens"],
        "seed": seed,
    }
    cfg_hash = config_hash(cfg)
    summary_metrics = {
        r["axis"]: {
            "layer": r["layer"],
            "prompt_ceiling": r["prompt_ceiling"],
            "steer_only_max": r["steer_only_max"],
            "reaches_beyond_prompt_ceiling": r["reaches_beyond_prompt_ceiling"],
            "beyond_margin": r["beyond_margin"],
        }
        for r in payload["axes"]  # type: ignore[index]
    }
    summary_metrics["_aggregate"] = payload["aggregate"]  # type: ignore[index]

    exp_id = new_experiment_id(registry, "c2b-reach", cfg_hash)
    record = ExperimentRecord(
        experiment_id=exp_id,
        hypothesis_id="H2",
        claim_ids=["C2b"],
        type="exploratory",
        status="done",
        code_commit=git_commit(str(_REPO)),
        config_hash=cfg_hash,
        model=str(payload["model"]),
        dataset="data/strongest_prompts/*.jsonl + data/contrast_pairs/*.jsonl (CAA dir)",
        seed=seed,
        hardware=hardware,
        started_at=utcnow(),
        ended_at=utcnow(),
        exit_code=0,
        summary_metrics=summary_metrics,
        artifacts=[_rel(json_path)],
        valid_for_paper=False,
        validation_notes=(
            "EXPLORATORY C2b behavioral reachability pilot. Steered generation "
            "(residual activation-addition of alpha*unit-CAA-direction at C1's "
            "chosen layer) + CRUDE automatic behavioral proxies (NOT validated "
            "instruments). Measures whether latent steering reaches a behavioral "
            "region beyond a bounded prompt ceiling. Protocol NOT frozen; the proxy "
            "crudeness is a stated limitation the Manager must weigh. "
            "HONESTY CAVEAT: " + C2B_HONESTY_CAVEAT
        ),
    )
    registry.append(record)
    manifest = ArtifactManifest(
        artifact_id="c2b-reachability-pilot-table",
        supports_claims=["C2b"],
        source_experiments=[exp_id],
        aggregation_script="scripts/run_gpu_phase0.py",
        aggregation_commit=git_commit(str(_REPO)),
        output_file=_rel(json_path),
        raw_data_hash=c1._sha256_file(json_path),
        last_verified=utcnow(),
        verdict="pending",
    )
    write_manifest(str(out_dir / "c2b_reachability_table.manifest.yaml"), manifest)
    return exp_id


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Unified GPU Phase-0 runner (C1 + C2b, EXPLORATORY)")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--axes", nargs="*", default=DEFAULT_AXES)
    ap.add_argument("--scan-step", type=int, default=2)
    ap.add_argument("--n-extraction", type=int, default=28)
    ap.add_argument("--seed", type=int, default=20260723)
    ap.add_argument("--n-null", type=int, default=2000)
    ap.add_argument("--alphas", type=float, nargs="*", default=[4.0, 8.0, 16.0],
                    help="C2b steering coefficients (absolute, unit direction)")
    ap.add_argument("--n-strong", type=int, default=DEFAULT_N_STRONG,
                    help="number of authored strong prompts per axis for the prompt "
                         "ceiling (default 16 = the FULL authored set; best-of these "
                         "static prompts, NOT OPRO)")
    ap.add_argument("--max-new-tokens", type=int, default=128)
    ap.add_argument("--disk-budget-gb", type=float, default=60.0)
    ap.add_argument("--disk-ceiling-gb", type=float, default=70.0)
    ap.add_argument("--hf-home", default=None, help="HF_HOME to disk-guard (default: env)")
    ap.add_argument("--venv", default=None, help="venv dir to disk-guard (default: $VIRTUAL_ENV)")
    ap.add_argument("--skip-c1", action="store_true", help="run only the C2b pilot")
    ap.add_argument("--out-dir", default=None)
    return ap


def main(argv: Optional[List[str]] = None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)

    out_dir = Path(args.out_dir) if args.out_dir else (
        _REPO / "results" / f"gpu_7b_{date.today().isoformat()}"
    )
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    guard_paths = default_guard_paths(args.hf_home, args.venv)

    t_start = time.time()
    # --- DISK GUARD (pre-run) -------------------------------------------------
    usage0 = check_disk_budget(guard_paths, args.disk_budget_gb, args.disk_ceiling_gb)
    print(f"[gpu] disk pre-run: {usage0.message}", flush=True)

    hardware = f"{_pick_device()}-{_pick_dtype()}"
    print(f"[gpu] device={hardware} model={args.model} out={out_dir}", flush=True)

    # --- C1 FACADE ------------------------------------------------------------
    c1_payload: Dict[str, object]
    if args.skip_c1:
        c1_payload = {"axes": [{"axis": a} for a in args.axes]}
        print("[gpu] --skip-c1: C2b will use mid-network fallback layers", flush=True)
    else:
        c1_out = out_dir / "c1"
        c1_payload = c1.run(
            model=args.model, axes=args.axes, scan_step=args.scan_step,
            n_extraction=args.n_extraction, seed=args.seed, n_null=args.n_null,
            out_dir=c1_out, ram_floor_mb=0.0,
        )
        c1_json, c1_summary = c1._write_results(c1_payload, c1_out, args.seed)
        c1_exp = c1._register(c1_payload, c1_out, c1_json, args.seed)
        print(f"[gpu] C1 done -> {c1_json} (exp {c1_exp})", flush=True)

    # --- DISK GUARD (post-C1 / model downloaded) ------------------------------
    # The pre-run check above measured a near-empty box; the model weights land
    # during C1. Now that the model is on disk, ABORT if we are over the ceiling
    # BEFORE spending more on C2b (a runaway download can never blow the box).
    usage_mid = check_disk_budget(guard_paths, args.disk_budget_gb, args.disk_ceiling_gb,
                                  raise_on_over=True)
    print(f"[gpu] disk post-C1 (model loaded): {usage_mid.message}", flush=True)

    # --- C2b REACHABILITY -----------------------------------------------------
    cache_dir = out_dir / "c1" / "activations" / "cache"
    c2b_payload = run_c2b(
        model=args.model, axes=args.axes, c1_payload=c1_payload, cache_dir=cache_dir,
        alphas=list(args.alphas), n_strong=args.n_strong,
        max_new_tokens=args.max_new_tokens, n_extraction=args.n_extraction, seed=args.seed,
    )
    wall = time.time() - t_start
    c2b_payload["wall_clock_seconds"] = round(wall, 2)
    c2b_payload["generated_at"] = utcnow()
    c2b_payload["platform"] = platform.platform()
    c2b_payload["hardware"] = hardware
    c2b_out = out_dir / "c2b"
    c2b_json = _write_c2b(c2b_payload, c2b_out)
    c2b_exp = _register_c2b(c2b_payload, c2b_out, c2b_json, args.seed, hardware)

    # --- DISK GUARD (post-run) ------------------------------------------------
    # Measure for the summary WITHOUT raising, so the (already-written) artifacts
    # + summary are recorded, then do a final ABORT check below.
    usage1 = check_disk_budget(guard_paths, args.disk_budget_gb, args.disk_ceiling_gb,
                               raise_on_over=False)
    print(f"[gpu] disk post-run: {usage1.message}", flush=True)

    # --- Combined summary -----------------------------------------------------
    combined = {
        "kind": "gpu_phase0_run",
        "type": "EXPLORATORY",
        "valid_for_paper": False,
        "model": args.model,
        "hardware": hardware,
        "wall_clock_seconds": round(wall, 2),
        "generated_at": utcnow(),
        "platform": platform.platform(),
        "disk_pre_run_gb": usage0.total_gb,
        "disk_post_c1_gb": usage_mid.total_gb,
        "disk_post_run_gb": usage1.total_gb,
        "c1_dir": "c1/",
        "c2b_dir": "c2b/",
        "c2b_experiment_id": c2b_exp,
        "c2b_honesty_caveat": C2B_HONESTY_CAVEAT,
        "prompt_ceiling_label": c2b_payload["prompt_ceiling_label"],
    }
    with open(out_dir / "run_summary.json", "w", encoding="utf-8") as fh:
        json.dump(combined, fh, indent=2)
    print(f"[gpu] C2b done -> {c2b_json} (exp {c2b_exp})", flush=True)
    print(f"[gpu] TOTAL wall-clock: {wall:.1f}s. Wrote {out_dir}", flush=True)

    # --- DISK GUARD (final abort) ---------------------------------------------
    # Artifacts + summary are safely on disk; now ABORT (non-zero) if the run
    # ended over the hard ceiling so the operator stops before reusing the box.
    check_disk_budget(guard_paths, args.disk_budget_gb, args.disk_ceiling_gb,
                      raise_on_over=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
