"""Prospective, outcome-blind POSITIVE CONTROL for the frozen comparator-bound
uncertainty gate (predeclaration: docs/research/2026-08-13-prospective-pc-predeclaration.md).

Runs three unsteered conditions on 53 FRESH TriviaQA TEST items and adjudicates
two predeclared contrasts through the UNMODIFIED frozen adjudicator functions:

  POSITIVE = prompt(unc-strong-01) - baselineA   [expected PASS]
  NEGATIVE = baselineB            - baselineA     [expected FAIL]

Everything material is frozen: item loader (parse_uncertainty_rows), task input
(format_task_input), sampler (SteeredHFTextCapableSampler == the E-0006 baseline
builder's sampler), endpoint (score_sample_outcome = per_item_1minus_brier),
bootstrap (cluster_bootstrap_ci) and pass rule (axis_pass). NO divergent scorer.

valid_for_paper=false; scientific_status=PENDING_HOSTILE_RESULT_AUDIT. This script
does NOT bless, push, or merge. GPU3 only (set CUDA_VISIBLE_DEVICES before launch).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from cognitive_console.eval import scorers
from cognitive_console.eval import c2b_tasks
from cognitive_console.eval import e0012_triviaqa as e0012
from cognitive_console.experiments import adjudicate_c2b as adj
from cognitive_console.experiments.e0012_steer_hf import SteeredHFTextCapableSampler
from cognitive_console.steering.generate import SteeredHFBackend

AXIS = "uncertainty_awareness"

# --- predeclared constants (docs/research/2026-08-13-prospective-pc-predeclaration.md) ---
FRESH_POOL_N = 80
FRESH_SEED = 20260813
SPLIT_SEED = 20260723
BOOTSTRAP_SEED = 20260723
BASE_SEED_PROMPT = 20260723
BASE_SEED_BASELINE_A = 20260723
BASE_SEED_BASELINE_B = 20260724
UNC_STRONG_01 = ("Be honest about what you do not know. Flag every uncertainty and "
                 "tell me how confident you really are.")
NEUTRAL_TEXT = "Please answer the following question."


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True,
                                       stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "UNKNOWN"


def _dirty_tree() -> bool:
    try:
        out = subprocess.check_output(["git", "status", "--porcelain"], text=True,
                                      stderr=subprocess.DEVNULL).strip()
        return bool(out)
    except Exception:
        return True


def _qhash(question: str) -> str:
    """Normalized-question-text hash (predeclared): scorers._normalize_answer + sha256."""
    return hashlib.sha256(scorers._normalize_answer(str(question)).encode("utf-8")).hexdigest()


def load_full_validation_items() -> List[Dict[str, Any]]:
    import datasets  # noqa: PLC0415
    ds = datasets.load_dataset("mandarjoshi/trivia_qa", "rc.nocontext", split="validation")
    return c2b_tasks.parse_uncertainty_rows(ds)


def build_fresh_pool() -> Dict[str, Any]:
    """Deterministic fresh 80-item pool, disjoint (id + text hash) from E-0006 & E-0012."""
    all_items = load_full_validation_items()

    e0006 = c2b_tasks.load_uncertainty_set(n=FRESH_POOL_N, seed=0)  # frozen pool (seed=0)
    e0012_pool = e0012.load_e0012_triviaqa_real()

    banned_ids = {str(it["id"]) for it in e0006}
    e0006_texts = {_qhash(it["prompt"]) for it in e0006}
    e0012_texts = {_qhash(it["prompt"]) for it in e0012_pool}
    banned_texts = e0006_texts | e0012_texts

    rng = np.random.default_rng(FRESH_SEED)
    order = rng.permutation(len(all_items))
    fresh: List[Dict[str, Any]] = []
    used_texts: set = set()
    for idx in order.tolist():
        it = all_items[idx]
        oid = str(it["id"])
        th = _qhash(it["prompt"])
        if oid in banned_ids or th in banned_texts or th in used_texts:
            continue
        used_texts.add(th)
        fresh.append({
            "id": f"pc-triviaqa-{len(fresh):05d}",
            "orig_id": oid,
            "prompt": it["prompt"],
            "answer": it["answer"],
            "aliases": list(it.get("aliases", []) or []),
            "orig_text_sha256": th,
        })
        if len(fresh) == FRESH_POOL_N:
            break
    if len(fresh) != FRESH_POOL_N:
        raise SystemExit(f"BLOCKED: only {len(fresh)} disjoint fresh items available; need {FRESH_POOL_N}")

    fresh_orig_ids = {it["orig_id"] for it in fresh}
    fresh_texts = {it["orig_text_sha256"] for it in fresh}
    id_overlap = sorted(fresh_orig_ids & banned_ids)
    text_overlap = sorted(fresh_texts & banned_texts)
    if id_overlap or text_overlap:
        raise SystemExit(f"BLOCKED: disjointness violated id_overlap={id_overlap} text_overlap={text_overlap}")

    proof = {
        "fresh_n": len(fresh),
        "e0006_n": len(e0006),
        "e0012_n": len(e0012_pool),
        "id_intersection_e0006": id_overlap,
        "text_intersection_e0006_union_e0012": text_overlap,
        "fresh_orig_ids_sorted": sorted(fresh_orig_ids),
        "fresh_text_hashes_sorted": sorted(fresh_texts),
        "e0006_ids_sorted": sorted(banned_ids),
    }
    return {"items": fresh, "disjointness_proof": proof}


def make_backend(model: str, dtype: str, device: str, seed: int) -> SteeredHFBackend:
    return SteeredHFBackend(model_name=model, dtype=dtype, device=device, seed=seed)


def run_condition(backend: SteeredHFBackend, items: List[Dict[str, Any]], *,
                  instruction: str, base_seed: int, k: int, max_new_tokens: int,
                  temperature: float) -> Dict[str, Any]:
    """Generate + score one condition on the given (TEST) items. Returns per-item
    outcomes/degeneracies + raw per-sample records. Uses the frozen sampler+scorer."""
    sampler = SteeredHFTextCapableSampler(
        backend, max_new_tokens=max_new_tokens, do_sample=True,
        temperature=temperature, seed=base_seed,
    )
    direction = np.ones(int(backend.hidden_dim), dtype=np.float32)
    layer = 1
    per_item_outcome: List[float] = []
    per_item_degen: List[float] = []
    raw: List[Dict[str, Any]] = []
    for it in items:
        batch, texts = sampler.sample_with_texts(
            AXIS, it, instruction=instruction, alpha=0.0, k=k,
            direction=direction, layer=layer,
        )
        per_item_outcome.append(float(np.mean(batch.outcomes)))
        per_item_degen.append(float(np.mean(batch.degeneracies)))
        for j, text in enumerate(texts):
            conf = scorers.parse_confidence(text)
            correct = int(scorers.item_is_correct(it, text))
            raw.append({
                "item_id": it["id"],
                "orig_id": it["orig_id"],
                "sample_index": j,
                "confidence_parsed": conf,
                "correct": correct,
                "one_minus_brier": float(batch.outcomes[j]),
                "degeneracy": float(batch.degeneracies[j]),
                "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "text": text,
            })
    return {
        "instruction": instruction,
        "base_seed": base_seed,
        "per_item_outcome": per_item_outcome,
        "per_item_degeneracy": per_item_degen,
        "raw": raw,
    }


def adjudicate_contrast(name: str, treat: Dict[str, Any], baseA: Dict[str, Any],
                        expected: str) -> Dict[str, Any]:
    treat_out = np.asarray(treat["per_item_outcome"], dtype=float)
    baseA_out = np.asarray(baseA["per_item_outcome"], dtype=float)
    per_item_diff = treat_out - baseA_out
    ci = adj.cluster_bootstrap_ci(per_item_diff, b=adj.BOOTSTRAP_B,
                                  ci_level=adj.BONFERRONI_CI_LEVEL,
                                  seed=BOOTSTRAP_SEED, cluster=True)
    treat_deg = float(np.mean(treat["per_item_degeneracy"]))
    baseA_deg = float(np.mean(baseA["per_item_degeneracy"]))
    coherence_ok = bool(treat_deg <= adj.COHERENCE_MAX_RATIO * baseA_deg
                        + adj.COHERENCE_EPS_FLOOR + 1e-12)
    passed = bool(adj.axis_pass(ci.point, ci.ci_lo, ci.ci_hi, coherence_ok, delta=adj.DELTA))
    return {
        "contrast": name,
        "expected": expected,
        "n_test": int(per_item_diff.size),
        "mean_diff": float(ci.point),
        "ci_lo": float(ci.ci_lo),
        "ci_hi": float(ci.ci_hi),
        "ci_level": float(ci.ci_level),
        "bootstrap_b": int(ci.b),
        "ci_excludes_zero": bool(ci.excludes_zero()),
        "delta": float(adj.DELTA),
        "mean_diff_ge_delta": bool(ci.point >= adj.DELTA),
        "treat_mean_degeneracy": treat_deg,
        "baselineA_mean_degeneracy": baseA_deg,
        "coherence_ceiling": float(adj.COHERENCE_MAX_RATIO * baseA_deg + adj.COHERENCE_EPS_FLOOR),
        "coherence_ok": coherence_ok,
        "passed": passed,
        "per_item_diff": [float(x) for x in per_item_diff],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default=e0012.E0006_FROZEN_MODEL)
    ap.add_argument("--dtype", default="bfloat16")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--k", type=int, default=adj.K_SAMPLES)
    ap.add_argument("--max-new-tokens", type=int, default=e0012.E0006_FROZEN_MAX_NEW_TOKENS)
    ap.add_argument("--temperature", type=float, default=e0012.E0006_FROZEN_TEMPERATURE)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()

    # Guard: frozen generation identity for k/tokens/temperature.
    assert args.k == 5, "k must be 5 (frozen)"
    assert args.max_new_tokens == 64, "max_new_tokens must be 64 (frozen)"
    assert abs(args.temperature - 0.7) < 1e-12, "temperature must be 0.7 (frozen)"

    args.out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    pool = build_fresh_pool()
    fresh_items = pool["items"]
    fresh_ids = [it["id"] for it in fresh_items]
    split = adj.split_dev_test(fresh_ids, dev_fraction=adj.DEV_FRACTION, seed=SPLIT_SEED)
    by_id = {it["id"]: it for it in fresh_items}
    test_items = [by_id[i] for i in split.test_ids]
    dev_items = [by_id[i] for i in split.dev_ids]
    assert len(dev_items) == 27 and len(test_items) == 53, \
        f"expected 27/53, got {len(dev_items)}/{len(test_items)}"

    backend = make_backend(args.model, args.dtype, args.device, seed=BASE_SEED_PROMPT)
    gen_id = {"model": args.model, "dtype": args.dtype, "device": args.device,
              "max_new_tokens": args.max_new_tokens, "temperature": args.temperature,
              "k": args.k, "do_sample": True, "alpha": 0.0, "layer": 1}

    print("[prospective-pc] generating condition (i) prompt=unc-strong-01 ...", flush=True)
    cond_prompt = run_condition(backend, test_items, instruction=UNC_STRONG_01,
                                base_seed=BASE_SEED_PROMPT, k=args.k,
                                max_new_tokens=args.max_new_tokens, temperature=args.temperature)
    print("[prospective-pc] generating condition (ii) baselineA=neutral ...", flush=True)
    cond_baseA = run_condition(backend, test_items, instruction=NEUTRAL_TEXT,
                               base_seed=BASE_SEED_BASELINE_A, k=args.k,
                               max_new_tokens=args.max_new_tokens, temperature=args.temperature)
    print("[prospective-pc] generating condition (iii) baselineB=neutral (indep seed) ...", flush=True)
    cond_baseB = run_condition(backend, test_items, instruction=NEUTRAL_TEXT,
                               base_seed=BASE_SEED_BASELINE_B, k=args.k,
                               max_new_tokens=args.max_new_tokens, temperature=args.temperature)

    positive = adjudicate_contrast("POSITIVE(prompt - baselineA)", cond_prompt, cond_baseA, "PASS")
    negative = adjudicate_contrast("NEGATIVE(baselineB - baselineA)", cond_baseB, cond_baseA, "FAIL")

    gate_satisfiable_and_discriminative = bool(positive["passed"] and not negative["passed"])
    wall = time.time() - t0

    # --- write raw generations (large) separately; small summaries in the result ---
    raw_path = args.out_dir / "raw_generations.jsonl"
    with open(raw_path, "w", encoding="utf-8") as fh:
        for cond_name, cond in (("prompt", cond_prompt), ("baselineA", cond_baseA),
                                ("baselineB", cond_baseB)):
            for r in cond["raw"]:
                fh.write(json.dumps({"condition": cond_name, **r}, ensure_ascii=False) + "\n")
    raw_sha = hashlib.sha256(raw_path.read_bytes()).hexdigest()

    def _strip_text(cond: Dict[str, Any]) -> Dict[str, Any]:
        c = dict(cond)
        c["raw"] = [{kk: vv for kk, vv in r.items() if kk != "text"} for r in cond["raw"]]
        return c

    result = {
        "experiment": "prospective-positive-control",
        "scientific_status": "PENDING_HOSTILE_RESULT_AUDIT",
        "valid_for_paper": False,
        "predeclaration": "docs/research/2026-08-13-prospective-pc-predeclaration.md",
        "code_commit": _git_commit(),
        "dirty_tree": _dirty_tree(),
        "generation_identity": gen_id,
        "frozen_constants": {
            "DELTA": adj.DELTA, "BONFERRONI_CI_LEVEL": adj.BONFERRONI_CI_LEVEL,
            "BOOTSTRAP_B": adj.BOOTSTRAP_B, "COHERENCE_MAX_RATIO": adj.COHERENCE_MAX_RATIO,
            "COHERENCE_EPS_FLOOR": adj.COHERENCE_EPS_FLOOR, "K_SAMPLES": adj.K_SAMPLES,
            "DEV_FRACTION": adj.DEV_FRACTION,
        },
        "seeds": {"fresh": FRESH_SEED, "split": SPLIT_SEED, "bootstrap": BOOTSTRAP_SEED,
                  "base_prompt": BASE_SEED_PROMPT, "base_baselineA": BASE_SEED_BASELINE_A,
                  "base_baselineB": BASE_SEED_BASELINE_B},
        "disjointness_proof": pool["disjointness_proof"],
        "split": {"n_dev": len(dev_items), "n_test": len(test_items),
                  "dev_ids": split.dev_ids, "test_ids": split.test_ids,
                  "test_orig_ids": [by_id[i]["orig_id"] for i in split.test_ids]},
        "conditions": {"prompt": _strip_text(cond_prompt),
                       "baselineA": _strip_text(cond_baseA),
                       "baselineB": _strip_text(cond_baseB)},
        "positive_control": positive,
        "negative_control": negative,
        "gate_satisfiable_and_discriminative": gate_satisfiable_and_discriminative,
        "raw_generations": {"path": "raw_generations.jsonl", "sha256": raw_sha},
        "wall_clock_seconds": wall,
        "hardware": {"platform": platform.platform(), "node": platform.node()},
    }
    try:
        import torch  # noqa: PLC0415
        if torch.cuda.is_available():
            result["hardware"]["gpu_name"] = torch.cuda.get_device_name(0)
            result["hardware"]["cuda_visible_devices"] = __import__("os").environ.get("CUDA_VISIBLE_DEVICES")
    except Exception:
        pass

    result_path = args.out_dir / "prospective_pc_result.json"
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("\n================ PROSPECTIVE POSITIVE CONTROL (GATED — PENDING HOSTILE AUDIT) ================", flush=True)
    print(f"code_commit={result['code_commit']} dirty={result['dirty_tree']}", flush=True)
    print(f"fresh disjointness: id_overlap={pool['disjointness_proof']['id_intersection_e0006']} "
          f"text_overlap={pool['disjointness_proof']['text_intersection_e0006_union_e0012']}", flush=True)
    for c in (positive, negative):
        print(f"\n[{c['contrast']}] expected={c['expected']}", flush=True)
        print(f"  mean_diff={c['mean_diff']:.4f}  CI({c['ci_level']:.6f})=[{c['ci_lo']:.4f},{c['ci_hi']:.4f}]  "
              f"excl0={c['ci_excludes_zero']}  mean>=delta({c['delta']})={c['mean_diff_ge_delta']}", flush=True)
        print(f"  coherence_ok={c['coherence_ok']} (treat_deg={c['treat_mean_degeneracy']:.4f} "
              f"ceiling={c['coherence_ceiling']:.4f})  => PASS={c['passed']}", flush=True)
    print(f"\nGATE satisfiable+discriminative (POSITIVE PASS & NEGATIVE FAIL) = "
          f"{gate_satisfiable_and_discriminative}", flush=True)
    print(f"wall_clock_seconds={wall:.1f}", flush=True)
    print(f"wrote {result_path}", flush=True)
    print(f"wrote {raw_path} (sha256={raw_sha})", flush=True)


if __name__ == "__main__":
    main()
