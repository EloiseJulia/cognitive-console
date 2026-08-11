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

AXIS_TASK_OUTCOMES = {
    "deliberation": {
        "task": "frozen deliberation item pool",
        "outcome": "binary deliberation success",
    },
    "skepticism": {
        "task": "frozen false-premise item pool",
        "outcome": "binary skepticism success",
    },
    "uncertainty_awareness": {
        "task": "frozen confidence-reporting item pool",
        "outcome": "per-item 1-Brier",
    },
    "focus": {
        "task": "exploratory focus probe pool",
        "outcome": "focus proxy",
    },
}

_TIER_MATCH_FIELDS = (
    "model",
    "method",
    "file_hash",
    "split_hash",
    "axis",
    "layer",
    "task",
    "outcome",
)

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


def _model_identity_key(model: object) -> Optional[str]:
    if not isinstance(model, str) or not model.strip():
        return None
    return model.replace("\\", "/").rstrip("/").rsplit("/", 1)[-1].lower()


def _axis_task_outcome(axis: str) -> Dict[str, str]:
    return AXIS_TASK_OUTCOMES.get(
        axis,
        {
            "task": f"{axis} task",
            "outcome": f"{axis} outcome",
        },
    )


def _tier_identity(
    *,
    model: object,
    method: object,
    axis: str,
    direction: object,
    layer: object,
    task: object,
    outcome: object,
    protocol: object,
    version: object,
    comparator: object,
    comparator_required: bool,
    source: str,
) -> Dict:
    identity = {
        "model": _model_identity_key(model),
        "method": str(method).lower() if method not in (None, "") else None,
        "direction_id": (
            direction.get("direction_id")
            if isinstance(direction, dict)
            else (str(direction) if direction not in (None, "") else None)
        ),
        "file_hash": direction.get("file_hash") if isinstance(direction, dict) else None,
        "split_hash": direction.get("split_hash") if isinstance(direction, dict) else None,
        "axis": axis if axis else None,
        "layer": int(layer) if isinstance(layer, (int, float)) else None,
        "task": task,
        "outcome": outcome,
        "protocol": protocol,
        "version": version,
        "comparator": comparator,
        "source": source,
    }
    required = [
        "model",
        "method",
        "file_hash",
        "split_hash",
        "axis",
        "layer",
        "protocol",
        "version",
    ]
    if task is not None or outcome is not None:
        required.extend(["task", "outcome"])
    if comparator_required:
        required.append("comparator")
    missing = [field for field in required if identity.get(field) in (None, "", {})]
    if comparator_required and isinstance(comparator, dict):
        if not comparator.get("kind") or not (
            comparator.get("best_prompt_id") or comparator.get("contrast")
        ):
            if "comparator" not in missing:
                missing.append("comparator")
    identity["complete"] = not missing
    identity["missing_fields"] = missing
    return identity


def _compare_tier_identities(read_identity: Dict, transfer_identity: Dict) -> Dict:
    missing = []
    mismatches = []
    match_fields = list(_TIER_MATCH_FIELDS)
    if read_identity.get("direction_id") or transfer_identity.get("direction_id"):
        match_fields.append("direction_id")
    for field in match_fields:
        read_value = read_identity.get(field)
        transfer_value = transfer_identity.get(field)
        if read_value in (None, ""):
            missing.append(f"READ.{field}")
        if transfer_value in (None, ""):
            missing.append(f"TRANSFER.{field}")
        if read_value not in (None, "") and transfer_value not in (None, "") and read_value != transfer_value:
            mismatches.append(
                {
                    "field": field,
                    "read": read_value,
                    "transfer": transfer_value,
                }
            )
    if missing:
        status = "INCOMPLETE"
        reason = "Evidence-tier identity is incomplete: " + ", ".join(missing) + "."
    elif mismatches:
        status = "MISMATCH"
        details = "; ".join(
            f"{row['field']} READ={row['read']} TRANSFER={row['transfer']}"
            for row in mismatches
        )
        reason = f"READ and TRANSFER belong to different evidence tiers: {details}."
    else:
        status = "MATCH"
        reason = (
            "READ and TRANSFER share the same model, method, direction file/split "
            "identity, axis, layer, task, and outcome."
        )
    return {
        "status": status,
        "matched": status == "MATCH",
        "missing_fields": missing,
        "mismatches": mismatches,
        "reason": reason,
    }


def _c1_method(data: Dict) -> Optional[str]:
    explicit = data.get("steering_method") or data.get("method")
    if explicit:
        return str(explicit).lower()
    if str(data.get("kind", "")).startswith("c1_facade"):
        return "caa"
    return None


def _c2_method(data: Dict, source_mode: str) -> Optional[str]:
    explicit = data.get("steering_method") or data.get("method")
    if explicit:
        return str(explicit).lower()
    if source_mode in {"results_c2b_json", "evidence_ledger_e0005_fallback"}:
        return "caa"
    return None


