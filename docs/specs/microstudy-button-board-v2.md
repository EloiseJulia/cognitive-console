# Spec: V2 Button-Board Gate Application Micro-Study

- **Spec ID:** `microstudy-button-board-v2`
- **Status:** `DRAFT / NOT FROZEN / OWNER-LOCAL ONLY / NO HUMAN DATA`
- **Governance:** D-0116
- **Materials:** `v10-button-board-20260812-draft`
- **Preregistration:** [`../research/2026-08-12-microstudy-button-board-v2-DRAFT.md`](../research/2026-08-12-microstudy-button-board-v2-DRAFT.md)
- **Plan:** [`../plans/microstudy-button-board-v2.md`](../plans/microstudy-button-board-v2.md)

## 1. Scope and honest claim boundary

V2 is a single-presentation, within-participant local activity in which a person
sorts fictional household/phone items onto a four-place button board. It may
measure immediate comprehension and application of four placement gates after a
short tutorial. It does **not** test benefit, trust, safety, productivity,
control ability, real products, deployment, latent mechanisms, or whether one
interface format is better than another.

V2 has no Contract/Flat treatment. It cannot be pooled with V1/V9 and cannot
support the V9 Contract-minus-Flat estimand. All products, buttons, counts, and
records are fictional examples rather than empirical product claims.

## 2. Independent normative artifacts

The structured source and derivation logic are in:

- `src/cognitive_console/button_board_materials.py`

The generator writes:

- `data/microstudy_button_board_v10/materials.json`
- `data/microstudy_button_board_v10/sequences.json`
- `data/microstudy_button_board_v10/derived_keys.json`

Run:

```powershell
$env:PYTHONPATH = "src"
python scripts\generate_microstudy_v10.py --check
python scripts\validate_button_board_materials.py
```

`materials.json` is participant-public and contains no expected answer keys.
`derived_keys.json` is server/analysis-private and is generated from router
fields; it is never projected to browser payloads, DOM, ARIA, or exports.

## 3. Participant framing and flow

Every screen displays the fixed fictional-material disclaimer. Language is
chosen without a default and locked at `/api/start`. The flow is:

1. language gate;
2. welcome and anonymous code;
3. one intuition only: a response does not mean better than the existing method;
4. stamp/lock/boundary/reason operation demonstration;
5. one diagnostic practice with record-specific feedback only;
6. six formal cards with no feedback;
7. one post-formal attention check outside GAA;
8. optional structured reflection with no free text;
9. signed manual JSON/CSV export and no score display.

Participant-visible places are equal-weight, equal-size cells:

| Internal ID | English | 中文 |
|---|---|---|
| `Q1_SUPPORTED` | Use area | 常用区 |
| `Q1_DIAGNOSTIC` | Info card | 信息牌 |
| `Q1_WITHHELD` | Leave it off | 不装 |
| `Q1_UNRESOLVED` | Check again | 再看看 |

The cells use no red/green, checkmark, warning, rank, or default-focus cue.

## 4. Scenario library and closed blockers

The formal plan is one mutually exclusive F1/F2 slot plus F3–F7:

| Scene | Derived state | Decisive route |
|---|---|---|
| F1 receipt-folder tab | S | positive paired count, safe, exact boundary |
| F2 receipt-folder tab | W | no higher paired completion count |
| F3 soil-status tile | D | readable display without outcome-changing comparison |
| F4 quiet-reading tab | W | positive target count but priority-call harm |
| F5 mirror-clearing tile | U | four pairs with direction changing by time |
| F6 anti-static clip | U | positive count but key boundary fields missing |
| F7 meal-box tab | S | positive paired count, safe, exact boundary |

The three implementation blockers are closed by construction:

1. **No answer leakage:** formal records show raw counts, occasions, conditions,
   and observed effects without verdict labels. Tutorial and practice do not
   teach the full router.
2. **F1/F2 isolation:** the variants share the same item, setting, target,
   existing method, pairing, response count, effects, boundary, scope options,
   reason options, and location. Only `paired_comparison.raw_counts` differs.
   The canonical non-manipulated hash must match or generation fails. One attempt
   receives exactly one variant.
3. **Active boundary judgment:** F1, F6, and F7 require the boundary selection
   for Strict GAA. A wrong boundary removes Strict credit. F6 requires the
   explicit missing-boundary option.

