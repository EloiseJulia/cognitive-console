from __future__ import annotations

import json
import re
from pathlib import Path
from statistics import mean
from typing import Dict, List, Optional, Tuple

AXIS_LABELS = {
    "deliberation": "Deliberation",
    "skepticism": "Skepticism",
    "uncertainty_awareness": "Uncertainty-awareness",
    "focus": "Focus",
}

C1_RESULTS_REL = Path("results") / "gpu_7b_2026-07-23" / "c1" / "c1_facade_results.json"
C2B_RESULTS_REL = Path("results") / "c2b_adjudication_hf_2026-07-24" / "c2b_adjudication_results.json"
ARM_SUMMARY_REL = Path("results") / "arm_full" / "arm_matrix_summary.json"
LLAMA_C1_RESULTS_REL = Path("results") / "llama_c1_facade_2026-07-24" / "c1_facade_results.json"
SOCIAL_BEHAVIOR_REL = Path("results") / "flagship_powered" / "behavior" / "flagship_l0_results.json"
SOCIAL_READ_REL = Path("results") / "flagship_powered" / "read" / "flagship_read_results.json"
PSR_RESULTS_REL = Path("results") / "psr_qwen_primary" / "psr_c2b_adjudication_results.json"
EVIDENCE_LEDGER_REL = Path("docs") / "ledgers" / "evidence-ledger.md"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _axis_label(axis: str) -> str:
    return AXIS_LABELS.get(axis, axis)


def _as_rel(path: Path) -> str:
    root = _repo_root()
    try:
        return str(path.resolve().relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path.resolve()).replace("\\", "/")


def _load_json(path: Path) -> Dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _load_c1_from_results(c1_path: Path) -> List[Dict]:
    data = _load_json(c1_path)
    rows: List[Dict] = []
    for axis_row in data.get("axes", []):
        axis = str(axis_row.get("axis"))
        rows.append(
            {
                "axis": axis,
                "label": _axis_label(axis),
                "prompt_reach": axis_row.get("prompt_reach"),
                "pole_reach": axis_row.get("pole_reach"),
                "ratio": axis_row.get("facade_ratio"),
                "ci_lo": axis_row.get("facade_ratio_ci_lo"),
                "ci_hi": axis_row.get("facade_ratio_ci_hi"),
                "ci_level": axis_row.get("facade_ratio_ci_level"),
                "holds_ci": bool(axis_row.get("facade_gap_holds_ci", False)),
                "limit_flag": bool(axis_row.get("facade_gap_holds_ci", False)),
                "source": "c1_results_json",
            }
        )
    return rows


def _parse_e0003_line(text: str) -> Dict[str, Tuple[float, float, float]]:
    out: Dict[str, Tuple[float, float, float]] = {}
    patterns = {
        "deliberation": r"deliberation\s+([0-9.]+)\s*\[\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\]",
        "skepticism": r"skepticism\s+([0-9.]+)\s*\[\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\]",
        "uncertainty_awareness": r"uncertainty\s+([0-9.]+)\s*\[\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\]",
    }
    for axis, pat in patterns.items():
        m = re.search(pat, text, flags=re.IGNORECASE)
        if not m:
            continue
        out[axis] = (float(m.group(1)), float(m.group(2)), float(m.group(3)))
    return out


_SIGNED_FLOAT = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)"


def _load_c1_fallback_from_evidence(evidence_ledger_path: Path) -> List[Dict]:
    text = evidence_ledger_path.read_text(encoding="utf-8")
    line = None
    for ln in text.splitlines():
        if ln.startswith("| E-0003 "):
            line = ln
            break
    if line is None:
        raise ValueError("Could not find E-0003 row in evidence ledger fallback.")
    parsed = _parse_e0003_line(line)
    if not parsed:
        raise ValueError("Could not parse C1 ratio+CI from E-0003 fallback text.")
    rows = []
    for axis in ["deliberation", "skepticism", "uncertainty_awareness"]:
        if axis not in parsed:
            continue
        ratio, ci_lo, ci_hi = parsed[axis]
        rows.append(
            {
                "axis": axis,
                "label": _axis_label(axis),
                "prompt_reach": None,
                "pole_reach": None,
                "ratio": ratio,
                "ci_lo": ci_lo,
                "ci_hi": ci_hi,
                "ci_level": None,
                "holds_ci": ci_hi < 1.0,
                "limit_flag": ci_hi < 1.0,
                "source": "evidence_ledger_e0003_fallback",
                "note": "prompt_reach/pole_reach unavailable in fallback source.",
            }
        )
    return rows


