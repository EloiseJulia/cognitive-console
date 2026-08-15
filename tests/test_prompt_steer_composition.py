import json

import numpy as np
import pytest

from cognitive_console.experiments import adjudicate_c2b as c2
from cognitive_console.experiments import prompt_steer_composition as C
from cognitive_console.experiments.adjudicate_c2b import AxisAdjSpec, OutcomeSampler, SampleBatch


class FactorialSampler(OutcomeSampler):
    def __init__(self):
        self.calls = []

    def sample(self, axis, item, instruction, alpha, k, direction, layer):
        self.calls.append((axis, str(item["id"]), instruction, float(alpha)))
        is_prompt = "strong" in instruction.lower()
        if alpha == 0:
            value = 0.50 if is_prompt else 0.20
        else:
            value = 0.70 if is_prompt else 0.30
        return SampleBatch(outcomes=[value] * k, degeneracies=[0.05] * k)


class NonFiniteDegeneracySampler(FactorialSampler):
    def sample(self, axis, item, instruction, alpha, k, direction, layer):
        batch = super().sample(axis, item, instruction, alpha, k, direction, layer)
        batch.degeneracies[0] = float("nan")
        return batch


def _items(n):
    return [
        {"id": f"item-{i:04d}", "prompt": f"Question {i}", "answer": str(i)}
        for i in range(n)
    ]


def _spec(items):
    return AxisAdjSpec(
        axis="deliberation",
        items=list(items),
        strong_prompts=[("weak", "weak instruction"), ("best", "strong instruction")],
        neutral_prompt="neutral instruction",
        direction=np.ones(8),
        layer=3,
    )


def test_confirmatory_pool_never_reuses_original_test():
    items = _items(1000)
    plan = C.build_confirmatory_pool(
        "deliberation", items, dev_n=96, test_max_n=384
    )
    dev_ids = {row["id"] for row in plan.dev_items}
    test_ids = {row["id"] for row in plan.test_reservoir}
    original_pool_ids = {row["id"] for row in items[:60]}

    assert len(plan.dev_items) == 96
    assert len(plan.test_reservoir) == 384
    assert not (dev_ids & set(plan.original_test_ids))
    assert not (test_ids & original_pool_ids)
    assert not (dev_ids & test_ids)


def test_power_plan_uses_prior_floor_and_cap():
    low_variance = np.zeros(96)
    planned = C.plan_test_n("deliberation", low_variance)
    assert planned["eligible"] is True
    assert planned["planning_sd"] == pytest.approx(C.PRIOR_SD_FLOOR["deliberation"])
    assert planned["n_test"] == C.TEST_MIN_N["deliberation"]

    high_variance = np.tile([-1.0, 1.0], 48)
    capped = C.plan_test_n("deliberation", high_variance)
    assert capped["eligible"] is False
    assert capped["n_test"] is None


def test_dev_selection_maximizes_incremental_prompt_value_without_test_calls():
    items = _items(12)
    pool = C.build_smoke_pool("deliberation", items, dev_n=4, test_n=6)
    spec = _spec(items)
    sampler = FactorialSampler()

    selection = C.select_composition_on_dev(
        sampler, spec, pool, smoke=True
    )

    assert selection.eligible is True
    assert selection.best_prompt_id == "best"
    assert selection.frozen_alpha == 2.0  # all alphas tie; prereg chooses lower alpha
    assert selection.planned_test_n == 6
    touched = {item_id for _, item_id, _, _ in sampler.calls}
    assert touched <= {row["id"] for row in pool.dev_items}
    assert not (touched & set(selection.selected_test_ids))


def test_factorial_estimands_and_primary_pass():
    items = _items(12)
    pool = C.build_smoke_pool("deliberation", items, dev_n=4, test_n=6)
    spec = _spec(items)
    sampler = FactorialSampler()
    selection = C.select_composition_on_dev(sampler, spec, pool, smoke=True)
    by_id = {row["id"]: row for row in items}
    test_items = [by_id[item_id] for item_id in selection.selected_test_ids]

    result = C.run_test_axis(
        sampler,
        spec,
        selection,
        test_items,
        bootstrap_b=200,
    )

    assert result.condition_means == pytest.approx(
        {"neutral": 0.2, "prompt": 0.5, "steer": 0.3, "prompt_steer": 0.7}
    )
    assert result.estimands["primary_steer_at_prompt"]["point"] == pytest.approx(0.2)
    assert result.estimands["steer_at_neutral"]["point"] == pytest.approx(0.1)
    assert result.estimands["interaction"]["point"] == pytest.approx(0.1)
    assert result.primary_pass is True
    assert result.verdict == "ADDED_VALUE"


