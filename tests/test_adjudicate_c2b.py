"""Tests for the FROZEN C2b adjudication harness (prereg §4/§5), offline + no torch."""

import numpy as np
import pytest
import random

from cognitive_console.experiments import adjudicate_c2b as A
from cognitive_console.experiments.adjudicate_c2b import (
    AxisAdjSpec, OutcomeSampler, SampleBatch,
)
from cognitive_console.steering.generate import SyntheticC2bTaskBackend, GenBackend
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


# --------------------------------------------------------------------------- #
# FIX 1 — uncertainty axis uses the PROPER per-item 1 - Brier end-to-end (D-0025)
# --------------------------------------------------------------------------- #
def test_uncertainty_sample_outcome_is_per_item_brier():
    item = {"id": "u1", "answer": "Canberra"}
    # confident + correct -> 1 - (1 - 1)^2 = 1.0
    conf_correct = A.score_sample_outcome(
        "uncertainty_awareness", item, "Answer: Canberra. Confidence: 100%.")
    assert conf_correct == pytest.approx(1.0)
    # overconfident + wrong -> 1 - (1 - 0)^2 = 0.0 (near 0)
    over_wrong = A.score_sample_outcome(
        "uncertainty_awareness", item, "Answer: Sydney. Confidence: 100%.")
    assert over_wrong == pytest.approx(0.0, abs=1e-9)
    # matches the scorer's Brier exactly (no L1 anywhere in the flow)
    from cognitive_console.eval import scorers as S
    assert not hasattr(S, "per_item_calibration_score")
    assert A.score_sample_outcome(
        "uncertainty_awareness", item, "Answer: Canberra. Confidence: 90%.") \
        == pytest.approx(S.per_item_brier(1, 0.9))


# --------------------------------------------------------------------------- #
# FIX 2 — sampled generation is reproducible under the run seed
# --------------------------------------------------------------------------- #
class _SeededStochasticBackend(GenBackend):
    """A stochastic GenBackend keyed on the per-call seed (no torch needed): it
    draws its 'answer' from ``random.Random(seed)`` so identical seeds reproduce
    identical generations, exactly like a torch-seeded sampled model."""

    def generate(self, prompt, steer=None, max_new_tokens=128,
                 do_sample=False, temperature=1.0, seed=None):
        r = random.Random(seed)
        return f"Let me think. Answer: {r.randint(0, 9)}."


def test_sampled_generation_reproducible_under_same_seed():
    items = [{"id": f"it-{i:02d}", "prompt": f"q{i}", "answer": str(i % 10)}
             for i in range(8)]
    backend = _SeededStochasticBackend()

    def run(base_seed):
        s = BackendOutcomeSampler(backend, do_sample=True, seed=base_seed)
        return [s.sample("deliberation", it, "instr", 4.0, 5, np.ones(8), 3).outcomes
                for it in items]

    a = run(20260723)
    b = run(20260723)
    assert a == b  # identical run seed -> bit-identical per-item outcomes

    # a DIFFERENT run seed produces different per-(item, sample) torch seeds.
    s1 = BackendOutcomeSampler(backend, do_sample=True, seed=20260723)
    s2 = BackendOutcomeSampler(backend, do_sample=True, seed=999)
    assert (s1._call_seed("deliberation", items[0], 4.0, 0)
            != s2._call_seed("deliberation", items[0], 4.0, 0))
    # per-sample seeds within one item differ (so the k samples actually vary)
    assert (s1._call_seed("deliberation", items[0], 4.0, 0)
            != s1._call_seed("deliberation", items[0], 4.0, 1))


