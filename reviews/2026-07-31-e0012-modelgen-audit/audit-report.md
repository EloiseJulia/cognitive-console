# E-0012 model-generated APE re-run hostile audit

**Audit date:** 2026-07-31  
**Audited checkout:** `run/e0012-modelgen-20260731`, observed HEAD `550a0b9` (parent prompt said `84afade`; current checkout already includes ledger commit `550a0b9`).  
**Scope:** source + persisted artifacts under `results/E-0012/`; no fixes made.

## Executive verdict

**VERDICT: NOT-SOUND** as a VERIFIED-CONTROL / LOCAL positive.

The Stage 1 held-out-test arithmetic is internally reproducible from `brier_raw_pairs.jsonl`: all three advanced buttons beat the stored prompt comparator on TEST. However, the positive flip depends on the APE comparator, and the re-run does **not** implement the frozen §5-B generation protocol fairly/reproducibly. The APE generator ignores frozen sampling parameters (`temperature=0.9`, `top_p=0.9`, seed=42), does not persist the 50 generated candidates or padding count, and the recorded winner is exactly one of the human-authored prompts (`CAL-09`) at candidate id 45, strongly consistent with fallback padding rather than a genuine model-generated winner. Therefore the comparator is unauditable and likely not the frozen strongest-prompt comparator.

## Ranked findings

### BLOCKER-1 — APE candidate generation violates frozen §5-B sampling protocol and is not reproducible

**Evidence:**
- Frozen prereg requires same target model, `temperature=0.9`, `top_p=0.9`, seed=42, one meta-prompt call, N=50 (`docs/research/2026-07-29-e0012-verified-control-button/prereg-e0012-verified-control-button-DRAFT.md:198-208`) and forbids changing any invariant (`:234-238`).
- Code defines `APE_TEMPERATURE=0.9` and `APE_TOP_P=0.9` but `generate_candidates_real` only calls `backend.generate(meta_prompt, steer, max_new_tokens=4096)` or `backend.generate(meta_prompt, None, max_new_tokens=4096)` (`src/cognitive_console/experiments/e0012_ape.py:134-156`). The `seed` argument is accepted but unused.
- `SteeredHFBackend.generate` defaults to `do_sample=False`, `temperature=1.0`, `seed=None`, and has no `top_p` argument (`src/cognitive_console/steering/generate.py:528-632`). Therefore the APE generation was greedy/default, not the frozen stochastic APE procedure.

**Impact:** The comparator that controls the kill rule is not the pre-registered comparator. This can directly explain the 0.827 -> 0.534 weakening and the TRANSFER -> LOCAL flip.

**Minimal fix:** Implement a byte-frozen APE generation wrapper that passes `do_sample=True`, `temperature=0.9`, `top_p=0.9`, `seed=42` (add backend support for top_p), and persist raw model output + parsed candidate list + generation config hash before any scoring. Re-run from a new prereg/decision record.

### BLOCKER-2 — The full APE candidate set and padding count are not persisted; winner appears to be fallback authored prompt

**Evidence:**
- `generate_candidates_real` pads parsed model candidates with authored prompts when fewer than N are parseable (`src/cognitive_console/experiments/e0012_ape.py:157-164`).
- The runner passes authored prompts as fallback (`scripts/run_e0012_verified_control.py:187-192`) but calls `run_ape` without a real `authored_count`; `run_ape` defaults `authored_count=0` and only keeps it in memory (`src/cognitive_console/experiments/e0012_ape.py:338-371`). The JSON output omits `n_cand_generated`, `n_cand_padded`, raw output, and all candidate texts (`scripts/run_e0012_verified_control.py:270-306`).
- Persisted winner: candidate_id `45`, text `Express appropriate uncertainty...` (`results/E-0012/e0012_results.json`). That text is byte-identical to authored `CAL-09` (`data/e0012_prompts/calibration_prompts.yaml:91-97`). Candidate id 45 is late in the 50-list and is consistent with model parse count <50 followed by authored fallback padding.

**Impact:** I cannot verify that N=50 genuine model-generated candidates were produced, that near-duplicates/empties were absent, or that the selected winner was model-generated. The strongest available evidence suggests the APE winner may be a fallback human-authored prompt, not a model-generated APE candidate.

**Minimal fix:** Persist `ape_raw_output.txt`, `ape_candidates.json` with `{candidate_id,text,source=model|authored_fallback,normalized_hash}`, duplicate/empty stats, `n_model_parseable`, `n_padded`, and all DEV k=3/k=5 scores. Treat any run without this as unauditable.

### MAJOR-1 — Honest scientific reading is prompt-sensitive: a competent authored prompt matched/beat the button in the first run

