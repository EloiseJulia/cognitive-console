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
    assert report["schema_version"] == "microstudy-stimuli-v7-bilingual"
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


def test_contract_labels_are_formal_only_and_shared_copy_is_neutral():
    stimuli, _ = load_sources()
    en = stimuli["locales"]["en"]
    zh = stimuli["locales"]["zh-Hans"]
    assert en["formal"]["contract_labels"] == {
        "representation": "READ",
        "comparison": "TRANSFER",
        "comparator": "BOUNDED PROMPT COMPARATOR",
        "coherence": "CALIBRATION WARNING",
        "scope": "EVIDENCE TIER",
    }
    assert en["formal"]["flat_labels"] == [f"Evidence {letter}" for letter in "ABCDE"]
    assert zh["formal"]["flat_labels"] == [f"证据 {letter}" for letter in "ABCDE"]
    shared = json.dumps(
        {
            "onboarding": en["onboarding"],
            "practice": en["practice"],
            "q1": en["formal"]["q1"],
            "q2": en["formal"]["q2_templates"],
            "items": en["formal"]["items"],
        }
    ).lower()
    assert "transfer" not in shared
    assert "bounded prompt comparator" not in shared
    assert "calibration warning" not in shared
    assert "evidence tier" not in shared
    assert " read " not in f" {shared} "


def test_single_community_room_practice_has_locked_answers_and_no_formal_card():
    stimuli, _ = load_sources()
    answers = stimuli["nonlocalized"]["answer_keys"]["practice"]
    assert answers == {"q1": "Q1_WITHHELD", "q2": "D"}
    for locale in ("en", "zh-Hans"):
        practice = stimuli["locales"][locale]["practice"]
        encoded = json.dumps(practice, ensure_ascii=False).lower()
        assert len(practice["q1"]["options"]) == 4
        assert len(practice["q2"]["options"]) == 4
        assert "primitive_evidence" not in encoded
        for forbidden in (
            "interval", "margin", "tier", "model", "method", "evidence a",
            "read", "transfer",
        ):
            assert forbidden not in encoded


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
