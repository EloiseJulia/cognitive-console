"""Go/No-Go routing (S11) — spec phase0-pilot.md §3 decision, as a pure function.

Maps a structured Phase-0 results object to one of three routes:

* ``main_line`` (GREEN): strongest-prompt projection significantly BELOW
  vector-only (facade holds) AND above the null (C1 holds) AND blind-eval above
  chance AND transfer/composition survive AND a behavioral prompt-search ceiling
  exists on >=1 task (C2b seed). -> build the coordination + conflict console.
* ``plan_b`` (PARTIAL): facade holds but there is no behavioral ceiling OR
  composition is fragile. -> prompt-engineering limit probe (hard-cutoff framing).
* ``plan_d`` (RED): strongest prompt ~= vector-only (no facade) OR steering only
  changes surface style everywhere. -> measurement/benchmark paper on the gap.

The decision is deterministic and thoroughly unit-tested. All thresholds are
carried on `RoutingThresholds` so they can be pre-registered / frozen and so the
routing is not tautological — it reads *measured* quantities, not a pre-baked
verdict.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

MAIN_LINE = "main_line"
PLAN_B = "plan_b"
PLAN_D = "plan_d"

GREEN = "green"
PARTIAL = "partial"
RED = "red"


@dataclass
class RoutingThresholds:
    """Pre-registered decision thresholds (freeze before confirmatory use)."""
    # Facade must hold on at least this fraction of axes to count as "facade holds".
    min_facade_support_fraction: float = 0.5
    # A facade_ratio at/above this on (most) axes => "prompt ~= vector-only" (RED).
    no_facade_ratio: float = 0.9


@dataclass
class RoutingInputs:
    """Measured Phase-0 signals feeding the routing decision.

    Populate these from the aggregated analysis artifacts (facade table,
    blind-eval, transfer/compose, conflict/OPRO ceiling, style-vs-substance) —
    never hand-typed verdicts.
    """
    facade_support_fraction: float       # frac of axes with C1 facade gap + above-null
    max_facade_ratio_observed: float     # worst (largest) facade_ratio across axes
    prompt_above_null: bool              # C1 signal clears the random null
    blind_eval_above_chance: bool        # AC4
    transfer_survives: bool              # AC5 transfer to held-out
    composition_survives: bool           # AC5 multi-axis composition doesn't collapse
    behavioral_ceiling_exists: bool      # AC8/AC6 prompt-search ceiling on >=1 task
    style_only_everywhere: bool          # AC7 steering only moves surface style, not correctness


@dataclass
class RoutingDecision:
    route: str                           # main_line | plan_b | plan_d
    verdict: str                         # green | partial | red
    rationale: str
    gates: Dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


def decide_route(
    inputs: RoutingInputs,
    thresholds: Optional[RoutingThresholds] = None,
) -> RoutingDecision:
    """Apply the spec §3 green/partial/red criteria. Pure, deterministic."""
    th = thresholds or RoutingThresholds()

    facade_holds = (
        inputs.facade_support_fraction >= th.min_facade_support_fraction
        and inputs.prompt_above_null
    )
    # "prompt ~= vector-only" — no meaningful facade anywhere.
    no_facade = inputs.max_facade_ratio_observed >= th.no_facade_ratio and not facade_holds

    gates = {
        "facade_holds": bool(facade_holds),
        "prompt_above_null": bool(inputs.prompt_above_null),
        "blind_eval_above_chance": bool(inputs.blind_eval_above_chance),
        "transfer_survives": bool(inputs.transfer_survives),
        "composition_survives": bool(inputs.composition_survives),
        "behavioral_ceiling_exists": bool(inputs.behavioral_ceiling_exists),
        "style_only_everywhere": bool(inputs.style_only_everywhere),
        "no_facade": bool(no_facade),
    }

    # RED: no facade (prompt ~= vector-only) OR steering only surface style everywhere.
    if no_facade or inputs.style_only_everywhere or not facade_holds:
        reason = []
        if not facade_holds:
            reason.append(
                f"facade does not hold (support={inputs.facade_support_fraction:.2f} "
                f"< {th.min_facade_support_fraction:.2f} or prompt not above null)"
            )
        if inputs.style_only_everywhere:
            reason.append("steering changes only surface style everywhere (AC7)")
        return RoutingDecision(
            route=PLAN_D,
            verdict=RED,
            rationale="RED -> Plan D (measurement/benchmark paper on the legibility "
            "gap): " + "; ".join(reason),
            gates=gates,
        )

    # GREEN: facade holds AND all downstream evidence survives.
    green = (
        facade_holds
        and inputs.blind_eval_above_chance
        and inputs.transfer_survives
        and inputs.composition_survives
        and inputs.behavioral_ceiling_exists
    )
    if green:
        return RoutingDecision(
            route=MAIN_LINE,
            verdict=GREEN,
            rationale="GREEN -> main line: facade gap holds above null, blind-eval "
            "above chance, transfer + composition survive, and a behavioral "
            "prompt-search ceiling exists. Build the coordination + conflict console.",
            gates=gates,
        )

    # PARTIAL: facade holds but a downstream condition is missing.
    missing = [k for k in (
        "blind_eval_above_chance",
        "transfer_survives",
        "composition_survives",
        "behavioral_ceiling_exists",
    ) if not gates[k]]
    return RoutingDecision(
        route=PLAN_B,
        verdict=PARTIAL,
        rationale="PARTIAL -> Plan B (prompt-engineering limit probe / hard-cutoff "
        "framing): facade holds but missing " + ", ".join(missing) + ".",
        gates=gates,
    )
