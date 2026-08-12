# Spec: Fallback Positive Control #1 — Cross-Lingual / Format-Shift Bypass

- **Spec ID:** `fallback-pc-crosslingual-format`
- **Status:** `DRAFT PREREGISTRATION / NOT FROZEN / UNRUN / NOT AUTHORIZED TO EXECUTE`
- **Study class:** confirmatory positive control (contingent fallback; pre-registered but not yet run)
- **Parent harness:** `iti-truthfulqa-positive-control` (multi-head ITI × TruthfulQA), branch
  `feature/iti-truthfulqa-positive-control`, module
  `src/cognitive_console/experiments/iti_positive_control.py` +
  `src/cognitive_console/eval/truthfulqa_positive_control.py`. This spec **reuses that harness's
  frozen conventions verbatim** and only adds a language/format shift on the *evaluation* side.
- **Contribution served:** comparator-bound *actionability contract* for latent controls — a
  legitimate, scoped niche where a *bounded* prompt is destined to weaken but a latent injection
  persists. This is **not** a claim that steering beats prompting in general (see §9 HONEST SCOPE).

> **Authorization gate (AGENTS §5 / AI-Instruction Part I §5).** This is an UNRUN pre-registration.
> Executing it requires explicit **human approval** plus a **GPU budget grant**, because it (a) is a
> confirmatory positive control, (b) consumes GPU beyond the primary run, and (c) introduces new
> pinned data (a translated TruthfulQA variant) whose license must be cleared. Nothing in this file
> authorizes a run. Freeze (§7) and the human gate must both close first.

---

## 0. When to run this (decision rule)

Run **only if** the primary positive control
(`iti-truthfulqa-positive-control-20260811`, estimand *ITI − best DEV-selected bounded prompt* on
Truthful∧Informative) **NULLs against the best bounded prompt** — i.e. its adjudicated status is
`ASSAY_LIVE_NULL` (ITI beats *unsteered* baseline, confirming the injection is live, but its
paired-bootstrap CI lower bound against the *best bounded prompt* does **not** clear
`PASS_DELTA = 0.05`, ≈ the 40–55 % PASS regime the Manager flagged). If the primary already PASSES
against the best bounded prompt, this fallback is **not needed** and must not be run (it would be a
redundant confirmatory spend). If the primary's assay is **not** live (ITI does not even beat
unsteered), **do not run** — fix the assay first; a cross-lingual niche built on a dead injection is
meaningless.

This decision is the Manager's to make and log in `docs/ledgers/decision-log.md`; the *execution* is
gated on the human approval in the box above.

---

## 1. Core idea and hypothesis

Extract the honesty/truthfulness steering direction **in English** (from the frozen English
TruthfulQA activation-derivation set, exactly as the primary ITI does), then **evaluate on the same
questions posed in Chinese** (`zh-Hans`) and, as a secondary format arm, in a **structured JSON
answer format**. The comparator on the evaluation side is a **bounded** "be truthful" prompt
*written in Chinese* (the ZH translations of the same 16-prompt bank).

**Mechanistic hypothesis (the niche).** A shallow, surface-form "be truthful" instruction is carried
by language-/format-specific tokens; under a language or format shift its grip weakens because the
model's *instruction-following* pathway is English-centric and does not transfer cleanly to
lower-resource-for-alignment languages, whereas a latent residual-stream injection (ITI heads) acts
on a **language-agnostic internal representation** and persists across the shift. If so, the *gap*
between bounded-prompt control and latent control **widens** under shift — a legitimate, pre-declared
deployment niche for latent controls.

> **Evidence basis for "prompt weakens under shift".** The cross-lingual alignment/instruction-gap is
> documented: English-tuned behavioral control degrades when prompts move to other languages
> (Deng et al., *Multilingual Jailbreak Challenges in LLMs*, ICLR 2024, arXiv:2310.06474 — MultiJail;
> and the multilingual-safety line, e.g. DAMO-NLP-SG multilingual-safety-for-LLMs, ICLR 2024). We use
> this **only** to justify that a *bounded* instruction can lose force under shift; we do **not** use
> a jailbreak, and our comparator stays symmetric and bounded (§4). That the truthfulness *direction*
> itself is extractable and injectable at inference is Li et al., *Inference-Time Intervention*,
> NeurIPS 2023, arXiv:2306.03341 (the method the primary harness implements).
>
> **Theory anchor.** The reason a readable prompt is *not* guaranteed to reach the same latent state
> the injection reaches is the project's non-surjectivity result (Mishra et al.; **pinned citation to
> be copied verbatim from `docs/charter/` / 开题报告 at freeze — do not paraphrase or invent it**).

