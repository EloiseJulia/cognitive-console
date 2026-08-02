# E-0012 Real-Direction Code Audit

Auditor: independent hostile code auditor; did not write the implementation.  
Checkout: `feature/e0012-real-directions` at `bdfb8f3`.  
Scope: compare against `main`; report only, no fixes.

## Commands actually run

- `git --no-pager status --short --branch`; `git --no-pager rev-parse --short HEAD`; `git --no-pager diff --name-only main...HEAD`.
- Read prereg §3-B-1/§3-B-2 and D-0068 addendum (`docs/research/2026-07-29-e0012-verified-control-button/prereg-e0012-verified-control-button-DRAFT.md:102-136`, `:487-496`), D-0067/D-0068 context (`docs/ledgers/decision-log.md:8-13`), feasibility assessment, and reconcile audit.
- Inspected source with `rg`, `view`, and numbered PowerShell `Get-Content` ranges.
- `python -m pytest -q tests/` → **PASS**, 618 passed / 6 skipped / 1 warning.
- `python scripts\run_e0012_verified_control.py --backend synthetic --output-dir results\audit-e0012-smoke --n-items 12 --seed 42` → **PASS**, Stage0 `70/70`, Stage1 `2`, families `{BTN-CAL-CONTRA-REEXTRACT, BTN-CAL-PROBE}`.
- Custom guard probe: actual synthetic factory was rejected; a random vector with forged `method=real_probe` provenance passed undetected.
- `git --no-pager diff main...HEAD -- src/cognitive_console/experiments/adjudicate_c2b.py` → **EMPTY**.

## Final verdict

**NEEDS-FIXES.** The default HF runner now wires real derivation functions for PROBE and CONTRA and the synthetic smoke honors the approved 70-combination A-lite grid. However, there are two BLOCKERs before freeze/run: (1) the hard guard is provenance-string-only and can be fooled by a random vector with real-looking labels, exactly the bypass class the prompt asked me to test; (2) CONTRA's E-0006 DEV baseline-score source is an arbitrary external JSONL with no lineage/hash/recompute validation, so I cannot confirm the items/scores are genuine E-0006 unsteered k=5 DEV artifacts rather than a fabricated fixture.

## Ranked findings

### BLOCKER-1 — Hard guard can be bypassed with a random vector carrying real-looking provenance

**Evidence:** The HF path accepts `prederived_directions_by_layer` before it attempts real derivation (`src/cognitive_console/experiments/e0012_harness.py:951-955`) and then calls `assert_real_direction_provenance` (`e0012_harness.py:977-978`). That guard only string-scans `method`, `source`, `source_split`, and `derivation_function` for `synthetic/random` and whitelists `method in {real_probe, real_caa_mean_diff}` (`src/cognitive_console/experiments/e0012_buttons.py:150-164`). My probe constructed a `ButtonDirection` from `np.random.default_rng(...).standard_normal(...)` with `method='real_probe'`, `source_split='TriviaQA-train'`, and `derivation_function='derive_probe_direction_real'`; output: `forged_random_real_label_guard=PASSED_UNDETECTED`.

The actual synthetic factories do set catchable labels (`synthetic_random_probe`, `synthetic_random_contra`) and were rejected (`src/cognitive_console/experiments/e0012_buttons.py:442-470`; test at `tests/test_e0012.py:1968-1989`), but the guard does not bind provenance to the vector, source data, derivation function, or hash.

**Impact:** This would not catch a malicious/accidental random vector wrapped in a `ButtonDirection` with real-looking strings. The requested defense is not hard enough for a fourth freeze-integrity failure class.

**Minimal fix:** On HF path, either remove/forbid `prederived_directions_by_layer` unless loading a signed/canonical provenance artifact, or validate a full derivation manifest: exact source artifact hashes, vector hash, method-specific required keys/counts, and recomputed derivation hash over vector bytes + source bytes + code commit. Tests must assert forged-real-label random vectors raise.

### BLOCKER-2 — CONTRA source data are not proven real E-0006 DEV unsteered k=5 baseline scores

**Evidence:** The runner requires `--e0006-dev-baseline-jsonl` (`scripts/run_e0012_verified_control.py:195-201`, `:488-489`). The loader checks only that the file exists, rows contain `id`, `prompt`, `answer`, and `baseline_score`, ids are unique, and `baseline_score` casts to float (`src/cognitive_console/eval/e0012_triviaqa.py:140-176`). I found no canonical `*e0006*baseline*` artifact in the worktree. There is no validation of E-0006 run id, DEV split membership, unsteered condition, k=5 raw pairs, real-model provenance, row count, source hash, or non-fixture status.

**Impact:** `derive_contra_direction_real` may compute a real activation mean-difference, but over arbitrary user-supplied rows. The persisted provenance then claims `source_split: E-0006 DEV baseline-scored calibration items` (`src/cognitive_console/experiments/e0012_buttons.py:513-524`) even if the JSONL was fabricated or from the wrong split/run.

**Minimal fix:** Generate/load a canonical E-0006 DEV baseline artifact from audited E-0006 raw outputs, persist its artifact hash and source run commit, enforce expected DEV ids/split and k=5 raw-pair lineage, and fail if the JSONL lacks those fields.

