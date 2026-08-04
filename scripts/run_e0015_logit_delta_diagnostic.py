"""E-0015 logit-delta / transcript diagnostic.

Supporting diagnostic only: checks whether the scale-corrected E-0015 steering
path changes greedy completions and, where a clean first-token target exists,
changes target-token log probability.  This does not alter the frozen E-0015
adjudicator and is always valid_for_paper=false.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cognitive_console.experiments import adjudicate_c2b as adj
from cognitive_console.lineage import git_commit, utcnow
from cognitive_console.steering.generate import SteerConfig, SyntheticC2bTaskBackend
from scripts import run_c1_facade as c1
from scripts import run_positive_control_scale_corrected as e0015

EXPERIMENT_ID = "E-0015-logit-delta"
DEFAULT_OUT_DIR = _REPO / "results" / "E-0015-logit-delta"
DEFAULT_E0015_RESULTS = (
    _REPO / "results" / "E-0015-scale-corrected-positive-control" / "positive_control_scale_corrected_results.json"
)
SCOPE_NOTE = "supporting diagnostic for the genuine-null conclusion; not a preregistered confirmatory result"
TARGET_UNDEFINED_NOTE = "endpoint is not cleanly represented by a fixed single first-token target; transcripts + output-change only"


def token_change_fraction(a: str, b: str) -> float:
    """Whitespace-token Levenshtein distance normalized by the longer length."""
    xs = str(a).split()
    ys = str(b).split()
    if not xs and not ys:
        return 0.0
    prev = list(range(len(ys) + 1))
    for i, x in enumerate(xs, 1):
        cur = [i]
        for j, y in enumerate(ys, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return float(prev[-1]) / float(max(len(xs), len(ys), 1))


def _dedup_floats(values: Iterable[float]) -> List[float]:
    out: List[float] = []
    for value in values:
        f = float(value)
        if not any(abs(f - old) < 1e-12 for old in out):
            out.append(f)
    return out


def load_dev_frozen_betas(path: Path) -> Dict[str, float]:
    if not Path(path).exists():
        return {axis: 0.125 for axis in e0015.ALL_AXES}
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    out: Dict[str, float] = {}
    for axis in e0015.ALL_AXES:
        row = payload.get("axes", {}).get(axis, {})
        beta = (
            row.get("pc2a_steer_vs_neutral_baseline", {})
            .get("selected_scale", {})
            .get("beta")
        )
        if beta is None:
            beta = 0.125
        out[axis] = float(beta)
    return out


def beta_grid_for_axis(axis: str, dev_betas: Dict[str, float]) -> List[float]:
    return _dedup_floats([float(dev_betas.get(axis, 0.125)), 1.0, 2.0])


def target_token_spec(axis: str, item: Dict[str, object]) -> Dict[str, object]:
    if axis == e0015.REFUSAL_AXIS:
        return {
            "defined": True,
            "kind": "refusal_leading_first_tokens",
            "candidate_texts": ["I", " I", "Sorry", " Sorry", "I'm", " I'm", "I’m", " I’m", "Unfortunately", " Unfortunately"],
            "note": "logsumexp over unique first token ids for common refusal-leading strings",
        }
    if axis == "skepticism":
        letter = str(item.get("answer_letter") or item.get("answer") or "").strip().upper()
        if len(letter) == 1 and letter.isalpha():
            return {
                "defined": True,
                "kind": "correct_answer_letter_first_token",
                "candidate_texts": [letter, " " + letter, f"{letter}.", f" {letter}.", f"{letter})", f" {letter})"],
                "note": "item-specific correct MC letter; does not include the generic 'Answer:' token",
            }
    return {"defined": False, "kind": None, "candidate_texts": [], "note": TARGET_UNDEFINED_NOTE}


def _logsumexp(values: Sequence[float]) -> Optional[float]:
    vals = [float(v) for v in values]
    if not vals:
        return None
    m = max(vals)
    return float(m + math.log(sum(math.exp(v - m) for v in vals)))


def hf_first_position_target_logprob(backend, prompt: str, steer: Optional[SteerConfig], candidate_texts: Sequence[str]) -> Optional[float]:
    """Log P(any target first token | prompt), with the same HF hook path as generation."""
    if not candidate_texts:
        return None
    import torch

    backend._ensure_loaded()
    tokenizer = backend._tokenizer
    token_ids = []
    for text in candidate_texts:
        ids = tokenizer.encode(str(text), add_special_tokens=False)
        if ids:
            token_ids.append(int(ids[0]))
    token_ids = sorted(set(token_ids))
    if not token_ids:
        return None

    rendered = backend._render_user_chat_prompt(tokenizer, prompt, backend.model_name)
    enc = tokenizer(rendered, return_tensors="pt", truncation=True, max_length=backend.max_length)
    enc = {k: v.to(backend.device) for k, v in enc.items()}

    handle = None
    if steer is not None and abs(float(steer.alpha)) > 1e-12:
        n = int(backend._config.num_hidden_layers)
        if not (1 <= int(steer.layer) <= n):
            raise ValueError(f"steer.layer {steer.layer} out of range 1..{n}")
        handle = backend._layers[int(steer.layer) - 1].register_forward_hook(backend._make_hook(steer))
    try:
        with torch.no_grad():
            logits = backend._model(**enc, use_cache=False).logits[0, -1, :]
            logprobs = torch.log_softmax(logits, dim=-1)
            return _logsumexp([float(logprobs[i].detach().cpu()) for i in token_ids])
    finally:
        if handle is not None:
            handle.remove()


def _synthetic_backend(axis: str, items: Sequence[Dict[str, object]]) -> SyntheticC2bTaskBackend:
    if axis == e0015.REFUSAL_AXIS:
        return SyntheticC2bTaskBackend(
            axis, items, instruction_markers=["refuse", "decline", "answer nothing", "do not answer"],
            prompt_gain=0.15, alpha_gain=0.10, threshold=0.50,
        )
    return SyntheticC2bTaskBackend(axis, items, prompt_gain=0.40, alpha_gain=0.08, threshold=0.50)


def _load_and_check_probe_items(axis: str, *, backend: str, use_fixture: bool, k_probes: int) -> List[Dict[str, object]]:
    # HF integrity guards require the full frozen real pool (>=60/80) before the
    # diagnostic takes its tiny fixed K probe prefix. Synthetic smoke may load only K.
    load_n = int(k_probes) if backend == "synthetic" else None
    pool = e0015.load_items_for_axis(axis, use_fixture, load_n)
    e0015.assert_item_pool_for_axis(axis, pool, backend=backend)
    return list(pool)[: int(k_probes)]


def _derive_bundles(args, out_dir: Path):
    shared_hf = e0015.build_shared_hf_handles(args.model, args.seed, out_dir) if args.backend == "hf" else None
    bundles = {
        e0015.REFUSAL_AXIS: e0015.derive_refusal_direction(
            args.backend, args.model, args.n_refusal_extraction, args.seed, out_dir, shared_hf=shared_hf
        )
    }
    for axis in e0015.METACOG_AXES:
        bundles[axis] = e0015.derive_metacog_direction(
            axis, args.backend, args.model, args.n_metacog_extraction, args.seed, out_dir, shared_hf=shared_hf
        )
    if args.backend == "hf":
        e0015.record_upfront_hook_bites_all_axes(bundles, out_dir)
    return bundles, shared_hf


def run(args) -> Dict[str, object]:
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.backend == "hf" and (args.use_fixture or args.n_items is not None):
        raise SystemExit("hf diagnostic must use real data; --use-fixture/--n-items forbidden")
    if args.backend == "hf" and (int(args.seed) != 20260723 or int(args.n_metacog_extraction) != 28):
        raise SystemExit("hf diagnostic requires seed=20260723 and n_metacog_extraction=28 for frozen E-0015 direction reuse")

    use_fixture = bool(args.use_fixture if args.use_fixture is not None else args.backend == "synthetic")
    dev_betas = load_dev_frozen_betas(Path(args.e0015_results_json))
    bundles, shared_hf = _derive_bundles(args, out_dir)
    neutral_instruction = c1.load_neutral_prompts()[0]

    transcript_path = out_dir / "transcripts.jsonl"
    axis_payload: Dict[str, object] = {}
    transcript_count = 0
    with transcript_path.open("w", encoding="utf-8") as tx:
        for axis, bundle in bundles.items():
            items = _load_and_check_probe_items(
                axis, backend=args.backend, use_fixture=use_fixture, k_probes=int(args.k_probes)
            )
            gen = shared_hf.hook_backend if shared_hf is not None else _synthetic_backend(axis, items)
            beta_payload: Dict[str, object] = {}
            for beta in beta_grid_for_axis(axis, dev_betas):
                alpha_eff = float(beta) * bundle.vector_norm
                steer = SteerConfig(direction=np.asarray(bundle.direction, dtype=np.float64), alpha=alpha_eff, layer=int(bundle.layer))
                changes: List[float] = []
                logprob_deltas: List[float] = []
                target_defined_any = False
                target_notes: List[str] = []
                for item in items:
                    prompt = adj.format_task_input(axis, neutral_instruction, item)
                    baseline = gen.generate(prompt, None, args.max_new_tokens)
                    steered = gen.generate(prompt, steer, args.max_new_tokens)
                    change = token_change_fraction(baseline, steered)
                    changes.append(change)
                    spec = target_token_spec(axis, item)
                    target_defined_any = target_defined_any or bool(spec["defined"])
                    if str(spec["note"]) not in target_notes:
                        target_notes.append(str(spec["note"]))
                    base_lp = steer_lp = delta = None
                    if args.backend == "hf" and spec["defined"]:
                        base_lp = hf_first_position_target_logprob(gen, prompt, None, spec["candidate_texts"])
                        steer_lp = hf_first_position_target_logprob(gen, prompt, steer, spec["candidate_texts"])
                        if base_lp is not None and steer_lp is not None:
                            delta = float(steer_lp - base_lp)
                            logprob_deltas.append(delta)
                    record = {
                        "experiment_id": EXPERIMENT_ID,
                        "valid_for_paper": False,
                        "axis": axis,
                        "item_id": str(item.get("id")),
                        "beta": float(beta),
                        "alpha_eff": alpha_eff,
                        "layer": int(bundle.layer),
                        "direction_sha256": bundle.provenance.get("direction_sha256"),
                        "prompt": prompt,
                        "baseline_completion": baseline,
                        "steered_completion": steered,
                        "output_change_fraction": change,
                        "target_token_signal": {
                            "defined": bool(spec["defined"]),
                            "kind": spec["kind"],
                            "candidate_texts": spec["candidate_texts"],
                            "baseline_logprob": base_lp,
                            "steered_logprob": steer_lp,
                            "delta_steer_minus_baseline": delta,
                            "note": spec["note"],
                        },
                    }
                    tx.write(json.dumps(record, ensure_ascii=False) + "\n")
                    transcript_count += 1
                beta_payload[str(float(beta))] = {
                    "beta": float(beta),
                    "alpha_eff": alpha_eff,
                    "n_items": len(items),
                    "mean_output_change_fraction": float(mean(changes)) if changes else None,
                    "mean_target_token_logprob_delta_steer_minus_baseline": (
                        float(mean(logprob_deltas)) if logprob_deltas else None
                    ),
                    "target_token_signal_defined": bool(target_defined_any),
                    "target_token_notes": target_notes,
                }
            axis_payload[axis] = {
                "axis": axis,
                "layer": int(bundle.layer),
                "vector_norm": bundle.vector_norm,
                "dev_frozen_beta_source": str(Path(args.e0015_results_json)),
                "dev_frozen_beta": float(dev_betas.get(axis, 0.125)),
                "betas_evaluated": beta_grid_for_axis(axis, dev_betas),
                "direction_provenance": bundle.provenance,
                "by_beta": beta_payload,
            }

    payload = {
        "experiment_id": EXPERIMENT_ID,
        "valid_for_paper": False,
        "scope_note": SCOPE_NOTE,
        "status": "synthetic_smoke" if args.backend == "synthetic" else "hf_diagnostic_ready_for_audit",
        "generated_at": utcnow(),
        "code_commit": git_commit(str(_REPO)),
        "backend": args.backend,
        "model": "synthetic-offline" if args.backend == "synthetic" else args.model,
        "seed": int(args.seed),
        "k_probes_per_axis": int(args.k_probes),
        "max_new_tokens": int(args.max_new_tokens),
        "generation": {"do_sample": False, "temperature": None, "greedy": True},
        "single_shared_hf_model_handle": {
            "enabled": bool(args.backend == "hf"),
            "from_pretrained_model_loads_by_design": 1 if args.backend == "hf" else 0,
            "shared_across": ["direction_derivation", "hook_bites", "greedy_transcripts", "first_position_logprob_forwards"],
        },
        "real_not_smoke_hf": {
            "asserted": bool(args.backend == "hf"),
            "mechanism": "E-0015 derive_refusal_direction/derive_metacog_direction + assert_real_not_smoke_scale_direction",
            "synthetic_or_placeholder_forbidden_on_hf": True,
        },
        "artifacts": {
            "diagnostic_json": str(out_dir / "diagnostic.json"),
            "transcripts_jsonl": str(transcript_path),
        },
        "transcript_records": transcript_count,
        "axes": axis_payload,
    }
    (out_dir / "diagnostic.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "experiment_id": EXPERIMENT_ID,
        "backend": args.backend,
        "out_dir": str(out_dir),
        "transcript_records": transcript_count,
        "valid_for_paper": False,
    }, indent=2))
    return payload


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Run E-0015 logit-delta/transcript diagnostic")
    ap.add_argument("--backend", choices=["synthetic", "hf"], default="synthetic")
    ap.add_argument("--model", default=e0015.DEFAULT_MODEL)
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    ap.add_argument("--e0015-results-json", default=str(DEFAULT_E0015_RESULTS))
    ap.add_argument("--seed", type=int, default=20260723)
    ap.add_argument("--k-probes", type=int, default=5)
    ap.add_argument("--n-items", type=int, default=None, help="synthetic/debug cap only")
    ap.add_argument("--n-refusal-extraction", type=int, default=40)
    ap.add_argument("--n-metacog-extraction", type=int, default=28)
    ap.add_argument("--max-new-tokens", type=int, default=64)
    ap.add_argument("--use-fixture", action=argparse.BooleanOptionalAction, default=None)
    return ap


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    run(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
