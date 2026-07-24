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
                "source": "evidence_ledger_e0003_fallback",
                "note": "prompt_reach/pole_reach unavailable in fallback source.",
            }
        )
    return rows


def _load_c1_rows(c1_path: Path, c2b_data: Dict, evidence_ledger_path: Path) -> Tuple[List[Dict], str]:
    if c1_path.exists():
        return _load_c1_from_results(c1_path), "results_c1_json"
    c2b_c1 = c2b_data.get("c1")
    if isinstance(c2b_c1, dict) and isinstance(c2b_c1.get("axes"), list):
        rows = []
        for axis_row in c2b_c1["axes"]:
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
                    "source": "c2b_embedded_c1",
                }
            )
        return rows, "c2b_embedded_c1"
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
                "Treat this as an off-manifold risk boundary."
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


def build_console_payload(
    c2b_path: Optional[Path] = None,
    c1_path: Optional[Path] = None,
    evidence_ledger_path: Optional[Path] = None,
) -> Dict:
    root = _repo_root()
    c2b_path = c2b_path or (root / "results" / "c2b_adjudication_hf_2026-07-24" / "c2b_adjudication_results.json")
    c1_path = c1_path or (root / "results" / "gpu_7b_2026-07-23" / "c1" / "c1_facade_results.json")
    evidence_ledger_path = evidence_ledger_path or (root / "docs" / "ledgers" / "evidence-ledger.md")

    c2b_data = _load_json(c2b_path)
    c1_rows, c1_source_mode = _load_c1_rows(c1_path, c2b_data, evidence_ledger_path)
    c2_rows = _build_c2_rows(c2b_data)

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
            "bonferroni_ci_level": c2b_data.get("frozen_params", {}).get("bonferroni_ci_level"),
            "delta": c2b_data.get("frozen_params", {}).get("delta"),
            "rows": c2_rows,
        },
        "trust_calibration": _build_trust_calibration(c2_rows),
        "provenance": {
            "c2b_results": _as_rel(c2b_path),
            "c1_results": _as_rel(c1_path),
            "evidence_ledger_fallback": _as_rel(evidence_ledger_path),
        },
    }

