# Predeclaration — NOISY (non-degenerate) positive control for the frozen comparator-bound gate

**Status:** PREDECLARED (this file is committed BEFORE any generation, scoring, or
result). `valid_for_paper=false`; `scientific_status=PENDING_HOSTILE_RESULT_AUDIT`.
This is a gate-validity **diagnostic**, not paper evidence. It blesses nothing,
pushes nothing, merges nothing, and touches no frozen artifact.

**Branch:** `feature/positive-control-noisy` · **Worktree:** `.worktrees/pc3`

---

## 0. Why this run exists (what two prior attempts got wrong)

A hostile audit REJECTED two prior positive-control attempts for the claim that the
frozen comparator-bound decision gate is **satisfiable + discriminative** (can
ACCEPT a real advantage and REJECT a null), not merely a rejection stamp:

1. **Uncertainty-endpoint attempt** — confounded (confidence-parseability ×
   64-token truncation) AND its "fresh" pool was NOT actually disjoint from the
   real frozen E-0006 pool (it reconstructed E-0006 by a *re-sample*
   `load_uncertainty_set(seed=0)` — a permutation subsample — instead of reading
   the ACTUAL frozen manifest ids `triviaqa-00000..00079`).
2. **Prefix-compliance ("ANSWER:") attempt** — PASSED but judged a STRAW/TRIVIAL
   control: every positive per-item diff was exactly 1.0 and every negative exactly
   0.0, so the bootstrap CI collapsed to [1,1] / [0,0] with **no realistic
   variance**. It proves the rule is non-vacuous but does NOT show the gate
   recognizes a realistic **noisy** advantage. Its pool also was not verified
   disjoint against the real frozen artifact.

This run fixes BOTH problems with (A) **real disjointness** verified against the
ACTUAL frozen E-0006 manifest + jsonl (hard-fail on any overlap), and (B) a
**domain-realistic, NON-DEGENERATE, noisy** endpoint chosen so per-item compliance
genuinely varies across the k=5 samples and the bootstrap CI is a proper
(non-collapsed) interval while the mean still clears δ.

---

## 1. Predeclared endpoint, scorer, and budget (LOCKED — no post-hoc swap/tuning)

- **Endpoint (predeclared, single choice, no swap after seeing outcomes):**
  instruction **"answer in exactly two words."**
- **Deterministic scorer** `exactly_two_words(text)`: strip the reply, split on
  runs of whitespace (`re.findall(r"\S+", text.strip())`); score **1.0 iff the
  whitespace-token count == 2**, else 0.0. No model, no value parsing, no
  correctness judgment — purely a length/format constraint.
- **Token budget (predeclared):** `max_new_tokens = 32`. The endpoint is NOT
  truncation-sensitive: a compliant 2-word reply is far under 32 tokens, and
  truncating a long (non-compliant) reply cannot turn it into exactly two words —
  so truncation never converts a fail into a pass or vice-versa.
- **Why this endpoint is NON-DEGENERATE (the whole point):** an "exactly two words"
  constraint *fights* the natural answer length of TriviaQA questions (whose gold
  answers are variously 1, 2, or 3+ words). Under temperature-0.7 sampling the model
  complies on some samples and not others for the same item, so **per-item
  compliance is fractional** (e.g. 0.2/0.4/0.6/0.8) rather than a hard 0/1. This
  yields real per-item spread → a proper, non-collapsed bootstrap CI, unlike the
  "ANSWER:" straw control. Predeclared expectation: strong-prompt compliance ≈
  **0.55–0.90** (NOT ~1.0), neutral baseline ≤ **~0.3**.
- **Why it is coherence-safe:** the frozen `degeneracy_score` returns 0.0 for texts
  shorter than its 3-gram window, so a 2-word reply scores 0 degeneracy; the
  neutral baseline (fluent sentence) also scores low. The coherence ceiling
  `1.5 × baseline_degeneracy + 0.02` is therefore comfortably satisfied — the
  positive arm cannot be spuriously killed by the coherence gate.
- **Not chosen (and why):** bracket-wrap `[answer]` and prefix `"Sure,"` were the
  other candidates; both risk the SAME near-1.0 uniform collapse the audit
  rejected, because Qwen2.5-Instruct follows explicit format directives almost
  perfectly. "Exactly two words" is the only candidate that is simultaneously
  robustly auto-scored, non-confounded, non-harmful, coherence-safe, AND genuinely
  noisy. **This choice is final; it will not be swapped or tuned to pass.**

