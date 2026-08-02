# E-0012 real-direction fixes audit

Auditor: independent hostile code auditor; did not write the implementation.  
Checkout: `feature/e0012-real-directions` at `d92a299`.  
Scope: verify fixes since prior audit `a1bb472` / compare `main..d92a299`; report only.

## Commands actually run

- `git -C "...\.worktrees\e0012-realdir" status --short --branch`; `git --no-pager log --oneline --decorate -5`; `git diff --name-only main..d92a299`; `git diff --name-only a1bb472..d92a299`.
- Read prior audit `reviews/2026-08-01-e0012-realdir-code-audit/audit-report.md`, prereg §3-B-2 and the D-0068 amendment (`docs/research/2026-07-29-e0012-verified-control-button/prereg-e0012-verified-control-button-DRAFT.md:121-136,482-496`), and D-0067 context (`docs/ledgers/decision-log.md:8-33`). D-0068 is missing from this branch's decision log; see MAJOR-2.
- Inspected `scripts/build_e0006_uncertainty_baseline.py`, `scripts/run_e0012_verified_control.py`, `src/cognitive_console/eval/e0012_triviaqa.py`, `src/cognitive_console/experiments/e0012_buttons.py`, `src/cognitive_console/experiments/e0012_harness.py`, `tests/test_e0012.py`, `scripts/run_c2b_adjudication.py`, and `src/cognitive_console/eval/c2b_tasks.py`.
- `python -m pytest -q tests/` → **PASS**, 619 passed / 6 skipped / 1 warning.
- `python scripts\run_e0012_verified_control.py --backend synthetic --output-dir results\audit-e0012-fixes-smoke --n-items 12 --seed 42` → **PASS**, Stage0 `70/70`, Stage1 `2`, families `{BTN-CAL-CONTRA-REEXTRACT, BTN-CAL-PROBE}`.
- Custom forged-vector probe: random `ButtonDirection(method="real_probe")` passed directly to the provenance string guard, but **raised on the hf/TextCapable harness path** with `RuntimeError: prederived_directions_by_layer is forbidden...`.
- Custom bad-artifact probes: arbitrary JSONL without manifest, tampered SHA manifest, and fixture-loader manifest all **raised**.
- `git --no-pager diff main..d92a299 -- src/cognitive_console/experiments/adjudicate_c2b.py` → **EMPTY**.

## Final verdict

**NEEDS-FIXES.** The two prior BLOCKERs and two prior MAJORs are substantively closed in code: hf runs now forbid prederived direction injection, direction provenance includes vector/source hashes and hyperparameters, the E-0006 artifact path is lineage-validated, CONTRA now uses all-80 top-40/bottom-40, and the CONTRA equality test now catches sign/replacement errors.

However, I found two new merge/freeze issues: the builder defaults do not match the frozen E-0006/arm_full generation identity, and this branch deletes D-0068 from `decision-log.md` relative to `main`. Fix these before freeze/run.

## Ranked findings

### MAJOR-1 — Baseline builder defaults can silently generate a non-E-0006-equivalent baseline

**Evidence:** The canonical baseline builder samples the correct source items and records lineage, but its CLI defaults are `--max-new-tokens 256` and `--seed 42` (`scripts/build_e0006_uncertainty_baseline.py:172,185`). The frozen C2b/E-0006 runner treats generation identity as lineage-critical ("Changing max_new_tokens, temperature, seed, model, or the item set invalidates..." at `scripts/run_c2b_adjudication.py:108-125`) and defaults to `--max-new-tokens 64`, `--temperature 0.7`, `--seed 20260723` (`scripts/run_c2b_adjudication.py:1018-1030`). D-0068 asks for the E-0006 uncertainty baseline lineage; running the builder with its defaults would produce all-80 unsteered scores under a different generation length and RNG base seed than E-0006 arm_full.

**Impact:** CONTRA pair ranking can be real and lineage-stamped but still not be the E-0006-equivalent baseline the protocol intends. Because the manifest only records the chosen values and the loader does not enforce E-0006 run identity, this can silently pass into the hf run.

**Minimum fix:** Change builder defaults or the A800 run command/checklist to the frozen E-0006 identity (`max_new_tokens=64`, `temperature=0.7`, `seed=20260723`, model Qwen2.5-7B, expected dtype/device), and make the loader reject manifest values that do not match the frozen builder contract unless an explicit protocol amendment says otherwise.

### MAJOR-2 — Branch deletes D-0068 owner approval from the decision log relative to `main`

**Evidence:** `git diff main..d92a299 -- docs/ledgers/decision-log.md` deletes the entire `## 2026-08-01 · D-0068 · Owner approved A-lite...` entry at the top of `docs/ledgers/decision-log.md`; `rg D-0068 docs/ledgers/decision-log.md` finds no current branch entry. The prereg addendum still cites D-0068 at `docs/research/2026-07-29-e0012-verified-control-button/prereg-e0012-verified-control-button-DRAFT.md:482`.

