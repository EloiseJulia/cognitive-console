"""OOD diagnostics for the robustness/mechanism arm (pure numpy, CPU-only).

Implements the frozen H-M mechanism check from:
`docs/ledgers/prereg-robustness-mechanism-arm.md` (FROZEN 2026-07-24).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, Mapping, Sequence

import numpy as np

from ..metrics import reach_fraction

_EPS = 1e-12

# Frozen H-M criterion (prereg-robustness-mechanism-arm.md §3, frozen 2026-07-24):
# Spearman rho(off-manifold distance, -delta_outcome) >= 0.30 AND 95% bootstrap CI
# excludes 0 in >=3/4 cells.
HM_SPEARMAN_THRESHOLD = 0.30
HM_CI_LEVEL = 0.95
HM_REQUIRED_PASS_CELLS = 3
HM_TOTAL_CELLS = 4


@dataclass(frozen=True)
class OODDistribution:
    mean: np.ndarray
    covariance: np.ndarray
    precision: np.ndarray
    shrinkage: float
    ridge: float
    n_obs: int


@dataclass(frozen=True)
class OODItemStats:
    mahalanobis: float
    norm_inflation: float


@dataclass(frozen=True)
class SpearmanBootstrap:
    rho: float
    ci_lo: float
    ci_hi: float
    ci_level: float
    b: int
    seed: int

    def ci_excludes_zero(self) -> bool:
        return not (self.ci_lo <= 0.0 <= self.ci_hi)


@dataclass(frozen=True)
class HMCellResult:
    cell: str
    rho: float
    ci_lo: float
    ci_hi: float
    threshold: float
    ci_excludes_zero: bool
    passed: bool

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class HMArmVerdict:
    passed_cells: int
    total_cells: int
    min_required: int
    supported: bool
    cells: Dict[str, HMCellResult]

    def to_dict(self) -> Dict[str, object]:
        return {
            "passed_cells": self.passed_cells,
            "total_cells": self.total_cells,
            "min_required": self.min_required,
            "supported": self.supported,
            "cells": {k: v.to_dict() for k, v in self.cells.items()},
        }


@dataclass(frozen=True)
class C1NullRelativeEffect:
    observed_ratio: float
    random_null_mean_ratio: float
    prompt_null_mean_ratio: float
    random_null_delta: float
    prompt_null_delta: float
    random_null_cohens_d: float
    prompt_null_cohens_d: float
    random_null_uplift: float
    prompt_null_uplift: float

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class C1SensitivityPoint:
    layer: int
    norm_scale: float
    random_null_cohens_d: float
    prompt_null_cohens_d: float

    @property
    def combined_effect(self) -> float:
        return 0.5 * (self.random_null_cohens_d + self.prompt_null_cohens_d)


@dataclass(frozen=True)
class C1SensitivitySummary:
    n_points: int
    mean_combined_effect: float
    min_combined_effect: float
    max_combined_effect: float
    positive_fraction: float
    per_layer_mean_effect: Dict[int, float]
    per_norm_mean_effect: Dict[str, float]

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


def _as_2d(name: str, x) -> np.ndarray:
    arr = np.asarray(x, dtype=np.float64)
    if arr.ndim != 2:
        raise ValueError(f"{name} must be 2-D [n, d], got {arr.shape}")
    if arr.shape[0] < 1 or arr.shape[1] < 1:
        raise ValueError(f"{name} must be non-empty")
    return arr


def _as_1d(name: str, x) -> np.ndarray:
    arr = np.asarray(x, dtype=np.float64)
    if arr.ndim != 1:
        raise ValueError(f"{name} must be 1-D, got {arr.shape}")
    if arr.size < 1:
        raise ValueError(f"{name} must be non-empty")
    return arr


def _rank_average_ties(x: np.ndarray) -> np.ndarray:
    order = np.argsort(x, kind="mergesort")
    sorted_x = x[order]
    ranks = np.empty(x.size, dtype=np.float64)
    i = 0
    while i < x.size:
        j = i + 1
        while j < x.size and sorted_x[j] == sorted_x[i]:
            j += 1
        # average 1-based rank for tie group [i, j)
        avg = 0.5 * (i + j - 1) + 1.0
        ranks[order[i:j]] = avg
        i = j
    return ranks


def _spearman_rho(x: np.ndarray, y: np.ndarray) -> float:
    if x.size != y.size:
        raise ValueError("x and y must have same size")
    if x.size < 2:
        raise ValueError("need at least 2 samples for Spearman rho")
    rx = _rank_average_ties(x)
    ry = _rank_average_ties(y)
    vx = rx - rx.mean()
    vy = ry - ry.mean()
    denom = float(np.linalg.norm(vx) * np.linalg.norm(vy))
    if denom < _EPS:
        return 0.0
    return float(np.dot(vx, vy) / denom)


def _cohens_d_vs_null(observed: float, null_samples: np.ndarray) -> float:
    mu = float(null_samples.mean())
    sigma = float(null_samples.std(ddof=1)) if null_samples.size > 1 else 0.0
    delta = observed - mu
    if sigma < _EPS:
        if abs(delta) < _EPS:
            return 0.0
        return float(np.sign(delta) * np.inf)
    return float(delta / sigma)


def estimate_ood_distribution(
    reference_activations,
    *,
    shrinkage: float = 0.05,
    ridge: float = 1e-6,
) -> OODDistribution:
    """Estimate a numerically stable Gaussian reference for Mahalanobis distance."""
    ref = _as_2d("reference_activations", reference_activations)
    if not (0.0 <= shrinkage <= 1.0):
        raise ValueError("shrinkage must be in [0, 1]")
    if ridge < 0.0:
        raise ValueError("ridge must be >= 0")

    mean = ref.mean(axis=0)
    centered = ref - mean
    # population covariance for a stable reference estimate
    cov = (centered.T @ centered) / max(ref.shape[0], 1)
    trace = float(np.trace(cov))
    d = cov.shape[0]
    target = (trace / max(d, 1)) * np.eye(d, dtype=np.float64)
    shrunk = (1.0 - shrinkage) * cov + shrinkage * target
    reg = shrunk + ridge * np.eye(d, dtype=np.float64)
    precision = np.linalg.pinv(reg, hermitian=True)
    return OODDistribution(
        mean=mean,
        covariance=reg,
        precision=precision,
        shrinkage=float(shrinkage),
        ridge=float(ridge),
        n_obs=int(ref.shape[0]),
    )


def whitened_mahalanobis(residual_activations, dist: OODDistribution) -> np.ndarray:
    """Per-item whitened Mahalanobis distance under the reference distribution."""
    acts = _as_2d("residual_activations", residual_activations)
    if acts.shape[1] != dist.mean.shape[0]:
        raise ValueError("activation dim mismatch with distribution mean")
    delta = acts - dist.mean[None, :]
    sq = np.einsum("ni,ij,nj->n", delta, dist.precision, delta, optimize=True)
    sq = np.clip(sq, a_min=0.0, a_max=None)
    return np.sqrt(sq)


def activation_norm_inflation(
    steered_residual_activations,
    baseline_residual_activations,
) -> np.ndarray:
    """Per-item norm inflation ratio: ||steered|| / ||baseline||."""
    steered = _as_2d("steered_residual_activations", steered_residual_activations)
    baseline = _as_2d("baseline_residual_activations", baseline_residual_activations)
    if steered.shape != baseline.shape:
        raise ValueError("steered and baseline residual arrays must have same shape")
    steered_norm = np.linalg.norm(steered, axis=1)
    baseline_norm = np.linalg.norm(baseline, axis=1)
    return steered_norm / np.maximum(baseline_norm, _EPS)


def per_item_ood_stats(
    steered_residual_activations,
    baseline_residual_activations,
    reference_activations,
    *,
    shrinkage: float = 0.05,
    ridge: float = 1e-6,
) -> tuple[np.ndarray, np.ndarray]:
    """Return per-item (mahalanobis_distance, norm_inflation)."""
    dist = estimate_ood_distribution(
        reference_activations, shrinkage=shrinkage, ridge=ridge
    )
    maha = whitened_mahalanobis(steered_residual_activations, dist)
    infl = activation_norm_inflation(
        steered_residual_activations, baseline_residual_activations
    )
    return maha, infl


def bootstrap_spearman(
    off_manifold_distance,
    delta_outcome,
    *,
    b: int = 10000,
    ci_level: float = HM_CI_LEVEL,
    seed: int = 0,
    correlate_with_harm: bool = True,
) -> SpearmanBootstrap:
    """Item-level paired bootstrap Spearman rho.

    `delta_outcome` is steer - baseline. For H-M, we correlate distance against
    `-delta_outcome` (harm) so larger means worse outcome.
    """
    x = _as_1d("off_manifold_distance", off_manifold_distance)
    d = _as_1d("delta_outcome", delta_outcome)
    if x.size != d.size:
        raise ValueError("off_manifold_distance and delta_outcome length mismatch")
    if x.size < 2:
        raise ValueError("need at least 2 items")
    if b < 1:
        raise ValueError("b must be >= 1")
    if not (0.0 < ci_level < 1.0):
        raise ValueError("ci_level must be in (0, 1)")

    y = -d if correlate_with_harm else d
    rho = _spearman_rho(x, y)

    rng = np.random.default_rng(seed)
    n = x.size
    idx = rng.integers(0, n, size=(b, n))
    boot = np.empty(b, dtype=np.float64)
    for i in range(b):
        boot[i] = _spearman_rho(x[idx[i]], y[idx[i]])

    lo_pct = 100.0 * (1.0 - ci_level) / 2.0
    hi_pct = 100.0 * (1.0 + ci_level) / 2.0
    return SpearmanBootstrap(
        rho=float(rho),
        ci_lo=float(np.percentile(boot, lo_pct)),
        ci_hi=float(np.percentile(boot, hi_pct)),
        ci_level=float(ci_level),
        b=int(b),
        seed=int(seed),
    )


def hm_cell_result(
    cell: str,
    off_manifold_distance,
    delta_outcome,
    *,
    rho_threshold: float = HM_SPEARMAN_THRESHOLD,
    b: int = 10000,
    ci_level: float = HM_CI_LEVEL,
    seed: int = 0,
) -> HMCellResult:
    """Evaluate one cell against the frozen H-M per-cell threshold."""
    s = bootstrap_spearman(
        off_manifold_distance,
        delta_outcome,
        b=b,
        ci_level=ci_level,
        seed=seed,
        correlate_with_harm=True,
    )
    ci_ok = s.ci_excludes_zero()
    passed = bool((s.rho >= rho_threshold) and ci_ok)
    return HMCellResult(
        cell=str(cell),
        rho=s.rho,
        ci_lo=s.ci_lo,
        ci_hi=s.ci_hi,
        threshold=float(rho_threshold),
        ci_excludes_zero=ci_ok,
        passed=passed,
    )


def hm_arm_verdict(
    per_cell: Mapping[str, tuple[Sequence[float], Sequence[float]]],
    *,
    rho_threshold: float = HM_SPEARMAN_THRESHOLD,
    min_required: int = HM_REQUIRED_PASS_CELLS,
    total_cells: int = HM_TOTAL_CELLS,
    b: int = 10000,
    ci_level: float = HM_CI_LEVEL,
    seed: int = 0,
) -> HMArmVerdict:
    """Aggregate the frozen H-M verdict: pass in >=3/4 cells."""
    cells: Dict[str, HMCellResult] = {}
    for i, (name, (dist, delta)) in enumerate(sorted(per_cell.items())):
        cells[name] = hm_cell_result(
            name,
            dist,
            delta,
            rho_threshold=rho_threshold,
            b=b,
            ci_level=ci_level,
            seed=seed + i,
        )
    passed_cells = sum(1 for c in cells.values() if c.passed)
    supported = bool(passed_cells >= min_required)
    if total_cells < 1:
        raise ValueError("total_cells must be >= 1")
    return HMArmVerdict(
        passed_cells=int(passed_cells),
        total_cells=int(total_cells),
        min_required=int(min_required),
        supported=supported,
        cells=cells,
    )


def c1_null_relative_effect(
    prompt_reach: float,
    pole_reach: float,
    random_null_prompt_reaches: Sequence[float],
    prompt_null_prompt_reaches: Sequence[float],
) -> C1NullRelativeEffect:
    """Null-relative C1 effect size from prompt/pole reach quantities."""
    observed = reach_fraction(float(prompt_reach), float(pole_reach))
    rnd = _as_1d("random_null_prompt_reaches", random_null_prompt_reaches)
    prm = _as_1d("prompt_null_prompt_reaches", prompt_null_prompt_reaches)
    rnd_ratio = rnd / float(pole_reach)
    prm_ratio = prm / float(pole_reach)

    rnd_mean = float(rnd_ratio.mean())
    prm_mean = float(prm_ratio.mean())
    rnd_delta = observed - rnd_mean
    prm_delta = observed - prm_mean
    return C1NullRelativeEffect(
        observed_ratio=float(observed),
        random_null_mean_ratio=rnd_mean,
        prompt_null_mean_ratio=prm_mean,
        random_null_delta=float(rnd_delta),
        prompt_null_delta=float(prm_delta),
        random_null_cohens_d=_cohens_d_vs_null(observed, rnd_ratio),
        prompt_null_cohens_d=_cohens_d_vs_null(observed, prm_ratio),
        random_null_uplift=float(observed / max(abs(rnd_mean), _EPS)),
        prompt_null_uplift=float(observed / max(abs(prm_mean), _EPS)),
    )


def summarize_c1_layer_norm_sensitivity(
    points: Sequence[C1SensitivityPoint],
) -> C1SensitivitySummary:
    """Summarize layer/norm sensitivity scan over null-relative C1 effects."""
    if not points:
        raise ValueError("points must be non-empty")
    eff = np.asarray([p.combined_effect for p in points], dtype=np.float64)
    per_layer: Dict[int, list[float]] = {}
    per_norm: Dict[str, list[float]] = {}
    for p in points:
        per_layer.setdefault(int(p.layer), []).append(p.combined_effect)
        key = f"{float(p.norm_scale):.6g}"
        per_norm.setdefault(key, []).append(p.combined_effect)
    return C1SensitivitySummary(
        n_points=len(points),
        mean_combined_effect=float(eff.mean()),
        min_combined_effect=float(eff.min()),
        max_combined_effect=float(eff.max()),
        positive_fraction=float(np.mean(eff > 0.0)),
        per_layer_mean_effect={k: float(np.mean(v)) for k, v in sorted(per_layer.items())},
        per_norm_mean_effect={k: float(np.mean(v)) for k, v in sorted(per_norm.items())},
    )
