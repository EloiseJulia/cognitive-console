
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from cognitive_console.experiments.breadth_l0 import (
    ClassifiedSample,
    ItemConditionResult,
    MockBreadthBackend,
    RuleBasedDomainClassifier,
    build_mock_activation_provider,
    coverage_guard,
    domain_coverage_at_k,
    extract_breadth_axis,
    load_contrast_pairs,
    load_readability_prompts,
    load_tasks,
    oracle_suppression,
    run_mock_l0,
    sample_conditions,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "persona_breadth_l0"


def test_domain_coverage_at_k_counts_distinct_valid_domains_only():
    samples = [
        ClassifiedSample(0, "a", ["graph", "spreadsheet"], True, True, True),
        ClassifiedSample(1, "b", ["graph"], True, False, True),
        ClassifiedSample(2, "", ["ignored"], False, False, False, "empty"),
    ]
    assert domain_coverage_at_k(samples) == 2


def test_oracle_suppression_strict_and_calibrated_rates():
    def s(i, domains, oracle, narrow):
        return ClassifiedSample(i, "x", domains, oracle, narrow, True)
    rows = [
        ItemConditionResult("a", "no_persona", "p", [s(0, ["oracle"], True, False)]),
        ItemConditionResult("a", "narrow_persona", "p", [s(0, ["narrow"], False, True)]),
        ItemConditionResult("a", "oracle_persona", "p", [s(0, ["oracle"], True, False)]),
        ItemConditionResult("b", "no_persona", "p", [s(0, ["narrow"], False, True)]),
        ItemConditionResult("b", "narrow_persona", "p", [s(0, ["narrow"], False, True)]),
        ItemConditionResult("b", "oracle_persona", "p", [s(0, ["oracle"], True, False)]),
    ]
    res = oracle_suppression(rows, bootstrap_b=50, seed=1)
    assert res.strict_item_ids == ["a"]
    assert res.calibrated_item_ids == ["a", "b"]
    assert res.strict_suppression_rate == pytest.approx(0.5)
    assert res.calibrated_suppression_rate == pytest.approx(1.0)
    assert set(res.coverage_bootstrap) >= {"point", "ci_lo", "ci_hi"}


def test_breadth_axis_extraction_reports_readable_mock_axis():
    broad, focus = load_contrast_pairs(DATA / "breadth_focus_contrast_pairs.jsonl")
    readability = load_readability_prompts(DATA / "readability_prompts.json")
    provider = build_mock_activation_provider(broad, focus, readability)
    axis = extract_breadth_axis(provider, broad, focus, readability, seed=7, n_null=100)
    assert axis.stable_layer_found
    assert axis.selected_layer == 6
    assert axis.linearly_readable
    assert axis.facade_ratio is not None and 0 < axis.facade_ratio <= 1.25
    assert axis.expected_order


def test_breadth_axis_can_report_not_linear_without_forcing_layer():
    broad, focus = load_contrast_pairs(DATA / "breadth_focus_contrast_pairs.jsonl")
    readability = load_readability_prompts(DATA / "readability_prompts.json")
    from cognitive_console.activations import SyntheticActivationProvider
    provider = SyntheticActivationProvider(dim=32, layers=[0, 1], seed=3, noise_scale=0.0)
    axis = extract_breadth_axis(provider, broad[:4], focus[:4], readability, seed=0, n_null=50)
    assert not axis.stable_layer_found
    assert not axis.linearly_readable
    assert axis.verdict == "NOT_LINEAR_OR_DEGENERATE"


def test_coverage_guard_fails_closed_on_missing_classification():
    tasks = load_tasks(DATA / "tasks.json")[:1]
    backend = MockBreadthBackend(tasks)
    classifier = RuleBasedDomainClassifier()
    rows = sample_conditions(backend, classifier, tasks, k=2)
    # Remove the explicit domain tags from one otherwise valid sample.
    bad_sample = replace(rows[0].samples[0], domains=[])
    bad_row = replace(rows[0], samples=[bad_sample] + rows[0].samples[1:])
    guard = coverage_guard([bad_row] + rows[1:], tasks, k=2)
    assert not guard["ok"]
    assert guard["n_unclassified_valid_samples"] == 1


def test_mock_smoke_whole_path_writes_complete_result_shape():
    res = run_mock_l0(
        DATA / "tasks.json",
        DATA / "breadth_focus_contrast_pairs.jsonl",
        DATA / "readability_prompts.json",
        k=5,
        seed=20260727,
    )
    assert res.coverage_guard_passed
    assert res.k == 5
    assert len(res.items) == 12 * 3
    assert res.metrics["no_persona"]["mean_domain_coverage_at_k"] >= 2
    assert res.suppression.calibrated_suppression_rate == pytest.approx(1.0)
    assert res.breadth_axis.linearly_readable
    json.dumps(res.to_dict())
