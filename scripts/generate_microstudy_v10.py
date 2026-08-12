"""Generate or verify the V10 button-board materials."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cognitive_console.button_board_materials import (  # noqa: E402
    DERIVED_KEYS_PATH,
    MATERIALS_PATH,
    SEQUENCES_PATH,
    generate_materials,
    generate_sequences,
    write_generated_materials,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if not args.check:
        write_generated_materials()
        print("generated V10 button-board materials")
        return 0
    materials, keys = generate_materials()
    expected = (
        MATERIALS_PATH.read_text(encoding="utf-8"),
        SEQUENCES_PATH.read_text(encoding="utf-8"),
        DERIVED_KEYS_PATH.read_text(encoding="utf-8"),
    )
    import json

    current = (
        json.dumps(materials, ensure_ascii=False, indent=2) + "\n",
        json.dumps(generate_sequences(), ensure_ascii=False, indent=2) + "\n",
        json.dumps(keys, ensure_ascii=False, indent=2) + "\n",
    )
    if expected != current:
        raise SystemExit("generated V10 files are not current")
    print("generated V10 files are current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
