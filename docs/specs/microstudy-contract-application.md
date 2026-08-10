# Spec: Contract Legibility/Application Micro-Study

- **Spec ID:** `microstudy-contract-application`
- **Status:** `DRAFT / NOT FROZEN / materials-only / protocol-finalization revision`
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

### 3.2 Cross-pattern Q2 template pool

Q2 uses three templates. A template's question and ordered options are byte-identical across all of its uses; only the primitive evidence changes the key. Every template is used by at least two patterns, has at least two correct positions across uses, contains no Q1 state name, and has no pattern-specific term in its options.

| Template | Exact question | Exact options (`A`–`D`) |
|---|---|---|
| `Q2-NEXT` | Which next evaluation is required? | A: Establish the READ relation at this tier now. B: Run a decisive comparison at this tier now. C: Check coherence at the registered tier again now. D: Retest the rule at a newly specified tier. |
| `Q2-BASELINE` | What follows about the unsteered baseline? | A: The baseline is below the reference range here. B: The baseline is near the reference range here. C: The baseline relation is unknown from this record. D: The baseline is above the reference range here. |
| `Q2-COVERAGE` | Which evidence is directly established in this record? | A: The record directly establishes READ evidence alone. B: The record directly establishes comparative evidence alone. C: The record directly establishes both evidence types. D: The record directly establishes neither evidence type. |

Exact assignment and primitive-evidence justification:

| Item | Template | Key | Primitive-evidence basis |
|---|---|---:|---|
| `MS-P1-X` | `Q2-COVERAGE` | D | Neither a tier-specific READ result nor a completed comparison exists. |
| `MS-P2-X` | `Q2-NEXT` | B | READ is established; the matched comparison has not been run. |
| `MS-P2-Y` | `Q2-BASELINE` | C | The comparator row explicitly says the baseline relation is unknown. |
| `MS-P1-Y` | `Q2-BASELINE` | A | The comparator row explicitly places the baseline below the reference range. |
| `MS-P3-X` | `Q2-COVERAGE` | C | Both READ and comparative results are directly established. |
| `MS-P3-Y` | `Q2-NEXT` | C | The resolved comparison is available but the coherence evaluation is unavailable. |
| `MS-P4-X` | `Q2-NEXT` | A | The interval is available but the tier-specific READ evaluation is unavailable. |
| `MS-P4-Y` | `Q2-BASELINE` | B | The comparator row explicitly places the baseline near the reference range. |
| `MS-P5-X` | `Q2-NEXT` | D | Current evidence is restricted to S1; another tier requires a new evaluation. |
| `MS-P5-Y` | `Q2-BASELINE` | D | The comparator row explicitly places the baseline above the reference range. |

Template reuse is `Q2-NEXT=4`, `Q2-BASELINE=4`, and `Q2-COVERAGE=2`. Correct positions within the three templates are respectively `{A,B,C,D}`, `{A,B,C,D}`, and `{C,D}`. Overall key balance is `A=2, B=2, C=3, D=3`. Q2 remains hidden until Q1 is irreversibly submitted and locked.

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
  q1: {derived_key: string}
  q2: {template_id: string, text: string, options: [{key: A|B|C|D, text: string}], correct_key: A|B|C|D}
state_routing_inputs:
  tier: string
  evaluation_tier: string
  read_status: supported | unsupported
  comparison:
    tested: boolean
    estimate: number | null
    ci_low: number | null
    ci_high: number | null
    registered_margin: number | null
  coherence_status: pass | fail | unavailable
answer_key_derivation:
  router_version: state-router-v1
  required_primitive_ids: [string, ...]
  claim_scope: structured_rule_application_only
