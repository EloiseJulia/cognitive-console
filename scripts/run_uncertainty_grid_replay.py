"""Exact, resumable replay orchestrator for the frozen uncertainty grid.

The default is a CPU-only protocol dry run. ``--execute`` is intentionally
explicit and must be used only after independent hostile audit approval.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cognitive_console.lineage import git_commit, utcnow
from scripts import reanalyse_uncertainty_grid as analysis
from scripts import run_uncertainty_format_recheck as runner
from scripts import run_arm_matrix as arm

GENERATED_ROOT = (
    _REPO / "results" / "E-0013-uncertainty-grid-recheck" / "generated"
).resolve()


def _write_json(path: Path, payload: Dict) -> None:
    runner._atomic_write_json(path, payload)


def _git_status_excluding_replay_outputs() -> List[str]:
    return runner._git_status_rows()


def _protected_snapshot(protocol: Dict) -> Dict[str, str]:
    paths: List[Path] = []
    legacy = dict(protocol["legacy_e0013"])
    for key in ("samples_path", "reanalysis_path", "run_manifest_path"):
        paths.append(analysis._resolve(legacy[key]))
    for cell_key in sorted(arm.FROZEN_CELL_KEYS):
        paths.append(
            analysis._resolve(protocol["cells"][cell_key]["frozen_result"]["path"])
        )
    snapshot: Dict[str, str] = {}
    for path in paths:
        if not path.is_file():
            raise analysis.RecheckError(f"protected artifact missing: {path}")
        snapshot[analysis._rel(path)] = analysis.sha256_file(path)
    return snapshot


def _assert_protected_unchanged(expected: Dict[str, str]) -> None:
    actual = {
        rel: analysis.sha256_file(analysis._resolve(rel)) for rel in sorted(expected)
    }
    if actual != expected:
        changed = [
            rel
            for rel in sorted(set(expected) | set(actual))
            if expected.get(rel) != actual.get(rel)
        ]
        raise analysis.RecheckError(
            "protected E-0013/E-0006 artifacts changed: " + ", ".join(changed)
        )


def _replay_target(cell_spec: Dict) -> Path:
    candidates = [
        source
        for source in cell_spec.get("sources", [])
        if source.get("kind") == "e0013_samples_v1"
        and source.get("origin") == "frozen_replay"
    ]
    if len(candidates) != 1:
        raise analysis.RecheckError(
            "each replay cell must have exactly one frozen_replay samples source"
        )
    target = analysis._resolve(candidates[0]["path"]).parent.resolve()
    if target.parent != GENERATED_ROOT:
        raise analysis.RecheckError(
            f"replay target must be a direct child of {GENERATED_ROOT}: {target}"
        )
    return target


def _build_cell_argv(
    *,
    protocol_path: Path,
    protocol: Dict,
    cell_key: str,
    out_dir: Path,
    qwen_model: Optional[str],
    llama_model: Optional[str],
    qwen_revision: Optional[str],
    llama_revision: Optional[str],
    expected_code_commit: str,
    authorization: str,
    scratch_dir: Path,
    hf_cache_dir: Optional[Path],
) -> List[str]:
    generation = dict(protocol["generation"])
    argv = [
        "--experiment-id",
        "E-0013-grid-recheck-" + cell_key.replace("__", "-").replace(".", "p"),
        "--backend",
        "hf",
        "--expected-code-commit",
        expected_code_commit,
        "--authorization",
        authorization,
        "--scratch-dir",
        str(scratch_dir),
        "--protocol-manifest",
        str(protocol_path),
        "--frozen-items",
        str(analysis._resolve(generation["item_artifact"]["path"])),
        "--frozen-root",
        str(analysis._resolve(generation["frozen_root"])),
        "--out-dir",
        str(out_dir),
        "--cells",
        cell_key,
        "--splits",
        "dev",
        "test",
        "--seed",
        str(generation["seed"]),
        "--n-extraction",
        str(generation["n_extraction"]),
        "--bootstrap-b",
        str(protocol["analysis"]["bootstrap_b"]),
        "--max-new-tokens",
        str(generation["max_new_tokens"]),
        "--temperature",
        str(generation["temperature"]),
        "--batch-size",
        str(generation["batch_size"]),
        "--raw-text-max-chars",
        str(generation["raw_text_max_chars"]),
        "--resume-incomplete",
    ]
    model_label = cell_key.split("__", 1)[1]
    if model_label == "qwen2.5-7b" and qwen_model:
        argv.extend(["--qwen-model", qwen_model])
    if model_label == "qwen2.5-7b" and qwen_revision:
        argv.extend(["--qwen-revision", qwen_revision])
    if model_label == "llama3-8b" and llama_model:
        argv.extend(["--llama-model", llama_model])
    if model_label == "llama3-8b" and llama_revision:
        argv.extend(["--llama-revision", llama_revision])
    if hf_cache_dir is not None:
        argv.extend(["--hf-cache-dir", str(hf_cache_dir)])
    return argv


def _planned_cells(protocol: Dict, requested: Optional[List[str]]) -> List[str]:
    if requested:
        cells = list(dict.fromkeys(requested))
    else:
        cells = [
            key
            for key, spec in sorted(protocol["cells"].items())
            if bool(spec.get("replay_required"))
        ]
    unknown = sorted(set(cells) - set(protocol["cells"]))
    if unknown:
        raise analysis.RecheckError(f"unknown cells: {unknown}")
    forbidden = [
        key for key in cells if not bool(protocol["cells"][key].get("replay_required"))
    ]
    if forbidden:
        raise analysis.RecheckError(
            "replay is forbidden for cells with immutable existing data: "
            + ", ".join(forbidden)
        )
    return cells


def _validate_recovered_source(
    protocol: Dict,
    *,
    cell_key: str,
    cfg: runner.FrozenCellConfig,
    frozen_payload: Dict,
    items_by_id: Dict[str, Dict],
    test_ids: Sequence[str],
) -> Optional[Dict]:
    recovered_policy = analysis._recovered_transcript_policy(protocol)
    candidates = [
        dict(source)
        for source in protocol["cells"][cell_key].get("sources", [])
        if source.get("kind") == "c2b_transcript_dir_v1"
    ]
    for candidate in candidates:
        path = analysis._resolve(candidate["path"])
        if not path.exists():
            continue
        if not path.is_dir():
            raise analysis.RecheckError(
                f"{cell_key}: recovered transcript candidate is present but "
                f"is not a directory: {path}"
            )
        registered_inventory = analysis._validate_registered_transcript_source(
            path,
            candidate=candidate,
            policy=recovered_policy,
            cell_key=cell_key,
        )
        if registered_inventory is None:
            continue
        records, source_meta = analysis._load_c2b_transcript_dir(
            path,
            cell_key=cell_key,
            cfg=cfg,
            frozen_payload=frozen_payload,
            items_by_id=items_by_id,
            test_ids=test_ids,
            generation=dict(protocol["generation"]),
        )
        coverage = analysis._validate_coverage(
            records,
            cell_key=cell_key,
            test_ids=test_ids,
            dev_ids=[],
            k=int(protocol["generation"]["k_samples"]),
        )
        return {
            "kind": candidate["kind"],
            "path": analysis._rel(path),
            "origin": candidate.get("origin"),
            "source_meta": source_meta,
            "registered_file_inventory": registered_inventory,
            "score_equivalence_establishes_provenance": False,
            "coverage": coverage,
            "gitignored_presence_was_validated": True,
        }
    return None


def _choose_replay_action(
    recovered: Optional[Dict], completion: Optional[Dict]
) -> str:
    if recovered is not None:
        return "USE_VALID_RECOVERED_SOURCE_SKIP_REPLAY"
    if completion is not None:
        return "VERIFY_AND_SKIP_COMPLETE"
    return "GENERATE_OR_RESUME"


def _assert_resumable_target(out_dir: Path) -> None:
    if not out_dir.exists():
        return
    allowed_files = {
        "samples.jsonl",
        "reanalysis.json",
        "run_manifest.json",
        "completion.json",
        "failure.json",
    }
    allowed_dirs = {"checkpoints", "failures"}
    for child in out_dir.iterdir():
        if child.is_dir() and (
            child.name in allowed_dirs or child.name.startswith("cell_")
        ):
            continue
        if child.is_file() and (
            child.name in allowed_files or child.name.endswith(".pending")
        ):
            continue
        raise analysis.RecheckError(
            f"unexpected file in isolated replay directory: {child}"
        )


def _validate_completion(
    out_dir: Path,
    *,
    protocol_path: Path,
    cell_key: str,
    expected_code_commit: str,
    authorization: str,
) -> Optional[Dict]:
    path = out_dir / "completion.json"
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("status") != "COMPLETE_PENDING_INDEPENDENT_RESULTS_AUDIT":
        raise analysis.RecheckError(f"{path}: invalid completion status")
    if payload.get("cell") != cell_key:
        raise analysis.RecheckError(f"{path}: completion cell mismatch")
    if payload.get("code_commit") != expected_code_commit:
        raise analysis.RecheckError(f"{path}: completion code commit mismatch")
    if payload.get("authorization_id") != authorization:
        raise analysis.RecheckError(f"{path}: completion authorization mismatch")
    if payload.get("protocol_manifest_sha256") != analysis.sha256_file(protocol_path):
        raise analysis.RecheckError(f"{path}: protocol hash mismatch")
    for key, filename in (
        ("samples_jsonl", "samples.jsonl"),
        ("reanalysis_json", "reanalysis.json"),
        ("run_manifest_json", "run_manifest.json"),
        ("test_complete_json", "checkpoints/test_complete.json"),
    ):
        artifact = dict(payload.get(key) or {})
        artifact_path = out_dir / filename
        if (
            not artifact_path.is_file()
            or artifact.get("path") != analysis._rel(artifact_path)
            or artifact.get("sha256") != analysis.sha256_file(artifact_path)
        ):
            raise analysis.RecheckError(f"{path}: invalid {key} identity")
    run_manifest = json.loads(
        (out_dir / "run_manifest.json").read_text(encoding="utf-8")
    )
    expected_experiment = (
        "E-0013-grid-recheck-" + cell_key.replace("__", "-").replace(".", "p")
    )
    if run_manifest.get("experiment_id") != expected_experiment:
        raise analysis.RecheckError(f"{path}: run experiment identity mismatch")
    if set(run_manifest.get("cells") or {}) != {cell_key}:
        raise analysis.RecheckError(f"{path}: run cell identity mismatch")
    protocol_identity = dict(run_manifest.get("protocol_manifest") or {})
    if protocol_identity.get("sha256") != analysis.sha256_file(protocol_path):
        raise analysis.RecheckError(f"{path}: run protocol identity mismatch")
    generation_identity = dict(run_manifest.get("generation_identity") or {})
    if generation_identity.get("test_use_policy") != runner.TEST_USE_POLICY:
        raise analysis.RecheckError(f"{path}: TEST-use policy mismatch")
    scope = dict(run_manifest.get("evidence_scope") or {})
    if scope.get("frozen_results_replaced") is not False:
        raise analysis.RecheckError(f"{path}: replay claims to replace frozen results")
    if scope.get("new_scorer_result_created") is not False:
        raise analysis.RecheckError(f"{path}: replay claims a new scorer result")
    if run_manifest.get("code_commit") != expected_code_commit:
        raise analysis.RecheckError(f"{path}: run code commit mismatch")
    if run_manifest.get("dirty_tree_at_start") is not False:
        raise analysis.RecheckError(f"{path}: run started from a dirty tree")
    execution_binding = dict(run_manifest.get("execution_binding") or {})
    if runner._canonical_hash(execution_binding) != run_manifest.get(
        "execution_identity_sha256"
    ):
        raise analysis.RecheckError(f"{path}: execution identity hash mismatch")
    if execution_binding.get("code_commit") != expected_code_commit:
        raise analysis.RecheckError(f"{path}: execution code identity mismatch")
    if dict(execution_binding.get("authorization") or {}).get("id") != authorization:
        raise analysis.RecheckError(f"{path}: execution authorization mismatch")
    manifest_identity = dict(execution_binding.get("protocol_manifest") or {})
    if manifest_identity.get("sha256") != analysis.sha256_file(protocol_path):
        raise analysis.RecheckError(f"{path}: execution manifest hash mismatch")
    if manifest_identity.get("git_blob_oid") != runner._git_blob_oid(
        protocol_path, expected_code_commit
    ):
        raise analysis.RecheckError(f"{path}: execution manifest blob mismatch")
    if payload.get("argv") != list(execution_binding.get("argv") or [])[2:]:
        raise analysis.RecheckError(f"{path}: completion argv mismatch")
    if payload.get("execution_identity_sha256") != run_manifest.get(
        "execution_identity_sha256"
    ):
        raise analysis.RecheckError(f"{path}: completion execution identity mismatch")
    return payload


def _cell_plan(
    protocol: Dict,
    *,
    cell_key: str,
    cfg: runner.FrozenCellConfig,
    split: Dict[str, List[Dict]],
) -> Dict:
    generation = dict(protocol["generation"])
    batch_size = int(generation["batch_size"])
    split_rows: Dict[str, Dict] = {}
    all_jobs: List[Dict] = []
    for split_name in ("dev", "test"):
        split_jobs: List[Dict] = []
        batches = 0
        for condition in runner.CONDITIONS:
            jobs, _, _, _ = runner._expected_batch_jobs(
                cfg=cfg,
                split_name=split_name,
                condition=condition,
                items=split[split_name],
                seed=int(generation["seed"]),
            )
            split_jobs.extend(jobs)
            batches += math.ceil(len(jobs) / batch_size)
        all_jobs.extend(split_jobs)
        split_rows[split_name] = {
            "items": len(split[split_name]),
            "generations": len(split_jobs),
            "batches": batches,
            "job_plan_sha256": runner._canonical_hash(split_jobs),
        }
    return {
        "cell": cell_key,
        "method": cfg.method,
        "model_label": cfg.model_label,
        "legacy_model_label_key": runner._legacy_model_label_key(cfg.model_id),
        "selected_prompt_id": cfg.best_prompt_id,
        "selected_prompt_sha256": runner._sha256_text(cfg.best_prompt_text),
        "neutral_prompt_sha256": runner._sha256_text(cfg.neutral_prompt),
        "layer": cfg.layer,
        "requested_alpha": cfg.frozen_alpha,
        "sigma": cfg.sigma,
        "effective_steer_alpha": (
            runner.sigma_scaled_alpha(cfg.frozen_alpha, cfg.sigma)
            if cfg.method == "iti"
            else cfg.frozen_alpha
        ),
        "source_result": cfg.source_result_file,
        "source_config_fingerprint": cfg.source_config_fingerprint,
        "splits": split_rows,
        "total_generations": len(all_jobs),
        "total_batches": sum(row["batches"] for row in split_rows.values()),
        "all_job_plan_sha256": runner._canonical_hash(all_jobs),
        "test_use_policy": runner.TEST_USE_POLICY,
    }


def _compute_estimate(plans: Sequence[Dict]) -> Dict:
    generations = sum(int(plan["total_generations"]) for plan in plans)
    batches = sum(int(plan["total_batches"]) for plan in plans)
    cells = len(plans)
    generation_lo = batches * 2.0 / 3600.0
    generation_hi = batches * 4.0 / 3600.0
    total_lo = generation_lo + cells * 0.05
    total_hi = generation_hi + cells * 0.15
    return {
        "cells_to_generate": cells,
        "generations": generations,
        "fixed_composition_batches": batches,
        "generation_only_a800_hours_at_2_to_4_seconds_per_batch": [
            round(generation_lo, 2),
            round(generation_hi, 2),
        ],
        "estimated_total_a800_gpu_hours_including_model_load_and_direction_derivation": [
            round(total_lo, 1),
            round(total_hi, 1),
        ],
        "estimate_note": (
            "Sequential single-GPU estimate; excludes queue/download time and "
            "assumes model weights are already local."
        ),
    }


def _write_failure(
    out_dir: Path,
    *,
    cell_key: str,
    protocol_path: Path,
    exc: BaseException,
    protected_before: Dict[str, str],
    authorization: Optional[str] = None,
    argv: Optional[Sequence[str]] = None,
    environment: Optional[Dict[str, object]] = None,
) -> None:
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%S.%fZ")
    payload = {
        "cell": cell_key,
        "failed_at": now.isoformat(),
        "code_commit": git_commit(str(_REPO)),
        "protocol_manifest_sha256": analysis.sha256_file(protocol_path),
        "authorization_id": authorization,
        "argv": list(argv) if argv is not None else None,
        "environment": environment,
        "error_type": type(exc).__name__,
        "error": str(exc),
        "status": "FAILED_NOT_AN_ANALYSIS_SOURCE",
        "test_recovery_rule": (
            "Re-run the identical command. Identity-matching completed checkpoint "
            "batches are reused; a sealed TEST is never regenerated."
        ),
        "preservation_rule": (
            "Failure history and checkpoints are retained for audit; original "
            "E-0013 and frozen E-0006 artifacts remain protected."
        ),
        "protected_before": protected_before,
        "protected_after": {
            rel: analysis.sha256_file(analysis._resolve(rel))
            for rel in sorted(protected_before)
        },
    }
    history_path = out_dir / "failures" / f"failure-{stamp}.json"
    _write_json(history_path, payload)
    latest = {**payload, "history_path": analysis._rel(history_path)}
    _write_json(out_dir / "failure.json", latest)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare or execute exact frozen uncertainty-cell replay"
    )
    parser.add_argument("--manifest", default=str(analysis.DEFAULT_MANIFEST))
    parser.add_argument("--cells", nargs="*", default=None)
    parser.add_argument("--qwen-model", default=None)
    parser.add_argument("--llama-model", default=None)
    parser.add_argument("--qwen-revision", default=None)
    parser.add_argument("--llama-revision", default=None)
    parser.add_argument("--expected-code-commit", default=None)
    parser.add_argument("--authorization", default=None)
    parser.add_argument("--scratch-root", default=None)
    parser.add_argument("--hf-cache-dir", default=None)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="perform real HF generation; omit for the default CPU-only dry run",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    raw_argv = list(argv) if argv is not None else list(sys.argv[1:])
    args = build_parser().parse_args(raw_argv)
    protocol_path = analysis._resolve(args.manifest)
    protocol_header = analysis._read_json(protocol_path)
    execution = runner._execution_policy(protocol_header)
    authorization = args.authorization or str(execution["authorization_id"])
    current_commit = git_commit(str(_REPO))
    expected_code_commit = args.expected_code_commit or current_commit
    qwen_model = args.qwen_model or str(
        execution["model_identity"]["qwen2.5-7b"]["hf_repo_id"]
    )
    llama_model = args.llama_model or str(
        execution["model_identity"]["llama3-8b"]["hf_repo_id"]
    )
    qwen_is_local = runner._looks_like_local_path(qwen_model) or Path(
        qwen_model
    ).expanduser().exists()
    llama_is_local = runner._looks_like_local_path(llama_model) or Path(
        llama_model
    ).expanduser().exists()
    qwen_revision = (
        args.qwen_revision
        if qwen_is_local
        else args.qwen_revision
        or str(execution["model_identity"]["qwen2.5-7b"]["revision"])
    )
    llama_revision = (
        args.llama_revision
        if llama_is_local
        else args.llama_revision
        or str(execution["model_identity"]["llama3-8b"]["revision"])
    )
    scratch_root = Path(
        args.scratch_root
        or (_REPO.parent / "cognitive-console-e0013-replay-scratch")
    ).expanduser().resolve()
    hf_cache_dir = Path(
        args.hf_cache_dir
        or (_REPO.parent / "cognitive-console-e0013-hf-cache")
    ).expanduser().resolve()
    if args.execute:
        if not args.expected_code_commit:
            raise analysis.RecheckError(
                "--expected-code-commit is mandatory for GPU execution"
            )
        if not args.authorization:
            raise analysis.RecheckError("--authorization is mandatory for GPU execution")
        if not args.scratch_root:
            raise analysis.RecheckError("--scratch-root is mandatory for GPU execution")
        if not args.hf_cache_dir and (
            not runner._looks_like_local_path(qwen_model)
            or not runner._looks_like_local_path(llama_model)
        ):
            raise analysis.RecheckError(
                "--hf-cache-dir is mandatory when using pinned HF repo ids"
            )
        if authorization != execution["authorization_id"]:
            raise analysis.RecheckError(
                "execution authorization does not match the frozen protocol"
            )
        if expected_code_commit != current_commit:
            raise analysis.RecheckError(
                f"HEAD {current_commit} != expected audited commit "
                f"{expected_code_commit}"
            )
        dirty = _git_status_excluding_replay_outputs()
        if dirty:
            raise analysis.RecheckError(
                "GPU replay requires a clean audited tree: " + "; ".join(dirty)
            )
        runner._git_blob_oid(protocol_path, current_commit)
        scratch_root = runner._require_external_directory(
            scratch_root, "--scratch-root"
        )
        hf_cache_dir = runner._require_external_directory(
            hf_cache_dir, "--hf-cache-dir"
        )
    protocol = analysis.load_protocol(protocol_path)
    frozen_root = analysis._resolve(protocol["generation"]["frozen_root"])
    protected_before = _protected_snapshot(protocol)
    items, split, item_identity = analysis.load_frozen_items(protocol)
    items_by_id = {str(item["id"]): item for item in items}
    test_ids = [str(item["id"]) for item in split["test"]]

    frozen_bindings: Dict[str, Dict] = {}
    frozen_payloads: Dict[str, Dict] = {}
    frozen_configs: Dict[str, runner.FrozenCellConfig] = {}
    for cell_key in sorted(arm.FROZEN_CELL_KEYS):
        cfg, frozen_payload, frozen_identity = analysis.validate_cell_manifest(
            cell_key, protocol["cells"][cell_key], frozen_root
        )
        frozen_configs[cell_key] = cfg
        frozen_payloads[cell_key] = frozen_payload
        binding = _cell_plan(protocol, cell_key=cell_key, cfg=cfg, split=split)
        binding["frozen_result_sha256"] = frozen_identity["sha256"]
        binding["replay_required"] = bool(
            protocol["cells"][cell_key].get("replay_required")
        )
        frozen_bindings[cell_key] = binding

    cells = _planned_cells(protocol, args.cells)
    plan: List[Dict] = []
    for cell_key in cells:
        out_dir = _replay_target(protocol["cells"][cell_key])
        scratch_dir = scratch_root / f"cell_{cell_key}"
        cell_argv = _build_cell_argv(
            protocol_path=protocol_path,
            protocol=protocol,
            cell_key=cell_key,
            out_dir=out_dir,
            qwen_model=qwen_model,
            llama_model=llama_model,
            qwen_revision=qwen_revision,
            llama_revision=llama_revision,
            expected_code_commit=expected_code_commit,
            authorization=authorization,
            scratch_dir=scratch_dir,
            hf_cache_dir=hf_cache_dir,
        )
        try:
            recovered = _validate_recovered_source(
                protocol,
                cell_key=cell_key,
                cfg=frozen_configs[cell_key],
                frozen_payload=frozen_payloads[cell_key],
                items_by_id=items_by_id,
                test_ids=test_ids,
            )
            if recovered is not None:
                completion = None
            else:
                completion = _validate_completion(
                    out_dir,
                    protocol_path=protocol_path,
                    cell_key=cell_key,
                    expected_code_commit=expected_code_commit,
                    authorization=authorization,
                )
            action = _choose_replay_action(recovered, completion)
            plan.append(
                {
                    **frozen_bindings[cell_key],
                    "out_dir": analysis._rel(out_dir),
                    "scratch_dir": str(scratch_dir),
                    "action": action,
                    "recovered_source": recovered,
                    "argv": cell_argv,
                }
            )
        except BaseException as exc:
            if args.execute:
                _write_failure(
                    out_dir,
                    cell_key=cell_key,
                    protocol_path=protocol_path,
                    exc=exc,
                    protected_before=protected_before,
                    authorization=authorization,
                    argv=cell_argv,
                )
            raise

    command = [
        "python",
        "scripts/run_uncertainty_grid_replay.py",
        "--execute",
        "--manifest",
        str(protocol_path),
        "--expected-code-commit",
        expected_code_commit,
        "--authorization",
        authorization,
        "--scratch-root",
        str(scratch_root),
        "--hf-cache-dir",
        str(hf_cache_dir),
        "--qwen-model",
        qwen_model,
        "--llama-model",
        llama_model,
    ]
    if qwen_revision:
        command.extend(["--qwen-revision", qwen_revision])
    if llama_revision:
        command.extend(["--llama-revision", llama_revision])
    executable_plans = [
        row for row in plan if row["action"] == "GENERATE_OR_RESUME"
    ]
    if not args.execute:
        print(
            json.dumps(
                {
                    "mode": "CPU_ONLY_DRY_RUN_NO_GENERATION",
                    "protocol_manifest": {
                        "path": analysis._rel(protocol_path),
                        "sha256": analysis.sha256_file(protocol_path),
                    },
                    "item_identity": item_identity,
                    "protected_artifacts": protected_before,
                    "all_four_frozen_cell_bindings": frozen_bindings,
                    "replay_plan": plan,
                    "compute_estimate": _compute_estimate(executable_plans),
                    "exact_gpu_command_after_hostile_audit": subprocess.list2cmdline(
                        command
                    ),
                    "gpu_block": (
                        "Do not pass --execute until an independent hostile audit "
                        "approves this committed branch."
                    ),
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0

    for cell in plan:
        cell_key = str(cell["cell"])
        out_dir = analysis._resolve(cell["out_dir"])
        scratch_dir = Path(str(cell["scratch_dir"])).resolve()
        cell_environment: Optional[Dict[str, object]] = None
        try:
            _assert_resumable_target(out_dir)
            _assert_protected_unchanged(protected_before)
            if cell["action"] in {
                "VERIFY_AND_SKIP_COMPLETE",
                "USE_VALID_RECOVERED_SOURCE_SKIP_REPLAY",
            }:
                continue
            activation_cache_dir = scratch_dir / "activations" / "cache"
            cell_environment = runner._assert_resource_guards(
                dict(execution["resource_guards"]),
                out_dir=out_dir,
                scratch_dir=scratch_dir,
                activation_cache_dir=activation_cache_dir,
                hf_cache_dir=hf_cache_dir,
                stage=f"orchestrator_before_cell:{cell_key}",
            )
            rc = runner.main(list(cell["argv"]))
            if rc != 0:
                raise RuntimeError(f"cell runner returned exit code {rc}")
            artifacts = {
                "samples_jsonl": out_dir / "samples.jsonl",
                "reanalysis_json": out_dir / "reanalysis.json",
                "run_manifest_json": out_dir / "run_manifest.json",
                "test_complete_json": out_dir / "checkpoints" / "test_complete.json",
            }
            for label, path in artifacts.items():
                if not path.is_file():
                    raise RuntimeError(f"missing completed {label}: {path}")
            _assert_protected_unchanged(protected_before)
            environment_after = runner._assert_resource_guards(
                dict(execution["resource_guards"]),
                out_dir=out_dir,
                scratch_dir=scratch_dir,
                activation_cache_dir=activation_cache_dir,
                hf_cache_dir=hf_cache_dir,
                stage=f"orchestrator_after_cell:{cell_key}",
            )
            run_manifest = json.loads(
                (out_dir / "run_manifest.json").read_text(encoding="utf-8")
            )
            completion = {
                "cell": cell_key,
                "completed_at": utcnow(),
                "code_commit": current_commit,
                "authorization_id": authorization,
                "argv": list(cell["argv"]),
                "execution_identity_sha256": run_manifest[
                    "execution_identity_sha256"
                ],
                "dirty_code_or_protocol_tree_at_start": False,
                "protocol_manifest_sha256": analysis.sha256_file(protocol_path),
                "protected_artifacts": protected_before,
                "evidence_scope": (
                    "format presence/missingness and pre-specified sensitivity "
                    "only; no frozen scorer replacement"
                ),
                "test_use_policy": runner.TEST_USE_POLICY,
                "environment_before_cell": cell_environment,
                "environment_after_cell": environment_after,
                "status": "COMPLETE_PENDING_INDEPENDENT_RESULTS_AUDIT",
            }
            for label, path in artifacts.items():
                completion[label] = {
                    "path": analysis._rel(path),
                    "sha256": analysis.sha256_file(path),
                }
            _write_json(out_dir / "completion.json", completion)
            _validate_completion(
                out_dir,
                protocol_path=protocol_path,
                cell_key=cell_key,
                expected_code_commit=current_commit,
                authorization=authorization,
            )
            analysis.main(
                [
                    "--manifest",
                    str(protocol_path),
                    "--out-dir",
                    str(analysis.DEFAULT_OUT_DIR),
                    "--allow-incomplete",
                ]
            )
        except BaseException as exc:
            _write_failure(
                out_dir,
                cell_key=cell_key,
                protocol_path=protocol_path,
                exc=exc,
                protected_before=protected_before,
                authorization=authorization,
                argv=cell["argv"],
                environment=cell_environment,
            )
            _assert_protected_unchanged(protected_before)
            raise

    analysis.main(
        [
            "--manifest",
            str(protocol_path),
            "--out-dir",
            str(analysis.DEFAULT_OUT_DIR),
        ]
    )
    _assert_protected_unchanged(protected_before)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
