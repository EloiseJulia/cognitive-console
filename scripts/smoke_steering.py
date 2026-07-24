"""CPU/1.5B steering smoke test — EVIDENCE that alpha>0 shifts generation.

Not part of the offline pytest suite (it loads a real model). Run manually:

    python scripts/smoke_steering.py --axis deliberation --alphas 0 6 12 20

It extracts the CAA direction for one axis at a mid layer on Qwen2.5-1.5B (CPU),
generates a short response to a neutral prompt at each alpha, and prints the
behavioral proxy score so you can SEE steering move the behavior vs alpha=0. Also
verifies alpha=0 (hooked, adds zero) == plain generation.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cognitive_console.activations.provider import HFActivationProvider
from cognitive_console.steering.extract import mean_difference_vector
from cognitive_console.steering.generate import SteeredHFBackend, SteerConfig, unit_vector
from cognitive_console.experiments.behavior import behavior_score
from scripts import run_c1_facade as c1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="CPU/1.5B steering smoke test")
    ap.add_argument("--model", default="Qwen/Qwen2.5-1.5B-Instruct")
    ap.add_argument("--axis", default="deliberation")
    ap.add_argument("--layer", type=int, default=None, help="hidden_states layer (default: mid)")
    ap.add_argument("--alphas", type=float, nargs="*", default=[0.0, 6.0, 12.0, 20.0])
    ap.add_argument("--prompt", default="Is 17 a prime number?")
    ap.add_argument("--max-new-tokens", type=int, default=64)
    ap.add_argument("--n-extraction", type=int, default=28)
    ap.add_argument("--seed", type=int, default=20260723)
    args = ap.parse_args(argv)

    cache = _REPO / "results" / "smoke_cache"
    provider = HFActivationProvider(args.model, device="cpu", dtype="float32", cache_dir=str(cache))
    top = provider.available_layers()[-1]
    layer = args.layer if args.layer is not None else max(1, top // 2)

    pairs = c1.load_axis_pairs(args.axis)
    split = c1.make_split(list(pairs.pos.keys()), n_extraction=args.n_extraction, seed=args.seed)
    ext_pos = [pairs.pos[p] for p in split.extraction_ids]
    ext_neg = [pairs.neg[p] for p in split.extraction_ids]
    pos_acts = provider.get_activations(ext_pos, layer).astype(np.float64)
    neg_acts = provider.get_activations(ext_neg, layer).astype(np.float64)
    direction = unit_vector(mean_difference_vector(pos_acts, neg_acts))
    print(f"[smoke] model={args.model} axis={args.axis} layer={layer}/{top} "
          f"hidden_dim={provider.hidden_dim}", flush=True)

    gen = SteeredHFBackend(args.model, device="cpu", dtype="float32")

    # alpha=0 (hooked, adds 0) must equal plain generation (control).
    plain = gen.generate(args.prompt, None, max_new_tokens=args.max_new_tokens)
    a0 = gen.generate(args.prompt, SteerConfig(direction, 0.0, layer), max_new_tokens=args.max_new_tokens)
    print(f"[smoke] alpha=0 == plain generation: {plain == a0}", flush=True)

    print(f"[smoke] prompt: {args.prompt!r}")
    base = None
    for a in args.alphas:
        out = gen.generate(args.prompt, SteerConfig(direction, a, layer),
                           max_new_tokens=args.max_new_tokens)
        score = behavior_score(out, args.axis)
        if base is None:
            base = score
        delta = score - base
        print(f"\n[smoke] alpha={a:>5} {args.axis}_proxy={score:.3f} (Δ vs α0 {delta:+.3f})")
        print("        " + out.replace("\n", " ")[:240])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
