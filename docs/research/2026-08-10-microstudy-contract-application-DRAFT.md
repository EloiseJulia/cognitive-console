# DRAFT Preregistration: Contract Legibility/Application Micro-Study

- **Status:** `DRAFT — NOT FROZEN — NOT AUTHORIZED FOR HUMAN DATA`
- **Date:** 2026-08-10
- **Study type:** exploratory formative micro-study
- **Owner boundary:** owner handles ethics and recruitment; current authorization covers materials and local web engineering only
- **Protocol spec:** [`../specs/microstudy-contract-application.md`](../specs/microstudy-contract-application.md)

## 1. Purpose and scope

This micro-study estimates whether semantic grouping of an interface-evaluation contract helps technical GenAI users apply the contract's four routing states to simulated records. It does not study calibrated reliance, user benefit, trust, productivity, deployment outcomes, or model behavior.

The study is intentionally small (`N ≈ 20`), within-subject, desktop-only, and approximately 10 minutes. Results are exploratory and formative. A null result is inconclusive at this sample size.

## 2. Design

- Conditions:
  - `C`: Contract UI
  - `F`: Info-Matched Flat Panel
- 10 scored trials: 5 C and 5 F.
- 1 unscored practice trial.
- Four fixed sequences A–D cross block order and X/Y item-set mapping.
- Five routing patterns appear once per condition through content-distinct X/Y instances.
- Each participant sees each `stimulus_id` once and never sees both UI renderings of the same content.
- Primitive evidence, values, qualification legend, order, typography, color, viewport, scroll, questions, options, and keys are identical across conditions.
- The only treatment is semantic grouping/headings versus neutral flat records.

## 3. Outcomes

### Primary outcome: Contract-application accuracy (CCA)

For participant \(i\), trial \(j\):

```text
CCA_ij = 1 if Q1 state is correct AND Q2 rule is correct; otherwise 0.
```

Condition means:

```text
CCA_iC = mean available C trials
CCA_iF = mean available F trials
d_i = CCA_iC - CCA_iF
```

### Secondary outcomes

1. Q1 state accuracy.
2. Q2 transfer/reason accuracy.
3. Relative trial response time in milliseconds.
4. Five-point block ease.
5. Pattern-specific and held-out-item descriptive accuracy.

RT analysis is descriptive and secondary. It will report condition medians and participant paired median differences; no RT trimming or inferential model is primary.

## 4. Hypotheses

### H1: primary directional exploratory hypothesis

The participant-level paired CCA difference is positive:

```text
estimand = mean_i(CCA_iC - CCA_iF)
H1 direction: estimand > 0
```

### H2: secondary state-identification hypothesis

Mean participant-level Q1 accuracy is higher in Contract than Flat.

### H3: secondary rule-identification hypothesis

Mean participant-level Q2 accuracy is higher in Contract than Flat.

### H4: descriptive efficiency hypothesis

Contract has lower participant-level median trial RT and/or higher block ease than Flat. H4 is descriptive; discordant speed/accuracy results will not be collapsed into a single benefit claim.

No hypothesis concerns calibrated reliance or user benefit.

## 5. Estimand and primary analysis

### Primary estimand

The arithmetic mean across eligible participants of the within-participant difference in condition-specific CCA proportions.

### Estimation-first report

Report:

1. `N` eligible and missingness;
2. condition means;
3. mean paired difference in percentage points;
4. participant-bootstrap 95% percentile CI, resampling participants with replacement;
5. individual paired differences in a dot/interval display;
6. exact sign-flip p-value as a compatibility statistic, not the main conclusion.

### Exact sign-flip test

- Unit: participant paired difference \(d_i\).
- Null: the distribution of paired differences is sign-symmetric around zero.
- Statistic: mean \(d_i\).
- Primary p-value: one-sided `P(T_flip >= T_observed)` for H1.
- Also report a two-sided sensitivity p-value.
- Enumerate all \(2^N\) sign assignments when feasible; otherwise use a fixed, predeclared exhaustive-equivalent Monte Carlo count of at least 1,000,000 sign assignments with seed `20260810`. At `N ≈ 20`, exact enumeration is feasible.
- Zero differences remain zero under flipping.

No GLMM is primary. Any mixed model is post hoc and clearly exploratory.

## 6. Secondary analyses

- Repeat paired estimation and sign-flip analysis separately for Q1 and Q2 accuracy.
- RT: participant-level median by condition; report paired median difference with participant bootstrap CI. No automatic log transformation.
- Ease: participant paired difference on the 1–5 scale with bootstrap CI.
- Pattern and held-out analyses: descriptive proportions and uncertainty only; no multiplicity-adjusted confirmatory claims.
- Sequence diagnostics: show estimates by A–D and by block order to identify gross carryover/item-map imbalance. These do not replace the pooled primary estimate.

