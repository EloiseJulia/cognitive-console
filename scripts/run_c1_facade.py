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
score the same-distribution prompts on it. We avoid that with a strict split, a
SEPARATELY-authored strongest-prompt set, an honest baseline, and a null:

1. DISJOINT split. The axis's 40 contrast pairs are split into a 28-pair
   EXTRACTION set and a 12-pair held-out PROBE set (fixed seed). The CAA vector
   is built ONLY from the extraction set.
2. LAYER by extraction-set separation only. The injection layer is chosen by
   Cohen's-d pos/neg separation on the EXTRACTION set (steering/extract.py), not
   by anything computed on the strongest-prompt set.
3. SEPARATE strongest-prompt set (FIX 2). The prompt reach is measured on
   naturally-authored, forceful user instructions in data/strongest_prompts/,
   which are DIFFERENT IN KIND from the terse contrast-pair templates and are NOT
   drawn from the CAA extraction distribution. The prior pilot reused held-out
   POS contrast-pair texts, which trivially project onto û ~= full ||v||
   (pseudo-circularity -> a manufactured overshoot). A leakage guard
   (tests/test_leakage.py) enforces the non-overlap.
4. NEUTRAL baseline. Every prompt reach is measured RELATIVE to axis-agnostic
   neutral instructions, so we credit the prompt only with the *displacement it
   adds beyond a content-free instruction*.
5. CONSISTENT estimators from the SAME neutral origin (CORRECTED, D-0016).
   pole_reach = <mean(EXTRACTION-POS act) − neutral_mean_act, û> is the model's
   ACHIEVABLE positive-pole displacement, measured from the SAME neutral origin
   as the prompt and taking NO steering coefficient alpha. prompt_reach =
   <mean(strong-prompt act) − neutral_mean_act, û>. This replaces the earlier
   ||v|| denominator (neg-pole→pos-pole displacement implicitly at alpha=1),
   which mixed origins and baked in an arbitrary alpha (audit BLOCKER-1/2). The
   old ||v||-based ratio is retained per-axis, clearly marked SUPERSEDED.
6. NULL. above-null is DEMOTED to a labelled sanity field (trivial in high-dim,
   audit MAJOR-3); extraction_success requires the positive pole itself to clear
   the random-direction null from the neutral origin.

facade_ratio = prompt_reach / pole_reach  (same-origin, scale-free, alpha-free) — HEADLINE.
A bootstrap 95% CI (resampling the strong-prompt set) and a leave-one-neutral-out
band are reported. EXPLORATORY read (thresholds NOT frozen): a facade holds when
0 < facade_ratio and the CI upper bound is meaningfully < 1. We report the
numbers; we do NOT hard-code a frozen verdict.
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
from cognitive_console.steering.extract import (
    extract_caa,
    layer_diagnostics,
    mean_difference_vector,
    min_layer_for_depth,
    select_nondegenerate_layer,
)
from cognitive_console.metrics import project_scalar, random_null_baseline, same_origin_facade
from cognitive_console.analysis.routing import (
    RoutingInputs,
    RoutingThresholds,
    decide_route,
)
from cognitive_console.config import config_hash
from cognitive_console.registry import ExperimentRecord, ExperimentRegistry
from cognitive_console.lineage import git_commit, new_experiment_id, utcnow
from cognitive_console.manifest import ArtifactManifest, write_manifest

DEFAULT_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
DEFAULT_AXES = ["deliberation", "skepticism", "uncertainty_awareness", "focus"]
DATA_ROOT = _REPO / "data"
PAIRS_DIR = DATA_ROOT / "contrast_pairs"
STRONGEST_DIR = DATA_ROOT / "strongest_prompts"
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


@dataclass
class StrongestPrompts:
    axis: str
    ids: List[str]
    texts: List[str]
    file_hash: str


