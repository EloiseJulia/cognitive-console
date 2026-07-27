"""Task-manifest loaders for the novice-disclosure flagship harness."""

from __future__ import annotations

import json
from importlib import resources
from typing import List, Sequence

VALID_TIERS = {"always_required", "novice_required", "expert_appropriate_only"}


def _validate_task(item: dict, *, expected_split: str) -> None:
    if not item.get("id") or not item.get("prompt"):
        raise ValueError("task item requires id and prompt")
    if item.get("split") != expected_split:
        raise ValueError(f"{item.get('id')}: item must be tagged split={expected_split!r}")
    options = item.get("options", [])
    if not isinstance(options, list) or len(options) < 2:
        raise ValueError(f"{item.get('id')}: options must contain at least two choices")
    for field in ("alternatives", "caveats"):
        entries = item.get("manifest", {}).get(field, [])
        if not entries:
            raise ValueError(f"{item.get('id')}: manifest.{field} must be non-empty")
        for entry in entries:
            tier = entry.get("tier")
            if tier not in VALID_TIERS:
                raise ValueError(f"{item.get('id')}: invalid tier {tier!r}")


def _load_payload(filename: str) -> dict:
    path = resources.files(__package__).joinpath(f"data/{filename}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload


def _validate_unique(tasks: Sequence[dict], *, split: str) -> None:
    ids = [str(item.get("id")) for item in tasks]
    prompts = [str(item.get("prompt")) for item in tasks]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{split} task ids must be unique")
    if len(prompts) != len(set(prompts)):
        raise ValueError(f"{split} task prompts must be unique")


def load_flagship_l0_tasks() -> List[dict]:
    payload = _load_payload("flagship_l0_tasks.json")
    if payload.get("pool") != "dev_power_pilot" or payload.get("must_not_reuse_as_test") is not True:
        raise ValueError("flagship L0 task file must be marked as DEV-only power pilot data")
    tasks = payload.get("items", [])
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("flagship L0 task file has no items")
    _validate_unique(tasks, split="dev")
    for item in tasks:
        _validate_task(item, expected_split="dev")
    return tasks


def load_flagship_test_tasks() -> List[dict]:
    payload = _load_payload("flagship_test_tasks.json")
    if payload.get("pool") != "confirmatory_test_powered" or payload.get("split") != "test":
        raise ValueError("flagship TEST task file must be marked confirmatory_test_powered/test")
    tasks = payload.get("items", [])
    if not isinstance(tasks, list) or len(tasks) < 53:
        raise ValueError("flagship TEST task file must contain at least 53 items")
    _validate_unique(tasks, split="test")
    for item in tasks:
        _validate_task(item, expected_split="test")
    dev = load_flagship_l0_tasks()
    dev_ids = {str(item["id"]) for item in dev}
    dev_prompts = {str(item["prompt"]) for item in dev}
    overlap_ids = sorted(dev_ids & {str(item["id"]) for item in tasks})
    overlap_prompts = sorted(dev_prompts & {str(item["prompt"]) for item in tasks})
    if overlap_ids or overlap_prompts:
        raise ValueError(f"DEV/TEST task pools overlap: ids={overlap_ids} prompts={overlap_prompts[:3]}")
    return tasks
