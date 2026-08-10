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

The JSON contains the exact ten records, proposition strings, Flat permutations, Q1 text/options, Q2 templates and assignments, structured router inputs, provenance, tutorial/legend, practice and feedback, post-task diagnostic, block-ease item, debrief, export fields, tokenization, heuristic definitions, and generated sequences. Documentation summarizes those records and must not become a second answer-key or stimulus source. A future website must consume these files and must not hardcode another materials copy.

Run:

```powershell
python scripts\validate_microstudy_materials.py
python -m pytest -q tests\test_microstudy_materials.py
```

The validator, not Markdown parsing, generates and validates answer keys and all reported material metrics.

## 2. Construct, treatment, and flow

The study measures **structured rule application**: whether technical GenAI users combine five displayed contract inputs to select an interface state, then answer a separate evidence/scope/comparator judgment. It does not measure deep integration, transfer, calibrated reliance, benefit, trust, safety, productivity, deployment, or latent control.

The treatment is a semantic-organization package:

- **Contract:** semantic headings, grouping, and fixed role order.
- **Flat:** neutral labels and item-specific deterministic row shuffles.
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
4. missing comparison resolution or CI crossing zero → unresolved;
5. resolved non-superiority, or positive resolved estimate below margin → withheld;
6. positive result meeting margin plus coherence fail/unavailable → withheld;
7. positive result meeting margin plus coherence pass → supported at the exact tier.

A tier change invalidates inherited inputs. Item IDs and pattern IDs are never state authority.

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

Duplicate decisions use anonymous `participant_code` and freeze before outcomes: retain the first complete attempt; if none completes, retain the most complete and break ties by owner-log order. All raw attempts remain.

## 7. Missingness, export, and exclusions

All ten planned slots are exported. Required trial-state invariants are:

```text
complete == q1_submitted && q2_submitted
q2_submitted => q1_submitted => presented => planned
submitted == complete
```

The exact session/trial fields and exclusion enum are normative in `export_schema` in `stimuli.json`. Session fields include practice status, nullable post-task diagnostic status/response/correctness, nullable block-ease responses, and analysis-derived exclusion fields. They exclude attention checks and free text.

Primary eligibility requires complete Contract `>=4`, complete Flat `>=4`, and complete total `>=8`. The primary uses complete trials only. The required ten-slot sensitivity treats a missing component as incorrect.

Mechanical reasons are limited to duplicate attempt, technical corruption, sequence mismatch, materials-version mismatch, and impossible state transition. Performance, RT, ease, practice, and diagnostic results never exclude. Analysis re-derives exclusions from raw export plus the frozen owner assignment list.

No absolute timestamp, IP, UA, headers, demographics, free text, or fingerprint is collected.

## 8. Statistics

The primary estimand is the mean eligible-participant paired difference in Contract versus Flat CCA.

- participant bootstrap: `B=10000`, seed `20260810`, percentile `2.5/97.5`;
- primary test: exact one-sided sign flip;
- sensitivity: exact two-sided sign flip;
- zero differences are reported ties and removed before enumeration;
- enumerate all `2^N_eff`, include equality in tails, and use no `+1`.

Q1, Q2, RT, block ease, post-task diagnostic, pattern, block, sequence, and position are descriptive.

Numerical MDE status remains `pending reproducible simulation before protocol freeze`.

## 9. Timing, accessibility, and privacy

The owner-run timing pilot is exactly three people and passes only if median completion is `<=10 min`, every participant is `<=12 min`, and forced timeouts equal zero. This DRAFT does not authorize that pilot.

Automated keyboard, focus, screen-reader, contrast, reduced-motion, 200% zoom, and no-horizontal-scroll checks are separate. A future implementation must bind loopback only, suppress access logs, use no persistence or remote network, and export only the frozen anonymous schema.

## 10. Acceptance criteria

1. JSON source/schema, router, Q2, parity, provenance, tutorial/practice, diagnostic/ease, export, and sequence validators pass.
2. Validator metrics exactly match Section 4.
3. P3-Y Q2 requests missing scope and Q1 remains withheld.
4. No attention-check field, free text, duplicate materials source, or hardcoded website key exists.
5. Registry and decision notes remain materials-only.
6. No web implementation, recruitment, pilot, human data, paper edit, or claim upgrade occurs in this revision.
