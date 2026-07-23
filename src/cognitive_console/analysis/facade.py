"""Semantic-facade analysis (Claim C1) over an ActivationProvider.

C1 hypothesis: the strongest *human-readable prompt's* mid-layer activation
projects onto the CAA steering direction far BELOW what the latent *vector-only*
intervention reaches, yet ABOVE a random-direction null baseline. This module
orchestrates that measurement across axes/layers using an `ActivationProvider`
and the extracted CAA vectors, reusing the pure-numpy primitives in
`cognitive_console.metrics`.

The heavy lifting (projection, null baseline, facade_ratio, signal_z) lives in
metrics.py; here we only fetch the two activations per axis from the provider,
call the metric, tag it with axis/layer + a pass/fail against pre-registered
thresholds, and aggregate to a results table.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Sequence

import numpy as np

from ..metrics import FacadeResult, facade_metric


@dataclass(frozen=True)
class AxisFacadeResult:
    axis: str
    layer: int
    facade_ratio: float
    prompt_projection: float
    vector_projection: float
    signal_z: float            # effect size: (|prompt_proj| - null_mean)/null_std
    prompt_above_null: bool
    # Pass criteria (pre-registered thresholds, see analyze_facade):
    facade_gap_holds: bool     # facade_ratio <= max_facade_ratio (prompt below latent)
    above_null: bool           # prompt clears the random-direction null
    c1_supported: bool         # facade_gap_holds AND above_null
    n_null: int
    seed: int

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


@dataclass
class FacadeSpec:
    """One axis's inputs to the facade analysis."""
    axis: str
    layer: int
    caa_direction: np.ndarray
    prompt_text: str
    vector_text: str


def analyze_axis_facade(
    provider,
    spec: FacadeSpec,
    max_facade_ratio: float = 0.8,
    n_null: int = 1000,
    seed: int = 0,
) -> AxisFacadeResult:
    """Compute the C1 facade metric for one axis at one layer.

    `max_facade_ratio` is the pre-registered ceiling below which the
    strongest-prompt projection counts as a genuine facade gap (prompt reaching
    at most this fraction of the latent vector-only projection).
    """
    prompt_act = provider.get_activations([spec.prompt_text], spec.layer)[0]
    vector_act = provider.get_activations([spec.vector_text], spec.layer)[0]
    res: FacadeResult = facade_metric(
        prompt_activation=prompt_act,
        vector_activation=vector_act,
        caa_direction=spec.caa_direction,
        n_null=n_null,
        seed=seed,
    )
    facade_gap_holds = res.facade_ratio <= max_facade_ratio
    above_null = bool(res.prompt_above_null)
    return AxisFacadeResult(
        axis=spec.axis,
        layer=spec.layer,
        facade_ratio=res.facade_ratio,
        prompt_projection=res.prompt_projection,
        vector_projection=res.vector_projection,
        signal_z=res.signal_z,
        prompt_above_null=above_null,
        facade_gap_holds=facade_gap_holds,
        above_null=above_null,
        c1_supported=bool(facade_gap_holds and above_null),
        n_null=int(n_null),
        seed=int(seed),
    )


@dataclass
class FacadeTable:
    """Aggregated facade results across axes."""
    rows: List[AxisFacadeResult] = field(default_factory=list)
    max_facade_ratio: float = 0.8

    @property
    def n_axes(self) -> int:
        return len(self.rows)

    @property
    def n_c1_supported(self) -> int:
        return sum(1 for r in self.rows if r.c1_supported)

    def fraction_supported(self) -> float:
        return self.n_c1_supported / self.n_axes if self.rows else 0.0

    def to_records(self) -> List[Dict[str, object]]:
        return [r.to_dict() for r in self.rows]


def analyze_facade(
    provider,
    specs: Sequence[FacadeSpec],
    max_facade_ratio: float = 0.8,
    n_null: int = 1000,
    seed: int = 0,
) -> FacadeTable:
    """Run the facade analysis for every axis spec and aggregate a table."""
    rows = [
        analyze_axis_facade(
            provider, s, max_facade_ratio=max_facade_ratio, n_null=n_null, seed=seed
        )
        for s in specs
    ]
    return FacadeTable(rows=rows, max_facade_ratio=max_facade_ratio)
