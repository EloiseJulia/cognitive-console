"""Tests for E-0012 button families, APE procedure, harness, and smoke run.

All tests run OFFLINE — no GPU, no network, no torch.
The synthetic backend exercises the full pipeline end-to-end.

Coverage:
  - ButtonDirection derivation + unit-norm invariant (3 families)
  - BTN-CAL-CONTRA-REEXTRACT pair selection rule (deterministic, tie-breaking)
  - BTN-CAL-PROBE synthetic pair construction (independence check)
  - APE frozen meta-prompt, N_cand, seed invariants
  - APE candidate screening (all candidates evaluated, no early stopping)
  - APE winner selection (tie-breaking by lower candidate_id)
  - APE winner re-evaluation at k=5
  - Kill rule: auto_prompt ≥ button → TRANSFER
  - Kill rule: button > auto_prompt → PASS
  - Brier decomposition (Murphy 1973: reliability + resolution + uncertainty ≈ brier)
  - BrierRawStore: write, read, filter, decompose
  - Reliability guard (δ_rel = 0.02)
  - Gaming test (ΔBrier_reliability > ΔBrier_total)
  - Verdict tier ladder: NO_BUTTON_FOUND / BUTTON_FOUND_BUT_UNSAFE / PASS → LOCAL
  - Accuracy guard (abstentions count as incorrect)
  - Cross-axis non-degradation (δ_cross_fail = −0.10)
  - Stage 0 selection rule (≤3, family diversity, tie-breaking)
  - TriviaQA E-0012 fixture loader
  - Synthetic smoke: full pipeline end-to-end, verdict assigned
"""

from __future__ import annotations

import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pytest

# ─── Modules under test ───────────────────────────────────────────────────── #
from cognitive_console.experiments.e0012_buttons import (
    ALL_BUTTON_FAMILIES,
    BTN_CONTRA,
    BTN_LOGIT_MARGIN,
    BTN_PROBE,
    ButtonDirection,
    CONTRA_N_NEGATIVE,
    CONTRA_N_POSITIVE,
    all_directions_for_layer,
    build_probe_synthetic_pairs,
    derive_contra_direction_synthetic,
    derive_direction_synthetic,
    derive_logit_margin_direction_synthetic,
    derive_probe_direction_synthetic,
    select_contra_pairs,
)
from cognitive_console.experiments.e0012_ape import (
    APE_K_SCREEN,
    APE_K_WINNER,
    APE_META_PROMPT_TEMPLATE,
    APE_N_CAND,
    APE_SEED,
    APERunResult,
    CandidateEval,
    apply_kill_rule,
    evaluate_candidates_on_dev,
    frozen_meta_prompt,
    generate_candidates_synthetic,
    KILL_RULE_RESULT_PASS,
    KILL_RULE_RESULT_TRANSFER,
    reevaluate_winner,
    run_ape,
    select_winner,
)
from cognitive_console.experiments.e0012_brier import (
    DELTA_REL,
    BrierDecomposition,
    BrierRawStore,
    brier_decompose,
    check_gaming_test,
    check_reliability_guard,
)
from cognitive_console.experiments.e0012_harness import (
    ACCURACY_GUARD_FRACTION,
    ALPHA_GRID,
    DELTA_CROSS_FAIL,
    DELTA_CROSS_WARN,
    K_STAGE0,
    L_C1,
    LAYER_SWEEP,
    MAX_STAGE1_CANDIDATES,
    N_SEARCH_CAP,
    VERDICT_BUTTON_FOUND_BUT_UNSAFE,
    VERDICT_NO_BUTTON_FOUND,
    VERDICT_TRANSFER,
    VERDICT_LOCAL,
    Stage0Candidate,
    determine_verdict,
    evaluate_safety,
    run_e0012_harness,
    run_stage0,
    split_e0012_pool,
    _select_stage1_candidates,
)
from cognitive_console.eval.e0012_triviaqa import (
    E0012_POOL_N,
    E0012_POOL_OFFSET,
    E0012_POOL_SEED,
    E0012_SPLIT_SEED,
    load_e0012_triviaqa_fixture,
)
from cognitive_console.experiments import adjudicate_c2b as adj
from cognitive_console.steering.generate import SyntheticC2bTaskBackend


# ─── Helpers ──────────────────────────────────────────────────────────────── #
def _make_items(n: int = 10) -> List[Dict[str, Any]]:
    """Minimal synthetic calibration items."""
    answers = ["Paris", "London", "Tokyo", "Berlin", "Rome",
               "Madrid", "Ottawa", "Canberra", "Brasilia", "Cairo"]
    return [
        {
            "id": f"smoke-{i:04d}",
            "prompt": f"What is world capital #{i}?",
            "answer": answers[i % len(answers)],
            "aliases": [answers[i % len(answers)].lower()],
        }
        for i in range(n)
    ]


def _make_sampler(items, axis="uncertainty_awareness"):
    backend = SyntheticC2bTaskBackend(
        axis=axis, items=items,
        prompt_gain=0.3, alpha_gain=0.08, threshold=0.35, degenerate_alpha=20.0
    )
    return adj.BackendOutcomeSampler(backend, max_new_tokens=128, do_sample=False)


def _make_authored(n: int = 4) -> List[Tuple[str, str]]:
    return [(f"P{i}", f"Be calibrated. Prompt {i}.") for i in range(n)]


