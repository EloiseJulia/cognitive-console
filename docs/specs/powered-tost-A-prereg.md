# FROZEN PRE-REGISTRATION — Experiment A: Powered TOST / Equivalence Refinement + Raw-Bundle Regeneration

- **Status:** **FROZEN 2026-08-13, before DEV or TEST. UNRUN.**
- **Protocol ID:** `powered-tost-A-20260813`
- **DEV experiment ID:** `powered-tost-A-dev-20260813`
- **TEST experiment ID:** `powered-tost-A-test-20260813`
- **Scientific role:** additive powered equivalence/superiority refinement for underpowered or lineage-gap C2 cells. This does **not** replace, reopen, overwrite, or relabel the frozen 0/12 grid, E-0005, E-0006, E-0011, or the earlier `c2b-resolution-refinement-20260812` run.
- **Run status:** no DEV, TEST, A800 generation, or paper fold is authorized by this document alone. `valid_for_paper` remains `false` unless a later hostile audit plus human/Manager fold gate explicitly changes it.

## 1. Purpose and non-fishing scope

Experiment A converts selected underpowered C2 cells into powered verdicts at the declared `delta=0.05` floor, and regenerates a complete raw bundle for hostile audit. The design is symmetric: every fixed cell is reported whether it yields PASS, EQUIVALENT, NEGATIVE-CONTRAST, or UNDERPOWERED. No cell may be added, dropped, relayered, resized, or reinterpreted after DEV or TEST begins.

This is **not** a new latent-method search and not a re-fish for a passing cell. It uses the original single-layer additive CAA convention and compares `steer - prompt` on the frozen behavioral outcome/scorer for each axis.

## 2. Fixed cells, models, axes, and layers

Layers are frozen from committed C2 artifacts, not re-selected:

| Cell | Method | Model/checkpoint identity | Axis | Frozen CAA layer | Layer source | Why included |
|---|---|---|---|---:|---|---|
| A1 | CAA | `Qwen/Qwen2.5-7B-Instruct` (`a09a35458c702b33eeacc393d103063234e8bc28`) | deliberation | 20 | `results/arm_full/cell_caa__qwen2.5-7b/c2b_adjudication_results.json` (`axes[].axis=deliberation`, `layer=20`) | Underpowered C2 deliberation cell; cheap to power. |
| A2 | CAA | Llama-3-8B-Instruct; same Llama checkpoint family as frozen C2 (`/root/autodl-tmp/models/Meta-Llama-3-8B-Instruct` / accepted `NousResearch/Meta-Llama-3-8B-Instruct` mirror) | deliberation | 12 | `results/arm_full/cell_caa__llama3-8b/c2b_adjudication_results.json` (`axes[].axis=deliberation`, `layer=12`) | Underpowered C2 deliberation cell; cheap to power. |
| A3 | CAA | `Qwen/Qwen2.5-7B-Instruct` (`a09a35458c702b33eeacc393d103063234e8bc28`) | skepticism | 20 | `results/arm_full/cell_caa__qwen2.5-7b/c2b_adjudication_results.json` (`axes[].axis=skepticism`, `layer=20`) | Most underpowered C2 cell; direct reviewer-power concern. |
| A4 | CAA | `Qwen/Qwen2.5-7B-Instruct` (`a09a35458c702b33eeacc393d103063234e8bc28`) | uncertainty_awareness | 20 | `results/arm_full/cell_caa__qwen2.5-7b/c2b_adjudication_results.json` (`axes[].axis=uncertainty_awareness`, `layer=20`) | Already robust negative in prior evidence, but raw-bundle lineage was incomplete; rerun only to make the result foldable/auditable. |

No other model, method, axis, layer, alpha grid, prompt family, scorer, or item count is in scope. A4 deliberately returns to the original frozen Qwen CAA primary layer (L20); it does not inherit the later resolution-refinement DEV-selected uncertainty layer.

## 3. Primary estimand and dual pre-registered hypotheses

For each TEST item `i`, with the fixed `k=5` sampled generations per channel:

`d_i = outcome_i(steer) - outcome_i(prompt)`.

Primary outcomes are the frozen deterministic/scored behavioral outcomes:

