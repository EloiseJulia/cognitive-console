"""Disk-budget guard tests (offline, temp dirs — no torch/network)."""

import os

import pytest

from cognitive_console.ops.disk_guard import (
    DiskBudgetError,
    check_disk_budget,
    dir_size_bytes,
    gb,
    measure_disk,
)

_MB = 1024 * 1024


def _write(path, n_bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(b"\0" * n_bytes)


def test_dir_size_counts_nested_files(tmp_path):
    _write(tmp_path / "a.bin", 3 * _MB)
    _write(tmp_path / "sub" / "b.bin", 2 * _MB)
    assert dir_size_bytes(tmp_path) == 5 * _MB


def test_dir_size_missing_is_zero(tmp_path):
    assert dir_size_bytes(tmp_path / "nope") == 0


def test_check_ok_below_budget(tmp_path):
    _write(tmp_path / "hf" / "w.bin", 4 * _MB)
    usage = check_disk_budget([tmp_path / "hf"], budget_gb=1.0, ceiling_gb=2.0)
    assert usage.status == "ok"
    assert not usage.over_ceiling


def test_check_warn_between_budget_and_ceiling(tmp_path):
    # 1.5 "GB" simulated by tiny budget/ceiling in GB with a small file: use gb math.
    _write(tmp_path / "hf" / "w.bin", 6 * _MB)
    budget = gb(4 * _MB)
    ceiling = gb(10 * _MB)
    usage = check_disk_budget([tmp_path / "hf"], budget_gb=budget, ceiling_gb=ceiling)
    assert usage.status == "warn"


def test_check_over_ceiling_raises(tmp_path):
    _write(tmp_path / "hf" / "w.bin", 12 * _MB)
    ceiling = gb(10 * _MB)
    with pytest.raises(DiskBudgetError):
        check_disk_budget([tmp_path / "hf"], budget_gb=gb(1 * _MB), ceiling_gb=ceiling)


def test_check_over_ceiling_no_raise_returns_over(tmp_path):
    _write(tmp_path / "hf" / "w.bin", 12 * _MB)
    ceiling = gb(10 * _MB)
    usage = check_disk_budget(
        [tmp_path / "hf"], budget_gb=gb(1 * _MB), ceiling_gb=ceiling, raise_on_over=False
    )
    assert usage.status == "over"
    assert usage.over_ceiling


def test_ceiling_below_budget_rejected(tmp_path):
    with pytest.raises(ValueError):
        check_disk_budget([tmp_path], budget_gb=70.0, ceiling_gb=60.0)


def test_measure_dedups_paths(tmp_path):
    _write(tmp_path / "w.bin", 2 * _MB)
    m = measure_disk([tmp_path, tmp_path])
    assert len(m) == 1