def _load_c1_rows(c1_path: Path, evidence_ledger_path: Path) -> Tuple[List[Dict], str]:
    if c1_path.exists():
        return _load_c1_from_results(c1_path), "results_c1_json"
    return _load_c1_fallback_from_evidence(evidence_ledger_path), "evidence_ledger_fallback"


def _parse_e0005_line(text: str) -> Dict[str, Tuple[float, float, float]]:
    out: Dict[str, Tuple[float, float, float]] = {}
    patterns = {
        "deliberation": rf"deliberation\s+\**({_SIGNED_FLOAT})\s*\[\s*({_SIGNED_FLOAT})\s*,\s*({_SIGNED_FLOAT})\s*\]\**",
        "skepticism": rf"skepticism\s+\**({_SIGNED_FLOAT})\s*\[\s*({_SIGNED_FLOAT})\s*,\s*({_SIGNED_FLOAT})\s*\]\**",
        "uncertainty_awareness": rf"uncertainty\s+\**({_SIGNED_FLOAT})\s*\[\s*({_SIGNED_FLOAT})\s*,\s*({_SIGNED_FLOAT})\s*\]\**",
    }
    for axis, pat in patterns.items():
        m = re.search(pat, text, flags=re.IGNORECASE)
        if not m:
            continue
        out[axis] = (float(m.group(1)), float(m.group(2)), float(m.group(3)))
    return out


def _load_c2_fallback_from_evidence(evidence_ledger_path: Path) -> Dict:
    text = evidence_ledger_path.read_text(encoding="utf-8")
    line = next((ln for ln in text.splitlines() if ln.startswith("| E-0005 ")), "")
    if not line:
        raise ValueError("Could not find E-0005 row in evidence ledger fallback.")
    parsed = _parse_e0005_line(line)
    if not parsed:
        raise ValueError("Could not parse C2 mean-diff+CI from E-0005 fallback text.")
    delta_match = re.search(r"δ=([0-9.]+)", line)
    ci_match = re.search(r"Bonferroni CI\s+([0-9.]+)", line, flags=re.IGNORECASE)
    verdict_match = re.search(r"VERDICT=([A-Z0-9_]+)", line)
    axes = []
    for axis in ["deliberation", "skepticism", "uncertainty_awareness"]:
        if axis not in parsed:
            continue
        mean_diff, ci_lo, ci_hi = parsed[axis]
        axes.append(
            {
                "axis": axis,
                "mean_diff": mean_diff,
                "ci_lo": ci_lo,
                "ci_hi": ci_hi,
                "passed": False,
                "coherence_ok": "coherence gates ok" in line.lower(),
                "source": "evidence_ledger_e0005_fallback",
                "note": "per-item prompt/steer values unavailable in fallback source.",
            }
        )
    return {
        "verdict": verdict_match.group(1) if verdict_match else None,
        "frozen_params": {
            "bonferroni_ci_level": float(ci_match.group(1)) if ci_match else None,
            "delta": float(delta_match.group(1)) if delta_match else None,
        },
        "axes": axes,
        "note": "Fallback parses C2 adjudication summary only from evidence-ledger E-0005.",
    }


def _load_c2_data(c2b_path: Path, evidence_ledger_path: Path) -> Tuple[Dict, str]:
    if c2b_path.exists():
        return _load_json(c2b_path), "results_c2b_json"
    return _load_c2_fallback_from_evidence(evidence_ledger_path), "evidence_ledger_e0005_fallback"


