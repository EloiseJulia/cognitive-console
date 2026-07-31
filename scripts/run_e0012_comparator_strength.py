"""E-0012-CS comparator-strength check.

Runs a frozen, descriptive held-out TEST comparison between all pre-specified
human-authored calibration prompts, the unsteered baseline, and the E-0012 v3
Stage1 button winner.  This script is additive and reuses the E-0012 harness
sampler/scoring path so scores are mean(1-Brier) from the same OutcomeSampler
and raw-pair machinery as ``run_e0012_verified_control.py``.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))
if str(_REPO / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO / "scripts"))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

import numpy as np

from cognitive_console.experiments import adjudicate_c2b as adj
from cognitive_console.experiments.e0012_ape import (
    _SYNTHETIC_APE_CANDIDATES,
    normalized_prompt_hash,
)
from cognitive_console.experiments.e0012_brier import BrierRawStore
from cognitive_console.experiments.e0012_buttons import BTN_PROBE, all_directions_for_layer
from cognitive_console.experiments.e0012_harness import (
    K_STAGE1,
    TextCapableSampler,
    _eval_items_with_raw_pairs,
    _mean_outcome,
    split_e0012_pool,
)
from cognitive_console.eval.e0012_triviaqa import (
    E0012_POOL_N,
    E0012_POOL_OFFSET,
    E0012_POOL_SEED,
    E0012_SPLIT_SEED,
    load_e0012_pool,
)
from cognitive_console.lineage import utcnow

from run_e0012_verified_control import load_authored_prompts, make_synthetic_sampler


EXPERIMENT_ID = "E-0012-CS"
AXIS = "uncertainty_awareness"
RUN_SEED = 42
FROZEN_K = 5
FROZEN_SYNTHETIC_BANK_COUNT = 30
BUTTON_FAMILY = BTN_PROBE
BUTTON_LAYER = 19
BUTTON_ALPHA = 24.0
HF_HIDDEN_DIM_FALLBACK = 3584


@dataclass(frozen=True)
class ComparatorCondition:
    """One pre-frozen condition for E-0012-CS."""

    condition_id: str
    source: str
    prompt_text: str
    alpha: float
    layer: int
    direction: np.ndarray
    button_spec: Optional[Dict[str, Any]] = None
    prompt_hash: Optional[str] = None


def load_frozen_split() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Load the same frozen E-0012 fixture and split as the verified-control run."""
    all_items = load_e0012_pool(use_fixture=True)
    dev_items, test_items = split_e0012_pool(all_items, split_seed=E0012_SPLIT_SEED)
    return all_items, dev_items, test_items


