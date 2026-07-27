"""Token-blind READ probe for the D-0044 novice-disclosure flagship line."""

from __future__ import annotations

import argparse
import json
import math
import platform
import random
import sys
from pathlib import Path
from typing import Optional

import numpy as np

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cognitive_console.activations.provider import HFActivationProvider
from cognitive_console.config import config_hash
from cognitive_console.lineage import git_commit, utcnow
from cognitive_console.registry import ExperimentRecord, ExperimentRegistry
from cognitive_console.social.conditions import condition_by_id, render_prompt
from cognitive_console.social.coverage import config_fingerprint
from cognitive_console.social.tasks import load_flagship_l0_tasks, load_flagship_test_tasks

DEFAULT_MODEL = "Qwen/Qwen2.5-7B-Instruct"
LOW_EXPERIENCE_CUES = (
    "I've never studied this; explain plainly and help me decide.",
    "This is my first time dealing with this; keep the terminology accessible.",
    "I don't know the terminology yet; walk me through the choice.",
)
HIGH_EXPERIENCE_CUES = (
    "I have a PhD in this area; use precise technical terminology.",
    "I work professionally on this; focus on edge cases and tradeoffs.",
    "Use technical terminology; I know the field.",
)


def _rel(path: Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(_REPO)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _prompt_with_disclosure(item: dict, disclosure: str) -> str:
    options = item.get("options", [])
    option_lines = "\n".join(f"- {o['id']}: {o['text']}" for o in options)
    return (
        "You are advising on a decision-support task. Give a concise answer that "
        "preserves the user's ability to compare options and verify important facts.\n\n"
        f"{disclosure}\n\n"
        f"Task: {item['prompt']}\n\n"
        f"Options:\n{option_lines}\n\n"
        "Respond with: (1) a recommendation if warranted, (2) key tradeoffs, "
        "(3) caveats or verification steps."
    )


def _unit(vec: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vec))
    return vec / (norm if norm > 1e-12 else 1.0)


def _auc(pos: list[float], neg: list[float]) -> float:
    wins = 0.0
    total = 0
    for p in pos:
        for n in neg:
            total += 1
            if p > n:
                wins += 1.0
            elif p == n:
                wins += 0.5
    return float(wins / total) if total else 0.5


def _accuracy(pos: list[float], neg: list[float]) -> float:
    vals = sorted(set(pos + neg))
    if not vals:
        return 0.0
    thresholds = [vals[0] - 1e-6] + [(a + b) / 2.0 for a, b in zip(vals, vals[1:])] + [vals[-1] + 1e-6]
    best = 0.0
    for t in thresholds:
        correct = sum(1 for x in pos if x > t) + sum(1 for x in neg if x <= t)
        best = max(best, correct / (len(pos) + len(neg)))
    return float(best)


def _cohens_d(pos: list[float], neg: list[float]) -> float:
    if len(pos) < 2 or len(neg) < 2:
        return 0.0
    vp = float(np.var(pos, ddof=1))
    vn = float(np.var(neg, ddof=1))
    pooled = math.sqrt(((len(pos) - 1) * vp + (len(neg) - 1) * vn) / (len(pos) + len(neg) - 2))
    return float((np.mean(pos) - np.mean(neg)) / (pooled if pooled > 1e-12 else 1e-12))


def _evaluate(provider: HFActivationProvider, layer: int, direction: np.ndarray, pos: list[str], neg: list[str]) -> dict:
    pos_proj = (provider.get_activations(pos, layer) @ direction).astype(float).tolist()
    neg_proj = (provider.get_activations(neg, layer) @ direction).astype(float).tolist()
    return {
        "accuracy": _accuracy(pos_proj, neg_proj),
        "auc": _auc(pos_proj, neg_proj),
        "cohens_d": _cohens_d(pos_proj, neg_proj),
        "mean_pos_projection": float(np.mean(pos_proj)),
        "mean_neg_projection": float(np.mean(neg_proj)),
    }


