"""Human-label ingestion hooks for validating the flagship judge."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List

REQUIRED_COLUMNS = ("item_id", "condition_id", "sample_index", "rater_id", "dimension", "score")
TARGET_ALPHA = 0.60


@dataclass(frozen=True)
class HumanCalibrationReport:
    status: str
    target_alpha: float
    n_labels: int
    alpha_by_dimension: Dict[str, float | None]
    required_columns: tuple[str, ...] = REQUIRED_COLUMNS

    def to_dict(self) -> dict:
        return asdict(self)


def load_human_labels(path: str | Path) -> List[dict]:
    path = Path(path)
    if path.suffix.lower() == ".jsonl":
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    else:
        with path.open("r", encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
    for row in rows:
        missing = [col for col in REQUIRED_COLUMNS if col not in row or row[col] in ("", None)]
        if missing:
            raise ValueError(f"human label row missing required columns: {missing}")
        row["sample_index"] = int(row["sample_index"])
        row["score"] = float(row["score"])
    return rows


def krippendorff_alpha_interval(rows: Iterable[dict]) -> float | None:
    by_unit: Dict[tuple[str, str, int], List[float]] = {}
    all_scores: List[float] = []
    for row in rows:
        unit = (str(row["item_id"]), str(row["condition_id"]), int(row["sample_index"]))
        score = float(row["score"])
        by_unit.setdefault(unit, []).append(score)
        all_scores.append(score)
    pair_diffs = []
    for vals in by_unit.values():
        if len(vals) < 2:
            continue
        for i, left in enumerate(vals):
            for right in vals[i + 1:]:
                pair_diffs.append((left - right) ** 2)
    if not pair_diffs or len(all_scores) < 2:
        return None
    observed = sum(pair_diffs) / len(pair_diffs)
    expected_pairs = []
    for i, left in enumerate(all_scores):
        for right in all_scores[i + 1:]:
            expected_pairs.append((left - right) ** 2)
    expected = sum(expected_pairs) / len(expected_pairs) if expected_pairs else 0.0
    if expected == 0.0:
        return 1.0 if observed == 0.0 else None
    return float(1.0 - observed / expected)


def summarize_human_calibration(path: str | Path | None) -> HumanCalibrationReport:
    if path is None:
        return HumanCalibrationReport(
            status="not_run_required_before_confirmatory_claim",
            target_alpha=TARGET_ALPHA,
            n_labels=0,
            alpha_by_dimension={},
        )
    rows = load_human_labels(path)
    dims = sorted({str(r["dimension"]) for r in rows})
    alpha_by_dim = {
        dim: krippendorff_alpha_interval(r for r in rows if str(r["dimension"]) == dim)
        for dim in dims
    }
    passed = all(alpha is not None and alpha >= TARGET_ALPHA for alpha in alpha_by_dim.values())
    return HumanCalibrationReport(
        status="passed" if passed else "failed_or_incomplete",
        target_alpha=TARGET_ALPHA,
        n_labels=len(rows),
        alpha_by_dimension=alpha_by_dim,
    )