# --------------------------------------------------------------------------- #
# FIX 4 — coherence gate additive floor (mildly-repetitive cell not discarded)
# --------------------------------------------------------------------------- #
def test_coherence_gate_additive_floor_keeps_mildly_repetitive_cell():
    spec = _spec(n=30)
    ids = [it["id"] for it in spec.items]
    split = A.split_dev_test(ids, dev_fraction=1 / 3, seed=0)
    dev_items = [it for it in spec.items if it["id"] in set(split.dev_ids)]

    # baseline degeneracy is 0; a mildly-repetitive-but-coherent steer cell (deg
    # 0.01 < eps_floor 0.02) must NOT be spuriously discarded. With the old
    # ceiling = 1.5 * 0 == 0 it would (0.01 <= 0 is False).
    def outcome(ax, it, instr, alpha):
        return 0.9 if alpha else 0.3

    def degeneracy(ax, it, instr, alpha):
        return 0.0 if alpha == 0 else 0.01
    sel = A.select_on_dev(RecordingSampler(outcome, degeneracy), spec, dev_items, k=5)
    assert sel.frozen_alpha is not None
    row = next(r for r in sel.alpha_grid if r["alpha"] == sel.frozen_alpha)
    assert row["coherence_ok"] is True
    assert A.COHERENCE_EPS_FLOOR == 0.02
    assert A.frozen_params_dict()["coherence_eps_floor"] == 0.02


def test_coherence_floor_still_conservative_on_a_broken_cell():
    # A genuinely degenerate cell (deg 1.0) is still discarded even with the floor.
    spec = _spec(n=30)
    ids = [it["id"] for it in spec.items]
    split = A.split_dev_test(ids, dev_fraction=1 / 3, seed=0)
    dev_items = [it for it in spec.items if it["id"] in set(split.dev_ids)]

    def outcome(ax, it, instr, alpha):
        return 0.9 if alpha else 0.3

    def degeneracy(ax, it, instr, alpha):
        return 0.1 if alpha == 0 else 1.0  # 1.0 >> 1.5*0.1 + 0.02 = 0.17
    sel = A.select_on_dev(RecordingSampler(outcome, degeneracy), spec, dev_items, k=5)
    assert sel.frozen_alpha is None


# --------------------------------------------------------------------------- #
# HARDEN FIX 4 — up-front planned generation count (budget visibility)
# --------------------------------------------------------------------------- #
def test_plan_generation_counts_matches_hand_count():
    # _spec: 2 strong prompts; alpha_grid=7; k=5; n=30 -> n_dev=10, n_test=20.
    spec = _spec(n=30)
    per_axis, total = A.plan_generation_counts([spec], k=5)
    # DEV = 5*10*(2 prompts + 1 baseline + 7 alphas) = 500
    # TEST = 5*20*(prompt+steer+baseline+conflict+conflict_pole = 5) = 500
    assert per_axis[spec.axis] == 1000
    assert total == 1000


def test_plan_generation_counts_uses_frozen_n_defaults():
    # With the frozen N=60/60/80, n_strong=16, k=5, grid=7 the planned TOTAL is
    # the budget the Manager sanity-checks before committing GPU time.
    def mk(axis, n):
        items = [{"id": f"{axis}-{i}", "prompt": f"q{i}", "answer": str(i)}
                 for i in range(n)]
        strong = [(f"p{j}", f"prompt {j}") for j in range(16)]
        return AxisAdjSpec(axis=axis, items=items, strong_prompts=strong,
                           neutral_prompt="n", direction=np.ones(8), layer=3)
    specs = [mk("deliberation", 60), mk("skepticism", 60),
             mk("uncertainty_awareness", 80)]
    per_axis, total = A.plan_generation_counts(specs, k=5)
    assert per_axis["deliberation"] == 3400
    assert per_axis["skepticism"] == 3400
    assert per_axis["uncertainty_awareness"] == 4565
    assert total == 11365


def test_progress_tracker_counts_and_eta():
    p = A.ProgressTracker(total_planned=100)
    p.add(20, fresh=True)
    p.add(30, fresh=False)
    assert p.done == 50
    assert p.fresh == 20
    assert p._eta() >= 0.0


