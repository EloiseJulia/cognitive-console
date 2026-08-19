# Review R1 (Methods / Statistical Rigor) — ACM IUI Full Paper

## 1. Scope check

This paper is in scope for IUI, but with venue-fit risk. The manuscript is about whether model-internal signals should be promoted into interface controls, and it explicitly frames the unit of analysis as an interface release decision: "whether such a control has earned an active role" and "for whom, and against what the user could already do without it" (Introduction). That is an IUI-relevant question because intelligent interfaces increasingly expose sliders, probes, and steering controls to end users.

The risk is that the empirical core is almost entirely computational. The paper repeatedly acknowledges that the human-interface side is planned rather than executed: Section "Planned Evaluation with Everyday and Proficient Users" says "this paper reports no user data"; Limitations says "The current study contains no human result." For IUI, a methods/evaluation-policy paper can still be publishable, but the current version must persuade reviewers that the computational qualification assay is itself the contribution, not merely an incomplete prelude to a user study. I think the topic fits IUI; the missing human validation and substitution-only setup are major venue-fit weaknesses.

## 2. My independent restatement of the contributions and central claims

The paper proposes an evaluation procedure for deciding whether a readable latent model direction deserves to become an active UI control. The key idea is not to ask whether steering changes outputs in absolute terms, but whether it improves behavior over the alternative available to the relevant user population: a DEV-selected strong prompt for proficient users and an average/ordinary prompt for everyday users. The procedure records READ evidence, TRANSFER evidence, the prompt comparator, warnings, and evidence tier, then maps that record to an interface action: active control passes only if both local representation and behavioral transfer pass; otherwise the control is withheld or kept read-only.

The worked case applies this to CAA and ITI steering on Qwen2.5-7B-Instruct and Llama-3-8B-Instruct over deliberation, skepticism, and uncertainty. The main empirical claim is a bounded negative result: none of twelve steering cells earns a quality advantage over the strong prompt. The manuscript further claims this negative is not simply because the assay is unsatisfiable, because a prompt-level positive control passes the gate and a separate Stolfo/Phi-3 latent positive control passes the same adjudicator on a different task. It also claims that the everyday-user quality comparison is not rescued by replacing the strong prompt with an ordinary prompt, though this arm is Qwen-only, exploratory, and convenience remains untested.

## 3. Claim-by-claim attack

### Claim A: The paper contributes a valid evaluation method for release decisions about internal-signal controls.

What would make it false: if the method's pass/fail rule is arbitrary, insensitive, comparator-dependent in an uncontrolled way, or not actually connected to realistic interface use.

Evidence in manuscript: The method defines a five-field record in Section "Five-Field Qualification Record" and a qualification rule in Eq. 3: `0 \notin I_a \land \bar d_a\ge\delta \land g_a^S\le\tau g_a^0+\epsilon`, with `\delta=0.05`, `\tau=1.5`, and `\epsilon=0.02`. It also states that the portable requirement is a declared comparator/outcome/uncertainty/floor/coherence gate, whereas the thresholds are "this application's settings."

Assessment: The framework is conceptually strong, but the statistical release rule is under-justified. A point-estimate floor with only `0 \notin I_a`, rather than requiring the lower confidence bound to exceed the minimum effect, means an estimate can pass even when the interval includes many effects below the declared minimum. The paper admits this: "it does not require the interval's lower bound to exceed \(\delta\)." For a release decision, this is a surprisingly permissive rule; it is not obvious why it is called conservative merely because false release is assumed costlier. If false release is costlier, the natural release rule would require the lower bound to clear the floor. This matters for IUI because the proposed method is meant to guide deployment of controls to users, not only scientific inference.

### Claim B: "None of the twelve model--method--axis tests qualifies" over a bounded strong prompt, and this supports withholding active controls for proficient users.

What would make it false: if the tests are underpowered, floored, or unable to detect effects near the declared floor; if DEV selection leaked into TEST; if the comparator was unfairly chosen; or if the conclusions over-generalize from no-pass to absence.

