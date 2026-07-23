"""C2b behavioral-gap ADJUDICATION harness — implements prereg §4 EXACTLY.

FROZEN spec: ``docs/ledgers/prereg-c2b-adjudication.md`` (§1 instrument, §2 design,
§4 decision rule, §5 parameters). This module implements the FROZEN, qualified
adjudication of Claim C2b — "on tasks with headroom, latent steering reaches a
BEHAVIORAL outcome beyond the best bounded-prompt outcome" — with a paired,
multiplicity-corrected, three-tier decision rule. The criteria are LOCKED; this
code implements them, it does NOT invent thresholds.

Frozen-criterion -> code map
----------------------------
* α grid {2,4,6,8,12,16,24}         -> ``ALPHA_GRID``                       (§5)
* δ = 0.05                          -> ``DELTA``                            (§5)
* N: delib 60 / skep 60 / unc 80    -> ``N_ITEMS_BY_AXIS``                  (§5)
* k = 5 samples/item                -> ``K_SAMPLES``                        (§5)
* coherence ≤ 1.5× baseline         -> ``COHERENCE_MAX_RATIO`` + gate       (§3/§5)
* cluster bootstrap, B ≥ 10000      -> ``cluster_bootstrap_ci`` (item-level) (§4/§5)
* per-axis CI at 1 − 0.05/3         -> ``BONFERRONI_CI_LEVEL``              (§4/§5)
* DEV ~1/3 selects+freezes α+prompt  -> ``split_dev_test`` + ``select_on_dev`` (§2/§4)
* TEST ~2/3 paired d_i=steer−prompt  -> ``adjudicate_axis`` (frozen α+prompt)  (§2/§4)
* pass iff CI excl 0 AND mean≥δ AND coherence -> ``axis_pass``               (§4)
* ≥2 / 1 / 0 axes pass -> STRONG_GO / CONDITIONAL_GO / KILL_PLAN_D -> ``three_tier_verdict`` (§4)
* conflict cells SECONDARY/descriptive only -> ``AxisAdjResult.conflict``   (§4)

Model-independent: all generation goes through a ``GenBackend`` (real
``SteeredHFBackend`` on the A800, ``SyntheticC2bTaskBackend`` offline) and the
deterministic answer-key scorers in ``eval.scorers``. No torch here.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field, asdict
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

from ..eval import scorers as _scorers
from ..steering.generate import GenBackend, SteerConfig

# --------------------------------------------------------------------------- #
# FROZEN parameters (prereg §5 — LOCKED, do not change after freeze 2026-07-23)
# --------------------------------------------------------------------------- #
ALPHA_GRID: Tuple[float, ...] = (2.0, 4.0, 6.0, 8.0, 12.0, 16.0, 24.0)
DELTA: float = 0.05
K_SAMPLES: int = 5
N_ITEMS_BY_AXIS: Dict[str, int] = {
    "deliberation": 60,
    "skepticism": 60,
    "uncertainty_awareness": 80,
}
COHERENCE_MAX_RATIO: float = 1.5
BOOTSTRAP_B: int = 10000
FAMILYWISE_ALPHA: float = 0.05
N_AXES: int = 3
BONFERRONI_CI_LEVEL: float = 1.0 - FAMILYWISE_ALPHA / N_AXES  # ≈ 0.98333...
DEV_FRACTION: float = 1.0 / 3.0

VERDICT_STRONG_GO = "STRONG_GO"
VERDICT_CONDITIONAL_GO = "CONDITIONAL_GO"
VERDICT_KILL = "KILL_PLAN_D"

# Which per-item outcome the paired bootstrap consumes per axis.
BINARY_OUTCOME_AXES = {"deliberation", "skepticism"}
CALIBRATION_OUTCOME_AXES = {"uncertainty_awareness"}


# --------------------------------------------------------------------------- #
# DEV/TEST split (prereg §2/§4 — ~1/3 DEV selection, disjoint ~2/3 TEST)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class DevTestSplit:
    dev_ids: List[str]
    test_ids: List[str]

    def __post_init__(self):
        overlap = set(self.dev_ids) & set(self.test_ids)
        if overlap:
            raise ValueError(f"DEV/TEST leakage: {sorted(overlap)}")


def split_dev_test(item_ids: Sequence[str], dev_fraction: float = DEV_FRACTION,
                   seed: int = 0) -> DevTestSplit:
    """Disjoint DEV (~dev_fraction) / TEST split with a fixed seed (deterministic).

    DEV is used ONLY to select+freeze the best-of-16 prompt and the best α; TEST
    is the disjoint adjudication pool. At least one item goes to each side.
    """
    ids = sorted(str(i) for i in item_ids)
    n = len(ids)
    if n < 2:
        raise ValueError("need at least 2 items to form a DEV/TEST split")
    rng = np.random.default_rng(seed)
    order = rng.permutation(n)
    shuffled = [ids[i] for i in order]
    n_dev = int(round(dev_fraction * n))
    n_dev = max(1, min(n_dev, n - 1))
    dev = sorted(shuffled[:n_dev])
    test = sorted(shuffled[n_dev:])
    return DevTestSplit(dev_ids=dev, test_ids=test)


# --------------------------------------------------------------------------- #
# Paired ITEM-cluster bootstrap (prereg §4 — resample ITEMS, each carries its k)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class BootstrapCI:
    point: float
    ci_lo: float
    ci_hi: float
    ci_level: float
    b: int
    cluster: bool

    def excludes_zero(self) -> bool:
        return ci_excludes_zero(self.ci_lo, self.ci_hi)


def ci_excludes_zero(ci_lo: float, ci_hi: float) -> bool:
    """True iff 0 is NOT in the closed interval [ci_lo, ci_hi]."""
    return not (ci_lo <= 0.0 <= ci_hi)


def cluster_bootstrap_ci(
    item_samples,
    b: int = BOOTSTRAP_B,
    ci_level: float = BONFERRONI_CI_LEVEL,
    seed: int = 0,
    cluster: bool = True,
) -> BootstrapCI:
    """Two-sided percentile bootstrap CI of the mean of per-item paired diffs.

    ``item_samples`` is either a 1-D array of per-item diffs ``d_i`` (one value
    per item / cluster) or a 2-D ``[n_items, k]`` array of per-sample values whose
    row means are the per-item diffs. Frozen behaviour (§4):

    * ``cluster=True`` (the pre-registered mode): resample ITEMS with replacement
      (each item carries ALL its k samples), statistic = mean over resampled items
      of their row means. This respects the k-sample nesting.
    * ``cluster=False`` (for the audit test only): pool all n*k sample values and
      resample at the SAMPLE level, breaking the item clustering — used to
      demonstrate the two give different CIs when k>1.

    Returns the point estimate (identical for both modes with balanced k) and the
    percentile CI at ``ci_level`` (default the Bonferroni 1 − 0.05/3).
    """
    arr = np.asarray(item_samples, dtype=np.float64)
    if arr.ndim == 1:
        arr = arr[:, None]
    if arr.ndim != 2:
        raise ValueError("item_samples must be 1-D [n] or 2-D [n, k]")
    n, k = arr.shape
    if n < 1:
        raise ValueError("need at least one item")
    if b < 1:
        raise ValueError("b (bootstrap resamples) must be >= 1")
    if not (0.0 < ci_level < 1.0):
        raise ValueError("ci_level must be in (0, 1)")
    rng = np.random.default_rng(seed)
    row_means = arr.mean(axis=1)  # per-item diff d_i

    if cluster:
        idx = rng.integers(0, n, size=(b, n))
        boot = row_means[idx].mean(axis=1)
        point = float(row_means.mean())
    else:
        flat = arr.reshape(-1)
        m = flat.size
        idx = rng.integers(0, m, size=(b, m))
        boot = flat[idx].mean(axis=1)
        point = float(flat.mean())

    lo_pct = 100.0 * (1.0 - ci_level) / 2.0
    hi_pct = 100.0 * (1.0 + ci_level) / 2.0
    ci_lo = float(np.percentile(boot, lo_pct))
    ci_hi = float(np.percentile(boot, hi_pct))
    return BootstrapCI(point=point, ci_lo=ci_lo, ci_hi=ci_hi,
                       ci_level=ci_level, b=int(b), cluster=cluster)


# --------------------------------------------------------------------------- #
# Per-axis pass rule + three-tier verdict (prereg §4)
# --------------------------------------------------------------------------- #
def axis_pass(mean_d: float, ci_lo: float, ci_hi: float, coherence_ok: bool,
              delta: float = DELTA) -> bool:
    """An axis PASSES (Bonferroni-corrected) iff ALL of (§4):
    (i) the CI of mean(d) EXCLUDES 0, (ii) mean(d) >= δ, (iii) coherence gate ok."""
    return bool(ci_excludes_zero(ci_lo, ci_hi) and (mean_d >= delta) and coherence_ok)


def three_tier_verdict(axis_passes: Dict[str, bool]) -> str:
    """Map the per-axis pass flags to the frozen three-tier verdict (§4):
    ≥2 pass -> STRONG_GO; exactly 1 -> CONDITIONAL_GO (single-axis replication
    required); 0 -> KILL_PLAN_D."""
    n_pass = sum(1 for v in axis_passes.values() if v)
    if n_pass >= 2:
        return VERDICT_STRONG_GO
    if n_pass == 1:
        return VERDICT_CONDITIONAL_GO
    return VERDICT_KILL


# --------------------------------------------------------------------------- #
# Outcome sampler seam (model-independent)
# --------------------------------------------------------------------------- #
@dataclass
class SampleBatch:
    """k per-sample outcomes in [0,1] plus their degeneracy scores for one cell."""
    outcomes: List[float]
    degeneracies: List[float]

    def mean_outcome(self) -> float:
        return float(np.mean(self.outcomes))

    def mean_degeneracy(self) -> float:
        return float(np.mean(self.degeneracies))


class OutcomeSampler(abc.ABC):
    """Produces k scored samples for one (item, channel) cell — the deferred seam."""

    @abc.abstractmethod
    def sample(self, axis: str, item: Dict, instruction: str, alpha: float,
               k: int, direction: np.ndarray, layer: int) -> SampleBatch:
        """Return a SampleBatch of k outcome+degeneracy scores for the cell."""


def format_task_input(axis: str, instruction: str, item: Dict) -> str:
    """Build the model input: instruction + task question (+ MC options / answer
    format cue). The instruction is the DEV-selected best prompt (prompt channel)
    or the neutral prompt (steer channel)."""
    q = str(item.get("prompt", "")).strip()
    lines = [instruction.strip(), q]
    choices = item.get("choices")
    if choices:
        opts = "\n".join(f"{ell}) {txt}" for ell, txt in choices.items())
        lines.append("Options:\n" + opts + "\n\nAnswer with the letter of the best option.")
    if axis == "deliberation":
        lines.append("Give the final numeric answer.")
    elif axis == "uncertainty_awareness":
        lines.append('End with: Answer: <your answer>. Confidence: <0-100>%.')
    return "\n\n".join(ln for ln in lines if ln)


def score_sample_outcome(axis: str, item: Dict, text: str) -> float:
    """Per-sample OUTCOME in [0,1] via the frozen answer-key scorers (§1)."""
    if axis == "deliberation":
        return float(_scorers.score_deliberation(text, item))
    if axis == "skepticism":
        return float(_scorers.score_skepticism(text, item))
    if axis == "uncertainty_awareness":
        correct = _scorers.item_is_correct(item, text)
        conf = _scorers.parse_confidence(text)
        if conf is None:
            conf = 0.5  # no stated confidence -> maximally uninformative prior
        return _scorers.per_item_calibration_score(correct, conf)
    raise ValueError(f"unknown axis {axis!r}")


class BackendOutcomeSampler(OutcomeSampler):
    """Wires a ``GenBackend`` + the frozen scorers into the adjudication harness.

    For each of k samples it generates a response to the formatted task input
    (steered at ``alpha`` on ``layer`` along ``direction``) and scores the outcome
    with the answer-key scorer plus a degeneracy score for the coherence gate.
    Sampling (``do_sample``) is used when k>1 so the k samples vary; with a greedy
    backend (or the synthetic offline backend) the k samples may coincide.
    """

    def __init__(self, gen_backend: GenBackend, max_new_tokens: int = 256,
                 do_sample: bool = True, temperature: float = 0.7):
        if not isinstance(gen_backend, GenBackend):
            raise TypeError("gen_backend must be a GenBackend")
        self.gen = gen_backend
        self.max_new_tokens = int(max_new_tokens)
        self.do_sample = bool(do_sample)
        self.temperature = float(temperature)

    def sample(self, axis: str, item: Dict, instruction: str, alpha: float,
               k: int, direction: np.ndarray, layer: int) -> SampleBatch:
        text_input = format_task_input(axis, instruction, item)
        steer = SteerConfig(direction=direction, alpha=float(alpha), layer=int(layer))
        outcomes: List[float] = []
        degens: List[float] = []
        for _ in range(int(k)):
            try:
                out = self.gen.generate(text_input, steer, self.max_new_tokens,
                                        do_sample=self.do_sample, temperature=self.temperature)
            except TypeError:
                # Synthetic backends ignore sampling kwargs.
                out = self.gen.generate(text_input, steer, self.max_new_tokens)
            outcomes.append(score_sample_outcome(axis, item, out))
            degens.append(_scorers.degeneracy_score(out))
        return SampleBatch(outcomes=outcomes, degeneracies=degens)


# --------------------------------------------------------------------------- #
# Per-axis adjudication
# --------------------------------------------------------------------------- #
@dataclass
class AxisAdjSpec:
    """Per-axis inputs to the adjudication (prereg §2)."""
    axis: str
    items: List[Dict]                        # each: id, prompt/question, answer key
    strong_prompts: List[Tuple[str, str]]    # up to 16 (prompt_id, instruction)
    neutral_prompt: str                      # steer-channel instruction
    direction: np.ndarray                    # unit CAA direction (C1 re-derived)
    layer: int                               # C1 chosen non-degenerate layer


@dataclass
class DevSelection:
    """What DEV froze: the best-of-16 prompt and the coherence-gated best α."""
    best_prompt_id: str
    best_prompt_text: str
    dev_prompt_outcome: float
    frozen_alpha: Optional[float]
    dev_steer_outcome: Optional[float]
    baseline_degeneracy: float
    alpha_grid: List[Dict[str, object]]      # per-α: outcome, degeneracy, coherence_ok
    any_alpha_passes_gate: bool


def _channel_item_outcomes(
    sampler: OutcomeSampler, axis: str, items: Sequence[Dict], instruction: str,
    alpha: float, k: int, direction: np.ndarray, layer: int,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (per_item_outcome[n], per_item_degeneracy[n], per_sample_outcomes[n,k])."""
    outs: List[float] = []
    degs: List[float] = []
    mat: List[List[float]] = []
    for it in items:
        batch = sampler.sample(axis, it, instruction, alpha, k, direction, layer)
        outs.append(batch.mean_outcome())
        degs.append(batch.mean_degeneracy())
        mat.append(list(batch.outcomes))
    return np.asarray(outs), np.asarray(degs), np.asarray(mat)


