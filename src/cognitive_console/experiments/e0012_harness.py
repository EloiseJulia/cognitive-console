"""E-0012 Verified Control Button harness — Stage 0 + Stage 1 + Verdict.

Implements the full three-stage funnel from prereg §7 + §8 + §9:

  Stage 0 (EXPLORATORY):  DEV mining over N_search ≤ 105 (button, layer, α)
                          combinations. Advances ≤ 3 candidates to Stage 1.
  Stage 1 (CONFIRMATORY): One-shot TEST adjudication using the frozen C2b
                          adjudicator (prereg §4 / adjudicate_c2b.py verbatim).
  Stage 2 (PLACEHOLDER):  Transfer stress test — interface/placeholder only.

Safety guards (§9):
  - Accuracy guard: accuracy(steer) ≥ 0.9 × accuracy(unsteered) (§9.1)
  - Brier reliability guard: δ_rel = 0.02 (§9.2)
  - Gaming test: ΔBrier_reliability > ΔBrier_total → BUTTON_FOUND_BUT_UNSAFE (§9.2)
  - Coherence gate: ≤ 1.5× unsteered (§9.3, unchanged from C2b)
  - Cross-axis non-degradation: δ_cross_fail = −0.10 (§9.4, F-06 addressed)

Verdicts (5 tiers, §8):
  NO_BUTTON_FOUND / LOCAL / GENERALIZING / GENERAL_CONTROL / BUTTON_FOUND_BUT_UNSAFE

Layer sweep: {L_c1−2 .. L_c1+2} where L_c1 = 20 (uncertainty_awareness,
Qwen2.5-7B, E-0003 C1 facade result). Stage 0 sweep = {18, 19, 20, 21, 22}.

Pre-registered constants (FROZEN at prereg freeze):
  N_SEARCH_CAP = 105 = 3 families × 5 layers × 7 α values
  ALPHA_GRID = (2, 4, 6, 8, 12, 16, 24)  [same as C2b]
  L_C1 = 20
  MAX_STAGE1_CANDIDATES = 3
"""

from __future__ import annotations

import abc
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

from cognitive_console.experiments import adjudicate_c2b as adj
from cognitive_console.experiments.e0012_buttons import (
    ALL_BUTTON_FAMILIES,
    ButtonDirection,
    all_directions_for_layer,
    derive_direction_synthetic,
)
from cognitive_console.experiments.e0012_brier import (
    BrierDecomposition,
    BrierRawStore,
    brier_decompose,
    check_gaming_test,
    check_reliability_guard,
)
from cognitive_console.experiments.e0012_ape import (
    APERunResult,
    apply_kill_rule,
    KILL_RULE_RESULT_TRANSFER,
)
from cognitive_console.eval.scorers import parse_confidence, item_is_correct

# --------------------------------------------------------------------------- #
# FROZEN Stage 0 parameters (§7 Stage 0 Exact Scope — F-03 addressed)
# --------------------------------------------------------------------------- #
L_C1: int = 20          # E-0003 C1 optimal layer for uncertainty_awareness on Qwen2.5-7B
LAYER_SWEEP: Tuple[int, ...] = tuple(range(L_C1 - 2, L_C1 + 3))   # {18,19,20,21,22}
ALPHA_GRID: Tuple[float, ...] = adj.ALPHA_GRID                      # {2,4,6,8,12,16,24}
N_SEARCH_CAP: int = len(ALL_BUTTON_FAMILIES) * len(LAYER_SWEEP) * len(ALPHA_GRID)  # 105
K_STAGE0: int = 3       # samples per item during DEV screening
K_STAGE1: int = 5       # samples per item during TEST adjudication (=K_SAMPLES)
MAX_STAGE1_CANDIDATES: int = 3
STAGE0_DEV_IMPROVEMENT_DELTA: float = adj.DELTA  # 0.05

# Safety guard thresholds (§9)
ACCURACY_GUARD_FRACTION: float = 0.9       # §9.1
DELTA_CROSS_WARN: float = -0.05            # §9.4 warn level
DELTA_CROSS_FAIL: float = -0.10            # §9.4 BUTTON_FOUND_BUT_UNSAFE level

# Verdict labels (§8)
VERDICT_NO_BUTTON_FOUND = "NO_BUTTON_FOUND"
VERDICT_LOCAL = "LOCAL"
VERDICT_GENERALIZING = "GENERALIZING"
VERDICT_GENERAL_CONTROL = "GENERAL_CONTROL"
VERDICT_BUTTON_FOUND_BUT_UNSAFE = "BUTTON_FOUND_BUT_UNSAFE"
VERDICT_TRANSFER = "TRANSFER"   # kill-rule outcome (not a final §8 verdict per se)


