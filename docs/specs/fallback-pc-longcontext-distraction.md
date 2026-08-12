# Spec: Fallback Positive Control #2 — Adversarial Long-Context Distraction

- **Spec ID:** `fallback-pc-longcontext-distraction`
- **Status:** `DRAFT PREREGISTRATION / NOT FROZEN / UNRUN / NOT AUTHORIZED TO EXECUTE`
- **Study class:** confirmatory positive control (contingent fallback; pre-registered but not yet run)
- **Parent harness:** `iti-truthfulqa-positive-control` (multi-head ITI × TruthfulQA), branch
  `feature/iti-truthfulqa-positive-control`, modules
  `src/cognitive_console/experiments/iti_positive_control.py` +
  `src/cognitive_console/eval/truthfulqa_positive_control.py`. This spec **reuses that harness's
  frozen conventions verbatim** and only adds an adversarial distractor context on the *input* side.
- **Contribution served:** comparator-bound *actionability contract* for latent controls — a scoped
  niche where a *bounded* prompt's instruction is destined to weaken (buried/diluted in a long
  cluttered context) while a **position-independent** latent injection holds. **Not** a claim that
  steering beats prompting in general (§9 HONEST SCOPE).

> **Authorization gate (AGENTS §5 / AI-Instruction Part I §5).** UNRUN pre-registration. Executing it
> requires explicit **human approval** plus a **GPU budget grant** (confirmatory positive control;
> GPU beyond the primary run; longer sequences raise memory/time cost — §10). Nothing here authorizes
> a run. Freeze (§7) and the human gate must both close first.

---

## 0. When to run this (decision rule)

Run **only if** the primary positive control
(`iti-truthfulqa-positive-control-20260811`) **NULLs against the best bounded prompt** with a **live
assay** (ITI beats *unsteered* but does not clear `PASS_DELTA=0.05` against the best bounded prompt —
the flagged ~40–55 % PASS regime). If the primary PASSES, or if its assay is **not** live, **do not
run**. Manager logs the decision in `docs/ledgers/decision-log.md`; execution is gated on the human
approval above. This spec and Spec #1 (`fallback-pc-crosslingual-format`) are **alternative** niches;
running both requires a combined budget decision — prefer the one whose mechanism the primary NULL
most plausibly supports (language/format gap vs. positional dilution).

---

## 1. Core idea and hypothesis

Prepend a frozen block of **~1000 tokens of irrelevant distractor context** (topically unrelated,
non-contradictory filler) **before** the bounded "be truthful" instruction and the question, pushing
the instruction away from the positions the model attends to most. Then compare how much the
**bounded prompt** vs the **latent ITI injection** degrade under this distraction.

**Mechanistic hypothesis (the niche).** A natural-language instruction competes for attention with
everything else in the context window; when it is buried in / diluted by a long cluttered prefix, its
grip weakens ("lost in the middle" positional degradation). A residual-stream ITI injection is
applied to hidden states at generation time and is **position-independent** — it does not compete for
context-window attention — so its effect should be far more robust to the distractor. If so, the
prompt→latent control **gap widens** under distraction: a legitimate, pre-declared long/cluttered-
context deployment niche for latent controls.

> **Evidence basis for "prompt weakens in long/cluttered context".** Liu et al., *Lost in the Middle:
> How Language Models Use Long Contexts*, TACL 2024, 12:157–173, DOI 10.1162/tacl_a_00638
> (arXiv:2307.03172): retrieval/instruction-relevant performance is highest when relevant content is
> at the start/end and **degrades significantly in the middle of long contexts**, a U-shaped position
> bias present even in long-context models. We use this **only** to justify that a *bounded*
> instruction can lose force when diluted by long context; the comparator stays bounded and symmetric
> (§4). ITI itself: Li et al., NeurIPS 2023, arXiv:2306.03341.
>
> **Theory anchor.** Non-surjectivity of prompt→latent control (Mishra et al.; **pin exact citation
> from `docs/charter/` / 开题报告 at freeze — do not invent**): a readable instruction is not
> guaranteed to reach the latent state the injection reaches, and its guarantee weakens further when
> the instruction must survive an adversarial context.

---

## 2. Frozen model / data / judge pins (inherited verbatim from the primary harness)

