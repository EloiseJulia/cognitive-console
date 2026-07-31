# E-0012 v3 Independent Hostile Audit

Auditor: independent hostile auditor (did not write the run code).  
Branch/HEAD: `run/e0012-modelgen-v3-20260731` / `ed78394793f3e051cefde035d17aa66dec9462bb`.  
Scope: E-0012 third run artifacts under `results/E-0012/` plus source/protocol/history needed to adjudicate comparator fairness.

## Commands and files actually checked

- Read `AGENTS.md`; `AI-Instruction.md` Part I §9; prereg §5-B, §8, §9.3, §9.4; available prior audit `reviews/2026-07-31-e0012-apefix-code-audit/audit-report.md`.
- Requested prior audit path `reviews/2026-07-31-e0012-modelgen-audit/audit-report.md` is absent in this checkout. I therefore read the historical first-run audit via git: `git show 4a80a26:reviews/2026-07-30-e0012-results-audit/review.yaml`.
- `git status --short --branch`; `git rev-parse HEAD`; `git log --oneline --decorate --all --max-count=20`.
- `git show 61567b1:results/E-0012/e0012_results.json`; `git show 61567b1:results/E-0012/run_e0012.log`; `git show 61567b1:scripts/run_e0012_verified_control.py`.
- Parsed `results/E-0012/e0012_results.json`, `e0012_ape_candidates.json`, `e0012_stage0_candidates.json`, `brier_raw_pairs.jsonl`, `run_e0012_v3.log` with Python.
- Recomputed split integrity and Stage 1 paired clustered bootstrap CIs from `brier_raw_pairs.jsonl`.
- Ran `python -m pytest -q tests/test_e0012.py` → PASS (all dots, exit 0).

## Comparator fairness & the 0.827 question — definitive ruling

**Ruling: the 0.827 first-run number is real-model-scored and apples-to-apples as a score on the same DEV split, but it is NOT a §5-B APE score.** It is a best-of-50 human-authored synthetic-bank prompt scored by the real HF sampler on the same 27-item DEV pool. It is therefore comparable as evidence that a human prompt can beat the button, but not compliant with the frozen model-generated APE comparator.

Evidence:

- First-run artifacts at commit `61567b1` say `backend="hf"`, `n_dev=27`, `n_test=53`, `ape_winner_dev_k3=0.8197530864`, `ape_winner_dev_k5=0.8269814815`, `kill_rule="TRANSFER"`, and `n_stage1_candidates=0` (`git show 61567b1:results/E-0012/e0012_results.json`: lines 1-27 in command output). The first-run log also says `backend='hf'`, `device='cuda'`, `Split: 27 DEV / 53 TEST`, and `APE winner DEV score (k=5): 0.8270` (`git show 61567b1:results/E-0012/run_e0012.log`: lines 2-26 in command output).
- First-run runner code used real HF for sampling/scoring, but **did not generate APE candidates with the model**: in the historical file, the HF branch also did `candidates = generate_candidates_synthetic(APE_N_CAND, APE_SEED)  # fallback`, with the real `generate_candidates_real` call commented (`scripts/run_e0012_verified_control.py@61567b1:185-188`). The same first-run runner created `SteeredHFTextCapableSampler` for the HF path (`scripts/run_e0012_verified_control.py@61567b1`, lines shown by command around `SteeredHFTextCapableSampler`).
- The first hostile audit independently recorded the same facts: `ape_winner_dev_k5: 0.8270`, all raw pairs `synthetic_proxy=false`, and the finding that the HF path used a pre-authored bank instead of model-generated candidates (`reviews/2026-07-30-e0012-results-audit/review.yaml@4a80a26:24,58-71`). It also records that the exact winning prompt identity was not persisted and is unverifiable from saved artifacts (`review.yaml@4a80a26:134-139`).
- Current source confirms `generate_candidates_synthetic()` is a shuffled pre-authored bank, not a mock outcome sampler (`src/cognitive_console/experiments/e0012_ape.py:82-153`). The real/synthetic distinction is about candidate generation, while outcome scoring comes from the sampler passed into `run_ape()` (`src/cognitive_console/experiments/e0012_ape.py:395-445`).

