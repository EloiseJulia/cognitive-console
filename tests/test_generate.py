"""Steered-generation seam tests.

Model-independent by default: the SyntheticSteeredBackend and the hook contract
are tested with NO torch. The REAL SteeredHFBackend smoke test is GATED — it only
runs when torch + a local model are available AND the env flag is set, so the
offline suite stays green without torch/model.
"""

import importlib.util
import os
import sys
import types

import numpy as np
import pytest

from cognitive_console.steering.generate import (
    GenBackend,
    SteerConfig,
    SteeredHFBackend,
    SyntheticSteeredBackend,
    unit_vector,
)
from cognitive_console.experiments.behavior import behavior_score


def test_unit_vector_normalizes():
    v = unit_vector([3.0, 4.0])
    np.testing.assert_allclose(np.linalg.norm(v), 1.0)


def test_unit_vector_rejects_zero():
    with pytest.raises(ValueError):
        unit_vector([0.0, 0.0])


def test_synthetic_backend_is_genbackend():
    assert isinstance(SyntheticSteeredBackend("deliberation"), GenBackend)


@pytest.mark.parametrize("axis", ["deliberation", "skepticism", "uncertainty_awareness"])
def test_synthetic_alpha_increases_behavior(axis):
    backend = SyntheticSteeredBackend(axis)
    d = np.ones(8)
    s0 = behavior_score(backend.generate("prompt", SteerConfig(d, 0.0, 3)), axis)
    s_hi = behavior_score(backend.generate("prompt", SteerConfig(d, 4.0, 3)), axis)
    assert s_hi > s0


def test_synthetic_focus_alpha_increases_focus():
    backend = SyntheticSteeredBackend("focus")
    d = np.ones(8)
    s0 = behavior_score(backend.generate("prompt", SteerConfig(d, 0.0, 3)), "focus")
    s_hi = behavior_score(backend.generate("prompt", SteerConfig(d, 4.0, 3)), "focus")
    assert s_hi > s0


def test_synthetic_prompt_bias_lifts_unsteered():
    backend = SyntheticSteeredBackend("deliberation", prompt_bias={"strong": 3.0})
    d = np.ones(4)
    weak = behavior_score(backend.generate("weak", SteerConfig(d, 0.0, 3)), "deliberation")
    strong = behavior_score(backend.generate("strong", SteerConfig(d, 0.0, 3)), "deliberation")
    assert strong > weak


def test_synthetic_deterministic():
    b1 = SyntheticSteeredBackend("skepticism")
    b2 = SyntheticSteeredBackend("skepticism")
    d = np.arange(6, dtype=float) + 1
    assert b1.generate("p", SteerConfig(d, 2.0, 3)) == b2.generate("p", SteerConfig(d, 2.0, 3))


def test_hf_backend_chat_template_render_is_model_agnostic():
    class FakeTokenizer:
        def __init__(self, family):
            self.family = family

        def apply_chat_template(self, messages, tokenize, add_generation_prompt):
            assert tokenize is False
            assert add_generation_prompt is True
            return f"{self.family}:{messages[0]['role']}:{messages[0]['content']}"

    for family in ("qwen", "llama"):
        tok = FakeTokenizer(family)
        rendered = SteeredHFBackend._render_user_chat_prompt(tok, "hi")
        assert rendered == f"{family}:user:hi"


def test_hf_backend_chat_template_falls_back_to_raw_text():
    class PlainTokenizer:
        pass

    assert SteeredHFBackend._render_user_chat_prompt(PlainTokenizer(), "raw") == "raw"


def test_hf_backend_chat_template_error_is_explicit():
    class BrokenTokenizer:
        def apply_chat_template(self, messages, tokenize, add_generation_prompt):
            raise ValueError("boom")

    with pytest.raises(RuntimeError, match="apply_chat_template failed"):
        SteeredHFBackend._render_user_chat_prompt(
            BrokenTokenizer(), "raw", model_name="Qwen/Qwen2.5-1.5B-Instruct"
        )


def test_locate_decoder_layers_supports_llama_style_path():
    class Dummy:
        pass

    model = Dummy()
    model.model = Dummy()
    model.model.layers = ["l0", "l1", "l2"]
    got = SteeredHFBackend._locate_decoder_layers(model)
    assert got == ["l0", "l1", "l2"]


