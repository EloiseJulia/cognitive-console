"""Experiment-registry writer (AI-Instruction Part I §8.1).

Append-only, identity-guarded log of experiment runs. The record schema mirrors
docs/ledgers/experiment-registry.yaml exactly. Every run — including failed,
cancelled, or invalidated ones — must get a UNIQUE experiment_id. The writer
REFUSES to silently overwrite an existing experiment_id (identity + atomicity
guard) so two differently-configured runs can never collide into one row.

Pure stdlib + pyyaml. No network, no model loading.
"""

from __future__ import annotations

import errno
import os
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

import yaml

# The canonical field order, matching docs/ledgers/experiment-registry.yaml.
REGISTRY_FIELDS = [
    "experiment_id",
    "parent",
    "hypothesis_id",
    "claim_ids",
    "type",
    "status",
    "code_commit",
    "dirty_tree",
    "data_hash",
    "env_hash",
    "config_hash",
    "model",
    "dataset",
    "seed",
    "hardware",
    "started_at",
    "ended_at",
    "exit_code",
    "raw_metrics",
    "summary_metrics",
    "artifacts",
    "failure_reason",
    "valid_for_paper",
    "validation_notes",
]

_VALID_TYPES = {"confirmatory", "exploratory", "diagnostic"}
_VALID_STATUS = {"planned", "running", "done", "failed", "cancelled", "invalidated"}


@dataclass
class ExperimentRecord:
    """One experiment-registry row. Field names/order match the ledger schema."""

    experiment_id: str
    hypothesis_id: Optional[str] = None
    claim_ids: List[str] = field(default_factory=list)
    type: str = "exploratory"
    status: str = "planned"
    parent: Optional[str] = None
    code_commit: Optional[str] = None
    dirty_tree: Optional[bool] = None
    data_hash: Optional[str] = None
    env_hash: Optional[str] = None
    config_hash: Optional[str] = None
    model: Optional[str] = None
    dataset: Optional[str] = None
    seed: Optional[int] = None
    hardware: Optional[str] = None
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    exit_code: Optional[int] = None
    raw_metrics: Optional[Dict[str, Any]] = None
    summary_metrics: Optional[Dict[str, Any]] = None
    artifacts: List[str] = field(default_factory=list)
    failure_reason: Optional[str] = None
    valid_for_paper: bool = False
    validation_notes: Optional[str] = None

    def __post_init__(self):
        if not self.experiment_id or not str(self.experiment_id).strip():
            raise ValueError("experiment_id is required and must be non-empty")
        if self.type not in _VALID_TYPES:
            raise ValueError(f"type must be one of {sorted(_VALID_TYPES)}, got {self.type!r}")
        if self.status not in _VALID_STATUS:
            raise ValueError(f"status must be one of {sorted(_VALID_STATUS)}, got {self.status!r}")

    def to_ordered_dict(self) -> Dict[str, Any]:
        raw = asdict(self)
        return {k: raw[k] for k in REGISTRY_FIELDS}


class ExperimentExistsError(KeyError):
    """Raised when appending an experiment_id that already exists."""


class RegistryLockTimeout(TimeoutError):
    """Raised when the cross-process registry lock cannot be acquired in time."""


@contextmanager
def _file_lock(target_path: str, timeout: float = 30.0, poll: float = 0.02):
    """Cross-process advisory lock via an O_CREAT|O_EXCL `.lock` sidecar.

    Only one holder can create the sidecar at a time; others spin with backoff
    until it is released (removed) or `timeout` elapses. This serializes the
    load -> check-existing -> append -> atomic_write critical section so two
    parallel appenders can never both read a stale file and clobber each other's
    row (the TOCTOU race that silently dropped runs). Portable across Windows and
    POSIX because it relies only on O_EXCL create semantics, not fcntl/msvcrt.
    """
    lock_path = os.path.abspath(target_path) + ".lock"
    os.makedirs(os.path.dirname(lock_path), exist_ok=True)
    deadline = time.monotonic() + timeout
    fd = None
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise RegistryLockTimeout(
                    f"could not acquire registry lock {lock_path!r} within {timeout}s"
                )
            time.sleep(poll)
        except OSError as exc:  # pragma: no cover - platform-specific fallbacks
            if exc.errno == errno.EEXIST:
                if time.monotonic() >= deadline:
                    raise RegistryLockTimeout(
                        f"could not acquire registry lock {lock_path!r} within {timeout}s"
                    )
                time.sleep(poll)
            else:
                raise
    try:
        os.write(fd, str(os.getpid()).encode("ascii"))
        yield
    finally:
        os.close(fd)
        try:
            os.remove(lock_path)
        except FileNotFoundError:
            pass


