import copy
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

import cognitive_console.button_board_stepwise_materials as sw
from cognitive_console.button_board_stepwise.materials import (
    material_hashes,
    planned_trials,
    stable_option_order,
)


ROOT = Path(__file__).resolve().parents[1]


def test_v11_generator_validator_and_versions_are_exact():
    report = sw.validate_materials()
    assert report["status"] == "PASS"
    assert report["schema_version"] == "microstudy-button-board-stepwise-v11-bilingual"
    assert report["materials_version"] == "v11-stepwise-20260812-draft"
    assert report["export_schema_version"] == "microstudy-export-v7-stepwise-bilingual-signed"
    assert report["analysis_version"] == "button-board-stepwise-gaa-v1"
    assert report["formal_scene_count"] == 6
    checked = subprocess.run(
        [sys.executable, "scripts/generate_microstudy_v11_stepwise.py", "--check"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "current" in checked.stdout
    validated = subprocess.run(
        [sys.executable, "scripts/validate_button_board_stepwise_materials.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(validated.stdout)["status"] == "PASS"


def test_expected_path_exit_decisive_step_and_state_are_automatic():
    expected = {
        "P1": ("WITHHELD", 3, "NOT_BETTER"),
        "AB1-A": ("SUPPORTED", 6, "ab1-s-m4"),
        "AB1-B": ("WITHHELD", 3, "NOT_BETTER"),
        "F2": ("DIAGNOSTIC", 1, "INFO"),
        "F3": ("WITHHELD", 4, "HARM"),
        "F4": ("UNRESOLVED", 2, "NOT_COMPARED"),
        "F5": ("UNRESOLVED", 5, "SCOPE_MISSING"),
        "F6": ("SUPPORTED", 6, "f6-s-r6"),
    }
    for row in [sw.PRACTICE, *sw.FORMAL_SCENES]:
        derived = sw.derive_expected(row)
        assert (
            derived["expected_state"],
            derived["expected_decisive_step"],
            derived["expected_exit_answer"],
        ) == expected[row["scene_id"]]
        assert sw.route_participant(
            [
                {"step": int(step), "answer": answer}
                for step, answer in derived["expected_answer_by_step"].items()
            ]
        )["state"] == derived["expected_state"]
        assert not {
            "expected_answer_by_step",
            "expected_exit_answer",
            "expected_decisive_step",
            "expected_state",
            "compared",
            "better",
            "harm",
            "scope_written",
            "scope_correct",
        } & set(row)


def test_unified_method_schema_covers_paired_single_and_information_items():
    for row in [sw.PRACTICE, *sw.FORMAL_SCENES]:
        rule = row["comparison_rule"]
        assert set(rule["methods"]) == {"existing", "new"}
        for method in rule["methods"].values():
            assert set(method) == {"rounds", "denominator", "successes"}
    f4 = sw.derive_expected(sw.F4)
    assert f4["comparison_rule"]["design"] == "single_method_record"
    assert f4["comparison_rule"]["methods"]["existing"] == {
        "rounds": 0,
        "denominator": 0,
        "successes": None,
    }
    assert f4["comparison_rule"]["methods"]["new"] == {
        "rounds": 10,
        "denominator": 10,
        "successes": 8,
    }
    assert f4["compared"] is False
    assert f4["better"] is None
    assert f4["expected_answer_by_step"] == {"1": "CONTROL", "2": "NOT_COMPARED"}
    f2 = sw.derive_expected(sw.F2)
    assert f2["compared"] is None and f2["better"] is None


def test_typed_fact_registry_is_the_card_and_structured_field_source(monkeypatch):
    for row in [sw.PRACTICE, *sw.FORMAL_SCENES]:
        sw._validate_fact_consistency(row)
        facts = sw._fact_rows(row)
        for locale in sw.LOCALES:
            public = sw._public_scene(row, locale)
            assert public["card"]["facts"] == [fact["text"][locale] for fact in facts]
            card = " ".join(public["card"]["facts"])
            for alignment in row["comparison_rule"]["alignment_dimensions"]:
                assert alignment["label"][locale] in card
            for dimension in row["scope_dimensions"]:
                assert dimension["value"][locale] in card

    original = sw._public_scene

    def divergent(row, locale):
        value = original(row, locale)
        if row["scene_id"] == "F4":
            value["card"]["facts"][1] = "divergent"
        return value

    monkeypatch.setattr(sw, "_public_scene", divergent)
    with pytest.raises(ValueError, match="card and fact registry diverged"):
        sw.validate_materials(require_files_current=False)


def test_scope_options_have_bilingual_parity_equal_lengths_and_one_dimension_difference():
    for row in [sw.PRACTICE, *sw.FORMAL_SCENES]:
        sw._validate_scope_options(row)
        vectors = sw._scope_vectors(row)
        fields = sw.derive_structured_fields(row)
        correct = next(option for option in vectors if option["id"] == fields["scope_correct"])
        for option in vectors:
            assert list(option["vector"]) == [
                dimension["id"] for dimension in row["scope_dimensions"]
            ]
            distance = sum(
                option["vector"][key]["value_id"] != correct["vector"][key]["value_id"]
                for key in correct["vector"]
            )
            assert distance == (0 if option["id"] == correct["id"] else 1)
        en = sw._scope_public(row, "en")
        zh = sw._scope_public(row, "zh-Hans")
        assert [option["id"] for option in en] == [option["id"] for option in zh]
        assert len({len(sw._english_words(option["text"])) for option in en}) == 1
        zh_lengths = [len(sw._normalize_zh(option["text"])) for option in zh]
        assert max(zh_lengths) - min(zh_lengths) <= 1
        assert len({len(option["segments"]) for option in en + zh}) == 1


def test_ab1_diff_is_success_counts_only_and_each_attempt_has_one_variant():
    assert len(sw.ab_invariance_hash()) == 64
    left = copy.deepcopy(sw.AB1_A)
    right = copy.deepcopy(sw.AB1_B)
    assert left["title"] == right["title"]
    assert left["scope_options"] == right["scope_options"]
    for row in (left, right):
        row.pop("scene_id")
        row.pop("variant_id")
        for method in row["comparison_rule"]["methods"].values():
            method.pop("successes")
    assert left == right
    changed = copy.deepcopy(sw.AB1_B)
    changed["goal"] = sw.bi("Changed.", "改变。")
    original = sw.AB1_B
    try:
        sw.AB1_B = changed
        with pytest.raises(ValueError, match="non-manipulated"):
            sw.ab_invariance_hash()
    finally:
        sw.AB1_B = original
    for variant in ("A", "B"):
        plan = planned_trials("BBS11-01", variant, f"P-{variant}")
        ids = {row["scene_id"] for row in plan}
        assert f"AB1-{variant}" in ids
        assert not {"AB1-A", "AB1-B"} <= ids
        assert len(plan) == 6


def test_sequences_balance_scene_positions_and_success_allocation_cells():
    sequences = sw.generate_sequences()["sequences"]
    cells = Counter()
    for sequence in sequences:
        assert {row["scene_slot"] for row in sequence["slots"]} == set(sw.FORMAL_SLOTS)
        for slot in sequence["slots"]:
            cells[slot["scene_slot"], slot["position"]] += 1
    assert set(cells.values()) == {2}
    allocations = [
        (f"BBS11-{cell // 2 + 1:02d}", "A" if cell % 2 == 0 else "B")
        for cell in range(24)
    ]
    assert Counter(sequence for sequence, _ in allocations) == {
        f"BBS11-{index:02d}": 2 for index in range(1, 13)
    }
    assert Counter(variant for _, variant in allocations) == {"A": 12, "B": 12}


def test_scope_order_is_stable_and_participant_specific():
    materials, _, _ = sw.load_sources()
    rows = materials["locales"]["en"]["scenes"]["F6"]["scope_options"]
    first = stable_option_order(rows, "P-ONE", "F6", "hash", "scope")
    second = stable_option_order(rows, "P-ONE", "F6", "hash", "scope")
    assert first == second
    orders = {
        tuple(
            row["id"]
            for row in stable_option_order(
                rows, f"P-{index}", "F6", "hash", "scope"
            )
        )
        for index in range(12)
    }
    assert len(orders) > 1


def test_public_materials_have_no_private_or_score_keys_and_are_bilingual():
    materials, _, keys = sw.load_sources()
    text = json.dumps(materials, ensure_ascii=False)
    for forbidden in (
        "expected_answer_by_step",
        "expected_exit_answer",
        "expected_decisive_step",
        "expected_state",
        "comparison_rule",
        "required_readings",
        "required_scope_dimensions",
        "scope_correct",
        "scope_written",
        "gaa_correct",
        "strict_correct",
    ):
        assert f'"{forbidden}"' not in text
    for locale in sw.LOCALES:
        bundle = materials["locales"][locale]
        assert set(bundle["scenes"]) == set(sw.FORMAL_SCENE_IDS)
        assert len(bundle["common"]["destinations"]) == 4
        assert len(bundle["common"]["checklist"]) == 6
        assert set(bundle["common"]["questions"]) == {str(step) for step in range(1, 7)}
    assert keys["scenes"]["F4"]["comparison_rule"]["design"] == "single_method_record"


def test_neutral_record_and_ambiguity_scans_fail_closed():
    materials, _ = sw.generate_materials()
    sw._validate_neutral_text(materials)
    leaked = copy.deepcopy(materials)
    leaked["locales"]["zh-Hans"]["scenes"]["F6"]["card"]["facts"][0] += " 智能"
    with pytest.raises(ValueError, match="ambiguous or conclusion"):
        sw._validate_neutral_text(leaked)
    leaked = copy.deepcopy(materials)
    leaked["locales"]["en"]["scenes"]["F3"]["card"]["facts"][0] += " supported"
    with pytest.raises(ValueError, match="ambiguous or conclusion"):
        sw._validate_neutral_text(leaked)


def test_material_hashes_cover_public_sequences_and_private_derivation():
    hashes = material_hashes()
    assert set(hashes) == {
        "canonical_materials_hash",
        "sequences_hash",
        "derived_keys_hash",
    }
    assert hashes["canonical_materials_hash"] == hashlib.sha256(
        sw.MATERIALS_PATH.read_bytes()
    ).hexdigest()
    assert len(set(hashes.values())) == 3
