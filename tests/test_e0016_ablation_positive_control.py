
import json
from pathlib import Path

import numpy as np
import pytest

from cognitive_console.steering.generate import project_out_direction_array, unit_vector
from scripts import run_e0016_ablation_positive_control as e0016


def _items(n, prefix="it"):
    return [e0016.Item(f"{prefix}-{i}", f"Benign safe prompt {i}", "test") for i in range(n)]


def test_projection_ablation_zeroes_component_and_hook_bites_guard():
    r = unit_vector(np.array([1.0, 2.0, -1.0]))
    h = np.array([[[3.0, 4.0, 5.0], [1.0, 0.0, -2.0]]])
    new = project_out_direction_array(h, r)
    assert np.max(np.abs(np.tensordot(new, r, axes=([-1], [0])))) < 1e-10
    stats = {1: {"max_abs_before": 3.0, "max_abs_after": 1e-8, "mean_abs_before": 1.0, "mean_abs_after": 1e-8, "n_values": 2}}
    payload = e0016.assert_ablation_hook_bites(stats, abs_tol=1e-5)
    assert payload["non_vacuous"] is True


def test_dev_eligibility_gate_fires_when_baseline_under_floor():
    low = e0016.EvalResult("baseline", np.zeros((4, 2)), np.zeros((4, 2)), ["h"] * 4)
    eligible, status, rate = e0016.dev_eligibility_status(low)
    assert eligible is False
    assert status == "INVALID_REGIME_B_UNDERPOWERED"
    assert rate == 0.0


def test_real_not_smoke_rejects_placeholder_provenance():
    bundle = e0016.DirectionBundle(
        direction=unit_vector(np.arange(1, 17, dtype=float)),
        source_layer=1,
        position="last_token",
        provenance={
            "method": "arditi_refusal_direction_mean_harmful_minus_harmless",
            "derivation_function": "forward_pass_only_no_generation",
            "selected_layer_separation": 2.0,
            "note": "synthetic placeholder",
        },
    )
    with pytest.raises(ValueError, match="smoke|placeholder"):
        e0016.assert_real_not_smoke(bundle, backend="hf", provider_hidden_dim=16, xstest_prov={"path": "real"}, dev=_items(2, "d"), test=_items(2, "t"))


def test_dev_test_disjoint_guard():
    dev = [e0016.Item("same", "a", "s")]
    test = [e0016.Item("same", "b", "s")]
    with pytest.raises(ValueError, match="DEV/TEST overlap"):
        e0016.assert_dev_test_disjoint(dev, test)


def test_random_control_path_does_not_pass_in_synthetic_smoke(tmp_path):
    payload = e0016.run(e0016.parse_args(["--backend", "synthetic", "--out-dir", str(tmp_path), "--dev-n", "4", "--test-n", "8", "--k", "2"]))
    assert payload["dev"]["status"] == "ELIGIBLE"
    assert payload["status"] == "PASS"
    assert payload["test"]["random_control"]["pass"] is False
    assert payload["harmful_generation_performed"] is False
    written = tmp_path / "e0016_ablation_positive_control_results.json"
    assert json.loads(written.read_text(encoding="utf-8"))["valid_for_paper"] is False


def test_pass_rule_logic_and_random_veto():
    base = e0016.EvalResult("baseline", np.ones((6, 2)), np.zeros((6, 2)), [str(i) for i in range(6)])
    ablated = e0016.EvalResult("ablation", np.zeros((6, 2)), np.zeros((6, 2)), [str(i) for i in range(6)])
    random_null = e0016.EvalResult("random", np.ones((6, 2)), np.zeros((6, 2)), [str(i) for i in range(6)])
    passed = e0016.pass_rule(base, ablated, random_null, bootstrap_seed=1)
    assert passed["pass"] is True
    random_bad = e0016.EvalResult("random", np.zeros((6, 2)), np.zeros((6, 2)), [str(i) for i in range(6)])
    vetoed = e0016.pass_rule(base, ablated, random_bad, bootstrap_seed=1)
    assert vetoed["pass"] is False
    assert vetoed["status"] == "INVALID_RANDOM"



def test_xstest_safe_filter_and_local_override(tmp_path):
    path = tmp_path / "xstest.csv"
    path.write_text(
        "id,prompt,type,label,focus,note\n"
        "s1,Safe benign prompt,safe,safe,general,\n"
        "u1,Unsafe prompt,unsafe,unsafe,general,\n"
        "s2,Another safe prompt,safe,safe,general,\n",
        encoding="utf-8",
    )
    dev, test, prov = e0016.load_xstest_items(path, backend="hf", split_seed=1, dev_n=1, test_n=1)
    assert len(dev) == 1 and len(test) == 1
    assert prov["safe_count"] == 2
    assert "safe_prompt_hashes_sha256" in prov


def test_ungated_contrast_sources_from_local_csvs_do_not_commit_raw_harmful(tmp_path):
    harmful = tmp_path / "harmful_behaviors.csv"
    harmless = tmp_path / "alpaca.csv"
    harmful.write_text("goal,target\n[unsafe-class placeholder A],x\n[unsafe-class placeholder B],x\n", encoding="utf-8")
    harmless.write_text("instruction\nPlan a picnic\nExplain photosynthesis\n", encoding="utf-8")
    harm, safe, prov = e0016.load_contrast_prompts(None, backend="hf", harmful_source=str(harmful), harmless_source=str(harmless), direction_n=2)
    assert len(harm) == len(safe) == 2
    assert prov["raw_harmful_prompts_committed"] is False
    assert prov["forward_pass_only_no_harmful_generation"] is True
    assert "harmful_prompt_hashes" in prov and "[unsafe-class placeholder A]" not in prov["harmful_prompt_hashes"]


def test_default_dataset_sources_are_ungated_choices():
    assert e0016.DEFAULT_XSTEST_SOURCE == "Paul/XSTest:train"
    assert "llm-attacks" in e0016.DEFAULT_HARMFUL_SOURCE
    assert "walledai" not in e0016.DEFAULT_XSTEST_SOURCE.lower()
    assert "walledai" not in e0016.DEFAULT_HARMFUL_SOURCE.lower()
    assert e0016.DEFAULT_HARMLESS_SOURCE == "tatsu-lab/alpaca:train:instruction"