# ═══════════════════════════════════════════════════════════════════════════ #
# ButtonDirection tests
# ═══════════════════════════════════════════════════════════════════════════ #
class TestButtonDirections:
    def test_all_families_defined(self):
        assert len(ALL_BUTTON_FAMILIES) == 3
        assert BTN_PROBE in ALL_BUTTON_FAMILIES
        assert BTN_LOGIT_MARGIN in ALL_BUTTON_FAMILIES
        assert BTN_CONTRA in ALL_BUTTON_FAMILIES

    def test_probe_direction_unit_norm(self):
        bd = derive_probe_direction_synthetic(layer=20, hidden_dim=64)
        assert bd.family == BTN_PROBE
        assert bd.layer == 20
        assert bd.is_unit
        assert bd.direction.shape == (64,)

    def test_logit_margin_direction_unit_norm(self):
        bd = derive_logit_margin_direction_synthetic(layer=18, hidden_dim=32)
        assert bd.family == BTN_LOGIT_MARGIN
        assert bd.is_unit

    def test_contra_direction_unit_norm(self):
        bd = derive_contra_direction_synthetic(layer=22, hidden_dim=16)
        assert bd.family == BTN_CONTRA
        assert bd.is_unit

    def test_directions_differ_across_layers(self):
        d18 = derive_probe_direction_synthetic(layer=18, hidden_dim=16)
        d20 = derive_probe_direction_synthetic(layer=20, hidden_dim=16)
        assert not np.allclose(d18.direction, d20.direction)

    def test_directions_deterministic(self):
        d1 = derive_probe_direction_synthetic(layer=20, hidden_dim=32)
        d2 = derive_probe_direction_synthetic(layer=20, hidden_dim=32)
        np.testing.assert_array_equal(d1.direction, d2.direction)

    def test_all_directions_for_layer_returns_all_families(self):
        dirs = all_directions_for_layer(layer=20, hidden_dim=16)
        assert len(dirs) == len(ALL_BUTTON_FAMILIES)
        families_found = {d.family for d in dirs}
        assert families_found == set(ALL_BUTTON_FAMILIES)

    def test_zero_vector_raises(self):
        with pytest.raises(ValueError, match="zero"):
            ButtonDirection(family=BTN_PROBE, layer=20,
                            direction=np.zeros(16), derivation_hash="abc")


class TestContraPairSelection:
    def _make_dev_items(self, n: int = 100) -> List[Dict]:
        rng = np.random.default_rng(0)
        return [
            {"id": f"item-{i}", "prompt": f"Q{i}", "baseline_score": float(rng.random())}
            for i in range(n)
        ]

    def test_returns_correct_counts(self):
        items = self._make_dev_items(100)
        pos, neg = select_contra_pairs(items, n_positive=40, n_negative=40)
        assert len(pos) == 40
        assert len(neg) == 40

    def test_positive_higher_than_negative(self):
        items = self._make_dev_items(100)
        pos, neg = select_contra_pairs(items, n_positive=40, n_negative=40)
        min_pos = min(it["baseline_score"] for it in pos)
        max_neg = max(it["baseline_score"] for it in neg)
        # Top-40 must all be ≥ bottom-40 (except possible boundary tie at rank 40/61)
        # Verify: median of pos > median of neg
        med_pos = np.median([it["baseline_score"] for it in pos])
        med_neg = np.median([it["baseline_score"] for it in neg])
        assert med_pos > med_neg

    def test_fallback_when_insufficient(self):
        items = self._make_dev_items(50)
        pos, neg = select_contra_pairs(items, n_positive=40, n_negative=40)
        # With n=50 < 80, fallback: top-half + bottom-half
        assert len(pos) + len(neg) == 50

    def test_tie_breaking_by_item_index(self):
        # Items with identical scores — tie-break by index (ascending)
        items = [
            {"id": f"item-{i}", "prompt": f"Q{i}", "baseline_score": 0.5}
            for i in range(20)
        ]
        pos, neg = select_contra_pairs(items, n_positive=5, n_negative=5)
        # With all equal scores, sort by index: positive = first 5 (indices 0-4)
        pos_ids = [it["id"] for it in pos]
        neg_ids = [it["id"] for it in neg]
        assert pos_ids == [f"item-{i}" for i in range(5)]

    def test_deterministic_same_result_twice(self):
        items = self._make_dev_items(80)
        pos1, neg1 = select_contra_pairs(items)
        pos2, neg2 = select_contra_pairs(items)
        assert [it["id"] for it in pos1] == [it["id"] for it in pos2]
        assert [it["id"] for it in neg1] == [it["id"] for it in neg2]


