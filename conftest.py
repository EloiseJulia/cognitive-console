"""Test bootstrap: make the src-layout package importable without an install,
and expose the repo data root to tests."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

DATA_ROOT = REPO_ROOT / "data"
