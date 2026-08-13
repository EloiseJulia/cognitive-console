# Plan — V3 stepwise study public deployment + consent gate

- **Decision**: D-0121 (owner-authorized public data collection).
- **Branch**: `feature/stepwise-public-deploy`.
- **Implementation commit**: `80f202e`.
- **Scope**: deployment infrastructure + a UI-only consent gate. **No study
  logic, expected answers, keys, routing, sequences, A/B design, or GAA/Strict
  scoring changes.** Logic fingerprint `cb91ebcf…b0bd` preserved; materials
  stay `v11.3`, export schema stays V8.

## Goal

Let the owner deploy **only** the `button_board_stepwise` study to a free
Render web service (free Postgres) to collect real volunteer data for a small
course user study, without changing what the study measures or how it is
scored.

## What was built

1. **`storage.py`** — idempotent, attempt-keyed store of signed exports.
   `InMemoryExportStore` (tests) and `PostgresExportStore` (deployment; lazy
   `psycopg`). `create_store(DATABASE_URL)` returns `None` when unset (volatile).
2. **`server.py`** — opt-in public mode via `STEPWISE_PUBLIC_ORIGIN`:
   - binds a public address (`0.0.0.0:$PORT`); loopback preview unchanged;
   - reads verification key + admin token from the environment (never a file);
   - validates CSRF/Host/Origin against the external public origin;
   - persists each signed export on `complete`/`save-exit` (fail-closed: does
     not advance phase if the store write fails, so the participant can retry);
   - owner-only `GET /admin/export?format=json|csv` guarded by
     `X-Admin-Token`; `GET /healthz` open for Render health checks.
3. **`static/study.js` + `study.css`** — placeholder bilingual informed-consent
   gate on the welcome screen. Begin is disabled until "I agree"; a decline
   button exits. UI-only. **Replace the placeholder `CONSENT_COPY` with the
   advisor's approved wording before recruiting.**
4. **`deploy/stepwise/`** — Render blueprint (`render.yaml`) + README.
   `pyproject` gains a `deploy` extra (`psycopg[binary]`).
5. **Tests** — `tests/test_button_board_stepwise_deploy.py` (12): storage
   idempotency/copy-safety, public-mode validation, persistence + admin
   download, admin-token rejection, healthz, 409 when persistence disabled.
   Existing browser CDP flows updated to tick consent (and assert the Begin
   button is disabled until consent).

## Invariants verified

- generator `--check` current; logic fingerprint reprinted equal to
  `cb91ebcf364bf07bea40cf541872de7efe07d548d75b2a265dc9be59a6a2b0bd`.
- Participant JSON/CSV/DOM/ARIA contain no expected/scoring fields (asserted in
  new tests and existing web tests).
- Loopback owner-preview mode unchanged; V1/V2 coexistence tests unaffected.

## Explicitly NOT done / out of scope

- No push, deploy, recruitment, or participant contact by the agent.
- No change to expected answers, materials logic, or scoring.
- Consent is **not** recorded into the export (would bump export schema);
  deferred as an owner decision.

## Open human gates (must close before data is confirmatory)

Protocol + preregistration freeze (answer key, primary metric GAA, exclusion
rules), sample-size/MDE, privacy/data-retention, bilingual/accessibility human
review. Ethics/informed-consent owner-asserted present. Until the freeze
closes, collected data is exploratory pilot only (`valid_for_paper=false`).
