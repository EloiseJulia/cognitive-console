# Review R2 (IUI): Contribution, Novelty, and Significance

## 1. Scope / venue fit for IUI and fit risk

This submission is adjacent to IUI, but the venue fit is risky in its current form. The paper's motivating object is explicitly an interface decision: "whether such a control has earned an active role, rather than a read-only one" (Abstract) and "what behavioral evidence turns such a representation into a warranted control?" (Related Work, `from-legible-representations-to-behavioral-actionability`). It also speaks to intelligent interfaces that expose latent/internal model signals: "Interfaces increasingly expose a model's internal signals as controls" (Abstract), and it names IUI-relevant precedents such as steering interfaces and neural-transparency interfaces.

However, the actual evidence is almost entirely computational. The paper states: "The current study contains no human result; whether people understand the record, calibrate reliance, or make better control-granting decisions is the object of the planned human evaluation" (`human-evidence-ethics-and-future-validation`). For IUI, this is a major fit risk because the central contribution is an interface-facing release method and record, yet there is no evidence that designers can use the record, that users understand it, that it calibrates reliance, or that the proposed mapping improves interface decisions. The paper even concedes: "The direct mapping from computational result to blocking reason and interface action is an author-proposed design recommendation. Whether that rule is necessary or sufficient for an interface is a question for future user-facing evaluation" (`comparator-substitution-and-interface-construct`).

The submission may fit IUI if positioned as a methods/theory paper for evaluating intelligent-interface affordances, but as written it reads more like an ML/HCI-adjacent evaluation protocol plus a negative steering benchmark than a fully validated IUI contribution. The fit risk is heightened by the substitution-only experiment: "the present experiment replaces that prompt with steering, whereas a user-facing slider normally acts on top of an instruction" (`why-the-comparator-changes-the-interface-claim`). This gap makes the interface claim less directly actionable for real IUI systems.

## 2. Independent restatement of contributions and central claims

In my words, the paper argues the following:

1. **Evaluation method.** The authors propose a per-control qualification method for deciding whether a readable internal model signal should be exposed as an active interface control. The method compares the control against a user-population-specific realistic alternative, not against no control. The paper states this as: "judge the control against each user population's realistic alternative---a strong best-of-set prompt for a proficient user, an average prompt for a non-expert---rather than against `no control'" (Introduction), and later formalizes this via READ, TRANSFER, bounded prompt comparator, calibration warning, and evidence tier (`five-field-qualification-record`).

2. **Interface-facing record.** The paper proposes a five-field record intended to translate computational evidence into a release action. The claimed mapping is: "READ support makes the representation a read-only diagnostic candidate within this evidence tier. An active control passes the computational gate within this evidence tier only when READ is supported and the reported TRANSFER rule passes" (`five-field-qualification-record`). The record is supposed to prevent three bad substitutions: "READ for TRANSFER, absolute output change for comparison against the declared alternative, and evidence from one tier for another" (`from-evaluation-output-to-interface-eligibility`).

3. **Worked negative case study.** The authors apply this method to CAA and ITI steering on Qwen2.5-7B and Llama-3-8B across deliberation, skepticism, and uncertainty. The central empirical result is that "none of the twelve tests beats the DEV-selected best-of-set prompt under the reported rule" (`against-the-experts-ceiling-no-latent-arm-wins`). They further claim the gate is not impossible because "a predeclared positive-control check confirms that the no-pass outcome reflects the evidence, not an unsatisfiable gate" (`against-the-experts-ceiling-no-latent-arm-wins`).

4. **Conceptual claim.** The paper frames the broader lesson as a readability--controllability gap: "a legible direction can be real yet behaviorally inert under these interventions" (`an-honest-negative-not-a-blind-assay`) and "READ supports inspection without presuming actionability" (`read-supports-inspection-without-presuming-actionability`).

## 3. Novelty and significance attack by contribution