Evidence in manuscript: Table 1 reports N_test of 40, 40, and 53 with five generations per item, but the estimand averages generations within item, so the inferential N is item count. The paper admits skepticism MDEs were "0.188, 0.268, 0.225, and 0.279 ... compared with a declared point-estimate floor of 0.05," and says this is "a need for finer resolution ... not an ineffectiveness verdict." Deliberation under 64 tokens is described as "near the floor" and "cannot separate equivalence from a floor effect." The two ITI deliberation cells were "not re-measured and remain 64-token--floored placeholders." Uncertainty is stronger: the paper reports negative contrasts, and a Qwen--CAA powered remeasurement at N=813 gives mean -0.088, 90% TOST CI [-0.109,-0.067], MDE 0.050.

Assessment: The broad headline "no latent arm wins" is literally supported by the gate, but the stronger interpretation that this is meaningful negative evidence varies sharply by axis. The uncertainty negative is relatively persuasive for Qwen--CAA and directionally negative in all four frozen uncertainty cells, but missingness and parser imputation remain threats. Skepticism and deliberation are not adequately powered to support absence at the 0.05 floor across the grid. The manuscript is commendably honest in places, but the abstract and conclusion compress unresolved/floored/underpowered cells into a clean "none of twelve" narrative. That is a classic underpowered-null risk.

### Claim C: The negative result is not an insensitive-assay artifact because positive controls pass.

What would make it false: if the positive controls validate only trivial parts of the pipeline or use a different task/model so distant that they do not establish sensitivity for the target axes.

Evidence in manuscript: The prompt-level positive control "accepts a non-degenerate format-following advantage (Delta=0.60, 98.33% CI [0.45,0.75])" and rejects noisy nulls. The latent positive control is "Stolfo instruction-steering on Phi-3-mini, keyword-existence task" with steer-baseline +0.222 and 98.33% CI [0.089,0.378]. The paper explicitly limits this: it "validates the adjudication procedure rather than sensitivity on Qwen and Llama at the three console axes specifically."

Assessment: The manuscript correctly scopes the positive controls in the limitations, but the abstract's phrase "a predeclared positive control confirms the gate can still qualify a control" is only partially responsive to the reviewer attack. A prompt-level format control mainly shows the adjudicator is not logically unsatisfiable. The Stolfo/Phi-3 control is more relevant, but it is a different model, method, and keyword task, found after a "non-preregistered fallback" from Qwen and gated Gemma to Phi-3. It licenses the narrow claim that the code path can certify a latent intervention somewhere, not that the CAA/ITI assay is sensitive on deliberation/skepticism/uncertainty. This should be a major limitation, not used to substantially defuse underpower concerns for the main grid.

### Claim D: The substitution estimand is appropriate for interface release decisions.

What would make it false: if real sliders compose with user prompts rather than replace them, or if substitution changes the construct being measured.

Evidence in manuscript: Section "Two Prompt Comparators and Substitution Design" says "The prompt condition uses the comparator instruction; the steering condition uses a neutral carrier instruction plus the latent intervention." Discussion states: "The application substitutes steering for the selected prompt, whereas a product control would ordinarily act in the presence of a user's instruction" and "Prompt-plus-steer evidence is pending, so the paper makes no composition claim."

Assessment: This is a serious construct validity limitation. The paper's title and motivating examples involve interface controls/sliders, but the main evidence evaluates latent intervention instead of a prompt. For proficient users, a real interface control would often be used on top of the user's instruction. The substitution design is useful as a stringent benchmark, but it cannot answer whether a slider deserves an active role in a composition setting. The paper acknowledges this, yet several interface-facing passages still sound deployment-oriented: "active control is withheld" and "team pauses the slider." Those claims are only justified for a latent-only substitute control, not for a compositional UI control.

### Claim E: The everyday-user comparison shows steering does not reliably beat an ordinary prompt; convenience remains open.

What would make it false: if the average prompt is not a valid ordinary-user proxy, the arm is underpowered, or the exploratory status is blurred.