## 2. Predeclared instruction wordings (LOCKED)

- **Strong (condition i):**
  `"Answer the following question in exactly two words. Your entire reply must contain exactly two words and nothing else."`
- **Neutral baseline (conditions ii and iii):** `"Please answer the following question."`
- **Task input builder:** `instruction + "\n\n" + question` (no answer-format cue in the question).

## 3. Predeclared data pool + REAL disjointness rule (HARD-FAIL on any overlap)

- **Source:** REAL TriviaQA `rc.nocontext` validation split, parsed by the frozen
  `c2b_tasks.parse_uncertainty_rows` (ids `triviaqa-{raw_row_index:05d}`).
- **Fresh pool (predeclared range):** the **first 80** parsed items whose id-index
  is **≥ 100** (i.e. `triviaqa-00100` onward). This is disjoint by construction
  from the frozen E-0006 pool (raw indices 0–79) and from the E-0012 pool
  (offset 500). No random permutation is used — the selection is a deterministic
  contiguous slice so the pool is reproducible and auditable.
- **MANDATORY verification against the ACTUAL frozen artifact (not a re-sample):**
  read the real frozen `data/e0006_uncertainty_baseline/e0006_uncertainty_baseline.manifest.json`
  (item ids) AND the real frozen `...e0006_uncertainty_baseline.jsonl` (per-item
  `prompt`). Compute the frozen id set and the frozen normalized-question-text hash
  set (`sha256(scorers._normalize_answer(prompt))`). Require
  **`fresh_ids ∩ frozen_ids == ∅` AND `fresh_text_hashes ∩ frozen_text_hashes == ∅`**.
  If either intersection is non-empty, the script **raises SystemExit and STOPS** —
  no generation occurs.
- **Split:** frozen `split_dev_test(dev_fraction=1/3, seed=20260723)` → 27 DEV / 53
  TEST. **Only the 53 TEST items are adjudicated.** DEV is not used to tune anything
  here (there is no α/prompt search — α=0 unsteered, prompts predeclared).

## 4. Predeclared conditions, contrasts, and seeds (LOCKED)

- **Model:** `Qwen/Qwen2.5-7B-Instruct`. **Unsteered** (α=0, layer=1 irrelevant at α=0).
  k=5 samples/item, temperature=0.7, do_sample=True, max_new_tokens=32.
- **Conditions:** (i) strong instruction; (ii) neutral baseline A; (iii) neutral
  baseline B (independent seed).
- **Per-(item,sample) seed derivation** (frozen convention, mirrors
  `BackendOutcomeSampler._call_seed`): `sha256(f"{base_seed}|{axis_label}|{item_id}|{alpha:.6f}|{j}") % 2^31`,
  with `axis_label = "instruction_two_words"`.
  - base seed (i) strong = **20260723**
  - base seed (ii) baseline A = **20260723** (paired with strong — same sampling seeds, only the instruction differs)
  - base seed (iii) baseline B = **20260724** (independent)
- **Contrasts through the UNMODIFIED frozen adjudicator**
  (`adjudicate_c2b.cluster_bootstrap_ci` / `axis_pass`; DELTA=0.05, CI level
  1−0.05/3 ≈ 0.983333, B=10000, bootstrap seed=20260723, item-cluster=True;
  coherence ceiling = 1.5×baseline_degeneracy + 0.02):
  - **POSITIVE** = strong(i) − baselineA(ii)  → **expected PASS**
  - **NEGATIVE** = baselineB(iii) − baselineA(ii)  → **expected FAIL**
- **Gate is satisfiable + discriminative iff** POSITIVE passes AND NEGATIVE fails.

## 5. Anti-gaming red line

Endpoint, scorer, token budget, pool range, split, contrasts, and all seeds are
fixed in THIS commit, which precedes the result commit. There will be **no tuning,
no search, no endpoint swap** to force a pass. If the predeclared endpoint comes out
degenerate or fails, that is reported HONESTLY and the run STOPS — no retry. Every
number in the result comes from the script's artifact; none is hand-entered.

## 6. Honest scope

A PASS here shows only that the frozen gate can ACCEPT a realistic, noisy
**prompt/instruction** effect and REJECT a null, on fresh outcome-blind data with
non-degenerate variance. It says **nothing** about a latent/steering-vector pass —
that is a separate, unmet burden.
