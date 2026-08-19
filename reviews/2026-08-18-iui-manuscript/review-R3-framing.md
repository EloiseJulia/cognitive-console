# Review R3 (IUI): Framing, Scope, Honesty, Reproducibility, Positioning, Presentation

## 1. Scope / venue fit for ACM IUI, and fit risk

This is plausibly in scope for IUI because it studies when an internal model signal should become an interface control. The manuscript frames the decision as an intelligent-interface release problem: "whether such a control has earned an active role, rather than a read-only one," and later says the record is for "the interface designer or team deciding whether to release a control." That is a good IUI hook.

The fit risk is also real. The empirical core is computational and contains no user result: "The current study contains no human result; whether people understand the record, calibrate reliance, or make better control-granting decisions is the object of the planned human evaluation." For IUI, a paper about interface controls without evidence from users must make the interface contribution extremely crisp. The paper does some of this through the "five-field record" and worked UI-facing example, but several passages concede that the core mapping is not user-validated: "The direct mapping from computational result to blocking reason and interface action is an author-proposed design recommendation" and "Whether that rule is necessary or sufficient for an interface is a question for future user-facing evaluation." This is honest, but it creates a venue risk: reviewers may see a strong ML evaluation paper with an interface motivation rather than a full IUI contribution.

## 2. Contributions and central claims in my own words

My reading is that the paper contributes:

1. A per-control evaluation framework for internal-signal controls. Instead of asking whether latent steering changes outputs, it asks whether a named control deserves active UI status relative to a realistic user alternative. The paper states this as: "judge it against each user population's realistic alternative ... separate convenience from warranted quality gain ... and bind the result to an evidence tier."
2. A structured record that translates computational evidence into interface action. The record includes "READ, TRANSFER, the bounded prompt comparator, a calibration warning, and an evidence tier" and maps a control to "promoted, withheld, or kept read-only for stated reasons."
3. A negative worked case: CAA and ITI steering on Qwen and Llama do not beat a strong prompt in twelve model--method--axis tests. The authors summarize this as: "no latent control earns an advantage over a strong prompt on any of the twelve model--method--axis tests." The negative is bounded to "these techniques" and to a "substitution design."
4. A claim of assay credibility, not success: a "predeclared positive control" and a separate latent positive control are used to argue that the gate can say yes and is not merely impossible to pass.

The core conceptual claim is not that latent controls fail generally. It is that readable internal signals should not be promoted to active UI controls without comparator-bound behavioral evidence, and that in this worked substitution case the tested latent steering controls fail that bar.

## 3. Attack on framing

### 3.1 Over-claiming

**Over-claim A: the method is sometimes presented as broader than the evidence.** The abstract says "We contribute an evaluation method" for interfaces that "expose a model's internal signals as controls," and the conclusion says the method is intended for "which internal-signal control has earned an active role, for whom, and against what alternative." Later the paper narrows this: "we demonstrate them here only for steering, and advance their broader extension as a design argument." This caveat is good, but the broad opening and closing language may still read as a general method for internal-signal controls, while the empirical support is limited to CAA/ITI, two 7--8B models, and substitution rather than composition.

**Cheapest fix:** In the abstract and first contribution, explicitly say "a steering-instantiated evaluation method" or "a generalizable design pattern evaluated here only for steering." Closing condition: no reader can miss that non-steering controls are not empirically validated.

**Over-claim B: the positive-control language risks overstating what is validated.** The abstract says "a predeclared positive control confirms the gate can still qualify a control." In Results, the paper distinguishes a prompt-level positive control from a latent positive control on a different model/task: the prompt check "bears on decision-rule behavior, not latent-steering efficacy," and the latent control "validates the adjudication procedure rather than sensitivity on Qwen and Llama at the three console axes specifically." This nuance is excellent but too late. In the abstract, "positive control" could be read as validating the same latent steering setting.

**Cheapest fix:** Change the abstract to "positive controls at the decision-rule level and, on a different model/task, the latent-procedure level..." Closing condition: the abstract no longer implies sensitivity on the exact three axes.

**Over-claim C: the everyday-user claim is sharper than the evidence.** The abstract states: "Against even an ordinary prompt, steering shows no reliable quality gain (Qwen, exploratory), leaving its convenience... as the open question." The manuscript later says the average-prompt arm is "exploratory and single-run on a single model," and Appendix says the novice comparator "did not pass its anchor-calibration gate." This is honest, but the abstract wording "Against even an ordinary prompt" may sound like a general everyday-user conclusion rather than Qwen-only exploratory evidence.

**Cheapest fix:** In the abstract, say "In a Qwen-only exploratory ordinary-prompt arm..." Closing condition: everyday-user evidence is clearly not part of the confirmatory headline.

