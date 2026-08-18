"""Run C2b composition shard A: CAA × Qwen × three axes × ordinary/strong prompts.

This is the GPU runner for ``docs/specs/c2b-composition-augmentation-prereg.md``.
It re-derives CAA directions via the frozen C2b extraction path, selects alpha on
the frozen DEV manifest only, then runs TEST once for prompt-alone vs prompt+steer.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Sequence

import numpy as np
import yaml

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cognitive_console.activations.provider import HFActivationProvider
from cognitive_console.eval import c2b_tasks
from cognitive_console.eval import scorers as c2b_scorers
from cognitive_console.experiments import adjudicate_c2b as adj
from cognitive_console.experiments.adjudicate_c2b import CheckpointStore, ProgressTracker, RunContext
from cognitive_console.lineage import git_commit, utcnow
from cognitive_console.steering.generate import SteeredHFBackend

from scripts import run_c2b_adjudication as c2br
from scripts import run_gpu_phase0 as p0


AXES = ("deliberation", "skepticism", "uncertainty_awareness")
BASELINES = ("ordinary", "strong")
MAX_NEW_TOKENS = {
    "deliberation": 512,
    "skepticism": 192,
    "uncertainty_awareness": 192,
}
DELTA = 0.05
Z_BONF = 2.394
Z_80 = 0.842


@dataclass
class CompositionCellResult:
    axis: str
    prompt_baseline: str
    prompt_id: str
    layer: int
    n_dev: int
    n_test: int
    k: int
    frozen_alpha: float | None
    dev_prompt_outcome: float
    dev_alpha_grid: List[Dict[str, Any]]
    dev_selected_mean_diff: float | None
    per_item_prompt: List[float]
    per_item_steer: List[float]
    per_item_diff: List[float]
    mean_diff: float
    ci_lo: float
    ci_hi: float
    ci_level: float
    bootstrap_b: int
    realized_mde_80pct: float
    coherence_ok: bool
    test_prompt_degeneracy: float
    test_steer_degeneracy: float
    parse: Dict[str, Any]
    truncation: Dict[str, Any]
    passed: bool
    verdict: str


class CompositionSampler(c2br.TranscriptScaledBackendOutcomeSampler):
    """Transcript sampler whose RNG seed identity includes prompt/phase labels."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seed_context = "unset"

    def _call_seed(self, axis: str, item: Dict, alpha: float, j: int) -> int:
        key = (
            f"{self.seed}|{self.seed_context}|{axis}|{item.get('id')}|"
            f"{float(alpha):.6f}|{j}"
        )
        return int(hashlib.sha256(key.encode("utf-8")).hexdigest(), 16) % (2**31)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _array_hash(arr: np.ndarray) -> str:
    arr = np.asarray(arr, dtype=np.float32)
    return _sha256_bytes(arr.tobytes(order="C"))


def _load_yaml(path: Path) -> Dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _load_item_manifest(path: Path) -> Dict[str, Dict[str, List[str]]]:
    out: Dict[str, Dict[str, List[str]]] = {a: {"DEV": [], "TEST": []} for a in AXES}
    seen: set[tuple[str, str]] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        axis = str(row["axis"])
        split = str(row["split"])
        item_id = str(row["item_id"])
        if row.get("headline_test_overlap"):
            raise RuntimeError(f"headline TEST overlap in frozen manifest: {axis} {item_id}")
        key = (axis, item_id)
        if key in seen:
            raise RuntimeError(f"duplicate item in frozen manifest: {key}")
        seen.add(key)
        out[axis][split].append(item_id)
    for axis in AXES:
        if set(out[axis]["DEV"]) & set(out[axis]["TEST"]):
            raise RuntimeError(f"DEV/TEST overlap in frozen manifest for {axis}")
    return out


def _load_axis_items_by_id(axis: str) -> Dict[str, Dict[str, Any]]:
    task = c2b_tasks.load_c2b_task(axis, use_fixture=False)
    return {str(item["id"]): dict(item) for item in task.items}


