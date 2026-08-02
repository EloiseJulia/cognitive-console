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
      Direction: CAA mean-difference from all 80 E-0006 uncertainty_awareness
      calibration items sorted by mean(1-Brier) at baseline: top-40 positive,
      bottom-40 negative.
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
import json
import os
import subprocess
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

from cognitive_console.steering.extract import mean_difference_vector

# --------------------------------------------------------------------------- #
# Button family identifiers (frozen)
# --------------------------------------------------------------------------- #
BTN_PROBE = "BTN-CAL-PROBE"
BTN_LOGIT_MARGIN = "BTN-CAL-LOGIT-MARGIN"
BTN_CONTRA = "BTN-CAL-CONTRA-REEXTRACT"

ALL_BUTTON_FAMILIES: Tuple[str, ...] = (BTN_PROBE, BTN_LOGIT_MARGIN, BTN_CONTRA)
CONSERVATIVE_BUTTON_FAMILIES: Tuple[str, ...] = (BTN_PROBE, BTN_CONTRA)

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
    provenance: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        norm = float(np.linalg.norm(self.direction))
        if norm < 1e-12:
            raise ValueError(f"ButtonDirection {self.family} has near-zero direction vector")
        self.direction = self.direction / norm  # ensure unit norm
        self.provenance = dict(self.provenance or {})
        self.provenance.setdefault("family", self.family)
        self.provenance.setdefault("layer", int(self.layer))
        self.provenance.setdefault("hidden_dim", int(self.direction.shape[0]))
        self.provenance.setdefault("vector_norm", float(np.linalg.norm(self.direction)))
        self.provenance.setdefault("vector_sha256", _vector_sha256(self.direction))
        self.provenance.setdefault("derivation_hash", self.derivation_hash)
        self.provenance.setdefault("notes", self.notes)

    @property
    def is_unit(self) -> bool:
        return abs(float(np.linalg.norm(self.direction)) - 1.0) < 1e-6


def _derivation_hash(*args) -> str:
    """Stable SHA-256 fingerprint of derivation parameters."""
    key = "|".join(
        json.dumps(a, sort_keys=True, default=str) if isinstance(a, (dict, list, tuple))
        else str(a)
        for a in args
    )
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def _git_commit() -> str:
    """Best-effort current git commit for provenance."""
    env = os.environ.get("COGNITIVE_CONSOLE_CODE_COMMIT")
    if env:
        return env
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "UNKNOWN"


def _provider_provenance(activation_provider) -> Dict[str, Any]:
    return {
        "model": str(getattr(activation_provider, "model_name", "UNKNOWN")),
        "dtype": str(getattr(activation_provider, "dtype", "UNKNOWN")),
        "device": str(getattr(activation_provider, "device", "UNKNOWN")),
        "activation_provider": type(activation_provider).__name__,
    }


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _vector_sha256(vec: np.ndarray) -> str:
    arr = np.asarray(vec, dtype=np.float32).ravel()
    return _sha256_bytes(arr.tobytes())


def _canonical_json_sha256(payload: Any) -> str:
    data = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return _sha256_bytes(data.encode("utf-8"))


def direction_provenance_records(
    directions_by_layer: Dict[int, Sequence[ButtonDirection]],
) -> List[Dict[str, Any]]:
    """Flatten direction provenance records for artifact persistence."""
    records: List[Dict[str, Any]] = []
    for layer in sorted(directions_by_layer):
        for bd in directions_by_layer[layer]:
            rec = dict(bd.provenance or {})
            rec.setdefault("family", bd.family)
            rec.setdefault("layer", int(bd.layer))
            rec.setdefault("method", "UNKNOWN")
            rec.setdefault("derivation_hash", bd.derivation_hash)
            rec.setdefault("hidden_dim", int(bd.direction.shape[0]))
            rec.setdefault("vector_norm", float(np.linalg.norm(bd.direction)))
            rec.setdefault("vector_sha256", _vector_sha256(bd.direction))
            records.append(rec)
    return records


def assert_real_direction_provenance(
    directions_by_layer: Dict[int, Sequence[ButtonDirection]],
) -> None:
    """Hard-fail if any HF-path direction is synthetic/random/non-real."""
    bad: List[str] = []
    for rec in direction_provenance_records(directions_by_layer):
        haystack = " ".join(
            str(rec.get(k, ""))
            for k in ("method", "source", "source_split", "derivation_function")
        )
        low = haystack.lower()
        if "synthetic" in low or "random" in low:
            bad.append(f"{rec.get('family')}@L{rec.get('layer')} method={rec.get('method')}")
        if str(rec.get("method", "")).lower() not in {"real_probe", "real_caa_mean_diff"}:
            bad.append(f"{rec.get('family')}@L{rec.get('layer')} method={rec.get('method')}")
        for required in ("vector_sha256", "source_artifact_sha256", "hyperparameters"):
            if not rec.get(required):
                bad.append(
                    f"{rec.get('family')}@L{rec.get('layer')} missing {required}"
                )
    if bad:
        raise RuntimeError(
            "REAL-NOT-SMOKE hard-fail: hf backend received non-real button "
            "directions: " + "; ".join(sorted(set(bad)))
        )


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


