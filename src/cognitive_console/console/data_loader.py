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
    return {
        "kind": "console_v1_simulated_demo",
        "source": "computed from frozen artifacts by cognitive_console.console.data_loader",
        "c1_source_mode": payload["c1"]["source_mode"],
        "c2_source_mode": payload["c2"]["source_mode"],
        "arm_source_mode": payload["arm"]["source_mode"],
        "facade_limit_flags": facade_flags,
        "facade_non_flags": facade_non_flags,
        "steering_degradation_flags": steering_degradation_flags,
        "arm_uncertainty_harm_flags": arm_uncertainty_flags,
        "summary": {
            "facade_limit_axes": [row["axis"] for row in facade_flags],
            "steering_degradation_or_fail_axes": [row["axis"] for row in steering_degradation_flags],
            "robust_uncertainty_harm_cells": [row["cell_key"] for row in arm_uncertainty_flags],
        },
    }


def build_console_payload(
    c2b_path: Optional[Path] = None,
    c1_path: Optional[Path] = None,
    arm_summary_path: Optional[Path] = None,
    evidence_ledger_path: Optional[Path] = None,
) -> Dict:
    root = _repo_root()
    c2b_path = c2b_path or (root / C2B_RESULTS_REL)
    c1_path = c1_path or (root / C1_RESULTS_REL)
    arm_summary_path = arm_summary_path or (root / ARM_SUMMARY_REL)
    evidence_ledger_path = evidence_ledger_path or (root / EVIDENCE_LEDGER_REL)

    c2b_data = _load_json(c2b_path)
    c1_rows, c1_source_mode = _load_c1_rows(c1_path, evidence_ledger_path)
    c2_rows = _build_c2_rows(c2b_data)
    arm_payload, arm_source_mode = _load_arm_rows(root, arm_summary_path, evidence_ledger_path)
    arm_payload["source_mode"] = arm_source_mode

    return {
        "title": "Dual-channel Cognitive Console v1 (Reality-check Instrument)",
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
        },
        "c2": {
            "evidence_id": "E-0005",
            "source_mode": "results_c2b_json",
            "bonferroni_ci_level": c2b_data.get("frozen_params", {}).get("bonferroni_ci_level"),
            "delta": c2b_data.get("frozen_params", {}).get("delta"),
            "rows": c2_rows,
        },
        "arm": arm_payload,
        "trust_calibration": _build_trust_calibration(c2_rows),
        "provenance": {
            "c2b_results": _as_rel(c2b_path),
            "c1_results": _as_rel(c1_path),
            "arm_summary": _as_rel(arm_summary_path),
            "evidence_ledger_fallback": _as_rel(evidence_ledger_path),
            "artifact_presence": {
                "c2b_results": c2b_path.exists(),
                "c1_results": c1_path.exists(),
                "arm_summary": arm_summary_path.exists(),
            },
        },
    }
