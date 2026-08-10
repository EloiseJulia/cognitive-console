# Spec: Contract Legibility/Application Micro-Study

- **Spec ID:** `microstudy-contract-application`
- **Status:** `DRAFT / NOT FROZEN / materials-only / protocol-finalization revision`
- **Study class:** exploratory formative micro-study
- **Authorized:** protocol, simulated materials, validators, and future loopback implementation
- **Not authorized:** recruitment, ethics administration, pilot/data collection, public deployment, or paper changes
- **Preregistration:** [`../research/2026-08-10-microstudy-contract-application-DRAFT.md`](../research/2026-08-10-microstudy-contract-application-DRAFT.md)
- **Implementation plan:** [`../plans/microstudy-contract-application-web.md`](../plans/microstudy-contract-application-web.md)

## 1. Normative machine-readable materials

The sole source of truth for trial materials and exported material fields is:

- [`../../data/microstudy_contract_application/stimuli.json`](../../data/microstudy_contract_application/stimuli.json)
- [`../../data/microstudy_contract_application/sequences.json`](../../data/microstudy_contract_application/sequences.json)

The JSON contains the exact ten records, proposition strings, Flat permutations, Q1 text/options, Q2 templates and assignments, structured router inputs, render contract, provenance, tutorial/legend, practice and feedback, post-task diagnostic, block-ease item, debrief, export fields, tokenization, heuristic definitions, and generated sequences. Documentation summarizes those records and must not become a second answer-key or stimulus source. A future website must consume these files and must not hardcode another materials copy.

Run:

```powershell
python scripts\validate_microstudy_materials.py
python -m pytest -q tests\test_microstudy_materials.py
```

The validator, not Markdown parsing, generates and validates answer keys and all reported material metrics.

## 2. Construct, treatment, and flow

The study measures **structured rule application**: whether technical GenAI users combine five displayed contract inputs to select an interface state, then answer a separate evidence/scope/comparator judgment. It does not measure deep integration, transfer, calibrated reliance, benefit, trust, safety, productivity, deployment, or latent control.

The treatment is a semantic-organization package:

- **Contract:** exact labels `READ`, `TRANSFER`, `BOUNDED PROMPT COMPARATOR`, `CALIBRATION WARNING`, `EVIDENCE TIER`, in fixed role order.
- **Flat:** exact neutral labels `Evidence A`–`Evidence E`, with per-item order read from `flat_order`.
- Both consume the same canonical proposition map and use identical questions, options, dimensions, word limits, viewport, and no-scroll behavior.

Every practice/formal card begins `Simulated evaluation record`. Q1 is persisted and irreversibly locked before Q2 appears. Formal trials show no correctness feedback. The primary outcome is:

```text
CCA = 1 iff Q1 is correct AND Q2 is correct
```

## 3. State routing and P3-Y repair

The five-input router in `stimuli.json` is the sole Q1 authority. Its priority is:

1. tier mismatch → unresolved;
2. READ unsupported → unresolved;
3. READ supported plus comparison untested → diagnostic-only;
4. missing comparison resolution or a CI crossing/touching zero (`ci_low <= 0 <= ci_high`) → unresolved;
5. resolved non-superiority, or a wholly positive CI with point estimate below the registered margin → withheld;
6. TRANSFER passes only when `tested && ci_low > 0 && estimate >= registered_margin`; then coherence fail/unavailable → withheld;
7. the same TRANSFER pass plus coherence pass → supported at the exact tier.

A tier change invalidates inherited inputs. Item IDs and pattern IDs are never state authority. Numeric comparisons use the exact JSON values with no floating tolerance: `estimate >= margin` is inclusive and `ci_low > 0` is strict.

`MS-P3-Y` remains Q1 withheld because its resolved interval is wholly non-positive. Its Q2 no longer asks for coherence: coherence cannot be the next required evaluation after non-superiority has already resolved the state. The authoritative record instead makes the scope boundary unavailable and uses `Q2-NEXT` option C, “Establish the missing scope boundary at this tier now.” This changes no Q1 routing input or Q1 key.

The validator must derive all ten Q1 keys from structured inputs and score `10/10`.

## 4. Leakage and parity gates

The authoritative JSON freezes:

- Q2 template reuse `NEXT=4`, `BASELINE=4`, `COVERAGE=2`;
- key distribution `A=2, B=2, C=3, D=3`;
- oracle fixed-per-template `3/10`, exact one-sided binomial `p=0.4744071960449219`;
- leave-one-item-out template-frequency `0/10`, `p=1.0`;
- global fixed position `3/10`, `p=0.4744071960449219`;
- equal-length `2/10`, `p=0.7559747695922852`;
- negation-marker `3/10`, `p=0.4744071960449219`;
- modal-marker `2/10`, `p=0.7559747695922852`;
- READ-lexical `2/10`, `p=0.7559747695922852`;
- single-comparison-row Q1 `8/10`, descriptive only;
- single-row plus oracle Q2 `2/10 CCA`, `p=0.7559747695922852`;
- single-row plus LOO Q2 `0/10 CCA`, `p=1.0`.

