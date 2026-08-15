"""Deliberation 512-token remeasurement runner.

This is a thin protocol wrapper around the powered-TOST A infrastructure. It
keeps the same loaders, split, CAA extraction, DEV sealing, TEST-once guard,
raw-bundle mechanics, statistics, and scorer, while freezing the deliberation
remeasurement to D1/D2 and ``max_new_tokens=512``.
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


PROTOCOL_ID = "deliberation-remeasure-512-20260815"
DEV_EXPERIMENT_ID = "delib-512-dev-20260815"
TEST_EXPERIMENT_ID = "delib-512-test-20260815"
PREREG_PATH = "docs/specs/deliberation-remeasure-512-prereg.md"
MAX_NEW_TOKENS = 512


def configure_protocol() -> None:
    powered.PROTOCOL_ID = PROTOCOL_ID
    powered.DEV_EXPERIMENT_ID = DEV_EXPERIMENT_ID
    powered.TEST_EXPERIMENT_ID = TEST_EXPERIMENT_ID
    powered.PREREG_PATH = PREREG_PATH
    powered.MAX_NEW_TOKENS = MAX_NEW_TOKENS
    powered.DEFAULT_TEST_ATTEMPT_ROOT = Path(
        "/var/lib/cognitive-console/deliberation-remeasure-512/test-attempts"
    )
    powered.CELLS = (
        powered.Cell(
            "D1",
            "caa",
            "qwen",
            powered.QWEN_MODEL_ID,
            powered.QWEN_REVISION,
            "deliberation",
            20,
            40,
            0.023080,
            0.074700,
            225,
            150,
            "results/arm_full/cell_caa__qwen2.5-7b/c2b_adjudication_results.json",
        ),
        powered.Cell(
            "D2",
            "caa",
            "llama",
            powered.LLAMA_MODEL_ID,
            None,
            "deliberation",
            12,
            40,
            0.021706,
            0.070200,
            225,
            150,
            "results/arm_full/cell_caa__llama3-8b/c2b_adjudication_results.json",
        ),
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    configure_protocol()
    return powered.main(list(argv) if argv is not None else None)


if __name__ == "__main__":
    raise SystemExit(main())
