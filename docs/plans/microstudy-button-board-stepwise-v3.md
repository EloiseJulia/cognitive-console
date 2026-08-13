# Implementation Plan: V3 Stepwise Open-Book Button Board

- **Status:** `DRAFT / NOT FROZEN / implementation for owner-local preview`
- **Branch:** `feature/microstudy-v3-guided-demo`
- **Governance:** D-0117, D-0118, D-0119, D-0120
- **Non-goals:** human data, recruitment, timing, ethics administration,
  Protocol Freeze, public deployment, paper/claim/result edits, Contract/Flat,
  or V1/V2 replacement

## Dependency order

1. Define the V11 typed fact registry and unified per-method comparison schema.
2. Render participant cards and scope options from that registry.
3. Derive every expected step, exit, decisive step, and state without hand keys.
4. Generate independent public materials, private keys, and balanced sequences.
5. Implement the independent stepwise server, UI, raw signed export, and
   offline analysis by reusing only the audited V2 security skeleton.
6. Add material, routing, scoring, leakage, sequence, security, browser,
   accessibility, coexistence, and cross-version tests.
7. Run generated-artifact checks, Node, targeted/full pytest, isolated HTTP
   smoke, V9/V2 regression smoke, and diff hygiene.
8. Commit without push; record the implementation hash in D-0117 and the
   experiment registry through a docs-only lineage commit.

## V11.1 polish dependency order

1. Capture a content-independent logic fingerprint over nature, comparison
   structure/counts, scope value IDs, expected path, decisive exit, and state.
2. Apply the owner-approved everyday bilingual object names and operational
   target definitions in the typed source; regenerate public/private artifacts.
3. Make F4's 0 original-method rounds, 10 new-button rounds, and absence of any
   original-method round explicit without changing its derived route.
4. Add a revise-step transition that truncates the selected step and every
   later answer, clears the former exit, and recomputes from the replacement.
5. Render Previous step and every answered-step summary as native buttons with
   localized ARIA labels and heading focus after revision.
6. Keep signed exports and GAA/Strict on the final surviving path only; add no
   revision-history or scoring field and retain the V7 export schema.
7. Validate generator/materials, Node, unit/API/security, Chrome/Edge en/zh at
   100%/200%, full pytest, isolated HTTP flows, coexistence, and diff hygiene.

## Acceptance checklist

- [x] One always-visible card, one current question, and one sticky reference.
- [x] Frozen early-exit route and no formal correctness feedback.
- [x] Six formal scenes, one AB variant per attempt, practice, and AC1.
- [x] Four states represented for either AB allocation.
- [x] F4 uses the same per-method schema as paired scenes.
- [x] Card text and structural fields share one typed fact source.
- [x] Step 6 options have bilingual stable-ID parity, equal dimensions,
      balanced lengths, and one-dimension distractors.
- [x] All expected fields are machine-derived and public projections omit them.
- [x] GAA/Strict are recomputed offline; wrong S scope keeps GAA and loses Strict.
- [x] V11 raw signatures and V5/V6/V7/V9/V10/V11 fail-closed isolation.
- [x] Loopback, Host/origin, CSRF, capability, idempotency, success-only TTL,
      capacity, no logs/storage/PII, and key isolation.
- [x] V9 and V2 entry points, materials, and tests remain unchanged.
- [x] Everyday bilingual names and one-sentence target definitions replace the
      coined names without changing the logic fingerprint.
- [x] F4 visibly states that no round used the original method.
- [x] Previous step and any answered-step summary can reopen a step.
- [x] Reopening clears every later step and recomputes early exit.
- [x] Final export/scoring contains only the surviving final path and no private
      derivation material.

## V11.2 declutter dependency order

1. Preserve the content-independent
   `cb91ebcf364bf07bea40cf541872de7efe07d548d75b2a265dc9be59a6a2b0bd`
   logic fingerprint and all generated expected fields.
2. Remove welcome/tutorial flow preamble and the participant-code input. Make
   start locale-only and use a random server UUID as the option-order,
   attempt, export, and deduplication identity.
3. Remove only the separate four-destination explanation cards from the sticky
   reference panel; retain the “How to think” checklist and every formal
   question option.
