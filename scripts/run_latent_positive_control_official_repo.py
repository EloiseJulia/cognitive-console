"""Stage-1 DEV rerun using the official Stolfo et al. repository code.

This runner intentionally imports and calls the official
``microsoft/llm-steer-instruct`` functions for:

* model loading (``utils.model_utils.load_model_from_tl_name``),
* representation extraction (``utils.generation_utils.extract_representation``),
* activation-addition hook (``utils.generation_utils.activation_addition_hook``),
* hooked generation (``utils.generation_utils.generate_with_hooks``), and
* IFEval keyword scoring (``ifeval_scripts.evaluation_main``).

The only project-local code here is orchestration plus the unchanged frozen
bootstrap/coherence gate used by our adjudicator. TEST is not implemented.
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import importlib
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Sequence

import numpy as np

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))

from cognitive_console.experiments import latent_positive_control as lpc

METHOD_SOURCE_COMMIT = "9dac937ef6fc3e483b1efc13863deeb03ec38dbe"
DEFAULT_MODEL_REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(_REPO), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def _git_dirty() -> bool | None:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(_REPO), "status", "--short"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return bool(out.strip())
    except Exception:
        return None


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def _load_official_modules(official_repo: Path):
    official_repo = Path(official_repo).resolve()
    if not (official_repo / "utils" / "generation_utils.py").exists():
        raise FileNotFoundError(f"official llm-steer-instruct repo not found: {official_repo}")
    sys.path.insert(0, str(official_repo))
    return {
        "model_utils": importlib.import_module("utils.model_utils"),
        "generation_utils": importlib.import_module("utils.generation_utils"),
        "tlutils": importlib.import_module("transformer_lens.utils"),
        "ifeval": importlib.import_module("ifeval_scripts.evaluation_main"),
    }


def _read_jsonl(path: Path) -> List[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _official_keyword(row: dict) -> str:
    kwargs = row.get("kwargs") or [{}]
    words = kwargs[0].get("keywords") or kwargs[0].get("forbidden_words")
    if not words or len(words) != 1:
        raise ValueError(f"expected exactly one keyword in official row: {row}")
    return str(words[0])


def _render_chat(tokenizer, prompt: str) -> str:
    return tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt}],
        add_generation_prompt=True,
        tokenize=False,
    )


def _official_score(mods, row: dict, response: str) -> int:
    out = mods["ifeval"].test_instruction_following_strict(row, {row["prompt"]: response})
    return int(bool(out.follow_all_instructions))


def _mean_instruction_vectors(mods, model, tokenizer, rows: Sequence[dict], *, device: str, num_final_tokens: int, max_new_tokens: int):
    """Compute per-keyword mean instruction vectors with official extraction code."""
    gen = mods["generation_utils"]
    by_word: Dict[str, List[np.ndarray]] = {}
    for i, row in enumerate(rows, 1):
        word = _official_keyword(row)
        prompt_with = row["prompt"]
        prompt_without = row["prompt_without_instruction"]
        ex_with = _render_chat(tokenizer, prompt_with)
        ex_without = _render_chat(tokenizer, prompt_without)
        # Official script also calls generate before extraction. Keep this for
        # fidelity even though the output is not used for the vector.
        gen.generate(model, tokenizer, ex_with, device, max_new_tokens=max_new_tokens)
        hs_with = gen.extract_representation(model, tokenizer, ex_with, device, num_final_tokens)
        gen.generate(model, tokenizer, ex_without, device, max_new_tokens=max_new_tokens)
        hs_without = gen.extract_representation(model, tokenizer, ex_without, device, num_final_tokens)
        diff = np.asarray(hs_with) - np.asarray(hs_without)
        by_word.setdefault(word, []).append(diff)
        if i % 25 == 0:
            print(f"[official-lpc] extracted {i}/{len(rows)} keyword representation rows", flush=True)

    vectors: Dict[str, np.ndarray] = {}
    for word, diffs in by_word.items():
        arr = np.asarray(diffs)
        # Official keyword/evaluate.py handles [n,layers,d] by inserting a final
        # token axis, then uses mean_repr_diffs[:, -1, :].
        if arr.ndim == 3:
            arr = arr[:, :, None, :]
        mean_diff = arr.mean(axis=0)
        vectors[word] = mean_diff[:, -1, :]
    return vectors


def _generate_baseline_or_prompt(mods, model, tokenizer, rows: Sequence[dict], *, device: str, include_instructions: bool, max_generation_length: int) -> tuple[List[str], List[int], List[float]]:
    gen = mods["generation_utils"]
    texts: List[str] = []
    scores: List[int] = []
    degs: List[float] = []
    for row in rows:
        prompt = row["prompt"] if include_instructions else row["prompt_without_instruction"]
        example = _render_chat(tokenizer, prompt)
        response = gen.generate(model, tokenizer, example, device, max_new_tokens=max_generation_length)
        texts.append(response)
        scores.append(_official_score(mods, row, response))
        degs.append(lpc.degeneracy_score(response))
    return texts, scores, degs


def _generate_steer(mods, model, tokenizer, rows: Sequence[dict], vectors: Dict[str, np.ndarray], *, device: str, source_layer_idx: int, alpha: float, max_generation_length: int) -> tuple[List[str], List[int], List[float]]:
    import torch

    gen = mods["generation_utils"]
    tlutils = mods["tlutils"]
    texts: List[str] = []
    scores: List[int] = []
    degs: List[float] = []
    for row in rows:
        word = _official_keyword(row)
        direction = torch.tensor(vectors[word][source_layer_idx], device=device)
        direction = direction / direction.norm()
        hook_fn = functools.partial(
            gen.activation_addition_hook,
            direction=direction,
            weight=float(alpha),
        )
        fwd_hooks = [(tlutils.get_act_name("resid_post", int(source_layer_idx)), hook_fn)]
        example = _render_chat(tokenizer, row["prompt_without_instruction"])
        encoded = tokenizer(example, return_tensors="pt").to(device)
        response = gen.generate_with_hooks(
            model,
            encoded["input_ids"],
            fwd_hooks=fwd_hooks,
            max_tokens_generated=max_generation_length,
            return_decoded=True,
        )
        if isinstance(response, list):
            response = response[0]
        texts.append(response)
        scores.append(_official_score(mods, row, response))
        degs.append(lpc.degeneracy_score(response))
    return texts, scores, degs


def _cell(item_ids: Sequence[str], scores: Sequence[int], degs: Sequence[float]) -> dict:
    return {
        "item_ids": list(item_ids),
        "scores": [int(x) for x in scores],
        "degeneracy": [float(x) for x in degs],
        "mean_score": float(np.mean(scores)),
        "mean_degeneracy": float(np.mean(degs)),
    }


def _bootstrap(a: Sequence[int], b: Sequence[int], seed: int):
    return lpc.paired_item_bootstrap(a, b, seed=seed)


def parse_args(argv: Sequence[str] | None = None):
    p = argparse.ArgumentParser()
    p.add_argument("--official-repo", required=True)
    p.add_argument("--out-dir", default=str(_REPO / "results" / "latent_positive_control_official_stage1_dev"))
    p.add_argument("--experiment-id", default="E-0017b-official-stolfo-latent-positive-control-stage1-dev")
    p.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct")
    p.add_argument("--model-revision", default=DEFAULT_MODEL_REVISION)
    p.add_argument("--device", default="cuda")
    p.add_argument("--cache-dir", default=os.environ.get("HF_HOME"))
    p.add_argument("--seed", type=int, default=20260817)
    p.add_argument("--n-extraction-per-keyword", type=int, default=7)
    p.add_argument("--n-dev-items", type=int, default=86)
    p.add_argument("--source-layers", default="24,26")
    p.add_argument("--alpha-grid", default="2,4,6,8,12,16,24")
    p.add_argument("--official-diagnostic-alpha", type=float, default=40.0)
    p.add_argument("--max-new-tokens-repr", type=int, default=2)
    p.add_argument("--max-generation-length", type=int, default=128)
    p.add_argument("--allow-test", action="store_true")
    args = p.parse_args(argv)
    if args.allow_test:
        raise SystemExit("TEST is hard-disabled in Stage-1 official rerun.")
    args.source_layers = [int(x) for x in str(args.source_layers).split(",") if str(x).strip()]
    args.alpha_grid = [float(x) for x in str(args.alpha_grid).split(",") if str(x).strip()]
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    t0 = time.time()
    started = _utcnow()
    np.random.seed(int(args.seed))

    official_repo = Path(args.official_repo).resolve()
    mods = _load_official_modules(official_repo)
    data_file = official_repo / "data" / "keywords" / "ifeval_single_keyword_include.jsonl"
    dev_rows = _read_jsonl(data_file)[: int(args.n_dev_items)]
    dev_words = {_official_keyword(r) for r in dev_rows}
    base_rows = _read_jsonl(official_repo / "data" / "ifeval_wo_instructions.jsonl")
    include_words = [line.strip() for line in (official_repo / "data" / "keywords" / "ifeval_keywords_include.txt").read_text(encoding="utf-8").splitlines() if line.strip()]
    extraction_rows: List[dict] = []
    phrasings = [
        ' Make sure to include the word "{}".',
        ' Please include the word "{}".',
        ' The output should contain the word "{}".',
        ' The output must contain the word "{}".',
        ' The output should say the word "{}".',
    ]
    # Recreate official keywords/compute_representations.py rows, but only for
    # DEV-needed words to avoid wasting GPU on unused IVs.
    for word in include_words:
        if word not in dev_words:
            continue
        for base in base_rows[: int(args.n_extraction_per_keyword)]:
            row = dict(base)
            row["prompt_no_instr"] = row.pop("model_output")
            row["prompt_without_instruction"] = row["prompt_no_instr"]
            row["prompt"] = row["prompt_no_instr"] + phrasings[0].format(word)
            row["kwargs"] = [{"keywords": [word]}]
            row["instruction_id_list"] = ["keywords:existence"]
            row["word"] = word
            extraction_rows.append(row)

    print(
        f"[official-lpc] method_repo={official_repo} dev_items={len(dev_rows)} "
        f"dev_words={len(dev_words)} extraction_rows={len(extraction_rows)} "
        f"source_layers={args.source_layers} alpha_grid={args.alpha_grid}",
        flush=True,
    )

    model, tokenizer = mods["model_utils"].load_model_from_tl_name(
        args.model,
        device=args.device,
        cache_dir=args.cache_dir,
        hf_model=False,
    )
    model.to(args.device)

    vectors = _mean_instruction_vectors(
        mods,
        model,
        tokenizer,
        extraction_rows,
        device=args.device,
        num_final_tokens=1,
        max_new_tokens=args.max_new_tokens_repr,
    )
    missing = sorted(dev_words - set(vectors))
    if missing:
        raise RuntimeError(f"missing official IVs for DEV words: {missing[:10]}")

    item_ids = [str(r.get("key", i)) for i, r in enumerate(dev_rows)]
    print("[official-lpc] generating baseline", flush=True)
    baseline_texts, baseline_scores, baseline_degs = _generate_baseline_or_prompt(
        mods, model, tokenizer, dev_rows,
        device=args.device, include_instructions=False,
        max_generation_length=args.max_generation_length,
    )
    print("[official-lpc] generating prompt comparator", flush=True)
    prompt_texts, prompt_scores, prompt_degs = _generate_baseline_or_prompt(
        mods, model, tokenizer, dev_rows,
        device=args.device, include_instructions=True,
        max_generation_length=args.max_generation_length,
    )

    candidates = []
    candidate_texts: Dict[str, list] = {}
    for layer in args.source_layers:
        for alpha in args.alpha_grid + [float(args.official_diagnostic_alpha)]:
            tag = f"layer{layer}_alpha{alpha:g}"
            print(f"[official-lpc] generating steer {tag}", flush=True)
            texts, scores, degs = _generate_steer(
                mods, model, tokenizer, dev_rows, vectors,
                device=args.device,
                source_layer_idx=layer,
                alpha=float(alpha),
                max_generation_length=args.max_generation_length,
            )
            mean_score = float(np.mean(scores))
            mean_deg = float(np.mean(degs))
            coh = lpc.coherence_ok(mean_deg, float(np.mean(baseline_degs)))
            selectable = float(alpha) in set(float(x) for x in args.alpha_grid)
            candidates.append({
                "source_layer_idx": int(layer),
                "alpha": float(alpha),
                "selectable_by_frozen_grid": selectable,
                "mean_score": mean_score,
                "mean_degeneracy": mean_deg,
                "coherence_ok": coh,
                "steer_minus_baseline": mean_score - float(np.mean(baseline_scores)),
                "steer_minus_prompt": mean_score - float(np.mean(prompt_scores)),
                "scores": [int(x) for x in scores],
                "degeneracy": [float(x) for x in degs],
            })
            candidate_texts[tag] = [{"item_id": iid, "text": text} for iid, text in zip(item_ids, texts)]

    selectable = [c for c in candidates if c["selectable_by_frozen_grid"]]
    selected = max(
        selectable,
        key=lambda c: (
            1 if c["coherence_ok"] else 0,
            c["steer_minus_baseline"],
            c["mean_score"],
            -c["mean_degeneracy"],
            -c["source_layer_idx"],
            -c["alpha"],
        ),
    )
    official_best = max(candidates, key=lambda c: (c["steer_minus_baseline"], c["mean_score"], 1 if c["coherence_ok"] else 0))

    primary = _bootstrap(selected["scores"], baseline_scores, args.seed + 101)
    secondary = _bootstrap(selected["scores"], prompt_scores, args.seed + 202)
    payload = {
        "experiment_id": args.experiment_id,
        "stage": "stage1_dev_only_no_test",
        "valid_for_paper": False,
        "official_repo": {
            "url": "https://github.com/microsoft/llm-steer-instruct",
            "commit": METHOD_SOURCE_COMMIT,
            "license": "MIT",
            "path": str(official_repo),
            "code_paths_used": [
                "utils/model_utils.py",
                "utils/generation_utils.py",
                "keywords/compute_representations.py logic",
                "keywords/evaluate.py logic",
                "ifeval_scripts/evaluation_main.py",
            ],
        },
        "model": args.model,
        "model_revision": args.model_revision,
        "data": {
            "dev_file": str(data_file),
            "dev_file_hash": _sha256_file(data_file),
            "n_dev_items": len(dev_rows),
            "n_extraction_per_keyword": args.n_extraction_per_keyword,
            "n_extraction_rows": len(extraction_rows),
            "task": "IFEval keywords:existence",
        },
        "frozen_procedure": {
            "primary_estimand": "steer_minus_baseline",
            "secondary_estimand": "steer_minus_prompt",
            "alpha_grid_selectable": args.alpha_grid,
            "official_diagnostic_alpha_not_selectable": args.official_diagnostic_alpha,
            "delta": lpc.DELTA,
            "bootstrap_b": lpc.BOOTSTRAP_B,
            "ci_level": lpc.BONFERRONI_CI_LEVEL,
            "coherence_gate": f"g^S <= {lpc.COHERENCE_MAX_RATIO} * g^0 + {lpc.COHERENCE_EPS_FLOOR}",
            "test_run": False,
        },
        "layer_alpha_source": {
            "official_keyword_config_default_layer": 24,
            "official_keyword_load_results_example_layer": 26,
            "official_keyword_load_results_example_weight": 40,
            "used_source_layers": args.source_layers,
            "note": "source_layer_idx is TransformerLens resid_post index used directly by official generation_utils hooks.",
        },
        "baseline": _cell(item_ids, baseline_scores, baseline_degs),
        "prompt": _cell(item_ids, prompt_scores, prompt_degs),
        "selected": selected,
        "official_diagnostic_best_any_alpha": official_best,
        "candidate_grid": candidates,
        "dev_effects": {
            "steer_minus_baseline": {
                "mean": primary.point,
                "ci_lo": primary.ci_lo,
                "ci_hi": primary.ci_hi,
                "b": primary.b,
                "ci_level": primary.ci_level,
                "passes_dev_sanity": bool(
                    primary.point >= lpc.DELTA
                    and selected["coherence_ok"]
                    and selected["mean_score"] > float(np.mean(baseline_scores))
                ),
            },
            "steer_minus_prompt": {
                "mean": secondary.point,
                "ci_lo": secondary.ci_lo,
                "ci_hi": secondary.ci_hi,
                "b": secondary.b,
                "ci_level": secondary.ci_level,
            },
        },
        "transcripts": {
            "baseline": [{"item_id": iid, "text": text} for iid, text in zip(item_ids, baseline_texts)],
            "prompt": [{"item_id": iid, "text": text} for iid, text in zip(item_ids, prompt_texts)],
            "steer": candidate_texts,
        },
        "run_metadata": {
            "started_at": started,
            "ended_at": _utcnow(),
            "wall_clock_seconds": round(time.time() - t0, 3),
            "host": platform.node(),
            "platform": platform.platform(),
            "python": sys.version,
            "code_commit": _git_commit(),
            "dirty_tree": _git_dirty(),
            "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
            "stage2_test_run": False,
        },
    }
    payload["config_hash"] = lpc.sha256_json({
        "model": args.model,
        "dev_file_hash": payload["data"]["dev_file_hash"],
        "n_dev_items": args.n_dev_items,
        "n_extraction_per_keyword": args.n_extraction_per_keyword,
        "source_layers": args.source_layers,
        "alpha_grid": args.alpha_grid,
        "official_diagnostic_alpha": args.official_diagnostic_alpha,
        "max_generation_length": args.max_generation_length,
        "max_new_tokens_repr": args.max_new_tokens_repr,
        "seed": args.seed,
    })

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "official_latent_positive_control_dev_results.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    summary = [
        "# Official Stolfo Latent Positive Control — Stage-1 DEV",
        "",
        f"- experiment_id: `{payload['experiment_id']}`",
        f"- valid_for_paper: `{payload['valid_for_paper']}`",
        f"- official repo commit: `{METHOD_SOURCE_COMMIT}`",
        f"- model: `{args.model}` @ `{args.model_revision}`",
        f"- task: IFEval `keywords:existence`, DEV n=`{len(dev_rows)}`",
        f"- source layers used: `{args.source_layers}`; selected layer `{selected['source_layer_idx']}`",
        f"- selected α: `{selected['alpha']}`",
        f"- baseline compliance: `{payload['baseline']['mean_score']:.6f}`",
        f"- prompt compliance: `{payload['prompt']['mean_score']:.6f}`",
        f"- steer compliance: `{selected['mean_score']:.6f}`",
        f"- primary steer-baseline: `{primary.point:.6f}` CI `{primary.ci_lo:.6f}, {primary.ci_hi:.6f}`; sanity_pass=`{payload['dev_effects']['steer_minus_baseline']['passes_dev_sanity']}`",
        f"- secondary steer-prompt: `{secondary.point:.6f}` CI `{secondary.ci_lo:.6f}, {secondary.ci_hi:.6f}`",
        f"- coherence: steer g=`{selected['mean_degeneracy']:.6f}`, baseline g0=`{payload['baseline']['mean_degeneracy']:.6f}`, ok=`{selected['coherence_ok']}`",
        f"- best diagnostic any α: layer `{official_best['source_layer_idx']}`, α `{official_best['alpha']}`, Δ `{official_best['steer_minus_baseline']:.6f}`, selectable=`{official_best['selectable_by_frozen_grid']}`",
        "",
        "No TEST item was generated or scored.",
    ]
    (out_dir / "official_latent_positive_control_dev_summary.md").write_text(
        "\n".join(summary) + "\n",
        encoding="utf-8",
    )
    print(f"[official-lpc] wrote {out_dir}", flush=True)
    return 0 if payload["dev_effects"]["steer_minus_baseline"]["passes_dev_sanity"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