def select_on_dev(
    sampler: OutcomeSampler, spec: AxisAdjSpec, dev_items: Sequence[Dict],
    k: int = K_SAMPLES, alpha_grid: Sequence[float] = ALPHA_GRID,
    coherence_max_ratio: float = COHERENCE_MAX_RATIO,
) -> DevSelection:
    """Select+FREEZE, ON DEV ONLY, the best-of-16 prompt and the best coherence-
    gated α (prereg §4 step 2). No TEST item is touched here (no leakage).

    * best prompt = the strong prompt with the highest DEV prompt-channel outcome.
    * baseline degeneracy = unsteered (α=0) neutral-prompt mean degeneracy on DEV.
    * α selection = among grid α whose DEV steer-only mean degeneracy ≤ 1.5× the
      baseline (coherence gate), pick the one with the highest DEV steer outcome.
    """
    # --- best-of-16 prompt (DEV prompt channel, unsteered) ---
    best_pid, best_ptext, best_pout = None, None, -np.inf
    for pid, ptext in spec.strong_prompts:
        outs, _, _ = _channel_item_outcomes(
            sampler, spec.axis, dev_items, ptext, 0.0, k, spec.direction, spec.layer)
        val = float(outs.mean())
        if val > best_pout:
            best_pid, best_ptext, best_pout = pid, ptext, val

    # --- unsteered baseline degeneracy (neutral prompt, α=0) on DEV ---
    _, base_deg, _ = _channel_item_outcomes(
        sampler, spec.axis, dev_items, spec.neutral_prompt, 0.0, k, spec.direction, spec.layer)
    baseline_degeneracy = float(base_deg.mean())
    gate_ceiling = coherence_max_ratio * baseline_degeneracy

    # --- α grid on DEV steer-only (neutral prompt, coherence-gated) ---
    grid_rows: List[Dict[str, object]] = []
    frozen_alpha: Optional[float] = None
    best_steer_out: Optional[float] = None
    for a in alpha_grid:
        outs, degs, _ = _channel_item_outcomes(
            sampler, spec.axis, dev_items, spec.neutral_prompt, float(a), k,
            spec.direction, spec.layer)
        steer_out = float(outs.mean())
        steer_deg = float(degs.mean())
        coherence_ok = steer_deg <= gate_ceiling + 1e-12
        grid_rows.append({
            "alpha": float(a), "dev_steer_outcome": steer_out,
            "degeneracy": steer_deg, "coherence_ok": coherence_ok,
        })
        if coherence_ok and (best_steer_out is None or steer_out > best_steer_out):
            best_steer_out = steer_out
            frozen_alpha = float(a)

    return DevSelection(
        best_prompt_id=str(best_pid), best_prompt_text=str(best_ptext),
        dev_prompt_outcome=float(best_pout), frozen_alpha=frozen_alpha,
        dev_steer_outcome=best_steer_out, baseline_degeneracy=baseline_degeneracy,
        alpha_grid=grid_rows, any_alpha_passes_gate=frozen_alpha is not None,
    )


