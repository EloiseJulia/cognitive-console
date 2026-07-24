# Paper Reframe — "Reality-Check" main thread (DRAFT for human review)

> Status: **DRAFT proposal**, not frozen. Follows owner directive 2026-07-24 (disciplined reframe, option 4):
> bank C1 + the generalized C2 negative as CORE evidence, freeze the judgment, reframe rather than pivot-to-bland
> or chase a positive. Target venue: **CHI**. This doc drafts the restructured Claims / Contributions /
> Claim↔Evidence map for sign-off and keeps C2-mech in Future Work after the E-0007 valid null.

---

## 1. One-line thesis (reframed)

> **A cognitive axis can be *legible* in a model's representations yet *not controllable* through those same
> legible directions: reading the state is not the same as steering the behavior — and naive off-the-shelf
> latent steering can make calibration worse.** Across 2 steering methods × 2 model families, this gap
> becomes a design stance: a console that instruments the *boundary/limits* of legible control and helps
> non-experts *recalibrate trust*, rather than a "latent superpower slider."

This keeps the non-surjective backbone (Mishra et al., internal non-surjectivity) as *why the gap plausibly
exists internally*, but our empirical contribution is the **reality check on the behavioral side**: the
internal legibility does **not** cash out into a behavioral advantage over the best prompt.

---

## 2. Restructured Claims (map to claim-ledger)

### C1 — Representational Legibility Gap ("facade") is REAL  · RQ1 · CORE-empirical
- **Statement:** For metacognitive axes, the strongest human-readable prompt's mid-layer activation projects
  onto the CAA axis-direction *well below* the vector-only pole (and above a random-direction null), i.e. a
  prompt reaches only a fraction of the representable axis extent — a measurable *legibility/representation gap*.
- **Evidence:** **E-0003** (Qwen2.5-7B, 3/4 axes, CI<1, seed-stable) + E-0001/2 (1.5B corroboration).
- **Status:** **partially-supported / STRENGTHENED @7B (exploratory, single model family).**
- **Owed for confirmatory:** ≥2 model families (Llama-3 replication), protocol freeze.

### C2 — Legibility ≠ Behavioral Controllability  · RQ2 · **CORE reality-check (was C2b)**
- **Statement:** Steering along the *legible* CAA/ITI mean-difference-style direction does **not** push task
  behavior beyond the best-prompt ceiling on any tested axis under frozen, pre-registered adjudication,
  across **2 steering method families × 2 model families**: CAA/ITI × Qwen2.5-7B/Llama-3-8B. All four cells
  are **0/3 pass**; on calibration, steering is **actively harmful in all four cells** (uncertainty-axis CI
  excludes 0 negatively in every method×model cell).
- **Evidence:** **E-0005** (Qwen×CAA, audited **VALID_NEGATIVE**) + **E-0006** (audited
  **VALID_ARM_EVIDENCE**, arm_verdict=**NON_TRANSFER_GENERALIZED**; cell1 reproduces E-0005 byte-for-byte;
  uncertainty harms: CAA×Qwen −0.228, CAA×Llama −0.072, ITI×Qwen −0.103, ITI×Llama −0.084, all CIs < 0).
- **Status:** **SUPPORTED as a pre-registered negative / generalized reality-check claim across the tested
  2×2 grid.**
- **Framing rule (owner):** reported as an honest scoped negative; the judgment is frozen and will not be
  revised. Stronger/trained/optimized steering lives in **Limitations/Future Work**, NOT as grounds to re-open
  the frozen verdict.

### C2a — Internal Non-Surjectivity (theory backdrop)  · RQ2 · BACKGROUND
- **Statement:** Latent steering reaches internal residual states no bounded prompt reproduces (Mishra et al.
  2604.09839). Used as *motivation for why an internal gap plausibly exists*, not as our empirical result.
- **Status:** **parked / cited-as-background** (we did not run the internal-reproduction probe; C2 is about
  the behavioral non-transfer, which is our contribution).

### C3 — Console as a Boundary/Limit + Trust-Calibration Instrument  · RQ3 · DESIGN/HCI (Plan B elevated)
- **Statement:** Re-cast the interface from a "latent control slider" to an instrument that (a) *surfaces
  where* legible latent control fails or degrades behavior, and (b) helps non-experts *recalibrate trust* and
  attribute prompt↔latent conflict — i.e., a legibility/limits console, not a superpower panel.
