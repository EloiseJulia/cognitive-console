# Compute Ledger

> Tracks GPU hours, API/token cost, full-run count, pivot count against Charter §9 caps.
> Manager may NOT authorize L4 full runs, paid/private API, or GPU allocation — human approval required.

| date | resource | amount | experiment_id | authorized_by | running_total |
|---|---|---|---|---|---|
| 2026-07-23 | (none) | 0 | — | — | 0 |
| 2026-08-05 | A800 GPU-hours (failed pre-DEV attempt) | 0.00722222 upper bound | E-0016 | D-0095 | >=0.00722222 (legacy GPU runs not backfilled) |

- max_gpu_hours: TBD (human)
- max_api_cost: TBD (human)
- max_full_runs: TBD (human)
- max_pivot_count: 2 (then mandatory human review)

- E-0016 D-0095/D-0097 authorized cap: 3 total GPU-hours across either the A800 profile or the owner-authorized AutoDL RTX 4080 SUPER 32 GiB profile; consumed upper bound 0.00722222 GPU-h before the valid pre-DEV failure. The remaining cumulative hard cap is 2.99277778 GPU-hours. D-0097 adds no hours; the operational amendment is DRAFT pending audit and a new exact run commit. No retry has yet been performed.