def _build_c2_rows(c2b_data: Dict) -> List[Dict]:
    rows: List[Dict] = []
    for axis_row in c2b_data.get("axes", []):
        axis = str(axis_row.get("axis"))
        prompt_values = axis_row.get("per_item_prompt", [])
        steer_values = axis_row.get("per_item_steer", [])
        prompt_mean = mean(prompt_values) if prompt_values else None
        steer_mean = mean(steer_values) if steer_values else None
        rows.append(
            {
                "axis": axis,
                "label": _axis_label(axis),
                "mean_diff": axis_row.get("mean_diff"),
                "ci_lo": axis_row.get("ci_lo"),
                "ci_hi": axis_row.get("ci_hi"),
                "ci_level": axis_row.get("ci_level"),
                "passed": bool(axis_row.get("passed", False)),
                "fail_flag": not bool(axis_row.get("passed", False)),
                "degradation_flag": isinstance(axis_row.get("mean_diff"), (int, float))
                and axis_row.get("mean_diff") < 0,
                "robust_degradation_flag": isinstance(axis_row.get("mean_diff"), (int, float))
                and isinstance(axis_row.get("ci_hi"), (int, float))
                and axis_row.get("mean_diff") < 0
                and axis_row.get("ci_hi") < 0,
                "coherence_ok": bool(axis_row.get("coherence_ok", False)),
                "delta": axis_row.get("delta"),
                "prompt_mean": prompt_mean,
                "steer_mean": steer_mean,
                "best_prompt_id": axis_row.get("dev_selection", {}).get("best_prompt_id"),
                "dev_prompt_outcome": axis_row.get("dev_selection", {}).get("dev_prompt_outcome"),
                "source": axis_row.get("source", "c2b_results_json"),
                "note": axis_row.get("note"),
                "conflict_latent_drags_down": bool(
                    axis_row.get("conflict", {}).get("latent_drags_down", False)
                ),
            }
        )
    return rows


def _build_trust_calibration(c2_rows: List[Dict]) -> List[Dict]:
    notes: List[Dict] = []
    for row in c2_rows:
        axis = row["axis"]
        mean_diff = row["mean_diff"]
        ci_hi = row["ci_hi"]
        ci_lo = row["ci_lo"]
        severity = "amber"
        title = f"{row['label']}: latent control not reliable as a default"
        body = "Use prompt channel as default; latent intervention should be audited case-by-case."
        if isinstance(mean_diff, (int, float)) and isinstance(ci_hi, (int, float)) and mean_diff < 0 and ci_hi < 0:
            severity = "red"
            title = f"{row['label']}: do not trust latent control by default"
            body = (
                f"Observed harm is robust (Δ={mean_diff:.3f}, CI [{ci_lo:.3f}, {ci_hi:.3f}]). "
                "Treat this as a trust boundary; the mechanism remains open."
            )
        elif isinstance(mean_diff, (int, float)) and mean_diff < 0:
            severity = "amber"
            body = (
                f"Observed degradation trend (Δ={mean_diff:.3f}) with uncertainty crossing zero. "
                "Do not claim latent advantage."
            )
        if axis == "uncertainty_awareness" and isinstance(mean_diff, (int, float)):
            title = "Uncertainty-awareness boundary: latent control can worsen calibration"
            if isinstance(ci_hi, (int, float)) and ci_hi < 0:
                severity = "red"
                body = (
                    f"Critical warning: steering underperforms prompt (Δ={mean_diff:.3f}, "
                    f"CI [{ci_lo:.3f}, {ci_hi:.3f}]). Use prompt channel; latent is boundary-only."
                )
        notes.append({"axis": axis, "severity": severity, "title": title, "body": body})
    return notes


def _read_signal_from_c1(row: Optional[Dict]) -> Dict:
    if not row:
        return {
            "status": "UNTESTED",
            "value": None,
            "ci_lo": None,
            "ci_hi": None,
            "source": None,
            "summary": "No local C1 READ artifact for this axis.",
        }
    status = "HOLDS" if row.get("holds_ci") else "FAILS"
    return {
        "status": status,
        "metric": "facade_ratio_ci",
        "value": row.get("ratio"),
        "ci_lo": row.get("ci_lo"),
        "ci_hi": row.get("ci_hi"),
        "source": row.get("source"),
        "summary": f"facade ratio={row.get('ratio'):.3f}" if isinstance(row.get("ratio"), (int, float)) else "facade ratio unavailable",
    }


def _transfer_signal_from_c2(row: Optional[Dict]) -> Dict:
    if not row:
        return {
            "verdict": "UNTESTED",
            "delta": None,
            "ci_lo": None,
            "ci_hi": None,
            "passed": None,
            "summary": "No local C2 behavior artifact for this axis.",
        }
    verdict = "PASS" if row.get("passed") else "FAIL"
    return {
        "verdict": verdict,
        "delta": row.get("mean_diff"),
        "ci_lo": row.get("ci_lo"),
        "ci_hi": row.get("ci_hi"),
        "passed": row.get("passed"),
        "bonferroni_ci_level": row.get("ci_level"),
        "source": row.get("source"),
        "summary": f"Δ={row.get('mean_diff'):.3f}" if isinstance(row.get("mean_diff"), (int, float)) else "Δ unavailable",
    }


