import json
from pathlib import Path

import pytest

from cognitive_console.experiments import latent_positive_control as lpc
from scripts import run_latent_positive_control as runner


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "latent_positive_control" / "keyword_blue_items.json"


def test_keyword_verifier_whole_word_case_insensitive():
    assert lpc.contains_keyword("The BLUE notebook is here.", "blue") == 1
    assert lpc.contains_keyword("A blue-green label is here.", "blue") == 0
    assert lpc.contains_keyword("A blueberry muffin is here.", "blue") == 0
    assert lpc.contains_keyword("No target word.", "blue") == 0


def test_protocol_data_has_sealed_test_but_dev_loader_does_not_mix_ids():
    data = lpc.load_protocol_items(DATA)
    dev_ids = {row["id"] for row in data["dev_items"]}
    test_ids = {row["id"] for row in data["test_items"]}
    extraction_ids = {row["id"] for row in data["extraction_prompts"]}
    assert dev_ids
    assert test_ids
    assert extraction_ids
    assert dev_ids.isdisjoint(test_ids)
    assert extraction_ids.isdisjoint(dev_ids)
    assert extraction_ids.isdisjoint(test_ids)


def test_coherence_gate_matches_frozen_formula():
    assert lpc.coherence_ok(0.17, 0.10)  # 0.17 <= 1.5*0.10+0.02
    assert not lpc.coherence_ok(0.171, 0.10)


def test_synthetic_smoke_writes_dev_only_artifact(tmp_path):
    out = tmp_path / "lpc-smoke"
    rc = runner.main([
        "--stage", "smoke",
        "--backend", "synthetic",
        "--data", str(DATA),
        "--out-dir", str(out),
        "--n-dev-items", "4",
    ])
    assert rc == 0
    payload = json.loads((out / "latent_positive_control_dev_results.json").read_text())
    assert payload["stage"] == "stage1_dev_only_no_test"
    assert payload["run_metadata"]["stage2_test_run"] is False
    assert payload["dev_effects"]["steer_minus_baseline"]["passes_dev_sanity"] is True
    dumped = json.dumps(payload)
    assert "test-000" not in dumped


def test_allow_test_is_rejected():
    with pytest.raises(SystemExit):
        runner.parse_args(["--allow-test"])
