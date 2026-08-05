# Submission Evidence Ledger (Filtered)

> Claim-bearing and scoped limitation evidence used by the IUI paper. E-0004, E-0010, all E-0012 variants, and the E-0015 logit diagnostic are excluded from submission evidence.

| evidence_id | paper use | artifact lineage | validity and scope |
|---|---|---|---|
| E-0003 | Exploratory Qwen READ/facade context | `results/gpu_7b_2026-07-23/c1/` | Exploratory/scoped only; not confirmatory. |
| E-0005 | Frozen single-cell C2 failed-superiority result | `results/c2b_adjudication_hf_2026-07-24/` | Honest scoped negative for CAA×Qwen; not an impossibility theorem. |
| E-0006 | Frozen 2×2 CAA/ITI×Qwen/Llama C2 result | `results/arm_full/` | Core tested-grid evidence; comparator-specific uncertainty contrast. |
| E-0007 | Off-manifold mechanism null | `results/ood_capture/` | Null/future-work context only; supports no positive mechanism claim. |
| E-0008 | Exploratory Llama READ/facade context | `results/llama_c1_facade_2026-07-24/` | Exploratory/scoped only; axis composition differs from Qwen. |
| E-0009 | Exploratory PSR-style method-strength context | `results/psr_qwen_primary/` | Single-model/single-seed supporting context; does not alter the frozen headline. |
| E-0011 | Five split-seed robustness companion | `results/E-0011/` | Valid for paper per D-0055; same item pool, varying DEV/TEST membership only. |
| E-0013 | CAA×Qwen format-robustness/limitation claim | `results/E-0013-uncertainty-recheck/reanalysis.json`, SHA-256 `ea91f10cce1de06f9c38c4777064e85b7fcf44f295f7ef983092ca0843edfd01`; run `70af3996ddea4f881efbb4c0bff9241aad3849ce`; audit `reviews/2026-08-03-e0013-result-audit/audit-report.md`; merge `a56db4f5622487a89a310496ea79b408b057f6af` | Valid only for D-0078's narrow CAA×Qwen use. Paired-compliant estimate \(-0.337\), 95% CI \([-0.508,-0.165]\); adversarial missingness bounds \([-0.478,+0.250]\). Three cells unverified. |
| E-0014 | Endpoint-live + bounded-latent-null limitation | `results/E-0014-positive-control/positive_control_results.json`, SHA-256 `d3275016bd04ed3b9f1e06b7aceb4c7230d2f32b089d7a1f4949a8f902b1790c`; code `720c6c880f0df1e4841c66d99c007e73fcfc5392`; results `f520610a596da4df2f2cca44125352a24557c0d4` | Scoped limitation evidence only. Not a passing latent positive control and no metacognitive support. |
| E-0015 | Scale-corrected null/assay-sensitivity limitation | `results/E-0015-scale-corrected-positive-control/positive_control_scale_corrected_results.json`, SHA-256 `205bce38d85d8976c2b361632561d8fe3aea5fe5f1a0711aaf88cf373e40a2f7`; run `4d900a94ff01c056c93f4fa87e3074037a349adb`; integrated `6231855` | Scoped limitation only: coherent ceiling about \(0.5\)--\(0.66\times\lVert h\rVert\), near-\(1.05\times\) point degenerate, MDE near 0.19. Not a universal/core latent negative. |
