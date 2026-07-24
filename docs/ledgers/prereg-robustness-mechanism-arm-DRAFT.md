# PREREG DRAFT — Robustness + Mechanism Arm (INDEPENDENT exploratory arm)

> Status: **DRAFT for human budget/go-no-go approval.** NOT frozen. This is a NEW independent
> pre-registration per owner directive 2026-07-24; it does NOT touch the frozen records E-0003 / E-0005 /
> prereg-c2b-adjudication.md. Purpose: harden (or overturn) the C2 behavioral-non-transfer negative and
> upgrade the C2-mech off-manifold hypothesis, both PURE-MODEL / no humans. Shaped by the 3 critic reviews
> (R1/R2/R3, 2026-07-24) whose unanimous BLOCKER is external validity (single method × single model).
>
> **Freeze rule:** success/kill criteria below are frozen BEFORE any run; not revised after seeing results.
> Asymmetric value (owner): all-cell failure → the C2 negative becomes *general* (not "CAA-on-Qwen weakness");
> any-cell success → a *scope-narrowed positive* (controllability recoverable under a stronger/constrained
> method) that becomes a SECONDARY contribution — never overwrites E-0005.

---

## 1. Mechanism hypotheses (frozen)

- **H-R (Robustness / non-transfer generality):** The behavioral non-transfer (steer along a *legible*
  direction does NOT beat the best prompt) holds across steering-method families and model families, not
  just CAA@Qwen2.5-7B.
- **H-M (Off-manifold):** The calibration harm (and, more generally, failure to help) is *monotonically
  associated with how far the steered activation is pushed off the natural data manifold*: cells/items with
  larger off-manifold displacement show worse Δoutcome. A linearly-legible direction is not a
  manifold-respecting control coordinate.
- **H-M-alt (rescue):** A *manifold-respecting / stronger* intervention (e.g. projected/whitened steering,
  layer-scheduled, or RepE-style) recovers behavioral gain on ≥1 axis where naive CAA failed → would
  *narrow* (not overturn) C2.

## 2. Design (frozen skeleton; PURE-MODEL, no humans)

- **Adjudication logic:** REUSE the frozen `adjudicate_c2b` decision rule VERBATIM (δ=0.05, Bonferroni
  item-cluster bootstrap, DEV/TEST split, coherence gate, three-tier). No change to §4 math.
- **Robustness matrix (≥2×2, target 3×2):**
  - Steering methods: **CAA (baseline, re-run) + ≥1 orthogonal family (ITI or RepE or projected/whitened
    CAA)**; stretch: a third (ActAdd/layer-scheduled).
  - Model families: **Qwen2.5-7B-Instruct + ≥1 non-Qwen (Llama-3-8B-Instruct or Mistral-7B)**.
  - Axes: at least **uncertainty (the harm axis) + one more**; full 3 axes if budget allows.
  - Each cell runs the SAME frozen adjudication; **SAVE RAW TRANSCRIPTS this time** (fixes R2-B2 —
    transcripts were wiped last run, so parser-artifact diagnostics need re-generation).
- **Off-manifold diagnostic (H-M):** on the SAME cached generations, compute per-item activation
  displacement proxies (e.g. Mahalanobis/whitened distance to the layer's train-activation distribution,
  local-linearity/norm inflation) at the steered layer; test correlation with per-item Δoutcome
  (esp. uncertainty). Pre-register the correlation sign/threshold.
- **Stronger-prompt-optimizer baseline (R1-F2 / R2-M1):** one bounded iterative prompt optimizer on DEV
  only under fixed compute parity, freeze winner, re-adjudicate on existing TEST items — to defend the
  "prompt is a hard ceiling" fairness. (Optional but recommended.)
- **C1 null-robustness appendix (R2-M3, cheap):** random-direction + prompt nulls, layer/norm sensitivity
  for C1 ratio — from existing/recomputable C1 artifacts.

## 3. Frozen success / kill criteria (set BEFORE running)

- **H-R verdict (per the frozen three-tier, applied per cell):**
  - **NON-TRANSFER GENERALIZED (strengthens C2):** 0 axes pass in **≥ (all but one)** cells → C2 negative
    reported as robust across methods×models. *This is the expected + paper-strengthening outcome.*
  - **SCOPE-NARROWED POSITIVE (secondary contribution):** ≥1 cell shows ≥1 axis PASS (frozen rule) →
    report as "controllability recoverable under {method/constraint}", narrow C2, add as secondary finding.
    Does NOT touch E-0005.
  - **INCONCLUSIVE:** mixed/underpowered → report qualified, no strong generality claim.
- **H-M verdict:** pre-register that off-manifold distance correlates with Δoutcome degradation at
  |ρ| ≥ [TBD, e.g. 0.3] with CI excluding 0 (pooled across items) → C2-mech upgraded hypothesis→evidence;
  else C2-mech stays explicit hypothesis / Future Work.
- **Kill:** if the instrument fails validity checks (as before) the cell is invalid, not a result.

## 4. Budget estimate (for human approval)

- **GPU (small):** ~4 cells (2 methods × 2 models) × ~11,365 gens × ~29 min ≈ **~2–3 h generation** +
  model loads + one-time Llama/Mistral download (~16 GB). Realistic **~5–6 h on one rented 32 GB GPU box**
  (≈ low tens of RMB). Off-manifold diagnostic + C1 nulls = minutes (on cached). Stronger-prompt-optimizer
  DEV runs add modest generation.
- **Engineering (AI credits, the real cost):** implement + INDEPENDENT-audit cycles for: (i) ITI/RepE (or
  projected-CAA) steering method, (ii) Llama-3/Mistral provider wiring, (iii) transcript-saving, (iv)
  off-manifold diagnostic, (v) stronger-prompt-optimizer, (vi) C1 null appendix. Est. **~5–8 implement+audit
  subagent cycles** (each behind a hostile audit before merge). Rough **~1500–2500 AI credits**.
- **Human gates:** (a) freeze THIS prereg's criteria before running; (b) GPU rental sign-off; (c) any venue
  change already covered by D-0035.

## 5. Sequencing (free before paid)
1. Freeze this prereg (fill the [TBD] threshold + final matrix) — human sign-off.
2. Engineering (pure-CPU dev + tests + audits) for the new methods/models/diagnostics — no GPU.
3. Smoke on 1.5B CPU (batched-equivalence + transcript save) — no GPU.
4. ONE rented GPU session runs the whole matrix + diagnostics — human GPU sign-off.
5. Manager verify + hostile-audit each cell's result; bank as E-0006.. ; update claim-ledger C2/C2-mech.

## 6. Untouchable
E-0003, E-0005, prereg-c2b-adjudication.md, and `adjudicate_c2b` frozen §4 logic are FROZEN. This arm ADDS
cells/diagnostics; it never edits the above.
