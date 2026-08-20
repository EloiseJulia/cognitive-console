# Hostile Audit — ITI Deliberation 512-token Re-measurement (additive, Table 2)

- **Auditor:** independent hostile audit session `audit-iti-delib512` (fresh, no-context, adversarial), 2026-08-20
- **Target:** `feature/iti-delib512@22fa0b5` (seal-rehash BLOCKER fix at `7362689`)
- **Experiment:** `iti-delib-512-test-20260820` (mirrors CAA E-DELIB512-REMEASURE, method=ITI)
- **Verdict:** **Numbers SOUND. One lineage BLOCKER (seal hash mismatch) — now CLOSED by rehash; seal==committed verified.**

## Independent re-derivation (from paired_test_channels.jsonl)
| cell | Δ (steer − best prompt) | 98.33% CI | 90% TOST | MDE | label |
|---|---|---|---|---|---|
| I1 (Qwen ITI) | −0.033333 | [−0.078667, +0.009333] | [−0.064, −0.004] | 0.0200 | UNDERPOWERED |
| I2 (Llama ITI) | +0.005333 | [−0.042667, +0.053333] | [−0.028, +0.038667] | 0.0347 | EQUIVALENT |

Labels correct.

## Checks
- **512 floor fixed:** I1 steer/prompt/unsteered accuracy = 0.840 / 0.873 / 0.843; I2 = 0.712 / 0.707 / 0.757; truncation 0. (Not the ~3% 64-token floor.)
- **DEV α reselected at 512:** both α=2.0 from the 512-DEV grid; DEV/TEST overlap = 0.
- **Estimand correct:** paired same-item steer − best-prompt; prompts I1 `delib-strong-09`, I2 `delib-strong-04`.
- **Method:** true ITI with σ scaling.
- **Coherence:** passes independently for both cells.
- **Additive:** no frozen 0/12 grid, E-0005/E-0006/E-0011, or CAA delib512 paths changed.

## Finding
### BLOCKER (CLOSED) — SEALED.json hash ≠ committed result/manifest
- Original: I1 SEALED `d8296...` vs committed/manifest `e1e1cf...`; I2 SEALED `00bd...` vs `7a9120...`.
- Root cause (documented in registry `lineage_fix`): per-cell result JSON was augmented with reporting diagnostics AFTER the initial TEST seal hashes were written; scientific arrays and metrics unchanged.
- Fix (`7362689`, `iti-delib512-seal-rehash`): regenerated SEALED.json / test/SEALED.json / SHA256_MANIFEST to match the committed result hashes (I1 `e1e1cf...`, I2 `7a9120...`); old hashes removed. Manager verified seal == committed; per-item arrays and all numbers unchanged.

### UNVERIFIED (not attributable) — pytest
- `tests/test_c2b_tasks.py::test_real_loader_is_deferred_offline` fails on this branch AND on main `5716cdd` — pre-existing env issue, not a regression.

## Paper scope
- Additive completion of the ITI deliberation cells in Table 2 (tab:c2-delta-4cell), mirroring the CAA E-DELIB512-REMEASURE.
- **Must report:** I1 (Qwen ITI) small-negative UNDERPOWERED; I2 (Llama ITI) near-zero EQUIVALENT — honest sign + power, no spin. Does not revise the frozen 0/12 grid.
