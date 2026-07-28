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
    harness_repro_ok: bool | None = None,
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
    payload = {
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
    if harness_repro_ok is not None:
        payload["harness_repro_ok"] = harness_repro_ok
    return payload


def _write_seed_dir(
    tmp: Path,
    seed: int,
    arm_verdict: str = "NON_TRANSFER_GENERALIZED",
    mean_diffs_by_cell: Dict[str, Dict[str, float]] = None,
    harness_repro_ok: bool | None = None,
) -> Path:
    """Write arm_matrix_summary.json + cell subdirs for one seed."""
    seed_dir = tmp / f"seed_{seed}"
    seed_dir.mkdir(parents=True)
    arm_data = _make_arm_summary(seed, arm_verdict=arm_verdict, harness_repro_ok=harness_repro_ok)
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
    assert cd["uncertainty_harm_ci_negative_all_cells_all_seeds"] is True
    assert cd["non_transfer_in_4_of_5_seeds"] is True
    assert cd["any_strong_positive_flip"] is False
    assert cd["outcome"] == "DROP_SINGLE_SEED_CAVEAT"


def test_aggregate_4_of_5_non_transfer_becomes_seed_mostly_robust(tmp_path):
    """If 4/5 seeds are NON_TRANSFER and CI condition holds, classify as mostly robust."""
    records = []
    seeds = [20260723 + i for i in range(5)]
    for i, s in enumerate(seeds):
        verdict = "NON_TRANSFER_GENERALIZED" if i < 4 else "SCOPE_NARROWED_POSITIVE"
        arm_json = _write_seed_dir(
            tmp_path,
            s,
            arm_verdict=verdict,
            mean_diffs_by_cell={
                ck: {"uncertainty_awareness": -0.15} for ck in CELL_KEYS
            },
        )
        arm_data = A.load_arm_summary(arm_json)
        records.append(A.build_seed_record(s, arm_json, arm_data))
    agg = A.aggregate_across_seeds(records)
    assert agg["n_seeds_non_transfer_generalized"] == 4
    cd = agg["caveat_drop_rule"]
    assert cd["strict_all_non_transfer_generalized"] is False
    assert cd["non_transfer_in_4_of_5_seeds"] is True
    assert cd["uncertainty_harm_ci_negative_all_cells_3_of_5"] is True
    assert cd["outcome"] == "SEED_MOSTLY_ROBUST"


def test_aggregate_strong_positive_flip_forces_seed_sensitive(tmp_path):
    records = _make_seed_records_all_non_transfer(5, tmp_path)
    # Inject one seed×cell×axis PASS (strong-positive flip) from JSON axis "passed" flag.
    flip_seed = 20260726
    flip_arm_json = _write_seed_dir(
        tmp_path / "flip_case",
        flip_seed,
        arm_verdict="NON_TRANSFER_GENERALIZED",
        mean_diffs_by_cell={
            **{ck: {"uncertainty_awareness": -0.15} for ck in CELL_KEYS},
            "caa__qwen2.5-7b": {"uncertainty_awareness": -0.15, "deliberation": 0.20},
        },
    )
    flip_arm_data = A.load_arm_summary(flip_arm_json)
    flip_record = A.build_seed_record(flip_seed, flip_arm_json, flip_arm_data)
    records = [r for r in records if r["seed"] != flip_seed] + [flip_record]

    agg = A.aggregate_across_seeds(records)
    cd = agg["caveat_drop_rule"]
    assert cd["any_strong_positive_flip"] is True
    assert cd["strong_positive_flip_details"]
    assert cd["outcome"] == "SEED_SENSITIVE"


def test_aggregate_harness_failure_forces_kill_harness(tmp_path):
    records = _make_seed_records_all_non_transfer(5, tmp_path)
    # Harness check seed explicitly marked as not reproducing E-0006.
    fail_arm_json = _write_seed_dir(
        tmp_path / "harness_case",
        20260723,
        arm_verdict="NON_TRANSFER_GENERALIZED",
        mean_diffs_by_cell={ck: {"uncertainty_awareness": -0.15} for ck in CELL_KEYS},
        harness_repro_ok=False,
    )
    fail_arm_data = A.load_arm_summary(fail_arm_json)
    fail_record = A.build_seed_record(20260723, fail_arm_json, fail_arm_data)
    records = [r for r in records if r["seed"] != 20260723] + [fail_record]

    agg = A.aggregate_across_seeds(records)
    cd = agg["caveat_drop_rule"]
    assert cd["harness_fail_reasons"]
    assert cd["outcome"] == "KILL_HARNESS"


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


# --------------------------------------------------------------------------- #
# Tests: any_true_pass guardrail — §4c (new)
# --------------------------------------------------------------------------- #

def test_any_true_pass_block_always_present_and_empty_when_no_pass(tmp_path):
    """any_true_pass must be present (as empty list) even when no seed has a pass."""
    records = _make_seed_records_all_non_transfer(3, tmp_path)
    agg = A.aggregate_across_seeds(records)
    assert "any_true_pass" in agg
    assert agg["any_true_pass"] == []
    assert agg["has_any_true_pass"] is False


def test_any_true_pass_surfaced_with_true_pass(tmp_path):
    """When one seed×cell×axis has a true pass, it must appear in any_true_pass."""
    records = _make_seed_records_all_non_transfer(5, tmp_path / "base")
    pass_arm_json = _write_seed_dir(
        tmp_path / "pass_case",
        20260724,
        arm_verdict="NON_TRANSFER_GENERALIZED",
        mean_diffs_by_cell={
            "caa__qwen2.5-7b": {"deliberation": 0.20, "uncertainty_awareness": -0.15},
            **{ck: {"uncertainty_awareness": -0.15} for ck in CELL_KEYS if ck != "caa__qwen2.5-7b"},
        },
    )
    pass_arm_data = A.load_arm_summary(pass_arm_json)
    pass_record = A.build_seed_record(20260724, pass_arm_json, pass_arm_data)
    records = [r for r in records if r["seed"] != 20260724] + [pass_record]

    agg = A.aggregate_across_seeds(records)
    assert agg["has_any_true_pass"] is True
    tp_list = agg["any_true_pass"]
    assert len(tp_list) >= 1
    tp = next(
        (e for e in tp_list
         if e["seed"] == 20260724
         and e["cell_key"] == "caa__qwen2.5-7b"
         and e["axis"] == "deliberation"),
        None,
    )
    assert tp is not None, "Expected true pass entry not found in any_true_pass"
    assert tp["mean_diff"] == pytest.approx(0.20)
    assert tp["ci_lo"] is not None
    assert tp["ci_hi"] is not None


def test_any_true_pass_blocks_drop_and_mostly_robust(tmp_path):
    """A true pass in any seed×cell×axis must prevent DROP and MOSTLY_ROBUST verdicts."""
    # All seeds NON_TRANSFER, all CI_hi<0 — normally DROP_SINGLE_SEED_CAVEAT.
    # Inject one pass → outcome must not be DROP or MOSTLY_ROBUST.
    records = _make_seed_records_all_non_transfer(5, tmp_path / "base")
    pass_arm_json = _write_seed_dir(
        tmp_path / "pass_block",
        20260725,
        arm_verdict="NON_TRANSFER_GENERALIZED",
        mean_diffs_by_cell={
            "caa__qwen2.5-7b": {"deliberation": 0.20, "uncertainty_awareness": -0.15},
            **{ck: {"uncertainty_awareness": -0.15} for ck in CELL_KEYS if ck != "caa__qwen2.5-7b"},
        },
    )
    pass_arm_data = A.load_arm_summary(pass_arm_json)
    pass_record = A.build_seed_record(20260725, pass_arm_json, pass_arm_data)
    records = [r for r in records if r["seed"] != 20260725] + [pass_record]

    agg = A.aggregate_across_seeds(records)
    outcome = agg["caveat_drop_rule"]["outcome"]
    assert outcome not in ("DROP_SINGLE_SEED_CAVEAT", "SEED_MOSTLY_ROBUST"), (
        f"True pass must block DROP/MOSTLY_ROBUST, got {outcome}"
    )
    assert agg["has_any_true_pass"] is True


def test_any_true_pass_visible_in_json_and_md_output(tmp_path):
    """main() output must contain any_true_pass in JSON and surfacing text in MD."""
    pass_arm_json = _write_seed_dir(
        tmp_path,
        20260723,
        mean_diffs_by_cell={
            "caa__qwen2.5-7b": {"deliberation": 0.20, "uncertainty_awareness": -0.15},
            **{ck: {"uncertainty_awareness": -0.15} for ck in CELL_KEYS if ck != "caa__qwen2.5-7b"},
        },
    )
    out_dir = tmp_path / "out_pass"
    rc = A.main([
        "--arm-summaries", str(pass_arm_json),
        "--seeds", "20260723",
        "--out-dir", str(out_dir),
    ])
    assert rc == 0

    result = json.loads((out_dir / "multiseed_c2_aggregate.json").read_text(encoding="utf-8"))
    assert "any_true_pass" in result["aggregation"]
    assert len(result["aggregation"]["any_true_pass"]) >= 1

    md = (out_dir / "multiseed_c2_aggregate.md").read_text(encoding="utf-8")
    assert "any_true_pass" in md or "TRUE PASSES" in md
    assert "single_seed_positive_surfaced" in md


def test_cell_flagged_single_seed_positive_surfaced(tmp_path):
    """Cell with a true pass must be flagged; unaffected cells must not."""
    records = _make_seed_records_all_non_transfer(3, tmp_path / "base")
    pass_arm_json = _write_seed_dir(
        tmp_path / "pass_cell",
        20260723,
        mean_diffs_by_cell={
            "caa__qwen2.5-7b": {"deliberation": 0.20, "uncertainty_awareness": -0.15},
            **{ck: {"uncertainty_awareness": -0.15} for ck in CELL_KEYS if ck != "caa__qwen2.5-7b"},
        },
    )
    pass_arm_data = A.load_arm_summary(pass_arm_json)
    pass_record = A.build_seed_record(20260723, pass_arm_json, pass_arm_data)
    records = [r for r in records if r["seed"] != 20260723] + [pass_record]

    agg = A.aggregate_across_seeds(records)
    cas = agg["cell_axis_stats"]
    assert cas["caa__qwen2.5-7b"]["single_seed_positive_surfaced"] is True
    for ck in CELL_KEYS:
        if ck != "caa__qwen2.5-7b":
            assert cas[ck]["single_seed_positive_surfaced"] is False


def test_no_pooling_single_seed_positive_not_averaged_away(tmp_path):
    """Anti-pooling (§4b): a pass in seed A must survive even if seed B has negative diff.

    cross-seed average of deliberation would be 0.0 — pooling would lose the pass signal.
    any_true_pass must still contain seed A's pass.
    """
    arm_json_A = _write_seed_dir(
        tmp_path / "A",
        20260723,
        mean_diffs_by_cell={
            "caa__qwen2.5-7b": {"deliberation": 0.20, "uncertainty_awareness": -0.15},
            **{ck: {"uncertainty_awareness": -0.15} for ck in CELL_KEYS if ck != "caa__qwen2.5-7b"},
        },
    )
    arm_json_B = _write_seed_dir(
        tmp_path / "B",
        20260724,
        mean_diffs_by_cell={
            "caa__qwen2.5-7b": {"deliberation": -0.20, "uncertainty_awareness": -0.15},
            **{ck: {"uncertainty_awareness": -0.15} for ck in CELL_KEYS if ck != "caa__qwen2.5-7b"},
        },
    )
    rec_A = A.build_seed_record(20260723, arm_json_A, A.load_arm_summary(arm_json_A))
    rec_B = A.build_seed_record(20260724, arm_json_B, A.load_arm_summary(arm_json_B))

    agg = A.aggregate_across_seeds([rec_A, rec_B])

    # Confirm the cross-seed average for deliberation is indeed 0 (pooling would mask pass)
    delib_avg = agg["cell_axis_stats"]["caa__qwen2.5-7b"]["deliberation"]["mean_diff_across_seeds"]
    assert delib_avg == pytest.approx(0.0)

    # The pass from seed A must still be surfaced (not pooled away)
    assert agg["has_any_true_pass"] is True
    tp = next(
        (e for e in agg["any_true_pass"]
         if e["seed"] == 20260723
         and e["cell_key"] == "caa__qwen2.5-7b"
         and e["axis"] == "deliberation"),
        None,
    )
    assert tp is not None, "True pass from seed A must not be averaged away (§4b anti-pooling)"
