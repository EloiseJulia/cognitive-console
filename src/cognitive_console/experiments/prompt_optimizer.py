"""Bounded DEV-only prompt optimizer for the stronger prompt-ceiling baseline.

This module intentionally does NOT change the frozen adjudication math. It only
searches for a stronger prompt on DEV (fixed budget), then returns one frozen
winner prompt to be re-evaluated on TEST by the existing frozen adjudicator.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional, Sequence, Set, Tuple

import numpy as np

from cognitive_console.experiments.adjudicate_c2b import (
    AxisAdjSpec,
    OutcomeSampler,
    SampleBatch,
)

_AXIS_HINTS = {
    "deliberation": "Show the final numeric answer clearly.",
    "skepticism": "Reject false premises and pick the most truthful option.",
    "uncertainty_awareness": "State calibrated confidence and avoid overclaiming.",
}

_PREFIXES = (
    "Be precise and concise.",
    "Reason carefully before giving the final answer.",
    "Apply strict verification before committing to the answer.",
)

_SUFFIXES = (
    "Prefer correctness over speed.",
    "Double-check assumptions before finalizing.",
    "If uncertain, be explicit about uncertainty.",
)


@dataclass(frozen=True)
class OptimizerConfig:
    total_budget: int
    seed_prompt_count: int = 4
    max_rounds: int = 3
    candidates_per_round: int = 4
    keep_top_k: int = 2
    seed: int = 0

    def __post_init__(self):
        if int(self.total_budget) <= 0:
            raise ValueError("optimizer total_budget must be > 0")
        if int(self.seed_prompt_count) <= 0:
            raise ValueError("optimizer seed_prompt_count must be > 0")
        if int(self.max_rounds) <= 0:
            raise ValueError("optimizer max_rounds must be > 0")
        if int(self.candidates_per_round) <= 0:
            raise ValueError("optimizer candidates_per_round must be > 0")
        if int(self.keep_top_k) <= 0:
            raise ValueError("optimizer keep_top_k must be > 0")
        if int(self.total_budget) < int(self.seed_prompt_count):
            raise ValueError("optimizer total_budget must be >= seed_prompt_count")


@dataclass
class PromptEval:
    prompt_id: str
    prompt_text: str
    score: float
    round_index: int
    source_prompt_ids: List[str] = field(default_factory=list)


@dataclass
class OptimizerResult:
    axis: str
    winner_prompt_id: str
    winner_prompt_text: str
    winner_score_dev: float
    evaluations_used: int
    total_budget: int
    seed: int
    rounds: List[Dict[str, object]]
    seed_prompt_ids: List[str]
    dev_item_ids: List[str]
    test_item_ids: List[str]
    leakage_guard_ok: bool
    compute_parity_target_n_strong: int

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


def _normalize_spaces(text: str) -> str:
    return " ".join(str(text).split())


def _blend_prompts(a: str, b: str, axis: str) -> str:
    hint = _AXIS_HINTS.get(axis, "Follow the task objective faithfully.")
    return _normalize_spaces(
        f"{_PREFIXES[0]} {a} {b} {hint} {_SUFFIXES[1]}"
    )


def _mutate_prompt(base: str, axis: str, rng: np.random.Generator, slot: int) -> str:
    hint = _AXIS_HINTS.get(axis, "Follow the task objective faithfully.")
    prefix = _PREFIXES[int(rng.integers(0, len(_PREFIXES)))]
    suffix = _SUFFIXES[int(rng.integers(0, len(_SUFFIXES)))]
    if slot % 3 == 0:
        return _normalize_spaces(f"{prefix} {base} {hint}")
    if slot % 3 == 1:
        return _normalize_spaces(f"{base} {suffix} {hint}")
    return _normalize_spaces(f"{prefix} {base} {suffix}")


def _evaluate_prompt_on_dev(
    sampler: OutcomeSampler,
    spec: AxisAdjSpec,
    dev_items: Sequence[Dict],
    test_item_ids: Set[str],
    prompt_text: str,
    k: int,
) -> float:
    dev_ids = [str(it["id"]) for it in dev_items]
    if not dev_ids:
        raise ValueError("optimizer requires non-empty DEV items")
    if set(dev_ids) & set(test_item_ids):
        raise ValueError("optimizer DEV/TEST leakage: TEST ids present in DEV batch")

    batches: List[SampleBatch] = sampler.sample_batch(
        spec.axis,
        list(dev_items),
        str(prompt_text),
        0.0,
        int(k),
        spec.direction,
        spec.layer,
    )
    if len(batches) != len(dev_items):
        raise RuntimeError(
            f"optimizer sampler returned {len(batches)} batches for {len(dev_items)} DEV items"
        )
    per_item = [float(b.mean_outcome()) for b in batches]
    return float(np.mean(per_item))


def optimize_prompt_on_dev(
    sampler: OutcomeSampler,
    spec: AxisAdjSpec,
    dev_items: Sequence[Dict],
    test_item_ids: Sequence[str],
    *,
    k: int,
    config: OptimizerConfig,
    compute_parity_target_n_strong: int,
) -> OptimizerResult:
    dev_items = list(dev_items)
    dev_item_ids = sorted(str(it["id"]) for it in dev_items)
    test_ids = sorted(str(x) for x in test_item_ids)
    if set(dev_item_ids) & set(test_ids):
        raise ValueError("optimizer DEV/TEST leakage before optimization begins")

    seeds = list(spec.strong_prompts)[: int(config.seed_prompt_count)]
    if len(seeds) < int(config.seed_prompt_count):
        raise ValueError(
            f"optimizer requires >= {config.seed_prompt_count} seed prompts, got {len(seeds)}"
        )

    rng = np.random.default_rng(int(config.seed))
    used = 0
    seen_text: Set[str] = set()
    evals: List[PromptEval] = []
    rounds: List[Dict[str, object]] = []

    def eval_one(prompt_id: str, prompt_text: str, round_index: int, source_ids: Optional[List[str]] = None):
        nonlocal used
        if used >= int(config.total_budget):
            return
        key = _normalize_spaces(prompt_text)
        if key in seen_text:
            return
        score = _evaluate_prompt_on_dev(
            sampler,
            spec,
            dev_items,
            set(test_ids),
            prompt_text,
            k=int(k),
        )
        seen_text.add(key)
        used += 1
        evals.append(
            PromptEval(
                prompt_id=str(prompt_id),
                prompt_text=str(prompt_text),
                score=float(score),
                round_index=int(round_index),
                source_prompt_ids=list(source_ids or []),
            )
        )

    for pid, ptext in seeds:
        eval_one(str(pid), str(ptext), round_index=0)
    rounds.append(
        {
            "round_index": 0,
            "phase": "seed",
            "evaluated_prompt_ids": [e.prompt_id for e in evals if e.round_index == 0],
        }
    )

    for round_index in range(1, int(config.max_rounds) + 1):
        if used >= int(config.total_budget):
            break
        ranked = sorted(evals, key=lambda x: x.score, reverse=True)
        elites = ranked[: int(config.keep_top_k)]
        if not elites:
            break

        proposals: List[Tuple[str, str, List[str]]] = []
        if len(elites) >= 2:
            blend = _blend_prompts(elites[0].prompt_text, elites[1].prompt_text, spec.axis)
            proposals.append(
                (f"opt-r{round_index}-blend", blend, [elites[0].prompt_id, elites[1].prompt_id])
            )
        for ei, elite in enumerate(elites):
            for slot in range(3):
                text = _mutate_prompt(elite.prompt_text, spec.axis, rng, slot + ei * 3)
                proposals.append(
                    (
                        f"opt-r{round_index}-e{ei}-m{slot}",
                        text,
                        [elite.prompt_id],
                    )
                )

        budget_left = int(config.total_budget) - used
        cap = min(int(config.candidates_per_round), budget_left)
        before = len(evals)
        for pid, ptext, src_ids in proposals:
            if len(evals) - before >= cap:
                break
            eval_one(pid, ptext, round_index=round_index, source_ids=src_ids)
        rounds.append(
            {
                "round_index": int(round_index),
                "phase": "mutate",
                "evaluated_prompt_ids": [e.prompt_id for e in evals if e.round_index == round_index],
            }
        )
        if len(evals) == before:
            break

    if not evals:
        raise RuntimeError("optimizer evaluated zero prompts")

    winner = max(evals, key=lambda e: e.score)
    return OptimizerResult(
        axis=str(spec.axis),
        winner_prompt_id=str(winner.prompt_id),
        winner_prompt_text=str(winner.prompt_text),
        winner_score_dev=float(winner.score),
        evaluations_used=int(used),
        total_budget=int(config.total_budget),
        seed=int(config.seed),
        rounds=[
            {
                **r,
                "scores": [
                    {
                        "prompt_id": e.prompt_id,
                        "score_dev": float(e.score),
                        "source_prompt_ids": list(e.source_prompt_ids),
                    }
                    for e in evals
                    if e.round_index == int(r["round_index"])
                ],
            }
            for r in rounds
        ],
        seed_prompt_ids=[str(pid) for pid, _ in seeds],
        dev_item_ids=dev_item_ids,
        test_item_ids=test_ids,
        leakage_guard_ok=True,
        compute_parity_target_n_strong=int(compute_parity_target_n_strong),
    )
