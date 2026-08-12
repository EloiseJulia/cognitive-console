import json
import math

import pytest

from cognitive_console.eval import c2b_tasks
from cognitive_console.experiments import resolution_refinement as rr
from cognitive_console.ops.hardware_profiles import (
    A800_80GB_PROFILE,
    validate_hardware_profile,
)
from scripts import run_c2b_resolution_refinement as runner


def test_all_frozen_cell_power_targets_match_registered_formula():
    expected = {
        ("caa", "qwen2.5-7b", "skepticism"): 566,
        ("caa", "qwen2.5-7b", "uncertainty_awareness"): 813,
        ("caa", "meta-llama-3-8b", "skepticism"): 1152,
        ("caa", "meta-llama-3-8b", "uncertainty_awareness"): 48,
        ("iti", "qwen2.5-7b", "skepticism"): 808,
        ("iti", "qwen2.5-7b", "uncertainty_awareness"): 46,
        ("iti", "meta-llama-3-8b", "skepticism"): 1246,
        ("iti", "meta-llama-3-8b", "uncertainty_awareness"): 45,
    }
    for row in rr.FROZEN_CELL_POWER:
        key = (row.method, row.model, row.axis)
        assert row.target_test_n == expected[key]
        assert row.per_item_sd == pytest.approx(
            row.se_estimate * math.sqrt(row.n_current_test)
        )


def test_primary_plan_caps_skepticism_and_hits_uncertainty_target():
    assert rr.selected_total_n_by_axis() == {
        "skepticism": 757,
        "uncertainty_awareness": 1219,
    }
    assert rr.achieved_test_n_by_axis() == {
        "skepticism": 505,
        "uncertainty_awareness": 813,
    }
    achieved = rr.achieved_mde_by_axis()
    assert achieved["skepticism"] == pytest.approx(0.05291, abs=1e-5)
    assert achieved["uncertainty_awareness"] <= 0.05


def test_disjoint_sampling_is_deterministic_and_excludes_frozen_ids():
    items = [{"id": f"truthfulqa-mc1-{i:05d}"} for i in range(817)]
    a = rr.select_disjoint_items(
        items,
        excluded_ids=rr.frozen_excluded_ids("skepticism"),
        n_total=757,
        seed=rr.SEED,
    )
    b = rr.select_disjoint_items(
        items,
        excluded_ids=rr.frozen_excluded_ids("skepticism"),
        n_total=757,
        seed=rr.SEED,
    )
    ids = [row["id"] for row in a]
    assert ids == [row["id"] for row in b]
    assert set(ids).isdisjoint(rr.frozen_excluded_ids("skepticism"))
    assert len(ids) == len(set(ids)) == 757


def test_real_loaders_pass_frozen_dataset_revisions(monkeypatch):
    calls = []

    class FakeDatasets:
        @staticmethod
        def load_dataset(dataset_id, config, split, revision):
            calls.append((dataset_id, config, split, revision))
            if dataset_id == "truthfulqa/truthful_qa":
                return [
                    {
                        "question": "Q?",
                        "mc1_targets": {
                            "choices": ["correct", "wrong"],
                            "labels": [1, 0],
                        },
                    }
                ]
            return [
                {
                    "question": "Q?",
                    "answer": {
                        "value": "A",
                        "aliases": ["A"],
                        "normalized_aliases": ["a"],
                    },
                }
            ]

    monkeypatch.setattr(c2b_tasks, "_require_datasets", lambda: FakeDatasets)
    assert len(c2b_tasks.load_skepticism_set()) == 1
    assert len(c2b_tasks.load_uncertainty_set()) == 1
    assert calls == [
        (
            "truthfulqa/truthful_qa",
            "multiple_choice",
            "validation",
            c2b_tasks.TRUTHFULQA_REVISION,
        ),
        (
            "mandarjoshi/trivia_qa",
            "rc.nocontext",
            "validation",
            c2b_tasks.TRIVIAQA_REVISION,
        ),
    ]


def test_a800_profile_accepts_a800_and_rejects_smaller_cards():
    accepted = validate_hardware_profile(
        A800_80GB_PROFILE,
        device_name="NVIDIA A800 80GB PCIe",
        total_vram_gib=79.1,
        free_vram_gib=70.0,
    )
    assert accepted["profile_sha256"] == A800_80GB_PROFILE.profile_sha256
    with pytest.raises(ValueError, match="unauthorized GPU"):
        validate_hardware_profile(
            A800_80GB_PROFILE,
            device_name="NVIDIA GeForce RTX 4090",
            total_vram_gib=24.0,
            free_vram_gib=23.0,
        )
    with pytest.raises(ValueError, match="smaller"):
        validate_hardware_profile(
            A800_80GB_PROFILE,
            device_name="NVIDIA A800",
            total_vram_gib=40.0,
            free_vram_gib=39.0,
        )


def test_synthetic_preflight_wires_power_and_sampling(tmp_path):
    out_dir = tmp_path / "preflight"
    assert runner.main(
        [
            "--phase",
            "preflight",
            "--backend",
            "synthetic",
            "--out-dir",
            str(out_dir),
        ]
    ) == 0
    payload = json.loads(
        (out_dir / "preflight" / "preflight.json").read_text(encoding="utf-8")
    )
    assert payload["scientific_status"] == "OPERATIONAL_ONLY_NOT_DEV_OR_TEST"
    assert payload["sampling"]["axes"]["skepticism"]["n_test"] == 505
    assert payload["sampling"]["axes"]["uncertainty_awareness"]["n_test"] == 813
    assert payload["power"]["primary"]["skepticism"]["achieved_mde"] > 0.05
    assert payload["power"]["primary"]["uncertainty_awareness"]["achieved_mde"] <= 0.05