### Contribution 1: Evaluation method for internal-signal controls

**What seems genuinely new:** The paper is careful about its novelty claim. It explicitly says: "We claim neither the first prompt--steering comparison nor the first interpretability--actionability gap. Our contribution is to combine these into an evaluation method for a single control's release decision" (`positioning-summary`). The per-affordance unit of analysis, user-population-specific comparator, evidence tiering, and release-decision framing are a plausible new combination for IUI.

**Nearest prior work pressure:** The manuscript itself identifies close neighbors: AxBench compares prompting and steering; Bo et al. evaluate steering interfaces with a prompt baseline; Karny et al. evaluate neural-transparency interfaces; model cards/datasheets structure claims; and Basu et al. study representation-actionability gaps. The novelty therefore depends almost entirely on "the unit of analysis and the binding, not any single ingredient" (`positioning-summary`). A skeptical PC could argue that this is a repackaging of good evaluation hygiene: choose a comparator, predefine a threshold, report uncertainty, and scope claims. The paper needs to show that this combination changes interface decisions in a way prior frameworks do not.

**Significance concern:** The method's core release rule is author-chosen: "the specific values (delta=0.05, the coherence ratio, and the two-axis aggregation) are this application's settings, not part of the portable procedure" (`reported-qualification-rule`). That makes the portable contribution somewhat abstract: if each future team chooses its own comparator, threshold, coherence gate, and tier boundaries, what exactly is the reusable IUI method beyond a checklist? The appendix checklist is inspectable, but it is not yet validated as a decision procedure.

### Contribution 2: Five-field record connecting evaluation to interface action

**What seems genuinely new:** The five-field record is the strongest IUI-facing contribution. It explicitly records READ, TRANSFER, comparator, calibration warning, and evidence tier, and it maps failures to withhold/read-only actions. The worked Qwen--CAA uncertainty record is concrete: "The active control is therefore withheld for this record while the comparator and blocking reason remain visible" (`worked-record-qwencaa-uncertainty`). This is a useful design pattern for preventing interpretability artifacts from being oversold as controls.

**Nearest prior work pressure:** The paper admits that documentation frameworks already "bind claims to provenance, evaluation, and scope" and that audit frameworks provide staged development records (`mechanistic-interpretability-interfaces-and-human-evidence`). The claimed novelty is applying this accountability move "at the control-affordance level". That is plausible, but the current paper does not demonstrate that this record is usable by interface designers or legible to users.

**Significance concern:** The interface-facing section remains mostly speculative. It says "An interface that exposes this record would need to keep the relative comparison visible" (`display-requirements-implied-by-the-record`) and includes an "Illustrative Design Scenario" in which "the team pauses the slider" (`illustrative-design-scenario`). But there is no designer study, no user study, no deployed prototype evaluation, and no evidence that the record improves decisions. The manuscript itself says the checklist "does not validate the interface mapping with people" (`author-proposed-record-checklist`). For IUI, this is a major weakness because the proposed contribution is not just a statistical record; it is an interface governance artifact.

### Contribution 3: Worked, independently audited negative case study

**What seems genuinely new:** The negative result is careful and bounded. The main table reports 12 steer-minus-prompt failures (`tab:c2-delta-4cell`), and the discussion repeatedly avoids overclaiming: "The verdict reported here is about CAA and ITI on two 7--8B models, and it will change as steering methods improve" (`what-transfers-beyond-this-case`). This honesty is valuable.

**Nearest prior work pressure:** The paper's own related work notes that AxBench already reports prompting strongly outperforming steering in aggregate: "mean overall steering score of 0.894 for Prompt and 0.239 for DiffMean" (`from-legible-representations-to-behavioral-actionability`). Thus the empirical observation that simple CAA/ITI do not beat a strong prompt may not surprise the community. A skeptical PC may reduce the case study to "a slider didn't work," especially because the paper states "no tested latent control shows an incremental quality advantage" and the tested intervention is "substitution-only" (`comparator-substitution-and-interface-construct`).

