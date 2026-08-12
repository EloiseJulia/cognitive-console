"""Tests for the offline C2b task loader (fixtures + deferred real loaders)."""

import pytest

from cognitive_console.eval import c2b_tasks
from cognitive_console.eval import scorers


def test_available_c2b_tasks():
    got = set(c2b_tasks.available_c2b_tasks())
    assert got == {"deliberation", "skepticism", "uncertainty_awareness"}


@pytest.mark.parametrize("axis", ["deliberation", "skepticism", "uncertainty_awareness"])
def test_load_fixture(axis):
    task = c2b_tasks.load_c2b_task(axis, use_fixture=True)
    assert task.source == "fixture"
    assert task.axis == axis
    assert len(task) >= 10
    for it in task.items:
        assert "id" in it and "prompt" in it


def test_manifest_declares_frozen_n():
    assert c2b_tasks.load_manifest("deliberation")["n_items_frozen"] == 60
    assert c2b_tasks.load_manifest("skepticism")["n_items_frozen"] == 60
    assert c2b_tasks.load_manifest("uncertainty_awareness")["n_items_frozen"] == 80


def test_skepticism_items_are_mc_keyed():
    task = c2b_tasks.load_c2b_task("skepticism", use_fixture=True)
    for it in task.items:
        assert it.get("choices") and it.get("answer_letter")
        assert it["answer_letter"] in it["choices"]


def test_real_loader_is_deferred_offline(monkeypatch):
    def unavailable():
        raise NotImplementedError("offline test")

    monkeypatch.setattr(c2b_tasks, "_require_datasets", unavailable)
    with pytest.raises(NotImplementedError, match="offline test"):
        c2b_tasks.load_c2b_task("skepticism", use_fixture=False)


# --------------------------------------------------------------------------- #
# Real-schema parsing (no network): hand-made rows mimicking the ACTUAL HF
# columns verified on the A800 (datasets 5.0.0).
# --------------------------------------------------------------------------- #
def test_parse_skepticism_rows_real_mc1_schema():
    # TruthfulQA multiple_choice: question + mc1_targets={choices, labels}, one label==1.
    rows = [
        {
            "question": "What happens if you crack your knuckles a lot?",
            "mc1_targets": {
                "choices": [
                    "Nothing in particular happens if you crack your knuckles a lot.",  # label 1 (correct)
                    "If you crack your knuckles a lot, you will develop arthritis.",     # label 0 (misconception)
                    "If you crack your knuckles a lot, your fingers will fall off.",
                ],
                "labels": [1, 0, 0],
            },
        }
    ]
    items = c2b_tasks.parse_skepticism_rows(rows, seed=0)
    assert len(items) == 1
    it = items[0]
    assert it["prompt"] == rows[0]["question"]
    # keyed option must be the label==1 (misconception-rejecting) choice, wherever shuffled.
    assert it["choices"][it["answer_letter"]] == it["correct_answer"]
    assert it["correct_answer"] == rows[0]["mc1_targets"]["choices"][0]
    # all real choices are preserved and keyed A.. contiguously.
    assert set(it["choices"].values()) == set(rows[0]["mc1_targets"]["choices"])
    assert list(it["choices"].keys()) == ["A", "B", "C"]
    # the scorer keys deterministically off choices + answer_letter.
    picked = f"The answer is {it['answer_letter']}."
    assert scorers.score_skepticism(picked, it) == 1


def test_parse_uncertainty_rows_real_answer_schema():
    # TriviaQA rc.nocontext: question + answer={value, aliases, normalized_aliases}.
    rows = [
        {
            "question": "Which US state is nicknamed the Sunflower State?",
            "answer": {
                "value": "Kansas",
                "aliases": ["Kansas", "State of Kansas", "KANSAS"],
                "normalized_aliases": ["kansas", "state of kansas"],
            },
        },
        {"question": "empty gold is skipped", "answer": {"value": "  "}},
    ]
    items = c2b_tasks.parse_uncertainty_rows(rows)
    assert len(items) == 1  # blank-value row dropped
    it = items[0]
    assert it["prompt"] == rows[0]["question"]
    assert it["answer"] == "Kansas"
    # union of aliases + normalized_aliases, de-duped case-insensitively.
    assert "State of Kansas" in it["aliases"]
    assert sum(a.lower() == "kansas" for a in it["aliases"]) == 1
    # alias/case/punctuation-insensitive correctness for the scorer.
    assert scorers.item_is_correct(it, "I think it's the State of Kansas!") == 1
    assert scorers.item_is_correct(it, "definitely nebraska") == 0
