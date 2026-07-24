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
from .iti import (
    ITIResult,
    ITILayerDiagnostics,
    extract_iti,
    sigma_scaled_alpha,
)

from .generate import (
    GenBackend,
    SteerConfig,
    SteeredHFBackend,
    SyntheticSteeredBackend,
    unit_vector,
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
    "ITIResult",
    "ITILayerDiagnostics",
    "extract_iti",
    "sigma_scaled_alpha",
    "GenBackend",
    "SteerConfig",
    "SteeredHFBackend",
    "SyntheticSteeredBackend",
    "unit_vector",
]