Evidence in manuscript: Section "Everyday-User Comparator" states the arm is Qwen-only, reuses the same TEST items/coefficient/adjudicator, and "is exploratory and single-run on a single model, and is not part of the confirmatory headline." It reports positive but uncertain estimates for CAA skepticism (+0.126 [-0.009,+0.261]), ITI skepticism (+0.106 [-0.051,+0.266]), and CAA deliberation (+0.027 [-0.054,+0.106]), with uncertainty missingness-limited.

Assessment: The paper is mostly honest here. However, the abstract says "Against even an ordinary prompt, steering shows no reliable quality gain (Qwen, exploratory), leaving its convenience ... open." That is acceptable if "no reliable" means unresolved; it should not be read as a powered absence. The ordinary-prompt proxy is not validated, and the manuscript itself says the planned study will check whether candidate-set average matches novices. For IUI, the everyday-user claim should be framed as preliminary context only.

## 4. Evidence audit of headline numbers/claims

### 0/12 no-pass grid

Supported as a procedural statement by Table 1: every row has "ok / fail." But the evidentiary interpretation is heterogeneous. Several CIs are wide relative to the 0.05 floor, e.g., CAA-Qwen skepticism -0.080 [-0.225,+0.045], CAA-Llama skepticism +0.000 [-0.190,+0.200], ITI-Llama skepticism +0.000 [-0.195,+0.205]. These are not precise nulls. The paper's own text says MDEs for skepticism are far above the floor. Therefore, 0/12 is not a well-powered global absence of benefit; it is a no-pass decision under a release rule.

### MDEs and power

The paper deserves credit for reporting MDE limitations explicitly. But it should make power central in the abstract/conclusion, not only in Results/Limitations. Skepticism MDEs of 0.188-0.279 versus a 0.05 floor mean the main grid could not rule out practically meaningful effects at the stated release margin. The Qwen--CAA refined skepticism result (N=505, mean -0.014, 90% TOST [-0.038,+0.010], MDE=0.053) is close, but the manuscript says MDE is still "slightly above the floor" and only one cell is refined. Deliberation CAA 512-token MDE around 0.037 is better, but estimates remain "slightly negative and underpowered" by the authors' own wording. The two ITI cells remain floored.

### Qualification rule and multiple comparisons

The within-cell Bonferroni correction across three axes is clear: "two-sided 98.33% intervals; it does not control familywise error over the full descriptive twelve-test grid." This honesty is good. However, for a release framework, a cell-level rule of "at least two axes pass" seems ad hoc and is not deeply justified. Also, because a pass only requires the point estimate to exceed delta rather than the interval lower bound, the rule is not a standard superiority-over-MCID rule. If the method is to guide UI deployment, the statistical semantics of "pass" require stronger defense.

### DEV/TEST split and leakage

The manuscript states that prompts and latent coefficients are selected on DEV and frozen for TEST, with counts 20/40, 20/40, and 27/53. That is good. Remaining concerns: the prompt comparator is selected from only sixteen prompts, and Limitations admits "authorship independence, TEST blindness, and resource parity are not established." Also, five split seeds reused the same item pool, and the original split had already been observed before additional splits were frozen. The manuscript appropriately says this is split sensitivity, not new-item replication. I do not see a fatal leakage admission in the manuscript, but comparator provenance is a major validity threat.

### Positive controls

The prompt-level control is useful to show the gate can fire. It does not validate latent steering sensitivity. The latent Stolfo/Phi-3 control is useful but narrow and partially post hoc because of fallback model selection. The paper quotes the limitation well: it "validates the adjudication procedure rather than sensitivity on Qwen and Llama at the three console axes specifically." Therefore the strongest reviewer attack is not fully closed: the target assay may still be insensitive for the tested axes.

### Uncertainty measurement and missingness

This is the strongest statistical result in sign, but also has the most measurement fragility. The frozen scorer imputes missing confidence as 0.5, yielding 1-Brier=0.75 regardless of correctness. The Qwen--CAA recheck shows parseable-confidence rates differ greatly: steering 0.826 versus prompt 0.445. Complete-case steer-minus-prompt is -0.337, but all-generation adversarial bounds are [-0.478,+0.250]. A later powered Qwen--CAA no-exclusion scorer remeasurement gives a clean negative at the floor. I find the comparator-negative Qwen--CAA uncertainty result credible under the frozen scorer, but not a general claim about uncertainty awareness without resolving missingness and parser behavior across cells.

