# PREREG — C2 Multi-seed Hardening (E-0011 family) — **DRAFT / Awaiting Manager freeze**

> **Status: DRAFT 2026-07-28** — Prepared by implement subagent.
> NOT frozen. Manager must review and explicitly set status to FROZEN before any run
> executes with E-0011 experiment IDs.
>
> This document DOES NOT modify, supersede, or touch:
> - `docs/ledgers/prereg-c2b-adjudication.md` (FROZEN 2026-07-23)
> - `docs/ledgers/prereg-robustness-mechanism-arm.md` (FROZEN 2026-07-24)
> - Evidence records E-0005, E-0006, or any result artifact under `results/arm_full/`
> - `src/cognitive_console/experiments/adjudicate_c2b.py` §4 judgment logic
>
> **Purpose:** Provide a pre-run specification for a multi-seed sensitivity analysis
> of the E-0006 result (NON_TRANSFER_GENERALIZED), so that if the negative holds
> across ≥4/5 seeds with consistent uncertainty harm, the "single-seed caveat"
> can be formally retired.

---

## 1. Motivation

E-0006 (arm_verdict=NON_TRANSFER_GENERALIZED, {CAA,ITI}×{Qwen,Llama}) used a single
seed (20260723). The honest caveat in the evidence ledger reads:
> "single model / single seed" (per E-0005) and "EXPLORATORY, valid_for_paper=false"
> for the arm (E-0006).

The remaining critic risk is seed sensitivity: a single draw for the DEV/TEST split,
item ordering, bootstrap resampling, and per-sample generation seeds means the
NON_TRANSFER verdict could (in principle) be artefactual for that one seed.

This multi-seed arm answers the question: **does the negative verdict hold across
different random seeds?** If yes (per the criteria in §4), the caveat "results
may reflect a particular seed choice" can be retired in the paper.

---

## 2. Design (pure reuse — NO protocol change)

**All adjudication logic is REUSED VERBATIM** from the frozen instrument:

- Decision rule: `adjudicate_c2b.py` §4 (paired item-cluster bootstrap, Bonferroni
  CI 1−0.05/3, δ=0.05, coherence gate ≤1.5×, three-tier verdict).
- Parameters: N=60/60/80, k=5, DEV/TEST 1:2, α grid {2,4,6,8,12,16,24}.
- Robustness matrix: same FROZEN 2×2 = {CAA,ITI}×{Qwen2.5-7B,Llama-3-8B},
  run via `scripts/run_arm_matrix.py --seed <SEED>`.
- Output per seed: one `arm_matrix_summary.json` + 4 `c2b_adjudication_results.json`.

**Only the `--seed` argument changes** across runs.  The seed affects:
1. DEV/TEST split (via `split_dev_test(..., seed=seed)` in `adjudicate_c2b.py`).
2. Per-sample generation RNG (via `BackendOutcomeSampler._call_seed` which hashes
   `f"{self.seed}|{axis}|{item_id}|{alpha}|{j}"`).
3. Bootstrap CI resampling (via `cluster_bootstrap_ci(..., seed=seed)`).
4. C1 direction extraction (CAA: `p0._extract_direction(..., seed=seed)`;
   ITI: `extract_iti(..., null_seed=seed)`).
5. Config fingerprint (seed is in `_config_fingerprint` payload → different seed
   = different fingerprint = fresh checkpoints, no cross-seed reuse).

**Seed propagation verdict (see §6):** seed IS fully threaded through all stochastic
components. No hardcoded seed bypasses were found. Changing `--seed` produces
genuinely independent runs with distinct DEV/TEST draws and generation RNG streams.

---

## 3. Proposed seed list (5 seeds, pre-run)

| seed | role |
|---|---|
| **20260723** | Baseline (must reproduce E-0006 byte-for-byte as harness correctness check) |
| **20260724** | Additional seed 2 |
| **20260725** | Additional seed 3 |
| **20260726** | Additional seed 4 |
| **20260727** | Additional seed 5 |

> **Harness correctness gate:** seed=20260723 MUST reproduce E-0006 results
> byte-for-byte (same arm_verdict=NON_TRANSFER_GENERALIZED, same 4-cell
> axis_passes all False, same mean(d) values within floating-point equality)
> before seeds 20260724–20260727 are analyzed. Any discrepancy terminates the
> run family and requires triage. This is a necessary but not sufficient condition
> for valid multi-seed evidence.

