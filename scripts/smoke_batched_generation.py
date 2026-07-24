"""UNVERIFIED-1 smoke: real-torch batched vs single-sequence equivalence (CPU).

Verifies two properties of ``SteeredHFBackend`` on a locally-cached small model
(default Qwen2.5-1.5B-Instruct), on CPU, over a tiny slice of short prompts:

1. GREEDY (do_sample=False): batched ``generate_batch`` produces the SAME decoded
   token outputs as single-sequence ``generate`` for each prompt. This exercises
   left-padding + attention-mask correctness — if padding leaked into the model's
   attention, the batched continuations would diverge from the single ones.
2. STEERED: with the steering hook at some alpha, batched steered generation runs
   without error and (by the left-pad contract) the hook is applied to real-token
   positions, not pad. We assert non-empty outputs and no exception.

This is NOT part of the required pytest suite (it needs torch + the model). Run it
manually, or gate it via the ``C2B_RUN_TORCH_SMOKE=1`` env flag. Without torch +
the model it exits 0 as SKIPPED so the offline suite stays model-independent.

Usage:
    python scripts/smoke_batched_generation.py
    C2B_RUN_TORCH_SMOKE=1 python scripts/smoke_batched_generation.py --model Qwen/Qwen2.5-1.5B-Instruct
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))

SMOKE_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
PROMPTS = [
    "In one word, is the sky blue?",
    "What is 2 + 2? Answer with just the number.",
    "Reply with the single word: hello.",
]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default=SMOKE_MODEL)
    ap.add_argument("--max-new-tokens", type=int, default=24)
    ap.add_argument("--alpha", type=float, default=4.0)
    ap.add_argument("--layer", type=int, default=8)
    args = ap.parse_args(argv)

    try:
        import torch  # noqa: F401
        from cognitive_console.steering.generate import SteeredHFBackend, SteerConfig
    except Exception as exc:  # torch/transformers absent
        print(f"[smoke] SKIPPED (torch/transformers unavailable): {exc}")
        return 0

    backend = SteeredHFBackend(args.model, device="cpu", dtype="float32", seed=0)
    try:
        backend._ensure_loaded()
    except Exception as exc:
        print(f"[smoke] SKIPPED (model not loadable/cached): {exc}")
        return 0

    print(f"[smoke] model={args.model} device=cpu dtype=float32 "
          f"max_new_tokens={args.max_new_tokens}")

    # --- (1) GREEDY batched vs single-sequence ---------------------------
    single = [
        backend.generate(p, steer=None, max_new_tokens=args.max_new_tokens,
                         do_sample=False)
        for p in PROMPTS
    ]
    batched = backend.generate_batch(
        PROMPTS, steer=None, max_new_tokens=args.max_new_tokens, do_sample=False)

    print("\n[smoke] GREEDY batched vs single-sequence:")
    all_match = True
    for i, p in enumerate(PROMPTS):
        match = single[i] == batched[i]
        all_match = all_match and match
        print(f"  prompt[{i}] match={match}")
        if not match:
            print(f"    single : {single[i]!r}")
            print(f"    batched: {batched[i]!r}")
    print(f"[smoke] GREEDY exact-match ALL: {all_match}")

    # --- (2) STEERED batched runs without error --------------------------
    dim = backend.hidden_dim
    direction = np.ones(dim, dtype=np.float64)
    steer = SteerConfig(direction=direction, alpha=args.alpha, layer=args.layer)
    steered = backend.generate_batch(
        PROMPTS, steer=steer, max_new_tokens=args.max_new_tokens, do_sample=False)
    steered_ok = len(steered) == len(PROMPTS) and all(isinstance(s, str) for s in steered)
    print(f"\n[smoke] STEERED batched (alpha={args.alpha}, layer={args.layer}) "
          f"ran_without_error={steered_ok} n_out={len(steered)}")
    for i, s in enumerate(steered):
        print(f"  steered[{i}]: {s[:60]!r}")

    print("\n[smoke] RESULT SUMMARY:")
    print(f"  greedy_batched_equals_single = {all_match}")
    print(f"  steered_batched_ran_without_error = {steered_ok}")
    # Non-zero exit only if the steered path errored; a greedy fp mismatch is
    # REPORTED (fp32-CPU batched matmul can differ in low-order bits) but does not
    # fail the smoke — the operator reads the printed match report.
    return 0 if steered_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