def _direction_identity(data: Dict, row: Dict, method: object, axis: str) -> Dict:
    del method
    return {
        "direction_id": (
            row.get("direction_id")
            or row.get("direction_sha256")
            or data.get("direction_by_axis", {}).get(axis)
        ),
        "file_hash": (
            row.get("direction_file_hash")
            or row.get("file_hash")
            or data.get("direction_file_hash_by_axis", {}).get(axis)
        ),
        "split_hash": (
            row.get("direction_split_hash")
            or row.get("split_hash")
            or data.get("direction_split_hash_by_axis", {}).get(axis)
        ),
    }


def _protocol_version(data: Dict, protocol: object, fallback: object) -> object:
    explicit = (
        data.get("protocol_version")
        or data.get("schema_version")
        or data.get("config_fingerprint")
    )
    if explicit not in (None, ""):
        return explicit
    frozen = re.search(r"FROZEN\s+(\d{4}-\d{2}-\d{2})", str(protocol))
    if frozen:
        return f"frozen-{frozen.group(1)}"
    return fallback


def _load_c1_from_results(c1_path: Path) -> List[Dict]:
    data = _load_json(c1_path)
    method = _c1_method(data)
    version = _protocol_version(data, data.get("kind"), data.get("generated_at") or data.get("type"))
    rows: List[Dict] = []
    for axis_row in data.get("axes", []):
        axis = str(axis_row.get("axis"))
        target = _axis_task_outcome(axis)
        task = axis_row.get("task") or target["task"]
        outcome = axis_row.get("outcome") or target["outcome"]
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
                "tier_identity": _tier_identity(
                    model=data.get("model"),
                    method=method,
                    axis=axis,
                    direction=_direction_identity(data, axis_row, method, axis),
                    layer=axis_row.get("chosen_layer"),
                    task=task,
                    outcome=outcome,
                    protocol=data.get("kind"),
                    version=version,
                    comparator=None,
                    comparator_required=False,
                    source=_as_rel(c1_path),
                ),
                "target_task": task,
                "target_outcome": outcome,
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
                "tier_identity": _tier_identity(
                    model=None,
                    method=None,
                    axis=axis,
                    direction=None,
                    layer=None,
                    task=None,
                    outcome=None,
                    protocol="evidence-ledger E-0003 fallback",
                    version="E-0003",
                    comparator=None,
                    comparator_required=False,
                    source=_as_rel(evidence_ledger_path),
                ),
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


