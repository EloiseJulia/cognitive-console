"""Fail-closed Transformers compatibility for the ITI positive control."""

from __future__ import annotations

import importlib.metadata
from typing import Dict, Mapping

REQUIRED_TRANSFORMERS_VERSION = "4.44.2"
GENERATION_CONFIG_METADATA_KEYS = {
    "_commit_hash",
    "_from_model_config",
    "_original_object_hash",
    "transformers_version",
}

# These knobs were added after Transformers 4.44.2. Their frozen values are
# neutral, so absence in the pinned runtime cannot change decoding behavior.
TRANSFORMERS_4_44_2_PROTOCOL_ONLY_NEUTRAL_FIELDS = {
    "assistant_confidence_threshold": None,
    "assistant_early_exit": None,
    "assistant_ensemble_weight": None,
    "assistant_lookbehind": None,
    "compile_config": None,
    "continuous_batching_config": None,
    "disable_compile": None,
    "is_assistant": None,
    "max_cache_len": None,
    "prefill_chunk_size": None,
    "target_lookbehind": None,
    "top_h": None,
    "use_mtp": None,
}


def installed_transformers_version() -> str:
    try:
        return importlib.metadata.version("transformers")
    except importlib.metadata.PackageNotFoundError as exc:
        raise RuntimeError(
            f"Transformers {REQUIRED_TRANSFORMERS_VERSION} is required"
        ) from exc


def assert_transformers_compatibility(
    installed_version: str | None = None,
) -> Dict[str, object]:
    version = installed_version or installed_transformers_version()
    if version != REQUIRED_TRANSFORMERS_VERSION:
        raise RuntimeError(
            "ITI positive control requires exact Transformers "
            f"{REQUIRED_TRANSFORMERS_VERSION}; found {version}"
        )
    return {
        "required_version": REQUIRED_TRANSFORMERS_VERSION,
        "installed_version": version,
        "protocol_only_neutral_fields": dict(
            TRANSFORMERS_4_44_2_PROTOCOL_ONLY_NEUTRAL_FIELDS
        ),
    }


def explicit_generation_material(
    runtime_defaults: Mapping[str, object],
    *,
    protocol_fields: Mapping[str, object],
    overrides: Mapping[str, object],
    installed_version: str | None = None,
) -> Dict[str, object]:
    """Return every 4.44.2 runtime field with frozen overrides applied."""

    assert_transformers_compatibility(installed_version)
    runtime_fields = set(runtime_defaults) - GENERATION_CONFIG_METADATA_KEYS
    unsupported = set(protocol_fields) - runtime_fields
    expected_unsupported = set(protocol_fields) & set(
        TRANSFORMERS_4_44_2_PROTOCOL_ONLY_NEUTRAL_FIELDS
    )
    if unsupported != expected_unsupported:
        raise RuntimeError(
            "Transformers 4.44.2 generation-field schema drift: "
            f"unsupported={sorted(unsupported)}, "
            f"expected={sorted(expected_unsupported)}"
        )
    for field in unsupported:
        expected = TRANSFORMERS_4_44_2_PROTOCOL_ONLY_NEUTRAL_FIELDS[field]
        if protocol_fields[field] != expected:
            raise RuntimeError(
                f"protocol-only generation field {field} is not neutral"
            )
    material = {
        key: value
        for key, value in runtime_defaults.items()
        if key not in GENERATION_CONFIG_METADATA_KEYS
    }
    material.update(
        {
            key: value
            for key, value in protocol_fields.items()
            if key in runtime_fields
        }
    )
    unknown_overrides = set(overrides) - runtime_fields
    if unknown_overrides:
        raise RuntimeError(
            "generation overrides are unavailable in Transformers 4.44.2: "
            f"{sorted(unknown_overrides)}"
        )
    material.update(overrides)
    if set(material) != runtime_fields:
        raise RuntimeError("not every Transformers 4.44.2 generation field is explicit")
    return material
