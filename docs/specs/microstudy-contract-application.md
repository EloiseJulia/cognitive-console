# Spec: Contract Legibility/Application Micro-Study

- **Spec ID:** `microstudy-contract-application`
- **Status:** `DRAFT / NOT FROZEN / materials-only / second revision`
- **Study class:** exploratory formative micro-study
- **Authorized:** protocol, simulated materials, future loopback implementation
- **Not authorized:** recruitment, ethics administration, pilot/data collection, public deployment, or paper changes
- **Preregistration:** [`../research/2026-08-10-microstudy-contract-application-DRAFT.md`](../research/2026-08-10-microstudy-contract-application-DRAFT.md)
- **Implementation plan:** [`../plans/microstudy-contract-application-web.md`](../plans/microstudy-contract-application-web.md)

## 1. Construct, treatment, and outcome

The study measures **structured rule application**: whether technical GenAI users can combine five displayed contract facts to choose an interface state and then make a separate scope/comparator/generalization judgment. It does not measure or claim deep conceptual integration, transfer, calibrated reliance, user benefit, trust, safety, productivity, latent control, or current-paper evidence.

The treatment is a **semantic-organization package**, not pure headings:

- **Contract:** semantic headings, grouping, and one fixed semantic role order.
- **Flat:** neutral labels, no semantic grouping, and item-specific deterministic row shuffles.
- Both use the same five primitive proposition strings, questions, answer options, dimensions, word-count limits, viewport, and no-scroll behavior.

The sole primary outcome is **conjunctive rule-application accuracy (CCA)**. A trial is correct only if Q1 and Q2 are both correct. Q1 alone may sometimes be strongly constrained by one primitive; the leakage gate therefore targets CCA rather than requiring every Q1 row to be independently at chance.

## 2. Trial flow and frozen display contract

1. Display `Simulated evaluation record` at the top of every practice and formal card.
2. Display five evidence rows.
3. Display Q1 only.
4. On Q1 submission, persist and lock Q1; disable browser/app back navigation to the Q1 view.
5. Only then display Q2. Q2 options contain no state names and do not map one-to-one onto the four Q1 states.
6. On Q2 submission, mark the trial complete and advance. Formal trials show no correctness feedback.

Minimum viewport is `1024 × 700`. The complete card, Q1, and Q2 views must fit without vertical or horizontal scrolling at the frozen viewport. Both conditions use exactly five fixed-height rows, fixed label/body columns, fixed card dimensions, identical typography/color/spacing, and row/body word caps.

### 2.1 Semantic roles and common legend

Primitive IDs and Contract order are:

```text
representation, comparison, comparator, coherence, scope
```

Contract headings in that order are:

```text
Representation relation
Comparative effect
Comparator construction
Coherence qualification
Scope boundary
```

Flat labels are `Evidence A` through `Evidence E`, assigned to the displayed shuffled positions. They do not identify primitive roles.

The identical legend is:

> Use all five facts together. They concern representation, comparison, comparator construction, coherence, and scope; their displayed order carries no meaning.

The legend is a paragraph/unordered rule statement and supplies no position-to-role map.

### 2.2 Flat deterministic row orders

Each list is primitive IDs in displayed positions 1→5:

| Item | Flat order |
|---|---|
| `MS-P1-X` | `comparison, scope, representation, coherence, comparator` |
| `MS-P2-X` | `scope, representation, coherence, comparator, comparison` |
| `MS-P3-X` | `representation, coherence, comparator, comparison, scope` |
| `MS-P4-X` | `coherence, comparator, comparison, scope, representation` |
| `MS-P5-X` | `comparator, comparison, scope, representation, coherence` |
| `MS-P1-Y` | `comparator, representation, scope, comparison, coherence` |
| `MS-P2-Y` | `representation, scope, comparison, coherence, comparator` |
| `MS-P3-Y` | `scope, comparison, coherence, comparator, representation` |
| `MS-P4-Y` | `comparison, coherence, comparator, representation, scope` |
| `MS-P5-Y` | `coherence, comparator, representation, scope, comparison` |

Machine checks must prove that, across ten items, every primitive role appears in every Flat position exactly twice. Contract always uses the fixed semantic role order. This deliberate difference is part of the declared treatment package.

### 2.3 Parity checks

Tests must enforce:

- one canonical proposition map consumed by both renderers;
- exact normalized proposition equality (`NFKC`, normalized newlines, trim, collapsed whitespace);
- exactly five rows and fixed row/body/card dimensions;
- fixed viewport and no scroll in Q1 and Q2 steps;
- equal question/options/order and visible non-label text;
- body word-count equality and total visible word-count difference ≤5%;
- DOM snapshots allowing only declared grouping, label, order, and ARIA-reference differences;
- screenshot masks limited to label glyph regions and the declared row-order permutation;
- keyboard and screen-reader equivalence of evidence and options.

## 3. Questions and keys

### 3.1 Q1

Exact text:

> Which interface state follows after applying the rule to this record?

Exact options:

```text
Q1_UNRESOLVED — Unresolved
Q1_DIAGNOSTIC — Diagnostic only
Q1_WITHHELD — Withheld control
Q1_SUPPORTED — Evidence-supported control at the exact stated tier
```

### 3.2 Item-specific Q2

Every Q2 has four options, shown in the listed order. Q2 wording and keys are independent scope/comparator/generalization judgments and contain no Q1 state name.

| Item | Exact Q2 | Options (`A`–`D`) | Key |
|---|---|---|---|
| `MS-P1-X` | Which use is licensed by the available comparison record? | A: Apply to Alder/North editing at S1. B: Apply to any Alder editing method. C: No comparative use is licensed from zero completed matched observations. D: Generalize to all S1 tasks. | C |
| `MS-P1-Y` | What is the narrowest warranted conclusion about the named scope? | A: Birch/Cedar triage at S2 is established. B: The record does not warrant a comparative conclusion for the named scope. C: All Birch tasks inherit the result. D: The comparator budget substitutes for observations. | B |
| `MS-P2-X` | Which boundary must be preserved when using this record? | A: Use only the representation-facing diagnostic for Alder/Cedar summarization S1. B: Treat the unobserved comparison as favorable. C: Extend to all summarization methods. D: Ignore the named tier. | A |
| `MS-P2-Y` | Which statement respects the comparator evidence? | A: The candidate budget proves a comparative advantage. B: The record generalizes across Birch tasks. C: The S2 boundary can be dropped. D: Representation-facing use is available, but no comparative claim is available without observations. | D |
| `MS-P3-X` | Which comparator judgment is warranted? | A: Coherence overrides the matched effect. B: The matched comparator does not establish the registered advantage for Alder/North planning S1. C: The result generalizes to unmatched budgets. D: The interval proves a positive advantage. | B |
| `MS-P3-Y` | What may be concluded about generalization? | A: The matched result applies to every Birch method. B: The coherence bound licenses cross-task use. C: No extension beyond Birch/Cedar review S2 is warranted, and the registered advantage is not established there. D: Candidate count alone licenses extension. | C |
| `MS-P4-X` | Why is a stronger comparative conclusion not licensed? | A: The interval does not resolve the registered advantage for the matched Alder/Cedar extraction S1 comparison. B: The model name is synthetic. C: Coherence is outside its bound. D: Scope may be generalized before resolving the interval. | A |
| `MS-P4-Y` | Which scope statement follows from the interval and margin? | A: All Birch ranking settings are covered. B: The named comparator can be ignored. C: S2 automatically generalizes to other tiers. D: The evidence does not resolve the registered advantage even within Birch/North ranking S2. | D |
| `MS-P5-X` | Which use stays within the record's supported boundary? | A: Any Alder routing method and tier. B: Alder/North routing at S1 only, with the matched comparator and coherence bound retained. C: All tasks sharing the candidate budget. D: Cross-model use if coherence is small. | B |
| `MS-P5-Y` | Which generalization is justified? | A: Birch/Cedar verification at S2 only; no cross-model, method, task, or tier extension. B: All Birch verification tiers. C: Any Cedar task with five samples. D: Any model whose interval is positive. | A |

## 4. Stimulus schema and provenance

