# STAGED FOLD DRAFT — Experiment A (Powered TOST + C1 confirmatory) — OWNER-APPROVED to fold, PENDING Writer application

> **STATUS: staged prose. Owner approved fold (exploratory→confirmatory gate PASSED 2026-08-14).**
> Independent hostile correctness audit `audit-powered-tost` = **SOUND** (4 cells recomputed
> from committed raw artifacts, match to the digit; no BLOCKER/MAJOR; two MINOR only).
> Numbers below are for Writer to apply to `main.tex`; every value must be pulled from the
> committed result JSONs on `feature/powered-tost-a`, not retyped from memory.
> **Additive only:** does NOT overwrite the frozen 0/12 grid, E-0005/E-0006/E-0011, or the
> frozen `tables/c2-delta-4cell.tex`. No latent arm PASSED — the 0/12 conclusion is unchanged;
> the upgrade is from "underpowered / not independently checkable" to "powered / auditable."

## 0. Verified results (audit-SOUND, from feature/powered-tost-a @ cd1b14c)
| Cell | Model·Method·Axis | Layer | N | α | Δ steer−prompt [98.33% CI] | TOST 90% CI | achieved MDE | Verdict |
|---|---|---|---:|---:|---|---|---:|---|
| A1 | Qwen·CAA·deliberation | 20 | 150 | 2 | +0.0213 [0.000, 0.048] | [0.0053, 0.0400] | 0.0386 | EQUIVALENT |
| A2 | Llama·CAA·deliberation | 12 | 150 | 2 | +0.0067 [−0.008, 0.021] | [−0.0040, 0.0160] | 0.0363 | EQUIVALENT |
| A3 | Qwen·CAA·skepticism | 20 | 505 | 2 | −0.0143 [−0.049, 0.021] | [−0.0384, 0.0103] | 0.0529 | EQUIVALENT |
| A4 | Qwen·CAA·uncertainty | 20 | 813 | 24 | −0.0881 [−0.120, −0.058] | [−0.1093, −0.0675] | 0.0500 | NEGATIVE-CONTRAST |

C1 READ confirmatory: seeds 20260812/13/14, 3/3 axes hold; ratios deliberation 0.566, skepticism 0.520, uncertainty 0.507.

**MANDATORY honesty caveat (A3):** achieved MDE 0.0529 **> δ=0.05** (TruthfulQA pool-limited). Equivalence is
declared under the pre-registered rule (90% TOST CI ⊂ ±0.05), which A3 satisfies; but A3 is **not** MDE≤δ fully
powered. Must be stated wherever A3 equivalence appears.

**Scope caveat (all):** single fixed CAA cell per axis (A1/A2 deliberation both models; A3/A4 Qwen only), frozen
E-0005 layers, DEV-selected α, substitution design. Does NOT power the ITI cells or the Llama skepticism/uncertainty
cells; those remain as in the frozen grid. Pre-registered `docs/specs/powered-tost-A-prereg.md`, TEST-once.

---

## 1. EDIT — Results, Skepticism paragraph (main.tex ~L370)
**Anchor (KEEP the frozen-grid MDE sentence):** `\textbf{Skepticism directs the next evaluation toward resolution.}`
**APPEND after "...not an ineffectiveness verdict.":**
```latex
A pre-registered higher-resolution refinement of the Qwen--CAA cell (additive to the frozen grid, which is unchanged; both refined axes reported regardless of sign) sharpens this: at $N=505$ the steer-minus-prompt contrast is equivalent to the best prompt within the registered $\pm0.05$ margin (mean $-0.014$, 90\% TOST CI $[-0.038,+0.010]$; superiority CI $[-0.049,+0.021]$; coherent). Because the achievable resolution on the disjoint pool was $\text{MDE}=0.053$, slightly above the floor, this is a bounded-equivalence result under the pre-registered rule rather than a fully floor-powered null; the axis remains a no-pass and is not upgraded. {}% experiment_id powered-tost-A A3 (feature/powered-tost-a@cd1b14c)
```

## 2. EDIT — Results, Deliberation paragraph (main.tex ~L374)
**Anchor:** `\textbf{Deliberation preserves a mixed result.} Two ITI cells fell inside a $\pm0.05$ equivalence interval in a post-hoc TOST, while the CAA cells remained underpowered.`
**REPLACE the "while the CAA cells remained underpowered." clause** with:
```latex
..., and a pre-registered refinement now powers both CAA cells to the same conclusion (Qwen mean $+0.021$, 90\% TOST CI $[0.005,0.040]$, $N=150$, MDE $0.039$; Llama mean $+0.007$, CI $[-0.004,0.016]$, $N=150$, MDE $0.036$): CAA steering is equivalent to the best prompt within $\pm0.05$ on deliberation, no longer merely underpowered. {}% experiment_id powered-tost-A A1,A2
```
(Keep the following sentence "The record keeps those outcomes separate...".)

