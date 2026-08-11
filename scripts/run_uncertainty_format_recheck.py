"""E-0013 uncertainty format-compliance recheck.

This is an additive robustness check for the frozen C2b uncertainty axis. It
reuses the E-0006 DEV-selected prompt/alpha/layer configurations and re-runs the
uncertainty items while capturing raw generations, confidence-parse success, the
frozen 0.5 imputation path, and a separate format-compliant-only reanalysis.
It does not alter the frozen C2b adjudicator or verdict.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cognitive_console.eval import c2b_tasks
from cognitive_console.eval import scorers
from cognitive_console.experiments import adjudicate_c2b as adj
from cognitive_console.experiments.adjudicate_c2b import BackendOutcomeSampler
from cognitive_console.lineage import git_commit, utcnow
from cognitive_console.steering.generate import SteerConfig, SyntheticC2bTaskBackend
from cognitive_console.steering.iti import extract_iti, sigma_scaled_alpha
from cognitive_console.steering.extract import min_layer_for_depth
from scripts import run_c1_facade as c1
from scripts import run_gpu_phase0 as p0
from scripts import run_arm_matrix as arm

AXIS = "uncertainty_awareness"
EXPERIMENT_ID = "E-0013"
CONDITIONS = ("prompt", "steer", "baseline")
DEFAULT_OUT_DIR = _REPO / "results" / "E-0013-uncertainty-recheck"
DEFAULT_FROZEN_ROOT = _REPO / "results" / "arm_full"
DEFAULT_MAX_NEW_TOKENS = 64
DEFAULT_TEMPERATURE = 0.7
DEFAULT_SEED = 20260723
DEFAULT_N_EXTRACTION = 28
ITI_SIGMA_IDENTITY_REL_TOL = 5e-4
ITI_SIGMA_IDENTITY_ABS_TOL = 5e-3
CHECKPOINT_SCHEMA_VERSION = "e0013-format-replay-checkpoint-v2"
EXECUTION_IDENTITY_SCHEMA_VERSION = "e0013-hf-execution-identity-v1"
MODEL_SNAPSHOT_MANIFEST_SCHEMA_VERSION = "e0013-model-snapshot-sha256-v1"
ACTIVATION_CACHE_SCHEMA_VERSION = "e0013-activation-cache-v2"
TEST_USE_POLICY = "FROZEN_TEST_ITEMS_EVALUATED_ONCE_WITH_NO_SELECTION_OR_TUNING"
_HF_REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_MODEL_TYPE_BY_LABEL = {
    "qwen2.5-7b": "qwen2",
    "llama3-8b": "llama",
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
    source_config_fingerprint: str
    source_mean_diff: float


def _sha256_text(text: str) -> str:
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _canonical_hash(payload: object) -> str:
    raw = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _array_sha256(value: np.ndarray) -> str:
    array = np.asarray(value, dtype="<f8")
    return hashlib.sha256(array.tobytes(order="C")).hexdigest()


def _atomic_write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_name(path.name + ".pending")
    with open(pending, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(pending, path)


def _write_once_or_verify_json(path: Path, payload: object) -> None:
    encoded = (
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    if path.exists():
        if path.read_bytes() != encoded:
            raise RuntimeError(f"refusing to overwrite non-identical artifact: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_name(path.name + ".pending")
    with open(pending, "wb") as fh:
        fh.write(encoded)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(pending, path)


def _write_once_or_verify_jsonl(path: Path, records: Iterable[Dict]) -> None:
    encoded = "".join(
        json.dumps(rec, ensure_ascii=False) + "\n" for rec in records
    ).encode("utf-8")
    if path.exists():
        if path.read_bytes() != encoded:
            raise RuntimeError(f"refusing to overwrite non-identical artifact: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_name(path.name + ".pending")
    with open(pending, "wb") as fh:
        fh.write(encoded)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(pending, path)


def _git_status_rows() -> List[str]:
    proc = subprocess.run(
        [
            "git",
            "-C",
            str(_REPO),
            "status",
            "--porcelain",
            "--untracked-files=all",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in proc.stdout.splitlines() if line.strip()]


def _git_dirty() -> bool:
    return bool(_git_status_rows())


def _git_blob_oid(path: Path, commit: str) -> str:
    resolved = Path(path).resolve()
    try:
        rel = resolved.relative_to(_REPO).as_posix()
    except ValueError as exc:
        raise RuntimeError(
            f"protocol manifest must be tracked inside the repository: {resolved}"
        ) from exc
    proc = subprocess.run(
        ["git", "-C", str(_REPO), "rev-parse", f"{commit}:{rel}"],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"protocol manifest is not present in audited commit {commit}: {rel}"
        )
    return proc.stdout.strip()


def _is_within(path: Path, root: Path) -> bool:
    try:
        Path(path).resolve().relative_to(Path(root).resolve())
        return True
    except ValueError:
        return False


def _require_external_directory(path: Path, label: str) -> Path:
    resolved = Path(path).expanduser().resolve()
    if _is_within(resolved, _REPO):
        raise RuntimeError(f"{label} must be outside the repository: {resolved}")
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def _directory_size_bytes(path: Path) -> int:
    root = Path(path)
    if not root.exists():
        return 0
    total = 0
    seen: set[Tuple[int, int]] = set()
    for candidate in root.rglob("*"):
        if not candidate.is_file():
            continue
        stat = candidate.stat()
        key = (int(stat.st_dev), int(stat.st_ino))
        if key in seen:
            continue
        seen.add(key)
        total += int(stat.st_size)
    return total


def _disk_free_bytes(path: Path) -> int:
    candidate = Path(path).resolve()
    while not candidate.exists() and candidate.parent != candidate:
        candidate = candidate.parent
    return int(shutil.disk_usage(candidate).free)


def _probe_cuda_environment() -> Dict[str, object]:
    try:
        import torch
        import transformers
    except ImportError as exc:
        raise RuntimeError("HF replay requires torch and transformers") from exc
    if not torch.cuda.is_available():
        raise RuntimeError("HF replay requires CUDA; torch.cuda.is_available() is false")
    properties = torch.cuda.get_device_properties(0)
    driver_probe = getattr(torch._C, "_cuda_getDriverVersion", None)
    return {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "torch_cuda_runtime": torch.version.cuda,
        "cuda_driver_version": (
            int(driver_probe()) if callable(driver_probe) else None
        ),
        "cudnn_version": (
            int(torch.backends.cudnn.version())
            if torch.backends.cudnn.is_available()
            else None
        ),
        "cuda_device_count": int(torch.cuda.device_count()),
        "cuda_device_index": 0,
        "cuda_device_name": str(torch.cuda.get_device_name(0)),
        "cuda_total_memory_bytes": int(properties.total_memory),
        "cuda_capability": [
            int(properties.major),
            int(properties.minor),
        ],
        "selected_device": p0._pick_device(),
        "selected_dtype": p0._pick_dtype(),
    }


def _assert_resource_guards(
    policy: Dict[str, object],
    *,
    out_dir: Path,
    scratch_dir: Path,
    activation_cache_dir: Path,
    hf_cache_dir: Optional[Path],
    stage: str,
) -> Dict[str, object]:
    env = _probe_cuda_environment()
    expected_device = str(policy["device"])
    expected_dtype = str(policy["dtype"])
    expected_gpu = str(policy["gpu_name_contains"])
    if env["selected_device"] != expected_device:
        raise RuntimeError(
            f"{stage}: expected device {expected_device!r}, got "
            f"{env['selected_device']!r}"
        )
    if env["selected_dtype"] != expected_dtype:
        raise RuntimeError(
            f"{stage}: expected dtype {expected_dtype!r}, got "
            f"{env['selected_dtype']!r}"
        )
    if expected_gpu.lower() not in str(env["cuda_device_name"]).lower():
        raise RuntimeError(
            f"{stage}: expected A800 GPU identity containing {expected_gpu!r}, "
            f"got {env['cuda_device_name']!r}"
        )

    min_free = int(policy["min_free_disk_bytes"])
    max_scratch = int(policy["max_scratch_bytes"])
    max_activation = int(policy["max_activation_cache_bytes"])
    max_hf_cache = int(policy["max_hf_cache_bytes"])
    disk = {
        "out_dir_free_bytes": _disk_free_bytes(out_dir),
        "scratch_free_bytes": _disk_free_bytes(scratch_dir),
        "scratch_size_bytes": _directory_size_bytes(scratch_dir),
        "activation_cache_size_bytes": _directory_size_bytes(activation_cache_dir),
        "hf_cache_size_bytes": (
            _directory_size_bytes(hf_cache_dir) if hf_cache_dir is not None else 0
        ),
    }
    for label in ("out_dir_free_bytes", "scratch_free_bytes"):
        if disk[label] < min_free:
            raise RuntimeError(
                f"{stage}: {label}={disk[label]} below frozen minimum {min_free}"
            )
    if disk["scratch_size_bytes"] > max_scratch:
        raise RuntimeError(
            f"{stage}: scratch budget exceeded: {disk['scratch_size_bytes']} > "
            f"{max_scratch}"
        )
    if disk["activation_cache_size_bytes"] > max_activation:
        raise RuntimeError(
            f"{stage}: activation-cache budget exceeded: "
            f"{disk['activation_cache_size_bytes']} > {max_activation}"
        )
    if disk["hf_cache_size_bytes"] > max_hf_cache:
        raise RuntimeError(
            f"{stage}: HF-cache budget exceeded: {disk['hf_cache_size_bytes']} > "
            f"{max_hf_cache}"
        )
    return {
        **env,
        "stage": stage,
        "resource_policy": dict(policy),
        "disk_and_cache": disk,
    }


def _stable_environment_identity(snapshot: Dict[str, object]) -> Dict[str, object]:
    return {
        key: value
        for key, value in snapshot.items()
        if key not in {"stage", "resource_policy", "disk_and_cache"}
    }


def _model_identity_category(name: str) -> Optional[str]:
    normalized = Path(name).as_posix()
    basename = Path(normalized).name
    if normalized == "config.json" or normalized == "original/params.json":
        return "config"
    if normalized == "generation_config.json":
        return "generation_config"
    if normalized == "chat_template.jinja":
        return "chat_template"
    if basename.endswith((".safetensors.index.json", ".bin.index.json")):
        return "weights_index"
    if (
        basename.endswith(".safetensors")
        or (
            basename.endswith(".bin")
            and (
                basename.startswith("pytorch_model")
                or basename.startswith("model")
            )
        )
        or (
            normalized.startswith("original/")
            and basename.startswith("consolidated.")
            and basename.endswith(".pth")
        )
    ):
        return "weights"
    if (
        basename.startswith("tokenizer")
        or basename
        in {
            "special_tokens_map.json",
            "added_tokens.json",
            "vocab.json",
            "merges.txt",
        }
    ):
        return "tokenizer"
    return None


def _load_model_snapshot_manifest(
    model_policy: Dict[str, object], *, model_label: str
) -> Dict[str, object]:
    reference = dict(model_policy.get("snapshot_manifest") or {})
    required_reference = {
        "source_path",
        "source_sha256",
        "source_hash_mode",
        "model_key",
        "aggregate_sha256",
    }
    missing_reference = sorted(required_reference - set(reference))
    if missing_reference:
        raise RuntimeError(
            f"{model_label}: frozen snapshot manifest reference missing "
            f"{missing_reference}"
        )
    source_path = Path(str(reference["source_path"]))
    if not source_path.is_absolute():
        source_path = (_REPO / source_path).resolve()
    try:
        source_path.relative_to(_REPO)
    except ValueError as exc:
        raise RuntimeError(
            f"{model_label}: model hash source must be tracked inside the repository"
        ) from exc
    expected_source_sha = str(reference["source_sha256"])
    if not _SHA256_RE.fullmatch(expected_source_sha):
        raise RuntimeError(f"{model_label}: invalid model hash source SHA-256")
    if reference["source_hash_mode"] != "utf8_lf_normalized":
        raise RuntimeError(f"{model_label}: unsupported model hash source mode")
    if not source_path.is_file():
        raise RuntimeError(f"{model_label}: model hash source record missing")
    source_bytes = source_path.read_bytes().replace(b"\r\n", b"\n")
    if b"\r" in source_bytes:
        raise RuntimeError(f"{model_label}: invalid model hash source line endings")
    if hashlib.sha256(source_bytes).hexdigest() != expected_source_sha:
        raise RuntimeError(f"{model_label}: model hash source record mismatch")
    source = json.loads(source_path.read_text(encoding="utf-8"))
    if source.get("schema_version") != MODEL_SNAPSHOT_MANIFEST_SCHEMA_VERSION:
        raise RuntimeError(f"{model_label}: unsupported model hash source schema")
    model_key = str(reference["model_key"])
    if model_key != model_label:
        raise RuntimeError(f"{model_label}: model hash source key mismatch")
    manifest = dict((source.get("models") or {}).get(model_key) or {})
    if manifest.get("hf_repo_id") != model_policy.get("hf_repo_id"):
        raise RuntimeError(f"{model_label}: source-record HF repo mismatch")
    if manifest.get("revision") != model_policy.get("revision"):
        raise RuntimeError(f"{model_label}: source-record revision mismatch")
    rows = manifest.get("files")
    if not isinstance(rows, list) or not rows:
        raise RuntimeError(f"{model_label}: source record has no required files")
    normalized: List[Dict[str, object]] = []
    seen = set()
    for row in rows:
        row = dict(row)
        path = str(row.get("path", ""))
        category = str(row.get("category", ""))
        sha256 = str(row.get("sha256", ""))
        if (
            not path
            or Path(path).is_absolute()
            or ".." in Path(path).parts
            or path in seen
            or _model_identity_category(path) != category
            or not _SHA256_RE.fullmatch(sha256)
            or int(row.get("size_bytes", -1)) < 0
        ):
            raise RuntimeError(
                f"{model_label}: invalid frozen model file manifest row {row!r}"
            )
        seen.add(path)
        normalized.append(
            {
                "path": path,
                "category": category,
                "size_bytes": int(row["size_bytes"]),
                "sha256": sha256,
            }
        )
    normalized.sort(key=lambda row: str(row["path"]))
    categories = {str(row["category"]) for row in normalized}
    mandatory = {
        "weights",
        "weights_index",
        "config",
        "generation_config",
        "tokenizer",
    }
    if not mandatory.issubset(categories):
        raise RuntimeError(
            f"{model_label}: source record lacks required model categories "
            f"{sorted(mandatory - categories)}"
        )
    aggregate = _canonical_hash(normalized)
    if (
        aggregate != manifest.get("aggregate_sha256")
        or aggregate != reference["aggregate_sha256"]
    ):
        raise RuntimeError(f"{model_label}: frozen model aggregate mismatch")
    chat_template = dict(manifest.get("chat_template") or {})
    if (
        chat_template.get("source")
        not in {"chat_template.jinja", "tokenizer_config.json:chat_template"}
        or not _SHA256_RE.fullmatch(str(chat_template.get("sha256", "")))
        or int(chat_template.get("utf8_bytes", -1)) < 0
    ):
        raise RuntimeError(f"{model_label}: invalid frozen chat-template identity")
    return {
        "schema_version": MODEL_SNAPSHOT_MANIFEST_SCHEMA_VERSION,
        "source_path": _rel(source_path),
        "source_sha256": expected_source_sha,
        "model_key": model_key,
        "hf_repo_id": manifest["hf_repo_id"],
        "revision": manifest["revision"],
        "files": normalized,
        "aggregate_sha256": aggregate,
        "chat_template": chat_template,
    }


def _snapshot_chat_template_identity(
    root: Path, expected: Dict[str, object]
) -> Dict[str, object]:
    source = str(expected["source"])
    if source == "chat_template.jinja":
        raw = (root / "chat_template.jinja").read_bytes()
        raw.decode("utf-8")
    else:
        tokenizer_config = json.loads(
            (root / "tokenizer_config.json").read_text(encoding="utf-8")
        )
        template = tokenizer_config.get("chat_template")
        if not isinstance(template, str) or not template:
            raise RuntimeError(
                f"{root}: tokenizer_config.json lacks a string chat_template"
            )
        raw = template.encode("utf-8")
    actual = {
        "source": source,
        "utf8_bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
    if actual != expected:
        raise RuntimeError(f"{root}: chat template identity mismatch")
    return actual


def _hash_model_snapshot(
    root: Path, *, model_label: str, expected_manifest: Dict[str, object]
) -> Dict[str, object]:
    root = Path(root).resolve()
    if not root.is_dir():
        raise RuntimeError(f"{model_label}: model snapshot missing: {root}")
    expected_rows = [
        dict(row) for row in list(expected_manifest.get("files") or [])
    ]
    expected_names = {str(row["path"]) for row in expected_rows}
    discovered_names = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
        and _model_identity_category(path.relative_to(root).as_posix())
        is not None
    }
    if discovered_names != expected_names:
        missing = sorted(expected_names - discovered_names)
        extra = sorted(discovered_names - expected_names)
        raise RuntimeError(
            f"{model_label}: snapshot file set mismatch; missing={missing}, "
            f"unexpected={extra}"
        )
    actual_rows: List[Dict[str, object]] = []
    for expected in expected_rows:
        path = root / str(expected["path"])
        actual = {
            "path": str(expected["path"]),
            "category": str(expected["category"]),
            "size_bytes": int(path.stat().st_size),
            "sha256": _sha256_file(path),
        }
        if actual != expected:
            raise RuntimeError(
                f"{model_label}: snapshot file identity mismatch for "
                f"{expected['path']}"
            )
        actual_rows.append(actual)
    actual_rows.sort(key=lambda row: str(row["path"]))
    aggregate = _canonical_hash(actual_rows)
    if aggregate != expected_manifest.get("aggregate_sha256"):
        raise RuntimeError(f"{model_label}: snapshot aggregate SHA-256 mismatch")
    config = json.loads((root / "config.json").read_text(encoding="utf-8"))
    expected_model_type = _MODEL_TYPE_BY_LABEL[model_label]
    if str(config.get("model_type")) != expected_model_type:
        raise RuntimeError(
            f"{root}: config model_type={config.get('model_type')!r}, expected "
            f"{expected_model_type!r} for {model_label}"
        )
    return {
        "root": str(root),
        "model_label": model_label,
        "model_type": expected_model_type,
        "files": actual_rows,
        "content_sha256": aggregate,
        "chat_template": _snapshot_chat_template_identity(
            root, dict(expected_manifest["chat_template"])
        ),
        "audited_snapshot_manifest": expected_manifest,
    }


def _resolve_model_identity(
    *,
    model_ref: str,
    model_label: str,
    revision: Optional[str],
    model_policy: Dict[str, object],
    hf_cache_dir: Optional[Path],
) -> Tuple[str, Dict[str, object]]:
    ref = str(model_ref).strip()
    expected_manifest = _load_model_snapshot_manifest(
        model_policy, model_label=model_label
    )
    local = _looks_like_local_path(ref) or Path(ref).expanduser().exists()
    if local:
        if revision:
            raise RuntimeError(
                f"{model_label}: --revision is incompatible with a local snapshot"
            )
        root = Path(ref).expanduser().resolve()
        content = _hash_model_snapshot(
            root,
            model_label=model_label,
            expected_manifest=expected_manifest,
        )
        identity = {
            "kind": "verified_local_snapshot",
            "configured_ref": ref,
            "resolved_path": str(root),
            **content,
        }
        return str(root), identity

    expected_repo = str(model_policy["hf_repo_id"])
    expected_revision = str(model_policy["revision"])
    if ref != expected_repo:
        raise RuntimeError(
            f"{model_label}: HF repo must be exactly {expected_repo!r}, got {ref!r}"
        )
    if revision != expected_revision or not _HF_REVISION_RE.fullmatch(str(revision)):
        raise RuntimeError(
            f"{model_label}: HF revision must equal frozen 40-hex revision "
            f"{expected_revision}"
        )
    if hf_cache_dir is None:
        raise RuntimeError(
            f"{model_label}: --hf-cache-dir is mandatory for pinned HF snapshots"
        )
    try:
        from huggingface_hub import snapshot_download
    except ImportError as exc:
        raise RuntimeError("pinned HF replay requires huggingface_hub") from exc
    snapshot = Path(
        snapshot_download(
            repo_id=ref,
            revision=revision,
            cache_dir=str(hf_cache_dir),
            local_files_only=True,
            allow_patterns=[
                str(row["path"]) for row in expected_manifest["files"]
            ],
        )
    ).resolve()
    if snapshot.name != revision:
        raise RuntimeError(
            f"{model_label}: resolved HF snapshot {snapshot} does not end in "
            f"the pinned revision {revision}"
        )
    content = _hash_model_snapshot(
        snapshot,
        model_label=model_label,
        expected_manifest=expected_manifest,
    )
    identity = {
        "kind": "pinned_hf_snapshot",
        "configured_ref": ref,
        "hf_repo_id": ref,
        "requested_revision": revision,
        "resolved_revision": snapshot.name,
        "resolved_path": str(snapshot),
        **content,
    }
    return str(snapshot), identity


def _verify_model_identity(identity: Dict[str, object]) -> None:
    current = _hash_model_snapshot(
        Path(str(identity["resolved_path"])),
        model_label=str(identity["model_label"]),
        expected_manifest=dict(identity["audited_snapshot_manifest"]),
    )
    if current["content_sha256"] != identity["content_sha256"]:
        raise RuntimeError(
            f"resolved model content changed: {identity['resolved_path']}"
        )
    if current["chat_template"] != identity["chat_template"]:
        raise RuntimeError(
            f"resolved model chat template changed: {identity['resolved_path']}"
        )


def _rel(path: Path) -> str:
    p = Path(path).resolve()
    try:
        return str(p.relative_to(_REPO)).replace("\\", "/")
    except ValueError:
        return str(p).replace("\\", "/")


def _execution_policy(protocol: Dict) -> Dict[str, object]:
    execution = dict(protocol.get("execution") or {})
    required = {
        "authorization_id",
        "authorization_scope",
        "model_identity",
        "resource_guards",
    }
    missing = sorted(required - set(execution))
    if missing:
        raise RuntimeError(f"protocol execution policy missing fields: {missing}")
    return execution


def _protected_protocol_snapshot(protocol: Dict) -> Dict[str, str]:
    protected: Dict[str, str] = {}
    legacy = dict(protocol["legacy_e0013"])
    for path_key, hash_key in (
        ("samples_path", "samples_sha256"),
        ("reanalysis_path", "reanalysis_sha256"),
        ("run_manifest_path", "run_manifest_sha256"),
    ):
        path = Path(legacy[path_key])
        if not path.is_absolute():
            path = (_REPO / path).resolve()
        actual = _sha256_file(path)
        if actual != legacy[hash_key]:
            raise RuntimeError(f"protected legacy artifact hash mismatch: {path}")
        protected[_rel(path)] = actual
    for cell_key, cell_spec in sorted(dict(protocol["cells"]).items()):
        frozen = dict(cell_spec["frozen_result"])
        path = Path(frozen["path"])
        if not path.is_absolute():
            path = (_REPO / path).resolve()
        actual = _sha256_file(path)
        if actual != frozen["sha256"]:
            raise RuntimeError(f"protected frozen result hash mismatch: {cell_key}")
        protected[_rel(path)] = actual
    return protected


def _assert_protected_protocol_snapshot(expected: Dict[str, str]) -> None:
    actual = {
        rel: _sha256_file((_REPO / rel).resolve())
        for rel in sorted(expected)
    }
    if actual != expected:
        changed = sorted(
            rel
            for rel in set(actual) | set(expected)
            if actual.get(rel) != expected.get(rel)
        )
        raise RuntimeError(
            "protected E-0013/E-0006 artifacts changed: " + ", ".join(changed)
        )


def _prepare_hf_execution_guard(
    args,
    *,
    raw_argv: Sequence[str],
) -> Tuple[Path, Dict, Dict[str, object], Path, Optional[Path]]:
    if not args.protocol_manifest:
        raise RuntimeError("--protocol-manifest is mandatory for direct HF replay")
    if not args.expected_code_commit:
        raise RuntimeError("--expected-code-commit is mandatory for direct HF replay")
    if not args.authorization:
        raise RuntimeError("--authorization is mandatory for direct HF replay")
    if not args.scratch_dir:
        raise RuntimeError("--scratch-dir is mandatory for direct HF replay")

    protocol_path = Path(args.protocol_manifest).resolve()
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    execution = _execution_policy(protocol)
    if args.authorization != execution["authorization_id"]:
        raise RuntimeError("HF replay authorization does not match the frozen protocol")
    current_commit = git_commit(str(_REPO))
    if current_commit != args.expected_code_commit:
        raise RuntimeError(
            f"HEAD {current_commit} != expected audited commit "
            f"{args.expected_code_commit}"
        )
    dirty = _git_status_rows()
    if dirty:
        raise RuntimeError(
            "direct HF replay requires a clean tree: " + "; ".join(dirty)
        )
    manifest_blob = _git_blob_oid(protocol_path, current_commit)
    scratch_dir = _require_external_directory(Path(args.scratch_dir), "--scratch-dir")
    hf_cache_dir = (
        _require_external_directory(Path(args.hf_cache_dir), "--hf-cache-dir")
        if args.hf_cache_dir
        else None
    )
    base_binding = {
        "schema_version": EXECUTION_IDENTITY_SCHEMA_VERSION,
        "code_commit": current_commit,
        "expected_audited_commit": args.expected_code_commit,
        "dirty_tree": False,
        "git_status": [],
        "protocol_manifest": {
            "path": _rel(protocol_path),
            "sha256": _sha256_file(protocol_path),
            "git_blob_oid": manifest_blob,
        },
        "argv": [
            "python",
            "scripts/run_uncertainty_format_recheck.py",
            *list(raw_argv),
        ],
        "authorization": {
            "id": args.authorization,
            "scope": execution["authorization_scope"],
        },
        "scratch_dir": str(scratch_dir),
        "hf_cache_dir": str(hf_cache_dir) if hf_cache_dir is not None else None,
        "resource_guards": dict(execution["resource_guards"]),
    }
    base_binding["argv_sha256"] = _canonical_hash(base_binding["argv"])
    return protocol_path, protocol, base_binding, scratch_dir, hf_cache_dir


def _assert_execution_binding_current(
    binding: Dict[str, object],
    *,
    protocol_path: Path,
    raw_argv: Sequence[str],
    model_identities: Dict[str, Dict[str, object]],
    out_dir: Path,
    scratch_dir: Path,
    activation_cache_dir: Path,
    hf_cache_dir: Optional[Path],
    stage: str,
) -> Dict[str, object]:
    current_commit = git_commit(str(_REPO))
    if current_commit != binding["code_commit"]:
        raise RuntimeError(
            f"{stage}: code commit changed from {binding['code_commit']} "
            f"to {current_commit}"
        )
    dirty = _git_status_rows()
    if dirty:
        raise RuntimeError(f"{stage}: repository became dirty: {'; '.join(dirty)}")
    manifest = dict(binding["protocol_manifest"])
    if _sha256_file(protocol_path) != manifest["sha256"]:
        raise RuntimeError(f"{stage}: protocol manifest hash changed")
    if _git_blob_oid(protocol_path, current_commit) != manifest["git_blob_oid"]:
        raise RuntimeError(f"{stage}: protocol manifest git blob changed")
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    execution = _execution_policy(protocol)
    authorization = dict(binding["authorization"])
    if execution["authorization_id"] != authorization["id"]:
        raise RuntimeError(f"{stage}: protocol authorization changed")
    current_argv = [
        "python",
        "scripts/run_uncertainty_format_recheck.py",
        *list(raw_argv),
    ]
    if current_argv != binding["argv"]:
        raise RuntimeError(f"{stage}: direct-run argv changed")
    for identity in model_identities.values():
        _verify_model_identity(identity)
    environment = _assert_resource_guards(
        dict(binding["resource_guards"]),
        out_dir=out_dir,
        scratch_dir=scratch_dir,
        activation_cache_dir=activation_cache_dir,
        hf_cache_dir=hf_cache_dir,
        stage=stage,
    )
    if _stable_environment_identity(environment) != binding["environment_identity"]:
        raise RuntimeError(f"{stage}: CUDA/software environment identity changed")
    return environment


def _cell_key(method: str, model_label: str) -> str:
    return f"{method}__{model_label}"


def _axis_rows(payload: Dict) -> List[Dict]:
    rows = payload.get("axes")
    if rows is None:
        rows = payload.get("axis_results")
    if not isinstance(rows, list):
        raise ValueError("frozen result lacks axes/axis_results list")
    return rows


def load_frozen_cell_config(frozen_root: Path, method: str, model_label: str) -> FrozenCellConfig:
    cell_key = _cell_key(method, model_label)
    path = Path(frozen_root) / f"cell_{cell_key}" / "c2b_adjudication_results.json"
    if not path.exists():
        raise FileNotFoundError(f"missing frozen E-0006 cell artifact: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    axis_rows = [r for r in _axis_rows(payload) if r.get("axis") == AXIS]
    if len(axis_rows) != 1:
        raise ValueError(f"{path}: expected exactly one {AXIS} row, got {len(axis_rows)}")
    row = axis_rows[0]
    dev = dict(row.get("dev_selection") or {})
    frozen_params = dict(payload.get("frozen_params") or {})
    if int(frozen_params.get("k_samples", adj.K_SAMPLES)) != adj.K_SAMPLES:
        raise ValueError(f"{path}: frozen k_samples mismatch: {frozen_params.get('k_samples')}")
    if str(payload.get("backend")) != "hf":
        raise ValueError(f"{path}: expected frozen hf result, got backend={payload.get('backend')!r}")
    if str(payload.get("steering_method")) != method:
        raise ValueError(f"{path}: method mismatch")

    neutral_prompt = c1.load_neutral_prompts()[0]
    c1_info = dict((payload.get("c1_layer_info") or {}).get(AXIS) or {})
    sigma = float(c1_info.get("sigma", (payload.get("alpha_scale_by_axis") or {}).get(AXIS, 1.0)))
    return FrozenCellConfig(
        cell_key=cell_key,
        method=method,
        model_label=model_label,
        model_id=str(payload.get("model") or ""),
        layer=int(row["layer"]),
        frozen_alpha=float(dev["frozen_alpha"]),
        best_prompt_id=str(dev["best_prompt_id"]),
        best_prompt_text=str(dev["best_prompt_text"]),
        neutral_prompt=str(neutral_prompt),
        sigma=sigma,
        source_result_file=_rel(path),
        source_config_fingerprint=str(payload.get("config_fingerprint", "")),
        source_mean_diff=float(row.get("mean_diff", math.nan)),
    )


def load_uncertainty_items(
    *,
    use_fixture: bool,
    n_items: Optional[int],
    frozen_items_path: Optional[Path] = None,
) -> List[Dict]:
    if use_fixture:
        task = c2b_tasks.load_c2b_task(AXIS, use_fixture=True)
        items = list(task.items)
    elif frozen_items_path is not None:
        path = Path(frozen_items_path)
        if not path.is_file():
            raise FileNotFoundError(f"missing frozen uncertainty item snapshot: {path}")
        items = []
        with open(path, "r", encoding="utf-8") as fh:
            for line_no, line in enumerate(fh, 1):
                if not line.strip():
                    continue
                row = json.loads(line)
                try:
                    items.append({
                        "id": str(row["id"]),
                        "prompt": str(row["prompt"]),
                        "answer": row["answer"],
                        "aliases": list(row.get("aliases") or []),
                    })
                except KeyError as exc:
                    raise ValueError(
                        f"{path}:{line_no}: frozen item missing {exc.args[0]!r}"
                    ) from exc
    else:
        items = c2b_tasks.load_uncertainty_set()
    cap = n_items if n_items is not None else adj.N_ITEMS_BY_AXIS[AXIS]
    return list(items)[: int(cap)]


def split_items(items: Sequence[Dict], seed: int) -> Dict[str, List[Dict]]:
    ids = [str(it["id"]) for it in items]
    if len(ids) != len(set(ids)):
        duplicates = sorted({item_id for item_id in ids if ids.count(item_id) > 1})
        raise ValueError(f"duplicate uncertainty item ids: {duplicates}")
    by_id = {str(it["id"]): it for it in items}
    split = adj.split_dev_test(list(by_id.keys()), dev_fraction=adj.DEV_FRACTION, seed=seed)
    dev_ids = list(split.dev_ids)
    test_ids = list(split.test_ids)
    if len(dev_ids) != len(set(dev_ids)) or len(test_ids) != len(set(test_ids)):
        raise ValueError("DEV/TEST splitter returned duplicate ids")
    if set(dev_ids) & set(test_ids):
        raise ValueError("DEV/TEST splitter returned overlapping ids")
    if set(dev_ids) | set(test_ids) != set(ids):
        raise ValueError("DEV/TEST splitter returned missing or extra ids")
    return {
        "dev": [by_id[i] for i in dev_ids],
        "test": [by_id[i] for i in test_ids],
    }


def score_uncertainty_record(text: str, item: Dict) -> Dict[str, object]:
    parsed_conf = scorers.parse_confidence(text)
    format_compliant = parsed_conf is not None
    imputed_conf = float(parsed_conf) if parsed_conf is not None else 0.5
    correct = int(scorers.item_is_correct(item, text))
    return {
        "parse_confidence": parsed_conf,
        "format_compliant": bool(format_compliant),
        "item_is_correct": correct,
        "imputed_confidence": imputed_conf,
        "per_item_1minus_brier": scorers.per_item_brier(correct, imputed_conf),
    }


def _condition_instruction_and_alpha(cfg: FrozenCellConfig, condition: str) -> Tuple[str, float, float]:
    if condition == "prompt":
        return cfg.best_prompt_text, 0.0, 0.0
    if condition == "baseline":
        return cfg.neutral_prompt, 0.0, 0.0
    if condition == "steer":
        effective = sigma_scaled_alpha(cfg.frozen_alpha, cfg.sigma) if cfg.method == "iti" else cfg.frozen_alpha
        return cfg.neutral_prompt, cfg.frozen_alpha, effective
    raise ValueError(f"unknown condition {condition!r}")


def _call_seed(base_seed: int, item: Dict, effective_alpha: float, sample_index: int) -> int:
    sampler = BackendOutcomeSampler(SyntheticC2bTaskBackend(AXIS, [item]), seed=base_seed)
    return sampler._call_seed(AXIS, item, effective_alpha, sample_index)


def _truncate_raw(text: str, max_chars: int) -> Tuple[str, bool]:
    text = str(text)
    if max_chars <= 0 or len(text) <= max_chars:
        return text, False
    suffix = " ...[truncated]"
    return text[: max(0, max_chars - len(suffix))] + suffix, True


def _derive_hf_direction(cfg: FrozenCellConfig, model_id: str, activation_cache_dir: Path,
                         n_extraction: int, seed: int,
                         model_identity: Dict[str, object]) -> Tuple[np.ndarray, Dict[str, object]]:
    from cognitive_console.activations.provider import HFActivationProvider

    device, dtype = p0._pick_device(), p0._pick_dtype()
    provider = HFActivationProvider(
        model_id,
        device=device,
        dtype=dtype,
        cache_dir=str(activation_cache_dir),
    )
    _, tokenizer, _ = provider.hf_handles()
    runtime_template = getattr(tokenizer, "chat_template", None)
    if not isinstance(runtime_template, str) or not runtime_template:
        raise RuntimeError(
            f"{cfg.cell_key}: runtime tokenizer has no string chat template"
        )
    runtime_chat_template_sha256 = _sha256_text(runtime_template)
    expected_chat_template = dict(model_identity.get("chat_template") or {})
    if runtime_chat_template_sha256 != expected_chat_template.get("sha256"):
        raise RuntimeError(
            f"{cfg.cell_key}: apply_chat_template runtime identity mismatch"
        )
    if cfg.method == "caa":
        direction = p0._extract_direction(provider, AXIS, cfg.layer, n_extraction, seed)
        return direction, {
            "direction_source": "caa_mean_difference_at_frozen_layer",
            "runtime_chat_template_sha256": runtime_chat_template_sha256,
        }

    pairs = c1.load_axis_pairs(AXIS)
    split = c1.make_split(list(pairs.pos.keys()), n_extraction=n_extraction, seed=seed)
    ext_pos = [pairs.pos[p] for p in split.extraction_ids]
    ext_neg = [pairs.neg[p] for p in split.extraction_ids]
    candidate_layers = [ell for ell in provider.available_layers() if ell >= 1]
    iti = extract_iti(
        provider,
        axis=AXIS,
        pos_texts=ext_pos,
        neg_texts=ext_neg,
        layers=candidate_layers,
        selection="nondegenerate",
        neutral_texts=c1.load_neutral_prompts(),
        min_layer=min_layer_for_depth(max(candidate_layers), min_depth_frac=0.2),
        min_depth_frac=0.2,
        n_null=2000,
        null_seed=seed,
    )
    if int(iti.layer) != int(cfg.layer):
        raise RuntimeError(
            f"{cfg.cell_key}: rederived ITI layer {iti.layer} != frozen layer {cfg.layer}; "
            "do not run E-0013 with a non-matching direction."
        )
    sigma_abs_diff = abs(float(iti.sigma) - float(cfg.sigma))
    sigma_limit = max(
        ITI_SIGMA_IDENTITY_ABS_TOL,
        ITI_SIGMA_IDENTITY_REL_TOL * abs(float(cfg.sigma)),
    )
    if sigma_abs_diff > sigma_limit:
        raise RuntimeError(
            f"{cfg.cell_key}: rederived ITI sigma {iti.sigma} != frozen sigma {cfg.sigma}; "
            f"identity tolerance={sigma_limit}. Do not run E-0013 with a "
            "non-matching direction."
        )
    return iti.direction, {
        "direction_source": "iti_probe_direction_rederived_by_frozen_c2_path",
        "rederived_sigma": float(iti.sigma),
        "frozen_sigma_used_for_effective_alpha": float(cfg.sigma),
        "sigma_identity_abs_diff": sigma_abs_diff,
        "sigma_identity_tolerance": sigma_limit,
        "rederived_probe_norm": float(np.linalg.norm(iti.vector)),
        "runtime_chat_template_sha256": runtime_chat_template_sha256,
    }


def _make_backend(backend: str, model_id: str, items: Sequence[Dict], seed: int):
    if backend == "synthetic":
        return SyntheticC2bTaskBackend(AXIS, items, prompt_gain=0.4, alpha_gain=0.1, threshold=0.5)
    from cognitive_console.steering.generate import SteeredHFBackend

    return SteeredHFBackend(model_id, device=p0._pick_device(), dtype=p0._pick_dtype(), seed=seed)


def _checkpoint_batch_path(
    checkpoint_dir: Path, split_name: str, condition: str, start: int
) -> Path:
    return checkpoint_dir / "batches" / (
        f"{split_name}__{condition}__batch-{int(start):05d}.json"
    )


def _expected_batch_jobs(
    *,
    cfg: FrozenCellConfig,
    split_name: str,
    condition: str,
    items: Sequence[Dict],
    seed: int,
) -> Tuple[List[Dict], str, float, float]:
    instruction, requested_alpha, effective_alpha = _condition_instruction_and_alpha(
        cfg, condition
    )
    jobs: List[Dict] = []
    for item in items:
        prompt_text = adj.format_task_input(AXIS, instruction, item)
        for sample_index in range(adj.K_SAMPLES):
            jobs.append(
                {
                    "split": split_name,
                    "condition": condition,
                    "item_id": str(item["id"]),
                    "sample_index": int(sample_index),
                    "sample_seed": int(
                        _call_seed(seed, item, effective_alpha, sample_index)
                    ),
                    "instruction_sha256": _sha256_text(instruction),
                    "prompt_text_sha256": _sha256_text(prompt_text),
                }
            )
    return jobs, instruction, requested_alpha, effective_alpha


def _validate_checkpoint_record(
    record: Dict,
    *,
    expected: Dict,
    cfg: FrozenCellConfig,
    item: Dict,
    model_id: str,
    experiment_id: str,
    instruction: str,
    requested_alpha: float,
    effective_alpha: float,
    backend_name: str,
    model_identity_sha256: str,
    execution_identity_sha256: str,
) -> None:
    exact = {
        "experiment_id": experiment_id,
        "axis": AXIS,
        "cell": cfg.cell_key,
        "method": cfg.method,
        "model_label": cfg.model_label,
        "model_id": model_id,
        "model_identity_sha256": model_identity_sha256,
        "execution_identity_sha256": execution_identity_sha256,
        "split": expected["split"],
        "condition": expected["condition"],
        "item_id": expected["item_id"],
        "sample_index": expected["sample_index"],
        "sample_seed": expected["sample_seed"],
        "layer": cfg.layer,
        "best_prompt_id": (
            cfg.best_prompt_id if expected["condition"] == "prompt" else None
        ),
        "instruction_sha256": expected["instruction_sha256"],
        "prompt_text_sha256": expected["prompt_text_sha256"],
        "synthetic_proxy": bool(backend_name == "synthetic"),
    }
    for key, value in exact.items():
        if record.get(key) != value:
            raise RuntimeError(
                f"{cfg.cell_key}: checkpoint {key} mismatch; "
                f"expected={value!r} got={record.get(key)!r}"
            )
    for key, value in (
        ("requested_alpha", requested_alpha),
        ("effective_alpha", effective_alpha),
    ):
        if not math.isclose(
            float(record.get(key)), float(value), rel_tol=1e-12, abs_tol=1e-12
        ):
            raise RuntimeError(f"{cfg.cell_key}: checkpoint {key} mismatch")
    text = str(record.get("raw_text", ""))
    if not text:
        raise RuntimeError(f"{cfg.cell_key}: checkpoint has empty raw text")
    if record.get("raw_text_sha256") != _sha256_text(text):
        raise RuntimeError(f"{cfg.cell_key}: checkpoint raw-text hash mismatch")
    expected_diag = score_uncertainty_record(text, item)
    for key in (
        "parse_confidence",
        "format_compliant",
        "item_is_correct",
        "imputed_confidence",
        "per_item_1minus_brier",
    ):
        actual, expected_value = record.get(key), expected_diag[key]
        if isinstance(expected_value, float):
            if not math.isclose(
                float(actual), expected_value, rel_tol=1e-12, abs_tol=1e-12
            ):
                raise RuntimeError(
                    f"{cfg.cell_key}: checkpoint scorer field {key} mismatch"
                )
        elif actual != expected_value:
            raise RuntimeError(
                f"{cfg.cell_key}: checkpoint scorer field {key} mismatch"
            )
    if _sha256_text(instruction) != expected["instruction_sha256"]:
        raise RuntimeError(f"{cfg.cell_key}: internal instruction hash mismatch")


def _load_checkpoint_batch(
    path: Path,
    *,
    identity_sha256: str,
    jobs: Sequence[Dict],
    cfg: FrozenCellConfig,
    items_by_id: Dict[str, Dict],
    model_id: str,
    experiment_id: str,
    instruction: str,
    requested_alpha: float,
    effective_alpha: float,
    backend_name: str,
    execution_binding: Dict[str, object],
    model_identity_sha256: str,
) -> Optional[List[Dict]]:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != CHECKPOINT_SCHEMA_VERSION:
        raise RuntimeError(f"{path}: unsupported checkpoint schema")
    if payload.get("checkpoint_identity_sha256") != identity_sha256:
        raise RuntimeError(f"{path}: checkpoint identity mismatch")
    if payload.get("execution_binding") != execution_binding:
        raise RuntimeError(f"{path}: checkpoint execution identity mismatch")
    if payload.get("jobs_sha256") != _canonical_hash(list(jobs)):
        raise RuntimeError(f"{path}: checkpoint job-plan mismatch")
    records = payload.get("records")
    if not isinstance(records, list) or len(records) != len(jobs):
        raise RuntimeError(f"{path}: checkpoint row count mismatch")
    if payload.get("records_sha256") != _canonical_hash(records):
        raise RuntimeError(f"{path}: checkpoint records hash mismatch")
    for record, expected in zip(records, jobs):
        _validate_checkpoint_record(
            record,
            expected=expected,
            cfg=cfg,
            item=items_by_id[str(expected["item_id"])],
            model_id=model_id,
            experiment_id=experiment_id,
            instruction=instruction,
            requested_alpha=requested_alpha,
            effective_alpha=effective_alpha,
            backend_name=backend_name,
            model_identity_sha256=model_identity_sha256,
            execution_identity_sha256=_canonical_hash(execution_binding),
        )
    return [dict(record) for record in records]


def _write_checkpoint_batch(
    path: Path,
    *,
    identity_sha256: str,
    jobs: Sequence[Dict],
    records: Sequence[Dict],
    execution_binding: Dict[str, object],
) -> None:
    payload = {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
        "checkpoint_identity_sha256": identity_sha256,
        "execution_binding": execution_binding,
        "jobs_sha256": _canonical_hash(list(jobs)),
        "records_sha256": _canonical_hash(list(records)),
        "records": list(records),
    }
    _atomic_write_json(path, payload)


def _checkpoint_inventory(paths: Sequence[Path]) -> List[Dict]:
    return [
        {"path": _rel(path), "sha256": _sha256_file(path)}
        for path in sorted(paths, key=lambda value: str(value))
    ]


def _write_or_verify_seal(path: Path, payload: Dict) -> None:
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing != payload:
            raise RuntimeError(f"{path}: replay seal identity mismatch")
        return
    _atomic_write_json(path, payload)


def _activation_cache_inventory(cache_dir: Path) -> List[Dict[str, object]]:
    cache_dir = Path(cache_dir).resolve()
    if not cache_dir.exists():
        return []
    rows: List[Dict[str, object]] = []
    for path in sorted(cache_dir.rglob("*"), key=lambda value: str(value)):
        if not path.is_file():
            continue
        relative = path.relative_to(cache_dir).as_posix()
        if "/" in relative or path.suffix != ".npy":
            raise RuntimeError(
                f"{cache_dir}: unexpected activation-cache file {relative}"
            )
        key = path.stem
        if not _SHA256_RE.fullmatch(key):
            raise RuntimeError(
                f"{cache_dir}: invalid activation-cache key {key!r}"
            )
        try:
            array = np.load(path, mmap_mode="r", allow_pickle=False)
        except Exception as exc:
            raise RuntimeError(f"{path}: invalid activation cache entry") from exc
        if (
            array.ndim != 1
            or array.size == 0
            or array.dtype.kind != "f"
            or not np.isfinite(array).all()
        ):
            raise RuntimeError(f"{path}: invalid activation vector shape/content")
        rows.append(
            {
                "key": key,
                "path": relative,
                "size_bytes": int(path.stat().st_size),
                "sha256": _sha256_file(path),
            }
        )
    return rows


def _activation_cache_binding(
    cache_dir: Path,
    *,
    model_identity: Dict[str, object],
    execution_binding: Dict[str, object],
) -> Dict[str, object]:
    return {
        "cache_dir": str(Path(cache_dir).resolve()),
        "model_identity_sha256": _canonical_hash(model_identity),
        "execution_identity_sha256": _canonical_hash(execution_binding),
        "device": p0._pick_device(),
        "dtype": p0._pick_dtype(),
    }


def _activation_cache_payload(
    binding: Dict[str, object], inventory: List[Dict[str, object]]
) -> Dict[str, object]:
    return {
        "schema_version": ACTIVATION_CACHE_SCHEMA_VERSION,
        "binding": binding,
        "inventory": inventory,
        "inventory_sha256": _canonical_hash(inventory),
    }


def _activation_cache_identity(
    payload: Dict[str, object], seal_path: Path
) -> Dict[str, object]:
    return {
        **payload,
        "seal_path": _rel(seal_path),
        "seal_sha256": _sha256_file(seal_path),
    }


def _prepare_activation_cache(
    cache_dir: Path,
    *,
    model_identity: Dict[str, object],
    execution_binding: Dict[str, object],
) -> Dict[str, object]:
    cache_dir = Path(cache_dir).resolve()
    seal_path = cache_dir.parent / "activation_cache_identity.json"
    existing_files = (
        [path for path in cache_dir.rglob("*") if path.is_file()]
        if cache_dir.exists()
        else []
    )
    incomplete = [path for path in existing_files if path.name.endswith(".tmp")]
    for path in incomplete:
        path.unlink()
    binding = _activation_cache_binding(
        cache_dir,
        model_identity=model_identity,
        execution_binding=execution_binding,
    )
    inventory = _activation_cache_inventory(cache_dir)
    if inventory and not seal_path.is_file():
        raise RuntimeError(
            f"{cache_dir}: activation cache has data without an identity seal"
        )
    expected = _activation_cache_payload(binding, inventory)
    if seal_path.is_file():
        sealed = json.loads(seal_path.read_text(encoding="utf-8"))
        if sealed.get("schema_version") != ACTIVATION_CACHE_SCHEMA_VERSION:
            raise RuntimeError(f"{seal_path}: unsupported activation-cache seal")
        if sealed.get("binding") != binding:
            raise RuntimeError(f"{seal_path}: activation-cache binding mismatch")
        sealed_inventory = sealed.get("inventory")
        if (
            not isinstance(sealed_inventory, list)
            or sealed.get("inventory_sha256")
            != _canonical_hash(sealed_inventory)
            or sealed_inventory != inventory
        ):
            raise RuntimeError(
                f"{seal_path}: activation-cache content inventory mismatch"
            )
    else:
        _atomic_write_json(seal_path, expected)
    return _activation_cache_identity(expected, seal_path)


def _finalize_activation_cache(
    cache_dir: Path,
    *,
    prepared_identity: Dict[str, object],
    model_identity: Dict[str, object],
    execution_binding: Dict[str, object],
) -> Dict[str, object]:
    cache_dir = Path(cache_dir).resolve()
    seal_path = cache_dir.parent / "activation_cache_identity.json"
    binding = _activation_cache_binding(
        cache_dir,
        model_identity=model_identity,
        execution_binding=execution_binding,
    )
    if prepared_identity.get("binding") != binding:
        raise RuntimeError(f"{seal_path}: activation-cache binding changed")
    before = {
        str(row["path"]): dict(row)
        for row in list(prepared_identity.get("inventory") or [])
    }
    inventory = _activation_cache_inventory(cache_dir)
    after = {str(row["path"]): dict(row) for row in inventory}
    changed = [
        path for path, row in before.items() if after.get(path) != row
    ]
    if changed:
        raise RuntimeError(
            "activation-cache entry changed during direction derivation: "
            + ", ".join(sorted(changed))
        )
    payload = _activation_cache_payload(binding, inventory)
    _atomic_write_json(seal_path, payload)
    verified = json.loads(seal_path.read_text(encoding="utf-8"))
    if verified != payload:
        raise RuntimeError(f"{seal_path}: atomic activation-cache seal failed")
    return _activation_cache_identity(payload, seal_path)


def generate_cell_samples(cfg: FrozenCellConfig, *, backend_name: str, model_id: str,
                          items_by_split: Dict[str, List[Dict]], splits: Sequence[str],
                          out_dir: Path, max_new_tokens: int, temperature: float,
                          seed: int, batch_size: int, raw_text_max_chars: int,
                          n_extraction: int, experiment_id: str,
                          protocol_identity: Optional[Dict[str, object]],
                          item_identity: Dict[str, object],
                          model_identity: Dict[str, object],
                          execution_binding: Dict[str, object],
                          activation_cache_dir: Optional[Path] = None,
                          resource_guard: Optional[Callable[[str], Dict[str, object]]] = None,
                          ) -> Tuple[List[Dict], Dict[str, object]]:
    if resource_guard is not None:
        resource_guard("before_cell")
    activation_cache_identity: Optional[Dict[str, object]] = None
    prepared_activation_cache_identity: Optional[Dict[str, object]] = None
    if backend_name == "hf":
        if activation_cache_dir is None:
            raise RuntimeError("HF replay requires an explicit activation cache directory")
        prepared_activation_cache_identity = _prepare_activation_cache(
            activation_cache_dir,
            model_identity=model_identity,
            execution_binding=execution_binding,
        )
    all_items = [it for sp in splits for it in items_by_split[sp]]
    backend = _make_backend(backend_name, model_id, all_items, seed)
    if backend_name == "synthetic":
        direction = np.ones(8, dtype=np.float64)
        direction_meta = {"direction_source": "synthetic_offline_placeholder"}
    else:
        assert activation_cache_dir is not None
        direction, direction_meta = _derive_hf_direction(
            cfg,
            model_id,
            activation_cache_dir,
            n_extraction,
            seed,
            model_identity,
        )
        assert prepared_activation_cache_identity is not None
        activation_cache_identity = _finalize_activation_cache(
            activation_cache_dir,
            prepared_identity=prepared_activation_cache_identity,
            model_identity=model_identity,
            execution_binding=execution_binding,
        )

    direction_sha256 = _array_sha256(direction)
    execution_identity_sha256 = _canonical_hash(execution_binding)
    model_identity_sha256 = _canonical_hash(model_identity)
    checkpoint_dir = out_dir / "checkpoints"
    checkpoint_identity = {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
        "experiment_id": experiment_id,
        "evidence_scope": (
            "format presence/missingness and pre-specified sensitivity only; "
            "never a replacement scorer result"
        ),
        "cell": cfg.cell_key,
        "method": cfg.method,
        "model_label": cfg.model_label,
        "model_id": model_id,
        "resolved_model_identity": model_identity,
        "model_identity_sha256": model_identity_sha256,
        "execution_binding": execution_binding,
        "execution_identity_sha256": execution_identity_sha256,
        "activation_cache_identity": activation_cache_identity,
        "frozen_source_result": cfg.source_result_file,
        "frozen_source_config_fingerprint": cfg.source_config_fingerprint,
        "layer": cfg.layer,
        "frozen_alpha": cfg.frozen_alpha,
        "sigma": cfg.sigma,
        "best_prompt_id": cfg.best_prompt_id,
        "best_prompt_sha256": _sha256_text(cfg.best_prompt_text),
        "neutral_prompt_sha256": _sha256_text(cfg.neutral_prompt),
        "direction_sha256": direction_sha256,
        "direction_identity": direction_meta,
        "item_identity": item_identity,
        "protocol_manifest": protocol_identity,
        "generation": {
            "seed": seed,
            "sample_seed_algorithm": (
                "BackendOutcomeSampler._call_seed(axis,item,effective_alpha,sample_index)"
            ),
            "k_samples": adj.K_SAMPLES,
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "do_sample": bool(backend_name == "hf"),
            "top_p": None,
            "batch_size": batch_size,
            "raw_text_max_chars": raw_text_max_chars,
            "n_extraction": n_extraction,
            "split_order": list(splits),
            "condition_order": list(CONDITIONS),
            "test_use_policy": TEST_USE_POLICY,
        },
    }
    identity_sha256 = _canonical_hash(checkpoint_identity)
    identity_path = checkpoint_dir / "checkpoint_identity.json"
    identity_payload = {
        "checkpoint_identity_sha256": identity_sha256,
        "checkpoint_identity": checkpoint_identity,
    }
    _write_or_verify_seal(identity_path, identity_payload)

    records: List[Dict] = []
    batch_paths_by_split: Dict[str, List[Path]] = {
        split_name: [] for split_name in splits
    }
    checkpoint_reused = 0
    checkpoint_generated = 0
    checkpoint_generated_by_split = {split_name: 0 for split_name in splits}
    test_complete_path = checkpoint_dir / "test_complete.json"
    test_was_complete = test_complete_path.exists()
    items_by_id = {str(item["id"]): item for item in all_items}
    for split_name in splits:
        split_plan: List[Dict] = []
        for condition in CONDITIONS:
            jobs, _, _, _ = _expected_batch_jobs(
                cfg=cfg,
                split_name=split_name,
                condition=condition,
                items=items_by_split[split_name],
                seed=seed,
            )
            split_plan.extend(jobs)
        if split_name == "test":
            _write_or_verify_seal(
                checkpoint_dir / "test_started.json",
                {
                    "checkpoint_identity_sha256": identity_sha256,
                    "execution_binding": execution_binding,
                    "execution_identity_sha256": execution_identity_sha256,
                    "test_use_policy": TEST_USE_POLICY,
                    "test_jobs": len(split_plan),
                    "test_plan_sha256": _canonical_hash(split_plan),
                    "selection_or_tuning_permitted": False,
                },
            )
        for condition in CONDITIONS:
            jobs, instruction, requested_alpha, effective_alpha = _expected_batch_jobs(
                cfg=cfg,
                split_name=split_name,
                condition=condition,
                items=items_by_split[split_name],
                seed=seed,
            )
            steer = SteerConfig(direction=direction, alpha=effective_alpha, layer=cfg.layer)
            for start in range(0, len(jobs), max(1, int(batch_size))):
                if resource_guard is not None:
                    resource_guard(
                        f"before_batch:{cfg.cell_key}:{split_name}:{condition}:{start}"
                    )
                chunk_jobs = jobs[start:start + max(1, int(batch_size))]
                checkpoint_path = _checkpoint_batch_path(
                    checkpoint_dir, split_name, condition, start
                )
                batch_paths_by_split[split_name].append(checkpoint_path)
                cached = _load_checkpoint_batch(
                    checkpoint_path,
                    identity_sha256=identity_sha256,
                    jobs=chunk_jobs,
                    cfg=cfg,
                    items_by_id=items_by_id,
                    model_id=model_id,
                    experiment_id=experiment_id,
                    instruction=instruction,
                    requested_alpha=requested_alpha,
                    effective_alpha=effective_alpha,
                    backend_name=backend_name,
                    execution_binding=execution_binding,
                    model_identity_sha256=model_identity_sha256,
                )
                if cached is not None:
                    records.extend(cached)
                    checkpoint_reused += len(cached)
                    continue
                if split_name == "test" and test_was_complete:
                    raise RuntimeError(
                        f"{cfg.cell_key}: TEST seal exists but checkpoint is missing; "
                        "refusing a second TEST generation"
                    )
                prompts = [
                    adj.format_task_input(
                        AXIS, instruction, items_by_id[str(job["item_id"])]
                    )
                    for job in chunk_jobs
                ]
                seeds = [int(job["sample_seed"]) for job in chunk_jobs]
                if hasattr(backend, "generate_batch"):
                    texts = backend.generate_batch(
                        prompts,
                        steer,
                        max_new_tokens=max_new_tokens,
                        seeds=seeds,
                        do_sample=(backend_name == "hf"),
                        temperature=temperature,
                    )
                else:
                    texts = []
                    for job, prompt in zip(chunk_jobs, prompts):
                        sample_seed = int(job["sample_seed"])
                        try:
                            text = backend.generate(
                                prompt,
                                steer,
                                max_new_tokens=max_new_tokens,
                                do_sample=(backend_name == "hf"),
                                temperature=temperature,
                                seed=sample_seed,
                            )
                        except TypeError:
                            text = backend.generate(prompt, steer, max_new_tokens=max_new_tokens)
                        texts.append(text)
                if len(texts) != len(chunk_jobs):
                    raise RuntimeError(
                        f"{cfg.cell_key}: backend returned {len(texts)} texts "
                        f"for {len(chunk_jobs)} frozen jobs"
                    )
                batch_records: List[Dict] = []
                for job, prompt_text, raw in zip(chunk_jobs, prompts, texts):
                    item = items_by_id[str(job["item_id"])]
                    raw_payload, raw_truncated = _truncate_raw(str(raw), raw_text_max_chars)
                    if raw_truncated:
                        raise RuntimeError(
                            f"{cfg.cell_key}: generated text exceeded the frozen "
                            f"raw-text limit for {job['split']}/"
                            f"{job['condition']}/{job['item_id']}/"
                            f"{job['sample_index']}; no truncated row may enter "
                            "format/missingness evidence"
                        )
                    diag = score_uncertainty_record(str(raw), item)
                    batch_records.append({
                        "experiment_id": experiment_id,
                        "axis": AXIS,
                        "cell": cfg.cell_key,
                        "method": cfg.method,
                        "model_label": cfg.model_label,
                        "model_id": model_id,
                        "model_identity_sha256": model_identity_sha256,
                        "execution_identity_sha256": execution_identity_sha256,
                        "split": split_name,
                        "condition": condition,
                        "item_id": str(item.get("id")),
                        "sample_index": int(job["sample_index"]),
                        "sample_seed": int(job["sample_seed"]),
                        "layer": int(cfg.layer),
                        "requested_alpha": float(requested_alpha),
                        "effective_alpha": float(effective_alpha),
                        "best_prompt_id": cfg.best_prompt_id if condition == "prompt" else None,
                        "instruction_sha256": _sha256_text(instruction),
                        "prompt_text_sha256": _sha256_text(prompt_text),
                        "raw_text": raw_payload,
                        "raw_text_sha256": _sha256_text(str(raw)),
                        "raw_text_truncated": bool(raw_truncated),
                        "synthetic_proxy": bool(backend_name == "synthetic"),
                        **diag,
                    })
                _write_checkpoint_batch(
                    checkpoint_path,
                    identity_sha256=identity_sha256,
                    jobs=chunk_jobs,
                    records=batch_records,
                    execution_binding=execution_binding,
                )
                records.extend(batch_records)
                checkpoint_generated += len(batch_records)
                checkpoint_generated_by_split[split_name] += len(batch_records)
                if resource_guard is not None:
                    resource_guard(
                        f"after_batch:{cfg.cell_key}:{split_name}:{condition}:{start}"
                    )
        split_paths = batch_paths_by_split[split_name]
        split_seal = {
            "checkpoint_identity_sha256": identity_sha256,
            "execution_binding": execution_binding,
            "execution_identity_sha256": execution_identity_sha256,
            "split": split_name,
            "jobs": len(split_plan),
            "plan_sha256": _canonical_hash(split_plan),
            "checkpoint_files": _checkpoint_inventory(split_paths),
        }
        _write_or_verify_seal(
            checkpoint_dir / f"{split_name}_complete.json", split_seal
        )
    if test_was_complete and checkpoint_generated_by_split.get("test", 0):
        raise RuntimeError(
            f"{cfg.cell_key}: TEST was previously sealed but fresh generations occurred"
        )
    checkpoint_paths = [
        path for paths in batch_paths_by_split.values() for path in paths
    ]
    checkpoint_paths.append(identity_path)
    checkpoint_paths.extend(
        checkpoint_dir / f"{split_name}_complete.json" for split_name in splits
    )
    if "test" in splits:
        checkpoint_paths.append(checkpoint_dir / "test_started.json")
    meta = {
        "direction": {**direction_meta, "direction_sha256": direction_sha256},
        "activation_cache": activation_cache_identity,
        "n_records": len(records),
        "splits": list(splits),
        "checkpoint": {
            "schema_version": CHECKPOINT_SCHEMA_VERSION,
            "identity_path": _rel(identity_path),
            "identity_sha256": identity_sha256,
            "execution_identity_sha256": execution_identity_sha256,
            "model_identity_sha256": model_identity_sha256,
            "records_reused": checkpoint_reused,
            "records_generated": checkpoint_generated,
            "files": _checkpoint_inventory(checkpoint_paths),
            "test_use_policy": TEST_USE_POLICY,
            "test_resumed_without_regenerating_completed_batches": True,
        },
    }
    if resource_guard is not None:
        resource_guard("after_cell")
    return records, meta


def _mean_by_item(records: Sequence[Dict], value_field: str = "per_item_1minus_brier") -> Dict[str, float]:
    grouped: Dict[str, List[float]] = {}
    for r in records:
        grouped.setdefault(str(r["item_id"]), []).append(float(r[value_field]))
    return {item_id: float(np.mean(vals)) for item_id, vals in grouped.items()}


def _paired_delta(
    records: Sequence[Dict], a: str, b: str, value_field: str = "per_item_1minus_brier"
) -> Tuple[float, List[float]]:
    by_cond = {
        a: _mean_by_item([r for r in records if r["condition"] == a], value_field=value_field),
        b: _mean_by_item([r for r in records if r["condition"] == b], value_field=value_field),
    }
    ids = sorted(set(by_cond[a]) & set(by_cond[b]))
    diffs = [by_cond[a][i] - by_cond[b][i] for i in ids]
    return (float(np.mean(diffs)) if diffs else math.nan), diffs


def _ci_from_diffs(diffs: Sequence[float], bootstrap_b: int, seed: int) -> Dict[str, object]:
    if not diffs:
        return {"point": math.nan, "ci_lo": math.nan, "ci_hi": math.nan, "n_items": 0}
    ci = adj.cluster_bootstrap_ci(np.asarray(diffs, dtype=float), b=bootstrap_b,
                                  ci_level=0.95, seed=seed, cluster=True)
    return {
        "point": ci.point,
        "ci_lo": ci.ci_lo,
        "ci_hi": ci.ci_hi,
        "ci_level": ci.ci_level,
        "bootstrap_b": int(bootstrap_b),
        "n_items": len(diffs),
    }


def _compliant_pair_diffs(records: Sequence[Dict], a: str, b: str) -> Tuple[List[float], int]:
    keyed: Dict[Tuple[str, int], Dict[str, Dict]] = {}
    for r in records:
        if r["condition"] not in {a, b}:
            continue
        key = (str(r["item_id"]), int(r["sample_index"]))
        keyed.setdefault(key, {})[str(r["condition"])] = r
    by_item: Dict[str, List[float]] = {}
    n_pairs = 0
    for (item_id, _sample_index), pair in keyed.items():
        if a not in pair or b not in pair:
            continue
        if not (pair[a]["format_compliant"] and pair[b]["format_compliant"]):
            continue
        n_pairs += 1
        by_item.setdefault(item_id, []).append(
            float(pair[a]["per_item_1minus_brier"]) - float(pair[b]["per_item_1minus_brier"])
        )
    return [float(np.mean(vals)) for _, vals in sorted(by_item.items())], n_pairs


def _score_with_bound(record: Dict, *, dropped_score: float) -> float:
    if bool(record["format_compliant"]):
        return float(record["per_item_1minus_brier"])
    return float(dropped_score)


def _worst_case_bounds(records: Sequence[Dict]) -> Dict[str, object]:
    rows = []
    for steer_drop_score, prompt_drop_score, label in [
        (0.0, 1.0, "least_favorable_to_steer"),
        (1.0, 0.0, "most_favorable_to_steer"),
    ]:
        adjusted = []
        for r in records:
            if r["condition"] not in {"steer", "prompt"}:
                continue
            rr = dict(r)
            rr["bounded_score"] = _score_with_bound(
                r,
                dropped_score=steer_drop_score if r["condition"] == "steer" else prompt_drop_score,
            )
            adjusted.append(rr)
        delta, diffs = _paired_delta(adjusted, "steer", "prompt", value_field="bounded_score")
        rows.append({"variant": label, "delta": delta, "n_items": len(diffs)})
    return {"bounds": rows}


def reanalyse(records: Sequence[Dict], *, bootstrap_b: int, seed: int) -> Dict[str, object]:
    by_cell: Dict[str, Dict[str, object]] = {}
    for cell in sorted({str(r["cell"]) for r in records}):
        cell_records = [r for r in records if str(r["cell"]) == cell and str(r["split"]) == "test"]
        cond_rows: Dict[str, Dict[str, object]] = {}
        for cond in CONDITIONS:
            rs = [r for r in cell_records if r["condition"] == cond]
            compliant = sum(1 for r in rs if bool(r["format_compliant"]))
            cond_rows[cond] = {
                "n_samples": len(rs),
                "n_format_compliant": compliant,
                "format_compliance_rate": compliant / len(rs) if rs else math.nan,
                "n_format_dropped": len(rs) - compliant,
                "format_dropped_rate": (len(rs) - compliant) / len(rs) if rs else math.nan,
                "mean_frozen_imputed_1minus_brier": (
                    float(np.mean([float(r["per_item_1minus_brier"]) for r in rs])) if rs else math.nan
                ),
            }
        all_delta, all_diffs = _paired_delta(cell_records, "steer", "prompt")
        compliant_diffs, n_compliant_pairs = _compliant_pair_diffs(cell_records, "steer", "prompt")
        by_cell[cell] = {
            "conditions": cond_rows,
            "frozen_uncertainty_delta_steer_minus_prompt_as_run_imputed": {
                "point": all_delta,
                "n_items": len(all_diffs),
            },
            "format_compliant_only_delta_steer_minus_prompt": {
                **_ci_from_diffs(compliant_diffs, bootstrap_b, seed),
                "n_compliant_sample_pairs": n_compliant_pairs,
                "restriction": "paired item/sample rows where both steer and prompt parsed confidence",
            },
            "sensitivity": {
                "drop_imputed": {
                    **_ci_from_diffs(compliant_diffs, bootstrap_b, seed),
                    "equivalent_to": "format_compliant_only_delta_steer_minus_prompt",
                },
                "worst_case_imputation_bounds": _worst_case_bounds(cell_records),
            },
        }
    return {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utcnow(),
        "headline_questions": {
            "does_harm_survive_format_compliant_only": (
                "inspect each cell's format_compliant_only_delta_steer_minus_prompt CI"
            ),
            "is_format_compliance_materially_different": (
                "compare condition format_compliance_rate for steer vs prompt/baseline"
            ),
        },
        "test_split_only": by_cell,
    }


def _legacy_model_label_key(model_ref: str) -> str:
    """Compatibility label for immutable legacy artifacts, never run identity."""
    parts = [p for p in str(model_ref).strip().replace(os.sep, "/").replace("\\", "/").split("/") if p]
    return (parts[-1] if parts else str(model_ref)).strip().lower()


def _looks_like_local_path(model_ref: str) -> bool:
    ref = str(model_ref).strip()
    return (
        ref.startswith(("/", "\\", "./", ".\\", "../", "..\\"))
        or (len(ref) >= 3 and ref[1] == ":" and ref[2] in {"/", "\\"})
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="E-0013 uncertainty format-compliance recheck")
    ap.add_argument("--experiment-id", default=EXPERIMENT_ID)
    ap.add_argument("--backend", choices=["synthetic", "hf"], default="synthetic")
    ap.add_argument("--frozen-root", default=str(DEFAULT_FROZEN_ROOT))
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    ap.add_argument("--qwen-model", default=None,
                    help="override Qwen model path/id; default reuses frozen cell artifact model")
    ap.add_argument("--llama-model", default=None,
                    help="override Llama model path/id; default reuses frozen cell artifact model")
    ap.add_argument("--qwen-revision", default=None)
    ap.add_argument("--llama-revision", default=None)
    ap.add_argument("--expected-code-commit", default=None)
    ap.add_argument("--authorization", default=None)
    ap.add_argument(
        "--scratch-dir",
        default=None,
        help="explicit external scratch directory; mandatory for HF replay",
    )
    ap.add_argument(
        "--hf-cache-dir",
        default=None,
        help="explicit external Hugging Face cache; mandatory for HF repo ids",
    )
    ap.add_argument("--cells", nargs="*", default=sorted(arm.FROZEN_CELL_KEYS))
    ap.add_argument("--splits", nargs="*", choices=["dev", "test"], default=["dev", "test"])
    ap.add_argument("--n-items", type=int, default=None, help="synthetic/debug cap only")
    ap.add_argument("--n-extraction", type=int, default=DEFAULT_N_EXTRACTION)
    ap.add_argument("--bootstrap-b", type=int, default=adj.BOOTSTRAP_B)
    ap.add_argument("--allow-underpowered", action="store_true")
    ap.add_argument("--max-new-tokens", type=int, default=DEFAULT_MAX_NEW_TOKENS)
    ap.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--raw-text-max-chars", type=int, default=8000)
    ap.add_argument(
        "--frozen-items",
        default=None,
        help="committed frozen 80-item JSONL snapshot; mandatory for manifest-pinned hf replay",
    )
    ap.add_argument(
        "--protocol-manifest",
        default=None,
        help="frozen four-cell replay manifest; hard-validates items/settings/cell identities",
    )
    ap.add_argument(
        "--resume-incomplete",
        action="store_true",
        help=(
            "resume only identity-matching checkpoints/finalization in an isolated "
            "replay directory; completed artifacts are never regenerated"
        ),
    )
    return ap


def _validate_generation_identity(
    args, frozen_cell: Optional[FrozenCellConfig] = None, requested_model: Optional[str] = None
) -> Optional[str]:
    expected = {
        "--max-new-tokens": (args.max_new_tokens, DEFAULT_MAX_NEW_TOKENS),
        "--temperature": (args.temperature, DEFAULT_TEMPERATURE),
        "--seed": (args.seed, DEFAULT_SEED),
    }
    effective_model = requested_model or (frozen_cell.model_id if frozen_cell is not None else None)
    mismatches = [f"{k}={got!r} (expected {want!r})" for k, (got, want) in expected.items() if got != want]
    if mismatches:
        raise SystemExit(
            "E-0013 must use the E-0006 generation identity; mismatches: "
            + ", ".join(mismatches)
        )
    if args.bootstrap_b < adj.BOOTSTRAP_B and not args.allow_underpowered:
        raise SystemExit(
            f"--bootstrap-b {args.bootstrap_b} < frozen {adj.BOOTSTRAP_B}; "
            "pass --allow-underpowered only for synthetic smoke/debug."
        )
    if args.backend == "hf" and args.n_items is not None:
        raise SystemExit("--n-items is forbidden for hf E-0013; use the frozen full uncertainty N")
    return effective_model if frozen_cell is not None else None


def _parse_cell(cell_key: str) -> Tuple[str, str]:
    method, model_label = str(cell_key).split("__", 1)
    if method not in {"caa", "iti"}:
        raise ValueError(f"bad method in cell {cell_key!r}")
    if model_label not in {"qwen2.5-7b", "llama3-8b"}:
        raise ValueError(f"bad model label in cell {cell_key!r}")
    return method, model_label


def _validate_protocol_manifest(
    args,
    *,
    frozen_configs: Dict[str, FrozenCellConfig],
    items: Sequence[Dict],
    items_by_split: Dict[str, List[Dict]],
) -> Optional[Dict[str, object]]:
    if not args.protocol_manifest:
        return None
    path = Path(args.protocol_manifest).resolve()
    payload = json.loads(path.read_text(encoding="utf-8"))
    generation = dict(payload.get("generation") or {})
    expected_values = {
        "seed": args.seed,
        "k_samples": adj.K_SAMPLES,
        "max_new_tokens": args.max_new_tokens,
        "temperature": args.temperature,
        "do_sample": bool(args.backend == "hf"),
        "top_p": None,
        "batch_size": args.batch_size,
        "n_extraction": args.n_extraction,
        "raw_text_max_chars": args.raw_text_max_chars,
    }
    mismatches = [
        f"{key}: manifest={generation.get(key)!r}, runner={actual!r}"
        for key, actual in expected_values.items()
        if generation.get(key) != actual
    ]
    if tuple(generation.get("split_order") or ()) != ("dev", "test"):
        mismatches.append("manifest split_order is not the frozen DEV-then-TEST order")
    if tuple(generation.get("condition_order") or ()) != CONDITIONS:
        mismatches.append("manifest condition_order mismatch")
    if generation.get("test_use_policy") != TEST_USE_POLICY:
        mismatches.append("manifest TEST-use policy mismatch")
    evidence_scope = dict(payload.get("evidence_scope") or {})
    if evidence_scope.get("frozen_results_replaced") is not False:
        mismatches.append("manifest permits frozen-result replacement")
    if evidence_scope.get("new_scorer_result_created") is not False:
        mismatches.append("manifest permits a new scorer result")
    item_spec = dict(generation.get("item_artifact") or {})
    if args.backend == "hf":
        if tuple(args.splits) != ("dev", "test"):
            mismatches.append(
                f"split order: manifest requires ('dev', 'test'), runner={tuple(args.splits)!r}"
            )
        if not args.frozen_items:
            mismatches.append("hf replay requires --frozen-items from the protocol manifest")
        else:
            actual_item_path = Path(args.frozen_items).resolve()
            manifest_item_path = Path(item_spec.get("path", ""))
            if not manifest_item_path.is_absolute():
                manifest_item_path = (_REPO / manifest_item_path).resolve()
            if actual_item_path != manifest_item_path:
                mismatches.append(
                    f"item path: manifest={manifest_item_path}, runner={actual_item_path}"
                )
            elif _sha256_file(actual_item_path) != item_spec.get("sha256"):
                mismatches.append("frozen item artifact sha256 mismatch")
    canonical_items = [
        {
            "id": str(item["id"]),
            "prompt": str(item["prompt"]),
            "answer": item["answer"],
            "aliases": list(item.get("aliases") or []),
        }
        for item in items
    ]
    if item_spec:
        if len(canonical_items) != int(item_spec.get("item_count", -1)):
            mismatches.append("frozen item count mismatch")
        if _canonical_hash(canonical_items) != item_spec.get("canonical_items_sha256"):
            mismatches.append("canonical frozen item hash mismatch")
        for split_name in ("dev", "test"):
            ids = [str(item["id"]) for item in items_by_split[split_name]]
            split_spec = dict((item_spec.get("splits") or {}).get(split_name) or {})
            if len(ids) != int(split_spec.get("count", -1)):
                mismatches.append(f"{split_name} count mismatch")
            if _canonical_hash(ids) != split_spec.get("ids_sha256"):
                mismatches.append(f"{split_name} item-id hash mismatch")
    manifest_cells = dict(payload.get("cells") or {})
    for cell_key, cfg in frozen_configs.items():
        if cell_key not in manifest_cells:
            mismatches.append(f"cell missing from protocol manifest: {cell_key}")
            continue
        cell_spec = dict(manifest_cells[cell_key])
        expected = dict(cell_spec.get("expected") or {})
        actuals = {
            "method": cfg.method,
            "model_label": cfg.model_label,
            "legacy_model_label_key": _legacy_model_label_key(cfg.model_id),
            "layer": cfg.layer,
            "frozen_alpha": cfg.frozen_alpha,
            "best_prompt_id": cfg.best_prompt_id,
            "best_prompt_sha256": _sha256_text(cfg.best_prompt_text),
            "neutral_prompt_sha256": _sha256_text(cfg.neutral_prompt),
            "source_config_fingerprint": cfg.source_config_fingerprint,
        }
        for key, actual in actuals.items():
            if expected.get(key) != actual:
                mismatches.append(
                    f"{cell_key}.{key}: manifest={expected.get(key)!r}, runner={actual!r}"
                )
        if not math.isclose(
            float(expected.get("sigma", math.nan)),
            float(cfg.sigma),
            rel_tol=1e-10,
            abs_tol=1e-10,
        ):
            mismatches.append(f"{cell_key}.sigma mismatch")
        frozen_spec = dict(cell_spec.get("frozen_result") or {})
        frozen_path = Path(cfg.source_result_file)
        if not frozen_path.is_absolute():
            frozen_path = (_REPO / frozen_path).resolve()
        if _sha256_file(frozen_path) != frozen_spec.get("sha256"):
            mismatches.append(f"{cell_key} frozen result sha256 mismatch")
    if mismatches:
        raise SystemExit(
            "protocol-manifest identity check failed: " + "; ".join(mismatches)
        )
    return {
        "path": _rel(path),
        "sha256": _sha256_file(path),
        "schema_version": payload.get("schema_version"),
        "experiment_id": payload.get("experiment_id"),
        "evidence_scope": payload.get("evidence_scope"),
    }


def main(argv: Optional[List[str]] = None) -> int:
    raw_argv = list(argv) if argv is not None else list(sys.argv[1:])
    args = build_parser().parse_args(raw_argv)
    _validate_generation_identity(args)
    guarded_protocol_path: Optional[Path] = None
    guarded_protocol: Optional[Dict] = None
    base_execution_binding: Optional[Dict[str, object]] = None
    scratch_dir: Optional[Path] = None
    hf_cache_dir: Optional[Path] = None
    if args.backend == "hf":
        (
            guarded_protocol_path,
            guarded_protocol,
            base_execution_binding,
            scratch_dir,
            hf_cache_dir,
        ) = _prepare_hf_execution_guard(args, raw_argv=raw_argv)
    out_dir = Path(args.out_dir).resolve()
    if out_dir == DEFAULT_OUT_DIR.resolve() and args.resume_incomplete:
        raise SystemExit(
            "--resume-incomplete is forbidden for the original E-0013 directory"
        )
    completed_artifacts = [
        out_dir / "samples.jsonl",
        out_dir / "reanalysis.json",
        out_dir / "run_manifest.json",
    ]
    existing = [path for path in completed_artifacts if path.exists()]
    if existing and not args.resume_incomplete:
        raise SystemExit(
            "refusing to overwrite existing E-0013 artifacts: "
            + ", ".join(_rel(path) for path in existing)
        )
    out_dir.mkdir(parents=True, exist_ok=True)
    frozen_configs: Dict[str, FrozenCellConfig] = {}
    model_ids: Dict[str, str] = {}
    model_identities: Dict[str, Dict[str, object]] = {}
    model_identity_by_label: Dict[str, Dict[str, object]] = {}
    model_load_path_by_label: Dict[str, str] = {}
    for cell_key in args.cells:
        method, model_label = _parse_cell(cell_key)
        cfg = load_frozen_cell_config(Path(args.frozen_root), method, model_label)
        override_model = (
            args.qwen_model if model_label == "qwen2.5-7b" else args.llama_model
        )
        if args.backend == "hf" and override_model is None:
            assert guarded_protocol is not None
            override_model = str(
                _execution_policy(guarded_protocol)["model_identity"][model_label][
                    "hf_repo_id"
                ]
            )
        model_ids[cell_key] = _validate_generation_identity(
            args, frozen_cell=cfg, requested_model=override_model
        )
        frozen_configs[cell_key] = cfg
    use_fixture = args.backend == "synthetic"
    frozen_items_path = Path(args.frozen_items).resolve() if args.frozen_items else None
    items = load_uncertainty_items(
        use_fixture=use_fixture,
        n_items=args.n_items,
        frozen_items_path=frozen_items_path,
    )
    items_by_split = split_items(items, args.seed)
    protocol_identity = _validate_protocol_manifest(
        args,
        frozen_configs=frozen_configs,
        items=items,
        items_by_split=items_by_split,
    )
    protected_snapshot = (
        _protected_protocol_snapshot(guarded_protocol)
        if args.backend == "hf" and guarded_protocol is not None
        else {}
    )
    execution_binding: Dict[str, object]
    environment_at_start: Optional[Dict[str, object]] = None
    if args.backend == "hf":
        assert guarded_protocol_path is not None
        assert guarded_protocol is not None
        assert base_execution_binding is not None
        assert scratch_dir is not None
        execution = _execution_policy(guarded_protocol)
        resource_policy = dict(execution["resource_guards"])
        pre_activation_cache = scratch_dir / "activation-cache-preflight"
        environment_at_start = _assert_resource_guards(
            resource_policy,
            out_dir=out_dir,
            scratch_dir=scratch_dir,
            activation_cache_dir=pre_activation_cache,
            hf_cache_dir=hf_cache_dir,
            stage="before_model_resolution",
        )
        labels = sorted({cfg.model_label for cfg in frozen_configs.values()})
        for model_label in labels:
            if model_label == "qwen2.5-7b":
                model_ref = args.qwen_model or str(
                    execution["model_identity"][model_label]["hf_repo_id"]
                )
                revision = args.qwen_revision
            else:
                model_ref = args.llama_model or str(
                    execution["model_identity"][model_label]["hf_repo_id"]
                )
                revision = args.llama_revision
            load_path, resolved_identity = _resolve_model_identity(
                model_ref=model_ref,
                model_label=model_label,
                revision=revision,
                model_policy=dict(execution["model_identity"][model_label]),
                hf_cache_dir=hf_cache_dir,
            )
            model_load_path_by_label[model_label] = load_path
            model_identity_by_label[model_label] = resolved_identity
        for cell_key, cfg in frozen_configs.items():
            model_ids[cell_key] = model_load_path_by_label[cfg.model_label]
            model_identities[cell_key] = model_identity_by_label[cfg.model_label]
        execution_binding = {
            **base_execution_binding,
            "resolved_model_identities": model_identity_by_label,
            "environment_identity": _stable_environment_identity(
                environment_at_start
            ),
        }
    else:
        for cell_key, cfg in frozen_configs.items():
            model_identities[cell_key] = {
                "kind": "synthetic_offline",
                "model_label": cfg.model_label,
                "configured_ref": model_ids[cell_key],
                "content_sha256": "synthetic-offline",
            }
        execution_binding = {
            "schema_version": "e0013-synthetic-execution-identity-v1",
            "experiment_id": args.experiment_id,
            "backend": "synthetic",
        }
    splits = list(dict.fromkeys(args.splits))
    item_identity = {
        "source": (
            _rel(frozen_items_path)
            if frozen_items_path is not None
            else ("synthetic_fixture" if use_fixture else "live_hf_dataset_loader")
        ),
        "source_sha256": (
            _sha256_file(frozen_items_path) if frozen_items_path is not None else None
        ),
        "canonical_items_sha256": _canonical_hash([
            {
                "id": str(item["id"]),
                "prompt": str(item["prompt"]),
                "answer": item["answer"],
                "aliases": list(item.get("aliases") or []),
            }
            for item in items
        ]),
        "item_count": len(items),
        "split_ids_sha256": {
            name: _canonical_hash([str(item["id"]) for item in rows])
            for name, rows in items_by_split.items()
        },
    }
    cell_records: List[Dict] = []
    cell_meta: Dict[str, object] = {}
    started = utcnow()
    dirty_at_start = _git_dirty()
    t0 = time.time()
    for cell_key in args.cells:
        cfg = frozen_configs[cell_key]
        effective_model_ref = model_ids[cell_key]
        model_id = effective_model_ref
        if args.backend == "synthetic":
            model_id = "synthetic-offline"
        print(
            f"[E-0013] cell={cell_key} backend={args.backend} model={model_id} "
            f"layer={cfg.layer} alpha={cfg.frozen_alpha} prompt={cfg.best_prompt_id}",
            flush=True,
        )
        cell_runtime_dir = (
            out_dir if len(args.cells) == 1 else out_dir / f"cell_{cell_key}"
        )
        activation_cache_dir: Optional[Path] = None
        resource_guard: Optional[Callable[[str], Dict[str, object]]] = None
        environment_before_cell: Optional[Dict[str, object]] = None
        if args.backend == "hf":
            assert scratch_dir is not None
            assert guarded_protocol_path is not None
            _assert_protected_protocol_snapshot(protected_snapshot)
            activation_cache_dir = (
                scratch_dir / f"cell_{cell_key}" / "activations" / "cache"
            )
            activation_cache_dir.parent.mkdir(parents=True, exist_ok=True)
            environment_before_cell = _assert_execution_binding_current(
                execution_binding,
                protocol_path=guarded_protocol_path,
                raw_argv=raw_argv,
                model_identities=model_identity_by_label,
                out_dir=cell_runtime_dir,
                scratch_dir=scratch_dir,
                activation_cache_dir=activation_cache_dir,
                hf_cache_dir=hf_cache_dir,
                stage=f"before_cell:{cell_key}",
            )

            def resource_guard(stage: str, *, _cache=activation_cache_dir):
                return _assert_resource_guards(
                    dict(execution_binding["resource_guards"]),
                    out_dir=cell_runtime_dir,
                    scratch_dir=scratch_dir,
                    activation_cache_dir=_cache,
                    hf_cache_dir=hf_cache_dir,
                    stage=stage,
                )

        recs, meta = generate_cell_samples(
            cfg,
            backend_name=args.backend,
            model_id=model_id,
            items_by_split=items_by_split,
            splits=splits,
            out_dir=cell_runtime_dir,
            max_new_tokens=args.max_new_tokens,
            temperature=args.temperature,
            seed=args.seed,
            batch_size=args.batch_size,
            raw_text_max_chars=args.raw_text_max_chars,
            n_extraction=args.n_extraction,
            experiment_id=args.experiment_id,
            protocol_identity=protocol_identity,
            item_identity=item_identity,
            model_identity=model_identities[cell_key],
            execution_binding=execution_binding,
            activation_cache_dir=activation_cache_dir,
            resource_guard=resource_guard,
        )
        environment_after_cell: Optional[Dict[str, object]] = None
        if args.backend == "hf":
            assert scratch_dir is not None
            assert guarded_protocol_path is not None
            assert activation_cache_dir is not None
            environment_after_cell = _assert_execution_binding_current(
                execution_binding,
                protocol_path=guarded_protocol_path,
                raw_argv=raw_argv,
                model_identities=model_identity_by_label,
                out_dir=cell_runtime_dir,
                scratch_dir=scratch_dir,
                activation_cache_dir=activation_cache_dir,
                hf_cache_dir=hf_cache_dir,
                stage=f"after_cell:{cell_key}",
            )
            _assert_protected_protocol_snapshot(protected_snapshot)
        for rec in recs:
            rec["experiment_id"] = args.experiment_id
        cell_records.extend(recs)
        cell_meta[cell_key] = {
            "frozen_config": cfg.__dict__,
            "frozen_model_id": cfg.model_id,
            "effective_model_ref": effective_model_ref,
            "resolved_model_identity": model_identities[cell_key],
            "run_model_id": model_id,
            "environment_before_cell": environment_before_cell,
            "environment_after_cell": environment_after_cell,
            **meta,
        }

    samples_path = out_dir / "samples.jsonl"
    reanalysis_path = out_dir / "reanalysis.json"
    manifest_path = out_dir / "run_manifest.json"
    _write_once_or_verify_jsonl(samples_path, cell_records)
    computed_analysis = reanalyse(
        cell_records, bootstrap_b=args.bootstrap_b, seed=args.seed
    )
    computed_analysis["experiment_id"] = args.experiment_id
    if reanalysis_path.exists():
        analysis = json.loads(reanalysis_path.read_text(encoding="utf-8"))
        old_comparable = dict(analysis)
        new_comparable = dict(computed_analysis)
        old_comparable.pop("generated_at", None)
        new_comparable.pop("generated_at", None)
        if old_comparable != new_comparable:
            raise RuntimeError(
                f"refusing to overwrite non-identical artifact: {reanalysis_path}"
            )
    else:
        analysis = computed_analysis
        _write_once_or_verify_json(reanalysis_path, analysis)
    manifest = {
        "experiment_id": args.experiment_id,
        "valid_for_paper": False,
        "purpose": (
            "uncertainty format/missingness robustness recheck; creates no "
            "replacement E-0006 scorer result"
        ),
        "evidence_scope": {
            "allowed": [
                "confidence-format presence/missingness",
                "pre-specified complete-case sensitivity",
                "pre-specified adversarial missingness bounds",
            ],
            "frozen_results_replaced": False,
            "new_scorer_result_created": False,
        },
        "backend": args.backend,
        "started_at": started,
        "ended_at": utcnow(),
        "wall_clock_seconds": time.time() - t0,
        "code_commit": git_commit(str(_REPO)),
        "dirty_tree_at_start": dirty_at_start,
        "execution_binding": execution_binding,
        "execution_identity_sha256": _canonical_hash(execution_binding),
        "environment_at_start": environment_at_start,
        "generation_identity": {
            "model_by_cell": {k: v.model_id for k, v in frozen_configs.items()},
            "frozen_model_by_cell": {k: v.model_id for k, v in frozen_configs.items()},
            "effective_model_by_cell": model_ids,
            "resolved_model_identity_by_cell": model_identities,
            "max_new_tokens": args.max_new_tokens,
            "temperature": args.temperature,
            "seed": args.seed,
            "k_samples": adj.K_SAMPLES,
            "batch_size": args.batch_size,
            "n_extraction": args.n_extraction,
            "raw_text_max_chars": args.raw_text_max_chars,
            "do_sample": bool(args.backend == "hf"),
            "top_p": None,
            "test_use_policy": TEST_USE_POLICY,
        },
        "protocol_manifest": protocol_identity,
        "item_identity": item_identity,
        "frozen_root": _rel(Path(args.frozen_root)),
        "cells": cell_meta,
        "artifacts": {
            "samples_jsonl": {
                "path": _rel(samples_path),
                "sha256": _sha256_file(samples_path),
            },
            "reanalysis_json": {
                "path": _rel(reanalysis_path),
                "sha256": _sha256_file(reanalysis_path),
            },
            "run_manifest_json": _rel(manifest_path),
        },
        "synthetic_proxy": bool(args.backend == "synthetic"),
    }
    if manifest_path.exists():
        existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        checks = {
            "experiment_id": args.experiment_id,
            "backend": args.backend,
            "protocol_manifest": protocol_identity,
            "item_identity": item_identity,
            "frozen_root": _rel(Path(args.frozen_root)),
            "execution_binding": execution_binding,
            "execution_identity_sha256": _canonical_hash(execution_binding),
        }
        for key, expected in checks.items():
            if existing_manifest.get(key) != expected:
                raise RuntimeError(
                    f"refusing to overwrite incompatible run manifest: {key}"
                )
        if set(existing_manifest.get("cells") or {}) != set(args.cells):
            raise RuntimeError(
                "refusing to overwrite incompatible run manifest: cells"
            )
        generation_identity = dict(
            existing_manifest.get("generation_identity") or {}
        )
        generation_checks = {
            "max_new_tokens": args.max_new_tokens,
            "temperature": args.temperature,
            "seed": args.seed,
            "k_samples": adj.K_SAMPLES,
            "batch_size": args.batch_size,
            "n_extraction": args.n_extraction,
            "raw_text_max_chars": args.raw_text_max_chars,
            "do_sample": bool(args.backend == "hf"),
            "top_p": None,
            "test_use_policy": TEST_USE_POLICY,
        }
        for key, expected in generation_checks.items():
            if generation_identity.get(key) != expected:
                raise RuntimeError(
                    f"refusing to overwrite incompatible run manifest: "
                    f"generation_identity.{key}"
                )
        artifacts = dict(existing_manifest.get("artifacts") or {})
        if (
            dict(artifacts.get("samples_jsonl") or {}).get("sha256")
            != _sha256_file(samples_path)
            or dict(artifacts.get("reanalysis_json") or {}).get("sha256")
            != _sha256_file(reanalysis_path)
        ):
            raise RuntimeError("existing run manifest artifact hashes do not match")
    else:
        _write_once_or_verify_json(manifest_path, manifest)
    if args.backend == "hf":
        assert scratch_dir is not None
        assert guarded_protocol_path is not None
        for cell_key in args.cells:
            cell_runtime_dir = (
                out_dir if len(args.cells) == 1 else out_dir / f"cell_{cell_key}"
            )
            activation_cache_dir = (
                scratch_dir / f"cell_{cell_key}" / "activations" / "cache"
            )
            _assert_execution_binding_current(
                execution_binding,
                protocol_path=guarded_protocol_path,
                raw_argv=raw_argv,
                model_identities=model_identity_by_label,
                out_dir=cell_runtime_dir,
                scratch_dir=scratch_dir,
                activation_cache_dir=activation_cache_dir,
                hf_cache_dir=hf_cache_dir,
                stage=f"after_artifact_seal:{cell_key}",
            )
            _assert_protected_protocol_snapshot(protected_snapshot)
    print(f"[E-0013] wrote {_rel(samples_path)}")
    print(f"[E-0013] wrote {_rel(reanalysis_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
