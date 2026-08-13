# Predeclaration — STRONG-vs-STRONG′ (non-degenerate NEGATIVE arm) positive control for the frozen comparator-bound gate

**Status:** PREDECLARED (this file is committed BEFORE any generation, scoring, or
result). `valid_for_paper=false`; `scientific_status=PENDING_HOSTILE_RESULT_AUDIT`.
This is a gate-validity **diagnostic**, not paper evidence. It blesses nothing,
pushes nothing, merges nothing, and touches no frozen artifact.

**Branch:** `feature/positive-control-strong-negative` · **Worktree:** `.worktrees/pc4`
**Predecessor run:** `feature/positive-control-noisy` (pc3), commit `364ee43` —
a SOUND positive control (POSITIVE Δ=0.600, CI[0.4453,0.7509], PASS) that proved
the frozen gate is SATISFIABLE, but whose NEGATIVE arm was a **degenerate exact
null** (both neutral baselines uniformly 0.0 → contrast CI `[0,0]`).

---

## 0. Why this run exists (the single audit gap it closes)

A hostile audit of pc3 accepted the POSITIVE arm but flagged (MAJOR) that the
NEGATIVE arm's `[0,0]` CI only demonstrates rejection of an **EXACT** null (a
contrast with literally zero per-item variance). It does **not** demonstrate that
the gate rejects a **NOISY / near-threshold** null — a contrast whose per-item
diffs genuinely vary but whose true mean effect is ~0. A rejection stamp that only
fires on a mathematically perfect zero is weak evidence of discrimination.

This run adds a **NON-DEGENERATE NEGATIVE arm** so the discrimination claim is
genuinely stressed: a null contrast that is **noisy** (proper, non-collapsed
bootstrap CI with real per-item spread) yet whose true effect is ~0, so the gate
should still **FAIL** it (CI includes 0 and/or mean < δ). The audit also noted
(UNVERIFIED) that pc3's raw rows lacked the generation `finish_reason` and the
per-(item,sample) seed; this run **records both in every raw row**.

Everything else reuses the SOUND pc3 setup **exactly** (endpoint, scorer, budget,
model, k, temperature, pool, split, frozen adjudicator). The ONLY change is what
condition (iii) is and which contrast is the negative arm.

---

## 1. Predeclared endpoint, scorer, and budget (LOCKED — identical to pc3, no swap/tuning)

- **Endpoint:** instruction **"answer in exactly two words."**
- **Deterministic scorer** `exactly_two_words(text)`: strip the reply, split on
  runs of whitespace (`re.findall(r"\S+", text.strip())`); score **1.0 iff the
  whitespace-token count == 2**, else 0.0. No model, no value parsing, no
  correctness judgment — purely a length/format constraint.
- **Token budget:** `max_new_tokens = 32`. Not truncation-confounded: a compliant
  2-word reply is far under 32 tokens, and truncating a long (non-compliant) reply
  cannot turn it into exactly two words, so truncation never converts a fail into a
  pass or vice-versa.
- **Why non-degenerate:** an "exactly two words" constraint *fights* the natural
  answer length of TriviaQA questions. Under temperature-0.7 sampling the model
  complies on some samples and not others for the same item, so **per-item
  compliance is fractional** (e.g. 0.2/0.4/0.6/0.8). This gives real per-item
  spread in the strong condition — which is exactly what makes the strong−strong′
  NEGATIVE contrast below **noisy** rather than an exact zero.
- **Coherence-safe:** the frozen `degeneracy_score` returns ~0.0 for short 2-word
  replies and low for the fluent neutral baseline, so the coherence ceiling
  `1.5×baseline_degeneracy + 0.02` is comfortably satisfied.

## 2. Predeclared instruction wordings (LOCKED — identical to pc3)

- **Strong (conditions i and iii — SAME wording, different seed):**
  `"Answer the following question in exactly two words. Your entire reply must contain exactly two words and nothing else."`
- **Neutral baseline (condition ii):** `"Please answer the following question."`
- **Task input builder:** `instruction + "\n\n" + question` (no answer-format cue in the question).

## 3. Predeclared data pool + REAL disjointness rule (HARD-FAIL on any overlap; identical to pc3)

- **Source:** REAL TriviaQA `rc.nocontext` validation split, parsed by the frozen
  `c2b_tasks.parse_uncertainty_rows` (ids `triviaqa-{raw_row_index:05d}`).
- **Fresh pool:** the **first 80** parsed items whose id-index is **≥ 100**
  (`triviaqa-00100` onward) — the SAME verified-disjoint pool as pc3. Deterministic
  contiguous slice; no random permutation.
- **MANDATORY verification against the ACTUAL frozen artifact (not a re-sample):**
  read the real frozen
  `data/e0006_uncertainty_baseline/e0006_uncertainty_baseline.manifest.json`
  (item ids) AND the real frozen `...e0006_uncertainty_baseline.jsonl` (per-item
  `prompt`). Compute the frozen id set and the frozen normalized-question-text hash
  set (`sha256(scorers._normalize_answer(prompt))`). Require
  **`fresh_ids ∩ frozen_ids == ∅` AND `fresh_text_hashes ∩ frozen_text_hashes == ∅`**.
  Also cross-check that the host jsonl file sha256 equals the manifest
  `artifact_sha256` (proves the genuine frozen artifact was read). If any
  intersection is non-empty, the script **raises SystemExit and STOPS** — no
  generation occurs.
