"""Artifact-lineage manifest writer (AI-Instruction Part I §8.3).

Every reported table/figure must carry a manifest so it can be reconstructed
from a committed script + fixed experiment_ids — no hand-copied numbers, no
manual edits, no reading of a "latest" directory. This writer produces that
manifest and refuses `manual_edits_allowed=True` (the whole point is that the
artifact is script-generated).

The schema mirrors §8.3: artifact_id, paper_location, supports_claims,
source_experiments, aggregation_script (+ commit), raw_data_hash, output_file,
manual_edits_allowed=false, last_verified, verdict.
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

import yaml

MANIFEST_FIELDS = [
    "artifact_id",
    "paper_location",
    "supports_claims",
    "source_experiments",
    "aggregation_script",
    "aggregation_commit",
    "raw_data_hash",
    "output_file",
    "manual_edits_allowed",
    "last_verified",
    "verdict",
]

_VALID_VERDICTS = {"pending", "verified", "stale", "rejected"}


@dataclass
class ArtifactManifest:
    artifact_id: str
    supports_claims: List[str]
    source_experiments: List[str]
    aggregation_script: str
    output_file: str
    paper_location: Optional[str] = None
    aggregation_commit: Optional[str] = None
    raw_data_hash: Optional[str] = None
    manual_edits_allowed: bool = False
    last_verified: Optional[str] = None
    verdict: str = "pending"

    def __post_init__(self):
        if not self.artifact_id or not str(self.artifact_id).strip():
            raise ValueError("artifact_id is required and must be non-empty")
        if self.manual_edits_allowed:
            raise ValueError(
                "manual_edits_allowed must be False — artifacts are script-generated "
                "(no hand-editing numbers into tables/figures, §8.3)"
            )
        if not self.source_experiments:
            raise ValueError(
                "source_experiments must be non-empty — an artifact with no lineage "
                "back to a registered experiment is not reconstructable"
            )
        if not self.supports_claims:
            raise ValueError("supports_claims must be non-empty (which Claim does it support?)")
        if self.verdict not in _VALID_VERDICTS:
            raise ValueError(f"verdict must be one of {sorted(_VALID_VERDICTS)}, got {self.verdict!r}")

    def to_ordered_dict(self) -> Dict[str, Any]:
        raw = asdict(self)
        return {k: raw[k] for k in MANIFEST_FIELDS}


def write_manifest(path: str, manifest: ArtifactManifest) -> Dict[str, Any]:
    """Atomically write a manifest YAML. Returns the ordered dict written."""
    row = manifest.to_ordered_dict()
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            yaml.safe_dump(row, fh, sort_keys=False, allow_unicode=True, default_flow_style=False)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
    return row
