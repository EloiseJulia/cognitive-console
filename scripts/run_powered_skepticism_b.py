"""Run E-0016 powered skepticism-only C2b re-measurement.

FROZEN prereg: docs/specs/powered-tost-B-skepticism-prereg.md.

This runner is intentionally additive: it reuses the frozen C2b code path,
frozen DEV-selected prompt/alpha from E-0006, excludes the frozen DEV items,
and enlarges TEST N for skepticism only. It never re-selects alpha/prompt on the
powered items.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import os
import platform
import sys
import time
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import numpy as np

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cognitive_console.eval import c2b_tasks
from cognitive_console.experiments import adjudicate_c2b as adj
from cognitive_console.experiments.adjudicate_c2b import AxisAdjResult, RunContext
from cognitive_console.lineage import git_commit, utcnow

from scripts import posthoc_equivalence as eq
from scripts import run_c2b_adjudication as c2run

AXIS = "skepticism"
EXPERIMENT_ID = "e0016-powered-skepticism-b"
PREREG = "docs/specs/powered-tost-B-skepticism-prereg.md (FROZEN 2026-08-18)"
FROZEN_SELECTION_SEED = 20260723
POWERED_SEED = 20260818
N_FULL = 100_000

CELLS: Dict[str, Dict[str, Any]] = {
    "caa_qwen25_7b": {
        "method": "caa",
        "model": "/root/autodl-tmp/models/Qwen2.5-7B-Instruct",
        "model_label": "Qwen2.5-7B",
        "source_artifact": "results/arm_full/cell_caa__qwen2.5-7b/c2b_adjudication_results.json",
        "target_n": 400,
        "expected_layer": 20,
        "frozen_alpha": 6.0,
        "expected_sigma": 1.0,
        "frozen_prompt_id": "skep-strong-06",
        "old_mde": 0.188,
    },
    "caa_llama3_8b": {
        "method": "caa",
        "model": "/root/autodl-tmp/models/Meta-Llama-3-8B-Instruct",
        "model_label": "Llama-3-8B",
        "source_artifact": "results/arm_full/cell_caa__llama3-8b/c2b_adjudication_results.json",
        "target_n": 800,
        "expected_layer": 14,
        "frozen_alpha": 2.0,
        "expected_sigma": 1.0,
        "frozen_prompt_id": "skep-strong-11",
        "old_mde": 0.268,
    },
    "iti_qwen25_7b": {
        "method": "iti",
        "model": "/root/autodl-tmp/models/Qwen2.5-7B-Instruct",
        "model_label": "Qwen2.5-7B",
        "source_artifact": "results/arm_full/cell_iti__qwen2.5-7b/c2b_adjudication_results.json",
        "target_n": 600,
        "expected_layer": 19,
        "frozen_alpha": 2.0,
        "expected_sigma": 8.781919619478579,
        "frozen_prompt_id": "skep-strong-06",
        "old_mde": 0.225,
    },
    "iti_llama3_8b": {
        "method": "iti",
        "model": "/root/autodl-tmp/models/Meta-Llama-3-8B-Instruct",
        "model_label": "Llama-3-8B",
        "source_artifact": "results/arm_full/cell_iti__llama3-8b/c2b_adjudication_results.json",
        "target_n": 900,
        "expected_layer": 14,
        "frozen_alpha": 2.0,
        "expected_sigma": 1.3239446225015263,
        "frozen_prompt_id": "skep-strong-11",
        "old_mde": 0.279,
    },
}


def sha256_bytes(blob: bytes) -> str:
    return "sha256:" + hashlib.sha256(blob).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def sha256_json(obj: Any) -> str:
    return sha256_bytes(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8"))


def load_source_selection(cell: Dict[str, Any]) -> Dict[str, Any]:
    path = _REPO / cell["source_artifact"]
    data = json.loads(path.read_text(encoding="utf-8"))
    for axis_rec in data["axes"]:
        if axis_rec["axis"] == AXIS:
            return axis_rec
    raise RuntimeError(f"source artifact lacks {AXIS}: {path}")


def frozen_dev_ids() -> List[str]:
    task = c2b_tasks.load_c2b_task(AXIS, use_fixture=False)
    first60 = [str(it["id"]) for it in list(task.items)[: adj.N_ITEMS_BY_AXIS[AXIS]]]
    split = adj.split_dev_test(first60, dev_fraction=adj.DEV_FRACTION, seed=FROZEN_SELECTION_SEED)
    return list(split.dev_ids)


def select_powered_items(items: List[Dict[str, Any]], target_n: int) -> Dict[str, Any]:
    dev_ids = set(frozen_dev_ids())
    eligible = [it for it in items if str(it["id"]) not in dev_ids]
    eligible_ids = [str(it["id"]) for it in eligible]
    realized_n = min(int(target_n), len(eligible))
    if realized_n < int(target_n):
        selected = eligible
        cap_reason = "target_n_exceeds_eligible_unique_items_after_frozen_DEV_exclusion"
    else:
        rng = np.random.default_rng(POWERED_SEED)
        idx = sorted(rng.permutation(len(eligible))[:realized_n].tolist())
        selected = [eligible[i] for i in idx]
        cap_reason = None
    ids = [str(it["id"]) for it in selected]
    if set(ids) & dev_ids:
        raise RuntimeError("powered TEST item list overlaps frozen DEV ids")
    if len(ids) != len(set(ids)):
        raise RuntimeError("powered TEST item list contains duplicates")
    return {
        "items": selected,
        "frozen_dev_ids": sorted(dev_ids),
        "eligible_universe_n": len(eligible),
        "target_n": int(target_n),
        "realized_n": int(realized_n),
        "cap_applied": bool(realized_n < int(target_n)),
        "cap_reason": cap_reason,
        "item_ids": ids,
        "item_ids_hash": sha256_json(ids),
        "eligible_ids_hash": sha256_json(eligible_ids),
    }


def prompt_by_id(prompt_id: str) -> str:
    prompts = dict(c2run.build_strong_prompts(AXIS, c2run.DEFAULT_N_STRONG))
    if prompt_id not in prompts:
        raise RuntimeError(f"frozen prompt id not found: {prompt_id}")
    return str(prompts[prompt_id])


def make_spec(cell: Dict[str, Any], out_dir: Path) -> tuple[adj.AxisAdjSpec, Dict[str, Any]]:
    specs, hf_meta = c2run.build_specs_hf(
        [AXIS],
        cell["model"],
        use_fixture=False,
        n_items=N_FULL,
        n_strong=c2run.DEFAULT_N_STRONG,
        n_extraction=28,
        seed=FROZEN_SELECTION_SEED,
        out_dir=out_dir,
        steering_method=cell["method"],
    )
    spec = specs[0]
    source_axis = load_source_selection(cell)
    source_alpha = float(source_axis["dev_selection"]["frozen_alpha"])
    source_prompt_id = str(source_axis["dev_selection"]["best_prompt_id"])
    source_prompt_text = str(source_axis["dev_selection"]["best_prompt_text"])
    source_layer = int(source_axis["layer"])
    if abs(source_alpha - float(cell["frozen_alpha"])) > 1e-9:
        raise RuntimeError(f"source alpha mismatch for {cell}: {source_alpha}")
    if source_prompt_id != cell["frozen_prompt_id"]:
        raise RuntimeError(f"source prompt mismatch: {source_prompt_id} != {cell['frozen_prompt_id']}")
    if int(spec.layer) != int(cell["expected_layer"]) or source_layer != int(cell["expected_layer"]):
        raise RuntimeError(
            f"layer mismatch: rebuilt={spec.layer}, source={source_layer}, expected={cell['expected_layer']}"
        )
    rebuilt_sigma = float(hf_meta.get("alpha_scale_by_axis", {}).get(AXIS, 1.0))
    expected_sigma = float(cell["expected_sigma"])
    if not math.isclose(rebuilt_sigma, expected_sigma, rel_tol=5e-4, abs_tol=5e-4):
        raise RuntimeError(f"sigma mismatch: rebuilt={rebuilt_sigma}, expected={expected_sigma}")
    # The protocol freezes the E-0006 alpha scale. Tiny cross-environment
    # numerical drift in the reconstructed ITI sigma is tolerated only for
    # provenance verification; generation uses the frozen source sigma.
    sigma = expected_sigma
    powered = select_powered_items(list(spec.items), int(cell["target_n"]))
    frozen_prompt_text = prompt_by_id(cell["frozen_prompt_id"])
    if frozen_prompt_text != source_prompt_text:
        raise RuntimeError("frozen prompt text in source artifact differs from prompt library")
    spec = adj.AxisAdjSpec(
        axis=AXIS,
        items=powered["items"],
        strong_prompts=[(cell["frozen_prompt_id"], frozen_prompt_text)],
        neutral_prompt=spec.neutral_prompt,
        direction=spec.direction,
        layer=spec.layer,
    )
    provenance = {
        **hf_meta,
        "frozen_source_artifact": cell["source_artifact"],
        "frozen_source_artifact_hash": sha256_file(_REPO / cell["source_artifact"]),
        "frozen_source_dev_selection": source_axis["dev_selection"],
        "frozen_source_ci_9833": {
            "mean_diff": source_axis["mean_diff"],
            "ci_lo": source_axis["ci_lo"],
            "ci_hi": source_axis["ci_hi"],
            "n_test": source_axis["n_test"],
        },
        "frozen_alpha_nominal": float(cell["frozen_alpha"]),
        "alpha_scale_sigma": sigma,
        "effective_alpha": float(cell["frozen_alpha"]) * sigma,
        "target_old_mde": float(cell["old_mde"]),
        "powered_item_selection": {k: v for k, v in powered.items() if k != "items"},
    }
    return spec, provenance


def verdict(point: float, ci_lo_9833: float, ci_hi_9833: float,
            ci_lo_90: float, ci_hi_90: float, coherence_ok: bool) -> str:
    if adj.axis_pass(point, ci_lo_9833, ci_hi_9833, coherence_ok, delta=adj.DELTA):
        return "SUPERIORITY_PASS"
    if ci_hi_90 < 0.0:
        return "COMPARATOR_NEGATIVE"
    if ci_lo_90 > -adj.DELTA and ci_hi_90 < adj.DELTA:
        return "BOUNDED_EQUIVALENT"
    return "UNDERPOWERED"


def token_len(tokenizer: Any, text: str) -> int:
    try:
        return int(len(tokenizer.encode(str(text), add_special_tokens=False)))
    except Exception:
        return int(len(str(text).split()))


def transcript_diagnostics(records: Iterable[Dict[str, Any]], tokenizer: Any) -> Dict[str, Any]:
    by_phase: Dict[str, List[Dict[str, Any]]] = {}
    for rec in records:
        by_phase.setdefault(str(rec.get("phase")), []).append(rec)
    out: Dict[str, Any] = {}
    for phase, rows in sorted(by_phase.items()):
        n = len(rows)
        parse_failed = sum(1 for r in rows if (r.get("parse") or {}).get("axis_parse_failed"))
        toks = [token_len(tokenizer, str(r.get("generation_text", ""))) for r in rows]
        parsed_toks = [
            tok for tok, r in zip(toks, rows)
            if not (r.get("parse") or {}).get("axis_parse_failed")
        ]
        out[phase] = {
            "n_generations": int(n),
            "parseable": int(n - parse_failed),
            "parse_failed": int(parse_failed),
            "parse_rate": round((n - parse_failed) / n, 6) if n else None,
            "generated_tokens_total": int(sum(toks)),
            "generated_tokens_mean_all": round(float(np.mean(toks)), 6) if toks else None,
            "generated_tokens_mean_parseable": round(float(np.mean(parsed_toks)), 6) if parsed_toks else None,
            "maybe_truncated": int(sum(1 for r in rows if (r.get("parse") or {}).get("maybe_truncated"))),
        }
    return out


def run_cell(cell_id: str, args: argparse.Namespace) -> Path:
    if cell_id not in CELLS:
        raise SystemExit(f"unknown cell {cell_id!r}; choices={sorted(CELLS)}")
    cell = dict(CELLS[cell_id])
    if "qwen" in cell_id:
        cell["model"] = os.environ.get("POWERED_B_QWEN_MODEL", cell["model"])
    if "llama" in cell_id:
        cell["model"] = os.environ.get("POWERED_B_LLAMA_MODEL", cell["model"])
    out_dir = Path(args.out_dir) / f"cell_{cell_id}"
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    started_at = utcnow()

    spec, provenance = make_spec(cell, out_dir)
    collector = c2run.TranscriptCollector(out_dir, cell["model"], cell["method"], "hf")
    sampler_factory = c2run.hf_sampler_factory(
        cell["model"],
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
        seed=POWERED_SEED,
        batch_size=args.batch_size,
        transcript_collector=collector,
        alpha_scale_by_axis={AXIS: provenance["alpha_scale_sigma"]},
    )
    sampler = sampler_factory(AXIS)

    fingerprint_payload = {
        "experiment_id": EXPERIMENT_ID,
        "cell_id": cell_id,
        "prereg": PREREG,
        "seed": POWERED_SEED,
        "frozen_selection_seed": FROZEN_SELECTION_SEED,
        "target_n": cell["target_n"],
        "realized_item_ids_hash": provenance["powered_item_selection"]["item_ids_hash"],
        "model": cell["model"],
        "method": cell["method"],
        "layer": spec.layer,
        "frozen_alpha": cell["frozen_alpha"],
        "alpha_scale_sigma": provenance["alpha_scale_sigma"],
        "max_new_tokens": args.max_new_tokens,
        "temperature": args.temperature,
        "batch_size": args.batch_size,
        "k": adj.K_SAMPLES,
        "bootstrap_b": args.bootstrap_b,
    }
    fingerprint = hashlib.sha256(
        json.dumps(fingerprint_payload, sort_keys=True).encode("utf-8")
    ).hexdigest()[:16]
    ckpt_dir = out_dir / "checkpoints"
    checkpoint = c2run.TranscriptCheckpointStore(
        ckpt_dir, fingerprint, seed=POWERED_SEED, fresh=args.fresh, collector=collector
    )
    total_plan = len(spec.items) * adj.K_SAMPLES * 3
    progress = adj.ProgressTracker(total_planned=total_plan)
    ctx = RunContext(checkpoint=checkpoint, progress=progress)
    print(
        f"[powered-B] cell={cell_id} model={cell['model_label']} method={cell['method']} "
        f"realized_N={len(spec.items)} target_N={cell['target_n']} generations={total_plan} "
        f"fingerprint={fingerprint}",
        flush=True,
    )
    watchdog = c2run.InactivityWatchdog(progress, args.stall_timeout).start()
    try:
        prompt_id, prompt_text = spec.strong_prompts[0]
        alpha = float(cell["frozen_alpha"])
        prompt_out, _, prompt_mat = adj._channel_item_outcomes(
            sampler, AXIS, spec.items, prompt_text, 0.0, adj.K_SAMPLES,
            spec.direction, spec.layer, ctx=ctx, phase=adj.PHASE_TEST_PROMPT,
            cell_key=f"prompt={prompt_id}|alpha=0",
        )
        steer_out, steer_deg, steer_mat = adj._channel_item_outcomes(
            sampler, AXIS, spec.items, spec.neutral_prompt, alpha, adj.K_SAMPLES,
            spec.direction, spec.layer, ctx=ctx, phase=adj.PHASE_TEST_STEER,
            cell_key=f"alpha={alpha}",
        )
        _, base_deg, _ = adj._channel_item_outcomes(
            sampler, AXIS, spec.items, spec.neutral_prompt, 0.0, adj.K_SAMPLES,
            spec.direction, spec.layer, ctx=ctx, phase=adj.PHASE_TEST_BASELINE,
            cell_key="alpha=0",
        )
    finally:
        watchdog.stop()
        checkpoint.close()

    per_item_diff = steer_out - prompt_out
    ci9833 = adj.cluster_bootstrap_ci(
        per_item_diff, b=args.bootstrap_b, ci_level=adj.BONFERRONI_CI_LEVEL,
        seed=POWERED_SEED, cluster=True,
    )
    ci90 = adj.cluster_bootstrap_ci(
        per_item_diff, b=args.bootstrap_b, ci_level=eq.TOST_CI_LEVEL,
        seed=POWERED_SEED, cluster=True,
    )
    test_baseline_deg = float(base_deg.mean())
    test_steer_deg = float(steer_deg.mean())
    coherence_ok = bool(
        test_steer_deg <= adj.COHERENCE_MAX_RATIO * test_baseline_deg + adj.COHERENCE_EPS_FLOOR + 1e-12
    )
    passed = adj.axis_pass(ci9833.point, ci9833.ci_lo, ci9833.ci_hi, coherence_ok, delta=adj.DELTA)
    cell_verdict = verdict(ci9833.point, ci9833.ci_lo, ci9833.ci_hi, ci90.ci_lo, ci90.ci_hi, coherence_ok)
    mde = eq.compute_mde(per_item_diff, sesoi=adj.DELTA)

    dev_selection = {
        "best_prompt_id": prompt_id,
        "best_prompt_text": prompt_text,
        "dev_prompt_outcome": provenance["frozen_source_dev_selection"].get("dev_prompt_outcome"),
        "frozen_alpha": alpha,
        "dev_steer_outcome": provenance["frozen_source_dev_selection"].get("dev_steer_outcome"),
        "baseline_degeneracy": provenance["frozen_source_dev_selection"].get("baseline_degeneracy"),
        "alpha_grid": provenance["frozen_source_dev_selection"].get("alpha_grid"),
        "any_alpha_passes_gate": provenance["frozen_source_dev_selection"].get("any_alpha_passes_gate"),
        "selection_note": "reused from frozen E-0006 source artifact; not re-selected on powered TEST",
    }
    axis_result = AxisAdjResult(
        axis=AXIS, layer=int(spec.layer), n_dev=0, n_test=len(spec.items), k=adj.K_SAMPLES,
        dev_selection=dev_selection,
        per_item_prompt=[float(x) for x in prompt_out],
        per_item_steer=[float(x) for x in steer_out],
        per_item_diff=[float(x) for x in per_item_diff],
        mean_diff=float(ci9833.point), ci_lo=float(ci9833.ci_lo), ci_hi=float(ci9833.ci_hi),
        ci_level=adj.BONFERRONI_CI_LEVEL, bootstrap_b=int(args.bootstrap_b),
        coherence_ok=coherence_ok, test_steer_degeneracy=test_steer_deg,
        test_baseline_degeneracy=test_baseline_deg, delta=adj.DELTA,
        passed=bool(passed),
        conflict={"note": "not run; powered skepticism-B prereg excludes conflict cell"},
        descriptive={},
    )
    report = adj.AdjudicationReport(
        axis_results=[axis_result],
        axis_passes={AXIS: bool(passed)},
        verdict=cell_verdict,
        frozen_params={**adj.frozen_params_dict(), "powered_prereg": PREREG, "axis": AXIS},
    )
    transcript_root = collector.write_all(out_dir, report)
    tokenizer = getattr(getattr(sampler, "gen", None), "_tokenizer", None)
    diagnostics = transcript_diagnostics(collector._all_records, tokenizer)
    wall = round(time.time() - t0, 2)
    payload = report.to_dict()
    payload.update({
        "experiment_id": EXPERIMENT_ID,
        "cell_id": cell_id,
        "prereg": PREREG,
        "status": "done",
        "code_commit": git_commit(str(_REPO)),
        "dirty_tree": None,
        "model": cell["model"],
        "model_label": cell["model_label"],
        "steering_method": cell["method"],
        "hardware": f"{c2run.p0._pick_device()}-{c2run.p0._pick_dtype()}",
        "platform": platform.platform(),
        "started_at": started_at,
        "generated_at": utcnow(),
        "wall_clock_seconds": wall,
        "seed": POWERED_SEED,
        "frozen_selection_seed": FROZEN_SELECTION_SEED,
        "config_fingerprint": fingerprint,
        "config_fingerprint_payload": fingerprint_payload,
        "source_provenance": provenance,
        "ci_90_tost": {"point": ci90.point, "ci_lo": ci90.ci_lo, "ci_hi": ci90.ci_hi},
        "cell_verdict": cell_verdict,
        "realized_mde": mde,
        "reached_mde_le_0_06": bool((mde.get("mde_superiority_80pct_power") or 999.0) <= 0.06),
        "diagnostics": diagnostics,
        "generation_accounting": {
            "phases": ["test_prompt", "test_steer", "test_baseline"],
            "total_generations": int(total_plan),
            "k_samples": adj.K_SAMPLES,
            "max_new_tokens": args.max_new_tokens,
            "temperature": args.temperature,
            "batch_size": args.batch_size,
        },
        "artifacts": {
            "json": "powered_skepticism_b_results.json",
            "transcripts": str(transcript_root.relative_to(out_dir)).replace("\\", "/"),
        },
    })
    json_path = out_dir / "powered_skepticism_b_results.json"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    summary_path = out_dir / "powered_skepticism_b_summary.md"
    summary_path.write_text(render_cell_summary(payload), encoding="utf-8")
    print(
        f"[powered-B] DONE {cell_id}: verdict={cell_verdict} mean={ci9833.point:+.4f} "
        f"CI98.33=[{ci9833.ci_lo:+.4f},{ci9833.ci_hi:+.4f}] "
        f"CI90=[{ci90.ci_lo:+.4f},{ci90.ci_hi:+.4f}] "
        f"MDE={mde.get('mde_superiority_80pct_power')} wall={wall}s",
        flush=True,
    )
    # Encourage model memory release for all-cells mode.
    del sampler
    gc.collect()
    return json_path


def render_cell_summary(payload: Dict[str, Any]) -> str:
    axis = payload["axes"][0]
    ci90 = payload["ci_90_tost"]
    diag = payload["diagnostics"]
    sel = payload["source_provenance"]["powered_item_selection"]
    lines = [
        f"# Powered skepticism-B cell — {payload['cell_id']}",
        "",
        f"- verdict: **{payload['cell_verdict']}**",
        f"- model/method: `{payload['model_label']}` / `{payload['steering_method']}`",
        f"- realized TEST N: **{axis['n_test']}** (target {sel['target_n']}; cap_applied={sel['cap_applied']})",
        f"- mean(d): {axis['mean_diff']:+.6f}",
        f"- 98.33% superiority CI: [{axis['ci_lo']:+.6f}, {axis['ci_hi']:+.6f}]",
        f"- 90% TOST CI: [{ci90['ci_lo']:+.6f}, {ci90['ci_hi']:+.6f}]",
        f"- realized MDE: {payload['realized_mde'].get('mde_superiority_80pct_power')} "
        f"(≤0.06: {payload['reached_mde_le_0_06']})",
        f"- coherence_ok: {axis['coherence_ok']} "
        f"(steer_deg={axis['test_steer_degeneracy']:.6f}, base_deg={axis['test_baseline_degeneracy']:.6f})",
        "",
        "## Format / token diagnostics",
        "",
        "| phase | generations | parse rate | parse failed | tokens total | mean tokens/parseable | maybe truncated |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for phase in [adj.PHASE_TEST_PROMPT, adj.PHASE_TEST_STEER, adj.PHASE_TEST_BASELINE]:
        row = diag.get(phase, {})
        lines.append(
            f"| {phase} | {row.get('n_generations')} | {row.get('parse_rate')} | "
            f"{row.get('parse_failed')} | {row.get('generated_tokens_total')} | "
            f"{row.get('generated_tokens_mean_parseable')} | {row.get('maybe_truncated')} |"
        )
    lines.extend([
        "",
        "All numbers are computed from `powered_skepticism_b_results.json`; no hand-filled metrics.",
        "",
    ])
    return "\n".join(lines)


def aggregate(out_dir: Path) -> Path:
    rows = []
    for cell_id in CELLS:
        p = out_dir / f"cell_{cell_id}" / "powered_skepticism_b_results.json"
        if not p.exists():
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        axis = data["axes"][0]
        rows.append({
            "cell_id": cell_id,
            "model": data["model_label"],
            "method": data["steering_method"],
            "target_n": data["source_provenance"]["powered_item_selection"]["target_n"],
            "realized_n": axis["n_test"],
            "cap_applied": data["source_provenance"]["powered_item_selection"]["cap_applied"],
            "mean_diff": axis["mean_diff"],
            "ci_9833": [axis["ci_lo"], axis["ci_hi"]],
            "ci_90": [data["ci_90_tost"]["ci_lo"], data["ci_90_tost"]["ci_hi"]],
            "realized_mde": data["realized_mde"]["mde_superiority_80pct_power"],
            "reached_mde_le_0_06": data["reached_mde_le_0_06"],
            "coherence_ok": axis["coherence_ok"],
            "verdict": data["cell_verdict"],
            "parse_rates": {
                phase: data["diagnostics"].get(phase, {}).get("parse_rate")
                for phase in [adj.PHASE_TEST_PROMPT, adj.PHASE_TEST_STEER, adj.PHASE_TEST_BASELINE]
            },
            "item_ids_hash": data["source_provenance"]["powered_item_selection"]["item_ids_hash"],
            "json": str(p.relative_to(_REPO)).replace("\\", "/"),
        })
    payload = {
        "experiment_id": EXPERIMENT_ID,
        "prereg": PREREG,
        "generated_at": utcnow(),
        "code_commit": git_commit(str(_REPO)),
        "seed": POWERED_SEED,
        "cells": rows,
        "result_hash_inputs": [r["json"] for r in rows],
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / "powered_skepticism_b_aggregate.json"
    out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        "# E-0016 Powered skepticism-B aggregate",
        "",
        f"- prereg: `{PREREG}`",
        f"- code_commit: `{payload['code_commit']}`",
        f"- seed: `{POWERED_SEED}`",
        "",
        "| cell | N target→realized | mean(d) | 98.33% CI | 90% TOST CI | MDE | ≤0.06? | coherence | parse prompt/steer | verdict |",
        "|---|---:|---:|---|---|---:|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['method']} × {r['model']} | {r['target_n']}→{r['realized_n']}"
            f"{' capped' if r['cap_applied'] else ''} | {r['mean_diff']:+.4f} | "
            f"[{r['ci_9833'][0]:+.4f}, {r['ci_9833'][1]:+.4f}] | "
            f"[{r['ci_90'][0]:+.4f}, {r['ci_90'][1]:+.4f}] | "
            f"{r['realized_mde']:.4f} | {r['reached_mde_le_0_06']} | "
            f"{r['coherence_ok']} | {r['parse_rates'].get(adj.PHASE_TEST_PROMPT)}/"
            f"{r['parse_rates'].get(adj.PHASE_TEST_STEER)} | **{r['verdict']}** |"
        )
    lines.append("")
    lines.append("Outcome-neutral: these additive results do not overwrite E-0005/E-0006/E-0011.")
    (out_dir / "powered_skepticism_b_aggregate.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_json


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="E-0016 powered skepticism-B runner")
    ap.add_argument("--cell", choices=sorted(CELLS), default=None, help="run one cell")
    ap.add_argument("--all-cells", action="store_true", help="run all four cells sequentially")
    ap.add_argument("--aggregate-only", action="store_true", help="aggregate completed cell JSON files")
    ap.add_argument("--out-dir", default=str(_REPO / "results" / "E-0016-powered-skepticism-b"))
    ap.add_argument("--max-new-tokens", type=int, default=64)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--bootstrap-b", type=int, default=10_000)
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--stall-timeout", type=float, default=600.0)
    return ap


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    out_dir = Path(args.out_dir).resolve()
    if args.bootstrap_b < 10_000:
        raise SystemExit("FROZEN protocol requires --bootstrap-b >= 10000")
    if args.aggregate_only:
        print(f"[powered-B] aggregate: {aggregate(out_dir)}", flush=True)
        return 0
    if args.all_cells:
        for cell_id in CELLS:
            run_cell(cell_id, args)
            try:
                import torch  # noqa: PLC0415
                torch.cuda.empty_cache()
            except Exception:
                pass
        print(f"[powered-B] aggregate: {aggregate(out_dir)}", flush=True)
        return 0
    if not args.cell:
        raise SystemExit("pass --cell CELL, --all-cells, or --aggregate-only")
    run_cell(args.cell, args)
    aggregate(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
