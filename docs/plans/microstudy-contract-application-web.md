# Implementation Plan: Local Contract-Application Micro-Study Web App

- **Plan ID:** `microstudy-contract-application-web`
- **Authorization:** Manager-authorized protocol/material/local-web engineering only
- **Status:** ready for implementation after independent protocol audit
- **Branch target:** a new implementation branch/worktree; this plan branch contains no web implementation
- **Spec:** [`../specs/microstudy-contract-application.md`](../specs/microstudy-contract-application.md)
- **DRAFT prereg:** [`../research/2026-08-10-microstudy-contract-application-DRAFT.md`](../research/2026-08-10-microstudy-contract-application-DRAFT.md)

## 1. Hard boundaries

- Do not recruit, contact, compensate, or collect data from participants.
- Do not deploy publicly or bind a server beyond `127.0.0.1`.
- Do not add analytics, telemetry, remote assets, live models, or network dependencies.
- Do not edit paper claims, paper prose, frozen results, current routing rules, or existing evidence verdicts.
- Do not freeze the DRAFT preregistration.
- Do not claim a study was run.

## 2. Proposed architecture

Use the repository's existing standard-library local-server approach with a separate `cognitive_console.microstudy` package. Keep study assets isolated from the existing demonstration console.

```text
src/cognitive_console/microstudy/
  __init__.py              package marker/version
  __main__.py              CLI entry
  server.py                loopback-only static server; no persistence
  schema.py                stimulus/sequence/export validation
  sequencing.py            exact A–D assignment lookup
  scoring.py               Q1/Q2/CCA and completion rules
  export.py                deterministic JSON/CSV serialization
  static/
    index.html             accessible shell
    app.js                 local state machine and relative timing
    styles.css             parity-constrained desktop presentation
  data/
    stimuli.json           generated from reviewed spec appendix
    sequences.json         exact A–D table
tests/
  test_microstudy_schema.py
  test_microstudy_parity.py
  test_microstudy_routing.py
  test_microstudy_sequences.py
  test_microstudy_export.py
  test_microstudy_server.py
```

No database is required. No response is posted to the server.

## 3. Executable checklist

### Slice 1 — Materialize and validate data

- [ ] Create `stimuli.json` with schema version, 10 stimuli, two render descriptors per stimulus, exact options, correct keys, source labels, and held-out flags.
- [ ] Create `sequences.json` implementing A–D exactly.
- [ ] Add `schema.py` dataclasses/validators.
- [ ] Fail closed on unknown fields, duplicate IDs, invalid keys, missing simulated-record notice, or unsupported source status.
- [ ] Validate every answer key through a small pure routing function that mirrors, but does not modify, the current checker.
- [ ] Add a generated material hash/version displayed in preview and export.

**Commit point 1:** material schema + sequence + routing tests.

### Slice 2 — Enforce parity

- [ ] Represent primitive evidence once per stimulus; render both conditions from the same evidence array.
- [ ] Store condition-specific headings separately from evidence text.
- [ ] Implement normalization: NFKC, trim, whitespace collapse, CRLF→LF.
- [ ] Add evidence equality tests across renderers.
- [ ] Add answer-option/key equality tests.
- [ ] Add DOM snapshot/structural allowlist test: only heading text, grouping wrappers, `aria-labelledby`, and class names may differ.
- [ ] Add CSS token equality test for font/color/spacing/viewport/scroll.
- [ ] Add forbidden-leak scanner for state answers, `TRANSFER`, aggregate verdicts, recommendations, pass/fail badges, green/deploy/check icons.

**Commit point 2:** parity engine and tests.

### Slice 3 — Implement local flow

- [ ] Add landing, setup, tutorial, practice, block 1, ease, transition, block 2, ease, export pages.
- [ ] Require valid anonymous code and sequence A–D.
- [ ] Default to preview mode.
- [ ] Keep scored session state only in browser memory.
- [ ] Disable scored back navigation and correctness feedback.
- [ ] Ensure exactly 5 trials per condition and 10 unique IDs.
- [ ] Implement fixed sequence order without runtime randomization.
- [ ] Mark exactly one designated held-out item per condition according to sequence.
- [ ] Support owner-operated practice/preview without creating a completed export.

**Commit point 3:** state machine and flow tests.

### Slice 4 — Timing, scoring, and export

