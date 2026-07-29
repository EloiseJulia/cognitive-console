# Reviewer B — Skeptical Reject Analysis

**Paper:** *Legible Need Not Be Controllable: A Frozen Reality Check for Prompt-vs-Latent Behavioral Control in LLMs*  
**Recommendation:** **Reject**  
**Confidence:** **5/5**

## Scope and bottom line

I reviewed only the submitted paper (`docs/paper/main.tex`, all included tables and figures, and `references.bib`) and Reviewer A's report. I also built the paper successfully. I did not consult author-intent ledgers or claim maps.

The paper is unusually disciplined about preregistration language, DEV/TEST separation, and artifact provenance. That procedural care does not rescue the submission. The central negative result is inferred using a test that can establish a sufficiently large latent win but cannot establish non-transfer or equivalence. The flagship “calibration harm” result uses Brier score as though it were a pure calibration measure. The proposed console then converts these uncertain statistical findings into categorical user-facing labels such as “NOT CONTROLLABLE.” Finally, the only distinct HCI contribution is an unevaluated static interface contract with no users, tasks, interaction study, or evidence of improved reliance.

At a sub-25% HCI venue, these are rejection-level defects rather than matters of presentation.

---

# Critical rejection arguments

## C1. The paper has no validated HCI contribution

**Paper evidence.**

> “This is a design implication from model evidence, not a user-study claim”  
> — Introduction, `main.tex:59`

> “The design contribution in this paper is an evidence-derived evaluation discipline and a working console instantiation, not a user-study finding.”  
> — Introduction, `main.tex:63`

> “We do not claim that users understand these warnings, rely on them appropriately, or benefit from the console without a future human-subjects study.”  
> — Design Implications, `main.tex:222`

> “Until such a study is run, we cannot claim that people understand the proposed warnings, calibrate trust better, or make better decisions with the console.”  
> — Limitations, `main.tex:261`

**Logic.** The paper's empirical work concerns model internals and benchmark outcomes. Its purported HCI contribution is a normative interface proposal, but it supplies no formative design process, user needs analysis, interaction technique evaluation, usability evidence, decision-quality outcome, reliance measure, or deployment. The authors explicitly concede that every human-facing benefit remains unknown. A static rendering plus recommendations about what interfaces “should” show is not enough to establish a top-tier HCI contribution.

The “working console instantiation” wording is particularly inflated. The paper describes no system architecture, interaction loop, implementation study, or use context. Figure 3 is explicitly a “Static paper rendering” (`main.tex:225–228`) and its PDF says, “no humans/GPU/API/model calls.”

**Persuasiveness to other reviewers:** **Very high (95%)**. This is likely decisive for CHI/CSCW and still serious for IUI.

**Possible author rebuttal.** The authors could argue that CHI accepts technical and methodological HCI contributions without user studies. To succeed, they would need to show that the interface contract itself is a novel, rigorously derived design method and demonstrate its utility on real design decisions. The present paper instead admits that user comprehension and benefit are untested. A preregistered comparative user study against a conventional slider/status interface would be the convincing rebuttal.

## C2. Failure to pass a superiority gate is misinterpreted as evidence of non-transfer

**Paper evidence.**

> “Under the frozen pass rule in Eq. (5), every method--model cell fails to produce a latent win on the adjudicated axes, yielding the pre-registered non-transfer verdict within the tested scope.”  
> — Results, `main.tex:197`

The deliberation intervals are:

> “+0.015 [-0.040, +0.070]”  
> “+0.025 [-0.030, +0.075]”  
> “+0.020 [+0.000, +0.055]”  
> “+0.015 [-0.040, +0.060]”  
> — Table 3, `tables/c2-delta-4cell.tex:11,15,19,23`

The skepticism intervals include:

> “+0.000 [-0.190, +0.200]”  
> “+0.000 [-0.195, +0.205]”  
> — Table 3, `tables/c2-delta-4cell.tex:16,24`

**Logic.** The preregistered rule asks whether a cell demonstrates a statistically significant gain of at least \(\delta=0.05\). Failing that rule means “a sufficiently large gain was not demonstrated.” It does **not** mean “non-transfer was demonstrated.”

