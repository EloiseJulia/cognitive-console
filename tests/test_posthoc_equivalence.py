"""Unit tests for scripts/posthoc_equivalence.py.

POST-HOC / exploratory / NOT pre-registered (D-0056).

Uses small synthetic arrays + spot-checks against real arm_full artifacts.
No GPU, no torch, no model weights required.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import posthoc_equivalence as PE

REPO = Path(__file__).resolve().parents[1]
ARM_FULL = REPO / "results" / "arm_full"


# ---------------------------------------------------------------------------
# bootstrap_ci
# ---------------------------------------------------------------------------
class TestBootstrapCI:
    def test_point_equals_mean(self):
        d = np.array([0.1, 0.2, 0.3, -0.05, 0.0])
        point, lo, hi = PE.bootstrap_ci(d, ci_level=0.90, b=5000, seed=0)
        assert math.isclose(point, float(d.mean()), rel_tol=1e-9)

    def test_deterministic_under_seed(self):
        d = np.linspace(-0.1, 0.3, 40)
        a = PE.bootstrap_ci(d, ci_level=0.90, b=5000, seed=99)
        b = PE.bootstrap_ci(d, ci_level=0.90, b=5000, seed=99)
        assert a == b

    def test_ci_bounds_ordered(self):
        d = np.random.default_rng(7).normal(0.05, 0.15, 40)
        _, lo, hi = PE.bootstrap_ci(d, ci_level=0.90, b=5000, seed=1)
        assert lo < hi

    def test_narrow_ci_for_constant_diffs(self):
        d = np.full(50, 0.10)
        _, lo, hi = PE.bootstrap_ci(d, ci_level=0.90, b=5000, seed=2)
        assert abs(lo - 0.10) < 1e-9
        assert abs(hi - 0.10) < 1e-9

    def test_wider_ci_for_more_variance(self):
        rng = np.random.default_rng(3)
        narrow = rng.normal(0.0, 0.05, 50)
        wide = rng.normal(0.0, 0.30, 50)
        _, lo_n, hi_n = PE.bootstrap_ci(narrow, ci_level=0.90, b=5000, seed=4)
        _, lo_w, hi_w = PE.bootstrap_ci(wide, ci_level=0.90, b=5000, seed=4)
        assert (hi_w - lo_w) > (hi_n - lo_n)

    def test_negative_mean_ci_below_zero_large_sample(self):
        d = np.full(60, -0.10)
        _, lo, hi = PE.bootstrap_ci(d, ci_level=0.90, b=5000, seed=5)
        assert hi < 0.0


# ---------------------------------------------------------------------------
# tost_verdict
# ---------------------------------------------------------------------------
class TestTostVerdict:
    def test_negative_steer_vs_prompt_contrast_when_ci_hi_below_zero(self):
        assert (
            PE.tost_verdict(point=-0.10, ci_lo_90=-0.15, ci_hi_90=-0.03)
            == PE.VERDICT_NEGATIVE_STEER_VS_PROMPT_CONTRAST
        )

    def test_negative_steer_vs_prompt_contrast_boundary(self):
        # ci_hi exactly 0 does not qualify (must be strictly < 0)
        result = PE.tost_verdict(point=-0.05, ci_lo_90=-0.10, ci_hi_90=0.0)
        assert result != PE.VERDICT_NEGATIVE_STEER_VS_PROMPT_CONTRAST

    def test_equivalent_when_ci_within_sesoi(self):
        # CI entirely within (-0.05, +0.05)
        verdict = PE.tost_verdict(point=0.01, ci_lo_90=-0.03, ci_hi_90=0.03)
        assert verdict == PE.VERDICT_EQUIVALENT

    def test_equivalent_boundary_just_inside(self):
        verdict = PE.tost_verdict(point=0.0, ci_lo_90=-0.049, ci_hi_90=0.049)
        assert verdict == PE.VERDICT_EQUIVALENT

    def test_underpowered_ci_spans_zero_and_exceeds_sesoi(self):
        # CI includes 0 and extends beyond δ = 0.05
        verdict = PE.tost_verdict(point=0.025, ci_lo_90=-0.03, ci_hi_90=0.075)
        assert verdict == PE.VERDICT_UNDERPOWERED

    def test_superiority_ci_above_zero_mean_above_delta(self):
        verdict = PE.tost_verdict(point=0.08, ci_lo_90=0.01, ci_hi_90=0.15)
        assert verdict == PE.VERDICT_SUPERIORITY

    def test_superiority_requires_mean_ge_delta(self):
        # CI above 0 but mean < δ → NOT superiority
        verdict = PE.tost_verdict(point=0.03, ci_lo_90=0.01, ci_hi_90=0.05)
        # ci_lo_90 > 0 but mean < 0.05 → NOT superiority → should be EQUIVALENT or UNDERPOWERED
        assert verdict != PE.VERDICT_SUPERIORITY

    def test_underpowered_ci_spans_minus_delta(self):
        # CI spans from well below -δ to above 0
        verdict = PE.tost_verdict(point=-0.05, ci_lo_90=-0.25, ci_hi_90=0.05)
        assert verdict == PE.VERDICT_UNDERPOWERED


# ---------------------------------------------------------------------------
# compute_mde
# ---------------------------------------------------------------------------
class TestComputeMDE:
    def test_se_positive_for_varied_diffs(self):
        d = np.array([0.1, -0.05, 0.2, 0.0, -0.1] * 10)
        mde = PE.compute_mde(d)
        assert mde["se_estimate"] > 0.0

    def test_mde_superiority_positive(self):
        d = np.linspace(-0.1, 0.2, 40)
        mde = PE.compute_mde(d)
        assert mde["mde_superiority_80pct_power"] > 0.0

    def test_tost_powered_for_small_variance(self):
        # Very small variance → tost_powered should be True
        d = np.full(80, 0.02) + np.random.default_rng(0).normal(0, 0.001, 80)
        mde = PE.compute_mde(d)
        assert mde["tost_powered_for_equiv"] is True

    def test_tost_not_powered_for_large_variance(self):
        # Large variance relative to SESOI → underpowered for TOST
        d = np.linspace(-0.5, 0.5, 40)
        mde = PE.compute_mde(d)
        assert mde["tost_powered_for_equiv"] is False

    def test_mde_keys_present(self):
        d = np.full(40, 0.05)
        mde = PE.compute_mde(d)
        for key in ("n", "se_estimate", "mde_superiority_80pct_power",
                    "mde_tost_max_equiv_80pct_power", "tost_powered_for_equiv"):
            assert key in mde

    def test_n_matches_input(self):
        d = np.zeros(37)
        mde = PE.compute_mde(d)
        assert mde["n"] == 37


# ---------------------------------------------------------------------------
# analyse_cell (integration with frozen artifact)
# ---------------------------------------------------------------------------
@pytest.mark.skipif(not ARM_FULL.exists(), reason="arm_full artifacts not present")
class TestAnalyseCell:
    CELLS = [
        ("caa__qwen2.5-7b", "caa", "qwen2.5-7b"),
        ("caa__llama3-8b", "caa", "llama3-8b"),
        ("iti__qwen2.5-7b", "iti", "qwen2.5-7b"),
        ("iti__llama3-8b", "iti", "llama3-8b"),
    ]

    @pytest.fixture(params=CELLS, ids=[c[0] for c in CELLS])
    def cell_result(self, request):
        cell_key, method, model = request.param
        cell_json = ARM_FULL / f"cell_{cell_key}" / "c2b_adjudication_results.json"
        return PE.analyse_cell(cell_json, b=2000, seed=0)

    def test_three_axes_per_cell(self, cell_result):
        assert len(cell_result["axes"]) == 3

    def test_axes_names(self, cell_result):
        names = {a["axis"] for a in cell_result["axes"]}
        assert names == {"deliberation", "skepticism", "uncertainty_awareness"}

    def test_point_matches_prereg_mean(self, cell_result):
        # The re-bootstrapped point must equal the prereg stored mean_diff (same data)
        # The script asserts this internally; here we verify the stored prereg_mean_diff
        # matches what's in the raw JSON
        cell_key = f"cell_{cell_result['method']}__{cell_result['model']}"
        cell_json = ARM_FULL / cell_key / "c2b_adjudication_results.json"
        if not cell_json.exists():
            pytest.skip("cell JSON not found")
        raw = json.loads(cell_json.read_text())
        raw_by_axis = {a["axis"]: a for a in raw["axes"]}
        for ax in cell_result["axes"]:
            raw_ax = raw_by_axis[ax["axis"]]
            assert math.isclose(ax["prereg_mean_diff"], raw_ax["mean_diff"], abs_tol=1e-5)

    def test_tost_ci_narrower_than_prereg_ci(self, cell_result):
        # 90% CI must be narrower than 98.33% CI
        for ax in cell_result["axes"]:
            tost_width = ax["tost_ci_hi"] - ax["tost_ci_lo"]
            prereg_width = ax["prereg_ci_hi"] - ax["prereg_ci_lo"]
            assert tost_width <= prereg_width + 1e-6, (
                f"{ax['axis']}: TOST CI width {tost_width:.4f} > prereg CI width {prereg_width:.4f}"
            )

    def test_uncertainty_negative_steer_vs_prompt_contrast(self, cell_result):
        # All 4 cells must show the comparator-bound negative contrast.
        for ax in cell_result["axes"]:
            if ax["axis"] == "uncertainty_awareness":
                assert ax["tost_verdict"] == PE.VERDICT_NEGATIVE_STEER_VS_PROMPT_CONTRAST, (
                    "Expected NEGATIVE_STEER_VS_PROMPT_CONTRAST for uncertainty "
                    f"but got {ax['tost_verdict']}"
                )

    def test_deliberation_and_skepticism_not_harm_or_superior(self, cell_result):
        # deliberation and skepticism should not be negative contrasts or superiority.
        # (they may be EQUIVALENT or UNDERPOWERED depending on the cell)
        for ax in cell_result["axes"]:
            if ax["axis"] in ("deliberation", "skepticism"):
                assert ax["tost_verdict"] not in (
                    PE.VERDICT_NEGATIVE_STEER_VS_PROMPT_CONTRAST,
                    PE.VERDICT_SUPERIORITY,
                ), (
                    f"Unexpected verdict {ax['tost_verdict']} for {ax['axis']}"
                )

    def test_mde_fields_present(self, cell_result):
        for ax in cell_result["axes"]:
            assert ax.get("mde") is not None
            assert ax["mde"].get("n") is not None
            assert ax["mde"].get("se_estimate") is not None

    def test_tost_ci_bounds_ordered(self, cell_result):
        for ax in cell_result["axes"]:
            assert ax["tost_ci_lo"] < ax["tost_ci_hi"]


# ---------------------------------------------------------------------------
# analyse_arm (integration)
# ---------------------------------------------------------------------------
@pytest.mark.skipif(not ARM_FULL.exists(), reason="arm_full artifacts not present")
class TestAnalyseArm:
    def test_four_cells_returned(self):
        results = PE.analyse_arm(ARM_FULL, b=2000, seed=0)
        assert len(results) == 4

    def test_all_uncertainty_axes_are_negative_steer_vs_prompt_contrasts(self):
        results = PE.analyse_arm(ARM_FULL, b=2000, seed=0)
        negative_count = sum(
            1 for cell in results for ax in cell["axes"]
            if ax["axis"] == "uncertainty_awareness"
            and ax["tost_verdict"] == PE.VERDICT_NEGATIVE_STEER_VS_PROMPT_CONTRAST
        )
        assert negative_count == 4, f"Expected 4 negative contrasts, got {negative_count}"

    def test_no_superiority_verdicts(self):
        results = PE.analyse_arm(ARM_FULL, b=2000, seed=0)
        for cell in results:
            for ax in cell["axes"]:
                assert ax["tost_verdict"] != PE.VERDICT_SUPERIORITY


# ---------------------------------------------------------------------------
# build_conclusions_md + build_latex_table smoke tests
# ---------------------------------------------------------------------------
@pytest.mark.skipif(not ARM_FULL.exists(), reason="arm_full artifacts not present")
class TestOutputGenerators:
    @pytest.fixture(scope="class")
    def arm_results(self):
        return PE.analyse_arm(ARM_FULL, b=1000, seed=0)

    def test_md_contains_posthoc_label(self, arm_results):
        md = PE.build_conclusions_md(arm_results, None)
        assert "POST-HOC" in md
        assert "exploratory" in md.lower()

    def test_md_contains_brier_deferred(self, arm_results):
        md = PE.build_conclusions_md(arm_results, None)
        assert "DEFERRED" in md

    def test_md_contains_negative_steer_vs_prompt_section(self, arm_results):
        md = PE.build_conclusions_md(arm_results, None)
        assert "NEGATIVE_STEER_VS_PROMPT_CONTRAST" in md
        assert "Direct Qwen/CAA steer-vs-baseline remains near zero." in md

    def test_latex_contains_autogens_header(self, arm_results):
        tex = PE.build_latex_table(arm_results)
        assert "AUTO-GENERATED" in tex
        assert "POST-HOC" in tex
        assert "—" not in tex
        assert r"\textemdash" not in tex
        assert "---" not in tex

    def test_latex_no_hand_edit_warning(self, arm_results):
        tex = PE.build_latex_table(arm_results)
        assert "DO NOT HAND-EDIT" in tex

    def test_latex_tabular_environment(self, arm_results):
        tex = PE.build_latex_table(arm_results)
        assert r"\begin{table*}" in tex
        assert r"\end{table*}" in tex
        assert r"\begin{tabular}" in tex

    def test_latex_twelve_data_rows(self, arm_results):
        # 4 cells × 3 axes = 12 data rows (excluding the header row)
        tex = PE.build_latex_table(arm_results)
        # Count lines with \\ and & that are NOT the header (header starts with spaces + "Method")
        data_rows = [
            line for line in tex.splitlines()
            if r"\\" in line and "&" in line and "Method" not in line
            and r"\toprule" not in line and r"\midrule" not in line
        ]
        assert len(data_rows) == 12

    def test_no_hand_coded_numbers_in_latex(self, arm_results):
        """Verify LaTeX table uses numbers from arm_results, not hardcoded."""
        tex = PE.build_latex_table(arm_results)
        # Spot check: prereg mean of uncertainty_awareness for CAA×Qwen is ≈ -0.228
        # This should appear as "-0.228" in the table (from artifact)
        for cell in arm_results:
            if "qwen" in cell["model"] and cell["method"] == "caa":
                for ax in cell["axes"]:
                    if ax["axis"] == "uncertainty_awareness":
                        expected = f"{ax['prereg_mean_diff']:+.3f}"
                        assert expected in tex, (
                            f"Expected {expected} to appear in LaTeX table"
                        )


# ---------------------------------------------------------------------------
# Brier decomposition feasibility constant
# ---------------------------------------------------------------------------
class TestBrierFeasibility:
    def test_feasibility_is_deferred(self):
        assert PE.BRIER_FEASIBILITY == "DEFERRED"

    def test_reason_mentions_raw_pairs(self):
        assert "confidence" in PE.BRIER_REASON.lower()
        assert "correctness" in PE.BRIER_REASON.lower() or "correct" in PE.BRIER_REASON.lower()

    def test_reason_mentions_transcripts(self):
        assert "transcript" in PE.BRIER_REASON.lower()

    def test_reason_no_fabricated_data(self):
        # The reason must explicitly state no numbers were imputed
        assert "not" in PE.BRIER_REASON.lower() or "cannot" in PE.BRIER_REASON.lower()


class TestCheckoutIndependentProvenance:
    def test_stable_artifact_path_ignores_checkout_root(self):
        suffix = Path("results") / "arm_full" / "cell_caa__qwen2.5-7b" / "c2b_adjudication_results.json"
        first = PE.stable_artifact_path(Path("C:/checkout-one") / suffix)
        second = PE.stable_artifact_path(Path("D:/different/depth/checkout-two") / suffix)
        assert first == second == suffix.as_posix()

    @pytest.mark.skipif(not ARM_FULL.exists(), reason="arm_full artifacts not present")
    def test_analysis_json_is_byte_identical_for_relative_and_absolute_paths(self):
        relative = ARM_FULL.relative_to(REPO)
        first = PE.analyse_arm(REPO / relative, b=100, seed=7)
        second = PE.analyse_arm((REPO / relative).resolve(), b=100, seed=7)
        first_bytes = json.dumps(first, indent=2).encode("utf-8")
        second_bytes = json.dumps(second, indent=2).encode("utf-8")
        assert first_bytes == second_bytes
        assert str(REPO.resolve()).encode("utf-8") not in first_bytes
