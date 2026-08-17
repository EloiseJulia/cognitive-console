# Phi-3 Official DEV Length-Rerun Grid Report

Derived from `official_latent_positive_control_dev_results.json`; no TEST item generated/scored.

- experiment_id: `E-0017e-phi3-official-stolfo-positive-control-stage1-dev-length-rerun`
- model: `phi-3` @ `f39ac1d28e925b323eae81227eaba4464caced4e`
- official repo: `9dac937ef6fc3e483b1efc13863deeb03ec38dbe`
- official generation source: `config/keywords/keyword_evaluation.yaml` sets `max_generation_length: 1024`; `keywords/evaluate.py` passes it to direct and hooked generation.
- completed cap: `256` new tokens (1024 infeasible; 256 owner-allowed fallback).
- DEV n: `40`; extraction rows: `820`
- baseline compliance: `0.275`; prompt compliance: `0.875`
- baseline truncation: `0.700`; mean tokens `208.50`
- prompt truncation: `0.675`; mean tokens `202.57`
- token normalization: `not_applicable: official keyword checker over decoded text`
- format compliance: `not_applicable: official IFEval keywords:existence binary verifier`

| layer | weight | steer compliance | steer-baseline Δ [CI] | steer-prompt Δ [CI] | coherence | truncation | mean gen tok | format |
|---:|---:|---:|---:|---:|---|---:|---:|---|
| 24 | 40 | 0.350 | 0.075 [-0.050, 0.225] | -0.525 [-0.700, -0.325] | PASS (g=0.039 ≤ 0.063) | 0.700 | 204.47 | n/a keyword verifier |
| 24 | 60 | 0.325 | 0.050 [-0.050, 0.175] | -0.550 [-0.725, -0.350] | PASS (g=0.033 ≤ 0.063) | 0.625 | 199.80 | n/a keyword verifier |
| 24 | 80 | 0.350 | 0.075 [-0.050, 0.225] | -0.525 [-0.700, -0.350] | PASS (g=0.031 ≤ 0.063) | 0.700 | 205.28 | n/a keyword verifier |
| 24 | 100 | 0.425 | 0.150 [0.000, 0.325] | -0.450 [-0.625, -0.275] | PASS (g=0.035 ≤ 0.063) | 0.675 | 205.62 | n/a keyword verifier |
| 26 | 40 | 0.350 | 0.075 [-0.050, 0.225] | -0.525 [-0.700, -0.325] | PASS (g=0.038 ≤ 0.063) | 0.750 | 207.75 | n/a keyword verifier |
| 26 | 60 | 0.325 | 0.050 [-0.075, 0.175] | -0.550 [-0.750, -0.350] | PASS (g=0.030 ≤ 0.063) | 0.750 | 207.75 | n/a keyword verifier |
| 26 | 80 | 0.400 | 0.125 [-0.025, 0.275] | -0.475 [-0.675, -0.275] | PASS (g=0.034 ≤ 0.063) | 0.750 | 208.12 | n/a keyword verifier |
| 26 | 100 | 0.575 | 0.300 [0.125, 0.475] | -0.300 [-0.475, -0.125] | PASS (g=0.040 ≤ 0.063) | 0.725 | 204.62 | n/a keyword verifier |
| 28 | 40 | 0.300 | 0.025 [-0.075, 0.125] | -0.575 [-0.750, -0.375] | PASS (g=0.037 ≤ 0.063) | 0.775 | 207.75 | n/a keyword verifier |
| 28 | 60 | 0.475 | 0.200 [0.025, 0.375] | -0.400 [-0.575, -0.225] | PASS (g=0.041 ≤ 0.063) | 0.675 | 206.70 | n/a keyword verifier |
| 28 | 80 | 0.650 | 0.375 [0.175, 0.575] | -0.225 [-0.400, -0.050] | PASS (g=0.034 ≤ 0.063) | 0.725 | 207.95 | n/a keyword verifier |
| 28 | 100 | 0.675 | 0.400 [0.200, 0.600] | -0.200 [-0.375, -0.025] | FAIL (g=0.064 ≤ 0.063) | 0.700 | 205.30 | n/a keyword verifier |

## Selected cell and old/new comparison

Selected by frozen DEV rule: layer `28`, weight `80.0`; steer `0.650`; primary Δ `0.375` CI `[0.175, 0.575]`; coherence `True`; truncation `0.725`; mean tokens `207.95`.
Old 32-token DEV: baseline `0.150`, prompt `0.450`, selected steer `0.250`, Δ `0.100` CI `[0.000, 0.225]`.
New 256-token DEV: baseline `0.275`, prompt `0.875`, selected steer `0.650`, Δ `0.375` CI `[0.175, 0.575]`.

Interpretation: length repair strengthened the positive-control signal and cleared zero on DEV, but cap-hit rates remain high at 256 tokens, so any Stage-2 plan should surface this runtime/length caveat explicitly.