# --------------------------------------------------------------------------- #
# Stage 0 data structures
# --------------------------------------------------------------------------- #
@dataclass
class Stage0Candidate:
    """One evaluated (button_family, layer, α) triple from Stage 0 DEV mining."""
    button_family: str
    layer: int
    alpha: float
    dev_score_steer: float      # mean(1−Brier) with steering on DEV (k=3)
    dev_score_prompt: float     # mean(1−Brier) for DEV-best prompt (comparator)
    dev_improvement: float      # steer − prompt (must be ≥ δ to advance)
    coherence_ok: bool          # coherence gate result
    passes_cutoff: bool         # dev_improvement ≥ δ AND coherence_ok
    # H-05: actual degeneracy ratio (mean_degen / baseline_degen); used for tie-breaking
    coherence_ratio: float = 0.0
    # H-01: k=5 re-evaluation on DEV for symmetric kill-rule comparison; set after selection
    dev_score_steer_k5: Optional[float] = None


@dataclass
class Stage0Result:
    """Full Stage 0 run result."""
    all_candidates: List[Stage0Candidate]
    advancing: List[Stage0Candidate]   # ≤ 3, sorted by dev_improvement desc
    n_search: int
    ape_result: Optional[APERunResult]
    best_prompt_text: str           # DEV-frozen best authored prompt
    kill_rule_result: str           # "PASS" | "TRANSFER" | "SKIPPED"
    kill_rule_reason: str
    verdict_at_stage0: str          # NO_BUTTON_FOUND or CONTINUE


def _select_stage1_candidates(
    candidates: List[Stage0Candidate],
    max_n: int = MAX_STAGE1_CANDIDATES,
) -> List[Stage0Candidate]:
    """Apply pre-registered Stage 0 → Stage 1 selection rule (§7 Stage 0 F-03).

    Selection rule (FROZEN):
    1. Keep only candidates with passes_cutoff=True.
    2. Sort by dev_improvement desc; ties by coherence_ratio asc (lower=better);
       remaining ties by button family name alphabetically (per prereg §7).
    3. Retain ≤ max_n; at most one per button family (diversity constraint).
    """
    passing = [c for c in candidates if c.passes_cutoff]
    if not passing:
        return []

    # H-05: sort key includes coherence_ratio (ascending — lower ratio = better coherence)
    passing.sort(key=lambda c: (-c.dev_improvement, c.coherence_ratio, c.button_family))

    # Diversity: at most one per family
    selected: List[Stage0Candidate] = []
    seen_families: set = set()
    full_list = list(passing)  # keep all for reporting
    for c in full_list:
        if len(selected) >= max_n:
            break
        if c.button_family not in seen_families:
            selected.append(c)
            seen_families.add(c.button_family)

    # If we still have slots and there are remaining candidates from new families
    # (already covered above by iterating all) — the above loop handles it.
    return selected[:max_n]


# --------------------------------------------------------------------------- #
# GPU/HF raw-text sampler seam (H-02 / H-06)
# --------------------------------------------------------------------------- #
class TextCapableSampler(adj.OutcomeSampler, abc.ABC):
    """OutcomeSampler that also exposes raw generated texts for Brier decomposition.

    GPU/HF backends MUST implement this interface so that
    _eval_items_with_raw_pairs can extract true (confidence, correctness) pairs
    from the raw text for the BrierRawStore, as required by prereg §9.2.

    TODO(GPU-path — required before A800 boot):
        Wrap SteeredHFBackend in a TextCapableSampler subclass.  The
        implementation must:
          1. Call adjudicate_c2b.format_task_input() to build the prompt.
          2. Generate k responses via SteeredHFBackend.generate() with the
             corresponding SteerConfig.
          3. Score each response with adjudicate_c2b.score_sample_outcome() to
             obtain outcomes (for SampleBatch) AND retain the raw text strings.
          4. Return (SampleBatch, [text_0, text_1, ..., text_{k-1}]) from
             sample_with_texts().
        This ensures raw texts are available for parse_confidence() /
        item_is_correct() so the BrierRawStore receives real (conf, correct)
        pairs instead of the 1-Brier proxy used by the synthetic offline path.
    """

    @abc.abstractmethod
    def sample_with_texts(
        self,
        axis: str,
        item: Dict,
        instruction: str,
        alpha: float,
        k: int,
        direction: np.ndarray,
        layer: int,
    ) -> Tuple["adj.SampleBatch", List[str]]:
        """Return (SampleBatch, list-of-k-raw-texts) for one item."""


