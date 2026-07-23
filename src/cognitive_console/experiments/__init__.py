"""Phase-0 experiments: conflict probe (C2b seed) + C2b reachability harness."""

from .conflict_probe import (
    BehaviorBackend,
    ConflictConfig,
    ConflictResult,
    HFBehaviorBackend,
    SteeredBehaviorBackend,
    SyntheticBehaviorBackend,
    compute_landing,
    compute_landing_raw,
    run_conflict_probe,
)
from .behavior import AXES, behavior_score, proxy_markers
from .reachability import (
    AxisSteerSpec,
    C2bAxisResult,
    run_c2b_axis,
    run_c2b_pilot,
)

__all__ = [
    "BehaviorBackend",
    "ConflictConfig",
    "ConflictResult",
    "HFBehaviorBackend",
    "SteeredBehaviorBackend",
    "SyntheticBehaviorBackend",
    "compute_landing",
    "compute_landing_raw",
    "run_conflict_probe",
    "AXES",
    "behavior_score",
    "proxy_markers",
    "AxisSteerSpec",
    "C2bAxisResult",
    "run_c2b_axis",
    "run_c2b_pilot",
]
