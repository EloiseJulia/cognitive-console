# Spec: Contract Legibility/Application Micro-Study

- **Spec ID:** `microstudy-contract-application`
- **Status:** `DRAFT / materials-only / ready for hostile re-audit`
- **Study class:** exploratory formative micro-study
- **Authorized scope:** protocol, simulated materials, and loopback-only implementation
- **Not authorized:** recruitment, ethics submission, pilot/data collection, public deployment, or paper changes
- **Related preregistration:** [`../research/2026-08-10-microstudy-contract-application-DRAFT.md`](../research/2026-08-10-microstudy-contract-application-DRAFT.md)
- **Implementation plan:** [`../plans/microstudy-contract-application-web.md`](../plans/microstudy-contract-application-web.md)

## 1. Objective, treatment, and claims

The study asks whether semantic organization helps technical GenAI users apply a four-state interface contract to simulated records. It compares:

- **Contract UI:** five rows labelled with the semantic field names below.
- **Info-Matched Flat Panel:** the same five rows labelled with neutral IDs.

The sole treatment is row labelling/grouping. The primary outcome is **conjunctive rule-application accuracy (CCA)**: Q1 and Q2 must both be correct. Q2 is **scope/reason application**, not transfer. The study makes no calibrated-reliance, benefit, trust, safety, productivity, latent-control, population, or paper-evidence claim.

All ten formal items are novel combinations not shown in practice. Practice teaches the response format using one different example; there is no independent transfer outcome or inferential transfer claim.

## 2. Design

- Within participant; 10 planned formal slots, 5 per condition, two blocks.
- One unscored practice item with different nouns, values, and combination.
- Exact sequence codes `A1` through `D5`.
- Every participant sees all ten content IDs once, never both renderings of one content ID.
- Desktop target; minimum viewport `1024 × 700`.
- No automatic timeout. Timing targets are usability gates, not exclusion rules.
- Owner assignment is external; the site accepts only anonymous owner code and exact sequence code.

## 3. Frozen parity contract

### 3.1 Common primitive propositions

Each stimulus stores one ordered `primitive_evidence` array. Both renderers consume those exact strings in that exact order. Evidence bodies contain no role heading and may not contain these direct state cues, case-insensitively:

```text
not tested
failed
failure
inconclusive
pass
passed
underpowered
unresolved
diagnostic only
withheld control
evidence-supported control
transfer
deploy
recommended action
```

No condition may synthesize, prefix, or repeat a semantic role inside the evidence body.

### 3.2 Labels and geometry

| Row | Contract label | Flat label |
|---|---|---|
| 1 | Representation relation | Evidence A |
| 2 | Comparative effect | Evidence B |
| 3 | Comparator construction | Evidence C |
| 4 | Coherence qualification | Evidence D |
| 5 | Scope boundary | Evidence E |

The neutral labels are selected to approximate the semantic labels' visual width through fixed label-column sizing; labels never change body width.

Both conditions must have:

- exactly five fixed-height rows;
- identical row order, label-column width, body width, font family/size/weight/line-height, colors, spacing, card/viewport dimensions, and no-scroll behavior;
- identical qualification legend, question text, option text/order, controls, and navigation;
- total visible word-count difference no greater than 5%;
- exact equality of evidence-body word count, wrapped line count, row height, and total card height.

The legend is identical:

> Combine the representation relation, comparative effect, comparator construction, coherence qualification, and exact scope. No single row determines the answer.

### 3.3 Required parity audits

Implementation acceptance must include:

1. normalized string/order equality tests (NFKC, CRLF→LF, trim, whitespace collapse);
2. word-count, wrapped-line-count, row-height, and card-height tests;
3. DOM snapshots at the frozen viewport, allowing differences only in labels, grouping wrappers/classes, and associated ARIA references;
4. pixel/screenshot comparison with masks limited to label glyph regions; all row/body geometry must match;
5. CSS-token and no-scroll assertions;
6. screen-reader evidence/options equality.

## 4. Routing questions and answer key

### Q1

**Which interface state follows after combining all five rows?**

- `Q1_UNRESOLVED`: Unresolved
- `Q1_DIAGNOSTIC`: Diagnostic only
- `Q1_WITHHELD`: Withheld control
- `Q1_SUPPORTED`: Evidence-supported control at the exact stated tier

### Q2: scope/reason application

