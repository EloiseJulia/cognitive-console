"""E-0017 deliberation 64/128/256-token sensitivity companion.

The frozen E-0006 0/12 result is never modified. This runner uses the
fingerprint-proven historical TEST index IDs on a revision-pinned reconstructed
GSM8K payload, plus each cell's prompt, alpha, layer, seeds, scorer, and batch
composition, while varying only max_new_tokens. Exact 64-token outcome
reproduction gates interpretation. Generated token IDs distinguish mechanical
token-cap stops from decoded-text heuristics.
"""

from __future__ import annotations

import argparse
import csv
import gc
import hashlib
import json
import math
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import time
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from statistics import NormalDist
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cognitive_console.eval import c2b_tasks, scorers
from cognitive_console.experiments import adjudicate_c2b as adj
from cognitive_console.lineage import utcnow
from cognitive_console.ops.disk_guard import check_disk_budget, default_guard_paths
from cognitive_console.steering.generate import GenerationTrace, SteerConfig
from cognitive_console.steering.extract import min_layer_for_depth
from cognitive_console.steering.iti import extract_iti, sigma_scaled_alpha
from scripts import run_c1_facade as c1
from scripts import run_gpu_phase0 as p0

EXPERIMENT_ID = "E-0017"
AXIS = "deliberation"
CAPS = (64, 128, 256)
CONDITIONS = ("prompt", "steer", "baseline")
FROZEN_CELL_KEYS = (
    "caa__qwen2.5-7b",
    "caa__llama3-8b",
    "iti__qwen2.5-7b",
    "iti__llama3-8b",
)
DEFAULT_FROZEN_ROOT = _REPO / "results" / "arm_full"
HOST_CONTROL_ROOT = (
    Path(r"C:\ProgramData\cognitive-console\host-control")
    if os.name == "nt"
    else Path("/var/lib/cognitive-console/host-control")
)
DEFAULT_OUT_DIR = Path.home() / ".cognitive-console" / "runs" / EXPERIMENT_ID
DEFAULT_SEED = 20260723
DEFAULT_TEMPERATURE = 0.7
DEFAULT_BATCH_SIZE = 16
DEFAULT_N_EXTRACTION = 28
DEFAULT_DISK_BUDGET_GB = 60.0
DEFAULT_DISK_CEILING_GB = 70.0
DEFAULT_MIN_FREE_GB = 5.0
DEFAULT_QWEN_MODEL = "Qwen/Qwen2.5-7B-Instruct"
DEFAULT_QWEN_REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"
DEFAULT_LLAMA_MODEL = "NousResearch/Meta-Llama-3-8B-Instruct"
DEFAULT_LLAMA_REVISION = "53346005fb0ef11d3b6a83b12c895cca40156b6c"
GSM8K_REVISION = "740312add88f781978c0658806c59bc2815b9866"
OWNER_IDENTITY = "EloiseJulia"
GPU_IDLE_MAX_MEMORY_MIB = 512
GPU_IDLE_MAX_UTILIZATION_PCT = 0
PREREG_PATH = (
    _REPO
    / "docs"
    / "research"
    / "2026-08-11-deliberation-token-sensitivity"
    / "prereg-e0017-DRAFT.md"
)
ITEM_IDENTITY_PATH = PREREG_PATH.parent / "e0006-item-identity.json"
CHECKPOINT_SCHEMA_VERSION = 1
TEST_ONCE_SCHEMA_VERSION = 1
AUTHORIZATION_SCHEMA_VERSION = 1
ATTEMPT_REGISTRY_SCHEMA_VERSION = 1
MODEL_IDENTITY_SCHEMA_VERSION = 1

MODEL_SPECS = {
    "qwen2.5-7b": {
        "repo_id": DEFAULT_QWEN_MODEL,
        "revision": DEFAULT_QWEN_REVISION,
    },
    "llama3-8b": {
        "repo_id": DEFAULT_LLAMA_MODEL,
        "revision": DEFAULT_LLAMA_REVISION,
    },
}

FROZEN_ARTIFACT_SHA256 = {
    "arm_matrix_summary.json": (
        "fd9140e8764da8b46e531644b9f885d363f718107c2e86d592ea4593eb75338e"
    ),
    "cell_caa__llama3-8b/c2b_adjudication_results.json": (
        "d301bacf70744406356fd2e1a597c01b8738c10d392a9901feae461bebfa0f42"
    ),
    "cell_caa__qwen2.5-7b/c2b_adjudication_results.json": (
        "33f242faf921f4a5de49b9620b6a5507415a157d21f9688dce6616d32cda1800"
    ),
    "cell_iti__llama3-8b/c2b_adjudication_results.json": (
        "ac9d18aa67a5e2afe9b37441fa08c008cfad139a557f323fa5052d8c38f85282"
    ),
    "cell_iti__qwen2.5-7b/c2b_adjudication_results.json": (
        "e168392f4c44d29467791883da122d27b470ce0770bc81c8b5d705119bc6647e"
    ),
}


@dataclass(frozen=True)
class FrozenCellConfig:
    cell_key: str
    method: str
    model_label: str
    model_id: str
    layer: int
    frozen_alpha: float
    best_prompt_id: str
    best_prompt_text: str
    neutral_prompt: str
    sigma: float
    source_result_file: str
    source_result_sha256: str
    source_config_fingerprint: str
    source_mean_diff: float
    source_ci_lo: float
    source_ci_hi: float
    source_passed: bool
    source_per_item_prompt: Tuple[float, ...]
    source_per_item_steer: Tuple[float, ...]


@dataclass(frozen=True)
class ModelArtifact:
    model_label: str
    repo_id: str
    revision: str
    snapshot_path: str
    identity: Dict[str, object]
    identity_sha256: str

    @property
    def canonical_id(self) -> str:
        return f"{self.repo_id}@{self.revision}"


def _rel(path: Path) -> str:
    path = Path(path).resolve()
    try:
        return str(path.relative_to(_REPO)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest()


def _canonical_json_hash(payload: object) -> str:
    return _sha256_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    )


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + ".partial")
    partial.write_text(text, encoding="utf-8")
    partial.replace(path)


def _write_json(path: Path, payload: Dict[str, object]) -> None:
    _write_text_atomic(
        path,
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
    )


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _contains_results_component(path: Path) -> bool:
    return any(part.casefold() == "results" for part in path.parts)


def _validate_external_control_path(
    path: Path,
    *,
    label: str,
    frozen_root: Path,
) -> Path:
    original = Path(path)
    if not original.is_absolute():
        raise SystemExit(f"E-0017 {label} must be an absolute path")
    resolved = original.resolve()
    if original != resolved:
        raise SystemExit(f"E-0017 {label} must already be canonical")
    frozen_root = frozen_root.resolve()
    if _is_relative_to(resolved, _REPO.resolve()):
        raise SystemExit(f"E-0017 {label} must be outside the repository")
    if _contains_results_component(resolved):
        raise SystemExit(
            f"E-0017 {label} may not be inside any directory named results"
        )
    if resolved == frozen_root or _is_relative_to(resolved, frozen_root):
        raise SystemExit(
            f"E-0017 {label} must not be the frozen E-0006 tree or its child"
        )
    return resolved


def _canonical_attempt_registry_path(source_commit: str) -> Path:
    commit = str(source_commit)
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("canonical attempt registry requires a full commit SHA")
    return (
        HOST_CONTROL_ROOT
        / "attempts"
        / EXPERIMENT_ID
        / f"{commit}.json"
    ).resolve()


def _validate_control_paths(
    *,
    out_dir: Path,
    registry_path: Path,
    frozen_root: Path,
) -> Tuple[Path, Path]:
    out = _validate_external_control_path(
        out_dir,
        label="output directory",
        frozen_root=frozen_root,
    )
    registry = _validate_external_control_path(
        registry_path,
        label="attempt registry",
        frozen_root=frozen_root,
    )
    if (
        out == registry
        or _is_relative_to(out, registry)
        or _is_relative_to(registry, out)
    ):
        raise SystemExit(
            "E-0017 output directory and attempt registry must be disjoint"
        )
    return out, registry


def _pinned_frozen_artifact_identity() -> Dict[str, object]:
    return {
        "root": "results/arm_full",
        "files": dict(FROZEN_ARTIFACT_SHA256),
    }


def _verify_pinned_frozen_root(path: Path) -> Tuple[Path, Dict[str, object]]:
    resolved = Path(path).resolve()
    expected_root = DEFAULT_FROZEN_ROOT.resolve()
    if resolved != expected_root:
        raise SystemExit(
            "E-0017 frozen root is pinned to in-repository results/arm_full; "
            "external or substitute roots are forbidden"
        )
    for relative_path, expected_sha256 in FROZEN_ARTIFACT_SHA256.items():
        artifact = resolved / Path(relative_path)
        if not artifact.is_file() or _sha256_file(artifact) != expected_sha256:
            raise SystemExit(
                f"E-0017 pinned frozen artifact mismatch: {relative_path}"
            )
    return resolved, _pinned_frozen_artifact_identity()


def _git_source_state(out_dir: Optional[Path] = None) -> Dict[str, object]:
    def _run(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", *args],
            cwd=str(_REPO),
            capture_output=True,
            check=False,
            timeout=30,
        )

    head = _run("rev-parse", "HEAD")
    if head.returncode != 0:
        raise SystemExit("E-0017 real run requires an identifiable git checkout")
    tracked = _run("diff", "--quiet", "HEAD", "--")
    if tracked.returncode not in {0, 1}:
        raise SystemExit("E-0017 could not inspect tracked source changes")
    untracked = _run("ls-files", "--others", "--exclude-standard", "-z")
    if untracked.returncode != 0:
        raise SystemExit("E-0017 could not inspect untracked source files")
    untracked_paths = [
        value.decode("utf-8", errors="surrogateescape")
        for value in untracked.stdout.split(b"\0")
        if value
    ]
    if out_dir is not None and _is_relative_to(out_dir.resolve(), _REPO.resolve()):
        excluded = out_dir.resolve().relative_to(_REPO.resolve()).as_posix()
        untracked_paths = [
            path
            for path in untracked_paths
            if path != excluded and not path.startswith(excluded + "/")
        ]
    return {
        "head": head.stdout.decode("ascii").strip(),
        "dirty": tracked.returncode == 1 or bool(untracked_paths),
        "untracked_paths": untracked_paths,
    }


def _parse_prereg_status(text: str) -> Tuple[str, str]:
    status_lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip().startswith("Status:")
    ]
    if len(status_lines) != 1:
        raise ValueError("preregistration must contain exactly one Status line")
    status_line = status_lines[0]
    canonical = {
        "Status: DRAFT / AUDIT-READY / NOT RUN": "DRAFT",
        "Status: FROZEN / AUDIT-READY / NOT RUN": "FROZEN",
    }
    status = canonical.get(status_line)
    if status is None:
        raise ValueError(
            "preregistration Status must equal one unambiguous canonical DRAFT "
            "or FROZEN line"
        )
    return status, status_line


def _preregistration_identity(*, require_frozen: bool) -> Dict[str, object]:
    text = PREREG_PATH.read_text(encoding="utf-8")
    try:
        status, status_line = _parse_prereg_status(text)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    frozen = status == "FROZEN"
    if require_frozen and not frozen:
        raise SystemExit(
            f"{_rel(PREREG_PATH)} is not marked FROZEN; real TEST generation is blocked"
        )
    return {
        "path": _rel(PREREG_PATH),
        "sha256": _sha256_text(text),
        "status": status,
        "status_line": status_line,
        "frozen": frozen,
    }


def _check_runtime_disk(
    *,
    out_dir: Path,
    hf_home: Optional[str],
    venv: Optional[str],
    budget_gb: float,
    ceiling_gb: float,
    min_free_gb: float,
    label: str,
) -> Dict[str, object]:
    guard_paths = [*default_guard_paths(hf_home, venv), str(out_dir)]
    usage = check_disk_budget(
        guard_paths,
        budget_gb=budget_gb,
        ceiling_gb=ceiling_gb,
        raise_on_over=True,
    )
    probe = out_dir if out_dir.exists() else out_dir.parent
    probe.mkdir(parents=True, exist_ok=True)
    free_gb = float(shutil.disk_usage(probe).free) / (1024.0**3)
    if free_gb < float(min_free_gb):
        raise RuntimeError(
            f"E-0017 disk free-space guard failed at {label}: "
            f"{free_gb:.2f} GiB < {float(min_free_gb):.2f} GiB"
        )
    result = {
        "label": label,
        "usage": usage.to_dict(),
        "filesystem_probe": str(probe),
        "free_gb": free_gb,
        "min_free_gb": float(min_free_gb),
        "checked_at": utcnow(),
    }
    print(f"[E-0017] disk {label}: {usage.message}; free={free_gb:.2f} GiB")
    return result


def _axis_rows(payload: Dict[str, object]) -> List[Dict[str, object]]:
    rows = payload.get("axes", payload.get("axis_results"))
    if not isinstance(rows, list):
        raise ValueError("frozen result lacks axes/axis_results")
    return rows


def _parse_cell_key(cell_key: str) -> Tuple[str, str]:
    method, model_label = str(cell_key).split("__", 1)
    if method not in {"caa", "iti"}:
        raise ValueError(f"unsupported method in cell {cell_key!r}")
    if model_label not in {"qwen2.5-7b", "llama3-8b"}:
        raise ValueError(f"unsupported model label in cell {cell_key!r}")
    return method, model_label