### Delib-512 remeasurement

The 512-token CAA remeasurement is an important repair. It shows prompt/steer accuracies 0.88/0.84 for Qwen and 0.71/0.69 for Llama, so the floor problem is reduced for CAA. However, it reselects alpha on a new 512-token DEV and is explicitly additive, not a frozen-grid replacement. ITI deliberation remains unrepaired. The headline should not imply deliberation is resolved for ITI.

### Exploratory versus confirmatory separation

The paper is unusually explicit about evidence tiers and exploratory arms: READ is "exploratory," average-prompt is "exploratory and single-run," novice-style prompt is "exploratory only," and composition/human slots are pending. This is a strength. The main weakness is rhetorical compression in abstract/conclusion: exploratory and underpowered results are sometimes used to support a broad narrative of no advantage. The paper should consistently say "no pass under the release rule" rather than "no reliable quality gain" unless power is adequate.

## 5. Strongest reject case and strongest accept case

### Strongest reject case

The paper asks an important IUI question but does not yet provide a sufficiently validated IUI evaluation. The central empirical result is a 0/12 no-pass grid, yet multiple cells are underpowered relative to the paper's own 0.05 floor, two ITI deliberation cells remain generation-length floored, skepticism MDEs are 4-5x the release floor, and uncertainty depends on a fragile confidence parser/missingness regime. The positive controls show the adjudicator can fire in other settings, not that it is sensitive for the target model-axis-method combinations. The substitution design does not match how an active UI slider would usually be used, i.e., composing with a user's prompt. The paper's interface action language ("withhold the active control") therefore exceeds the evidence. For IUI, there is no user study, no validation that designers or users understand the record, and no tested convenience/accessibility benefit. The result is a thoughtful computational audit, but not yet a full IUI contribution.

### Strongest accept case

This is a careful, unusually transparent negative-result paper on a timely IUI problem: how to decide when readable internal model signals should become controls. It makes a valuable methodological contribution by forcing comparator disclosure, evidence-tier binding, separation of READ and TRANSFER, and explicit blocking reasons. The authors do not hide uncomfortable findings: they report floor effects, MDE limitations, missingness, exploratory status, lack of immutable model hashes, and substitution-only scope. The no-pass result is not presented as a universal anti-steering verdict, and the positive controls plus 512-token and powered remeasurements show serious effort to rule out trivial assay failure. IUI needs principled release criteria for intelligent controls; even with computational-only evidence, this paper provides a concrete and auditable template.

## 6. Ranked findings

### [BLOCKER] The main 0/12 negative is not adequately powered at the declared 0.05 floor across the grid.

Location: Abstract: "naive latent steering beats the strong prompt on none of the twelve tests"; Results: "None of the twelve model--method--axis tests qualifies"; Section "TRANSFER Produces Axis-Specific Reasons": "Minimum detectable positive effects (MDEs) were 0.188, 0.268, 0.225, and 0.279 ... compared with a declared point-estimate floor of 0.05"; "two ITI cells remain 64-token--floored placeholders."

Why it matters for IUI: A release method for controls must distinguish "withhold because likely no benefit" from "withhold because the assay cannot resolve the relevant effect." If reviewers see an underpowered null, the paper's central negative contribution weakens substantially.

Cheapest discriminating action: Revise the headline claim and abstract to explicitly say "no pass under the release rule" rather than implying absence of benefit; add a compact table or paragraph classifying each of the 12 cells by power status: powered negative, underpowered unresolved, floored, missingness-limited, or refined. If possible without new GPU runs, compute and report per-cell MDEs in the main table.

Closure condition: The manuscript no longer rhetorically treats 0/12 as a powered global absence; each no-pass is tied to a resolution class, and any claim of absence is limited to powered/refined cells.

