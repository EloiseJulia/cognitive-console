"""Facade analysis (C1): recover a planted gap; guard against tautology."""

import numpy as np
import pytest

from cognitive_console.activations import SyntheticActivationProvider
from cognitive_console.analysis.facade import FacadeSpec, analyze_axis_facade, analyze_facade
from cognitive_console.steering import extract_caa


def _provider_with_axis(seed=1, dim=128, best_layer=8):
    prov = SyntheticActivationProvider(dim=dim, layers=[4, 8, 12], seed=seed)
    pos = [f"p{i}" for i in range(40)]
    neg = [f"n{i}" for i in range(40)]
    gain = {4: 0.4, best_layer: 1.5, 12: 0.5}
    prov.plant_contrast("delib", pos, neg, magnitude=6.0, layer_gain=gain)
    caa = extract_caa(prov, "delib", pos, neg, layers=[4, 8, 12])
    return prov, caa


def test_recovers_planted_facade_ratio():
    prov, caa = _provider_with_axis()
    # Prompt reaches 30% of the vector-only projection along the axis.
    prov.plant_facade("delib", "PROMPT", "VECTOR", vector_magnitude=8.0,
                      facade_fraction=0.3, layer=caa.layer)
    spec = FacadeSpec(axis="delib", layer=caa.layer, caa_direction=caa.direction,
                      prompt_text="PROMPT", vector_text="VECTOR")
    r = analyze_axis_facade(prov, spec, max_facade_ratio=0.8, n_null=500, seed=0)
    assert 0.2 <= r.facade_ratio <= 0.45          # recovered ~= planted 0.3
    assert r.prompt_above_null                     # genuine signal, above chance
    assert r.facade_gap_holds                       # below the 0.8 latent-ceiling
    assert r.c1_supported


def test_no_gap_when_prompt_matches_vector_guards_tautology():
    # facade_fraction = 1.0 => prompt reaches the SAME as vector-only. The
    # pipeline must NOT manufacture a facade gap here (it is not hardwired to
    # always report one).
    prov, caa = _provider_with_axis(seed=2)
    prov.plant_facade("delib", "PROMPT", "VECTOR", vector_magnitude=8.0,
                      facade_fraction=1.0, layer=caa.layer)
    spec = FacadeSpec(axis="delib", layer=caa.layer, caa_direction=caa.direction,
                      prompt_text="PROMPT", vector_text="VECTOR")
    r = analyze_axis_facade(prov, spec, max_facade_ratio=0.8, n_null=500, seed=0)
    assert r.facade_ratio >= 0.85                  # ~1.0: no gap
    assert not r.facade_gap_holds
    assert not r.c1_supported


def test_zero_signal_prompt_not_above_null_guards_above_null():
    # A prompt with NO planted axis component projects at chance onto the CAA
    # direction => prompt_above_null must be False (the null test is not rigged).
    prov, caa = _provider_with_axis(seed=3)
    # Only the vector-only text is planted; PROMPT is pure noise (never planted).
    prov.plant_facade("delib", "PROMPT_UNPLANTED", "VECTOR", vector_magnitude=8.0,
                      facade_fraction=0.0, layer=caa.layer)
    spec = FacadeSpec(axis="delib", layer=caa.layer, caa_direction=caa.direction,
                      prompt_text="TOTALLY_UNRELATED_PROMPT", vector_text="VECTOR")
    r = analyze_axis_facade(prov, spec, max_facade_ratio=0.8, n_null=1000, seed=0)
    assert not r.prompt_above_null
    assert not r.c1_supported


def test_analyze_facade_table_aggregates():
    prov, caa = _provider_with_axis(seed=4)
    prov.plant_facade("delib", "PROMPT", "VECTOR", vector_magnitude=8.0,
                      facade_fraction=0.25, layer=caa.layer)
    specs = [FacadeSpec(axis="delib", layer=caa.layer, caa_direction=caa.direction,
                        prompt_text="PROMPT", vector_text="VECTOR")]
    table = analyze_facade(prov, specs, max_facade_ratio=0.8, n_null=300, seed=0)
    assert table.n_axes == 1
    assert table.n_c1_supported == 1
    assert table.fraction_supported() == 1.0
    recs = table.to_records()
    assert recs[0]["axis"] == "delib"
