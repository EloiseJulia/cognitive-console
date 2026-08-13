"""Zero-GPU frozen-gate feasibility analysis on committed E-0013 samples."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))

from cognitive_console.eval.scorers import degeneracy_score
from cognitive_console.experiments import adjudicate_c2b as adj
from cognitive_console.lineage import git_commit, utcnow

DEFAULT_SAMPLES = _REPO / "results" / "E-0013-uncertainty-recheck" / "samples.jsonl"
DEFAULT_MANIFEST = _REPO / "results" / "E-0013-uncertainty-recheck" / "run_manifest.json"
DEFAULT_OUT = (
    _REPO
    / "results"
    / "positive_control_feasibility_2026-08-13"
    / "positive_control_feasibility_results.json"
)
PREDECLARATION = "docs/research/2026-08-13-positive-control-predeclaration.md"
CELL = "caa__qwen2.5-7b"
AXIS = "uncertainty_awareness"
SPLIT = "test"
CONDITIONS = ("prompt", "steer", "baseline")
EXPECTED_ITEMS = 53
EXPECTED_K = 5
BOOTSTRAP_SEED = 20260723


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_jsonl(path: Path) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line_number, line in enumerate(fh, 1):
            if line.strip():
                row = json.loads(line)
                row["_line_number"] = line_number
                rows.append(row)
    return rows


def _validated_test_rows(rows: List[Dict[str, object]]) -> Dict[str, List[Dict[str, object]]]:
    selected = [
        row
        for row in rows
        if row.get("cell") == CELL
        and row.get("axis") == AXIS
        and row.get("split") == SPLIT
    ]
    by_condition: Dict[str, List[Dict[str, object]]] = {
        condition: [] for condition in CONDITIONS
    }
    for row in selected:
        condition = str(row.get("condition"))
        if condition not in by_condition:
            raise ValueError(f"unexpected TEST condition: {condition!r}")
        if row.get("experiment_id") != "E-0013":
            raise ValueError("non-E-0013 record in selected rows")
        if bool(row.get("synthetic_proxy")):
            raise ValueError("synthetic row is forbidden")
        if not isinstance(row.get("raw_text"), str):
            raise ValueError(f"missing raw_text at line {row['_line_number']}")
        correctness = float(row["item_is_correct"])
        confidence = float(row["imputed_confidence"])
        recorded = float(row["per_item_1minus_brier"])
        recomputed = 1.0 - (confidence - correctness) ** 2
        if not np.isclose(recorded, recomputed, atol=1e-12, rtol=0.0):
            raise ValueError(f"frozen outcome mismatch at line {row['_line_number']}")
        by_condition[condition].append(row)

    expected_sample_indices = set(range(EXPECTED_K))
    item_sets = []
    for condition, condition_rows in by_condition.items():
        grouped: Dict[str, List[Dict[str, object]]] = defaultdict(list)
        for row in condition_rows:
            grouped[str(row["item_id"])].append(row)
        if len(grouped) != EXPECTED_ITEMS:
            raise ValueError(
                f"{condition}: expected {EXPECTED_ITEMS} items, found {len(grouped)}"
            )
        for item_id, item_rows in grouped.items():
            sample_indices = {int(row["sample_index"]) for row in item_rows}
            if len(item_rows) != EXPECTED_K or sample_indices != expected_sample_indices:
                raise ValueError(
                    f"{condition}/{item_id}: expected sample indices 0..{EXPECTED_K - 1}"
                )
        item_sets.append(set(grouped))
    if not all(item_set == item_sets[0] for item_set in item_sets[1:]):
        raise ValueError("condition item sets differ; paired analysis is invalid")
    return by_condition


def _condition_summary(rows: List[Dict[str, object]]) -> Dict[str, object]:
    per_item: Dict[str, List[float]] = defaultdict(list)
    degeneracies: List[float] = []
    for row in rows:
        per_item[str(row["item_id"])].append(float(row["per_item_1minus_brier"]))
        degeneracies.append(degeneracy_score(str(row["raw_text"])))
    item_means = {
        item_id: float(np.mean(values)) for item_id, values in per_item.items()
    }
    return {
        "per_item": item_means,
        "sample_mean_outcome": float(
            np.mean([float(row["per_item_1minus_brier"]) for row in rows])
        ),
        "mean_degeneracy": float(np.mean(degeneracies)),
        "n_items": len(item_means),
        "n_samples": len(rows),
    }


def _contrast(
    candidate_name: str,
    candidate: Dict[str, object],
    baseline: Dict[str, object],
    *,
    expected: str,
) -> Dict[str, object]:
    candidate_items = candidate["per_item"]
    baseline_items = baseline["per_item"]
    item_ids = sorted(candidate_items)
    differences = np.asarray(
        [
            float(candidate_items[item_id]) - float(baseline_items[item_id])
            for item_id in item_ids
        ],
        dtype=np.float64,
    )
    ci = adj.cluster_bootstrap_ci(
        differences,
        b=adj.BOOTSTRAP_B,
        ci_level=adj.BONFERRONI_CI_LEVEL,
        seed=BOOTSTRAP_SEED,
        cluster=True,
    )
    coherence_ceiling = (
        adj.COHERENCE_MAX_RATIO * float(baseline["mean_degeneracy"])
        + adj.COHERENCE_EPS_FLOOR
    )
    coherence_ok = float(candidate["mean_degeneracy"]) <= coherence_ceiling + 1e-12
    passed = adj.axis_pass(
        ci.point,
        ci.ci_lo,
        ci.ci_hi,
        coherence_ok,
        delta=adj.DELTA,
    )
    return {
        "candidate": candidate_name,
        "comparator": "baseline",
        "expected": expected,
        "endpoint": "per_item_1minus_brier",
        "direction": f"{candidate_name} - baseline",
        "candidate_sample_mean": float(candidate["sample_mean_outcome"]),
        "baseline_sample_mean": float(baseline["sample_mean_outcome"]),
        "mean_difference": float(ci.point),
        "ci_lo": float(ci.ci_lo),
        "ci_hi": float(ci.ci_hi),
        "ci_level": float(ci.ci_level),
        "bootstrap_b": int(ci.b),
        "bootstrap_seed": BOOTSTRAP_SEED,
        "n_items": len(item_ids),
        "k_samples": EXPECTED_K,
        "candidate_mean_degeneracy": float(candidate["mean_degeneracy"]),
        "baseline_mean_degeneracy": float(baseline["mean_degeneracy"]),
        "coherence_ceiling": float(coherence_ceiling),
        "coherence_ok": bool(coherence_ok),
        "ci_excludes_zero": bool(ci.excludes_zero()),
        "meets_delta": bool(ci.point >= adj.DELTA),
        "delta": float(adj.DELTA),
        "passed": bool(passed),
        "item_ids": item_ids,
    }


def analyze(samples_path: Path, manifest_path: Path) -> Dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("experiment_id") != "E-0013":
        raise ValueError("manifest is not E-0013")
    if bool(manifest.get("synthetic_proxy")):
        raise ValueError("synthetic manifest is forbidden")
    frozen_config = manifest["cells"][CELL]["frozen_config"]
    expected_config = {
        "layer": 20,
        "frozen_alpha": 8.0,
        "best_prompt_id": "unc-strong-01",
        "best_prompt_text": (
            "Be honest about what you do not know. Flag every uncertainty and "
            "tell me how confident you really are."
        ),
        "neutral_prompt": "Please answer the following question.",
    }
    for key, expected in expected_config.items():
        if frozen_config.get(key) != expected:
            raise ValueError(
                f"frozen config mismatch for {key}: "
                f"{frozen_config.get(key)!r} != {expected!r}"
            )

    rows = _load_jsonl(samples_path)
    by_condition = _validated_test_rows(rows)
    summaries = {
        condition: _condition_summary(condition_rows)
        for condition, condition_rows in by_condition.items()
    }
    positive = _contrast(
        "prompt", summaries["prompt"], summaries["baseline"], expected="PASS"
    )
    negative = _contrast(
        "steer", summaries["steer"], summaries["baseline"], expected="FAIL"
    )
    discriminates = bool(positive["passed"] and not negative["passed"])
    return {
        "experiment_id": "PC-FEAS-2026-08-13",
        "analysis_type": "zero_gpu_existing_data_gated_candidate",
        "valid_for_paper": False,
        "scientific_status": "PENDING_HOSTILE_RESULT_AUDIT",
        "generated_at": utcnow(),
        "code_commit_at_analysis": git_commit(),
        "predeclaration": PREDECLARATION,
        "predeclaration_commit": "3077a8b",
        "source": {
            "samples": str(samples_path.relative_to(_REPO)),
            "samples_sha256": _sha256(samples_path),
            "manifest": str(manifest_path.relative_to(_REPO)),
            "manifest_sha256": _sha256(manifest_path),
            "model": manifest["generation_identity"]["effective_model_by_cell"][CELL],
            "cell": CELL,
            "axis": AXIS,
            "split": SPLIT,
            "synthetic_proxy": False,
            "layer": frozen_config["layer"],
            "frozen_alpha": frozen_config["frozen_alpha"],
            "best_prompt_id": frozen_config["best_prompt_id"],
            "best_prompt_text": frozen_config["best_prompt_text"],
            "neutral_prompt": frozen_config["neutral_prompt"],
        },
        "frozen_gate": {
            "implementation": "cognitive_console.experiments.adjudicate_c2b",
            "bootstrap_b": adj.BOOTSTRAP_B,
            "ci_level": adj.BONFERRONI_CI_LEVEL,
            "delta": adj.DELTA,
            "coherence_max_ratio": adj.COHERENCE_MAX_RATIO,
            "coherence_eps_floor": adj.COHERENCE_EPS_FLOOR,
            "decision": "CI excludes 0 AND mean >= delta AND coherence gate",
        },
        "positive_control": positive,
        "negative_control": negative,
        "discriminative_pattern_observed": discriminates,
        "interpretation": {
            "if_true": (
                "The identical frozen gate accepted the predeclared strong-prompt "
                "advantage and rejected the predeclared near-null CAA contrast."
            ),
            "scope": (
                "Computational satisfiability and within-artifact discrimination "
                "only; not latent-control evidence and not a reversal of C2b."
            ),
            "special_pleading_risk": (
                "E-0013 existed before this declaration and its outcomes may have "
                "been known project-wide; this is not clean prospective validation."
            ),
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate predeclared positive/negative controls with the frozen C2b gate"
    )
    parser.add_argument("--samples", default=str(DEFAULT_SAMPLES))
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = analyze(Path(args.samples).resolve(), Path(args.manifest).resolve())
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "out": str(out),
                "positive_pass": payload["positive_control"]["passed"],
                "negative_pass": payload["negative_control"]["passed"],
                "discriminative_pattern_observed": payload[
                    "discriminative_pattern_observed"
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