def _prompt_ceiling_from_c2(row: Optional[Dict]) -> Dict:
    if not row:
        return {"status": "UNTESTED", "value": None, "summary": "No bounded-prompt comparator loaded."}
    return {
        "status": "LOADED",
        "value": row.get("prompt_mean"),
        "best_prompt_id": row.get("best_prompt_id"),
        "dev_prompt_outcome": row.get("dev_prompt_outcome"),
        "summary": (
            f"TEST prompt mean={row.get('prompt_mean'):.3f}"
            if isinstance(row.get("prompt_mean"), (int, float))
            else "prompt ceiling loaded from DEV-selected best prompt"
        ),
    }


def _calibration_harm_from_c2(row: Optional[Dict], arm_payload: Dict) -> Dict:
    if not row:
        return {"status": "UNTESTED", "severity": "none", "summary": "No calibration artifact loaded."}
    harm = bool(row.get("robust_degradation_flag"))
    arm_cells = []
    if row.get("axis") == "uncertainty_awareness":
        for cell in arm_payload.get("cells", []):
            unc = next((axis for axis in cell.get("axes", []) if axis.get("axis") == "uncertainty_awareness"), None)
            if unc:
                arm_cells.append(
                    {
                        "cell_key": cell.get("cell_key"),
                        "method": cell.get("method"),
                        "model_label": cell.get("model_label"),
                        "delta": unc.get("mean_diff"),
                        "ci_lo": unc.get("ci_lo"),
                        "ci_hi": unc.get("ci_hi"),
                        "robust_harm": unc.get("robust_degradation_flag"),
                    }
                )
    return {
        "status": "HARM" if harm else "NO_ROBUST_HARM",
        "severity": "red" if harm else "amber",
        "delta": row.get("mean_diff"),
        "ci_lo": row.get("ci_lo"),
        "ci_hi": row.get("ci_hi"),
        "arm_replications": arm_cells,
        "summary": (
            f"calibration harm Δ={row.get('mean_diff'):.3f}, CI=[{row.get('ci_lo'):.3f},{row.get('ci_hi'):.3f}]"
            if harm
            and isinstance(row.get("mean_diff"), (int, float))
            and isinstance(row.get("ci_lo"), (int, float))
            and isinstance(row.get("ci_hi"), (int, float))
            else "No robust calibration harm flag for this axis."
        ),
    }


def _card_verdict(read_signal: Dict, transfer_signal: Dict, calibration_harm: Dict) -> str:
    if read_signal.get("status") == "HOLDS" and transfer_signal.get("verdict") in {"FAIL", "NULL"}:
        return "LEGIBLE: no added control demonstrated"
    if calibration_harm.get("status") == "HARM":
        return "CONTROL ATTEMPT HARMS CALIBRATION"
    if read_signal.get("status") == "HOLDS" and transfer_signal.get("verdict") == "PASS":
        return "LEGIBLE and TRANSFERS"
    if read_signal.get("status") == "FAILS":
        return "NOT LEGIBLE as facade axis"
    return "UNTESTED BOUNDARY"


def _build_axis_cards(c1_rows: List[Dict], c2_rows: List[Dict], arm_payload: Dict) -> List[Dict]:
    c1_by_axis = {row["axis"]: row for row in c1_rows}
    c2_by_axis = {row["axis"]: row for row in c2_rows}
    cards = []
    for axis in ["deliberation", "uncertainty_awareness", "focus"]:
        c1 = c1_by_axis.get(axis)
        c2 = c2_by_axis.get(axis)
        read = _read_signal_from_c1(c1)
        transfer = _transfer_signal_from_c2(c2)
        prompt_ceiling = _prompt_ceiling_from_c2(c2)
        calibration = _calibration_harm_from_c2(c2, arm_payload)
        cards.append(
            {
                "axis": axis,
                "label": _axis_label(axis),
                "evidence_ids": ["E-0003", "E-0005", "E-0006"] if c2 else ["E-0003", "E-0008"],
                "headline": _card_verdict(read, transfer, calibration),
                "read_status": read,
                "transfer_verdict": transfer,
                "prompt_ceiling": prompt_ceiling,
                "calibration_harm": calibration,
                "evidence_tier": {
                    "tier": "exploratory",
                    "notes": ["single-run facade READ", "C2 behavior has 2×2 robustness for uncertainty harm"],
                },
                "source_files": {
                    "c1": c1.get("source") if c1 else None,
                    "c2": c2.get("source") if c2 else None,
                    "arm": ARM_SUMMARY_REL.as_posix(),
                },
            }
        )
    return cards


