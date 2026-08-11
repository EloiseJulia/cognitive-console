import hashlib
import json
import subprocess
import sys
from pathlib import Path

from cognitive_console.microstudy_materials import (
    SEQUENCES_PATH,
    STIMULI_PATH,
    canonical_locale_bytes,
    exact_binomial_upper_tail,
    load_sources,
    locale_manifest,
    route_state,
    validate_materials,
)


REPO = Path(__file__).resolve().parent.parent


def test_authoritative_sources_validate_with_bilingual_manifest():
    report = validate_materials()
    assert report["status"] == "PASS"
    assert report["schema_version"] == "microstudy-stimuli-v8-bilingual-novice-ux"
    assert report["template_reuse"] == {
        "Q2-NEXT": 4,
        "Q2-BASELINE": 4,
        "Q2-COVERAGE": 2,
    }
    assert report["key_distribution"] == {"A": 2, "B": 2, "C": 3, "D": 3}
    assert report["sequence_count"] == 20
    assert report["trial_row_count"] == 200
    assert report["locale_leakage_counts"] == {
        locale: {
            "equal_length": 2,
            "negation_marker": 3,
            "modal_marker": 2,
            "initial_lexical": 2,
        }
        for locale in ("en", "zh-Hans")
    }


def test_locale_tree_is_complete_no_fallback_and_canonical_hashes():
    stimuli, _ = load_sources()
    contract = stimuli["locale_contract"]
    assert contract["supported"] == ["en", "zh-Hans"]
    assert contract["fallback"] is None
    assert contract["auto_detect"] is False
    assert contract["stable_id_parity"] is True
    manifest = locale_manifest(stimuli)
    for locale in contract["supported"]:
        assert manifest[locale]["locale_bundle_hash"] == hashlib.sha256(
            canonical_locale_bytes(stimuli["locales"][locale])
        ).hexdigest()
        assert manifest[locale]["locale_bundle_version"].endswith(locale)
    assert manifest["en"]["locale_bundle_hash"] != manifest["zh-Hans"]["locale_bundle_hash"]


def test_frozen_leakage_and_router_metrics():
    metrics = validate_materials()["metrics"]
    expected = {
        "oracle_template": 3,
        "loo_template": 0,
        "global_position": 3,
        "equal_length": 2,
        "negation_marker": 3,
        "modal_marker": 2,
        "read_lexical": 2,
        "single_row_q1": 8,
        "combined_oracle_cca": 2,
        "combined_loo_cca": 0,
        "router": 10,
    }
    assert {name: row["correct"] for name, row in metrics.items()} == expected
    for name, row in metrics.items():
        if name not in {"single_row_q1", "router"}:
            assert row["binomial_p_upper_vs_0_25"] >= 0.05


def test_exact_binomial_values():
    assert exact_binomial_upper_tail(3, 10) == 0.4744071960449219
    assert exact_binomial_upper_tail(2, 10) == 0.7559747695922852
    assert exact_binomial_upper_tail(0, 10) == 1.0


def test_p3_y_q2_requests_missing_scope_without_changing_q1():
    stimuli, _ = load_sources()
    item = next(
        item
        for item in stimuli["nonlocalized"]["items"]
        if item["stimulus_id"] == "MS-P3-Y"
    )
    template = next(
        template
        for template in stimuli["locales"]["en"]["formal"]["q2_templates"]
        if template["id"] == item["q2"]["template_id"]
    )
    localized_item = next(
        row
        for row in stimuli["locales"]["en"]["formal"]["items"]
        if row["id"] == "MS-P3-Y"
    )
    assert item["q2"] == {"template_id": "Q2-NEXT", "correct_key": "C"}
    assert "applicability boundary" in template["options"][2]["text"]
    assert "unavailable" in localized_item["primitive_evidence"]["scope"]
    assert route_state(item["state_routing_inputs"]) == "Q1_WITHHELD"


def test_transfer_pass_uses_positive_ci_and_point_estimate_margin():
    base = {
        "tier": "S1",
        "evaluation_tier": "S1",
        "read_status": "supported",
        "comparison": {
            "tested": True,
            "estimate": 0.1,
            "ci_low": 0.001,
            "ci_high": 0.2,
            "registered_margin": 0.1,
        },
        "coherence_status": "pass",
    }
    assert route_state(base) == "Q1_SUPPORTED"
    touches_zero = json.loads(json.dumps(base))
    touches_zero["comparison"]["ci_low"] = 0.0
    assert route_state(touches_zero) == "Q1_UNRESOLVED"
    below_margin = json.loads(json.dumps(base))
    below_margin["comparison"]["estimate"] = 0.1 - 1e-12
    assert route_state(below_margin) == "Q1_WITHHELD"


