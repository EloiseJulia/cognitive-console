"""CLI wrapper for the authoritative micro-study materials validator."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cognitive_console.microstudy_materials import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