**Over-claim D: "independently audited" is not substantiated inside the manuscript.** Contribution 3 calls the case "fully worked, independently audited." The reproducibility section says the repository contains "independent audit summaries." But the manuscript itself does not report audit method, scope, findings, or what was audited. Since the review is based only on the manuscript, this reads as a provenance assertion without enough evidence.

**Cheapest fix:** Either remove "independently audited" from the contribution title or add a concise audit paragraph/table in the paper. Closing condition: the reader sees who/what/when/criteria/verdict at manuscript level, not only a repository pointer.

### 3.2 Over-defensiveness / self-undermining

The paper is unusually careful, sometimes productively so. The scope statement "It is not evidence that latent sliders are not worth building" prevents an invalid generalization. The substitution caveat "a slider that composes on top of a user instruction is out of scope" is essential.

However, the manuscript sometimes over-defends to the point of weakening its own contribution. Examples:

* "The direct mapping from computational result to blocking reason and interface action is an author-proposed design recommendation" followed by "Whether that rule is necessary or sufficient for an interface is a question for future user-facing evaluation." This is honest, but it can make the record sound like a speculative checklist rather than a contribution.
* "The rule also scores one thing---behavioral quality against a comparator---and not the effort, accessibility, discoverability, and willingness to use that make a slider attractive to a non-expert." This is important, but repeated limitations around everyday users make the Alex framing feel only partially served.
* "The finding is deliberately narrow" and "will date as steering improves" are true, but the paper should more confidently state what survives: the release-decision unit, not the negative result.

The strongest version is: this paper offers a rigorous computational gate for one necessary condition of active UI release, not a complete UI validation. That is a real IUI contribution. I recommend moving that sentence-level stance earlier and reducing repeated apologies.

## 4. Evidence / presentation audit

### Reproducibility and provenance

Strengths: the Method gives unusually concrete details: models, layers, hook convention, coefficient grid, item counts, bootstrap level, and qualification rule. The paper says "Exact values trace to committed result artifacts, preregistrations, analysis code, and machine-readable paper manifests" and that "Generated tables and figures rebuild from those artifacts without manual value edits." The paired estimand is clearly defined, and Table 2 is marked "Auto-generated... from frozen JSON artifacts."

Concerns: the reproducibility claims exceed what a paper reader can verify. The manuscript admits "Immutable upstream model revision hashes were not recorded" and "incomplete environment/data hashes in the earliest adjudication run's registry entries." It also says regenerating raw generations requires "reconstructing those model snapshots and software environments." For an IUI reproducibility claim, this should be framed as artifact reproducibility, not full computational reproducibility. The current sentence "committed JSON artifacts can regenerate the claim-bearing paper tables and figures without GPU access" is precise; the broader repository sentence should be softened.

### Exploratory vs confirmatory labeling

This is mostly strong. The manuscript marks READ as "exploratory," average-prompt as "exploratory and single-run on a single model," and novice prompts as "exploratory only." It also distinguishes frozen grid vs additive re-measurements: the 512-token deliberation re-measurement "does not overwrite the frozen grid." This is exemplary.

Weak point: the abstract compresses these statuses too aggressively. It says "the comparator-negative uncertainty axis is fully powered" and "Against even an ordinary prompt" without enough status markers. The paper should carry the exploratory/confirmatory distinction into the abstract and contribution bullets.

### Structure and length balance

The paper is readable but front-loaded with caveats and method details. Results are rich; Discussion is comparatively thin and partially repeats limitations. The Discussion sections contain useful conceptual synthesis, e.g., "The alternative is not 'ship a slider' or 'hide the representation'" and "Choosing a comparator is therefore choosing a population." These should be elevated earlier because they are the IUI contribution.

Appendices are not merely supplementary; the novice comparator materially affects the everyday-user framing. Because the abstract mentions ordinary/everyday users, the main text should include one sentence that the novice-style comparator is exploratory and failed calibration, not only send this to Appendix.

### Figures and tables

The figures/tables appear purposeful from their captions. Figure 1's caption clearly describes the decision flow. Figure 3's caption appropriately warns that it "does not show direct steer-versus-unsteered-baseline harm or resolve missingness." Table 2 is compact and useful.

Concerns: Table 2's "Gate / pass" column is visually repetitive (all "ok / fail") and may not help readers understand *why* each failed. Table "axis-actions" is more interpretable for IUI readers because it states blocking reasons and next evaluations. Consider foregrounding the axis-action table earlier or merging failure reason columns into Table 2.

Figure 4 / console record sounds important for IUI, but the caption emphasizes "artifact-derived cards" and "missing provenance link" rather than the user's/designer's decision. If this is the interface-facing artifact, the presentation should make the decision semantics more visually central.

### Related-work positioning