def _direction_reference_candidates(root: Path) -> List[Path]:
    candidates: List[Path] = []
    for base in (
        root / "results" / "arm_full" / "cell_caa__qwen2.5-7b",
        root / "results" / "c2b_adjudication_hf_2026-07-24",
    ):
        if not base.exists():
            continue
        for p in base.rglob("*"):
            name = p.name.lower()
            if p.is_file() and any(tok in name for tok in ("direction", "vector", ".npy", ".npz")):
                candidates.append(p)
    return candidates


def _derive_caa_directions(model: str, out_dir: Path, axes: Sequence[str], *,
                           n_extraction: int, direction_seed: int) -> Dict[str, Any]:
    device, dtype = p0._pick_device(), p0._pick_dtype()
    provider = HFActivationProvider(
        model,
        device=device,
        dtype=dtype,
        cache_dir=str(out_dir / "c1" / "activations" / "cache"),
    )
    refs = _direction_reference_candidates(_REPO)
    by_axis: Dict[str, Any] = {}
    for axis in axes:
        layer = 20
        direction = p0._extract_direction(provider, axis, layer, n_extraction, direction_seed)
        direction = np.asarray(direction, dtype=np.float32)
        norm = float(np.linalg.norm(direction))
        if not math.isfinite(norm) or norm <= 0:
            raise RuntimeError(f"invalid CAA direction norm for {axis}: {norm}")
        by_axis[axis] = {
            "layer": layer,
            "direction": direction,
            "norm": norm,
            "sha256": _array_hash(direction),
            "reference_status": "NO_REFERENCE_FOUND",
            "reference_cosine": None,
            "reference_candidates": [str(p.relative_to(_REPO)).replace("\\", "/") for p in refs],
            "provenance_caveat": (
                "No persisted E-0006 CAA direction vector/reference was found in this worktree; "
                "direction was re-derived with frozen C2b extraction code, layer=20, "
                f"n_extraction={n_extraction}, direction_seed={direction_seed}."
            ),
        }
    return {
        "status": "DIRECTIONS_REDERIVED_WITH_PROVENANCE_CAVEAT" if not refs else "DIRECTIONS_REDERIVED_REFERENCE_UNCHECKED",
        "model": model,
        "device": device,
        "dtype": str(dtype),
        "n_extraction": n_extraction,
        "direction_seed": direction_seed,
        "axes": by_axis,
    }


def _channel(
    sampler: CompositionSampler,
    *,
    axis: str,
    items: Sequence[Dict[str, Any]],
    instruction: str,
    alpha: float,
    k: int,
    direction: np.ndarray,
    layer: int,
    ctx: RunContext,
    phase: str,
    cell_key: str,
    cell_idx: int,
    cell_total: int,
):
    sampler.seed_context = f"{axis}|{phase}|{cell_key}|{hashlib.sha256(instruction.encode('utf-8')).hexdigest()[:12]}"
    return adj._channel_item_outcomes(  # noqa: SLF001 - frozen harness primitive
        sampler,
        axis,
        items,
        instruction,
        float(alpha),
        int(k),
        direction,
        int(layer),
        ctx=ctx,
        phase=phase,
        cell_key=cell_key,
        cell_idx=cell_idx,
        cell_total=cell_total,
    )


def _parse_stats(collector: c2br.TranscriptCollector, axis: str, phase: str, cell_key: str,
                 n_items: int, k: int) -> Dict[str, Any]:
    rows = collector._by_cell.get((axis, phase, cell_key), [])  # noqa: SLF001
    expected = int(n_items) * int(k)
    parse_fail = 0
    maybe_trunc = 0
    for row in rows:
        parse = row.get("parse") or {}
        parse_fail += int(bool(parse.get("axis_parse_failed")))
        maybe_trunc += int(bool(parse.get("maybe_truncated")))
    return {
        "records": len(rows),
        "expected_records": expected,
        "complete": len(rows) == expected,
        "axis_parse_fail_count": parse_fail,
        "axis_parse_fail_rate": parse_fail / expected if expected else None,
        "maybe_truncated_count": maybe_trunc,
        "maybe_truncated_rate": maybe_trunc / expected if expected else None,
    }


