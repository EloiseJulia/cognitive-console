"""C2b reachability harness tests (offline, synthetic backend + real proxies)."""

import numpy as np
import pytest

from cognitive_console.experiments.reachability import (
    AxisSteerSpec,
    C2bAxisResult,
    run_c2b_axis,
    run_c2b_pilot,
)
from cognitive_console.steering.generate import SyntheticSteeredBackend


def _spec(axis, prompt_bias):
    strong = [(f"{axis}-s1", "s1"), (f"{axis}-s2", "s2")]
    return AxisSteerSpec(
        axis=axis,
        direction=np.ones(8),
        layer=3,
        strong_prompts=strong,
        neutral_prompt="neutral",
    )


def test_harness_output_shape():
    axis = "deliberation"
    # strong prompts get a modest positive bias (bounded prompt ceiling);
    # steering can exceed it (gain*alpha).
    backend = SyntheticSteeredBackend(axis, prompt_bias={"s1": 1.0, "s2": 0.5})
    res = run_c2b_axis(backend, _spec(axis, None), alphas=(1.0, 2.0, 4.0), max_new_tokens=16)
    assert isinstance(res, C2bAxisResult)
    assert res.axis == axis
    assert len(res.prompt_scores) == 2
    assert len(res.steer_only) == 3
    assert len(res.conflict) == 3
    # each conflict row has the audited landing fields
    for c in res.conflict:
        assert "landing_fraction" in c and "landing_fraction_raw" in c
        assert "winner" in c and "steer_pole" in c and "prompt_pole" in c


def test_steer_reaches_beyond_prompt_ceiling():
    axis = "deliberation"
    # bounded prompt reaches modest behavior; big-alpha steering goes further.
    backend = SyntheticSteeredBackend(axis, prompt_bias={"s1": 0.5, "s2": 0.3}, gain=1.0)
    res = run_c2b_axis(backend, _spec(axis, None), alphas=(2.0, 4.0, 8.0), max_new_tokens=16)
    assert res.steer_only_max >= res.prompt_ceiling
    assert res.reaches_beyond_prompt_ceiling is True
    assert res.beyond_margin > 0


def test_steer_does_not_reach_beyond_when_prompt_ceiling_high():
    axis = "deliberation"
    # strong prompts saturate the proxy; steering cannot exceed the ceiling.
    backend = SyntheticSteeredBackend(axis, prompt_bias={"s1": 10.0, "s2": 10.0}, gain=0.01)
    res = run_c2b_axis(backend, _spec(axis, None), alphas=(1.0, 2.0), max_new_tokens=16)
    assert res.reaches_beyond_prompt_ceiling is False


def test_conflict_latent_wins_at_high_alpha():
    axis = "skepticism"
    # prompt pushes skepticism UP (bias), steer pushes DOWN (negative alpha in harness).
    backend = SyntheticSteeredBackend(axis, prompt_bias={"s1": 2.0, "s2": 1.0}, gain=1.0)
    res = run_c2b_axis(backend, _spec(axis, None), alphas=(2.0, 8.0), max_new_tokens=16)
    high = res.conflict[-1]
    # at strong opposite steer, latent should drag behavior toward the steer pole.
    assert high["landing_fraction_raw"] > 0.3


def test_run_pilot_over_multiple_axes():
    specs = [_spec("deliberation", None), _spec("focus", None)]
    backends = {
        "deliberation": SyntheticSteeredBackend("deliberation", prompt_bias={"s1": 0.5, "s2": 0.5}),
        "focus": SyntheticSteeredBackend("focus", prompt_bias={"s1": 0.2, "s2": 0.2}),
    }
    results = run_c2b_pilot(lambda ax: backends[ax], specs, alphas=(1.0, 2.0), max_new_tokens=16)
    assert len(results) == 2
    assert {r.axis for r in results} == {"deliberation", "focus"}
    for r in results:
        assert r.to_row()["axis"] == r.axis
