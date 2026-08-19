# Uncertainty missingness sensitivity — ITI × Qwen composition shard

- experiment_id: `composition-a-qwen-iti-20260818-0001`
- bootstrap_seed: `20260819`; B=10000; item-cluster bootstrap; CI=98.33%.
- Complete-case excludes any paired TEST item with at least one unparseable confidence sample in either prompt-alone or prompt+steer.
- Adversarial lower sets missing prompt scores to 1 and missing steer scores to 0; adversarial upper sets missing prompt scores to 0 and missing steer scores to 1.

| baseline | parse prompt/steer | missing items | complete-case N | complete-case mean Δ | complete-case 98.33% CI | lower-bound mean Δ | lower-bound CI | upper-bound mean Δ | upper-bound CI | upper-bound gain pass? |
|---|---:|---:|---:|---:|---|---:|---|---:|---|---|
| ordinary | 0.995/0.963 | 47 | 353 | -0.044726 | [-0.083687, -0.006673] | -0.073093 | [-0.110798, -0.035603] | -0.031093 | [-0.068345, +0.003765] | false |
| strong | 0.990/0.983 | 25 | 375 | -0.013071 | [-0.029780, +0.003816] | -0.027924 | [-0.046534, -0.009362] | -0.000424 | [-0.017973, +0.018070] | false |

These analyses are diagnostic safeguards against confidence-parse missingness and do not replace the preregistered primary verdict.