Indeed, all four deliberation confidence intervals include effects at or above the paper's own meaningful margin, and the skepticism intervals are so wide that they include very large positive effects. The data therefore remain compatible with practically meaningful latent benefits. To support “non-transfer,” the authors would need an equivalence/non-inferiority design that excludes gains of \(\delta\), not a failed superiority test. Preregistration freezes an inferential mistake; it does not make the mistake valid.

The problem infects the abstract, contribution list, results, discussion, and conclusion through phrases such as “does not beat,” “non-transfer verdict,” and “legible but not controllable.”

**Persuasiveness to other reviewers:** **Extremely high (98%)**. This is the cleanest statistical reason to reject the headline.

**Possible author rebuttal.** The authors can defend “no cell passed the preregistered win criterion” as a descriptive procedural fact. They cannot defend it as evidence of equivalence or absence. A credible rebuttal requires larger TEST sets, prospective power/MDE analysis, and equivalence tests whose confidence bounds exclude effects of \(+\delta\). Otherwise the claims must be rewritten as “no win was detected.”

## C3. The proposed interface turns statistical uncertainty into a misleading categorical control verdict

**Paper evidence.**

> “a TRANSFER verdict, indicating whether it has passed the prompt-vs-latent behavioral test”  
> — Design Implications, `main.tex:222`

The console figure labels:

> “Deliberation — LEGIBLE but NOT CONTROLLABLE”  
> “TRANSFER: FAIL Δ=0.015”  
> — `figures/console-ui-contract.pdf`, Deliberation card

The corresponding interval is:

> “CAA & Qwen2.5-7B & Deliberation ... +0.015 [-0.040, +0.070] ... fail”  
> — Table 3, `tables/c2-delta-4cell.tex:11`

**Logic.** The interface does not merely report the cautious fact “did not pass this test.” It announces “NOT CONTROLLABLE,” even though the interval includes a gain above the paper's meaningful threshold. This is precisely the sort of uncertainty-to-certainty collapse that a trust-calibration interface should avoid.

The design contribution is therefore not just unevaluated; its flagship instantiation is epistemically unsafe. It conflates a conservative decision rule with a property of the model and presents that conflation as a user-facing status. A console intended to calibrate trust should show “inconclusive / insufficient power” where appropriate, distinguish evidence of harm from lack of demonstrated benefit, and expose interval width.

**Persuasiveness to other reviewers:** **Extremely high (97%)**. It directly connects the statistical flaw to the claimed HCI artifact and makes the paper self-undermining.

**Possible author rebuttal.** The authors could say “NOT CONTROLLABLE” is shorthand for “did not satisfy our frozen deployment gate.” That interpretation is absent from the card and inconsistent with ordinary language. A rebuttal requires redesigning the state model to separate **PASS**, **HARM**, **NO DETECTED WIN**, and **INCONCLUSIVE**, followed by user testing of how those labels are interpreted.

## C4. “Calibration harm” is unsupported because Brier score is not a pure calibration measure

**Paper evidence.**

> “uncertainty [is scored] by the proper per-item score \(1-\mathrm{Brier}\)”  
> — Methods, `main.tex:135`

> “Uncertainty & \(1 - \mathrm{Brier} = 1 - (\mathrm{conf}_i - \mathrm{correct}_i)^2\)”  
> — Table 2, `tables/axis-outcome-definitions.tex:11`

> “On the uncertainty axis ... it worsens calibration relative to the DEV-selected best prompt.”  
> — Results, `main.tex:210`

**Logic.** Brier score is a proper probabilistic scoring rule, but it is not a pure calibration statistic. Its classical Murphy decomposition includes reliability/calibration, resolution, and outcome uncertainty. A worse mean Brier score can arise from changed accuracy, changed sharpness/resolution, or changed confidence conditional on correctness—not necessarily worse calibration.

The paper performs no calibration-curve analysis, reliability decomposition, ECE-style diagnostic, accuracy-controlled analysis, or confidence/correctness stratification. It also never clearly establishes whether the “uncertainty” steering direction is intended to increase hedging, decrease confidence, improve probability calibration, or express epistemic uncertainty. Calling the observed score difference “calibration harm,” “calibration backfire,” and a “trust-control” risk therefore overstates the construct measured.

