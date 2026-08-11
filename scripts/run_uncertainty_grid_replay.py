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
    ignored_prefix = "results/E-0013-uncertainty-grid-recheck/"
    rows: List[str] = []
    for line in proc.stdout.splitlines():
        path = line[3:].replace("\\", "/")
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if not path.startswith(ignored_prefix):
            rows.append(line)
    return rows


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
) -> List[str]:
    generation = dict(protocol["generation"])
    argv = [
        "--experiment-id",
        "E-0013-grid-recheck-" + cell_key.replace("__", "-").replace(".", "p"),
        "--backend",
        "hf",
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
    if model_label == "llama3-8b" and llama_model:
        argv.extend(["--llama-model", llama_model])
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
    out_dir: Path, *, protocol_path: Path, cell_key: str
) -> Optional[Dict]:
    path = out_dir / "completion.json"
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("status") != "COMPLETE_PENDING_INDEPENDENT_RESULTS_AUDIT":
        raise analysis.RecheckError(f"{path}: invalid completion status")
    if payload.get("cell") != cell_key:
        raise analysis.RecheckError(f"{path}: completion cell mismatch")
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
        "model_identity_key": runner._model_identity_key(cfg.model_id),
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
) -> None:
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%S.%fZ")
    payload = {
        "cell": cell_key,
        "failed_at": now.isoformat(),
        "code_commit": git_commit(str(_REPO)),
        "protocol_manifest_sha256": analysis.sha256_file(protocol_path),
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
    parser.add_argument("--expected-code-commit", default=None)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="perform real HF generation; omit for the default CPU-only dry run",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    protocol_path = analysis._resolve(args.manifest)
    protocol = analysis.load_protocol(protocol_path)
    _, split, item_identity = analysis.load_frozen_items(protocol)
    frozen_root = analysis._resolve(protocol["generation"]["frozen_root"])
    protected_before = _protected_snapshot(protocol)

    frozen_bindings: Dict[str, Dict] = {}
    for cell_key in sorted(arm.FROZEN_CELL_KEYS):
        cfg, _, frozen_identity = analysis.validate_cell_manifest(
            cell_key, protocol["cells"][cell_key], frozen_root
        )
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
        completion = _validate_completion(
            out_dir, protocol_path=protocol_path, cell_key=cell_key
        )
        cell_argv = _build_cell_argv(
            protocol_path=protocol_path,
            protocol=protocol,
            cell_key=cell_key,
            out_dir=out_dir,
            qwen_model=args.qwen_model,
            llama_model=args.llama_model,
        )
        plan.append(
            {
                **frozen_bindings[cell_key],
                "out_dir": analysis._rel(out_dir),
                "action": "VERIFY_AND_SKIP_COMPLETE" if completion else "GENERATE_OR_RESUME",
                "argv": cell_argv,
            }
        )

    current_commit = git_commit(str(_REPO))
    command = [
        "python",
        "scripts/run_uncertainty_grid_replay.py",
        "--execute",
        "--expected-code-commit",
        current_commit,
        "--qwen-model",
        args.qwen_model or "Qwen/Qwen2.5-7B-Instruct",
        "--llama-model",
        args.llama_model or "meta-llama/Meta-Llama-3-8B-Instruct",
    ]
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

    if not args.expected_code_commit:
        raise analysis.RecheckError(
            "--expected-code-commit is mandatory for GPU execution"
        )
    if args.expected_code_commit != current_commit:
        raise analysis.RecheckError(
            f"HEAD {current_commit} != expected audited commit "
            f"{args.expected_code_commit}"
        )
    dirty = _git_status_excluding_replay_outputs()
    if dirty:
        raise analysis.RecheckError(
            "GPU replay requires a clean audited code/protocol tree: "
            + "; ".join(dirty)
        )

    for cell in plan:
        cell_key = str(cell["cell"])
        out_dir = analysis._resolve(cell["out_dir"])
        _assert_resumable_target(out_dir)
        if cell["action"] == "VERIFY_AND_SKIP_COMPLETE":
            _assert_protected_unchanged(protected_before)
            continue
        try:
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
            completion = {
                "cell": cell_key,
                "completed_at": utcnow(),
                "code_commit": current_commit,
                "dirty_code_or_protocol_tree_at_start": False,
                "protocol_manifest_sha256": analysis.sha256_file(protocol_path),
                "protected_artifacts": protected_before,
                "evidence_scope": (
                    "format presence/missingness and pre-specified sensitivity "
                    "only; no frozen scorer replacement"
                ),
                "test_use_policy": runner.TEST_USE_POLICY,
                "status": "COMPLETE_PENDING_INDEPENDENT_RESULTS_AUDIT",
            }
            for label, path in artifacts.items():
                completion[label] = {
                    "path": analysis._rel(path),
                    "sha256": analysis.sha256_file(path),
                }
            _write_json(out_dir / "completion.json", completion)
            _validate_completion(
                out_dir, protocol_path=protocol_path, cell_key=cell_key
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