**Significance concern:** The paper tries to rescue significance by saying the contribution is the method, not the negative. But then the worked application must convincingly demonstrate method utility. Some cells are underpowered or measurement-limited: skepticism MDEs "far exceed the 0.05 point-estimate floor" (`transfer-produces-axis-specific-reasons-and-next-steps`), deliberation ITI cells "remain 64-token--floored placeholders" (`transfer-produces-axis-specific-reasons-and-next-steps`), and uncertainty has missingness issues where "the sign is therefore not identified under unrestricted missingness" (`comparator-choice-changes-the-calibration-reading`). These limitations make the case study less clean as a demonstration of the method's discriminative value for real interface decisions.

### Conceptual framing: readability vs behavioral controllability gap

**What seems genuinely new:** The phrase and framing are useful: "READ supports inspection without presuming actionability" (`read-supports-inspection-without-presuming-actionability`) and "a legible direction can be real yet behaviorally inert" (`an-honest-negative-not-a-blind-assay`). This is a valuable warning for IUI/HCI systems that convert interpretability artifacts into controls.

**Novelty pressure:** The paper cites prior work that already motivates representation-actionability gaps, including Basu et al., Mishra et al., and Karny et al. The authors therefore need to clarify whether the conceptual contribution is a new theory, a design principle, or simply an operationalization. As written, it is most defensible as an operationalized design principle, not a new conceptual theory.

## 4. Significance audit

### Does the community gain a reusable method or a one-off negative?

The community gains a promising evaluation template, but its reusability is not yet proven. The portable pieces are clear: "a declared comparator, outcome, uncertainty rule, floor, and coherence gate" (`reported-qualification-rule`) and a record that binds evidence to "model, method, axis, task, layer, protocol, and evidence status" (`five-field-qualification-record`). That is useful.

However, the empirical work mostly shows that this particular grid fails. The most IUI-relevant payoff would be evidence that the five-field record changes design decisions or improves user/designer calibration. The paper does not provide that. It says: "Whether people understand the record, calibrate reliance, or make better control-granting decisions is the object of the planned human evaluation" (`human-evidence-ethics-and-future-validation`). Thus, for IUI, the reusable-method claim remains under-evidenced.

### Is the missing user study fatal or acceptable?

For a full IUI paper, the absence of any human/user study is close to fatal unless the paper is explicitly framed as a computational evaluation method paper with limited interface claims. The manuscript currently makes strong interface-facing claims: "The record's user is the interface designer or team deciding whether to release a control" (`from-evaluation-output-to-interface-eligibility`), and it offers a concrete interface action: "the team pauses the slider" (`illustrative-design-scenario`). Yet it also states that "The current study contains no human result" (`human-evidence-ethics-and-future-validation`).

I would not require a user study for every IUI methods paper, but here the central object is an intelligent interface affordance and a proposed interface-facing record. At minimum, the paper needs either (a) a designer-facing evaluation of the record/checklist, (b) a user-facing study of comprehension/reliance/convenience, or (c) a much narrower claim that this is only a computational pre-release gate, not an IUI-validated interface method. The planned study cannot substitute for results.

### Are design implications concrete and grounded?

Partly. The strongest grounded implication is: do not expose a latent slider as an active quality control merely because READ is supported or outputs move. This is directly supported by the text: "promoting a control on READ or on output movement alone" is blocked by the record (`from-evaluation-output-to-interface-eligibility`). The worked record also grounds a concrete action: "active control is withheld" while READ remains "a read-only diagnostic candidate" (`worked-record-qwencaa-uncertainty`).

But the broader implications are speculative. The paper says the record should show comparator, warning, and evidence tier (`illustrative-design-scenario`; `display-requirements-implied-by-the-record`), but it does not evaluate whether this display is understandable, actionable, or burdensome. The planned study measures "effort," "accessibility," "discoverability," and "willingness to use" (`planned-evaluation`), which are exactly the missing IUI evidence.

