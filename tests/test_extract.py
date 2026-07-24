"""CAA extraction: exact mean-difference on fixed activations + layer scan."""

import numpy as np
import pytest

from cognitive_console.activations import SyntheticActivationProvider
from cognitive_console.metrics import cosine_similarity
from cognitive_console.steering import (
    extract_caa,
    layer_diagnostics,
    mean_difference_vector,
)


def test_mean_difference_exact_on_fixed_activations():
    pos = np.array([[2.0, 0.0], [4.0, 2.0]])   # mean [3, 1]
    neg = np.array([[0.0, 0.0], [2.0, 2.0]])   # mean [1, 1]
    vec = mean_difference_vector(pos, neg)
    np.testing.assert_allclose(vec, [2.0, 0.0])


def test_layer_diagnostics_separation_sign_and_scale():
    # Perfectly separated along +x with zero within-group spread => large sep.
    pos = np.array([[10.0, 0.0], [10.0, 0.0]])
    neg = np.array([[-10.0, 0.0], [-10.0, 0.0]])
    d = layer_diagnostics(pos, neg, layer=0)
    assert d.vector_norm == pytest.approx(20.0)
    assert d.separation > 0


def test_layer_scan_picks_planted_best_layer():
    prov = SyntheticActivationProvider(dim=128, layers=[2, 4, 6, 8], seed=11)
    pos = [f"p{i}" for i in range(50)]
    neg = [f"n{i}" for i in range(50)]
    # Layer 6 has by far the strongest planted separation.
    gain = {2: 0.2, 4: 0.5, 6: 2.0, 8: 0.3}
    prov.plant_contrast("delib", pos, neg, magnitude=6.0, layer_gain=gain)
    res = extract_caa(prov, "delib", pos, neg, layers=[2, 4, 6, 8])
    assert res.layer == 6
    # Recovered direction aligns with the planted direction at the chosen layer.
    assert cosine_similarity(res.direction, prov.direction("delib", 6)) > 0.9
    # Separation ranking matches the planted gains.
    seps = {ell: res.per_layer[ell].separation for ell in [2, 4, 6, 8]}
    assert seps[6] == max(seps.values())
    assert seps[6] > seps[4] > seps[2]


def test_extraction_reproducible():
    def run():
        prov = SyntheticActivationProvider(dim=64, layers=[1, 2], seed=5)
        pos = [f"p{i}" for i in range(30)]
        neg = [f"n{i}" for i in range(30)]
        prov.plant_contrast("ax", pos, neg, magnitude=4.0, layer_gain={1: 1.0, 2: 0.5})
        return extract_caa(prov, "ax", pos, neg, layers=[1, 2])

    r1, r2 = run(), run()
    assert r1.layer == r2.layer
    np.testing.assert_allclose(r1.vector, r2.vector)


def test_unsupported_selection_raises():
    prov = SyntheticActivationProvider(dim=8, layers=[0])
    with pytest.raises(ValueError):
        extract_caa(prov, "ax", ["a"], ["b"], layers=[0], selection="magic")


# --------------------------------------------------------------------------- #
# Non-degenerate layer selection (feature/4, D-0019). These are pure, model-
# independent tests over separation / pole_reach / null dicts — no provider.
# --------------------------------------------------------------------------- #
from cognitive_console.steering import (  # noqa: E402
    min_layer_for_depth,
    select_nondegenerate_layer,
)


def test_min_layer_for_depth():
    # 28-block model, 20% floor -> ceil(5.6) = 6 (excludes layers 1..5).
    assert min_layer_for_depth(28, 0.2) == 6
    assert min_layer_for_depth(28, 0.0) == 0
    assert min_layer_for_depth(10, 0.25) == 3  # ceil(2.5)
    with pytest.raises(ValueError):
        min_layer_for_depth(28, 1.0)


def test_select_rejects_degenerate_shallow_high_sep_layer():
    """The `focus`-on-1.5B failure mode: the highest-separation layer is a shallow
    layer whose pole barely separates from neutral (pole_reach ~= 0). It must be
    rejected in favour of a deeper NON-DEGENERATE layer."""
    sep = {2: 6.5, 4: 5.7, 12: 4.4, 18: 3.6}
    pole = {2: -0.01, 4: 0.02, 12: 3.0, 18: 2.5}
    null = {2: 0.5, 4: 0.5, 12: 0.5, 18: 0.5}
    sel = select_nondegenerate_layer(sep, pole, null, min_layer=6, top_k=3)
    assert sel.chosen == 12          # best-separation NON-DEGENERATE layer
    assert sel.ranked == [12, 18]    # both valid, ordered by separation
    assert sel.has_stable_layer
    # Layer 2 rejected for BOTH depth floor and non-positive pole_reach.
    assert not sel.candidates[2].valid
    assert "depth floor" in sel.candidates[2].reject_reason
    assert not sel.candidates[4].valid  # below floor


def test_select_rejects_high_sep_layer_with_pole_below_null():
    """A deep, high-separation layer whose pole displacement does NOT clear the
    random-direction null (extraction failed) must still be excluded."""
    sep = {8: 9.0, 12: 4.4, 18: 3.6}
    pole = {8: 0.1, 12: 3.0, 18: 2.5}   # layer 8's pole is below its null p95
    null = {8: 0.5, 12: 0.5, 18: 0.5}
    sel = select_nondegenerate_layer(sep, pole, null, min_layer=6, top_k=3)
    assert sel.chosen == 12
    assert 8 not in sel.ranked
    assert not sel.candidates[8].valid
    assert "random-null" in sel.candidates[8].reject_reason


def test_select_returns_none_when_all_degenerate():
    """If no layer is non-degenerate, chosen is None (caller reports UNSTABLE) —
    we must NOT p-hack a facade at a degenerate layer."""
    sep = {2: 6.5, 4: 5.7}               # both below the depth floor
    pole = {2: 2.0, 4: 2.0}
    null = {2: 0.5, 4: 0.5}
    sel = select_nondegenerate_layer(sep, pole, null, min_layer=6, top_k=3)
    assert sel.chosen is None
    assert sel.ranked == []
    assert not sel.has_stable_layer


def test_select_top_k_truncates_and_orders_by_separation():
    sep = {10: 1.0, 12: 5.0, 14: 3.0, 16: 4.0}
    pole = {10: 2.0, 12: 2.0, 14: 2.0, 16: 2.0}
    null = {10: 0.5, 12: 0.5, 14: 0.5, 16: 0.5}
    sel = select_nondegenerate_layer(sep, pole, null, min_layer=6, top_k=2)
    assert sel.ranked == [12, 16]       # top-2 by separation
    assert sel.chosen == 12


def test_select_ties_break_to_lower_layer():
    sep = {10: 5.0, 20: 5.0}
    pole = {10: 2.0, 20: 2.0}
    null = {10: 0.5, 20: 0.5}
    sel = select_nondegenerate_layer(sep, pole, null, min_layer=6, top_k=3)
    assert sel.chosen == 10