@dataclass
class AxisAdjResult:
    axis: str
    layer: int
    n_dev: int
    n_test: int
    k: int
    dev_selection: Dict[str, object]
    # TEST (frozen prompt + frozen α)
    per_item_prompt: List[float]
    per_item_steer: List[float]
    per_item_diff: List[float]
    mean_diff: float
    ci_lo: float
    ci_hi: float
    ci_level: float
    bootstrap_b: int
    coherence_ok: bool
    test_steer_degeneracy: float
    test_baseline_degeneracy: float
    delta: float
    passed: bool
    # SECONDARY / descriptive
    conflict: Dict[str, object]
    descriptive: Dict[str, object]

    def to_row(self) -> Dict[str, object]:
        return asdict(self)


def adjudicate_axis(
    sampler: OutcomeSampler, spec: AxisAdjSpec, *,
    k: int = K_SAMPLES, alpha_grid: Sequence[float] = ALPHA_GRID,
    bootstrap_b: int = BOOTSTRAP_B, ci_level: float = BONFERRONI_CI_LEVEL,
    delta: float = DELTA, coherence_max_ratio: float = COHERENCE_MAX_RATIO,
    dev_fraction: float = DEV_FRACTION, seed: int = 0,
) -> AxisAdjResult:
    """Full FROZEN adjudication for ONE axis (prereg §4 steps 1-7).

    1. DEV/TEST split (disjoint, fixed seed).
    2. DEV: freeze best-of-16 prompt + best coherence-gated α.
    3. TEST: per item, prompt_i (frozen prompt, α=0) & steer_i (frozen α),
       paired diff d_i = steer_i − prompt_i (k-sample means).
    4. Paired ITEM-cluster bootstrap CI of mean(d) at the Bonferroni level.
    5. Coherence gate on the winning steer cell (TEST).
    6. Axis pass iff CI excludes 0 AND mean(d) ≥ δ AND coherence ok.
    7. Conflict cell computed as SECONDARY/descriptive only.
    """
    ids = [str(it["id"]) for it in spec.items]
    by_id = {str(it["id"]): it for it in spec.items}
    split = split_dev_test(ids, dev_fraction=dev_fraction, seed=seed)
    dev_items = [by_id[i] for i in split.dev_ids]
    test_items = [by_id[i] for i in split.test_ids]

    dev_sel = select_on_dev(sampler, spec, dev_items, k=k, alpha_grid=alpha_grid,
                            coherence_max_ratio=coherence_max_ratio)

    frozen_alpha = dev_sel.frozen_alpha
    # If NO α cleared the DEV coherence gate, the axis has no valid steer cell:
    # it cannot pass (§4 iii). Report an honest non-pass with an empty steer cell.
    if frozen_alpha is None:
        n_test = len(test_items)
        prompt_out, _, _ = _channel_item_outcomes(
            sampler, spec.axis, test_items, dev_sel.best_prompt_text, 0.0, k,
            spec.direction, spec.layer)
        return AxisAdjResult(
            axis=spec.axis, layer=int(spec.layer), n_dev=len(dev_items), n_test=n_test,
            k=int(k), dev_selection=asdict(dev_sel),
            per_item_prompt=[float(x) for x in prompt_out],
            per_item_steer=[], per_item_diff=[],
            mean_diff=float("nan"), ci_lo=float("nan"), ci_hi=float("nan"),
            ci_level=ci_level, bootstrap_b=int(bootstrap_b), coherence_ok=False,
            test_steer_degeneracy=float("nan"),
            test_baseline_degeneracy=dev_sel.baseline_degeneracy,
            delta=delta, passed=False,
            conflict={"note": "no coherence-gated α; conflict not computed"},
            descriptive={"reason": "no α cleared the DEV coherence gate"},
        )

    # --- TEST: prompt channel (frozen prompt, α=0) & steer channel (frozen α) ---
    prompt_out, _, prompt_mat = _channel_item_outcomes(
        sampler, spec.axis, test_items, dev_sel.best_prompt_text, 0.0, k,
        spec.direction, spec.layer)
    steer_out, steer_deg, steer_mat = _channel_item_outcomes(
        sampler, spec.axis, test_items, spec.neutral_prompt, frozen_alpha, k,
        spec.direction, spec.layer)
    _, base_deg_test, _ = _channel_item_outcomes(
        sampler, spec.axis, test_items, spec.neutral_prompt, 0.0, k,
        spec.direction, spec.layer)

    per_item_diff = steer_out - prompt_out
    ci = cluster_bootstrap_ci(per_item_diff, b=bootstrap_b, ci_level=ci_level,
                              seed=seed, cluster=True)

    test_baseline_deg = float(base_deg_test.mean())
    test_steer_deg = float(steer_deg.mean())
    coherence_ok = test_steer_deg <= coherence_max_ratio * test_baseline_deg + 1e-12

    passed = axis_pass(ci.point, ci.ci_lo, ci.ci_hi, coherence_ok, delta=delta)

    conflict = _conflict_cell(sampler, spec, test_items, dev_sel.best_prompt_text,
                              frozen_alpha, k)
    descriptive = _descriptive(spec.axis, test_items, prompt_mat, steer_mat)

    return AxisAdjResult(
        axis=spec.axis, layer=int(spec.layer), n_dev=len(dev_items),
        n_test=len(test_items), k=int(k), dev_selection=asdict(dev_sel),
        per_item_prompt=[float(x) for x in prompt_out],
        per_item_steer=[float(x) for x in steer_out],
        per_item_diff=[float(x) for x in per_item_diff],
        mean_diff=ci.point, ci_lo=ci.ci_lo, ci_hi=ci.ci_hi, ci_level=ci.ci_level,
        bootstrap_b=int(bootstrap_b), coherence_ok=coherence_ok,
        test_steer_degeneracy=test_steer_deg,
        test_baseline_degeneracy=test_baseline_deg,
        delta=delta, passed=passed, conflict=conflict, descriptive=descriptive,
    )


