# FROZEN PRE-REGISTRATION — ITI Deliberation Remeasurement at 512 New Tokens

- **Status:** **FROZEN 2026-08-20, before DEV or TEST. UNRUN.**
- **Protocol ID:** `iti-deliberation-remeasure-512-20260820`
- **DEV experiment ID:** `iti-delib-512-dev-20260820`
- **TEST experiment ID:** `iti-delib-512-test-20260820`
- **Mirrors:** CAA protocol `E-DELIB512-REMEASURE` / `docs/specs/deliberation-remeasure-512-prereg.md` from `feature/delib512-lineage@c1ef7e7`, artifacts `results/delib_512_20260815/`.
- **Scientific role:** additive two-cell completion of Table 2 (`tab:c2-delta-4cell`) so both CAA and ITI deliberation cells have the same 512-token floor-effect repair.
- **Paper status:** `valid_for_paper=false` until raw bundles are committed, hostile result audit passes, and Manager fold gate explicitly approves use. This protocol does not alter frozen `E-0005`/`E-0006`/`E-0011` or the 0/12 grid.

## 1. Rationale and anti-fishing scope

The CAA deliberation cells were remeasured at `max_new_tokens=512` because the original `max_new_tokens=64` cap put GSM8K deliberation near a parser/truncation floor. The ITI deliberation cells were not remeasured, creating an asymmetric artifact risk. This protocol mirrors the CAA 512-token protocol and changes only the steering method from CAA to ITI, including ITI sigma-scaled interventions.

The 512-token limit, cells, split, metrics, prompts, bootstrap, adjudicator, and verdict rule are fixed a priori. No other token budget, model, method, layer, prompt family, item count, or scorer may be added under this protocol.

## 2. Fixed cells

| Cell | Method | Model/checkpoint identity | Axis | Frozen ITI layer | Layer source | Change from powered-tost-A |
|---|---|---|---|---:|---|---|
| I1 | ITI | `Qwen/Qwen2.5-7B-Instruct` (`a09a35458c702b33eeacc393d103063234e8bc28`) | deliberation | 20 | `results/arm_full/cell_iti__qwen2.5-7b/c2b_adjudication_results.json` (`axes[].axis=deliberation`, `layer=20`) | `max_new_tokens: 64 -> 512`; DEV reselects alpha at 512 |
| I2 | ITI | `NousResearch/Meta-Llama-3-8B-Instruct` | deliberation | 8 | `results/arm_full/cell_iti__llama3-8b/c2b_adjudication_results.json` (`axes[].axis=deliberation`, `layer=8`) | `max_new_tokens: 64 -> 512`; DEV reselects alpha at 512 |

ITI direction extraction is the frozen logistic-probe method at the fixed layer. Intervention strength is `effective_alpha = alpha * sigma`, where `sigma` is measured from the extraction activations along the ITI probe direction and recorded in the DEV/TEST seals.

## 3. Parameters inherited unchanged from E-DELIB512-REMEASURE

Except for `method=iti` and the fixed ITI layer sources above, all parameters mirror the CAA 512 protocol:

- GSM8K test pool after excluding frozen first 60 IDs (`gsm8k-test-00000` through `gsm8k-test-00059`);
- deterministic selected total `225`, DEV `75`, TEST `150`, selection seed `20260812`, and the existing `split_dev_test` rule;
- `k=5`, temperature `0.7`, sampled generation, same neutral prompt and bounded best-of-16 authored prompt family;
- DEV-only best prompt selection and DEV-only alpha selection on `{2,4,6,8,12,16,24}`;
- paired item-cluster bootstrap `B=10000`, seed `20260812`;
- superiority CI `98.33%` Bonferroni, equivalence/TOST CI `90%`, SESOI/δ `±0.05`;
- unchanged coherence gate and item-level ITT with no post-hoc item deletion;
- raw-bundle retention, manifest, code/data/config lineage, and TEST-once marker requirements.

DEV selects the alpha with the largest DEV `steer - prompt` contrast among coherence-passing alpha values. Because the selected prompt outcome is fixed before alpha evaluation, this is equivalent to maximizing DEV steered GSM8K accuracy under the inherited implementation.

## 4. Primary estimand and hypotheses

For each TEST item `i`, with fixed `k=5` sampled generations per channel:

`d_i = GSM8K_exact_match_i(steer) - GSM8K_exact_match_i(prompt)`.

The primary estimand is the paired mean `Δ = mean_i(d_i)` for each fixed cell: the same steer-vs-best-prompt substitution estimand as the headline C2b table.

Report both:

- **H_sup:** PASS only if the 98.33% Bonferroni item-cluster bootstrap CI excludes 0, `Δ >= δ=0.05`, and the coherence gate passes.
- **H_equiv:** EQUIVALENT only if the 90% TOST item-cluster bootstrap CI lies wholly inside `[-0.05, +0.05]`.

Ordinary nonsignificance is not equivalence.

## 5. Strict verdict rule

Each cell is reported exactly once:

1. **PASS:** H_sup holds.
2. **NEGATIVE-CONTRAST:** the paired steer-minus-prompt superiority CI is wholly below zero (`CI_hi < 0`).
3. **EQUIVALENT:** the 90% TOST CI is wholly inside `[-0.05, +0.05]`.
4. **UNDERPOWERED:** none of the above holds.

Coherence failure is a failed-cell diagnostic and cannot rescue or hide a favorable interpretation.

## 6. Staging, gates, and anti-artifact checks

1. Commit this frozen UNRUN protocol and runner before DEV/TEST.
2. Run `nvidia-smi` and use only a genuinely idle A800 GPU.
3. Run DEV and seal prompt/alpha/sigma/direction.
4. Run TEST exactly once per cell using the sealed DEV selection.
5. Commit raw bundles, per-item TEST arrays, transcripts, hashes, and registry rows with `valid_for_paper=false`.

Mandatory reporting per cell: realized `N`, 98.33% CI, TOST90 CI, achieved MDE, coherence gate, `steer_accuracy`, `prompt_accuracy`, `unsteered_accuracy`, truncation count, strict verdict, and sign/power interpretation. If the result is small negative/null/underpowered, report it as such.

The 512-token remeasure must demonstrate that deliberation is no longer at the old ~0–3% 64-token floor by reporting steer/prompt/unsteered accuracy and token/truncation diagnostics.

## 7. Mandatory raw-bundle retention

Retain and commit:

- per-item generations/transcripts for prompt, steer, and baseline channels;
- per-item and per-sample outcomes;
- parse, truncation, degeneracy/coherence, and missingness diagnostics;
- DEV prompt scores, selected prompt, alpha grid rows, selected alpha, ITI sigma, direction path/hash, layer, item IDs, and sealed DEV hash;
- config, command line, seeds, data hashes/revisions, model identity, code commit, dirty-tree state, hardware profile, and environment metadata;
- experiment-registry row with `valid_for_paper: false`.

Manual transcription of scientific numbers is prohibited. Final reporting must use script artifacts.
