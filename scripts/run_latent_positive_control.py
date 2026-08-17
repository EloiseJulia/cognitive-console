"""Stage-1 DEV runner for the latent behavioral positive-control assay.

Hard boundary: this script intentionally implements DEV/smoke only. It never
runs the frozen TEST split; Stage-2 must add an explicit, audited TEST entry point
after Manager approval.
"""

from __future__ import annotations

import argparse
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
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cognitive_console.experiments import latent_positive_control as lpc
from cognitive_console.steering.generate import SteerConfig, SteeredHFBackend

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


def _render_chat(tokenizer, prompt: str, model_name: str) -> str:
    if hasattr(tokenizer, "apply_chat_template"):
        return tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}],
            tokenize=False,
            add_generation_prompt=True,
        )
    return prompt


def _candidate_source_layers(n_layers: int) -> List[int]:
    # Stolfo et al. format/find_best_layer.py uses range(n_layers // 5, n_layers, 2)
    # for non-Gemma models. These are 0-based decoder-block / TransformerLens
    # resid_post indices.
    return list(range(int(n_layers) // 5, int(n_layers), 2))


def _load_hf(model_name: str, device: str, dtype_name: str, cache_dir: str | None):
    try:
        import torch
        from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        raise SystemExit(
            "HF backend requires torch + transformers. Install optional GPU deps first."
        ) from exc

    dtype = getattr(torch, dtype_name, torch.float16)
    config = AutoConfig.from_pretrained(model_name, cache_dir=cache_dir)
    tok = AutoTokenizer.from_pretrained(model_name, cache_dir=cache_dir)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    tok.padding_side = "left"
    try:
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            cache_dir=cache_dir,
            torch_dtype=dtype,
            low_cpu_mem_usage=True,
        )
    except TypeError:
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            cache_dir=cache_dir,
            dtype=dtype,
            low_cpu_mem_usage=True,
        )
    model.to(device)
    model.eval()
    return model, tok, config


def _capture_all_layers(
    model,
    tokenizer,
    prompts: Sequence[str],
    *,
    model_name: str,
    device: str,
    max_length: int,
    batch_size: int,
) -> np.ndarray:
    """Return [n_layers+1, n_prompts, hidden_dim] last-token residual activations."""
    import torch

    base_model = getattr(model, "model", model)
    rows: List[np.ndarray] = []
    prompts = list(prompts)
    for start in range(0, len(prompts), int(batch_size)):
        batch = prompts[start : start + int(batch_size)]
        texts = [_render_chat(tokenizer, p, model_name) for p in batch]
        tokenizer.padding_side = "left"
        enc = tokenizer(
            texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=int(max_length),
        )
        enc = {k: v.to(device) for k, v in enc.items()}
        with torch.no_grad():
            out = base_model(**enc, output_hidden_states=True, use_cache=False)
        # Left padding means the final prompt token is at -1 for every row.
        hs = torch.stack([h[:, -1, :].to(torch.float32).cpu() for h in out.hidden_states])
        rows.append(hs.numpy())
        del out, hs
        if str(device).startswith("cuda"):
            torch.cuda.empty_cache()
    return np.concatenate(rows, axis=1)


def _generate_chunks(backend: SteeredHFBackend, prompts: Sequence[str], *, steer, max_new_tokens: int, batch_size: int) -> List[str]:
    outs: List[str] = []
    for start in range(0, len(prompts), int(batch_size)):
        chunk = list(prompts[start : start + int(batch_size)])
        outs.extend(backend.generate_batch(chunk, steer=steer, max_new_tokens=max_new_tokens, do_sample=False))
    return outs


