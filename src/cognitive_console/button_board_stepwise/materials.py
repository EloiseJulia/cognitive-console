"""Validated public/private access to V11 stepwise materials."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from cognitive_console.button_board_stepwise_materials import (
    FORMAL_SLOTS,
    LOCALES,
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
    common = json.loads(json.dumps(materials["locales"][locale]["common"]))
    common.pop("questions", None)
    return {
        "selected_locale": locale,
        "materials_version": materials["materials_version"],
        **locale_bundle_metadata(locale),
        "common": common,
        "practice": json.loads(json.dumps(materials["locales"][locale]["practice"])),
        "sequence_count": len(sequences["sequences"]),
    }


def stable_option_order(
    rows: list[dict[str, Any]],
    participant_code: str,
    scene_id: str,
    materials_hash: str,
    kind: str,
) -> list[dict[str, Any]]:
    def key(row: dict[str, Any]) -> str:
        payload = (
            f"{participant_code}\0{scene_id}\0{materials_hash}\0{kind}\0{row['id']}"
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    return sorted(json.loads(json.dumps(rows)), key=key)


def planned_trials(
    sequence_id: str,
    ab_variant: str,
    participant_code: str,
) -> list[dict[str, Any]]:
    materials, sequences, keys = validated_sources()
    if ab_variant not in {"A", "B"}:
        raise ValueError("invalid A/B variant")
    sequence = next(
        (row for row in sequences["sequences"] if row["sequence_id"] == sequence_id),
        None,
    )
    if sequence is None:
        raise ValueError("unknown sequence")
    canonical_hash = material_hashes()["canonical_materials_hash"]
    scenes = materials["locales"]["en"]["scenes"]
    planned = []
    for slot_index, slot in enumerate(sequence["slots"], 1):
        scene_id = f"AB1-{ab_variant}" if slot["scene_slot"] == "AB1" else slot["scene_slot"]
        scene = scenes[scene_id]
        planned.append(
            {
                "slot_index": slot_index,
                "position": slot["position"],
                "scene_slot": slot["scene_slot"],
                "scene_id": scene_id,
                "scope_order_ids": [
                    row["id"]
                    for row in stable_option_order(
                        scene["scope_options"],
                        participant_code,
                        scene_id,
                        canonical_hash,
                        "scope",
                    )
                ],
                **json.loads(json.dumps(keys["scenes"][scene_id])),
            }
        )
    if len(planned) != len(FORMAL_SLOTS):
        raise ValueError("formal plan must contain six slots")
    return planned


def scene_material(locale: str, scene_id: str) -> dict[str, Any]:
    materials, _, _ = validated_sources()
    if locale not in LOCALES:
        raise ValueError("unsupported locale")
    try:
        return json.loads(json.dumps(materials["locales"][locale]["scenes"][scene_id]))
    except KeyError:
        raise ValueError("unknown scene") from None


def question_material(locale: str, step: int) -> dict[str, Any]:
    materials, _, _ = validated_sources()
    if locale not in LOCALES or step not in range(1, 7):
        raise ValueError("unsupported question")
    return json.loads(
        json.dumps(materials["locales"][locale]["common"]["questions"][str(step)])
    )


__all__ = [
    "common_materials",
    "locale_bundle_metadata",
    "material_hashes",
    "planned_trials",
    "question_material",
    "scene_material",
    "stable_option_order",
    "validated_sources",
]
