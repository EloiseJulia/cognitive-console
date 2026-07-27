"""Task-manifest loader for the L0 novice-disclosure harness."""

from __future__ import annotations

import json
from importlib import resources
from typing import List

VALID_TIERS = {"always_required", "novice_required", "expert_appropriate_only"}


def _validate_task(item: dict) -> None:
    if not item.get("id") or not item.get("prompt"):
        raise ValueError("task item requires id and prompt")
    for field in ("alternatives", "caveats"):
        entries = item.get("manifest", {}).get(field, [])
        if not entries:
            raise ValueError(f"{item.get('id')}: manifest.{field} must be non-empty")
        for entry in entries:
            tier = entry.get("tier")
            if tier not in VALID_TIERS:
                raise ValueError(f"{item.get('id')}: invalid tier {tier!r}")


def load_flagship_l0_tasks() -> List[dict]:
    path = resources.files(__package__).joinpath("data/flagship_l0_tasks.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    tasks = payload.get("items", [])
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("flagship L0 task file has no items")
    for item in tasks:
        _validate_task(item)
    return tasks
