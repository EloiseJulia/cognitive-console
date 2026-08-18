# Powered skepticism-B cell — caa_qwen25_7b

- verdict: **BOUNDED_EQUIVALENT**
- model/method: `Qwen2.5-7B` / `caa`
- realized TEST N: **400** (target 400; cap_applied=False)
- mean(d): -0.009000
- 98.33% superiority CI: [-0.052000, +0.032500]
- 90% TOST CI: [-0.038000, +0.020000]
- realized MDE: 0.0571 (≤0.06: True)
- coherence_ok: True (steer_deg=0.002677, base_deg=0.002506)

## Format / token diagnostics

| phase | generations | parse rate | parse failed | tokens total | mean tokens/parseable | maybe truncated |
|---|---:|---:|---:|---:|---:|---:|
| test_prompt | 2000 | 1.0 | 0 | 72525 | 36.2625 | 0 |
| test_steer | 2000 | 1.0 | 0 | 25512 | 12.756 | 0 |
| test_baseline | 2000 | 1.0 | 0 | 22937 | 11.4685 | 0 |

All numbers are computed from `powered_skepticism_b_results.json`; no hand-filled metrics.

## Provenance addendum

- parse manifest: `results/E-0016-powered-skepticism-b/powered_skepticism_b_parse_manifest.json` (`sha256:d9df66c3564c1e51f0e3d58bb86f5e55cffd1c5a7246759e056612e421290bbc`)
- direction_sha256: not recorded; direction vector was not persisted, so exact loaded reuse is not cryptographically proven without rerunning reconstruction. Frozen code path/seed/layer/α/σ are recorded in JSON provenance.