def _conflict_cell(sampler: OutcomeSampler, spec: AxisAdjSpec, test_items: Sequence[Dict],
                   best_prompt_text: str, frozen_alpha: float, k: int) -> Dict[str, object]:
    """SECONDARY/descriptive only (§4): best pro-axis prompt UP vs latent steer the
    OPPOSITE way (−α). Reports which channel the behavior lands nearer. NOT part of
    the pass/fail verdict."""
    conf_out, _, _ = _channel_item_outcomes(
        sampler, spec.axis, test_items, best_prompt_text, -float(frozen_alpha), k,
        spec.direction, spec.layer)
    prompt_pole, _, _ = _channel_item_outcomes(
        sampler, spec.axis, test_items, best_prompt_text, 0.0, k,
        spec.direction, spec.layer)
    return {
        "note": "SECONDARY/descriptive only — NOT part of the verdict (prereg §4).",
        "alpha_opposite": -float(frozen_alpha),
        "mean_conflict_outcome": float(conf_out.mean()),
        "mean_prompt_pole_outcome": float(prompt_pole.mean()),
        "latent_drags_down": float(conf_out.mean()) < float(prompt_pole.mean()),
    }


def _descriptive(axis: str, test_items: Sequence[Dict],
                 prompt_mat: np.ndarray, steer_mat: np.ndarray) -> Dict[str, object]:
    """Descriptive extras (e.g. binned set ECE for uncertainty) reported alongside
    the frozen per-item outcome — never used in the verdict."""
    d: Dict[str, object] = {}
    if axis in CALIBRATION_OUTCOME_AXES:
        d["set_ece_note"] = (
            "Per-item outcome is 1-|correct-conf| (prereg-ambiguity resolution "
            "flagged for Manager); binned set ECE is descriptive only."
        )
    return d


