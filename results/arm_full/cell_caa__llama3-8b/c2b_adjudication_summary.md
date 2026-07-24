# C2b QUALIFIED Adjudication — FROZEN instrument (prereg §4/§5)

- verdict: **KILL_PLAN_D**
- model: `/root/autodl-tmp/models/Meta-Llama-3-8B-Instruct`   backend: `hf`   valid_for_paper: **False**
- run_type: **exploratory**   bootstrap_B: 10000   CI level: 0.98333 (Bonferroni 1−0.05/3)
- δ = 0.05   α grid: [2.0, 4.0, 6.0, 8.0, 12.0, 16.0, 24.0]

| axis | layer | frozen α | best prompt | n_dev | n_test | mean(d) | CI | coherence | PASS |
|---|---|---|---|---|---|---|---|---|---|
| deliberation | 12 | 4.0 | delib-strong-02 | 20 | 40 | +0.025 | [-0.030, +0.075] | ok | no |
| skepticism | 14 | 2.0 | skep-strong-11 | 20 | 40 | +0.000 | [-0.190, +0.200] | ok | no |
| uncertainty_awareness | 10 | 8.0 | unc-strong-09 | 27 | 53 | -0.072 | [-0.103, -0.034] | ok | no |

- axes passing (Bonferroni): **0/3** -> **KILL_PLAN_D**

## Conflict cells (SECONDARY / descriptive only — NOT part of the verdict)

| axis | opposite α | mean conflict outcome | mean prompt-pole | latent drags down? |
|---|---|---|---|---|
| deliberation | -4.0 | 0.060 | 0.015 | False |
| skepticism | -2.0 | 0.330 | 0.500 | True |
| uncertainty_awareness | -8.0 | 0.748 | 0.822 | True |
