# C1 Semantic-Facade Pilot — EXPLORATORY (protocol NOT frozen)

- model: `Qwen/Qwen2.5-0.5B-Instruct`  (CPU, float32)
- generated: 2026-07-23T08:37:01.681912+00:00
- seed: 20260723   n_null: 2000   hidden_dim: 896
- scan layers: [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24]
- wall-clock: 81.01s   peak RSS: 3249.2 MB
- valid_for_paper: **False**

## Per-axis facade gap

| axis | layer | \|\|v\|\| | neutral_proj | strongest_shift | facade_ratio | mean_ratio | above_null | signal_z | C1 signal | ext/probe |
|---|---|---|---|---|---|---|---|---|---|---|
| deliberation | 16 | 4.52 | 0.66 | 5.24 | 1.161 | 0.725 | True | 25.84 | no | 28/12 |
| skepticism | 2 | 0.18 | 0.06 | -0.02 | -0.129 | -0.515 | False | 1.43 | no | 28/12 |
| uncertainty_awareness | 12 | 1.27 | -1.79 | 1.34 | 1.059 | 0.652 | True | 12.06 | no | 28/12 |
| focus | 12 | 2.47 | -1.84 | 1.72 | 0.696 | 0.409 | True | 15.85 | YES | 28/12 |

## Aggregate

- axes with a C1 signal: 25% (1/4)
- worst (max) facade_ratio: 1.161
- all axes above null: False

## Routing (EXPLORATORY — not a real Go/No-Go)

- route: `plan_d`  verdict: `red`
- EXPLORATORY only. This C1 pilot measures the semantic-facade gap; it does NOT measure blind-eval (AC4), transfer/composition (AC5), or the behavioral prompt-search ceiling (AC8). Those routing gates are set False here by construction, so the route is NOT a real Go/No-Go — the meaningful signal is the per-axis facade_ratio + above_null.

## How to read facade_ratio

- `facade_ratio = strongest_prompt_shift / ||v||` (signed). ~1 => the best readable prompt reaches as far as the latent vector (NO facade). Near 0 (but > 0 and above null) => strong facade: the prompt points the right way but falls far short of the latent reach. < 0 => the best prompt pushes the WRONG way along the axis (evidence against a clean prompt->latent map, not a facade).
