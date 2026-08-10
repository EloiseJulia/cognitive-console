# Implementation Plan: Local Contract-Application Micro-Study

- **Plan ID:** `microstudy-contract-application-web`
- **Status:** `implemented_pending_reaudit_nohuman`
- **Current scope:** loopback website, deterministic export, analysis, MDE sensitivity, tests, and docs
- **Spec:** [`../specs/microstudy-contract-application.md`](../specs/microstudy-contract-application.md)

## 1. Current revision

This revision creates the only authoritative future-web inputs:

```text
data/microstudy_contract_application/stimuli.json
data/microstudy_contract_application/sequences.json
```

It also adds:

```text
src/cognitive_console/microstudy_materials.py
scripts/validate_microstudy_materials.py
tests/test_microstudy_materials.py
```

The validator owns router derivation, render-contract schema/tokens, sequence generation checks, parity, template reuse, key variation, lexical/token heuristics, oracle/LOO/global baselines, single-row Q1, and combined CCA. Markdown is not parsed and is not a second materials source.

The local web app is implemented without recruitment, pilot, public deployment,
paper changes, or participant data.

## 2. Implemented rule

The loopback server consumes the two JSON files directly and exposes only a
participant-facing projection. Formal answer keys, routing inputs, validation
metadata, and scoring never enter the browser. The server owns the strict
practice→Q1→Q2→ease→diagnostic→debrief state machine and scores from private
authoritative materials.

Implemented package:

```text
src/cognitive_console/microstudy/
  server.py
  materials.py
  analysis.py
  __main__.py
  static/
```

## 3. Implemented slices

### Rendering and flow

- Render Contract/Flat from one proposition map.
- Use exact Contract labels `READ`/`TRANSFER`/`BOUNDED PROMPT COMPARATOR`/`CALIBRATION WARNING`/`EVIDENCE TIER`; use Flat `Evidence A`–`Evidence E`.
- Use Contract's fixed JSON role order and each Flat item's JSON `flat_order`.
- Implement the exact JSON DOM tags/classes/data attributes and bind all evidence-body text only to `primitive_evidence`.
- Lock Q1 before Q2 and prohibit navigation back.
- Apply the same exact geometry tokens to both conditions: `1440×900` desktop (`1280px` minimum), `960px` card, `240/648px` label/body, `72px` row minimum, and declared padding/gap/type tokens.
- At 100% zoom prohibit internal card scroll and clipping; at 200% allow page scrolling but prohibit hidden/clipped content.
- Add fixed-viewport DOM and screenshot parity at `1px` tolerance, evidence-text identity after label/order removal, forbidden answer/state/verdict/action row checks, and label-only pixel masking plus declared-permutation structural comparison.
- Preserve the acknowledged label word-count/visual treatment difference; never add filler padding, words, hidden text, or blank rows.

### Allocation and export

- Use exact validated `A1..D5` rows.
- Generate a server-side random UUID attempt ID.
- Preserve ten planned slots and all truth-table states in volatile server memory.
- Generate complete and Save-&-Exit partial exports canonically on the server and
  HMAC-SHA256 sign them; partials retain all ten slots and nullable fields.
- Sign random per-run `run_id` and monotonic per-start `attempt_serial`; require an
  explicit global-order manifest for duplicate participant codes across runs.
- Keep the verification key in an owner-selected file (default gitignored
  `.runtime/microstudy-verification.key`); never send it to the browser or export.
- Keep post-task diagnostic and block ease nullable/descriptive.
- Implement no attention check and no free-text controls.

### Analysis

- Verify signature/hash/schema before analysis; reject forged/tampered exports.
- Resolve duplicate attempts by first-complete rule before assignment/mechanical
  classification without using input-file order. Keep assignment-mismatch attempts in missing-as-incorrect ITT
  sensitivity while excluding them from primary eligibility.
- Provide only a DRAFT sign-binomial MDE sensitivity; primary-test MDE remains
  `UNVERIFIED_NOT_ESTIMATED`.

### Privacy

- Loopback only, no access logging, persistence, remote requests, timestamps, IP, UA, headers, demographics, or fingerprints.
- Exact Host/origin, JSON-only POST, bootstrap CSRF and session capability checks;
  16 KiB request limit, configurable session cap/monotonic TTL, per-session locks,
  and request-id idempotency.
- Real Chrome/Edge full-flow CDP gates cover both viewports and zooms, keyboard
  operation, geometry/overflow/focus/ARIA/hidden attributes, and PNG artifacts.
  Manual screen-reader testing remains `UNVERIFIED PRE-RECRUITMENT`.

## 4. Current acceptance

```powershell
python scripts\validate_microstudy_materials.py
python -m pytest -q tests\test_microstudy_materials.py
python -m pytest -q
python -c "import yaml, pathlib; yaml.safe_load(pathlib.Path('docs/ledgers/experiment-registry.yaml').read_text(encoding='utf-8'))"
git diff --check
```

Required validator results are documented in the spec/prereg and enforced from
JSON. Registry status is
`implemented_pending_reaudit_nohuman`; there is no human run,
public deployment, paper evidence, or confirmatory MDE result.
