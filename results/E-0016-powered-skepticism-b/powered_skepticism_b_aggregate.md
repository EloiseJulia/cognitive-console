# E-0016 Powered skepticism-B aggregate

- prereg: `docs/specs/powered-tost-B-skepticism-prereg.md (FROZEN 2026-08-18)`
- code_commit: `81c7e79765e4526be3920617f173c921917ac858`
- seed: `20260818`

| cell | N target→realized | mean(d) | 98.33% CI | 90% TOST CI | MDE | ≤0.06? | coherence | parse prompt/steer | verdict |
|---|---:|---:|---|---|---:|---|---|---|---|
| caa × Qwen2.5-7B | 400→400 | -0.0090 | [-0.0520, +0.0325] | [-0.0380, +0.0200] | 0.0571 | True | True | 1.0/1.0 | **BOUNDED_EQUIVALENT** |
| caa × Llama-3-8B | 800→797 capped | +0.0276 | [-0.0095, +0.0657] | [+0.0013, +0.0542] | 0.0510 | True | True | 1.0/1.0 | **UNDERPOWERED** |
| iti × Qwen2.5-7B | 600→600 | -0.0200 | [-0.0556, +0.0150] | [-0.0440, +0.0043] | 0.0475 | True | True | 1.0/1.0 | **BOUNDED_EQUIVALENT** |
| iti × Llama-3-8B | 900→797 capped | +0.0281 | [-0.0105, +0.0659] | [+0.0018, +0.0540] | 0.0508 | True | True | 1.0/1.0 | **UNDERPOWERED** |

Outcome-neutral: these additive results do not overwrite E-0005/E-0006/E-0011.

## Auditability addendum

- Parse/missingness manifest: `results/E-0016-powered-skepticism-b/powered_skepticism_b_parse_manifest.json` (`sha256:d9df66c3564c1e51f0e3d58bb86f5e55cffd1c5a7246759e056612e421290bbc`); source transcripts were available and compact per-item/sample parse flags are committed.
- Direction-vector caveat: `direction_sha256` is not recorded because the direction vectors were not persisted. The run used frozen C2b reconstruction code + frozen seed/layer/α/σ; exact vector identity is not cryptographically proven without rerunning direction reconstruction.
