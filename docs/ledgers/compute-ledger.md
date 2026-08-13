# Compute Ledger

> Tracks GPU hours, API/token cost, full-run count, pivot count against Charter §9 caps.
> Manager may NOT authorize L4 full runs, paid/private API, or GPU allocation — human approval required.

| date | resource | amount | experiment_id | authorized_by | running_total |
|---|---|---|---|---|---|
| 2026-07-23 | (none) | 0 | — | — | 0 |
| 2026-08-05 | A800 GPU-hours (failed pre-DEV attempt) | 0.00722222 upper bound | E-0016 | D-0095 | >=0.00722222 (legacy GPU runs not backfilled) |
| 2026-08-13 | A800 GPU3 hours (strong-vs-strong' non-degenerate negative positive-control) | 0.0837 (wall 301.2s, GPU3 only) | strong-negative-pc-c839e1c-20260813 | owner GPU auth (<=0.3 A800-GPU-h, GPU3 only) | n/a (diagnostic; separate owner authorization) |

- max_gpu_hours: TBD (human)
- max_api_cost: TBD (human)
- max_full_runs: TBD (human)
- max_pivot_count: 2 (then mandatory human review)

- E-0016 D-0095 authorized cap: 3 A800 GPU-hours; consumed upper bound 0.00722222 GPU-h before the valid pre-DEV failure. Retry is authorized under unchanged protocol/run commit `c094f07fa3592c2210f46caba9e69c49a5a92fad` with a remaining hard cap of 2.99277778 A800 GPU-hours; no retry has yet been performed.
