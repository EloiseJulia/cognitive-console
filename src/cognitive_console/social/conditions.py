"""Frozen condition templates for the novice-disclosure flagship line."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Sequence


@dataclass(frozen=True)
class Condition:
    id: str
    label: str
    disclosure: str
    audience: str


CONDITIONS: Sequence[Condition] = (
    Condition("A", "control", "", "control"),
    Condition(
        "B",
        "novice_disclosure",
        "I'm a novice in this area; please explain simply and help me decide.",
        "novice",
    ),
    Condition(
        "E",
        "explain_simple",
        "Please explain this simply.",
        "novice",
    ),
    Condition(
        "C",
        "expert_disclosure",
        "I'm an expert in this area; be precise and assume I can evaluate tradeoffs.",
        "expert",
    ),
)

_BY_ID: Dict[str, Condition] = {c.id: c for c in CONDITIONS}


def condition_by_id(condition_id: str) -> Condition:
    try:
        return _BY_ID[str(condition_id)]
    except KeyError as exc:
        raise ValueError(f"unknown condition {condition_id!r}") from exc


def render_prompt(item: dict, condition: Condition) -> str:
    """Render matched task prompt; only the frozen condition line differs."""
    options = item.get("options", [])
    option_lines = "\n".join(f"- {o['id']}: {o['text']}" for o in options)
    disclosure = f"{condition.disclosure}\n\n" if condition.disclosure else ""
    return (
        "You are advising on a decision-support task. Give a concise answer that "
        "preserves the user's ability to compare options and verify important facts.\n\n"
        f"{disclosure}"
        f"Task: {item['prompt']}\n\n"
        f"Options:\n{option_lines}\n\n"
        "Respond with: (1) a recommendation if warranted, (2) key tradeoffs, "
        "(3) caveats or verification steps."
    )
