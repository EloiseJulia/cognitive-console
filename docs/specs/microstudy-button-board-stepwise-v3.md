# Spec: V3 Stepwise Open-Book Button-Board Micro-Study

- **Spec ID:** `microstudy-button-board-stepwise-v3`
- **Status:** `DRAFT / NOT FROZEN / OWNER-LOCAL ONLY / NO HUMAN DATA`
- **Governance:** D-0117
- **Materials:** `v11-stepwise-20260812-draft`
- **Preregistration:** [`../research/2026-08-12-microstudy-button-board-stepwise-v3-DRAFT.md`](../research/2026-08-12-microstudy-button-board-stepwise-v3-DRAFT.md)
- **Plan:** [`../plans/microstudy-button-board-stepwise-v3.md`](../plans/microstudy-button-board-stepwise-v3.md)

## Scope and claim boundary

V3 may measure accuracy when applying frozen evidence thresholds one question at
a time after short teaching while the fictional trial card and reference panel
remain visible. It does not test benefit, trust, safety, control, efficiency,
long-term memory, Contract/Flat, latent mechanisms, real products, or whether
V3 is better than V1/V9 or V2/V10. All counts and products are synthetic design
inputs, not empirical findings.

## Independent identity and coexistence

V3 uses:

```text
entry point: cognitive_console.button_board_stepwise
data directory: data/button_board_stepwise_v11
schema: microstudy-button-board-stepwise-v11-bilingual
materials: v11-stepwise-20260812-draft
export: microstudy-export-v7-stepwise-bilingual-signed
analysis: button-board-stepwise-gaa-v1
```

V1/V9, V2/V10, and V3/V11 coexist. Their materials, schemas, entry points,
exports, analyses, and any future observations cannot be pooled or backfilled.
The V9 and V2 defaults remain unchanged.

## Interaction

- Left: the complete fictional card, including “What you originally did,” stays
  visible for the entire trial.
- Right: a 300 px sticky open-book panel keeps four equal-weight destinations
  and the six-question checklist visible.
- Below the card: exactly one applicable question appears.
- Submitted answers cannot be changed. Branch exits hide later steps.
- The result repeats only the participant-derived destination and raw path. It
  never displays correctness, an expected path, or a score.
- Practice P1 teaches only that an action occurring is not the same as meeting
  the target more often. Formal trials provide no feedback.

The frozen route is:

```text
INFO -> DIAGNOSTIC
CONTROL + NOT_COMPARED -> UNRESOLVED
CONTROL + COMPARED + NOT_BETTER -> WITHHELD
CONTROL + COMPARED + BETTER + HARM -> WITHHELD
CONTROL + COMPARED + BETTER + NO_HARM + SCOPE_MISSING -> UNRESOLVED
CONTROL + COMPARED + BETTER + NO_HARM + SCOPE_WRITTEN + any scope -> SUPPORTED
```

## Typed fact source and derivation

`src/cognitive_console/button_board_stepwise_materials.py` is the only source
for participant card text, comparison fields, scope values, scope options, and
private expected derivation. Every scene uses one method-map comparison schema:

```text
methods.existing = {rounds, denominator, successes}
methods.new      = {rounds, denominator, successes}
```

F4 is represented in that schema as 0 existing-method rounds and 10 new-item
rounds. Card sentences are rendered from the same typed values. Validation
requires all denominators, counts, alignment labels, and scope values to occur
in the generated card.

The source cannot contain `expected_*`, `compared`, `better`, `harm`,
`scope_written`, or `scope_correct`. The generator derives those fields,
`expected_answer_by_step`, exit answer, decisive step, and state. Public
materials omit all private fields.

## Frozen scenario set

Each attempt receives P1, one mutually exclusive AB1 variant, F2–F6, and AC1:

| Scene | Derived exit |
|---|---|
| P1 sock-drawer key | W at Step 3 |
| AB1-A receipt-folder finder | S at Step 6 |
| AB1-B receipt-folder finder | W at Step 3 |
| F2 pot-soil status tile | D at Step 1 |
| F3 quiet-reading notification key | W at Step 4 |
| F4 insole drying key | U at Step 2 |
| F5 static-release clip | U at Step 5 |
| F6 mirror clearing tile | S at Step 6 |

AB1-A/B differ only in existing/new target counts. Each variant still exposes
all four states across six formal trials.

## Scope-option constraints

Every Step 6 option uses the same dimension order and equal-width slots. English
word counts match; normalized Chinese lengths differ by at most one character.
Each distractor changes exactly one dimension from the faithful vector. Stable
IDs and structure are shared across locales; position is a stable hash of
participant, scene, material hash, and question type. Human bilingual semantic
equivalence review remains open.

## Measures and leakage boundary

```text
GAA = participant-derived final state equals machine-derived expected state
Strict = GAA + exact full path + correct decisive exit reading
```

A wrong Step 6 scope still yields participant state S and therefore may retain
GAA, but it fails Strict. AC1 is excluded from both.

Participant payload, DOM, ARIA, logs, and raw signed JSON/CSV contain no
expected path, structural key, comparison rule, correct scope, GAA, Strict, or
correctness marker. Offline analysis verifies the signature, reconstructs the
plan from exact V11 hashes, re-derives expected values, and fails closed on any
V5/V6/V7/V9/V10/V11 mixture.

## Security, privacy, and accessibility

The independent V3 server is loopback-only and volatile. It enforces Host,
Origin, CSRF, per-session capability, request-ID idempotency, capacity, request
size, and success-only TTL. The verification key is never sent to the browser.
There are no access logs, absolute timestamps, browser storage, resume, free
text, or automatic downloads.

Automated gates cover Chrome and Edge, English and Simplified Chinese, 100% and
200%, native keyboard controls, heading focus, DOM/ARIA leakage, sticky
open-book layout, one-question flow, complete/partial export, and the 1023 px
desktop block. Manual screen-reader and human semantic review remain open.

## Human gates

Before any human data: ethics/IRB applicability; recruitment, compensation,
privacy, retention, and deletion approval; owner bilingual material approval;
two independent structural reviews; 5–10 cognitive/usability interviews;
special checks for matched conditions, priority contact, and missing scope;
ceiling/floor, timing, and over-teaching review; manual accessibility; sample
size/MDE; preregistration; and Protocol Freeze. No public deployment,
recruitment, paper claim, or exploratory-to-confirmatory upgrade is authorized.