## 3. EDIT — Results, Uncertainty paragraph (main.tex ~L379)
**Anchor:** `\textbf{Uncertainty produces a comparator-specific warning.} All four steer-minus-prompt contrasts were negative under the frozen scorer ... while its all-generation bounds cross zero.`
**APPEND after that (before "The record therefore reports..."):**
```latex
A pre-registered, fully powered re-measurement of the Qwen--CAA cell with a retained, independently audited raw bundle confirms the negative comparator contrast at the floor ($N=813$, mean $-0.088$, 90\% TOST CI $[-0.109,-0.067]$, MDE $0.050$, coherent): steering is worse than the best prompt on this axis, not merely unresolved. {}% experiment_id powered-tost-A A4
```
(This is the **frozen no-exclusion scorer** contrast; it does NOT reopen the E-0013 complete-case/missingness question for the other three cells, which remain as reported.)

## 4. EDIT — tab:axis-actions (narrative table, main.tex ~L392) — allowed (not frozen artifact)
- **Skepticism "Next evaluation":** replace `Collect evidence with resolution near the declared floor.` →
  `Resolution near the floor obtained for the Qwen--CAA cell (bounded-equivalent within $\pm0.05$ at MDE $0.053$); the other three cells, ITI, and a passing latent positive control remain open.`
- **Deliberation "Next evaluation":** replace `Run a targeted confirmatory test rather than treating the profile as equivalence.` →
  `Both CAA cells now powered to $\pm0.05$ equivalence; ITI cells were already equivalent.`
- **Uncertainty "Next evaluation":** keep `Repair measurement and retain the comparator-specific warning.`; optionally append `A fully powered Qwen--CAA re-measurement confirms the comparator-negative direction.`
- **DO NOT** touch `tab:c2-delta-4cell` (frozen) or the 0/12 count.

## 5. EDIT — READ / C1 (main.tex ~L307, C1 exploratory caveat) — confirmatory upgrade
**Anchor:** the exploratory READ sentence describing single-run CAA facade.
**Soften the "one run / single-run exploratory" caveat** to reflect 3-seed replication:
```latex
The READ facade readout replicates across three seeds (all three tested axes hold in every seed) with a retained raw bundle, moving it from a single-run exploratory readout toward a seed-stable one; it remains CAA-style and diagnostic (not behavioral evidence).
```
(Verify the exact current wording at L302–L320 before editing; keep READ scoped as diagnostic-precondition, NOT actionability.)

## 6. EDIT — Discussion, three profiles (main.tex ~L536) & three-profiles framing (Results ~L340, Abstract ~L33)
- Results L340 "insufficient resolution for skepticism, mixed evidence for deliberation" → may soften "insufficient resolution" toward "bounded-equivalent (Qwen--CAA) with the rest resolution-limited" and "mixed evidence for deliberation" toward "equivalent-within-margin for the powered cells." Keep additive scope.
- **Abstract L33:** currently "skepticism is resolution-limited, deliberation is mixed, and all four uncertainty contrasts are negative...". CONSERVATIVE option (only if it reads cleanly and stays honest):
  "skepticism and deliberation are equivalent to the best prompt within the margin where powered, and all four uncertainty contrasts are negative under the frozen scorer." — **RISK:** abstract speaks grid-wide; the refinement powers only specific cells. Prefer to leave the abstract's axis summary mostly as-is and add at most a short clause "(now powered for the refined cells)"; do NOT overgeneralize one-cell/two-cell refinements to the whole grid.

## 7. Ledger / manifest updates (Writer or a bookkeeping subagent)
- experiment-registry rows for powered-tost-A A1–A4 + C1 (valid_for_paper flips to true **only after** this fold is applied and a claim-map row exists).
- claim-map.yaml: add evidence rows mapping the refined axis claims → powered-tost-A artifacts; note A3 MDE>δ caveat.
- evidence-ledger.md: add E-POWERED-TOST-A entry (SOUND, raw bundle committed, scope).
- Merge `feature/powered-tost-a` result artifacts into the writing branch (or cross-reference) so the paper's numbers are traceable on the same branch that builds the PDF.

## 8. Residual risks to re-check at application
1. Do NOT relabel the frozen 0/12 grid or imply any latent PASS. (No cell passed.)
2. A3 MDE>δ caveat must appear wherever A3 equivalence is stated. (BLOCKER if omitted.)
3. Scope: refinement powers specific CAA cells only; ITI + other-model cells stay as frozen.
4. Uncertainty A4 is the frozen no-exclusion scorer; does not resolve E-0013 missingness for other cells.
5. Abstract must not overgeneralize cell-level refinements to grid-wide claims.
6. Rebuild `.\docs\paper\build.ps1 -Clean`; check title/pages/undefined cites+refs; no manual edits to generated artifacts.
7. Independent claim/citation/lineage hostile audit of the writing diff after application.