**Which combination of contract facts justifies that state and scope?**

- `Q2_UNRESOLVED_REASON`: The representation relation and comparative record together do not establish the required route at this scope.
- `Q2_DIAGNOSTIC_REASON`: The representation threshold is met, while the comparative ledger has no completed observations, so only the representation-facing use is available.
- `Q2_WITHHELD_REASON`: The representation threshold is met, but the matched comparison does not establish the required advantage; coherence alone cannot supply it.
- `Q2_SUPPORTED_REASON`: The matched comparison establishes the registered advantage, coherence remains inside its bound, and support is limited to the named model–method–task–tier scope.

Every correct Q1/Q2 derivation requires at least two rows:

- P1: representation relation + comparative ledger;
- P2: representation relation + comparative ledger;
- P3: comparative effect + matched comparator (with coherence unable to override);
- P4: comparative interval + registered margin/resolution;
- P5: comparative effect + coherence + exact scope.

## 5. Stimulus schema

```yaml
schema_version: microstudy-stimuli-v2
stimulus_id: string
content_set: X | Y
pattern_id: P1 | P2 | P3 | P4 | P5
provenance: real_inspired_non_pass | synthetic_rule_case
source_note: nonempty string
hypothetical: boolean
no_current_pass_statement: string | null
simulated_record_notice: "Simulated evaluation record — not a current paper result."
primitive_evidence:
  - primitive_id: read
    proposition: string
  - primitive_id: comparison
    proposition: string
  - primitive_id: comparator
    proposition: string
  - primitive_id: coherence
    proposition: string
  - primitive_id: scope
    proposition: string
questions:
  q1: {correct_key: string}
  q2: {correct_key: string}
answer_key_derivation:
  required_primitive_ids: [string, ...]
  claim_scope: rule_application_only
```

Required provenance assignment:

- P1, P3, P4: `real_inspired_non_pass`;
- P2, P5: `synthetic_rule_case`;
- P5: `hypothetical=true` and `no_current_pass_statement="Hypothetical teaching case; the current paper contains no passing latent behavioral positive control."`;
- all other patterns: `hypothetical=false`, `no_current_pass_statement=null`.

`source_note` describes only the design provenance and must state that values are fabricated teaching values, not paper evidence.

## 6. Ten formal stimuli and keys

All propositions below are the exact common body strings for both conditions. Values are fabricated and must never be represented as paper results.