# --------------------------------------------------------------------------- #
# HARDEN FIX 2 — checkpointing + deterministic RESUME -> identical verdict
# --------------------------------------------------------------------------- #
def _synth_factory():
    def sampler_for_axis(axis):
        task = c2b_tasks.load_c2b_task(axis, use_fixture=True)
        backend = SyntheticC2bTaskBackend(axis, task.items, prompt_gain=0.4,
                                          alpha_gain=0.1, threshold=0.5)
        return BackendOutcomeSampler(backend, do_sample=False)
    return sampler_for_axis


class _PoisonSampler(OutcomeSampler):
    """Fails loudly if asked to GENERATE — proves a resumed run used the cache."""
    def sample(self, axis, item, instruction, alpha, k, direction, layer):
        raise AssertionError("generation attempted despite a complete checkpoint")


def test_checkpoint_store_roundtrip(tmp_path):
    cp = A.CheckpointStore(tmp_path / "ck", "cfg-abc", seed=7)
    assert cp.get("deliberation", A.PHASE_TEST_STEER, "alpha=4.0", "it-1") is None
    cp.put("deliberation", A.PHASE_TEST_STEER, "alpha=4.0", "it-1",
           [1.0, 0.0, 1.0], [0.1, 0.1, 0.1], 4.0, "neutral")
    cp.close()
    # a NEW store on the same dir with the same config reloads the cell
    cp2 = A.CheckpointStore(tmp_path / "ck", "cfg-abc", seed=7)
    got = cp2.get("deliberation", A.PHASE_TEST_STEER, "alpha=4.0", "it-1")
    assert got == ([1.0, 0.0, 1.0], [0.1, 0.1, 0.1])
    # a DIFFERENT config does NOT resume (stale outcomes never reused)
    cp3 = A.CheckpointStore(tmp_path / "ck", "cfg-DIFFERENT", seed=7)
    assert cp3.get("deliberation", A.PHASE_TEST_STEER, "alpha=4.0", "it-1") is None


def test_fresh_flag_clears_checkpoints(tmp_path):
    cp = A.CheckpointStore(tmp_path / "ck", "cfg", seed=1)
    cp.put("skepticism", A.PHASE_DEV_ALPHA, "alpha=2.0", "s-0",
           [1.0], [0.0], 2.0, "n")
    cp.close()
    cp_fresh = A.CheckpointStore(tmp_path / "ck", "cfg", seed=1, fresh=True)
    assert cp_fresh.get("skepticism", A.PHASE_DEV_ALPHA, "alpha=2.0", "s-0") is None


def test_full_resume_skips_all_generation_and_matches_verdict(tmp_path):
    axes = ["deliberation", "skepticism", "uncertainty_awareness"]
    specs = [_fixture_spec(a) for a in axes]

    # RUN 1: populate the checkpoint with the synthetic backend.
    cp1 = A.CheckpointStore(tmp_path / "ck", "fp-1", seed=0)
    ctx1 = A.RunContext(checkpoint=cp1, progress=A.ProgressTracker(1))
    rep1 = A.adjudicate(_synth_factory(), specs, bootstrap_b=2000, seed=0, ctx=ctx1)
    cp1.close()

    # RUN 2: resume. A poison sampler proves NO generation happens (all cached),
    # yet the FROZEN verdict + per-axis mean(d) are bit-identical to run 1.
    cp2 = A.CheckpointStore(tmp_path / "ck", "fp-1", seed=0)
    ctx2 = A.RunContext(checkpoint=cp2, progress=A.ProgressTracker(1))
    rep2 = A.adjudicate(lambda axis: _PoisonSampler(), specs,
                        bootstrap_b=2000, seed=0, ctx=ctx2)
    cp2.close()

    assert rep2.verdict == rep1.verdict
    assert rep2.axis_passes == rep1.axis_passes
    for r1, r2 in zip(rep1.axis_results, rep2.axis_results):
        assert r2.mean_diff == pytest.approx(r1.mean_diff, nan_ok=True)
        assert r2.per_item_diff == r1.per_item_diff