This is not a semantic quibble: calibration harm is the only result whose four displayed intervals clearly exclude zero and is the main bridge to trust, fairness, and safety claims.

**Persuasiveness to other reviewers:** **Very high (92%)**, especially among statistically sophisticated reviewers.

**Possible author rebuttal.** The authors could narrow the term to “probabilistic-score harm” or “worse \(1-\)Brier outcome.” To preserve “calibration harm,” they need Brier decomposition, calibration plots, reliability error, confidence distributions for correct/incorrect answers, and evidence that task accuracy or resolution does not explain the change. They should also cite foundational scoring-rule work such as Brier (1950) and Murphy (1973).

## C5. The novelty collapses to methodological hygiene plus an unvalidated framing

**Paper evidence.**

> “Mishra et al. show internal non-surjectivity”  
> — Introduction, `main.tex:46`

> “Prompt-steering-recovery work shows that trained steering can mimic prompting.”  
> — Introduction, `main.tex:46`

> “A concurrent study by Sprejer et al. reaches a related degradation pattern”  
> — Introduction, `main.tex:50`

> “The novelty is not a better steering method, but a frozen, interface-relevant test...”  
> — Related Work, `main.tex:93`

**Logic.** The paper's conceptual premise comes from Mishra; the important counterexample comes from Heyman; and the empirical degradation-vs-prompt pattern substantially overlaps Sprejer. The remaining distinction is that this paper combines two old steering methods, two small models, three author-defined axes, preregistration, and an HCI framing.

Preregistration, held-out selection, pairing, multiplicity control, generated tables, and audit trails are commendable research hygiene, not by themselves a scientific contribution. The paper's claimed HCI novelty is the console framing, but that framing is not evaluated. Consequently, after prior work is credited, the residual contribution is close to: naive CAA/ITI did not clear a conservative superiority gate against selected prompts on a small benchmark grid. That is too incremental for a highly selective venue.

**Persuasiveness to other reviewers:** **High (85–90%)**. Novelty judgments vary, but the paper itself supplies the damaging comparison.

**Possible author rebuttal.** The authors could demonstrate that the adjudicator exposes a previously unknown and consequential failure mode that prior benchmarks cannot detect, then validate that this information changes interface design or user decisions. As submitted, the claimed distinctive unit is primarily a protocol configuration.

## C6. The “bounded best-prompt ceiling” and fairness claim are not auditable from the paper

**Paper evidence.**

> “the comparator is the best bounded prompt selected under the same DEV/TEST discipline”  
> — Related Work, `main.tex:84`

> “DEV-only selection ... prevents the prompt channel from being weakened by an under-tuned comparator.”  
> — Methods, `main.tex:137`

> “Full prompt text for DEV-selected best prompts is contained in the supplementary `c2-delta-4cell.yaml` manifest”  
> — Artifact Availability, `main.tex:176`

**Logic.** “Ceiling” is a strong term. The paper does not state in the main submission the candidate prompt set, who authored it, the prompt budget, whether prompts were axis-specific or model-specific, how prompt variants were generated, whether system prompts were allowed, the alpha grid, layer search budget, direction-construction sample sizes, or whether prompt and latent channels received comparable optimization effort.

Selecting each channel on DEV is not sufficient to establish fairness. A best element from an arbitrary bounded list is not a ceiling on prompting, and a coarse alpha/layer search can make steering appear weak. Because the scientific claim is explicitly relative to this comparator, relegating its definition to a manifest prevents readers from assessing the headline.

**Persuasiveness to other reviewers:** **High (88%)**. The comparator is the linchpin of every C2 claim.

**Possible author rebuttal.** Include the complete prompt-generation protocol, all candidates, search budgets, alpha/layer grids, selection objectives, and compute parity in the paper or immediately inspectable appendix. Replace “ceiling” with “best prompt in our preregistered candidate set” unless a genuine upper-bound argument is supplied.

---

# Major rejection arguments

## M1. The “metacognitive axes” have weak construct validity

