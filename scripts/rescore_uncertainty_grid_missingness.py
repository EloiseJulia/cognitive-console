"""CPU-only no-imputation rescore of cached E-0006 uncertainty transcripts.

This exploratory extension validates cached transcript rows against the frozen
E-0006 per-item outcomes, then separates confidence-format compliance from
calibration. It never uses confidence=0.5 in a reported estimand.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cognitive_console.experiments import adjudicate_c2b as adj
from scripts import reanalyse_uncertainty_grid as grid

EXPERIMENT_ID = "E-0017-uncertainty-grid-no-impute-extension"
DEFAULT_OUTPUT = (
    _REPO
    / "results"
    / "E-0017-uncertainty-grid-no-impute-extension"
    / "missingness_rescore.json"
)
CONDITIONS = ("prompt", "steer", "baseline")


class RescoreError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_hash(value: object) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def git_commit() -> str:
    return subprocess.run(
        ["git", "-C", str(_REPO), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def git_dirty() -> bool:
    return bool(
        subprocess.run(
            [
                "git",
                "-C",
                str(_REPO),
                "status",
                "--porcelain",
                "--untracked-files=all",
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    )


def _json_number(value: float) -> Optional[float]:
    return float(value) if math.isfinite(float(value)) else None


def _ci(
    diffs: Sequence[float], *, bootstrap_b: int, seed: int, ci_level: float
) -> Dict[str, object]:
    if not diffs:
        return {
            "estimand_available": False,
            "point": None,
            "ci_lo": None,
            "ci_hi": None,
            "ci_level": ci_level,
            "bootstrap_b": bootstrap_b,
            "n_items": 0,
        }
    result = adj.cluster_bootstrap_ci(
        np.asarray(diffs, dtype=float),
        b=bootstrap_b,
        ci_level=ci_level,
        seed=seed,
        cluster=True,
    )
    return {
        "estimand_available": True,
        "point": _json_number(result.point),
        "ci_lo": _json_number(result.ci_lo),
        "ci_hi": _json_number(result.ci_hi),
        "ci_level": result.ci_level,
        "bootstrap_b": bootstrap_b,
        "n_items": len(diffs),
    }


def _condition_item_means(
    records: Sequence[Dict], condition: str, *, observed_only: bool
) -> Tuple[Dict[str, float], int]:
    grouped: Dict[str, List[float]] = defaultdict(list)
    used = 0
    for row in records:
        if row["condition"] != condition:
            continue
        if observed_only and not bool(row["format_compliant"]):
            continue
        grouped[str(row["item_id"])].append(float(row["per_item_1minus_brier"]))
        used += 1
    return {
        item_id: float(np.mean(values)) for item_id, values in grouped.items()
    }, used


def paired_sample_complete_case(
    records: Sequence[Dict],
) -> Tuple[List[float], Dict[str, int]]:
    keyed: Dict[Tuple[str, int], Dict[str, Dict]] = defaultdict(dict)
    for row in records:
        if row["condition"] in {"prompt", "steer"}:
            keyed[(str(row["item_id"]), int(row["sample_index"]))][
                str(row["condition"])
            ] = row
    by_item: Dict[str, List[float]] = defaultdict(list)
    counts = {
        "total_sample_pairs": len(keyed),
        "retained_sample_pairs": 0,
        "dropped_sample_pairs": 0,
    }
    for (item_id, _), pair in keyed.items():
        if not (
            pair["prompt"]["format_compliant"]
            and pair["steer"]["format_compliant"]
        ):
            counts["dropped_sample_pairs"] += 1
            continue
        counts["retained_sample_pairs"] += 1
        by_item[item_id].append(
            float(pair["steer"]["per_item_1minus_brier"])
            - float(pair["prompt"]["per_item_1minus_brier"])
        )
    diffs = [
        float(np.mean(values)) for _, values in sorted(by_item.items())
    ]
    counts["retained_items"] = len(diffs)
    counts["dropped_items_zero_complete_pairs"] = (
        len({item_id for item_id, _ in keyed}) - len(diffs)
    )
    return diffs, counts


def no_impute_itemwise_available_case(
    records: Sequence[Dict],
) -> Tuple[List[float], Dict[str, int]]:
    prompt, n_prompt = _condition_item_means(
        records, "prompt", observed_only=True
    )
    steer, n_steer = _condition_item_means(
        records, "steer", observed_only=True
    )
    retained = sorted(set(prompt) & set(steer))
    all_items = {
        str(row["item_id"])
        for row in records
        if row["condition"] in {"prompt", "steer"}
    }
    return [steer[item_id] - prompt[item_id] for item_id in retained], {
        "observed_prompt_samples": n_prompt,
        "observed_steer_samples": n_steer,
        "retained_items": len(retained),
        "dropped_items_without_observed_prompt_or_steer": len(all_items)
        - len(retained),
    }


def adversarial_endpoint_diffs(
    records: Sequence[Dict], *, steer_missing_score: float, prompt_missing_score: float
) -> List[float]:
    grouped: Dict[str, Dict[str, List[float]]] = defaultdict(
        lambda: {"prompt": [], "steer": []}
    )
    for row in records:
        condition = str(row["condition"])
        if condition not in {"prompt", "steer"}:
            continue
        if bool(row["format_compliant"]):
            score = float(row["per_item_1minus_brier"])
        else:
            score = (
                steer_missing_score
                if condition == "steer"
                else prompt_missing_score
            )
        grouped[str(row["item_id"])][condition].append(score)
    return [
        float(np.mean(values["steer"]) - np.mean(values["prompt"]))
        for _, values in sorted(grouped.items())
    ]


def condition_summary(
    records: Sequence[Dict],
    condition: str,
    *,
    bootstrap_b: int,
    seed: int,
    ci_level: float,
) -> Dict[str, object]:
    rows = [row for row in records if row["condition"] == condition]
    compliant = [row for row in rows if bool(row["format_compliant"])]
    item_means, _ = _condition_item_means(
        records, condition, observed_only=True
    )
    calibration = _ci(
        list(item_means.values()),
        bootstrap_b=bootstrap_b,
        seed=seed,
        ci_level=ci_level,
    )
    if not calibration["estimand_available"]:
        calibration["unavailable_reason"] = (
            "No parsable confidence values in this condition."
        )
    return {
        "generation_quality": {
            "n_samples": len(rows),
            "n_format_compliant": len(compliant),
            "n_parse_failures": len(rows) - len(compliant),
            "format_compliance_rate": len(compliant) / len(rows) if rows else None,
            "format_compliance_exact": f"{len(compliant)}/{len(rows)}",
        },
        "calibration_among_parsable_only": {
            **calibration,
            "metric": "1_minus_Brier",
            "n_observed_samples": len(compliant),
            "conditioning_warning": (
                "Post-generation conditional calibration; parse failures are "
                "not assigned confidence=0.5 or any calibration score."
            ),
        },
    }


def analyse_cell(
    records: Sequence[Dict], *, bootstrap_b: int, seed: int, ci_level: float
) -> Dict[str, object]:
    paired_diffs, paired_counts = paired_sample_complete_case(records)
    item_diffs, item_counts = no_impute_itemwise_available_case(records)
    lower_diffs = adversarial_endpoint_diffs(
        records, steer_missing_score=0.0, prompt_missing_score=1.0
    )
    upper_diffs = adversarial_endpoint_diffs(
        records, steer_missing_score=1.0, prompt_missing_score=0.0
    )
    lower = _ci(
        lower_diffs, bootstrap_b=bootstrap_b, seed=seed, ci_level=ci_level
    )
    upper = _ci(
        upper_diffs, bootstrap_b=bootstrap_b, seed=seed, ci_level=ci_level
    )
    lower_point = float(lower["point"])
    upper_point = float(upper["point"])
    return {
        "conditions": {
            condition: condition_summary(
                records,
                condition,
                bootstrap_b=bootstrap_b,
                seed=seed,
                ci_level=ci_level,
            )
            for condition in CONDITIONS
        },
        "steer_minus_prompt": {
            "metric": "1_minus_Brier",
            "paired_sample_complete_case": {
                **_ci(
                    paired_diffs,
                    bootstrap_b=bootstrap_b,
                    seed=seed,
                    ci_level=ci_level,
                ),
                **paired_counts,
                "policy": (
                    "Retain an (item_id, sample_index) pair only when both "
                    "prompt and steer confidence parse; average retained pair "
                    "differences within item, then bootstrap items."
                ),
            },
            "no_impute_drop_missing_item": {
                **_ci(
                    item_diffs,
                    bootstrap_b=bootstrap_b,
                    seed=seed,
                    ci_level=ci_level,
                ),
                **item_counts,
                "policy": (
                    "Within each condition, average only parsable samples. "
                    "Drop an item if either prompt or steer has zero parsable "
                    "samples; never fill a missing confidence."
                ),
            },
            "adversarial_missingness_bounds": {
                "least_favorable_to_steer": {
                    **lower,
                    "missing_steer_1minus_Brier": 0.0,
                    "missing_prompt_1minus_Brier": 1.0,
                },
                "most_favorable_to_steer": {
                    **upper,
                    "missing_steer_1minus_Brier": 1.0,
                    "missing_prompt_1minus_Brier": 0.0,
                },
                "point_identification_interval": [lower_point, upper_point],
                "spans_zero": lower_point <= 0.0 <= upper_point,
                "strict_negative_sign_stable": upper_point < 0.0,
                "strict_positive_sign_stable": lower_point > 0.0,
                "policy": (
                    "Use every generated sample. Assign missing 1-Brier to "
                    "the [0,1] endpoints that respectively minimize and "
                    "maximize steer-minus-prompt, then bootstrap items at each "
                    "endpoint."
                ),
            },
        },
    }


def directory_inventory(path: Path) -> Dict[str, object]:
    files = sorted(candidate for candidate in path.rglob("*") if candidate.is_file())
    manifest = [
        {
            "path": candidate.relative_to(path).as_posix(),
            "size_bytes": candidate.stat().st_size,
            "sha256": sha256_file(candidate),
        }
        for candidate in files
    ]
    return {
        "file_count": len(manifest),
        "total_bytes": sum(row["size_bytes"] for row in manifest),
        "manifest_sha256": canonical_hash(manifest),
    }


def _used_file_manifest(source_meta: Dict, cache_root: Path) -> List[Dict]:
    output = []
    for row in source_meta["files"]:
        path = Path(str(row["path"]))
        if not path.is_absolute():
            path = (_REPO / path).resolve()
        output.append(
            {
                "path_relative_to_cache_root": path.relative_to(
                    cache_root.resolve()
                ).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": row["sha256"],
                "rows": row["rows"],
            }
        )
    return sorted(output, key=lambda row: row["path_relative_to_cache_root"])


def run(cache_root: Path, protocol_path: Path) -> Dict[str, object]:
    protocol = grid.load_protocol(protocol_path)
    analysis = dict(protocol["analysis"])
    bootstrap_b = int(analysis["bootstrap_b"])
    seed = int(analysis["bootstrap_seed"])
    ci_level = float(analysis["ci_level"])
    items, splits, item_meta = grid.load_frozen_items(protocol)
    items_by_id = {str(item["id"]): item for item in items}
    test_ids = [str(item["id"]) for item in splits["test"]]
    frozen_root = grid._resolve(protocol["generation"]["frozen_root"])
    local_root = frozen_root.resolve()
    cache_root = cache_root.resolve()
    cells: Dict[str, Dict] = {}
    unavailable: Dict[str, Dict] = {}

    for cell_key, cell_spec in sorted(protocol["cells"].items()):
        cfg, frozen_payload, frozen_meta = grid.validate_cell_manifest(
            cell_key, cell_spec, frozen_root
        )
        transcript_dir = cache_root / f"cell_{cell_key}" / "transcripts"
        local_dir = local_root / f"cell_{cell_key}" / "transcripts"
        availability = {
            "worktree_snapshot_path": local_dir.relative_to(_REPO).as_posix(),
            "worktree_snapshot_exists": local_dir.is_dir(),
            "cache_path_relative_to_cache_root": transcript_dir.relative_to(
                cache_root
            ).as_posix(),
            "cache_snapshot_exists": transcript_dir.is_dir(),
        }
        if not transcript_dir.is_dir():
            unavailable[cell_key] = {
                **availability,
                "status": "SNAPSHOT_ABSENT_FAIL_CLOSED",
            }
            continue
        try:
            records, source_meta = grid._load_c2b_transcript_dir(
                transcript_dir,
                cell_key=cell_key,
                cfg=cfg,
                frozen_payload=frozen_payload,
                items_by_id=items_by_id,
                test_ids=test_ids,
                generation=protocol["generation"],
            )
        except Exception as exc:
            unavailable[cell_key] = {
                **availability,
                "status": "PRESENT_BUT_VALIDATION_FAILED_FAIL_CLOSED",
                "failure_type": type(exc).__name__,
                "failure_reason": str(exc),
            }
            continue
        coverage = grid._validate_coverage(
            records,
            cell_key=cell_key,
            test_ids=test_ids,
            k=int(protocol["generation"]["k_samples"]),
        )
        used_files = _used_file_manifest(source_meta, cache_root)
        cells[cell_key] = {
            "availability": {
                **availability,
                "status": "PRESENT_VALIDATED_EXPLORATORY_CACHE",
                "transcript_directory_inventory": directory_inventory(
                    transcript_dir
                ),
                "used_test_files": used_files,
                "used_test_files_manifest_sha256": canonical_hash(used_files),
                "source_rows": len(records),
                "frozen_per_item_outcomes_reproduced": bool(
                    source_meta["frozen_per_item_outcomes_reproduced"]
                ),
                "coverage": coverage,
            },
            "frozen_identity": {
                "method": cfg.method,
                "model_label": cfg.model_label,
                "layer": cfg.layer,
                "requested_alpha": cfg.frozen_alpha,
                "frozen_result": frozen_meta,
            },
            "analysis": analyse_cell(
                records,
                bootstrap_b=bootstrap_b,
                seed=seed,
                ci_level=ci_level,
            ),
        }

    return {
        "schema_version": "uncertainty-grid-no-impute-extension-v1",
        "experiment_id": EXPERIMENT_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "experiment_type": "exploratory_robustness_extension",
        "valid_for_paper": False,
        "code_commit": git_commit(),
        "dirty_tree_at_run": git_dirty(),
        "hardware": "CPU-only rescoring; no model inference",
        "metric": "1_minus_Brier",
        "bootstrap": {
            "B": bootstrap_b,
            "seed": seed,
            "ci_level": ci_level,
            "unit": "item",
            "method": "percentile item-cluster bootstrap",
        },
        "relationship_to_frozen_e0013": {
            "frozen_confirmatory_scope": "CAA×Qwen only",
            "extension_scope": "cached E-0006 TEST transcripts across available four-grid cells",
            "replacement": False,
            "guard": (
                "This artifact does not overwrite or re-authorize E-0013. "
                "Recovered transcript hashes were not frozen before recovery; "
                "frozen-score reproduction establishes internal consistency, "
                "not original-source provenance. All new cell results remain "
                "exploratory pending independent audit."
            ),
        },
        "input_lineage": {
            "protocol_path": protocol_path.relative_to(_REPO).as_posix(),
            "protocol_sha256": sha256_file(protocol_path),
            "item_artifact": item_meta,
            "runtime_cache_root": str(cache_root),
        },
        "available_cells": sorted(cells),
        "unavailable_cells": sorted(unavailable),
        "cells": cells,
        "unavailable": unavailable,
        "grid_complete_in_local_cache": len(cells) == len(protocol["cells"]),
        "claim_guard": (
            "Compliance and parsability are generation-quality outcomes. "
            "Calibration is reported only among observed confidences or under "
            "explicit [0,1] adversarial bounds; confidence=0.5 is never used "
            "in a reported E-0017 estimand."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cache-root",
        type=Path,
        required=True,
        help="Path containing cell_*/transcripts cached arm directories.",
    )
    parser.add_argument(
        "--protocol",
        type=Path,
        default=grid.DEFAULT_MANIFEST,
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = run(args.cache_root, args.protocol.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(
        output, indent=2, ensure_ascii=False, allow_nan=False
    ) + "\n"
    args.output.write_text(encoded, encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
