"""Tests for the E-0012-SG settling-grid script."""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from cognitive_console.eval.e0012_triviaqa import E0012_SPLIT_SEED, load_e0012_pool
from cognitive_console.experiments.e0012_buttons import ButtonDirection
from cognitive_console.experiments.e0012_harness import K_STAGE1, split_e0012_pool


REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _runner():
    if "run_e0012_settling_grid" not in sys.modules:
        return importlib.import_module("run_e0012_settling_grid")
    return sys.modules["run_e0012_settling_grid"]


def test_condition_grid_has_exactly_six_frozen_cells():
    runner = _runner()
    conditions = runner.build_conditions(hidden_dim=16)
    assert len(conditions) == 6
    assert [(c.prompt_label, c.steering) for c in conditions] == [
        ("empty", "none"),
        ("empty", "probe_L18_a24"),
        ("CAL-09", "none"),
        ("CAL-09", "probe_L18_a24"),
        ("SYNTH-BANK-26", "none"),
        ("SYNTH-BANK-26", "probe_L18_a24"),
    ]
    assert all(c.alpha == 0.0 for c in conditions if c.steering == "none")
    assert all(c.alpha == 24.0 and c.layer == 18 for c in conditions if c.steering != "none")
    assert next(c for c in conditions if c.prompt_label == "empty").prompt_text == ""
    assert "Best guess" in next(c for c in conditions if c.prompt_label == "SYNTH-BANK-26").prompt_text


def test_frozen_split_is_test_only_and_disjoint():
    runner = _runner()
    _, dev_items, test_items = runner.load_frozen_split()
    canonical_dev, canonical_test = split_e0012_pool(
        load_e0012_pool(use_fixture=True), split_seed=E0012_SPLIT_SEED
    )
    assert [it["id"] for it in dev_items] == [it["id"] for it in canonical_dev]
    assert [it["id"] for it in test_items] == [it["id"] for it in canonical_test]
    assert len(dev_items) == 27
    assert len(test_items) == 53
    assert {it["id"] for it in dev_items}.isdisjoint({it["id"] for it in test_items})


def test_k_is_frozen_to_stage1_k5():
    runner = _runner()
    assert runner.FROZEN_K == 5
    assert runner.FROZEN_K == K_STAGE1


def test_vector_sha256_match_assertion_raises_on_mismatch():
    runner = _runner()
    direction = ButtonDirection(
        family=runner.BTN_PROBE,
        layer=18,
        direction=np.ones(4),
        derivation_hash="fake",
    )
    with pytest.raises(RuntimeError, match="direction mismatch"):
        runner.assert_matching_alite_direction(direction, "not-the-real-hash")


def test_synthetic_smoke_persists_delta_ci_fields(tmp_path):
    script = SCRIPTS / "run_e0012_settling_grid.py"
    out_dir = tmp_path / "e0012_sg_smoke"
    proc = subprocess.run(
        [
            sys.executable,
            str(script),
            "--backend",
            "synthetic",
            "--output-dir",
            str(out_dir),
            "--bootstrap-b",
            "100",
        ],
        cwd=str(REPO),
        text=True,
        capture_output=True,
        check=True,
    )
    assert "E-0012-SG settling-grid summary" in proc.stdout
    result = json.loads((out_dir / "settling_grid.json").read_text(encoding="utf-8"))
    assert result["valid_for_paper"] is False
    assert result["experiment_id"] == "E-0012-SG"
    assert result["pool"]["n_dev"] == 27
    assert result["pool"]["n_test"] == 53
    assert result["pool"]["dev_test_overlap_n"] == 0
    assert result["sampler_settings"]["k"] == 5
    assert len(result["conditions"]) == 6
    assert {row["id"] for row in result["conditions"]} == {
        "empty__none",
        "empty__probe_L18_a24",
        "CAL-09__none",
        "CAL-09__probe_L18_a24",
        "SYNTH-BANK-26__none",
        "SYNTH-BANK-26__probe_L18_a24",
    }
    assert result["direction"]["hash_assertion"]["performed"] is False
    for delta_name in (
        "empty_probe_minus_empty",
        "CAL09_probe_minus_CAL09",
        "SYNTH26_probe_minus_SYNTH26",
        "best_steered_minus_best_prompt_only",
    ):
        delta = result["deltas"][delta_name]
        assert "mean_delta" in delta
        assert len(delta["ci95"]) == 2
        assert delta["bootstrap_b"] == 100
        assert delta["n_items"] == 53
        assert delta["cluster"] is True
    raw_path = Path(result["raw_pairs_path"])
    assert raw_path.exists()
    assert sum(1 for _ in raw_path.open(encoding="utf-8")) == 6 * 53 * 5
