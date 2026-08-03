# Stage B Hostile Rejection Case

**Recommendation:** Reject  
**Target:** ACM IUI (also below the bar for CHI/CSCW)  
**Confidence:** 4.5/5  
**Posture:** I read the frozen paper and Stage A review. I agree with A's central diagnosis, but the rejection case is stronger than A states because the paper does not actually connect its READ measurement to every steering intervention, and its allegedly user-realistic prompt comparator is a benchmark oracle.

## Summary

The paper compares DEV-selected prompts with DEV-selected CAA/ITI strengths on small deterministic slices of GSM8K and TruthfulQA. It reports no steering superiority and four negative uncertainty-score differences, then proposes a five-signal console contract. The work is admirably candid, but candor does not repair three structural failures: the legibility and control experiments do not validate the same construct/intervention, the prompt comparator is not a realistic user channel, and the only robust effect is inseparable from confidence-format compliance. The human-interface contribution remains unevaluated.

## Critical Rejection Arguments

### C1. The central “legible but non-transfer” inference is not identified, especially for ITI **[NEW]**

**Logic.** C1 and C2 do not establish the two halves of the claimed relation on the same intervention. C1 projects prompts onto a contrastively extracted “axis pole” (`main.tex`, lines 132–140). CAA uses a contrastive mean-difference direction, but ITI explicitly “obtains the direction from a probe-derived signal” (lines 165–172). The paper never shows that either ITI direction is READ-positive under the C1 measure. Consequently, ITI failure can support “this probe intervention did not beat prompting,” but not “a legible direction failed to transfer.” Even for CAA, C1 is a single-run exploratory ratio while C2 evaluates behavioral endpoints; no matched direction-level mediation or alignment test links READ magnitude to TRANSFER outcome.

**Paper quote.** “C1 asks whether a readable prompt occupies the same representational direction as an extracted cognitive-axis pole. C2 asks whether acting on a legible latent direction improves behavior” (lines 128–130). Yet: “ITI … obtains the direction from a probe-derived signal rather than a CAA contrast” (lines 169–172).

**Why dangerous.** This attacks the title, conceptual thesis, F1 taxonomy, and console contract—not merely one statistic. A negative C2 result survives, but the claimed legibility/control boundary does not.

**Persuasiveness to reviewers:** Very high (90%). ML-literate IUI reviewers should notice that READ and TRANSFER are not measured on a common treatment object.

**Possible rebuttal.** Provide per-method/per-model/per-axis READ validation for the exact frozen CAA and ITI directions and layers, then analyze whether direction-level READ predicts TRANSFER. Otherwise rename the contribution “prompt-versus-steering failed superiority” and remove the legibility-transfer thesis.

### C2. The “non-expert bounded prompt channel” is actually a labeled benchmark oracle **[NEW]**

**Logic.** The best prompt is chosen by evaluating 16 authored prompts on 20–27 labeled DEV items per axis/model. A normal interface user does not possess benchmark ground truth, run hundreds of trials, or select prompts by task accuracy/Brier/rejection labels. Thus the comparator is an offline benchmark-optimized prompt policy, not “what a user could already do.” The design may answer whether steering beats an oracle-tuned prompt baseline; it cannot answer the user-facing question repeatedly used to motivate the paper. Calling this “realistic bounded interface-effort” is unsupported.

**Paper quote.** “if a non-expert already has a bounded prompt channel” (line 51); “a set of 16 authored candidate prompts” and “the best-performing prompt … is selected on DEV item outcomes” (line 146); this allegedly reflects “a realistic bounded interface-effort.”

**Why dangerous.** This collapses ecological validity and reverses the practical meaning of the negative result. Steering may fail against an expert-authored, ground-truth-selected prompt while still adding value over prompts a real user can formulate or validate.

**Persuasiveness:** Very high (85%), particularly for HCI/IUI reviewers.

