# Predeclaration — Prospective, Outcome-Blind POSITIVE CONTROL on a CONFOUND-FREE endpoint (frozen comparator-bound gate)

- **Date (predeclared):** 2026-08-13
- **Branch:** `feature/positive-control-clean`
- **Author role:** Implementation/Experiment subagent (owner-authorized single GPU run, ≤ ~0.5 A800-GPU-hour, A800 **GPU3 only**)
- **Status of this document:** written and committed **BEFORE** any generation or scoring. This commit **PRECEDES** the script and the result commits. Nothing below may be changed after outcomes are seen.
- **Scientific status of the eventual result:** `valid_for_paper=false`, `scientific_status=PENDING_HOSTILE_RESULT_AUDIT`. This run does **not** bless anything; it produces a GATED artifact for a subsequent independent hostile result-audit.

> **Purpose.** Demonstrate, on FRESH outcome-blind data, that the frozen comparator-bound decision gate (the `adjudicate_c2b` `cluster_bootstrap_ci` + `axis_pass` rule: δ=0.05, Bonferroni CI level 1−0.05/3=0.98333…, coherence gate τ=1.5 / eps=0.02, item-cluster bootstrap B=10000, seed 20260723) is **satisfiable** by a genuine, robustly auto-scored behavioral effect (a strong instruction PROMPT vs a neutral baseline) **and discriminative** (rejects a null: neutral baseline vs an independently-seeded neutral baseline). This is a **positive control on the GATE**, using a PROMPT effect. It intentionally says **nothing** about whether a latent/steering signal can satisfy the gate.

## 0. Why a new endpoint (motivation, predeclared)

A prior prospective positive control on the frozen **uncertainty** endpoint (branch `feature/prospective-positive-control`, `prospective-pc-efb6520-20260813`) was **DISCRIMINATIVE** (NEGATIVE correctly FAILED) but its **POSITIVE** arm **narrowly MISSED** PASS: mean_diff = +0.1399 with the 98.333% CI = [−0.0011, 0.2771], i.e. the CI lower bound dipped 0.0011 below 0. The documented root cause is a **confidence-parseability × truncation confound**: under the frozen 64-token budget the strong uncertainty prompt produces verbose, hedged answers that frequently **truncate before** emitting the `Confidence: X%` token, so only ~37% of strong-prompt samples parse a confidence (vs ~81% for the neutral baselines). Unparsed confidence falls back to `conf=0.5 → 1−Brier=0.75`, which raises the strong-prompt mean and shrinks its sd but leaves the baseline sd high, inflating paired-diff variance and pushing the stringent Bonferroni CI lower bound just below 0.

This run replaces the endpoint with a **confound-free** one that (a) a strong instruction reliably drives to ≈1.0 while a neutral baseline leaves near 0, (b) is scored by a **simple deterministic** check, (c) has **no parsing/truncation confound** (the scored signal appears at the very START of the reply, so it is captured regardless of the token budget), and (d) has **no harmful content**. Per Part I anti-special-pleading: this endpoint is chosen for being confound-free and near-guaranteed, **before** any generation. The endpoint, scorer, token budget, both contrasts, and all seeds are LOCKED here. **No arm/endpoint/scorer/threshold/CI/seed may be substituted after outcomes are seen, and if the predeclared endpoint does not PASS it will NOT be swapped for another endpoint in this run** — the honest result is reported and the run stops.

## 1. Population (items)

- **Source:** TriviaQA `mandarjoshi/trivia_qa`, config `rc.nocontext`, **validation** split (Apache-2.0), parsed by the UNMODIFIED frozen `cognitive_console.eval.c2b_tasks.parse_uncertainty_rows` (item id = original validation row index `triviaqa-{i:05d}`; the question text is the item `prompt`).
- **Fresh pool size:** **80** items.
- **Disjointness requirement (MANDATORY, verified before scoring):** the 80 fresh items must be disjoint — by **item id** AND by **normalized-question-text hash** — from BOTH existing frozen uncertainty item pools:
  1. the **frozen E-0006 uncertainty pool** = `cognitive_console.eval.c2b_tasks.load_uncertainty_set(n=80, seed=0)` (the pool the frozen endpoint/baseline is defined against); and
  2. the **E-0012 pool** = `cognitive_console.eval.e0012_triviaqa.load_e0012_triviaqa_real()` (seed 12, offset 500).
  Normalization for the text hash = `cognitive_console.eval.scorers._normalize_answer` applied to the question string, then `sha256`.
