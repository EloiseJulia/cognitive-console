"""Run the preregistered prompt-plus-steer composition experiment.

The real run is split into two commands:

1. DEV selects the bounded prompt, steer alpha, and power-qualified TEST N.
2. TEST consumes the sealed DEV artifact and an external one-use authorization.

Synthetic DEV/TEST is available for CPU-only pipeline validation. Synthetic
artifacts are always invalid for paper claims.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import io
import json
import math
import os
import platform
import shutil
import subprocess
import sys
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cognitive_console.eval import c2b_tasks
from cognitive_console.eval import scorers as c2b_scorers
from cognitive_console.experiments import adjudicate_c2b as c2
from cognitive_console.experiments import prompt_steer_composition as comp
from cognitive_console.lineage import git_commit, new_experiment_id, utcnow
from cognitive_console.manifest import ArtifactManifest, write_manifest
from cognitive_console.ops.disk_guard import DiskBudgetError, check_disk_budget
from cognitive_console.registry import ExperimentRecord, ExperimentRegistry
from cognitive_console.steering.generate import (
    GenerationResult,
    SteerConfig,
    SteeredHFBackend,
    SyntheticC2bTaskBackend,
)

from scripts import run_c1_facade as c1
from scripts import run_c2b_adjudication as base
from scripts import run_gpu_phase0 as p0

DEFAULT_OUT_DIR = _REPO / "results" / "E-0017-prompt-steer-composition"
MAX_NEW_TOKENS = 64
BATCH_SIZE = 16
TEMPERATURE = 0.7
N_EXTRACTION = 28
N_STRONG = 16
DISK_BUDGET_GB = comp.FROZEN_DISK_BUDGET_GB
DISK_CEILING_GB = comp.FROZEN_DISK_CEILING_GB
STALL_TIMEOUT_SECONDS = comp.FROZEN_STALL_TIMEOUT_SECONDS
GENERATION_RETRY_BUDGET = comp.FROZEN_RETRY_BUDGET
MAX_PHYSICAL_GENERATION_MULTIPLIER = GENERATION_RETRY_BUDGET + 1
DEV_ATTEMPT = "attempt-0001"
TEST_ATTEMPT = "attempt-0001"
IDENTITY_FILES = (
    "scripts/run_prompt_steer_composition.py",
    "src/cognitive_console/experiments/prompt_steer_composition.py",
    "src/cognitive_console/experiments/adjudicate_c2b.py",
    "scripts/run_c2b_adjudication.py",
    "src/cognitive_console/eval/c2b_tasks.py",
    "src/cognitive_console/eval/scorers.py",
    "scripts/run_c1_facade.py",
    "scripts/run_gpu_phase0.py",
    "src/cognitive_console/activations/provider.py",
    "src/cognitive_console/steering/generate.py",
    "docs/research/2026-08-11-prereg-prompt-steer-composition-FROZEN.md",
)
AUTODL_HF_HOME = Path("/root/autodl-tmp/hf")
AUTODL_OUTPUT_ROOT = Path("/root/autodl-tmp")
AUTODL_REQUIRED_PYTHON = (3, 12)
AUTODL_REQUIRED_PYTHON_EXECUTABLE = Path("/root/miniconda3/bin/python")
AUTODL_REQUIRED_TORCH = "2.8.0"
AUTODL_REQUIRED_CUDA = "12.8"
AUTODL_REQUIRED_TRANSFORMERS = "4.44.2"


@dataclass(frozen=True)
class HardwareProfile:
    profile_id: str
    accepted_name_fragments: tuple[str, ...]
    min_total_vram_gib: float
    max_total_vram_gib: Optional[float]
    min_free_before_load_gib: float
    min_free_after_load_gib: float
    disk_budget_gb: float
    disk_ceiling_gb: float
    filesystem_free_reserve_gib: float
    required_visible_selector: Optional[str] = None
    required_physical_gpu_count: Optional[int] = None
    required_hf_home: Optional[Path] = None
    required_output_root: Optional[Path] = None
    required_python: Optional[tuple[int, int]] = None
    required_python_executable: Optional[Path] = None
    required_torch: Optional[str] = None
    required_cuda: Optional[str] = None
    required_transformers: Optional[str] = None


AUTHORIZED_HARDWARE_PROFILES = (
    HardwareProfile(
        profile_id="nvidia-a800-80gb",
        accepted_name_fragments=("NVIDIA A800",),
        min_total_vram_gib=75.0,
        max_total_vram_gib=82.0,
        min_free_before_load_gib=40.0,
        min_free_after_load_gib=10.0,
        disk_budget_gb=DISK_BUDGET_GB,
        disk_ceiling_gb=DISK_CEILING_GB,
        filesystem_free_reserve_gib=5.0,
    ),
    HardwareProfile(
        profile_id="autodl-rtx4080-super-32gb",
        accepted_name_fragments=("NVIDIA GeForce RTX 4080 SUPER",),
        min_total_vram_gib=31.0,
        max_total_vram_gib=33.0,
        min_free_before_load_gib=24.0,
        min_free_after_load_gib=10.0,
        disk_budget_gb=40.0,
        disk_ceiling_gb=45.0,
        filesystem_free_reserve_gib=5.0,
        required_visible_selector="0",
        required_physical_gpu_count=1,
        required_hf_home=AUTODL_HF_HOME,
        required_output_root=AUTODL_OUTPUT_ROOT,
        required_python=AUTODL_REQUIRED_PYTHON,
        required_python_executable=AUTODL_REQUIRED_PYTHON_EXECUTABLE,
        required_torch=AUTODL_REQUIRED_TORCH,
        required_cuda=AUTODL_REQUIRED_CUDA,
        required_transformers=AUTODL_REQUIRED_TRANSFORMERS,
    ),
)


def _rel(path: Path) -> str:
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(_REPO)).replace("\\", "/")
    except ValueError:
        return str(resolved).replace("\\", "/")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def _sha256_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _atomic_json(path: Path, payload: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_name(path.name + ".new")
    pending.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    os.replace(pending, path)


def _git_dirty() -> bool:
    proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=_REPO,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return proc.returncode != 0 or bool(proc.stdout.strip())


def _env_hash() -> str:
    payload = {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
    }
    return comp.canonical_hash(payload)


def _source_hashes() -> Dict[str, str]:
    return {
        relative: _sha256_file(_REPO / relative)
        for relative in IDENTITY_FILES
    }


@dataclass(frozen=True)
class RunPaths:
    root: Path
    backend_root: Path
    dev_attempt: Path
    dev_sealed: Path
    test_attempt: Path
    test_sealed: Path
    registry: Path


def _run_paths(out_dir: Path, backend: str) -> RunPaths:
    root = Path(out_dir).resolve()
    backend_root = root / f"backend-{backend}"
    return RunPaths(
        root=root,
        backend_root=backend_root,
        dev_attempt=backend_root / "dev" / "attempts" / DEV_ATTEMPT,
        dev_sealed=backend_root / "dev" / "sealed",
        test_attempt=backend_root / "test" / "attempts" / TEST_ATTEMPT,
        test_sealed=backend_root / "test" / "sealed",
        registry=backend_root / "experiment-registry.yaml",
    )


def _seal_contents(path: Path) -> Dict[str, str]:
    return {
        str(file.relative_to(path)).replace("\\", "/"): _sha256_file(file)
        for file in sorted(path.rglob("*"))
        if file.is_file() and file.name != "SEAL.json"
    }


def _write_seal(path: Path, *, identity: Dict[str, object]) -> None:
    _atomic_json(
        path / "SEAL.json",
        {
            "sealed_at": utcnow(),
            "identity": identity,
            "files": _seal_contents(path),
        },
    )


def _verify_seal(path: Path) -> Dict:
    seal_path = path / "SEAL.json"
    if not seal_path.exists():
        raise RuntimeError(f"sealed directory lacks SEAL.json: {path}")
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    actual = _seal_contents(path)
    if actual != seal.get("files"):
        raise RuntimeError(f"sealed directory was modified: {path}")
    return seal


def _publish_sealed_directory(
    staging: Path,
    sealed: Path,
    *,
    identity: Dict[str, object],
) -> None:
    if sealed.exists():
        existing = _verify_seal(sealed)
        if existing.get("identity") != identity:
            raise RuntimeError(f"conflicting immutable sealed directory: {sealed}")
        shutil.rmtree(staging, ignore_errors=True)
        return
    _write_seal(staging, identity=identity)
    sealed.parent.mkdir(parents=True, exist_ok=True)
    os.replace(staging, sealed)


def _cache_layout(paths: RunPaths, hf_home: Optional[str]) -> Dict[str, str]:
    root = (
        Path(hf_home).resolve()
        if hf_home
        else (paths.backend_root / "cache" / "hf-home").resolve()
    )
    layout = {
        "hf_home": str(root),
        "hub_cache": str(root / "hub"),
        "datasets_cache": str(root / "datasets"),
        "transformers_cache": str(root / "transformers"),
        "activation_cache": str(root / "activations"),
    }
    for value in layout.values():
        Path(value).mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = layout["hf_home"]
    os.environ["HF_HUB_CACHE"] = layout["hub_cache"]
    os.environ["HUGGINGFACE_HUB_CACHE"] = layout["hub_cache"]
    os.environ["HF_DATASETS_CACHE"] = layout["datasets_cache"]
    os.environ["TRANSFORMERS_CACHE"] = layout["transformers_cache"]
    os.environ["COGNITIVE_CONSOLE_ACT_CACHE"] = layout["activation_cache"]
    return layout


def _guarded_growth_paths(
    paths: RunPaths,
    cache_layout: Dict[str, str],
    venv: Optional[str],
) -> List[str]:
    candidates = [
        paths.backend_root.resolve(),
        Path(cache_layout["hf_home"]).resolve(),
    ]
    resolved_venv = venv or os.environ.get("VIRTUAL_ENV")
    if resolved_venv:
        candidates.append(Path(resolved_venv).resolve())

    unique: List[Path] = []
    for candidate in candidates:
        if candidate not in unique:
            unique.append(candidate)
    guarded: List[Path] = []
    for candidate in unique:
        if any(
            candidate != other and candidate.is_relative_to(other)
            for other in unique
        ):
            continue
        guarded.append(candidate)
    return [str(path) for path in guarded]


def _gib(n_bytes: float) -> float:
    return float(n_bytes) / (1024.0 ** 3)


def _base_package_version(value: str) -> str:
    return str(value).split("+", 1)[0]


def _package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "not-installed"


def hardware_profile_identity(profile: HardwareProfile) -> Dict[str, object]:
    payload = asdict(profile)
    payload["accepted_name_fragments"] = list(
        profile.accepted_name_fragments
    )
    if profile.required_python is not None:
        payload["required_python"] = list(profile.required_python)
    for key in (
        "required_hf_home",
        "required_output_root",
        "required_python_executable",
    ):
        value = payload.get(key)
        if value is not None:
            payload[key] = str(value)
    return payload


def select_authorized_hardware_profile(
    device_name: str,
    total_vram_gib: float,
) -> HardwareProfile:
    matches = [
        profile
        for profile in AUTHORIZED_HARDWARE_PROFILES
        if any(
            fragment in str(device_name)
            for fragment in profile.accepted_name_fragments
        )
        and float(total_vram_gib) >= profile.min_total_vram_gib
        and (
            profile.max_total_vram_gib is None
            or float(total_vram_gib) <= profile.max_total_vram_gib
        )
    ]
    if len(matches) != 1:
        raise ValueError(
            "unauthorized GPU hardware profile: "
            f"name={device_name!r}, usable_total_vram_gib="
            f"{float(total_vram_gib):.3f}; accepted profiles are NVIDIA A800 "
            "80GB or owner-authorized NVIDIA GeForce RTX 4080 SUPER with "
            "at least 31.0 GiB torch-usable memory"
        )
    return matches[0]


def validate_torch_smi_total_memory(
    torch_total_gib: float,
    smi_total_gib: float,
) -> Dict[str, float]:
    torch_total = float(torch_total_gib)
    smi_total = float(smi_total_gib)
    if (
        not math.isfinite(torch_total)
        or not math.isfinite(smi_total)
        or torch_total <= 0.0
        or smi_total <= 0.0
    ):
        raise ValueError(
            "torch/nvidia-smi total-memory values must be finite and positive"
        )
    allowed_gap = max(0.75, 0.03 * smi_total)
    gap = smi_total - torch_total
    if torch_total > smi_total or gap > allowed_gap:
        raise ValueError(
            "torch/nvidia-smi total-memory mismatch: "
            f"torch={torch_total:.3f} GiB, nvidia-smi={smi_total:.3f} GiB, "
            f"allowed_gap={allowed_gap:.3f} GiB"
        )
    return {
        "torch_total_gib": torch_total,
        "nvidia_smi_total_gib": smi_total,
        "gap_gib": gap,
        "allowed_gap_gib": allowed_gap,
    }


def _parse_nvidia_smi_rows(raw: str) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for line in str(raw).splitlines():
        if not line.strip():
            continue
        parts = [part.strip() for part in line.split(",", 5)]
        if len(parts) != 6:
            raise ValueError(f"unexpected nvidia-smi row: {line!r}")
        rows.append(
            {
                "physical_index": int(parts[0]),
                "uuid": parts[1],
                "pci_bus_id": parts[2],
                "name": parts[3],
                "total_memory_mib": int(parts[4]),
                "free_memory_mib": int(parts[5]),
            }
        )
    if not rows:
        raise ValueError("nvidia-smi returned no GPU rows")
    return rows


def _query_nvidia_smi_rows() -> List[Dict[str, object]]:
    completed = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=index,uuid,pci.bus_id,name,memory.total,memory.free",
            "--format=csv,noheader,nounits",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return _parse_nvidia_smi_rows(completed.stdout)


def _single_visible_gpu_selector() -> str:
    raw = os.environ.get("CUDA_VISIBLE_DEVICES")
    if raw is None or not raw.strip():
        raise ValueError(
            "HF E-0017 requires CUDA_VISIBLE_DEVICES to bind one physical GPU"
        )
    selectors = [part.strip() for part in raw.split(",") if part.strip()]
    if len(selectors) != 1:
        raise ValueError(
            "HF E-0017 requires exactly one CUDA_VISIBLE_DEVICES selector"
        )
    selector = selectors[0]
    if selector.startswith("MIG-"):
        raise ValueError("MIG devices are not an authorized E-0017 profile")
    return selector


def _select_physical_gpu_row(
    rows: Sequence[Dict[str, object]],
    selector: str,
) -> Dict[str, object]:
    if selector.isdigit():
        matches = [
            row
            for row in rows
            if int(row["physical_index"]) == int(selector)
        ]
    else:
        matches = [row for row in rows if str(row["uuid"]) == selector]
    if len(matches) != 1:
        raise ValueError(
            "CUDA_VISIBLE_DEVICES selector did not bind one nvidia-smi "
            f"physical GPU: {selector!r}"
        )
    return dict(matches[0])


def _validate_profile_runtime(
    profile: HardwareProfile,
    *,
    torch_version: str,
    cuda_runtime: object,
) -> Dict[str, object]:
    transformers_version = _package_version("transformers")
    python_version = (sys.version_info.major, sys.version_info.minor)
    if profile.required_python and python_version != profile.required_python:
        raise ValueError(
            f"{profile.profile_id} requires Python "
            f"{profile.required_python[0]}.{profile.required_python[1]}, got "
            f"{python_version[0]}.{python_version[1]}"
        )
    if profile.required_python_executable is not None:
        expected = profile.required_python_executable.resolve(strict=False)
        actual = Path(sys.executable).resolve(strict=False)
        if actual != expected:
            raise ValueError(
                f"{profile.profile_id} requires Python executable {expected}, "
                f"got {actual}"
            )
    if (
        profile.required_torch
        and _base_package_version(torch_version) != profile.required_torch
    ):
        raise ValueError(
            f"{profile.profile_id} requires torch {profile.required_torch}, "
            f"got {torch_version}"
        )
    if profile.required_cuda and str(cuda_runtime) != profile.required_cuda:
        raise ValueError(
            f"{profile.profile_id} requires torch CUDA {profile.required_cuda}, "
            f"got {cuda_runtime}"
        )
    if (
        profile.required_transformers
        and transformers_version != profile.required_transformers
    ):
        raise ValueError(
            f"{profile.profile_id} requires transformers "
            f"{profile.required_transformers}, got {transformers_version}"
        )
    return {
        "python": platform.python_version(),
        "python_executable": str(Path(sys.executable).resolve(strict=False)),
        "torch": torch_version,
        "torch_cuda_runtime": cuda_runtime,
        "transformers": transformers_version,
    }


def configure_cuda_allocator_environment() -> str:
    key = "PYTORCH_CUDA_ALLOC_CONF"
    required = "expandable_segments:True"
    current = os.environ.get(key)
    if current and required not in current.replace(" ", ""):
        raise ValueError(
            f"{key} must include {required} for E-0017 memory-safe execution"
        )
    if not current:
        os.environ[key] = required
    return os.environ[key]


def capture_authorized_hardware_preflight(
) -> tuple[HardwareProfile, Dict[str, object]]:
    import torch

    if not torch.cuda.is_available():
        raise ValueError("HF E-0017 requires CUDA; CPU execution is not authorized")
    if torch.cuda.device_count() != 1:
        raise ValueError(
            "HF E-0017 requires exactly one logical CUDA device after binding"
        )
    selector = _single_visible_gpu_selector()
    smi_rows = _query_nvidia_smi_rows()
    physical = _select_physical_gpu_row(smi_rows, selector)
    torch.cuda.set_device(0)
    props = torch.cuda.get_device_properties(0)
    free_bytes, total_bytes = torch.cuda.mem_get_info(0)
    total_gib = _gib(total_bytes)
    free_gib = _gib(free_bytes)
    smi_total_gib = float(physical["total_memory_mib"]) / 1024.0
    if str(props.name) != str(physical["name"]):
        raise ValueError(
            "torch/nvidia-smi GPU-name mismatch: "
            f"torch={props.name!r}, nvidia-smi={physical['name']!r}"
        )
    memory_consistency = validate_torch_smi_total_memory(
        total_gib,
        smi_total_gib,
    )
    profile = select_authorized_hardware_profile(str(props.name), total_gib)
    if (
        profile.required_visible_selector is not None
        and selector != profile.required_visible_selector
    ):
        raise ValueError(
            f"{profile.profile_id} requires CUDA_VISIBLE_DEVICES="
            f"{profile.required_visible_selector}, got {selector!r}"
        )
    if (
        profile.required_physical_gpu_count is not None
        and len(smi_rows) != profile.required_physical_gpu_count
    ):
        raise ValueError(
            f"{profile.profile_id} requires exactly "
            f"{profile.required_physical_gpu_count} nvidia-smi GPU row, got "
            f"{len(smi_rows)}"
        )
    if free_gib < profile.min_free_before_load_gib:
        raise ValueError(
            f"{profile.profile_id} requires at least "
            f"{profile.min_free_before_load_gib:.1f} GiB free before model "
            f"load, got {free_gib:.3f} GiB"
        )
    runtime = _validate_profile_runtime(
        profile,
        torch_version=str(torch.__version__),
        cuda_runtime=getattr(torch.version, "cuda", None),
    )
    return profile, {
        "profile": hardware_profile_identity(profile),
        "cuda_visible_devices": selector,
        "logical_device": "cuda:0",
        "physical_gpu": {
            **physical,
            "torch_device_name": str(props.name),
            "torch_total_vram_gib": total_gib,
            "compute_capability": [int(props.major), int(props.minor)],
            "torch_nvidia_smi_memory_consistency": memory_consistency,
        },
        "runtime": runtime,
        "memory_observation": {
            "stage": "before_model_load",
            "free_gib": free_gib,
            "total_gib": total_gib,
            "required_free_gib": profile.min_free_before_load_gib,
        },
    }


def _validate_profile_paths(
    profile: HardwareProfile,
    paths: RunPaths,
    cache_layout: Dict[str, str],
) -> Dict[str, object]:
    hf_home = Path(cache_layout["hf_home"]).resolve(strict=False)
    if profile.required_hf_home is not None:
        required = profile.required_hf_home.resolve(strict=False)
        if hf_home != required:
            raise ValueError(
                f"{profile.profile_id} requires HF_HOME={required}, got {hf_home}"
            )
    out_dir = paths.root.resolve(strict=False)
    if profile.required_output_root is not None:
        output_root = profile.required_output_root.resolve(strict=False)
        if out_dir == output_root or not out_dir.is_relative_to(output_root):
            raise ValueError(
                f"{profile.profile_id} requires OUT_DIR below {output_root}"
            )
    if out_dir == hf_home or out_dir.is_relative_to(hf_home):
        raise ValueError("OUT_DIR must not be inside HF_HOME")
    for name, value in cache_layout.items():
        cache_path = Path(value).resolve(strict=False)
        if name != "hf_home" and not cache_path.is_relative_to(hf_home):
            raise ValueError(
                f"{name} points outside the authorized HF_HOME: {cache_path}"
            )
    return {
        "hf_home": str(hf_home),
        "out_dir": str(out_dir),
        "disk_budget_gb": profile.disk_budget_gb,
        "disk_ceiling_gb": profile.disk_ceiling_gb,
        "filesystem_free_reserve_gib": profile.filesystem_free_reserve_gib,
    }


def _nearest_existing_parent(path: Path) -> Path:
    cursor = Path(path)
    while not cursor.exists() and cursor != cursor.parent:
        cursor = cursor.parent
    if not cursor.exists():
        raise ValueError(f"no existing filesystem ancestor for {path}")
    return cursor


def check_profile_disk_guard(
    profile: HardwareProfile,
    guard_paths: Sequence[str],
    cache_layout: Dict[str, str],
    paths: RunPaths,
    *,
    stage: str,
) -> Dict[str, object]:
    usage = check_disk_budget(
        guard_paths,
        profile.disk_budget_gb,
        profile.disk_ceiling_gb,
        raise_on_over=True,
    )
    filesystem_rows = []
    checked_parents: set[Path] = set()
    for requested in (
        Path(cache_layout["hf_home"]).resolve(strict=False),
        paths.root.resolve(strict=False),
    ):
        parent = _nearest_existing_parent(requested).resolve(strict=False)
        if parent in checked_parents:
            continue
        checked_parents.add(parent)
        disk = shutil.disk_usage(parent)
        free_gib = _gib(disk.free)
        if free_gib < profile.filesystem_free_reserve_gib:
            raise ValueError(
                f"{profile.profile_id} filesystem free space {free_gib:.3f} "
                f"GiB is below the {stage} reserve "
                f"{profile.filesystem_free_reserve_gib:.1f} GiB"
            )
        filesystem_rows.append(
            {
                "path": str(parent),
                "free_gib": free_gib,
                "required_free_gib": profile.filesystem_free_reserve_gib,
            }
        )
    return {
        "stage": stage,
        "managed_usage": usage.to_dict(),
        "filesystems": filesystem_rows,
    }


def check_cuda_memory_headroom(
    profile: HardwareProfile,
    *,
    stage: str,
) -> Dict[str, object]:
    import torch

    free_bytes, total_bytes = torch.cuda.mem_get_info(0)
    free_gib = _gib(free_bytes)
    total_gib = _gib(total_bytes)
    if free_gib < profile.min_free_after_load_gib:
        raise ValueError(
            f"{profile.profile_id} CUDA free memory {free_gib:.3f} GiB is "
            f"below the post-load/run requirement "
            f"{profile.min_free_after_load_gib:.1f} GiB at {stage}"
        )
    return {
        "stage": stage,
        "free_gib": free_gib,
        "total_gib": total_gib,
        "required_free_gib": profile.min_free_after_load_gib,
        "allocated_gib": _gib(torch.cuda.memory_allocated(0)),
        "reserved_gib": _gib(torch.cuda.memory_reserved(0)),
        "max_allocated_gib": _gib(torch.cuda.max_memory_allocated(0)),
    }


def _prepare_hf_operational_preflight(
    paths: RunPaths,
    cache_layout: Dict[str, str],
    guard_paths: Sequence[str],
) -> tuple[HardwareProfile, Dict[str, object]]:
    allocator = configure_cuda_allocator_environment()
    profile, hardware = capture_authorized_hardware_preflight()
    cache = _validate_profile_paths(profile, paths, cache_layout)
    disk = check_profile_disk_guard(
        profile,
        guard_paths,
        cache_layout,
        paths,
        stage="before_model_load",
    )
    return profile, {
        **hardware,
        "cuda_allocator": {
            "environment_variable": "PYTORCH_CUDA_ALLOC_CONF",
            "value": allocator,
        },
        "cache": cache,
        "pre_load_disk_observation": disk,
    }


def _code_identity() -> Dict[str, object]:
    return {
        "commit": git_commit(str(_REPO)),
        "dirty": _git_dirty(),
        "source_hashes": _source_hashes(),
    }


def _assert_end_identity(
    start: Dict[str, object],
    *,
    config_fingerprint: str,
    expected_config_fingerprint: str,
) -> None:
    end = _code_identity()
    if end != start:
        raise RuntimeError("code/commit/source identity changed during the run")
    if config_fingerprint != expected_config_fingerprint:
        raise RuntimeError("effective config fingerprint changed during the run")


def selection_hash(payload: Dict) -> str:
    clean = dict(payload)
    clean.pop("selection_hash", None)
    clean.pop("started_at", None)
    clean.pop("completed_at", None)
    return comp.canonical_hash(clean)


def test_config_fingerprint(selection: Dict, bootstrap_b: int) -> str:
    sealed_bootstrap_b = int(selection["bootstrap_b"])
    if int(bootstrap_b) != sealed_bootstrap_b:
        raise ValueError(
            "TEST bootstrap_b differs from the DEV-sealed value: "
            f"{bootstrap_b} != {sealed_bootstrap_b}"
        )
    return comp.canonical_hash(
        {
            "protocol_id": comp.PROTOCOL_ID,
            "selection_hash": selection["selection_hash"],
            "phase": "TEST",
            "backend": selection["backend"],
            "bootstrap_b": sealed_bootstrap_b,
            "operational_limits": frozen_operational_limits(),
        }
    )


def frozen_operational_limits() -> Dict[str, object]:
    return {
        "disk_budget_gb": DISK_BUDGET_GB,
        "disk_ceiling_gb": DISK_CEILING_GB,
        "stall_timeout_seconds": STALL_TIMEOUT_SECONDS,
        "generation_retry_budget_per_backend_call": GENERATION_RETRY_BUDGET,
        "max_physical_generation_multiplier": MAX_PHYSICAL_GENERATION_MULTIPLIER,
    }


@dataclass
class PhysicalGenerationBudget:
    logical_limit: int
    retry_budget: int = GENERATION_RETRY_BUDGET
    state_path: Optional[Path] = None
    config_fingerprint: Optional[str] = None
    physical_generations: int = 0
    physical_backend_calls: int = 0
    retry_backend_calls: int = 0

    def __post_init__(self) -> None:
        if self.state_path is None or not Path(self.state_path).exists():
            return
        payload = json.loads(Path(self.state_path).read_text(encoding="utf-8"))
        expected = {
            "logical_generation_limit": int(self.logical_limit),
            "retry_budget_per_backend_call": int(self.retry_budget),
            "config_fingerprint": self.config_fingerprint,
        }
        for key, value in expected.items():
            if payload.get(key) != value:
                raise RuntimeError(
                    f"generation budget state identity mismatch for {key}"
                )
        self.physical_generations = int(payload.get("physical_generations", 0))
        self.physical_backend_calls = int(payload.get("physical_backend_calls", 0))
        self.retry_backend_calls = int(payload.get("retry_backend_calls", 0))

    @property
    def physical_limit(self) -> int:
        return int(self.logical_limit) * (int(self.retry_budget) + 1)

    def consume(self, rows: int, *, retry: bool) -> None:
        requested = int(rows)
        if requested < 1:
            raise ValueError("physical generation accounting requires rows >=1")
        if self.physical_generations + requested > self.physical_limit:
            raise RuntimeError(
                "frozen physical-generation cap exceeded: "
                f"{self.physical_generations}+{requested}>{self.physical_limit}"
            )
        self.physical_generations += requested
        self.physical_backend_calls += 1
        if retry:
            self.retry_backend_calls += 1
        if self.state_path is not None:
            _atomic_json(Path(self.state_path), self.to_dict())

    def to_dict(self) -> Dict[str, object]:
        return {
            "logical_generation_limit": int(self.logical_limit),
            "physical_generation_limit": int(self.physical_limit),
            "physical_generations": int(self.physical_generations),
            "physical_backend_calls": int(self.physical_backend_calls),
            "retry_backend_calls": int(self.retry_backend_calls),
            "retry_budget_per_backend_call": int(self.retry_budget),
            "config_fingerprint": self.config_fingerprint,
        }


class PersistentTranscriptCollector(base.TranscriptCollector):
    """Append aligned generation records so checkpoint resume preserves diagnostics."""

    def __init__(
        self,
        raw_path: Path,
        config_fingerprint: str,
        *,
        model: str,
        method: str,
        backend: str,
        fresh: bool,
    ):
        super().__init__(raw_path.parent, model, method, backend)
        self.raw_path = Path(raw_path)
        self.config_fingerprint = str(config_fingerprint)
        self.raw_path.parent.mkdir(parents=True, exist_ok=True)
        if fresh and self.raw_path.exists():
            self.raw_path.unlink()
        self._persisted: Dict[tuple, Dict] = {}
        if self.raw_path.exists():
            with open(self.raw_path, "r", encoding="utf-8") as fh:
                for line_number, line in enumerate(fh, start=1):
                    line = line.strip()
                    if not line:
                        continue
                    row = json.loads(line)
                    if row.get("config_fingerprint") != self.config_fingerprint:
                        continue
                    key = self._record_key(row)
                    existing = self._persisted.get(key)
                    if existing is not None and comp.canonical_hash(existing) != comp.canonical_hash(row):
                        raise RuntimeError(
                            "conflicting transcript identity at "
                            f"{self.raw_path}:{line_number}: {key}"
                        )
                    self._persisted[key] = row

    @staticmethod
    def _record_key(row: Dict) -> tuple:
        return (
            str(row.get("axis")),
            str(row.get("phase")),
            str(row.get("cell_key")),
            str(row.get("item_id")),
            int(row.get("sample_index", -1)),
        )

    def attach_cell(self, **kwargs) -> None:
        before = len(self._all_records)
        super().attach_cell(**kwargs)
        new_rows = self._all_records[before:]
        if not new_rows:
            return
        with open(self.raw_path, "a", encoding="utf-8") as fh:
            for row in new_rows:
                out = dict(row)
                out["config_fingerprint"] = self.config_fingerprint
                key = self._record_key(out)
                existing = self._persisted.get(key)
                if existing is not None:
                    if comp.canonical_hash(existing) != comp.canonical_hash(out):
                        raise RuntimeError(
                            f"conflicting transcript identity generated: {key}"
                        )
                    continue
                fh.write(json.dumps(out, ensure_ascii=False) + "\n")
                self._persisted[key] = out
            fh.flush()

    def records(self) -> List[Dict]:
        return list(self._persisted.values())

    def _parse_diag(
        self,
        axis: str,
        item: Dict,
        text: str,
        max_new_tokens: int,
        generation_metadata: Optional[Dict] = None,
    ) -> Dict:
        parsed = c2b_scorers.parse_axis_response(axis, item, text)
        return {
            "numbers_extracted": [
                str(n) for n in base._TRANSCRIPT_NUMBER_RE.findall(text or "")
            ],
            **parsed,
            "maybe_truncated": bool(
                (generation_metadata or {}).get("hit_max_new_tokens", False)
            ),
        }

    def diagnostics(
        self,
        axis: str,
        phase: str,
        cell_key: str,
        items: Sequence[Dict],
        k: int,
    ) -> Dict[str, object]:
        wanted = {str(row["id"]) for row in items}
        rows = [
            row
            for row in self.records()
            if str(row.get("axis")) == str(axis)
            and str(row.get("phase")) == str(phase)
            and str(row.get("cell_key")) == str(cell_key)
            and str(row.get("item_id")) in wanted
        ]
        expected = len(wanted) * int(k)
        expected_identity = {
            (item_id, sample_index)
            for item_id in wanted
            for sample_index in range(int(k))
        }
        observed_identity = {
            (str(row.get("item_id")), int(row.get("sample_index", -1)))
            for row in rows
        }
        missing_identity = expected_identity - observed_identity
        unexpected_identity = observed_identity - expected_identity
        observed = len(observed_identity & expected_identity)
        parse_ok = sum(
            1
            for row in rows
            if (str(row.get("item_id")), int(row.get("sample_index", -1)))
            in expected_identity
            and not bool((row.get("parse") or {}).get("axis_parse_failed"))
        )
        truncated = sum(
            1
            for row in rows
            if (str(row.get("item_id")), int(row.get("sample_index", -1)))
            in expected_identity
            and (
                bool((row.get("parse") or {}).get("maybe_truncated"))
                or bool(row.get("generation_hit_max_new_tokens"))
            )
        )
        missing_fields: Dict[str, int] = {}
        for row in rows:
            identity = (str(row.get("item_id")), int(row.get("sample_index", -1)))
            if identity not in expected_identity:
                continue
            for field in (row.get("parse") or {}).get("missing_fields", []):
                key = str(field)
                missing_fields[key] = missing_fields.get(key, 0) + 1
        return {
            "expected_records": expected,
            "observed_records": observed,
            "coverage": float(observed / expected) if expected else 0.0,
            "parse_rate": float(parse_ok / observed) if observed else 0.0,
            "truncation_rate": float(truncated / observed) if observed else 1.0,
            "identity_ok": not missing_identity and not unexpected_identity,
            "missing_identities": len(missing_identity),
            "unexpected_identities": len(unexpected_identity),
            "missing_field_counts": missing_fields,
        }


class CompositionTranscriptOutcomeSampler(base.TranscriptBackendOutcomeSampler):
    """Composition sampler with shared-pair RNG, strict scoring, and hard budgets."""

    def __init__(
        self,
        *args,
        generation_budget: PhysicalGenerationBudget,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._generation_budget = generation_budget

    def _call_seed(self, axis: str, item: Dict, alpha: float, j: int) -> int:
        key = f"{self.seed}|{axis}|{item.get('id')}|{j}"
        return int(hashlib.sha256(key.encode("utf-8")).hexdigest(), 16) % (2 ** 31)

    @staticmethod
    def _normalize_generation(value) -> tuple[str, Dict[str, object]]:
        if isinstance(value, GenerationResult):
            return value.text, asdict(value)
        return str(value), {
            "generated_token_ids": None,
            "generated_token_count": None,
            "finish_reason": "metadata_unavailable",
            "eos_token_ids": None,
            "contains_eos_token": None,
            "ended_with_eos": None,
            "hit_max_new_tokens": False,
        }

    def _call_with_retry(self, rows: int, invoke):
        last_error = None
        for attempt in range(GENERATION_RETRY_BUDGET + 1):
            self._generation_budget.consume(rows, retry=attempt > 0)
            try:
                return invoke()
            except (RuntimeError, OSError) as exc:
                last_error = exc
                if attempt >= GENERATION_RETRY_BUDGET:
                    raise
        raise RuntimeError(f"generation retry loop exhausted: {last_error}")

    def sample_batch(
        self,
        axis: str,
        items: List[Dict],
        instruction: str,
        alpha: float,
        k: int,
        direction: np.ndarray,
        layer: int,
    ):
        items = list(items)
        if not self.supports_batch:
            return [
                self.sample(axis, item, instruction, alpha, k, direction, layer)
                for item in items
            ]
        steer = SteerConfig(
            direction=direction,
            alpha=float(alpha),
            layer=int(layer),
        )
        prompts: List[str] = []
        seeds: List[int] = []
        owners: List[int] = []
        sample_indexes: List[int] = []
        for owner, item in enumerate(items):
            prompt = c2.format_task_input(axis, instruction, item)
            for sample_index in range(int(k)):
                prompts.append(prompt)
                seeds.append(self._call_seed(axis, item, alpha, sample_index))
                owners.append(owner)
                sample_indexes.append(sample_index)

        generated = self._call_with_retry(
            len(prompts),
            lambda: self.gen.generate_batch(
                prompts,
                steer,
                self.max_new_tokens,
                seeds=seeds,
                do_sample=self.do_sample,
                temperature=self.temperature,
                return_metadata=True,
            ),
        )
        if len(generated) != len(prompts):
            raise RuntimeError(
                f"backend returned {len(generated)} rows for {len(prompts)} prompts"
            )
        batches: List[c2.SampleBatch] = []
        for owner, item in enumerate(items):
            outcomes: List[float] = []
            degeneracies: List[float] = []
            for idx, row_owner in enumerate(owners):
                if row_owner != owner:
                    continue
                text, metadata = self._normalize_generation(generated[idx])
                outcome = c2b_scorers.score_strict_axis_response(axis, item, text)
                degeneracy = c2b_scorers.degeneracy_score(text)
                outcomes.append(outcome)
                degeneracies.append(degeneracy)
                self._collector.record_generation(
                    axis=axis,
                    item=item,
                    instruction=instruction,
                    alpha=float(alpha),
                    layer=int(layer),
                    sample_index=int(sample_indexes[idx]),
                    sample_seed=int(seeds[idx]),
                    prompt_text=str(prompts[idx]),
                    generation_text=text,
                    outcome=float(outcome),
                    degeneracy=float(degeneracy),
                    max_new_tokens=self.max_new_tokens,
                    generation_metadata=metadata,
                )
            batches.append(
                c2.SampleBatch(outcomes=outcomes, degeneracies=degeneracies)
            )
        return batches

    def sample(
        self,
        axis: str,
        item: Dict,
        instruction: str,
        alpha: float,
        k: int,
        direction: np.ndarray,
        layer: int,
    ):
        prompt = c2.format_task_input(axis, instruction, item)
        steer = SteerConfig(
            direction=direction,
            alpha=float(alpha),
            layer=int(layer),
        )
        outcomes: List[float] = []
        degeneracies: List[float] = []
        for sample_index in range(int(k)):
            sample_seed = self._call_seed(axis, item, alpha, sample_index)

            def invoke():
                try:
                    return self.gen.generate(
                        prompt,
                        steer,
                        self.max_new_tokens,
                        do_sample=self.do_sample,
                        temperature=self.temperature,
                        seed=sample_seed,
                        return_metadata=True,
                    )
                except TypeError as exc:
                    if "unexpected keyword argument" not in str(exc):
                        raise
                    return self.gen.generate(prompt, steer, self.max_new_tokens)

            generated = self._call_with_retry(1, invoke)
            text, metadata = self._normalize_generation(generated)
            outcome = c2b_scorers.score_strict_axis_response(axis, item, text)
            degeneracy = c2b_scorers.degeneracy_score(text)
            outcomes.append(outcome)
            degeneracies.append(degeneracy)
            self._collector.record_generation(
                axis=axis,
                item=item,
                instruction=instruction,
                alpha=float(alpha),
                layer=int(layer),
                sample_index=sample_index,
                sample_seed=sample_seed,
                prompt_text=prompt,
                generation_text=text,
                outcome=float(outcome),
                degeneracy=float(degeneracy),
                max_new_tokens=self.max_new_tokens,
                generation_metadata=metadata,
            )
        return c2.SampleBatch(outcomes=outcomes, degeneracies=degeneracies)


def _load_all_items(
    backend: str,
    *,
    dataset_cache_dir: Optional[Path] = None,
) -> Dict[str, List[Dict]]:
    use_fixture = backend == "synthetic"
    return {
        axis: list(
            c2b_tasks.load_c2b_task(
                axis,
                use_fixture=use_fixture,
                cache_dir=dataset_cache_dir,
            ).items
        )
        for axis in comp.AXES
    }


def _build_pools(
    backend: str,
    all_items: Dict[str, List[Dict]],
    *,
    smoke_dev_n: int,
    smoke_test_n: int,
) -> Dict[str, comp.PoolPlan]:
    if backend == "synthetic":
        return {
            axis: comp.build_smoke_pool(
                axis,
                all_items[axis],
                dev_n=smoke_dev_n,
                test_n=smoke_test_n,
                seed=comp.SEED,
            )
            for axis in comp.AXES
        }
    return {
        axis: comp.build_confirmatory_pool(axis, all_items[axis])
        for axis in comp.AXES
    }


def _save_directions(path: Path, specs: Sequence[c2.AxisAdjSpec]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    arrays = {
        **{f"{spec.axis}__direction": np.asarray(spec.direction) for spec in specs},
        **{
            f"{spec.axis}__layer": np.asarray([spec.layer], dtype=np.int64)
            for spec in specs
        },
    }
    pending = path.with_name(path.name + ".new")
    with zipfile.ZipFile(pending, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, array in sorted(arrays.items()):
            payload = io.BytesIO()
            np.lib.format.write_array(payload, np.asarray(array), allow_pickle=False)
            info = zipfile.ZipInfo(f"{name}.npy", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o600 << 16
            archive.writestr(info, payload.getvalue())
    os.replace(pending, path)
    return _sha256_file(path)


def _load_direction_specs(
    direction_path: Path,
    all_items: Dict[str, List[Dict]],
    selection: Dict,
) -> List[c2.AxisAdjSpec]:
    expected_hash = str(selection["direction_artifact"]["sha256"])
    actual_hash = _sha256_file(direction_path)
    if actual_hash != expected_hash:
        raise SystemExit(
            f"[composition] direction artifact hash mismatch: {actual_hash} != {expected_hash}"
        )
    data = np.load(direction_path)
    specs: List[c2.AxisAdjSpec] = []
    by_axis = {row["axis"]: row for row in selection["axes"]}
    neutral = c1.load_neutral_prompts()[0]
    all_by_axis = {
        axis: {str(row["id"]): row for row in rows}
        for axis, rows in all_items.items()
    }
    for axis in comp.AXES:
        row = by_axis[axis]
        if not bool(row["eligible"]):
            continue
        ids = list(row["selected_test_ids"])
        missing = [item_id for item_id in ids if item_id not in all_by_axis[axis]]
        if missing:
            raise SystemExit(f"[composition] {axis}: sealed TEST IDs missing: {missing[:3]}")
        specs.append(
            c2.AxisAdjSpec(
                axis=axis,
                items=[all_by_axis[axis][item_id] for item_id in ids],
                strong_prompts=[(row["best_prompt_id"], row["best_prompt_text"])],
                neutral_prompt=neutral,
                direction=np.asarray(data[f"{axis}__direction"]),
                layer=int(np.asarray(data[f"{axis}__layer"])[0]),
            )
        )
    return specs


def _hf_device_dtype() -> tuple[str, str]:
    if p0._pick_device() != "cuda" or p0._pick_dtype() != "float16":
        raise ValueError("HF E-0017 requires one CUDA device with fp16 loading")
    return "cuda:0", "float16"


def _build_dev_specs(
    backend: str,
    pools: Dict[str, comp.PoolPlan],
    attempt_dir: Path,
    cache_layout: Dict[str, str],
) -> tuple[List[c2.AxisAdjSpec], Dict, Optional[SteeredHFBackend]]:
    neutral = c1.load_neutral_prompts()[0]
    if backend == "synthetic":
        specs = [
            c2.AxisAdjSpec(
                axis=axis,
                items=pools[axis].dev_items + pools[axis].test_reservoir,
                strong_prompts=base.build_strong_prompts(axis, N_STRONG),
                neutral_prompt=neutral,
                direction=np.ones(8),
                layer=3,
            )
            for axis in comp.AXES
        ]
        return (
            specs,
            {
                "backend": "synthetic",
                "model": "synthetic-offline",
                "model_revision_resolved": None,
                "steering_method": comp.FROZEN_METHOD,
                "note": "CPU-only pipeline smoke; not scientific evidence",
            },
            None,
        )

    from cognitive_console.activations.provider import HFActivationProvider

    device, dtype = _hf_device_dtype()
    c1_out = attempt_dir / "direction_derivation" / "c1"
    provider = HFActivationProvider(
        comp.FROZEN_MODEL,
        device=device,
        dtype=dtype,
        cache_dir=cache_layout["activation_cache"],
        hf_cache_dir=cache_layout["hub_cache"],
        model_revision=comp.FROZEN_MODEL_REVISION,
    )
    c1_payload = c1.run(
        model=comp.FROZEN_MODEL,
        axes=list(comp.AXES),
        scan_step=2,
        n_extraction=N_EXTRACTION,
        seed=comp.SEED,
        n_null=2000,
        out_dir=c1_out,
        ram_floor_mb=0.0,
        device=device,
        dtype=dtype,
        activation_provider=provider,
    )
    resolved_revision = getattr(provider._config, "_commit_hash", None)
    if resolved_revision != comp.FROZEN_MODEL_REVISION:
        raise ValueError(
            "resolved model revision mismatch during direction derivation: "
            f"expected {comp.FROZEN_MODEL_REVISION}, got {resolved_revision}"
        )
    c1_by_axis = {row["axis"]: row for row in c1_payload["axes"]}
    specs = [
        c2.AxisAdjSpec(
            axis=axis,
            items=pools[axis].dev_items + pools[axis].test_reservoir,
            strong_prompts=base.build_strong_prompts(axis, N_STRONG),
            neutral_prompt=neutral,
            direction=p0._extract_direction(
                provider,
                axis,
                int(c1_by_axis[axis]["chosen_layer"]),
                N_EXTRACTION,
                comp.SEED,
            ),
            layer=int(c1_by_axis[axis]["chosen_layer"]),
        )
        for axis in comp.AXES
    ]
    model, tokenizer, config = provider.hf_handles()
    generation_backend = SteeredHFBackend(
        comp.FROZEN_MODEL,
        device=device,
        dtype=dtype,
        seed=comp.SEED,
        model=model,
        tokenizer=tokenizer,
        config=config,
    )
    meta = {
        "backend": "hf",
        "model": comp.FROZEN_MODEL,
        "model_revision_resolved": resolved_revision,
        "steering_method": comp.FROZEN_METHOD,
        "c1_layer_info": {
            axis: {
                "chosen_layer": int(c1_by_axis[axis]["chosen_layer"]),
                "stable_layer_found": c1_by_axis[axis].get("stable_layer_found"),
                "selection": "c1_chosen_layer",
                "sigma": 1.0,
            }
            for axis in comp.AXES
        },
        "alpha_scale_by_axis": {axis: 1.0 for axis in comp.AXES},
    }
    return specs, meta, generation_backend


def _synthetic_factory(
    all_items: Dict[str, List[Dict]],
    collector: PersistentTranscriptCollector,
    generation_budget: PhysicalGenerationBudget,
):
    def factory(axis: str):
        backend = SyntheticC2bTaskBackend(
            axis,
            all_items[axis],
            prompt_gain=0.4,
            alpha_gain=0.1,
            threshold=0.5,
        )
        return CompositionTranscriptOutcomeSampler(
            backend,
            do_sample=False,
            seed=comp.SEED,
            batch_size=BATCH_SIZE,
            transcript_collector=collector,
            generation_budget=generation_budget,
        )

    return factory


def _load_pinned_hf_backend(
    activation_cache_dir: Path,
    hf_cache_dir: Path,
) -> tuple[SteeredHFBackend, str]:
    from cognitive_console.activations.provider import HFActivationProvider

    device, dtype = _hf_device_dtype()
    provider = HFActivationProvider(
        comp.FROZEN_MODEL,
        device=device,
        dtype=dtype,
        cache_dir=str(activation_cache_dir),
        hf_cache_dir=str(hf_cache_dir),
        model_revision=comp.FROZEN_MODEL_REVISION,
    )
    model, tokenizer, config = provider.hf_handles()
    backend = SteeredHFBackend(
        comp.FROZEN_MODEL,
        device=device,
        dtype=dtype,
        seed=comp.SEED,
        model=model,
        tokenizer=tokenizer,
        config=config,
    )
    resolved = getattr(backend._config, "_commit_hash", None)
    if resolved != comp.FROZEN_MODEL_REVISION:
        raise ValueError(
            "resolved model revision mismatch: "
            f"expected {comp.FROZEN_MODEL_REVISION}, got {resolved}"
        )
    return backend, str(resolved)


def _verify_hf_hook_generation_compatibility(
    backend: SteeredHFBackend,
) -> Dict[str, object]:
    direction = np.ones(backend.hidden_dim, dtype=np.float32)
    layer = max(1, backend.num_hidden_layers // 2)
    probe_batch_size = max(
        1,
        (BATCH_SIZE // comp.K_SAMPLES) * comp.K_SAMPLES,
    )
    results = backend.generate_batch(
        ["Reply with exactly: OK"] * probe_batch_size,
        SteerConfig(direction=direction, alpha=0.01, layer=layer),
        max_new_tokens=1,
        seeds=[comp.SEED + index for index in range(probe_batch_size)],
        do_sample=False,
        return_metadata=True,
    )
    if len(results) != probe_batch_size or not all(
        isinstance(result, GenerationResult) for result in results
    ):
        raise RuntimeError("transformers generation compatibility probe failed")
    return {
        "transformers_version": _package_version("transformers"),
        "generation_api": "model.generate",
        "hook_path": "decoder_block_forward_hook_additive_residual",
        "compatible_steering_methods": ["caa", "iti"],
        "shared_hook_contract": (
            "CAA and ITI use the same SteerConfig additive forward-hook path; "
            "ITI differs only in direction derivation/alpha scaling"
        ),
        "probe_batch_size": probe_batch_size,
        "frozen_sampler_batch_size": BATCH_SIZE,
        "k_samples": comp.K_SAMPLES,
        "probe_max_new_tokens": 1,
        "probe_layer": layer,
        "probe_finish_reason": results[0].finish_reason,
        "probe_generated_token_count": results[0].generated_token_count,
    }


def _hf_factory(
    collector: PersistentTranscriptCollector,
    *,
    generation_budget: PhysicalGenerationBudget,
    backend: Optional[SteeredHFBackend] = None,
    resolved_revision: Optional[str] = None,
    activation_cache_dir: Optional[Path] = None,
    hf_cache_dir: Optional[Path] = None,
):
    if backend is None:
        if activation_cache_dir is None or hf_cache_dir is None:
            raise ValueError(
                "activation_cache_dir and hf_cache_dir are required "
                "when loading the HF backend"
            )
        backend, resolved_revision = _load_pinned_hf_backend(
            activation_cache_dir,
            hf_cache_dir,
        )
    if resolved_revision != comp.FROZEN_MODEL_REVISION:
        raise ValueError(
            "HF sampler revision is not the frozen revision: "
            f"{resolved_revision!r}"
        )

    def factory(_axis: str):
        return CompositionTranscriptOutcomeSampler(
            backend,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=True,
            temperature=TEMPERATURE,
            seed=comp.SEED,
            batch_size=BATCH_SIZE,
            transcript_collector=collector,
            generation_budget=generation_budget,
        )

    return factory, str(resolved_revision)


def _base_identity(
    backend: str,
    pools: Dict[str, comp.PoolPlan],
    specs: Sequence[c2.AxisAdjSpec],
    cache_layout: Dict[str, str],
) -> Dict:
    by_axis = {spec.axis: spec for spec in specs}
    return {
        "protocol": comp.frozen_protocol_dict(),
        "backend": backend,
        "code_commit": git_commit(str(_REPO)),
        "source_hashes": _source_hashes(),
        "operational_limits": frozen_operational_limits(),
        "cache_layout": dict(cache_layout),
        "generation": {
            "max_new_tokens": MAX_NEW_TOKENS,
            "batch_size": BATCH_SIZE,
            "temperature": TEMPERATURE,
            "do_sample": backend == "hf",
            "seed": comp.SEED,
            "condition_shared_sample_rng": True,
        },
        "axes": {
            axis: {
                "pool": pools[axis].to_dict(),
                "layer": int(by_axis[axis].layer),
                "prompt_candidates": [
                    {"id": pid, "text": text}
                    for pid, text in by_axis[axis].strong_prompts
                ],
                "neutral_prompt": by_axis[axis].neutral_prompt,
            }
            for axis in comp.AXES
        },
    }


def _register(
    *,
    registry_path: Path,
    prefix: str,
    run_type: str,
    status: str,
    cfg_hash: str,
    backend: str,
    artifact: Optional[Path],
    started_at: str,
    dirty_tree_at_start: bool,
    summary: Dict,
    validation_notes: str,
    failure_reason: Optional[str] = None,
    exit_code: Optional[int] = None,
    scientific: bool = True,
    experiment_id: Optional[str] = None,
) -> str:
    registry = ExperimentRegistry(str(registry_path))
    for existing in registry.load():
        if (
            str(existing.get("experiment_id", "")).startswith(prefix + "-")
            and existing.get("config_hash") == cfg_hash
            and existing.get("status") == status
            and existing.get("failure_reason") == failure_reason
        ):
            return str(existing["experiment_id"])
    exp_id = experiment_id or new_experiment_id(registry, prefix, cfg_hash)
    record = ExperimentRecord(
        experiment_id=exp_id,
        hypothesis_id="H4" if scientific else None,
        claim_ids=["C2"] if scientific else [],
        type=run_type,
        status=status,
        code_commit=git_commit(str(_REPO)),
        dirty_tree=bool(dirty_tree_at_start),
        data_hash=summary.get("data_hash"),
        env_hash=_env_hash(),
        config_hash=cfg_hash,
        model=comp.FROZEN_MODEL if backend == "hf" else "synthetic-offline",
        dataset=(
            "fresh TEST outside original C2 first-N pool; "
            "original C2 DEV reused only on DEV"
            if scientific
            else "bundled synthetic fixtures; SMOKE_ONLY"
        ),
        seed=comp.SEED,
        hardware=(
            f"{p0._pick_device()}-{p0._pick_dtype()}"
            if backend == "hf"
            else "cpu-offline"
        ),
        started_at=started_at,
        ended_at=utcnow(),
        exit_code=0 if status == "done" else exit_code,
        summary_metrics=summary,
        artifacts=[_rel(artifact)] if artifact is not None else [],
        failure_reason=failure_reason,
        valid_for_paper=False,
        validation_notes=validation_notes,
    )
    registry.append(record)
    return exp_id


def _register_failure(**kwargs) -> None:
    try:
        _register(status="failed", exit_code=2, **kwargs)
    except Exception as exc:  # noqa: BLE001 - preserve the original run failure
        print(
            f"[composition] WARNING failed to append failure lineage: "
            f"{type(exc).__name__}: {exc}",
            flush=True,
        )


def _mirror_sealed_registry_record(
    registry_path: Path,
    sealed_dir: Path,
) -> str:
    record_path = sealed_dir / "experiment_record.json"
    payload = json.loads(record_path.read_text(encoding="utf-8"))
    record = ExperimentRecord(**payload)
    registry = ExperimentRegistry(str(registry_path))
    existing = registry.get(record.experiment_id)
    if existing is None:
        registry.append(record)
    elif comp.canonical_hash(existing) != comp.canonical_hash(
        record.to_ordered_dict()
    ):
        raise RuntimeError(
            f"registry record conflict for {record.experiment_id}"
        )
    return record.experiment_id


def write_authorization_template(path: Path, selection: Dict) -> None:
    payload = {
        "protocol_id": comp.PROTOCOL_ID,
        "selection_hash": selection["selection_hash"],
        "protocol_commit": selection["code_commit"],
        "bootstrap_b": int(selection["bootstrap_b"]),
        "authorization_id": "",
        "authorized_by": "",
        "authorized_at": "",
        "hostile_audit_verdict": "PENDING",
        "budget_status": "pending",
        "test_authorized": False,
        "max_test_starts": 1,
        "note": (
            "External hostile auditor/Manager must fill this file after audit. "
            "Do not authorize if DEV eligibility, lineage, power, or budget fails."
        ),
    }
    _atomic_json(path, payload)


def validate_test_authorization(path: Path, selection: Dict) -> Dict:
    if not path.exists():
        raise SystemExit(f"[composition] TEST authorization file not found: {path}")
    raw = path.read_bytes()
    auth = json.loads(raw.decode("utf-8-sig"))
    required_equal = {
        "protocol_id": comp.PROTOCOL_ID,
        "selection_hash": selection["selection_hash"],
        "protocol_commit": selection["code_commit"],
        "bootstrap_b": int(selection["bootstrap_b"]),
        "hostile_audit_verdict": "PASS",
        "budget_status": "approved",
        "test_authorized": True,
        "max_test_starts": 1,
    }
    for key, expected in required_equal.items():
        if auth.get(key) != expected:
            raise SystemExit(
                f"[composition] TEST authorization invalid: {key}="
                f"{auth.get(key)!r}, expected {expected!r}"
            )
    for key in ("authorization_id", "authorized_by", "authorized_at"):
        if not str(auth.get(key, "")).strip():
            raise SystemExit(f"[composition] TEST authorization missing {key}")
    auth["_validated_file_sha256"] = _sha256_bytes(raw)
    return auth


def _pid_is_alive(pid: object) -> bool:
    try:
        value = int(pid)
    except (TypeError, ValueError):
        return False
    if value <= 0:
        return False
    try:
        os.kill(value, 0)
    except OSError:
        return False
    return True


def _acquire_test_runtime_lock(out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    lock = out_dir / "test_authorization.run.lock"
    payload = {
        "host": platform.node(),
        "pid": os.getpid(),
        "acquired_at": utcnow(),
    }
    while True:
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            existing = json.loads(lock.read_text(encoding="utf-8"))
            same_host = existing.get("host") == platform.node()
            if same_host and _pid_is_alive(existing.get("pid")):
                raise SystemExit(
                    "[composition] authorized TEST runtime lock is already active"
                )
            if not same_host:
                raise SystemExit(
                    "[composition] cannot prove a cross-host TEST runtime lock is stale"
                )
            try:
                lock.unlink()
            except FileNotFoundError:
                pass
            continue
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
            fh.write("\n")
            fh.flush()
        return lock


def release_test_runtime_lock(lock: Path) -> None:
    try:
        payload = json.loads(lock.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return
    if (
        payload.get("host") == platform.node()
        and int(payload.get("pid", -1)) == os.getpid()
    ):
        lock.unlink()


def reserve_test_once(
    auth_path: Path,
    selection: Dict,
    backend_root: Path,
    checkpoint_fingerprint: str,
    authorization_file_sha256: Optional[str] = None,
) -> Path:
    sealed_backend_root = Path(str(selection["backend_root"])).resolve()
    if backend_root.resolve() != sealed_backend_root:
        raise SystemExit(
            "[composition] TEST backend directory differs from the DEV seal"
        )
    marker_root = backend_root / "test"
    marker_root.mkdir(parents=True, exist_ok=True)
    marker = marker_root / "test_authorization.used.json"
    requested = {
        "protocol_id": comp.PROTOCOL_ID,
        "selection_hash": selection["selection_hash"],
        "authorization_file_sha256": (
            str(authorization_file_sha256)
            if authorization_file_sha256 is not None
            else _sha256_file(auth_path)
        ),
        "out_dir": str(Path(str(selection["out_dir"])).resolve()),
        "backend_root": str(backend_root.resolve()),
        "checkpoint_fingerprint": str(checkpoint_fingerprint),
        "status": "running",
        "started_at": utcnow(),
        "completed_at": None,
        "host": platform.node(),
        "pid": os.getpid(),
    }
    try:
        fd = os.open(marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        existing = json.loads(marker.read_text(encoding="utf-8"))
        same_run = (
            existing.get("selection_hash") == requested["selection_hash"]
            and existing.get("backend_root") == requested["backend_root"]
            and existing.get("authorization_file_sha256")
            == requested["authorization_file_sha256"]
            and existing.get("checkpoint_fingerprint")
            == requested["checkpoint_fingerprint"]
        )
        if not same_run:
            raise SystemExit(
                "[composition] TEST authorization was already consumed by another run"
            )
        if existing.get("status") == "completed":
            raise SystemExit(
                "[composition] TEST already completed; TEST-once forbids another start"
            )
        if existing.get("status") == "running":
            same_host = existing.get("host") == platform.node()
            active_other_process = (
                same_host
                and _pid_is_alive(existing.get("pid"))
            )
            if active_other_process:
                raise SystemExit(
                    "[composition] authorized TEST is already running in another process"
                )
            if not same_host:
                raise SystemExit(
                    "[composition] cannot prove a cross-host TEST marker is stale"
                )
        if existing.get("status") not in {"running", "failed"}:
            raise SystemExit(
                "[composition] TEST marker has an invalid non-resumable status"
            )
        runtime_lock = _acquire_test_runtime_lock(marker_root)
        try:
            existing["status"] = "running"
            existing["resumed_at"] = utcnow()
            existing["host"] = platform.node()
            existing["pid"] = os.getpid()
            _atomic_json(marker, existing)
        except BaseException:
            release_test_runtime_lock(runtime_lock)
            raise
        return marker
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(requested, fh, indent=2)
        fh.write("\n")
        fh.flush()
    try:
        _acquire_test_runtime_lock(marker_root)
    except BaseException:
        try:
            current = json.loads(marker.read_text(encoding="utf-8"))
            if (
                current.get("host") == platform.node()
                and int(current.get("pid", -1)) == os.getpid()
            ):
                marker.unlink()
        except (FileNotFoundError, ValueError, json.JSONDecodeError):
            pass
        raise
    return marker


def update_test_marker(marker: Path, status: str) -> None:
    payload = json.loads(marker.read_text(encoding="utf-8"))
    payload["status"] = str(status)
    payload["completed_at"] = utcnow() if status == "completed" else None
    _atomic_json(marker, payload)


def _record_dev_finalization_failure(
    paths: RunPaths,
    *,
    selection_hash_value: Optional[str],
    config_fingerprint: Optional[str],
    exc: BaseException,
) -> Path:
    failure_path = paths.dev_attempt / "finalization_failure.json"
    _atomic_json(
        failure_path,
        {
            "phase": "DEV_FINALIZATION",
            "selection_hash": selection_hash_value,
            "config_fingerprint": config_fingerprint,
            "failure_reason": f"{type(exc).__name__}: {exc}",
            "recorded_at": utcnow(),
        },
    )
    return failure_path


def _register_recorded_dev_finalization_failure(
    paths: RunPaths,
    *,
    backend: str,
) -> None:
    failure_path = paths.dev_attempt / "finalization_failure.json"
    if not failure_path.exists():
        return
    payload = json.loads(failure_path.read_text(encoding="utf-8"))
    _register_failure(
        registry_path=paths.registry,
        prefix="e0017-composition-dev-finalization",
        run_type="diagnostic",
        cfg_hash=str(payload.get("config_fingerprint") or "unknown"),
        backend=backend,
        artifact=failure_path,
        started_at=str(payload.get("recorded_at") or utcnow()),
        dirty_tree_at_start=_git_dirty(),
        summary={
            "phase": "DEV_FINALIZATION",
            "selection_hash": payload.get("selection_hash"),
        },
        validation_notes=(
            "DEV seal was published but registry mirroring failed; the failure "
            "was preserved and the sealed record was repaired idempotently."
        ),
        failure_reason=str(payload.get("failure_reason") or "unknown"),
        scientific=backend == "hf",
    )


def _run_preflight(args) -> int:
    paths = _run_paths(Path(args.out_dir), args.backend)
    paths.backend_root.mkdir(parents=True, exist_ok=True)
    cache_layout = _cache_layout(paths, args.hf_home)
    identity = _code_identity()
    if identity["dirty"]:
        raise SystemExit(
            "[composition] HF preflight requires a clean committed tree"
        )
    guard_paths = _guarded_growth_paths(paths, cache_layout, args.venv)
    profile, operational = _prepare_hf_operational_preflight(
        paths,
        cache_layout,
        guard_paths,
    )
    backend, resolved_revision = _load_pinned_hf_backend(
        Path(cache_layout["activation_cache"]),
        Path(cache_layout["hub_cache"]),
    )
    compatibility = _verify_hf_hook_generation_compatibility(backend)
    operational["post_load_probe_memory_observation"] = (
        check_cuda_memory_headroom(
            profile,
            stage="after_model_load_and_one_token_hook_probe",
        )
    )
    operational["post_load_probe_disk_observation"] = (
        check_profile_disk_guard(
            profile,
            guard_paths,
            cache_layout,
            paths,
            stage="after_model_load_and_one_token_hook_probe",
        )
    )
    payload = {
        "protocol_id": comp.PROTOCOL_ID,
        "phase": "PREFLIGHT",
        "status": "PREFLIGHT_PASSED_DIAGNOSTIC_ONE_TOKEN_GENERATION",
        "scientific_status": "OPERATIONAL_ONLY_NOT_DEV_OR_TEST",
        "created_at": utcnow(),
        "code_identity": identity,
        "out_dir": str(paths.root),
        "backend_root": str(paths.backend_root),
        "model": comp.FROZEN_MODEL,
        "model_revision_expected": comp.FROZEN_MODEL_REVISION,
        "model_revision_resolved": resolved_revision,
        "device": backend.device,
        "dtype": backend.dtype,
        "runtime_batch_size": BATCH_SIZE,
        "operational_preflight": operational,
        "transformers_hook_generation_compatibility": compatibility,
        "generation_scope": (
            "one-token operational compatibility probe only; no C2 item, "
            "DEV selection, TEST item, estimand, or verdict was evaluated"
        ),
        "valid_for_paper": False,
    }
    output = paths.backend_root / "preflight" / "hardware_preflight.json"
    _atomic_json(output, payload)
    print(
        f"[composition] preflight passed: profile={profile.profile_id} "
        f"model={comp.FROZEN_MODEL} fp16; wrote {_rel(output)}",
        flush=True,
    )
    return 0


def _run_dev(args) -> int:
    paths = _run_paths(Path(args.out_dir), args.backend)
    paths.backend_root.mkdir(parents=True, exist_ok=True)
    cache_layout = _cache_layout(paths, args.hf_home)
    if paths.dev_sealed.exists():
        dev_seal = _verify_seal(paths.dev_sealed)
        selection_path = paths.dev_sealed / "dev_selection.json"
        selection = json.loads(selection_path.read_text(encoding="utf-8"))
        current_identity = _code_identity()
        current_guard_paths = _guarded_growth_paths(
            paths,
            cache_layout,
            args.venv,
        )
        if (
            selection.get("backend") != args.backend
            or Path(str(selection.get("out_dir"))).resolve() != paths.root
            or selection.get("code_commit") != current_identity["commit"]
            or selection.get("source_hashes") != current_identity["source_hashes"]
            or int(selection.get("bootstrap_b", -1)) != int(args.bootstrap_b)
            or selection.get("cache_layout") != cache_layout
            or selection.get("guarded_growth_paths") != current_guard_paths
            or (dev_seal.get("identity") or {}).get("selection_hash")
            != selection.get("selection_hash")
        ):
            raise SystemExit("[composition] immutable DEV seal identity mismatch")
        try:
            exp_id = _mirror_sealed_registry_record(
                paths.registry,
                paths.dev_sealed,
            )
            _register_recorded_dev_finalization_failure(
                paths,
                backend=args.backend,
            )
        except BaseException as exc:
            _record_dev_finalization_failure(
                paths,
                selection_hash_value=selection.get("selection_hash"),
                config_fingerprint=selection.get("effective_config_fingerprint"),
                exc=exc,
            )
            print(
                f"[composition] DEV registry finalization failed: "
                f"{type(exc).__name__}: {exc}",
                flush=True,
            )
            return 5
        print(
            f"[composition] DEV already sealed at {_rel(paths.dev_sealed)}; "
            f"registry={exp_id}; leaving it unchanged",
            flush=True,
        )
        return 0

    start_identity = _code_identity()
    dirty_tree_at_start = bool(start_identity["dirty"])
    if args.backend == "hf" and dirty_tree_at_start:
        raise SystemExit(
            "[composition] HF DEV requires a clean committed tree for protocol identity"
        )
    if args.backend == "hf" and args.fresh:
        raise SystemExit(
            "[composition] real DEV checkpoints are append-only; use a new out-dir "
            "instead of --fresh"
        )
    if args.fresh and paths.dev_attempt.exists():
        shutil.rmtree(paths.dev_attempt)
    paths.dev_attempt.mkdir(parents=True, exist_ok=True)
    started_at = utcnow()

    guard_paths = _guarded_growth_paths(paths, cache_layout, args.venv)
    hardware_profile: Optional[HardwareProfile] = None
    operational_preflight: Optional[Dict[str, object]] = None
    if args.backend == "hf":
        hardware_profile, operational_preflight = (
            _prepare_hf_operational_preflight(
                paths,
                cache_layout,
                guard_paths,
            )
        )
        pre_disk = operational_preflight["pre_load_disk_observation"]
        print(
            "[composition] disk pre-DEV: "
            f"{pre_disk['managed_usage']['message']}",
            flush=True,
        )

    all_items = _load_all_items(
        args.backend,
        dataset_cache_dir=Path(cache_layout["datasets_cache"]),
    )
    pools = _build_pools(
        args.backend,
        all_items,
        smoke_dev_n=args.smoke_dev_n,
        smoke_test_n=args.smoke_test_n,
    )
    request_identity = {
        "protocol": comp.frozen_protocol_dict(),
        "phase": "DEV",
        "backend": args.backend,
        "out_dir": str(paths.root),
        "backend_root": str(paths.backend_root),
        "code_identity": start_identity,
        "pool_plans": {axis: pools[axis].to_dict() for axis in comp.AXES},
        "generation": {
            "max_new_tokens": MAX_NEW_TOKENS,
            "batch_size": BATCH_SIZE,
            "temperature": TEMPERATURE,
            "seed": comp.SEED,
            "condition_shared_sample_rng": True,
        },
        "operational_limits": frozen_operational_limits(),
        "hardware_profile": (
            None
            if hardware_profile is None
            else hardware_profile_identity(hardware_profile)
        ),
        "cache_layout": cache_layout,
        "guarded_growth_paths": guard_paths,
        "bootstrap_b": int(args.bootstrap_b),
        "model_revision_expected": comp.FROZEN_MODEL_REVISION,
    }
    dev_request_hash = comp.canonical_hash(request_identity)
    try:
        specs, meta, shared_hf_backend = _build_dev_specs(
            args.backend,
            pools,
            paths.dev_attempt,
            cache_layout,
        )
        if args.backend == "hf":
            assert hardware_profile is not None
            assert operational_preflight is not None
            operational_preflight["post_load_memory_observation"] = (
                check_cuda_memory_headroom(
                    hardware_profile,
                    stage="after_DEV_model_load",
                )
            )
            operational_preflight["post_load_disk_observation"] = (
                check_profile_disk_guard(
                    hardware_profile,
                    guard_paths,
                    cache_layout,
                    paths,
                    stage="after_DEV_model_load",
                )
            )
            _atomic_json(
                paths.dev_attempt / "hardware_preflight.json",
                operational_preflight,
            )
    except (RuntimeError, MemoryError, ValueError, OSError) as exc:
        failure_reason = f"{type(exc).__name__}: {exc}"
        _register_failure(
            registry_path=paths.registry,
            prefix="e0017-composition-dev",
            run_type="diagnostic",
            cfg_hash=dev_request_hash,
            backend=args.backend,
            artifact=paths.dev_attempt / "direction_derivation",
            started_at=started_at,
            dirty_tree_at_start=dirty_tree_at_start,
            summary={"phase": "DEV", "scientific_status": "SMOKE_ONLY"
                     if args.backend == "synthetic" else "DEV_SETUP_FAILED"},
            validation_notes="DEV setup failed before selection; no TEST was accessed.",
            failure_reason=failure_reason,
            scientific=args.backend == "hf",
        )
        print(f"[composition] DEV direction/model setup failed: {failure_reason}")
        return 2

    attempt_direction = paths.dev_attempt / "directions.npz"
    direction_hash = _save_directions(attempt_direction, specs)
    identity = _base_identity(
        args.backend,
        pools,
        specs,
        cache_layout,
    )
    identity["direction_artifact_sha256"] = direction_hash
    identity["model_revision_expected"] = comp.FROZEN_MODEL_REVISION
    identity["hardware_profile"] = (
        None
        if hardware_profile is None
        else hardware_profile_identity(hardware_profile)
    )
    preliminary_hash = comp.canonical_hash(identity)
    collector = PersistentTranscriptCollector(
        paths.dev_attempt / "checkpoints" / "raw_generations.jsonl",
        preliminary_hash,
        model=str(meta.get("model", "synthetic-offline")),
        method=comp.FROZEN_METHOD,
        backend=args.backend,
        fresh=args.fresh,
    )
    planned = sum(
        len(pools[axis].dev_items)
        * comp.K_SAMPLES
        * (N_STRONG + 1 + 2 * len(comp.ALPHA_GRID))
        for axis in comp.AXES
    )
    generation_budget = PhysicalGenerationBudget(
        planned,
        state_path=paths.dev_attempt / "physical_generation_budget.json",
        config_fingerprint=preliminary_hash,
    )
    if args.backend == "synthetic":
        sampler_for_axis = _synthetic_factory(
            all_items,
            collector,
            generation_budget,
        )
        resolved_revision = None
    else:
        sampler_for_axis, resolved_revision = _hf_factory(
            collector,
            generation_budget=generation_budget,
            backend=shared_hf_backend,
            resolved_revision=meta.get("model_revision_resolved"),
        )

    progress = c2.ProgressTracker(planned)
    checkpoint = base.TranscriptCheckpointStore(
        paths.dev_attempt / "checkpoints",
        preliminary_hash,
        seed=comp.SEED,
        fresh=args.fresh,
        collector=collector,
    )
    ctx = c2.RunContext(checkpoint=checkpoint, progress=progress)
    watchdog = base.InactivityWatchdog(
        progress,
        STALL_TIMEOUT_SECONDS,
    ).start()
    by_spec = {spec.axis: spec for spec in specs}
    selections: List[comp.DevCompositionSelection] = []
    try:
        for axis in comp.AXES:
            selections.append(
                comp.select_composition_on_dev(
                    sampler_for_axis(axis),
                    by_spec[axis],
                    pools[axis],
                    diagnostics_fn=collector.diagnostics,
                    ctx=ctx,
                    smoke=args.backend == "synthetic",
                )
            )
    except (RuntimeError, MemoryError, ValueError, OSError) as exc:
        failure_reason = f"{type(exc).__name__}: {exc}"
        _register_failure(
            registry_path=paths.registry,
            prefix="e0017-composition-dev",
            run_type="diagnostic",
            cfg_hash=preliminary_hash,
            backend=args.backend,
            artifact=paths.dev_attempt / "checkpoints" / "raw_generations.jsonl",
            started_at=started_at,
            dirty_tree_at_start=dirty_tree_at_start,
            summary={
                "phase": "DEV",
                "generation_accounting": generation_budget.to_dict(),
            },
            validation_notes=(
                "DEV generation failed; append-only attempt checkpoints retained "
                "and TEST was not accessed."
            ),
            failure_reason=failure_reason,
            scientific=args.backend == "hf",
        )
        print(f"[composition] DEV generation failed: {failure_reason}")
        return 2
    finally:
        watchdog.stop()
        checkpoint.close()

    if args.backend == "hf":
        try:
            assert hardware_profile is not None
            assert operational_preflight is not None
            operational_preflight["post_dev_memory_observation"] = (
                check_cuda_memory_headroom(
                    hardware_profile,
                    stage="after_DEV_generation",
                )
            )
            operational_preflight["post_dev_disk_observation"] = (
                check_profile_disk_guard(
                    hardware_profile,
                    guard_paths,
                    cache_layout,
                    paths,
                    stage="after_DEV_generation",
                )
            )
            _atomic_json(
                paths.dev_attempt / "hardware_preflight.json",
                operational_preflight,
            )
            post_dev_disk = operational_preflight[
                "post_dev_disk_observation"
            ]
            print(
                "[composition] disk post-DEV: "
                f"{post_dev_disk['managed_usage']['message']}",
                flush=True,
            )
        except (DiskBudgetError, ValueError) as exc:
            failure_reason = f"post-DEV operational guard violation: {exc}"
            _register_failure(
                registry_path=paths.registry,
                prefix="e0017-composition-dev",
                run_type="diagnostic",
                cfg_hash=preliminary_hash,
                backend=args.backend,
                artifact=paths.dev_attempt / "checkpoints" / "raw_generations.jsonl",
                started_at=started_at,
                dirty_tree_at_start=dirty_tree_at_start,
                summary={"phase": "DEV"},
                validation_notes=(
                    "DEV completed generation but failed a frozen post-run "
                    "memory/disk guard; no DEV seal or TEST authorization "
                    "template was issued."
                ),
                failure_reason=failure_reason,
                scientific=True,
            )
            print(f"[composition] {failure_reason}", flush=True)
            return 4

    _assert_end_identity(
        start_identity,
        config_fingerprint=comp.canonical_hash(request_identity),
        expected_config_fingerprint=dev_request_hash,
    )
    staging = paths.dev_sealed.with_name("sealed.new")
    shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True)
    sealed_direction = staging / "directions.npz"
    shutil.copy2(attempt_direction, sealed_direction)
    payload = {
        "protocol_id": comp.PROTOCOL_ID,
        "phase": "DEV",
        "scientific_status": (
            "SMOKE_ONLY"
            if args.backend == "synthetic"
            else "DEV_SELECTION_ONLY_NO_TEST_SEEN"
        ),
        "backend": args.backend,
        "model": comp.FROZEN_MODEL if args.backend == "hf" else "synthetic-offline",
        "model_revision_expected": comp.FROZEN_MODEL_REVISION,
        "model_revision_resolved": resolved_revision,
        "method": comp.FROZEN_METHOD,
        "out_dir": str(paths.root),
        "backend_root": str(paths.backend_root),
        "dev_attempt_dir": str(paths.dev_attempt),
        "dev_sealed_dir": str(paths.dev_sealed),
        "code_commit": start_identity["commit"],
        "source_hashes": start_identity["source_hashes"],
        "dirty_tree_at_start": dirty_tree_at_start,
        "started_at": started_at,
        "completed_at": utcnow(),
        "preliminary_config_hash": preliminary_hash,
        "effective_config_fingerprint": dev_request_hash,
        "bootstrap_b": int(args.bootstrap_b),
        "direction_artifact": {
            "path": _rel(paths.dev_sealed / "directions.npz"),
            "sha256": direction_hash,
        },
        "pool_plans": {axis: pools[axis].to_dict() for axis in comp.AXES},
        "axes": [selection.to_dict() for selection in selections],
        "eligible_axes": [
            selection.axis for selection in selections if selection.eligible
        ],
        "test_seen": False,
        "test_authorized": False,
        "protocol": comp.frozen_protocol_dict(),
        "identity": identity,
        "operational_limits": frozen_operational_limits(),
        "hardware_profile": (
            None
            if hardware_profile is None
            else hardware_profile_identity(hardware_profile)
        ),
        "dev_operational_preflight": operational_preflight,
        "cache_layout": cache_layout,
        "guarded_growth_paths": guard_paths,
        "generation_accounting": generation_budget.to_dict(),
    }
    payload["selection_hash"] = selection_hash(payload)
    summary = {
        "data_hash": comp.canonical_hash(
            {axis: pools[axis].data_hash for axis in comp.AXES}
        ),
        "eligible_axes": payload["eligible_axes"],
        "selection_hash": payload["selection_hash"],
        "test_seen": False,
        "scientific_status": payload["scientific_status"],
        "generation_accounting": generation_budget.to_dict(),
    }
    try:
        registry = ExperimentRegistry(str(paths.registry))
        existing = next(
            (
                row
                for row in registry.load()
                if str(row.get("experiment_id", "")).startswith(
                    "e0017-composition-dev-"
                )
                and row.get("config_hash") == payload["selection_hash"]
                and row.get("status") == "done"
            ),
            None,
        )
        exp_id = (
            str(existing["experiment_id"])
            if existing is not None
            else new_experiment_id(
                registry,
                "e0017-composition-dev",
                payload["selection_hash"],
            )
        )
        record = ExperimentRecord(
            experiment_id=exp_id,
            hypothesis_id="H4" if args.backend == "hf" else None,
            claim_ids=["C2"] if args.backend == "hf" else [],
            type="diagnostic",
            status="done",
            code_commit=str(start_identity["commit"]),
            dirty_tree=dirty_tree_at_start,
            data_hash=summary["data_hash"],
            env_hash=_env_hash(),
            config_hash=payload["selection_hash"],
            model=(
                comp.FROZEN_MODEL
                if args.backend == "hf"
                else "synthetic-offline"
            ),
            dataset=(
                "fresh TEST outside original C2 first-N pool; "
                "original C2 DEV reused only on DEV"
                if args.backend == "hf"
                else "bundled synthetic fixtures; SMOKE_ONLY"
            ),
            seed=comp.SEED,
            hardware=(
                hardware_profile.profile_id
                if args.backend == "hf"
                else "cpu-offline"
            ),
            started_at=started_at,
            ended_at=utcnow(),
            exit_code=0,
            summary_metrics=summary,
            artifacts=[_rel(paths.dev_sealed / "dev_selection.json")],
            valid_for_paper=False,
            validation_notes=(
                "SMOKE_ONLY synthetic pipeline validation; no scientific verdict."
                if args.backend == "synthetic"
                else "DEV-only prompt/alpha/power selection; TEST was not generated."
            ),
        )
        _atomic_json(staging / "dev_selection.json", payload)
        write_authorization_template(
            staging / "test_authorization.template.json",
            payload,
        )
        _atomic_json(
            staging / "experiment_record.json",
            record.to_ordered_dict(),
        )
        _publish_sealed_directory(
            staging,
            paths.dev_sealed,
            identity={
                "selection_hash": payload["selection_hash"],
                "config_fingerprint": dev_request_hash,
                "code_commit": start_identity["commit"],
                "bootstrap_b": int(args.bootstrap_b),
                "experiment_id": exp_id,
            },
        )
        _mirror_sealed_registry_record(paths.registry, paths.dev_sealed)
    except BaseException as exc:
        _record_dev_finalization_failure(
            paths,
            selection_hash_value=payload.get("selection_hash"),
            config_fingerprint=dev_request_hash,
            exc=exc,
        )
        print(
            f"[composition] DEV finalization failed: "
            f"{type(exc).__name__}: {exc}",
            flush=True,
        )
        return 5
    print(
        f"[composition] DEV complete: eligible={payload['eligible_axes']} "
        f"selection={payload['selection_hash']} exp={exp_id}",
        flush=True,
    )
    print(f"[composition] sealed {_rel(paths.dev_sealed)}; TEST remains locked")
    return 0


def _run_test_impl(args) -> int:
    if args.fresh:
        raise SystemExit(
            "[composition] TEST checkpoints are append-only; --fresh is forbidden"
        )
    paths = _run_paths(Path(args.out_dir), args.backend)
    cache_layout = _cache_layout(paths, args.hf_home)
    if paths.test_sealed.exists():
        _verify_seal(paths.test_sealed)
        try:
            exp_id = _mirror_sealed_registry_record(
                paths.registry,
                paths.test_sealed,
            )
            consumption = json.loads(
                (
                    paths.test_sealed / "authorization_consumption.json"
                ).read_text(encoding="utf-8")
            )
            _atomic_json(
                paths.backend_root / "test" / "test_authorization.used.json",
                consumption,
            )
        except Exception as exc:
            failure_path = paths.test_attempt / "finalization_failure.json"
            _atomic_json(
                failure_path,
                {
                    "phase": "TEST_FINALIZATION",
                    "failure_reason": f"{type(exc).__name__}: {exc}",
                    "recorded_at": utcnow(),
                },
            )
            raise
        print(
            f"[composition] TEST already atomically finalized at "
            f"{_rel(paths.test_sealed)}; registry={exp_id}",
            flush=True,
        )
        return 0

    start_identity = _code_identity()
    dirty_tree_at_start = bool(start_identity["dirty"])
    dev_seal = _verify_seal(paths.dev_sealed)
    selection_path = (paths.dev_sealed / "dev_selection.json").resolve()
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    if selection_hash(selection) != selection.get("selection_hash"):
        raise SystemExit("[composition] DEV selection artifact identity is invalid")
    if (
        (dev_seal.get("identity") or {}).get("selection_hash")
        != selection.get("selection_hash")
    ):
        raise SystemExit(
            "[composition] DEV selection hash differs from the verified seal identity"
        )
    if selection.get("protocol_id") != comp.PROTOCOL_ID:
        raise SystemExit("[composition] selection protocol mismatch")
    if not selection.get("eligible_axes"):
        raise SystemExit("[composition] no DEV-eligible axis; TEST must not run")
    if args.backend != selection.get("backend"):
        raise SystemExit("[composition] TEST backend differs from sealed DEV backend")
    if paths.root != Path(str(selection.get("out_dir", ""))).resolve():
        raise SystemExit(
            "[composition] TEST out-dir differs from the DEV-sealed out-dir"
        )
    if paths.backend_root != Path(
        str(selection.get("backend_root", ""))
    ).resolve():
        raise SystemExit("[composition] TEST backend directory differs from DEV")
    if cache_layout != selection.get("cache_layout"):
        raise SystemExit("[composition] TEST cache layout differs from DEV")
    guard_paths = _guarded_growth_paths(paths, cache_layout, args.venv)
    if guard_paths != selection.get("guarded_growth_paths"):
        raise SystemExit("[composition] TEST guarded growth paths differ from DEV")
    if start_identity["commit"] != selection.get("code_commit"):
        raise SystemExit(
            "[composition] TEST HEAD must exactly equal the DEV commit"
        )
    if start_identity["source_hashes"] != selection.get("source_hashes"):
        raise SystemExit(
            "[composition] protocol/source hashes differ from DEV; rerun DEV"
        )
    if args.backend == "hf":
        if dirty_tree_at_start:
            raise SystemExit("[composition] HF TEST requires a clean committed tree")
    if args.backend == "hf" and args.bootstrap_b != comp.BOOTSTRAP_B:
        raise SystemExit(
            f"[composition] real TEST requires bootstrap B=={comp.BOOTSTRAP_B}"
        )
    if int(args.bootstrap_b) != int(selection.get("bootstrap_b", -1)):
        raise SystemExit(
            "[composition] TEST bootstrap B differs from the DEV-sealed value"
        )
    if not args.test_authorization_file:
        raise SystemExit("[composition] TEST requires --test-authorization-file")
    auth_path = Path(args.test_authorization_file).resolve()
    authorization = validate_test_authorization(auth_path, selection)

    hardware_profile: Optional[HardwareProfile] = None
    operational_preflight: Optional[Dict[str, object]] = None
    if args.backend == "hf":
        hardware_profile, operational_preflight = (
            _prepare_hf_operational_preflight(
                paths,
                cache_layout,
                guard_paths,
            )
        )
        if hardware_profile_identity(hardware_profile) != selection.get(
            "hardware_profile"
        ):
            raise SystemExit(
                "[composition] TEST hardware profile differs from sealed DEV"
            )
        pre_test_disk = operational_preflight[
            "pre_load_disk_observation"
        ]
        print(
            "[composition] disk pre-TEST: "
            f"{pre_test_disk['managed_usage']['message']}",
            flush=True,
        )

    all_items = _load_all_items(
        args.backend,
        dataset_cache_dir=Path(cache_layout["datasets_cache"]),
    )
    pools = _build_pools(
        args.backend,
        all_items,
        smoke_dev_n=args.smoke_dev_n,
        smoke_test_n=args.smoke_test_n,
    )
    for axis in comp.AXES:
        sealed_pool = selection["pool_plans"][axis]
        if pools[axis].to_dict() != sealed_pool:
            raise SystemExit(f"[composition] {axis}: reconstructed data pool identity changed")

    direction_path = (
        _REPO / selection["direction_artifact"]["path"]
        if not Path(selection["direction_artifact"]["path"]).is_absolute()
        else Path(selection["direction_artifact"]["path"])
    )
    specs = _load_direction_specs(direction_path, all_items, selection)
    test_fingerprint = test_config_fingerprint(selection, args.bootstrap_b)
    marker = reserve_test_once(
        auth_path,
        selection,
        paths.backend_root,
        test_fingerprint,
        authorization["_validated_file_sha256"],
    )
    runtime_lock = paths.backend_root / "test" / "test_authorization.run.lock"
    started_at = utcnow()
    results: List[comp.AxisCompositionResult] = []
    checkpoint = None
    watchdog = None
    logical_generation_limit = sum(
        len(spec.items) * comp.K_SAMPLES * 4 for spec in specs
    )
    generation_budget = PhysicalGenerationBudget(
        logical_generation_limit,
        state_path=paths.test_attempt / "physical_generation_budget.json",
        config_fingerprint=test_fingerprint,
    )
    try:
        collector = PersistentTranscriptCollector(
            paths.test_attempt / "checkpoints" / "raw_generations.jsonl",
            test_fingerprint,
            model=str(selection["model"]),
            method=comp.FROZEN_METHOD,
            backend=args.backend,
            fresh=False,
        )
        if args.backend == "synthetic":
            sampler_for_axis = _synthetic_factory(
                all_items,
                collector,
                generation_budget,
            )
        else:
            sampler_for_axis, resolved = _hf_factory(
                collector,
                generation_budget=generation_budget,
                activation_cache_dir=Path(cache_layout["activation_cache"]),
                hf_cache_dir=Path(cache_layout["hub_cache"]),
            )
            if resolved != selection.get("model_revision_resolved"):
                raise ValueError("TEST model revision differs from DEV")
            assert hardware_profile is not None
            assert operational_preflight is not None
            operational_preflight["post_load_memory_observation"] = (
                check_cuda_memory_headroom(
                    hardware_profile,
                    stage="after_TEST_model_load",
                )
            )
            operational_preflight["post_load_disk_observation"] = (
                check_profile_disk_guard(
                    hardware_profile,
                    guard_paths,
                    cache_layout,
                    paths,
                    stage="after_TEST_model_load",
                )
            )
            _atomic_json(
                paths.test_attempt / "hardware_preflight.json",
                operational_preflight,
            )

        progress = c2.ProgressTracker(logical_generation_limit)
        checkpoint = base.TranscriptCheckpointStore(
            paths.test_attempt / "checkpoints",
            test_fingerprint,
            seed=comp.SEED,
            fresh=False,
            collector=collector,
        )
        ctx = c2.RunContext(checkpoint=checkpoint, progress=progress)
        watchdog = base.InactivityWatchdog(
            progress,
            STALL_TIMEOUT_SECONDS,
        ).start()
        selection_by_axis = {
            row["axis"]: comp.DevCompositionSelection(**row)
            for row in selection["axes"]
        }
        for spec in specs:
            results.append(
                comp.run_test_axis(
                    sampler_for_axis(spec.axis),
                    spec,
                    selection_by_axis[spec.axis],
                    spec.items,
                    diagnostics_fn=collector.diagnostics,
                    bootstrap_b=args.bootstrap_b,
                    seed=comp.SEED,
                    ctx=ctx,
                )
            )
    except (RuntimeError, MemoryError, ValueError, OSError) as exc:
        update_test_marker(marker, "failed")
        failure_reason = f"{type(exc).__name__}: {exc}"
        _register_failure(
            registry_path=paths.registry,
            prefix="e0017-composition-test",
            run_type="confirmatory" if args.backend == "hf" else "diagnostic",
            cfg_hash=test_fingerprint,
            backend=args.backend,
            artifact=paths.test_attempt / "checkpoints" / "raw_generations.jsonl",
            started_at=started_at,
            dirty_tree_at_start=dirty_tree_at_start,
            summary={
                "data_hash": comp.canonical_hash(
                    {axis: pools[axis].data_hash for axis in comp.AXES}
                ),
                "selection_hash": selection["selection_hash"],
                "phase": "TEST",
                "generation_accounting": generation_budget.to_dict(),
            },
            validation_notes=(
                "Authorized TEST attempt failed; same-config checkpoint resume "
                "is allowed, but a second TEST identity is forbidden."
            ),
            failure_reason=failure_reason,
            scientific=args.backend == "hf",
        )
        print(f"[composition] TEST failed: {failure_reason}")
        print("[composition] same-config checkpoint resume is allowed; a second TEST start is not")
        return 2
    finally:
        if watchdog is not None:
            watchdog.stop()
        if checkpoint is not None:
            checkpoint.close()
        release_test_runtime_lock(runtime_lock)

    args._finalization_context = {
        "paths": paths,
        "marker": marker,
        "test_fingerprint": test_fingerprint,
        "backend": args.backend,
        "started_at": started_at,
        "dirty_tree_at_start": dirty_tree_at_start,
    }
    post_test_operational_violation = None
    if args.backend == "hf":
        try:
            assert hardware_profile is not None
            assert operational_preflight is not None
            operational_preflight["post_test_memory_observation"] = (
                check_cuda_memory_headroom(
                    hardware_profile,
                    stage="after_TEST_generation",
                )
            )
            operational_preflight["post_test_disk_observation"] = (
                check_profile_disk_guard(
                    hardware_profile,
                    guard_paths,
                    cache_layout,
                    paths,
                    stage="after_TEST_generation",
                )
            )
            _atomic_json(
                paths.test_attempt / "hardware_preflight.json",
                operational_preflight,
            )
            post_test_disk = operational_preflight[
                "post_test_disk_observation"
            ]
            print(
                "[composition] disk post-TEST: "
                f"{post_test_disk['managed_usage']['message']}",
                flush=True,
            )
        except (DiskBudgetError, ValueError) as exc:
            post_test_operational_violation = str(exc)
            print(
                f"[composition] post-TEST operational violation: {exc}",
                flush=True,
            )

    _assert_end_identity(
        start_identity,
        config_fingerprint=test_config_fingerprint(selection, args.bootstrap_b),
        expected_config_fingerprint=test_fingerprint,
    )
    report = comp.summarize_report(results)
    payload = report.to_dict()
    if args.backend == "synthetic":
        payload["overall_verdict"] = "SMOKE_ONLY"
        for axis_payload in payload["axes"]:
            axis_payload["verdict"] = "SMOKE_ONLY"
            axis_payload["primary_pass"] = False
    payload.update(
        {
            "protocol_id": comp.PROTOCOL_ID,
            "phase": "TEST",
            "backend": args.backend,
            "model": selection["model"],
            "model_revision": selection.get("model_revision_resolved"),
            "method": comp.FROZEN_METHOD,
            "selection_hash": selection["selection_hash"],
            "test_config_fingerprint": test_fingerprint,
            "authorization_id": authorization["authorization_id"],
            "authorization_file_sha256": authorization[
                "_validated_file_sha256"
            ],
            "started_at": started_at,
            "completed_at": utcnow(),
            "valid_for_paper": False,
            "validation_status": (
                "SMOKE_ONLY"
                if args.backend == "synthetic"
                else (
                    "BLOCKED_POST_TEST_OPERATIONAL_GUARD_VIOLATION"
                    if post_test_operational_violation
                    else "PENDING_HOSTILE_RESULT_AUDIT"
                )
            ),
            "post_test_operational_violation": (
                post_test_operational_violation
            ),
            "hardware_profile": (
                None
                if hardware_profile is None
                else hardware_profile_identity(hardware_profile)
            ),
            "test_operational_preflight": operational_preflight,
            "scientific_status": (
                "SMOKE_ONLY"
                if args.backend == "synthetic"
                else "PENDING_HOSTILE_RESULT_AUDIT"
            ),
            "operational_limits": frozen_operational_limits(),
            "cache_layout": cache_layout,
            "generation_accounting": generation_budget.to_dict(),
        }
    )
    summary = {
        "data_hash": comp.canonical_hash(
            {axis: pools[axis].data_hash for axis in comp.AXES}
        ),
        "overall_verdict": (
            "SMOKE_ONLY"
            if args.backend == "synthetic"
            else report.overall_verdict
        ),
        "selection_hash": selection["selection_hash"],
        "axis_verdicts": (
            {row.axis: "SMOKE_ONLY" for row in results}
            if args.backend == "synthetic"
            else {row.axis: row.verdict for row in results}
        ),
        "generation_accounting": generation_budget.to_dict(),
    }
    prefix = (
        "e0017-composition-test"
        if args.backend == "hf"
        else "e0017-composition-smoke"
    )
    registry = ExperimentRegistry(str(paths.registry))
    existing = next(
        (
            row
            for row in registry.load()
            if str(row.get("experiment_id", "")).startswith(prefix + "-")
            and row.get("config_hash") == test_fingerprint
            and row.get("status")
            == ("invalidated" if post_test_operational_violation else "done")
        ),
        None,
    )
    exp_id = (
        str(existing["experiment_id"])
        if existing is not None
        else new_experiment_id(registry, prefix, test_fingerprint)
    )
    payload["experiment_id"] = exp_id
    staging = paths.test_sealed.with_name("sealed.new")
    shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True)
    result_path = staging / "composition_test_results.json"
    _atomic_json(result_path, payload)
    record = ExperimentRecord(
        experiment_id=exp_id,
        hypothesis_id="H4" if args.backend == "hf" else None,
        claim_ids=["C2"] if args.backend == "hf" else [],
        type="confirmatory" if args.backend == "hf" else "diagnostic",
        status="invalidated" if post_test_operational_violation else "done",
        code_commit=str(start_identity["commit"]),
        dirty_tree=dirty_tree_at_start,
        data_hash=summary["data_hash"],
        env_hash=_env_hash(),
        config_hash=test_fingerprint,
        model=comp.FROZEN_MODEL if args.backend == "hf" else "synthetic-offline",
        dataset=(
            "fresh TEST outside original C2 first-N pool"
            if args.backend == "hf"
            else "bundled synthetic fixtures; SMOKE_ONLY"
        ),
        seed=comp.SEED,
        hardware=(
            hardware_profile.profile_id
            if args.backend == "hf"
            else "cpu-offline"
        ),
        started_at=started_at,
        ended_at=utcnow(),
        exit_code=4 if post_test_operational_violation else 0,
        summary_metrics=summary,
        artifacts=[_rel(paths.test_sealed / "composition_test_results.json")],
        valid_for_paper=False,
        validation_notes=(
            "SMOKE_ONLY synthetic pipeline validation; no scientific verdict, "
            "confirmatory registry entry, or C2 claim manifest."
            if args.backend == "synthetic"
            else (
                "Authorized TEST-once composition run; valid_for_paper remains "
                "false pending independent hostile result/statistics/lineage audit."
            )
        ),
    )
    _atomic_json(staging / "experiment_record.json", record.to_ordered_dict())
    if args.backend == "hf":
        manifest = ArtifactManifest(
            artifact_id="e0017-prompt-steer-composition-results",
            supports_claims=["C2"],
            source_experiments=[exp_id],
            aggregation_script="scripts/run_prompt_steer_composition.py",
            aggregation_commit=str(start_identity["commit"]),
            output_file=_rel(paths.test_sealed / "composition_test_results.json"),
            raw_data_hash=_sha256_file(result_path),
            manual_edits_allowed=False,
            last_verified=utcnow(),
            verdict=(
                "rejected" if post_test_operational_violation else "pending"
            ),
        )
        write_manifest(
            str(staging / "composition_results.manifest.yaml"),
            manifest,
        )
    completed_marker = json.loads(marker.read_text(encoding="utf-8"))
    completed_marker["status"] = "completed"
    completed_marker["completed_at"] = utcnow()
    _atomic_json(staging / "authorization_consumption.json", completed_marker)
    try:
        _publish_sealed_directory(
            staging,
            paths.test_sealed,
            identity={
                "selection_hash": selection["selection_hash"],
                "test_config_fingerprint": test_fingerprint,
                "authorization_file_sha256": authorization[
                    "_validated_file_sha256"
                ],
                "experiment_id": exp_id,
            },
        )
        _mirror_sealed_registry_record(paths.registry, paths.test_sealed)
        update_test_marker(marker, "completed")
    except BaseException as exc:
        update_test_marker(marker, "failed")
        failure_reason = f"{type(exc).__name__}: {exc}"
        _atomic_json(
            paths.test_attempt / "finalization_failure.json",
            {
                "phase": "TEST_FINALIZATION",
                "test_config_fingerprint": test_fingerprint,
                "failure_reason": failure_reason,
                "recorded_at": utcnow(),
            },
        )
        _register_failure(
            registry_path=paths.registry,
            prefix="e0017-composition-test-finalization",
            run_type="diagnostic",
            cfg_hash=test_fingerprint,
            backend=args.backend,
            artifact=paths.test_attempt / "finalization_failure.json",
            started_at=started_at,
            dirty_tree_at_start=dirty_tree_at_start,
            summary={"phase": "TEST_FINALIZATION"},
            validation_notes="Atomic TEST finalization failed and was recorded.",
            failure_reason=failure_reason,
            scientific=args.backend == "hf",
        )
        print(f"[composition] TEST finalization failed: {failure_reason}")
        return 5

    if post_test_operational_violation:
        return 4
    print(
        f"[composition] TEST complete: verdict={payload['overall_verdict']} "
        f"exp={exp_id}; valid_for_paper=false pending hostile audit",
        flush=True,
    )
    return 0


def _record_uncaught_finalization_failure(context: Dict, exc: BaseException) -> None:
    paths: RunPaths = context["paths"]
    marker: Path = context["marker"]
    failure_reason = f"{type(exc).__name__}: {exc}"
    try:
        update_test_marker(marker, "failed")
    except Exception:
        pass
    failure_path = paths.test_attempt / "finalization_failure.json"
    _atomic_json(
        failure_path,
        {
            "phase": "TEST_FINALIZATION",
            "test_config_fingerprint": context["test_fingerprint"],
            "failure_reason": failure_reason,
            "recorded_at": utcnow(),
        },
    )
    _register_failure(
        registry_path=paths.registry,
        prefix="e0017-composition-test-finalization",
        run_type="diagnostic",
        cfg_hash=context["test_fingerprint"],
        backend=context["backend"],
        artifact=failure_path,
        started_at=context["started_at"],
        dirty_tree_at_start=context["dirty_tree_at_start"],
        summary={"phase": "TEST_FINALIZATION"},
        validation_notes="Atomic TEST finalization failed and was recorded.",
        failure_reason=failure_reason,
        scientific=context["backend"] == "hf",
    )


def _run_test(args) -> int:
    try:
        return _run_test_impl(args)
    except BaseException as exc:
        context = getattr(args, "_finalization_context", None)
        if context is None:
            raise
        _record_uncaught_finalization_failure(context, exc)
        print(
            f"[composition] TEST finalization failed: "
            f"{type(exc).__name__}: {exc}",
            flush=True,
        )
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        return 5


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="E-0017 prompt-plus-steer composition (DEV-sealed, TEST-once)"
    )
    parser.add_argument("--phase", choices=["dev", "test"], required=True)
    parser.add_argument("--backend", choices=["synthetic", "hf"], default="synthetic")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--test-authorization-file", default=None)
    parser.add_argument("--bootstrap-b", type=int, default=comp.BOOTSTRAP_B)
    parser.add_argument("--fresh", action="store_true")
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help=(
            "Validate authorized GPU/runtime/cache/disk/fp16 model load and run "
            "one non-scientific token through the shared CAA/ITI hook path; "
            "never starts DEV or TEST."
        ),
    )
    parser.add_argument("--smoke-dev-n", type=int, default=4)
    parser.add_argument("--smoke-test-n", type=int, default=6)
    parser.add_argument("--hf-home", default=None)
    parser.add_argument("--venv", default=None)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.preflight_only and (
        args.backend != "hf" or args.phase != "dev"
    ):
        raise SystemExit(
            "--preflight-only requires --phase dev --backend hf"
        )
    if args.bootstrap_b < 1:
        raise SystemExit("--bootstrap-b must be >=1")
    if args.backend == "hf" and args.bootstrap_b != comp.BOOTSTRAP_B:
        raise SystemExit(
            f"real run requires --bootstrap-b == {comp.BOOTSTRAP_B}"
        )
    if args.backend == "synthetic":
        if args.smoke_dev_n < 2 or args.smoke_test_n < 2:
            raise SystemExit("synthetic smoke requires DEV and TEST N>=2")
    if args.preflight_only:
        return _run_preflight(args)
    if args.phase == "dev":
        return _run_dev(args)
    return _run_test(args)


if __name__ == "__main__":
    raise SystemExit(main())
