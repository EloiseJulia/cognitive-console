# Hostile Audit — Composition ITI×Qwen Shard (2nd shard, additive)

- **Auditor:** independent hostile audit session `audit-composition-iti` (fresh, no-context, adversarial), 2026-08-19
- **Target:** `feature/composition-a@a569407`
- **Experiment:** `composition-a-qwen-iti-20260818-0001` (ITI shard of the frozen c2b-composition-augmentation prereg)
- **Verdict:** **SCIENCE SOUND for merge; paper-use CONDITIONAL on ledger fold-gate (now done, D-0137).**

## Independent re-derivation
All 6 cell mean/CI/MDE recomputed from committed `per_item_test_pairs.jsonl` (prereg bootstrap_seed=20260819, B=10000) **bit-match** the JSON.

| baseline | axis | Δ | 98.33% CI | MDE | verdict |
|---|---|---|---|---|---|
| ordinary | deliberation | −0.0090 | [−0.0280, +0.0100] | 0.0260 | NO_INCREMENT |
| ordinary | skepticism | −0.0175 | [−0.0425, +0.0070] | 0.0344 | NO_INCREMENT |
| ordinary | uncertainty | −0.0441 | [−0.0808, −0.0091] | 0.0492 | **INVALID (parse gate fail)** |
| strong | deliberation | −0.0255 | [−0.0455, −0.0067] | 0.0260 | NO_INCREMENT (real small negative) |
| strong | skepticism | −0.0250 | [−0.0535, +0.0035] | 0.0386 | NO_INCREMENT |
| strong | uncertainty | −0.0123 | [−0.0281, +0.0038] | 0.0219 | NO_INCREMENT |

## Findings
- **MAJOR (now closed by fold-gate D-0137):** ledger/paper gate — registry `valid_for_paper:false` and evidence-ledger "ITI/Llama untested" needed updating.
- **MINOR — strong-deliberation is a REAL small negative:** Δ=−0.0255 CI[−0.0455,−0.0067], coherence PASS (prompt 0.1212, steer 0.1352, gate 0.2018). Not an artifact. Must be reported as a small degradation, not merely "null."
- **MINOR — ordinary-uncertainty must be labeled INVALID/PARSE, not harm evidence:** 47/400 items missing (unparseable confidence → 0.5 imputation). Complete-case Δ=−0.0447; adversarial upper Δ=−0.0311 with CI crossing 0 → no gain either way. Diagnostic-only.
- **UNVERIFIED:** raw transcripts remote-only; direction reference absent (frozen-code reconstruction caveat only).

## Usable cells & combined picture
- 5/6 cells valid, all non-positive; ordinary-uncertainty diagnostic-only.
- Combined with the CAA shard (E-COMPOSITION-A), **Qwen composition shows a robust absence of positive increment across BOTH methods (CAA and ITI)**; ITI additionally trends slightly negative (strong-deliberation a real small decrement).
- Caveats retained: single model (Qwen), Llama untested; ordinary prompt is a plain-instruction everyday-user proxy (human-anchor gap); additive, does not revise frozen 0/12.

## Tests
- Full pytest: 1 env/pre-existing failure, reproduced on main; not attributable to this branch.
