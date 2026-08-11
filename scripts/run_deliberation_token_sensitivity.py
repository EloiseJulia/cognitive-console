"""E-0017 deliberation 64/128/256-token sensitivity companion.

The frozen E-0006 0/12 result is never modified. This runner reuses each
deliberation cell's frozen TEST items, prompt, alpha, layer, seeds, scorer, and
batch composition, while varying only max_new_tokens. It captures generated
token IDs so a mechanical token-cap stop is measured exactly rather than
inferred from whitespace or decoded-text length.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import platform
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
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
DEFAULT_OUT_DIR = _REPO / "results" / "E-0017-deliberation-token-sensitivity"
DEFAULT_SEED = 20260723
DEFAULT_TEMPERATURE = 0.7
DEFAULT_BATCH_SIZE = 16
DEFAULT_N_EXTRACTION = 28
DEFAULT_DISK_BUDGET_GB = 60.0
DEFAULT_DISK_CEILING_GB = 70.0
DEFAULT_MIN_FREE_GB = 5.0
PREREG_PATH = (
    _REPO
    / "docs"
    / "research"
    / "2026-08-11-deliberation-token-sensitivity"
    / "prereg-e0017-DRAFT.md"
)
CHECKPOINT_SCHEMA_VERSION = 1
TEST_ONCE_SCHEMA_VERSION = 1


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


def _validate_output_path(out_dir: Path, frozen_root: Path) -> None:
    out_dir = out_dir.resolve()
    frozen_root = frozen_root.resolve()
    if out_dir == frozen_root or _is_relative_to(out_dir, frozen_root):
        raise SystemExit(
            "E-0017 output must not be the frozen E-0006 tree or one of its children"
        )
    if out_dir == _REPO.resolve():
        raise SystemExit("E-0017 output must use a dedicated directory")


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


def _preregistration_identity(*, require_frozen: bool) -> Dict[str, object]:
    text = PREREG_PATH.read_text(encoding="utf-8")
    first_status = next(
        (line.strip() for line in text.splitlines() if line.startswith("Status:")),
        "",
    )
    frozen = "FROZEN" in first_status and "NOT FROZEN" not in first_status
    if require_frozen and not frozen:
        raise SystemExit(
            f"{_rel(PREREG_PATH)} is not marked FROZEN; real TEST generation is blocked"
        )
    return {
        "path": _rel(PREREG_PATH),
        "sha256": _sha256_text(text),
        "status_line": first_status,
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


def _model_identity_key(model_ref: str) -> str:
    parts = [
        part
        for part in str(model_ref).strip().replace("\\", "/").split("/")
        if part
    ]
    return (parts[-1] if parts else str(model_ref)).lower()


def _looks_like_local_path(model_ref: str) -> bool:
    ref = str(model_ref).strip()
    return (
        ref.startswith(("/", "\\", "./", ".\\", "../", "..\\"))
        or (len(ref) >= 3 and ref[1] == ":" and ref[2] in {"/", "\\"})
    )


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


def load_test_items(*, seed: int) -> List[Dict[str, object]]:
    items = list(c2b_tasks.load_c2b_task(AXIS, use_fixture=False).items)[
        : adj.N_ITEMS_BY_AXIS[AXIS]
    ]
    by_id = {str(item["id"]): item for item in items}
    split = adj.split_dev_test(
        list(by_id),
        dev_fraction=adj.DEV_FRACTION,
        seed=seed,
    )
    return [by_id[item_id] for item_id in split.test_ids]


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
    model_id: str,
    out_dir: Path,
    n_extraction: int,
    seed: int,
) -> Tuple[np.ndarray, Dict[str, object]]:
    from cognitive_console.activations.provider import HFActivationProvider

    provider = HFActivationProvider(
        model_id,
        device=p0._pick_device(),
        dtype=p0._pick_dtype(),
        cache_dir=str(out_dir / "activations" / "cache"),
    )
    if cfg.method == "caa":
        direction = p0._extract_direction(provider, AXIS, cfg.layer, n_extraction, seed)
        return direction, {
            "source": "caa_mean_difference_rederived_at_frozen_layer",
            "layer": cfg.layer,
            "direction_sha256": hashlib.sha256(
                np.asarray(direction, dtype=np.float64).tobytes()
            ).hexdigest(),
        }

    pairs = c1.load_axis_pairs(AXIS)
    split = c1.make_split(
        list(pairs.pos),
        n_extraction=n_extraction,
        seed=seed,
    )
    candidate_layers = [layer for layer in provider.available_layers() if layer >= 1]
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
    if not math.isclose(float(iti.sigma), cfg.sigma, rel_tol=1e-6, abs_tol=1e-8):
        raise RuntimeError(
            f"{cfg.cell_key}: rederived ITI sigma {iti.sigma} != frozen {cfg.sigma}"
        )
    return iti.direction, {
        "source": "iti_probe_rederived_by_frozen_path",
        "layer": int(iti.layer),
        "sigma": float(iti.sigma),
        "probe_norm": float(np.linalg.norm(iti.vector)),
        "direction_sha256": hashlib.sha256(
            np.asarray(iti.direction, dtype=np.float64).tobytes()
        ).hexdigest(),
    }


def score_generation(text: str, item: Dict[str, object]) -> Dict[str, object]:
    parsed = scorers.parse_final_number(text)
    return {
        "parsed_final_number": parsed,
        "final_answer_present": parsed is not None,
        "parser_failed": parsed is None,
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
        for field in ("final_answer_present", "parser_failed", "correct"):
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
    correct_hit = [
        int(record["correct"])
        for record in records
        if bool(record["hit_max_new_tokens"])
    ]
    correct_not_hit = [
        int(record["correct"])
        for record in records
        if not bool(record["hit_max_new_tokens"])
    ]
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
        lambda record: bool(record["parser_failed"]),
        bootstrap_b=bootstrap_b,
        seed=seed,
    )
    answer_present_ci = _item_cluster_metric_ci(
        records,
        lambda record: bool(record["final_answer_present"]),
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
    accuracy_hit = float(np.mean(correct_hit)) if correct_hit else None
    accuracy_not_hit = (
        float(np.mean(correct_not_hit)) if correct_not_hit else None
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
        "parser": {
            "n_final_answer_present": sum(
                bool(record["final_answer_present"]) for record in records
            ),
            "final_answer_present_rate": float(
                np.mean([bool(record["final_answer_present"]) for record in records])
            )
            if n
            else math.nan,
            "final_answer_present_ci_95_item_cluster": answer_present_ci,
            "n_failed": sum(bool(record["parser_failed"]) for record in records),
            "failure_rate": float(
                np.mean([bool(record["parser_failed"]) for record in records])
            )
            if n
            else math.nan,
            "failure_ci_95_item_cluster": parser_failure_ci,
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
            "n_hit_cap": len(correct_hit),
            "n_did_not_hit_cap": len(correct_not_hit),
            "hit_cap": accuracy_hit,
            "did_not_hit_cap": accuracy_not_hit,
            "hit_minus_did_not_hit": (
                None
                if accuracy_hit is None or accuracy_not_hit is None
                else accuracy_hit - accuracy_not_hit
            ),
            "association_only": True,
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


def _continuation_materiality(
    cell_records: Sequence[Dict[str, object]], *, long_cap: int
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
        for key, short in lookup.items():
            cond, cap, item_id, sample_index = key
            if cond != condition or cap != 64 or not bool(short["hit_max_new_tokens"]):
                continue
            long = lookup.get((condition, int(long_cap), item_id, sample_index))
            if long is None:
                raise ValueError(f"missing paired long-cap sample for {key}")
            compared += 1
            short_ids = [int(value) for value in short["token_ids"]]
            long_ids = [int(value) for value in long["token_ids"]]
            prefix_matches += int(long_ids[: len(short_ids)] == short_ids)
            short_answer = short.get("parsed_final_number")
            long_answer = long.get("parsed_final_number")
            sample_answer_changed = int(
                short_answer is not None
                and long_answer is not None
                and float(short_answer) != float(long_answer)
            )
            sample_correctness_recovered = int(
                int(short["correct"]) == 0 and int(long["correct"]) == 1
            )
            sample_correctness_lost = int(
                int(short["correct"]) == 1 and int(long["correct"]) == 0
            )
            sample_added_answer = int(
                not bool(short["final_answer_present"])
                and bool(long["final_answer_present"])
            )
            added_answer += sample_added_answer
            answer_changed += sample_answer_changed
            correctness_recovered += sample_correctness_recovered
            correctness_lost += sample_correctness_lost
            materially_changed += int(
                any(
                    (
                        sample_added_answer,
                        sample_answer_changed,
                        sample_correctness_recovered,
                        sample_correctness_lost,
                    )
                )
            )
        by_condition[condition] = {
            "n_64_cap_stops_compared": compared,
            "n_exact_token_prefix_matches": prefix_matches,
            "all_prefixes_match": prefix_matches == compared,
            "n_continuation_added_parseable_answer": added_answer,
            "n_continuation_changed_parseable_answer": answer_changed,
            "n_correctness_recovered": correctness_recovered,
            "n_correctness_lost": correctness_lost,
            "n_operational_semantic_truncation_evidence": materially_changed,
            "fraction_operational_semantic_truncation_evidence_among_64_cap_stops": (
                float(materially_changed / compared) if compared else None
            ),
            "operational_semantic_truncation_evidence_present": (
                prefix_matches == compared and materially_changed > 0
            ),
            "semantic_note": (
                "A mechanical cap stop is not semantic truncation. Same-seed "
                "exact-prefix continuation that adds/changes the parsed answer "
                "or changes correctness is the predeclared operational evidence "
                "that the 64-token cap was semantically material."
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
                effect_ci = _ci(
                    effect,
                    bootstrap_b=bootstrap_b,
                    ci_level=0.95,
                    seed=seed,
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
            interaction_ci = _ci(
                interaction,
                bootstrap_b=bootstrap_b,
                ci_level=adj.BONFERRONI_CI_LEVEL,
                seed=seed,
            )
            affects_comparison |= _meaningful_nonzero(interaction_ci)
            all_interactions_equivalent &= _equivalent_within(interaction_ci)
            continuation = _continuation_materiality(
                cell_records, long_cap=long_cap
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
        affects_comparison |= pass_changed
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
            "primary_ci_level": adj.BONFERRONI_CI_LEVEL,
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
                "its same-seed longer continuation and the continuation adds or "
                "changes the parsed answer or changes correctness"
            ),
        },
        "scope": (
            "TEST-only sensitivity companion for deliberation; never replaces or "
            "edits the frozen E-0006 0/12 result"
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
        "- scope: TEST-only companion; frozen E-0006 and its 0/12 result are unchanged.",
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


def _model_reference_identity(model_ref: str) -> Dict[str, object]:
    path = Path(model_ref)
    if not path.exists():
        return {
            "reference": str(model_ref),
            "kind": "hub_or_external_reference",
            "identity_limitation": (
                "E-0006 retained model labels/local paths but no immutable weight "
                "hash. The 64-token exact reproduction gate is therefore mandatory."
            ),
        }
    resolved = path.resolve()
    metadata_files = []
    for name in (
        "config.json",
        "generation_config.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "special_tokens_map.json",
        "model.safetensors.index.json",
    ):
        candidate = resolved / name
        if candidate.exists() and candidate.is_file():
            metadata_files.append(
                {
                    "name": name,
                    "size_bytes": candidate.stat().st_size,
                    "sha256": _sha256_file(candidate),
                }
            )
    weight_files = [
        {
            "name": candidate.name,
            "size_bytes": candidate.stat().st_size,
        }
        for candidate in sorted(resolved.glob("*.safetensors"))
        if candidate.is_file()
    ]
    return {
        "reference": str(model_ref),
        "kind": "local_directory",
        "resolved_path": str(resolved),
        "metadata_files": metadata_files,
        "weight_file_size_manifest": weight_files,
        "weight_bytes": sum(int(row["size_bytes"]) for row in weight_files),
        "identity_limitation": (
            "Weight shard bytes are not re-hashed by this runner. Exact effective "
            "compatibility is gated by the frozen 64-token reproduction."
        ),
    }


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
        analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
        if analysis.get("experiment_id") != EXPERIMENT_ID:
            raise ValueError("locked TEST analysis artifact has wrong experiment id")
        seal["status"] = "ANALYZED"
        seal["analysis_written_at"] = utcnow()
        seal["analysis_json_sha256"] = _sha256_file(analysis_path)
        _write_json(seal_path, seal)
        return analysis
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
    parser.add_argument("--qwen-model", default=None)
    parser.add_argument("--llama-model", default=None)
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
    if not args.dry_run and not args.confirm_frozen_test_once:
        mismatches.append(
            "real run requires --confirm-frozen-test-once after protocol freeze/approval"
        )
    if mismatches:
        raise SystemExit("E-0017 frozen companion identity mismatch: " + ", ".join(mismatches))


def _effective_model_ref(
    cfg: FrozenCellConfig,
    *,
    qwen_model: Optional[str],
    llama_model: Optional[str],
    dry_run: bool,
) -> str:
    override = qwen_model if cfg.model_label == "qwen2.5-7b" else llama_model
    effective = str(override or cfg.model_id)
    if _model_identity_key(effective) != _model_identity_key(cfg.model_id):
        raise SystemExit(
            f"{cfg.cell_key}: model identity {_model_identity_key(effective)!r} "
            f"does not match frozen {_model_identity_key(cfg.model_id)!r}"
        )
    if (
        not dry_run
        and override is None
        and _looks_like_local_path(cfg.model_id)
        and not Path(cfg.model_id).exists()
    ):
        flag = "--qwen-model" if cfg.model_label == "qwen2.5-7b" else "--llama-model"
        raise SystemExit(
            f"{cfg.cell_key}: frozen local model path {cfg.model_id!r} is absent; "
            f"pass {flag} with the same checkpoint identity"
        )
    return effective


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


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    _validate_args(args)
    frozen_root = Path(args.frozen_root).resolve()
    out_dir = Path(args.out_dir).resolve()
    _validate_output_path(out_dir, frozen_root)
    preregistration = _preregistration_identity(require_frozen=not args.dry_run)
    configs = {
        cell_key: load_frozen_cell_config(frozen_root, cell_key)
        for cell_key in FROZEN_CELL_KEYS
    }
    frozen_lineage = frozen_lineage_inventory(
        frozen_root, configs, seed=args.seed
    )
    test_items = load_test_items(seed=args.seed)
    if len(test_items) != 40:
        raise SystemExit(f"E-0017 expected 40 TEST items, got {len(test_items)}")
    model_refs = {
        cell_key: _effective_model_ref(
            cfg,
            qwen_model=args.qwen_model,
            llama_model=args.llama_model,
            dry_run=args.dry_run,
        )
        for cell_key, cfg in configs.items()
    }
    inventory = {
        "experiment_id": EXPERIMENT_ID,
        "cells": {
            cell_key: {
                "model": model_refs[cell_key],
                "model_reference_identity": _model_reference_identity(
                    model_refs[cell_key]
                ),
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
        "frozen_lineage": frozen_lineage,
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
    for cell_key in FROZEN_CELL_KEYS:
        cfg = configs[cell_key]
        model_id = model_refs[cell_key]
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

        direction, derivation = _derive_hf_direction(
            cfg,
            model_id=model_id,
            out_dir=out_dir / f"cell_{cell_key}",
            n_extraction=args.n_extraction,
            seed=args.seed,
        )
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
            model_id,
            device=p0._pick_device(),
            dtype=p0._pick_dtype(),
            seed=args.seed,
        )
        try:
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
        "primary_ci_level": adj.BONFERRONI_CI_LEVEL,
        "diagnostic_ci_level": 0.95,
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
    print(f"[E-0017] wrote {_rel(analysis_path)}")
    print(f"[E-0017] outcome={analysis['overall_outcome_branch']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
