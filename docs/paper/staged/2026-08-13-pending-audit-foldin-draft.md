# STAGED FOLD-IN DRAFT — PENDING AUDIT, NOT BLESSED

> **STATUS: DO NOT LAND. DO NOT `\input`. DO NOT MERGE INTO `main.tex`.**
> This file is a *staged* draft of proposed edits for two experiments. Every number
> below is currently `valid_for_paper=false` and has **not** cleared the required
> independent correctness audit. Nothing here may enter `docs/paper/main.tex`, the
> frozen `tables/c2-delta-4cell.tex`, the frozen 0/12 grid, or the abstract until the
> **Landing Preconditions** (below) are all satisfied. Author: Writer session; wording
> converged from a 4-family advisory panel (Claude Opus 4.8 / GPT-5.6 / Gemini 3.1 Pro /
> Grok 4.5). This doc is prose only; it cannot compile into the paper.

---

## 0. What these two results are (verified numbers, unverified lineage)

**A — Calibrated ITI × TruthfulQA positive-control attempt.**
- experiment_id `iti-truthfulqa-calibrated-positive-control-20260812`, code `32195f6`, Llama-3-8B, seed 20260811.
- α-recalibration (ratio grid {0.025..0.125} bounding injected per-layer norm to a fraction of ‖h‖ + coherence-aware DEV selection) fixed an earlier incoherent collapse.
- `coherence_ok=True`; **mean(ITI − baseline) = +0.0293 < required_delta 0.05** → `status=INVALID_SETUP`, `valid_for_paper=false`, **TEST not accessed**. Folds +0.0195, +0.0390.
- Meaning: a calibrated, coherent, in-domain, literature-standard latent method on its **own home benchmark** clears only +0.029 → **still NO passing latent behavioral positive control.**
- **Comparator caveat (must state):** +0.029 is **ITI − no-steer baseline on the home task**, NOT steer-vs-bounded-prompt. Do not conflate estimands.

**B — resolution-refinement TEST.** experiment_id `c2b-resolution-caa-qwen-test-20260812`.
- **CAA × Qwen2.5-7B ONLY** (single cell), two axes. `additive_to_frozen_0_of_12=True`; `must_not_overwrite=E-0005/6/11`.
- skepticism: steer−prompt **−0.01347**, 98.33% CI **[−0.0482, +0.0222]**, n=505, coherent, δ=0.05 → **entire CI within ±0.05 floor** (sub-floor bounded estimate).
- uncertainty_awareness: **−0.09024**, 98.33% CI **[−0.1237, −0.0582]**, n=813, coherent → comparator-negative, CI excludes zero. On the **frozen no-exclusion scorer** (missing confidence imputed).
- `scientific_status=PENDING_HOSTILE_RESULT_AUDIT`, `valid_for_paper=False`.

## 1. Landing Preconditions (ALL must hold before any edit below is applied)

1. **Lineage committed.** A's calibrated run registered in the ITI experiment-registry; B's TEST artifact + registry row committed (data_hash, code_commit, raw_metrics). *(In progress via the lineage-fix subagent; keep `valid_for_paper=false`.)*
2. **Independent correctness audit PASS.** B (confirmatory TEST) needs a full independent adversarial correctness audit (reproduce stats from raw artifacts; verify n, CI method/level, item-pool provenance vs frozen pools, scorer identity, no overwrite of E-0005/6/11). A (DEV, supports no Claim) needs only a lighter lineage/soundness check (coherence gate; confirm +0.029 is ITI−baseline; confirm calibration was coherence-selected, not outcome-tuned).
3. **Manager exploratory→confirmatory + claim gate.** The skepticism framing shift and any use of A touch core-claim scope → Manager/human sign-off before Claim-freeze.
4. **Numbers regenerable, not hand-copied.** Every landed value must come from a committed script/artifact, not from this doc.

## 2. Wording decisions locked by the panel (rationale)

