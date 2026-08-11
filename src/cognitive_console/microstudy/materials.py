"""Validated access to the authoritative V9 scenario materials."""

from __future__ import annotations

import hashlib
from functools import lru_cache
from typing import Any

from cognitive_console.microstudy_materials import (
    MATERIALS_PATH,
    SEQUENCES_PATH,
    SOURCE_REGISTRY_PATH,
    load_sources,
    locale_manifest,
    private_answer_keys,
    validate_materials,
)


def material_hashes() -> dict[str, str]:
    return {
        "materials_sha256": hashlib.sha256(MATERIALS_PATH.read_bytes()).hexdigest(),
        "sequences_sha256": hashlib.sha256(SEQUENCES_PATH.read_bytes()).hexdigest(),
        "source_registry_sha256": hashlib.sha256(
            SOURCE_REGISTRY_PATH.read_bytes()
        ).hexdigest(),
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
    materials, sequences = validated_sources()
    sequence = next(
        (row for row in sequences["sequences"] if row["code"] == sequence_code), None
    )
    if sequence is None:
        raise ValueError(f"unknown sequence: {sequence_code}")
    keys = private_answer_keys()
    ticket_codes = set(materials["nonlocalized"]["ticket_codes"])
    slots = []
    for index, row in enumerate(sequence["slots"], 1):
        ticket_code = row["ticket_code"]
        if ticket_code not in ticket_codes or ticket_code not in keys:
            raise ValueError(f"unknown ticket: {ticket_code}")
        slots.append(
            {
                "slot_index": index,
                "ticket_code": ticket_code,
                "position": row["position"],
                "condition": row["condition"],
                "q1_key": keys[ticket_code]["q1_code"],
                "q2_key": keys[ticket_code]["q2_code"],
            }
        )
    return slots
