"""Conflict-probe harness (C2b seed) — prompt channel vs latent channel.

Research question this seeds (RQ2): when the *prompt* channel pushes an axis one
way (e.g. prompt = "answer with high confidence") and the *latent* channel pushes
it the other way (e.g. a high-skepticism steering vector at some magnitude),
where does the model's BEHAVIOR actually land between the two poles, and which
channel wins by how much?

Only the config / orchestration / landing computation / logging is pure code
here. The actual generate-and-measure step is abstracted behind `BehaviorBackend`
exactly like the ActivationProvider seam:

* `SyntheticBehaviorBackend` — deterministic, seeded, OFFLINE. Models the landing
  as a magnitude-dependent blend of the two channel targets, so tests can assert
  the harness computes a sensible landing metric and logs a registry row.
* `HFBehaviorBackend` — STUB; raises NotImplementedError (deferred to GPU phase),
  torch/transformers never imported at module top-level.
"""

from __future__ import annotations

import abc
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

import numpy as np

from .. import lineage
from ..registry import ExperimentRegistry

_EPS = 1e-12
_MODEL_HINT = (
    "GPU phase: generate under prompt + latent steering, measure the axis "
    "behavior score; deferred until GPU is approved (AGENTS.md §5)."
)


@dataclass
class ConflictConfig:
    """One prompt-vs-latent conflict trial along an axis.

    prompt_target / latent_target are the axis-behavior scores each channel would
    produce ALONE (the two poles the landing point sits between). They are set by
    the experiment design (e.g. calibration runs), not invented by the backend.
    """
    axis: str
    prompt_text: str
    prompt_target: float
    latent_vector: np.ndarray
    latent_magnitude: float
    latent_target: float
    layer: int
    seed: int = 0

    def key(self) -> str:
        h = hashlib.sha256(
            f"{self.axis}|{self.prompt_text}|{self.prompt_target}|"
            f"{self.latent_magnitude}|{self.latent_target}|{self.layer}|{self.seed}".encode()
        ).hexdigest()[:12]
        return f"{self.axis}-{h}"


class BehaviorBackend(abc.ABC):
    """Abstract generate-and-measure backend (the deferred model seam)."""

    @abc.abstractmethod
    def behavior_score(self, config: ConflictConfig) -> float:
        """Return the measured axis-behavior score under prompt + latent steering."""


class SyntheticBehaviorBackend(BehaviorBackend):
    """Deterministic offline backend: landing = magnitude-weighted channel blend.

    The latent channel's pull grows with steering magnitude via a saturating
    weight w = (m*gain) / (m*gain + 1). The landing sits at
    (1-w)*prompt_target + w*latent_target, plus tiny seeded noise. So m=0 => the
    prompt wins outright; large m => the latent wins; intermediate m => a genuine
    in-between landing point.
    """

    def __init__(self, latent_gain: float = 1.0, noise_scale: float = 0.0, seed: int = 0):
        self.latent_gain = float(latent_gain)
        self.noise_scale = float(noise_scale)
        self.seed = int(seed)

    def latent_weight(self, magnitude: float) -> float:
        m = max(0.0, float(magnitude)) * self.latent_gain
        return m / (m + 1.0)

    def behavior_score(self, config: ConflictConfig) -> float:
        w = self.latent_weight(config.latent_magnitude)
        score = (1.0 - w) * config.prompt_target + w * config.latent_target
        if self.noise_scale > 0.0:
            key = f"{self.seed}|{config.key()}".encode()
            digest = hashlib.sha256(key).digest()
            rng = np.random.default_rng(int.from_bytes(digest[:8], "big"))
            score += float(rng.normal(0.0, self.noise_scale))
        return float(score)


class HFBehaviorBackend(BehaviorBackend):
    """Legacy STUB kept for API compatibility (superseded by SteeredBehaviorBackend).

    The C2b generate-and-measure path is now REAL via ``SteeredBehaviorBackend``
    (which composes a ``GenBackend`` steered generator + the ``behavior_score``
    proxies). This stub is retained so nothing that imported it breaks; it still
    raises to force callers onto the wired backend.
    """

    def __init__(self, model_name: str):
        self.model_name = model_name

    def behavior_score(self, config: ConflictConfig) -> float:
        raise NotImplementedError(_MODEL_HINT)


