# REPORT — STRONG-vs-STRONG′ (non-degenerate NEGATIVE arm) positive control

**Experiment id:** `strong-negative-pc-c839e1c-20260813`
**Status:** GATED — `valid_for_paper=false`, `scientific_status=PENDING_HOSTILE_RESULT_AUDIT`
**Branch:** `feature/positive-control-strong-negative` · **Predeclaration:** `docs/research/2026-08-13-strong-negative-positive-control-predeclaration.md` (commit `2b64bb9`, precedes this result) · **Script commit:** `c839e1c`
**Hardware:** A800 GPU3 only (`CUDA_VISIBLE_DEVICES=3`), bfloat16, host `suzlab-a800`

This run blesses nothing, pushes nothing, merges nothing, and touched no frozen
artifact. On the host, `git diff --stat f5dd878..HEAD -- src data` (branch tip vs its
base) is **empty**; the only files my two commits add are the predeclaration and the
script. (`git diff main -- …` on the host is misleading because the host's `main`
checkout is an OLDER commit, 394954d, so it shows unrelated prior merges — the
correct base-relative diff is empty for `src`/`data`.)

---

## 1. Why this run exists (the single audit gap it closes)

A prior SOUND positive control (pc3, `feature/positive-control-noisy`, commit
`364ee43`) proved the frozen comparator-bound gate is **SATISFIABLE**: its POSITIVE
arm PASSED cleanly (Δ=0.600, CI[0.4453,0.7509], non-degenerate). But its NEGATIVE
arm was a **degenerate EXACT null** — both neutral baselines were uniformly 0.0, so
the contrast CI collapsed to `[0,0]`. A hostile audit flagged (MAJOR) that `[0,0]`
only demonstrates rejection of an **exact** null (zero per-item variance), not of a
**noisy / near-threshold** null.