def _cell_verdict(passed: bool, mde: float, coherence_ok: bool, parse_ok: bool, trunc_ok: bool) -> str:
    if passed:
        return "COMPOSITION_GAIN_SUPPORTED"
    if (not coherence_ok) or (not parse_ok) or (not trunc_ok) or (not math.isfinite(mde)) or mde > 0.06:
        return "UNDERPOWERED_OR_INVALID"
    return "NO_INCREMENT_DEMONSTRATED"


def _realized_mde(diff: np.ndarray) -> float:
    if len(diff) <= 1:
        return float("nan")
    sd = float(np.std(diff, ddof=1))
    return float((Z_BONF + Z_80) * sd / math.sqrt(len(diff)))


def _select_alpha_on_dev(
    sampler: CompositionSampler,
    *,
    axis: str,
    prompt_baseline: str,
    prompt_id: str,
    instruction: str,
    dev_items: Sequence[Dict[str, Any]],
    direction: np.ndarray,
    layer: int,
    k: int,
    ctx: RunContext,
    cell_offset: int,
    cell_total: int,
) -> tuple[np.ndarray, np.ndarray, List[Dict[str, Any]], float | None, float | None]:
    prompt_out, prompt_deg, _ = _channel(
        sampler,
        axis=axis,
        items=dev_items,
        instruction=instruction,
        alpha=0.0,
        k=k,
        direction=direction,
        layer=layer,
        ctx=ctx,
        phase=f"dev_prompt_{prompt_baseline}",
        cell_key=f"{prompt_id}|alpha=0",
        cell_idx=cell_offset,
        cell_total=cell_total,
    )
    baseline_degen = float(prompt_deg.mean())
    gate = adj.COHERENCE_MAX_RATIO * baseline_degen + adj.COHERENCE_EPS_FLOOR
    rows: List[Dict[str, Any]] = []
    best_alpha: float | None = None
    best_improvement: float | None = None
    for i, alpha in enumerate(adj.ALPHA_GRID, 1):
        steer_out, steer_deg, _ = _channel(
            sampler,
            axis=axis,
            items=dev_items,
            instruction=instruction,
            alpha=float(alpha),
            k=k,
            direction=direction,
            layer=layer,
            ctx=ctx,
            phase=f"dev_alpha_{prompt_baseline}",
            cell_key=f"{prompt_id}|alpha={float(alpha)}",
            cell_idx=cell_offset + i,
            cell_total=cell_total,
        )
        mean_diff = float(np.mean(steer_out - prompt_out))
        degen = float(steer_deg.mean())
        ok = degen <= gate + 1e-12
        rows.append({
            "alpha": float(alpha),
            "dev_prompt_outcome": float(prompt_out.mean()),
            "dev_prompt_degeneracy": baseline_degen,
            "dev_steer_outcome": float(steer_out.mean()),
            "dev_steer_degeneracy": degen,
            "dev_mean_diff": mean_diff,
            "coherence_gate": gate,
            "coherence_ok": bool(ok),
        })
        if ok and (best_improvement is None or mean_diff > best_improvement + 1e-12):
            best_alpha = float(alpha)
            best_improvement = mean_diff
    return prompt_out, prompt_deg, rows, best_alpha, best_improvement


