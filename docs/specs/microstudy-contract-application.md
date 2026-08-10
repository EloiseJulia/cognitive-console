# Spec: Contract Legibility/Application Micro-Study

- **Spec ID:** `microstudy-contract-application`
- **Status:** implementation-ready protocol/material specification; no human-data authorization
- **Study class:** exploratory formative micro-study
- **Target:** desktop-only, approximately 10 minutes, approximately 20 technical GenAI users
- **Authorized scope:** protocol, materials, and local web engineering only
- **Prohibited scope:** recruitment, ethics submission, public deployment, human pilot/data collection, paper-claim changes
- **Related draft preregistration:** [`../research/2026-08-10-microstudy-contract-application-DRAFT.md`](../research/2026-08-10-microstudy-contract-application-DRAFT.md)
- **Implementation plan:** [`../plans/microstudy-contract-application-web.md`](../plans/microstudy-contract-application-web.md)

## 1. Objective and research question

### Objective

Determine whether the paper's five-field contract is easier to apply when the same primitive evidence is organized with contract-relevant semantic grouping/headings rather than shown as neutral flat records.

### Research question

With primitive evidence, values, qualification legend, order, typography, color, viewport, and scrolling held constant, does semantic contract organization improve correct application of the current four-state routing rules relative to an information-matched flat panel?

This study evaluates **contract legibility and rule application only**. It does not evaluate calibrated reliance, user benefit, trust, deployment safety, latent-control effectiveness, or whether the paper's model evidence is correct.

## 2. Allowed claims and non-claims

### Potential exploratory claims

If supported by the collected data after owner authorization:

1. In this small technical-user sample and these simulated records, semantic grouping was associated with a participant-level difference in correct contract application.
2. The study estimates state-identification accuracy, transfer/reason accuracy, joint contract-application accuracy (CCA), response time, and perceived block ease.
3. Errors identify specific rule-application confusions that can inform interface revision.

### Non-claims

- No calibrated-reliance, behavioral-benefit, safety, productivity, trust, or deployment claim.
- No causal generalization beyond this within-subject manipulation, item set, and recruited technical-user population.
- No population prevalence or representative-user claim.
- No claim that the hypothetical evidence-supported item exists in the current paper. The current paper has no passing latent behavioral positive control.
- No upgrade of exploratory findings to confirmatory evidence or paper claims without a new owner decision and protocol gate.
- No claim about whether latent control is generally possible or impossible.

## 3. Personas and eligibility

### Intended participant persona

A desktop user with practical familiarity with GenAI systems and basic comfort reading compact evaluation records. Examples include ML/HCI researchers, engineers, technical product practitioners, or advanced technical students.

### Owner-managed screening boundary

Recruitment and ethics are outside this implementation. The site records no screening answers. The owner determines eligibility outside the site and provides:

- an anonymous participant code;
- one sequence code: `A`, `B`, `C`, or `D`.

The site must not collect name, email, employer, location, age, gender, ethnicity, education, disability, or other demographics.

## 4. Experimental design

### 4.1 Structure

- Within-subject comparison:
  - **Contract UI**
  - **Info-Matched Flat Panel**
- 1 unscored practice trial.
- 10 scored trials total: 5 per condition.
- Two blocks of 5 scored trials.
- Four-sequence counterbalance crosses:
  1. block order; and
  2. item-set-to-condition mapping.
- Desktop-only. Minimum supported CSS viewport: `1024 × 700`.
- No live model, network request, analytics, server storage, or public deployment.

### 4.2 Treatment isolation and parity

Both conditions show the same five primitive evidence propositions for the assigned stimulus, in the same proposition order, with byte-equivalent normalized evidence text.

Held constant:

- evidence propositions and values;
- qualification legend;
- answer options and answer key;
- evidence order;
- font family, size, weight budget, line height, color tokens, spacing budget, viewport, card width, and scroll behavior;
- question wording and option order;
- navigation and timing behavior.

Only treatment:

- **Contract UI:** propositions are grouped under semantic headings that name the evidence role without stating the final route.
- **Flat Panel:** the same propositions appear as neutral records (`Record 1` … `Record 5`) without semantic grouping.

| Primitive | Contract UI heading | Flat heading |
|---|---|---|
| 1 | Representation evidence | Record 1 |
| 2 | Comparative behavior evidence | Record 2 |
| 3 | Bounded prompt comparator | Record 3 |
| 4 | Calibration and reliability qualification | Record 4 |
| 5 | Scope and evidence tier | Record 5 |

Headings are presentation metadata and are excluded from normalized evidence-text parity. The evidence panel itself never uses a direct final-state label or the word `TRANSFER`.

Neither condition may display:

- the final four-state answer;
- a `TRANSFER` label or aggregate transfer verdict;
- a recommended action;
- pass/fail badges, green status, deploy icons, checkmarks, traffic lights, or directional recommendation language.

### 4.3 Machine-checkable parity contract

For each `stimulus_id` and rendering condition:

```text
normalize(contract.evidence[*].text)
  == normalize(flat.evidence[*].text)
contract.answer_key == flat.answer_key
contract.evidence[*].primitive_id == flat.evidence[*].primitive_id
contract.evidence[*].order == flat.evidence[*].order
```

Normalization is: Unicode NFKC, trim, collapse whitespace, normalize CRLF to LF, and exclude headings/DOM wrappers. A test must reject any evidence-text, value, legend, item, or answer-key drift. A DOM allowlist must restrict condition differences to heading text, grouping wrappers, and associated accessibility relationships.

## 5. Current four-state routing contract

The implementation must mirror the current narrative checker:

| Evidence pattern | Correct state |
|---|---|
| READ unsupported | Unresolved |
| READ supported; comparative behavior not yet tested | Diagnostic only |
| Comparative behavior tested and failed | Withheld control |
| Comparative behavior underpowered or inconclusive | Unresolved |
| Comparative pass with coherence | Evidence-supported control at the exact stated tier |

Additional constraints:

- Diagnostic evidence may remain visible within a withheld-control presentation, but the primary state remains withheld control.
- A method/model/task/scope change returns the candidate to unresolved until new READ and comparative evidence exist.
- The hypothetical passing records are synthetic teaching cases, not paper evidence.

## 6. Stimulus schema proposal and answer key

Implementation should later materialize this appendix as a versioned JSON file. The specification below is authoritative until that JSON is generated and reviewed.

### 6.1 Proposed schema

```yaml
schema_version: microstudy-stimuli-v1
stimulus_id: string
content_set: X | Y
pattern_id: P1 | P2 | P3 | P4 | P5
pattern_name: string
surface_variant_pair:
  contract_render_id: string
  flat_render_id: string
source_status: synthetic | real-inspired-non-pass
source_note: string
simulated_record_notice: "Simulated evaluation record — not a current paper result."
held_out_transfer: boolean
primitive_evidence:
  - primitive_id: read
    proposition: string
  - primitive_id: behavior
    proposition: string
  - primitive_id: comparator
    proposition: string
  - primitive_id: qualification
    proposition: string
  - primitive_id: tier
    proposition: string
questions:
  q1:
    prompt: string
    options: [Q1_UNRESOLVED, Q1_DIAGNOSTIC, Q1_WITHHELD, Q1_SUPPORTED]
    correct_key: string
  q2:
    prompt: string
    options: [Q2_UNRESOLVED_RULE, Q2_DIAGNOSTIC_RULE, Q2_WITHHELD_RULE, Q2_SUPPORTED_RULE]
    correct_key: string
answer_key_derivation:
  checker_rule: string
  claim_scope: rule_application_only
```

### 6.2 Standard question options

**Q1: Which interface state follows from this record?**

| Key | Option text |
|---|---|
| `Q1_UNRESOLVED` | Unresolved |
| `Q1_DIAGNOSTIC` | Diagnostic only |
| `Q1_WITHHELD` | Withheld control |
| `Q1_SUPPORTED` | Evidence-supported control at the stated tier |

