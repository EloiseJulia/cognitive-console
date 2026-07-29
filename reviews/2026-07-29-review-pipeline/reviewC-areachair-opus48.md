# Meta-Review — Associate Chair (Area Chair) Decision

**Paper:** *Legible Need Not Be Controllable: A Frozen Reality Check for Prompt-vs-Latent Behavioral Control in LLMs*

**Venue:** ACM CHI (sub-25% acceptance)

**Reviewer pool considered:** Reviewer A (senior HCI, 10-task review, including its three simulated sub-reviewers A/B/C in Task 6) and Reviewer B (reject-focused methodological skeptic, confidence 5/5). I also read the submitted source myself (`main.tex`, all `tables/*.tex`, `figures/`, `references.bib`) before adjudicating.

---

## DECISION: **Weak Reject**

This is a reject-side decision *for this CHI cycle*. The paper is well above clear-reject quality — it is one of the more disciplined, honest, and self-aware submissions I have handled — but as submitted it does not clear the human-centered contribution bar at CHI, and its central empirical framing over-reads a non-detection as demonstrated non-transfer. Neither problem is fixable within a rebuttal. I am deliberately **not** recording a full Reject, because (a) two of the reviewers' "critical/fatal" charges (novelty collapse; "it's all an underpowered null") are partly overstated and unfair to the paper's honest scoping, and (b) most of the remaining defects are fixable framing/reporting issues rather than validity failures. A future version with even a modest human-subjects evaluation would be a genuinely strong CHI paper.

---

## 1. What the paper actually is

A frozen, pre-registered, multiplicity-controlled behavioral adjudication on two 7–8B instruction models (Qwen2.5-7B, Llama-3-8B) and two off-the-shelf steering methods (CAA, ITI). Findings:

- **C1 (exploratory):** a representational "facade ratio" is legible on some metacognitive axes; two-model support on deliberation/skepticism, model-dependent on uncertainty/focus (n=1 run per model).
- **C2 (frozen):** across the full 2×2 grid, naive latent steering fails the pre-registered superiority gate on every adjudicated axis; the uncertainty axis shows a negative steer-minus-prompt effect whose CI excludes zero in all four cells (calibration harm).
- **C3/C4:** a "generalized scoped negative," and a normative five-signal console "contract," explicitly framed as *a design implication from model evidence, not a user-study claim*.

The reviewers correctly identify that the empirical core is an ML-interpretability result and the HCI contribution is a normative interface proposal with no user data.

---

## 2. Triage — which criticisms are truly fatal

I find **two** genuinely decisive issues for CHI, plus a third that is serious:

**F1 (fatal for CHI-as-a-venue). No human in the loop supporting the sole HCI contribution.** The paper's only claimed *design* contribution (C4, the console UI contract) is an entirely normative prescription about what an interface "should" surface. There is no implemented/deployed system, no task, no participant, no comprehension, reliance, or decision-quality measure. The console figure is an explicitly static, cropped rendering. For a venue whose contribution model is human-centered, an unvalidated design prescription — however principled — is below bar. Both reviewers converge here, and they are right. Critically, this is **not fixable in rebuttal**: it requires running a study.

**F2 (fatal to the headline framing). "Non-transfer" is over-read from a failed superiority gate.** The pass rule (Eq. 5) requires a *demonstrated* gain ≥ δ=0.05 with a CI excluding zero. Failing it means "no sufficiently large latent win was demonstrated," not "non-transfer was demonstrated." For deliberation/skepticism the intervals are wide and include effects at or above the paper's own meaningful margin (e.g., CAA×Qwen skepticism −0.080 [−0.225, +0.045]; Llama skepticism [−0.190, +0.200]; ITI×Qwen deliberation +0.020 [+0.000, +0.055]). The paper nonetheless propagates "non-transfer verdict," "does not beat," and "legible but not controllable" into the abstract, contributions, results, and conclusion — and the console hard-codes it as **"NOT CONTROLLABLE."** Absent an equivalence/non-inferiority design (TOST, MDE, power), the null is not evidence of absence. This is the single cleanest validity criticism in the pool and I fully endorse it.

