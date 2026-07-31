"""Tests for the E-0012-CS comparator-strength script."""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path

from cognitive_console.eval.e0012_triviaqa import E0012_SPLIT_SEED, load_e0012_pool
from cognitive_console.experiments.e0012_harness import K_STAGE1, split_e0012_pool


REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _runner():
    if "run_e0012_comparator_strength" not in sys.modules:
        return importlib.import_module("run_e0012_comparator_strength")
    return sys.modules["run_e0012_comparator_strength"]


def test_condition_counts_and_ids():
    runner = _runner()
    conditions = runner.build_conditions(hidden_dim=16)
    assert len(conditions) == 50
    assert sum(1 for c in conditions if c.source == "synthetic_bank") == 30
    assert sum(1 for c in conditions if c.source == "calibration_yaml") == 18
    assert sum(1 for c in conditions if c.source == "baseline") == 1
    assert sum(1 for c in conditions if c.source == "button") == 1
    assert {c.condition_id for c in conditions if c.source == "calibration_yaml"} >= {"CAL-09"}
    assert {c.condition_id for c in conditions if c.source == "button"} == {"BTN-CAL-PROBE-L19-A24"}


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


def test_condition_payload_persists_prompt_text_and_button_spec():
    runner = _runner()
    conditions = runner.build_conditions(hidden_dim=16)
    prompt_condition = next(c for c in conditions if c.condition_id == "SYNTH-BANK-00")
    button_condition = next(c for c in conditions if c.condition_id == "BTN-CAL-PROBE-L19-A24")
    prompt_payload = runner._condition_payload(prompt_condition, 0.5, 265)
    button_payload = runner._condition_payload(button_condition, 0.6, 265)
    assert prompt_payload["prompt_text"]
    assert prompt_payload["prompt_hash"]
    assert button_payload["prompt_text"] == ""
    assert button_payload["button_spec"]["family"] == "BTN-CAL-PROBE"
    assert button_payload["button_spec"]["layer"] == 19
    assert button_payload["button_spec"]["alpha"] == 24.0


def test_synthetic_smoke_persists_summary_fields(tmp_path):
    script = SCRIPTS / "run_e0012_comparator_strength.py"
    out_dir = tmp_path / "e0012_cs_smoke"
    proc = subprocess.run(
        [sys.executable, str(script), "--backend", "synthetic", "--output-dir", str(out_dir)],
        cwd=str(REPO),
        text=True,
        capture_output=True,
        check=True,
    )
    assert "E-0012-CS comparator-strength summary" in proc.stdout
    result = json.loads((out_dir / "comparator_strength.json").read_text(encoding="utf-8"))
    assert result["valid_for_paper"] is False
    assert result["n_conditions"] == 50
    assert result["condition_counts"] == {
        "synthetic_bank": 30,
        "calibration_yaml": 18,
        "baseline": 1,
        "button": 1,
    }
    assert result["pool"]["n_dev"] == 27
    assert result["pool"]["n_test"] == 53
    assert result["pool"]["dev_test_overlap_n"] == 0
    assert result["k"] == 5
    for field in ("max_condition", "best_synthetic_bank", "cal_09", "button", "baseline"):
        assert field in result
    raw_path = Path(result["raw_pairs_path"])
    assert raw_path.exists()
    assert sum(1 for _ in raw_path.open(encoding="utf-8")) == 50 * 53 * 5
