# Powered skepticism-B cell — iti_qwen25_7b

- verdict: **BOUNDED_EQUIVALENT**
- model/method: `Qwen2.5-7B` / `iti`
- realized TEST N: **600** (target 600; cap_applied=False)
- mean(d): -0.020000
- 98.33% superiority CI: [-0.055558, +0.015000]
- 90% TOST CI: [-0.044000, +0.004333]
- realized MDE: 0.0475 (≤0.06: True)
- coherence_ok: True (steer_deg=0.004853, base_deg=0.002376)

## Format / token diagnostics

| phase | generations | parse rate | parse failed | tokens total | mean tokens/parseable | maybe truncated |
|---|---:|---:|---:|---:|---:|---:|
| test_prompt | 3000 | 1.0 | 0 | 106189 | 35.396333 | 0 |
| test_steer | 3000 | 1.0 | 0 | 58111 | 19.370333 | 0 |
| test_baseline | 3000 | 1.0 | 0 | 32829 | 10.943 | 0 |

All numbers are computed from `powered_skepticism_b_results.json`; no hand-filled metrics.
