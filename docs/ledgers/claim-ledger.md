# Claim Ledger

> Every Claim entering Abstract / Introduction-Contributions / Conclusion MUST map here with sufficient
> evidence. Every main table/figure MUST state which Claims it supports. Contradicting evidence is never
> deleted — only explained, scope-narrowed, or the Claim withdrawn. (AI-Instruction Part I §4.2)

Status values: proposed | partially-supported | supported | contradicted | withdrawn

---

## C1 — Representational Legibility Gap / Semantic Facade (RQ1) — CORE-empirical
- **Statement:** In the two-model C1 readout, the cross-model-invariant facade claim is restricted to
  **deliberation + skepticism**: the strongest human-readable prompt's mid-layer activation projects onto
  the CAA vector direction far below vector-only and above a random-direction null. **Uncertainty and focus
  are explicitly model-dependent, not invariant** (uncertainty: Qwen 0.713 hold vs Llama 1.000 no-facade;
  focus: Llama 0.471 hold vs Qwen 2.844 overshoot).
- **Scope:** Llama-3-8B-Instruct, Qwen2.5-7B-Instruct; axes = Deliberation/Skepticism/Uncertainty/Focus.
- **Type:** empirical regularity (diagnostic → confirmatory after protocol freeze)
- **Status:** **partially-supported / 2-MODEL support at 3/4 aggregate, EXPLORATORY, with per-axis
  heterogeneity.** E-0003 (Qwen2.5-7B): 3/4 hold (deliberation 0.583, skepticism 0.548, uncertainty 0.713;
  focus overshoot/no facade). **E-0008 (Llama-3-8B, frozen protocol, audited): also 3/4 hold** (deliberation
  0.872, skepticism 0.628, focus 0.471; **uncertainty 1.000 does NOT hold**). **HONEST CAVEAT:** facade is
  MODEL-INVARIANT only on **deliberation + skepticism** (both models); uncertainty and focus FLIP across
  models. "3/4" replicates in magnitude, NOT in axis composition — NOT a clean identical replication. Both
  EXPLORATORY, valid_for_paper=false (single run per model). Corroborated at 1.5B (E-0001/2).
- **Required evidence:** projection/cosine of strongest-prompt vs CAA vector vs random null; blind-eval.
- **Known limits:** projection is a linear proxy; axis may be non-linear/multi-mechanism.
- **Paper location:** Contribution 1 (measurement); ratio-CI figure. See reframe-2026-07-24-reality-check.md.

## C2 — Legibility ≠ Behavioral Controllability (RQ2, CORE reality-check; reframed from C2b)
- **Statement:** Steering along the *legible* CAA/ITI direction does NOT push task behavior beyond the
  best-prompt ceiling on any tested axis under a frozen, pre-registered adjudication, across TWO steering
  method families (CAA, ITI) and TWO model families (Qwen2.5-7B, Llama-3-8B); on calibration it is
  consistently HARMFUL (uncertainty axis negative, CI excludes 0, in all 4 method×model cells).
- **Scope:** {CAA,ITI}×{Qwen2.5-7B, Llama-3-8B}; frozen instrument (prereg-c2b-adjudication.md +
  prereg-robustness-mechanism-arm.md). Single-family caveat REMOVED (now 2 methods × 2 models).
  **Not an impossibility theorem for activation steering in general; scoped to bounded prompt effort vs
  naive/off-the-shelf CAA/ITI. PSR robustness arm (E-0009) is exploratory only; it pre-empts the
  "method too weak" attack but does not upgrade the frozen headline.**
- **Type:** pre-registered empirical (qualified NEGATIVE, GENERALIZED; reported as core reality-check claim)
- **Status:** **SUPPORTED as a pre-registered negative, GENERALIZED across methods+models, and now confirmed
  robust across 5 pre-registered seeds (D-0055).** Core evidence: **E-0005** (Qwen/CAA, VALID_NEGATIVE) +
  **E-0006** (2×2 arm, VALID_ARM_EVIDENCE, arm_verdict=NON_TRANSFER_GENERALIZED, all 4 cells 0/3).
  **E-0011** (multi-seed robustness, valid_for_paper=true per D-0055): 5/5 seeds NON_TRANSFER_GENERALIZED;
  uncertainty CI_hi<0 in all 4 cells × all 5 seeds; any_true_pass=false → **DROP_SINGLE_SEED_CAVEAT
  enacted (D-0055); single-seed caveat RETIRED.** cell1 reproduces E-0005 byte-for-byte. Judgment FROZEN.
  **Disclosure:** E-0011 uses the same item pool as E-0006 across seeds (GSM8K test / TruthfulQA validation,
  first-N deterministic slice); only DEV/TEST split membership varies by seed (NOT independent item draws).
  **This closes the unanimous critic BLOCKER (external validity / single-method×single-model).**