def test_partial_resume_regenerates_missing_cells_identically(tmp_path):
    axis = "deliberation"
    specs = [_fixture_spec(axis)]

    cp1 = A.CheckpointStore(tmp_path / "ck", "fp-2", seed=0)
    ctx1 = A.RunContext(checkpoint=cp1)
    rep1 = A.adjudicate(_synth_factory(), specs, bootstrap_b=2000, seed=0, ctx=ctx1)
    cp1.close()

    # Simulate a crash mid TEST-steer: drop that phase's checkpoint file.
    ((tmp_path / "ck") / f"{axis}_{A.PHASE_TEST_STEER}.jsonl").unlink()

    cp2 = A.CheckpointStore(tmp_path / "ck", "fp-2", seed=0)
    ctx2 = A.RunContext(checkpoint=cp2)
    rep2 = A.adjudicate(_synth_factory(), specs, bootstrap_b=2000, seed=0, ctx=ctx2)
    cp2.close()

    # The deterministic backend reproduces the dropped cell -> identical verdict.
    assert rep2.verdict == rep1.verdict
    assert rep2.axis_results[0].per_item_steer == rep1.axis_results[0].per_item_steer
    assert rep2.axis_results[0].mean_diff == pytest.approx(rep1.axis_results[0].mean_diff)


# --------------------------------------------------------------------------- #
# HARDEN FIX 3 — batched sample_batch is equivalent to per-item sampling
# --------------------------------------------------------------------------- #
class _FakeBatchBackend(GenBackend):
    """A GenBackend that also exposes ``generate_batch`` (like SteeredHFBackend).
    Deterministic (greedy synthetic answers), so a padded batch is IDENTICAL to
    per-sequence generation — the offline analogue of the gated real-model test."""

    def __init__(self, axis, items):
        self._syn = SyntheticC2bTaskBackend(axis, items, prompt_gain=0.4,
                                            alpha_gain=0.1, threshold=0.5)
        self.batch_calls = 0

    def generate(self, prompt, steer=None, max_new_tokens=128,
                 do_sample=False, temperature=1.0, seed=None):
        return self._syn.generate(prompt, steer, max_new_tokens)

    def generate_batch(self, prompts, steer=None, max_new_tokens=128,
                       seeds=None, do_sample=False, temperature=1.0):
        self.batch_calls += 1
        return [self._syn.generate(p, steer, max_new_tokens) for p in prompts]


def test_batched_sample_batch_equivalent_to_unbatched(tmp_path):
    axis = "deliberation"
    task = c2b_tasks.load_c2b_task(axis, use_fixture=True)
    items = list(task.items)

    backend = _FakeBatchBackend(axis, items)
    batched = BackendOutcomeSampler(backend, do_sample=False, batch_size=16)
    unbatched = BackendOutcomeSampler(backend, do_sample=False, batch_size=1)
    assert batched.supports_batch is True
    assert unbatched.supports_batch is False

    b = batched.sample_batch(axis, items, "Think step by step.", 4.0, 5,
                             np.ones(8), 3)
    u = [unbatched.sample(axis, it, "Think step by step.", 4.0, 5, np.ones(8), 3)
         for it in items]
    assert backend.batch_calls >= 1  # the batched path really used generate_batch
    assert [x.outcomes for x in b] == [x.outcomes for x in u]
    assert [x.degeneracies for x in b] == [x.degeneracies for x in u]


def test_channel_chunking_respects_batch_size(tmp_path):
    # With batch_size=16 and k=5, items_per_batch = 16//5 = 3 => ceil(9/3)=3 batches
    # for the 9-item deliberation fixture. Outcomes must match the per-item path.
    axis = "deliberation"
    task = c2b_tasks.load_c2b_task(axis, use_fixture=True)
    items = list(task.items)
    backend = _FakeBatchBackend(axis, items)
    sampler = BackendOutcomeSampler(backend, do_sample=False, batch_size=16)
    outs, degs, mat = A._channel_item_outcomes(
        sampler, axis, items, "Think step by step.", 4.0, 5, np.ones(8), 3)
    assert outs.shape[0] == len(items)
    assert mat.shape == (len(items), 5)
    expected_batches = -(-len(items) // (16 // 5))
    assert backend.batch_calls == expected_batches
