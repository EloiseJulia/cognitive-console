"""OOD activation capture for frozen robustness-arm H-M mechanism check.

Pure observational diagnostic: reads frozen 2x2 arm results, captures baseline vs
steered residual activations at each cell's frozen uncertainty layer/alpha, and
tests rho(distance, -delta_outcome) with frozen OOD guardrails.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cognitive_console.analysis import ood
from cognitive_console.experiments import adjudicate_c2b as adj
from cognitive_console.eval import c2b_tasks
from cognitive_console.lineage import git_commit, utcnow
from cognitive_console.steering.extract import extract_caa
from cognitive_console.steering.generate import SteerConfig, SteeredHFBackend
from cognitive_console.steering.iti import extract_iti, sigma_scaled_alpha
from scripts import run_c1_facade as c1
from scripts import run_gpu_phase0 as p0

from scripts.run_arm_matrix import FROZEN_CELL_KEYS

AXIS = "uncertainty_awareness"
DEFAULT_QWEN_MODEL = "Qwen/Qwen2.5-7B-Instruct"
DEFAULT_LLAMA_MODEL = "meta-llama/Meta-Llama-3-8B-Instruct"


@dataclass(frozen=True)
class CellFrozenSpec:
    cell_key: str
    steering_method: str
    model_label: str
    frozen_result_model: str
    runtime_model: str
    layer: int
    frozen_alpha: float
    effective_alpha: float
    delta_outcome: np.ndarray
    item_ids: List[str]
    item_prompts: List[str]
    source_result: Path


class _HFBackendActivationAdapter:
    """ActivationProvider adapter over SteeredHFBackend (unsteered forward)."""

    def __init__(self, backend: SteeredHFBackend):
        self._backend = backend

    def available_layers(self) -> List[int]:
        return self._backend.available_layers()

    def get_activations(self, texts: Sequence[str], layer: int) -> np.ndarray:
        return self._backend.capture_residual_activations(texts, int(layer), steer=None)


def _rel(path: Path) -> str:
    p = Path(path).resolve()
    try:
        return str(p.relative_to(_REPO)).replace("\\", "/")
    except ValueError:
        return str(p).replace("\\", "/")


def _json_load(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_array(x: np.ndarray) -> str:
    arr = np.ascontiguousarray(np.asarray(x, dtype=np.float64))
    return "sha256:" + hashlib.sha256(arr.tobytes()).hexdigest()


def _parse_cell_key(cell_dir_name: str) -> tuple[str, str]:
    if not cell_dir_name.startswith("cell_"):
        raise ValueError(f"unexpected cell directory name: {cell_dir_name}")
    cell_key = cell_dir_name[len("cell_") :]
    if "__" not in cell_key:
        raise ValueError(f"bad frozen cell key format: {cell_key}")
    method, model_label = cell_key.split("__", 1)
    return method, model_label


def _runtime_model_for_label(model_label: str, qwen_model: str, llama_model: str) -> str:
    if model_label == "qwen2.5-7b":
        return str(qwen_model)
    if model_label == "llama3-8b":
        return str(llama_model)
    raise ValueError(f"unknown frozen model label in cell key: {model_label}")


def _resolve_uncertainty_items(payload: Dict, axis_row: Dict, seed: int) -> tuple[List[str], List[str]]:
    explicit_ids = axis_row.get("test_item_ids")
    explicit_prompts = axis_row.get("test_item_prompts")
    if isinstance(explicit_ids, list) and explicit_ids:
        ids = [str(x) for x in explicit_ids]
        if isinstance(explicit_prompts, list) and len(explicit_prompts) == len(ids):
            return ids, [str(x) for x in explicit_prompts]

    frozen_params = payload.get("frozen_params", {})
    n_items = int((frozen_params.get("n_items_by_axis", {}) or {}).get(AXIS, adj.N_ITEMS_BY_AXIS[AXIS]))
    dev_fraction = float(frozen_params.get("dev_fraction", adj.DEV_FRACTION))
    use_fixture = bool(payload.get("use_fixture", False))
    task = c2b_tasks.load_c2b_task(AXIS, use_fixture=use_fixture)
    items = list(task.items)[:n_items]
    ids = [str(it["id"]) for it in items]
    split = adj.split_dev_test(ids, dev_fraction=dev_fraction, seed=int(seed))
    by_id = {str(it["id"]): it for it in items}
    test_items = [by_id[i] for i in split.test_ids]
    return [str(it["id"]) for it in test_items], [str(it.get("prompt", "")) for it in test_items]


def _load_cell_spec(cell_dir: Path, *, seed: int, qwen_model: str, llama_model: str) -> CellFrozenSpec:
    method_from_key, model_label = _parse_cell_key(cell_dir.name)
    result_path = cell_dir / "c2b_adjudication_results.json"
    if not result_path.exists():
        raise FileNotFoundError(f"missing frozen cell result: {result_path}")
    payload = _json_load(result_path)

    steering_method = str(payload.get("steering_method", method_from_key))
    if steering_method != method_from_key:
        raise ValueError(
            f"{cell_dir.name}: steering_method mismatch result={steering_method!r} key={method_from_key!r}"
        )

    axes = payload.get("axes", [])
    row = None
    for cand in axes:
        if str(cand.get("axis")) == AXIS:
            row = cand
            break
    if row is None:
        raise ValueError(f"{cell_dir.name}: missing {AXIS} row in frozen result")

    layer = int(row.get("layer"))
    frozen_alpha = float((row.get("dev_selection") or {}).get("frozen_alpha"))
    delta_outcome = np.asarray(row.get("per_item_diff", []), dtype=np.float64)
    if delta_outcome.ndim != 1 or delta_outcome.size < 2:
        raise ValueError(f"{cell_dir.name}: invalid per_item_diff for {AXIS}")

    sigma = float((payload.get("alpha_scale_by_axis") or {}).get(AXIS, 1.0))
    effective_alpha = (
        sigma_scaled_alpha(frozen_alpha, sigma)
        if steering_method == "iti"
        else float(frozen_alpha)
    )
    item_ids, item_prompts = _resolve_uncertainty_items(payload, row, seed)
    if len(item_ids) != delta_outcome.size:
        raise ValueError(
            f"{cell_dir.name}: item/delta length mismatch ({len(item_ids)} vs {delta_outcome.size})"
        )
    runtime_model = _runtime_model_for_label(model_label, qwen_model, llama_model)
    return CellFrozenSpec(
        cell_key=cell_dir.name[len("cell_") :],
        steering_method=steering_method,
        model_label=model_label,
        frozen_result_model=str(payload.get("model", "")),
        runtime_model=runtime_model,
        layer=layer,
        frozen_alpha=frozen_alpha,
        effective_alpha=float(effective_alpha),
        delta_outcome=delta_outcome,
        item_ids=item_ids,
        item_prompts=item_prompts,
        source_result=result_path,
    )


def _build_uncertainty_direction(
    backend: SteeredHFBackend,
    *,
    layer: int,
    method: str,
    n_extraction: int,
    seed: int,
) -> np.ndarray:
    pairs = c1.load_axis_pairs(AXIS)
    split = c1.make_split(list(pairs.pos.keys()), n_extraction=n_extraction, seed=seed)
    ext_pos = [pairs.pos[p] for p in split.extraction_ids]
    ext_neg = [pairs.neg[p] for p in split.extraction_ids]
    adapter = _HFBackendActivationAdapter(backend)
    if method == "caa":
        out = extract_caa(
            adapter,
            axis=AXIS,
            pos_texts=ext_pos,
            neg_texts=ext_neg,
            layers=[int(layer)],
            selection="separation",
        )
        return np.asarray(out.direction, dtype=np.float64)
    if method == "iti":
        out = extract_iti(
            adapter,
            axis=AXIS,
            pos_texts=ext_pos,
            neg_texts=ext_neg,
            layers=[int(layer)],
            selection="separation",
        )
        return np.asarray(out.direction, dtype=np.float64)
    raise ValueError(f"unsupported steering method: {method!r}")


def _build_prompts(item_prompts: Sequence[str]) -> List[str]:
    neutral = c1.load_neutral_prompts()[0]
    return [
        adj.format_task_input(
            AXIS,
            neutral,
            {"id": f"tmp-{i}", "prompt": str(p), "answer": "", "aliases": []},
        )
        for i, p in enumerate(item_prompts)
    ]


def _capture_hf_cell(
    spec: CellFrozenSpec,
    *,
    backend: SteeredHFBackend,
    n_extraction: int,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    prompts = _build_prompts(spec.item_prompts)
    direction = _build_uncertainty_direction(
        backend,
        layer=spec.layer,
        method=spec.steering_method,
        n_extraction=n_extraction,
        seed=seed,
    )
    baseline = backend.capture_residual_activations(prompts, spec.layer, steer=None)
    steer_cfg = SteerConfig(direction=direction, alpha=spec.effective_alpha, layer=spec.layer)
    steered = backend.capture_residual_activations(prompts, spec.layer, steer=steer_cfg)
    return baseline, steered


def _capture_synthetic_cell(
    spec: CellFrozenSpec,
    *,
    seed: int,
    mode: str,
) -> tuple[np.ndarray, np.ndarray]:
    n = len(spec.item_ids)
    d = 96
    rng = np.random.default_rng(seed)
    baseline = rng.normal(0.0, 1.0, size=(n, d))
    if mode == "signal":
        harm = -spec.delta_outcome
        order = np.argsort(np.argsort(harm))
        shift = 0.2 + 2.5 * (order / max(n - 1, 1))
        direction = rng.normal(0.0, 1.0, size=(d,))
        direction = direction / np.linalg.norm(direction)
        steered = baseline + shift[:, None] * direction[None, :]
    elif mode == "null":
        steered = baseline + rng.normal(0.0, 0.8, size=(n, d))
    else:
        raise ValueError(f"unknown synthetic mode: {mode!r}")
    return baseline.astype(np.float64), steered.astype(np.float64)


def _evaluate_cell(
    spec: CellFrozenSpec,
    *,
    baseline: np.ndarray,
    steered: np.ndarray,
    seed: int,
    bootstrap_b: int,
) -> tuple[Dict[str, object], np.ndarray]:
    reference_split_id = f"baseline_L{spec.layer}"
    evaluated_split_id = f"steered_L{spec.layer}"
    stats = ood.per_item_ood_stats(
        steered,
        baseline,
        baseline,
        reference_id=f"{spec.cell_key}:{AXIS}:baseline",
        source_hash=_sha256_array(baseline),
        reference_split_id=reference_split_id,
        evaluated_split_id=evaluated_split_id,
    )
    sp = ood.bootstrap_spearman(
        stats.mahalanobis,
        spec.delta_outcome,
        b=int(bootstrap_b),
        seed=int(seed),
        correlate_with_harm=True,
        cluster_ids=spec.item_ids,
    )
    passed = bool((sp.rho >= ood.HM_SPEARMAN_THRESHOLD) and sp.ci_excludes_zero())
    cell_out = {
        "cell_key": spec.cell_key,
        "steering_method": spec.steering_method,
        "model_label": spec.model_label,
        "frozen_result_model": spec.frozen_result_model,
        "runtime_model": spec.runtime_model,
        "layer": int(spec.layer),
        "frozen_alpha": float(spec.frozen_alpha),
        "effective_alpha": float(spec.effective_alpha),
        "n_items": int(len(spec.item_ids)),
        "item_ids": list(spec.item_ids),
        "delta_outcome": [float(x) for x in spec.delta_outcome.tolist()],
        "distance_metric": "whitened_mahalanobis",
        "norm_inflation_mean": float(np.mean(stats.norm_inflation)),
        "spearman_rho_harm": float(sp.rho),
        "ci_lo": float(sp.ci_lo),
        "ci_hi": float(sp.ci_hi),
        "ci_level": float(sp.ci_level),
        "bootstrap_b": int(sp.b),
        "threshold": float(ood.HM_SPEARMAN_THRESHOLD),
        "ci_excludes_zero": bool(sp.ci_excludes_zero()),
        "passed": passed,
        "provenance": {
            "source_result": _rel(spec.source_result),
            "reference_split_id": reference_split_id,
            "evaluated_split_id": evaluated_split_id,
            "reference_hash": stats.reference_provenance["source_hash"],
            "seed": int(seed),
        },
    }
    return cell_out, np.asarray(stats.mahalanobis, dtype=np.float64)


def _write_summary(out_dir: Path, payload: Dict[str, object]) -> None:
    lines: List[str] = []
    lines.append("# OOD Capture Summary")
    lines.append("")
    lines.append(f"- verdict: **{payload['arm_verdict']}**")
    lines.append(
        f"- criterion: >=3/4 cells with rho >= {ood.HM_SPEARMAN_THRESHOLD:.2f} and CI excluding 0"
    )
    lines.append(f"- backend: `{payload['backend']}`")
    lines.append("")
    lines.append("| cell | method | model | layer | alpha | rho(distance, -delta) | CI | n | pass |")
    lines.append("|---|---|---|---:|---:|---:|---|---:|---|")
    for cell in sorted(payload["cells"], key=lambda c: c["cell_key"]):
        ci = f"[{cell['ci_lo']:+.3f}, {cell['ci_hi']:+.3f}]"
        lines.append(
            f"| {cell['cell_key']} | {cell['steering_method']} | {cell['model_label']} | "
            f"{cell['layer']} | {cell['frozen_alpha']:.3g} | {cell['spearman_rho_harm']:+.3f} | "
            f"{ci} | {cell['n_items']} | {'YES' if cell['passed'] else 'no'} |"
        )
    lines.append("")
    out_path = out_dir / "summary.md"
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Capture OOD activations on frozen arm_full cells")
    ap.add_argument("--backend", choices=["hf", "synthetic"], default="synthetic")
    ap.add_argument("--qwen-model", default=DEFAULT_QWEN_MODEL)
    ap.add_argument("--llama-model", default=DEFAULT_LLAMA_MODEL)
    ap.add_argument("--arm-dir", default=str(_REPO / "results" / "arm_full"))
    ap.add_argument("--out-dir", default=str(_REPO / "results" / "ood_capture"))
    ap.add_argument("--seed", type=int, default=20260723)
    ap.add_argument("--n-extraction", type=int, default=28)
    ap.add_argument("--bootstrap-b", type=int, default=10000)
    ap.add_argument("--hf-home", default=None)
    ap.add_argument("--synthetic-mode", choices=["signal", "null"], default="signal")
    return ap


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.hf_home:
        os.environ["HF_HOME"] = str(args.hf_home)

    arm_dir = Path(args.arm_dir).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    cell_dirs = sorted(p for p in arm_dir.glob("cell_*") if p.is_dir())
    seen_keys = {p.name[len("cell_") :] for p in cell_dirs if p.name.startswith("cell_")}
    if seen_keys != set(FROZEN_CELL_KEYS):
        raise ValueError(
            f"frozen arm requires exactly these 4 cells: {sorted(FROZEN_CELL_KEYS)}; got {sorted(seen_keys)}"
        )

    cell_specs = [
        _load_cell_spec(
            p,
            seed=args.seed,
            qwen_model=args.qwen_model,
            llama_model=args.llama_model,
        )
        for p in cell_dirs
    ]

    model_backends: Dict[str, SteeredHFBackend] = {}
    cells_out: List[Dict[str, object]] = []
    per_cell_for_verdict: Dict[str, tuple[Sequence[float], Sequence[float]]] = {}

    for idx, spec in enumerate(cell_specs):
        if args.backend == "hf":
            backend = model_backends.get(spec.runtime_model)
            if backend is None:
                backend = SteeredHFBackend(
                    spec.runtime_model,
                    device=p0._pick_device(),
                    dtype=p0._pick_dtype(),
                    seed=args.seed,
                )
                model_backends[spec.runtime_model] = backend
            baseline, steered = _capture_hf_cell(
                spec,
                backend=backend,
                n_extraction=int(args.n_extraction),
                seed=int(args.seed),
            )
        else:
            baseline, steered = _capture_synthetic_cell(
                spec,
                seed=int(args.seed) + idx,
                mode=str(args.synthetic_mode),
            )

        cell_out, distances = _evaluate_cell(
            spec,
            baseline=baseline,
            steered=steered,
            seed=int(args.seed) + idx,
            bootstrap_b=int(args.bootstrap_b),
        )
        cells_out.append(cell_out)
        per_cell_for_verdict[spec.cell_key] = (
            list(distances),
            list(spec.delta_outcome.astype(np.float64)),
        )

    hm = ood.hm_arm_verdict(
        per_cell_for_verdict,
        b=int(args.bootstrap_b),
        seed=int(args.seed),
    )
    arm_verdict = "SUPPORT" if hm.supported else "NOT_SUPPORTED"

    payload = {
        "generated_at": utcnow(),
        "backend": str(args.backend),
        "seed": int(args.seed),
        "arm_dir": _rel(arm_dir),
        "out_dir": _rel(out_dir),
        "axis": AXIS,
        "distance_metric": "whitened_mahalanobis",
        "hm_threshold": float(ood.HM_SPEARMAN_THRESHOLD),
        "hm_required_pass_cells": int(ood.HM_REQUIRED_PASS_CELLS),
        "hm_total_cells": int(ood.HM_TOTAL_CELLS),
        "arm_verdict": arm_verdict,
        "hm_arm": hm.to_dict(),
        "cells": cells_out,
        "provenance": {
            "code_commit": git_commit(str(_REPO)),
            "platform": platform.platform(),
            "qwen_model_runtime": str(args.qwen_model),
            "llama_model_runtime": str(args.llama_model),
        },
    }

    out_json = out_dir / "ood_results.json"
    out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    _write_summary(out_dir, payload)
    print(f"[ood-capture] wrote {_rel(out_json)} ({arm_verdict})", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