# --------------------------------------------------------------------------- #
# Whole-adjudication driver (all axes -> three-tier verdict)
# --------------------------------------------------------------------------- #
@dataclass
class AdjudicationReport:
    axis_results: List[AxisAdjResult]
    axis_passes: Dict[str, bool]
    verdict: str
    frozen_params: Dict[str, object]

    def to_dict(self) -> Dict[str, object]:
        return {
            "verdict": self.verdict,
            "axis_passes": self.axis_passes,
            "frozen_params": self.frozen_params,
            "axes": [r.to_row() for r in self.axis_results],
        }


def frozen_params_dict() -> Dict[str, object]:
    return {
        "alpha_grid": list(ALPHA_GRID),
        "delta": DELTA,
        "k_samples": K_SAMPLES,
        "n_items_by_axis": dict(N_ITEMS_BY_AXIS),
        "coherence_max_ratio": COHERENCE_MAX_RATIO,
        "bootstrap_b": BOOTSTRAP_B,
        "familywise_alpha": FAMILYWISE_ALPHA,
        "n_axes": N_AXES,
        "bonferroni_ci_level": BONFERRONI_CI_LEVEL,
        "dev_fraction": DEV_FRACTION,
        "bootstrap": "paired item-cluster (resample items, each carries its k)",
        "decision": "CI excludes 0 AND mean(d) >= delta AND coherence gate pass",
        "verdict_rule": ">=2 pass STRONG_GO; ==1 CONDITIONAL_GO; 0 KILL_PLAN_D",
        "prereg": "docs/ledgers/prereg-c2b-adjudication.md (FROZEN 2026-07-23)",
    }