**Paper evidence.**

> “deliberation is scored by task accuracy, skepticism by false-premise rejection, and uncertainty by the proper per-item score \(1-\mathrm{Brier}\)”  
> — Methods, `main.tex:135`

> “Deliberation & Accuracy”; “Skepticism & False-premise rejection rate”  
> — Table 2, `tables/axis-outcome-definitions.tex:9–10`

**Logic.** Accuracy is not deliberation; false-premise rejection is not skepticism; and Brier score is not uncertainty awareness. These are task outcomes that may correlate with the named constructs, but the paper supplies no construct validation, convergent measure, manipulation check, annotation study, or evidence that the latent directions correspond to stable metacognitive properties rather than benchmark-specific response tendencies. Anthropomorphic labels amplify the apparent HCI relevance without validating the constructs.

**Persuasiveness:** **High (85%)**.

**Possible rebuttal.** Treat the labels as operational shorthand, provide validated item/task definitions, triangulate each axis with multiple measures, and avoid claims about cognition or metacognition unless construct validity is demonstrated.

## M2. The five-seed result is pseudo-replication, not replication

**Paper evidence.**

> “This pre-registered negative replicates across five seeds”  
> — Abstract, `main.tex:37`

> “The five seeds share the same item pool (the same first-\(N\) deterministic slice of GSM8K test and TruthfulQA validation); only DEV/TEST split membership varies by seed”  
> — Results, `main.tex:199`

**Logic.** Repartitioning the same small deterministic item pool measures split sensitivity. It does not replicate across independent items, data collections, tasks, prompts, or model runs. Reusing the word “replicates” in the abstract creates a stronger impression than the design supports. Moreover, repeated split results under the same conservative pass rule largely repeat the inferential flaw in C2.

**Persuasiveness:** **Very high (93%)**.

**Possible rebuttal.** Rename it “five-way split sensitivity,” remove replication language from the abstract, and test independent random item draws or new datasets.

## M3. The external-validity bridge from two small open models and two benchmarks to cognitive consoles is too long

**Paper evidence.**

> “We cover two model families, two off-the-shelf steering families, and three adjudicated metacognitive axes”  
> — Discussion, `main.tex:250`

> “We do not test larger models, trained steering, multi-layer schedules, RepE variants, product-specific prompts, or user adaptation to console feedback.”  
> — Discussion, `main.tex:250`

**Logic.** Qwen2.5-7B and Llama-3-8B are a narrow slice of the LLM design space and are not representative of the frontier systems users encounter in deployed products. GSM8K and TruthfulQA are likewise poor proxies for interactive reasoning, search, drafting, or decision support. The data are single-turn, use deterministic first-\(N\) slices, and do not include real user prompts. The paper's strongest generalizable conclusion should therefore be about these exact model-task-method combinations, not cognitive-console design broadly.

**Persuasiveness:** **High (88%)**.

**Possible rebuttal.** Add larger and newer model families, independent datasets, realistic interaction tasks, multi-turn prompts, and product-relevant steering methods—or narrow the design claims substantially.

## M4. C1's “facade” classification lacks a stated decision rule and is vulnerable to layer/prompt selection

**Paper evidence.**

> “ask how far the strongest readable prompt travels along the extracted axis”  
> — Methods, `main.tex:123`

> “the reach of the extracted axis pole at the chosen non-degenerate layer”  
> — Methods, `main.tex:130`

> “each model has a single exploratory run”  
> — Methods, `main.tex:123`

The table nevertheless gives categorical labels:

> “Facade?” / “yes” / “no”  
> — Table 1, `tables/c1-twomodel.tex:9–18`

**Logic.** The paper does not define the formal threshold for “facade,” how the “strongest” prompt was selected, how the “chosen” layer was selected, or how prompt/layer selection uncertainty enters the confidence interval. A ratio below one merely says one selected displacement is smaller than another selected displacement; it does not by itself establish semantic legibility, a facade, or a meaningful prompt/latent mismatch. With one run per model and half the axes changing status across models, “cross-model support” is fragile.

**Persuasiveness:** **High (82%)**.