## 7. Missingness and exclusions

### Participant exclusion

- Exclude from primary analysis only if fewer than 8 of 10 scored trials are present.
- Do not exclude based on performance, practice result, condition difference, RT, block ease, or suspected low effort inferred from correctness.
- Duplicate owner codes are flagged and resolved by the owner before analysis; the site does not identify people.

### Trial missingness

- Primary available-case scoring for participants with at least 8 scored trials.
- A trial with one missing component has `CCA=0` only in the required sensitivity analysis.
- Required sensitivity counts every missing Q1/Q2 component as incorrect.
- Report both analyses and all missingness by condition/sequence.

### Timing anomalies

Zero, negative, or technically impossible relative RT is flagged as invalid timing but does not remove the accuracy trial. Hidden-tab time is recorded separately and subtracted.

## 8. Interpretation matrix

| Estimate / uncertainty pattern | Interpretation |
|---|---|
| Positive paired CCA estimate; CI largely above 0; sign-flip compatible with positive effect | Preliminary evidence that semantic grouping improves rule application in this sample/material set |
| Positive estimate near or above 10 pp but wide CI crossing 0 | Promising but inconclusive; do not claim a reliable effect |
| Estimate near 0 with CI spanning practically meaningful positive and negative effects | Inconclusive; study is under-resolved |
| Negative estimate with CI largely below 0 | Evidence the semantic organization may impair application; revise or simplify |
| CCA improves but RT/ease worsens | Accuracy-effort tradeoff; do not call the UI globally better |
| Q1 improves but Q2 does not | State-label recognition without improved rule reasoning |
| Q2 improves but Q1 does not | Rule comprehension does not consistently translate to final routing |
| Held-out accuracy drops while practiced patterns improve | Possible pattern memorization; restrict interpretation |
| Strong sequence/block interaction | Carryover or item-map concern; pooled estimate is fragile |

The **10 percentage-point value is an interest/reference effect only**, not a success threshold, equivalence margin, or smallest worthwhile effect.

## 9. Sample size and resolution

Target `N ≈ 20` completed, eligible participants. This is a formative feasibility sample, not a powered confirmatory study. With five binary trials per condition and participant heterogeneity, the approximate detectable paired difference is expected to be roughly **20–25 percentage points**, depending on within-participant correlation and baseline accuracy.

Consequences:

- A null or small estimate is inconclusive.
- The study cannot establish equivalence or rule out a 10 pp effect.
- Exact p-values do not repair low resolution.
- Any later confirmatory sample-size calculation must use blinded or owner-approved pilot variance and a newly frozen protocol.

## 10. Synthetic labels and provenance

- Every trial is labeled: `Simulated evaluation record — not a current paper result.`
- No raw harmful content is used.
- Current paper numbers are not copied into the stimuli.
- P1–P4 use synthetic non-pass/untested patterns.
- P5 is a synthetic hypothetical pass used solely to test routing completeness; the interface must state that the current paper has no passing latent behavioral positive control.
- Answer keys are mechanically derived from the current four-state contract and support only a **rule-application** claim.

## 11. Pilot stop rules (owner-executed only)

The implementation supports preview/practice, but the owner alone may authorize and run any human pilot. If a future owner-run pilot occurs, stop and revise materials before further collection if any of the following occurs:

1. Any participant can see a final state, aggregate verdict, or recommended action before answering.
2. Contract/Flat normalized evidence parity fails.
3. A stimulus answer key disagrees with the current checker.
4. More than 20% of pilot sessions cannot complete within 15 minutes for non-accessibility reasons.
5. More than 20% encounter a blocking technical/export failure.
6. Any participant reports that the hypothetical pass appears to be a real paper result.
7. Any network request, analytics event, absolute timestamp, IP/UA, sensitive demographic, free text, or person-identifying field is captured.
8. A sequence repeats the same stimulus content or fails the 5/condition assignment.

These rules do not authorize recruitment or collection.

## 12. No-upgrade rule

This document is not frozen. Materials-only implementation, unit testing, synthetic preview, and independent protocol audit do not create human evidence. No study result may be called confirmatory, used to change current paper claims, or promoted to a benefit/reliance claim without:

1. owner ethics/recruitment authorization;
2. a frozen protocol and materials commit;
3. an immutable study/analysis registration;
4. independently audited exports and analysis;
5. a separate owner decision for any paper-claim change.