def adjudicate(
    sampler_for_axis: Callable[[str], OutcomeSampler],
    specs: Sequence[AxisAdjSpec], *,
    k: int = K_SAMPLES, alpha_grid: Sequence[float] = ALPHA_GRID,
    bootstrap_b: int = BOOTSTRAP_B, ci_level: float = BONFERRONI_CI_LEVEL,
    delta: float = DELTA, coherence_max_ratio: float = COHERENCE_MAX_RATIO,
    dev_fraction: float = DEV_FRACTION, seed: int = 0,
) -> AdjudicationReport:
    """Run the FROZEN adjudication over all axis specs and emit the three-tier
    verdict (§4). ``sampler_for_axis`` returns the OutcomeSampler for an axis (one
    shared real backend, or a per-axis synthetic backend in tests)."""
    results: List[AxisAdjResult] = []
    passes: Dict[str, bool] = {}
    for spec in specs:
        sampler = sampler_for_axis(spec.axis)
        res = adjudicate_axis(
            sampler, spec, k=k, alpha_grid=alpha_grid, bootstrap_b=bootstrap_b,
            ci_level=ci_level, delta=delta, coherence_max_ratio=coherence_max_ratio,
            dev_fraction=dev_fraction, seed=seed)
        results.append(res)
        passes[spec.axis] = res.passed
    verdict = three_tier_verdict(passes)
    return AdjudicationReport(axis_results=results, axis_passes=passes,
                              verdict=verdict, frozen_params=frozen_params_dict())
