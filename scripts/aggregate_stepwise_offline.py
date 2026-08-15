"""Validate and aggregate unsigned V3 stepwise offline exports for the owner."""

from __future__ import annotations

import argparse
import csv
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any

from cognitive_console.button_board_stepwise.analysis import analyze, trial_scores
from cognitive_console.button_board_stepwise.materials import (
    locale_bundle_metadata,
    material_hashes,
    planned_trials,
    validated_sources,
)
from cognitive_console.button_board_stepwise.server import EXPORTED_TRIAL_FIELDS
from cognitive_console.button_board_stepwise_materials import MATERIALS_VERSION, route_participant

OFFLINE_SCHEMA = "microstudy-export-offline-stepwise-v1"
HONESTY_NOTICE = (
    "Fictional illustrative materials; unsigned offline returns depend on honest "
    "submission. Exploratory pilot only; protocol is not frozen. One participant "
    "does not represent the population."
)
PRIVATE_KEY_PARTS = (
    "expected",
    "comparison_rule",
    "required_readings",
    "required_scope_dimensions",
    "scope_correct",
    "gaa_correct",
    "strict_correct",
    "correctness",
)
TOP_LEVEL_FIELDS = {
    "export_schema",
    "signed",
    "submission_id",
    "honesty_notice",
    "materials_version",
    "canonical_materials_hash",
    "locale_bundle_version",
    "locale_bundle_hash",
    "ab_invariance_hash",
    "selected_locale",
    "allocation_cell",
    "sequence_id",
    "ab_variant",
    "participant_label",
    "client_started_at",
    "client_finished_at",
    "demonstration_status",
    "attention_selected_id",
    "reflection_choice_ids",
    "completion_status",
    "trials",
}