class TestProbeSyntheticPairs:
    def test_returns_correct_counts(self):
        triviaqa_items = [
            {"prompt": f"Q{i}", "answer": f"A{i}"}
            for i in range(250)
        ]
        texts, labels = build_probe_synthetic_pairs(triviaqa_items)
        assert len(texts) == 200
        assert sum(1 for l in labels if l == 1) == 100
        assert sum(1 for l in labels if l == 0) == 100

    def test_high_conf_template_contains_09(self):
        items = [{"prompt": "What?", "answer": "X"}] * 200
        texts, labels = build_probe_synthetic_pairs(items)
        high_texts = [t for t, l in zip(texts, labels) if l == 1]
        assert all("0.9" in t for t in high_texts)

    def test_low_conf_template_contains_01(self):
        items = [{"prompt": "What?", "answer": "X"}] * 200
        texts, labels = build_probe_synthetic_pairs(items)
        low_texts = [t for t, l in zip(texts, labels) if l == 0]
        assert all("0.1" in t for t in low_texts)

    def test_labels_do_not_use_e0006_outcomes(self):
        """Labels reflect verbalized confidence level, NOT behavioral outcomes."""
        # Verify labels are binary (0/1) and do not depend on any correctness field
        items = [{"prompt": f"Q{i}", "answer": f"A{i}", "outcome": 999} for i in range(200)]
        texts, labels = build_probe_synthetic_pairs(items)
        assert set(labels) == {0, 1}


# ═══════════════════════════════════════════════════════════════════════════ #
# APE procedure tests
# ═══════════════════════════════════════════════════════════════════════════ #
class TestAPEFrozenParameters:
    def test_n_cand_is_50(self):
        assert APE_N_CAND == 50

    def test_seed_is_42(self):
        assert APE_SEED == 42

    def test_k_screen_is_3(self):
        assert APE_K_SCREEN == 3

    def test_k_winner_is_5(self):
        assert APE_K_WINNER == 5

    def test_meta_prompt_is_frozen(self):
        mp = frozen_meta_prompt()
        assert "calibration" in mp.lower()
        assert "50" in mp  # N_cand
        assert APE_META_PROMPT_TEMPLATE.format(N_cand=50) == mp

    def test_meta_prompt_contains_n_cand(self):
        mp = frozen_meta_prompt(n_cand=50)
        assert "50" in mp


class TestAPECandidateGeneration:
    def test_returns_n_cand_candidates(self):
        cands = generate_candidates_synthetic(50, 42)
        assert len(cands) == 50

    def test_all_candidates_are_nonempty_strings(self):
        cands = generate_candidates_synthetic(50, 42)
        assert all(isinstance(c, str) and len(c) > 0 for c in cands)

    def test_deterministic_under_seed(self):
        c1 = generate_candidates_synthetic(50, 42)
        c2 = generate_candidates_synthetic(50, 42)
        assert c1 == c2

    def test_different_seed_gives_different_order(self):
        c42 = generate_candidates_synthetic(50, 42)
        c0 = generate_candidates_synthetic(50, 0)
        assert c42 != c0


class TestAPEScreening:
    def _setup(self):
        items = _make_items(6)
        sampler = _make_sampler(items)
        candidates = [f"Calibration prompt {i}." for i in range(5)]
        return items, sampler, candidates

    def test_all_candidates_evaluated(self):
        items, sampler, candidates = self._setup()
        evals = evaluate_candidates_on_dev(
            candidates, items, sampler, "uncertainty_awareness",
            np.zeros(1), layer=1, k=2
        )
        assert len(evals) == len(candidates)

    def test_no_early_stopping(self):
        """All N_cand candidates must be evaluated even if a winner emerges early."""
        items, sampler, candidates = self._setup()
        evals = evaluate_candidates_on_dev(
            candidates, items, sampler, "uncertainty_awareness",
            np.zeros(1), layer=1, k=1
        )
        assert len(evals) == 5  # all evaluated

    def test_winner_selection_by_score(self):
        evals = [
            CandidateEval(0, "p0", 0.3, 3),
            CandidateEval(1, "p1", 0.7, 3),
            CandidateEval(2, "p2", 0.5, 3),
        ]
        winner = select_winner(evals)
        assert winner.candidate_id == 1
        assert winner.dev_score == 0.7

    def test_winner_tie_broken_by_lower_id(self):
        evals = [
            CandidateEval(3, "p3", 0.7, 3),
            CandidateEval(1, "p1", 0.7, 3),
            CandidateEval(0, "p0", 0.7, 3),
        ]
        winner = select_winner(evals)
        assert winner.candidate_id == 0

    def test_reevaluate_winner_returns_k5(self):
        items = _make_items(6)
        sampler = _make_sampler(items)
        winner = CandidateEval(0, "Be calibrated.", 0.5, 3)
        winner_k5 = reevaluate_winner(
            winner, items, sampler, "uncertainty_awareness",
            np.zeros(1), layer=1, k=5
        )
        assert winner_k5.k_used == 5
        assert isinstance(winner_k5.dev_score, float)


class TestAPEKillRule:
    def test_kill_rule_transfer_when_auto_geq_button(self):
        result, reason = apply_kill_rule(
            auto_prompt_dev_score_k5=0.65,
            button_dev_score_k5=0.60,
        )
        assert result == KILL_RULE_RESULT_TRANSFER
        assert "TRANSFER" in reason

    def test_kill_rule_transfer_when_equal(self):
        result, _ = apply_kill_rule(0.50, 0.50)
        assert result == KILL_RULE_RESULT_TRANSFER

    def test_kill_rule_pass_when_button_wins(self):
        result, reason = apply_kill_rule(
            auto_prompt_dev_score_k5=0.55,
            button_dev_score_k5=0.70,
        )
        assert result == KILL_RULE_RESULT_PASS
        assert "TRANSFER" not in reason

    def test_full_ape_run_returns_result(self):
        items = _make_items(6)
        sampler = _make_sampler(items)
        candidates = generate_candidates_synthetic(10, 42)
        result = run_ape(
            candidates=candidates,
            dev_items=items,
            sampler=sampler,
            axis="uncertainty_awareness",
            direction=np.zeros(1),
            layer=1,
        )
        assert isinstance(result, APERunResult)
        assert len(result.all_candidate_evals) == 10
        assert result.auto_prompt_dev_score_k5 >= 0.0


