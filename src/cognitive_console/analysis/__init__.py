"""Phase-0 analysis: facade (C1) + Go/No-Go routing (S11)."""

from .facade import (
    AxisFacadeResult,
    FacadeSpec,
    FacadeTable,
    analyze_axis_facade,
    analyze_facade,
)
from .routing import (
    MAIN_LINE,
    PLAN_B,
    PLAN_D,
    RoutingDecision,
    RoutingInputs,
    RoutingThresholds,
    decide_route,
)

__all__ = [
    "AxisFacadeResult",
    "FacadeSpec",
    "FacadeTable",
    "analyze_axis_facade",
    "analyze_facade",
    "MAIN_LINE",
    "PLAN_B",
    "PLAN_D",
    "RoutingDecision",
    "RoutingInputs",
    "RoutingThresholds",
    "decide_route",
]
