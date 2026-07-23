"""ActivationProvider contract + synthetic (offline) and HF (stub) impls.

Contract
--------
`get_activations(texts, layer) -> np.ndarray` returns a float array of shape
`[len(texts), hidden_dim]`: one residual-stream (or hidden-state) activation
vector per input text at the requested layer. `available_layers()` lists the
layer indices the provider can serve. Nothing else in the pipeline is allowed to
touch a model directly — this is the single seam where the deferred GPU forward
pass will eventually plug in.

Synthetic provider (test double)
--------------------------------
`SyntheticActivationProvider` fabricates activations deterministically from a
seed so the whole pipeline is unit-testable with NO model, NO GPU, NO network.
Crucially it can *plant* a known axis signal:

* `plant_contrast(axis, pos_texts, neg_texts, magnitude, layer_gain)` makes the
  pos members exceed the neg members by `magnitude * gain(layer)` along a fixed,
  per-(axis,layer) planted unit direction. CAA extraction should then recover
  that direction, and the layer scan should pick the layer with the largest gain.
* `plant_facade(axis, prompt_text, vector_text, vector_magnitude,
  facade_fraction, layer)` makes the `vector_text` activation sit at
  `vector_magnitude` along the axis direction while the `prompt_text` activation
  reaches only `facade_fraction` of that — so the facade analysis recovers a
  facade_ratio ~= facade_fraction. `facade_fraction=1.0` => no gap;
  `facade_fraction=0.0` => the prompt carries no axis signal at all.

Everything is additive on top of deterministic per-(text,layer) Gaussian noise,
so means over many pairs cancel the noise and expose the planted signal.
"""

from __future__ import annotations

import abc
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple

import numpy as np

_DEFAULT_MODEL_HINT = (
    "GPU phase: load Llama-3-8B-Instruct / Qwen2.5-7B-Instruct via transformers "
    "and capture residual-stream activations; deferred until GPU is approved "
    "(AGENTS.md §5)."
)


class ActivationProvider(abc.ABC):
    """Abstract source of per-text activation vectors at a chosen layer."""

    @abc.abstractmethod
    def available_layers(self) -> List[int]:
        """Return the sorted list of layer indices this provider can serve."""

    @abc.abstractmethod
    def get_activations(self, texts: Sequence[str], layer: int) -> np.ndarray:
        """Return activations of shape [len(texts), hidden_dim] at `layer`."""

    @property
    @abc.abstractmethod
    def hidden_dim(self) -> int:
        """Dimensionality d of each activation vector."""

    def _check_layer(self, layer: int) -> None:
        if layer not in self.available_layers():
            raise ValueError(
                f"layer {layer} not available; have {self.available_layers()}"
            )


def _stable_rng(*parts: object) -> np.random.Generator:
    """Deterministic Generator seeded by a stable hash of `parts`.

    Uses hashlib (NOT Python's salted hash()) so results are identical across
    processes and runs — reproducibility is a hard requirement here.
    """
    key = "\x1f".join(str(p) for p in parts).encode("utf-8")
    digest = hashlib.sha256(key).digest()
    seed = int.from_bytes(digest[:8], "big", signed=False)
    return np.random.default_rng(seed)


def _planted_direction(dim: int, base_seed: int, axis: str, layer: int) -> np.ndarray:
    """A fixed unit direction for (axis, layer). Deterministic, unit-norm."""
    rng = _stable_rng("direction", base_seed, axis, layer)
    v = rng.standard_normal(dim)
    n = float(np.linalg.norm(v))
    return v / (n if n > 1e-12 else 1.0)


@dataclass
class _ContrastPlant:
    axis: str
    pos: frozenset
    neg: frozenset
    magnitude: float
    layer_gain: Dict[int, float]


@dataclass
class _FacadePlant:
    axis: str
    prompt_text: str
    vector_text: str
    vector_magnitude: float
    facade_fraction: float
    layer: int