### [BLOCKER] The substitution design does not justify deployment-language claims about active UI sliders.

Location: Method: "The prompt condition uses the comparator instruction; the steering condition uses a neutral carrier instruction plus the latent intervention." Discussion: "a product control would ordinarily act in the presence of a user's instruction" and "Prompt-plus-steer evidence is pending." Interface-facing record: "the active control is withheld" and "the team pauses the slider."

Why it matters for IUI: The key interface question is whether a user-facing control should exist in a real interaction. A substitution assay answers whether steering replaces a prompt, not whether it helps as a slider alongside prompts. IUI reviewers will care about ecological validity.

Cheapest discriminating action: Recast all interface-action language as applying to "latent-only substitution controls" unless composition evidence is added. Add a short formal construct statement: what exact UI release decision the substitution rule does and does not govern.

Closure condition: No sentence implies that prompt-plus-slider controls should be withheld based solely on substitution evidence; the title/abstract/conclusion are aligned with substitution-only scope.

### [MAJOR] The pass criterion is statistically permissive relative to the declared meaningful floor.

Location: Section "Reported Qualification Rule": "it does not require the interval's lower bound to exceed \(\delta\)" and "A stricter release can raise \(\delta\) or require the lower bound to clear it."

Why it matters for IUI: A release rule for user-facing controls should have clear statistical semantics. Passing when the point estimate exceeds 0.05 but the CI includes effects below 0.05 can license controls with uncertain practical value.

Cheapest discriminating action: Add a sensitivity analysis showing whether any conclusions or positive controls change under the stricter lower-bound-clears-delta rule. If the framework intentionally uses a point-estimate floor, justify why this is appropriate for UI release.

Closure condition: The manuscript either adopts the stricter rule or explicitly reports how all relevant results behave under it and gives a convincing decision-theoretic rationale for the chosen rule.

### [MAJOR] Positive controls do not fully close the "insensitive assay" objection for the target axes.

Location: Results: "a predeclared positive control confirms that the no-pass outcome reflects the evidence, not an unsatisfiable gate"; Limitations: Stolfo/Phi-3 "validates the adjudication procedure rather than sensitivity on Qwen and Llama at the three console axes specifically."

Why it matters for IUI: If the assay cannot detect genuine improvements on deliberation/skepticism/uncertainty, then withholding controls based on the assay is premature.

Cheapest discriminating action: Move the narrower limitation into the main positive-control paragraph and abstract if possible. Explicitly separate three levels: gate satisfiability, latent pipeline liveness, and target-axis sensitivity. Do not claim the positive controls show the target assay is sensitive.

Closure condition: Positive controls are no longer used to over-answer the underpowered-null critique; target-axis sensitivity remains an open limitation unless directly tested.

### [MAJOR] Uncertainty results are important but parser/missingness confounds remain too central for the current wording.

Location: Method: missing confidence is imputed as 0.5, producing 1-Brier=0.75; Results: parseable-confidence rate "0.826 for steering and 0.445 for the prompt"; complete-case contrast -0.337 but adversarial all-generation bound [-0.478,+0.250].

Why it matters for IUI: An "uncertainty awareness" control is directly about calibrated confidence reporting. If prompt and steering conditions differ in whether confidence is parseable, the UI conclusion may reflect formatting compliance rather than epistemic behavior.

Cheapest discriminating action: Make the powered Qwen--CAA no-exclusion scorer result the only strong uncertainty claim, and clearly label the other uncertainty cells as frozen-score negative but unrepaired for missingness. Add a main-text caveat that uncertainty is a measurement construct, not a validated psychological uncertainty-awareness outcome.

Closure condition: The paper no longer generalizes uncertainty results beyond the scorer/missingness scope; all four cells' repair status is visible wherever the uncertainty headline is made.

### [MAJOR] Comparator provenance and fairness are insufficiently established.

Location: Limitations: "The prompt comparator is selected on DEV from a preregistered bounded candidate set. Its authorship independence, TEST blindness, and resource parity are not established"; Method: "best-of-set prompt is selected on DEV ... stands for the proficient user's realistic alternative."

