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
import io
import json
import os
import platform
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cognitive_console.eval import c2b_tasks
from cognitive_console.experiments import adjudicate_c2b as c2
from cognitive_console.experiments import prompt_steer_composition as comp
from cognitive_console.lineage import git_commit, new_experiment_id, utcnow
from cognitive_console.manifest import ArtifactManifest, write_manifest
from cognitive_console.ops.disk_guard import DiskBudgetError, check_disk_budget, default_guard_paths
from cognitive_console.registry import ExperimentRecord, ExperimentRegistry
from cognitive_console.steering.generate import SteeredHFBackend, SyntheticC2bTaskBackend

from scripts import run_c1_facade as c1
from scripts import run_c2b_adjudication as base
from scripts import run_gpu_phase0 as p0

DEFAULT_OUT_DIR = _REPO / "results" / "E-0017-prompt-steer-composition"
MAX_NEW_TOKENS = 64
BATCH_SIZE = 16
TEMPERATURE = 0.7
N_EXTRACTION = 28
N_STRONG = 16
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


def selection_hash(payload: Dict) -> str:
    clean = dict(payload)
    clean.pop("selection_hash", None)
    clean.pop("started_at", None)
    clean.pop("completed_at", None)
    return comp.canonical_hash(clean)


def test_config_fingerprint(selection: Dict, bootstrap_b: int) -> str:
    return comp.canonical_hash(
        {
            "protocol_id": comp.PROTOCOL_ID,
            "selection_hash": selection["selection_hash"],
            "phase": "TEST",
            "backend": selection["backend"],
            "bootstrap_b": int(bootstrap_b),
        }
    )


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
                or bool(row.get("generation_truncated"))
            )
        )
        return {
            "expected_records": expected,
            "observed_records": observed,
            "coverage": float(observed / expected) if expected else 0.0,
            "parse_rate": float(parse_ok / observed) if observed else 0.0,
            "truncation_rate": float(truncated / observed) if observed else 1.0,
            "identity_ok": not missing_identity and not unexpected_identity,
            "missing_identities": len(missing_identity),
            "unexpected_identities": len(unexpected_identity),
        }


