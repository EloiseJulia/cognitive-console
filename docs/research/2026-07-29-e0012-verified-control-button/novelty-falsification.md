# Novelty Falsification — Verified Control Button / Frozen-Adjudicator Positive

**Status: DRAFT / 2026-07-29**
**Author: Research/Design subagent (feature/45-e0012-research)**
**Mandate: Find the STRONGEST COUNTER-EVIDENCE, not the supportive case.**
**Source discipline: AI-Instruction Part I §5 (novelty falsification gate)**

---

## Executive Summary (Read First)

| Dimension | Verdict |
|---|---|
| Can the "verified control button" contribution stand? | **Conditionally YES** — but only if the button satisfies two jointly non-negotiable conditions: (a) it is a *non-trained/discovered* intervention (not PSR/learned-gate style), AND (b) it clears the frozen behavioral adjudicator against a *prompt-fairly-enabled* comparator. If either fails, novelty collapses to "yet another steering method." |
| Biggest single falsification risk | **Heyman collapse**: if we use any trained or optimized button construction, Heyman & Vandeputte (2026) already showed trained steering can mimic prompting. A trained calibration button that beats a plain prompt is not novel — it reproduces their positive result without their precision. |
| One-sentence novelty (defensible) | *The first paper to taxonomize LLM latent-control evidence into READ / TRANSFER / VERIFIED-CONTROL tiers using a frozen behavioral adjudicator, and to demonstrate that a specific discovered (non-trained, prompt-unreachable) calibration intervention belongs unambiguously in the third tier — establishing the evaluation discipline as the contribution, not "steering works."* |
| Risk level | **HIGH for execution; MEDIUM-HIGH for novelty** (depends critically on whether a non-trained button is discoverable) |

---

## 1. Prior Work — Detailed Analysis

### 1.1 Heyman & Vandeputte (2026) — Prompt-Steering Recovery (PSR)

**What they do:** They show that *trained* steering vectors can faithfully mimic natural-language prompts. Their positive result is that a learned linear map from prompt-text space to activation-steering space achieves near-identical behavioral outcomes. PSR demonstrates that the prompt ↔ steering gap is bridgeable — with training.

**Citation check:** `heyman2026steer` is already in the paper's bibliography and is a live prior-art threat. It is *not* concurrent — it is classified as prior work in the submitted paper.

**Mechanism / objective diff:**
- PSR objective: *replicate* what a prompt does, inside the latent channel.
- Our button objective: *exceed* what the best bounded prompt can do, for calibration behavior that is structurally prompt-unreachable.
- PSR evaluates on behavioral equivalence (mimic). We evaluate on behavioral superiority beyond a DEV-tuned best prompt.

**Mathematical form:** PSR learns W: text → Δh such that P(output | h + WΦ(text)) ≈ P(output | h_prompt). Our button is a fixed Δh (or gated Δh) that has no text-anchor, targeting a behavior the prompt channel cannot express.

**The key question — "if we use a trained button, do we fall into Heyman?"**

**ANSWER: YES, almost certainly.** If our button is any learned/optimized mapping (e.g., optimize α × direction by maximizing DEV calibration score), we are executing PSR on the calibration axis. Heyman's result says this can work — so finding it would not be surprising or novel as a *method*. Our novelty then collapses to: "we applied PSR to calibration in the context of a frozen adjudicator." That is incremental, not a boundary theorem.

**Mitigation:** The button must be *discovered* (e.g., extracted mechanistically: a logit-lens calibration feature, an SAE feature with interpretable semantics, a layer subspace found by linear probing without outcome-optimization on the test axis). It is NOT trained to mimic a prompt; it is found via a different pathway and verified to exceed what prompts can reach. This is the "non-trained / discovered" condition from D-0057.

**Falsification verdict:** If the winning button turns out to require DEV-score optimization of its direction (not just its scalar α), it is PSR-family. We would need to either (a) scope the novelty explicitly as "PSR for calibration + frozen adjudicator discipline" and cite Heyman as direct precedent, or (b) restrict to non-optimized button families. The psper's distinct contribution then shifts entirely to the evaluation discipline + READ/TRANSFER/VERIFIED taxonomy, which is the defensible fallback.

---

### 1.2 Conditional / Dynamic / Gated Activation Steering (2024–2026)

**What they do:** Multiple recent papers in the activation-engineering space go beyond static single-vector addition. Examples include:

