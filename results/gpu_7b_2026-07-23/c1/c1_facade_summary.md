# C1 Semantic-Facade Pilot — EXPLORATORY (protocol NOT frozen)

- model: `Qwen/Qwen2.5-7B-Instruct`  (CPU, float32)
- generated: 2026-07-23T11:59:32.525627+00:00
- seed: 20260723   n_null: 2000   hidden_dim: 3584
- scan layers: [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28]
- wall-clock: 27.74s (cache_was_cold=True, true_full_compute=True)   peak RSS: 2452.2 MB
- bootstrap: n_boot=2000  CI level=0.95
- layer selection (D-0019): NON-DEGENERATE rule — depth floor min_layer=6 (>= 20% of depth), pole_reach > 0 above random-null p95, positive pos/neg separation. top_k=3 candidate layers, seeds=[20260723, 20260724, 20260725].
- valid_for_paper: **False**

## Per-axis facade gap — CORRECTED same-origin, scale-free, alpha-free metric (D-0016)

facade_ratio = prompt_reach / pole_reach, both measured as on-axis displacement from the SAME neutral origin projected on û, at the chosen NON-DEGENERATE layer (D-0019). A facade genuinely HOLDS only when a stable layer exists AND extraction succeeded AND the bootstrap CI upper bound is < 1 (number reported; NO frozen verdict). An UNSTABLE axis has no non-degenerate layer at this model — reported honestly, NOT forced.

| axis | layer | stable? | prompt_reach | pole_reach | facade_ratio | 95% CI | leave-1-neutral band | extract ok? | seed-stable? | CI upper<1? | C1 signal |
|---|---|---|---|---|---|---|---|---|---|---|---|
| deliberation | 20 | yes | 10.418 | 17.878 | 0.583 | [0.488, 0.680] | [0.555, 0.603] | yes | yes | yes | YES |
| skepticism | 20 | yes | 11.484 | 20.970 | 0.548 | [0.434, 0.670] | [0.542, 0.556] | yes | yes | yes | YES |
| uncertainty_awareness | 20 | yes | 15.192 | 21.304 | 0.713 | [0.517, 0.910] | [0.703, 0.720] | yes | yes | yes | YES |
| focus | 16 | yes | 5.654 | 1.988 | 2.844 | [2.061, 3.549] | [2.616, 3.173] | yes | yes | no | no |

## ROBUSTNESS 1 — facade_ratio across top-k NON-DEGENERATE candidate layers (D-0019)

Shows whether the facade gap holds across NEARBY valid layers (not a single-layer artifact). Unstable axes have no candidates.

| axis | layer | separation | pole_reach | facade_ratio | 95% CI | CI upper<1? |
|---|---|---|---|---|---|---|
| deliberation | 20 | 5.197 | 17.878 | 0.583 | [0.488, 0.680] | yes |
| deliberation | 16 | 4.997 | 8.706 | 0.946 | [0.847, 1.050] | no |
| deliberation | 24 | 4.912 | 39.702 | 0.419 | [0.285, 0.568] | yes |
| skepticism | 20 | 5.749 | 20.970 | 0.548 | [0.434, 0.670] | yes |
| skepticism | 18 | 5.419 | 10.058 | 0.757 | [0.699, 0.813] | yes |
| skepticism | 28 | 5.409 | 87.222 | 0.329 | [0.215, 0.454] | yes |
| uncertainty_awareness | 20 | 5.367 | 21.304 | 0.713 | [0.517, 0.910] | yes |
| uncertainty_awareness | 24 | 5.159 | 43.567 | 0.543 | [0.297, 0.779] | yes |
| uncertainty_awareness | 18 | 4.959 | 9.886 | 0.522 | [0.429, 0.609] | yes |
| focus | 16 | 5.747 | 1.988 | 2.844 | [2.061, 3.549] | no |
| focus | 20 | 5.682 | 14.762 | 1.178 | [1.031, 1.310] | no |
| focus | 22 | 5.162 | 15.891 | 1.118 | [0.896, 1.328] | no |

## ROBUSTNESS 2 — facade_ratio + CI at the chosen layer under multiple RNG seeds (D-0019)