**Q2: Which contract rule best justifies that state?**

| Key | Option text |
|---|---|
| `Q2_UNRESOLVED_RULE` | Required representation or comparative evidence is absent, untested, underpowered, or inconclusive; the record stays unresolved. |
| `Q2_DIAGNOSTIC_RULE` | Representation evidence exists, but comparative behavior has not been tested; the record is diagnostic only. |
| `Q2_WITHHELD_RULE` | Comparative behavior was tested and failed, or coherence failed; control is withheld even if diagnostic evidence remains. |
| `Q2_SUPPORTED_RULE` | Comparative behavior passed and coherence held; control is supported only at the exact stated tier. |

### 6.3 Ten scored stimuli

All values and records below are safe synthetic teaching materials and are **not sourced from paper numbers**. No raw harmful content is used.

| ID | Pattern → state | Primitive evidence propositions in fixed order | Q1 / Q2 key | Status | Variant pair | Held-out |
|---|---|---|---|---|---|---|
| `MS-P1-X` | P1 READ unsupported → Unresolved | (1) Representation check did not meet its stated support rule. (2) No comparative behavior result is available. (3) The bounded prompt comparator is documented but was not compared. (4) Coherence was not evaluated. (5) Scope is simulated model Alpha / method North / task editing. | `Q1_UNRESOLVED` / `Q2_UNRESOLVED_RULE` | synthetic | `MS-P1-X-contract`, `MS-P1-X-flat` | false |
| `MS-P1-Y` | P1 READ unsupported → Unresolved | (1) Representation check was unstable across the stated resamples. (2) No comparative behavior result is available. (3) The bounded prompt comparator is specified but unused. (4) Reliability qualification is unavailable. (5) Scope is simulated model Beta / method Cedar / task triage. | `Q1_UNRESOLVED` / `Q2_UNRESOLVED_RULE` | synthetic | `MS-P1-Y-contract`, `MS-P1-Y-flat` | false |
| `MS-P2-X` | P2 READ supported, behavior untested → Diagnostic only | (1) Representation check met its local support rule. (2) Comparative behavior has not been run. (3) The bounded prompt comparator and budget are specified. (4) Coherence has not been evaluated. (5) Scope is simulated model Alpha / method Cedar / task summarization. | `Q1_DIAGNOSTIC` / `Q2_DIAGNOSTIC_RULE` | synthetic | `MS-P2-X-contract`, `MS-P2-X-flat` | false |
| `MS-P2-Y` | P2 READ supported, behavior untested → Diagnostic only | (1) Representation check met its stated local criterion. (2) Comparative behavior is marked not yet evaluated. (3) The bounded prompt comparator is reconstructable. (4) Reliability qualification awaits the comparison. (5) Scope is simulated model Beta / method North / task classification. | `Q1_DIAGNOSTIC` / `Q2_DIAGNOSTIC_RULE` | synthetic | `MS-P2-Y-contract`, `MS-P2-Y-flat` | false |
| `MS-P3-X` | P3 tested failure → Withheld control | (1) Representation check met its local support rule. (2) Comparative behavior was evaluated and did not meet the stated superiority rule. (3) The bounded prompt comparator used the same item and selection budget. (4) Coherence remained within its allowed range. (5) Scope is simulated model Alpha / method North / task planning. | `Q1_WITHHELD` / `Q2_WITHHELD_RULE` | synthetic | `MS-P3-X-contract`, `MS-P3-X-flat` | false |
| `MS-P3-Y` | P3 tested failure → Withheld control | (1) Representation check met its local criterion. (2) Comparative behavior was evaluated and its interval did not satisfy the required direction and margin. (3) The bounded prompt comparator was selected without test-item access. (4) Coherence remained acceptable. (5) Scope is simulated model Beta / method Cedar / task review. | `Q1_WITHHELD` / `Q2_WITHHELD_RULE` | synthetic | `MS-P3-Y-contract`, `MS-P3-Y-flat` | false |
| `MS-P4-X` | P4 underpowered → Unresolved | (1) Representation check met its local support rule. (2) Comparative behavior was run, but its resolution was too low for the stated margin. (3) The bounded prompt comparator followed the matched budget. (4) Coherence remained within range. (5) Scope is simulated model Alpha / method Cedar / task extraction. | `Q1_UNRESOLVED` / `Q2_UNRESOLVED_RULE` | synthetic | `MS-P4-X-contract`, `MS-P4-X-flat` | false |
| `MS-P4-Y` | P4 underpowered → Unresolved | (1) Representation check met its stated criterion. (2) Comparative behavior was inconclusive at the registered resolution. (3) The bounded prompt comparator followed the same selection discipline. (4) Coherence remained acceptable. (5) Scope is simulated model Beta / method North / task ranking. | `Q1_UNRESOLVED` / `Q2_UNRESOLVED_RULE` | synthetic | `MS-P4-Y-contract`, `MS-P4-Y-flat` | true |
| `MS-P5-X` | P5 pass + coherence → Evidence-supported exact tier | (1) Representation check met its local support rule. (2) Comparative behavior met the stated direction, margin, and interval rule. (3) The bounded prompt comparator used the matched budget and held-out items. (4) Coherence remained within the allowed range. (5) Qualification is limited to simulated model Alpha / method North / task routing / protocol tier S1. | `Q1_SUPPORTED` / `Q2_SUPPORTED_RULE` | synthetic hypothetical pass; current paper has no pass | `MS-P5-X-contract`, `MS-P5-X-flat` | true |
| `MS-P5-Y` | P5 pass + coherence → Evidence-supported exact tier | (1) Representation check met its stated local criterion. (2) Comparative behavior met the required direction, margin, and interval rule. (3) The bounded prompt comparator was reconstructable and matched in budget. (4) Coherence remained acceptable. (5) Qualification is limited to simulated model Beta / method Cedar / task verification / protocol tier S2. | `Q1_SUPPORTED` / `Q2_SUPPORTED_RULE` | synthetic hypothetical pass; current paper has no pass | `MS-P5-Y-contract`, `MS-P5-Y-flat` | false |

