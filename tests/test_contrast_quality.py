"""B1 guard: contrast pairs must be LENGTH-MATCHED minimal contrasts.

Rationale (why this test exists)
--------------------------------
A CAA / RepE steering vector is (roughly) the mean difference of activations
between the pos and neg members of each contrast pair. If, within every pair,
polarity is perfectly rank-correlated with text length (pos always longer, or
pos always shorter), then the mean-difference direction is dominated by a
length / verbosity signal rather than the intended cognitive axis. That would
silently destroy the validity of the C1 "semantic facade" measurement: we'd be
projecting onto a "verbosity" direction and calling it "deliberation".

So this test fails if the pos/neg length relationship is one-sided, or if the
typical within-pair length gap is large relative to the texts themselves.

Token definition
----------------
"Tokens" here are whitespace-delimited words (`str.split()`). This is a coarse
but model-agnostic proxy for length; it needs no tokenizer and is deterministic.

Thresholds (documented, so drift is intentional not accidental)
---------------------------------------------------------------
* POS_LONGER_FRACTION must lie strictly inside (POS_FRAC_LO, POS_FRAC_HI) =
  (0.25, 0.75). A value of 0.0 or 1.0 means length is a perfect proxy for
  polarity — exactly the confound we are guarding against. We keep a wide band
  so natural variation is fine; only a *systematic* skew fails.
* MAX_MEAN_ABS_TOKEN_DIFF = 2.0 tokens. Each axis's mean over pairs of
  |len(pos) - len(neg)| must be <= this. With ~15-19 tokens/text this is a
  ~10-13% gap ceiling, i.e. "small relative to text length" per the spec.

How this test would catch the OLD (defective) data
--------------------------------------------------
The pre-fix pairs were length-confounded: deliberation/skepticism/uncertainty
had pos ALWAYS longer than neg (pos-longer-fraction == 1.0) and focus had pos
ALWAYS shorter (fraction == 0.0). Both violate the (0.25, 0.75) band, so
check (a) below would fail for every axis. Additionally the old focus/
deliberation pairs paired a one-line answer (e.g. "Ship it.") against a long
multi-clause completion, so the mean absolute token gap was many tokens —
check (b) would also fail. (Verified conceptually; do not commit defective data
just to see red.)
"""

import json
from collections import defaultdict
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
PAIRS_DIR = REPO / "data" / "contrast_pairs"

POS_FRAC_LO = 0.25
POS_FRAC_HI = 0.75
MAX_MEAN_ABS_TOKEN_DIFF = 2.0


def _jsonl(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _tok(text):
    return len(text.split())


def _axis_files():
    files = sorted(PAIRS_DIR.glob("*.jsonl"))
    assert files, "no contrast-pair files found"
    return files


def _pairs(path):
    """Return {pair_id: {'pos': text, 'neg': text}} for one axis file."""
    by_pair = defaultdict(dict)
    for row in _jsonl(path):
        by_pair[row["pair_id"]][row["polarity"]] = row["text"]
    return by_pair


@pytest.mark.parametrize("path", _axis_files(), ids=lambda p: p.stem)
def test_pair_polarity_complete(path):
    # (c) every pair_id has exactly one pos and exactly one neg.
    counts = defaultdict(list)
    for row in _jsonl(path):
        counts[row["pair_id"]].append(row["polarity"])
    for pid, pols in counts.items():
        assert sorted(pols) == ["neg", "pos"], f"{path.name}: pair {pid} has polarities {sorted(pols)}"


@pytest.mark.parametrize("path", _axis_files(), ids=lambda p: p.stem)
def test_pos_longer_fraction_not_one_sided(path):
    # (a) polarity must NOT be a one-sided proxy for length.
    pairs = _pairs(path)
    n = len(pairs)
    assert n > 0, f"{path.name}: no pairs"
    pos_longer = sum(1 for p in pairs.values() if _tok(p["pos"]) > _tok(p["neg"]))
    frac = pos_longer / n
    assert POS_FRAC_LO < frac < POS_FRAC_HI, (
        f"{path.name}: pos-longer fraction {frac:.3f} outside ({POS_FRAC_LO}, {POS_FRAC_HI}); "
        "length is acting as a proxy for polarity (verbosity confound)"
    )


@pytest.mark.parametrize("path", _axis_files(), ids=lambda p: p.stem)
def test_mean_abs_length_gap_small(path):
    # (b) typical within-pair length gap must be small.
    pairs = _pairs(path)
    n = len(pairs)
    mad = sum(abs(_tok(p["pos"]) - _tok(p["neg"])) for p in pairs.values()) / n
    assert mad <= MAX_MEAN_ABS_TOKEN_DIFF, (
        f"{path.name}: mean |len(pos)-len(neg)| = {mad:.3f} tokens exceeds "
        f"{MAX_MEAN_ABS_TOKEN_DIFF}; pairs are not length-matched"
    )


def test_no_duplicate_texts_across_all_pairs():
    # (d) no duplicate `text` values anywhere in the contrast-pair corpus.
    texts = []
    for path in _axis_files():
        texts.extend(row["text"] for row in _jsonl(path))
    dups = {t for t in texts if texts.count(t) > 1}
    assert not dups, f"duplicate contrast-pair texts: {sorted(dups)}"


@pytest.mark.parametrize("path", _axis_files(), ids=lambda p: p.stem)
def test_pair_count_in_spec_band(path):
    # Spec AC1: 30-50 validated pairs per axis.
    n = len(_pairs(path))
    assert 30 <= n <= 50, f"{path.name}: {n} pairs, outside the 30-50 spec band"