**Possible rebuttal.** Predefine a null/equivalence band, report all layers and prompts, account for selection in uncertainty estimates, repeat across seeds and prompt sets, and validate legibility with independent probes or judgments.

## M5. The common \(\delta=0.05\) margin is unjustified across incommensurate outcomes

**Paper evidence.**

> “\(\delta = 0.05\)”  
> — Methods, Eq. 5, `main.tex:157–164`

The outcomes are:

> “Accuracy”; “False-premise rejection rate”; “\(1-\mathrm{Brier}\)”  
> — Table 2, `tables/axis-outcome-definitions.tex:9–11`

**Logic.** A five-point change has different practical meaning, variance, ceiling behavior, and user consequence for accuracy, rejection rate, and Brier score. The paper supplies no domain-specific justification, utility analysis, or user-centered basis for treating 0.05 as a common meaningful effect. This arbitrary shared margin directly determines every pass/fail label.

**Persuasiveness:** **Moderate-high (78%)**.

**Possible rebuttal.** Justify axis-specific margins prospectively using prior evidence, decision utility, or user-centered thresholds; report sensitivity across plausible margins.

## M6. Multiplicity handling does not match the grid-wide rhetoric

**Paper evidence.**

> “Bonferroni correction across axes controls the chance of declaring a latent win by trying several metacognitive targets.”  
> — Methods, `main.tex:137`

> “A generalized scoped negative with calibration harm”  
> — Contribution list, `main.tex:58`

**Logic.** The stated correction is within three axes, while the paper narratively aggregates four method-model cells, multiple seeds, C1 analyses, a mechanism test, and exploratory recovery. For the negative claim, the deeper issue remains lack of equivalence testing; for positive “harm” and robustness rhetoric, the paper should clearly define the confirmatory family and joint estimand. “All four intervals exclude zero” is not a substitute for a prespecified grid-level model or test.

**Persuasiveness:** **Moderate-high (75%)**.

**Possible rebuttal.** Define the confirmatory family and primary estimands explicitly, provide a hierarchical or grid-level analysis, and separate confirmatory from descriptive cross-cell summaries.

## M7. Preregistration, hostile audits, and artifact lineage are self-attested rather than independently verifiable in the paper

**Paper evidence.**

> “were each reviewed by independent hostile audit sessions”  
> — Methods, `main.tex:173`

> “This lineage is what permits the paper to report negative and exploratory results without asking the reader to trust a narrative reconstruction.”  
> — Methods, `main.tex:173`

**Logic.** The paper gives no registration URL/date, immutable protocol identifier, auditor identities or independence criteria, audit method, disagreement record, or accessible full execution environment. “Independent hostile audit sessions” may mean internal automated agents rather than independent researchers; the phrase risks borrowing the credibility of external audit without explaining what independence entails. Frozen JSON and scripts help reproduce plots, but they do not independently reproduce model generation, parsing, direction extraction, or item selection.

**Persuasiveness:** **Moderate-high (80%)**.

**Possible rebuttal.** Provide timestamped public preregistrations, complete audit reports, auditor relationship/disclosure, raw generations, hashes, executable pipelines, and enough information to rerun the model-level experiment rather than only regenerate figures from stored JSON.

## M8. The PSR-style recovery arm cannot carry the abstract's method-strength rebuttal

**Paper evidence.**

> “providing preliminary evidence that this negative result is not merely a consequence of using naive steering directions”  
> — Abstract, `main.tex:37`

> “it is single-model, single-seed, and valid only as preliminary support”  
> — Limitations, `main.tex:257`

> “the optimizer's internal search objective uses its own alpha ... whereas the adjudicated comparison still uses the DEV-frozen alpha”  
> — Discussion, `main.tex:246`

**Logic.** A single-model, single-seed exploratory null with an alpha-objective mismatch does not neutralize the obvious objection that CAA/ITI are weak baselines. Yet the abstract uses this arm to protect the headline from precisely that objection. The method is insufficiently described in the main paper to assess fidelity to Heyman or optimization adequacy.

**Persuasiveness:** **High (82%)**.

**Possible rebuttal.** Remove the abstract-level defense or run a fully specified, preregistered recovery method across both models, multiple independent samples, and adequate optimization budgets.