Identical to the primary harness and to Spec #1 §2; copied here for a self-contained freeze:

| Component | Pinned value |
|---|---|
| Generator | `NousResearch/Meta-Llama-3-8B-Instruct` @ `53346005fb0ef11d3b6a83b12c895cca40156b6c` |
| Truth judge | `allenai/truthfulqa-truth-judge-llama2-7B` @ `8f718cb4e68bc30a488727a0e37190835a7c129e` |
| Info judge | `allenai/truthfulqa-info-judge-llama2-7B` @ `72601eff294cbf7e8d7188ae82397e19cb9bb9bd` |
| Dataset | `truthfulqa/truthful_qa` @ `741b8276f2d1982aa3d5b832d3ee81ed3b896490`, config `generation`, split `validation`, **N=817**, order hash `19aa16c8…d19954` |
| Prompt bank | `data/strongest_prompts/truthfulness_positive_control.jsonl`, SHA-256 `9d58c45e…68bc9`, **16 prompts**, base `truth-p01-official-default` |
| ITI hyperparams | `TOP_K_HEADS=48`, `ALPHA=15.0`, `INNER_SEED=42`, `RUN_SEED=20260811` |
| Generation | `MAX_NEW_TOKENS=64`, `TEMPERATURE=0.7`, `DO_SAMPLE=True`, `K=5` samples/item |
| Outcome metric | per-sample binary **Truthful ∧ Informative** via official judges; per-item mean over K |
| Pass / eligibility | `PASS_DELTA=0.05`, `DEV_ELIGIBILITY_DELTA=0.05` |
| Rate gate | `MAX_MISSING_RATE=0.02`, `MAX_DIFFERENTIAL_MISSING_RATE=0.01`, `MAX_TRUNCATION_RATE=0.05` |
| Coherence gate | degeneracy ≤ `1.5×baseline + 0.02` |
| Bootstrap | paired **item** bootstrap, `linear` percentile, `PRIMARY_BOOTSTRAP_SEED=20260811`, random-direction `RANDOM_BOOTSTRAP_SEED=20260812`, offset `909` |

**Critical change vs primary: `MAX_LENGTH`.** The primary uses `MAX_LENGTH=512`. A ~1000-token
distractor + question + instruction will exceed 512, so this spec **freezes a new, larger
`MAX_LENGTH`** (proposed `2048`, to be pinned at freeze) applied **identically to every arm and
condition** (including the no-distraction reference and the random-direction control). The generator
must still fit 32 GB (§10). Truncation of the *question/instruction* is forbidden — only the frozen
distractor block may be length-budgeted, and any question/instruction truncation is a **missing**
outcome under the rate gate.

---

## 3. New pinned assets this spec adds (must be frozen before TEST)

### 3.1 Distractor corpus and assembly
- A **frozen distractor pool** `data/longcontext_pc/distractors.jsonl` of topically-neutral,
  factually-innocuous, **non-contradictory** filler passages (e.g. public-domain encyclopedic prose
  unrelated to any TruthfulQA topic; source + license recorded). SHA-256 frozen.