4. Project P1 as a read-only worked example with card-cited reasoning and one
   direct “Begin formal scenarios” action. Delete practice response transitions
   and export no practice answer/path/timing/score.
5. Replace `practice_status` with the minimal
   `demonstration_status: acknowledged`, remove `participant_code`, and bump
   materials/export/analysis identities to V11.2/V8/V2 with exact
   cross-version failure.
6. Re-run generator/materials, Node, targeted/full pytest, Chrome/Edge en/zh at
   100%/200%, security, isolated V3/V2/V9 smokes, cleanup, and diff hygiene.

V11.2 acceptance:

- [x] Locale selection is the only participant-provided start value.
- [x] No anonymous-code control or client/server validation remains.
- [x] The sticky panel contains the checklist but no four-destination explainer.
- [x] P1 is read-only, card-cited, separate from formal scenes, and unscored.
- [x] Formal router, options, sequence/allocation, A/B isolation, backtracking,
      GAA/Strict, expected derivation, and logic fingerprint are unchanged.
- [x] Signed export contains a generated attempt identity and minimal
      demonstration acknowledgement, with no practice answer data.

## V11.3 guided-demonstration dependency order

1. Preserve the exact formal/P1 logic projection and
   `cb91ebcf364bf07bea40cf541872de7efe07d548d75b2a265dc9be59a6a2b0bd`
   fingerprint; change only the read-only P1 presentation.
2. Extend only the P1 demonstration projection with both localized options and
   one practice-only `demonstrated` marker derived from P1's unchanged route.
   Keep the marker out of every formal scene, formal payload, export, and
   analysis input.
3. Render one P1 question at a time. Show the demonstrated option with green
   styling and the explicit “✓ Correct choice / ✓ 正确选择” label; show the
   rationale and card citation in a separate neutral-blue information panel.
4. Advance locally with a keyboard-operable “Next step” button. After the last
   worked question, reveal the final destination and overall reason, then use
   the existing server transition to begin formal trials.
5. Focus each newly revealed step/result heading and expose it through polite,
   atomic live regions. Keep the P1 card, original method, and checklist
   continuously visible.
6. Bump materials only to `v11.3-stepwise-20260813-draft`; retain V8 export,
   V2 analysis, formal routing, A/B allocation, backtracking, final-path
   scoring, and all security/privacy contracts.
7. Re-run generator/materials/Node, targeted and full pytest, Chrome/Edge
   en/zh at 100%/200%, isolated V3/V2/V9 smokes, cleanup, and diff hygiene.

V11.3 acceptance:

- [x] P1 reveals exactly one current worked question; later questions and the
      final result are absent until “Next step.”
- [x] Both options are visible but non-interactive; one has a green treatment
      plus a textual correct-choice label, so color is not the only cue.
- [x] Each step has a distinct neutral-blue reasoning/evidence panel.
- [x] Final destination/summary appears only after the worked chain, followed
      by “Begin formal scenarios.”
- [x] P1 still creates no answer/path/timing/score data; the signed export
      remains only `demonstration_status: acknowledged`.
- [x] Formal expected derivation, logic fingerprint, sequence, A/B-only
      manipulation, router, scoring, revision, and leakage boundaries remain
      unchanged.

## Preview

```powershell
Set-Location "C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\.worktrees\microstudy-v3-guided-demo"
$env:PYTHONPATH = "src"
python -m cognitive_console.button_board_stepwise --port 0
```

Use a V3-only key path:

```powershell
$env:PYTHONPATH = "src"
python -m cognitive_console.button_board_stepwise --port 0 `
  --verification-key-file ".runtime\button-board-stepwise-v11-verification.key"
```

Do not reuse ports 8876/8878/8891 or their verification keys for polish smoke
tests; choose an isolated ephemeral port.

## Validation commands

```powershell
$env:PYTHONPATH = "src"
python scripts\generate_microstudy_v11_stepwise.py --check
python scripts\validate_button_board_stepwise_materials.py
node tests\button_board_stepwise_js_test.mjs
python -m pytest -q tests\test_button_board_stepwise_materials.py tests\test_button_board_stepwise_web.py
python -m pytest -q
git diff --check
```

Maximum state:
`ready_for_owner_local_preview_no_human_data`; `valid_for_paper=false`.
