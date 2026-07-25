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
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

_DEFAULT_MODEL_HINT = (
    "GPU phase: load Llama-3-8B-Instruct / Qwen2.5-7B-Instruct via transformers "
    "and capture residual-stream activations; deferred until GPU is approved "
    "(AGENTS.md §5)."
)

_HF_INSTALL_HINT = (
    "The real HFActivationProvider needs torch + transformers, which are OPTIONAL "
    "extras (not installed by default). Install the CPU wheels, e.g.:\n"
    "  pip install torch --index-url https://download.pytorch.org/whl/cpu\n"
    "  pip install -e .[hf]"
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
    """Real transformers-backed activation provider — CPU-only implementation.

    Captures per-text hidden-state activations from a locally-run causal LM (no
    generation, single forward pass with ``output_hidden_states=True``). Built and
    validated on ``Qwen/Qwen2.5-0.5B-Instruct`` (Apache-2.0, ungated) running on
    CPU in float32, for the exploratory C1 "semantic facade" pilot.

    torch/transformers are imported LAZILY inside methods, never at module import
    time, so the whole package still imports and the offline unit-test suite still
    runs even when those optional extras are NOT installed.

    Layer indexing convention
    -------------------------
    ``layer`` indexes directly into HuggingFace's ``hidden_states`` tuple, which
    has ``num_hidden_layers + 1`` entries: ``hidden_states[0]`` is the embedding
    output (pre-block-0), and ``hidden_states[k]`` (k>=1) is the residual stream
    AFTER transformer block ``k-1``. So the valid range is ``0 .. num_hidden_layers``
    inclusive. ``available_layers()`` reflects exactly this range.

    Pooling
    -------
    Each text is rendered through the tokenizer chat template as a single USER
    turn (``add_generation_prompt=True``) and pooled at the LAST non-pad token of
    the requested hidden-state layer — the position whose residual stream has
    attended over the whole prompt, i.e. the model's summary state right before it
    would begin generating.

    On-disk cache
    -------------
    Every pooled vector is cached to ``.npy`` keyed by
    ``sha256(model, layer, pooling, device, dtype, text)`` under ``cache_dir`` so
    re-runs (e.g. the extraction pass then the probe pass) never recompute a
    forward for a text already seen. device/dtype are in the key so a warm
    cpu-fp32 cache is never reused for a gpu-fp16 run. The cache is regenerable
    and git-ignored.
    """

    _POOLING = "last_non_pad"

    def __init__(
        self,
        model_name: str,
        layers: Sequence[int] | None = None,
        device: str = "cpu",
        dtype: str = "float32",
        cache_dir: str | os.PathLike | None = None,
        max_length: int = 256,
    ) -> None:
        self.model_name = model_name
        self._layers = list(layers) if layers is not None else []
        self.device = device
        self.dtype = dtype
        self.max_length = int(max_length)
        if cache_dir is None:
            cache_dir = os.environ.get("COGNITIVE_CONSOLE_ACT_CACHE", ".act_cache")
        self.cache_dir = Path(cache_dir)
        # Lazily-populated handles (kept on the instance so we load the model once).
        self._model = None
        self._tokenizer = None
        self._config = None

    # -- ActivationProvider interface -------------------------------------
    @property
    def hidden_dim(self) -> int:
        self._ensure_loaded()
        return int(self._config.hidden_size)

    def available_layers(self) -> List[int]:
        # If the caller pinned an explicit layer set, honour it WITHOUT loading a
        # model (keeps config-naming / offline construction cheap and torch-free).
        if self._layers:
            return sorted(int(x) for x in self._layers)
        self._ensure_loaded()
        return list(range(int(self._config.num_hidden_layers) + 1))

    # -- model loading (lazy, torch/transformers optional) -----------------
    def _ensure_loaded(self):
        if self._model is not None:
            return
        try:
            import torch
            from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise NotImplementedError(_HF_INSTALL_HINT) from exc

        dtype = getattr(torch, self.dtype, torch.float32)
        self._config = AutoConfig.from_pretrained(self.model_name)
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        if self._tokenizer.pad_token is None:
            self._tokenizer.pad_token = self._tokenizer.eos_token
        # transformers >=5 renamed `torch_dtype` -> `dtype`; support both.
        try:
            model = AutoModelForCausalLM.from_pretrained(
                self.model_name, dtype=dtype, low_cpu_mem_usage=True
            )
        except TypeError:
            model = AutoModelForCausalLM.from_pretrained(
                self.model_name, torch_dtype=dtype, low_cpu_mem_usage=True
            )
        model.to(self.device)
        model.eval()
        self._model = model

    def hf_handles(self):
        """Return the loaded HF model/tokenizer/config for same-process sharing."""
        self._ensure_loaded()
        return self._model, self._tokenizer, self._config

    @staticmethod
    def _render_user_chat_prompt(tokenizer, text: str, model_name: str = "unknown") -> str:
        """Render one user turn through model chat template when available.

        Qwen/Llama instruct models both expose ``apply_chat_template``. For non-chat
        tokenizers, we fall back to raw text.
        """
        if hasattr(tokenizer, "apply_chat_template"):
            try:
                return tokenizer.apply_chat_template(
                    [{"role": "user", "content": text}],
                    tokenize=False,
                    add_generation_prompt=True,
                )
            except Exception as exc:
                tok_cls = tokenizer.__class__.__name__
                raise RuntimeError(
                    "tokenizer.apply_chat_template failed for "
                    f"model '{model_name}' (tokenizer={tok_cls})"
                ) from exc
        return text

    # -- disk cache --------------------------------------------------------
    def _cache_key(self, text: str, layer: int) -> str:
        h = hashlib.sha256()
        # device/dtype are part of the key: an fp16/cuda forward yields numerically
        # different activations than an fp32/cpu one, so a warm cpu-fp32 cache must
        # NOT be silently reused for a gpu-fp16 run (would corrupt the GPU results).
        for part in (self.model_name, str(layer), self._POOLING,
                     self.device, self.dtype, text):
            h.update(part.encode("utf-8"))
            h.update(b"\x1f")
        return h.hexdigest()

    def _cache_path(self, text: str, layer: int) -> Path:
        return self.cache_dir / f"{self._cache_key(text, layer)}.npy"

    def _load_cached(self, text: str, layer: int) -> Optional[np.ndarray]:
        path = self._cache_path(text, layer)
        if path.exists():
            try:
                return np.load(path)
            except Exception:  # noqa: BLE001 - a corrupt cache entry: recompute
                return None
        return None

    def _store_cached(self, text: str, layer: int, vec: np.ndarray) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        path = self._cache_path(text, layer)
        # NOTE: np.save appends ".npy" to a path unless a file OBJECT is passed,
        # so we write through an explicit handle to keep the tmp name exact and
        # make the os.replace atomic swap work.
        tmp = path.with_name(path.name + ".tmp")
        with open(tmp, "wb") as fh:
            np.save(fh, vec)
        os.replace(tmp, path)

    # -- forward pass ------------------------------------------------------
    def _forward_all_layers(self, text: str) -> Dict[int, np.ndarray]:
        """One forward pass, pooled at the last non-pad token for EVERY layer.

        A single forward already produces the whole ``hidden_states`` tuple, so we
        pool + cache every layer at once. This makes the layer scan cost one
        forward per text instead of one-per-(text, layer).
        """
        import torch

        prompt = self._render_user_chat_prompt(self._tokenizer, text, self.model_name)
        enc = self._tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=self.max_length,
        )
        enc = {k: v.to(self.device) for k, v in enc.items()}
        with torch.no_grad():
            out = self._model(**enc, output_hidden_states=True, use_cache=False)
        attn = enc.get("attention_mask")
        if attn is not None:
            nonpad = attn[0].nonzero(as_tuple=False).flatten()
            last_idx = int(nonpad[-1].item())
        else:
            last_idx = out.hidden_states[0].shape[1] - 1
        pooled: Dict[int, np.ndarray] = {}
        for ell, hs in enumerate(out.hidden_states):
            vec = hs[0, last_idx].to(torch.float32).cpu().numpy()
            pooled[ell] = np.asarray(vec, dtype=np.float32)
        return pooled

    def get_activations(self, texts: Sequence[str], layer: int) -> np.ndarray:
        texts = list(texts)
        layer = int(layer)
        results: List[Optional[np.ndarray]] = [None] * len(texts)

        # First serve everything we can from the disk cache (no model load needed).
        missing: List[int] = []
        for i, text in enumerate(texts):
            cached = self._load_cached(text, layer)
            if cached is not None:
                results[i] = np.asarray(cached, dtype=np.float32)
            else:
                missing.append(i)

        if missing:
            self._ensure_loaded()
            n_layers = int(self._config.num_hidden_layers)
            if not (0 <= layer <= n_layers):
                raise ValueError(
                    f"layer {layer} out of range 0..{n_layers} "
                    f"(hidden_states has {n_layers + 1} entries)"
                )
            for i in missing:
                pooled = self._forward_all_layers(texts[i])
                # Cache every layer from this single forward (cheap scan re-use).
                for ell, vec in pooled.items():
                    self._store_cached(texts[i], ell, vec)
                results[i] = pooled[layer]

        if not texts:
            self._ensure_loaded()
            return np.empty((0, int(self._config.hidden_size)), dtype=np.float32)
        return np.stack(results).astype(np.float32)
