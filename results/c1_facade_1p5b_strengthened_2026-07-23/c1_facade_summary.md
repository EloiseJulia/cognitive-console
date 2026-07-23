# C1 Semantic-Facade Pilot — EXPLORATORY (protocol NOT frozen)

- model: `Qwen/Qwen2.5-1.5B-Instruct`  (CPU, float32)
- generated: 2026-07-23T10:25:21.823363+00:00
- seed: 20260723   n_null: 2000   hidden_dim: 1536
- scan layers: [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28]
- wall-clock: 461.3s (cache_was_cold=True, true_full_compute=True)   peak RSS: 9258.7 MB
- bootstrap: n_boot=2000  CI level=0.95
- layer selection (D-0019): NON-DEGENERATE rule — depth floor min_layer=6 (>= 20% of depth), pole_reach > 0 above random-null p95, positive pos/neg separation. top_k=3 candidate layers, seeds=[20260723, 20260724, 20260725].
- valid_for_paper: **False**

## Per-axis facade gap — CORRECTED same-origin, scale-free, alpha-free metric (D-0016)

facade_ratio = prompt_reach / pole_reach, both measured as on-axis displacement from the SAME neutral origin projected on û, at the chosen NON-DEGENERATE layer (D-0019). A facade genuinely HOLDS only when a stable layer exists AND extraction succeeded AND the bootstrap CI upper bound is < 1 (number reported; NO frozen verdict). An UNSTABLE axis has no non-degenerate layer at this model — reported honestly, NOT forced.

| axis | layer | stable? | prompt_reach | pole_reach | facade_ratio | 95% CI | leave-1-neutral band | extract ok? | seed-stable? | CI upper<1? | C1 signal |
|---|---|---|---|---|---|---|---|---|---|---|---|
| deliberation | 14 | yes | 4.324 | 6.568 | 0.658 | [0.567, 0.750] | [0.651, 0.668] | yes | yes | yes | YES |
| skepticism | 16 | yes | 2.834 | 3.195 | 0.887 | [0.743, 1.032] | [0.881, 0.892] | yes | yes | no | no |
| uncertainty_awareness | 18 | yes | 4.875 | 7.100 | 0.687 | [0.590, 0.782] | [0.678, 0.695] | yes | yes | yes | YES |
| focus | 2 | UNSTABLE | -0.461 | -0.010 | 44.272 | [33.970, 53.962] | [-110.037, 1474.281] | NO | yes | no | no |

### Unstable axes (HONEST — no facade forced)

- **focus**: no non-degenerate layer (min_layer=6); max-sep layer 2: below depth floor (layer 2 < 6); pole_reach <= 0 (pole not on +û side of neutral)

## ROBUSTNESS 1 — facade_ratio across top-k NON-DEGENERATE candidate layers (D-0019)

Shows whether the facade gap holds across NEARBY valid layers (not a single-layer artifact). Unstable axes have no candidates.

| axis | layer | separation | pole_reach | facade_ratio | 95% CI | CI upper<1? |
|---|---|---|---|---|---|---|
| deliberation | 14 | 5.669 | 6.568 | 0.658 | [0.567, 0.750] | yes |
| deliberation | 16 | 4.798 | 4.198 | 0.688 | [0.482, 0.899] | yes |
| deliberation | 18 | 4.795 | 5.518 | 0.685 | [0.498, 0.884] | yes |
| skepticism | 16 | 4.367 | 3.195 | 0.887 | [0.743, 1.032] | no |
| skepticism | 18 | 4.319 | 4.676 | 0.878 | [0.671, 1.059] | no |
| skepticism | 20 | 4.289 | 9.578 | 0.769 | [0.602, 0.914] | yes |
| uncertainty_awareness | 18 | 4.758 | 7.100 | 0.687 | [0.590, 0.782] | yes |
| uncertainty_awareness | 14 | 3.915 | 5.077 | 0.533 | [0.445, 0.621] | yes |
| uncertainty_awareness | 20 | 3.708 | 8.259 | 0.657 | [0.481, 0.825] | yes |
| focus | — (unstable) | — | — | — | — | — |

## ROBUSTNESS 2 — facade_ratio + CI at the chosen layer under multiple RNG seeds (D-0019)

The bootstrap/null seed should not move the verdict. `seed-stable` = all seeds agree on whether the CI upper bound is < 1.

| axis | seed | facade_ratio | 95% CI | CI upper<1? |
|---|---|---|---|---|
| deliberation | 20260723 | 0.658 | [0.567, 0.750] | yes |
| deliberation | 20260724 | 0.658 | [0.569, 0.756] | yes |
| deliberation | 20260725 | 0.658 | [0.569, 0.747] | yes |
| skepticism | 20260723 | 0.887 | [0.743, 1.032] | no |
| skepticism | 20260724 | 0.887 | [0.738, 1.036] | no |
| skepticism | 20260725 | 0.887 | [0.737, 1.034] | no |
| uncertainty_awareness | 20260723 | 0.687 | [0.590, 0.782] | yes |
| uncertainty_awareness | 20260724 | 0.687 | [0.593, 0.785] | yes |
| uncertainty_awareness | 20260725 | 0.687 | [0.591, 0.778] | yes |
| focus | 20260723 | 44.272 | [33.970, 53.962] | no |
| focus | 20260724 | 44.272 | [34.149, 53.599] | no |
| focus | 20260725 | 44.272 | [33.421, 53.727] | no |

## SUPERSEDED old ||v||-based ratio (denominator artifact, see D-0016) — for comparison only

| axis | ||v|| (SUPERSEDED) | old facade_ratio (prompt_reach/||v||) | new facade_ratio (prompt_reach/pole_reach) | flips verdict? |
|---|---|---|---|---|
| deliberation | 7.186 | 0.602 | 0.658 | no |
| skepticism | 5.650 | 0.502 | 0.887 | YES |
| uncertainty_awareness | 6.158 | 0.792 | 0.687 | no |
| focus | 1.078 | -0.428 | 44.272 | no |

## Sanity (labelled — NOT headline; trivial in high-dim, audit MAJOR-3)

| axis | prompt_reach above random-null? | signal_z | pole above-null p95 |
|---|---|---|---|
| deliberation | True | 16.76 | 0.936 |
| skepticism | True | 9.85 | 0.881 |
| uncertainty_awareness | True | 11.11 | 1.359 |
| focus | True | 12.16 | 0.102 |

## Aggregate

- axes where a facade genuinely holds (stable layer AND extract ok AND CI upper<1): 2/4 (50%)
- axes with a stable (non-degenerate) layer: 3/4 (unstable: 1)
- axes seed-stable (verdict invariant across seeds): 4/4
- max same-origin facade_ratio observed: 44.272
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