- **Fresh deterministic draw (predeclared, outcome-independent):**
  1. Load the full validation split; `all_items = parse_uncertainty_rows(validation)` (ids = original enumerate index).
  2. Compute `banned_ids` = the 80 E-0006 ids; `banned_texts` = normalized-question-text hashes of the E-0006 80 items ∪ the E-0012 80 items.
  3. Iterate item indices in the order given by `np.random.default_rng(FRESH_SEED).permutation(len(all_items))` with **`FRESH_SEED = 20260814`** (a genuinely NEW fresh seed, distinct from the prior run's 20260813); append an item iff its id ∉ `banned_ids` AND its normalized-question-text hash ∉ `banned_texts` AND its hash is not already used within the fresh pool (intra-pool de-dup). Stop at 80.
  4. Re-id the fresh pool as `pc2-triviaqa-{rank:05d}` (rank = position in accepted order) while retaining `orig_id` for provenance.
- **Disjointness proof persisted in the result:** the run records `|fresh_ids ∩ E0006_ids| = 0`, `|fresh_texts ∩ (E0006 ∪ E0012) texts| = 0`, and the sorted lists of fresh `orig_id`s + their text hashes. If any intersection is non-empty the run **STOPS** and reports (no improvisation).

## 2. DEV/TEST split

- **Split function:** UNMODIFIED frozen `cognitive_console.experiments.adjudicate_c2b.split_dev_test(fresh_ids, dev_fraction=1/3, seed=20260723)`.
- **Result (deterministic):** `n_dev = int(round(80/3)) = 27`, `n_test = 53`. → **27 DEV / 53 TEST.**
- **Evaluation set:** **TEST only (53 items).** DEV is held out; the prompt condition wording is predeclared below (not selected on outcomes), so DEV items are not generated on. (This mirrors the frozen convention and the prior prospective run; DEV plays no role in this fixed-prompt control.)

## 3. Endpoint (per-item outcome) — PREFIX-COMPLIANCE (deterministic, confound-free)

- **Behavioral endpoint:** **instruction/format compliance** — whether the model's reply begins with an exact predeclared literal marker.
- **Deterministic scorer (LOCKED):** for a decoded generation `text` (HF `skip_special_tokens=True`), the per-sample compliance is

  ```python
  def prefix_compliance(text: str) -> float:
      return 1.0 if text.lstrip().startswith("ANSWER:") else 0.0
  ```

  i.e. after stripping leading whitespace, the reply must begin with the **case-sensitive, exact** six-character marker `ANSWER:` (`A N S W E R` then a colon). No other parsing; no value extraction; no dependence on the END or length of the reply.
- **Per item:** mean over `k = 5` samples of the per-sample `prefix_compliance` ∈ {0, 1} → per-item outcome ∈ [0, 1].
- **Why confound-free (predeclared rationale):** the scored signal is at the very START of the reply, so it is captured under ANY token budget (no truncation confound); there is no numeric value to parse (no parseability confound as in the uncertainty endpoint); the instruction is a benign formatting directive on trivia questions (no harmful content); an instruction-tuned model reliably obeys an explicit "begin with exact text ANSWER:" directive (near-guaranteed ≈1.0 for the strong prompt), while a neutral baseline almost never spontaneously begins with the all-caps literal `ANSWER:` (near 0) → a large, clean, robustly auto-scored effect ≫ δ=0.05.
- **Coherence gate input:** the frozen `cognitive_console.eval.scorers.degeneracy_score(text)` (repetition score) is still computed per sample and the frozen coherence gate still applies (compliance outputs must be coherent, not degenerate).

## 4. Conditions (3), generation identity

Generation is **unsteered** (activation-addition α=0 with a neutral unit direction, layer=1) via the frozen `cognitive_console.steering.generate.SteeredHFBackend.generate` — the exact generation primitive used by the frozen samplers. Generation identity matches the frozen E-0006 convention **except the token budget** (predeclared below, adequate for and not confounding this endpoint):

- **Model:** `Qwen/Qwen2.5-7B-Instruct` (dtype bfloat16, device cuda — A800 **GPU3 only**).
- **Generation:** `max_new_tokens = 32` (predeclared; ample for a coherent one-line answer and — because compliance depends only on the reply prefix — **not truncation-confounded**; this is the intentional, predeclared departure from the frozen 64-token budget), `temperature = 0.7`, `do_sample = True`, `k = 5` samples/item.
- **Per-(item,sample) seed (frozen derivation):** `sha256(f"{base_seed}|instruction_compliance|{item_id}|{alpha:.6f}|{j}") % 2**31`, mirroring the frozen `BackendOutcomeSampler._call_seed` / `SteeredHFTextCapableSampler._call_seed` (axis label = `instruction_compliance`, `alpha=0.0`), where `base_seed` is the per-condition base seed below.
- **Task input (predeclared builder):** `text_input = instruction.strip() + "\n\n" + question.strip()` — the instruction followed by the TriviaQA question, with **no** additional answer-format cue appended (deliberately unlike the frozen uncertainty axis cue, so the neutral baseline carries no `Answer:` hint). Rendered through the model's chat template by `SteeredHFBackend` exactly as in the frozen path.

| Condition | Role | Instruction text | base_seed |
|---|---|---|---|
| (i) prompt | strong format instruction | `Formatting requirement: Your reply MUST begin with the exact text "ANSWER:" written in all capital letters (the six characters A, N, S, W, E, R followed by a colon), and nothing may come before it. After "ANSWER:", write your answer to the question on the same line.` | **20260723** |
| (ii) baselineA | neutral baseline A | `Please answer the following question.` | **20260723** |
| (iii) baselineB | independently-seeded neutral baseline B | `Please answer the following question.` (same neutral text as A) | **20260724** |

Note (paired design, predeclared): (i) and (ii) share `base_seed=20260723` → identical per-(item,sample) sampling randomness, differing only by the prompt; this is a variance-reducing paired contrast and does **not** bias the mean. (iii) uses a genuinely independent `base_seed=20260724` (same neutral text) → the NEGATIVE contrast reflects pure sampling noise between two neutral conditions.

## 5. Predeclared contrasts (per-item paired diffs on the 53 TEST items)

- **POSITIVE control:** `d_i = compliance_prompt(i)_i − compliance_baselineA(ii)_i`  → **expected PASS**.
- **NEGATIVE control:** `d_i = compliance_baselineB(iii)_i − compliance_baselineA(ii)_i`  → **expected FAIL**.

## 6. Frozen gate (decision rule — copied, LOCKED)

Adjudicated through the UNMODIFIED frozen `adjudicate_c2b` functions and constants:

- **Bootstrap CI:** `cluster_bootstrap_ci(per_item_diff, b=10000, ci_level=BONFERRONI_CI_LEVEL, seed=20260723, cluster=True)` where `BONFERRONI_CI_LEVEL = 1 − 0.05/3 = 0.98333…` (item-cluster bootstrap: resample the 53 TEST items with replacement).
- **Coherence gate (per contrast):** `coherence_ok = mean_degeneracy(treatment on TEST) ≤ COHERENCE_MAX_RATIO × mean_degeneracy(baselineA on TEST) + COHERENCE_EPS_FLOOR + 1e-12`, with `COHERENCE_MAX_RATIO = 1.5`, `COHERENCE_EPS_FLOOR = 0.02`, degeneracy = frozen `scorers.degeneracy_score`. Treatment = prompt(i) for POSITIVE; baselineB(iii) for NEGATIVE.
- **Pass rule:** `axis_pass(mean_d = ci.point, ci_lo, ci_hi, coherence_ok, delta=DELTA)` with `DELTA = 0.05`. An arm PASSES iff **(i)** the CI excludes 0 **AND (ii)** `mean_d ≥ 0.05` **AND (iii)** coherence_ok.

## 7. Interpretation rule (predeclared)

- The gate is demonstrated **satisfiable + discriminative on FRESH outcome-blind data** iff **POSITIVE = PASS and NEGATIVE = FAIL**.
- Any other combination (POSITIVE fails, or NEGATIVE passes) is reported **honestly and in full**; it is not massaged. **No** arm/endpoint/scorer/threshold/CI/seed substitution after seeing outcomes; **no** tuning-to-pass; **no** switching to a different endpoint and retrying within this run.
- **Honest scope caveat (predeclared):** this control shows the gate accepts a real **PROMPT/instruction** effect and rejects a null. It does **NOT** show the gate accepting a **latent/steering** signal. It is a positive control on the decision machinery, not evidence for the project's steering claims.

## 8. Frozen artifacts NOT touched

No frozen artifact is modified: E-0005/6/11/13, `arm_full`, `data/e0006_uncertainty_baseline/*`, `e0006_uncertainty_baseline`, and all frozen `src/cognitive_console` modules are read-only inputs. All new files live on `feature/positive-control-clean`. No push, no merge, no bless. Compute is GPU3-only; GPUs 0–2 are untouched.