def _run_test_cell(
    sampler: CompositionSampler,
    collector: c2br.TranscriptCollector,
    *,
    axis: str,
    prompt_baseline: str,
    prompt_id: str,
    instruction: str,
    test_items: Sequence[Dict[str, Any]],
    direction: np.ndarray,
    layer: int,
    alpha: float | None,
    k: int,
    ctx: RunContext,
    bootstrap_b: int,
    run_seed: int,
    cell_idx: int,
    cell_total: int,
    dev_prompt_outcome: float,
    dev_alpha_grid: List[Dict[str, Any]],
    dev_selected_mean_diff: float | None,
) -> CompositionCellResult:
    prompt_phase = f"test_prompt_{prompt_baseline}"
    steer_phase = f"test_steer_{prompt_baseline}"
    prompt_key = f"{prompt_id}|alpha=0"
    if alpha is None:
        n = len(test_items)
        return CompositionCellResult(
            axis=axis, prompt_baseline=prompt_baseline, prompt_id=prompt_id,
            layer=layer, n_dev=0, n_test=n, k=k, frozen_alpha=None,
            dev_prompt_outcome=dev_prompt_outcome, dev_alpha_grid=dev_alpha_grid,
            dev_selected_mean_diff=dev_selected_mean_diff, per_item_prompt=[],
            per_item_steer=[], per_item_diff=[], mean_diff=float("nan"),
            ci_lo=float("nan"), ci_hi=float("nan"), ci_level=adj.BONFERRONI_CI_LEVEL,
            bootstrap_b=bootstrap_b, realized_mde_80pct=float("nan"),
            coherence_ok=False, test_prompt_degeneracy=float("nan"),
            test_steer_degeneracy=float("nan"), parse={}, truncation={},
            passed=False, verdict="UNDERPOWERED_OR_INVALID",
        )
    prompt_out, prompt_deg, _ = _channel(
        sampler,
        axis=axis,
        items=test_items,
        instruction=instruction,
        alpha=0.0,
        k=k,
        direction=direction,
        layer=layer,
        ctx=ctx,
        phase=prompt_phase,
        cell_key=prompt_key,
        cell_idx=cell_idx,
        cell_total=cell_total,
    )
    steer_key = f"{prompt_id}|alpha={float(alpha)}"
    steer_out, steer_deg, _ = _channel(
        sampler,
        axis=axis,
        items=test_items,
        instruction=instruction,
        alpha=float(alpha),
        k=k,
        direction=direction,
        layer=layer,
        ctx=ctx,
        phase=steer_phase,
        cell_key=steer_key,
        cell_idx=cell_idx + 1,
        cell_total=cell_total,
    )
    diff = steer_out - prompt_out
    ci = adj.cluster_bootstrap_ci(
        diff,
        b=bootstrap_b,
        ci_level=adj.BONFERRONI_CI_LEVEL,
        seed=run_seed + abs(hash((axis, prompt_baseline))) % 100000,
        cluster=True,
    )
    prompt_degen = float(prompt_deg.mean())
    steer_degen = float(steer_deg.mean())
    coherence_ok = bool(steer_degen <= adj.COHERENCE_MAX_RATIO * prompt_degen + adj.COHERENCE_EPS_FLOOR + 1e-12)
    passed = bool(adj.axis_pass(ci.point, ci.ci_lo, ci.ci_hi, coherence_ok, delta=DELTA))
    pstats = _parse_stats(collector, axis, prompt_phase, prompt_key, len(test_items), k)
    sstats = _parse_stats(collector, axis, steer_phase, steer_key, len(test_items), k)
    parse_fail_rate = max(
        float(pstats.get("axis_parse_fail_rate") or 0.0),
        float(sstats.get("axis_parse_fail_rate") or 0.0),
    )
    parse_ok = parse_fail_rate <= (0.02 if axis == "uncertainty_awareness" else 0.05)
    trunc_rate = max(
        float(pstats.get("maybe_truncated_rate") or 0.0),
        float(sstats.get("maybe_truncated_rate") or 0.0),
    )
    trunc_ok = trunc_rate <= 0.05
    mde = _realized_mde(diff)
    return CompositionCellResult(
        axis=axis,
        prompt_baseline=prompt_baseline,
        prompt_id=prompt_id,
        layer=layer,
        n_dev=0,
        n_test=len(test_items),
        k=k,
        frozen_alpha=float(alpha),
        dev_prompt_outcome=dev_prompt_outcome,
        dev_alpha_grid=dev_alpha_grid,
        dev_selected_mean_diff=dev_selected_mean_diff,
        per_item_prompt=[float(x) for x in prompt_out],
        per_item_steer=[float(x) for x in steer_out],
        per_item_diff=[float(x) for x in diff],
        mean_diff=float(ci.point),
        ci_lo=float(ci.ci_lo),
        ci_hi=float(ci.ci_hi),
        ci_level=float(ci.ci_level),
        bootstrap_b=int(bootstrap_b),
        realized_mde_80pct=mde,
        coherence_ok=coherence_ok,
        test_prompt_degeneracy=prompt_degen,
        test_steer_degeneracy=steer_degen,
        parse={"prompt": pstats, "steer": sstats, "parse_gate_ok": parse_ok},
        truncation={"max_maybe_truncated_rate": trunc_rate, "truncation_gate_ok": trunc_ok},
        passed=passed,
        verdict=_cell_verdict(passed, mde, coherence_ok, parse_ok, trunc_ok),
    )


