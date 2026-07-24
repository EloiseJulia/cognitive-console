"""Steered-generation seam tests.

Model-independent by default: the SyntheticSteeredBackend and the hook contract
are tested with NO torch. The REAL SteeredHFBackend smoke test is GATED — it only
runs when torch + a local model are available AND the env flag is set, so the
offline suite stays green without torch/model.
"""

import importlib.util
import os

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