```

Exact provenance by item:

| Item | `source_status` | `hypothetical` | Exact `source_note` |
|---|---|---:|---|
| `MS-P1-X` | `real_inspired_non_pass` | false | `Semantic artifact source: incomplete representation/comparison pattern; fabricated teaching values; no raw internal IDs; not paper evidence.` |
| `MS-P1-Y` | `real_inspired_non_pass` | false | `Semantic artifact source: interval-resolution non-pass pattern; fabricated teaching values; no raw internal IDs; not paper evidence.` |
| `MS-P2-X` | `synthetic_rule_case` | false | `Synthetic rule case created for representation-only routing; fabricated teaching values; not paper evidence.` |
| `MS-P2-Y` | `synthetic_rule_case` | false | `Synthetic rule case created for representation-only routing; fabricated teaching values; not paper evidence.` |
| `MS-P3-X` | `real_inspired_non_pass` | false | `Semantic artifact source: coherence-qualified non-pass pattern; fabricated teaching values; no raw internal IDs; not paper evidence.` |
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
| `MS-P1-X` | The tier-specific READ evaluation has not been completed. | The matched ledger contains 0 completed observations. | Budget: 16 candidates, fixed item split, 5 samples each. | Bound 0.10; no paired outputs are available to calculate change. | Alder / North / editing / S1. | `Q1_UNRESOLVED` / D |
| `MS-P1-Y` | Alignment estimate 0.31; registered minimum 0.25. | Matched effect +0.03; 95% interval [−0.07, +0.13]. | Registered advantage +0.08; the unsteered baseline is below the reference range. | Change 0.02 against absolute bound 0.08. | Birch / Cedar / triage / S2. | `Q1_UNRESOLVED` / A |
| `MS-P2-X` | Alignment estimate 0.31; registered minimum 0.20. | The matched ledger contains 0 completed observations. | Budget: 16 candidates, fixed item split, 5 samples each. | Bound 0.10; no paired outputs are available to calculate change. | Alder / Cedar / summarization / S1. | `Q1_DIAGNOSTIC` / B |
| `MS-P2-Y` | Alignment estimate 0.34; registered minimum 0.25. | The matched ledger contains 0 completed observations. | Registered advantage +0.08; the unsteered baseline relation is unknown. | Bound 0.08; no paired outputs are available to calculate change. | Birch / North / classification / S2. | `Q1_DIAGNOSTIC` / C |
| `MS-P3-X` | Alignment estimate 0.32; registered minimum 0.20. | Matched effect +0.16; 95% interval [+0.11, +0.21]. | Registered advantage +0.10; budget, split, and 5 samples are matched. | The registered coherence evaluation is unavailable. | Alder / North / planning / S1. | `Q1_WITHHELD` / C |
| `MS-P3-Y` | Alignment estimate 0.36; registered minimum 0.25. | Matched effect −0.04; 95% interval [−0.11, −0.01]. | Registered advantage +0.08; budget, split, and 5 samples are matched. | The registered coherence evaluation is unavailable. | Birch / Cedar / review / S2. | `Q1_WITHHELD` / C |
| `MS-P4-X` | The tier-specific READ evaluation is unavailable. | Matched effect +0.05; 95% interval [−0.09, +0.19]. | Registered advantage +0.10; budget, split, and 5 samples are matched. | Change 0.03 against absolute bound 0.10. | Alder / Cedar / extraction / S1. | `Q1_UNRESOLVED` / A |
| `MS-P4-Y` | Alignment estimate 0.37; registered minimum 0.25. | Matched effect +0.03; 95% interval [−0.07, +0.13]. | Registered advantage +0.08; the unsteered baseline is near the reference range. | Change 0.02 against absolute bound 0.08. | Birch / North / ranking / S2. | `Q1_UNRESOLVED` / B |
| `MS-P5-X` | Alignment estimate 0.35; registered minimum 0.20. | Matched effect +0.16; 95% interval [+0.11, +0.21]. | Registered advantage +0.10; budget, split, and 5 samples are matched. | Change 0.03 against absolute bound 0.10. | Alder / North / routing / S1 only; another tier requires retesting. | `Q1_SUPPORTED` / D |
| `MS-P5-Y` | Alignment estimate 0.39; registered minimum 0.25. | Matched effect +0.14; 95% interval [+0.09, +0.19]. | Registered advantage +0.08; the unsteered baseline is above the reference range. | Change 0.02 against absolute bound 0.08. | Birch / Cedar / verification / S2 only. | `Q1_SUPPORTED` / D |

### 5.1 Normative state-routing function

`route_state(tier, evaluation_tier, read_status, tested, estimate, ci_low, ci_high, registered_margin, coherence_status)` is the sole authority for Q1:

```text
if evaluation_tier != tier:
    return Q1_UNRESOLVED
if read_status == unsupported:
    return Q1_UNRESOLVED
if tested == false:
    return Q1_DIAGNOSTIC
if any required comparison value is missing or ci_low <= 0 <= ci_high:
    return Q1_UNRESOLVED
if ci_high <= 0:
    return Q1_WITHHELD
if ci_low > 0 and estimate < registered_margin:
    return Q1_WITHHELD
if ci_low >= registered_margin and estimate >= registered_margin:
    if coherence_status != pass:
        return Q1_WITHHELD
    return Q1_SUPPORTED(tier)
