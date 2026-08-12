"""Print the V11 stepwise material validation report."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cognitive_console.button_board_stepwise_materials import validate_materials  # noqa: E402


print(json.dumps(validate_materials(), ensure_ascii=False, indent=2))