- **Say "sub-floor bounded estimate", NOT "powered null".** The prereg (`frozen_params`) only defines the QUALIFY rule (CI excludes 0 ∧ mean ≥ δ ∧ coherence); **no equivalence/TOST was pre-registered**. So "CI within ±0.05" = a bounded sub-floor estimate, not a formal null/equivalence claim. (GPT-5.6; I concur.)
- **Scope = CAA × Qwen ONLY.** Do NOT rewrite the grid-wide skepticism profile. Present as "frozen grid (historical) vs CAA×Qwen additive refinement". (Grok; confirmed from experiment_id.)
- **Cherry-pick defense (must appear):** state a priori that only the CAA×Qwen cell was authorized for refinement and **both** axes are reported regardless of sign.
- **Additive, never overwrite.** Frozen 0/12 grid and E-0005/6/11 unchanged; uncertainty companion does not close the three unrechecked cells and does not generalize E-0013.
- **A is home-task context only.** Never "assay validated", never "standard ITI fails", never a table row or Claim. TruthfulQA truthfulness on Llama-3-8B is a different construct from the three behavioral axes; it cannot validate them.
- **State achieved resolution for skepticism** (MDE ≈ 0.05-scale, exact value TBD-by-audit); do not imply the effect is exactly at 0.05.

---

## 3. STAGED EDIT A — one sentence in Assay Validity (ITI)

**Anchor:** `\subsection{Assay Validity and Statistical Resolution}`, immediately after the sentence ending "...direction construction, scale, hook/layer selection, normalization, generation, outcome, or scoring." (currently `main.tex` ~L579).

**INSERT (staged):**
```latex
As a further check that the eligibility floor is not simply unreachable, a coherence-passing, calibrated ITI run on its own home benchmark (TruthfulQA, Llama-3-8B) improved truthfulness over its no-steer baseline by only $+0.029$ (DEV; folds $+0.020$, $+0.039$), below the same $0.05$ floor, with the held-out test left unaccessed per preregistration. This is a coherent in-domain negative on the method's home task, not a validated positive control, and it does not license any claim about the behavioral assays.
```
**Caveats carried:** DEV-only, `INVALID_SETUP`, comparator = ITI−baseline (home task), TEST not accessed. If a reviewer could read it as assay validation, CUT it.

---

## 4. STAGED EDIT B1 — Results, skepticism (additive companion)

**Anchor:** the `\textbf{Skepticism directs the next evaluation toward resolution.}` paragraph (`main.tex` ~L394–396). **KEEP** the existing frozen-grid sentence (MDEs 0.188/0.268/0.225/0.279). **APPEND** a companion:

**APPEND (staged):**
```latex
A prospectively frozen, higher-resolution TEST-once re-measurement of the CAA--Qwen2.5-7B cell (additive to the frozen grid, which is unchanged; only this cell was authorized for refinement and both axes are reported regardless of sign) sharpens skepticism: the steer-minus-prompt contrast is a bounded sub-floor estimate whose entire 98.33\% interval lies within the registered $\pm0.05$ floor (mean $-0.0135$, CI $[-0.048, +0.022]$, $n=505$, coherent). At the achieved resolution the effect, if any, is bounded inside the floor rather than merely undetected; the axis remains a no-pass and is not upgraded.
```

## 5. STAGED EDIT B2 — Results, uncertainty (additive companion)

**Anchor:** the `\textbf{Uncertainty produces a comparator-specific warning.}` paragraph (`main.tex` ~L403–405). **KEEP** existing frozen text (four negative contrasts; E-0013 complete-case −0.337, all-generation bounds cross zero). **APPEND:**

**APPEND (staged):**
```latex
The same CAA--Qwen refinement returns a comparator-negative estimate whose interval excludes zero (mean $-0.0902$, CI $[-0.124, -0.058]$, $n=813$, coherent) on the frozen no-exclusion scorer. Because that scorer imputes missing confidences rather than dropping them, this estimate is not subject to the complete-case missingness confound that qualified the E-0013 recheck; it corroborates the frozen comparator-negative direction additively, without replacing the frozen cells and without closing the three unrechecked cells.
```

