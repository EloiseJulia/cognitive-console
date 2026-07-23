"""Steering-vector extraction (CAA / RepE) — pure numpy over provider activations."""

from .extract import (
    CAAResult,
    LayerCandidate,
    LayerDiagnostics,
    LayerSelection,
    extract_caa,
    layer_diagnostics,
    mean_difference_vector,
    min_layer_for_depth,
    select_nondegenerate_layer,
)

__all__ = [
    "CAAResult",
    "LayerCandidate",
    "LayerDiagnostics",
    "LayerSelection",
    "extract_caa",
    "layer_diagnostics",
    "mean_difference_vector",
    "min_layer_for_depth",
    "select_nondegenerate_layer",
]
