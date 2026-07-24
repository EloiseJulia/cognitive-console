"""Steered text generation (C2b core capability) — real HF + synthetic offline.

This is the generation counterpart to `activations/provider.py`. The activation
provider is FORWARD-ONLY (single pass, no generation); this module actually
GENERATES text while ADDING a CAA steering vector to the residual stream, so we
can measure how the model's BEHAVIOR changes under latent steering (C2b), not
just how its activations project (C1).

Steering-hook contract
----------------------
Given a unit direction ``û`` (the CAA direction for an axis) and a coefficient
``alpha``, we register a PyTorch forward hook on ONE decoder block so that its
output residual-stream hidden state ``h`` becomes::

    h  ->  h + alpha * û          (added at EVERY token position of every forward)

* ``alpha`` and the injection layer are configurable.
* ``alpha == 0`` adds nothing, so generation is bit-identical to plain generation
  (verified in the CPU smoke test) — this is the unsteered control.
* The hook fires on every forward call, so with KV-caching it adds to all prompt
  positions on the prefill pass and to each newly-generated token afterwards,
  i.e. every generated position is steered. This matches standard CAA/RepE
  activation-addition steering (we add a fixed vector, we do NOT rescale the
  hidden state).

Layer-index convention (matches HFActivationProvider)
-----------------------------------------------------
``layer`` indexes the HuggingFace ``hidden_states`` tuple, where ``hidden_states[k]``
(k >= 1) is the residual stream AFTER decoder block ``k-1`` and ``hidden_states[0]``
is the embedding output. To steer the residual that becomes ``hidden_states[L]`` we
hook the OUTPUT of decoder block ``L-1``. Valid range: ``1 .. num_hidden_layers``.

torch/transformers are imported LAZILY inside methods, never at module import
time, so the package still imports (and the offline test suite still runs) when
those optional extras are absent.
"""

from __future__ import annotations

import abc
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

import numpy as np

_EPS = 1e-12

_HF_INSTALL_HINT = (
    "SteeredHFBackend needs torch + transformers (optional extras). Install, e.g.:\n"
    "  pip install torch --index-url https://download.pytorch.org/whl/cpu\n"
    "  pip install -e .[hf]"
)


def unit_vector(v) -> np.ndarray:
    """Return v / ||v|| as float64. Raises on a (near-)zero vector."""
    arr = np.asarray(v, dtype=np.float64).ravel()
    if arr.size == 0:
        raise ValueError("empty direction vector")
    norm = float(np.linalg.norm(arr))
    if norm < _EPS:
        raise ValueError("cannot steer along a (near-)zero direction")
    return arr / norm


@dataclass
class SteerConfig:
    """One steering configuration for a generation call."""
    direction: np.ndarray          # axis vector (need NOT be unit-norm; normalized here)
    alpha: float                   # steering coefficient (0 => unsteered)
    layer: int                     # hidden_states index to steer (hooks block layer-1)

    def unit(self) -> np.ndarray:
        return unit_vector(self.direction)


class GenBackend(abc.ABC):
    """Abstract steered-generation backend (the deferred model seam)."""

    @abc.abstractmethod
    def generate(
        self,
        prompt: str,
        steer: Optional[SteerConfig] = None,
        max_new_tokens: int = 128,
    ) -> str:
        """Generate a response to `prompt`, optionally steered by `steer`."""


# --------------------------------------------------------------------------- #
# Synthetic offline backend (deterministic, no torch)
# --------------------------------------------------------------------------- #
# Models ONE axis. Produces text whose `behavior_score(text, axis)` rises
# monotonically with an "intensity" = prompt_bias(prompt) + gain * alpha, so the
# whole C2b harness is exercisable offline with the REAL behavioral proxies.
_SYNTH_POS_SENTENCE = {
    "deliberation": (
        "First, let me think step by step. Second, I consider the reason. "
        "Therefore, working through it, "
    ),
    "skepticism": (
        "However, I doubt that premise. What is your evidence? "
        "That assumption is unsupported, so I question it. "
    ),
    "uncertainty_awareness": (
        "I might be wrong, and it is possibly uncertain. Perhaps it depends; "
        "I am not sure, so roughly probably. "
    ),
}