class SyntheticActivationProvider(ActivationProvider):
    """Deterministic, seeded, offline activation source with planted signals."""

    def __init__(
        self,
        dim: int = 64,
        layers: Sequence[int] = (0, 1, 2, 3),
        seed: int = 0,
        noise_scale: float = 1.0,
    ) -> None:
        if dim <= 0:
            raise ValueError("dim must be positive")
        if not layers:
            raise ValueError("layers must be non-empty")
        self._dim = int(dim)
        self._layers = sorted(int(x) for x in layers)
        self._seed = int(seed)
        self._noise_scale = float(noise_scale)
        self._contrasts: List[_ContrastPlant] = []
        self._facades: List[_FacadePlant] = []

    # -- ActivationProvider interface -------------------------------------
    @property
    def hidden_dim(self) -> int:
        return self._dim

    def available_layers(self) -> List[int]:
        return list(self._layers)

    def direction(self, axis: str, layer: int) -> np.ndarray:
        """Expose the planted unit direction so tests can compare recovery."""
        return _planted_direction(self._dim, self._seed, axis, layer)

    def get_activations(self, texts: Sequence[str], layer: int) -> np.ndarray:
        self._check_layer(layer)
        texts = list(texts)
        out = np.empty((len(texts), self._dim), dtype=np.float64)
        for i, text in enumerate(texts):
            out[i] = self._activation_for(text, layer)
        return out

    # -- planting API ------------------------------------------------------
    def plant_contrast(
        self,
        axis: str,
        pos_texts: Sequence[str],
        neg_texts: Sequence[str],
        magnitude: float,
        layer_gain: Dict[int, float] | None = None,
    ) -> np.ndarray:
        """Plant a contrast signal along the (axis) direction.

        pos members get +magnitude/2 * gain(layer) * dir, neg get -that, so the
        mean difference (pos - neg) ~= magnitude * gain(layer) * dir. Returns the
        chosen-layer (max-gain) planted direction for convenience.
        """
        if layer_gain is None:
            layer_gain = {ell: 1.0 for ell in self._layers}
        for ell in layer_gain:
            self._check_layer(ell)
        self._contrasts.append(
            _ContrastPlant(
                axis=axis,
                pos=frozenset(pos_texts),
                neg=frozenset(neg_texts),
                magnitude=float(magnitude),
                layer_gain={int(k): float(v) for k, v in layer_gain.items()},
            )
        )
        best_layer = max(layer_gain, key=lambda k: layer_gain[k])
        return self.direction(axis, best_layer)

    def plant_facade(
        self,
        axis: str,
        prompt_text: str,
        vector_text: str,
        vector_magnitude: float,
        facade_fraction: float,
        layer: int,
    ) -> None:
        """Plant a strongest-prompt vs vector-only pair with a known facade gap.

        vector_text lands at `vector_magnitude` along dir(axis, layer);
        prompt_text lands at `facade_fraction * vector_magnitude`.
        """
        self._check_layer(layer)
        self._facades.append(
            _FacadePlant(
                axis=axis,
                prompt_text=prompt_text,
                vector_text=vector_text,
                vector_magnitude=float(vector_magnitude),
                facade_fraction=float(facade_fraction),
                layer=int(layer),
            )
        )

    # -- internals ---------------------------------------------------------
    def _activation_for(self, text: str, layer: int) -> np.ndarray:
        rng = _stable_rng("noise", self._seed, layer, text)
        vec = rng.standard_normal(self._dim) * self._noise_scale
        for c in self._contrasts:
            gain = c.layer_gain.get(layer, 0.0)
            if gain == 0.0:
                continue
            direction = _planted_direction(self._dim, self._seed, c.axis, layer)
            half = 0.5 * c.magnitude * gain
            if text in c.pos:
                vec = vec + half * direction
            elif text in c.neg:
                vec = vec - half * direction
        for f in self._facades:
            if f.layer != layer:
                continue
            direction = _planted_direction(self._dim, self._seed, f.axis, layer)
            if text == f.vector_text:
                vec = vec + f.vector_magnitude * direction
            elif text == f.prompt_text:
                vec = vec + f.facade_fraction * f.vector_magnitude * direction
        return vec


class HFActivationProvider(ActivationProvider):
    """Real transformers-backed provider — STUB (deferred to GPU phase).

    Instantiation is allowed (so configs can name it), but any activation
    capture raises NotImplementedError. torch/transformers are imported LAZILY
    inside methods, never at module import time, so the whole package imports
    and unit-tests without torch installed.
    """

    def __init__(
        self,
        model_name: str,
        layers: Sequence[int] | None = None,
        device: str = "cuda",
        dtype: str = "bfloat16",
    ) -> None:
        self.model_name = model_name
        self._layers = list(layers) if layers is not None else []
        self.device = device
        self.dtype = dtype

    @property
    def hidden_dim(self) -> int:
        raise NotImplementedError(_DEFAULT_MODEL_HINT)

    def available_layers(self) -> List[int]:
        if self._layers:
            return sorted(self._layers)
        raise NotImplementedError(_DEFAULT_MODEL_HINT)

    def _load(self):  # pragma: no cover - exercised only in the GPU phase
        # Lazy import keeps torch/transformers OPTIONAL for Phase 0.
        try:
            import torch  # noqa: F401
            from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: F401
        except ImportError as exc:  # pragma: no cover
            raise NotImplementedError(_DEFAULT_MODEL_HINT) from exc
        raise NotImplementedError(_DEFAULT_MODEL_HINT)

    def get_activations(self, texts: Sequence[str], layer: int) -> np.ndarray:
        raise NotImplementedError(_DEFAULT_MODEL_HINT)