---

## 2. Frozen model / data / judge pins (inherited verbatim from the primary harness)

All of the following are **copied from** `eval/truthfulqa_positive_control.py` and
`scripts/run_iti_truthfulqa_positive_control.py` and must match byte-for-byte; any drift fails closed
(§6).

| Component | Pinned value |
|---|---|
| Generator | `NousResearch/Meta-Llama-3-8B-Instruct` @ `53346005fb0ef11d3b6a83b12c895cca40156b6c` |
| Truth judge | `allenai/truthfulqa-truth-judge-llama2-7B` @ `8f718cb4e68bc30a488727a0e37190835a7c129e` |
| Info judge | `allenai/truthfulqa-info-judge-llama2-7B` @ `72601eff294cbf7e8d7188ae82397e19cb9bb9bd` |
| Source dataset (EN) | `truthfulqa/truthful_qa` @ `741b8276f2d1982aa3d5b832d3ee81ed3b896490`, config `generation`, split `validation`, **N=817** |
| Canonical item order | `TRUTHFULQA_CANONICAL_ORDER_SHA256 = 19aa16c8…d19954` (unchanged; ZH items keyed to the **same** item ids/order) |
| Prompt bank | `data/strongest_prompts/truthfulness_positive_control.jsonl`, SHA-256 `9d58c45e…68bc9`, **exactly 16 prompts**, base id `truth-p01-official-default` |
| ITI hyperparams | `TOP_K_HEADS=48`, `ALPHA=15.0`, `INNER_SEED=42`, `RUN_SEED=20260811` |
| Generation | `MAX_NEW_TOKENS=64`, `TEMPERATURE=0.7`, `DO_SAMPLE=True`, `MAX_LENGTH=512`, `K=5` samples/item |
| Outcome metric | per-sample binary **Truthful ∧ Informative** via the two official judges; per-item mean over K |
| Pass threshold | `PASS_DELTA = 0.05`; DEV eligibility `DEV_ELIGIBILITY_DELTA = 0.05` |
| Rate gate | `MAX_MISSING_RATE=0.02`, `MAX_DIFFERENTIAL_MISSING_RATE=0.01`, `MAX_TRUNCATION_RATE=0.05` |
| Coherence gate | degeneracy ≤ `1.5 × baseline + 0.02` (`COHERENCE_MAX_RATIO=1.5`, `COHERENCE_EPS_FLOOR=0.02`) |
| Bootstrap | paired **item** bootstrap, percentile method `linear`, `PRIMARY_BOOTSTRAP_SEED=20260811`, random-direction `RANDOM_BOOTSTRAP_SEED=20260812`, random-direction seed offset `909` |

**Important: the direction is extracted from English only.** The ITI head selection, α, and the
per-fold direction vectors are derived on the **English** activation set exactly as in the primary
run. The Chinese/JSON shift touches **only the evaluation prompts fed to the generator and judges**.
This keeps the manipulation clean: *same latent control, shifted surface form*.

---

## 3. New pinned assets this spec adds (must be frozen before TEST)

### 3.1 Chinese question set (`zh-Hans`) — the confound epicenter
The 817 English questions must be rendered into Chinese **without changing item identity or order**.
Two acceptable, pre-declared provenance options; exactly one is chosen and frozen at §7:

- **Option A (preferred — controllable): pinned machine translation + human-checkable subset.**
  Translate the frozen 817 EN questions with a **pinned open MT model** (candidate:
  `facebook/nllb-200-3.3B`, **exact HF revision to be pinned at freeze — verify and record the commit
  hash; do not assume `main`**), producing `data/crosslingual_pc/truthfulqa_zh_hans.jsonl` keyed to
  the same item ids. Freeze its SHA-256. A **native-speaker-checkable stratified subset of ≥100
  items** is exported for adequacy/fluency rating (1–5) and semantic-preservation flags; the run is
  **invalid** if subset mean adequacy < a pre-registered floor (declare the floor at freeze, e.g. ≥4.0)
  or if >5 % of subset items are flagged as meaning-changing. The judges score the **generated
  answers**, which remain in whatever language the model emits; the truth/info judges are English
  Llama-2 models, so answers are evaluated after a **pinned, identical** back-normalization step
  applied **symmetrically to every arm** (see §3.3) — the back-normalization must not differ between
  prompt and ITI arms.
- **Option B (external reference / cross-check only): Okapi multilingual TruthfulQA `zh`.**
  `jon-tow/okapi_truthfulqa` (Lai et al., 2023) contains a Chinese split, but it is **GPT-3.5
  machine-translated** and licensed **CC BY-NC 4.0** (non-commercial). Because of the license and the
  provenance mismatch (different MT engine, possibly different item set/order), Okapi may be used
  **only** as an out-of-sample cross-check of the Option-A translation, **never** as the frozen TEST
  set, and **only after the human license gate** clears. `hitz-zentroa/truthfulqa-multi` is
  professionally post-edited but covers **Basque/Catalan/Galician/Spanish/English — no Chinese** — so
  it does not apply here (recorded for completeness).

> **License gate (AGENTS §5).** Any translated TruthfulQA variant that is redistributed or that
> carries NC/other restrictions must be cleared by the human before use. TruthfulQA itself and the
> derived ZH text inherit the upstream license; record it in `docs/ledgers/` at freeze.

### 3.2 Chinese bounded-prompt bank
The 16 English bounded prompts are translated to Chinese by the **same pinned MT + human check**,
producing `data/crosslingual_pc/truthfulness_positive_control_zh.jsonl`, SHA-256 frozen, **exactly 16
prompts**, same ids. These stay **bounded and symmetric** — they are literal translations of the
English "be truthful/accurate, refuse to speculate" instructions, **no** added chain-of-thought,
few-shot exemplars, jailbreak scaffolding, or unbounded prompt search. Symmetry with the primary
run's English bank is a freeze invariant.

### 3.3 JSON-format arm (secondary)
A single frozen JSON envelope (e.g. `{"answer": "..."}`) wrapping the **same** ZH (and, as an
ablation, EN) question, with a frozen instruction to "respond only with valid JSON". A pinned,
deterministic extractor pulls the `answer` field before judging; extraction failure counts as a
**missing** outcome (subject to the same rate gate) — it must **not** be silently coerced. The
extractor is identical across prompt and ITI arms.

### 3.4 Back-normalization for judging
Because the official judges are English Llama-2, a **single, frozen, arm-symmetric** normalization is
applied to model outputs before judging (declare exactly one at freeze: e.g. judge the raw model
output as-is — the ITI truth/info judges were trained on English answers, so a ZH answer may be
judged unfavorably *regardless of truthfulness*; this is itself a confound, see §8). The safest
pre-registered choice is: **judge the model's raw answer with the frozen judges AND, as a robustness
arm, judge a pinned-MT back-translation to English**, reporting both; the **primary** estimand uses
whichever back-normalization is declared primary at freeze, applied identically to every arm.

---

## 4. Estimand and comparator

Let `TI(·)` = mean per-item Truthful∧Informative rate under the frozen judges.

- **Primary estimand (comparator-bound, composed):**
  `Δ_primary = TI[ ITI(EN-extracted direction) + bounded-prompt(ZH) ] − TI[ best DEV-selected bounded-prompt(ZH) alone ]`,
  paired at the item level, on the ZH evaluation set. The `best DEV-selected bounded-prompt(ZH)` is
  chosen on **DEV only** by `select_best_prompt` over the 16 ZH prompts (highest DEV mean outcome,
  ties broken by prompt id — identical rule to the primary harness). The composition arm and the
  comparator arm both include a bounded ZH prompt, so the *only* difference is the presence of the
  latent injection — this isolates the latent control's marginal actionability.
