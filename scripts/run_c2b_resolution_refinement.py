"""Staged runner for the frozen C2b resolution-refinement preregistration."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cognitive_console.eval import c2b_tasks
from cognitive_console.experiments import adjudicate_c2b as adj
from cognitive_console.experiments import resolution_refinement as rr
from cognitive_console.ops.disk_guard import check_disk_budget, default_guard_paths
from cognitive_console.ops.hardware_profiles import (
    get_authorized_hardware_profile,
    validate_hardware_profile,
)
from cognitive_console.steering.generate import SteeredHFBackend
from scripts import run_c1_facade as c1
from scripts import run_c2b_adjudication as base
from scripts import run_gpu_phase0 as p0

PREREG_PATH = "docs/specs/resolution-refinement-prereg.md"
MAX_NEW_TOKENS = 64
TEMPERATURE = 0.7
N_EXTRACTION = 28
N_STRONG = 16


def _sha256_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _atomic_json(path: Path, payload: Dict) -> None:
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
    dirty = bool(
        subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=_REPO,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    )
    if expected_commit and actual != expected_commit:
        raise ValueError(
            f"code commit mismatch: expected={expected_commit}, actual={actual}"
        )
    if require_clean and dirty:
        raise ValueError("HF resolution run requires a clean committed source tree")
    return {"code_commit": actual, "dirty_tree": dirty}


def _assert_external_output(out_dir: Path) -> None:
    try:
        out_dir.resolve().relative_to(_REPO.resolve())
    except ValueError:
        return
    raise ValueError("HF output directory must be outside the source repository")


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


def _load_resolution_items(backend: str) -> Dict[str, List[Dict]]:
    if backend == "synthetic":
        skepticism = [
            {
                "id": f"truthfulqa-mc1-{i:05d}",
                "prompt": f"Synthetic skepticism question {i}?",
                "choices": {"A": "reject", "B": "accept"},
                "answer_letter": "A",
            }
            for i in range(rr.TRUTHFULQA_VALIDATION_SIZE)
        ]
        uncertainty = [
            {
                "id": f"triviaqa-{i:05d}",
                "prompt": f"Synthetic uncertainty question {i}?",
                "answer": "answer",
                "aliases": ["answer"],
            }
            for i in range(2_000)
        ]
    else:
        skepticism = c2b_tasks.load_skepticism_set(
            n=None,
            seed=0,
            revision=c2b_tasks.TRUTHFULQA_REVISION,
        )
        uncertainty = c2b_tasks.load_uncertainty_set(
            n=None,
            seed=0,
            revision=c2b_tasks.TRIVIAQA_REVISION,
        )
    all_items = {
        "skepticism": skepticism,
        "uncertainty_awareness": uncertainty,
    }
    selected: Dict[str, List[Dict]] = {}
    for axis, total in rr.selected_total_n_by_axis().items():
        selected[axis] = rr.select_disjoint_items(
            all_items[axis],
            excluded_ids=rr.frozen_excluded_ids(axis),
            n_total=total,
            seed=rr.SEED,
        )
    return selected


def _split_items(spec: adj.AxisAdjSpec):
    ids = [str(item["id"]) for item in spec.items]
    by_id = {str(item["id"]): item for item in spec.items}
    split = adj.split_dev_test(ids, seed=rr.SEED)
    return (
        [by_id[item_id] for item_id in split.dev_ids],
        [by_id[item_id] for item_id in split.test_ids],
    )


def _build_hf_specs(items_by_axis: Dict[str, List[Dict]], out_dir: Path):
    return base.build_specs_hf(
        list(rr.AXES),
        rr.MODEL_ID,
        False,
        None,
        N_STRONG,
        N_EXTRACTION,
        rr.SEED,
        out_dir,
        rr.METHOD,
        items_by_axis=items_by_axis,
        model_revision=rr.MODEL_REVISION,
    )


def _sampler(hf_meta: Dict, out_dir: Path):
    collector = base.TranscriptCollector(
        out_dir, rr.MODEL_ID, rr.METHOD, "hf"
    )
    factory = base.hf_sampler_factory(
        rr.MODEL_ID,
        MAX_NEW_TOKENS,
        TEMPERATURE,
        rr.SEED,
        get_authorized_hardware_profile(
            "nvidia-a800-80gb"
        ).generation_batch_size,
        collector,
        hf_meta.get("alpha_scale_by_axis"),
        model_revision=rr.MODEL_REVISION,
    )
    factory.backend._ensure_loaded()
    _capture_hardware("nvidia-a800-80gb", after_load=True)
    return factory, collector


def _preflight(args) -> int:
    out_dir = Path(args.out_dir).resolve()
    identity = _git_identity(args.expected_code_commit, args.backend == "hf")
    items = _load_resolution_items(args.backend)
    payload = {
        "protocol_id": rr.PROTOCOL_ID,
        "phase": "PREFLIGHT",
        "scientific_status": "OPERATIONAL_ONLY_NOT_DEV_OR_TEST",
        "code_identity": identity,
        "power": rr.power_manifest(),
        "sampling": rr.sampling_manifest(items),
        "dataset_revisions": {
            "truthfulqa/truthful_qa": c2b_tasks.TRUTHFULQA_REVISION,
            "mandarjoshi/trivia_qa": c2b_tasks.TRIVIAQA_REVISION,
        },
        "model": rr.MODEL_ID,
        "model_revision": rr.MODEL_REVISION,
        "platform": platform.platform(),
    }
    if args.backend == "hf":
        _assert_external_output(out_dir)
        hardware = _capture_hardware(args.hardware_profile)
        profile = get_authorized_hardware_profile(args.hardware_profile)
        disk = check_disk_budget(
            default_guard_paths(args.hf_home, args.venv),
            profile.disk_budget_gib,
            profile.disk_ceiling_gib,
        )
        backend = SteeredHFBackend(
            rr.MODEL_ID,
            device=p0._pick_device(),
            dtype=p0._pick_dtype(),
            seed=rr.SEED,
            model_revision=rr.MODEL_REVISION,
        )
        probe = backend.generate("Reply with OK.", max_new_tokens=1)
        payload["hardware_pre_load"] = hardware
        payload["hardware_post_load"] = _capture_hardware(
            args.hardware_profile, after_load=True
        )
        payload["disk"] = disk.to_dict()
        payload["one_token_probe_nonempty"] = bool(str(probe).strip())
    _atomic_json(out_dir / "preflight" / "preflight.json", payload)
    rows = payload["sampling"]["axes"]
    print(
        "[resolution] preflight: "
        f"skepticism DEV/TEST={rows['skepticism']['n_dev']}/"
        f"{rows['skepticism']['n_test']}; uncertainty DEV/TEST="
        f"{rows['uncertainty_awareness']['n_dev']}/"
        f"{rows['uncertainty_awareness']['n_test']}",
        flush=True,
    )
    return 0


def _dev(args) -> int:
    out_dir = Path(args.out_dir).resolve()
    _assert_external_output(out_dir)
    identity = _git_identity(args.expected_code_commit, True)
    if (out_dir / "dev" / "SEALED.json").exists():
        raise ValueError("DEV is already sealed; do not overwrite it")
    hardware = _capture_hardware(args.hardware_profile)
    items = _load_resolution_items("hf")
    specs, hf_meta = _build_hf_specs(items, out_dir / "dev" / "work")
    sampler_for_axis, collector = _sampler(hf_meta, out_dir / "dev" / "work")
    selections: Dict[str, object] = {}
    direction_files: Dict[str, object] = {}
    for spec in specs:
        dev_items, _ = _split_items(spec)
        checkpoint = base.TranscriptCheckpointStore(
            out_dir / "dev" / "work" / "checkpoints" / spec.axis,
            f"{rr.PROTOCOL_ID}-dev-{spec.axis}",
            seed=rr.SEED,
            fresh=False,
            collector=collector,
        )
        ctx = adj.RunContext(checkpoint=checkpoint)
        try:
            selection = adj.select_on_dev(
                sampler_for_axis(spec.axis),
                spec,
                dev_items,
                k=adj.K_SAMPLES,
                alpha_grid=adj.ALPHA_GRID,
                coherence_max_ratio=adj.COHERENCE_MAX_RATIO,
                ctx=ctx,
            )
        finally:
            checkpoint.close()
        direction_path = out_dir / "dev" / "sealed" / f"{spec.axis}-direction.npy"
        direction_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(direction_path, np.asarray(spec.direction))
        selections[spec.axis] = {
            "selection": asdict(selection),
            "layer": int(spec.layer),
            "dev_item_ids": [str(item["id"]) for item in dev_items],
        }
        direction_files[spec.axis] = {
            "path": str(direction_path),
            "sha256": _sha256_file(direction_path),
        }
    collector.write_raw(out_dir / "dev" / "work" / "transcripts")
    selection_payload = {
        "protocol_id": rr.PROTOCOL_ID,
        "experiment_id": rr.DEV_EXPERIMENT_ID,
        "phase": "DEV",
        "code_identity": identity,
        "hardware": hardware,
        "hardware_profile_sha256": get_authorized_hardware_profile(
            args.hardware_profile
        ).profile_sha256,
        "sampling": rr.sampling_manifest(items),
        "selections": selections,
        "directions": direction_files,
        "hf_meta": hf_meta,
    }
    selection_path = out_dir / "dev" / "sealed" / "dev_selection.json"
    _atomic_json(selection_path, selection_payload)
    _atomic_json(
        out_dir / "dev" / "SEALED.json",
        {"dev_selection_sha256": _sha256_file(selection_path)},
    )
    return 0


def _test(args) -> int:
    out_dir = Path(args.out_dir).resolve()
    _assert_external_output(out_dir)
    identity = _git_identity(args.expected_code_commit, True)
    seal_path = out_dir / "dev" / "SEALED.json"
    selection_path = out_dir / "dev" / "sealed" / "dev_selection.json"
    if not seal_path.exists() or not selection_path.exists():
        raise ValueError("TEST requires a sealed DEV selection")
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    if seal["dev_selection_sha256"] != _sha256_file(selection_path):
        raise ValueError("sealed DEV selection hash mismatch")
    started = out_dir / "test" / "TEST_STARTED.json"
    if started.exists():
        raise ValueError("TEST-once guard: this output directory already started TEST")
    frozen = json.loads(selection_path.read_text(encoding="utf-8"))
    if frozen["code_identity"] != identity:
        raise ValueError("TEST code identity differs from sealed DEV")
    hardware = _capture_hardware(args.hardware_profile)
    if frozen["hardware_profile_sha256"] != get_authorized_hardware_profile(
        args.hardware_profile
    ).profile_sha256:
        raise ValueError("TEST hardware profile differs from sealed DEV")
    items = _load_resolution_items("hf")
    if rr.sampling_manifest(items) != frozen["sampling"]:
        raise ValueError("TEST sampling identity differs from sealed DEV")
    neutral = c1.load_neutral_prompts()[0]
    specs: List[adj.AxisAdjSpec] = []
    for axis in rr.AXES:
        direction_path = Path(frozen["directions"][axis]["path"])
        if _sha256_file(direction_path) != frozen["directions"][axis]["sha256"]:
            raise ValueError(f"sealed direction hash mismatch for {axis}")
        specs.append(
            adj.AxisAdjSpec(
                axis=axis,
                items=items[axis],
                strong_prompts=base.build_strong_prompts(axis, N_STRONG),
                neutral_prompt=neutral,
                direction=np.load(direction_path),
                layer=int(frozen["selections"][axis]["layer"]),
            )
        )
    sampler_for_axis, collector = _sampler(
        frozen["hf_meta"], out_dir / "test" / "work"
    )
    _atomic_json(
        started,
        {
            "protocol_id": rr.PROTOCOL_ID,
            "experiment_id": rr.TEST_EXPERIMENT_ID,
            "code_identity": identity,
            "meaning": "TEST generation is now authorized to begin exactly once",
        },
    )
    axis_results = []
    for spec in specs:
        dev_items, test_items = _split_items(spec)
        expected_dev = frozen["selections"][spec.axis]["dev_item_ids"]
        if [str(item["id"]) for item in dev_items] != expected_dev:
            raise ValueError(f"DEV item identity drift for {spec.axis}")
        checkpoint = base.TranscriptCheckpointStore(
            out_dir / "test" / "work" / "checkpoints" / spec.axis,
            f"{rr.PROTOCOL_ID}-test-{spec.axis}",
            seed=rr.SEED,
            fresh=True,
            collector=collector,
        )
        ctx = adj.RunContext(checkpoint=checkpoint)
        try:
            result = adj.adjudicate_axis_test(
                sampler_for_axis(spec.axis),
                spec,
                dev_items=dev_items,
                test_items=test_items,
                dev_selection=frozen["selections"][spec.axis]["selection"],
                k=adj.K_SAMPLES,
                bootstrap_b=adj.BOOTSTRAP_B,
                ci_level=adj.BONFERRONI_CI_LEVEL,
                delta=adj.DELTA,
                coherence_max_ratio=adj.COHERENCE_MAX_RATIO,
                seed=rr.SEED,
                ctx=ctx,
            )
        finally:
            checkpoint.close()
        axis_results.append(result)
    report = adj.AdjudicationReport(
        axis_results=axis_results,
        axis_passes={result.axis: bool(result.passed) for result in axis_results},
        verdict="RESOLUTION_REFINEMENT_ADDITIVE_NO_GRID_REPLACEMENT",
        frozen_params=adj.frozen_params_dict(),
    )
    payload = {
        "protocol_id": rr.PROTOCOL_ID,
        "experiment_id": rr.TEST_EXPERIMENT_ID,
        "phase": "TEST",
        "scientific_status": "PENDING_HOSTILE_RESULT_AUDIT",
        "additive_to_frozen_0_of_12": True,
        "must_not_overwrite": "E-0005/E-0006/E-0011 frozen artifacts and verdicts",
        "code_identity": identity,
        "hardware": hardware,
        "power": rr.power_manifest(),
        "sampling": frozen["sampling"],
        "frozen_params": adj.frozen_params_dict(),
        "max_new_tokens": MAX_NEW_TOKENS,
        "temperature": TEMPERATURE,
        "batch_size": get_authorized_hardware_profile(
            args.hardware_profile
        ).generation_batch_size,
        "axes": [result.to_row() for result in axis_results],
        "valid_for_paper": False,
    }
    result_path = out_dir / "test" / "sealed" / "resolution_refinement_results.json"
    _atomic_json(result_path, payload)
    collector.write_all(out_dir / "test" / "work", report)
    _atomic_json(
        out_dir / "test" / "SEALED.json",
        {"results_sha256": _sha256_file(result_path)},
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=["preflight", "dev", "test"], required=True)
    parser.add_argument("--backend", choices=["synthetic", "hf"], default="hf")
    parser.add_argument("--hardware-profile", default="nvidia-a800-80gb")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--expected-code-commit")
    parser.add_argument("--hf-home")
    parser.add_argument("--venv")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.backend == "synthetic" and args.phase != "preflight":
        raise SystemExit("synthetic backend is authorized for preflight wiring only")
    if args.backend == "hf" and not args.expected_code_commit:
        raise SystemExit("--expected-code-commit is required for HF phases")
    if args.phase == "preflight":
        return _preflight(args)
    if args.phase == "dev":
        return _dev(args)
    return _test(args)


if __name__ == "__main__":
    raise SystemExit(main())