```yaml
schema_version: microstudy-stimuli-v3
stimulus_id: string
content_set: X | Y
pattern_id: P1 | P2 | P3 | P4 | P5
source_status: real_inspired_non_pass | synthetic_rule_case
source_note: nonempty string
hypothetical: boolean
simulated_record_notice: "Simulated evaluation record"
primitive_evidence:
  representation: string
  comparison: string
  comparator: string
  coherence: string
  scope: string
flat_order: [primitive_id, primitive_id, primitive_id, primitive_id, primitive_id]
questions:
  q1: {correct_key: string}
  q2: {text: string, options: [{key: A|B|C|D, text: string}], correct_key: A|B|C|D}
answer_key_derivation:
  required_primitive_ids: [string, ...]
  claim_scope: structured_rule_application_only
```

Exact provenance by item:

| Item | `source_status` | `hypothetical` | Exact `source_note` |
|---|---|---:|---|
| `MS-P1-X` | `real_inspired_non_pass` | false | `Semantic artifact source: incomplete representation/comparison pattern; fabricated teaching values; no raw internal IDs; not paper evidence.` |
| `MS-P1-Y` | `real_inspired_non_pass` | false | `Semantic artifact source: incomplete representation/comparison pattern; fabricated teaching values; no raw internal IDs; not paper evidence.` |
| `MS-P2-X` | `synthetic_rule_case` | false | `Synthetic rule case created for representation-only routing; fabricated teaching values; not paper evidence.` |
| `MS-P2-Y` | `synthetic_rule_case` | false | `Synthetic rule case created for representation-only routing; fabricated teaching values; not paper evidence.` |
| `MS-P3-X` | `real_inspired_non_pass` | false | `Semantic artifact source: matched-comparator non-advantage pattern; fabricated teaching values; no raw internal IDs; not paper evidence.` |
| `MS-P3-Y` | `real_inspired_non_pass` | false | `Semantic artifact source: matched-comparator non-advantage pattern; fabricated teaching values; no raw internal IDs; not paper evidence.` |
| `MS-P4-X` | `real_inspired_non_pass` | false | `Semantic artifact source: interval-resolution pattern; fabricated teaching values; no raw internal IDs; not paper evidence.` |
| `MS-P4-Y` | `real_inspired_non_pass` | false | `Semantic artifact source: interval-resolution pattern; fabricated teaching values; no raw internal IDs; not paper evidence.` |
| `MS-P5-X` | `synthetic_rule_case` | true | `Hypothetical synthetic positive rule case; fabricated teaching values; the current paper contains no passing latent behavioral positive control.` |
| `MS-P5-Y` | `synthetic_rule_case` | true | `Hypothetical synthetic positive rule case; fabricated teaching values; the current paper contains no passing latent behavioral positive control.` |

No UI field exposes raw internal experiment IDs. The debrief explicitly says that no current paper pass is represented.

## 5. Exact formal stimuli

The following are the canonical common primitive propositions. They contain no interface-state words.

