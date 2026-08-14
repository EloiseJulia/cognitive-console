# C1 Semantic-Facade Pilot — EXPLORATORY (protocol NOT frozen)

- model: `Qwen/Qwen2.5-7B-Instruct`  (CPU, float32)
- generated: 2026-08-14T03:01:00.425096+00:00
- seed: 20260812   n_null: 2000   hidden_dim: 3584
- scan layers: [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28]
- wall-clock: 26.83s (cache_was_cold=True, true_full_compute=True)   peak RSS: 1685.9 MB
- bootstrap: n_boot=2000  CI level=0.95
- layer selection (D-0019): NON-DEGENERATE rule — depth floor min_layer=6 (>= 20% of depth), pole_reach > 0 above random-null p95, positive pos/neg separation. top_k=3 candidate layers, seeds=[20260812, 20260813, 20260814].
- valid_for_paper: **False**

## Per-axis facade gap — CORRECTED same-origin, scale-free, alpha-free metric (D-0016)

facade_ratio = prompt_reach / pole_reach, both measured as on-axis displacement from the SAME neutral origin projected on û, at the chosen NON-DEGENERATE layer (D-0019). A facade genuinely HOLDS only when a stable layer exists AND extraction succeeded AND the bootstrap CI upper bound is < 1 (number reported; NO frozen verdict). An UNSTABLE axis has no non-degenerate layer at this model — reported honestly, NOT forced.

| axis | layer | stable? | prompt_reach | pole_reach | facade_ratio | 95% CI | leave-1-neutral band | extract ok? | seed-stable? | CI upper<1? | C1 signal |
|---|---|---|---|---|---|---|---|---|---|---|---|
| deliberation | 20 | yes | 9.358 | 16.531 | 0.566 | [0.462, 0.674] | [0.532, 0.592] | yes | yes | yes | YES |
| skepticism | 20 | yes | 12.096 | 23.269 | 0.520 | [0.420, 0.628] | [0.515, 0.527] | yes | yes | yes | YES |
| uncertainty_awareness | 24 | yes | 18.160 | 35.845 | 0.507 | [0.229, 0.760] | [0.476, 0.523] | yes | yes | yes | YES |

## ROBUSTNESS 1 — facade_ratio across top-k NON-DEGENERATE candidate layers (D-0019)

Shows whether the facade gap holds across NEARBY valid layers (not a single-layer artifact). Unstable axes have no candidates.

| axis | layer | separation | pole_reach | facade_ratio | 95% CI | CI upper<1? |
|---|---|---|---|---|---|---|
| deliberation | 20 | 5.421 | 16.531 | 0.566 | [0.462, 0.674] | yes |
| deliberation | 16 | 5.386 | 8.462 | 0.993 | [0.880, 1.094] | no |
| deliberation | 18 | 5.317 | 9.031 | 0.930 | [0.792, 1.063] | no |
| skepticism | 20 | 6.021 | 23.269 | 0.520 | [0.420, 0.628] | yes |
| skepticism | 28 | 5.614 | 94.898 | 0.326 | [0.221, 0.444] | yes |
| skepticism | 18 | 5.066 | 10.801 | 0.759 | [0.710, 0.812] | yes |
| uncertainty_awareness | 24 | 6.404 | 35.845 | 0.507 | [0.229, 0.760] | yes |
| uncertainty_awareness | 26 | 5.898 | 52.718 | 0.582 | [0.304, 0.841] | yes |
| uncertainty_awareness | 20 | 5.716 | 18.118 | 0.715 | [0.492, 0.934] | yes |

## ROBUSTNESS 2 — facade_ratio + CI at the chosen layer under multiple RNG seeds (D-0019)

The bootstrap/null seed should not move the verdict. `seed-stable` = all seeds agree on whether the CI upper bound is < 1.

| axis | seed | facade_ratio | 95% CI | CI upper<1? |
|---|---|---|---|---|
| deliberation | 20260812 | 0.566 | [0.462, 0.674] | yes |
| deliberation | 20260813 | 0.566 | [0.463, 0.679] | yes |
| deliberation | 20260814 | 0.566 | [0.461, 0.674] | yes |
| skepticism | 20260812 | 0.520 | [0.420, 0.628] | yes |
| skepticism | 20260813 | 0.520 | [0.419, 0.625] | yes |
| skepticism | 20260814 | 0.520 | [0.416, 0.625] | yes |
| uncertainty_awareness | 20260812 | 0.507 | [0.229, 0.760] | yes |
| uncertainty_awareness | 20260813 | 0.507 | [0.225, 0.765] | yes |
| uncertainty_awareness | 20260814 | 0.507 | [0.235, 0.763] | yes |

## SUPERSEDED old ||v||-based ratio (denominator artifact, see D-0016) — for comparison only

| axis | ||v|| (SUPERSEDED) | old facade_ratio (prompt_reach/||v||) | new facade_ratio (prompt_reach/pole_reach) | flips verdict? |
|---|---|---|---|---|
| deliberation | 32.498 | 0.288 | 0.566 | no |
| skepticism | 29.255 | 0.413 | 0.520 | no |
| uncertainty_awareness | 74.952 | 0.242 | 0.507 | no |

## Sanity (labelled — NOT headline; trivial in high-dim, audit MAJOR-3)

| axis | prompt_reach above random-null? | signal_z | pole above-null p95 |
|---|---|---|---|
| deliberation | True | 14.25 | 1.893 |
| skepticism | True | 19.57 | 2.204 |
| uncertainty_awareness | True | 10.85 | 4.881 |

## Aggregate

- axes where a facade genuinely holds (stable layer AND extract ok AND CI upper<1): 3/3 (100%)
- axes with a stable (non-degenerate) layer: 3/3 (unstable: 0)
- axes seed-stable (verdict invariant across seeds): 3/3
- max same-origin facade_ratio observed: 0.566
- extraction succeeded on all axes: True

## Routing (EXPLORATORY — not a real Go/No-Go)

- route: `plan_b`  verdict: `partial`
- EXPLORATORY only. This C1 pilot measures the semantic-facade gap; it does NOT measure blind-eval (AC4), transfer/composition (AC5), or the behavioral prompt-search ceiling (AC8). Those routing gates are set False here by construction, so the route is NOT a real Go/No-Go — the meaningful signal is the per-axis same-origin facade_ratio + its CI.

## How to read facade_ratio (CORRECTED, D-0016)

- `pole_reach = <mean(EXTRACTION-POS act) − neutral_mean_act, û>` — the model's ACHIEVABLE positive-pole displacement from the SAME neutral origin (NO steering coefficient alpha; replaces the old ||v|| denominator).
- `prompt_reach = <mean(strong-prompt act) − neutral_mean_act, û>` — the strongest readable prompt's displacement from the SAME origin.
- `facade_ratio = prompt_reach / pole_reach` (scale-free, alpha-free, same-origin). 0 < ratio << 1 AND CI upper<1 => genuine facade (prompt points right way, only part-way to the pole). ratio ~= 1 or >1 => NO facade. ratio < 0 => prompt goes the WRONG way.
- A facade 'holds' only if the bootstrap CI upper bound is meaningfully < 1 — we report the number and do NOT hard-code a frozen verdict.
- The strongest-prompt set is DISTINCT IN KIND from the contrast pairs used to build v (guarded in tests/test_leakage.py), so the ratio is not inflated by pseudo-circularity.
