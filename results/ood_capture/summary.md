# OOD Capture Summary

- verdict: **NOT_SUPPORTED**
- criterion: >=3/4 cells with rho >= 0.30 and CI excluding 0
- backend: `hf`

| cell | method | model | layer | alpha | rho(distance, -delta) | CI | n | pass |
|---|---|---|---:|---:|---:|---|---:|---|
| caa__llama3-8b | caa | llama3-8b | 10 | 8 | +0.033 | [-0.252, +0.317] | 53 | no |
| caa__qwen2.5-7b | caa | qwen2.5-7b | 20 | 8 | +0.039 | [-0.259, +0.335] | 53 | no |
| iti__llama3-8b | iti | llama3-8b | 11 | 6 | -0.060 | [-0.321, +0.216] | 53 | no |
| iti__qwen2.5-7b | iti | qwen2.5-7b | 17 | 12 | -0.223 | [-0.485, +0.065] | 53 | no |