def _probe_selected_item_ids(
    triviaqa_train_items: Sequence[Dict],
    seed: int = PROBE_SYNTHETIC_SEED,
    n_high: int = PROBE_N_HIGH,
    n_low: int = PROBE_N_LOW,
) -> List[str]:
    items = list(triviaqa_train_items)
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(items))[: n_high + n_low].tolist()
    return [str(items[i].get("id", "")) for i in idx]


def _probe_source_artifact(
    texts: Sequence[str],
    labels: Sequence[int],
    source_ids: Sequence[str],
) -> Dict[str, Any]:
    return {
        "source_split": "TriviaQA-train",
        "source_item_ids": list(source_ids),
        "pair_texts": list(texts),
        "labels": [int(x) for x in labels],
        "label_semantics": "verbalized confidence 0.9 vs 0.1 only",
    }


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
        provenance={
            "method": "synthetic_random_probe",
            "source_split": "offline_synthetic",
            "derivation_function": "derive_probe_direction_synthetic",
            "code_commit": _git_commit(),
        },
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
    texts, labels = build_probe_synthetic_pairs(
        triviaqa_train_items, seed=seed, n_high=n_high, n_low=n_low
    )
    acts = activation_provider.get_activations(texts, layer)  # [N, hidden_dim]
    x = np.asarray(acts, dtype=np.float64)
    y = np.asarray(labels, dtype=np.float64)
    mu = x.mean(axis=0)
    sigma = x.std(axis=0)
    sigma[sigma < 1e-8] = 1.0
    xs = (x - mu) / sigma
    w = np.zeros(xs.shape[1], dtype=np.float64)
    b = 0.0
    n_iters = 800
    lr = 0.2
    l2 = 1e-4
    standardization = "zscore_train_pairs_sigma_floor_1e-8"
    for _ in range(n_iters):
        logits = np.clip(xs @ w + b, -40.0, 40.0)
        p = 1.0 / (1.0 + np.exp(-logits))
        err = p - y
        w -= lr * ((xs.T @ err) / len(y) + l2 * w)
        b -= lr * float(err.mean())
    direction = w / sigma
    source_ids = _probe_selected_item_ids(triviaqa_train_items, seed, n_high, n_low)
    source_artifact_sha256 = _canonical_json_sha256(
        _probe_source_artifact(texts, labels, source_ids)
    )
    deriv_hash = _derivation_hash(
        BTN_PROBE,
        layer,
        list(acts.shape),
        seed,
        n_high,
        n_low,
        source_ids,
        source_artifact_sha256,
        {"n_iters": n_iters, "lr": lr, "l2": l2, "standardization": standardization},
        _provider_provenance(activation_provider),
    )
    return ButtonDirection(
        family=BTN_PROBE,
        layer=layer,
        direction=direction,
        derivation_hash=deriv_hash,
        notes=(
            "Real GPU probe direction: logistic regression on "
            f"{n_high} high-conf + {n_low} low-conf synthetic pairs at layer={layer}."
        ),
        provenance={
            "method": "real_probe",
            "source_split": "TriviaQA-train",
            "source_item_ids": source_ids,
            "n_high": int(n_high),
            "n_low": int(n_low),
            "seed": int(seed),
            "source_artifact_sha256": source_artifact_sha256,
            "hyperparameters": {
                "seed": int(seed),
                "n_iters": int(n_iters),
                "lr": float(lr),
                "l2": float(l2),
                "standardization": standardization,
            },
            "label_semantics": "verbalized confidence 0.9 vs 0.1 only",
            "derivation_function": "derive_probe_direction_real",
            "code_commit": _git_commit(),
            **_provider_provenance(activation_provider),
        },
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
        provenance={
            "method": "synthetic_random_logit_margin",
            "source_split": "offline_synthetic",
            "derivation_function": "derive_logit_margin_direction_synthetic",
            "code_commit": _git_commit(),
        },
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
    e0006_items: Sequence[Dict],
    n_positive: int = CONTRA_N_POSITIVE,
    n_negative: int = CONTRA_N_NEGATIVE,
) -> Tuple[List[Dict], List[Dict]]:
    """Pre-specified deterministic pair selection rule for BTN-CAL-CONTRA-REEXTRACT.

    Manager-resolved A-lite rule:
      - Source: full E-0006 uncertainty_awareness calibration set (all 80 items)
      - Score: mean(1−Brier) over k=5 unsteered baseline samples per item
      - Sort descending by score; tie-break by item index ascending
      - Positive pairs: top-40 items (best-calibrated at baseline)
      - Negative pairs: bottom-40 items (worst-calibrated at baseline)

    Each item in ``e0006_items`` must have a 'baseline_score' key
    (mean 1−Brier over unsteered k=5 samples) and an 'id' key.
    """
    items = list(e0006_items)
    n = len(items)
    total_needed = n_positive + n_negative

    if n != total_needed:
        raise ValueError(
            f"BTN-CAL-CONTRA-REEXTRACT requires exactly {total_needed} E-0006 "
            f"uncertainty_awareness baseline-scored items; got {n}"
        )

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
    e0006_items: Optional[Sequence[Dict]] = None,
    seed: int = 77,
) -> ButtonDirection:
    """Derive BTN-CAL-CONTRA-REEXTRACT direction synthetically (no GPU).

    Real path: collect activations for positive/negative pairs from all-80 E-0006,
    compute mean difference.  Offline smoke uses seeded random projection.
    """
    rng = np.random.default_rng(seed + layer + 2000)
    direction = rng.standard_normal(hidden_dim)
    return ButtonDirection(
        family=BTN_CONTRA,
        layer=layer,
        direction=direction,
        derivation_hash=_derivation_hash(BTN_CONTRA, layer, hidden_dim, seed, CONTRA_N_POSITIVE),
        notes=(
            "SYNTHETIC (offline): random unit vector. Real GPU path: CAA "
            "mean-diff of activations from pre-selected top-40/bottom-40 E-0006 "
            "uncertainty_awareness calibration items at layer={layer}."
        ),
        provenance={
            "method": "synthetic_random_contra",
            "source_split": "offline_synthetic",
            "derivation_function": "derive_contra_direction_synthetic",
            "code_commit": _git_commit(),
        },
    )