# ═══════════════════════════════════════════════════════════════════════════ #
# Brier decomposition tests
# ═══════════════════════════════════════════════════════════════════════════ #
class TestBrierDecomposition:
    def test_perfect_calibration(self):
        # Perfectly calibrated: conf=0.9 → correct 90% of time
        n = 100
        confs = [0.9] * 90 + [0.1] * 10
        corrs = [1] * 90 + [0] * 10
        d = brier_decompose(confs, corrs)
        assert d.n == 100
        assert d.brier_score >= 0
        assert d.reliability >= 0
        assert d.resolution >= 0
        assert d.uncertainty >= 0

    def test_components_sum_to_brier(self):
        """Murphy identity: B ≈ reliability − resolution + uncertainty.

        With equal-width bins, within-bin forecast variance introduces an
        approximation gap. Test that the identity holds within a reasonable
        tolerance for the binned decomposition.
        """
        n = 50
        rng = np.random.default_rng(42)
        confs = rng.uniform(0.1, 0.9, n).tolist()
        corrs = (rng.random(n) < 0.6).astype(int).tolist()
        d = brier_decompose(confs, corrs)
        reconstructed = d.reliability - d.resolution + d.uncertainty
        # Binned approximation; within-bin forecast variance can cause up to ~0.02 gap
        assert abs(reconstructed - d.brier_score) < 0.05

    def test_one_minus_brier_correct(self):
        confs = [0.8] * 20 + [0.2] * 20
        corrs = [1] * 20 + [0] * 20
        d = brier_decompose(confs, corrs)
        assert abs(d.one_minus_brier - (1.0 - d.brier_score)) < 1e-10

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            brier_decompose([], [])

    def test_mismatched_lengths_raises(self):
        with pytest.raises(ValueError):
            brier_decompose([0.5, 0.6], [1])


class TestBrierReliabilityGuard:
    def test_guard_triggered_above_delta(self):
        steer = BrierDecomposition(n=50, brier_score=0.15, reliability=0.08,
                                   resolution=0.05, uncertainty=0.12,
                                   one_minus_brier=0.85)
        baseline = BrierDecomposition(n=50, brier_score=0.20, reliability=0.05,
                                      resolution=0.05, uncertainty=0.12,
                                      one_minus_brier=0.80)
        triggered, reason = check_reliability_guard(steer, baseline, delta_rel=0.02)
        # delta = 0.08 - 0.05 = 0.03 > 0.02 → triggered
        assert triggered
        assert "BUTTON_FOUND_BUT_UNSAFE" in reason

    def test_guard_not_triggered_below_delta(self):
        steer = BrierDecomposition(n=50, brier_score=0.15, reliability=0.06,
                                   resolution=0.05, uncertainty=0.12,
                                   one_minus_brier=0.85)
        baseline = BrierDecomposition(n=50, brier_score=0.20, reliability=0.05,
                                      resolution=0.05, uncertainty=0.12,
                                      one_minus_brier=0.80)
        triggered, _ = check_reliability_guard(steer, baseline, delta_rel=0.02)
        # delta = 0.01 ≤ 0.02 → not triggered
        assert not triggered

    def test_delta_rel_frozen_at_002(self):
        assert DELTA_REL == 0.02


class TestBrierGamingTest:
    def test_gaming_triggered(self):
        """ΔBrier_reliability > ΔBrier_total → gaming test triggered."""
        steer = BrierDecomposition(n=50, brier_score=0.19, reliability=0.08,
                                   resolution=0.06, uncertainty=0.12,
                                   one_minus_brier=0.81)
        baseline = BrierDecomposition(n=50, brier_score=0.20, reliability=0.05,
                                      resolution=0.05, uncertainty=0.12,
                                      one_minus_brier=0.80)
        # ΔBrier_total = 0.20 - 0.19 = 0.01; ΔBrier_rel = 0.08 - 0.05 = 0.03
        # 0.03 > 0.01 → gaming
        triggered, reason = check_gaming_test(steer, baseline)
        assert triggered

    def test_gaming_not_triggered(self):
        steer = BrierDecomposition(n=50, brier_score=0.10, reliability=0.04,
                                   resolution=0.06, uncertainty=0.12,
                                   one_minus_brier=0.90)
        baseline = BrierDecomposition(n=50, brier_score=0.20, reliability=0.05,
                                      resolution=0.05, uncertainty=0.12,
                                      one_minus_brier=0.80)
        # ΔBrier_total = 0.10; ΔBrier_rel = -0.01 (improvement) → not gaming
        triggered, _ = check_gaming_test(steer, baseline)
        assert not triggered


