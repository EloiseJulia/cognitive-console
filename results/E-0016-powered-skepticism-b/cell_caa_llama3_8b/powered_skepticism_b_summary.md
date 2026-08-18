# Powered skepticism-B cell — caa_llama3_8b

- verdict: **UNDERPOWERED**
- model/method: `Llama-3-8B` / `caa`
- realized TEST N: **797** (target 800; cap_applied=True)
- mean(d): +0.027604
- 98.33% superiority CI: [-0.009536, +0.065747]
- 90% TOST CI: [+0.001255, +0.054203]
- realized MDE: 0.051 (≤0.06: True)
- coherence_ok: True (steer_deg=0.023913, base_deg=0.021682)

## Format / token diagnostics

| phase | generations | parse rate | parse failed | tokens total | mean tokens/parseable | maybe truncated |
|---|---:|---:|---:|---:|---:|---:|
| test_prompt | 3985 | 1.0 | 0 | 196029 | 49.191719 | 0 |
| test_steer | 3985 | 1.0 | 0 | 201191 | 50.487077 | 0 |
| test_baseline | 3985 | 1.0 | 0 | 182904 | 45.898118 | 0 |

All numbers are computed from `powered_skepticism_b_results.json`; no hand-filled metrics.

## Provenance addendum

- parse manifest: `results/E-0016-powered-skepticism-b/powered_skepticism_b_parse_manifest.json` (`sha256:d9df66c3564c1e51f0e3d58bb86f5e55cffd1c5a7246759e056612e421290bbc`)
- direction_sha256: not recorded; direction vector was not persisted, so exact loaded reuse is not cryptographically proven without rerunning reconstruction. Frozen code path/seed/layer/α/σ are recorded in JSON provenance.
