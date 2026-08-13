"""Prospective, outcome-blind NOISY (non-degenerate) POSITIVE CONTROL for the frozen
comparator-bound decision gate.

Predeclaration: docs/research/2026-08-13-noisy-positive-control-predeclaration.md
(committed BEFORE this script and BEFORE any generation/scoring).

Fixes the two hostile-audit rejections of the prior positive controls:
  1. REAL disjointness — the fresh pool is verified id- AND normalized-text-hash
     disjoint from the ACTUAL frozen E-0006 artifact (manifest ids + jsonl prompts),
     NOT from a re-sampled reconstruction. HARD-FAIL (SystemExit) on any overlap.
  2. NON-DEGENERATE noisy endpoint — instruction "answer in exactly two words"
     scored by a deterministic whitespace-token-count==2 check. The length
     constraint fights TriviaQA answer lengths, so per-item compliance is fractional
     across the k=5 samples and the bootstrap CI is a proper (non-collapsed)
     interval, unlike the rejected [1,1]/[0,0] "ANSWER:" straw control.

Runs three UNSTEERED conditions on 53 FRESH TriviaQA TEST items and adjudicates two
predeclared contrasts through the UNMODIFIED frozen adjudicator functions:

  POSITIVE = strong(exactly-two-words) - baselineA(neutral)   [expected PASS]
  NEGATIVE = baselineB(neutral)        - baselineA(neutral)    [expected FAIL]

Frozen/UNMODIFIED: item parser (parse_uncertainty_rows), split (split_dev_test),
generation primitive (SteeredHFBackend.generate), per-(item,sample) seed derivation,
degeneracy/coherence (scorers.degeneracy_score), bootstrap (cluster_bootstrap_ci)
and pass rule (axis_pass). The ONLY novel, PREDECLARED components are the endpoint
(exactly-two-words), its deterministic scorer, the strong instruction wording, the
token budget (32), and the deterministic disjoint pool range — all locked in the
predeclaration BEFORE generation.

valid_for_paper=false; scientific_status=PENDING_HOSTILE_RESULT_AUDIT. Does NOT
bless, push, or merge. GPU3 only (set CUDA_VISIBLE_DEVICES=3 before launch).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from cognitive_console.eval import scorers
from cognitive_console.eval import c2b_tasks
from cognitive_console.eval import e0012_triviaqa as e0012
from cognitive_console.experiments import adjudicate_c2b as adj
from cognitive_console.steering.generate import SteeredHFBackend, SteerConfig

# --- predeclared constants (docs/research/2026-08-13-noisy-positive-control-predeclaration.md) ---
AXIS_SEED_LABEL = "instruction_two_words"
FRESH_POOL_N = 80
FRESH_INDEX_MIN = 100        # first 80 parsed items with id-index >= 100 (disjoint by construction)
SPLIT_SEED = 20260723
BOOTSTRAP_SEED = 20260723
BASE_SEED_STRONG = 20260723
BASE_SEED_BASELINE_A = 20260723   # paired with strong (same sampling seeds; only instruction differs)
BASE_SEED_BASELINE_B = 20260724   # independent

MAX_NEW_TOKENS = 32          # predeclared; endpoint is NOT truncation-confounded
TEMPERATURE = 0.7            # frozen convention
K_SAMPLES = 5               # frozen convention
ALPHA = 0.0                 # unsteered
LAYER = 1

STRONG_INSTRUCTION = (
    "Answer the following question in exactly two words. Your entire reply must "
    "contain exactly two words and nothing else."
)
NEUTRAL_TEXT = "Please answer the following question."

# Frozen E-0006 artifact locations (REAL artifact — read directly, NOT re-sampled).
FROZEN_MANIFEST = Path("data/e0006_uncertainty_baseline/e0006_uncertainty_baseline.manifest.json")
FROZEN_JSONL = Path("data/e0006_uncertainty_baseline/e0006_uncertainty_baseline.jsonl")


def exactly_two_words(text: str) -> float:
    """Predeclared deterministic scorer: 1.0 iff the reply (stripped) contains
    exactly two whitespace-delimited tokens, else 0.0."""
    toks = re.findall(r"\S+", str(text).strip())
    return 1.0 if len(toks) == 2 else 0.0


def build_task_input(instruction: str, item: Dict[str, Any]) -> str:
    """Predeclared task-input builder: instruction + question, NO answer-format cue."""
    q = str(item.get("prompt", "")).strip()
    return instruction.strip() + "\n\n" + q


def _call_seed(base_seed: int, item_id: str, j: int) -> int:
    """Frozen per-(item,sample) seed derivation (mirrors BackendOutcomeSampler._call_seed)."""
    key = f"{base_seed}|{AXIS_SEED_LABEL}|{item_id}|{float(ALPHA):.6f}|{j}"
    return int(hashlib.sha256(key.encode("utf-8")).hexdigest(), 16) % (2 ** 31)


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


def read_frozen_e0006() -> Dict[str, Any]:
    """Read the REAL frozen E-0006 artifact (manifest ids + jsonl prompts). Returns
    the frozen id set and the frozen normalized-question-text hash set. This reads
    the ACTUAL frozen files, NOT a re-sampled reconstruction."""
    if not FROZEN_MANIFEST.exists() or not FROZEN_JSONL.exists():
        raise SystemExit(f"BLOCKED: frozen E-0006 artifact not found at {FROZEN_MANIFEST} / {FROZEN_JSONL}")
    manifest = json.loads(FROZEN_MANIFEST.read_text(encoding="utf-8"))
    frozen_ids = set(str(x) for x in manifest["item_ids"])
    frozen_id_to_text: Dict[str, str] = {}
    frozen_texts: set = set()
    with open(FROZEN_JSONL, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            th = _qhash(row["prompt"])
            frozen_id_to_text[str(row["id"])] = th
            frozen_texts.add(th)
    # cross-check: every manifest id present in the jsonl
    missing = sorted(frozen_ids - set(frozen_id_to_text))
    if missing:
        raise SystemExit(f"BLOCKED: frozen manifest ids missing from jsonl: {missing[:5]} ...")
    jsonl_ids = sorted(frozen_id_to_text)
    return {
        "manifest_path": str(FROZEN_MANIFEST),
        "jsonl_path": str(FROZEN_JSONL),
        "manifest_artifact_sha256": manifest.get("artifact_sha256"),
        "jsonl_file_sha256": hashlib.sha256(FROZEN_JSONL.read_bytes()).hexdigest(),
        "frozen_ids": frozen_ids,
        "frozen_texts": frozen_texts,
        "frozen_ids_sorted": sorted(frozen_ids),
        "frozen_jsonl_ids_sorted": jsonl_ids,
        "frozen_n": len(frozen_ids),
    }


def build_fresh_pool() -> Dict[str, Any]:
    """Deterministic fresh 80-item pool = first 80 parsed items with id-index >= 100,
    HARD-verified id+text disjoint from the REAL frozen E-0006 artifact."""
    all_items = load_full_validation_items()
    frozen = read_frozen_e0006()

    fresh: List[Dict[str, Any]] = []
    for it in all_items:
        oid = str(it["id"])
        try:
            idx = int(oid.split("-")[-1])
        except ValueError:
            continue
        if idx < FRESH_INDEX_MIN:
            continue
        th = _qhash(it["prompt"])
        fresh.append({
            "id": f"pc3-triviaqa-{len(fresh):05d}",
            "orig_id": oid,
            "prompt": it["prompt"],
            "answer": it["answer"],
            "aliases": list(it.get("aliases", []) or []),
            "orig_text_sha256": th,
        })
        if len(fresh) == FRESH_POOL_N:
            break
    if len(fresh) != FRESH_POOL_N:
        raise SystemExit(f"BLOCKED: only {len(fresh)} items with index>={FRESH_INDEX_MIN}; need {FRESH_POOL_N}")

    fresh_orig_ids = {it["orig_id"] for it in fresh}
    fresh_texts = {it["orig_text_sha256"] for it in fresh}

    # E-0012 pool (offset 500) for extra transparency — disjoint by construction.
    e0012_ids: set = set()
    e0012_texts: set = set()
    try:
        e0012_pool = e0012.load_e0012_triviaqa_real()
        e0012_ids = {str(it["id"]) for it in e0012_pool}
        e0012_texts = {_qhash(it["prompt"]) for it in e0012_pool}
    except Exception as exc:  # non-fatal: E-0012 is not the MANDATORY gate
        e0012_pool = []
        e0012_load_error = repr(exc)
    else:
        e0012_load_error = None

    id_overlap_e0006 = sorted(fresh_orig_ids & frozen["frozen_ids"])
    text_overlap_e0006 = sorted(fresh_texts & frozen["frozen_texts"])
    id_overlap_e0012 = sorted(fresh_orig_ids & e0012_ids)
    text_overlap_e0012 = sorted(fresh_texts & e0012_texts)

    # HARD-FAIL on any overlap with the MANDATORY frozen E-0006 artifact.
    if id_overlap_e0006 or text_overlap_e0006:
        raise SystemExit(
            f"BLOCKED: E-0006 disjointness violated id_overlap={id_overlap_e0006} "
            f"text_overlap={text_overlap_e0006}")
    # E-0012 is disjoint by construction (offset 500); hard-fail too if violated.
    if id_overlap_e0012 or text_overlap_e0012:
        raise SystemExit(
            f"BLOCKED: E-0012 disjointness violated id_overlap={id_overlap_e0012} "
            f"text_overlap={text_overlap_e0012}")

    proof = {
        "fresh_n": len(fresh),
        "fresh_index_min": FRESH_INDEX_MIN,
        "frozen_e0006_n": frozen["frozen_n"],
        "frozen_manifest_path": frozen["manifest_path"],
        "frozen_jsonl_path": frozen["jsonl_path"],
        "frozen_manifest_artifact_sha256": frozen["manifest_artifact_sha256"],
        "frozen_jsonl_file_sha256": frozen["jsonl_file_sha256"],
        "id_intersection_e0006": id_overlap_e0006,
        "text_intersection_e0006": text_overlap_e0006,
        "id_intersection_e0012": id_overlap_e0012,
        "text_intersection_e0012": text_overlap_e0012,
        "e0012_n": len(e0012_pool),
        "e0012_load_error": e0012_load_error,
        "fresh_orig_ids_sorted": sorted(fresh_orig_ids),
        "fresh_text_hashes_sorted": sorted(fresh_texts),
        "frozen_e0006_ids_sorted": frozen["frozen_ids_sorted"],
        "frozen_e0006_text_hashes_sorted": sorted(frozen["frozen_texts"]),
    }
    return {"items": fresh, "disjointness_proof": proof}


def run_condition(backend: SteeredHFBackend, items: List[Dict[str, Any]], *,
                  instruction: str, base_seed: int) -> Dict[str, Any]:
    """Generate + score one condition on the TEST items. Per-item outcome = mean over
    k samples of the predeclared exactly-two-words compliance; degeneracy via frozen
    scorer. Also keeps the per-sample outcome matrix for the CLUSTER bootstrap."""
    direction = np.ones(int(backend.hidden_dim), dtype=np.float32)
    steer = SteerConfig(direction=direction, alpha=float(ALPHA), layer=int(LAYER))
    per_item_outcome: List[float] = []
    per_item_degen: List[float] = []
    per_sample_outcomes: List[List[float]] = []
    raw: List[Dict[str, Any]] = []
    for it in items:
        comp_k: List[float] = []
        deg_k: List[float] = []
        for j in range(K_SAMPLES):
            seed = _call_seed(base_seed, it["id"], j)
            text_input = build_task_input(instruction, it)
            out = backend.generate(
                text_input, steer, MAX_NEW_TOKENS,
                do_sample=True, temperature=TEMPERATURE, seed=seed,
            )
            comp = exactly_two_words(out)
            deg = scorers.degeneracy_score(out)
            comp_k.append(comp)
            deg_k.append(deg)
            raw.append({
                "item_id": it["id"],
                "orig_id": it["orig_id"],
                "sample_index": j,
                "compliance": comp,
                "token_count": len(re.findall(r"\S+", str(out).strip())),
                "degeneracy": deg,
                "text_sha256": hashlib.sha256(out.encode("utf-8")).hexdigest(),
                "text": out,
            })
        per_item_outcome.append(float(np.mean(comp_k)))
        per_item_degen.append(float(np.mean(deg_k)))
        per_sample_outcomes.append(comp_k)
    return {
        "instruction": instruction,
        "base_seed": base_seed,
        "per_item_outcome": per_item_outcome,
        "per_item_degeneracy": per_item_degen,
        "per_sample_outcomes": per_sample_outcomes,
        "compliance_rate": float(np.mean([r["compliance"] for r in raw])),
        "raw": raw,
    }


def _spread_stats(per_item: List[float]) -> Dict[str, Any]:
    a = np.asarray(per_item, dtype=float)
    frac_interior = float(np.mean((a > 0.0) & (a < 1.0)))  # fraction of items with fractional (noisy) compliance
    return {
        "mean": float(a.mean()),
        "std": float(a.std(ddof=0)),
        "min": float(a.min()),
        "max": float(a.max()),
        "n_zero": int(np.sum(a == 0.0)),
        "n_one": int(np.sum(a == 1.0)),
        "n_fractional": int(np.sum((a > 0.0) & (a < 1.0))),
        "fraction_fractional": frac_interior,
        "distinct_values": sorted(set(round(float(x), 6) for x in a.tolist())),
        "per_item_outcome": [float(x) for x in a.tolist()],
    }


def adjudicate_contrast(name: str, treat: Dict[str, Any], baseA: Dict[str, Any],
                        expected: str) -> Dict[str, Any]:
    treat_ps = np.asarray(treat["per_sample_outcomes"], dtype=float)   # [n_items, k]
    baseA_ps = np.asarray(baseA["per_sample_outcomes"], dtype=float)   # [n_items, k]
    # Paired per-(item,sample) diff matrix -> row means are the per-item diffs d_i.
    per_sample_diff = treat_ps - baseA_ps                             # [n_items, k]
    per_item_diff = per_sample_diff.mean(axis=1)
    # Frozen item-cluster bootstrap consumes the [n_items, k] matrix (resamples ITEMS).
    ci = adj.cluster_bootstrap_ci(per_sample_diff, b=adj.BOOTSTRAP_B,
                                  ci_level=adj.BONFERRONI_CI_LEVEL,
                                  seed=BOOTSTRAP_SEED, cluster=True)
    treat_deg = float(np.mean(treat["per_item_degeneracy"]))
    baseA_deg = float(np.mean(baseA["per_item_degeneracy"]))
    coherence_ok = bool(treat_deg <= adj.COHERENCE_MAX_RATIO * baseA_deg
                        + adj.COHERENCE_EPS_FLOOR + 1e-12)
    passed = bool(adj.axis_pass(ci.point, ci.ci_lo, ci.ci_hi, coherence_ok, delta=adj.DELTA))
    # Non-degeneracy diagnostics on the per-item DIFFS the bootstrap actually resamples.
    diff_arr = np.asarray(per_item_diff, dtype=float)
    ci_width = float(ci.ci_hi - ci.ci_lo)
    return {
        "contrast": name,
        "expected": expected,
        "n_test": int(diff_arr.size),
        "mean_diff": float(ci.point),
        "ci_lo": float(ci.ci_lo),
        "ci_hi": float(ci.ci_hi),
        "ci_width": ci_width,
        "ci_level": float(ci.ci_level),
        "bootstrap_b": int(ci.b),
        "bootstrap_cluster": bool(ci.cluster),
        "ci_excludes_zero": bool(ci.excludes_zero()),
        "delta": float(adj.DELTA),
        "mean_diff_ge_delta": bool(ci.point >= adj.DELTA),
        "treat_mean_outcome": float(treat_ps.mean(axis=1).mean()),
        "baselineA_mean_outcome": float(baseA_ps.mean(axis=1).mean()),
        "treat_mean_degeneracy": treat_deg,
        "baselineA_mean_degeneracy": baseA_deg,
        "coherence_ceiling": float(adj.COHERENCE_MAX_RATIO * baseA_deg + adj.COHERENCE_EPS_FLOOR),
        "coherence_ok": coherence_ok,
        "passed": passed,
        "per_item_diff": [float(x) for x in diff_arr.tolist()],
        "per_item_diff_std": float(diff_arr.std(ddof=0)),
        "per_item_diff_distinct_values": sorted(set(round(float(x), 6) for x in diff_arr.tolist())),
        "n_distinct_per_item_diff": int(len({round(float(x), 6) for x in diff_arr.tolist()})),
        "ci_is_degenerate_point": bool(ci_width == 0.0),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default=e0012.E0006_FROZEN_MODEL)
    ap.add_argument("--dtype", default="bfloat16")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()

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

    backend = SteeredHFBackend(model_name=args.model, dtype=args.dtype,
                               device=args.device, seed=BASE_SEED_STRONG)
    gen_id = {"model": args.model, "dtype": args.dtype, "device": args.device,
              "max_new_tokens": MAX_NEW_TOKENS, "temperature": TEMPERATURE,
              "k": K_SAMPLES, "do_sample": True, "alpha": ALPHA, "layer": LAYER}

    print("[noisy-pc] generating condition (i) strong=exactly-two-words ...", flush=True)
    cond_strong = run_condition(backend, test_items, instruction=STRONG_INSTRUCTION,
                                base_seed=BASE_SEED_STRONG)
    print(f"[noisy-pc]   strong compliance_rate={cond_strong['compliance_rate']:.3f}", flush=True)
    print("[noisy-pc] generating condition (ii) baselineA=neutral ...", flush=True)
    cond_baseA = run_condition(backend, test_items, instruction=NEUTRAL_TEXT,
                               base_seed=BASE_SEED_BASELINE_A)
    print(f"[noisy-pc]   baselineA compliance_rate={cond_baseA['compliance_rate']:.3f}", flush=True)
    print("[noisy-pc] generating condition (iii) baselineB=neutral (indep seed) ...", flush=True)
    cond_baseB = run_condition(backend, test_items, instruction=NEUTRAL_TEXT,
                               base_seed=BASE_SEED_BASELINE_B)
    print(f"[noisy-pc]   baselineB compliance_rate={cond_baseB['compliance_rate']:.3f}", flush=True)

    positive = adjudicate_contrast("POSITIVE(strong - baselineA)", cond_strong, cond_baseA, "PASS")
    negative = adjudicate_contrast("NEGATIVE(baselineB - baselineA)", cond_baseB, cond_baseA, "FAIL")

    gate_satisfiable_and_discriminative = bool(positive["passed"] and not negative["passed"])
    positive_non_degenerate = bool(not positive["ci_is_degenerate_point"]
                                   and positive["n_distinct_per_item_diff"] >= 3)
    wall = time.time() - t0

    raw_path = args.out_dir / "raw_generations.jsonl"
    with open(raw_path, "w", encoding="utf-8") as fh:
        for cond_name, cond in (("strong", cond_strong), ("baselineA", cond_baseA),
                                ("baselineB", cond_baseB)):
            for r in cond["raw"]:
                fh.write(json.dumps({"condition": cond_name, **r}, ensure_ascii=False) + "\n")
    raw_sha = hashlib.sha256(raw_path.read_bytes()).hexdigest()

    def _strip_text(cond: Dict[str, Any]) -> Dict[str, Any]:
        c = {kk: vv for kk, vv in cond.items() if kk != "raw"}
        c["spread"] = _spread_stats(cond["per_item_outcome"])
        c["raw"] = [{kk: vv for kk, vv in r.items() if kk != "text"} for r in cond["raw"]]
        return c

    result = {
        "experiment": "noisy-positive-control",
        "endpoint": "exactly_two_words(token_count==2)",
        "scientific_status": "PENDING_HOSTILE_RESULT_AUDIT",
        "valid_for_paper": False,
        "predeclaration": "docs/research/2026-08-13-noisy-positive-control-predeclaration.md",
        "code_commit": _git_commit(),
        "dirty_tree": _dirty_tree(),
        "generation_identity": gen_id,
        "strong_instruction": STRONG_INSTRUCTION,
        "neutral_text": NEUTRAL_TEXT,
        "frozen_constants": {
            "DELTA": adj.DELTA, "BONFERRONI_CI_LEVEL": adj.BONFERRONI_CI_LEVEL,
            "BOOTSTRAP_B": adj.BOOTSTRAP_B, "COHERENCE_MAX_RATIO": adj.COHERENCE_MAX_RATIO,
            "COHERENCE_EPS_FLOOR": adj.COHERENCE_EPS_FLOOR, "K_SAMPLES": adj.K_SAMPLES,
            "DEV_FRACTION": adj.DEV_FRACTION,
        },
        "seeds": {"split": SPLIT_SEED, "bootstrap": BOOTSTRAP_SEED,
                  "base_strong": BASE_SEED_STRONG, "base_baselineA": BASE_SEED_BASELINE_A,
                  "base_baselineB": BASE_SEED_BASELINE_B, "fresh_index_min": FRESH_INDEX_MIN},
        "disjointness_proof": pool["disjointness_proof"],
        "split": {"n_dev": len(dev_items), "n_test": len(test_items),
                  "dev_ids": split.dev_ids, "test_ids": split.test_ids,
                  "test_orig_ids": [by_id[i]["orig_id"] for i in split.test_ids]},
        "compliance_rates": {
            "strong": cond_strong["compliance_rate"],
            "baselineA": cond_baseA["compliance_rate"],
            "baselineB": cond_baseB["compliance_rate"],
        },
        "conditions": {"strong": _strip_text(cond_strong),
                       "baselineA": _strip_text(cond_baseA),
                       "baselineB": _strip_text(cond_baseB)},
        "positive_control": positive,
        "negative_control": negative,
        "positive_non_degenerate": positive_non_degenerate,
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

    result_path = args.out_dir / "noisy_pc_result.json"
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("\n============ NOISY POSITIVE CONTROL (GATED — PENDING HOSTILE AUDIT) ============", flush=True)
    print(f"code_commit={result['code_commit']} dirty={result['dirty_tree']}", flush=True)
    print(f"endpoint=exactly_two_words(==2)  budget={MAX_NEW_TOKENS}  k={K_SAMPLES}", flush=True)
    print(f"compliance rates: strong={cond_strong['compliance_rate']:.3f} "
          f"baselineA={cond_baseA['compliance_rate']:.3f} baselineB={cond_baseB['compliance_rate']:.3f}", flush=True)
    dp = pool["disjointness_proof"]
    print(f"fresh disjointness vs REAL frozen E-0006: id_overlap={dp['id_intersection_e0006']} "
          f"text_overlap={dp['text_intersection_e0006']} (frozen_n={dp['frozen_e0006_n']}, "
          f"jsonl_sha={dp['frozen_jsonl_file_sha256'][:12]})", flush=True)
    for c in (positive, negative):
        print(f"\n[{c['contrast']}] expected={c['expected']}", flush=True)
        print(f"  mean_diff={c['mean_diff']:.4f}  CI({c['ci_level']:.6f})=[{c['ci_lo']:.4f},{c['ci_hi']:.4f}]  "
              f"width={c['ci_width']:.4f}  excl0={c['ci_excludes_zero']}  mean>=delta({c['delta']})={c['mean_diff_ge_delta']}", flush=True)
        print(f"  per-item diff: std={c['per_item_diff_std']:.4f} distinct_values={c['n_distinct_per_item_diff']} "
              f"degenerate_point_CI={c['ci_is_degenerate_point']}", flush=True)
        print(f"  coherence_ok={c['coherence_ok']} (treat_deg={c['treat_mean_degeneracy']:.4f} "
              f"ceiling={c['coherence_ceiling']:.4f})  => PASS={c['passed']}", flush=True)
    print(f"\nPOSITIVE non-degenerate (proper CI + >=3 distinct per-item diffs) = {positive_non_degenerate}", flush=True)
    print(f"GATE satisfiable+discriminative (POSITIVE PASS & NEGATIVE FAIL) = "
          f"{gate_satisfiable_and_discriminative}", flush=True)
    print(f"wall_clock_seconds={wall:.1f}", flush=True)
    print(f"wrote {result_path}", flush=True)
    print(f"wrote {raw_path} (sha256={raw_sha})", flush=True)


if __name__ == "__main__":
    main()