The bootstrap/null seed should not move the verdict. `seed-stable` = all seeds agree on whether the CI upper bound is < 1.

| axis | seed | facade_ratio | 95% CI | CI upper<1? |
|---|---|---|---|---|
| deliberation | 20260723 | 0.583 | [0.488, 0.680] | yes |
| deliberation | 20260724 | 0.583 | [0.487, 0.689] | yes |
| deliberation | 20260725 | 0.583 | [0.494, 0.679] | yes |
| skepticism | 20260723 | 0.548 | [0.434, 0.670] | yes |
| skepticism | 20260724 | 0.548 | [0.436, 0.660] | yes |
| skepticism | 20260725 | 0.548 | [0.429, 0.660] | yes |
| uncertainty_awareness | 20260723 | 0.713 | [0.517, 0.910] | yes |
| uncertainty_awareness | 20260724 | 0.713 | [0.517, 0.899] | yes |
| uncertainty_awareness | 20260725 | 0.713 | [0.514, 0.911] | yes |
| focus | 20260723 | 2.844 | [2.061, 3.549] | no |
| focus | 20260724 | 2.844 | [2.045, 3.541] | no |
| focus | 20260725 | 2.844 | [2.047, 3.537] | no |

## SUPERSEDED old ||v||-based ratio (denominator artifact, see D-0016) — for comparison only

| axis | ||v|| (SUPERSEDED) | old facade_ratio (prompt_reach/||v||) | new facade_ratio (prompt_reach/pole_reach) | flips verdict? |
|---|---|---|---|---|
| deliberation | 31.595 | 0.330 | 0.583 | no |
| skepticism | 29.948 | 0.383 | 0.548 | no |
| uncertainty_awareness | 27.067 | 0.561 | 0.713 | no |
| focus | 16.879 | 0.335 | 2.844 | YES |

## Sanity (labelled — NOT headline; trivial in high-dim, audit MAJOR-3)

| axis | prompt_reach above random-null? | signal_z | pole above-null p95 |
|---|---|---|---|
| deliberation | True | 15.86 | 1.974 |
| skepticism | True | 17.68 | 2.214 |
| uncertainty_awareness | True | 22.64 | 2.029 |
| focus | True | 17.05 | 0.901 |

## Aggregate

- axes where a facade genuinely holds (stable layer AND extract ok AND CI upper<1): 3/4 (75%)
- axes with a stable (non-degenerate) layer: 4/4 (unstable: 0)
- axes seed-stable (verdict invariant across seeds): 4/4
- max same-origin facade_ratio observed: 2.844
- extraction succeeded on all axes: True

## Routing (EXPLORATORY — not a real Go/No-Go)

- route: `plan_d`  verdict: `red`
- EXPLORATORY only. This C1 pilot measures the semantic-facade gap; it does NOT measure blind-eval (AC4), transfer/composition (AC5), or the behavioral prompt-search ceiling (AC8). Those routing gates are set False here by construction, so the route is NOT a real Go/No-Go — the meaningful signal is the per-axis same-origin facade_ratio + its CI.

## How to read facade_ratio (CORRECTED, D-0016)

- `pole_reach = <mean(EXTRACTION-POS act) − neutral_mean_act, û>` — the model's ACHIEVABLE positive-pole displacement from the SAME neutral origin (NO steering coefficient alpha; replaces the old ||v|| denominator).
- `prompt_reach = <mean(strong-prompt act) − neutral_mean_act, û>` — the strongest readable prompt's displacement from the SAME origin.
- `facade_ratio = prompt_reach / pole_reach` (scale-free, alpha-free, same-origin). 0 < ratio << 1 AND CI upper<1 => genuine facade (prompt points right way, only part-way to the pole). ratio ~= 1 or >1 => NO facade. ratio < 0 => prompt goes the WRONG way.
- A facade 'holds' only if the bootstrap CI upper bound is meaningfully < 1 — we report the number and do NOT hard-code a frozen verdict.
- The strongest-prompt set is DISTINCT IN KIND from the contrast pairs used to build v (guarded in tests/test_leakage.py), so the ratio is not inflated by pseudo-circularity.
