# C2b QUALIFIED Adjudication — FROZEN instrument (prereg §4/§5)

- verdict: **KILL_PLAN_D**
- model: `/root/autodl-tmp/models/Qwen2.5-7B-Instruct`   backend: `hf`   valid_for_paper: **False**
- run_type: **exploratory**   bootstrap_B: 10000   CI level: 0.98333 (Bonferroni 1−0.05/3)
- δ = 0.05   α grid: [2.0, 4.0, 6.0, 8.0, 12.0, 16.0, 24.0]

| axis | layer | frozen α | best prompt | n_dev | n_test | mean(d) | CI | coherence | PASS |
|---|---|---|---|---|---|---|---|---|---|
| deliberation | 20 | 2.0 | delib-strong-09 | 20 | 40 | +0.015 | [-0.040, +0.070] | ok | no |
| skepticism | 20 | 6.0 | skep-strong-06 | 20 | 40 | -0.080 | [-0.225, +0.045] | ok | no |
| uncertainty_awareness | 20 | 8.0 | unc-strong-01 | 27 | 53 | -0.228 | [-0.370, -0.092] | ok | no |

- axes passing (Bonferroni): **0/3** -> **KILL_PLAN_D**

## Conflict cells (SECONDARY / descriptive only — NOT part of the verdict)

| axis | opposite α | mean conflict outcome | mean prompt-pole | latent drags down? |
|---|---|---|---|---|
| deliberation | -2.0 | 0.030 | 0.020 | False |
| skepticism | -6.0 | 0.775 | 0.775 | False |
| uncertainty_awareness | -8.0 | 0.841 | 0.848 | True |
