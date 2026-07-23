"""L0 leakage check: eval fixture ids must not overlap contrast-pair ids.

If an eval item's id collided with a contrast-pair id used to extract the steering
vector, we could silently evaluate on the very data used to build the intervention.
This guards the extraction/eval boundary before any GPU run."""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PAIRS_DIR = REPO / "data" / "contrast_pairs"
FIXTURES_DIR = REPO / "data" / "eval_sets" / "fixtures"


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


def test_data_files_exist():
    assert list(PAIRS_DIR.glob("*.jsonl")), "no contrast-pair files found"
    assert list(FIXTURES_DIR.glob("*.jsonl")), "no fixture files found"


def test_no_id_overlap_between_fixtures_and_pairs():
    pair_ids = set(contrast_pair_ids())
    fix_ids = set(fixture_ids())
    overlap = pair_ids & fix_ids
    assert not overlap, f"leakage: ids shared between contrast pairs and eval fixtures: {sorted(overlap)}"


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
