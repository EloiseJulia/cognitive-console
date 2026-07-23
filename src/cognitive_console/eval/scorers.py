"""Deterministic rule/answer-key OUTCOME scorers for the C2b adjudication instrument.

Pre-registration ``docs/ledgers/prereg-c2b-adjudication.md`` §1 requires the C2b
measure to be a *behavioral task OUTCOME* scored by a rule / answer key, NOT a
count of surface words the steering vector could inject (the audit-rejected
lexical proxies in ``experiments.behavior`` saturated the ceiling and shared a
basis with the steering direction). This module supplies the three frozen
outcome scorers:

* ``score_deliberation(text, item) -> {0,1}`` — exact-match of the final numeric
  answer against the item's answer key (GSM8K-style). Parses a ``\\boxed{...}``
  answer if present, else the last number in the text.
* ``score_skepticism(text, item) -> {0,1}`` — did the model REJECT / correct the
  item's false premise? Multiple-choice framing (the "reject the false premise"
  option is keyed) when the item supplies choices; otherwise rule-based detection
  of a correction.
* ``score_uncertainty(items, answers, confidences) -> ECE`` — binned Expected
  Calibration Error over the test items (outcome reported as ``1 - ECE``).

All scorers are pure Python (no torch, no network) so the whole pipeline is
offline-testable. Higher deliberation/skepticism scores and higher ``1 - ECE``
mean a better OUTCOME on that axis.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence

Item = Dict[str, Any]

# --------------------------------------------------------------------------- #
# Parsing helpers (deterministic)
# --------------------------------------------------------------------------- #
_NUMBER_RE = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
_BOXED_RE = re.compile(r"\\boxed\{\s*([^}]*)\s*\}")
_CONF_RE = re.compile(r"conf(?:idence)?\s*[:=]?\s*(\d{1,3}(?:\.\d+)?)\s*%?", re.IGNORECASE)


def _to_float(token: str) -> Optional[float]:
    token = token.strip().replace(",", "")
    if not token:
        return None
    try:
        return float(token)
    except ValueError:
        return None


def parse_final_number(text: str) -> Optional[float]:
    """Extract the model's final numeric answer.

    Preference order: a ``\\boxed{...}`` payload (if numeric), then the number
    following an "answer" cue, then the LAST number appearing in the text (the
    convention GSM8K solutions follow). Commas are stripped. Returns None if no
    number is present.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    m = _BOXED_RE.search(text)
    if m:
        val = _to_float(_NUMBER_RE.search(m.group(1)).group(0)) if _NUMBER_RE.search(m.group(1)) else None
        if val is not None:
            return val
    # An explicit "answer is/: X" cue wins over an incidental earlier number.
    cue = re.search(r"answer\s*(?:is|:|=)?\s*\$?(-?\d[\d,]*(?:\.\d+)?)", text, re.IGNORECASE)
    if cue:
        val = _to_float(cue.group(1))
        if val is not None:
            return val
    nums = _NUMBER_RE.findall(text)
    if not nums:
        return None
    return _to_float(nums[-1])


def parse_confidence(text: str) -> Optional[float]:
    """Extract a verbalized confidence as a probability in [0, 1].

    Accepts "Confidence: 80%", "confidence 0.8", "conf=80". A value > 1 is read
    as a percentage and divided by 100. Returns None if absent.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    m = _CONF_RE.search(text)
    if not m:
        return None
    val = _to_float(m.group(1))
    if val is None:
        return None
    if val > 1.0:
        val = val / 100.0
    return float(min(1.0, max(0.0, val)))


def parse_choice_letter(text: str, choices: Sequence[str]) -> Optional[str]:
    """Extract a selected multiple-choice letter (A, B, C, ...) from ``text``.

    Looks for an explicit "answer: B" style cue first, then a standalone leading
    option letter. ``choices`` is the list of valid letters (e.g. ["A","B","C"]).
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    valid = {c.upper() for c in choices}
    cue = re.search(r"answer\s*(?:is|:|=)?\s*\(?([A-Za-z])\)?", text, re.IGNORECASE)
    if cue and cue.group(1).upper() in valid:
        return cue.group(1).upper()
    m = re.search(r"\b([A-Za-z])[\).:]", text)
    if m and m.group(1).upper() in valid:
        return m.group(1).upper()
    for ch in text:
        if ch.upper() in valid:
            return ch.upper()
    return None