def _load_social_card(behavior_path: Path, read_path: Path) -> Dict:
    behavior = _load_json(behavior_path)
    read = _load_json(read_path)
    selected_layer = str(read.get("selected_layer"))
    selected = read.get("layer_results", {}).get(selected_layer, {})
    token_blind = selected.get("token_blind", {})
    literal = selected.get("literal", {})
    null = read.get("random_direction_null", {})
    ba_m1 = behavior.get("paired_bootstrap", {}).get("B_minus_A", {}).get("M1", {})
    be_m1 = behavior.get("paired_bootstrap", {}).get("B_minus_E", {}).get("M1", {})
    m4 = behavior.get("condition_means", {}).get("M4", {})
    read_status = {
        "status": read.get("read_verdict", {}).get("status", "UNTESTED").replace("READ_", ""),
        "metric": "token_blind_auc",
        "value": token_blind.get("auc"),
        "literal_auc": literal.get("auc"),
        "auc_drop_pp": selected.get("auc_drop_pp"),
        "null_p95": null.get("token_blind_auc_p95"),
        "selected_layer": read.get("selected_layer"),
        "source": _as_rel(read_path),
        "summary": (
            f"token-blind AUC={token_blind.get('auc'):.3f}"
            if isinstance(token_blind.get("auc"), (int, float))
            else "token-blind AUC unavailable"
        ),
    }
    transfer = {
        "verdict": "NULL"
        if not ba_m1.get("passes_effect_rule_without_human_alpha", False)
        else "PASS",
        "contrast": "B_minus_A",
        "metric": "M1 option-pushing",
        "delta": ba_m1.get("point_estimate"),
        "ci_lo": ba_m1.get("ci_low"),
        "ci_hi": ba_m1.get("ci_high"),
        "p_bonferroni": ba_m1.get("p_bonferroni"),
        "source": _as_rel(behavior_path),
        "summary": (
            f"B−A M1={ba_m1.get('point_estimate'):.5f}, p_bonf={ba_m1.get('p_bonferroni'):.1f}"
            if isinstance(ba_m1.get("point_estimate"), (int, float))
            and isinstance(ba_m1.get("p_bonferroni"), (int, float))
            else "B−A M1 unavailable"
        ),
    }
    prompt_ceiling = {
        "status": "LOADED",
        "condition": "B_novice",
        "metric": "condition_mean_M1",
        "value": behavior.get("condition_means", {}).get("M1", {}).get("B"),
        "summary": "bounded social prompt condition B mean loaded from behavior artifact",
    }
    calibration = {
        "status": "NO_CALIBRATION_AXIS",
        "severity": "none",
        "m4_deference_means": m4,
        "summary": "Social card measures option-pushing/deference, not uncertainty calibration.",
    }
    evidence_tier = {
        "tier": "exploratory",
        "notes": [
            behavior.get("behavioral_verdict", {}).get("status", "human-alpha PENDING"),
            behavior.get("behavioral_verdict", {}).get("human_alpha_gate", "human-alpha PENDING"),
            "single model",
            "single seed",
            "LLM-judge-only",
        ],
    }
    return {
        "axis": "social_inference_novice_disclosure",
        "label": "Social inference: novice-disclosure",
        "evidence_ids": ["E-0010"],
        "headline": _card_verdict(read_status, transfer, calibration),
        "read_status": read_status,
        "transfer_verdict": transfer,
        "prompt_ceiling": prompt_ceiling,
        "calibration_harm": calibration,
        "evidence_tier": evidence_tier,
        "secondary_contrasts": {
            "B_minus_E_M1_delta": be_m1.get("point_estimate"),
            "B_minus_E_M1_p_bonferroni": be_m1.get("p_bonferroni"),
            "M4_deference_all_conditions": m4,
        },
        "source_files": {"behavior": _as_rel(behavior_path), "read": _as_rel(read_path)},
    }