class _FakeTensor:
    def __init__(self, arr):
        self.arr = np.asarray(arr)

    @property
    def shape(self):
        return self.arr.shape

    @property
    def dtype(self):
        return self.arr.dtype

    @property
    def device(self):
        return "cpu"

    def to(self, target=None):
        if target is np.float32:
            return _FakeTensor(self.arr.astype(np.float32))
        return self

    def cpu(self):
        return self

    def numpy(self):
        return np.asarray(self.arr)

    def sum(self, dim):
        return _FakeTensor(self.arr.sum(axis=dim))

    def __add__(self, other):
        other_arr = other.arr if isinstance(other, _FakeTensor) else other
        return _FakeTensor(self.arr + other_arr)

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        other_arr = other.arr if isinstance(other, _FakeTensor) else other
        return _FakeTensor(self.arr - other_arr)

    def __mul__(self, other):
        other_arr = other.arr if isinstance(other, _FakeTensor) else other
        return _FakeTensor(self.arr * other_arr)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __getitem__(self, idx):
        if isinstance(idx, tuple):
            idx = tuple(i.arr if isinstance(i, _FakeTensor) else i for i in idx)
        elif isinstance(idx, _FakeTensor):
            idx = idx.arr
        return _FakeTensor(self.arr[idx])


class _FakeNoGrad:
    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeHandle:
    def __init__(self, hooks, fn):
        self._hooks = hooks
        self._fn = fn

    def remove(self):
        if self._fn in self._hooks:
            self._hooks.remove(self._fn)


class _FakeBlock:
    def __init__(self, bias):
        self._bias = float(bias)
        self._hooks = []
        self._pre_hooks = []

    def register_forward_hook(self, fn):
        self._hooks.append(fn)
        return _FakeHandle(self._hooks, fn)

    def register_forward_pre_hook(self, fn):
        self._pre_hooks.append(fn)
        return _FakeHandle(self._pre_hooks, fn)

    def forward(self, hidden):
        for pre_hook in list(self._pre_hooks):
            pre_hook(self, (hidden,))
        pre = hidden + self._bias
        output = (pre,)
        for hook in list(self._hooks):
            hooked = hook(self, (hidden,), output)
            if hooked is not None:
                output = hooked
        post = output[0] if isinstance(output, tuple) else output
        return pre, post


class _FakeTokenizer:
    def __init__(self):
        self.padding_side = "left"

    def __call__(self, texts, **kwargs):
        if isinstance(texts, str):
            texts = [texts]
        max_length = int(kwargs.get("max_length", 512))
        tokenized = []
        for text in texts:
            ids = [(ord(ch) % 17) + 1 for ch in str(text) if ch != " "]
            ids = ids[-max_length:] or [1]
            tokenized.append(ids)
        max_len = max(len(ids) for ids in tokenized)
        input_ids = []
        attn = []
        for ids in tokenized:
            pad = max_len - len(ids)
            input_ids.append(([0] * pad) + ids)
            attn.append(([0] * pad) + ([1] * len(ids)))
        return {
            "input_ids": _FakeTensor(np.asarray(input_ids, dtype=np.int64)),
            "attention_mask": _FakeTensor(np.asarray(attn, dtype=np.int64)),
        }


class _FakeModel:
    class _FakeBaseModel:
        def __init__(self, *, layers, hidden_size):
            self.layers = layers
            self._hidden_size = int(hidden_size)

        def __call__(self, **enc):
            enc.pop("use_cache", None)
            enc.pop("output_hidden_states", None)
            ids = enc["input_ids"].numpy().astype(np.float32)
            hidden = np.repeat(ids[..., None], self._hidden_size, axis=-1)
            hidden += np.arange(self._hidden_size, dtype=np.float32).reshape(1, 1, -1)
            cur = _FakeTensor(hidden)
            for block in self.layers:
                _pre, post = block.forward(cur)
                cur = post
            return types.SimpleNamespace(hidden_states=None)

    def __init__(self, n_layers, hidden_size):
        self.model = self._FakeBaseModel(
            layers=[_FakeBlock(i + 1) for i in range(n_layers)],
            hidden_size=hidden_size,
        )
        self._hidden_size = int(hidden_size)

    def __call__(self, **enc):
        output_hidden_states = bool(enc.pop("output_hidden_states", False))
        enc.pop("use_cache", None)

        ids = enc["input_ids"].numpy().astype(np.float32)
        hidden = np.repeat(ids[..., None], self._hidden_size, axis=-1)
        hidden += np.arange(self._hidden_size, dtype=np.float32).reshape(1, 1, -1)
        cur = _FakeTensor(hidden)

        all_hidden = [_FakeTensor(cur.numpy().copy())]
        for block in self.model.layers:
            pre, post = block.forward(cur)
            if output_hidden_states:
                # Simulate the HF ordering bug: hidden_states tracks pre-hook residuals.
                all_hidden.append(_FakeTensor(pre.numpy().copy()))
            cur = post

        return types.SimpleNamespace(
            hidden_states=tuple(all_hidden) if output_hidden_states else None
        )