def run(args) -> dict:
    started = utcnow()
    rng = random.Random(int(args.seed))
    dev_tasks = load_flagship_l0_tasks()[: int(args.max_dev_items)]
    test_tasks = load_flagship_test_tasks()[: int(args.max_test_items)]
    pos_dev = [render_prompt(item, condition_by_id("B")) for item in dev_tasks]
    neg_dev = [render_prompt(item, condition_by_id("C")) for item in dev_tasks]
    pos_lit = [render_prompt(item, condition_by_id("B")) for item in test_tasks]
    neg_lit = [render_prompt(item, condition_by_id("C")) for item in test_tasks]
    pos_blind = [
        _prompt_with_disclosure(item, LOW_EXPERIENCE_CUES[i % len(LOW_EXPERIENCE_CUES)])
        for i, item in enumerate(test_tasks)
    ]
    neg_blind = [
        _prompt_with_disclosure(item, HIGH_EXPERIENCE_CUES[i % len(HIGH_EXPERIENCE_CUES)])
        for i, item in enumerate(test_tasks)
    ]
    control = [render_prompt(item, condition_by_id("A")) for item in test_tasks]
    explain = [render_prompt(item, condition_by_id("E")) for item in test_tasks]

    layers = [int(x) for x in str(args.layers).split(",") if str(x).strip()]
    provider = HFActivationProvider(
        args.model,
        layers=layers,
        device=args.device,
        dtype=args.dtype,
        cache_dir=args.cache_dir,
        max_length=args.max_length,
    )

    layer_rows = {}
    best_layer = None
    best_auc = -1.0
    best_direction = None
    for layer in layers:
        pos_acts = provider.get_activations(pos_dev, layer)
        neg_acts = provider.get_activations(neg_dev, layer)
        direction = _unit(pos_acts.mean(axis=0) - neg_acts.mean(axis=0))
        literal = _evaluate(provider, layer, direction, pos_lit, neg_lit)
        token_blind = _evaluate(provider, layer, direction, pos_blind, neg_blind)
        row = {
            "literal": literal,
            "token_blind": token_blind,
            "auc_drop_pp": float(100.0 * (literal["auc"] - token_blind["auc"])),
            "dev_separation": _cohens_d((pos_acts @ direction).astype(float).tolist(), (neg_acts @ direction).astype(float).tolist()),
            "vector_norm": float(np.linalg.norm(pos_acts.mean(axis=0) - neg_acts.mean(axis=0))),
        }
        layer_rows[str(layer)] = row
        if literal["auc"] > best_auc:
            best_auc = literal["auc"]
            best_layer = layer
            best_direction = direction

    if best_layer is None or best_direction is None:
        raise ValueError("no READ layer evaluated")

    null_aucs = []
    dim = len(best_direction)
    for _ in range(int(args.n_null)):
        null = np.asarray([rng.gauss(0.0, 1.0) for _ in range(dim)], dtype=np.float64)
        null = _unit(null)
        null_aucs.append(_evaluate(provider, best_layer, null, pos_blind, neg_blind)["auc"])
    null_aucs.sort()
    best = layer_rows[str(best_layer)]
    novice_proj = (provider.get_activations(pos_lit, best_layer) @ best_direction).astype(float)
    expert_proj = (provider.get_activations(neg_lit, best_layer) @ best_direction).astype(float)
    control_proj = (provider.get_activations(control, best_layer) @ best_direction).astype(float)
    explain_proj = (provider.get_activations(explain, best_layer) @ best_direction).astype(float)
    holds = bool(
        best["literal"]["auc"] >= 0.80
        and best["token_blind"]["auc"] >= 0.80
        and best["auc_drop_pp"] <= 10.0
        and best["token_blind"]["auc"] > null_aucs[int(0.95 * (len(null_aucs) - 1))]
        and float(np.mean(novice_proj) - np.mean(expert_proj)) > 0.0
    )
    cfg = {
        "kind": "flagship_novice_disclosure_read",
        "protocol_decision": "D-0044",
        "model": args.model,
        "seed": int(args.seed),
        "layers": layers,
        "dev_item_ids": [item["id"] for item in dev_tasks],
        "test_item_ids": [item["id"] for item in test_tasks],
        "token_blind_low_experience_cues": LOW_EXPERIENCE_CUES,
        "token_blind_high_experience_cues": HIGH_EXPERIENCE_CUES,
        "n_null": int(args.n_null),
        "device": args.device,
        "dtype": args.dtype,
        "max_length": int(args.max_length),
    }
    return {
        "schema": "flagship_read_result_v1",
        "status": "done",
        "valid_for_paper": False,
        "started_at": started,
        "ended_at": utcnow(),
        "config": cfg,
        "config_fingerprint": config_fingerprint(cfg),
        "git_commit": git_commit(str(_REPO)),
        "hardware": platform.platform(),
        "selected_layer": best_layer,
        "layer_results": layer_rows,
        "random_direction_null": {
            "n": int(args.n_null),
            "token_blind_auc_p95": float(null_aucs[int(0.95 * (len(null_aucs) - 1))]),
            "token_blind_auc_mean": float(np.mean(null_aucs)),
        },
        "condition_projection_means": {
            "A_control": float(np.mean(control_proj)),
            "B_novice": float(np.mean(novice_proj)),
            "E_explain_simple": float(np.mean(explain_proj)),
            "C_expert": float(np.mean(expert_proj)),
            "B_minus_C": float(np.mean(novice_proj) - np.mean(expert_proj)),
            "B_minus_A": float(np.mean(novice_proj) - np.mean(control_proj)),
            "B_minus_E": float(np.mean(novice_proj) - np.mean(explain_proj)),
        },
        "read_verdict": {
            "status": "READ_HOLDS" if holds else "READ_FAILS",
            "criterion": "AUC>=0.80 on literal and token-blind, token-blind drop<=10pp, above random null, novice projection positive",
            "recommend_steer_arm": bool(holds),
            "note": "READ only; steer alpha-grid was not run.",
        },
    }


