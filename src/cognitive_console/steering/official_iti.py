"""Official-style sparse attention-head ITI for the TruthfulQA positive control.

This module is deliberately separate from :mod:`cognitive_console.steering.iti`.
The existing module implements the frozen single-layer residual-stream ITI cell;
this module implements the published-style intervention at selected attention
head outputs immediately before ``self_attn.o_proj``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

from .generate import SteeredHFBackend, unit_vector

_EPS = 1e-12


def _array_sha256(array: np.ndarray) -> str:
    import hashlib

    return hashlib.sha256(
        np.asarray(array, dtype=np.float64).ravel().tobytes()
    ).hexdigest()


@dataclass(frozen=True)
class ITIHeadSpec:
    layer: int
    head: int
    direction: np.ndarray
    sigma: float
    validation_accuracy: float

    def __post_init__(self) -> None:
        direction = np.asarray(self.direction, dtype=np.float64).ravel()
        if direction.size == 0 or not np.isfinite(direction).all():
            raise ValueError("ITI head direction must be finite and non-empty")
        norm = float(np.linalg.norm(direction))
        if abs(norm - 1.0) > 1e-6:
            raise ValueError("ITI head direction must be unit-normalized")
        if not np.isfinite(self.sigma) or self.sigma < 0.0:
            raise ValueError("ITI head sigma must be finite and non-negative")
        object.__setattr__(self, "direction", direction)

    @property
    def direction_sha256(self) -> str:
        return _array_sha256(self.direction)

    def to_dict(self) -> Dict[str, object]:
        return {
            "layer": int(self.layer),
            "head": int(self.head),
            "direction": [float(x) for x in self.direction],
            "direction_sha256": self.direction_sha256,
            "sigma": float(self.sigma),
            "validation_accuracy": float(self.validation_accuracy),
        }

    @classmethod
    def from_dict(cls, row: Dict[str, object]) -> "ITIHeadSpec":
        spec = cls(
            layer=int(row["layer"]),
            head=int(row["head"]),
            direction=np.asarray(row["direction"], dtype=np.float64),
            sigma=float(row["sigma"]),
            validation_accuracy=float(row["validation_accuracy"]),
        )
        expected = row.get("direction_sha256")
        if expected is not None and expected != spec.direction_sha256:
            raise ValueError("persisted ITI head direction hash mismatch")
        return spec


@dataclass(frozen=True)
class OfficialITIConfig:
    specs: Tuple[ITIHeadSpec, ...]
    alpha: float
    num_attention_heads: int
    head_dim: int
    method: str = "official_style_sparse_attention_head_iti"

    def __post_init__(self) -> None:
        if not self.specs:
            raise ValueError("official ITI config requires at least one head")
        if self.num_attention_heads <= 0 or self.head_dim <= 0:
            raise ValueError("invalid attention-head geometry")
        seen = set()
        for spec in self.specs:
            key = (int(spec.layer), int(spec.head))
            if key in seen:
                raise ValueError(f"duplicate ITI head {key}")
            seen.add(key)
            if not (0 <= spec.head < self.num_attention_heads):
                raise ValueError(f"head {spec.head} outside model geometry")
            if spec.direction.size != self.head_dim:
                raise ValueError("head direction dimension mismatch")

    @property
    def hidden_size(self) -> int:
        return int(self.num_attention_heads * self.head_dim)

    def by_layer(self) -> Dict[int, List[ITIHeadSpec]]:
        out: Dict[int, List[ITIHeadSpec]] = {}
        for spec in self.specs:
            out.setdefault(int(spec.layer), []).append(spec)
        for layer in out:
            out[layer].sort(key=lambda row: row.head)
        return out

    def to_dict(self) -> Dict[str, object]:
        return {
            "method": self.method,
            "alpha": float(self.alpha),
            "num_attention_heads": int(self.num_attention_heads),
            "head_dim": int(self.head_dim),
            "top_k": len(self.specs),
            "specs": [spec.to_dict() for spec in self.specs],
        }

    @classmethod
    def from_dict(cls, row: Dict[str, object]) -> "OfficialITIConfig":
        return cls(
            specs=tuple(ITIHeadSpec.from_dict(x) for x in row["specs"]),
            alpha=float(row["alpha"]),
            num_attention_heads=int(row["num_attention_heads"]),
            head_dim=int(row["head_dim"]),
            method=str(row.get("method", "official_style_sparse_attention_head_iti")),
        )


def fit_official_iti(
    train_activations: np.ndarray,
    train_labels: Sequence[int],
    validation_activations: np.ndarray,
    validation_labels: Sequence[int],
    *,
    top_k: int = 48,
    alpha: float = 15.0,
) -> OfficialITIConfig:
    """Fit per-head probes, select top heads, and derive COM directions.

    Activations have shape ``[examples, layers, heads, head_dim]``. Probe
    validation accuracy selects heads. The actual intervention direction is the
    center-of-mass difference ``mean(true)-mean(false)`` over the combined outer
    training partition, matching the official ``--use_center_of_mass`` recipe.
    """

    train = np.asarray(train_activations, dtype=np.float64)
    valid = np.asarray(validation_activations, dtype=np.float64)
    y_train = np.asarray(train_labels, dtype=np.int64)
    y_valid = np.asarray(validation_labels, dtype=np.int64)
    if train.ndim != 4 or valid.ndim != 4 or train.shape[1:] != valid.shape[1:]:
        raise ValueError("ITI activations must be matching [n,l,h,d] arrays")
    if len(train) != len(y_train) or len(valid) != len(y_valid):
        raise ValueError("activation/label length mismatch")
    if set(np.unique(y_train)) != {0, 1} or set(np.unique(y_valid)) != {0, 1}:
        raise ValueError("both train and validation labels must contain 0 and 1")
    n_layers, n_heads, head_dim = train.shape[1:]
    candidates: List[Tuple[float, int, int, np.ndarray, float]] = []
    combined = np.concatenate([train, valid], axis=0)
    combined_y = np.concatenate([y_train, y_valid], axis=0)
    try:
        from sklearn.linear_model import LogisticRegression
    except ImportError as exc:  # pragma: no cover - declared in the HF extra
        raise NotImplementedError(
            "official-style ITI probe fitting requires scikit-learn"
        ) from exc

    for layer in range(n_layers):
        for head in range(n_heads):
            x_train = train[:, layer, head, :]
            probe = LogisticRegression(
                random_state=42,
                max_iter=1000,
            )
            probe.fit(x_train, y_train)
            accuracy = float(probe.score(valid[:, layer, head, :], y_valid))

            all_head = combined[:, layer, head, :]
            com = all_head[combined_y == 1].mean(axis=0) - all_head[
                combined_y == 0
            ].mean(axis=0)
            direction = unit_vector(com)
            projections = all_head @ direction
            sigma = float(np.std(projections, ddof=1))
            candidates.append((accuracy, layer, head, direction, sigma))

    if not (1 <= int(top_k) <= len(candidates)):
        raise ValueError("top_k outside available head count")
    candidates.sort(key=lambda row: (-row[0], row[1], row[2]))
    specs = tuple(
        ITIHeadSpec(
            layer=layer,
            head=head,
            direction=direction,
            sigma=sigma,
            validation_accuracy=accuracy,
        )
        for accuracy, layer, head, direction, sigma in candidates[: int(top_k)]
    )
    return OfficialITIConfig(
        specs=specs,
        alpha=float(alpha),
        num_attention_heads=int(n_heads),
        head_dim=int(head_dim),
    )


def matched_random_config(config: OfficialITIConfig, seed: int) -> OfficialITIConfig:
    """Random unit directions on the same heads with the same sigma and alpha."""

    rng = np.random.default_rng(int(seed))
    specs = tuple(
        ITIHeadSpec(
            layer=spec.layer,
            head=spec.head,
            direction=unit_vector(rng.standard_normal(config.head_dim)),
            sigma=spec.sigma,
            validation_accuracy=spec.validation_accuracy,
        )
        for spec in config.specs
    )
    return OfficialITIConfig(
        specs=specs,
        alpha=config.alpha,
        num_attention_heads=config.num_attention_heads,
        head_dim=config.head_dim,
        method="matched_random_attention_head_control",
    )


def expected_layer_delta(config: OfficialITIConfig, layer: int) -> np.ndarray:
    delta = np.zeros(config.hidden_size, dtype=np.float64)
    for spec in config.by_layer().get(int(layer), []):
        start = spec.head * config.head_dim
        delta[start : start + config.head_dim] += (
            float(config.alpha) * float(spec.sigma) * spec.direction
        )
    return delta


def hook_bite_metrics(
    before_by_layer: Dict[int, np.ndarray],
    after_by_layer: Dict[int, np.ndarray],
    config: OfficialITIConfig,
    *,
    relative_tolerance: float = 0.05,
    absolute_tolerance: float = 2e-3,
) -> Dict[str, object]:
    expected_layers = set(config.by_layer())
    if set(before_by_layer) != expected_layers or set(after_by_layer) != expected_layers:
        raise ValueError("ITI hook-bites layer coverage mismatch")
    rows: Dict[str, object] = {}
    passed = True
    for layer in sorted(expected_layers):
        before = np.asarray(before_by_layer[layer], dtype=np.float64)
        after = np.asarray(after_by_layer[layer], dtype=np.float64)
        if before.shape != after.shape or before.shape[-1] != config.hidden_size:
            raise ValueError("ITI hook-bites tensor shape mismatch")
        expected = expected_layer_delta(config, layer)
        observed = after - before
        error = observed - expected
        denom = max(float(np.linalg.norm(expected)), _EPS)
        relative_error = float(
            np.max(np.linalg.norm(error.reshape(-1, config.hidden_size), axis=1))
            / denom
        )
        max_abs_error = float(np.max(np.abs(error)))
        non_vacuous = float(np.linalg.norm(expected)) > _EPS
        row_pass = bool(
            non_vacuous
            and (
                relative_error <= float(relative_tolerance)
                or max_abs_error <= float(absolute_tolerance)
            )
        )
        passed = passed and row_pass
        rows[str(layer)] = {
            "expected_delta_norm": float(np.linalg.norm(expected)),
            "relative_error": relative_error,
            "max_abs_error": max_abs_error,
            "non_vacuous": non_vacuous,
            "passed": row_pass,
        }
    return {
        "passed": bool(passed),
        "relative_tolerance": float(relative_tolerance),
        "absolute_tolerance": float(absolute_tolerance),
        "layers": rows,
    }


class OfficialITIHFBackend(SteeredHFBackend):
    """Llama-compatible head-output collector and official-style ITI generator."""

    @staticmethod
    def _render_protocol_prompt(text: str) -> str:
        """Use the official repository's plain `Q: ... A:` tokenization path."""

        return str(text)

    @classmethod
    def from_pretrained(
        cls,
        model_name: str,
        *,
        revision: str,
        device: str,
        dtype: str,
        max_length: int,
        seed: int,
    ) -> "OfficialITIHFBackend":
        import torch
        from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer

        torch_dtype = getattr(torch, dtype)
        config = AutoConfig.from_pretrained(model_name, revision=revision)
        tokenizer = AutoTokenizer.from_pretrained(model_name, revision=revision)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        try:
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                revision=revision,
                dtype=torch_dtype,
                low_cpu_mem_usage=True,
            )
        except TypeError:
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                revision=revision,
                torch_dtype=torch_dtype,
                low_cpu_mem_usage=True,
            )
        model.to(device)
        model.eval()
        resolved = getattr(config, "_commit_hash", None)
        if resolved is not None and resolved != revision:
            raise ValueError(
                f"resolved model revision mismatch: expected={revision}, actual={resolved}"
            )
        return cls(
            model_name,
            device=device,
            dtype=dtype,
            max_length=max_length,
            seed=seed,
            model=model,
            tokenizer=tokenizer,
            config=config,
        )

    @property
    def num_attention_heads(self) -> int:
        self._ensure_loaded()
        return int(self._config.num_attention_heads)

    @property
    def head_dim(self) -> int:
        hidden = self.hidden_dim
        heads = self.num_attention_heads
        if hidden % heads:
            raise ValueError("hidden size is not divisible by attention-head count")
        return hidden // heads

    def _o_proj_modules(self) -> List[object]:
        self._ensure_loaded()
        modules = []
        for index, block in enumerate(self._layers):
            attn = getattr(block, "self_attn", None)
            o_proj = getattr(attn, "o_proj", None)
            if o_proj is None:
                raise ValueError(f"decoder layer {index} lacks self_attn.o_proj")
            modules.append(o_proj)
        return modules

    def _validate_iti_geometry(self, config: OfficialITIConfig) -> None:
        if config.num_attention_heads != self.num_attention_heads:
            raise ValueError("ITI config attention-head count mismatch")
        if config.head_dim != self.head_dim:
            raise ValueError("ITI config head dimension mismatch")
        n_layers = self.num_hidden_layers
        for layer in config.by_layer():
            if not (0 <= layer < n_layers):
                raise ValueError(f"ITI layer {layer} outside decoder range")

    @staticmethod
    def _make_iti_pre_hook(
        layer_specs: Sequence[ITIHeadSpec],
        *,
        alpha: float,
        head_dim: int,
        stats: Optional[Dict[str, List[np.ndarray]]] = None,
    ):
        def hook(module, inputs):
            import torch

            if not inputs:
                raise RuntimeError("o_proj pre-hook received no inputs")
            hidden = inputs[0]
            if hidden.ndim != 3:
                raise ValueError("o_proj input must be [batch, sequence, hidden]")
            edited = hidden.clone()
            before = hidden[:, -1, :].detach().to(torch.float32)
            for spec in layer_specs:
                start = int(spec.head) * int(head_dim)
                stop = start + int(head_dim)
                direction = torch.as_tensor(
                    spec.direction, dtype=edited.dtype, device=edited.device
                )
                edited[:, -1, start:stop] = (
                    edited[:, -1, start:stop]
                    + float(alpha) * float(spec.sigma) * direction
                )
            if stats is not None:
                stats.setdefault("before", []).append(before.cpu().numpy())
                stats.setdefault("after", []).append(
                    edited[:, -1, :].detach().to(torch.float32).cpu().numpy()
                )
            return (edited,) + tuple(inputs[1:])

        return hook

    def _register_iti_hooks(
        self,
        config: OfficialITIConfig,
        *,
        stats_by_layer: Optional[Dict[int, Dict[str, List[np.ndarray]]]] = None,
    ) -> List[object]:
        self._validate_iti_geometry(config)
        modules = self._o_proj_modules()
        handles: List[object] = []
        try:
            for layer, specs in config.by_layer().items():
                stats = None if stats_by_layer is None else stats_by_layer.setdefault(layer, {})
                handles.append(
                    modules[layer].register_forward_pre_hook(
                        self._make_iti_pre_hook(
                            specs,
                            alpha=config.alpha,
                            head_dim=config.head_dim,
                            stats=stats,
                        )
                    )
                )
        except Exception:
            for handle in reversed(handles):
                handle.remove()
            raise
        return handles

    def collect_head_activations(
        self,
        prompts: Sequence[str],
        *,
        batch_size: int = 8,
    ) -> np.ndarray:
        """Collect last-token ``o_proj`` inputs as ``[n,l,h,d]``."""

        import torch

        self._ensure_loaded()
        prompts = list(prompts)
        if not prompts:
            return np.empty(
                (0, self.num_hidden_layers, self.num_attention_heads, self.head_dim),
                dtype=np.float32,
            )
        modules = self._o_proj_modules()
        rows: List[np.ndarray] = []
        for start in range(0, len(prompts), int(batch_size)):
            batch = prompts[start : start + int(batch_size)]
            rendered = [
                self._render_protocol_prompt(text)
                for text in batch
            ]
            enc = self._tokenizer(
                rendered,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=self.max_length,
            )
            enc = {key: value.to(self.device) for key, value in enc.items()}
            captured: Dict[int, np.ndarray] = {}
            handles = []
            try:
                for layer, module in enumerate(modules):
                    def make_capture(layer_index):
                        def capture(mod, inputs):
                            if not inputs:
                                raise RuntimeError("attention capture hook received no inputs")
                            captured[layer_index] = (
                                inputs[0][:, -1, :]
                                .detach()
                                .to(torch.float32)
                                .cpu()
                                .numpy()
                            )
                            return None

                        return capture

                    handles.append(
                        module.register_forward_pre_hook(make_capture(layer))
                    )
                base_model = getattr(self._model, "model", self._model)
                with torch.no_grad():
                    base_model(**enc, use_cache=False)
            finally:
                for handle in reversed(handles):
                    handle.remove()
            if set(captured) != set(range(self.num_hidden_layers)):
                raise RuntimeError("not every decoder attention head was captured")
            stacked = np.stack(
                [captured[layer] for layer in range(self.num_hidden_layers)], axis=1
            )
            rows.append(
                stacked.reshape(
                    len(batch),
                    self.num_hidden_layers,
                    self.num_attention_heads,
                    self.head_dim,
                )
            )
        return np.concatenate(rows, axis=0)

    def assert_hook_bites(
        self,
        prompts: Sequence[str],
        config: OfficialITIConfig,
    ) -> Dict[str, object]:
        import torch

        rendered = [
            self._render_protocol_prompt(text)
            for text in prompts
        ]
        enc = self._tokenizer(
            rendered,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=self.max_length,
        )
        enc = {key: value.to(self.device) for key, value in enc.items()}
        stats: Dict[int, Dict[str, List[np.ndarray]]] = {}
        handles = self._register_iti_hooks(config, stats_by_layer=stats)
        try:
            base_model = getattr(self._model, "model", self._model)
            with torch.no_grad():
                base_model(**enc, use_cache=False)
        finally:
            for handle in reversed(handles):
                handle.remove()
        before = {
            layer: np.concatenate(row["before"], axis=0) for layer, row in stats.items()
        }
        after = {
            layer: np.concatenate(row["after"], axis=0) for layer, row in stats.items()
        }
        result = hook_bite_metrics(before, after, config)
        if not result["passed"]:
            raise AssertionError(f"official ITI hook-bites failed: {result}")
        return result

    def generate_with_metadata(
        self,
        prompt: str,
        *,
        config: Optional[OfficialITIConfig],
        max_new_tokens: int,
        do_sample: bool,
        temperature: float,
        seed: int,
    ) -> Tuple[str, int, bool]:
        import torch

        self._ensure_loaded()
        self._seed_torch(seed)
        rendered = self._render_protocol_prompt(prompt)
        enc = self._tokenizer(
            rendered,
            return_tensors="pt",
            truncation=True,
            max_length=self.max_length,
        )
        enc = {key: value.to(self.device) for key, value in enc.items()}
        input_len = int(enc["input_ids"].shape[1])
        handles = [] if config is None else self._register_iti_hooks(config)
        try:
            kwargs = {
                "max_new_tokens": int(max_new_tokens),
                "do_sample": bool(do_sample),
                "pad_token_id": self._tokenizer.pad_token_id,
            }
            if do_sample:
                kwargs["temperature"] = float(temperature)
            with torch.no_grad():
                output = self._model.generate(**enc, **kwargs)
        finally:
            for handle in reversed(handles):
                handle.remove()
        generated = output[0][input_len:]
        token_count = int(generated.shape[0])
        text = self._tokenizer.decode(generated, skip_special_tokens=True).strip()
        eos_id = getattr(self._tokenizer, "eos_token_id", None)
        ended_with_eos = bool(
            token_count and eos_id is not None and int(generated[-1]) == int(eos_id)
        )
        truncated = bool(token_count >= int(max_new_tokens) and not ended_with_eos)
        return text, token_count, truncated