def _load_all_items(backend: str) -> Dict[str, List[Dict]]:
    use_fixture = backend == "synthetic"
    return {
        axis: list(c2b_tasks.load_c2b_task(axis, use_fixture=use_fixture).items)
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


def _build_dev_specs(
    backend: str,
    pools: Dict[str, comp.PoolPlan],
    out_dir: Path,
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

    device, dtype = p0._pick_device(), p0._pick_dtype()
    c1_out = out_dir / "direction_derivation" / "c1"
    provider = HFActivationProvider(
        comp.FROZEN_MODEL,
        device=device,
        dtype=dtype,
        cache_dir=str(c1_out / "activations" / "cache"),
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
):
    def factory(axis: str):
        backend = SyntheticC2bTaskBackend(
            axis,
            all_items[axis],
            prompt_gain=0.4,
            alpha_gain=0.1,
            threshold=0.5,
        )
        return base.TranscriptBackendOutcomeSampler(
            backend,
            do_sample=False,
            seed=comp.SEED,
            batch_size=BATCH_SIZE,
            transcript_collector=collector,
        )

    return factory


def _load_pinned_hf_backend(cache_dir: Path) -> tuple[SteeredHFBackend, str]:
    from cognitive_console.activations.provider import HFActivationProvider

    device, dtype = p0._pick_device(), p0._pick_dtype()
    provider = HFActivationProvider(
        comp.FROZEN_MODEL,
        device=device,
        dtype=dtype,
        cache_dir=str(cache_dir),
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


def _hf_factory(
    collector: PersistentTranscriptCollector,
    *,
    backend: Optional[SteeredHFBackend] = None,
    resolved_revision: Optional[str] = None,
    cache_dir: Optional[Path] = None,
):
    if backend is None:
        if cache_dir is None:
            raise ValueError("cache_dir is required when loading the HF backend")
        backend, resolved_revision = _load_pinned_hf_backend(cache_dir)
    if resolved_revision != comp.FROZEN_MODEL_REVISION:
        raise ValueError(
            "HF sampler revision is not the frozen revision: "
            f"{resolved_revision!r}"
        )

    def factory(_axis: str):
        return base.TranscriptBackendOutcomeSampler(
            backend,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=True,
            temperature=TEMPERATURE,
            seed=comp.SEED,
            batch_size=BATCH_SIZE,
            transcript_collector=collector,
        )

    return factory, str(resolved_revision)


def _base_identity(
    backend: str,
    pools: Dict[str, comp.PoolPlan],
    specs: Sequence[c2.AxisAdjSpec],
) -> Dict:
    by_axis = {spec.axis: spec for spec in specs}
    return {
        "protocol": comp.frozen_protocol_dict(),
        "backend": backend,
        "code_commit": git_commit(str(_REPO)),
        "source_hashes": _source_hashes(),
        "generation": {
            "max_new_tokens": MAX_NEW_TOKENS,
            "batch_size": BATCH_SIZE,
            "temperature": TEMPERATURE,
            "do_sample": backend == "hf",
            "seed": comp.SEED,
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
    out_dir: Path,
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
) -> str:
    registry = ExperimentRegistry(str(out_dir / "experiment-registry.yaml"))
    exp_id = new_experiment_id(registry, prefix, cfg_hash)
    record = ExperimentRecord(
        experiment_id=exp_id,
        hypothesis_id="H4",
        claim_ids=["C2"],
        type=run_type,
        status=status,
        code_commit=git_commit(str(_REPO)),
        dirty_tree=bool(dirty_tree_at_start),
        data_hash=summary.get("data_hash"),
        env_hash=_env_hash(),
        config_hash=cfg_hash,
        model=comp.FROZEN_MODEL if backend == "hf" else "synthetic-offline",
        dataset="fresh TEST outside original C2 first-N pool; original C2 DEV reused only on DEV",
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


def write_authorization_template(path: Path, selection: Dict) -> None:
    payload = {
        "protocol_id": comp.PROTOCOL_ID,
        "selection_hash": selection["selection_hash"],
        "protocol_commit": selection["code_commit"],
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
    out_dir: Path,
    checkpoint_fingerprint: str,
    authorization_file_sha256: Optional[str] = None,
) -> Path:
    sealed_out_dir = Path(str(selection["out_dir"])).resolve()
    if out_dir.resolve() != sealed_out_dir:
        raise SystemExit(
            "[composition] TEST out-dir differs from the DEV-sealed out-dir"
        )
    marker = out_dir / "test_authorization.used.json"
    requested = {
        "protocol_id": comp.PROTOCOL_ID,
        "selection_hash": selection["selection_hash"],
        "authorization_file_sha256": (
            str(authorization_file_sha256)
            if authorization_file_sha256 is not None
            else _sha256_file(auth_path)
        ),
        "out_dir": str(out_dir.resolve()),
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
            and existing.get("out_dir") == requested["out_dir"]
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
        runtime_lock = _acquire_test_runtime_lock(out_dir)
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
        _acquire_test_runtime_lock(out_dir)
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


def _run_dev(args) -> int:
    dirty_tree_at_start = _git_dirty()
    if args.backend == "hf" and dirty_tree_at_start:
        raise SystemExit(
            "[composition] HF DEV requires a clean committed tree for protocol identity"
        )
    if args.backend == "hf" and args.fresh:
        raise SystemExit(
            "[composition] real DEV checkpoints are append-only; use a new out-dir "
            "instead of --fresh"
        )
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    started_at = utcnow()

    guard_paths = default_guard_paths(args.hf_home, args.venv)
    if args.backend == "hf":
        usage = check_disk_budget(
            guard_paths, args.disk_budget_gb, args.disk_ceiling_gb, raise_on_over=True
        )
        print(f"[composition] disk pre-DEV: {usage.message}", flush=True)

    all_items = _load_all_items(args.backend)
    pools = _build_pools(
        args.backend,
        all_items,
        smoke_dev_n=args.smoke_dev_n,
        smoke_test_n=args.smoke_test_n,
    )
    dev_request_hash = comp.canonical_hash(
        {
            "protocol": comp.frozen_protocol_dict(),
            "phase": "DEV",
            "backend": args.backend,
            "out_dir": str(out_dir),
            "code_commit": git_commit(str(_REPO)),
            "source_hashes": _source_hashes(),
            "pool_plans": {axis: pools[axis].to_dict() for axis in comp.AXES},
            "generation": {
                "max_new_tokens": MAX_NEW_TOKENS,
                "batch_size": BATCH_SIZE,
                "temperature": TEMPERATURE,
                "seed": comp.SEED,
            },
            "model_revision_expected": comp.FROZEN_MODEL_REVISION,
        }
    )
    try:
        specs, meta, shared_hf_backend = _build_dev_specs(
            args.backend, pools, out_dir
        )
    except (RuntimeError, MemoryError, ValueError, OSError) as exc:
        failure_reason = f"{type(exc).__name__}: {exc}"
        _register_failure(
            out_dir=out_dir,
            prefix="e0017-composition-dev",
            run_type="diagnostic",
            cfg_hash=dev_request_hash,
            backend=args.backend,
            artifact=out_dir / "direction_derivation",
            started_at=started_at,
            dirty_tree_at_start=dirty_tree_at_start,
            summary={
                "data_hash": comp.canonical_hash(
                    {axis: pools[axis].data_hash for axis in comp.AXES}
                ),
                "phase": "DEV",
            },
            validation_notes="DEV setup failed before selection; no TEST was accessed.",
            failure_reason=failure_reason,
        )
        print(
            f"[composition] DEV direction/model setup failed: "
            f"{failure_reason}"
        )
        return 2
    direction_path = out_dir / "directions.npz"
    direction_hash = _save_directions(direction_path, specs)

    identity = _base_identity(args.backend, pools, specs)
    identity["direction_artifact_sha256"] = direction_hash
    identity["model_revision_expected"] = comp.FROZEN_MODEL_REVISION
    preliminary_hash = comp.canonical_hash(identity)
    collector = PersistentTranscriptCollector(
        out_dir / "dev_checkpoints" / "raw_generations.jsonl",
        preliminary_hash,
        model=str(meta.get("model", "synthetic-offline")),
        method=comp.FROZEN_METHOD,
        backend=args.backend,
        fresh=args.fresh,
    )
    if args.backend == "synthetic":
        sampler_for_axis = _synthetic_factory(all_items, collector)
        resolved_revision = None
    else:
        sampler_for_axis, resolved_revision = _hf_factory(
            collector,
            backend=shared_hf_backend,
            resolved_revision=meta.get("model_revision_resolved"),
        )

    planned = sum(
        len(pools[axis].dev_items)
        * comp.K_SAMPLES
        * (N_STRONG + 1 + 2 * len(comp.ALPHA_GRID))
        for axis in comp.AXES
    )
    progress = c2.ProgressTracker(planned)
    checkpoint = base.TranscriptCheckpointStore(
        out_dir / "dev_checkpoints",
        preliminary_hash,
        seed=comp.SEED,
        fresh=args.fresh,
        collector=collector,
    )
    ctx = c2.RunContext(checkpoint=checkpoint, progress=progress)
    watchdog = base.InactivityWatchdog(progress, args.stall_timeout).start()
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
            out_dir=out_dir,
            prefix="e0017-composition-dev",
            run_type="diagnostic",
            cfg_hash=preliminary_hash,
            backend=args.backend,
            artifact=out_dir / "dev_checkpoints" / "raw_generations.jsonl",
            started_at=started_at,
            dirty_tree_at_start=dirty_tree_at_start,
            summary={
                "data_hash": comp.canonical_hash(
                    {axis: pools[axis].data_hash for axis in comp.AXES}
                ),
                "phase": "DEV",
            },
            validation_notes=(
                "DEV generation failed; append-only checkpoints retained and "
                "TEST was not accessed."
            ),
            failure_reason=failure_reason,
        )
        print(f"[composition] DEV generation failed: {failure_reason}")
        print("[composition] checkpoints retained; rerun the same command without --fresh")
        return 2
    finally:
        watchdog.stop()
        checkpoint.close()

    if args.backend == "hf":
        try:
            usage = check_disk_budget(
                guard_paths,
                args.disk_budget_gb,
                args.disk_ceiling_gb,
                raise_on_over=True,
            )
            print(f"[composition] disk post-DEV: {usage.message}", flush=True)
        except DiskBudgetError as exc:
            failure_reason = f"post-DEV disk budget violation: {exc}"
            _register_failure(
                out_dir=out_dir,
                prefix="e0017-composition-dev",
                run_type="diagnostic",
                cfg_hash=preliminary_hash,
                backend=args.backend,
                artifact=out_dir / "dev_checkpoints" / "raw_generations.jsonl",
                started_at=started_at,
                dirty_tree_at_start=dirty_tree_at_start,
                summary={
                    "data_hash": comp.canonical_hash(
                        {axis: pools[axis].data_hash for axis in comp.AXES}
                    ),
                    "phase": "DEV",
                },
                validation_notes=(
                    "DEV completed generation but failed the frozen post-run disk "
                    "guard; no DEV selection or TEST authorization template was issued."
                ),
                failure_reason=failure_reason,
            )
            print(f"[composition] {failure_reason}", flush=True)
            return 4

    payload = {
        "protocol_id": comp.PROTOCOL_ID,
        "phase": "DEV",
        "scientific_status": (
            "synthetic_smoke_invalid_for_paper"
            if args.backend == "synthetic"
            else "DEV_selection_only_no_TEST_seen"
        ),
        "backend": args.backend,
        "model": comp.FROZEN_MODEL if args.backend == "hf" else "synthetic-offline",
        "model_revision_expected": comp.FROZEN_MODEL_REVISION,
        "model_revision_resolved": resolved_revision,
        "method": comp.FROZEN_METHOD,
        "out_dir": str(out_dir),
        "code_commit": git_commit(str(_REPO)),
        "source_hashes": _source_hashes(),
        "dirty_tree_at_start": dirty_tree_at_start,
        "started_at": started_at,
        "completed_at": utcnow(),
        "preliminary_config_hash": preliminary_hash,
        "direction_artifact": {
            "path": _rel(direction_path),
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
    }
    payload["selection_hash"] = selection_hash(payload)
    selection_path = out_dir / "dev_selection.json"
    _atomic_json(selection_path, payload)
    write_authorization_template(out_dir / "test_authorization.template.json", payload)
    summary = {
        "data_hash": comp.canonical_hash(
            {axis: pools[axis].data_hash for axis in comp.AXES}
        ),
        "eligible_axes": payload["eligible_axes"],
        "selection_hash": payload["selection_hash"],
        "test_seen": False,
    }
    exp_id = _register(
        out_dir=out_dir,
        prefix="e0017-composition-dev",
        run_type="diagnostic",
        status="done",
        cfg_hash=payload["selection_hash"],
        backend=args.backend,
        artifact=selection_path,
        started_at=started_at,
        dirty_tree_at_start=dirty_tree_at_start,
        summary=summary,
        validation_notes=(
            "DEV-only prompt/alpha/power selection. TEST was not generated. "
            "Synthetic runs are pipeline smoke only; real DEV remains invalid for "
            "paper until hostile audit and authorized TEST."
        ),
    )

    print(
        f"[composition] DEV complete: eligible={payload['eligible_axes']} "
        f"selection={payload['selection_hash']} exp={exp_id}",
        flush=True,
    )
    print(f"[composition] wrote {_rel(selection_path)}; TEST remains locked", flush=True)
    return 0


def _run_test(args) -> int:
    if args.fresh:
        raise SystemExit(
            "[composition] TEST checkpoints are append-only; --fresh is forbidden"
        )
    dirty_tree_at_start = _git_dirty()
    out_dir = Path(args.out_dir).resolve()
    selection_path = Path(args.selection_json or out_dir / "dev_selection.json").resolve()
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    if selection_hash(selection) != selection.get("selection_hash"):
        raise SystemExit("[composition] DEV selection artifact identity is invalid")
    if selection.get("protocol_id") != comp.PROTOCOL_ID:
        raise SystemExit("[composition] selection protocol mismatch")
    if not selection.get("eligible_axes"):
        raise SystemExit("[composition] no DEV-eligible axis; TEST must not run")
    if args.backend != selection.get("backend"):
        raise SystemExit("[composition] TEST backend differs from sealed DEV backend")
    if out_dir != Path(str(selection.get("out_dir", ""))).resolve():
        raise SystemExit(
            "[composition] TEST out-dir differs from the DEV-sealed out-dir"
        )
    if args.backend == "hf":
        if dirty_tree_at_start:
            raise SystemExit("[composition] HF TEST requires a clean committed tree")
        if _source_hashes() != selection.get("source_hashes"):
            raise SystemExit(
                "[composition] protocol/source hashes differ from DEV; rerun DEV after code changes"
            )
    if args.bootstrap_b < comp.BOOTSTRAP_B and args.backend == "hf":
        raise SystemExit(
            f"[composition] real TEST requires bootstrap B>={comp.BOOTSTRAP_B}"
        )
    if not args.test_authorization_file:
        raise SystemExit("[composition] TEST requires --test-authorization-file")
    auth_path = Path(args.test_authorization_file).resolve()
    authorization = validate_test_authorization(auth_path, selection)

    guard_paths = default_guard_paths(args.hf_home, args.venv)
    if args.backend == "hf":
        usage = check_disk_budget(
            guard_paths, args.disk_budget_gb, args.disk_ceiling_gb, raise_on_over=True
        )
        print(f"[composition] disk pre-TEST: {usage.message}", flush=True)

    all_items = _load_all_items(args.backend)
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
        out_dir,
        test_fingerprint,
        authorization["_validated_file_sha256"],
    )
    runtime_lock = out_dir / "test_authorization.run.lock"
    started_at = utcnow()
    results: List[comp.AxisCompositionResult] = []
    checkpoint = None
    watchdog = None
    try:
        collector = PersistentTranscriptCollector(
            out_dir / "test_checkpoints" / "raw_generations.jsonl",
            test_fingerprint,
            model=str(selection["model"]),
            method=comp.FROZEN_METHOD,
            backend=args.backend,
            fresh=False,
        )
        if args.backend == "synthetic":
            sampler_for_axis = _synthetic_factory(all_items, collector)
        else:
            sampler_for_axis, resolved = _hf_factory(
                collector,
                cache_dir=out_dir / "test_model_cache",
            )
            if resolved != selection.get("model_revision_resolved"):
                raise ValueError("TEST model revision differs from DEV")

        total = sum(len(spec.items) * comp.K_SAMPLES * 4 for spec in specs)
        progress = c2.ProgressTracker(total)
        checkpoint = base.TranscriptCheckpointStore(
            out_dir / "test_checkpoints",
            test_fingerprint,
            seed=comp.SEED,
            fresh=False,
            collector=collector,
        )
        ctx = c2.RunContext(checkpoint=checkpoint, progress=progress)
        watchdog = base.InactivityWatchdog(progress, args.stall_timeout).start()
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
            out_dir=out_dir,
            prefix="e0017-composition-test",
            run_type="confirmatory",
            cfg_hash=test_fingerprint,
            backend=args.backend,
            artifact=out_dir / "test_checkpoints" / "raw_generations.jsonl",
            started_at=started_at,
            dirty_tree_at_start=dirty_tree_at_start,
            summary={
                "data_hash": comp.canonical_hash(
                    {axis: pools[axis].data_hash for axis in comp.AXES}
                ),
                "selection_hash": selection["selection_hash"],
                "phase": "TEST",
            },
            validation_notes=(
                "Authorized TEST attempt failed; same-config checkpoint resume "
                "is allowed, but a second TEST identity is forbidden."
            ),
            failure_reason=failure_reason,
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

    post_test_disk_violation = None
    if args.backend == "hf":
        try:
            usage = check_disk_budget(
                guard_paths,
                args.disk_budget_gb,
                args.disk_ceiling_gb,
                raise_on_over=True,
            )
            print(f"[composition] disk post-TEST: {usage.message}", flush=True)
        except DiskBudgetError as exc:
            post_test_disk_violation = str(exc)
            print(
                f"[composition] post-TEST disk violation: {exc}",
                flush=True,
            )

    report = comp.summarize_report(results)
    payload = report.to_dict()
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
                "BLOCKED_POST_TEST_DISK_BUDGET_VIOLATION"
                if post_test_disk_violation
                else "PENDING_HOSTILE_RESULT_AUDIT"
            ),
            "post_test_disk_violation": post_test_disk_violation,
        }
    )
    result_path = out_dir / "composition_test_results.json"
    _atomic_json(result_path, payload)
    summary = {
        "data_hash": comp.canonical_hash(
            {axis: pools[axis].data_hash for axis in comp.AXES}
        ),
        "overall_verdict": report.overall_verdict,
        "selection_hash": selection["selection_hash"],
        "axis_verdicts": {row.axis: row.verdict for row in results},
    }
    exp_id = _register(
        out_dir=out_dir,
        prefix="e0017-composition-test",
        run_type="confirmatory",
        status="invalidated" if post_test_disk_violation else "done",
        cfg_hash=test_fingerprint,
        backend=args.backend,
        artifact=result_path,
        started_at=started_at,
        dirty_tree_at_start=dirty_tree_at_start,
        summary=summary,
        validation_notes=(
            (
                "Authorized TEST-once composition run was invalidated by the "
                f"post-run disk guard: {post_test_disk_violation}"
            )
            if post_test_disk_violation
            else (
                "Authorized TEST-once composition run. valid_for_paper remains "
                "false until independent hostile result/statistics/lineage audit."
            )
        ),
        exit_code=4 if post_test_disk_violation else None,
    )
    manifest = ArtifactManifest(
        artifact_id="e0017-prompt-steer-composition-results",
        supports_claims=["C2"],
        source_experiments=[exp_id],
        aggregation_script="scripts/run_prompt_steer_composition.py",
        aggregation_commit=git_commit(str(_REPO)),
        output_file=_rel(result_path),
        raw_data_hash=_sha256_file(result_path),
        manual_edits_allowed=False,
        last_verified=utcnow(),
        verdict="rejected" if post_test_disk_violation else "pending",
    )
    write_manifest(str(out_dir / "composition_results.manifest.yaml"), manifest)
    update_test_marker(marker, "completed")

    if post_test_disk_violation:
        return 4
    print(
        f"[composition] TEST complete: verdict={report.overall_verdict} "
        f"exp={exp_id}; valid_for_paper=false pending hostile audit",
        flush=True,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="E-0017 prompt-plus-steer composition (DEV-sealed, TEST-once)"
    )
    parser.add_argument("--phase", choices=["dev", "test"], required=True)
    parser.add_argument("--backend", choices=["synthetic", "hf"], default="synthetic")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--selection-json", default=None)
    parser.add_argument("--test-authorization-file", default=None)
    parser.add_argument("--bootstrap-b", type=int, default=comp.BOOTSTRAP_B)
    parser.add_argument("--fresh", action="store_true")
    parser.add_argument("--smoke-dev-n", type=int, default=4)
    parser.add_argument("--smoke-test-n", type=int, default=6)
    parser.add_argument("--stall-timeout", type=float, default=600.0)
    parser.add_argument("--disk-budget-gb", type=float, default=60.0)
    parser.add_argument("--disk-ceiling-gb", type=float, default=70.0)
    parser.add_argument("--hf-home", default=None)
    parser.add_argument("--venv", default=None)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.bootstrap_b < 1:
        raise SystemExit("--bootstrap-b must be >=1")
    if args.backend == "hf" and args.bootstrap_b < comp.BOOTSTRAP_B:
        raise SystemExit(
            f"real run requires --bootstrap-b >= {comp.BOOTSTRAP_B}"
        )
    if args.backend == "synthetic":
        if args.smoke_dev_n < 2 or args.smoke_test_n < 2:
            raise SystemExit("synthetic smoke requires DEV and TEST N>=2")
    if args.phase == "dev":
        return _run_dev(args)
    return _run_test(args)


if __name__ == "__main__":
    raise SystemExit(main())
