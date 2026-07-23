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
