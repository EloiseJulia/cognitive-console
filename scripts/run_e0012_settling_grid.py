"""E-0012-SG settling grid.

Frozen descriptive TEST-only grid for closing the E-0012 A-lite audit's
UNVERIFIED-1: pure real BTN-CAL-PROBE steering was not measured.  This script
reuses the E-0012 harness scoring path, split loader, OutcomeSampler seam, and
Brier raw-pair store used by the verified-control and comparator-strength runs.
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
from cognitive_console.experiments.e0012_ape import _SYNTHETIC_APE_CANDIDATES, normalized_prompt_hash
from cognitive_console.experiments.e0012_brier import BrierRawPair, BrierRawStore
from cognitive_console.experiments.e0012_buttons import (
    BTN_PROBE,
    ButtonDirection,
    all_directions_for_layer,
    derive_probe_direction_real,
)
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
    load_triviaqa_train_for_probe,
)
from cognitive_console.lineage import utcnow

from run_e0012_verified_control import load_authored_prompts, make_synthetic_sampler


EXPERIMENT_ID = "E-0012-SG"
AXIS = "uncertainty_awareness"
RUN_SEED = 42
FROZEN_K = 5
PROBE_LAYER = 18
PROBE_ALPHA = 24.0
SYNTH_BANK_INDEX = 26
HF_HIDDEN_DIM_FALLBACK = 3584
DEFAULT_MODEL = "Qwen/Qwen2.5-7B-Instruct"
DEFAULT_PROVENANCE_PATH = _REPO / "results" / "E-0012" / "direction_provenance.json"


@dataclass(frozen=True)
class SettlingCondition:
    """One frozen E-0012-SG cell."""

    condition_id: str
    prompt_label: str
    prompt_text: str
    steering: str
    alpha: float
    layer: int
    direction: np.ndarray
    prompt_hash: Optional[str]
    direction_vector_sha256: Optional[str]


def load_frozen_split() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Load the frozen E-0012 fixture and DEV/TEST split used by A-lite/CS."""
    all_items = load_e0012_pool(use_fixture=True)
    dev_items, test_items = split_e0012_pool(all_items, split_seed=E0012_SPLIT_SEED)
    return all_items, dev_items, test_items


def load_cal09_prompt() -> str:
    authored = dict(load_authored_prompts())
    if "CAL-09" not in authored:
        raise ValueError("CAL-09 missing from calibration_prompts.yaml")
    return authored["CAL-09"]


def load_synth_bank_26_prompt() -> str:
    if len(_SYNTHETIC_APE_CANDIDATES) <= SYNTH_BANK_INDEX:
        raise ValueError(f"_SYNTHETIC_APE_CANDIDATES missing index {SYNTH_BANK_INDEX}")
    return _SYNTHETIC_APE_CANDIDATES[SYNTH_BANK_INDEX]


def load_alite_probe_l18_hash(path: Path = DEFAULT_PROVENANCE_PATH) -> str:
    """Read the frozen A-lite real_probe@layer18 vector SHA-256 from provenance."""
    records = json.loads(Path(path).read_text(encoding="utf-8"))
    matches = [
        rec for rec in records
        if rec.get("method") == "real_probe"
        and rec.get("family") == BTN_PROBE
        and int(rec.get("layer", -1)) == PROBE_LAYER
    ]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one real_probe {BTN_PROBE}@L{PROBE_LAYER}; got {len(matches)}")
    vector_sha = str(matches[0].get("vector_sha256", ""))
    if not vector_sha:
        raise ValueError(f"A-lite provenance record for {BTN_PROBE}@L{PROBE_LAYER} lacks vector_sha256")
    return vector_sha


