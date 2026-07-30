"""E-0012 non-trained button families (§3-B) — direction derivation ONLY.

FROZEN specification source: prereg-e0012-verified-control-button-DRAFT.md §3 + §3-B.

Three pre-registered non-trained button families for the Calibration
(uncertainty_awareness) axis:

  BTN-CAL-PROBE
      Direction: linear probe weight vector from cross-entropy training on synthetic
      confidence-verbalization pairs (TriviaQA-train, seed=42, 100 high-conf +
      100 low-conf).  Labels encode expressed verbal confidence (0.9 vs 0.1) —
      NOT behavioral correctness outcomes from E-0005/E-0006.
      Non-trained: pair labels are surface-linguistic (verbalized confidence level),
      not behavioral-outcome labels from the adjudication pool distribution.

  BTN-CAL-LOGIT-MARGIN
      Direction: leading PCA eigenvector of the matrix of
      (top-1 logit − top-2 logit) activation differences across calibration items.
      Fully non-trained: PCA of a geometric quantity, no behavioral labels.

  BTN-CAL-CONTRA-REEXTRACT
      Direction: CAA mean-difference from E-0006 DEV items sorted by
      mean(1-Brier) at baseline: top-40 positive, bottom-40 negative.
      Pair selection rule is pre-specified and deterministic (sort by baseline
      calibration score, tie-break by item index).
      Non-trained: pair selection is deterministic from a PRE-SPECIFIED rule,
      direction is a mean-activation difference NOT optimized toward behavioral
      outcomes.

IMPORTANT: On CPU / no-GPU (synthetic backend), the direction vectors are
derived from SYNTHETIC activations (seeded random vectors) so the full harness
runs offline. The GPU path must call the real activation provider.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

# --------------------------------------------------------------------------- #
# Button family identifiers (frozen)
# --------------------------------------------------------------------------- #
BTN_PROBE = "BTN-CAL-PROBE"
BTN_LOGIT_MARGIN = "BTN-CAL-LOGIT-MARGIN"
BTN_CONTRA = "BTN-CAL-CONTRA-REEXTRACT"

ALL_BUTTON_FAMILIES: Tuple[str, ...] = (BTN_PROBE, BTN_LOGIT_MARGIN, BTN_CONTRA)

# Pre-registered constants for BTN-CAL-PROBE synthetic pair construction (§3-B-1)
PROBE_SYNTHETIC_SEED: int = 42
PROBE_N_HIGH: int = 100
PROBE_N_LOW: int = 100
PROBE_HIGH_CONF: float = 0.9
PROBE_LOW_CONF: float = 0.1

# Pre-registered constants for BTN-CAL-CONTRA-REEXTRACT (§3-B-2)
CONTRA_N_POSITIVE: int = 40
CONTRA_N_NEGATIVE: int = 40


@dataclass
class ButtonDirection:
    """A derived steering direction for a button family at a target layer."""
    family: str           # one of ALL_BUTTON_FAMILIES
    layer: int
    direction: np.ndarray  # unit-norm vector in hidden-state space
    derivation_hash: str  # SHA-256 hex of derivation parameters (reproducibility)
    notes: str = ""

    def __post_init__(self):
        norm = float(np.linalg.norm(self.direction))
        if norm < 1e-12:
            raise ValueError(f"ButtonDirection {self.family} has near-zero direction vector")
        self.direction = self.direction / norm  # ensure unit norm

    @property
    def is_unit(self) -> bool:
        return abs(float(np.linalg.norm(self.direction)) - 1.0) < 1e-6


def _derivation_hash(*args) -> str:
    """Stable SHA-256 fingerprint of derivation parameters."""
    key = "|".join(str(a) for a in args)
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


# --------------------------------------------------------------------------- #
# BTN-CAL-PROBE (§3-B-1)
# --------------------------------------------------------------------------- #
def _high_conf_template(q: str, a: str) -> str:
    return (
        f"Question: {q}. Answer: {a}. "
        f"I am very confident in this answer. My confidence is {PROBE_HIGH_CONF}."
    )


def _low_conf_template(q: str, a: str) -> str:
    return (
        f"Question: {q}. Answer: {a}. "
        f"I am not very sure about this. My confidence is {PROBE_LOW_CONF}."
    )


def build_probe_synthetic_pairs(
    triviaqa_train_items: Sequence[Dict],
    seed: int = PROBE_SYNTHETIC_SEED,
    n_high: int = PROBE_N_HIGH,
    n_low: int = PROBE_N_LOW,
) -> Tuple[List[str], List[int]]:
    """Build synthetic pairs for BTN-CAL-PROBE from TriviaQA-train items.

    Returns (texts, labels) where labels ∈ {0=low-conf, 1=high-conf}.
    Labels encode expressed verbal confidence ONLY, NOT behavioral correctness.
    This satisfies §3-B-1 independence from E-0005/E-0006 behavioral outcomes.
    """
    items = list(triviaqa_train_items)
    rng = np.random.default_rng(seed)
    total_needed = n_high + n_low
    if len(items) < total_needed:
        raise ValueError(
            f"Need {total_needed} TriviaQA-train items; only {len(items)} provided."
        )
    idx = rng.permutation(len(items))[:total_needed].tolist()
    high_items = [items[i] for i in idx[:n_high]]
    low_items = [items[i] for i in idx[n_high:]]

    texts: List[str] = []
    labels: List[int] = []
    for it in high_items:
        q = str(it.get("prompt", it.get("question", "")))
        a = str(it.get("answer", ""))
        texts.append(_high_conf_template(q, a))
        labels.append(1)
    for it in low_items:
        q = str(it.get("prompt", it.get("question", "")))
        a = str(it.get("answer", ""))
        texts.append(_low_conf_template(q, a))
        labels.append(0)
    return texts, labels


def derive_probe_direction_synthetic(
    layer: int,
    hidden_dim: int,
    seed: int = PROBE_SYNTHETIC_SEED,
) -> ButtonDirection:
    """Derive BTN-CAL-PROBE direction synthetically (no GPU).

    On real hardware this would be: get activations for synthetic pairs at
    ``layer``, train a logistic probe, return the weight vector.  For offline
    smoke this produces a reproducible pseudo-direction via seeded random
    projection — sufficient for pipeline validation.
    """
    rng = np.random.default_rng(seed + layer)
    direction = rng.standard_normal(hidden_dim)
    return ButtonDirection(
        family=BTN_PROBE,
        layer=layer,
        direction=direction,
        derivation_hash=_derivation_hash(BTN_PROBE, layer, hidden_dim, seed),
        notes=(
            "SYNTHETIC (offline): random unit vector used as stand-in for real "
            "probe direction. Real GPU path trains logistic probe on §3-B-1 pairs."
        ),
    )


def derive_probe_direction_real(
    layer: int,
    activation_provider,
    triviaqa_train_items: Sequence[Dict],
    seed: int = PROBE_SYNTHETIC_SEED,
    n_high: int = PROBE_N_HIGH,
    n_low: int = PROBE_N_LOW,
) -> ButtonDirection:
    """Derive BTN-CAL-PROBE direction on real GPU (A800 only).

    Trains a logistic probe on synthetic pair activations at ``layer``.
    ``activation_provider`` must expose ``get_activations(texts, layer) -> np.ndarray``.
    """
    try:
        from sklearn.linear_model import LogisticRegression  # noqa: PLC0415
    except ImportError as exc:
        raise NotImplementedError(
            "derive_probe_direction_real needs scikit-learn. "
            "Install: pip install scikit-learn"
        ) from exc
    texts, labels = build_probe_synthetic_pairs(
        triviaqa_train_items, seed=seed, n_high=n_high, n_low=n_low
    )
    acts = activation_provider.get_activations(texts, layer)  # [N, hidden_dim]
    clf = LogisticRegression(max_iter=200, random_state=seed)
    clf.fit(acts, labels)
    direction = clf.coef_[0]
    return ButtonDirection(
        family=BTN_PROBE,
        layer=layer,
        direction=direction,
        derivation_hash=_derivation_hash(
            BTN_PROBE, layer, acts.shape, seed, n_high, n_low
        ),
        notes=(
            "Real GPU probe direction: logistic regression on "
            f"{n_high} high-conf + {n_low} low-conf synthetic pairs at layer={layer}."
        ),
    )


# --------------------------------------------------------------------------- #
# BTN-CAL-LOGIT-MARGIN (PCA of Δlogit-margin activations)
# --------------------------------------------------------------------------- #
def derive_logit_margin_direction_synthetic(
    layer: int,
    hidden_dim: int,
    seed: int = 99,
) -> ButtonDirection:
    """Derive BTN-CAL-LOGIT-MARGIN direction synthetically (no GPU).

    Real path: collect (top-1 logit − top-2 logit) activation differences over
    calibration items at ``layer``, take leading PCA eigenvector.  Offline smoke
    uses seeded random projection.
    """
    rng = np.random.default_rng(seed + layer + 1000)
    direction = rng.standard_normal(hidden_dim)
    return ButtonDirection(
        family=BTN_LOGIT_MARGIN,
        layer=layer,
        direction=direction,
        derivation_hash=_derivation_hash(BTN_LOGIT_MARGIN, layer, hidden_dim, seed),
        notes=(
            "SYNTHETIC (offline): random unit vector. Real GPU path: PCA of "
            "Δlogit-margin activation matrix at the target layer."
        ),
    )


def derive_logit_margin_direction_real(
    layer: int,
    activation_provider,
    calibration_items: Sequence[Dict],
) -> ButtonDirection:
    """Derive BTN-CAL-LOGIT-MARGIN direction on real GPU (A800 only).

    Collects per-item (top-1 logit − top-2 logit) hidden-state differences at
    ``layer`` and returns the leading PCA eigenvector.
    """
    texts = [str(it.get("prompt", "")) for it in calibration_items]
    delta_acts = activation_provider.get_logit_margin_activations(texts, layer)
    _, _, Vt = np.linalg.svd(delta_acts, full_matrices=False)
    direction = Vt[0]
    return ButtonDirection(
        family=BTN_LOGIT_MARGIN,
        layer=layer,
        direction=direction,
        derivation_hash=_derivation_hash(BTN_LOGIT_MARGIN, layer, len(texts)),
        notes=f"Real GPU: leading PCA of Δlogit-margin acts at layer={layer}.",
    )


# --------------------------------------------------------------------------- #
# BTN-CAL-CONTRA-REEXTRACT (§3-B-2)
# --------------------------------------------------------------------------- #
def select_contra_pairs(
    e0006_dev_items: Sequence[Dict],
    n_positive: int = CONTRA_N_POSITIVE,
    n_negative: int = CONTRA_N_NEGATIVE,
) -> Tuple[List[Dict], List[Dict]]:
    """Pre-specified deterministic pair selection rule for BTN-CAL-CONTRA-REEXTRACT.

    Pre-registered rule (§3-B-2):
      - Score: mean(1−Brier) over k=5 unsteered baseline samples per item
      - Sort descending by score; tie-break by item index ascending
      - Positive pairs: top-{n_positive} items (best-calibrated at baseline)
      - Negative pairs: bottom-{n_negative} items (worst-calibrated at baseline)

    Each item in ``e0006_dev_items`` must have a 'baseline_score' key
    (mean 1−Brier over unsteered k=5 samples) and an 'id' key.

    Falls back to top-half / bottom-half if fewer than n_positive + n_negative
    items are available (§3-B-2 fallback rule).
    """
    items = list(e0006_dev_items)
    n = len(items)
    total_needed = n_positive + n_negative

    if n < total_needed:
        # Fallback: top-half / bottom-half (round down for positive)
        n_pos_fb = n // 2
        n_neg_fb = n - n_pos_fb
        n_positive = n_pos_fb
        n_negative = n_neg_fb

    # Deterministic sort: descending score, ascending item index for ties
    scored = [
        (float(it.get("baseline_score", 0.0)), i, it)
        for i, it in enumerate(items)
    ]
    scored.sort(key=lambda x: (-x[0], x[1]))  # ↓ score, ↑ index

    positives = [it for _, _, it in scored[:n_positive]]
    negatives = [it for _, _, it in scored[n - n_negative:]]
    return positives, negatives


def derive_contra_direction_synthetic(
    layer: int,
    hidden_dim: int,
    e0006_dev_items: Optional[Sequence[Dict]] = None,
    seed: int = 77,
) -> ButtonDirection:
    """Derive BTN-CAL-CONTRA-REEXTRACT direction synthetically (no GPU).

    Real path: collect activations for positive/negative pairs from E-0006 DEV,
    compute mean difference.  Offline smoke uses seeded random projection.
    """
    rng = np.random.default_rng(seed + layer + 2000)
    direction = rng.standard_normal(hidden_dim)
    n_pos = len(e0006_dev_items) // 2 if e0006_dev_items else CONTRA_N_POSITIVE
    return ButtonDirection(
        family=BTN_CONTRA,
        layer=layer,
        direction=direction,
        derivation_hash=_derivation_hash(BTN_CONTRA, layer, hidden_dim, seed, n_pos),
        notes=(
            "SYNTHETIC (offline): random unit vector. Real GPU path: CAA "
            "mean-diff of activations from pre-selected top-40/bottom-40 E-0006 "
            "DEV pairs at layer={layer}."
        ),
    )


def derive_contra_direction_real(
    layer: int,
    activation_provider,
    e0006_dev_items: Sequence[Dict],
    n_positive: int = CONTRA_N_POSITIVE,
    n_negative: int = CONTRA_N_NEGATIVE,
) -> ButtonDirection:
    """Derive BTN-CAL-CONTRA-REEXTRACT direction on real GPU (A800 only).

    Computes CAA mean-difference from pre-specified E-0006 DEV pairs at ``layer``.
    The pair selection is deterministic (pre-committed rule §3-B-2).
    Direction = mean(activations[positive]) − mean(activations[negative]).
    """
    positives, negatives = select_contra_pairs(e0006_dev_items, n_positive, n_negative)
    pos_texts = [str(it.get("prompt", "")) for it in positives]
    neg_texts = [str(it.get("prompt", "")) for it in negatives]
    pos_acts = activation_provider.get_activations(pos_texts, layer)
    neg_acts = activation_provider.get_activations(neg_texts, layer)
    direction = pos_acts.mean(axis=0) - neg_acts.mean(axis=0)
    return ButtonDirection(
        family=BTN_CONTRA,
        layer=layer,
        direction=direction,
        derivation_hash=_derivation_hash(
            BTN_CONTRA, layer, len(positives), len(negatives)
        ),
        notes=(
            f"Real GPU CAA mean-diff: {len(positives)} positive − {len(negatives)} "
            f"negative pairs from E-0006 DEV at layer={layer}."
        ),
    )


# --------------------------------------------------------------------------- #
# Synthetic direction factory (dispatch by family)
# --------------------------------------------------------------------------- #
def derive_direction_synthetic(
    family: str,
    layer: int,
    hidden_dim: int,
    e0006_dev_items: Optional[Sequence[Dict]] = None,
) -> ButtonDirection:
    """Dispatch to the appropriate synthetic direction derivation function."""
    if family == BTN_PROBE:
        return derive_probe_direction_synthetic(layer, hidden_dim)
    if family == BTN_LOGIT_MARGIN:
        return derive_logit_margin_direction_synthetic(layer, hidden_dim)
    if family == BTN_CONTRA:
        return derive_contra_direction_synthetic(layer, hidden_dim, e0006_dev_items)
    raise ValueError(f"unknown button family: {family!r}")


def all_directions_for_layer(
    layer: int,
    hidden_dim: int,
    e0006_dev_items: Optional[Sequence[Dict]] = None,
    families: Sequence[str] = ALL_BUTTON_FAMILIES,
) -> List[ButtonDirection]:
    """Derive synthetic directions for all families at a given layer."""
    return [
        derive_direction_synthetic(fam, layer, hidden_dim, e0006_dev_items)
        for fam in families
    ]