**Identity of the 0.827 prompt:** UNVERIFIED from artifacts. The winning prompt text/candidate id were not persisted in the first run; prior audit explicitly flagged that gap (`review.yaml@4a80a26:134-139`). I will not fabricate an identity by re-scoring or guessing from the bank.

**Implication:** A human-authored prompt bank has already produced a real-model DEV score of ~0.827, exceeding the current button DEV k5 of 0.6967. Therefore the current v3 `LOCAL` result is sound only against the frozen §5-B comparator actually run in v3 (model-generated prompts + `calibration_prompts.yaml` fallback). It is an **over-claim** to call the v3 comparator "the hardest prompt comparator" in an unrestricted human-prompt sense. The honest wording is: the button beats the frozen model-generated APE procedure plus the owner-confirmed authored fallback bank, but does **not** beat every known human-authored prompt bank tried in this project.

## Current v3 artifact reconstruction

- Current v3 result: `VERDICT=LOCAL`, `backend="hf"`, `n_dev=27`, `n_test=53`, `ape_winner_candidate_id=44`, APE winner k3=0.513062963 and k5=0.534305926, `button_best_dev_k5=0.6967`, kill rule PASS, 13/105 Stage0 candidates pass, 3 Stage1 candidates all PASS (`results/E-0012/e0012_results.json:1-132`).
- Current v3 APE provenance: 50 candidates, 36 model parseable and 14 authored fallback. Recomputed from `e0012_ape_candidates.json`: all 36 model-generated candidates score DEV k3 ≤ 0.213703704 (not merely <0.284); the top eight candidates are all authored fallback, led by candidate 44/CAL-09 at k3=0.513062963 and k5=0.534305926 (`results/E-0012/e0012_ape_candidates.json:1-180` and Python parse).
- The v3 HF runner now calls `generate_candidates_real(...)` with authored prompts only as padding (`scripts/run_e0012_verified_control.py:206-213`). `generate_candidates_real` uses the frozen stochastic generation params `do_sample=True`, `temperature=0.9`, `top_p=0.9`, `seed=42` (`src/cognitive_console/experiments/e0012_ape.py:156-181`).

## Mandatory checks

### 1. Split integrity / no leakage

PASS. Source freezes pool `N=80`, `pool_seed=12`, `offset=500`, `split_seed=42` (`src/cognitive_console/eval/e0012_triviaqa.py:27-30,96-110`). Runner loads the E-0012 pool and calls `split_e0012_pool(..., split_seed=E0012_SPLIT_SEED)` (`scripts/run_e0012_verified_control.py:146-149`); split implementation delegates to frozen `adj.split_dev_test` (`src/cognitive_console/experiments/e0012_harness.py:1000-1009`).

Recomputed: pool=80, DEV=27, TEST=53, DEV∩TEST=0. Stage1 raw-pair item ids are a subset of TEST and have 0 DEV overlap; DEV channels (`prompt_dev`, `steer_dev`) have 0 non-DEV ids. No Stage1 TEST leakage into DEV/APE was found.

### 2. Real pairs / N-01 guard

PASS. `SteeredHFTextCapableSampler` is used in the HF path (`scripts/run_e0012_verified_control.py:163-176`) and records real text-derived confidence/correctness pairs with `synthetic_proxy=False` (`src/cognitive_console/experiments/e0012_harness.py:257-270`; `src/cognitive_console/experiments/e0012_steer_hf.py:26-33,96-97`). N-01 hard-fails if a real GPU `TextCapableSampler` lacks real pairs (`src/cognitive_console/experiments/e0012_harness.py:697-727`).

Recomputed from `brier_raw_pairs.jsonl`: 22,311 records, `synthetic_proxy=false` for all 22,311, `true=0`. Channel counts: `prompt_dev=2916`, `steer_dev=17010`, and for each of 3 Stage1 candidates: `s1_steer=265`, `s1_prompt=265`, `s1_baseline=265` (53 TEST items × k=5).

