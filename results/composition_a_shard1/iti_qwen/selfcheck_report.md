# Self-check gate: C2b Composition Shard A — ITI × Qwen

- experiment_id: `composition-a-qwen-iti-20260818-0001`
- status: `done`; valid_for_paper: `False` (awaiting independent audit)
- code_commit: `f6a15f69b08b5a0e9ecfedc3fa0514e4eaa1c69a`; run_seed: `20260818`; direction_seed: `20260723`; bootstrap_seed: `20260819`
- model: `Qwen/Qwen2.5-7B-Instruct`; HF snapshot revision: `a09a35458c702b33eeacc393d103063234e8bc28`
- wall_clock_seconds: `37654.356`; hardware: `cuda-float16`
- direction provenance: `DIRECTIONS_REDERIVED_WITH_PROVENANCE_CAVEAT`; no persisted headline ITI reference vector was found, so no cosine comparison was available.
- per-item audit arrays: `per_item_test_pairs.jsonl` contains item_id, item_sha256, prompt/steer sample scores, per-item means, paired diffs, and uncertainty parse-missingness flags.
- raw TEST transcripts are not committed; remote pointer + sha256 are in `transcript_pointers_sha256.txt`.

## Recomputed TEST cells

| baseline | axis | N | alpha* | prompt mean | steer mean | mean Δ | 98.33% CI | MDE80 | coherence | parse prompt/steer | trunc max | verdict |
|---|---|---:|---:|---:|---:|---:|---|---:|---|---|---:|---|
| ordinary | deliberation | 400 | 2.0 | 0.894500 | 0.885500 | -0.009000 | [-0.028000, +0.010000] | 0.025981 | ok | 1.000/1.000 | 0.000 | NO_INCREMENT_DEMONSTRATED |
| strong | deliberation | 400 | 2.0 | 0.901500 | 0.876000 | -0.025500 | [-0.045500, -0.006662] | 0.026047 | ok | 1.000/1.000 | 0.000 | NO_INCREMENT_DEMONSTRATED |
| ordinary | skepticism | 400 | 2.0 | 0.688000 | 0.670500 | -0.017500 | [-0.042500, +0.007000] | 0.034440 | ok | 1.000/1.000 | 0.000 | NO_INCREMENT_DEMONSTRATED |
| strong | skepticism | 400 | 2.0 | 0.695000 | 0.670000 | -0.025000 | [-0.053500, +0.003500] | 0.038601 | ok | 1.000/1.000 | 0.000 | NO_INCREMENT_DEMONSTRATED |
| ordinary | uncertainty_awareness | 400 | 8.0 | 0.673054 | 0.628961 | -0.044093 | [-0.080767, -0.009073] | 0.049178 | ok | 0.995/0.963 | 0.000 | UNDERPOWERED_OR_INVALID |
| strong | uncertainty_awareness | 400 | 2.0 | 0.860152 | 0.847854 | -0.012299 | [-0.028107, +0.003846] | 0.021904 | ok | 0.990/0.983 | 0.000 | NO_INCREMENT_DEMONSTRATED |

## Gate checks

- Bootstrap seed: PASS (`bootstrap_seed=20260819`).
- Coherence gate: PASS (all six cells).
- Parse gate: FAIL; ordinary uncertainty fails the frozen parse gate and is therefore invalid/underpowered, not a null.
- Truncation gate: PASS; deliberation used max_new_tokens=512, not the invalid 64-token floor.
- MDE screen: PASS; all six realized MDE80 values are <= 0.06, but validity still requires parse/coherence/truncation gates.
- Outcome interpretation: ordinary baseline shard verdict is `UNDERPOWERED_OR_INVALID` because uncertainty parse gate failed; strong baseline shard verdict is `NO_INCREMENT_DEMONSTRATED`. This is not an equivalence proof and not a positive augmentation finding.

## Uncertainty missingness sensitivity

| baseline | parse prompt/steer | missing items | complete-case N | complete-case mean Δ | complete-case 98.33% CI | lower-bound mean Δ | lower-bound CI | upper-bound mean Δ | upper-bound CI | upper-bound gain pass? |
|---|---:|---:|---:|---:|---|---:|---|---:|---|---|
| ordinary | 0.995/0.963 | 47 | 353 | -0.044726 | [-0.083687, -0.006673] | -0.073093 | [-0.110798, -0.035603] | -0.031093 | [-0.068345, +0.003765] | false |
| strong | 0.990/0.983 | 25 | 375 | -0.013071 | [-0.029780, +0.003816] | -0.027924 | [-0.046534, -0.009362] | -0.000424 | [-0.017973, +0.018070] | false |

These analyses are diagnostic safeguards against confidence-parse missingness and do not replace the preregistered primary verdict.

## Files/checksums

- `alpha_manifest.yaml` sha256 `481ca52f0cedda4e4cd28dddf953ca84ebd0c7d6ed9255b9863fbd5890cb450a`
- `composition_results.json` sha256 `174ec1ddba8f10130167d8a220dfc4cda88cf60ce61a6e2abcb79923b5cdf37e`
- `composition_summary.md` sha256 `8e8caa865325247f7220ad6cb66a684a36315c4009737826d6e31983c056dc77`
- `direction_provenance.json` sha256 `766ecc9f16b363bd789160449f25c06736222071e95cf7ff4c9879b275e65993`
- `missingness_sensitivity.json` sha256 `3755193c639f9aeb85f087fcbd6c92653dcca6ba332728743a46d60339ad2078`
- `missingness_sensitivity.md` sha256 `ab7fd1acddc99b4142ab2d99ca2f2687f3fc0cdbb746bc0fe4ef00c05dde200d`
- `model_provenance.json` sha256 `dc0200323c7b4b06a465646fb1cf43064a181d1fb440c6fe9fd12ca690037498`
- `per_item_test_pairs.jsonl` sha256 `b0ec248f2f5016a7981b31c5c924711630584bddf33dd700a71cd43a1d2ec208`
- `run.log` sha256 `be283a474b365a42241336ef9c951eb0463a512e972bb3db694693388966a90f`
- `transcript_pointers_sha256.txt` sha256 `8c22317cee59a48065c34fedcc8109d9dfbc347d40f249f3afa33046e8f923d6`

No recomputation mismatches detected beyond floating-point equality against the runner output.