| ID | Pattern | Five propositions in fixed order | Q1 / Q2 | Provenance |
|---|---|---|---|---|
| `MS-P1-X` | P1 | (1) Alignment estimate 0.08; registered representation minimum 0.20. (2) Comparative ledger contains 0 completed matched observations. (3) Prompt comparator budget is 16 candidates and 5 samples per item. (4) Coherence bound is 0.10; no paired output set exists for calculation. (5) Scope: model Alder, method North, editing, tier S1. | `Q1_UNRESOLVED` / `Q2_UNRESOLVED_REASON` | `real_inspired_non_pass` |
| `MS-P1-Y` | P1 | (1) Alignment estimate 0.14; registered representation minimum 0.25. (2) Comparative ledger contains 0 completed matched observations. (3) Prompt comparator budget is 12 candidates and 5 samples per item. (4) Coherence bound is 0.08; no paired output set exists for calculation. (5) Scope: model Birch, method Cedar, triage, tier S2. | `Q1_UNRESOLVED` / `Q2_UNRESOLVED_REASON` | `real_inspired_non_pass` |
| `MS-P2-X` | P2 | (1) Alignment estimate 0.31; registered representation minimum 0.20. (2) Comparative ledger contains 0 completed matched observations. (3) Prompt comparator budget is 16 candidates and 5 samples per item. (4) Coherence bound is 0.10; no paired output set exists for calculation. (5) Scope: model Alder, method Cedar, summarization, tier S1. | `Q1_DIAGNOSTIC` / `Q2_DIAGNOSTIC_REASON` | `synthetic_rule_case` |
| `MS-P2-Y` | P2 | (1) Alignment estimate 0.34; registered representation minimum 0.25. (2) Comparative ledger contains 0 completed matched observations. (3) Prompt comparator budget is 12 candidates and 5 samples per item. (4) Coherence bound is 0.08; no paired output set exists for calculation. (5) Scope: model Birch, method North, classification, tier S2. | `Q1_DIAGNOSTIC` / `Q2_DIAGNOSTIC_REASON` | `synthetic_rule_case` |
| `MS-P3-X` | P3 | (1) Alignment estimate 0.32; registered representation minimum 0.20. (2) Matched effect is −0.07; 95% interval [−0.15, +0.01]. (3) Registered advantage is +0.10; comparator matched the 16-candidate budget, item split, and 5 samples. (4) Coherence change is 0.03 against an absolute bound of 0.10. (5) Scope: model Alder, method North, planning, tier S1. | `Q1_WITHHELD` / `Q2_WITHHELD_REASON` | `real_inspired_non_pass` |
| `MS-P3-Y` | P3 | (1) Alignment estimate 0.36; registered representation minimum 0.25. (2) Matched effect is −0.04; 95% interval [−0.11, +0.03]. (3) Registered advantage is +0.08; comparator matched the 12-candidate budget, item split, and 5 samples. (4) Coherence change is 0.02 against an absolute bound of 0.08. (5) Scope: model Birch, method Cedar, review, tier S2. | `Q1_WITHHELD` / `Q2_WITHHELD_REASON` | `real_inspired_non_pass` |
| `MS-P4-X` | P4 | (1) Alignment estimate 0.33; registered representation minimum 0.20. (2) Matched effect is +0.05; 95% interval [−0.09, +0.19]. (3) Registered advantage is +0.10; comparator matched the 16-candidate budget, item split, and 5 samples. (4) Coherence change is 0.03 against an absolute bound of 0.10. (5) Scope: model Alder, method Cedar, extraction, tier S1. | `Q1_UNRESOLVED` / `Q2_UNRESOLVED_REASON` | `real_inspired_non_pass` |
| `MS-P4-Y` | P4 | (1) Alignment estimate 0.37; registered representation minimum 0.25. (2) Matched effect is +0.03; 95% interval [−0.07, +0.13]. (3) Registered advantage is +0.08; comparator matched the 12-candidate budget, item split, and 5 samples. (4) Coherence change is 0.02 against an absolute bound of 0.08. (5) Scope: model Birch, method North, ranking, tier S2. | `Q1_UNRESOLVED` / `Q2_UNRESOLVED_REASON` | `real_inspired_non_pass` |
| `MS-P5-X` | P5 | (1) Alignment estimate 0.35; registered representation minimum 0.20. (2) Matched effect is +0.16; 95% interval [+0.11, +0.21]. (3) Registered advantage is +0.10; comparator matched the 16-candidate budget, item split, and 5 samples. (4) Coherence change is 0.03 against an absolute bound of 0.10. (5) Scope: model Alder, method North, routing, tier S1 only. | `Q1_SUPPORTED` / `Q2_SUPPORTED_REASON` | `synthetic_rule_case` |
| `MS-P5-Y` | P5 | (1) Alignment estimate 0.39; registered representation minimum 0.25. (2) Matched effect is +0.14; 95% interval [+0.09, +0.19]. (3) Registered advantage is +0.08; comparator matched the 12-candidate budget, item split, and 5 samples. (4) Coherence change is 0.02 against an absolute bound of 0.08. (5) Scope: model Birch, method Cedar, verification, tier S2 only. | `Q1_SUPPORTED` / `Q2_SUPPORTED_REASON` | `synthetic_rule_case` |

The UI shows the simulated-record notice on every item and the no-current-pass statement on P5 outside the five evidence rows.

### 6.1 Answer-leakage audit

Implementation tests must freeze and run blind baselines that receive no condition label or semantic heading:

- fixed-position-only majority lookup;
- single-row bag-of-words logistic/naive-Bayes baselines for each row separately;
- forbidden-keyword/rule-word lookup;
- record-B/second-row-only lookup.

Use leave-one-X/Y-pair-out evaluation and report exact accuracy. No single-row, keyword, or fixed-position baseline may exceed the empirical Q1 majority-class chance (`4/10 = 0.40`); Q2 uses the same key distribution and threshold. A failure blocks materials. The combined rule checker must score `10/10`. Tests also assert every key's `required_primitive_ids` has length at least two.

## 7. Practice

Practice is one unscored synthetic example with different nouns and values. It demonstrates combining representation and comparison with one explanation after submission. It does not contain any formal item string, does not expose a formal answer, and does not create a “seen pattern” or transfer designation.