def _load(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {"experiments": []}
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if data is None:
        return {"experiments": []}
    if not isinstance(data, dict) or "experiments" not in data:
        raise ValueError(f"{path} is not a valid registry (missing 'experiments' key)")
    if data["experiments"] is None:
        data["experiments"] = []
    if not isinstance(data["experiments"], list):
        raise ValueError(f"{path}: 'experiments' must be a list")
    return data


def _atomic_write(path: str, data: Dict[str, Any]) -> None:
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=True, default_flow_style=False)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


class ExperimentRegistry:
    """Append-only registry backed by a YAML file (`experiments:` list)."""

    def __init__(self, path: str):
        self.path = path

    def load(self) -> List[Dict[str, Any]]:
        return _load(self.path)["experiments"]

    def ids(self) -> List[str]:
        return [r.get("experiment_id") for r in self.load()]

    def get(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        for rec in self.load():
            if rec.get("experiment_id") == experiment_id:
                return rec
        return None

    def append(self, record: ExperimentRecord) -> Dict[str, Any]:
        """Append a record. Refuses to overwrite an existing experiment_id.

        The load -> check -> write sequence is serialized by a cross-process
        lock so concurrent appenders cannot both read a stale file and drop a
        row (TOCTOU). Each appender re-loads the freshest file inside the lock.
        """
        return self.append_minted(lambda _ids: record)

    def append_minted(self, minter) -> Dict[str, Any]:
        """Mint AND append a record atomically under the registry lock.

        `minter(existing_ids)` receives the current experiment_ids (read INSIDE
        the lock) and returns the `ExperimentRecord` to append. Doing the mint
        inside the lock closes the race where an id is chosen against a stale,
        outside-lock read: two parallel same-prefix+config runs would otherwise
        pick the same NNNN (and, on Windows, a concurrent read could even collide
        with the atomic replace). Still refuses to overwrite an existing id.
        """
        with _file_lock(self.path):
            data = _load(self.path)
            existing = {r.get("experiment_id") for r in data["experiments"]}
            record = minter([r.get("experiment_id") for r in data["experiments"]])
            if record.experiment_id in existing:
                raise ExperimentExistsError(
                    f"experiment_id {record.experiment_id!r} already exists; "
                    "registry is append-only and will not silently overwrite"
                )
            row = record.to_ordered_dict()
            data["experiments"].append(row)
            _atomic_write(self.path, data)
            return row

    def update_status(
        self,
        experiment_id: str,
        status: str,
        **updates: Any,
    ) -> Dict[str, Any]:
        """Update mutable end-of-run fields on an existing row (status, ended_at,
        exit_code, metrics, ...). Does NOT create rows and errors if the id is
        unknown — status transitions must target a registered experiment."""
        if status not in _VALID_STATUS:
            raise ValueError(f"status must be one of {sorted(_VALID_STATUS)}, got {status!r}")
        with _file_lock(self.path):
            data = _load(self.path)
            for rec in data["experiments"]:
                if rec.get("experiment_id") == experiment_id:
                    rec["status"] = status
                    for key, val in updates.items():
                        if key not in REGISTRY_FIELDS:
                            raise ValueError(f"unknown registry field: {key}")
                        rec[key] = val
                    _atomic_write(self.path, data)
                    return rec
            raise KeyError(f"experiment_id {experiment_id!r} not found")