**Evidence:**
- Prior run log records APE/synthetic authored comparator winner k=5 = `0.8270`, kill rule TRANSFER (`results/E-0012/run_e0012_modelgen.log:26-33`).
- Current result records APE winner k=5 = `0.5343059259`, button best DEV k5 = `0.6967`, kill rule PASS (`results/E-0012/e0012_results.json`).
- The same 105 Stage0 button cells still produced 13 pass-cutoff candidates in both logs, so the verdict flip is entirely comparator-side.

**Impact:** Calling the result “LOCAL VERIFIED-CONTROL” without the caveat “only against this weak/unaudited APE comparator; not superior to the earlier competent prompt comparator” would over-claim. The scientifically safe statement is: the button beats the stored prompt in this re-run, but it has not been shown superior to good prompting.

**Minimal fix:** Downgrade any claim to exploratory/diagnostic until the frozen APE comparator is rerun and candidate artifacts are auditable. Explicitly report the 0.827 negative comparator result as contradicting evidence.

### MAJOR-2 — Stage 1 safety side-effect check is incomplete (cross-axis guard skipped)

**Evidence:**
- Prereg §9.4 makes cross-axis non-degradation a pass/fail safety guard where any tested non-calibration axis with delta < -0.10 triggers BUTTON_FOUND_BUT_UNSAFE (`prereg...md:358-378`).
- `run_stage1_candidate` sets `cross_deltas: Dict[str, float] = {}` and never evaluates deliberation/skepticism side effects (`src/cognitive_console/experiments/e0012_harness.py:697-705`).
- Current result prints `safety_unsafe=False` for all three Stage1 candidates, but that only covers accuracy and Brier decomposition, not cross-axis harm.

**Impact:** This does not invalidate the calibration TEST delta, but it makes the safety statement incomplete. It is acceptable only for a narrowly scoped LOCAL/exploratory result with an explicit “cross-axis skipped” limitation.

**Minimal fix:** Persist an explicit `cross_axis_check: SKIPPED` field and do not summarize as simply `safety_unsafe=False`; run the §9.4 DEV side-effect check before any stronger control/safety claim.

### UNVERIFIED-1 — Coherence ratios are applied in code but not persisted for independent recomputation

**Evidence:**
- Stage0/Stage1 code computes coherence gates from degeneracy scores (`src/cognitive_console/experiments/e0012_harness.py:345-405`, `:629-637`).
- Persisted `e0012_stage0_candidates.json` only stores `coherence_ok`, not `coherence_ratio` or raw degeneracy; `brier_raw_pairs.jsonl` stores confidence/correctness but not raw text/degeneracy.

**Impact:** I can verify pass flags from code and artifacts only indirectly; I cannot independently recompute coherence ratios from persisted artifacts.

**Minimal fix:** Persist per-item/per-sample degeneracy or at least per-candidate mean steer/baseline degeneracy and ratio for Stage0 and Stage1.

## Comparator fairness analysis

- **Genuine model generation?** Not established. The runner calls `generate_candidates_real` for HF (`scripts/run_e0012_verified_control.py:187-192`), so it no longer calls `generate_candidates_synthetic` on the HF path. But the actual generation call ignores frozen stochastic parameters and seed, and candidate texts are absent. The winner exactly matches human-authored `CAL-09` at candidate id 45, consistent with fallback padding.
- **N_cand=50 generated/scored?** The log says `Running APE (N_cand=50, seed=42)` and `run_ape` screens all candidates at k=3 with no early stopping (`e0012_ape.py:338-371`). But because the candidate list is not persisted, I cannot verify 50 model-generated candidates versus a shorter parseable list padded by authored prompts.
- **Apples-to-apples DEV scoring?** Conditional on the candidate list, scoring uses the same `OutcomeSampler`, same `mean_outcome` metric, DEV items, and k=3 screen / k=5 winner re-eval (`e0012_ape.py:222-290`). The kill rule compares APE k=5 to button k=5 via `apply_kill_rule` (`e0012_ape.py:293-317`) and `run_stage0` re-evaluates the best advancing button at k=5 (`e0012_harness.py:417-437`). That arithmetic is symmetric.
- **Can I regenerate without GPU?** No. `generate_candidates_real` requires a loaded HF backend/model generation call. The current environment cannot reproduce the APE list without the model/GPU, and in any case the run did not persist enough config (`do_sample/top_p/raw output`) to replay exactly.

## Kill rule / verdict derivation

The kill rule implementation itself is correct: `auto_prompt_dev >= button_dev` returns TRANSFER; otherwise PASS (`e0012_ape.py:293-317`). Current artifacts have `ape_winner_dev_k5=0.5343059259`, `button_best_dev_k5=0.6967`, so PASS is derived correctly. `determine_verdict` maps Stage1 PASS with Stage2 not run to LOCAL (`e0012_harness.py:728-839`), matching prereg §8 LOCAL definition (`prereg...md:321-333`). No off-by-one in Stage0 selection found: 105 total, 13 pass cutoff, selected top per family: PROBE 19/24 (0.1909 DEV improvement), CONTRA 18/16 (0.1045), LOGIT 22/24 (0.0928).

