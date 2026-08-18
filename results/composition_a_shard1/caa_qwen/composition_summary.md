# C2b Composition Shard A — CAA × Qwen

- experiment_id: `composition-a-qwen-caa-20260818-0001`
- model: `Qwen/Qwen2.5-7B-Instruct`
- status: `done`
- direction provenance: `DIRECTIONS_REDERIVED_WITH_PROVENANCE_CAVEAT`
- bootstrap_B: 10000  CI: 0.98333

| baseline | axis | N_test | alpha* | mean Δ | 98.33% CI | MDE80 | coherence | parse | verdict |
|---|---:|---:|---:|---:|---|---:|---|---|---|
| ordinary | deliberation | 400 | 2.0 | +0.0045 | [-0.0085, +0.0175] | 0.0178 | ok | ok | NO_INCREMENT_DEMONSTRATED |
| strong | deliberation | 400 | 6.0 | -0.0105 | [-0.0263, +0.0050] | 0.0210 | ok | ok | NO_INCREMENT_DEMONSTRATED |
| ordinary | skepticism | 400 | 8.0 | +0.0055 | [-0.0090, +0.0210] | 0.0201 | ok | ok | NO_INCREMENT_DEMONSTRATED |
| strong | skepticism | 400 | 2.0 | -0.0005 | [-0.0175, +0.0165] | 0.0231 | ok | ok | NO_INCREMENT_DEMONSTRATED |
| ordinary | uncertainty_awareness | 400 | 6.0 | -0.0055 | [-0.0199, +0.0082] | 0.0194 | ok | ok | NO_INCREMENT_DEMONSTRATED |
| strong | uncertainty_awareness | 400 | 2.0 | +0.0034 | [-0.0100, +0.0160] | 0.0179 | ok | ok | NO_INCREMENT_DEMONSTRATED |

Ordinary and strong baselines are separate estimands. Results are additive to, and do not overwrite, the frozen substitution grid.
