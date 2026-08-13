"""Uncertainty missingness/format-compliance recheck for the THREE cells that
E-0013 never rechecked (ITI-Qwen, CAA-Llama, ITI-Llama).

MOTIVATION (reviewer finding): the paper's "uncertainty favors the comparator"
headline rests on all four steer-vs-prompt uncertainty contrasts being negative
under the frozen 0.5-confidence-imputation scorer. E-0013 showed that for the
CAA-Qwen cell there is a large confidence-PARSEABILITY asymmetry (steer 0.826 vs
prompt 0.445), so the frozen scorer's 0.5 imputation could be systematically
penalising the higher-missingness condition. E-0013 decomposed ONLY CAA-Qwen
(complete-case -0.337 CI[-0.508,-0.165]; adversarial all-generation bounds
[-0.478,+0.250] cross zero). The other three cells were never rechecked.

This script reproduces the SAME decomposition E-0013 applied to CAA-Qwen for the
three unrechecked cells, using ONLY already-collected frozen generations:
``results/arm_full/cell_*/transcripts/uncertainty_awareness__test_{steer,prompt,
baseline}__*.jsonl``. It computes, per cell:
  (a) parseable-confidence rate steer vs prompt (and baseline),
  (b) complete-case steer-minus-prompt point + item-cluster bootstrap CI,
  (c) adversarial all-generation missingness bounds (best/worst imputation),
      and whether they cross zero.

NO new generation, NO GPU. It reads the frozen transcripts READ-ONLY from the
main checkout and does NOT modify any frozen artifact. The CAA-Qwen cell is also
recomputed here PURELY as a method-validation anchor against E-0013's published
reanalysis.json (must reproduce to numerical tolerance).

valid_for_paper=False. scientific_status=PENDING_HOSTILE_RESULT_AUDIT.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

# --- locate the frozen (main) checkout for READ-ONLY transcript access -------
_THIS = Path(__file__).resolve()
_WORKTREE_REPO = _THIS.parents[1]
if str(_WORKTREE_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_WORKTREE_REPO / "src"))

from cognitive_console.experiments.adjudicate_c2b import (  # noqa: E402
    BONFERRONI_CI_LEVEL,
    BOOTSTRAP_B,
    cluster_bootstrap_ci,
)

# E-0013 used DEFAULT_SEED=20260723 for the reanalysis bootstrap and ci_level=0.95
# (see scripts/run_uncertainty_format_recheck.py _ci_from_diffs / DEFAULT_SEED).
E0013_SEED = 20260723
E0013_CI_LEVEL = 0.95  # the level actually used in E-0013 reanalysis.json
GRID_CI_LEVEL = BONFERRONI_CI_LEVEL  # 0.98333..., the frozen grid's per-cell level
AXIS = "uncertainty_awareness"
CONDITIONS = ("prompt", "steer", "baseline")
PHASE_TO_CONDITION = {
    "test_steer": "steer",
    "test_prompt": "prompt",
    "test_baseline": "baseline",
}

CELLS = (
    "caa__qwen2.5-7b",  # validation anchor (reproduce E-0013)
    "iti__qwen2.5-7b",
    "caa__llama3-8b",
    "iti__llama3-8b",
)


# --------------------------------------------------------------------------- #
# Record loading from frozen transcripts
# --------------------------------------------------------------------------- #
def _frozen_root(main_repo: Path) -> Path:
    return main_repo / "results" / "arm_full"


def _find_phase_file(cell_dir: Path, phase: str) -> Optional[Path]:
    matches = sorted(cell_dir.glob(f"{AXIS}__{phase}__*.jsonl"))
    if not matches:
        return None
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one {phase} transcript in {cell_dir}, "
                           f"found {len(matches)}: {[m.name for m in matches]}")
    return matches[0]


def _load_transcript_records(main_repo: Path, cell_key: str) -> Tuple[List[Dict], Dict[str, str]]:
    """Return (records, phase_file_names) for one cell across the three test phases.

    Each record mirrors the E-0013 samples schema fields used by ``reanalyse``:
      cell, split, condition, item_id, sample_index, format_compliant,
      per_item_1minus_brier.
    Field mapping from the frozen transcript row:
      format_compliant       <- (row["parse"]["parsed_confidence"] is not None)
      per_item_1minus_brier  <- row["sample_outcome"]  (frozen 0.5-imputed 1-Brier)
    """
    cell_dir = _frozen_root(main_repo) / f"cell_{cell_key}" / "transcripts"
    records: List[Dict] = []
    files: Dict[str, str] = {}
    for phase, condition in PHASE_TO_CONDITION.items():
        fp = _find_phase_file(cell_dir, phase)
        if fp is None:
            raise FileNotFoundError(f"missing {phase} transcript for cell {cell_key} in {cell_dir}")
        files[condition] = str(fp.relative_to(main_repo)).replace("\\", "/")
        with fp.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                parse = row.get("parse") or {}
                parsed_conf = parse.get("parsed_confidence", None)
                records.append({
                    "cell": cell_key,
                    "split": "test",
                    "condition": condition,
                    "item_id": str(row["item_id"]),
                    "sample_index": int(row["sample_index"]),
                    "format_compliant": bool(parsed_conf is not None),
                    "parsed_confidence": parsed_conf,
                    "per_item_1minus_brier": float(row["sample_outcome"]),
                })
    return records, files


# --------------------------------------------------------------------------- #
# Decomposition primitives — replicated EXACTLY from
# scripts/run_uncertainty_format_recheck.py (E-0013 reference).
# --------------------------------------------------------------------------- #
def _mean_by_item(records: Sequence[Dict], value_field: str = "per_item_1minus_brier") -> Dict[str, float]:
    grouped: Dict[str, List[float]] = {}
    for r in records:
        grouped.setdefault(str(r["item_id"]), []).append(float(r[value_field]))
    return {item_id: float(np.mean(vals)) for item_id, vals in grouped.items()}


def _paired_delta(records, a, b, value_field="per_item_1minus_brier"):
    by_cond = {
        a: _mean_by_item([r for r in records if r["condition"] == a], value_field=value_field),
        b: _mean_by_item([r for r in records if r["condition"] == b], value_field=value_field),
    }
    ids = sorted(set(by_cond[a]) & set(by_cond[b]))
    diffs = [by_cond[a][i] - by_cond[b][i] for i in ids]
    return (float(np.mean(diffs)) if diffs else math.nan), diffs


def _ci_from_diffs(diffs, bootstrap_b, seed, ci_level):
    if not diffs:
        return {"point": math.nan, "ci_lo": math.nan, "ci_hi": math.nan,
                "ci_level": ci_level, "bootstrap_b": int(bootstrap_b),
                "n_items": 0, "excludes_zero": False}
    ci = cluster_bootstrap_ci(np.asarray(diffs, dtype=float), b=bootstrap_b,
                              ci_level=ci_level, seed=seed, cluster=True)
    return {
        "point": ci.point,
        "ci_lo": ci.ci_lo,
        "ci_hi": ci.ci_hi,
        "ci_level": ci.ci_level,
        "bootstrap_b": int(bootstrap_b),
        "n_items": len(diffs),
        "excludes_zero": bool(ci.excludes_zero()),
    }


def _compliant_pair_diffs(records, a, b) -> Tuple[List[float], int]:
    keyed: Dict[Tuple[str, int], Dict[str, Dict]] = {}
    for r in records:
        if r["condition"] not in {a, b}:
            continue
        key = (str(r["item_id"]), int(r["sample_index"]))
        keyed.setdefault(key, {})[str(r["condition"])] = r
    by_item: Dict[str, List[float]] = {}
    n_pairs = 0
    for (item_id, _si), pair in keyed.items():
        if a not in pair or b not in pair:
            continue
        if not (pair[a]["format_compliant"] and pair[b]["format_compliant"]):
            continue
        n_pairs += 1
        by_item.setdefault(item_id, []).append(
            float(pair[a]["per_item_1minus_brier"]) - float(pair[b]["per_item_1minus_brier"])
        )
    return [float(np.mean(vals)) for _, vals in sorted(by_item.items())], n_pairs


def _score_with_bound(record, *, dropped_score):
    if bool(record["format_compliant"]):
        return float(record["per_item_1minus_brier"])
    return float(dropped_score)


def _worst_case_bounds(records) -> Dict[str, object]:
    rows = []
    for steer_drop, prompt_drop, label in [
        (0.0, 1.0, "least_favorable_to_steer"),
        (1.0, 0.0, "most_favorable_to_steer"),
    ]:
        adjusted = []
        for r in records:
            if r["condition"] not in {"steer", "prompt"}:
                continue
            rr = dict(r)
            rr["bounded_score"] = _score_with_bound(
                r, dropped_score=steer_drop if r["condition"] == "steer" else prompt_drop)
            adjusted.append(rr)
        delta, diffs = _paired_delta(adjusted, "steer", "prompt", value_field="bounded_score")
        rows.append({"variant": label, "delta": delta, "n_items": len(diffs)})
    crosses = (min(r["delta"] for r in rows) <= 0.0 <= max(r["delta"] for r in rows))
    return {"bounds": rows, "crosses_zero": bool(crosses)}


def reanalyse_cell(records, *, bootstrap_b, seed, ci_level) -> Dict[str, object]:
    cell_records = [r for r in records if str(r["split"]) == "test"]
    cond_rows: Dict[str, Dict[str, object]] = {}
    for cond in CONDITIONS:
        rs = [r for r in cell_records if r["condition"] == cond]
        compliant = sum(1 for r in rs if bool(r["format_compliant"]))
        cond_rows[cond] = {
            "n_samples": len(rs),
            "n_format_compliant": compliant,
            "format_compliance_rate": compliant / len(rs) if rs else math.nan,
            "n_format_dropped": len(rs) - compliant,
            "format_dropped_rate": (len(rs) - compliant) / len(rs) if rs else math.nan,
            "mean_frozen_imputed_1minus_brier": (
                float(np.mean([float(r["per_item_1minus_brier"]) for r in rs])) if rs else math.nan),
        }
    all_delta, all_diffs = _paired_delta(cell_records, "steer", "prompt")
    compliant_diffs, n_pairs = _compliant_pair_diffs(cell_records, "steer", "prompt")
    return {
        "conditions": cond_rows,
        "frozen_uncertainty_delta_steer_minus_prompt_as_run_imputed": {
            "point": all_delta, "n_items": len(all_diffs),
        },
        "format_compliant_only_delta_steer_minus_prompt": {
            **_ci_from_diffs(compliant_diffs, bootstrap_b, seed, ci_level),
            "n_compliant_sample_pairs": n_pairs,
            "restriction": "paired item/sample rows where both steer and prompt parsed confidence",
        },
        "sensitivity": {
            "worst_case_imputation_bounds": _worst_case_bounds(cell_records),
        },
    }


# --------------------------------------------------------------------------- #
# Validation against E-0013 published reanalysis.json (CAA-Qwen)
# --------------------------------------------------------------------------- #
def _load_e0013_samples(main_repo: Path) -> List[Dict]:
    p = main_repo / "results" / "E-0013-uncertainty-recheck" / "samples.jsonl"
    rows = []
    with p.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            rows.append({
                "cell": r["cell"],
                "split": r["split"],
                "condition": r["condition"],
                "item_id": str(r["item_id"]),
                "sample_index": int(r["sample_index"]),
                "format_compliant": bool(r["format_compliant"]),
                "per_item_1minus_brier": float(r["per_item_1minus_brier"]),
            })
    return rows


def _compare(name, got, exp, checks, tol=1e-9):
    ok = (got is not None and exp is not None
          and not (isinstance(got, float) and math.isnan(got))
          and abs(float(got) - float(exp)) <= tol)
    checks.append({"metric": name, "reconstructed": got, "e0013_reference": exp,
                   "abs_diff": (abs(float(got) - float(exp))
                                if got is not None and exp is not None else None),
                   "match": bool(ok)})
    return ok


def validate_method_on_e0013_samples(main_repo: Path, bootstrap_b: int) -> Dict[str, object]:
    """EXACT method validation: run our decomposition on E-0013's OWN samples.jsonl
    (seed/level as E-0013 used) and require bit-for-bit reproduction of its
    published reanalysis.json for the CAA-Qwen cell."""
    ref_path = main_repo / "results" / "E-0013-uncertainty-recheck" / "reanalysis.json"
    ref = json.loads(ref_path.read_text(encoding="utf-8"))["test_split_only"]["caa__qwen2.5-7b"]
    rows = [r for r in _load_e0013_samples(main_repo) if r["cell"] == "caa__qwen2.5-7b"]
    my = reanalyse_cell(rows, bootstrap_b=bootstrap_b, seed=E0013_SEED, ci_level=E0013_CI_LEVEL)
    checks: List[Dict] = []
    _compare("steer_format_compliance_rate",
             my["conditions"]["steer"]["format_compliance_rate"],
             ref["conditions"]["steer"]["format_compliance_rate"], checks)
    _compare("prompt_format_compliance_rate",
             my["conditions"]["prompt"]["format_compliance_rate"],
             ref["conditions"]["prompt"]["format_compliance_rate"], checks)
    _compare("as_run_imputed_delta",
             my["frozen_uncertainty_delta_steer_minus_prompt_as_run_imputed"]["point"],
             ref["frozen_uncertainty_delta_steer_minus_prompt_as_run_imputed"]["point"], checks)
    _compare("complete_case_point",
             my["format_compliant_only_delta_steer_minus_prompt"]["point"],
             ref["format_compliant_only_delta_steer_minus_prompt"]["point"], checks)
    _compare("complete_case_ci_lo",
             my["format_compliant_only_delta_steer_minus_prompt"]["ci_lo"],
             ref["format_compliant_only_delta_steer_minus_prompt"]["ci_lo"], checks)
    _compare("complete_case_ci_hi",
             my["format_compliant_only_delta_steer_minus_prompt"]["ci_hi"],
             ref["format_compliant_only_delta_steer_minus_prompt"]["ci_hi"], checks)
    _compare("n_compliant_sample_pairs",
             my["format_compliant_only_delta_steer_minus_prompt"]["n_compliant_sample_pairs"],
             ref["format_compliant_only_delta_steer_minus_prompt"]["n_compliant_sample_pairs"], checks)
    ref_b = {b["variant"]: b["delta"] for b in ref["sensitivity"]["worst_case_imputation_bounds"]["bounds"]}
    my_b = {b["variant"]: b["delta"] for b in my["sensitivity"]["worst_case_imputation_bounds"]["bounds"]}
    for v in ("least_favorable_to_steer", "most_favorable_to_steer"):
        _compare(f"bound_{v}", my_b.get(v), ref_b.get(v), checks)
    return {"all_match": bool(all(c["match"] for c in checks)), "checks": checks,
            "note": "exact reproduction of E-0013 reanalysis.json from E-0013's own samples.jsonl",
            "reference_file": str(ref_path.relative_to(main_repo)).replace("\\", "/")}


def crosscheck_caaqwen_transcripts_vs_e0013(main_repo: Path,
                                            caa_qwen_from_transcripts_095: Dict) -> Dict[str, object]:
    """Directional cross-check: CAA-Qwen decomposed from the FROZEN transcripts vs
    E-0013's re-generated numbers. These need NOT bit-match (E-0013 re-ran
    generation with a different seed) but should agree in sign/story."""
    ref = json.loads((main_repo / "results" / "E-0013-uncertainty-recheck" /
                      "reanalysis.json").read_text(encoding="utf-8"))["test_split_only"]["caa__qwen2.5-7b"]
    my = caa_qwen_from_transcripts_095
    return {
        "note": ("CAA-Qwen re-decomposed from FROZEN arm_full transcripts; E-0013 re-GENERATED "
                 "its own samples, so exact equality is NOT expected. Compared for directional agreement."),
        "steer_parseable_rate": {"frozen_transcripts": my["conditions"]["steer"]["format_compliance_rate"],
                                 "e0013_regen": ref["conditions"]["steer"]["format_compliance_rate"]},
        "prompt_parseable_rate": {"frozen_transcripts": my["conditions"]["prompt"]["format_compliance_rate"],
                                  "e0013_regen": ref["conditions"]["prompt"]["format_compliance_rate"]},
        "complete_case_point": {"frozen_transcripts": my["format_compliant_only_delta_steer_minus_prompt"]["point"],
                                "e0013_regen": ref["format_compliant_only_delta_steer_minus_prompt"]["point"]},
        "adversarial_bounds": {
            "frozen_transcripts": [b["delta"] for b in my["sensitivity"]["worst_case_imputation_bounds"]["bounds"]],
            "e0013_regen": [b["delta"] for b in ref["sensitivity"]["worst_case_imputation_bounds"]["bounds"]],
        },
    }


# --------------------------------------------------------------------------- #
def _verdict(per_cell_095: Dict[str, Dict]) -> Dict[str, object]:
    """Robustness verdict for the grid-wide 'uncertainty favors the comparator'.

    A cell's negative result is a plausible missingness/scoring artifact when the
    adversarial all-generation imputation bounds CROSS ZERO (i.e., a benign
    imputation of the dropped generations could flip the sign), OR the
    complete-case CI (both conditions parsed) no longer excludes zero / flips sign.
    """
    rechecked = ["iti__qwen2.5-7b", "caa__llama3-8b", "iti__llama3-8b"]
    per = {}
    n_bounds_cross = 0
    n_complete_case_negative_excl0 = 0
    for cell in rechecked:
        c = per_cell_095[cell]
        cc = c["format_compliant_only_delta_steer_minus_prompt"]
        bounds = c["sensitivity"]["worst_case_imputation_bounds"]
        crosses = bounds["crosses_zero"]
        cc_neg_excl0 = (cc["point"] < 0.0 and cc.get("excludes_zero", False))
        if crosses:
            n_bounds_cross += 1
        if cc_neg_excl0:
            n_complete_case_negative_excl0 += 1
        per[cell] = {
            "adversarial_bounds_cross_zero": bool(crosses),
            "complete_case_point": cc["point"],
            "complete_case_excludes_zero": bool(cc.get("excludes_zero", False)),
            "complete_case_negative_and_significant": bool(cc_neg_excl0),
            "steer_parseable_rate": c["conditions"]["steer"]["format_compliance_rate"],
            "prompt_parseable_rate": c["conditions"]["prompt"]["format_compliance_rate"],
        }
    return {
        "rechecked_cells": rechecked,
        "per_cell": per,
        "n_cells_adversarial_bounds_cross_zero": n_bounds_cross,
        "n_cells_complete_case_negative_and_significant": n_complete_case_negative_excl0,
    }


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--main-repo", default=r"C:\Users\v-elzhang\Desktop\MyFolder\cognitive console",
                    help="path to the frozen (main) checkout holding results/arm_full transcripts")
    ap.add_argument("--out", default=str(_WORKTREE_REPO / "results" /
                                         "E-0013b-uncertainty-missingness" / "reanalysis.json"))
    ap.add_argument("--bootstrap-b", type=int, default=BOOTSTRAP_B)
    ap.add_argument("--seed", type=int, default=E0013_SEED)
    args = ap.parse_args(argv)

    main_repo = Path(args.main_repo).resolve()
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    per_cell_095: Dict[str, Dict] = {}
    per_cell_grid: Dict[str, Dict] = {}
    phase_files: Dict[str, Dict[str, str]] = {}
    sanity: Dict[str, Dict] = {}

    for cell in CELLS:
        records, files = _load_transcript_records(main_repo, cell)
        phase_files[cell] = files
        # sanity: item/sample counts
        counts = {}
        for cond in CONDITIONS:
            rs = [r for r in records if r["condition"] == cond]
            counts[cond] = {
                "n_rows": len(rs),
                "n_items": len({r["item_id"] for r in rs}),
                "k_per_item": sorted({sum(1 for x in rs if x["item_id"] == r["item_id"]) for r in rs}),
            }
        sanity[cell] = counts
        per_cell_095[cell] = reanalyse_cell(records, bootstrap_b=args.bootstrap_b,
                                            seed=args.seed, ci_level=E0013_CI_LEVEL)
        per_cell_grid[cell] = reanalyse_cell(records, bootstrap_b=args.bootstrap_b,
                                             seed=args.seed, ci_level=GRID_CI_LEVEL)

    validation = validate_method_on_e0013_samples(main_repo, args.bootstrap_b)
    crosscheck = crosscheck_caaqwen_transcripts_vs_e0013(main_repo, per_cell_095["caa__qwen2.5-7b"])
    verdict = _verdict(per_cell_095)

    payload = {
        "experiment_id": "E-0013b",
        "title": "Uncertainty missingness/format-compliance recheck for the three unrechecked cells",
        "valid_for_paper": False,
        "scientific_status": "PENDING_HOSTILE_RESULT_AUDIT",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "method": {
            "source_of_generations": "frozen results/arm_full/cell_*/transcripts test_{steer,prompt,baseline}",
            "no_new_generation": True,
            "format_compliant_definition": "parse.parsed_confidence is not None",
            "per_generation_score_field": "sample_outcome (frozen 0.5-imputed per-generation 1-Brier)",
            "decomposition_reference": "scripts/run_uncertainty_format_recheck.py (E-0013)",
            "bootstrap": "item-cluster percentile bootstrap (adjudicate_c2b.cluster_bootstrap_ci, cluster=True)",
            "bootstrap_b": args.bootstrap_b,
            "bootstrap_seed": args.seed,
            "primary_ci_level": GRID_CI_LEVEL,
            "anchor_ci_level_for_e0013_reproduction": E0013_CI_LEVEL,
        },
        "phase_files": phase_files,
        "sanity_counts": sanity,
        "e0013_method_reproduction_validation": validation,
        "caaqwen_frozen_transcript_vs_e0013_regen_crosscheck": crosscheck,
        "per_cell_ci_level_0p95_e0013_anchor": per_cell_095,
        "per_cell_ci_level_grid_0p9833": per_cell_grid,
        "robustness_verdict_inputs": verdict,
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[E-0013b] wrote {out_path}")
    print(f"[E-0013b] E-0013 method reproduction all_match={validation['all_match']}")
    for cell in ("iti__qwen2.5-7b", "caa__llama3-8b", "iti__llama3-8b"):
        cc = per_cell_095[cell]["format_compliant_only_delta_steer_minus_prompt"]
        bd = per_cell_095[cell]["sensitivity"]["worst_case_imputation_bounds"]
        s = per_cell_095[cell]["conditions"]["steer"]["format_compliance_rate"]
        p = per_cell_095[cell]["conditions"]["prompt"]["format_compliance_rate"]
        ccp = cc["point"]
        ccp_s = f"{ccp:.4f}" if not (isinstance(ccp, float) and math.isnan(ccp)) else "nan"
        cilo = cc["ci_lo"]; cihi = cc["ci_hi"]
        cilo_s = f"{cilo:.4f}" if not (isinstance(cilo, float) and math.isnan(cilo)) else "nan"
        cihi_s = f"{cihi:.4f}" if not (isinstance(cihi, float) and math.isnan(cihi)) else "nan"
        print(f"[E-0013b] {cell}: parseable steer={s:.3f} prompt={p:.3f} | "
              f"complete-case {ccp_s} CI[{cilo_s},{cihi_s}] n_pairs={cc['n_compliant_sample_pairs']} "
              f"excl0={cc['excludes_zero']} | bounds cross_zero={bd['crosses_zero']} "
              f"{[round(b['delta'],4) for b in bd['bounds']]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
