"""Regenerate deliberation steering at 512 tokens for avg-prompt comparator repair.

This is a narrow audit repair for the average-prompt comparator arm: the
candidate-prompt side already used max_new_tokens=512, while the frozen
best-prompt steering arrays were generated with 64 tokens. This script keeps
the frozen TEST split, frozen alpha, frozen layer/direction construction, and
frozen scorers, regenerates only the deliberation steering side at 512 tokens,
then recomputes paired contrasts against the existing 512 candidate-prompt
outcomes.
"""

from __future__ import annotations

import argparse
import gc
import json
import platform
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cognitive_console.activations.provider import HFActivationProvider
from cognitive_console.config import config_hash
from cognitive_console.experiments import adjudicate_c2b as adj
from cognitive_console.experiments.adjudicate_c2b import (
    AxisAdjSpec,
    ProgressTracker,
    RunContext,
)
from cognitive_console.lineage import git_commit, new_experiment_id, utcnow
from cognitive_console.registry import ExperimentRecord, ExperimentRegistry
from cognitive_console.steering.extract import min_layer_for_depth
from cognitive_console.steering.iti import extract_iti

from scripts import run_c1_facade as c1
from scripts import run_c2b_adjudication as c2b
from scripts import run_gpu_phase0 as p0

DEFAULT_MODEL = "Qwen/Qwen2.5-7B-Instruct"
DEFAULT_REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"


def _rel(path: Path) -> str:
    p = Path(path).resolve()
    try:
        return str(p.relative_to(_REPO)).replace("\\", "/")
    except ValueError:
        return str(p).replace("\\", "/")


def _load_frozen_axis(path: Path, axis: str) -> Dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    for row in data["axes"]:
        if row["axis"] == axis:
            return row
    raise ValueError(f"{path} has no axis={axis}")


def _load_avg_axis(path: Path, axis: str) -> Dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    for row in data["axes"]:
        if row["axis"] == axis:
            return row
    raise ValueError(f"{path} has no axis={axis}")


def _fixed_spec_and_scale(*, method: str, axis: str, layer: int, model: str,
                          revision: str, n_extraction: int, seed: int,
                          out_dir: Path) -> tuple[AxisAdjSpec, Dict[str, float], Dict]:
    device, dtype = p0._pick_device(), p0._pick_dtype()
    provider = HFActivationProvider(
        model,
        device=device,
        dtype=dtype,
        cache_dir=str(out_dir / "c1_fixed" / method / "activations" / "cache"),
        model_revision=revision,
    )
    neutral = c1.load_neutral_prompts()[0]
    alpha_scale_by_axis = {axis: 1.0}
    meta: Dict[str, object] = {"fixed_layer": int(layer)}
    if method == "caa":
        direction = p0._extract_direction(provider, axis, int(layer), n_extraction, seed)
        meta["direction_source"] = "CAA mean-difference at frozen layer"
    elif method == "iti":
        pairs = c1.load_axis_pairs(axis)
        split = c1.make_split(list(pairs.pos.keys()), n_extraction=n_extraction, seed=seed)
        ext_pos = [pairs.pos[p] for p in split.extraction_ids]
        ext_neg = [pairs.neg[p] for p in split.extraction_ids]
        iti = extract_iti(
            provider,
            axis=axis,
            pos_texts=ext_pos,
            neg_texts=ext_neg,
            layers=[int(layer)],
            selection="separation",
            neutral_texts=c1.load_neutral_prompts(),
            min_layer=min_layer_for_depth(max(provider.available_layers()), min_depth_frac=0.2),
            n_null=2000,
            null_seed=seed,
        )
        direction = iti.direction
        alpha_scale_by_axis[axis] = float(iti.sigma)
        meta.update({
            "direction_source": "ITI logistic-probe direction at frozen layer",
            "iti_sigma": float(iti.sigma),
            "iti_probe_norm": float(np.linalg.norm(iti.vector)),
        })
    else:
        raise ValueError(f"unsupported method {method!r}")
    items = c2b.load_axis_items(axis, False, None)
    spec = AxisAdjSpec(
        axis=axis,
        items=items,
        strong_prompts=c2b.build_strong_prompts(axis, 16),
        neutral_prompt=neutral,
        direction=direction,
        layer=int(layer),
    )
    del provider
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass
    return spec, alpha_scale_by_axis, meta