All inferential values use an inclusive exact one-sided binomial upper tail versus `0.25`. Tokenization and every heuristic are algorithmically defined in `validation_contract`; no post-inspection tuning is permitted. LOO and global-position results remain separate.

Parity validation additionally proves:

- both renderers derive from one proposition map;
- NFKC/token-normalized proposition equality;
- every primitive occupies every Flat position exactly twice;
- byte-identical question/options for every use of a Q2 template;
- zero answer-state phrases in formal primitive/Q2 text;
- fixed row/card geometry, viewport, no-scroll, DOM, screenshot-mask, keyboard, and screen-reader parity are required when the web layer exists.

The participant DOM uses neutral `article.evidence-card[aria-label="Evidence panel"]`
and opaque `div.evidence-row[data-row-id][data-position]` nodes. It must not expose
condition, stimulus, primitive-role, answer-key, or router semantics through ARIA,
hidden text, or data attributes. Evidence-body text has one source only: the
current item's `primitive_evidence`; visible labels and order are the only
condition-dependent fields.

CSS tokens are exact and shared by both conditions: desktop `1440×900` with minimum width `1280`; card max width `960px`, padding `24px`, row gap `12px`; row label/body widths `240/648px`, minimum height `72px`, block padding `12px`, column gap `24px`; label/body fonts `14/16px`, line-height `1.5`. At 100% zoom there is no internal card scroll or clipped/hidden content. At 200% zoom page scrolling is allowed, but clipping/hiding is not.

Parity audit uses headless Chrome and Edge on the current machine at fixed
`1440×900` and `1280×800` viewports, 100% and 200% zoom, and `1px` DOM-geometry
tolerance. It executes the full flow and captures nontrivial, dimension-checked
Contract and Flat PNG artifacts. CDP checks card/row bounds, exact shared widths
and fonts, overflow, clipping, focus order, accessible names, and forbidden hidden
semantic attributes. After declared order normalization, evidence text must be
byte-identical by evidence ID. Pixel equality is not an acceptance criterion:
labels and declared row order intentionally differ. Filler text, blank rows,
spacer glyphs, hidden text, and condition-specific padding remain forbidden.

## 5. Participant-facing materials

The exact participant strings are in `participant_materials` in `stimuli.json`; A/B conditions use the same strings.

The legend explains all inputs and the full routing priority in plain language without identifying trial answers. The tutorial explains the irreversible Q1→Q2 flow and conjunctive scoring. The single different practice record includes exact Q1/Q2 keys and feedback; formal trials do not.

The post-task manipulation diagnostic has one fixed four-option question/key, is descriptive only, and is never an exclusion criterion. The block-ease item uses exact options `SEQ1`–`SEQ7`, appears once after each five-trial block, permits null, and exports `block_1_ease`/`block_2_ease`. Neither task has free text.

There is no attention check or attention-check export field.

## 6. Sequence generation and allocation

`sequences.json` defines base order `[P1,P3,P2,P5,P4]`, block-1 rotation `r`, block-2 rotation `(r+2) mod 5`, letter mappings, and exact `A1..D5` sequences. The validator generates 200 trial rows and proves:

- each pattern-position cell occurs eight times overall;
- each condition×set×pattern×position cell occurs twice;
- each content ID appears ten times per condition;
- no pattern repeats its block-1 position in block 2;
- every sequence contains all ten content IDs exactly once.

Before outcomes, the owner prepares one blinded slot per sequence. Dropout or primary-ineligible completion reuses the slot. A ten-trial completion later mechanically excluded consumes it and remains in the specified sensitivity. Assignment never uses outcomes, RT, ease, practice, or diagnostic responses.

Each server start creates a signed random `run_id` and assigns a signed monotonic
`attempt_serial`; neither is an absolute time. Within one run, retain the complete
attempt with the lowest serial; if none completes, retain the most complete and
break ties by lowest serial. If a participant code appears across run IDs,
analysis hard-fails unless the owner supplies the explicit versioned
`--attempt-order-manifest` mapping every relevant `attempt_id` to a unique global
order. Input-file order is never authority. All raw exported attempts remain.

## 7. Missingness, export, and exclusions

