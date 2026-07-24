"""Tests for OOD diagnostics + C1 null-relative robustness helpers."""

import numpy as np
import pytest

from cognitive_console.analysis.ood import (
    C1SensitivityPoint,
    HM_SPEARMAN_THRESHOLD,
    HM_TOTAL_CELLS,
    bootstrap_spearman,
    c1_null_relative_effect,
    estimate_ood_distribution,
    hm_arm_verdict,
    hm_cell_result,
    per_item_ood_stats,
    summarize_c1_layer_norm_sensitivity,
    whitened_mahalanobis,
)


def _unit(v):
    v = np.asarray(v, dtype=np.float64)
    return v / np.linalg.norm(v)


def _planted_hm_cell(seed=0, n=120, d=10):
    rng = np.random.default_rng(seed)
    ref = rng.normal(0.0, 1.0, size=(300, d))
    base = rng.normal(0.0, 1.0, size=(n, d))
    off = rng.uniform(0.0, 2.5, size=n)
    direction = _unit(rng.normal(size=d))
    steered = base + off[:, None] * direction[None, :]
    # delta = steer - baseline; larger off-manifold => more negative delta.
    delta = 0.08 - 0.22 * off + rng.normal(0.0, 0.01, size=n)
    return steered, base, ref, delta


def test_hm_detects_planted_positive_association():
    steered, baseline, ref, delta = _planted_hm_cell(seed=1)
    stats = per_item_ood_stats(
        steered,
        baseline,
        ref,
        reference_id="c1-ref",
        source_hash="sha256:ref-1",
        reference_split_id="c1-train",
        evaluated_split_id="cell-1-uncertainty-test",
    )
    dist = stats.mahalanobis
    r = hm_cell_result("cell-a", dist, delta, b=4000, seed=3)
    assert r.rho >= HM_SPEARMAN_THRESHOLD
    assert r.ci_lo > 0.0
    assert r.passed


def test_hm_null_data_does_not_always_pass():
    rng = np.random.default_rng(2)
    ref = rng.normal(0.0, 1.0, size=(200, 8))
    baseline = rng.normal(0.0, 1.0, size=(120, 8))
    steered = rng.normal(0.0, 1.0, size=(120, 8))
    delta = rng.normal(0.0, 0.2, size=120)  # independent of OOD distance
    stats = per_item_ood_stats(
        steered,
        baseline,
        ref,
        reference_id="c1-ref",
        source_hash="sha256:ref-2",
        reference_split_id="c1-train",
        evaluated_split_id="cell-null-test",
    )
    dist = stats.mahalanobis
    r = hm_cell_result("cell-null", dist, delta, b=3000, seed=7)
    assert abs(r.rho) < 0.30
    assert not r.passed


def test_mahalanobis_stays_finite_with_singular_covariance():
    rng = np.random.default_rng(0)
    x = rng.normal(size=(120, 4))
    # collinearity -> singular covariance (x3 duplicates x1, x4 duplicates x2).
    ref = np.column_stack([x[:, 0], x[:, 1], x[:, 0], x[:, 1]])
    dist = estimate_ood_distribution(ref, shrinkage=0.1, ridge=1e-6)
    q = ref[:20] + 0.1
    m = whitened_mahalanobis(q, dist)
    assert np.all(np.isfinite(m))
    assert np.all(m >= 0.0)


def test_hm_aggregate_verdict_requires_three_of_four_cells():
    cell_data = {}
    for idx in range(3):
        steered, baseline, ref, delta = _planted_hm_cell(seed=10 + idx)
        stats = per_item_ood_stats(
            steered,
            baseline,
            ref,
            reference_id="c1-ref",
            source_hash=f"sha256:ref-good-{idx}",
            reference_split_id="c1-train",
            evaluated_split_id=f"good-{idx}-test",
        )
        cell_data[f"good-{idx}"] = (stats.mahalanobis, delta)
    rng = np.random.default_rng(99)
    cell_data["bad-3"] = (
        rng.normal(0.0, 1.0, size=120),
        rng.normal(0.0, 0.2, size=120),
    )
    v = hm_arm_verdict(cell_data, b=2000, seed=11)
    assert v.passed_cells == 3
    assert v.supported


def test_hm_arm_verdict_raises_when_not_all_frozen_cells_are_present():
    cell_data = {}
    for idx in range(HM_TOTAL_CELLS - 1):
        steered, baseline, ref, delta = _planted_hm_cell(seed=30 + idx)
        stats = per_item_ood_stats(
            steered,
            baseline,
            ref,
            reference_id="c1-ref",
            source_hash=f"sha256:ref-partial-{idx}",
            reference_split_id="c1-train",
            evaluated_split_id=f"partial-{idx}-test",
        )
        cell_data[f"good-{idx}"] = (stats.mahalanobis, delta)
    with pytest.raises(ValueError, match="requires exactly"):
        hm_arm_verdict(cell_data, b=2000, seed=13)


def test_hm_aggregate_verdict_fails_with_only_two_passing_cells():
    rng = np.random.default_rng(1234)
    cell_data = {}
    n = 120
    x = np.linspace(0.0, 3.0, num=n)
    for idx in range(2):
        d = 0.4 - 0.5 * x + rng.normal(0.0, 0.01, size=n)
        cell_data[f"good-{idx}"] = (x + rng.normal(0.0, 0.01, size=n), d)
    for idx in range(2):
        cell_data[f"bad-{idx}"] = (
            rng.normal(0.0, 1.0, size=120),
            rng.normal(0.0, 0.2, size=120),
        )
    v = hm_arm_verdict(cell_data, b=2000, seed=17)
    assert v.passed_cells == 2
    assert not v.supported


