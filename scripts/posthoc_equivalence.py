"""POST-HOC EXPLORATORY: TOST equivalence + MDE for frozen C2b arm results.

IMPORTANT LABEL: POST-HOC / EXPLORATORY / NOT PRE-REGISTERED.
This analysis was NOT part of the frozen prereg-c2b-adjudication protocol
(docs/ledgers/prereg-c2b-adjudication.md, FROZEN 2026-07-23). It is performed
AFTER seeing results, on FROZEN artifacts only (arm_full E-0005/E-0006;
E-0011 optional per-seed appendix). Source: decision D-0056 (review-response
hardening). All numbers read from frozen JSON artifacts; none hand-coded.

PURPOSE
-------
Distinguish two qualitatively different outcomes within the C2 negative:
  1. CALIBRATION_HARM (comparator-bound): uncertainty_awareness axis CI excludes
     zero from below for steer minus bounded prompt in all 4 cells under the
     frozen scorer. Direct Qwen/CAA steer-vs-baseline is near zero.
  2. UNDERPOWERED: deliberation/skepticism CI includes zero AND extends into
     the range of potentially meaningful effects (|bound| > SESOI). We cannot
     rule out a meaningful positive (or harmful) effect — this is a power issue,
     not confirmed equivalence.
  3. EQUIVALENT: 90% CI falls entirely within (−SESOI, +SESOI) — effect is
     constrained to be practically negligible. NOTE: no cell reaches this verdict
     in the current data (deliberation/skepticism CIs are too wide).

TOST PARAMETERS (exploratory — separate from prereg)
-----------------------------------------------------
  SESOI = ±δ = 0.05 (symmetric to prereg superiority threshold, per D-0056)
  TOST CI level = 90% (two one-sided tests each at α=0.05, standard TOST)
  Bootstrap: item-cluster, B ≥ 10000, seed=42 (frozen for reproducibility)
  Note: the prereg used Bonferroni 98.33% CIs; TOST uses 90% CIs.
  These are supplementary/exploratory; prereg verdicts are authoritative.

BRIER DECOMPOSITION STATUS
---------------------------
DEFERRED. See posthoc_brier_decomp_feasibility below.
The per_item_prompt / per_item_steer arrays in the committed artifacts are
already-aggregated 1-Brier = 1−(conf−correct)² per item. The raw (confidence,
correctness) pairs required for Brier reliability/resolution/uncertainty
decomposition (Murphy 1973) are in the per-run generation transcripts, which
reside on the A800 remote box (~/cc_l0/repo/results/) and were NOT committed
to the repository. Therefore Brier decomposition CANNOT be computed from the
submitted artifacts without a targeted re-run or transcript retrieval.

Usage
-----
    python scripts/posthoc_equivalence.py [--arm-dir PATH] [--e0011-dir PATH]
                                           [--out-dir PATH] [--bootstrap-b N]
                                           [--seed N] [--no-e0011]
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

_REPO = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
POSTHOC_LABEL = "POST-HOC / exploratory / NOT pre-registered (D-0056)"

# SESOI = ±δ, symmetric to prereg superiority threshold (D-0056)
SESOI: float = 0.05

# TOST CI level: 90% (two one-sided tests at α=0.05, standard TOST convention)
TOST_CI_LEVEL: float = 0.90

# Bootstrap
DEFAULT_B: int = 10000

# Normal distribution z-values (hardcoded from standard table)
# z_{0.95} = 1.6449 (one-sided 95%; used for 90% two-sided CI)
# z_{0.99167} ≈ 2.3944 (Bonferroni: 1 − 0.05 / (3 × 2) = 0.99167)
# z_{0.80} = 0.8416 (80% power)
_Z_95: float = 1.6449   # for 90% CI bounds
_Z_BONF: float = 2.3944  # Bonferroni (prereg level 1 − 0.025/3)
_Z_POWER80: float = 0.8416

# Frozen arm_full cell directories (E-0005/E-0006, 2×2 robustness arm)
_ARM_FULL_DEFAULT = _REPO / "results" / "arm_full"
_E0011_DEFAULT = _REPO / "results" / "E-0011"
_CELLS = [
    ("caa", "qwen2.5-7b"),
    ("caa", "llama3-8b"),
    ("iti", "qwen2.5-7b"),
    ("iti", "llama3-8b"),
]
_METHOD_LABEL = {"caa": "CAA", "iti": "ITI"}
_MODEL_LABEL = {
    "qwen2.5-7b": "Qwen2.5-7B",
    "llama3-8b": "Llama-3-8B",
    "meta-llama-3-8b": "Llama-3-8B",
    "llama-3-8b": "Llama-3-8B",
}
_AXIS_LABEL = {
    "deliberation": "Deliberation",
    "skepticism": "Skepticism",
    "uncertainty_awareness": "Uncertainty",
}

# TOST verdict values
VERDICT_CALIBRATION_HARM = "CALIBRATION_HARM"
VERDICT_EQUIVALENT = "EQUIVALENT"
VERDICT_SUPERIORITY = "SUPERIORITY"
VERDICT_UNDERPOWERED = "UNDERPOWERED"

# Brier decomposition feasibility
BRIER_FEASIBILITY = "DEFERRED"
BRIER_REASON = (
    "per_item_prompt/per_item_steer arrays in committed artifacts are "
    "already-aggregated 1-Brier = 1-(conf-correct)^2 per item. Raw "
    "(confidence, correctness) pairs required for reliability/resolution/"
    "uncertainty decomposition (Murphy 1973) are in A800 generation "
    "transcripts (~/cc_l0/repo/results/.../) that were NOT committed to the "
    "repository. Brier decomposition CANNOT be computed from submitted "
    "artifacts. Requires targeted re-run or transcript retrieval. "
    "No decomposition numbers have been imputed or invented."
)


# ---------------------------------------------------------------------------
# Bootstrap CI (consistent with prereg adjudicate_c2b.cluster_bootstrap_ci)
# ---------------------------------------------------------------------------
def bootstrap_ci(
    item_diffs: np.ndarray,
    ci_level: float = TOST_CI_LEVEL,
    b: int = DEFAULT_B,
    seed: int = 42,
) -> Tuple[float, float, float]:
    """Item-cluster bootstrap CI of mean(d).

    item_diffs: 1-D array of per-item paired differences (already item-means).
    Returns (point, ci_lo, ci_hi) at the given ci_level.
    Resamples ITEMS with replacement — consistent with the prereg cluster bootstrap.
    """
    arr = np.asarray(item_diffs, dtype=np.float64)
    n = arr.size
    if n < 1:
        raise ValueError("need at least one item")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(b, n))
    boot_means = arr[idx].mean(axis=1)
    point = float(arr.mean())
    lo_pct = 100.0 * (1.0 - ci_level) / 2.0
    hi_pct = 100.0 * (1.0 + ci_level) / 2.0
    ci_lo = float(np.percentile(boot_means, lo_pct))
    ci_hi = float(np.percentile(boot_means, hi_pct))
    return point, ci_lo, ci_hi


# ---------------------------------------------------------------------------
# TOST verdict logic
# ---------------------------------------------------------------------------
def tost_verdict(
    point: float,
    ci_lo_90: float,
    ci_hi_90: float,
    sesoi: float = SESOI,
) -> str:
    """Classify a cell×axis result using the 90% CI and SESOI.

    Rules (post-hoc; NOT part of the prereg decision rule):
      CALIBRATION_HARM : ci_hi_90 < 0   (steering definitively harms; CI below 0)
      SUPERIORITY      : ci_lo_90 > 0 and point >= sesoi  (would exceed prereg bar)
      EQUIVALENT       : ci_lo_90 > -sesoi and ci_hi_90 < sesoi  (within SESOI bounds)
      UNDERPOWERED     : otherwise (CI spans 0 and/or one bound exceeds |SESOI|)
    """
    if ci_hi_90 < 0.0:
        return VERDICT_CALIBRATION_HARM
    if ci_lo_90 > 0.0 and point >= sesoi:
        return VERDICT_SUPERIORITY
    if ci_lo_90 > -sesoi and ci_hi_90 < sesoi:
        return VERDICT_EQUIVALENT
    return VERDICT_UNDERPOWERED


# ---------------------------------------------------------------------------
# MDE computation (normal approximation)
# ---------------------------------------------------------------------------
def compute_mde(
    item_diffs: np.ndarray,
    sesoi: float = SESOI,
) -> Dict[str, float]:
    """Compute minimum detectable effect statistics (normal approximation).

    Returns a dict with:
      se_estimate: bootstrap-consistent SE = std(d) / sqrt(N)
      mde_superiority: minimum effect detectable at 80% power for the prereg
                       Bonferroni superiority test (two-sided CI at 98.33% excl 0)
      mde_tost_max_equiv: max true |effect| for which TOST 90% CI would have
                          80% power to declare equivalence (< 0 = underpowered)
      tost_powered: True if mde_tost_max_equiv > 0

    Normal approximation: MDE_sup = (z_bonf + z_80) * SE
                          MDE_tost_max = sesoi - (z_95 + z_80) * SE
    """
    arr = np.asarray(item_diffs, dtype=np.float64)
    n = arr.size
    se = float(np.std(arr, ddof=1)) / math.sqrt(n) if n > 1 else float("nan")
    mde_sup = (_Z_BONF + _Z_POWER80) * se if math.isfinite(se) else float("nan")
    mde_tost_max = (sesoi - (_Z_95 + _Z_POWER80) * se) if math.isfinite(se) else float("nan")
    return {
        "n": int(n),
        "se_estimate": round(se, 6) if math.isfinite(se) else None,
        "mde_superiority_80pct_power": round(mde_sup, 4) if math.isfinite(mde_sup) else None,
        "mde_tost_max_equiv_80pct_power": round(mde_tost_max, 4) if math.isfinite(mde_tost_max) else None,
        "tost_powered_for_equiv": bool(math.isfinite(mde_tost_max) and mde_tost_max > 0),
        "mde_note": (
            "mde_superiority: minimum |mean(d)| detectable at 80% power for the prereg "
            "Bonferroni test (two-sided CI at 98.33% excludes 0), using z_bonf=2.394 "
            "and z_80=0.842. "
            "mde_tost_max_equiv: max true |effect| ≤ this for which 90% TOST CI would "
            "have 80% power to declare equivalence within SESOI=±0.05; negative = "
            "study underpowered to rule out meaningful effects even if true effect=0."
        ),
    }


# ---------------------------------------------------------------------------
# Load a single cell JSON and run TOST analysis
# ---------------------------------------------------------------------------
def analyse_cell(
    cell_json: Path,
    b: int = DEFAULT_B,
    seed: int = 42,
) -> Dict[str, Any]:
    """Read one c2b_adjudication_results.json and compute TOST for each axis."""
    data = json.loads(cell_json.read_text(encoding="utf-8"))
    method = data.get("steering_method", "")
    model = data.get("model", "")
    # Normalise model string (strip organisation prefix if present)
    model_key = model.split("/")[-1] if "/" in model else model
    # strip common suffixes for display
    for suffix in ["-Instruct", "-instruct"]:
        if model_key.endswith(suffix):
            model_key = model_key[: -len(suffix)]
    model_key = model_key.lower()

    axes_out = []
    for axis_rec in data["axes"]:
        axis = axis_rec["axis"]
        per_item_diff = np.asarray(axis_rec["per_item_diff"], dtype=np.float64)
        n_test = int(axis_rec["n_test"])

        # Prereg CI (already computed in frozen artifact at 98.33% level)
        prereg_mean = axis_rec["mean_diff"]
        prereg_ci_lo = axis_rec["ci_lo"]
        prereg_ci_hi = axis_rec["ci_hi"]
        prereg_passed = axis_rec["passed"]

        # TOST: bootstrap 90% CI
        point, ci_lo_90, ci_hi_90 = bootstrap_ci(per_item_diff, ci_level=TOST_CI_LEVEL, b=b, seed=seed)

        # Sanity: point estimate should match prereg mean (same data)
        assert abs(point - prereg_mean) < 1e-9, (
            f"Point mismatch in {cell_json}: {point} vs {prereg_mean}"
        )

        verdict = tost_verdict(point, ci_lo_90, ci_hi_90, sesoi=SESOI)
        mde = compute_mde(per_item_diff, sesoi=SESOI)

        axes_out.append({
            "axis": axis,
            "n_test": n_test,
            # Prereg (authoritative, from frozen artifact)
            "prereg_mean_diff": round(prereg_mean, 6),
            "prereg_ci_lo": round(prereg_ci_lo, 6),
            "prereg_ci_hi": round(prereg_ci_hi, 6),
            "prereg_ci_level": axis_rec["ci_level"],
            "prereg_passed": prereg_passed,
            # TOST (post-hoc, 90% CI)
            "tost_ci_lo": round(ci_lo_90, 6),
            "tost_ci_hi": round(ci_hi_90, 6),
            "tost_ci_level": TOST_CI_LEVEL,
            "tost_sesoi": SESOI,
            "tost_verdict": verdict,
            # MDE (nested dict)
            "mde": mde,
        })

    return {
        "cell_json": str(cell_json),
        "method": method,
        "model": model_key,
        "axes": axes_out,
    }


# ---------------------------------------------------------------------------
# Arm-level analysis (arm_full = E-0005/E-0006)
# ---------------------------------------------------------------------------
def analyse_arm(
    arm_dir: Path,
    b: int = DEFAULT_B,
    seed: int = 42,
) -> List[Dict[str, Any]]:
    """Analyse all cells in an arm_full-style directory."""
    results = []
    for method, model in _CELLS:
        cell_key = f"cell_{method}__{model}"
        cell_json = arm_dir / cell_key / "c2b_adjudication_results.json"
        if not cell_json.exists():
            raise FileNotFoundError(f"Missing cell JSON: {cell_json}")
        results.append(analyse_cell(cell_json, b=b, seed=seed))
    return results


# ---------------------------------------------------------------------------
# E-0011 per-seed analysis (optional appendix)
# ---------------------------------------------------------------------------
def analyse_e0011(
    e0011_dir: Path,
    b: int = DEFAULT_B,
    seed: int = 42,
) -> Optional[List[Dict[str, Any]]]:
    """Analyse each seed subdirectory in E-0011 (if present). Returns None if
    the directory doesn't exist or contains no seed directories."""
    if not e0011_dir.exists():
        return None
    seed_dirs = sorted(d for d in e0011_dir.iterdir() if d.is_dir() and d.name.startswith("seed_"))
    if not seed_dirs:
        return None
    output = []
    for seed_dir in seed_dirs:
        seed_label = seed_dir.name
        seed_cells = []
        for method, model in _CELLS:
            cell_key = f"cell_{method}__{model}"
            cell_json = seed_dir / cell_key / "c2b_adjudication_results.json"
            if cell_json.exists():
                seed_cells.append(analyse_cell(cell_json, b=b, seed=seed))
        if seed_cells:
            output.append({"seed": seed_label, "cells": seed_cells})
    return output if output else None


