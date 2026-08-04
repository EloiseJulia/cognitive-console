import json
from pathlib import Path

import numpy as np
import pytest

from cognitive_console.experiments import adjudicate_c2b as adj
from cognitive_console.eval import c2b_tasks, scorers
from scripts import run_positive_control as R


def test_refusal_scorer_and_axis_dispatch():
    item = {"id": "x", "prompt": "What is the capital of France?"}
    assert scorers.score_refusal("I'm sorry, but I can't answer that.", item) == 1
    assert scorers.score_refusal("Sure — Paris.", item) == 0
    assert adj.score_sample_outcome(R.AXIS, item, "I cannot help with that request.") == 1.0
    rendered = adj.format_task_input(R.AXIS, "Please answer the following question.", item)
    assert "Confidence:" not in rendered
    assert "Give the final numeric answer" not in rendered


def test_real_not_smoke_guard_raises_on_synthetic_random_direction_hf():
    direction = np.ones(8, dtype=np.float64) / np.sqrt(8)
    provenance = {
        "backend": "hf",
        "method": "synthetic_random_probe",
        "derivation_function": "derive_probe_direction_synthetic",
        "selected_layer_separation": 9.0,
    }
    with pytest.raises(ValueError, match="hidden_dim|placeholder|banned|dim"):
        R.assert_real_not_smoke_direction(direction, provenance, provider_hidden_dim=4096, backend="hf")


def test_random_direction_negative_control_is_wired(tmp_path):
    out_dir = tmp_path / "e0014"
    rc = R.main([
        "--backend", "synthetic",
        "--out-dir", str(out_dir),
        "--n-items", "6",
        "--n-extraction", "4",
        "--bootstrap-b", "200",
        "--allow-underpowered",
    ])
    assert rc == 0
    payload = json.loads((out_dir / "positive_control_results.json").read_text(encoding="utf-8"))
    neg = payload["random_direction_negative_control"]
    assert neg["direction_kind"] == "random_unit_negative_control"
    assert neg["expected_to_pass"] is False
    assert "result" in neg and "passed" in neg["result"]


def test_adjudicator_reuse_records_frozen_delta_bootstrap_bonferroni_coherence(tmp_path):
    out_dir = tmp_path / "e0014-reuse"
    R.main([
        "--backend", "synthetic",
        "--out-dir", str(out_dir),
        "--n-items", "6",
        "--n-extraction", "4",
        "--bootstrap-b", "200",
        "--allow-underpowered",
    ])
    payload = json.loads((out_dir / "positive_control_results.json").read_text(encoding="utf-8"))
    frozen = payload["frozen_adjudicator_reuse"]
    assert frozen["delta"] == adj.DELTA
    assert frozen["bootstrap"] == "paired item-cluster (resample items, each carries its k)"
    assert frozen["bonferroni_ci_level"] == adj.BONFERRONI_CI_LEVEL
    assert frozen["coherence_max_ratio"] == adj.COHERENCE_MAX_RATIO
    assert payload["pc3_steer_vs_best_of_n_prompt"]["ci_level"] == adj.BONFERRONI_CI_LEVEL
    assert payload["pc3_steer_vs_best_of_n_prompt"]["delta"] == adj.DELTA


def test_dev_test_disjoint_and_real_loader_excludes_frozen_uncertainty_prefix():
    task = c2b_tasks.load_c2b_task(R.AXIS, use_fixture=True)
    assert len(task.items) >= 6
    spec = R.build_spec("strong", np.ones(64), 3, use_fixture=True, n_items=6, n_strong=4)
    split = adj.split_dev_test([str(it["id"]) for it in spec.items], seed=20260723)
    assert set(split.dev_ids).isdisjoint(set(split.test_ids))


def test_hf_forbids_fixture_and_item_cap(tmp_path):
    with pytest.raises(SystemExit, match="real data"):
        R.main([
            "--backend", "hf",
            "--use-fixture",
            "--out-dir", str(tmp_path / "bad"),
        ])
    with pytest.raises(SystemExit, match="real data"):
        R.main([
            "--backend", "hf",
            "--n-items", "6",
            "--out-dir", str(tmp_path / "bad2"),
        ])
