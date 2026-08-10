"""Deterministic validation for the micro-study's machine-readable materials."""

from __future__ import annotations

import json
import math
import statistics
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data" / "microstudy_contract_application"
STIMULI_PATH = DATA_DIR / "stimuli.json"
SEQUENCES_PATH = DATA_DIR / "sequences.json"
OPTION_KEYS = ("A", "B", "C", "D")
Q1_KEYS = {"Q1_UNRESOLVED", "Q1_DIAGNOSTIC", "Q1_WITHHELD", "Q1_SUPPORTED"}
STATE_WORDS = ("unresolved", "diagnostic only", "withheld control", "evidence-supported control")


def load_sources(
    stimuli_path: Path = STIMULI_PATH, sequences_path: Path = SEQUENCES_PATH
) -> tuple[dict[str, Any], dict[str, Any]]:
    return (
        json.loads(stimuli_path.read_text(encoding="utf-8")),
        json.loads(sequences_path.read_text(encoding="utf-8")),
    )


def tokens(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFKC", text).lower()
    return ["".join(run) for run in _alphanumeric_runs(normalized)]


def _alphanumeric_runs(text: str):
    run: list[str] = []
    for character in text:
        if character.isalnum():
            run.append(character)
        elif run:
            yield run
            run = []
    if run:
        yield run


def normalize_text(text: str) -> str:
    return " ".join(tokens(text))


def exact_binomial_upper_tail(correct: int, total: int, chance: float = 0.25) -> float:
    return sum(
        math.comb(total, k) * chance**k * (1.0 - chance) ** (total - k)
        for k in range(correct, total + 1)
    )


def route_state(inputs: dict[str, Any]) -> str:
    comparison = inputs["comparison"]
    if inputs["evaluation_tier"] != inputs["tier"]:
        return "Q1_UNRESOLVED"
    if inputs["read_status"] == "unsupported":
        return "Q1_UNRESOLVED"
    if not comparison["tested"]:
        return "Q1_DIAGNOSTIC"
    required = ("estimate", "ci_low", "ci_high", "registered_margin")
    if any(comparison[name] is None for name in required):
        return "Q1_UNRESOLVED"
    estimate = comparison["estimate"]
    ci_low = comparison["ci_low"]
    ci_high = comparison["ci_high"]
    margin = comparison["registered_margin"]
    if ci_low <= 0 <= ci_high:
        return "Q1_UNRESOLVED"
    if ci_high <= 0 or (ci_low > 0 and estimate < margin):
        return "Q1_WITHHELD"
    if ci_low > 0 and estimate >= margin:
        return "Q1_SUPPORTED" if inputs["coherence_status"] == "pass" else "Q1_WITHHELD"
    return "Q1_UNRESOLVED"


def single_row_q1(inputs: dict[str, Any]) -> str:
    comparison = inputs["comparison"]
    if not comparison["tested"]:
        return "Q1_DIAGNOSTIC"
    if comparison["ci_low"] is None or comparison["ci_high"] is None:
        return "Q1_UNRESOLVED"
    if comparison["ci_high"] <= 0:
        return "Q1_WITHHELD"
    if comparison["ci_low"] <= 0 <= comparison["ci_high"]:
        return "Q1_UNRESOLVED"
    if comparison["registered_margin"] is not None and comparison["estimate"] is not None:
        if comparison["ci_low"] > 0 and comparison["estimate"] >= comparison["registered_margin"]:
            return "Q1_SUPPORTED"
        if comparison["ci_low"] > 0 and comparison["estimate"] < comparison["registered_margin"]:
            return "Q1_WITHHELD"
    return "Q1_UNRESOLVED"


def _first_matching_option(template: dict[str, Any], words: set[str]) -> str:
    for option in template["options"]:
        if words.intersection(tokens(option["text"])):
            return option["key"]
    return "A"


def equal_length_prediction(template: dict[str, Any]) -> str:
    lengths = {option["key"]: len(tokens(option["text"])) for option in template["options"]}
    target = statistics.median(lengths.values())
    return min(lengths, key=lambda key: (abs(lengths[key] - target), key))


def negation_prediction(template: dict[str, Any]) -> str:
    return _first_matching_option(template, {"neither", "no", "not", "unknown", "unavailable"})


def modal_prediction(template: dict[str, Any]) -> str:
    return _first_matching_option(template, {"required", "require", "requires", "now", "must"})


def read_prediction(template: dict[str, Any]) -> str:
    return _first_matching_option(template, {"read"})


def _majority_key(keys: list[str]) -> str:
    counts = Counter(keys)
    maximum = max(counts.values())
    return min(key for key, count in counts.items() if count == maximum)


def _validate_source_schema(stimuli: dict[str, Any], sequences: dict[str, Any]) -> None:
    assert stimuli["schema_version"] == "microstudy-stimuli-v5"
    assert sequences["schema_version"] == "microstudy-sequences-v1"
    assert len(stimuli["items"]) == 10
    assert len(stimuli["q2_templates"]) == 3
    assert len(sequences["sequences"]) == 20
    assert len({item["stimulus_id"] for item in stimuli["items"]}) == 10
    assert {template["template_id"] for template in stimuli["q2_templates"]} == {
        "Q2-NEXT",
        "Q2-BASELINE",
        "Q2-COVERAGE",
    }
    expected_item_fields = {
        "stimulus_id",
        "content_set",
        "pattern_id",
        "source_status",
        "source_note",
        "hypothetical",
        "primitive_evidence",
        "flat_order",
        "q2",
        "state_routing_inputs",
        "expected_q1_key",
        "required_primitive_ids",
    }
    expected_inputs = {"tier", "evaluation_tier", "read_status", "comparison", "coherence_status"}
    expected_comparison = {"tested", "estimate", "ci_low", "ci_high", "registered_margin"}
    primitive_ids = stimuli["primitive_ids"]
    for item in stimuli["items"]:
        assert set(item) == expected_item_fields
        assert set(item["primitive_evidence"]) == set(primitive_ids)
        assert sorted(item["flat_order"]) == sorted(primitive_ids)
        assert set(item["state_routing_inputs"]) == expected_inputs
        assert set(item["state_routing_inputs"]["comparison"]) == expected_comparison
        assert item["expected_q1_key"] in Q1_KEYS
        assert len(item["required_primitive_ids"]) >= 2
        assert set(item["required_primitive_ids"]) <= set(primitive_ids)
        assert item["source_status"] in {"real_inspired_non_pass", "synthetic_rule_case"}
        assert item["source_note"]
    assert not any("attention_check" in field for field in stimuli["export_schema"]["session_fields"])
    assert stimuli["export_schema"]["free_text_fields"] == []


def _validate_render_contract(stimuli: dict[str, Any]) -> None:
    render = stimuli["render_contract"]
    primitive_ids = stimuli["primitive_ids"]
    expected_contract_labels = {
        "representation": "READ",
        "comparison": "TRANSFER",
        "comparator": "BOUNDED PROMPT COMPARATOR",
        "coherence": "CALIBRATION WARNING",
        "scope": "EVIDENCE TIER",
    }
    expected_flat_labels = [f"Evidence {letter}" for letter in "ABCDE"]
    assert render["version"] == "microstudy-render-contract-v1"
    assert render["common_evidence_text_source"] == "items[*].primitive_evidence"
    assert stimuli["contract_headings"] == expected_contract_labels
    assert render["conditions"]["contract"] == {
        "labels": expected_contract_labels,
        "role_order_source": "primitive_ids",
        "role_order": primitive_ids,
    }
    assert render["conditions"]["flat"] == {
        "labels_by_position": expected_flat_labels,
        "label_binding": "display position 1-5 after applying the current item's flat_order",
        "role_order_source": "items[*].flat_order",
    }

    dom = render["dom"]
    assert dom["card"] == {
        "tag": "article",
        "classes": ["evidence-card"],
        "data_attributes": ["data-condition", "data-stimulus-id"],
    }
    assert dom["rows_container"] == {"tag": "dl", "classes": ["evidence-rows"]}
    assert dom["row"] == {
        "tag": "div",
        "classes": ["evidence-row"],
        "data_attributes": ["data-evidence-id", "data-position"],
    }
    assert dom["label"] == {"tag": "dt", "classes": ["evidence-label"]}
    assert dom["body"] == {"tag": "dd", "classes": ["evidence-body"]}
    assert "primitive_evidence" in dom["text_binding"]
    assert "only condition-dependent fields" in dom["text_binding"]

    geometry = render["geometry"]
    assert geometry["desktop_viewport"] == {
        "width_px": 1440,
        "height_px": 900,
        "minimum_width_px": 1280,
    }
    assert geometry["card"] == {
        "max_width_px": 960,
        "padding_px": 24,
        "row_gap_px": 12,
        "overflow": "visible",
    }
    assert geometry["row"] == {
        "label_width_px": 240,
        "body_width_px": 648,
        "min_height_px": 72,
        "padding_block_px": 12,
        "column_gap_px": 24,
    }
    assert geometry["typography"] == {
        "label_font_size_px": 14,
        "body_font_size_px": 16,
        "line_height": 1.5,
    }
    assert (
        2 * geometry["card"]["padding_px"]
        + geometry["row"]["label_width_px"]
        + geometry["row"]["column_gap_px"]
        + geometry["row"]["body_width_px"]
        == geometry["card"]["max_width_px"]
    )
    assert "identical" in geometry["condition_invariance"]
    assert "no internal scrollbars" in geometry["desktop_overflow"]
    assert "may scroll" in geometry["zoom_200"] and "clipped or hidden" in geometry["zoom_200"]

    audit = render["parity_audit"]
    assert audit["viewports"] == [
        {"width_px": 1440, "height_px": 900},
        {"width_px": 1280, "height_px": 800},
    ]
    assert audit["geometry_tolerance_px"] == 1
    assert len(audit["dom_expectations"]) == 4
    assert "byte-identical by evidence ID" in audit["text_identity"]
    assert audit["forbidden_evidence_row_content"] == [
        "answer",
        "state",
        "verdict",
        "action",
    ]
    assert "Mask label text glyphs only" in audit["screenshot_comparison"]["pixel_mask"]
    assert "declared row permutation" in audit["screenshot_comparison"]["structural_expectation"]
    forbidden = set(audit["forbidden_evidence_row_content"])
    for item in stimuli["items"]:
        assert not forbidden.intersection(
            token
            for evidence_text in item["primitive_evidence"].values()
            for token in tokens(evidence_text)
        )

    treatment = render["treatment_acknowledgement"]
    assert "word count" in treatment["label_word_count_and_visual_difference"]
    assert "part of the semantic-organization treatment" in treatment[
        "label_word_count_and_visual_difference"
    ]
    assert "Do not add filler words" in treatment["no_filler_padding"]


def _validate_tutorial_and_post_task(stimuli: dict[str, Any]) -> None:
    materials = stimuli["participant_materials"]
    legend = materials["legend"].lower()
    required_phrases = (
        "unsupported read stays unresolved",
        "supported read with an untested comparison is diagnostic only",
        "interval crossing zero stays unresolved",
        "showing no superiority",
        "is withheld if coherence fails",
        "supported only if coherence passes",
        "tier change needs new tier-specific evidence",
    )
    assert all(phrase in legend for phrase in required_phrases)
    diagnostic = materials["post_task_manipulation_diagnostic"]
    assert [option["key"] for option in diagnostic["options"]] == list(OPTION_KEYS)
    assert diagnostic["correct_key"] == "A"
    assert diagnostic["used_for_exclusion"] is False
    ease = materials["block_ease"]
    assert [option["key"] for option in ease["options"]] == [f"SEQ{i}" for i in range(1, 8)]
    assert ease["when_shown"]
    assert ease["nullable"] is True
    assert ease["export_fields"] == ["block_1_ease", "block_2_ease"]
    assert ease["used_for_exclusion"] is False
    practice = materials["practice"]
    assert practice["q1"]["correct_key"] == "Q1_UNRESOLVED"
    assert practice["q2"]["correct_key"] == "B"
    assert practice["feedback"]


def _validate_parity_and_keys(stimuli: dict[str, Any]) -> dict[str, int]:
    primitive_ids = stimuli["primitive_ids"]
    templates = {template["template_id"]: template for template in stimuli["q2_templates"]}
    flat_position_counts: Counter[tuple[str, int]] = Counter()
    template_reuse: Counter[str] = Counter()
    key_counts: Counter[str] = Counter()
    q2_signatures: dict[str, set[str]] = {template_id: set() for template_id in templates}
    for item in stimuli["items"]:
        canonical = item["primitive_evidence"]
        contract = [canonical[primitive_id] for primitive_id in primitive_ids]
        flat = [canonical[primitive_id] for primitive_id in item["flat_order"]]
        assert sorted(map(normalize_text, contract)) == sorted(map(normalize_text, flat))
        for position, primitive_id in enumerate(item["flat_order"], start=1):
            flat_position_counts[(primitive_id, position)] += 1
        template_id = item["q2"]["template_id"]
        template = templates[template_id]
        signature = json.dumps(
            {"text": template["text"], "options": template["options"]},
            ensure_ascii=False,
            sort_keys=True,
        )
        q2_signatures[template_id].add(signature)
        template_reuse[template_id] += 1
        key_counts[item["q2"]["correct_key"]] += 1
    assert all(count == 2 for count in flat_position_counts.values())
    assert len(flat_position_counts) == len(primitive_ids) * 5
    assert all(len(signatures) == 1 for signatures in q2_signatures.values())
    assert template_reuse == {"Q2-NEXT": 4, "Q2-BASELINE": 4, "Q2-COVERAGE": 2}
    assert key_counts == {"A": 2, "B": 2, "C": 3, "D": 3}
    forbidden_texts = [
        template["text"] for template in templates.values()
    ] + [
        option["text"] for template in templates.values() for option in template["options"]
    ] + [
        text for item in stimuli["items"] for text in item["primitive_evidence"].values()
    ]
    for text in forbidden_texts:
        lowered = normalize_text(text)
        assert not any(state_word in lowered for state_word in STATE_WORDS)
    return dict(template_reuse)


def _validate_sequences(sequences: dict[str, Any]) -> dict[str, int]:
    base = sequences["base_pattern_order"]
    offset = sequences["block_2_rotation_offset"]
    rows: list[dict[str, Any]] = []
    codes = []
    for sequence in sequences["sequences"]:
        code = sequence["code"]
        codes.append(code)
        letter = code[0]
        rotation = int(code[1:]) - 1
        expected_block_1 = base[rotation:] + base[:rotation]
        block_2_rotation = (rotation + offset) % len(base)
        expected_block_2 = base[block_2_rotation:] + base[:block_2_rotation]
        assert sequence["block_1"] == expected_block_1
        assert sequence["block_2"] == expected_block_2
        mapping = sequences["letter_mapping"][letter]
        content_ids = []
        for block_number in (1, 2):
            block_key = f"block_{block_number}"
            cell = mapping[block_key]
            for position, pattern in enumerate(sequence[block_key], start=1):
                content_id = f"MS-{pattern}-{cell['content_set']}"
                content_ids.append(content_id)
                rows.append(
                    {
                        "code": code,
                        "condition": cell["condition"],
                        "content_set": cell["content_set"],
                        "pattern": pattern,
                        "position": position,
                        "block": block_number,
                        "content_id": content_id,
                    }
                )
        assert len(set(content_ids)) == 10
        positions_1 = {pattern: index for index, pattern in enumerate(sequence["block_1"], start=1)}
        positions_2 = {pattern: index for index, pattern in enumerate(sequence["block_2"], start=1)}
        assert all(positions_1[pattern] != positions_2[pattern] for pattern in base)
    assert codes == [f"{letter}{suffix}" for letter in "ABCD" for suffix in range(1, 6)]
    assert len(rows) == 200
    assert set(Counter((row["pattern"], row["position"]) for row in rows).values()) == {8}
    assert set(
        Counter(
            (row["condition"], row["content_set"], row["pattern"], row["position"])
            for row in rows
        ).values()
    ) == {2}
    assert set(Counter((row["content_id"], row["condition"]) for row in rows).values()) == {10}
    return {"sequence_count": len(codes), "trial_row_count": len(rows)}


def _score_predictions(
    items: list[dict[str, Any]], predictions: list[str], answer_field: Callable[[dict[str, Any]], str]
) -> int:
    return sum(prediction == answer_field(item) for item, prediction in zip(items, predictions))


def _leakage_metrics(stimuli: dict[str, Any]) -> dict[str, dict[str, float | int | None]]:
    items = stimuli["items"]
    templates = {template["template_id"]: template for template in stimuli["q2_templates"]}
    keys_by_template: dict[str, list[str]] = {
        template_id: [
            item["q2"]["correct_key"]
            for item in items
            if item["q2"]["template_id"] == template_id
        ]
        for template_id in templates
    }
    oracle_by_template = {
        template_id: _majority_key(keys) for template_id, keys in keys_by_template.items()
    }
    oracle = [oracle_by_template[item["q2"]["template_id"]] for item in items]
    loo = []
    for index, item in enumerate(items):
        other_keys = [
            candidate["q2"]["correct_key"]
            for other_index, candidate in enumerate(items)
            if other_index != index and candidate["q2"]["template_id"] == item["q2"]["template_id"]
        ]
        loo.append(_majority_key(other_keys))
    global_prediction = _majority_key([item["q2"]["correct_key"] for item in items])
    prediction_sets = {
        "oracle_template": oracle,
        "loo_template": loo,
        "global_position": [global_prediction] * len(items),
        "equal_length": [
            equal_length_prediction(templates[item["q2"]["template_id"]]) for item in items
        ],
        "negation_marker": [
            negation_prediction(templates[item["q2"]["template_id"]]) for item in items
        ],
        "modal_marker": [
            modal_prediction(templates[item["q2"]["template_id"]]) for item in items
        ],
        "read_lexical": [
            read_prediction(templates[item["q2"]["template_id"]]) for item in items
        ],
    }
    q2_answer = lambda item: item["q2"]["correct_key"]
    counts = {
        name: _score_predictions(items, predictions, q2_answer)
        for name, predictions in prediction_sets.items()
    }
    single_predictions = [single_row_q1(item["state_routing_inputs"]) for item in items]
    counts["single_row_q1"] = _score_predictions(
        items, single_predictions, lambda item: item["expected_q1_key"]
    )
    counts["combined_oracle_cca"] = sum(
        q1 == item["expected_q1_key"] and q2 == item["q2"]["correct_key"]
        for item, q1, q2 in zip(items, single_predictions, oracle)
    )
    counts["combined_loo_cca"] = sum(
        q1 == item["expected_q1_key"] and q2 == item["q2"]["correct_key"]
        for item, q1, q2 in zip(items, single_predictions, loo)
    )
    counts["router"] = sum(
        route_state(item["state_routing_inputs"]) == item["expected_q1_key"] for item in items
    )
    expected = stimuli["validation_contract"]["expected_counts"]
    assert counts == expected, f"leakage metric drift: expected={expected}, actual={counts}"
    metrics: dict[str, dict[str, float | int | None]] = {}
    for name, correct in counts.items():
        inferential = name != "single_row_q1" and name != "router"
        metrics[name] = {
            "correct": correct,
            "total": len(items),
            "accuracy": correct / len(items),
            "binomial_p_upper_vs_0_25": (
                exact_binomial_upper_tail(correct, len(items)) if inferential else None
            ),
        }
    return metrics


def validate_materials(
    stimuli_path: Path = STIMULI_PATH, sequences_path: Path = SEQUENCES_PATH
) -> dict[str, Any]:
    stimuli, sequences = load_sources(stimuli_path, sequences_path)
    _validate_source_schema(stimuli, sequences)
    _validate_render_contract(stimuli)
    _validate_tutorial_and_post_task(stimuli)
    template_reuse = _validate_parity_and_keys(stimuli)
    sequence_metrics = _validate_sequences(sequences)
    metrics = _leakage_metrics(stimuli)
    return {
        "status": "PASS",
        "schema_version": stimuli["schema_version"],
        "materials_version": stimuli["materials_version"],
        "template_reuse": template_reuse,
        "key_distribution": dict(Counter(item["q2"]["correct_key"] for item in stimuli["items"])),
        "metrics": metrics,
        **sequence_metrics,
    }


def main() -> int:
    print(json.dumps(validate_materials(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