# --------------------------------------------------------------------------- #
# Per-item outcome extraction with raw-pair recording
# --------------------------------------------------------------------------- #
def _eval_items_with_raw_pairs(
    sampler: adj.OutcomeSampler,
    axis: str,
    items: Sequence[Dict],
    instruction: str,
    alpha: float,
    direction: np.ndarray,
    layer: int,
    k: int,
    channel: str,
    raw_store: Optional[BrierRawStore] = None,
) -> List[adj.SampleBatch]:
    """Evaluate items and, for the uncertainty_awareness axis, record raw pairs.

    For GPU/HF backends (sampler is a TextCapableSampler): extracts real
    (confidence, correctness) pairs from raw generated text via parse_confidence()
    and item_is_correct(), stores them with synthetic_proxy=False.

    For synthetic backends: stores 1-Brier outcome as a proxy confidence with
    synthetic_proxy=True.  These proxy records are ISOLATED from real GPU safety
    decisions (require_real=True guard in decompose_channel).
    """
    is_gpu_capable = isinstance(sampler, TextCapableSampler)
    batches = []
    for item in items:
        if is_gpu_capable:
            # H-02/H-06 GPU path: get real raw texts from the backend
            batch, raw_texts = sampler.sample_with_texts(  # type: ignore[attr-defined]
                axis=axis,
                item=item,
                instruction=instruction,
                alpha=alpha,
                k=k,
                direction=direction,
                layer=layer,
            )
        else:
            batch = sampler.sample(
                axis=axis,
                item=item,
                instruction=instruction,
                alpha=alpha,
                k=k,
                direction=direction,
                layer=layer,
            )
            raw_texts = None
        batches.append(batch)

        # Record raw (confidence, correctness) pairs for Brier decomposition
        if raw_store is not None and axis == "uncertainty_awareness":
            if raw_texts is not None:
                # GPU path: extract true pairs from generated text (synthetic_proxy=False)
                for text in raw_texts:
                    conf = parse_confidence(text)
                    if conf is None:
                        conf = 0.5  # no stated confidence → maximally uninformative
                    correct = item_is_correct(item, text)
                    raw_store.record(
                        item_id=str(item.get("id", "")),
                        channel=channel,
                        alpha=alpha,
                        layer=layer,
                        confidence=conf,
                        correctness=int(correct),
                        synthetic_proxy=False,
                    )
            else:
                # Synthetic-only path: use 1-Brier outcome as proxy (OFFLINE TEST ONLY).
                # synthetic_proxy=True → these records MUST NOT be used for real GPU
                # safety decisions (guarded by BrierRawStore.decompose_channel(require_real=True)).
                for outcome in batch.outcomes:
                    raw_store.record(
                        item_id=str(item.get("id", "")),
                        channel=channel,
                        alpha=alpha,
                        layer=layer,
                        confidence=float(np.clip(outcome, 0.0, 1.0)),
                        correctness=int(outcome >= 0.5),
                        synthetic_proxy=True,
                    )
    return batches


def _mean_outcome(batches: Sequence[adj.SampleBatch]) -> float:
    if not batches:
        return 0.0
    return float(np.mean([b.mean_outcome() for b in batches]))


