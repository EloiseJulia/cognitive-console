"""cognitive_console — Phase 0 prep package (data-level, CPU-only).

No torch / transformers / vLLM at import time. Metrics are numpy-only. This
package holds:

* `registry` — the immutable experiment-registry writer (§8.1).
* `metrics` — semantic-facade metric primitives (C1).
* `config` / `manifest` / `lineage` — config hashing, artifact-lineage manifests
  (§8.3), and run registration helpers.
* `activations` — the ActivationProvider seam: a synthetic offline provider and
  an HF stub (real forward pass deferred to the GPU phase).
* `steering.extract` — CAA mean-difference extraction + layer scan.
* `analysis.facade` / `analysis.routing` — C1 facade analysis and the Go/No-Go
  routing decision (S11).
* `experiments.conflict_probe` — the C2b conflict-probe harness (BehaviorBackend
  seam + landing computation).

The real model forward pass (Llama-3-8B / Qwen2.5-7B) is abstracted behind the
provider/backend seams and STUBBED until GPU is approved; the whole pipeline runs
and is unit-tested offline.
"""

__version__ = "0.0.1"
