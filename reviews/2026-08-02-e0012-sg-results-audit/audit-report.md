# E-0012-SG settling-grid results hostile audit

Auditor: independent hostile auditor; did not write the code or run the experiment.  
Checkout audited: `run/e0012-sg-20260802` at `dcad974`.  
Primary artifacts: `results/E-0012-SG/settling_grid.json`, `results/E-0012-SG/settling_grid_raw_pairs.jsonl`, `results/E-0012-SG/run_e0012_sg.log`.  
Related artifacts: `results/E-0012/direction_provenance.json`, `results/E-0012-CS/comparator_strength.json`.

## Commands actually run

- Verified branch/status/head and artifact presence with `git --no-pager status --short --branch`, `git --no-pager rev-parse --short HEAD`, and `Get-ChildItem results\E-0012-SG`.
- Read `AGENTS.md`, `AI-Instruction.md` Part I §9, the frozen SG prereg, A-lite results audit, CS reconcile audit, and decision-log D-0067..D-0071.
- Inspected source: `scripts/run_e0012_settling_grid.py`, `scripts/run_e0012_verified_control.py`, `src/cognitive_console/eval/e0012_triviaqa.py`, `src/cognitive_console/eval/scorers.py`, `src/cognitive_console/experiments/e0012_harness.py`, `src/cognitive_console/experiments/e0012_steer_hf.py`, and `src/cognitive_console/experiments/adjudicate_c2b.py`.
- Parsed and recomputed from raw JSONL with independent Python: counts, condition means, paired deltas, cluster bootstrap CIs (`B=10000, seed=0`), prompt equality, confidence/correctness distributions, correct-vs-incorrect confidence gaps, AUC-style confidence discrimination, ECE/reliability bins, and fixture contents.
- Searched for answer/transcript artifacts with `glob **/*transcript*`, `glob **/*answer*`, `glob **/*raw*`, and script/source `rg`; none of SG/E-0012/CS preserve generated texts, only raw confidence/correctness pairs (and E-0006 text hashes).

## Same-direction guarantee

**PASS.** The HF SG artifact records `backend=hf`, `synthetic_proxy=false`, layer 18, alpha 24, and a hash assertion where expected and actual A-lite hashes are identical: `da5723a451f7bb57c5b8c35c32e679fa30d89d428d8fb24fa5f4cdf236a6e60e` (`results/E-0012-SG/settling_grid.json:110-121`; also printed in `results/E-0012-SG/run_e0012_sg.log:21-32`). The A-lite provenance has the matching real-probe layer-18 record with `method=real_probe`, `family=BTN-CAL-PROBE`, `layer=18`, `vector_norm=1.0`, and the same vector SHA (`results/E-0012/direction_provenance.json:1-233`).

The code path is hard-fail, not advisory: SG loads exactly one A-lite `real_probe` L18 hash, re-derives `derive_probe_direction_real(layer=18, ..., seed=42)`, and raises on mismatch (`scripts/run_e0012_settling_grid.py:105-153`). Steered scoring then passes each condition's `prompt_text`, `alpha`, `direction`, and `layer` into `_eval_items_with_raw_pairs` (`scripts/run_e0012_settling_grid.py:275-292`). Each steered condition in JSON carries `alpha=24.0`, `layer=18`, and the same direction SHA; e.g. `SYNTH-BANK-26__probe_L18_a24` at `results/E-0012-SG/settling_grid.json:15030-15043`.

## Integrity checks

- Raw rows: 1,590 = 6 conditions × 53 items × k=5.
- `synthetic_proxy=false`: 1,590/1,590 rows. This means HF generations were parsed, **not** that the item fixture itself is real TriviaQA.
- Per condition: exactly 265 rows, 53 item ids, min/max 5 samples per item.
- Split: 27 DEV / 53 TEST, `dev_test_overlap_n=0` in artifact and recomputed (`results/E-0012-SG/settling_grid.json:40-104`).
- N-01 real-pair guard is active for HF: source requires `raw_store.has_real_pairs(condition_id)` after scoring (`scripts/run_e0012_settling_grid.py:293-297`); raw rows all have `synthetic_proxy=false`.
- Prompt identity: SG `SYNTH-BANK-26` prompt exactly equals CS `best_synthetic_bank.text`, and SG `CAL-09` exactly equals CS `cal_09.text`. SG reproduces CS anchors exactly: SYNTH26/none 0.794047, CAL09/none 0.536575, empty/none 0.144028 (`results/E-0012-SG/settling_grid.json:18067-18070`; CS values at `results/E-0012-CS/comparator_strength.json:672-704`).