class OfflineExportError(ValueError):
    """Raised when an offline file does not match the study contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise OfflineExportError(message)


def _assert_no_private_keys(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _require(
                not any(part in key.lower() for part in PRIVATE_KEY_PARTS),
                f"private key at {path}.{key}",
            )
            _assert_no_private_keys(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_no_private_keys(item, f"{path}[{index}]")


def _path(trial: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"step": step, "answer": answer}
        for step, answer in zip(
            trial["step_presented"], trial["step_selected_option_id"], strict=True
        )
    ]


def _validate_export(data: Any) -> tuple[dict[str, Any], list[str]]:
    _require(isinstance(data, dict), "root must be an object")
    _assert_no_private_keys(data)
    _require(set(data) == TOP_LEVEL_FIELDS, "unexpected or missing top-level fields")
    _require(data["export_schema"] == OFFLINE_SCHEMA, "wrong export schema")
    _require(data["signed"] is False, "offline export must be explicitly unsigned")
    _require(
        isinstance(data["submission_id"], str) and len(data["submission_id"].strip()) >= 8,
        "submission id missing or too short",
    )
    _require(data["materials_version"] == MATERIALS_VERSION, "materials version mismatch")
    hashes = material_hashes()
    _require(
        data["canonical_materials_hash"] == hashes["canonical_materials_hash"],
        "canonical materials hash mismatch",
    )
    _, _, keys = validated_sources()
    _require(
        data["ab_invariance_hash"] == keys["ab_invariance_hash"],
        "A/B invariance hash mismatch",
    )
    locale = data["selected_locale"]
    _require(locale in {"en", "zh-Hans"}, "unsupported locale")
    locale_meta = locale_bundle_metadata(locale)
    _require(
        data["locale_bundle_version"] == locale_meta["locale_bundle_version"]
        and data["locale_bundle_hash"] == locale_meta["locale_bundle_hash"],
        "locale bundle mismatch",
    )
    cell = data["allocation_cell"]
    _require(type(cell) is int and 0 <= cell < 24, "allocation cell out of range")
    sequence_id = f"BBS11-{cell // 2 + 1:02d}"
    ab_variant = "A" if cell % 2 == 0 else "B"
    _require(
        data["sequence_id"] == sequence_id and data["ab_variant"] == ab_variant,
        "allocation identity mismatch",
    )
    _require(
        data["completion_status"] in {"complete", "partial"},
        "invalid completion status",
    )
    _require(isinstance(data["honesty_notice"], str), "honesty notice missing")
    _require(isinstance(data["participant_label"], str), "participant label must be text")
    _require(
        all(isinstance(data[key], str) for key in ("client_started_at", "client_finished_at")),
        "client timestamps must be text",
    )
    _require(
        isinstance(data["reflection_choice_ids"], dict)
        and set(data["reflection_choice_ids"]) == {"hardest", "confusing", "amount", "pace"}
        and all(
            value is None or isinstance(value, str)
            for value in data["reflection_choice_ids"].values()
        ),
        "reflection fields invalid",
    )
    _require(data["demonstration_status"] == "acknowledged", "demonstration not acknowledged")
    _require(
        data["attention_selected_id"] in {"INFO", "CONTROL", None},
        "invalid attention answer",
    )
    _require(isinstance(data["trials"], list) and len(data["trials"]) == 6, "six trials required")

    plan = planned_trials(sequence_id, ab_variant, str(cell))
    warnings: list[str] = []
    cleaned_trials = []
    for index, (trial, slot) in enumerate(zip(data["trials"], plan, strict=True), 1):
        _require(isinstance(trial, dict), f"trial {index} must be an object")
        _require(set(trial) == set(EXPORTED_TRIAL_FIELDS), f"trial {index} fields mismatch")
        _require(
            trial["slot_index"] == slot["slot_index"]
            and trial["scene_id"] == slot["scene_id"]
            and trial["position"] == slot["position"],
            f"trial {index} identity mismatch",
        )
        variant = ab_variant if slot["scene_id"].startswith("AB1-") else None
        _require(trial["variant_id"] == variant, f"trial {index} variant mismatch")
        _require(trial["planned"] is True, f"trial {index} is not planned")
        _require(trial["materials_version"] == MATERIALS_VERSION, f"trial {index} materials mismatch")
        presented = trial["step_presented"]
        selected = trial["step_selected_option_id"]
        orders = trial["step_presented_option_order"]
        shown = trial["step_shown_at_relative"]
        answered = trial["step_answered_at_relative"]
        _require(
            all(isinstance(x, list) for x in (presented, selected, orders, shown, answered)),
            f"trial {index} step fields must be lists",
        )
        _require(
            len(presented) == len(selected) == len(orders) == len(shown) == len(answered),
            f"trial {index} step fields are misaligned",
        )
        _require(presented == list(range(1, len(presented) + 1)), f"trial {index} steps not sequential")
        _require(
            all(type(value) is int and value >= 0 for value in shown + answered),
            f"trial {index} times invalid",
        )
        _require(
            all(answered_at >= shown_at for shown_at, answered_at in zip(shown, answered, strict=True)),
            f"trial {index} answer precedes display",
        )
        valid_options = {
            1: {"INFO", "CONTROL"},
            2: {"COMPARED", "NOT_COMPARED"},
            3: {"BETTER", "NOT_BETTER"},
            4: {"HARM", "NO_HARM"},
            5: {"SCOPE_WRITTEN", "SCOPE_MISSING"},
        }
        for step, answer, order in zip(presented, selected, orders, strict=True):
            _require(isinstance(order, list) and answer in order, f"trial {index} answer not presented")
            if step == 6:
                _require(order == slot["scope_order_ids"], f"trial {index} scope order mismatch")
            else:
                _require(set(order) == valid_options[step], f"trial {index} option order invalid")
        _require(
            trial["completion_status"] in {"not_started", "in_progress", "complete"},
            f"trial {index} completion invalid",
        )
        _require(
            trial["presented"] is (trial["completion_status"] != "not_started"),
            f"trial {index} presented status mismatch",
        )
        cleaned = json.loads(json.dumps(trial))
        if selected:
            path = _path(trial)
            routed = route_participant(path)
            first_exit = next(
                (
                    cutoff
                    for cutoff in range(1, len(path) + 1)
                    if route_participant(path[:cutoff])["done"]
                ),
                None,
            )
            _require(
                first_exit is None or first_exit == len(path),
                f"trial {index} contains answers after route exit",
            )
            rebuilt_exit = first_exit
            rebuilt_state = routed["state"] if routed["done"] else None
            rebuilt_scope = selected[-1] if rebuilt_exit == 6 else None
            if (
                trial["participant_exit_step"] != rebuilt_exit
                or trial["participant_derived_state"] != rebuilt_state
                or trial["scope_selected_id"] != rebuilt_scope
            ):
                warnings.append(f"trial {index}: recorded route metadata disagreed with raw answers; rebuilt values used")
            cleaned["participant_exit_step"] = rebuilt_exit
            cleaned["participant_derived_state"] = rebuilt_state
            cleaned["scope_selected_id"] = rebuilt_scope
            _require(
                (trial["completion_status"] == "complete") is routed["done"],
                f"trial {index} completion disagrees with route",
            )
        else:
            _require(
                trial["completion_status"] != "complete",
                f"trial {index} marked complete without answers",
            )
            cleaned["participant_exit_step"] = None
            cleaned["participant_derived_state"] = None
            cleaned["scope_selected_id"] = None
        cleaned_trials.append(cleaned)
    all_complete = all(trial["completion_status"] == "complete" for trial in cleaned_trials)
    _require(
        (data["completion_status"] == "complete") is all_complete,
        "export completion disagrees with trials",
    )
    cleaned = json.loads(json.dumps(data))
    cleaned["trials"] = cleaned_trials
    return cleaned, warnings


def _safe(value: Any) -> str:
    if value is None:
        return ""
    text = (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        if isinstance(value, (dict, list))
        else str(value)
    )
    return "'" + text if text.startswith(("=", "+", "-", "@")) else text


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\r\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: _safe(row.get(field)) for field in fields})
    path.write_text("\ufeff" + output.getvalue(), encoding="utf-8", newline="")


def aggregate(input_dir: Path, out_dir: Path) -> dict[str, Any]:
    input_dir = Path(input_dir)
    out_dir = Path(out_dir)
    _require(input_dir.is_dir(), "input path must be a directory")
    out_dir.mkdir(parents=True, exist_ok=True)
    accepted: list[tuple[Path, dict[str, Any]]] = []
    skipped: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    seen_ids: dict[str, str] = {}
    for path in sorted(input_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
            cleaned, file_warnings = _validate_export(data)
            submission_id = cleaned["submission_id"]
            if submission_id in seen_ids:
                skipped.append(
                    {
                        "file": path.name,
                        "reason": f"duplicate submission_id (already counted in {seen_ids[submission_id]})",
                    }
                )
                continue
            seen_ids[submission_id] = path.name
            accepted.append((path, cleaned))
            warnings.extend({"file": path.name, "message": message} for message in file_warnings)
        except (OSError, json.JSONDecodeError, OfflineExportError, ValueError) as error:
            skipped.append({"file": path.name, "reason": str(error)})

    participant_rows: list[dict[str, Any]] = []
    trial_rows: list[dict[str, Any]] = []
    analysis_exports = []
    for path, export in accepted:
        cell = export["allocation_cell"]
        plan = planned_trials(export["sequence_id"], export["ab_variant"], str(cell))
        gaa_values: list[int] = []
        strict_values: list[int] = []
        for trial, slot in zip(export["trials"], plan, strict=True):
            scores = trial_scores(trial, slot)
            gaa = scores["gaa_trial"]
            strict = scores["strict_gaa_trial"]
            if gaa is not None:
                gaa_values.append(int(bool(gaa)))
                strict_values.append(int(bool(strict)))
            step_matches = [
                answer == slot["expected_answer_by_step"].get(str(step))
                for step, answer in zip(
                    trial["step_presented"], trial["step_selected_option_id"], strict=True
                )
            ]
            total_ms = (
                trial["step_answered_at_relative"][-1] - trial["step_shown_at_relative"][0]
                if trial["step_answered_at_relative"]
                else None
            )
            trial_rows.append(
                {
                    "source_file": path.name,
                    "participant_label": export["participant_label"],
                    "allocation_cell": cell,
                    "sequence_id": export["sequence_id"],
                    "ab_variant": export["ab_variant"],
                    "slot_index": trial["slot_index"],
                    "scene_id": trial["scene_id"],
                    "reference_state": slot["expected_state"],
                    "participant_state": trial["participant_derived_state"],
                    "gaa_trial": gaa,
                    "path_exact": scores["path_exact"],
                    "decisive_read_correct": scores["decisive_read_correct"],
                    "strict_gaa_trial": strict,
                    "step_matches": step_matches,
                    "scope_match": (
                        trial["scope_selected_id"] == slot["scope_correct"]
                        if trial["participant_exit_step"] == 6
                        else None
                    ),
                    "total_ms": total_ms,
                    "completion_status": trial["completion_status"],
                }
            )
        participant_rows.append(
            {
                "source_file": path.name,
                "submission_id": export["submission_id"],
                "participant_label": export["participant_label"],
                "allocation_cell": cell,
                "sequence_id": export["sequence_id"],
                "ab_variant": export["ab_variant"],
                "selected_locale": export["selected_locale"],
                "completion_status": export["completion_status"],
                "answered_trials": len(gaa_values),
                "gaa_count": sum(gaa_values),
                "gaa_rate": sum(gaa_values) / len(gaa_values) if gaa_values else None,
                "strict_count": sum(strict_values),
                "strict_rate": sum(strict_values) / len(strict_values) if strict_values else None,
                "attention_pass": export["attention_selected_id"] == "INFO",
            }
        )
        analysis_copy = json.loads(json.dumps(export))
        analysis_copy["attempt_id"] = str(cell)
        analysis_exports.append(analysis_copy)

    summary = analyze(analysis_exports)
    summary.update(
        {
            "participants": participant_rows,
            "source_schema": OFFLINE_SCHEMA,
            "signed": False,
            "honesty_notice": HONESTY_NOTICE,
            "accepted_files": [path.name for path, _ in accepted],
            "skipped_files": skipped,
            "warnings": warnings,
        }
    )
    _write_csv(out_dir / "participants.csv", list(participant_rows[0]) if participant_rows else [
        "source_file", "submission_id", "participant_label", "allocation_cell", "sequence_id", "ab_variant",
        "selected_locale", "completion_status", "answered_trials", "gaa_count", "gaa_rate",
        "strict_count", "strict_rate", "attention_pass"
    ], participant_rows)
    _write_csv(out_dir / "per_trial.csv", list(trial_rows[0]) if trial_rows else [
        "source_file", "participant_label", "allocation_cell", "sequence_id", "ab_variant",
        "slot_index", "scene_id", "reference_state", "participant_state", "gaa_trial",
        "path_exact", "decisive_read_correct", "strict_gaa_trial", "step_matches", "scope_match",
        "total_ms", "completion_status"
    ], trial_rows)
    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    print(HONESTY_NOTICE)
    summary = aggregate(args.input_dir, args.out_dir)
    print(
        f"accepted={len(summary['accepted_files'])} skipped={len(summary['skipped_files'])} "
        f"warnings={len(summary['warnings'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
