"""Recompute avg-prompt minus frozen best-prompt diagnostics from raw JSON.

This repairs only derived reporting fields. It never changes frozen E-0005/E-0006
inputs, prompt/alpha selection, generated transcripts, or per-item outcomes.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))

from cognitive_console.experiments import adjudicate_c2b as adj
from cognitive_console.lineage import utcnow

METHODS = ("caa", "iti")
AXES = ("deliberation", "skepticism", "uncertainty_awareness")


def _load_axis(path: Path, axis: str) -> Dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    for row in data["axes"]:
        if row["axis"] == axis:
            return row
    raise ValueError(f"{path} has no axis={axis}")


def _contrast(avg16: List[float], frozen_best: List[float], *,
              seed: int, bootstrap_b: int) -> Dict[str, object]:
    diff = np.asarray(avg16, dtype=float) - np.asarray(frozen_best, dtype=float)
    ci = adj.cluster_bootstrap_ci(
        diff,
        b=int(bootstrap_b),
        ci_level=adj.BONFERRONI_CI_LEVEL,
        seed=int(seed),
        cluster=True,
    )
    return {
        "name": "avg16_minus_frozen_best_prompt",
        "mean_diff": ci.point,
        "ci_lo": ci.ci_lo,
        "ci_hi": ci.ci_hi,
        "ci_level": ci.ci_level,
        "bootstrap_b": int(bootstrap_b),
        "per_item_diff": [float(x) for x in diff],
        "note": "diagnostic avg-prompt minus frozen DEV-selected best-prompt arm; not a pass/fail contrast",
    }


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(_REPO))
    ap.add_argument("--seed", type=int, default=20260723)
    ap.add_argument("--bootstrap-b", type=int, default=adj.BOOTSTRAP_B)
    args = ap.parse_args(argv)

    root = Path(args.root)
    rows: List[Dict[str, object]] = []
    for method in METHODS:
        frozen_path = root / "results" / "arm_full" / f"cell_{method}__qwen2.5-7b" / "c2b_adjudication_results.json"
        for axis in AXES:
            avg_path = root / "results" / "avg_prompt_full" / f"cell_{method}__qwen2.5-7b__{axis}" / "avg_prompt_comparator_results.json"
            avg_doc = json.loads(avg_path.read_text(encoding="utf-8"))
            if len(avg_doc["axes"]) != 1 or avg_doc["axes"][0]["axis"] != axis:
                raise ValueError(f"{avg_path}: expected exactly one axis row for {axis}")
            avg_row = avg_doc["axes"][0]
            frozen_row = _load_axis(frozen_path, axis)
            contrast = _contrast(
                avg_row["primary_avg16"]["per_item_comparator"],
                frozen_row["per_item_prompt"],
                seed=args.seed,
                bootstrap_b=args.bootstrap_b,
            )
            avg_row.setdefault("descriptive", {})["avg16_minus_frozen_best_prompt"] = contrast
            avg_doc["avg_minus_best_recomputed_at"] = utcnow()
            avg_path.write_text(json.dumps(avg_doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            rows.append({
                "method": method,
                "axis": axis,
                "result_json": str(avg_path.relative_to(root)).replace("\\", "/"),
                "mean_diff": contrast["mean_diff"],
                "ci_lo": contrast["ci_lo"],
                "ci_hi": contrast["ci_hi"],
                "bootstrap_b": contrast["bootstrap_b"],
            })

    repair_root = root / "results" / "avg_prompt_delib512_repair"
    for method in METHODS:
        repair_path = (
            repair_root
            / f"cell_{method}__qwen2.5-7b__deliberation_steer512"
            / "delib_512_steer_repair_results.json"
        )
        if repair_path.exists():
            doc = json.loads(repair_path.read_text(encoding="utf-8"))
            old = doc["contrasts"]["avg512_minus_frozen_best64"]
            doc["contrasts"]["avg512_minus_frozen_best_prompt"] = old
            doc["avg_minus_best_recomputed_at"] = utcnow()
            repair_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    summary = {
        "generated_at": utcnow(),
        "source": "scripts/recompute_avg_best_contrasts.py",
        "note": "All means are recomputed from raw per-item avg16 and frozen best-prompt arrays.",
        "rows": rows,
    }
    out = root / "results" / "avg_prompt_full" / "avg_minus_frozen_best_summary.json"
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