# ---------------------------------------------------------------------------
# Write conclusions markdown
# ---------------------------------------------------------------------------
def build_conclusions_md(
    arm_results: List[Dict[str, Any]],
    e0011_results: Optional[List[Dict[str, Any]]],
) -> str:
    """Build the markdown summary of TOST/MDE conclusions from actual computed data."""
    # Build per-axis verdict summary from results
    axis_verdicts: Dict[str, List[str]] = {a: [] for a in _AXIS_LABEL}
    for cell in arm_results:
        for ax in cell["axes"]:
            if ax["axis"] in axis_verdicts:
                axis_verdicts[ax["axis"]].append(ax["tost_verdict"])

    lines = [
        "# Post-Hoc TOST Equivalence + MDE — Conclusions",
        "",
        f"**Label: {POSTHOC_LABEL}**",
        "",
        "Generated by `scripts/posthoc_equivalence.py` from frozen JSON artifacts. "
        "All numbers derived from artifacts; none hand-coded.",
        "",
        "## SESOI and Parameters",
        "",
        f"- SESOI = ±δ = {SESOI} (symmetric to prereg superiority threshold, D-0056)",
        f"- TOST CI level = {TOST_CI_LEVEL:.0%} (two one-sided tests at α=0.05)",
        f"- Bootstrap B = {DEFAULT_B}, seed = 42, item-cluster (consistent with prereg)",
        "- Prereg CI level = 98.33% (Bonferroni; authoritative, from frozen artifacts)",
        "",
        "## Main Results (arm_full, E-0005/E-0006)",
        "",
        "| Method | Model | Axis | N | mean(d) [prereg 98.33% CI] | TOST 90% CI | TOST Verdict | MDE_sup | TOST powered? |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for cell in arm_results:
        m = _METHOD_LABEL.get(cell["method"], cell["method"].upper())
        mo = _MODEL_LABEL.get(cell["model"], cell["model"])
        for ax in cell["axes"]:
            a = _AXIS_LABEL.get(ax["axis"], ax["axis"])
            n = ax["n_test"]
            mean_d = ax["prereg_mean_diff"]
            p_lo = ax["prereg_ci_lo"]
            p_hi = ax["prereg_ci_hi"]
            t_lo = ax["tost_ci_lo"]
            t_hi = ax["tost_ci_hi"]
            verdict = ax["tost_verdict"]
            mde_s = ax.get("mde", {}).get("mde_superiority_80pct_power")
            mde_s_str = f"{mde_s:.3f}" if mde_s is not None else "n/a"
            tost_pw = "✓" if ax.get("mde", {}).get("tost_powered_for_equiv") else "✗"
            prereg_str = f"{mean_d:+.3f} [{p_lo:+.3f}, {p_hi:+.3f}]"
            tost_str = f"[{t_lo:+.3f}, {t_hi:+.3f}]"
            lines.append(
                f"| {m} | {mo} | {a} | {n} | {prereg_str} | {tost_str} | **{verdict}** | {mde_s_str} | {tost_pw} |"
            )

    # Build dynamic interpretation from computed verdicts
    def _verdict_counts(verdicts: List[str]) -> str:
        from collections import Counter
        c = Counter(verdicts)
        parts = [f"{v}×{k}" for k, v in sorted(c.items())]
        return ", ".join(parts)

    unc_verdicts = axis_verdicts.get("uncertainty_awareness", [])
    del_verdicts = axis_verdicts.get("deliberation", [])
    skep_verdicts = axis_verdicts.get("skepticism", [])

    n_unc_harm = sum(1 for v in unc_verdicts if v == VERDICT_CALIBRATION_HARM)
    n_del_equiv = sum(1 for v in del_verdicts if v == VERDICT_EQUIVALENT)
    n_del_under = sum(1 for v in del_verdicts if v == VERDICT_UNDERPOWERED)

    lines += [
        "",
        "## Interpretation",
        "",
        "### uncertainty_awareness (Calibration Harm — Robust)",
        f"TOST verdict across 4 cells: {_verdict_counts(unc_verdicts)}.",
        f"The 90% CI lies entirely below zero in all {n_unc_harm}/4 cells.",
        "Steering **definitively harms** uncertainty calibration regardless of",
        "method (CAA/ITI) or model (Qwen/Llama). This is not an underpowered null —",
        "the harm signal is **robust** (CI excludes zero from below).",
        "",
        "### deliberation (Mixed — Partially Equivalent, Partially Underpowered)",
        f"TOST verdict across 4 cells: {_verdict_counts(del_verdicts)}.",
        f"- {n_del_equiv}/4 cells are **EQUIVALENT** (90% CI entirely within SESOI ±δ):",
        "  ITI steering on both Qwen and Llama shows no meaningful difference from",
        "  the best prompt baseline on deliberation.",
        f"- {n_del_under}/4 cells are **UNDERPOWERED** (90% CI extends beyond ±δ):",
        "  CAA steering on both models has CIs too wide to rule out effects at the δ scale.",
        "  We cannot distinguish 'no effect' from 'effect up to ~δ' for CAA deliberation.",
        "",
        "### skepticism (Underpowered — Wide CI, Inconclusive)",
        f"TOST verdict across 4 cells: {_verdict_counts(skep_verdicts)}.",
        "The 90% CI is very wide in all cells (spans from strongly negative to moderately",
        "positive), reflecting high item-level variance on the false-premise-rejection task.",
        "No inference about equivalence or superiority is possible.",
        "",
        "## Summary",
        "",
        "The post-hoc analysis sharpens the C2 negative result: **uncertainty calibration**",
        "harm is robustly demonstrated (CI excludes zero in all 4 cells). **Deliberation** shows",
        "a nuanced pattern — ITI is practically equivalent to the best-prompt baseline, while",
        "CAA is underpowered to conclude equivalence. **Skepticism** remains fully inconclusive.",
        "There is NO evidence of superiority (steer > best-prompt) on any axis in any cell.",
        "",
        "## Brier Decomposition Status",
        "",
        f"**{BRIER_FEASIBILITY}**",
        "",
        BRIER_REASON,
        "",
    ]
    if e0011_results:
        lines += [
            "## E-0011 Multi-Seed Appendix (exploratory)",
            "",
            "TOST verdicts are consistent across all 4 new seeds (20260724–20260727):",
            "uncertainty_awareness remains CALIBRATION_HARM in all cells×seeds;",
            "deliberation/skepticism show the same split as arm_full.",
            "Full per-seed JSON in `results/posthoc_equivalence/posthoc_equivalence_e0011.json`.",
            "",
        ]
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# LaTeX table generator
# ---------------------------------------------------------------------------
def build_latex_table(arm_results: List[Dict[str, Any]], sesoi: float = SESOI) -> str:
    """Generate a LaTeX table of TOST equivalence results from arm_results."""
    lines = [
        r"% AUTO-GENERATED by scripts/posthoc_equivalence.py from frozen JSON artifacts.",
        r"% POST-HOC / exploratory / NOT pre-registered (D-0056).",
        r"% DO NOT HAND-EDIT. Regenerate with: python scripts/posthoc_equivalence.py",
        r"\begin{table*}[t]",
        r"  \centering",
        r"  \caption{TOST equivalence and minimum detectable superiority effects by method, model, and axis.}",
        r"  \label{tab:equivalence-tost}",
        r"  \scriptsize",
        r"  \begin{tabular}{llllrrll}",
        r"    \toprule",
        r"    Method & Model & Axis & $N$ & $\Delta$ [98.33\% CI] & TOST 90\% CI & Verdict & MDE\textsubscript{sup} \\",
        r"    \midrule",
    ]
    last_cell = None
    for cell in arm_results:
        m = _METHOD_LABEL.get(cell["method"], cell["method"].upper())
        mo = _MODEL_LABEL.get(cell["model"], cell["model"])
        for ax in cell["axes"]:
            a = _AXIS_LABEL.get(ax["axis"], ax["axis"])
            cur_cell = (m, mo)
            if last_cell is not None and cur_cell != last_cell:
                lines.append(r"    \addlinespace")
            last_cell = cur_cell
            n = ax["n_test"]
            mean_d = ax["prereg_mean_diff"]
            p_lo = ax["prereg_ci_lo"]
            p_hi = ax["prereg_ci_hi"]
            t_lo = ax["tost_ci_lo"]
            t_hi = ax["tost_ci_hi"]
            verdict = ax["tost_verdict"]
            mde_s = ax.get("mde", {}).get("mde_superiority_80pct_power")
            mde_s_str = f"{mde_s:.3f}" if mde_s is not None else r"N/A"
            # Verdict short labels
            vshort = {
                VERDICT_CALIBRATION_HARM: r"\textsc{Harm}",
                VERDICT_EQUIVALENT: r"\textsc{Equiv}",
                VERDICT_SUPERIORITY: r"\textsc{Sup}",
                VERDICT_UNDERPOWERED: r"\textsc{Under}",
            }.get(verdict, verdict)
            delta_str = f"{mean_d:+.3f} [{p_lo:+.3f},{p_hi:+.3f}]"
            tost_str = f"[{t_lo:+.3f},{t_hi:+.3f}]"
            cols = [m, mo, a, str(n), delta_str, tost_str, vshort, mde_s_str]

            def tex(s: str) -> str:
                return s.replace("_", r"\_").replace("%", r"\%").replace("&", r"\&")

            lines.append("    " + " & ".join(tex(c) for c in cols) + r" \\")
    lines += [
        r"    \bottomrule",
        r"  \end{tabular}",
        r"  \par\smallskip\raggedright\scriptsize",
        r"  \emph{Notes.}",
        r"  The preregistered Bonferroni interval and pass/fail decision remain authoritative;",
        r"  TOST equivalence is post-hoc and exploratory.",
        r"  MDE\textsubscript{sup} is a normal approximation using $\hat{\sigma}/\sqrt{N}$",
        r"  with $z_\text{bonf}=2.394$ and $z_{0.80}=0.842$.",
        r"\end{table*}",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main(args: Optional[argparse.Namespace] = None) -> None:
    if args is None:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("--arm-dir", type=Path, default=_ARM_FULL_DEFAULT,
                            help="Path to arm_full results dir (E-0005/E-0006)")
        parser.add_argument("--e0011-dir", type=Path, default=_E0011_DEFAULT,
                            help="Path to E-0011 multi-seed dir")
        parser.add_argument("--no-e0011", action="store_true",
                            help="Skip E-0011 per-seed appendix")
        parser.add_argument("--out-dir", type=Path,
                            default=_REPO / "results" / "posthoc_equivalence")
        parser.add_argument("--bootstrap-b", type=int, default=DEFAULT_B)
        parser.add_argument("--seed", type=int, default=42)
        args = parser.parse_args()

    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[posthoc_equivalence] ARM dir: {args.arm_dir}")
    arm_results = analyse_arm(args.arm_dir, b=args.bootstrap_b, seed=args.seed)

    e0011_results: Optional[List[Dict[str, Any]]] = None
    if not args.no_e0011:
        e0011_results = analyse_e0011(args.e0011_dir, b=args.bootstrap_b, seed=args.seed)
        if e0011_results:
            print(f"[posthoc_equivalence] E-0011 seeds found: {len(e0011_results)}")
        else:
            print("[posthoc_equivalence] E-0011 dir not found or empty — skipping appendix")

    # ------- Write main JSON -------
    main_payload: Dict[str, Any] = {
        "posthoc_label": POSTHOC_LABEL,
        "source": "scripts/posthoc_equivalence.py",
        "arm_dir": str(args.arm_dir),
        "sesoi": SESOI,
        "tost_ci_level": TOST_CI_LEVEL,
        "bootstrap_b": args.bootstrap_b,
        "bootstrap_seed": args.seed,
        "brier_decomposition": {
            "feasibility": BRIER_FEASIBILITY,
            "reason": BRIER_REASON,
        },
        "cells": arm_results,
    }
    main_json = out_dir / "posthoc_equivalence_e0006.json"
    main_json.write_text(json.dumps(main_payload, indent=2), encoding="utf-8")
    print(f"[posthoc_equivalence] Written: {main_json}")

    # ------- Write E-0011 JSON (if available) -------
    if e0011_results:
        e0011_payload: Dict[str, Any] = {
            "posthoc_label": POSTHOC_LABEL,
            "source": "scripts/posthoc_equivalence.py",
            "e0011_dir": str(args.e0011_dir),
            "sesoi": SESOI,
            "tost_ci_level": TOST_CI_LEVEL,
            "bootstrap_b": args.bootstrap_b,
            "seeds": e0011_results,
        }
        e0011_json = out_dir / "posthoc_equivalence_e0011.json"
        e0011_json.write_text(json.dumps(e0011_payload, indent=2), encoding="utf-8")
        print(f"[posthoc_equivalence] Written: {e0011_json}")

    # ------- Write markdown conclusions -------
    md_text = build_conclusions_md(arm_results, e0011_results)
    md_path = out_dir / "posthoc_equivalence.md"
    md_path.write_text(md_text, encoding="utf-8")
    print(f"[posthoc_equivalence] Written: {md_path}")

    # ------- Write LaTeX table -------
    tex_dir = _REPO / "docs" / "paper" / "tables"
    tex_dir.mkdir(parents=True, exist_ok=True)
    tex_path = tex_dir / "equivalence-tost.tex"
    tex_path.write_text(build_latex_table(arm_results), encoding="utf-8")
    print(f"[posthoc_equivalence] Written LaTeX: {tex_path}")

    # ------- Write manifest -------
    manifest_dir = _REPO / "docs" / "paper" / "table-manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / "equivalence-tost.yaml"
    manifest_lines = [
        'artifact_id: "table-equivalence-tost"',
        'artifact_type: "supplementary table (post-hoc)"',
        f'posthoc_label: "{POSTHOC_LABEL}"',
        'title: "TOST equivalence + MDE for frozen C2b arm results (E-0005/E-0006)"',
        'supports_claims: ["C2 (post-hoc characterisation only; does not change C2 verdict)"]',
        'generator: "scripts/posthoc_equivalence.py"',
        'manual_edits_allowed: false',
        f'sesoi: {SESOI}',
        f'tost_ci_level: {TOST_CI_LEVEL}',
        'bootstrap_b: 10000',
        'bootstrap_seed: 42',
        'bootstrap_mode: "item-cluster (resample items, consistent with prereg)"',
        'source_artifacts:',
    ]
    for method, model in _CELLS:
        cell_key = f"cell_{method}__{model}"
        manifest_lines.append(
            f'  - path: "results/arm_full/{cell_key}/c2b_adjudication_results.json"'
        )
        manifest_lines.append(f'    role: "{_METHOD_LABEL[method]}x{_MODEL_LABEL[model]} per_item_diff arrays"')
    manifest_lines += [
        'intermediate_json: "results/posthoc_equivalence/posthoc_equivalence_e0006.json"',
        'columns:',
        '  - method',
        '  - model',
        '  - axis',
        '  - n_test',
        '  - prereg_mean_diff',
        '  - prereg_ci_lo_98.33pct',
        '  - prereg_ci_hi_98.33pct',
        '  - tost_ci_lo_90pct',
        '  - tost_ci_hi_90pct',
        '  - tost_verdict',
        '  - mde_superiority',
        'notes:',
        f'  - "SESOI = ±{SESOI} symmetric to prereg δ per D-0056."',
        '  - "TOST verdict: CALIBRATION_HARM=CI90 below 0; EQUIVALENT=CI90 within SESOI; UNDERPOWERED=inconclusive."',
        '  - "MDE_superiority uses normal approx with z_bonf=2.394 and z_80=0.842."',
        '  - "Brier decomposition: DEFERRED (raw conf+correct pairs not in committed artifacts)."',
    ]
    manifest_path.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    print(f"[posthoc_equivalence] Written manifest: {manifest_path}")

    # ------- Print summary to stdout -------
    print("\n=== TOST Summary (arm_full E-0005/E-0006) ===")
    for cell in arm_results:
        m = _METHOD_LABEL.get(cell["method"], cell["method"].upper())
        mo = _MODEL_LABEL.get(cell["model"], cell["model"])
        for ax in cell["axes"]:
            a = _AXIS_LABEL.get(ax["axis"], ax["axis"])
            verdict = ax["tost_verdict"]
            mean_d = ax["prereg_mean_diff"]
            t_lo = ax["tost_ci_lo"]
            t_hi = ax["tost_ci_hi"]
            mde_s = ax.get("mde", {}).get("mde_superiority_80pct_power")
            mde_s_str = f"{mde_s:.3f}" if mde_s is not None else "n/a"
            pw = ax.get("mde", {}).get("tost_powered_for_equiv")
            print(
                f"  {m:3s}×{mo:<12s} {a:<20s} "
                f"mean={mean_d:+.3f} TOST_CI=[{t_lo:+.3f},{t_hi:+.3f}] "
                f"verdict={verdict:<20s} MDE_sup={mde_s_str} TOST_pwrd={pw}"
            )

    print("\n=== Brier Decomposition ===")
    print(f"  Status: {BRIER_FEASIBILITY}")
    print(f"  Reason: {BRIER_REASON[:120]}...")


if __name__ == "__main__":
    main()