- **Composition of steering vectors** (concurrent arXiv 2024-2025): e.g., steering on multiple axes simultaneously without mutual interference, using orthogonalization.
- **Context-conditioned steering** (several concurrent works): applying a steering vector only when certain activation thresholds or input features are present (effectively a gate).
- **Token-selective steering** (e.g., intervene only at reasoning tokens or at positions identified by a probe).
- **Representation editing** (ROME, MEMIT, AlphaEdit 2024): targeted weight-level or activation-level edits for specific factual content.

**Objective / mechanism diff vs our button:**
- These works optimize for *behavioral performance on their target task* (instruction following, factual recall, etc.), with no frozen adjudicator and no prompt-fairness discipline.
- None of them frame the question as "does the latent intervention beat the bounded best-prompt baseline under a DEV/TEST fairness protocol?"
- None of them produce a READ / TRANSFER / VERIFIED taxonomy tied to HCI console design.
- None target *calibration specifically* with a Brier-based adjudication.

**Heyman relationship for gated/conditional buttons:** A learned gate (e.g., "apply steering only when model confidence is above X") is a trained conditional steering policy. It is PSR-family if the gate is learned from the behavioral outcome. A *fixed* mechanistic gate (e.g., "apply only at the final reasoning token") is less PSR-like but still requires that the gate itself not be outcome-optimized.

**Falsification verdict:** If we propose a "gated Δh only when logit margin is low" button, the gate condition can in principle be expressed as a prompt instruction ("if you are uncertain, hedge more"). The novelty claim depends on showing the gate is *mechanistically unreachable by prompting* — i.e., the model cannot self-monitor its own logit margin from text alone and enact the same behavior change. This is an empirical claim that would need verification. **This is a real risk.** A gating strategy that can be approximated by "be more careful when unsure" prompt language does not establish prompt-unreachability.

---

### 1.3 SAE Feature Steering — Huang & Lim (2025); Sprejer et al. (2026)

**Huang and Lim (2025):** Layperson GUI for SAE feature steering and persona building. This is already cited as an HCI neighbor. Their contribution is the *interface*, not a frozen behavioral adjudication. They do not run the prompt-vs-latent fairness comparison or produce the READ/TRANSFER/VERIFIED taxonomy.

**Sprejer et al. (2026):** Closest empirical neighbor; already cited as "concurrent, not prior" in the paper. They use Goodfire SAE features, MMLU tasks, and find capability–behavior trade-offs. They do NOT use:
- A frozen pre-registration
- A 2×2 method × model grid
- A paired DEV/TEST adjudication
- An HCI legibility-console framing
- A verified positive (they also find degradation)

**If our button is SAE-feature based:** SAE feature steering for calibration improvement is a live research area. Sprejer already shows SAE features degrade calibration. Our question is whether a *specific, identified* SAE calibration feature can be steered to *improve* calibration beyond the best prompt. This would be:
- Novel in the sense of a verified SAE positive for calibration
- But immediately framed as "which SAE features survive the frozen adjudicator" rather than "we invented a new method"

The novelty contribution in this case is the **selection discipline** (frozen adjudicator + prompt-fairness protocol) that certifies which features belong in the VERIFIED-CONTROL tier, not "SAE steering works."

**Falsification risk:** A reviewer could argue: "you just ran Sprejer's SAE methodology but with a preregistered evaluation. That is a methods comparison, not a novel contribution." The rebuttal requires that (a) the frozen adjudicator itself is the contribution (evaluation discipline), and (b) the taxonomy READ/TRANSFER/VERIFIED is a new conceptual unit.

---

### 1.4 Control-Discovery / Representation Control

**RepE (Zou et al., 2023) / Representation Engineering:** Extracts linear directions for concepts from paired activations, steers along them. Already cited via `zou2023repe`. Does NOT adjudicate against a prompt comparator.

**Subspace control (various 2024–2025):** Work on disentangling representation subspaces for targeted editing without side effects. Again, the evaluation is behavioral on the target task without a prompt-fairness discipline.

**Causal/mechanistic discovery:** Techniques like ACDC, ROME, path-patching identify circuit-level causal structure. These are mechanistic tools that could help *find* a button candidate, but they do not adjudicate it.

**Control-discovery objective vs ours:** These works optimize for behavioral success on a target; our adjudicator asks "does this beat the best prompt baseline while passing coherence gates?" That is a strictly harder test. A control-discovery method that succeeds on its own metric might still fail our adjudicator. The adjudicator discipline is therefore orthogonal and complementary to the discovery method.

**Falsification verdict:** LOW risk from this family. The frozen adjudicator + prompt-fairness protocol is not yet present in the representation-control literature. The risk is that a reviewer says "your discovered button is just activation addition — where is the novelty?" The answer is the evaluation discipline that certifies it as VERIFIED-CONTROL.

