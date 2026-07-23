"""Conflict-probe harness: landing metric + registry logging + HF stub."""

import numpy as np
import pytest

from cognitive_console.experiments.conflict_probe import (
    BehaviorBackend,
    ConflictConfig,
    HFBehaviorBackend,
    SyntheticBehaviorBackend,
    compute_landing,
    compute_landing_raw,
    run_conflict_probe,
)
from cognitive_console.registry import ExperimentRegistry


def _config(magnitude, seed=0):
    return ConflictConfig(
        axis="skepticism",
        prompt_text="answer with high confidence",   # prompt pole = 0.0
        prompt_target=0.0,
        latent_vector=np.ones(8),
        latent_magnitude=magnitude,
        latent_target=1.0,                            # latent pole = 1.0
        layer=12,
        seed=seed,
    )


def test_compute_landing_bounds_and_sign():
    assert compute_landing(0.0, 0.0, 1.0) == 0.0     # fully prompt pole
    assert compute_landing(1.0, 0.0, 1.0) == 1.0     # fully latent pole
    assert compute_landing(0.5, 0.0, 1.0) == 0.5     # exactly between
    # Clipped to [0,1] beyond the poles.
    assert compute_landing(2.0, 0.0, 1.0) == 1.0
    with pytest.raises(ValueError):
        compute_landing(0.5, 0.3, 0.3)                # coincident poles


def test_zero_magnitude_prompt_wins():
    backend = SyntheticBehaviorBackend(latent_gain=1.0)
    res = run_conflict_probe(backend, _config(magnitude=0.0))
    assert res.landing_fraction == pytest.approx(0.0)
    assert res.winner == "prompt"


def test_large_magnitude_latent_wins():
    backend = SyntheticBehaviorBackend(latent_gain=1.0)
    res = run_conflict_probe(backend, _config(magnitude=50.0))
    assert res.landing_fraction > 0.9
    assert res.winner == "latent"


def test_intermediate_magnitude_lands_between():
    backend = SyntheticBehaviorBackend(latent_gain=1.0)
    res = run_conflict_probe(backend, _config(magnitude=1.0))
    # w = 1/(1+1) = 0.5 => lands mid-way.
    assert 0.4 < res.landing_fraction < 0.6


def test_compute_landing_raw_preserves_overshoot_and_wrong_side():
    # Raw keeps the C2b/AC6 signal that clipping would erase.
    assert compute_landing_raw(1.5, 0.0, 1.0) == pytest.approx(1.5)   # latent overshoot
    assert compute_landing_raw(-0.3, 0.0, 1.0) == pytest.approx(-0.3)  # wrong side
    # Clipped view still bounds to [0,1].
    assert compute_landing(1.5, 0.0, 1.0) == 1.0
    assert compute_landing(-0.3, 0.0, 1.0) == 0.0


class _FixedBackend(BehaviorBackend):
    """Returns a preset behavior score, to exercise out-of-pole landings."""

    def __init__(self, score: float):
        self._score = float(score)

    def behavior_score(self, config: ConflictConfig) -> float:
        return self._score


def test_run_conflict_probe_flags_latent_overshoot():
    # behavior beyond the latent pole (score 1.5 with poles 0->1): clipped landing
    # saturates at 1.0 but raw exposes the overshoot and `clipped` is True.
    res = run_conflict_probe(_FixedBackend(1.5), _config(magnitude=3.0))
    assert res.landing_fraction == pytest.approx(1.0)
    assert res.landing_fraction_raw == pytest.approx(1.5)
    assert res.clipped is True
    assert res.winner == "latent"
    assert res.to_summary()["landing_fraction_raw"] == pytest.approx(1.5)
    assert res.to_summary()["clipped"] is True


def test_run_conflict_probe_flags_wrong_side_landing():
    # behavior on the wrong side of the prompt pole (score -0.4): clipped landing
    # pins at 0.0 but raw is negative and `clipped` is True.
    res = run_conflict_probe(_FixedBackend(-0.4), _config(magnitude=3.0))
    assert res.landing_fraction == pytest.approx(0.0)
    assert res.landing_fraction_raw == pytest.approx(-0.4)
    assert res.clipped is True
    assert res.winner == "prompt"


def test_synthetic_landing_is_not_clipped():
    # A normal in-between landing must NOT be flagged as clipped.
    res = run_conflict_probe(SyntheticBehaviorBackend(latent_gain=1.0), _config(magnitude=1.0))
    assert res.clipped is False
    assert 0.0 <= res.landing_fraction_raw <= 1.0


def test_conflict_probe_logs_registry_entry(tmp_path):
    reg = ExperimentRegistry(str(tmp_path / "registry.yaml"))
    backend = SyntheticBehaviorBackend(latent_gain=1.0)
    res = run_conflict_probe(
        backend, _config(magnitude=3.0, seed=17), registry=reg,
        config_hash="sha256:deadbeef", claim_ids=["C2b"],
    )
    assert res.experiment_id is not None
    row = reg.get(res.experiment_id)
    assert row is not None
    assert row["claim_ids"] == ["C2b"]
    assert row["hypothesis_id"] == "H2"
    assert row["config_hash"] == "sha256:deadbeef"
    assert row["seed"] == 17  # config seed passthrough
    # Logged numbers come from the computed result, not hand values.
    assert row["summary_metrics"]["landing_fraction"] == pytest.approx(res.landing_fraction)


def test_two_probes_get_distinct_experiment_ids(tmp_path):
    reg = ExperimentRegistry(str(tmp_path / "registry.yaml"))
    backend = SyntheticBehaviorBackend(latent_gain=1.0)
    r1 = run_conflict_probe(backend, _config(1.0, seed=1), registry=reg, config_hash="sha256:aa")
    r2 = run_conflict_probe(backend, _config(2.0, seed=2), registry=reg, config_hash="sha256:aa")
    assert r1.experiment_id != r2.experiment_id
    assert len(reg.load()) == 2


def test_hf_behavior_backend_is_stub():
    backend = HFBehaviorBackend("meta-llama/Meta-Llama-3-8B-Instruct")
    with pytest.raises(NotImplementedError):
        backend.behavior_score(_config(1.0))
