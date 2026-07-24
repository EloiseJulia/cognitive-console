# Paper Reframe — "Reality-Check" main thread (DRAFT for human review)

> Status: **DRAFT proposal**, not frozen. Follows owner directive 2026-07-24 (disciplined reframe, option 4):
> bank C1 + the C2b qualified negative as CORE evidence, freeze the judgment, reframe rather than pivot-to-bland
> or chase a positive. Target venue: **CHI**. This doc drafts the restructured Claims / Contributions /
> Claim↔Evidence map for sign-off. The optional new independent pre-registered exploratory arm (§5 of this doc)
> is a SEPARATE budget decision.

---

## 1. One-line thesis (reframed)

> **A cognitive axis can be *legible* in a model's representations yet *not controllable* through those same
> legible directions: reading the state is not the same as steering the behavior — and naive latent steering
> can make calibration worse.** We turn this gap into a design stance: a console that instruments the
> *boundary/limits* of legible control and helps non-experts *recalibrate trust*, rather than a "latent
> superpower slider."

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
- **Statement:** Steering along the *legible* CAA direction does **not** push task behavior beyond the
  best-prompt ceiling on any tested axis under a frozen, pre-registered adjudication; on calibration it is
  **actively harmful**. Concretely (frozen instrument, N=60/60/80, k=5, Bonferroni item-cluster bootstrap):
  Δ(steer−prompt) = deliberation +0.015 [-0.040,+0.070], skepticism −0.080 [-0.225,+0.045],
  uncertainty **−0.228 [-0.370,-0.092]** → **0/3 pass**.
- **Evidence:** **E-0005** (audited **VALID_NEGATIVE**, KILL_PLAN_D verdict, exp c2b-adj-deac6326-0001).
- **Status:** **SUPPORTED as a (pre-registered) negative / reality-check claim.**
- **Framing rule (owner):** reported as an honest qualified negative; the judgment is frozen and will not be
  revised. "Our steering method may be too weak" lives in **Limitations/Future Work**, NOT as grounds to
  re-open the frozen verdict.

### C2-mech — Off-manifold degradation (calibration harm) — INSIGHT / mechanism HYPOTHESIS · RQ2
- **Statement (hypothesis):** The calibration *worsening* under steering (uncertainty −0.228) is consistent
  with the intervention pushing activations *off the natural data manifold* along a direction that is
  linearly legible but not a valid behavioral control coordinate — legibility of a direction does not imply
  it is a manifold-respecting lever.
- **Evidence:** currently **inferential** from E-0005 (behavioral), NOT mechanistically proven.
- **Status:** **proposed (core insight framed as hypothesis).** A targeted diagnostic (activation-norm /
  manifold-distance vs. Δoutcome) is the natural cheap confirmation — candidate for the new exploratory arm
  (§5) or Future Work.

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
2. **A reality check** — the headline: this legibility **does not transfer to behavioral control**. Under a
   frozen, independently-audited pre-registered adjudication, latent steering along the legible direction
   fails to beat the best prompt on every axis and *degrades* calibration (C2 / E-0005). *Legibility ≠
   controllability.*
3. **An insight**: the calibration harm is consistent with an *off-manifold* account of why a linearly
   legible direction is not a valid control coordinate (C2-mech, framed as hypothesis).
4. **A design reframe**: a console that instruments the *boundaries/limits* of legible control and supports
   *trust recalibration*, rather than promising latent superpowers (C3, study human-gated).

Honest scope line for Abstract/Intro: *single open-model family (Qwen2.5), one steering method family (CAA);
we claim a reality check + design stance, not a general impossibility theorem.*

---

## 4. Claim ↔ Evidence map (bidirectional; gate: nothing enters Abstract/Contrib/Conclusion without this)

| Claim | Supported by | Verdict/strength | Main table/figure (planned) | valid_for_paper |
|---|---|---|---|---|
| C1 (legibility gap real) | E-0003 (7B 3/4), E-0001/2 (1.5B) | exploratory, CI<1 seed-stable | Fig: per-axis prompt-reach/pole-reach ratio + CI | exploratory (needs 2nd model) |
| C2 (legibility ≠ control) | E-0005 (audited VALID_NEGATIVE, 0/3) | pre-registered qualified negative | Table: Δ(steer−prompt) + Bonferroni CI per axis | YES (frozen negative) |
| C2-mech (off-manifold) | inferential from E-0005 | hypothesis | Fig (future): manifold-dist vs Δoutcome | NO (hypothesis) |
| C2a (internal non-surj) | Mishra et al. 2604.09839 | cited background | — | background only |
| C3 (limits+trust console) | formative+controlled study | not yet run (IRB §5) | study figures (future) | NO (pending study) |

**Reverse map (every planned main artifact → which Claim):** Δ-table → C2; ratio-CI figure → C1;
manifold figure (future) → C2-mech; study figures (future) → C3.

---

## 5. OPTIONAL new independent pre-registered exploratory arm (SEPARATE budget decision — human-gated)

> Per owner: this must be an INDEPENDENT prereg with its own mechanism hypothesis + success/kill + budget,
> must NOT touch the frozen C2b record (E-0005), and has *asymmetric* paper value. Drafted separately for a
> go/no-go; NOT part of the frozen reality-check spine above. See companion draft:
> `docs/ledgers/prereg-latent-recovery-arm-DRAFT.md` (to be written on request).
>
> - **Mechanism hypothesis:** a *manifold-constrained* / *layer-targeted* / *stronger-but-projected* latent
>   intervention can recover behavioral gain on ≥1 axis where naive CAA failed (esp. reverse the uncertainty
>   harm), because the failure is off-manifold, not intrinsic non-reachability.
> - **Asymmetric value:** all-axes failure → *strengthens & generalizes* the C2 negative (not just "our method
>   was weak"); some-axis success → a *scope-narrowed positive* (controllability recoverable under manifold
>   constraints) that becomes a secondary contribution — never overwrites E-0005.
> - **Needs:** frozen success/kill criteria + GPU budget estimate BEFORE running (owner sign-off).

---

## 6. What is now FROZEN and must not be revised
- E-0003 (C1 @7B) and **E-0005 (C2b qualified negative, KILL_PLAN_D)** — banked, judgment frozen.
- prereg-c2b-adjudication.md — the frozen protocol; post-hoc changes forbidden.
- Any method-improvement exploration = new independent prereg (§5), never edits to the above.
