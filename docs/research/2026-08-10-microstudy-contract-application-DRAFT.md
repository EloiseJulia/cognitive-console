# DRAFT Preregistration: Contract Legibility/Application Micro-Study

- **Status:** `DRAFT — NOT FROZEN — NOT AUTHORIZED FOR HUMAN DATA`
- **Date:** 2026-08-10
- **Protocol:** [`../specs/microstudy-contract-application.md`](../specs/microstudy-contract-application.md)

## 1. Scope and treatment

This exploratory formative study estimates whether a semantic-organization package changes technical GenAI users' structured application of a four-state contract to simulated records. Contract uses semantic grouping, semantic labels, and fixed role order. Flat uses neutral labels and item-specific deterministic shuffled order. The treatment is not characterized as pure headings.

The study does not measure deep integration, transfer, calibrated reliance, benefit, trust, safety, productivity, deployment, latent control, or current-paper evidence. The owner remains responsible for ethics, recruitment, and any pilot/data collection; none is authorized by this DRAFT.

## 2. Design and flow

- Within participant; ten planned formal slots, five per condition, in two blocks.
- One different unscored practice item.
- Q1 is submitted and irreversibly locked before Q2 appears.
- Q2 is an independent scope/comparator/generalization judgment; its options contain no state names and do not map one-to-one onto Q1 states.
- Every formal card begins `Simulated evaluation record`.
- Common primitive propositions are identical across conditions.
- Exact 20-code allocation `A1..D5`; block 2 uses rotation `r+2 mod 5`, not the block-1 rotation.

## 3. Primary outcome and leakage target

For a complete trial:

```text
CCA_ij = 1 iff Q1_ij is correct AND Q2_ij is correct.
```

The primary estimand is the mean eligible-participant paired difference:

```text
d_i = mean complete Contract CCA_i - mean complete Flat CCA_i
estimand = mean_i(d_i)
```

Q1 may be partly predictable from a single primitive because the contract logic permits one fact to strongly constrain a state. Leakage acceptance therefore targets CCA. All forty Q2 options are parallel positive action/interpretation statements with ten normalized tokens, zero occurrences of `no/not/only/without/within/must/cannot`, and identical scope-marker positions. The frozen option-only heuristic uses only length, negation, modal, scope-marker, and option-position features under leave-one-item-out evaluation. It must not significantly exceed `0.25`.

Materials verification found the option-only fixed-position ceiling at `3/10` (`p=0.4744`, exact one-sided binomial versus `0.25`). The frozen single-comparison-row mapping predicts Q1 for `8/10`; combined with any option-only position it reaches at most `2/10 CCA = 20%` (`p=0.7560`). The normative five-input router scores all `10/10`. These figures came from a disposable deterministic script and must be recreated as implementation tests.

## 4. State routing and key authority

The sole Q1 authority is the ordered function of READ status, comparison tested/estimate/CI/margin, coherence status, and tier:

1. READ unsupported → unresolved.
2. READ supported plus comparison untested → diagnostic-only.
3. Missing comparison resolution or CI crossing zero → unresolved.
4. Resolved non-superiority (`ci_high<=0`) or positive resolved estimate below margin → withheld.
5. Positive CI meeting margin plus coherence failure → withheld.
6. Positive CI meeting margin plus coherence pass → evidence-supported at the exact tier.

A tier change invalidates inherited READ/evaluation inputs and returns unresolved until new tier-specific inputs exist. Q1 keys are generated and validated by this router; item IDs are never state authority. The ten derived states are P1 unresolved, P2 diagnostic-only, P3 withheld, P4 unresolved, and P5 evidence-supported at S1/S2, for both X/Y records.

## 5. Missingness, identity, and exclusions

Every export contains all ten planned slots and the fields:

```text
planned, presented, q1_submitted, q2_submitted, complete
```

with:

```text
complete == q1_submitted && q2_submitted
q2_submitted => q1_submitted => presented => planned
submitted == complete
```

Session-level export contains a locally generated random UUID `attempt_id`, owner-assigned anonymous `participant_code`, `sequence`, `completion_status`, attention/practice status fields, and analysis-derived `mechanical_exclusion` plus its reason enum. Each slot includes exact `source_status/source_note/hypothetical` and explicit missing flags for nullable response/timing fields. Participants cannot edit exclusion fields.

