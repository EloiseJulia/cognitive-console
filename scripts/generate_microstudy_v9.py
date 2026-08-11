"""Generate or check the V9 scenario micro-study artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cognitive_console.microstudy_materials import (  # noqa: E402
    MATERIALS_PATH,
    SEQUENCES_PATH,
    generate_materials,
    generate_sequences,
    write_generated_materials,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if not args.check:
        write_generated_materials()
        return 0
    expected_materials, _ = generate_materials()
    expected_sequences = generate_sequences()
    actual_materials = json.loads(MATERIALS_PATH.read_text(encoding="utf-8"))
    actual_sequences = json.loads(SEQUENCES_PATH.read_text(encoding="utf-8"))
    if actual_materials != expected_materials or actual_sequences != expected_sequences:
        raise SystemExit("generated V9 artifacts are stale")
    print("V9 generated artifacts are current.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
