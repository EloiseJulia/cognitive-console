"""SteeredHFTextCapableSampler — real GPU/HF sampler with raw-text support for E-0012.

Implements the TextCapableSampler TODO from e0012_harness.py, required before
A800 boot (N-01 fix).  Wraps SteeredHFBackend so that _eval_items_with_raw_pairs
records true (confidence, correctness) pairs with synthetic_proxy=False for the
§9.2 Brier decomposition safety guards (reliability guard + gaming test).

Without this class the HF path wraps SteeredHFBackend in BackendOutcomeSampler
(not a TextCapableSampler), causing _eval_items_with_raw_pairs to write
synthetic_proxy=True records → has_real_pairs()=False → §9.2 guards run on
wrong 1-Brier proxy data, silently ignoring genuine gaming.
"""
from __future__ import annotations

import hashlib
from typing import Dict, List, Tuple

import numpy as np

from cognitive_console.eval import scorers as _scorers
from cognitive_console.experiments import adjudicate_c2b as adj
from cognitive_console.experiments.e0012_harness import TextCapableSampler
from cognitive_console.steering.generate import SteeredHFBackend, SteerConfig


class SteeredHFTextCapableSampler(TextCapableSampler):
    """Wraps SteeredHFBackend as a TextCapableSampler for E-0012.

    sample_with_texts() generates k steered responses and returns both the
    SampleBatch (outcomes + degeneracies) and the k raw text strings.
    _eval_items_with_raw_pairs then extracts true (confidence, correctness) pairs
    via parse_confidence() / item_is_correct() and records them with
    synthetic_proxy=False in the BrierRawStore, satisfying §9.2.

    Usage in run_e0012_verified_control.py (HF path):
        hf_backend = SteeredHFBackend(model_name=model_name)
        sampler = SteeredHFTextCapableSampler(hf_backend, ...)
    """

    def __init__(
        self,
        hf_backend: SteeredHFBackend,
        max_new_tokens: int = 256,
        do_sample: bool = True,
        temperature: float = 0.7,
        seed: int = 0,
    ) -> None:
        if not isinstance(hf_backend, SteeredHFBackend):
            raise TypeError("hf_backend must be a SteeredHFBackend")
        self._hf = hf_backend
        self.max_new_tokens = int(max_new_tokens)
        self.do_sample = bool(do_sample)
        self.temperature = float(temperature)
        self.seed = int(seed)

    def _call_seed(self, axis: str, item: Dict, alpha: float, j: int) -> int:
        """Deterministic per-(item, sample-index) seed — mirrors BackendOutcomeSampler."""
        key = f"{self.seed}|{axis}|{item.get('id')}|{float(alpha):.6f}|{j}"
        return int(hashlib.sha256(key.encode("utf-8")).hexdigest(), 16) % (2 ** 31)

    def sample(
        self,
        axis: str,
        item: Dict,
        instruction: str,
        alpha: float,
        k: int,
        direction: np.ndarray,
        layer: int,
    ) -> adj.SampleBatch:
        """Return SampleBatch only (delegates to sample_with_texts)."""
        batch, _ = self.sample_with_texts(axis, item, instruction, alpha, k, direction, layer)
        return batch

    def sample_with_texts(
        self,
        axis: str,
        item: Dict,
        instruction: str,
        alpha: float,
        k: int,
        direction: np.ndarray,
        layer: int,
    ) -> Tuple[adj.SampleBatch, List[str]]:
        """Generate k steered responses; return (SampleBatch, raw_texts).

        Procedure:
          1. Build the task prompt via adj.format_task_input(axis, instruction, item).
          2. Generate k responses via SteeredHFBackend.generate() with per-sample
             deterministic seeds (same derivation as BackendOutcomeSampler).
          3. Score each response via adj.score_sample_outcome() (outcome in [0,1])
             and _scorers.degeneracy_score() (coherence gate input).
          4. Return (SampleBatch, [text_0, ..., text_{k-1}]).

        The caller (_eval_items_with_raw_pairs) passes raw_texts to
        parse_confidence() / item_is_correct() and records each pair with
        synthetic_proxy=False in the BrierRawStore.
        """
        text_input = adj.format_task_input(axis, instruction, item)
        steer = SteerConfig(direction=direction, alpha=float(alpha), layer=int(layer))
        outcomes: List[float] = []
        degens: List[float] = []
        texts: List[str] = []
        for j in range(int(k)):
            call_seed = self._call_seed(axis, item, alpha, j)
            try:
                out = self._hf.generate(
                    text_input, steer, self.max_new_tokens,
                    do_sample=self.do_sample, temperature=self.temperature,
                    seed=call_seed,
                )
            except TypeError:
                # Backends that don't accept do_sample/temperature/seed kwargs.
                out = self._hf.generate(text_input, steer, self.max_new_tokens)
            outcomes.append(adj.score_sample_outcome(axis, item, out))
            degens.append(_scorers.degeneracy_score(out))
            texts.append(out)
        return adj.SampleBatch(outcomes=outcomes, degeneracies=degens), texts
