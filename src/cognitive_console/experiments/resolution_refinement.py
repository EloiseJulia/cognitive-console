"""Frozen power and sampling plan for the C2b resolution refinement."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from typing import Dict, Iterable, List, Mapping, Sequence

import numpy as np

from cognitive_console.experiments import adjudicate_c2b as c2b

PROTOCOL_ID = "c2b-resolution-refinement-20260812"
DEV_EXPERIMENT_ID = "c2b-resolution-caa-qwen-dev-20260812"
TEST_EXPERIMENT_ID = "c2b-resolution-caa-qwen-test-20260812"
MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"
MODEL_REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"
METHOD = "caa"
SEED = 20260812
AXES = ("skepticism", "uncertainty_awareness")
TARGET_MDE = 0.05
TRUTHFULQA_VALIDATION_SIZE = 817
TRIVIAQA_VALIDATION_SIZE = 17_944


@dataclass(frozen=True)
class FrozenCellPower:
    method: str
    model: str
    axis: str
    n_current_test: int
    se_estimate: float
    mde_current: float

    @property
    def per_item_sd(self) -> float:
        return self.se_estimate * math.sqrt(self.n_current_test)

    @property
    def target_test_n_exact(self) -> float:
        return self.n_current_test * (self.mde_current / TARGET_MDE) ** 2

    @property
    def target_test_n(self) -> int:
        return math.ceil(self.target_test_n_exact)


# Source: results/posthoc_equivalence/posthoc_equivalence_e0006.json.
FROZEN_CELL_POWER: tuple[FrozenCellPower, ...] = (
    FrozenCellPower("caa", "qwen2.5-7b", "skepticism", 40, 0.058089, 0.1880),
    FrozenCellPower("caa", "qwen2.5-7b", "uncertainty_awareness", 53, 0.060493, 0.1958),
    FrozenCellPower("caa", "meta-llama-3-8b", "skepticism", 40, 0.082896, 0.2683),
    FrozenCellPower("caa", "meta-llama-3-8b", "uncertainty_awareness", 53, 0.014663, 0.0474),
    FrozenCellPower("iti", "qwen2.5-7b", "skepticism", 40, 0.069430, 0.2247),
    FrozenCellPower("iti", "qwen2.5-7b", "uncertainty_awareness", 53, 0.014236, 0.0461),
    FrozenCellPower("iti", "meta-llama-3-8b", "skepticism", 40, 0.086232, 0.2790),
    FrozenCellPower("iti", "meta-llama-3-8b", "uncertainty_awareness", 53, 0.014227, 0.0460),
)


def minimum_total_n_for_test_target(target_test_n: int) -> int:
    total = max(2, int(target_test_n))
    while c2b._split_sizes(total)[1] < int(target_test_n):
        total += 1
    return total


def frozen_excluded_ids(axis: str) -> frozenset[str]:
    if axis == "skepticism":
        return frozenset(f"truthfulqa-mc1-{i:05d}" for i in range(60))
    if axis == "uncertainty_awareness":
        return frozenset(f"triviaqa-{i:05d}" for i in range(80))
    raise ValueError(f"resolution refinement does not include axis {axis!r}")


def primary_power_rows() -> Dict[str, FrozenCellPower]:
    return {
        row.axis: row
        for row in FROZEN_CELL_POWER
        if row.method == METHOD and row.model == "qwen2.5-7b"
    }


def selected_total_n_by_axis() -> Dict[str, int]:
    primary = primary_power_rows()
    skepticism_fresh_cap = TRUTHFULQA_VALIDATION_SIZE - len(
        frozen_excluded_ids("skepticism")
    )
    return {
        "skepticism": skepticism_fresh_cap,
        "uncertainty_awareness": minimum_total_n_for_test_target(
            primary["uncertainty_awareness"].target_test_n
        ),
    }


def achieved_test_n_by_axis() -> Dict[str, int]:
    return {
        axis: c2b._split_sizes(total)[1]
        for axis, total in selected_total_n_by_axis().items()
    }


def achieved_mde_by_axis() -> Dict[str, float]:
    primary = primary_power_rows()
    return {
        axis: row.mde_current
        * math.sqrt(row.n_current_test / achieved_test_n_by_axis()[axis])
        for axis, row in primary.items()
    }


def select_disjoint_items(
    items: Sequence[Mapping[str, object]],
    *,
    excluded_ids: Iterable[str],
    n_total: int,
    seed: int,
) -> List[Dict[str, object]]:
    excluded = {str(value) for value in excluded_ids}
    seen: set[str] = set()
    eligible: List[Dict[str, object]] = []
    for raw in items:
        item = dict(raw)
        item_id = str(item.get("id", ""))
        if not item_id:
            raise ValueError("resolution item lacks a non-empty id")
        if item_id in seen:
            raise ValueError(f"duplicate resolution item id: {item_id}")
        seen.add(item_id)
        if item_id not in excluded:
            eligible.append(item)
    if len(eligible) < int(n_total):
        raise ValueError(
            f"disjoint pool too small: eligible={len(eligible)}, requested={n_total}"
        )
    rng = np.random.default_rng(int(seed))
    selected_positions = sorted(
        rng.permutation(len(eligible))[: int(n_total)].tolist()
    )
    selected = [eligible[index] for index in selected_positions]
    selected_ids = {str(item["id"]) for item in selected}
    if selected_ids & excluded:
        raise AssertionError("frozen-item leakage after disjoint sampling")
    return selected


def sampling_manifest(items_by_axis: Mapping[str, Sequence[Mapping[str, object]]]) -> Dict:
    rows: Dict[str, object] = {}
    for axis in AXES:
        ids = [str(item["id"]) for item in items_by_axis[axis]]
        split = c2b.split_dev_test(ids, seed=SEED)
        rows[axis] = {
            "n_total": len(ids),
            "n_dev": len(split.dev_ids),
            "n_test": len(split.test_ids),
            "excluded_frozen_ids": sorted(frozen_excluded_ids(axis)),
            "selected_item_ids_sha256": "sha256:"
            + hashlib.sha256(
                json.dumps(ids, separators=(",", ":")).encode("utf-8")
            ).hexdigest(),
            "dev_item_ids_sha256": "sha256:"
            + hashlib.sha256(
                json.dumps(split.dev_ids, separators=(",", ":")).encode("utf-8")
            ).hexdigest(),
            "test_item_ids_sha256": "sha256:"
            + hashlib.sha256(
                json.dumps(split.test_ids, separators=(",", ":")).encode("utf-8")
            ).hexdigest(),
        }
    return {
        "protocol_id": PROTOCOL_ID,
        "seed": SEED,
        "axes": rows,
    }


def power_manifest() -> Dict[str, object]:
    return {
        "target_mde": TARGET_MDE,
        "source": "results/posthoc_equivalence/posthoc_equivalence_e0006.json",
        "cells": [
            {
                **asdict(row),
                "per_item_sd": row.per_item_sd,
                "target_test_n_exact": row.target_test_n_exact,
                "target_test_n_ceiling": row.target_test_n,
            }
            for row in FROZEN_CELL_POWER
        ],
        "primary": {
            axis: {
                "selected_total_n": selected_total_n_by_axis()[axis],
                "achieved_test_n": achieved_test_n_by_axis()[axis],
                "achieved_mde": achieved_mde_by_axis()[axis],
            }
            for axis in AXES
        },
    }
