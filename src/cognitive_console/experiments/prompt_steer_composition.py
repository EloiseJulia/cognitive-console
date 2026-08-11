"""Preregistered prompt-plus-steer composition design.

This module is additive: it does not modify the frozen C2 substitution
adjudicator or its results.  It reuses C2 task scorers, prompt candidates,
steering settings, checkpoint machinery, and item-cluster bootstrap while
estimating a four-condition factorial:

    N  = neutral / no steer
    P  = DEV-selected bounded prompt / no steer
    S  = neutral / DEV-selected steer
    PS = the same selected prompt + the same selected steer

The primary estimand is PS - P: incremental slider value over the prompt.
The factorial interaction is (PS - P) - (S - N).
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

from . import adjudicate_c2b as c2

PROTOCOL_ID = "E-0017-prompt-steer-composition-v1"
FROZEN_MODEL = "Qwen/Qwen2.5-7B-Instruct"
FROZEN_MODEL_REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"
FROZEN_METHOD = "caa"
AXES: Tuple[str, ...] = (
    "deliberation",
    "skepticism",
    "uncertainty_awareness",
)

SEED = 20260811
ORIGINAL_C2_SEED = 20260723
DEV_N = 96
TEST_MIN_N: Dict[str, int] = {
    "deliberation": 128,
    "skepticism": 256,
    "uncertainty_awareness": 256,
}
TEST_MAX_N: Dict[str, int] = {
    "deliberation": 384,
    "skepticism": 680,
    "uncertainty_awareness": 1024,
}

ALPHA_GRID = c2.ALPHA_GRID
K_SAMPLES = c2.K_SAMPLES
DELTA = c2.DELTA
COHERENCE_MAX_RATIO = c2.COHERENCE_MAX_RATIO
COHERENCE_EPS_FLOOR = c2.COHERENCE_EPS_FLOOR
BOOTSTRAP_B = c2.BOOTSTRAP_B
FAMILYWISE_ALPHA = 0.05
PRIMARY_FAMILY_SIZE = len(AXES)
PRIMARY_CI_LEVEL = 1.0 - FAMILYWISE_ALPHA / PRIMARY_FAMILY_SIZE
INTERACTION_CI_LEVEL = PRIMARY_CI_LEVEL
EQUIVALENCE_CI_LEVEL = 0.90
INTERACTION_SCOPE = (
    "Registered secondary factorial diagnostic scoped to the tested Qwen CAA "
    "cell. It does not establish prompt-plus-steer utility when the primary "
    "prompt_steer - prompt estimand fails."
)

POWER_TARGET = 0.80
POWER_INFLATION = 1.20
Z_PRIMARY = 2.3944  # two-sided 98.33% CI, matching the frozen three-axis family
Z_POWER80 = 0.8416
POWER_ROUND_TO = 8

# Planning lower bounds from the canonical CAA x Qwen E-0006 item-level
# substitution differences.  DEV can increase, but never decrease, these SDs.
PRIOR_SD_FLOOR: Dict[str, float] = {
    "deliberation": 0.14597154622628447,
    "skepticism": 0.367388566744202,
    "uncertainty_awareness": 0.4403960139219864,
}

PARSE_RATE_MIN: Dict[str, float] = {
    "deliberation": 0.95,
    "skepticism": 0.95,
    "uncertainty_awareness": 0.80,
}
TRUNCATION_RATE_MAX = 0.05
FROZEN_BATCH_SIZE = 16
FROZEN_RETRY_BUDGET = 1
FROZEN_DISK_BUDGET_GB = 60.0
FROZEN_DISK_CEILING_GB = 70.0
FROZEN_STALL_TIMEOUT_SECONDS = 600.0

PHASE_DEV_PROMPT = "composition_dev_prompt"
PHASE_DEV_NEUTRAL = "composition_dev_neutral"
PHASE_DEV_STEER = "composition_dev_steer"
PHASE_DEV_COMPOSED = "composition_dev_prompt_steer"
PHASE_TEST_NEUTRAL = "composition_test_neutral"
PHASE_TEST_PROMPT = "composition_test_prompt"
PHASE_TEST_STEER = "composition_test_steer"
PHASE_TEST_COMPOSED = "composition_test_prompt_steer"

DiagnosticsFn = Callable[
    [str, str, str, Sequence[Dict], int],
    Dict[str, object],
]


def padded_batch_count(
    item_count: int,
    *,
    cells: int,
    k: int = K_SAMPLES,
    batch_size: int = FROZEN_BATCH_SIZE,
) -> int:
    items_per_batch = max(1, int(batch_size) // max(1, int(k)))
    return int(cells) * int(math.ceil(int(item_count) / items_per_batch))


def worst_case_compute_plan() -> Dict[str, int]:
    dev_cells = 16 + 1 + 2 * len(ALPHA_GRID)
    dev_generations = len(AXES) * DEV_N * K_SAMPLES * dev_cells
    test_items = sum(TEST_MAX_N.values())
    test_generations = 4 * K_SAMPLES * test_items
    dev_batches = len(AXES) * padded_batch_count(DEV_N, cells=dev_cells)
    test_batches = sum(
        padded_batch_count(n, cells=4) for n in TEST_MAX_N.values()
    )
    logical_generations = dev_generations + test_generations
    return {
        "dev_logical_generations": int(dev_generations),
        "test_logical_generations": int(test_generations),
        "total_logical_generations": int(logical_generations),
        "dev_padded_batches": int(dev_batches),
        "test_padded_batches": int(test_batches),
        "total_padded_batches": int(dev_batches + test_batches),
        "retry_budget_per_backend_call": FROZEN_RETRY_BUDGET,
        "max_physical_generations": int(
            logical_generations * (FROZEN_RETRY_BUDGET + 1)
        ),
    }


def canonical_hash(value: object) -> str:
    blob = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(blob).hexdigest()


def item_data_hash(items: Sequence[Dict]) -> str:
    rows = sorted((dict(row) for row in items), key=lambda row: str(row.get("id")))
    return canonical_hash(rows)


def _axis_seed(axis: str, seed: int) -> int:
    slug = int(hashlib.sha256(axis.encode("utf-8")).hexdigest()[:8], 16)
    return int(seed) + slug % 1_000_000


@dataclass
class PoolPlan:
    axis: str
    dev_items: List[Dict]
    test_reservoir: List[Dict]
    original_dev_ids: List[str]
    original_test_ids: List[str]
    fresh_dev_ids: List[str]
    data_hash: str

    def to_dict(self) -> Dict[str, object]:
        return {
            "axis": self.axis,
            "dev_item_ids": [str(row["id"]) for row in self.dev_items],
            "test_reservoir_ids": [str(row["id"]) for row in self.test_reservoir],
            "original_dev_ids": list(self.original_dev_ids),
            "original_test_ids": list(self.original_test_ids),
            "fresh_dev_ids": list(self.fresh_dev_ids),
            "data_hash": self.data_hash,
        }


def build_confirmatory_pool(
    axis: str,
    items: Sequence[Dict],
    *,
    dev_n: int = DEV_N,
    test_max_n: Optional[int] = None,
    seed: int = SEED,
    original_seed: int = ORIGINAL_C2_SEED,
) -> PoolPlan:
    """Build a leakage-safe pool.

    The original C2 TEST items are excluded completely. Original C2 DEV items may
    be reused only in the new DEV set. Every new TEST item is outside the entire
    original C2 first-N pool, so the composition TEST remains genuinely unseen.
    """
    if axis not in AXES:
        raise ValueError(f"unsupported composition axis: {axis!r}")
    rows = list(items)
    ids = [str(row.get("id", "")) for row in rows]
    if any(not item_id for item_id in ids):
        raise ValueError(f"{axis}: every item needs a non-empty id")
    if len(ids) != len(set(ids)):
        raise ValueError(f"{axis}: duplicate item ids")

    original_n = int(c2.N_ITEMS_BY_AXIS[axis])
    if len(rows) < original_n:
        raise ValueError(
            f"{axis}: pool has {len(rows)} items, fewer than original C2 N={original_n}"
        )
    original_rows = rows[:original_n]
    original_by_id = {str(row["id"]): row for row in original_rows}
    original_split = c2.split_dev_test(
        list(original_by_id), dev_fraction=c2.DEV_FRACTION, seed=original_seed
    )
    old_dev = [original_by_id[item_id] for item_id in original_split.dev_ids]
    if dev_n < len(old_dev):
        raise ValueError(
            f"{axis}: dev_n={dev_n} cannot retain original DEV count={len(old_dev)}"
        )

    fresh_rows = rows[original_n:]
    rng = np.random.default_rng(_axis_seed(axis, seed))
    order = rng.permutation(len(fresh_rows)).tolist()
    shuffled_fresh = [fresh_rows[i] for i in order]
    fresh_dev_count = int(dev_n) - len(old_dev)
    max_test = int(TEST_MAX_N[axis] if test_max_n is None else test_max_n)
    required = fresh_dev_count + max_test
    if len(shuffled_fresh) < required:
        raise ValueError(
            f"{axis}: need {required} post-C2 fresh items "
            f"({fresh_dev_count} DEV + {max_test} TEST reservoir), "
            f"found {len(shuffled_fresh)}"
        )

    fresh_dev = shuffled_fresh[:fresh_dev_count]
    test_reservoir = shuffled_fresh[fresh_dev_count:required]
    dev_items = old_dev + fresh_dev
    dev_ids = {str(row["id"]) for row in dev_items}
    test_ids = {str(row["id"]) for row in test_reservoir}
    original_test_ids = set(original_split.test_ids)
    original_pool_ids = set(original_by_id)
    if dev_ids & original_test_ids:
        raise ValueError(f"{axis}: original C2 TEST leaked into composition DEV")
    if test_ids & original_pool_ids:
        raise ValueError(f"{axis}: original C2 pool leaked into composition TEST")
    if dev_ids & test_ids:
        raise ValueError(f"{axis}: composition DEV/TEST overlap")

    return PoolPlan(
        axis=axis,
        dev_items=dev_items,
        test_reservoir=test_reservoir,
        original_dev_ids=list(original_split.dev_ids),
        original_test_ids=list(original_split.test_ids),
        fresh_dev_ids=[str(row["id"]) for row in fresh_dev],
        data_hash=item_data_hash(dev_items + test_reservoir),
    )


def build_smoke_pool(
    axis: str,
    items: Sequence[Dict],
    *,
    dev_n: int = 4,
    test_n: int = 6,
    seed: int = SEED,
) -> PoolPlan:
    rows = list(items)
    if len(rows) < dev_n + test_n:
        raise ValueError(
            f"{axis}: smoke pool needs {dev_n + test_n} items, found {len(rows)}"
        )
    rng = np.random.default_rng(_axis_seed(axis, seed))
    chosen = [rows[i] for i in rng.permutation(len(rows)).tolist()[: dev_n + test_n]]
    dev_items = chosen[:dev_n]
    test_items = chosen[dev_n:]
    return PoolPlan(
        axis=axis,
        dev_items=dev_items,
        test_reservoir=test_items,
        original_dev_ids=[],
        original_test_ids=[],
        fresh_dev_ids=[str(row["id"]) for row in dev_items],
        data_hash=item_data_hash(chosen),
    )


def _ceil_multiple(value: float, multiple: int = POWER_ROUND_TO) -> int:
    return int(math.ceil(float(value) / int(multiple)) * int(multiple))


def plan_test_n(
    axis: str,
    dev_primary_diffs: Sequence[float],
    *,
    smoke: bool = False,
    smoke_test_n: Optional[int] = None,
) -> Dict[str, object]:
    arr = np.asarray(dev_primary_diffs, dtype=np.float64)
    if arr.ndim != 1 or arr.size < 2 or not np.all(np.isfinite(arr)):
        return {
            "eligible": False,
            "reason": "DEV primary differences are missing, non-finite, or N<2",
            "n_test": None,
        }
    observed_sd = float(np.std(arr, ddof=1))
    sd_floor = float(PRIOR_SD_FLOOR[axis])
    sd_plan = max(observed_sd, sd_floor)
    if smoke:
        n_test = int(smoke_test_n if smoke_test_n is not None else arr.size)
        return {
            "eligible": True,
            "reason": "synthetic smoke bypasses confirmatory power gate",
            "n_test": n_test,
            "observed_dev_sd": observed_sd,
            "prior_sd_floor": sd_floor,
            "planning_sd": sd_plan,
            "raw_required_n": n_test,
            "inflation": None,
            "target_power": None,
            "confirmatory": False,
        }

    raw = POWER_INFLATION * (
        ((Z_PRIMARY + Z_POWER80) * sd_plan / DELTA) ** 2
    )
    required = _ceil_multiple(raw)
    selected = max(int(TEST_MIN_N[axis]), required)
    cap = int(TEST_MAX_N[axis])
    eligible = selected <= cap
    return {
        "eligible": bool(eligible),
        "reason": (
            "powered within frozen cap"
            if eligible
            else f"required N={selected} exceeds frozen cap={cap}"
        ),
        "n_test": int(selected) if eligible else None,
        "required_n_before_cap": int(selected),
        "test_min_n": int(TEST_MIN_N[axis]),
        "test_max_n": cap,
        "observed_dev_sd": observed_sd,
        "prior_sd_floor": sd_floor,
        "planning_sd": sd_plan,
        "raw_required_n": float(raw),
        "inflation": POWER_INFLATION,
        "target_power": POWER_TARGET,
        "z_primary": Z_PRIMARY,
        "z_power80": Z_POWER80,
        "delta": DELTA,
        "confirmatory": True,
    }


def _default_diagnostics(
    _axis: str, _phase: str, _cell_key: str, items: Sequence[Dict], k: int
) -> Dict[str, object]:
    expected = len(items) * int(k)
    return {
        "expected_records": expected,
        "observed_records": expected,
        "coverage": 1.0,
        "parse_rate": 1.0,
        "truncation_rate": 0.0,
    }


def diagnostics_eligible(axis: str, stats: Dict[str, object]) -> Tuple[bool, str]:
    coverage = float(stats.get("coverage", 0.0))
    parse_rate = float(stats.get("parse_rate", 0.0))
    truncation_rate = float(stats.get("truncation_rate", 1.0))
    identity_ok = bool(stats.get("identity_ok", True))
    if not identity_ok:
        return False, "generation/transcript identity mismatch"
    if abs(coverage - 1.0) > 1e-12:
        return False, f"generation/transcript coverage must equal 1, got {coverage:.4f}"
    if parse_rate < PARSE_RATE_MIN[axis] - 1e-12:
        return False, (
            f"parse_rate={parse_rate:.4f} below DEV eligibility "
            f"{PARSE_RATE_MIN[axis]:.2f}"
        )
    if truncation_rate > TRUNCATION_RATE_MAX + 1e-12:
        return False, (
            f"truncation_rate={truncation_rate:.4f} exceeds "
            f"{TRUNCATION_RATE_MAX:.2f}"
        )
    return True, "eligible"


@dataclass
class DevCompositionSelection:
    axis: str
    eligible: bool
    reason: str
    layer: int
    best_prompt_id: Optional[str]
    best_prompt_text: Optional[str]
    frozen_alpha: Optional[float]
    dev_n: int
    planned_test_n: Optional[int]
    selected_test_ids: List[str]
    prompt_rows: List[Dict[str, object]]
    alpha_rows: List[Dict[str, object]]
    power: Dict[str, object]
    dev_primary_mean: Optional[float]
    dev_interaction_mean: Optional[float]

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


def _eval(
    sampler: c2.OutcomeSampler,
    spec: c2.AxisAdjSpec,
    items: Sequence[Dict],
    instruction: str,
    alpha: float,
    *,
    phase: str,
    cell_key: str,
    ctx: Optional[c2.RunContext],
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    outcomes, degeneracies, samples = c2._channel_item_outcomes(
        sampler,
        spec.axis,
        items,
        instruction,
        float(alpha),
        K_SAMPLES,
        spec.direction,
        spec.layer,
        ctx=ctx,
        phase=phase,
        cell_key=cell_key,
    )
    expected_n = len(items)
    if outcomes.shape != (expected_n,):
        raise ValueError(
            f"{spec.axis}/{phase}/{cell_key}: outcome shape {outcomes.shape}, "
            f"expected {(expected_n,)}"
        )
    if degeneracies.shape != (expected_n,):
        raise ValueError(
            f"{spec.axis}/{phase}/{cell_key}: degeneracy shape "
            f"{degeneracies.shape}, expected {(expected_n,)}"
        )
    if samples.shape != (expected_n, K_SAMPLES):
        raise ValueError(
            f"{spec.axis}/{phase}/{cell_key}: sample shape {samples.shape}, "
            f"expected {(expected_n, K_SAMPLES)}"
        )
    if not (
        np.all(np.isfinite(outcomes))
        and np.all(np.isfinite(degeneracies))
        and np.all(np.isfinite(samples))
    ):
        raise ValueError(
            f"{spec.axis}/{phase}/{cell_key}: non-finite outcome or degeneracy"
        )
    return outcomes, degeneracies, samples


def select_composition_on_dev(
    sampler: c2.OutcomeSampler,
    spec: c2.AxisAdjSpec,
    pool: PoolPlan,
    *,
    diagnostics_fn: Optional[DiagnosticsFn] = None,
    ctx: Optional[c2.RunContext] = None,
    smoke: bool = False,
) -> DevCompositionSelection:
    """Select prompt and steer strictly on DEV.

    Prompt is selected first from the bounded 16-candidate set. Alpha is then
    selected to maximize PS-P, subject to both S-vs-N and PS-vs-P coherence and
    DEV parse/truncation eligibility. Ties use prompt id then lower alpha.
    """
    diag = diagnostics_fn or _default_diagnostics
    dev_items = list(pool.dev_items)
    prompt_rows: List[Dict[str, object]] = []
    prompt_cache: Dict[str, Tuple[np.ndarray, np.ndarray]] = {}

    for prompt_id, prompt_text in spec.strong_prompts:
        key = f"prompt={prompt_id}|alpha=0"
        outcomes, degeneracies, _ = _eval(
            sampler,
            spec,
            dev_items,
            prompt_text,
            0.0,
            phase=PHASE_DEV_PROMPT,
            cell_key=key,
            ctx=ctx,
        )
        stats = diag(spec.axis, PHASE_DEV_PROMPT, key, dev_items, K_SAMPLES)
        eligible, reason = diagnostics_eligible(spec.axis, stats)
        prompt_cache[str(prompt_id)] = (outcomes, degeneracies)
        prompt_rows.append(
            {
                "prompt_id": str(prompt_id),
                "prompt_text": str(prompt_text),
                "mean_outcome": float(outcomes.mean()),
                "mean_degeneracy": float(degeneracies.mean()),
                "diagnostics": stats,
                "eligible": bool(eligible),
                "eligibility_reason": reason,
            }
        )

    eligible_prompts = [row for row in prompt_rows if bool(row["eligible"])]
    if not eligible_prompts:
        return DevCompositionSelection(
            axis=spec.axis,
            eligible=False,
            reason="no bounded prompt passed DEV parse/truncation eligibility",
            layer=int(spec.layer),
            best_prompt_id=None,
            best_prompt_text=None,
            frozen_alpha=None,
            dev_n=len(dev_items),
            planned_test_n=None,
            selected_test_ids=[],
            prompt_rows=prompt_rows,
            alpha_rows=[],
            power={"eligible": False, "reason": "prompt eligibility failed"},
            dev_primary_mean=None,
            dev_interaction_mean=None,
        )

    best_prompt_row = sorted(
        eligible_prompts,
        key=lambda row: (-float(row["mean_outcome"]), str(row["prompt_id"])),
    )[0]
    best_prompt_id = str(best_prompt_row["prompt_id"])
    best_prompt_text = str(best_prompt_row["prompt_text"])
    prompt_out, prompt_deg = prompt_cache[best_prompt_id]

    neutral_key = "prompt=neutral|alpha=0"
    neutral_out, neutral_deg, _ = _eval(
        sampler,
        spec,
        dev_items,
        spec.neutral_prompt,
        0.0,
        phase=PHASE_DEV_NEUTRAL,
        cell_key=neutral_key,
        ctx=ctx,
    )
    neutral_stats = diag(
        spec.axis, PHASE_DEV_NEUTRAL, neutral_key, dev_items, K_SAMPLES
    )
    neutral_eligible, neutral_reason = diagnostics_eligible(spec.axis, neutral_stats)
    if not neutral_eligible:
        return DevCompositionSelection(
            axis=spec.axis,
            eligible=False,
            reason=f"neutral DEV condition ineligible: {neutral_reason}",
            layer=int(spec.layer),
            best_prompt_id=best_prompt_id,
            best_prompt_text=best_prompt_text,
            frozen_alpha=None,
            dev_n=len(dev_items),
            planned_test_n=None,
            selected_test_ids=[],
            prompt_rows=prompt_rows,
            alpha_rows=[],
            power={"eligible": False, "reason": "neutral eligibility failed"},
            dev_primary_mean=None,
            dev_interaction_mean=None,
        )

    alpha_rows: List[Dict[str, object]] = []
    alpha_cache: Dict[float, Tuple[np.ndarray, np.ndarray]] = {}
    for alpha in ALPHA_GRID:
        steer_key = f"prompt=neutral|alpha={float(alpha):g}"
        composed_key = f"prompt={best_prompt_id}|alpha={float(alpha):g}"
        steer_out, steer_deg, _ = _eval(
            sampler,
            spec,
            dev_items,
            spec.neutral_prompt,
            alpha,
            phase=PHASE_DEV_STEER,
            cell_key=steer_key,
            ctx=ctx,
        )
        composed_out, composed_deg, _ = _eval(
            sampler,
            spec,
            dev_items,
            best_prompt_text,
            alpha,
            phase=PHASE_DEV_COMPOSED,
            cell_key=composed_key,
            ctx=ctx,
        )
        steer_stats = diag(
            spec.axis, PHASE_DEV_STEER, steer_key, dev_items, K_SAMPLES
        )
        composed_stats = diag(
            spec.axis, PHASE_DEV_COMPOSED, composed_key, dev_items, K_SAMPLES
        )
        steer_measure_ok, steer_measure_reason = diagnostics_eligible(
            spec.axis, steer_stats
        )
        composed_measure_ok, composed_measure_reason = diagnostics_eligible(
            spec.axis, composed_stats
        )
        steer_coherence_ok = float(steer_deg.mean()) <= (
            COHERENCE_MAX_RATIO * float(neutral_deg.mean())
            + COHERENCE_EPS_FLOOR
            + 1e-12
        )
        composed_coherence_ok = float(composed_deg.mean()) <= (
            COHERENCE_MAX_RATIO * float(prompt_deg.mean())
            + COHERENCE_EPS_FLOOR
            + 1e-12
        )
        primary = composed_out - prompt_out
        steer_main = steer_out - neutral_out
        interaction = primary - steer_main
        eligible = (
            steer_measure_ok
            and composed_measure_ok
            and steer_coherence_ok
            and composed_coherence_ok
        )
        alpha_cache[float(alpha)] = (primary, interaction)
        alpha_rows.append(
            {
                "alpha": float(alpha),
                "mean_steer_at_prompt": float(primary.mean()),
                "mean_steer_at_neutral": float(steer_main.mean()),
                "mean_interaction": float(interaction.mean()),
                "steer_degeneracy": float(steer_deg.mean()),
                "composed_degeneracy": float(composed_deg.mean()),
                "steer_coherence_ok": bool(steer_coherence_ok),
                "composed_coherence_ok": bool(composed_coherence_ok),
                "steer_diagnostics": steer_stats,
                "composed_diagnostics": composed_stats,
                "eligible": bool(eligible),
                "eligibility_reason": "; ".join(
                    reason
                    for ok, reason in (
                        (steer_measure_ok, steer_measure_reason),
                        (composed_measure_ok, composed_measure_reason),
                        (steer_coherence_ok, "steer-only coherence failed"),
                        (composed_coherence_ok, "prompt+steer coherence failed"),
                    )
                    if not ok
                )
                or "eligible",
            }
        )

    eligible_alphas = [row for row in alpha_rows if bool(row["eligible"])]
    if not eligible_alphas:
        return DevCompositionSelection(
            axis=spec.axis,
            eligible=False,
            reason="no alpha passed both-context DEV coherence and measurement gates",
            layer=int(spec.layer),
            best_prompt_id=best_prompt_id,
            best_prompt_text=best_prompt_text,
            frozen_alpha=None,
            dev_n=len(dev_items),
            planned_test_n=None,
            selected_test_ids=[],
            prompt_rows=prompt_rows,
            alpha_rows=alpha_rows,
            power={"eligible": False, "reason": "alpha eligibility failed"},
            dev_primary_mean=None,
            dev_interaction_mean=None,
        )

    best_alpha_row = sorted(
        eligible_alphas,
        key=lambda row: (-float(row["mean_steer_at_prompt"]), float(row["alpha"])),
    )[0]
    frozen_alpha = float(best_alpha_row["alpha"])
    primary, interaction = alpha_cache[frozen_alpha]
    power = plan_test_n(
        spec.axis,
        primary,
        smoke=smoke,
        smoke_test_n=len(pool.test_reservoir) if smoke else None,
    )
    if not bool(power.get("eligible")):
        return DevCompositionSelection(
            axis=spec.axis,
            eligible=False,
            reason=f"DEV power gate failed: {power.get('reason')}",
            layer=int(spec.layer),
            best_prompt_id=best_prompt_id,
            best_prompt_text=best_prompt_text,
            frozen_alpha=frozen_alpha,
            dev_n=len(dev_items),
            planned_test_n=None,
            selected_test_ids=[],
            prompt_rows=prompt_rows,
            alpha_rows=alpha_rows,
            power=power,
            dev_primary_mean=float(primary.mean()),
            dev_interaction_mean=float(interaction.mean()),
        )

    planned_test_n = int(power["n_test"])
    selected_test_ids = [
        str(row["id"]) for row in pool.test_reservoir[:planned_test_n]
    ]
    if len(selected_test_ids) != planned_test_n:
        raise ValueError(
            f"{spec.axis}: planned TEST N={planned_test_n}, "
            f"reservoir only has {len(selected_test_ids)}"
        )
    return DevCompositionSelection(
        axis=spec.axis,
        eligible=True,
        reason="DEV prompt, alpha, coherence, measurement, and power gates passed",
        layer=int(spec.layer),
        best_prompt_id=best_prompt_id,
        best_prompt_text=best_prompt_text,
        frozen_alpha=frozen_alpha,
        dev_n=len(dev_items),
        planned_test_n=planned_test_n,
        selected_test_ids=selected_test_ids,
        prompt_rows=prompt_rows,
        alpha_rows=alpha_rows,
        power=power,
        dev_primary_mean=float(primary.mean()),
        dev_interaction_mean=float(interaction.mean()),
    )


def achieved_mde(item_diffs: Sequence[float]) -> float:
    arr = np.asarray(item_diffs, dtype=np.float64)
    if arr.size < 2:
        return float("nan")
    se = float(np.std(arr, ddof=1)) / math.sqrt(arr.size)
    return (Z_PRIMARY + Z_POWER80) * se


def _ci_dict(values: np.ndarray, *, b: int, level: float, seed: int) -> Dict[str, object]:
    ci = c2.cluster_bootstrap_ci(values, b=b, ci_level=level, seed=seed, cluster=True)
    return {
        "point": ci.point,
        "ci_lo": ci.ci_lo,
        "ci_hi": ci.ci_hi,
        "ci_level": ci.ci_level,
        "bootstrap_b": ci.b,
    }


@dataclass
class AxisCompositionResult:
    axis: str
    layer: int
    n_test: int
    k: int
    best_prompt_id: str
    best_prompt_text: str
    frozen_alpha: float
    condition_means: Dict[str, float]
    condition_degeneracy: Dict[str, float]
    per_item: Dict[str, List[float]]
    estimands: Dict[str, Dict[str, object]]
    diagnostics: Dict[str, Dict[str, object]]
    coherence: Dict[str, bool]
    primary_measurement_eligible: bool
    factorial_measurement_eligible: bool
    achieved_mde: float
    powered_at_delta: bool
    primary_pass: bool
    primary_equivalent_within_delta: bool
    interaction_class: str
    interaction_scope: str
    verdict: str

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


def run_test_axis(
    sampler: c2.OutcomeSampler,
    spec: c2.AxisAdjSpec,
    selection: DevCompositionSelection,
    test_items: Sequence[Dict],
    *,
    diagnostics_fn: Optional[DiagnosticsFn] = None,
    bootstrap_b: int = BOOTSTRAP_B,
    seed: int = SEED,
    ctx: Optional[c2.RunContext] = None,
) -> AxisCompositionResult:
    if not selection.eligible:
        raise ValueError(f"{spec.axis}: cannot TEST an ineligible DEV selection")
    if selection.best_prompt_text is None or selection.best_prompt_id is None:
        raise ValueError(f"{spec.axis}: selection lacks a prompt")
    if selection.frozen_alpha is None:
        raise ValueError(f"{spec.axis}: selection lacks alpha")
    items = list(test_items)
    if [str(row["id"]) for row in items] != list(selection.selected_test_ids):
        raise ValueError(f"{spec.axis}: TEST item IDs differ from DEV-sealed selection")

    diag = diagnostics_fn or _default_diagnostics
    conditions = {
        "neutral": (
            spec.neutral_prompt,
            0.0,
            PHASE_TEST_NEUTRAL,
            "prompt=neutral|alpha=0",
        ),
        "prompt": (
            selection.best_prompt_text,
            0.0,
            PHASE_TEST_PROMPT,
            f"prompt={selection.best_prompt_id}|alpha=0",
        ),
        "steer": (
            spec.neutral_prompt,
            float(selection.frozen_alpha),
            PHASE_TEST_STEER,
            f"prompt=neutral|alpha={float(selection.frozen_alpha):g}",
        ),
        "prompt_steer": (
            selection.best_prompt_text,
            float(selection.frozen_alpha),
            PHASE_TEST_COMPOSED,
            (
                f"prompt={selection.best_prompt_id}|"
                f"alpha={float(selection.frozen_alpha):g}"
            ),
        ),
    }
    outcomes: Dict[str, np.ndarray] = {}
    degeneracies: Dict[str, np.ndarray] = {}
    diagnostics: Dict[str, Dict[str, object]] = {}
    for label, (instruction, alpha, phase, cell_key) in conditions.items():
        out, deg, _ = _eval(
            sampler,
            spec,
            items,
            instruction,
            alpha,
            phase=phase,
            cell_key=cell_key,
            ctx=ctx,
        )
        if len(out) != len(items) or not np.all(np.isfinite(out)):
            raise ValueError(f"{spec.axis}/{label}: incomplete or non-finite outcomes")
        outcomes[label] = out
        degeneracies[label] = deg
        diagnostics[label] = diag(spec.axis, phase, cell_key, items, K_SAMPLES)

    primary = outcomes["prompt_steer"] - outcomes["prompt"]
    steer_neutral = outcomes["steer"] - outcomes["neutral"]
    prompt_main = outcomes["prompt"] - outcomes["neutral"]
    interaction = primary - steer_neutral

    axis_index = AXES.index(spec.axis)
    estimands = {
        "primary_steer_at_prompt": _ci_dict(
            primary,
            b=bootstrap_b,
            level=PRIMARY_CI_LEVEL,
            seed=seed + 100 * axis_index + 1,
        ),
        "steer_at_neutral": _ci_dict(
            steer_neutral,
            b=bootstrap_b,
            level=0.95,
            seed=seed + 100 * axis_index + 2,
        ),
        "prompt_main": _ci_dict(
            prompt_main,
            b=bootstrap_b,
            level=0.95,
            seed=seed + 100 * axis_index + 3,
        ),
        "interaction": _ci_dict(
            interaction,
            b=bootstrap_b,
            level=INTERACTION_CI_LEVEL,
            seed=seed + 100 * axis_index + 4,
        ),
        "primary_equivalence_90pct": _ci_dict(
            primary,
            b=bootstrap_b,
            level=EQUIVALENCE_CI_LEVEL,
            seed=seed + 100 * axis_index + 5,
        ),
        "interaction_equivalence_90pct": _ci_dict(
            interaction,
            b=bootstrap_b,
            level=EQUIVALENCE_CI_LEVEL,
            seed=seed + 100 * axis_index + 6,
        ),
    }

    steer_coherence = float(degeneracies["steer"].mean()) <= (
        COHERENCE_MAX_RATIO * float(degeneracies["neutral"].mean())
        + COHERENCE_EPS_FLOOR
        + 1e-12
    )
    composed_coherence = float(degeneracies["prompt_steer"].mean()) <= (
        COHERENCE_MAX_RATIO * float(degeneracies["prompt"].mean())
        + COHERENCE_EPS_FLOOR
        + 1e-12
    )
    measurement_flags = {
        label: diagnostics_eligible(spec.axis, stats)[0]
        for label, stats in diagnostics.items()
    }
    primary_measurement_eligible = bool(
        measurement_flags["prompt"] and measurement_flags["prompt_steer"]
    )
    factorial_measurement_eligible = bool(all(measurement_flags.values()))

    primary_ci = estimands["primary_steer_at_prompt"]
    primary_pass = bool(
        primary_measurement_eligible
        and steer_coherence
        and composed_coherence
        and float(primary_ci["point"]) >= DELTA
        and float(primary_ci["ci_lo"]) > 0.0
    )
    eq_ci = estimands["primary_equivalence_90pct"]
    equivalent = bool(
        float(eq_ci["ci_lo"]) > -DELTA and float(eq_ci["ci_hi"]) < DELTA
    )
    mde = achieved_mde(primary)
    powered = bool(math.isfinite(mde) and mde <= DELTA)

    interaction_ci = estimands["interaction"]
    interaction_eq = estimands["interaction_equivalence_90pct"]
    if not factorial_measurement_eligible:
        interaction_class = "MEASUREMENT_LIMITED"
    elif float(interaction_ci["ci_lo"]) > 0.0:
        interaction_class = "SYNERGISTIC"
    elif float(interaction_ci["ci_hi"]) < 0.0:
        interaction_class = "ANTAGONISTIC"
    elif (
        float(interaction_eq["ci_lo"]) > -DELTA
        and float(interaction_eq["ci_hi"]) < DELTA
    ):
        interaction_class = "ADDITIVE_WITHIN_DELTA"
    else:
        interaction_class = "INTERACTION_UNRESOLVED"

    if not primary_measurement_eligible:
        verdict = "MEASUREMENT_LIMITED"
    elif not (steer_coherence and composed_coherence):
        verdict = "COHERENCE_FAIL"
    elif primary_pass:
        verdict = "ADDED_VALUE"
    elif equivalent:
        verdict = "EQUIVALENT_WITHIN_DELTA"
    elif powered:
        verdict = "NO_QUALIFYING_INCREMENT"
    else:
        verdict = "INCONCLUSIVE_POWER"

    return AxisCompositionResult(
        axis=spec.axis,
        layer=int(spec.layer),
        n_test=len(items),
        k=K_SAMPLES,
        best_prompt_id=str(selection.best_prompt_id),
        best_prompt_text=str(selection.best_prompt_text),
        frozen_alpha=float(selection.frozen_alpha),
        condition_means={
            label: float(value.mean()) for label, value in outcomes.items()
        },
        condition_degeneracy={
            label: float(value.mean()) for label, value in degeneracies.items()
        },
        per_item={
            label: [float(x) for x in value] for label, value in outcomes.items()
        },
        estimands=estimands,
        diagnostics=diagnostics,
        coherence={
            "steer_vs_neutral": bool(steer_coherence),
            "prompt_steer_vs_prompt": bool(composed_coherence),
        },
        primary_measurement_eligible=primary_measurement_eligible,
        factorial_measurement_eligible=factorial_measurement_eligible,
        achieved_mde=float(mde),
        powered_at_delta=powered,
        primary_pass=primary_pass,
        primary_equivalent_within_delta=equivalent,
        interaction_class=interaction_class,
        interaction_scope=INTERACTION_SCOPE,
        verdict=verdict,
    )


@dataclass
class CompositionReport:
    axis_results: List[AxisCompositionResult]
    overall_verdict: str
    protocol: Dict[str, object]

    def to_dict(self) -> Dict[str, object]:
        return {
            "overall_verdict": self.overall_verdict,
            "protocol": self.protocol,
            "axes": [row.to_dict() for row in self.axis_results],
        }


def summarize_report(results: Sequence[AxisCompositionResult]) -> CompositionReport:
    rows = list(results)
    valid = [
        row
        for row in rows
        if row.verdict not in {"MEASUREMENT_LIMITED", "COHERENCE_FAIL"}
    ]
    passed = [row for row in valid if row.primary_pass]
    if not valid:
        verdict = "INVALID"
    elif passed and len(passed) == len(rows) == len(AXES):
        verdict = "POSITIVE"
    elif passed:
        verdict = "MIXED"
    elif len(valid) == len(rows) == len(AXES) and all(
        row.powered_at_delta for row in rows
    ):
        verdict = "QUALIFIED_NULL"
    else:
        verdict = "INCONCLUSIVE"
    return CompositionReport(
        axis_results=rows,
        overall_verdict=verdict,
        protocol=frozen_protocol_dict(),
    )


def frozen_protocol_dict() -> Dict[str, object]:
    return {
        "protocol_id": PROTOCOL_ID,
        "status": "FROZEN",
        "execution_gate": (
            "CPU/synthetic validation only until hostile implementation audit PASS; "
            "real TEST additionally requires one-use authorization and budget approval"
        ),
        "model": FROZEN_MODEL,
        "model_revision": FROZEN_MODEL_REVISION,
        "method": FROZEN_METHOD,
        "scientific_scope": "construct validation for the tested Qwen CAA cell",
        "prior_work_boundary": (
            "Bo et al. already tested prompting on top of activation steering; "
            "this experiment does not claim composition novelty"
        ),
        "historical_exposure": (
            "historical invalidated E-0012 artifacts had been inspected, but "
            "supply no evidence, prior, item selection, direction, or claim support"
        ),
        "preserved_substitution_result": "original frozen substitution result remains 0/12",
        "axes": list(AXES),
        "conditions": ["neutral", "prompt", "steer", "prompt_steer"],
        "primary_estimand": "prompt_steer - prompt",
        "interaction_estimand": "(prompt_steer - prompt) - (steer - neutral)",
        "interaction_scope": INTERACTION_SCOPE,
        "prompt_selection": "best of 16 bounded prompts on DEV only",
        "alpha_selection": (
            "maximize DEV prompt_steer-prompt over frozen alpha grid, subject to "
            "both-context coherence and measurement eligibility"
        ),
        "alpha_grid": list(ALPHA_GRID),
        "k_samples": K_SAMPLES,
        "delta": DELTA,
        "dev_n": DEV_N,
        "test_min_n": dict(TEST_MIN_N),
        "test_max_n": dict(TEST_MAX_N),
        "power": {
            "target": POWER_TARGET,
            "inflation": POWER_INFLATION,
            "prior_sd_floor": dict(PRIOR_SD_FLOOR),
            "rule": (
                "ceil8(1.20*((z_98.33pct+z_80)*max(SD_DEV,SD_prior)/0.05)^2)"
            ),
        },
        "bootstrap_b": BOOTSTRAP_B,
        "bootstrap_rule": "real HF DEV/TEST requires exactly B=10000",
        "primary_ci_level": PRIMARY_CI_LEVEL,
        "interaction_ci_level": INTERACTION_CI_LEVEL,
        "equivalence_ci_level": EQUIVALENCE_CI_LEVEL,
        "coherence": (
            "S <= 1.5*N + 0.02 and PS <= 1.5*P + 0.02 on degeneracy score"
        ),
        "parse_rate_min": dict(PARSE_RATE_MIN),
        "truncation_rate_max": TRUNCATION_RATE_MAX,
        "strict_parser": (
            "uncertainty requires explicit Answer and Confidence fields; "
            "skepticism requires an explicit valid option cue; missing fields "
            "score 0 and remain recorded"
        ),
        "batch_size": FROZEN_BATCH_SIZE,
        "generation_retry_budget_per_backend_call": FROZEN_RETRY_BUDGET,
        "disk_budget_gb": FROZEN_DISK_BUDGET_GB,
        "disk_ceiling_gb": FROZEN_DISK_CEILING_GB,
        "stall_timeout_seconds": FROZEN_STALL_TIMEOUT_SECONDS,
        "worst_case_compute_plan": worst_case_compute_plan(),
        "synthetic_rule": (
            "SMOKE_ONLY; no scientific verdict, confirmatory registry row, "
            "C2 claim manifest, or evidence upgrade"
        ),
        "test_head_rule": "TEST HEAD must exactly equal the DEV commit",
        "selection_rule": (
            "TEST loads only verified DEV-seal/dev_selection.json and matches "
            "its selection hash to the seal identity"
        ),
        "disk_guard_scope": (
            "non-overlapping roots cover the full backend artifact tree plus "
            "external HF_HOME/venv growth"
        ),
        "test_rule": "TEST is generated once after external hostile-audit authorization",
    }