def test_test_item_identity_is_sealed():
    items = _items(12)
    pool = C.build_smoke_pool("deliberation", items, dev_n=4, test_n=6)
    spec = _spec(items)
    selection = C.select_composition_on_dev(
        FactorialSampler(), spec, pool, smoke=True
    )
    wrong_items = list(reversed(pool.test_reservoir))
    with pytest.raises(ValueError, match="TEST item IDs differ"):
        C.run_test_axis(
            FactorialSampler(),
            spec,
            selection,
            wrong_items,
            bootstrap_b=100,
        )


def test_protocol_keeps_original_frozen_settings():
    protocol = C.frozen_protocol_dict()
    assert protocol["status"] == "FROZEN"
    assert protocol["protocol_id"] == "E-0017-prompt-steer-composition-v2"
    assert protocol["supersedes"] == "E-0017-prompt-steer-composition-v1"
    assert protocol["conditions"] == ["neutral", "prompt", "steer", "prompt_steer"]
    assert protocol["primary_estimand"] == "prompt_steer - prompt"
    assert "Bo et al." in protocol["prior_work_boundary"]
    assert "does not claim composition novelty" in protocol["prior_work_boundary"]
    assert "0/12" in protocol["preserved_substitution_result"]
    assert "does not establish" in protocol["interaction_scope"]
    assert protocol["alpha_grid"] == list(c2.ALPHA_GRID)
    assert protocol["k_samples"] == c2.K_SAMPLES
    assert protocol["delta"] == c2.DELTA
    assert protocol["max_new_tokens"] == 512
    assert protocol["generation_retry_budget_per_backend_call"] == 1
    assert protocol["disk_budget_gb"] == 60.0
    assert protocol["disk_ceiling_gb"] == 70.0
    assert protocol["stall_timeout_seconds"] == 600.0
    assert protocol["bootstrap_rule"] == "real HF DEV/TEST requires exactly B=10000"
    assert "verified DEV-seal" in protocol["selection_rule"]
    assert "full backend artifact tree" in protocol["disk_guard_scope"]
    assert C.PRIMARY_CI_LEVEL == pytest.approx(1.0 - 0.05 / 3.0)


def test_worst_case_compute_plan_counts_partial_padded_batches():
    plan = C.worst_case_compute_plan()
    assert plan["dev_logical_generations"] == 44_640
    assert plan["test_logical_generations"] == 41_760
    assert plan["total_logical_generations"] == 86_400
    assert plan["dev_padded_batches"] == 2_976
    assert plan["test_padded_batches"] == 2_788
    assert plan["total_padded_batches"] == 5_764
    assert plan["max_physical_generations"] == 172_800


def test_interaction_is_explicitly_secondary_and_scoped():
    items = _items(12)
    pool = C.build_smoke_pool("deliberation", items, dev_n=4, test_n=6)
    spec = _spec(items)
    selection = C.select_composition_on_dev(
        FactorialSampler(), spec, pool, smoke=True
    )
    by_id = {row["id"]: row for row in items}
    result = C.run_test_axis(
        FactorialSampler(),
        spec,
        selection,
        [by_id[item_id] for item_id in selection.selected_test_ids],
        bootstrap_b=100,
    )
    assert result.interaction_class == "SYNERGISTIC"
    assert "does not establish prompt-plus-steer utility" in result.interaction_scope


def test_nonfinite_degeneracy_is_invalid_not_silently_coherence_failed():
    items = _items(12)
    pool = C.build_smoke_pool("deliberation", items, dev_n=4, test_n=6)
    with pytest.raises(ValueError, match="non-finite outcome or degeneracy"):
        C.select_composition_on_dev(
            NonFiniteDegeneracySampler(),
            _spec(items),
            pool,
            smoke=True,
        )


def test_diagnostics_require_exact_identity_coverage():
    ok, reason = C.diagnostics_eligible(
        "deliberation",
        {
            "coverage": 1.0,
            "parse_rate": 1.0,
            "truncation_rate": 0.0,
            "identity_ok": False,
        },
    )
    assert ok is False
    assert "identity mismatch" in reason