- **Split:** frozen `split_dev_test(dev_fraction=1/3, seed=20260723)` → 27 DEV / 53
  TEST. **Only the 53 TEST items are adjudicated.** No α/prompt search (α=0
  unsteered, prompts predeclared), so DEV tunes nothing.

## 4. Predeclared conditions, contrasts, and seeds (LOCKED — the ONLY change vs pc3)

- **Model:** `Qwen/Qwen2.5-7B-Instruct`. **Unsteered** (α=0). k=5 samples/item,
  temperature=0.7, do_sample=True, max_new_tokens=32.
- **Conditions:**
  - (i) **strong** instruction, base seed **20260723**.
  - (ii) **neutral baseline A**, base seed **20260723** (paired with strong — same
    sampling seeds, only the instruction differs). Kept for POSITIVE-arm
    continuity/context.
  - (iii) **strong′** = the SAME strong instruction, base seed **20260813**
    (INDEPENDENT of the strong seed 20260723). This is a second independent draw of
    the identical instruction.
- **Per-(item,sample) seed derivation** (frozen convention, mirrors
  `BackendOutcomeSampler._call_seed`):
  `sha256(f"{base_seed}|{axis_label}|{item_id}|{alpha:.6f}|{j}") % 2^31`,
  with `axis_label = "instruction_two_words"`. Because strong (20260723) and
  strong′ (20260813) differ only in `base_seed`, every one of the k=5 per-sample
  seeds differs between them → strong and strong′ are **independent draws of the
  same instruction**.
- **Contrasts through the UNMODIFIED frozen adjudicator**
  (`adjudicate_c2b.cluster_bootstrap_ci` / `axis_pass`; DELTA=0.05, CI level
  1−0.05/3 ≈ 0.983333, B=10000, bootstrap seed=20260723, item-cluster=True;
  coherence ceiling = 1.5×baseline_degeneracy + 0.02):
  - **POSITIVE** = strong(i) − baselineA(ii) → **expected PASS** (continuity with
    the SOUND pc3 result).
  - **NON-DEGENERATE NEGATIVE** = strong(i) − strong′(iii) → **expected FAIL**.
    SAME instruction, different seed → expected mean ≈ 0, BUT with genuine per-item
    variance (both arms have fractional per-item compliance), so the paired
    per-item diffs span negative AND positive values, the bootstrap CI is a proper
    **NON-degenerate** interval (NOT `[0,0]`), and the gate should still FAIL (CI
    includes 0 and/or mean < δ). This is the whole point: the gate rejects a
    **noisy** null, not merely an exact one.
- **Gate is satisfiable + discriminative-against-a-noisy-null iff** POSITIVE passes
  AND NON-DEGENERATE NEGATIVE fails AND the negative arm's CI is verifiably
  non-degenerate (CI width > 0 and ≥ 3 distinct per-item diff values).

- **OPTIONAL sub-δ POSITIVE arm:** a small real effect with predeclared
  0 < mean < δ (0.05) that should FAIL on the mean≥δ criterion would further stress
  the gate. **It is OMITTED from this run**: constructing an endpoint confidently
  known a priori to land in the narrow (0, 0.05) band cannot be done without tuning
  against outcomes, which the anti-gaming red line forbids. Per the run
  instruction, it is omitted rather than guessed. This omission is predeclared here
  so its absence is not a post-hoc choice.

## 5. Raw-row provenance additions (closes pc3's UNVERIFIED note)

Every raw generation record additionally carries: `base_seed`, `call_seed` (the
derived per-(item,sample) seed actually fed to the backend), and `finish_reason`
∈ {`stop` (EOS emitted before the budget), `length` (hit max_new_tokens)}. The
`finish_reason` is read from the TRUE generated token ids captured by a
non-invasive shim that wraps `backend._model.generate` (records the output tensor,
then returns it verbatim); the frozen generation primitive is unchanged (`git diff
main -- src` stays empty).

## 6. Anti-gaming red line

Endpoint, scorer, token budget, pool range, split, all three base seeds, both
contrasts, and their expected directions are fixed in THIS commit, which PRECEDES
the result commit. There will be **no tuning, no search, no endpoint swap, no
retry** to force an outcome. The run executes **ONCE**. If the NON-DEGENERATE
NEGATIVE unexpectedly PASSES, or the POSITIVE fails, or the negative CI comes out
degenerate, that is reported HONESTLY and the run STOPS. Every number in the result
comes from the script's artifact; none is hand-entered.

## 7. Honest scope

A PASS here shows only that the frozen gate can ACCEPT a realistic prompt/
instruction effect and REJECT a **noisy** (non-degenerate) null on fresh,
outcome-blind, verified-disjoint data. It still says **nothing** about a
latent/steering-vector pass — that remains a separate, unmet burden. This is
decision-machinery satisfiability + discrimination on a benign prompt-format
effect, NOT latent/steering efficacy.