## Recomputed condition means

| condition | mean 1-Brier | mean confidence | conf std | accuracy |
|---|---:|---:|---:|---:|
| empty / none | 0.144028 | 0.952264 | 0.010396 | 0.056604 |
| empty / probe | 0.104199 | 0.975283 | 0.021754 | 0.060377 |
| CAL-09 / none | 0.536575 | 0.696189 | 0.131290 | 0.083019 |
| CAL-09 / probe | 0.825648 | 0.364340 | 0.174034 | 0.060377 |
| SYNTH-BANK-26 / none | 0.794047 | 0.433019 | 0.141269 | 0.056604 |
| SYNTH-BANK-26 / probe | 0.925094 | 0.201132 | 0.035270 | 0.056604 |

## Recomputed paired deltas + proper CIs

Independent paired per-item cluster bootstrap, percentile CI, `B=10000`, `seed=0`:

| readout | treatment - control | mean delta | 95% CI | excludes 0? |
|---|---|---:|---:|---|
| pure steering | empty+probe − empty | -0.039829 | [-0.049222, -0.028520] | yes, negative |
| CAL-09-conditioned steering | CAL09+probe − CAL09 | +0.289073 | [+0.216607, +0.355069] | yes, positive |
| SYNTH26-conditioned steering | SYNTH26+probe − SYNTH26 | +0.131047 | [+0.087999, +0.168935] | yes, positive |
| best steered vs best prompt-only | SYNTH26+probe − SYNTH26 | +0.131047 | [+0.087999, +0.168935] | yes, positive |

This confirms the arithmetic of the Manager's key +0.131 with CI about `[0.087, 0.169]`. The persisted artifact also contains nonzero CIs, using script seeds 42..45: key artifact CI `[0.086791, 0.169039]`; best-vs-best artifact CI `[0.088302, 0.169294]` (`results/E-0012-SG/settling_grid.json:18011-18065`). I do **not** reproduce a `[0,0]` CI serialization bug in this checkout; source serializes `ci95: [ci.ci_lo, ci.ci_hi]` after `cluster_bootstrap_ci` (`scripts/run_e0012_settling_grid.py:321-370`).

## Primary degeneracy audit: discrimination and ECE

The +0.131 is **not** evidence of improved confidence discrimination. It is a mechanical Brier gain from lowering nearly all confidence on an almost-always-wrong item set.

| condition | acc | mean conf correct | mean conf incorrect | correct−incorrect gap | confidence AUC | ECE-10 |
|---|---:|---:|---:|---:|---:|---:|
| empty / none | 0.056604 | 0.950000 | 0.952400 | -0.002400 | 0.4760 | 0.895660 |
| empty / probe | 0.060377 | 0.962500 | 0.976104 | -0.013604 | 0.3907 | 0.914906 |
| CAL-09 / none | 0.083019 | 0.731818 | 0.692963 | +0.038855 | 0.5459 | 0.613170 |
| CAL-09 / probe | 0.060377 | 0.406250 | 0.361647 | +0.044603 | 0.5453 | 0.303962 |
| SYNTH-BANK-26 / none | 0.056604 | 0.513333 | 0.428200 | +0.085133 | 0.6823 | 0.376415 |
| SYNTH-BANK-26 / probe | 0.056604 | 0.206667 | 0.200800 | +0.005867 | 0.5212 | 0.144528 |

For the key SYNTH26 condition, steering collapses confidence from 0.433±0.141 to 0.201±0.035 while accuracy stays exactly 0.056604. The correct-vs-incorrect confidence gap collapses from +0.0851 to +0.0059, and AUC falls from 0.682 to near chance (0.521). ECE improves only because global mean confidence moves closer to the base error rate (~94% wrong), not because the model better distinguishes right from wrong.

