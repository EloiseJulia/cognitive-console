# Frozen Prereg — Latent Behavioral Positive Control (Stage-1 DEV only)

- **Owner approval:** 2026-08-17.
- **Experiment ID:** `E-0017-latent-behavioral-positive-control`.
- **Stage covered by this file:** **Stage-1 only** — freeze protocol, license gate, reproduce direction, DEV select layer/α, smoke/tests. **TEST is hard-disabled until Manager says “Stage-2 GO.”**
- **Paper status:** `valid_for_paper=false` until Stage-2 TEST and independent hostile audit pass.

## 1. Purpose and hypothesis

The current paper has an assay-validity threat: 0/12 latent-control cells could mean either true non-operability or a broken/insensitive latent behavioral pipeline. This positive control tests whether the same adjudication machinery can detect a known latent behavioral effect.

**Positive-control hypothesis (diagnostic, not a core paper claim):** a faithful Stolfo-style instruction steering vector for a clean constraint task increases programmatically verified constraint satisfaction relative to an unsteered/no-instruction baseline on DEV, and later on a frozen TEST if Manager approves Stage-2.

## 2. Method source and fidelity constraints

Primary literature/code reference:

- Alessandro Stolfo, Vidhisha Balachandran, Safoora Yousefi, Eric Horvitz, Besmira Nushi. *Improving Instruction-Following in Language Models through Activation Steering*, ICLR 2025. OpenReview `wozhdnRCtw`; code `microsoft/llm-steer-instruct` at main commit `9dac937ef6fc3e483b1efc13863deeb03ec38dbe`.

Faithful reproduction choices:

1. Build paired inputs from the same base prompt: **with instruction** vs **without instruction**.
2. Run the model and capture final-token residual activations.
3. Compute the instruction vector as `mean(h_with_instruction - h_without_instruction)`.
4. Normalize the vector and add `α * unit_vector` to the residual stream at one decoder-block output during generation.
5. Use the Stolfo non-Gemma validation layer-search family: candidate source-layer indices `range(n_layers // 5, n_layers, 2)` (0-based TransformerLens-style `resid_post` block indices). In this repo’s HF hook convention, source layer `s` maps to hidden-state / hook layer `s+1`.
6. DEV selects the layer and α; TEST will use the sealed DEV choice once, with no TEST tuning.

## 3. Model, data, and license

- **Model:** `Qwen/Qwen2.5-7B-Instruct`, pinned revision `a09a35458c702b33eeacc393d103063234e8bc28` if the local HF cache permits revision pinning; otherwise record the exact resolved revision in the run artifact.
- **Model license:** Apache-2.0 (checked in `docs/research/2026-08-17-latent-positive-control-license.md`).
- **Method/code license:** `microsoft/llm-steer-instruct` MIT (same license document).
- **Dataset:** self-authored keyword-inclusion prompts in `data/latent_positive_control/keyword_blue_items.json`.
- **Data hash:** `sha256:2c6d946433edd555d504dc2c8ab7e75fee01eb6f589728b47687ea889b594d91`.
- **No external dataset is used in Stage-1.** IFEval is intentionally avoided for this assay-validity DEV run.

## 4. Task and verifier

- **Constraint family:** Stolfo-style word-specific instruction following.
- **Keyword:** `blue`.
- **Prompt arm:** append ` Include the word "blue" exactly once.` to the base prompt.
- **Baseline arm:** base prompt only, no steering.
- **Steer arm:** base prompt only, with the instruction steering vector added to the residual stream.
- **Verifier:** deterministic case-insensitive whole-word regex for `blue`; output is binary `{0,1}`. No confidence, judge, or imputation outcome is allowed.
- **Degeneracy/coherence score:** existing frozen trigram degeneracy score `g(text)=1-distinct_trigram_ratio`.

## 5. Estimands and decision procedure

Primary estimand (owner-approved option B):

- `Δ_primary = mean(score_steer - score_baseline)`.

Secondary/comparator-bound estimand:

- `Δ_secondary = mean(score_steer - score_prompt)`.

Frozen thresholds/procedure reused from C2b where applicable:

- α grid: `{2,4,6,8,12,16,24}`.
- δ: `0.05`.
- Bootstrap: paired item-cluster percentile bootstrap, `B=10000`.
- CI level: Bonferroni `1 - 0.05/3 = 0.983333...` (kept intentionally identical to C2b).
- Coherence gate: `g^S <= 1.5 * g^0 + 0.02`.
- Generation: greedy deterministic decoding to match Stolfo scripts; represented as `k=5` identical within-item samples for the unchanged item-cluster bootstrap shape.
- DEV success sanity: selected coherent steer cell has `Δ_primary >= δ` and strictly higher DEV compliance than baseline. DEV sanity is **not** paper evidence.
- Stage-2 TEST pass rule, if approved later: CI excludes 0, mean `Δ_primary >= δ`, and coherence passes. `Δ_secondary` is always reported, even if it underperforms a strong prompt.

