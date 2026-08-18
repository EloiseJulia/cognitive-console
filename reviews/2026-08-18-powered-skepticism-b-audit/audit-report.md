# Hostile Audit — Dispatch B Powered Skepticism Re-measurement (E-0016, additive)

- **Auditor:** independent hostile audit session `audit-powered-b` (fresh, no-context, adversarial), 2026-08-18
- **Target:** `feature/powered-remeasure-b@95b0905` (generation code `81c7e79`, ancestor); provenance fixes at `e42b3ef`
- **Experiment:** `e0016-powered-skepticism-b` (additive powered re-measurement of skepticism cells)
- **Verdict:** **CONDITIONALLY SOUND → SOUND after provenance fixes.** No BLOCKER. Four cell labels independently reproduced.

## Independent re-derivation (from committed per-item arrays)

| cell | mean(steer−prompt) | 90% TOST CI | label |
|---|---|---|---|
| CAA×Qwen | −0.0090 | [−0.0380, 0.0200] | **BOUNDED_EQUIVALENT** (within ±0.05) |
| ITI×Qwen | −0.0200 | [−0.0440, 0.0043] | **BOUNDED_EQUIVALENT** |
| CAA×Llama | +0.0276 | [0.0013, 0.0542] | **UNDERPOWERED** (upper > +0.05) |
| ITI×Llama | +0.0281 | [0.0018, 0.0540] | **UNDERPOWERED** |

MDEs reproduce: 0.0571 / 0.0475 / 0.0510 / 0.0508. All labels correctly applied per the frozen decision rule.

## Findings (both MAJORs now closed)

### MAJOR 1 (CLOSED) — parse/transcript not independently reproducible
- Original: E-0016 transcripts gitignored; parse rates summary-only.
- Fix (commit `e42b3ef`): committed `powered_skepticism_b_parse_manifest.{json,md}` built from still-available raw transcripts. All 4 cells × 3 conditions: parse_rate = 1.0, missing = 0. Parse/missingness now independently auditable.

### MAJOR 2 (CLOSED via caveat) — exact frozen direction reuse not cryptographically proven
- Original: runner reconstructs directions; no direction hash in provenance.
- Fix (commit `e42b3ef`): direction vector not persisted → `direction_sha256: null` recorded explicitly with a caveat that the direction is reconstructed via the frozen C2b code path + frozen inputs/seed/layer/α/σ, not a cryptographically-proven exact loaded-vector reuse. Reconstruction path and parameters frozen for auditability.

### MINOR — commit-lineage wording
- Aggregate/registry cite generation code `81c7e79` while branch/artifact commit is `95b0905`. Acceptable; made explicit.

## Other checks
- Additive only: no E-0005/E-0006/E-0011 artifacts modified.
- DEV/TEST zero overlap; Llama cap N=797 is the fixed TruthfulQA item ceiling (no duplicates/replacement/new source).
- Coherence gates independently pass for all cells.
- Paired arrays satisfy diff = steer − prompt; item-cluster bootstrap B=10000.
- Targeted tests: 31 passed. Full-suite failures are baseline/env, not attributed to this branch.

## Paper scope (what is licensed)
- **Can state:** Qwen skepticism no-pass survives near δ=0.05 under powered additive re-measurement (bounded-equivalent).
- **Must state:** Llama cells remain underpowered/indeterminate; single dataset (TruthfulQA), skepticism-only, additive appendix; does not revise the frozen 0/12 headline.