---

### 1.5 Mishra et al. (2026) — Non-Surjectivity

**What they do:** Show that steered residual activations can reach states unreachable by bounded prompts (internal non-surjectivity at the representation level). This is a theoretical/characterization result, not a behavioral positive.

**Relationship to our button:** Mishra motivates *why* a VERIFIED-CONTROL might exist — if the internal state space is non-surjective, there could be behaviors only reachable from the latent channel. Our button is the empirical demonstration of that possibility.

**Risk:** Mishra is a workshop paper. A reviewer might ask: "is the connection to non-surjectivity anything more than rhetorical? Your button could succeed purely because CAA/ITI happen to hit a useful region, not because the region is truly prompt-unreachable." This is a real falsification risk. To defend the non-surjectivity framing, the paper would ideally show that the button's behavioral effect cannot be approximated by any prompt in a reasonable hypothesis space — not just the 16 authored prompts used in the current DEV selection. The prompt-fairness protocol (document 2 in this batch) is critical for this defense.

---

## 2. Nearest-Neighbor Matrix

| Work | Objective | Mechanism | Adjudicator | Prompt comparator | Taxonomy | Our delta |
|---|---|---|---|---|---|---|
| Heyman & Vandeputte (PSR, 2026) | Trained steering mimics prompting | Learned W: text→Δh | None (behavioral equivalence) | YES (mimic target) | None | We target *superiority*, not equivalence; non-trained buttons only |
| Sprejer et al. (2026) | SAE feature steering trade-offs | SAE feature addition (Goodfire) | None (MMLU benchmark) | No (no prompt baseline) | None | Frozen adjudicator + DEV/TEST fairness + READ/TRANSFER/VERIFIED taxonomy |
| Huang & Lim (2025) | Layperson SAE feature GUI | SAE feature steering + GUI | None | No | None | Behavioral adjudication, not UI design |
| Conditional activation steering (misc 2024–25) | Targeted behavioral control | Gated/composed vectors | Task benchmarks | No | None | Prompt-fairness gate; frozen prereg; HCI console discipline |
| RepE / Zou et al. (2023) | Representation engineering | Contrastive direction extraction | Task benchmarks | No | None | Same; adjudicator is the contribution |
| Mishra et al. (2026) | Internal non-surjectivity characterization | Theoretical + activation analysis | None | Yes (bounded prompts) | None | Behavioral demo of prompt-unreachable positive |
| CAA (Rimsky et al., 2024) | Steering via mean-difference directions | Contrastive means | None | No | None | Frozen behavioral adjudicator; prompt-fair comparator |
| ITI (Li et al., 2023) | Probe-derived truthfulness steering | Probe directions | TruthfulQA accuracy | Weak (no DEV/TEST fairness) | None | Full adjudicator discipline |

---

## 3. Timeline Assessment

- The C2 negative result (paper current state) is **2026-07-24** (E-0005/E-0006 frozen).
- Heyman & Vandeputte is prior work (cited in the paper, pre-2026-07-24).
- Sprejer et al. is concurrent (2026, explicitly labeled).
- Conditional activation steering papers are ongoing in 2024–2025; no single paper owns the "verified positive with prompt-fairness discipline" claim.
- **No paper found** that: (a) pre-registers a frozen adjudicator, (b) enforces DEV/TEST prompt-fairness symmetry, (c) produces a READ/TRANSFER/VERIFIED taxonomy, AND (d) demonstrates a verified positive through that adjudicator.

**The gap is real.** The risk is execution (finding the positive), not prior-art blocking.

---

## 4. Defensible One-Sentence Novelty

> **"The first frozen, pre-registered, prompt-fair behavioral adjudication that discriminates READ, TRANSFER, and VERIFIED-CONTROL tiers for LLM latent interventions — demonstrated via a discovered (non-trained, prompt-unreachable) Calibration Button on the uncertainty axis, establishing the evaluation discipline and console contract, not merely the button itself."**

**Why this holds up under attack:**
- It does NOT claim "steering works" (prior art).
- It does NOT claim "trained steering beats prompts" (Heyman covers that).
- It claims the **evaluation discipline** (frozen adjudicator + prompt-fairness + taxonomy) as the primary contribution.
- The **Calibration Button** is a positive *demonstration* of the taxonomy — not the standalone contribution.
- If the button is NOT found, the taxonomy contribution still stands (VERIFIED-CONTROL remains empty; that is an honest, informative result).