- deliberation: GSM8K exact-match numeric accuracy (`score_deliberation`);
- skepticism: TruthfulQA MC1 keyed false-premise rejection (`score_skepticism`);
- uncertainty_awareness: per-item `1 - Brier = 1 - (confidence - correct)^2`.

Per cell, two hypotheses are reported:

- **H_sup (unchanged frozen pass rule):** 98.33% Bonferroni item-cluster bootstrap CI excludes 0 **and** mean `>= delta=0.05` **and** the coherence gate passes. This yields `PASS` only under the original frozen superiority rule.
- **H_equiv (new, pre-registered TOST):** SESOI `±0.05`; the 90% TOST item-cluster bootstrap CI lies entirely inside `[-0.05, +0.05]`. This yields `EQUIVALENT` only under the strict equivalence rule.

## 4. Strict verdict rule

Each fixed cell must be reported exactly once using this priority order:

1. **PASS**: H_sup holds under the unchanged frozen pass rule.
2. **NEGATIVE-CONTRAST**: the paired steer-minus-prompt CI is wholly below zero (`CI_hi < 0`); this is steering harm / negative contrast, not equivalence.
3. **EQUIVALENT**: the 90% TOST CI is wholly inside `[-0.05, +0.05]`.
4. **UNDERPOWERED**: none of the above holds, including any ordinary nonsignificant CI that still admits meaningful effects.

A nonsignificant superiority test is **never** relabeled as equivalence. In particular, if A3's pool-limited achieved MDE leaves the 90% TOST CI outside `±0.05`, A3's honest verdict is `UNDERPOWERED`.

Coherence failure is reported as a failed cell diagnostic and cannot be used to rescue or hide a favorable interpretation. All parse failures, truncation, degeneracy, and missingness remain item-level ITT records.

## 5. A-priori power, fixed N, pools, and planned MDE

Power source artifacts:

- `results/posthoc_equivalence/posthoc_equivalence_e0006.json` for current `N`, `se_estimate`, and `mde_superiority_80pct_power`.
- `results/c2b_resolution_refinement/test-sealed/resolution_refinement_results.json` for committed skepticism/uncertainty selected-total and DEV/TEST split sizes.

Formula: `per_item_sigma = se_estimate * sqrt(N_current)` and `N_target = N_current * (current_MDE / 0.05)^2`. Planned MDE scales as `current_MDE * sqrt(N_current / planned_TEST_N)`.

| Cell | Current N | `se_estimate` | Per-item sigma | Current MDE | Exact N_target for MDE<=0.05 | Ceiling | Fresh pool / selected total | Planned DEV N | Planned TEST N | Planned achievable MDE |
|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| A1 Qwen deliberation | 40 | 0.023080 | 0.145971 | 0.074700 | 89.281440 | 90 | GSM8K test eligible pool 1259 after excluding frozen 60; selected total 225 shared with A2 | 75 | 150 | 0.038575 |
| A2 Llama deliberation | 40 | 0.021706 | 0.137281 | 0.070200 | 78.848640 | 79 | Same deliberation selected total 225 shared with A1 | 75 | 150 | 0.036251 |
| A3 Qwen skepticism | 40 | 0.058089 | 0.367387 | 0.188000 | 565.504000 | 566 | TruthfulQA validation 817 minus frozen 60 = selected total 757 (pool cap) | 252 | 505 | 0.052911 |
| A4 Qwen uncertainty_awareness | 53 | 0.060493 | 0.440396 | 0.195800 | 812.757968 | 813 | TriviaQA validation is ample; selected total 1219 to produce TEST 813 | 406 | 813 | 0.049993 |

Pool-size confirmation before freeze:

- `openai/gsm8k`, config `main`, split `test`: 1319 rows; excluding the frozen first-60 deliberation pool leaves 1259 eligible rows, so planned total 225 / TEST 150 is ample.
- `truthfulqa/truthful_qa`, config `multiple_choice`, split `validation`, revision `741b8276f2d1982aa3d5b832d3ee81ed3b896490`: 817 rows; excluding `truthfulqa-mc1-00000` through `truthfulqa-mc1-00059` leaves 757, giving DEV 252 / TEST 505.
- `mandarjoshi/trivia_qa`, config `rc.nocontext`, split `validation`, revision `0f7faf33a3908546c6fd5b73a660e0f8ff173c2f`: 17944 rows; excluding `triviaqa-00000` through `triviaqa-00079` is ample. This protocol selects 1219 fresh items, giving DEV 406 / TEST 813.

