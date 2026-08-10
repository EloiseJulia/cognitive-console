# DRAFT Preregistration: Contract Legibility/Application Micro-Study

- **Status:** `DRAFT — NOT FROZEN — NOT AUTHORIZED FOR HUMAN DATA`
- **Date:** 2026-08-10
- **Study type:** exploratory formative micro-study
- **Protocol:** [`../specs/microstudy-contract-application.md`](../specs/microstudy-contract-application.md)

## 1. Scope

This study estimates whether semantic organization changes technical GenAI users' application of a four-state interface contract to simulated records. It does not study calibrated reliance, user benefit, trust, safety, productivity, deployment, model behavior, or current paper evidence.

The owner retains responsibility for ethics, recruitment, and any pilot/data collection. Current authorization is materials and loopback implementation only.

## 2. Design

- Within participant: Contract UI versus information-matched Flat Panel.
- Ten planned formal slots: five per condition in two blocks.
- One different, unscored practice example.
- Exact 20-code counterbalance `A1..D5`: A–D crosses condition/set/block mapping; 1–5 applies balanced Latin rotations.
- Every participant sees ten unique content IDs once.
- All formal combinations are unseen in practice. There is no separately designated subset or separate generalization outcome.
- Primitive evidence strings/order, legend, questions, options, keys, geometry, typography, color, viewport, and no-scroll behavior are frozen equal. Only semantic versus neutral row labels differ.

## 3. Outcomes

### Primary: conjunctive rule-application accuracy

For submitted trial \(j\) from participant \(i\):

```text
CCA_ij = 1 only when Q1 state and Q2 scope/reason are both correct.
```

For primary-eligible participants:

```text
CCA_iC = mean submitted Contract trials
CCA_iF = mean submitted Flat trials
d_i = CCA_iC - CCA_iF
```

### Secondary descriptive outcomes

- Q1 state accuracy;
- Q2 scope/reason application accuracy;
- relative trial RT;
- five-point block ease;
- pattern, position, block, and sequence summaries.

Secondary analyses are descriptive. There is no confirmatory multiple-hypothesis family.

## 4. Primary estimand and analysis

The primary estimand is the arithmetic mean of participant-level paired CCA differences among eligible participants.

Report:

1. eligible N and missingness by condition/sequence;
2. condition means;
3. mean paired difference in percentage points;
4. participant-bootstrap 95% percentile CI;
5. individual paired differences;
6. exact one-sided sign-flip p-value as the sole primary test;
7. two-sided sign-flip sensitivity.

The exact test flips each participant difference around zero and uses mean difference as the statistic. Enumerate all assignments when feasible; otherwise use at least 1,000,000 assignments with seed `20260810`. Zero differences remain zero.

No GLMM is primary. Any model not listed above is post hoc and exploratory.

## 5. Missingness and exclusions

All ten planned records are pre-generated and exported, including unpresented/unsubmitted slots. A participant enters the available-case primary analysis only if:

```text
submitted Contract >= 4
submitted Flat >= 4
submitted total >= 8 of 10
```

Otherwise the participant is excluded from the primary analysis with an explicit reason. There is no performance-, practice-, RT-, ease-, or suspected-effort exclusion.

Primary CCA uses submitted trials among eligible participants. Required sensitivity counts every missing Q1/Q2 component as incorrect over all ten planned slots. Missing/presented/submitted counts are reported by condition and sequence.

Impossible relative timing is flagged but does not remove accuracy data.

## 6. Estimation-first interpretation

The point estimate and CI are always primary. The following categories are descriptive labels, not progression gates:

1. **Inconclusive/wide:** CI crosses both −10 and +10 percentage-point reference anchors.
2. **Negative direction:** otherwise, point estimate is below zero.
3. **Directionally positive:** otherwise, point estimate is above zero.
4. **No directional signal:** point estimate equals zero.

The ±10-point anchors are not pass/fail thresholds, equivalence margins, or smallest worthwhile effects. A positive point estimate is described only as directional. No category authorizes paper use or a benefit claim.