Each participant sees every stimulus ID exactly once and therefore never sees both UI renderings of the same content. X and Y are content-distinct instances of the same routing pattern, not duplicate wording.

### 6.4 Practice item

Practice is an unscored, synthetic P2-style record using different model/method/task nouns and different proposition wording from all scored items. It is rendered in a neutral tutorial frame that explains how to answer Q1 and Q2 but does not expose any scored answer. It must not rehearse the held-out P4/P5 distinction.

## 7. Exact four-sequence mapping

`X` means the five X stimuli; `Y` means the five Y stimuli. Within each block, use the fixed order P1, P3, P2, P5, P4 or a precomputed order that is identical for both conditions and all sequences. Do not runtime-randomize.

| Sequence | Block 1 | Block 2 | Contract receives | Flat receives |
|---|---|---|---|---|
| `A` | Contract / X | Flat / Y | X | Y |
| `B` | Flat / Y | Contract / X | X | Y |
| `C` | Contract / Y | Flat / X | Y | X |
| `D` | Flat / X | Contract / Y | Y | X |

Balance properties:

- A/B versus C/D approximately balances each content set across conditions.
- A/C versus B/D balances block order.
- Each stimulus is rendered in Contract for two sequences and Flat for two sequences.
- Every participant receives one held-out/unpracticed item per condition: X designates P5 as held out and Y designates P4 as held out. Thus each condition receives exactly one `held_out_transfer=true` item under every sequence.
- No participant receives both renderings of any `stimulus_id`.

Owner assignment should rotate A→B→C→D in enrollment order or use pre-generated balanced envelopes; the site does not allocate sequences.

## 8. Ten-minute page flow and textual wireframes

Target timing is a design budget, not an exclusion rule.

