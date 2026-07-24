import numpy as np
import pytest

from cognitive_console.experiments.adjudicate_c2b import AxisAdjSpec, OutcomeSampler, SampleBatch
from cognitive_console.experiments.prompt_optimizer import (
    OptimizerConfig,
    optimize_prompt_on_dev,
)


class _PromptLengthSampler(OutcomeSampler):
    def sample(self, axis, item, instruction, alpha, k, direction, layer):
        score = min(1.0, len(str(instruction)) / 200.0)
        return SampleBatch(outcomes=[float(score)] * int(k), degeneracies=[0.0] * int(k))


def _spec(n=9):
    items = [{"id": f"it-{i:02d}", "prompt": f"q{i}", "answer": str(i)} for i in range(n)]
    strong = [
        ("p1", "Answer directly."),
        ("p2", "Reason step by step and verify your final answer."),
        ("p3", "Be precise."),
        ("p4", "State confidence."),
    ]
    return AxisAdjSpec(
        axis="deliberation",
        items=items,
        strong_prompts=strong,
        neutral_prompt="Answer.",
        direction=np.ones(8),
        layer=3,
    )


def test_optimizer_rejects_invalid_budget_config():
    with pytest.raises(ValueError):
        OptimizerConfig(total_budget=2, seed_prompt_count=3)


def test_optimizer_dev_test_leakage_guard_fails_when_test_id_in_dev():
    spec = _spec()
    dev_items = spec.items[:3] + [spec.items[-1]]
    test_ids = [it["id"] for it in spec.items[-2:]]
    cfg = OptimizerConfig(total_budget=8, seed_prompt_count=3, max_rounds=2, candidates_per_round=2)
    with pytest.raises(ValueError, match="DEV/TEST leakage"):
        optimize_prompt_on_dev(
            _PromptLengthSampler(),
            spec,
            dev_items,
            test_ids,
            k=5,
            config=cfg,
            compute_parity_target_n_strong=16,
        )


def test_optimizer_respects_budget_and_records_provenance():
    spec = _spec()
    dev_items = spec.items[:3]
    test_ids = [it["id"] for it in spec.items[3:]]
    cfg = OptimizerConfig(
        total_budget=8,
        seed_prompt_count=3,
        max_rounds=3,
        candidates_per_round=2,
        keep_top_k=2,
        seed=123,
    )
    out = optimize_prompt_on_dev(
        _PromptLengthSampler(),
        spec,
        dev_items,
        test_ids,
        k=5,
        config=cfg,
        compute_parity_target_n_strong=16,
    )
    assert out.evaluations_used <= 8
    assert out.total_budget == 8
    assert out.leakage_guard_ok is True
    assert set(out.dev_item_ids).isdisjoint(set(out.test_item_ids))
    assert out.compute_parity_target_n_strong == 16
    assert out.winner_prompt_id
    assert out.winner_prompt_text
