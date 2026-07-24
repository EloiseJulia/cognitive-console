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


def test_capture_residual_left_padding_matches_singleton(monkeypatch):
    class FakeTensor:
        def __init__(self, arr):
            self.arr = np.asarray(arr)

        @property
        def shape(self):
            return self.arr.shape

        def to(self, target=None):
            if target is np.float32:
                return FakeTensor(self.arr.astype(np.float32))
            return self

        def cpu(self):
            return self

        def numpy(self):
            return np.asarray(self.arr)

        def __getitem__(self, idx):
            return FakeTensor(self.arr[idx])

    class FakeNoGrad:
        def __enter__(self):
            return None

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakeTokenizer:
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
                "input_ids": FakeTensor(np.asarray(input_ids, dtype=np.int64)),
                "attention_mask": FakeTensor(np.asarray(attn, dtype=np.int64)),
            }

    class FakeModel:
        def __call__(self, **enc):
            ids = enc["input_ids"].numpy().astype(np.float32)
            hs = np.stack([ids, ids + 0.5, ids * 2.0], axis=-1)
            return types.SimpleNamespace(hidden_states=(None, FakeTensor(hs)))

    fake_torch = types.SimpleNamespace(float32=np.float32, no_grad=FakeNoGrad)
    monkeypatch.setitem(sys.modules, "torch", fake_torch)

    backend = SteeredHFBackend("fake-model")
    backend._ensure_loaded = lambda: None
    backend._config = types.SimpleNamespace(num_hidden_layers=1, hidden_size=3)
    backend._tokenizer = FakeTokenizer()
    backend._model = FakeModel()
    backend._layers = []

    prompts = ["A", "A much longer prompt", "mid size"]
    batched = backend.capture_residual_activations(prompts, layer=1)
    single = np.vstack(
        [backend.capture_residual_activations([prompt], layer=1)[0] for prompt in prompts]
    )
    np.testing.assert_allclose(batched, single)


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
