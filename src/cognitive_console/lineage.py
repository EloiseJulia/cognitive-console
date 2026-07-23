"""Run-lineage helpers: mint experiment_ids and register analysis runs.

Ties `config.py` (config_hash) to `registry.py` so every analysis "run" gets a
unique, reconstructable experiment_id. experiment_ids are derived from the run
prefix + a short config-hash slug + a monotonic counter against the live
registry, so re-running the same config in the same registry never collides.
Numbers written into `summary_metrics` come only from computed artifacts — this
helper never fabricates values.
"""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .registry import ExperimentRecord, ExperimentRegistry


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_commit(repo_dir: Optional[str] = None) -> Optional[str]:
    """Best-effort current commit SHA; None if unavailable (never raises)."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if out.returncode == 0:
            return out.stdout.strip()
    except Exception:  # noqa: BLE001 - lineage is best-effort, must not crash a run
        return None
    return None


def _hash_slug(config_hash: Optional[str]) -> str:
    if not config_hash:
        return "nohash"
    return config_hash.split(":", 1)[-1][:8]


def _mint_id_from(
    existing_ids, prefix: str, config_hash: Optional[str] = None
) -> str:
    """Mint a unique `<prefix>-<hashslug>-<NNNN>` against an ids snapshot.

    The counter starts at (# ids sharing the same prefix+slug) + 1 and advances
    past any already-taken id, so the mint is collision-free w.r.t. the snapshot.
    """
    slug = _hash_slug(config_hash)
    stem = f"{prefix}-{slug}"
    taken = {i for i in existing_ids if isinstance(i, str)}
    same_stem = [i for i in taken if i.startswith(stem + "-")]
    n = len(same_stem) + 1
    while True:
        candidate = f"{stem}-{n:04d}"
        if candidate not in taken:
            return candidate
        n += 1


def new_experiment_id(
    registry: ExperimentRegistry,
    prefix: str,
    config_hash: Optional[str] = None,
) -> str:
    """Mint a unique experiment_id: `<prefix>-<hashslug>-<NNNN>`.

    The counter is derived from existing ids sharing the same prefix+slug, so the
    id is stable-per-run and collision-free within one registry snapshot. NOTE:
    this reads the registry OUTSIDE any lock; for collision-safe minting under
    parallel same-config runs use `register_run`, which mints INSIDE the lock.
    """
    return _mint_id_from(registry.ids(), prefix, config_hash)


def register_run(
    registry: ExperimentRegistry,
    prefix: str,
    hypothesis_id: Optional[str],
    claim_ids: List[str],
    config_hash: Optional[str],
    summary_metrics: Dict[str, Any],
    run_type: str = "exploratory",
    model: Optional[str] = None,
    dataset: Optional[str] = None,
    seed: Optional[int] = None,
    hardware: str = "cpu-offline",
    repo_dir: Optional[str] = None,
    status: str = "done",
    artifacts: Optional[List[str]] = None,
) -> str:
    """Create + append a registry row for one analysis run. Returns experiment_id.

    `summary_metrics` must be the computed metrics (no hand values). `hardware`
    defaults to cpu-offline because Phase-0 analysis is the offline pipeline; the
    GPU forward pass is a separate, later run.

    The experiment_id is minted INSIDE the registry lock (via `append_minted`)
    against the freshest ids, so two parallel same-prefix+config runs auto-
    increment to distinct ids instead of colliding on the same NNNN.
    """
    now = utcnow()
    commit = git_commit(repo_dir)

    def _mint(existing_ids) -> ExperimentRecord:
        exp_id = _mint_id_from(existing_ids, prefix, config_hash)
        return ExperimentRecord(
            experiment_id=exp_id,
            hypothesis_id=hypothesis_id,
            claim_ids=list(claim_ids),
            type=run_type,
            status=status,
            code_commit=commit,
            config_hash=config_hash,
            model=model,
            dataset=dataset,
            seed=seed,
            hardware=hardware,
            started_at=now,
            ended_at=now,
            exit_code=0 if status == "done" else None,
            summary_metrics=summary_metrics,
            artifacts=list(artifacts or []),
        )

    row = registry.append_minted(_mint)
    return row["experiment_id"]
