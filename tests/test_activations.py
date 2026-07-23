"""ActivationProvider seam: synthetic determinism/planting + HF stub (no torch)."""

import sys

import numpy as np
import pytest

from cognitive_console.activations import (
    ActivationProvider,
    HFActivationProvider,
    SyntheticActivationProvider,
)


def test_synthetic_shape_and_layers():
    prov = SyntheticActivationProvider(dim=32, layers=[4, 8, 12], seed=0)
    assert prov.available_layers() == [4, 8, 12]
    assert prov.hidden_dim == 32
    acts = prov.get_activations(["a", "b", "c"], layer=8)
    assert acts.shape == (3, 32)


def test_synthetic_is_deterministic():
    p1 = SyntheticActivationProvider(dim=16, layers=[0, 1], seed=7)
    p2 = SyntheticActivationProvider(dim=16, layers=[0, 1], seed=7)
    a1 = p1.get_activations(["x", "y"], 1)
    a2 = p2.get_activations(["x", "y"], 1)
    np.testing.assert_allclose(a1, a2)
    # Different seed => different activations (with overwhelming probability).
    p3 = SyntheticActivationProvider(dim=16, layers=[0, 1], seed=8)
    a3 = p3.get_activations(["x", "y"], 1)
    assert not np.allclose(a1, a3)


def test_unknown_layer_raises():
    prov = SyntheticActivationProvider(dim=8, layers=[0, 1])
    with pytest.raises(ValueError):
        prov.get_activations(["a"], layer=99)


def test_planted_contrast_recovers_direction_and_magnitude():
    # With enough pairs, the mean pos-neg difference should align with the
    # planted unit direction and have norm ~= planted magnitude (noise cancels
    # at rate ~sqrt(2*dim/n), so we use enough pairs to clear that floor).
    prov = SyntheticActivationProvider(dim=128, layers=[5], seed=3, noise_scale=1.0)
    pos = [f"pos-{i}" for i in range(200)]
    neg = [f"neg-{i}" for i in range(200)]
    prov.plant_contrast("focus", pos, neg, magnitude=6.0, layer_gain={5: 1.0})
    p = prov.get_activations(pos, 5)
    n = prov.get_activations(neg, 5)
    mean_diff = p.mean(axis=0) - n.mean(axis=0)
    planted = prov.direction("focus", 5)
    cos = float(np.dot(mean_diff, planted) / np.linalg.norm(mean_diff))
    assert cos > 0.9
    assert abs(np.linalg.norm(mean_diff) - 6.0) < 1.5


def test_zero_magnitude_plant_has_no_recoverable_direction():
    # A zero-signal plant must NOT create a systematic pos/neg difference: the
    # residual is just the noise floor, far below a real planted magnitude.
    prov = SyntheticActivationProvider(dim=128, layers=[5], seed=3, noise_scale=1.0)
    pos = [f"pos-{i}" for i in range(200)]
    neg = [f"neg-{i}" for i in range(200)]
    prov.plant_contrast("focus", pos, neg, magnitude=0.0, layer_gain={5: 1.0})
    p = prov.get_activations(pos, 5)
    n = prov.get_activations(neg, 5)
    mean_diff = p.mean(axis=0) - n.mean(axis=0)
    # Noise floor ~ sqrt(2*dim/n) ~ 1.13; far below the magnitude-6 signal above.
    assert np.linalg.norm(mean_diff) < 2.0


def test_hf_provider_lazy_no_torch_at_import_and_offline_construction():
    # The real HF provider imports torch/transformers LAZILY (inside methods),
    # so merely importing the package + constructing the provider must not pull
    # torch into sys.modules and must not touch the network / load a model.
    prov = HFActivationProvider(
        "Qwen/Qwen2.5-0.5B-Instruct", layers=[0, 6, 12], device="cpu", dtype="float32"
    )
    assert isinstance(prov, ActivationProvider)
    # Explicit layer set is honoured WITHOUT loading a model (cheap, torch-free).
    assert prov.available_layers() == [0, 6, 12]
    # Constructing the package must NOT have imported torch.
    assert "torch" not in sys.modules


def test_hf_provider_raises_helpful_error_without_torch():
    # If torch is not installed, activation capture must fail with a clear,
    # actionable NotImplementedError (install hint) rather than a bare ImportError.
    if any(m in sys.modules for m in ("torch", "transformers")):
        pytest.skip("torch/transformers installed in this env; hint-path not exercised")
    try:
        import torch  # noqa: F401

        pytest.skip("torch importable; the missing-extra path is not reachable here")
    except ImportError:
        pass
    prov = HFActivationProvider("Qwen/Qwen2.5-0.5B-Instruct")
    with pytest.raises(NotImplementedError):
        prov.get_activations(["hi"], layer=6)


def test_hf_cache_key_includes_device_and_dtype():
    # A cpu/fp32 forward is numerically different from a cuda/fp16 forward, so the
    # on-disk activation cache MUST NOT be shared across (device, dtype): otherwise
    # a warm cpu-fp32 cache would be silently reused for a gpu-fp16 run and corrupt
    # the GPU results. Construction is torch-free (no model load).
    cpu = HFActivationProvider(
        "Qwen/Qwen2.5-0.5B-Instruct", layers=[6], device="cpu", dtype="float32"
    )
    gpu = HFActivationProvider(
        "Qwen/Qwen2.5-0.5B-Instruct", layers=[6], device="cuda", dtype="float16"
    )
    text, layer = "hello world", 6
    assert cpu._cache_key(text, layer) != gpu._cache_key(text, layer)
    assert cpu._cache_path(text, layer) != gpu._cache_path(text, layer)
    # Same (device, dtype) is deterministic / reused.
    cpu2 = HFActivationProvider(
        "Qwen/Qwen2.5-0.5B-Instruct", layers=[6], device="cpu", dtype="float32"
    )
    assert cpu._cache_key(text, layer) == cpu2._cache_key(text, layer)
    # dtype alone flips the key even on the same device.
    gpu_fp32 = HFActivationProvider(
        "Qwen/Qwen2.5-0.5B-Instruct", layers=[6], device="cuda", dtype="float32"
    )
    assert gpu._cache_key(text, layer) != gpu_fp32._cache_key(text, layer)
