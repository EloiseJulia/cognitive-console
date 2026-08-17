"""校验并汇总 Study B **半实时**（live）未签名导出（owner 侧）。

与离线版一致的红线：本汇总器 **不运行模型、不计算 Q、不给 prompt 打分、不判方向**。Q 是
独立登记的事后批量评分实验（固定 code commit / seed / model / rubric），本脚本只校验参与者侧
契约、按 ``submission_id`` 去重、产出整洁 CSV/JSON，并为事后 Q 留 **空占位列**。

与离线版的差异（live 新增）：
* schema id = ``microstudy-export-live-studyB-v1``；顶层新增 ``model_id`` / ``params_hash``
  / ``bridge_version``。
* ``tasks[].slider`` / ``tasks[].own_prompt`` 各新增 ``generations`` 列表、``final_*`` 字段。
* 新产物 ``generations.csv``：一行/次生成，``output_text`` 单列保存（供事后 Q 取用）。

**完全自包含**：不 import / 不依赖 V3 button_board_stepwise 包、其冻结答案或 materials v11.3。

**硬契约**：payload 中任何 ``expected`` / ``answer_key`` / ``rubric`` / Q 值 **键名** 一律拒绝；
模型输出文本是 **数据**，作为自由文本值不扫描。沿用离线版标量守卫（拒绝把答案藏进无害键的
嵌套容器）。协议未冻结 → 数据 exploratory。

Status: RED pre-freeze DRAFT 工具。
"""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
from typing import Any

EXPORT_SCHEMA = "microstudy-export-live-studyB-v1"
HONESTY_NOTICE = (
    "Fictional / illustrative materials; this study DISPLAYS AI-generated example "
    "outputs. Unsigned local returns depend on honest submission. Exploratory pilot; "
    "protocol is not frozen. One participant does not represent any population. This "
    "tool draws no user-benefit conclusion. No task-quality (Q) value is computed "
    "here; Q is a separate post-hoc scoring experiment. Model outputs are DATA, not "
    "answer keys."
)

# 出现在 KEY 中即视为答案键/rubric/Q 值泄漏。参与者自由文本值（含模型输出）是数据，不扫描。
PRIVATE_KEY_PARTS = (
    "expected",
    "answer_key",
    "answerkey",
    "rubric",
    "gold_answer",
    "ground_truth",
    "correct",
    "correct_answer",
    "correctanswer",
    "quality_score",
    "q_value",
)

TOP_LEVEL_FIELDS = {
    "export_schema",
    "signed",
    "submission_id",
    "honesty_notice",
    "instrument_version",
    "bridge_version",
    "model_id",
    "params_hash",
    "selected_locale",
    "consent_agreed",
    "consent_agreed_at",
    "consent_copy_version",
    "client_started_at",
    "client_finished_at",
    "completion_status",
    "covariates",
    "probe",
    "task_order",
    "tasks",
    "convenience",
    "attention",
}
COVARIATE_KEYS = {
    "usage_frequency",
    "tuned_parameters",
    "understands_latent_control",
    "self_rating",
}
PROBE_KEYS = {
    "prompt_text",
    "started_at_relative",
    "committed_at_relative",
    "char_count",
    "edit_count",
}
TASK_ORDER_KEYS = {"seed", "sequence"}
TASK_KEYS = {"task_id", "condition_order", "slider", "own_prompt"}
SLIDER_KEYS = {
    "final_stop_id",
    "final_output_text",
    "settings_explored",
    "generations",
    "started_at_relative",
    "committed_at_relative",
}
SLIDER_GENERATION_KEYS = {"stop_id", "output_text", "at_relative"}
OWN_PROMPT_KEYS = {
    "prompt_text",
    "char_count",
    "edit_count",
    "final_output_text",
    "generations",
    "started_at_relative",
    "committed_at_relative",
}
OWN_PROMPT_GENERATION_KEYS = {"prompt_text", "output_text", "at_relative"}
CONVENIENCE_KEYS = {
    "tlx_effort",
    "likert_effort",
    "likert_discoverability",
    "willingness_choice",
    "willingness_reason",
}
ATTENTION_KEYS = {"selected_id"}

