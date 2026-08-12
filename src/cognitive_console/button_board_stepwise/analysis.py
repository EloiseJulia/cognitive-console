"""Fail-closed validation and descriptive analysis for signed V11 exports."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from cognitive_console.button_board_stepwise_materials import (
    ANALYSIS_VERSION,
    EXPORT_SCHEMA_VERSION,
    MATERIAL_SCHEMA_VERSION,
    MATERIALS_VERSION,
    SEQUENCE_SCHEMA_VERSION,
    STATES,
    route_participant,
)
from cognitive_console.microstudy.server import canonical_bytes, load_or_create_key

from .materials import (
    locale_bundle_metadata,
    material_hashes,
    planned_trials,
    validated_sources,
)


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
    "attention_selected_id",
    "reflection_choice_ids",
    "trials",
    "verification",
}
TRIAL_FIELDS = {
    "slot_index",
    "scene_id",
    "variant_id",
    "position",
    "planned",
    "presented",
    "step_presented",
    "step_selected_option_id",
    "step_presented_option_order",
    "step_shown_at_relative",
    "step_answered_at_relative",
    "participant_exit_step",
    "participant_derived_state",
    "scope_selected_id",
    "completion_status",
    "materials_version",
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ExportError(message)


def _assert_no_private_keys(value: Any, path: str = "$") -> None:
    blocked = (
        "expected",
        "comparison_rule",
        "required_readings",
        "required_scope_dimensions",
        "scope_correct",
        "scope_written",
        "gaa_correct",
        "strict_correct",
        "correctness",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            _require(
                not any(term in key.lower() for term in blocked),
                f"private or score-derived key at {path}.{key}",
            )
            _assert_no_private_keys(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_no_private_keys(item, f"{path}[{index}]")


def _path(trial: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"step": step, "answer": answer}
        for step, answer in zip(
            trial["step_presented"],
            trial["step_selected_option_id"],
        )
    ]


def trial_scores(
    trial: dict[str, Any],
    slot: dict[str, Any],
) -> dict[str, bool | None]:
    if trial["completion_status"] != "complete":
        return {
            "gaa_trial": None,
            "path_exact": None,
            "decisive_read_correct": None,
            "strict_gaa_trial": None,
        }
    expected_path = [
        {"step": int(step), "answer": answer}
        for step, answer in slot["expected_answer_by_step"].items()
    ]
    participant_path = _path(trial)
    gaa = trial["participant_derived_state"] == slot["expected_state"]
    path_exact = participant_path == expected_path
    decisive_read = (
        trial["participant_exit_step"] == slot["expected_decisive_step"]
        and participant_path[-1]["answer"] == slot["expected_exit_answer"]
    )
    return {
        "gaa_trial": gaa,
        "path_exact": path_exact,
        "decisive_read_correct": decisive_read,
        "strict_gaa_trial": bool(gaa and path_exact and decisive_read),
    }


def _validate_trial(trial: dict[str, Any], slot: dict[str, Any]) -> None:
    _require(set(trial) == TRIAL_FIELDS, "unexpected or missing trial fields")
    _require(
        trial["slot_index"] == slot["slot_index"]
        and trial["scene_id"] == slot["scene_id"]
        and trial["position"] == slot["position"],
        "trial identity mismatch",
    )
    expected_variant = (
        slot["scene_id"].split("-", 1)[1]
        if slot["scene_id"].startswith("AB1-")
        else None
    )
    _require(trial["variant_id"] == expected_variant, "trial variant mismatch")
    _require(trial["planned"] is True, "formal trial must be planned")
    _require(
        trial["materials_version"] == MATERIALS_VERSION,
        "trial materials version mismatch",
    )
    presented = trial["step_presented"]
    selected = trial["step_selected_option_id"]
    orders = trial["step_presented_option_order"]
    shown_times = trial["step_shown_at_relative"]
    answered_times = trial["step_answered_at_relative"]
    _require(
        all(isinstance(row, list) for row in (presented, selected, orders, shown_times, answered_times)),
        "trial step fields must be lists",
    )
    _require(
        len(presented) == len(orders) == len(shown_times),
        "presented step fields are misaligned",
    )
    _require(
        len(selected) == len(answered_times)
        and len(selected) in {len(presented), max(0, len(presented) - 1)},
        "answered step fields are misaligned",
    )
    _require(
        all(type(value) is int and value >= 0 for value in shown_times + answered_times),
        "relative times must be nonnegative integers",
    )
    _require(
        all(later >= earlier for earlier, later in zip(shown_times, answered_times)),
        "answer time precedes shown time",
    )
    if presented:
        _require(presented == list(range(1, len(presented) + 1)), "steps must be sequential")
    for index, step in enumerate(presented):
        order = orders[index]
        _require(isinstance(order, list) and len(order) in {2, 3}, "invalid option order")
        if step == 6:
            _require(order == slot["scope_order_ids"], "scope presentation order mismatch")
        else:
            valid_by_step = {
                1: {"INFO", "CONTROL"},
                2: {"COMPARED", "NOT_COMPARED"},
                3: {"BETTER", "NOT_BETTER"},
                4: {"HARM", "NO_HARM"},
                5: {"SCOPE_WRITTEN", "SCOPE_MISSING"},
            }
            _require(set(order) == valid_by_step[step], f"invalid step {step} options")
        if index < len(selected):
            _require(selected[index] in order, "selected option was not presented")
    if trial["completion_status"] == "complete":
        _require(len(selected) == len(presented) >= 1, "complete trial has missing answer")
        routed = route_participant(_path(trial))
        _require(routed["done"] is True, "complete trial did not reach an exit")
        _require(
            trial["participant_exit_step"] == presented[-1],
            "participant exit step mismatch",
        )
        _require(
            trial["participant_derived_state"] == routed["state"]
            and routed["state"] in STATES,
            "participant state does not match raw route",
        )
        _require(
            trial["scope_selected_id"]
            == (selected[-1] if presented[-1] == 6 else None),
            "scope selection mismatch",
        )
    else:
        _require(
            trial["participant_exit_step"] is None
            and trial["participant_derived_state"] is None
            and trial["scope_selected_id"] is None,
            "unfinished trial contains an exit",
        )
    _require(
        trial["presented"] or not presented,
        "unpresented trial contains step records",
    )


def validate_export(data: dict[str, Any], key: bytes) -> dict[str, Any]:
    _require(isinstance(data, dict), "export must be an object")
    _require(set(data) == SESSION_FIELDS, "unexpected or missing session fields")
    _assert_no_private_keys(data)
    _require(
        data["schema_version"] == MATERIAL_SCHEMA_VERSION,
        "wrong material schema; V9/V10/V11 mixing is forbidden",
    )
    _require(
        data["export_schema_version"] == EXPORT_SCHEMA_VERSION,
        "wrong export schema; V5/V6/V7/V9/V11 mixing is forbidden",
    )
    _require(
        data["sequence_schema_version"] == SEQUENCE_SCHEMA_VERSION,
        "wrong sequence schema",
    )
    _require(data["materials_version"] == MATERIALS_VERSION, "wrong materials version")
    _require(data["analysis_version"] == ANALYSIS_VERSION, "wrong analysis version")
    for field, expected in material_hashes().items():
        _require(data[field] == expected, f"{field} mismatch")
    _, _, keys = validated_sources()
    _require(
        data["ab_invariance_hash"] == keys["ab_invariance_hash"],
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
    signature = hmac.new(key, canonical_bytes(data), hashlib.sha256).hexdigest()
    _require(
        hmac.compare_digest(verification["signature"], signature),
        "invalid export signature",
    )
    _require(data["selected_locale"] in {"en", "zh-Hans"}, "invalid selected locale")
    locale_meta = locale_bundle_metadata(data["selected_locale"])
    _require(
        data["locale_bundle_version"] == locale_meta["locale_bundle_version"]
        and data["locale_bundle_hash"] == locale_meta["locale_bundle_hash"],
        "locale identity mismatch",
    )
    _require(data["ab_variant"] in {"A", "B"}, "invalid A/B variant")
    _require(
        type(data["attempt_serial"]) is int and data["attempt_serial"] >= 1,
        "invalid attempt serial",
    )
    _require(
        type(data["allocation_block"]) is int and data["allocation_block"] >= 0,
        "invalid allocation block",
    )
    _require(
        type(data["allocation_cell"]) is int and 0 <= data["allocation_cell"] < 24,
        "invalid allocation cell",
    )
    expected_sequence = f"BBS11-{data['allocation_cell'] // 2 + 1:02d}"
    expected_variant = "A" if data["allocation_cell"] % 2 == 0 else "B"
    _require(data["sequence_id"] == expected_sequence, "allocation sequence mismatch")
    _require(data["ab_variant"] == expected_variant, "allocation variant mismatch")
    _require(
        data["complete"] is (data["completion_status"] == "complete"),
        "completion status mismatch",
    )
    plan = planned_trials(
        data["sequence_id"],
        data["ab_variant"],
        data["participant_code"],
    )
    trials = data["trials"]
    _require(isinstance(trials, list) and len(trials) == 6, "six trials required")
    for trial, slot in zip(trials, plan):
        _validate_trial(trial, slot)
    expected_ids = {f"AB1-{data['ab_variant']}", "F2", "F3", "F4", "F5", "F6"}
    _require({row["scene_id"] for row in trials} == expected_ids, "formal scene mismatch")
    _require(
        not ({"AB1-A", "AB1-B"} <= {row["scene_id"] for row in trials}),
        "one attempt cannot contain both AB1 variants",
    )
    practice = data["practice_status"]
    _require(
        isinstance(practice, dict)
        and set(practice)
        == {
            "step_presented",
            "step_selected_option_id",
            "participant_exit_step",
            "participant_derived_state",
            "scope_selected_id",
            "completion_status",
        },
        "invalid practice status",
    )
    _require(
        data["attention_selected_id"] in {"INFO", "CONTROL", None},
        "invalid attention response",
    )
    reflection = data["reflection_choice_ids"]
    _require(
        isinstance(reflection, dict)
        and set(reflection) == {"hardest", "confusing", "amount", "pace"},
        "invalid reflection",
    )
    if data["complete"]:
        _require(
            all(row["completion_status"] == "complete" for row in trials),
            "complete export has unfinished trial",
        )
        _require(data["attention_selected_id"] is not None, "complete export lacks attention")
        _require(all(value is not None for value in reflection.values()), "complete export lacks reflection")
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
    participants = [row["participant_code"] for row in exports]
    _require(
        len(participants) == len(set(participants)),
        "duplicate participant code requires owner adjudication",
    )
    return exports


def _mean(values: list[int | float]) -> float | None:
    return sum(values) / len(values) if values else None


def analyze(exports: list[dict[str, Any]]) -> dict[str, Any]:
    confusion: Counter[tuple[str, str]] = Counter()
    decisive = Counter()
    displayed_steps = Counter()
    correct_steps = Counter()
    scope_choices = Counter()
    participant_rows = []
    for export in exports:
        plan = planned_trials(
            export["sequence_id"],
            export["ab_variant"],
            export["participant_code"],
        )
        gaa_values: list[int] = []
        strict_values: list[int] = []
        for trial, slot in zip(export["trials"], plan):
            scores = trial_scores(trial, slot)
            if scores["gaa_trial"] is not None:
                gaa_values.append(int(bool(scores["gaa_trial"])))
                strict_values.append(int(bool(scores["strict_gaa_trial"])))
                confusion[
                    slot["expected_state"],
                    trial["participant_derived_state"],
                ] += 1
                decisive[
                    slot["expected_decisive_step"],
                    bool(scores["decisive_read_correct"]),
                ] += 1
                expected = slot["expected_answer_by_step"]
                for step, answer in zip(
                    trial["step_presented"],
                    trial["step_selected_option_id"],
                ):
                    displayed_steps[step] += 1
                    if answer == expected.get(str(step)):
                        correct_steps[step] += 1
                if trial["participant_exit_step"] == 6:
                    scope_choices[
                        trial["scene_id"],
                        trial["scope_selected_id"] == slot["scope_correct"],
                    ] += 1
        participant_rows.append(
            {
                "participant_code": export["participant_code"],
                "selected_locale": export["selected_locale"],
                "ab_variant": export["ab_variant"],
                "completion_status": export["completion_status"],
                "answered_formal_trials": len(gaa_values),
                "gaa_count": sum(gaa_values),
                "gaa_rate": sum(gaa_values) / len(gaa_values) if gaa_values else None,
                "strict_count": sum(strict_values),
                "strict_rate": (
                    sum(strict_values) / len(strict_values) if strict_values else None
                ),
                "attention_pass": export["attention_selected_id"] == "INFO",
            }
        )
    complete_rows = [row for row in participant_rows if row["completion_status"] == "complete"]
    return {
        "schema_version": "button-board-stepwise-analysis-summary-v1",
        "materials_version": MATERIALS_VERSION,
        "analysis_version": ANALYSIS_VERSION,
        "participant_count": len(participant_rows),
        "complete_count": len(complete_rows),
        "mean_gaa_rate_complete": _mean(
            [row["gaa_rate"] for row in complete_rows if row["gaa_rate"] is not None]
        ),
        "mean_strict_rate_complete": _mean(
            [row["strict_rate"] for row in complete_rows if row["strict_rate"] is not None]
        ),
        "state_confusion": [
            {"expected_state": expected, "participant_state": actual, "count": count}
            for (expected, actual), count in sorted(confusion.items())
        ],
        "decisive_step_accuracy": [
            {
                "step": step,
                "correct": correct,
                "count": count,
            }
            for (step, correct), count in sorted(decisive.items())
        ],
        "displayed_step_accuracy": [
            {
                "step": step,
                "displayed": displayed_steps[step],
                "correct": correct_steps[step],
                "rate": correct_steps[step] / displayed_steps[step],
            }
            for step in sorted(displayed_steps)
        ],
        "scope_choice_counts": [
            {"scene_id": scene_id, "correct": correct, "count": count}
            for (scene_id, correct), count in sorted(scope_choices.items())
        ],
        "participants": participant_rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze signed V11 stepwise exports.")
    parser.add_argument("exports", nargs="+", type=Path)
    parser.add_argument(
        "--verification-key-file",
        type=Path,
        default=Path(".runtime") / "button-board-stepwise-v11-verification.key",
    )
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)
    key = load_or_create_key(args.verification_key_file)
    summary = analyze(load_exports(args.exports, key))
    text = json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    if args.json_out:
        args.json_out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