def derive_contra_direction_real(
    layer: int,
    activation_provider,
    e0006_items: Sequence[Dict],
    n_positive: int = CONTRA_N_POSITIVE,
    n_negative: int = CONTRA_N_NEGATIVE,
) -> ButtonDirection:
    """Derive BTN-CAL-CONTRA-REEXTRACT direction on real GPU (A800 only).

    Computes CAA mean-difference from pre-specified E-0006 all-80 pairs at ``layer``.
    The pair selection is deterministic (pre-committed rule §3-B-2).
    Direction = mean(activations[positive]) − mean(activations[negative]).
    """
    positives, negatives = select_contra_pairs(e0006_items, n_positive, n_negative)
    pos_texts = [str(it.get("prompt", "")) for it in positives]
    neg_texts = [str(it.get("prompt", "")) for it in negatives]
    pos_acts = activation_provider.get_activations(pos_texts, layer)
    neg_acts = activation_provider.get_activations(neg_texts, layer)
    direction = mean_difference_vector(pos_acts, neg_acts)
    pos_ids = [str(it.get("id", "")) for it in positives]
    neg_ids = [str(it.get("id", "")) for it in negatives]
    source_artifact_sha256 = str(e0006_items[0].get("source_artifact_sha256", ""))
    deriv_hash = _derivation_hash(
        BTN_CONTRA,
        layer,
        pos_ids,
        neg_ids,
        [float(it.get("baseline_score", 0.0)) for it in positives + negatives],
        source_artifact_sha256,
        _provider_provenance(activation_provider),
    )
    return ButtonDirection(
        family=BTN_CONTRA,
        layer=layer,
        direction=direction,
        derivation_hash=deriv_hash,
        notes=(
            f"Real GPU CAA mean-diff: {len(positives)} positive − {len(negatives)} "
            f"negative pairs from all-80 E-0006 uncertainty_awareness items at layer={layer}."
        ),
        provenance={
            "method": "real_caa_mean_diff",
            "source_split": "E-0006 uncertainty_awareness all-80 baseline-scored calibration items",
            "positive_item_ids": pos_ids,
            "negative_item_ids": neg_ids,
            "n_positive": len(positives),
            "n_negative": len(negatives),
            "source_artifact_sha256": source_artifact_sha256,
            "hyperparameters": {
                "selection_rule": (
                    "rank all 80 E-0006 uncertainty_awareness items by baseline_score "
                    "descending; top40 positive, bottom40 negative; ties by item_index ascending"
                ),
                "n_positive": int(n_positive),
                "n_negative": int(n_negative),
                "tie_break": "item_index_ascending",
                "source_item_count": len(e0006_items),
            },
            "baseline_score_field": "baseline_score = unsteered baseline mean(1-Brier), k=5",
            "derivation_function": "derive_contra_direction_real",
            "code_commit": _git_commit(),
            **_provider_provenance(activation_provider),
        },
    )


def all_real_directions_for_layer(
    layer: int,
    activation_provider,
    triviaqa_train_items: Sequence[Dict],
    e0006_items: Sequence[Dict],
    families: Sequence[str] = CONSERVATIVE_BUTTON_FAMILIES,
) -> List[ButtonDirection]:
    """Derive the A-lite real E-0012 directions for one layer."""
    directions: List[ButtonDirection] = []
    for fam in families:
        if fam == BTN_PROBE:
            directions.append(
                derive_probe_direction_real(layer, activation_provider, triviaqa_train_items)
            )
        elif fam == BTN_CONTRA:
            directions.append(
                derive_contra_direction_real(layer, activation_provider, e0006_items)
            )
        else:
            raise ValueError(
                f"{fam!r} is not in the owner-approved A-lite real-direction family set"
            )
    return directions


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