## M9. The related-work review omits foundational HCI trust/reliance and uncertainty-interface literature

**Paper evidence.**

> “HCI research has long treated AI interaction as a problem of legibility, control, and calibrated reliance.”  
> — Related Work, `main.tex:87`

The paragraph then cites only a small set of recent works, and the bibliography lacks foundational references on appropriate reliance, interaction guidelines, cognitive forcing, and uncertainty visualization.

**Logic.** For a paper whose HCI contribution is supposedly trust recalibration through interface warnings, the related work should engage with at least:

- Lee and See (2004), *Trust in Automation: Designing for Appropriate Reliance*;
- Amershi et al. (CHI 2019), *Guidelines for Human-AI Interaction*;
- Buçinca, Malaya, and Gajos (CSCW 2021), *To Trust or to Think*;
- Wischnewski et al. (CHI 2023), trust-calibration measurement survey;
- Kay et al. (CHI 2016), uncertainty visualization in predictive systems;
- Kaur et al. (CHI 2020), use of interpretability tools.

The statistical framing also omits Brier (1950) and Murphy's (1973) decomposition. These omissions matter because prior HCI work already studies how limitation cues, uncertainty displays, and forcing functions affect reliance—the exact empirical bridge this paper leaves untested.

**Persuasiveness:** **High for HCI reviewers (85%)**.

**Possible rebuttal.** Add and synthesize this literature, then specify what new design knowledge the five-signal contract contributes beyond established limitation disclosure and reliance-calibration interventions.

## M10. Fairness, safety, and deployment implications are inflated beyond the evidence

**Paper evidence.**

> “potentially of interest across HCI, fairness, and AI safety communities”  
> — Introduction, `main.tex:63`

> “Do not deploy naive CAA/ITI steering as a trust-control primitive for calibration-facing products”  
> — Failure taxonomy, `tables/failure-taxonomy.tex:11`

**Logic.** There is no fairness analysis, subgroup analysis, safety-critical task, stakeholder study, deployment study, or risk assessment. The paper moves from two small models on GSM8K/TruthfulQA to a categorical deployment recommendation. Even if the Brier result is accepted, it does not establish downstream trust harm or safety impact.

**Persuasiveness:** **Moderate-high (80%)**.

**Possible rebuttal.** Recast these as hypotheses or precautionary motivations, not evidence-backed contributions. Support deployment guidance with domain-specific validation and human reliance outcomes.

## M11. The social-inference section is a self-declared non-contribution that dilutes the paper

**Paper evidence.**

> “As an explicitly exploratory extension, not a paper contribution”  
> — Discussion, `main.tex:240`

> “single-model ... single-seed, and LLM-judge-only; human-rater calibration is still pending”  
> — Discussion, `main.tex:240`

**Logic.** The section introduces novice disclosure, manipulation, M1–M4 outcomes, an LLM judge, unimplemented measures, and another exploratory latent readout, while explicitly disclaiming contribution status. It adds conceptual and ethical complexity without supporting the main claim. Its inclusion suggests result accumulation rather than a focused argument and consumes space needed for comparator details, power analysis, and construct validation.

**Persuasiveness:** **Moderate (70%)**.

**Possible rebuttal.** Remove it from the main paper or reduce it to one future-work sentence.

## M12. The paper confuses reproducible rendering with reproducible experimentation

**Paper evidence.**

> “Regenerating tables and figures requires only Python 3 and the frozen JSON artifacts; no GPU access is needed”  
> — Artifact Availability, `main.tex:176`

**Logic.** This permits regeneration of presentation artifacts from author-produced summaries. It does not independently reproduce generations, sampling, extraction, probe fitting, parser behavior, prompt selection, or model interventions. The paper repeatedly invokes “audited artifacts” as credibility, but stored JSON cannot reveal upstream errors or selective construction by itself.

**Persuasiveness:** **Moderate-high (76%)**.

**Possible rebuttal.** Distinguish figure reproducibility from end-to-end experimental reproducibility and provide raw generations plus executable end-to-end pipelines.

---

# Minor rejection arguments

