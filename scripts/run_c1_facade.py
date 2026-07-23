"""C1 "semantic facade" pilot — anti-circular, CPU-only, EXPLORATORY.

Run (from the worktree root):

    python -m scripts.run_c1_facade

or

    python scripts/run_c1_facade.py

What this measures (Claim C1, exploratory)
------------------------------------------
For each cognitive axis we ask: how far along the axis's CAA steering direction
does the *best human-readable prompt* push the model's activation, compared with
how far the latent *vector-only* intervention reaches? If readable prompts land
FAR SHORT of the latent vector (but still above a random-direction null), that is
the "semantic facade" gap that motivates a legibility/controllability console.

Anti-circularity protocol (the critics flagged tautology as the #1 risk)
------------------------------------------------------------------------
The single biggest way to fake this result is to build the direction and then
score the same prompts on it. We avoid that with a strict split + an honest
baseline + a null:

1. DISJOINT split. The axis's 40 contrast pairs are split into a 28-pair
   EXTRACTION set and a 12-pair held-out PROBE set (fixed seed). The CAA vector
   is built ONLY from the extraction set; the prompt shift is measured ONLY on
   held-out POS prompts the vector never saw.
2. LAYER by extraction-set separation only. The injection layer is chosen by
   Cohen's-d pos/neg separation on the EXTRACTION set (steering/extract.py), not
   by anything computed on the probe set.
3. NEUTRAL baseline. The prompt shift is measured RELATIVE to axis-agnostic
   neutral instructions, so we credit the prompt only with the *displacement it
   adds beyond a content-free instruction*, not the model's baseline position.
4. LATENT reference = ||v||. The honest "how far latent reaches" scalar is the
   magnitude of the CAA vector at the chosen layer (its projection on its own
   unit direction is exactly ||v||).
5. NULL. The strongest prompt's displacement must clear the p95 of projecting
   that same displacement onto random unit directions (metrics.random_null_baseline).

facade_ratio = strongest_prompt_shift / ||v||  (signed).
EXPLORATORY read (thresholds NOT frozen): a facade gap looks real when
facade_ratio > 0 (prompt pushes the right way), well below 1 (prompt falls short
of latent), AND the strongest prompt clears the null. We report the numbers; we
do NOT hard-code a frozen verdict.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
from collections import OrderedDict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

# Make the src-layout package importable when run as a plain script.
_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))

from cognitive_console.activations.provider import HFActivationProvider
from cognitive_console.steering.extract import extract_caa
from cognitive_console.metrics import project_scalar, random_null_baseline
from cognitive_console.analysis.routing import (
    RoutingInputs,
    RoutingThresholds,
    decide_route,
)
from cognitive_console.config import config_hash
from cognitive_console.registry import ExperimentRecord, ExperimentRegistry
from cognitive_console.lineage import git_commit, new_experiment_id, utcnow
from cognitive_console.manifest import ArtifactManifest, write_manifest

DEFAULT_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
DEFAULT_AXES = ["deliberation", "skepticism", "uncertainty_awareness", "focus"]
DATA_ROOT = _REPO / "data"
PAIRS_DIR = DATA_ROOT / "contrast_pairs"
NEUTRAL_FILE = DATA_ROOT / "neutral_prompts.jsonl"


# --------------------------------------------------------------------------- #
# Data loading + hashing
# --------------------------------------------------------------------------- #
def _read_jsonl(path: Path) -> List[dict]:
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_str(s: str) -> str:
    return "sha256:" + hashlib.sha256(s.encode("utf-8")).hexdigest()


@dataclass
class AxisPairs:
    axis: str
    pos: "OrderedDict[str, str]"  # pair_id -> pos text
    neg: "OrderedDict[str, str]"  # pair_id -> neg text
    file_hash: str


def load_axis_pairs(axis: str) -> AxisPairs:
    path = PAIRS_DIR / f"{axis}.jsonl"
    rows = _read_jsonl(path)
    pos: "OrderedDict[str, str]" = OrderedDict()
    neg: "OrderedDict[str, str]" = OrderedDict()
    for r in rows:
        pid = r["pair_id"]
        if r["polarity"] == "pos":
            pos[pid] = r["text"]
        elif r["polarity"] == "neg":
            neg[pid] = r["text"]
    common = [p for p in pos if p in neg]
    pos = OrderedDict((p, pos[p]) for p in common)
    neg = OrderedDict((p, neg[p]) for p in common)
    return AxisPairs(axis=axis, pos=pos, neg=neg, file_hash=_sha256_file(path))


def load_neutral_prompts() -> List[str]:
    return [r["text"] for r in _read_jsonl(NEUTRAL_FILE)]


# --------------------------------------------------------------------------- #
# Split
# --------------------------------------------------------------------------- #
@dataclass
class Split:
    extraction_ids: List[str]
    probe_ids: List[str]

    def hash(self) -> str:
        payload = json.dumps(
            {"extraction": self.extraction_ids, "probe": self.probe_ids},
            sort_keys=True,
        )
        return _sha256_str(payload)


def make_split(pair_ids: List[str], n_extraction: int, seed: int) -> Split:
    """Disjoint extraction/probe split with a fixed, per-axis-stable seed."""
    ids = sorted(pair_ids)
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(ids))
    shuffled = [ids[i] for i in order]
    extraction = sorted(shuffled[:n_extraction])
    probe = sorted(shuffled[n_extraction:])
    assert not (set(extraction) & set(probe)), "extraction/probe leakage!"
    return Split(extraction_ids=extraction, probe_ids=probe)


# --------------------------------------------------------------------------- #
# Per-axis analysis
# --------------------------------------------------------------------------- #
@dataclass
class AxisResult:
    axis: str
    chosen_layer: int
    vector_norm: float                 # ||v||, latent reference (how far latent reaches)
    neutral_proj: float                # mean neutral projection on û
    strongest_prompt_shift: float      # max over held-out POS of (proj - neutral_proj)
    strongest_prompt_id: str
    mean_prompt_shift: float           # mean over held-out POS
    facade_ratio: float                # strongest_prompt_shift / ||v|| (signed)
    mean_facade_ratio: float           # mean_prompt_shift / ||v||
    above_null: bool                   # |strongest shift| > null p95
    null_p95: float
    null_mean: float
    signal_z: float                    # (|shift| - null_mean)/null_std
    facade_gap_positive: bool          # 0 < facade_ratio
    facade_below_latent: bool          # facade_ratio < 1
    c1_signal: bool                    # positive AND below latent AND above null
    n_extraction: int
    n_probe: int
    extraction_separation: float       # Cohen's d at chosen layer (extraction set)
    per_layer_separation: Dict[str, float]
    extraction_ids: List[str]
    probe_ids: List[str]
    split_hash: str
    file_hash: str

    def to_row(self) -> Dict[str, object]:
        return asdict(self)


def analyze_axis(
    provider: HFActivationProvider,
    axis: str,
    scan_layers: List[int],
    n_extraction: int,
    seed: int,
    n_null: int,
) -> AxisResult:
    pairs = load_axis_pairs(axis)
    pair_ids = list(pairs.pos.keys())
    split = make_split(pair_ids, n_extraction=n_extraction, seed=seed)

    ext_pos = [pairs.pos[p] for p in split.extraction_ids]
    ext_neg = [pairs.neg[p] for p in split.extraction_ids]

    # Step 2: CAA extraction + layer scan on the EXTRACTION set only.
    caa = extract_caa(provider, axis, ext_pos, ext_neg, layers=scan_layers)
    layer = caa.layer
    v = np.asarray(caa.vector, dtype=np.float64)
    unit = np.asarray(caa.direction, dtype=np.float64)
    v_norm = float(np.linalg.norm(v))

    # Step 3: neutral baseline projection on û at the chosen layer.
    neutral_texts = load_neutral_prompts()
    neutral_acts = provider.get_activations(neutral_texts, layer)
    neutral_projs = np.array(
        [project_scalar(a, unit) for a in neutral_acts], dtype=np.float64
    )
    neutral_proj = float(neutral_projs.mean())

    # Step 5: prompt shift on HELD-OUT POS prompts (never seen by extraction).
    probe_pos_texts = [pairs.pos[p] for p in split.probe_ids]
    probe_acts = provider.get_activations(probe_pos_texts, layer)
    shifts = np.array(
        [project_scalar(a, unit) - neutral_proj for a in probe_acts], dtype=np.float64
    )
    strongest_idx = int(np.argmax(shifts))
    strongest_shift = float(shifts[strongest_idx])
    strongest_id = split.probe_ids[strongest_idx]
    mean_shift = float(shifts.mean())

    # Step 6: facade_ratio (signed) + random-direction null on the displacement.
    facade_ratio = strongest_shift / v_norm if v_norm > 1e-12 else float("nan")
    mean_facade_ratio = mean_shift / v_norm if v_norm > 1e-12 else float("nan")

    strongest_act = np.asarray(probe_acts[strongest_idx], dtype=np.float64)
    neutral_mean_act = np.asarray(neutral_acts, dtype=np.float64).mean(axis=0)
    displacement = strongest_act - neutral_mean_act  # what the prompt actually moved
    null = random_null_baseline(displacement, n_samples=n_null, seed=seed)
    null_p95 = float(np.percentile(null, 95))
    null_mean = float(null.mean())
    null_std = float(null.std())
    above_null = bool(abs(strongest_shift) > null_p95)
    if null_std > 1e-12:
        signal_z = float((abs(strongest_shift) - null_mean) / null_std)
    else:
        signal_z = float("nan")

    facade_positive = facade_ratio > 0
    facade_below = facade_ratio < 1.0
    c1_signal = bool(facade_positive and facade_below and above_null)

    per_layer_sep = {
        str(ell): float(d.separation) for ell, d in sorted(caa.per_layer.items())
    }

    return AxisResult(
        axis=axis,
        chosen_layer=int(layer),
        vector_norm=v_norm,
        neutral_proj=neutral_proj,
        strongest_prompt_shift=strongest_shift,
        strongest_prompt_id=strongest_id,
        mean_prompt_shift=mean_shift,
        facade_ratio=float(facade_ratio),
        mean_facade_ratio=float(mean_facade_ratio),
        above_null=above_null,
        null_p95=null_p95,
        null_mean=null_mean,
        signal_z=signal_z,
        facade_gap_positive=bool(facade_positive),
        facade_below_latent=bool(facade_below),
        c1_signal=c1_signal,
        n_extraction=len(split.extraction_ids),
        n_probe=len(split.probe_ids),
        extraction_separation=float(caa.per_layer[layer].separation),
        per_layer_separation=per_layer_sep,
        extraction_ids=split.extraction_ids,
        probe_ids=split.probe_ids,
        split_hash=split.hash(),
        file_hash=pairs.file_hash,
    )


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def _peak_rss_mb() -> Optional[float]:
    # psutil exposes the Windows peak working set (peak_wset) and RSS elsewhere.
    try:
        import psutil

        mi = psutil.Process().memory_info()
        peak = getattr(mi, "peak_wset", None)
        if peak:
            return peak / (1024.0 * 1024.0)
        return mi.rss / (1024.0 * 1024.0)
    except Exception:
        pass
    try:
        import resource  # POSIX only

        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    except Exception:
        return None


def run(
    model: str,
    axes: List[str],
    scan_step: int,
    n_extraction: int,
    seed: int,
    n_null: int,
    out_dir: Path,
    max_scan_layers: Optional[int] = None,
) -> Dict[str, object]:
    t0 = time.time()
    cache_dir = out_dir / "activations" / "cache"
    provider = HFActivationProvider(
        model, device="cpu", dtype="float32", cache_dir=str(cache_dir)
    )

    # hidden_states index range is 0..num_hidden_layers inclusive. Scan every
    # `scan_step`-th layer, skipping the embedding layer (0) and staying within
    # the transformer blocks where steering vectors typically live.
    all_layers = provider.available_layers()  # loads the model once
    top = all_layers[-1]
    scan_layers = list(range(scan_step, top + 1, scan_step))
    if max_scan_layers is not None and len(scan_layers) > max_scan_layers:
        # Keep a spread across depth if we must cap the scan.
        idx = np.linspace(0, len(scan_layers) - 1, max_scan_layers).round().astype(int)
        scan_layers = sorted({scan_layers[i] for i in idx})
    print(f"[c1] model={model} hidden_dim={provider.hidden_dim} "
          f"layers=0..{top} scan={scan_layers}", flush=True)

    results: List[AxisResult] = []
    for axis in axes:
        ta = time.time()
        res = analyze_axis(
            provider, axis, scan_layers, n_extraction, seed, n_null
        )
        results.append(res)
        print(
            f"[c1] axis={axis:<24} layer={res.chosen_layer:>3} "
            f"||v||={res.vector_norm:8.3f} strongest_shift={res.strongest_prompt_shift:8.3f} "
            f"facade_ratio={res.facade_ratio:6.3f} above_null={res.above_null} "
            f"c1={res.c1_signal}  ({time.time()-ta:.1f}s)",
            flush=True,
        )

    # ---- EXPLORATORY Go/No-Go routing (thresholds NOT frozen) --------------
    n_axes = len(results)
    support_fraction = sum(r.c1_signal for r in results) / n_axes if n_axes else 0.0
    finite_ratios = [r.facade_ratio for r in results if np.isfinite(r.facade_ratio)]
    max_ratio = max(finite_ratios) if finite_ratios else float("nan")
    routing_inputs = RoutingInputs(
        facade_support_fraction=support_fraction,
        max_facade_ratio_observed=max_ratio if np.isfinite(max_ratio) else 0.0,
        prompt_above_null=all(r.above_null for r in results) if results else False,
        # C1-only pilot: the downstream AC4/5/8 signals are NOT measured here.
        # Set to False and label the routing EXPLORATORY (see 'routing_caveat').
        blind_eval_above_chance=False,
        transfer_survives=False,
        composition_survives=False,
        behavioral_ceiling_exists=False,
        style_only_everywhere=False,
    )
    routing = decide_route(routing_inputs, RoutingThresholds())

    wall_clock = time.time() - t0
    peak_rss = _peak_rss_mb()

    payload: Dict[str, object] = {
        "kind": "c1_facade_pilot",
        "type": "EXPLORATORY",
        "valid_for_paper": False,
        "protocol_frozen": False,
        "model": model,
        "seed": seed,
        "n_null": n_null,
        "n_extraction_pairs": n_extraction,
        "scan_layers": scan_layers,
        "hidden_dim": int(provider.hidden_dim),
        "generated_at": utcnow(),
        "wall_clock_seconds": round(wall_clock, 2),
        "peak_rss_mb": round(peak_rss, 1) if peak_rss else None,
        "platform": platform.platform(),
        "axes": [r.to_row() for r in results],
        "aggregate": {
            "n_axes": n_axes,
            "facade_support_fraction": support_fraction,
            "max_facade_ratio_observed": max_ratio,
            "prompt_above_null_all": bool(all(r.above_null for r in results)),
        },
        "routing_EXPLORATORY": routing.to_dict(),
        "routing_caveat": (
            "EXPLORATORY only. This C1 pilot measures the semantic-facade gap; it "
            "does NOT measure blind-eval (AC4), transfer/composition (AC5), or the "
            "behavioral prompt-search ceiling (AC8). Those routing gates are set "
            "False here by construction, so the route is NOT a real Go/No-Go — the "
            "meaningful signal is the per-axis facade_ratio + above_null."
        ),
    }
    return payload


def _write_results(payload: Dict[str, object], out_dir: Path, seed: int) -> Tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "c1_facade_results.json"
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)

    lines: List[str] = []
    lines.append("# C1 Semantic-Facade Pilot — EXPLORATORY (protocol NOT frozen)\n")
    lines.append(f"- model: `{payload['model']}`  (CPU, float32)")
    lines.append(f"- generated: {payload['generated_at']}")
    lines.append(f"- seed: {seed}   n_null: {payload['n_null']}   "
                 f"hidden_dim: {payload['hidden_dim']}")
    lines.append(f"- scan layers: {payload['scan_layers']}")
    lines.append(f"- wall-clock: {payload['wall_clock_seconds']}s   "
                 f"peak RSS: {payload['peak_rss_mb']} MB")
    lines.append(f"- valid_for_paper: **{payload['valid_for_paper']}**\n")
    lines.append("## Per-axis facade gap\n")
    lines.append(
        "| axis | layer | \\|\\|v\\|\\| | neutral_proj | strongest_shift | "
        "facade_ratio | mean_ratio | above_null | signal_z | C1 signal | ext/probe |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in payload["axes"]:  # type: ignore[index]
        lines.append(
            f"| {r['axis']} | {r['chosen_layer']} | {r['vector_norm']:.2f} | "
            f"{r['neutral_proj']:.2f} | {r['strongest_prompt_shift']:.2f} | "
            f"{r['facade_ratio']:.3f} | {r['mean_facade_ratio']:.3f} | "
            f"{r['above_null']} | {r['signal_z']:.2f} | "
            f"{'YES' if r['c1_signal'] else 'no'} | "
            f"{r['n_extraction']}/{r['n_probe']} |"
        )
    agg = payload["aggregate"]  # type: ignore[index]
    lines.append("")
    lines.append("## Aggregate\n")
    lines.append(f"- axes with a C1 signal: "
                 f"{agg['facade_support_fraction']*100:.0f}% "
                 f"({int(round(agg['facade_support_fraction']*agg['n_axes']))}/{agg['n_axes']})")
    lines.append(f"- worst (max) facade_ratio: {agg['max_facade_ratio_observed']:.3f}")
    lines.append(f"- all axes above null: {agg['prompt_above_null_all']}")
    lines.append("")
    lines.append("## Routing (EXPLORATORY — not a real Go/No-Go)\n")
    lines.append(f"- route: `{payload['routing_EXPLORATORY']['route']}`  "  # type: ignore[index]
                 f"verdict: `{payload['routing_EXPLORATORY']['verdict']}`")
    lines.append(f"- {payload['routing_caveat']}")
    lines.append("")
    lines.append("## How to read facade_ratio\n")
    lines.append(
        "- `facade_ratio = strongest_prompt_shift / ||v||` (signed). ~1 => the best "
        "readable prompt reaches as far as the latent vector (NO facade). Near 0 (but "
        "> 0 and above null) => strong facade: the prompt points the right way but "
        "falls far short of the latent reach. < 0 => the best prompt pushes the WRONG "
        "way along the axis (evidence against a clean prompt->latent map, not a facade)."
    )
    summary_path = out_dir / "c1_facade_summary.md"
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return json_path, summary_path


def _register(payload: Dict[str, object], out_dir: Path, json_path: Path, seed: int) -> str:
    """Register the run in a RUN-LOCAL experiment registry (results/…).

    NOTE (judgment call): the canonical ledger lives under docs/ledgers/, but this
    task is scoped to NOT modify docs/. We therefore write the same schema via the
    same ExperimentRegistry writer into the results directory so the run is still
    registered + reconstructable; the Manager can fold it into the canonical ledger.
    """
    reg_path = out_dir / "experiment-registry.yaml"
    registry = ExperimentRegistry(str(reg_path))

    axis_rows = payload["axes"]  # type: ignore[index]
    cfg = {
        "kind": "c1_facade_pilot",
        "model": payload["model"],
        "axes": [r["axis"] for r in axis_rows],
        "scan_layers": payload["scan_layers"],
        "seed": seed,
        "n_null": payload["n_null"],
        "n_extraction": payload["n_extraction_pairs"],
    }
    cfg_hash = config_hash(cfg)
    data_hashes = {
        r["axis"]: {"file": r["file_hash"], "split": r["split_hash"]} for r in axis_rows
    }
    summary_metrics = {
        r["axis"]: {
            "chosen_layer": r["chosen_layer"],
            "vector_norm": r["vector_norm"],
            "strongest_prompt_shift": r["strongest_prompt_shift"],
            "facade_ratio": r["facade_ratio"],
            "above_null": r["above_null"],
            "c1_signal": r["c1_signal"],
        }
        for r in axis_rows
    }
    summary_metrics["_aggregate"] = payload["aggregate"]

    exp_id = new_experiment_id(registry, "c1-facade", cfg_hash)
    record = ExperimentRecord(
        experiment_id=exp_id,
        hypothesis_id="H1",
        claim_ids=["C1"],
        type="exploratory",
        status="done",
        code_commit=git_commit(str(_REPO)),
        data_hash=_sha256_str(json.dumps(data_hashes, sort_keys=True)),
        config_hash=cfg_hash,
        model=str(payload["model"]),
        dataset="data/contrast_pairs/*.jsonl (28/12 disjoint split)",
        seed=seed,
        hardware="cpu-local-float32",
        started_at=str(payload["generated_at"]),
        ended_at=utcnow(),
        exit_code=0,
        summary_metrics=summary_metrics,
        artifacts=[str(json_path.relative_to(_REPO)).replace("\\", "/")],
        valid_for_paper=False,
        validation_notes=(
            "EXPLORATORY C1 facade pilot on Qwen2.5-0.5B (CPU). Protocol NOT frozen. "
            "Registered in a run-local registry (docs/ untouched by task scope)."
        ),
    )
    registry.append(record)

    manifest = ArtifactManifest(
        artifact_id="c1-facade-pilot-table",
        supports_claims=["C1"],
        source_experiments=[exp_id],
        aggregation_script="scripts/run_c1_facade.py",
        aggregation_commit=git_commit(str(_REPO)),
        output_file=str(json_path.relative_to(_REPO)).replace("\\", "/"),
        raw_data_hash=_sha256_str(json.dumps(data_hashes, sort_keys=True)),
        last_verified=utcnow(),
        verdict="pending",
    )
    write_manifest(str(out_dir / "c1_facade_table.manifest.yaml"), manifest)
    return exp_id


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="C1 semantic-facade pilot (CPU, exploratory)")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--axes", nargs="*", default=DEFAULT_AXES)
    ap.add_argument("--scan-step", type=int, default=2, help="scan every Nth layer")
    ap.add_argument("--max-scan-layers", type=int, default=None,
                    help="cap the number of scanned layers (spread across depth)")
    ap.add_argument("--n-extraction", type=int, default=28)
    ap.add_argument("--seed", type=int, default=20260723)
    ap.add_argument("--n-null", type=int, default=2000)
    ap.add_argument(
        "--out-dir",
        default=str(_REPO / "results" / "c1_facade_pilot_2026-07-23"),
    )
    args = ap.parse_args(argv)

    out_dir = Path(args.out_dir)
    payload = run(
        model=args.model,
        axes=args.axes,
        scan_step=args.scan_step,
        n_extraction=args.n_extraction,
        seed=args.seed,
        n_null=args.n_null,
        out_dir=out_dir,
        max_scan_layers=args.max_scan_layers,
    )
    json_path, summary_path = _write_results(payload, out_dir, args.seed)
    exp_id = _register(payload, out_dir, json_path, args.seed)
    print(f"[c1] wrote {json_path}")
    print(f"[c1] wrote {summary_path}")
    print(f"[c1] registered experiment_id={exp_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
