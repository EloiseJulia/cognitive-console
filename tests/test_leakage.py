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
STRONGEST_DIR = REPO / "data" / "strongest_prompts"

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


# --------------------------------------------------------------------------- #
# Strongest-prompt set guards (FIX 2): the separately-authored strong
# instructions that drive the C1 facade measurement must NOT be drawn from the
# contrast-pair distribution used to build the CAA vector. If they overlapped,
# they would trivially project onto û ~= full ||v|| (pseudo-circularity), which
# is exactly the manufactured "overshoot" the prior pilot suffered from.
# --------------------------------------------------------------------------- #
def strongest_axes():
    return sorted(f.stem for f in STRONGEST_DIR.glob("*.jsonl"))


def strongest_texts():
    out = []
    for f in sorted(STRONGEST_DIR.glob("*.jsonl")):
        for row in _jsonl(f):
            out.append(row["text"])
    return out


def _texts_by_axis(root):
    out = {}
    for f in sorted(root.glob("*.jsonl")):
        rows = _jsonl(f)
        if root == PAIRS_DIR:
            out[f.stem] = [row["text"] for row in rows]
        else:
            out[f.stem] = [row["text"] for row in rows]
    return out


def test_strongest_prompt_files_exist_for_every_axis():
    axes = strongest_axes()
    pair_axes = sorted(f.stem for f in PAIRS_DIR.glob("*.jsonl"))
    assert axes, "no strongest-prompt files found"
    # Every axis with contrast pairs must have an authored strongest-prompt set.
    missing = set(pair_axes) - set(axes)
    assert not missing, f"axes without a strongest-prompt set: {sorted(missing)}"


def test_strongest_prompt_sets_have_expected_size_and_schema():
    for f in sorted(STRONGEST_DIR.glob("*.jsonl")):
        rows = _jsonl(f)
        n = len(rows)
        # Expanded set (feature/4, D-0019): 15-20 diverse strong prompts per axis
        # tightens the bootstrap CI. Lower bound guards against silent truncation.
        assert 15 <= n <= 20, f"{f.name}: {n} strongest prompts, expected 15-20"
        ids = set()
        for row in rows:
            assert set(row) == {"axis", "prompt_id", "text"}, f"{f.name}: bad keys {row}"
            assert row["axis"] == f.stem, f"{f.name}: axis mismatch in {row}"
            assert isinstance(row["text"], str) and row["text"].strip()
            assert row["prompt_id"] not in ids, f"{f.name}: dup prompt_id {row['prompt_id']}"
            ids.add(row["prompt_id"])


def test_no_content_overlap_between_strongest_prompts_and_pairs():
    """The strongest-prompt texts must be DIFFERENT IN KIND from the contrast
    pairs (no verbatim reuse, no near-duplicate distinctive phrasing). This is the
    anti-pseudo-circularity guard for the C1 facade measurement."""
    strong_texts = strongest_texts()
    pair_texts = contrast_pair_texts()
    assert strong_texts, "no strongest-prompt texts collected"
    assert pair_texts, "no contrast-pair texts collected"

    strong_norm = {_normalize(t) for t in strong_texts}
    pair_norm = {_normalize(t) for t in pair_texts}

    # (1) No exact normalized-string collision.
    exact = strong_norm & pair_norm
    assert not exact, f"leakage: identical normalized text in strongest prompts and pairs: {sorted(exact)}"

    # (2) No high n-gram overlap (near-duplicate reuse of a distinctive phrase).
    pair_ngrams = set()
    for t in pair_norm:
        pair_ngrams |= _ngrams(t)
    shared = set()
    for t in strong_norm:
        shared |= _ngrams(t) & pair_ngrams
    assert not shared, (
        f"leakage: shared {NGRAM_N}-gram(s) between strongest prompts and contrast pairs: "
        f"{sorted(shared)[:5]}"
    )


def test_refusal_axis_does_not_leak_into_metacognitive_axes():
    pair_by_axis = _texts_by_axis(PAIRS_DIR)
    strong_by_axis = _texts_by_axis(STRONGEST_DIR)
    metacognitive_axes = {"deliberation", "skepticism", "uncertainty_awareness"}
    assert "refusal_positive_control" in pair_by_axis
    assert "refusal_positive_control" in strong_by_axis
    assert metacognitive_axes <= set(pair_by_axis)
    assert metacognitive_axes <= set(strong_by_axis)

    refusal_texts = pair_by_axis["refusal_positive_control"] + strong_by_axis["refusal_positive_control"]
    meta_texts = []
    for axis in sorted(metacognitive_axes):
        meta_texts.extend(pair_by_axis[axis])
        meta_texts.extend(strong_by_axis[axis])

    refusal_norm = {_normalize(t) for t in refusal_texts}
    meta_norm = {_normalize(t) for t in meta_texts}
    exact = refusal_norm & meta_norm
    assert not exact, f"refusal/metacognitive leakage: identical normalized text: {sorted(exact)}"

    meta_ngrams = set()
    for t in meta_norm:
        meta_ngrams |= _ngrams(t)
    shared = set()
    for t in refusal_norm:
        shared |= _ngrams(t) & meta_ngrams
    assert not shared, (
        f"refusal/metacognitive leakage: shared {NGRAM_N}-gram(s): {sorted(shared)[:5]}"
    )