def _load_psr_panel(psr_path: Path) -> Dict:
    data = _load_json(psr_path)
    rows = []
    for axis_row in data.get("axes", []):
        rows.append(
            {
                "axis": axis_row.get("axis"),
                "label": _axis_label(str(axis_row.get("axis"))),
                "delta": axis_row.get("mean_diff"),
                "ci_lo": axis_row.get("ci_lo"),
                "ci_hi": axis_row.get("ci_hi"),
                "passed": bool(axis_row.get("passed", False)),
                "best_prompt_id": axis_row.get("dev_selection", {}).get("best_prompt_id"),
                "dev_prompt_outcome": axis_row.get("dev_selection", {}).get("dev_prompt_outcome"),
                "source": _as_rel(psr_path),
            }
        )
    return {
        "evidence_id": "E-0009",
        "source_mode": "results_psr_qwen_primary_json",
        "verdict": data.get("verdict"),
        "rows": rows,
        "summary": "DEV-optimized PSR-style latent recovery also fails all C2 axes on TEST.",
        "evidence_tier": {
            "tier": "exploratory",
            "notes": ["single model", "single seed", "method-strength robustness marker"],
        },
    }


def _cell_result_path(root: Path, cell: Dict) -> Path:
    key = str(cell.get("cell_key"))
    return root / "results" / "arm_full" / f"cell_{key}" / "c2b_adjudication_results.json"


def _load_arm_from_results(root: Path, arm_summary_path: Path) -> Tuple[Dict, str]:
    summary = _load_json(arm_summary_path)
    cells: List[Dict] = []
    for cell in summary.get("cells", []):
        result_path = _cell_result_path(root, cell)
        axes = []
        if result_path.exists():
            result = _load_json(result_path)
            for axis_row in result.get("axes", []):
                axis = str(axis_row.get("axis"))
                axes.append(
                    {
                        "axis": axis,
                        "label": _axis_label(axis),
                        "mean_diff": axis_row.get("mean_diff"),
                        "ci_lo": axis_row.get("ci_lo"),
                        "ci_hi": axis_row.get("ci_hi"),
                        "passed": bool(axis_row.get("passed", False)),
                        "degradation_flag": isinstance(axis_row.get("mean_diff"), (int, float))
                        and axis_row.get("mean_diff") < 0,
                        "robust_degradation_flag": isinstance(axis_row.get("mean_diff"), (int, float))
                        and isinstance(axis_row.get("ci_hi"), (int, float))
                        and axis_row.get("mean_diff") < 0
                        and axis_row.get("ci_hi") < 0,
                    }
                )
        cells.append(
            {
                "cell_key": cell.get("cell_key"),
                "method": cell.get("method"),
                "model_label": cell.get("model_label"),
                "verdict": cell.get("verdict"),
                "axes_passed": cell.get("axes_passed"),
                "axis_passes": cell.get("axis_passes"),
                "result_file": _as_rel(result_path),
                "result_present": result_path.exists(),
                "axes": axes,
            }
        )
    return (
        {
            "evidence_id": "E-0006",
            "arm_verdict": summary.get("arm_verdict"),
            "zero_pass_cells": summary.get("zero_pass_cells"),
            "n_cells": summary.get("n_cells"),
            "cells": cells,
        },
        "results_arm_full_json",
    )


def _load_arm_fallback_from_evidence(evidence_ledger_path: Path) -> Tuple[Dict, str]:
    text = evidence_ledger_path.read_text(encoding="utf-8")
    line = next((ln for ln in text.splitlines() if ln.startswith("| E-0006 ")), "")
    pattern = re.compile(
        r"(CAA|ITI)×(Qwen|Llama)\s+(-?[0-9.]+)\s*\[\s*(-?[0-9.]+)\s*,\s*(-?[0-9.]+)\s*\]",
        flags=re.IGNORECASE,
    )
    cells = []
    for method, model, mean_diff, ci_lo, ci_hi in pattern.findall(line):
        mean_v = float(mean_diff)
        hi_v = float(ci_hi)
        cells.append(
            {
                "cell_key": f"{method.lower()}__{model.lower()}_fallback",
                "method": method.lower(),
                "model_label": model,
                "verdict": "KILL_PLAN_D",
                "axes_passed": 0,
                "axis_passes": {"uncertainty_awareness": False},
                "result_file": _as_rel(evidence_ledger_path),
                "result_present": False,
                "axes": [
                    {
                        "axis": "uncertainty_awareness",
                        "label": _axis_label("uncertainty_awareness"),
                        "mean_diff": mean_v,
                        "ci_lo": float(ci_lo),
                        "ci_hi": hi_v,
                        "passed": False,
                        "degradation_flag": mean_v < 0,
                        "robust_degradation_flag": mean_v < 0 and hi_v < 0,
                    }
                ],
            }
        )
    return (
        {
            "evidence_id": "E-0006",
            "arm_verdict": "NON_TRANSFER_GENERALIZED",
            "zero_pass_cells": 4 if cells else None,
            "n_cells": 4 if cells else None,
            "cells": cells,
            "note": "Fallback parses uncertainty-axis harm only from evidence-ledger E-0006.",
        },
        "evidence_ledger_fallback",
    )


