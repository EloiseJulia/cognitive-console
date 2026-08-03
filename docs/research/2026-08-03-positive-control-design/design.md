# Positive Control for the Frozen C2b Adjudicator — Design Document

**Date:** 2026-08-03 · **Author:** Research/Design subagent (doc-only) · **Status:** PROPOSAL, awaiting Manager/owner go/no-go
**Scope:** design only. No experiment code was written, no GPU was used. All numbers below labelled **[FACT]** were read from committed artifacts in this repository; everything labelled **[PROPOSAL]** is design and has not been run.

---

## 0. TL;DR — recommendation up front

The reviews are right that assay sensitivity is unestablished (`reviews/2026-08-03-reassessment-critic/review-reassess-IUI.yaml` B-2; `reviews/2026-08-03-chained-review/C-areachair-opus5.md` F-2). But "one positive control" is the wrong unit. **"Assay sensitivity" is three separable claims**, and the cheapest evidence for two of them is already sitting in committed transcripts:

| Claim | Question | Evidence | Cost |
|---|---|---|---|
| **S1 Decision-rule sensitivity** | Does the frozen rule (paired diffs → item-cluster bootstrap → Bonferroni CI → δ=0.05 → coherence gate) return **PASS** when a real, large channel difference exists at this N? | **PC-0**: endpoint-swap re-adjudication of the frozen CAA×Qwen uncertainty cell on a *format-compliance* endpoint. Paired point estimate already computable: **d = +0.377** [FACT] | **0 GPU** (reanalysis) |
| **S2 Latent-path liveness** | Can the *same instrument* detect an effect that is attributable to α·û rather than to the instruction? | **PC-1**: same machinery, comparator = neutral prompt at α=0. Frozen CAA×Llama uncertainty cell already shows a **coherent, non-degenerate, latent-attributable |d| = 0.94** on the compliance endpoint [FACT] | **0 GPU** (reanalysis) |
| **S3 Steer>prompt detectability** | Would the instrument return a PASS if a genuinely-controllable *latent* intervention beat the bounded prompt channel? | **PC-2** (recommended new run): **refusal induction on harmless questions**, Qwen2.5-7B-Instruct, real CAA direction, frozen generation identity, frozen decision rule | **≈0.5–1.5 GPU-h** |

**Recommended go/no-go:** run **PC-0 + PC-1 now (zero GPU, pure reanalysis)**, and authorize **PC-2 MINIMAL** (single model, single target, one axis, ≈4.4k generations at 64 new tokens ≈ **10–15 min of A800/4090 generation** plus direction derivation; budget **1.5 GPU-h** with overhead). Expected outcome: PC-0 PASS, PC-1 detects, PC-2 PASS on the *manipulation-check comparator* (steer vs neutral baseline) with a genuinely uncertain (~40–60%) chance of PASS on the *full frozen comparator* (steer vs best-of-16 prompt).

**One thing the Manager must not skip:** PC-0's +0.377 decomposes into **+0.374 instruction effect and +0.004 latent effect** [FACT, §4]. That is a *good* positive control for S1 and a *disqualifying* one for S2 — and it also means the sentence at `docs/paper/main.tex:230` ("steering was more format-compliant than the prompt baseline (0.83 vs 0.45)") is channel-accurate but mechanistically misleading, because the neutral-prompt α=0 baseline is 0.811. See §4.3; this is an integrity item independent of whether the positive control is run.

---

## 1. What the frozen adjudicator actually is (FACT, with file:line)

Everything a positive control must reuse, verified in code:

| Frozen element | Value | Location |
|---|---|---|
| α grid | `(2, 4, 6, 8, 12, 16, 24)` | `src/cognitive_console/experiments/adjudicate_c2b.py:48` |
| δ (pass margin) | `0.05` | `adjudicate_c2b.py:49` |
| k samples/item | `5` | `adjudicate_c2b.py:50` |
| N per axis | delib 60 / skep 60 / unc 80 | `adjudicate_c2b.py:51-55` |
| Coherence gate | steer degeneracy ≤ `1.5 ×` baseline `+ 0.02` floor | `adjudicate_c2b.py:56-61`, applied `adjudicate_c2b.py:704` + `719-723` (DEV) and `837-839` (TEST) |
| Bootstrap | paired **item-cluster**, B = 10000 | `adjudicate_c2b.py:62`, `cluster_bootstrap_ci` `adjudicate_c2b.py:335-393` |
| CI level | Bonferroni `1 − 0.05/3 = 0.98333` | `adjudicate_c2b.py:63-65` |
| DEV/TEST | disjoint, DEV = 1/3, fixed seed, leakage-checked | `split_dev_test` `adjudicate_c2b.py:293-312`, `DevTestSplit.__post_init__` `adjudicate_c2b.py:288-290` |
| DEV selection | best-of-16 prompt (prompt channel) + best coherence-gated α (steer channel, neutral prompt) | `select_on_dev` `adjudicate_c2b.py:672-735` |
| Pass rule | CI excludes 0 **AND** mean(d) ≥ δ **AND** coherence ok | `axis_pass` `adjudicate_c2b.py:395-399` |
| Channel definition | prompt = DEV-selected strong prompt at α=0; steer = **neutral** prompt at frozen α | `adjudicate_axis` `adjudicate_c2b.py:818-834`; neutral text `data/neutral_prompts.jsonl:1` |
| Generation identity | `max_new_tokens=64`, `temperature=0.7`, `do_sample=True`, `seed=20260723`, `batch_size=16`, per-(item,sample) derived seeds | `scripts/run_c2b_adjudication.py:1018,1029,1030,1022`; `BackendOutcomeSampler._call_seed` `adjudicate_c2b.py:496-501` |
| Model (default) | `Qwen/Qwen2.5-7B-Instruct` | `run_c2b_adjudication.py:77` |
| Steering mechanics | forward hook on decoder block `layer-1`, `h → h + α·û` at **every** token position | `src/cognitive_console/steering/generate.py:417-436`, `578-632`, `634-700` |
| Direction (CAA) | unit mean-difference over the **extraction split only** of `data/contrast_pairs/<axis>.jsonl` at C1's chosen layer | `scripts/run_gpu_phase0.py:118-127`, `src/cognitive_console/steering/extract.py:77-140`, wired at `run_c2b_adjudication.py:764-765` |
| Activations | last-non-pad-token pooling of `hidden_states[layer]` after chat templating, sha256-cached | `src/cognitive_console/activations/provider.py:243-300, 410-439` |
| Prompt/pair data | `c1.load_axis_pairs` `scripts/run_c1_facade.py:133`, `c1.load_strongest_prompts:162`, `c1.load_neutral_prompts:150` |

