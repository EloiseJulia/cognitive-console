"""Study B 半实时（live）采集器测试：生成器 + 汇总器 + 桥接。

覆盖：参与者侧硬契约（零答案键 / 零 Q）、schema 校验、submission_id 去重、标量守卫、
generations 解析、桥接组装（slider 用冻结预设 / own_prompt 用参与者 prompt）、
预设不含任务成功条件字样、模型白名单拒未知 id、桥接只 bind 127.0.0.1。
桥接对 8313 的 HTTP 用本地 stub 注入，**不在单测里真打 8313**。自包含，不 import V3。
"""

import csv
import importlib.util
import io
import json
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


generator = _load("studyB_live_generator", "scripts/generate_studyB_live.py")
aggregator = _load("studyB_live_aggregator", "scripts/aggregate_studyB_live.py")
bridge = _load("studyB_live_bridge", "scripts/run_studyB_live.py")


def _payload_from_html(html: str) -> dict:
    marker = '<script id="study-data" type="application/json">'
    raw = html.split(marker, 1)[1].split("</script>", 1)[0]
    return json.loads(raw.replace("<\\/", "</"))


def _slider(*, complete: bool = True) -> dict:
    gens = (
        [{"stop_id": "s3", "output_text": "A calm vegan oat bar blurb.", "at_relative": 1200}]
        if complete
        else []
    )
    return {
        "final_stop_id": "s3" if complete else None,
        "final_output_text": "A calm vegan oat bar blurb." if complete else None,
        "settings_explored": 2 if complete else 0,
        "generations": gens,
        "started_at_relative": 1000,
        "committed_at_relative": 1500 if complete else None,
    }


def _own(*, complete: bool = True) -> dict:
    gens = (
        [
            {
                "prompt_text": "Rewrite it warmly and briefly.",
                "output_text": "A warm, brief vegan oat bar note.",
                "at_relative": 2000,
            }
        ]
        if complete
        else []
    )
    return {
        "prompt_text": "Rewrite it warmly and briefly." if complete else "",
        "char_count": 30 if complete else 0,
        "edit_count": 5 if complete else 0,
        "final_output_text": "A warm, brief vegan oat bar note." if complete else None,
        "generations": gens,
        "started_at_relative": 1600,
        "committed_at_relative": 2200 if complete else None,
    }


def _task(task_id: str, condition_order: str = "slider_first", *, complete: bool = True) -> dict:
    return {
        "task_id": task_id,
        "condition_order": condition_order,
        "slider": _slider(complete=complete),
        "own_prompt": _own(complete=complete),
    }


def _base_export(*, complete: bool = True) -> dict:
    order = [{"task_id": "draftA-recipe-blurb", "condition_order": "slider_first"}]
    return {
        "export_schema": aggregator.EXPORT_SCHEMA,
        "signed": False,
        "submission_id": str(uuid.uuid4()),
        "honesty_notice": "Fictional illustrative; displays AI output; exploratory.",
        "instrument_version": "studyB-collector-live-0.1.0-draft",
        "bridge_version": "studyB-bridge-0.1.0-draft",
        "model_id": "gpt-4o-mini" if complete else None,
        "params_hash": "sha256:abcdef0123456789" if complete else None,
        "selected_locale": "en",
        "consent_agreed": True,
        "consent_agreed_at": "2026-08-17T00:00:00.000Z",
        "consent_copy_version": "studyB-consent-live-1.0",
        "client_started_at": "2026-08-17T00:00:00.000Z",
        "client_finished_at": "2026-08-17T00:10:00.000Z" if complete else None,
        "completion_status": "complete" if complete else "partial",
        "covariates": {
            "usage_frequency": "weekly",
            "tuned_parameters": "no",
            "understands_latent_control": "a_little",
            "self_rating": 3,
        },
        "probe": {
            "prompt_text": "Rewrite the notice in under 60 words, warm tone.",
            "started_at_relative": 100,
            "committed_at_relative": 800,
            "char_count": 48,
            "edit_count": 12,
        },
        "task_order": {"seed": 123456789, "sequence": order},
        "tasks": [_task("draftA-recipe-blurb", "slider_first", complete=complete)],
        "convenience": {
            "tlx_effort": 3,
            "likert_effort": 4,
            "likert_discoverability": 3,
            "willingness_choice": "own_prompt" if complete else None,
            "willingness_reason": "I trust my own wording.",
        },
        "attention": {"selected_id": "purple" if complete else None},
    }


