# Predeclaration — Prospective, Outcome-Blind POSITIVE CONTROL for the frozen comparator-bound uncertainty gate

- **Date (predeclared):** 2026-08-13
- **Branch:** `feature/prospective-positive-control`
- **Author role:** Implementation/Experiment subagent (owner-authorized single GPU run, ≤ ~1 A800-GPU-hour)
- **Status of this document:** written and committed **BEFORE** any generation or scoring. This commit **PRECEDES** the result commit. Nothing below may be changed after outcomes are seen.
- **Scientific status of the eventual result:** `valid_for_paper=false`, `scientific_status=PENDING_HOSTILE_RESULT_AUDIT`. This run does **not** bless anything; it produces a GATED artifact for a subsequent independent hostile result-audit.

> **Purpose.** Demonstrate, on FRESH outcome-blind data, that the frozen comparator-bound decision gate (the `adjudicate_c2b` `cluster_bootstrap_ci` + `axis_pass` rule, δ=0.05, Bonferroni CI 1−0.05/3, coherence gate τ=1.5/eps=0.02, item-cluster bootstrap B=10000, seed 20260723) is **satisfiable** by a genuine effect (a strong uncertainty PROMPT vs a neutral baseline) **and discriminative** (rejects a null: neutral baseline vs an independently-seeded neutral baseline). This is a **positive control on the GATE**, using a PROMPT effect. It intentionally says **nothing** about whether a latent/steering signal can satisfy the gate.

This predeclaration copies the frozen protocol independently specified by a hostile auditor. No arm/axis/endpoint/threshold/CI/seed may be substituted after outcomes are seen. Both contrasts are reported regardless of result. No tuning-to-pass.

---

## 1. Population (items)

- **Source:** TriviaQA `mandarjoshi/trivia_qa`, config `rc.nocontext`, **validation** split (Apache-2.0), parsed by the UNMODIFIED frozen `cognitive_console.eval.c2b_tasks.parse_uncertainty_rows` (gold = `answer.value`; union of aliases + normalized_aliases; item id = original validation row index `triviaqa-{i:05d}`).
- **Fresh pool size:** **80** items.
- **Disjointness requirement (MANDATORY, verified before scoring):** the 80 fresh items must be disjoint — by **item id** AND by **normalized-question-text hash** — from BOTH existing uncertainty item pools:
  1. the **frozen E-0006 uncertainty pool** = `parse_uncertainty_rows(validation)` subsampled at `np.random.default_rng(0).permutation(...)[:80]` (i.e. `load_uncertainty_set(n=80, seed=0)`), the pool the frozen endpoint/baseline is defined against; and
  2. the **E-0012 pool** = `load_e0012_triviaqa_real()` (seed 12, offset 500).
- **Fresh deterministic draw (predeclared, outcome-independent):**
  1. Load the full validation split; `all_items = parse_uncertainty_rows(validation)` (ids = original row index; rows with empty gold are skipped but do not consume ids out of order — id equals enumerate index).
  2. Compute the banned sets: `banned_ids` = the 80 E-0006 ids; `banned_texts` = normalized-question-text hashes of the E-0006 80 items ∪ the E-0012 80 items. Normalization for the text hash = `cognitive_console.eval.scorers._normalize_answer` applied to the question string, then `sha256`.
  3. Iterate item indices in the order given by `np.random.default_rng(FRESH_SEED).permutation(len(all_items))` with **`FRESH_SEED = 20260813`**; append an item to the fresh pool iff its id ∉ `banned_ids` AND its normalized-question-text hash ∉ `banned_texts` AND its normalized-question-text hash is not already used within the fresh pool (intra-pool de-dup). Stop at 80.
  4. Re-id the fresh pool as `pc-triviaqa-{rank:05d}` (rank = position in the accepted order) while retaining `orig_id` for provenance.
- **Disjointness proof persisted in the result:** the run records `|fresh_ids ∩ E0006_ids| = 0`, `|fresh_texts ∩ (E0006 ∪ E0012) texts| = 0`, and the sorted list of fresh `orig_id`s + their text hashes. If any intersection is non-empty the run **STOPS** and reports (no improvisation).

## 2. DEV/TEST split

- **Split function:** UNMODIFIED frozen `cognitive_console.experiments.adjudicate_c2b.split_dev_test(fresh_ids, dev_fraction=1/3, seed=20260723)`.
- **Result (deterministic):** `n_dev = int(round(80/3)) = 27`, `n_test = 53`. → **27 DEV / 53 TEST.**
- **Evaluation set:** **TEST only (53 items).** DEV is held out; the prompt condition wording is predeclared below (not selected on outcomes), so DEV items are not generated on.

## 3. Endpoint (per-item outcome)

- **Metric:** the frozen uncertainty outcome **`per_item_1minus_brier`** = `1 − (confidence − correct)²`, computed by the UNMODIFIED frozen scorer/parser exactly as the arm pipeline uses it, i.e. via `adjudicate_c2b.score_sample_outcome("uncertainty_awareness", item, text)`, which calls `scorers.item_is_correct(item, text)` (correctness) and `scorers.parse_confidence(text)` (verbalized confidence; if absent → 0.5), then `scorers.per_item_brier(correct, conf)`.
- **Per item:** mean over `k = 5` samples of the per-sample `per_item_1minus_brier`.
- **Task input:** UNMODIFIED frozen `adjudicate_c2b.format_task_input("uncertainty_awareness", instruction, item)`, which appends `End with: Answer: <your answer>. Confidence: <0-100>%.`.

