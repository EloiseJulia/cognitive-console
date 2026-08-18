# Powered skepticism-B cell — iti_llama3_8b

- verdict: **UNDERPOWERED**
- model/method: `Llama-3-8B` / `iti`
- realized TEST N: **797** (target 900; cap_applied=True)
- mean(d): +0.028105
- 98.33% superiority CI: [-0.010540, +0.065916]
- 90% TOST CI: [+0.001757, +0.053952]
- realized MDE: 0.0508 (≤0.06: True)
- coherence_ok: True (steer_deg=0.024954, base_deg=0.021682)

## Format / token diagnostics

| phase | generations | parse rate | parse failed | tokens total | mean tokens/parseable | maybe truncated |
|---|---:|---:|---:|---:|---:|---:|
| test_prompt | 3985 | 1.0 | 0 | 196029 | 49.191719 | 0 |
| test_steer | 3985 | 1.0 | 0 | 203579 | 51.086324 | 0 |
| test_baseline | 3985 | 1.0 | 0 | 182904 | 45.898118 | 0 |

All numbers are computed from `powered_skepticism_b_results.json`; no hand-filled metrics.