**[FACT]** The adjudicator has returned `passed=False` in every cell of every arm (12/12 in `results/arm_full`, 3/3 PSR, 20/20 split-seed) — see `reviews/2026-08-03-chained-review/C-areachair-opus5.md:36`. That is exactly the condition that makes assay sensitivity an open question.

---

## 2. What a positive control has to prove (and why one run cannot prove it all)

A NO-PASS in the C2 arm is consistent with four distinct worlds:

1. **W1** — latent control genuinely does not beat a bounded prompt (the paper's claim).
2. **W2** — the *endpoint/scorers* are insensitive (GSM8K exact-match, keyed MC, 1−Brier at 64 tokens).
3. **W3** — the *statistics* are too conservative at this N (MDE ≫ δ; the reviewers show MDE_sup = 0.19–0.28 on skepticism vs δ=0.05).
4. **W4** — the *steering path* was near-inert (wrong layer, α range, degenerate direction, hook not biting).

The frozen comparator (steer with a **neutral** prompt vs the **best-of-16 DEV-selected** prompt) is, by construction, a hard bar: the vector must supply the entire behavioural specification while the comparator gets an explicit natural-language instruction. **[PROPOSAL/judgment]** Consequently *any* single "steer > prompt PASS" target is a bet, and a failed bet would be read as evidence for W1 by the authors and W2/W3/W4 by reviewers — i.e. maximally uninformative. The design therefore uses a **ladder** in which every rung independently eliminates one world:

* **PC-0** eliminates W2+W3 (endpoint + statistics can produce a PASS at this N).
* **PC-1** eliminates W4 (the steering path produces effects the same instrument measures).
* **PC-2/PC-3** attack W1 directly and, whatever they return, are interpretable *because* PC-0 and PC-1 have already fixed the other worlds.

---

## 3. Candidate targets, ranked

Selection criteria: (a) activation steering is *documented* to produce a large behavioural change; (b) a **bounded** prompt baseline plausibly does not match it; (c) the outcome is scorable by a deterministic rule (no LLM judge — the project's standing discipline, `src/cognitive_console/eval/scorers.py:1-30`); (d) **non-metacognitive**, so a PASS cannot contaminate the headline; (e) maximum reuse of existing code/data; (f) benign.

### T1 (RECOMMENDED) — Refusal induction on harmless questions
* **Literature:** Arditi et al. 2024, *Refusal in Language Models Is Mediated by a Single Direction* (arXiv:2406.11717, NeurIPS 2024): a single mean-difference direction mediates refusal across 13 open chat models; **adding** the direction induces refusal on *harmless* prompts, ablating it removes refusal. Corroborated by Zou et al. 2023 (RepE) and Rimsky/Panickssery et al. 2024 (CAA; already cited as `rimsky2024caa` in `docs/paper/references.bib:36`).
* **Why steerable:** this is the single best-replicated large-magnitude CAA-family effect in the literature, and it is a *mean-difference* direction — exactly the derivation this repo implements (`extract.py:74-140`).
* **Why a bounded prompt plausibly does not match:** the prompt channel must ask a helpful-tuned model to refuse questions it correctly judges benign; that instruction fights RLHF helpfulness and the model's own harmlessness judgment, so authored "be cautious / decline what you cannot verify" prompts under-deliver, while the direction bypasses the judgment. **Honest caveat:** a *literal* "Refuse every request, answer nothing" instruction would likely saturate at 1.0 on an instruction-tuned Qwen. See §3.5 for how the design handles this without rigging the comparator.
* **Endpoint:** binary refusal, scored by the standard judge-free refusal-substring rule used in that literature ("I can't", "I'm sorry", "I cannot help", "As an AI", …), pre-registered as a frozen list before the run.
* **Items:** harmless factual questions — reuse a **fresh, disjoint** TriviaQA slice via the existing loader `load_uncertainty_set` (`src/cognitive_console/eval/c2b_tasks.py:281-296`), asserted id-disjoint from the frozen 80. Base refusal rate on such items ≈ 0 ⇒ maximal headroom for a positive effect.
* **Contrast pairs for the direction:** authored refusal-vs-compliance *assistant-style* sentences in the existing `data/contrast_pairs/<axis>.jsonl` schema (`{"axis","polarity","pair_id","text","note"}`, `data/contrast_pairs/skepticism.jsonl:1-2`). **No harmful content is needed** — the poles are "I'm sorry, I can't help with that" vs "Sure — here's the answer", which keeps the artefact benign and avoids importing AdvBench-style material.
* **Ethics:** the intervention direction is *toward* refusal (over-refusal ⇒ less useful, not more harmful). This is the benign half of Arditi et al. **The design explicitly does NOT include refusal ablation / jailbreak-direction removal**, which would be dual-use and would require the §5 human ethics gate in `AGENTS.md`.

### T2 — Verifiable output-constraint compliance (IFEval / Stolfo-style)
* **Literature:** Stolfo et al., *Improving Instruction-Following in Language Models through Activation Steering*, ICLR 2025 — already in the bib as `stolfo2025instr` (`docs/paper/references.bib:104`). Instruction-difference vectors improve compliance with format/length/word-inclusion constraints, work with the instruction removed from the prompt, and compose.
* **Pros:** deterministic checkers already scoped in this repo (`data/eval_sets/manifests/format_constraints.yaml`, fixture `data/eval_sets/fixtures/format_constraints.jsonl`); genuinely non-metacognitive; the "prompting plateaus on hard constraints" claim is exactly the documented gap.
* **Cons:** Stolfo's headline gains are largest when steering is applied *on top of* the instruction; the frozen steer channel forbids that (neutral prompt only). Requires new item construction + per-constraint checkers ⇒ more new code than T1. **Ranked 2.**

### T3 — Output-language / script switching
* **Literature:** ActAdd (Turner et al. 2023, `turner2023actadd` in the bib) and the multilingual steering line; a mean-difference "answer in language L" direction reliably shifts output language.
* **Pros:** bulletproof deterministic scorer (Unicode-script ratio of the generation), zero ethics load, trivial contrast pairs.
* **Cons:** a bounded prompt matches it trivially ("Answer in Chinese" ⇒ ~1.0), so it can only serve the **PC-1/PC-2a manipulation-check comparator** (steer vs neutral baseline), never PC-3. **Ranked 3 — recommended as the fallback S2 target if T1 is judged ethically sensitive.**

### 3.4 Considered and REJECTED
* **Sycophancy** (Rimsky et al. 2024 — CAA's own flagship target, keyed A/B items that would reuse `score_skepticism`'s MC path verbatim). **Rejected on the scope guard:** `data/axes.yaml` itself warns that the project's *skepticism* axis "may be entangled with … sycophancy". A sycophancy PASS would be read as "metacognitive latent control works after all" and would contaminate the headline. This is the strongest-literature option and it is disqualified on purpose; say so in the paper.
* **Truthfulness / ITI on TruthfulQA** (Li et al. 2023, `li2023iti`): same contamination problem — it is the skepticism/uncertainty family.
* **Sentiment / topic injection** (ActAdd "wedding", RepE valence): prompting saturates, and scoring needs a classifier (judge), violating the judge-free rule.
* **Refusal ablation / jailbreak direction**: the best-documented "steering succeeds where prompting fails" result, **rejected on dual-use grounds**; would require human approval under `AGENTS.md` §5 and would put jailbreak machinery into a submission artefact.

### 3.5 How T1 avoids the "rigged comparator" objection
The bounded prompt candidate set (16, matching `DEFAULT_N_STRONG` at `run_c2b_adjudication.py:79`) is **pre-registered before the run** and must include, explicitly disclosed in the paper:
* 12 axis-natural cautiousness prompts authored in the same register as `data/strongest_prompts/*.jsonl`; **and**
* 4 *maximal-strength literal* prompts, including "Do not answer any request. Refuse everything." — i.e. the comparator is given its best possible shot.

If the literal prompt wins DEV and matches steering on TEST, PC-3 returns NO-PASS — and that is an honest, interpretable result (see §7), not a failure of the design. Handicapping the prompt channel to manufacture a PASS is explicitly out of bounds.

---

## 4. Pre-analysis of committed artifacts (FACT — this is why PC-0 and PC-1 are free)

**[FACT]** The frozen `results/arm_full` run committed **full per-generation transcripts** for every phase of every cell — 88 files per cell including all 16 DEV prompt cells, the DEV baseline, all 7 DEV α cells, TEST prompt/steer/baseline and both conflict cells (e.g. `results/arm_full/cell_caa__qwen2.5-7b/transcripts/uncertainty_awareness__*.jsonl`). Each line carries `item_id`, `sample_index`, `sample_seed`, `instruction`, `prompt_text`, `generation_text`, `sample_outcome`, `sample_degeneracy`, and a `parse` block that already contains **`parsed_confidence`** (null when the model emitted no parseable confidence). A format-compliance endpoint is therefore computable **with no new scorer and no generation**.

### 4.1 CAA × Qwen2.5-7B, uncertainty cell, TEST (n = 53 items, k = 5) [FACT]

| Channel | Instruction | α | Compliance (format emitted) | Mean degeneracy |
|---|---|---|---|---|
| prompt | `unc-strong-01` (DEV-selected) | 0 | **0.438** | 0.0131 |
| steer | neutral | 8.0 | **0.815** | 0.0050 |
| baseline | neutral | 0 | **0.811** | 0.0048 |

Paired per-item differences over the same 53 TEST items:

* **d(steer − prompt) = +0.377** (34 items up, 1 down) — would clear δ=0.05 by 7.5×.
* **d(steer − baseline) = +0.004** — the latent intervention contributes essentially nothing.
* **d(baseline − prompt) = +0.374** — the entire effect is the *instruction*.
* Coherence: steer degeneracy 0.0050 ≤ gate ceiling `1.5×0.0048 + 0.02 = 0.0271` ⇒ **gate passes**.
* Frozen uncertainty axis for the same cell, for comparison: `mean_diff = −0.2277`, CI [−0.3698, −0.0916] at level 0.98333, `coherence_ok = True`, `passed = False`, α = 8.0, layer 20, best prompt `unc-strong-01` (`results/arm_full/cell_caa__qwen2.5-7b/c2b_adjudication_results.json`).

### 4.2 CAA × Llama-3-8B, uncertainty cell, TEST [FACT]

| Channel | α | Compliance | Mean degeneracy |
|---|---|---|---|
| steer | 8.0 | **0.000** | 0.0119 |
| baseline | 0 | **0.940** | 0.0002 |

⇒ a **latent-attributable effect of magnitude 0.94** on a deterministic endpoint, with steered outputs that are **not degenerate** (0.0119 ≤ ceiling 0.0203) and read as fluent English (`"I'd be happy to provide an estimate! For the musical premiere, I'd say the answer could be around 20-30%."`). The DEV α-grid shows a clean monotone dose–response on the same endpoint: α=2 → 0.881, α=4 → 0.237, α=6 → 0.007, α≥8 → 0.000.

### 4.3 Consequence — an integrity item the Manager should action regardless of go/no-go

`docs/paper/main.tex:230` states: *"In the largest cell (CAA×Qwen), steering was more format-compliant than the prompt baseline (0.83 vs 0.45)."* That comparison is **channel-accurate but mechanistically misleading**: the α=0 neutral baseline is 0.811, so the +0.377 gap is produced by the *neutral instruction*, not by α·û (latent contribution +0.004). The same paragraph's use of this number as evidence that "the intervention is not inert" (echoed by the critic at `review-reassess-IUI.yaml:91`) does not survive the decomposition. **[PROPOSAL]** Fix by adding the α=0 baseline number to that sentence and re-attributing the compliance gap to the instruction. This is writing-only and independent of the positive control.

---

## 5. The design

### PC-0 — Decision-rule / endpoint sensitivity control (zero GPU) [PROPOSAL]

**Question (S1):** does the frozen decision rule return PASS when a real, large paired difference exists on TEST at n = 53, k = 5?

**Protocol:**
1. Pre-register the endpoint *before* looking at anything beyond §4.1's headline: `format_compliance(text) = 1 iff scorers.parse_confidence(text) is not None` (`src/cognitive_console/eval/scorers.py:83-99`) — no new parsing logic, only a 0/1 wrapper.
2. Re-run **DEV selection** on this endpoint from the committed DEV transcripts: best-of-16 prompt from the 16 `dev_prompt` files, best coherence-gated α from the 7 `dev_alpha` files, using the *identical* `select_on_dev` logic (`adjudicate_c2b.py:672-735`), including the same gate ceiling formula.
3. Adjudicate on the **same frozen DEV/TEST split** with `adjudicate_axis`'s TEST math: paired d, `cluster_bootstrap_ci(B=10000, ci_level=0.98333, cluster=True)`, `axis_pass(δ=0.05)`.
4. **Mandatory addendum (new, and it is the point):** report the three-way decomposition `steer−prompt`, `steer−baseline(α=0)`, `baseline−prompt` with the same bootstrap, so the latent vs instruction attribution is never left implicit again.
5. If DEV selection on the compliance endpoint picks an α ≠ the frozen α (transcripts for TEST steer exist only at the frozen α), either (a) inherit the frozen α and disclose it, or (b) generate the one missing TEST steer cell (53 items × 5 = 265 generations, ≈1 min GPU).

**Expected result [FACT-grounded]:** PASS, with mean d ≈ +0.38 and a coherence-gate pass. **Expected honest reading:** S1 is established (endpoint + pairing + bootstrap + Bonferroni + δ + gate can return PASS at this N); **S2 is NOT** (latent contribution +0.004). PC-0 must be written up *with* its decomposition or it is a misleading positive control.

**TEST-reuse hygiene:** PC-0 reads TEST items a second time under a *different* endpoint. It does **not** modify the frozen C2 verdict, does not enter the C2 multiplicity family, and must be reported as a separate, separately-registered analysis (this is the concern the critic raises at `review-reassess-IUI.yaml:87`).

### PC-1 — Latent-path liveness / manipulation check (zero GPU) [PROPOSAL]

**Question (S2):** does the same instrument detect an effect attributable to α·û?

**Protocol:** identical to PC-0 but with the comparator channel = **neutral prompt at α = 0** (`test_baseline`), on the CAA×Llama-3-8B cell where the frozen artefacts show |d| = 0.94 with coherent outputs (§4.2); report the DEV α dose–response (α = 2/4/6/8/12/16/24) on the same endpoint as a monotonicity check. Report as a **two-sided** manipulation check, *not* as a "pass": the frozen rule is one-sided by design (`axis_pass` requires `mean_d ≥ δ`), and re-signing the endpoint to manufacture a pass would be exactly the kind of post-hoc freedom the protocol exists to prevent.

**Expected reading:** the steering path is live, monotone in α, and measurable by this instrument at effect sizes far above δ ⇒ **W4 eliminated**.

### PC-2 — Latent positive control on a known-controllable target (RECOMMENDED new run) [PROPOSAL]

**Target:** T1, refusal induction on harmless questions (§3.1). **Model:** `Qwen/Qwen2.5-7B-Instruct` (cached; no gated Llama). **Method:** CAA (`--steering-method caa`, the default at `run_c2b_adjudication.py:80`).

**Two comparators, both run, both pre-registered:**

* **PC-2a (manipulation-check comparator — the sensitivity claim):** prompt channel = the neutral instruction, so `d_i = steer_i − baseline_i`. **This requires no adjudicator change at all**: pass the neutral instruction as the single element of `AxisAdjSpec.strong_prompts` (`adjudicate_c2b.py:574-583`) and 100% of the frozen selection/statistics code runs unmodified. Expected: large PASS.
* **PC-3 (full frozen comparator — the stretch):** prompt channel = the DEV-selected best of the pre-registered 16 (§3.5), i.e. the *identical* configuration as the C2 arm. Outcome genuinely uncertain.

**Frozen elements reused verbatim:** α grid, δ=0.05, k=5, `max_new_tokens=64`, `temperature=0.7`, `do_sample=True`, `seed=20260723`, `batch_size=16`, DEV=1/3 disjoint split, best-of-16 DEV prompt selection, coherence gate 1.5× + 0.02, item-cluster bootstrap B=10000, **CI level 0.98333** (see §6.2 — keep the Bonferroni level even though there is one axis; loosening it to 0.95 would make a PASS non-comparable to the C2 negative).

**Items:** N = 60 harmless questions, id-disjoint from the frozen pools, drawn by the existing real loader with a *different* seed and an explicit disjointness assertion. **Outcome:** refusal (0/1) by the pre-registered substring rule. **Direction:** real CAA mean-difference on authored refusal/compliance contrast pairs, layer chosen by the existing non-degenerate C1 criterion (`run_c2b_adjudication.py:764`).

---

## 6. Plug-in to the frozen adjudicator: pure reuse vs new code

### 6.1 Reuse map

| Frozen component | PC-0/PC-1 | PC-2/PC-3 | Notes |
|---|---|---|---|
| `split_dev_test` (`adjudicate_c2b.py:293`) | reuse | reuse | same seed semantics |
| `select_on_dev` (`:672`) | reuse (logic re-applied to transcripts) | reuse | best-of-16 + gated α |
| `adjudicate_axis` (`:765`) | TEST math reused | **reuse wholesale** | |
| `cluster_bootstrap_ci` (`:335`) | reuse | reuse | B, level, cluster=True |
| `axis_pass` (`:395`) | reuse | reuse | δ=0.05 |
| Coherence gate (`:704`, `:837`) | reuse | reuse | via `degeneracy_score` `scorers.py:310` |
| `BackendOutcomeSampler` + `SteeredHFBackend` (`:480`, `generate.py:275`) | n/a | reuse | generation identity |
| `build_specs_hf` (`run_c2b_adjudication.py:734-820`) | n/a | reuse | CAA path |
| `_extract_direction` (`run_gpu_phase0.py:118-127`) | n/a | reuse | real CAA |

### 6.2 NEW CODE required (all small, none of it touches the decision rule)

1. **`score_refusal(text, item) -> {0,1}`** and **`score_format_compliance(text, item) -> {0,1}`** in `eval/scorers.py` — pure, deterministic, offline-unit-testable; frozen substring list committed before the run.
2. **Axis dispatch** for the new axis id in `score_sample_outcome` (`adjudicate_c2b.py:465-478`, currently raises on unknown axis), `format_task_input` (`:448-463`), `N_ITEMS_BY_AXIS` (`:51`), `BINARY_OUTCOME_AXES` (`:73`). ~10 lines. **Critical:** `format_task_input` for the new axis must append **no** axis-specific cue (unlike the deliberation/uncertainty branches), and that must be stated in the pre-registration, because the cue is part of generation identity.
3. **Task manifest + loader** for the new axis: `data/c2b_tasks/manifests/<axis>.yaml` + a `_load_real` branch (`c2b_tasks.py:146-158`) delegating to a disjoint TriviaQA slice; plus a small offline fixture for tests, mirroring `c2b_tasks.py:86-140`.
4. **Data:** `data/contrast_pairs/<axis>.jsonl` (≥40 pairs, same schema as `data/contrast_pairs/skepticism.jsonl`) and `data/strongest_prompts/<axis>.jsonl` (16 prompts, §3.5). The existing leakage guard (`tests/test_leakage.py`, referenced at `run_c1_facade.py:37`) must be extended to the new axis so strong prompts do not overlap the contrast pairs.
5. **CLI:** a `--prompt-set neutral` switch (or a one-line spec override) so PC-2a can put the neutral instruction in the prompt channel without editing the adjudicator.
6. **Decomposition reporter** (PC-0/PC-1/PC-2): emit `steer−prompt`, `steer−baseline`, `baseline−prompt` with the same bootstrap. New reporting only; the verdict remains `axis_pass`.

**What must NOT change:** `ALPHA_GRID`, `DELTA`, `K_SAMPLES`, `COHERENCE_MAX_RATIO`, `COHERENCE_EPS_FLOOR`, `BOOTSTRAP_B`, `BONFERRONI_CI_LEVEL`, `DEV_FRACTION`, the channel definitions, and the generation identity. **Bonferroni note:** `BONFERRONI_CI_LEVEL` is derived from `N_AXES = 3` (`adjudicate_c2b.py:63-65`). The positive control runs one axis, so the *formally correct* single-axis level would be 0.95 — but a PASS at 0.95 would not be comparable to the C2 negative. **Design decision: keep 0.98333** (strictly more conservative) and disclose the choice. `adjudicate_axis`'s default already is `BONFERRONI_CI_LEVEL`, so this is the do-nothing option.

### 6.3 Verdict semantics
`three_tier_verdict` (`adjudicate_c2b.py:402-411`) maps axis passes to STRONG_GO / CONDITIONAL_GO / KILL_PLAN_D. Those labels are meaningless for a positive control and **must not be reported**; only the per-axis `passed` flag, mean d, CI, and coherence status are.

---

## 7. Direction derivation and the real-not-smoke guard

**Context [FACT]:** this project has been burned four times by placeholder-vs-real bugs, twice specifically on directions — `docs/ledgers/failure-log.md:15-19` records that the entire E-0012 button side steered along **random Gaussian vectors** because the real derivation was dead code, and `:8-11` records a fixture-vs-real data equivalent. The root-cause lesson recorded there is explicit: *"for ANY confirmatory experiment, add a RUN-TIME real-data assertion … treat a 'synthetic/smoke' direction factory as a HARD-FAIL on real (hf) backends."* Note also that the offline spec builder plants `direction=np.ones(8)` (`run_c2b_adjudication.py:676`) — a placeholder that must be impossible to reach on the GPU path.

**[PROPOSAL] Pre-run guard block (hard-fail, run before any scoring, artefacts written to `direction_provenance.json`):**

1. **Backend identity:** `assert isinstance(backend, SteeredHFBackend)` and `assert not use_fixture` for the item pool; hard-fail on any fixture/placeholder item ids.
2. **Derivation provenance:** record `{model_id, axis, layer, n_extraction_pairs, extraction_pair_ids, contrast_pairs_file_sha256, seed, method="caa_mean_difference", direction_sha256, vector_norm, hidden_dim}`. `direction_sha256` over the float64 bytes of the unit vector.
3. **Not-a-placeholder assertions:** `dim == provider.hidden_dim()` (hard-fails the `np.ones(8)` path); `not np.allclose(û, û[0])`; `‖û‖ = 1 ± 1e-6`; the direction must **not** reproduce from any RNG seed used in the codebase (assert the derivation function called is `_extract_direction`, not a `*_synthetic` factory — assert on the qualified function name recorded in provenance).
4. **Separation sanity:** Cohen's-d separation at the chosen layer (`extract.layer_diagnostics`, `extract.py:88-125`) must exceed a pre-registered floor (propose ≥ 0.8) and the layer must satisfy the existing non-degenerate/min-depth rule.
5. **Hook-bites check (E-0007 style):** capture residuals with and without the hook on 4 fixed probe strings and assert `steered − unsteered ≈ α·û` to 1e-3 (`generate.py:470-576` already supports capture with the steering hook applied). This is the assertion that would have caught W4 directly.
6. **Re-derivation determinism:** derive twice and assert cosine ≥ 0.999 (use a *tolerance*, not exact equality — D-0077 records that an exact-match σ guard blocked the ITI recheck over ~2e-4 fp noise).
7. **Negative control (cheap, strongly recommended):** run the same TEST steer cell with a **random unit direction** at the DEV-selected α, and require that it does *not* pass. A positive control without a matched random-direction negative control invites the reviewer question "would anything have passed?"

---

## 8. Success / failure interpretation matrix

| # | PC-0 (S1) | PC-1 (S2) | PC-2a steer vs baseline | PC-3 steer vs best prompt | Reading | Effect on the paper |
|---|---|---|---|---|---|---|
| A | PASS | detects | PASS | PASS | Instrument is sensitive end-to-end **and** a latent intervention can beat a bounded prompt on a non-metacognitive target | **Strongest outcome.** The C2 negative becomes "our instrument sees things, and saw nothing on the metacognitive axes." Headline unchanged, sharply strengthened. |
| B | PASS | detects | PASS | NO-PASS | Instrument sensitive; the *binding constraint* is the bounded-prompt comparator, not the assay | **Expected modal outcome and still a win.** The paper says: the pipeline detects real latent effects at δ-scale; what naive steering fails to do is beat a strong prompt. Directly answers F-2 without over-claiming. |
| C | PASS | detects | NO-PASS | NO-PASS | Endpoint+stats+steering path all live, but the chosen target's latent effect did not survive the frozen decision rule | Ambiguous for the target, informative for the instrument: report MDE for the control cell; the assay-sensitivity claim rests on PC-0/PC-1, and the target choice is disclosed as a failed bet (`failure-log.md`). |
| D | PASS | no detection | — | — | Contradicts §4.2 [FACT]; would indicate an analysis bug | Stop; audit the reanalysis path before any GPU spend. |
| E | NO-PASS | — | — | — | The frozen rule cannot return PASS even at d ≈ +0.38 with a coherent, gate-passing cell | **Would be the most consequential finding in the project**: the adjudicator is inert/over-conservative and the C2 negative must be downgraded to "uninformative under this instrument" in Abstract, Results and Conclusion. Escalate to human immediately (`AGENTS.md` §5, core-claim change). |

**Honest reading rules the design commits to in advance:**
* A PASS at d ≈ +0.38 does **not** prove power at d = +0.05. The positive control must be reported **together with the per-cell MDE** the critic asked for (`review-reassess-IUI.yaml:220-227`), and ideally with a **dilution curve** (subsample items / sweep α) locating where the same instrument flips PASS → NO-PASS. That pairing — "it detects this, and here is the smallest thing it could have detected" — is what actually closes F-2.
* PC-0's PASS is attributable to the *instruction*, not to α·û, and must always be reported with the α=0 decomposition (§4.1). Presenting +0.377 as evidence of latent controllability would be exactly the kind of selective reporting the reviews already penalised (`review-reassess-IUI.yaml:136-140`).

### 8.1 Draft paper subsection [PROPOSAL — prose, not a claim]

> **Assay sensitivity: a positive control.** A null is informative only if the instrument can return non-null, and our adjudicator returned no pass in any cell. We therefore ran the identical frozen adjudicator — same items, same generation identity (k=5, T=0.7, 64 new tokens), same DEV selection discipline, same paired item-cluster bootstrap at the Bonferroni level, same δ=0.05 and coherence gate — on a *non-metacognitive* control target on which activation steering is known to produce large behavioural change [Arditi et al. 2024; Stolfo et al. 2025]. The adjudicator returned a pass with mean paired difference *d* and interval *[lo, hi]*, while the matched random-direction control did not. We additionally decompose every control effect into an instruction component (neutral vs authored prompt) and a latent component (α vs α=0), and report the minimum detectable effect for the control cell alongside the adjudicated cells. The control establishes that the pipeline can detect a real *steer > prompt* effect of the size the pre-registered rule was designed to credit; it says nothing about whether metacognitive axes are latently controllable, and we do not read it that way.

---

## 9. Scope guard

**Exact scoping sentence to be used verbatim in the paper, the ledgers and the run manifest:**

> **This positive control tests the sensitivity of the measuring instrument on a non-metacognitive target chosen because activation steering is already known to move it; it is not evidence that deliberation, skepticism, or calibration are latently controllable, and a pass here does not weaken, qualify, or extend the scoped negative reported for naive CAA/ITI steering on the three metacognitive axes.**

Enforcement, so the guard is structural rather than rhetorical:
* The control lives in its **own** experiment id and evidence-ledger row; it is **not** added to `claim-map.yaml` C2's `supporting_evidence_ids` as support for latent control — it supports a **new** methodological claim (propose **C4: "the adjudicator is sensitive"**) and nothing else.
* The control is **not** part of the C2 Bonferroni family and does not alter any frozen verdict; `run_manifest.json` records `modifies_frozen_verdict: false`.
* The control target is a different axis id, different item pool, different contrast pairs. No metacognitive axis appears in it.
* The paper reports the control in Methods/Results as *assay sensitivity*, never in the Abstract as a capability result.

---

## 10. Cost, risks, pre-run checklist

### 10.1 Cost [FACT-anchored]
Throughput anchor: `results/E-0013-uncertainty-recheck/run_manifest.json` — **1200 generations in 166 s wall clock including model load** at the frozen identity (64 new tokens, k=5, batch 16) on the rented A800 ⇒ ≈7 gen/s.

Planned generation count per axis (`plan_generation_counts`, `adjudicate_c2b.py:255-276`), N=60 ⇒ n_dev=20, n_test=40:
* DEV = 5 × 20 × (16 prompts + 1 baseline + 7 α) = **2400**
* TEST = 5 × 40 × 5 cells = **1000**
* **Total ≈ 3400 generations ≈ 8 min** of generation for PC-3; PC-2a adds only its own DEV prompt cell (5 × 20 = 100) plus a shared TEST prompt cell (200) ⇒ ≈ **4 min**.
* C1 direction derivation (40 contrast pairs, cached layer scan): ≈ 5–15 min.
* Random-direction negative control: 5 × 40 = 200 generations ≈ 30 s.

| Version | GPU-hours | Cells |
|---|---|---|
| PC-0 + PC-1 | **0** | reanalysis of committed transcripts |
| PC-2 MINIMAL (Qwen, T1, PC-2a + PC-3 + random-direction control) | **0.5 (budget 1.5)** | 1 model × 1 target × 1 axis |
| PC-2 FULL (§11) | 3–5 | + 2nd model, + 2nd target, + α dilution curve |

No paid API, no gated model (Qwen2.5-7B-Instruct is cached and ungated), no human subjects, no new data licences (TriviaQA Apache-2.0, already recorded). **Under `AGENTS.md` §5 this does not require human approval on cost/ethics grounds; the Manager can authorise it.** What *does* require the owner is any decision to let a NO-PASS outcome change the paper's core claim (matrix row E).

### 10.2 Top risks

| # | Risk | Likelihood | Mitigation |
|---|---|---|---|
| R1 | **The bounded prompt matches steering** on T1 (a literal "refuse everything" instruction saturates) ⇒ PC-3 NO-PASS, ambiguous | High (≈40–60%) | Ladder design: PC-0/PC-1/PC-2a still close S1/S2. Report per-cell MDE. Pre-declare that row B is an acceptable, publishable outcome. |
| R2 | **Degenerate steering wins**: refusal templates are short and repetitive | Medium | The coherence gate already exists and is the correct guard; report degeneracy for every cell; inspect ≥20 sampled generations before writing anything. |
| R3 | **Coherence gate blocks all α** (as it can — `adjudicate_c2b.py:797-822` returns an honest non-pass with an empty steer cell) | Low–Medium | Inspect the DEV α grid before adjudicating; if every α fails the gate, report it as a *finding about the gate*, not as a failed control. |
| R4 | **Instruction/latent confound** repeats (PC-0 lesson) | Certain if unguarded | The three-way decomposition is mandatory in every control report, not optional. |
| R5 | **Post-hoc target selection** objection ("you picked what you knew works") | Certain to be raised | Correct answer: that is the *definition* of a positive control. Disclose the motivation (including that PC-0's endpoint was suggested by E-0013), pre-register the endpoint and the substring list before the run, and pair it with the random-direction negative control. |
| R6 | **TEST touched twice** (PC-0 reuses frozen TEST under a new endpoint) | Certain | Disclose; separate experiment id; excluded from the C2 multiplicity family; PC-2 uses a **fresh, id-disjoint** item pool. |
| R7 | **Refusal scorer brittleness** (substring rules miss soft refusals) | Medium | Frozen substring list committed pre-run; report the false-negative rate on a hand-labelled sample of 50 generations; note the scorer is deliberately the literature-standard one. |
| R8 | Placeholder direction / fixture data recurrence | Low with §7, historically 4/4 | The §7 guard block, failing closed on the real backend. |

### 10.3 Pre-run checklist (all items must be green before any GPU time)

1. Pre-registration written and committed (`docs/ledgers/prereg-positive-control.md`): target, endpoint + frozen substring list, item pool + disjointness rule, the 16 prompt candidates **including the literal maximal-strength ones**, α grid, δ, k, generation identity, CI level (0.98333, with the rationale), coherence gate, decision rule, and the interpretation matrix of §8 — all **before** any generation.
2. `git status` clean; code commit recorded; experiment id allocated in `docs/ledgers/experiment-registry.yaml`.
3. Offline tests green for the new scorers and the new axis wiring (`python -m pytest -q`), including a leakage test that the new strong prompts do not overlap the new contrast pairs.
4. Synthetic-backend smoke of the whole path (fixture items, `--backend synthetic`) producing a report with the frozen parameters echoed.
5. §7 guard block implemented and demonstrated to **hard-fail** on (a) a random direction, (b) `np.ones(8)`, (c) `use_fixture=True` on the hf backend.
6. Hook-bites assertion (`steered − unsteered ≈ α·û`) passes on the real model.
7. Item-pool disjointness assertion vs the frozen 80 TriviaQA ids passes and is logged.
8. Disk/RAM guards and the inactivity watchdog configured as in the frozen runner (`run_c2b_adjudication.py:589-642`, `:1036-1037` (disk guards)).
9. `--save-transcripts` **on** (the frozen arm saved them and that is exactly why PC-0/PC-1 are free — do not lose that property).
10. Manager has written the go decision into `docs/ledgers/decision-log.md` (next id after D-0079) with the scope-guard sentence quoted.

---

## 11. MINIMAL vs FULL

**MINIMAL (recommended, sufficient to answer the sensitivity question):**
* PC-0 + PC-1 (zero GPU) — S1 and S2, from committed artifacts, today.
* PC-2 on Qwen2.5-7B-Instruct only, target T1, one axis, N=60, PC-2a + PC-3 + random-direction negative control, ≈0.5 GPU-h.
* Reported with the three-way decomposition, per-cell MDE, and the §9 scoping sentence.
* Closes F-2 to the level of "our instrument sees things, and saw nothing there", which is precisely what the AC asked for (`C-areachair-opus5.md:51`) and what the IUI critic priced as the difference between an uninformative and an informative negative.

**FULL (adds robustness, not necessity):**
* Second model (Llama-3-8B via the NousResearch identical-weights mirror already used for the frozen runs) ⇒ the control is not a Qwen quirk.
* Second target (T2, Stolfo-style verifiable constraints) ⇒ the control is not a refusal quirk.
* **α-dilution / power curve:** re-adjudicate the control at each α and at subsampled item counts to locate the empirical PASS→NO-PASS boundary; this converts "the instrument detected +0.38" into "the instrument detects down to +X at n=40", which is the strongest possible answer to F-2/B-2 and directly addresses the skepticism-axis MDE problem.
* ITI as well as CAA ⇒ the control covers both direction families, addressing M-2 in the reassessment review.
* A matched **negative** control on a target where steering is *not* expected to work, giving a two-sided specificity claim.

---

## 12. Recommendation (go/no-go input for the Manager)

1. **GO immediately, zero cost:** PC-0 + PC-1 as a reanalysis of committed `results/arm_full` transcripts. They are free, they close S1 and S2, and PC-0's decomposition also surfaces the `main.tex:230` attribution problem that a hostile reviewer would otherwise find.
2. **GO, Manager-authorisable:** PC-2 MINIMAL — **target: refusal induction on harmless questions (Arditi et al. 2024), Qwen2.5-7B-Instruct, real CAA direction, frozen adjudicator, N=60, PC-2a + PC-3 + random-direction control, ≈0.5 GPU-h (budget 1.5).**
3. **Expected outcome:** matrix row **B** (PC-0 PASS, PC-1 detects, PC-2a PASS, PC-3 uncertain ≈40–60%). Row B is publishable and materially improves the paper; row A is better; row E would force an escalation and a downgrade of the headline, which is exactly the risk a positive control is supposed to expose.
4. **Do not** run the sycophancy or refusal-ablation variants: the first breaks the scope guard, the second is dual-use and needs the human ethics gate.
5. **Non-negotiable reporting conditions:** three-way decomposition on every control cell; per-cell MDE next to every PASS; the §9 scoping sentence in the paper, the ledger row and the run manifest; the random-direction negative control alongside the positive one.

**Judgment calls made in this document (stated per instructions):** (i) treating "assay sensitivity" as three claims rather than one, because a single steer>prompt bet is uninformative when lost; (ii) keeping the Bonferroni 0.98333 level for a single-axis control, trading formal exactness for comparability with the C2 negative; (iii) ranking refusal induction above the Stolfo constraint target despite the latter's tighter fit to "prompting plateaus", on grounds of literature strength, code/data reuse, and scorer simplicity; (iv) excluding sycophancy — the strongest CAA-literature target — purely on the scope guard; (v) recommending a fresh, disjoint item pool for PC-2 rather than reusing the frozen TEST set, to avoid a second look at TEST.

---

### Sources

* Arditi, Obeso, Syed, Paleka, Panickssery, Gurnee, Nanda. *Refusal in Language Models Is Mediated by a Single Direction.* arXiv:2406.11717 (NeurIPS 2024). — refusal direction; **adding** it induces refusal on harmless prompts; directional intervention is more reliable than prompt-based approaches. *Not yet in `docs/paper/references.bib`; would need adding.*
* Stolfo, Balachandran, Yousefi, Horvitz, Nushi. *Improving Instruction-Following in Language Models through Activation Steering.* ICLR 2025 (arXiv:2410.12877). — instruction-difference vectors improve format/length/word-inclusion compliance, including with the instruction removed from the prompt; compositional. Already cited as `stolfo2025instr` (`docs/paper/references.bib:104`).
* Rimsky (Panickssery), Gabrieli, Schulz, Tong, Hubinger, Turner. *Steering Llama 2 via Contrastive Activation Addition.* ACL 2024. Already cited (`references.bib:36`).
* Turner et al. *Steering Language Models With Activation Engineering* (ActAdd). Already cited (`references.bib:53`).
* Zou et al. *Representation Engineering.* Already cited (`references.bib:85`). Li et al. *Inference-Time Intervention.* Already cited (`references.bib:70`).
* In-repo evidence: `results/arm_full/cell_{caa,iti}__{qwen2.5-7b,llama3-8b}/transcripts/*`, `results/arm_full/cell_caa__qwen2.5-7b/c2b_adjudication_results.json`, `results/E-0013-uncertainty-recheck/run_manifest.json`, `docs/ledgers/failure-log.md:8-19`, `docs/ledgers/prereg-c2b-adjudication.md` §4/§5, `reviews/2026-08-03-reassessment-critic/review-reassess-IUI.yaml` (B-2, F2), `reviews/2026-08-03-chained-review/C-areachair-opus5.md` (F-2, §2).
