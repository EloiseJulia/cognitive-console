"""Aggregate multi-seed C2 robustness arm results across seeds.

Reads arm_matrix_summary.json files from a manifest (or CLI arguments), one
per seed run, and produces:
  - A per-seed arm verdict table (seed → arm_verdict, per-cell axes_passed).
  - A per-cell per-axis mean(d) / CI summary (loaded from each cell's
    c2b_adjudication_results.json alongside the arm summary).

ALL numbers are read from JSON artifacts.  Nothing is hand-filled.
Output: <out_dir>/multiseed_c2_aggregate.json + multiseed_c2_aggregate.md.

Usage
-----
  python scripts/aggregate_multiseed_c2.py \\
      --manifest path/to/multiseed_manifest.json \\
      [--out-dir results/multiseed_c2]

Manifest format (JSON array, one object per seed run):
  [
    {
      "seed": 20260723,
      "arm_summary_json": "results/arm_full/arm_matrix_summary.json"
    },
    ...
  ]

Alternatively pass --arm-summaries directly:
  python scripts/aggregate_multiseed_c2.py \\
      --arm-summaries seed1/arm_matrix_summary.json seed2/arm_matrix_summary.json \\
      --seeds 20260723 20260724
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import timezone, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_REPO = Path(__file__).resolve().parents[1]
_FROZEN_AXES = ["deliberation", "skepticism", "uncertainty_awareness"]
_FROZEN_CELL_KEYS = ["caa__qwen2.5-7b", "caa__llama3-8b", "iti__qwen2.5-7b", "iti__llama3-8b"]

# Number of pre-registered seeds (20260723–20260727).
# DROP_SINGLE_SEED_CAVEAT requires ALL N_FROZEN seeds to be present; fewer seeds → INSUFFICIENT_SEEDS.
N_FROZEN: int = 5
# Frozen E-0006 reference artifact directory for harness reproduction numeric check.
_E0006_REF_PATH: Path = _REPO / "results" / "arm_full"
# Absolute tolerance for E-0006 numeric reproduction check (mean_diff / ci_lo / ci_hi).
_HARNESS_REPRO_TOL: float = 1e-6


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


# --------------------------------------------------------------------------- #
# Loading helpers
# --------------------------------------------------------------------------- #

def load_arm_summary(path: Path) -> Dict[str, Any]:
    """Load and validate an arm_matrix_summary.json."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if "arm_verdict" not in data:
        raise ValueError(f"missing 'arm_verdict' in {path}")
    if "cells" not in data:
        raise ValueError(f"missing 'cells' in {path}")
    return data


def _find_cell_result_json(arm_summary_path: Path, cell_key: str) -> Optional[Path]:
    """Find the c2b_adjudication_results.json for a cell relative to the arm summary."""
    arm_dir = arm_summary_path.parent
    candidate = arm_dir / f"cell_{cell_key}" / "c2b_adjudication_results.json"
    return candidate if candidate.exists() else None


def _extract_axis_stats(cell_result: Dict[str, Any], axis: str) -> Dict[str, Any]:
    """Extract mean_diff / ci_lo / ci_hi / passed for one axis from a cell result JSON."""
    for row in cell_result.get("axes", []):
        if row.get("axis") == axis:
            return {
                "mean_diff": row.get("mean_diff"),
                "ci_lo": row.get("ci_lo"),
                "ci_hi": row.get("ci_hi"),
                "ci_level": row.get("ci_level"),
                "passed": bool(row.get("passed", False)),
                "coherence_ok": bool(row.get("coherence_ok", True)),
                "frozen_alpha": row.get("dev_selection", {}).get("frozen_alpha"),
            }
    return {"mean_diff": None, "ci_lo": None, "ci_hi": None,
            "ci_level": None, "passed": False, "coherence_ok": None, "frozen_alpha": None}


# --------------------------------------------------------------------------- #
# E-0006 harness numeric reproduction check
# --------------------------------------------------------------------------- #

def _load_e0006_cell_stats(ref_dir: Path) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """Load frozen E-0006 reference stats for all 4 cells × 3 axes.

    Returns ``{cell_key: {axis: {mean_diff, ci_lo, ci_hi}}}``.
    Values are always read from artifact files; nothing is hard-coded.
    """
    stats: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for cell_key in _FROZEN_CELL_KEYS:
        cell_json = ref_dir / f"cell_{cell_key}" / "c2b_adjudication_results.json"
        if not cell_json.exists():
            raise FileNotFoundError(f"E-0006 reference cell JSON not found: {cell_json}")
        data = json.loads(cell_json.read_text(encoding="utf-8"))
        stats[cell_key] = {}
        for row in data.get("axes", []):
            axis = row.get("axis")
            if axis in _FROZEN_AXES:
                stats[cell_key][axis] = {
                    "mean_diff": row.get("mean_diff"),
                    "ci_lo": row.get("ci_lo"),
                    "ci_hi": row.get("ci_hi"),
                }
    return stats


