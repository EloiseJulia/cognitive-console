"""Go/No-Go routing: green->main_line, partial->plan_b, red->plan_d."""

import pytest

from cognitive_console.analysis.routing import (
    MAIN_LINE,
    PLAN_B,
    PLAN_D,
    RoutingInputs,
    RoutingThresholds,
    decide_route,
)


def _green():
    return RoutingInputs(
        facade_support_fraction=0.75,
        max_facade_ratio_observed=0.35,
        prompt_above_null=True,
        blind_eval_above_chance=True,
        transfer_survives=True,
        composition_survives=True,
        behavioral_ceiling_exists=True,
        style_only_everywhere=False,
    )


def test_green_routes_main_line():
    d = decide_route(_green())
    assert d.route == MAIN_LINE
    assert d.verdict == "green"
    assert d.gates["facade_holds"]


def test_partial_no_ceiling_routes_plan_b():
    inp = _green()
    inp.behavioral_ceiling_exists = False   # facade holds but no behavioral ceiling
    d = decide_route(inp)
    assert d.route == PLAN_B
    assert d.verdict == "partial"
    assert "behavioral_ceiling_exists" in d.rationale


def test_partial_fragile_composition_routes_plan_b():
    inp = _green()
    inp.composition_survives = False
    d = decide_route(inp)
    assert d.route == PLAN_B


def test_red_no_facade_routes_plan_d():
    inp = _green()
    inp.facade_support_fraction = 0.0        # facade does not hold anywhere
    inp.max_facade_ratio_observed = 0.98     # prompt ~= vector-only
    d = decide_route(inp)
    assert d.route == PLAN_D
    assert d.verdict == "red"


def test_red_style_only_everywhere_routes_plan_d():
    inp = _green()
    inp.style_only_everywhere = True         # steering only moves surface style
    d = decide_route(inp)
    assert d.route == PLAN_D


def test_facade_not_above_null_is_red():
    inp = _green()
    inp.prompt_above_null = False            # C1 signal doesn't clear the null
    d = decide_route(inp)
    assert d.route == PLAN_D


def test_thresholds_are_honored():
    # Support fraction 0.4: fails the default 0.5 gate (red) but passes a 0.3 gate.
    inp = _green()
    inp.facade_support_fraction = 0.4
    assert decide_route(inp).route == PLAN_D
    lenient = RoutingThresholds(min_facade_support_fraction=0.3)
    assert decide_route(inp, lenient).route == MAIN_LINE


def test_decision_serializes():
    d = decide_route(_green())
    out = d.to_dict()
    assert set(out) == {"route", "verdict", "rationale", "gates"}