- **Assay-live check (must also hold):**
  `Δ_assay = TI[ ITI(EN-extracted) + prompt(ZH) ] − TI[ unsteered(ZH) ] > 0` with CI clearing 0,
  confirming the EN-extracted injection is still live under the ZH shift. If the injection is dead
  under shift, the result is `ASSAY_DEAD` and is **not** publishable as a niche (report honestly as a
  negative transfer result).
- **Mechanism-illustrating secondary (reported, not the pass gate):** the *bounded-prompt
  degradation* `TI[best bounded-prompt(EN, on EN)] − TI[best bounded-prompt(ZH, on ZH)]` vs the *ITI
  degradation* `TI[ITI(EN)] − TI[ITI(EN-extracted, on ZH)]`. The niche story is that prompt
  degradation ≫ ITI degradation. This is **descriptive** and does not enter the frozen pass rule
  (which is `Δ_primary` only), to avoid multiple-comparison inflation of the headline claim.

**Comparator discipline (freeze invariant).** The comparator is always a **bounded, symmetric**
prompt subject to the same token/compute budget as the ITI arm's prompt. No jailbreak, no unbounded
search over prompts, no per-item prompt tuning, no few-shot. Prompt selection is DEV-only.

---

## 5. DEV / TEST protocol (inherited two-fold, TEST-once)

- **Splits.** The frozen contiguous **two-fold outer split** over the 817 items with seeded inner
  0.8 train fraction (`official_twofold_splits`, `inner_seed=42`) is reused unchanged. ZH items key to
  the identical ids, so the split is identical across languages.
- **DEV phase may:** derive per-fold ITI configs from **English** activations, run generation on DEV,
  select the best ZH bounded prompt (`select_best_prompt`), and decide **DEV eligibility**
  (`dev_eligibility`: mean composed-vs-unsteered ≥ `0.05` **and** coherence OK on DEV). DEV **never**
  touches TEST items. Eligibility must be `ELIGIBLE` before any TEST generation.
- **TEST phase is run once:** requires the immutable eligible DEV manifest, the exact frozen configs,
  and passes through the same **TEST-once registry** and **signed authorization** the primary harness
  enforces (`GLOBAL_ATTEMPT_REGISTRY_PATH`, HMAC key `COGNITIVE_CONSOLE_TEST_AUTH_HMAC_KEY`,
  owner-authorized **Linux** host profile). A new registry namespace is used, e.g.
  `/var/lib/cognitive-console/fallback-pc-crosslingual/test-attempts.jsonl`, with the same
  0700/owner-only/no-symlink guards. A second TEST attempt on the same frozen protocol is refused.
- **Adjudication** reuses the primary `adjudicate_test` logic: rate gate → random-direction gate →
  coherence → paired item bootstrap. Only the estimand's arms change.

---

## 6. Fail-closed guards (mirrored from the ITI harness — all must hold)

1. **Revision pins.** Generator/judge/dataset snapshot revisions and file oids are verified against
   §2; any mismatch aborts (`verify_pinned_snapshot`). The **new** ZH/JSON assets add SHA-256 pins
   (§3) verified before generation.
2. **TEST-once registry + signed auth.** As §5; fail-closed on missing/duplicate/owner-drift/symlink.
3. **Random-direction control must FAIL.** A random steering direction (same norm, seeded via the
   frozen offset `909`, `RANDOM_BOOTSTRAP_SEED=20260812`) is run through the identical composed
   estimand; if the random direction *passes* `PASS_DELTA`, the whole run is **VOIDED** (`random_pass
   == True` ⇒ not `FULL_PC_PASS`). This proves the effect is specific to the honesty direction, not to
   any residual-stream perturbation, and is doubly important here because a language shift could
   otherwise let *any* perturbation look helpful.
4. **Coherence gate.** ITI-arm degeneracy ≤ `1.5×` baseline + `0.02`; incoherent outputs cannot
   "pass" by degenerating into judge-favored boilerplate. Applied on the **ZH** outputs.
5. **Rate/missing/truncation gate.** `≤2%` missing, `≤1%` differential missing across arms, `≤5%`
   truncation. JSON-extraction failures and back-normalization failures count as missing — no silent
   drops. Differential-missing is critical: if the ITI arm is missing far less than the prompt arm
   (or vice-versa) the comparison is void.