The related work is unusually honest. It explicitly says: "We claim neither the first prompt--steering comparison nor the first interpretability--actionability gap." The novelty table usefully distinguishes AxBench, Basu et al., Bo et al., Karny et al., and Mishra et al. The readability-vs-controllability / non-surjectivity gap is positioned through "Internal reach and behavioral advantage are distinct design quantities" and Mishra's "residual states outside a bounded prompt image."

Risk: the paper may over-index on very recent/preprint-like neighbors and under-explain the IUI tradition of control affordances, end-user programming, and intelligibility/actionability in interfaces. For IUI readers, the closest conceptual question is not only steering-vs-prompting but when an intelligent interface affordance warrants user agency. The current related work covers HCI transparency and neural-transparency systems, but could more explicitly connect to IUI evaluation norms: utility, effort, learnability, trust calibration, and decision quality.

## 5. Strongest reject case and strongest accept case

### Strongest reject case

This is a careful computational paper with an interface wrapper, but not yet a full IUI paper. The authors admit "The current study contains no human result" and that the interface mapping is "an author-proposed design recommendation" whose necessity/sufficiency awaits "future user-facing evaluation." The everyday-user motivation is central in the introduction, but the convenience side is explicitly untested: "what remains open is whether its convenience alone makes it preferable." The negative result is narrow: "specific to these techniques" and "substitution-only." Therefore, an IUI reviewer could reject because the central interface claim is not empirically validated with users and the computational result is too bounded to carry a full-paper IUI contribution alone.

### Strongest accept case

This paper addresses an important emerging IUI failure mode: making internal model signals into controls because they are legible or convenient. It provides a disciplined, reproducible, comparator-bound method that separates "convenient" from "warranted," and it reports a bounded negative rather than overselling latent steering. The writing is unusually honest: "READ is a diagnostic precondition, not behavioral evidence," "The current study contains no human result," and "a slider that composes on top of a user instruction is out of scope." The per-control record, comparator field, calibration warning, and evidence tier are concrete design artifacts that could improve how intelligent interfaces are evaluated. The negative case is valuable because it prevents an unjustified UI release and gives a template for future controls.

## 6. Ranked findings

### [BLOCKER-1] IUI contribution may be judged under-validated because the paper has no human/interface evaluation

**Location / quote:** Limitations: "The current study contains no human result"; Comparator section: "Whether that rule is necessary or sufficient for an interface is a question for future user-facing evaluation." Planned Evaluation says the study is future work.

**Why it matters for IUI:** IUI full papers usually need evidence about intelligent interface use, not only computational gate behavior. The paper's title and abstract center "everyday and proficient users," but no users are studied.

**Cheapest fix / discriminating action:** Reframe the contribution as a computational release-gate and record for interface designers, not an evaluated user interface. In title/abstract/intro, reduce user-evaluation implications and explicitly state "no user-facing validation is reported." If any small user-facing evidence exists, add it; if not, do not imply it.

**Closing condition:** A reviewer can summarize the paper as "a rigorous computational qualification method for IUI controls" rather than "an unvalidated UI study."

### [MAJOR-1] Abstract over-compresses evidence status and can mislead about positive controls and ordinary-prompt evidence

**Location / quote:** Abstract: "a predeclared positive control confirms the gate can still qualify a control"; "Against even an ordinary prompt, steering shows no reliable quality gain (Qwen, exploratory)." Results later says the prompt positive control is "not latent-steering efficacy," and the average-prompt arm is "exploratory and single-run on a single model."

**Why it matters for IUI:** The abstract is where reviewers calibrate scope. If the limits appear only later, the paper risks looking like it hides caveats.

**Cheapest fix / discriminating action:** Add status qualifiers in the abstract: prompt-level vs latent positive control; Qwen-only exploratory ordinary-prompt arm; no human result.

**Closing condition:** Every headline empirical statement in the abstract carries its model/task/status scope.

### [MAJOR-2] The broad "any internal-signal control" method claim is not sufficiently separated from the steering-only empirical demonstration

**Location / quote:** Contribution: "An evaluation method for internal-signal controls"; Discussion: "designed to extend to any interface that promotes an internal signal to a control"; caveat: "we demonstrate them here only for steering, and advance their broader extension as a design argument."

**Why it matters for IUI:** General interface methods require evidence across interface/control types or a clearly theoretical contribution. Here the empirical basis is steering only.

**Cheapest fix / discriminating action:** Rename the contribution to "a steering-instantiated evaluation method for internal-signal controls" and state which components are portable vs empirically demonstrated.

**Closing condition:** The paper no longer appears to empirically validate non-steering internal-signal controls.

### [MAJOR-3] "Independently audited" is asserted but not reported at manuscript level

**Location / quote:** Contribution 3: "A fully worked, independently audited case study." Limitations: repository contains "independent audit summaries."

**Why it matters for IUI:** Audit status is a credibility claim. If used as a contribution, the manuscript should include enough audit metadata for peer review.

