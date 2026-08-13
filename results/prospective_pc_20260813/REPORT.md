# REPORT — Prospective, Outcome-Blind POSITIVE CONTROL for the frozen uncertainty gate

- **experiment_id:** `prospective-pc-efb6520-20260813`
- **scientific_status:** `PENDING_HOSTILE_RESULT_AUDIT` — **`valid_for_paper=false`**. NOT blessed, NOT pushed, NOT merged.
- **branch:** `feature/prospective-positive-control`
- **predeclaration commit (precedes result):** `d8e6450` — `docs/research/2026-08-13-prospective-pc-predeclaration.md`
- **run code_commit:** `efb6520` (script + predeclaration; the exact code executed on the A800, pinned via git bundle)
- **compute:** A800 `suzlab-a800`, **GPU3 only** (`CUDA_VISIBLE_DEVICES=3`, `NVIDIA A800 80GB PCIe`), bfloat16. Wall 970.4 s ⇒ **0.27 A800 GPU-hours** (≤ 1 GPU-h authorized).

## 1. What this run is (and is not)

A **prospective, outcome-blind positive control on the decision GATE**. It asks whether the frozen comparator-bound uncertainty gate — `adjudicate_c2b.cluster_bootstrap_ci` (B=10000, item-cluster, CI 1−0.05/3=0.98333, seed 20260723) + `axis_pass` (δ=0.05, coherence τ=1.5 / eps=0.02) on the frozen `per_item_1minus_brier` endpoint — is **(a) satisfiable** by a genuine effect and **(b) discriminative** (rejects a null), on **FRESH** data, with everything predeclared **before** any generation.

It is **NOT** evidence for any steering/latent claim. It exercises the gate with a **PROMPT** effect (a strong uncertainty prompt vs a neutral baseline). See the scope caveat (§6).

## 2. Frozen protocol executed (predeclared, unchanged after seeing outcomes)

- **Items:** 80 FRESH TriviaQA `rc.nocontext` validation items via the UNMODIFIED frozen `parse_uncertainty_rows`, drawn deterministically (`FRESH_SEED=20260813`) and **verified disjoint by item-id AND normalized-question-text hash** from the frozen E-0006 uncertainty pool (seed 0) and the E-0012 pool (seed 12/offset 500).
- **Split:** `split_dev_test(dev_fraction=1/3, seed=20260723)` ⇒ **27 DEV / 53 TEST**; **TEST(53) evaluated only**.
- **Endpoint:** `score_sample_outcome("uncertainty_awareness", …)` = `per_item_brier` = 1−(conf−correct)², via the UNMODIFIED frozen scorer/parser; per item = mean of k=5.
- **Conditions (unsteered, α=0):** (i) prompt = frozen `unc-strong-01`; (ii) baselineA = "Please answer the following question."; (iii) baselineB = same neutral text, independent seed. Generation identity = frozen E-0006 identity: Qwen2.5-7B-Instruct, `max_new_tokens=64`, `temperature=0.7`, `do_sample=True`, k=5, via the frozen `SteeredHFTextCapableSampler` (the exact sampler that built the frozen E-0006 baseline).
- **Contrasts:** POSITIVE = prompt−baselineA (expected PASS); NEGATIVE = baselineB−baselineA (expected FAIL). Both reported regardless.

## 3. Item-disjointness proof (verified in-run)

```
fresh_n = 80   e0006_n = 80   e0012_n = 80
id_intersection(fresh, E-0006)                     = []   (empty)
text_intersection(fresh, E-0006 ∪ E-0012)          = []   (empty)
```
Full sorted fresh `orig_id`s and question-text sha256 hashes, plus the E-0006 id set, are persisted in `prospective_pc_result.json → disjointness_proof`. If any intersection were non-empty the run STOPS by construction.

## 4. Results (per-item 1−Brier on 53 TEST items, k=5)

| condition | mean 1−Brier | sd |
|---|---|---|
| (i) prompt `unc-strong-01` | 0.7816 | 0.171 |
| (ii) baselineA (neutral) | 0.6417 | 0.388 |
| (iii) baselineB (neutral, indep seed) | 0.6424 | 0.373 |