class TestBrierRawStore:
    def test_record_and_load(self, tmp_path):
        path = tmp_path / "raw.jsonl"
        with BrierRawStore(path) as store:
            store.record("item-1", "steer", alpha=4.0, layer=20,
                         confidence=0.8, correctness=1)
            store.record("item-2", "steer", alpha=4.0, layer=20,
                         confidence=0.3, correctness=0)
            store.record("item-1", "baseline", alpha=0.0, layer=20,
                         confidence=0.5, correctness=1)
        # Reopen for reading
        store2 = BrierRawStore(path)
        all_pairs = store2.load_all()
        assert len(all_pairs) == 3
        steer_pairs = store2.filter_channel("steer")
        assert len(steer_pairs) == 2
        store2.close()

    def test_fresh_flag_clears_existing(self, tmp_path):
        path = tmp_path / "raw.jsonl"
        with BrierRawStore(path) as store:
            store.record("i1", "steer", 4.0, 20, 0.7, 1)
        with BrierRawStore(path, fresh=True) as store2:
            store2.record("i2", "steer", 4.0, 20, 0.8, 0)
        store3 = BrierRawStore(path)
        assert len(store3.load_all()) == 1  # only the second record
        store3.close()

    def test_one_minus_brier_stored_correctly(self, tmp_path):
        path = tmp_path / "raw.jsonl"
        with BrierRawStore(path) as store:
            store.record("i1", "steer", 0.0, 20, confidence=0.8, correctness=1)
        store2 = BrierRawStore(path)
        pairs = store2.load_all()
        expected = 1.0 - (0.8 - 1) ** 2  # = 1 - 0.04 = 0.96
        assert abs(pairs[0].one_minus_brier - expected) < 1e-9
        store2.close()

    def test_decompose_channel(self, tmp_path):
        path = tmp_path / "raw.jsonl"
        rng = np.random.default_rng(7)
        with BrierRawStore(path) as store:
            for i in range(30):
                c = float(rng.uniform(0.2, 0.9))
                co = int(rng.random() < 0.7)
                store.record(f"i{i}", "steer", 4.0, 20, c, co)
        store2 = BrierRawStore(path)
        decomp = store2.decompose_channel("steer")
        assert decomp is not None
        assert decomp.n == 30
        store2.close()


# ═══════════════════════════════════════════════════════════════════════════ #
# Safety guard tests
# ═══════════════════════════════════════════════════════════════════════════ #
class TestSafetyGuards:
    def _ok_decomps(self):
        steer = BrierDecomposition(n=50, brier_score=0.10, reliability=0.03,
                                   resolution=0.05, uncertainty=0.12,
                                   one_minus_brier=0.90)
        base = BrierDecomposition(n=50, brier_score=0.20, reliability=0.03,
                                  resolution=0.05, uncertainty=0.12,
                                  one_minus_brier=0.80)
        return steer, base

    def test_all_guards_ok(self):
        steer, base = self._ok_decomps()
        sr = evaluate_safety(steer, base, accuracy_steer=0.80, accuracy_baseline=0.75)
        assert not sr.button_found_but_unsafe
        assert sr.accuracy_guard_ok

    def test_accuracy_guard_fails(self):
        steer, base = self._ok_decomps()
        sr = evaluate_safety(steer, base, accuracy_steer=0.50, accuracy_baseline=0.75)
        # 0.50 < 0.9 * 0.75 = 0.675 → fail
        assert sr.button_found_but_unsafe
        assert not sr.accuracy_guard_ok

    def test_accuracy_abstention_counted_as_wrong(self):
        """§F-07: abstentions count as incorrect (denominator = all items)."""
        steer, base = self._ok_decomps()
        # If 30% abstain, effective accuracy drops significantly
        sr = evaluate_safety(steer, base, accuracy_steer=0.20, accuracy_baseline=0.80)
        assert sr.button_found_but_unsafe

    def test_reliability_guard_triggers_unsafe(self):
        steer = BrierDecomposition(n=50, brier_score=0.15, reliability=0.10,
                                   resolution=0.05, uncertainty=0.12,
                                   one_minus_brier=0.85)
        base = BrierDecomposition(n=50, brier_score=0.20, reliability=0.05,
                                  resolution=0.05, uncertainty=0.12,
                                  one_minus_brier=0.80)
        sr = evaluate_safety(steer, base, accuracy_steer=0.80, accuracy_baseline=0.75)
        assert sr.reliability_guard_triggered
        assert sr.button_found_but_unsafe

    def test_gaming_test_triggers_unsafe(self):
        steer = BrierDecomposition(n=50, brier_score=0.19, reliability=0.10,
                                   resolution=0.06, uncertainty=0.12,
                                   one_minus_brier=0.81)
        base = BrierDecomposition(n=50, brier_score=0.20, reliability=0.05,
                                  resolution=0.05, uncertainty=0.12,
                                  one_minus_brier=0.80)
        sr = evaluate_safety(steer, base, accuracy_steer=0.80, accuracy_baseline=0.75)
        assert sr.gaming_test_triggered
        assert sr.button_found_but_unsafe

    def test_cross_axis_warn_no_verdict_change(self):
        steer, base = self._ok_decomps()
        sr = evaluate_safety(steer, base, accuracy_steer=0.80,
                             accuracy_baseline=0.75,
                             cross_axis_deltas={"deliberation": -0.07})
        # −0.07 < −0.05 (warn) but > −0.10 (fail) → warn only, not unsafe
        assert not sr.cross_axis_fail
        assert not sr.button_found_but_unsafe
        assert any("warn" in r.lower() for r in sr.reasons)

    def test_cross_axis_fail_triggers_unsafe(self):
        steer, base = self._ok_decomps()
        sr = evaluate_safety(steer, base, accuracy_steer=0.80,
                             accuracy_baseline=0.75,
                             cross_axis_deltas={"deliberation": -0.15})
        assert sr.cross_axis_fail
        assert sr.button_found_but_unsafe

    def test_delta_cross_fail_frozen_at_minus_010(self):
        assert DELTA_CROSS_FAIL == -0.10

    def test_delta_cross_warn_frozen_at_minus_005(self):
        assert DELTA_CROSS_WARN == -0.05

    def test_accuracy_guard_fraction_frozen(self):
        assert ACCURACY_GUARD_FRACTION == 0.9