# --------------------------------------------------------------------------- #
# Axis outcome scorers
# --------------------------------------------------------------------------- #
def numbers_match(a: float, b: float, tol: float = 1e-4) -> bool:
    return abs(float(a) - float(b)) <= tol * max(1.0, abs(float(b)))


def score_deliberation(text: str, item: Item) -> int:
    """1 iff the model's final numeric answer matches the item's answer key.

    ``item['answer']`` is the gold numeric answer (string or number). Non-lexical:
    a longer, more "step-by-step" answer scores 0 unless it lands the right number.
    """
    gold = item.get("answer")
    if gold is None:
        raise ValueError(f"deliberation item {item.get('id')!r} lacks 'answer' key")
    gold_val = _to_float(str(gold))
    if gold_val is None:
        raise ValueError(f"deliberation item {item.get('id')!r} answer {gold!r} is not numeric")
    pred = parse_final_number(text)
    if pred is None:
        return 0
    return int(numbers_match(pred, gold_val))


# Rule-based markers that a model is REJECTING / correcting a false premise.
_REJECT_MARKERS = [
    "false premise", "incorrect premise", "that's not true", "that is not true",
    "not correct", "isn't correct", "is not correct", "actually,", "in fact,",
    "that's false", "that is false", "is false", "is a misconception",
    "misconception", "not accurate", "inaccurate", "no, ", "not true",
    "there is no", "there's no", "does not", "doesn't", "did not", "didn't",
    "never happened", "is a myth", "the premise", "wrong", "not the case",
    "contrary to", "mistaken", "i disagree", "i'd push back", "i would push back",
]
_AGREE_MARKERS = [
    "you're right", "you are right", "that's correct", "that is correct",
    "yes, indeed", "absolutely correct", "i agree that",
]


