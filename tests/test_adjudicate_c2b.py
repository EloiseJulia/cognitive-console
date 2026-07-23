"""Tests for the FROZEN C2b adjudication harness (prereg §4/§5), offline + no torch."""

import numpy as np
import pytest

from cognitive_console.experiments import adjudicate_c2b as A
from cognitive_console.experiments.adjudicate_c2b import (
    AxisAdjSpec, OutcomeSampler, SampleBatch,
)
from cognitive_console.steering.generate import SyntheticC2bTaskBackend
from cognitive_console.experiments.adjudicate_c2b import BackendOutcomeSampler
from cognitive_console.eval import c2b_tasks


# --------------------------------------------------------------------------- #
# Frozen parameters are exactly the pre-registered values (§5)
# --------------------------------------------------------------------------- #
def test_frozen_parameters_match_prereg():
    assert A.ALPHA_GRID == (2.0, 4.0, 6.0, 8.0, 12.0, 16.0, 24.0)
    assert A.DELTA == 0.05
    assert A.K_SAMPLES == 5
    assert A.N_ITEMS_BY_AXIS == {"deliberation": 60, "skepticism": 60,
                                 "uncertainty_awareness": 80}
    assert A.COHERENCE_MAX_RATIO == 1.5
    assert A.BOOTSTRAP_B >= 10000
    assert A.BONFERRONI_CI_LEVEL == pytest.approx(1.0 - 0.05 / 3.0)


# --------------------------------------------------------------------------- #
# Paired cluster bootstrap (§4)
# --------------------------------------------------------------------------- #
def test_bootstrap_ci_brackets_known_mean():
    rng = np.random.default_rng(1)
    true_mean = 0.2
    d = true_mean + rng.normal(0.0, 0.1, size=300)
    ci = A.cluster_bootstrap_ci(d, b=10000, ci_level=A.BONFERRONI_CI_LEVEL, seed=7)
    assert ci.point == pytest.approx(float(d.mean()), abs=1e-9)
    assert ci.ci_lo < true_mean < ci.ci_hi
    assert ci.excludes_zero()  # a clearly-positive mean excludes 0


def test_bootstrap_is_deterministic_under_seed():
    d = np.linspace(-0.1, 0.3, 50)
    a = A.cluster_bootstrap_ci(d, b=5000, seed=42)
    b = A.cluster_bootstrap_ci(d, b=5000, seed=42)
    assert (a.ci_lo, a.ci_hi, a.point) == (b.ci_lo, b.ci_hi, b.point)


def test_bootstrap_ci_level_is_bonferroni():
    d = np.full(40, 0.1)
    ci = A.cluster_bootstrap_ci(d, b=2000, seed=0)
    assert ci.ci_level == pytest.approx(1.0 - 0.05 / 3.0)


def test_cluster_vs_sample_level_differ_when_k_gt_1():
    # Build [n, k] with strong WITHIN-item correlation: each item has a shared
    # offset across its k samples plus tiny per-sample noise. Item-level (cluster)
    # resampling must give a WIDER CI than (incorrectly) pooling all n*k samples.
    rng = np.random.default_rng(3)
    n, k = 40, 5
    item_offset = rng.normal(0.2, 0.3, size=(n, 1))          # between-item variance
    noise = rng.normal(0.0, 0.01, size=(n, k))               # tiny within-item noise
    mat = item_offset + noise
    clus = A.cluster_bootstrap_ci(mat, b=8000, seed=5, cluster=True)
    samp = A.cluster_bootstrap_ci(mat, b=8000, seed=5, cluster=False)
    # same point estimate, DIFFERENT width; clustering respects the nesting => wider.
    assert clus.point == pytest.approx(samp.point, abs=1e-9)
    width_cluster = clus.ci_hi - clus.ci_lo
    width_sample = samp.ci_hi - samp.ci_lo
    assert width_cluster != pytest.approx(width_sample)
    assert width_cluster > width_sample


def test_ci_excludes_zero_helper():
    assert A.ci_excludes_zero(0.1, 0.3) is True
    assert A.ci_excludes_zero(-0.1, 0.3) is False
    assert A.ci_excludes_zero(-0.3, -0.1) is True