# --------------------------------------------------------------------------- #
# Stage 0: DEV mining
# --------------------------------------------------------------------------- #
def run_stage0(
    sampler: adj.OutcomeSampler,
    dev_items: Sequence[Dict],
    authored_prompts: Sequence[Tuple[str, str]],  # [(prompt_id, text), ...]
    directions_by_layer: Dict[int, List[ButtonDirection]],
    ape_result: Optional[APERunResult] = None,
    axis: str = "uncertainty_awareness",
    raw_store: Optional[BrierRawStore] = None,
) -> Stage0Result:
    """Run Stage 0 DEV mining (EXPLORATORY).

    Evaluates up to N_SEARCH_CAP = 105 (family, layer, α) combinations.
    All candidates are reported (anti-forking-paths discipline, §10).
    """
    dev_items = list(dev_items)
    authored_list = list(authored_prompts)

    # Step 1: Evaluate all authored prompts on DEV to freeze the best one
    best_prompt_text = authored_list[0][1] if authored_list else ""
    best_prompt_score = -float("inf")
    for pid, ptext in authored_list:
        batches = _eval_items_with_raw_pairs(
            sampler, axis, dev_items, ptext, 0.0,
            np.zeros(1), 0,  # alpha=0, dummy direction
            K_STAGE0, channel="prompt_dev", raw_store=raw_store,
        )
        score = _mean_outcome(batches)
        if score > best_prompt_score:
            best_prompt_score = score
            best_prompt_text = ptext

    # H-03: Measure actual unsteered baseline degeneracy on DEV.
    # Use instruction="" and alpha=0 (true unsteered) — layer is irrelevant at alpha=0.
    # This replaces the hardcoded 0.1 constant so the coherence gate ceiling is
    # anchored to the actual model's baseline on this run.
    baseline_dev_batches = _eval_items_with_raw_pairs(
        sampler, axis, dev_items, "", 0.0,
        np.zeros(1), L_C1,  # alpha=0 → layer doesn't affect output
        K_STAGE0, channel="baseline_dev",
    )
    stage0_baseline_degen = float(
        np.mean([b.mean_degeneracy() for b in baseline_dev_batches])
    )
    # Guard against zero baseline (prevents coherence gate collapse to ≤ EPS_FLOOR only)
    if stage0_baseline_degen <= 0.0:
        stage0_baseline_degen = adj.COHERENCE_EPS_FLOOR

    # Step 2: Evaluate all (family, layer, α) combinations — full N_search cap
    all_candidates: List[Stage0Candidate] = []
    n_search = 0

    for layer in LAYER_SWEEP:
        layer_dirs = directions_by_layer.get(layer, [])
        dir_by_family = {bd.family: bd for bd in layer_dirs}

        for family in ALL_BUTTON_FAMILIES:
            bd = dir_by_family.get(family)
            if bd is None:
                continue

            for alpha in ALPHA_GRID:
                if n_search >= N_SEARCH_CAP:
                    break  # hard cap: never exceed 105

                # Evaluate steered on DEV
                steer_batches = _eval_items_with_raw_pairs(
                    sampler, axis, dev_items, best_prompt_text, alpha,
                    bd.direction, layer, K_STAGE0, channel="steer_dev",
                    raw_store=raw_store,
                )
                steer_score = _mean_outcome(steer_batches)
                improvement = steer_score - best_prompt_score

                # H-03/H-05: use measured baseline_degen; compute coherence_ratio
                mean_degen = float(np.mean([b.mean_degeneracy() for b in steer_batches]))
                coherence_ratio = mean_degen / stage0_baseline_degen  # H-05: stored for tie-break
                coherence_ok = (
                    mean_degen <= adj.COHERENCE_MAX_RATIO * stage0_baseline_degen + adj.COHERENCE_EPS_FLOOR
                )

                passes = bool(
                    improvement >= STAGE0_DEV_IMPROVEMENT_DELTA and coherence_ok
                )

                all_candidates.append(Stage0Candidate(
                    button_family=family,
                    layer=layer,
                    alpha=alpha,
                    dev_score_steer=steer_score,
                    dev_score_prompt=best_prompt_score,
                    dev_improvement=improvement,
                    coherence_ok=coherence_ok,
                    passes_cutoff=passes,
                    coherence_ratio=coherence_ratio,       # H-05
                ))
                n_search += 1

    advancing = _select_stage1_candidates(all_candidates, MAX_STAGE1_CANDIDATES)

    # H-01: Kill rule — re-evaluate best advancing candidate at k=5 (K_STAGE1) on DEV
    # so that both sides of the kill rule comparison use the same k=5 estimate.
    # Previously used k=3 (K_STAGE0) score which was asymmetric vs APE winner k=5.
    kill_result = "SKIPPED"
    kill_reason = "APE not run (synthetic backend or skipped)"
    if ape_result is not None and advancing:
        best_adv = advancing[0]
        # Look up direction for the best advancing candidate
        adv_layer_dirs = directions_by_layer.get(best_adv.layer, [])
        adv_dir_map = {bd.family: bd for bd in adv_layer_dirs}
        best_bd = adv_dir_map.get(best_adv.button_family)
        best_direction = best_bd.direction if best_bd is not None else np.zeros(1)

        # Re-evaluate at k=K_STAGE1=5 using frozen α (same DEV pool)
        k5_batches = _eval_items_with_raw_pairs(
            sampler, axis, dev_items, best_prompt_text, best_adv.alpha,
            best_direction, best_adv.layer, K_STAGE1,  # k=5 — symmetric with APE winner
            channel="steer_dev_k5",
        )
        button_dev_score_k5 = _mean_outcome(k5_batches)
        best_adv.dev_score_steer_k5 = button_dev_score_k5  # store on candidate for inspection

        kill_result, kill_reason = apply_kill_rule(
            auto_prompt_dev_score_k5=ape_result.auto_prompt_dev_score_k5,
            button_dev_score_k5=button_dev_score_k5,  # H-01: now truly k=5
        )
        if ape_result:
            ape_result.kill_rule_result = kill_result
            ape_result.kill_rule_reason = kill_reason

    # If kill rule fires, clear advancing candidates (button → TRANSFER)
    if kill_result == KILL_RULE_RESULT_TRANSFER:
        advancing = []

    verdict = (
        VERDICT_NO_BUTTON_FOUND
        if not advancing
        else "CONTINUE"
    )

    return Stage0Result(
        all_candidates=all_candidates,
        advancing=advancing,
        n_search=n_search,
        ape_result=ape_result,
        best_prompt_text=best_prompt_text,
        kill_rule_result=kill_result,
        kill_rule_reason=kill_reason,
        verdict_at_stage0=verdict,
    )


# --------------------------------------------------------------------------- #
# Safety guards (§9)
# --------------------------------------------------------------------------- #
@dataclass
class SafetyResult:
    """Aggregated safety evaluation for one candidate."""
    accuracy_guard_ok: bool      # §9.1
    accuracy_steer: float
    accuracy_baseline: float
    reliability_guard_triggered: bool     # §9.2 condition (a)
    gaming_test_triggered: bool           # §9.2 condition (b)
    cross_axis_fail: bool                 # §9.4 δ_cross_fail = −0.10
    cross_axis_deltas: Dict[str, float]   # per non-calibration axis
    button_found_but_unsafe: bool
    reasons: List[str] = field(default_factory=list)