class SyntheticSteeredBackend(GenBackend):
    """Deterministic offline generator for ONE axis (no model, no torch).

    Construct with the axis it models plus an optional ``prompt_bias`` mapping
    (exact prompt string -> baseline intensity). ``generate`` emits text whose
    intensity = prompt_bias.get(prompt, 0) + gain * alpha, engineered so that
    ``experiments.behavior.behavior_score(text, axis)`` increases with intensity.
    This lets the reachability harness + proxies be unit-tested end-to-end with
    NO model.
    """

    def __init__(
        self,
        axis: str,
        prompt_bias: Optional[Dict[str, float]] = None,
        gain: float = 1.0,
        base_words: int = 40,
    ) -> None:
        self.axis = axis
        self.prompt_bias = dict(prompt_bias or {})
        self.gain = float(gain)
        self.base_words = int(base_words)

    def intensity(self, prompt: str, steer: Optional[SteerConfig]) -> float:
        alpha = float(steer.alpha) if steer is not None else 0.0
        return self.prompt_bias.get(prompt, 0.0) + self.gain * alpha

    def _text_for_intensity(self, intensity: float) -> str:
        if self.axis == "focus":
            # Focus: HIGH intensity => short, on-topic; LOW/negative => long + tangents.
            if intensity >= 1.0:
                return "The answer is 42."
            # more tangents / length as intensity drops
            n_tangent = int(max(0, round(3 - intensity)))
            n_filler = int(max(0, round(self.base_words * (2.0 - intensity))))
            tangent = "By the way, furthermore, on a related note, additionally, "
            filler = ("this relates to many other broad topics worth exploring "
                      "at length ") * max(1, n_filler // 8)
            return "The answer is 42. " + tangent * max(1, n_tangent) + filler

        sent = _SYNTH_POS_SENTENCE.get(self.axis)
        if sent is None:
            raise ValueError(f"SyntheticSteeredBackend: unknown axis {self.axis!r}")
        n = int(max(0, round(intensity * 3.0)))
        body = sent * n
        return ("The answer is 42. " + body).strip()

    def generate(
        self,
        prompt: str,
        steer: Optional[SteerConfig] = None,
        max_new_tokens: int = 128,
    ) -> str:
        return self._text_for_intensity(self.intensity(prompt, steer))


class SyntheticC2bTaskBackend(GenBackend):
    """Deterministic offline backend emitting SCORER-PARSEABLE task answers (no torch).

    For the C2b adjudication (``experiments.adjudicate_c2b``) the outcome scorers
    (``eval.scorers``) parse a numeric answer / a keyed MC letter / an answer +
    confidence. This backend produces exactly that text so the WHOLE adjudication
    pipeline — DEV/TEST split, α selection, paired cluster bootstrap, coherence
    gate, three-tier verdict — runs end-to-end offline with the REAL scorers.

    It is constructed with the axis and the item list, and looks up the item by
    finding its question (``item['prompt']``) as a substring of the generation
    prompt. An "intensity" drives correctness:

        intensity = prompt_gain * (instruction present?) + alpha_gain * |alpha|

    The item is answered CORRECTLY iff intensity >= ``threshold``. So a bounded
    prompt reaches ``prompt_gain`` and latent steering adds ``alpha_gain*|alpha|``
    on top — exactly the C2b "does steering reach beyond the prompt?" structure.
    Above ``degenerate_alpha`` the output is made repetitive (high degeneracy) so
    the coherence gate can be exercised.
    """

    def __init__(
        self,
        axis: str,
        items: Sequence[dict],
        instruction_markers: Optional[Sequence[str]] = None,
        prompt_gain: float = 0.4,
        alpha_gain: float = 0.1,
        threshold: float = 0.5,
        degenerate_alpha: Optional[float] = None,
    ) -> None:
        self.axis = axis
        self.items = list(items)
        self.instruction_markers = list(
            instruction_markers or ["think", "careful", "step", "skeptic", "premise",
                                    "confidence", "reason", "verify", "certain"]
        )
        self.prompt_gain = float(prompt_gain)
        self.alpha_gain = float(alpha_gain)
        self.threshold = float(threshold)
        self.degenerate_alpha = degenerate_alpha

    def _find_item(self, prompt: str) -> Optional[dict]:
        for it in self.items:
            q = str(it.get("prompt", "")).strip()
            if q and q in prompt:
                return it
        return None

    def _has_instruction(self, prompt: str) -> bool:
        low = prompt.lower()
        return any(m in low for m in self.instruction_markers)

    def generate(
        self,
        prompt: str,
        steer: Optional[SteerConfig] = None,
        max_new_tokens: int = 128,
    ) -> str:
        alpha = abs(float(steer.alpha)) if steer is not None else 0.0
        item = self._find_item(prompt)
        intensity = self.prompt_gain * (1.0 if self._has_instruction(prompt) else 0.0)
        intensity += self.alpha_gain * alpha
        correct = intensity >= self.threshold

        degenerate = self.degenerate_alpha is not None and alpha >= self.degenerate_alpha
        if item is None:
            body = "Answer: 0."
        elif self.axis == "deliberation":
            gold = str(item.get("answer", "0"))
            if correct:
                body = f"Let me work through it. Answer: {gold}."
            else:
                wrong = _perturb_number(gold)
                body = f"Let me work through it. Answer: {wrong}."
        elif self.axis == "skepticism":
            key = str(item.get("answer_letter", "B"))
            wrong_letter = "A" if key.upper() != "A" else "C"
            body = f"Answer: {key}." if correct else f"Answer: {wrong_letter}."
        elif self.axis == "uncertainty_awareness":
            gold = str(item.get("answer", ""))
            distractor = str(item.get("distractor", gold + " (other)"))
            if correct:
                body = f"Answer: {gold}. Confidence: 90%."
            else:
                body = f"Answer: {distractor}. Confidence: 30%."
        else:
            raise ValueError(f"SyntheticC2bTaskBackend: unknown axis {self.axis!r}")

        if degenerate:
            body = body + (" repeat repeat repeat" * 12)
        return body


def _perturb_number(gold: str) -> str:
    try:
        val = float(gold)
        return str(int(val + 1)) if val == int(val) else str(val + 1.0)
    except ValueError:
        return gold + "0"


# --------------------------------------------------------------------------- #
# Real transformers-backed steered generator
# --------------------------------------------------------------------------- #
class SteeredHFBackend(GenBackend):
    """Real causal-LM generator with residual-stream activation-addition steering.

    Loads an HF causal LM (default configurable; smoke-tested on Qwen2.5-1.5B on
    CPU, intended for Qwen2.5-7B on GPU). Generation is greedy by default
    (deterministic) so an alpha sweep is comparable. torch/transformers are
    imported lazily.
    """

    def __init__(
        self,
        model_name: str,
        device: str = "cpu",
        dtype: str = "float32",
        max_length: int = 512,
        seed: Optional[int] = None,
    ) -> None:
        self.model_name = model_name
        self.device = device
        self.dtype = dtype
        self.max_length = int(max_length)
        self.seed = None if seed is None else int(seed)
        self._model = None
        self._tokenizer = None
        self._config = None
        self._layers = None  # the decoder-block module list

    def _seed_torch(self, seed: Optional[int]) -> None:
        """Deterministically seed torch (global + all CUDA devices) from ``seed``.

        Sampled generation (``do_sample=True``) draws from torch's global RNG, so
        without seeding the k samples (and the whole verdict) are non-reproducible.
        Seeding before each generate call makes every (item, sample) reproducible
        across re-runs with the same run ``--seed`` (prereg reproducibility)."""
        if seed is None:
            return
        import torch

        torch.manual_seed(int(seed))
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(int(seed))

    # -- lazy load --------------------------------------------------------
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
        # Left-pad for batched generation: newly-generated tokens then start at the
        # SAME index (the padded length) for every row, so decoding each row's
        # continuation is a single slice. Single-sequence generate() is unaffected
        # (it tokenizes one prompt with no padding).
        self._tokenizer.padding_side = "left"
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
        self._layers = self._locate_decoder_layers(model)
        # Seed torch once at load so even an unseeded per-call path is reproducible.
        self._seed_torch(self.seed)

    @staticmethod
    def _locate_decoder_layers(model):
        """Find the ModuleList of decoder blocks (Qwen2/Llama: model.model.layers)."""
        for attr_path in ("model.layers", "transformer.h", "gpt_neox.layers", "model.decoder.layers"):
            obj = model
            ok = True
            for part in attr_path.split("."):
                if hasattr(obj, part):
                    obj = getattr(obj, part)
                else:
                    ok = False
                    break
            if ok:
                return obj
        raise RuntimeError(
            "could not locate decoder-block ModuleList on this model architecture"
        )

    @staticmethod
    def _render_user_chat_prompt(tokenizer, text: str, model_name: str = "unknown") -> str:
        """Render one user turn through model chat template when available."""
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

    @property
    def num_hidden_layers(self) -> int:
        self._ensure_loaded()
        return int(self._config.num_hidden_layers)

    @property
    def hidden_dim(self) -> int:
        self._ensure_loaded()
        return int(self._config.hidden_size)

    def available_layers(self) -> List[int]:
        self._ensure_loaded()
        return list(range(int(self._config.num_hidden_layers) + 1))

    # -- hook -------------------------------------------------------------
    def _make_hook(self, steer: SteerConfig):
        import torch

        u = steer.unit()
        alpha = float(steer.alpha)

        def hook(module, inputs, output):
            # A decoder block returns either a Tensor or a tuple whose [0] is the
            # residual-stream hidden state [batch, seq, hidden]. Add alpha*û to it.
            if isinstance(output, tuple):
                hidden = output[0]
            else:
                hidden = output
            vec = torch.as_tensor(u, dtype=hidden.dtype, device=hidden.device)
            hidden = hidden + alpha * vec
            if isinstance(output, tuple):
                return (hidden,) + tuple(output[1:])
            return hidden

        return hook

    def capture_residual_activations(
        self,
        prompts: Sequence[str],
        layer: int,
        *,
        steer: Optional[SteerConfig] = None,
    ) -> np.ndarray:
        """Capture last-token residual activations at one hidden-state layer.

        Returns shape ``[len(prompts), hidden_dim]``. When ``steer`` is provided,
        the same residual-addition hook used for generation is applied during the
        forward pass.
        """
        import torch

        self._ensure_loaded()
        layer = int(layer)
        n_layers = int(self._config.num_hidden_layers)
        if not (0 <= layer <= n_layers):
            raise ValueError(f"layer {layer} out of range 0..{n_layers}")

        prompts = list(prompts)
        if not prompts:
            return np.empty((0, self.hidden_dim), dtype=np.float32)

        texts = [
            self._render_user_chat_prompt(self._tokenizer, p, self.model_name)
            for p in prompts
        ]
        self._tokenizer.padding_side = "left"
        enc = self._tokenizer(
            texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=self.max_length,
        )
        enc = {k: v.to(self.device) for k, v in enc.items()}

        handle = None
        if steer is not None and abs(float(steer.alpha)) > _EPS:
            if not (1 <= int(steer.layer) <= n_layers):
                raise ValueError(
                    f"steer.layer {steer.layer} out of range 1..{n_layers} "
                    f"(hidden_states index; hooks decoder block layer-1)"
                )
            block = self._layers[int(steer.layer) - 1]
            handle = block.register_forward_hook(self._make_hook(steer))

        try:
            with torch.no_grad():
                out = self._model(**enc, output_hidden_states=True, use_cache=False)
        finally:
            if handle is not None:
                handle.remove()

        hs = out.hidden_states[layer]
        attn = enc.get("attention_mask")
        if attn is None:
            last = hs[:, -1, :]
        else:
            last_idx = attn.sum(dim=1) - 1
            rows = torch.arange(hs.shape[0], device=hs.device)
            last = hs[rows, last_idx, :]
        return last.to(torch.float32).cpu().numpy()

    # -- generation -------------------------------------------------------
    def generate(
        self,
        prompt: str,
        steer: Optional[SteerConfig] = None,
        max_new_tokens: int = 128,
        do_sample: bool = False,
        temperature: float = 1.0,
        seed: Optional[int] = None,
    ) -> str:
        import torch

        self._ensure_loaded()
        # Per-call deterministic seed (e.g. keyed on item + sample index) so re-
        # runs with the same run seed reproduce every sampled generation. Falls
        # back to the load-time seed when no per-call seed is supplied.
        self._seed_torch(seed if seed is not None else self.seed)
        text = self._render_user_chat_prompt(self._tokenizer, prompt, self.model_name)
        enc = self._tokenizer(
            text, return_tensors="pt", truncation=True, max_length=self.max_length
        )
        enc = {k: v.to(self.device) for k, v in enc.items()}
        input_len = enc["input_ids"].shape[1]

        handle = None
        # alpha==0 => no hook needed (bit-identical to plain generation).
        if steer is not None and abs(float(steer.alpha)) > _EPS:
            n = int(self._config.num_hidden_layers)
            if not (1 <= steer.layer <= n):
                raise ValueError(
                    f"steer.layer {steer.layer} out of range 1..{n} "
                    f"(hidden_states index; hooks decoder block layer-1)"
                )
            block = self._layers[steer.layer - 1]
            handle = block.register_forward_hook(self._make_hook(steer))

        try:
            gen_kwargs = dict(
                max_new_tokens=int(max_new_tokens),
                do_sample=bool(do_sample),
                pad_token_id=self._tokenizer.pad_token_id,
            )
            if do_sample:
                gen_kwargs["temperature"] = float(temperature)
            with torch.no_grad():
                out = self._model.generate(**enc, **gen_kwargs)
        finally:
            if handle is not None:
                handle.remove()

        new_tokens = out[0][input_len:]
        return self._tokenizer.decode(new_tokens, skip_special_tokens=True)

    # -- BATCHED generation (performance: FIX 3) ---------------------------
    def generate_batch(
        self,
        prompts: Sequence[str],
        steer: Optional[SteerConfig] = None,
        max_new_tokens: int = 128,
        seeds: Optional[Sequence[int]] = None,
        do_sample: bool = False,
        temperature: float = 1.0,
    ) -> List[str]:
        """Generate a whole PADDED batch in ONE forward loop on the GPU.

        The steering hook is registered on the shared decoder block, so it fires
        for the entire batch at once (``h -> h + alpha*û`` on every row/position).
        Left-padding + attention masks make each row's continuation a clean slice.

        Determinism (resume-safe): for sampled generation we derive ONE
        deterministic ``batch_seed`` from the per-(item,sample) ``seeds`` list and
        seed torch's global RNG with it before the single ``generate`` call. The
        batch is therefore reproducible for a fixed batch composition — the caller
        (``_channel_item_outcomes``) uses a FIXED, cache-independent chunking so a
        resumed run regenerates any incomplete batch with the identical
        composition and reproduces its outputs. Greedy (``do_sample=False``) uses
        no RNG, so a batch is bit-identical to the per-row single-sequence path.
        """
        import torch

        self._ensure_loaded()
        prompts = list(prompts)
        if not prompts:
            return []

        if do_sample:
            if seeds:
                key = "|".join(str(int(s)) for s in seeds)
            else:
                key = str(self.seed)
            batch_seed = int(hashlib.sha256(key.encode("utf-8")).hexdigest(), 16) % (2 ** 31)
            self._seed_torch(batch_seed)

        texts = [
            self._render_user_chat_prompt(self._tokenizer, p, self.model_name)
            for p in prompts
        ]
        self._tokenizer.padding_side = "left"
        enc = self._tokenizer(
            texts, return_tensors="pt", padding=True, truncation=True,
            max_length=self.max_length,
        )
        enc = {k: v.to(self.device) for k, v in enc.items()}
        input_len = enc["input_ids"].shape[1]

        handle = None
        if steer is not None and abs(float(steer.alpha)) > _EPS:
            n = int(self._config.num_hidden_layers)
            if not (1 <= steer.layer <= n):
                raise ValueError(
                    f"steer.layer {steer.layer} out of range 1..{n} "
                    f"(hidden_states index; hooks decoder block layer-1)"
                )
            block = self._layers[steer.layer - 1]
            handle = block.register_forward_hook(self._make_hook(steer))

        try:
            gen_kwargs = dict(
                max_new_tokens=int(max_new_tokens),
                do_sample=bool(do_sample),
                pad_token_id=self._tokenizer.pad_token_id,
            )
            if do_sample:
                gen_kwargs["temperature"] = float(temperature)
            with torch.no_grad():
                out = self._model.generate(**enc, **gen_kwargs)
        finally:
            if handle is not None:
                handle.remove()

        new = out[:, input_len:]
        return [self._tokenizer.decode(row, skip_special_tokens=True) for row in new]