Discordant accuracy, RT, or ease is reported as a tradeoff, not collapsed into a global verdict.

## 7. Sample and resolution

The planning target remains approximately 20 eligible completions. This is not a powered confirmatory study.

The previously stated 20–25 percentage-point detectable range is a simulation estimate only. Before protocol freeze, `cognitive_console.microstudy.analysis` must regenerate the estimate from explicit assumptions, including N, baseline accuracy, within-participant correlation, binary-trial count, missingness scenario, test direction, and alpha. The generated artifact and assumptions, not this prose range, become authoritative.

A null or small estimate cannot establish equivalence. Exact p-values do not repair low resolution.

## 8. Materials, leakage, and provenance

- Every item says: `Simulated evaluation record — not a current paper result.`
- Evidence bodies contain no direct status vocabulary, role headings, aggregate verdict, or recommended action.
- Q1/Q2 require at least two primitive rows.
- Blind fixed-position, keyword, second-row-only, and single-row bag-of-words baselines are frozen implementation tests and may not exceed empirical majority chance (`0.40`).
- Contract/Flat use exact common proposition strings/order and parity audits including DOM snapshots and masked screenshots.
- Provenance enum is exactly `real_inspired_non_pass` or `synthetic_rule_case`, with required `source_note`.
- P1/P3/P4 are real-inspired non-pass designs; P2/P5 are synthetic rule cases.
- P5 is hypothetical and visibly states that the current paper contains no passing latent behavioral positive control.
- All numeric values are fabricated teaching values and are not paper evidence.

## 9. Sequence allocation

The owner supplies one of `A1..D5`.

- A/B: Contract receives X; C/D: Contract receives Y.
- A/C: Contract first; B/D: Flat first.
- Rotation 1–5 left-rotates `[P1,P3,P2,P5,P4]`.

Across the exact 20 codes, each pattern occupies each within-block position eight times overall (four per condition and two per condition/set cell), every content ID is assigned ten times to each condition, and no participant repeats content. The implementation must machine-check the generated mapping.

## 10. Timing, accessibility, and stop/revise gate

The web app does not enforce a per-trial or study timeout. Design targets for an owner-authorized pilot are:

- median completion ≤10 minutes;
- P90 completion ≤12 minutes.

Tutorial/practice are compressed; every evidence row and total evidence body obey the word caps in the spec.

Before formal collection, the owner must approve a pilot gate. Stop and revise if P90 exceeds 12 minutes, keyboard-only flow fails, 200% zoom loses content/introduces horizontal scrolling, parity fails, keys disagree with the checker, exports fail, or any privacy/network violation occurs.

These criteria do not authorize a pilot.

## 11. Privacy

The implementation is loopback-only and stores only anonymous owner code, sequence, answers, ease, and relative monotonic durations. It must:

- suppress server access logging by overriding `log_message` or equivalent;
- use no local/session storage, cookies, service worker, IndexedDB, Cache API, analytics, telemetry, remote asset, or external network request;
- use a restrictive loopback CSP;
- emit no IP, UA, request line, absolute timestamp, demographics, free text, fingerprint, or server-side response file;
- pass tests capturing stdout, stderr, created files, server state, and exports.

## 12. Export and reproducibility

Each export has exactly ten planned slot records with:

```text
presented, submitted, nullable q1/q2/correctness/rt_ms/hidden_ms,
condition, item, pattern, position, block, sequence
```

JSON and CSV must rebuild, without hidden state:

- eligibility;
- primary available-case inputs;
- ten-slot missing-as-incorrect sensitivity;
- missingness by condition/sequence;
- participant bootstrap CI;
- exact sign-flip test;
- descriptive secondary summaries.

End-to-end tests cover early exit, partial completion, a missing component, full completion, round-trip, and deterministic rebuild.

## 13. No-upgrade rule

This preregistration is not frozen. Materials, unit tests, synthetic preview, and audit produce no human evidence. No result may be called confirmatory or used to change paper claims without owner authorization, frozen protocol/materials, ethics/recruitment approval, immutable registration, audited exports/analysis, and a separate paper-claim decision.