def _verify_harness_repro_numeric(
    seed_record: Dict[str, Any],
    ref_dir: Path,
    tol: float = _HARNESS_REPRO_TOL,
) -> Tuple[bool, List[Dict[str, Any]]]:
    """Compare seed=20260723 cell axis stats against frozen E-0006 reference.

    Returns ``(ok, mismatches)``.  ``ok=True`` iff all 4 cells × 3 axes have
    mean_diff, ci_lo, ci_hi within *tol* of the reference.
    Reference values are always read from artifact files; nothing is hard-coded.
    """
    try:
        ref_stats = _load_e0006_cell_stats(ref_dir)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        return False, [{"reason": f"e0006_ref_load_error: {exc}"}]

    mismatches: List[Dict[str, Any]] = []
    for c in seed_record.get("cells", []):
        cell_key = c.get("cell_key", "")
        if cell_key not in ref_stats:
            continue
        for axis in _FROZEN_AXES:
            new_stats = c.get("axis_stats", {}).get(axis, {})
            ref = ref_stats.get(cell_key, {}).get(axis, {})
            for field in ("mean_diff", "ci_lo", "ci_hi"):
                nv = new_stats.get(field)
                rv = ref.get(field)
                if nv is None or rv is None:
                    mismatches.append({
                        "cell_key": cell_key, "axis": axis, "field": field,
                        "reason": "missing_value", "new": nv, "ref": rv,
                    })
                elif abs(float(nv) - float(rv)) > tol:
                    mismatches.append({
                        "cell_key": cell_key, "axis": axis, "field": field,
                        "reason": "numeric_mismatch",
                        "new": nv, "ref": rv,
                        "abs_diff": abs(float(nv) - float(rv)),
                        "tol": tol,
                    })
    return len(mismatches) == 0, mismatches