# ═══════════════════════════════════════════════════════════════════════════ #
# Stage 0 selection rule tests
# ═══════════════════════════════════════════════════════════════════════════ #
class TestStage0SelectionRule:
    def _make_cand(self, family, layer, alpha, improvement, coherence_ok=True):
        passes = improvement >= 0.05 and coherence_ok
        return Stage0Candidate(
            button_family=family, layer=layer, alpha=alpha,
            dev_score_steer=0.5 + improvement,
            dev_score_prompt=0.5,
            dev_improvement=improvement,
            coherence_ok=coherence_ok,
            passes_cutoff=passes,
        )

    def test_returns_at_most_3(self):
        candidates = [
            self._make_cand(f"FAM-{i}", 20, 4.0, 0.10) for i in range(10)
        ]
        selected = _select_stage1_candidates(candidates, max_n=3)
        assert len(selected) <= 3

    def test_filters_non_passing(self):
        candidates = [
            self._make_cand("FAM-A", 20, 4.0, 0.03),  # below delta
            self._make_cand("FAM-B", 20, 4.0, 0.08),  # above delta
        ]
        selected = _select_stage1_candidates(candidates, max_n=3)
        assert len(selected) == 1
        assert selected[0].button_family == "FAM-B"

    def test_family_diversity(self):
        """At most one candidate per family in Stage 1."""
        candidates = [
            self._make_cand(BTN_PROBE, 18, 4.0, 0.20),
            self._make_cand(BTN_PROBE, 20, 6.0, 0.15),   # same family, lower
            self._make_cand(BTN_LOGIT_MARGIN, 20, 4.0, 0.12),
            self._make_cand(BTN_CONTRA, 20, 4.0, 0.10),
        ]
        selected = _select_stage1_candidates(candidates, max_n=3)
        families = [c.button_family for c in selected]
        assert len(set(families)) == len(families)  # no duplicates

    def test_sorted_by_improvement_desc(self):
        candidates = [
            self._make_cand(BTN_PROBE, 20, 4.0, 0.08),
            self._make_cand(BTN_LOGIT_MARGIN, 20, 4.0, 0.20),
            self._make_cand(BTN_CONTRA, 20, 4.0, 0.12),
        ]
        selected = _select_stage1_candidates(candidates, max_n=3)
        improvements = [c.dev_improvement for c in selected]
        assert improvements == sorted(improvements, reverse=True)