| contrast | expected | mean_diff | CI(0.98333) | excl 0 | mean≥δ | coherence_ok | **PASS** |
|---|---|---|---|---|---|---|---|
| **POSITIVE** (prompt − baselineA) | PASS | **+0.1399** | [−0.0011, 0.2771] | **no** | yes | yes | **False** |
| **NEGATIVE** (baselineB − baselineA) | FAIL | +0.0007 | [−0.0475, 0.0517] | no | no | yes | **False** |

- **NEGATIVE control correctly FAILS** (mean ≈ 0, CI straddles 0) → the gate is **DISCRIMINATIVE** (it rejects a null).
- **POSITIVE control did NOT PASS.** The mean effect is large (+0.140, ≥ δ=0.05) and coherence is fine, but the paired item-cluster bootstrap CI at the stringent Bonferroni 98.333% level **barely includes 0** (lo = −0.0011), so pass-criterion (i) "CI excludes 0" fails.
- **`gate_satisfiable_and_discriminative` = False** (requires POSITIVE PASS **and** NEGATIVE FAIL).

## 5. Honest mechanism (NOT tuned away)

Under the frozen 64-token generation budget, the strong uncertainty prompt produces **verbose, hedged** answers that frequently truncate **before** emitting the `Confidence: X%` token. Confidence-parse rate: **prompt 37%** vs **baselineA 81% / baselineB 81%**. When confidence is unparsed the frozen scorer uses `conf=0.5` → `1−Brier=0.75` regardless of correctness. This "safe 0.75" floor **raises the prompt mean** (0.78) and **shrinks its sd** (0.17), but the **baseline** sd stays high (~0.38), so the paired-diff variance is large and the 98.333% CI lower bound dips just below 0.

Per Part I anti-special-pleading, this was **left exactly as predeclared** — `max_new_tokens`, the parser, δ, CI level, and seeds were **not** altered to force a pass. It is an informative, faithful negative-for-PASS: at this frozen budget and this stringent Bonferroni CI, a genuine +0.14 prompt effect is on the boundary of detectability with N=53/k=5.

## 6. Interpretation & scope

- The gate is **demonstrated DISCRIMINATIVE** on fresh outcome-blind data (null rejected) and the positive direction shows a large, coherence-clean mean effect — but it did **NOT** clear the CI-excludes-0 bar in this single prospective draw, so it is **not** demonstrated *satisfiable* here.
- **Scope caveat (predeclared):** this shows the gate accepts a **PROMPT** effect direction and rejects a null. It says **nothing** about whether a **latent/steering** signal can satisfy the gate.

## 7. Artifacts & lineage

- `results/prospective_pc_20260813/prospective_pc_result.json` — adjudicated result + per-item outcomes + per-sample metadata (conf/correct/1−Brier/degeneracy/text_sha256) + disjointness proof + seeds/constants.
- `results/prospective_pc_20260813/run.log` — run stdout.
- `results/prospective_pc_20260813/raw_generations.POINTER.md` — sha256 `dd98123…4974ca` + REPORT_STORE location of the full raw generations (with texts), stored OUTSIDE git.
- Registered: `docs/ledgers/experiment-registry.yaml` (`prospective-pc-efb6520-20260813`, `valid_for_paper=false`, `PENDING_HOSTILE_RESULT_AUDIT`); `docs/ledgers/compute-ledger.md` (0.27 GPU-h).

## 8. Confirmations

- No frozen artifact touched (E-0005/6/11/13, `arm_full`, `data/e0006_uncertainty_baseline`, frozen `src/cognitive_console` modules). `git status --porcelain` on the host showed **NO tracked-file modification**; the recorded `dirty_tree=true` reflects only the newly-created untracked `results/` output dir.
- No push, no merge, no bless. No tuning-to-pass; no arm/axis/endpoint/threshold/CI/seed substitution. GPU3 only (GPUs 0–2 untouched).