return Q1_UNRESOLVED
```

Priority is top-to-bottom. Thus READ unsupported dominates every downstream field; READ supported plus untested comparison is diagnostic-only; insufficient resolution or an interval crossing zero is unresolved; resolved non-superiority or a positive resolved point estimate below margin is withheld; positive-CI margin satisfaction is withheld on coherence failure and evidence-supported only on coherence pass. `Q1_SUPPORTED` carries the exact input `tier`.

Changing `tier` invalidates inherited evaluation because the prior `evaluation_tier` no longer matches. The changed record returns `Q1_UNRESOLVED` until a new READ result and comparison/coherence evaluation explicitly tied to that tier replace the prior inputs.

Normative truth table for the ten records:

| Item | READ | Comparison classification | Coherence | Tier | Derived Q1 |
|---|---|---|---|---|---|
| `MS-P1-X` | unsupported | untested | unavailable | S1 | `Q1_UNRESOLVED` |
| `MS-P1-Y` | supported | CI crosses 0 | pass | S2 | `Q1_UNRESOLVED` |
| `MS-P2-X` | supported | untested | unavailable | S1 | `Q1_DIAGNOSTIC` |
| `MS-P2-Y` | supported | untested | unavailable | S2 | `Q1_DIAGNOSTIC` |
| `MS-P3-X` | supported | positive CI meets +0.10 margin | unavailable | S1 | `Q1_WITHHELD` |
| `MS-P3-Y` | supported | resolved non-superiority, CI≤0 | unavailable | S2 | `Q1_WITHHELD` |
| `MS-P4-X` | unsupported | CI crosses 0 | pass | S1 | `Q1_UNRESOLVED` |
| `MS-P4-Y` | supported | CI crosses 0 | pass | S2 | `Q1_UNRESOLVED` |
| `MS-P5-X` | supported | positive CI meets +0.10 margin | pass | S1 | `Q1_SUPPORTED(S1)` |
| `MS-P5-Y` | supported | positive CI meets +0.08 margin | pass | S2 | `Q1_SUPPORTED(S2)` |

Implementations must never use `stimulus_id`, `pattern_id`, or an item-ID lookup as state authority. The answer key is generated from structured router inputs and validated against this table; a mismatch is a materials build failure.

Required derivation primitives:

```text
P1-X: representation + comparison
P1-Y: representation + comparison + comparator
P2: representation + comparison
P3: comparison + comparator + coherence
P4: comparison + comparator
P5: comparison + comparator + coherence + scope
```

## 6. Leakage gate

The primary leakage target is CCA, not row-wise Q1 chance.

Frozen pre-implementation tests:

1. A question+options-only observer must emit one fixed answer per repeated template because the displayed Q2 text is identical across that template's uses. Report the oracle best fixed-per-template ceiling, not a fitted result.
2. Report separately: (a) leave-one-item-out template-frequency prediction with deterministic alphabetical tie-breaking and (b) the global best fixed-position prediction. Never call the global result leave-one-out.
3. Report option-only lexical, normalized-token-length, negation, modal, and position heuristics. These heuristics may inspect question/options but never primitive evidence, item ID, pattern ID, condition, or Q1 response.
4. The single-comparison-row baseline maps `untested→Q1_DIAGNOSTIC`, `CI≤0→Q1_WITHHELD`, `CI crosses 0→Q1_UNRESOLVED`, and positive margin-resolved→Q1_SUPPORTED`, while deliberately ignoring READ, coherence, and tier mismatch.
5. Cross the single-row Q1 prediction with every allowed question/options-only prediction and report the maximum CCA. The combined ceiling must be `≤25%`.
6. Every no-evidence accuracy is tested by an exact one-sided binomial test against `p=0.25`, alpha `0.05`, inclusive upper tail, with no post-inspection tuning. Every preregistered heuristic must have `p>=0.05`.
7. The normative five-input router must score `10/10`; each derivation uses at least two primitive IDs.

If Q2 option count changes, chance is frozen again as `1 / option_count` before any pilot.

Temporary deterministic verification on 2026-08-10 found:

| Audit | Correct | Accuracy | Exact one-sided `p` vs `.25` |
|---|---:|---:|---:|
| Oracle fixed answer per repeated template | 3/10 | 30% | 0.4744 |
| Leave-one-item-out template-frequency, alphabetical tie-break | 0/10 | 0% | 1.0000 |
| Global best fixed position | 3/10 | 30% | 0.4744 |
| Equal-length heuristic, ties→A | 2/10 | 20% | 0.7560 |
| Negation-marker heuristic, otherwise ties→A | 3/10 | 30% | 0.4744 |
| Modal-marker heuristic, ties→A | 2/10 | 20% | 0.7560 |
| READ-lexical heuristic, otherwise ties→A | 2/10 | 20% | 0.7560 |
| Single-comparison-row Q1 | 8/10 | 80% | descriptive only |
| Single-row + oracle template answer CCA | 2/10 | 20% | 0.7560 |
| Single-row + LOO template answer CCA | 0/10 | 0% | 1.0000 |

All questions/options contain zero Q1 state names. All allowed no-evidence heuristics are nonsignificant; the maximum combined CCA is 20%. The disposable verification script was not retained. Implementation must recreate the exact template identities, assignments, truth table, heuristic definitions, and values as tests.

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

### 8.3 Slot allocation and duplicate attempts