def _write_summary(out_dir: Path, payload: Dict[str, Any]) -> None:
    lines = [
        "# C2b Composition Shard A — CAA × Qwen",
        "",
        f"- experiment_id: `{payload['experiment_id']}`",
        f"- model: `{payload['model']}`",
        f"- status: `{payload['status']}`",
        f"- direction provenance: `{payload['direction_provenance']['status']}`",
        f"- bootstrap_B: {payload['params']['bootstrap_b']}  CI: {payload['params']['ci_level']:.5f}",
        "",
        "| baseline | axis | N_test | alpha* | mean Δ | 98.33% CI | MDE80 | coherence | parse | verdict |",
        "|---|---:|---:|---:|---:|---|---:|---|---|---|",
    ]
    for cell in payload["cells"]:
        lines.append(
            f"| {cell['prompt_baseline']} | {cell['axis']} | {cell['n_test']} | "
            f"{cell['frozen_alpha']} | {cell['mean_diff']:+.4f} | "
            f"[{cell['ci_lo']:+.4f}, {cell['ci_hi']:+.4f}] | "
            f"{cell['realized_mde_80pct']:.4f} | "
            f"{'ok' if cell['coherence_ok'] else 'FAIL'} | "
            f"{'ok' if cell['parse'].get('parse_gate_ok') else 'FAIL'} | "
            f"{cell['verdict']} |"
        )
    lines.extend([
        "",
        "Ordinary and strong baselines are separate estimands. Results are additive to, and do not overwrite, the frozen substitution grid.",
    ])
    (out_dir / "composition_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct")
    parser.add_argument("--out-dir", default=str(_REPO / "results" / "composition_a_shard1" / "caa_qwen"))
    parser.add_argument("--item-manifest", default=str(_REPO / "docs" / "specs" / "c2b-composition-item-manifest.jsonl"))
    parser.add_argument("--prompt-manifest", default=str(_REPO / "docs" / "specs" / "c2b-composition-prompt-manifest.yaml"))
    parser.add_argument("--run-seed", type=int, default=20260818)
    parser.add_argument("--direction-seed", type=int, default=20260723)
    parser.add_argument("--n-extraction", type=int, default=28)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--bootstrap-b", type=int, default=10000)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--stall-timeout", type=float, default=900)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    started_at = utcnow()
    t0 = time.time()

    item_ids = _load_item_manifest(Path(args.item_manifest))
    prompt_manifest = _load_yaml(Path(args.prompt_manifest))
    prompts = prompt_manifest["axes"]

    planned_total = 0
    for axis in AXES:
        planned_total += len(BASELINES) * (
            len(item_ids[axis]["DEV"]) * adj.K_SAMPLES * (1 + len(adj.ALPHA_GRID))
            + len(item_ids[axis]["TEST"]) * adj.K_SAMPLES * 2
        )
    progress = ProgressTracker(planned_total)
    collector = c2br.TranscriptCollector(out_dir, args.model, "caa", "hf")
    checkpoint = c2br.TranscriptCheckpointStore(
        out_dir / "checkpoints",
        c2br._config_fingerprint(  # noqa: SLF001
            argparse.Namespace(
                seed=args.run_seed,
                backend="hf",
                steering_method="caa",
                max_new_tokens=max(MAX_NEW_TOKENS.values()),
                temperature=args.temperature,
                batch_size=args.batch_size,
                bootstrap_b=args.bootstrap_b,
                n_strong=1,
                enable_stronger_prompt_optimizer=False,
            ),
            args.model,
            [],
        ),
        collector=collector,
    )
    ctx = RunContext(progress=progress, checkpoint=checkpoint)

    direction_prov = _derive_caa_directions(
        args.model, out_dir, AXES, n_extraction=args.n_extraction, direction_seed=args.direction_seed
    )
    direction_public = {
        **{k: v for k, v in direction_prov.items() if k != "axes"},
        "axes": {
            axis: {k: v for k, v in row.items() if k != "direction"}
            for axis, row in direction_prov["axes"].items()
        },
    }
    (out_dir / "direction_provenance.json").write_text(
        json.dumps(direction_public, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    device, dtype = p0._pick_device(), p0._pick_dtype()
    backend = SteeredHFBackend(args.model, device=device, dtype=dtype, seed=args.run_seed)
    cells: List[CompositionCellResult] = []
    alpha_manifest: Dict[str, Any] = {
        "status": "FROZEN_AFTER_DEV_BEFORE_TEST",
        "run_seed": args.run_seed,
        "direction_seed": args.direction_seed,
        "axes": {},
    }
    cell_idx = 1
    cell_total = planned_total // adj.K_SAMPLES
    for axis in AXES:
        all_by_id = _load_axis_items_by_id(axis)
        dev_items = [all_by_id[i] for i in item_ids[axis]["DEV"]]
        test_items = [all_by_id[i] for i in item_ids[axis]["TEST"]]
        sampler = CompositionSampler(
            backend,
            max_new_tokens=MAX_NEW_TOKENS[axis],
            do_sample=True,
            temperature=args.temperature,
            seed=args.run_seed,
            batch_size=args.batch_size,
            transcript_collector=collector,
            alpha_scale_by_axis={axis: 1.0},
        )
        direction = direction_prov["axes"][axis]["direction"]
        layer = int(direction_prov["axes"][axis]["layer"])
        alpha_manifest["axes"][axis] = {}
        for baseline in BASELINES:
            prompt_row = prompts[axis][baseline]
            prompt_id = str(prompt_row["prompt_id"])
            instruction = str(prompt_row["text"])
            _, _, grid, alpha, dev_diff = _select_alpha_on_dev(
                sampler,
                axis=axis,
                prompt_baseline=baseline,
                prompt_id=prompt_id,
                instruction=instruction,
                dev_items=dev_items,
                direction=direction,
                layer=layer,
                k=adj.K_SAMPLES,
                ctx=ctx,
                cell_offset=cell_idx,
                cell_total=cell_total,
            )
            cell_idx += 1 + len(adj.ALPHA_GRID)
            alpha_manifest["axes"][axis][baseline] = {
                "prompt_id": prompt_id,
                "frozen_alpha": alpha,
                "dev_selected_mean_diff": dev_diff,
                "grid": grid,
            }
        (out_dir / "alpha_manifest.yaml").write_text(
            yaml.safe_dump(alpha_manifest, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )

    # TEST starts only after all DEV alpha selections have been persisted.
    for axis in AXES:
        all_by_id = _load_axis_items_by_id(axis)
        test_items = [all_by_id[i] for i in item_ids[axis]["TEST"]]
        sampler = CompositionSampler(
            backend,
            max_new_tokens=MAX_NEW_TOKENS[axis],
            do_sample=True,
            temperature=args.temperature,
            seed=args.run_seed,
            batch_size=args.batch_size,
            transcript_collector=collector,
            alpha_scale_by_axis={axis: 1.0},
        )
        direction = direction_prov["axes"][axis]["direction"]
        layer = int(direction_prov["axes"][axis]["layer"])
        for baseline in BASELINES:
            prompt_row = prompts[axis][baseline]
            prompt_id = str(prompt_row["prompt_id"])
            instruction = str(prompt_row["text"])
            alpha_info = alpha_manifest["axes"][axis][baseline]
            cell = _run_test_cell(
                sampler,
                collector,
                axis=axis,
                prompt_baseline=baseline,
                prompt_id=prompt_id,
                instruction=instruction,
                test_items=test_items,
                direction=direction,
                layer=layer,
                alpha=alpha_info["frozen_alpha"],
                k=adj.K_SAMPLES,
                ctx=ctx,
                bootstrap_b=args.bootstrap_b,
                run_seed=args.run_seed,
                cell_idx=cell_idx,
                cell_total=cell_total,
                dev_prompt_outcome=float(alpha_info["grid"][0]["dev_prompt_outcome"]),
                dev_alpha_grid=list(alpha_info["grid"]),
                dev_selected_mean_diff=alpha_info["dev_selected_mean_diff"],
            )
            cell.n_dev = len(item_ids[axis]["DEV"])
            cells.append(cell)
            cell_idx += 2

    transcript_dir = out_dir / "transcripts"
    transcript_dir.mkdir(parents=True, exist_ok=True)
    for (axis, phase, cell_key), rows in sorted(collector._by_cell.items()):  # noqa: SLF001
        path = transcript_dir / f"{axis}__{phase}__{c2br._normalize_alpha(abs(hash(cell_key)) % 10**8)}.jsonl"  # noqa: SLF001
        with path.open("w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    payload = {
        "experiment_id": "composition-a-qwen-caa-20260818-0001",
        "status": "done",
        "valid_for_paper": False,
        "prereg": "docs/specs/c2b-composition-augmentation-prereg.md",
        "item_manifest": "docs/specs/c2b-composition-item-manifest.jsonl",
        "prompt_manifest": "docs/specs/c2b-composition-prompt-manifest.yaml",
        "model": args.model,
        "backend": "hf",
        "steering_method": "CAA",
        "run_seed": args.run_seed,
        "direction_seed": args.direction_seed,
        "started_at": started_at,
        "ended_at": utcnow(),
        "wall_clock_seconds": round(time.time() - t0, 3),
        "platform": platform.platform(),
        "hardware": f"{device}-{dtype}",
        "code_commit": git_commit(str(_REPO)),
        "params": {
            "alpha_grid": list(adj.ALPHA_GRID),
            "delta": DELTA,
            "k": adj.K_SAMPLES,
            "bootstrap_b": args.bootstrap_b,
            "ci_level": adj.BONFERRONI_CI_LEVEL,
            "coherence_rule": "steered_degeneracy <= 1.5 * prompt_alone_degeneracy + 0.02",
            "max_new_tokens": MAX_NEW_TOKENS,
            "temperature": args.temperature,
            "batch_size": args.batch_size,
        },
        "direction_provenance": direction_public,
        "cells": [asdict(cell) for cell in cells],
        "shard_verdicts_by_baseline": {},
    }
    for baseline in BASELINES:
        b_cells = [c for c in payload["cells"] if c["prompt_baseline"] == baseline]
        if any(c["verdict"] == "COMPOSITION_GAIN_SUPPORTED" for c in b_cells):
            verdict = "COMPOSITION_GAIN_SUPPORTED"
        elif any(c["verdict"] == "UNDERPOWERED_OR_INVALID" for c in b_cells):
            verdict = "UNDERPOWERED_OR_INVALID"
        else:
            verdict = "NO_INCREMENT_DEMONSTRATED"
        payload["shard_verdicts_by_baseline"][baseline] = verdict

    (out_dir / "composition_results.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    _write_summary(out_dir, payload)
    print(json.dumps({
        "experiment_id": payload["experiment_id"],
        "out_dir": str(out_dir),
        "wall_clock_seconds": payload["wall_clock_seconds"],
        "verdicts": payload["shard_verdicts_by_baseline"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
