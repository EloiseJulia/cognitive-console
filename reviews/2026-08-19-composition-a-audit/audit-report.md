# Hostile Audit — Dispatch A Composition / Augmentation (CAA × Qwen)

- **Auditor:** independent hostile audit session `audit-composition-a` (fresh, no-context, adversarial), 2026-08-19
- **Target:** `feature/composition-a@f3494a0` (audit-major fixes at `d75ba65`)
- **Experiment:** `composition-a-qwen-caa-20260818-0001` (composition estimand: paired (prompt+steer) − (prompt alone))
- **Verdict:** **CONDITIONALLY SOUND → SOUND after fixes.** Core result sound: all 6 cells are well-powered nulls (MDE ≤ 0.023 < 0.06, CI includes 0).

## What the result supports
Only: **CAA × Qwen prompt+steer shows no detectable incremental gain over prompt-alone under these frozen ordinary/strong prompts, across the three axes.** NOT an equivalence proof; NOT a global "slider never works" claim.

## Independent re-derivation (from per_item_test_pairs.jsonl)
Reported means/MDE reproduce. All 6 CI include 0; all MDE pass (≤0.023). Recomputed with prereg bootstrap_seed=20260819 (fix commit `d75ba65`): all 6 verdicts unchanged.

| baseline | axis | mean Δ | 98.33% CI | MDE | verdict |
|---|---|---|---|---|---|
| ordinary | deliberation | +0.0045 | [−0.0085, +0.0175] | 0.0178 | NO_INCREMENT |
| ordinary | skepticism | +0.0055 | [−0.0090, +0.0205] | 0.0201 | NO_INCREMENT |
| ordinary | uncertainty | −0.0055 | [−0.0201, +0.0086] | 0.0194 | NO_INCREMENT |
| strong | deliberation | −0.0105 | [−0.0255, +0.0050] | 0.0210 | NO_INCREMENT |
| strong | skepticism | −0.0005 | [−0.0175, +0.0165] | 0.0231 | NO_INCREMENT |
| strong | uncertainty | +0.0034 | [−0.0098, +0.0167] | 0.0179 | NO_INCREMENT |

## Findings (both MAJORs now closed)

### MAJOR 1 (CLOSED) — bootstrap seed mismatch
- Original: prereg §206 froze bootstrap_seed=20260819; runner used run_seed+hash(axis|baseline).
- Fix (`d75ba65`): recomputed all 6 cells with the prereg seed; verdicts and MDE unchanged.

### MAJOR 2 (CLOSED) — uncertainty missingness sensitivity incomplete
- Original: scorer imputes missing confidence as 0.5; artifacts reported parse rates only.
- Fix (`d75ba65`): committed `missingness_sensitivity.{json,md}` with complete-case + adversarial bounds. Parse rates 0.99+ (ordinary 0.995/0.998, strong 0.990/0.9945), truncation 0; neither complete-case nor adversarial upper bound supports a gain.

### UNVERIFIED — raw transcript audit
- Raw transcripts remote-only (`transcript_pointers_sha256.txt`). Committed per-item/stat artifacts verified; raw text parsing not re-verified. Acceptable via pointer+hash.

## Other checks
- No re-selection: α* selected on composition-DEV and frozen before TEST; DEV/TEST zero overlap.
- Estimand correct: paired (prompt+steer) − (prompt alone), same item; ordinary/strong separate; prompts match frozen manifest.
- deliberation 512-token off floor; coherence pass all cells.
- Additive: no E-0005/E-0006/E-0011 artifacts modified.
- Full pytest: same 2 baseline failures as main, not attributable to this branch.

## Paper scope (what is licensed)
- **Can state:** even in the composition regime (steering added on top of a user instruction), CAA×Qwen provides no detectable incremental behavioral gain over the prompt alone on any of the three axes — a well-powered null that answers the "substitution-only ≠ real slider" reviewer BLOCKER.
- **Must state:** single method (CAA), single model (Qwen), ITI/Llama untested; ordinary prompt is a plain-instruction everyday-user proxy (human-anchor gap); additive, does not revise the frozen 0/12 headline; not an equivalence proof.
