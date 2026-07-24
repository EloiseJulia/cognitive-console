"""ITI steering-vector extraction (probe direction + sigma-scaled intervention).

Mechanism contrast with CAA
---------------------------
CAA uses a *class-mean difference* direction (mean(pos) - mean(neg)); ITI uses a
*discriminative probe* direction fitted by logistic regression. They are related
but methodologically orthogonal:

* **CAA** asks: "where are the class centroids separated?"
* **ITI** asks: "which linear direction best predicts class identity?"

For inference-time intervention we keep the same residual-addition hook surface as
CAA (`h -> h + alpha * u`) but reinterpret `alpha` as a multiple of the activation
standard deviation along the probe direction (`sigma`), i.e. effective magnitude
`alpha * sigma`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from ..metrics import random_null_baseline
from .extract import LayerSelection, min_layer_for_depth, select_nondegenerate_layer

_EPS = 1e-12


@dataclass(frozen=True)
class ITILayerDiagnostics:
    layer: int
    separation: float
    probe_norm: float
    sigma: float
    mean_pos_proj: float
    mean_neg_proj: float
    pooled_std: float
    objective: float
    grad_norm: float
    n_pos: int
    n_neg: int


@dataclass
class ITIResult:
    axis: str
    layer: int
    vector: np.ndarray
    direction: np.ndarray
    sigma: float
    selection: str
    per_layer: Dict[int, ITILayerDiagnostics] = field(default_factory=dict)
    layer_selection: Optional[LayerSelection] = None

    def to_summary(self) -> Dict[str, object]:
        return {
            "axis": self.axis,
            "selected_layer": self.layer,
            "selection": self.selection,
            "probe_norm": float(np.linalg.norm(self.vector)),
            "sigma": float(self.sigma),
            "separation_by_layer": {
                str(ell): d.separation for ell, d in sorted(self.per_layer.items())
            },
        }


def sigma_scaled_alpha(alpha: float, sigma: float) -> float:
    """Convert an alpha-in-sigma-units coefficient into absolute residual magnitude."""
    sigma = float(sigma)
    if sigma < 0.0:
        raise ValueError("sigma must be >= 0")
    return float(alpha) * sigma


def _sigmoid(z: np.ndarray) -> np.ndarray:
    z = np.clip(z, -60.0, 60.0)
    return 1.0 / (1.0 + np.exp(-z))


def _pooled_std(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = len(a), len(b)
    if na + nb - 2 <= 0:
        return float(np.sqrt((a.var() + b.var()) / 2.0))
    ss = (na - 1) * a.var(ddof=1) + (nb - 1) * b.var(ddof=1)
    return float(np.sqrt(ss / (na + nb - 2)))


def _fit_logistic_probe(
    pos_acts: np.ndarray,
    neg_acts: np.ndarray,
    l2: float,
    max_iter: int,
    lr: float,
    tol: float,
) -> Tuple[np.ndarray, float, float, float]:
    """Fit a binary logistic probe and return raw-space (w, objective, grad_norm)."""
    x_pos = np.asarray(pos_acts, dtype=np.float64)
    x_neg = np.asarray(neg_acts, dtype=np.float64)
    x = np.vstack([x_pos, x_neg])
    y = np.concatenate([np.ones(len(x_pos)), np.zeros(len(x_neg))])
    if x.ndim != 2 or len(x) == 0:
        raise ValueError("invalid activations for probe fit")

    feat_mu = x.mean(axis=0)
    feat_std = x.std(axis=0)
    feat_std = np.where(feat_std < _EPS, 1.0, feat_std)
    xz = (x - feat_mu) / feat_std

    w = np.zeros(xz.shape[1], dtype=np.float64)
    p0 = np.clip(y.mean(), 1e-5, 1.0 - 1e-5)
    b = float(np.log(p0 / (1.0 - p0)))
    l2 = float(max(l2, 0.0))
    n = float(len(y))

    objective = float("inf")
    grad_norm = float("inf")
    for _ in range(int(max_iter)):
        logits = xz @ w + b
        probs = _sigmoid(logits)
        err = probs - y
        grad_w = (xz.T @ err) / n + l2 * w
        grad_b = float(err.mean())
        grad_norm = float(np.sqrt(np.dot(grad_w, grad_w) + grad_b * grad_b))
        w = w - float(lr) * grad_w
        b = b - float(lr) * grad_b
        probs = np.clip(probs, 1e-8, 1.0 - 1e-8)
        ce = -np.mean(y * np.log(probs) + (1.0 - y) * np.log(1.0 - probs))
        new_obj = float(ce + 0.5 * l2 * np.dot(w, w))
        if abs(objective - new_obj) <= tol and grad_norm <= np.sqrt(tol):
            objective = new_obj
            break
        objective = new_obj

    w_raw = w / feat_std
    return w_raw, objective, grad_norm, b - float(np.dot(feat_mu / feat_std, w))


def _probe_diagnostics(
    pos_acts: np.ndarray,
    neg_acts: np.ndarray,
    layer: int,
    probe_l2: float,
    max_iter: int,
    lr: float,
    tol: float,
) -> Tuple[np.ndarray, np.ndarray, ITILayerDiagnostics]:
    if pos_acts.ndim != 2 or neg_acts.ndim != 2:
        raise ValueError("activations must be 2-D [n, d]")
    if pos_acts.shape[1] != neg_acts.shape[1]:
        raise ValueError("pos/neg activation dim mismatch")
    if len(pos_acts) == 0 or len(neg_acts) == 0:
        raise ValueError("need at least one pos and one neg activation")

    w_raw, objective, grad_norm, _ = _fit_logistic_probe(
        pos_acts, neg_acts, l2=probe_l2, max_iter=max_iter, lr=lr, tol=tol
    )
    norm = float(np.linalg.norm(w_raw))
    direction = w_raw / (norm if norm > _EPS else 1.0)
    pos_proj = pos_acts @ direction
    neg_proj = neg_acts @ direction
    pooled = _pooled_std(pos_proj, neg_proj)
    mean_pos = float(pos_proj.mean())
    mean_neg = float(neg_proj.mean())
    sep = (mean_pos - mean_neg) / (pooled if pooled > _EPS else _EPS)
    sigma = float(np.std(np.concatenate([pos_proj, neg_proj]), ddof=1))
    diag = ITILayerDiagnostics(
        layer=layer,
        separation=float(sep),
        probe_norm=norm,
        sigma=sigma,
        mean_pos_proj=mean_pos,
        mean_neg_proj=mean_neg,
        pooled_std=pooled,
        objective=float(objective),
        grad_norm=float(grad_norm),
        n_pos=len(pos_acts),
        n_neg=len(neg_acts),
    )
    return w_raw, direction, diag


def extract_iti(
    provider,
    axis: str,
    pos_texts: Sequence[str],
    neg_texts: Sequence[str],
    layers: Sequence[int] | None = None,
    selection: str = "nondegenerate",
    *,
    neutral_texts: Sequence[str] | None = None,
    min_layer: Optional[int] = None,
    min_depth_frac: float = 0.2,
    top_k: int = 3,
    n_null: int = 2000,
    null_seed: int = 0,
    probe_l2: float = 1e-2,
    max_iter: int = 300,
    lr: float = 0.25,
    tol: float = 1e-7,
) -> ITIResult:
    """Extract ITI probe directions, then pick one layer for residual steering.

    If `selection="nondegenerate"`, layer selection follows the same rule as C1/CAA:
    choose best separation among layers that clear depth floor + pole reach + null.
    """
    if selection not in {"separation", "nondegenerate"}:
        raise ValueError(f"unsupported selection criterion: {selection!r}")
    if layers is None:
        layers = provider.available_layers()
    layers = [int(x) for x in layers]
    if not layers:
        raise ValueError("no candidate layers")

    pos_by_layer: Dict[int, np.ndarray] = {}
    neg_by_layer: Dict[int, np.ndarray] = {}
    vec_by_layer: Dict[int, np.ndarray] = {}
    dir_by_layer: Dict[int, np.ndarray] = {}
    per_layer: Dict[int, ITILayerDiagnostics] = {}

    for ell in layers:
        pos = provider.get_activations(pos_texts, ell).astype(np.float64)
        neg = provider.get_activations(neg_texts, ell).astype(np.float64)
        vec, direction, diag = _probe_diagnostics(
            pos, neg, ell, probe_l2=probe_l2, max_iter=max_iter, lr=lr, tol=tol
        )
        pos_by_layer[ell] = pos
        neg_by_layer[ell] = neg
        vec_by_layer[ell] = vec
        dir_by_layer[ell] = direction
        per_layer[ell] = diag

    layer_selection: Optional[LayerSelection] = None
    if selection == "nondegenerate":
        if not neutral_texts:
            raise ValueError("neutral_texts are required for nondegenerate selection")
        if min_layer is None:
            min_layer = min_layer_for_depth(max(layers), min_depth_frac=min_depth_frac)
        sep_by = {ell: per_layer[ell].separation for ell in layers}
        pole_by: Dict[int, float] = {}
        null_by: Dict[int, float] = {}
        for ell in layers:
            neutral = provider.get_activations(neutral_texts, ell).astype(np.float64)
            displacement = pos_by_layer[ell].mean(axis=0) - neutral.mean(axis=0)
            pole = float(np.dot(displacement, dir_by_layer[ell]))
            null_dist = random_null_baseline(
                displacement, n_samples=int(n_null), seed=int(null_seed) + int(ell)
            )
            pole_by[ell] = pole
            null_by[ell] = float(np.percentile(null_dist, 95))
        layer_selection = select_nondegenerate_layer(
            sep_by, pole_by, null_by, min_layer=int(min_layer), top_k=int(top_k)
        )
        if layer_selection.chosen is None:
            raise ValueError("ITI selection found no non-degenerate layer")
        best_layer = int(layer_selection.chosen)
    else:
        best_layer = max(layers, key=lambda ell: (per_layer[ell].separation, -ell))

    chosen = per_layer[best_layer]
    direction = dir_by_layer[best_layer]
    sigma = float(chosen.sigma)
    return ITIResult(
        axis=axis,
        layer=best_layer,
        vector=vec_by_layer[best_layer],
        direction=direction,
        sigma=sigma,
        selection=selection,
        per_layer=per_layer,
        layer_selection=layer_selection,
    )