def _stats(name: str, lhs: np.ndarray, rhs: np.ndarray, *,
           seed: int, bootstrap_b: int, coherence_ok: bool) -> Dict:
    diff = np.asarray(lhs, dtype=float) - np.asarray(rhs, dtype=float)
    ci = adj.cluster_bootstrap_ci(
        diff,
        b=int(bootstrap_b),
        ci_level=adj.BONFERRONI_CI_LEVEL,
        seed=int(seed),
        cluster=True,
    )
    return {
        "name": name,
        "mean_diff": ci.point,
        "ci_lo": ci.ci_lo,
        "ci_hi": ci.ci_hi,
        "ci_level": ci.ci_level,
        "bootstrap_b": int(bootstrap_b),
        "delta": adj.DELTA,
        "coherence_ok": bool(coherence_ok),
        "passed": adj.axis_pass(ci.point, ci.ci_lo, ci.ci_hi, coherence_ok, delta=adj.DELTA),
        "per_item_diff": [float(x) for x in diff],
    }


def _format_compliance(transcript_root: Path, axis: str) -> Dict:
    rows: List[Dict] = []
    for path in transcript_root.glob(f"{axis}__test_steer_512__*.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    failures = sum(1 for r in rows if (r.get("parse") or {}).get("axis_parse_failed"))
    n = len(rows)
    return {
        "available": True,
        "source": _rel(transcript_root),
        "steering_samples": n,
        "parse_failures": failures,
        "format_compliance_rate": None if n == 0 else 1.0 - failures / n,
    }


def run_one(args, *, method: str, avg_path: Path, frozen_path: Path,
            alpha: float, layer: int, out_dir: Path) -> Path:
    axis = "deliberation"
    t0 = time.time()
    started_at = utcnow()
    out_dir.mkdir(parents=True, exist_ok=True)
    avg_row = _load_avg_axis(avg_path, axis)
    frozen_row = _load_frozen_axis(frozen_path, axis)
    if int(frozen_row["layer"]) != int(layer):
        raise SystemExit(f"{method}: frozen layer mismatch: source={frozen_row['layer']} requested={layer}")
    if float(frozen_row["dev_selection"]["frozen_alpha"]) != float(alpha):
        raise SystemExit(
            f"{method}: frozen alpha mismatch: source={frozen_row['dev_selection']['frozen_alpha']} requested={alpha}"
        )

    spec, alpha_scale_by_axis, dir_meta = _fixed_spec_and_scale(
        method=method,
        axis=axis,
        layer=layer,
        model=args.model,
        revision=args.model_revision,
        n_extraction=args.n_extraction,
        seed=args.seed,
        out_dir=out_dir,
    )
    ids = [str(it["id"]) for it in spec.items]
    by_id = {str(it["id"]): it for it in spec.items}
    split = adj.split_dev_test(ids, seed=args.seed)
    test_items = [by_id[i] for i in split.test_ids]
    test_item_ids = [str(it["id"]) for it in test_items]
    if test_item_ids != list(avg_row["test_item_ids"]):
        raise SystemExit(f"{method}: TEST item ordering mismatch with avg-prompt source")

    collector = c2b.TranscriptCollector(out_dir, args.model, method, "hf")
    sampler = c2b.hf_sampler_factory(
        args.model,
        args.max_new_tokens,
        args.temperature,
        args.seed,
        args.batch_size,
        collector,
        alpha_scale_by_axis,
        model_revision=args.model_revision,
    )(axis)
    fp = config_hash({
        "kind": "delib_512_steer_repair",
        "method": method,
        "axis": axis,
        "model": args.model,
        "model_revision": args.model_revision,
        "seed": args.seed,
        "alpha": alpha,
        "layer": layer,
        "max_new_tokens": args.max_new_tokens,
        "avg_source": _rel(avg_path),
        "frozen_source": _rel(frozen_path),
    }).replace("sha256:", "")[:16]
    ckpt = c2b.TranscriptCheckpointStore(
        out_dir / "checkpoints",
        fp,
        seed=args.seed,
        fresh=args.fresh,
        collector=collector,
    )
    ctx = RunContext(checkpoint=ckpt, progress=ProgressTracker(len(test_items) * adj.K_SAMPLES * 2))
    try:
        steer_out, steer_deg, steer_mat = adj._channel_item_outcomes(
            sampler,
            axis,
            test_items,
            spec.neutral_prompt,
            float(alpha),
            adj.K_SAMPLES,
            spec.direction,
            spec.layer,
            ctx=ctx,
            phase="test_steer_512",
            cell_key=f"alpha={float(alpha)}|max_new_tokens={args.max_new_tokens}",
        )
        _, base_deg, _ = adj._channel_item_outcomes(
            sampler,
            axis,
            test_items,
            spec.neutral_prompt,
            0.0,
            adj.K_SAMPLES,
            spec.direction,
            spec.layer,
            ctx=ctx,
            phase="test_baseline_512",
            cell_key=f"alpha=0|max_new_tokens={args.max_new_tokens}",
        )
    finally:
        ckpt.close()

    steer_mean = float(np.mean(steer_out))
    if steer_mean < float(args.min_steer_mean):
        # Persist enough evidence before aborting so the failure is auditable.
        (out_dir / "HARD_ABORT_steering_floor.json").write_text(
            json.dumps({
                "method": method,
                "axis": axis,
                "steer_mean": steer_mean,
                "min_steer_mean": float(args.min_steer_mean),
                "note": "512-token steering still failed validity floor; no workaround/reselection attempted",
            }, indent=2) + "\n",
            encoding="utf-8",
        )
        raise SystemExit(f"{method}: 512 steering validity failed, mean={steer_mean:.4f}")

    transcript_root = out_dir / "transcripts"
    transcript_root.mkdir(parents=True, exist_ok=True)
    collector._write_cell_files(transcript_root, {})

    avg16 = np.asarray(avg_row["primary_avg16"]["per_item_comparator"], dtype=float)
    best_id = str(avg_row["best_prompt_id"])
    best512 = np.asarray(avg_row["candidate_outcomes_by_prompt"][best_id], dtype=float)
    frozen_best = np.asarray(frozen_row["per_item_prompt"], dtype=float)
    if len(frozen_best) != len(steer_out):
        raise SystemExit(f"{method}: frozen best length mismatch")

    test_steer_deg = float(np.mean(steer_deg))
    test_base_deg = float(np.mean(base_deg))
    coherence_ok = (
        test_steer_deg
        <= adj.COHERENCE_MAX_RATIO * test_base_deg + adj.COHERENCE_EPS_FLOOR + 1e-12
    )
    result = {
        "generated_at": utcnow(),
        "started_at": started_at,
        "wall_clock_seconds": round(time.time() - t0, 2),
        "backend": "hf",
        "model": args.model,
        "model_revision": args.model_revision,
        "method": method,
        "axis": axis,
        "seed": args.seed,
        "max_new_tokens": args.max_new_tokens,
        "batch_size": args.batch_size,
        "valid_for_paper": False,
        "protocol_frozen": True,
        "repair_note": "deliberation steering regenerated at 512 tokens; frozen E-0005/E-0006 left read-only",
        "frozen_alpha": float(alpha),
        "layer": int(layer),
        "n_test": len(test_items),
        "test_item_ids": test_item_ids,
        "per_item_steer_512": [float(x) for x in steer_out],
        "per_sample_steer_512": np.asarray(steer_mat, dtype=float).tolist(),
        "steer_512_mean_accuracy": steer_mean,
        "validity_check": {
            "min_steer_mean": float(args.min_steer_mean),
            "passed": True,
            "old_frozen_64_steer_mean": float(np.mean(frozen_row["per_item_steer"])),
        },
        "comparators": {
            "avg16_512": [float(x) for x in avg16],
            "best_prompt_512": [float(x) for x in best512],
            "best_prompt_frozen_64": [float(x) for x in frozen_best],
        },
        "contrasts": {
            "steer512_minus_avg512": _stats(
                "steer512_minus_avg512", steer_out, avg16,
                seed=args.seed, bootstrap_b=args.bootstrap_b, coherence_ok=coherence_ok,
            ),
            "steer512_minus_best512": _stats(
                "steer512_minus_best512", steer_out, best512,
                seed=args.seed, bootstrap_b=args.bootstrap_b, coherence_ok=coherence_ok,
            ),
            "avg512_minus_frozen_best64": _stats(
                "avg512_minus_frozen_best64", avg16, frozen_best,
                seed=args.seed, bootstrap_b=args.bootstrap_b, coherence_ok=True,
            ),
        },
        "coherence": {
            "coherence_ok": coherence_ok,
            "test_steer_degeneracy": test_steer_deg,
            "test_baseline_degeneracy": test_base_deg,
            "max_ratio": adj.COHERENCE_MAX_RATIO,
            "eps_floor": adj.COHERENCE_EPS_FLOOR,
        },
        "format_compliance": _format_compliance(transcript_root, axis),
        "sources": {
            "avg_prompt_512_result": _rel(avg_path),
            "frozen_best_prompt_result": _rel(frozen_path),
        },
        "direction_meta": dir_meta,
        "platform": platform.platform(),
    }
    result_path = out_dir / "delib_512_steer_repair_results.json"
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    rows_path = out_dir / "delib_512_steer_per_item.jsonl"
    with open(rows_path, "w", encoding="utf-8") as fh:
        for i, item_id in enumerate(test_item_ids):
            fh.write(json.dumps({
                "item_id": item_id,
                "steer512": float(steer_out[i]),
                "avg512": float(avg16[i]),
                "best512": float(best512[i]),
                "frozen_best64": float(frozen_best[i]),
            }, ensure_ascii=False) + "\n")

    reg = ExperimentRegistry(str(out_dir / "experiment-registry.yaml"))
    cfg_hash = config_hash({
        "kind": "delib_512_steer_repair",
        "method": method,
        "model": args.model,
        "model_revision": args.model_revision,
        "alpha": alpha,
        "layer": layer,
        "seed": args.seed,
        "max_new_tokens": args.max_new_tokens,
    })
    exp_id = new_experiment_id(reg, "avg-prompt-delib512", cfg_hash)
    reg.append(ExperimentRecord(
        experiment_id=exp_id,
        hypothesis_id="H-AVG-PROMPT",
        claim_ids=["C2b"],
        type="diagnostic",
        status="done",
        code_commit=git_commit(str(_REPO)),
        dirty_tree=False,
        config_hash=cfg_hash,
        model=args.model,
        dataset="data/c2b_tasks/deliberation + existing avg-prompt candidate outcomes",
        seed=args.seed,
        hardware=f"{p0._pick_device()}-{p0._pick_dtype()}",
        started_at=started_at,
        ended_at=utcnow(),
        exit_code=0,
        summary_metrics={
            "steer_512_mean_accuracy": steer_mean,
            "steer512_minus_avg512": result["contrasts"]["steer512_minus_avg512"],
            "steer512_minus_best512": result["contrasts"]["steer512_minus_best512"],
            "avg512_minus_frozen_best64": result["contrasts"]["avg512_minus_frozen_best64"],
            "coherence_ok": coherence_ok,
        },
        artifacts=[_rel(result_path), _rel(rows_path), _rel(transcript_root)],
        valid_for_paper=False,
        validation_notes="512-token deliberation steering repair; valid_for_paper=false until hostile audit and Manager/owner fold gate.",
    ))
    print(f"[delib512] {method} wrote {_rel(result_path)} exp={exp_id}", flush=True)
    return result_path


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Regenerate deliberation steering at 512 tokens")
    ap.add_argument("--method", choices=["caa", "iti"], required=True)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--model-revision", default=DEFAULT_REVISION)
    ap.add_argument("--avg-result", required=True)
    ap.add_argument("--frozen-result", required=True)
    ap.add_argument("--alpha", type=float, required=True)
    ap.add_argument("--layer", type=int, required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--seed", type=int, default=20260723)
    ap.add_argument("--n-extraction", type=int, default=28)
    ap.add_argument("--max-new-tokens", type=int, default=512)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--bootstrap-b", type=int, default=adj.BOOTSTRAP_B)
    ap.add_argument("--min-steer-mean", type=float, default=0.5)
    ap.add_argument("--fresh", action="store_true")
    return ap


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    run_one(
        args,
        method=args.method,
        avg_path=Path(args.avg_result),
        frozen_path=Path(args.frozen_result),
        alpha=args.alpha,
        layer=args.layer,
        out_dir=Path(args.out_dir),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
