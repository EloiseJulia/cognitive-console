"""Tests for the offline eval-set loader (manifest + fixture, no network)."""

from pathlib import Path

import pytest

from cognitive_console.eval import loaders

REPO = Path(__file__).resolve().parent.parent
DATA_ROOT = REPO / "data"

EXPECTED = {"gsm8k", "truthfulqa", "sycophancy_probe", "format_constraints"}


def test_available_eval_sets():
    got = set(loaders.available_eval_sets(DATA_ROOT))
    assert got == EXPECTED


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_load_fixture_items(name):
    es = loaders.load_items(name, use_fixture=True, data_root=DATA_ROOT)
    assert es.source == "fixture"
    assert 5 <= len(es) <= 10, f"{name}: fixture should have 5-10 items, has {len(es)}"
    # answer_field, if declared, present on every item (validated by loader too).
    if es.answer_field:
        for item in es.items:
            assert es.answer_field in item


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_manifest_declares_support_mapping(name):
    m = loaders.load_manifest(name, DATA_ROOT)
    supports = m["supports"]
    assert supports.get("claims"), f"{name}: manifest must map to at least one claim"
    assert supports.get("axes"), f"{name}: manifest must map to at least one axis"
    assert m.get("license"), f"{name}: manifest must state a license"
    assert m.get("download_status") == "deferred"


def test_real_download_is_deferred():
    with pytest.raises(NotImplementedError):
        loaders.load_items("gsm8k", use_fixture=False, data_root=DATA_ROOT)


def test_missing_manifest_raises():
    with pytest.raises(FileNotFoundError):
        loaders.load_manifest("no_such_set", DATA_ROOT)
