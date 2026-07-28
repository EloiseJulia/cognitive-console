"""Unit tests for scripts/aggregate_multiseed_c2.py.

Uses small synthetic JSON fixtures — no real model outputs, no GPU.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from scripts import aggregate_multiseed_c2 as A

# --------------------------------------------------------------------------- #
# Fixture builders
# --------------------------------------------------------------------------- #

AXES = ["deliberation", "skepticism", "uncertainty_awareness"]
CELL_KEYS = ["caa__qwen2.5-7b", "caa__llama3-8b", "iti__qwen2.5-7b", "iti__llama3-8b"]


def _make_axis_result(axis: str, mean_diff: float, ci_lo: float, ci_hi: float,
                      passed: bool = False) -> Dict[str, Any]:
    return {
        "axis": axis,
        "layer": 20,
        "n_dev": 20,
        "n_test": 40,
        "k": 5,
        "dev_selection": {"best_prompt_id": f"{axis}-p1", "frozen_alpha": 2.0},
        "per_item_prompt": [0.0] * 40,
        "per_item_steer": [mean_diff] * 40,
        "per_item_diff": [mean_diff] * 40,
        "mean_diff": mean_diff,
        "ci_lo": ci_lo,
        "ci_hi": ci_hi,
        "ci_level": 0.9833333333333333,
        "bootstrap_b": 10000,
        "coherence_ok": True,
        "delta": 0.05,
        "passed": passed,
        "conflict": {},
        "descriptive": {},
    }


def _make_cell_result(mean_diffs: Dict[str, float]) -> Dict[str, Any]:
    """Build a minimal c2b_adjudication_results.json payload."""
    axes_list = []
    for axis in AXES:
        md = mean_diffs.get(axis, 0.0)
        ci_lo = md - 0.05
        ci_hi = md + 0.05
        passed = ci_lo > 0 and md >= 0.05
        axes_list.append(_make_axis_result(axis, md, ci_lo, ci_hi, passed))
    axis_passes = {a: axes_list[i]["passed"] for i, a in enumerate(AXES)}
    return {
        "verdict": "KILL_PLAN_D",
        "axis_passes": axis_passes,
        "frozen_params": {"bootstrap_b": 10000, "bonferroni_ci_level": 0.983},
        "axes": axes_list,
    }


def _make_arm_summary(
    seed: int,
    arm_verdict: str = "NON_TRANSFER_GENERALIZED",
    cells_overrides: Dict[str, int] = None,
) -> Dict[str, Any]:
    """Build a minimal arm_matrix_summary.json payload."""
    cells = []
    for ck in CELL_KEYS:
        axes_passed = (cells_overrides or {}).get(ck, 0)
        cells.append({
            "cell_key": ck,
            "method": ck.split("__")[0],
            "model_label": ck.split("__")[1],
            "model_id": "synthetic/model",
            "axes_passed": axes_passed,
            "verdict": "KILL_PLAN_D" if axes_passed == 0 else "CONDITIONAL_GO",
            "axis_passes": {a: (i < axes_passed) for i, a in enumerate(AXES)},
        })
    any_pass = any(c["axes_passed"] > 0 for c in cells)
    zero_pass = sum(1 for c in cells if c["axes_passed"] == 0)
    return {
        "generated_at": "2026-07-28T00:00:00+00:00",
        "backend": "hf",
        "seed": seed,
        "arm_rule": "any-pass => SCOPE_NARROWED_POSITIVE; ...",
        "cells": cells,
        "arm_verdict": arm_verdict,
        "n_cells": 4,
        "zero_pass_cells": zero_pass,
        "min_zero_pass_cells_for_generalized": 3,
        "any_cell_has_pass": any_pass,
    }


def _write_seed_dir(
    tmp: Path,
    seed: int,
    arm_verdict: str = "NON_TRANSFER_GENERALIZED",
    mean_diffs_by_cell: Dict[str, Dict[str, float]] = None,
) -> Path:
    """Write arm_matrix_summary.json + cell subdirs for one seed."""
    seed_dir = tmp / f"seed_{seed}"
    seed_dir.mkdir(parents=True)
    arm_data = _make_arm_summary(seed, arm_verdict=arm_verdict)
    arm_json = seed_dir / "arm_matrix_summary.json"
    arm_json.write_text(json.dumps(arm_data, indent=2), encoding="utf-8")
    for ck in CELL_KEYS:
        cell_dir = seed_dir / f"cell_{ck}"
        cell_dir.mkdir()
        mds = (mean_diffs_by_cell or {}).get(ck, {})
        cell_result = _make_cell_result(mds)
        (cell_dir / "c2b_adjudication_results.json").write_text(
            json.dumps(cell_result, indent=2), encoding="utf-8"
        )
    return arm_json


# --------------------------------------------------------------------------- #
# Tests: load_arm_summary
# --------------------------------------------------------------------------- #

def test_load_arm_summary_valid(tmp_path):
    data = _make_arm_summary(20260723)
    p = tmp_path / "arm.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    loaded = A.load_arm_summary(p)
    assert loaded["arm_verdict"] == "NON_TRANSFER_GENERALIZED"
    assert len(loaded["cells"]) == 4


def test_load_arm_summary_missing_verdict(tmp_path):
    data = {"cells": []}
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="arm_verdict"):
        A.load_arm_summary(p)


def test_load_arm_summary_missing_cells(tmp_path):
    data = {"arm_verdict": "NON_TRANSFER_GENERALIZED"}
    p = tmp_path / "bad2.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="cells"):
        A.load_arm_summary(p)


# --------------------------------------------------------------------------- #
# Tests: _extract_axis_stats
# --------------------------------------------------------------------------- #

def test_extract_axis_stats_returns_correct_values():
    cell_result = _make_cell_result({"uncertainty_awareness": -0.2})
    stats = A._extract_axis_stats(cell_result, "uncertainty_awareness")
    assert stats["mean_diff"] == pytest.approx(-0.2)
    assert stats["ci_lo"] == pytest.approx(-0.25)
    assert stats["ci_hi"] == pytest.approx(-0.15)
    assert stats["passed"] is False  # negative diff cannot pass


def test_extract_axis_stats_missing_axis_returns_none():
    cell_result = {"axes": []}
    stats = A._extract_axis_stats(cell_result, "deliberation")
    assert stats["mean_diff"] is None
    assert stats["passed"] is False


# --------------------------------------------------------------------------- #
# Tests: build_seed_record
# --------------------------------------------------------------------------- #

def test_build_seed_record_finds_cell_results(tmp_path):
    arm_json = _write_seed_dir(
        tmp_path, 20260723,
        mean_diffs_by_cell={
            "caa__qwen2.5-7b": {"uncertainty_awareness": -0.228},
        },
    )
    arm_data = A.load_arm_summary(arm_json)
    rec = A.build_seed_record(20260723, arm_json, arm_data)
    assert rec["seed"] == 20260723
    assert rec["arm_verdict"] == "NON_TRANSFER_GENERALIZED"
    # Check uncertainty arm for caa__qwen2.5-7b
    cq = next(c for c in rec["cells"] if c["cell_key"] == "caa__qwen2.5-7b")
    unc = cq["axis_stats"]["uncertainty_awareness"]
    assert unc["mean_diff"] == pytest.approx(-0.228)
    assert unc["ci_hi"] == pytest.approx(-0.228 + 0.05)


def test_build_seed_record_missing_cell_result_graceful(tmp_path):
    """If no cell result JSON exists, axis_stats should contain a 'note' key."""
    seed_dir = tmp_path / "seed_notexist"
    seed_dir.mkdir()
    arm_data = _make_arm_summary(99)
    arm_json = seed_dir / "arm_matrix_summary.json"
    arm_json.write_text(json.dumps(arm_data), encoding="utf-8")
    # Do NOT write any cell sub-dirs.
    rec = A.build_seed_record(99, arm_json, arm_data)
    for c in rec["cells"]:
        for axis in AXES:
            s = c["axis_stats"][axis]
            assert "note" in s


# --------------------------------------------------------------------------- #
# Tests: aggregate_across_seeds
# --------------------------------------------------------------------------- #

def _make_seed_records_all_non_transfer(n: int, tmp_path: Path) -> List[Dict]:
    records = []
    seeds = [20260723 + i for i in range(n)]
    for s in seeds:
        arm_json = _write_seed_dir(
            tmp_path, s,
            mean_diffs_by_cell={
                ck: {"uncertainty_awareness": -0.15, "deliberation": 0.01, "skepticism": -0.05}
                for ck in CELL_KEYS
            },
        )
        arm_data = A.load_arm_summary(arm_json)
        records.append(A.build_seed_record(s, arm_json, arm_data))
    return records


def test_aggregate_all_non_transfer_5_seeds(tmp_path):
    records = _make_seed_records_all_non_transfer(5, tmp_path)
    agg = A.aggregate_across_seeds(records)
    assert agg["n_seeds"] == 5
    assert agg["n_seeds_non_transfer_generalized"] == 5
    cd = agg["caveat_drop_rule"]
    # uncertainty harm CI_hi = -0.15 + 0.05 = -0.10 < 0 → all_ci_negative=True
    assert cd["uncertainty_harm_ci_negative_all_cells"] is True
    assert cd["non_transfer_in_4_of_5_seeds"] is True
    assert cd["outcome"] == "DROP_SINGLE_SEED_CAVEAT"


def test_aggregate_caveat_retained_when_few_non_transfer(tmp_path):
    """If only 3/5 seeds are NON_TRANSFER, caveat must be retained."""
    records = []
    seeds = [20260723 + i for i in range(5)]
    for i, s in enumerate(seeds):
        verdict = "NON_TRANSFER_GENERALIZED" if i < 3 else "SCOPE_NARROWED_POSITIVE"
        arm_json = _write_seed_dir(tmp_path, s, arm_verdict=verdict)
        arm_data = A.load_arm_summary(arm_json)
        records.append(A.build_seed_record(s, arm_json, arm_data))
    agg = A.aggregate_across_seeds(records)
    assert agg["n_seeds_non_transfer_generalized"] == 3
    cd = agg["caveat_drop_rule"]
    assert cd["non_transfer_in_4_of_5_seeds"] is False
    assert cd["outcome"] == "RETAIN_CAVEAT_OR_HONEST_FAIL"


def test_aggregate_mean_diff_across_seeds_computed(tmp_path):
    """mean_diff_across_seeds should average correctly."""
    seeds_and_diffs = [(20260723, -0.2), (20260724, -0.1), (20260725, -0.15)]
    records = []
    for s, md in seeds_and_diffs:
        arm_json = _write_seed_dir(
            tmp_path, s,
            mean_diffs_by_cell={ck: {"uncertainty_awareness": md} for ck in CELL_KEYS},
        )
        arm_data = A.load_arm_summary(arm_json)
        records.append(A.build_seed_record(s, arm_json, arm_data))
    agg = A.aggregate_across_seeds(records)
    for ck in CELL_KEYS:
        st = agg["cell_axis_stats"][ck]["uncertainty_awareness"]
        assert st["mean_diff_across_seeds"] == pytest.approx(-0.15)


def test_aggregate_all_ci_negative_flag(tmp_path):
    """all_ci_negative=True only when all CI_hi values are < 0."""
    # ci_hi = mean_diff + 0.05; use mean_diff=-0.10 → ci_hi=-0.05 < 0
    records = []
    for i in range(3):
        s = 20260723 + i
        arm_json = _write_seed_dir(
            tmp_path, s,
            mean_diffs_by_cell={ck: {"uncertainty_awareness": -0.10} for ck in CELL_KEYS},
        )
        arm_data = A.load_arm_summary(arm_json)
        records.append(A.build_seed_record(s, arm_json, arm_data))
    agg = A.aggregate_across_seeds(records)
    for ck in CELL_KEYS:
        st = agg["cell_axis_stats"][ck]["uncertainty_awareness"]
        assert st["all_ci_negative"] is True

    # Now a positive ci_hi
    s = 20260730
    arm_json = _write_seed_dir(
        tmp_path, s,
        mean_diffs_by_cell={ck: {"uncertainty_awareness": 0.03} for ck in CELL_KEYS},
    )
    arm_data = A.load_arm_summary(arm_json)
    records.append(A.build_seed_record(s, arm_json, arm_data))
    agg2 = A.aggregate_across_seeds(records)
    for ck in CELL_KEYS:
        st = agg2["cell_axis_stats"][ck]["uncertainty_awareness"]
        assert st["all_ci_negative"] is False


# --------------------------------------------------------------------------- #
# Tests: main (CLI integration)
# --------------------------------------------------------------------------- #

def test_main_via_manifest(tmp_path):
    """End-to-end test of main() with a manifest file."""
    arm_jsons = []
    seeds = [20260723, 20260724]
    for s in seeds:
        arm_json = _write_seed_dir(
            tmp_path, s,
            mean_diffs_by_cell={ck: {"uncertainty_awareness": -0.15} for ck in CELL_KEYS},
        )
        arm_jsons.append(arm_json)

    manifest = [
        {"seed": s, "arm_summary_json": str(arm_jsons[i])}
        for i, s in enumerate(seeds)
    ]
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    out_dir = tmp_path / "out"
    rc = A.main(["--manifest", str(manifest_path), "--out-dir", str(out_dir)])
    assert rc == 0
    assert (out_dir / "multiseed_c2_aggregate.json").exists()
    assert (out_dir / "multiseed_c2_aggregate.md").exists()

    result = json.loads((out_dir / "multiseed_c2_aggregate.json").read_text(encoding="utf-8"))
    assert result["aggregation"]["n_seeds"] == 2
    assert result["experiment_family"] == "E-0011"


def test_main_via_arm_summaries_cli(tmp_path):
    """End-to-end test using --arm-summaries + --seeds."""
    arm_jsons = []
    seeds = [20260723, 20260724, 20260725]
    for s in seeds:
        arm_json = _write_seed_dir(tmp_path, s)
        arm_jsons.append(arm_json)

    out_dir = tmp_path / "out2"
    rc = A.main([
        "--arm-summaries"] + [str(p) for p in arm_jsons] + [
        "--seeds"] + [str(s) for s in seeds] + [
        "--out-dir", str(out_dir),
    ])
    assert rc == 0
    result = json.loads((out_dir / "multiseed_c2_aggregate.json").read_text(encoding="utf-8"))
    assert result["aggregation"]["n_seeds"] == 3
    for r in result["seed_records"]:
        assert r["seed"] in seeds


def test_main_missing_arm_summary_returns_error(tmp_path):
    out_dir = tmp_path / "out3"
    rc = A.main([
        "--arm-summaries", str(tmp_path / "nonexistent.json"),
        "--seeds", "12345",
        "--out-dir", str(out_dir),
    ])
    assert rc == 1


def test_main_seed_count_mismatch_returns_error(tmp_path):
    arm_json = _write_seed_dir(tmp_path, 20260723)
    out_dir = tmp_path / "out4"
    rc = A.main([
        "--arm-summaries", str(arm_json),
        "--seeds", "20260723", "20260724",  # mismatch: 1 path but 2 seeds
        "--out-dir", str(out_dir),
    ])
    assert rc == 1


def test_output_json_numbers_from_json_not_hardcoded(tmp_path):
    """Verify that mean_diff values in the aggregate match the fixture values exactly."""
    expected_md = -0.228
    arm_jsons = []
    seeds = [20260723, 20260724]
    for s in seeds:
        arm_json = _write_seed_dir(
            tmp_path, s,
            mean_diffs_by_cell={
                "caa__qwen2.5-7b": {"uncertainty_awareness": expected_md},
            },
        )
        arm_jsons.append(arm_json)

    out_dir = tmp_path / "out5"
    rc = A.main([
        "--arm-summaries"] + [str(p) for p in arm_jsons] + [
        "--seeds", "20260723", "20260724",
        "--out-dir", str(out_dir),
    ])
    assert rc == 0
    result = json.loads((out_dir / "multiseed_c2_aggregate.json").read_text(encoding="utf-8"))
    vals = result["aggregation"]["cell_axis_stats"]["caa__qwen2.5-7b"]["uncertainty_awareness"]
    for v in vals["mean_diff_values"]:
        assert v == pytest.approx(expected_md)
    assert vals["mean_diff_across_seeds"] == pytest.approx(expected_md)
