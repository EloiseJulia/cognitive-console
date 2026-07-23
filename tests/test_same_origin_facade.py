"""Unit tests for the CORRECTED same-origin, scale-free facade metric (D-0016).

These pin the fair reach-fraction computation on tiny synthetic SCALAR-projection
cases with a KNOWN answer, plus the bootstrap CI and leave-one-neutral-out band.
Fully model-independent (no torch, no model load).
"""

import numpy as np
import pytest

from cognitive_console import metrics


# --------------------------------------------------------------------------- #
# reach_fraction primitive
# --------------------------------------------------------------------------- #
def test_reach_fraction_basic():
    assert metrics.reach_fraction(4.0, 10.0) == pytest.approx(0.4)


def test_reach_fraction_zero_pole_raises():
    with pytest.raises(ValueError):
        metrics.reach_fraction(4.0, 0.0)


# --------------------------------------------------------------------------- #
# same_origin_facade point estimate — KNOWN planted reach fraction
# --------------------------------------------------------------------------- #
def test_planted_reach_fraction_is_recovered():
    # Neutral origin at 0; positive pole reaches +10; the strongest prompts plant a
    # displacement of 0.4 * pole (=+4) along û  =>  facade_ratio must be ~0.40.
    neutral = [0.0, 0.0, 0.0]
    pos = [10.0, 10.0, 10.0]
    strong = [4.0, 4.0, 4.0, 4.0, 4.0]
    r = metrics.same_origin_facade(strong, pos, neutral, n_boot=1000, seed=0)
    assert r.prompt_reach == pytest.approx(4.0)
    assert r.pole_reach == pytest.approx(10.0)
    assert r.facade_ratio == pytest.approx(0.40)
    assert r.ci_lo <= r.facade_ratio <= r.ci_hi
    assert r.ci_hi < 1.0  # CI upper bound below 1 => a genuine facade holds


def test_planted_reach_fraction_recovered_with_nonzero_origin():
    # Same 0.4 fraction, but the neutral origin is NOT at zero: origin=+2, pole at
    # +12 (pole_reach=10), prompt at +6 (prompt_reach=4). Both reaches must be
    # measured from the SAME neutral origin -> ratio still 0.4 (audit BLOCKER-2).
    neutral = [2.0, 2.0]
    pos = [12.0, 12.0]
    strong = [6.0, 6.0, 6.0]
    r = metrics.same_origin_facade(strong, pos, neutral, n_boot=500, seed=1)
    assert r.pole_reach == pytest.approx(10.0)
    assert r.prompt_reach == pytest.approx(4.0)
    assert r.facade_ratio == pytest.approx(0.40)


def test_prompt_at_pole_gives_ratio_one_no_facade():
    # Prompt planted AT the pole => reaches as far as the model's own pole => NO
    # facade (ratio ~= 1, CI upper bound NOT below 1).
    neutral = [0.0, 0.0]
    pos = [10.0, 10.0]
    strong = [10.0, 10.0, 10.0]
    r = metrics.same_origin_facade(strong, pos, neutral, n_boot=500, seed=2)
    assert r.facade_ratio == pytest.approx(1.0)
    assert not (r.ci_hi < 1.0)  # no facade: CI upper bound reaches/exceeds 1


def test_wrong_way_prompt_gives_negative_ratio():
    # Prompt pushes the WRONG way along û (negative displacement from neutral) while
    # the pole is positive => signed facade_ratio < 0 (evidence against a clean
    # prompt->latent map, NOT a facade).
    neutral = [0.0, 0.0]
    pos = [10.0, 10.0]
    strong = [-3.0, -3.0, -3.0]
    r = metrics.same_origin_facade(strong, pos, neutral, n_boot=500, seed=3)
    assert r.facade_ratio == pytest.approx(-0.30)
    assert r.facade_ratio < 0.0


# --------------------------------------------------------------------------- #
# bootstrap CI
# --------------------------------------------------------------------------- #
def test_bootstrap_ci_is_deterministic_and_brackets_estimate():
    rng = np.random.default_rng(42)
    strong = list(4.0 + rng.normal(0, 1.0, size=7))  # spread around 0.4*pole
    pos = [10.0] * 6
    neutral = [0.0] * 5
    r1 = metrics.same_origin_facade(strong, pos, neutral, n_boot=3000, seed=7)
    r2 = metrics.same_origin_facade(strong, pos, neutral, n_boot=3000, seed=7)
    # Deterministic given the seed.
    assert r1.ci_lo == r2.ci_lo
    assert r1.ci_hi == r2.ci_hi
    # A real interval that brackets the point estimate.
    assert r1.ci_lo < r1.ci_hi
    assert r1.ci_lo <= r1.facade_ratio <= r1.ci_hi
    # Facade holds here (strong reaches ~0.4 of the pole, well under 1).
    assert r1.ci_hi < 1.0


def test_bootstrap_ci_upper_bound_reaches_one_when_no_facade():
    # Strong prompts scatter AROUND the pole => the CI upper bound is NOT below 1,
    # so the facade does NOT hold (the guard is not hardwired to always fire).
    rng = np.random.default_rng(0)
    strong = list(10.0 + rng.normal(0, 1.5, size=7))
    pos = [10.0] * 6
    neutral = [0.0] * 5
    r = metrics.same_origin_facade(strong, pos, neutral, n_boot=3000, seed=11)
    assert not (r.ci_hi < 1.0)


# --------------------------------------------------------------------------- #
# leave-one-neutral-out sensitivity band
# --------------------------------------------------------------------------- #
def test_leave_one_neutral_out_band_reflects_sensitivity():
    # One neutral is an outlier: dropping it vs dropping an ordinary neutral shifts
    # the shared origin and therefore the ratio => a non-degenerate LOO band.
    neutral = [0.0, 0.0, 0.0, 6.0]
    pos = [12.0] * 4
    strong = [6.0] * 5
    r = metrics.same_origin_facade(strong, pos, neutral, n_boot=200, seed=5)
    assert r.loo_min < r.loo_max                       # band has real width
    assert np.isfinite(r.loo_min) and np.isfinite(r.loo_max)


def test_leave_one_neutral_out_band_collapses_when_neutrals_identical():
    # Identical neutrals => dropping any one leaves the origin unchanged => the band
    # collapses onto the point estimate.
    neutral = [0.0, 0.0, 0.0, 0.0]
    pos = [10.0] * 3
    strong = [4.0] * 4
    r = metrics.same_origin_facade(strong, pos, neutral, n_boot=200, seed=6)
    assert r.loo_min == pytest.approx(r.facade_ratio)
    assert r.loo_max == pytest.approx(r.facade_ratio)


# --------------------------------------------------------------------------- #
# serialization
# --------------------------------------------------------------------------- #
def test_same_origin_result_serializes():
    r = metrics.same_origin_facade([4.0, 4.0], [10.0], [0.0], n_boot=100, seed=0)
    d = r.to_dict()
    assert set(d) >= {
        "prompt_reach", "pole_reach", "facade_ratio",
        "ci_lo", "ci_hi", "loo_min", "loo_max",
    }
    assert d["facade_ratio"] == pytest.approx(0.4)