def load_strongest_prompts(axis: str) -> StrongestPrompts:
    """Load the SEPARATELY-authored strongest human-style instructions for an axis.

    These are deliberately DIFFERENT IN KIND from the terse contrast-pair
    templates (they are forceful, natural user instructions, not first-person
    model statements) and are NOT drawn from the CAA extraction distribution, so
    projecting them onto the axis direction is NOT pseudo-circular. A leakage
    guard (tests/test_leakage.py) enforces the non-overlap with contrast pairs.
    """
    path = STRONGEST_DIR / f"{axis}.jsonl"
    rows = _read_jsonl(path)
    ids = [r["prompt_id"] for r in rows]
    texts = [r["text"] for r in rows]
    return StrongestPrompts(
        axis=axis, ids=ids, texts=texts, file_hash=_sha256_file(path)
    )


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
    stable_layer_found: bool           # a non-degenerate layer exists (D-0019)
    unstable_reason: str               # "" if stable; else why no layer qualifies
    min_layer_scanned: int             # depth-floor cutoff for the scan
    neutral_proj: float                # mean neutral projection on û = SHARED ORIGIN
    # --- PRIMARY (corrected, same-origin, scale-free, alpha-free -- see D-0016) --
    prompt_reach: float                # <mean(strong) - neutral_mean, û>
    pole_reach: float                  # <mean(EXTRACTION-POS) - neutral_mean, û>:
                                       # the model's ACHIEVABLE positive-pole
                                       # displacement from the SAME neutral origin
    facade_ratio: float                # prompt_reach / pole_reach  -- HEADLINE
    facade_ratio_ci_lo: float          # bootstrap 95% CI over strong-prompt set
    facade_ratio_ci_hi: float
    facade_ratio_ci_level: float
    facade_ratio_loo_min: float        # leave-one-neutral-out band (neutral sensitivity)
    facade_ratio_loo_max: float
    facade_gap_holds_ci: bool          # CI upper bound < 1 (facade genuinely holds)
    extraction_success: bool           # positive pole is separated from neutral along
                                       # û above the random-direction null (metric is
                                       # only meaningful if the pole itself reaches)
    pole_null_p95: float               # random-direction null p95 on the pole displacement
    # --- ROBUSTNESS (D-0019): top-k non-degenerate layers + multi-seed CI --------
    top_k_layers: List[Dict[str, object]]   # per non-degenerate candidate layer:
                                            # layer, separation, pole_reach,
                                            # facade_ratio, ci_lo/hi, extraction_success
    seed_robustness: List[Dict[str, object]]  # facade_ratio + CI at chosen layer
                                              # under multiple RNG seeds
    seed_stable: bool                  # all seeds agree on facade_gap_holds_ci
    # --- Clearly-labelled UPPER BOUND (single strongest prompt), same-origin ----
    prompt_reach_max: float            # MAX same-origin reach over the strong set
    strongest_prompt_id: str
    facade_ratio_max: float            # prompt_reach_max / pole_reach (upper bound)
    # --- SUPERSEDED old ||v||-based ratio (denominator artifact; kept for compare)
    vector_norm_SUPERSEDED: float      # ||v|| = ||mean(pos)-mean(neg)|| (neg->pos pole)
    facade_ratio_vnorm_mean_SUPERSEDED: float   # old headline = prompt_reach / ||v||
    facade_ratio_vnorm_max_SUPERSEDED: float
    # --- Labelled SANITY fields (NOT headline; trivial in high-dim, audit MAJOR-3)
    sanity_above_null: bool            # |prompt_reach| > null p95 (mean displacement)
    sanity_signal_z: float             # (|prompt_reach| - null_mean)/null_std
    sanity_null_p95: float
    # --- EXPLORATORY read (thresholds NOT frozen; c1_signal is data-derived) ----
    c1_signal: bool                    # stable AND extraction_success AND ratio>0 AND CI upper<1
    n_strongest: int
    strongest_file_hash: str
    n_extraction: int
    n_probe: int
    extraction_separation: float       # Cohen's d at chosen layer (extraction set)
    per_layer_separation: Dict[str, float]
    per_layer_pole_reach: Dict[str, float]
    per_layer_pole_null_p95: Dict[str, float]
    extraction_ids: List[str]
    probe_ids: List[str]
    split_hash: str
    file_hash: str

    def to_row(self) -> Dict[str, object]:
        return asdict(self)


def _unit_direction(pos_acts: np.ndarray, neg_acts: np.ndarray) -> Tuple[np.ndarray, float]:
    """Return (unit CAA direction, ||v||) for one layer's extraction acts."""
    v = mean_difference_vector(pos_acts, neg_acts)
    norm = float(np.linalg.norm(v))
    unit = v / norm if norm > 1e-12 else np.zeros_like(v)
    return unit, norm


