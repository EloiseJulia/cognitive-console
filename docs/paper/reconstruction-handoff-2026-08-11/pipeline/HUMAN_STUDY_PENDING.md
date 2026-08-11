# Human Study Pending Integration Packet

## Status

- Planned completion: **on or before 2026-08-20**.
- Current evidence date: **2026-08-11**.
- Current state: **no supplied human result**.
- Evidence policy: every empty field below remains non-evidence. No direction, effect size, sample size, significance, quotation, participant characteristic, or user benefit may be inferred.

## Submission Branches

| Branch | Trigger | Required narrative action |
|---|---|---|
| H-A Positive/qualified support | Valid study supports one or more preregistered human claims | Add only supported claims with effect sizes, uncertainty, exclusions, deviations, and scope. Re-rank Arc A/B/C. |
| H-B Null or practically negligible | Valid study does not support the targeted effect | Report the null/interval; do not erase the study. Reconsider interface contribution and Arc B viability. |
| H-C Mixed or adverse | Outcomes differ by task/group/measure or reveal harm/confusion | Foreground heterogeneity/adverse evidence; revise the contract/interface rather than averaging it away. |
| H-D Incomplete or invalid | Recruitment, manipulation, measurement, power, or protocol failure prevents inference | Report as incomplete/invalid where relevant; human claims remain unavailable. |
| H-E Delayed | Results are not ready by submission freeze | Submit the model-only fallback or delay submission; never fill result slots speculatively. |

## Protocol and Governance

| Field | Pending value | Evidence required |
|---|---|---|
| Study title / registry ID | `[PENDING]` | Dated registry or preregistration |
| Protocol version and freeze time | `[PENDING]` | Immutable protocol/hash |
| Ethics/IRB determination | `[PENDING]` | Approval, exemption, or institutional determination |
| Human owner | `[PENDING]` | Named study/ethics owner in private records |
| Recruitment window | `[PENDING]` | Dated recruitment log |
| Data freeze time | `[PENDING]` | Immutable dataset/hash |
| Analysis code/version | `[PENDING]` | Frozen code and environment |

## Research Questions and Claims

| Field | Pending value |
|---|---|
| Human research question(s) | `[PENDING]` |
| Primary human claim(s) | `[PENDING]` |
| Secondary/exploratory claim(s) | `[PENDING]` |
| Claims explicitly out of scope | `[PENDING]` |
| Smallest effect / practical threshold | `[PENDING]` |

## Design

| Field | Pending value |
|---|---|
| Study design | `[PENDING]` |
| Conditions | `[PENDING]` |
| Tasks/materials | `[PENDING]` |
| Comparator/interface variants | `[PENDING]` |
| Manipulation checks | `[PENDING]` |
| Randomization/counterbalancing | `[PENDING]` |
| Session duration | `[PENDING]` |

## Participants and Flow

| Field | Pending value |
|---|---|
| Target population | `[PENDING]` |
| Planned sample and rationale | `[PENDING]` |
| Recruitment source | `[PENDING]` |
| Inclusion/exclusion criteria | `[PENDING]` |
| Enrolled / started / completed / analyzed | `[PENDING]` |
| Exclusions with timing and reasons | `[PENDING]` |
| Compensation | `[PENDING]` |

## Measures and Analysis

| Field | Pending value |
|---|---|
| Primary outcome(s) | `[PENDING]` |
| Secondary outcome(s) | `[PENDING]` |
| Behavioral vs. self-report distinction | `[PENDING]` |
| Scales and provenance | `[PENDING]` |
| Statistical model/test | `[PENDING]` |
| Multiplicity handling | `[PENDING]` |
| Missing-data handling | `[PENDING]` |
| Robustness/sensitivity analyses | `[PENDING]` |

## Results — Keep Empty Until Frozen

| Result ID | Estimand / measure | N | Estimate | Interval / uncertainty | Test | Status |
|---|---|---:|---:|---|---|---|
| H-F1 | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` | NO RESULT |
| H-F2 | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` | NO RESULT |
| H-F3 | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` | NO RESULT |

## Qualitative Material

- Participant quotations: `[PENDING — none may be invented or paraphrased before data]`
- Coding procedure and coders: `[PENDING]`
- Codebook/version: `[PENDING]`
- Agreement/adjudication: `[PENDING]`

## Deviations and Limitations

| Field | Pending value |
|---|---|
| Protocol deviations | `[PENDING]` |
| Recruitment/sample limitations | `[PENDING]` |
| Manipulation/measurement limitations | `[PENDING]` |
| Generalization boundaries | `[PENDING]` |
| Adverse/unexpected findings | `[PENDING]` |

## Required Integration Audit

When results arrive, the pipeline must update and revalidate:

1. `SOURCE_REGISTRY.yml` verification state.
2. `FACT_LEDGER.md` with new `H-F*` / `FL-*` rows.
3. `CLAIM_GRAPH.md` and `EVIDENCE_INVENTORY.md`.
4. `ARC_OPTIONS.md`, `VENUE_FIT.md`, and `NARRATIVE_CONTRACT.md`.
5. Introduction promise budget and selected Introduction.
6. Method, Results, Discussion, Limitations, Abstract, and Title.
7. Citation needs for measures/scales and related human evidence.
8. `ASSEMBLY_AUDIT.md`, number lint, caveat lint, and author sign-off.

## Human Sign-Off

- Ethics/protocol owner: `[PENDING]`
- Analysis owner: `[PENDING]`
- Claim adjudicator: `[PENDING]`
- Corresponding-author approval: `[PENDING]`