| Item | Representation | Comparison | Comparator | Coherence | Scope | Q1 / Q2 |
|---|---|---|---|---|---|---|
| `MS-P1-X` | Alignment estimate 0.08; registered minimum 0.20. | The matched ledger contains 0 completed observations. | Budget: 16 candidates, fixed item split, 5 samples each. | Bound 0.10; no paired outputs are available to calculate change. | Alder / North / editing / S1. | `Q1_UNRESOLVED` / C |
| `MS-P1-Y` | Alignment estimate 0.14; registered minimum 0.25. | The matched ledger contains 0 completed observations. | Budget: 12 candidates, fixed item split, 5 samples each. | Bound 0.08; no paired outputs are available to calculate change. | Birch / Cedar / triage / S2. | `Q1_UNRESOLVED` / B |
| `MS-P2-X` | Alignment estimate 0.31; registered minimum 0.20. | The matched ledger contains 0 completed observations. | Budget: 16 candidates, fixed item split, 5 samples each. | Bound 0.10; no paired outputs are available to calculate change. | Alder / Cedar / summarization / S1. | `Q1_DIAGNOSTIC` / A |
| `MS-P2-Y` | Alignment estimate 0.34; registered minimum 0.25. | The matched ledger contains 0 completed observations. | Budget: 12 candidates, fixed item split, 5 samples each. | Bound 0.08; no paired outputs are available to calculate change. | Birch / North / classification / S2. | `Q1_DIAGNOSTIC` / D |
| `MS-P3-X` | Alignment estimate 0.32; registered minimum 0.20. | Matched effect −0.07; 95% interval [−0.15, +0.01]. | Registered advantage +0.10; budget, split, and 5 samples are matched. | Change 0.03 against absolute bound 0.10. | Alder / North / planning / S1. | `Q1_WITHHELD` / B |
| `MS-P3-Y` | Alignment estimate 0.36; registered minimum 0.25. | Matched effect −0.04; 95% interval [−0.11, +0.03]. | Registered advantage +0.08; budget, split, and 5 samples are matched. | Change 0.02 against absolute bound 0.08. | Birch / Cedar / review / S2. | `Q1_WITHHELD` / C |
| `MS-P4-X` | Alignment estimate 0.33; registered minimum 0.20. | Matched effect +0.05; 95% interval [−0.09, +0.19]. | Registered advantage +0.10; budget, split, and 5 samples are matched. | Change 0.03 against absolute bound 0.10. | Alder / Cedar / extraction / S1. | `Q1_UNRESOLVED` / A |
| `MS-P4-Y` | Alignment estimate 0.37; registered minimum 0.25. | Matched effect +0.03; 95% interval [−0.07, +0.13]. | Registered advantage +0.08; budget, split, and 5 samples are matched. | Change 0.02 against absolute bound 0.08. | Birch / North / ranking / S2. | `Q1_UNRESOLVED` / D |
| `MS-P5-X` | Alignment estimate 0.35; registered minimum 0.20. | Matched effect +0.16; 95% interval [+0.11, +0.21]. | Registered advantage +0.10; budget, split, and 5 samples are matched. | Change 0.03 against absolute bound 0.10. | Alder / North / routing / S1 only. | `Q1_SUPPORTED` / B |
| `MS-P5-Y` | Alignment estimate 0.39; registered minimum 0.25. | Matched effect +0.14; 95% interval [+0.09, +0.19]. | Registered advantage +0.08; budget, split, and 5 samples are matched. | Change 0.02 against absolute bound 0.08. | Birch / Cedar / verification / S2 only. | `Q1_SUPPORTED` / A |

Required derivation primitives:

```text
P1: representation + comparison
P2: representation + comparison
P3: comparison + comparator + coherence
P4: comparison + comparator
P5: comparison + comparator + coherence + scope
```

## 6. Leakage gate

The primary leakage target is CCA, not row-wise Q1 chance.

Frozen tests:

1. Q1-only single-row, keyword, fixed-position, and lexical heuristics may predict part of Q1; their exact leave-one-X/Y-pair-out Q1 accuracy is reported, not treated as an automatic failure.
2. Give each heuristic its Q1 prediction but no Q2 information. With four Q2 choices, deterministic option guessing is evaluated over all four fixed guesses and seeded uniform guessing; expected CCA must be `≤0.25`.
3. Evaluate every predeclared `single row + one option lexical` heuristic end-to-end under leave-one-X/Y-pair-out. No heuristic may significantly exceed the predeclared CCA chance bound `0.25`.
4. Significance test: exact one-sided binomial test against `p=0.25`, alpha `0.05`, no tuning after data or materials inspection.
5. Combined rule checker must score `10/10`; each derivation uses at least two primitive IDs.

If Q2 option count changes, the chance bound is recomputed as `1 / option_count` and frozen before any pilot. Q2 keys are balanced `A=3, B=3, C=2, D=2`, and item-specific wording prevents a state-to-option lookup.

## 7. Practice/tutorial/debrief materials

### Setup and consent placeholder

> Study information and consent text will be supplied by the owner after the applicable ethics and recruitment process. This materials draft does not provide or imply ethics approval.

### Qualification legend

> Use all five facts together. They concern representation, comparison, comparator construction, coherence, and scope; their displayed order carries no meaning.

### Tutorial

> First answer which interface state follows from the five facts. After you submit Q1, it is locked and Q2 appears. Q2 asks a separate question about scope, comparator, or generalization. A formal trial counts as correct only when both answers are correct. Formal trials give no feedback.

### Exact practice item

Top notice: `Simulated evaluation record`

```text
Representation relation: Fit estimate 0.27; registered minimum 0.20.
Comparative effect: Matched effect +0.02; 95% interval [−0.06, +0.10].
Comparator construction: Registered advantage +0.07; budget and split are matched.
Coherence qualification: Change 0.01 against absolute bound 0.05.
Scope boundary: Juniper / East / labeling / T1.
```

Practice Q1:

> Which interface state follows after applying the rule to this record?

