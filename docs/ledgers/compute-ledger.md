# Compute Ledger

> Tracks GPU hours, API/token cost, full-run count, pivot count against Charter §9 caps.
> Manager may NOT authorize L4 full runs, paid/private API, or GPU allocation — human approval required.

| date | resource | amount | experiment_id | authorized_by | running_total |
|---|---|---|---|---|---|
| 2026-07-23 | (none) | 0 | — | — | 0 |
| 2026-08-05 | A800 GPU-hours (failed pre-DEV attempt) | 0.00722222 upper bound | E-0016 | D-0095 | >=0.00722222 (legacy GPU runs not backfilled) |
| 2026-08-17 | A800 setup + avg-prompt synthetic CPU smoke; GPU1 identified free, no GPU generation run | 0 GPU-hours | AVG-PROMPT-COMPARATOR-20260817-FROZEN-UNRUN / smoke `avg-prompt-comparator-a41d7462-0001` | owner-approved Stage 1 | >=0.00722222 |

- max_gpu_hours: TBD (human)
- max_api_cost: TBD (human)
- max_full_runs: TBD (human)
- max_pivot_count: 2 (then mandatory human review)

- E-0016 D-0095 authorized cap: 3 A800 GPU-hours; consumed upper bound 0.00722222 GPU-h before the valid pre-DEV failure. Retry is authorized under unchanged protocol/run commit `c094f07fa3592c2210f46caba9e69c49a5a92fad` with a remaining hard cap of 2.99277778 A800 GPU-hours; no retry has yet been performed.
