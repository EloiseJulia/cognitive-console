"""Steering-vector extraction (CAA / RepE) — pure numpy over provider activations."""

from .extract import (
    CAAResult,
    LayerDiagnostics,
    extract_caa,
    layer_diagnostics,
    mean_difference_vector,
)

__all__ = [
    "CAAResult",
    "LayerDiagnostics",
    "extract_caa",
    "layer_diagnostics",
    "mean_difference_vector",
]