## 5. Strongest reject case and strongest accept case

### Strongest reject case

This is not yet a full IUI contribution. The paper proposes an interface-facing method but has "no human result" (`human-evidence-ethics-and-future-validation`). Its key interface mapping is admitted to be "an author-proposed design recommendation" whose necessity/sufficiency remains future work (`comparator-substitution-and-interface-construct`). The empirical case is a bounded computational negative on a substitution-only setup, while "a user-facing slider normally acts on top of an instruction" (`why-the-comparator-changes-the-interface-claim`). Several result cells are underpowered, floored, or missingness-sensitive. Prior work already suggests prompting can outperform steering (`from-legible-representations-to-behavioral-actionability`). Therefore, a skeptical IUI PC could see this as an ML evaluation protocol plus a negative result, with insufficient user/interface validation for full-paper acceptance.

### Strongest accept case

The paper addresses an important emerging IUI problem: interpretability artifacts are increasingly exposed as controls, and the field lacks a rigorous per-control release gate. It contributes a careful, transparent, and reusable qualification record that separates READ from TRANSFER, comparator-relative benefit from output movement, and convenience from warranted quality gain. The authors are unusually honest about limitations: "What is new is the unit of analysis and the binding, not any single ingredient" (`positioning-summary`), and "The verdict reported here is about CAA and ITI on two 7--8B models" (`what-transfers-beyond-this-case`). The negative result is valuable because it operationalizes a real design risk: "a legible direction can be real yet behaviorally inert" (`an-honest-negative-not-a-blind-assay`). If IUI is willing to accept method papers without human studies when the interface decision is computationally grounded, this is a thoughtful and potentially influential submission.

## 6. Ranked findings

### [BLOCKER 1] No human/user/designer evidence for an interface-facing IUI contribution

- **Location / quote:** `human-evidence-ethics-and-future-validation`: "The current study contains no human result"; `comparator-substitution-and-interface-construct`: "Whether that rule is necessary or sufficient for an interface is a question for future user-facing evaluation"; `from-evaluation-output-to-interface-eligibility`: "The record's user is the interface designer or team deciding whether to release a control."
- **Why it matters for IUI:** The claimed contribution is not only a computational metric; it is a release method and interface-facing record. IUI reviewers will expect evidence that the record/action is usable, understandable, or improves intelligent-interface decisions.
- **Cheapest discriminating/repair action:** Add a small but real study with target users of the record (e.g., interface designers/AI practitioners) comparing decisions with vs. without the five-field record on several control-release scenarios; or add the planned everyday/proficient user study if already feasible.
- **Closing condition:** The paper reports empirical evidence that people can understand and use the record, or the claims are narrowed throughout to a computational pre-release assay with no claim of validated IUI/interface actionability.

### [BLOCKER 2] Substitution-only experiment does not match the normal slider use case

- **Location / quote:** `two-prompt-comparators-and-substitution-design`: "The core experiment is a substitution design"; `comparator-substitution-and-interface-construct`: "a product control would ordinarily act in the presence of a user's instruction"; `illustrative-design-scenario`: "a slider that acts on top of a user instruction would need composition evidence the present evaluation does not provide."
- **Why it matters for IUI:** The motivating interface is a slider users manipulate while interacting with an assistant. If real use is prompt-plus-slider, then prompt-vs-slider substitution may reject controls that are useful as complements.
- **Cheapest discriminating/repair action:** Add a minimal prompt-plus-steer composition arm for the worked uncertainty control and one additional axis, or reframe the entire paper as evaluating only latent-only replacement controls.
- **Closing condition:** Either composition evidence is reported, or all interface examples/claims explicitly restrict themselves to substitution controls and remove implications about ordinary product sliders.

### [MAJOR 1] Novelty over prior steering/interface/evaluation work depends on a combination claim that needs sharper differentiation

