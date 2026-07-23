"""CAA / RepE steering-vector extraction (Contrastive Activation Addition).

Given an `ActivationProvider` and labelled contrast pairs (pos vs neg) for one
axis, extract the mean-difference steering vector at each candidate layer and
select the best injection layer by a documented separation criterion.

Selection criterion (documented so drift is intentional, not accidental)
------------------------------------------------------------------------
For each layer we project every sample onto the *unit* mean-difference direction
and compute the standardized separation between the pos and neg projections:

    separation(layer) = (mean_pos_proj - mean_neg_proj) / pooled_within_std

This is a Cohen's-d style signal-to-noise ratio. It is scale-invariant across
layers (unlike the raw ||mean_diff||, which can be inflated by a layer whose
activations simply have larger norm), so the layer with the genuinely cleanest
pos/neg separation wins. Ties break toward the lower layer index (deterministic).

Everything here is pure numpy over activations handed in by the provider — no
model, no GPU, no I/O.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

import numpy as np

_EPS = 1e-12


@dataclass(frozen=True)
class LayerDiagnostics:
    layer: int
    separation: float          # Cohen's-d style pos/neg separation
    vector_norm: float         # ||mean_pos - mean_neg||
    mean_pos_proj: float
    mean_neg_proj: float
    pooled_std: float
    n_pos: int
    n_neg: int


@dataclass
class CAAResult:
    axis: str
    layer: int                 # selected best injection layer
    vector: np.ndarray         # raw mean-difference (pos - neg) at chosen layer
    direction: np.ndarray      # unit-norm steering direction at chosen layer
    selection: str
    per_layer: Dict[int, LayerDiagnostics] = field(default_factory=dict)

    def to_summary(self) -> Dict[str, object]:
        """JSON-safe summary (no raw arrays) for registry/manifest logging."""
        return {
            "axis": self.axis,
            "selected_layer": self.layer,
            "selection": self.selection,
            "vector_norm": float(np.linalg.norm(self.vector)),
            "separation_by_layer": {
                str(ell): d.separation for ell, d in sorted(self.per_layer.items())
            },
        }


def _pooled_std(a: np.ndarray, b: np.ndarray) -> float:
    """Pooled within-group std of two 1-D projection samples."""
    na, nb = len(a), len(b)
    if na + nb - 2 <= 0:
        return float(np.sqrt((a.var() + b.var()) / 2.0))
    ss = (na - 1) * a.var(ddof=1) + (nb - 1) * b.var(ddof=1)
    return float(np.sqrt(ss / (na + nb - 2)))


def layer_diagnostics(
    pos_acts: np.ndarray, neg_acts: np.ndarray, layer: int
) -> LayerDiagnostics:
    """Mean-difference direction quality at one layer."""
    pos_acts = np.asarray(pos_acts, dtype=np.float64)
    neg_acts = np.asarray(neg_acts, dtype=np.float64)
    if pos_acts.ndim != 2 or neg_acts.ndim != 2:
        raise ValueError("activations must be 2-D [n, d]")
    if pos_acts.shape[1] != neg_acts.shape[1]:
        raise ValueError("pos/neg activation dim mismatch")
    if len(pos_acts) == 0 or len(neg_acts) == 0:
        raise ValueError("need at least one pos and one neg activation")

    mean_diff = pos_acts.mean(axis=0) - neg_acts.mean(axis=0)
    norm = float(np.linalg.norm(mean_diff))
    if norm < _EPS:
        # No separable direction; report zero separation rather than dividing by 0.
        return LayerDiagnostics(
            layer=layer, separation=0.0, vector_norm=0.0,
            mean_pos_proj=0.0, mean_neg_proj=0.0, pooled_std=0.0,
            n_pos=len(pos_acts), n_neg=len(neg_acts),
        )
    unit = mean_diff / norm
    pos_proj = pos_acts @ unit
    neg_proj = neg_acts @ unit
    pooled = _pooled_std(pos_proj, neg_proj)
    mean_pos = float(pos_proj.mean())
    mean_neg = float(neg_proj.mean())
    sep = (mean_pos - mean_neg) / (pooled if pooled > _EPS else _EPS)
    return LayerDiagnostics(
        layer=layer,
        separation=float(sep),
        vector_norm=norm,
        mean_pos_proj=mean_pos,
        mean_neg_proj=mean_neg,
        pooled_std=pooled,
        n_pos=len(pos_acts),
        n_neg=len(neg_acts),
    )


def mean_difference_vector(pos_acts: np.ndarray, neg_acts: np.ndarray) -> np.ndarray:
    """The raw CAA vector: mean(pos) - mean(neg)."""
    pos_acts = np.asarray(pos_acts, dtype=np.float64)
    neg_acts = np.asarray(neg_acts, dtype=np.float64)
    return pos_acts.mean(axis=0) - neg_acts.mean(axis=0)


def extract_caa(
    provider,
    axis: str,
    pos_texts: Sequence[str],
    neg_texts: Sequence[str],
    layers: Sequence[int] | None = None,
    selection: str = "separation",
) -> CAAResult:
    """Extract a CAA steering vector for `axis` with a layer scan.

    Parameters
    ----------
    provider : ActivationProvider — supplies pos/neg activations per layer.
    pos_texts / neg_texts : the contrast-pair members.
    layers : candidate injection layers (default: all provider layers).
    selection : criterion for the best layer. Only "separation" (Cohen's d) is
        currently supported.

    Returns a `CAAResult` with the chosen layer, its raw + unit vector, and the
    per-layer diagnostics used to select it.
    """
    if selection != "separation":
        raise ValueError(f"unsupported selection criterion: {selection!r}")
    if layers is None:
        layers = provider.available_layers()
    layers = [int(x) for x in layers]
    if not layers:
        raise ValueError("no candidate layers")

    per_layer: Dict[int, LayerDiagnostics] = {}
    for ell in layers:
        pos = provider.get_activations(pos_texts, ell)
        neg = provider.get_activations(neg_texts, ell)
        per_layer[ell] = layer_diagnostics(pos, neg, ell)

    # Select the max-separation layer; ties -> lower layer index (deterministic).
    best_layer = max(layers, key=lambda ell: (per_layer[ell].separation, -ell))
    pos_best = provider.get_activations(pos_texts, best_layer)
    neg_best = provider.get_activations(neg_texts, best_layer)
    vector = mean_difference_vector(pos_best, neg_best)
    norm = float(np.linalg.norm(vector))
    direction = vector / (norm if norm > _EPS else 1.0)

    return CAAResult(
        axis=axis,
        layer=best_layer,
        vector=vector,
        direction=direction,
        selection=selection,
        per_layer=per_layer,
    )


# --------------------------------------------------------------------------- #
# Non-degenerate layer selection (feature/4, D-0019)
# --------------------------------------------------------------------------- #
# The bare Cohen's-d rule above maximizes pos/neg SEPARATION, which can pick a
# shallow, near-lexical layer whose contrast direction û does NOT actually move
# the positive pole away from a content-free NEUTRAL origin. On Qwen2.5-1.5B the
# `focus` axis hit exactly this: layer 2 had the highest separation (6.54) yet
# pole_reach = <mean(pos) - mean(neutral), û> ~= 0 (a degenerate direction for
# the facade measurement — there is no achievable range to take a fraction of).
#
# A layer is NON-DEGENERATE for the C1 facade read only if ALL hold:
#   1. depth floor: layer >= min_layer (~>=20% of network depth) — steering
#      directions live in the transformer's mid/late blocks, not the shallow
#      near-embedding layers where separation is often lexical.
#   2. positive pos/neg separation (separation > 0).
#   3. the positive pole clears the random-direction null from the neutral
#      origin: pole_reach > 0 AND pole_reach > pole_null_p95 (extraction_success).
#
# We select the best-separation layer AMONG the non-degenerate ones (ties -> lower
# index), and expose the top-k for robustness reporting. If NO layer qualifies,
# `chosen` is None and the caller must report the axis as UNSTABLE rather than
# forcing a facade at a degenerate layer.


def min_layer_for_depth(top_layer: int, min_depth_frac: float = 0.2) -> int:
    """Shallowest layer index allowed for CAA selection: ceil(frac * top_layer).

    `top_layer` is the deepest hidden-state index (num_hidden_layers). With
    frac=0.2 on a 28-block model this excludes layers 1..5 (below index 6)."""
    if not (0.0 <= min_depth_frac < 1.0):
        raise ValueError("min_depth_frac must be in [0, 1)")
    if top_layer < 0:
        raise ValueError("top_layer must be >= 0")
    return int(math.ceil(min_depth_frac * top_layer))


@dataclass(frozen=True)
class LayerCandidate:
    layer: int
    separation: float          # Cohen's-d pos/neg separation
    pole_reach: float          # <mean(pos) - mean(neutral), û>
    pole_null_p95: float       # random-direction null p95 on the pole displacement
    valid: bool                # non-degenerate for the facade read
    reject_reason: str         # "" if valid, else why it was rejected


@dataclass(frozen=True)
class LayerSelection:
    chosen: Optional[int]                       # best non-degenerate layer, or None
    ranked: List[int]                           # top-k non-degenerate layers (best sep first)
    candidates: Dict[int, LayerCandidate]       # per-layer diagnostics + validity
    min_layer: int
    top_k: int

    @property
    def has_stable_layer(self) -> bool:
        return self.chosen is not None


def select_nondegenerate_layer(
    separation_by_layer: Dict[int, float],
    pole_reach_by_layer: Dict[int, float],
    pole_null_p95_by_layer: Dict[int, float],
    min_layer: int,
    top_k: int = 3,
) -> LayerSelection:
    """Pick the best NON-DEGENERATE layer for the C1 facade read.

    A layer qualifies iff layer >= min_layer AND separation > 0 AND
    pole_reach > 0 AND pole_reach > pole_null_p95. Among qualifying layers the
    one with the highest Cohen's-d separation wins (ties -> lower index). The
    top-k qualifying layers are returned for robustness reporting. If none
    qualify, `chosen` is None (caller reports the axis as unstable).
    """
    if top_k < 1:
        raise ValueError("top_k must be >= 1")
    layers = sorted(separation_by_layer)
    candidates: Dict[int, LayerCandidate] = {}
    for ell in layers:
        sep = float(separation_by_layer[ell])
        pole = float(pole_reach_by_layer[ell])
        p95 = float(pole_null_p95_by_layer[ell])
        reasons: List[str] = []
        if ell < min_layer:
            reasons.append(f"below depth floor (layer {ell} < {min_layer})")
        if not (sep > 0.0):
            reasons.append("non-positive pos/neg separation")
        if not (pole > 0.0):
            reasons.append("pole_reach <= 0 (pole not on +û side of neutral)")
        elif not (pole > p95):
            reasons.append("pole_reach below random-null p95 (extraction failed)")
        valid = not reasons
        candidates[ell] = LayerCandidate(
            layer=ell,
            separation=sep,
            pole_reach=pole,
            pole_null_p95=p95,
            valid=valid,
            reject_reason="; ".join(reasons),
        )

    valid_layers = [ell for ell in layers if candidates[ell].valid]
    # Best separation first; ties -> lower layer index (deterministic).
    valid_layers.sort(key=lambda ell: (-candidates[ell].separation, ell))
    ranked = valid_layers[:top_k]
    chosen = ranked[0] if ranked else None
    return LayerSelection(
        chosen=chosen,
        ranked=ranked,
        candidates=candidates,
        min_layer=int(min_layer),
        top_k=int(top_k),
    )