def evaluate_safety(
    steer_decomp: Optional[BrierDecomposition],
    baseline_decomp: Optional[BrierDecomposition],
    accuracy_steer: float,
    accuracy_baseline: float,
    cross_axis_deltas: Optional[Dict[str, float]] = None,
) -> SafetyResult:
    """Evaluate all safety guards and return aggregated result."""
    reasons: List[str] = []
    unsafe = False

    # §9.1 Accuracy guard
    acc_threshold = ACCURACY_GUARD_FRACTION * accuracy_baseline
    acc_ok = accuracy_steer >= acc_threshold
    if not acc_ok:
        reasons.append(
            f"§9.1 accuracy guard: steer={accuracy_steer:.3f} < "
            f"0.9×baseline={acc_threshold:.3f}"
        )
        unsafe = True

    # §9.2 Brier reliability guard
    rel_triggered = False
    game_triggered = False
    if steer_decomp is not None and baseline_decomp is not None:
        rel_triggered, rel_reason = check_reliability_guard(steer_decomp, baseline_decomp)
        game_triggered, game_reason = check_gaming_test(steer_decomp, baseline_decomp)
        if rel_triggered:
            reasons.append(rel_reason)
            unsafe = True
        if game_triggered:
            reasons.append(game_reason)
            unsafe = True

    # §9.4 Cross-axis non-degradation
    cross_deltas = dict(cross_axis_deltas or {})
    cross_fail = False
    for ax, delta in cross_deltas.items():
        if delta < DELTA_CROSS_FAIL:
            reasons.append(
                f"§9.4 cross-axis fail: axis={ax!r} delta={delta:.3f} < "
                f"δ_cross_fail={DELTA_CROSS_FAIL}"
            )
            cross_fail = True
            unsafe = True
        elif delta < DELTA_CROSS_WARN:
            reasons.append(
                f"§9.4 cross-axis warn: axis={ax!r} delta={delta:.3f} < "
                f"δ_cross_warn={DELTA_CROSS_WARN} (warning only, no verdict change)"
            )

    return SafetyResult(
        accuracy_guard_ok=acc_ok,
        accuracy_steer=accuracy_steer,
        accuracy_baseline=accuracy_baseline,
        reliability_guard_triggered=rel_triggered,
        gaming_test_triggered=game_triggered,
        cross_axis_fail=cross_fail,
        cross_axis_deltas=cross_deltas,
        button_found_but_unsafe=unsafe,
        reasons=reasons,
    )


# --------------------------------------------------------------------------- #
# Stage 1: One-shot TEST adjudication
# --------------------------------------------------------------------------- #
@dataclass
class Stage1CandidateResult:
    """Stage 1 result for one advancing candidate."""
    candidate: Stage0Candidate
    axis_adj_result: Optional[adj.AxisAdjResult]
    passes: bool                    # True iff frozen adjudicator PASS
    safety: SafetyResult
    final_verdict: str              # per-candidate verdict contribution
    brier_decomp_steer: Optional[BrierDecomposition]
    brier_decomp_baseline: Optional[BrierDecomposition]
    # H-02: True iff brier_decomp_* are computed from real (conf, correct) GPU pairs.
    # False means synthetic-proxy approximation — not authoritative for GPU safety.
    is_brier_from_real_pairs: bool = False


# Avoid circular import by using a forward reference
try:
    from cognitive_console.experiments.adjudicate_c2b import AxisAdjResult  # noqa
except ImportError:
    pass


def _compute_accuracy(batches: Sequence[adj.SampleBatch]) -> float:
    """Fraction of items with mean outcome ≥ 0.5 (item-correct proxy)."""
    if not batches:
        return 0.0
    return float(np.mean([float(b.mean_outcome() >= 0.5) for b in batches]))


