# REPORT — NOISY (non-degenerate) positive control for the frozen comparator-bound gate

**Experiment id:** `noisy-pc-f16ce51-20260813`
**Status:** GATED — `valid_for_paper=false`, `scientific_status=PENDING_HOSTILE_RESULT_AUDIT`
**Branch:** `feature/positive-control-noisy` · **Predeclaration:** `docs/research/2026-08-13-noisy-positive-control-predeclaration.md` (commit `0573a78`, precedes this result)
**Script commit:** `f16ce51` · **Hardware:** A800 GPU3 only (`CUDA_VISIBLE_DEVICES=3`), bfloat16

This run blesses nothing, pushes nothing, merges nothing, and touched no frozen
artifact (`git diff main -- src` and `git diff main -- data` are both empty; the
host `git status --porcelain` showed no tracked-file modification).

---

## 1. Why this run exists

A hostile audit REJECTED two prior positive-control attempts for the claim that the
frozen gate is *satisfiable + discriminative*:

1. an **uncertainty-endpoint** attempt — confounded (confidence-parseability ×
   64-token truncation) AND its "fresh" pool was not verified disjoint from the
   ACTUAL frozen E-0006 pool (it reconstructed E-0006 by a re-sample instead of
   reading the real manifest);
2. a **prefix-compliance ("ANSWER:")** attempt — PASSED but was a STRAW control:
   every positive diff was exactly 1.0 and every negative exactly 0.0, so the
   bootstrap CI collapsed to `[1,1]` / `[0,0]` with **no realistic variance**.

This run fixes BOTH: (A) real disjointness verified against the actual frozen
artifact with a hard-fail on any overlap, and (B) a **non-degenerate, noisy**
endpoint whose per-item compliance is fractional so the bootstrap CI is a proper
interval.

## 2. Predeclared design (locked before any generation)

- **Endpoint:** instruction *"answer in exactly two words"*; deterministic scorer
  `exactly_two_words` = 1.0 iff whitespace-token-count == 2, else 0.0.
- **Token budget:** 32 (not truncation-confounded). **k=5**, temperature 0.7,
  do_sample, **unsteered (α=0)**.
- **Conditions:** (i) strong instruction; (ii) neutral baseline A; (iii) neutral
  baseline B (independent seed 20260724; A/strong share seed 20260723 — paired).
- **Fresh pool:** first 80 TriviaQA `rc.nocontext` validation items with id-index
  ≥ 100 (`triviaqa-00100..00179`). Split `split_dev_test(dev=1/3, seed=20260723)`
  → 27 DEV / **53 TEST**; only TEST is adjudicated.
- **Contrasts through the UNMODIFIED frozen adjudicator** (`cluster_bootstrap_ci` /
  `axis_pass`; DELTA=0.05, CI level 0.983333, B=10000, bootstrap seed 20260723,
  item-cluster; coherence ceiling 1.5×baseline+0.02):
  - POSITIVE = strong − baselineA (expected PASS)
  - NEGATIVE = baselineB − baselineA (expected FAIL)

## 3. Disjointness verification against the REAL frozen E-0006 artifact

Read directly from `data/e0006_uncertainty_baseline/e0006_uncertainty_baseline.manifest.json`
(item ids) and `...jsonl` (per-item prompt); the jsonl file sha256 on the host
(`9c1e12ccef16...`) **equals the manifest `artifact_sha256`**, confirming the
genuine frozen artifact was read (not a re-sample).

| check | frozen E-0006 (n=80) | E-0012 (n=80) |
|---|---|---|
| id intersection with fresh pool | **[] (empty)** | [] (empty) |
| normalized-question-text-hash intersection | **[] (empty)** | [] (empty) |

Fresh pool ids `triviaqa-00100..00179` are disjoint from E-0006 (indices 0–79) and
E-0012 (offset 500) by construction, AND verified empty by id + text hash. Any
overlap would have raised `SystemExit` before generation.

## 4. Results (all numbers from `noisy_pc_result.json`)

Per-condition compliance (mean over 53 items × 5 samples):

| condition | compliance rate | per-item spread |
|---|---|---|
| (i) strong = exactly-two-words | **0.600** | 18 items @0.0, 8 fractional (0.2/0.6/0.8), 27 @1.0; distinct {0.0, 0.2, 0.6, 0.8, 1.0} |
| (ii) baseline A (neutral) | 0.000 | all 53 @0.0 |
| (iii) baseline B (neutral, indep seed) | 0.000 | all 53 @0.0 |

Strong compliance (0.600) landed inside the predeclared noisy band [0.55, 0.90];
baseline (0.000) is below the predeclared ≤0.3 — as designed, NOT ~1.0.

### POSITIVE (strong − baselineA) — expected PASS

- mean_diff = **0.6000**; CI(0.983333) = **[0.4453, 0.7509]**, width **0.3057** (a
  proper interval, NOT the `[1,1]` collapse of the straw control)
- CI excludes 0 = **True**; mean ≥ δ(0.05) = **True**
- per-item diff: std **0.4613**, **5 distinct values** {0.0, 0.2, 0.6, 0.8, 1.0},
  `ci_is_degenerate_point = False`
- coherence_ok = **True** (treat_deg 0.0000 ≤ ceiling 0.0252)
- **=> PASS = True**, and `positive_non_degenerate = True`

### NEGATIVE (baselineB − baselineA) — expected FAIL

- mean_diff = **0.0000**; CI(0.983333) = **[0.0000, 0.0000]**, width 0.0
- CI excludes 0 = False; mean ≥ δ = False
- **=> PASS = False** (correctly rejects the null)

**`gate_satisfiable_and_discriminative = True`** (POSITIVE PASS ∧ NEGATIVE FAIL).

## 5. Interpretation, scope, and honest caveats

- The frozen gate **accepts a realistic, noisy prompt/instruction advantage** (a
  proper CI well inside the interior, not a degenerate point) **and rejects a
  null** — on fresh, outcome-blind, verified-disjoint data. This directly answers
  the audit's BLOCKER B1 (satisfiable + discriminative, non-trivially).
- **Non-degeneracy is real but concentrated in the strong arm.** The bootstrap CI
  is non-degenerate because the strong condition's per-item compliance genuinely
  varies (8/53 items are fractional across the k=5 samples; the rest split 18 zeros
  / 27 ones), giving per-item diffs spanning 0.0→1.0 with 5 distinct values and
  std 0.46. The neutral baselines are uniformly 0.0 (a neutral prompt essentially
  never yields exactly two words), so the null contrast is a true `[0,0]`. This is
  the *correct* behavior of a genuine null, and it is materially different from the
  rejected straw control, whose **positive** arm was the degenerate `[1,1]`.
- **Scope (unchanged):** this demonstrates the gate recognizes a **prompt /
  instruction** effect and rejects a null. It says **nothing** about a
  latent/steering-vector pass — that remains a separate, unmet burden.

## 6. Provenance / compute

- Wall clock **473.4 s**; **GPU-hours ≈ 0.1315** (A800 GPU3 only; GPUs 0–2 untouched;
  well under the 0.5 GPU-h cap).
- 795 raw generation records (3 conditions × 53 items × 5 samples) →
  `raw_generations.jsonl`, **sha256 `0b29eebf45eec37d3cc7507f12d19246ce20cfb8ff92eb4e1a404c8e549aad8d`**,
  stored in REPORT_STORE (see `raw_generations.POINTER.md`), NOT committed to git.
- `noisy_pc_result.json` (committed) carries every per-item outcome, per-item diff,
  spread stats, disjointness proof, and frozen constants for independent recompute.
