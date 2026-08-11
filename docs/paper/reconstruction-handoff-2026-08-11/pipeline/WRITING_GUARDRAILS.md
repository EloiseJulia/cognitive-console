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
- computational result → structured evidence/blocking reason → interface eligibility/action;
- read-only diagnostic candidate within this evidence tier;
- active control withheld;
- active control passes the computational gate within this evidence tier;
- unresolved manipulation validity;
- no passing latent behavioral positive control;

## Canonical Terminology

| Concept | Canonical expression | Do not use as a synonym |
|---|---|---|
| Representational evidence | READ evidence | CONTROL evidence |
| Behavioral evidence | TRANSFER evidence | behavioral CONTROL evidence |
| Interface decision | interface eligibility / interface action | deployment readiness |
| Test unit | model–method–axis test | axis-by-method-model test |
| Descriptive result pattern | evidence profile | evidence state |
| Computational output | READ/TRANSFER status and qualification result | affordance state |
| Interpretation | structured evidence / blocking reason | badge / formal taxonomy |
| Read-only action | read-only diagnostic candidate within this evidence tier | Diagnostic-only |
| Active-control action | active control withheld / active control passes the computational gate within this evidence tier | Unresolved / Unstable / Eligible |
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
- the record or interface mapping improves decisions;
- the console is usable, preferred, or beneficial;
- warnings reduce over-trust;
- any predicted positive, null, adverse, or mixed human-study outcome.

## Same-Sentence Caveat Rules

| Claim surface | Required caveat in the same sentence |
|---|---|
| 0/12 / no tested cell qualified | reported rule; tested models/methods/axes; no passing latent behavioral positive control |
| comparator result | identify the declared comparator or use “the comparator” after its Method definition; do not repeat the full provenance list |
| five-field/interface mapping | at first definition, identify it as a proposed computational eligibility mapping and not evidence of user benefit or deployment readiness |
| uncertainty contrast | one-cell complete-case support; bounds cross zero; three cells unrechecked |
| prompt-plus-steer | pending until verified results arrive |
| human effect | no result as of 2026-08-11; pending packet controls integration |

## Disclaimer Placement

- Define the comparator once in Introduction as a DEV-selected prompt drawn from a preregistered bounded set.
- State the full provenance caveat once in the Method comparator subsection.
- State the consequence once in Limitations: conclusions are relative to this comparator and may change with another candidate set or budget.
- In Results, the worked record, Discussion, and Conclusion, use “the comparator” unless disambiguation is necessary.
- Do not repeat lists such as “blind, fair, exhaustive, globally optimal” across sections. Repetition is not additional rigor and should be treated as a prose defect.
- State the human-evidence limitation at the first interface-mapping definition and once in Limitations. Do not repeat it in captions, contribution bullets, scenario prose, Discussion summaries, or Conclusion.

## Direct Hybrid Mapping

- The reported qualification rule produces the 0/12 pass/no-pass result.
- The manuscript then preserves the structured evidence or blocking reason before giving a record-specific interface action.
- READ support makes a representation a read-only diagnostic candidate within the exact evidence tier.
- An active control passes the computational gate within the exact evidence tier only when READ is supported and TRANSFER passes; otherwise the active control is withheld.
- READ unsupported/not evaluated, TRANSFER not tested/not evaluable/no-pass/pass, interval includes zero, comparator-negative, below-floor, coherence failure, and missingness-limited are reasons or computational statuses, not formal interface states.
- Do not classify all 0/12 as withheld scientific states. The illustrated slider action applies only to the worked Qwen–CAA uncertainty record.

## Pending-Result Rule

The human and prompt-plus-steer studies expected by 2026-08-20 may strengthen, weaken, redirect, or invalidate the current arc. Neither study can be written as successful in advance.