def build_seed_record(
    seed: int,
    arm_summary_path: Path,
    arm_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Build a per-seed record: arm verdict + per-cell axis stats."""
    cells_by_key: Dict[str, Dict[str, Any]] = {}
    for c in arm_data.get("cells", []):
        cells_by_key[str(c["cell_key"])] = c

    cell_records: List[Dict[str, Any]] = []
    for cell_key in _FROZEN_CELL_KEYS:
        cell_summary = cells_by_key.get(cell_key, {})
        axis_stats: Dict[str, Dict[str, Any]] = {}

        # Try to load per-axis mean(d)/CI from the detailed cell result JSON.
        cell_result_path = _find_cell_result_json(arm_summary_path, cell_key)
        if cell_result_path is not None:
            try:
                cell_result = json.loads(cell_result_path.read_text(encoding="utf-8"))
                for axis in _FROZEN_AXES:
                    axis_stats[axis] = _extract_axis_stats(cell_result, axis)
            except (json.JSONDecodeError, OSError) as exc:
                axis_stats = {a: {"error": str(exc)} for a in _FROZEN_AXES}
        else:
            axis_stats = {a: {"note": "cell_result_json_not_found"} for a in _FROZEN_AXES}

        cell_records.append({
            "cell_key": cell_key,
            "axes_passed": int(cell_summary.get("axes_passed", 0)),
            "cell_verdict": str(cell_summary.get("verdict", "UNKNOWN")),
            "axis_passes": dict(cell_summary.get("axis_passes", {})),
            "axis_stats": axis_stats,
        })

    return {
        "seed": int(seed),
        "arm_summary_path": str(arm_summary_path),
        "arm_verdict": str(arm_data.get("arm_verdict", "UNKNOWN")),
        "harness_repro_ok": arm_data.get("harness_repro_ok"),
        "zero_pass_cells": int(arm_data.get("zero_pass_cells", 0)),
        "any_cell_has_pass": bool(arm_data.get("any_cell_has_pass", False)),
        "cells": cell_records,
    }


# --------------------------------------------------------------------------- #
# Cross-seed aggregation
# --------------------------------------------------------------------------- #

def aggregate_across_seeds(
    seed_records: List[Dict[str, Any]],
    e0006_ref_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Compute cross-seed summary statistics for each cell × axis."""
    n_seeds = len(seed_records)
    if n_seeds < 2:
        raise ValueError(
            f"aggregate_across_seeds requires at least 2 seed records; got {n_seeds}. "
            f"For single-seed harness validation, compare directly against the E-0006 "
            f"reference at {_E0006_REF_PATH}. Do not use the aggregation DROP path for "
            f"a single seed — harness check should be run against E-0006 directly."
        )

    # Per-seed arm verdict tally
    verdict_counts: Dict[str, int] = {}
    for r in seed_records:
        v = str(r["arm_verdict"])
        verdict_counts[v] = verdict_counts.get(v, 0) + 1

    # Per-cell per-axis stats across seeds
    cell_axis_stats: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for cell_key in _FROZEN_CELL_KEYS:
        cell_axis_stats[cell_key] = {}
        for axis in _FROZEN_AXES:
            mean_diffs: List[float] = []
            ci_los: List[float] = []
            ci_his: List[float] = []
            n_pass = 0
            for r in seed_records:
                for c in r.get("cells", []):
                    if c["cell_key"] != cell_key:
                        continue
                    astats = c.get("axis_stats", {}).get(axis, {})
                    md = astats.get("mean_diff")
                    cl = astats.get("ci_lo")
                    ch = astats.get("ci_hi")
                    passed = bool(astats.get("passed", False))
                    if md is not None:
                        mean_diffs.append(float(md))
                    if cl is not None:
                        ci_los.append(float(cl))
                    if ch is not None:
                        ci_his.append(float(ch))
                    if passed:
                        n_pass += 1
            cell_axis_stats[cell_key][axis] = {
                "n_seeds_with_data": len(mean_diffs),
                "n_seeds_pass": n_pass,
                "mean_diff_values": mean_diffs,
                "mean_diff_across_seeds": (
                    # descriptive only — not used in any verdict condition (see prereg §4b)
                    sum(mean_diffs) / len(mean_diffs) if mean_diffs else None
                ),
                "ci_lo_values": ci_los,
                "ci_hi_values": ci_his,
                "all_ci_negative": (
                    all(ch < 0 for ch in ci_his) if ci_his else None
                ),
            }

    # Caveat status rule (see prereg-c2b-multiseed-DRAFT.md §4a)
    n_seeds_non_transfer = verdict_counts.get("NON_TRANSFER_GENERALIZED", 0)
    uncertainty_ci_negative_counts: Dict[str, int] = {
        ck: 0 for ck in _FROZEN_CELL_KEYS
    }
    # any_true_pass_details: unconditional surfacing of every (seed,cell,axis) true PASS
    # (prereg §4c). This list is always present in the output; empty means no passes.
    any_true_pass_details: List[Dict[str, Any]] = []
    # strong_positive_flip_details: kept for backward-compat; same events, fewer fields.
    strong_positive_flip_details: List[Dict[str, Any]] = []
    for r in seed_records:
        for c in r.get("cells", []):
            cell_key = str(c.get("cell_key"))
            if cell_key not in _FROZEN_CELL_KEYS:
                continue
            ua = c.get("axis_stats", {}).get("uncertainty_awareness", {})
            ua_ci_hi = ua.get("ci_hi")
            if ua_ci_hi is not None and float(ua_ci_hi) < 0:
                uncertainty_ci_negative_counts[cell_key] += 1

            axis_stats = c.get("axis_stats", {})
            axis_passes = c.get("axis_passes", {})
            for axis in _FROZEN_AXES:
                astats = axis_stats.get(axis, {})
                axis_stat_passed = bool(astats.get("passed", False))
                axis_summary_passed = bool(axis_passes.get(axis, False))
                if axis_stat_passed or axis_summary_passed:
                    strong_positive_flip_details.append({
                        "seed": int(r["seed"]),
                        "cell_key": cell_key,
                        "axis": axis,
                    })
                    any_true_pass_details.append({
                        "seed": int(r["seed"]),
                        "cell_key": cell_key,
                        "axis": axis,
                        "mean_diff": astats.get("mean_diff"),
                        "ci_lo": astats.get("ci_lo"),
                        "ci_hi": astats.get("ci_hi"),
                    })

    any_strong_positive_flip = bool(strong_positive_flip_details)

    # Per-cell §4c flags: mark cells that had ≥1 true pass (per-seed, not pooled).
    cells_with_true_pass = {e["cell_key"] for e in any_true_pass_details}
    for ck in _FROZEN_CELL_KEYS:
        cell_axis_stats[ck]["single_seed_positive_surfaced"] = ck in cells_with_true_pass
        cell_axis_stats[ck]["positive_surfaced_passes"] = [
            e for e in any_true_pass_details if e["cell_key"] == ck
        ]

    uncertainty_harm_ci_negative_all_cells_all_seeds = all(
        uncertainty_ci_negative_counts[ck] == n_seeds
        for ck in _FROZEN_CELL_KEYS
    )
    uncertainty_harm_ci_negative_all_cells_3_of_5 = all(
        uncertainty_ci_negative_counts[ck] >= 3
        for ck in _FROZEN_CELL_KEYS
    )
    strict_all_non_transfer_generalized = (n_seeds_non_transfer == n_seeds)
    robust_4_of_5_non_transfer_generalized = (n_seeds_non_transfer >= 4)

    harness_fail_reasons: List[Dict[str, Any]] = []
    for r in seed_records:
        if int(r.get("seed", -1)) != 20260723:
            continue
        # Numeric reproduction check against frozen E-0006 artifact.
        # Only runs when e0006_ref_dir is provided (e.g., from main()).
        if e0006_ref_dir is not None:
            ok, mismatches = _verify_harness_repro_numeric(r, e0006_ref_dir)
            if not ok:
                harness_fail_reasons.append({
                    "seed": 20260723,
                    "reason": "e0006_numeric_repro_fail",
                    "mismatches": mismatches,
                })
        if str(r.get("arm_verdict")) != "NON_TRANSFER_GENERALIZED":
            harness_fail_reasons.append({
                "seed": 20260723,
                "reason": "arm_verdict_not_non_transfer_generalized",
                "arm_verdict": r.get("arm_verdict"),
            })

    if harness_fail_reasons:
        caveat_status = "KILL_HARNESS"
    elif (
        strict_all_non_transfer_generalized
        and uncertainty_harm_ci_negative_all_cells_all_seeds
        and not any_strong_positive_flip
    ):
        if n_seeds == N_FROZEN:
            caveat_status = "DROP_SINGLE_SEED_CAVEAT"
        else:
            # All strict conditions hold but fewer than N_FROZEN seeds are present.
            # Cannot DROP until the full pre-registered seed set is complete.
            caveat_status = "INSUFFICIENT_SEEDS"
    elif (
        robust_4_of_5_non_transfer_generalized
        and uncertainty_harm_ci_negative_all_cells_3_of_5
        and not any_strong_positive_flip
    ):
        caveat_status = "SEED_MOSTLY_ROBUST"
    else:
        caveat_status = "SEED_SENSITIVE"

    return {
        "any_true_pass": any_true_pass_details,
        "has_any_true_pass": bool(any_true_pass_details),
        "n_seeds": n_seeds,
        "arm_verdict_counts": verdict_counts,
        "n_seeds_non_transfer_generalized": n_seeds_non_transfer,
        "caveat_drop_rule": {
            "description": (
                "Caveat status ladder: "
                f"KILL_HARNESS if seed=20260723 fails E-0006 numeric repro check "
                f"(tol={_HARNESS_REPRO_TOL}) or arm_verdict != NON_TRANSFER_GENERALIZED; "
                f"DROP_SINGLE_SEED_CAVEAT iff n_seeds == N_FROZEN={N_FROZEN} AND all seeds are "
                "NON_TRANSFER_GENERALIZED, all 4 cells have uncertainty_awareness CI_hi<0 in all seeds, "
                "and no seed×cell×axis PASS; "
                f"INSUFFICIENT_SEEDS iff strict-all conditions hold but n_seeds < N_FROZEN={N_FROZEN} "
                "(pending remaining seeds — cannot DROP until full seed set present); "
                "SEED_MOSTLY_ROBUST iff >=4/5 seeds are NON_TRANSFER_GENERALIZED, "
                "all 4 cells have uncertainty_awareness CI_hi<0 in >=3/5 seeds, and no strong-positive flip; "
                "else SEED_SENSITIVE."
            ),
            "n_seeds_required_for_drop": N_FROZEN,
            "insufficient_seeds_warning": (
                f"INSUFFICIENT_SEEDS: n_seeds={n_seeds} < N_FROZEN={N_FROZEN}; "
                f"cannot DROP until all {N_FROZEN} pre-registered seeds are present"
                if n_seeds < N_FROZEN else None
            ),
            "strict_all_non_transfer_generalized": strict_all_non_transfer_generalized,
            "non_transfer_in_4_of_5_seeds": robust_4_of_5_non_transfer_generalized,
            "uncertainty_harm_ci_negative_counts_per_cell": uncertainty_ci_negative_counts,
            "uncertainty_harm_ci_negative_all_cells_all_seeds": (
                uncertainty_harm_ci_negative_all_cells_all_seeds
            ),
            "uncertainty_harm_ci_negative_all_cells_3_of_5": (
                uncertainty_harm_ci_negative_all_cells_3_of_5
            ),
            "any_strong_positive_flip": any_strong_positive_flip,
            "strong_positive_flip_details": strong_positive_flip_details,
            "harness_fail_reasons": harness_fail_reasons,
            "outcome": caveat_status,
        },
        "cell_axis_stats": cell_axis_stats,
    }


# --------------------------------------------------------------------------- #
# Markdown output
# --------------------------------------------------------------------------- #

def _fmt(v: Any, fmt: str = ".3f") -> str:
    if v is None:
        return "n/a"
    try:
        return format(float(v), fmt)
    except (TypeError, ValueError):
        return str(v)


def write_aggregate_md(payload: Dict[str, Any], out_path: Path) -> None:
    agg = payload["aggregation"]
    seed_records = payload["seed_records"]
    lines: List[str] = []
    lines.append("# Multi-seed C2 Robustness Aggregation")
    lines.append("")
    lines.append(f"- generated_at: `{payload.get('generated_at')}`")
    lines.append(f"- n_seeds: {agg['n_seeds']}")
    lines.append(f"- arm_verdict_counts: {agg['arm_verdict_counts']}")
    lines.append(f"- n_seeds NON_TRANSFER_GENERALIZED: **{agg['n_seeds_non_transfer_generalized']}**")
    lines.append("")
    # --- §4c: any_true_pass block (unconditional, always at top) ---
    any_tp = agg.get("any_true_pass", [])
    lines.append("## True-pass surfacing (unconditional guard — prereg §4c)")
    lines.append("")
    if not any_tp:
        lines.append(
            "- `any_true_pass: []` — no true pass detected in any seed×cell×axis."
        )
    else:
        lines.append(
            "> ⚠ **TRUE PASSES DETECTED** — negative conclusions for affected cells "
            "are NOT confirmatory. Each true pass is listed below."
        )
        lines.append("")
        lines.append("| seed | cell_key | axis | mean_diff | ci_lo | ci_hi |")
        lines.append("|---|---|---|---|---|---|")
        for tp in any_tp:
            lines.append(
                f"| {tp['seed']} | {tp['cell_key']} | {tp['axis']} "
                f"| {_fmt(tp.get('mean_diff'))} "
                f"| {_fmt(tp.get('ci_lo'))} "
                f"| {_fmt(tp.get('ci_hi'))} |"
            )
        lines.append("")
        cells_flagged = sorted({tp["cell_key"] for tp in any_tp})
        lines.append(
            f"- Cells flagged `single_seed_positive_surfaced`: **{cells_flagged}**"
        )
    lines.append("")
    lines.append("## Caveat-drop evaluation")
    cd = agg["caveat_drop_rule"]
    lines.append(f"- {cd['description']}")
    lines.append(f"- strict all NON_TRANSFER_GENERALIZED: **{cd['strict_all_non_transfer_generalized']}**")
    lines.append(f"- non_transfer in ≥4/5 seeds: **{cd['non_transfer_in_4_of_5_seeds']}**")
    lines.append(
        f"- uncertainty CI_hi<0 counts per cell: "
        f"**{cd['uncertainty_harm_ci_negative_counts_per_cell']}**"
    )
    lines.append(
        f"- uncertainty CI_hi<0 all cells/all seeds: "
        f"**{cd['uncertainty_harm_ci_negative_all_cells_all_seeds']}**"
    )
    lines.append(
        f"- uncertainty CI_hi<0 all cells/≥3 seeds: "
        f"**{cd['uncertainty_harm_ci_negative_all_cells_3_of_5']}**"
    )
    lines.append(f"- any strong-positive flip: **{cd['any_strong_positive_flip']}**")
    lines.append(f"- **Outcome: {cd['outcome']}**")
    lines.append("")
    lines.append("## Per-seed arm verdicts")
    lines.append("")
    lines.append("| seed | arm_verdict | zero_pass_cells |")
    lines.append("|---|---|---|")
    for r in seed_records:
        lines.append(f"| {r['seed']} | {r['arm_verdict']} | {r['zero_pass_cells']} |")
    lines.append("")
    lines.append("## Per-cell per-axis mean(d) across seeds")
    lines.append("")
    for cell_key in _FROZEN_CELL_KEYS:
        lines.append(f"### Cell: `{cell_key}`")
        cell_cs = agg["cell_axis_stats"][cell_key]
        if cell_cs.get("single_seed_positive_surfaced"):
            lines.append("")
            lines.append(
                "> ⚠ **`single_seed_positive_surfaced`** — this cell has ≥1 true pass "
                "in at least one seed×axis; its negative conclusion is NOT confirmatory."
            )
        lines.append("")
        lines.append("| axis | seeds_with_data | n_pass | mean_diff_values | mean_across_seeds | all_CI_hi<0 |")
        lines.append("|---|---|---|---|---|---|")
        for axis in _FROZEN_AXES:
            s = agg["cell_axis_stats"][cell_key][axis]
            vals = ", ".join(_fmt(v) for v in s["mean_diff_values"])
            lines.append(
                f"| {axis} | {s['n_seeds_with_data']} | {s['n_seeds_pass']} | "
                f"[{vals}] | {_fmt(s['mean_diff_across_seeds'])} | {s['all_ci_negative']} |"
            )
        lines.append("")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Aggregate multi-seed C2 robustness arm results (E-0011 family)"
    )
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--manifest",
        type=Path,
        help=(
            "JSON array manifest: [{seed: int, arm_summary_json: str}, ...]. "
            "All numbers read from JSON; no hand-filling."
        ),
    )
    group.add_argument(
        "--arm-summaries",
        nargs="+",
        type=Path,
        metavar="PATH",
        help="Paths to arm_matrix_summary.json files (use with --seeds).",
    )
    ap.add_argument(
        "--seeds",
        nargs="*",
        type=int,
        default=None,
        help="Seed values corresponding to --arm-summaries (same order).",
    )
    ap.add_argument("--out-dir", type=Path, default=None)
    return ap


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    # Build (seed, path) list
    entries: List[Tuple[int, Path]] = []
    if args.manifest is not None:
        raw = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        for item in raw:
            entries.append((int(item["seed"]), Path(item["arm_summary_json"])))
    else:
        paths = list(args.arm_summaries)
        seeds = list(args.seeds) if args.seeds else list(range(len(paths)))
        if len(seeds) != len(paths):
            print(
                f"[aggregate] ERROR: --seeds length ({len(seeds)}) != "
                f"--arm-summaries length ({len(paths)})",
                file=sys.stderr,
            )
            return 1
        entries = list(zip(seeds, paths))

    if not entries:
        print("[aggregate] ERROR: no seed entries provided", file=sys.stderr)
        return 1

    # Build per-seed records
    seed_records: List[Dict[str, Any]] = []
    for seed, arm_path in entries:
        arm_path = arm_path.resolve()
        if not arm_path.exists():
            print(f"[aggregate] ERROR: arm summary not found: {arm_path}", file=sys.stderr)
            return 1
        try:
            arm_data = load_arm_summary(arm_path)
        except (json.JSONDecodeError, ValueError) as exc:
            print(f"[aggregate] ERROR loading {arm_path}: {exc}", file=sys.stderr)
            return 1
        seed_records.append(build_seed_record(seed, arm_path, arm_data))
        print(f"[aggregate] loaded seed={seed}: arm_verdict={arm_data.get('arm_verdict')}")

    try:
        agg = aggregate_across_seeds(seed_records, e0006_ref_dir=_E0006_REF_PATH)
    except ValueError as exc:
        print(f"[aggregate] ERROR: {exc}", file=sys.stderr)
        return 1

    payload: Dict[str, Any] = {
        "generated_at": _utcnow(),
        "experiment_family": "E-0011",
        "protocol": "reuses frozen prereg-c2b-adjudication §4/§5; only seed varies",
        "seed_records": seed_records,
        "aggregation": agg,
    }

    # Output
    out_dir = Path(args.out_dir) if args.out_dir else (_REPO / "results" / "multiseed_c2")
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    json_out = out_dir / "multiseed_c2_aggregate.json"
    md_out = out_dir / "multiseed_c2_aggregate.md"
    json_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_aggregate_md(payload, md_out)
    print(f"[aggregate] written → {json_out}")
    print(f"[aggregate] written → {md_out}")
    print(
        f"[aggregate] caveat_outcome: "
        f"{agg['caveat_drop_rule']['outcome']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