def _load_arm_rows(root: Path, arm_summary_path: Path, evidence_ledger_path: Path) -> Tuple[Dict, str]:
    if arm_summary_path.exists():
        return _load_arm_from_results(root, arm_summary_path)
    return _load_arm_fallback_from_evidence(evidence_ledger_path)


def build_demo_report(payload: Dict) -> Dict:
    facade_flags = [
        {
            "axis": row["axis"],
            "label": row["label"],
            "ratio": row["ratio"],
            "ci_lo": row["ci_lo"],
            "ci_hi": row["ci_hi"],
            "source": row["source"],
        }
        for row in payload["c1"]["rows"]
        if row.get("limit_flag")
    ]
    facade_non_flags = [
        {
            "axis": row["axis"],
            "label": row["label"],
            "ratio": row["ratio"],
            "ci_lo": row["ci_lo"],
            "ci_hi": row["ci_hi"],
            "source": row["source"],
        }
        for row in payload["c1"]["rows"]
        if not row.get("limit_flag")
    ]
    steering_degradation_flags = [
        {
            "axis": row["axis"],
            "label": row["label"],
            "mean_diff": row["mean_diff"],
            "ci_lo": row["ci_lo"],
            "ci_hi": row["ci_hi"],
            "passed": row["passed"],
            "robust": row["robust_degradation_flag"],
        }
        for row in payload["c2"]["rows"]
        if row.get("degradation_flag") or row.get("fail_flag")
    ]
    arm_uncertainty_flags = []
    for cell in payload["arm"]["cells"]:
        for axis in cell.get("axes", []):
            if axis["axis"] == "uncertainty_awareness" and axis.get("robust_degradation_flag"):
                arm_uncertainty_flags.append(
                    {
                        "cell_key": cell["cell_key"],
                        "method": cell["method"],
                        "model_label": cell["model_label"],
                        "mean_diff": axis["mean_diff"],
                        "ci_lo": axis["ci_lo"],
                        "ci_hi": axis["ci_hi"],
                    }
                )
    social_cards = [
        card
        for card in payload.get("ui_contract", {}).get("cards", [])
        if card.get("axis") == "social_inference_novice_disclosure"
        and card.get("read_status", {}).get("status") == "HOLDS"
        and card.get("transfer_verdict", {}).get("verdict") == "NULL"
    ]
    psr_fail_axes = [
        row
        for row in payload.get("ui_contract", {}).get("psr_method_strength", {}).get("rows", [])
        if not row.get("passed")
    ]
    return {
        "kind": "console_v2_ui_contract_simulated_demo",
        "source": "computed from frozen artifacts by cognitive_console.console.data_loader",
        "constraints": "No humans, GPU, paid APIs, model downloads, or live model calls; frozen local artifact read only.",
        "c1_source_mode": payload["c1"]["source_mode"],
        "c2_source_mode": payload["c2"]["source_mode"],
        "arm_source_mode": payload["arm"]["source_mode"],
        "facade_limit_flags": facade_flags,
        "facade_non_flags": facade_non_flags,
        "steering_degradation_flags": steering_degradation_flags,
        "arm_uncertainty_harm_flags": arm_uncertainty_flags,
        "social_legible_but_not_controllable_flags": social_cards,
        "psr_method_strength_fail_flags": psr_fail_axes,
        "summary": {
            "facade_limit_axes": [row["axis"] for row in facade_flags],
            "steering_degradation_or_fail_axes": [row["axis"] for row in steering_degradation_flags],
            "robust_uncertainty_harm_cells": [row["cell_key"] for row in arm_uncertainty_flags],
            "legible_but_not_controllable_axes": [row["axis"] for row in social_cards],
            "psr_fail_axes": [row["axis"] for row in psr_fail_axes],
        },
    }


