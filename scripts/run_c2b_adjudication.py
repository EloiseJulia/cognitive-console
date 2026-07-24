"""C2b QUALIFIED adjudication runner — FROZEN instrument (prereg §4/§5).

Runs the pre-registered, three-tier C2b behavioral-gap adjudication:
DEV/TEST split -> DEV-frozen best-of-16 prompt + coherence-gated α -> TEST paired
per-item diffs -> paired ITEM-cluster bootstrap (B≥10000, Bonferroni CI 1−0.05/3)
-> per-axis pass (CI excludes 0 AND mean(d)≥δ=0.05 AND coherence ≤1.5×) ->
three-tier verdict (STRONG_GO / CONDITIONAL_GO / KILL_PLAN_D). Conflict cells are
SECONDARY/descriptive only.

Two backends (model-independent core):
* ``--backend synthetic`` — offline, no torch: exercises the WHOLE pipeline on the
  bundled fixtures with ``SyntheticC2bTaskBackend`` and produces a real verdict
  artifact. This is the CPU smoke that proves the pipeline end-to-end.
* ``--backend hf`` — real ``SteeredHFBackend`` (CPU/1.5B smoke or A800/7B). Re-
  derives the C1 chosen non-degenerate layer per axis + the CAA unit direction at
  that layer on the RUN's model (never hardcoded), reuses the disk guard, and runs
  the adjudication with sampled (k=5) generation.

EVERYTHING is EXPLORATORY until the A800 7B run: valid_for_paper=false, honest
wall-clock, numbers only from computed artifacts. See RUN_ON_A800.md §Adjudication.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import threading
import time
from dataclasses import asdict
from datetime import date
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
from cognitive_console.experiments.adjudicate_c2b import (
    AxisAdjSpec, BackendOutcomeSampler, CheckpointStore, ProgressTracker,
    RunContext, plan_generation_counts,
)
from cognitive_console.steering.generate import SyntheticC2bTaskBackend
from cognitive_console.steering.extract import min_layer_for_depth
from cognitive_console.steering.iti import extract_iti, sigma_scaled_alpha
from cognitive_console.config import config_hash
from cognitive_console.registry import ExperimentRecord, ExperimentRegistry
from cognitive_console.lineage import git_commit, new_experiment_id, utcnow
from cognitive_console.manifest import ArtifactManifest, write_manifest
from cognitive_console.ops.disk_guard import check_disk_budget, default_guard_paths

from scripts import run_c1_facade as c1
from scripts import run_gpu_phase0 as p0

# The three FROZEN axes (focus DROPPED per prereg §1.6).
ADJ_AXES = ["deliberation", "skepticism", "uncertainty_awareness"]
DEFAULT_MODEL = "Qwen/Qwen2.5-7B-Instruct"
SMOKE_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
DEFAULT_N_STRONG = 16  # best-of-16 authored prompts (prereg §4)
DEFAULT_STEERING_METHOD = "caa"


def _rel(path: Path) -> str:
    p = Path(path).resolve()
    try:
        return str(p.relative_to(_REPO)).replace("\\", "/")
    except ValueError:
        return str(p).replace("\\", "/")


def _config_fingerprint(args, model: str, specs) -> str:
    """Stable hash of everything that affects generated outcomes, so a resumed run
    only reuses checkpoints from an IDENTICAL config (seed/model/N/items/gen knobs).
    Changing max_new_tokens, temperature, seed, model, or the item set invalidates
    resume (fresh generations), keeping the frozen verdict faithful."""
    payload = {
        "seed": int(args.seed),
        "model": str(model),
        "backend": str(args.backend),
        "steering_method": str(getattr(args, "steering_method", DEFAULT_STEERING_METHOD)),
        "max_new_tokens": int(args.max_new_tokens),
        "temperature": float(args.temperature),
        # batch_size changes the chunk composition, hence each chunk's derived
        # batch_seed and RNG stream, hence the sampled outcomes — so it MUST be in
        # the fingerprint (MAJOR-1): resuming with a different --batch-size would
        # otherwise silently reuse a cache built at a different composition and
        # yield non-reproducible sampled cells. do_sample likewise gates whether
        # the RNG path is used at all (hf=True samples, synthetic=greedy).
        "batch_size": int(args.batch_size),
        "do_sample": bool(args.backend == "hf"),
        "k": int(adj.K_SAMPLES),
        "alpha_grid": list(adj.ALPHA_GRID),
        "dev_fraction": float(adj.DEV_FRACTION),
        "axes": {
            spec.axis: {
                "n_items": len(spec.items),
                "item_ids": sorted(str(it["id"]) for it in spec.items),
                "n_strong": len(spec.strong_prompts),
                "strong_ids": [str(pid) for pid, _ in spec.strong_prompts],
            }
            for spec in specs
        },
    }
    blob = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]


class ScaledBackendOutcomeSampler(BackendOutcomeSampler):
    """Outcome sampler with per-axis alpha scaling (ITI uses alpha*sigma)."""

    def __init__(self, *args, alpha_scale_by_axis: Optional[Dict[str, float]] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.alpha_scale_by_axis = dict(alpha_scale_by_axis or {})

    def _scaled_alpha(self, axis: str, alpha: float) -> float:
        scale = float(self.alpha_scale_by_axis.get(axis, 1.0))
        return sigma_scaled_alpha(alpha, scale)

    def sample(self, axis, item, instruction, alpha, k, direction, layer):
        return super().sample(
            axis, item, instruction, self._scaled_alpha(axis, alpha), k, direction, layer
        )

    def sample_batch(self, axis, items, instruction, alpha, k, direction, layer):
        return super().sample_batch(
            axis, items, instruction, self._scaled_alpha(axis, alpha), k, direction, layer
        )


# --------------------------------------------------------------------------- #
# MINOR-1: silent-hang watchdog + honest CUDA/driver error labeling
# --------------------------------------------------------------------------- #
_CUDA_TOKENS = ("cuda", "cublas", "cudnn", "device", "nccl", "hip", "gpu",
                "out of memory")


def _looks_like_cuda_error(exc: BaseException) -> bool:
    """Only call an error 'likely CUDA/driver' if its text actually looks like one
    (MINOR-1): a plain RuntimeError from unrelated code would otherwise be
    mislabeled as a GPU fault, misdirecting triage."""
    msg = f"{type(exc).__name__}: {exc}".lower()
    return any(tok in msg for tok in _CUDA_TOKENS)


def watchdog_should_abort(last_activity_ts: float, stall_timeout: float,
                          now: Optional[float] = None) -> bool:
    """Pure, testable stall decision: True iff more than ``stall_timeout`` seconds
    have elapsed since ``last_activity_ts``. ``stall_timeout <= 0`` disables the
    watchdog (never aborts). The runner (never the test) turns True into os._exit.

    This targets the D-0029 failure mode: a SILENT 100%-CPU spin after a host
    driver reload that raises NO exception, so ``except (RuntimeError, MemoryError)``
    never fires and the process holds a borrowed GPU forever."""
    if stall_timeout is None or float(stall_timeout) <= 0:
        return False
    ref = time.time() if now is None else float(now)
    return (ref - float(last_activity_ts)) > float(stall_timeout)


class InactivityWatchdog:
    """Background daemon thread that hard-exits the process if no generation cell
    has completed for longer than ``stall_timeout`` seconds. Off when timeout<=0.

    The abort action is injected (``on_abort``) so tests can assert firing without
    actually calling ``os._exit``; the runner uses the default hard-exit."""

    def __init__(self, progress, stall_timeout: float,
                 check_interval: Optional[float] = None, on_abort=None):
        self.progress = progress
        self.stall_timeout = float(stall_timeout)
        if check_interval is not None:
            self.check_interval = float(check_interval)
        else:
            self.check_interval = min(30.0, max(1.0, self.stall_timeout / 10.0))
        self._on_abort = on_abort if on_abort is not None else self._default_abort
        self._thread = None
        self._stop = threading.Event()

    def start(self) -> "InactivityWatchdog":
        if self.stall_timeout <= 0:
            return self  # disabled
        self._thread = threading.Thread(
            target=self._run, name="c2b-stall-watchdog", daemon=True)
        self._thread.start()
        return self

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:
        while not self._stop.wait(self.check_interval):
            last = getattr(self.progress, "last_activity", None)
            if last is None:
                continue
            if watchdog_should_abort(last, self.stall_timeout):
                idle = time.time() - float(last)
                self._on_abort(self.stall_timeout, idle)
                return

    @staticmethod
    def _default_abort(stall_timeout: float, idle: float) -> None:
        msg = (f"\n[c2b-adj] FATAL STALL: no generation cell completed for "
               f"{idle:.0f}s (> --stall-timeout {stall_timeout:.0f}s). This is the "
               f"D-0029 silent-hang mode (100% CPU spin, NO exception raised, e.g. "
               f"after a host driver reload). Hard-exiting non-zero so the process "
               f"does NOT spin forever holding a borrowed GPU. Partial results are "
               f"CHECKPOINTED per-cell; re-run the SAME command (no --fresh) to "
               f"RESUME.\n")
        sys.stderr.write(msg)
        sys.stderr.flush()
        sys.stdout.flush()
        os._exit(3)


# --------------------------------------------------------------------------- #
# Spec construction
# --------------------------------------------------------------------------- #
def load_axis_items(axis: str, use_fixture: bool, n_items: Optional[int]) -> List[Dict]:
    """Load items for one axis with frozen per-axis caps by default.

    If ``n_items`` is provided, it explicitly overrides the cap. Otherwise we use
    the frozen preregistered per-axis default from ``adj.N_ITEMS_BY_AXIS`` when
    available. Unknown axes keep the legacy uncapped behavior.
    """
    task = c2b_tasks.load_c2b_task(axis, use_fixture=use_fixture)
    items = list(task.items)
    cap = n_items if n_items is not None else adj.N_ITEMS_BY_AXIS.get(axis)
    if cap is not None:
        items = items[:cap]
    return items


def build_strong_prompts(axis: str, n_strong: int) -> List:
    strong = c1.load_strongest_prompts(axis)
    return list(zip(strong.ids, strong.texts))[:n_strong]


def build_specs_synthetic(axes: List[str], use_fixture: bool,
                          n_items: Optional[int], n_strong: int) -> List[AxisAdjSpec]:
    """Offline specs — direction/layer are placeholders the synthetic backend ignores."""
    specs = []
    neutral = c1.load_neutral_prompts()[0]
    for axis in axes:
        items = load_axis_items(axis, use_fixture, n_items)
        specs.append(AxisAdjSpec(
            axis=axis, items=items, strong_prompts=build_strong_prompts(axis, n_strong),
            neutral_prompt=neutral, direction=np.ones(8), layer=3,
        ))
    return specs


def build_specs_hf(axes: List[str], model: str, use_fixture: bool,
                   n_items: Optional[int], n_strong: int, n_extraction: int,
                   seed: int, out_dir: Path, steering_method: str = DEFAULT_STEERING_METHOD
                   ) -> (List[AxisAdjSpec], Dict):  # noqa
    """Real specs: derive per-axis steering direction on THIS model.

    * ``caa``: mean-difference direction at C1's chosen non-degenerate layer.
    * ``iti``: logistic-probe direction with the same non-degenerate layer rule;
      intervention uses alpha in sigma-units (effective magnitude alpha*sigma).
    """
    from cognitive_console.activations.provider import HFActivationProvider

    device, dtype = p0._pick_device(), p0._pick_dtype()
    c1_out = out_dir / "c1"
    c1_payload = c1.run(
        model=model, axes=axes, scan_step=2, n_extraction=n_extraction, seed=seed,
        n_null=2000, out_dir=c1_out, ram_floor_mb=0.0, device=device, dtype=dtype,
    )
    c1_by_axis = {r["axis"]: r for r in c1_payload["axes"]}

    provider = HFActivationProvider(model, device=device, dtype=dtype,
                                    cache_dir=str(c1_out / "activations" / "cache"))
    neutral = c1.load_neutral_prompts()[0]
    neutral_all = c1.load_neutral_prompts()
    specs = []
    layer_info = {}
    alpha_scale_by_axis: Dict[str, float] = {}
    for axis in axes:
        row = c1_by_axis.get(axis, {})
        if steering_method == "caa":
            layer = int(row.get("chosen_layer", max(1, provider.available_layers()[-1] // 2)))
            direction = p0._extract_direction(provider, axis, layer, n_extraction, seed)
            sigma = 1.0
            steering_diag = {"selection": "c1_chosen_layer", "sigma": sigma}
        elif steering_method == "iti":
            pairs = c1.load_axis_pairs(axis)
            split = c1.make_split(
                list(pairs.pos.keys()), n_extraction=n_extraction, seed=seed
            )
            ext_pos = [pairs.pos[p] for p in split.extraction_ids]
            ext_neg = [pairs.neg[p] for p in split.extraction_ids]
            candidate_layers = [ell for ell in provider.available_layers() if ell >= 1]
            min_layer = min_layer_for_depth(max(candidate_layers), min_depth_frac=0.2)
            iti = extract_iti(
                provider,
                axis=axis,
                pos_texts=ext_pos,
                neg_texts=ext_neg,
                layers=candidate_layers,
                selection="nondegenerate",
                neutral_texts=neutral_all,
                min_layer=min_layer,
                min_depth_frac=0.2,
                n_null=2000,
                null_seed=seed,
            )
            layer = int(iti.layer)
            direction = iti.direction
            sigma = float(iti.sigma)
            steering_diag = {
                "selection": iti.selection,
                "sigma": sigma,
                "iti_probe_norm": float(np.linalg.norm(iti.vector)),
            }
        else:
            raise ValueError(f"unsupported steering method: {steering_method!r}")

        alpha_scale_by_axis[axis] = sigma
        items = load_axis_items(axis, use_fixture, n_items)
        specs.append(AxisAdjSpec(
            axis=axis, items=items, strong_prompts=build_strong_prompts(axis, n_strong),
            neutral_prompt=neutral, direction=direction, layer=layer,
        ))
        layer_info[axis] = {"chosen_layer": layer,
                            "stable_layer_found": row.get("stable_layer_found"),
                            **steering_diag}
    return specs, {
        "c1_layer_info": layer_info,
        "model": model,
        "steering_method": steering_method,
        "alpha_scale_by_axis": alpha_scale_by_axis,
    }


# --------------------------------------------------------------------------- #
# Samplers
# --------------------------------------------------------------------------- #
def synthetic_sampler_factory(use_fixture: bool, n_items: Optional[int]):
    def factory(axis: str):
        items = load_axis_items(axis, use_fixture, n_items)
        backend = SyntheticC2bTaskBackend(axis, items, prompt_gain=0.4,
                                          alpha_gain=0.1, threshold=0.5)
        return BackendOutcomeSampler(backend, do_sample=False)
    return factory


def hf_sampler_factory(model: str, max_new_tokens: int, temperature: float,
                       seed: int, batch_size: int,
                       alpha_scale_by_axis: Optional[Dict[str, float]] = None):
    from cognitive_console.steering.generate import SteeredHFBackend
    device, dtype = p0._pick_device(), p0._pick_dtype()
    backend = SteeredHFBackend(model, device=device, dtype=dtype, seed=seed)

    def factory(axis: str):
        return ScaledBackendOutcomeSampler(
            backend,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=temperature,
            seed=seed,
            batch_size=batch_size,
            alpha_scale_by_axis=alpha_scale_by_axis,
        )
    return factory


# --------------------------------------------------------------------------- #
# Output + registration
# --------------------------------------------------------------------------- #
def write_results(report: adj.AdjudicationReport, out_dir: Path, meta: Dict) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = report.to_dict()
    payload.update(meta)
    json_path = out_dir / "c2b_adjudication_results.json"
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)

    lines: List[str] = []
    lines.append("# C2b QUALIFIED Adjudication — FROZEN instrument (prereg §4/§5)\n")
    lines.append(f"- verdict: **{report.verdict}**")
    lines.append(f"- model: `{meta.get('model')}`   backend: `{meta.get('backend')}`   "
                 f"valid_for_paper: **{meta.get('valid_for_paper')}**")
    lines.append(f"- run_type: **{meta.get('run_type')}**   "
                 f"bootstrap_B: {report.frozen_params['bootstrap_b']}   "
                 f"CI level: {report.frozen_params['bonferroni_ci_level']:.5f} (Bonferroni 1−0.05/3)")
    lines.append(f"- δ = {report.frozen_params['delta']}   α grid: {report.frozen_params['alpha_grid']}")
    lines.append("")
    lines.append("| axis | layer | frozen α | best prompt | n_dev | n_test | mean(d) | CI | coherence | PASS |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in report.axis_results:
        ds = r.dev_selection
        ci = "n/a" if r.mean_diff != r.mean_diff else f"[{r.ci_lo:+.3f}, {r.ci_hi:+.3f}]"
        md = "n/a" if r.mean_diff != r.mean_diff else f"{r.mean_diff:+.3f}"
        lines.append(
            f"| {r.axis} | {r.layer} | {ds.get('frozen_alpha')} | "
            f"{ds.get('best_prompt_id')} | {r.n_dev} | {r.n_test} | {md} | {ci} | "
            f"{'ok' if r.coherence_ok else 'FAIL'} | {'YES' if r.passed else 'no'} |")
    lines.append("")
    n_pass = sum(1 for v in report.axis_passes.values() if v)
    lines.append(f"- axes passing (Bonferroni): **{n_pass}/3** -> **{report.verdict}**")
    if report.verdict == adj.VERDICT_CONDITIONAL_GO:
        lines.append("- CONDITIONAL_GO: a pre-registered single-axis REPLICATION on fresh "
                     "items (new DEV/TEST draw, new seed) is REQUIRED before any claim (prereg §4).")
    lines.append("")
    lines.append("## Conflict cells (SECONDARY / descriptive only — NOT part of the verdict)\n")
    lines.append("| axis | opposite α | mean conflict outcome | mean prompt-pole | latent drags down? |")
    lines.append("|---|---|---|---|---|")
    for r in report.axis_results:
        cf = r.conflict
        if "mean_conflict_outcome" in cf:
            lines.append(f"| {r.axis} | {cf['alpha_opposite']} | "
                         f"{cf['mean_conflict_outcome']:.3f} | {cf['mean_prompt_pole_outcome']:.3f} | "
                         f"{cf['latent_drags_down']} |")
    summary_path = out_dir / "c2b_adjudication_summary.md"
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return json_path


def register(report: adj.AdjudicationReport, out_dir: Path, json_path: Path,
             meta: Dict, seed: int) -> str:
    reg_path = out_dir / "experiment-registry.yaml"
    registry = ExperimentRegistry(str(reg_path))
    cfg = {
        "kind": "c2b_qualified_adjudication",
        "model": meta.get("model"),
        "backend": meta.get("backend"),
        "axes": [r.axis for r in report.axis_results],
        "frozen_params": report.frozen_params,
        "seed": seed,
        "torch_seed": seed,  # base torch seed; per-(item,sample) seeds derived from it
    }
    cfg_hash = config_hash(cfg)
    summary_metrics = {
        r.axis: {
            "layer": r.layer,
            "frozen_alpha": r.dev_selection.get("frozen_alpha"),
            "mean_diff": r.mean_diff,
            "ci_lo": r.ci_lo, "ci_hi": r.ci_hi, "ci_level": r.ci_level,
            "coherence_ok": r.coherence_ok,
            "passed": r.passed,
        }
        for r in report.axis_results
    }
    summary_metrics["_verdict"] = report.verdict
    summary_metrics["_axis_passes"] = report.axis_passes
    summary_metrics["_torch_seed"] = seed

    valid_for_paper = bool(meta.get("valid_for_paper", False))
    run_type = str(meta.get("run_type", "exploratory"))
    exp_id = new_experiment_id(registry, "c2b-adj", cfg_hash)
    record = ExperimentRecord(
        experiment_id=exp_id, hypothesis_id="H2", claim_ids=["C2b"],
        type=run_type, status="done", code_commit=git_commit(str(_REPO)),
        config_hash=cfg_hash, model=str(meta.get("model")),
        dataset="data/c2b_tasks/* (fixtures) or deferred real loaders",
        seed=seed, hardware=str(meta.get("hardware")),
        started_at=meta.get("started_at"), ended_at=utcnow(), exit_code=0,
        summary_metrics=summary_metrics, artifacts=[_rel(json_path)],
        valid_for_paper=valid_for_paper,
        validation_notes=(
            "C2b QUALIFIED adjudication implementing FROZEN prereg §4/§5 "
            "(paired ITEM-cluster bootstrap B>=10000, Bonferroni CI 1-0.05/3, "
            "delta=0.05, coherence<=1.5x, three-tier verdict). "
            + ("EXPLORATORY until the A800 7B run (valid_for_paper=false); this run "
               "is a " + run_type + " on " + str(meta.get("backend")) + ".")
        ),
    )
    registry.append(record)
    manifest = ArtifactManifest(
        artifact_id="c2b-qualified-adjudication-table", supports_claims=["C2b"],
        source_experiments=[exp_id], aggregation_script="scripts/run_c2b_adjudication.py",
        aggregation_commit=git_commit(str(_REPO)), output_file=_rel(json_path),
        raw_data_hash=c1._sha256_file(json_path), last_verified=utcnow(), verdict="pending",
    )
    write_manifest(str(out_dir / "c2b_adjudication_table.manifest.yaml"), manifest)
    return exp_id


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="C2b QUALIFIED adjudication (FROZEN prereg §4/§5)")
    ap.add_argument("--backend", choices=["synthetic", "hf"], default="synthetic",
                    help="synthetic = offline no-torch pipeline smoke; hf = real model")
    ap.add_argument("--model", default=None,
                    help="HF model id (default: 7B for hf; ignored for synthetic)")
    ap.add_argument(
        "--steering-method",
        choices=["caa", "iti"],
        default=DEFAULT_STEERING_METHOD,
        help="steering family: caa(mean-diff) or iti(logistic-probe, alpha in sigma units)",
    )
    ap.add_argument("--axes", nargs="*", default=ADJ_AXES)
    ap.add_argument("--use-fixture", action="store_true",
                    help="use the bundled OFFLINE task fixtures (default for synthetic; "
                         "also the CPU/1.5B smoke). Omit on the A800 for the real loaders.")
    ap.add_argument("--n-items", type=int, default=None,
                    help="cap items/axis (default: frozen per-axis N; explicit value overrides)")
    ap.add_argument("--n-strong", type=int, default=DEFAULT_N_STRONG)
    ap.add_argument("--n-extraction", type=int, default=28)
    ap.add_argument("--bootstrap-b", type=int, default=adj.BOOTSTRAP_B)
    ap.add_argument("--allow-underpowered", action="store_true",
                    help="permit --bootstrap-b < frozen 10000 (prereg §5). OFF by "
                         "default: the confirmatory run HARD-FAILS if underpowered.")
    ap.add_argument("--max-new-tokens", type=int, default=64,
                    help="max new tokens per generation (default 64: these tasks "
                         "have SHORT answers — a number / MC letter / short answer "
                         "+ confidence; the prior 256 was overkill, D-0029). Tunable.")
    ap.add_argument("--batch-size", type=int, default=16,
                    help="padded GPU batch size for generation (hf backend). Cuts "
                         "wall-clock several-fold vs one-sequence-at-a-time (FIX 3). "
                         "The chunk = batch_size//k items generated in one batch.")
    ap.add_argument("--fresh", action="store_true",
                    help="ignore/clear any existing checkpoints and start over "
                         "(default: RESUME from out_dir/checkpoints if config matches).")
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--seed", type=int, default=20260723)
    ap.add_argument("--stall-timeout", type=float, default=600.0,
                    help="inactivity watchdog (MINOR-1): hard-exit non-zero if no "
                         "generation cell completes for this many seconds, to break "
                         "the D-0029 SILENT 100%%-CPU spin (no exception raised). "
                         "0 = disabled.")
    ap.add_argument("--disk-budget-gb", type=float, default=60.0)
    ap.add_argument("--disk-ceiling-gb", type=float, default=70.0)
    ap.add_argument("--hf-home", default=None)
    ap.add_argument("--venv", default=None)
    ap.add_argument("--out-dir", default=None)
    return ap


def main(argv: Optional[List[str]] = None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)
    axes = list(args.axes)

    if args.bootstrap_b < 10000:
        if not args.allow_underpowered:
            raise SystemExit(
                f"[c2b-adj] FATAL: --bootstrap-b {args.bootstrap_b} < frozen 10000 "
                f"(prereg §5). The confirmatory run requires B>=10000. Pass "
                f"--allow-underpowered to override for a smoke/debug run only.")
        print(f"[c2b-adj] WARNING: --bootstrap-b {args.bootstrap_b} < frozen 10000 "
              f"(prereg §5) but --allow-underpowered was passed; NOT valid for the "
              f"confirmatory adjudication.", flush=True)

    out_dir = Path(args.out_dir) if args.out_dir else (
        _REPO / "results" / f"c2b_adjudication_{args.backend}_{date.today().isoformat()}")
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    t_start = time.time()
    started_at = utcnow()

    if args.backend == "synthetic":
        use_fixture = True  # synthetic backend only makes sense on the offline fixtures
        specs = build_specs_synthetic(axes, use_fixture, args.n_items, args.n_strong)
        sampler_for_axis = synthetic_sampler_factory(use_fixture, args.n_items)
        model = "synthetic-offline"
        hardware = "cpu-offline"
        meta_extra: Dict = {"backend": "synthetic", "steering_method": args.steering_method,
                            "note": "offline no-torch pipeline smoke on fixtures"}
    else:
        model = args.model or DEFAULT_MODEL
        guard_paths = default_guard_paths(args.hf_home, args.venv)
        usage0 = check_disk_budget(guard_paths, args.disk_budget_gb, args.disk_ceiling_gb)
        print(f"[c2b-adj] disk pre-run: {usage0.message}", flush=True)
        specs, hf_meta = build_specs_hf(
            axes, model, args.use_fixture, args.n_items, args.n_strong,
            args.n_extraction, args.seed, out_dir, args.steering_method)
        # abort before spending on generation if the model download blew the budget
        usage_mid = check_disk_budget(guard_paths, args.disk_budget_gb,
                                      args.disk_ceiling_gb, raise_on_over=True)
        print(f"[c2b-adj] disk post-C1 (model loaded): {usage_mid.message}", flush=True)
        sampler_for_axis = hf_sampler_factory(model, args.max_new_tokens,
                                              args.temperature, args.seed,
                                              args.batch_size,
                                              hf_meta.get("alpha_scale_by_axis"))
        hardware = f"{p0._pick_device()}-{p0._pick_dtype()}"
        meta_extra = {"backend": "hf", **hf_meta}

    # --- FIX 4: up-front PLANNED generation count + rough wall-clock budget so
    # the run's size is visible BEFORE committing GPU time (sanity-check knob). ---
    per_axis_plan, total_plan = plan_generation_counts(
        specs, k=adj.K_SAMPLES, alpha_grid=adj.ALPHA_GRID,
        dev_fraction=adj.DEV_FRACTION)
    plan_str = ", ".join(f"{a}={c}" for a, c in per_axis_plan.items())
    print(f"[c2b-adj] PLANNED generations (upper bound): {plan_str}  "
          f"TOTAL={total_plan}", flush=True)
    n_batches = -(-total_plan // max(1, args.batch_size))  # ceil
    lo_h = n_batches * 2.0 / 3600.0
    hi_h = n_batches * 4.0 / 3600.0
    print(f"[c2b-adj] budget: batch_size={args.batch_size} "
          f"max_new_tokens={args.max_new_tokens} -> ~{n_batches} batches; "
          f"rough wall-clock ~{lo_h:.2f}-{hi_h:.2f}h "
          f"(assuming ~2-4 s/batch on the target GPU; SANITY-CHECK before "
          f"committing GPU time).", flush=True)

    # --- FIX 1/2: progress tracker + resumable checkpoint store ---
    fingerprint = _config_fingerprint(args, model, specs)
    ckpt_dir = out_dir / "checkpoints"
    checkpoint = CheckpointStore(ckpt_dir, fingerprint, seed=args.seed,
                                 fresh=args.fresh)
    progress = ProgressTracker(total_planned=total_plan)
    run_ctx = RunContext(checkpoint=checkpoint, progress=progress)
    print(f"[c2b-adj] checkpoints: {_rel(ckpt_dir)}  "
          f"(fresh={args.fresh}; resume auto-skips cells whose config matches)",
          flush=True)

    # --- FIX 5 + MINOR-1: a CUDA/driver error (e.g. driver reload) must NOT spin
    # forever; checkpoints are flushed per-cell, so we log clearly and EXIT
    # non-zero. A background inactivity watchdog also breaks the D-0029 SILENT
    # hang (100% CPU spin, NO exception) that the except below cannot catch. ---
    watchdog = InactivityWatchdog(progress, args.stall_timeout).start()
    try:
        report = adj.adjudicate(
            sampler_for_axis, specs, k=adj.K_SAMPLES, alpha_grid=adj.ALPHA_GRID,
            bootstrap_b=args.bootstrap_b, ci_level=adj.BONFERRONI_CI_LEVEL,
            delta=adj.DELTA, coherence_max_ratio=adj.COHERENCE_MAX_RATIO,
            dev_fraction=adj.DEV_FRACTION, seed=args.seed, ctx=run_ctx)
    except (RuntimeError, MemoryError) as exc:
        checkpoint.close()
        label = ("likely CUDA/driver" if _looks_like_cuda_error(exc)
                 else "generic error")
        print(f"\n[c2b-adj] FATAL generation error ({label}): "
              f"{type(exc).__name__}: {exc}", flush=True)
        print(f"[c2b-adj] partial results are CHECKPOINTED at {_rel(ckpt_dir)} — "
              f"re-run the SAME command (without --fresh) to RESUME.", flush=True)
        return 2
    finally:
        watchdog.stop()
        checkpoint.close()

    wall = time.time() - t_start
    meta = {
        "model": model, "hardware": hardware, "run_type": "exploratory",
        "valid_for_paper": False, "protocol_frozen": True,
        "prereg": "docs/ledgers/prereg-c2b-adjudication.md (FROZEN 2026-07-23)",
        "started_at": started_at, "generated_at": utcnow(),
        "wall_clock_seconds": round(wall, 2), "platform": platform.platform(),
        "use_fixture": bool(args.use_fixture) or args.backend == "synthetic",
        **meta_extra,
    }
    json_path = write_results(report, out_dir, meta)
    exp_id = register(report, out_dir, json_path, meta, args.seed)

    if args.backend == "hf":
        guard_paths = default_guard_paths(args.hf_home, args.venv)
        usage1 = check_disk_budget(guard_paths, args.disk_budget_gb,
                                   args.disk_ceiling_gb, raise_on_over=False)
        print(f"[c2b-adj] disk post-run: {usage1.message}", flush=True)

    print(f"\n[c2b-adj] VERDICT: {report.verdict}  "
          f"(axes passing: {sum(1 for v in report.axis_passes.values() if v)}/3)", flush=True)
    print(f"[c2b-adj] wrote {_rel(json_path)}  (exp {exp_id})  wall={wall:.1f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
