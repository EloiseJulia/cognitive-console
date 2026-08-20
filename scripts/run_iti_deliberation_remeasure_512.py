"""ITI deliberation 512-token remeasurement runner.

Thin protocol wrapper around the powered-TOST A infrastructure, mirroring
``scripts/run_deliberation_remeasure_512.py`` except that the two deliberation
cells use ITI directions with sigma-scaled alpha.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional, Sequence

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))

from scripts import run_powered_tost_a as powered


PROTOCOL_ID = "iti-deliberation-remeasure-512-20260820"
DEV_EXPERIMENT_ID = "iti-delib-512-dev-20260820"
TEST_EXPERIMENT_ID = "iti-delib-512-test-20260820"
PREREG_PATH = "docs/specs/iti-deliberation-remeasure-512-prereg.md"
MAX_NEW_TOKENS = 512


def configure_protocol() -> None:
    powered.PROTOCOL_ID = PROTOCOL_ID
    powered.DEV_EXPERIMENT_ID = DEV_EXPERIMENT_ID
    powered.TEST_EXPERIMENT_ID = TEST_EXPERIMENT_ID
    powered.PREREG_PATH = PREREG_PATH
    powered.MAX_NEW_TOKENS = MAX_NEW_TOKENS
    powered.DEFAULT_TEST_ATTEMPT_ROOT = Path(
        "/var/lib/cognitive-console/iti-deliberation-remeasure-512/test-attempts"
    )
    powered.CELLS = (
        powered.Cell(
            "I1",
            "iti",
            "qwen",
            powered.QWEN_MODEL_ID,
            powered.QWEN_REVISION,
            "deliberation",
            20,
            40,
            0.011983,
            0.038800,
            225,
            150,
            "results/arm_full/cell_iti__qwen2.5-7b/c2b_adjudication_results.json",
        ),
        powered.Cell(
            "I2",
            "iti",
            "llama",
            powered.LLAMA_MODEL_ID,
            None,
            "deliberation",
            8,
            40,
            0.020740,
            0.067100,
            225,
            150,
            "results/arm_full/cell_iti__llama3-8b/c2b_adjudication_results.json",
        ),
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    configure_protocol()
    return powered.main(list(argv) if argv is not None else None)


if __name__ == "__main__":
    raise SystemExit(main())
