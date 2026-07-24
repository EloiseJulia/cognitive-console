"""ITI extraction tests (offline, synthetic, no torch)."""

import numpy as np
import pytest

from cognitive_console.activations import SyntheticActivationProvider
from cognitive_console.metrics import cosine_similarity
from cognitive_console.steering import extract_caa
from cognitive_console.steering.iti import extract_iti, sigma_scaled_alpha


class _FixedProvider:
    def __init__(self, layer_to_matrix, hidden_dim):
        self._acts = layer_to_matrix
        self._dim = hidden_dim

    @property
    def hidden_dim(self):
        return self._dim

    def available_layers(self):
        return sorted(self._acts)

    def get_activations(self, texts, layer):
        rows = [self._acts[int(layer)][t] for t in texts]
        return np.asarray(rows, dtype=np.float64)


def test_iti_recovers_planted_direction_on_synthetic_provider():
    prov = SyntheticActivationProvider(dim=128, layers=[6], seed=9, noise_scale=1.0)
    pos = [f"p{i}" for i in range(240)]
    neg = [f"n{i}" for i in range(240)]
    prov.plant_contrast("delib", pos, neg, magnitude=5.0, layer_gain={6: 1.0})
    res = extract_iti(prov, "delib", pos, neg, layers=[6], selection="separation")
    assert res.layer == 6
    assert cosine_similarity(res.direction, prov.direction("delib", 6)) > 0.9
    assert res.sigma > 0.0


def test_iti_and_caa_differ_under_outlier_tilt_but_both_are_reasonable():
    rng = np.random.default_rng(7)
    dim = 32
    u = np.zeros(dim)
    u[0] = 1.0
    v = np.zeros(dim)
    v[1] = 1.0

    neg = rng.normal(0.0, 0.4, size=(120, dim)) - 1.5 * u
    pos_core = rng.normal(0.0, 0.4, size=(116, dim)) + 1.5 * u
    pos_outliers = rng.normal(0.0, 0.1, size=(4, dim)) + 12.0 * v
    pos = np.vstack([pos_core, pos_outliers])

    pos_ids = [f"p{i}" for i in range(len(pos))]
    neg_ids = [f"n{i}" for i in range(len(neg))]
    table = {3: {}}
    for i, t in enumerate(pos_ids):
        table[3][t] = pos[i]
    for i, t in enumerate(neg_ids):
        table[3][t] = neg[i]
    prov = _FixedProvider(table, hidden_dim=dim)

    caa = extract_caa(prov, "axis", pos_ids, neg_ids, layers=[3])
    iti = extract_iti(prov, "axis", pos_ids, neg_ids, layers=[3], selection="separation")

    assert cosine_similarity(caa.direction, iti.direction) < 0.98
    assert cosine_similarity(caa.direction, u) > 0.5
    assert cosine_similarity(iti.direction, u) > 0.8
    assert iti.per_layer[3].separation > 0.0
    assert caa.per_layer[3].separation > 0.0


def test_sigma_scaling_alpha_conversion():
    assert sigma_scaled_alpha(4.0, 0.5) == pytest.approx(2.0)
    assert sigma_scaled_alpha(-3.0, 1.2) == pytest.approx(-3.6)
    with pytest.raises(ValueError):
        sigma_scaled_alpha(1.0, -0.1)
