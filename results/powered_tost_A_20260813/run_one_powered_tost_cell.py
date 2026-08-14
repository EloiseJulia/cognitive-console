from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np

REPO = Path.home() / "cc_l0" / "powered_tost_a_repo"
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from cognitive_console.experiments import adjudicate_c2b as adj
from scripts import run_c1_facade as c1
from scripts import run_c2b_adjudication as base
from scripts import run_powered_tost_a as r

EXPECTED = "0ce7377384b4ba6daa0ccf153d95f18aeaac333c"
OUT_DIR = Path.home() / "reports" / "cognitive-console" / "powered_tost_A_20260813"


def cell_by_id(cell_id: str) -> r.Cell:
    for cell in r.CELLS:
        if cell.cell_id == cell_id:
            return cell
    raise SystemExit(f"unknown cell {cell_id}")


def build_sealed_spec(cell: r.Cell, items_by_axis, frozen):
    sealed_direction = frozen.get("direction") or {}
    if not sealed_direction.get("path"):
        raise ValueError(f"missing sealed direction path for {cell.cell_id}")
    direction_path = Path(str(sealed_direction["path"]))
    if r._sha256_file(direction_path) != sealed_direction.get("sha256"):
        raise ValueError(f"sealed direction hash mismatch for {cell.cell_id}")
    return adj.AxisAdjSpec(
        axis=cell.axis,
        items=[dict(item) for item in items_by_axis[cell.axis]],
        strong_prompts=base.build_strong_prompts(cell.axis, r.N_STRONG),
        neutral_prompt=c1.load_neutral_prompts()[0],
        direction=np.load(direction_path),
        layer=cell.layer,
    )


def run_cell(cell_id: str, batch_size: int) -> int:
    out_dir = OUT_DIR.resolve()
    cell = cell_by_id(cell_id)
    if cell.cell_id == "A1":
        raise ValueError("A1 is sealed and must not be rerun by this resume helper")
    os.environ.setdefault("CC_TEST_ATTEMPT_ROOT", str(Path.home() / ".local" / "state" / "cognitive-console"))
    identity = r._git_identity(EXPECTED, True)
    dev_seal = out_dir / "dev" / "SEALED.json"
    if not dev_seal.exists():
        raise ValueError("TEST requires DEV SEALED.json")
    if (out_dir / "test" / "SEALED.json").exists():
        raise ValueError("global TEST SEALED exists; refusing incremental cell run")
    dev_payload = json.loads(dev_seal.read_text(encoding="utf-8"))
    if dev_payload.get("protocol_id") != r.PROTOCOL_ID:
        raise ValueError("DEV seal protocol mismatch")
    if dev_payload.get("code_identity", {}).get("code_commit") != identity["code_commit"]:
        raise ValueError("TEST code commit differs from DEV")
    items = r.load_selected_items("hf")
    sampling = r.sampling_manifest(items)
    if sampling != dev_payload["sampling"]:
        raise ValueError("TEST sampling identity differs from DEV")
    hardware = r._capture_hardware("nvidia-a800-80gb")
    registry_profile = r.resolve_test_attempt_registry(prepare=True)
    cell_out = r._cell_dir(out_dir / "test", cell)
    if (cell_out / "TEST_STARTED.json").exists():
        raise ValueError(f"TEST already started for {cell.cell_id}")
    if (cell_out / "sealed" / "powered_tost_A_result.json").exists():
        raise ValueError(f"TEST result already exists for {cell.cell_id}")
    frozen, dev_sha = r._load_dev_selection(out_dir, cell)
    if frozen.get("cell", {}).get("cell_id") != cell.cell_id:
        raise ValueError(f"DEV selection cell mismatch for {cell.cell_id}")
    if frozen.get("code_identity", {}).get("code_commit") != identity["code_commit"]:
        raise ValueError(f"code commit differs from sealed DEV for {cell.cell_id}")
    spec = build_sealed_spec(cell, items, frozen)
    dev_items, test_items = r._dev_test_items(spec.items)
    if [str(item["id"]) for item in dev_items] != frozen["sampling_axis"]["dev_item_ids"]:
        raise ValueError(f"DEV item identity drift for {cell.cell_id}")
    if [str(item["id"]) for item in test_items] != frozen["sampling_axis"]["test_item_ids"]:
        raise ValueError(f"TEST item identity drift for {cell.cell_id}")
    collector = base.TranscriptCollector(cell_out / "work", cell.model_id, cell.method, "hf")
    sampler = r._sampler_factory(cell, backend="hf", collector=collector, batch_size=batch_size)
    marker = r.claim_test_attempt(
        cell=cell,
        code_identity=identity,
        dev_selection_sha256=dev_sha,
        out_dir=out_dir,
        profile=registry_profile,
    )
    r._atomic_json(
        cell_out / "TEST_STARTED.json",
        {
            "protocol_id": r.PROTOCOL_ID,
            "experiment_id": f"{r.TEST_EXPERIMENT_ID}-{cell.cell_id}",
            "cell_id": cell.cell_id,
            "global_attempt_marker": str(marker),
            "registry_profile": registry_profile,
            "code_identity": identity,
        },
    )
    ckpt = base.TranscriptCheckpointStore(
        cell_out / "work" / "checkpoints",
        r._config_fingerprint(cell, spec, "test"),
        seed=r.SEED,
        fresh=True,
        collector=collector,
    )
    ctx = adj.RunContext(checkpoint=ckpt)
    try:
        result = adj.adjudicate_axis_test(
            sampler,
            spec,
            dev_items=dev_items,
            test_items=test_items,
            dev_selection=frozen["selection"],
            k=r.K_SAMPLES,
            bootstrap_b=r.BOOTSTRAP_B,
            ci_level=r.BONFERRONI_CI_LEVEL,
            delta=adj.DELTA,
            coherence_max_ratio=adj.COHERENCE_MAX_RATIO,
            seed=r.SEED,
            ctx=ctx,
        )
    finally:
        ckpt.close()
    tost_ci = adj.cluster_bootstrap_ci(
        result.per_item_diff,
        b=r.BOOTSTRAP_B,
        ci_level=r.TOST_CI_LEVEL,
        seed=r.SEED,
        cluster=True,
    )
    verdict = r.strict_verdict(result, tost_ci)
    report = adj.AdjudicationReport(
        axis_results=[result],
        axis_passes={cell.cell_id: bool(result.passed)},
        verdict=verdict,
        frozen_params=adj.frozen_params_dict(),
    )
    transcript_root = collector.write_all(cell_out / "work", report)
    payload = {
        "protocol_id": r.PROTOCOL_ID,
        "experiment_id": f"{r.TEST_EXPERIMENT_ID}-{cell.cell_id}",
        "phase": "TEST",
        "scientific_status": "PENDING_HOSTILE_RESULT_AUDIT",
        "valid_for_paper": False,
        "cell": asdict(cell),
        "code_identity": identity,
        "hardware": hardware,
        "sampling_axis": sampling["axes"][cell.axis],
        "dev_selection_sha256": dev_sha,
        "test_attempt_marker": str(marker),
        "direction": frozen.get("direction"),
        "result": result.to_row(),
        "tost": asdict(tost_ci),
        "strict_verdict": verdict,
        "achieved_mde": cell.planned_mde,
        "transcript_root": str(transcript_root),
        "config": {
            "k": r.K_SAMPLES,
            "bootstrap_b": r.BOOTSTRAP_B,
            "bonferroni_ci_level": r.BONFERRONI_CI_LEVEL,
            "tost_ci_level": r.TOST_CI_LEVEL,
            "sesoi": r.SESOI,
            "max_new_tokens": r.MAX_NEW_TOKENS,
            "temperature": r.TEMPERATURE,
            "seed": r.SEED,
            "alpha_grid": list(adj.ALPHA_GRID),
        },
    }
    result_path = cell_out / "sealed" / "powered_tost_A_result.json"
    r._atomic_json(result_path, payload)
    r._atomic_json(cell_out / "SEALED.json", {"result_sha256": r._sha256_file(result_path)})
    print(
        f"[powered-tost-A] TEST sealed {cell.cell_id}: verdict={verdict} "
        f"Δ={result.mean_diff:+.4f} CI=[{result.ci_lo:+.4f},{result.ci_hi:+.4f}] "
        f"TOST=[{tost_ci.ci_lo:+.4f},{tost_ci.ci_hi:+.4f}] coherence={result.coherence_ok}",
        flush=True,
    )
    return 0


