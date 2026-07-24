# Robustness Arm 2x2 Matrix Summary

- generated_at: `2026-07-24T11:39:45.332358+00:00`
- arm_verdict: **NON_TRANSFER_GENERALIZED**
- rule: `any-pass => SCOPE_NARROWED_POSITIVE; else >=(n_cells-1) zero-pass => NON_TRANSFER_GENERALIZED; else INCONCLUSIVE`

| cell | method | model | per-axis pass | axes passed | verdict |
|---|---|---|---|---:|---|
| caa__qwen2.5-7b | caa | qwen2.5-7b | deliberation=n, skepticism=n, uncertainty_awareness=n | 0 | KILL_PLAN_D |
| caa__llama3-8b | caa | llama3-8b | deliberation=n, skepticism=n, uncertainty_awareness=n | 0 | KILL_PLAN_D |
| iti__qwen2.5-7b | iti | qwen2.5-7b | deliberation=n, skepticism=n, uncertainty_awareness=n | 0 | KILL_PLAN_D |
| iti__llama3-8b | iti | llama3-8b | deliberation=n, skepticism=n, uncertainty_awareness=n | 0 | KILL_PLAN_D |
