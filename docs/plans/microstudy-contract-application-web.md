# Implementation Plan: Local Contract-Application Micro-Study

- **Plan ID:** `microstudy-contract-application-web`
- **Status:** `ready_for_owner_local_preview_no_human_data`
- **Current scope:** loopback website, deterministic export, analysis, MDE sensitivity, tests, and docs
- **Spec:** [`../specs/microstudy-contract-application.md`](../specs/microstudy-contract-application.md)

## 1. Current revision

The bilingual revision keeps the only authoritative inputs:

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

`stimuli.json` is now an explicit nonlocalized + `en` / `zh-Hans` stable-ID
tree with no fallback or auto-detection. It is the only participant-copy source;
JavaScript has no second locale bundle. The validator owns canonical UTF-8
locale versions/hashes, stable-ID completeness, numeric/polarity/modality/scope
parity, independent locale leakage heuristics, Contract-token forbidden scans,
same-locale body parity, router derivation, sequence checks, and the existing
CCA/leakage gates.

The local web app is implemented without recruitment, pilot, public deployment,
paper changes, or participant data.

The final audited implementation identity is
`1702d7a4ae5132b09fd29d216502504c7afb493c`. Any subsequent docs-only commit
that persists audit or governance records is not the implementation code
commit.

## 2. Implemented rule

The loopback server consumes the two JSON files directly. Bootstrap exposes
only CSRF plus the bilingual gate labels. `/api/welcome` exposes only the chosen
locale's common projection. `/api/start` requires and immutably locks exact
`ui_language`; formal endpoints send only already-rendered visible rows and the
selected question/options. Formal answer keys, routing inputs, primitive-role
IDs, condition metadata, validation metadata, the other locale's formal bundle,
and scoring never enter browser state/network/DOM/ARIA. The server owns the
strict practice→Q1→Q2→ease→diagnostic→debrief state machine.

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

- Initial bilingual language gate; no default, browser/URL/storage detection, or
  recovery token. Welcome may switch; start may not.
- Neutral common onboarding explains four states and five information types
  without Contract labels, a complete router, threshold priority, or lookup.
- One community activity-room practice, Q1 withheld and Q2 lock answer D, with
  example-only feedback.
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
- Generate complete and Save-&-Exit partial V4 bilingual exports canonically on
  the server and HMAC-SHA256 sign them; both retain all ten slots and add
  `ui_language`, locale bundle version, and locale bundle hash.
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
- Reject V3/V4 mixing. Locale contributes only descriptive counts and duplicate
  conflict metadata; it never enters outcome or inferential paths.

### Privacy

- Loopback only, no access logging, persistence, remote requests, timestamps, IP, UA, headers, demographics, or fingerprints.
- Exact Host/origin, JSON-only POST, bootstrap CSRF and session capability checks;
  16 KiB request limit, configurable session cap/monotonic TTL, per-session locks,
  and request-id idempotency.
- Real Chrome/Edge full-flow CDP gates cover both viewports and zooms, keyboard
  operation, dynamic `lang`, h1 focus, selected-only DOM/network/ARIA,
  geometry/overflow, complete/partial/retry, refresh-to-gate, and PNG artifacts.
  Manual bilingual semantic and screen-reader review remain `UNVERIFIED
  PRE-RECRUITMENT`.

## 4. Current acceptance

```powershell
python scripts\validate_microstudy_materials.py
python -m pytest -q tests\test_microstudy_materials.py
python -m pytest -q
python -c "import yaml, pathlib; yaml.safe_load(pathlib.Path('docs/ledgers/experiment-registry.yaml').read_text(encoding='utf-8'))"
git diff --check
```

Required validator results are documented in the spec/prereg and enforced from
JSON. The final independent hostile audit closed the TTL-renewal MAJOR and
verified the validator, Node checks, HTTP TTL/idempotency/export behavior,
Chrome/Edge bilingual flows, and the full pytest suite without residue.
Registry status is `ready_for_owner_local_preview_no_human_data`; there is no
human run, public deployment, paper evidence, or confirmatory MDE result.
