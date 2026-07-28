# Console v2 UI-contract simulated demo report

No human labels, GPU, paid APIs, model downloads, or live model calls were used. The flags below are computed from frozen local artifacts.

## C1 facade-limit flags
- deliberation: ratio=0.583, CI=[0.488, 0.680], source=c1_results_json
- skepticism: ratio=0.548, CI=[0.434, 0.670], source=c1_results_json
- uncertainty_awareness: ratio=0.713, CI=[0.517, 0.910], source=c1_results_json

## C1 non-facade / overshoot flags
- focus: ratio=2.844, CI=[2.061, 3.549], source=c1_results_json

## C2 steering degradation or adjudication-fail flags
- deliberation: Δ=0.015, CI=[-0.040, 0.070], pass=False, robust=False
- skepticism: Δ=-0.080, CI=[-0.225, 0.045], pass=False, robust=False
- uncertainty_awareness: Δ=-0.228, CI=[-0.370, -0.092], pass=False, robust=True

## E-0006 2×2 uncertainty harm replication flags
- caa×qwen2.5-7b: Δ=-0.228, CI=[-0.370, -0.092]
- caa×llama3-8b: Δ=-0.072, CI=[-0.103, -0.034]
- iti×qwen2.5-7b: Δ=-0.103, CI=[-0.136, -0.069]
- iti×llama3-8b: Δ=-0.084, CI=[-0.115, -0.049]

## E-0010 legible-but-not-controllable social-axis flags
- Social inference: novice-disclosure: LEGIBLE but NOT CONTROLLABLE; READ=HOLDS token-blind AUC=0.954; TRANSFER=NULL B−A M1=0.001, CI=[-0.048, 0.047], p_bonf=1.000; sources={'behavior': 'results/flagship_powered/behavior/flagship_l0_results.json', 'read': 'results/flagship_powered/read/flagship_read_results.json'}

## E-0009 PSR method-strength robustness flags
- Deliberation: pass=False, Δ=0.025, CI=[-0.030, 0.100], source=results/psr_qwen_primary/psr_c2b_adjudication_results.json
- Skepticism: pass=False, Δ=-0.060, CI=[-0.210, 0.070], source=results/psr_qwen_primary/psr_c2b_adjudication_results.json
- Uncertainty-awareness: pass=False, Δ=-0.160, CI=[-0.292, -0.039], source=results/psr_qwen_primary/psr_c2b_adjudication_results.json
