"""Semantic-facade metric primitives (Claim C1) — pure numpy, no torch.

The C1 hypothesis: the strongest *human-readable prompt's* mid-layer activation
projects onto a CAA steering direction far BELOW what the latent *vector-only*
intervention reaches, yet far ABOVE a *random-direction null baseline*. This
module supplies the projection / cosine primitives and the random-null baseline
used to quantify that gap. It does NOT extract activations (that is the deferred
GPU phase); it only computes metrics over activation vectors handed to it.

All functions operate on 1-D float arrays. No model loading, no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict

import numpy as np

_EPS = 1e-12


def _as_vector(x) -> np.ndarray:
    arr = np.asarray(x, dtype=np.float64)
    if arr.ndim != 1:
        raise ValueError(f"expected a 1-D vector, got shape {arr.shape}")
    if arr.size == 0:
        raise ValueError("empty vector")
    return arr


def unit(v) -> np.ndarray:
    """Return v / ||v||. Raises on a (near-)zero vector — a zero direction has
    no defined orientation and silently returning zeros would corrupt every
    downstream projection."""
    arr = _as_vector(v)
    norm = float(np.linalg.norm(arr))
    if norm < _EPS:
        raise ValueError("cannot normalize a (near-)zero vector")
    return arr / norm


def cosine_similarity(a, b) -> float:
    """Cosine similarity in [-1, 1]."""
    ua, ub = unit(a), unit(b)
    return float(np.clip(np.dot(ua, ub), -1.0, 1.0))


def project_scalar(x, direction) -> float:
    """Signed scalar projection of x onto `direction`: <x, dir/||dir||>.

    This is the component of x along the (oriented) direction, in activation
    units. Sign matters — a prompt that pushes the activation the *wrong* way
    along the axis should read negative, not be hidden by an abs().
    """
    x = _as_vector(x)
    d = unit(direction)
    if x.shape != d.shape:
        raise ValueError(f"dim mismatch: x={x.shape} direction={d.shape}")
    return float(np.dot(x, d))


def random_null_baseline(x, n_samples: int = 1000, seed: int = 0) -> np.ndarray:
    """Distribution of |signed projection| of x onto random unit directions.

    Establishes the chance level: how large a projection magnitude arises purely
    from random directions of the same dimensionality. A real signal must clear
    this null. Deterministic given `seed`.
    """
    x = _as_vector(x)
    if n_samples <= 0:
        raise ValueError("n_samples must be positive")
    rng = np.random.default_rng(seed)
    dirs = rng.standard_normal((n_samples, x.size))
    norms = np.linalg.norm(dirs, axis=1, keepdims=True)
    norms = np.where(norms < _EPS, 1.0, norms)
    dirs = dirs / norms
    projs = dirs @ x
    return np.abs(projs)


def facade_ratio(prompt_projection: float, vector_projection: float) -> float:
    """Fraction of the latent (vector-only) projection that the best prompt
    reproduces: prompt_proj / vector_proj. ~1.0 => no facade (prompt matches
    latent); near 0 (or negative) => strong facade. Guarded against a zero
    latent projection."""
    if abs(vector_projection) < _EPS:
        raise ValueError("vector_projection is ~0; facade_ratio undefined")
    return float(prompt_projection / vector_projection)


@dataclass(frozen=True)
class FacadeResult:
    prompt_projection: float
    vector_projection: float
    facade_ratio: float
    null_mean: float
    null_std: float
    null_p95: float
    signal_z: float           # (|prompt_proj| - null_mean) / null_std
    prompt_above_null: bool   # |prompt_proj| > null_p95
    n_null: int
    seed: int

    def to_dict(self) -> Dict:
        return asdict(self)


def facade_metric(
    prompt_activation,
    vector_activation,
    caa_direction,
    n_null: int = 1000,
    seed: int = 0,
) -> FacadeResult:
    """Compute the full C1 facade metric for one axis on one model.

    Parameters
    ----------
    prompt_activation : mid-layer activation under the strongest human-readable prompt.
    vector_activation : mid-layer activation under the latent vector-only intervention.
    caa_direction     : the CAA / RepE steering direction for the axis.

    Returns a FacadeResult with the prompt vs vector-only projections, the facade
    ratio, and the random-null baseline stats. Green C1 = prompt_above_null True
    (above chance) AND facade_ratio well below 1 (below latent ceiling).
    """
    p_proj = project_scalar(prompt_activation, caa_direction)
    v_proj = project_scalar(vector_activation, caa_direction)
    null = random_null_baseline(prompt_activation, n_samples=n_null, seed=seed)
    null_mean = float(null.mean())
    null_std = float(null.std())
    null_p95 = float(np.percentile(null, 95))
    # signal_z = (|prompt_proj| - null_mean) / null_std. Guard the degenerate
    # null: when null_std ~ 0 the ratio is undefined. If the excess signal
    # (|prompt_proj| - null_mean) is also ~ 0 we have 0/0 -> return nan (no
    # measurable signal, z is meaningless) rather than the misleading +inf a
    # naive division would produce. A real excess over a zero-variance null is
    # reported as +/-inf, which is the honest limit.
    excess = abs(p_proj) - null_mean
    if null_std > _EPS:
        signal_z = float(excess / null_std)
    elif abs(excess) < _EPS:
        signal_z = float("nan")
    else:
        signal_z = float("inf") if excess > 0 else float("-inf")
    return FacadeResult(
        prompt_projection=p_proj,
        vector_projection=v_proj,
        facade_ratio=facade_ratio(p_proj, v_proj),
        null_mean=null_mean,
        null_std=null_std,
        null_p95=null_p95,
        signal_z=signal_z,
        prompt_above_null=bool(abs(p_proj) > null_p95),
        n_null=int(n_null),
        seed=int(seed),
    )
