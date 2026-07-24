# C2b QUALIFIED Adjudication — FROZEN instrument (prereg §4/§5)

- verdict: **KILL_PLAN_D**
- model: `/root/autodl-tmp/models/Qwen2.5-7B-Instruct`   backend: `hf`   valid_for_paper: **False**
- run_type: **exploratory**   bootstrap_B: 10000   CI level: 0.98333 (Bonferroni 1−0.05/3)
- δ = 0.05   α grid: [2.0, 4.0, 6.0, 8.0, 12.0, 16.0, 24.0]

| axis | layer | frozen α | best prompt | n_dev | n_test | mean(d) | CI | coherence | PASS |
|---|---|---|---|---|---|---|---|---|---|
| deliberation | 20 | 4.0 | delib-strong-09 | 20 | 40 | +0.020 | [+0.000, +0.055] | ok | no |
| skepticism | 19 | 2.0 | skep-strong-06 | 20 | 40 | -0.100 | [-0.270, +0.060] | ok | no |
| uncertainty_awareness | 17 | 12.0 | unc-strong-01 | 27 | 53 | -0.103 | [-0.136, -0.069] | ok | no |

- axes passing (Bonferroni): **0/3** -> **KILL_PLAN_D**

## Conflict cells (SECONDARY / descriptive only — NOT part of the verdict)

| axis | opposite α | mean conflict outcome | mean prompt-pole | latent drags down? |
|---|---|---|---|---|
| deliberation | -4.0 | 0.035 | 0.020 | False |
| skepticism | -2.0 | 0.800 | 0.775 | False |
| uncertainty_awareness | -12.0 | 0.312 | 0.848 | True |
