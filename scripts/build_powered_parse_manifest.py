"""Build a compact parse/missingness manifest for E-0016 powered skepticism.

Reads the ignored raw transcript JSONL files, commits only parse flags and
missingness counts. If transcripts are absent, writes an honest summary-only
manifest instead of reconstructing or inventing parse evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List


PHASES = ("test_prompt", "test_steer", "test_baseline")


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def phase_from_name(path: Path) -> str | None:
    name = path.name
    for phase in PHASES:
        if f"__{phase}__" in name:
            return phase
    return None


def build_from_transcripts(cell_dir: Path) -> Dict[str, Any] | None:
    transcript_dir = cell_dir / "transcripts"
    files = sorted(transcript_dir.glob("skepticism__*.jsonl"))
    if not files:
        return None
    by_phase: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
        phase: {} for phase in PHASES
    }
    transcript_hashes: Dict[str, str] = {}
    for path in files:
        phase = phase_from_name(path)
        if phase is None:
            continue
        transcript_hashes[path.name] = sha256_file(path)
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                item_id = str(row["item_id"])
                by_phase[phase].setdefault(item_id, []).append(row)

    phase_summary: Dict[str, Any] = {}
    item_parse: Dict[str, Any] = {}
    all_item_ids = sorted({i for phase_rows in by_phase.values() for i in phase_rows})
    for phase in PHASES:
        rows = [r for per_item in by_phase[phase].values() for r in per_item]
        n = len(rows)
        missing = sum(1 for r in rows if (r.get("parse") or {}).get("axis_parse_failed"))
        phase_summary[phase] = {
            "n_generations": n,
            "parseable": n - missing,
            "missingness_count": missing,
            "parse_rate": (n - missing) / n if n else None,
            "n_items": len(by_phase[phase]),
        }
    for item_id in all_item_ids:
        item_parse[item_id] = {}
        for phase in PHASES:
            rows = sorted(by_phase[phase].get(item_id, []), key=lambda r: int(r["sample_index"]))
            flags = "".join(
                "0" if (r.get("parse") or {}).get("axis_parse_failed") else "1"
                for r in rows
            )
            letters = "".join(
                str((r.get("parse") or {}).get("parsed_choice") or "?")
                for r in rows
            )
            item_parse[item_id][phase] = {
                "sample_parse_flags": flags,
                "parsed_letters": letters,
                "parseable": flags.count("1"),
                "missingness_count": flags.count("0"),
                "all_samples_parseable": bool(flags and set(flags) == {"1"}),
            }
    return {
        "source_transcripts_available": True,
        "source_transcript_hashes": transcript_hashes,
        "phase_summary": phase_summary,
        "item_parse": item_parse,
    }


def build_summary_only(cell_dir: Path) -> Dict[str, Any]:
    result_path = cell_dir / "powered_skepticism_b_results.json"
    diagnostics = {}
    if result_path.exists():
        diagnostics = json.loads(result_path.read_text(encoding="utf-8")).get("diagnostics", {})
    return {
        "source_transcripts_available": False,
        "source_transcripts_note": (
            "Raw transcripts were unavailable when this manifest was built; "
            "parse/missingness is summary-only and not independently reproducible "
            "from committed artifacts."
        ),
        "phase_summary": {
            phase: {
                "n_generations": diagnostics.get(phase, {}).get("n_generations"),
                "parseable": diagnostics.get(phase, {}).get("parseable"),
                "missingness_count": diagnostics.get(phase, {}).get("parse_failed"),
                "parse_rate": diagnostics.get(phase, {}).get("parse_rate"),
                "n_items": None,
            }
            for phase in PHASES
        },
        "item_parse": {},
    }


def render_md(manifest: Dict[str, Any]) -> str:
    lines = [
        "# E-0016 powered skepticism-B parse manifest",
        "",
        f"- source_transcripts_available: **{manifest['source_transcripts_available']}**",
        f"- generated_at: `{manifest['generated_at']}`",
        "",
        "| cell | phase | generations | parseable | missing | parse rate | items |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for cell_id, cell in manifest["cells"].items():
        for phase in PHASES:
            row = cell["phase_summary"].get(phase, {})
            lines.append(
                f"| {cell_id} | {phase} | {row.get('n_generations')} | "
                f"{row.get('parseable')} | {row.get('missingness_count')} | "
                f"{row.get('parse_rate')} | {row.get('n_items')} |"
            )
    lines.append("")
    lines.append("Per-item sample parse flags are in `powered_skepticism_b_parse_manifest.json`.")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--results-dir",
        default="results/E-0016-powered-skepticism-b",
        help="E-0016 result directory",
    )
    args = parser.parse_args()
    results_dir = Path(args.results_dir)
    cells: Dict[str, Any] = {}
    for cell_dir in sorted(results_dir.glob("cell_*")):
        if not cell_dir.is_dir():
            continue
        cell_id = cell_dir.name.removeprefix("cell_")
        cells[cell_id] = build_from_transcripts(cell_dir) or build_summary_only(cell_dir)
    manifest = {
        "experiment_id": "e0016-powered-skepticism-b",
        "manifest_type": "parse_missingness_compact",
        "generated_at": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat(),
        "source_transcripts_available": all(
            c.get("source_transcripts_available") for c in cells.values()
        ),
        "cells": cells,
    }
    out_json = results_dir / "powered_skepticism_b_parse_manifest.json"
    out_md = results_dir / "powered_skepticism_b_parse_manifest.md"
    out_json.write_text(
        json.dumps(manifest, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    out_md.write_text(render_md(manifest), encoding="utf-8")
    print(out_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