**Rationale for 5 seeds:**
- 5 seeds with a pre-specified threshold (≥4/5) gives a concrete, falsifiable rule
  that is decided before any new run.
- Seed spacing of +1 (days) is arbitrary but deterministic and easy to reproduce.
- No cherry-picking: all 5 seeds are enumerated here before any run.

---

## 4. Pre-registered aggregation criteria (PROPOSED — frozen by Manager before run)

The following success/failure branches are proposed. **They must be frozen
before any new seed is run.** Changing them after seeing results is not permitted.

### 4a. Single-seed caveat status ladder (frozen; Manager decision)

The aggregate emits one of four statuses:

1. **`KILL_HARNESS`** if seed=20260723 fails the E-0006 harness check (cannot
   reproduce the expected E-0006 anchor behavior).

2. **`DROP_SINGLE_SEED_CAVEAT`** (strict, primary criterion) iff **ALL** hold:
   - For all N seeds (N=5 including 20260723),
     `arm_verdict == NON_TRANSFER_GENERALIZED`.
   - For all 4 cells
     (caa__qwen2.5-7b, caa__llama3-8b, iti__qwen2.5-7b, iti__llama3-8b),
     uncertainty_awareness `ci_hi < 0` in all N seeds.
   - Guardrail: no seed×cell×axis may show PASS / strong-positive (all seeds
     must remain zero-pass with no axis crossing a success threshold).

3. **`SEED_MOSTLY_ROBUST`** (softened, but caveat retained) iff:
   - `arm_verdict == NON_TRANSFER_GENERALIZED` in ≥4/5 seeds;
   - each of the 4 cells has uncertainty_awareness `ci_hi < 0` in ≥3/5 seeds;
   - no strong-positive flip.

4. **`SEED_SENSITIVE`** (honest fail, caveat retained): all remaining cases.

For terminology stability, **`NON_TRANSFER_GENERALIZED` is taken directly from
the `run_arm_matrix.py` output field `arm_verdict`**. This DRAFT no longer uses
equivalent paraphrases such as "≥3/4 cells with 0/3 axes" as the decision key.

Outcome interpretation:
- Only `DROP_SINGLE_SEED_CAVEAT` authorizes removing the single-seed caveat.
- `SEED_MOSTLY_ROBUST` and `SEED_SENSITIVE` both retain caveat; the latter is
  the default honest-fail bucket.

---

### 4b. Anti-pooling clause for confirmatory negative judgment (mandatory)

**Any confirmatory negative judgment MUST be evaluated per-seed independently.**
The following is explicitly **prohibited**:

- Pooling raw outcome records from multiple seeds before computing a negative verdict.
- Computing `mean(d)` by averaging raw outcome values across seeds and using that
  aggregate mean to reach a negative conclusion.
- Using any cross-seed statistical summary (pooled CI, mean-across-seeds, etc.) as a
  sufficient condition for a negative judgment.

Each seed's `arm_verdict` and per-cell / per-axis pass/fail status MUST be derived
from that seed's own JSON artifacts, using the single-seed adjudicator
(`adjudicate_c2b.py §4`). The four-status ladder in §4a operates exclusively on
*per-seed verdict counts*, not on pooled statistics.

**Implementation note (pre-run check):** `aggregate_multiseed_c2.py` determines
`caveat_drop_rule` outcome by counting per-seed `arm_verdict == NON_TRANSFER_GENERALIZED`
and per-seed `ci_hi < 0` flags from each seed's own JSON.  The `mean_diff_across_seeds`
field in the output is **descriptive only** and is never used for verdict determination.
No pooling path exists in the aggregation logic; this was verified before writing this
document.

---

### 4c. Unconditional true-pass surfacing

If **any** seed × cell × axis combination shows a true PASS (`passed=True` in the
adjudication JSON for that seed), the aggregate output **must unconditionally and
prominently surface it**, regardless of the overall §4a outcome:

1. The output artifacts (`multiseed_c2_aggregate.json` and `.md`) must contain an
   **`any_true_pass`** block at the top level, listing each
   `(seed, cell_key, axis, mean_diff, ci_lo, ci_hi)` true pass.
   This block is **always present** (empty list if no passes occurred).