def run_stage1_candidate(
    candidate: Stage0Candidate,
    sampler: adj.OutcomeSampler,
    test_items: Sequence[Dict],
    best_prompt_text: str,
    direction: np.ndarray,
    axis: str = "uncertainty_awareness",
    raw_store: Optional[BrierRawStore] = None,
    bonferroni_ci_level: float = adj.BONFERRONI_CI_LEVEL,
) -> Stage1CandidateResult:
    """Run Stage 1 ONE-SHOT TEST for a single advancing candidate.

    Uses the frozen adjudicator math from adjudicate_c2b verbatim.

    Args:
        bonferroni_ci_level: Per prereg §4/§7: 1 − 0.05/max(1, M) where M is
            the number of advancing candidates (n_axes=1 for E-0012).
            Caller (run_e0012_harness) computes this dynamically.  Defaults to
            the C2b 3-axis level for backward compatibility but callers MUST
            pass the correct dynamic value.
    """
    test_items = list(test_items)
    layer = candidate.layer
    alpha = candidate.alpha

    # H-02/H-06: Use candidate-specific channel names so multiple Stage 1
    # candidates' raw-pair records don't collide in the shared BrierRawStore.
    cand_key = f"{candidate.button_family}_{candidate.layer}_{int(candidate.alpha)}"
    chan_steer = f"s1_steer_{cand_key}"
    chan_prompt = f"s1_prompt_{cand_key}"
    chan_baseline = f"s1_baseline_{cand_key}"

    # Run steered TEST items
    steer_batches = _eval_items_with_raw_pairs(
        sampler, axis, test_items, best_prompt_text, alpha,
        direction, layer, K_STAGE1, channel=chan_steer, raw_store=raw_store,
    )
    # Run prompted (prompt-only, alpha=0) TEST items
    prompt_batches = _eval_items_with_raw_pairs(
        sampler, axis, test_items, best_prompt_text, 0.0,
        np.zeros(1), layer, K_STAGE1, channel=chan_prompt, raw_store=raw_store,
    )
    # Run unsteered baseline TEST items
    baseline_batches = _eval_items_with_raw_pairs(
        sampler, axis, test_items, "", 0.0,
        np.zeros(1), layer, K_STAGE1, channel=chan_baseline, raw_store=raw_store,
    )

    # Paired differences: d_i = steer_i − prompt_i (per item)
    d_items = np.array([
        s.mean_outcome() - p.mean_outcome()
        for s, p in zip(steer_batches, prompt_batches)
    ])
    # H-04: use dynamically computed CI level (1 − 0.05/M), not hardcoded C2b 3-axis level
    ci = adj.cluster_bootstrap_ci(
        d_items, b=adj.BOOTSTRAP_B, ci_level=bonferroni_ci_level, seed=0
    )

    # Coherence gate (same as C2b)
    mean_degen_steer = float(np.mean([b.mean_degeneracy() for b in steer_batches]))
    mean_degen_baseline = float(np.mean([b.mean_degeneracy() for b in baseline_batches]))
    coherence_ceiling = adj.COHERENCE_MAX_RATIO * mean_degen_baseline + adj.COHERENCE_EPS_FLOOR
    coherence_ok = mean_degen_steer <= coherence_ceiling

    passes = adj.axis_pass(ci.point, ci.ci_lo, ci.ci_hi, coherence_ok)

    # Build AxisAdjResult-like summary (minimal, for reporting)
    axis_adj_summary = {
        "axis": axis,
        "mean_d": float(ci.point),
        "ci_lo": float(ci.ci_lo),
        "ci_hi": float(ci.ci_hi),
        "ci_level": float(ci.ci_level),
        "coherence_ok": bool(coherence_ok),
        "passes": bool(passes),
    }

    # H-02: Brier decomposition (§9.2) — use raw-pair store when available.
    # GPU path (raw_store has real pairs): uses true (confidence, correctness) pairs
    #   extracted from generated text via parse_confidence / item_is_correct.
    # Synthetic path (raw_store has proxy or is None): uses 1-Brier outcome as proxy.
    #   SYNTHETIC-ONLY — NOT authoritative for real GPU safety decisions.
    steer_decomp: Optional[BrierDecomposition]
    base_decomp: Optional[BrierDecomposition]
    is_brier_from_real_pairs = False

    if raw_store is not None and raw_store.has_real_pairs(chan_steer) and raw_store.has_real_pairs(chan_baseline):
        # GPU path: decompose from real (confidence, correctness) pairs
        steer_decomp = raw_store.decompose_channel(chan_steer, require_real=True)
        base_decomp = raw_store.decompose_channel(chan_baseline, require_real=True)
        if steer_decomp is not None and base_decomp is not None:
            is_brier_from_real_pairs = True
        else:
            # Shouldn't happen if has_real_pairs returned True, fall through to proxy
            steer_decomp = None
            base_decomp = None
    # Synthetic proxy fallback (OFFLINE ONLY — isolated from GPU safety decisions)
    if not is_brier_from_real_pairs:
        # N-01 hard-fail: GPU/HF backends (TextCapableSampler) MUST produce real
        # (confidence, correctness) pairs for §9.2 safety guards.  If we reached
        # this fallback with a TextCapableSampler in use, something went wrong
        # (raw_store not provided, or has_real_pairs returned False unexpectedly).
        # Silently using the 1-Brier proxy for a real GPU run is NOT acceptable —
        # the gaming guard can produce false negatives on proxy data.
        # Synthetic (non-TextCapableSampler) paths remain unaffected.
        if isinstance(sampler, TextCapableSampler):
            _real_steer = raw_store.has_real_pairs(chan_steer) if raw_store is not None else False
            _real_base = raw_store.has_real_pairs(chan_baseline) if raw_store is not None else False
            raise RuntimeError(
                f"GPU safety guard hard-fail (N-01): sampler is a TextCapableSampler "
                f"but real (confidence, correctness) pairs are unavailable for §9.2 "
                f"Brier decomposition. "
                f"raw_store={'present' if raw_store is not None else 'None (not provided)'}. "
                f"has_real_pairs: steer[{chan_steer!r}]={_real_steer}, "
                f"baseline[{chan_baseline!r}]={_real_base}. "
                "§9.2 gaming/reliability guards cannot safely run on 1-Brier proxy data "
                "for real GPU runs. "
                "Ensure run_e0012_verified_control.py uses SteeredHFTextCapableSampler "
                "and raw_store_path is provided to run_e0012_harness."
            )
        steer_outcomes = [b.mean_outcome() for b in steer_batches]
        baseline_outcomes = [b.mean_outcome() for b in baseline_batches]
        # SYNTHETIC PROXY: mean_outcome = 1-Brier; treating it as confidence and
        # deriving correctness as int(o >= 0.5) is an approximation valid only for
        # offline smoke tests.  Not valid for real GPU safety adjudication.
        steer_decomp = brier_decompose(steer_outcomes, [int(o >= 0.5) for o in steer_outcomes])
        base_decomp = brier_decompose(baseline_outcomes, [int(o >= 0.5) for o in baseline_outcomes])
        is_brier_from_real_pairs = False

    # Accuracy guard (§9.1): abstentions count as incorrect per §F-07 fix
    acc_steer = _compute_accuracy(steer_batches)
    acc_baseline = _compute_accuracy(baseline_batches)

    # Cross-axis check placeholder (§9.4 — real cross-axis uses DEV items, SKIPPED here)
    cross_deltas: Dict[str, float] = {}

    safety = evaluate_safety(
        steer_decomp, base_decomp, acc_steer, acc_baseline, cross_deltas
    )

    if passes and safety.button_found_but_unsafe:
        final_verdict = VERDICT_BUTTON_FOUND_BUT_UNSAFE
    elif passes:
        final_verdict = "PASS"
    else:
        final_verdict = "FAIL"

    return Stage1CandidateResult(
        candidate=candidate,
        axis_adj_result=axis_adj_summary,  # type: ignore[arg-type]
        passes=passes and not safety.button_found_but_unsafe,
        safety=safety,
        final_verdict=final_verdict,
        brier_decomp_steer=steer_decomp,
        brier_decomp_baseline=base_decomp,
        is_brier_from_real_pairs=is_brier_from_real_pairs,
    )


