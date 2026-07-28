# Multi-seed C2 Robustness Aggregation

- generated_at: `2026-07-28T17:19:39.991807+00:00`
- n_seeds: 5
- arm_verdict_counts: {'NON_TRANSFER_GENERALIZED': 5}
- n_seeds NON_TRANSFER_GENERALIZED: **5**

## True-pass surfacing (unconditional guard — prereg §4c)

- `any_true_pass: []` — no true pass detected in any seed×cell×axis.

## Caveat-drop evaluation
- Caveat status ladder: KILL_HARNESS if seed=20260723 fails E-0006 numeric repro check (tol=1e-06) or arm_verdict != NON_TRANSFER_GENERALIZED; DROP_SINGLE_SEED_CAVEAT iff n_seeds == N_FROZEN=5 AND all seeds are NON_TRANSFER_GENERALIZED, all 4 cells have uncertainty_awareness CI_hi<0 in all seeds, and no seed×cell×axis PASS; INSUFFICIENT_SEEDS iff strict-all conditions hold but n_seeds < N_FROZEN=5 (pending remaining seeds — cannot DROP until full seed set present); SEED_MOSTLY_ROBUST iff >=4/5 seeds are NON_TRANSFER_GENERALIZED, all 4 cells have uncertainty_awareness CI_hi<0 in >=3/5 seeds, and no strong-positive flip; else SEED_SENSITIVE.
- strict all NON_TRANSFER_GENERALIZED: **True**
- non_transfer in ≥4/5 seeds: **True**
- uncertainty CI_hi<0 counts per cell: **{'caa__qwen2.5-7b': 5, 'caa__llama3-8b': 5, 'iti__qwen2.5-7b': 5, 'iti__llama3-8b': 5}**
- uncertainty CI_hi<0 all cells/all seeds: **True**
- uncertainty CI_hi<0 all cells/≥3 seeds: **True**
- any strong-positive flip: **False**
- **Outcome: DROP_SINGLE_SEED_CAVEAT**

## Per-seed arm verdicts

| seed | arm_verdict | zero_pass_cells |
|---|---|---|
| 20260723 | NON_TRANSFER_GENERALIZED | 4 |
| 20260724 | NON_TRANSFER_GENERALIZED | 4 |
| 20260725 | NON_TRANSFER_GENERALIZED | 4 |
| 20260726 | NON_TRANSFER_GENERALIZED | 4 |
| 20260727 | NON_TRANSFER_GENERALIZED | 4 |

## Per-cell per-axis mean(d) across seeds

### Cell: `caa__qwen2.5-7b`

| axis | seeds_with_data | n_pass | mean_diff_values | mean_across_seeds | all_CI_hi<0 |
|---|---|---|---|---|---|
| deliberation | 5 | 0 | [0.015, 0.045, 0.000, 0.025, 0.010] | 0.019 | False |
| skepticism | 5 | 0 | [-0.080, -0.025, -0.065, 0.040, -0.060] | -0.038 | False |
| uncertainty_awareness | 5 | 0 | [-0.228, -0.234, -0.214, -0.180, -0.268] | -0.225 | True |

### Cell: `caa__llama3-8b`

| axis | seeds_with_data | n_pass | mean_diff_values | mean_across_seeds | all_CI_hi<0 |
|---|---|---|---|---|---|
| deliberation | 5 | 0 | [0.025, -0.005, 0.015, 0.025, -0.005] | 0.011 | False |
| skepticism | 5 | 0 | [0.000, 0.030, 0.000, -0.090, -0.125] | -0.037 | False |
| uncertainty_awareness | 5 | 0 | [-0.072, -0.044, -0.196, -0.080, -0.072] | -0.093 | True |

### Cell: `iti__qwen2.5-7b`

| axis | seeds_with_data | n_pass | mean_diff_values | mean_across_seeds | all_CI_hi<0 |
|---|---|---|---|---|---|
| deliberation | 5 | 0 | [0.020, 0.040, -0.030, -0.010, -0.020] | -0.000 | False |
| skepticism | 5 | 0 | [-0.100, -0.025, -0.095, 0.030, -0.075] | -0.053 | False |
| uncertainty_awareness | 5 | 0 | [-0.103, -0.264, -0.181, -0.161, -0.258] | -0.193 | True |

### Cell: `iti__llama3-8b`

| axis | seeds_with_data | n_pass | mean_diff_values | mean_across_seeds | all_CI_hi<0 |
|---|---|---|---|---|---|
| deliberation | 5 | 0 | [0.015, 0.010, -0.025, 0.020, 0.005] | 0.005 | False |
| skepticism | 5 | 0 | [0.000, 0.030, 0.015, -0.085, -0.135] | -0.035 | False |
| uncertainty_awareness | 5 | 0 | [-0.084, -0.062, -0.051, -0.137, -0.068] | -0.080 | True |