Reliability bins make this explicit. `SYNTH-BANK-26__probe_L18_a24` places 252/265 samples in the 0.2-0.3 bin with accuracy 0.0595 and mean confidence 0.2060; it is a nearly constant low-confidence policy. Correct samples are harmed by lower confidence (correct-sample 1-Brier 0.7607 → 0.3703), while incorrect samples dominate the mean and benefit (incorrect-sample 1-Brier 0.7961 → 0.9584). This is degenerate confidence suppression, not a genuine calibration-control affordance.

## Accuracy/scoring artifact audit

### The ~6% accuracy is not credible TriviaQA performance

E-0012 is documented as a TriviaQA validation `rc.nocontext` pool (`src/cognitive_console/eval/e0012_triviaqa.py:1-16`), but SG and A-lite/CS load the offline fixture unconditionally: SG `load_frozen_split()` calls `load_e0012_pool(use_fixture=True)` (`scripts/run_e0012_settling_grid.py:85-89`), and A-lite HF does the same (`scripts/run_e0012_verified_control.py:145-151`). The unified loader returns the committed fixture when `use_fixture=True` (`src/cognitive_console/eval/e0012_triviaqa.py:419-428`).

That committed fixture is **not** TriviaQA. All 80 rows are templated prompts like `What is the name of a world capital city? (1)` with arbitrary cyclic city answers (`Paris`, `London`, ..., `Bern`) (`data/e0012_pool/triviaqa_e0012.jsonl:1-12`, `75-80`). This is not a question with a unique gold answer; many world capitals are valid. Scoring with exact/alias substring matching therefore marks almost every plausible capital answer incorrect unless it happens to match the row's arbitrary assigned city. The observed ~5-8% accuracy is consistent with this invalid fixture, not with Qwen2.5-7B's TriviaQA capability.

### Scoring path and transcripts

`item_is_correct` itself is a simple deterministic exact/alias substring scorer for nonnumeric free text (`src/cognitive_console/eval/scorers.py:208-238`). `_eval_items_with_raw_pairs` applies `parse_confidence(text)` and `item_is_correct(item, text)` to HF raw texts, then persists only confidence/correctness/1-Brier, not the text (`src/cognitive_console/experiments/e0012_harness.py:256-272`). `SteeredHFTextCapableSampler` does return texts in memory (`src/cognitive_console/experiments/e0012_steer_hf.py:85-124`), but SG does not save them.

I found no SG/E-0012/CS transcript or answer-text artifact. E-0006 baseline stores `text_sha256` only, not answer text (`data/e0006_uncertainty_baseline/e0006_uncertainty_baseline.jsonl:1-5`). Therefore I cannot spot-check whether genuinely correct generated answers were marked wrong. But the committed E-0012 item fixture itself is already sufficient to explain and invalidate the ~6% accuracy: the gold labels are arbitrary for nonspecific prompts.

## Over-claim / confound analysis

1. **Arithmetic paired Brier claim:** The raw paired SYNTH26 1-Brier delta is real in these artifacts, but it is not a genuine calibration/discrimination improvement.
2. **Degenerate confidence-suppression:** The key positive survives only as "lowering confidence improved Brier on a dataset where ~94% of samples are scored wrong." It does not survive as a control affordance.
3. **Data validity:** Because the E-0012 fixture is not real TriviaQA and has non-unique prompts with arbitrary gold answers, the entire E-0012/A-lite/CS calibration signal is corrupted for paper claims.
4. **Selection/multiple comparisons:** Even ignoring the fixture blocker, the "best steered beats best prompt-only" framing inherits CS TEST selection of SYNTH-BANK-26 and should be treated as descriptive, not unbiased confirmatory evidence.
5. **Pure steering harmful:** Empty+probe is significantly worse than empty/no-steer (delta -0.0398), reinforcing that the direction is not a standalone calibration button.
6. **Scope:** No generalization to other models, real TriviaQA, other axes, directions, prompts, causal mechanisms, answer quality, or user-facing fluency is supported.

## Ranked findings

