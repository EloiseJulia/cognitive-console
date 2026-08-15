# FROZEN PRE-REGISTRATION — Deliberation Remeasurement at 512 New Tokens

- **Status:** **FROZEN 2026-08-15, before DEV or TEST. UNRUN.**
- **Protocol ID:** `deliberation-remeasure-512-20260815`
- **DEV experiment ID:** `delib-512-dev-20260815`
- **TEST experiment ID:** `delib-512-test-20260815`
- **Scientific role:** owner-approved protocol revision for the GSM8K deliberation-only powered-TOST cells whose original `max_new_tokens=64` generation cap caused a floor-effect artifact by truncating multi-step reasoning before final answers.
- **Paper status:** `valid_for_paper=false` until raw bundles are committed, hostile result audit passes, and Manager/human fold gate explicitly approves use. This protocol does not restore or modify any withdrawn manuscript claim by itself.

## 1. Owner-approved rationale and anti-fishing scope

Owner approval was granted on **2026-08-15** to remeasure deliberation with `max_new_tokens=512` because the frozen 64-new-token cap was too short for GSM8K chain-of-thought answers: generations were often cut before the final answer, all channels scored near the floor (~0–3%), and the parser could capture only intermediate numbers. The prior Experiment A deliberation "equivalence" is therefore treated as a floor-effect artifact and was rolled back from the manuscript.

The 512-token limit is fixed **a priori** from GSM8K task requirements. It is not a sweep, tuning axis, or search for a passing threshold. No other token limit may be tried under this protocol. Results must be reported whether they support superiority, equivalence, negative contrast, or underpowered/inconclusive outcomes.

## 2. Fixed cells

Only the two CAA deliberation cells corresponding to Experiment A A1/A2 are in scope:

| Cell | Method | Model/checkpoint identity | Axis | Frozen CAA layer | Layer source | Change from powered-tost-A |
|---|---|---|---|---:|---|---|
| D1 | CAA | `Qwen/Qwen2.5-7B-Instruct` (`a09a35458c702b33eeacc393d103063234e8bc28`) | deliberation | 20 | `results/arm_full/cell_caa__qwen2.5-7b/c2b_adjudication_results.json` (`axes[].axis=deliberation`, `layer=20`) | `max_new_tokens: 64 -> 512` only |
| D2 | CAA | Llama-3-8B-Instruct; same frozen C2 checkpoint family (`/root/autodl-tmp/models/Meta-Llama-3-8B-Instruct` / accepted `NousResearch/Meta-Llama-3-8B-Instruct` mirror) | deliberation | 12 | `results/arm_full/cell_caa__llama3-8b/c2b_adjudication_results.json` (`axes[].axis=deliberation`, `layer=12`) | `max_new_tokens: 64 -> 512` only |

No skepticism, uncertainty-awareness, C1 READ piggyback, new model, new method, new layer, new scorer, new item count, headroom filter, or prompt family is authorized.

## 3. Parameters inherited unchanged from powered-tost-A

Except for `max_new_tokens=512` and restricting the fixed cell set to D1/D2, all parameters inherit `docs/specs/powered-tost-A-prereg.md`:

- GSM8K test pool after excluding the frozen first 60 IDs (`gsm8k-test-00000` through `gsm8k-test-00059`);
- deterministic selected total `225`, DEV `75`, TEST `150`, selection seed `20260812`, and the existing `split_dev_test` rule;
- `k=5`, temperature `0.7`, sampled generation, same neutral prompt and bounded best-of-16 authored prompt family;
- DEV-only prompt selection and DEV-only alpha selection on `{2,4,6,8,12,16,24}`;
- CAA direction extraction convention, `N_EXTRACTION=28`, single-layer additive intervention, and layers fixed above;
- paired item-cluster bootstrap `B=10000`, seed `20260812`;
- superiority CI `98.33%` Bonferroni, equivalence/TOST CI `90%`, SESOI/δ `±0.05`;
- unchanged coherence gate and item-level ITT with no post-hoc item deletion;
- raw-bundle retention, manifest, code/data/config lineage, and TEST-once marker requirements.

DEV must select the alpha with the largest DEV `steer - prompt` contrast among coherence-passing alpha values. Because the selected prompt outcome is fixed before alpha evaluation, this is equivalent to maximizing DEV steered GSM8K accuracy under the inherited implementation.

## 4. Primary estimand and hypotheses

For each TEST item `i`, with fixed `k=5` sampled generations per channel:

`d_i = GSM8K_exact_match_i(steer) - GSM8K_exact_match_i(prompt)`.

The primary estimand is the paired mean `Δ = mean_i(d_i)` for each fixed cell.

Two hypotheses are reported per cell:

- **H_sup:** original powered-TOST pass rule. A cell is `PASS` only if the 98.33% Bonferroni item-cluster bootstrap CI excludes 0, the mean `Δ >= δ=0.05`, and the coherence gate passes.
- **H_equiv:** strict TOST equivalence with SESOI `±0.05`. A cell is `EQUIVALENT` only if the 90% TOST item-cluster bootstrap CI lies entirely inside `[-0.05, +0.05]`.

Ordinary nonsignificance is not equivalence. If a CI includes nontrivial effects outside `±0.05`, the honest verdict is `UNDERPOWERED` unless the negative-contrast rule applies.

## 5. Strict verdict rule

Each fixed cell is reported exactly once using this priority order:

1. **PASS:** H_sup holds.
2. **NEGATIVE-CONTRAST:** the paired steer-minus-prompt superiority CI is wholly below zero (`CI_hi < 0`).
3. **EQUIVALENT:** the 90% TOST CI is wholly inside `[-0.05, +0.05]`.
4. **UNDERPOWERED:** none of the above holds.

Coherence failure is reported as a failed-cell diagnostic and cannot rescue or hide a favorable interpretation. Parse failures, truncation, degeneracy, and missingness remain item-level ITT records.

## 6. Staging, gates, and no-peeking

The sequence is:

1. commit this frozen UNRUN protocol and code configuration before DEV;
2. run DEV only, on GPU3 only after verifying it is idle;
3. seal DEV selections and commit the raw DEV bundle;
4. stop for Manager confirmation;
5. run TEST exactly once only after explicit "阶段2 GO".

This Stage 1 protocol authorizes **no TEST generation**. TEST must not be started, peeked at, copied, summarized, or partially run in this stage. If DEV GSM8K accuracy remains near the old floor (~0–3%) rather than returning to a plausible Qwen/Llama range (~70–85%), the run hard-stops before TEST and reports that 512 did not repair truncation or another implementation/scoring bug remains.

## 7. Mandatory raw-bundle retention

DEV and later TEST raw bundles must be retained and committed to this branch, including:

- per-item generations/transcripts for prompt, steer, and baseline channels;
- per-item and per-sample outcomes;
- parse, truncation, degeneracy/coherence, and missingness diagnostics;
- DEV prompt scores, selected prompt, alpha grid rows, selected alpha, direction path/hash, layer, item IDs, and sealed DEV hash;
- config, command line, seeds, data hashes/revisions, model identity, code commit, dirty-tree state, hardware profile, and environment metadata;
- an experiment-registry row with `valid_for_paper: false`.

Manual transcription of scientific numbers is prohibited. Final reporting must use script artifacts.
