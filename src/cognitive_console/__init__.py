"""cognitive_console — Phase 0 prep package (data-level, CPU-only).

No torch / transformers / vLLM. Metrics are numpy-only. This package holds the
experiment-registry writer, the semantic-facade metric primitives (C1), and the
offline eval-set loader stub. GPU-phase code (vector extraction, facade runs) is
deferred and NOT part of this package yet.
"""

__version__ = "0.0.1"