**F3 (serious, self-undermining). The console encodes F2's inferential error as a categorical user-facing verdict.** For a paper whose thesis is *trust calibration*, converting an inconclusive statistical result into "NOT CONTROLLABLE" is exactly the uncertainty-to-certainty collapse the console is supposed to prevent. Reviewer B's C3 is a sharp, fair observation. I rate it serious rather than strictly fatal because the paper does carry an explicit evidence-tier signal (exploratory/confirmatory/untested), and the specific label is *fixable* by separating PASS / HARM / NO-DETECTED-WIN / INCONCLUSIVE states.

---

## 3. Triage — which criticisms are fixable (high-leverage)

These are real but addressable in a revision cycle; several would materially strengthen the paper:

1. **Reframe the null + add equivalence/power.** Replace "non-transfer"/"does not beat" with "no demonstrated added control," and supply TOST/equivalence bounds and minimum-detectable-effect at N=40–53. This directly neutralizes F2 for the axes where the data genuinely support only non-detection, while preserving the one axis (uncertainty) that has real signal. **Highest analytic leverage.**
2. **Move the comparator protocol into the main text.** The "bounded best-prompt ceiling" is the linchpin of every C2 claim, yet the candidate prompt set, prompt budget, α grid, layer search, and direction-construction sample sizes live only in a supplementary manifest. Relabel "ceiling" → "best prompt in the pre-registered candidate set." Cheap, and it makes the headline auditable.
3. **Decompose the Brier result.** The one robust finding (calibration harm) is currently vulnerable to the "steering toward an uncertainty pole mechanically worsens 1−Brier" confound. A Murphy-style reliability/resolution/base-rate decomposition (or reliability curves / ECE, accuracy-controlled) would convert this from "probabilistic-score harm" into a defensible *calibration* claim — or honestly downgrade the label. High leverage because this is the paper's most publishable empirical nugget.
4. **Fix the console state model** (F3): PASS / HARM / NO-DETECTED-WIN / INCONCLUSIVE, exposing interval width. Turns a self-undermining artifact into one that embodies the paper's own thesis.
5. **Downgrade "replication" language** for the five-seed arm → "five-way split sensitivity on a shared item pool" (the authors already concede seeds share the same deterministic slice). Trivial, and removes an inflation reviewers flagged.
6. **Trim the social-inference / breadth-focus digression** (self-declared non-contributions) to a pointer, reclaiming space for items 1–3.

---

## 4. Where the reviewers OVER-estimate the weaknesses (fairness check)

I am not rubber-stamping the two Rejects. Several charges are overstated and should be discounted:

- **"Novelty collapse" is too strong.** Both reviewers lean on concurrent Sprejer et al. as if it were prior art. It is **concurrent** and uses different machinery (Goodfire SAE features, MMLU) versus this paper's CAA/ITI on metacognitive axes under a frozen pre-registration. CHI does not penalize independent concurrent corroboration; if anything, convergent evidence from a different route raises confidence. The Mishra (premise) + Heyman (bounds the claim to naive steering) squeeze is real and does shrink the ML novelty, but the residual — a pre-registered, fairness-controlled, interface-framed prompt-vs-latent behavioral adjudication — is a *modest but genuine* new configuration, not a scoop of Sprejer. Reviewer B's "Critical: novelty collapse" is the least fair of its critical items.

- **"It's all an underpowered null" under-credits the one real result.** The uncertainty calibration-harm result is *not* a null: its CIs exclude zero in all four cells and the sign is consistent. Treating the entire headline as non-detection erases the paper's most defensible finding. The correct critique is narrower (construct validity of "calibration"), not "the whole thing is uninterpretable."

- **The paper is penalized for its own honesty.** It repeatedly and explicitly declines to overclaim (design implication ≠ user study; exploratory ≠ confirmatory; not an impossibility theorem). Reviewer B even lists the repeated caveats as a weakness (m3). An AC should credit this discipline — it is exactly what we want authors to do. The honesty does not manufacture the missing HCI contribution, but it means the paper's *stated* claims are largely well-scoped; most "overclaim" findings are about a handful of specific words ("ceiling," "replication," "generalized," "NOT CONTROLLABLE") that are cheaply fixable, not about a pattern of dishonest inflation.

