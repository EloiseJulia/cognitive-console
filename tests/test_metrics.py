"""Unit tests for the semantic-facade metric (C1) — hand-verified on tiny vectors."""

import math

import numpy as np
import pytest

from cognitive_console import metrics


def test_project_scalar_axis_aligned():
    # x = (3, 4); projecting onto the two coordinate axes recovers 3 and 4.
    assert metrics.project_scalar([3.0, 4.0], [1.0, 0.0]) == pytest.approx(3.0)
    assert metrics.project_scalar([3.0, 4.0], [0.0, 1.0]) == pytest.approx(4.0)


def test_project_scalar_is_signed():
    # Pushing the wrong way along the axis must read negative, not abs().
    assert metrics.project_scalar([-3.0, 0.0], [1.0, 0.0]) == pytest.approx(-3.0)


def test_project_scalar_unnormalized_direction():
    # direction (0, 5) is normalized internally, so projection is the y-component.
    assert metrics.project_scalar([3.0, 4.0], [0.0, 5.0]) == pytest.approx(4.0)


def test_project_scalar_diagonal():
    # x=(1,1) onto unit diagonal (1,1)/sqrt2 -> sqrt2.
    assert metrics.project_scalar([1.0, 1.0], [1.0, 1.0]) == pytest.approx(math.sqrt(2.0))


def test_cosine_similarity_known_values():
    assert metrics.cosine_similarity([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)
    assert metrics.cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)
    assert metrics.cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(-1.0)


def test_facade_ratio_basic():
    assert metrics.facade_ratio(2.0, 8.0) == pytest.approx(0.25)


def test_facade_ratio_zero_vector_projection_raises():
    with pytest.raises(ValueError):
        metrics.facade_ratio(2.0, 0.0)


def test_unit_zero_vector_raises():
    with pytest.raises(ValueError):
        metrics.unit([0.0, 0.0, 0.0])


def test_empty_vector_raises():
    with pytest.raises(ValueError):
        metrics.project_scalar([], [1.0])


def test_dim_mismatch_raises():
    with pytest.raises(ValueError):
        metrics.project_scalar([1.0, 2.0, 3.0], [1.0, 0.0])


def test_random_null_deterministic_with_seed():
    x = np.arange(1.0, 17.0)  # 16-dim
    a = metrics.random_null_baseline(x, n_samples=500, seed=7)
    b = metrics.random_null_baseline(x, n_samples=500, seed=7)
    assert np.array_equal(a, b)
    c = metrics.random_null_baseline(x, n_samples=500, seed=8)
    assert not np.array_equal(a, c)


def test_random_null_baseline_bad_n_raises():
    with pytest.raises(ValueError):
        metrics.random_null_baseline([1.0, 2.0], n_samples=0)


def test_null_baseline_differs_from_signal():
    # Signal: project x onto its OWN direction -> full norm ||x||.
    # Null: projections onto random directions -> small relative to ||x|| in high dim.
    rng = np.random.default_rng(0)
    x = rng.standard_normal(64)
    signal = abs(metrics.project_scalar(x, x))  # == ||x||
    null = metrics.random_null_baseline(x, n_samples=2000, seed=1)
    # The true-direction projection must clear the random-null 95th percentile by a wide margin.
    assert signal > np.percentile(null, 95)
    assert signal > null.mean() * 3
    # Sanity: null itself is not degenerate.
    assert null.mean() > 0.0


def test_facade_metric_strong_signal_above_null():
    # Construct: caa direction = e0. Vector-only reaches strongly along e0 (proj 10).
    # Strongest prompt reaches only partway (proj 3) but still above random null.
    dim = 64
    caa = np.zeros(dim)
    caa[0] = 1.0
    vector_act = np.zeros(dim)
    vector_act[0] = 10.0
    prompt_act = np.zeros(dim)
    prompt_act[0] = 3.0
    prompt_act[1:] = 0.01  # tiny off-axis noise
    res = metrics.facade_metric(prompt_act, vector_act, caa, n_null=2000, seed=3)
    assert res.prompt_projection == pytest.approx(3.0, abs=1e-6)
    assert res.vector_projection == pytest.approx(10.0, abs=1e-6)
    assert res.facade_ratio == pytest.approx(0.3, abs=1e-6)
    assert res.prompt_above_null is True          # prompt beats chance (facade is real, not noise)
    assert res.facade_ratio < 1.0                  # but well below the latent ceiling
    assert res.signal_z > 3.0


def test_facade_metric_result_serializes():
    res = metrics.facade_metric([2.0, 0.0, 0.0, 0.0], [4.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0], n_null=100, seed=0)
    d = res.to_dict()
    assert set(d) >= {"prompt_projection", "vector_projection", "facade_ratio", "null_p95", "signal_z"}
    assert d["facade_ratio"] == pytest.approx(0.5)