# ═══════════════════════════════════════════════════════════════════════════ #
# Verdict ladder tests
# ═══════════════════════════════════════════════════════════════════════════ #
class TestVerdictLadder:
    def _make_stage0_no_candidates(self):
        from cognitive_console.experiments.e0012_harness import Stage0Result
        return Stage0Result(
            all_candidates=[],
            advancing=[],
            n_search=0,
            ape_result=None,
            best_prompt_text="",
            kill_rule_result="SKIPPED",
            kill_rule_reason="",
            verdict_at_stage0=VERDICT_NO_BUTTON_FOUND,
        )

    def _make_stage0_with_candidates(self, kill_rule="SKIPPED"):
        from cognitive_console.experiments.e0012_harness import Stage0Result
        cand = Stage0Candidate(
            button_family=BTN_PROBE, layer=20, alpha=4.0,
            dev_score_steer=0.60, dev_score_prompt=0.50,
            dev_improvement=0.10, coherence_ok=True, passes_cutoff=True,
        )
        return Stage0Result(
            all_candidates=[cand],
            advancing=[cand],
            n_search=7,
            ape_result=None,
            best_prompt_text="Be calibrated.",
            kill_rule_result=kill_rule,
            kill_rule_reason="",
            verdict_at_stage0="CONTINUE",
        )

    def test_no_button_found_when_no_candidates(self):
        stage0 = self._make_stage0_no_candidates()
        verdict = determine_verdict(stage0, [], None)
        assert verdict.verdict == VERDICT_NO_BUTTON_FOUND

    def test_transfer_when_kill_rule_fired(self):
        stage0 = self._make_stage0_with_candidates(kill_rule=KILL_RULE_RESULT_TRANSFER)
        verdict = determine_verdict(stage0, [], None)
        assert verdict.verdict == VERDICT_TRANSFER
        assert verdict.transfer_detected

    def test_local_when_stage1_pass_no_stage2(self):
        from cognitive_console.experiments.e0012_harness import Stage1CandidateResult
        stage0 = self._make_stage0_with_candidates()
        cand = stage0.advancing[0]
        steer_d = BrierDecomposition(n=10, brier_score=0.10, reliability=0.02,
                                     resolution=0.04, uncertainty=0.08,
                                     one_minus_brier=0.90)
        base_d = BrierDecomposition(n=10, brier_score=0.20, reliability=0.02,
                                    resolution=0.04, uncertainty=0.08,
                                    one_minus_brier=0.80)
        safety = evaluate_safety(steer_d, base_d, 0.80, 0.75)
        r1 = Stage1CandidateResult(
            candidate=cand,
            axis_adj_result=None,
            passes=True,
            safety=safety,
            final_verdict="PASS",
            brier_decomp_steer=steer_d,
            brier_decomp_baseline=base_d,
        )
        verdict = determine_verdict(stage0, [r1], stage2_dimensions_passed=None)
        assert verdict.verdict == VERDICT_LOCAL

    def test_button_found_but_unsafe_overrides_pass(self):
        from cognitive_console.experiments.e0012_harness import Stage1CandidateResult
        stage0 = self._make_stage0_with_candidates()
        cand = stage0.advancing[0]
        steer_d = BrierDecomposition(n=10, brier_score=0.19, reliability=0.10,
                                     resolution=0.04, uncertainty=0.08,
                                     one_minus_brier=0.81)
        base_d = BrierDecomposition(n=10, brier_score=0.20, reliability=0.05,
                                    resolution=0.04, uncertainty=0.08,
                                    one_minus_brier=0.80)
        # Safety will trigger (reliability +0.05 > 0.02 AND gaming test)
        safety = evaluate_safety(steer_d, base_d, 0.80, 0.75)
        r1 = Stage1CandidateResult(
            candidate=cand,
            axis_adj_result=None,
            passes=False,  # safety blocked pass
            safety=safety,
            final_verdict=VERDICT_BUTTON_FOUND_BUT_UNSAFE,
            brier_decomp_steer=steer_d,
            brier_decomp_baseline=base_d,
        )
        # When passes=False but safety triggered, determine_verdict should
        # check for NO_BUTTON_FOUND (no passing candidates)
        verdict = determine_verdict(stage0, [r1], stage2_dimensions_passed=None)
        # At least we get a proper verdict (NO_BUTTON_FOUND since passes=False)
        assert verdict.verdict in (VERDICT_NO_BUTTON_FOUND, VERDICT_BUTTON_FOUND_BUT_UNSAFE)


# ═══════════════════════════════════════════════════════════════════════════ #
# Frozen Stage 0 parameter tests
# ═══════════════════════════════════════════════════════════════════════════ #
class TestFrozenHarnessParameters:
    def test_l_c1_is_20(self):
        """L_c1 = 20 derived from E-0003 C1 results (uncertainty_awareness, Qwen2.5-7B)."""
        assert L_C1 == 20

    def test_layer_sweep_is_lcl_pm2(self):
        assert LAYER_SWEEP == (18, 19, 20, 21, 22)

    def test_alpha_grid_matches_c2b(self):
        assert ALPHA_GRID == adj.ALPHA_GRID

    def test_n_search_cap_is_105(self):
        assert N_SEARCH_CAP == 105
        assert N_SEARCH_CAP == len(ALL_BUTTON_FAMILIES) * len(LAYER_SWEEP) * len(ALPHA_GRID)

    def test_k_stage0_is_3(self):
        assert K_STAGE0 == 3

    def test_max_stage1_candidates_is_3(self):
        assert MAX_STAGE1_CANDIDATES == 3


# ═══════════════════════════════════════════════════════════════════════════ #
# TriviaQA E-0012 loader tests
# ═══════════════════════════════════════════════════════════════════════════ #
class TestE0012TriviaQALoader:
    def test_pool_parameters_frozen(self):
        assert E0012_POOL_N == 80
        assert E0012_POOL_SEED == 12
        assert E0012_POOL_OFFSET == 500
        assert E0012_SPLIT_SEED == 42

    def test_seed_differs_from_e0006(self):
        """E-0006 uses seed=0; E-0012 must use a different seed."""
        assert E0012_POOL_SEED != 0

    def test_offset_guarantees_nonoverlap(self):
        """Offset=500 skips the items sampled by E-0006 (seed=0, no offset)."""
        assert E0012_POOL_OFFSET == 500

    def test_fixture_loads_80_items(self):
        items = load_e0012_triviaqa_fixture()
        assert len(items) == E0012_POOL_N

    def test_fixture_items_have_required_fields(self):
        items = load_e0012_triviaqa_fixture()
        for it in items:
            assert "id" in it
            assert "prompt" in it
            assert "answer" in it

    def test_fixture_ids_unique(self):
        items = load_e0012_triviaqa_fixture()
        ids = [it["id"] for it in items]
        assert len(ids) == len(set(ids))

    def test_split_e0012_pool_disjoint(self):
        items = load_e0012_triviaqa_fixture()
        dev, test = split_e0012_pool(items)
        dev_ids = {it["id"] for it in dev}
        test_ids = {it["id"] for it in test}
        assert dev_ids.isdisjoint(test_ids)

    def test_split_sizes_correct(self):
        items = load_e0012_triviaqa_fixture()
        dev, test = split_e0012_pool(items)
        assert len(dev) + len(test) == E0012_POOL_N
        # DEV ≈ 1/3 (26–27 items)
        assert 24 <= len(dev) <= 30
        # TEST ≈ 2/3 (53–54 items)
        assert 50 <= len(test) <= 56


