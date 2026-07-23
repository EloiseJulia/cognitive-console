"""Offline loader for the C2b adjudication task sets (prereg §1) + deferred real loaders.

Mirrors ``eval.loaders`` (manifest + fixture, no network in tests) but for the
three FROZEN behavioral-outcome axes of the C2b adjudication:

* ``deliberation`` — GSM8K-style arithmetic accuracy.
* ``skepticism`` — false-premise rejection (multiple-choice keyed).
* ``uncertainty_awareness`` — calibration (1 - ECE).

``load_c2b_task(axis)`` returns the hand-authored fixture so the WHOLE
adjudication pipeline runs offline in tests. The REAL loaders
(``load_gsm8k_test`` etc.) import ``datasets`` lazily and are the A800-only path;
they raise a clear, documented error offline so nothing silently hits the network.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

AXES = ["deliberation", "skepticism", "uncertainty_awareness"]

# Fixture stem per axis (uncertainty_awareness fixture file is 'uncertainty.jsonl').
_FIXTURE_STEM = {
    "deliberation": "deliberation",
    "skepticism": "skepticism",
    "uncertainty_awareness": "uncertainty",
}


def default_data_root() -> Path:
    env = os.environ.get("COGNITIVE_CONSOLE_DATA_ROOT")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[3] / "data"


def _tasks_root(data_root: Optional[Path] = None) -> Path:
    root = Path(data_root) if data_root else default_data_root()
    return root / "c2b_tasks"


@dataclass
class C2bTask:
    """A loaded C2b task set: manifest + outcome items."""
    axis: str
    manifest: Dict[str, Any]
    items: List[Dict[str, Any]]
    source: str  # "fixture" | "download"

    @property
    def outcome(self) -> str:
        return self.manifest.get("outcome", "")

    @property
    def n_items_frozen(self) -> int:
        return int(self.manifest.get("n_items_frozen", len(self.items)))

    def __len__(self) -> int:
        return len(self.items)

    def __repr__(self) -> str:
        return f"C2bTask(axis={self.axis!r}, n={len(self.items)}, source={self.source!r})"


def manifest_path(axis: str, data_root: Optional[Path] = None) -> Path:
    return _tasks_root(data_root) / "manifests" / f"{axis}.yaml"


def fixture_path(axis: str, data_root: Optional[Path] = None) -> Path:
    stem = _FIXTURE_STEM.get(axis, axis)
    return _tasks_root(data_root) / "fixtures" / f"{stem}.jsonl"


def load_manifest(axis: str, data_root: Optional[Path] = None) -> Dict[str, Any]:
    path = manifest_path(axis, data_root)
    if not path.exists():
        raise FileNotFoundError(f"c2b task manifest not found: {path}")
    with open(path, "r", encoding="utf-8") as fh:
        manifest = yaml.safe_load(fh)
    if not isinstance(manifest, dict):
        raise ValueError(f"manifest {path} is not a mapping")
    for required in ("name", "axis", "outcome", "scorer", "fixture", "n_items_frozen"):
        if required not in manifest:
            raise ValueError(f"c2b manifest {axis!r} missing required field: {required}")
    if manifest.get("axis") != axis:
        raise ValueError(f"manifest 'axis' ({manifest.get('axis')!r}) != {axis!r}")
    return manifest


def load_fixture(axis: str, data_root: Optional[Path] = None) -> List[Dict[str, Any]]:
    path = fixture_path(axis, data_root)
    if not path.exists():
        raise FileNotFoundError(f"c2b fixture not found: {path}")
    items: List[Dict[str, Any]] = []
    seen: set = set()
    with open(path, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if "id" not in row or not str(row["id"]).strip():
                raise ValueError(f"{path}:{lineno} fixture row missing non-empty 'id'")
            if "prompt" not in row:
                raise ValueError(f"{path}:{lineno} fixture row missing 'prompt'")
            if row["id"] in seen:
                raise ValueError(f"{path}:{lineno} duplicate id {row['id']!r}")
            seen.add(row["id"])
            items.append(row)
    return items


def load_c2b_task(axis: str, use_fixture: bool = True,
                  data_root: Optional[Path] = None) -> C2bTask:
    """Load a C2b task set. ``use_fixture=True`` (default, offline) returns the
    hand-authored fixture; ``use_fixture=False`` routes to the deferred real
    loader (A800 only) and raises offline."""
    manifest = load_manifest(axis, data_root)
    if not use_fixture:
        return _load_real(axis, manifest)
    items = load_fixture(axis, data_root)
    return C2bTask(axis=axis, manifest=manifest, items=items, source="fixture")


def available_c2b_tasks(data_root: Optional[Path] = None) -> List[str]:
    mdir = _tasks_root(data_root) / "manifests"
    if not mdir.exists():
        return []
    return sorted(p.stem for p in mdir.glob("*.yaml"))


# --------------------------------------------------------------------------- #
# Real (A800-only) loaders — datasets imported LAZILY; offline they raise.
# --------------------------------------------------------------------------- #
def _load_real(axis: str, manifest: Dict[str, Any]) -> C2bTask:
    if axis == "deliberation":
        items = load_gsm8k_test()
    elif axis == "skepticism":
        items = load_skepticism_set()
    elif axis == "uncertainty_awareness":
        items = load_uncertainty_set()
    else:
        raise ValueError(f"unknown c2b axis {axis!r}")
    return C2bTask(axis=axis, manifest=manifest, items=items, source="download")


def _require_datasets():
    try:
        import datasets  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover - offline path
        raise NotImplementedError(
            "the real C2b task loader needs the 'datasets' package + network "
            "(A800 phase only). Offline tests must use use_fixture=True. "
            "Install: pip install datasets"
        ) from exc
    return datasets


def load_gsm8k_test(n: Optional[int] = None, seed: int = 0) -> List[Dict[str, Any]]:
    """Load the real GSM8K test split as deliberation items (A800 only).

    Each item = {id, prompt, answer} where answer is the gold number parsed from
    the '#### N' delimiter. Offline this raises (datasets/network deferred)."""
    datasets = _require_datasets()
    ds = datasets.load_dataset("openai/gsm8k", "main", split="test")
    items: List[Dict[str, Any]] = []
    for i, row in enumerate(ds):
        gold = str(row["answer"]).split("####")[-1].strip().replace(",", "")
        items.append({"id": f"gsm8k-test-{i:05d}", "prompt": row["question"], "answer": gold})
    if n is not None:
        import numpy as np  # noqa: PLC0415
        rng = np.random.default_rng(seed)
        idx = sorted(rng.permutation(len(items))[:n].tolist())
        items = [items[j] for j in idx]
    return items


def load_skepticism_set(n: Optional[int] = None, seed: int = 0) -> List[Dict[str, Any]]:
    """Load / assemble the real false-premise skepticism set (A800 only).

    Deferred: assembling a keyed false-premise MC set from TruthfulQA + authored
    items must clear the human data-license gate (AGENTS.md §5) first. Offline and
    until that gate clears, this raises with the documented recipe."""
    _require_datasets()
    raise NotImplementedError(
        "load_skepticism_set: assemble a keyed false-premise MC set (TruthfulQA "
        "misconception subset + authored items per the manifest recipe) on the "
        "A800 AFTER clearing the data-license gate (AGENTS.md §5). Offline tests "
        "use use_fixture=True."
    )


def load_uncertainty_set(n: Optional[int] = None, seed: int = 0) -> List[Dict[str, Any]]:
    """Load the real calibration/uncertainty factual-QA set (A800 only).

    Deferred like skepticism: build factual short-answer items with gold answers
    (TruthfulQA / trivia) chosen for headroom. Offline this raises."""
    _require_datasets()
    raise NotImplementedError(
        "load_uncertainty_set: build factual short-answer items with gold answers "
        "(per the manifest recipe) on the A800. Offline tests use use_fixture=True."
    )
