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
    # ISOLATE the no_facade_ratio trigger: facade support looks fine (facade_holds
    # is True) but the worst-axis facade ratio is >= no_facade_ratio (0.9), so the
    # gap vanishes on the worst axis => RED on its own. This is the independent
    # trigger that used to be dead code (subsumed by `not facade_holds`).
    inp = _green()
    assert inp.facade_support_fraction >= 0.5 and inp.prompt_above_null  # facade holds
    inp.max_facade_ratio_observed = 0.98     # worst-axis prompt ~= vector-only
    d = decide_route(inp)
    assert d.route == PLAN_D
    assert d.verdict == "red"
    assert d.gates["facade_holds"]           # facade DID hold: this is not the trigger
    assert d.gates["no_facade_ratio_hit"]    # THIS is what forced RED
    assert "worst-axis facade_ratio" in d.rationale


def test_red_no_support_fraction_routes_plan_d():
    # The OTHER red path: no facade support anywhere (facade_holds False), with a
    # benign worst-case ratio so no_facade_ratio is NOT what triggers RED.
    inp = _green()
    inp.facade_support_fraction = 0.0        # facade does not hold anywhere
    inp.max_facade_ratio_observed = 0.30     # benign; not the trigger
    d = decide_route(inp)
    assert d.route == PLAN_D
    assert d.verdict == "red"
    assert not d.gates["facade_holds"]
    assert not d.gates["no_facade_ratio_hit"]


def test_no_facade_ratio_is_a_real_independent_knob():
    # Below the 0.9 threshold with facade holding => GREEN. Raising the observed
    # worst ratio above the threshold flips the SAME inputs to RED, proving the
    # knob independently affects the outcome (not dead code).
    below = _green()
    below.max_facade_ratio_observed = 0.85
    assert decide_route(below).route == MAIN_LINE
    above = _green()
    above.max_facade_ratio_observed = 0.91
    assert decide_route(above).route == PLAN_D
    # A stricter threshold makes an otherwise-green run RED: the threshold matters.
    strict = RoutingThresholds(no_facade_ratio=0.30)
    assert decide_route(_green(), strict).route == PLAN_D


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