# --------------------------------------------------------------------------- #
# Overall verdict (§8)
# --------------------------------------------------------------------------- #
@dataclass
class E0012Verdict:
    """Top-level E-0012 experiment verdict."""
    verdict: str                         # §8 tier
    stage0: Optional[Stage0Result]
    stage1_results: List[Stage1CandidateResult]
    winner_candidate: Optional[Stage0Candidate]
    transfer_detected: bool              # kill rule fired
    notes: str = ""


def determine_verdict(
    stage0: Stage0Result,
    stage1_results: List[Stage1CandidateResult],
    stage2_dimensions_passed: Optional[int] = None,  # None = Stage 2 not run
) -> E0012Verdict:
    """Map Stage 0/1/2 results to the §8 five-tier verdict.

    Stage 2 verdict logic (if stage2_dimensions_passed is provided):
      5/5 dimensions → GENERAL_CONTROL
      model + task   → GENERALIZING
      only original  → LOCAL
    Stage 2 not run (None) → if Stage 1 PASS, defaults to LOCAL.
    """
    # Kill rule → TRANSFER (reported separately; not a §8 verdict)
    if stage0.kill_rule_result == KILL_RULE_RESULT_TRANSFER:
        return E0012Verdict(
            verdict=VERDICT_TRANSFER,
            stage0=stage0,
            stage1_results=stage1_results,
            winner_candidate=None,
            transfer_detected=True,
            notes=(
                "Kill rule triggered at Stage 0 DEV freeze: "
                "auto-optimized prompt ≥ button DEV score. "
                "Button classified TRANSFER, not VERIFIED-CONTROL."
            ),
        )

    if stage0.verdict_at_stage0 == VERDICT_NO_BUTTON_FOUND:
        return E0012Verdict(
            verdict=VERDICT_NO_BUTTON_FOUND,
            stage0=stage0,
            stage1_results=stage1_results,
            winner_candidate=None,
            transfer_detected=False,
            notes="Zero candidates passed Stage 0 cutoff (improvement ≥ δ AND coherence OK).",
        )

    # N-02 fix: BUTTON_FOUND_BUT_UNSAFE requires the Stage 1 adjudicator to have
    # passed (prereg §8: "Stage 1 PASS but ANY of the following safety conditions
    # triggered").  If the adjudicator itself failed, the result is NO_BUTTON_FOUND
    # (or falls through below), not BUTTON_FOUND_BUT_UNSAFE.
    # Exception: cross-axis fail is unconditional per prereg §9.4 operational rule
    # ("regardless of primary calibration adjudication result").
    def _adj_passed_for_result(r: "Stage1CandidateResult") -> bool:
        """Extract raw adjudicator pass from axis_adj_result (stored as a dict)."""
        aaj = r.axis_adj_result
        if aaj is None:
            return False
        if isinstance(aaj, dict):
            return bool(aaj.get("passes", False))
        return bool(getattr(aaj, "passes", False))

    def _qualifies_for_unsafe_verdict(r: "Stage1CandidateResult") -> bool:
        # Cross-axis fail is unconditional (§9.4); accuracy/reliability guards
        # require adjudicator to also have passed (§8).
        return r.safety.cross_axis_fail or _adj_passed_for_result(r)

    unsafe_results = [
        r for r in stage1_results
        if r.safety.button_found_but_unsafe and _qualifies_for_unsafe_verdict(r)
    ]
    if unsafe_results and not any(r.passes for r in stage1_results):
        winner = unsafe_results[0].candidate
        return E0012Verdict(
            verdict=VERDICT_BUTTON_FOUND_BUT_UNSAFE,
            stage0=stage0,
            stage1_results=stage1_results,
            winner_candidate=winner,
            transfer_detected=False,
            notes=(
                "TERMINAL verdict. Stage 1 passed primary adjudication but "
                "safety guards triggered. No upgrade path within E-0012. "
                "Reasons: " + "; ".join(r for sr in unsafe_results for r in sr.safety.reasons)
            ),
        )

    # Stage 1 PASSes
    passing = [r for r in stage1_results if r.passes]
    if not passing:
        return E0012Verdict(
            verdict=VERDICT_NO_BUTTON_FOUND,
            stage0=stage0,
            stage1_results=stage1_results,
            winner_candidate=None,
            transfer_detected=False,
            notes="Stage 1: no candidate passed the frozen adjudicator.",
        )

    winner = passing[0].candidate

    # Stage 2 verdict
    if stage2_dimensions_passed is None:
        # Stage 2 not run → default to LOCAL
        verdict = VERDICT_LOCAL
        notes = (
            "Stage 1 PASS; Stage 2 not run. "
            "Verdict defaulted to LOCAL (model-specific). "
            "Stage 2 required for GENERALIZING or GENERAL_CONTROL."
        )
    elif stage2_dimensions_passed >= 5:
        verdict = VERDICT_GENERAL_CONTROL
        notes = "Stage 1 PASS + all 5 Stage 2 dimensions pass → GENERAL_CONTROL."
    elif stage2_dimensions_passed >= 2:  # model + task at minimum
        verdict = VERDICT_GENERALIZING
        notes = f"Stage 1 PASS + {stage2_dimensions_passed}/5 Stage 2 dimensions → GENERALIZING."
    else:
        verdict = VERDICT_LOCAL
        notes = f"Stage 1 PASS but only {stage2_dimensions_passed}/5 Stage 2 dimensions → LOCAL."

    return E0012Verdict(
        verdict=verdict,
        stage0=stage0,
        stage1_results=stage1_results,
        winner_candidate=winner,
        transfer_detected=False,
        notes=notes,
    )