Correct: `Q1_UNRESOLVED`.

Practice Q2:

> Which conclusion respects the comparison and scope?

```text
A: Generalize to all Juniper tasks.
B: The interval does not resolve the registered advantage within Juniper/East labeling T1.
C: The coherence value alone establishes comparative advantage.
D: The matched budget permits use at every tier.
```

Correct: B.

Feedback after both answers:

> The interval does not resolve the registered advantage. The named model, method, task, and tier remain the boundary. This example teaches the two-step response format; it is not a formal item.

### Debrief

> These were simulated teaching records with fabricated values. They assess structured rule application, not deep integration or real-world benefit. No item reports a current paper pass, and no response changes the paper's claims.

## 8. Sequence generation and allocation

### 8.1 Exact sequence algorithm

Base pattern order `b=[P1,P3,P2,P5,P4]`. Let `r=0..4` for suffix `1..5`.

- Block 1 order: `left_rotate(b, r)`.
- Block 2 order: `left_rotate(b, (r+2) mod 5)`.

Letter mapping:

| Letter | Block 1 | Block 2 |
|---|---|---|
| A | Contract X | Flat Y |
| B | Flat Y | Contract X |
| C | Contract Y | Flat X |
| D | Flat X | Contract Y |

Exact order table:

| Suffix | Block 1 | Block 2 |
|---|---|---|
| 1 | P1 P3 P2 P5 P4 | P2 P5 P4 P1 P3 |
| 2 | P3 P2 P5 P4 P1 | P5 P4 P1 P3 P2 |
| 3 | P2 P5 P4 P1 P3 | P4 P1 P3 P2 P5 |
| 4 | P5 P4 P1 P3 P2 | P1 P3 P2 P5 P4 |
| 5 | P4 P1 P3 P2 P5 | P3 P2 P5 P4 P1 |

This yields exactly `A1..A5, B1..B5, C1..C5, D1..D5`.

### 8.2 Balance proof obligations

Across the 20 sequences:

- each letter contributes five rotations, so every pattern occupies each position once in each block for that letter;
- therefore every pattern occupies each position `4 letters × 2 blocks = 8` times overall;
- A/B assign X to Contract and Y to Flat; C/D assign Y to Contract and X to Flat, giving each content ID 10 Contract and 10 Flat presentations;
- each condition×set cell occurs in two letters and both block positions, with every pattern-position cell appearing twice per condition×set;
- the `+2 mod 5` block-2 rotation is a derangement, so no pattern repeats its block-1 within-block position;
- every sequence contains each of the ten content IDs exactly once.

Tests generate the full 200 trial rows and assert these counts rather than trusting prose.

### 8.3 Slot allocation

Before outcomes exist, the owner creates a blinded allocation list containing exactly 20 sequence slots `A1..D5`, one of each code. Assignment sees only the next open slot and participant code.

- A participant consumes a slot only after all ten trials are `complete` and the export is finalized.
- Dropout or primary-ineligible completion does not consume the slot; the replacement receives the same sequence code.
- A fully completed participant later excluded for a predeclared mechanical reason consumes the slot, is not replaced, and remains in an ITT-style sensitivity labeled with the mechanical exclusion.
- Outcome data, accuracy, RT, or ease may never inform assignment or replacement.
- Allocation log records slot, anonymous attempt ID, assignment status, consumption status, and mechanical-exclusion reason; no outcomes are present.

## 9. Missingness truth table and export

Per planned slot:

| State | `planned` | `presented` | `q1_submitted` | `q2_submitted` | `complete` |
|---|---:|---:|---:|---:|---:|
| Not reached | true | false | false | false | false |
| Viewed, no Q1 | true | true | false | false | false |
| Q1 locked, dropout before Q2 | true | true | true | false | false |
| Q1 and Q2 submitted | true | true | true | true | true |

Invariants:

```text
complete == (q1_submitted && q2_submitted)
q2_submitted implies q1_submitted
q1_submitted implies presented
presented implies planned
submitted == complete  # compatibility alias only; never used independently
```

All ten planned slots are exported, including slots not reached. Each slot includes:

```text
slot_index, participant_code, sequence, condition, item, pattern, content_set,
block, position, planned, presented, q1_submitted, q2_submitted, complete,
submitted, q1, q2, q1_correct, q2_correct, cca_correct, rt_q1_ms, rt_q2_ms,
rt_total_ms, hidden_ms, source_status, hypothetical, materials_version
```

