# E-0012-CS Reconciliation Hostile Audit

Auditor: independent hostile auditor; did not write the code.  
Checkout audited: `run/e0012-cs-20260801` at `7fbb5f04f3fd5c18a72fe4c7558a03a9ee9fccd3`.  
Primary artifacts: `results/E-0012-CS/*`, `results/E-0012/*`; v3 source cross-check via `git show run/e0012-modelgen-v3-20260731:...`.

## Commands actually run

- Read `AGENTS.md`, `AI-Instruction.md` §9, both preregs, `reviews/2026-07-31-e0012-v3-audit/audit-report.md`, and `reviews/2026-07-31-e0012-cs-code-audit/audit-report.md`.
- Inspected source with `rg`, `view`, and `git show run/e0012-modelgen-v3-20260731:src/cognitive_console/experiments/e0012_harness.py`.
- Parsed and recomputed from:
  - `results/E-0012/brier_raw_pairs.jsonl`
  - `results/E-0012/e0012_results.json`
  - `results/E-0012/e0012_stage0_candidates.json`
  - `results/E-0012-CS/comparator_strength.json`
  - `results/E-0012-CS/comparator_strength_raw_pairs.jsonl`
- Verified branch/status with `git --no-pager status --short --branch`, `git --no-pager rev-parse HEAD`, and `git --no-pager branch --show-current`.
- Imported `scripts/run_e0012_comparator_strength.py` and rebuilt the button condition to verify direction shape/norm/hash.

## CS-button-0.141 vs v3-button-0.680 reconciliation

### Definitive ruling: **A — v3 "steer" is prompt-contaminated; the true pure-steering TEST effect is CS ≈ baseline**

The contradiction is resolved by source, not statistics: v3's Stage1 `steer` channel is **not** pure steering. It passes `best_prompt_text` into the steered call.

Exact v3 source (`src/cognitive_console/experiments/e0012_harness.py` on `run/e0012-modelgen-v3-20260731`):

- `run_e0012_harness` passes `best_prompt_text=stage0.best_prompt_text` into every Stage1 candidate (`e0012_harness.py:977-982`).
- `run_stage1_candidate` then evaluates:
  - steered channel with `best_prompt_text`, candidate `alpha`, candidate `direction`, candidate `layer` (`e0012_harness.py:638-642`);
  - prompt channel with the same `best_prompt_text`, `alpha=0.0` (`e0012_harness.py:643-647`);
  - baseline with empty instruction, `alpha=0.0` (`e0012_harness.py:648-652`).

Therefore v3's reported BTN-CAL-PROBE TEST score 0.680 is **CAL-09/best-prompt + steering**, not empty-prompt/pure steering.

Raw recomputation confirms the contamination:

| Artifact/channel | Instruction condition | Mean 1-Brier | Mean confidence | Mean correctness |
|---|---|---:|---:|---:|
| v3 `s1_baseline_BTN-CAL-PROBE_19_24` | empty, no steering | 0.144028 | 0.952264 | 0.056604 |
| v3 `s1_prompt_BTN-CAL-PROBE_19_24` | best prompt, no steering | 0.536575 | 0.696189 | 0.083019 |
| v3 `s1_steer_BTN-CAL-PROBE_19_24` | best prompt + L19 α24 steering | 0.680364 | 0.528717 | 0.064151 |
| CS `BASELINE-UNSTEERED-NO-PROMPT` | empty, no steering | 0.144028 | 0.952264 | 0.056604 |
| CS `BTN-CAL-PROBE-L19-A24` | empty + L19 α24 steering | 0.140547 | 0.959623 | 0.067925 |

So the true pure-steering held-out TEST effect is:

`0.140547 - 0.144028 = -0.003481` mean 1-Brier versus no-prompt baseline.

The v3 absolute 0.680 decomposes as mostly prompt effect plus a prompt-conditioned steering increment:

- prompt-only over baseline: `0.536575 - 0.144028 = +0.392547`;
- prompt+steer over prompt-only: `0.680364 - 0.536575 = +0.143789`;
- pure empty-prompt steering over baseline in CS: `-0.003481`.

**Implication:** v3 `LOCAL` is prompt-contaminated if narrated as "the button alone beats the prompt comparator" or "pure steering control." At most, v3 shows a prompt-conditioned additive effect on top of the best prompt used by Stage1. E-0012-CS correctly measures the pure empty-prompt button and shows it is a near-no-op.

## Button direction and alpha sanity

CS did not use a zero/wrong-shape direction. The button condition is legitimate as a pure-steering measurement:

- CS constructs the button by calling `all_directions_for_layer(BUTTON_LAYER, hidden_dim)` and selecting `BTN-CAL-PROBE` (`scripts/run_e0012_comparator_strength.py:135-139`).
- It persists `system_prompt=""`, `layer=19`, and `alpha=24.0` (`scripts/run_e0012_comparator_strength.py:140-155`).
- `score_condition` passes `instruction=condition.prompt_text`, `alpha=condition.alpha`, `direction=condition.direction`, `layer=condition.layer`, and `k=5` into `_eval_items_with_raw_pairs` (`scripts/run_e0012_comparator_strength.py:202-211`).
- Rebuilt direction: shape `(3584,)`, norm `0.9999999999999999`, nonzero entries `3584/3584`, derivation hash `2ce428b423aaa900`; it exactly matches direct `all_directions_for_layer(19, 3584)`.
- CS raw pairs are not byte-identical to baseline: 197/265 sequential `(confidence, correctness)` pairs match, but 31/53 item-level means differ. This is not a hard no-op implementation bug; it is a real but scientifically negligible perturbation.

