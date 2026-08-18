# Self-check gate: C2b Composition Shard A — CAA × Qwen

- experiment_id: `composition-a-qwen-caa-20260818-0001`
- status: `done`; valid_for_paper: `False` (awaiting independent audit)
- code_commit: `d342ef6438974af6c31019bc2d74ac9389b5ded5`; run_seed: `20260818`; direction_seed: `20260723`
- model: `Qwen/Qwen2.5-7B-Instruct`; HF snapshot revision: `a09a35458c702b33eeacc393d103063234e8bc28`
- wall_clock_seconds: `30206.684`; hardware: `cuda-float16`
- direction provenance: `DIRECTIONS_REDERIVED_WITH_PROVENANCE_CAVEAT`; no persisted E-0006 reference vector found, so no cosine comparison was available.
- per-item audit arrays: `per_item_test_pairs.jsonl` contains item_id, item_sha256, prompt/steer sample scores, per-item means, and paired diffs for all 6 TEST cells (2400 rows).
- raw TEST transcripts are not committed; remote pointer + sha256 are in `transcript_pointers_sha256.txt`.

## Recomputed TEST cells

| baseline | axis | N | alpha* | prompt mean | steer mean | mean Δ | 98.33% CI | MDE80 | coherence | parse prompt/steer | trunc max | verdict |
|---|---:|---:|---:|---:|---:|---:|---|---:|---|---|---:|---|
| ordinary | deliberation | 400 | 2.0 | 0.894500 | 0.899000 | +0.004500 | [-0.008500, +0.017500] | 0.017805 | ok | 1.000/1.000 | 0.000 | NO_INCREMENT_DEMONSTRATED |
| strong | deliberation | 400 | 6.0 | 0.901500 | 0.891000 | -0.010500 | [-0.026337, +0.005000] | 0.020992 | ok | 1.000/1.000 | 0.000 | NO_INCREMENT_DEMONSTRATED |
| ordinary | skepticism | 400 | 8.0 | 0.688000 | 0.693500 | +0.005500 | [-0.009000, +0.021000] | 0.020149 | ok | 1.000/1.000 | 0.000 | NO_INCREMENT_DEMONSTRATED |
| strong | skepticism | 400 | 2.0 | 0.695000 | 0.694500 | -0.000500 | [-0.017500, +0.016500] | 0.023082 | ok | 1.000/1.000 | 0.000 | NO_INCREMENT_DEMONSTRATED |
| ordinary | uncertainty_awareness | 400 | 6.0 | 0.673054 | 0.667551 | -0.005503 | [-0.019934, +0.008229] | 0.019448 | ok | 0.995/0.998 | 0.000 | NO_INCREMENT_DEMONSTRATED |
| strong | uncertainty_awareness | 400 | 2.0 | 0.860152 | 0.863542 | +0.003389 | [-0.009981, +0.016036] | 0.017892 | ok | 0.990/0.995 | 0.000 | NO_INCREMENT_DEMONSTRATED |

## Gate checks

- Coherence gate: PASS (all six cells).
- Parse gate: PASS; uncertainty_awareness parse rates are reported above to rule out missingness/imputation artifacts.
- Truncation gate: PASS; deliberation used max_new_tokens=512, not the invalid 64-token floor.
- Power/MDE gate: PASS; all six realized MDE80 values are <= 0.06.
- Outcome interpretation: all six TEST CIs include zero and all frozen verdicts remain `NO_INCREMENT_DEMONSTRATED`; this is a well-powered null for the CAA×Qwen composition shard, not an equivalence proof and not a positive augmentation finding.

## Files/checksums

- `composition_results.json` sha256 `6f978e6027a1283551ca6a2f83b4890fb9633bdb4232d2faf55725672a6c7711`
- `composition_summary.md` sha256 `229520ab3033aae24814d2cf09fdcee3e645ccf464fe4a7e0e18f3ab333d6338`
- `direction_provenance.json` sha256 `0e0da08edea53fdf437548f47df57a6ce5b17352a1145ee370eb72ae0d0dd964`
- `alpha_manifest.yaml` sha256 `41ccf08d4572505205ef5d1cfcc73acd138f6ba59a673da6b719fe121e44e8f7`
- `per_item_test_pairs.jsonl` sha256 `109eb9240b6b7b808e5a4dc0517e1c54f214ab03b43fb2438e14cfafc729585a`
- `model_provenance.json` sha256 `88c567e89d455079507e53376818f582a33290cc0e6af682efb567d1fef33ebf`
- `transcript_pointers_sha256.txt` sha256 `16c1c84a9d209c1e085e55b09a9e7dbfa22aaea5457e07286eae5ec50278497d`

No self-check mismatches detected.
