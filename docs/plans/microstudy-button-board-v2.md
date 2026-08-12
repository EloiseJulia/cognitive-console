# Implementation Plan: V2 Button-Board Gate Application Micro-Study

- **Status:** `DRAFT / NOT FROZEN / implementation complete for owner-local preview`
- **Branch:** `feature/microstudy-v2-buttonboard`
- **Governance:** D-0116
- **Non-goals:** human data, recruitment, timing, freeze, public deployment,
  paper/claim/result edits, Contract/Flat comparison, or V9 migration

## Dependency order

1. Read and preserve the V9 local security/export/accessibility skeleton.
2. Add independent structured V10 fictional source and automatic router/reason/
   boundary key derivation.
3. Generate public materials, private derived keys, and balanced sequences.
4. Add an independent V2 server, button-board UI, signed V6 export, and
   V2-only analysis while leaving the V9 entry point and artifacts unchanged.
5. Add generator, material, router, leakage, A/B, boundary-scoring, bilingual,
   export, analysis, HTTP security, privacy, Node, and real-browser tests.
6. Run generator check, validators, Node, targeted tests, full pytest, isolated
   HTTP smoke, Chrome/Edge gates, and diff hygiene.
7. Commit without push; pin the implementation commit in D-0116 and registry
   through a docs-only lineage commit.

## Acceptance checklist

- [x] F1/F2 differ only in structured paired raw counts.
- [x] Non-manipulated F1/F2 canonical hash fails closed.
- [x] Each attempt receives one variant and six formal cards.
- [x] Router and reason keys are generated rather than hand-entered.
- [x] F1/F6/F7 boundary choice controls Strict GAA.
- [x] Formal cards contain neutral records and every card includes response,
      paired comparison, amount, effects, and conditions.
- [x] Tutorial teaches one intuition and interaction only.
- [x] Practice feedback is record-specific.
- [x] Public materials/payload/DOM/ARIA/export contain no expected keys.
- [x] English/Simplified Chinese stable-ID parity and locale locking.
- [x] V6 signature and fail-closed V5/V9 mixing rejection.
- [x] Loopback/origin/CSRF/capability/idempotency/TTL/capacity/no-log/no-storage.
- [x] Chrome/Edge, both locales, 100%/200%, keyboard/focus/equal-grid/desktop gate.
- [x] V9 source, materials, tests, schemas, and default entry point unchanged.

## Preview

From this worktree, explicitly force the local source tree:

```powershell
Set-Location "C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\.worktrees\microstudy-v2-buttonboard"
$env:PYTHONPATH = "src"
python -m cognitive_console.button_board --port 8878 --open
```

Use an owner-selected V2-only key path when desired:

```powershell
$env:PYTHONPATH = "src"
python -m cognitive_console.button_board --port 8878 `
  --verification-key-file ".runtime\button-board-v10-verification.key"
```

Do not use the running V9 port/key. The V9 preview remains:

```powershell
$env:PYTHONPATH = "src"
python -m cognitive_console.microstudy
```

## Validation commands

```powershell
$env:PYTHONPATH = "src"
python scripts\generate_microstudy_v10.py --check
python scripts\validate_button_board_materials.py
node tests\button_board_js_test.mjs
python -m pytest -q tests\test_button_board_materials.py tests\test_button_board_web.py
python -m pytest -q
git diff --check
```

Maximum state:
`ready_for_owner_local_preview_no_human_data`; `valid_for_paper=false`.