**Possible rebuttal.** Reframe the baseline honestly as an oracle benchmark comparator; add ordinary-user prompts, zero-shot/default prompts, and budget curves (best-of-1/4/8/16). Better, empirically measure how users construct/select prompts.

### C3. “Calibration harm” may be format-following harm, and the paper supplies no adjudicable parser rule **[REINFORCES A, SHARPENED]**

**Logic.** The uncertainty endpoint is computed from parsed confidence. The authors concede that steered outputs “often dropped the required confidence format,” but neither the paper nor table states how missing/malformed confidence is scored. “No truncation or empty-output collapse” does not rule out parser-induced degradation. Indeed, losing a required confidence field is exactly a mechanism that can generate a lower Brier-derived score without demonstrating worse epistemic calibration. Because this is the only axis with a robust signal, the unresolved confound threatens the entire empirical headline.

**Paper quote.** “\(1-\mathrm{Brier}\) conflates reliability, resolution, base-rate behavior, and confidence-format effects” (line 148); “steered uncertainty outputs often dropped the required confidence format” (line 229); nevertheless, “the data actively show that steering worsens calibration” (line 212).

**Why dangerous.** The paper acknowledges the alternative explanation and then states the stronger interpretation anyway. If the effect is format compliance, the title paper becomes eight underpowered non-detections plus an instruction-following artifact.

**Persuasiveness:** Extremely high (95%).

**Possible rebuttal.** Report the exact parser/imputation rule and format-compliance rates by condition/cell; rerun on pairs where both outputs are valid; separately score format adherence, confidence calibration, and answer accuracy; include reliability diagrams and Brier decomposition.

### C4. No positive control means “non-transfer” is indistinguishable from an inert or mis-targeted intervention **[REINFORCES A]**

**Logic.** There is no manipulation check showing that the selected direction and alpha reliably changed the intended construct. A coherence gate only proves outputs were not grossly degenerate. It does not prove the intervention altered deliberation, skepticism, or uncertainty. Near-zero effects can therefore mean “legible but uncontrollable,” “direction extraction failed,” “wrong layer,” “alpha too small,” “endpoint insensitive,” or “the intervention never moved behavior.”

**Paper quote.** “all-cell failure strengthens only the scoped statement about these naive, off-the-shelf steering families” (lines 181–183). The failure taxonomy nevertheless calls F1 “Legible-but-non-transfer” (`tables/failure-taxonomy.tex`, lines 9–10).

**Why dangerous.** Negative-result papers require assay sensitivity. This assay has never demonstrated a positive TRANSFER verdict, so its ability to discriminate controllable from uncontrollable axes is unknown.

**Persuasiveness:** Extremely high (95%).

**Possible rebuttal.** Add a preregistered known-steerable positive control at the same layers and alpha scale, random/scrambled-direction controls, and per-item behavioral-change rates. Demonstrate that the adjudicator can return positive when it should.

### C5. The HCI contribution is a prescription without human, design, or systems evidence **[REINFORCES A]**

**Logic.** The paper calls the contract a contribution while conceding no user evidence exists. There was no formative study, participatory design, expert walkthrough, heuristic evaluation, controlled study, longitudinal deployment, or comparison with a model card. A static figure generated from result files does not establish comprehensibility, actionability, calibrated reliance, or safety. Hedging the claim does not create evidence.

**Paper quote.** “A cognitive console should therefore instrument boundaries” (line 239); “working reality-check console” (line 239); but “We do not claim that users understand these warnings, rely on them appropriately, or benefit” (line 239). `claim-map.yaml` marks C3: “no standalone evidence row” and `gate_result: FLAGGED`.

**Why dangerous.** This is the paper's main venue-justification, yet it is the least evidenced contribution. For CHI/CSCW it is fatal; for IUI it remains a major gap because the intelligent interface is not evaluated.

**Persuasiveness:** Very high (90% at CHI/CSCW; 75% at IUI).