## m1. “Model family” and “generalized” language remains rhetorically stronger than the design

**Paper evidence.**

> “a generalized scoped negative”  
> — Contributions, `main.tex:58`

> “two model families”  
> — Discussion, `main.tex:250`

**Logic.** One Qwen checkpoint and one Llama checkpoint do not establish family-level behavior. “Generalized scoped” is an awkward hedge that still invites overreading.

**Persuasiveness:** **Moderate (65%)**.

**Possible rebuttal.** Say “two checkpoints” and “observed across the tested 2×2 grid.”

## m2. The prose relies on bespoke terminology that overpackages standard procedures

**Paper evidence.**

> “HARKing-resistant measurement instrument”  
> — Methods, `main.tex:137`

> “representational facade,” “frozen behavioral adjudicator,” and “interface evaluation contract”  
> — Methods and Design Implications, `main.tex:121–137,222`

**Logic.** These terms make ordinary held-out comparison, a projection ratio, and a proposed status card sound like established constructs. The terminology increases cognitive load without corresponding validation.

**Persuasiveness:** **Moderate (60%)**.

**Possible rebuttal.** Use standard statistical and HCI terminology and reserve new construct names for validated concepts.

## m3. The manuscript is overlong and internally repetitive

**Paper evidence.**

> “We do not claim a universal limit on steering, a proven mechanism for calibration harm, or demonstrated user benefit.”  
> — Conclusion, `main.tex:274`

Similar scope disclaimers recur in the abstract, introduction, results, discussion, limitations, and conclusion.

**Logic.** Repeated caveats do not compensate for overclaiming elsewhere and make the paper feel defensive. The social extension and repeated audit/provenance assertions obscure the actual evidence.

**Persuasiveness:** **Low-moderate (55%)**.

**Possible rebuttal.** Tighten the manuscript, state scope once clearly, and use the recovered space for essential methodological detail.

---

# Ranked danger summary

## Critical

1. **No validated HCI contribution:** no users, interaction evaluation, or evidence that the console improves reliance.
2. **Invalid non-transfer inference:** failure of a superiority gate is treated as evidence of absence despite intervals permitting meaningful gains.
3. **Misleading UI verdicts:** the console converts inconclusive evidence into “NOT CONTROLLABLE.”
4. **Calibration construct failure:** Brier-score degradation is mislabeled as calibration harm without decomposition or diagnostics.
5. **Novelty collapse:** prior work supplies the theory, counterexample, and related degradation finding; the residue is protocol hygiene plus framing.
6. **Unauditable comparator:** “best-prompt ceiling” and fairness cannot be assessed without the prompt/search protocol.

## Major

1. Weak construct validity for deliberation, skepticism, and uncertainty.
2. Five-seed pseudo-replication on the same deterministic item pool.
3. Poor generalizability from two 7–8B checkpoints and two benchmark slices.
4. Undefined and selection-sensitive C1 facade classification.
5. Unjustified common \(\delta=0.05\) across heterogeneous outcomes.
6. Multiplicity analysis does not match grid-wide rhetoric.
7. Preregistration/audit independence is asserted but insufficiently documented.
8. Exploratory PSR arm is too weak to answer the method-strength objection.
9. Missing foundational trust, reliance, uncertainty-interface, and Brier-score literature.
10. Unsupported fairness, safety, and deployment claims.
11. Irrelevant, underdeveloped social-inference extension.
12. Figure/table regeneration is presented too close to end-to-end reproducibility.

## Minor

1. “Model family” and “generalized” language overstates checkpoint-level evidence.
2. Bespoke terminology packages standard procedures as new constructs.
3. Repetitive caveats and exploratory digressions weaken clarity.

---

# Final verdict

**Reject.** The paper is rejectable at a sub-25% HCI venue on multiple independent grounds. Most decisively, it has no demonstrated human-centered contribution, its central negative claim is not supported by an equivalence design, its proposed interface encodes that inferential error as a categorical user-facing verdict, and its calibration headline does not use a calibration-specific analysis. The methodological hygiene is commendable, but it cannot substitute for valid inference, construct validity, novelty, or HCI evidence.