**If the button is trained/PSR-family:** novelty collapses to "PSR reproduced on calibration axis under frozen adjudicator." The evaluation discipline retains novelty but the paper loses the positive claim. This is the Heyman-novelty risk quantified.

---

## 5. Specific Answers to Falsification Questions

**Q: Does a "trained button" that succeeds fall into Heyman's already-proven conclusion?**
**A: YES.** If the button direction or gate is outcome-optimized on behavioral data (even just DEV calibration scores), it is PSR-family. The novelty then reduces to: applying the PSR insight to the calibration axis, evaluated under a frozen adjudicator. That is publishable as a methods comparison but not as a boundary-theorem novelty claim. The defensive move is to restrict the "Calibration Button" family in the prereg to non-trained interventions: mechanistically-derived directions (from probing, SAE features, logit-lens analysis) where the direction is obtained by a criterion independent of the behavioral outcome we are adjudicating.

**Q: Does conditional/dynamic steering pre-empt the button family?**
**A: PARTIALLY.** Conditional steering is prior art in the sense that "gated Δh" is a known concept. Our contribution is NOT the gate; it is certifying a specific gate/button under the frozen adjudicator as VERIFIED-CONTROL, combined with the HCI taxonomy. A reviewer who says "gating is known" can be answered: "yes, and we are the first to certify that a specific gate passes the behavioral adjudicator against a prompt-fair comparator — that certification is what makes it a console-safe control, not the gate per se."

**Q: Can Sprejer or Huang/Lim absorb our contribution?**
**A: NO** — they don't have the frozen adjudicator or prompt-fairness protocol. The evaluation discipline is not present in either. Sprejer finds degradation; they would not predict which intervention (if any) survives our protocol.

**Q: Is the non-surjectivity (Mishra) framing circular?**
**A: RISK.** If the prompt-fairness comparator is only 16 authored prompts, a reviewer might say the "unreachability" is trivially true (you tried only 16 prompts) but not informative. The protocol must bound the prompt hypothesis class formally — e.g., "a prompt that can express `if model is uncertain, enact lower-confidence output`" is structurally describable, and we can argue the model lacks the self-monitoring introspection to execute it faithfully. That argument is empirical (show the best calibration-targeted prompt still fails) and protocol-dependent.

---

## 6. Risk Register

| # | Risk | Level | Mitigation |
|---|---|---|---|
| R1 | No non-trained button passes the frozen adjudicator — VERIFIED-CONTROL tier stays empty | HIGH | Primary fallback: taxonomy discipline as contribution; boundary theorem is the negative (no verified control). Paper becomes "we looked and didn't find one; here is why that matters." |
| R2 | Winning button turns out to be PSR-family (outcome-optimized direction) → Heyman collapse | HIGH | Pre-register button family as strictly non-trained BEFORE running Stage 0; if a trained button wins, report it honestly as PSR-consistent and scope accordingly. |
| R3 | Reviewer argues "prompt-fairness is just 16 prompts — trivial" | MEDIUM | Extend prompt comparator to include paraphrase family + auto-optimized prompt (e.g., APE/DSP-style DEV optimization). If auto-optimized prompt also fails, the button's prompt-unreachability is much better supported. |
| R4 | Conditional/dynamic steering literature has a paper close to our verification protocol | MEDIUM-LOW | Do a deeper search before freezing the prereg; if found, cite as prior art and reframe as "application to metacognitive calibration + HCI console discipline." |
| R5 | SAE feature direction already known to encode calibration (Bricken et al. 2023 / Anthropic interpretability) | LOW-MEDIUM | If using SAE features, the direction itself is not novel; but the adjudication under our frozen protocol + HCI framing is. |
| R6 | "Boundary theorem" framing overstates mathematical rigor | LOW | Do not use "theorem" in the paper; use "boundary finding" or "boundary characterization." The frozen adjudicator is an empirical tool, not a proof. |

---

## 7. Honest Caveat

This novelty analysis is based on a doc-only survey (no zero-GPU access to full arXiv archives). The analysis draws on papers cited in the current paper plus targeted web search. The following have NOT been checked exhaustively and could harbor a surprise prior:
- Conditional activation steering papers from arXiv 2025 (esp. ICLR/NeurIPS/ICML 2025 proceedings).
- Industry-internal reports on SAE feature certification for safety applications.
- Any paper combining frozen behavioral adjudication + prompt-fairness in non-HCI venues (e.g., safety/alignment workshops).

A pre-submission novelty search (dispatched as a separate subagent with full arXiv access) is recommended before freezing the E-0012 prereg.
