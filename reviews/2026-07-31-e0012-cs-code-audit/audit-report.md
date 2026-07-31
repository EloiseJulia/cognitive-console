# E-0012-CS Independent Hostile Code Audit

Auditor: independent hostile code auditor (did not write E-0012-CS).  
Branch/HEAD audited: `feature/e0012-comparator-strength` / `54212b1` (worktree: `.worktrees\e0012-cs`).  
Scope: `scripts/run_e0012_comparator_strength.py`, DRAFT prereg, CS tests, and frozen E-0012 harness/runner dependencies.

## Commands actually run

- Read: `AGENTS.md`; `AI-Instruction.md` Part I audit references; `docs/research/2026-07-31-e0012-comparator-strength/prereg-e0012-cs-DRAFT.md`; `reviews/2026-07-31-e0012-v3-audit/audit-report.md`; `scripts/run_e0012_comparator_strength.py`; `scripts/run_e0012_verified_control.py`; relevant harness/Brier/button/source files; `tests/test_e0012_cs.py`.
- `git --no-pager status --short --branch`; `git --no-pager diff --name-only main...HEAD`; `git --no-pager diff --name-only main -- src/`; `git --no-pager diff --stat main...HEAD`; `git --no-pager diff --check main...HEAD`.
- Recomputed split/condition inventory with Python import of `run_e0012_comparator_strength`: `pool 80`, `dev 27`, `test 53`, `overlap 0`, `counts {'synthetic_bank': 30, 'calibration_yaml': 18, 'baseline': 1, 'button': 1}`, `unique_ids 50 total 50`.
- `python -m pytest -q tests\test_e0012_cs.py` -> PASS, 5/5 passed.
- `python -m pytest -q` -> PASS, 617 collected; observed 611 passed, 6 skipped, 1 warning. No `tests/test_lineage.py` PermissionError occurred, so no clean-main attribution run was needed.

## Apples-to-apples comparability

**PASS.** The CS HF sampler matches the v3 verified-control sampling settings that matter for score comparability:

- CS requires CUDA for HF and hard-fails otherwise: `--backend hf requires cuda; E-0012-CS is frozen as fp16-on-cuda` (`scripts/run_e0012_comparator_strength.py:172-179`). The backend is constructed with `device="cuda"`, `dtype="float16"`, and `seed=seed` (`scripts/run_e0012_comparator_strength.py:175-180`).
- CS constructs `SteeredHFTextCapableSampler(hf_backend, max_new_tokens=256, do_sample=True, temperature=0.7, seed=seed)` (`scripts/run_e0012_comparator_strength.py:181-187`). The v3 verified-control runner constructs the same sampler class and generation knobs at `max_new_tokens=256`, `do_sample=True`, `temperature=0.7`, `seed=run_seed` (`scripts/run_e0012_verified_control.py:167-175`).
- CS uses `FROZEN_K = 5` (`scripts/run_e0012_comparator_strength.py:58-60`) and asserts it equals the frozen harness `K_STAGE1` (`scripts/run_e0012_comparator_strength.py:246-247`; `src/cognitive_console/experiments/e0012_harness.py:69-70`).
- CS does not reimplement the score. `score_condition()` calls `e0012_harness._eval_items_with_raw_pairs(...)` with `k=FROZEN_K`, then returns `_mean_outcome(batches)` (`scripts/run_e0012_comparator_strength.py:194-214`). The harness path records raw `(confidence, correctness)` pairs for TextCapable samplers and uses `SampleBatch.mean_outcome()` through `_mean_outcome` (`src/cognitive_console/experiments/e0012_harness.py:205-292`).

## Test-only / no leakage / no selection

**PASS.** Frozen pool constants are unchanged and imported from the E-0012 fixture: `E0012_POOL_N=80`, `E0012_POOL_SEED=12`, `E0012_POOL_OFFSET=500`, `E0012_SPLIT_SEED=42` (`src/cognitive_console/eval/e0012_triviaqa.py:27-30`). CS loads `load_e0012_pool(use_fixture=True)` and splits with `split_e0012_pool(..., split_seed=E0012_SPLIT_SEED)` (`scripts/run_e0012_comparator_strength.py:81-85`), where the harness split delegates to the frozen adjudicator split rule (`src/cognitive_console/experiments/e0012_harness.py:1000-1010`).

The only evaluation call passes `test_items` into `score_condition()` (`scripts/run_e0012_comparator_strength.py:262-268`). `dev_items` are only counted and overlap-checked in the summary (`scripts/run_e0012_comparator_strength.py:240-245`, `296-305`). My recomputation produced 27 DEV / 53 TEST with 0 overlap.

