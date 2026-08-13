"""Experiment A runner: powered TOST + retained raw bundle.

Implements the frozen protocol in ``docs/specs/powered-tost-A-prereg.md``.
The runner is staged: preflight -> DEV seal -> TEST-once -> manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence

import numpy as np

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cognitive_console.activations.provider import HFActivationProvider
from cognitive_console.eval import c2b_tasks
from cognitive_console.experiments import adjudicate_c2b as adj
from cognitive_console.ops.disk_guard import check_disk_budget, default_guard_paths
from cognitive_console.ops.hardware_profiles import (
    get_authorized_hardware_profile,
    validate_hardware_profile,
)
from scripts import run_c1_facade as c1
from scripts import run_c2b_adjudication as base
from scripts import run_gpu_phase0 as p0

PROTOCOL_ID = "powered-tost-A-20260813"
DEV_EXPERIMENT_ID = "powered-tost-A-dev-20260813"
TEST_EXPERIMENT_ID = "powered-tost-A-test-20260813"
PREREG_PATH = "docs/specs/powered-tost-A-prereg.md"
SEED = 20260812
K_SAMPLES = adj.K_SAMPLES
BOOTSTRAP_B = 10_000
BONFERRONI_CI_LEVEL = adj.BONFERRONI_CI_LEVEL
TOST_CI_LEVEL = 0.90
SESOI = 0.05
MAX_NEW_TOKENS = 64
TEMPERATURE = 0.7
N_STRONG = 16
N_EXTRACTION = 28
TEST_ATTEMPT_ROOT_ENV = "CC_TEST_ATTEMPT_ROOT"
DEFAULT_TEST_ATTEMPT_ROOT = Path(
    "/var/lib/cognitive-console/powered-tost-A/test-attempts"
)

QWEN_MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"
QWEN_REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"
LLAMA_MODEL_ID = "NousResearch/Meta-Llama-3-8B-Instruct"


@dataclass(frozen=True)
class Cell:
    cell_id: str
    method: str
    model_key: str
    model_id: str
    model_revision: Optional[str]
    axis: str
    layer: int
    current_n: int
    se_estimate: float
    current_mde: float
    selected_total_n: int
    planned_test_n: int
    layer_source: str

    @property
    def per_item_sigma(self) -> float:
        return self.se_estimate * float(np.sqrt(self.current_n))

    @property
    def exact_n_target(self) -> float:
        return self.current_n * (self.current_mde / SESOI) ** 2

    @property
    def planned_mde(self) -> float:
        return self.current_mde * float(np.sqrt(self.current_n / self.planned_test_n))


CELLS: tuple[Cell, ...] = (
    Cell(
        "A1",
        "caa",
        "qwen",
        QWEN_MODEL_ID,
        QWEN_REVISION,
        "deliberation",
        20,
        40,
        0.023080,
        0.074700,
        225,
        150,
        "results/arm_full/cell_caa__qwen2.5-7b/c2b_adjudication_results.json",
    ),
    Cell(
        "A2",
        "caa",
        "llama",
        LLAMA_MODEL_ID,
        None,
        "deliberation",
        12,
        40,
        0.021706,
        0.070200,
        225,
        150,
        "results/arm_full/cell_caa__llama3-8b/c2b_adjudication_results.json",
    ),
    Cell(
        "A3",
        "caa",
        "qwen",
        QWEN_MODEL_ID,
        QWEN_REVISION,
        "skepticism",
        20,
        40,
        0.058089,
        0.188000,
        757,
        505,
        "results/arm_full/cell_caa__qwen2.5-7b/c2b_adjudication_results.json",
    ),
    Cell(
        "A4",
        "caa",
        "qwen",
        QWEN_MODEL_ID,
        QWEN_REVISION,
        "uncertainty_awareness",
        20,
        53,
        0.060493,
        0.195800,
        1219,
        813,
        "results/arm_full/cell_caa__qwen2.5-7b/c2b_adjudication_results.json",
    ),
)


def _sha256_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _atomic_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_name(path.name + ".new")
    pending.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(pending, path)


def _git_identity(expected_commit: Optional[str], require_clean: bool) -> Dict[str, object]:
    actual = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=_REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=_REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    dirty = bool(status)
    if expected_commit and actual != expected_commit:
        raise ValueError(
            f"code commit mismatch: expected={expected_commit}, actual={actual}"
        )
    if require_clean and dirty:
        raise ValueError(f"run requires a clean source tree; dirty status:\n{status}")
    return {"code_commit": actual, "dirty_tree": dirty}


def _assert_external_output(out_dir: Path) -> None:
    try:
        Path(out_dir).resolve().relative_to(_REPO.resolve())
    except ValueError:
        return
    raise ValueError("HF output directory must be outside the source repository")


def _reject_symlink_components(path: Path) -> None:
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"TEST attempt path must not contain symlinks: {current}")


def _assert_owner_writable_directory(path: Path) -> None:
    mode = path.stat()
    if os.name == "posix":
        if mode.st_uid != os.geteuid():
            raise PermissionError(f"TEST attempt path is not owned by current user: {path}")
        if not mode.st_mode & stat.S_IWUSR:
            raise PermissionError(f"TEST attempt path is not owner-writable: {path}")
    if not os.access(path, os.W_OK):
        raise PermissionError(f"TEST attempt path is not writable: {path}")


def resolve_test_attempt_registry(*, prepare: bool = False) -> Dict[str, object]:
    raw_override = os.environ.get(TEST_ATTEMPT_ROOT_ENV)
    overridden = raw_override is not None
    if overridden:
        owner_root = Path(str(raw_override))
        if not owner_root.is_absolute():
            raise ValueError(f"{TEST_ATTEMPT_ROOT_ENV} must be absolute")
        registry_root = owner_root / "powered-tost-A" / "test-attempts"
    else:
        owner_root = DEFAULT_TEST_ATTEMPT_ROOT.parents[1]
        registry_root = DEFAULT_TEST_ATTEMPT_ROOT
    _reject_symlink_components(owner_root)
    _reject_symlink_components(registry_root)
    if prepare:
        registry_root.mkdir(parents=True, exist_ok=True)
        _reject_symlink_components(owner_root)
        _reject_symlink_components(registry_root)
        _assert_owner_writable_directory(owner_root)
        _assert_owner_writable_directory(registry_root)
    return {
        "registry_root": str(registry_root),
        "registry_root_overridden": overridden,
        "registry_owner_root": str(owner_root),
        "registry_root_env": TEST_ATTEMPT_ROOT_ENV,
    }


def test_attempt_marker_path(cell_id: str, profile: Optional[Mapping[str, object]] = None) -> Path:
    if cell_id not in {cell.cell_id for cell in CELLS}:
        raise ValueError(f"unknown cell_id {cell_id!r}")
    registry = profile or resolve_test_attempt_registry()
    return Path(str(registry["registry_root"])) / f"{TEST_EXPERIMENT_ID}-{cell_id}.json"


def claim_test_attempt(
    *,
    cell: Cell,
    code_identity: Mapping[str, object],
    dev_selection_sha256: str,
    out_dir: Path,
    profile: Optional[Mapping[str, object]] = None,
) -> Path:
    registry = profile or resolve_test_attempt_registry(prepare=True)
    marker = test_attempt_marker_path(cell.cell_id, registry)
    payload = {
        "protocol_id": PROTOCOL_ID,
        "experiment_id": f"{TEST_EXPERIMENT_ID}-{cell.cell_id}",
        "cell": asdict(cell),
        "code_identity": dict(code_identity),
        "dev_selection_sha256": str(dev_selection_sha256),
        "artifact_out_dir": str(Path(out_dir).resolve()),
        **dict(registry),
        "meaning": "TEST generation for this fixed cell is authorized to begin exactly once",
    }
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    try:
        fd = os.open(marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise PermissionError(
            f"TEST-once guard: {cell.cell_id} already has marker at {marker}"
        ) from exc
    with os.fdopen(fd, "wb") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
    return marker


def _capture_hardware(profile_id: str, *, after_load: bool = False) -> Dict[str, object]:
    import torch

    if not torch.cuda.is_available():
        raise ValueError("authorized A800 profile requires CUDA")
    if torch.cuda.device_count() != 1:
        raise ValueError("bind exactly one logical CUDA device before the run")
    profile = get_authorized_hardware_profile(profile_id)
    free_bytes, total_bytes = torch.cuda.mem_get_info(0)
    return validate_hardware_profile(
        profile,
        device_name=torch.cuda.get_device_name(0),
        total_vram_gib=total_bytes / 1024**3,
        free_vram_gib=free_bytes / 1024**3,
        after_load=after_load,
    )


def _excluded_ids(axis: str) -> frozenset[str]:
    if axis == "deliberation":
        return frozenset(f"gsm8k-test-{i:05d}" for i in range(60))
    if axis == "skepticism":
        return frozenset(f"truthfulqa-mc1-{i:05d}" for i in range(60))
    if axis == "uncertainty_awareness":
        return frozenset(f"triviaqa-{i:05d}" for i in range(80))
    raise ValueError(f"unknown axis {axis!r}")


def _split_sizes(total: int) -> tuple[int, int]:
    n_dev = int(round(total * adj.DEV_FRACTION))
    n_dev = max(1, min(n_dev, total - 1))
    return n_dev, total - n_dev


def _select_disjoint_items(
    items: Sequence[Mapping[str, object]],
    *,
    excluded_ids: Iterable[str],
    n_total: int,
    seed: int = SEED,
) -> List[Dict[str, object]]:
    excluded = {str(value) for value in excluded_ids}
    seen: set[str] = set()
    eligible: List[Dict[str, object]] = []
    for raw in items:
        item = dict(raw)
        item_id = str(item.get("id", ""))
        if not item_id:
            raise ValueError("item lacks non-empty id")
        if item_id in seen:
            raise ValueError(f"duplicate item id: {item_id}")
        seen.add(item_id)
        if item_id not in excluded:
            eligible.append(item)
    if len(eligible) < int(n_total):
        raise ValueError(
            f"disjoint pool too small: eligible={len(eligible)}, requested={n_total}"
        )
    rng = np.random.default_rng(seed)
    selected_positions = sorted(rng.permutation(len(eligible))[: int(n_total)].tolist())
    selected = [eligible[index] for index in selected_positions]
    selected_ids = {str(item["id"]) for item in selected}
    if selected_ids & excluded:
        raise AssertionError("frozen-item leakage after disjoint sampling")
    return selected


def _synthetic_items(axis: str, n: int) -> List[Dict[str, object]]:
    if axis == "deliberation":
        return [
            {"id": f"gsm8k-test-{i:05d}", "prompt": f"Synthetic math {i}: 1+1?", "answer": "2"}
            for i in range(max(n, 300))
        ]
    if axis == "skepticism":
        return [
            {
                "id": f"truthfulqa-mc1-{i:05d}",
                "prompt": f"Synthetic false-premise question {i}?",
                "choices": {"A": "reject", "B": "accept"},
                "answer_letter": "A",
            }
            for i in range(max(n, 900))
        ]
    if axis == "uncertainty_awareness":
        return [
            {
                "id": f"triviaqa-{i:05d}",
                "prompt": f"Synthetic trivia {i}?",
                "answer": "answer",
                "aliases": ["answer"],
            }
            for i in range(max(n, 1400))
        ]
    raise ValueError(axis)


def _load_axis_pool(axis: str, backend: str) -> List[Dict[str, object]]:
    if backend == "synthetic":
        n = max(cell.selected_total_n for cell in CELLS if cell.axis == axis)
        return _synthetic_items(axis, n + len(_excluded_ids(axis)) + 10)
    if axis == "deliberation":
        return c2b_tasks.load_gsm8k_test(n=None, seed=0)
    if axis == "skepticism":
        return c2b_tasks.load_skepticism_set(
            n=None, seed=0, revision=c2b_tasks.TRUTHFULQA_REVISION
        )
    if axis == "uncertainty_awareness":
        return c2b_tasks.load_uncertainty_set(
            n=None, seed=0, revision=c2b_tasks.TRIVIAQA_REVISION
        )
    raise ValueError(axis)


def load_selected_items(backend: str) -> Dict[str, List[Dict[str, object]]]:
    selected: Dict[str, List[Dict[str, object]]] = {}
    for axis in sorted({cell.axis for cell in CELLS}):
        pool = _load_axis_pool(axis, backend)
        n_total = max(cell.selected_total_n for cell in CELLS if cell.axis == axis)
        selected[axis] = _select_disjoint_items(
            pool,
            excluded_ids=_excluded_ids(axis),
            n_total=n_total,
            seed=SEED,
        )
    return selected


def sampling_manifest(items_by_axis: Mapping[str, Sequence[Mapping[str, object]]]) -> Dict[str, object]:
    axes: Dict[str, object] = {}
    for axis, items in sorted(items_by_axis.items()):
        ids = [str(item["id"]) for item in items]
        split = adj.split_dev_test(ids, seed=SEED)
        n_dev, n_test = _split_sizes(len(ids))
        if len(split.dev_ids) != n_dev or len(split.test_ids) != n_test:
            raise AssertionError(f"split-size mismatch for {axis}")
        if set(split.dev_ids) & set(split.test_ids):
            raise AssertionError(f"DEV/TEST overlap for {axis}")
        axes[axis] = {
            "n_total": len(ids),
            "n_dev": len(split.dev_ids),
            "n_test": len(split.test_ids),
            "excluded_frozen_ids": sorted(_excluded_ids(axis)),
            "selected_item_ids_sha256": _sha256_bytes(
                json.dumps(ids, separators=(",", ":")).encode("utf-8")
            ),
            "dev_item_ids_sha256": _sha256_bytes(
                json.dumps(split.dev_ids, separators=(",", ":")).encode("utf-8")
            ),
            "test_item_ids_sha256": _sha256_bytes(
                json.dumps(split.test_ids, separators=(",", ":")).encode("utf-8")
            ),
            "selected_item_ids": ids,
            "dev_item_ids": split.dev_ids,
            "test_item_ids": split.test_ids,
        }
    return {"protocol_id": PROTOCOL_ID, "seed": SEED, "axes": axes}


def power_manifest() -> Dict[str, object]:
    return {
        "sesoi": SESOI,
        "source": "results/posthoc_equivalence/posthoc_equivalence_e0006.json",
        "cells": [
            {
                **asdict(cell),
                "per_item_sigma": cell.per_item_sigma,
                "exact_n_target": cell.exact_n_target,
                "n_target_ceiling": int(np.ceil(cell.exact_n_target)),
                "planned_mde": cell.planned_mde,
            }
            for cell in CELLS
        ],
    }


def _by_id(items: Sequence[Mapping[str, object]]) -> Dict[str, Dict[str, object]]:
    return {str(item["id"]): dict(item) for item in items}


def _dev_test_items(axis_items: Sequence[Mapping[str, object]]) -> tuple[List[Dict], List[Dict]]:
    ids = [str(item["id"]) for item in axis_items]
    by_id = _by_id(axis_items)
    split = adj.split_dev_test(ids, seed=SEED)
    return [by_id[item_id] for item_id in split.dev_ids], [by_id[item_id] for item_id in split.test_ids]


def _build_synthetic_spec(cell: Cell, items_by_axis: Mapping[str, Sequence[Mapping[str, object]]]) -> adj.AxisAdjSpec:
    return adj.AxisAdjSpec(
        axis=cell.axis,
        items=[dict(item) for item in items_by_axis[cell.axis]],
        strong_prompts=base.build_strong_prompts(cell.axis, N_STRONG),
        neutral_prompt=c1.load_neutral_prompts()[0],
        direction=np.ones(8),
        layer=cell.layer,
    )


def _provider_for_model(cell: Cell, cache_root: Path) -> HFActivationProvider:
    device, dtype = p0._pick_device(), p0._pick_dtype()
    return HFActivationProvider(
        cell.model_id,
        device=device,
        dtype=dtype,
        cache_dir=str(Path(os.environ.get("POWERED_TOST_ACTIVATION_CACHE", str(cache_root))) / cell.model_key),
        model_revision=cell.model_revision,
    )


def _build_hf_specs(
    cells: Sequence[Cell],
    items_by_axis: Mapping[str, Sequence[Mapping[str, object]]],
    work_dir: Path,
) -> tuple[Dict[str, adj.AxisAdjSpec], Dict[str, object]]:
    specs: Dict[str, adj.AxisAdjSpec] = {}
    meta: Dict[str, object] = {"models": {}, "directions": {}}
    neutral = c1.load_neutral_prompts()[0]
    for model_key in sorted({cell.model_key for cell in cells}):
        model_cells = [cell for cell in cells if cell.model_key == model_key]
        provider = _provider_for_model(model_cells[0], work_dir / "activation_cache")
        meta["models"][model_key] = {
            "model_id": model_cells[0].model_id,
            "model_revision": model_cells[0].model_revision,
            "available_layers": list(provider.available_layers()),
        }
        for cell in model_cells:
            direction = p0._extract_direction(
                provider, cell.axis, cell.layer, N_EXTRACTION, SEED
            )
            direction_path = work_dir / "directions" / f"{cell.cell_id}-{cell.axis}-L{cell.layer}.npy"
            direction_path.parent.mkdir(parents=True, exist_ok=True)
            np.save(direction_path, np.asarray(direction))
            meta["directions"][cell.cell_id] = {
                "path": str(direction_path),
                "sha256": _sha256_file(direction_path),
                "layer": cell.layer,
                "axis": cell.axis,
            }
            specs[cell.cell_id] = adj.AxisAdjSpec(
                axis=cell.axis,
                items=[dict(item) for item in items_by_axis[cell.axis]],
                strong_prompts=base.build_strong_prompts(cell.axis, N_STRONG),
                neutral_prompt=neutral,
                direction=np.asarray(direction),
                layer=cell.layer,
            )
    return specs, meta


def _config_fingerprint(cell: Cell, spec: adj.AxisAdjSpec, phase: str) -> str:
    payload = {
        "protocol_id": PROTOCOL_ID,
        "cell": asdict(cell),
        "phase": phase,
        "seed": SEED,
        "k": K_SAMPLES,
        "bootstrap_b": BOOTSTRAP_B,
        "bonferroni_ci_level": BONFERRONI_CI_LEVEL,
        "tost_ci_level": TOST_CI_LEVEL,
        "sesoi": SESOI,
        "alpha_grid": list(adj.ALPHA_GRID),
        "max_new_tokens": MAX_NEW_TOKENS,
        "temperature": TEMPERATURE,
        "item_ids": [str(item["id"]) for item in spec.items],
        "strong_prompt_ids": [str(pid) for pid, _ in spec.strong_prompts],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]


def select_on_dev_with_scores(
    sampler: adj.OutcomeSampler,
    spec: adj.AxisAdjSpec,
    dev_items: Sequence[Dict],
    *,
    ctx: Optional[adj.RunContext],
) -> tuple[adj.DevSelection, Dict[str, object]]:
    best_pid, best_ptext, best_pout = None, None, -np.inf
    prompt_scores: List[Dict[str, object]] = []
    for pi, (pid, ptext) in enumerate(spec.strong_prompts):
        outs, _, _ = adj._channel_item_outcomes(  # noqa: SLF001 - frozen runner hook
            sampler,
            spec.axis,
            dev_items,
            ptext,
            0.0,
            K_SAMPLES,
            spec.direction,
            spec.layer,
            ctx=ctx,
            phase=adj.PHASE_DEV_PROMPT,
            cell_key=f"prompt={pid}|alpha=0",
            cell_idx=pi + 1,
            cell_total=len(spec.strong_prompts),
        )
        val = float(outs.mean())
        prompt_scores.append({"prompt_id": str(pid), "dev_prompt_outcome": val})
        if val > best_pout:
            best_pid, best_ptext, best_pout = pid, ptext, val

    _, base_deg, _ = adj._channel_item_outcomes(  # noqa: SLF001
        sampler,
        spec.axis,
        dev_items,
        spec.neutral_prompt,
        0.0,
        K_SAMPLES,
        spec.direction,
        spec.layer,
        ctx=ctx,
        phase=adj.PHASE_DEV_BASELINE,
        cell_key="alpha=0",
        cell_idx=1,
        cell_total=1,
    )
    baseline_degeneracy = float(base_deg.mean())
    gate_ceiling = adj.COHERENCE_MAX_RATIO * baseline_degeneracy + adj.COHERENCE_EPS_FLOOR

    grid_rows: List[Dict[str, object]] = []
    frozen_alpha: Optional[float] = None
    best_steer_out: Optional[float] = None
    for ai, alpha in enumerate(adj.ALPHA_GRID):
        outs, degs, _ = adj._channel_item_outcomes(  # noqa: SLF001
            sampler,
            spec.axis,
            dev_items,
            spec.neutral_prompt,
            float(alpha),
            K_SAMPLES,
            spec.direction,
            spec.layer,
            ctx=ctx,
            phase=adj.PHASE_DEV_ALPHA,
            cell_key=f"alpha={float(alpha)}",
            cell_idx=ai + 1,
            cell_total=len(adj.ALPHA_GRID),
        )
        steer_out = float(outs.mean())
        steer_deg = float(degs.mean())
        coherence_ok = steer_deg <= gate_ceiling + 1e-12
        grid_rows.append(
            {
                "alpha": float(alpha),
                "dev_steer_outcome": steer_out,
                "degeneracy": steer_deg,
                "coherence_ok": coherence_ok,
            }
        )
        if coherence_ok and (best_steer_out is None or steer_out > best_steer_out):
            best_steer_out = steer_out
            frozen_alpha = float(alpha)

    selection = adj.DevSelection(
        best_prompt_id=str(best_pid),
        best_prompt_text=str(best_ptext),
        dev_prompt_outcome=float(best_pout),
        frozen_alpha=frozen_alpha,
        dev_steer_outcome=best_steer_out,
        baseline_degeneracy=baseline_degeneracy,
        alpha_grid=grid_rows,
        any_alpha_passes_gate=frozen_alpha is not None,
    )
    diagnostics = {
        "prompt_scores": prompt_scores,
        "gate_ceiling": gate_ceiling,
        "n_dev": len(dev_items),
        "dev_item_ids": [str(item["id"]) for item in dev_items],
    }
    return selection, diagnostics


def _sampler_factory(
    cell: Cell,
    *,
    backend: str,
    collector: base.TranscriptCollector,
    batch_size: int,
):
    if backend == "synthetic":
        task_backend = base.SyntheticC2bTaskBackend(
            cell.axis, _synthetic_items(cell.axis, cell.selected_total_n + 100), prompt_gain=0.4, alpha_gain=0.1, threshold=0.5
        )
        return base.TranscriptBackendOutcomeSampler(
            task_backend,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=False,
            temperature=TEMPERATURE,
            seed=SEED,
            batch_size=batch_size,
            transcript_collector=collector,
        )
    factory = base.hf_sampler_factory(
        cell.model_id,
        MAX_NEW_TOKENS,
        TEMPERATURE,
        SEED,
        batch_size,
        collector,
        alpha_scale_by_axis={cell.axis: 1.0},
        model_revision=cell.model_revision,
    )
    factory.backend._ensure_loaded()
    return factory(cell.axis)


def _cell_dir(out_dir: Path, cell: Cell) -> Path:
    return out_dir / "cells" / cell.cell_id


def _preflight(args) -> int:
    out_dir = Path(args.out_dir).resolve()
    identity = _git_identity(args.expected_code_commit, args.backend == "hf")
    if args.backend == "hf":
        _assert_external_output(out_dir)
    items = load_selected_items(args.backend)
    payload = {
        "protocol_id": PROTOCOL_ID,
        "phase": "PREFLIGHT",
        "scientific_status": "OPERATIONAL_ONLY_NOT_DEV_OR_TEST",
        "code_identity": identity,
        "power": power_manifest(),
        "sampling": sampling_manifest(items),
        "dataset_revisions": {
            "openai/gsm8k": "default-as-resolved-at-run",
            "truthfulqa/truthful_qa": c2b_tasks.TRUTHFULQA_REVISION,
            "mandarjoshi/trivia_qa": c2b_tasks.TRIVIAQA_REVISION,
        },
        "platform": platform.platform(),
    }
    if args.backend == "hf":
        hardware = _capture_hardware(args.hardware_profile)
        profile = get_authorized_hardware_profile(args.hardware_profile)
        disk = check_disk_budget(
            default_guard_paths(args.hf_home, args.venv),
            profile.disk_budget_gib,
            profile.disk_ceiling_gib,
        )
        payload["hardware_pre_load"] = hardware
        payload["disk"] = disk.to_dict()
    _atomic_json(out_dir / "preflight" / "preflight.json", payload)
    for axis, row in payload["sampling"]["axes"].items():
        print(f"[powered-tost-A] preflight {axis}: DEV/TEST={row['n_dev']}/{row['n_test']}", flush=True)
    return 0


def _make_specs(args, items: Mapping[str, Sequence[Mapping[str, object]]], work_dir: Path) -> tuple[Dict[str, adj.AxisAdjSpec], Dict[str, object]]:
    if args.backend == "synthetic":
        return (
            {cell.cell_id: _build_synthetic_spec(cell, items) for cell in CELLS},
            {"models": {"synthetic": {"model_id": "synthetic"}}, "directions": {}},
        )
    return _build_hf_specs(CELLS, items, work_dir)


def _dev(args) -> int:
    out_dir = Path(args.out_dir).resolve()
    if args.backend == "hf":
        _assert_external_output(out_dir)
    identity = _git_identity(args.expected_code_commit, args.backend == "hf")
    if (out_dir / "dev" / "SEALED.json").exists():
        raise ValueError("DEV is already sealed; do not overwrite it")
    items = load_selected_items(args.backend)
    hardware = _capture_hardware(args.hardware_profile) if args.backend == "hf" else None
    specs, spec_meta = _make_specs(args, items, out_dir / "dev" / "work")
    sampling = sampling_manifest(items)
    selections: Dict[str, object] = {}
    for cell in CELLS:
        cell_out = _cell_dir(out_dir / "dev", cell)
        collector = base.TranscriptCollector(cell_out / "work", cell.model_id, cell.method, args.backend)
        sampler = _sampler_factory(cell, backend=args.backend, collector=collector, batch_size=args.batch_size)
        spec = specs[cell.cell_id]
        dev_items, _ = _dev_test_items(spec.items)
        ckpt = base.TranscriptCheckpointStore(
            cell_out / "work" / "checkpoints",
            _config_fingerprint(cell, spec, "dev"),
            seed=SEED,
            fresh=False,
            collector=collector,
        )
        ctx = adj.RunContext(checkpoint=ckpt)
        try:
            selection, diagnostics = select_on_dev_with_scores(sampler, spec, dev_items, ctx=ctx)
        finally:
            ckpt.close()
        collector.write_raw(cell_out / "work" / "transcripts")
        selection_payload = {
            "protocol_id": PROTOCOL_ID,
            "experiment_id": f"{DEV_EXPERIMENT_ID}-{cell.cell_id}",
            "phase": "DEV",
            "cell": asdict(cell),
            "code_identity": identity,
            "hardware": hardware,
            "sampling_axis": sampling["axes"][cell.axis],
            "direction": spec_meta.get("directions", {}).get(cell.cell_id),
            "selection": asdict(selection),
            "diagnostics": diagnostics,
            "model_meta": spec_meta.get("models", {}).get(cell.model_key),
        }
        selection_path = cell_out / "sealed" / "dev_selection.json"
        _atomic_json(selection_path, selection_payload)
        selections[cell.cell_id] = {
            "dev_selection_path": str(selection_path),
            "dev_selection_sha256": _sha256_file(selection_path),
            "selected_alpha": selection.frozen_alpha,
            "best_prompt_id": selection.best_prompt_id,
        }
        print(
            f"[powered-tost-A] DEV sealed {cell.cell_id}: alpha={selection.frozen_alpha} prompt={selection.best_prompt_id}",
            flush=True,
        )
    seal_payload = {
        "protocol_id": PROTOCOL_ID,
        "experiment_id": DEV_EXPERIMENT_ID,
        "phase": "DEV_SEALED",
        "code_identity": identity,
        "sampling": sampling,
        "selections": selections,
    }
    seal_path = out_dir / "dev" / "SEALED.json"
    _atomic_json(seal_path, seal_payload)
    print(f"[powered-tost-A] DEV SEALED {seal_path}", flush=True)
    return 0


def _load_dev_selection(out_dir: Path, cell: Cell) -> tuple[Dict[str, object], str]:
    path = _cell_dir(out_dir / "dev", cell) / "sealed" / "dev_selection.json"
    if not path.exists():
        raise ValueError(f"missing DEV selection for {cell.cell_id}: {path}")
    return json.loads(path.read_text(encoding="utf-8")), _sha256_file(path)


def strict_verdict(result: adj.AxisAdjResult, tost_ci: adj.BootstrapCI) -> str:
    if bool(result.passed):
        return "PASS"
    if result.ci_hi < 0.0:
        return "NEGATIVE-CONTRAST"
    if tost_ci.ci_lo >= -SESOI and tost_ci.ci_hi <= SESOI:
        return "EQUIVALENT"
    return "UNDERPOWERED"


def _test(args) -> int:
    out_dir = Path(args.out_dir).resolve()
    if args.backend == "hf":
        _assert_external_output(out_dir)
    identity = _git_identity(args.expected_code_commit, args.backend == "hf")
    dev_seal = out_dir / "dev" / "SEALED.json"
    if not dev_seal.exists():
        raise ValueError("TEST requires DEV SEALED.json")
    if (out_dir / "test" / "SEALED.json").exists():
        raise ValueError("TEST is already sealed; do not overwrite it")
    dev_payload = json.loads(dev_seal.read_text(encoding="utf-8"))
    if dev_payload.get("protocol_id") != PROTOCOL_ID:
        raise ValueError("DEV seal protocol mismatch")
    if dev_payload.get("code_identity", {}).get("code_commit") != identity["code_commit"]:
        raise ValueError("TEST code commit differs from DEV")

    items = load_selected_items(args.backend)
    sampling = sampling_manifest(items)
    if sampling != dev_payload["sampling"]:
        raise ValueError("TEST sampling identity differs from DEV")
    hardware = _capture_hardware(args.hardware_profile) if args.backend == "hf" else None
    specs, spec_meta = _make_specs(args, items, out_dir / "test" / "work")
    registry_profile = resolve_test_attempt_registry(prepare=True)
    cell_summaries: Dict[str, object] = {}
    for cell in CELLS:
        cell_out = _cell_dir(out_dir / "test", cell)
        if (cell_out / "TEST_STARTED.json").exists():
            raise ValueError(f"TEST already started for {cell.cell_id}")
        frozen, dev_sha = _load_dev_selection(out_dir, cell)
        if frozen.get("cell", {}).get("cell_id") != cell.cell_id:
            raise ValueError(f"DEV selection cell mismatch for {cell.cell_id}")
        if frozen.get("code_identity", {}).get("code_commit") != identity["code_commit"]:
            raise ValueError(f"code commit differs from sealed DEV for {cell.cell_id}")
        spec = specs[cell.cell_id]
        sealed_direction = frozen.get("direction") or {}
        if sealed_direction.get("path"):
            direction_path = Path(str(sealed_direction["path"]))
            if _sha256_file(direction_path) != sealed_direction.get("sha256"):
                raise ValueError(f"sealed direction hash mismatch for {cell.cell_id}")
            spec = adj.AxisAdjSpec(
                axis=spec.axis,
                items=spec.items,
                strong_prompts=spec.strong_prompts,
                neutral_prompt=spec.neutral_prompt,
                direction=np.load(direction_path),
                layer=spec.layer,
            )
        if spec.layer != cell.layer:
            raise ValueError(f"layer mismatch for {cell.cell_id}: {spec.layer} != {cell.layer}")
        dev_items, test_items = _dev_test_items(spec.items)
        if [str(item["id"]) for item in dev_items] != frozen["sampling_axis"]["dev_item_ids"]:
            raise ValueError(f"DEV item identity drift for {cell.cell_id}")
        if [str(item["id"]) for item in test_items] != frozen["sampling_axis"]["test_item_ids"]:
            raise ValueError(f"TEST item identity drift for {cell.cell_id}")

        collector = base.TranscriptCollector(cell_out / "work", cell.model_id, cell.method, args.backend)
        sampler = _sampler_factory(cell, backend=args.backend, collector=collector, batch_size=args.batch_size)
        marker = claim_test_attempt(
            cell=cell,
            code_identity=identity,
            dev_selection_sha256=dev_sha,
            out_dir=out_dir,
            profile=registry_profile,
        )
        _atomic_json(
            cell_out / "TEST_STARTED.json",
            {
                "protocol_id": PROTOCOL_ID,
                "experiment_id": f"{TEST_EXPERIMENT_ID}-{cell.cell_id}",
                "cell_id": cell.cell_id,
                "global_attempt_marker": str(marker),
                "registry_profile": registry_profile,
                "code_identity": identity,
            },
        )
        ckpt = base.TranscriptCheckpointStore(
            cell_out / "work" / "checkpoints",
            _config_fingerprint(cell, spec, "test"),
            seed=SEED,
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
                k=K_SAMPLES,
                bootstrap_b=BOOTSTRAP_B,
                ci_level=BONFERRONI_CI_LEVEL,
                delta=adj.DELTA,
                coherence_max_ratio=adj.COHERENCE_MAX_RATIO,
                seed=SEED,
                ctx=ctx,
            )
        finally:
            ckpt.close()
        tost_ci = adj.cluster_bootstrap_ci(
            result.per_item_diff,
            b=BOOTSTRAP_B,
            ci_level=TOST_CI_LEVEL,
            seed=SEED,
            cluster=True,
        )
        verdict = strict_verdict(result, tost_ci)
        report = adj.AdjudicationReport(
            axis_results=[result],
            axis_passes={cell.cell_id: bool(result.passed)},
            verdict=verdict,
            frozen_params=adj.frozen_params_dict(),
        )
        transcript_root = collector.write_all(cell_out / "work", report)
        payload = {
            "protocol_id": PROTOCOL_ID,
            "experiment_id": f"{TEST_EXPERIMENT_ID}-{cell.cell_id}",
            "phase": "TEST",
            "scientific_status": "PENDING_HOSTILE_RESULT_AUDIT",
            "valid_for_paper": False,
            "cell": asdict(cell),
            "code_identity": identity,
            "hardware": hardware,
            "sampling_axis": sampling["axes"][cell.axis],
            "dev_selection_sha256": dev_sha,
            "test_attempt_marker": str(marker),
            "direction": spec_meta.get("directions", {}).get(cell.cell_id),
            "result": result.to_row(),
            "tost": asdict(tost_ci),
            "strict_verdict": verdict,
            "achieved_mde": cell.planned_mde,
            "transcript_root": str(transcript_root),
            "config": {
                "k": K_SAMPLES,
                "bootstrap_b": BOOTSTRAP_B,
                "bonferroni_ci_level": BONFERRONI_CI_LEVEL,
                "tost_ci_level": TOST_CI_LEVEL,
                "sesoi": SESOI,
                "max_new_tokens": MAX_NEW_TOKENS,
                "temperature": TEMPERATURE,
                "seed": SEED,
                "alpha_grid": list(adj.ALPHA_GRID),
            },
        }
        result_path = cell_out / "sealed" / "powered_tost_A_result.json"
        _atomic_json(result_path, payload)
        _atomic_json(cell_out / "SEALED.json", {"result_sha256": _sha256_file(result_path)})
        cell_summaries[cell.cell_id] = {
            "strict_verdict": verdict,
            "n_test": result.n_test,
            "achieved_mde": cell.planned_mde,
            "dev_alpha": result.dev_selection.get("frozen_alpha"),
            "mean_diff": result.mean_diff,
            "ci_lo": result.ci_lo,
            "ci_hi": result.ci_hi,
            "tost_ci_lo": tost_ci.ci_lo,
            "tost_ci_hi": tost_ci.ci_hi,
            "coherence_ok": result.coherence_ok,
            "result_path": str(result_path),
            "result_sha256": _sha256_file(result_path),
        }
        print(
            f"[powered-tost-A] TEST sealed {cell.cell_id}: verdict={verdict} "
            f"Δ={result.mean_diff:+.4f} CI=[{result.ci_lo:+.4f},{result.ci_hi:+.4f}] "
            f"TOST=[{tost_ci.ci_lo:+.4f},{tost_ci.ci_hi:+.4f}] coherence={result.coherence_ok}",
            flush=True,
        )
    seal_payload = {
        "protocol_id": PROTOCOL_ID,
        "experiment_id": TEST_EXPERIMENT_ID,
        "phase": "TEST_SEALED",
        "code_identity": identity,
        "sampling": sampling,
        "cells": cell_summaries,
        "valid_for_paper": False,
    }
    _atomic_json(out_dir / "test" / "SEALED.json", seal_payload)
    return 0


def _copy_into_repo(args) -> int:
    source = Path(args.source_dir).resolve()
    dest = Path(args.repo_results_dir).resolve()
    if not source.exists():
        raise FileNotFoundError(source)
    if dest.exists():
        raise ValueError(f"destination already exists: {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    ignore = shutil.ignore_patterns(".powered_tost_activation_cache")
    shutil.copytree(source, dest, ignore=ignore)
    print(f"[powered-tost-A] copied raw bundle {source} -> {dest}", flush=True)
    return 0


def _write_sha_manifest(root: Path) -> Dict[str, object]:
    files = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            files.append({"path": rel, "bytes": path.stat().st_size, "sha256": _sha256_file(path)})
    manifest = {
        "protocol_id": PROTOCOL_ID,
        "root": str(root),
        "file_count": len(files),
        "total_bytes": sum(int(row["bytes"]) for row in files),
        "files": files,
    }
    _atomic_json(root / "SHA256_MANIFEST.json", manifest)
    return manifest


def _write_registry(root: Path, code_identity: Mapping[str, object]) -> Dict[str, object]:
    test_seal = root / "test" / "SEALED.json"
    cells = {}
    if test_seal.exists():
        cells = json.loads(test_seal.read_text(encoding="utf-8")).get("cells", {})
    record = {
        "experiments": [
            {
                "experiment_id": TEST_EXPERIMENT_ID,
                "parent": "c2b-resolution-refinement-20260812",
                "hypothesis_id": "H2-powered-equivalence",
                "claim_ids": ["C2b"],
                "type": "confirmatory-protocol-pending-audit",
                "status": "done" if cells else "partial",
                "protocol_id": PROTOCOL_ID,
                "code_commit": code_identity.get("code_commit"),
                "dirty_tree": code_identity.get("dirty_tree"),
                "seed": SEED,
                "hardware": "nvidia-a800-80gb",
                "valid_for_paper": False,
                "validation_notes": "PENDING_HOSTILE_RESULT_AUDIT; do not fold until Manager/human gate.",
                "summary_metrics": cells,
                "artifacts": [str(root.as_posix())],
            }
        ]
    }
    try:
        import yaml  # noqa: PLC0415

        path = root / "experiment-registry.yaml"
        path.write_text(yaml.safe_dump(record, sort_keys=False), encoding="utf-8")
    except Exception:
        _atomic_json(root / "experiment-registry.yaml.json", record)
    return record


def _manifest(args) -> int:
    root = Path(args.repo_results_dir).resolve()
    identity = _git_identity(args.expected_code_commit, False)
    registry = _write_registry(root, identity)
    manifest = _write_sha_manifest(root)
    print(
        f"[powered-tost-A] manifest files={manifest['file_count']} bytes={manifest['total_bytes']} "
        f"registry_status={registry['experiments'][0]['status']}",
        flush=True,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=["preflight", "dev", "test", "copy-into-repo", "manifest"], required=True)
    parser.add_argument("--backend", choices=["synthetic", "hf"], default="hf")
    parser.add_argument("--hardware-profile", default="nvidia-a800-80gb")
    parser.add_argument("--out-dir")
    parser.add_argument("--source-dir")
    parser.add_argument("--repo-results-dir", default=str(_REPO / "results" / "powered_tost_A_20260813"))
    parser.add_argument("--expected-code-commit")
    parser.add_argument("--hf-home")
    parser.add_argument("--venv")
    parser.add_argument("--batch-size", type=int, default=32)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.phase in {"preflight", "dev", "test"} and not args.out_dir:
        raise SystemExit("--out-dir is required for preflight/dev/test")
    if args.backend == "hf" and args.phase in {"preflight", "dev", "test"} and not args.expected_code_commit:
        raise SystemExit("--expected-code-commit is required for HF phases")
    if args.phase == "preflight":
        return _preflight(args)
    if args.phase == "dev":
        return _dev(args)
    if args.phase == "test":
        return _test(args)
    if args.phase == "copy-into-repo":
        if not args.source_dir:
            raise SystemExit("--source-dir is required for copy-into-repo")
        return _copy_into_repo(args)
    return _manifest(args)


if __name__ == "__main__":
    raise SystemExit(main())