## 6. Stage-1 split and sealed TEST boundary

- Extraction pairs: first 24 self-authored extraction prompts.
- DEV: 12 self-authored DEV items.
- TEST: 60 self-authored TEST items sealed in the same data file but **not generated, scored, inspected for outcomes, or used for tuning in Stage-1**.
- Script boundary: `scripts/run_latent_positive_control.py` rejects `--allow-test`; Stage-1 artifacts must state `stage2_test_run=false`.

## 7. Fixed run configuration

- Seed: `20260817`.
- Max new tokens: `64`.
- Max prompt length: `256`.
- Activation batch size default: `4`.
- Generation batch size default: `4`.
- Candidate source layers: derived from model depth by the Stolfo rule above.
- Code commit: the protocol/code commit is the git commit containing this prereg and runner; the exact hash is reported in the Stage-1 handoff because a commit cannot self-contain its own future hash.
- Config hash: script-generated from all fields affecting outcomes and persisted in `latent_positive_control_dev_results.json`.

## 8. Outcome neutrality

Both outcomes are valid and must be reported honestly:

- **Pass / DEV positive:** the assay can detect a known latent instruction-following control, strengthening the interpretation that later TEST negatives are method/task-specific rather than a broken pipeline.
- **No-pass / DEV null:** even this known positive control does not reproduce under our model/hook/layer/scoring setup; the assay has a deeper sensitivity limitation. Stop and report; do not change thresholds or mine TEST.

## 9. Pre-Stage-2 gates

Before true TEST, Manager must verify:

1. Stage-1 prereg commit exists and DEV artifact records `valid_for_paper=false`.
2. License gate remains clear.
3. DEV selected layer/α is sealed.
4. TEST command is added/reviewed only after “Stage-2 GO”.
5. GPU is free and budget remains approved.
6. TEST runs once; no TEST tuning.
7. Independent hostile audit reviews TEST artifacts before any paper use.

## 10. Owner-approved Stage-1 rerun addendum (2026-08-17)

After the first Stage-1 DEV failed with a from-scratch reimplementation, owner approved a rerun that directly uses `microsoft/llm-steer-instruct` official code rather than project-local extraction/injection code.

Frozen addendum for `E-0017b-official-stolfo-latent-positive-control-stage1-dev`:

- **Official repo commit:** `9dac937ef6fc3e483b1efc13863deeb03ec38dbe`.
- **Official code paths used:** `utils/model_utils.py`, `utils/generation_utils.py`, keyword representation/evaluation logic, and `ifeval_scripts/evaluation_main.py`.
- **Task/data:** official repo `data/keywords/ifeval_single_keyword_include.jsonl`, IFEval `keywords:existence`.
- **DEV size:** complete DEV rerun uses 40 official keyword items after an 86-item attempt was stopped for runtime; this is still above the rejected 12-item toy prompt setup and uses official task format. TEST remains sealed/not run.
- **Layer/α source:** official keyword config defaults to `source_layer_idx=24`; official `keywords/load_results.py` example reports layer `26`, weight `40`. The completed DEV rerun uses official layer `26` and scans frozen α `{2,4,6,8,12,16,24}` plus diagnostic non-selectable α `40`.
- **Decision procedure unchanged:** primary `steer-baseline`; secondary `steer-prompt`; same δ/bootstrap/coherence/Bonferroni; no TEST tuning.

## 11. Owner-approved Phi-3 official positive-control addendum (2026-08-17)

After Qwen official-code DEV failed and Gemma-2-2B-IT was blocked by gated access, owner approved the non-gated official Stolfo positive-control setup on `microsoft/Phi-3-mini-4k-instruct`.

Frozen addendum for `E-0017d-phi3-official-stolfo-positive-control-stage1-dev`:

- **Model:** `microsoft/Phi-3-mini-4k-instruct`, pinned revision `f39ac1d28e925b323eae81227eaba4464caced4e`.
- **Official repo commit:** `9dac937ef6fc3e483b1efc13863deeb03ec38dbe`.
- **Task/data:** official repo `data/keywords/ifeval_single_keyword_include.jsonl`, IFEval `keywords:existence`.
- **DEV size:** first 40 official keyword-inclusion items; TEST remains sealed/not run.
- **Direction extraction:** official contrast-set flow with `n_extraction_per_keyword=20`, yielding 820 extraction rows.
- **Layer/weight source:** official Appendix-E Phi-3 word-inclusion grid: layers `{24,26,28}`, weights `{40,60,80,100}`.
- **Decision procedure unchanged:** primary `steer-baseline`; secondary `steer-prompt`; δ/bootstrap/coherence/Bonferroni unchanged.
- **Runtime caveat:** full 1024-token and then 128-token DEV attempts were stopped for runtime before completion. The completed DEV used the same official layers/weights/direction/task/verifier but capped generation at 32 new tokens. This cap is recorded in the artifact config hash and must be reported before any Stage-2 decision.