def assert_matching_alite_direction(direction: ButtonDirection, expected_vector_sha256: str) -> str:
    """Hard-fail unless the freshly derived real direction equals A-lite provenance."""
    actual = str(direction.provenance.get("vector_sha256", ""))
    if not actual:
        raise RuntimeError("freshly derived direction is missing vector_sha256")
    if actual != expected_vector_sha256:
        raise RuntimeError(
            "E-0012-SG direction mismatch: freshly derived "
            f"{BTN_PROBE}@L{PROBE_LAYER} vector_sha256={actual} != "
            f"A-lite provenance vector_sha256={expected_vector_sha256}. "
            "Refusing to score a different direction."
        )
    return actual


def derive_real_probe_l18_with_assertion(
    *,
    activation_provider: Any,
    triviaqa_train_items: Sequence[Dict[str, Any]],
    provenance_path: Path = DEFAULT_PROVENANCE_PATH,
) -> Tuple[ButtonDirection, str]:
    """Derive the real probe direction via the A-lite path and assert exact hash."""
    expected = load_alite_probe_l18_hash(provenance_path)
    direction = derive_probe_direction_real(
        layer=PROBE_LAYER,
        activation_provider=activation_provider,
        triviaqa_train_items=triviaqa_train_items,
        seed=RUN_SEED,
    )
    actual = assert_matching_alite_direction(direction, expected)
    return direction, actual


def build_conditions(probe_direction: Optional[ButtonDirection] = None, hidden_dim: int = 16) -> List[SettlingCondition]:
    """Build exactly the frozen 3 prompts × 2 steering-state grid."""
    zero_dir = np.zeros(1)
    if probe_direction is None:
        layer_dirs = all_directions_for_layer(PROBE_LAYER, hidden_dim, families=(BTN_PROBE,))
        probe_direction = layer_dirs[0]
    probe_vec = probe_direction.direction
    probe_sha = str(probe_direction.provenance.get("vector_sha256", ""))

    prompts = [
        ("empty", ""),
        ("CAL-09", load_cal09_prompt()),
        ("SYNTH-BANK-26", load_synth_bank_26_prompt()),
    ]
    conditions: List[SettlingCondition] = []
    for prompt_label, prompt_text in prompts:
        prompt_hash = normalized_prompt_hash(prompt_text) if prompt_text else None
        conditions.append(SettlingCondition(
            condition_id=f"{prompt_label}__none",
            prompt_label=prompt_label,
            prompt_text=prompt_text,
            steering="none",
            alpha=0.0,
            layer=0,
            direction=zero_dir,
            prompt_hash=prompt_hash,
            direction_vector_sha256=None,
        ))
        conditions.append(SettlingCondition(
            condition_id=f"{prompt_label}__probe_L18_a24",
            prompt_label=prompt_label,
            prompt_text=prompt_text,
            steering="probe_L18_a24",
            alpha=PROBE_ALPHA,
            layer=PROBE_LAYER,
            direction=probe_vec,
            prompt_hash=prompt_hash,
            direction_vector_sha256=probe_sha,
        ))
    if len(conditions) != 6:
        raise RuntimeError(f"E-0012-SG must build exactly 6 conditions; got {len(conditions)}")
    return conditions


