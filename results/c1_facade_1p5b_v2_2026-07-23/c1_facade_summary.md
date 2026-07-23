# C1 Semantic-Facade Pilot — EXPLORATORY (protocol NOT frozen)

- model: `Qwen/Qwen2.5-1.5B-Instruct`  (CPU, float32)
- generated: 2026-07-23T09:49:45.070488+00:00
- seed: 20260723   n_null: 2000   hidden_dim: 1536
- scan layers: [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28]
- wall-clock: 391.59s (cache_was_cold=True, true_full_compute=True)   peak RSS: 9254.7 MB
- bootstrap: n_boot=2000  CI level=0.95
- valid_for_paper: **False**

## Per-axis facade gap — CORRECTED same-origin, scale-free, alpha-free metric (D-0016)

facade_ratio = prompt_reach / pole_reach, both measured as on-axis displacement from the SAME neutral origin projected on û. A facade genuinely HOLDS only when extraction succeeded AND the bootstrap CI upper bound is < 1 (number reported; NO frozen verdict).

| axis | layer | prompt_reach | pole_reach | facade_ratio | 95% CI | leave-1-neutral band | extract ok? | CI upper<1? | C1 signal |
|---|---|---|---|---|---|---|---|---|---|
| deliberation | 14 | 3.718 | 6.568 | 0.566 | [0.437, 0.710] | [0.557, 0.578] | yes | yes | YES |
| skepticism | 16 | 2.726 | 3.195 | 0.853 | [0.634, 1.066] | [0.845, 0.859] | yes | no | no |
| uncertainty_awareness | 18 | 5.071 | 7.100 | 0.714 | [0.643, 0.796] | [0.706, 0.722] | yes | yes | YES |
| focus | 2 | -0.443 | -0.010 | 42.584 | [25.059, 57.889] | [-105.705, 1416.809] | NO | no | no |

## SUPERSEDED old ||v||-based ratio (denominator artifact, see D-0016) — for comparison only

| axis | ||v|| (SUPERSEDED) | old facade_ratio (prompt_reach/||v||) | new facade_ratio (prompt_reach/pole_reach) | flips verdict? |
|---|---|---|---|---|
| deliberation | 7.186 | 0.517 | 0.566 | no |
| skepticism | 5.650 | 0.482 | 0.853 | YES |
| uncertainty_awareness | 6.158 | 0.824 | 0.714 | no |
| focus | 1.078 | -0.412 | 42.584 | no |

## Sanity (labelled — NOT headline; trivial in high-dim, audit MAJOR-3)

| axis | prompt_reach above random-null? | signal_z | pole above-null p95 |
|---|---|---|---|
| deliberation | True | 14.44 | 0.936 |
| skepticism | True | 9.67 | 0.881 |
| uncertainty_awareness | True | 10.90 | 1.359 |
| focus | True | 11.25 | 0.102 |

## Aggregate

- axes where a facade genuinely holds (extract ok AND CI upper<1): 2/4 (50%)
- max same-origin facade_ratio observed: 42.584
- extraction succeeded on all axes: False

## Routing (EXPLORATORY — not a real Go/No-Go)

- route: `plan_d`  verdict: `red`
- EXPLORATORY only. This C1 pilot measures the semantic-facade gap; it does NOT measure blind-eval (AC4), transfer/composition (AC5), or the behavioral prompt-search ceiling (AC8). Those routing gates are set False here by construction, so the route is NOT a real Go/No-Go — the meaningful signal is the per-axis same-origin facade_ratio + its CI.

## How to read facade_ratio (CORRECTED, D-0016)

- `pole_reach = <mean(EXTRACTION-POS act) − neutral_mean_act, û>` — the model's ACHIEVABLE positive-pole displacement from the SAME neutral origin (NO steering coefficient alpha; replaces the old ||v|| denominator).
- `prompt_reach = <mean(strong-prompt act) − neutral_mean_act, û>` — the strongest readable prompt's displacement from the SAME origin.
- `facade_ratio = prompt_reach / pole_reach` (scale-free, alpha-free, same-origin). 0 < ratio << 1 AND CI upper<1 => genuine facade (prompt points right way, only part-way to the pole). ratio ~= 1 or >1 => NO facade. ratio < 0 => prompt goes the WRONG way.
- A facade 'holds' only if the bootstrap CI upper bound is meaningfully < 1 — we report the number and do NOT hard-code a frozen verdict.
- The strongest-prompt set is DISTINCT IN KIND from the contrast pairs used to build v (guarded in tests/test_leakage.py), so the ratio is not inflated by pseudo-circularity.