2. **If `any_true_pass` is non-empty:**
   - The `caveat_drop_rule.outcome` of `DROP_SINGLE_SEED_CAVEAT` and
     `SEED_MOSTLY_ROBUST` are **blocked** — a true positive in any
     seed × cell × axis prevents a clean caveat-drop decision.
   - Each affected cell must be flagged `single_seed_positive_surfaced = true` in
     `cell_axis_stats`, and the negative conclusion for that cell **must not** be
     labeled confirmatory.
   - The `.md` output must display a prominent warning at the top of the document.

3. The §4a "no strong-positive flip" guardrail already encodes the blocking logic.
   §4c makes the **disclosure obligation** explicit and independent: even if the final
   verdict is `SEED_SENSITIVE`, the individual passes must be surfaced for the paper
   record.

**Rationale:** Arithmetic averaging can obscure a single-seed positive signal.
A cell that shows a true pass in one seed cannot be collectively labeled "negative"
without explicit disclosure.  The `any_true_pass` block ensures such signals are
always visible in the paper audit trail, even when the headline verdict is
`SEED_SENSITIVE`.

---

## 5. Analysis script

`scripts/aggregate_multiseed_c2.py` — manifest-driven, reads all numbers from
JSON artifacts, zero hand-filling.

Input manifest format:
```json
[
  {"seed": 20260723, "arm_summary_json": "results/E-0011/seed_20260723/arm_matrix_summary.json"},
  {"seed": 20260724, "arm_summary_json": "results/E-0011/seed_20260724/arm_matrix_summary.json"},
  ...
]
```

Output: `multiseed_c2_aggregate.json` + `multiseed_c2_aggregate.md`.

The aggregation rule for `caveat_drop_rule` is implemented in
`aggregate_multiseed_c2.aggregate_across_seeds()` and matches §4a above
(`KILL_HARNESS` / `DROP_SINGLE_SEED_CAVEAT` / `SEED_MOSTLY_ROBUST` /
`SEED_SENSITIVE`).

Tests: `tests/test_aggregate_multiseed_c2.py` (includes dedicated coverage for
`DROP_SINGLE_SEED_CAVEAT` / `SEED_MOSTLY_ROBUST` / `SEED_SENSITIVE` /
`KILL_HARNESS`).

---

## 6. Seed-propagation audit (implementation check)

**Traced through the codebase before writing this document.**

### Seed transmission path in `run_arm_matrix.py`
```
main(args)
  └─ _build_single_cell_argv(args, cell, cell_dir)
       └─ ["--seed", str(args.seed)]   # ← seed forwarded to each cell
  └─ single.main(cell_argv)            # = run_c2b_adjudication.main()
```

### Seed use sites in `run_c2b_adjudication.py` / `adjudicate_c2b.py`

| Site | Function | Effect |
|---|---|---|
| DEV/TEST split | `split_dev_test(item_ids, seed=seed)` | Item-level RNG; different seed → different DEV/TEST draw → independent adjudication |
| C1 direction (CAA) | `p0._extract_direction(..., seed=seed)` | Extraction split; direction varies per seed |
| C1 direction (ITI) | `extract_iti(..., null_seed=seed)` | Null distribution for ITI probe; varies per seed |
| Per-sample generation seed | `BackendOutcomeSampler._call_seed(axis, item, alpha, j)` hashes `f"{self.seed}|..."` | Every generation sample has a seed derived from run seed; changing seed changes all samples |
| Bootstrap CI | `cluster_bootstrap_ci(..., seed=seed)` | Bootstrap resample RNG; different seed → different CI realization (same width in expectation) |
| Config fingerprint | `_config_fingerprint(...)` includes `"seed": int(args.seed)` | Different seed → different fingerprint → no checkpoint reuse across seeds |

**Verdict: No hardcoded seed bypasses found.** The `--seed` argument is fully
propagated through all stochastic components. Each seed produces a genuinely
independent run with a different DEV/TEST split, different per-item generation
seeds, and a different bootstrap resample. Changing `--seed` from 20260723 to
20260724–20260727 will produce meaningfully different (not just re-ordered) results.

