"""Run the frozen robustness arm 2x2 matrix: {CAA, ITI} x {Qwen, Llama}.

This script orchestrates four independent C2b adjudication cells by reusing
``scripts.run_c2b_adjudication`` (no duplicated adjudication math), writes each
cell under its own output directory, and emits an arm-level summary verdict.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cognitive_console.experiments import adjudicate_c2b as adj
from cognitive_console.ops.disk_guard import check_disk_budget, default_guard_paths
from cognitive_console.lineage import utcnow
from scripts import run_c2b_adjudication as single

DEFAULT_QWEN_MODEL = "Qwen/Qwen2.5-7B-Instruct"
DEFAULT_LLAMA_MODEL = "meta-llama/Meta-Llama-3-8B-Instruct"

ARM_SCOPE_NARROWED_POSITIVE = "SCOPE_NARROWED_POSITIVE"
ARM_NON_TRANSFER_GENERALIZED = "NON_TRANSFER_GENERALIZED"
ARM_INCONCLUSIVE = "INCONCLUSIVE"


@dataclass(frozen=True)
class MatrixCell:
    method: str
    model_label: str
    model_id: str

    @property
    def key(self) -> str:
        return f"{self.method}__{self.model_label}"


def matrix_cells(qwen_model: str, llama_model: str) -> List[MatrixCell]:
    return [
        MatrixCell(method="caa", model_label="qwen2.5-7b", model_id=qwen_model),
        MatrixCell(method="caa", model_label="llama3-8b", model_id=llama_model),
        MatrixCell(method="iti", model_label="qwen2.5-7b", model_id=qwen_model),
        MatrixCell(method="iti", model_label="llama3-8b", model_id=llama_model),
    ]


def _planned_generations_per_axis(n_items_override: Optional[int], n_strong: int) -> Dict[str, int]:
    per_axis: Dict[str, int] = {}
    for axis in single.ADJ_AXES:
        n = int(n_items_override if n_items_override is not None else adj.N_ITEMS_BY_AXIS[axis])
        n_dev = int(round(adj.DEV_FRACTION * n))
        n_dev = max(1, min(n_dev, n - 1))
        n_test = n - n_dev
        dev = int(adj.K_SAMPLES) * n_dev * (int(n_strong) + 1 + len(adj.ALPHA_GRID))
        test = int(adj.K_SAMPLES) * n_test * 5
        per_axis[axis] = int(dev + test)
    return per_axis


def summarize_arm_verdict(cell_summaries: List[Dict]) -> Dict[str, object]:
    total = len(cell_summaries)
    min_zero_for_generalized = max(1, total - 1)
    zero_pass_cells = sum(1 for c in cell_summaries if int(c.get("axes_passed", 0)) == 0)
    any_pass = any(int(c.get("axes_passed", 0)) >= 1 for c in cell_summaries)
    if any_pass:
        verdict = ARM_SCOPE_NARROWED_POSITIVE
    elif zero_pass_cells >= min_zero_for_generalized:
        verdict = ARM_NON_TRANSFER_GENERALIZED
    else:
        verdict = ARM_INCONCLUSIVE
    return {
        "arm_verdict": verdict,
        "n_cells": total,
        "zero_pass_cells": zero_pass_cells,
        "min_zero_pass_cells_for_generalized": min_zero_for_generalized,
        "any_cell_has_pass": any_pass,
    }


def _cell_out_dir(root: Path, cell: MatrixCell) -> Path:
    return root / f"cell_{cell.key}"


def _cell_result_path(root: Path, cell: MatrixCell) -> Path:
    return _cell_out_dir(root, cell) / "c2b_adjudication_results.json"


def _build_single_cell_argv(args, cell: MatrixCell, out_dir: Path) -> List[str]:
    argv = [
        "--backend", args.backend,
        "--steering-method", cell.method,
        "--seed", str(args.seed),
        "--n-strong", str(args.n_strong),
        "--n-extraction", str(args.n_extraction),
        "--bootstrap-b", str(args.bootstrap_b),
        "--max-new-tokens", str(args.max_new_tokens),
        "--batch-size", str(args.batch_size),
        "--temperature", str(args.temperature),
        "--disk-budget-gb", str(args.disk_budget_gb),
        "--disk-ceiling-gb", str(args.disk_ceiling_gb),
        "--out-dir", str(out_dir),
    ]
    if args.backend == "hf":
        argv.extend(["--model", cell.model_id])
    if args.allow_underpowered:
        argv.append("--allow-underpowered")
    if args.use_fixture:
        argv.append("--use-fixture")
    if args.fresh:
        argv.append("--fresh")
    if args.save_transcripts:
        argv.append("--save-transcripts")
    if args.n_items is not None:
        argv.extend(["--n-items", str(args.n_items)])
    if args.hf_home:
        argv.extend(["--hf-home", str(args.hf_home)])
    if args.venv:
        argv.extend(["--venv", str(args.venv)])
    return argv


def _read_cell_result(path: Path, cell: MatrixCell) -> Dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    axis_passes = dict(data.get("axis_passes", {}))
    axes_passed = sum(1 for v in axis_passes.values() if bool(v))
    transcripts_dir = path.parent / "transcripts"
    return {
        "cell_key": cell.key,
        "method": cell.method,
        "model_label": cell.model_label,
        "model_id": cell.model_id,
        "out_dir": str(path.parent),
        "result_file": str(path),
        "verdict": data.get("verdict"),
        "axis_passes": axis_passes,
        "axes_passed": int(axes_passed),
        "transcripts_dir": str(transcripts_dir),
        "transcripts_present": transcripts_dir.exists(),
    }


def write_matrix_summary(out_dir: Path, payload: Dict[str, object]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_json = out_dir / "arm_matrix_summary.json"
    summary_md = out_dir / "arm_matrix_summary.md"
    summary_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines: List[str] = []
    lines.append("# Robustness Arm 2x2 Matrix Summary")
    lines.append("")
    lines.append(f"- generated_at: `{payload.get('generated_at')}`")
    lines.append(f"- arm_verdict: **{payload.get('arm_verdict')}**")
    lines.append(f"- rule: `{payload.get('arm_rule')}`")
    lines.append("")
    lines.append("| cell | method | model | per-axis pass | axes passed | verdict |")
    lines.append("|---|---|---|---|---:|---|")
    for cell in payload.get("cells", []):
        axis_passes = cell.get("axis_passes", {})
        axis_str = ", ".join(f"{k}={'Y' if v else 'n'}" for k, v in sorted(axis_passes.items()))
        lines.append(
            f"| {cell.get('cell_key')} | {cell.get('method')} | {cell.get('model_label')} | "
            f"{axis_str} | {cell.get('axes_passed')} | {cell.get('verdict')} |"
        )
    summary_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary_json


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Run frozen robustness arm matrix 2x2")
    ap.add_argument("--backend", choices=["synthetic", "hf"], default="hf")
    ap.add_argument("--qwen-model", default=DEFAULT_QWEN_MODEL)
    ap.add_argument("--llama-model", default=DEFAULT_LLAMA_MODEL)
    ap.add_argument("--seed", type=int, default=20260723)
    ap.add_argument("--n-items", type=int, default=None)
    ap.add_argument("--n-strong", type=int, default=single.DEFAULT_N_STRONG)
    ap.add_argument("--n-extraction", type=int, default=28)
    ap.add_argument("--bootstrap-b", type=int, default=adj.BOOTSTRAP_B)
    ap.add_argument("--allow-underpowered", action="store_true")
    ap.add_argument("--max-new-tokens", type=int, default=64)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--disk-budget-gb", type=float, default=60.0)
    ap.add_argument("--disk-ceiling-gb", type=float, default=70.0)
    ap.add_argument("--hf-home", default=None)
    ap.add_argument("--venv", default=None)
    ap.add_argument("--use-fixture", action="store_true")
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--save-transcripts", action=argparse.BooleanOptionalAction, default=True)
    ap.add_argument("--out-dir", default=None)
    return ap


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    out_dir = Path(args.out_dir) if args.out_dir else (
        _REPO / "results" / f"arm_matrix_{args.backend}_{date.today().isoformat()}"
    )
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    cells = matrix_cells(args.qwen_model, args.llama_model)
    per_axis_plan = _planned_generations_per_axis(args.n_items, args.n_strong)
    per_cell_total = sum(per_axis_plan.values())
    total_plan = per_cell_total * len(cells)

    print("[arm-matrix] planned cells:", flush=True)
    for cell in cells:
        print(
            f"  - {cell.key}: method={cell.method} model={cell.model_id} "
            f"out={_cell_out_dir(out_dir, cell)}",
            flush=True,
        )
    print(
        f"[arm-matrix] budget plan per-cell={per_cell_total} generations; total={total_plan}; "
        f"per-axis={per_axis_plan}",
        flush=True,
    )

    if args.dry_run:
        print("[arm-matrix] dry-run enabled: no cell executed.", flush=True)
        return 0

    cell_summaries: List[Dict[str, object]] = []
    guard_paths = default_guard_paths(args.hf_home, args.venv)
    for cell in cells:
        result_path = _cell_result_path(out_dir, cell)
        if result_path.exists() and not args.fresh:
            print(f"[arm-matrix] skip completed {cell.key}: {result_path}", flush=True)
            cell_summaries.append(_read_cell_result(result_path, cell))
            continue

        usage0 = check_disk_budget(guard_paths, args.disk_budget_gb, args.disk_ceiling_gb, raise_on_over=True)
        print(f"[arm-matrix] disk pre-cell {cell.key}: {usage0.message}", flush=True)

        cell_dir = _cell_out_dir(out_dir, cell)
        cell_dir.mkdir(parents=True, exist_ok=True)
        rc = single.main(_build_single_cell_argv(args, cell, cell_dir))
        if rc != 0:
            print(f"[arm-matrix] cell failed {cell.key}: rc={rc}", flush=True)
            return int(rc)
        if not result_path.exists():
            raise FileNotFoundError(f"cell completed but missing result file: {result_path}")
        cell_summaries.append(_read_cell_result(result_path, cell))

        usage1 = check_disk_budget(guard_paths, args.disk_budget_gb, args.disk_ceiling_gb, raise_on_over=True)
        print(f"[arm-matrix] disk post-cell {cell.key}: {usage1.message}", flush=True)

    arm_eval = summarize_arm_verdict(cell_summaries)
    payload = {
        "generated_at": utcnow(),
        "backend": args.backend,
        "seed": int(args.seed),
        "arm_rule": "any-pass => SCOPE_NARROWED_POSITIVE; else >=(n_cells-1) zero-pass => NON_TRANSFER_GENERALIZED; else INCONCLUSIVE",
        "cells": cell_summaries,
        **arm_eval,
    }
    write_matrix_summary(out_dir, payload)
    print(f"[arm-matrix] arm verdict: {payload['arm_verdict']} ({out_dir})", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
