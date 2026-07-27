"""Deterministically audit response-side disclosure redaction for flagship records."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))

from cognitive_console.social.scoring import DISCLOSURE_PATTERNS


def has_redacted_response_disclosure_leak(text: str) -> bool:
    redacted = str(text)
    if any(pattern.search(redacted) for pattern in DISCLOSURE_PATTERNS):
        return True
    return bool(
        re.search(
            r"\bnovice\b|\bexpert\b|novice_disclosure|expert_disclosure",
            redacted,
            re.I,
        )
    )


def build_redaction_audit(result_path: Path) -> dict:
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    leaks = []
    for index, record in enumerate(payload.get("records", [])):
        redacted_response = record.get("scores", {}).get("redacted_response", "")
        if has_redacted_response_disclosure_leak(redacted_response):
            leaks.append(
                {
                    "record_index": index,
                    "item_id": record.get("item_id"),
                    "condition_id": record.get("condition_id"),
                    "sample_index": record.get("sample_index"),
                    "redacted_response": redacted_response,
                }
            )
    return {
        "schema": "flagship_redaction_audit_v1",
        "source_result": str(result_path).replace("\\", "/"),
        "audit_scope": "response-side redacted_response exact disclosure terms using committed DISCLOSURE_PATTERNS",
        "passed": len(leaks) == 0,
        "leak_count": len(leaks),
        "leaks": leaks,
        "note": (
            "Generated deterministically from records[*].scores.redacted_response; "
            "generic expertise/experts words are not condition disclosures."
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("result_json", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    return ap


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    audit = build_redaction_audit(args.result_json)
    text = json.dumps(audit, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0 if audit["passed"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
