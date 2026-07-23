# Evidence Ledger

> Links Hypothesis → Experiment → Evidence → Claim. Every quantitative datum used in the paper must
> trace to an immutable experiment_id in experiment-registry.yaml. No hand-copied numbers.

| evidence_id | supports_claim | from_experiment_id | artifact | verdict | last_verified |
|---|---|---|---|---|---|
| E-0001 | C1 (partial, exploratory) | c1-facade-d553d2cb-0001 | results/c1_facade_1p5b_v2_2026-07-23/ | 2/4 axes (deliberation 0.566, uncertainty 0.714) facade gap CI<1; skepticism no; focus fail. Qwen2.5-1.5B EXPLORATORY. SUPERSEDED by E-0002. | 2026-07-23 |
| E-0002 | C1 (partial, exploratory, STRENGTHENED) | feature/4 strengthened run | results/c1_facade_1p5b_strengthened_2026-07-23/ | Non-degenerate layer rule + 16 prompts/axis + 3 seeds + top-k layers. **2/4 axes hold:** deliberation 0.658 [0.567,0.750], uncertainty 0.687 [0.590,0.782] (CI<1, seed-stable, multi-layer robust). skepticism 0.887 [0.743,1.032] borderline (layer-fragile: L20→0.769 holds). focus UNSTABLE (no non-degenerate layer at 1.5B, pole_reach≤0 all layers — real negative). Qwen2.5-1.5B, EXPLORATORY, valid_for_paper=false. | 2026-07-23 (Manager light check: metric audit-blessed, layer-rule test-pinned, 131 tests green, summary reviewed) |
