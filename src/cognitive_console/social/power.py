"""DEV-power / variance estimator for the flagship L0 harness."""

from __future__ import annotations

import statistics
from dataclasses import asdict, dataclass
from statistics import NormalDist
from typing import Dict, Iterable, List, Sequence


@dataclass(frozen=True)
class DimensionPower:
    dimension: str
    control_within_item_variance: float
    paired_diff_variance: float
    n_observed_items: int
    mde_by_candidate: Dict[str, float]

    def to_dict(self) -> dict:
        return asdict(self)


def _variance(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    return float(statistics.variance([float(v) for v in values]))


def _z_two_sided(alpha: float, power: float) -> float:
    nd = NormalDist()
    return float(nd.inv_cdf(1.0 - alpha / 2.0) + nd.inv_cdf(power))


def estimate_mde(
    rows: Iterable[dict],
    dimensions: Sequence[str] = ("m1", "m4"),
    candidates: Sequence[tuple[int, int]] = ((40, 3), (80, 5), (120, 5)),
    alpha: float = 0.05 / 4.0,
    power: float = 0.80,
) -> List[DimensionPower]:
    """Estimate variance and MDE from per-item/condition/sample score rows.

    Rows contain ``item_id``, ``condition_id``, ``sample_index`` and dimension
    columns (``m1``, ``m4`` by default). MDE uses the larger of observed paired
    B-A item-mean variance and within-control sample variance scaled by k.
    """
    by_dim: List[DimensionPower] = []
    data = list(rows)
    z = _z_two_sided(alpha, power)
    for dim in dimensions:
        control_by_item: Dict[str, List[float]] = {}
        means_by_item_cond: Dict[tuple[str, str], List[float]] = {}
        for row in data:
            if dim not in row:
                continue
            item_id = str(row["item_id"])
            cond = str(row["condition_id"])
            value = float(row[dim])
            means_by_item_cond.setdefault((item_id, cond), []).append(value)
            if cond == "A":
                control_by_item.setdefault(item_id, []).append(value)

        within_vars = [_variance(vals) for vals in control_by_item.values() if len(vals) >= 2]
        control_within = float(statistics.mean(within_vars)) if within_vars else 0.0
        diffs = []
        for item_id in sorted({key[0] for key in means_by_item_cond}):
            a = means_by_item_cond.get((item_id, "A"))
            b = means_by_item_cond.get((item_id, "B"))
            if a and b:
                diffs.append(float(statistics.mean(b) - statistics.mean(a)))
        paired_var = _variance(diffs)
        mde = {}
        for n, k in candidates:
            effective_var = max(paired_var, 2.0 * control_within / max(1, int(k)))
            mde[f"N{int(n)}_k{int(k)}"] = float(z * (effective_var / max(1, int(n))) ** 0.5)
        by_dim.append(
            DimensionPower(
                dimension=dim,
                control_within_item_variance=control_within,
                paired_diff_variance=paired_var,
                n_observed_items=len(diffs),
                mde_by_candidate=mde,
            )
        )
    return by_dim
