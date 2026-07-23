"""Phase-0 experiments: conflict probe (C2b seed)."""

from .conflict_probe import (
    BehaviorBackend,
    ConflictConfig,
    ConflictResult,
    HFBehaviorBackend,
    SyntheticBehaviorBackend,
    compute_landing,
    run_conflict_probe,
)

__all__ = [
    "BehaviorBackend",
    "ConflictConfig",
    "ConflictResult",
    "HFBehaviorBackend",
    "SyntheticBehaviorBackend",
    "compute_landing",
    "run_conflict_probe",
]