Caveat: both v3 and CS use the same `all_directions_for_layer` synthetic direction factory (`e0012_harness.py:940-945`; `e0012_buttons.py:387-397`). The persisted CS note says "SYNTHETIC (offline): random unit vector used as stand-in for real probe direction." This does **not** explain 0.141 vs 0.680 because both code paths use the same derivation; it is a separate naming/provenance caveat if the paper calls this a trained probe direction.

## Human-prompt evidence validity

The CS human-prompt side is sound and usable as robustness evidence after sign-off:

- `comparator_strength.json` reports 27 DEV / 53 TEST, split overlap 0, 50 conditions, counts `{synthetic_bank: 30, calibration_yaml: 18, baseline: 1, button: 1}`.
- Raw JSONL has 13,250 rows = `50 * 53 * 5`; every row has `synthetic_proxy=false`; every condition has 265 rows.
- TEST-only: artifact DEV ids and TEST ids have recomputed intersection 0; scoring loop uses `test_items` only in `score_condition`.
- Recomputed from raw pairs:
  - `SYNTH-BANK-26`: 0.794047 mean 1-Brier; mean confidence 0.433019; mean correctness 0.056604.
  - `CAL-09`: 0.536575 mean 1-Brier; mean confidence 0.696189; mean correctness 0.083019.
  - baseline: 0.144028 mean 1-Brier; mean confidence 0.952264; mean correctness 0.056604.
  - button: 0.140547 mean 1-Brier; mean confidence 0.959623; mean correctness 0.067925.
- Summary fields correctly identify `max_human_prompt = SYNTH-BANK-26` with score 0.794047 and `best_calibration_yaml = CAL-09` with score 0.536575.

Conclusion: the human prompt measurement is sound. It demonstrates a human-authored prompt far exceeds both pure steering and the v3 prompt+steer score on the same TEST split.

## Ranked findings

### BLOCKER-1 — v3 Stage1 "steer" channel is not pure steering

**Evidence:** v3 `run_stage1_candidate` calls `_eval_items_with_raw_pairs(..., best_prompt_text, alpha, direction, layer, ...)` for `chan_steer` (`e0012_harness.py:638-642`), while only `chan_baseline` uses `""` (`e0012_harness.py:648-652`). Raw v3 `s1_steer_BTN-CAL-PROBE_19_24` score 0.680364 is prompt+steer; CS empty-prompt button is 0.140547.

**Impact:** Any paper claim that v3 established a pure button/steering-only effect is false. v3 `LOCAL` is contaminated for that narrative.

**Minimum fix:** Reword v3 as prompt-conditioned additive steering only, or discard v3 as evidence for pure steering. Use CS as the pure-steering result.

### MAJOR-1 — Pure empty-prompt button is a near-no-op and loses to baseline by raw recomputation

**Evidence:** CS button score 0.140547 vs baseline 0.144028 from `comparator_strength_raw_pairs.jsonl`; confidence barely changes upward 0.952264 → 0.959623. Direction/alpha were applied and nondegenerate, so this is not a zero-vector implementation failure.

**Impact:** The "button" does not provide standalone calibration control on TEST.

**Minimum fix:** Treat the button-side E-0012 result as negative/null for pure steering. Do not use it as positive evidence for latent control.

### MAJOR-2 — Human prompts are stronger than both pure button and v3 prompt+steer

**Evidence:** CS `SYNTH-BANK-26` recomputes to 0.794047 on TEST, exceeding v3 prompt+steer 0.680364 and pure button 0.140547.

**Impact:** The paper can use CS as evidence for the non-surjective/control-gap narrative, but not for "button beats prompt."

**Minimum fix:** Center the narrative on prompt strength and failed pure steering, not verified-control success.

### MINOR-1 — Direction provenance wording is risky

**Evidence:** CS and v3 derive the direction through `all_directions_for_layer`, which dispatches to synthetic derivations (`e0012_buttons.py:371-397`); the CS persisted direction note calls it a random stand-in. The vector is real/nonzero but not a trained real-GPU probe in these artifacts.

**Impact:** Mislabeling it as a trained probe direction would overstate mechanism validity.

**Minimum fix:** Explicitly call it the frozen synthetic stand-in direction unless a real probe artifact is produced and audited.

## Final verdict

**CS-SOUND-BUTTON-IS-NOOP-V3-CONTAMINATED.**

CS is sound for the human-prompt evidence and for the pure empty-prompt button measurement. The true pure-steering TEST effect is approximately baseline/no-op (`0.140547` vs `0.144028`). The v3 0.680 number is prompt+steer, not pure steering; v3 `LOCAL` must not be used as evidence that the button alone beats prompts.
