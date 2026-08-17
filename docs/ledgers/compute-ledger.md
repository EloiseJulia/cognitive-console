# Compute Ledger

> Tracks GPU hours, API/token cost, full-run count, pivot count against Charter §9 caps.
> Manager may NOT authorize L4 full runs, paid/private API, or GPU allocation — human approval required.

| date | resource | amount | experiment_id | authorized_by | running_total |
|---|---|---|---|---|---|
| 2026-07-23 | (none) | 0 | — | — | 0 |
| 2026-08-05 | A800 GPU-hours (failed pre-DEV attempt) | 0.00722222 upper bound | E-0016 | D-0095 | >=0.00722222 (legacy GPU runs not backfilled) |
| 2026-08-17 | A800 setup + avg-prompt synthetic CPU smoke; GPU1 identified free, no GPU generation run | 0 GPU-hours | AVG-PROMPT-COMPARATOR-20260817-FROZEN-UNRUN / smoke `avg-prompt-comparator-a41d7462-0001` | owner-approved Stage 1 | >=0.00722222 |
| 2026-08-17 | A800 GPU-hours (avg-prompt comparator Qwen 3 axes × CAA/ITI; GPU0/GPU1 only; valid_for_paper=false pending hostile audit) | 2.2913 GPU-hours | avg-prompt comparator raw bundles `8da27748`, `59ffba47`, `0cd02fe5`, `f64fa982`, `87f271fb`, `6d18ccd3` | GO-FAST owner approval 2026-08-17 | >=2.2985 |
| 2026-08-17 | A800 GPU1-hours (deliberation 512-token steering repair CAA/ITI serial; includes initial over-strict ITI floor-abort diagnostic and rerun; valid_for_paper=false pending hostile audit) | 0.2832 GPU-hours | repair raw bundles `5b3869d4`, `eaa42cf2` + avg−best correction | owner-approved deliberation repair 2026-08-17 | >=2.5817 |
| 2026-08-17 | A800 GPU-hours (simulated-novice prompt comparator Qwen 3 axes × CAA/ITI; GPU1 then GPU0 after free-card recheck; valid_for_paper=false, anchor calibration gate NOT passed; prompt generation used GPU1 but was not instrumented) | 2.7503 comparator-cell GPU-hours | novice prompt comparator raw bundles `novice-prompt-comparator-58951ae9-0001`, `novice-prompt-comparator-3da9a9b9-0001`, `novice-prompt-comparator-9eb1a5a7-0001`, `novice-prompt-comparator-1f352dc2-0001`, `novice-prompt-comparator-26e04e8d-0001`, `novice-prompt-comparator-8b5a5d58-0001` | owner-approved simulated-novice exploratory bridge 2026-08-17 | >=5.3320 |

- max_gpu_hours: TBD (human)
- max_api_cost: TBD (human)
- max_full_runs: TBD (human)
- max_pivot_count: 2 (then mandatory human review)

- E-0016 D-0095 authorized cap: 3 A800 GPU-hours; consumed upper bound 0.00722222 GPU-h before the valid pre-DEV failure. Retry is authorized under unchanged protocol/run commit `c094f07fa3592c2210f46caba9e69c49a5a92fad` with a remaining hard cap of 2.99277778 A800 GPU-hours; no retry has yet been performed.
