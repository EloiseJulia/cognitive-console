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

- E-0016 D-0095 authorized cap: 3 A800 GPU-hours; consumed upper bound 0.00722222 GPU-h before the valid pre-DEV failure. Retry is authorized under unchanged protocol/run commit `c094f07fa3592c2210f46caba9e69c49a5a92fad` with a remaining hard cap of 2.99277778 A800 GPU-hours; no retry has yet been performed.
- E-0017 deliberation token-cap sensitivity is **planned, not run, and not
  authorized here**. Estimate: 7,200 continuations, at most 1,075,200
  continuation-token slots, four direction/model passes, and full SHA-256 reads
  of both pinned model snapshots before generation. Runtime is restricted to
  exactly one owner-approved UUID-selected NVIDIA A800 in CUDA float16, with no
  CPU fallback, and an authorization cap of at most 3 A800 GPU-hours enforced
  at every fixed batch/milestone. **Authorized amount remains 0 GPU-hours**
  until an independent re-audit recommends FREEZE and owner `EloiseJulia`
  issues the commit/GPU-UUID/canonical-attempt authorization.