# --------------------------------------------------------------------------- #
# Per-axis pass rule + three-tier verdict (§4)
# --------------------------------------------------------------------------- #
def test_axis_pass_requires_all_three_conditions():
    # CI excludes 0, mean>=delta, coherence ok -> pass.
    assert A.axis_pass(0.06, 0.02, 0.10, True) is True
    # mean below delta -> fail even if CI excludes 0.
    assert A.axis_pass(0.04, 0.01, 0.07, True) is False
    # CI includes 0 -> fail.
    assert A.axis_pass(0.06, -0.01, 0.13, True) is False
    # coherence gate failed -> fail.
    assert A.axis_pass(0.06, 0.02, 0.10, False) is False


@pytest.mark.parametrize("passes,expected", [
    ({"a": True, "b": True, "c": True}, A.VERDICT_STRONG_GO),
    ({"a": True, "b": True, "c": False}, A.VERDICT_STRONG_GO),
    ({"a": True, "b": False, "c": False}, A.VERDICT_CONDITIONAL_GO),
    ({"a": False, "b": False, "c": False}, A.VERDICT_KILL),
])
def test_three_tier_verdict(passes, expected):
    assert A.three_tier_verdict(passes) == expected


# --------------------------------------------------------------------------- #
# DEV/TEST split (§2/§4)
# --------------------------------------------------------------------------- #
def test_dev_test_split_disjoint_and_deterministic():
    ids = [f"item-{i:02d}" for i in range(30)]
    s1 = A.split_dev_test(ids, dev_fraction=1 / 3, seed=11)
    s2 = A.split_dev_test(ids, dev_fraction=1 / 3, seed=11)
    assert s1.dev_ids == s2.dev_ids and s1.test_ids == s2.test_ids
    assert set(s1.dev_ids) & set(s1.test_ids) == set()
    assert set(s1.dev_ids) | set(s1.test_ids) == set(ids)
    assert len(s1.dev_ids) == 10 and len(s1.test_ids) == 20


# --------------------------------------------------------------------------- #
# A controllable recording sampler for selection-leakage + gate tests
# --------------------------------------------------------------------------- #
class RecordingSampler(OutcomeSampler):
    def __init__(self, outcome_fn, degeneracy_fn=None):
        self.outcome_fn = outcome_fn
        self.degeneracy_fn = degeneracy_fn or (lambda axis, item, instr, alpha: 0.1)
        self.calls = []

    def sample(self, axis, item, instruction, alpha, k, direction, layer):
        self.calls.append({"id": item["id"], "instruction": instruction, "alpha": float(alpha)})
        o = float(self.outcome_fn(axis, item, instruction, alpha))
        d = float(self.degeneracy_fn(axis, item, instruction, alpha))
        return SampleBatch(outcomes=[o] * k, degeneracies=[d] * k)


def _spec(axis="deliberation", n=30):
    items = [{"id": f"it-{i:02d}", "prompt": f"q{i}", "answer": str(i)} for i in range(n)]
    strong = [("p-weak", "weak instruction"), ("p-strong", "STRONG instruction")]
    return AxisAdjSpec(axis=axis, items=items, strong_prompts=strong,
                       neutral_prompt="neutral", direction=np.ones(8), layer=3)


def test_selection_only_touches_dev_items_no_test_leakage():
    spec = _spec(n=30)
    ids = [it["id"] for it in spec.items]
    split = A.split_dev_test(ids, dev_fraction=1 / 3, seed=0)
    dev_items = [it for it in spec.items if it["id"] in set(split.dev_ids)]

    sampler = RecordingSampler(outcome_fn=lambda ax, it, instr, a: 0.5)
    A.select_on_dev(sampler, spec, dev_items, k=5, alpha_grid=A.ALPHA_GRID)
    touched = {c["id"] for c in sampler.calls}
    assert touched <= set(split.dev_ids)
    assert touched & set(split.test_ids) == set()


def test_selection_picks_best_prompt_and_best_alpha_on_dev():
    spec = _spec(n=30)
    ids = [it["id"] for it in spec.items]
    split = A.split_dev_test(ids, dev_fraction=1 / 3, seed=0)
    dev_items = [it for it in spec.items if it["id"] in set(split.dev_ids)]

    # STRONG instruction beats weak; steer outcome rises with alpha (best = 24).
    def outcome(ax, it, instr, alpha):
        if alpha == 0:
            return 0.8 if "STRONG" in instr else 0.3
        return min(1.0, 0.05 * alpha)
    sel = A.select_on_dev(RecordingSampler(outcome), spec, dev_items, k=5)
    assert sel.best_prompt_id == "p-strong"
    assert sel.frozen_alpha == 24.0
    assert sel.any_alpha_passes_gate is True