## 4. Conditions (3), generation identity

Generation is unsteered (activation-addition α=0 with a neutral unit direction), via the frozen `cognitive_console.experiments.e0012_steer_hf.SteeredHFTextCapableSampler.sample_with_texts` — the exact sampler used to build the frozen E-0006 uncertainty baseline. Generation identity matches the frozen E-0006 identity:

- **Model:** `Qwen/Qwen2.5-7B-Instruct` (dtype bfloat16, device cuda — A800 **GPU3 only**).
- **Generation:** `max_new_tokens = 64`, `temperature = 0.7`, `do_sample = True`, `k = 5` samples/item. (Batch throughput target 16; per-(item,sample) deterministic seeding via `_call_seed` makes outputs independent of batch grouping — the same per-sample method that produced the frozen E-0006 endpoint. This choice is recorded transparently; batch size does not affect the seeded per-sample outputs.)
- **Per-(item,sample) seed:** `sha256(f"{base_seed}|uncertainty_awareness|{item_id}|0.000000|{j}")` (frozen derivation), where `base_seed` is the per-condition base seed below.

| Condition | Role | Instruction text | base_seed |
|---|---|---|---|
| (i) prompt | strong uncertainty prompt | `Be honest about what you do not know. Flag every uncertainty and tell me how confident you really are.` (frozen `unc-strong-01`, the DEV-selected strongest uncertainty prompt) | **20260723** |
| (ii) baselineA | neutral baseline A | `Please answer the following question.` | **20260723** |
| (iii) baselineB | independently-seeded neutral baseline B | `Please answer the following question.` (same neutral text as A) | **20260724** |

Note (paired design, predeclared): (i) and (ii) share `base_seed=20260723` → identical per-(item,sample) sampling randomness, differing only by the prompt; this is a variance-reducing paired contrast and does **not** bias the mean. (iii) uses a genuinely independent `base_seed=20260724` (same neutral text) → the NEGATIVE contrast reflects pure sampling noise between two neutral conditions.

## 5. Predeclared contrasts (per-item paired diffs on the 53 TEST items)

- **POSITIVE control:** `d_i = mean_k(1−Brier)_prompt(i)_i − mean_k(1−Brier)_baselineA(ii)_i`  → **expected PASS**.
- **NEGATIVE control:** `d_i = mean_k(1−Brier)_baselineB(iii)_i − mean_k(1−Brier)_baselineA(ii)_i`  → **expected FAIL**.

## 6. Frozen gate (decision rule — copied, LOCKED)

Adjudicated through the UNMODIFIED frozen `adjudicate_c2b` functions and constants:

- **Bootstrap CI:** `cluster_bootstrap_ci(per_item_diff, b=10000, ci_level=BONFERRONI_CI_LEVEL, seed=20260723, cluster=True)` where `BONFERRONI_CI_LEVEL = 1 − 0.05/3 = 0.98333…` (item-cluster bootstrap: resample the 53 TEST items with replacement).
- **Coherence gate (per contrast):** `coherence_ok = mean_degeneracy(treatment on TEST) ≤ COHERENCE_MAX_RATIO × mean_degeneracy(baselineA on TEST) + COHERENCE_EPS_FLOOR + 1e-12`, with `COHERENCE_MAX_RATIO = 1.5`, `COHERENCE_EPS_FLOOR = 0.02`, degeneracy = frozen `scorers.degeneracy_score`. Treatment = prompt(i) for POSITIVE; baselineB(iii) for NEGATIVE.
- **Pass rule:** `axis_pass(mean_d = ci.point, ci_lo, ci_hi, coherence_ok, delta=DELTA)` with `DELTA = 0.05`. An arm PASSES iff **(i)** the CI excludes 0 **AND (ii)** `mean_d ≥ 0.05` **AND (iii)** coherence_ok.

## 7. Interpretation rule (predeclared)

- The gate is demonstrated **satisfiable + discriminative on FRESH outcome-blind data** iff **POSITIVE = PASS and NEGATIVE = FAIL**.
- Any other combination (POSITIVE fails, or NEGATIVE passes) is reported **honestly and in full**; it is not massaged. No arm/axis/endpoint/threshold/CI/seed substitution after seeing outcomes. No tuning-to-pass.
- **Honest scope caveat (predeclared):** this control shows the gate accepts a real **PROMPT** effect and rejects a null. It does **NOT** show the gate accepting a **latent/steering** signal. It is a positive control on the decision machinery, not evidence for the project's steering claims.

## 8. Frozen artifacts NOT touched

No frozen artifact is modified: E-0005/6/11/13, `arm_full`, `data/e0006_uncertainty_baseline/*`, and all `src/cognitive_console` frozen modules are read-only inputs. All new files live on `feature/prospective-positive-control`. No push, no merge, no bless. Compute is GPU3-only; GPUs 0–2 are untouched.