def _run_synthetic(args, data: Dict[str, object], out_dir: Path) -> Dict[str, object]:
    keyword = str(data["keyword"])
    dev_items = list(data["dev_items"])[: int(args.n_dev_items)]
    ids = [str(x["id"]) for x in dev_items]
    baseline_texts = [f"A concise note about {i}." for i in ids]
    prompt_texts = [f"A concise note with {keyword} for {i}." for i in ids]
    baseline = lpc.CellScores.from_texts(ids, baseline_texts, keyword)
    prompt = lpc.CellScores.from_texts(ids, prompt_texts, keyword)
    candidates = []
    for source_layer in (5, 7, 9):
        for alpha in lpc.ALPHA_GRID:
            ok = float(alpha) >= 4.0 and source_layer == 7
            texts = [
                (f"A concise note with {keyword} for {i}." if ok else f"A concise note about {i}.")
                for i in ids
            ]
            if float(alpha) >= 24.0:
                texts = [t + (" repeat repeat repeat" * 8) for t in texts]
            steer = lpc.CellScores.from_texts(ids, texts, keyword)
            candidates.append(
                lpc.CandidateResult(
                    source_layer_idx=source_layer,
                    steering_hidden_state_layer=source_layer + 1,
                    alpha=float(alpha),
                    steer=steer,
                    baseline_mean_degeneracy=baseline.mean_degeneracy,
                    coherence_ok=lpc.coherence_ok(steer.mean_degeneracy, baseline.mean_degeneracy),
                    steer_minus_baseline=steer.mean_score - baseline.mean_score,
                )
            )
    selected = lpc.choose_candidate(candidates)
    config_hash = lpc.sha256_json(_config_payload(args, data, backend="synthetic"))
    payload = lpc.make_summary_payload(
        experiment_id=args.experiment_id,
        model="synthetic-keyword-positive-control",
        model_revision=None,
        method_source_commit=METHOD_SOURCE_COMMIT,
        data_hash=lpc.sha256_file(args.data),
        config_hash=config_hash,
        seed=args.seed,
        keyword=keyword,
        baseline=baseline,
        prompt=prompt,
        selected=selected,
        steer_minus_baseline_ci_seed=args.seed + 101,
        steer_minus_prompt_ci_seed=args.seed + 202,
    )
    payload["candidate_grid"] = [_candidate_to_json(c) for c in candidates]
    return payload


def _candidate_to_json(c: lpc.CandidateResult) -> Dict[str, object]:
    return {
        "source_layer_idx": c.source_layer_idx,
        "steering_hidden_state_layer": c.steering_hidden_state_layer,
        "alpha": c.alpha,
        "steer_mean": c.steer.mean_score,
        "steer_mean_degeneracy": c.steer.mean_degeneracy,
        "coherence_ok": c.coherence_ok,
        "steer_minus_baseline": c.steer_minus_baseline,
    }


def _config_payload(args, data: Dict[str, object], *, backend: str) -> Dict[str, object]:
    return {
        "stage": "stage1_dev_only_no_test",
        "backend": backend,
        "model": args.model,
        "model_revision": args.model_revision,
        "data_path": str(Path(args.data).as_posix()),
        "keyword": data["keyword"],
        "n_extraction_pairs": int(args.n_extraction_pairs),
        "n_dev_items": int(args.n_dev_items),
        "test_items_sealed_not_run": len(data["test_items"]),
        "alpha_grid": list(lpc.ALPHA_GRID),
        "candidate_layers": "Stolfo non-Gemma layer range: range(n_layers // 5, n_layers, 2)",
        "delta": lpc.DELTA,
        "bootstrap_b": lpc.BOOTSTRAP_B,
        "ci_level": lpc.BONFERRONI_CI_LEVEL,
        "coherence_max_ratio": lpc.COHERENCE_MAX_RATIO,
        "coherence_eps_floor": lpc.COHERENCE_EPS_FLOOR,
        "k_samples": lpc.K_SAMPLES,
        "greedy_deterministic": True,
        "max_new_tokens": int(args.max_new_tokens),
        "max_length": int(args.max_length),
        "seed": int(args.seed),
    }


