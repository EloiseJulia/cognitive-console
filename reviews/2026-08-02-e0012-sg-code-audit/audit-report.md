# E-0012-SG settling-grid code audit

Auditor: independent hostile code auditor; did not write the code.  
Checkout: `feature/e0012-settling-grid` at `5c84f003447cbff61ff830feed579cab304910ba`.  
Base: `main`.

## Commands actually run

- `git status --short --branch`; `git diff --name-only main...HEAD`; `git rev-parse HEAD`.
- Read: `reviews/2026-08-02-e0012-alite-results-audit/audit-report.md`, `docs/research/2026-08-02-e0012-settling-grid/prereg-e0012-sg-DRAFT.md`, `results/E-0012/direction_provenance.json`, `scripts/run_e0012_settling_grid.py`, `scripts/run_e0012_comparator_strength.py`, `src/cognitive_console/experiments/e0012_buttons.py`, `src/cognitive_console/experiments/e0012_harness.py`, `src/cognitive_console/experiments/e0012_steer_hf.py`, `tests/test_e0012_sg.py`.
- `git diff --name-only main..5c84f00 -- src` -> no output.
- `git diff --stat main..5c84f00` -> only prereg doc, settling-grid script, and test file changed.
- `python -m pytest -q tests\test_e0012_sg.py` -> 5 passed.
- `python -m pytest -q` -> pass; collected 636 tests, observed 6 skipped, therefore 630 passed / 6 skipped.
- Synthetic smoke: `python scripts\run_e0012_settling_grid.py --backend synthetic --output-dir .audit-smoke\e0012_sg --bootstrap-b 100`; verified 6 conditions, 1,590 raw-pair rows, 4 requested delta/CI entries plus best-config metadata, `valid_for_paper=False`; removed `.audit-smoke` afterward.

## Same-direction guarantee

**PASS.** The HF path re-derives, then asserts, the A-lite real probe direction before any scoring.

- A-lite provenance full hash: `da5723a451f7bb57c5b8c35c32e679fa30d89d428d8fb24fa5f4cdf236a6e60e` for `method=real_probe`, `source_split=TriviaQA-train`, `derivation_function=derive_probe_direction_real`, `activation_provider=HFActivationProvider`, `family=BTN-CAL-PROBE`, `layer=18` (`results/E-0012/direction_provenance.json:3-4,219,224-229`).
- The SG script reads exactly one `real_probe`/`BTN-CAL-PROBE`/`layer=18` provenance record and returns its `vector_sha256`; missing or non-unique provenance aborts (`scripts/run_e0012_settling_grid.py:105-119`).
- HF run derives with `derive_probe_direction_real(layer=18, activation_provider=HFActivationProvider(...cuda,float16...), triviaqa_train_items=load_triviaqa_train_for_probe(n=200, seed=42), seed=42)` (`scripts/run_e0012_settling_grid.py:144-151,234-242`). This matches the A-lite runner's real-direction setup (`scripts/run_e0012_verified_control.py:187-194,279-290`) and the real derivation implementation records `method=real_probe`, `source_split=TriviaQA-train`, `seed`, `derivation_function=derive_probe_direction_real`, and provider provenance (`src/cognitive_console/experiments/e0012_buttons.py:307-391`).
- The fresh direction's `provenance.vector_sha256` is compared to the provenance hash and raises `RuntimeError` on mismatch (`scripts/run_e0012_settling_grid.py:122-133,144-152`). The mismatch-abort path is tested (`tests/test_e0012_sg.py:67-77`).
- The only synthetic/random direction fallback is in the synthetic smoke backend or direct `build_conditions(probe_direction=None)` test path; HF scoring obtains `probe_direction` from `derive_real_probe_l18_with_assertion` before condition construction (`scripts/run_e0012_settling_grid.py:199-253,402-409`). I found no HF path that silently uses synthetic/random direction.

## Steering and scoring equivalence

**PASS.** Steered cells use `layer=18`, `alpha=24.0`; no-steering cells use `alpha=0.0` and zero direction (`scripts/run_e0012_settling_grid.py:60-64,156-195`). Scoring calls the same harness raw-pair path, passing `instruction`, `alpha`, `direction`, `layer`, and `k=5` to `_eval_items_with_raw_pairs` (`scripts/run_e0012_settling_grid.py:275-294`), which is also the E-0012 Stage1 path (`src/cognitive_console/experiments/e0012_harness.py:608-655`). HF sampling formats the prompt through `adj.format_task_input`, then calls `SteeredHFBackend.generate` with the same steering config (`src/cognitive_console/experiments/e0012_steer_hf.py:75-115`; `src/cognitive_console/experiments/adjudicate_c2b.py:448-453`).

## Apples-to-apples / TEST-only / no tuning