def _read_csv(path: Path) -> tuple[list[str], list[dict]]:
    text = path.read_text(encoding="utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    return reader.fieldnames or [], list(reader)


# --- 生成器 / 参与者侧契约 ----------------------------------------------------


def test_generated_html_contains_no_forbidden_terms(tmp_path):
    output = tmp_path / "studyB.html"
    generator.generate(output)
    html = output.read_text(encoding="utf-8")
    lowered = html.lower()
    for term in generator.FORBIDDEN_TERMS:
        assert term not in lowered


def test_generated_payload_has_no_answer_keys_and_right_schema(tmp_path):
    output = tmp_path / "studyB.html"
    generator.generate(output)
    payload = _payload_from_html(output.read_text(encoding="utf-8"))
    serialized = json.dumps(payload, ensure_ascii=False).lower()
    for term in ("expected", "answer_key", "rubric", "ground_truth", "correct_answer"):
        assert term not in serialized
    assert payload["export_schema"] == aggregator.EXPORT_SCHEMA
    assert payload["export_schema"] == "microstudy-export-live-studyB-v1"
    assert payload["signed"] is False
    assert len(payload["tasks"]) == 1
    assert set(payload["honesty_notice"]) == {"en", "zh-Hans"}
    assert "submission_id" not in payload
    # 预设文本绝不出现在前端 payload / HTML（只存服务端桥接）。
    for preset_text in bridge.FROZEN_TASKS["draftA-recipe-blurb"]["presets"].values():
        assert preset_text not in output.read_text(encoding="utf-8")


def test_html_generates_submission_id_and_fetches_bridge(tmp_path):
    output = tmp_path / "studyB.html"
    generator.generate(output)
    html = output.read_text(encoding="utf-8")
    assert "crypto.randomUUID" in html
    assert "/api/generate" in html
    payload = _payload_from_html(html)
    assert "submission_id" not in payload


def test_build_html_matches_generated_file(tmp_path):
    output = tmp_path / "studyB.html"
    generator.generate(output)
    assert generator.build_html() == output.read_text(encoding="utf-8")


# --- 汇总器：接受与产物 -------------------------------------------------------


def test_aggregate_accepts_valid_export(tmp_path):
    inputs, out = tmp_path / "in", tmp_path / "out"
    inputs.mkdir()
    (inputs / "p1.json").write_text(json.dumps(_base_export()), encoding="utf-8")
    summary = aggregator.aggregate(inputs, out)
    assert summary["participant_count"] == 1
    assert summary["task_row_count"] == 1
    assert summary["generation_row_count"] == 2
    assert summary["model_id"] == ["gpt-4o-mini"]
    assert summary["q_scoring"]["computed_here"] is False
    for artifact in ("participants.csv", "tasks.csv", "generations.csv"):
        assert (out / artifact).read_bytes().startswith(b"\xef\xbb\xbf")


def test_tasks_csv_has_empty_q_placeholder_columns(tmp_path):
    inputs, out = tmp_path / "in", tmp_path / "out"
    inputs.mkdir()
    (inputs / "p1.json").write_text(json.dumps(_base_export()), encoding="utf-8")
    aggregator.aggregate(inputs, out)
    fields, rows = _read_csv(out / "tasks.csv")
    for column in aggregator.TASK_Q_PLACEHOLDER_COLUMNS:
        assert column in fields
        assert all(row[column] == "" for row in rows)


def test_generations_csv_parses_both_conditions(tmp_path):
    inputs, out = tmp_path / "in", tmp_path / "out"
    inputs.mkdir()
    (inputs / "p1.json").write_text(json.dumps(_base_export()), encoding="utf-8")
    aggregator.aggregate(inputs, out)
    fields, rows = _read_csv(out / "generations.csv")
    assert "output_text" in fields
    conditions = {row["condition"] for row in rows}
    assert conditions == {"slider", "own_prompt"}
    slider_row = next(r for r in rows if r["condition"] == "slider")
    own_row = next(r for r in rows if r["condition"] == "own_prompt")
    assert slider_row["stop_id"] == "s3"
    assert slider_row["prompt_char_count"] == ""
    assert own_row["stop_id"] == ""
    assert int(own_row["prompt_char_count"]) > 0
    assert int(own_row["output_char_count"]) > 0
    assert own_row["output_text"]


def test_participants_csv_carries_model_id(tmp_path):
    inputs, out = tmp_path / "in", tmp_path / "out"
    inputs.mkdir()
    (inputs / "p1.json").write_text(json.dumps(_base_export()), encoding="utf-8")
    aggregator.aggregate(inputs, out)
    fields, rows = _read_csv(out / "participants.csv")
    assert "model_id" in fields
    assert rows[0]["model_id"] == "gpt-4o-mini"
    assert rows[0]["params_hash"] == "sha256:abcdef0123456789"


# --- 汇总器：去重 -------------------------------------------------------------


def test_aggregate_deduplicates_repeated_submission_id(tmp_path):
    inputs, out = tmp_path / "in", tmp_path / "out"
    inputs.mkdir()
    export = _base_export()
    (inputs / "a.json").write_text(json.dumps(export), encoding="utf-8")
    (inputs / "b.json").write_text(json.dumps(export), encoding="utf-8")
    summary = aggregator.aggregate(inputs, out)
    assert summary["participant_count"] == 1
    assert {item["file"] for item in summary["skipped_files"]} == {"b.json"}
    assert any("duplicate" in item["reason"] for item in summary["skipped_files"])


def test_aggregate_counts_distinct_ids_separately(tmp_path):
    inputs, out = tmp_path / "in", tmp_path / "out"
    inputs.mkdir()
    (inputs / "a.json").write_text(json.dumps(_base_export()), encoding="utf-8")
    (inputs / "b.json").write_text(json.dumps(_base_export()), encoding="utf-8")
    summary = aggregator.aggregate(inputs, out)
    assert summary["participant_count"] == 2
    assert summary["skipped_files"] == []


# --- 汇总器：拒绝 -------------------------------------------------------------


def test_aggregate_rejects_wrong_schema_and_signed(tmp_path):
    inputs, out = tmp_path / "in", tmp_path / "out"
    inputs.mkdir()
    signed = _base_export()
    signed["signed"] = True
    wrong = _base_export()
    wrong["export_schema"] = "microstudy-export-offline-studyB-v1"
    (inputs / "signed.json").write_text(json.dumps(signed), encoding="utf-8")
    (inputs / "wrong.json").write_text(json.dumps(wrong), encoding="utf-8")
    summary = aggregator.aggregate(inputs, out)
    assert summary["participant_count"] == 0
    assert {item["file"] for item in summary["skipped_files"]} == {"signed.json", "wrong.json"}


def test_aggregate_rejects_injected_answer_key(tmp_path):
    inputs, out = tmp_path / "in", tmp_path / "out"
    inputs.mkdir()
    export = _base_export()
    export["tasks"][0]["answer_key"] = "s3"
    (inputs / "leak.json").write_text(json.dumps(export), encoding="utf-8")
    summary = aggregator.aggregate(inputs, out)
    assert summary["participant_count"] == 0
    assert any("private key" in item["reason"] for item in summary["skipped_files"])


def test_aggregate_rejects_answer_key_in_generation(tmp_path):
    inputs, out = tmp_path / "in", tmp_path / "out"
    inputs.mkdir()
    export = _base_export()
    export["tasks"][0]["slider"]["generations"][0]["correct_answer"] = "s3"
    (inputs / "leak.json").write_text(json.dumps(export), encoding="utf-8")
    summary = aggregator.aggregate(inputs, out)
    assert summary["participant_count"] == 0
    assert any("private key" in item["reason"] for item in summary["skipped_files"])


def test_aggregate_rejects_container_smuggled_into_scalar_field(tmp_path):
    inputs, out = tmp_path / "in", tmp_path / "out"
    inputs.mkdir()
    dict_leak = _base_export()
    dict_leak["covariates"]["self_rating"] = {"winner": "s3"}
    (inputs / "dict_leak.json").write_text(json.dumps(dict_leak), encoding="utf-8")
    list_leak = _base_export()
    list_leak["convenience"]["willingness_choice"] = ["own_prompt", "s3"]
    (inputs / "list_leak.json").write_text(json.dumps(list_leak), encoding="utf-8")
    summary = aggregator.aggregate(inputs, out)
    assert summary["participant_count"] == 0
    assert {item["file"] for item in summary["skipped_files"]} == {"dict_leak.json", "list_leak.json"}
    assert all("scalar value" in item["reason"] for item in summary["skipped_files"])


def test_aggregate_rejects_bad_generation_shape(tmp_path):
    inputs, out = tmp_path / "in", tmp_path / "out"
    inputs.mkdir()
    export = _base_export()
    export["tasks"][0]["own_prompt"]["generations"][0]["output_text"] = 123  # not text
    (inputs / "bad.json").write_text(json.dumps(export), encoding="utf-8")
    summary = aggregator.aggregate(inputs, out)
    assert summary["participant_count"] == 0
    assert any("output_text" in item["reason"] for item in summary["skipped_files"])


def test_aggregate_rejects_complete_without_generation(tmp_path):
    inputs, out = tmp_path / "in", tmp_path / "out"
    inputs.mkdir()
    export = _base_export()
    export["tasks"][0]["slider"]["generations"] = []
    (inputs / "nogen.json").write_text(json.dumps(export), encoding="utf-8")
    summary = aggregator.aggregate(inputs, out)
    assert summary["participant_count"] == 0
    assert any("generation" in item["reason"] for item in summary["skipped_files"])


def test_aggregate_rejects_complete_without_model_id(tmp_path):
    inputs, out = tmp_path / "in", tmp_path / "out"
    inputs.mkdir()
    export = _base_export()
    export["model_id"] = None
    (inputs / "nomodel.json").write_text(json.dumps(export), encoding="utf-8")
    summary = aggregator.aggregate(inputs, out)
    assert summary["participant_count"] == 0
    assert any("model_id" in item["reason"] for item in summary["skipped_files"])


def test_aggregate_accepts_partial(tmp_path):
    inputs, out = tmp_path / "in", tmp_path / "out"
    inputs.mkdir()
    (inputs / "partial.json").write_text(json.dumps(_base_export(complete=False)), encoding="utf-8")
    summary = aggregator.aggregate(inputs, out)
    assert summary["participant_count"] == 1
    _, rows = _read_csv(out / "participants.csv")
    assert rows[0]["completion_status"] == "partial"


def test_aggregate_rejects_reintroduced_offline_slider_field(tmp_path):
    inputs, out = tmp_path / "in", tmp_path / "out"
    inputs.mkdir()
    export = _base_export()
    export["tasks"][0]["slider"]["final_setting"] = "s3"  # offline-only field
    (inputs / "old.json").write_text(json.dumps(export), encoding="utf-8")
    summary = aggregator.aggregate(inputs, out)
    assert summary["participant_count"] == 0
    assert any("slider fields mismatch" in item["reason"] for item in summary["skipped_files"])


# --- 桥接：组装 / 白名单 / 公平性 / 绑定 --------------------------------------


def test_bridge_binds_loopback_only():
    assert bridge.DEFAULT_HOST == "127.0.0.1"
    # main 不暴露 --host，强制回环；确认常量未被改成 0.0.0.0。
    assert bridge.DEFAULT_HOST != "0.0.0.0"


def test_bridge_slider_uses_frozen_preset_and_neutral_context():
    messages = bridge.assemble_messages("slider", "draftA-recipe-blurb", "s5", None)
    user = messages[-1]["content"]
    preset = bridge.FROZEN_TASKS["draftA-recipe-blurb"]["presets"]["s5"]
    assert preset in user
    # 中性 model_context 也在（两条件对称共享）。
    assert bridge.FROZEN_TASKS["draftA-recipe-blurb"]["model_context"] in user
    # 旧的含成功条件的 brief 键已移除（修 A）。
    assert "brief" not in bridge.FROZEN_TASKS["draftA-recipe-blurb"]
    assert "base_material" not in bridge.FROZEN_TASKS["draftA-recipe-blurb"]


def test_bridge_own_prompt_uses_participant_prompt():
    messages = bridge.assemble_messages(
        "own_prompt", "draftA-recipe-blurb", None, "Make it warm and short."
    )
    user = messages[-1]["content"]
    assert "Make it warm and short." in user
    # 参与者条件不注入任何滑块预设文本。
    for preset in bridge.FROZEN_TASKS["draftA-recipe-blurb"]["presets"].values():
        assert preset not in user


# 任务成功条件（participant_goal）字样 —— 绝不应出现在任何送模型的 slider/context 输入里。
SUCCESS_CONDITION_SUBSTRINGS = (
    "40",
    "word",
    "vegan",
    "exclamation",
    "friendly",
    "under",
    "纯素",
    "感叹",
    "友好",
    "字",
)


def test_bridge_presets_do_not_encode_task_success_conditions():
    """公平性硬约束：预设只做风格位移，绝不含任务成功条件字样。"""
    for stop_id, preset in bridge.FROZEN_TASKS["draftA-recipe-blurb"]["presets"].items():
        low = preset.lower()
        for bad in SUCCESS_CONDITION_SUBSTRINGS:
            assert bad not in low, f"preset {stop_id} leaks success condition: {bad!r}"


def test_bridge_model_context_has_no_success_conditions():
    """修 A：中性 model_context 不含任何任务成功条件字样。"""
    low = bridge.FROZEN_TASKS["draftA-recipe-blurb"]["model_context"].lower()
    for bad in SUCCESS_CONDITION_SUBSTRINGS:
        assert bad not in low, f"model_context leaks success condition: {bad!r}"


def test_bridge_slider_message_never_contains_success_conditions():
    """修 A（构念效度 BLOCKER）：SLIDER 组装出的最终 model message 不含成功条件字样。"""
    for stop_id in bridge.FROZEN_TASKS["draftA-recipe-blurb"]["presets"]:
        messages = bridge.assemble_messages("slider", "draftA-recipe-blurb", stop_id, None)
        blob = json.dumps(messages, ensure_ascii=False).lower()
        for bad in SUCCESS_CONDITION_SUBSTRINGS:
            assert bad not in blob, f"slider[{stop_id}] model message leaks: {bad!r}"


def test_participant_goal_text_not_auto_fed_to_model():
    """修 A：generator 的 participant_goal（goal + requirements）文本不出现在 SLIDER 模型输入。

    只有当参与者把成功条件写进 own_prompt 时才应进入模型（下面单独验证）。
    """
    task = next(t for t in generator.TASKS if t["task_id"] == "draftA-recipe-blurb")
    goal_texts = [task["goal"]["en"], task["goal"]["zh-Hans"]]
    for req in task["requirements"]:
        goal_texts += [req["en"], req["zh-Hans"]]
    for stop_id in bridge.FROZEN_TASKS["draftA-recipe-blurb"]["presets"]:
        messages = bridge.assemble_messages("slider", "draftA-recipe-blurb", stop_id, None)
        blob = json.dumps(messages, ensure_ascii=False)
        for goal in goal_texts:
            assert goal not in blob


def test_own_prompt_can_carry_participant_success_conditions():
    """自写条件：成功条件仅当参与者自己写入 prompt 时才进入模型（这是研究对象，正确）。"""
    participant_prompt = "Make sure to say it is vegan and keep it under 40 words."
    messages = bridge.assemble_messages(
        "own_prompt", "draftA-recipe-blurb", None, participant_prompt
    )
    assert participant_prompt in messages[-1]["content"]




def test_bridge_rejects_unknown_model():
    try:
        bridge.validate_request(
            {"condition": "slider", "task_id": "draftA-recipe-blurb", "stop_id": "s1", "model_id": "gpt-4-turbo"}
        )
        assert False, "should have rejected non-whitelisted model"
    except bridge.RequestError as error:
        assert "whitelist" in str(error)


def test_bridge_rejects_unknown_task_and_stop():
    for bad in (
        {"condition": "slider", "task_id": "nope", "stop_id": "s1"},
        {"condition": "slider", "task_id": "draftA-recipe-blurb", "stop_id": "s99"},
        {"condition": "own_prompt", "task_id": "draftA-recipe-blurb", "prompt_text": "  "},
        {"condition": "banana", "task_id": "draftA-recipe-blurb"},
    ):
        try:
            bridge.validate_request(bad)
            assert False, f"should have rejected {bad}"
        except bridge.RequestError:
            pass


def test_bridge_endpoint_with_stub_forward():
    """generate_endpoint 用本地 stub 替换转发；不真打 8313。"""
    captured = {}

    def stub(messages, model_id):
        captured["messages"] = messages
        captured["model_id"] = model_id
        return "STUB OUTPUT"

    result = bridge.generate_endpoint(
        {"condition": "slider", "task_id": "draftA-recipe-blurb", "stop_id": "s2"},
        forward=stub,
    )
    assert result["output_text"] == "STUB OUTPUT"
    assert result["model_id"] == "gpt-4o-mini"
    assert result["params_hash"].startswith("sha256:")
    assert result["bridge_version"] == bridge.BRIDGE_VERSION
    assert captured["model_id"] == "gpt-4o-mini"


def test_bridge_params_hash_stable_and_frozen():
    assert bridge.params_hash("gpt-4o-mini") == bridge.params_hash("gpt-4o-mini")
    assert bridge.FROZEN_TEMPERATURE == 0
    assert bridge.FROZEN_MAX_TOKENS == 512
