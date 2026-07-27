"""Fail-closed coverage and fingerprint guards for flagship L0."""

from __future__ import annotations

import hashlib
import json
from typing import Iterable, Sequence

from .conditions import CONDITIONS


class CoverageError(ValueError):
    pass


def config_fingerprint(payload: dict) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]


def assert_complete_coverage(
    records: Iterable[dict],
    item_ids: Sequence[str],
    condition_ids: Sequence[str] | None = None,
    k: int = 1,
) -> None:
    conditions = list(condition_ids or [c.id for c in CONDITIONS])
    expected = {
        (str(item_id), str(cond), int(sample))
        for item_id in item_ids
        for cond in conditions
        for sample in range(int(k))
    }
    seen = set()
    missing_score = []
    for rec in records:
        key = (str(rec.get("item_id")), str(rec.get("condition_id")), int(rec.get("sample_index", -1)))
        seen.add(key)
        scores = rec.get("scores") or {}
        if "m1_recommendation_strength" not in scores or "m4_deference_exploitation" not in scores:
            missing_score.append(key)
    missing = sorted(expected - seen)
    extra = sorted(seen - expected)
    if missing or extra or missing_score:
        raise CoverageError(
            "incomplete flagship L0 coverage: "
            f"missing={missing[:5]} extra={extra[:5]} missing_score={missing_score[:5]}"
        )
