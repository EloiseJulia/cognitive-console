# PRE-REGISTRATION — C2b Behavioral-Gap Adjudication (RQ2 core)

- **Status:** **FROZEN 2026-07-23** (owner-confirmed decision rule §4 + parameters §5). Success/kill criteria
  and analysis plan MUST NOT change after seeing results (owner directive, AI-Instruction Part I §7/§12).
- **Adjudicates:** Claim **C2b** — "on tasks with headroom, latent steering reaches a BEHAVIORAL outcome
  beyond the best bounded-prompt outcome." A qualified NO → pivot to Plan D (RQ1-core measurement paper).
- **Why re-run:** the first C2b probe (E-0004) used audit-rejected lexical/length proxies that saturated the
  ceiling (~0.88–1.0) — INVALID evidence. This pre-registration fixes the instrument before adjudicating.

---

## 1. Instrument fixes (all four axes' issues addressed)

1. **Eliminate the ceiling effect** — replace saturating lexical proxies with **behavioral-OUTCOME tasks
   that have real headroom** and require genuine capability change, not keyword presence:
   - **deliberation** → GSM8K-style multi-step arithmetic/reasoning: measure **accuracy** (0–1) with headroom.
   - **skepticism** → false-premise / sycophancy items: measure **false-premise-rejection rate**.
   - **uncertainty_awareness** → calibration items (questions the model often gets wrong): elicit answer +
     verbalized confidence; per-item outcome = **1 − Brier = 1 − (conf_i − correct_i)²** (proper scoring rule;
     per-item, cluster-bootstrappable). Binned ECE reported DESCRIPTIVELY only (not in the gate). This axis
     gets the MOST items (noisiest metric). *[Pre-run clarification D-0025: the original wording "(1−ECE)" was
     a SET metric with no per-item value; replaced with per-item (1−Brier). The improper 1−|correct−conf| is
     rejected (L1-optimal is reporting 0/1 → rewards overconfidence, reverses the axis). Pre-run spec fix, not
     a post-hoc criterion change; all other criteria unchanged.]*
2. **Orthogonal, NON-lexical proxy** — the measure is a TASK OUTCOME (accuracy / rejection rate / calibration),
   scored by a rule/answer-key (deterministic), NOT a count of words the steering vector could inject.
3. **Sample sizes + clustering (upgraded per owner):** **N = 60–80 items per axis** (uncertainty/ECE = 80;
   deliberation & skepticism = 60), **k = 5 samples/item**. **Bootstrap resamples at the ITEM level (cluster
   bootstrap), NOT at the sample level** — each item (with its k samples) is one cluster.
4. **DEV/TEST split to remove selection bias (owner):** split each axis's items into a DEV pool (~1/3) and a
   disjoint TEST pool (~2/3), drawn from the same task distribution. **α is selected AND frozen on DEV only;
   the best-of-16 prompt is also selected on DEV only.** Adjudication is computed on TEST with the DEV-frozen
   α and DEV-selected prompt — eliminating the "best-of-7 α" and "best-of-16 prompt" selection bias for BOTH
   channels symmetrically.
5. **Alpha sweep** over a documented grid (α selection on DEV), with a **coherence gate** (§3).
6. **Drop focus** — no stable CAA direction / overshoots; excluded.

## 2. Design
- Model: Qwen2.5-7B-Instruct (GPU fp16), same C1 chosen non-degenerate layer per axis (from E-0003).
- Steering vector = C1's re-derived CAA unit direction at the chosen layer (same extraction/split as E-0003).
- Per axis, on the TEST pool, compute per-item, at the DEV-frozen α and DEV-selected best prompt:
  - `prompt_i` = outcome of the DEV-selected best prompt on item i (mean over k samples).
  - `steer_i`  = outcome of steer-only at the DEV-frozen α on item i (mean over k samples).
  - **paired difference** `d_i = steer_i − prompt_i`.
- Conflict cells (prompt vs opposing steer) reported as SECONDARY/descriptive only.

## 3. Coherence gate (prevents "steering wins by breaking the model")
A steered cell only counts if outputs remain coherent: pre-registered check = (mean output perplexity or a
simple degeneracy/ repetition score) stays within a factor of the unsteered baseline (exact bound set at
freeze). Gains achieved only above the coherence bound are DISCARDED.

## 4. PRE-REGISTERED DECISION RULE — paired, multiplicity-corrected, three-tier (FROZEN after confirm)

**Per-axis test (paired cluster bootstrap — replaces the biased "non-overlapping independent CIs"):**
For each axis a, take the per-item paired differences `d_i = steer_i − prompt_i` on the TEST pool (α and
prompt frozen on DEV). Do a **cluster bootstrap resampling ITEMS** (each item = one cluster carrying its k
samples), B ≥ 10000 resamples, to get the CI of `mean_i(d_i)`.
An axis **PASSES (Bonferroni-corrected)** iff:
  (i) the **two-sided (1 − 0.05/3) ≈ 98.33% CI of mean(d) EXCLUDES 0** (family-wise correction over 3 axes), AND
  (ii) the **point estimate mean(d) ≥ δ**, AND
  (iii) the winning steer cell passes the **coherence gate** (§3).
