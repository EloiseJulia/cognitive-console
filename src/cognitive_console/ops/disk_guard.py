"""Disk-budget guard for the borrowed A800 session (D-0020: total disk < 70 GB).

The human constraint on the borrowed hardware is HARD: keep total disk under a
budget and delete everything after. This helper measures the on-disk footprint of
the paths that grow during a run — primarily ``HF_HOME`` (downloaded model
weights + hub cache) and the ``venv`` — and ABORTS with a clear message BEFORE the
footprint crosses the ceiling, so a runaway download can never blow the borrowed
box's disk.

Pure stdlib. No torch, no network — unit-testable offline against temp dirs.

Budget vs ceiling
-----------------
* ``budget_gb`` (default 60) is the soft target we plan to stay under.
* ``ceiling_gb`` (default 70) is the HARD limit from D-0020. Crossing it raises
  ``DiskBudgetError``. Between budget and ceiling we return a WARNING status so
  the caller can log it and proceed cautiously.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence

_BYTES_PER_GB = 1024.0 ** 3


def gb(n_bytes: float) -> float:
    """Bytes -> gibibytes."""
    return float(n_bytes) / _BYTES_PER_GB


class DiskBudgetError(RuntimeError):
    """Raised when measured disk usage meets/exceeds the hard ceiling."""


def dir_size_bytes(path: str | os.PathLike) -> int:
    """Total size in bytes of all files under `path` (0 if it does not exist).

    Follows the tree with ``os.scandir`` (fast), skips symlinks to avoid double
    counting / cycles, and ignores entries that vanish mid-walk (a cache being
    written concurrently) rather than crashing.
    """
    root = Path(path)
    if not root.exists():
        return 0
    if root.is_file():
        try:
            return root.stat().st_size
        except OSError:
            return 0
    total = 0
    stack: List[str] = [str(root)]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as it:
                for entry in it:
                    try:
                        if entry.is_symlink():
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            stack.append(entry.path)
                        elif entry.is_file(follow_symlinks=False):
                            total += entry.stat(follow_symlinks=False).st_size
                    except OSError:
                        continue
        except OSError:
            continue
    return total


@dataclass
class DiskUsage:
    per_path_gb: Dict[str, float]
    total_gb: float
    budget_gb: float
    ceiling_gb: float
    status: str          # "ok" | "warn" | "over"
    message: str

    @property
    def over_ceiling(self) -> bool:
        return self.status == "over"

    def to_dict(self) -> Dict[str, object]:
        return {
            "per_path_gb": {k: round(v, 3) for k, v in self.per_path_gb.items()},
            "total_gb": round(self.total_gb, 3),
            "budget_gb": self.budget_gb,
            "ceiling_gb": self.ceiling_gb,
            "status": self.status,
            "message": self.message,
        }


def measure_disk(paths: Sequence[str | os.PathLike]) -> Dict[str, float]:
    """Return {path: size_in_gb} for each existing path (deduplicated)."""
    seen = []
    out: Dict[str, float] = {}
    for p in paths:
        if p is None:
            continue
        key = str(Path(p))
        if key in out:
            continue
        seen.append(key)
        out[key] = gb(dir_size_bytes(key))
    return out


def check_disk_budget(
    paths: Sequence[str | os.PathLike],
    budget_gb: float = 60.0,
    ceiling_gb: float = 70.0,
    raise_on_over: bool = True,
) -> DiskUsage:
    """Measure `paths` and check them against the budget / hard ceiling.

    Returns a ``DiskUsage``. If total >= ceiling and ``raise_on_over`` is True,
    raises ``DiskBudgetError`` (the abort-before-exceeding guard). Between budget
    and ceiling the status is "warn"; below budget it is "ok".
    """
    if ceiling_gb < budget_gb:
        raise ValueError("ceiling_gb must be >= budget_gb")
    per_path = measure_disk(paths)
    total = float(sum(per_path.values()))
    breakdown = ", ".join(f"{k}={v:.2f}GB" for k, v in per_path.items()) or "(none)"
    if total >= ceiling_gb:
        status = "over"
        message = (
            f"DISK OVER CEILING: total {total:.2f}GB >= ceiling {ceiling_gb:.0f}GB "
            f"[{breakdown}]. Aborting BEFORE exceeding the borrowed-box budget "
            "(D-0020: total disk must stay < 70GB, delete-after)."
        )
    elif total >= budget_gb:
        status = "warn"
        message = (
            f"DISK WARN: total {total:.2f}GB >= budget {budget_gb:.0f}GB "
            f"(ceiling {ceiling_gb:.0f}GB) [{breakdown}]. Proceed cautiously; do "
            "not download further large models."
        )
    else:
        status = "ok"
        message = (
            f"disk ok: total {total:.2f}GB < budget {budget_gb:.0f}GB "
            f"(ceiling {ceiling_gb:.0f}GB) [{breakdown}]."
        )
    usage = DiskUsage(
        per_path_gb=per_path,
        total_gb=total,
        budget_gb=float(budget_gb),
        ceiling_gb=float(ceiling_gb),
        status=status,
        message=message,
    )
    if status == "over" and raise_on_over:
        raise DiskBudgetError(message)
    return usage


def default_guard_paths(hf_home: Optional[str] = None, venv: Optional[str] = None) -> List[str]:
    """Best-effort default set of paths to guard: HF_HOME + venv.

    Resolves HF_HOME from the arg or the environment (HF_HOME, then
    HUGGINGFACE_HUB_CACHE, then ~/.cache/huggingface). Resolves the venv from the
    arg or the active VIRTUAL_ENV. Missing paths are simply measured as 0.
    """
    paths: List[str] = []
    hf = hf_home or os.environ.get("HF_HOME") or os.environ.get("HUGGINGFACE_HUB_CACHE")
    if not hf:
        hf = str(Path.home() / ".cache" / "huggingface")
    paths.append(hf)
    v = venv or os.environ.get("VIRTUAL_ENV")
    if v:
        paths.append(v)
    return paths
