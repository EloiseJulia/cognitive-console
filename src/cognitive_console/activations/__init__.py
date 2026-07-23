"""Activation-provider seam (the key abstraction that defers GPU work).

The rest of the Phase 0 analysis pipeline (CAA extraction, facade analysis,
conflict probe) consumes activations *only* through the `ActivationProvider`
interface. Two implementations exist:

* `SyntheticActivationProvider` — deterministic, seeded, OFFLINE. It can plant a
  known "axis signal" so unit tests can verify the pipeline RECOVERS a facade
  gap that was injected on purpose (guards against tautological pipelines).
* `HFActivationProvider` — the real (Llama-3-8B / Qwen2.5-7B) implementation is a
  STUB that raises `NotImplementedError`. All torch/transformers imports are
  lazy (inside the method) so importing this package never requires torch.
"""

from .provider import (
    ActivationProvider,
    SyntheticActivationProvider,
    HFActivationProvider,
)

__all__ = [
    "ActivationProvider",
    "SyntheticActivationProvider",
    "HFActivationProvider",
]
