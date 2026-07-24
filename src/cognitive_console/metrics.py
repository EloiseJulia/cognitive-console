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


# --------------------------------------------------------------------------- #
# Same-origin, scale-free "reach fraction" (Claim C1, corrected — see D-0016)
# --------------------------------------------------------------------------- #
# The original facade_ratio above divides prompt_reach (measured from a NEUTRAL
# origin) by ||v|| = ||mean(pos)-mean(neg)|| (a neg-pole->pos-pole displacement
# that also silently bakes in the CAA steering coefficient alpha=1). That mixes
# two different origins and an arbitrary alpha, so the ratio is a metric-
# construction artifact rather than an achievable-range fraction (audit
# BLOCKER-1 alpha dependence, BLOCKER-2 origin mismatch).
#
# The corrected metric measures BOTH the prompt displacement and the achievable
# on-axis displacement from the SAME neutral origin, projected on the SAME unit
# direction û, and takes NO steering coefficient:
#
#   prompt_reach = <mean(strong-prompt act) - neutral_mean_act, û>
#   pole_reach   = <mean(EXTRACTION-POS act) - neutral_mean_act, û>
#   facade_ratio = prompt_reach / pole_reach
#
# Scale-free (û is unit-norm, both reaches in the same activation units) and
# alpha-independent (pole_reach is the model's own positive-pole displacement,
# not alpha*||v||). Interpretation:
#   0 < ratio << 1  -> genuine facade (prompt points right way, only part-way)
#   ratio ~= 1 or >1 -> NO facade (prompt reaches as far as the pole)
#   ratio < 0        -> prompt goes the WRONG way along the axis.
#
# These helpers operate on SCALAR projection arrays (activations already dotted
# onto û), so they are pure, fast, and model-independent for unit testing.


def reach_fraction(prompt_reach: float, pole_reach: float) -> float:
    """Same-origin scale-free facade ratio: prompt_reach / pole_reach.

    Both reaches are signed on-axis displacements from the SAME neutral origin.
    Raises if the achievable pole displacement is ~0 (ratio undefined — the
    positive pole is not separated from neutral along û, so there is no range to
    take a fraction of)."""
    if abs(pole_reach) < _EPS:
        raise ValueError("pole_reach is ~0; reach_fraction undefined")
    return float(prompt_reach / pole_reach)


@dataclass(frozen=True)
class SameOriginFacadeResult:
    prompt_reach: float             # <mean(strong) - neutral_mean, û>
    pole_reach: float               # <mean(extraction-POS) - neutral_mean, û>
    facade_ratio: float             # prompt_reach / pole_reach (SAME origin, alpha-free)
    ci_lo: float                    # bootstrap CI lower bound (resample strong set)
    ci_hi: float                    # bootstrap CI upper bound
    ci_level: float                 # e.g. 0.95
    loo_min: float                  # leave-one-neutral-out ratio band (min)
    loo_max: float                  # leave-one-neutral-out ratio band (max)
    n_strong: int
    n_neutral: int
    n_boot: int
    seed: int

    def to_dict(self) -> Dict:
        return asdict(self)


def same_origin_facade(
    strong_projs,
    pos_projs,
    neutral_projs,
    n_boot: int = 2000,
    seed: int = 0,
    ci_level: float = 0.95,
) -> SameOriginFacadeResult:
    """Corrected C1 facade metric from SCALAR projections onto û.

    Parameters
    ----------
    strong_projs  : per-strong-prompt scalar projections onto û (len ~7).
    pos_projs     : per-EXTRACTION-POS scalar projections onto û (the positive
                    pole the model can actually reach on this axis).
    neutral_projs : per-neutral-prompt scalar projections onto û (the shared
                    origin for BOTH prompt_reach and pole_reach).

    Returns a SameOriginFacadeResult with the point estimate, a bootstrap 95% CI
    over the strong-prompt set, and a leave-one-neutral-out sensitivity band.
    """
    strong = _as_vector(strong_projs)
    pos = _as_vector(pos_projs)
    neutral = _as_vector(neutral_projs)
    if n_boot <= 0:
        raise ValueError("n_boot must be positive")
    if not (0.0 < ci_level < 1.0):
        raise ValueError("ci_level must be in (0, 1)")

    neutral_origin = float(neutral.mean())
    pole_proj = float(pos.mean())
    prompt_reach = float(strong.mean()) - neutral_origin
    pole_reach = pole_proj - neutral_origin
    ratio = reach_fraction(prompt_reach, pole_reach)

    # Bootstrap 95% CI by resampling the strong-prompt set (pole_reach is the
    # fixed achievable range; the sampling uncertainty is in the prompt reach).
    rng = np.random.default_rng(seed)
    n = strong.size
    idx = rng.integers(0, n, size=(n_boot, n))
    boot_prompt_reach = strong[idx].mean(axis=1) - neutral_origin
    boot_ratios = boot_prompt_reach / pole_reach
    lo_pct = 100.0 * (1.0 - ci_level) / 2.0
    hi_pct = 100.0 * (1.0 + ci_level) / 2.0
    ci_lo = float(np.percentile(boot_ratios, lo_pct))
    ci_hi = float(np.percentile(boot_ratios, hi_pct))

    # Leave-one-neutral-out: dropping a neutral shifts the shared origin, which
    # moves BOTH numerator and denominator. Report the band so neutral-set
    # sensitivity is visible (audit MINOR-7).
    loo_ratios = []
    if neutral.size > 1:
        for i in range(neutral.size):
            origin_i = float(np.delete(neutral, i).mean())
            pr_i = float(strong.mean()) - origin_i
            pole_i = pole_proj - origin_i
            if abs(pole_i) >= _EPS:
                loo_ratios.append(pr_i / pole_i)
    if not loo_ratios:
        loo_ratios = [ratio]
    loo_min = float(min(loo_ratios))
    loo_max = float(max(loo_ratios))

    return SameOriginFacadeResult(
        prompt_reach=prompt_reach,
        pole_reach=pole_reach,
        facade_ratio=ratio,
        ci_lo=ci_lo,
        ci_hi=ci_hi,
        ci_level=float(ci_level),
        loo_min=loo_min,
        loo_max=loo_max,
        n_strong=int(n),
        n_neutral=int(neutral.size),
        n_boot=int(n_boot),
        seed=int(seed),
    )


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