def analyze_axis(
    provider: HFActivationProvider,
    axis: str,
    scan_layers: List[int],
    n_extraction: int,
    seed: int,
    n_null: int,
    top_layer: int,
    min_depth_frac: float = 0.2,
    top_k: int = 3,
    seeds: Optional[List[int]] = None,
    n_boot: int = 2000,
    ci_level: float = 0.95,
) -> AxisResult:
    if seeds is None:
        seeds = [seed, seed + 1, seed + 2]
    pairs = load_axis_pairs(axis)
    pair_ids = list(pairs.pos.keys())
    split = make_split(pair_ids, n_extraction=n_extraction, seed=seed)

    ext_pos = [pairs.pos[p] for p in split.extraction_ids]
    ext_neg = [pairs.neg[p] for p in split.extraction_ids]
    neutral_texts = load_neutral_prompts()
    strongest = load_strongest_prompts(axis)

    # ---- Full per-layer scan (D-0019): the layer is chosen on the EXTRACTION set
    # ---- only, but now by a NON-DEGENERATE rule, not bare Cohen's-d. For every
    # ---- scan layer we compute (a) pos/neg separation, (b) the unit direction û,
    # ---- and (c) pole_reach = <mean(pos) - mean(neutral), û> plus its random-null
    # ---- p95, so degenerate shallow/lexical layers (high separation but pole not
    # ---- separated from neutral along û) are excluded from selection.
    per_layer_sep: Dict[int, float] = {}
    per_layer_pole_reach: Dict[int, float] = {}
    per_layer_pole_null: Dict[int, float] = {}
    per_layer_unit: Dict[int, np.ndarray] = {}
    per_layer_vnorm: Dict[int, float] = {}
    for ell in scan_layers:
        pos_acts = provider.get_activations(ext_pos, ell).astype(np.float64)
        neg_acts = provider.get_activations(ext_neg, ell).astype(np.float64)
        diag = layer_diagnostics(pos_acts, neg_acts, ell)
        unit, vnorm = _unit_direction(pos_acts, neg_acts)
        neutral_acts = provider.get_activations(neutral_texts, ell).astype(np.float64)
        neutral_mean_act = neutral_acts.mean(axis=0)
        pole_disp = pos_acts.mean(axis=0) - neutral_mean_act
        pole_reach_ell = float(np.dot(pole_disp, unit)) if vnorm > 1e-12 else 0.0
        null_pole = random_null_baseline(pole_disp, n_samples=n_null, seed=seed)
        per_layer_sep[ell] = float(diag.separation)
        per_layer_pole_reach[ell] = pole_reach_ell
        per_layer_pole_null[ell] = float(np.percentile(null_pole, 95))
        per_layer_unit[ell] = unit
        per_layer_vnorm[ell] = vnorm

    min_layer = min_layer_for_depth(top_layer, min_depth_frac)
    sel = select_nondegenerate_layer(
        per_layer_sep, per_layer_pole_reach, per_layer_pole_null,
        min_layer=min_layer, top_k=top_k,
    )
    stable = sel.has_stable_layer

    if stable:
        layer = int(sel.chosen)
        unstable_reason = ""
    else:
        # HONEST fallback: no non-degenerate layer exists. We still report numbers
        # at the max-separation layer (so the failure is inspectable) but flag the
        # axis UNSTABLE and force c1_signal False — we do NOT p-hack a facade.
        layer = max(scan_layers, key=lambda e: (per_layer_sep[e], -e))
        best_cand = sel.candidates[layer]
        unstable_reason = (
            f"no non-degenerate layer (min_layer={min_layer}); "
            f"max-sep layer {layer}: {best_cand.reject_reason or 'degenerate'}"
        )

    unit = per_layer_unit[layer]
    v_norm = per_layer_vnorm[layer]

    # ---- Facade metric at a given layer under a given RNG seed (all cached acts).
    def _facade_at(ell: int, seed_: int):
        u = per_layer_unit[ell]
        neutral_acts = provider.get_activations(neutral_texts, ell).astype(np.float64)
        pos_acts = provider.get_activations(ext_pos, ell).astype(np.float64)
        strong_acts = provider.get_activations(strongest.texts, ell).astype(np.float64)
        neutral_projs = np.array([project_scalar(a, u) for a in neutral_acts])
        pos_projs = np.array([project_scalar(a, u) for a in pos_acts])
        strong_projs = np.array([project_scalar(a, u) for a in strong_acts])
        so = same_origin_facade(
            strong_projs=strong_projs, pos_projs=pos_projs, neutral_projs=neutral_projs,
            n_boot=n_boot, seed=seed_, ci_level=ci_level,
        )
        return so, neutral_projs, pos_projs, strong_projs, strong_acts

    # PRIMARY (chosen layer, primary seed).
    so, neutral_projs, pos_projs, strong_projs, strong_acts = _facade_at(layer, seeds[0])
    neutral_proj = float(neutral_projs.mean())
    neutral_mean_act = provider.get_activations(neutral_texts, layer).astype(np.float64).mean(axis=0)
    prompt_reach = so.prompt_reach
    pole_reach = so.pole_reach

    # ROBUSTNESS 1 — multi-seed CI at the chosen layer (seed-stability of the CI).
    seed_rows: List[Dict[str, object]] = []
    for s in seeds:
        so_s, *_ = _facade_at(layer, s)
        seed_rows.append({
            "seed": int(s),
            "facade_ratio": float(so_s.facade_ratio),
            "ci_lo": float(so_s.ci_lo),
            "ci_hi": float(so_s.ci_hi),
            "ci_upper_below_1": bool(so_s.ci_hi < 1.0),
        })
    seed_stable = len({r["ci_upper_below_1"] for r in seed_rows}) == 1

    # ROBUSTNESS 2 — facade_ratio across the top-k non-degenerate candidate layers
    # (primary seed). Empty when the axis is unstable (no candidate qualifies).
    top_k_rows: List[Dict[str, object]] = []
    for ell in sel.ranked:
        so_k, *_ = _facade_at(ell, seeds[0])
        cand = sel.candidates[ell]
        top_k_rows.append({
            "layer": int(ell),
            "separation": float(cand.separation),
            "pole_reach": float(cand.pole_reach),
            "facade_ratio": float(so_k.facade_ratio),
            "ci_lo": float(so_k.ci_lo),
            "ci_hi": float(so_k.ci_hi),
            "ci_upper_below_1": bool(so_k.ci_hi < 1.0),
            "extraction_success": True,  # non-degenerate by construction
        })

    # UPPER BOUND (clearly labelled, NOT the headline): the single strongest prompt.
    reaches = strong_projs - neutral_proj
    max_idx = int(np.argmax(reaches))
    prompt_reach_max = float(reaches[max_idx])
    strongest_id = strongest.ids[max_idx]
    facade_ratio_max = (
        prompt_reach_max / pole_reach if abs(pole_reach) > 1e-12 else float("nan")
    )

    # SUPERSEDED old ||v||-based ratios, retained for a direct comparison only.
    facade_ratio_vnorm_mean = prompt_reach / v_norm if v_norm > 1e-12 else float("nan")
    facade_ratio_vnorm_max = prompt_reach_max / v_norm if v_norm > 1e-12 else float("nan")

    # SANITY (labelled, NOT headline): does the prompt displacement clear a random
    # direction null? Trivial in high-dim (audit MAJOR-3) -> demoted from headline.
    mean_displacement = strong_acts.mean(axis=0) - neutral_mean_act
    null_mean_dist = random_null_baseline(mean_displacement, n_samples=n_null, seed=seed)
    sanity_null_p95 = float(np.percentile(null_mean_dist, 95))
    nm_mean, nm_std = float(null_mean_dist.mean()), float(null_mean_dist.std())
    sanity_above_null = bool(abs(prompt_reach) > sanity_null_p95)
    sanity_signal_z = (
        float((abs(prompt_reach) - nm_mean) / nm_std) if nm_std > 1e-12 else float("nan")
    )

    # EXTRACTION-SUCCESS at the chosen layer (pole clears the null from neutral).
    pole_null_p95 = per_layer_pole_null[layer]
    extraction_success = bool(stable and pole_reach > 0.0 and abs(pole_reach) > pole_null_p95)

    # EXPLORATORY data-derived read (thresholds NOT frozen): a facade genuinely
    # holds only when a NON-DEGENERATE layer exists (stable), the pole is reachable
    # (extraction_success), the prompt points the RIGHT way (ratio > 0), and the
    # bootstrap CI upper bound is below 1.
    facade_gap_holds_ci = bool(so.ci_hi < 1.0)
    c1_signal = bool(
        stable and extraction_success and so.facade_ratio > 0.0 and facade_gap_holds_ci
    )

    per_layer_sep_out = {str(e): float(per_layer_sep[e]) for e in sorted(per_layer_sep)}
    per_layer_pole_out = {str(e): float(per_layer_pole_reach[e]) for e in sorted(per_layer_pole_reach)}
    per_layer_null_out = {str(e): float(per_layer_pole_null[e]) for e in sorted(per_layer_pole_null)}

    return AxisResult(
        axis=axis,
        chosen_layer=int(layer),
        stable_layer_found=bool(stable),
        unstable_reason=unstable_reason,
        min_layer_scanned=int(min_layer),
        neutral_proj=neutral_proj,
        prompt_reach=prompt_reach,
        pole_reach=pole_reach,
        facade_ratio=so.facade_ratio,
        facade_ratio_ci_lo=so.ci_lo,
        facade_ratio_ci_hi=so.ci_hi,
        facade_ratio_ci_level=so.ci_level,
        facade_ratio_loo_min=so.loo_min,
        facade_ratio_loo_max=so.loo_max,
        facade_gap_holds_ci=facade_gap_holds_ci,
        extraction_success=extraction_success,
        pole_null_p95=pole_null_p95,
        top_k_layers=top_k_rows,
        seed_robustness=seed_rows,
        seed_stable=bool(seed_stable),
        prompt_reach_max=prompt_reach_max,
        strongest_prompt_id=strongest_id,
        facade_ratio_max=float(facade_ratio_max),
        vector_norm_SUPERSEDED=v_norm,
        facade_ratio_vnorm_mean_SUPERSEDED=float(facade_ratio_vnorm_mean),
        facade_ratio_vnorm_max_SUPERSEDED=float(facade_ratio_vnorm_max),
        sanity_above_null=sanity_above_null,
        sanity_signal_z=sanity_signal_z,
        sanity_null_p95=sanity_null_p95,
        c1_signal=c1_signal,
        n_strongest=len(strongest.texts),
        strongest_file_hash=strongest.file_hash,
        n_extraction=len(split.extraction_ids),
        n_probe=len(split.probe_ids),
        extraction_separation=float(per_layer_sep[layer]),
        per_layer_separation=per_layer_sep_out,
        per_layer_pole_reach=per_layer_pole_out,
        per_layer_pole_null_p95=per_layer_null_out,
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


def _available_ram_mb() -> Optional[float]:
    try:
        import psutil

        return psutil.virtual_memory().available / (1024.0 * 1024.0)
    except Exception:
        return None


def start_ram_watchdog(floor_mb: float, poll_s: float = 0.5) -> threading.Event:
    """Hard-abort the process if system-available RAM drops below ``floor_mb``.

    The 1.5B float32 load materializes ~6-8 GB of weights. On this shared machine
    we must NEVER page into swap-thrash. A daemon thread polls psutil's
    system-available memory; if it dips below the floor it prints the exact RAM
    numbers and calls ``os._exit`` so the OS reclaims the partially-loaded weights
    immediately instead of thrashing. Returns a stop Event the caller sets once the
    memory-heavy phase (model load + forwards) is safely past its peak.
    """
    stop = threading.Event()

    def _watch() -> None:
        peak_used = 0.0
        while not stop.is_set():
            avail = _available_ram_mb()
            if avail is not None:
                peak = _peak_rss_mb() or 0.0
                peak_used = max(peak_used, peak)
                if avail < floor_mb:
                    sys.stderr.write(
                        "\n[c1][WATCHDOG] system-available RAM "
                        f"{avail:.0f} MB < floor {floor_mb:.0f} MB "
                        f"(peak process RSS {peak_used:.0f} MB). "
                        "Hard-aborting BEFORE swap-thrash — the 1.5B float32 load "
                        "does not fit in free physical RAM.\n"
                    )
                    sys.stderr.flush()
                    os._exit(75)
            stop.wait(poll_s)

    t = threading.Thread(target=_watch, name="ram-watchdog", daemon=True)
    t.start()
    return stop


def run(
    model: str,
    axes: List[str],
    scan_step: int,
    n_extraction: int,
    seed: int,
    n_null: int,
    out_dir: Path,
    max_scan_layers: Optional[int] = None,
    ram_floor_mb: float = 450.0,
    n_boot: int = 2000,
    ci_level: float = 0.95,
    min_depth_frac: float = 0.2,
    top_k: int = 3,
    seeds: Optional[List[int]] = None,
    device: str = "cpu",
    dtype: str = "float32",
    activation_provider: Optional[HFActivationProvider] = None,
) -> Dict[str, object]:
    t0 = time.time()
    if seeds is None:
        seeds = [seed, seed + 1, seed + 2]
    # Guard the whole memory-heavy phase (model load + all forwards). We only stop
    # the watchdog once every axis is analyzed and activations are cached/pooled.
    watchdog_stop = start_ram_watchdog(ram_floor_mb)
    avail0 = _available_ram_mb()
    if avail0 is not None:
        print(f"[c1] system-available RAM at start: {avail0:.0f} MB "
              f"(watchdog floor {ram_floor_mb:.0f} MB)", flush=True)
    cache_dir = out_dir / "activations" / "cache"
    # Honest wall-clock (audit MINOR-6): if the activation cache is already warm,
    # the measured wall-clock UNDER-reports the true full-compute cost. Record
    # whether the cache was cold so the registry can qualify the number.
    cache_was_cold = not (cache_dir.exists() and any(cache_dir.iterdir()))
    provider = activation_provider or HFActivationProvider(
        model, device=device, dtype=dtype, cache_dir=str(cache_dir)
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
            provider, axis, scan_layers, n_extraction, seed, n_null,
            top_layer=top, min_depth_frac=min_depth_frac, top_k=top_k, seeds=seeds,
            n_boot=n_boot, ci_level=ci_level,
        )
        results.append(res)
        stab = "stable" if res.stable_layer_found else "UNSTABLE"
        print(
            f"[c1] axis={axis:<24} layer={res.chosen_layer:>3}({stab}) "
            f"prompt_reach={res.prompt_reach:7.3f} pole_reach={res.pole_reach:7.3f} "
            f"ratio={res.facade_ratio:6.3f} CI=[{res.facade_ratio_ci_lo:.3f},{res.facade_ratio_ci_hi:.3f}] "
            f"extract_ok={res.extraction_success} seed_stable={res.seed_stable} "
            f"c1={res.c1_signal}  ({time.time()-ta:.1f}s)",
            flush=True,
        )

    # Peak memory pressure is behind us (weights loaded, all activations pooled).
    watchdog_stop.set()

    # ---- EXPLORATORY Go/No-Go routing (thresholds NOT frozen) --------------
    # Fed with the CORRECTED same-origin facade_ratio (see D-0016). facade_holds
    # per axis = extraction_success AND ratio>0 AND CI upper bound < 1.
    n_axes = len(results)
    support_fraction = sum(r.c1_signal for r in results) / n_axes if n_axes else 0.0
    finite_ratios = [
        r.facade_ratio for r in results if np.isfinite(r.facade_ratio)
    ]
    max_ratio = max(finite_ratios) if finite_ratios else float("nan")
    routing_inputs = RoutingInputs(
        facade_support_fraction=support_fraction,
        max_facade_ratio_observed=max_ratio if np.isfinite(max_ratio) else 0.0,
        prompt_above_null=all(r.extraction_success for r in results) if results else False,
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
        "cache_was_cold": bool(cache_was_cold),
        "wall_clock_is_true_full_compute": bool(cache_was_cold),
        "peak_rss_mb": round(peak_rss, 1) if peak_rss else None,
        "platform": platform.platform(),
        "n_boot": n_boot,
        "ci_level": ci_level,
        "min_depth_frac": min_depth_frac,
        "min_layer_scanned": min_layer_for_depth(top, min_depth_frac),
        "top_k_layers": top_k,
        "seeds": list(seeds),
        "axes": [r.to_row() for r in results],
        "aggregate": {
            "n_axes": n_axes,
            "facade_support_fraction": support_fraction,
            "n_axes_facade_holds_ci": int(sum(r.c1_signal for r in results)),
            "n_axes_stable_layer": int(sum(r.stable_layer_found for r in results)),
            "n_axes_unstable": int(sum(not r.stable_layer_found for r in results)),
            "n_axes_seed_stable": int(sum(r.seed_stable for r in results)),
            "max_facade_ratio_observed": max_ratio,
            "extraction_success_all": bool(all(r.extraction_success for r in results)),
        },
        "routing_EXPLORATORY": routing.to_dict(),
        "routing_caveat": (
            "EXPLORATORY only. This C1 pilot measures the semantic-facade gap; it "
            "does NOT measure blind-eval (AC4), transfer/composition (AC5), or the "
            "behavioral prompt-search ceiling (AC8). Those routing gates are set "
            "False here by construction, so the route is NOT a real Go/No-Go — the "
            "meaningful signal is the per-axis same-origin facade_ratio + its CI."
        ),
        "metric_note": (
            "facade_ratio is the CORRECTED same-origin, scale-free, alpha-free "
            "reach fraction (D-0016): prompt_reach / pole_reach, both measured as "
            "on-axis displacement from the SAME neutral origin projected on û. The "
            "old ||v||-based ratio (facade_ratio_vnorm_*_SUPERSEDED) is retained "
            "per-axis for comparison only — it mixed origins and baked in alpha=1."
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
    lines.append(f"- wall-clock: {payload['wall_clock_seconds']}s "
                 f"(cache_was_cold={payload['cache_was_cold']}, "
                 f"true_full_compute={payload['wall_clock_is_true_full_compute']})   "
                 f"peak RSS: {payload['peak_rss_mb']} MB")
    lines.append(f"- bootstrap: n_boot={payload['n_boot']}  CI level={payload['ci_level']}")
    lines.append(f"- layer selection (D-0019): NON-DEGENERATE rule — depth floor "
                 f"min_layer={payload['min_layer_scanned']} (>= {payload['min_depth_frac']*100:.0f}% of depth), "
                 f"pole_reach > 0 above random-null p95, positive pos/neg separation. "
                 f"top_k={payload['top_k_layers']} candidate layers, seeds={payload['seeds']}.")
    lines.append(f"- valid_for_paper: **{payload['valid_for_paper']}**\n")
    lines.append(
        "## Per-axis facade gap — CORRECTED same-origin, scale-free, alpha-free metric (D-0016)\n"
    )
    lines.append(
        "facade_ratio = prompt_reach / pole_reach, both measured as on-axis "
        "displacement from the SAME neutral origin projected on û, at the chosen "
        "NON-DEGENERATE layer (D-0019). A facade genuinely HOLDS only when a stable "
        "layer exists AND extraction succeeded AND the bootstrap CI upper bound is "
        "< 1 (number reported; NO frozen verdict). An UNSTABLE axis has no "
        "non-degenerate layer at this model — reported honestly, NOT forced.\n"
    )
    lines.append(
        "| axis | layer | stable? | prompt_reach | pole_reach | facade_ratio | 95% CI | "
        "leave-1-neutral band | extract ok? | seed-stable? | CI upper<1? | C1 signal |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in payload["axes"]:  # type: ignore[index]
        lines.append(
            f"| {r['axis']} | {r['chosen_layer']} | "
            f"{'yes' if r['stable_layer_found'] else 'UNSTABLE'} | {r['prompt_reach']:.3f} | "
            f"{r['pole_reach']:.3f} | {r['facade_ratio']:.3f} | "
            f"[{r['facade_ratio_ci_lo']:.3f}, {r['facade_ratio_ci_hi']:.3f}] | "
            f"[{r['facade_ratio_loo_min']:.3f}, {r['facade_ratio_loo_max']:.3f}] | "
            f"{'yes' if r['extraction_success'] else 'NO'} | "
            f"{'yes' if r['seed_stable'] else 'no'} | "
            f"{'yes' if r['facade_gap_holds_ci'] else 'no'} | "
            f"{'YES' if r['c1_signal'] else 'no'} |"
        )
    lines.append("")
    # Honest note for any unstable axis.
    unstable = [r for r in payload["axes"] if not r["stable_layer_found"]]  # type: ignore[index]
    if unstable:
        lines.append("### Unstable axes (HONEST — no facade forced)\n")
        for r in unstable:
            lines.append(f"- **{r['axis']}**: {r['unstable_reason']}")
        lines.append("")
    lines.append("## ROBUSTNESS 1 — facade_ratio across top-k NON-DEGENERATE candidate layers (D-0019)\n")
    lines.append(
        "Shows whether the facade gap holds across NEARBY valid layers (not a "
        "single-layer artifact). Unstable axes have no candidates.\n"
    )
    lines.append("| axis | layer | separation | pole_reach | facade_ratio | 95% CI | CI upper<1? |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in payload["axes"]:  # type: ignore[index]
        if not r["top_k_layers"]:
            lines.append(f"| {r['axis']} | — (unstable) | — | — | — | — | — |")
            continue
        for c in r["top_k_layers"]:
            lines.append(
                f"| {r['axis']} | {c['layer']} | {c['separation']:.3f} | {c['pole_reach']:.3f} | "
                f"{c['facade_ratio']:.3f} | [{c['ci_lo']:.3f}, {c['ci_hi']:.3f}] | "
                f"{'yes' if c['ci_upper_below_1'] else 'no'} |"
            )
    lines.append("")
    lines.append("## ROBUSTNESS 2 — facade_ratio + CI at the chosen layer under multiple RNG seeds (D-0019)\n")
    lines.append(
        "The bootstrap/null seed should not move the verdict. `seed-stable` = all "
        "seeds agree on whether the CI upper bound is < 1.\n"
    )
    lines.append("| axis | seed | facade_ratio | 95% CI | CI upper<1? |")
    lines.append("|---|---|---|---|---|")
    for r in payload["axes"]:  # type: ignore[index]
        for s in r["seed_robustness"]:
            lines.append(
                f"| {r['axis']} | {s['seed']} | {s['facade_ratio']:.3f} | "
                f"[{s['ci_lo']:.3f}, {s['ci_hi']:.3f}] | "
                f"{'yes' if s['ci_upper_below_1'] else 'no'} |"
            )
    lines.append("")
    lines.append("## SUPERSEDED old ||v||-based ratio (denominator artifact, see D-0016) — for comparison only\n")
    lines.append(
        "| axis | ||v|| (SUPERSEDED) | old facade_ratio (prompt_reach/||v||) | "
        "new facade_ratio (prompt_reach/pole_reach) | flips verdict? |"
    )
    lines.append("|---|---|---|---|---|")
    for r in payload["axes"]:  # type: ignore[index]
        old = r["facade_ratio_vnorm_mean_SUPERSEDED"]
        new = r["facade_ratio"]
        # "flip" = old said facade (0<old<1) but new says none (>=1 / <=0), or vice-versa
        old_facade = 0.0 < old < 1.0
        new_facade = bool(r["c1_signal"])
        flip = "YES" if old_facade != new_facade else "no"
        lines.append(
            f"| {r['axis']} | {r['vector_norm_SUPERSEDED']:.3f} | {old:.3f} | {new:.3f} | {flip} |"
        )
    lines.append("")
    lines.append("## Sanity (labelled — NOT headline; trivial in high-dim, audit MAJOR-3)\n")
    lines.append("| axis | prompt_reach above random-null? | signal_z | pole above-null p95 |")
    lines.append("|---|---|---|---|")
    for r in payload["axes"]:  # type: ignore[index]
        lines.append(
            f"| {r['axis']} | {r['sanity_above_null']} | {r['sanity_signal_z']:.2f} | "
            f"{r['pole_null_p95']:.3f} |"
        )
    agg = payload["aggregate"]  # type: ignore[index]
    lines.append("")
    lines.append("## Aggregate\n")
    lines.append(f"- axes where a facade genuinely holds (stable layer AND extract ok AND CI upper<1): "
                 f"{agg['n_axes_facade_holds_ci']}/{agg['n_axes']} "
                 f"({agg['facade_support_fraction']*100:.0f}%)")
    lines.append(f"- axes with a stable (non-degenerate) layer: {agg['n_axes_stable_layer']}/{agg['n_axes']} "
                 f"(unstable: {agg['n_axes_unstable']})")
    lines.append(f"- axes seed-stable (verdict invariant across seeds): {agg['n_axes_seed_stable']}/{agg['n_axes']}")
    lines.append(f"- max same-origin facade_ratio observed: {agg['max_facade_ratio_observed']:.3f}")
    lines.append(f"- extraction succeeded on all axes: {agg['extraction_success_all']}")
    lines.append("")
    lines.append("## Routing (EXPLORATORY — not a real Go/No-Go)\n")
    lines.append(f"- route: `{payload['routing_EXPLORATORY']['route']}`  "  # type: ignore[index]
                 f"verdict: `{payload['routing_EXPLORATORY']['verdict']}`")
    lines.append(f"- {payload['routing_caveat']}")
    lines.append("")
    lines.append("## How to read facade_ratio (CORRECTED, D-0016)\n")
    lines.append(
        "- `pole_reach = <mean(EXTRACTION-POS act) − neutral_mean_act, û>` — the model's "
        "ACHIEVABLE positive-pole displacement from the SAME neutral origin (NO steering "
        "coefficient alpha; replaces the old ||v|| denominator).\n"
        "- `prompt_reach = <mean(strong-prompt act) − neutral_mean_act, û>` — the strongest "
        "readable prompt's displacement from the SAME origin.\n"
        "- `facade_ratio = prompt_reach / pole_reach` (scale-free, alpha-free, same-origin). "
        "0 < ratio << 1 AND CI upper<1 => genuine facade (prompt points right way, only "
        "part-way to the pole). ratio ~= 1 or >1 => NO facade. ratio < 0 => prompt goes the "
        "WRONG way.\n"
        "- A facade 'holds' only if the bootstrap CI upper bound is meaningfully < 1 — we "
        "report the number and do NOT hard-code a frozen verdict.\n"
        "- The strongest-prompt set is DISTINCT IN KIND from the contrast pairs used to build v "
        "(guarded in tests/test_leakage.py), so the ratio is not inflated by pseudo-circularity."
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
        "min_depth_frac": payload["min_depth_frac"],
        "min_layer_scanned": payload["min_layer_scanned"],
        "top_k_layers": payload["top_k_layers"],
        "seeds": payload["seeds"],
    }
    cfg_hash = config_hash(cfg)
    data_hashes = {
        r["axis"]: {
            "file": r["file_hash"],
            "split": r["split_hash"],
            "strongest": r["strongest_file_hash"],
        }
        for r in axis_rows
    }
    summary_metrics = {
        r["axis"]: {
            "chosen_layer": r["chosen_layer"],
            "prompt_reach": r["prompt_reach"],
            "pole_reach": r["pole_reach"],
            "facade_ratio": r["facade_ratio"],
            "facade_ratio_ci_lo": r["facade_ratio_ci_lo"],
            "facade_ratio_ci_hi": r["facade_ratio_ci_hi"],
            "facade_ratio_loo_min": r["facade_ratio_loo_min"],
            "facade_ratio_loo_max": r["facade_ratio_loo_max"],
            "facade_ratio_vnorm_mean_SUPERSEDED": r["facade_ratio_vnorm_mean_SUPERSEDED"],
            "extraction_success": r["extraction_success"],
            "facade_gap_holds_ci": r["facade_gap_holds_ci"],
            "stable_layer_found": r["stable_layer_found"],
            "seed_stable": r["seed_stable"],
            "c1_signal": r["c1_signal"],
        }
        for r in axis_rows
    }
    summary_metrics["_aggregate"] = payload["aggregate"]

    # Honest wall-clock (audit MINOR-6): record the TRUE full-compute seconds and
    # flag whether the activation cache was cold (a warm-cache run under-reports).
    raw_metrics = {
        "wall_clock_seconds": payload["wall_clock_seconds"],
        "cache_was_cold": payload["cache_was_cold"],
        "wall_clock_is_true_full_compute": payload["wall_clock_is_true_full_compute"],
        "peak_rss_mb": payload["peak_rss_mb"],
        "n_boot": payload["n_boot"],
        "ci_level": payload["ci_level"],
    }

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
        dataset=(
            "data/contrast_pairs/*.jsonl (28/12 disjoint split for v) + "
            "data/strongest_prompts/*.jsonl (separate strongest-prompt set)"
        ),
        seed=seed,
        hardware="cpu-local-float32",
        started_at=str(payload["generated_at"]),
        ended_at=utcnow(),
        exit_code=0,
        summary_metrics=summary_metrics,
        raw_metrics=raw_metrics,
        artifacts=[str(json_path.relative_to(_REPO)).replace("\\", "/")],
        valid_for_paper=False,
        validation_notes=(
            f"EXPLORATORY C1 facade pilot on {payload['model']} (CPU). Protocol NOT "
            "frozen. CORRECTED METRIC (D-0016): facade_ratio = prompt_reach / "
            "pole_reach is same-origin, scale-free, and alpha-free — both reaches "
            "are on-axis displacement from the SAME neutral origin projected on û. "
            "This replaces the SUPERSEDED ||v||-based ratio (BLOCKER-1 alpha=1 "
            "dependence, BLOCKER-2 origin mismatch), which is retained per-axis for "
            "comparison only. Bootstrap 95% CI over the strong-prompt set + "
            "leave-one-neutral-out band reported. above-null demoted to a labelled "
            "sanity field (MAJOR-3). FIX2 retained: strongest-prompt reach on a "
            "SEPARATELY-authored instruction set, distinct in kind from the contrast "
            "pairs (expanded 7->16/axis, D-0019, to tighten the CI). STRENGTHENED "
            "(D-0019): NON-DEGENERATE layer selection (depth floor + pole_reach above "
            "random-null p95 + positive separation) replaces bare Cohen's-d, which had "
            "picked a degenerate shallow layer for focus; facade_ratio reported across "
            "top-k candidate layers and under multiple RNG seeds for robustness; an "
            "axis with no non-degenerate layer is reported UNSTABLE, not forced. "
            f"Wall-clock {payload['wall_clock_seconds']}s recorded as TRUE "
            f"full-compute (cache_was_cold={payload['cache_was_cold']}, MINOR-6). "
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
    ap.add_argument("--n-boot", type=int, default=2000,
                    help="bootstrap resamples for the facade_ratio CI")
    ap.add_argument("--ci-level", type=float, default=0.95,
                    help="bootstrap CI level for the facade_ratio")
    ap.add_argument("--min-depth-frac", type=float, default=0.2,
                    help="depth floor for layer selection (fraction of network depth)")
    ap.add_argument("--top-k", type=int, default=3,
                    help="report facade_ratio across the top-k non-degenerate layers")
    ap.add_argument("--seeds", type=int, nargs="*", default=None,
                    help="RNG seeds for the multi-seed CI robustness check "
                         "(default: seed, seed+1, seed+2)")
    ap.add_argument("--ram-floor-mb", type=float, default=450.0,
                    help="hard-abort the run if system-available RAM drops below this")
    ap.add_argument("--device", default="cpu",
                    help="torch device for the activation forward pass (e.g. cpu, cuda)")
    ap.add_argument("--dtype", default="float32",
                    help="torch dtype for the model (e.g. float32, float16)")
    ap.add_argument(
        "--out-dir",
        default=str(_REPO / "results" / "c1_facade_1p5b_strengthened_2026-07-23"),
    )
    args = ap.parse_args(argv)

    seeds = args.seeds if args.seeds else [args.seed, args.seed + 1, args.seed + 2]
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
        ram_floor_mb=args.ram_floor_mb,
        n_boot=args.n_boot,
        ci_level=args.ci_level,
        min_depth_frac=args.min_depth_frac,
        top_k=args.top_k,
        seeds=seeds,
        device=args.device,
        dtype=args.dtype,
    )
    json_path, summary_path = _write_results(payload, out_dir, args.seed)
    exp_id = _register(payload, out_dir, json_path, args.seed)
    print(f"[c1] wrote {json_path}")
    print(f"[c1] wrote {summary_path}")
    print(f"[c1] registered experiment_id={exp_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
