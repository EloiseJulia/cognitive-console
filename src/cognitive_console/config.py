"""Experiment config loading + deterministic config hashing (reproducibility).

Phase-0 analysis runs are config-driven: a YAML file names the axes, candidate
layers, seed, null-baseline sample count, and pre-registered thresholds. To make
a run reconstructable, the config is hashed canonically (sorted-key JSON) so the
same config always yields the same `config_hash`, which is recorded in the
experiment registry alongside the run.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


def config_hash(config: Dict[str, Any]) -> str:
    """Deterministic sha256 over canonical (sorted-key) JSON of the config."""
    canonical = json.dumps(config, sort_keys=True, separators=(",", ":"), default=str)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass
class ExperimentConfig:
    axes: List[str]
    layers: List[int]
    seed: int = 0
    n_null: int = 1000
    max_facade_ratio: float = 0.8
    min_facade_support_fraction: float = 0.5
    no_facade_ratio: float = 0.9
    model: Optional[str] = None
    dataset: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def hash(self) -> str:
        return config_hash(self.to_canonical())

    def to_canonical(self) -> Dict[str, Any]:
        """The exact fields that define the run (excludes derived/raw echo)."""
        return {
            "axes": list(self.axes),
            "layers": list(self.layers),
            "seed": self.seed,
            "n_null": self.n_null,
            "max_facade_ratio": self.max_facade_ratio,
            "min_facade_support_fraction": self.min_facade_support_fraction,
            "no_facade_ratio": self.no_facade_ratio,
            "model": self.model,
            "dataset": self.dataset,
        }


def _require(d: Dict[str, Any], key: str, path: str) -> Any:
    if key not in d:
        raise ValueError(f"config {path}: missing required key {key!r}")
    return d[key]


def load_config(path: str | Path) -> ExperimentConfig:
    """Load and validate an experiment config YAML."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"config not found: {path}")
    with open(path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    if not isinstance(raw, dict):
        raise ValueError(f"config {path} is not a mapping")

    axes = _require(raw, "axes", str(path))
    layers = _require(raw, "layers", str(path))
    if not isinstance(axes, list) or not axes:
        raise ValueError(f"config {path}: 'axes' must be a non-empty list")
    if not isinstance(layers, list) or not layers:
        raise ValueError(f"config {path}: 'layers' must be a non-empty list")

    return ExperimentConfig(
        axes=[str(a) for a in axes],
        layers=[int(x) for x in layers],
        seed=int(raw.get("seed", 0)),
        n_null=int(raw.get("n_null", 1000)),
        max_facade_ratio=float(raw.get("max_facade_ratio", 0.8)),
        min_facade_support_fraction=float(raw.get("min_facade_support_fraction", 0.5)),
        no_facade_ratio=float(raw.get("no_facade_ratio", 0.9)),
        model=raw.get("model"),
        dataset=raw.get("dataset"),
        raw=raw,
    )