**Cheapest fix / discriminating action:** Add a short audit table: audit target, auditor independence, checks, findings, unresolved issues, verdict. Or remove "independently audited" from the contribution framing.

**Closing condition:** Audit is either substantiated in the paper or not used as a selling point.

### [MAJOR-4] Everyday-user framing is compelling but currently only half answered

**Location / quote:** Intro: "For an everyday user who cannot easily write a strong prompt, a low-effort, accessible slider is attractive." Later: "The rule also scores one thing---behavioral quality against a comparator---and not the effort, accessibility, discoverability, and willingness to use"; "convenience half is left to the planned study."

**Why it matters for IUI:** Everyday-user value is fundamentally interactional. A Qwen-only average-prompt quality arm cannot answer whether the slider helps everyday users.

**Cheapest fix / discriminating action:** Make the proficient-user claim primary and move everyday-user claims to a clearly labeled research agenda, or add user evidence.

**Closing condition:** The paper's main contribution does not depend on unmeasured convenience/accessibility benefits.

### [MINOR-1] Table 2 reports all cells as "ok / fail" but does not make failure reasons salient

**Location / quote:** Table 2 column "Gate / pass" lists "ok / fail" for all rows; later Table "axis-actions" explains "bounded-equivalent," "floored," and "missingness-limited" reasons.

**Why it matters for IUI:** The paper's value is not just no-pass but structured blocking reasons. The main numeric table should teach that.

**Cheapest fix:** Add a failure-reason column or move axis-action summary immediately after Table 2.

**Closing condition:** A reader can infer the interface-relevant reason without reading several subsections.

### [MINOR-2] Discussion repeats limitations instead of foregrounding the design lesson

**Location / quote:** Discussion has strong lines: "The alternative is not 'ship a slider' or 'hide the representation'" and "Choosing a comparator is therefore choosing a population." But much space repeats scope caveats such as "the present experiment replaces that prompt with steering."

**Why it matters for IUI:** IUI reviewers need a crisp design takeaway.

**Cheapest fix:** Start Discussion with the design lesson and move repeated caveats to a compact "Scope" paragraph.

**Closing condition:** Discussion reads as synthesis, not a second limitations section.

### [MINOR-3] Reproducibility should distinguish artifact regeneration from raw rerun reproducibility

**Location / quote:** "committed JSON artifacts can regenerate the claim-bearing paper tables" vs "Immutable upstream model revision hashes were not recorded" and "reproducing raw generations therefore requires reconstructing those model snapshots."

**Why it matters for IUI:** Artifact claims are valuable but should not overstate full reproducibility.

**Cheapest fix:** Use terms like "paper-artifact reproducibility" and "raw-generation rerun limits."

**Closing condition:** The reproducibility claim exactly matches what can be regenerated.

### [QUESTION-1] Is the comparator really a "proficient user's realistic alternative"?

**Location / quote:** Method: "best-of-set prompt is selected on DEV... and stands for the proficient user's realistic alternative"; Limitations: "authorship independence, TEST blindness, and resource parity are not established" and "a proficient user who iterates... could do better still."

**Why it matters for IUI:** The user-population framing rests on this proxy. If the comparator is more like an author-engineered benchmark prompt, the interpretation shifts.

**Cheapest discriminating action:** Provide the prompt candidate provenance and selection budget in main text, or rename it "bounded strong prompt comparator" everywhere and avoid equating it too strongly with proficient users.

**Closing condition:** The proxy status is explicit and not rhetorically stronger than its provenance.

## 7. Overall numeric score range, confidence, top-3 rejection risks

**Score range:** 5.0--6.5 / 10 (borderline to weak accept depending on IUI tolerance for computational-method papers without human evidence).

**Confidence:** Medium-high. I reviewed the manuscript source and allowed table input, not author-internal ledgers or audits.

**Top-3 rejection risks:**
1. No human/interface evaluation despite IUI user/control framing.
2. Abstract and contribution language overgeneralize beyond steering-only, substitution-only evidence.
3. Everyday-user/convenience claims are motivating but not empirically answered.

## 10-line executive summary

1. Score range: 5.0--6.5 / 10.
2. Confidence: medium-high.
3. Venue fit: plausible IUI, but high fit risk without human evidence.
4. Strongest contribution: rigorous comparator-bound release gate for internal-signal controls.
5. Strongest empirical result: bounded negative for CAA/ITI on Qwen/Llama under substitution.
6. Top rejection risk #1: no user-facing validation of the interface record or convenience claims.
7. Top rejection risk #2: abstract over-compresses exploratory and positive-control scope.
8. Top rejection risk #3: broad internal-signal-control claims exceed steering-only evidence.
9. Finding counts: 1 BLOCKER, 4 MAJOR, 3 MINOR, 1 QUESTION.
10. Recommendation: revise framing to a computational IUI release-gate paper and surface limits in the abstract.
