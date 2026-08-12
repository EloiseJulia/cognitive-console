# Implementation Plan: V3 Stepwise Open-Book Button Board

- **Status:** `DRAFT / NOT FROZEN / implementation for owner-local preview`
- **Branch:** `feature/microstudy-v3-stepwise`
- **Governance:** D-0117
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

## Preview

```powershell
Set-Location "C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\.worktrees\microstudy-v3-stepwise"
$env:PYTHONPATH = "src"
python -m cognitive_console.button_board_stepwise --port 8891 --open
```

Use a V3-only key path:

```powershell
$env:PYTHONPATH = "src"
python -m cognitive_console.button_board_stepwise --port 8891 `
  --verification-key-file ".runtime\button-board-stepwise-v11-verification.key"
```

Do not reuse ports 8876/8878 or their verification keys.

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
