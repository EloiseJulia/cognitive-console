# PREREG — Robustness + Mechanism Arm (INDEPENDENT exploratory arm) — FINAL, pending human freeze

> Status: **FINAL draft, submitted for human §5 freeze/budget approval (2026-07-24).** NOT yet frozen. This is a NEW independent
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

## 2. Design (FINAL skeleton; PURE-MODEL, no humans)

- **Adjudication logic:** REUSE the frozen `adjudicate_c2b` decision rule VERBATIM (δ=0.05, Bonferroni
  item-cluster bootstrap, DEV/TEST split, coherence gate, three-tier). No change to §4 math.
- **Robustness matrix — LOCKED 2×2 (4 cells), each running the full frozen 3-axis adjudication:**

  | | Qwen2.5-7B-Instruct | Llama-3-8B-Instruct |
  |---|---|---|
  | **CAA** (baseline family, re-run) | cell-1 (reproduces E-0005) | cell-2 |
  | **ITI** (orthogonal family: per-head probe direction, inference-time intervention) | cell-3 | cell-4 |

  - Axes per cell: **all 3** (uncertainty [harm axis] + deliberation + skepticism) — generation is cheap
    (~29 min/cell), so no axis subsetting.
  - **Stretch (budget-permitting, NOT required for the BLOCKER):** a 3rd method column =
    **projected/whitened CAA** (covariance-respecting) as the direct H-M-alt "manifold-respecting rescue"
    test → would make it 3×2 = 6 cells.
  - **SAVE RAW TRANSCRIPTS every cell** (fixes R2-B2: last run's transcripts were wiped, so
    parser/extraction-artifact diagnostics need regeneration). Store per-item: prompt, steered/baseline
    generations, parsed answer+confidence, outcome.
- **Off-manifold diagnostic (H-M) — LOCKED:** on the SAME cached generations, at the steered layer L,
  compute per-item **whitened (Mahalanobis) distance** of the steered residual to the train-prompt
  activation distribution (mean+covariance estimated from the C1 extraction contrast set), plus
  activation-norm inflation ratio. Pre-registered test: **Spearman ρ between off-manifold distance and
  per-item Δoutcome (steer−baseline)** — primary on the **uncertainty** axis per cell, secondary pooled
  across cells.
- **Stronger-prompt-optimizer baseline (R1-F2 / R2-M1) — RECOMMENDED, in-scope:** one bounded iterative
  prompt optimizer on DEV only, fixed compute parity vs. the best-of-16 pool; freeze winner; re-adjudicate
  on existing TEST items → defends "prompt is a hard ceiling." Run on Qwen cell-1 at minimum.
- **C1 null-robustness appendix (R2-M3, cheap):** random-direction + prompt nulls, layer/norm sensitivity
  for the C1 ratio — recomputed from C1 extraction artifacts (regenerated in-cell if wiped).

## 3. Frozen success / kill criteria (set BEFORE running; NOT revised after results)

- **H-R (robustness of the non-transfer) — per-cell verdict uses the frozen three-tier, aggregated:**
  - **NON-TRANSFER GENERALIZED (strengthens C2, expected):** across the 4 required cells, **0 axes PASS in
    ≥3 of 4 cells** (i.e. the direction-consistent negative holds broadly) → C2 negative reported as robust
    across methods × models.
  - **SCOPE-NARROWED POSITIVE (secondary contribution):** **≥1 cell has ≥1 axis PASS** under the frozen
    rule → report as "controllability recoverable under {method/model}", NARROW C2 to the failing regime,
    add the positive as a SECONDARY finding. Does NOT touch E-0005.
  - **INCONCLUSIVE:** neither clean pattern (mixed, or ≥2 cells invalid) → report qualified, no strong
    generality claim; consider a power top-up (new decision).
- **H-M (off-manifold) — frozen threshold:** on the uncertainty axis, **Spearman ρ(off-manifold distance,
  −Δoutcome) ≥ 0.30 with 95% bootstrap CI excluding 0** in **≥3 of 4 cells** → C2-mech UPGRADED
  hypothesis→evidence. Else C2-mech remains an explicit hypothesis / Future Work (no mechanism credit).
- **Per-cell validity kill:** a cell that fails instrument validity checks (coherence-gate degeneracy on
  ALL α, generation stall, extraction collapse) is marked INVALID (not a result) and re-run or dropped —
  it does not count toward either verdict.

## 4. Budget estimate (for §5 human approval)

- **GPU (small, one box):** 4 required cells × (~29 min gen + ~4 min load) ≈ **~2.2 h generation**; +
  one-time Llama-3-8B download (~16 GB); + stronger-prompt-optimizer DEV runs (~20-30 min) + OOD diagnostic
  & C1 nulls (minutes, on cached). **Total ≈ 4-6 h on ONE rented 32 GB GPU box** (RTX 4080S/4090 class),
  ≈ **low tens of RMB**. Stretch 3rd method column adds ~1.2 h (2 more cells).
- **Engineering (AI credits — the real cost, PRE-GPU / no spend on hardware):** implement + INDEPENDENT-audit
  cycles for (i) **ITI** steering method, (ii) **Llama-3 provider** wiring (chat template + hook layers),
  (iii) **transcript-saving**, (iv) **off-manifold diagnostic**, (v) **stronger-prompt-optimizer**, (vi)
  **C1 null appendix**. Est. **~6-8 implement+audit subagent cycles**, rough **~1800-2600 AI credits**.
  (Optional projected/whitened-CAA adds ~1 cycle.)
- **Human §5 gates:** (a) FREEZE this prereg (this doc) — sign-off requested now; (b) GPU rental sign-off
  before the single GPU session; (c) venue policy already set (D-0035, IUI-first).

## 5. Sequencing (free before paid)
1. **Human freezes this prereg** (§4a) — the LOCKED 2×2 + OOD threshold above become immutable.
2. **Engineering (pure-CPU dev + tests + hostile audits)** for ITI / Llama provider / transcript-save /
   OOD diagnostic / prompt-optimizer / C1 nulls — NO GPU. (Can start in parallel with console + methodology
   asset, which do not depend on this freeze.)
3. **Smoke on 1.5B CPU** — batched-equivalence + transcript-save + OOD-diagnostic sanity — NO GPU.
4. **ONE rented GPU session** runs the whole 2×2 (+ optional stretch) + diagnostics — human GPU sign-off (§4b).
5. Manager verify + **hostile-audit each cell** → bank as E-0006.. ; update claim-ledger C2 / C2-mech.

## 6. Untouchable
E-0003, E-0005, prereg-c2b-adjudication.md, and `adjudicate_c2b` frozen §4 logic are FROZEN. This arm ADDS
cells/diagnostics; it never edits the above.
