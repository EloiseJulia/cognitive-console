"""Build canonical E-0006 all-80 uncertainty baseline artifact from real raw pairs.

Input requirements are intentionally strict: the raw pair JSONL must contain
real-model (``synthetic_proxy=false``) unsteered baseline pairs for exactly 80
uncertainty_awareness items, k=5 each.  This script refuses fixture/proxy data.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))

from cognitive_console.eval.e0012_triviaqa import (  # noqa: E402
    E0006_BASELINE_ITEM_COUNT,
    make_e0006_baseline_artifact,
)


def _load_items(path: Path) -> Dict[str, Dict[str, Any]]:
    rows: Dict[str, Dict[str, Any]] = {}
    with open(path, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            missing = {"id", "prompt", "answer"} - set(row)
            if missing:
                raise ValueError(f"{path}:{lineno} missing item fields {sorted(missing)}")
            rows[str(row["id"])] = row
    return rows


def _load_raw_baseline(path: Path, channel: str) -> Dict[str, List[float]]:
    grouped: Dict[str, List[float]] = defaultdict(list)
    with open(path, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("channel") != channel:
                continue
            if bool(row.get("synthetic_proxy", False)):
                raise ValueError(f"{path}:{lineno} is synthetic_proxy=true; refusing fixture/proxy data")
            if float(row.get("alpha", 0.0)) != 0.0:
                raise ValueError(f"{path}:{lineno} baseline channel has nonzero alpha")
            grouped[str(row["item_id"])].append(float(row["one_minus_brier"]))
    return grouped


def build_artifact(
    *,
    raw_pairs_path: Path,
    item_metadata_path: Path,
    source_experiment_id: str,
    source_run_commit: str,
    baseline_channel: str,
) -> Dict[str, Any]:
    item_meta = _load_items(item_metadata_path)
    grouped = _load_raw_baseline(raw_pairs_path, baseline_channel)
    if len(grouped) != E0006_BASELINE_ITEM_COUNT:
        raise ValueError(
            f"expected {E0006_BASELINE_ITEM_COUNT} baseline item ids; got {len(grouped)}"
        )
    items: List[Dict[str, Any]] = []
    for item_index, item_id in enumerate(sorted(grouped)):
        vals = grouped[item_id]
        if len(vals) != 5:
            raise ValueError(f"item {item_id!r} has k={len(vals)} baseline pairs, expected 5")
        if item_id not in item_meta:
            raise ValueError(f"item metadata missing for {item_id!r}")
        meta = item_meta[item_id]
        items.append({
            "item_index": item_index,
            "id": item_id,
            "prompt": str(meta["prompt"]),
            "answer": str(meta["answer"]),
            "aliases": list(meta.get("aliases", []) or []),
            "baseline_score": sum(vals) / len(vals),
        })
    return make_e0006_baseline_artifact(
        source_experiment_id=source_experiment_id,
        source_run_commit=source_run_commit,
        items=items,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-pairs", required=True, type=Path)
    parser.add_argument("--item-metadata", required=True, type=Path)
    parser.add_argument("--source-experiment-id", required=True)
    parser.add_argument("--source-run-commit", required=True)
    parser.add_argument("--baseline-channel", default="baseline")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    artifact = build_artifact(
        raw_pairs_path=args.raw_pairs,
        item_metadata_path=args.item_metadata,
        source_experiment_id=args.source_experiment_id,
        source_run_commit=args.source_run_commit,
        baseline_channel=args.baseline_channel,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(f"wrote {args.output} sha256={artifact['artifact_sha256']}")


if __name__ == "__main__":
    main()