F1/F2 use the same reason options. The correct reason changes only because the
router trace changes; variant-specific wording cannot become a second
manipulation.

## 5. Router and automatic derivation

Comparison is derived from structured paired records:

```text
no same-condition pair                       -> missing
direction reverses across frozen blocks      -> mixed
paired trials < 8                            -> thin
new_success - old_success >= 2               -> decisive_positive
new_success <= old_success                   -> decisive_negative
otherwise                                    -> thin
```

State priority:

```text
quality fail OR decisive_negative                    -> Q1_WITHHELD
decisive_positive + quality pass + exact boundary    -> Q1_SUPPORTED
usable read + missing comparison                     -> Q1_DIAGNOSTIC
otherwise                                            -> Q1_UNRESOLVED
```

Reason class, correct reason ID, correct boundary ID, paper-state shorthand, and
`scope_gate_required` are generated from this trace. Option records carry
non-public semantic tags, not hand-entered expected keys. Missing or
non-unique matches fail generation.

## 6. Measures

For six formal cards:

```text
GAA_trial = 1 iff Q1 stamp equals the derived four-state route
Strict_GAA_trial = 1 iff Q1 is correct
                   AND reason choice is correct
                   AND, when required, boundary choice is correct
```

The attention check is not part of GAA. Primary summaries may exclude failed
attention checks only while also reporting all-completer sensitivity. Secondary
descriptions include state confusion, reason class, F1/F2 variant judgments,
F1/F7 exact-boundary choice, F6 missing-boundary recognition, relative response
times, completion, and structured reflection.

## 7. Allocation, export, and coexistence

Within each locale, successful starts cycle through 24 cells: every one of 12
balanced six-card sequences is paired once with F1 and once with F2. Allocation
is locked after start. Four-place visual orders are near-balanced inside every
sequence and exactly balanced over all sequences. Scope and reason options use a
stable hash of participant code, scene ID, material hash, and question kind.

Identity is independent of V9:

```text
schema_version: microstudy-button-board-v10-bilingual
materials_version: v10-button-board-20260812-draft
export_schema: microstudy-export-v7-button-board-raw-signed
analysis_version: button-board-gaa-v2
```

V5/V6/V7 or V9/V10 mixtures fail closed. V2 uses
`cognitive_console.button_board`; the existing `cognitive_console.microstudy`
V9 entry point and default remain unchanged.

Signed V7 JSON and CSV exports contain only raw selections, presentation
orders, completion state, and relative timing. They must not contain
`scope_gate_required`, correctness flags, GAA scores, attention-pass flags, or
other answer-derived scoring keys. Validation and analysis recompute all scores
privately from the structured materials and raw responses.

`q1_locked_at` is an integer number of milliseconds relative to local session
start, not an absolute timestamp. Q1, boundary, and reason response times are
likewise relative monotonic durations and are descriptive only.

## 8. Security, privacy, and accessibility

The V2 server reuses the audited V9 fail-closed verification-key implementation
and independently enforces loopback Host/origin, CSRF, per-session capability,
request-ID idempotency, request size, session capacity, monotonic TTL renewed
only after success, volatile memory, no access log, no PII, no absolute
timestamps, no browser storage, and no resume.

Automated gates cover Chrome and Edge, English and Simplified Chinese,
1280×800/1440×900, 100%/200%, keyboard radio/button operation, heading focus,
equal board-cell geometry, DOM/ARIA privacy, no horizontal clipping, manual
downloads, and the 1279-pixel desktop block. Manual screen-reader and human
bilingual semantic review remain open.

## 9. Human gates

This implementation authorizes owner-local preview only. Before any human data:

- ethics/IRB applicability and recruitment/compensation approval;
- privacy and retention approval;
- human English/Chinese stable-ID semantic review;
- hostile answer-leakage and name-guessing review;
- reason-length and unique-answer review;
- boundary-option cognitive interviews;
- manual screen-reader, color, keyboard, 200%, responsive/mobile checks;
- 5–10 person cognitive/usability work;
- timing and defensible GAA/Strict-GAA/F1-F2 sample-size basis;
- Protocol Freeze;
- explicit approval before exploratory findings become confirmatory evidence.