def build_conditions(hidden_dim: int = HF_HIDDEN_DIM_FALLBACK) -> List[ComparatorCondition]:
    """Build the frozen 30 + 18 + baseline + button condition set."""
    zero_dir = np.zeros(1)
    conditions: List[ComparatorCondition] = []

    synthetic_prompts = list(_SYNTHETIC_APE_CANDIDATES[:FROZEN_SYNTHETIC_BANK_COUNT])
    if len(synthetic_prompts) != FROZEN_SYNTHETIC_BANK_COUNT:
        raise ValueError(
            f"expected {FROZEN_SYNTHETIC_BANK_COUNT} synthetic-bank prompts; "
            f"got {len(synthetic_prompts)}"
        )
    for i, prompt in enumerate(synthetic_prompts):
        conditions.append(ComparatorCondition(
            condition_id=f"SYNTH-BANK-{i:02d}",
            source="synthetic_bank",
            prompt_text=prompt,
            alpha=0.0,
            layer=0,
            direction=zero_dir,
            prompt_hash=normalized_prompt_hash(prompt),
        ))

    authored_prompts = load_authored_prompts()
    if len(authored_prompts) != 18:
        raise ValueError(f"expected 18 calibration YAML prompts; got {len(authored_prompts)}")
    for prompt_id, prompt in authored_prompts:
        conditions.append(ComparatorCondition(
            condition_id=prompt_id,
            source="calibration_yaml",
            prompt_text=prompt,
            alpha=0.0,
            layer=0,
            direction=zero_dir,
            prompt_hash=normalized_prompt_hash(prompt),
        ))

    conditions.append(ComparatorCondition(
        condition_id="BASELINE-UNSTEERED-NO-PROMPT",
        source="baseline",
        prompt_text="",
        alpha=0.0,
        layer=0,
        direction=zero_dir,
        button_spec=None,
        prompt_hash=None,
    ))

    layer_dirs = all_directions_for_layer(BUTTON_LAYER, hidden_dim)
    dir_by_family = {bd.family: bd for bd in layer_dirs}
    if BUTTON_FAMILY not in dir_by_family:
        raise ValueError(f"{BUTTON_FAMILY} direction unavailable at layer {BUTTON_LAYER}")
    button_direction = dir_by_family[BUTTON_FAMILY]
    button_spec = {
        "family": BUTTON_FAMILY,
        "layer": BUTTON_LAYER,
        "alpha": BUTTON_ALPHA,
        "system_prompt": "",
        "direction_derivation": "all_directions_for_layer(layer, hidden_dim) as used by e0012_harness.run_e0012_harness",
        "derivation_hash": button_direction.derivation_hash,
        "direction_notes": button_direction.notes,
    }
    conditions.append(ComparatorCondition(
        condition_id=f"{BUTTON_FAMILY}-L{BUTTON_LAYER}-A{BUTTON_ALPHA:g}",
        source="button",
        prompt_text="",
        alpha=BUTTON_ALPHA,
        layer=BUTTON_LAYER,
        direction=button_direction.direction,
        button_spec=button_spec,
        prompt_hash=None,
    ))

    return conditions


def make_sampler(backend: str, all_items: Sequence[Dict[str, Any]], seed: int, model: Optional[str]):
    """Construct the synthetic smoke sampler or the real HF TextCapableSampler."""
    if backend == "synthetic":
        return make_synthetic_sampler(list(all_items), axis=AXIS), 16

    import torch as _torch  # noqa: PLC0415
    from cognitive_console.experiments.e0012_steer_hf import SteeredHFTextCapableSampler  # noqa: PLC0415
    from cognitive_console.steering.generate import SteeredHFBackend  # noqa: PLC0415

    if not _torch.cuda.is_available():
        raise RuntimeError("--backend hf requires cuda; E-0012-CS is frozen as fp16-on-cuda")
    model_name = model or "Qwen/Qwen2.5-7B-Instruct"
    hf_backend = SteeredHFBackend(
        model_name=model_name,
        device="cuda",
        dtype="float16",
        seed=seed,
    )
    sampler = SteeredHFTextCapableSampler(
        hf_backend,
        max_new_tokens=256,
        do_sample=True,
        temperature=0.7,
        seed=seed,
    )
    if not isinstance(sampler, TextCapableSampler):
        raise RuntimeError("HF path must use SteeredHFTextCapableSampler for real raw pairs")
    hidden_dim = int(getattr(hf_backend, "hidden_dim", HF_HIDDEN_DIM_FALLBACK))
    return sampler, hidden_dim


def score_condition(
    *,
    condition: ComparatorCondition,
    sampler: adj.OutcomeSampler,
    test_items: Sequence[Dict[str, Any]],
    raw_store: BrierRawStore,
) -> Tuple[float, int]:
    """Evaluate one condition on frozen TEST with the harness scoring path."""
    batches = _eval_items_with_raw_pairs(
        sampler=sampler,
        axis=AXIS,
        items=list(test_items),
        instruction=condition.prompt_text,
        alpha=condition.alpha,
        direction=condition.direction,
        layer=condition.layer,
        k=FROZEN_K,
        channel=condition.condition_id,
        raw_store=raw_store,
    )
    return _mean_outcome(batches), sum(len(b.outcomes) for b in batches)


