"""E-0012 Verified Control Button — main runner script.

Usage (synthetic smoke, no GPU):
  python scripts/run_e0012_verified_control.py --backend synthetic --output-dir results/e0012_smoke

Usage (generate fixture, needs network):
  python scripts/run_e0012_verified_control.py --generate-fixture

Usage (real GPU, A800):
  python scripts/run_e0012_verified_control.py --backend hf --model Qwen/Qwen2.5-7B-Instruct
    --output-dir results/e0012_<date>

Flags:
  --backend synthetic|hf  : backend (default: synthetic)
  --generate-fixture      : download and save TriviaQA fixture for offline use (requires network)
  --output-dir DIR        : where to write results
  --stage0-only           : run Stage 0 only (no Stage 1)
  --seed INT              : run seed (default: 42)
  --model STR             : HF model id (hf backend only)
  --n-items INT           : override pool size (synthetic only; for quick smoke)
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

import numpy as np

from cognitive_console.experiments import adjudicate_c2b as adj
from cognitive_console.experiments.e0012_harness import (
    run_e0012_harness,
    split_e0012_pool,
    L_C1,
    LAYER_SWEEP,
    ALPHA_GRID,
    N_SEARCH_CAP,
    CROSS_AXIS_SKIP_REASON,
    VERDICT_NO_BUTTON_FOUND,
    VERDICT_BUTTON_FOUND_BUT_UNSAFE,
    VERDICT_TRANSFER,
)
from cognitive_console.experiments.e0012_ape import (
    APE_N_CAND,
    APE_SEED,
    generate_candidates_synthetic,
    generate_candidates_real,
    run_ape,
    frozen_meta_prompt,
    normalized_prompt_hash,
)
from cognitive_console.experiments.e0012_brier import BrierRawStore
from cognitive_console.eval.e0012_triviaqa import (
    E0012_POOL_N,
    E0012_POOL_SEED,
    E0012_POOL_OFFSET,
    E0012_SPLIT_SEED,
    load_e0012_pool,
    save_fixture,
    load_e0012_triviaqa_real,
    load_triviaqa_train_for_probe,
    load_e0006_dev_baseline_scores,
)
from cognitive_console.lineage import utcnow


def load_authored_prompts(data_root: Optional[Path] = None) -> List[Tuple[str, str]]:
    """Load authored calibration prompts from data/e0012_prompts/calibration_prompts.yaml."""
    import yaml  # noqa: PLC0415
    root = data_root or (_REPO / "data")
    path = root / "e0012_prompts" / "calibration_prompts.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Calibration prompts file not found: {path}")
    with open(path, encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    prompts = doc.get("prompts", [])
    return [(p["id"], p["text"].strip()) for p in prompts]


def make_synthetic_pool(n: int = 10, seed: int = 0) -> List[Dict[str, Any]]:
    """Create a minimal synthetic pool for smoke testing (no network)."""
    rng = np.random.default_rng(seed)
    items = []
    answers = ["Paris", "London", "Tokyo", "Berlin", "Rome", "Madrid",
               "Ottawa", "Canberra", "Brasilia", "Cairo"]
    for i in range(n):
        answer = answers[i % len(answers)]
        items.append({
            "id": f"e0012-smoke-{i:04d}",
            "prompt": f"What is the capital city number {i + 1}?",
            "answer": answer,
            "aliases": [answer.lower()],
        })
    return items


def make_synthetic_sampler(items: List[Dict], axis: str = "uncertainty_awareness"):
    """Create a synthetic backend sampler for smoke testing."""
    from cognitive_console.steering.generate import SyntheticC2bTaskBackend  # noqa
    backend = SyntheticC2bTaskBackend(
        axis=axis,
        items=items,
        prompt_gain=0.3,
        alpha_gain=0.08,
        threshold=0.35,
        degenerate_alpha=20.0,
    )
    return adj.BackendOutcomeSampler(backend, max_new_tokens=128, do_sample=False)


def cmd_generate_fixture(args: argparse.Namespace) -> None:
    """Download and save the E-0012 TriviaQA fixture."""
    print(f"Downloading TriviaQA validation split (offset={E0012_POOL_OFFSET}, "
          f"seed={E0012_POOL_SEED}, N={E0012_POOL_N})...")
    items = load_e0012_triviaqa_real()
    out_path = save_fixture(items)
    print(f"Saved {len(items)} items to {out_path}")


def cmd_run(args: argparse.Namespace) -> None:
    """Main experiment run (synthetic or hf backend)."""
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    run_seed = int(args.seed)
    t0 = time.time()

    print(f"[e0012] backend={args.backend!r} output={out_dir} seed={run_seed}")
    print(f"[e0012] L_c1={L_C1} layer_sweep={LAYER_SWEEP} alpha_grid={ALPHA_GRID}")
    print(f"[e0012] N_search_cap={N_SEARCH_CAP}")

    # ── Load pool ──────────────────────────────────────────────────────────── #
    if args.backend == "synthetic":
        n_items = int(args.n_items) if args.n_items else 12
        all_items = make_synthetic_pool(n=n_items, seed=run_seed)
        print(f"[e0012] Synthetic pool: {len(all_items)} items")
    else:
        all_items = load_e0012_pool(use_fixture=True)
        print(f"[e0012] Loaded E-0012 pool: {len(all_items)} items")

    dev_items, test_items = split_e0012_pool(all_items, split_seed=E0012_SPLIT_SEED)
    print(f"[e0012] Split: {len(dev_items)} DEV / {len(test_items)} TEST")

    # ── Load authored prompts ──────────────────────────────────────────────── #
    authored_prompts = load_authored_prompts()
    print(f"[e0012] Loaded {len(authored_prompts)} authored calibration prompts")

    # ── Create sampler ─────────────────────────────────────────────────────── #
    if args.backend == "synthetic":
        sampler = make_synthetic_sampler(all_items)
        hidden_dim = 16
    else:
        import torch as _torch  # noqa
        from cognitive_console.steering.generate import SteeredHFBackend  # noqa
        from cognitive_console.experiments.e0012_steer_hf import SteeredHFTextCapableSampler  # noqa
        from cognitive_console.activations.provider import HFActivationProvider  # noqa
        model_name = args.model or "Qwen/Qwen2.5-7B-Instruct"
        _hf_device = "cuda" if _torch.cuda.is_available() else "cpu"
        _hf_dtype = "float16" if _hf_device == "cuda" else "float32"
        print(f"[e0012] device={_hf_device!r} (CUDA_VISIBLE_DEVICES={__import__('os').environ.get('CUDA_VISIBLE_DEVICES','unset')!r})")
        hf_backend = SteeredHFBackend(model_name=model_name, device=_hf_device,
                                       dtype=_hf_dtype)
        # N-01 fix: wrap in SteeredHFTextCapableSampler (not BackendOutcomeSampler)
        # so _eval_items_with_raw_pairs records real (confidence, correctness) pairs
        # (synthetic_proxy=False) for the §9.2 Brier safety guards.
        sampler = SteeredHFTextCapableSampler(
            hf_backend, max_new_tokens=256, do_sample=True,
            temperature=0.7, seed=run_seed
        )
        # Assert GPU path is TextCapableSampler so hard-fail guard in
        # run_stage1_candidate() can enforce real-pair requirement.
        from cognitive_console.experiments.e0012_harness import TextCapableSampler  # noqa
        assert isinstance(sampler, TextCapableSampler), (
            "GPU run requires a TextCapableSampler; got " + type(sampler).__name__
        )
        hidden_dim = 3584  # Qwen2.5-7B hidden dim
        activation_provider = HFActivationProvider(
            model_name=model_name,
            layers=LAYER_SWEEP,
            device=_hf_device,
            dtype=_hf_dtype,
            cache_dir=str(out_dir / "activation_cache"),
        )
        triviaqa_train_items = load_triviaqa_train_for_probe(n=200, seed=42)
        e0006_path_arg = getattr(args, "e0006_dev_baseline_jsonl", None) or (
            "data/e0006_uncertainty_baseline/e0006_uncertainty_baseline.jsonl"
        )
        e0006_dev_items = load_e0006_dev_baseline_scores(
            Path(e0006_path_arg), validate_item_source=True
        )
    if args.backend == "synthetic":
        activation_provider = None
        triviaqa_train_items = None
        e0006_dev_items = None

    # ── APE run ────────────────────────────────────────────────────────────── #
    print(f"[e0012] Running APE (N_cand={APE_N_CAND}, seed={APE_SEED})")
    axis = "uncertainty_awareness"
    if args.backend == "synthetic":
        candidates = generate_candidates_synthetic(APE_N_CAND, APE_SEED)
        raw_model_output = "SYNTHETIC_OFFLINE_GENERATOR"
        candidate_provenance = [
            {
                "candidate_id": i,
                "text": text,
                "source": "model",
                "normalized_hash": normalized_prompt_hash(text),
            }
            for i, text in enumerate(candidates)
        ]
        n_model_parseable = len(candidates)
        n_cand_padded = 0
    else:
        # F-01: §5-B protocol compliance — generate via frozen meta-prompt using the real model,
        # not the pre-authored calibration bank. authored_texts serves as §5-B pad-fallback only.
        authored_texts = [text for _, text in authored_prompts]
        try:
            gen_trace = generate_candidates_real(hf_backend, APE_N_CAND, APE_SEED,
                                                 authored_prompts=authored_texts,
                                                 return_trace=True)
        except TypeError:
            gen_trace = generate_candidates_real(hf_backend, APE_N_CAND, APE_SEED,
                                                 authored_prompts=authored_texts)
        if hasattr(gen_trace, "texts"):
            candidates = gen_trace.texts
            raw_model_output = gen_trace.raw_model_output
            candidate_provenance = gen_trace.candidates
            n_model_parseable = gen_trace.n_model_parseable
            n_cand_padded = gen_trace.n_padded
        else:
            candidates = list(gen_trace)
            raw_model_output = ""
            candidate_provenance = [
                {
                    "candidate_id": i,
                    "text": text,
                    "source": "model",
                    "normalized_hash": normalized_prompt_hash(text),
                }
                for i, text in enumerate(candidates)
            ]
            n_model_parseable = len(candidates)
            n_cand_padded = 0

    # Use first authored prompt layer/direction for APE screening
    layer_for_ape = L_C1
    ape_result = run_ape(
        candidates=candidates,
        dev_items=dev_items,
        sampler=sampler,
        axis=axis,
        direction=np.zeros(1),
        layer=layer_for_ape,
        authored_count=n_cand_padded,
        raw_model_output=raw_model_output,
        candidate_provenance=candidate_provenance,
        n_model_parseable=n_model_parseable,
    )
    print(f"[e0012] APE winner DEV score (k=3): {ape_result.auto_prompt_dev_score_k3:.4f}")
    print(f"[e0012] APE winner DEV score (k=5): {ape_result.auto_prompt_dev_score_k5:.4f}")

    # ── Raw pair store ─────────────────────────────────────────────────────── #
    raw_store_path = out_dir / "brier_raw_pairs.jsonl"

    # ── Full harness ───────────────────────────────────────────────────────── #
    print("[e0012] Running Stage 0 + Stage 1...")
    verdict_obj = run_e0012_harness(
        sampler=sampler,
        dev_items=dev_items,
        test_items=test_items if not args.stage0_only else [],
        authored_prompts=authored_prompts,
        hidden_dim=hidden_dim,
        ape_result=ape_result,
        axis=axis,
        raw_store_path=raw_store_path,
        e0006_dev_items=e0006_dev_items,
        activation_provider=activation_provider,
        triviaqa_train_items=triviaqa_train_items,
        direction_provenance_path=out_dir / "direction_provenance.json",
    )
    wall_clock = time.time() - t0

    # ── Write results ──────────────────────────────────────────────────────── #
    print(f"\n[e0012] ═══ VERDICT: {verdict_obj.verdict} ═══")
    if verdict_obj.notes:
        print(f"[e0012] Notes: {verdict_obj.notes}")

    stage0 = verdict_obj.stage0
    if stage0:
        n_pass = sum(1 for c in stage0.all_candidates if c.passes_cutoff)
        print(f"[e0012] Stage 0: {stage0.n_search}/{N_SEARCH_CAP} combinations evaluated, "
              f"{n_pass} pass cutoff, {len(stage0.advancing)} advancing to Stage 1")
        print(f"[e0012] Kill rule: {stage0.kill_rule_result}")

    for r in verdict_obj.stage1_results:
        print(f"[e0012] Stage 1 candidate {r.candidate.button_family}@"
              f"layer={r.candidate.layer} α={r.candidate.alpha}: "
              f"{'PASS' if r.passes else 'FAIL'} (safety_unsafe={r.safety.button_found_but_unsafe})")

    # F-03: persist button best DEV k5 for independent kill-rule reconstruction
    # (exactly one candidate has dev_score_steer_k5 set: the best advancing before kill rule)
    button_best_dev_k5 = None
    button_best_k5_family_layer_alpha = None
    if stage0:
        k5_candidates = [c for c in stage0.all_candidates if c.dev_score_steer_k5 is not None]
        if k5_candidates:
            k5_cand = k5_candidates[0]
            button_best_dev_k5 = round(k5_cand.dev_score_steer_k5, 4)
            button_best_k5_family_layer_alpha = (
                f"{k5_cand.button_family}@layer={k5_cand.layer}@alpha={k5_cand.alpha}"
            )

    # F-04: persist APE winner prompt text and candidate id
    ape_winner_prompt_text = ape_result.auto_prompt_text if ape_result else None
    ape_winner_candidate_id = None
    if ape_result:
        for _ev in ape_result.all_candidate_evals:
            if _ev.prompt_text == ape_result.auto_prompt_text:
                ape_winner_candidate_id = _ev.candidate_id
                break

    def _int_attr(obj: Any, name: str, default: int) -> int:
        value = getattr(obj, name, default)
        return value if isinstance(value, int) else default

    def _str_attr(obj: Any, name: str, default: str) -> str:
        value = getattr(obj, name, default)
        return value if isinstance(value, str) else default

    def _list_attr(obj: Any, name: str, default: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        value = getattr(obj, name, default)
        return value if isinstance(value, list) else default

    # Serialize results
    result_dict = {
        "experiment_id": f"e0012-{date.today().isoformat()}",
        "generated_at": utcnow(),
        "verdict": verdict_obj.verdict,
        "notes": verdict_obj.notes,
        "backend": args.backend,
        "valid_for_paper": False,  # F-02: set True only via Manager review in ledger, never auto
        "l_c1": L_C1,
        "layer_sweep": list(LAYER_SWEEP),
        "alpha_grid": list(ALPHA_GRID),
        "n_search_cap": N_SEARCH_CAP,
        "pool_seed": E0012_POOL_SEED,
        "pool_offset": E0012_POOL_OFFSET,
        "n_dev": len(dev_items),
        "n_test": len(test_items),
        "ape_winner_dev_k3": ape_result.auto_prompt_dev_score_k3,
        "ape_winner_dev_k5": ape_result.auto_prompt_dev_score_k5,
        "ape_winner_prompt_text": ape_winner_prompt_text,           # F-04
        "ape_winner_candidate_id": ape_winner_candidate_id,         # F-04
        "n_cand_generated": _int_attr(ape_result, "n_cand_generated", len(candidates)),
        "n_cand_padded": _int_attr(ape_result, "n_cand_padded", n_cand_padded),
        "button_best_dev_k5": button_best_dev_k5,                   # F-03
        "button_best_k5_family_layer_alpha": button_best_k5_family_layer_alpha,  # F-03
        "kill_rule": stage0.kill_rule_result if stage0 else "N/A",
        "n_stage0_candidates_total": len(stage0.all_candidates) if stage0 else 0,
        "n_stage0_passing_cutoff": sum(1 for c in stage0.all_candidates if c.passes_cutoff) if stage0 else 0,
        "n_stage1_candidates": len(verdict_obj.stage1_results),
        "stage1_passes": [r.passes for r in verdict_obj.stage1_results],
        "cross_axis_check": (
            "SKIPPED"
            if not verdict_obj.stage1_results
            or all(r.cross_axis_check == "SKIPPED" for r in verdict_obj.stage1_results)
            else "CHECKED"
        ),
        "cross_axis_skip_reason": CROSS_AXIS_SKIP_REASON,
        "stage1_results_detail": [
            {
                "family": r.candidate.button_family,
                "layer": r.candidate.layer,
                "alpha": r.candidate.alpha,
                "passes": r.passes,
                "coherence_ok": bool(
                    r.axis_adj_result.get("coherence_ok", False)
                    if isinstance(r.axis_adj_result, dict) else False
                ),
                "coherence_ratio": r.coherence_ratio,
                "coherence_degeneracy_steer": r.coherence_degeneracy_steer,
                "coherence_degeneracy_baseline": r.coherence_degeneracy_baseline,
                "cross_axis_check": r.cross_axis_check,
                "cross_axis_skip_reason": r.cross_axis_skip_reason,
                "cross_axis_deltas": r.safety.cross_axis_deltas,
                "safety": {
                    "accuracy_guard_ok": r.safety.accuracy_guard_ok,
                    "accuracy_steer": r.safety.accuracy_steer,
                    "accuracy_baseline": r.safety.accuracy_baseline,
                    "reliability_guard_triggered": r.safety.reliability_guard_triggered,
                    "gaming_test_triggered": r.safety.gaming_test_triggered,
                    "cross_axis_check": r.cross_axis_check,
                    "cross_axis_skip_reason": r.cross_axis_skip_reason,
                    "cross_axis_fail": r.safety.cross_axis_fail,
                    "cross_axis_deltas": r.safety.cross_axis_deltas,
                    "button_found_but_unsafe": r.safety.button_found_but_unsafe,
                    "reasons": r.safety.reasons,
                },
                "safety_reasons": r.safety.reasons,
            }
            for r in verdict_obj.stage1_results
        ],
        "wall_clock_seconds": wall_clock,
        "brier_raw_pairs_path": str(raw_store_path),
        "direction_provenance_path": str(out_dir / "direction_provenance.json"),
    }

    out_json = out_dir / "e0012_results.json"
    out_json.write_text(json.dumps(result_dict, indent=2), encoding="utf-8")
    print(f"[e0012] Results written to {out_json}")

    # Stage 0 full candidate table
    if stage0:
        stage0_table = [
            {
                "family": c.button_family,
                "layer": c.layer,
                "alpha": c.alpha,
                "dev_score_steer": round(c.dev_score_steer, 4),
                "dev_score_prompt": round(c.dev_score_prompt, 4),
                "dev_improvement": round(c.dev_improvement, 4),
                "coherence_ok": c.coherence_ok,
                "coherence_ratio": c.coherence_ratio,
                "coherence_degeneracy_steer": c.coherence_degeneracy_steer,
                "coherence_degeneracy_baseline": c.coherence_degeneracy_baseline,
                "passes_cutoff": c.passes_cutoff,
            }
            for c in stage0.all_candidates
        ]
        stage0_path = out_dir / "e0012_stage0_candidates.json"
        stage0_path.write_text(json.dumps(stage0_table, indent=2), encoding="utf-8")
        print(f"[e0012] Stage 0 candidate table written to {stage0_path}")

    eval_by_id = {ev.candidate_id: ev for ev in ape_result.all_candidate_evals}
    winner_id = ape_winner_candidate_id
    ape_candidate_provenance = _list_attr(
        ape_result, "candidate_provenance", candidate_provenance
    )
    ape_candidates_payload = {
        "raw_model_output": _str_attr(ape_result, "raw_model_output", raw_model_output),
        "n_model_parseable": _int_attr(ape_result, "n_model_parseable", n_model_parseable),
        "n_padded": _int_attr(ape_result, "n_cand_padded", n_cand_padded),
        "candidates": [
            {
                **prov,
                "dev_score_k3": (
                    eval_by_id[int(prov["candidate_id"])].dev_score
                    if int(prov["candidate_id"]) in eval_by_id else None
                ),
                "dev_score_k5": (
                    ape_result.auto_prompt_dev_score_k5
                    if winner_id is not None and int(prov["candidate_id"]) == int(winner_id)
                    else None
                ),
            }
            for prov in ape_candidate_provenance
        ],
    }
    ape_candidates_path = out_dir / "e0012_ape_candidates.json"
    ape_candidates_path.write_text(json.dumps(ape_candidates_payload, indent=2), encoding="utf-8")
    print(f"[e0012] APE candidate provenance written to {ape_candidates_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="E-0012 Verified Control Button harness"
    )
    parser.add_argument("--backend", default="synthetic", choices=["synthetic", "hf"])
    parser.add_argument("--generate-fixture", action="store_true",
                        help="Download and save TriviaQA fixture (requires network)")
    parser.add_argument("--output-dir", default="results/e0012_smoke")
    parser.add_argument("--stage0-only", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--model", default=None, help="HF model id")
    parser.add_argument("--n-items", type=int, default=None,
                        help="Synthetic pool size (smoke only)")
    parser.add_argument("--e0006-dev-baseline-jsonl", default=None,
                        help=("HF only: canonical E-0006 all-80 unsteered-empty-prompt "
                              "JSONL artifact (with .manifest.json sidecar); defaults to "
                              "data/e0006_uncertainty_baseline/e0006_uncertainty_baseline.jsonl"))
    args = parser.parse_args()

    if args.generate_fixture:
        cmd_generate_fixture(args)
    else:
        cmd_run(args)


if __name__ == "__main__":
    main()