The stdlib loopback server keeps attempts, sequence plans, phase, index, responses,
and relative monotonic timing only in volatile memory. Its strict endpoints are
start/practice/Q1/Q2/ease/diagnostic/complete/save-exit/export; the browser cannot skip a
phase or construct a completed export. All ten planned slots are exported only
as server-signed complete or partial products. During every formal-study stage,
`Save & Exit` atomically transitions the session to `export_ready` and freezes a
signed partial export (`complete=false`). Full completion uses the same
`export_ready` lifecycle. The server retains that immutable product until the
session TTL expires; JSON and CSV GETs are idempotent and retryable. The browser
shows persistent manual JSON/CSV download buttons, never auto-downloads, reports
download failure with `role=alert` while retaining both buttons, and may offer
`Finish` only to clear the client view without deleting the server export.
Required trial-state invariants are:

```text
complete == q1_submitted && q2_submitted
q2_submitted => q1_submitted => presented => planned
submitted == complete
```

The exact session/trial fields and exclusion enum are normative in `export_schema` in `stimuli.json`. Session fields include practice status, nullable post-task diagnostic status/response/correctness, nullable block-ease responses, and analysis-derived exclusion fields. They exclude attention checks and free text.

Primary eligibility requires complete Contract `>=4`, complete Flat `>=4`, and complete total `>=8`. The primary uses complete trials only. The required ten-slot sensitivity treats a missing component as incorrect.

Complete and partial JSON and CSV are canonical server products. JSON is HMAC-SHA256 signed
with an owner-held key generated at startup in an owner-selected file (default
gitignored runtime path). The key is never sent to the browser or written into an
export. Analysis requires the key and rejects unsigned, forged, tampered,
wrong-key, wrong-hash, unknown-field, and impossible-state exports.

Duplicate resolution precedes assignment/mechanical classification. Mechanical
reasons are limited to duplicate attempt, technical corruption, sequence mismatch,
materials-version mismatch, and impossible state transition. Performance, RT,
ease, practice, and diagnostic results never exclude. Assignment-mismatch attempts
are excluded from primary eligibility but retained in the ten-slot
missing-as-incorrect ITT sensitivity; only non-kept duplicates and
technical-corrupt attempts are omitted there.

Browser abandonment without a signed export is not observable by this memory-only
server and cannot enter study-export ITT. If recruitment is later authorized, the
recruitment platform completion log reports that separate count. The protocol
makes no promise to reconstruct silent/no-export dropouts.

No absolute timestamp, IP, UA, headers, demographics, free text, or fingerprint is collected.

## 8. Statistics

The primary estimand is the mean eligible-participant paired difference in Contract versus Flat CCA.

- participant bootstrap: `B=10000`, seed `20260810`, percentile `2.5/97.5`;
- primary test: exact one-sided sign flip;
- sensitivity: exact two-sided sign flip;
- zero differences are reported ties and removed before enumeration;
- enumerate all `2^N_eff`, include equality in tails, and use no `+1`.

Q1, Q2, RT, block ease, post-task diagnostic, pattern, block, sequence, and position are descriptive.

The sign-binomial MDE simulation is explicitly sensitivity-only. Primary paired
sign-flip MDE remains `UNVERIFIED_NOT_ESTIMATED` before protocol freeze.

## 9. Timing, accessibility, and privacy

The owner-run timing pilot is exactly three people and passes only if median completion is `<=10 min`, every participant is `<=12 min`, and forced timeouts equal zero. This DRAFT does not authorize that pilot.

Automated keyboard, focus, screen-reader, contrast, reduced-motion, 200% zoom, and
no-horizontal-scroll checks are separate. The implementation binds loopback only, checks the exact loopback Host/port,
rejects cross-origin and non-JSON POSTs, requires a same-origin bootstrap CSRF
token plus per-session capability, limits request size, caps sessions (default
100), expires them using monotonic TTL (default two hours), and serializes each
session under its own lock. Request nonces make duplicate endpoint calls
idempotent without duplicate transitions. It suppresses access logs, stores no
IP/UA/header/absolute timestamp or participant data on disk, and loses volatile
sessions at shutdown. Automated keyboard Tab/Space/Enter checks are required;
manual screen-reader semantic evaluation remains `UNVERIFIED PRE-RECRUITMENT`.
Every real-browser case starts its own loopback server on an ephemeral port,
waits for readiness, and owns its shutdown; cases never share a server lifecycle.
Chrome and Edge exercise A1/D5, complete/partial paths, failed-download button
retention, security probes, and a configurable repeated stress gate.

## 10. Acceptance criteria

1. JSON source/schema, router, Q2, parity, provenance, tutorial/practice, diagnostic/ease, export, and sequence validators pass.
2. Validator metrics exactly match Section 4.
3. P3-Y Q2 requests missing scope and Q1 remains withheld.
4. No attention-check field, free text, duplicate materials source, or hardcoded website key exists.
5. Registry and decision notes identify implementation pending hostile audit.
6. The website is loopback-only, memory-only, and consumes authoritative JSON.
7. No recruitment, pilot, human data, public deployment, paper edit, or claim
   upgrade occurs in this revision.
