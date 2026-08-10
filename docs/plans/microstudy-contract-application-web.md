# Implementation Plan: Local Contract-Application Micro-Study

- **Plan ID:** `microstudy-contract-application-web`
- **Status:** protocol revised; implementation pending fresh hostile audit
- **Scope:** future loopback implementation only; this commit implements no web application
- **Spec:** [`../specs/microstudy-contract-application.md`](../specs/microstudy-contract-application.md)
- **DRAFT prereg:** [`../research/2026-08-10-microstudy-contract-application-DRAFT.md`](../research/2026-08-10-microstudy-contract-application-DRAFT.md)

## 1. Boundaries

- No recruitment, ethics administration, pilot, data collection, public deployment, or paper edit.
- No live model, remote dependency, analytics, telemetry, browser persistence, or server response persistence.
- The DRAFT remains unfrozen and materials-only.

## 2. File plan

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

## 3. Slices

### Slice 1 — Materials and provenance

- Materialize all ten exact proposition arrays from the spec.
- Enforce provenance enum `real_inspired_non_pass|synthetic_rule_case`, nonempty `source_note`, P1/P3/P4 real-inspired, P2/P5 synthetic, and P5 hypothetical/no-current-pass fields.
- Reject forbidden direct state vocabulary and repeated role headings in evidence bodies.
- Store answer-key primitive dependencies and require at least two.
- Validate the combined checker at `10/10`.

### Slice 2 — Leakage resistance

- Freeze fixed-position, forbidden-keyword, second-row-only, and per-row bag-of-words blind baselines.
- Use leave-one-X/Y-pair-out evaluation.
- Block materials if any blind baseline exceeds empirical majority chance `0.40`.
- Keep these tests deterministic and versioned; do not tune them after viewing participant data.

### Slice 3 — Twenty exact sequences

- Generate A–D mapping and five left rotations into exactly `A1..D5`.
- Validate pattern/position/condition/set/block balance across all 20 codes.
- Validate 10 unique content IDs, five per condition, and no repeated rendering per participant.
- Do not expose any subset-designation or separate-generalization field.

### Slice 4 — Rendering parity

- Render both conditions from one proposition array.
- Use exactly five fixed-height rows and fixed label/body columns.
- Make legend, questions, options, typography, color, viewport, and no-scroll behavior identical.
- Enforce ≤5% total visible word-count difference and exact body word/line/row/card dimensions.
- Add DOM snapshots, CSS-token tests, and frozen-viewport pixel/screenshot comparison masking only label glyph regions.
- Test screen-reader evidence/options equality.

### Slice 5 — Flow, timing, and accessibility

- Landing, setup, compressed tutorial, one different practice example, two blocks, block ease, export.
- Accept owner code and `A1..D5`; no runtime randomization.
- No correctness feedback on formal trials and no automatic timeout/submission.
- Relative monotonic timing only; pause/subtract hidden time.
- Enforce row/body word caps.
- Keyboard-only, visible focus, fieldsets/legends, contrast, reduced motion, and 200% zoom checks.
- Keep owner pilot gate explicit: median ≤10 minutes, P90 ≤12; stop/revise if P90 exceeds 12 or accessibility fails.

### Slice 6 — Complete export and privacy

- Pre-generate ten response slots before presentation.
- Export every slot with `presented`, `submitted`, nullable Q1/Q2/correctness/RT, and condition/item/pattern/position/block/sequence.
- Eligibility is exactly ≥4 submitted per condition and ≥8/10 total.
- Primary is available-case only for eligible participants.
- Sensitivity marks missing components incorrect over all ten slots.
- Report missingness by condition/sequence; prohibit performance-based exclusion.
- Override server `log_message`; capture stdout/stderr/files in tests.
- Reject local/session storage, cookies, service worker, Cache/IndexedDB, analytics, external network, UA/IP, absolute timestamps, request logs, or server persistence.
- Enforce loopback binding and restrictive CSP.

### Slice 7 — Analysis and rebuild

- `analysis.py` reads export only and rebuilds eligibility, primary paired CCA, ten-slot sensitivity, missingness tables, participant bootstrap CI, and exact sign-flip test.
- Apply descriptive interpretation precedence from the prereg; never emit pass/fail.
- Keep Q1/Q2/RT/ease/pattern/sequence/position analyses descriptive.
- Implement MDE/resolution simulation with explicit N, baseline, correlation, trial count, missingness, alpha, direction, iterations, and seed.
- Recompute the provisional 20–25 pp range before protocol freeze; generated artifact is authoritative.
- Add end-to-end early-exit, partial, missing-component, full, round-trip, and rebuild tests.

## 4. Acceptance test matrix

| Area | Required proof |
|---|---|
| Materials | exact 10 IDs/keys; provenance closure; P5 notice; fabricated-value warning |
| Leakage | no forbidden terms/headings; ≥2 primitives/key; all blind heuristics ≤0.40; checker=1.00 |
| Sequences | exact `A1..D5`; machine-balanced pattern/position/condition/set/block; no repeated content |
| Parity | same strings/order; legend/options/keys; five rows; word/line/height; DOM and masked screenshot parity |
| Export | exactly ten planned slots; nullable incomplete fields; exact eligibility; missing sensitivity |
| Analysis | export-only deterministic rebuild; bootstrap CI; sole primary sign-flip; simulation assumptions |
| Privacy | no access log/storage/cookies/SW/network/analytics/IP/UA/absolute time/files |
| Accessibility | keyboard and focus; 200% zoom; contrast; reduced motion; no horizontal scroll |

## 5. Validation commands after implementation

```powershell
python -m pytest -q tests\test_microstudy_schema.py tests\test_microstudy_parity.py tests\test_microstudy_leakage.py tests\test_microstudy_routing.py tests\test_microstudy_sequences.py tests\test_microstudy_export.py tests\test_microstudy_analysis.py tests\test_microstudy_server.py tests\test_microstudy_end_to_end.py
python -m pytest -q
python -c "import json, pathlib; json.loads(pathlib.Path('src/cognitive_console/microstudy/data/stimuli.json').read_text(encoding='utf-8')); json.loads(pathlib.Path('src/cognitive_console/microstudy/data/sequences.json').read_text(encoding='utf-8'))"
python -c "import yaml, pathlib; yaml.safe_load(pathlib.Path('docs/ledgers/experiment-registry.yaml').read_text(encoding='utf-8'))"
git diff --check
```

## 6. Definition of done

- Every spec acceptance criterion is automated where feasible.
- Synthetic preview is loopback-only, parity-constrained, accessible, and privacy-clean.
- Export/analysis reconstruct all planned slots and missingness without hidden state.
- Registry remains `not_started_materials_only`.
- Owner pilot gate remains unexecuted and required.
- Fresh independent hostile audit reports no BLOCKER before merge or implementation.