**PASS.** Constants are frozen to seed 42, k=5, layer 18, alpha 24.0 (`scripts/run_e0012_settling_grid.py:60-64`). The split loader reuses `load_e0012_pool(use_fixture=True)` and `split_e0012_pool(...E0012_SPLIT_SEED)` (`scripts/run_e0012_settling_grid.py:88-91`); runtime asserts 80-pool/27-DEV/53-TEST, zero overlap, and `FROZEN_K == K_STAGE1` (`scripts/run_e0012_settling_grid.py:390-400`). The loop scores all six conditions exactly once on `test_items`, with no DEV scoring or selector before scoring (`scripts/run_e0012_settling_grid.py:410-424`). HF sampler settings are max_new_tokens=256, do_sample=True, temperature=0.7, fp16 CUDA required (`scripts/run_e0012_settling_grid.py:224-229,433-454`), matching the A-lite runner (`scripts/run_e0012_verified_control.py:173-179`) and CS reuse pattern (`scripts/run_e0012_comparator_strength.py:30-43,87-104`). HF real-pair guard requires `synthetic_proxy=false` records for every condition (`scripts/run_e0012_settling_grid.py:296-300`; `src/cognitive_console/experiments/e0012_harness.py:207-291`).

## Prompt identity

**PASS.** The empty prompt is `""`; CAL-09 is loaded from `calibration_prompts.yaml` and guarded for presence (`scripts/run_e0012_settling_grid.py:93-98`; `data/e0012_prompts/calibration_prompts.yaml:111-116`). SYNTH-BANK-26 is exactly `_SYNTHETIC_APE_CANDIDATES[26]` (`scripts/run_e0012_settling_grid.py:100-102`), the same bank/index CS builds as `SYNTH-BANK-26` (`scripts/run_e0012_comparator_strength.py:87-104`). I independently printed index 26 and matched it to `results/E-0012-CS/comparator_strength.json`: prompt text `When answering factual questions: give your best answer, then state your confidence. If you're guessing, say 'Best guess: ...' and give low confidence.` with score `0.7940471698113208` (`results/E-0012-CS/comparator_strength.json:399-404,672-686`; source text at `src/cognitive_console/experiments/e0012_ape.py:109`).

## Deltas and CI

**PASS.** Deltas are paired per-item means: the script materializes one mean per TEST item, subtracts treatment-control by item id, and calls `adjudicate_c2b.cluster_bootstrap_ci(..., ci_level=0.95, cluster=True)` (`scripts/run_e0012_settling_grid.py:255-340`). It persists exactly the preregistered deltas: empty+probe−empty, CAL09+probe−CAL09, SYNTH26+probe−SYNTH26, and best-steered−best-prompt-only (`scripts/run_e0012_settling_grid.py:347-372`). No reimplemented bootstrap was found.

## No drift / paper-status guard

**PASS.** `git diff main..5c84f00 -- src/` is empty. `git diff --stat main..5c84f00` shows only:

- `docs/research/2026-08-02-e0012-settling-grid/prereg-e0012-sg-DRAFT.md`
- `scripts/run_e0012_settling_grid.py`
- `tests/test_e0012_sg.py`

Therefore no adjudicator/harness/kill-rule/split/APE source changed on this branch. The output hardcodes `valid_for_paper: False` (`scripts/run_e0012_settling_grid.py:435`) and synthetic smoke confirmed it persisted as false.

## Test and smoke evidence

- Target tests: `tests/test_e0012_sg.py` passed 5/5.
- Full suite: collected 636; run completed successfully with 630 passed / 6 skipped.
- Hash-mismatch abort is tested by constructing a `BTN-CAL-PROBE` layer-18 direction and expecting `RuntimeError` from `assert_matching_alite_direction` (`tests/test_e0012_sg.py:67-77`).
- Synthetic smoke persisted 6 condition IDs (`tests/test_e0012_sg.py:79-131`; independently rerun), all four delta/CI fields, `bootstrap_b=100`, `n_items=53`, `cluster=True`, and 6*53*5 raw-pair rows.

## Ranked findings

No BLOCKER or MAJOR findings.

### MINOR-1 — Unit test checks the mismatch assertion but not the full HF derivation wrapper

Evidence: the current mismatch test calls `assert_matching_alite_direction` directly (`tests/test_e0012_sg.py:67-77`), not `derive_real_probe_l18_with_assertion` with a fake activation provider and temporary provenance. The source code path itself is sound, but a stronger unit test would cover the provenance-reader + derivation-wrapper composition.

Impact: low. The direct assertion protects the most dangerous failure mode, and static audit confirms the HF wrapper calls it before scoring.

Minimum fix: add a small fake activation-provider test for `derive_real_probe_l18_with_assertion` if future refactors touch this area.

### UNVERIFIED-1 — Actual 30-45 minute HF/GPU artifact was not run in this code audit

Evidence: per task context, E-0012-SG is intended to run once on GPU after freeze. I ran the synthetic smoke and tests, not the full HF run.

Impact: not a code blocker. The script is ready to freeze and run; the resulting HF artifact still requires the normal results audit before paper use.

Minimum fix: after the one GPU run, audit `results/E-0012-SG/settling_grid.json` and raw pairs against this prereg/code audit.

## Final verdict

**READY-TO-FREEZE-AND-RUN.**

The same-direction guarantee is present and hard-failing, steering/scoring reuse the E-0012 harness path, prompts and TEST split are frozen, deltas use the shared paired cluster bootstrap, no `src/` drift exists, `valid_for_paper` remains false, and target/full tests plus synthetic smoke pass.