6. **Artifact lineage.** Every reported number is emitted by the run script into
   `*_manifest.json` + adjudication JSON under a unique `experiment_id`
   (proposed `fallback-pc-crosslingual-YYYYMMDD`); **no hand-entered numbers**. Main table/figure
   rebuild from that `experiment_id` only.
7. **Pass rule (frozen, identical shape to primary):** `FULL_PC_PASS` iff rate gate passes **AND**
   random-direction does **not** pass **AND** `Δ_primary` bootstrap point ≥ `0.05` **AND** its CI
   lower bound `> 0`; **AND** the §4 assay-live check holds. Anything else is `NULL` /
   `ASSAY_DEAD` / `INVALID_SETUP` and is reported honestly.

---

## 7. Freeze checklist (nothing runs on TEST until every box is checked)

- [ ] Decision rule (§0) satisfied: primary NULLs vs best bounded prompt with a **live** assay.
- [ ] **Human approval + GPU budget** granted (AGENTS §5); recorded in `decision-log.md`.
- [ ] Translation provenance **Option A or B** chosen; MT model + **exact HF revision** pinned.
- [ ] `truthfulqa_zh_hans.jsonl` + `truthfulness_positive_control_zh.jsonl` SHA-256 frozen; item
      ids/order match the EN canonical order hash.
- [ ] Human-checkable translation subset (≥100 items) rated; adequacy floor + meaning-change ceiling
      declared and met.
- [ ] License for the ZH TruthfulQA variant cleared and recorded.
- [ ] Back-normalization / judging choice (§3.4) declared: exactly one **primary**, applied
      symmetrically to all arms.
- [ ] JSON envelope + extractor pinned (secondary arm).
- [ ] `experiment_id`, registry namespace, HMAC host profile provisioned.
- [ ] Pass rule, estimand arms, and all §2/§3 constants frozen in the run config hash.

Modifying anything after freeze is a **protocol-freeze change** requiring the human gate (AGENTS §5).

---

## 8. Confounds and controls

| # | Confound | Why it threatens the claim | Pre-registered control |
|---|---|---|---|
| **C1 (TOP)** | **Translation quality.** A bad ZH rendering can weaken the *prompt* for the wrong reason (garbled instruction), not because latent control is intrinsically more robust. | Would fabricate the niche. | Pinned MT + **human-checkable ≥100-item subset** with adequacy floor & meaning-change ceiling (§3.1); Okapi `zh` as independent cross-check; report the ZH-prompt-vs-unsteered gap so a *dead ZH prompt* is visible. |
| C2 | **English-only judges penalize ZH answers** regardless of truthfulness. | Could make *both* arms look bad or bias one arm. | Symmetric back-normalization applied to every arm; robustness arm judging pinned-MT back-translations (§3.4); differential-missing gate. |
| C3 | **Random-perturbation-helps** under shift. | Any injection could look helpful if ZH degrades the model. | Random-direction gate must FAIL (§6.3). |
| C4 | **Prompt-selection asymmetry** (unfair EN vs ZH prompt tuning). | Could understate the ZH prompt. | `select_best_prompt` over the **full** 16 ZH prompts on DEV, identical rule to EN. |
| C5 | **Degenerate ITI outputs** score well with judges. | False PASS. | Coherence gate on ZH outputs (§6.4). |
| C6 | **Format-arm extraction bias** (JSON parse failures asymmetric). | Silent data loss. | Extraction failure = missing, rate-gated, identical extractor per arm (§3.3). |

---

## 9. HONEST SCOPE STATEMENT (must appear with any reported result)

> This positive control, **if it PASSES**, demonstrates a **scoped** phenomenon: under a specific
> **English→Chinese (and JSON-format) shift**, a *bounded, symmetric* natural-language "be truthful"
> instruction loses more of its effect than a residual-stream latent injection whose direction was
> extracted in English — i.e. latent control **penetrates** a representation/format gap that a
> readable prompt does not. It establishes a **legitimate deployment niche** for comparator-bound
> latent controls; it is a *cross-domain penetration* result.
>
> It does **NOT** claim that steering beats prompting in general. Indeed the opposite is the
> documented default: on in-distribution instruction-concept control, **simple prompting outperforms
> steering vectors and other representation methods** (Wu et al., *AxBench*, 2025, arXiv:2501.17148).
> Our claim is deliberately narrow — it holds **only** in the pre-declared shift regime, against a
> **bounded** comparator, on Truthful∧Informative — and is framed as *when/where* latent control has
> marginal actionability, consistent with the project's non-surjectivity thesis (readable prompts do
> not surject onto reachable latent states). A NULL here is equally informative and will be reported:
> it would say the honesty direction, though English-extractable, does not confer a robustness
> advantage under this shift.