def _install_fake_torch(monkeypatch):
    fake_torch = types.SimpleNamespace(
        float32=np.float32,
        no_grad=_FakeNoGrad,
        as_tensor=lambda arr, dtype=None, device=None: _FakeTensor(
            np.asarray(arr, dtype=dtype)
        ),
        arange=lambda n, device=None: _FakeTensor(np.arange(int(n), dtype=np.int64)),
    )
    monkeypatch.setitem(sys.modules, "torch", fake_torch)


def _build_fake_backend(monkeypatch, *, n_layers=2, hidden_size=4):
    _install_fake_torch(monkeypatch)
    backend = SteeredHFBackend("fake-model")
    backend._ensure_loaded = lambda: None
    backend._config = types.SimpleNamespace(
        num_hidden_layers=int(n_layers),
        hidden_size=int(hidden_size),
    )
    backend._tokenizer = _FakeTokenizer()
    backend._model = _FakeModel(n_layers=n_layers, hidden_size=hidden_size)
    backend._layers = backend._model.model.layers
    return backend


def test_capture_residual_left_padding_matches_singleton(monkeypatch):
    backend = _build_fake_backend(monkeypatch, n_layers=2, hidden_size=4)

    prompts = ["A", "A much longer prompt", "mid size"]
    batched = backend.capture_residual_activations(prompts, layer=1, batch_size=8)
    single = np.vstack(
        [backend.capture_residual_activations([prompt], layer=1)[0] for prompt in prompts]
    )
    np.testing.assert_allclose(batched, single)


def test_capture_residual_batching_is_equivalent(monkeypatch):
    backend = _build_fake_backend(monkeypatch, n_layers=2, hidden_size=4)
    prompts = ["alpha", "beta beta", "gamma gamma gamma", "delta"]
    one_shot = backend.capture_residual_activations(prompts, layer=1, batch_size=len(prompts))
    chunked = backend.capture_residual_activations(prompts, layer=1, batch_size=2)
    np.testing.assert_allclose(chunked, one_shot)


def test_capture_residual_unsteered_equals_zero_alpha_steer(monkeypatch):
    backend = _build_fake_backend(monkeypatch, n_layers=2, hidden_size=4)
    prompts = ["alpha beta", "gamma delta"]
    layer = 1
    direction = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float64)
    steer_zero = SteerConfig(direction=direction, alpha=0.0, layer=layer)
    baseline = backend.capture_residual_activations(prompts, layer=layer, steer=None)
    zero = backend.capture_residual_activations(prompts, layer=layer, steer=steer_zero)
    np.testing.assert_allclose(zero, baseline, rtol=0.0, atol=1e-6)


def test_capture_residual_steered_minus_baseline_matches_alpha_direction(monkeypatch):
    backend = _build_fake_backend(monkeypatch, n_layers=2, hidden_size=4)
    prompts = ["alpha beta", "gamma delta"]
    layer = 1
    alpha = 0.75
    direction = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float64)
    steer = SteerConfig(direction=direction, alpha=alpha, layer=layer)

    baseline = backend.capture_residual_activations(prompts, layer=layer, steer=None)
    steered = backend.capture_residual_activations(prompts, layer=layer, steer=steer)
    delta = steered - baseline
    expected = np.broadcast_to(
        (alpha * unit_vector(direction)).astype(np.float32),
        delta.shape,
    )

    assert not np.array_equal(steered, baseline)
    np.testing.assert_allclose(delta, expected, rtol=0.0, atol=1e-6)


