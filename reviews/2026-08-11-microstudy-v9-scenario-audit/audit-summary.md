# V9 Scenario Micro-Study Hostile Audit Closure

- **Audited implementation:** `3b8d429be058b38512604d287530b83068e79029`
- **Scope:** synthetic V9 design and owner-local loopback preview only
- **Protocol state:** `DRAFT / NOT FROZEN`
- **Human data:** none; recruitment and participant contact remain unauthorized

## Ranked findings and closure

### BLOCKER — verification-key permissions were not fail-closed

`src/cognitive_console/microstudy/server.py` previously ignored `chmod`
failures, leaving the HMAC verification key potentially broad on Windows.
Windows startup now uses `icacls` to reset the file ACL, set the current SID as
owner, remove inheritance, and grant only that SID full control. A separate
.NET ACL read verifies one non-inherited allow rule, the current owner SID, and
full control. Any setup or verification failure raises before server startup
and removes the key; cleanup failure also raises. POSIX startup applies and
verifies mode `0600`. Existing and newly created keys follow the same
fail-closed path. The key remains absent from browser projections, exports, and
logs.

Tests cover Windows ACL failure cleanup, existing-key cleanup, POSIX chmod
failure cleanup, POSIX `0600` dispatch, and a real Windows owner-only ACL.
Isolated HTTP smoke shut down its server and removed its runtime key. No V9 PID,
browser profile, test runtime, or verification-key residue remained.

### MAJOR — practice revealed the formal route

`src/cognitive_console/microstudy_materials.py` and generated
`data/microstudy_scenario_v9/materials.json` no longer say `use W` or state the
formal policy route. The sixth neutral audio fact now rehearses only the
irreversible Q1 lock. Feedback teaches only that a changed preview does not
show superiority over the existing preset and that the speech-quality check
failed. It names no formal state and gives no state-to-policy mapping. Q1 still
locks before Q2.

### MAJOR — V9 governance lineage was missing

D-0114 records the owner-approved V9 version break, synthetic/no-human scope,
owner-local-only ceiling, `valid_for_paper=false`, V8 historical separation,
and open human gates. The experiment registry now pins the implementation
commit, V9 material/sequence/export schemas, artifact hashes, and canonical
E-series source lineage. The V9 plan is explicitly `DRAFT / NOT FROZEN`.
Historical V8 spec/preregistration remain DRAFT and are not relabeled or mixed
with V9.

## Validation

- `python scripts\generate_microstudy_v9.py --check` — PASS
- `python scripts\validate_microstudy_materials.py` — PASS
- `node tests\microstudy_js_test.mjs` — PASS
- targeted materials/web suite — 30 passed
- full `python -m pytest -q` — 838 collected; 832 passed, 6 skipped
- isolated loopback HTTP smoke — PASS; runtime key removed
- `git diff --check` — PASS

The hostile-audit baseline had also encountered a `test_lineage.py`
`PermissionError` on clean `main`, establishing that occurrence as pre-existing
and unrelated to V9. This closure did not modify that unrelated test. The
current full-suite rerun completed without that environmental error.

## Verdict

**READY FOR OWNER LOCAL PREVIEW; NO HUMAN DATA.**

This verdict authorizes no recruitment, participant contact, ethics activity,
timing pilot, public deployment, paper evidence, Claim/result upgrade, or
Protocol Freeze. Human bilingual semantic review, responsive/mobile review,
manual screen-reader evaluation, ethics/recruitment authorization, owner
timing, and defensible sample-size/MDE justification remain open.