Before outcomes exist, the owner creates a blinded allocation list containing exactly 20 sequence slots `A1..D5`, one of each code. Assignment sees only the next open slot and participant code.

- A participant consumes a slot only after all ten trials are `complete` and the export is finalized.
- Dropout or primary-ineligible completion does not consume the slot; the replacement receives the same sequence code.
- A fully completed participant later excluded for a predeclared mechanical reason consumes the slot, is not replaced, and remains in an ITT-style sensitivity labeled with the mechanical exclusion.
- Outcome data, accuracy, RT, or ease may never inform assignment or replacement.
- Allocation log records slot, anonymous attempt ID, assignment status, consumption status, and mechanical-exclusion reason; no outcomes are present.
- `attempt_id` is a random UUID generated locally for each start. `participant_code` is the owner-assigned anonymous deduplication key.
- Duplicate status is frozen before outcomes are inspected. The owner assignment log marks all attempts sharing a `participant_code`; keep the first complete attempt. If none is complete, keep the attempt with the greatest number of complete trials, breaking ties by owner-log assignment order. No absolute timestamp is collected or used.
- Every duplicate remains in raw export. Non-kept duplicates enter the frozen analysis-exclusion list as `duplicate_attempt`; the keep/exclude decision and owner-log order are auditable without response outcomes.

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
slot_index, condition, item, pattern, content_set,
block, position, planned, presented, q1_submitted, q2_submitted, complete,
submitted, q1, q2, q1_correct, q2_correct, cca_correct, rt_q1_ms, rt_q2_ms,
rt_total_ms, hidden_ms, source_status, source_note, hypothetical,
q1_missing, q2_missing, q1_correct_missing, q2_correct_missing,
cca_correct_missing, rt_q1_missing, rt_q2_missing, rt_total_missing,
hidden_ms_missing,
materials_version
```

Session-level export includes:

```text
attempt_id, participant_code, sequence, completion_status,
attention_check_presented, attention_check_submitted, attention_check_passed,
practice_presented, practice_q1_submitted, practice_q2_submitted, practice_complete,
mechanical_exclusion, mechanical_exclusion_reason
```

`attempt_id` is a local random UUID. `completion_status` is one of `started`, `partial`, or `ten_trial_complete`. `mechanical_exclusion` and `mechanical_exclusion_reason` are analysis-derived fields, never participant-editable. The reason enum is:

```text
none | duplicate_attempt | technical_corrupt | sequence_mismatch |
materials_version_mismatch | impossible_state_transition
```

Every trial slot carries exact `source_status`, `source_note`, and `hypothetical`, plus explicit missing flags for every nullable response/timing field. No absolute timestamp, IP address, user agent, header dump, or fingerprint is collected.

`technical_corrupt` is limited to an unreadable/truncated export, schema/checksum failure, or loss of planned-slot identity that prevents deterministic reconstruction. Ordinary dropout, missing responses, long duration, attention/practice performance, and low accuracy are never technical corruption. This classification is frozen before outcome inspection.

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

Analysis re-derives mechanical exclusions from raw exports and the frozen owner assignment list; exported derived flags are consistency checks, not authority. The primary analysis uses the kept attempt and excludes all mechanically excluded attempts. The ITT sensitivity includes every attempt, including other mechanically excluded complete attempts, except non-kept duplicates and `technical_corrupt` attempts under the rules frozen before outcome inspection. Raw export retains all attempts. Primary and sensitivity reports enumerate exclusion reasons and prove that attention/practice performance never changes eligibility.

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
4. Q2 leakage checks reproduce template reuse `4/4/2`, keys `A2/B2/C3/D3`, oracle template `3/10`, LOO template `0/10`, global fixed-position `3/10`, all lexical/length/negation/modal heuristics `≤3/10` with `p>=.05`, comparison-row Q1 `8/10`, and combined CCA `2/10`; router checker is `10/10`.
5. Contract/Flat proposition identity, treatment declaration, geometry, word count, viewport, and no-scroll tests pass.
6. Flat primitive-role×position counts equal two; all 20 sequence and cross-block balance invariants pass.
7. Allocation replacement/consumption/duplicate rules are machine represented and outcome blind.
8. Export has session identity/status fields, all ten enriched slots, provenance, explicit missing flags, and every truth-table invariant/nullability case.
9. Primary and ITT sensitivity rebuild exclusions from raw export plus the pre-outcome owner log; ITT omits only frozen duplicates and technical-corrupt attempts.
10. Bootstrap/sign-flip settings are exact; no numerical MDE claim remains.
11. Exact tutorial/practice/feedback/debrief strings are materialized.
12. Timing and accessibility gates remain separate and unauthorized for execution.
13. No web implementation, recruitment, data, paper edit, or claim upgrade is included in this revision.