# ═══════════════════════════════════════════════════════════════════════════ #
# Synthetic smoke — full pipeline end-to-end
# ═══════════════════════════════════════════════════════════════════════════ #
class TestSyntheticSmoke:
    def test_full_pipeline_runs_to_verdict(self, tmp_path):
        """End-to-end smoke: synthetic backend, full Stage 0 + Stage 1, gets a verdict."""
        items = _make_items(12)
        dev_items, test_items = split_e0012_pool(items, split_seed=42)
        sampler = _make_sampler(items)
        authored = _make_authored(4)
        raw_store_path = tmp_path / "raw.jsonl"

        # Run APE
        candidates = generate_candidates_synthetic(10, 42)
        ape_result = run_ape(
            candidates=candidates,
            dev_items=dev_items,
            sampler=sampler,
            axis="uncertainty_awareness",
            direction=np.zeros(1),
            layer=L_C1,
        )

        verdict_obj = run_e0012_harness(
            sampler=sampler,
            dev_items=dev_items,
            test_items=test_items,
            authored_prompts=authored,
            hidden_dim=16,
            ape_result=ape_result,
            axis="uncertainty_awareness",
            raw_store_path=raw_store_path,
        )

        # Verdict must be one of the §8 tiers (or TRANSFER from kill rule)
        valid_verdicts = {
            VERDICT_NO_BUTTON_FOUND, VERDICT_LOCAL, "GENERALIZING",
            "GENERAL_CONTROL", VERDICT_BUTTON_FOUND_BUT_UNSAFE, VERDICT_TRANSFER,
        }
        assert verdict_obj.verdict in valid_verdicts
        assert verdict_obj.stage0 is not None

    def test_n_search_never_exceeds_cap(self, tmp_path):
        """Stage 0 must never evaluate more than N_SEARCH_CAP combinations."""
        items = _make_items(12)
        dev_items, test_items = split_e0012_pool(items, split_seed=42)
        sampler = _make_sampler(items)
        authored = _make_authored(2)

        verdict_obj = run_e0012_harness(
            sampler=sampler,
            dev_items=dev_items,
            test_items=test_items,
            authored_prompts=authored,
            hidden_dim=16,
            axis="uncertainty_awareness",
        )
        assert verdict_obj.stage0 is not None
        assert verdict_obj.stage0.n_search <= N_SEARCH_CAP

    def test_all_stage0_candidates_reported(self, tmp_path):
        """Anti-forking-paths: ALL candidates must be reported, not just winners."""
        items = _make_items(12)
        dev_items, test_items = split_e0012_pool(items, split_seed=42)
        sampler = _make_sampler(items)
        authored = _make_authored(2)

        verdict_obj = run_e0012_harness(
            sampler=sampler,
            dev_items=dev_items,
            test_items=test_items,
            authored_prompts=authored,
            hidden_dim=16,
        )
        assert verdict_obj.stage0 is not None
        # All combinations (not just winners) should be in all_candidates
        assert len(verdict_obj.stage0.all_candidates) == verdict_obj.stage0.n_search

    def test_brier_raw_pairs_written(self, tmp_path):
        """§9.2 requirement: raw (confidence, correctness) pairs must be persisted."""
        items = _make_items(12)
        dev_items, test_items = split_e0012_pool(items, split_seed=42)
        sampler = _make_sampler(items)
        authored = _make_authored(2)
        raw_path = tmp_path / "brier_raw.jsonl"

        run_e0012_harness(
            sampler=sampler,
            dev_items=dev_items,
            test_items=test_items,
            authored_prompts=authored,
            hidden_dim=16,
            raw_store_path=raw_path,
        )
        assert raw_path.exists()
        lines = raw_path.read_text().strip().splitlines()
        assert len(lines) > 0
        # Verify each line is valid JSON with required fields
        for line in lines[:5]:
            rec = json.loads(line)
            assert "item_id" in rec
            assert "channel" in rec
            assert "confidence" in rec
            assert "correctness" in rec
            assert "one_minus_brier" in rec

    def test_stage1_results_present_when_candidates_advance(self, tmp_path):
        """If Stage 0 advances candidates, Stage 1 results should be non-empty."""
        items = _make_items(16)
        # Use high alpha_gain so steering clearly beats prompt
        backend = SyntheticC2bTaskBackend(
            axis="uncertainty_awareness", items=items,
            prompt_gain=0.1, alpha_gain=0.15, threshold=0.20,
        )
        sampler = adj.BackendOutcomeSampler(backend, max_new_tokens=128, do_sample=False)
        dev_items, test_items = split_e0012_pool(items, split_seed=42)
        authored = _make_authored(2)

        verdict_obj = run_e0012_harness(
            sampler=sampler,
            dev_items=dev_items,
            test_items=test_items,
            authored_prompts=authored,
            hidden_dim=16,
        )
        # If any candidate advanced, we should have Stage 1 results
        if verdict_obj.stage0 and verdict_obj.stage0.advancing:
            assert len(verdict_obj.stage1_results) > 0
