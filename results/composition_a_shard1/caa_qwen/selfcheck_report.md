# Self-check gate: C2b Composition Shard A — CAA × Qwen

- experiment_id: `composition-a-qwen-caa-20260818-0001`
- status: `done`; valid_for_paper: `False` (awaiting fold-gate/audit closure)
- code_commit: `d342ef6438974af6c31019bc2d74ac9389b5ded5`; run_seed: `20260818`; direction_seed: `20260723`; bootstrap_seed: `20260819`
- model: `Qwen/Qwen2.5-7B-Instruct`; HF snapshot revision: `a09a35458c702b33eeacc393d103063234e8bc28`
- wall_clock_seconds: `30206.684`; hardware: `cuda-float16`
- direction provenance: `DIRECTIONS_REDERIVED_WITH_PROVENANCE_CAVEAT`; no persisted E-0006 reference vector found, so no cosine comparison was available.
- per-item audit arrays: `per_item_test_pairs.jsonl` contains item_id, item_sha256, prompt/steer sample scores, per-item means, paired diffs, and uncertainty parse-missingness flags.
- raw TEST transcripts are not committed; remote pointer + sha256 are in `transcript_pointers_sha256.txt`.

## Recomputed TEST cells (preregistered bootstrap seed)

| baseline | axis | N | alpha* | prompt mean | steer mean | mean Δ | 98.33% CI | MDE80 | coherence | parse prompt/steer | trunc max | verdict |
|---|---:|---:|---:|---:|---:|---:|---|---:|---|---|---:|---|
| ordinary | deliberation | 400 | 2.0 | 0.894500 | 0.899000 | +0.004500 | [-0.008500, +0.017500] | 0.017805 | ok | 1.000/1.000 | 0.000 | NO_INCREMENT_DEMONSTRATED |
| strong | deliberation | 400 | 6.0 | 0.901500 | 0.891000 | -0.010500 | [-0.025500, +0.005000] | 0.020992 | ok | 1.000/1.000 | 0.000 | NO_INCREMENT_DEMONSTRATED |
| ordinary | skepticism | 400 | 8.0 | 0.688000 | 0.693500 | +0.005500 | [-0.009000, +0.020500] | 0.020149 | ok | 1.000/1.000 | 0.000 | NO_INCREMENT_DEMONSTRATED |
| strong | skepticism | 400 | 2.0 | 0.695000 | 0.694500 | -0.000500 | [-0.017500, +0.016500] | 0.023082 | ok | 1.000/1.000 | 0.000 | NO_INCREMENT_DEMONSTRATED |
| ordinary | uncertainty_awareness | 400 | 6.0 | 0.673054 | 0.667551 | -0.005503 | [-0.020113, +0.008565] | 0.019448 | ok | 0.995/0.998 | 0.000 | NO_INCREMENT_DEMONSTRATED |
| strong | uncertainty_awareness | 400 | 2.0 | 0.860152 | 0.863542 | +0.003389 | [-0.009757, +0.016701] | 0.017892 | ok | 0.990/0.995 | 0.000 | NO_INCREMENT_DEMONSTRATED |

## Gate checks

- Bootstrap seed: PASS (`bootstrap_seed=20260819`, prereg §8).
- Coherence gate: PASS (all six cells).
- Parse gate: PASS; uncertainty parse rates and missingness sensitivity are reported separately.
- Truncation gate: PASS; deliberation used max_new_tokens=512, not the invalid 64-token floor.
- Power/MDE gate: PASS; all six realized MDE80 values are <= 0.06.
- Outcome interpretation: all six TEST CIs include zero and all frozen verdicts remain `NO_INCREMENT_DEMONSTRATED`; this is a well-powered null for the CAA×Qwen composition shard, not an equivalence proof and not a positive augmentation finding.

## Uncertainty missingness sensitivity

| baseline | parse prompt/steer | missing items | complete-case N | complete-case mean Δ | complete-case 98.33% CI | lower-bound mean Δ | lower-bound CI | upper-bound mean Δ | upper-bound CI | upper-bound gain pass? |
|---|---:|---:|---:|---:|---|---:|---|---:|---|---|
| ordinary | 0.995/0.998 | 8 | 392 | -0.002946 | [-0.017336, +0.011022] | -0.008253 | [-0.023903, +0.006351] | -0.001253 | [-0.015985, +0.012806] | false |
| strong | 0.990/0.995 | 15 | 385 | +0.004037 | [-0.009119, +0.017476] | -0.003236 | [-0.017596, +0.010864] | +0.012264 | [-0.003015, +0.028037] | false |

Sensitivity does not change the primary frozen verdict: both uncertainty cells remain NO_INCREMENT_DEMONSTRATED under the preregistered primary analysis. Adversarial bounds are diagnostic for the small parse-missingness rates and are not used to claim gain.

## Files/checksums

- `alpha_manifest.yaml` sha256 `41ccf08d4572505205ef5d1cfcc73acd138f6ba59a673da6b719fe121e44e8f7`
- `composition_results.json` sha256 `75b49a2a1451730dbf2597c469770361121a2c0a70a1abf4a63e155dcbbc62c6`
- `composition_summary.md` sha256 `9d3356ccddd428066002fa6fa625e26f5099932218bf70232cff973c0fd6bdfe`
- `direction_provenance.json` sha256 `0e0da08edea53fdf437548f47df57a6ce5b17352a1145ee370eb72ae0d0dd964`
- `missingness_sensitivity.json` sha256 `02a666b07498ad7461703512671dc7ecfba5e1ce434e9b4725b2cddda657a03a`
- `missingness_sensitivity.md` sha256 `708cf5ac08659ed113f710c4fa2715e5b3538df77e93f0443c2ba823ff40b794`
- `model_provenance.json` sha256 `88c567e89d455079507e53376818f582a33290cc0e6af682efb567d1fef33ebf`
- `per_item_test_pairs.jsonl` sha256 `63cff0a958632a80d7a26a55fd26d5e734482061ca0b9afcd758fb6e461b88a0`
- `run.log` sha256 `69aa6feab813ec6945653fa699215691008c96b3671426d25a3e0ffb9ca5f82b`
- `transcript_pointers_sha256.txt` sha256 `16c1c84a9d209c1e085e55b09a9e7dbfa22aaea5457e07286eae5ec50278497d`

No self-check mismatches detected.