**One important nuance:** The per-axis items themselves (the task items, e.g., GSM8K
questions) are loaded from a fixed dataset and only their DEV/TEST assignment varies
by seed. The item pool is the same across seeds (first N items per axis cap). This
is correct behavior — we want to vary the split, not the items — but it means all
5 seeds adjudicate on the same underlying task distribution (not independent item
draws from a larger pool). This is a scope limitation that should be noted.

---

## 7. Generation budget and compute estimate

### Per-seed generation counts (from `_planned_generations_per_axis`)

| axis | N_total | n_dev | n_test | dev_gens | test_gens | subtotal |
|---|---|---|---|---|---|---|
| deliberation | 60 | 20 | 40 | 2400 | 1000 | **3400** |
| skepticism | 60 | 20 | 40 | 2400 | 1000 | **3400** |
| uncertainty_awareness | 80 | 27 | 53 | 3240 | 1325 | **4565** |
| **per-cell total** | | | | | | **11,365** |

_(dev_gens = k × n_dev × (n_strong + 1 baseline + 7 alpha) = 5 × 20 × 24 = 2400;
test_gens = k × n_test × 5 channels = 5 × 40 × 5 = 1000)_

| Scope | Generation count |
|---|---|
| 1 cell | 11,365 |
| 1 seed (4 cells) | 45,460 |
| 5 seeds (4 cells × 5) | **227,300** |

### Compute time estimate (A800 80GB)

Based on E-0006 actual run (~29 min/cell on rented RTX4080S).
A800 is meaningfully faster; conservative estimate 15–20 min/cell:

| Scenario | Time per cell | Per seed (4 cells) | 5 seeds total |
|---|---|---|---|
| Optimistic (A800 15 min/cell) | 15 min | 60 min | **5.0 h** |
| Conservative (A800 20 min/cell) | 20 min | 80 min | **6.7 h** |
| E-0006 baseline (RTX4080S 29 min/cell) | 29 min | 116 min | **9.7 h** |

**Recommendation:** budget 7–10 h of A800 GPU time for 5 seeds.
Disk: 5 × (E-0006 used ~37 GB) ≈ 185 GB raw; checkpoints can be wiped after
each seed is verified and the result JSON is pushed. Peak concurrent: ~37 GB
per seed (1 seed at a time) → within A800 budget cap.

**Owner decision required (§5):** GPU rental sign-off before any run. This is
the same class of expenditure as E-0006 (low tens of RMB per GPU hour on
rented box), but 5× the number of seeds.

---

## 8. Experiment family

- **Experiment IDs:** E-0011 family (E-0011a through E-0011e for seeds
  20260723–20260727 respectively; E-0011-agg for the aggregate).
- **hypothesis_id:** H2 (same as E-0005/E-0006).
- **claim_ids:** ["C2"] (same as E-0006).
- **valid_for_paper:** false until frozen + hostile audit.
- **Does NOT overwrite:** E-0005, E-0006, or any frozen record.

---

## 9. Questions for Manager before freeze

1. **Seed list confirmed?** The proposed 5 seeds (20260723–20260727) are the
   simplest non-cherry-picked choice. Manager may substitute others, but ALL
   seeds must be listed here before any run.

2. **Aggregation thresholds confirmed?** The proposed rules (strict all-5 for
   caveat drop; 4/5 + 3/5 for mostly-robust; otherwise seed-sensitive) are
   proposed pre-run. Manager may
   adjust these thresholds, but they must be frozen before seeing any new result
   beyond E-0006 (seed 20260723).

3. **GPU budget sign-off?** ~7–10 h of A800 time = §5 owner-gated item.
   Manager may not schedule the GPU run without owner approval.

4. **Is seed=20260723 re-run truly necessary?** Option A: skip it (accept E-0006
   as the seed-20260723 data point, count it as 1/5). Option B: re-run it
   independently to verify bit-exact reproduction as a harness check. Option B
   is more rigorous but doubles the seed-20260723 GPU cost. Manager should decide.

---

## 10. Freeze block (to be filled by Manager)

- protocol_frozen: **NO — DRAFT, awaiting Manager review and owner GPU sign-off**
- freeze_date: (TBD)
- freeze_decision_id: (TBD)
- seeds_frozen: (TBD)
- aggregation_thresholds_frozen: (TBD)
