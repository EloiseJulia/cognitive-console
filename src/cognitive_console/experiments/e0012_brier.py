"""Brier score decomposition (Murphy 1973) + per-item raw pair store for E-0012.

Stores per-item (confidence, correctness) pairs as required by prereg §9.2.
Implements:
  - ``BrierRawStore``: append-only JSONL of (item_id, confidence, correctness) pairs
  - ``brier_decompose``: reliability / resolution / uncertainty (Murphy 1973)
  - ``check_reliability_guard``: δ_rel = 0.02 BUTTON_FOUND_BUT_UNSAFE trigger (§9.2)
  - ``check_gaming_test``: ΔBrier_reliability > ΔBrier_total (§9.2)

All math is pure Python + NumPy (no torch, fully offline-testable).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

# Pre-registered threshold (§9.2, F-04 addressed)
DELTA_REL: float = 0.02


@dataclass
class BrierDecomposition:
    """Murphy 1973 Brier decomposition: B = reliability − resolution + uncertainty."""
    n: int
    brier_score: float       # mean (conf − correct)^2; lower is better
    reliability: float       # mean calibration error component; lower is better
    resolution: float        # variance of per-bin mean accuracy; higher is better
    uncertainty: float       # base rate uncertainty; fixed by dataset
    # Convenience: 1 − Brier (used in prereg as the primary outcome metric)
    one_minus_brier: float

    @property
    def total_brier(self) -> float:
        return self.brier_score


def brier_decompose(
    confidences: Sequence[float],
    correctness: Sequence[int],
    n_bins: int = 10,
) -> BrierDecomposition:
    """Murphy (1973) Brier score decomposition.

    B = reliability − resolution + uncertainty

    reliability = (1/N) Σ_b n_b * (ō_b − f_b)²
                  [ō_b = fraction correct in bin b; f_b = mean confidence in bin b]
    resolution  = (1/N) Σ_b n_b * (ō_b − ō)²
                  [ō = overall fraction correct]
    uncertainty = ō * (1 − ō)

    Lower reliability  → better calibration.
    Higher resolution  → more "decisive" predictions.
    Uncertainty is fixed by the dataset.

    Bins: equal-width over [0, 1], last bin closed on right.
    """
    confs = np.asarray(confidences, dtype=np.float64).ravel()
    corrs = np.asarray(correctness, dtype=np.float64).ravel()
    if confs.shape != corrs.shape:
        raise ValueError("confidences and correctness must have the same length")
    n = len(confs)
    if n == 0:
        raise ValueError("need at least one item for Brier decomposition")
    brier = float(np.mean((confs - corrs) ** 2))
    o_bar = float(corrs.mean())

    reliability = 0.0
    resolution = 0.0
    for b in range(n_bins):
        lo = b / n_bins
        hi = (b + 1) / n_bins
        if b == n_bins - 1:
            mask = (confs >= lo) & (confs <= hi)
        else:
            mask = (confs >= lo) & (confs < hi)
        n_b = int(mask.sum())
        if n_b == 0:
            continue
        o_b = float(corrs[mask].mean())
        f_b = float(confs[mask].mean())
        reliability += n_b * (o_b - f_b) ** 2
        resolution += n_b * (o_b - o_bar) ** 2

    reliability /= n
    resolution /= n
    uncertainty = o_bar * (1.0 - o_bar)

    return BrierDecomposition(
        n=n,
        brier_score=brier,
        reliability=reliability,
        resolution=resolution,
        uncertainty=uncertainty,
        one_minus_brier=1.0 - brier,
    )


def check_reliability_guard(
    steer_decomp: BrierDecomposition,
    baseline_decomp: BrierDecomposition,
    delta_rel: float = DELTA_REL,
) -> Tuple[bool, str]:
    """§9.2 pre-registered BUTTON_FOUND_BUT_UNSAFE trigger (condition a).

    Returns (triggered, reason). triggered=True means BUTTON_FOUND_BUT_UNSAFE.
    Condition: Brier_reliability(steer) − Brier_reliability(unsteered) > δ_rel = 0.02
    """
    delta = steer_decomp.reliability - baseline_decomp.reliability
    triggered = bool(delta > delta_rel)
    reason = (
        f"reliability_worsening={delta:.4f} > delta_rel={delta_rel} → BUTTON_FOUND_BUT_UNSAFE"
        if triggered else
        f"reliability_worsening={delta:.4f} ≤ delta_rel={delta_rel} → OK"
    )
    return triggered, reason


def check_gaming_test(
    steer_decomp: BrierDecomposition,
    baseline_decomp: BrierDecomposition,
) -> Tuple[bool, str]:
    """§9.2 gaming test (condition b): ΔBrier_reliability > ΔBrier_total.

    If the reliability component degrades by more than the total Brier improves,
    the improvement is entirely from resolution/uncertainty gaming.
    Returns (triggered, reason).
    """
    delta_brier_total = baseline_decomp.brier_score - steer_decomp.brier_score  # positive = improvement
    delta_brier_rel = steer_decomp.reliability - baseline_decomp.reliability    # positive = degradation
    triggered = bool(delta_brier_rel > delta_brier_total)
    reason = (
        f"ΔBrier_reliability={delta_brier_rel:.4f} > ΔBrier_total={delta_brier_total:.4f} → gaming test TRIGGERED"
        if triggered else
        f"ΔBrier_reliability={delta_brier_rel:.4f} ≤ ΔBrier_total={delta_brier_total:.4f} → gaming test OK"
    )
    return triggered, reason


@dataclass
class BrierRawPair:
    """One per-item raw (confidence, correctness) observation."""
    item_id: str
    channel: str          # "steer" | "prompt" | "baseline"
    alpha: float
    layer: int
    confidence: float     # verbalized confidence ∈ [0, 1]
    correctness: int      # 0 or 1
    one_minus_brier: float  # per-item outcome used in adjudication
    # H-02: True iff confidence/correctness are 1-Brier proxy values (synthetic backend).
    # Real GPU pairs must have synthetic_proxy=False; proxy pairs MUST NOT be used
    # for authoritative safety decisions on real GPU runs.
    synthetic_proxy: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BrierRawStore:
    """Append-only JSONL store of per-item (confidence, correctness) raw pairs.

    Each line is one BrierRawPair serialized as JSON.  This store satisfies the
    §9.2 requirement that raw pairs be persisted from the outset, enabling full
    Brier decomposition post-hoc without re-running experiments.
    """

    def __init__(self, path: Path, fresh: bool = False) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if fresh and self.path.exists():
            self.path.unlink()
        self._handle = open(self.path, "a", encoding="utf-8")

    def record(
        self,
        item_id: str,
        channel: str,
        alpha: float,
        layer: int,
        confidence: float,
        correctness: int,
        synthetic_proxy: bool = False,
    ) -> None:
        """Append one raw (confidence, correctness) pair to the store.

        Args:
            synthetic_proxy: True iff confidence/correctness are derived from
                the 1-Brier outcome proxy (synthetic backend).  Must be False
                for real GPU pairs.  Records with synthetic_proxy=True MUST NOT
                be used for authoritative safety decisions on real GPU runs.
        """
        one_minus_brier = 1.0 - (float(confidence) - float(correctness)) ** 2
        pair = BrierRawPair(
            item_id=str(item_id),
            channel=str(channel),
            alpha=float(alpha),
            layer=int(layer),
            confidence=float(confidence),
            correctness=int(correctness),
            one_minus_brier=float(one_minus_brier),
            synthetic_proxy=bool(synthetic_proxy),
        )
        self._handle.write(json.dumps(pair.to_dict()) + "\n")
        self._handle.flush()

    def close(self) -> None:
        try:
            self._handle.close()
        except OSError:
            pass

    def load_all(self) -> List[BrierRawPair]:
        """Read all stored pairs from disk."""
        # Flush buffered writes before reading — do NOT close the handle here,
        # as more records may still be written after load_all() is called
        # (e.g. between Stage 1 candidates).  Closing here would break subsequent
        # record() calls (the old self.close() caused this exact failure).
        try:
            self._handle.flush()
        except (OSError, ValueError):
            pass  # already closed — safe to ignore
        pairs: List[BrierRawPair] = []
        if not self.path.exists():
            return pairs
        with open(self.path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                d = json.loads(line)
                # Backward-compatible: records written before H-02 fix lack synthetic_proxy
                d.setdefault("synthetic_proxy", False)
                pairs.append(BrierRawPair(**d))
        return pairs

    def filter_channel(self, channel: str) -> List[BrierRawPair]:
        return [p for p in self.load_all() if p.channel == channel]

    def has_real_pairs(self, channel: str) -> bool:
        """Return True iff the channel has at least one non-proxy (real GPU) pair."""
        return any(
            not p.synthetic_proxy
            for p in self.load_all()
            if p.channel == channel
        )

    def decompose_channel(
        self,
        channel: str,
        n_bins: int = 10,
        require_real: bool = False,
    ) -> Optional[BrierDecomposition]:
        """Compute Brier decomposition for all pairs in a given channel.

        Args:
            require_real: If True, return None when only synthetic-proxy pairs
                exist (safe guard: prevents proxy data from being used for
                authoritative GPU safety decisions).
        """
        pairs = self.filter_channel(channel)
        if not pairs:
            return None
        if require_real and all(p.synthetic_proxy for p in pairs):
            return None
        confs = [p.confidence for p in pairs]
        corrs = [p.correctness for p in pairs]
        return brier_decompose(confs, corrs, n_bins=n_bins)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