# 事后 Q 批量评分的空占位列，本汇总器永不填。
TASK_Q_PLACEHOLDER_COLUMNS = (
    "q_slider_pending",
    "q_own_prompt_pending",
    "d_paired_pending",
)


class LiveExportError(ValueError):
    """导出不符合 Study B live 契约时抛出。"""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise LiveExportError(message)


def _assert_no_private_keys(value: Any, path: str = "$") -> None:
    """拒绝任何 answer-key/rubric/Q 词作为 dict KEY 出现。"""
    if isinstance(value, dict):
        for key, item in value.items():
            _require(
                not any(part in str(key).lower() for part in PRIVATE_KEY_PARTS),
                f"private key at {path}.{key}",
            )
            _assert_no_private_keys(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_no_private_keys(item, f"{path}[{index}]")


def _assert_scalar_values(mapping: dict[str, Any], label: str) -> None:
    """拒绝在应存标量的字段里藏嵌套容器（沿用离线版 MAJOR-1 修复）。"""
    for key, value in mapping.items():
        _require(
            value is None or isinstance(value, (int, float, str)),
            f"{label}.{key} must be a scalar value, not a container",
        )


def _monotonic(started: Any, committed: Any, label: str) -> None:
    if started is not None and committed is not None:
        _require(
            type(started) is int and type(committed) is int and started >= 0 and committed >= 0,
            f"{label} relative times must be non-negative ints",
        )
        _require(committed >= started, f"{label} committed precedes start")


def _validate_generation(gen: Any, allowed: set[str], text_key: str, label: str) -> None:
    _require(isinstance(gen, dict) and set(gen) == allowed, f"{label} generation fields mismatch")
    _require(isinstance(gen["output_text"], str), f"{label} generation output_text must be text")
    _require(isinstance(gen[text_key], str) and gen[text_key] != "", f"{label} generation {text_key} invalid")
    _require(
        type(gen["at_relative"]) is int and gen["at_relative"] >= 0,
        f"{label} generation at_relative invalid",
    )


def _validate_export(data: Any) -> dict[str, Any]:
    _require(isinstance(data, dict), "root must be an object")
    _assert_no_private_keys(data)
    _require(set(data) == TOP_LEVEL_FIELDS, "unexpected or missing top-level fields")
    _require(data["export_schema"] == EXPORT_SCHEMA, "wrong export schema")
    _require(data["signed"] is False, "live export must be explicitly unsigned")
    _require(
        isinstance(data["submission_id"], str) and len(data["submission_id"].strip()) >= 8,
        "submission id missing or too short",
    )
    _require(data["selected_locale"] in {"en", "zh-Hans"}, "unsupported locale")
    _require(isinstance(data["consent_agreed"], bool), "consent_agreed must be boolean")
    _require(data["consent_agreed"] is True, "export requires recorded consent")
    _require(isinstance(data["honesty_notice"], str), "honesty notice missing")
    _require(isinstance(data["instrument_version"], str), "instrument version missing")
    _require(isinstance(data["consent_copy_version"], str), "consent copy version missing")
    for key in ("model_id", "params_hash", "bridge_version"):
        _require(
            data[key] is None or isinstance(data[key], str),
            f"{key} must be text or null",
        )
    _require(
        data["completion_status"] in {"complete", "partial"},
        "invalid completion status",
    )
    for key in ("client_started_at", "consent_agreed_at"):
        _require(isinstance(data[key], str), f"{key} must be text")
    _require(
        data["client_finished_at"] is None or isinstance(data["client_finished_at"], str),
        "client_finished_at must be text or null",
    )
    if isinstance(data["client_finished_at"], str):
        _require(
            data["client_finished_at"] >= data["client_started_at"],
            "client_finished_at precedes start",
        )

    covariates = data["covariates"]
    _require(isinstance(covariates, dict) and set(covariates) == COVARIATE_KEYS, "covariate fields mismatch")
    _assert_scalar_values(covariates, "covariates")

    probe = data["probe"]
    _require(isinstance(probe, dict) and set(probe) == PROBE_KEYS, "probe fields mismatch")
    _require(isinstance(probe["prompt_text"], str), "probe prompt_text must be text")
    _require(type(probe["char_count"]) is int and probe["char_count"] >= 0, "probe char_count invalid")
    _require(type(probe["edit_count"]) is int and probe["edit_count"] >= 0, "probe edit_count invalid")
    _monotonic(probe["started_at_relative"], probe["committed_at_relative"], "probe")

    order = data["task_order"]
    _require(isinstance(order, dict) and set(order) == TASK_ORDER_KEYS, "task_order fields mismatch")
    _require(type(order["seed"]) is int and order["seed"] >= 0, "task_order seed invalid")
    _require(isinstance(order["sequence"], list), "task_order sequence must be a list")
    for item in order["sequence"]:
        _require(
            isinstance(item, dict) and set(item) == {"task_id", "condition_order"},
            "task_order sequence element malformed",
        )
        _require(item["condition_order"] in {"slider_first", "prompt_first"}, "invalid condition order in sequence")

    tasks = data["tasks"]
    _require(isinstance(tasks, list) and len(tasks) == 1, "simplified collector requires exactly one task")
    _require(
        [t["task_id"] for t in order["sequence"]] == [t["task_id"] for t in tasks],
        "task_order sequence and tasks disagree on task ids/order",
    )
    _require(
        [t["condition_order"] for t in order["sequence"]] == [t["condition_order"] for t in tasks],
        "task_order sequence and tasks disagree on condition order",
    )
    for index, task in enumerate(tasks, 1):
        _require(isinstance(task, dict) and set(task) == TASK_KEYS, f"task {index} fields mismatch")
        _require(isinstance(task["task_id"], str) and task["task_id"], f"task {index} id missing")
        _require(
            task["condition_order"] in {"slider_first", "prompt_first"},
            f"task {index} condition order invalid",
        )
        slider = task["slider"]
        _require(isinstance(slider, dict) and set(slider) == SLIDER_KEYS, f"task {index} slider fields mismatch")
        _require(
            slider["final_stop_id"] is None or isinstance(slider["final_stop_id"], str),
            f"task {index} slider final_stop_id invalid",
        )
        _require(
            slider["final_output_text"] is None or isinstance(slider["final_output_text"], str),
            f"task {index} slider final_output_text invalid",
        )
        _require(
            type(slider["settings_explored"]) is int and slider["settings_explored"] >= 0,
            f"task {index} settings_explored invalid",
        )
        _require(isinstance(slider["generations"], list), f"task {index} slider generations must be a list")
        for gen in slider["generations"]:
            _validate_generation(gen, SLIDER_GENERATION_KEYS, "stop_id", f"task {index} slider")
        _monotonic(slider["started_at_relative"], slider["committed_at_relative"], f"task {index} slider")

        own = task["own_prompt"]
        _require(isinstance(own, dict) and set(own) == OWN_PROMPT_KEYS, f"task {index} own_prompt fields mismatch")
        _require(isinstance(own["prompt_text"], str), f"task {index} own_prompt text invalid")
        _require(type(own["char_count"]) is int and own["char_count"] >= 0, f"task {index} own_prompt char_count invalid")
        _require(type(own["edit_count"]) is int and own["edit_count"] >= 0, f"task {index} own_prompt edit_count invalid")
        _require(
            own["final_output_text"] is None or isinstance(own["final_output_text"], str),
            f"task {index} own_prompt final_output_text invalid",
        )
        _require(isinstance(own["generations"], list), f"task {index} own_prompt generations must be a list")
        for gen in own["generations"]:
            _validate_generation(gen, OWN_PROMPT_GENERATION_KEYS, "prompt_text", f"task {index} own_prompt")
        _monotonic(own["started_at_relative"], own["committed_at_relative"], f"task {index} own_prompt")

    convenience = data["convenience"]
    _require(
        isinstance(convenience, dict) and set(convenience) == CONVENIENCE_KEYS,
        "convenience fields mismatch",
    )
    _assert_scalar_values(convenience, "convenience")
    _require(
        convenience["willingness_choice"] in {"slider", "own_prompt", None},
        "willingness_choice invalid",
    )
    _require(isinstance(convenience["willingness_reason"], str), "willingness_reason must be text")

    attention = data["attention"]
    _require(isinstance(attention, dict) and set(attention) == ATTENTION_KEYS, "attention fields mismatch")
    _assert_scalar_values(attention, "attention")
    _require(
        attention["selected_id"] is None or isinstance(attention["selected_id"], str),
        "attention selected_id invalid",
    )

    if data["completion_status"] == "complete":
        _require(isinstance(data["client_finished_at"], str), "complete export must have a finish time")
        _require(isinstance(data["model_id"], str) and data["model_id"], "complete export must record model_id")
        _require(probe["committed_at_relative"] is not None, "complete export must have a committed probe")
        _require(
            all(
                t["slider"]["committed_at_relative"] is not None
                and t["own_prompt"]["committed_at_relative"] is not None
                for t in tasks
            ),
            "complete export must have both conditions committed for every task",
        )
        _require(
            all(
                len(t["slider"]["generations"]) >= 1 and len(t["own_prompt"]["generations"]) >= 1
                for t in tasks
            ),
            "complete export must have at least one generation per condition",
        )
        _require(convenience["willingness_choice"] is not None, "complete export must record willingness")
        _require(attention["selected_id"] is not None, "complete export must record attention answer")

    return json.loads(json.dumps(data))


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


def _duration(started: Any, committed: Any) -> Any:
    if started is None or committed is None:
        return None
    return committed - started


PARTICIPANT_FIELDS = [
    "source_file",
    "submission_id",
    "instrument_version",
    "bridge_version",
    "model_id",
    "params_hash",
    "consent_copy_version",
    "selected_locale",
    "completion_status",
    "consent_agreed",
    "consent_agreed_at",
    "order_seed",
    "cov_usage_frequency",
    "cov_tuned_parameters",
    "cov_understands_latent_control",
    "cov_self_rating",
    "probe_char_count",
    "probe_edit_count",
    "probe_duration_ms",
    "tlx_effort",
    "likert_effort",
    "likert_discoverability",
    "willingness_choice",
    "willingness_reason",
    "attention_selected_id",
    "n_tasks",
]
TASK_FIELDS = [
    "source_file",
    "submission_id",
    "selected_locale",
    "model_id",
    "task_id",
    "condition_order",
    "slider_final_stop_id",
    "slider_settings_explored",
    "slider_generation_count",
    "slider_duration_ms",
    "own_prompt_char_count",
    "own_prompt_edit_count",
    "own_prompt_generation_count",
    "own_prompt_duration_ms",
    "own_prompt_text",
    *TASK_Q_PLACEHOLDER_COLUMNS,
]
GENERATION_FIELDS = [
    "source_file",
    "submission_id",
    "task_id",
    "condition",
    "generation_index",
    "stop_id",
    "prompt_char_count",
    "output_char_count",
    "at_relative",
    "output_text",
]


def aggregate(input_dir: Path, out_dir: Path) -> dict[str, Any]:
    input_dir = Path(input_dir)
    out_dir = Path(out_dir)
    _require(input_dir.is_dir(), "input path must be a directory")
    out_dir.mkdir(parents=True, exist_ok=True)

    accepted: list[tuple[str, dict[str, Any]]] = []
    skipped: list[dict[str, str]] = []
    seen_ids: dict[str, str] = {}

    for path in sorted(input_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
            cleaned = _validate_export(data)
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
            accepted.append((path.name, cleaned))
        except (OSError, json.JSONDecodeError, LiveExportError, ValueError) as error:
            skipped.append({"file": path.name, "reason": str(error)})

    participant_rows: list[dict[str, Any]] = []
    task_rows: list[dict[str, Any]] = []
    generation_rows: list[dict[str, Any]] = []
    for name, export in accepted:
        cov = export["covariates"]
        conv = export["convenience"]
        probe = export["probe"]
        participant_rows.append(
            {
                "source_file": name,
                "submission_id": export["submission_id"],
                "instrument_version": export["instrument_version"],
                "bridge_version": export["bridge_version"],
                "model_id": export["model_id"],
                "params_hash": export["params_hash"],
                "consent_copy_version": export["consent_copy_version"],
                "selected_locale": export["selected_locale"],
                "completion_status": export["completion_status"],
                "consent_agreed": export["consent_agreed"],
                "consent_agreed_at": export["consent_agreed_at"],
                "order_seed": export["task_order"]["seed"],
                "cov_usage_frequency": cov["usage_frequency"],
                "cov_tuned_parameters": cov["tuned_parameters"],
                "cov_understands_latent_control": cov["understands_latent_control"],
                "cov_self_rating": cov["self_rating"],
                "probe_char_count": probe["char_count"],
                "probe_edit_count": probe["edit_count"],
                "probe_duration_ms": _duration(
                    probe["started_at_relative"], probe["committed_at_relative"]
                ),
                "tlx_effort": conv["tlx_effort"],
                "likert_effort": conv["likert_effort"],
                "likert_discoverability": conv["likert_discoverability"],
                "willingness_choice": conv["willingness_choice"],
                "willingness_reason": conv["willingness_reason"],
                "attention_selected_id": export["attention"]["selected_id"],
                "n_tasks": len(export["tasks"]),
            }
        )
        for task in export["tasks"]:
            slider = task["slider"]
            own = task["own_prompt"]
            row = {
                "source_file": name,
                "submission_id": export["submission_id"],
                "selected_locale": export["selected_locale"],
                "model_id": export["model_id"],
                "task_id": task["task_id"],
                "condition_order": task["condition_order"],
                "slider_final_stop_id": slider["final_stop_id"],
                "slider_settings_explored": slider["settings_explored"],
                "slider_generation_count": len(slider["generations"]),
                "slider_duration_ms": _duration(
                    slider["started_at_relative"], slider["committed_at_relative"]
                ),
                "own_prompt_char_count": own["char_count"],
                "own_prompt_edit_count": own["edit_count"],
                "own_prompt_generation_count": len(own["generations"]),
                "own_prompt_duration_ms": _duration(
                    own["started_at_relative"], own["committed_at_relative"]
                ),
                "own_prompt_text": own["prompt_text"],
            }
            # Q 占位列留空，供事后评分实验回填。
            for column in TASK_Q_PLACEHOLDER_COLUMNS:
                row[column] = None
            task_rows.append(row)

            for gen_index, gen in enumerate(slider["generations"]):
                generation_rows.append(
                    {
                        "source_file": name,
                        "submission_id": export["submission_id"],
                        "task_id": task["task_id"],
                        "condition": "slider",
                        "generation_index": gen_index,
                        "stop_id": gen["stop_id"],
                        "prompt_char_count": None,
                        "output_char_count": len(gen["output_text"]),
                        "at_relative": gen["at_relative"],
                        "output_text": gen["output_text"],
                    }
                )
            for gen_index, gen in enumerate(own["generations"]):
                generation_rows.append(
                    {
                        "source_file": name,
                        "submission_id": export["submission_id"],
                        "task_id": task["task_id"],
                        "condition": "own_prompt",
                        "generation_index": gen_index,
                        "stop_id": None,
                        "prompt_char_count": len(gen["prompt_text"]),
                        "output_char_count": len(gen["output_text"]),
                        "at_relative": gen["at_relative"],
                        "output_text": gen["output_text"],
                    }
                )

    _write_csv(out_dir / "participants.csv", PARTICIPANT_FIELDS, participant_rows)
    _write_csv(out_dir / "tasks.csv", TASK_FIELDS, task_rows)
    _write_csv(out_dir / "generations.csv", GENERATION_FIELDS, generation_rows)

    model_ids = sorted({export["model_id"] for _, export in accepted if export["model_id"]})
    summary = {
        "source_schema": EXPORT_SCHEMA,
        "signed": False,
        "honesty_notice": HONESTY_NOTICE,
        "participant_count": len(accepted),
        "task_row_count": len(task_rows),
        "generation_row_count": len(generation_rows),
        "model_id": model_ids,
        "accepted_files": [name for name, _ in accepted],
        "skipped_files": skipped,
        "q_scoring": {
            "computed_here": False,
            "note": (
                "Q (task-quality) is NOT computed by this aggregator. It is a "
                "separate post-hoc batch-scoring experiment registered in "
                "experiment-registry, run over the saved output_text in "
                "generations.csv. The columns below are empty placeholders in "
                "tasks.csv awaiting that experiment."
            ),
            "pending_columns": list(TASK_Q_PLACEHOLDER_COLUMNS),
        },
    }
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
        f"accepted={summary['participant_count']} skipped={len(summary['skipped_files'])} "
        f"task_rows={summary['task_row_count']} generation_rows={summary['generation_row_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
