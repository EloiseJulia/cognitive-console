"""Run Workstream D faithful-PSR arm without changing frozen adjudication math."""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cognitive_console.activations.provider import SyntheticActivationProvider
from cognitive_console.experiments import adjudicate_c2b as adj
from cognitive_console.experiments.adjudicate_c2b import (
    AxisAdjSpec,
    CheckpointStore,
    ProgressTracker,
    RunContext,
    plan_generation_counts,
)
from cognitive_console.lineage import git_commit, utcnow
from cognitive_console.ops.disk_guard import check_disk_budget, default_guard_paths
from cognitive_console.registry import ExperimentRecord, ExperimentRegistry
from cognitive_console.steering import psr
from cognitive_console.steering.extract import min_layer_for_depth
from cognitive_console.steering.generate import SyntheticC2bTaskBackend
from cognitive_console.steering.iti import extract_iti

from scripts import run_c1_facade as c1
from scripts import run_c2b_adjudication as c2b
from scripts import run_gpu_phase0 as p0

DEFAULT_MODEL = "Qwen/Qwen2.5-7B-Instruct"
ADJ_AXES = c2b.ADJ_AXES


def _rel(path: Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(_REPO)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _split_items(items: Sequence[Dict], seed: int) -> Tuple[List[Dict], List[Dict]]:
    ids = [str(it["id"]) for it in items]
    by_id = {str(it["id"]): it for it in items}
    split = adj.split_dev_test(ids, dev_fraction=adj.DEV_FRACTION, seed=int(seed))
    return [by_id[i] for i in split.dev_ids], [by_id[i] for i in split.test_ids]


def _synthetic_basis(axis: str, layer: int, dim: int = 24, seed: int = 0) -> psr.PSRBasis:
    provider = SyntheticActivationProvider(dim=dim, layers=(1, 2, 3, 4), seed=seed, noise_scale=0.05)
    pos = [f"{axis} pos {i}" for i in range(24)]
    neg = [f"{axis} neg {i}" for i in range(24)]
    caa = provider.plant_contrast(axis, pos, neg, magnitude=4.0, layer_gain={layer: 1.0})
    # Deliberately make ITI independent-ish but unit-length.
    rng = np.random.default_rng(seed + len(axis))
    iti = rng.normal(size=dim)
    acts = provider.get_activations(pos + neg + [f"{axis} natural {i}" for i in range(24)], layer)
    return psr.build_psr_basis(
        axis=axis,
        layer=layer,
        caa_direction=caa,
        iti_direction=iti,
        natural_activations=acts,
        r=16,
    )


def build_specs_synthetic_psr(args, out_dir: Path, transcript_collector=None):
    neutral = c1.load_neutral_prompts()[0]
    specs: List[AxisAdjSpec] = []
    results: Dict[str, psr.PSRResult] = {}
    schedule_by_axis = {}
    backends: Dict[str, SyntheticC2bTaskBackend] = {}
    cfg = psr.PSRConfig(
        basis_rank=int(args.psr_rank),
        candidate_budget=int(args.psr_candidate_budget),
        optimizer_seed=int(args.psr_seed),
        coherence_lambda=float(args.psr_coherence_lambda),
    )
    for axis in args.axes:
        items = c2b.load_axis_items(axis, True, args.n_items)
        dev_items, test_items = _split_items(items, args.seed)
        basis = _synthetic_basis(axis, layer=3, seed=args.seed)
        backend = SyntheticC2bTaskBackend(axis, items, prompt_gain=0.4, alpha_gain=0.1, threshold=0.5)
        backends[axis] = backend

        def sampler_factory(schedule, backend=backend):
            return psr.PSROutcomeSampler(
                backend,
                schedule_by_axis=schedule,
                max_new_tokens=args.max_new_tokens,
                do_sample=False,
                seed=args.seed,
                batch_size=args.batch_size,
            )

        opt = psr.optimize_psr_on_dev(
            axis=axis,
            model="synthetic-offline",
            backend="synthetic",
            basis=basis,
            sampler_factory=sampler_factory,
            dev_items=dev_items,
            forbidden_test_items=test_items,
            neutral_prompt=neutral,
            config=cfg,
            k=adj.K_SAMPLES,
            num_hidden_layers=4,
        )
        results[axis] = opt
        schedule_by_axis[axis] = (opt.schedule_layers, opt.schedule_weights)
        specs.append(
            AxisAdjSpec(
                axis=axis,
                items=items,
                strong_prompts=c2b.build_strong_prompts(axis, args.n_strong),
                neutral_prompt=neutral,
                direction=opt.direction_array(),
                layer=opt.layer,
            )
        )

    def sampler_for_axis(axis: str):
        return psr.PSROutcomeSampler(
            backends[axis],
            schedule_by_axis=schedule_by_axis,
            max_new_tokens=args.max_new_tokens,
            do_sample=False,
            seed=args.seed,
            batch_size=args.batch_size,
            generation_observer=(
                transcript_collector.record_generation if transcript_collector is not None else None
            ),
        )

    return specs, results, sampler_for_axis, "synthetic-offline", "cpu-offline"


def _hf_natural_activations(provider, axis: str, layer: int, n_extraction: int, seed: int) -> np.ndarray:
    pairs = c1.load_axis_pairs(axis)
    split = c1.make_split(list(pairs.pos.keys()), n_extraction=n_extraction, seed=seed)
    pos = [pairs.pos[p] for p in split.extraction_ids]
    neg = [pairs.neg[p] for p in split.extraction_ids]
    natural = c1.load_neutral_prompts() + pos + neg
    return provider.get_activations(natural, layer)


def build_specs_hf_psr(args, out_dir: Path, transcript_collector=None):
    from cognitive_console.activations.provider import HFActivationProvider

    device, dtype = p0._pick_device(), p0._pick_dtype()
    model = args.model or DEFAULT_MODEL
    c1_out = out_dir / "c1"
    c1_payload = c1.run(
        model=model,
        axes=args.axes,
        scan_step=2,
        n_extraction=args.n_extraction,
        seed=args.seed,
        n_null=2000,
        out_dir=c1_out,
        ram_floor_mb=0.0,
        device=device,
        dtype=dtype,
    )
    c1_by_axis = {r["axis"]: r for r in c1_payload["axes"]}
    provider = HFActivationProvider(model, device=device, dtype=dtype,
                                    cache_dir=str(c1_out / "activations" / "cache"))
    neutral = c1.load_neutral_prompts()[0]
    neutral_all = c1.load_neutral_prompts()
    cfg = psr.PSRConfig(
        basis_rank=int(args.psr_rank),
        candidate_budget=int(args.psr_candidate_budget),
        optimizer_seed=int(args.psr_seed),
        coherence_lambda=float(args.psr_coherence_lambda),
    )
    backend = psr.ScheduledSteeredHFBackend(model, device=device, dtype=dtype, seed=args.seed)
    specs: List[AxisAdjSpec] = []
    results: Dict[str, psr.PSRResult] = {}
    schedule_by_axis = {}
    for axis in args.axes:
        row = c1_by_axis.get(axis, {})
        layer = int(row.get("chosen_layer", max(1, provider.available_layers()[-1] // 2)))
        caa_direction = p0._extract_direction(provider, axis, layer, args.n_extraction, args.seed)
        pairs = c1.load_axis_pairs(axis)
        split = c1.make_split(list(pairs.pos.keys()), n_extraction=args.n_extraction, seed=args.seed)
        ext_pos = [pairs.pos[p] for p in split.extraction_ids]
        ext_neg = [pairs.neg[p] for p in split.extraction_ids]
        candidate_layers = [ell for ell in provider.available_layers() if ell >= 1]
        iti = extract_iti(
            provider,
            axis=axis,
            pos_texts=ext_pos,
            neg_texts=ext_neg,
            layers=candidate_layers,
            selection="nondegenerate",
            neutral_texts=neutral_all,
            min_layer=min_layer_for_depth(max(candidate_layers), min_depth_frac=0.2),
            n_null=2000,
            null_seed=args.seed,
        )
        acts = _hf_natural_activations(provider, axis, layer, args.n_extraction, args.seed)
        basis = psr.build_psr_basis(
            axis=axis,
            layer=layer,
            caa_direction=caa_direction,
            iti_direction=iti.direction,
            natural_activations=acts,
            r=args.psr_rank,
        )
        items = c2b.load_axis_items(axis, args.use_fixture, args.n_items)
        dev_items, test_items = _split_items(items, args.seed)

        def sampler_factory(schedule, backend=backend):
            return psr.PSROutcomeSampler(
                backend,
                schedule_by_axis=schedule,
                max_new_tokens=args.max_new_tokens,
                do_sample=True,
                temperature=args.temperature,
                seed=args.seed,
                batch_size=args.batch_size,
            )

        opt = psr.optimize_psr_on_dev(
            axis=axis,
            model=model,
            backend="hf",
            basis=basis,
            sampler_factory=sampler_factory,
            dev_items=dev_items,
            forbidden_test_items=test_items,
            neutral_prompt=neutral,
            config=cfg,
            k=adj.K_SAMPLES,
            num_hidden_layers=max(candidate_layers),
        )
        results[axis] = opt
        schedule_by_axis[axis] = (opt.schedule_layers, opt.schedule_weights)
        specs.append(
            AxisAdjSpec(
                axis=axis,
                items=items,
                strong_prompts=c2b.build_strong_prompts(axis, args.n_strong),
                neutral_prompt=neutral,
                direction=opt.direction_array(),
                layer=opt.layer,
            )
        )

    def sampler_for_axis(axis: str):
        return psr.PSROutcomeSampler(
            backend,
            schedule_by_axis=schedule_by_axis,
            max_new_tokens=args.max_new_tokens,
            do_sample=True,
            temperature=args.temperature,
            seed=args.seed,
            batch_size=args.batch_size,
            generation_observer=(
                transcript_collector.record_generation if transcript_collector is not None else None
            ),
        )

    return specs, results, sampler_for_axis, model, f"{device}-{dtype}"


def _fingerprint_payload(args, model: str, specs: Sequence[AxisAdjSpec],
                         psr_results: Dict[str, psr.PSRResult]) -> Dict[str, object]:
    return {
        "runner": "scripts/run_psr_arm.py",
        "steering_method": "psr",
        "model": model,
        "backend": args.backend,
        "seed": int(args.seed),
        "max_new_tokens": int(args.max_new_tokens),
        "temperature": float(args.temperature),
        "batch_size": int(args.batch_size),
        "k": int(adj.K_SAMPLES),
        "alpha_grid": list(adj.ALPHA_GRID),
        "bootstrap_b": int(args.bootstrap_b),
        "coherence_max_ratio": float(adj.COHERENCE_MAX_RATIO),
        "delta": float(adj.DELTA),
        "bonferroni_ci_level": float(adj.BONFERRONI_CI_LEVEL),
        "dev_fraction": float(adj.DEV_FRACTION),
        "psr": {axis: row.to_dict() for axis, row in sorted(psr_results.items())},
        "axes": {
            spec.axis: {
                "n_items": len(spec.items),
                "item_ids": [str(it["id"]) for it in spec.items],
                "n_strong": len(spec.strong_prompts),
                "strong_ids": [str(pid) for pid, _ in spec.strong_prompts],
            }
            for spec in specs
        },
    }


def write_results(report: adj.AdjudicationReport, out_dir: Path, meta: Dict) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = report.to_dict()
    payload.update(meta)
    path = out_dir / "psr_c2b_adjudication_results.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def register(out_dir: Path, result_path: Path, meta: Dict, report: adj.AdjudicationReport,
             seed: int, config_fingerprint: str) -> str:
    registry = ExperimentRegistry(str(out_dir / "experiment-registry.yaml"))
    # The prereg requires the PSR optimization config to be collision-proof in
    # both the config_fingerprint and experiment_id.  Use the full fingerprint,
    # not the repository-wide 8-char lineage slug used by generic helpers.
    stem = f"psr-c2b-adj-{config_fingerprint}"
    taken = {str(x) for x in registry.ids()}
    n = 1
    while f"{stem}-{n:04d}" in taken:
        n += 1
    exp_id = f"{stem}-{n:04d}"
    record = ExperimentRecord(
        experiment_id=exp_id,
        hypothesis_id="H2",
        claim_ids=["C2b"],
        type="exploratory",
        status="done",
        code_commit=git_commit(str(_REPO)),
        config_hash=f"sha256:{config_fingerprint}",
        model=str(meta.get("model")),
        dataset="data/c2b_tasks/* (fixtures) or deferred real loaders",
        seed=int(seed),
        hardware=str(meta.get("hardware")),
        started_at=meta.get("started_at"),
        ended_at=utcnow(),
        exit_code=0,
        summary_metrics={
            "_verdict": report.verdict,
            "_axis_passes": report.axis_passes,
            "_steering_method": "psr",
        },
        artifacts=[_rel(result_path)],
        valid_for_paper=False,
        validation_notes=(
            "Faithful-PSR Workstream D arm. Frozen C2b adjudicator imported "
            "unchanged; PSR optimization is DEV-only and provenance guarded."
        ),
    )
    registry.append(record)
    return exp_id


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Faithful-PSR DEV-optimized C2b arm")
    ap.add_argument("--backend", choices=["synthetic", "hf"], default="synthetic")
    ap.add_argument("--model", default=None)
    ap.add_argument("--axes", nargs="*", default=ADJ_AXES)
    ap.add_argument("--use-fixture", action="store_true")
    ap.add_argument("--n-items", type=int, default=None)
    ap.add_argument("--n-strong", type=int, default=c2b.DEFAULT_N_STRONG)
    ap.add_argument("--n-extraction", type=int, default=28)
    ap.add_argument("--psr-rank", type=int, default=16)
    ap.add_argument("--psr-candidate-budget", type=int, default=32)
    ap.add_argument("--psr-seed", type=int, default=20260723)
    ap.add_argument("--psr-coherence-lambda", type=float, default=1.0)
    ap.add_argument("--bootstrap-b", type=int, default=adj.BOOTSTRAP_B)
    ap.add_argument("--allow-underpowered", action="store_true")
    ap.add_argument("--max-new-tokens", type=int, default=64)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--seed", type=int, default=20260723)
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--save-transcripts", action=argparse.BooleanOptionalAction, default=True,
                    help="emit raw per-generation transcripts for hostile audit (default: true)")
    ap.add_argument("--disk-budget-gb", type=float, default=15.0)
    ap.add_argument("--disk-ceiling-gb", type=float, default=70.0)
    ap.add_argument("--hf-home", default=None)
    ap.add_argument("--venv", default=None)
    ap.add_argument("--out-dir", default=None)
    return ap


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.bootstrap_b < 10000 and not args.allow_underpowered:
        raise SystemExit(
            f"[psr-arm] FATAL: --bootstrap-b {args.bootstrap_b} < frozen 10000; "
            "pass --allow-underpowered for smoke/debug only."
        )
    if int(args.psr_candidate_budget) > 32:
        raise SystemExit("[psr-arm] --psr-candidate-budget must be <= frozen cap 32")
    if int(args.psr_rank) != 16:
        raise SystemExit("[psr-arm] primary prereg requires --psr-rank 16")
    if float(args.psr_coherence_lambda) != 1.0:
        raise SystemExit("[psr-arm] primary prereg requires --psr-coherence-lambda 1.0")

    out_dir = Path(args.out_dir) if args.out_dir else (
        _REPO / "results" / f"psr_arm_{args.backend}_{utcnow().split('T')[0]}"
    )
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    started_at = utcnow()
    t0 = time.time()

    model_hint = (args.model or DEFAULT_MODEL) if args.backend == "hf" else "synthetic-offline"
    transcript_collector = (
        c2b.TranscriptCollector(out_dir, model_hint, "psr", args.backend)
        if args.save_transcripts else None
    )

    if args.backend == "hf":
        usage0 = check_disk_budget(default_guard_paths(args.hf_home, args.venv),
                                   args.disk_budget_gb, args.disk_ceiling_gb)
        print(f"[psr-arm] disk pre-run: {usage0.message}", flush=True)
        specs, psr_results, sampler_for_axis, model, hardware = build_specs_hf_psr(
            args, out_dir, transcript_collector
        )
    else:
        specs, psr_results, sampler_for_axis, model, hardware = build_specs_synthetic_psr(
            args, out_dir, transcript_collector
        )

    fp_payload = _fingerprint_payload(args, model, specs, psr_results)
    fingerprint = psr.canonical_json_hash(fp_payload, n=32)
    expected_items = {spec.axis: [str(it["id"]) for it in spec.items] for spec in specs}
    provenance = psr.psr_provenance_payload(
        model=model,
        backend=args.backend,
        seed=args.seed,
        psr_results=psr_results,
        adjudication_params=adj.frozen_params_dict(),
        item_ids_by_axis=expected_items,
        extra={"fingerprint_payload": fp_payload},
    )
    per_axis_plan, total_plan = plan_generation_counts(specs)
    print(f"[psr-arm] config_fingerprint={fingerprint}", flush=True)
    print(f"[psr-arm] planned adjudication generations={total_plan} per_axis={per_axis_plan}", flush=True)
    print(
        "[psr-arm] PSR DEV optimizer evals: "
        + ", ".join(f"{a}={r.evaluations_used}/{r.candidate_budget}" for a, r in psr_results.items()),
        flush=True,
    )

    checkpoint_cls = c2b.TranscriptCheckpointStore if transcript_collector is not None else CheckpointStore
    checkpoint_kwargs = {"collector": transcript_collector} if transcript_collector is not None else {}
    checkpoint = checkpoint_cls(
        out_dir / "checkpoints", fingerprint, seed=args.seed, fresh=args.fresh, **checkpoint_kwargs
    )
    progress = ProgressTracker(total_planned=total_plan)
    try:
        report = adj.adjudicate(
            sampler_for_axis,
            specs,
            k=adj.K_SAMPLES,
            alpha_grid=adj.ALPHA_GRID,
            bootstrap_b=args.bootstrap_b,
            ci_level=adj.BONFERRONI_CI_LEVEL,
            delta=adj.DELTA,
            coherence_max_ratio=adj.COHERENCE_MAX_RATIO,
            dev_fraction=adj.DEV_FRACTION,
            seed=args.seed,
            ctx=RunContext(checkpoint=checkpoint, progress=progress),
        )
    finally:
        checkpoint.close()

    meta = {
        "model": model,
        "backend": args.backend,
        "hardware": hardware,
        "steering_method": "psr",
        "run_type": "exploratory",
        "valid_for_paper": False,
        "protocol_frozen": True,
        "prereg": "docs/ledgers/prereg-latent-recovery-arm.md (FROZEN Option 1) + prereg-c2b-adjudication.md",
        "started_at": started_at,
        "generated_at": utcnow(),
        "wall_clock_seconds": round(time.time() - t0, 2),
        "platform": platform.platform(),
        "use_fixture": bool(args.use_fixture) or args.backend == "synthetic",
        "config_fingerprint": fingerprint,
        "config_fingerprint_payload": fp_payload,
        "psr_provenance": provenance,
    }
    validation_payload = report.to_dict()
    validation_payload.update(meta)
    psr.validate_psr_coverage(
        result_payload=validation_payload,
        expected_fingerprint=fingerprint,
        expected_axes=args.axes,
        expected_item_ids_by_axis=expected_items,
        expected_k=adj.K_SAMPLES,
    )
    result_path = write_results(report, out_dir, meta)
    transcript_root = None
    if transcript_collector is not None:
        transcript_root = transcript_collector.write_all(out_dir, report)
        print(f"[psr-arm] transcripts: {_rel(transcript_root)}", flush=True)
    exp_id = register(out_dir, result_path, meta, report, args.seed, fingerprint)
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    payload["experiment_id"] = exp_id
    result_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[psr-arm] VERDICT: {report.verdict}", flush=True)
    print(f"[psr-arm] wrote {_rel(result_path)} experiment_id={exp_id}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
