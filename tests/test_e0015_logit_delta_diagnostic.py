import json

import pytest

from scripts import run_e0015_logit_delta_diagnostic as D
from scripts import run_positive_control_scale_corrected as E0015


def test_token_change_fraction_detects_identical_and_changed_outputs():
    assert D.token_change_fraction("same tokens", "same tokens") == 0.0
    assert D.token_change_fraction("a b c", "a x c") == pytest.approx(1 / 3)
    assert D.token_change_fraction("", "new token") == 1.0


def test_beta_grid_includes_dev_frozen_once_plus_one_and_two(tmp_path):
    p = tmp_path / "e0015.json"
    p.write_text(json.dumps({
        "axes": {
            E0015.REFUSAL_AXIS: {
                "pc2a_steer_vs_neutral_baseline": {"selected_scale": {"beta": 1.0}}
            }
        }
    }), encoding="utf-8")
    betas = D.load_dev_frozen_betas(p)
    assert betas[E0015.REFUSAL_AXIS] == 1.0
    assert D.beta_grid_for_axis(E0015.REFUSAL_AXIS, betas) == [1.0, 2.0]


def test_target_token_specs_are_explicit_about_clean_and_fallback_cases():
    refusal = D.target_token_spec(E0015.REFUSAL_AXIS, {"id": "x"})
    assert refusal["defined"] is True
    assert "Sorry" in refusal["candidate_texts"]
    skepticism = D.target_token_spec("skepticism", {"answer_letter": "B"})
    assert skepticism["defined"] is True
    assert "B" in skepticism["candidate_texts"]
    deliberation = D.target_token_spec("deliberation", {"answer": "42"})
    assert deliberation["defined"] is False
    assert "not cleanly" in deliberation["note"]


def test_synthetic_smoke_writes_diagnostic_and_transcripts(tmp_path):
    out_dir = tmp_path / "diag"
    rc = D.main([
        "--backend", "synthetic",
        "--out-dir", str(out_dir),
        "--k-probes", "2",
        "--n-refusal-extraction", "4",
        "--n-metacog-extraction", "4",
    ])
    assert rc == 0
    payload = json.loads((out_dir / "diagnostic.json").read_text(encoding="utf-8"))
    assert payload["experiment_id"] == D.EXPERIMENT_ID
    assert payload["valid_for_paper"] is False
    assert payload["single_shared_hf_model_handle"]["enabled"] is False
    expected_records = sum(len(payload["axes"][axis]["by_beta"]) * 2 for axis in E0015.ALL_AXES)
    assert payload["transcript_records"] == expected_records
    rows = (out_dir / "transcripts.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(rows) == payload["transcript_records"]
    first = json.loads(rows[0])
    assert {"baseline_completion", "steered_completion", "output_change_fraction"} <= set(first)
    for axis in E0015.ALL_AXES:
        assert axis in payload["axes"]
        assert payload["axes"][axis]["by_beta"]
