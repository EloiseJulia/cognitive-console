# Writing Guardrails — Current Evidence State

Source of author adjudication: `AUTHOR_ADJUDICATION_2026-08-11.md`.

## Required Positioning

Use this as the current substantive center:

> We propose a comparator-bound qualification procedure for active latent controls and instantiate it with a DEV-selected prompt comparator drawn from a preregistered bounded candidate set. The current CAA/ITI application is a worked procedural classification, not a validated assay, inter-rater-validated rubric, or general steering verdict.

The problem is grounded in real interface precedents: Bo et al. prototype direct linear-factor steering controls, while Golden Gate Claude provides a public research demonstration of an internally modified model. Describe these as a research-interface trajectory, not deployed product maturity or a public Anthropic slider.

## Allowed Terms

- preregistered bounded candidate set;
- DEV-selected prompt comparator;
- executable qualification procedure;
- worked application / worked instantiation;
- procedural no-pass classification;
- study-specific comparator;
- author-proposed five-field record;
- unresolved manipulation validity;
- no passing latent behavioral positive control;
- no blinded independent state assignment.

## Canonical Terminology

| Concept | Canonical expression | Do not use as a synonym |
|---|---|---|
| Representational evidence | READ evidence | CONTROL evidence |
| Behavioral evidence | TRANSFER evidence | behavioral CONTROL evidence |
| Interface authorization | CONTROL permission | TRANSFER permission |
| Test unit | model–method–axis test | axis-by-method-model test |
| Descriptive result pattern | evidence profile | evidence state |
| Formal interface classification | affordance state | evidence profile / evidence tier |
| Formal states | *Diagnostic-only*, *Unresolved*, *Unstable*, *Eligible* | compound variants such as unresolved-untested or unstable-no-pass |
| Prompt search space | preregistered bounded candidate set | bounded comparator |
| Selected alternative | DEV-selected prompt comparator | DEV-selected prompt set |
| Full workflow | qualification procedure | qualification criterion |
| Equation-level decision | qualification rule | qualification procedure |
| Individual predicate | criterion | gate / requirement / condition |
| End-to-end empirical system | assay | rule / record |
| Quality predicate | coherence criterion | coherence gate / bound / condition |
| Model–method order | Qwen–CAA | CAA–Qwen / Qwen/CAA |
| Follow-up analysis | format-and-missingness recheck | format recheck |
| Reporting metric | parseable-confidence rate | format compliance |
| Missing-data sensitivity | missingness bounds | format bounds |
| Technical candidate | active latent control | active affordance |
| UI realization | control affordance | active latent control, when referring to the widget |
| Assay check | behavioral positive control | positive affordance |
| Effect threshold | point-estimate floor | effect floor / margin |
| Composition condition | prompt-plus-steer | prompt+steer in visible prose |
| Classification noun/adjective | no-pass | non-pass |
| Scope/provenance field | evidence tier | evidence state |

## Forbidden Terms and Claims

### Comparator

- blind / TEST-blind;
- fair;
- strong, unless explicitly defined without implying fairness;
- global-best / globally optimal;
- exhaustive;
- budget-optimal;
- equivalent to the best prompt a user could ever write.

### Validation

- assay validated / validated assay;
- end-to-end manipulation validated;
- known-positive latent control passed;
- inter-rater validated;
- independently reproducible state assignment;
- validated rubric;
- five fields are necessary or sufficient.

### Empirical Interpretation

- latent steering fails;
- steering is equivalent to prompting;
- all twelve controls should be withheld;
- 0/12 diagnoses transfer failure;
- uncertainty is grid-wide resolved;
- split-seed consistency is replication;
- CAA READ evidence transfers to ITI;
- `alpha <= 24` is a common injected-norm bound.

### Human and Interface Claims Before Pending Results

- users understand the contract;
- the record improves calibrated reliance;
- the state machine improves decisions;
- the console is usable, preferred, or beneficial;
- warnings reduce over-trust;
- any predicted positive, null, adverse, or mixed human-study outcome.

## Same-Sentence Caveat Rules

| Claim surface | Required caveat in the same sentence |
|---|---|
| 0/12 / no tested cell qualified | reported rule; tested models/methods/axes; no passing latent behavioral positive control |
| comparator result | identify the declared comparator or use “the comparator” after its Method definition; do not repeat the full provenance list |
| five-field/state assignment | at first definition or a new worked assignment, identify the mapping as author-proposed and not independently reproduced; ordinary later mentions need not repeat it |
| uncertainty contrast | one-cell complete-case support; bounds cross zero; three cells unrechecked |
| prompt-plus-steer | pending until verified results arrive |
| human effect | no result as of 2026-08-11; pending packet controls integration |

## Disclaimer Placement

- Define the comparator once in Introduction as a DEV-selected prompt drawn from a preregistered bounded set.
- State the full provenance caveat once in the Method comparator subsection.
- State the consequence once in Limitations: conclusions are relative to this comparator and may change with another candidate set or budget.
- In Results, the worked record, Discussion, and Conclusion, use “the comparator” unless disambiguation is necessary.
- Do not repeat lists such as “blind, fair, exhaustive, globally optimal” across sections. Repetition is not additional rigor and should be treated as a prose defect.
- State the assignment limitation at the first state-vocabulary definition, the worked mapping, and Limitations. Do not repeat it in captions, contribution bullets, scenario prose, Discussion summaries, or Conclusion.

## Rule and Mapping Separation

- The reported qualification rule produces the 0/12 pass/no-pass result.
- The four-state affordance vocabulary is a post hoc design synthesis of observed evidence profiles.
- The state mapping does not generate, validate, or explain the 0/12 result.
- Present the mapping as a hypothesis for interface evaluation, not as preregistered or validated rubric output.

## Pending-Result Rule

The human and prompt-plus-steer studies expected by 2026-08-20 may strengthen, weaken, redirect, or invalidate the current arc. Neither study can be written as successful in advance.
