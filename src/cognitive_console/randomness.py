"""Frozen random-number primitives used by confirmatory experiment code."""

from __future__ import annotations

import numpy as np

NUMPY_RNG_ALGORITHM = "numpy.random.Generator(numpy.random.PCG64)"


def pcg64_rng(seed: int) -> np.random.Generator:
    """Return the explicitly frozen NumPy bit-generator."""

    return np.random.Generator(np.random.PCG64(int(seed)))