### MAJOR-1 — New tests do not prove the CONTRA vector equals the expected mean-difference

**Evidence:** `test_real_contra_direction_uses_caa_mean_difference` calls `derive_contra_direction_real` but asserts only family, unit norm, method, source split, and 13/14 fallback counts (`tests/test_e0012.py:269-276`). It does not compare `bd.direction` to `mean(pos_acts)-mean(neg_acts)`. The implementation itself does call `activation_provider.get_activations` for pos/neg and `mean_difference_vector` (`src/cognitive_console/experiments/e0012_buttons.py:488-493`), and that primitive is the same CAA mean-difference (`src/cognitive_console/steering/extract.py:118-122`), but the regression test would not catch a future sign flip or replacement with another vector.

**Minimal fix:** Add a deterministic fake-provider test that independently computes selected positive/negative activations and asserts the normalized direction equals normalized `mean_difference_vector(pos, neg)`.

### MAJOR-2 — Direction provenance is useful but not cryptographically/checkably tied to actual derivation bytes

**Evidence:** PROBE provenance includes method, `source_item_ids`, split, n_high/n_low, seed, derivation function, code commit, provider model/dtype/device (`src/cognitive_console/experiments/e0012_buttons.py:325-336`). CONTRA provenance includes method, positive/negative ids, split, counts, fallback flag, baseline-score field, code commit, provider metadata (`e0012_buttons.py:513-524`). `direction_provenance.json` is written from these records (`src/cognitive_console/experiments/e0012_harness.py:979-982`). However `_derivation_hash` is only a 16-character prefix over metadata such as shape, ids, scores, and provider info (`e0012_buttons.py:306-315`, `:496-503`); it does not hash the actual vector bytes, activation bytes/cache keys, source JSONL file bytes, or training hyperparameters such as lr/l2/iterations.

**Impact:** The artifact is informative but not sufficient to prove that the persisted vector came from the recorded derivation rather than being swapped after derivation.

**Minimal fix:** Add `vector_sha256`, source artifact SHA-256, activation cache/model revision hashes where possible, and method hyperparameters to provenance; make the guard verify them.

### MINOR-1 — Stale comments still say ≤3 / 105 in the A-lite path

**Evidence:** `Stage0Result.advancing` still says `≤ 3` (`src/cognitive_console/experiments/e0012_harness.py:118-121` from inspected range), and the Stage0 cap comment says `never exceed 105` at the new cap check (`e0012_harness.py:361-363`). Runtime constants are correct at `N_SEARCH_CAP=70` and `MAX_STAGE1_CANDIDATES=2` (`e0012_harness.py:67-73`).

**Minimal fix:** Update comments to avoid future audit confusion.

## Are the directions genuinely real?

### BTN-CAL-CONTRA-REEXTRACT trace

- Approved spec: top-40/bottom-40 E-0006 DEV items by unsteered baseline mean(1-Brier), fallback top-half/bottom-half if fewer than 80, direction `mean(pos activations)-mean(neg activations)` (`prereg...DRAFT.md:124-136`, addendum `:492-496`).
- Runner: HF backend demands `--e0006-dev-baseline-jsonl` and loads rows through `load_e0006_dev_baseline_scores` (`scripts/run_e0012_verified_control.py:195-201`).
- Loader: schema-only validation; it does not prove the rows are genuine E-0006 DEV or real unsteered k=5 scores (`src/cognitive_console/eval/e0012_triviaqa.py:140-176`).
- Selection: deterministic descending `baseline_score`, tie by input index; if `n < 80`, fallback uses `n//2` positives and the remainder negatives (`src/cognitive_console/experiments/e0012_buttons.py:400-438`).
- Real activations/math: `derive_contra_direction_real` captures positive/negative prompts via `activation_provider.get_activations` and calls `mean_difference_vector` (`e0012_buttons.py:488-493`), the C2 CAA primitive `mean(pos)-mean(neg)` (`src/cognitive_console/steering/extract.py:118-122`). `HFActivationProvider.get_activations` performs real model forward passes with `output_hidden_states=True` and last-token pooling (`src/cognitive_console/activations/provider.py:410-468`).

**Conclusion:** The computation is a real CAA mean-difference if and only if the supplied JSONL is genuine. That source authenticity is currently unverified, so CONTRA is **not ready to freeze**.

### BTN-CAL-PROBE trace

- Approved spec: 100 high-confidence + 100 low-confidence rule-generated TriviaQA-train pairs, seed 42, labels 1/0 for verbal confidence only (`prereg...DRAFT.md:102-119`, addendum `:489-491`).
- Runner: HF path loads `HFActivationProvider` and `load_triviaqa_train_for_probe(n=200, seed=42)` before calling the harness (`scripts/run_e0012_verified_control.py:187-194`).
- Loader: uses HuggingFace `mandarjoshi/trivia_qa`, `rc.nocontext`, split `train` (`src/cognitive_console/eval/e0012_triviaqa.py:115-137`). E-0012 validation pool uses split `validation` with offset/seed (`e0012_triviaqa.py:75-112`), so train-vs-validation leakage is structurally avoided. E-0006 is also described as validation/seed=0, so train split should not overlap.
- Pair construction/training: `derive_probe_direction_real` builds §3-B-1 texts, calls `activation_provider.get_activations(texts, layer)`, standardizes activations, and runs 800 iterations of logistic-gradient updates before returning `direction = w / sigma` (`src/cognitive_console/experiments/e0012_buttons.py:271-304`). Provenance records `real_probe`, `TriviaQA-train`, 200 source ids, seed, and label semantics (`e0012_buttons.py:325-336`).