def build_console_payload(
    c2b_path: Optional[Path] = None,
    c1_path: Optional[Path] = None,
    arm_summary_path: Optional[Path] = None,
    social_behavior_path: Optional[Path] = None,
    social_read_path: Optional[Path] = None,
    psr_path: Optional[Path] = None,
    evidence_ledger_path: Optional[Path] = None,
) -> Dict:
    root = _repo_root()
    c2b_path = c2b_path or (root / C2B_RESULTS_REL)
    c1_path = c1_path or (root / C1_RESULTS_REL)
    llama_c1_path = root / LLAMA_C1_RESULTS_REL
    arm_summary_path = arm_summary_path or (root / ARM_SUMMARY_REL)
    social_behavior_path = social_behavior_path or (root / SOCIAL_BEHAVIOR_REL)
    social_read_path = social_read_path or (root / SOCIAL_READ_REL)
    psr_path = psr_path or (root / PSR_RESULTS_REL)
    evidence_ledger_path = evidence_ledger_path or (root / EVIDENCE_LEDGER_REL)

    c2b_data, c2_source_mode = _load_c2_data(c2b_path, evidence_ledger_path)
    c1_rows, c1_source_mode = _load_c1_rows(c1_path, evidence_ledger_path)
    c2_rows = _build_c2_rows(c2b_data)
    arm_payload, arm_source_mode = _load_arm_rows(root, arm_summary_path, evidence_ledger_path)
    arm_payload["source_mode"] = arm_source_mode
    cards = _build_axis_cards(c1_rows, c2_rows, arm_payload)
    if social_behavior_path.exists() and social_read_path.exists():
        cards.append(_load_social_card(social_behavior_path, social_read_path))
    psr_panel = _load_psr_panel(psr_path) if psr_path.exists() else {
        "evidence_id": "E-0009",
        "source_mode": "missing",
        "verdict": "UNTESTED",
        "rows": [],
        "summary": "PSR artifact missing.",
    }

    return {
        "title": "Dual-channel Cognitive Console v2 (UI-contract Reality-check Instrument)",
        "positioning": "Boundary/limit instrumentation + trust calibration. Not a latent superpower slider.",
        "verdict": c2b_data.get("verdict"),
        "channels": {
            "prompt_channel": "Human-readable instruction channel",
            "latent_channel": "CAA steering channel",
        },
        "c1": {
            "evidence_id": "E-0003",
            "source_mode": c1_source_mode,
            "rows": c1_rows,
            "replication": {
                "evidence_id": "E-0008",
                "source_mode": "results_llama_c1_json" if llama_c1_path.exists() else "missing",
                "rows": _load_c1_from_results(llama_c1_path) if llama_c1_path.exists() else [],
            },
        },
        "c2": {
            "evidence_id": "E-0005",
            "source_mode": c2_source_mode,
            "bonferroni_ci_level": c2b_data.get("frozen_params", {}).get("bonferroni_ci_level"),
            "delta": c2b_data.get("frozen_params", {}).get("delta"),
            "rows": c2_rows,
        },
        "arm": arm_payload,
        "trust_calibration": _build_trust_calibration(c2_rows),
        "ui_contract": {
            "kind": "latent-control affordance cards",
            "signals": [
                "READ status",
                "TRANSFER verdict",
                "PROMPT-CEILING",
                "CALIBRATION-HARM",
                "EVIDENCE-TIER",
            ],
            "cards": cards,
            "psr_method_strength": psr_panel,
        },
        "provenance": {
            "c2b_results": _as_rel(c2b_path),
            "c1_results": _as_rel(c1_path),
            "llama_c1_results": _as_rel(llama_c1_path),
            "arm_summary": _as_rel(arm_summary_path),
            "social_behavior": _as_rel(social_behavior_path),
            "social_read": _as_rel(social_read_path),
            "psr_results": _as_rel(psr_path),
            "evidence_ledger_fallback": _as_rel(evidence_ledger_path),
            "artifact_presence": {
                "c2b_results": c2b_path.exists(),
                "c1_results": c1_path.exists(),
                "llama_c1_results": llama_c1_path.exists(),
                "arm_summary": arm_summary_path.exists(),
                "social_behavior": social_behavior_path.exists(),
                "social_read": social_read_path.exists(),
                "psr_results": psr_path.exists(),
            },
        },
    }