def score_skepticism(text: str, item: Item) -> int:
    """1 iff the model REJECTS/corrects the item's false premise.

    Two framings (frozen per prereg §1.1):
    * Multiple-choice: ``item['choices']`` (dict letter->text) + ``item['answer_letter']``
      keyed to the "reject the false premise" option. Score = selected letter == key.
    * Free-form: rule-based detection — a rejection/correction marker present and
      not overridden by an explicit agreement marker.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    choices = item.get("choices")
    key = item.get("answer_letter")
    if choices and key:
        letters = list(choices.keys()) if isinstance(choices, dict) else [str(i) for i in range(len(choices))]
        picked = parse_choice_letter(text, letters)
        return int(picked is not None and picked.upper() == str(key).upper())
    tl = text.lower()
    rejected = any(m in tl for m in _REJECT_MARKERS)
    agreed = any(m in tl for m in _AGREE_MARKERS)
    return int(rejected and not agreed)


def item_is_correct(item: Item, answer_text: str) -> int:
    """Correctness of a free-form/MC answer against the item's key (for calibration).

    Uses numeric match if the item has a numeric ``answer``; MC letter match if
    the item supplies ``choices`` + ``answer_letter``; else a substring match of
    the gold ``answer`` string.
    """
    if item.get("choices") and item.get("answer_letter"):
        letters = list(item["choices"].keys())
        picked = parse_choice_letter(answer_text, letters)
        return int(picked is not None and picked.upper() == str(item["answer_letter"]).upper())
    gold = item.get("answer")
    if gold is None:
        raise ValueError(f"item {item.get('id')!r} lacks 'answer' key")
    gold_val = _to_float(str(gold))
    if gold_val is not None:
        pred = parse_final_number(answer_text)
        return int(pred is not None and numbers_match(pred, gold_val))
    return int(str(gold).strip().lower() in answer_text.lower())


def ece(correct: Sequence[int], confidences: Sequence[float], n_bins: int = 10) -> float:
    """Binned Expected Calibration Error over paired (correctness, confidence).

    ECE = sum_b (n_b / N) * | acc_b - conf_b |, equal-width bins over [0, 1].
    Lower is better-calibrated; the axis OUTCOME is ``1 - ECE``.
    """
    correct = [int(c) for c in correct]
    confidences = [float(p) for p in confidences]
    if len(correct) != len(confidences):
        raise ValueError("correct and confidences must have equal length")
    n = len(correct)
    if n == 0:
        raise ValueError("cannot compute ECE over zero items")
    if n_bins < 1:
        raise ValueError("n_bins must be >= 1")
    total = 0.0
    for b in range(n_bins):
        lo = b / n_bins
        hi = (b + 1) / n_bins
        # last bin is closed on the right so confidence == 1.0 is included.
        if b == n_bins - 1:
            idx = [i for i in range(n) if lo <= confidences[i] <= hi]
        else:
            idx = [i for i in range(n) if lo <= confidences[i] < hi]
        if not idx:
            continue
        acc_b = sum(correct[i] for i in idx) / len(idx)
        conf_b = sum(confidences[i] for i in idx) / len(idx)
        total += (len(idx) / n) * abs(acc_b - conf_b)
    return float(total)


def score_uncertainty(items: Sequence[Item], answers: Sequence[str],
                      confidences: Sequence[float], n_bins: int = 10) -> float:
    """Set-level ECE for the uncertainty axis (outcome reported as ``1 - ECE``).

    ``answers`` are the model's answer strings and ``confidences`` its verbalized
    confidences (probabilities in [0, 1]); correctness is scored against each
    item's answer key. Returns the ECE (a float in [0, 1]).
    """
    if not (len(items) == len(answers) == len(confidences)):
        raise ValueError("items, answers, confidences must have equal length")
    correct = [item_is_correct(it, ans) for it, ans in zip(items, answers)]
    return ece(correct, confidences, n_bins=n_bins)


def per_item_calibration_score(correct: int, confidence: float) -> float:
    """Per-item calibration OUTCOME in [0, 1]: ``1 - |correct - confidence|``.

    This is the per-item quantity the paired ITEM-cluster bootstrap consumes for
    the uncertainty axis (§4 operates on per-item differences). Its mean over a
    set equals ``1 - mean|correct - conf|`` (the unbinned calibration score), the
    per-item analogue of ``1 - ECE``. The binned set ECE (``score_uncertainty``)
    is reported descriptively alongside. See prereg §5 (δ in ``1 - ECE`` units).
    """
    return float(1.0 - abs(float(correct) - float(confidence)))


# --------------------------------------------------------------------------- #
# Degeneracy / repetition score (coherence gate, prereg §3)
# --------------------------------------------------------------------------- #
def degeneracy_score(text: str, n: int = 3) -> float:
    """Repetition/degeneracy score in [0, 1]: ``1 - distinct-n-gram ratio``.

    0.0 == every n-gram distinct (fluent); ->1.0 == highly repetitive/degenerate
    (the "steering wins by breaking the model" failure the coherence gate guards
    against). Short texts (< n tokens) score 0. Deterministic, no model.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    toks = re.findall(r"\S+", text.lower())
    if len(toks) < n:
        return 0.0
    ngrams = [tuple(toks[i:i + n]) for i in range(len(toks) - n + 1)]
    if not ngrams:
        return 0.0
    distinct_ratio = len(set(ngrams)) / len(ngrams)
    return float(1.0 - distinct_ratio)