def _condition_payload(condition: ComparatorCondition, score: float, n_pairs: int) -> Dict[str, Any]:
    return {
        "id": condition.condition_id,
        "source": condition.source,
        "prompt_text": condition.prompt_text,
        "prompt_hash": condition.prompt_hash,
        "button_spec": condition.button_spec,
        "test_mean_1minus_brier_k5": float(score),
        "k": FROZEN_K,
        "n_test_items": 53,
        "n_raw_pairs_expected": n_pairs,
    }


def run_comparator_strength(args: argparse.Namespace) -> Dict[str, Any]:
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_pairs_path = out_dir / "comparator_strength_raw_pairs.jsonl"
    if raw_pairs_path.exists():
        raw_pairs_path.unlink()

    seed = int(args.seed)
    t0 = time.time()
    all_items, dev_items, test_items = load_frozen_split()
    sampler, hidden_dim = make_sampler(args.backend, all_items, seed, args.model)
    conditions = build_conditions(hidden_dim=hidden_dim)

    if len(dev_items) != 27 or len(test_items) != 53:
        raise RuntimeError(f"frozen split mismatch: {len(dev_items)} DEV / {len(test_items)} TEST")
    if FROZEN_K != K_STAGE1:
        raise RuntimeError(f"E-0012-CS k={FROZEN_K} must match K_STAGE1={K_STAGE1}")
    expected_counts = {
        "synthetic_bank": FROZEN_SYNTHETIC_BANK_COUNT,
        "calibration_yaml": 18,
        "baseline": 1,
        "button": 1,
    }
    for source, expected in expected_counts.items():
        actual = sum(1 for c in conditions if c.source == source)
        if actual != expected:
            raise RuntimeError(f"condition count mismatch for {source}: {actual} != {expected}")

    condition_results: List[Dict[str, Any]] = []
    raw_store = BrierRawStore(raw_pairs_path, fresh=True)
    try:
        for condition in conditions:
            score, n_pairs = score_condition(
                condition=condition,
                sampler=sampler,
                test_items=test_items,
                raw_store=raw_store,
            )
            if args.backend == "hf" and not raw_store.has_real_pairs(condition.condition_id):
                raise RuntimeError(
                    f"HF real-pair guard failed for {condition.condition_id}: "
                    "no synthetic_proxy=false raw pairs persisted"
                )
            condition_results.append(_condition_payload(condition, score, n_pairs))
    finally:
        raw_store.close()

    max_condition = max(condition_results, key=lambda r: (r["test_mean_1minus_brier_k5"], r["id"]))
    max_human_prompt = max(
        (r for r in condition_results if r["source"] in {"synthetic_bank", "calibration_yaml"}),
        key=lambda r: (r["test_mean_1minus_brier_k5"], r["id"]),
    )
    best_synthetic = max(
        (r for r in condition_results if r["source"] == "synthetic_bank"),
        key=lambda r: (r["test_mean_1minus_brier_k5"], r["id"]),
    )
    best_calibration_yaml = max(
        (r for r in condition_results if r["source"] == "calibration_yaml"),
        key=lambda r: (r["test_mean_1minus_brier_k5"], r["id"]),
    )
    by_id = {r["id"]: r for r in condition_results}
    baseline = by_id["BASELINE-UNSTEERED-NO-PROMPT"]
    button = by_id[f"{BUTTON_FAMILY}-L{BUTTON_LAYER}-A{BUTTON_ALPHA:g}"]
    cal_09 = by_id["CAL-09"]

    summary = {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utcnow(),
        "backend": args.backend,
        "model": args.model,
        "seed": seed,
        "valid_for_paper": False,
        "purpose": "comparator-strength robustness check; can only weaken a positive E-0012 claim",
        "pool": {
            "pool_n": E0012_POOL_N,
            "pool_seed": E0012_POOL_SEED,
            "pool_offset": E0012_POOL_OFFSET,
            "split_seed": E0012_SPLIT_SEED,
            "n_dev": len(dev_items),
            "n_test": len(test_items),
            "dev_ids": [str(it["id"]) for it in dev_items],
            "test_ids": [str(it["id"]) for it in test_items],
            "dev_test_overlap_n": len({str(it["id"]) for it in dev_items} & {str(it["id"]) for it in test_items}),
        },
        "metric": "mean(1-Brier) over frozen TEST items via e0012_harness._eval_items_with_raw_pairs/_mean_outcome",
        "k": FROZEN_K,
        "condition_counts": expected_counts,
        "n_conditions": len(condition_results),
        "conditions": condition_results,
        "max_condition": {
            "id": max_condition["id"],
            "source": max_condition["source"],
            "score": max_condition["test_mean_1minus_brier_k5"],
            "prompt_text": max_condition["prompt_text"],
            "button_spec": max_condition["button_spec"],
        },
        "max_human_prompt": {
            "id": max_human_prompt["id"],
            "source": max_human_prompt["source"],
            "score": max_human_prompt["test_mean_1minus_brier_k5"],
            "prompt_text": max_human_prompt["prompt_text"],
        },
        "best_synthetic_bank": {
            "id": best_synthetic["id"],
            "score": best_synthetic["test_mean_1minus_brier_k5"],
            "text": best_synthetic["prompt_text"],
        },
        "best_calibration_yaml": {
            "id": best_calibration_yaml["id"],
            "score": best_calibration_yaml["test_mean_1minus_brier_k5"],
            "text": best_calibration_yaml["prompt_text"],
        },
        "cal_09": {
            "id": "CAL-09",
            "score": cal_09["test_mean_1minus_brier_k5"],
            "text": cal_09["prompt_text"],
        },
        "button": {
            "id": button["id"],
            "score": button["test_mean_1minus_brier_k5"],
            "spec": button["button_spec"],
        },
        "baseline": {
            "id": baseline["id"],
            "score": baseline["test_mean_1minus_brier_k5"],
        },
        "raw_pairs_path": str(raw_pairs_path),
        "wall_clock_seconds": time.time() - t0,
    }

    out_json = out_dir / "comparator_strength.json"
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def print_summary_table(summary: Dict[str, Any]) -> None:
    print("\nE-0012-CS comparator-strength summary")
    print(f"backend={summary['backend']} seed={summary['seed']} k={summary['k']} "
          f"split={summary['pool']['n_dev']} DEV / {summary['pool']['n_test']} TEST")
    print(f"{'id':<32} {'source':<18} {'TEST mean(1-Brier)':>20}")
    print("-" * 74)
    for row in sorted(summary["conditions"], key=lambda r: r["test_mean_1minus_brier_k5"], reverse=True):
        print(f"{row['id']:<32} {row['source']:<18} {row['test_mean_1minus_brier_k5']:>20.6f}")
    print("-" * 74)
    print("MAX:", json.dumps(summary["max_condition"], ensure_ascii=False))
    print("max_human_prompt:", json.dumps(summary["max_human_prompt"], ensure_ascii=False))
    print("best_synthetic_bank:", json.dumps(summary["best_synthetic_bank"], ensure_ascii=False))
    print("best_calibration_yaml:", json.dumps(summary["best_calibration_yaml"], ensure_ascii=False))
    print("CAL-09:", json.dumps(summary["cal_09"], ensure_ascii=False))
    print("button:", json.dumps(summary["button"], ensure_ascii=False))
    print("baseline:", json.dumps(summary["baseline"], ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run E-0012-CS comparator-strength check")
    parser.add_argument("--backend", choices=["synthetic", "hf"], default="synthetic")
    parser.add_argument("--output-dir", default=str(_REPO / "results" / "E-0012-CS"))
    parser.add_argument("--seed", type=int, default=RUN_SEED)
    parser.add_argument("--model", default=None, help="HF model id for --backend hf")
    args = parser.parse_args()
    summary = run_comparator_strength(args)
    print_summary_table(summary)


if __name__ == "__main__":
    main()