def test_coherence_gate_discards_degenerate_cell():
    spec = _spec(n=30)
    ids = [it["id"] for it in spec.items]
    split = A.split_dev_test(ids, dev_fraction=1 / 3, seed=0)
    dev_items = [it for it in spec.items if it["id"] in set(split.dev_ids)]

    # Highest steer outcome is at alpha=24 but it is DEGENERATE (deg 1.0 >> 1.5x
    # baseline 0.1); the gate must discard it and freeze the best GATED alpha (16).
    def outcome(ax, it, instr, alpha):
        return min(1.0, 0.04 * alpha) if alpha else 0.3

    def degeneracy(ax, it, instr, alpha):
        if alpha == 0:
            return 0.1  # baseline
        return 1.0 if alpha >= 24 else 0.1
    sel = A.select_on_dev(RecordingSampler(outcome, degeneracy), spec, dev_items, k=5)
    assert sel.frozen_alpha == 16.0            # 24 discarded by the coherence gate
    row24 = next(r for r in sel.alpha_grid if r["alpha"] == 24.0)
    assert row24["coherence_ok"] is False


def test_all_alphas_degenerate_means_axis_cannot_pass():
    spec = _spec(n=30)
    ids = [it["id"] for it in spec.items]

    def outcome(ax, it, instr, alpha):
        return 0.9 if alpha else 0.1

    def degeneracy(ax, it, instr, alpha):
        return 0.1 if alpha == 0 else 1.0  # every steered cell degenerate
    sampler = RecordingSampler(outcome, degeneracy)
    res = A.adjudicate_axis(sampler, spec, k=5, bootstrap_b=2000, seed=0)
    assert res.dev_selection["frozen_alpha"] is None
    assert res.coherence_ok is False
    assert res.passed is False


# --------------------------------------------------------------------------- #
# Whole adjudication end-to-end, offline, WITHOUT torch (§ tests)
# --------------------------------------------------------------------------- #
def _fixture_spec(axis):
    task = c2b_tasks.load_c2b_task(axis, use_fixture=True)
    strong = [("p1", "Think step by step and be careful; question the premise; state confidence.")]
    return AxisAdjSpec(axis=axis, items=task.items, strong_prompts=strong,
                       neutral_prompt="Answer.", direction=np.ones(8), layer=3)


def test_whole_adjudication_runs_offline_and_produces_verdict():
    axes = ["deliberation", "skepticism", "uncertainty_awareness"]
    specs = [_fixture_spec(a) for a in axes]

    # Synthetic task backend: prompt channel (has markers) ~0.4 intensity (< 0.5
    # threshold => wrong), steering adds 0.1*alpha => a real behavioral GAP.
    def sampler_for_axis(axis):
        task = c2b_tasks.load_c2b_task(axis, use_fixture=True)
        backend = SyntheticC2bTaskBackend(axis, task.items, prompt_gain=0.4,
                                          alpha_gain=0.1, threshold=0.5)
        return BackendOutcomeSampler(backend, do_sample=False)

    report = A.adjudicate(sampler_for_axis, specs, bootstrap_b=2000, seed=0)
    assert report.verdict in {A.VERDICT_STRONG_GO, A.VERDICT_CONDITIONAL_GO, A.VERDICT_KILL}
    # With a clean synthetic gap on all three axes, steering beats the prompt.
    assert report.verdict == A.VERDICT_STRONG_GO
    for res in report.axis_results:
        assert res.n_dev + res.n_test == len(res.per_item_prompt) + res.n_dev
        assert res.mean_diff >= A.DELTA
        assert res.ci_lo > 0.0
        # conflict is present but flagged SECONDARY-only
        assert "SECONDARY" in res.conflict["note"]


def test_adjudication_report_serializes():
    specs = [_fixture_spec("deliberation")]

    def sampler_for_axis(axis):
        task = c2b_tasks.load_c2b_task(axis, use_fixture=True)
        return BackendOutcomeSampler(SyntheticC2bTaskBackend(axis, task.items),
                                     do_sample=False)
    report = A.adjudicate(sampler_for_axis, specs, bootstrap_b=1000, seed=0)
    d = report.to_dict()
    assert d["verdict"] in {A.VERDICT_STRONG_GO, A.VERDICT_CONDITIONAL_GO, A.VERDICT_KILL}
    assert d["frozen_params"]["delta"] == 0.05
    assert d["frozen_params"]["bonferroni_ci_level"] == pytest.approx(1 - 0.05 / 3)