def make_sampler_and_direction(
    backend: str,
    all_items: Sequence[Dict[str, Any]],
    seed: int,
    model: Optional[str],
    output_dir: Path,
    provenance_path: Path,
) -> Tuple[adj.OutcomeSampler, int, Optional[ButtonDirection], Dict[str, Any]]:
    """Construct sampler plus the asserted real direction for HF runs."""
    if backend == "synthetic":
        return make_synthetic_sampler(list(all_items), axis=AXIS), 16, None, {
            "performed": False,
            "reason": "synthetic smoke uses synthetic BTN-CAL-PROBE direction; HF run asserts A-lite hash",
            "expected_alite_vector_sha256": load_alite_probe_l18_hash(provenance_path),
        }

    import torch as _torch  # noqa: PLC0415
    from cognitive_console.activations.provider import HFActivationProvider  # noqa: PLC0415
    from cognitive_console.experiments.e0012_steer_hf import SteeredHFTextCapableSampler  # noqa: PLC0415
    from cognitive_console.steering.generate import SteeredHFBackend  # noqa: PLC0415

    if not _torch.cuda.is_available():
        raise RuntimeError("--backend hf requires CUDA; E-0012-SG is frozen as fp16-on-cuda")
    model_name = model or DEFAULT_MODEL
    hf_backend = SteeredHFBackend(model_name=model_name, device="cuda", dtype="float16", seed=seed)
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
    activation_provider = HFActivationProvider(
        model_name=model_name,
        layers=[PROBE_LAYER],
        device="cuda",
        dtype="float16",
        cache_dir=str(output_dir / "activation_cache"),
    )
    triviaqa_train_items = load_triviaqa_train_for_probe(n=200, seed=RUN_SEED)
    direction, actual_sha = derive_real_probe_l18_with_assertion(
        activation_provider=activation_provider,
        triviaqa_train_items=triviaqa_train_items,
        provenance_path=provenance_path,
    )
    return sampler, hidden_dim, direction, {
        "performed": True,
        "expected_alite_vector_sha256": load_alite_probe_l18_hash(provenance_path),
        "actual_vector_sha256": actual_sha,
        "matched": True,
        "derivation": "derive_probe_direction_real(layer=18, TriviaQA-train pairs, seed=42)",
    }