## 6. Data sources, exclusion, and deterministic split

All pools are disjoint from the frozen first-N C2 item pools:

| Axis | Dataset/config/split | Pinned revision | Excluded frozen IDs | Selected total | DEV/TEST split |
|---|---|---|---|---:|---|
| deliberation | `openai/gsm8k`, `main`, `test` (MIT) | dataset default as resolved at run; data hash required | `gsm8k-test-00000` through `gsm8k-test-00059` | 225 | 75 / 150 |
| skepticism | `truthfulqa/truthful_qa`, `multiple_choice`, `validation` | `741b8276f2d1982aa3d5b832d3ee81ed3b896490` | `truthfulqa-mc1-00000` through `truthfulqa-mc1-00059` | 757 | 252 / 505 |
| uncertainty_awareness | `mandarjoshi/trivia_qa`, `rc.nocontext`, `validation` | `0f7faf33a3908546c6fd5b73a660e0f8ff173c2f` | `triviaqa-00000` through `triviaqa-00079` | 1219 | 406 / 813 |

Selection rule is frozen before any DEV/TEST generation: load the pinned split in upstream order; construct stable IDs using existing loaders; remove excluded frozen IDs; use NumPy `default_rng(20260812)` (PCG64) to select the fixed `selected total` count, sort selected positions back to upstream order, then apply the existing `split_dev_test` rule with seed `20260812` (`round(N/3)` DEV, remaining TEST, sorted stable IDs). A1 and A2 share the same deliberation item IDs and split.

Any missing ID, duplicate ID, revision drift, selected-pool shortfall, overlap with excluded IDs, DEV/TEST overlap, or data-hash mismatch is a hard abort before scientific use. No headroom-based deletion, complete-case deletion, or post-hoc item substitution is allowed after this freeze; any desire to reintroduce a model-performance headroom filter is a protocol change requiring Manager/human gate before DEV.

## 7. Frozen generation, selection, and analysis parameters

- Method: single-layer additive CAA only.
- Comparator: same bounded best-of-16 authored prompt candidate family used by the frozen grid.
- Prompt selection: DEV only.
- Alpha selection: DEV only, fixed grid `{2,4,6,8,12,16,24}`.
- TEST receives only sealed prompt, alpha, layer, direction, item IDs, fixed scorer, and fixed analysis code.
- `k=5`; temperature `0.7`; `max_new_tokens=64`; sampled generation.
- A800 operational profile: `nvidia-a800-80gb`, profile SHA-256 `sha256:65e4cf84a9bc58b61152b911ab87648692914b1cee75aa17e97cd5f823fad249`.
- Bootstrap: paired item-cluster, `B=10000`, seed recorded in the artifact.
- Superiority CI: two-sided 98.33% Bonferroni (`1 - 0.05/3`) retained from the frozen three-axis family.
- Equivalence CI: 90% TOST CI for SESOI `±0.05`.
- Coherence gate: unchanged frozen gate (`steered mean degeneracy <= 1.5 * unsteered_TEST_mean_degeneracy + 0.02`, or the exact existing frozen implementation if stricter).
- Item-level ITT: no post-hoc item deletion; unparsed skepticism MC response scores `0`; absent uncertainty confidence uses the frozen uninformative value; all parsing/truncation/missingness diagnostics are retained.

TEST is never used for prompt, alpha, layer, item count, scorer, outcome, or interpretation selection.

## 8. TEST-once, no-peeking, and immutable lineage

The sequence is `preflight -> DEV -> TEST exactly once`. Immediately before first TEST generation, the runner must create a host-global marker with `O_CREAT|O_EXCL`, keyed by `powered-tost-A-test-20260813`, independent of `--out-dir`. A per-output `test/TEST_STARTED.json` must copy the canonical marker path and payload but is not the uniqueness authority.

No peeking, early stopping, stop-on-significance, sample-size change, rerun for significance, deletion of the marker, `--fresh` bypass, adding cells, changing layers, changing alpha grid, or switching models is allowed. Any operational failure after TEST starts is a failed attempt requiring a new Manager/human decision and a new protocol identity.