> Rationale (owner): a paired test on per-item differences is far more powerful and avoids the systematic
> FALSE-KILL bias of comparing two independent non-overlapping CIs. Item-level clustering respects the k-sample
> nesting. Bonferroni over 3 axes controls false positives.

**Three-tier verdict:**
- **≥ 2 axes PASS (corrected) → STRONG GO.** RQ2 behavioral-gap supported (exploratory-confirmatory); continue
  the dual-channel line.
- **EXACTLY 1 axis PASSES (corrected) → CONDITIONAL GO.** Run a **pre-registered REPLICATION of that one axis**
  on fresh items (new DEV/TEST draw, new seed), same frozen rule. If it PASSES again → a **scope-narrowed RQ2
  claim limited to that axis**. If it does NOT replicate → **Plan D**.
- **0 axes PASS → KILL → Plan D** (RQ1-core measurement/diagnostic CHI paper). C1 evidence retained; C2b
  reported as an honest, qualified NEGATIVE.

**Conflict cells:** secondary/descriptive only — reported per axis+α, NOT part of the pass/fail decision.

**Why not simpler:** owner directive — a FALSE KILL is irreversible (permanently discards the core selling
point), and "non-overlapping CIs + N=30" biases toward false kill; the paired test + larger N guard against
false kill, while Bonferroni + the single-axis-must-replicate rule guard against a false positive.

## 5. FROZEN parameters (confirmed by owner 2026-07-23)
- N items/axis: **deliberation 60, skepticism 60, uncertainty 80**; k = 5 samples/item.
- DEV/TEST split: ~1/3 DEV (α + best-prompt selection), ~2/3 TEST (adjudication), disjoint, same distribution.
- α grid (selected on DEV): {2, 4, 6, 8, 12, 16, 24}.
- δ (meaningful margin) = **0.05** in each axis's outcome units — meaning per axis: deliberation = +0.05
  accuracy; skepticism = +0.05 false-premise-rejection rate; uncertainty = +0.05 in **(1−Brier)** (per-item
  Brier scale; ECE reported descriptively only).
- Coherence gate: steered mean repetition/degeneracy score ≤ **1.5×** the unsteered baseline; cells above the
  bound are DISCARDED.
- Bootstrap: cluster (item-level), B ≥ 10000, two-sided; per-axis CI at **1 − 0.05/3** (Bonferroni).
- Decision: paired-diff CI excludes 0 AND point ≥ δ AND coherence-gate pass; three-tier verdict as in §4.

### 5a. Pre-run generation-mechanics addendum (frozen 2026-07-24, D-0031 — PRE-RUN, no results seen)
These fix generation COMPUTE mechanics only; they do NOT touch the §4 statistical decision rule or the §5
statistical parameters (N, k, δ, α grid, DEV/TEST, Bonferroni, coherence, bootstrap). Recorded pre-run so they
are pre-registered, not post-hoc.
- **max_new_tokens = 64** (was an un-frozen default 256). Justification: the three tasks have SHORT answers —
  GSM8K final number, TruthfulQA MC letter, TriviaQA short answer + a verbalized confidence — so 64 new tokens
  is ample; 256 was overkill and 4× slower. Risk noted: 64 could truncate an unusually long chain; the answer
  parsers key on the final answer/MC letter/confidence, which fit well within 64. If any axis shows pervasive
  truncation of the keyed answer in the logs, that is reported as a limitation (not a criteria change).
- **batch_size = 16** (batched generation; audit-verified greedy batched == single-sequence EXACT on
  Qwen2.5-1.5B; sampled cells deterministic per fixed batch_size, which is now in the checkpoint fingerprint).
- **stall_timeout = 600s** (inactivity watchdog → hard-exit on a silent GPU/driver hang, per D-0029).
- **N unchanged = 60/60/80, k=5** — the hardened instrument runs the full frozen N in ~25–50 min, so no N
  reduction is needed. seed = 20260723 (as before).
- **Run must checkpoint/resume** (per-cell) and run on a machine we control OR a confirmed no-driver-maintenance
  window (D-0029 root cause).

## 6. Freeze block
- protocol_frozen: **YES — frozen 2026-07-23 after owner confirmation of the §4 decision rule + §5 parameters.**
- After freeze: tasks, outcome proxies, DEV/TEST protocol, α grid, δ, coherence bound, bootstrap/clustering,
  Bonferroni level, and the three-tier decision rule are LOCKED. Results may NOT change these criteria.
- Freeze recorded in decision-log D-0024 with the commit hash.

## 6. Budget (capped)
- Local first: implement qualified instrument + CPU/1.5B smoke + independent audit (free).
- Then ONE A800 allocation (<70GB disk, wipe after) for the 7B adjudication. Adjudicate immediately against
  the frozen criteria. No second GPU run (beyond a triggered single-axis replication) without a fresh human decision.
