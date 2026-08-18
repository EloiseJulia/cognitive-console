# Uncertainty missingness sensitivity — CAA × Qwen composition shard

- experiment_id: `composition-a-qwen-caa-20260818-0001`
- bootstrap_seed: `20260819`; B=10000; item-cluster bootstrap; CI=98.33%.
- Complete-case excludes any paired TEST item with at least one unparseable confidence sample in either prompt-alone or prompt+steer.
- Adversarial lower sets missing prompt scores to 1 and missing steer scores to 0; adversarial upper sets missing prompt scores to 0 and missing steer scores to 1.

| baseline | parse prompt/steer | missing items | complete-case N | complete-case mean Δ | complete-case 98.33% CI | lower-bound mean Δ | lower-bound CI | upper-bound mean Δ | upper-bound CI | upper-bound gain pass? |
|---|---:|---:|---:|---:|---|---:|---|---:|---|---|
| ordinary | 0.995/0.998 | 8 | 392 | -0.002946 | [-0.017336, +0.011022] | -0.008253 | [-0.023903, +0.006351] | -0.001253 | [-0.015985, +0.012806] | false |
| strong | 0.990/0.995 | 15 | 385 | +0.004037 | [-0.009119, +0.017476] | -0.003236 | [-0.017596, +0.010864] | +0.012264 | [-0.003015, +0.028037] | false |

Sensitivity does not change the primary frozen verdict: both uncertainty cells remain NO_INCREMENT_DEMONSTRATED under the preregistered primary analysis. Adversarial bounds are diagnostic for the small parse-missingness rates and are not used to claim gain.
