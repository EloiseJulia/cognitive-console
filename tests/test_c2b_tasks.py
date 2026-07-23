"""Tests for the offline C2b task loader (fixtures + deferred real loaders)."""

import pytest

from cognitive_console.eval import c2b_tasks


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


def test_real_loader_is_deferred_offline():
    # datasets may be absent OR present-but-offline; both must not silently fetch.
    with pytest.raises((NotImplementedError, Exception)):
        c2b_tasks.load_c2b_task("skepticism", use_fixture=False)