All conditions are constructed before scoring and then evaluated exactly once in a single `for condition in conditions` loop (`scripts/run_e0012_comparator_strength.py:240-274`). Count guards enforce 30 synthetic-bank, 18 calibration-YAML, 1 baseline, and 1 button condition (`scripts/run_e0012_comparator_strength.py:248-257`). My recomputation found 50 unique IDs and no missing CAL-09/button.

## Real pairs / N-01 guard

**PASS.** The HF path must return a `SteeredHFTextCapableSampler` and the script hard-fails if it is not a `TextCapableSampler` (`scripts/run_e0012_comparator_strength.py:168-190`). The harness `TextCapableSampler` path calls `sample_with_texts`, parses confidence and correctness from generated text, and records `synthetic_proxy=False` (`src/cognitive_console/experiments/e0012_harness.py:227-271`). The synthetic fallback path is explicitly isolated as `synthetic_proxy=True` (`src/cognitive_console/experiments/e0012_harness.py:272-285`).

CS adds a per-condition HF guard: after each condition, `raw_store.has_real_pairs(condition.condition_id)` must be true or the run raises (`scripts/run_e0012_comparator_strength.py:269-273`). `BrierRawStore.has_real_pairs()` checks for at least one non-proxy pair in that channel (`src/cognitive_console/experiments/e0012_brier.py:244-250`). Given the TextCapable branch, a real GPU run cannot silently fall back to proxy pairs without tripping this guard.

## Button correctness and fair head-to-head

**PASS.** The constants freeze the intended button: `BUTTON_FAMILY = BTN_PROBE`, `BUTTON_LAYER = 19`, `BUTTON_ALPHA = 24.0` (`scripts/run_e0012_comparator_strength.py:61-63`), and `BTN_PROBE` is `"BTN-CAL-PROBE"` (`src/cognitive_console/experiments/e0012_buttons.py:46`). CS derives layer directions by calling `all_directions_for_layer(BUTTON_LAYER, hidden_dim)` and selecting the matching family (`scripts/run_e0012_comparator_strength.py:135-139`), the same harness derivation shape used for E-0012 directions (`src/cognitive_console/experiments/e0012_harness.py:940-945`, `971-975`; `src/cognitive_console/experiments/e0012_buttons.py:387-397`).

The button condition has empty prompt text, `alpha=24.0`, `layer=19`, and the selected button direction (`scripts/run_e0012_comparator_strength.py:149-157`). Prompt and baseline conditions use zero direction, `alpha=0.0`, `layer=0`; prompt conditions carry only the system prompt text, and baseline carries no prompt (`scripts/run_e0012_comparator_strength.py:99-132`). Every condition, including button and prompt conditions, is scored through the same `score_condition()` call and same raw-pair store (`scripts/run_e0012_comparator_strength.py:194-214`, `262-274`).

## Persistence / provenance

**PASS with one minor summary gap below.** Each condition payload persists stable `id`, `source`, full `prompt_text`, `prompt_hash`, `button_spec`, TEST mean `1-Brier`, `k`, `n_test_items`, and raw-pair count (`scripts/run_e0012_comparator_strength.py:217-228`). The summary hardcodes `valid_for_paper: False` (`scripts/run_e0012_comparator_strength.py:288-295`), includes pool seeds/IDs and split overlap (`scripts/run_e0012_comparator_strength.py:296-305`), all condition results (`scripts/run_e0012_comparator_strength.py:309-311`), explicit `max_condition`, `best_synthetic_bank`, `cal_09`, `button`, `baseline`, and `raw_pairs_path` (`scripts/run_e0012_comparator_strength.py:312-338`). The raw JSONL store is opened fresh at `comparator_strength_raw_pairs.jsonl` and closed after scoring (`scripts/run_e0012_comparator_strength.py:234-236`, `259-276`).

## Prereg faithfulness

**Mostly PASS.** The script implements the frozen condition set described in the DRAFT prereg: first 30 `_SYNTHETIC_APE_CANDIDATES`, all 18 YAML prompts including CAL-09, baseline, and `BTN-CAL-PROBE` at L19 alpha 24.0 (`docs/research/2026-07-31-e0012-comparator-strength/prereg-e0012-cs-DRAFT.md:12-21`; `scripts/run_e0012_comparator_strength.py:88-160`). It implements the frozen evaluation commitments: E-0012 pool/split, TEST-only scoring, mean `1-Brier` through the harness, `k=5`, seed 42, HF CUDA fp16 real pairs, and synthetic smoke as non-paper-valid (`docs/research/2026-07-31-e0012-comparator-strength/prereg-e0012-cs-DRAFT.md:23-31`; `scripts/run_e0012_comparator_strength.py:56-64`, `81-85`, `163-191`, `194-214`, `288-338`). No extra conditions, no DEV selection/tuning, no prompt rewriting, no reranking, no early stopping, and no new adjudication tier were found.