| Page | Target | Content |
|---|---:|---|
| 1. Local landing | 20 s | “Simulated records; local-only preview”; study scope; no benefit/reliance claim |
| 2. Session setup | 20 s | anonymous owner-assigned code; sequence A–D; desktop check |
| 3. Contract legend/tutorial | 60 s | five primitive evidence roles; four state definitions; no scored example answer |
| 4. Practice | 45 s | one unscored record; Q1/Q2; immediate explanation |
| 5. Block 1 | 180 s | five scored trials, one screen each |
| 6. Block ease | 15 s | one 5-point ease item |
| 7. Short transition | 10 s | neutral break; no performance feedback |
| 8. Block 2 | 180 s | five scored trials |
| 9. Block ease | 15 s | same ease item |
| 10. Review/export | 30 s | completion summary without correctness; JSON/CSV download buttons |

### Trial screen wireframe

```text
+---------------------------------------------------------------+
| Simulated evaluation record                 Trial 3 of 10     |
| Not a current paper result                                      |
+---------------------------------------------------------------+
| [Contract semantic group OR neutral records; same dimensions] |
| Heading/Record 1                                               |
| Primitive evidence proposition                                 |
| ... five propositions in fixed order ...                       |
| Qualification legend (identical)                               |
+---------------------------------------------------------------+
| Q1 Which interface state follows?  [four radio options]        |
| Q2 Which rule best justifies it?    [four radio options]        |
|                                               [Next]            |
+---------------------------------------------------------------+
```

No correctness feedback appears after scored trials. Back navigation is disabled after submission to preserve timing and answers.

## 9. Timing, accessibility, and interaction requirements

### Timing

- Record relative monotonic durations only:
  - `trial_rt_ms`: record render to valid submission;
  - `block_rt_ms`: first record render to block-ease render;
  - `study_rt_ms`: tutorial start to export-ready state.
- Pause timing while the document is hidden; store `hidden_ms` separately and subtract it from RT.
- Do not store absolute timestamps.

### Accessibility

- Semantic landmarks, heading hierarchy, fieldsets, legends, and explicit labels.
- Full keyboard operation with visible focus.
- No meaning conveyed by color alone; no green/deploy status iconography.
- Minimum 4.5:1 text contrast and 3:1 control/focus contrast.
- Respect `prefers-reduced-motion`; no timed animation.
- Zoom to 200% without loss of content or horizontal scrolling at supported desktop width.
- Screen-reader condition parity: the evidence text and answer options must be identical; semantic grouping may differ only as the intended treatment.
- Error messages identify missing Q1/Q2 without clearing selections.

## 10. Privacy and local-only security boundary

- Static local site bound to `127.0.0.1`; never `0.0.0.0`.
- No network dependencies, analytics, cookies, telemetry, service worker, CDN fonts, external assets, fetch to remote origins, or live model.
- No server persistence. Session state remains in memory/local browser state until download or reset.
- No sensitive demographics, free text, names, emails, IP address, user agent, screen fingerprint, geolocation, or absolute timestamps.
- Anonymous code format: owner-defined 4–24 characters, allowlist `[A-Za-z0-9_-]`; the code is not generated or resolved by the site.
- A reset action clears all session data after explicit confirmation.

## 11. Exact local export schema

### JSON

```json
{
  "schema_version": "microstudy-export-v1",
  "study_id": "microstudy-contract-application",
  "materials_version": "TBD_COMMIT",
  "participant_code": "OWNER_ASSIGNED",
  "sequence": "A",
  "completion": {
    "practice_completed": true,
    "scored_trials_present": 10,
    "eligible_for_primary": true,
    "exclusion_reason": null
  },
  "responses": [
    {
      "trial_index": 1,
      "block_index": 1,
      "condition": "contract",
      "stimulus_id": "MS-P1-X",
      "pattern_id": "P1",
      "held_out_transfer": false,
      "q1_key": "Q1_UNRESOLVED",
      "q2_key": "Q2_UNRESOLVED_RULE",
      "q1_correct": true,
      "q2_correct": true,
      "cca_correct": true,
      "trial_rt_ms": 18000,
      "hidden_ms": 0
    }
  ],
  "block_ease": [
    {"block_index": 1, "condition": "contract", "ease_1_to_5": 4},
    {"block_index": 2, "condition": "flat", "ease_1_to_5": 3}
  ],
  "relative_timing": {
    "study_rt_ms": 480000
  }
}
```