Why it matters for IUI: The entire method is comparator-relative. If the strong prompt is not a fair or realistic proficient-user alternative, the central release decision changes.

Cheapest discriminating action: Add concise details in the Method about who authored the 16 prompts, whether authors saw TEST items/outcomes, and what budget the latent and prompt sides received. If unknown, state it in the main method rather than only limitations.

Closure condition: A reviewer can evaluate comparator fairness from the paper alone, and all claims are explicitly relative to that bounded comparator rather than "the" proficient-user prompt.

### [MAJOR] Everyday-user arm is exploratory but is used in abstract/conclusion in a way that may read as a negative result.

Location: Abstract: "Against even an ordinary prompt, steering shows no reliable quality gain (Qwen, exploratory)"; Section "Everyday-User Comparator": "Qwen-only ... exploratory and single-run ... not part of the confirmatory headline" and intervals crossing zero.

Why it matters for IUI: Everyday users are central to IUI. Underpowered exploratory nulls should not substitute for human evidence or a validated novice-prompt comparator.

Cheapest discriminating action: In abstract/conclusion, call this "exploratory and unresolved" rather than a negative quality finding, unless powered equivalence/negative evidence is available.

Closure condition: The everyday-user claim is consistently framed as preliminary context; the paper does not imply steering has been shown not to help everyday users.

### [MINOR] The paper sometimes relies on internal artifact language inappropriate for anonymous reviewer-facing manuscript.

Location: Method: "Exact values trace to committed result artifacts, preregistrations, analysis code, and machine-readable paper manifests"; table notes mention "supplementary artifact record."

Why it matters for IUI: Reviewers need enough information in the paper/supplement to assess claims without author-internal ledgers. Artifact traceability is good, but the paper must be self-contained.

Cheapest discriminating action: Ensure all claim-bearing numbers and protocol details needed for review are in the manuscript or anonymous supplement, not only in ledgers/manifests.

Closure condition: A reviewer can reproduce the argument from the manuscript and allowed supplement alone.

### [QUESTION] What is the rationale for the cell-level "at least two axes pass" aggregation?

Location: Section "Reported Qualification Rule": "labels a model--method cell positive when at least two axes pass, conditional when one passes, and negative when none pass."

Why it matters for IUI: A real UI control may be axis-specific; requiring two axes to label a cell positive may be arbitrary and may not match release decisions for single affordances.

Cheapest discriminating action: Explain why aggregation exists and whether interface action is per-axis or per-model-method. Consider removing the aggregate cell label if the record is per control/axis.

Closure condition: The aggregation rule is justified or clearly marked as descriptive and non-decisional.

### [MINOR] Immutable model revisions missing weaken reproducibility.

Location: Method: "Immutable upstream model revision hashes were not recorded"; Limitations: "Remaining reproducibility limits include immutable upstream model revision hashes and incomplete environment/data hashes."

Why it matters for IUI: The proposed evidence-tier logic depends on exact model/method/version. Missing hashes undermine the versioned-record principle.

Cheapest discriminating action: If retrievable from local cache or artifacts, add revision hashes. If not, move this limitation into the evidence-tier table as a visible field.

Closure condition: Evidence tiers either include exact revisions or explicitly mark revision identity as missing in each relevant record.

## 7. Overall assessment

Score range: 2.5-3.5 on a typical IUI 1-5 scale, leaning borderline/weak accept only if the paper is framed as a computational evaluation-method contribution rather than a validated interface paper.

Confidence: medium-high. I read the full manuscript source and the input table included in the paper. I did not inspect author-internal ledgers or artifacts.

Top rejection risks:
1. Underpowered/floored null: reviewers may view "0/12" as an assay-resolution failure, not a meaningful negative result.
2. Substitution-only construct: the evidence does not match prompt-plus-slider interface use.
3. No human validation: for IUI, the interface mapping and everyday-user convenience claims remain planned, not demonstrated.

Finding counts: 2 BLOCKER, 5 MAJOR, 2 MINOR, 1 QUESTION.
