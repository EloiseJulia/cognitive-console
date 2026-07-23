"""Eval-set loader stub (S3) — reads a manifest + hand-written fixture OFFLINE.

Phase 0 is data-level only: NO dataset downloads. Each eval set is described by a
YAML manifest under data/eval_sets/manifests/ and shipped with a tiny fixture
(5-10 items) under data/eval_sets/fixtures/ so the pipeline can be unit-tested
without network. The REAL download (HuggingFace / assembled sources) is deferred
to the GPU phase; `load_items(..., use_fixture=False)` deliberately raises until
then, so nothing silently hits the network in Phase 0.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


def default_data_root() -> Path:
    """Repo `data/` dir. Under the src layout this file is
    src/cognitive_console/eval/loaders.py, so the repo root is parents[3].
    Overridable via the COGNITIVE_CONSOLE_DATA_ROOT env var."""
    env = os.environ.get("COGNITIVE_CONSOLE_DATA_ROOT")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[3] / "data"


class EvalSet:
    """A loaded eval set: its manifest plus (fixture or real) items."""

    def __init__(self, name: str, manifest: Dict[str, Any], items: List[Dict[str, Any]], source: str):
        self.name = name
        self.manifest = manifest
        self.items = items
        self.source = source  # "fixture" | "download"

    @property
    def answer_field(self) -> Optional[str]:
        return self.manifest.get("answer_field")

    def __len__(self) -> int:
        return len(self.items)

    def __repr__(self) -> str:
        return f"EvalSet(name={self.name!r}, n={len(self.items)}, source={self.source!r})"


def manifest_path(name: str, data_root: Optional[Path] = None) -> Path:
    root = Path(data_root) if data_root else default_data_root()
    return root / "eval_sets" / "manifests" / f"{name}.yaml"


def fixture_path(name: str, data_root: Optional[Path] = None) -> Path:
    root = Path(data_root) if data_root else default_data_root()
    return root / "eval_sets" / "fixtures" / f"{name}.jsonl"


def load_manifest(name: str, data_root: Optional[Path] = None) -> Dict[str, Any]:
    path = manifest_path(name, data_root)
    if not path.exists():
        raise FileNotFoundError(f"manifest not found: {path}")
    with open(path, "r", encoding="utf-8") as fh:
        manifest = yaml.safe_load(fh)
    if not isinstance(manifest, dict):
        raise ValueError(f"manifest {path} is not a mapping")
    for required in ("name", "metric", "supports", "fixture"):
        if required not in manifest:
            raise ValueError(f"manifest {name!r} missing required field: {required}")
    if manifest.get("name") != name:
        raise ValueError(f"manifest 'name' ({manifest.get('name')!r}) != file stem ({name!r})")
    return manifest


def load_fixture(name: str, data_root: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Read the fixture JSONL. Skips blank lines; validates each row has an 'id'."""
    path = fixture_path(name, data_root)
    if not path.exists():
        raise FileNotFoundError(f"fixture not found: {path}")
    items: List[Dict[str, Any]] = []
    seen_ids: set = set()
    with open(path, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if "id" not in row or not str(row["id"]).strip():
                raise ValueError(f"{path}:{lineno} fixture row missing non-empty 'id'")
            if row["id"] in seen_ids:
                raise ValueError(f"{path}:{lineno} duplicate fixture id {row['id']!r}")
            seen_ids.add(row["id"])
            items.append(row)
    return items


def load_items(
    name: str,
    use_fixture: bool = True,
    data_root: Optional[Path] = None,
) -> EvalSet:
    """Load an eval set. With use_fixture=True (default) returns the hand-written
    fixture, validated against the manifest's answer_field. With use_fixture=False
    raises NotImplementedError — the real download is a GPU-phase task and must not
    run during Phase 0 prep."""
    manifest = load_manifest(name, data_root)
    if not use_fixture:
        raise NotImplementedError(
            f"real download for {name!r} is deferred to the GPU phase "
            f"(manifest download_status={manifest.get('download_status')!r}); "
            "Phase 0 prep is offline — use use_fixture=True"
        )
    items = load_fixture(name, data_root)
    answer_field = manifest.get("answer_field")
    if answer_field:
        for row in items:
            if answer_field not in row:
                raise ValueError(
                    f"fixture {name!r} row {row.get('id')!r} lacks the manifest "
                    f"answer_field {answer_field!r}"
                )
    return EvalSet(name=name, manifest=manifest, items=items, source="fixture")


def available_eval_sets(data_root: Optional[Path] = None) -> List[str]:
    root = Path(data_root) if data_root else default_data_root()
    mdir = root / "eval_sets" / "manifests"
    if not mdir.exists():
        return []
    return sorted(p.stem for p in mdir.glob("*.yaml"))