## Frozen TEST integrity / leakage

I verified the split and raw artifact membership:

- Pool constants are frozen at seed=12, offset=500, split_seed=42 (`src/cognitive_console/eval/e0012_triviaqa.py:28-31`); split uses deterministic disjoint `adj.split_dev_test` (`e0012_harness.py:929-939`; `adjudicate_c2b.py:298-315`).
- Independent check: 80 pool items -> 27 DEV / 53 TEST, DEV/TEST overlap 0. Raw `prompt_dev`/`steer_dev` IDs match exactly the 27 DEV IDs; raw `s1_*` IDs match exactly the 53 TEST IDs; raw DEV/TEST overlap 0.
- All `brier_raw_pairs.jsonl` records have `synthetic_proxy=false`: 22,311 / 22,311 non-proxy records. Stage1 has 3 candidates x 3 channels x 53 items x 5 samples = 2,385 records, as expected.

Independent Stage1 recomputation from raw pairs (paired item-cluster bootstrap B=10000, CI level 98.333%, seed=0):

| Candidate | TEST mean steer | TEST mean prompt | mean delta | CI | PASS if coherence OK |
|---|---:|---:|---:|---:|---|
| BTN-CAL-PROBE layer 19 alpha 24 | 0.680364 | 0.536575 | 0.143789 | [0.086352, 0.198117] | yes |
| BTN-CAL-CONTRA-REEXTRACT layer 18 alpha 16 | 0.644309 | 0.536575 | 0.107734 | [0.048742, 0.168192] | yes |
| BTN-CAL-LOGIT-MARGIN layer 22 alpha 24 | 0.603904 | 0.536575 | 0.067329 | [0.030584, 0.105300] | yes |

Note the CONTRA lower CI is slightly below 0.05, but the prereg requires CI exclude 0 and point estimate >= 0.05; it passes under the coded criterion.

## Synthetic-proxy / N-01 guard

The HF runner wraps `SteeredHFBackend` with `SteeredHFTextCapableSampler` (`scripts/run_e0012_verified_control.py:160-181`), and `run_stage1_candidate` raises if a `TextCapableSampler` lacks real pairs (`e0012_harness.py:664-684`). Artifact check found `synthetic_proxy=false` for all 22,311 raw-pair rows. N-01 appears active for Stage1 safety decomposition.

## Safety / side effects

Accuracy guard and Brier reliability/gaming guard are numerically OK on calibration TEST:

| Candidate | item accuracy steer | item accuracy baseline | reliability delta vs baseline | gaming |
|---|---:|---:|---:|---|
| PROBE 19/24 | 0.905660 | 0.056604 | -0.5411 | OK |
| CONTRA 18/16 | 0.811321 | 0.056604 | -0.4873 | OK |
| LOGIT 22/24 | 0.773585 | 0.056604 | -0.4616 | OK |

However, the adequacy is limited: `parse_confidence` only recognizes explicit confidence patterns and otherwise the harness records 0.5 (`scorers.py:83-99`; `e0012_harness.py:245-249`), and `item_is_correct` uses substring/alias matching (`scorers.py:208-230`). This is reasonable for a scripted artifact check but not a full semantic safety evaluator. Cross-axis side effects are skipped as above.

## Forking paths / multiplicity

Stage0 scope and selection are pre-registered: 3 families x 5 layers x 7 alphas = 105, cutoff improvement >= 0.05 plus coherence, advance <=3 with family diversity (`prereg...md:247-284`). The artifact reports all 105 candidates and 13 pass cutoff. Prereg explicitly acknowledges Stage0 multiplicity is exploratory and only Stage1 Bonferroni controls M<=3 confirmatory hypotheses (`prereg...md:286-299`). Stage1 dynamic Bonferroni uses `ci_level = 1 - 0.05 / M` (`e0012_harness.py:899-913`), so multiplicity across the 3 advanced candidates is handled in the TEST adjudication.

## Reconciling the two runs

The honest scientific reading is:

> A competent human-authored/prompt-bank comparator reached DEV k5 = 0.8270 and triggered TRANSFER against the same best button DEV k5 around 0.697. The button is therefore **not** shown superior to good prompting. The current LOCAL result only shows that the button beats a weaker, unaudited APE/fallback comparator with DEV k5 = 0.5343.

Until the frozen APE comparator is rerun with persisted candidate artifacts and correct sampling, “LOCAL VERIFIED-CONTROL” would be an over-claim. The current artifacts are useful as exploratory evidence that the button has a real held-out calibration effect against the stored prompt, not as sound evidence of verified control beyond prompting.

## Final explicit verdict

**VERDICT: NOT-SOUND**
