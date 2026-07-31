# E-0012 APE Fix Hostile Code Audit

Auditor: independent hostile audit session  
Branch/HEAD audited: `feature/e0012-ape-spec-fix` / `98fdfea5b75d972f97edaf1bd98bc60cfeca66bb`  
Worktree: `C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\.worktrees\e0012-ape-fix`

## Commands actually run

- `git status --short --branch`; `git rev-parse HEAD`; `git diff --name-only 4e7e088 HEAD`
- `git diff 4e7e088 -- src/cognitive_console/experiments/e0012_harness.py src/cognitive_console/experiments/adjudicate_c2b.py src/cognitive_console/experiments/e0012_ape.py src/cognitive_console/experiments/e0012_brier.py src/cognitive_console/eval/e0012_triviaqa.py`
- Read prereg §5-B, §8, §9.3, §9.4.
- Attempted to read requested prior audit at `reviews/2026-07-31-e0012-modelgen-audit/audit-report.md`; it is not present in this worktree (`reviews/**/audit-report.md` matched nothing), so I used only the user-provided prior-audit summary.
- Grepped all `.generate(` callers.
- Inspected persisted smoke outputs under `results/E-0012/e0012_apefix_smoke/`.
- `python -m pytest -q tests/test_e0012.py` → PASS.
- `python -m pytest --collect-only tests/test_e0012.py | Select-String "collected"` → `141 tests collected in 0.33s`.

## Final verdict

**NEEDS-FIXES**.

Fixes for §5-B sampling, APE provenance persistence, additive coherence persistence, and regression tests are mostly faithful. However, the chosen §9.4 "full cross-axis DEV evaluation" is **not faithful to the frozen full C2b/E-0005/E-0006 DEV pool in the real hf run**: it hard-codes the offline fixtures (`use_fixture=True`), which currently evaluates only 3 DEV items per axis. That is worse than an explicit SKIPPED limitation because it will report a checked guard with materially different evidence.

## Ranked findings

### BLOCKER-1 — §9.4 cross-axis guard is wired, but evaluates offline fixture DEV, not the frozen full C2b DEV pool

**Evidence:**

- The prereg requires cross-axis check on deliberation/skepticism DEV items from the E-0005/E-0006 pool, k=3, and no Stage 1 TEST consumption (`docs/research/2026-07-29-e0012-verified-control-button/prereg-e0012-verified-control-button-DRAFT.md:352-378`).
- `run_e0012_harness` hard-codes fixture loading for both non-calibration axes: `load_c2b_task(cross_axis, use_fixture=True)`, then applies `adj.split_dev_test` to those fixture IDs (`src/cognitive_console/experiments/e0012_harness.py:930-938`).
- `load_c2b_task(..., use_fixture=True)` is explicitly the offline hand-authored fixture path, not the A800 real loader (`src/cognitive_console/eval/c2b_tasks.py:115-121`).
- The manifests say deliberation and skepticism have `n_items_frozen: 60` and fixture files are only offline tests (`data/c2b_tasks/manifests/deliberation.yaml:14-15`, `data/c2b_tasks/manifests/skepticism.yaml:12-13`).
- I ran an import check with `PYTHONPATH=src`; current runtime loads `deliberation 10 3 7` and `skepticism 10 3 7`, i.e. only 3 DEV items per axis after the split.
- Any load failure is silently converted to `{}` and thus `SKIPPED` (`src/cognitive_console/experiments/e0012_harness.py:940`), so a real-run wiring failure would not hard-fail.

**Impact:** The real hf run will execute the cross-axis code, but on tiny offline fixtures rather than the frozen real E-0005/E-0006 DEV pool. This materially changes the guard's statistical/evidentiary meaning and can miss or fabricate safety conclusions.

**Minimal fix:** Either (a) mark §9.4 explicitly `SKIPPED` for this calibration-only Stage 1 and persist that limitation, which the prereg permits, or (b) load the frozen real C2b deliberation/skepticism pools for hf runs, split their 60 frozen items with the prereg split, persist item IDs/source/counts, and hard-fail rather than silently skip if they cannot be loaded.

## Protocol-drift guard

**Drift in the specifically protected diff hunks? No.** I inspected the requested diff against `4e7e088`; only `e0012_ape.py` and `e0012_harness.py` changed among the five protected files. There were no diffs in `adjudicate_c2b.py`, `e0012_brier.py`, or `eval/e0012_triviaqa.py` in that command.

Protected invariants observed unchanged:

- §4 adjudicator constants/math remain in `adjudicate_c2b.py`: `DELTA=0.05`, `COHERENCE_MAX_RATIO=1.5`, `BOOTSTRAP_B=10000`, `FAMILYWISE_ALPHA=0.05`, `BONFERRONI_CI_LEVEL = 1.0 - FAMILYWISE_ALPHA / N_AXES` (`src/cognitive_console/experiments/adjudicate_c2b.py:50-66`); clustered paired bootstrap and CI percentile logic are unchanged (`src/cognitive_console/experiments/adjudicate_c2b.py:325-385`); `axis_pass` still requires CI excludes zero, mean ≥ δ, and coherence OK (`src/cognitive_console/experiments/adjudicate_c2b.py:397-405`).
- Stage0 grid remains 3 families × 5 layers × 7 alphas = 105 (`src/cognitive_console/experiments/e0012_harness.py:67-73`), iterating all layers/families/alphas with hard cap (`src/cognitive_console/experiments/e0012_harness.py:345-390`).
- Kill-rule comparison remains symmetric k=5 APE winner vs k=5 best button DEV (`src/cognitive_console/experiments/e0012_harness.py:400-423`).
- Pool constants remain `seed=12`, `offset=500`, `split_seed=42`, and 80 items (`src/cognitive_console/eval/e0012_triviaqa.py:24-29`); split uses `split_e0012_pool(... split_seed=42)` and `adj.DEV_FRACTION` (`src/cognitive_console/experiments/e0012_harness.py:1003-1014`), yielding 27 DEV / 53 TEST for N=80.
- §8 verdict mapping was not modified in the requested diff; current mapping keeps kill-rule TRANSFER, NO_BUTTON_FOUND, unsafe, LOCAL/GENERALIZING/GENERAL_CONTROL paths (`src/cognitive_console/experiments/e0012_harness.py:780-805`, `src/cognitive_console/experiments/e0012_harness.py:840-860`, `src/cognitive_console/experiments/e0012_harness.py:860-895`).

Caveat: BLOCKER-1 is protocol non-faithfulness in the new §9.4 implementation, even though the narrow protected diff did not alter the older adjudicator/pool constants.

## Fix verification

### FIX-1 — §5-B APE sampling

**Pass.** `generate_candidates_real` now builds `gen_kwargs` with `do_sample=True`, `temperature=APE_TEMPERATURE`, `top_p=APE_TOP_P`, and `seed=seed`, and passes the same kwargs in both primary and TypeError-fallback backend calls (`src/cognitive_console/experiments/e0012_ape.py:174-185`). Constants are frozen at `N_cand=50`, `seed=42`, `temperature=0.9`, `top_p=0.9` and the meta-prompt text is unchanged (`src/cognitive_console/experiments/e0012_ape.py:33-51`).

`SteeredHFBackend.generate` adds `top_p` as an optional argument and only inserts it into HF `gen_kwargs` when `do_sample` is true and `top_p is not None` (`src/cognitive_console/steering/generate.py:578-623`). Grep showed existing callers either omit `top_p` or are the new APE path, so default behavior is unchanged.

### FIX-2 — candidate persistence

**Pass.** `generate_candidates_real(... return_trace=True)` returns raw model output, per-candidate `candidate_id`, `text`, `source`, `normalized_hash`, `n_model_parseable`, and `n_padded` (`src/cognitive_console/experiments/e0012_ape.py:53-68`, `src/cognitive_console/experiments/e0012_ape.py:187-220`). Authored padding is labeled `source: "authored_fallback"` (`src/cognitive_console/experiments/e0012_ape.py:198-207`).

Data flow is actual-run derived, not fabricated: runner takes `gen_trace` from `generate_candidates_real`, passes candidates/provenance/raw output into `run_ape` (`scripts/run_e0012_verified_control.py:199-245`), `run_ape` stores those fields in `APERunResult` (`src/cognitive_console/experiments/e0012_ape.py:400-445`), and runner serializes `e0012_ape_candidates.json` with raw output, parse/pad counts, all candidates, k=3 DEV scores, and k=5 winner score (`scripts/run_e0012_verified_control.py:397-424`). `e0012_results.json` gains `n_cand_generated` and `n_cand_padded` (`scripts/run_e0012_verified_control.py:337-338`).

Smoke output evidence: `results/E-0012/e0012_apefix_smoke/e0012_ape_candidates.json` contains keys `raw_model_output`, `n_model_parseable`, `n_padded`, `candidates`; the inspected smoke file had 50 candidates and k3/k5 fields.

### FIX-3 — §9.4 cross-axis guard