def summarize_cell(cell: r.Cell):
    result_path = r._cell_dir(OUT_DIR / "test", cell) / "sealed" / "powered_tost_A_result.json"
    if not result_path.exists():
        raise ValueError(f"missing sealed result for {cell.cell_id}: {result_path}")
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    result = payload["result"]
    tost = payload["tost"]
    return {
        "strict_verdict": payload["strict_verdict"],
        "n_test": result["n_test"],
        "achieved_mde": payload["achieved_mde"],
        "dev_alpha": result["dev_selection"].get("frozen_alpha"),
        "mean_diff": result["mean_diff"],
        "ci_lo": result["ci_lo"],
        "ci_hi": result["ci_hi"],
        "tost_ci_lo": tost["ci_lo"],
        "tost_ci_hi": tost["ci_hi"],
        "coherence_ok": result["coherence_ok"],
        "result_path": str(result_path),
        "result_sha256": r._sha256_file(result_path),
    }


def finalize() -> int:
    identity = r._git_identity(EXPECTED, True)
    dev_payload = json.loads((OUT_DIR / "dev" / "SEALED.json").read_text(encoding="utf-8"))
    items = r.load_selected_items("hf")
    sampling = r.sampling_manifest(items)
    if sampling != dev_payload["sampling"]:
        raise ValueError("TEST sampling identity differs from DEV")
    cell_summaries = {cell.cell_id: summarize_cell(cell) for cell in r.CELLS}
    seal_payload = {
        "protocol_id": r.PROTOCOL_ID,
        "experiment_id": r.TEST_EXPERIMENT_ID,
        "phase": "TEST_SEALED",
        "code_identity": identity,
        "sampling": sampling,
        "cells": cell_summaries,
        "valid_for_paper": False,
    }
    r._atomic_json(OUT_DIR / "test" / "SEALED.json", seal_payload)
    print(f"[powered-tost-A] TEST SEALED {OUT_DIR / 'test' / 'SEALED.json'}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cell", choices=["A2", "A3", "A4"])
    ap.add_argument("--finalize", action="store_true")
    ap.add_argument("--batch-size", type=int, default=32)
    args = ap.parse_args()
    if args.finalize:
        return finalize()
    if not args.cell:
        raise SystemExit("--cell or --finalize required")
    return run_cell(args.cell, args.batch_size)


if __name__ == "__main__":
    raise SystemExit(main())
