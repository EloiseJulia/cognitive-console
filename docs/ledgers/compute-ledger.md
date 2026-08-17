# Compute Ledger

> Tracks GPU hours, API/token cost, full-run count, pivot count against Charter §9 caps.
> Manager may NOT authorize L4 full runs, paid/private API, or GPU allocation — human approval required.

| date | resource | amount | experiment_id | authorized_by | running_total |
|---|---|---|---|---|---|
| 2026-07-23 | (none) | 0 | — | — | 0 |
| 2026-08-05 | A800 GPU-hours (failed pre-DEV attempt) | 0.00722222 upper bound | E-0016 | D-0095 | >=0.00722222 (legacy GPU runs not backfilled) |
| 2026-08-17 | A800 GPU-hours (Stage-1 latent behavioral positive-control DEV; GPU3; TEST not run) | 0.16343 | E-0017 | owner-approved Stage-1 latent positive control | >=0.17065 |
| 2026-08-17 | A800 GPU-hours (official Stolfo rerun: one 86-item run stopped for runtime + one 40-item DEV completed; GPU3; TEST not run) | ~1.31 | E-0017b | owner-approved official-code rerun | >=1.48065 |
| 2026-08-17 | A800 GPU-hours (Gemma official DEV attempt blocked at gated model auth; no generation) | ~0.00 | E-0017c | owner-approved Gemma official positive control | >=1.48065 |

- max_gpu_hours: TBD (human)
- max_api_cost: TBD (human)
- max_full_runs: TBD (human)
- max_pivot_count: 2 (then mandatory human review)

- E-0016 D-0095 authorized cap: 3 A800 GPU-hours; consumed upper bound 0.00722222 GPU-h before the valid pre-DEV failure. Retry is authorized under unchanged protocol/run commit `c094f07fa3592c2210f46caba9e69c49a5a92fad` with a remaining hard cap of 2.99277778 A800 GPU-hours; no retry has yet been performed.