This run adds a **NON-DEGENERATE NEGATIVE arm** so the discrimination claim is
genuinely stressed, and records the generation `finish_reason` + per-(item,sample)
seed in every raw row (closing pc3's UNVERIFIED note). Everything else reuses the
SOUND pc3 setup **exactly**.

## 2. Predeclared design (locked before any generation; commit `2b64bb9`)

- **Endpoint / scorer / budget (identical to pc3):** instruction *"answer in exactly
  two words"*; deterministic `exactly_two_words` = 1.0 iff whitespace-token-count
  == 2, else 0.0; `max_new_tokens = 32`; k=5; temperature 0.7; do_sample;
  **unsteered (α=0)**; model `Qwen/Qwen2.5-7B-Instruct`.
- **Conditions:** (i) **strong** instruction, base seed **20260723**; (ii) **neutral
  baseline A**, base seed **20260723** (paired with strong); (iii) **strong′** = the
  SAME strong instruction under an **INDEPENDENT** base seed **20260813**.
- **Item ids kept byte-identical to pc3** (`pc3-triviaqa-%05d`) so strong(i) and
  baselineA(ii) reproduce pc3 **bit-for-bit** — a built-in continuity cross-check.
- **Fresh pool:** first 80 TriviaQA `rc.nocontext` validation items with id-index
  ≥ 100 (`triviaqa-00100..00179`), the SAME verified-disjoint pool as pc3. Split
  `split_dev_test(dev=1/3, seed=20260723)` → 27 DEV / **53 TEST**; only TEST is
  adjudicated.
- **Contrasts through the UNMODIFIED frozen adjudicator** (`cluster_bootstrap_ci` /
  `axis_pass`; DELTA=0.05, CI level 0.983333, B=10000, bootstrap seed 20260723,
  item-cluster; coherence ceiling 1.5×baseline+0.02):
  - POSITIVE = strong − baselineA (expected **PASS**) — continuity with pc3.
  - **NON-DEGENERATE NEGATIVE** = strong − strong′ (expected **FAIL**) — same
    instruction, different seed → expected mean ≈ 0 with genuine per-item variance.
- **OPTIONAL sub-δ arm: OMITTED** (predeclared) — cannot be placed in the narrow
  (0, 0.05) band without tuning against outcomes, which the anti-gaming rule forbids.

## 3. Disjointness verification against the REAL frozen E-0006 artifact

Read directly from
`data/e0006_uncertainty_baseline/e0006_uncertainty_baseline.manifest.json` (ids) and
`...jsonl` (per-item prompt). The host jsonl file sha256
(`9c1e12ccef1659b9686688bd3d408dfc898ffc70d81d5fe0be783f2d979a4b2f`) **equals** the
manifest `artifact_sha256` (`manifest_matches_host_jsonl = True`), confirming the
genuine frozen artifact was read (not a re-sample).

| check | frozen E-0006 (n=80) | E-0012 (n=80) |
|---|---|---|
| id ∩ fresh pool | **[] (empty)** | [] (empty) |
| normalized-question-text-hash ∩ fresh pool | **[] (empty)** | [] (empty) |

Any overlap would have raised `SystemExit` before generation.

## 4. Results (all numbers from `strong_negative_pc_result.json`)

Per-condition compliance (mean over 53 TEST items × 5 samples):

| condition | compliance | per-item spread |
|---|---|---|
| (i) strong (seed 20260723) | **0.600** | 18 @0.0, 8 fractional, 27 @1.0; distinct {0.0,0.2,0.6,0.8,1.0} |
| (ii) baseline A (neutral, seed 20260723) | 0.000 | all 53 @0.0 |
| (iii) strong′ (SAME instr, indep seed 20260813) | **0.589** | 17 @0.0, 10 fractional, 26 @1.0; distinct {0.0,0.2,0.4,0.6,0.8,1.0} |

**Continuity cross-check:** strong (0.600) and baselineA (0.000) reproduce pc3
**exactly** (same seeds + item ids), so the POSITIVE arm is byte-identical to the
SOUND pc3 result. strong′ (0.589) is close to strong (0.600) — as expected for the
same instruction under a different seed.

### POSITIVE (strong − baselineA) — expected PASS

- mean_diff = **0.6000**; CI(0.983333) = **[0.4453, 0.7509]**, width 0.3057
- CI excludes 0 = **True**; mean ≥ δ(0.05) = **True**; coherence_ok = **True**
- per-item diff: std 0.4613, 5 distinct {0.0,0.2,0.6,0.8,1.0}, non-degenerate
- **=> PASS = True** (identical to pc3)

### NON-DEGENERATE NEGATIVE (strong − strong′) — expected FAIL

- mean_diff = **0.0113**; CI(0.983333) = **[−0.0302, 0.0528]**, **width 0.0830**
- CI excludes 0 = **False**; mean ≥ δ(0.05) = **False**; coherence_ok = True
- per-item diff: **std 0.1254, min −0.400, max +0.400, 5 distinct values
  {−0.4, −0.2, 0.0, 0.2, 0.4}, 9 nonzero**, `ci_is_degenerate_point = False`
- **`is_non_degenerate = True`** (CI width > 0 AND ≥ 3 distinct per-item diffs)
- **=> PASS = False** (gate correctly FAILS a NOISY null)

**Headline:** `rejects_noisy_null = True` (NEGATIVE fails AND its CI is genuinely
non-degenerate) and `gate_satisfiable_and_discriminative = True` (POSITIVE PASS ∧
NEGATIVE FAIL). This directly closes the pc3 audit MAJOR: the gate rejects a
**noisy** null (a proper interval `[−0.030, 0.053]` straddling 0 with per-item diffs
spanning −0.4→+0.4), not merely an exact `[0,0]`.

### finish_reason + seed provenance (closes pc3 UNVERIFIED)

Every raw row records `base_seed`, the derived per-(item,sample) `call_seed`, and
`finish_reason` (from the TRUE generated token ids). Distribution:

| condition | finish_reason counts |
|---|---|
| strong | 265 `stop` (short 2-word-ish replies, EOS before budget) |
| baselineA (neutral) | 254 `length` (hit 32-token budget), 11 `stop` |
| strong′ | 265 `stop` |

This confirms the strong instruction yields short EOS-terminated replies while the
neutral prompt runs to the token budget — and shows the budget=32 is not truncating
the compliant (2-word) replies. `eos_token_ids = [151645]` (`<|im_end|>`).

## 5. Interpretation, scope, and honest caveats

- The frozen gate **accepts a realistic prompt/instruction advantage** (POSITIVE, a
  proper CI in the interior) **and rejects a NOISY null** (NEGATIVE, a proper
  non-degenerate CI that straddles 0), on fresh, outcome-blind, verified-disjoint
  data. This is strictly stronger than pc3's discrimination evidence.
- **The negative arm is genuinely noisy, not exact.** Per-item diffs span
  −0.4→+0.4 with std 0.1254 and 5 distinct values; the bootstrap CI width is 0.083
  (vs pc3's 0.0). The gate still FAILS it because the mean (0.0113) is far below δ
  and the CI includes 0.
- **Scope (unchanged):** this demonstrates the gate recognizes a **prompt /
  instruction** effect and rejects a noisy null. It says **nothing** about a
  latent/steering-vector pass — that remains a separate, unmet burden. This is
  decision-machinery satisfiability + discrimination on a benign prompt-format
  effect, NOT latent/steering efficacy.

## 6. Provenance / compute

- Wall clock **301.2 s**; **GPU-hours ≈ 0.0837** (A800 GPU3 only; GPUs 0–2
  untouched; well under the 0.3 GPU-h cap).
- 795 raw generation records (3 conditions × 53 TEST items × 5 samples, incl.
  base_seed / call_seed / finish_reason / decoded text) → `raw_generations.jsonl`,
  **sha256 `08025f4890fa197c5d943380799562565698da33c0eaea8b6601f3ee79a363bf`**,
  stored in REPORT_STORE (see `raw_generations.POINTER.md`), NOT committed to git.
- `strong_negative_pc_result.json` (committed) carries every per-item outcome,
  per-item diff, spread stats, per-sample raw metadata (text stripped), disjointness
  proof, and frozen constants for independent recompute.
- Run once. No tuning, no retry, no endpoint swap. Every number comes from the
  script artifact.