- **"Unauditable comparator/audits" conflates 'not in the paper' with 'not done.'** The prompt/α protocol and audit lineage exist in the supplementary manifests; the defect is *placement*, not absence. Fixable, and not the near-fatal linchpin failure the reviews imply.

None of these fairness corrections lift the paper to acceptance — they establish that this is a *respectable* reject, not a contemptible one, which is why my verdict is Weak Reject rather than Reject.

---

## 5. Is the contribution sufficiently impactful for CHI?

**As submitted: no.** The conceptual thesis (legibility ≠ controllability; a console should instrument that boundary) is timely and relevant — steering/feature-dashboard interfaces are proliferating, and a principled "don't turn every legible direction into a slider" message has real design value. The calibration-harm sub-finding is practically consequential for trust-facing interfaces. But at CHI specifically, impact is gated by the absence of *any* human-centered evidence for the sole design contribution, plus the ML-interpretability character of the empirical core. The natural home of the current artifact is an interpretability venue or IUI; the CHI-worthy version requires a human study.

**Contribution-type read (Wobbrock & Kientz):** Empirical — thin and, for two axes, a non-detection presented as absence; no humans. Methodological — competent held-out evaluation with multiplicity control, but standard ML practice, not a method for studying people. Theoretical — a corollary of cited theory, not new theory. Artifact/Design — a static mock + normative contract, unevaluated. None reaches the CHI bar alone.

---

## 6. Rebuttal analysis — what would most likely change my decision

**The single argument that would move me toward acceptance:** credible **human-subjects evidence that the five-signal boundary-instrumenting console improves users' calibrated reliance / decision quality** relative to a conventional slider-or-status baseline (ideally the pre-registered study the authors say is "registered but owner-gated"). This is the only rebuttal that closes F1, the central venue gap, and would convert C4 from assertion into an actual CHI contribution. Because that study cannot be run inside a rebuttal window, its practical availability is near-zero this cycle — which is precisely why the decision is reject-side rather than borderline.

**Rebuttals that would move me from Weak Reject toward Borderline (but not to Accept):**
- A convincing **reframe of F2**: TOST/equivalence + MDE showing that "no demonstrated added control" is the exact, defensible claim, with all "non-transfer / NOT CONTROLLABLE" language corrected — *and* a redesigned console state model (F3) that surfaces INCONCLUSIVE.
- A **Brier decomposition** demonstrating the calibration harm is genuine calibration degradation, not the mechanical consequence of steering toward an uncertainty pole (item 3). This would harden the one robust finding.
- Moving the **comparator protocol into the main text** so the "best-prompt" claim is auditable.

Together these would make a strong *evaluation-methodology* contribution (well suited to IUI, or a reframed CHI submission) but, absent human data, would still leave the CHI design contribution unvalidated. Hence they raise the floor without reaching accept.

**Rebuttals that would NOT move me:** arguing that CHI accepts non-user-study contributions in the abstract (true, but the artifact here is an unevaluated normative prescription, not a validated method or system); arguing Sprejer is merely concurrent (I already grant this — it does not create the missing HCI evidence); or adding more caveats (the paper is already maximally hedged).

---

## 7. Summary of reasoning for the record

- **Fatal, unfixable-in-cycle:** (F1) no human-centered evidence for the sole design contribution at a human-centered venue; (F2) "non-transfer" over-read from a failed superiority gate without an equivalence design.
- **Serious but fixable:** (F3) console converts inconclusive evidence into a categorical "NOT CONTROLLABLE" verdict.
- **Fixable, high-leverage:** equivalence/power analysis + reframed null; comparator protocol in main text; Brier decomposition for the calibration-harm result.
- **Reviewer overreach I discount:** "novelty collapse" (Sprejer is concurrent, not prior); "entirely an underpowered null" (the calibration-harm result is real signal); penalizing the paper's honest scoping; treating supplementary-only material as "not done."
- **Impact for CHI:** insufficient as submitted; strong latent potential with a user study.
- **Decision:** **Weak Reject**, with an explicit invitation to resubmit either (a) with a human-subjects evaluation of the console (→ competitive CHI), or (b) reframed as an evaluation methodology at IUI/an interpretability venue.

*End of Associate Chair meta-review.*
