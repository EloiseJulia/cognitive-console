# Prompt-Fairness Protocol — Verified Control Button Comparator Design

**Status: DRAFT / PROPOSAL — 2026-07-29**
**Author: Research/Design subagent (feature/45-e0012-research)**
**Priority: MAKE-OR-BREAK DESIGN (D-0057 flag #1)**
**Discipline: Doc-only; no experiments; no frozen records touched**

---

## 1. Why This Document Is the "Whole Ballgame"

D-0057 identifies prompt-fairness as the single most critical design requirement for E-0012:

> "A button only counts if it beats a bounded best prompt that is ALSO allowed to attempt the same target behavior."

If the Calibration Button only beats a naive "be more careful" prompt rather than a *seriously-constructed*, DEV-tuned calibration prompt, the result is trivial. Any reviewer will immediately ask: "did you try a strong calibration-instruction prompt?" A weak comparator invalidates the VERIFIED-CONTROL claim entirely.

This document specifies exactly how the comparator is constructed, how the adjudication is run, what constitutes "prompt-unreachability," and what failure modes would torpedo the argument.

---

## 2. The Calibration Button: Target Behavior

The Calibration Button targets the `uncertainty_awareness` axis: the per-item outcome `1 − Brier = 1 − (conf_i − correct_i)²`.

A "better calibrated" output means:
- When the model is correct, it expresses high confidence (reducing Brier).
- When the model is incorrect, it expresses low confidence (reducing Brier).
- Abstaining / refusing to answer on hard items (if the adjudicator rewards abstention-as-uncertainty).

The **target behavior** is therefore: *systematically lower Brier score on the calibration item pool, under k=5 samples/item, without collapsing output coherence.*

---

## 3. The Bounded Best-Prompt Baseline — Construction

### 3.1 Prompt Family Requirement

The bounded best-prompt baseline for the Calibration Button must include prompts that *seriously attempt the same goal*. This rules out:
- A "baseline" that uses the same generic system prompt as the unsteered model (too weak).
- A "baseline" that uses only deliberation-style prompts with no calibration-specific instruction.

The Calibration Button comparator family MUST include at minimum:
1. **Explicit confidence-calibration instruction:** "Express your confidence level accurately. If you are unsure, say so clearly and give a lower confidence estimate."
2. **Abstention-enabling instruction:** "If you do not know the answer, it is better to say 'I don't know' than to guess. Include your confidence as a number from 0 to 1."
3. **Hedging + uncertainty acknowledgment:** "When answering, always indicate how certain you are. Use phrases like 'I'm fairly confident that...' or 'I'm not sure but...' to reflect your actual uncertainty."
4. **Forced-confidence elicitation:** "After giving your answer, rate your confidence in it from 0 (completely uncertain) to 1 (completely certain)."
5. **Step-through-uncertainty instruction:** "Before answering, assess how confident you are. If there are multiple plausible answers, state them and give each a probability."
6. **Anti-overconfidence instruction:** "Do not overstate your confidence. If the question is ambiguous or you lack relevant knowledge, express that uncertainty explicitly."
7. **Brier-implicitly-targeted instruction:** "Aim to be well-calibrated: don't claim more certainty than you have, and don't understate your certainty either. Give your confidence accurately."
8. **Abstention-gate instruction:** "If you are less than 50% confident in your answer, state 'I am not confident' instead of guessing."

**In addition**, to match the DEV-optimization budget given to the steering channel, the prompt family should include:
9. A **paraphrase family** (3–4 variants of the strongest prompt above) to test whether surface phrasing drives the result.
10. An **auto-optimized prompt**: use a prompt-optimization method (e.g., greedy token refinement on DEV items, or a meta-prompt that asks the model to generate a calibration-maximizing instruction) to produce the strongest achievable prompt-only baseline. This is important for blocking the "you didn't try hard enough" objection.

Baseline family size recommendation: **16 authored prompts** (matching the C2b adjudicator) **+ 1 auto-optimized prompt** = 17 total candidates. The best-performing on DEV is the "bounded best-prompt baseline."

### 3.2 DEV Selection Procedure (mirrors C2b adjudicator exactly)

1. Items are split into DEV (~1/3) and TEST (~2/3) by the same frozen procedure as E-0012 prereg.
2. Each of the 17 prompt candidates is evaluated on ALL DEV items, k=5 samples/item.
3. The candidate achieving the highest mean `1 − Brier` on DEV is selected as `best_calibration_prompt`.
4. `best_calibration_prompt` is FROZEN before TEST evaluation begins.
5. The button's α parameter is ALSO selected on DEV (same protocol as C2b adjudicator §3.1).
6. **Both selections are frozen simultaneously** before any TEST item is evaluated.

This gives the prompt channel a fair chance: it can use *any* of 17 calibration-targeted candidates and picks the best on DEV — exactly the same selection discipline as the latent channel's α optimization.

---

## 4. The Adjudication — Paired Comparison

The adjudication reuses the **frozen C2b behavioral adjudicator** (`prereg-c2b-adjudication.md §4`) with no modification to the statistical decision rule. The paired comparison is:

```
d_i = steer_i − prompt_i
```

where:
- `prompt_i` = `1 − Brier` on item i using `best_calibration_prompt` (DEV-frozen), mean over k=5 samples.
- `steer_i` = `1 − Brier` on item i using the Calibration Button at DEV-frozen α, mean over k=5 samples.

**Pass criterion (Bonferroni-corrected, same as C2b):**
- 98.33% CI of mean(d) excludes 0 (upward)
- Point estimate mean(d) ≥ δ = 0.05
- Coherence gate ≤ 1.5× baseline

A positive verdict here means: **the Calibration Button improves calibration beyond what even the best DEV-tuned calibration-specific prompt achieves.** This is the "prompt-unreachable" condition.

---

## 5. What "Prompt Can't Reach" Means Operationally

The button is VERIFIED-CONTROL if and only if it passes the adjudicator above. "Prompt-unreachable" is therefore an *empirical* label, not a theoretical claim.

**Structural argument supporting the label:** The calibration button (e.g., a probe-derived direction targeting the logit-margin subspace) acts on the model's *internal confidence representation* at a layer before decoding, without going through the text-instruction-following pathway. A prompt instruction like "express accurate confidence" asks the model to *reason about and then enact* a confidence adjustment — a two-step process dependent on instruction-following capability. The button directly edits the representation, potentially bypassing the instruction-following gap. If the model's instruction-following is imperfect for confidence calibration (which the C2b negative suggests), the button may succeed where the prompt fails.

**Caveat:** This structural argument is supportive but not decisive. The adjudicator verdict is what matters for the paper claim. The structural argument goes in the Discussion.

---

## 6. Prompt Families for Other Candidate Buttons

If Stage 0 identifies candidates beyond Calibration, each needs its own prompt family:

| Button type | Prompt comparator must include |
|---|---|
| Abstention / verification gate | "Before answering, verify you know the answer. If you don't, say 'I don't know' explicitly." + several hedging variants |
| Premise-gate (skepticism) | "Before answering, check whether the premise of the question is true. If it contains a false premise, identify and reject it." + false-premise rejection variants |
| Deliberation quality | "Think step by step and show your full reasoning before giving a final answer." + variants of chain-of-thought prompts |

The rule is: **the prompt comparator must be allowed to attempt the exact target behavior the button attempts.** A deliberation button must beat a chain-of-thought prompt, not a bare "solve this" prompt.

---

## 7. Failure Modes That Would Torpedo the Argument

### 7.1 FATAL: The Button Only Implements a Describable Prompt Strategy
**Scenario:** The Calibration Button, under analysis, is essentially performing "add hedge language and lower the confidence token logprob." A prompt like "output a lower confidence estimate and hedge your language" achieves the same effect.

**Detection:** Run the paraphrase family including explicit hedge/lower-confidence instructions. If any such prompt achieves similar DEV performance to the button, the button is prompt-reachable.

**Protection:** Include at least 3–4 explicit hedge-plus-low-confidence prompts in the DEV family. If the button's DEV advantage over the best prompt is < δ, declare it prompt-reachable and exclude it.

### 7.2 FATAL: "Best Prompt" Is Artificially Weak
**Scenario:** We select only generic prompts, not calibration-specific ones. The button beats a straw-man comparator.

**Protection:** The 17-prompt family above is specifically designed to prevent this. The auto-optimized prompt further hardens the comparator. If a reviewer can name a strong calibration prompt not in the family, we lose credibility. The DEV family must be authored before seeing ANY TEST outcomes.

### 7.3 FATAL: The Button Only "Wins" by Abstaining Always
**Scenario:** The button routes most items to "I don't know" (confidence ≈ 0), which trivially minimizes Brier on wrong items. But it destroys accuracy.

**Detection:** Monitor accuracy alongside Brier. The prereg must include an **accuracy guard** (see Document 4): button must not reduce accuracy below a pre-specified floor (e.g., accuracy ≥ 0.8× unsteered baseline on same items). The coherence gate already catches some of this, but a specific accuracy guard is needed.

**Protection:** Add to the pass criterion: `accuracy(steer) ≥ accuracy_floor` where `accuracy_floor = 0.9 × accuracy(unsteered)`. This prevents the trivial "abstain on everything" solution.

### 7.4 FATAL: Brier-Gaming without Genuine Calibration Improvement
**Scenario:** The button improves `1 − Brier` by increasing expressed confidence on correct items only (cherry-picking by memorization / exposure bias), not genuine calibration.

**Detection:** Brier decomposition (reliability/resolution/uncertainty split). This requires per-item (confidence, correctness) pairs. Since Brier decomposition is marked DEFERRED in the current results (raw pairs not committed), the E-0012 item pool must generate and store these raw pairs from the outset.

**Protection:** Pre-register that the Stage 1 evaluation MUST store raw (confidence, correctness) pairs per item per sample, enabling Brier decomposition. This is a data-collection requirement, not a post-hoc add-on.

### 7.5 MAJOR: Cross-Model Failure — Button Is Local, Not General
**Scenario:** The button works on Qwen2.5-7B but fails on Llama-3-8B at Stage 2.

**Classification:** This gives LOCAL verdict (one-model button). It is honest and publishable but the console implication is weaker ("this specific model has a verified calibration button").

**Protection:** Stage 2 transfer stress testing is designed to catch this. The paper's claim must be scoped to the specific model for which VERIFIED-CONTROL is confirmed.

### 7.6 MAJOR: Button Is Model-Layer-Specific with No Mechanism
**Scenario:** The button works only at one specific layer for one specific α. Robustness is low.

**Detection:** Report the α × layer sensitivity analysis as part of Stage 1. If the button only passes at one (layer, α) combination, it is fragile.

**Protection:** Require at least 2 adjacent (layer, α) combinations to pass coherence+calibration jointly before declaring VERIFIED-CONTROL. Or report the fragility honestly in the console contract.

---

## 8. Edge Cases and Protocol Guards

### 8.1 What If the Auto-Optimized Prompt Beats the Button?
This is an expected possibility. If APE/DSP-style prompt optimization on DEV achieves better `1 − Brier` than the button, the button is prompt-reachable (by a sufficiently engineered prompt). In this case:
- The button does NOT earn VERIFIED-CONTROL.
- Report it as TRANSFER (it improves over naive prompting but not over engineered prompting).
- This is an honest, informative result.

**Pre-register:** if the auto-optimized prompt outperforms the button on DEV, the button is classified as TRANSFER or UNDERPOWERED, not VERIFIED-CONTROL. This must be in the prereg to prevent post-hoc reclassification.

### 8.2 The Prompt Wins on DEV but Button Wins on TEST
This would suggest a DEV overfitting artifact. The prereg must specify: DEV performance determines which comparator is used in TEST. If the prompt wins on DEV, the prompt is the baseline; if the button wins on DEV AND also wins the paired TEST comparison, it is VERIFIED-CONTROL.

### 8.3 Multiple Buttons — Which Prompt Family?
Each button family has its own prompt comparator family (see Section 6). The pre-registered button list must specify, for each button, which prompt family it competes against. Cross-family comparisons (calibration button vs. deliberation prompt) are explicitly excluded from the adjudication.

---

## 9. Summary: Protocol-Level Checklist for Prompt-Fairness

| Check | Requirement | Status |
|---|---|---|
| Prompt family includes calibration-specific instructions | ≥ 16 authored prompts targeting same behavior as button | To be authored pre-Stage 0 |
| Auto-optimized prompt included | DEV-optimized prompt variant (APE-style) | To be pre-registered |
| DEV selection is frozen before TEST | Both best_prompt and button_α frozen on DEV simultaneously | Pre-register |
| Accuracy guard specified | accuracy(steer) ≥ 0.9 × accuracy(unsteered) | Pre-register |
| Brier decomposition enabled | Raw (conf, correct) pairs stored per item per sample | Stage 1 data-collection requirement |
| Coherence gate unchanged | ≤ 1.5× unsteered baseline (from frozen C2b adjudicator) | Already frozen |
| Button family restricted to non-trained | Direction obtained by criterion independent of behavioral outcome | Pre-register button family types |
| Statistical test unchanged | Frozen C2b §4 rule (paired bootstrap, Bonferroni, δ=0.05) | Reuse frozen adjudicator |
| Failure modes pre-registered | Abstain-always guard, Brier-gaming guard, prompt-wins-DEV rule | Pre-register |
