"""Automatic per-axis behavioral proxies (C2b) — NO external/paid judge.

`behavior_score(text, axis) -> float` scores a generated response along one
cognitive axis using CRUDE, purely-lexical heuristics. These are exploratory
proxies, NOT validated psychometric instruments — they count surface markers
(reasoning connectives, hedges, pushback words, tangent phrases) and answer
length. They are good enough to detect a LARGE, deliberate behavioral shift
(e.g. a step-by-step answer vs a one-word answer, an agreeable answer vs a
skeptical one) for an exploratory C2b read, but they will misfire on subtle or
adversarial text and MUST NOT be reported as a calibrated measurement.

IMPORTANT (judgment call flagged for the Manager): the whole C2b "does steering
reach behavior a bounded prompt cannot?" read hangs on these proxies. A stronger
follow-up would replace them with a held-out task with ground truth (TruthfulQA
calibration for uncertainty, a reasoning-gain task for deliberation, a sycophancy
probe for skepticism — see data/axes.yaml bottom_up_risk notes) or a blinded
human/independent-model rating. Until then every number these produce is
EXPLORATORY.

Each proxy returns a float in [0, 1] where higher = MORE of the axis's positive
pole (more deliberate / more skeptical / more uncertainty-aware / more focused).
The scores across axes are NOT on a common calibrated scale; only WITHIN-axis
comparisons (prompt vs steer vs conflict, same axis) are meaningful.
"""

from __future__ import annotations

import math
import re
from typing import Dict, List, Sequence

AXES: List[str] = ["deliberation", "skepticism", "uncertainty_awareness", "focus"]


def _words(text: str) -> List[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


def _count_markers(text_lower: str, markers: Sequence[str]) -> int:
    """Total (overlapping-safe) occurrences of any marker phrase in the text.

    Multi-word markers are matched as substrings; single tokens are matched on
    word boundaries so "but" does not fire inside "butter".
    """
    total = 0
    for m in markers:
        if " " in m:
            total += text_lower.count(m)
        else:
            total += len(re.findall(r"\b" + re.escape(m) + r"\b", text_lower))
    return total


def _logistic(x: float, scale: float = 2.0) -> float:
    """Map a signed marker balance to (0, 1); 0 -> 0.5."""
    return 1.0 / (1.0 + math.exp(-x / scale))


# --------------------------------------------------------------------------- #
# Marker lexicons (crude, hand-picked — exploratory)
# --------------------------------------------------------------------------- #
_DELIB_POS = [
    "first", "second", "third", "next", "then", "step", "step by step",
    "let's think", "let me think", "because", "therefore", "thus", "reason",
    "consider", "break this down", "work through", "on one hand",
    "on the other hand", "let's reason",
]
_SKEPT_PUSH = [
    "however", "but", "doubt", "question", "questionable", "evidence",
    "verify", "not necessarily", "unsupported", "are you sure", "citation",
    "source", "skeptic", "challenge", "assumption", "proof", "how do you know",
    "that's not clear", "i disagree", "unproven",
]
_SKEPT_AGREE = [
    "absolutely", "of course", "agreed", "definitely", "certainly",
    "you're right", "great point", "happy to", "sure thing", "no problem",
    "as you say", "indeed you are",
]
_UNC_HEDGE = [
    "might", "maybe", "perhaps", "possibly", "i think", "i'm not sure",
    "not sure", "uncertain", "not certain", "could be", "likely", "probably",
    "approximately", "around", "it depends", "hard to say", "seems",
    "i believe", "roughly", "estimate",
]
_UNC_CONFIDENT = [
    "definitely", "certainly", "guaranteed", "without doubt", "clearly",
    "obviously", "always", "never", "undoubtedly", "for sure",
    "100%", "no question", "unquestionably",
]
_FOCUS_TANGENT = [
    "by the way", "additionally", "also worth", "side note", "incidentally",
    "on a related note", "tangent", "furthermore", "moreover", "as an aside",
    "speaking of", "in addition", "it's worth noting", "on a separate note",
]


def deliberation_score(text: str) -> float:
    """Presence of step/reasoning markers + reasoning length (normalized)."""
    tl = text.lower()
    hits = _count_markers(tl, _DELIB_POS)
    n_words = len(_words(text))
    marker_term = min(hits / 6.0, 1.0)
    length_term = min(n_words / 60.0, 1.0)
    return float(0.7 * marker_term + 0.3 * length_term)


def skepticism_score(text: str) -> float:
    """Pushback/doubt/verification markers vs agreement markers."""
    tl = text.lower()
    push = _count_markers(tl, _SKEPT_PUSH)
    agree = _count_markers(tl, _SKEPT_AGREE)
    return _logistic(float(push - agree))


def uncertainty_awareness_score(text: str) -> float:
    """Hedging/uncertainty markers vs confident-assertion markers."""
    tl = text.lower()
    hedge = _count_markers(tl, _UNC_HEDGE)
    confident = _count_markers(tl, _UNC_CONFIDENT)
    return _logistic(float(hedge - confident))


def focus_score(text: str) -> float:
    """On-topic concision proxy: short answer, few tangent markers => focused."""
    tl = text.lower()
    tangents = _count_markers(tl, _FOCUS_TANGENT)
    n_words = len(_words(text))
    length_penalty = min(n_words / 120.0, 1.0)
    tangent_penalty = min(tangents / 3.0, 1.0)
    score = 1.0 - 0.6 * length_penalty - 0.4 * tangent_penalty
    return float(max(0.0, min(1.0, score)))


_PROXIES = {
    "deliberation": deliberation_score,
    "skepticism": skepticism_score,
    "uncertainty_awareness": uncertainty_awareness_score,
    "focus": focus_score,
}


def behavior_score(text: str, axis: str) -> float:
    """Crude automatic behavioral proxy for `axis` on `text`, in [0, 1].

    Higher = more of the axis's positive pole. See module docstring: these are
    EXPLORATORY lexical proxies, not validated instruments.
    """
    if axis not in _PROXIES:
        raise ValueError(f"unknown axis {axis!r}; known axes: {sorted(_PROXIES)}")
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    return _PROXIES[axis](text)


def proxy_markers(axis: str) -> Dict[str, List[str]]:
    """Expose the marker lexicons used for `axis` (for docs / auditing)."""
    if axis == "deliberation":
        return {"positive": list(_DELIB_POS)}
    if axis == "skepticism":
        return {"pushback": list(_SKEPT_PUSH), "agreement": list(_SKEPT_AGREE)}
    if axis == "uncertainty_awareness":
        return {"hedge": list(_UNC_HEDGE), "confident": list(_UNC_CONFIDENT)}
    if axis == "focus":
        return {"tangent": list(_FOCUS_TANGENT)}
    raise ValueError(f"unknown axis {axis!r}")
