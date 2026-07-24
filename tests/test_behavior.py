"""Behavioral proxy tests — each crude proxy must separate clear +/- snippets."""

import pytest

from cognitive_console.experiments.behavior import (
    AXES,
    behavior_score,
    proxy_markers,
)

# Hand-written clear-positive vs clear-negative snippets per axis.
_CASES = {
    "deliberation": (
        # positive: visible step-by-step reasoning
        "First, let me think step by step. Second, I consider the options because "
        "each matters. Then, working through the reasoning, therefore I conclude X.",
        # negative: snap answer
        "42.",
    ),
    "skepticism": (
        # positive: pushback + demand for evidence
        "However, I doubt that premise. What is your evidence? That assumption is "
        "unsupported, so I question it and challenge the claim.",
        # negative: agreeable / sycophantic
        "Absolutely, of course, you're right! Definitely, I certainly agree with you.",
    ),
    "uncertainty_awareness": (
        # positive: hedging / calibrated
        "I might be wrong, and it is possibly uncertain. Perhaps it depends; I am "
        "not sure, so probably roughly this.",
        # negative: flat confidence
        "This is definitely certain and obviously guaranteed. Clearly it is always "
        "true, without doubt.",
    ),
    "focus": (
        # positive: short on-topic
        "The answer is 42.",
        # negative: rambling with tangents
        "The answer is 42. By the way, furthermore, on a related note, additionally, "
        "as an aside this connects to many broad related topics worth exploring at "
        "great length across many other only-loosely-related and expansive areas "
        "that go well beyond what was actually asked here in this question.",
    ),
}


@pytest.mark.parametrize("axis", AXES)
def test_proxy_separates_positive_from_negative(axis):
    pos_text, neg_text = _CASES[axis]
    pos = behavior_score(pos_text, axis)
    neg = behavior_score(neg_text, axis)
    assert pos > neg, f"{axis}: positive {pos} not > negative {neg}"
    # Meaningful, not marginal, separation.
    assert pos - neg > 0.1


@pytest.mark.parametrize("axis", AXES)
def test_proxy_in_unit_range(axis):
    for text in _CASES[axis]:
        s = behavior_score(text, axis)
        assert 0.0 <= s <= 1.0


def test_unknown_axis_raises():
    with pytest.raises(ValueError):
        behavior_score("hello", "not_an_axis")


def test_non_string_raises():
    with pytest.raises(TypeError):
        behavior_score(123, "focus")  # type: ignore[arg-type]


def test_proxy_markers_exposed():
    m = proxy_markers("skepticism")
    assert "pushback" in m and "agreement" in m
    assert len(m["pushback"]) > 0