def test_contract_labels_are_plain_semantic_and_academic_labels_are_absent():
    stimuli, _ = load_sources()
    en = stimuli["locales"]["en"]
    zh = stimuli["locales"]["zh-Hans"]
    assert en["formal"]["contract_labels"] == {
        "representation": "Initial check",
        "comparison": "Paired comparison",
        "comparator": "Reference setup",
        "coherence": "Consistency check",
        "scope": "Applicable setting",
    }
    assert zh["formal"]["contract_labels"] == {
        "representation": "初始检查",
        "comparison": "配对比较",
        "comparator": "参照设置",
        "coherence": "一致性检查",
        "scope": "适用情境",
    }
    assert en["formal"]["flat_labels"] == [f"Evidence {letter}" for letter in "ABCDE"]
    assert zh["formal"]["flat_labels"] == [f"证据 {letter}" for letter in "ABCDE"]
    for bundle, forbidden in (
        (en, (
            "READ", "TRANSFER", "BOUNDED PROMPT COMPARATOR",
            "CALIBRATION WARNING", "EVIDENCE TIER",
        )),
        (zh, ("初始读取", "迁移比较", "有界提示比较器", "校准警示", "证据层级")),
    ):
        participant_copy = json.dumps(bundle, ensure_ascii=False)
        assert not any(term in participant_copy for term in forbidden)


def test_single_safety_practice_is_five_rows_with_no_formal_pattern_mapping():
    stimuli, _ = load_sources()
    answers = stimuli["nonlocalized"]["answer_keys"]["practice"]
    assert answers == {"q1": "Q1_WITHHELD", "q2": "D"}
    practice_ids = stimuli["nonlocalized"]["practice_fact_ids"]
    assert set(practice_ids).isdisjoint(stimuli["nonlocalized"]["primitive_ids"])
    assert stimuli["nonlocalized"]["render_contract"]["practice_independence"][
        "formal_role_mapping"
    ] == "none"
    for locale in ("en", "zh-Hans"):
        practice = stimuli["locales"][locale]["practice"]
        encoded = json.dumps(practice, ensure_ascii=False).lower()
        assert [row["id"] for row in practice["facts"]] == practice_ids
        assert len(practice["facts"]) == 5
        assert len(practice["q1"]["options"]) == 4
        assert len(practice["q2"]["options"]) == 4
        assert "primitive_evidence" not in encoded
        for forbidden in (
            "interval", "margin", "tier", "model", "method", "evidence a",
            "transfer", "bounded prompt comparator", "calibration warning",
        ):
            assert forbidden not in encoded
    assert [row["body"] for row in stimuli["locales"]["en"]["practice"]["facts"]] == [
        "The room is requested for Saturday afternoon.",
        "The safety check is complete.",
        "A blocked emergency exit was found.",
        "Policy requires exits to remain clear while the room is in use.",
        "The result applies to this room and time: the room cannot be opened.",
    ]
    assert [row["body"] for row in stimuli["locales"]["zh-Hans"]["practice"]["facts"]] == [
        "有人申请周六下午使用该房间。",
        "安全检查已完成。",
        "检查发现紧急出口受阻。",
        "政策要求房间使用期间紧急出口保持畅通。",
        "结论适用于该房间和时段：房间不能开放。",
    ]