def _build_c2_rows(c2b_data: Dict, source_mode: str) -> List[Dict]:
    method = _c2_method(c2b_data, source_mode)
    protocol = c2b_data.get("prereg") or c2b_data.get("frozen_params", {}).get("prereg")
    version = _protocol_version(c2b_data, protocol, c2b_data.get("generated_at"))
    rows: List[Dict] = []
    for axis_row in c2b_data.get("axes", []):
        axis = str(axis_row.get("axis"))
        target = _axis_task_outcome(axis)
        task = axis_row.get("task") or target["task"]
        outcome = axis_row.get("outcome") or target["outcome"]
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
                "tier_identity": _tier_identity(
                    model=c2b_data.get("model"),
                    method=method,
                    axis=axis,
                    direction=_direction_identity(c2b_data, axis_row, method, axis),
                    layer=axis_row.get("layer"),
                    task=task,
                    outcome=outcome,
                    protocol=protocol,
                    version=version,
                    comparator={
                        "kind": "DEV-selected bounded prompt",
                        "best_prompt_id": axis_row.get("dev_selection", {}).get("best_prompt_id"),
                    },
                    comparator_required=True,
                    source=source_mode,
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
            "tier_identity": _tier_identity(
                model=None,
                method=None,
                axis="unknown",
                direction=None,
                layer=None,
                task=None,
                outcome=None,
                protocol=None,
                version=None,
                comparator=None,
                comparator_required=False,
                source="missing",
            ),
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
        "tier_identity": row.get("tier_identity", {}),
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
            "coherence_ok": None,
            "tier_identity": _tier_identity(
                model=None,
                method=None,
                axis="unknown",
                direction=None,
                layer=None,
                task=None,
                outcome=None,
                protocol=None,
                version=None,
                comparator=None,
                comparator_required=True,
                source="missing",
            ),
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
        "coherence_ok": row.get("coherence_ok"),
        "tier_identity": row.get("tier_identity", {}),
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


def _interface_mapping(
    read_signal: Dict,
    transfer_signal: Dict,
    calibration_harm: Dict,
) -> Dict:
    tier_match = _compare_tier_identities(
        read_signal.get("tier_identity", {}),
        transfer_signal.get("tier_identity", {}),
    )
    read_candidate = read_signal.get("status") == "HOLDS"
    transfer_pass = (
        transfer_signal.get("verdict") == "PASS"
        and transfer_signal.get("coherence_ok") is True
    )

    if not read_signal.get("tier_identity", {}).get("complete", False):
        code = "READ_TIER_INCOMPLETE"
        reason = (
            "READ evidence lacks a complete model, method, direction file/split, "
            "axis/layer, task/outcome, or protocol/version identity."
        )
    elif not transfer_signal.get("tier_identity", {}).get("complete", False):
        code = "TRANSFER_TIER_INCOMPLETE"
        reason = (
            "TRANSFER evidence lacks a complete direction file/split, task/outcome, "
            "protocol/version, or comparator identity."
        )
    elif not tier_match["matched"]:
        code = f"TIER_{tier_match['status']}"
        reason = tier_match["reason"]
    elif not read_candidate:
        code = "READ_NOT_SUPPORTED"
        reason = "READ is not supported within the matched evidence tier."
    elif transfer_signal.get("verdict") == "UNTESTED":
        code = "TRANSFER_UNTESTED"
        reason = "TRANSFER has not been tested against the bounded comparator in this tier."
    elif transfer_signal.get("coherence_ok") is False:
        code = "COHERENCE_NOT_MET"
        reason = "The comparative result does not satisfy the coherence requirement in this tier."
    elif transfer_signal.get("verdict") != "PASS":
        code = "TRANSFER_NOT_PASSED"
        reason = "TRANSFER did not pass the comparator-bound behavioral gate in this tier."
    elif calibration_harm.get("status") == "HARM":
        code = "CALIBRATION_HARM"
        reason = "The matched record carries a robust comparator-specific calibration warning."
    else:
        code = "NONE"
        reason = "No blocking reason remains within the exact matched tier."

    active_passes = transfer_pass and code == "NONE"
    read_summary = (
        "Read-only diagnostic candidate within this evidence tier."
        if read_candidate
        else "Read-only diagnostic candidate withheld because READ is unsupported."
    )
    active_summary = (
        "Active control passes the computational gate within exact tier."
        if active_passes
        else f"Active control withheld: {reason}"
    )
    return {
        "tier_match": tier_match,
        "computational_result": {
            "read": read_signal.get("status"),
            "transfer": transfer_signal.get("verdict"),
            "coherence_ok": transfer_signal.get("coherence_ok"),
            "calibration": calibration_harm.get("status"),
            "summary": (
                f"READ={read_signal.get('status')}; "
                f"TRANSFER={transfer_signal.get('verdict')}; "
                f"tier={tier_match['status']}."
            ),
        },
        "blocking_reason": {
            "code": code,
            "summary": reason,
        },
        "interface_action": {
            "read_only_diagnostic": {
                "eligibility": "candidate" if read_candidate else "withheld",
                "summary": read_summary,
            },
            "active_control": {
                "eligibility": (
                    "passes_computational_gate" if active_passes else "withheld"
                ),
                "summary": active_summary,
            },
            "summary": f"{read_summary} {active_summary}",
        },
    }


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
        mapping = _interface_mapping(read, transfer, calibration)
        cards.append(
            {
                "axis": axis,
                "label": _axis_label(axis),
                "evidence_ids": ["E-0003", "E-0005", "E-0006"] if c2 else ["E-0003", "E-0008"],
                "headline": mapping["interface_action"]["active_control"]["summary"],
                "read_status": read,
                "transfer_verdict": transfer,
                "prompt_ceiling": prompt_ceiling,
                "calibration_harm": calibration,
                "evidence_tier": {
                    "tier": "exploratory",
                    "read_identity": read.get("tier_identity"),
                    "transfer_identity": transfer.get("tier_identity"),
                    "match": mapping["tier_match"],
                    "notes": ["single-run facade READ", "C2 behavior has 2×2 robustness for uncertainty harm"],
                },
                "computational_result": mapping["computational_result"],
                "blocking_reason": mapping["blocking_reason"],
                "interface_action": mapping["interface_action"],
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
        "tier_identity": _tier_identity(
            model=read.get("config", {}).get("model"),
            method="caa",
            axis="social_inference_novice_disclosure",
            direction=read.get("direction_id"),
            layer=read.get("selected_layer"),
            task="novice-disclosure representational probe",
            outcome="token-blind AUC",
            protocol=read.get("config", {}).get("protocol_decision"),
            version=read.get("config_fingerprint"),
            comparator=None,
            comparator_required=False,
            source=_as_rel(read_path),
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
        "coherence_ok": None,
        "tier_identity": _tier_identity(
            model=behavior.get("config", {}).get("model"),
            method=behavior.get("config", {}).get("steering_method"),
            axis="social_inference_novice_disclosure",
            direction=behavior.get("direction_id"),
            layer=None,
            task=behavior.get("config", {}).get("task_pool"),
            outcome="M1 option-pushing",
            protocol=behavior.get("config", {}).get("protocol_decision"),
            version=behavior.get("config_fingerprint"),
            comparator={
                "kind": "paired condition",
                "contrast": "B_minus_A",
            },
            comparator_required=True,
            source=_as_rel(behavior_path),
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
    mapping = _interface_mapping(read_status, transfer, calibration)
    evidence_tier["read_identity"] = read_status["tier_identity"]
    evidence_tier["transfer_identity"] = transfer["tier_identity"]
    evidence_tier["match"] = mapping["tier_match"]
    return {
        "axis": "social_inference_novice_disclosure",
        "label": "Social inference: novice-disclosure",
        "evidence_ids": ["E-0010"],
        "headline": mapping["interface_action"]["active_control"]["summary"],
        "read_status": read_status,
        "transfer_verdict": transfer,
        "prompt_ceiling": prompt_ceiling,
        "calibration_harm": calibration,
        "evidence_tier": evidence_tier,
        "computational_result": mapping["computational_result"],
        "blocking_reason": mapping["blocking_reason"],
        "interface_action": mapping["interface_action"],
        "secondary_contrasts": {
            "B_minus_E_M1_delta": be_m1.get("point_estimate"),
            "B_minus_E_M1_p_bonferroni": be_m1.get("p_bonferroni"),
            "M4_deference_all_conditions": m4,
        },
        "source_files": {"behavior": _as_rel(behavior_path), "read": _as_rel(read_path)},
    }


def _load_psr_panel(psr_path: Path) -> Dict:
    data = _load_json(psr_path)
    method = data.get("steering_method")
    protocol = data.get("prereg") or data.get("frozen_params", {}).get("prereg")
    version = data.get("config_fingerprint") or data.get("generated_at")
    rows = []
    for axis_row in data.get("axes", []):
        axis = str(axis_row.get("axis"))
        target = _axis_task_outcome(axis)
        rows.append(
            {
                "axis": axis,
                "label": _axis_label(axis),
                "delta": axis_row.get("mean_diff"),
                "ci_lo": axis_row.get("ci_lo"),
                "ci_hi": axis_row.get("ci_hi"),
                "passed": bool(axis_row.get("passed", False)),
                "best_prompt_id": axis_row.get("dev_selection", {}).get("best_prompt_id"),
                "dev_prompt_outcome": axis_row.get("dev_selection", {}).get("dev_prompt_outcome"),
                "source": _as_rel(psr_path),
                "tier_identity": _tier_identity(
                    model=data.get("model"),
                    method=method,
                    axis=axis,
                    direction=_direction_identity(data, axis_row, method, axis),
                    layer=axis_row.get("layer"),
                    task=target["task"],
                    outcome=target["outcome"],
                    protocol=protocol,
                    version=version,
                    comparator={
                        "kind": "DEV-selected bounded prompt",
                        "best_prompt_id": axis_row.get("dev_selection", {}).get("best_prompt_id"),
                    },
                    comparator_required=True,
                    source=_as_rel(psr_path),
                ),
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
                target = _axis_task_outcome(axis)
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
                        "tier_identity": _tier_identity(
                            model=result.get("model") or cell.get("model_id"),
                            method=result.get("steering_method") or cell.get("method"),
                            axis=axis,
                            direction=_direction_identity(
                                result,
                                axis_row,
                                result.get("steering_method") or cell.get("method"),
                                axis,
                            ),
                            layer=axis_row.get("layer"),
                            task=target["task"],
                            outcome=target["outcome"],
                            protocol=result.get("prereg")
                            or result.get("frozen_params", {}).get("prereg"),
                            version=result.get("config_fingerprint")
                            or result.get("generated_at"),
                            comparator={
                                "kind": "DEV-selected bounded prompt",
                                "best_prompt_id": axis_row.get("dev_selection", {}).get(
                                    "best_prompt_id"
                                ),
                            },
                            comparator_required=True,
                            source=_as_rel(result_path),
                        ),
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
                        "tier_identity": _tier_identity(
                            model=None,
                            method=method.lower(),
                            axis="uncertainty_awareness",
                            direction=None,
                            layer=None,
                            task=_axis_task_outcome("uncertainty_awareness")["task"],
                            outcome=_axis_task_outcome("uncertainty_awareness")["outcome"],
                            protocol="evidence-ledger E-0006 fallback",
                            version="E-0006",
                            comparator=None,
                            comparator_required=True,
                            source=_as_rel(evidence_ledger_path),
                        ),
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
    c2_rows = _build_c2_rows(c2b_data, c2_source_mode)
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
                "BOUNDED PROMPT COMPARATOR",
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