**Possible rebuttal.** Run a designer/user study, or demote the contract and console to future-work implications. At minimum, conduct a structured expert evaluation and compare against existing documentation/interface patterns.

### C6. The endpoint labels do not validate the claimed metacognitive constructs **[NEW]**

**Logic.** Deliberation is operationalized as GSM8K accuracy, skepticism as false-premise rejection, and uncertainty as one confidence score. Accuracy is not deliberation: a model can reason extensively and err, or answer correctly without deliberating. False-premise rejection is not general skepticism. The uncertainty score conflates multiple calibration components and formatting. There is no convergent, discriminant, or human validation of these axis measures. Therefore, failure to improve these endpoints is not evidence that “deliberation,” “skepticism,” or “uncertainty awareness” failed to transfer.

**Paper quote.** “deliberation is scored by task accuracy, skepticism by false-premise rejection, and uncertainty by … \(1-\mathrm{Brier}\)” (line 148). The authors concede these are “not complete psychological measurements.”

**Why dangerous.** The caveat is not peripheral; it breaks the semantic bridge from benchmark performance to “cognitive axes,” the feature that gives the paper novelty and interface relevance.

**Persuasiveness:** High (80%).

**Possible rebuttal.** Validate axis measures with process-sensitive indicators and blinded human judgments; show convergent/discriminant validity; narrow terminology to “GSM8K accuracy,” “false-premise rejection,” and “parsed-confidence score.”

## Major Rejection Arguments

### M1. Most of the negative grid is statistically uninformative **[REINFORCES A]**

**Logic.** The paper's post-hoc MDEs reach 0.188–0.279 for skepticism and exceed 0.067 in several deliberation cells. Eight of twelve cells cannot exclude effects that would be large on bounded outcomes. “No pass” is mechanically easy when the conjunction requires CI exclusion, mean \(\ge .05\), and coherence with only 40–53 TEST items.

**Paper quote.** “deliberation and skepticism remain underpowered non-detections” (line 38). `tables/equivalence-tost.tex` reports skepticism MDEs of 0.188, 0.268, 0.225, and 0.279.

**Persuasiveness:** Very high (90%).

**Possible rebuttal.** Increase independent item samples based on prospective power; report pooled hierarchical estimates; remove generalized-negative rhetoric for underpowered axes.

### M2. The item sample is a deterministic convenience slice, not a population sample **[NEW]**

**Logic.** All five “split seeds” reuse “the same first-\(N\) deterministic slice” of GSM8K test and TruthfulQA validation. First-\(N\) ordering can encode difficulty, source, formatting, or curation artifacts. Repartitioning the same convenience slice cannot support task-level generalization and may repeatedly expose overlapping items to DEV selection across seeds.

**Paper quote.** “the same first-\(N\) deterministic slice … only DEV/TEST split membership varies” (line 216).

**Persuasiveness:** High (80%).

**Possible rebuttal.** Sample items randomly from the full benchmark with a frozen seed, stratify on relevant attributes, evaluate independent held-out pools, and report sensitivity to pool construction.

### M3. “Fairness-controlled” confuses shared data discipline with comparable optimization opportunity **[REINFORCES A]**

**Logic.** Prompt search has 16 semantically diverse authored candidates; latent search has seven alpha values at one C1-selected layer. The spaces have different dimensionality, priors, and capacity. Layer choice is not jointly optimized, direction construction is fixed, and prompt wording carries task-format instructions that alpha cannot supply. Same DEV split does not imply a fair contest.

**Paper quote.** “This symmetric DEV-only selection … prevents the prompt channel from being weakened by an under-tuned comparator” (line 146).

**Persuasiveness:** High (85%).

**Possible rebuttal.** Drop “fairness-controlled,” justify matched budgets formally, add layer/direction/schedule search under equal compute or evaluation calls, and present performance-budget curves.

### M4. The uncertainty comparison may be structurally asymmetric in instructions **[NEW extension of C3]**