### BLOCKER-1 — E-0012/CS/SG did not evaluate the documented TriviaQA pool; it evaluated an invalid templated fixture

**Evidence:** SG and A-lite HF load `load_e0012_pool(use_fixture=True)` (`scripts/run_e0012_settling_grid.py:85-89`; `scripts/run_e0012_verified_control.py:145-151`). The fixture rows are all `What is the name of a world capital city? (n)` with arbitrary city gold answers (`data/e0012_pool/triviaqa_e0012.jsonl:1-12`, `75-80`).

**Impact:** The ~6% accuracy is a data/scoring artifact from non-unique prompts and arbitrary labels. This corrupts E-0012, CS, and SG as evidence about TriviaQA calibration.

**Minimum fix:** Regenerate and audit the E-0012 fixture from real `mandarjoshi/trivia_qa` `rc.nocontext` validation rows, persist item-source hashes, and rerun CS/A-lite/SG. Save generated texts for scoring audit.

### BLOCKER-2 — SG positive is degenerate confidence suppression, not genuine calibration/discrimination improvement

**Evidence:** SYNTH26+probe leaves accuracy unchanged (0.056604 → 0.056604) while collapsing confidence (0.433019 → 0.201132; std 0.141269 → 0.035270). Correct-vs-incorrect confidence gap collapses from +0.085133 to +0.005867 and confidence AUC falls from 0.6823 to 0.5212. ECE improves only because the global confidence level moves toward the very low scored accuracy.

**Impact:** The +0.131 1-Brier delta must not be called a genuine control affordance, complementary steering, or improved calibration in the discriminative sense.

**Minimum fix:** Treat this run as a negative/invalid diagnostic. Require real data plus discrimination/reliability criteria that cannot be passed by uniform confidence lowering.

### MAJOR-1 — Generated answers/transcripts were not persisted, preventing scoring audit

**Evidence:** SG raw JSONL contains item id, channel, alpha, layer, confidence, correctness, 1-Brier, and synthetic flag only. Source records parsed pairs but discards raw text (`e0012_harness.py:256-272`); E-0006 stores text hashes only.

**Impact:** Alias/format scoring failures cannot be spot-checked after the fact. This is especially severe because the observed accuracy is implausibly low.

**Minimum fix:** Persist generated answer text or a redacted auditable answer field for every calibration run.

### MINOR-1 — Pure steering alone is significantly harmful

**Evidence:** empty+probe − empty = -0.039829, CI [-0.049222, -0.028520].

**Impact:** Any "button alone works" claim is false for E-0012-SG.

**Minimum fix:** Present pure steering as negative if E-0012 is rerun on valid data.

## Honest defensible claim

Only this narrow artifact-level statement is defensible: on the committed E-0012 placeholder fixture, with the audited real `BTN-CAL-PROBE@L18` direction at α=24, adding steering to `SYNTH-BANK-26` lowers verbal confidence to an almost constant ~0.20; because the fixture/scorer marks ~94% of samples wrong, this mechanically increases mean 1-Brier by +0.131. This is **not** defensible evidence of genuine calibration control or steering complementing prompting.

## Claims that would over-reach

- "Genuine positive: steering complements prompting" — not supported; the positive is degenerate confidence suppression on invalid labels.
- "Calibration/discrimination improved" — contradicted by collapsed correct-vs-incorrect confidence gap and near-chance confidence AUC.
- "E-0012 measures TriviaQA calibration" — contradicted by the committed world-capital placeholder fixture.
- "Qwen2.5-7B is only ~6% accurate on TriviaQA" — the run did not use real TriviaQA questions.
- "Accuracy/answer quality/fluency improved" — accuracy did not improve and texts were not persisted.
- "Steering alone works" — contradicted by empty+probe.

## Final verdict

**NOT-SOUND.**

The same-direction and raw-pair arithmetic checks pass, but the primary scientific claim fails. The SG +0.131 is a degenerate confidence-suppression artifact on an invalid E-0012 placeholder fixture with arbitrary labels and ~6% scored accuracy. E-0012/CS/SG should not be used to upgrade any core paper claim until the data fixture, scoring auditability, and discrimination-based calibration criteria are fixed and rerun.
