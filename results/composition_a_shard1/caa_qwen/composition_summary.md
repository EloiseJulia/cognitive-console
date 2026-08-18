# C2b Composition Shard A — CAA × Qwen

- experiment_id: `composition-a-qwen-caa-20260818-0001`
- model: `Qwen/Qwen2.5-7B-Instruct`
- status: `done`
- direction provenance: `DIRECTIONS_REDERIVED_WITH_PROVENANCE_CAVEAT`
- bootstrap_B: 10000  CI: 0.98333  bootstrap_seed: 20260819

| baseline | axis | N_test | alpha* | mean Δ | 98.33% CI | MDE80 | coherence | parse | verdict |
|---|---:|---:|---:|---:|---|---:|---|---|---|
| ordinary | deliberation | 400 | 2.0 | +0.0045 | [-0.0085, +0.0175] | 0.0178 | ok | ok | NO_INCREMENT_DEMONSTRATED |
| strong | deliberation | 400 | 6.0 | -0.0105 | [-0.0255, +0.0050] | 0.0210 | ok | ok | NO_INCREMENT_DEMONSTRATED |
| ordinary | skepticism | 400 | 8.0 | +0.0055 | [-0.0090, +0.0205] | 0.0201 | ok | ok | NO_INCREMENT_DEMONSTRATED |
| strong | skepticism | 400 | 2.0 | -0.0005 | [-0.0175, +0.0165] | 0.0231 | ok | ok | NO_INCREMENT_DEMONSTRATED |
| ordinary | uncertainty_awareness | 400 | 6.0 | -0.0055 | [-0.0201, +0.0086] | 0.0194 | ok | ok | NO_INCREMENT_DEMONSTRATED |
| strong | uncertainty_awareness | 400 | 2.0 | +0.0034 | [-0.0098, +0.0167] | 0.0179 | ok | ok | NO_INCREMENT_DEMONSTRATED |

## Uncertainty missingness sensitivity

| baseline | primary Δ [CI] | complete-case N Δ [CI] | adversarial lower Δ [CI] | adversarial upper Δ [CI] | missing samples prompt/steer |
|---|---|---|---|---|---:|
| ordinary | -0.0055 [-0.0201, +0.0086] | 392 -0.0029 [-0.0173, +0.0110] | -0.0083 [-0.0239, +0.0064] | -0.0013 [-0.0160, +0.0128] | 10/4 |
| strong | +0.0034 [-0.0098, +0.0167] | 385 +0.0040 [-0.0091, +0.0175] | -0.0032 [-0.0176, +0.0109] | +0.0123 [-0.0030, +0.0280] | 20/11 |

Ordinary and strong baselines are separate estimands. Results are additive to, and do not overwrite, the frozen substitution grid. All reported shard verdicts remain NO_INCREMENT_DEMONSTRATED; this is not an equivalence proof.