def load_frozen_cell_config(frozen_root: Path, cell_key: str) -> FrozenCellConfig:
    method, model_label = _parse_cell_key(cell_key)
    path = Path(frozen_root) / f"cell_{cell_key}" / "c2b_adjudication_results.json"
    if not path.exists():
        raise FileNotFoundError(f"missing frozen E-0006 cell artifact: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("backend") != "hf" or payload.get("steering_method") != method:
        raise ValueError(f"{path}: frozen backend/method mismatch")
    if bool(payload.get("use_fixture")):
        raise ValueError(f"{path}: frozen E-0006 must use real, not fixture, items")
    params = dict(payload.get("frozen_params") or {})
    if int(params.get("k_samples", -1)) != adj.K_SAMPLES:
        raise ValueError(f"{path}: frozen k mismatch")
    n_by_axis = dict(params.get("n_items_by_axis") or {})
    if int(n_by_axis.get(AXIS, -1)) != adj.N_ITEMS_BY_AXIS[AXIS]:
        raise ValueError(f"{path}: frozen deliberation N mismatch")
    rows = [row for row in _axis_rows(payload) if row.get("axis") == AXIS]
    if len(rows) != 1:
        raise ValueError(f"{path}: expected one deliberation row, got {len(rows)}")
    row = rows[0]
    dev = dict(row.get("dev_selection") or {})
    c1_info = dict((payload.get("c1_layer_info") or {}).get(AXIS) or {})
    sigma = float(
        c1_info.get(
            "sigma",
            (payload.get("alpha_scale_by_axis") or {}).get(AXIS, 1.0),
        )
    )
    prompt = tuple(float(value) for value in row.get("per_item_prompt", []))
    steer = tuple(float(value) for value in row.get("per_item_steer", []))
    if len(prompt) != 40 or len(steer) != 40:
        raise ValueError(f"{path}: expected 40 frozen TEST item outcomes per channel")
    return FrozenCellConfig(
        cell_key=cell_key,
        method=method,
        model_label=model_label,
        model_id=str(payload.get("model") or ""),
        layer=int(row["layer"]),
        frozen_alpha=float(dev["frozen_alpha"]),
        best_prompt_id=str(dev["best_prompt_id"]),
        best_prompt_text=str(dev["best_prompt_text"]),
        neutral_prompt=str(c1.load_neutral_prompts()[0]),
        sigma=sigma,
        source_result_file=_rel(path),
        source_result_sha256=_sha256_file(path),
        source_config_fingerprint=str(payload.get("config_fingerprint", "")),
        source_mean_diff=float(row["mean_diff"]),
        source_ci_lo=float(row["ci_lo"]),
        source_ci_hi=float(row["ci_hi"]),
        source_passed=bool(row["passed"]),
        source_per_item_prompt=prompt,
        source_per_item_steer=steer,
    )


def validate_frozen_arm_summary(
    frozen_root: Path, *, seed: int
) -> Dict[str, object]:
    path = Path(frozen_root) / "arm_matrix_summary.json"
    if not path.exists():
        raise FileNotFoundError(f"missing frozen arm summary: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if int(payload.get("seed", -1)) != int(seed):
        raise ValueError(f"{path}: frozen seed mismatch")
    cells = list(payload.get("cells", []))
    observed = {str(row.get("cell_key")) for row in cells}
    if observed != set(FROZEN_CELL_KEYS):
        raise ValueError(f"{path}: frozen cell set mismatch")
    axis_decisions = [
        bool(value)
        for row in cells
        for value in dict(row.get("axis_passes") or {}).values()
    ]
    if len(axis_decisions) != 12 or any(axis_decisions):
        raise ValueError(f"{path}: expected the frozen E-0006 0/12 decision")
    if any(int(row.get("axes_passed", -1)) != 0 for row in cells):
        raise ValueError(f"{path}: frozen cell axes_passed is not uniformly zero")
    return {
        "path": _rel(path),
        "sha256": _sha256_file(path),
        "seed": int(seed),
        "n_passed": 0,
        "n_decisions": 12,
        "arm_verdict": payload.get("arm_verdict"),
    }


def frozen_lineage_inventory(
    frozen_root: Path, configs: Dict[str, FrozenCellConfig], *, seed: int
) -> Dict[str, object]:
    return {
        "arm_summary": validate_frozen_arm_summary(frozen_root, seed=seed),
        "cells": {
            cell_key: {
                "result_file": cfg.source_result_file,
                "result_sha256": _sha256_file(_REPO / cfg.source_result_file),
                "config_fingerprint": cfg.source_config_fingerprint,
                "source_passed": cfg.source_passed,
            }
            for cell_key, cfg in configs.items()
        },
        "original_decision": "0/12",
        "original_result_immutable": True,
    }


def _recompute_historical_e0006_fingerprints(
    deliberation_pool_ids: Sequence[str],
) -> Dict[str, str]:
    axes = {
        "deliberation": {
            "item_ids": sorted(str(value) for value in deliberation_pool_ids),
            "strong_ids": c1.load_strongest_prompts("deliberation").ids[:16],
        },
        "skepticism": {
            "item_ids": [f"truthfulqa-mc1-{index:05d}" for index in range(60)],
            "strong_ids": c1.load_strongest_prompts("skepticism").ids[:16],
        },
        "uncertainty_awareness": {
            "item_ids": [f"triviaqa-{index:05d}" for index in range(80)],
            "strong_ids": c1.load_strongest_prompts(
                "uncertainty_awareness"
            ).ids[:16],
        },
    }
    results: Dict[str, str] = {}
    for method, model_label, model_path in (
        ("caa", "qwen2.5-7b", "/root/autodl-tmp/models/Qwen2.5-7B-Instruct"),
        ("caa", "llama3-8b", "/root/autodl-tmp/models/Meta-Llama-3-8B-Instruct"),
        ("iti", "qwen2.5-7b", "/root/autodl-tmp/models/Qwen2.5-7B-Instruct"),
        ("iti", "llama3-8b", "/root/autodl-tmp/models/Meta-Llama-3-8B-Instruct"),
    ):
        payload = {
            "seed": DEFAULT_SEED,
            "model": model_path,
            "backend": "hf",
            "steering_method": method,
            "max_new_tokens": 64,
            "temperature": DEFAULT_TEMPERATURE,
            "batch_size": DEFAULT_BATCH_SIZE,
            "do_sample": True,
            "k": adj.K_SAMPLES,
            "bootstrap_b": adj.BOOTSTRAP_B,
            "alpha_grid": list(adj.ALPHA_GRID),
            "coherence_max_ratio": adj.COHERENCE_MAX_RATIO,
            "delta": adj.DELTA,
            "bonferroni_ci_level": adj.BONFERRONI_CI_LEVEL,
            "dev_fraction": adj.DEV_FRACTION,
            "stronger_prompt_optimizer": {
                "enabled": False,
                "budget_cli": None,
                "budget_effective": None,
                "seed_prompts": 4,
                "rounds": 3,
                "candidates_per_round": 4,
                "keep_top_k": 2,
                "optimizer_seed": DEFAULT_SEED,
                "compute_parity_target_n_strong": 16,
                "n_strong_requested": 16,
            },
            "axes": {
                axis: {
                    "n_items": len(values["item_ids"]),
                    "item_ids": values["item_ids"],
                    "n_strong": len(values["strong_ids"]),
                    "strong_ids": values["strong_ids"],
                }
                for axis, values in axes.items()
            },
        }
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]
        results[f"{method}__{model_label}"] = digest
    return results


def load_item_identity() -> Dict[str, object]:
    payload = json.loads(ITEM_IDENTITY_PATH.read_text(encoding="utf-8"))
    required = {
        "schema_version",
        "identity_status",
        "historical_code_commit",
        "dataset",
        "ordered_pool_ids",
        "ordered_test_ids",
        "ordered_pool_ids_sha256",
        "ordered_test_ids_sha256",
        "matched_source_config_fingerprints",
        "limitations",
    }
    if not isinstance(payload, dict) or set(payload) != required:
        raise ValueError(f"{ITEM_IDENTITY_PATH}: identity schema mismatch")
    if payload["schema_version"] != 1:
        raise ValueError(f"{ITEM_IDENTITY_PATH}: unsupported schema")
    if payload["identity_status"] != "ORDERED_IDS_PROVEN_CONTENT_RECONSTRUCTED":
        raise ValueError(f"{ITEM_IDENTITY_PATH}: item identity is not audit-ready")
    dataset = dict(payload["dataset"])
    if (
        dataset.get("repo_id") != "openai/gsm8k"
        or dataset.get("config") != "main"
        or dataset.get("split") != "test"
        or dataset.get("revision") != GSM8K_REVISION
    ):
        raise ValueError(f"{ITEM_IDENTITY_PATH}: pinned GSM8K identity mismatch")
    pool_ids = [str(value) for value in payload["ordered_pool_ids"]]
    test_ids = [str(value) for value in payload["ordered_test_ids"]]
    if len(pool_ids) != adj.N_ITEMS_BY_AXIS[AXIS] or len(test_ids) != 40:
        raise ValueError(f"{ITEM_IDENTITY_PATH}: recovered item count mismatch")
    if payload["ordered_pool_ids_sha256"] != _canonical_json_hash(pool_ids):
        raise ValueError(f"{ITEM_IDENTITY_PATH}: pool ID hash mismatch")
    if payload["ordered_test_ids_sha256"] != _canonical_json_hash(test_ids):
        raise ValueError(f"{ITEM_IDENTITY_PATH}: TEST ID hash mismatch")
    expected_fingerprints = {
        "caa__qwen2.5-7b": "433c5772c8ede7f8",
        "caa__llama3-8b": "861d5b5f8773c6f0",
        "iti__qwen2.5-7b": "2d1749bdc7089f83",
        "iti__llama3-8b": "d39efbeac006dac5",
    }
    recomputed = _recompute_historical_e0006_fingerprints(pool_ids)
    if (
        payload["matched_source_config_fingerprints"] != expected_fingerprints
        or recomputed != expected_fingerprints
    ):
        raise ValueError(f"{ITEM_IDENTITY_PATH}: fingerprint proof mismatch")
    return payload


def load_test_items(*, seed: int) -> Tuple[List[Dict[str, object]], Dict[str, object]]:
    identity = load_item_identity()
    items = list(
        c2b_tasks.load_gsm8k_test(revision=GSM8K_REVISION)
    )[: adj.N_ITEMS_BY_AXIS[AXIS]]
    observed_pool_ids = [str(item["id"]) for item in items]
    expected_pool_ids = [str(value) for value in identity["ordered_pool_ids"]]
    if observed_pool_ids != expected_pool_ids:
        raise ValueError(
            "pinned GSM8K snapshot does not reproduce the recovered ordered "
            "E-0006 index-ID pool"
        )
    by_id = {str(item["id"]): item for item in items}
    split = adj.split_dev_test(
        list(by_id),
        dev_fraction=adj.DEV_FRACTION,
        seed=seed,
    )
    expected_test_ids = [str(value) for value in identity["ordered_test_ids"]]
    if split.test_ids != expected_test_ids:
        raise ValueError("recovered E-0006 TEST ID split mismatch")
    return [by_id[item_id] for item_id in split.test_ids], identity


def _condition_instruction_and_alpha(
    cfg: FrozenCellConfig, condition: str
) -> Tuple[str, float, float]:
    if condition == "prompt":
        return cfg.best_prompt_text, 0.0, 0.0
    if condition == "baseline":
        return cfg.neutral_prompt, 0.0, 0.0
    if condition == "steer":
        effective = (
            sigma_scaled_alpha(cfg.frozen_alpha, cfg.sigma)
            if cfg.method == "iti"
            else cfg.frozen_alpha
        )
        return cfg.neutral_prompt, cfg.frozen_alpha, effective
    raise ValueError(f"unknown condition {condition!r}")


def _call_seed(base_seed: int, item_id: str, effective_alpha: float, sample_index: int) -> int:
    key = (
        f"{int(base_seed)}|{AXIS}|{item_id}|"
        f"{float(effective_alpha):.6f}|{int(sample_index)}"
    )
    return int(hashlib.sha256(key.encode("utf-8")).hexdigest(), 16) % (2**31)


def iter_original_batches(
    items: Sequence[Dict[str, object]], *, batch_size: int
) -> Iterable[List[Dict[str, object]]]:
    """Yield the exact item chunking used by frozen _channel_item_outcomes."""

    items_per_batch = max(1, int(batch_size) // int(adj.K_SAMPLES))
    for start in range(0, len(items), items_per_batch):
        yield list(items[start : start + items_per_batch])


def _derive_hf_direction(
    cfg: FrozenCellConfig,
    *,
    model_load_path: str,
    out_dir: Path,
    n_extraction: int,
    seed: int,
) -> Tuple[np.ndarray, Dict[str, object]]:
    from cognitive_console.activations.provider import HFActivationProvider

    provider = HFActivationProvider(
        model_load_path,
        device="cuda:0",
        dtype="float16",
        cache_dir=str(out_dir / "activations" / "cache"),
    )
    if cfg.method == "caa":
        direction = p0._extract_direction(provider, AXIS, cfg.layer, n_extraction, seed)
        metadata = {
            "source": "caa_mean_difference_rederived_at_frozen_layer",
            "layer": cfg.layer,
            "direction_sha256": hashlib.sha256(
                np.asarray(direction, dtype=np.float64).tobytes()
            ).hexdigest(),
        }
    else:
        pairs = c1.load_axis_pairs(AXIS)
        split = c1.make_split(
            list(pairs.pos),
            n_extraction=n_extraction,
            seed=seed,
        )
        candidate_layers = [
            layer for layer in provider.available_layers() if layer >= 1
        ]
        iti = extract_iti(
            provider,
            axis=AXIS,
            pos_texts=[pairs.pos[pair_id] for pair_id in split.extraction_ids],
            neg_texts=[pairs.neg[pair_id] for pair_id in split.extraction_ids],
            layers=candidate_layers,
            selection="nondegenerate",
            neutral_texts=c1.load_neutral_prompts(),
            min_layer=min_layer_for_depth(max(candidate_layers), min_depth_frac=0.2),
            min_depth_frac=0.2,
            n_null=2000,
            null_seed=seed,
        )
        if int(iti.layer) != cfg.layer:
            raise RuntimeError(
                f"{cfg.cell_key}: rederived ITI layer {iti.layer} != frozen {cfg.layer}"
            )
        if not math.isclose(
            float(iti.sigma),
            cfg.sigma,
            rel_tol=1e-6,
            abs_tol=1e-8,
        ):
            raise RuntimeError(
                f"{cfg.cell_key}: rederived ITI sigma {iti.sigma} != frozen {cfg.sigma}"
            )
        direction = iti.direction
        metadata = {
            "source": "iti_probe_rederived_by_frozen_path",
            "layer": int(iti.layer),
            "sigma": float(iti.sigma),
            "probe_norm": float(np.linalg.norm(iti.vector)),
            "direction_sha256": hashlib.sha256(
                np.asarray(iti.direction, dtype=np.float64).tobytes()
            ).hexdigest(),
        }
    del provider
    gc.collect()
    try:
        import torch

        torch.cuda.empty_cache()
    except ImportError:
        pass
    return np.asarray(direction), metadata


_EXPLICIT_FINAL_NUMBER_RE = re.compile(
    r"(?:\\boxed\s*\{\s*-?\d[\d,]*(?:\.\d+)?\s*\}"
    r"|(?:final\s+)?answer\s*(?:is|:|=)\s*\$?\s*-?\d[\d,]*(?:\.\d+)?)",
    re.IGNORECASE,
)
_TERMINAL_NUMBER_RE = re.compile(
    r"(?:^|[\s:=])\$?\s*-?\d[\d,]*(?:\.\d+)?\s*"
    r"(?:%|[.!?)]*)?\s*$",
    re.IGNORECASE,
)


def explicit_or_terminal_final_answer_present(text: str) -> bool:
    """Detect an explicit answer cue/box or a numeric answer at text termination."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    stripped = text.strip()
    return bool(
        stripped
        and (
            _EXPLICIT_FINAL_NUMBER_RE.search(stripped)
            or _TERMINAL_NUMBER_RE.search(stripped)
        )
    )


def score_generation(text: str, item: Dict[str, object]) -> Dict[str, object]:
    parsed = scorers.parse_final_number(text)
    return {
        "parsed_final_number": parsed,
        "frozen_parser_number_present": parsed is not None,
        "frozen_parser_failed": parsed is None,
        "explicit_or_terminal_final_answer_present": (
            explicit_or_terminal_final_answer_present(text)
        ),
        "correct": int(scorers.score_deliberation(text, item)),
        "degeneracy": float(scorers.degeneracy_score(text)),
    }


def _records_path(out_dir: Path, cell_key: str, cap: int, condition: str) -> Path:
    return out_dir / "samples" / f"{cell_key}__cap{int(cap)}__{condition}.jsonl"


def _write_jsonl_atomic(path: Path, records: Sequence[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + ".partial")
    with open(partial, "w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    partial.replace(path)


def _read_jsonl(path: Path) -> List[Dict[str, object]]:
    records: List[Dict[str, object]] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON") from exc
    return records


def _expected_condition_jobs(
    *,
    cfg: FrozenCellConfig,
    model_id: str,
    cap: int,
    condition: str,
    test_items: Sequence[Dict[str, object]],
    seed: int,
) -> List[Dict[str, object]]:
    instruction, requested_alpha, effective_alpha = _condition_instruction_and_alpha(
        cfg, condition
    )
    jobs: List[Dict[str, object]] = []
    for item in test_items:
        prompt = adj.format_task_input(AXIS, instruction, item)
        for sample_index in range(adj.K_SAMPLES):
            jobs.append(
                {
                    "experiment_id": EXPERIMENT_ID,
                    "axis": AXIS,
                    "cell": cfg.cell_key,
                    "method": cfg.method,
                    "model_label": cfg.model_label,
                    "model_id": model_id,
                    "condition": condition,
                    "max_new_tokens": int(cap),
                    "item_id": str(item["id"]),
                    "sample_index": int(sample_index),
                    "sample_seed": int(
                        _call_seed(
                            seed,
                            str(item["id"]),
                            effective_alpha,
                            sample_index,
                        )
                    ),
                    "layer": int(cfg.layer),
                    "requested_alpha": float(requested_alpha),
                    "effective_alpha": float(effective_alpha),
                    "best_prompt_id": (
                        cfg.best_prompt_id if condition == "prompt" else None
                    ),
                    "instruction_sha256": _sha256_text(instruction),
                    "prompt_text_sha256": _sha256_text(prompt),
                    "source_result_file": cfg.source_result_file,
                    "source_result_sha256": cfg.source_result_sha256,
                    "source_config_fingerprint": cfg.source_config_fingerprint,
                }
            )
    return jobs


def _checkpoint_record_boundaries(
    test_items: Sequence[Dict[str, object]], *, batch_size: int
) -> List[int]:
    total = 0
    boundaries = [0]
    for chunk in iter_original_batches(test_items, batch_size=batch_size):
        total += len(chunk) * adj.K_SAMPLES
        boundaries.append(total)
    return boundaries


def _same_number(left: object, right: object) -> bool:
    if left is None or right is None:
        return left is None and right is None
    return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=1e-12)


def _validate_condition_records(
    records: Sequence[Dict[str, object]],
    *,
    cfg: FrozenCellConfig,
    model_id: str,
    cap: int,
    condition: str,
    test_items: Sequence[Dict[str, object]],
    seed: int,
    batch_size: int,
    allow_checkpoint_prefix: bool = False,
) -> None:
    expected = _expected_condition_jobs(
        cfg=cfg,
        model_id=model_id,
        cap=cap,
        condition=condition,
        test_items=test_items,
        seed=seed,
    )
    boundaries = _checkpoint_record_boundaries(test_items, batch_size=batch_size)
    if allow_checkpoint_prefix:
        if len(records) not in boundaries:
            raise ValueError(
                f"{cfg.cell_key} cap={cap} condition={condition}: checkpoint does "
                "not end at a fixed original-batch boundary"
            )
    elif len(records) != len(expected):
        raise ValueError(
            f"{cfg.cell_key} cap={cap} condition={condition}: incomplete/duplicate records"
        )
    item_by_id = {str(item["id"]): item for item in test_items}
    for index, (record, job) in enumerate(zip(records, expected)):
        for field, value in job.items():
            if record.get(field) != value:
                raise ValueError(
                    f"{cfg.cell_key} cap={cap} condition={condition}: "
                    f"record {index} field {field!r} mismatch"
                )
        token_ids = [int(value) for value in record.get("token_ids", [])]
        generated_count = int(record.get("generated_token_count", -1))
        visible_count = int(record.get("visible_token_count", -1))
        raw_width = int(record.get("raw_continuation_width", -1))
        stop_reason = str(record.get("stop_reason", ""))
        hit_cap = record.get("hit_max_new_tokens")
        eos_token_id = record.get("eos_token_id")
        if generated_count != len(token_ids) or not (0 <= generated_count <= int(cap)):
            raise ValueError(
                f"{cfg.cell_key} cap={cap} condition={condition}: invalid token count"
            )
        if raw_width < generated_count or raw_width > int(cap):
            raise ValueError(
                f"{cfg.cell_key} cap={cap} condition={condition}: invalid raw width"
            )
        if stop_reason == "eos":
            if (
                hit_cap is not False
                or eos_token_id is None
                or not token_ids
                or token_ids[-1] != int(eos_token_id)
                or int(eos_token_id) in token_ids[:-1]
                or visible_count != generated_count - 1
            ):
                raise ValueError(
                    f"{cfg.cell_key} cap={cap} condition={condition}: invalid EOS trace"
                )
        elif stop_reason == "max_new_tokens":
            if (
                hit_cap is not True
                or eos_token_id is not None
                or generated_count != int(cap)
                or visible_count != generated_count
            ):
                raise ValueError(
                    f"{cfg.cell_key} cap={cap} condition={condition}: invalid cap trace"
                )
        elif stop_reason == "other":
            if (
                hit_cap is not False
                or eos_token_id is not None
                or generated_count >= int(cap)
                or visible_count != generated_count
            ):
                raise ValueError(
                    f"{cfg.cell_key} cap={cap} condition={condition}: invalid other trace"
                )
        else:
            raise ValueError(
                f"{cfg.cell_key} cap={cap} condition={condition}: unknown stop reason"
            )
        text = str(record.get("generation_text", ""))
        if record.get("generation_text_sha256") != _sha256_text(text):
            raise ValueError(
                f"{cfg.cell_key} cap={cap} condition={condition}: text hash mismatch"
            )
        rescored = score_generation(text, item_by_id[str(job["item_id"])])
        for field in (
            "frozen_parser_number_present",
            "frozen_parser_failed",
            "explicit_or_terminal_final_answer_present",
            "correct",
        ):
            if record.get(field) != rescored[field]:
                raise ValueError(
                    f"{cfg.cell_key} cap={cap} condition={condition}: "
                    f"rescored {field} mismatch"
                )
        if not _same_number(
            record.get("parsed_final_number"), rescored["parsed_final_number"]
        ):
            raise ValueError(
                f"{cfg.cell_key} cap={cap} condition={condition}: parsed answer mismatch"
            )
        if not math.isclose(
            float(record.get("degeneracy", math.nan)),
            float(rescored["degeneracy"]),
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise ValueError(
                f"{cfg.cell_key} cap={cap} condition={condition}: degeneracy mismatch"
            )


def _checkpoint_payload(
    *,
    checkpoint_identity: Dict[str, object],
    expected_jobs: Sequence[Dict[str, object]],
    records: Sequence[Dict[str, object]],
    complete: bool,
    final_sample_sha256: Optional[str] = None,
) -> Dict[str, object]:
    return {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
        "experiment_id": EXPERIMENT_ID,
        "checkpoint_identity": checkpoint_identity,
        "checkpoint_identity_sha256": _canonical_json_hash(checkpoint_identity),
        "expected_jobs_sha256": _canonical_json_hash(list(expected_jobs)),
        "record_count": len(records),
        "records_sha256": _canonical_json_hash(list(records)),
        "complete": bool(complete),
        "final_sample_sha256": final_sample_sha256,
        "records": list(records),
        "valid_for_paper": False,
        "updated_at": utcnow(),
    }


def _load_condition_checkpoint(
    path: Path,
    *,
    checkpoint_identity: Dict[str, object],
    expected_jobs: Sequence[Dict[str, object]],
    cfg: FrozenCellConfig,
    model_id: str,
    cap: int,
    condition: str,
    test_items: Sequence[Dict[str, object]],
    seed: int,
    batch_size: int,
) -> Tuple[List[Dict[str, object]], Dict[str, object]]:
    if not path.exists():
        return [], {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected_fields = {
        "schema_version",
        "experiment_id",
        "checkpoint_identity",
        "checkpoint_identity_sha256",
        "expected_jobs_sha256",
        "record_count",
        "records_sha256",
        "complete",
        "final_sample_sha256",
        "records",
        "valid_for_paper",
        "updated_at",
    }
    if (
        not isinstance(payload, dict)
        or set(payload) != expected_fields
        or payload.get("schema_version") != CHECKPOINT_SCHEMA_VERSION
        or payload.get("experiment_id") != EXPERIMENT_ID
        or payload.get("checkpoint_identity") != checkpoint_identity
        or payload.get("checkpoint_identity_sha256")
        != _canonical_json_hash(checkpoint_identity)
        or payload.get("expected_jobs_sha256")
        != _canonical_json_hash(list(expected_jobs))
        or payload.get("records_sha256")
        != _canonical_json_hash(list(payload.get("records") or []))
        or payload.get("valid_for_paper") is not False
        or type(payload.get("complete")) is not bool
    ):
        raise ValueError(f"{path}: checkpoint identity mismatch")
    records = list(payload.get("records") or [])
    if int(payload.get("record_count", -1)) != len(records):
        raise ValueError(f"{path}: checkpoint record count mismatch")
    _validate_condition_records(
        records,
        cfg=cfg,
        model_id=model_id,
        cap=cap,
        condition=condition,
        test_items=test_items,
        seed=seed,
        batch_size=batch_size,
        allow_checkpoint_prefix=not bool(payload["complete"]),
    )
    if payload["complete"] and len(records) != len(expected_jobs):
        raise ValueError(f"{path}: complete checkpoint is not complete")
    if not payload["complete"] and len(records) == len(expected_jobs):
        raise ValueError(f"{path}: full checkpoint may not be marked partial")
    return records, payload


def generate_condition(
    *,
    backend,
    cfg: FrozenCellConfig,
    direction: np.ndarray,
    model_id: str,
    cap: int,
    condition: str,
    test_items: Sequence[Dict[str, object]],
    seed: int,
    temperature: float,
    batch_size: int,
    checkpoint_path: Optional[Path] = None,
    checkpoint_identity: Optional[Dict[str, object]] = None,
    budget_guard=None,
) -> List[Dict[str, object]]:
    instruction, requested_alpha, effective_alpha = _condition_instruction_and_alpha(
        cfg, condition
    )
    steer = SteerConfig(
        direction=direction,
        alpha=effective_alpha,
        layer=cfg.layer,
    )
    expected_jobs = _expected_condition_jobs(
        cfg=cfg,
        model_id=model_id,
        cap=cap,
        condition=condition,
        test_items=test_items,
        seed=seed,
    )
    identity = dict(checkpoint_identity or {})
    records: List[Dict[str, object]] = []
    if checkpoint_path is not None:
        if not identity:
            raise ValueError("checkpoint identity is required when checkpointing")
        records, _ = _load_condition_checkpoint(
            checkpoint_path,
            checkpoint_identity=identity,
            expected_jobs=expected_jobs,
            cfg=cfg,
            model_id=model_id,
            cap=cap,
            condition=condition,
            test_items=test_items,
            seed=seed,
            batch_size=batch_size,
        )
    completed_items = len(records) // adj.K_SAMPLES
    item_offset = 0
    for item_chunk in iter_original_batches(test_items, batch_size=batch_size):
        if budget_guard is not None:
            budget_guard()
        next_item_offset = item_offset + len(item_chunk)
        if next_item_offset <= completed_items:
            item_offset = next_item_offset
            continue
        if item_offset < completed_items:
            raise ValueError("checkpoint splits a fixed original generation batch")
        prompts: List[str] = []
        seeds: List[int] = []
        owners: List[Tuple[Dict[str, object], int]] = []
        for item in item_chunk:
            prompt = adj.format_task_input(AXIS, instruction, item)
            for sample_index in range(adj.K_SAMPLES):
                prompts.append(prompt)
                seeds.append(
                    _call_seed(
                        seed,
                        str(item["id"]),
                        effective_alpha,
                        sample_index,
                    )
                )
                owners.append((item, sample_index))
        traces: List[GenerationTrace] = backend.generate_batch_with_metadata(
            prompts,
            steer,
            max_new_tokens=cap,
            seeds=seeds,
            do_sample=True,
            temperature=temperature,
        )
        if len(traces) != len(owners):
            raise RuntimeError("generation trace count mismatch")
        for (item, sample_index), sample_seed, prompt, trace in zip(
            owners, seeds, prompts, traces
        ):
            records.append(
                {
                    "experiment_id": EXPERIMENT_ID,
                    "axis": AXIS,
                    "cell": cfg.cell_key,
                    "method": cfg.method,
                    "model_label": cfg.model_label,
                    "model_id": model_id,
                    "condition": condition,
                    "max_new_tokens": int(cap),
                    "item_id": str(item["id"]),
                    "sample_index": int(sample_index),
                    "sample_seed": int(sample_seed),
                    "layer": int(cfg.layer),
                    "requested_alpha": float(requested_alpha),
                    "effective_alpha": float(effective_alpha),
                    "best_prompt_id": (
                        cfg.best_prompt_id if condition == "prompt" else None
                    ),
                    "instruction_sha256": _sha256_text(instruction),
                    "prompt_text_sha256": _sha256_text(prompt),
                    "generation_text": trace.text,
                    "generation_text_sha256": _sha256_text(trace.text),
                    "token_ids": list(trace.token_ids),
                    "generated_token_count": int(trace.generated_token_count),
                    "visible_token_count": int(trace.visible_token_count),
                    "raw_continuation_width": int(trace.raw_continuation_width),
                    "stop_reason": trace.stop_reason,
                    "hit_max_new_tokens": bool(trace.hit_max_new_tokens),
                    "eos_token_id": trace.eos_token_id,
                    "source_result_file": cfg.source_result_file,
                    "source_result_sha256": cfg.source_result_sha256,
                    "source_config_fingerprint": cfg.source_config_fingerprint,
                    **score_generation(trace.text, item),
                }
            )
        item_offset = next_item_offset
        _validate_condition_records(
            records,
            cfg=cfg,
            model_id=model_id,
            cap=cap,
            condition=condition,
            test_items=test_items,
            seed=seed,
            batch_size=batch_size,
            allow_checkpoint_prefix=True,
        )
        if checkpoint_path is not None:
            _write_json(
                checkpoint_path,
                _checkpoint_payload(
                    checkpoint_identity=identity,
                    expected_jobs=expected_jobs,
                    records=records,
                    complete=item_offset == len(test_items),
                ),
            )
        if budget_guard is not None:
            budget_guard()
    _validate_condition_records(
        records,
        cfg=cfg,
        model_id=model_id,
        cap=cap,
        condition=condition,
        test_items=test_items,
        seed=seed,
        batch_size=batch_size,
    )
    if checkpoint_path is not None:
        _write_json(
            checkpoint_path,
            _checkpoint_payload(
                checkpoint_identity=identity,
                expected_jobs=expected_jobs,
                records=records,
                complete=True,
            ),
        )
    return records


def _mean_by_item(
    records: Sequence[Dict[str, object]], field: str
) -> Dict[str, float]:
    grouped: Dict[str, List[float]] = {}
    for record in records:
        grouped.setdefault(str(record["item_id"]), []).append(float(record[field]))
    return {
        item_id: float(np.mean(values))
        for item_id, values in sorted(grouped.items())
    }


def _paired_item_diffs(
    records: Sequence[Dict[str, object]],
    *,
    a_filter,
    b_filter,
    field: str,
) -> Tuple[List[str], List[float]]:
    a = _mean_by_item([record for record in records if a_filter(record)], field)
    b = _mean_by_item([record for record in records if b_filter(record)], field)
    ids = sorted(set(a) & set(b))
    return ids, [a[item_id] - b[item_id] for item_id in ids]


def _ci(
    diffs: Sequence[float],
    *,
    bootstrap_b: int,
    ci_level: float,
    seed: int,
) -> Dict[str, object]:
    if not diffs:
        return {
            "point": math.nan,
            "ci_lo": math.nan,
            "ci_hi": math.nan,
            "ci_level": ci_level,
            "bootstrap_b": bootstrap_b,
            "n_items": 0,
        }
    result = adj.cluster_bootstrap_ci(
        np.asarray(diffs, dtype=float),
        b=bootstrap_b,
        ci_level=ci_level,
        seed=seed,
        cluster=True,
    )
    return {
        "point": float(result.point),
        "ci_lo": float(result.ci_lo),
        "ci_hi": float(result.ci_hi),
        "ci_level": float(result.ci_level),
        "bootstrap_b": int(result.b),
        "n_items": len(diffs),
    }


def _max_t_simultaneous_cis(
    estimands: Dict[str, Tuple[Sequence[str], Sequence[float]]],
    *,
    bootstrap_b: int,
    seed: int,
    ci_level: float = 0.95,
) -> Dict[str, Dict[str, object]]:
    if not estimands:
        raise ValueError("max-T family must contain at least one estimand")
    ordered_names = sorted(estimands)
    reference_ids = [str(value) for value in estimands[ordered_names[0]][0]]
    if not reference_ids:
        raise ValueError("max-T family has no item clusters")
    values: List[List[float]] = []
    for name in ordered_names:
        ids, diffs = estimands[name]
        if [str(value) for value in ids] != reference_ids:
            raise ValueError(f"max-T family item mismatch for {name}")
        if len(diffs) != len(reference_ids):
            raise ValueError(f"max-T family value count mismatch for {name}")
        values.append([float(value) for value in diffs])
    matrix = np.asarray(values, dtype=float).T
    point = np.mean(matrix, axis=0)
    rng = np.random.default_rng(seed)
    sample_indices = rng.integers(
        0,
        len(reference_ids),
        size=(int(bootstrap_b), len(reference_ids)),
    )
    boot = np.mean(matrix[sample_indices, :], axis=1)
    centered = boot - point[None, :]
    se = np.std(boot, axis=0, ddof=1)
    standardized = np.zeros_like(centered)
    nonzero_se = se > 0
    standardized[:, nonzero_se] = (
        np.abs(centered[:, nonzero_se]) / se[nonzero_se]
    )
    max_t = np.max(standardized, axis=1)
    quantile = float(np.quantile(max_t, ci_level))
    results: Dict[str, Dict[str, object]] = {}
    for index, name in enumerate(ordered_names):
        half_width = quantile * float(se[index])
        if se[index] == 0:
            adjusted_p = 0.0 if point[index] != 0 else 1.0
        else:
            observed_t = abs(float(point[index])) / float(se[index])
            adjusted_p = float(
                (1 + np.count_nonzero(max_t >= observed_t))
                / (int(bootstrap_b) + 1)
            )
        results[name] = {
            "point": float(point[index]),
            "ci_lo": float(point[index] - half_width),
            "ci_hi": float(point[index] + half_width),
            "ci_level": float(ci_level),
            "bootstrap_b": int(bootstrap_b),
            "n_items": len(reference_ids),
            "max_t_critical_value": quantile,
            "bootstrap_se": float(se[index]),
            "p_fwer_max_t": adjusted_p,
            "multiplicity_method": "joint-item-cluster bootstrap max-T",
            "family_size": len(ordered_names),
            "familywise_alpha": 1.0 - float(ci_level),
        }
    return results


def _build_primary_inference_family(
    records: Sequence[Dict[str, object]],
    *,
    bootstrap_b: int,
    seed: int,
) -> Dict[str, Dict[str, object]]:
    estimands: Dict[str, Tuple[Sequence[str], Sequence[float]]] = {}
    for cell_key in FROZEN_CELL_KEYS:
        cell_records = [
            record for record in records if str(record["cell"]) == cell_key
        ]
        for long_cap in (128, 256):
            effects: Dict[str, Tuple[List[str], List[float]]] = {}
            for condition in ("prompt", "steer"):
                ids, values = _paired_item_diffs(
                    cell_records,
                    a_filter=lambda record, c=condition, lc=long_cap: (
                        record["condition"] == c
                        and int(record["max_new_tokens"]) == lc
                    ),
                    b_filter=lambda record, c=condition: (
                        record["condition"] == c
                        and int(record["max_new_tokens"]) == 64
                    ),
                    field="correct",
                )
                name = f"{cell_key}|E_{condition}_{long_cap}"
                estimands[name] = (ids, values)
                effects[condition] = (ids, values)
            if effects["prompt"][0] != effects["steer"][0]:
                raise ValueError(f"{cell_key}: cap interaction item mismatch")
            interaction = [
                steer_value - prompt_value
                for steer_value, prompt_value in zip(
                    effects["steer"][1],
                    effects["prompt"][1],
                )
            ]
            estimands[f"{cell_key}|I_{long_cap}"] = (
                effects["prompt"][0],
                interaction,
            )
    return _max_t_simultaneous_cis(
        estimands,
        bootstrap_b=bootstrap_b,
        seed=seed,
        ci_level=0.95,
    )


def _item_cluster_metric_ci(
    records: Sequence[Dict[str, object]],
    value_fn,
    *,
    bootstrap_b: int,
    seed: int,
    ci_level: float = 0.95,
) -> Dict[str, object]:
    grouped: Dict[str, List[float]] = {}
    for record in records:
        grouped.setdefault(str(record["item_id"]), []).append(float(value_fn(record)))
    item_means = [
        float(np.mean(grouped[item_id])) for item_id in sorted(grouped)
    ]
    return _ci(
        item_means,
        bootstrap_b=bootstrap_b,
        ci_level=ci_level,
        seed=seed,
    )


def _conditional_accuracy_by_item(
    records: Sequence[Dict[str, object]],
    *,
    hit_cap: bool,
) -> Tuple[Dict[str, float], int]:
    grouped: Dict[str, List[float]] = {}
    n_samples = 0
    for record in records:
        if bool(record["hit_max_new_tokens"]) != bool(hit_cap):
            continue
        grouped.setdefault(str(record["item_id"]), []).append(
            float(record["correct"])
        )
        n_samples += 1
    return (
        {
            item_id: float(np.mean(values))
            for item_id, values in sorted(grouped.items())
        },
        n_samples,
    )


def _conditional_accuracy_summary(
    item_means: Dict[str, float],
    *,
    n_samples: int,
    bootstrap_b: int,
    seed: int,
) -> Dict[str, object]:
    if not item_means:
        return {
            "defined": False,
            "point": None,
            "ci_lo": None,
            "ci_hi": None,
            "ci_level": 0.95,
            "bootstrap_b": int(bootstrap_b),
            "n_items": 0,
            "n_samples": int(n_samples),
            "zero_denominator": True,
        }
    ci = _ci(
        [item_means[item_id] for item_id in sorted(item_means)],
        bootstrap_b=bootstrap_b,
        ci_level=0.95,
        seed=seed,
    )
    return {
        "defined": True,
        **ci,
        "n_samples": int(n_samples),
        "zero_denominator": False,
        "estimand": "mean per-item conditional accuracy",
    }


def _conditional_accuracy_difference(
    hit_by_item: Dict[str, float],
    nonhit_by_item: Dict[str, float],
    *,
    bootstrap_b: int,
    seed: int,
) -> Dict[str, object]:
    paired_ids = sorted(set(hit_by_item) & set(nonhit_by_item))
    if not paired_ids:
        return {
            "defined": False,
            "point": None,
            "ci_lo": None,
            "ci_hi": None,
            "ci_level": 0.95,
            "bootstrap_b": int(bootstrap_b),
            "n_items": 0,
            "zero_denominator": True,
        }
    ci = _ci(
        [
            hit_by_item[item_id] - nonhit_by_item[item_id]
            for item_id in paired_ids
        ],
        bootstrap_b=bootstrap_b,
        ci_level=0.95,
        seed=seed,
    )
    return {
        "defined": True,
        **ci,
        "zero_denominator": False,
        "estimand": (
            "mean within-item conditional-accuracy difference among items "
            "observed in both stop strata"
        ),
    }


def _condition_summary(
    records: Sequence[Dict[str, object]],
    cap: int,
    *,
    bootstrap_b: int,
    seed: int,
) -> Dict[str, object]:
    counts = np.asarray(
        [int(record["generated_token_count"]) for record in records],
        dtype=float,
    )
    hit = [bool(record["hit_max_new_tokens"]) for record in records]
    equals_cap = [int(record["generated_token_count"]) == int(cap) for record in records]
    n = len(records)
    hit_ci = _item_cluster_metric_ci(
        records,
        lambda record: bool(record["hit_max_new_tokens"]),
        bootstrap_b=bootstrap_b,
        seed=seed,
    )
    equals_cap_ci = _item_cluster_metric_ci(
        records,
        lambda record: int(record["generated_token_count"]) == int(cap),
        bootstrap_b=bootstrap_b,
        seed=seed,
    )
    parser_failure_ci = _item_cluster_metric_ci(
        records,
        lambda record: bool(record["frozen_parser_failed"]),
        bootstrap_b=bootstrap_b,
        seed=seed,
    )
    parser_number_present_ci = _item_cluster_metric_ci(
        records,
        lambda record: bool(record["frozen_parser_number_present"]),
        bootstrap_b=bootstrap_b,
        seed=seed,
    )
    explicit_or_terminal_ci = _item_cluster_metric_ci(
        records,
        lambda record: bool(
            record["explicit_or_terminal_final_answer_present"]
        ),
        bootstrap_b=bootstrap_b,
        seed=seed,
    )
    accuracy_ci = _item_cluster_metric_ci(
        records,
        lambda record: int(record["correct"]),
        bootstrap_b=bootstrap_b,
        seed=seed,
    )
    degeneracy_ci = _item_cluster_metric_ci(
        records,
        lambda record: float(record["degeneracy"]),
        bootstrap_b=bootstrap_b,
        seed=seed,
    )
    hit_accuracy_by_item, n_hit_samples = _conditional_accuracy_by_item(
        records,
        hit_cap=True,
    )
    nonhit_accuracy_by_item, n_nonhit_samples = _conditional_accuracy_by_item(
        records,
        hit_cap=False,
    )
    hit_accuracy = _conditional_accuracy_summary(
        hit_accuracy_by_item,
        n_samples=n_hit_samples,
        bootstrap_b=bootstrap_b,
        seed=seed,
    )
    nonhit_accuracy = _conditional_accuracy_summary(
        nonhit_accuracy_by_item,
        n_samples=n_nonhit_samples,
        bootstrap_b=bootstrap_b,
        seed=seed,
    )
    accuracy_difference = _conditional_accuracy_difference(
        hit_accuracy_by_item,
        nonhit_accuracy_by_item,
        bootstrap_b=bootstrap_b,
        seed=seed,
    )
    return {
        "n_samples": n,
        "token_count": {
            "min": int(np.min(counts)) if n else None,
            "median": float(np.median(counts)) if n else None,
            "p95": float(np.quantile(counts, 0.95)) if n else None,
            "max": int(np.max(counts)) if n else None,
            "n_equal_cap": int(sum(equals_cap)),
            "fraction_equal_cap": float(np.mean(equals_cap)) if n else math.nan,
            "fraction_equal_cap_ci_95_item_cluster": equals_cap_ci,
            "n_equal_cap_but_not_mechanical_stop": int(
                sum(equal and not stopped for equal, stopped in zip(equals_cap, hit))
            ),
        },
        "mechanical_cap_stop": {
            "n": int(sum(hit)),
            "fraction": float(np.mean(hit)) if n else math.nan,
            "fraction_ci_95_item_cluster": hit_ci,
            "definition": (
                "no EOS token occurred and model.generate consumed exactly "
                "max_new_tokens; token count equal to cap alone is not sufficient"
            ),
        },
        "frozen_parser": {
            "n_number_present": sum(
                bool(record["frozen_parser_number_present"]) for record in records
            ),
            "number_present_rate": float(
                np.mean(
                    [
                        bool(record["frozen_parser_number_present"])
                        for record in records
                    ]
                )
            )
            if n
            else math.nan,
            "number_present_ci_95_item_cluster": parser_number_present_ci,
            "n_failed": sum(
                bool(record["frozen_parser_failed"]) for record in records
            ),
            "failure_rate": float(
                np.mean(
                    [bool(record["frozen_parser_failed"]) for record in records]
                )
            )
            if n
            else math.nan,
            "failure_ci_95_item_cluster": parser_failure_ci,
            "interpretation": (
                "The frozen correctness parser may fall back to any last number. "
                "Parser success is not labelled final-answer presence."
            ),
        },
        "explicit_or_terminal_final_answer": {
            "n_present": sum(
                bool(record["explicit_or_terminal_final_answer_present"])
                for record in records
            ),
            "present_rate": float(
                np.mean(
                    [
                        bool(
                            record[
                                "explicit_or_terminal_final_answer_present"
                            ]
                        )
                        for record in records
                    ]
                )
            )
            if n
            else math.nan,
            "present_ci_95_item_cluster": explicit_or_terminal_ci,
            "definition": (
                "numeric answer in an explicit answer cue/box or at the terminal "
                "end of the decoded continuation; independent of the frozen parser"
            ),
        },
        "accuracy": float(np.mean([int(record["correct"]) for record in records]))
        if n
        else math.nan,
        "accuracy_ci_95_item_cluster": accuracy_ci,
        "mean_degeneracy": float(
            np.mean([float(record["degeneracy"]) for record in records])
        )
        if n
        else math.nan,
        "mean_degeneracy_ci_95_item_cluster": degeneracy_ci,
        "accuracy_by_cap_stop": {
            "hit_cap": hit_accuracy,
            "did_not_hit_cap": nonhit_accuracy,
            "hit_minus_did_not_hit": accuracy_difference,
            "association_only": True,
            "unit": (
                "item; sample outcomes are averaged within item and stratum "
                "before item-cluster inference"
            ),
        },
    }


def _sample_lookup(
    records: Sequence[Dict[str, object]],
) -> Dict[Tuple[str, int, str, int], Dict[str, object]]:
    lookup: Dict[Tuple[str, int, str, int], Dict[str, object]] = {}
    for record in records:
        key = (
            str(record["condition"]),
            int(record["max_new_tokens"]),
            str(record["item_id"]),
            int(record["sample_index"]),
        )
        if key in lookup:
            raise ValueError(f"duplicate sample key: {key}")
        lookup[key] = record
    return lookup


def _conditional_item_cluster_rate_ci(
    numerators: Dict[str, int],
    denominators: Dict[str, int],
    *,
    bootstrap_b: int,
    seed: int,
    ci_level: float = 0.95,
) -> Dict[str, object]:
    eligible_ids = [
        item_id
        for item_id in sorted(denominators)
        if int(denominators[item_id]) > 0
    ]
    denominator_samples = sum(int(denominators[item_id]) for item_id in eligible_ids)
    if not eligible_ids:
        return {
            "defined": False,
            "point": None,
            "ci_lo": None,
            "ci_hi": None,
            "ci_level": float(ci_level),
            "bootstrap_b": int(bootstrap_b),
            "n_eligible_items": 0,
            "n_denominator_samples": 0,
            "zero_denominator": True,
        }
    item_rates = [
        float(numerators.get(item_id, 0)) / float(denominators[item_id])
        for item_id in eligible_ids
    ]
    ci = _ci(
        item_rates,
        bootstrap_b=bootstrap_b,
        ci_level=ci_level,
        seed=seed,
    )
    return {
        "defined": True,
        **ci,
        "n_eligible_items": len(eligible_ids),
        "n_denominator_samples": int(denominator_samples),
        "zero_denominator": False,
        "estimand": (
            "mean item-level conditional rate among items with at least one "
            "64-token mechanical stop"
        ),
    }


def _continuation_materiality(
    cell_records: Sequence[Dict[str, object]],
    *,
    long_cap: int,
    bootstrap_b: int,
    seed: int,
) -> Dict[str, object]:
    lookup = _sample_lookup(cell_records)
    by_condition: Dict[str, Dict[str, object]] = {}
    for condition in CONDITIONS:
        compared = 0
        prefix_matches = 0
        added_answer = 0
        answer_changed = 0
        correctness_recovered = 0
        correctness_lost = 0
        materially_changed = 0
        denominators: Dict[str, int] = {}
        per_item: Dict[str, Dict[str, int]] = {
            name: {}
            for name in (
                "prefix_match",
                "explicit_or_terminal_answer_added",
                "frozen_parser_number_added",
                "frozen_parser_number_changed",
                "correctness_recovered",
                "correctness_lost",
                "operational_semantic_evidence",
            )
        }
        for key, short in lookup.items():
            cond, cap, item_id, sample_index = key
            if cond != condition or cap != 64 or not bool(short["hit_max_new_tokens"]):
                continue
            long = lookup.get((condition, int(long_cap), item_id, sample_index))
            if long is None:
                raise ValueError(f"missing paired long-cap sample for {key}")
            compared += 1
            denominators[item_id] = denominators.get(item_id, 0) + 1
            short_ids = [int(value) for value in short["token_ids"]]
            long_ids = [int(value) for value in long["token_ids"]]
            sample_prefix_match = int(long_ids[: len(short_ids)] == short_ids)
            prefix_matches += sample_prefix_match
            short_answer = short.get("parsed_final_number")
            long_answer = long.get("parsed_final_number")
            sample_parser_number_added = int(
                short_answer is None and long_answer is not None
            )
            sample_answer_changed = int(
                sample_parser_number_added
                or (
                    short_answer is not None
                    and long_answer is not None
                    and float(short_answer) != float(long_answer)
                )
            )
            sample_correctness_recovered = int(
                int(short["correct"]) == 0 and int(long["correct"]) == 1
            )
            sample_correctness_lost = int(
                int(short["correct"]) == 1 and int(long["correct"]) == 0
            )
            sample_explicit_answer_added = int(
                not bool(short["explicit_or_terminal_final_answer_present"])
                and bool(long["explicit_or_terminal_final_answer_present"])
            )
            added_answer += sample_explicit_answer_added
            answer_changed += sample_answer_changed
            correctness_recovered += sample_correctness_recovered
            correctness_lost += sample_correctness_lost
            sample_materially_changed = int(
                any(
                    (
                        sample_explicit_answer_added,
                        sample_parser_number_added,
                        sample_answer_changed,
                        sample_correctness_recovered,
                        sample_correctness_lost,
                    )
                )
            )
            materially_changed += sample_materially_changed
            sample_values = {
                "prefix_match": sample_prefix_match,
                "explicit_or_terminal_answer_added": sample_explicit_answer_added,
                "frozen_parser_number_added": sample_parser_number_added,
                "frozen_parser_number_changed": sample_answer_changed,
                "correctness_recovered": sample_correctness_recovered,
                "correctness_lost": sample_correctness_lost,
                "operational_semantic_evidence": sample_materially_changed,
            }
            for name, value in sample_values.items():
                per_item[name][item_id] = per_item[name].get(item_id, 0) + int(value)
        rate_cis = {
            name: _conditional_item_cluster_rate_ci(
                values,
                denominators,
                bootstrap_b=bootstrap_b,
                seed=seed,
            )
            for name, values in per_item.items()
        }
        by_condition[condition] = {
            "n_64_cap_stops_compared": compared,
            "n_exact_token_prefix_matches": prefix_matches,
            "all_prefixes_match": (
                prefix_matches == compared if compared else None
            ),
            "n_continuation_added_explicit_or_terminal_final_answer": added_answer,
            "n_continuation_added_frozen_parser_number": sum(
                per_item["frozen_parser_number_added"].values()
            ),
            "n_continuation_changed_frozen_parser_number": answer_changed,
            "n_correctness_recovered": correctness_recovered,
            "n_correctness_lost": correctness_lost,
            "n_operational_semantic_truncation_evidence": materially_changed,
            "fraction_operational_semantic_truncation_evidence_among_64_cap_stops": (
                float(materially_changed / compared) if compared else None
            ),
            "operational_semantic_truncation_evidence_present": (
                compared > 0
                and prefix_matches == compared
                and materially_changed > 0
            ),
            "conditional_rates_ci_95_item_cluster": rate_cis,
            "semantic_note": (
                "A mechanical cap stop is not semantic truncation. Same-seed "
                "exact-prefix continuation that adds an explicit/terminal final "
                "answer, changes the frozen parser number (including None-to-number), "
                "or changes correctness is the predeclared operational evidence "
                "that the 64-token cap was semantically material. Frozen parser "
                "success alone is not labelled final-answer presence."
            ),
        }
    return by_condition


def _equivalent_within(ci: Dict[str, object], margin: float = adj.DELTA) -> bool:
    return (
        float(ci["ci_lo"]) > -float(margin)
        and float(ci["ci_hi"]) < float(margin)
    )


def _meaningful_nonzero(ci: Dict[str, object], margin: float = adj.DELTA) -> bool:
    point = float(ci["point"])
    excludes_zero = not (float(ci["ci_lo"]) <= 0.0 <= float(ci["ci_hi"]))
    return abs(point) >= float(margin) and excludes_zero


def _planning_power(cfg: FrozenCellConfig) -> Dict[str, object]:
    diffs = np.asarray(cfg.source_per_item_steer) - np.asarray(
        cfg.source_per_item_prompt
    )
    sd = float(np.std(diffs, ddof=1))
    n = len(diffs)
    z_alpha = NormalDist().inv_cdf(0.975)
    z_power = NormalDist().inv_cdf(0.80)
    mde = (z_alpha + z_power) * sd / math.sqrt(n)
    return {
        "n_test_items": n,
        "k_samples": adj.K_SAMPLES,
        "frozen_64_item_diff_sd": sd,
        "normal_approx_two_sided_80pct_mde": mde,
        "limitation": (
            "Planning reference only. The cap-by-condition interaction can have "
            "different variance; inference uses paired item bootstrap and does "
            "not treat a non-significant result as equivalence."
        ),
    }


def analyse(
    records: Sequence[Dict[str, object]],
    configs: Dict[str, FrozenCellConfig],
    *,
    bootstrap_b: int,
    seed: int,
) -> Dict[str, object]:
    cells: Dict[str, Dict[str, object]] = {}
    overall_branches: List[str] = []
    primary_family = _build_primary_inference_family(
        records,
        bootstrap_b=bootstrap_b,
        seed=seed,
    )
    for cell_key in FROZEN_CELL_KEYS:
        cfg = configs[cell_key]
        cell_records = [
            record for record in records if str(record["cell"]) == cell_key
        ]
        cap_rows: Dict[str, Dict[str, object]] = {}
        pass_by_cap: Dict[int, bool] = {}
        d_by_cap: Dict[int, Dict[str, object]] = {}
        for cap in CAPS:
            cap_records = [
                record
                for record in cell_records
                if int(record["max_new_tokens"]) == cap
            ]
            conditions = {
                condition: _condition_summary(
                    [
                        record
                        for record in cap_records
                        if record["condition"] == condition
                    ],
                    cap,
                    bootstrap_b=bootstrap_b,
                    seed=seed,
                )
                for condition in CONDITIONS
            }
            _, diffs = _paired_item_diffs(
                cap_records,
                a_filter=lambda record: record["condition"] == "steer",
                b_filter=lambda record: record["condition"] == "prompt",
                field="correct",
            )
            delta_ci = _ci(
                diffs,
                bootstrap_b=bootstrap_b,
                ci_level=adj.BONFERRONI_CI_LEVEL,
                seed=seed,
            )
            steer_deg = float(conditions["steer"]["mean_degeneracy"])
            baseline_deg = float(conditions["baseline"]["mean_degeneracy"])
            coherence_ok = (
                steer_deg
                <= adj.COHERENCE_MAX_RATIO * baseline_deg
                + adj.COHERENCE_EPS_FLOOR
                + 1e-12
            )
            passed = adj.axis_pass(
                float(delta_ci["point"]),
                float(delta_ci["ci_lo"]),
                float(delta_ci["ci_hi"]),
                coherence_ok,
                delta=adj.DELTA,
            )
            _, hit_diffs = _paired_item_diffs(
                cap_records,
                a_filter=lambda record: record["condition"] == "steer",
                b_filter=lambda record: record["condition"] == "prompt",
                field="hit_max_new_tokens",
            )
            hit_ci = _ci(
                hit_diffs,
                bootstrap_b=bootstrap_b,
                ci_level=0.95,
                seed=seed,
            )
            cap_rows[str(cap)] = {
                "conditions": conditions,
                "steer_minus_prompt_accuracy": delta_ci,
                "steer_minus_prompt_cap_stop_rate": hit_ci,
                "coherence": {
                    "steer_mean_degeneracy": steer_deg,
                    "baseline_mean_degeneracy": baseline_deg,
                    "ceiling": (
                        adj.COHERENCE_MAX_RATIO * baseline_deg
                        + adj.COHERENCE_EPS_FLOOR
                    ),
                    "passed": coherence_ok,
                },
                "frozen_axis_pass_rule_applied_as_companion": passed,
            }
            pass_by_cap[cap] = bool(passed)
            d_by_cap[cap] = delta_ci

        cap64_prompt = _mean_by_item(
            [
                record
                for record in cell_records
                if int(record["max_new_tokens"]) == 64
                and record["condition"] == "prompt"
            ],
            "correct",
        )
        cap64_steer = _mean_by_item(
            [
                record
                for record in cell_records
                if int(record["max_new_tokens"]) == 64
                and record["condition"] == "steer"
            ],
            "correct",
        )
        item_ids = sorted(cap64_prompt)
        current_prompt = [cap64_prompt[item_id] for item_id in item_ids]
        current_steer = [cap64_steer[item_id] for item_id in item_ids]
        frozen_prompt = list(cfg.source_per_item_prompt)
        frozen_steer = list(cfg.source_per_item_steer)
        prompt_mismatch_ids = [
            item_id
            for item_id, current, frozen in zip(
                item_ids, current_prompt, frozen_prompt
            )
            if current != frozen
        ]
        steer_mismatch_ids = [
            item_id
            for item_id, current, frozen in zip(
                item_ids, current_steer, frozen_steer
            )
            if current != frozen
        ]
        aggregate_matches = (
            math.isclose(
                float(d_by_cap[64]["point"]),
                cfg.source_mean_diff,
                rel_tol=0.0,
                abs_tol=1e-12,
            )
            and math.isclose(
                float(d_by_cap[64]["ci_lo"]),
                cfg.source_ci_lo,
                rel_tol=0.0,
                abs_tol=1e-12,
            )
            and math.isclose(
                float(d_by_cap[64]["ci_hi"]),
                cfg.source_ci_hi,
                rel_tol=0.0,
                abs_tol=1e-12,
            )
            and pass_by_cap[64] == cfg.source_passed
        )
        reproduced = (
            len(item_ids) == 40
            and current_prompt == frozen_prompt
            and current_steer == frozen_steer
            and aggregate_matches
        )

        comparisons: Dict[str, Dict[str, object]] = {}
        affects_comparison = False
        absolute_material = False
        semantic_materiality_observed = False
        all_interactions_equivalent = True
        all_absolute_equivalent = True
        for long_cap in (128, 256):
            condition_effects: Dict[str, Dict[str, object]] = {}
            for condition in ("prompt", "steer"):
                _, effect = _paired_item_diffs(
                    cell_records,
                    a_filter=lambda record, c=condition, lc=long_cap: (
                        record["condition"] == c
                        and int(record["max_new_tokens"]) == lc
                    ),
                    b_filter=lambda record, c=condition: (
                        record["condition"] == c
                        and int(record["max_new_tokens"]) == 64
                    ),
                    field="correct",
                )
                unadjusted_effect_ci = _ci(
                    effect,
                    bootstrap_b=bootstrap_b,
                    ci_level=0.95,
                    seed=seed,
                )
                effect_ci = dict(
                    primary_family[
                        f"{cell_key}|E_{condition}_{long_cap}"
                    ]
                )
                effect_ci["unadjusted_ci_95_item_cluster"] = (
                    unadjusted_effect_ci
                )
                condition_effects[condition] = effect_ci
                absolute_material |= _meaningful_nonzero(effect_ci)
                all_absolute_equivalent &= _equivalent_within(effect_ci)

            ids_steer, steer_effect = _paired_item_diffs(
                cell_records,
                a_filter=lambda record, lc=long_cap: (
                    record["condition"] == "steer"
                    and int(record["max_new_tokens"]) == lc
                ),
                b_filter=lambda record: (
                    record["condition"] == "steer"
                    and int(record["max_new_tokens"]) == 64
                ),
                field="correct",
            )
            ids_prompt, prompt_effect = _paired_item_diffs(
                cell_records,
                a_filter=lambda record, lc=long_cap: (
                    record["condition"] == "prompt"
                    and int(record["max_new_tokens"]) == lc
                ),
                b_filter=lambda record: (
                    record["condition"] == "prompt"
                    and int(record["max_new_tokens"]) == 64
                ),
                field="correct",
            )
            if ids_steer != ids_prompt:
                raise ValueError(f"{cell_key}: cap interaction item mismatch")
            interaction = [
                steer_value - prompt_value
                for steer_value, prompt_value in zip(steer_effect, prompt_effect)
            ]
            unadjusted_interaction_ci = _ci(
                interaction,
                bootstrap_b=bootstrap_b,
                ci_level=0.95,
                seed=seed,
            )
            interaction_ci = dict(
                primary_family[f"{cell_key}|I_{long_cap}"]
            )
            interaction_ci["unadjusted_ci_95_item_cluster"] = (
                unadjusted_interaction_ci
            )
            affects_comparison |= _meaningful_nonzero(interaction_ci)
            all_interactions_equivalent &= _equivalent_within(interaction_ci)
            continuation = _continuation_materiality(
                cell_records,
                long_cap=long_cap,
                bootstrap_b=bootstrap_b,
                seed=seed,
            )
            for condition, continuation_row in continuation.items():
                if (
                    int(continuation_row["n_64_cap_stops_compared"]) > 0
                    and not bool(continuation_row["all_prefixes_match"])
                ):
                    raise ValueError(
                        f"{cell_key} {condition}: 64-token output is not an exact "
                        f"prefix of the paired {long_cap}-token continuation"
                    )
                semantic_materiality_observed |= bool(
                    continuation_row[
                        "operational_semantic_truncation_evidence_present"
                    ]
                )
            comparisons[str(long_cap)] = {
                "accuracy_effect_long_minus_64_by_condition": condition_effects,
                "cap_by_condition_accuracy_interaction": interaction_ci,
                "d_long_minus_d_64": (
                    float(d_by_cap[long_cap]["point"])
                    - float(d_by_cap[64]["point"])
                ),
                "continuation_materiality_among_64_cap_stops": continuation,
            }

        pass_changed = any(
            pass_by_cap[long_cap] != pass_by_cap[64] for long_cap in (128, 256)
        )
        if not reproduced:
            branch = "INVALID_64_NONREPRODUCTION"
        elif affects_comparison:
            branch = "DISTORTION_AFFECTS_STEER_VS_PROMPT_COMPARISON"
        elif absolute_material and all_interactions_equivalent:
            branch = "CAP_MATERIAL_BUT_COMPARISON_STABLE"
        elif all_absolute_equivalent and all_interactions_equivalent:
            branch = "NO_MEANINGFUL_CAP_EFFECT_DEMONSTRATED"
        else:
            branch = "INCONCLUSIVE_FIXED_N"
        overall_branches.append(branch)
        cells[cell_key] = {
            "source_frozen_64": {
                "result_file": cfg.source_result_file,
                "result_sha256": cfg.source_result_sha256,
                "mean_diff": cfg.source_mean_diff,
                "ci_lo": cfg.source_ci_lo,
                "ci_hi": cfg.source_ci_hi,
                "passed": cfg.source_passed,
            },
            "planning_power": _planning_power(cfg),
            "cap_64_reproduction_gate": {
                "passed": reproduced,
                "requirement": (
                    "per-item prompt and steer correctness arrays must exactly "
                    "match the frozen E-0006 artifact, and the 64-token point/CI/"
                    "pass diagnostic must reproduce, before interpreting cap effects"
                ),
                "n_test_items": len(item_ids),
                "prompt_mismatch_item_ids": prompt_mismatch_ids,
                "steer_mismatch_item_ids": steer_mismatch_ids,
                "aggregate_matches": aggregate_matches,
            },
            "by_cap": cap_rows,
            "paired_cap_comparisons": comparisons,
            "operational_semantic_truncation_evidence_present": (
                semantic_materiality_observed
            ),
            "companion_pass_status_changed": pass_changed,
            "companion_pass_status_branch_role": (
                "reported diagnostic only; it does not trigger the frozen overall "
                "branch outside the 24-estimand max-T family"
            ),
            "outcome_branch": branch,
            "original_result_untouched": True,
        }
    if any(branch == "INVALID_64_NONREPRODUCTION" for branch in overall_branches):
        overall = "INVALID_64_NONREPRODUCTION"
    elif any(
        branch == "DISTORTION_AFFECTS_STEER_VS_PROMPT_COMPARISON"
        for branch in overall_branches
    ):
        overall = "DISTORTION_AFFECTS_STEER_VS_PROMPT_COMPARISON"
    elif any(branch == "INCONCLUSIVE_FIXED_N" for branch in overall_branches):
        overall = "INCONCLUSIVE_FIXED_N"
    elif any(
        branch == "CAP_MATERIAL_BUT_COMPARISON_STABLE"
        for branch in overall_branches
    ):
        overall = "CAP_MATERIAL_BUT_COMPARISON_STABLE"
    else:
        overall = "NO_MEANINGFUL_CAP_EFFECT_DEMONSTRATED"
    return {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utcnow(),
        "valid_for_paper": False,
        "estimand_contract": {
            "unit": "TEST item; each item carries its five frozen samples",
            "caps": list(CAPS),
            "conditions": list(CONDITIONS),
            "primary_contrast": "D_t=accuracy_steer,t-accuracy_prompt,t",
            "cap_effect": "E_c,t=accuracy_c,t-accuracy_c,64",
            "interaction": "I_t=E_steer,t-E_prompt,t=D_t-D_64",
            "primary_family": (
                "24 predeclared E_c,t and I_t estimands: four cells × "
                "(four condition effects + two interactions)"
            ),
            "primary_ci_level": 0.95,
            "primary_multiplicity_method": (
                "joint item-cluster bootstrap max-T simultaneous confidence intervals"
            ),
            "primary_family_size": len(primary_family),
            "diagnostic_ci_level": 0.95,
            "bootstrap_b": bootstrap_b,
            "meaningful_margin": adj.DELTA,
            "equivalence_rule": "entire CI strictly inside [-0.05,+0.05]",
        },
        "stop_definition_contract": {
            "count_equals_cap": (
                "generated token count including a terminal EOS equals the cap; "
                "descriptive only"
            ),
            "mechanical_cap_stop": (
                "no generated EOS and exactly max_new_tokens were consumed"
            ),
            "operational_semantic_truncation": (
                "a mechanically stopped 64-token sequence is an exact prefix of "
                "its same-seed longer continuation and the continuation adds an "
                "explicit/terminal final answer, changes the frozen parser number, "
                "or changes correctness"
            ),
        },
        "primary_multiplicity_family": primary_family,
        "scope": (
            "sensitivity companion on fingerprint-proven historical TEST index "
            "IDs with a revision-pinned reconstructed payload; never replaces "
            "or edits the frozen E-0006 0/12 result"
        ),
        "per_cell_branch_evaluation_order": [
            "INVALID_64_NONREPRODUCTION",
            "DISTORTION_AFFECTS_STEER_VS_PROMPT_COMPARISON",
            "CAP_MATERIAL_BUT_COMPARISON_STABLE",
            "NO_MEANINGFUL_CAP_EFFECT_DEMONSTRATED",
            "INCONCLUSIVE_FIXED_N",
        ],
        "overall_conservative_priority": [
            "INVALID_64_NONREPRODUCTION",
            "DISTORTION_AFFECTS_STEER_VS_PROMPT_COMPARISON",
            "INCONCLUSIVE_FIXED_N",
            "CAP_MATERIAL_BUT_COMPARISON_STABLE",
            "NO_MEANINGFUL_CAP_EFFECT_DEMONSTRATED",
        ],
        "overall_outcome_branch": overall,
        "cells": cells,
    }


def _write_summary(path: Path, analysis: Dict[str, object]) -> None:
    lines = [
        "# E-0017 Deliberation Token-Cap Sensitivity",
        "",
        f"- outcome: **{analysis['overall_outcome_branch']}**",
        "- scope: recovered historical TEST index IDs on a pinned reconstructed payload; frozen E-0006 0/12 is unchanged.",
        "- mechanical cap stop is exact from generated token IDs and EOS; it is not, by itself, semantic truncation.",
        "",
        "| cell | 64 reproduction | 64/128/256 companion pass | branch |",
        "|---|---|---|---|",
    ]
    for cell_key, row in analysis["cells"].items():
        passes = "/".join(
            "Y" if row["by_cap"][str(cap)]["frozen_axis_pass_rule_applied_as_companion"] else "n"
            for cap in CAPS
        )
        lines.append(
            f"| {cell_key} | {row['cap_64_reproduction_gate']['passed']} | "
            f"{passes} | {row['outcome_branch']} |"
        )
    _write_text_atomic(path, "\n".join(lines) + "\n")


def _implementation_lineage() -> Dict[str, str]:
    paths = (
        Path(__file__).resolve(),
        _REPO / "src" / "cognitive_console" / "steering" / "generate.py",
        _REPO / "src" / "cognitive_console" / "experiments" / "adjudicate_c2b.py",
        _REPO / "src" / "cognitive_console" / "eval" / "scorers.py",
        _REPO / "src" / "cognitive_console" / "eval" / "c2b_tasks.py",
        _REPO / "scripts" / "run_c1_facade.py",
        _REPO / "scripts" / "run_gpu_phase0.py",
    )
    return {_rel(path): _sha256_file(path) for path in paths}


def _file_identity(path: Path, *, logical_name: Optional[str] = None) -> Dict[str, object]:
    return {
        "name": logical_name or path.name,
        "size_bytes": path.stat().st_size,
        "sha256": _sha256_file(path),
    }


def _hash_model_snapshot(
    snapshot_path: Path,
    *,
    repo_id: str,
    revision: str,
) -> Dict[str, object]:
    snapshot = Path(snapshot_path).resolve()
    if not snapshot.is_dir() or snapshot.name != revision:
        raise ValueError(
            f"{repo_id}@{revision}: resolved snapshot path must end in the "
            "full pinned revision"
        )
    required_metadata = (
        "config.json",
        "generation_config.json",
        "tokenizer_config.json",
    )
    for name in required_metadata:
        if not (snapshot / name).is_file():
            raise ValueError(f"{repo_id}@{revision}: missing required {name}")
    tokenizer_candidates = sorted(
        {
            path.name
            for pattern in (
                "tokenizer*",
                "special_tokens_map.json",
                "added_tokens.json",
                "chat_template.jinja",
            )
            for path in snapshot.glob(pattern)
            if path.is_file()
        }
    )
    if not any(name in tokenizer_candidates for name in ("tokenizer.json", "tokenizer.model")):
        raise ValueError(f"{repo_id}@{revision}: tokenizer payload is incomplete")
    metadata_names = sorted(
        set(required_metadata)
        | set(tokenizer_candidates)
        | {
            name
            for name in (
                "special_tokens_map.json",
                "added_tokens.json",
                "chat_template.jinja",
                "model.safetensors.index.json",
            )
            if (snapshot / name).is_file()
        }
    )
    index_path = snapshot / "model.safetensors.index.json"
    shard_names: List[str]
    if index_path.is_file():
        index = json.loads(index_path.read_text(encoding="utf-8"))
        weight_map = dict(index.get("weight_map") or {})
        if not weight_map:
            raise ValueError(f"{index_path}: missing weight_map")
        shard_names = sorted({str(value) for value in weight_map.values()})
        if any(
            Path(name).name != name
            or "/" in name
            or "\\" in name
            or not name.endswith(".safetensors")
            for name in shard_names
        ):
            raise ValueError(f"{index_path}: unsafe weight shard reference")
    else:
        shard_names = [
            path.name
            for path in sorted(snapshot.glob("*.safetensors"))
            if path.is_file()
        ]
        if shard_names != ["model.safetensors"]:
            raise ValueError(
                f"{repo_id}@{revision}: unindexed snapshot must contain exactly "
                "model.safetensors"
            )
    actual_shards = {
        path.name
        for path in snapshot.glob("*.safetensors")
        if path.is_file()
    }
    if set(shard_names) != actual_shards:
        raise ValueError(
            f"{repo_id}@{revision}: weight index/shard set mismatch"
        )
    metadata = [
        _file_identity(snapshot / name, logical_name=name)
        for name in metadata_names
    ]
    weights = [
        _file_identity(snapshot / name, logical_name=name)
        for name in shard_names
    ]
    return {
        "schema_version": MODEL_IDENTITY_SCHEMA_VERSION,
        "repo_id": repo_id,
        "revision": revision,
        "snapshot_path": str(snapshot),
        "metadata_files": metadata,
        "weight_shards": weights,
        "weight_bytes": sum(int(row["size_bytes"]) for row in weights),
        "all_weight_shards_hashed": True,
    }


def _resolve_model_artifact(
    *,
    model_label: str,
    repo_id: str,
    revision: str,
    hf_home: Optional[str],
) -> ModelArtifact:
    expected = MODEL_SPECS[model_label]
    if repo_id != expected["repo_id"] or revision != expected["revision"]:
        raise SystemExit(
            f"{model_label}: only exact pinned identity "
            f"{expected['repo_id']}@{expected['revision']} is accepted"
        )
    try:
        from huggingface_hub import snapshot_download
    except ImportError as exc:
        raise SystemExit(
            "E-0017 model identity resolution requires huggingface_hub"
        ) from exc
    snapshot = snapshot_download(
        repo_id=repo_id,
        revision=revision,
        cache_dir=(str(Path(hf_home).resolve() / "hub") if hf_home else None),
        local_files_only=True,
    )
    identity = _hash_model_snapshot(
        Path(snapshot),
        repo_id=repo_id,
        revision=revision,
    )
    identity_sha256 = _canonical_json_hash(identity)
    return ModelArtifact(
        model_label=model_label,
        repo_id=repo_id,
        revision=revision,
        snapshot_path=str(Path(snapshot).resolve()),
        identity=identity,
        identity_sha256=identity_sha256,
    )


def _parse_utc_timestamp(value: object, *, field: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError(f"{field} must be an ISO-8601 UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError(f"{field} is not a valid timestamp") from exc
    return parsed.astimezone(timezone.utc)


def _require_normalized_identifier(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise SystemExit(f"{field} must be a string")
    normalized = unicodedata.normalize("NFKC", value).strip()
    if (
        not normalized
        or normalized != value
        or any(unicodedata.category(char).startswith("C") for char in normalized)
    ):
        raise SystemExit(f"{field} must be non-empty and already normalized")
    return normalized


def _load_run_authorization(
    path: Path,
    *,
    source_commit: str,
    preregistration: Dict[str, object],
    out_dir: Path,
    registry_path: Path,
    frozen_root: Path,
) -> Tuple[Dict[str, object], str]:
    auth_path = Path(path).resolve()
    if not auth_path.is_file():
        raise SystemExit(f"E-0017 authorization file is missing: {auth_path}")
    payload = json.loads(auth_path.read_text(encoding="utf-8"))
    expected_top = {
        "schema_version",
        "experiment_id",
        "status",
        "issued_at",
        "expires_at",
        "protocol_freeze",
        "independent_audit",
        "owner_authorization",
        "designated_host",
        "model_pins",
        "dataset_pin",
        "frozen_artifacts",
    }
    if not isinstance(payload, dict) or set(payload) != expected_top:
        raise SystemExit("E-0017 authorization schema mismatch")
    if (
        payload["schema_version"] != AUTHORIZATION_SCHEMA_VERSION
        or payload["experiment_id"] != EXPERIMENT_ID
        or payload["status"] != "AUTHORIZED_FOR_ONE_CANONICAL_ATTEMPT"
    ):
        raise SystemExit("E-0017 authorization status mismatch")
    issued_at = _parse_utc_timestamp(payload["issued_at"], field="issued_at")
    expires_at = _parse_utc_timestamp(payload["expires_at"], field="expires_at")
    now = datetime.now(timezone.utc)
    if not issued_at <= now < expires_at:
        raise SystemExit("E-0017 authorization is not currently valid")

    freeze = dict(payload["protocol_freeze"])
    if set(freeze) != {"prereg_path", "prereg_sha256", "status"}:
        raise SystemExit("E-0017 protocol-freeze schema mismatch")
    if (
        freeze["prereg_path"] != _rel(PREREG_PATH)
        or freeze["prereg_sha256"] != preregistration["sha256"]
        or freeze["status"] != "FROZEN"
        or preregistration["frozen"] is not True
    ):
        raise SystemExit("E-0017 protocol freeze does not bind the current preregistration")

    audit = dict(payload["independent_audit"])
    if set(audit) != {
        "audit_record_id",
        "auditor_id",
        "auditor_role",
        "verdict",
        "audited_run_commit",
    }:
        raise SystemExit("E-0017 independent-audit schema mismatch")
    _require_normalized_identifier(
        audit["audit_record_id"],
        field="independent_audit.audit_record_id",
    )
    auditor_id = _require_normalized_identifier(
        audit["auditor_id"],
        field="independent_audit.auditor_id",
    )
    if (
        audit["auditor_role"] != "independent_hostile_auditor"
        or audit["verdict"] != "FREEZE_RECOMMENDED"
        or audit["audited_run_commit"] != source_commit
        or not re.fullmatch(r"[0-9a-f]{40}", str(audit["audited_run_commit"]))
        or auditor_id.casefold() == OWNER_IDENTITY.casefold()
    ):
        raise SystemExit("E-0017 current run commit lacks an independent freeze recommendation")

    owner = dict(payload["owner_authorization"])
    if set(owner) != {
        "authorization_id",
        "authorized_by",
        "authorized_at",
        "audited_run_commit",
        "max_gpu_hours",
        "approved_gpu_uuid",
        "approved_gpu_name",
    }:
        raise SystemExit("E-0017 owner-authorization schema mismatch")
    _parse_utc_timestamp(owner["authorized_at"], field="authorized_at")
    _require_normalized_identifier(
        owner["authorization_id"],
        field="owner_authorization.authorization_id",
    )
    if (
        owner["authorized_by"] != OWNER_IDENTITY
        or owner["audited_run_commit"] != source_commit
        or auditor_id.casefold() == str(owner["authorized_by"]).casefold()
        or not (0.0 < float(owner["max_gpu_hours"]) <= 3.0)
        or not re.fullmatch(r"GPU-[0-9A-Fa-f-]+", str(owner["approved_gpu_uuid"]))
        or "A800" not in str(owner["approved_gpu_name"]).upper()
    ):
        raise SystemExit("E-0017 owner GPU/budget authorization mismatch")

    designated = dict(payload["designated_host"])
    if set(designated) != {"hostname", "canonical_out_dir"}:
        raise SystemExit("E-0017 designated-host schema mismatch")
    expected_out = Path(str(designated["canonical_out_dir"]))
    validated_out, validated_registry = _validate_control_paths(
        out_dir=expected_out,
        registry_path=registry_path,
        frozen_root=frozen_root,
    )
    if (
        validated_out != out_dir.resolve()
        or validated_registry != _canonical_attempt_registry_path(source_commit)
        or str(designated["hostname"]) != socket.gethostname()
    ):
        raise SystemExit("E-0017 invocation is not on the authorized canonical host/path")

    if payload["model_pins"] != MODEL_SPECS:
        raise SystemExit("E-0017 authorization model pins mismatch")
    if payload["frozen_artifacts"] != _pinned_frozen_artifact_identity():
        raise SystemExit("E-0017 authorization frozen-artifact pins mismatch")
    if payload["dataset_pin"] != {
        "repo_id": "openai/gsm8k",
        "config": "main",
        "split": "test",
        "revision": GSM8K_REVISION,
        "item_identity_sha256": _sha256_file(ITEM_IDENTITY_PATH),
    }:
        raise SystemExit("E-0017 authorization dataset/item identity mismatch")
    return payload, _sha256_file(auth_path)


def _run_nvidia_smi(*args: str) -> str:
    completed = subprocess.run(
        ["nvidia-smi", *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "nvidia-smi failed: "
            + (completed.stderr.strip() or completed.stdout.strip())
        )
    return completed.stdout.strip()


def _parse_gpu_inventory(text: str) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for row in csv.reader(StringIO(text)):
        if not row:
            continue
        if len(row) != 6:
            raise ValueError("unexpected nvidia-smi GPU inventory row")
        index, uuid, name, total, used, utilization = [value.strip() for value in row]
        rows.append(
            {
                "index": int(index),
                "uuid": uuid,
                "name": name,
                "memory_total_mib": int(total),
                "memory_used_mib": int(used),
                "utilization_gpu_pct": int(utilization),
            }
        )
    return rows


def _query_gpu_state() -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    inventory = _parse_gpu_inventory(
        _run_nvidia_smi(
            "--query-gpu=index,uuid,name,memory.total,memory.used,utilization.gpu",
            "--format=csv,noheader,nounits",
        )
    )
    process_text = _run_nvidia_smi(
        "--query-compute-apps=gpu_uuid,pid,process_name,used_gpu_memory",
        "--format=csv,noheader,nounits",
    )
    processes: List[Dict[str, object]] = []
    if process_text and "No running processes found" not in process_text:
        for row in csv.reader(StringIO(process_text)):
            if len(row) != 4:
                raise ValueError("unexpected nvidia-smi compute-process row")
            gpu_uuid, pid, process_name, used = [value.strip() for value in row]
            processes.append(
                {
                    "gpu_uuid": gpu_uuid,
                    "pid": int(pid),
                    "process_name": process_name,
                    "used_gpu_memory_mib": int(used),
                }
            )
    return inventory, processes


def _verify_idle_a800(authorization: Dict[str, object]) -> Dict[str, object]:
    owner = dict(authorization["owner_authorization"])
    expected_uuid = str(owner["approved_gpu_uuid"])
    expected_name = str(owner["approved_gpu_name"])
    if os.environ.get("CUDA_VISIBLE_DEVICES") != expected_uuid:
        raise RuntimeError(
            "CUDA_VISIBLE_DEVICES must be the single authorized GPU UUID, not an "
            "index, list, or basename"
        )
    if os.environ.get("CUDA_DEVICE_ORDER") != "PCI_BUS_ID":
        raise RuntimeError("CUDA_DEVICE_ORDER=PCI_BUS_ID is required")
    if os.environ.get("TRANSFORMERS_OFFLINE", "").lower() not in {"1", "true"}:
        raise RuntimeError("TRANSFORMERS_OFFLINE=1 is required for the pinned run")
    observations: List[Dict[str, object]] = []
    for check_index in range(2):
        inventory, processes = _query_gpu_state()
        matches = [gpu for gpu in inventory if gpu["uuid"] == expected_uuid]
        if len(matches) != 1:
            raise RuntimeError("authorized GPU UUID is not uniquely present")
        gpu = matches[0]
        active = [
            process for process in processes
            if process["gpu_uuid"] == expected_uuid
        ]
        if (
            gpu["name"] != expected_name
            or "A800" not in str(gpu["name"]).upper()
            or active
            or int(gpu["memory_used_mib"]) > GPU_IDLE_MAX_MEMORY_MIB
            or int(gpu["utilization_gpu_pct"]) > GPU_IDLE_MAX_UTILIZATION_PCT
        ):
            raise RuntimeError(
                "authorized A800 is not idle under the frozen threat model"
            )
        observations.append(
            {
                "checked_at": utcnow(),
                "gpu": gpu,
                "compute_processes": active,
            }
        )
        if check_index == 0:
            time.sleep(2.0)
    try:
        import torch
    except ImportError as exc:
        raise RuntimeError("E-0017 requires CUDA torch; CPU fallback is forbidden") from exc
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise RuntimeError("E-0017 requires exactly one visible CUDA device")
    torch_name = str(torch.cuda.get_device_name(0))
    if torch_name != expected_name or "A800" not in torch_name.upper():
        raise RuntimeError("torch CUDA device does not match the authorized A800")
    return {
        "gpu_uuid": expected_uuid,
        "gpu_name": expected_name,
        "cuda_visible_devices": os.environ["CUDA_VISIBLE_DEVICES"],
        "cuda_device_order": os.environ["CUDA_DEVICE_ORDER"],
        "torch_device_count": int(torch.cuda.device_count()),
        "torch_device_name": torch_name,
        "required_dtype": "float16",
        "idle_thresholds": {
            "max_memory_used_mib": GPU_IDLE_MAX_MEMORY_MIB,
            "max_utilization_gpu_pct": GPU_IDLE_MAX_UTILIZATION_PCT,
            "compute_processes": 0,
        },
        "observations": observations,
        "threat_model": (
            "Enforces one UUID-selected A800, two idle observations, no visible "
            "compute process, bounded memory/utilization, and a host-global lock. "
            "It prevents cooperative cross-output retries and accidental CPU/GPU "
            "fallback; it cannot stop a privileged external process from starting "
            "after the final idle observation."
        ),
    }


def _verify_backend_cuda_float16(backend) -> Dict[str, object]:
    backend._ensure_loaded()
    floating_dtypes = set()
    devices = set()
    parameter_count = 0
    for parameter in backend._model.parameters():
        parameter_count += int(parameter.numel())
        devices.add(str(parameter.device))
        if getattr(parameter, "is_floating_point", lambda: False)():
            floating_dtypes.add(str(parameter.dtype))
    if not devices or any(not device.startswith("cuda:0") for device in devices):
        raise RuntimeError("model parameters are not exclusively on cuda:0")
    if floating_dtypes != {"torch.float16"}:
        raise RuntimeError(
            f"model floating dtypes are not exclusively float16: {floating_dtypes}"
        )
    return {
        "parameter_count": parameter_count,
        "parameter_devices": sorted(devices),
        "floating_parameter_dtypes": sorted(floating_dtypes),
        "eval_mode": not bool(backend._model.training),
    }


class CanonicalAttemptRegistry:
    def __init__(
        self,
        *,
        authorization: Dict[str, object],
        authorization_sha256: str,
        source_commit: str,
        out_dir: Path,
        frozen_root: Path,
    ) -> None:
        canonical_registry = _canonical_attempt_registry_path(source_commit)
        validated_out, validated_registry = _validate_control_paths(
            out_dir=out_dir,
            registry_path=canonical_registry,
            frozen_root=frozen_root,
        )
        self.path = validated_registry
        self.lock_path = Path(str(self.path) + ".lock")
        self.authorization = authorization
        self.authorization_sha256 = authorization_sha256
        self.source_commit = source_commit
        self.out_dir = validated_out
        self._handle = None
        self._active_invocation_id: Optional[str] = None
        self.already_complete = False

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = open(self.lock_path, "a+b")
        self._handle.seek(0, os.SEEK_END)
        if self._handle.tell() == 0:
            self._handle.write(b"\0")
            self._handle.flush()
        self._handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(self._handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(self._handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (OSError, ImportError) as exc:
            self._handle.close()
            self._handle = None
            raise RuntimeError("another E-0017 canonical attempt is active") from exc

    def release(self) -> None:
        if self._handle is None:
            return
        try:
            self._handle.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(self._handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)
        finally:
            self._handle.close()
            self._handle = None

    def _identity(self) -> Dict[str, object]:
        owner = dict(self.authorization["owner_authorization"])
        designated = dict(self.authorization["designated_host"])
        return {
            "experiment_id": EXPERIMENT_ID,
            "authorization_id": owner["authorization_id"],
            "authorization_sha256": self.authorization_sha256,
            "audited_run_commit": self.source_commit,
            "designated_hostname": designated["hostname"],
            "approved_gpu_uuid": owner["approved_gpu_uuid"],
            "canonical_out_dir": str(self.out_dir),
            "canonical_registry_path": str(self.path),
        }

    def start(self) -> Dict[str, object]:
        if self._handle is None:
            raise RuntimeError("attempt registry lock is not held")
        identity = self._identity()
        if self.path.exists():
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            if (
                payload.get("schema_version") != ATTEMPT_REGISTRY_SCHEMA_VERSION
                or payload.get("identity") != identity
                or payload.get("valid_for_paper") is not False
            ):
                raise RuntimeError(
                    "canonical attempt registry identity mismatch; cross-out-dir "
                    "or reauthorized retries are forbidden"
                )
            if payload.get("status") == "COMPLETE":
                self.already_complete = True
                return payload
            if payload.get("status") not in {"STARTED", "FAILED"}:
                raise RuntimeError("canonical attempt registry has invalid status")
        else:
            payload = {
                "schema_version": ATTEMPT_REGISTRY_SCHEMA_VERSION,
                "identity": identity,
                "status": None,
                "first_started_at": utcnow(),
                "invocations": [],
                "failures": [],
                "seal_binding": None,
                "valid_for_paper": False,
            }
        invocation_id = f"{socket.gethostname()}:{os.getpid()}:{time.time_ns()}"
        payload["status"] = "STARTED"
        payload["last_started_at"] = utcnow()
        payload["invocations"].append(
            {
                "invocation_id": invocation_id,
                "pid": os.getpid(),
                "started_at": payload["last_started_at"],
            }
        )
        self._active_invocation_id = invocation_id
        _write_json(self.path, payload)
        return payload

    def bind_run_config(self, run_config_sha256: str) -> None:
        if self.already_complete:
            return
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if payload.get("status") != "STARTED":
            raise RuntimeError("attempt registry is not STARTED")
        existing = payload.get("run_config_sha256")
        if existing not in {None, run_config_sha256}:
            raise RuntimeError("canonical attempt run-config drift")
        payload["run_config_sha256"] = run_config_sha256
        _write_json(self.path, payload)

    def assert_budget(self) -> None:
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        started = datetime.fromisoformat(str(payload["first_started_at"]))
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
        elapsed_hours = (
            datetime.now(timezone.utc) - started.astimezone(timezone.utc)
        ).total_seconds() / 3600.0
        max_hours = float(
            self.authorization["owner_authorization"]["max_gpu_hours"]
        )
        if elapsed_hours > max_hours:
            raise RuntimeError(
                f"E-0017 authorized GPU budget exceeded: "
                f"{elapsed_hours:.3f}h > {max_hours:.3f}h"
            )

    def mark_failed(self, exc: BaseException) -> None:
        if self.already_complete or not self.path.exists():
            return
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if payload.get("status") != "STARTED":
            return
        payload["status"] = "FAILED"
        payload["failed_at"] = utcnow()
        failure = {
            "invocation_id": self._active_invocation_id,
            "type": type(exc).__name__,
            "message": str(exc)[:2000],
        }
        payload["last_failure"] = failure
        payload.setdefault("failures", []).append(
            {**failure, "failed_at": payload["failed_at"]}
        )
        _write_json(self.path, payload)

    def mark_complete(self, seal_binding: Dict[str, object]) -> None:
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if payload.get("status") == "COMPLETE":
            if payload.get("seal_binding") != seal_binding:
                raise RuntimeError("completed canonical attempt seal drift")
            self.already_complete = True
            return
        if payload.get("status") != "STARTED":
            raise RuntimeError("attempt registry must be STARTED before COMPLETE")
        payload["status"] = "COMPLETE"
        payload["completed_at"] = utcnow()
        payload["seal_binding"] = seal_binding
        _write_json(self.path, payload)
        self.already_complete = True


_ACTIVE_ATTEMPT_REGISTRY: Optional[CanonicalAttemptRegistry] = None


def _raw_input_manifest(
    *,
    out_dir: Path,
    run_config_sha256: str,
    frozen_lineage: Dict[str, object],
) -> Dict[str, object]:
    sample_paths = sorted((out_dir / "samples").glob("*.jsonl"))
    direction_paths = sorted(out_dir.glob("cell_*/direction_manifest.json"))
    if len(sample_paths) != len(FROZEN_CELL_KEYS) * len(CAPS) * len(CONDITIONS):
        raise ValueError("E-0017 cannot lock TEST analysis before all sample files exist")
    if len(direction_paths) != len(FROZEN_CELL_KEYS):
        raise ValueError("E-0017 cannot lock TEST analysis without four direction manifests")
    return {
        "run_config_sha256": run_config_sha256,
        "frozen_lineage": frozen_lineage,
        "sample_files": [
            {
                "path": _rel(path),
                "sha256": _sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
            for path in sample_paths
        ],
        "direction_manifests": [
            {"path": _rel(path), "sha256": _sha256_file(path)}
            for path in direction_paths
        ],
    }


def _prepare_test_once_analysis(
    *,
    seal_path: Path,
    raw_inputs: Dict[str, object],
    analysis_spec: Dict[str, object],
    analysis_path: Path,
    summary_path: Path,
    manifest_path: Path,
) -> Optional[Dict[str, object]]:
    raw_sha = _canonical_json_hash(raw_inputs)
    spec_sha = _canonical_json_hash(analysis_spec)
    if not seal_path.exists():
        orphaned = [
            path
            for path in (analysis_path, summary_path, manifest_path)
            if path.exists()
        ]
        if orphaned:
            raise ValueError(
                "analysis artifacts exist without a TEST-once seal: "
                + ", ".join(str(path) for path in orphaned)
            )
        _write_json(
            seal_path,
            {
                "schema_version": TEST_ONCE_SCHEMA_VERSION,
                "experiment_id": EXPERIMENT_ID,
                "status": "LOCKED",
                "locked_at": utcnow(),
                "raw_inputs": raw_inputs,
                "raw_inputs_sha256": raw_sha,
                "analysis_spec": analysis_spec,
                "analysis_spec_sha256": spec_sha,
                "outputs": None,
                "valid_for_paper": False,
            },
        )
        return None

    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    if (
        seal.get("schema_version") != TEST_ONCE_SCHEMA_VERSION
        or seal.get("experiment_id") != EXPERIMENT_ID
        or seal.get("raw_inputs") != raw_inputs
        or seal.get("raw_inputs_sha256") != raw_sha
        or seal.get("analysis_spec") != analysis_spec
        or seal.get("analysis_spec_sha256") != spec_sha
        or seal.get("valid_for_paper") is not False
    ):
        raise ValueError("TEST-once seal identity mismatch; TEST inputs may not change")
    status = seal.get("status")
    if status == "COMPLETE":
        outputs = dict(seal.get("outputs") or {})
        for key, path in (
            ("analysis_json", analysis_path),
            ("analysis_md", summary_path),
            ("run_manifest", manifest_path),
        ):
            expected = dict(outputs.get(key) or {})
            if (
                not path.exists()
                or expected.get("path") != _rel(path)
                or expected.get("sha256") != _sha256_file(path)
            ):
                raise ValueError(f"completed TEST-once output mismatch: {key}")
        return json.loads(analysis_path.read_text(encoding="utf-8"))
    if status == "ANALYZED":
        if (
            not analysis_path.exists()
            or seal.get("analysis_json_sha256") != _sha256_file(analysis_path)
        ):
            raise ValueError("ANALYZED TEST-once artifact hash mismatch")
        return json.loads(analysis_path.read_text(encoding="utf-8"))
    if status != "LOCKED":
        raise ValueError(f"unknown TEST-once seal status: {status!r}")
    if analysis_path.exists():
        raise ValueError(
            "LOCKED TEST-once seal cannot adopt an existing analysis.json; "
            "the canonical attempt is invalidated rather than blessing an "
            "unsealed analysis artifact"
        )
    return None


def _mark_test_once_analysis_written(*, seal_path: Path, analysis_path: Path) -> None:
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    if seal.get("status") != "LOCKED":
        raise ValueError("TEST-once seal must be LOCKED when analysis is first written")
    seal["status"] = "ANALYZED"
    seal["analysis_written_at"] = utcnow()
    seal["analysis_json_sha256"] = _sha256_file(analysis_path)
    _write_json(seal_path, seal)


def _complete_test_once_analysis(
    *,
    seal_path: Path,
    analysis_path: Path,
    summary_path: Path,
    manifest_path: Path,
) -> None:
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    if seal.get("status") != "ANALYZED":
        raise ValueError("TEST-once seal must be ANALYZED before completion")
    if seal.get("analysis_json_sha256") != _sha256_file(analysis_path):
        raise ValueError("TEST-once analysis changed before completion")
    seal["status"] = "COMPLETE"
    seal["completed_at"] = utcnow()
    seal["outputs"] = {
        "analysis_json": {
            "path": _rel(analysis_path),
            "sha256": _sha256_file(analysis_path),
        },
        "analysis_md": {
            "path": _rel(summary_path),
            "sha256": _sha256_file(summary_path),
        },
        "run_manifest": {
            "path": _rel(manifest_path),
            "sha256": _sha256_file(manifest_path),
        },
    }
    _write_json(seal_path, seal)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="E-0017 frozen-config deliberation 64/128/256 sensitivity"
    )
    parser.add_argument("--frozen-root", default=str(DEFAULT_FROZEN_ROOT))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--qwen-model", default=DEFAULT_QWEN_MODEL)
    parser.add_argument("--qwen-revision", default=DEFAULT_QWEN_REVISION)
    parser.add_argument("--llama-model", default=DEFAULT_LLAMA_MODEL)
    parser.add_argument("--llama-revision", default=DEFAULT_LLAMA_REVISION)
    parser.add_argument("--caps", nargs="+", type=int, default=list(CAPS))
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--n-extraction", type=int, default=DEFAULT_N_EXTRACTION)
    parser.add_argument("--bootstrap-b", type=int, default=adj.BOOTSTRAP_B)
    parser.add_argument("--hf-home", default=None)
    parser.add_argument("--venv", default=None)
    parser.add_argument("--disk-budget-gb", type=float, default=DEFAULT_DISK_BUDGET_GB)
    parser.add_argument(
        "--disk-ceiling-gb", type=float, default=DEFAULT_DISK_CEILING_GB
    )
    parser.add_argument("--min-free-gb", type=float, default=DEFAULT_MIN_FREE_GB)
    parser.add_argument("--authorization-file", default=None)
    parser.add_argument("--confirm-frozen-test-once", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def _validate_args(args) -> None:
    mismatches = []
    if tuple(args.caps) != CAPS:
        mismatches.append(f"--caps={args.caps!r} expected {list(CAPS)!r}")
    if args.seed != DEFAULT_SEED:
        mismatches.append(f"--seed={args.seed!r} expected {DEFAULT_SEED!r}")
    if args.temperature != DEFAULT_TEMPERATURE:
        mismatches.append(
            f"--temperature={args.temperature!r} expected {DEFAULT_TEMPERATURE!r}"
        )
    if args.batch_size != DEFAULT_BATCH_SIZE:
        mismatches.append(
            f"--batch-size={args.batch_size!r} expected {DEFAULT_BATCH_SIZE!r}"
        )
    if args.n_extraction != DEFAULT_N_EXTRACTION:
        mismatches.append(
            f"--n-extraction={args.n_extraction!r} expected {DEFAULT_N_EXTRACTION!r}"
        )
    if args.bootstrap_b != adj.BOOTSTRAP_B:
        mismatches.append(
            f"--bootstrap-b={args.bootstrap_b!r} expected {adj.BOOTSTRAP_B!r}"
        )
    if args.disk_budget_gb <= 0:
        mismatches.append("--disk-budget-gb must be positive")
    if args.disk_ceiling_gb < args.disk_budget_gb:
        mismatches.append("--disk-ceiling-gb must be >= --disk-budget-gb")
    if args.min_free_gb <= 0:
        mismatches.append("--min-free-gb must be positive")
    if args.qwen_model != DEFAULT_QWEN_MODEL:
        mismatches.append(
            f"--qwen-model={args.qwen_model!r} expected {DEFAULT_QWEN_MODEL!r}"
        )
    if args.qwen_revision != DEFAULT_QWEN_REVISION:
        mismatches.append(
            "--qwen-revision must equal the preregistered full commit SHA"
        )
    if args.llama_model != DEFAULT_LLAMA_MODEL:
        mismatches.append(
            f"--llama-model={args.llama_model!r} expected {DEFAULT_LLAMA_MODEL!r}"
        )
    if args.llama_revision != DEFAULT_LLAMA_REVISION:
        mismatches.append(
            "--llama-revision must equal the preregistered full commit SHA"
        )
    if not args.dry_run and not args.confirm_frozen_test_once:
        mismatches.append(
            "real run requires --confirm-frozen-test-once after protocol freeze/approval"
        )
    if not args.dry_run and not args.authorization_file:
        mismatches.append("real run requires --authorization-file")
    if mismatches:
        raise SystemExit("E-0017 frozen companion identity mismatch: " + ", ".join(mismatches))


def _requested_model_pin(args, model_label: str) -> Dict[str, str]:
    if model_label == "qwen2.5-7b":
        return {
            "repo_id": str(args.qwen_model),
            "revision": str(args.qwen_revision),
        }
    if model_label == "llama3-8b":
        return {
            "repo_id": str(args.llama_model),
            "revision": str(args.llama_revision),
        }
    raise ValueError(f"unsupported model label: {model_label}")


def _direction_manifest(
    *,
    cfg: FrozenCellConfig,
    model_id: str,
    seed: int,
    n_extraction: int,
    run_config_sha256: str,
    derivation: Dict[str, object],
) -> Dict[str, object]:
    return {
        "experiment_id": EXPERIMENT_ID,
        "cell": cfg.cell_key,
        "method": cfg.method,
        "model_label": cfg.model_label,
        "model_id": model_id,
        "layer": cfg.layer,
        "seed": int(seed),
        "n_extraction": int(n_extraction),
        "source_result_file": cfg.source_result_file,
        "source_result_sha256": cfg.source_result_sha256,
        "source_config_fingerprint": cfg.source_config_fingerprint,
        "run_config_sha256": run_config_sha256,
        "derivation": derivation,
        "valid_for_paper": False,
    }


def _checkpoint_identity(
    *,
    cfg: FrozenCellConfig,
    model_id: str,
    cap: int,
    condition: str,
    seed: int,
    temperature: float,
    batch_size: int,
    run_config_sha256: str,
    direction_sha256: str,
) -> Dict[str, object]:
    instruction, requested_alpha, effective_alpha = _condition_instruction_and_alpha(
        cfg, condition
    )
    return {
        "experiment_id": EXPERIMENT_ID,
        "cell": cfg.cell_key,
        "model_id": model_id,
        "condition": condition,
        "max_new_tokens": int(cap),
        "seed": int(seed),
        "temperature": float(temperature),
        "batch_size": int(batch_size),
        "k_samples": adj.K_SAMPLES,
        "layer": cfg.layer,
        "requested_alpha": requested_alpha,
        "effective_alpha": effective_alpha,
        "instruction_sha256": _sha256_text(instruction),
        "source_result_sha256": cfg.source_result_sha256,
        "source_config_fingerprint": cfg.source_config_fingerprint,
        "direction_sha256": direction_sha256,
        "run_config_sha256": run_config_sha256,
    }


def _main(argv: Optional[List[str]] = None) -> int:
    global _ACTIVE_ATTEMPT_REGISTRY

    args = build_parser().parse_args(argv)
    _validate_args(args)
    frozen_root, frozen_artifact_pins = _verify_pinned_frozen_root(
        Path(args.frozen_root)
    )
    out_dir = _validate_external_control_path(
        Path(args.out_dir),
        label="output directory",
        frozen_root=frozen_root,
    )
    preregistration = _preregistration_identity(require_frozen=not args.dry_run)
    configs = {
        cell_key: load_frozen_cell_config(frozen_root, cell_key)
        for cell_key in FROZEN_CELL_KEYS
    }
    frozen_lineage = frozen_lineage_inventory(
        frozen_root, configs, seed=args.seed
    )
    test_items, item_identity = load_test_items(seed=args.seed)
    if len(test_items) != 40:
        raise SystemExit(f"E-0017 expected 40 TEST items, got {len(test_items)}")
    requested_model_pins = {
        label: _requested_model_pin(args, label)
        for label in MODEL_SPECS
    }
    model_artifacts: Dict[str, ModelArtifact] = {}
    inventory = {
        "experiment_id": EXPERIMENT_ID,
        "cells": {
            cell_key: {
                "model": {
                    **requested_model_pins[cfg.model_label],
                    "canonical_id": (
                        f"{requested_model_pins[cfg.model_label]['repo_id']}@"
                        f"{requested_model_pins[cfg.model_label]['revision']}"
                    ),
                    "resolved_identity": None,
                },
                "layer": cfg.layer,
                "frozen_alpha": cfg.frozen_alpha,
                "effective_alpha": _condition_instruction_and_alpha(
                    cfg, "steer"
                )[2],
                "best_prompt_id": cfg.best_prompt_id,
                "best_prompt_sha256": _sha256_text(cfg.best_prompt_text),
                "neutral_prompt_sha256": _sha256_text(cfg.neutral_prompt),
                "source_result_file": cfg.source_result_file,
                "source_result_sha256": cfg.source_result_sha256,
                "source_config_fingerprint": cfg.source_config_fingerprint,
                "planning_power": _planning_power(cfg),
            }
            for cell_key, cfg in configs.items()
        },
        "caps": list(CAPS),
        "n_test_items": len(test_items),
        "k_samples": adj.K_SAMPLES,
        "conditions": list(CONDITIONS),
        "test_item_ids": [str(item["id"]) for item in test_items],
        "test_items_sha256": _sha256_text(
            json.dumps(test_items, sort_keys=True, ensure_ascii=False)
        ),
        "item_identity": {
            "path": _rel(ITEM_IDENTITY_PATH),
            "sha256": _sha256_file(ITEM_IDENTITY_PATH),
            "status": item_identity["identity_status"],
            "historical_ordered_ids_proven": True,
            "historical_dataset_content_hash_recorded": False,
            "reconstruction_revision": GSM8K_REVISION,
        },
        "frozen_lineage": frozen_lineage,
        "frozen_artifact_pins": frozen_artifact_pins,
        "preregistration": preregistration,
        "implementation_files_sha256": _implementation_lineage(),
        "scorer_contract": {
            "parse": "cognitive_console.eval.scorers.parse_final_number",
            "accuracy": "cognitive_console.eval.scorers.score_deliberation",
            "coherence": "cognitive_console.eval.scorers.degeneracy_score",
        },
        "planned_generations": (
            len(FROZEN_CELL_KEYS)
            * len(CAPS)
            * len(CONDITIONS)
            * len(test_items)
            * adj.K_SAMPLES
        ),
        "worst_case_continuation_token_slots": (
            len(FROZEN_CELL_KEYS)
            * len(CONDITIONS)
            * len(test_items)
            * adj.K_SAMPLES
            * sum(CAPS)
        ),
        "original_e0006_decision": "0/12 and immutable",
    }
    if args.dry_run:
        print(json.dumps(inventory, indent=2))
        return 0

    from cognitive_console.steering.generate import SteeredHFBackend

    if out_dir.exists() and any(out_dir.iterdir()) and not (
        out_dir / "run_config.json"
    ).exists():
        raise SystemExit(
            f"{out_dir}: non-empty output directory lacks E-0017 run_config.json"
        )
    source_state = _git_source_state(out_dir)
    if bool(source_state["dirty"]):
        raise SystemExit(
            "E-0017 real TEST run requires a clean committed tree; "
            f"untracked={source_state['untracked_paths']!r}"
        )
    registry_path = _canonical_attempt_registry_path(str(source_state["head"]))
    out_dir, registry_path = _validate_control_paths(
        out_dir=out_dir,
        registry_path=registry_path,
        frozen_root=frozen_root,
    )
    authorization, authorization_sha256 = _load_run_authorization(
        Path(args.authorization_file),
        source_commit=str(source_state["head"]),
        preregistration=preregistration,
        out_dir=out_dir,
        registry_path=registry_path,
        frozen_root=frozen_root,
    )
    attempt_registry = CanonicalAttemptRegistry(
        authorization=authorization,
        authorization_sha256=authorization_sha256,
        source_commit=str(source_state["head"]),
        out_dir=out_dir,
        frozen_root=frozen_root,
    )
    attempt_registry.acquire()
    _ACTIVE_ATTEMPT_REGISTRY = attempt_registry
    attempt_registry.start()

    for label, pin in requested_model_pins.items():
        model_artifacts[label] = _resolve_model_artifact(
            model_label=label,
            repo_id=pin["repo_id"],
            revision=pin["revision"],
            hf_home=args.hf_home,
        )
    gpu_gate = _verify_idle_a800(authorization)
    for cell_key, cfg in configs.items():
        artifact = model_artifacts[cfg.model_label]
        inventory["cells"][cell_key]["model"]["resolved_identity"] = artifact.identity
        inventory["cells"][cell_key]["model"]["identity_sha256"] = (
            artifact.identity_sha256
        )
    out_dir.mkdir(parents=True, exist_ok=True)
    invocation_started_at = utcnow()
    t0 = time.time()
    disk_checks = [
        _check_runtime_disk(
            out_dir=out_dir,
            hf_home=args.hf_home,
            venv=args.venv,
            budget_gb=args.disk_budget_gb,
            ceiling_gb=args.disk_ceiling_gb,
            min_free_gb=args.min_free_gb,
            label="pre-run",
        )
    ]
    run_config_path = out_dir / "run_config.json"
    run_config = {
        **inventory,
        "seed": args.seed,
        "temperature": args.temperature,
        "batch_size": args.batch_size,
        "n_extraction": args.n_extraction,
        "bootstrap_b": args.bootstrap_b,
        "code_commit": source_state["head"],
        "dirty_tree": False,
        "source_state": source_state,
        "authorization": {
            "authorization_sha256": authorization_sha256,
            "authorization_id": authorization["owner_authorization"][
                "authorization_id"
            ],
            "audit_record_id": authorization["independent_audit"][
                "audit_record_id"
            ],
            "audited_run_commit": authorization["independent_audit"][
                "audited_run_commit"
            ],
            "canonical_attempt_registry": str(attempt_registry.path),
        },
        "gpu_policy": {
            "gpu_uuid": gpu_gate["gpu_uuid"],
            "gpu_name": gpu_gate["gpu_name"],
            "cuda_visible_devices": gpu_gate["cuda_visible_devices"],
            "cuda_device_order": gpu_gate["cuda_device_order"],
            "required_dtype": gpu_gate["required_dtype"],
            "idle_thresholds": gpu_gate["idle_thresholds"],
            "threat_model": gpu_gate["threat_model"],
        },
        "disk_policy": {
            "hf_home": args.hf_home,
            "venv": args.venv,
            "budget_gb": args.disk_budget_gb,
            "ceiling_gb": args.disk_ceiling_gb,
            "min_free_gb": args.min_free_gb,
        },
        "test_once": True,
    }
    run_config_sha256 = _canonical_json_hash(run_config)
    attempt_registry.bind_run_config(run_config_sha256)
    if run_config_path.exists():
        existing = json.loads(run_config_path.read_text(encoding="utf-8"))
        if existing != run_config:
            raise SystemExit(
                f"{run_config_path}: existing run identity differs; use a new out-dir"
            )
    else:
        _write_json(run_config_path, run_config)

    run_state_path = out_dir / "run_state.json"
    if run_state_path.exists():
        run_state = json.loads(run_state_path.read_text(encoding="utf-8"))
        if (
            run_state.get("experiment_id") != EXPERIMENT_ID
            or run_state.get("run_config_sha256") != run_config_sha256
        ):
            raise SystemExit("E-0017 run_state identity mismatch")
    else:
        run_state = {
            "experiment_id": EXPERIMENT_ID,
            "run_config_sha256": run_config_sha256,
            "first_started_at": invocation_started_at,
            "valid_for_paper": False,
        }
    run_state.setdefault("gpu_idle_checks", []).append(gpu_gate)
    _write_json(run_state_path, run_state)

    seal_path = out_dir / "test_once_analysis.json"
    if seal_path.exists():
        expected_sample_count = (
            len(FROZEN_CELL_KEYS) * len(CAPS) * len(CONDITIONS)
        )
        if len(list((out_dir / "samples").glob("*.jsonl"))) != expected_sample_count:
            raise SystemExit(
                "TEST-once analysis was locked before a complete sample bank; "
                "the run is invalid and may not generate further TEST records"
            )

    all_records: List[Dict[str, object]] = []
    direction_meta: Dict[str, object] = {}
    backend_runtime_meta: Dict[str, object] = dict(
        run_state.get("backend_runtime") or {}
    )
    for cell_key in FROZEN_CELL_KEYS:
        cfg = configs[cell_key]
        model_artifact = model_artifacts[cfg.model_label]
        model_id = model_artifact.canonical_id
        model_load_path = model_artifact.snapshot_path
        expected_paths = [
            _records_path(out_dir, cell_key, cap, condition)
            for cap in CAPS
            for condition in CONDITIONS
        ]
        direction_path = out_dir / f"cell_{cell_key}" / "direction_manifest.json"
        if all(path.exists() for path in expected_paths):
            if not direction_path.exists():
                raise SystemExit(
                    f"{cell_key}: complete sample files exist but direction manifest is missing"
                )
            direction_payload = json.loads(
                direction_path.read_text(encoding="utf-8")
            )
            expected_direction_base = _direction_manifest(
                cfg=cfg,
                model_id=model_id,
                seed=args.seed,
                n_extraction=args.n_extraction,
                run_config_sha256=run_config_sha256,
                derivation=dict(direction_payload.get("derivation") or {}),
            )
            if direction_payload != expected_direction_base:
                raise SystemExit(f"{direction_path}: direction identity mismatch")
            direction_sha256 = str(
                dict(direction_payload["derivation"]).get("direction_sha256", "")
            )
            if not direction_sha256:
                raise SystemExit(f"{direction_path}: missing direction_sha256")
            direction_meta[cell_key] = direction_payload
            for cap in CAPS:
                for condition in CONDITIONS:
                    path = _records_path(out_dir, cell_key, cap, condition)
                    checkpoint_path = (
                        out_dir
                        / "checkpoints"
                        / f"{cell_key}__cap{cap}__{condition}.json"
                    )
                    checkpoint_identity = _checkpoint_identity(
                        cfg=cfg,
                        model_id=model_id,
                        cap=cap,
                        condition=condition,
                        seed=args.seed,
                        temperature=args.temperature,
                        batch_size=args.batch_size,
                        run_config_sha256=run_config_sha256,
                        direction_sha256=direction_sha256,
                    )
                    expected_jobs = _expected_condition_jobs(
                        cfg=cfg,
                        model_id=model_id,
                        cap=cap,
                        condition=condition,
                        test_items=test_items,
                        seed=args.seed,
                    )
                    records = _read_jsonl(path)
                    _validate_condition_records(
                        records,
                        cfg=cfg,
                        model_id=model_id,
                        cap=cap,
                        condition=condition,
                        test_items=test_items,
                        seed=args.seed,
                        batch_size=args.batch_size,
                    )
                    checkpoint_records, checkpoint_payload = (
                        _load_condition_checkpoint(
                            checkpoint_path,
                            checkpoint_identity=checkpoint_identity,
                            expected_jobs=expected_jobs,
                            cfg=cfg,
                            model_id=model_id,
                            cap=cap,
                            condition=condition,
                            test_items=test_items,
                            seed=args.seed,
                            batch_size=args.batch_size,
                        )
                    )
                    if checkpoint_records != records or not checkpoint_payload.get(
                        "complete"
                    ):
                        raise SystemExit(
                            f"{checkpoint_path}: complete sample/checkpoint mismatch"
                        )
                    sample_sha = _sha256_file(path)
                    checkpoint_sample_sha = checkpoint_payload.get(
                        "final_sample_sha256"
                    )
                    if checkpoint_sample_sha not in {None, sample_sha}:
                        raise SystemExit(
                            f"{checkpoint_path}: final sample hash mismatch"
                        )
                    if checkpoint_sample_sha is None:
                        _write_json(
                            checkpoint_path,
                            _checkpoint_payload(
                                checkpoint_identity=checkpoint_identity,
                                expected_jobs=expected_jobs,
                                records=records,
                                complete=True,
                                final_sample_sha256=sample_sha,
                            ),
                        )
                    all_records.extend(records)
            continue

        attempt_registry.assert_budget()
        direction, derivation = _derive_hf_direction(
            cfg,
            model_load_path=model_load_path,
            out_dir=out_dir / f"cell_{cell_key}",
            n_extraction=args.n_extraction,
            seed=args.seed,
        )
        attempt_registry.assert_budget()
        direction_payload = _direction_manifest(
            cfg=cfg,
            model_id=model_id,
            seed=args.seed,
            n_extraction=args.n_extraction,
            run_config_sha256=run_config_sha256,
            derivation=derivation,
        )
        if direction_path.exists():
            existing_direction = json.loads(
                direction_path.read_text(encoding="utf-8")
            )
            if existing_direction != direction_payload:
                raise SystemExit(
                    f"{direction_path}: rederived direction does not match checkpoint"
                )
        else:
            _write_json(direction_path, direction_payload)
        direction_meta[cell_key] = direction_payload
        direction_sha256 = str(derivation["direction_sha256"])
        disk_checks.append(
            _check_runtime_disk(
                out_dir=out_dir,
                hf_home=args.hf_home,
                venv=args.venv,
                budget_gb=args.disk_budget_gb,
                ceiling_gb=args.disk_ceiling_gb,
                min_free_gb=args.min_free_gb,
                label=f"post-direction-{cell_key}",
            )
        )
        backend = SteeredHFBackend(
            model_load_path,
            device="cuda:0",
            dtype="float16",
            seed=args.seed,
        )
        try:
            backend_runtime_meta[cell_key] = {
                "model_id": model_id,
                "model_identity_sha256": model_artifact.identity_sha256,
                **_verify_backend_cuda_float16(backend),
            }
            run_state["backend_runtime"] = backend_runtime_meta
            _write_json(run_state_path, run_state)
            for cap in CAPS:
                for condition in CONDITIONS:
                    path = _records_path(out_dir, cell_key, cap, condition)
                    checkpoint_path = (
                        out_dir
                        / "checkpoints"
                        / f"{cell_key}__cap{cap}__{condition}.json"
                    )
                    checkpoint_identity = _checkpoint_identity(
                        cfg=cfg,
                        model_id=model_id,
                        cap=cap,
                        condition=condition,
                        seed=args.seed,
                        temperature=args.temperature,
                        batch_size=args.batch_size,
                        run_config_sha256=run_config_sha256,
                        direction_sha256=direction_sha256,
                    )
                    expected_jobs = _expected_condition_jobs(
                        cfg=cfg,
                        model_id=model_id,
                        cap=cap,
                        condition=condition,
                        test_items=test_items,
                        seed=args.seed,
                    )
                    if path.exists():
                        records = _read_jsonl(path)
                        checkpoint_records, checkpoint_payload = (
                            _load_condition_checkpoint(
                                checkpoint_path,
                                checkpoint_identity=checkpoint_identity,
                                expected_jobs=expected_jobs,
                                cfg=cfg,
                                model_id=model_id,
                                cap=cap,
                                condition=condition,
                                test_items=test_items,
                                seed=args.seed,
                                batch_size=args.batch_size,
                            )
                        )
                        if checkpoint_records != records or not checkpoint_payload.get(
                            "complete"
                        ):
                            raise SystemExit(
                                f"{path}: final sample exists without matching complete checkpoint"
                            )
                        checkpoint_sample_sha = checkpoint_payload.get(
                            "final_sample_sha256"
                        )
                        current_sample_sha = _sha256_file(path)
                        if checkpoint_sample_sha not in {
                            None,
                            current_sample_sha,
                        }:
                            raise SystemExit(
                                f"{path}: checkpoint final sample hash mismatch"
                            )
                    else:
                        print(
                            f"[E-0017] cell={cell_key} cap={cap} "
                            f"condition={condition}",
                            flush=True,
                        )
                        records = generate_condition(
                            backend=backend,
                            cfg=cfg,
                            direction=direction,
                            model_id=model_id,
                            cap=cap,
                            condition=condition,
                            test_items=test_items,
                            seed=args.seed,
                            temperature=args.temperature,
                            batch_size=args.batch_size,
                            checkpoint_path=checkpoint_path,
                            checkpoint_identity=checkpoint_identity,
                            budget_guard=attempt_registry.assert_budget,
                        )
                        _write_jsonl_atomic(path, records)
                    _validate_condition_records(
                        records,
                        cfg=cfg,
                        model_id=model_id,
                        cap=cap,
                        condition=condition,
                        test_items=test_items,
                        seed=args.seed,
                        batch_size=args.batch_size,
                    )
                    sample_sha = _sha256_file(path)
                    _write_json(
                        checkpoint_path,
                        _checkpoint_payload(
                            checkpoint_identity=checkpoint_identity,
                            expected_jobs=expected_jobs,
                            records=records,
                            complete=True,
                            final_sample_sha256=sample_sha,
                        ),
                    )
                    all_records.extend(records)
        finally:
            del backend
            gc.collect()
            try:
                import torch

                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass
        disk_checks.append(
            _check_runtime_disk(
                out_dir=out_dir,
                hf_home=args.hf_home,
                venv=args.venv,
                budget_gb=args.disk_budget_gb,
                ceiling_gb=args.disk_ceiling_gb,
                min_free_gb=args.min_free_gb,
                label=f"post-cell-{cell_key}",
            )
        )
        attempt_registry.assert_budget()

    expected_records = (
        len(FROZEN_CELL_KEYS)
        * len(CAPS)
        * len(CONDITIONS)
        * len(test_items)
        * adj.K_SAMPLES
    )
    if len(all_records) != expected_records:
        raise SystemExit(
            f"E-0017 expected {expected_records} records, got {len(all_records)}"
        )
    frozen_lineage_after = frozen_lineage_inventory(
        frozen_root, configs, seed=args.seed
    )
    if frozen_lineage_after != frozen_lineage:
        raise SystemExit("frozen E-0006 lineage changed during E-0017")

    analysis_path = out_dir / "analysis.json"
    summary_path = out_dir / "analysis.md"
    manifest_path = out_dir / "run_manifest.json"
    raw_inputs = _raw_input_manifest(
        out_dir=out_dir,
        run_config_sha256=run_config_sha256,
        frozen_lineage=frozen_lineage_after,
    )
    analysis_spec = {
        "experiment_id": EXPERIMENT_ID,
        "bootstrap_b": args.bootstrap_b,
        "bootstrap_seed": args.seed,
        "primary_ci_level": 0.95,
        "primary_multiplicity_method": "joint-item-cluster-bootstrap-max-T",
        "primary_family_size": 24,
        "primary_family": (
            "4 cells x (E_prompt_128,E_steer_128,I_128,"
            "E_prompt_256,E_steer_256,I_256)"
        ),
        "diagnostic_ci_level": 0.95,
        "continuation_diagnostic_ci": (
            "item-cluster bootstrap among items with >=1 64-token cap stop; "
            "undefined with explicit zero-denominator metadata otherwise"
        ),
        "meaningful_margin": adj.DELTA,
        "caps": list(CAPS),
        "conditions": list(CONDITIONS),
        "analysis_implementation_sha256": _sha256_file(Path(__file__).resolve()),
    }
    analysis_preexisting = analysis_path.exists()
    analysis = _prepare_test_once_analysis(
        seal_path=seal_path,
        raw_inputs=raw_inputs,
        analysis_spec=analysis_spec,
        analysis_path=analysis_path,
        summary_path=summary_path,
        manifest_path=manifest_path,
    )
    if analysis is not None and json.loads(
        seal_path.read_text(encoding="utf-8")
    ).get("status") == "COMPLETE":
        attempt_registry.mark_complete(
            {
                "test_once_seal_path": _rel(seal_path),
                "test_once_seal_sha256": _sha256_file(seal_path),
                "raw_inputs_sha256": _canonical_json_hash(raw_inputs),
                "analysis_spec_sha256": _canonical_json_hash(analysis_spec),
                "analysis_json_sha256": _sha256_file(analysis_path),
                "run_manifest_sha256": _sha256_file(manifest_path),
            }
        )
        print(f"[E-0017] TEST-once analysis already complete: {_rel(analysis_path)}")
        print(f"[E-0017] outcome={analysis['overall_outcome_branch']}")
        return 0
    if analysis is None:
        analysis = analyse(
            all_records,
            configs,
            bootstrap_b=args.bootstrap_b,
            seed=args.seed,
        )
        _write_json(analysis_path, analysis)
        _mark_test_once_analysis_written(
            seal_path=seal_path,
            analysis_path=analysis_path,
        )
    _write_summary(summary_path, analysis)
    sample_paths = sorted((out_dir / "samples").glob("*.jsonl"))
    checkpoint_paths = sorted((out_dir / "checkpoints").glob("*.json"))
    direction_paths = sorted(out_dir.glob("cell_*/direction_manifest.json"))
    manifest = {
        "experiment_id": EXPERIMENT_ID,
        "valid_for_paper": False,
        "original_e0006_untouched": True,
        "original_e0006_decision": "0/12",
        "first_started_at": run_state["first_started_at"],
        "final_invocation_started_at": invocation_started_at,
        "ended_at": utcnow(),
        "final_invocation_wall_clock_seconds": time.time() - t0,
        "analysis_recovered_without_reanalysis": analysis_preexisting,
        "code_commit": source_state["head"],
        "dirty_tree": False,
        "platform": platform.platform(),
        "preregistration": preregistration,
        "generation_identity": run_config,
        "run_config_sha256": run_config_sha256,
        "frozen_lineage": frozen_lineage_after,
        "direction_derivation": direction_meta,
        "backend_runtime": backend_runtime_meta,
        "canonical_attempt_registry": str(attempt_registry.path),
        "disk_checks": disk_checks,
        "test_once": {
            "seal": _rel(seal_path),
            "raw_inputs_sha256": _canonical_json_hash(raw_inputs),
            "analysis_spec_sha256": _canonical_json_hash(analysis_spec),
        },
        "artifacts": {
            "analysis_json": _rel(analysis_path),
            "analysis_md": _rel(summary_path),
            "run_config": {
                "path": _rel(run_config_path),
                "sha256": _sha256_file(run_config_path),
            },
            "sample_files": [
                {"path": _rel(path), "sha256": _sha256_file(path)}
                for path in sample_paths
            ],
            "checkpoint_files": [
                {"path": _rel(path), "sha256": _sha256_file(path)}
                for path in checkpoint_paths
            ],
            "direction_manifests": [
                {"path": _rel(path), "sha256": _sha256_file(path)}
                for path in direction_paths
            ],
        },
    }
    _write_json(manifest_path, manifest)
    _complete_test_once_analysis(
        seal_path=seal_path,
        analysis_path=analysis_path,
        summary_path=summary_path,
        manifest_path=manifest_path,
    )
    attempt_registry.mark_complete(
        {
            "test_once_seal_path": _rel(seal_path),
            "test_once_seal_sha256": _sha256_file(seal_path),
            "raw_inputs_sha256": _canonical_json_hash(raw_inputs),
            "analysis_spec_sha256": _canonical_json_hash(analysis_spec),
            "analysis_json_sha256": _sha256_file(analysis_path),
            "run_manifest_sha256": _sha256_file(manifest_path),
        }
    )
    print(f"[E-0017] wrote {_rel(analysis_path)}")
    print(f"[E-0017] outcome={analysis['overall_outcome_branch']}")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    global _ACTIVE_ATTEMPT_REGISTRY

    try:
        return _main(argv)
    except BaseException as exc:
        if _ACTIVE_ATTEMPT_REGISTRY is not None:
            _ACTIVE_ATTEMPT_REGISTRY.mark_failed(exc)
        raise
    finally:
        if _ACTIVE_ATTEMPT_REGISTRY is not None:
            _ACTIVE_ATTEMPT_REGISTRY.release()
        _ACTIVE_ATTEMPT_REGISTRY = None


if __name__ == "__main__":
    raise SystemExit(main())