**Conclusion:** PROBE is a genuine activation-based logistic probe in the default HF path, not random. The caveat is guard/provenance robustness, not the derivation function itself.

## Hard-guard efficacy

- **Runs before steering on HF:** `run_e0012_harness` derives/loads directions, then calls `assert_real_direction_provenance` before Stage0 (`src/cognitive_console/experiments/e0012_harness.py:947-982`).
- **Catches actual current synthetic factories:** Synthetic factories record `method=synthetic_random_*`, `source_split=offline_synthetic`, and synthetic derivation function names (`src/cognitive_console/experiments/e0012_buttons.py:442-470`; PROBE analogous at `:239-270`). The test feeds synthetic directions to a fake HF/TextCapable sampler and asserts `RuntimeError` (`tests/test_e0012.py:1968-1989`). My custom probe confirmed `actual_synthetic_guard=RAISED`.
- **Can be fooled:** Because validation is only string/provenance based (`e0012_buttons.py:150-164`), my forged random vector with `method=real_probe` passed. This is BLOCKER-1.

## Scope / drift

Changed files vs `main` are exactly:

- `docs/research/2026-07-29-e0012-verified-control-button/prereg-e0012-verified-control-button-DRAFT.md`
- `scripts/run_e0012_verified_control.py`
- `src/cognitive_console/eval/e0012_triviaqa.py`
- `src/cognitive_console/experiments/e0012_buttons.py`
- `src/cognitive_console/experiments/e0012_harness.py`
- `tests/test_e0012.py`

`src/cognitive_console/experiments/adjudicate_c2b.py` diff is empty. I found no changes to the adjudicator §4 math, kill-rule implementation, pool split constants, §5-B APE implementation, §9.1/§9.2/§9.4 thresholds, or §8 verdict mapping. The changed harness constants match A-lite: `CONSERVATIVE_BUTTON_FAMILIES=(BTN-CAL-PROBE, BTN-CAL-CONTRA-REEXTRACT)`, `N_SEARCH_CAP=70`, `MAX_STAGE1_CANDIDATES=2` (`src/cognitive_console/experiments/e0012_harness.py:67-73`; tests at `tests/test_e0012.py:1074-1082`). No dependency manifest changed; the probe uses in-repo NumPy logistic updates, not scikit-learn.

## Anti-forking paths at 70

Runtime smoke reported `Stage 0: 70/70 combinations evaluated`, `2 advancing to Stage 1`, and the persisted Stage0 table contained 70 rows with families only `BTN-CAL-CONTRA-REEXTRACT` and `BTN-CAL-PROBE`. Code loops all layers × approved families × alphas and stores every candidate before selection (`src/cognitive_console/experiments/e0012_harness.py:348-400`). Selection enforces cutoff sort and at most one per family up to `MAX_STAGE1_CANDIDATES=2` (`e0012_harness.py:130-160`). Bonferroni uses dynamic `M=len(stage0.advancing)` (`e0012_harness.py:1006-1010`).

## Cardinality assessment

The implementation interprets “E-0006 DEV” literally as the actual DEV split, not all 80 calibration items: the loader doc says “E-0006 DEV, not all 80” and fallback is used below 80 (`src/cognitive_console/eval/e0012_triviaqa.py:141-148`). With 27 DEV items, `select_contra_pairs` yields 13 positive and 14 negative rows (`src/cognitive_console/experiments/e0012_buttons.py:423-428`; test at `tests/test_e0012.py:269-276`). This is defensible against the text “E-0006 DEV,” but the prereg also says “Top-40/Bottom-40,” so the cardinality is ambiguous enough that the addendum should explicitly freeze 13/14 for the actual DEV split. Risk: tiny-N CAA direction instability relative to the originally imagined 80-item top/bottom ranking.

## Tests

- Full suite passed: `python -m pytest -q tests/` → 618 passed / 6 skipped.
- New/changed tests cover: real PROBE function with fake activations (`tests/test_e0012.py:261-267`), CONTRA function/fallback counts (`tests/test_e0012.py:269-276`), provenance guard direct rejection (`tests/test_e0012.py:278-288`), N cap and Stage1 cap (`tests/test_e0012.py:1074-1082`), anti-forking table presence (`tests/test_e0012.py:1196-1211`), and HF synthetic-direction rejection (`tests/test_e0012.py:1968-1989`).
- Test gap: CONTRA test does not independently assert vector equality to CAA mean-difference (MAJOR-1), and no test covers forged real-looking provenance (BLOCKER-1).