- [ ] Use monotonic `performance.now()` deltas only.
- [ ] Pause/subtract timing while hidden and record relative `hidden_ms`.
- [ ] Implement Q1, Q2, CCA scoring.
- [ ] Implement `<8/10` primary exclusion metadata.
- [ ] Implement missing-as-incorrect sensitivity fields without performance exclusion.
- [ ] Add 1–5 block ease.
- [ ] Implement deterministic `microstudy-export-v1` JSON.
- [ ] Implement one-row-per-trial RFC 4180 CSV with spreadsheet-formula escaping.
- [ ] Prohibit absolute timestamp, UA, IP, referrer, demographics, free text, and fingerprint fields in schema and tests.
- [ ] Add local download and reset actions.

**Commit point 4:** scoring/export and privacy tests.

### Slice 5 — Accessibility and loopback hardening

- [ ] Fieldsets/legends, landmarks, correct headings, explicit labels, and live error summary.
- [ ] Keyboard-only flow and visible focus.
- [ ] Contrast checks; no color-only meaning and no green/deploy semantics.
- [ ] Reduced-motion support and 200% zoom check.
- [ ] Screen-reader parity check for evidence/options.
- [ ] Server rejects `0.0.0.0`, non-loopback IPv4, and non-loopback IPv6.
- [ ] Add Content-Security-Policy allowing only local static assets; no remote origins.
- [ ] Test that application code contains no analytics/network endpoints.

**Commit point 5:** accessibility and security hardening.

### Slice 6 — Documentation and verification

- [ ] Add CLI help and local preview instructions to the spec or existing README only where directly relevant.
- [ ] Run targeted micro-study tests.
- [ ] Run full test suite.
- [ ] Run Markdown link check.
- [ ] Parse YAML registry and JSON materials.
- [ ] Inspect `git diff --check`.
- [ ] Produce screenshots only as local audit artifacts if requested; do not collect interaction data.
- [ ] Request a fresh independent hostile protocol/material/web audit before merge.

**Commit point 6:** verified implementation candidate.

## 4. Required tests

### Schema/material tests

- exactly 10 scored IDs and 5 patterns × 2 content instances;
- all source labels allowed and notices present;
- P5 records marked hypothetical and current-paper-no-pass;
- correct Q1/Q2 keys and rule derivation;
- no current paper numbers or raw harmful content.

### Sequence tests

- A–D table exact;
- 5 Contract + 5 Flat per sequence;
- 10 unique stimulus IDs per participant;
- each stimulus Contract in two sequences and Flat in two;
- block order and item-set mapping crossed;
- exactly one designated held-out item per condition.

### Parity tests

- normalized primitive evidence equality;
- value, legend, order, question, option, and key equality;
- equal style tokens and viewport/scroll contract;
- only allowlisted semantic heading/DOM differences;
- leak scanner rejects final states, direct `TRANSFER`, recommendations, and green/deploy icons.

### Scoring/export tests

- CCA requires both answers correct;
- incomplete response behavior;
- `<8/10` exclusion;
- missing-as-incorrect sensitivity;
- only relative RT;
- exact JSON keys and CSV header/order;
- formula injection escaping;
- no forbidden privacy fields.

### Server/security tests

- loopback works;
- non-loopback bind rejected;
- no external resource URL;
- CSP present;
- preview produces no completed export automatically;
- no server-side response storage.

## 5. Validation commands

```powershell
python -m pytest -q tests\test_microstudy_schema.py tests\test_microstudy_parity.py tests\test_microstudy_routing.py tests\test_microstudy_sequences.py tests\test_microstudy_export.py tests\test_microstudy_server.py
python -m pytest -q
python -c "import json, pathlib; json.loads(pathlib.Path('src/cognitive_console/microstudy/data/stimuli.json').read_text(encoding='utf-8')); json.loads(pathlib.Path('src/cognitive_console/microstudy/data/sequences.json').read_text(encoding='utf-8'))"
python -c "import yaml, pathlib; yaml.safe_load(pathlib.Path('docs/ledgers/experiment-registry.yaml').read_text(encoding='utf-8'))"
git diff --check
```

## 6. Definition of done

- All acceptance criteria in the spec are automated where feasible.
- Local preview is usable on desktop, accessible, offline, loopback-only, and exports the exact schema.
- No human data was collected and no study-result artifact exists.
- Registry remains `not_started_materials_only`.
- Independent protocol/material/web audit reports no BLOCKER before merge.