**Impact:** This is governance drift: merging the branch would erase the owner approval ledger that authorizes the scope reduction being implemented. The prereg and code would point at a decision-log entry that no longer exists.

**Minimum fix:** Restore the D-0068 decision-log entry from `main` before merge.

### MINOR-1 — Loader validates lineage shape and item ids, but not raw-pair completeness

**Evidence:** `load_e0006_dev_baseline_scores(..., validate_item_source=True)` requires JSONL+manifest, correct schema, condition, k, synthetic_proxy, item_count, artifact SHA, source loader name, and exact frozen E-0006 item ids (`src/cognitive_console/eval/e0012_triviaqa.py:294-367`). Per-row required fields are only `item_index`, `id`, `prompt`, `answer`, and `baseline_score` (`e0012_triviaqa.py:335-351`); it does not require each row to contain 5 raw pairs or recompute `baseline_score` from them.

**Impact:** The loader rejects casual arbitrary/tampered artifacts, but a self-consistent manifest with correct ids and fake scores could pass if produced outside the builder. This is acceptable only if the Manager treats the builder command log + manifest as the trusted lineage artifact.

**Minimum fix:** Preferably require `raw_pairs` length 5, all `synthetic_proxy=false`, and `baseline_score == mean(raw_pairs.one_minus_brier)` in the loader. At minimum, include this in the A800 checklist.

## Prior finding closure verification

### BLOCKER-1 FIX — Guard is no longer bypassable on hf path

**Status:** **CLOSED for the hf runner path.**

- The hf/TextCapable branch now raises immediately if `prederived_directions_by_layer` is supplied (`src/cognitive_console/experiments/e0012_harness.py:934-955`), before Stage0 or steering can occur.
- Real hf directions are derived via `all_real_directions_for_layer(...)` from activation provider, TriviaQA-train probe items, and validated E-0006 all-80 baseline items (`e0012_harness.py:960-976`), then checked and persisted (`e0012_harness.py:984-989`; runner passes `direction_provenance_path` at `scripts/run_e0012_verified_control.py:289`).
- Provenance records include `vector_sha256` over normalized float32 vector bytes (`src/cognitive_console/experiments/e0012_buttons.py:91,138,162`), require `source_artifact_sha256` and `hyperparameters` (`e0012_buttons.py:182-186`), compute PROBE source hash from actual pair texts/labels/source ids (`e0012_buttons.py:261-276,344-384`), and compute CONTRA source hash from the loaded E-0006 artifact (`e0012_buttons.py:543-581`).
- My forged-random-vector reproduction now closes the prior bypass on hf path:
  - `forged_random_real_label_hf_path=RAISED`
  - `RuntimeError: REAL-NOT-SMOKE hard-fail: prederived_directions_by_layer is forbidden...`
- Caveat: the direct string provenance guard still accepts a forged record with plausible `method`, source hash, and hyperparameters (`direct_provenance_guard_on_forged_record=ACCEPTED` in my probe). The important closure is that the hf harness no longer allows prederived injection, so that direct guard is no longer the sole defense.

### BLOCKER-2 FIX — E-0006 baseline lineage is no longer arbitrary JSONL

**Status:** **CLOSED with MAJOR-1 caveat on generation defaults.**

- The builder uses the frozen C2b uncertainty loader with `use_fixture=False`: `load_axis_items("uncertainty_awareness", use_fixture=False, n_items=None)` (`scripts/build_e0006_uncertainty_baseline.py:35,51-63`). That loader routes through `c2b_tasks.load_c2b_task(... use_fixture=False)` (`scripts/run_c2b_adjudication.py:647-655`), which calls the real loader instead of fixture (`src/cognitive_console/eval/c2b_tasks.py:124-153`) and is capped to E-0006's 80 uncertainty items by `N_ITEMS_BY_AXIS["uncertainty_awareness"]=80` (`src/cognitive_console/experiments/adjudicate_c2b.py:51-54`).
- The builder scores unsteered empty-prompt samples: `instruction=""`, `alpha=0.0`, `k=adj.K_SAMPLES` (`scripts/build_e0006_uncertainty_baseline.py:90-96`); per raw pair it stores `synthetic_proxy: False` (`build_e0006_uncertainty_baseline.py:103-115`), and manifest lineage records `condition=unsteered_empty_prompt`, `k=5`, `synthetic_proxy=false`, model/dtype/device/code commit, item ids, and artifact SHA (`build_e0006_uncertainty_baseline.py:126-158`).
- The hf runner defaults to the canonical JSONL path and calls `load_e0006_dev_baseline_scores(..., validate_item_source=True)` (`scripts/run_e0012_verified_control.py:195-199`), so arbitrary JSON/legacy artifact paths are rejected for hf.
- Loader validation rejects missing/tampered/fixture artifacts:
  - My arbitrary JSONL probe: `bad_artifact_missing_manifest=RAISED` / `FileNotFoundError: E-0006 baseline sidecar manifest not found...`
  - My tampered SHA probe: `bad_artifact_tampered_sha=RAISED` / `ValueError: E-0006 baseline artifact sha mismatch...`
  - My fixture-loader manifest probe: `fixture_loader_artifact=RAISED` / `ValueError: source_item_loader must name the frozen C2b loader...`