- **Evidence:** formative + controlled user study — **NOT yet run; IRB/human-subjects = §5, human-gated.**
- **Status:** **proposed (design contribution).**

---

## 3. Contribution structure (Introduction bullets, reframed)

1. **A measurement** showing a *representational legibility gap* on metacognitive axes: the best readable
   prompt occupies only a fraction of the axis extent a latent vector spans (C1 / E-0003).
2. **A generalized reality check** — the headline: this legibility **does not transfer to behavioral control**
   across the tested 2×2 grid. Under frozen, independently-audited pre-registered adjudication, naive
   CAA/ITI steering fails to beat the best prompt on every axis in every method×model cell and *degrades*
   calibration in all four cells (C2 / E-0005 + E-0006). *Legibility ≠ controllability.*
3. **A reusable adjudication asset**: a frozen prompt-vs-latent behavioral comparison protocol that turns a
   negative result into auditable method infrastructure rather than post-hoc narrative (E-0005/E-0006; see
   methodology asset).
4. **A design reframe**: a console that instruments the *boundaries/limits* of legible control and supports
   *trust recalibration*, rather than promising latent superpowers (C3, study human-gated).

Honest scope line for Abstract/Intro: *steering is naive, bounded, off-the-shelf (CAA/ITI mean-difference-style); this is a reality-check under user-realistic bounded prompt effort, NOT a general impossibility theorem; cf. PSR "Steer Like the LLM" (ICML 2026), which shows trained/optimized steering can match prompting — our claim is explicitly about naive off-the-shelf steering.*

---

## 4. Claim ↔ Evidence map (bidirectional; gate: nothing enters Abstract/Contrib/Conclusion without this)

| Claim | Supported by | Verdict/strength | Main table/figure (planned) | valid_for_paper |
|---|---|---|---|---|
| C1 (legibility gap real) | E-0003 (7B 3/4), E-0001/2 (1.5B) | exploratory, CI<1 seed-stable | Fig: per-axis prompt-reach/pole-reach ratio + CI | exploratory (needs 2nd model) |
| C2 (legibility ≠ control) | E-0005 (Qwen×CAA VALID_NEGATIVE) + E-0006 (2×2 VALID_ARM_EVIDENCE, all cells 0/3) | pre-registered negative generalized across tested methods+models | Table: 4-cell Δ(steer−prompt) verdicts + Bonferroni CI per axis | YES (frozen scoped negative) |
| C2a (internal non-surj) | Mishra et al. 2604.09839 | cited background | — | background only |
| C3 (limits+trust console) | formative+controlled study | not yet run (IRB §5) | study figures (future) | NO (pending study) |

**Reverse map (every planned main artifact → which Claim):** Δ-table → C2; ratio-CI figure → C1;
study figures (future) → C3. No mechanism figure enters the main contribution set.

---

## 5. Future Work / mechanism status (NOT a contribution)

- **C2-mech / off-manifold distance account:** The targeted, pre-registered off-manifold test returned a
  **VALID NULL** (**E-0007**, audited VALID_NULL): whitened Mahalanobis distance vs per-item calibration harm
  had per-cell Spearman ρ ≈ {0.033, 0.039, -0.060, -0.223}, **0/4 pass**.
- **Consequence:** the distance-based off-manifold mechanism is **not evidenced** and must not appear as a
  contribution, core insight, or hypothesis in the contribution list. The calibration harm remains a robust
  empirical phenomenon (E-0006), but **the mechanism of the calibration harm is open**. Per D-0040, do not
  re-mine an alternative mechanism on the same data.
- **Permitted wording:** Limitations/Future Work may say that stronger, trained, optimized, or
  manifold-constrained steering could behave differently and would require a new independent preregistered
  test; it may not be used to revise E-0005/E-0006.

---

## 6. What is now FROZEN and must not be revised
- E-0003 (C1 @7B), **E-0005 (C2b qualified negative, KILL_PLAN_D)**, **E-0006 (2×2 NON_TRANSFER_GENERALIZED)**,
  and **E-0007 (off-manifold VALID_NULL)** — banked, judgment frozen.
- prereg-c2b-adjudication.md, prereg-robustness-mechanism-arm.md, and prereg-ood-capture.md — frozen
  protocols; post-hoc changes forbidden.
- Any method-improvement or mechanism exploration = new independent prereg, never edits to the above.
