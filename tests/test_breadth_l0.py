
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from cognitive_console.experiments.breadth_l0 import (
    DEFAULT_MAX_OTHER_FRACTION,
    OTHER_DOMAIN,
    ClassifiedSample,
    ItemConditionResult,
    LLMJudgeDomainClassifier,
    MockBreadthBackend,
    RuleBasedDomainClassifier,
    build_mock_activation_provider,
    classifier_agreement,
    coverage_guard,
    domain_coverage_at_k,
    extract_breadth_axis,
    load_contrast_pairs,
    load_readability_prompts,
    load_tasks,
    oracle_suppression,
    run_mock_l0,
    sample_conditions,
    _marker_hit,
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
    assert axis.broad_reach > axis.lexical_control_reach


def test_rule_classifier_ignores_stray_digits_and_ev_substrings():
    task = next(t for t in load_tasks(DATA / "tasks.json") if t.item_id == "contract_expected_value")
    classifier = RuleBasedDomainClassifier()
    text = (
        "However, after review of section 6, I would revise clause 9.5 for tone. "
        "This is legal drafting commentary, not a quantitative method."
    )
    sample = classifier.classify(text, task, sample_index=3)
    assert sample.sample_index == 3
    assert not sample.uses_oracle_domain
    assert task.oracle_domain not in sample.domains
    assert sample.uses_narrow_domain


def test_oracle_markers_are_method_markers_not_bare_answers():
    tasks = load_tasks(DATA / "tasks.json")
    for task in tasks:
        for marker in task.oracle_domain_markers:
            assert not marker.replace(".", "", 1).isdigit()
            assert marker.lower() not in {"ev", "dp"}




def test_design_knapsack_greedy_text_classifies_consistently_without_oracle_credit():
    task = next(t for t in load_tasks(DATA / "tasks.json") if t.item_id == "design_knapsack")
    classifier = RuleBasedDomainClassifier()
    greedy = (
        "Using a design-thinking value/cost heuristic, I would greedily pick B and D "
        "as a plausible prototype bundle under budget, then revisit with users."
    )
    no_persona = classifier.classify(greedy, task, sample_index=0)
    narrow_persona = classifier.classify(greedy, task, sample_index=0)
    assert no_persona == narrow_persona
    assert not no_persona.uses_oracle_domain
    assert no_persona.uses_narrow_domain
    assert task.oracle_domain not in no_persona.domains
    assert task.narrow_domain in no_persona.domains


def test_tricky_markers_are_disjoint_under_word_boundary_matching():
    tasks = {t.item_id: t for t in load_tasks(DATA / "tasks.json")}
    classifier = RuleBasedDomainClassifier()

    topo = tasks["excel_topological_order"]
    topo_sample = classifier.classify("Use a topological sort on the dependency graph.", topo)
    assert topo_sample.uses_oracle_domain
    assert not topo_sample.uses_narrow_domain

    queue = tasks["pm_queue_bottleneck"]
    narrow_queue = classifier.classify("Coordinate staffing around the bottleneck and milestones.", queue)
    assert narrow_queue.uses_narrow_domain
    assert not narrow_queue.uses_oracle_domain
    oracle_queue = classifier.classify("Compute service rate: 20 tickets/hour vs 12 tickets/hour, so specialist is the bottleneck station.", queue)
    assert oracle_queue.uses_oracle_domain

    knapsack = tasks["design_knapsack"]
    generic_opt = classifier.classify("Optimize the prototype choices with a greedy value/cost heuristic.", knapsack)
    assert not generic_opt.uses_oracle_domain
    dp = classifier.classify("Solve as 0/1 knapsack with dynamic programming; pick A and D.", knapsack)
    assert dp.uses_oracle_domain


def test_oracle_and_narrow_markers_are_pairwise_disjoint_under_matcher():
    for task in load_tasks(DATA / "tasks.json"):
        for oracle_marker in task.oracle_domain_markers:
            assert not _marker_hit(oracle_marker, task.persona_domain_markers), (task.item_id, oracle_marker)
        for narrow_marker in task.persona_domain_markers:
            assert not _marker_hit(narrow_marker, task.oracle_domain_markers), (task.item_id, narrow_marker)


def test_classifier_agreement_reports_kappa_and_disagreements():
    task = load_tasks(DATA / "tasks.json")[0]
    rows = [
        ItemConditionResult(task.item_id, "no_persona", "p", [
            ClassifiedSample(0, "shortest path by Dijkstra", [task.oracle_domain], True, False, True),
            ClassifiedSample(1, "spreadsheet formula", [task.narrow_domain], False, True, True),
            ClassifiedSample(2, "graph edge relaxation", [task.oracle_domain], True, False, True),
            ClassifiedSample(3, "excel table", [task.narrow_domain], False, True, True),
        ])
    ]

    class Secondary:
        def classify(self, text, task, sample_index=0):
            oracle = sample_index in {0, 1}
            domains = [task.oracle_domain] if oracle else [task.narrow_domain]
            return ClassifiedSample(sample_index, text, domains, oracle, not oracle, True)

    agreement = classifier_agreement(rows, [task], Secondary(), secondary_classifier_name="mock_blinded_judge")
    assert agreement.n_samples == 4
    assert agreement.oracle_reach_agreement == pytest.approx(0.5)
    assert agreement.oracle_reach_cohen_kappa == pytest.approx(0.0)
    assert agreement.confusion["oracle_primary_only"] == 1
    assert agreement.confusion["oracle_secondary_only"] == 1
    assert agreement.disagreements

def test_breadth_axis_can_report_not_linear_without_forcing_layer():
    broad, focus = load_contrast_pairs(DATA / "breadth_focus_contrast_pairs.jsonl")
    readability = load_readability_prompts(DATA / "readability_prompts.json")
    from cognitive_console.activations import SyntheticActivationProvider
    provider = SyntheticActivationProvider(dim=32, layers=[0, 1], seed=3, noise_scale=0.0)
    axis = extract_breadth_axis(provider, broad[:4], focus[:4], readability, seed=0, n_null=50)
    assert not axis.stable_layer_found
    assert not axis.linearly_readable
    assert axis.verdict == "NOT_LINEAR_OR_DEGENERATE"


def test_lexical_control_axis_is_rejected_as_nonspecific():
    broad, focus = load_contrast_pairs(DATA / "breadth_focus_contrast_pairs.jsonl")
    readability = load_readability_prompts(DATA / "readability_prompts.json")
    provider = build_mock_activation_provider(broad, focus, readability)
    for text in readability["lexical_controls"]:
        provider.plant_facade("breadth_focus", text, f"CONTROL_DOMINATES::{text}", 4.0, 2.0, 6)
    axis = extract_breadth_axis(provider, broad, focus, readability, seed=9, n_null=100)
    assert axis.stable_layer_found
    assert axis.expected_order
    assert not axis.linearly_readable
    assert axis.lexical_control_reach >= axis.broad_reach
    assert axis.verdict == "READABLE_BUT_NONSPECIFIC_LEXICAL_CONTROL"


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
    assert guard["n_unclassified_valid_samples"] == len(guard["unclassified_valid_samples"])


def test_coverage_guard_unclassified_count_equals_enumerated_list_length():
    tasks = load_tasks(DATA / "tasks.json")[:1]
    backend = MockBreadthBackend(tasks)
    classifier = RuleBasedDomainClassifier()
    rows = sample_conditions(backend, classifier, tasks, k=2)
    bad_samples = [replace(s, domains=[]) for s in rows[0].samples]
    bad_row = replace(rows[0], samples=bad_samples)
    guard = coverage_guard([bad_row] + rows[1:], tasks, k=2)
    assert not guard["ok"]
    assert guard["n_unclassified_valid_samples"] == 2
    assert guard["n_unclassified_valid_samples"] == len(guard["unclassified_valid_samples"])


def test_rule_classifier_falls_back_to_reported_other_without_oracle_credit():
    task = next(t for t in load_tasks(DATA / "tasks.json") if t.item_id == "excel_shortest_path")
    sample = RuleBasedDomainClassifier().classify(
        "I am not sure which formal method applies here, but I would inspect the options carefully.",
        task,
        sample_index=2,
    )
    assert sample.valid
    assert sample.domains == [OTHER_DOMAIN]
    assert not sample.uses_oracle_domain
    assert not sample.uses_narrow_domain


def test_coverage_guard_allows_only_low_other_fraction():
    assert DEFAULT_MAX_OTHER_FRACTION == pytest.approx(0.05)
    task = load_tasks(DATA / "tasks.json")[0]

    def sample(i, domain):
        return ClassifiedSample(i, "valid sample text", [domain], domain == task.oracle_domain, domain == task.narrow_domain, True)

    low_other_rows = []
    high_other_rows = []
    for condition in ("no_persona", "narrow_persona", "oracle_persona"):
        low_domains = [OTHER_DOMAIN, task.oracle_domain, task.narrow_domain, task.oracle_domain, task.narrow_domain]
        high_domains = [OTHER_DOMAIN, OTHER_DOMAIN, OTHER_DOMAIN, task.oracle_domain, task.narrow_domain]
        low_other_rows.append(ItemConditionResult(task.item_id, condition, "p", [sample(i, d) for i, d in enumerate(low_domains)]))
        high_other_rows.append(ItemConditionResult(task.item_id, condition, "p", [sample(i, d) for i, d in enumerate(high_domains)]))

    low_guard = coverage_guard(low_other_rows, [task], k=5, max_other_fraction=0.25)
    assert low_guard["ok"]
    assert low_guard["n_other_valid_samples"] == 3
    assert low_guard["max_other_fraction"] == pytest.approx(0.25)

    high_guard = coverage_guard(high_other_rows, [task], k=5, max_other_fraction=0.25)
    assert not high_guard["ok"]
    assert high_guard["too_many_other"]
    assert high_guard["n_unclassified_valid_samples"] == 0


def test_d0046_unclassified_phrasings_now_classify_to_method_or_other():
    tasks = {t.item_id: t for t in load_tasks(DATA / "tasks.json")}
    failed = json.loads((ROOT / "results" / "breadth_confirm" / "breadth_l0_hf_FAILED_COVERAGE.json").read_text(encoding="utf-8"))
    transcripts = json.loads((ROOT / "results" / "breadth_l0_qwen" / "breadth_l0_hf_k5_seed20260727.json").read_text(encoding="utf-8"))
    listed_unclassified = {tuple(x) for x in failed["coverage_guard"]["unclassified_valid_samples"]}
    classifier = RuleBasedDomainClassifier()
    checked = {}
    reclassified_rows = []
    for row in transcripts["items"]:
        task = tasks[row["item_id"]]
        reclassified_samples = []
        for sample in row["samples"]:
            classified = classifier.classify(sample["text"], task, sample_index=sample["sample_index"])
            reclassified_samples.append(classified)
            key = (row["item_id"], row["condition"], sample["sample_index"])
            if key not in listed_unclassified:
                continue
            assert classified.valid
            assert classified.domains
            checked[key] = classified
        reclassified_rows.append(ItemConditionResult(row["item_id"], row["condition"], row["prompt"], reclassified_samples))

    assert len(checked) == len(listed_unclassified)
    guard = coverage_guard(reclassified_rows, list(tasks.values()), k=5)
    assert guard["ok"]
    assert guard["n_unclassified_valid_samples"] == 0
    assert guard["n_other_valid_samples"] == 3
    assert checked[("design_knapsack", "no_persona", 0)].uses_narrow_domain
    assert not checked[("design_knapsack", "no_persona", 0)].uses_oracle_domain
    assert checked[("design_knapsack", "narrow_persona", 4)].uses_narrow_domain
    assert not checked[("design_knapsack", "narrow_persona", 4)].uses_oracle_domain
    assert checked[("pm_critical_path", "no_persona", 0)].uses_oracle_domain
    assert checked[("pm_queue_bottleneck", "no_persona", 0)].uses_oracle_domain
    assert checked[("design_assignment_problem", "narrow_persona", 0)].uses_oracle_domain


def test_sample_conditions_uses_swappable_classifier_protocol():
    tasks = load_tasks(DATA / "tasks.json")[:1]

    class AlwaysOracleClassifier:
        def __init__(self):
            self.calls = []

        def classify(self, text, task, sample_index=0):
            self.calls.append((text, task.item_id, sample_index))
            return ClassifiedSample(
                sample_index, text, [task.oracle_domain], True, False, True
            )

    classifier = AlwaysOracleClassifier()
    rows = sample_conditions(MockBreadthBackend(tasks), classifier, tasks, k=2)
    assert len(classifier.calls) == 3 * 2
    assert all(s.uses_oracle_domain for row in rows for s in row.samples)


def test_llm_judge_classifier_injected_fn_seam():
    task = load_tasks(DATA / "tasks.json")[0]

    def judge_fn(text, task, sample_index):
        return {"domains": [task.oracle_domain], "valid": True, "invalid_reason": ""}

    sample = LLMJudgeDomainClassifier(judge_fn=judge_fn).classify("anything", task, sample_index=4)
    assert sample.sample_index == 4
    assert sample.uses_oracle_domain
    assert not sample.uses_narrow_domain


def test_runner_accepts_classifier_switch(tmp_path):
    from scripts.run_breadth_l0 import main

    rc = main([
        "--mock",
        "--classifier", "rule",
        "--k", "1",
        "--output-dir", str(tmp_path),
    ])
    assert rc == 0
    assert list(tmp_path.glob("breadth_l0_mock_k1_seed*.json"))


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
