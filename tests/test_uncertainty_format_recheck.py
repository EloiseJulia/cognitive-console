import json

import pytest

from scripts import run_uncertainty_format_recheck as R


def test_confidence_parse_none_sets_noncompliant_and_frozen_imputation():
    item = {"id": "u1", "prompt": "Capital of France?", "answer": "Paris"}
    rec = R.score_uncertainty_record("Answer: Paris.", item)
    assert rec["parse_confidence"] is None
    assert rec["format_compliant"] is False
    assert rec["item_is_correct"] == 1
    assert rec["imputed_confidence"] == 0.5
    assert rec["per_item_1minus_brier"] == pytest.approx(0.75)


def test_compliant_only_reanalysis_uses_only_paired_compliant_samples():
    records = [
        _row("it1", 0, "prompt", True, 0.80),
        _row("it1", 0, "steer", True, 0.60),
        _row("it1", 1, "prompt", True, 0.70),
        _row("it1", 1, "steer", False, 0.75),  # excluded: steer dropped format
        _row("it2", 0, "prompt", True, 0.50),
        _row("it2", 0, "steer", True, 0.90),
        _row("it2", 1, "prompt", False, 0.75),  # excluded: prompt dropped format
        _row("it2", 1, "steer", True, 0.95),
    ]
    out = R.reanalyse(records, bootstrap_b=200, seed=7)["test_split_only"]["caa__qwen2.5-7b"]
    assert out["format_compliant_only_delta_steer_minus_prompt"]["n_compliant_sample_pairs"] == 2
    assert out["format_compliant_only_delta_steer_minus_prompt"]["n_items"] == 2
    # item means: it1=(0.60-0.80)=-0.20; it2=(0.90-0.50)=+0.40; mean=+0.10
    assert out["format_compliant_only_delta_steer_minus_prompt"]["point"] == pytest.approx(0.10)
    assert out["conditions"]["steer"]["format_compliance_rate"] == pytest.approx(3 / 4)
    assert out["conditions"]["prompt"]["format_compliance_rate"] == pytest.approx(3 / 4)


def test_synthetic_smoke_writes_compliance_and_delta_fields(tmp_path):
    frozen_root = _write_minimal_frozen_root(tmp_path / "frozen")
    out_dir = tmp_path / "e0013"
    rc = R.main([
        "--backend", "synthetic",
        "--frozen-root", str(frozen_root),
        "--out-dir", str(out_dir),
        "--cells", "caa__qwen2.5-7b",
        "--splits", "test",
        "--n-items", "4",
        "--bootstrap-b", "200",
        "--allow-underpowered",
    ])
    assert rc == 0
    payload = json.loads((out_dir / "reanalysis.json").read_text(encoding="utf-8"))
    cell = payload["test_split_only"]["caa__qwen2.5-7b"]
    assert "format_compliance_rate" in cell["conditions"]["steer"]
    assert "frozen_uncertainty_delta_steer_minus_prompt_as_run_imputed" in cell
    assert "format_compliant_only_delta_steer_minus_prompt" in cell
    sample = json.loads((out_dir / "samples.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert sample["synthetic_proxy"] is True
    assert sample["format_compliant"] is True
    assert sample["parse_confidence"] is not None
    manifest = json.loads((out_dir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["synthetic_proxy"] is True
    assert manifest["generation_identity"]["model_by_cell"]["caa__qwen2.5-7b"] == "frozen-qwen"


def test_model_identity_mismatch_raises_before_generation(tmp_path):
    frozen_root = _write_minimal_frozen_root(tmp_path / "frozen")
    out_dir = tmp_path / "e0013"
    with pytest.raises(SystemExit, match="--model"):
        R.main([
            "--backend", "synthetic",
            "--frozen-root", str(frozen_root),
            "--out-dir", str(out_dir),
            "--cells", "caa__qwen2.5-7b",
            "--qwen-model", "wrong-qwen",
            "--n-items", "4",
            "--bootstrap-b", "200",
            "--allow-underpowered",
        ])
    assert not (out_dir / "samples.jsonl").exists()


def _row(item_id, sample_index, condition, compliant, score):
    return {
        "cell": "caa__qwen2.5-7b",
        "split": "test",
        "item_id": item_id,
        "sample_index": sample_index,
        "condition": condition,
        "format_compliant": compliant,
        "per_item_1minus_brier": score,
    }


def _write_minimal_frozen_root(root):
    path = root / "cell_caa__qwen2.5-7b"
    path.mkdir(parents=True)
    payload = {
        "backend": "hf",
        "steering_method": "caa",
        "model": "frozen-qwen",
        "config_fingerprint": "abc123",
        "frozen_params": {"k_samples": 5},
        "c1_layer_info": {"uncertainty_awareness": {"sigma": 1.0}},
        "axes": [{
            "axis": "uncertainty_awareness",
            "layer": 3,
            "mean_diff": -0.1,
            "dev_selection": {
                "best_prompt_id": "unc-test",
                "best_prompt_text": "Answer and state confidence.",
                "frozen_alpha": 8.0,
            },
        }],
    }
    (path / "c2b_adjudication_results.json").write_text(json.dumps(payload), encoding="utf-8")
    return root