- **Falsified if:** a manifold-respecting / stronger latent intervention beats best-prompt behavior — tested
  ONLY via a SEPARATE independent pre-registered arm (never edits E-0005/E-0006).
- **Robustness update (EXPLORATORY, does NOT change the frozen headline):** the SEPARATE pre-registered PSR
  latent-recovery arm (E-0009, prereg-latent-recovery-arm Option 1) ran on Qwen2.5-7B: a faithful DEV-optimized
  PSR-style steering method (the direct answer to PSR / open-risk #9) ALSO returned KILL_PLAN_D (all 3 axes fail;
  uncertainty significantly HURTS). Audited VALID_NEGATIVE. This suggests the negative is robust to METHOD
  STRENGTH, not merely to naive CAA/ITI — but it is EXPLORATORY (single model, single seed, valid_for_paper=false)
  and pre-empts the "method too weak" attack; it does NOT overwrite or upgrade the frozen E-0005/E-0006 headline.
- **Paper location:** Contribution 2 (headline); Δ-table (4 cells) + per-cell verdicts.

## C2-mech — Off-manifold degradation (calibration harm) — **HYPOTHESIS / FUTURE WORK (NOT supported by direct test)** · RQ2
- **Statement (hypothesis):** the calibration worsening under steering (uncertainty axis, negative in all 4
  cells) *might* be explained by steering pushing activations off the natural data manifold.
- **Type:** interpretive hypothesis — **DIRECTLY TESTED and NOT SUPPORTED.**
- **Status:** **DEMOTED to explicit hypothesis / Future Work (E-0007, D-0040).** The pre-registered off-manifold
  test (whitened Mahalanobis distance vs per-item calibration harm, frozen prereg-ood-capture) returned a
  VALID NULL: per-cell Spearman ρ ≈ {0.033, 0.039, -0.060, -0.223}, 0/4 pass. Audited VALID_NULL. Per owner's
  honest-fail rule, we do NOT re-mine an alternative mechanism on the same data. The *distance-based*
  off-manifold account is not evidenced; the calibration harm is reported as a robust empirical phenomenon
  (E-0006) whose mechanism is open.
- **Evidence:** E-0007 (valid null). Does NOT enter Contributions as a mechanism claim; appears in
  Limitations/Future Work only.
- **Paper location:** Future Work (mechanism of the calibration harm is an open question).

## C2a — Internal-State Non-Surjectivity (RQ2, theory backdrop) — BACKGROUND
- **Statement:** Latent steering reaches internal residual states that no prompt in a bounded search
  reproduces. **Basis:** Mishra et al. (2604.09839).
- **Type:** theory-supported motivation (NOT our empirical result)
- **Status:** **parked / cited-as-background.** We did not run the internal-reproduction probe; our
  empirical contribution (C2) is the behavioral non-transfer, not internal non-surjectivity.
- **Falsified if:** a bounded prompt search reproduces the steered internal state.

## C3 — Console as Boundary/Limit + Trust-Calibration Instrument (RQ3, DESIGN/HCI — Plan B elevated)
- **Statement:** Re-cast the interface from a "latent control slider" to an instrument that surfaces WHERE
  legible latent control fails/degrades behavior and helps non-experts recalibrate trust and attribute
  prompt↔latent conflict.
- **Scope:** formative + 4-condition controlled study; open white-box models.
- **Type:** design/HCI contribution (empirical user study)
- **Status:** **proposed.** Evidence = formative + controlled study — NOT yet run; IRB/human-subjects = §5,
  human-gated.
- **Known limits:** cross-model automatic re-mapping is the hardest engineering piece.
- **Paper location:** Contribution 4 (design).