class SteeredBehaviorBackend(BehaviorBackend):
    """REAL behavior backend: steered generation + automatic behavioral proxy.

    Wires the conflict probe to the deferred model seam. For a ``ConflictConfig``
    it generates a response to ``config.prompt_text`` while steering along
    ``config.latent_vector`` at ``config.latent_magnitude`` on ``config.layer``,
    then scores the axis behavior with ``experiments.behavior.behavior_score``.

    Works with any ``GenBackend``: the real ``SteeredHFBackend`` on GPU or the
    ``SyntheticSteeredBackend`` offline. No torch is imported here (the backend
    handles that lazily), so this class stays import-safe for the offline suite.
    """

    def __init__(self, gen_backend, max_new_tokens: int = 128, scorer=None):
        from ..steering.generate import GenBackend  # local import: no torch cost

        if not isinstance(gen_backend, GenBackend):
            raise TypeError("gen_backend must be a GenBackend")
        self.gen = gen_backend
        self.max_new_tokens = int(max_new_tokens)
        if scorer is None:
            from .behavior import behavior_score as scorer  # noqa: PLC0415
        self.scorer = scorer

    def behavior_score(self, config: ConflictConfig) -> float:
        from ..steering.generate import SteerConfig

        steer = SteerConfig(
            direction=config.latent_vector,
            alpha=config.latent_magnitude,
            layer=config.layer,
        )
        text = self.gen.generate(config.prompt_text, steer, self.max_new_tokens)
        return float(self.scorer(text, config.axis))


@dataclass
class ConflictResult:
    axis: str
    behavior_score: float
    prompt_target: float
    latent_target: float
    latent_magnitude: float
    landing_fraction: float      # 0 => prompt wins, 1 => latent wins (clipped)
    landing_fraction_raw: float  # UNCLIPPED: >1 == latent overshoots its pole,
                                 # <0 == landed on the wrong side (C2b / AC6 signal)
    clipped: bool                # True iff raw fell outside [0,1] (overshoot / wrong-side)
    winner: str                  # "prompt" | "latent" | "tie"
    margin: float                # |landing_fraction - 0.5| * 2 in [0,1]
    experiment_id: Optional[str] = None

    def to_summary(self) -> Dict[str, object]:
        return {
            "axis": self.axis,
            "behavior_score": self.behavior_score,
            "landing_fraction": self.landing_fraction,
            "landing_fraction_raw": self.landing_fraction_raw,
            "clipped": self.clipped,
            "winner": self.winner,
            "margin": self.margin,
            "latent_magnitude": self.latent_magnitude,
        }


def compute_landing_raw(
    behavior_score: float, prompt_target: float, latent_target: float
) -> float:
    """UNCLIPPED landing fraction between the two channel poles.

    0.0 == prompt pole, 1.0 == latent pole. Values >1 mean the latent channel
    overshoots its own pole; values <0 mean the behavior landed on the wrong side
    of the prompt pole. These out-of-range cases are exactly the non-additive
    conflict outcomes C2b/AC6 cares about, so they are preserved here rather than
    clipped away. Undefined (raises) when the two poles coincide.
    """
    span = latent_target - prompt_target
    if abs(span) < _EPS:
        raise ValueError("prompt_target == latent_target: no conflict axis to measure")
    return float((behavior_score - prompt_target) / span)


def compute_landing(
    behavior_score: float, prompt_target: float, latent_target: float
) -> float:
    """Landing fraction of the behavior between the two channel poles.

    0.0 == fully at the prompt pole, 1.0 == fully at the latent pole. Clipped to
    [0,1] for convenience. Use `compute_landing_raw` to keep overshoot/wrong-side
    signal. Undefined (raises) when the two poles coincide.
    """
    raw = compute_landing_raw(behavior_score, prompt_target, latent_target)
    return float(np.clip(raw, 0.0, 1.0))


def run_conflict_probe(
    backend: BehaviorBackend,
    config: ConflictConfig,
    registry: Optional[ExperimentRegistry] = None,
    config_hash: Optional[str] = None,
    hypothesis_id: str = "H2",
    claim_ids: Optional[Sequence[str]] = None,
    repo_dir: Optional[str] = None,
) -> ConflictResult:
    """Run one conflict trial, compute the landing, and (optionally) log lineage.

    The behavior_score comes ONLY from the backend; the landing is derived from
    it. When a registry is supplied, a unique experiment_id is minted and the
    computed landing metrics are recorded (no hand values).
    """
    score = backend.behavior_score(config)
    frac_raw = compute_landing_raw(score, config.prompt_target, config.latent_target)
    frac = float(np.clip(frac_raw, 0.0, 1.0))
    clipped = bool(abs(frac - frac_raw) > _EPS)
    if frac > 0.5 + _EPS:
        winner = "latent"
    elif frac < 0.5 - _EPS:
        winner = "prompt"
    else:
        winner = "tie"
    margin = float(abs(frac - 0.5) * 2.0)

    result = ConflictResult(
        axis=config.axis,
        behavior_score=score,
        prompt_target=config.prompt_target,
        latent_target=config.latent_target,
        latent_magnitude=config.latent_magnitude,
        landing_fraction=frac,
        landing_fraction_raw=frac_raw,
        clipped=clipped,
        winner=winner,
        margin=margin,
    )

    if registry is not None:
        exp_id = lineage.register_run(
            registry=registry,
            prefix="conflict",
            hypothesis_id=hypothesis_id,
            claim_ids=list(claim_ids) if claim_ids else ["C2b"],
            config_hash=config_hash,
            summary_metrics=result.to_summary(),
            run_type="exploratory",
            seed=config.seed,
            repo_dir=repo_dir,
        )
        result.experiment_id = exp_id

    return result