def test_per_item_ood_stats_requires_reference_provenance():
    steered, baseline, ref, _delta = _planted_hm_cell(seed=70)
    with pytest.raises(ValueError, match="reference_id is required"):
        per_item_ood_stats(
            steered,
            baseline,
            ref,
            source_hash="sha256:ref-missing-id",
            reference_split_id="c1-train",
            evaluated_split_id="cell-a-test",
        )


def test_per_item_ood_stats_rejects_same_split_reference():
    steered, baseline, ref, _delta = _planted_hm_cell(seed=71)
    with pytest.raises(ValueError, match="must differ"):
        per_item_ood_stats(
            steered,
            baseline,
            ref,
            reference_id="c1-ref",
            source_hash="sha256:ref-same-split",
            reference_split_id="shared-split",
            evaluated_split_id="shared-split",
        )


def test_per_item_ood_stats_rejects_same_content_even_if_split_id_is_renamed():
    steered, baseline, _ref, _delta = _planted_hm_cell(seed=171)
    with pytest.raises(ValueError, match="content guardrail"):
        per_item_ood_stats(
            steered,
            baseline,
            steered.copy(),
            reference_id="c1-ref",
            source_hash="sha256:ref-renamed-self-fit",
            reference_split_id="independent-looking-label",
            evaluated_split_id="different-label",
        )


def test_per_item_ood_stats_rejects_high_overlap_reference():
    steered, baseline, ref, _delta = _planted_hm_cell(seed=172, n=200)
    ref_like_steered = steered.copy()
    ref_like_steered[:2] = ref[:2]
    with pytest.raises(ValueError, match="content guardrail"):
        per_item_ood_stats(
            steered,
            baseline,
            ref_like_steered,
            reference_id="c1-ref",
            source_hash="sha256:ref-overlap",
            reference_split_id="train-like",
            evaluated_split_id="test-like",
        )


def test_per_item_ood_stats_accepts_independent_reference_provenance():
    steered, baseline, ref, _delta = _planted_hm_cell(seed=72)
    stats = per_item_ood_stats(
        steered,
        baseline,
        ref,
        reference_id="c1-ref",
        source_hash="sha256:ref-independent",
        reference_split_id="c1-train",
        evaluated_split_id="cell-b-test",
    )
    assert stats.mahalanobis.shape == (steered.shape[0],)
    assert stats.norm_inflation.shape == (steered.shape[0],)
    assert stats.reference_provenance["reference_id"] == "c1-ref"
    assert stats.reference_provenance["split_id"] == "c1-train"
    assert stats.reference_provenance["evaluated_split_id"] == "cell-b-test"


def test_cluster_aware_bootstrap_ci_is_not_narrower_than_item_level():
    rng = np.random.default_rng(77)
    n_clusters = 20
    items_per_cluster = 6
    n = n_clusters * items_per_cluster
    cluster_ids = np.repeat(np.arange(n_clusters), items_per_cluster)
    cluster_signal = rng.normal(0.0, 1.0, size=n_clusters)
    x = np.repeat(cluster_signal, items_per_cluster) + rng.normal(0.0, 0.02, size=n)
    d = -(0.35 * np.repeat(cluster_signal, items_per_cluster) + rng.normal(0.0, 0.08, size=n))

    item_level = bootstrap_spearman(x, d, b=4000, seed=5)
    cluster_level = bootstrap_spearman(x, d, b=4000, seed=5, cluster_ids=cluster_ids)
    item_width = item_level.ci_hi - item_level.ci_lo
    cluster_width = cluster_level.ci_hi - cluster_level.ci_lo
    assert cluster_width >= item_width


def test_c1_null_relative_effect_has_expected_sign():
    eff = c1_null_relative_effect(
        prompt_reach=4.0,
        pole_reach=10.0,
        random_null_prompt_reaches=[0.8, 1.0, 1.2, 1.1],
        prompt_null_prompt_reaches=[2.6, 3.0, 3.2, 2.8],
    )
    assert eff.observed_ratio == pytest.approx(0.4)
    assert eff.random_null_delta > 0.0
    assert eff.prompt_null_delta > 0.0
    assert eff.random_null_cohens_d > 0.0
    assert eff.prompt_null_cohens_d > 0.0


def test_layer_norm_sensitivity_summary_aggregates_points():
    pts = [
        C1SensitivityPoint(layer=10, norm_scale=0.5, random_null_cohens_d=1.2, prompt_null_cohens_d=0.8),
        C1SensitivityPoint(layer=10, norm_scale=1.0, random_null_cohens_d=1.0, prompt_null_cohens_d=0.6),
        C1SensitivityPoint(layer=14, norm_scale=0.5, random_null_cohens_d=0.2, prompt_null_cohens_d=-0.2),
        C1SensitivityPoint(layer=14, norm_scale=1.0, random_null_cohens_d=0.8, prompt_null_cohens_d=0.4),
    ]
    s = summarize_c1_layer_norm_sensitivity(pts)
    assert s.n_points == 4
    assert s.max_combined_effect >= s.mean_combined_effect >= s.min_combined_effect
    assert s.positive_fraction == pytest.approx(0.75)
    assert set(s.per_layer_mean_effect) == {10, 14}
    assert set(s.per_norm_mean_effect) == {"0.5", "1"}


def test_bootstrap_spearman_deterministic_given_seed():
    rng = np.random.default_rng(123)
    x = rng.normal(size=100)
    d = 0.1 - 0.2 * x + rng.normal(0.0, 0.02, size=100)
    a = bootstrap_spearman(x, d, b=2000, seed=42)
    b = bootstrap_spearman(x, d, b=2000, seed=42)
    assert (a.rho, a.ci_lo, a.ci_hi) == pytest.approx((b.rho, b.ci_lo, b.ci_hi))
