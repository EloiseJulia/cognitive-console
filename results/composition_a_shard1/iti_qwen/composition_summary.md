# C2b Composition Shard A — ITI × Qwen

- experiment_id: `composition-a-qwen-iti-20260818-0001`
- model: `Qwen/Qwen2.5-7B-Instruct`
- method: `ITI`
- status: `done`
- direction provenance: `DIRECTIONS_REDERIVED_WITH_PROVENANCE_CAVEAT`
- bootstrap_B: 10000  CI: 0.98333  bootstrap_seed: 20260819

| baseline | axis | N_test | alpha* | mean Δ | 98.33% CI | MDE80 | coherence | parse | verdict |
|---|---|---:|---:|---:|---|---:|---|---|---|
| ordinary | deliberation | 400 | 2.0 | -0.0090 | [-0.0280, +0.0100] | 0.0260 | ok | ok | NO_INCREMENT_DEMONSTRATED |
| strong | deliberation | 400 | 2.0 | -0.0255 | [-0.0455, -0.0067] | 0.0260 | ok | ok | NO_INCREMENT_DEMONSTRATED |
| ordinary | skepticism | 400 | 2.0 | -0.0175 | [-0.0425, +0.0070] | 0.0344 | ok | ok | NO_INCREMENT_DEMONSTRATED |
| strong | skepticism | 400 | 2.0 | -0.0250 | [-0.0535, +0.0035] | 0.0386 | ok | ok | NO_INCREMENT_DEMONSTRATED |
| ordinary | uncertainty_awareness | 400 | 8.0 | -0.0441 | [-0.0808, -0.0091] | 0.0492 | ok | FAIL | UNDERPOWERED_OR_INVALID |
| strong | uncertainty_awareness | 400 | 2.0 | -0.0123 | [-0.0281, +0.0038] | 0.0219 | ok | ok | NO_INCREMENT_DEMONSTRATED |

## Uncertainty missingness sensitivity

| baseline | primary Δ [CI] | complete-case N Δ [CI] | adversarial lower Δ [CI] | adversarial upper Δ [CI] | missing samples prompt/steer |
|---|---|---|---|---|---:|
| ordinary | -0.0441 [-0.0808, -0.0091] | 353 -0.0447 [-0.0837, -0.0067] | -0.0731 [-0.1108, -0.0356] | -0.0311 [-0.0683, +0.0038] | 10/74 |
| strong | -0.0123 [-0.0281, +0.0038] | 375 -0.0131 [-0.0298, +0.0038] | -0.0279 [-0.0465, -0.0094] | -0.0004 [-0.0180, +0.0181] | 20/35 |

Ordinary and strong baselines are separate estimands. ITI is the second Qwen method shard under the frozen composition prereg; it is additive to, and does not overwrite, the frozen substitution grid or CAA shard.
Interpretation is neutral: ordinary contains one invalid/underpowered uncertainty cell because the preregistered parse gate failed; strong is a no-increment-demonstrated null.
