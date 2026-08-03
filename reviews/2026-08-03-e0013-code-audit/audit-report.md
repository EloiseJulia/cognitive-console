# E-0013 uncertainty format recheck — hostile code audit

**Scope audited:** branch `feature/uncertainty-format-recheck` / HEAD `139f904` vs `main`; E-0013 prereg, runner, tests, frozen C2 scorer/imputation path, and C2 direction/data wiring.

**Final verdict: NEEDS-FIXES.** The HF path is substantially additive and does not repeat the E-0012 random-direction or fixture-data bug by default, but one protocol-identity guard is incomplete: model identity can be overridden without a hard failure.

## Ranked findings

### BLOCKER-1 — HF run can silently use a non-E-0006 model
- **Where:** `scripts/run_uncertainty_format_recheck.py:489-493`, `scripts/run_uncertainty_format_recheck.py:554-556`, `scripts/run_uncertainty_format_recheck.py:510-517`
- **Evidence:** the parser exposes `--qwen-model` / `--llama-model`; `main()` sets `model_id = override_model or cfg.model_id`; `_validate_generation_identity()` only checks max_new_tokens/temperature/seed, not model identity.
- **Impact:** E-0013 is defined as reusing the exact E-0006 generation identity, including model per cell. A wrong model path/id would still run and only be recorded in the manifest, not rejected.
- **Minimal fix:** remove model overrides for paper runs, or require an explicit frozen-model alias map plus a hard check that the resolved model identity matches the frozen artifact.

### MAJOR-1 — Synthetic smoke is labelled `synthetic_proxy=false`
- **Where:** `scripts/run_uncertainty_format_recheck.py:258-262`, `scripts/run_uncertainty_format_recheck.py:155-166`, `scripts/run_uncertainty_format_recheck.py:593-614`; test pins this at `tests/test_uncertainty_format_recheck.py:66-69`.
- **Evidence:** synthetic backend uses a placeholder all-ones direction, but per-sample and manifest `synthetic_proxy` are always false. The committed synthetic smoke manifest also has `backend: synthetic` but `synthetic_proxy: false`.
- **Impact:** backend metadata prevents total confusion, but the explicit proxy flag is false for proxy data. Given E-0012 failed from fake-data/fake-direction leakage, this should be unambiguous.
- **Minimal fix:** set `synthetic_proxy=true` for synthetic records/manifests and assert `synthetic_proxy=false` only when `backend=hf`.

## Real directions & real data: no E-0012 repeat on the HF path

- **CAA direction:** `generate_cell_samples()` calls `_derive_hf_direction()` for non-synthetic backends (`scripts/run_uncertainty_format_recheck.py:257-262`). CAA then calls `p0._extract_direction(provider, AXIS, cfg.layer, n_extraction, seed)` (`scripts/run_uncertainty_format_recheck.py:193-206`), which loads C1 contrast pairs and computes mean-difference activations through `HFActivationProvider` (`scripts/run_gpu_phase0.py:118-128`). No random/synthetic factory is in the HF path.
- **ITI direction:** the HF path reloads C1 axis pairs, builds the extraction split, calls `extract_iti()` on real activations, and hard-fails if rederived ITI layer or sigma differs from the frozen artifact (`scripts/run_uncertainty_format_recheck.py:209-239`). This matches the C2 derivation structure in `scripts/run_c2b_adjudication.py:734-815`.
- **Real uncertainty data:** `main()` sets `use_fixture = args.backend == "synthetic"`; therefore HF uses `False` (`scripts/run_uncertainty_format_recheck.py:544-545`). `load_uncertainty_items(False, ...)` calls `c2b_tasks.load_uncertainty_set()` (`scripts/run_uncertainty_format_recheck.py:135-143`), which loads TriviaQA `rc.nocontext` (`src/cognitive_console/eval/c2b_tasks.py:281-296`). HF also forbids `--n-items` (`scripts/run_uncertainty_format_recheck.py:524-526`).

## Other audit results