# --------------------------------------------------------------------------- #
# Full harness runner (synthetic backend)
# --------------------------------------------------------------------------- #
def run_e0012_harness(
    sampler: adj.OutcomeSampler,
    dev_items: Sequence[Dict],
    test_items: Sequence[Dict],
    authored_prompts: Sequence[Tuple[str, str]],
    hidden_dim: int = 16,
    ape_result: Optional[APERunResult] = None,
    axis: str = "uncertainty_awareness",
    raw_store_path: Optional[Path] = None,
    e0006_dev_items: Optional[Sequence[Dict]] = None,
) -> E0012Verdict:
    """Run the full E-0012 harness end-to-end (Stage 0 → Stage 1 → verdict).

    Works with synthetic or real backends.  ``hidden_dim`` is only used for
    synthetic direction derivation (ignored on real GPU).
    """
    raw_store: Optional[BrierRawStore] = None
    if raw_store_path is not None:
        raw_store = BrierRawStore(raw_store_path)

    try:
        # Derive directions for all families × all layers
        directions_by_layer: Dict[int, List[ButtonDirection]] = {}
        for layer in LAYER_SWEEP:
            directions_by_layer[layer] = all_directions_for_layer(
                layer, hidden_dim, e0006_dev_items
            )

        # Stage 0
        stage0 = run_stage0(
            sampler=sampler,
            dev_items=dev_items,
            authored_prompts=authored_prompts,
            directions_by_layer=directions_by_layer,
            ape_result=ape_result,
            axis=axis,
            raw_store=raw_store,
        )

        if stage0.verdict_at_stage0 == VERDICT_NO_BUTTON_FOUND:
            return determine_verdict(stage0, [], None)
        if stage0.kill_rule_result == KILL_RULE_RESULT_TRANSFER:
            return determine_verdict(stage0, [], None)

        # Stage 1: one-shot TEST for each advancing candidate
        stage1_results: List[Stage1CandidateResult] = []
        # H-04: dynamic Bonferroni correction over M=len(advancing) candidates × 1 axis
        # per prereg §4/§7: ci_level = 1 − 0.05 / max(1, M × n_axes=1)
        m = max(1, len(stage0.advancing))
        bonferroni_ci_level = 1.0 - 0.05 / m
        for cand in stage0.advancing:
            layer_dirs = directions_by_layer.get(cand.layer, [])
            dir_map = {bd.family: bd for bd in layer_dirs}
            bd = dir_map.get(cand.button_family)
            direction = bd.direction if bd is not None else np.zeros(hidden_dim)

            result = run_stage1_candidate(
                candidate=cand,
                sampler=sampler,
                test_items=test_items,
                best_prompt_text=stage0.best_prompt_text,
                direction=direction,
                axis=axis,
                raw_store=raw_store,
                bonferroni_ci_level=bonferroni_ci_level,  # H-04
            )
            stage1_results.append(result)

        return determine_verdict(stage0, stage1_results, stage2_dimensions_passed=None)

    finally:
        if raw_store is not None:
            raw_store.close()


# --------------------------------------------------------------------------- #
# Utility: split dev/test for E-0012 pool
# --------------------------------------------------------------------------- #
def split_e0012_pool(
    items: Sequence[Dict],
    split_seed: int = 42,
) -> Tuple[List[Dict], List[Dict]]:
    """Split E-0012 pool into DEV (~1/3) and TEST (~2/3) using the frozen rule."""
    items = list(items)
    ids = [str(it["id"]) for it in items]
    split = adj.split_dev_test(ids, dev_fraction=adj.DEV_FRACTION, seed=split_seed)
    id_to_item = {str(it["id"]): it for it in items}
    dev = [id_to_item[i] for i in split.dev_ids]
    test = [id_to_item[i] for i in split.test_ids]
    return dev, test