## 8. Exact 20-sequence mapping

Base mappings:

| Letter | Block 1 | Block 2 | Contract set | Flat set |
|---|---|---|---|---|
| A | Contract X | Flat Y | X | Y |
| B | Flat Y | Contract X | X | Y |
| C | Contract Y | Flat X | Y | X |
| D | Flat X | Contract Y | Y | X |

Base within-block pattern order is `[P1, P3, P2, P5, P4]`. Rotation `r` (1–5) left-rotates this list by `r-1`. Sequence code is letter plus rotation, producing exactly:

```text
A1 A2 A3 A4 A5 B1 B2 B3 B4 B5 C1 C2 C3 C4 C5 D1 D2 D3 D4 D5
```

The same rotation is applied to both blocks. For example:

| Rotation | Pattern positions 1→5 |
|---|---|
| 1 | P1 P3 P2 P5 P4 |
| 2 | P3 P2 P5 P4 P1 |
| 3 | P2 P5 P4 P1 P3 |
| 4 | P5 P4 P1 P3 P2 |
| 5 | P4 P1 P3 P2 P5 |

Machine checks must prove across all 20 codes:

- exactly 10 unique content IDs and 5 per condition per sequence;
- letter mapping and block order exactly match the table;
- each pattern appears in every within-block position exactly eight times overall, four times per condition, and twice per condition/set assignment;
- each content ID appears in Contract 10 times and Flat 10 times;
- pattern, position, condition, set, and block counts match the generated expected table;
- no participant repeats content.

## 9. Timing and accessibility gate

Target completion distribution for owner pilot:

- median `study_rt_ms ≤ 10 minutes`;
- P90 `study_rt_ms ≤ 12 minutes`.

Tutorial and practice must be concise. Each formal row is capped at 24 visible words and each five-row evidence body at 110 visible words. The web app never auto-submits or times out.

Before any formal collection, the owner must run an authorized pilot and approve the timing/accessibility gate. Stop and revise if P90 exceeds 12 minutes, any keyboard-only path fails, or any supported desktop view at 200% zoom loses content or requires horizontal scrolling.

Required accessibility: landmarks, heading hierarchy, fieldsets/legends, explicit labels, visible focus, keyboard-only operation, 4.5:1 text contrast, 3:1 control/focus contrast, reduced-motion support, no color-only meaning, and screen-reader parity.

## 10. Privacy and loopback security

- Bind only to loopback; reject non-loopback IPv4/IPv6.
- Override `BaseHTTPRequestHandler.log_message` (or equivalent) so request/access logs emit nothing.
- No `localStorage`, `sessionStorage`, cookies, service worker, Cache API, IndexedDB, analytics, telemetry, remote assets, remote network calls, referrer collection, or server persistence.
- CSP permits only required loopback static resources and blocks remote origins.
- Session state exists only in page memory until explicit local download/reset.
- Store only anonymous owner code, sequence code, responses, ease, and relative monotonic durations.
- Never store/export IP, UA, headers, absolute timestamps, path outside the package, screen/device fingerprint, demographics, free text, or recruitment source.

Tests must capture stdout, stderr, created files, server state, and exports during representative requests/sessions and assert absence of IPs, UAs, request lines, absolute timestamps, and participant data. Static-source tests reject browser storage, service worker, analytics, and external URL APIs.

## 11. Complete ten-slot export

At session start, pre-generate all ten planned response records. Export always contains all ten in planned order, including unpresented/unsubmitted slots:

```json
{
  "schema_version": "microstudy-export-v2",
  "study_id": "microstudy-contract-application",
  "materials_version": "TBD_COMMIT",
  "participant_code": "OWNER_ASSIGNED",
  "sequence": "A1",
  "responses": [{
    "slot_index": 1,
    "condition": "contract",
    "item": "MS-P1-X",
    "pattern": "P1",
    "position": 1,
    "block": 1,
    "sequence": "A1",
    "presented": true,
    "submitted": true,
    "q1": "Q1_UNRESOLVED",
    "q2": "Q2_UNRESOLVED_REASON",
    "q1_correct": true,
    "q2_correct": true,
    "cca_correct": true,
    "rt_ms": 18000,
    "hidden_ms": 0
  }],
  "block_ease": [],
  "relative_timing": {"study_rt_ms": 480000},
  "analysis_eligibility": {
    "submitted_contract": 5,
    "submitted_flat": 5,
    "submitted_total": 10,
    "eligible_primary": true,
    "reason": null
  }
}
```