- **Frozen config reuse:** each cell loads `results/arm_full/cell_<method>__<model>/c2b_adjudication_results.json`, extracts the uncertainty row, and reuses `layer`, `frozen_alpha`, `best_prompt_id`, and `best_prompt_text` without prompt/alpha reselection (`scripts/run_uncertainty_format_recheck.py:74-130`, `scripts/run_uncertainty_format_recheck.py:168-177`). Frozen artifacts are HF and `use_fixture=false`.
- **Generation identity:** max_new_tokens=64, temperature=0.7, seed=20260723, and k=5 are guarded (`scripts/run_uncertainty_format_recheck.py:42-45`, `scripts/run_uncertainty_format_recheck.py:510-526`); model identity is not guarded (BLOCKER-1).
- **Format-compliance logic:** `parse_confidence(text) is None` sets `format_compliant=false`, imputes confidence 0.5, and computes the frozen `1-Brier` (`scripts/run_uncertainty_format_recheck.py:153-166`). This mirrors frozen adjudicator imputation at `src/cognitive_console/experiments/adjudicate_c2b.py:471-476`.
- **Compliant-only recompute:** paired item/sample rows require both prompt and steer confidence parses, then item means feed `adjudicate_c2b.cluster_bootstrap_ci(..., cluster=True)` (`scripts/run_uncertainty_format_recheck.py:357-388`, `scripts/run_uncertainty_format_recheck.py:420-454`). Rates are reported for steer/prompt/baseline (`scripts/run_uncertainty_format_recheck.py:424-438`).
- **No drift:** `git diff main..139f904 -- src/` is empty; frozen scorer/adjudicator math is unchanged. `valid_for_paper` is hardcoded false in the run manifest (`scripts/run_uncertainty_format_recheck.py:593-594`).
- **Raw text:** per-sample raw text and SHA are persisted (`scripts/run_uncertainty_format_recheck.py:304-327`).

## Tests run

- `python -m pytest -q tests\test_uncertainty_format_recheck.py` → **3 passed**.
- `python -m pytest -q` → **633 passed, 6 skipped** (639 collected), one deprecation warning in `tests/test_posthoc_equivalence.py`.
- Synthetic smoke: `python scripts\run_uncertainty_format_recheck.py --backend synthetic --cells caa__qwen2.5-7b caa__llama3-8b iti__qwen2.5-7b iti__llama3-8b --splits test --n-items 4 --bootstrap-b 200 --allow-underpowered --out-dir results\E-0013-uncertainty-recheck\audit_synthetic_smoke_all4` → completed; scratch output removed after inspection.

The tests do assert the confidence-parse/noncompliance/imputation path and that compliant-only deltas exclude unpaired noncompliant samples (`tests/test_uncertainty_format_recheck.py:8-42`).

## A800 run-time checklist

1. Apply BLOCKER-1 fix before paper run; do not use model overrides unless identity is hard-validated.
2. Run HF backend only: `--backend hf`; verify manifest `backend=hf`, all four frozen cells present, `valid_for_paper=false`, `k_samples=5`, `max_new_tokens=64`, `temperature=0.7`, `seed=20260723`.
3. Verify each cell manifest points to `results/arm_full/cell_*` and frozen `layer`, `frozen_alpha`, `best_prompt_id`, and `best_prompt_text` match E-0006.
4. Verify HF item count is the frozen 80 uncertainty items before split; no `--n-items`; no fixture files.
5. Verify direction metadata is `caa_mean_difference_at_frozen_layer` or `iti_probe_direction_rederived_by_frozen_c2_path`; no `synthetic_offline_placeholder`.
6. Verify `samples.jsonl` contains raw_text, raw_text_sha256, parse_confidence, format_compliant, imputed_confidence, item_is_correct, and per_item_1minus_brier for every condition/sample.
7. Inspect reanalysis: per-cell steer/prompt/baseline compliance rates, as-run imputed delta, compliant-only delta/CI, and compliant pair counts.
8. Keep E-0013 as robustness evidence only until post-run results audit closes.

## UNVERIFIED

I did not execute the HF/A800 path or load the actual models/datasets in this Windows audit environment. Static trace shows the intended HF path uses real directions and real TriviaQA data, subject to the model-identity blocker above.