def _run_hf(args, data: Dict[str, object], out_dir: Path) -> Dict[str, object]:
    import torch

    torch.manual_seed(int(args.seed))
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(int(args.seed))

    model, tok, config = _load_hf(args.model, args.device, args.dtype, args.hf_home)
    backend = SteeredHFBackend(
        args.model,
        device=args.device,
        dtype=args.dtype,
        max_length=args.max_length,
        seed=args.seed,
        model=model,
        tokenizer=tok,
        config=config,
    )
    n_layers = backend.num_hidden_layers
    source_layers = _candidate_source_layers(n_layers)
    hidden_layers = [x + 1 for x in source_layers]

    keyword = str(data["keyword"])
    instruction_template = str(data["instruction_template"])
    extraction = list(data["extraction_prompts"])[: int(args.n_extraction_pairs)]
    dev_items = list(data["dev_items"])[: int(args.n_dev_items)]
    ids = [str(x["id"]) for x in dev_items]
    dev_prompts = [str(x["prompt"]) for x in dev_items]
    dev_prompt_with_instr = [lpc.add_instruction(p, instruction_template, keyword) for p in dev_prompts]

    no_instr_prompts = [str(x["prompt"]) for x in extraction]
    with_instr_prompts = [lpc.add_instruction(p, instruction_template, keyword) for p in no_instr_prompts]

    print(f"[latent-pc] extracting directions: pairs={len(extraction)} layers={source_layers}", flush=True)
    hs_no = _capture_all_layers(
        model, tok, no_instr_prompts, model_name=args.model, device=args.device,
        max_length=args.max_length, batch_size=args.activation_batch_size,
    )
    hs_yes = _capture_all_layers(
        model, tok, with_instr_prompts, model_name=args.model, device=args.device,
        max_length=args.max_length, batch_size=args.activation_batch_size,
    )
    diffs = hs_yes - hs_no
    mean_diffs = diffs.mean(axis=1)  # [hidden_layer, hidden_dim]

    print("[latent-pc] generating baseline and prompt DEV cells", flush=True)
    baseline_texts = _generate_chunks(backend, dev_prompts, steer=None, max_new_tokens=args.max_new_tokens, batch_size=args.generation_batch_size)
    prompt_texts = _generate_chunks(backend, dev_prompt_with_instr, steer=None, max_new_tokens=args.max_new_tokens, batch_size=args.generation_batch_size)
    baseline = lpc.CellScores.from_texts(ids, baseline_texts, keyword)
    prompt = lpc.CellScores.from_texts(ids, prompt_texts, keyword)

    candidates = []
    all_texts: Dict[str, List[Dict[str, str]]] = {
        "baseline": [{"item_id": i, "text": t} for i, t in zip(ids, baseline_texts)],
        "prompt": [{"item_id": i, "text": t} for i, t in zip(ids, prompt_texts)],
    }
    for source_idx, hidden_idx in zip(source_layers, hidden_layers):
        direction = mean_diffs[hidden_idx]
        norm = float(np.linalg.norm(direction))
        if norm <= 1e-12:
            print(f"[latent-pc] skip layer={source_idx}: near-zero direction", flush=True)
            continue
        direction = direction / norm
        for alpha in lpc.ALPHA_GRID:
            print(f"[latent-pc] DEV layer={source_idx} hidden={hidden_idx} alpha={alpha}", flush=True)
            steer_cfg = SteerConfig(direction=direction, alpha=float(alpha), layer=hidden_idx)
            steer_texts = _generate_chunks(
                backend, dev_prompts, steer=steer_cfg,
                max_new_tokens=args.max_new_tokens, batch_size=args.generation_batch_size,
            )
            steer = lpc.CellScores.from_texts(ids, steer_texts, keyword)
            cand = lpc.CandidateResult(
                source_layer_idx=int(source_idx),
                steering_hidden_state_layer=int(hidden_idx),
                alpha=float(alpha),
                steer=steer,
                baseline_mean_degeneracy=baseline.mean_degeneracy,
                coherence_ok=lpc.coherence_ok(steer.mean_degeneracy, baseline.mean_degeneracy),
                steer_minus_baseline=steer.mean_score - baseline.mean_score,
            )
            candidates.append(cand)
            all_texts[f"steer_layer{source_idx}_alpha{alpha:g}"] = [
                {"item_id": i, "text": t} for i, t in zip(ids, steer_texts)
            ]
    selected = lpc.choose_candidate(candidates)
    config_hash = lpc.sha256_json(_config_payload(args, data, backend="hf"))
    payload = lpc.make_summary_payload(
        experiment_id=args.experiment_id,
        model=args.model,
        model_revision=args.model_revision,
        method_source_commit=METHOD_SOURCE_COMMIT,
        data_hash=lpc.sha256_file(args.data),
        config_hash=config_hash,
        seed=args.seed,
        keyword=keyword,
        baseline=baseline,
        prompt=prompt,
        selected=selected,
        steer_minus_baseline_ci_seed=args.seed + 101,
        steer_minus_prompt_ci_seed=args.seed + 202,
    )
    payload["candidate_grid"] = [_candidate_to_json(c) for c in candidates]
    payload["direction_extraction"] = {
        "n_pairs": len(extraction),
        "source_layer_indices": source_layers,
        "hidden_state_layers": hidden_layers,
        "selected_source_layer_idx": selected.source_layer_idx,
        "selected_steering_hidden_state_layer": selected.steering_hidden_state_layer,
        "stolfo_layer_rule": "non-Gemma validation layer search over range(n_layers // 5, n_layers, 2)",
    }
    payload["transcripts"] = all_texts
    return payload