def test_wrong_hook_order_captures_presteer_and_breaks_delta_equivalence(monkeypatch):
    backend = _build_fake_backend(monkeypatch, n_layers=1, hidden_size=4)
    block = backend._layers[0]
    direction = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float64)
    alpha = 0.5
    steer = SteerConfig(direction=direction, alpha=alpha, layer=1)
    expected = (alpha * unit_vector(direction)).astype(np.float32)[None, :]

    hidden = _FakeTensor(np.asarray([[[2.0, 4.0, 6.0, 8.0]]], dtype=np.float32))
    _, baseline_post = block.forward(hidden)
    baseline_last = baseline_post[:, -1, :].numpy()

    captured = {}

    def capture_hook(module, inputs, output):
        h = output[0] if isinstance(output, tuple) else output
        captured["last"] = h[:, -1, :]
        return output

    h_capture = block.register_forward_hook(capture_hook)
    h_steer = block.register_forward_hook(backend._make_hook(steer))
    try:
        block.forward(hidden)
    finally:
        h_steer.remove()
        h_capture.remove()

    delta = captured["last"].numpy() - baseline_last
    np.testing.assert_allclose(delta, np.zeros_like(delta), rtol=0.0, atol=1e-6)
    with pytest.raises(AssertionError):
        np.testing.assert_allclose(delta, expected, rtol=0.0, atol=1e-6)


# --------------------------------------------------------------------------- #
# GATED real-model smoke test (skipped unless torch + model + env flag)
# --------------------------------------------------------------------------- #
_HAS_TORCH = importlib.util.find_spec("torch") is not None
_HAS_TF = importlib.util.find_spec("transformers") is not None
_SMOKE = os.environ.get("COGNITIVE_CONSOLE_GPU_SMOKE") == "1"
_SMOKE_MODEL = os.environ.get("COGNITIVE_CONSOLE_SMOKE_MODEL", "Qwen/Qwen2.5-1.5B-Instruct")


@pytest.mark.skipif(
    not (_HAS_TORCH and _HAS_TF and _SMOKE),
    reason="real-model smoke test: set COGNITIVE_CONSOLE_GPU_SMOKE=1 with torch+transformers+model",
)
def test_real_steered_generation_alpha0_matches_plain():
    backend = SteeredHFBackend(_SMOKE_MODEL, device="cpu", dtype="float32")
    d = np.ones(backend.hidden_dim)
    layer = max(1, backend.num_hidden_layers // 2)
    plain = backend.generate("Tell me about the moon.", None, max_new_tokens=16)
    a0 = backend.generate(
        "Tell me about the moon.", SteerConfig(d, 0.0, layer), max_new_tokens=16
    )
    assert plain == a0  # alpha=0 must be bit-identical to unsteered


@pytest.mark.skipif(
    not (_HAS_TORCH and _HAS_TF and _SMOKE),
    reason="real-model smoke test: set COGNITIVE_CONSOLE_GPU_SMOKE=1 with torch+transformers+model",
)
def test_batched_vs_unbatched_greedy_identical():
    """FIX 3: a padded GREEDY batch must reproduce the per-sequence outputs exactly
    (no RNG), so batching never changes greedy outcomes for the same inputs."""
    backend = SteeredHFBackend(_SMOKE_MODEL, device="cpu", dtype="float32")
    d = np.ones(backend.hidden_dim)
    layer = max(1, backend.num_hidden_layers // 2)
    steer = SteerConfig(d, 6.0, layer)
    prompts = ["What is 2+2?", "Name a color.", "Is the sky blue?"]
    single = [backend.generate(p, steer, max_new_tokens=16) for p in prompts]
    batched = backend.generate_batch(prompts, steer, max_new_tokens=16, do_sample=False)
    assert batched == single


@pytest.mark.skipif(
    not (_HAS_TORCH and _HAS_TF and _SMOKE),
    reason="real-model smoke test: set COGNITIVE_CONSOLE_GPU_SMOKE=1 with torch+transformers+model",
)
def test_batched_sampled_is_deterministic_and_well_formed():
    """FIX 3: SAMPLED batched generation is deterministic for a fixed batch
    composition/seeds (reproducible -> resume-safe) and yields one output per row.
    (Bit-identity to the per-row seeded path is NOT required — samples are only
    required to be statistically equivalent; here we assert reproducibility.)"""
    backend = SteeredHFBackend(_SMOKE_MODEL, device="cpu", dtype="float32")
    d = np.ones(backend.hidden_dim)
    layer = max(1, backend.num_hidden_layers // 2)
    steer = SteerConfig(d, 6.0, layer)
    prompts = ["Tell me about the moon.", "Tell me about the sun."]
    seeds = [11, 22]
    a = backend.generate_batch(prompts, steer, max_new_tokens=16, seeds=seeds,
                               do_sample=True, temperature=0.7)
    b = backend.generate_batch(prompts, steer, max_new_tokens=16, seeds=seeds,
                               do_sample=True, temperature=0.7)
    assert a == b  # same seeds + composition -> reproducible
    assert len(a) == len(prompts)
