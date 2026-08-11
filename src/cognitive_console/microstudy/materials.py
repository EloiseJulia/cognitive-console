"""Validated access to the authoritative micro-study JSON."""

from __future__ import annotations

import hashlib
from functools import lru_cache
from typing import Any

from cognitive_console.microstudy_materials import (
    SEQUENCES_PATH,
    STIMULI_PATH,
    load_sources,
    locale_manifest,
    route_state,
    validate_materials,
)


def material_hashes() -> dict[str, str]:
    return {
        "stimuli_sha256": hashlib.sha256(STIMULI_PATH.read_bytes()).hexdigest(),
        "sequences_sha256": hashlib.sha256(SEQUENCES_PATH.read_bytes()).hexdigest(),
    }


def locale_bundle_metadata(locale: str) -> dict[str, str]:
    stimuli, _ = validated_sources()
    try:
        return locale_manifest(stimuli)[locale]
    except KeyError:
        raise ValueError(f"unsupported locale: {locale}") from None


@lru_cache(maxsize=1)
def validated_sources() -> tuple[dict[str, Any], dict[str, Any]]:
    validate_materials()
    return load_sources()


def planned_trials(sequence_code: str) -> list[dict[str, Any]]:
    stimuli, sequences = validated_sources()
    sequence = next(
        (row for row in sequences["sequences"] if row["code"] == sequence_code), None
    )
    if sequence is None:
        raise ValueError(f"unknown sequence: {sequence_code}")
    mapping = sequences["letter_mapping"][sequence_code[0]]
    items = {
        (item["pattern_id"], item["content_set"]): item
        for item in stimuli["nonlocalized"]["items"]
    }
    slots: list[dict[str, Any]] = []
    for block in (1, 2):
        cell = mapping[f"block_{block}"]
        for position, pattern in enumerate(sequence[f"block_{block}"], 1):
            item = items[(pattern, cell["content_set"])]
            derived_q1 = route_state(item["state_routing_inputs"])
            if derived_q1 != item["expected_q1_key"]:
                raise ValueError(f"router/key mismatch for {item['stimulus_id']}")
            slots.append(
                {
                    "slot_index": len(slots) + 1,
                    "condition": cell["condition"],
                    "item": item["stimulus_id"],
                    "pattern": pattern,
                    "content_set": cell["content_set"],
                    "block": block,
                    "position": position,
                    "q1_key": derived_q1,
                    "q2_key": item["q2"]["correct_key"],
                    "q2_template_id": item["q2"]["template_id"],
                }
            )
    return slots
