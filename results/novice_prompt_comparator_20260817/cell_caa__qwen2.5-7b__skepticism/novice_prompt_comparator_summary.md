# Simulated-Novice Prompt Comparator Arm

- valid_for_paper: **False**
- anchor calibration gate: **NOT passed; exploratory only**
- model: `Qwen/Qwen2.5-7B-Instruct` backend: `hf`
- steering_source: `frozen-result with optional deliberation 512-token repair`

| axis | frozen α | n_test | steer−novice mean(d) | 98.33% CI | coherence | pass/invalid | novice−best analogue |
|---|---:|---:|---:|---|---|---|---:|
| skepticism | 6 | 40 | -0.0000 | [-0.0784, +0.0659] | ok | no | -0.0800 |
