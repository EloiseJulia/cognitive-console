"""C2b conflict + reachability harness — the behavioral gap read (EXPLORATORY).

The C2b question (RQ2 seed): can latent STEERING push the model's BEHAVIOR into a
region that a bounded, human-readable PROMPT cannot reach? For each axis we run
three probes over a real (or synthetic) steered-generation backend and the crude
automatic behavioral proxies in ``experiments.behavior``:

  (a) BOUNDED PROMPT SEARCH — the prompt ceiling. Generate UNSTEERED (alpha=0)
      under each of a small set of strong, readable prompts (data/strongest_prompts)
      and take the best behavioral proxy. This is the best a bounded prompt reaches.
  (b) STEER-ONLY — generate under a neutral prompt with latent steering at a few
      positive alphas; the best is how far latent steering alone pushes behavior.
  (c) CONFLICT — the strongest pro-axis prompt pushes the axis UP while the latent
      vector steers the OPPOSITE way (negative alpha). We record where behavior
      lands between the prompt pole and the steer pole using the audited
      ``compute_landing_raw`` (keeps overshoot / wrong-side signal) — which channel
      wins, by how much.

Headline: ``reaches_beyond_prompt_ceiling`` = does steer-only behavior exceed the
prompt ceiling? EXPLORATORY — no frozen verdict, no threshold; we report numbers.

This module is model-independent: it consumes any ``GenBackend`` (real
``SteeredHFBackend`` on GPU, ``SyntheticSteeredBackend`` offline) plus a per-axis
(direction, layer). All scoring goes through ``behavior_score``.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

from ..steering.generate import GenBackend, SteerConfig
from .behavior import behavior_score as _default_scorer
from .conflict_probe import compute_landing, compute_landing_raw

_EPS = 1e-9

Scorer = Callable[[str, str], float]


@dataclass
class AxisSteerSpec:
    """Per-axis inputs to the C2b harness."""
    axis: str
    direction: np.ndarray       # CAA axis vector (normalized inside the backend)
    layer: int                  # hidden_states index to steer
    strong_prompts: List[Tuple[str, str]]   # (prompt_id, text) — the bounded search
    neutral_prompt: str         # axis-agnostic prompt for steer-only / steer pole


@dataclass
class C2bAxisResult:
    axis: str
    layer: int
    alphas: List[float]
    # (a) prompt ceiling
    prompt_ceiling: float
    prompt_ceiling_mean: float
    best_prompt_id: str
    prompt_scores: List[Dict[str, object]]
    # (b) steer-only
    steer_only: List[Dict[str, object]]
    steer_only_max: float
    steer_only_max_alpha: float
    # headline
    reaches_beyond_prompt_ceiling: bool
    beyond_margin: float          # steer_only_max - prompt_ceiling (signed)
    # (c) conflict
    conflict: List[Dict[str, object]]
    max_new_tokens: int
    scorer_name: str
    note: str = (
        "EXPLORATORY C2b read. Behavior measured by CRUDE lexical proxies "
        "(experiments.behavior), NOT validated instruments. No frozen verdict."
    )

    def to_row(self) -> Dict[str, object]:
        return asdict(self)


def run_c2b_axis(
    gen: GenBackend,
    spec: AxisSteerSpec,
    alphas: Sequence[float] = (2.0, 4.0, 8.0),
    max_new_tokens: int = 128,
    scorer: Scorer = _default_scorer,
    preview_chars: int = 160,
) -> C2bAxisResult:
    """Run the (a) prompt-ceiling, (b) steer-only, (c) conflict probes for one axis."""
    axis = spec.axis
    alphas = [float(a) for a in alphas]

    # (a) BOUNDED PROMPT SEARCH — unsteered generation under each strong prompt.
    prompt_scores: List[Dict[str, object]] = []
    for pid, text in spec.strong_prompts:
        out = gen.generate(text, SteerConfig(spec.direction, 0.0, spec.layer), max_new_tokens)
        prompt_scores.append({
            "prompt_id": pid,
            "score": float(scorer(out, axis)),
            "preview": out[:preview_chars],
        })
    if not prompt_scores:
        raise ValueError(f"axis {axis}: no strong prompts supplied")
    best = max(prompt_scores, key=lambda r: r["score"])
    prompt_ceiling = float(best["score"])
    prompt_ceiling_mean = float(np.mean([r["score"] for r in prompt_scores]))
    best_prompt_id = str(best["prompt_id"])
    best_prompt_text = dict(spec.strong_prompts)[best_prompt_id]

    # (b) STEER-ONLY — neutral prompt, positive alphas.
    steer_only: List[Dict[str, object]] = []
    for a in alphas:
        out = gen.generate(spec.neutral_prompt, SteerConfig(spec.direction, a, spec.layer), max_new_tokens)
        steer_only.append({"alpha": a, "score": float(scorer(out, axis)), "preview": out[:preview_chars]})
    # include the alpha=0 neutral baseline for reference
    base_out = gen.generate(spec.neutral_prompt, SteerConfig(spec.direction, 0.0, spec.layer), max_new_tokens)
    steer_baseline = float(scorer(base_out, axis))
    steer_row_max = max(steer_only, key=lambda r: r["score"])
    steer_only_max = float(steer_row_max["score"])
    steer_only_max_alpha = float(steer_row_max["alpha"])

    reaches_beyond = bool(steer_only_max > prompt_ceiling + _EPS)
    beyond_margin = float(steer_only_max - prompt_ceiling)

    # (c) CONFLICT — pro-axis prompt (UP) vs latent steer the OPPOSITE way (DOWN).
    conflict: List[Dict[str, object]] = []
    prompt_pole = prompt_ceiling  # behavior of the best prompt alone (alpha=0)
    for a in alphas:
        # steer pole: neutral prompt steered the OPPOSITE (negative) way at magnitude a.
        steer_out = gen.generate(spec.neutral_prompt, SteerConfig(spec.direction, -a, spec.layer), max_new_tokens)
        steer_pole = float(scorer(steer_out, axis))
        # conflict: best pro-axis prompt AND opposite steer together.
        conf_out = gen.generate(best_prompt_text, SteerConfig(spec.direction, -a, spec.layer), max_new_tokens)
        behavior = float(scorer(conf_out, axis))
        if abs(steer_pole - prompt_pole) < _EPS:
            landing_raw = float("nan")
            landing = float("nan")
            winner = "undefined"
            clipped = False
        else:
            landing_raw = compute_landing_raw(behavior, prompt_pole, steer_pole)
            landing = compute_landing(behavior, prompt_pole, steer_pole)
            clipped = bool(abs(landing - landing_raw) > _EPS)
            if landing > 0.5 + _EPS:
                winner = "latent"
            elif landing < 0.5 - _EPS:
                winner = "prompt"
            else:
                winner = "tie"
        conflict.append({
            "alpha": a,
            "steer_sign": -1,
            "prompt_pole": prompt_pole,
            "steer_pole": steer_pole,
            "behavior": behavior,
            "landing_fraction": landing,
            "landing_fraction_raw": landing_raw,
            "clipped": clipped,
            "winner": winner,
            "preview": conf_out[:preview_chars],
        })

    return C2bAxisResult(
        axis=axis,
        layer=int(spec.layer),
        alphas=alphas,
        prompt_ceiling=prompt_ceiling,
        prompt_ceiling_mean=prompt_ceiling_mean,
        best_prompt_id=best_prompt_id,
        prompt_scores=prompt_scores,
        steer_only=[{**r, "steer_baseline_alpha0": steer_baseline} for r in steer_only],
        steer_only_max=steer_only_max,
        steer_only_max_alpha=steer_only_max_alpha,
        reaches_beyond_prompt_ceiling=reaches_beyond,
        beyond_margin=beyond_margin,
        conflict=conflict,
        max_new_tokens=int(max_new_tokens),
        scorer_name=getattr(scorer, "__name__", "behavior_score"),
    )


def run_c2b_pilot(
    gen_for_axis: Callable[[str], GenBackend],
    specs: Sequence[AxisSteerSpec],
    alphas: Sequence[float] = (2.0, 4.0, 8.0),
    max_new_tokens: int = 128,
    scorer: Scorer = _default_scorer,
) -> List[C2bAxisResult]:
    """Run the C2b harness for every axis spec.

    ``gen_for_axis`` returns the generation backend to use for a given axis (a
    single shared real backend for all axes, or a per-axis synthetic one in
    tests).
    """
    results: List[C2bAxisResult] = []
    for spec in specs:
        gen = gen_for_axis(spec.axis)
        results.append(
            run_c2b_axis(gen, spec, alphas=alphas, max_new_tokens=max_new_tokens, scorer=scorer)
        )
    return results
