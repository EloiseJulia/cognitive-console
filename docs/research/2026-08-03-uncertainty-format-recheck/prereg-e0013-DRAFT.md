# E-0013 UNCERTAINTY FORMAT-COMPLIANCE RECHECK — DRAFT

**Status:** draft mini-prereg; `valid_for_paper=false` until independent audit and Manager sign-off.  
**Run commit:** `<MANAGER_TO_FILL_RUN_COMMIT>`  
**Scope:** exploratory robustness check only. E-0013 does **not** overwrite, refreeze, or re-judge the frozen E-0005/E-0006 C2b protocol/verdict.

## Purpose

The C2b uncertainty axis uses frozen per-item `1 - Brier`, with missing confidence parsed as `None` and imputed to `conf=0.5`. Reviewers identified a format-vs-calibration confound: if steering causes generations to drop the required `Confidence:` format, the observed uncertainty harm may partly reflect format-compliance failure plus imputation rather than genuine calibration degradation. E-0013 reruns the uncertainty axis with raw-text capture to decompose this confound.

## Frozen cells and reused configs

Run exactly the four E-0006 uncertainty cells, reusing each cell's frozen DEV-selected configuration from `results/arm_full/cell_{caa,iti}__{qwen2.5-7b,llama3-8b}/c2b_adjudication_results.json`:

- CAA × Qwen2.5-7B
- CAA × Llama-3-8B
- ITI × Qwen2.5-7B
- ITI × Llama-3-8B

For each cell, reuse the frozen uncertainty-axis layer, `frozen_alpha`, `best_prompt_id`, and `best_prompt_text`. Re-derive the real CAA/ITI direction through the same C2 path and validate ITI layer/sigma against the frozen artifact. Do not re-select prompts, alpha, or layer.

## Generation identity

Use the E-0006 generation identity: `k=5`, `max_new_tokens=64`, `temperature=0.7`, `seed=20260723`, real uncertainty items (`use_fixture=false`), and synthetic_proxy=false. Generate TEST and DEV where feasible; the headline reanalysis is TEST-only.

## Pre-stated readouts

For each cell and condition (`steer`, `prompt`, `baseline`), persist per-sample raw text, item id, split, parsed confidence (`None` means format dropped), correctness, frozen-imputed per-item `1 - Brier`, and `format_compliant`.

Report:

1. Format-compliance rate by cell and condition; primary comparison is steer vs prompt.
2. Frozen uncertainty delta (steer − prompt) as-run with the original `conf=0.5` imputation.
3. Steer − prompt delta restricted to paired item/sample rows where both generations are format-compliant, with paired item-cluster bootstrap 95% CI.
4. Imputation share and sensitivity bounds/drop-imputed variant.

Interpretation question: does the uncertainty harm survive on format-compliant generations, and is steering materially less format-compliant than the prompt arm?
