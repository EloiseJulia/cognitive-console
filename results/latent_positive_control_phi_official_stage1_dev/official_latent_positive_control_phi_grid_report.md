# Phi-3 Official DEV Derived Grid Report

Derived from `official_latent_positive_control_dev_results.json`; no TEST item generated/scored.

- model: `phi-3` @ `f39ac1d28e925b323eae81227eaba4464caced4e`
- official repo: `9dac937ef6fc3e483b1efc13863deeb03ec38dbe`
- DEV n: `40`; extraction rows: `820`
- generation cap: `32` max new tokens for this DEV rerun (run command; included in config hash inputs but not separately serialized).
- baseline compliance: `0.150`; prompt compliance: `0.450`
- token normalization: `not_applicable: official keyword checker over decoded text`
- format compliance: `not_applicable: official IFEval keywords:existence binary verifier`

| layer | weight | steer compliance | steer-baseline Δ [CI] | steer-prompt Δ [CI] | coherence | format |
|---:|---:|---:|---:|---:|---|---|
| 24 | 40 | 0.175 | 0.025 [0.000, 0.100] | -0.275 [-0.450, -0.125] | PASS (g=0.000 ≤ 0.020) | n/a keyword verifier |
| 24 | 60 | 0.200 | 0.050 [0.000, 0.150] | -0.250 [-0.425, -0.075] | PASS (g=0.000 ≤ 0.020) | n/a keyword verifier |
| 24 | 80 | 0.200 | 0.050 [0.000, 0.150] | -0.250 [-0.425, -0.075] | PASS (g=0.000 ≤ 0.020) | n/a keyword verifier |
| 24 | 100 | 0.225 | 0.075 [0.000, 0.175] | -0.225 [-0.425, -0.025] | PASS (g=0.000 ≤ 0.020) | n/a keyword verifier |
| 26 | 40 | 0.200 | 0.050 [0.000, 0.150] | -0.250 [-0.425, -0.100] | PASS (g=0.000 ≤ 0.020) | n/a keyword verifier |
| 26 | 60 | 0.200 | 0.050 [0.000, 0.150] | -0.250 [-0.425, -0.100] | PASS (g=0.000 ≤ 0.020) | n/a keyword verifier |
| 26 | 80 | 0.225 | 0.075 [0.000, 0.175] | -0.225 [-0.425, -0.025] | PASS (g=0.000 ≤ 0.020) | n/a keyword verifier |
| 26 | 100 | 0.250 | 0.100 [0.000, 0.225] | -0.200 [-0.400, 0.000] | PASS (g=0.000 ≤ 0.020) | n/a keyword verifier |
| 28 | 40 | 0.175 | 0.025 [0.000, 0.100] | -0.275 [-0.450, -0.125] | PASS (g=0.000 ≤ 0.020) | n/a keyword verifier |
| 28 | 60 | 0.150 | 0.000 [-0.100, 0.075] | -0.300 [-0.475, -0.150] | PASS (g=0.000 ≤ 0.020) | n/a keyword verifier |
| 28 | 80 | 0.200 | 0.050 [-0.050, 0.175] | -0.250 [-0.450, -0.075] | PASS (g=0.000 ≤ 0.020) | n/a keyword verifier |
| 28 | 100 | 0.250 | 0.100 [0.000, 0.225] | -0.200 [-0.400, 0.000] | PASS (g=0.000 ≤ 0.020) | n/a keyword verifier |

Selected by frozen DEV rule: layer `26`, weight `100.0`; primary Δ `0.100` CI `[0.000, 0.225]`; sanity_pass `True`.
