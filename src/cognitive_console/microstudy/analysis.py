"""Strict V5 analysis and DRAFT schedule-aware sensitivity simulation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import hmac
import itertools
import json
import math
import random
import statistics
import uuid
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from cognitive_console.microstudy_materials import (
    EXPORT_SCHEMA_VERSION,
    MATERIAL_SCHEMA_VERSION,
    MATERIALS_VERSION,
    SEQUENCE_SCHEMA_VERSION,
)

from .materials import (
    locale_bundle_metadata,
    material_hashes,
    planned_trials,
    validated_sources,
)
from .server import canonical_bytes

BOOTSTRAP_B = 10_000
BOOTSTRAP_SEED = 20_260_811


class ExportError(ValueError):
    def __init__(self, message: str, reason: str = "technical_corrupt"):
        super().__init__(message)
        self.reason = reason


def _check(
    condition: bool, message: str, reason: str = "technical_corrupt"
) -> None:
    if not condition:
        raise ExportError(message, reason)


def _is_bool(value: Any) -> bool:
    return type(value) is bool


def validate_export(
    data: dict[str, Any], verification_key: bytes
) -> dict[str, Any]:
    materials, sequences = validated_sources()
    _check(isinstance(data, dict), "export must be an object")
    verification = data.get("verification")
    _check(
        isinstance(verification, dict)
        and set(verification) == {"algorithm", "key_id", "signature"},
        "missing or invalid verification block",
        "signature_invalid",
    )
    _check(
        verification["algorithm"] == "HMAC-SHA256",
        "wrong signature algorithm",
        "signature_invalid",
    )
    _check(
        verification["key_id"]
        == hashlib.sha256(verification_key).hexdigest()[:16],
        "wrong verification key",
        "signature_invalid",
    )
    signature = hmac.new(
        verification_key, canonical_bytes(data), hashlib.sha256
    ).hexdigest()
    _check(
        isinstance(verification["signature"], str)
        and hmac.compare_digest(verification["signature"], signature),
        "signature mismatch",
        "signature_invalid",
    )
    _check(
        data.get("export_schema_version") == EXPORT_SCHEMA_VERSION,
        "wrong export schema",
        "export_version_mismatch",
    )
    _check(
        data.get("material_schema_version") == MATERIAL_SCHEMA_VERSION,
        "wrong V9 material schema",
        "materials_version_mismatch",
    )
    _check(
        data.get("sequence_schema_version") == SEQUENCE_SCHEMA_VERSION,
        "wrong V9 sequence schema",
        "sequence_mismatch",
    )
    _check(
        data.get("material_hashes") == material_hashes(),
        "wrong material hashes",
        "materials_version_mismatch",
    )
    ui_language = data.get("ui_language")
    _check(
        ui_language in materials["locale_contract"]["supported"],
        "missing or invalid ui_language",
        "locale_mismatch",
    )
    locale_meta = locale_bundle_metadata(ui_language)
    _check(
        data.get("locale_bundle_version") == locale_meta["locale_bundle_version"],
        "wrong locale bundle version",
        "locale_mismatch",
    )
    _check(
        data.get("locale_bundle_hash") == locale_meta["locale_bundle_hash"],
        "wrong locale bundle hash",
        "locale_mismatch",
    )
    session_fields = materials["nonlocalized"]["export_schema"]["session_fields"]
    expected_top = {
        "export_schema_version",
        "material_schema_version",
        "sequence_schema_version",
        "material_hashes",
        "verification",
        "trials",
        *session_fields,
    }
    _check(
        set(data) == expected_top,
        "unexpected or missing top-level export fields",
        "unknown_field",
    )
    for field in (
        "practice_presented", "practice_q1_submitted",
        "practice_q2_submitted", "practice_complete",
        "mechanical_exclusion", "complete",
    ):
        _check(_is_bool(data[field]), f"{field} must be boolean")
    for identifier in ("attempt_id", "run_id"):
        try:
            _check(
                uuid.UUID(data[identifier]).version == 4,
                f"{identifier} must be UUIDv4",
            )
        except (ValueError, AttributeError, TypeError):
            raise ExportError(f"{identifier} must be UUIDv4") from None
    _check(
        type(data["attempt_serial"]) is int and data["attempt_serial"] >= 1,
        "attempt_serial must be a positive integer",
    )
    _check(
        isinstance(data["participant_code"], str)
        and 1 <= len(data["participant_code"]) <= 64
        and all(
            character.isalnum() or character in "._-"
            for character in data["participant_code"]
        ),
        "invalid participant code",
    )
    _check(
        data["practice_complete"]
        == (data["practice_q1_submitted"] and data["practice_q2_submitted"]),
        "practice transition invalid",
        "impossible_state_transition",
    )
    _check(
        data["practice_presented"] and data["practice_complete"],
        "formal export requires completed practice",
        "impossible_state_transition",
    )
    _check(
        not data["practice_q2_submitted"] or data["practice_q1_submitted"],
        "practice Q2 precedes Q1",
        "impossible_state_transition",
    )
    _check(
        data["mechanical_exclusion"] is False
        and data["mechanical_exclusion_reason"] == "none",
        "client cannot set exclusions",
        "impossible_state_transition",
    )
    trials = data.get("trials")
    _check(
        isinstance(trials, list) and len(trials) == 6,
        "exactly six planned trial slots required",
        "ticket_mismatch",
    )
    try:
        plan = planned_trials(data["sequence"])
    except ValueError:
        raise ExportError("unknown sequence", "sequence_mismatch") from None
    q1_ids = set(materials["nonlocalized"]["q1_option_ids"])
    q2_ids = set(materials["nonlocalized"]["q2_option_ids"])
    trial_fields = materials["nonlocalized"]["export_schema"]["trial_fields"]
    for expected, trial in zip(plan, trials):
        _check(
            isinstance(trial, dict) and set(trial) == set(trial_fields),
            "unexpected or missing trial fields",
            "unknown_field",
        )
        for field in ("slot_index", "ticket_code", "position"):
            _check(
                trial[field] == expected[field],
                f"sequence mismatch at {field}",
                "ticket_mismatch" if field == "ticket_code" else "sequence_mismatch",
            )
        for field in (
            "planned", "presented", "q1_submitted", "q2_submitted",
            "complete", "submitted", "q1_missing", "q2_missing",
            "q1_correct_missing", "q2_correct_missing", "cca_correct_missing",
            "rt_q1_missing", "rt_q2_missing", "rt_total_missing",
            "hidden_ms_missing",
        ):
            _check(_is_bool(trial[field]), f"{field} must be boolean")
        for field in ("q1_correct", "q2_correct", "cca_correct"):
            _check(
                trial[field] is None or _is_bool(trial[field]),
                f"{field} must be boolean or null",
            )
        _check(trial["planned"] is True, "planned must be true")
        _check(
            trial["q2_submitted"] <= trial["q1_submitted"] <= trial["presented"],
            "impossible submit transition: submitted responses require a presented trial",
            "impossible_state_transition",
        )
        _check(
            trial["complete"] == (
                trial["q1_submitted"] and trial["q2_submitted"]
            ),
            "complete invariant failed",
            "impossible_state_transition",
        )
        _check(
            trial["submitted"] == trial["complete"],
            "submitted invariant failed",
            "impossible_state_transition",
        )
        if trial["q1_submitted"]:
            _check(trial["q1"] in q1_ids, "invalid Q1 response")
            _check(
                trial["q1_correct"] == (trial["q1"] == expected["q1_key"]),
                "wrong Q1 scoring",
            )
        else:
            _check(
                trial["q1"] is None and trial["q1_correct"] is None,
                "unsubmitted Q1 populated",
                "impossible_state_transition",
            )
        if trial["q2_submitted"]:
            _check(trial["q2"] in q2_ids, "invalid Q2 response")
            _check(
                trial["q2_correct"] == (trial["q2"] == expected["q2_key"]),
                "wrong Q2 scoring",
            )
            _check(
                trial["cca_correct"]
                == (trial["q1_correct"] and trial["q2_correct"]),
                "wrong CCA scoring",
            )
        else:
            _check(
                trial["q2"] is None and trial["q2_correct"] is None,
                "unsubmitted Q2 populated",
                "impossible_state_transition",
            )
        for field in ("rt_q1_ms", "rt_q2_ms", "rt_total_ms", "hidden_ms"):
            value = trial[field]
            _check(
                value is None or (type(value) is int and value >= 0),
                f"invalid {field}",
            )
        for value_field, missing_field in (
            ("q1", "q1_missing"),
            ("q2", "q2_missing"),
            ("q1_correct", "q1_correct_missing"),
            ("q2_correct", "q2_correct_missing"),
            ("cca_correct", "cca_correct_missing"),
            ("rt_q1_ms", "rt_q1_missing"),
            ("rt_q2_ms", "rt_q2_missing"),
            ("rt_total_ms", "rt_total_missing"),
            ("hidden_ms", "hidden_ms_missing"),
        ):
            _check(
                trial[missing_field] == (trial[value_field] is None),
                f"missing flag mismatch for {value_field}",
            )
        if trial["complete"]:
            _check(
                trial["rt_total_ms"] == trial["rt_q1_ms"] + trial["rt_q2_ms"],
                "RT total mismatch",
            )
        _check(
            trial["materials_version"] == MATERIALS_VERSION,
            "materials version mismatch",
            "materials_version_mismatch",
        )
    completed = sum(row["complete"] for row in trials)
    presented = sum(row["presented"] for row in trials)
    _check(
        [row["presented"] for row in trials]
        == [True] * presented + [False] * (6 - presented),
        "presented trials must form a prefix",
        "impossible_state_transition",
    )
    _check(
        [row["complete"] for row in trials]
        == [True] * completed + [False] * (6 - completed),
        "complete trials must form a prefix",
        "impossible_state_transition",
    )
    _check(
        presented in {completed, completed + 1},
        "at most one presented trial may be incomplete",
        "impossible_state_transition",
    )
    if data["complete"]:
        _check(
            completed == 6,
            "signed complete export must contain six complete trials",
            "impossible_state_transition",
        )
        _check(data["completion_status"] == "complete", "completion status mismatch")
    else:
        _check(
            presented >= 1,
            "partial export requires a formal ticket presentation",
            "impossible_state_transition",
        )
        _check(data["completion_status"] == "partial", "completion status mismatch")
    return data


def _complete_count(data: dict[str, Any]) -> int:
    return sum(bool(row["complete"]) for row in data["trials"])


def load_exports(
    paths: Iterable[Path],
    verification_key: bytes,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    valid: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    attempts: dict[str, tuple[bytes, str, str]] = {}
    observed_export_schemas: set[str] = set()
    observed_material_schemas: set[str] = set()
    raw_rows: list[tuple[Path, Any]] = []
    for path in paths:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            raw_rows.append((path, raw))
            if isinstance(raw, dict):
                if isinstance(raw.get("export_schema_version"), str):
                    observed_export_schemas.add(raw["export_schema_version"])
                if isinstance(raw.get("material_schema_version"), str):
                    observed_material_schemas.add(raw["material_schema_version"])
        except (OSError, json.JSONDecodeError) as exc:
            rejected.append(
                {
                    "source_file": str(path),
                    "reason": "technical_corrupt",
                    "detail": str(exc),
                }
            )
    if observed_export_schemas - {EXPORT_SCHEMA_VERSION}:
        raise ExportError(
            "V4/V5 or unsupported export schemas must not be mixed",
            "export_version_mismatch",
        )
    if observed_material_schemas - {MATERIAL_SCHEMA_VERSION}:
        raise ExportError(
            "V8/V9 or unsupported material schemas must not be mixed",
            "materials_version_mismatch",
        )
    for path, raw in raw_rows:
        try:
            if isinstance(raw, dict):
                attempt_id = raw.get("attempt_id")
                verification = raw.get("verification")
                signature = (
                    verification.get("signature")
                    if isinstance(verification, dict)
                    else None
                )
                if isinstance(attempt_id, str) and isinstance(signature, str):
                    fingerprint = (canonical_bytes(raw), signature, str(path))
                    previous = attempts.get(attempt_id)
                    if previous is not None:
                        if previous[:2] != fingerprint[:2]:
                            raise ExportError(
                                "same attempt_id has conflicting payload or signature: "
                                f"{previous[2]} vs {path}",
                                "attempt_id_conflict",
                            )
                        continue
                    attempts[attempt_id] = fingerprint
            data = validate_export(raw, verification_key)
            data["_source_file"] = str(path)
            valid.append(data)
        except ExportError as exc:
            if exc.reason == "attempt_id_conflict":
                raise
            rejected.append(
                {
                    "source_file": str(path),
                    "reason": exc.reason,
                    "detail": str(exc),
                }
            )
        except (KeyError, TypeError) as exc:
            rejected.append(
                {
                    "source_file": str(path),
                    "reason": "technical_corrupt",
                    "detail": str(exc),
                }
            )
    return valid, rejected


def load_attempt_order_manifest(path: Path) -> dict[str, int]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    _check(
        isinstance(raw, dict)
        and set(raw) == {"schema_version", "attempt_order"}
        and raw["schema_version"] == "microstudy-attempt-order-v1"
        and isinstance(raw["attempt_order"], dict),
        "invalid attempt-order manifest",
        "attempt_order_manifest",
    )
    mapping: dict[str, int] = {}
    for attempt_id, order in raw["attempt_order"].items():
        _check(
            isinstance(attempt_id, str)
            and type(order) is int
            and order >= 1,
            "invalid attempt-order row",
            "attempt_order_manifest",
        )
        try:
            _check(
                uuid.UUID(attempt_id).version == 4,
                "attempt-order attempt_id must be UUIDv4",
                "attempt_order_manifest",
            )
        except (ValueError, AttributeError, TypeError):
            raise ExportError(
                "attempt-order attempt_id must be UUIDv4",
                "attempt_order_manifest",
            ) from None
        mapping[attempt_id] = order
    _check(
        len(set(mapping.values())) == len(mapping),
        "attempt global orders must be unique",
        "attempt_order_manifest",
    )
    return mapping


def resolve_duplicates(
    exports: list[dict[str, Any]],
    attempt_order: dict[str, int] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for data in exports:
        groups[data["participant_code"]].append(data)
    kept: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for participant, attempts in groups.items():
        run_ids = {row["run_id"] for row in attempts}
        if len(run_ids) > 1:
            if attempt_order is None:
                raise ExportError(
                    "participant appears across run_ids; attempt-order manifest required",
                    "duplicate_order_ambiguous",
                )
            missing = {
                row["attempt_id"] for row in attempts
            } - set(attempt_order)
            _check(
                not missing,
                f"attempt-order manifest missing attempt_ids: {sorted(missing)}",
                "attempt_order_manifest",
            )
            order_key = lambda row: (attempt_order[row["attempt_id"]],)
        else:
            serials = [row["attempt_serial"] for row in attempts]
            _check(
                len(serials) == len(set(serials)),
                "duplicate attempt_serial within run",
                "duplicate_order_ambiguous",
            )
            order_key = lambda row: (0, row["attempt_serial"])
        complete = [row for row in attempts if _complete_count(row) == 6]
        if complete:
            winner = min(complete, key=order_key)
        else:
            winner = min(
                attempts,
                key=lambda row: (-_complete_count(row), *order_key(row)),
            )
        kept.append(winner)
        for row in attempts:
            if row is winner:
                continue
            excluded.append(
                {
                    "attempt_id": row["attempt_id"],
                    "participant_code": participant,
                    "reason": "duplicate_attempt",
                    "ui_language": row["ui_language"],
                    "kept_ui_language": winner["ui_language"],
                    "locale_conflict": row["ui_language"] != winner["ui_language"],
                    "complete_trials": _complete_count(row),
                }
            )
    return kept, excluded


def load_assignments(path: Path) -> dict[str, str]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    _check(
        isinstance(raw, dict)
        and set(raw) == {"schema_version", "assignments"}
        and raw["schema_version"] == "microstudy-owner-assignment-v2"
        and isinstance(raw["assignments"], list),
        "invalid assignment manifest",
        "assignment_invalid",
    )
    valid_sequences = {
        row["code"] for row in validated_sources()[1]["sequences"]
    }
    assignments: dict[str, str] = {}
    for row in raw["assignments"]:
        _check(
            isinstance(row, dict)
            and set(row) == {"participant_code", "sequence"}
            and isinstance(row["participant_code"], str)
            and isinstance(row["sequence"], str),
            "invalid assignment row",
            "assignment_invalid",
        )
        _check(
            row["participant_code"] not in assignments,
            "duplicate participant assignment",
            "assignment_invalid",
        )
        _check(
            row["sequence"] in valid_sequences,
            "unknown assigned sequence",
            "assignment_invalid",
        )
        assignments[row["participant_code"]] = row["sequence"]
    return assignments


def apply_assignments(
    exports: list[dict[str, Any]],
    assignments: dict[str, str] | None,
) -> list[dict[str, Any]]:
    if assignments is None:
        return []
    missing = {row["participant_code"] for row in exports} - set(assignments)
    _check(
        not missing,
        f"assignment manifest missing participants: {sorted(missing)}",
        "assignment_invalid",
    )
    return [
        {
            "attempt_id": row["attempt_id"],
            "participant_code": row["participant_code"],
            "reason": "assignment_mismatch",
        }
        for row in exports
        if assignments[row["participant_code"]] != row["sequence"]
    ]


def exact_sign_flip(
    differences: list[float], *, two_sided: bool = False
) -> dict[str, Any]:
    nonzero = [value for value in differences if value != 0]
    ties = len(differences) - len(nonzero)
    if not nonzero:
        return {"n_eff": 0, "ties": ties, "p": 1.0}
    observed = sum(nonzero) / len(nonzero)
    permutations = [
        sum(sign * value for sign, value in zip(signs, nonzero)) / len(nonzero)
        for signs in itertools.product((-1, 1), repeat=len(nonzero))
    ]
    if two_sided:
        count = sum(abs(value) >= abs(observed) for value in permutations)
    else:
        count = sum(value >= observed for value in permutations)
    return {"n_eff": len(nonzero), "ties": ties, "p": count / len(permutations)}


def bootstrap_ci(differences: list[float]) -> list[float | None]:
    if not differences:
        return [None, None]
    rng = random.Random(BOOTSTRAP_SEED)
    n = len(differences)
    samples = sorted(
        sum(rng.choice(differences) for _ in range(n)) / n
        for _ in range(BOOTSTRAP_B)
    )
    return [
        samples[math.floor(0.025 * BOOTSTRAP_B)],
        samples[math.ceil(0.975 * BOOTSTRAP_B) - 1],
    ]


def _mean(values: list[float | int]) -> float | None:
    return statistics.fmean(values) if values else None


def _condition_rows(data: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    plan = planned_trials(data["sequence"])
    condition_by_slot = {
        row["slot_index"]: row["condition"] for row in plan
    }
    return {
        condition: [
            trial
            for trial in data["trials"]
            if condition_by_slot[trial["slot_index"]] == condition
        ]
        for condition in ("C", "F")
    }


def analyze(
    exports: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
    *,
    attempt_order: dict[str, int] | None = None,
    assignments: dict[str, str] | None = None,
) -> dict[str, Any]:
    all_valid = list(exports)
    kept, duplicate_exclusions = resolve_duplicates(exports, attempt_order)
    assignment_exclusions = apply_assignments(kept, assignments)
    mechanical_ids = {
        row["attempt_id"] for row in assignment_exclusions
    }
    participants: list[dict[str, Any]] = []
    primary_differences: list[float] = []
    available_differences: list[float] = []
    missing_differences: list[float] = []
    descriptive = {
        condition: defaultdict(list) for condition in ("C", "F")
    }
    for data in kept:
        rows_by_condition = _condition_rows(data)
        complete_counts = {
            condition: sum(row["complete"] for row in rows)
            for condition, rows in rows_by_condition.items()
        }
        total_complete = sum(complete_counts.values())
        mechanical = data["attempt_id"] in mechanical_ids
        primary_eligible = total_complete == 6 and not mechanical
        available_eligible = (
            complete_counts["C"] >= 2
            and complete_counts["F"] >= 2
            and total_complete >= 4
            and not mechanical
        )
        scores: dict[str, float | None] = {}
        missing_scores: dict[str, float] = {}
        for condition, rows in rows_by_condition.items():
            completed = [row for row in rows if row["complete"]]
            scores[condition] = _mean(
                [int(row["cca_correct"]) for row in completed]
            )
            missing_scores[condition] = statistics.fmean(
                int(bool(row["complete"]) and bool(row["cca_correct"]))
                for row in rows
            )
            for row in completed:
                descriptive[condition]["q1_accuracy"].append(
                    int(row["q1_correct"])
                )
                descriptive[condition]["q2_accuracy"].append(
                    int(row["q2_correct"])
                )
                descriptive[condition]["cca_accuracy"].append(
                    int(row["cca_correct"])
                )
                descriptive[condition]["rt_q1_ms"].append(row["rt_q1_ms"])
                descriptive[condition]["rt_q2_ms"].append(row["rt_q2_ms"])
        paired = (
            scores["C"] - scores["F"]
            if scores["C"] is not None and scores["F"] is not None
            else None
        )
        if primary_eligible and paired is not None:
            primary_differences.append(paired)
        if available_eligible and paired is not None:
            available_differences.append(paired)
        missing_difference = missing_scores["C"] - missing_scores["F"]
        missing_differences.append(missing_difference)
        participants.append(
            {
                "attempt_id": data["attempt_id"],
                "participant_code": data["participant_code"],
                "sequence": data["sequence"],
                "ui_language": data["ui_language"],
                "complete_c": complete_counts["C"],
                "complete_f": complete_counts["F"],
                "complete_total": total_complete,
                "eligible_primary": primary_eligible,
                "eligible_available": available_eligible,
                "mechanical_exclusion": mechanical,
                "mechanical_exclusion_reason": (
                    "assignment_mismatch" if mechanical else "none"
                ),
                "c_cca": scores["C"],
                "f_cca": scores["F"],
                "paired_difference": paired,
                "missing_incorrect_difference": missing_difference,
            }
        )
    all_rejections = rejected + duplicate_exclusions + assignment_exclusions
    consumed = [
        {
            "attempt_id": row["attempt_id"],
            "participant_code": row["participant_code"],
            "sequence": row["sequence"],
            "mechanically_excluded": row["attempt_id"] in mechanical_ids,
            "duplicate_excluded": any(
                exclusion["attempt_id"] == row["attempt_id"]
                for exclusion in duplicate_exclusions
            ),
        }
        for row in all_valid
        if _complete_count(row) == 6
    ]
    return {
        "analysis_version": "microstudy-analysis-v3-scenario-v5-only",
        "status": "DRAFT_ANALYSIS_NOT_PAPER_EVIDENCE",
        "mde_status": "UNVERIFIED_NOT_ESTIMATED",
        "bootstrap": {"B": BOOTSTRAP_B, "seed": BOOTSTRAP_SEED},
        "input_attempts": len(all_valid) + len(rejected),
        "kept_attempts": len(kept),
        "eligible_primary_n": len(primary_differences),
        "eligible_available_n": len(available_differences),
        "rejected": all_rejections,
        "sequence_slot_consumption": {
            "rule": (
                "valid six-complete exports consume; partial/fewer-than-six "
                "reuse; mechanically excluded complete exports consume"
            ),
            "consumed": consumed,
        },
        "participants": participants,
        "primary": {
            "estimand": "mean participant paired C-minus-F CCA among all-six complete",
            "mean_difference": _mean(primary_differences),
            "bootstrap_percentile_95_ci": bootstrap_ci(primary_differences),
            "exact_one_sided_sign_flip": exact_sign_flip(primary_differences),
        },
        "available_case_sensitivity": {
            "eligibility": "at least two complete per condition and four total",
            "mean_difference": _mean(available_differences),
            "exact_two_sided_sign_flip": exact_sign_flip(
                available_differences, two_sided=True
            ),
        },
        "missing_as_incorrect_sensitivity": {
            "estimand": "C-minus-F CCA over all six planned slots",
            "mean_difference": _mean(missing_differences),
            "exact_two_sided_sign_flip": exact_sign_flip(
                missing_differences, two_sided=True
            ),
        },
        "descriptive": {
            condition: {
                metric: _mean(values) for metric, values in metrics.items()
            }
            for condition, metrics in descriptive.items()
        },
        "descriptive_locale_qa": {
            "kept_counts": dict(
                Counter(row["ui_language"] for row in kept)
            ),
            "duplicate_locale_conflict_count": sum(
                row.get("locale_conflict") is True for row in all_rejections
            ),
            "duplicate_locale_conflicts": [
                {
                    "participant_code": row["participant_code"],
                    "excluded_ui_language": row["ui_language"],
                    "kept_ui_language": row["kept_ui_language"],
                }
                for row in all_rejections
                if row.get("locale_conflict") is True
            ],
            "analysis_role": (
                "descriptive QA only; locale, source badge, ticket state, "
                "performance, and response time do not affect duplicate "
                "winner selection, assignment, exclusion, or eligibility"
            ),
        },
    }


def write_summary(
    summary: dict[str, Any], json_path: Path, csv_path: Path
) -> None:
    json_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    fields = [
        "attempt_id", "participant_code", "sequence", "ui_language",
        "eligible_primary", "eligible_available", "mechanical_exclusion",
        "mechanical_exclusion_reason", "complete_c", "complete_f",
        "complete_total", "c_cca", "f_cca", "paired_difference",
        "missing_incorrect_difference",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(summary["participants"])


def simulate_schedule_aware_mde(
    n: int, simulations: int, seed: int
) -> dict[str, Any]:
    if n < 2 or simulations < 100:
        raise ValueError("simulation requires n>=2 and simulations>=100")
    rng = random.Random(seed)
    grid = [round(value / 100, 2) for value in range(1, 41)]
    power: dict[str, float] = {}
    for effect in grid:
        rejected = 0
        for _ in range(simulations):
            differences = []
            for participant_index in range(n):
                sequence = planned_trials(f"V9-{participant_index % 12 + 1:02d}")
                participant_shift = rng.gauss(0, 0.16)
                condition_scores = {"C": [], "F": []}
                for slot in sequence:
                    ticket_shift = rng.gauss(0, 0.10)
                    probability = max(
                        0.02,
                        min(
                            0.98,
                            0.58
                            + participant_shift
                            + ticket_shift
                            + (effect if slot["condition"] == "C" else 0),
                        ),
                    )
                    condition_scores[slot["condition"]].append(
                        int(rng.random() < probability)
                    )
                differences.append(
                    statistics.fmean(condition_scores["C"])
                    - statistics.fmean(condition_scores["F"])
                )
            if exact_sign_flip(differences)["p"] <= 0.05:
                rejected += 1
        power[str(effect)] = rejected / simulations
    mde = next(
        (float(effect) for effect, value in power.items() if value >= 0.8),
        None,
    )
    return {
        "status": "DRAFT_SCHEDULE_AWARE_SIMULATION_NOT_RECRUITMENT_BASIS",
        "primary_mde_status": "UNVERIFIED_NOT_ESTIMATED",
        "assumptions": {
            "n": n,
            "simulations": simulations,
            "seed": seed,
            "schedule": SEQUENCE_SCHEMA_VERSION,
            "participant_random_sd": 0.16,
            "ticket_random_sd": 0.10,
            "baseline_probability": 0.58,
            "test": "exact one-sided sign flip",
            "warning": (
                "DRAFT assumption sensitivity only; owner timing, human variance, "
                "dropout, and Protocol Freeze are pending"
            ),
        },
        "estimated_effect_for_80_percent_simulated_power": mde,
        "power_by_effect": power,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("exports", nargs="+", type=Path)
    analyze_parser.add_argument(
        "--json-out", type=Path, default=Path("microstudy-v9-summary.json")
    )
    analyze_parser.add_argument(
        "--csv-out", type=Path, default=Path("microstudy-v9-participants.csv")
    )
    analyze_parser.add_argument("--assignments", type=Path)
    analyze_parser.add_argument("--attempt-order-manifest", type=Path)
    analyze_parser.add_argument(
        "--verification-key-file", type=Path, required=True
    )
    mde_parser = subparsers.add_parser("mde")
    mde_parser.add_argument("--n", type=int, required=True)
    mde_parser.add_argument("--simulations", type=int, default=10_000)
    mde_parser.add_argument("--seed", type=int, default=BOOTSTRAP_SEED)
    mde_parser.add_argument(
        "--json-out", type=Path, default=Path("microstudy-v9-mde-DRAFT.json")
    )
    args = parser.parse_args(argv)
    if args.command == "analyze":
        key = args.verification_key_file.read_bytes()
        valid, rejected = load_exports(args.exports, key)
        attempt_order = (
            load_attempt_order_manifest(args.attempt_order_manifest)
            if args.attempt_order_manifest
            else None
        )
        assignments = (
            load_assignments(args.assignments) if args.assignments else None
        )
        summary = analyze(
            valid,
            rejected,
            attempt_order=attempt_order,
            assignments=assignments,
        )
        write_summary(summary, args.json_out, args.csv_out)
    else:
        args.json_out.write_text(
            json.dumps(
                simulate_schedule_aware_mde(
                    args.n, args.simulations, args.seed
                ),
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