### CARDINALITY FIX — all-80 top-40/bottom-40 is implemented and prereg-amended

**Status:** **CLOSED.**

- Prereg amendment states full all-80 ranking, top-40 positive and bottom-40 negative, ties by item index (`prereg-e0012-verified-control-button-DRAFT.md:482-494`).
- Code requires exactly `40+40=80` items (`src/cognitive_console/experiments/e0012_buttons.py:67-68,451-477`), sorts by descending `baseline_score` and ascending input/item index (`e0012_buttons.py:483`), then takes top-40 and bottom-40 (`e0012_buttons.py:485-486`). The old 13/14 fallback is gone.
- Tests assert rejection below 80 and tie behavior (`tests/test_e0012.py:384-399`).

### MAJOR-1 FIX — CONTRA vector equality test now catches sign/replacement

**Status:** **CLOSED.**

- Implementation computes `direction = mean_difference_vector(pos_acts, neg_acts)` after independently collecting positive and negative activations (`src/cognitive_console/experiments/e0012_buttons.py:535-540`).
- New test independently selects pairs, recomputes positive/negative activations, normalizes `mean_difference_vector`, and asserts equality to `derive_contra_direction_real` (`tests/test_e0012.py:334-343`).

### MAJOR-2 FIX — provenance detects post-derivation vector/source swaps better than before

**Status:** **CLOSED for required fields; see MINOR-1 for stronger artifact recomputation.**

- `ButtonDirection.__post_init__` hashes the actual normalized direction bytes into `vector_sha256` (`src/cognitive_console/experiments/e0012_buttons.py:85-92,138-140`), and persisted records also set it from the actual vector (`e0012_buttons.py:154-164`).
- PROBE `source_artifact_sha256` is computed from the actual pair texts, labels, and selected source ids, with hyperparameters recorded (`e0012_buttons.py:261-276,344-384`).
- CONTRA `source_artifact_sha256` comes from the validated E-0006 source artifact attached to loaded rows, and selection hyperparameters are recorded (`e0012_buttons.py:543-581`).
- hf provenance guard requires `vector_sha256`, `source_artifact_sha256`, and `hyperparameters` (`e0012_buttons.py:182-186`), and runner writes `direction_provenance.json` (`scripts/run_e0012_verified_control.py:289,415`).

## No-new-drift / scope check

- `adjudicate_c2b.py` diff is empty.
- A-lite constants remain as amended: `CONSERVATIVE_BUTTON_FAMILIES=(BTN-CAL-PROBE, BTN-CAL-CONTRA-REEXTRACT)` (`src/cognitive_console/experiments/e0012_buttons.py:55-56`), `N_SEARCH_CAP=70` and `MAX_STAGE1_CANDIDATES=2` (`src/cognitive_console/experiments/e0012_harness.py:70-73`).
- Synthetic smoke confirmed `Stage 0: 70/70 combinations evaluated` and `2 advancing to Stage 1`.
- I found no code diff to the adjudicator math, kill-rule implementation, APE generation/evaluation, §9 guard thresholds, pool seed/offset/split, or verdict mapping. The main drift issue is documentary/governance: D-0068 deletion from `decision-log.md`.

## A800 run-time checklist for Manager

Before running the main hf E-0012 job:

1. Restore D-0068 in `docs/ledgers/decision-log.md`.
2. Build the baseline artifact with frozen E-0006-equivalent generation identity, or explicitly amend the protocol if different: model `Qwen/Qwen2.5-7B-Instruct`, unsteered `alpha=0`, empty instruction, `k=5`, `max_new_tokens=64`, `temperature=0.7`, seed `20260723`, real CUDA dtype/device recorded.
3. Verify the builder manifest: schema `e0006-uncertainty-baseline-v1`, `source_item_loader` names `scripts.run_c2b_adjudication.load_axis_items(... use_fixture=False ...)`, `condition=unsteered_empty_prompt`, `synthetic_proxy=false`, `item_count=80`, `artifact_sha256` matches the JSONL, and `item_ids` exactly match the frozen E-0006 uncertainty pool.
4. Verify every JSONL row has `raw_pairs` length 5, all `synthetic_proxy=false`, and `baseline_score == mean(raw_pairs.one_minus_brier)`; record parse/fallback anomalies if confidence extraction fails.
5. Run main hf with `--e0006-dev-baseline-jsonl data\e0006_uncertainty_baseline\e0006_uncertainty_baseline.jsonl`; confirm it writes `direction_provenance.json`.
6. Inspect `direction_provenance.json`: exactly 10 records (5 layers × 2 families), methods `{real_probe, real_caa_mean_diff}`, all have `vector_sha256`, `source_artifact_sha256`, and hyperparameters; no `synthetic`/`random` strings.
7. Confirm Stage0 reports `70/70`, Stage1 `≤2`, families only PROBE/CONTRA, and `adjudicate_c2b.py` remains unchanged at run commit.