For unsubmitted slots, `submitted=false` and `q1`, `q2`, correctness fields, `rt_ms`, and `hidden_ms` are nullable. `presented` independently records whether the trial was displayed.

Primary available-case CCA is computed only when:

```text
submitted_contract >= 4
AND submitted_flat >= 4
AND submitted_total >= 8
```

Otherwise the participant is excluded from the primary analysis. There is no performance-, RT-, ease-, or practice-based exclusion. The required sensitivity treats every missing Q1/Q2 component as incorrect across all ten planned slots. Reports must show missing/presented/submitted counts by condition and sequence.

CSV is one row per planned slot with the exact response fields plus repeated session/eligibility fields. RFC 4180 quoting and spreadsheet-formula escaping are mandatory.

## 12. Analysis and interpretation

### Primary

- Estimand: mean participant-level `CCA_contract − CCA_flat` among primary-eligible participants.
- Estimation: condition means, paired difference, participant-bootstrap percentile 95% CI, individual paired differences.
- Sole primary test: exact one-sided sign-flip test on participant differences; report two-sided sensitivity.
- Secondary Q1, Q2, RT, ease, pattern, sequence, and position summaries are descriptive. No multiple-hypothesis family or confirmatory secondary claim.

### Descriptive interpretation categories

References `−0.10` and `+0.10` are symmetric descriptive anchors, not pass/fail gates, equivalence margins, or smallest worthwhile effects. Apply this precedence:

1. **Inconclusive/wide:** CI crosses both −0.10 and +0.10.
2. **Negative direction:** otherwise, point estimate < 0.
3. **Directionally positive:** otherwise, point estimate > 0.
4. **No directional signal:** point estimate = 0.

Always report the point and CI; categories cannot authorize progression, paper use, or protocol claims.

The current 20–25 percentage-point resolution statement is only a simulation estimate. `analysis.py` must recompute it from explicit assumptions before protocol freeze; generated output, not prose, becomes the frozen value.

## 13. Implementation file plan

```text
src/cognitive_console/microstudy/
  __init__.py
  __main__.py
  server.py
  schema.py
  sequencing.py
  scoring.py
  export.py
  analysis.py
  static/index.html
  static/app.js
  static/styles.css
  data/stimuli.json
  data/sequences.json
tests/
  test_microstudy_schema.py
  test_microstudy_parity.py
  test_microstudy_leakage.py
  test_microstudy_routing.py
  test_microstudy_sequences.py
  test_microstudy_export.py
  test_microstudy_analysis.py
  test_microstudy_server.py
  test_microstudy_end_to_end.py
```

`analysis.py` must rebuild eligibility, available-case primary inputs, ten-slot missing-as-incorrect sensitivity, bootstrap CI, exact sign-flip statistic, missingness tables, and MDE/resolution simulation from exports. End-to-end tests must cover early exit before presentation, partial condition completion, one missing answer component, full completion, JSON/CSV round-trip, and deterministic rebuild from export alone.

## 14. Acceptance criteria

1. Ten items validate; P1/P3/P4 and P2/P5 provenance enums and notes are exact.
2. P5 is hypothetical and displays the no-current-pass statement.
3. Evidence contains no forbidden state terms/headings; all keys require at least two primitives.
4. Frozen blind single-row/keyword/position heuristics score at most 0.40; combined checker scores 1.00.
5. Common strings/order, legend, options, keys, geometry, word/line/height, DOM snapshot, and masked screenshot parity pass.
6. All `A1..D5` sequence balance invariants pass.
7. Export always has ten slots and applies the `4/condition + 8/10` primary rule exactly.
8. Missing-as-incorrect sensitivity and missingness by condition/sequence rebuild from export.
9. No performance-based exclusion exists.
10. Server/browser privacy tests prove no access logs, storage, external network, absolute time, IP, UA, or persistence.
11. Keyboard and 200% zoom checks pass; owner pilot gate remains required before formal collection.
12. Analysis tests reproduce bootstrap/sign-flip/descriptive outputs and simulation assumptions.
13. No web implementation, recruitment, data, paper edit, or claim upgrade is included in this protocol-revision commit.
