# Phi-3 Official Stage-2 TEST Report

Derived from `official_latent_positive_control_dev_results.json`; TEST was run once with frozen layer 28 × weight 80; no re-selection.

- experiment_id: `E-0017f-phi3-official-stolfo-positive-control-stage2-test-once`
- valid_for_paper: `False` (pending hostile audit)
- model: `phi-3` @ `f39ac1d28e925b323eae81227eaba4464caced4e`
- official repo: `9dac937ef6fc3e483b1efc13863deeb03ec38dbe`
- code commit: `78db8d096ac57909d2592cf449cf0feead1ba2df`; dirty_tree `False`
- data hash: `sha256:1f4452fe01a36621e13d9ff926c4ec12a5d99ef33902ae158576e78f98e89dc8`; TEST n `45`; test_start_index `41`; DEV/TEST overlap `0`
- DEV selection provenance: `E-0017e DEV artifact results/latent_positive_control_phi_official_stage1_dev_len256/official_latent_positive_control_dev_results.json at commit 6b11630 selected layer 28 × weight 80`
- frozen adjudicator: δ `0.05`, bootstrap B `10000`, CI `0.9833333333333333`, Bonferroni source `headline C2b convention: 1 - 0.05/3 = 0.983333... family CI reused unchanged for primary/secondary positive-control reporting`
- token normalization: `not_applicable: official keyword checker over decoded text`
- format compliance: `not_applicable: official IFEval keywords:existence binary verifier`

| arm | compliance | n | truncation | mean generated tokens | mean degeneracy |
|---|---:|---:|---:|---:|---:|
| baseline | 0.200000 | 45 | 0.044444 | 327.40 | 0.061064 |
| prompt | 0.866667 | 45 | 0.000000 | 332.07 | 0.044137 |
| steer L28 W80 | 0.422222 | 45 | 0.066667 | 372.76 | 0.102290 |

| cell | primary steer-baseline [98.33% CI] | secondary steer-prompt [98.33% CI] | coherence | format |
|---|---:|---:|---|---|
| layer 28 × weight 80 | 0.222222 [0.088889, 0.377778] | -0.444444 [-0.644444, -0.244444] | PASS (g=0.102290 ≤ 0.111595) | n/a keyword verifier |

Stage-2 verdict: `PASS` — PASS iff primary steer-baseline CI lower bound > 0, mean >= δ=0.05, and coherence passes; otherwise NO-PASS.