### 3. Kill rule symmetry / verdict mapping

PASS. The kill rule compares APE winner DEV k5 to the best advancing button DEV k5 (`src/cognitive_console/experiments/e0012_ape.py:342-362`; `src/cognitive_console/experiments/e0012_harness.py:392-420`). In v3, 0.534305926 < 0.6967, so kill rule PASS is correctly persisted (`results/E-0012/e0012_results.json:20-24,32`). Because Stage1 passes and Stage2 is not run, `LOCAL` is the correct §8 mapping (`docs/research/2026-07-29-e0012-verified-control-button/prereg-e0012-verified-control-button-DRAFT.md:283-293`; `src/cognitive_console/experiments/e0012_harness.py:780-805`).

### 4. Stage1 TEST recomputation + Bonferroni

PASS. The harness dynamically applies Bonferroni over the M=3 advancing candidates: `ci_level = 1.0 - 0.05 / m` (`src/cognitive_console/experiments/e0012_harness.py:966-986`), matching prereg Stage1 multiplicity language (`prereg...DRAFT.md:314-324`). Recomputed from raw TEST pairs using paired item-level differences and clustered bootstrap (`b=10000`, `seed=0`, `ci_level=0.9833333333`):

| Candidate | n TEST | mean delta | 98.333% CI | PASS? |
|---|---:|---:|---:|---|
| BTN-CAL-PROBE@L19 α24 | 53 | 0.143789 | [0.086352, 0.198117] | yes |
| BTN-CAL-CONTRA-REEXTRACT@L18 α16 | 53 | 0.107734 | [0.048742, 0.168192] | yes |
| BTN-CAL-LOGIT-MARGIN@L22 α24 | 53 | 0.067329 | [0.030584, 0.105300] | yes |

The third candidate's CI lower bound is above zero but its margin is narrow; this is still a prereg PASS because mean ≥ δ=0.05 and CI excludes zero (`src/cognitive_console/experiments/adjudicate_c2b.py:338-385,395-399`).

### 5. §9.4 cross-axis SKIPPED

PASS for LOCAL only. Prereg permits marking cross-axis as SKIPPED when only calibration is evaluated and requires Stage2 cross-axis before GENERAL_CONTROL (`prereg...DRAFT.md:352-379`). Current harness passes `cross_axis_dev_items=None` into every Stage1 candidate (`src/cognitive_console/experiments/e0012_harness.py:986`); `_compute_cross_axis_deltas` returns `{}`, `"SKIPPED"` when no cross-axis items are supplied (`src/cognitive_console/experiments/e0012_harness.py:561-588`). Current artifacts persist `cross_axis_check="SKIPPED"` and empty deltas for all candidates (`results/E-0012/e0012_results.json:35-132`). Raw channels contain no `cross_` records. This does not flip LOCAL, but it would block any honest GENERAL_CONTROL claim.

### 6. Coherence `Infinity`

MINOR / cosmetic persistence artifact, not a gate failure. Stage1 coherence is computed from raw degeneracy values, not from the persisted ratio: `coherence_ok = mean_degen_steer <= 1.5*baseline + eps_floor`; only then is `coherence_ratio` set to `inf` when baseline degeneracy is zero (`src/cognitive_console/experiments/e0012_harness.py:668-674`). The pass rule consumes `coherence_ok`, not the ratio (`src/cognitive_console/experiments/e0012_harness.py:674`; `src/cognitive_console/experiments/adjudicate_c2b.py:395-399`). Current artifacts show `coherence_ok=true` despite ratio `Infinity` because absolute steer degeneracy is within the epsilon-floored ceiling (`results/E-0012/e0012_results.json:43-125`).

### 7. Forking paths / search multiplicity

