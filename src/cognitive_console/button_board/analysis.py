"""Fail-closed validation and descriptive analysis for signed V10 exports."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from cognitive_console.button_board_materials import (
    ANALYSIS_VERSION,
    EXPORT_SCHEMA_VERSION,
    FORMAL_SCENES,
    MATERIAL_SCHEMA_VERSION,
    MATERIALS_VERSION,
    Q1_STATES,
    SEQUENCE_SCHEMA_VERSION,
)
from cognitive_console.microstudy.server import canonical_bytes

from .materials import material_hashes, planned_trials, validated_sources


class ExportError(ValueError):
    """Raised when an export cannot be trusted or belongs to another study."""


SESSION_FIELDS = {
    "schema_version",
    "export_schema_version",
    "sequence_schema_version",
    "materials_version",
    "analysis_version",
    "canonical_materials_hash",
    "sequences_hash",
    "derived_keys_hash",
    "ab_invariance_hash",
    "attempt_id",
    "run_id",
    "attempt_serial",
    "participant_code",
    "selected_locale",
    "locale_bundle_version",
    "locale_bundle_hash",
    "sequence_id",
    "ab_variant",
    "allocation_block",
    "allocation_cell",
    "completion_status",
    "complete",
    "practice_status",
    "attention_check",
    "reflection",
    "trials",
    "verification",
}
TRIAL_FIELDS = {
    "slot_index",
    "scene_id",
    "position",
    "planned",
    "presented",
    "q1_selected",
    "q1_correct",
    "q1_locked_at",
    "scope_selected",
    "scope_choice_correct",
    "scope_gate_required",
    "reason_selected",
    "reason_choice_correct",
    "reason_correct",
    "gaa_trial",
    "strict_gaa_trial",
    "q1_submitted",
    "scope_submitted",
    "reason_submitted",
    "complete",
    "presented_q1_order",
    "presented_scope_order",
    "presented_reason_order",
    "relative_rt_q1",
    "relative_rt_scope",
    "relative_rt_reason",
    "materials_version",
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ExportError(message)


def _is_nonnegative_int_or_none(value: Any) -> bool:
    return value is None or (type(value) is int and value >= 0)


def _assert_no_expected_keys(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            if (
                "expected" in lowered
                or "correct_reason_id" in lowered
                or "correct_scope_id" in lowered
                or lowered in {"paper_state", "reason_class"}
            ):
                raise ExportError(f"private expected key in export at {path}.{key}")
            _assert_no_expected_keys(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_no_expected_keys(item, f"{path}[{index}]")


def validate_export(data: dict[str, Any], key: bytes) -> dict[str, Any]:
    _require(isinstance(data, dict), "export must be an object")
    _require(set(data) == SESSION_FIELDS, "unexpected or missing session fields")
    _assert_no_expected_keys(data)
    _require(
        data["schema_version"] == MATERIAL_SCHEMA_VERSION,
        "wrong material schema; V9/V10 mixing is forbidden",
    )
    _require(
        data["export_schema_version"] == EXPORT_SCHEMA_VERSION,
        "wrong export schema; V5/V6 mixing is forbidden",
    )
    _require(
        data["sequence_schema_version"] == SEQUENCE_SCHEMA_VERSION,
        "wrong sequence schema",
    )
    _require(data["materials_version"] == MATERIALS_VERSION, "wrong materials version")
    _require(data["analysis_version"] == ANALYSIS_VERSION, "wrong analysis version")
    expected_hashes = material_hashes()
    for field, expected in expected_hashes.items():
        _require(data[field] == expected, f"{field} mismatch")
    _, _, derived = validated_sources()
    _require(
        data["ab_invariance_hash"] == derived["ab_invariance_hash"],
        "A/B invariance hash mismatch",
    )
    verification = data["verification"]
    _require(
        isinstance(verification, dict)
        and set(verification) == {"algorithm", "key_id", "signature"},
        "invalid verification object",
    )
    _require(verification["algorithm"] == "HMAC-SHA256", "invalid signature algorithm")
    _require(
        verification["key_id"] == hashlib.sha256(key).hexdigest()[:16],
        "wrong verification key",
    )
    expected_signature = hmac.new(
        key, canonical_bytes(data), hashlib.sha256
    ).hexdigest()
    _require(
        hmac.compare_digest(verification["signature"], expected_signature),
        "invalid export signature",
    )
    _require(
        data["selected_locale"] in {"en", "zh-Hans"},
        "invalid selected locale",
    )
    materials, _, _ = validated_sources()
    from .materials import locale_bundle_metadata

    locale_meta = locale_bundle_metadata(data["selected_locale"])
    _require(
        data["locale_bundle_version"] == locale_meta["locale_bundle_version"]
        and data["locale_bundle_hash"] == locale_meta["locale_bundle_hash"],
        "locale identity mismatch",
    )
    _require(
        data["ab_variant"] in {"F1", "F2"},
        "invalid A/B variant",
    )
    _require(
        type(data["attempt_serial"]) is int and data["attempt_serial"] >= 1,
        "invalid attempt serial",
    )
    _require(
        type(data["allocation_block"]) is int and data["allocation_block"] >= 0,
        "invalid allocation block",
    )
    _require(
        type(data["allocation_cell"]) is int
        and 0 <= data["allocation_cell"] < 24,
        "invalid allocation cell",
    )
    expected_sequence = f"BB10-{data['allocation_cell'] // 2 + 1:02d}"
    expected_variant = "F1" if data["allocation_cell"] % 2 == 0 else "F2"
    _require(data["sequence_id"] == expected_sequence, "allocation sequence mismatch")
    _require(data["ab_variant"] == expected_variant, "allocation variant mismatch")
    _require(
        data["complete"] is (data["completion_status"] == "complete"),
        "completion status mismatch",
    )
    plan = planned_trials(
        data["sequence_id"], data["ab_variant"], data["participant_code"]
    )
    trials = data["trials"]
    _require(isinstance(trials, list) and len(trials) == 6, "six trials required")
    for trial, slot in zip(trials, plan):
        _require(
            isinstance(trial, dict) and set(trial) == TRIAL_FIELDS,
            "unexpected or missing trial fields",
        )
        _require(
            trial["slot_index"] == slot["slot_index"]
            and trial["scene_id"] == slot["scene_id"]
            and trial["position"] == slot["position"],
            "trial identity mismatch",
        )
        _require(trial["planned"] is True, "every exported slot must be planned")
        _require(
            trial["materials_version"] == MATERIALS_VERSION,
            "trial materials version mismatch",
        )
        _require(
            trial["presented_q1_order"] == slot["q1_order"],
            "Q1 presentation order mismatch",
        )
        _require(
            set(trial["presented_q1_order"])
            == {"board-use", "board-info", "board-off", "board-check"},
            "invalid Q1 presentation order",
        )
        _require(
            trial["reason_submitted"] <= trial["scope_submitted"]
            <= trial["q1_submitted"],
            "invalid submission ordering",
        )
        _require(
            trial["complete"] is trial["reason_submitted"],
            "trial completion mismatch",
        )
        _require(
            trial["presented"] or not trial["q1_submitted"],
            "unpresented trial contains an answer",
        )
        for field in (
            "q1_locked_at",
            "relative_rt_q1",
            "relative_rt_scope",
            "relative_rt_reason",
        ):
            _require(_is_nonnegative_int_or_none(trial[field]), f"invalid {field}")
        if trial["q1_submitted"]:
            _require(trial["q1_selected"] in Q1_STATES, "invalid Q1 selection")
            q1_correct = trial["q1_selected"] == slot["q1_state"]
            _require(
                trial["q1_correct"] is q1_correct
                and trial["gaa_trial"] is q1_correct,
                "Q1 score does not match derived router key",
            )
        else:
            _require(
                trial["q1_selected"] is None
                and trial["q1_correct"] is None
                and trial["gaa_trial"] is None,
                "missing Q1 has populated score",
            )
        if trial["scope_submitted"]:
            _require(
                trial["presented_scope_order"] == slot["scope_order_ids"],
                "scope presentation order mismatch",
            )
            _require(
                set(trial["presented_scope_order"]) == set(slot["scope_order_ids"]),
                "invalid scope order",
            )
            _require(
                trial["scope_selected"] in slot["scope_order_ids"],
                "invalid scope selection",
            )
            scope_correct = trial["scope_selected"] == slot["correct_scope_id"]
            _require(
                trial["scope_choice_correct"] is scope_correct,
                "scope score does not match derived key",
            )
        else:
            _require(
                trial["scope_selected"] is None
                and trial["scope_choice_correct"] is None,
                "missing scope has populated fields",
            )
            _require(
                trial["presented_scope_order"] in ([], slot["scope_order_ids"]),
                "invalid unsubmitted scope order",
            )
        _require(
            trial["scope_gate_required"] is slot["scope_gate_required"],
            "scope gate mismatch",
        )
        if trial["reason_submitted"]:
            _require(
                trial["presented_reason_order"] == slot["reason_order_ids"],
                "reason presentation order mismatch",
            )
            _require(
                trial["reason_selected"] in slot["reason_order_ids"],
                "invalid reason selection",
            )
            reason_choice_correct = (
                trial["reason_selected"] == slot["correct_reason_id"]
            )
            reason_correct = reason_choice_correct and (
                bool(trial["scope_choice_correct"])
                if slot["scope_gate_required"]
                else True
            )
            strict = bool(trial["q1_correct"]) and reason_correct
            _require(
                trial["reason_choice_correct"] is reason_choice_correct,
                "reason-choice score mismatch",
            )
            _require(trial["reason_correct"] is reason_correct, "reason score mismatch")
            _require(
                trial["strict_gaa_trial"] is strict,
                "Strict GAA score mismatch",
            )
        else:
            _require(
                trial["reason_selected"] is None
                and trial["reason_choice_correct"] is None
                and trial["reason_correct"] is None
                and trial["strict_gaa_trial"] is None,
                "missing reason has populated fields",
            )
            _require(
                trial["presented_reason_order"] in ([], slot["reason_order_ids"]),
                "invalid unsubmitted reason order",
            )
    expected_scene_ids = {
        data["ab_variant"], "F3", "F4", "F5", "F6", "F7"
    }
    _require(
        {trial["scene_id"] for trial in trials} == expected_scene_ids,
        "F1/F2 coexistence or formal scene mismatch",
    )
    _require(
        not ({"F1", "F2"} <= {trial["scene_id"] for trial in trials}),
        "one participant cannot receive both A/B variants",
    )
    if data["complete"]:
        _require(all(trial["complete"] for trial in trials), "complete export has gaps")
        _require(data["attention_check"]["pass"] in {True, False}, "attention missing")
        _require(
            all(value is not None for value in data["reflection"].values()),
            "complete export has missing reflection response",
        )
    _require(
        set(data["practice_status"])
        == {"q1_selected", "scope_selected", "reason_selected", "complete"},
        "invalid practice status",
    )
    _require(
        set(data["attention_check"])
        == {"q1_selected", "reason_selected", "pass"},
        "invalid attention status",
    )
    _require(
        set(data["reflection"]) == {"helpful", "confusing", "amount"},
        "invalid reflection",
    )
    return data


def load_exports(paths: Iterable[Path], key: bytes) -> list[dict[str, Any]]:
    exports = [
        validate_export(json.loads(path.read_text(encoding="utf-8")), key)
        for path in paths
    ]
    _require(bool(exports), "at least one export is required")
    versions = {
        (
            row["schema_version"],
            row["export_schema_version"],
            row["materials_version"],
            row["analysis_version"],
        )
        for row in exports
    }
    _require(len(versions) == 1, "mixed export versions are forbidden")
    identities = [(row["run_id"], row["attempt_id"]) for row in exports]
    _require(len(identities) == len(set(identities)), "duplicate export file")
    participant_codes = [row["participant_code"] for row in exports]
    _require(
        len(participant_codes) == len(set(participant_codes)),
        "duplicate participant code requires owner adjudication",
    )
    return exports


def _mean(values: list[int | float]) -> float | None:
    return sum(values) / len(values) if values else None


def v9_compat_trial(trial: dict[str, Any]) -> dict[str, bool | None]:
    """Expose the documented score aliases without reusing the V9 schema."""
    return {
        "q1_correct": trial["gaa_trial"],
        "q2_correct": trial["reason_correct"],
        "cca_correct": trial["strict_gaa_trial"],
    }


def analyze(exports: list[dict[str, Any]]) -> dict[str, Any]:
    complete = [row for row in exports if row["complete"]]
    primary = [row for row in complete if row["attention_check"]["pass"] is True]
    sensitivity = complete

    def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
        gaa_counts = [
            sum(bool(trial["gaa_trial"]) for trial in row["trials"]) for row in rows
        ]
        strict_counts = [
            sum(bool(trial["strict_gaa_trial"]) for trial in row["trials"])
            for row in rows
        ]
        confusion: Counter[tuple[str, str]] = Counter()
        reason_accuracy: defaultdict[str, list[int]] = defaultdict(list)
        scope_accuracy: defaultdict[str, list[int]] = defaultdict(list)
        scope_error_types: Counter[str] = Counter()
        ab_accuracy: defaultdict[str, list[int]] = defaultdict(list)
        ab_selected: defaultdict[str, Counter[str]] = defaultdict(Counter)
        state_reason_cells: Counter[str] = Counter()
        rt_q1: list[int] = []
        rt_scope: list[int] = []
        rt_reason: list[int] = []
        _, _, keys = validated_sources()
        source_scenes = {scene["scene_id"]: scene for scene in FORMAL_SCENES}
        for row in rows:
            for trial in row["trials"]:
                expected = keys["scenes"][trial["scene_id"]]
                confusion[expected["q1_state"], trial["q1_selected"]] += 1
                reason_accuracy[expected["reason_class"]].append(
                    int(bool(trial["reason_choice_correct"]))
                )
                cell = (
                    "state_correct_reason_correct"
                    if trial["q1_correct"] and trial["reason_correct"]
                    else "state_correct_reason_wrong"
                    if trial["q1_correct"]
                    else "state_wrong_reason_correct"
                    if trial["reason_correct"]
                    else "state_wrong_reason_wrong"
                )
                state_reason_cells[cell] += 1
                if trial["scene_id"] in {"F1", "F6", "F7"}:
                    scope_accuracy[trial["scene_id"]].append(
                        int(bool(trial["scope_choice_correct"]))
                    )
                if not trial["scope_choice_correct"]:
                    selected = next(
                        option
                        for option in source_scenes[trial["scene_id"]]["scope_options"]
                        if option["id"] == trial["scope_selected"]
                    )
                    scope_error_types[selected["tag"]] += 1
                if trial["scene_id"] in {"F1", "F2"}:
                    ab_accuracy[row["ab_variant"]].append(
                        int(bool(trial["q1_correct"]))
                    )
                    ab_selected[row["ab_variant"]][trial["q1_selected"]] += 1
                rt_q1.append(trial["relative_rt_q1"])
                rt_scope.append(trial["relative_rt_scope"])
                rt_reason.append(trial["relative_rt_reason"])
        total_trials = sum(state_reason_cells.values())
        return {
            "n": len(rows),
            "mean_gaa_count": _mean(gaa_counts),
            "mean_gaa_rate": (
                _mean([value / 6 for value in gaa_counts]) if gaa_counts else None
            ),
            "mean_strict_gaa_count": _mean(strict_counts),
            "mean_strict_gaa_rate": (
                _mean([value / 6 for value in strict_counts])
                if strict_counts
                else None
            ),
            "q1_confusion": [
                {"expected": expected, "selected": selected, "count": count}
                for (expected, selected), count in sorted(confusion.items())
            ],
            "reason_class_accuracy": {
                key: _mean(values) for key, values in sorted(reason_accuracy.items())
            },
            "scope_accuracy": {
                key: _mean(values) for key, values in sorted(scope_accuracy.items())
            },
            "scope_error_types": dict(sorted(scope_error_types.items())),
            "ab_variant_q1_accuracy": {
                key: _mean(values) for key, values in sorted(ab_accuracy.items())
            },
            "ab_variant_q1_distribution": {
                key: dict(sorted(values.items()))
                for key, values in sorted(ab_selected.items())
            },
            "state_reason_cells": {
                key: {
                    "count": value,
                    "rate": value / total_trials if total_trials else None,
                }
                for key, value in sorted(state_reason_cells.items())
            },
            "relative_rt_ms": {
                "q1_mean": _mean(rt_q1),
                "scope_mean": _mean(rt_scope),
                "reason_mean": _mean(rt_reason),
            },
        }

    reflection = {
        field: dict(
            Counter(
                row["reflection"][field]
                for row in complete
                if row["reflection"][field] is not None
            )
        )
        for field in ("helpful", "confusing", "amount")
    }
    return {
        "schema_version": "button-board-analysis-summary-v1",
        "analysis_version": ANALYSIS_VERSION,
        "materials_version": MATERIALS_VERSION,
        "completed_exports": len(complete),
        "attention_pass_rate": (
            _mean([int(row["attention_check"]["pass"]) for row in complete])
            if complete
            else None
        ),
        "primary_attention_pass": summarize(primary),
        "all_completers_sensitivity": summarize(sensitivity),
        "partial_exports": len(exports) - len(complete),
        "completion_rate_among_exports": len(complete) / len(exports) if exports else None,
        "reflection_distribution": reflection,
        "v9_compatibility_aliases": {
            "q1_correct": "gaa_trial",
            "q2_correct": "reason_correct",
            "cca_correct": "strict_gaa_trial",
            "schema_reused": False,
        },
        "claim_boundary": (
            "Describes comprehension/application of fictional button-board gates "
            "only; it does not test benefit, Contract/Flat differences, real "
            "products, deployment, or human outcomes."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("exports", nargs="+", type=Path)
    parser.add_argument("--verification-key", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    key = args.verification_key.read_bytes()
    summary = analyze(load_exports(args.exports, key))
    text = json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
