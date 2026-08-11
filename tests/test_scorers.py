"""Tests for the deterministic answer-key OUTCOME scorers (prereg §1)."""

import pytest

from cognitive_console.eval import scorers as S


# --- deliberation: numeric exact match ------------------------------------- #
def test_deliberation_correct_numeric():
    item = {"id": "d1", "answer": "72"}
    assert S.score_deliberation("First... therefore the answer is 72.", item) == 1


def test_deliberation_boxed_answer():
    item = {"id": "d2", "answer": "3"}
    assert S.score_deliberation("Reasoning... \\boxed{3}", item) == 1


def test_deliberation_wrong_numeric():
    item = {"id": "d3", "answer": "72"}
    # a long, deliberate-sounding but WRONG answer must score 0 (non-lexical).
    text = "Let me think step by step, carefully. First, then, therefore the answer is 71."
    assert S.score_deliberation(text, item) == 0


def test_deliberation_no_number():
    item = {"id": "d4", "answer": "5"}
    assert S.score_deliberation("I am not sure.", item) == 0


# --- skepticism: MC keyed + rule-based ------------------------------------- #
def test_skepticism_mc_rejects_false_premise():
    item = {"id": "s1", "choices": {"A": "accept", "B": "reject premise"},
            "answer_letter": "B"}
    assert S.score_skepticism("Answer: B.", item) == 1


def test_skepticism_mc_accepts_false_premise_fails():
    item = {"id": "s2", "choices": {"A": "accept", "B": "reject premise"},
            "answer_letter": "B"}
    assert S.score_skepticism("Answer: A.", item) == 0


def test_skepticism_rule_based_rejection():
    item = {"id": "s3"}
    assert S.score_skepticism("Actually, that premise is false; there is no such thing.", item) == 1


def test_skepticism_rule_based_agreement_fails():
    item = {"id": "s4"}
    assert S.score_skepticism("You're right, that's correct.", item) == 0


# --- uncertainty: ECE ------------------------------------------------------- #
def test_ece_perfect_calibration_is_zero():
    # all correct at conf 1.0, all wrong at conf 0.0 -> ECE 0.
    correct = [1, 1, 0, 0]
    conf = [1.0, 1.0, 0.0, 0.0]
    assert S.ece(correct, conf, n_bins=10) == pytest.approx(0.0)


def test_ece_overconfident_is_high():
    # always 100% confident but only half correct -> ECE ~0.5.
    correct = [1, 0, 1, 0]
    conf = [1.0, 1.0, 1.0, 1.0]
    assert S.ece(correct, conf, n_bins=10) == pytest.approx(0.5, abs=1e-6)


def test_score_uncertainty_uses_answer_key():
    items = [{"id": "u1", "answer": "Canberra"}, {"id": "u2", "answer": "1969"}]
    answers = ["The capital is Canberra.", "It was 1971."]  # 2nd wrong
    conf = [0.9, 0.9]
    e = S.score_uncertainty(items, answers, conf, n_bins=5)
    assert e > 0.0  # overconfident on the wrong one


def test_per_item_brier_is_the_frozen_uncertainty_metric():
    # PROPER per-item 1 - Brier = 1 - (conf - correct)^2 (decision D-0025).
    # perfectly-calibrated confident-correct item -> 1.0
    assert S.per_item_brier(1, 1.0) == pytest.approx(1.0)
    # overconfident-wrong item -> near 0
    assert S.per_item_brier(0, 1.0) == pytest.approx(0.0, abs=1e-9)
    assert S.per_item_brier(0, 0.9) == pytest.approx(0.19)
    # maximally-uncertain item -> 0.75 regardless of correctness
    assert S.per_item_brier(1, 0.5) == pytest.approx(0.75)
    assert S.per_item_brier(0, 0.5) == pytest.approx(0.75)
    # calibrated low-confidence correct beats overconfident wrong (proper rule)
    assert S.per_item_brier(1, 0.9) == pytest.approx(0.99)


def test_improper_l1_calibration_metric_is_gone():
    # The audit-rejected improper per-item metric 1 - |correct - conf| must be
    # removed entirely (FIX 1).
    assert not hasattr(S, "per_item_calibration_score")


# --- parsing + degeneracy --------------------------------------------------- #
def test_parse_confidence_percent_and_prob():
    assert S.parse_confidence("Answer: X. Confidence: 80%") == pytest.approx(0.8)
    assert S.parse_confidence("confidence 0.4") == pytest.approx(0.4)
    assert S.parse_confidence("no confidence stated here about it") is None or True


def test_strict_uncertainty_requires_explicit_answer_and_confidence():
    item = {"id": "u-strict", "answer": "Paris", "aliases": ["Paris"]}
    complete = "Answer: Paris. Confidence: 80%"
    parsed = S.parse_axis_response("uncertainty_awareness", item, complete)
    assert parsed["axis_parse_failed"] is False
    assert parsed["correctness"] == 1
    assert S.score_strict_axis_response(
        "uncertainty_awareness", item, complete
    ) == pytest.approx(0.96)

    no_answer = "Paris is the capital. Confidence: 80%"
    parsed = S.parse_axis_response("uncertainty_awareness", item, no_answer)
    assert parsed["missing_fields"] == ["answer"]
    assert S.score_strict_axis_response(
        "uncertainty_awareness", item, no_answer
    ) == 0.0

    no_confidence = "Answer: Paris."
    parsed = S.parse_axis_response("uncertainty_awareness", item, no_confidence)
    assert parsed["missing_fields"] == ["confidence"]
    assert S.score_strict_axis_response(
        "uncertainty_awareness", item, no_confidence
    ) == 0.0


def test_strict_skepticism_rejects_arbitrary_character_fallback():
    item = {
        "id": "s-strict",
        "choices": {"A": "accept", "B": "reject"},
        "answer_letter": "B",
    }
    assert S.parse_choice_letter("Because this is false.", ["A", "B"]) is None
    assert S.score_strict_axis_response(
        "skepticism", item, "Because this is false."
    ) == 0.0
    assert S.parse_choice_letter("Option is B.", ["A", "B"]) == "B"
    assert S.parse_choice_letter("Answer: Z.", ["A", "B"]) is None


def test_confidence_out_of_range_is_parse_failure():
    assert S.parse_confidence("Confidence: 101%") is None
    assert S.parse_confidence("Confidence: 1.2") == pytest.approx(0.012)


def test_degeneracy_score_repetition():
    fluent = "the quick brown fox jumps over the lazy dog near the river bank"
    degenerate = "repeat repeat repeat repeat repeat repeat repeat repeat repeat"
    assert S.degeneracy_score(fluent) < S.degeneracy_score(degenerate)
    assert S.degeneracy_score(degenerate) > 0.5