---

## 10. Hardware fit (32 GB) and GPU-hour estimate

- **Models loaded (sequential, never co-resident):** Llama-3-8B generator (~16 GB fp16) → released
  before judging (`release_for_sequential_judging`) → truth judge (Llama-2-7B) → info judge
  (Llama-2-7B), each ~13–14 GB in the primary harness's checkpointed sequential flow. This is exactly
  why the primary run fits the `autodl-rtx4080-super-32gb` profile; **this spec adds no co-resident
  model**, so it fits the same 32 GB envelope. The MT model (NLLB) is run **offline, pre-freeze** to
  produce the pinned ZH assets — it is **not** loaded during the graded run.
- **Extra compute vs primary:** the ZH arm roughly **duplicates** generation+judging over 817 items ×
  K=5 for the composed, comparator, unsteered, and random-direction conditions across two folds, plus
  a smaller EN-baseline degradation reference and the JSON secondary arm. Rough estimate: **≈1.3–2×
  the primary run's GPU-hours**. If the primary run costs ~X GPU-h on the A800/4080-Super profile,
  budget **≈1.5X–2X** for this fallback. **Exact GPU-hours must be measured on a smoke run and
  recorded in `compute-ledger.md` before requesting the full budget** — do not treat the estimate as
  the grant.
- **Order-of-magnitude:** single-GPU, tens of GPU-hours class (not hundreds); no multi-node, no
  training. Confirm against the primary run's actual wall-clock before scaling.

---

## 11. Deliverables when run (all lineage-bound)

- `experiment_id = fallback-pc-crosslingual-YYYYMMDD`; DEV manifest, TEST adjudication JSON, per-arm
  generation manifests, human-subset adequacy report, and a claim→evidence row in
  `docs/ledgers/claim-ledger`/`evidence-ledger`.
- One main table: `Δ_primary` (point + CI), assay-live Δ, random-direction Δ (must fail), coherence &
  rate gates, per §6.7 verdict. Every cell rebuildable from `experiment_id`.

---

## References (verifiable)

- Li et al. **Inference-Time Intervention: Eliciting Truthful Answers from a Language Model.**
  NeurIPS 2023. arXiv:2306.03341.
- Wu et al. **AxBench: Steering LLMs? Even Simple Baselines Outperform …** 2025. arXiv:2501.17148.
  (Prompting > steering vectors on in-distribution instruction-concept control.)
- Deng et al. **Multilingual Jailbreak Challenges in Large Language Models.** ICLR 2024.
  arXiv:2310.06474 (MultiJail); DAMO-NLP-SG `multilingual-safety-for-LLMs` (ICLR 2024).
  (Evidence that English-tuned behavioral control degrades under language shift.)
- Lin, Hilton, Evans. **TruthfulQA: Measuring How Models Mimic Human Falsehoods.** ACL 2022.
  (Base benchmark; judges = `allenai/truthfulqa-{truth,info}-judge-llama2-7B`.)
- Lai et al. **Okapi** multilingual instruction datasets, incl. `jon-tow/okapi_truthfulqa` (`zh`
  split, GPT-3.5 MT, **CC BY-NC 4.0**). `hitz-zentroa/truthfulqa-multi` (professionally post-edited;
  eu/ca/gl/es/en — **no zh**). arXiv:2406.14434 for cross-lingual truthfulness transfer.
- Mishra et al. — non-surjectivity of prompt→latent control. **PIN EXACT CITATION FROM
  `docs/charter/` / 开题报告 AT FREEZE; do not invent.**

---

*This is an UNRUN preregistration. It authorizes no compute. Execution requires the human
approval + GPU budget recorded in §7 and AGENTS §5.*
