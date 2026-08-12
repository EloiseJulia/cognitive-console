import copy
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

import cognitive_console.button_board_materials as bb
from cognitive_console.button_board.materials import (
    material_hashes,
    planned_trials,
    stable_option_order,
)


ROOT = Path(__file__).resolve().parents[1]


def test_v10_generator_validator_and_versions_are_exact():
    report = bb.validate_materials()
    assert report["status"] == "PASS"
    assert report["schema_version"] == "microstudy-button-board-v10-bilingual"
    assert report["materials_version"] == "v10-button-board-20260812-draft"
    assert (
        report["export_schema_version"]
        == "microstudy-export-v6-button-board-bilingual-signed"
    )
    assert report["analysis_version"] == "button-board-gaa-v2"
    assert report["formal_scene_count"] == 6
    assert report["variant_scene_count"] == 2
    assert report["scope_gate_scenes"] == ["F1", "F6", "F7"]
    checked = subprocess.run(
        [sys.executable, "scripts/generate_microstudy_v10.py", "--check"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "current" in checked.stdout
    validated = subprocess.run(
        [sys.executable, "scripts/validate_button_board_materials.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(validated.stdout)["status"] == "PASS"


def test_router_and_reason_keys_are_derived_only_from_structured_fields():
    expected = {
        "P1": ("Q1_DIAGNOSTIC", "READ_WITHOUT_CONTROL_COMPARISON"),
        "F1": ("Q1_SUPPORTED", "POSITIVE_SAFE_SCOPED"),
        "F2": ("Q1_WITHHELD", "RESOLVED_NO_SUPERIORITY"),
        "F3": ("Q1_DIAGNOSTIC", "READ_WITHOUT_CONTROL_COMPARISON"),
        "F4": ("Q1_WITHHELD", "COHERENCE_FAIL"),
        "F5": ("Q1_UNRESOLVED", "COMPARISON_UNCLEAR"),
        "F6": ("Q1_UNRESOLVED", "POSITIVE_SCOPE_UNSPECIFIED"),
        "F7": ("Q1_SUPPORTED", "POSITIVE_SAFE_SCOPED"),
    }
    for scene in [bb.PRACTICE, *bb.FORMAL_SCENES]:
        derived = bb.derive_scene_keys(scene)
        assert (derived["q1_state"], derived["reason_class"]) == expected[
            scene["scene_id"]
        ]
        changed = copy.deepcopy(scene)
        changed["title"] = bb.bi("Changed non-key title", "改变的非键标题")
        changed["record"]["situation"] = bb.bi("Changed situation.", "改变的情境。")
        assert bb.derive_scene_keys(changed) == derived
    assert all(
        "expected" not in key.lower()
        for scene in [bb.PRACTICE, *bb.FORMAL_SCENES]
        for key in scene
    )
    public = bb.MATERIALS_PATH.read_text(encoding="utf-8")
    for private in (
        "correct_reason_id",
        "correct_scope_id",
        "q1_state",
        "paper_state",
        "reason_class",
        "scope_gate_required",
        "decisive_positive",
        "quality_status",
    ):
        assert private not in public


def test_router_priority_and_frozen_route_coverage():
    assert bb.derive_q1_state(
        {
            "read_status": "usable",
            "comparison": "decisive_positive",
            "quality_status": "pass",
            "scope_status": "exact",
        }
    ) == "Q1_SUPPORTED"
    assert bb.derive_q1_state(
        {
            "read_status": "usable",
            "comparison": "decisive_positive",
            "quality_status": "pass",
            "scope_status": "scope_missing",
        }
    ) == "Q1_UNRESOLVED"
    assert bb.derive_q1_state(
        {
            "read_status": "usable",
            "comparison": "decisive_negative",
            "quality_status": "pass",
            "scope_status": "exact",
        }
    ) == "Q1_WITHHELD"
    assert bb.derive_q1_state(
        {
            "read_status": "usable",
            "comparison": "missing",
            "quality_status": "pass",
            "scope_status": "exact",
        }
    ) == "Q1_DIAGNOSTIC"
    assert bb.derive_q1_state(
        {
            "read_status": "usable",
            "comparison": "mixed",
            "quality_status": "pass",
            "scope_status": "exact",
        }
    ) == "Q1_UNRESOLVED"
    assert bb.derive_q1_state(
        {
            "read_status": "usable",
            "comparison": "decisive_positive",
            "quality_status": "fail",
            "scope_status": "exact",
        }
    ) == "Q1_WITHHELD"


def test_f1_f2_invariance_and_single_field_manipulation_fail_closed(monkeypatch):
    original = bb.ab_invariance_hash()
    assert len(original) == 64
    assert bb.F1["title"] == bb.F2["title"]
    assert bb.F1["reason_options"] == bb.F2["reason_options"]
    assert bb.F1["scope_options"] == bb.F2["scope_options"]
    assert (
        bb.F1["paired_comparison"]["raw_counts"]
        != bb.F2["paired_comparison"]["raw_counts"]
    )
    changed = copy.deepcopy(bb.F2)
    changed["record"]["effects"] = bb.bi("Changed effect.", "改变的影响。")
    monkeypatch.setattr(bb, "F2", changed)
    with pytest.raises(ValueError, match="non-manipulated"):
        bb.ab_invariance_hash()


def test_public_materials_are_neutral_fictional_and_bilingual_stable_id_parity():
    materials, _, keys = bb.load_sources()
    assert materials["locale_contract"]["fallback"] is None
    assert materials["locale_contract"]["auto_detect"] is False
    assert materials["locale_contract"]["selected_locale_locked"] is True
    for locale in bb.LOCALES:
        bundle = materials["locales"][locale]
        assert bundle["common"]["disclaimer"] == bb.DISCLAIMER[locale]
        assert [row["id"] for row in bundle["common"]["q1_options"]] == list(
            bb.Q1_PUBLIC_IDS.values()
        )
        assert set(bundle["scenes"]) == set(bb.FORMAL_SCENE_IDS)
        for scene_id, scene in bundle["scenes"].items():
            assert set(scene["record"]) == {
                "situation",
                "goal",
                "existing",
                "new_item",
                "respond",
                "comparison",
                "amount",
                "effects",
                "conditions",
            }
            assert len(scene["scope_options"]) == 4
            assert len(scene["reason_options"]) == 4
            correct = keys["scenes"][scene_id]["correct_reason_id"]
            lengths = {row["id"]: len(row["text"]) for row in scene["reason_options"]}
            assert lengths[correct] < max(lengths.values())
            assert max(lengths.values()) / min(lengths.values()) <= 1.65
    assert (
        bb.locale_manifest(materials)["en"]["locale_bundle_hash"]
        != bb.locale_manifest(materials)["zh-Hans"]["locale_bundle_hash"]
    )


def test_teaching_practice_and_formal_leakage_scans_are_enforced(monkeypatch):
    materials, _ = bb.generate_materials()
    bb._validate_banned_text(materials)
    leaked = copy.deepcopy(materials)
    leaked["locales"]["en"]["scenes"]["F3"]["record"]["effects"] += " verdict"
    with pytest.raises(ValueError, match="formal record leakage"):
        bb._validate_banned_text(leaked)
    leaked = copy.deepcopy(materials)
    leaked["locales"]["zh-Hans"]["scenes"]["F4"]["reason_options"][0][
        "text"
    ] += " 常用区"
    with pytest.raises(ValueError, match="formal reason leakage"):
        bb._validate_banned_text(leaked)
    leaked = copy.deepcopy(materials)
    leaked["locales"]["en"]["common"]["tutorial"]["frame_2"] += " router"
    with pytest.raises(ValueError, match="tutorial router leakage"):
        bb._validate_banned_text(leaked)


def test_sequences_balance_order_q1_positions_and_ab_cells():
    sequences = bb.generate_sequences()["sequences"]
    assert [row["sequence_id"] for row in sequences] == [
        f"BB10-{index:02d}" for index in range(1, 13)
    ]
    scene_cells = Counter()
    q1_cells = Counter()
    for sequence in sequences:
        per_sequence = Counter()
        for slot in sequence["slots"]:
            scene_cells[slot["scene_slot"], slot["position"]] += 1
            for position, option_id in enumerate(slot["q1_order"], 1):
                q1_cells[option_id, position] += 1
                per_sequence[option_id, position] += 1
        for option_id in bb.Q1_PUBLIC_IDS.values():
            counts = [per_sequence[option_id, pos] for pos in range(1, 5)]
            assert max(counts) - min(counts) <= 1
    assert set(scene_cells.values()) == {2}
    assert set(q1_cells.values()) == {18}
    allocations = [
        (f"BB10-{cell // 2 + 1:02d}", "F1" if cell % 2 == 0 else "F2")
        for cell in range(24)
    ]
    assert Counter(sequence for sequence, _ in allocations) == {
        f"BB10-{index:02d}": 2 for index in range(1, 13)
    }
    assert Counter(variant for _, variant in allocations) == {"F1": 12, "F2": 12}


def test_plans_are_variant_isolated_and_option_order_is_stable():
    f1 = planned_trials("BB10-01", "F1", "P-ORDER")
    f2 = planned_trials("BB10-01", "F2", "P-ORDER")
    assert len(f1) == len(f2) == 6
    assert {row["scene_id"] for row in f1} == {"F1", "F3", "F4", "F5", "F6", "F7"}
    assert {row["scene_id"] for row in f2} == {"F2", "F3", "F4", "F5", "F6", "F7"}
    assert not ({"F1", "F2"} <= {row["scene_id"] for row in f1})
    materials, _, _ = bb.load_sources()
    rows = materials["locales"]["en"]["scenes"]["F7"]["reason_options"]
    first = stable_option_order(rows, "P-ORDER", "F7", "abc", "reason")
    second = stable_option_order(rows, "P-ORDER", "F7", "abc", "reason")
    assert first == second
    assert [row["id"] for row in first] != [
        row["id"]
        for row in stable_option_order(rows, "P-OTHER", "F7", "abc", "reason")
    ]


def test_material_hashes_cover_public_sequences_and_private_derivation():
    hashes = material_hashes()
    assert set(hashes) == {
        "canonical_materials_hash",
        "sequences_hash",
        "derived_keys_hash",
    }
    assert hashes["canonical_materials_hash"] == hashlib.sha256(
        bb.MATERIALS_PATH.read_bytes()
    ).hexdigest()
    assert len(set(hashes.values())) == 3