- **Location / quote:** `positioning-summary`: "What is new is the unit of analysis and the binding, not any single ingredient"; `tab:novelty-neighbors`: Bo et al. already provide "SELECT, CALIBRATE, and LEARN interfaces, an unscaffolded PROMPT baseline, and exploratory within-subject user evidence"; AxBench already provides "a method-level benchmark comparing prompting with multiple representation-level interventions."
- **Why it matters for IUI:** If the novelty is only packaging existing comparator/evidence practices into a checklist, significance may be judged incremental.
- **Cheapest discriminating/repair action:** Add a concise contrast table that maps each prior work to the exact missing decision fields and shows at least one concrete decision prior methods would get wrong or leave ambiguous.
- **Closing condition:** A skeptical reader can state a unique methodological capability of this paper beyond "compare to prompt and report uncertainty."

### [MAJOR 2] Mostly-negative case study risks reading as "a slider didn't work"

- **Location / quote:** Abstract: "naive latent steering beats the strong prompt on none of the twelve tests"; `against-the-experts-ceiling-no-latent-arm-wins`: "moving the slider buys no warranted quality gain over an instruction"; `what-transfers-beyond-this-case`: "The verdict reported here is about CAA and ITI on two 7--8B models."
- **Why it matters for IUI:** Negative results can be valuable, but the IUI contribution must be more than a failed control, especially when the studied techniques are narrow and may soon date.
- **Cheapest discriminating/repair action:** Foreground the method's decision utility by adding a side-by-side example of naive release criteria (READ-only/output-change) vs. the proposed record producing different interface actions.
- **Closing condition:** The reader can see the case study as demonstrating a reusable decision method, not merely reporting failure of CAA/ITI.

### [MAJOR 3] Everyday-user contribution is unresolved despite being central to the framing

- **Location / quote:** Introduction frames Alex, "an everyday user," for whom "nudging a slider is far easier"; `everyday-user-comparator`: "Whether its convenience nonetheless makes it preferable for the everyday user is the question the planned study addresses"; `comparator-substitution-and-interface-construct`: the rule does not score "effort, accessibility, discoverability, and willingness to use."
- **Why it matters for IUI:** IUI/HCI significance often turns on user experience, not just behavioral quality. The everyday-user side is introduced as a co-equal standard but remains mostly future work.
- **Cheapest discriminating/repair action:** Either add the planned study or demote the everyday-user claims to motivation and keep the main contribution focused on proficient-user quality qualification.
- **Closing condition:** The paper no longer claims to answer the everyday-user control question without human evidence, or it supplies such evidence.

### [MAJOR 4] Several empirical cells are underpowered, floored, or measurement-limited, weakening the demonstration

- **Location / quote:** `transfer-produces-axis-specific-reasons-and-next-steps`: skepticism MDEs "far exceed the 0.05 point-estimate floor"; deliberation ITI cells "remain 64-token--floored placeholders"; `comparator-choice-changes-the-calibration-reading`: uncertainty all-generation bound "crosses zero" and "no grid-wide resolved uncertainty effect follows."
- **Why it matters for IUI:** The method's value is to make robust release decisions. If many cells are unresolved or artifact-limited, the worked application demonstrates caution but not a clean evaluation.
- **Cheapest discriminating/repair action:** Reduce headline emphasis on "none of the twelve" and restructure results around resolved vs. unresolved blocking reasons; optionally complete the ITI 512-token deliberation remeasurement and missingness repair for all uncertainty cells.
- **Closing condition:** The headline no-pass cannot be misread as twelve equally informative negatives; unresolved cells are clearly separated from resolved comparator-negative cells.

### [MAJOR 5] Interface-facing record is not evaluated as an artifact