Nullability:

- no Q1: Q1 and all correctness fields null;
- Q1 only: Q1/Q1 correctness populated; Q2/Q2 correctness/CCA null;
- complete: both answers and all correctness fields populated.

Primary available-case CCA uses **complete trials only**. Eligibility is:

```text
complete_contract >= 4
AND complete_flat >= 4
AND complete_total >= 8
```

Sensitivity uses all ten planned slots and sets `cca_correct=false` whenever either component is missing. Reports include every truth-table state by condition and sequence. No performance-, RT-, ease-, or practice-based exclusion exists.

## 10. Statistics freeze

Primary estimand:

```text
mean_i(CCA_contract_i - CCA_flat_i)
```

where each eligible participant's condition mean uses complete trials only.

Bootstrap:

- `B=10000`;
- seed `20260810`;
- resample participants with replacement;
- recompute the mean paired difference;
- percentile endpoints at `2.5%` and `97.5%`.

Exact sign-flip:

- remove zero participant differences before enumeration and report their count as ties;
- let `N_eff` be nonzero differences;
- enumerate all `2^N_eff` sign assignments, with no Monte Carlo fallback;
- statistic is mean signed difference using the original eligible-participant denominator (zeros contribute zero);
- one-sided p is the fraction of enumerated statistics `>=` observed;
- two-sided sensitivity is the fraction with absolute statistic `>= abs(observed)`;
- equality is included; no `+1` correction.

Q1, Q2, RT, ease, pattern, block, sequence, and position analyses are descriptive.

No numerical MDE claim is currently permitted. Status is:

> `pending reproducible simulation before protocol freeze`

Before freeze, an audited script must state N, baseline probabilities, paired correlation/data-generating mechanism, ten binary trials, missingness, alpha, direction, effect grid, iterations, and seed; emit machine-readable assumptions/results plus a plot/table; and be independently reproduced. Until then, the DRAFT must not cite a numerical MDE.

## 11. Timing and accessibility gates

Owner-run timing pilot: exactly three usability-pilot participants under the eventual authorized process.

Pass iff:

- median total completion time `≤10 min`;
- every participant `≤12 min`;
- forced timeout count `=0`.

If any condition fails, revise and rerun a new three-person pilot. The app never forces timeout. Automated keyboard, screen-reader, contrast, reduced-motion, 200% zoom, and no-horizontal-scroll checks are separate and are not counted as timing participants or timing pass criteria.

This document does not authorize the owner pilot or provide ethics/recruitment wording.

## 12. Privacy and security

- loopback binding only; reject non-loopback IPv4/IPv6;
- suppress request/access logs;
- no browser persistence, cookies, service worker, Cache API, IndexedDB, analytics, telemetry, remote assets, or external requests;
- restrictive CSP;
- export only anonymous codes, responses, allocation metadata, and relative monotonic durations;
- no IP, UA, headers, absolute timestamps, demographics, free text, fingerprint, or server-side response persistence.

## 13. Acceptance criteria

1. Ten canonical items, exact Q2/options/keys, exact `source_status/source_note/hypothetical`, and exact Flat orders validate.
2. Every card starts with `Simulated evaluation record`; debrief says there is no current paper pass.
3. Q1 locks before Q2; Q2 contains no state names or state-option mapping.
4. CCA leakage tests use the frozen `0.25` bound and exact binomial rule; combined checker is `10/10`.
5. Contract/Flat proposition identity, treatment declaration, geometry, word count, viewport, and no-scroll tests pass.
6. Flat primitive-role×position counts equal two; all 20 sequence and cross-block balance invariants pass.
7. Allocation replacement/consumption rules are machine represented and outcome blind.
8. Export has all ten slots and satisfies every truth-table invariant and nullability case.
9. Primary uses complete trials only; eligibility and ten-slot missing-as-incorrect sensitivity rebuild from export.
10. Bootstrap/sign-flip settings are exact; no numerical MDE claim remains.
11. Exact tutorial/practice/feedback/debrief strings are materialized.
12. Timing and accessibility gates remain separate and unauthorized for execution.
13. No web implementation, recruitment, data, paper edit, or claim upgrade is included in this revision.