def _write_outputs(payload: Dict[str, object], out_dir: Path, *, started_at: str, args) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    ended_at = _utcnow()
    payload["run_metadata"] = {
        "started_at": started_at,
        "ended_at": ended_at,
        "wall_clock_seconds": round(time.time() - args._t0, 3),
        "host": platform.node(),
        "platform": platform.platform(),
        "python": sys.version,
        "code_commit": _git_commit(),
        "dirty_tree": _git_dirty(),
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "stage2_test_run": False,
        "hard_boundary": "TEST split was loaded only for sealing/hash; no TEST item was generated or scored.",
    }
    results_path = out_dir / "latent_positive_control_dev_results.json"
    summary_path = out_dir / "latent_positive_control_dev_summary.md"
    results_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    sel = payload["selected"]
    primary = payload["dev_effects"]["steer_minus_baseline"]
    secondary = payload["dev_effects"]["steer_minus_prompt"]
    lines = [
        "# Latent Positive Control — Stage-1 DEV Summary",
        "",
        f"- experiment_id: `{payload['experiment_id']}`",
        f"- valid_for_paper: `{payload['valid_for_paper']}`",
        f"- model: `{payload['model']}` @ `{payload.get('model_revision')}`",
        f"- keyword verifier: whole-word `{payload['keyword']}` inclusion",
        f"- selected source_layer_idx: `{sel['source_layer_idx']}` (HF hidden-state layer `{sel['steering_hidden_state_layer']}`)",
        f"- selected alpha: `{sel['alpha']}`",
        f"- baseline DEV compliance: `{payload['baseline']['mean_score']:.6f}`",
        f"- prompt DEV compliance: `{payload['prompt']['mean_score']:.6f}`",
        f"- steer DEV compliance: `{sel['steer']['mean_score']:.6f}`",
        f"- primary DEV steer-baseline: `{primary['mean']:.6f}` CI `{primary['ci_lo']:.6f}, {primary['ci_hi']:.6f}`; sanity_pass=`{primary['passes_dev_sanity']}`",
        f"- secondary DEV steer-prompt: `{secondary['mean']:.6f}` CI `{secondary['ci_lo']:.6f}, {secondary['ci_hi']:.6f}`",
        f"- coherence: steer g=`{sel['steer']['mean_degeneracy']:.6f}`, baseline g0=`{sel['baseline_mean_degeneracy']:.6f}`, ok=`{sel['coherence_ok']}`",
        "",
        "No TEST item was generated or scored in this Stage-1 run.",
    ]
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[latent-pc] wrote {results_path}", flush=True)
    print(f"[latent-pc] wrote {summary_path}", flush=True)


def parse_args(argv: Sequence[str] | None = None):
    p = argparse.ArgumentParser()
    p.add_argument("--stage", choices=["dev", "smoke"], default="dev")
    p.add_argument("--backend", choices=["synthetic", "hf"], default="synthetic")
    p.add_argument("--data", default=str(_REPO / "data" / "latent_positive_control" / "keyword_blue_items.json"))
    p.add_argument("--out-dir", default=str(_REPO / "results" / "latent_positive_control_stage1_dev"))
    p.add_argument("--experiment-id", default="E-0017-latent-behavioral-positive-control-stage1-dev")
    p.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct")
    p.add_argument("--model-revision", default=DEFAULT_MODEL_REVISION)
    p.add_argument("--hf-home", default=os.environ.get("HF_HOME"))
    p.add_argument("--device", default="cuda")
    p.add_argument("--dtype", default="float16")
    p.add_argument("--seed", type=int, default=20260817)
    p.add_argument("--n-extraction-pairs", type=int, default=24)
    p.add_argument("--n-dev-items", type=int, default=12)
    p.add_argument("--max-new-tokens", type=int, default=64)
    p.add_argument("--max-length", type=int, default=256)
    p.add_argument("--activation-batch-size", type=int, default=4)
    p.add_argument("--generation-batch-size", type=int, default=4)
    p.add_argument("--allow-test", action="store_true", help="Reserved for Stage-2; currently rejected.")
    args = p.parse_args(argv)
    if args.allow_test:
        raise SystemExit("TEST is hard-disabled in Stage-1; wait for Manager Stage-2 GO.")
    if args.stage != "dev" and args.backend == "hf":
        raise SystemExit("HF backend is only used for Stage-1 DEV; use synthetic for smoke.")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    args._t0 = time.time()
    started = _utcnow()
    data = lpc.load_protocol_items(args.data)
    # Explicitly touch TEST only for sealing/hash visibility; never generate/score it.
    print(
        f"[latent-pc] stage={args.stage} backend={args.backend} dev_items={args.n_dev_items} "
        f"test_items_sealed_not_run={len(data['test_items'])}",
        flush=True,
    )
    out_dir = Path(args.out_dir)
    if args.backend == "synthetic":
        payload = _run_synthetic(args, data, out_dir)
    else:
        payload = _run_hf(args, data, out_dir)
    _write_outputs(payload, out_dir, started_at=started, args=args)
    primary = payload["dev_effects"]["steer_minus_baseline"]
    if args.stage == "dev" and not primary["passes_dev_sanity"]:
        print("[latent-pc] DEV sanity failed: steering did not improve over baseline under the frozen gate.", flush=True)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
