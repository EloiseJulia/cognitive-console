"""L0 leakage check: eval fixture ids must not overlap contrast-pair ids.

If an eval item's id collided with a contrast-pair id used to extract the steering
vector, we could silently evaluate on the very data used to build the intervention.
This guards the extraction/eval boundary before any GPU run."""

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PAIRS_DIR = REPO / "data" / "contrast_pairs"
FIXTURES_DIR = REPO / "data" / "eval_sets" / "fixtures"

# Fixture fields that carry model-facing prompt text (any that exist per row).
FIXTURE_TEXT_FIELDS = ("prompt", "question", "user_view")
# n-gram width for the near-duplicate content check.
NGRAM_N = 6


def _jsonl(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def contrast_pair_ids():
    ids = []
    for f in sorted(PAIRS_DIR.glob("*.jsonl")):
        for row in _jsonl(f):
            ids.append(row["pair_id"])
    return ids


def fixture_ids():
    ids = []
    for f in sorted(FIXTURES_DIR.glob("*.jsonl")):
        for row in _jsonl(f):
            ids.append(row["id"])
    return ids


def _normalize(text):
    """Lowercase, drop punctuation, collapse whitespace -> canonical form."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def contrast_pair_texts():
    out = []
    for f in sorted(PAIRS_DIR.glob("*.jsonl")):
        for row in _jsonl(f):
            out.append(row["text"])
    return out


def fixture_prompt_texts():
    out = []
    for f in sorted(FIXTURES_DIR.glob("*.jsonl")):
        for row in _jsonl(f):
            for field in FIXTURE_TEXT_FIELDS:
                if field in row and isinstance(row[field], str):
                    out.append(row[field])
    return out


def _ngrams(normalized, n=NGRAM_N):
    toks = normalized.split()
    return {" ".join(toks[i : i + n]) for i in range(0, max(0, len(toks) - n + 1))}


def test_data_files_exist():
    assert list(PAIRS_DIR.glob("*.jsonl")), "no contrast-pair files found"
    assert list(FIXTURES_DIR.glob("*.jsonl")), "no fixture files found"


def test_no_id_overlap_between_fixtures_and_pairs():
    pair_ids = set(contrast_pair_ids())
    fix_ids = set(fixture_ids())
    # Non-vacuous: both id spaces must be populated, else this check proves nothing.
    assert pair_ids, "no contrast-pair ids collected"
    assert fix_ids, "no fixture ids collected"
    overlap = pair_ids & fix_ids
    assert not overlap, f"leakage: ids shared between contrast pairs and eval fixtures: {sorted(overlap)}"


def test_no_content_overlap_between_pairs_and_fixtures():
    """CONTENT-level leakage guard (the id-prefix check alone is vacuous because
    the prefixes are disjoint by construction). If a steering contrast text also
    appeared, verbatim or nearly so, as an eval prompt, we'd be evaluating on the
    very strings used to build the intervention."""
    pair_texts = contrast_pair_texts()
    fix_texts = fixture_prompt_texts()
    # Non-vacuous: fail loudly if either corpus is empty.
    assert pair_texts, "no contrast-pair texts collected"
    assert fix_texts, "no fixture prompt texts collected"

    pair_norm = {_normalize(t) for t in pair_texts}
    fix_norm = {_normalize(t) for t in fix_texts}
    assert pair_norm, "normalized contrast-pair texts are empty"
    assert fix_norm, "normalized fixture prompt texts are empty"

    # (1) No exact normalized-string collision.
    exact = pair_norm & fix_norm
    assert not exact, f"content leakage: identical normalized text in pairs and fixtures: {sorted(exact)}"

    # (2) No high n-gram overlap (near-duplicate reuse of a distinctive phrase).
    fixture_ngrams = set()
    for t in fix_norm:
        fixture_ngrams |= _ngrams(t)
    shared = set()
    for t in pair_norm:
        shared |= _ngrams(t) & fixture_ngrams
    assert not shared, (
        f"content leakage: shared {NGRAM_N}-gram(s) between contrast pairs and eval fixtures: "
        f"{sorted(shared)[:5]}"
    )


def test_fixture_ids_globally_unique():
    ids = fixture_ids()
    assert len(ids) == len(set(ids)), "duplicate fixture ids across eval sets"


def test_each_axis_pairs_have_matched_polarity():
    # For every axis file: each pair_id has exactly one pos and one neg.
    from collections import defaultdict

    for f in sorted(PAIRS_DIR.glob("*.jsonl")):
        by_pair = defaultdict(set)
        for row in _jsonl(f):
            assert set(row) == {"axis", "polarity", "pair_id", "text", "note"}, f"{f.name}: bad keys {row}"
            assert row["polarity"] in {"pos", "neg"}
            by_pair[row["pair_id"]].add(row["polarity"])
        for pid, pols in by_pair.items():
            assert pols == {"pos", "neg"}, f"{f.name}: pair {pid} missing a polarity: {pols}"
        n_pairs = len(by_pair)
        assert 30 <= n_pairs <= 50, f"{f.name}: {n_pairs} pairs, out of the 30-50 spec band"


def test_pair_ids_unique_within_axis_polarity():
    for f in sorted(PAIRS_DIR.glob("*.jsonl")):
        seen = set()
        for row in _jsonl(f):
            key = (row["pair_id"], row["polarity"])
            assert key not in seen, f"{f.name}: duplicate {key}"
            seen.add(key)