- **Location / quote:** `author-proposed-record-checklist`: "The checklist makes the proposed procedure inspectable; it does not validate the interface mapping with people"; `display-requirements-implied-by-the-record`: "An interface that exposes this record would need to keep the relative comparison visible."
- **Why it matters for IUI:** The record/checklist is the most novel IUI artifact, but its usability, comprehensibility, and decision impact are assumed.
- **Cheapest discriminating/repair action:** Conduct a lightweight expert walkthrough or heuristic evaluation with interface designers using the record to make release decisions.
- **Closing condition:** The paper contains evidence, even preliminary, that the record supports its intended user.

### [MINOR 1] Positive controls validate parts of the pipeline, but not the target IUI axes

- **Location / quote:** `assay-validity-and-statistical-resolution`: latent positive control "uses a different model and task than the headline axes" and "validates the adjudication procedure rather than sensitivity on Qwen and Llama at the three console axes specifically."
- **Why it matters for IUI:** The strongest defense against "dead assay" does not prove sensitivity for the actual proposed controls.
- **Cheapest repair action:** Move this caveat earlier into the Results when the positive control is first used rhetorically.
- **Closing condition:** Readers cannot overinterpret the positive control as validating the target axes.

### [MINOR 2] The manuscript still contains pending-slot comments that reduce submission polish

- **Location / quote:** Several visible source comments in the manuscript include `% PENDING_HUMAN_STUDY_SLOT`, `% PENDING_PROMPT_STEER_SLOT`, `% PENDING HUMAN RESULTS`, and `% PENDING HUMAN DISCUSSION`.
- **Why it matters for IUI:** If these appear in source only, not PDF, they are not reviewer-visible in compiled form; but they signal an unfinished paper state and correspond to substantive missing evidence.
- **Cheapest repair action:** Remove source-level pending markers before submission and ensure limitations plainly state absent evidence.
- **Closing condition:** The submitted source/PDF contains no internal placeholders.

### [QUESTION 1] What is the intended IUI review category: method paper, empirical paper, or design artifact paper?

- **Location / quote:** CCS says "Empirical studies in HCI"; Abstract says "We contribute an evaluation method"; `interface-facing-qualification-record` proposes a design record; `human-evidence-ethics-and-future-validation` says no human result.
- **Why it matters for IUI:** Evaluation expectations differ by category. The paper currently invokes all three but fully satisfies only the computational-method category.
- **Cheapest repair action:** State the intended contribution type explicitly in the introduction and align evidence/claims accordingly.
- **Closing condition:** Reviewers know what standard to apply.

## 7. Overall score range, confidence, and top-3 rejection risks

**Overall numeric score range:** 2.0--2.5 / 5 (lean reject to weak reject for IUI full paper in current form). If IUI treats this as a computational methods paper and does not require user-facing validation, it could rise to borderline; as an IUI interface contribution, it is under-evidenced.

**Confidence:** High. The manuscript is explicit about its missing human evidence and substitution-only scope, which makes the main venue-fit and significance risks clear.

**Top-3 rejection risks:**
1. No human/user/designer evidence despite an interface-facing contribution and IUI venue expectations.
2. Substitution-only prompt-vs-steer experiment does not match typical prompt-plus-slider interface use.
3. Novelty/significance may be judged as a careful but incremental evaluation checklist plus a narrow negative CAA/ITI result.

## 10-line executive summary

1. Score range: 2.0--2.5 / 5.
2. Confidence: High.
3. Recommendation tendency: Lean/weak reject for IUI full paper as currently framed.
4. Main strength: Careful per-control evaluation framing separating READ from TRANSFER.
5. Main strength: Honest bounded negative with explicit comparator and evidence tiering.
6. Top rejection risk #1: No human/user/designer evidence for an interface-facing method.
7. Top rejection risk #2: Substitution-only setup mismatches normal prompt-plus-slider use.
8. Top rejection risk #3: Novelty may read as existing evaluation hygiene plus a failed slider.
9. BLOCKER count: 2.
10. MAJOR count: 5.