**Logic.** The manifest reveals that the selected prompt explicitly says, “Flag every uncertainty and tell me how confident you really are” (`table-manifests/c2-delta-4cell.yaml`). The paper does not disclose the steer-condition prompt. If the prompt arm receives explicit confidence-format scaffolding while the latent arm relies on steering alone, the experiment compares “instruction plus format cue” against “latent perturbation without equivalent cue.” That is not a clean comparison of control mechanisms.

**Paper quote.** “Full prompt text … [is] contained in the supplementary manifest” (lines 193–195), while no exact steer-condition prompt is reported.

**Persuasiveness:** High (85%).

**Possible rebuttal.** Publish both complete condition templates and use an identical neutral output-format instruction in both arms, varying only axis control.

### M5. Multiplicity and practical-significance standards are asymmetric **[REINFORCES A]**

**Logic.** Bonferroni correction is only across three axes within a cell, not the 12 grid tests or four harm claims. A gain must exceed \(\delta=.05\), but any statistically negative score is called harm. The harm interpretation is the opposite tail of a superiority design and is not identified as a separate preregistered family. Three effects are close to the margin.

**Paper quote.** “Bonferroni correction across axes” (line 150); “meaningful-margin threshold prevents tiny … differences from being written as practical control” (line 150); yet “all four … intervals exclude zero” is sufficient for “robust calibration harm” (line 212).

**Persuasiveness:** High (80%).

**Possible rebuttal.** Define the harm family and threshold prospectively, correct across claimed tests, apply symmetric SESOI standards, and report adjusted p-values plus pooled estimates.

### M6. Selective narrative treatment favors negative uncertainty over positive deliberation **[REINFORCES A]**

**Logic.** Deliberation is positive in all four cells (+.015 to +.025), with ITI×Qwen's 90% interval entirely positive. The paper elevates four negative uncertainty estimates into the headline while treating the four-direction-consistent deliberation pattern only as failed superiority. This may be statistically defensible cellwise, but without pooled analysis it looks narratively asymmetric.

**Paper quote.** “The headline empirical result is sharper … uncertainty calibration is consistently harmed” (line 38). `tables/c2-delta-4cell.tex` reports all four deliberation point estimates as positive.

**Persuasiveness:** Moderate-high (70%).

**Possible rebuttal.** Report preregistered or clearly exploratory pooled axis estimates, interaction tests, and symmetric interpretation of all directional patterns.

### M7. The facade ratio is an unvalidated construct with a near-tautological interpretation **[NEW]**

**Logic.** C1 divides the “strongest prompt” projection by an extracted pole reach and labels ratios below one a facade. An axis pole built from contrastive extremes should often exceed an ordinary prompt by construction. No validated threshold establishes when under-reach becomes a “facade,” no evidence shows the ratio predicts behavior or user interpretation, and the per-axis pattern fails compositional replication.

**Paper quote.** “A small ratio means that the prompt is semantically legible but reaches only part of the corresponding extracted activation direction” (lines 137–140). Yet uncertainty and focus swap status across models (lines 203–205).

**Persuasiveness:** Moderate-high (75%).

**Possible rebuttal.** Validate the ratio against independent behavioral and human-legibility criteria, establish null/positive controls and thresholds, and stop calling it a facade until predictive validity is shown.

### M8. The artifact story contains internal contradictions **[NEW]**

**Logic.** The paper says the calibration-harm figure is generated from frozen artifacts and presents artifact lineage as a credibility contribution (lines 186–195). However, `figure-manifests/c2-calibration-harm-4cell.yaml`, line 31, says: `status: "stub: plotting script/table source not yet created"`. The PDF and a script may exist, but the frozen manifest—the claimed machine-readable source of truth—declares the artifact unfinished. The main console manifest also consumes E-0010, which is `valid_for_paper=false`, while the main figure is used to instantiate C3.

**Paper quote.** “each displayed value is read from frozen, independently audited artifacts” (line 239).