def test_novice_welcome_guard_state_distinction_and_q2_coverage_copy():
    stimuli, _ = load_sources()
    en = stimuli["locales"]["en"]
    zh = stimuli["locales"]["zh-Hans"]
    assert en["welcome"]["heading"] == "Five-fact decision task"
    assert zh["welcome"]["heading"] == "五条事实判断任务"
    assert en["welcome"]["subtitle"] == (
        "Read five facts, choose one status, then answer one follow-up question."
    )
    assert zh["welcome"]["subtitle"] == "阅读五条事实，选择一个状态，再回答一个跟进问题。"
    assert "1 practice record and 10 formal records" in en["welcome"]["task_size"]
    assert "not been timing-validated" in en["welcome"]["estimate"]
    assert "请勿填写姓名" in zh["welcome"]["participant_code_help"]
    assert "not an answer hint" in en["welcome"]["sequence_help"]
    assert "不能恢复" in zh["welcome"]["no_resume"]
    assert len(en["onboarding"]["steps"]) == len(zh["onboarding"]["steps"]) == 3
    assert "cannot yet tell" in en["onboarding"]["state_distinction"]
    assert "decision is not to support" in en["onboarding"]["state_distinction"]
    assert en["position_guard"] == (
        "Use all five facts; row order and Fact/Evidence labels are not clues."
    )
    assert zh["position_guard"] == "请结合全部五条事实；行顺序和事实/证据编号不是线索。"
    coverage_en = next(
        row for row in en["formal"]["q2_templates"] if row["id"] == "Q2-COVERAGE"
    )
    coverage_zh = next(
        row for row in zh["formal"]["q2_templates"] if row["id"] == "Q2-COVERAGE"
    )
    assert coverage_en["text"] == (
        "Which checks have completed, usable results in this record?"
    )
    assert coverage_zh["text"] == "这条记录中，哪些检查已有完成且可用的结果？"
    assert coverage_en["helper"] == "Usable does not mean positive."
    assert coverage_zh["helper"] == "“可用”不等于“结果为正”。"


def test_q1_q2_keys_and_noncoverage_templates_are_unchanged():
    stimuli, _ = load_sources()
    expected_q1 = {
        "MS-P1-X": "Q1_UNRESOLVED", "MS-P1-Y": "Q1_UNRESOLVED",
        "MS-P2-X": "Q1_DIAGNOSTIC", "MS-P2-Y": "Q1_DIAGNOSTIC",
        "MS-P3-X": "Q1_WITHHELD", "MS-P3-Y": "Q1_WITHHELD",
        "MS-P4-X": "Q1_UNRESOLVED", "MS-P4-Y": "Q1_UNRESOLVED",
        "MS-P5-X": "Q1_SUPPORTED", "MS-P5-Y": "Q1_SUPPORTED",
    }
    expected_q2 = {
        "MS-P1-X": "D", "MS-P1-Y": "A", "MS-P2-X": "B", "MS-P2-Y": "C",
        "MS-P3-X": "C", "MS-P3-Y": "C", "MS-P4-X": "A", "MS-P4-Y": "B",
        "MS-P5-X": "D", "MS-P5-Y": "D",
    }
    assert {
        item["stimulus_id"]: route_state(item["state_routing_inputs"])
        for item in stimuli["nonlocalized"]["items"]
    } == expected_q1
    assert {
        item["stimulus_id"]: item["q2"]["correct_key"]
        for item in stimuli["nonlocalized"]["items"]
    } == expected_q2
    templates = {
        row["id"]: row for row in stimuli["locales"]["en"]["formal"]["q2_templates"]
    }
    assert templates["Q2-NEXT"]["text"] == "What needs to be checked next?"
    assert templates["Q2-BASELINE"]["text"] == (
        "What does this record say about the reference?"
    )


def test_render_contract_is_selected_locale_and_semantic_attribute_safe():
    stimuli, _ = load_sources()
    render = stimuli["nonlocalized"]["render_contract"]
    assert render["conditions"]["contract"]["labels"] == (
        "selected locale formal.contract_labels"
    )
    assert render["conditions"]["flat"]["labels_by_position"] == (
        "selected locale formal.flat_labels"
    )
    assert render["dom"]["card"]["data_attributes"] == []
    assert render["dom"]["row"]["data_attributes"] == [
        "data-row-id", "data-position"
    ]
    assert render["parity_audit"]["geometry_tolerance_px"] == 1


def test_sources_are_json_and_cli_emits_report():
    assert STIMULI_PATH.suffix == ".json"
    assert SEQUENCES_PATH.suffix == ".json"
    completed = subprocess.run(
        [sys.executable, "scripts/validate_microstudy_materials.py"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(completed.stdout)["status"] == "PASS"


def test_no_attention_check_or_free_text_export_fields():
    stimuli, _ = load_sources()
    export = stimuli["nonlocalized"]["export_schema"]
    assert not any("attention" in field for field in export["session_fields"])
    assert export["free_text_fields"] == []
    assert {
        "ui_language", "locale_bundle_version", "locale_bundle_hash",
        "block_1_ease", "block_2_ease",
    } <= set(export["session_fields"])