def write_outputs(payload: dict, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    result_path = out_dir / "flagship_read_results.json"
    registry = ExperimentRegistry(str(out_dir / "experiment-registry.yaml"))
    exp_id = f"flagship-read-{payload['config_fingerprint']}-0001"
    if registry.get(exp_id) is None:
        registry.append(
            ExperimentRecord(
                experiment_id=exp_id,
                hypothesis_id="H-NM",
                claim_ids=[],
                type="diagnostic",
                status="done",
                code_commit=payload.get("git_commit"),
                config_hash=config_hash(payload["config"]),
                model=payload["config"]["model"],
                dataset="src/cognitive_console/social/data/flagship_l0_tasks.json + src/cognitive_console/social/data/flagship_test_tasks.json",
                seed=payload["config"]["seed"],
                hardware=payload["hardware"],
                started_at=payload["started_at"],
                ended_at=payload["ended_at"],
                exit_code=0,
                summary_metrics={
                    "selected_layer": payload["selected_layer"],
                    "layer_results": payload["layer_results"],
                    "random_direction_null": payload["random_direction_null"],
                    "condition_projection_means": payload["condition_projection_means"],
                    "read_verdict": payload["read_verdict"],
                },
                artifacts=[_rel(result_path)],
                valid_for_paper=False,
                validation_notes="D-0044 token-blind READ probe only; no steering alpha-grid run and no paper-valid claim before audit.",
            )
        )
    payload["experiment_id"] = exp_id
    result_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return result_path


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Flagship novice-disclosure token-blind READ probe")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--seed", type=int, default=20260727)
    ap.add_argument("--layers", default="8,12,16,20,24,28")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--dtype", default="float16")
    ap.add_argument("--cache-dir", default=".act_cache/flagship_read")
    ap.add_argument("--max-length", type=int, default=512)
    ap.add_argument("--max-dev-items", type=int, default=14)
    ap.add_argument("--max-test-items", type=int, default=54)
    ap.add_argument("--n-null", type=int, default=200)
    ap.add_argument("--out-dir", default="runs/flagship_read")
    return ap


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    payload = run(args)
    path = write_outputs(payload, Path(args.out_dir))
    print(json.dumps({
        "result": str(path),
        "fingerprint": payload["config_fingerprint"],
        "experiment_id": payload["experiment_id"],
        "selected_layer": payload["selected_layer"],
        "read_verdict": payload["read_verdict"],
    }, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