**Persuasiveness:** Moderate-high (70%); particularly damaging because reproducibility is a claimed differentiator.

**Possible rebuttal.** Regenerate and freeze consistent manifests; remove invalid/exploratory inputs from the headline UI or visibly segregate them; provide hashes and an anonymized reproducibility check.

### M9. “Split-seed robust” is pseudoreplication rhetoric **[REINFORCES A]**

**Logic.** Five partitions of one deterministic item pool test split sensitivity, not robustness to item sampling, benchmark variation, decoding randomness, or model training. The abstract's compact phrase overstates what the body later concedes.

**Paper quote.** “This negative verdict is split-seed robust” (line 38), versus “should not be read as evidence from independent item draws” (line 216).

**Persuasiveness:** High (80%).

**Possible rebuttal.** Replace the phrase with “stable to five repartitions of one fixed item pool” and test independent pools and generation seeds.

### M10. Novelty is process-level and incremental, while the substantive result is expected **[REINFORCES A]**

**Logic.** The paper itself cites steerability limits, collateral damage, capability–behavior trade-offs, and trained methods that outperform naive steering. The empirical delta is primarily a frozen comparison on two small models and two benchmarks. Pre-registration and auditing are good practice, not sufficient novelty for a top-tier contribution.

**Paper quote.** Sprejer et al. report “a related degradation pattern” (line 51); Heyman and Vandeputte “show that trained steering can mimic prompting” (lines 84–90).

**Persuasiveness:** High (80%).

**Possible rebuttal.** Center a demonstrably reusable, validated adjudication method or establish a surprising phenomenon that changes prior belief. The present contract does neither.

### M11. Missing foundational HCI/accountability literature makes C3 look repackaged **[REINFORCES A]**

**Logic.** The bibliography omits Model Cards, FactSheets, Datasheets, Amershi's Guidelines for Human-AI Interaction, and canonical calibrated-reliance/automation-trust work. READ/TRANSFER/evidence-tier cards resemble per-capability documentation and warning patterns with renamed fields. Without direct differentiation, the contract's novelty is unconvincing.

**Paper quote.** “Our distinctive move is to make the prompt channel and the latent channel compete … then translate the resulting boundary into a console evaluation discipline” (lines 98–100).

**Persuasiveness:** High for HCI reviewers (85%).

**Possible rebuttal.** Add and engage the missing literature; compare the contract row-by-row against model cards/FactSheets and existing confidence/reliance interfaces.

### M12. Generalizability to deployed cognitive consoles is negligible

**Logic.** Evidence comes from two 7–8B instruct models, GSM8K/TruthfulQA slices, three narrow endpoints, naive single-layer additive interventions, and short offline single-turn generation. It excludes frontier models, reasoning models, dialogue, adaptation, trained steering, multi-layer schedules, and product prompts—the actual setting implied by “cognitive console.”

**Paper quote.** “We do not test larger models, trained steering, multi-layer schedules, RepE variants, product-specific prompts, or user adaptation” (lines 267–268).

**Persuasiveness:** Very high (90%).

**Possible rebuttal.** Narrow title and implications to the exact benchmark setting or expand the evaluation to realistic interactive systems and stronger model/method classes.

## Minor Rejection Arguments

### m1. Fairness and safety-critical relevance is contribution inflation

The paper claims “direct relevance for fairness and safety-critical contexts” (line 74) without demographic groups, disparities, consequential decisions, users, or deployment. **Persuasiveness:** 65%. **Rebuttal:** remove fairness claims or conduct subgroup/deployment analysis.

### m2. Internal “hostile audits” are not independent external validation

The abstract/contribution rhetoric emphasizes “independently audited” work (lines 69, 186), but reviewers receive no auditor identities, protocols, complete reports, or external replication. Agent sessions organized by the same project are quality control, not independent science. **Persuasiveness:** 65%. **Rebuttal:** provide anonymized audit reports and call them internal adversarial checks.