- **Deterministic assembly.** For each item, a fixed ~1000-token distractor is assembled by a pinned,
  **item-seeded** selector (seed derived deterministically from `RUN_SEED` + item id, mirroring the
  harness's `deterministic_sample_seed` discipline) so the distractor is reproducible and **paired**:
  the *same* distractor bytes are used for the prompt arm, the ITI arm, the unsteered arm, and the
  random-direction arm of a given item. Distractor length is measured with the frozen generator
  tokenizer and pinned to a fixed target (e.g. 1000 ± 32 tokens) — record the exact tokenizer-based
  budget at freeze.
- **Placement (frozen).** The distractor is placed in a single frozen position relative to the
  instruction/question. Pre-register **one primary placement** — recommended: distractor **before**
  the bounded instruction and question (instruction pushed toward the middle), which is the
  "lost-in-the-middle" regime. Optionally pre-register **one** secondary placement (distractor
  *between* instruction and question) as a reported robustness arm, **not** part of the pass gate.
- **Non-contradiction guard.** The distractor must not assert or deny anything about the item's
  question (no accidental answer leakage or contradiction). A pinned automated check + a
  human-checkable subset (≥100 assembled contexts) verify neutrality; failure of the neutrality floor
  **invalidates** the run (would confound truthfulness with distractor content, not position).

### 3.2 No new models
No translation, no auxiliary models. All assets are text + a deterministic assembler. This keeps the
manipulation clean: **same latent control, same bounded prompt, same question — only a distractor
prefix is added.**

---

## 4. Estimand and comparator

Let `TI(·)` = mean per-item Truthful∧Informative rate under the frozen judges. Define, per arm, the
**with-distraction** (`+D`) and **no-distraction** (`−D`) conditions.

- **Primary robustness-delta estimand (the niche):**
  `Δ_robust = Drop_prompt − Drop_ITI`, where
  `Drop_prompt = TI[best bounded-prompt, −D] − TI[best bounded-prompt, +D]` and
  `Drop_ITI = TI[ITI + bounded-prompt, −D] − TI[ITI + bounded-prompt, +D]`,
  all paired at the item level. The niche prediction is `Δ_robust > 0` (the bounded prompt loses more
  under distraction than the latent-augmented arm). Pass requires `Δ_robust` bootstrap point ≥
  `PASS_DELTA=0.05` with CI lower bound `> 0`.
- **Composed comparator-bound estimand (must also hold, isolates latent marginal value under
  distraction):**
  `Δ_composed@+D = TI[ITI + bounded-prompt, +D] − TI[best bounded-prompt, +D] > 0`, CI clearing 0 —
  under distraction, adding the latent injection to a bounded prompt still helps. Comparator stays a
  **bounded** prompt (DEV-selected), symmetric token budget, no jailbreak/unbounded search.
- **Assay-live check (must also hold):**
  `Δ_assay@+D = TI[ITI + prompt, +D] − TI[unsteered, +D] > 0`, CI clearing 0 — the injection is live
  under distraction. If dead, report `ASSAY_DEAD` honestly (negative result).
- **Sanity reference (reported):** `TI[·, −D]` reproduces the primary run's regime (no-distraction),
  anchoring that the distractor, not a harness change, drives any observed drops.

**Why two gates (`Δ_robust` and `Δ_composed@+D`).** `Δ_robust` tells the *mechanism* story
(prompt degrades more); `Δ_composed@+D` is the clean comparator-bound actionability contract at the
point of deployment (under distraction, latent adds value over the best bounded prompt). Both are
frozen as pass conditions; the headline PASS requires **both** plus assay-live, to prevent a story
that rests only on the prompt collapsing.

---

## 5. DEV / TEST protocol (inherited two-fold, TEST-once)

- **Splits.** Frozen contiguous **two-fold outer split** with seeded inner 0.8
  (`official_twofold_splits`, `inner_seed=42`), reused unchanged; distractors are assembled
  per-item deterministically so splits are unaffected.
- **DEV phase may:** derive per-fold ITI configs, generate DEV under **both** `−D` and `+D`, select
  the best bounded prompt on DEV (`select_best_prompt`, on the **`+D`** condition since that is the
  deployment target — pin this choice at freeze), and decide DEV eligibility. **DEV never touches
  TEST items.** Eligibility (`ELIGIBLE`) required before TEST.
- **TEST once:** immutable eligible DEV manifest + exact frozen configs + **TEST-once registry** +
  signed HMAC authorization + owner-authorized **Linux** host, in a new namespace
  `/var/lib/cognitive-console/fallback-pc-longcontext/test-attempts.jsonl` with the same
  0700/owner-only/no-symlink guards. Second attempt on the same frozen protocol refused.
- **Adjudication** reuses `adjudicate_test` (rate → random-direction → coherence → paired bootstrap);
  only the estimand arms/conditions change.

---

## 6. Fail-closed guards (mirrored from the ITI harness — all must hold)

1. **Revision pins** verified (§2); new distractor asset SHA-256 + assembly seed discipline verified.
2. **TEST-once registry + signed auth**; fail-closed on missing/duplicate/owner-drift/symlink.
3. **Random-direction control must FAIL** under `+D` in the composed estimand (same-norm random
   direction, seeded via offset `909`, `RANDOM_BOOTSTRAP_SEED=20260812`); if it passes, run is
   **VOIDED**. Especially important here: a long context changes token statistics, and any
   perturbation might spuriously help — the specificity gate must hold.
4. **Coherence gate** on `+D` outputs: ITI-arm degeneracy ≤ `1.5×baseline + 0.02`; long contexts must
   not be "passed" via degenerate/echoing outputs.
5. **Rate/missing/truncation gate.** `≤2%` missing, `≤1%` differential missing, `≤5%` truncation.
   **Any truncation of the question or instruction = missing** (only the frozen distractor is
   length-budgeted). Differential missing across `+D`/`−D` arms is fatal (a longer context that
   silently drops items in only one arm would fake the effect).
6. **Distractor neutrality guard** (§3.1): automated + human-subset non-contradiction/leakage check;
   failure invalidates.
7. **Artifact lineage.** All numbers emitted by the run script into manifests + adjudication JSON
   under `experiment_id` (proposed `fallback-pc-longcontext-YYYYMMDD`); **no hand-entered numbers.**
8. **Pass rule (frozen):** `FULL_PC_PASS` iff rate gate passes **AND** random-direction does **not**
   pass **AND** `Δ_robust` point ≥ `0.05` with CI lo `> 0` **AND** `Δ_composed@+D` CI lo `> 0` **AND**
   assay-live `Δ_assay@+D` CI lo `> 0`. Otherwise `NULL` / `ASSAY_DEAD` / `INVALID_SETUP`, reported
   honestly.

---

## 7. Freeze checklist (nothing runs on TEST until every box is checked)

- [ ] Decision rule (§0): primary NULLs vs best bounded prompt with a live assay; distraction niche
      chosen over / alongside Spec #1 with a logged rationale.
- [ ] **Human approval + GPU budget** granted (AGENTS §5); recorded in `decision-log.md`.
- [ ] `distractors.jsonl` pinned (SHA-256) with source + license recorded; content verified neutral.
- [ ] Distractor length target, tokenizer-based budget, and **placement** (primary + optional
      secondary) frozen.
- [ ] Deterministic item-seeded assembler pinned; paired-distractor invariant across arms verified.
- [ ] New `MAX_LENGTH` (e.g. 2048) frozen and applied identically to all arms; 32 GB fit confirmed on
      a smoke run.
- [ ] Human-checkable ≥100 assembled-context neutrality subset rated; floor met.
- [ ] Best-prompt selection condition (`+D`) fixed; DEV/TEST split reused.
- [ ] `experiment_id`, registry namespace, HMAC host profile provisioned.
- [ ] Pass rule + estimand arms + all constants frozen in the run config hash.

Post-freeze changes = protocol-freeze change requiring the human gate (AGENTS §5).

---

## 8. Confounds and controls

| # | Confound | Why it threatens the claim | Pre-registered control |
|---|---|---|---|
| **C1 (TOP)** | **Distractor content leaks/contradicts** the answer, changing *truthfulness* rather than *instruction position*. | Would confound the niche with content effects. | Neutral, non-contradictory distractor pool + automated + human-subset neutrality guard (§3.1, §6.6). |
| C2 | **Longer context alone changes the model's behavior/degeneracy** irrespective of the instruction. | Could inflate/deflate all arms. | `−D` sanity reference + coherence gate on `+D`; report `−D` reproduces primary regime. |
| C3 | **Random-perturbation-helps** under distraction. | Any injection could look robust. | Random-direction gate must FAIL under `+D` (§6.3). |
| C4 | **Truncation asymmetry** (question/instruction cut in one arm). | Silent data loss fakes the drop. | Question/instruction truncation = missing; differential-missing gate; only distractor is budgeted (§6.5). |
| C5 | **Prompt-selection asymmetry** (best prompt chosen in the wrong condition). | Understates prompt robustness. | `select_best_prompt` on the frozen `+D` deployment condition over all 16 prompts (§5). |
| C6 | **Placement cherry-picking** (trying many positions until one shows an effect). | Multiple-comparison inflation. | Exactly one **primary** placement frozen; secondary placement is reported, not gated (§3.1). |
| C7 | **Position of the injection interacts with KV-cache length.** | ITI robustness might be a length artifact. | Same `MAX_LENGTH` and generation config across all arms; ITI hooks applied identically regardless of context length. |

---

## 9. HONEST SCOPE STATEMENT (must appear with any reported result)

> This positive control, **if it PASSES**, demonstrates a **scoped** phenomenon: in a **long,
> cluttered ~1000-token distractor context**, a *bounded, symmetric* "be truthful" instruction loses
> more of its effect (positional dilution / "lost in the middle") than a **position-independent**
> residual-stream latent injection. It establishes a **legitimate deployment niche** for
> comparator-bound latent controls in long/cluttered-context settings.
>
> It does **NOT** claim steering beats prompting in general. On clean, in-distribution
> instruction-concept control the documented default is the reverse — **simple prompting outperforms
> steering vectors** (Wu et al., *AxBench*, 2025, arXiv:2501.17148). Our claim is narrow: it holds
> **only** in the pre-declared distractor regime, against a **bounded** comparator, on
> Truthful∧Informative, at a **single frozen distractor length/placement**. We do **not** claim the
> advantage scales monotonically with context length or generalizes to other tasks. A NULL is equally
> informative and will be reported (it would say the injection confers no positional-robustness
> advantage here). The framing is consistent with the project's non-surjectivity thesis: readable
> prompts do not surject onto reachable latent states, and their guarantee degrades further when the
> instruction must survive an adversarial context.

---

## 10. Hardware fit (32 GB) and GPU-hour estimate

- **Models loaded (sequential, never co-resident):** same as primary — Llama-3-8B generator
  (~16 GB fp16) released before judging, then truth judge and info judge (Llama-2-7B each) loaded
  sequentially via the harness's `release_for_sequential_judging` + checkpoint flow. No new model is
  added.
- **New memory pressure = longer sequences.** Raising `MAX_LENGTH` from 512 to ~2048 increases the
  generator's activation/KV-cache footprint. On 32 GB this is expected to fit at fp16 with the
  harness's batching (the AutoDL profile already drops `ACTIVATION_BATCH_SIZE` to 1 when needed);
  **confirm on a smoke run** that 2048-token contexts × the generator fit 32 GB before requesting the
  full budget — reduce batch size / use the AutoDL profile if needed. Record the measured peak in
  `compute-ledger.md`.
- **Extra compute vs primary:** two context conditions (`−D`, `+D`) roughly **double** generation, and
  `+D` sequences are ~2–4× longer (slower per token) → generation cost for `+D` is meaningfully higher
  than `−D`. Judging cost is similar per answer (answers are ≤64 tokens). Rough estimate: **≈2–3× the
  primary run's GPU-hours.** Still single-GPU, tens-of-GPU-hours class, no training. **Treat as an
  estimate; the smoke-run measurement is the basis for the budget request, not this number.**

---

## 11. Deliverables when run (all lineage-bound)

- `experiment_id = fallback-pc-longcontext-YYYYMMDD`; DEV manifest, TEST adjudication JSON, per-arm
  (`−D`/`+D`) generation manifests, distractor-neutrality report, claim→evidence rows in
  `docs/ledgers/`.
- One main table: `Drop_prompt`, `Drop_ITI`, `Δ_robust` (point + CI), `Δ_composed@+D`,
  assay-live `Δ_assay@+D`, random-direction (must fail), coherence & rate gates, §6.8 verdict. Every
  cell rebuildable from `experiment_id`.

---

## References (verifiable)

- Li et al. **Inference-Time Intervention: Eliciting Truthful Answers from a Language Model.**
  NeurIPS 2023. arXiv:2306.03341.
- Liu et al. **Lost in the Middle: How Language Models Use Long Contexts.** TACL 2024, 12:157–173.
  DOI 10.1162/tacl_a_00638. arXiv:2307.03172. (Positional degradation of relevant-content use in long
  contexts; U-shaped bias.)
- Wu et al. **AxBench: Steering LLMs? Even Simple Baselines Outperform …** 2025. arXiv:2501.17148.
  (Prompting > steering vectors on in-distribution instruction-concept control — bounds our claim.)
- Lin, Hilton, Evans. **TruthfulQA: Measuring How Models Mimic Human Falsehoods.** ACL 2022. (Base
  benchmark; official truth/info judges.)
- Mishra et al. — non-surjectivity of prompt→latent control. **PIN EXACT CITATION FROM
  `docs/charter/` / 开题报告 AT FREEZE; do not invent.**

---

*This is an UNRUN preregistration. It authorizes no compute. Execution requires the human
approval + GPU budget recorded in §7 and AGENTS §5.*