Forbidden export fields: absolute timestamp, IP, UA, referrer, location, demographics, free text, recruitment source, or device fingerprint.

### CSV

One row per scored trial with repeated session fields:

```text
schema_version,study_id,materials_version,participant_code,sequence,
trial_index,block_index,condition,stimulus_id,pattern_id,held_out_transfer,
q1_key,q2_key,q1_correct,q2_correct,cca_correct,trial_rt_ms,hidden_ms,
block_ease_1_to_5,scored_trials_present,eligible_for_primary,exclusion_reason
```

CSV must use RFC 4180 quoting, UTF-8 with BOM optional, LF or CRLF consistently, and spreadsheet-formula escaping for any cell beginning with `=`, `+`, `-`, or `@`.

## 12. Missingness, exclusion, and preview behavior

- Primary analysis excludes sessions with fewer than 8 of 10 scored trials present.
- No performance-based exclusion.
- No RT-based participant exclusion; impossible/zero RT is flagged for audit, not silently removed.
- Primary scoring uses available scored trials only for sessions with at least 8.
- Required sensitivity: all missing Q1/Q2 components count as incorrect; CCA is correct only when both are correct.
- Practice performance never excludes a participant.
- Preview mode and practice mode must write no exportable scored response unless the operator explicitly starts a local session.
- Pilot stop rules are retained in the DRAFT preregistration, but only the owner may run a human pilot.

## 13. File plan

Expected implementation files:

```text
src/cognitive_console/microstudy/
  __init__.py
  __main__.py
  server.py
  schema.py
  sequencing.py
  scoring.py
  export.py
  static/index.html
  static/app.js
  static/styles.css
  data/stimuli.json
  data/sequences.json
tests/
  test_microstudy_schema.py
  test_microstudy_parity.py
  test_microstudy_routing.py
  test_microstudy_sequences.py
  test_microstudy_export.py
  test_microstudy_server.py
```

No paper source, paper claims, frozen result artifact, or existing checker rule may be changed by the implementation slice.

## 14. Run and test contract

Proposed local commands after implementation:

```powershell
python -m cognitive_console.microstudy --host 127.0.0.1 --port 8765 --preview
python -m pytest -q tests\test_microstudy_schema.py tests\test_microstudy_parity.py tests\test_microstudy_routing.py tests\test_microstudy_sequences.py tests\test_microstudy_export.py tests\test_microstudy_server.py
python -m pytest -q
```

The CLI must reject non-loopback hosts. `--preview` is the default and cannot produce a completed study export without an explicit “Start local session” action.

## 15. Acceptance criteria

1. All 10 scored stimuli validate against the schema and route to the specified current-checker state.
2. Contract/Flat normalized primitive evidence, values, legend, questions, options, and answer keys are identical for every stimulus.
3. Automated DOM/CSS parity test finds only allowlisted grouping/headings differences.
4. Four sequences exactly implement the table and balance each stimulus across conditions.
5. Each participant sees 10 unique stimulus IDs, 5 per condition, with no repeated content rendering.
6. Exactly one designated held-out/unpracticed item appears per condition and sequence.
7. No stimulus contains final-state, aggregate-transfer, pass/fail recommendation, green, deploy, or recommended-action leakage.
8. All records visibly state that they are simulated; hypothetical pass records explicitly state that the current paper has no pass.
9. Q1, Q2, CCA, RT, hidden time, and block ease are scored/exported as specified.
10. Export contains no forbidden field and works offline as both JSON and CSV.
11. Site makes no network request and binds only to loopback.
12. Keyboard, focus, contrast, zoom, reduced-motion, and screen-reader checks pass.
13. Fewer-than-8 exclusion and missing-as-incorrect sensitivity are reproducible from export.
14. No recruitment, public deployment, human pilot, data collection, paper edit, or claim upgrade occurs in this slice.