PASS with caveat. Stage0 evaluated and reported the full 105-cell grid, with 13 cutoff passes; recomputed top pass list matches persisted totals. Prereg acknowledges Stage0 is exploratory and uncorrected, while Stage1 controls the ≤3 precommitted hypotheses (`prereg...DRAFT.md:300-324`). The harness selects ≤3 with family diversity before TEST (`src/cognitive_console/experiments/e0012_harness.py:132-153,966-986`). This is acceptable under the prereg; it should remain described as screened-then-confirmed, not as 105 independent confirmatory tests.

## Ranked findings

### MAJOR-1 — Comparator fairness overclaim: known real-model human prompt bank beats the button

**Evidence:** first-run 0.827 was real HF scoring on the same DEV split but candidates came from `generate_candidates_synthetic`, a pre-authored bank (`scripts/run_e0012_verified_control.py@61567b1:185-188`; `reviews/2026-07-30-e0012-results-audit/review.yaml@4a80a26:24,58-71`). Current v3 button best DEV k5 is 0.6967 while current frozen §5-B comparator is 0.5343 (`results/E-0012/e0012_results.json:20-24`).

**Impact:** If the paper says the button beats "the hardest prompt comparator" without qualification, that is false. A human-authored prompt bank already beat it. The valid claim is narrower: the button beats the frozen model-generated APE procedure plus the `calibration_prompts.yaml` fallback in this v3 run.

**Minimum fix:** Reconcile wording/ledgers: explicitly separate (a) protocol-faithful model-gen APE result = LOCAL, from (b) prior human-bank robustness/comparator result = prompt can beat button. Do not call v3 VERIFIED-CONTROL or prompt-unreachable in an unrestricted sense.

### MINOR-1 — 0.827 winning prompt identity is unrecoverable from first-run artifacts

**Evidence:** first-run results persisted scores but not `ape_winner_prompt_text`/candidate id (`git show 61567b1:results/E-0012/e0012_results.json`); prior audit flagged this exact issue (`review.yaml@4a80a26:134-139`).

**Impact:** Does not change the 0.827 comparability ruling, but prevents identifying which synthetic-bank prompt won. This weakens forensic reproducibility of the prior human-bank comparator.

**Minimum fix:** Treat the identity as unknown unless the run is reproduced or hidden logs are found; do not cite a specific winning text.

### MINOR-2 — `coherence_ratio=Infinity` should be explained in reports

**Evidence:** persisted Stage1 ratios are `Infinity` where baseline degeneracy is 0.0 (`results/E-0012/e0012_results.json:43-125`); source gates on raw degeneracy/epsilon floor, not the ratio (`src/cognitive_console/experiments/e0012_harness.py:668-674`).

**Impact:** Cosmetic, but readers may misread Infinity as coherence failure.

**Minimum fix:** In paper/ledger, report raw degeneracies and clarify that coherence_ok is the adjudicated field.

## Reconciliation

The apparent contradiction is resolved as follows:

1. **First run (TRANSFER, 0.827):** real model, same DEV split, real (confidence, correctness) pairs, but the comparator candidates were a stronger/different human-authored synthetic bank. It proves at least one human-authored prompt procedure can beat the button on DEV, but it violated frozen §5-B model-generation.
2. **Second model-gen run:** prior history/audits show it was not sound because generation was greedy/fallback-biased and provenance/cross-axis persistence were broken.
3. **Current v3 run (LOCAL):** §5-B-conformant stochastic model generation with candidate provenance. The generated prompts are weak on this model/run; fallback CAL-09 wins at 0.534, and the button passes kill rule plus Stage1 TEST. This is sound as a local, protocol-faithful result, but not evidence that no strong human prompt can match/beat the button.

## Final verdict

**SOUND-BUT-OVERCLAIMS-IF-CALLED-VERIFIED-CONTROL.**

The v3 artifacts support `LOCAL` under the frozen §5-B model-generated APE comparator, with clean split integrity, real-pair guards, symmetric kill rule, Bonferroni Stage1 PASS, and correctly skipped §9.4 for LOCAL. They do **not** support an unrestricted "hardest prompt" or prompt-unreachable/VERIFIED-CONTROL claim because the prior 0.827 human-bank prompt score is real-model-comparable and exceeds the button.
