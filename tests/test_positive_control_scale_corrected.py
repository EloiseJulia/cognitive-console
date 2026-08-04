import json

import numpy as np
import pytest

from cognitive_console.experiments import adjudicate_c2b as adj
from scripts import run_positive_control_scale_corrected as R


def test_beta_grid_scaling_records_raw_caa_alpha_eff_and_residual_ratio():
    rows = R.beta_scale_rows(216.0, residual_norm_mean=108.0)
    assert [r["beta"] for r in rows] == list(R.BETA_GRID)
    assert [r["alpha_eff"] for r in rows] == [27.0, 54.0, 108.0, 216.0, 432.0]
    assert rows[2]["alpha_eff_over_mean_residual_l2"] == pytest.approx(1.0)


def test_metacognitive_direction_layer_reuses_frozen_c2_without_reselection(tmp_path):
    bundle = R.derive_metacog_direction(
        "deliberation", "synthetic", R.DEFAULT_MODEL, n_extraction=4, seed=20260723, out_dir=tmp_path
    )
    assert bundle.layer == R.FROZEN_C2_LAYER_BY_AXIS["deliberation"]
    reuse = bundle.provenance["frozen_c2_reuse"]
    assert reuse["source"] == R.FROZEN_C2_LAYER_SOURCE
    assert reuse["same_contrast_pairs"] is True
    assert reuse["direction_sha256"] == bundle.provenance["direction_sha256"]
    assert bundle.provenance["selection"] == "frozen_c2_layer_reuse"


class FakeHookBackend:
    def __init__(self, *, dead=False):
        self.dead = dead

    def capture_residual_activations(self, prompts, layer, *, steer=None, batch_size=None):
        n = len(prompts)
        base = np.zeros((n, 3), dtype=np.float64)
        if steer is None or self.dead:
            return base
        return base + float(steer.alpha) * steer.unit()[None, :]


def _fake_bundle(dead=False):
    v = np.array([3.0, 4.0, 0.0], dtype=np.float64)
    u = v / np.linalg.norm(v)
    return R.ScaleDirectionBundle(
        axis="deliberation",
        vector=v,
        direction=u,
        layer=2,
        provenance={"axis": "deliberation", "direction_sha256": R._vector_sha256(u), "vector_norm": 5.0},
        hook_backend=FakeHookBackend(dead=dead),
    )


def _guard_bundle(axis="deliberation", *, dim=16, selection="frozen_c2_direction_layer_reuse_no_reselection",
                  provenance_extra=None, direction=None, separation=1.2):
    if direction is None:
        raw = np.arange(1, dim + 1, dtype=np.float64)
        direction = raw / np.linalg.norm(raw)
    else:
        direction = np.asarray(direction, dtype=np.float64)
        raw = direction.copy()
    prov = {
        "backend": "hf",
        "model_id": R.DEFAULT_MODEL,
        "axis": axis,
        "method": "caa_mean_difference_raw_magnitude_scale_corrected",
        "derivation_function": (
            "cognitive_console.steering.extract.extract_caa"
            if axis == R.REFUSAL_AXIS
            else "cognitive_console.steering.extract.extract_caa_at_single_frozen_c2_layer"
        ),
        "selection": selection,
        "selected_layer_separation": separation,
        "vector_sha256": R._vector_sha256(raw),
        "direction_sha256": R._vector_sha256(direction),
        "contrast_pairs_file_sha256": "sha256:" + "a" * 64,
        "layer": 20,
        "model_id": R.DEFAULT_MODEL,
        "extraction_pair_ids": ["pair-001"],
        "vector_norm": float(np.linalg.norm(raw)),
    }
    prov.update(provenance_extra or {})
    return R.ScaleDirectionBundle(axis, raw, direction, 20, prov)


def test_real_not_smoke_scale_guard_hf_valid_bundle_passes():
    bundle = _guard_bundle()
    R.assert_real_not_smoke_scale_direction(bundle, provider_hidden_dim=16, backend="hf")


@pytest.mark.parametrize(
    "bundle, hidden_dim, pattern",
    [
        (_guard_bundle(selection="reselected_layer"), 16, "frozen C2 layer"),
        (_guard_bundle(direction=np.ones(16, dtype=np.float64) / 4.0), 16, "constant"),
        (_guard_bundle(dim=16), 32, "dim"),
        (_guard_bundle(provenance_extra={"notes": "random placeholder direction"}), 16, "banned smoke token"),
        (_guard_bundle(axis=R.REFUSAL_AXIS, separation=0.2), 16, "separation floor"),
    ],
)
def test_real_not_smoke_scale_guard_hf_rejects_bad_bundles(bundle, hidden_dim, pattern):
    with pytest.raises(ValueError, match=pattern):
        R.assert_real_not_smoke_scale_direction(bundle, provider_hidden_dim=hidden_dim, backend="hf")