### m3. The appendix is distracting invalid evidence

The appendix includes an LLM-judge-only, single-model, single-seed study explicitly marked `valid_for_paper=false` and with unimplemented dimensions (lines 297–299). It adds attack surface and no support. **Persuasiveness:** 60%. **Rebuttal:** remove it.

### m4. Preregistration is unverifiable from the submission

The paper repeatedly invokes preregistration but supplies no review-accessible timestamped registration link. **Persuasiveness:** 75%. **Rebuttal:** provide anonymized timestamped artifacts and immutable hashes.

## Missing Related Work

At minimum, the paper must engage:

1. Model Cards, FactSheets, Datasheets, and system/capability documentation;
2. Amershi et al.'s Guidelines for Human-AI Interaction;
3. canonical automation-trust and calibrated-reliance work (e.g., Lee & See);
4. explanations/confidence interventions that fail or backfire (Bansal, Buçinca, Zhang/Liao and related work);
5. measurement-validity literature distinguishing process constructs such as deliberation from task accuracy;
6. benchmark-oracle versus user-available baselines in interactive AI evaluation.

## Unsupported or Inflated Claims

- **“fairness-controlled”** (lines 38, 69, 104, 146): same DEV split is not equal search opportunity.
- **“realistic bounded interface-effort”** (line 146): no user evidence supports this.
- **“legible … fail[s] as behavioral control”** (lines 47, 257): exact ITI directions were not shown legible.
- **“calibration harm”** (lines 38, 212, 225–229): confidence-format effects are unresolved.
- **“working console instantiation”** (line 74): a generated static figure is not an evaluated system contribution.
- **“direct relevance for fairness and safety-critical contexts”** (line 74): no fairness or safety-critical evaluation exists.
- **“split-seed robust”** (line 38): only fixed-pool repartition stability was tested.

## E-0012 Hygiene Check

I found no E-0012 / verified-control / settling-grid reference in `main.tex`, submitted tables, table manifests, or figure manifests. The filtered evidence ledger mentions E-0012 only to state that it is excluded; I do not treat that administrative note as paper evidence. No rejection argument relies on E-0012.

## Danger Ranking

### Critical
1. **C3:** Calibration claim confounded by confidence-format handling.
2. **C4:** No positive control/manipulation check; assay sensitivity unknown.
3. **C1:** READ and TRANSFER are not established on the same intervention, especially ITI.
4. **C2:** Prompt comparator is a labeled benchmark oracle, not a non-expert user channel.
5. **C5:** Interface contract has no human/design evaluation.
6. **C6:** Endpoints do not validate the named metacognitive constructs.

### Major
1. **M1:** Catastrophic power for most cells.
2. **M3/M4:** Unfair and potentially instruction-asymmetric comparison.
3. **M2/M9:** Deterministic fixed-pool pseudoreplication.
4. **M5/M6:** Multiplicity, asymmetric SESOI, and selective narrative.
5. **M7:** Unvalidated facade ratio.
6. **M8:** Artifact-manifest contradictions.
7. **M10/M11:** Incremental novelty and missing foundational prior art.
8. **M12:** Minimal ecological/generalization scope.

### Minor
Fairness inflation; unverifiable internal audits/preregistration; invalid appendix material.

## Final Verdict

**Reject.** Stage A is correct that the model-side evidence and interface-side contribution are disconnected. My stronger objection is that the model-side thesis is itself not fully identified: C1 does not validate READ for the exact ITI interventions, the benchmark endpoints do not validate the named cognitive constructs, and the user-facing comparator is an oracle selected with labeled DEV outcomes. Even before asking for a user study, the paper has not shown the relation asserted by “Legible Need Not Be Controllable.”

The most plausible resubmission is a narrower ML/IUI methods paper: disclose and repair the parser/format analysis, add positive and negative controls, validate exact-direction READ, use independent randomly sampled pools, characterize comparator budgets, and demote the console contract until it has human evidence.