## 6. STAGED EDIT B3 — `tab:axis-actions` rows (NOT the frozen `tab:c2-delta-4cell`)

The `\label{tab:axis-actions}` table is a NARRATIVE table in `main.tex` (not a generated/frozen artifact), so editing it is allowed *once B lands*.

- **Skepticism "Next evaluation" cell** — replace `Collect evidence with resolution near the declared floor.` with:
  `Resolution near the floor obtained for the CAA--Qwen cell (bounded within $\pm0.05$); remaining: the other three cells, deliberation, and a passing latent positive control.`
- **Uncertainty "Next evaluation" cell** — keep `Repair measurement and retain the comparator-specific warning.`; optionally append `A frozen-scorer refinement of the CAA--Qwen cell corroborates the direction additively.`
- **Do NOT touch** `tab:c2-delta-4cell` (frozen) or the 0/12 count.

## 7. STAGED EDIT B4 — Discussion three-profiles sentence

**Anchor:** `main.tex` L542: "The three evidence profiles lead to different evaluation work. Skepticism requests more resolution; deliberation calls for a better-targeted test; uncertainty calls for measurement repair and a comparator-specific warning."

**REPLACE (staged):**
```latex
The three evidence profiles lead to different evaluation work. For skepticism, a higher-resolution refinement of the CAA--Qwen cell now bounds the contrast within the floor; deliberation calls for a better-targeted test; and uncertainty calls for measurement repair and a comparator-specific warning, additively corroborated on the refined cell.
```

## 8. STAGED EDIT B5 — Abstract (OPTIONAL, only if space and only after B lands)

**Anchor:** abstract sentence "The contract preserves three evidence profiles: skepticism requires greater resolution, deliberation is mixed, and uncertainty favors the comparator under the frozen scorer while its all-generation interpretation remains open."

**CONSERVATIVE staged option** (scoped to the refined cell; do NOT overclaim grid-wide):
```latex
The contract preserves three evidence profiles: skepticism is bounded within the floor where refined (CAA--Qwen), deliberation is mixed, and uncertainty favors the comparator under the frozen scorer while its all-generation interpretation remains open.
```
**Risk:** the abstract speaks grid-wide; a one-cell refinement in the abstract can read as over-generalization. Prefer leaving the abstract unchanged if space is tight; land B3/B4 first.

---

## 9. Residual risks to re-check at landing (ranked)

1. Using B in main text while `valid_for_paper=False` / pre-audit — confirmatory laundering. **Blocked by §1.**
2. Global profile rewrite from one cell (cherry-pick). **Mitigated: CAA×Qwen scope + both-axes-reported stated in B1.**
3. A read as pseudo-positive-control or "standard method fails" / assay validation. **Mitigated: §3 wording + CUT rule.**
4. Overwriting/re-labeling frozen 0/12 or E-0005/6/11. **Forbidden; B edits are additive/narrative only.**
5. "Sub-floor" without stating achieved MDE. **B1 says "at the achieved resolution"; audit to fill exact MDE.**
6. Uncertainty companion misused to dismiss E-0013 missingness for other cells — different estimands. **B2 scopes it to the one cell.**
7. A's comparator estimand (baseline vs prompt) mismatch. **§3 fixes to ITI−baseline; audit to confirm.**

## 10. Process order (who does what)

1. lineage-fix subagent commits A + B lineage (in progress; `valid_for_paper=false`).
2. Independent correctness audit: B full/hostile; A lighter soundness. (Manager-orchestrated.)
3. Manager exploratory→confirmatory + claim-scope gate.
4. Writer applies §3–§8 to `main.tex`, rebuilds (`build.ps1 -Clean`), records title/pages/hash/undefined-cites, updates claim-map/evidence-ledger.
5. Independent claim/citation/lineage hostile audit of the writing diff.