def test_hf_isolation_runtime_lock_fails_before_model_load(tmp_path):
    with pytest.raises(SystemExit, match="seed=20260723"):
        R.main(["--backend", "hf", "--seed", "123", "--out-dir", str(tmp_path / "bad-seed")])
    with pytest.raises(SystemExit, match="n_metacog_extraction=28"):
        R.main(["--backend", "hf", "--n-metacog-extraction", "4", "--out-dir", str(tmp_path / "bad-n")])


def test_hf_sampler_uses_shared_backend_instance_not_string_reload():
    items = [{"id": "x", "prompt": "What is 2+2?", "answer": "4"}]
    shared = R.SyntheticC2bTaskBackend("deliberation", items)
    sampler = R._make_sampler(
        "deliberation", "hf", R.DEFAULT_MODEL, items,
        max_new_tokens=8, temperature=0.7, seed=1, batch_size=1,
        shared_hf_backend=shared,
    )
    assert sampler.gen is shared
    with pytest.raises(ValueError, match="single shared"):
        R._make_sampler(
            "deliberation", "hf", R.DEFAULT_MODEL, items,
            max_new_tokens=8, temperature=0.7, seed=1, batch_size=1,
            shared_hf_backend=None,
        )


def test_upfront_full_beta_grid_hook_bites_passes_and_records_all_betas(tmp_path):
    bundle = _fake_bundle(dead=False)
    R.record_upfront_hook_bites_all_axes({"deliberation": bundle}, tmp_path)
    prov = json.loads((tmp_path / "direction_provenance.json").read_text(encoding="utf-8"))
    check = prov["deliberation"]["hook_bites_check"]
    assert check["mode"] == "pre_generation_full_beta_grid_every_axis"
    assert check["passed"] is True
    assert set(check["by_beta"].keys()) == {str(float(b)) for b in R.BETA_GRID}
    assert [check["by_beta"][str(float(b))]["alpha_eff"] for b in R.BETA_GRID] == [b * 5.0 for b in R.BETA_GRID]


def test_dead_hook_fails_closed_before_generation_and_writes_provenance(tmp_path):
    bundle = _fake_bundle(dead=True)
    with pytest.raises(AssertionError, match="before generation"):
        R.record_upfront_hook_bites_all_axes({"deliberation": bundle}, tmp_path)
    prov = json.loads((tmp_path / "direction_provenance.json").read_text(encoding="utf-8"))
    assert prov["deliberation"]["hook_bites_check"]["passed"] is False


def test_runtime_item_pool_disjointness_assertion_fires():
    bad_items = [
        {"id": "triviaqa-00079", "prompt": "Bad?", "answer": "bad"},
        {"id": "triviaqa-00080", "prompt": "Good?", "answer": "good"},
    ]
    with pytest.raises(AssertionError, match="triviaqa-00079"):
        R.assert_item_pool_for_axis(R.REFUSAL_AXIS, bad_items, backend="synthetic")


def test_metacognitive_hf_item_pool_minimum_assertion_fires():
    short = [{"id": f"gsm8k-test-{i:05d}", "prompt": "q", "answer": "1"} for i in range(59)]
    with pytest.raises(AssertionError, match="frozen N requires >=60"):
        R.assert_item_pool_for_axis("deliberation", short, backend="hf")
    short_unc = [{"id": f"triviaqa-{i:05d}", "prompt": "q", "answer": "a"} for i in range(79)]
    with pytest.raises(AssertionError, match="frozen N requires >=80"):
        R.assert_item_pool_for_axis("uncertainty_awareness", short_unc, backend="hf")


def test_mde_computation_has_underpowered_binary_floor():
    mde = R._normal_mde([0.0] * 40, ci_level=adj.BONFERRONI_CI_LEVEL, delta=adj.DELTA, fallback_n=40)
    assert mde["minimum_detectable_effect"] > 0.18
    assert mde["minimum_detectable_effect"] < 0.25
    assert "Null cells" in mde["power_honesty_note"]


def test_synthetic_smoke_exercises_scale_reuse_random_and_payload(tmp_path):
    rc = R.main([
        "--backend", "synthetic",
        "--out-dir", str(tmp_path / "e0015"),
        "--n-items", "6",
        "--n-refusal-extraction", "4",
        "--n-metacog-extraction", "4",
        "--bootstrap-b", "200",
        "--allow-underpowered",
    ])
    assert rc == 0
    payload = json.loads((tmp_path / "e0015" / "positive_control_scale_corrected_results.json").read_text(encoding="utf-8"))
    assert payload["experiment_id"] == "E-0015"
    assert payload["valid_for_paper"] is False
    assert payload["frozen_adjudicator_reuse"]["delta"] == adj.DELTA
    assert payload["single_variable_isolation"]["only_beta_varies_for_metacognitive_axes"] is True
    assert len(payload["interpretation_matrix"]) >= 6
    for axis in R.ALL_AXES:
        row = payload["axes"][axis]
        assert "mde" in row["pc2a_steer_vs_neutral_baseline"]
        assert row["random_direction_negative_control"]["expected_to_pass"] is False
        assert row["pc2a_steer_vs_neutral_baseline"]["selected_scale"]["alpha_eff"] in payload["direction_provenance"][axis]["alpha_eff_grid"]
