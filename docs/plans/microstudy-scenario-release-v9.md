# Implementation Plan: V9 Scenario Knob-Release Micro-Study

- **Status:** DRAFT implementation authorized; no human data
- **Branch:** `feature/microstudy-v9-scenario`
- **Scope:** owner-local loopback materials, generator, analysis, browser flow, tests, and governance only
- **Non-goals:** recruitment, timing, ethics administration, public deployment, protocol freeze, paper edits, or evidence upgrades

## Dependency order

1. Pin immutable Git-blob source registry and implement fail-closed evidence extraction.
2. Generate six scenario tickets, private answer derivation, bilingual public materials, and twelve exact-cover sequences.
3. Replace the active local preview with the V9 six-slot staged flow while retaining V8 data as historical material.
4. Introduce signed V5 complete/partial exports and V9-only analysis/duplicate/allocation rules.
5. Add material, leakage, security, browser, export, and analysis regression tests.
6. Run validator, Node checks, targeted tests, full pytest, isolated HTTP/browser smoke, and diff hygiene.
7. Commit implementation, then persist its exact commit in D-0114 and the experiment registry.

## Implementation constraints

- Public materials, browser state, endpoint projections, DOM/ARIA, and exports contain no expected answer keys.
- Contract and Flat use the same six localized fact bodies, product context, source badge, illustrative outputs, Q1, and Q2.
- Only headings/order/neutral labels differ. No condition, group, or semantic role identifiers enter participant projections.
- Real numbers are formatted only from verified canonical Git blob bytes.
- E-0014/E-0015 cannot generate a positive latent pass.
- Source/product/output display fields are excluded from answer derivation.
- The server remains loopback-only, volatile, no-log, origin/CSRF/capability protected, size/capacity/TTL bounded, per-session locked, and request-id idempotent.
- V4/V5 and V8/V9 mixtures hard-fail.

## Validation

```powershell
python scripts\generate_microstudy_v9.py --check
python scripts\validate_microstudy_materials.py
node tests\microstudy_js_test.mjs
python -m pytest -q tests\test_microstudy_materials.py tests\test_microstudy_web.py
python -m pytest -q
git diff --check
```

The maximum deliverable state is `ready_for_owner_local_preview_no_human_data`;
`valid_for_paper=false`. Human bilingual semantic review, responsive/mobile
design, manual screen-reader review, ethics/recruitment authorization, timing,
sample-size/MDE justification, and Protocol Freeze remain open.