Primary available-case CCA uses complete trials only. Eligibility requires:

```text
complete Contract >= 4
complete Flat >= 4
complete total >= 8
```

Required sensitivity uses all ten planned trials and treats either missing component as incorrect. Reports enumerate not reached, viewed/no-Q1, Q1-only dropout, and complete states by condition and sequence. There is no performance-, RT-, ease-, or practice-based exclusion.

Analysis re-derives exclusions from raw export and a pre-outcome owner assignment list. Duplicate handling uses `participant_code`: keep the first complete attempt; if none completes, keep the most complete and break ties by owner-log assignment order. All attempts remain raw. The ITT sensitivity includes all attempts except non-kept duplicates and predeclared `technical_corrupt` attempts; exclusion decisions freeze before outcomes. No absolute timestamp, IP, UA, or header/fingerprint data is collected.

## 6. Allocation and balance

Before outcomes, the owner prepares one blinded slot for each `A1..D5`. A slot is consumed only by a finalized ten-complete-trial participant. Dropout/primary-ineligible attempts reuse the same sequence. A fully completed participant later mechanically excluded consumes the slot, is not replaced, and remains in an ITT-style sensitivity.

Base order is `[P1,P3,P2,P5,P4]`; suffix `r=0..4` uses `rotate(r)` in block 1 and `rotate(r+2 mod 5)` in block 2. A/B assign Contract X; C/D Contract Y. A/C put Contract first; B/D put Flat first.

Across 20 codes, each pattern occupies each within-block position eight times overall, four times per condition, and twice per condition×set cell. Every content ID appears ten times per condition. The +2 rotation prevents a pattern from repeating its block-1 position. Machine tests, not prose, establish the generated 200-row table.

## 7. Statistical analysis

Report eligible N, condition means, mean paired CCA difference, individual differences, missingness, and:

- participant bootstrap, `B=10000`, seed `20260810`, percentile `2.5/97.5`;
- exact one-sided sign-flip as sole primary test;
- exact two-sided sign-flip sensitivity.

Zero differences are ties and removed before enumerating all `2^N_eff` assignments. Tail equality is included and there is no `+1` correction. Q1, Q2, RT, ease, pattern, block, sequence, and position are descriptive.

MDE status is `pending reproducible simulation before protocol freeze`. This DRAFT makes no numerical MDE claim. A script with explicit assumptions, machine-readable outputs, and independent audit is required before freeze.

## 8. Materials and provenance

The exact ten stimuli, item-specific Q2s, keys, Flat orders, tutorial, practice, feedback, and debrief are normative in the protocol.

The provenance field is exactly `source_status`. P1/P3/P4 are `real_inspired_non_pass` with semantic artifact source notes and no raw internal IDs. P2/P5 are `synthetic_rule_case`; P5 has `hypothetical=true`. All values are fabricated. The debrief states there is no current paper pass.

Contract and Flat share fixed dimensions, word-count constraints, viewport, and no-scroll behavior. Flat role order is balanced so every primitive occupies every position exactly twice across ten items.

## 9. Timing and accessibility

The owner-run timing pilot is exactly three people and passes only if median completion is `≤10 min`, all three are `≤12 min`, and forced timeouts are zero. Failure requires revision and a new pilot.

Automated accessibility testing is separate and not included in timing: keyboard, visible focus, screen-reader parity, contrast, reduced motion, 200% zoom, and no horizontal scrolling. This DRAFT does not authorize either activity.

## 10. Privacy and reproducibility

The future implementation is loopback-only, suppresses access logs, uses no browser/server persistence or remote network, and exports no IP, UA, absolute timestamp, demographics, free text, or fingerprint.

Analysis must rebuild routing validation, eligibility, exclusions, primary inputs, ten-slot ITT sensitivity, missingness, bootstrap, and sign-flip outputs from raw export plus the frozen owner assignment list.

## 11. No-upgrade rule

This protocol remains DRAFT/materials-only. It changes no paper and authorizes no recruitment, pilot, data collection, or claim upgrade. Human evidence requires owner authorization, applicable ethics/recruitment handling, frozen audited materials/protocol, and a separate paper-claim decision.