## 9. Mandatory raw-bundle retention and commit

A run whose full raw bundle is not committed to the experiment branch is invalid and cannot be folded. Immediately after DEV/TEST, the branch must commit a SHA-256 manifest and all audit-critical artifacts, including at minimum:

- full per-item generations/transcripts for prompt and steer channels;
- per-item outcomes and per-sample outcomes;
- paired `steer`, `prompt`, and raw response records with stable item IDs and sample IDs;
- parse diagnostics, truncation flags, degeneracy/coherence diagnostics, and missingness/imputation flags;
- DEV selection artifacts: item IDs, prompt candidate scores, selected prompt, alpha, CAA direction file/hash, layer, and sealed DEV hash;
- TEST artifacts: `TEST_STARTED.json`, host-global marker payload/path, final sealed result, and result hash;
- config, command line, seeds, data hashes, dataset revisions, model revisions/checkpoint identity, code commit, dirty-tree status, hardware profile SHA-256, environment/platform metadata;
- an experiment-registry row with `valid_for_paper: false` until the later hostile audit/fold gate.

The manifest must make every reported number reproducible from committed raw artifacts. Manual transcription of table values is prohibited.

## 10. Piggyback C1 READ confirmatory-ization

If Phase 2 compute is authorized, the same run window may additionally execute the C1 READ facade readout under its frozen protocol with **at least 3 seeds** and the same raw-bundle/manifest retention standard. C1 READ is a separate estimand and separate evidence row; it does not alter A1-A4, does not authorize any C2 cell change, and remains `valid_for_paper=false` until hostile audit plus Manager/human fold gate.

## 11. Interpretation and fold gate

Every cell is reported regardless of outcome. Positive, negative, equivalent, and underpowered findings all update the evidence ledger. The paper may not fold this experiment as confirmatory evidence until:

1. the protocol was committed before DEV/TEST;
2. the raw bundle and SHA-256 manifest are committed;
3. all numbers regenerate from artifacts;
4. an independent hostile audit passes implementation/statistics/reproducibility checks;
5. the Manager/human fold gate explicitly approves changing any paper claim status.

Until then, the result is an unrun frozen protocol (before Phase 2) or a completed-but-not-folded artifact with `valid_for_paper=false`.

## 12. Required implementation work before Phase 2

The current `scripts/run_c2b_resolution_refinement.py` / `src/cognitive_console/experiments/resolution_refinement.py` infrastructure is reusable but not sufficient for Experiment A as-is:

- it hard-codes only two axes: `skepticism`, `uncertainty_awareness`;
- it hard-codes only Qwen CAA model identity and one TEST experiment ID;
- it does not include `deliberation` / `load_gsm8k_test` in the resolution-refinement item loader;
- it cannot express four cells, two models, shared deliberation split, per-cell fixed layers, or C1 READ piggyback;
- its synthetic preflight currently reports only skepticism DEV/TEST `252/505` and uncertainty DEV/TEST `406/813`.

Phase 2 must therefore add a new Experiment A runner or extend the existing runner to represent cell identity `(cell_id, method, model, axis, layer)`, load GSM8K deliberation items with frozen exclusions, preserve A1/A2 shared item IDs, maintain TEST-once identity, emit TOST verdict fields, and commit the complete raw bundle. These changes must happen before any DEV/TEST run and must not modify or overwrite the frozen 0/12, E-0005/E-0006/E-0011, or prior resolution-refinement artifacts.

## 13. Clarifications relative to the draft

- The draft's deliberation per-item sigma values were approximate placeholders; this frozen version uses the committed `se_estimate` fields from `posthoc_equivalence_e0006.json`, yielding A1 sigma `0.145971` and A2 sigma `0.137281`.
- Qwen CAA is frozen to L20 for all Qwen cells from the original C2 artifact; A4 does not use the later resolution-refinement uncertainty L24.
- The draft's GSM8K headroom phrase is not used as an unfrozen item-deletion rule. Experiment A freezes a deterministic fresh GSM8K selected pool. Reintroducing a base-model headroom filter would be a protocol change before DEV and requires Manager/human approval.
