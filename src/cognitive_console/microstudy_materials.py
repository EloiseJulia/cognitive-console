"""Deterministic validation for the micro-study's machine-readable materials."""

from __future__ import annotations

import json
import hashlib
import math
import re
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
STATE_WORDS = (
    "unresolved", "diagnostic only", "withheld", "supported for this setting",
    "尚未确定", "仅供诊断", "暂不启用", "可在该设置下启用",
)
LOCALES = ("en", "zh-Hans")


def load_sources(
    stimuli_path: Path = STIMULI_PATH, sequences_path: Path = SEQUENCES_PATH
) -> tuple[dict[str, Any], dict[str, Any]]:
    return (
        json.loads(stimuli_path.read_text(encoding="utf-8")),
        json.loads(sequences_path.read_text(encoding="utf-8")),
    )


def canonical_locale_bytes(bundle: dict[str, Any]) -> bytes:
    return json.dumps(
        bundle, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def locale_manifest(stimuli: dict[str, Any]) -> dict[str, dict[str, str]]:
    return {
        locale: {
            "locale_bundle_version": (
                f"{stimuli['materials_version']}-{locale}"
            ),
            "locale_bundle_hash": hashlib.sha256(
                canonical_locale_bytes(stimuli["locales"][locale])
            ).hexdigest(),
        }
        for locale in stimuli["locale_contract"]["supported"]
    }


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
            return option.get("key", option["id"])
    return "A"


def equal_length_prediction(template: dict[str, Any]) -> str:
    lengths = {
        option.get("key", option["id"]): len(tokens(option["text"]))
        for option in template["options"]
    }
    target = statistics.median(lengths.values())
    return min(lengths, key=lambda key: (abs(lengths[key] - target), key))


def negation_prediction(template: dict[str, Any]) -> str:
    return _first_matching_option(template, {"neither", "no", "not", "unknown", "unavailable"})


def modal_prediction(template: dict[str, Any]) -> str:
    return _first_matching_option(template, {"required", "require", "requires", "now", "must"})


def read_prediction(template: dict[str, Any]) -> str:
    return _first_matching_option(template, {"initial", "初始"})


def _majority_key(keys: list[str]) -> str:
    counts = Counter(keys)
    maximum = max(counts.values())
    return min(key for key, count in counts.items() if count == maximum)


def _validate_source_schema(stimuli: dict[str, Any], sequences: dict[str, Any]) -> None:
    assert stimuli["schema_version"] == "microstudy-stimuli-v7-bilingual"
    assert sequences["schema_version"] == "microstudy-sequences-v1"
    assert set(stimuli) == {
        "schema_version", "materials_version", "status", "locale_contract",
        "nonlocalized", "locales",
    }
    assert stimuli["locale_contract"] == {
        "version": "microstudy-locale-contract-v1",
        "supported": list(LOCALES),
        "fallback": None,
        "auto_detect": False,
        "canonicalization": (
            "UTF-8 JSON, ensure_ascii=false, sort_keys=true, separators=(',', ':')"
        ),
        "stable_id_parity": True,
        "human_semantic_review": "UNVERIFIED_PRE_RECRUITMENT",
    }
    assert set(stimuli["locales"]) == set(LOCALES)
    nonlocalized = stimuli["nonlocalized"]
    assert len(nonlocalized["items"]) == 10
    assert len(nonlocalized["q2_templates"]) == 3
    assert len(sequences["sequences"]) == 20
    assert len({item["stimulus_id"] for item in nonlocalized["items"]}) == 10
    assert {template["template_id"] for template in nonlocalized["q2_templates"]} == {
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
        "flat_order",
        "q2",
        "state_routing_inputs",
        "expected_q1_key",
        "required_primitive_ids",
    }
    expected_inputs = {"tier", "evaluation_tier", "read_status", "comparison", "coherence_status"}
    expected_comparison = {"tested", "estimate", "ci_low", "ci_high", "registered_margin"}
    primitive_ids = nonlocalized["primitive_ids"]
    for item in nonlocalized["items"]:
        assert set(item) == expected_item_fields
        assert sorted(item["flat_order"]) == sorted(primitive_ids)
        assert set(item["state_routing_inputs"]) == expected_inputs
        assert set(item["state_routing_inputs"]["comparison"]) == expected_comparison
        assert item["expected_q1_key"] in Q1_KEYS
        assert len(item["required_primitive_ids"]) >= 2
        assert set(item["required_primitive_ids"]) <= set(primitive_ids)
        assert item["source_status"] in {"real_inspired_non_pass", "synthetic_rule_case"}
        assert item["source_note"]
    assert not any(
        "attention_check" in field
        for field in nonlocalized["export_schema"]["session_fields"]
    )
    assert nonlocalized["export_schema"]["free_text_fields"] == []
    assert {
        "ui_language", "locale_bundle_version", "locale_bundle_hash"
    } <= set(nonlocalized["export_schema"]["session_fields"])


def _stable_shape(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _stable_shape(child) for key, child in value.items()}
    if isinstance(value, list):
        if all(isinstance(row, dict) and "id" in row for row in value):
            return [(row["id"], _stable_shape(row)) for row in value]
        return [_stable_shape(child) for child in value]
    return "<localized>"


def _validate_locales(stimuli: dict[str, Any]) -> None:
    locales = stimuli["locales"]
    assert _stable_shape(locales["en"]) == _stable_shape(locales["zh-Hans"])
    nonlocalized = stimuli["nonlocalized"]
    primitive_ids = set(nonlocalized["primitive_ids"])
    item_ids = {item["stimulus_id"] for item in nonlocalized["items"]}
    template_ids = {
        template["template_id"] for template in nonlocalized["q2_templates"]
    }
    option_ids = {"A", "B", "C", "D"}
    for locale, bundle in locales.items():
        assert bundle["language_name"]
        assert len(bundle["onboarding"]["glossary"]) == 5
        assert len(bundle["onboarding"]["states"]) == 4
        assert {
            row["id"] for row in bundle["onboarding"]["states"]
        } == Q1_KEYS
        formal = bundle["formal"]
        assert set(formal["contract_labels"]) == primitive_ids
        assert len(formal["flat_labels"]) == 5
        assert {row["id"] for row in formal["items"]} == item_ids
        assert {
            row["id"] for row in formal["q2_templates"]
        } == template_ids
        for item in formal["items"]:
            assert set(item["primitive_evidence"]) == primitive_ids
        for template in formal["q2_templates"]:
            assert {row["id"] for row in template["options"]} == option_ids
        assert {
            row["id"] for row in formal["q1"]["options"]
        } == Q1_KEYS
        assert {
            row["id"] for row in bundle["practice"]["q1"]["options"]
        } == Q1_KEYS
        assert {
            row["id"] for row in bundle["practice"]["q2"]["options"]
        } == option_ids
        assert {
            row["id"] for row in bundle["diagnostic"]["options"]
        } == option_ids
        assert {
            row["id"] for row in bundle["ease"]["options"]
        } == {f"SEQ{i}" for i in range(1, 8)}
        encoded = json.dumps(
            {
                "onboarding": bundle["onboarding"],
                "formal": bundle["formal"],
                "practice": bundle["practice"],
                "buttons": bundle["buttons"],
                "progress": bundle["progress"],
                "ease": bundle["ease"],
                "diagnostic": bundle["diagnostic"],
                "export": bundle["export"],
                "debrief": bundle["debrief"],
                "errors": bundle["errors"],
            },
            ensure_ascii=False,
        ).lower()
        if locale == "en":
            assert not any("\u4e00" <= char <= "\u9fff" for char in encoded)
        else:
            assert any("\u4e00" <= char <= "\u9fff" for char in encoded)
    english = locales["en"]
    common_text = json.dumps(
        {
            "onboarding": english["onboarding"],
            "practice": english["practice"],
        }
    ).lower()
    common_tokens = set(tokens(common_text))
    assert "read" not in common_tokens
    for phrase in (
        "transfer", "bounded prompt comparator", "calibration warning", "evidence tier",
    ):
        assert phrase not in common_text
    practice = english["practice"]
    practice_text = json.dumps(practice).lower()
    for token in (
        "interval", "margin", "tier", "model", "method", "task",
        "evidence a", "evidence b", "transfer",
    ):
        assert token not in practice_text
    assert "read" not in set(tokens(practice_text))
    assert nonlocalized["answer_keys"]["practice"] == {
        "q1": "Q1_WITHHELD", "q2": "D"
    }
    assert nonlocalized["answer_keys"]["diagnostic"] == "A"
    assert locale_manifest(stimuli) == locale_manifest(stimuli)

    en_items = {
        item["id"]: item["primitive_evidence"]
        for item in locales["en"]["formal"]["items"]
    }
    zh_items = {
        item["id"]: item["primitive_evidence"]
        for item in locales["zh-Hans"]["formal"]["items"]
    }
    for item_id in item_ids:
        for primitive_id in primitive_ids:
            en_text = en_items[item_id][primitive_id]
            zh_text = zh_items[item_id][primitive_id]
            assert _numeric_literals(en_text) == _numeric_literals(zh_text)
            assert _polarity_symbols(en_text) == _polarity_symbols(zh_text)
            assert _semantic_flags(en_text, "en") == _semantic_flags(
                zh_text, "zh-Hans"
            )
    en_templates = {
        row["id"]: row for row in locales["en"]["formal"]["q2_templates"]
    }
    zh_templates = {
        row["id"]: row for row in locales["zh-Hans"]["formal"]["q2_templates"]
    }
    for template_id in template_ids:
        for en_option, zh_option in zip(
            en_templates[template_id]["options"],
            zh_templates[template_id]["options"],
        ):
            assert en_option["id"] == zh_option["id"]
            assert _semantic_flags(
                en_option["text"], "en"
            ) == _semantic_flags(zh_option["text"], "zh-Hans")


def _numeric_literals(text: str) -> list[str]:
    return re.findall(r"(?<![\w])\d+(?:\.\d+)?", text)


def _polarity_symbols(text: str) -> list[str]:
    return re.findall(r"[+−]", text)


def _semantic_flags(text: str, locale: str) -> set[str]:
    lowered = text.lower()
    vocabulary = {
        "en": {
            "missing": (
                "unknown", "unavailable", "not been completed", "0 completed",
                "no paired", "neither",
            ),
            "only": ("only", "alone"),
            "new_setting": ("newly specified", "another setting"),
            "below": ("below",),
            "near": ("near",),
            "above": ("above",),
            "initial": ("initial",),
            "comparison": ("paired comparison", "paired-comparison"),
            "boundary": ("boundary",),
        },
        "zh-Hans": {
            "missing": (
                "未知", "不可用", "尚未完成", "0 条已完成", "没有可", "都未", "无法",
            ),
            "only": ("仅",),
            "new_setting": ("新指定", "其他设置"),
            "below": ("低于",),
            "near": ("接近",),
            "above": ("高于",),
            "initial": ("初始",),
            "comparison": ("配对比较",),
            "boundary": ("边界",),
        },
    }[locale]
    return {
        flag
        for flag, markers in vocabulary.items()
        if any(marker in lowered for marker in markers)
    }


def _localized_leakage_counts(
    stimuli: dict[str, Any], locale: str
) -> dict[str, int]:
    items = stimuli["nonlocalized"]["items"]
    templates = {
        row["id"]: row
        for row in stimuli["locales"][locale]["formal"]["q2_templates"]
    }
    marker_sets = {
        "en": {
            "negation_marker": {"neither", "no", "not", "unknown", "unavailable"},
            "modal_marker": {"required", "require", "requires", "now", "must"},
            "initial_lexical": {"initial"},
        },
        "zh-Hans": {
            "negation_marker": {"未", "无法", "不可用", "未知"},
            "modal_marker": {"需要", "重新", "补充", "完成", "进行"},
            "initial_lexical": {"初始"},
        },
    }[locale]

    def char_length_prediction(template: dict[str, Any]) -> str:
        lengths = {
            option["id"]: sum(character.isalnum() for character in option["text"])
            for option in template["options"]
        }
        target = statistics.median(lengths.values())
        return min(lengths, key=lambda key: (abs(lengths[key] - target), key))

    def localized_marker_prediction(
        template: dict[str, Any], markers: set[str]
    ) -> str:
        for option in template["options"]:
            normalized = option["text"].lower()
            if any(marker in normalized for marker in markers):
                return option["id"]
        return "A"

    predictions = {
        "equal_length": [
            char_length_prediction(templates[item["q2"]["template_id"]])
            for item in items
        ],
        **{
            name: [
                localized_marker_prediction(
                    templates[item["q2"]["template_id"]], markers
                )
                for item in items
            ]
            for name, markers in marker_sets.items()
        },
    }
    counts = {
        name: sum(
            prediction == item["q2"]["correct_key"]
            for prediction, item in zip(values, items)
        )
        for name, values in predictions.items()
    }
    assert counts == {
        "equal_length": 2,
        "negation_marker": 3,
        "modal_marker": 2,
        "initial_lexical": 2,
    }
    return counts


def _validate_render_contract(stimuli: dict[str, Any]) -> None:
    nonlocalized = stimuli["nonlocalized"]
    render = nonlocalized["render_contract"]
    primitive_ids = nonlocalized["primitive_ids"]
    assert render["version"] == "microstudy-render-contract-v2-bilingual"
    assert render["common_evidence_text_source"] == (
        "locales[ui_language].formal.items[*].primitive_evidence"
    )
    assert render["conditions"]["contract"] == {
        "labels": "selected locale formal.contract_labels",
        "role_order_source": "primitive_ids",
        "role_order": primitive_ids,
    }
    assert render["conditions"]["flat"] == {
        "labels_by_position": "selected locale formal.flat_labels",
        "label_binding": "display position 1-5 after applying the current item's flat_order",
        "role_order_source": "items[*].flat_order",
    }

    dom = render["dom"]
    assert dom["card"] == {
        "tag": "article",
        "classes": ["evidence-card"],
        "data_attributes": [],
    }
    assert dom["rows_container"] == {"tag": "dl", "classes": ["evidence-rows"]}
    assert dom["row"] == {
        "tag": "div",
        "classes": ["evidence-row"],
        "data_attributes": ["data-row-id", "data-position"],
    }
    assert dom["label"] == {"tag": "dt", "classes": ["evidence-label"]}
    assert dom["body"] == {"tag": "dd", "classes": ["evidence-body"]}
    assert "selected locale" in dom["text_binding"]
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
    for locale in LOCALES:
        for item in stimuli["locales"][locale]["formal"]["items"]:
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
    for locale in LOCALES:
        materials = stimuli["locales"][locale]
        assert len(materials["onboarding"]["glossary"]) == 5
        assert len(materials["onboarding"]["steps"]) == 4
        assert materials["practice"]["narrative"]
        assert materials["practice"]["feedback"]


def _validate_parity_and_keys(stimuli: dict[str, Any]) -> dict[str, int]:
    nonlocalized = stimuli["nonlocalized"]
    primitive_ids = nonlocalized["primitive_ids"]
    templates = {
        template["template_id"]: template for template in nonlocalized["q2_templates"]
    }
    flat_position_counts: Counter[tuple[str, int]] = Counter()
    template_reuse: Counter[str] = Counter()
    key_counts: Counter[str] = Counter()
    q2_signatures: dict[str, set[str]] = {template_id: set() for template_id in templates}
    locale_items = {
        locale: {
            item["id"]: item["primitive_evidence"]
            for item in stimuli["locales"][locale]["formal"]["items"]
        }
        for locale in LOCALES
    }
    locale_templates = {
        locale: {
            template["id"]: template
            for template in stimuli["locales"][locale]["formal"]["q2_templates"]
        }
        for locale in LOCALES
    }
    for item in nonlocalized["items"]:
        for position, primitive_id in enumerate(item["flat_order"], start=1):
            flat_position_counts[(primitive_id, position)] += 1
        template_id = item["q2"]["template_id"]
        for locale in LOCALES:
            canonical = locale_items[locale][item["stimulus_id"]]
            contract = [canonical[primitive_id] for primitive_id in primitive_ids]
            flat = [canonical[primitive_id] for primitive_id in item["flat_order"]]
            assert sorted(map(normalize_text, contract)) == sorted(map(normalize_text, flat))
            template = locale_templates[locale][template_id]
            signature = json.dumps(
                {"text": template["text"], "options": template["options"]},
                ensure_ascii=False,
                sort_keys=True,
            )
            q2_signatures[template_id].add(f"{locale}:{signature}")
        template_reuse[template_id] += 1
        key_counts[item["q2"]["correct_key"]] += 1
    assert all(count == 2 for count in flat_position_counts.values())
    assert len(flat_position_counts) == len(primitive_ids) * 5
    assert all(len(signatures) == len(LOCALES) for signatures in q2_signatures.values())
    assert template_reuse == {"Q2-NEXT": 4, "Q2-BASELINE": 4, "Q2-COVERAGE": 2}
    assert key_counts == {"A": 2, "B": 2, "C": 3, "D": 3}
    for locale in LOCALES:
        forbidden_texts = [
            template["text"] for template in locale_templates[locale].values()
        ] + [
            option["text"]
            for template in locale_templates[locale].values()
            for option in template["options"]
        ] + [
            text
            for item in locale_items[locale].values()
            for text in item.values()
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
    items = stimuli["nonlocalized"]["items"]
    templates = {
        template["id"]: template
        for template in stimuli["locales"]["en"]["formal"]["q2_templates"]
    }
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
    expected = stimuli["nonlocalized"]["validation_contract"]["expected_counts"]
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
    _validate_locales(stimuli)
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
        "key_distribution": dict(
            Counter(
                item["q2"]["correct_key"]
                for item in stimuli["nonlocalized"]["items"]
            )
        ),
        "locale_manifest": locale_manifest(stimuli),
        "locale_leakage_counts": {
            locale: _localized_leakage_counts(stimuli, locale)
            for locale in LOCALES
        },
        "metrics": metrics,
        **sequence_metrics,
    }


def main() -> int:
    print(json.dumps(validate_materials(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
