# Flagship powered behavior + READ run summary

- protocol: D-0044 frozen novice-disclosure preregistration
- model: Qwen/Qwen2.5-7B-Instruct
- hardware: A800 GPU 1 via CUDA_VISIBLE_DEVICES=1
- valid_for_paper: false
- verdict: behavioral-powered, human-α PENDING -> not-yet-confirmatory
- human-α: PENDING / not run; no confirmatory paper claim may be made
- TEST pool freeze commit: cb749b16a6b5e969608e50f2a74310ac675eb67d
- run code commit used on A800 archive: fb9c4c341af09112c427fe097465d29974582a8d

## Coverage and gates
- behavior experiment_id: flagship-l0-test-e9c69c0e317a6cc3-0001
- coverage: complete=True, n_items=54, k=5, n_records=1080
- judge-condition-bias: passed=True, max_abs_bias=0
- disclosure redaction exact audit: passed=True, leak_count=0
- original coarse substring redaction diagnostic in behavior JSON: passed=False, leak_count=36 (false positives from generic expertise/experts; see behavior/redaction_audit.json)
- human calibration: not_run_required_before_confirmatory_claim (target alpha=0.6)

## Condition means
| Dimension | A control | B novice | E explain-simple | C expert |
|---|---:|---:|---:|---:|
| M1 | 0.480741 | 0.482222 | 0.494074 | 0.438148 |
| M2 | 0 | 0 | 0 | 0 |
| M3 | 0 | 0 | 0 | 0 |
| M4 | 0 | 0 | 0 | 0 |

## Paired bootstrap contrasts
| Contrast | Dimension | point | CI low | CI high | p_raw | p_bonferroni | pass_without_human_alpha |
|---|---|---:|---:|---:|---:|---:|---|
| B-A | M1 | 0.00148148 | -0.0483356 | 0.0466667 | 0.9158 | 1 | False |
| B-A | M2 | 0 | 0 | 0 | 1 | 1 | False |
| B-A | M3 | 0 | 0 | 0 | 1 | 1 | False |
| B-A | M4 | 0 | 0 | 0 | 1 | 1 | False |
| B-E | M1 | -0.0118519 | -0.0703704 | 0.0388889 | 0.6448 | 1 | False |
| B-E | M4 | 0 | 0 | 0 | 1 | 1 | False |

## Behavioral verdict
- ba_pass_without_human_alpha: []
- be_m1_m4_pass_without_human_alpha: []
- manipulation_present_without_human_alpha: False
- interpretation: powered honest-null on behavior under this LLM-judge run; because human α is pending and audit is pending, this is not confirmatory evidence for paper claims.

## READ probe
- READ experiment_id: flagship-read-2ab4d4f5ff9cad62-0001
- selected_layer: 8
- literal AUC=1, token_blind AUC=0.954047, AUC drop pp=4.59534
- random null token-blind AUC p95=0.785665
- read_verdict: READ_HOLDS; recommend_steer_arm=True
- projections: B-A=0.692769, B-E=0.312655, B-C=1.36944
- steer alpha-grid was not run.

## Artifacts
- behavior/flagship_l0_results.json
- behavior/experiment-registry.yaml
- behavior/redaction_audit.json
- read/flagship_read_results.json
- read/experiment-registry.yaml