The only prereg divergence I found is a summary/reporting gap: the DRAFT says to report the maximum human-prompt TEST score across the 30 synthetic-bank plus 18 calibration-YAML prompts side-by-side with the button (`docs/research/2026-07-31-e0012-comparator-strength/prereg-e0012-cs-DRAFT.md:33-39`). The code persists all per-condition scores, `best_synthetic_bank`, CAL-09, and overall `max_condition`, but does not explicitly persist `max_human_prompt` or `best_calibration_yaml` (`scripts/run_e0012_comparator_strength.py:278-338`). This is reconstructable from `conditions`, so I do not consider it a soundness blocker.

## No drift to frozen files

**PASS.** `git diff main...HEAD --name-only` shows only:

- `docs/research/2026-07-31-e0012-comparator-strength/prereg-e0012-cs-DRAFT.md`
- `scripts/run_e0012_comparator_strength.py`
- `tests/test_e0012_cs.py`

`git diff main -- src/` produced no paths. The branch imports frozen harness/split/button helpers but does not modify `src/` adjudicator, kill-rule, grid, split constants, or frozen experiment logic.

## Tests

**PASS.** `tests/test_e0012_cs.py` asserts the full 50-condition set and IDs (`tests/test_e0012_cs.py:27-36`), frozen split identity, 27/53 sizes, and disjointness (`tests/test_e0012_cs.py:39-49`), frozen `k=5` equals `K_STAGE1` (`tests/test_e0012_cs.py:52-55`), prompt text/button spec persistence (`tests/test_e0012_cs.py:58-70`), and smoke-output provenance including `valid_for_paper=false`, counts, split, `k`, summary fields, raw-pairs path, and exactly `50 * 53 * 5` raw-pair rows (`tests/test_e0012_cs.py:73-101`).

Targeted run: `python -m pytest -q tests\test_e0012_cs.py` -> `..... [100%]`, 5/5 passed.  
Full run: `python -m pytest -q` -> PASS, 617 collected; observed 611 passed, 6 skipped, 1 warning. No lineage PermissionError flake occurred.

## Ranked findings

### MINOR-1 — Summary omits explicit `max_human_prompt` / `best_calibration_yaml` decision variable

**Evidence:** The prereg's descriptive decision rule says to report the maximum human-prompt TEST score across all 48 human prompts side-by-side with the button (`docs/research/2026-07-31-e0012-comparator-strength/prereg-e0012-cs-DRAFT.md:33-39`). The script persists all conditions and summary fields for overall `max_condition`, `best_synthetic_bank`, `cal_09`, `button`, and `baseline`, but no explicit `max_human_prompt` and no explicit best calibration-YAML prompt if a non-CAL-09 YAML prompt wins (`scripts/run_e0012_comparator_strength.py:278-338`).

**Impact:** The artifact remains reconstructable and the raw condition list is complete, so the head-to-head can still be settled. However, a one-shot paper-evidence run should persist the exact descriptive decision variable directly to avoid manual post-hoc interpretation.

**Minimal fix:** Add summary fields `max_human_prompt` over `source in {'synthetic_bank','calibration_yaml'}` and `best_calibration_yaml` with id/text/score. Keep `valid_for_paper=false`.

### MINOR-2 — Markdown trailing whitespace in prereg

**Evidence:** `git diff --check main...HEAD` reports trailing whitespace at `docs/research/2026-07-31-e0012-comparator-strength/prereg-e0012-cs-DRAFT.md:3-5`.

**Impact:** No scientific or runtime effect, but it is a pre-freeze hygiene issue.

**Minimal fix:** Remove trailing spaces or use explicit `<br>` if line breaks are intended.

## Final verdict

**READY-TO-FREEZE-AND-RUN.**

I found no BLOCKER or MAJOR issue. The CS script is additive, TEST-only, uses the same HF sampler settings and harness scoring path as the verified-control run, evaluates exactly 50 predeclared conditions once, preserves real-pair guards, applies the correct button and prompt/no-steering conditions, persists raw pairs and provenance, and passes targeted plus full tests. Fixing MINOR-1 before the GPU run would improve paper-evidence clarity, but the current implementation is sound enough to freeze and run because the complete condition table makes the strongest-human-vs-button comparison reconstructable.
