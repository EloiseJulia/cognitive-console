"""Validated access to V10 button-board materials and private derived keys."""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from typing import Any

from cognitive_console.button_board_materials import (
    FORMAL_SLOTS,
    LOCALES,
    Q1_OPTIONS,
    Q1_PUBLIC_IDS,
    locale_manifest,
    material_hashes,
    validated_sources,
)


def locale_bundle_metadata(locale: str) -> dict[str, str]:
    materials, _, _ = validated_sources()
    try:
        return locale_manifest(materials)[locale]
    except KeyError:
        raise ValueError(f"unsupported locale: {locale}") from None


def common_materials(locale: str) -> dict[str, Any]:
    materials, sequences, _ = validated_sources()
    if locale not in LOCALES:
        raise ValueError("unsupported locale")
    return {
        "selected_locale": locale,
        "materials_version": materials["materials_version"],
        **locale_bundle_metadata(locale),
        "common": json.loads(json.dumps(materials["locales"][locale]["common"])),
        "practice": json.loads(json.dumps(materials["locales"][locale]["practice"])),
        "sequence_count": len(sequences["sequences"]),
    }


def q1_public_to_state(option_id: str) -> str:
    for row in Q1_OPTIONS:
        if row["id"] == option_id:
            return row["state"]
    raise ValueError("invalid Q1 option")


def q1_state_to_public(state: str) -> str:
    try:
        return Q1_PUBLIC_IDS[state]
    except KeyError:
        raise ValueError("invalid Q1 state") from None


def stable_option_order(
    rows: list[dict[str, Any]],
    participant_code: str,
    scene_id: str,
    materials_hash: str,
    kind: str,
) -> list[dict[str, Any]]:
    def sort_key(row: dict[str, Any]) -> str:
        value = (
            f"{participant_code}\0{scene_id}\0{materials_hash}\0{kind}\0{row['id']}"
        ).encode("utf-8")
        return hashlib.sha256(value).hexdigest()

    return sorted(json.loads(json.dumps(rows)), key=sort_key)


def planned_trials(
    sequence_id: str,
    ab_variant: str,
    participant_code: str,
) -> list[dict[str, Any]]:
    materials, sequences, keys = validated_sources()
    if ab_variant not in {"F1", "F2"}:
        raise ValueError("invalid A/B variant")
    sequence = next(
        (
            row
            for row in sequences["sequences"]
            if row["sequence_id"] == sequence_id
        ),
        None,
    )
    if sequence is None:
        raise ValueError("unknown sequence")
    hashes = material_hashes()
    locale_independent_hash = hashes["canonical_materials_hash"]
    scenes = materials["locales"]["en"]["scenes"]
    planned = []
    for slot_index, slot in enumerate(sequence["slots"], 1):
        scene_id = ab_variant if slot["scene_slot"] == "FAB" else slot["scene_slot"]
        if scene_id not in keys["scenes"] or scene_id not in scenes:
            raise ValueError("unknown formal scene")
        key = keys["scenes"][scene_id]
        planned.append(
            {
                "slot_index": slot_index,
                "position": slot["position"],
                "scene_slot": slot["scene_slot"],
                "scene_id": scene_id,
                "q1_order": slot["q1_order"],
                "scope_order_ids": [
                    row["id"]
                    for row in stable_option_order(
                        scenes[scene_id]["scope_options"],
                        participant_code,
                        scene_id,
                        locale_independent_hash,
                        "scope",
                    )
                ],
                "reason_order_ids": [
                    row["id"]
                    for row in stable_option_order(
                        scenes[scene_id]["reason_options"],
                        participant_code,
                        scene_id,
                        locale_independent_hash,
                        "reason",
                    )
                ],
                **json.loads(json.dumps(key)),
            }
        )
    if len(planned) != len(FORMAL_SLOTS):
        raise ValueError("formal plan must have six slots")
    return planned


__all__ = [
    "common_materials",
    "locale_bundle_metadata",
    "material_hashes",
    "planned_trials",
    "q1_public_to_state",
    "q1_state_to_public",
    "stable_option_order",
    "validated_sources",
]