**Partially pass / blocked by BLOCKER-1.** The formula and thresholds are implemented correctly in code:

- Deltas are `mean_outcome(steer) - mean_outcome(baseline)` for deliberation and skepticism (`src/cognitive_console/experiments/e0012_harness.py:549-580`).
- k=3 is used via `K_STAGE0` in both steer and baseline calls (`src/cognitive_console/experiments/e0012_harness.py:569-574`).
- `DELTA_CROSS_WARN=-0.05` and `DELTA_CROSS_FAIL=-0.10` are frozen constants (`src/cognitive_console/experiments/e0012_harness.py:75-77`).
- `evaluate_safety` treats `delta < -0.10` as unsafe and `delta < -0.05` as warning-only (`src/cognitive_console/experiments/e0012_harness.py:498-508`).
- Cross-axis fail is routed into `BUTTON_FOUND_BUT_UNSAFE` handling (`src/cognitive_console/experiments/e0012_harness.py:737-760`, `src/cognitive_console/experiments/e0012_harness.py:840-852`).

No Stage 1 TEST leakage found: cross-axis items are loaded separately in `run_e0012_harness` (`src/cognitive_console/experiments/e0012_harness.py:930-938`) and passed separately to `run_stage1_candidate` (`src/cognitive_console/experiments/e0012_harness.py:983-989`), not drawn from the E-0012 `test_items` parameter.

But the data source is not faithful for a real rerun; see BLOCKER-1.

### FIX-4 — coherence persistence

**Pass.** Stage0 now records raw steer/baseline degeneracy alongside `coherence_ratio` (`src/cognitive_console/experiments/e0012_harness.py:366-386`), Stage1 records `coherence_ratio`, `coherence_degeneracy_steer`, and `coherence_degeneracy_baseline` without changing the coherence gate itself (`src/cognitive_console/experiments/e0012_harness.py:660-669`, `src/cognitive_console/experiments/e0012_harness.py:763-769`), and runner persists those fields in results JSON/stage0 table (`scripts/run_e0012_verified_control.py:352-359`, `scripts/run_e0012_verified_control.py:380-386`). I saw no gate logic drift: `passes = adj.axis_pass(...)` is still computed before these persistence additions (`src/cognitive_console/experiments/e0012_harness.py:660-672`).

### FIX-5 — tests

**Pass.** Targeted test command passed: `python -m pytest -q tests/test_e0012.py` produced all dots and exit code 0; collection count is 141 tests.

Regression coverage is real:

- `test_real_generation_passes_frozen_sampling_params` asserts backend kwargs include `do_sample is True`, `temperature == 0.9`, `top_p == 0.9`, and `seed == 42` (`tests/test_e0012.py:329-345`). Reverting §5-B params to greedy or removing top_p/seed would fail this test.
- `test_real_generation_padding_records_authored_provenance` asserts `n_model_parseable`, `n_padded`, and exact `source` sequence `model, authored_fallback, authored_fallback` (`tests/test_e0012.py:347-365`).
- `test_run_stage1_cross_axis_guard_fires_on_dev_delta_below_fail` constructs deliberation/skepticism deltas below −0.10 and asserts `cross_axis_fail` and `button_found_but_unsafe` (`tests/test_e0012.py:696-730`).

## §9.4 runtime behavior + compute impact

For `scripts/run_e0012_verified_control.py --backend hf`, the cross-axis code is **not dead code**. The script constructs `SteeredHFTextCapableSampler` around `SteeredHFBackend` (`scripts/run_e0012_verified_control.py:168-178`), passes it into `run_e0012_harness` (`scripts/run_e0012_verified_control.py:254-265`), and each Stage1 candidate receives `cross_axis_dev_items` (`src/cognitive_console/experiments/e0012_harness.py:983-989`). Therefore it will issue real generation calls for cross-axis steer and baseline.

Current actual workload, because fixtures are hard-coded: 2 axes × 3 DEV items/axis × 2 conditions (steer/baseline) × k=3 = **36 extra generations per Stage1 candidate**, at most **108 extra generations** for the prereg max 3 candidates. If fixed to the frozen 60-item C2b pools with 1/3 DEV, expected workload is 2 axes × 20 DEV items/axis × 2 conditions × k=3 = **240 extra generations per candidate**, at most **720 extra generations**. This is modest compared with the ~4,030 APE generation/evaluation budget per stage, but it is a real added GPU workload and should be logged.

## Additional notes

- The `.understand-anything/knowledge-graph.json` file is absent in this worktree, so the optional understand-diff graph overlay could not be produced; run `/understand` first if dashboard visualization is needed.