def _per_item_from_pairs(pairs: Sequence[BrierRawPair], test_items: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_id: Dict[str, List[BrierRawPair]] = {}
    for pair in pairs:
        by_id.setdefault(str(pair.item_id), []).append(pair)
    rows: List[Dict[str, Any]] = []
    for item in test_items:
        item_id = str(item["id"])
        item_pairs = by_id.get(item_id, [])
        if len(item_pairs) != FROZEN_K:
            raise RuntimeError(f"condition has {len(item_pairs)} raw pairs for item {item_id}; expected k={FROZEN_K}")
        values = [float(p.one_minus_brier) for p in item_pairs]
        rows.append({
            "item_id": item_id,
            "mean_1minus_brier": float(np.mean(values)),
            "raw_pairs": [p.to_dict() for p in item_pairs],
        })
    return rows


def score_condition(
    *,
    condition: SettlingCondition,
    sampler: adj.OutcomeSampler,
    test_items: Sequence[Dict[str, Any]],
    raw_store: BrierRawStore,
    require_real_pairs: bool,
) -> Dict[str, Any]:
    """Evaluate one grid condition on frozen TEST with the harness scoring path."""
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
    if require_real_pairs and not raw_store.has_real_pairs(condition.condition_id):
        raise RuntimeError(
            f"HF real-pair guard failed for {condition.condition_id}: "
            "no synthetic_proxy=false raw pairs persisted"
        )
    pairs = raw_store.filter_channel(condition.condition_id)
    per_item = _per_item_from_pairs(pairs, test_items)
    return {
        "id": condition.condition_id,
        "prompt_label": condition.prompt_label,
        "prompt_text": condition.prompt_text,
        "prompt_hash": condition.prompt_hash,
        "steering": condition.steering,
        "alpha": condition.alpha,
        "layer": condition.layer,
        "direction_vector_sha256": condition.direction_vector_sha256,
        "test_mean_1minus_brier_k5": _mean_outcome(batches),
        "per_item": per_item,
    }


def _per_item_means(row: Dict[str, Any]) -> Dict[str, float]:
    return {str(item["item_id"]): float(item["mean_1minus_brier"]) for item in row["per_item"]}


def paired_delta_with_ci(
    treatment: Dict[str, Any],
    control: Dict[str, Any],
    *,
    bootstrap_b: int,
    seed: int,
) -> Dict[str, Any]:
    t = _per_item_means(treatment)
    c = _per_item_means(control)
    ids = sorted(t)
    if ids != sorted(c):
        raise RuntimeError(f"paired delta item mismatch: {treatment['id']} vs {control['id']}")
    diffs = np.asarray([t[item_id] - c[item_id] for item_id in ids], dtype=np.float64)
    ci = adj.cluster_bootstrap_ci(diffs, b=bootstrap_b, ci_level=0.95, seed=seed, cluster=True)
    return {
        "treatment_id": treatment["id"],
        "control_id": control["id"],
        "mean_delta": float(ci.point),
        "ci95": [float(ci.ci_lo), float(ci.ci_hi)],
        "bootstrap_b": int(ci.b),
        "bootstrap_seed": int(seed),
        "n_items": len(ids),
        "cluster": bool(ci.cluster),
    }


def compute_deltas(condition_results: Sequence[Dict[str, Any]], *, bootstrap_b: int, seed: int) -> Dict[str, Any]:
    by_id = {row["id"]: row for row in condition_results}
    best_steered = max(
        (row for row in condition_results if row["steering"] == "probe_L18_a24"),
        key=lambda r: (r["test_mean_1minus_brier_k5"], r["id"]),
    )
    best_prompt_only = max(
        (row for row in condition_results if row["steering"] == "none"),
        key=lambda r: (r["test_mean_1minus_brier_k5"], r["id"]),
    )
    return {
        "empty_probe_minus_empty": paired_delta_with_ci(
            by_id["empty__probe_L18_a24"], by_id["empty__none"], bootstrap_b=bootstrap_b, seed=seed
        ),
        "CAL09_probe_minus_CAL09": paired_delta_with_ci(
            by_id["CAL-09__probe_L18_a24"], by_id["CAL-09__none"], bootstrap_b=bootstrap_b, seed=seed + 1
        ),
        "SYNTH26_probe_minus_SYNTH26": paired_delta_with_ci(
            by_id["SYNTH-BANK-26__probe_L18_a24"], by_id["SYNTH-BANK-26__none"], bootstrap_b=bootstrap_b, seed=seed + 2
        ),
        "best_steered_minus_best_prompt_only": paired_delta_with_ci(
            best_steered, best_prompt_only, bootstrap_b=bootstrap_b, seed=seed + 3
        ),
        "best_steered_config": {
            "id": best_steered["id"],
            "prompt_label": best_steered["prompt_label"],
            "score": best_steered["test_mean_1minus_brier_k5"],
        },
        "best_prompt_only_config": {
            "id": best_prompt_only["id"],
            "prompt_label": best_prompt_only["prompt_label"],
            "score": best_prompt_only["test_mean_1minus_brier_k5"],
        },
    }


def run_settling_grid(args: argparse.Namespace) -> Dict[str, Any]:
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_pairs_path = out_dir / "settling_grid_raw_pairs.jsonl"
    if raw_pairs_path.exists():
        raw_pairs_path.unlink()

    t0 = time.time()
    seed = int(args.seed)
    all_items, dev_items, test_items = load_frozen_split()
    if len(all_items) != E0012_POOL_N or len(dev_items) != 27 or len(test_items) != 53:
        raise RuntimeError(f"frozen split mismatch: pool={len(all_items)} DEV={len(dev_items)} TEST={len(test_items)}")
    dev_ids = {str(it["id"]) for it in dev_items}
    test_ids = {str(it["id"]) for it in test_items}
    if dev_ids & test_ids:
        raise RuntimeError("frozen split invalid: DEV/TEST overlap is non-zero")
    if FROZEN_K != K_STAGE1:
        raise RuntimeError(f"E-0012-SG k={FROZEN_K} must match K_STAGE1={K_STAGE1}")

    sampler, hidden_dim, probe_direction, hash_assertion = make_sampler_and_direction(
        args.backend,
        all_items,
        seed,
        args.model,
        out_dir,
        Path(args.provenance_path),
    )
    conditions = build_conditions(probe_direction=probe_direction, hidden_dim=hidden_dim)
    if len(conditions) != 6:
        raise RuntimeError(f"E-0012-SG expected exactly 6 conditions; got {len(conditions)}")

    condition_results: List[Dict[str, Any]] = []
    raw_store = BrierRawStore(raw_pairs_path, fresh=True)
    try:
        for condition in conditions:
            condition_results.append(score_condition(
                condition=condition,
                sampler=sampler,
                test_items=test_items,
                raw_store=raw_store,
                require_real_pairs=(args.backend == "hf"),
            ))
    finally:
        raw_store.close()

    deltas = compute_deltas(condition_results, bootstrap_b=int(args.bootstrap_b), seed=seed)
    summary = {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utcnow(),
        "backend": args.backend,
        "model": args.model or (DEFAULT_MODEL if args.backend == "hf" else None),
        "seed": seed,
        "valid_for_paper": False,
        "purpose": "frozen descriptive settling grid for E-0012 A-lite UNVERIFIED-1",
        "anti_forking_paths": "All 6 cells are evaluated once on TEST; no selection, tuning, or DEV scoring.",
        "pool": {
            "pool_n": E0012_POOL_N,
            "pool_seed": E0012_POOL_SEED,
            "pool_offset": E0012_POOL_OFFSET,
            "split_seed": E0012_SPLIT_SEED,
            "n_dev": len(dev_items),
            "n_test": len(test_items),
            "dev_test_overlap_n": len(dev_ids & test_ids),
            "dev_ids": sorted(dev_ids),
            "test_ids": [str(it["id"]) for it in test_items],
        },
        "sampler_settings": {
            "k": FROZEN_K,
            "max_new_tokens": 256,
            "do_sample": True,
            "temperature": 0.7,
            "fp16_cuda_required_for_hf": True,
        },
        "direction": {
            "family": BTN_PROBE,
            "layer": PROBE_LAYER,
            "alpha": PROBE_ALPHA,
            "synthetic_proxy": args.backend == "synthetic",
            "hash_assertion": hash_assertion,
        },
        "conditions": condition_results,
        "deltas": deltas,
        "raw_pairs_path": str(raw_pairs_path),
        "wall_clock_seconds": time.time() - t0,
    }
    out_json = out_dir / "settling_grid.json"
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def print_summary_table(summary: Dict[str, Any]) -> None:
    print("\nE-0012-SG settling-grid summary")
    print(f"backend={summary['backend']} seed={summary['seed']} k={summary['sampler_settings']['k']} "
          f"split={summary['pool']['n_dev']} DEV / {summary['pool']['n_test']} TEST")
    print(f"{'id':<32} {'prompt':<14} {'steering':<16} {'TEST mean(1-Brier)':>20}")
    print("-" * 88)
    for row in summary["conditions"]:
        print(f"{row['id']:<32} {row['prompt_label']:<14} {row['steering']:<16} "
              f"{row['test_mean_1minus_brier_k5']:>20.6f}")
    print("-" * 88)
    print("deltas:", json.dumps(summary["deltas"], ensure_ascii=False))
    print("direction:", json.dumps(summary["direction"], ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run frozen E-0012-SG settling grid")
    parser.add_argument("--backend", choices=["synthetic", "hf"], default="synthetic")
    parser.add_argument("--output-dir", default=str(_REPO / "results" / "E-0012-SG"))
    parser.add_argument("--seed", type=int, default=RUN_SEED)
    parser.add_argument("--model", default=None, help="HF model id for --backend hf")
    parser.add_argument("--bootstrap-b", type=int, default=10000)
    parser.add_argument("--provenance-path", default=str(DEFAULT_PROVENANCE_PATH))
    args = parser.parse_args()
    summary = run_settling_grid(args)
    print_summary_table(summary)


if __name__ == "__main__":
    main()
