# C1 Semantic-Facade Pilot — EXPLORATORY (protocol NOT frozen)

- model: `Qwen/Qwen2.5-1.5B-Instruct`  (CPU, float32)
- generated: 2026-07-23T09:18:03.506525+00:00
- seed: 20260723   n_null: 2000   hidden_dim: 1536
- scan layers: [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28]
- wall-clock: 19.64s   peak RSS: 9253.1 MB
- valid_for_paper: **False**

## Per-axis facade gap  (PRIMARY = mean-based; max = labelled UPPER BOUND)

| axis | layer | \|\|v\|\| (latent_reach) | neutral_proj | prompt_reach_mean | facade_ratio_mean | above_null(mean) | signal_z(mean) | prompt_reach_max | facade_ratio_max | above_null(max) | C1 signal | ext_sep | n_strong |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| deliberation | 14 | 7.19 | 4.57 | 3.72 | 0.517 | True | 14.44 | 5.89 | 0.819 | True | YES | 5.67 | 7 |
| skepticism | 16 | 5.65 | -1.46 | 2.73 | 0.482 | True | 9.67 | 4.11 | 0.727 | True | YES | 4.37 | 7 |
| uncertainty_awareness | 18 | 6.16 | -2.34 | 5.07 | 0.824 | True | 10.90 | 6.45 | 1.047 | True | YES | 4.76 | 7 |
| focus | 2 | 1.08 | -0.08 | -0.44 | -0.412 | True | 11.25 | 0.02 | 0.014 | False | no | 6.54 | 7 |

## Aggregate

- axes with a C1 signal (mean-based): 75% (3/4)
- max facade_ratio_mean observed: 0.824
- all axes above null (mean-based): True

## Routing (EXPLORATORY — not a real Go/No-Go)

- route: `plan_b`  verdict: `partial`
- EXPLORATORY only. This C1 pilot measures the semantic-facade gap; it does NOT measure blind-eval (AC4), transfer/composition (AC5), or the behavioral prompt-search ceiling (AC8). Those routing gates are set False here by construction, so the route is NOT a real Go/No-Go — the meaningful signal is the per-axis facade_ratio + above_null.

## How to read facade_ratio

- `latent_reach = ||v||` — the displacement adding the CAA vector produces along û.
- **PRIMARY** `prompt_reach_mean = MEAN` over the separately-authored strongest-prompt set of `project_scalar(act, û) − neutral_proj`, from the SAME neutral baseline.
- **UPPER BOUND (not headline)** `prompt_reach_max = MAX` over that set.
- `facade_ratio_{mean,max} = prompt_reach_{mean,max} / ||v||` (signed). ~1 => the prompt reaches as far as the latent vector (NO facade). 0 < ratio << 1 AND above null => a semantic-facade gap (prompt points the right way but falls short). < 0 => the prompt pushes the WRONG way along the axis (evidence against a clean prompt->latent map).
- The strongest-prompt set is DISTINCT IN KIND from the contrast pairs used to build v (guarded in tests/test_leakage.py), so the ratio is not inflated by pseudo-circularity.

## Provenance / cost note (added by hand — not spin)

- The `wall-clock` above (~20s) is a **cache-backed re-run** used to stamp clean
  code-commit provenance onto the artifact. The **true first full-compute run**
  (fresh activations for all 4 axes) took **453.6 s (~7.5 min)** on CPU.
- `peak RSS ≈ 9.25 GB` is genuine in both runs — it is dominated by the
  `from_pretrained` float32 1.5B weight materialization, which the cache-backed
  re-run still performs. System-available RAM at start was ~10.4 GB; the watchdog
  (450 MB floor) never tripped.
- The facade-ratio numbers are deterministic (fixed seed) and identical across the
  full-compute run and the cache-backed re-run.
