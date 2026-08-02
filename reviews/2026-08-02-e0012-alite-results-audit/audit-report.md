# E-0012 A-lite results hostile audit

Auditor: independent hostile auditor; did not write the code/run.  
Checkout: `run/e0012-alite-20260802` at `846e9fd`.  
Primary artifacts: `results/E-0012/*`; comparator read from current checkout and `git show main:results/E-0012-CS/comparator_strength.json`.

## Commands actually run

- `git status --short --branch`, `git rev-parse HEAD`, artifact listings for `results/E-0012/` and `results/E-0012-CS/`.
- Read `AGENTS.md`, `AI-Instruction.md` audit gate lines, prereg A-lite amendment, D-0067/D-0068/D-0069, CS reconcile audit, real-direction fixes audit/checklist.
- Inspected source with `rg`/`view`: `e0012_harness.py`, `e0012_buttons.py`, `e0012_ape.py`, `run_e0012_verified_control.py`, `e0012_triviaqa.py`, `build_e0006_uncertainty_baseline.py`.
- Parsed and recomputed from `results/E-0012/brier_raw_pairs.jsonl`, `e0012_results.json`, `e0012_stage0_candidates.json`, `e0012_ape_candidates.json`, `direction_provenance.json`, `data/e0006_uncertainty_baseline/*`, and `results/E-0012-CS/*`.
- Used `git show main:results/E-0012-CS/comparator_strength.json` to verify main's CS headline comparator values.

## Directions genuinely real?

**Yes for this A-lite run.** `direction_provenance.json` has exactly 10 records: 5 `real_probe` and 5 `real_caa_mean_diff`, one per layer 18-22 (`results/E-0012/direction_provenance.json:3,234,346,577,689,920,1032,1263,1375,1606`). Every sampled record has `vector_sha256`, `source_artifact_sha256`, and `hyperparameters` (`direction_provenance.json:210-229,322-341`). No record's `method` is synthetic/random; the only "synthetic" wording is prereg-specified PROBE verbal-confidence pair construction, not a random direction.

CONTRA provenance source hash is always `9c1e12ccef1659b9686688bd3d408dfc898ffc70d81d5fe0be783f2d979a4b2f` (`direction_provenance.json:322,665,1008,1351,1694`), matching the E-0006 manifest artifact SHA (`data/e0006_uncertainty_baseline/e0006_uncertainty_baseline.manifest.json:2`). That manifest records frozen E-0006 identity: unsteered empty prompt, k=5, max_new_tokens=64, temperature=0.7, seed=20260723, synthetic_proxy=false (`...manifest.json:87-107`).

The HF run did not hard-fail the real-not-smoke guard: the run log reaches `VERDICT: LOCAL`, Stage0 70/70, Stage1 PASS, and writes results/provenance without Traceback/RuntimeError. Source would hard-fail HF if prederived directions were injected or real inputs missing (`src/cognitive_console/experiments/e0012_harness.py:951-975`) and then asserts real provenance (`e0012_harness.py:984-989`; `e0012_buttons.py:170-186`).

E-0006/E-0012 leakage check: I recomputed overlap between `data/e0006_uncertainty_baseline/e0006_uncertainty_baseline.jsonl` and `data/e0012_pool/triviaqa_e0012.jsonl`: id overlap=0, prompt overlap=0, answer overlap=0. This is consistent with the pool code's seed/offset disjointness statement (`src/cognitive_console/eval/e0012_triviaqa.py:6-11,93-95`).

## Prompt-conditioning of the button score

The button score is **not pure steering**. Stage0 first freezes the best authored prompt on DEV, then evaluates every button with that `best_prompt_text` (`src/cognitive_console/experiments/e0012_harness.py:319-330,367-368`). The DEV kill-rule k5 button score also uses `best_prompt_text` plus the candidate's alpha/direction (`e0012_harness.py:417-421`). Stage1 likewise evaluates:

- steer: `best_prompt_text` + alpha + direction (`e0012_harness.py:637-644`);
- prompt: same `best_prompt_text`, alpha=0 (`e0012_harness.py:648-649`);
- baseline: empty instruction `""`, alpha=0 (`e0012_harness.py:653-654`).

The exact `best_prompt_text` is CAL-09 / APE fallback candidate 44: "Express appropriate uncertainty... Best guess: X. Confidence: 25%." (`results/E-0012/e0012_ape_candidates.json:359-364`; `data/e0012_prompts/calibration_prompts.yaml:111-114`). Therefore:

| Condition | Prompt present? | Steering? | Recomputed TEST mean 1-Brier |
|---|---|---:|---:|
| button_best DEV k5 | CAL-09 | real PROBE L18 α24 | 0.8242 reported (`results/E-0012/e0012_results.json:36-37`) |
| Stage1 TEST steer | CAL-09 | real PROBE L18 α24 | 0.825648 |
| Stage1 TEST prompt | CAL-09 | none | 0.536575 |
| Stage1 TEST baseline | empty string | none | 0.144028 |

Stage1 paired bootstrap Bonferroni CI (M=1, 95%) from `brier_raw_pairs.jsonl`:

| Paired delta | Mean δ | 95% CI |
|---|---:|---:|
| steer - prompt | +0.289073 | [0.216607, 0.355069] |
| steer - baseline | +0.681620 | [0.592850, 0.753366] |
| prompt - baseline | +0.392546 | [0.344921, 0.438165] |

So the run shows a **prompt-conditioned steering increment over CAL-09**, not a standalone button.

## Decisive comparison: real PROBE button vs strongest human prompt

Main's CS comparator reports strongest human prompt `SYNTH-BANK-26` = 0.794047 and `CAL-09` = 0.536575 on the same 53 TEST items (`results/E-0012-CS/comparator_strength.json:672-695`). I verified the same values through `git show main:results/E-0012-CS/comparator_strength.json`.

Head-to-head, using per-item paired differences on the same 53 TEST items:

| Comparison | Mean paired δ | 95% bootstrap CI | Ruling |
|---|---:|---:|---|
| real PROBE prompt+steer (0.825648) - SYNTH-BANK-26 prompt-only (0.794047) | +0.031601 | [-0.013832, 0.075061] | numerically above, **not meaningfully/CI-separated above** |
| real PROBE prompt+steer - CAL-09 prompt-only (0.536575) | +0.289073 | [0.216607, 0.355069] | clearly above CAL-09 |

Fairness caveat: this is prompt+real-steer vs prompt-only. It does **not** isolate pure real PROBE steering. The raw pairs do not include empty-prompt + real PROBE@L18 α24 on TEST, nor SYNTH-BANK-26 + real PROBE. The settling measurement is a same-53-TEST scoring grid: empty+real PROBE vs empty baseline, CAL-09+real PROBE vs CAL-09, and SYNTH-BANK-26+real PROBE vs SYNTH-BANK-26.

### Is this a genuine positive or the honest negative?

**Ruling:** not a genuine verified-control positive. The LOCAL result is technically sound as a prompt-conditioned additive effect, but it does not establish that a real discovered direction beats strong prompting. Against the strongest known human prompt, the real PROBE prompt+steer score is only +0.0316 with a CI crossing zero. Because the channel is CAL-09+steer, calling this "real steering beats prompting" or "verified control" would overclaim.

I also would not reduce it to "steering dominated entirely by prompting": the real direction adds a large held-out increment over CAL-09 (+0.2891 CI excluding zero). The honest narrative is: **sound local prompt-conditioned steering effect; strongest-prompt head-to-head is roughly equal, not beaten; pure steering remains unmeasured.**

## Standard gates

- Split: 27 DEV / 53 TEST, split_seed=42 (`results/E-0012-CS/comparator_strength.json:13-15`); recomputed DEV/TEST overlap=0 and Stage1 item set equals CS TEST.
- Raw pairs: `results/E-0012/brier_raw_pairs.jsonl` has 7,923 rows, all `synthetic_proxy=false`.
- N-01 active: HF sampler is `TextCapableSampler` and hard-fails if real confidence/correctness pairs are unavailable (`e0012_harness.py:711-731`).
- Kill rule: APE k5=0.534306 vs button DEV k5=0.8242, PASS (`results/E-0012/e0012_results.json:31,36-38`); symmetric k=5 code at `e0012_harness.py:403-429`.
- Verdict: LOCAL is correct for Stage1 PASS with no Stage2 (`e0012_harness.py:893-907`; `results/E-0012/e0012_results.json:4,47-66`).
- Cross-axis: SKIPPED is correct for calibration-only conservative run (`e0012_harness.py:80-83`; `results/E-0012/e0012_results.json:45,57`).
- Stage0 anti-forking: 70/70 candidates, 8 pass cutoff, 1 Stage1 candidate (`results/E-0012/e0012_results.json:39-41`; Stage0 best at `results/E-0012/e0012_stage0_candidates.json:81-91`).
- Bonferroni: M=1 advancing candidate, so CI level=0.95 (`e0012_harness.py:1013-1024`). Recomputed Stage1 steer-prompt δ=+0.289073, 95% CI [0.216607, 0.355069], PASS.
- Coherence/safety: reported Stage1 coherence_ok=true, safety unsafe=false (`results/E-0012/e0012_results.json:47-66`).

## APE comparator

APE generation is protocol-conformant and persisted: `generate_candidates_real` samples with `do_sample=True`, temperature `APE_TEMPERATURE`, top_p `APE_TOP_P`, seed=42 (`src/cognitive_console/experiments/e0012_ape.py:174-179`), and the runner persists `e0012_ape_candidates.json` (`scripts/run_e0012_verified_control.py:469-470`). The artifact records 36 model-parseable candidates and 14 authored fallbacks (`results/E-0012/e0012_ape_candidates.json:3-4`); model candidates are present from line 9 onward and authored fallbacks begin at line 297. Winner candidate 44 is an authored fallback CAL-09, with DEV k3=0.513063 and k5=0.534306 (`e0012_ape_candidates.json:359-364`).

## Ranked findings

### MAJOR-1 — Calling LOCAL a pure button / verified-control positive would be false

**Evidence:** Stage0 and Stage1 steer channels use `best_prompt_text` (`e0012_harness.py:367-368,417-421,643-644`), and the baseline alone uses `""` (`e0012_harness.py:653-654`). Recomputed Stage1 steer is CAL-09+real PROBE L18 α24 = 0.825648; prompt-only CAL-09 = 0.536575.

**Impact:** The result is not proof that steering alone beats prompting or that a prompt-unreachable control was discovered.

**Minimum fix:** Frame as prompt-conditioned steering only; require empty-prompt real PROBE TEST measurement before any pure-steering claim.

### MAJOR-2 — Strongest human prompt is not meaningfully beaten

**Evidence:** CS `SYNTH-BANK-26` scored 0.794047 on the same 53 TEST items (`results/E-0012-CS/comparator_strength.json:672-685`). A-lite prompt+steer vs SYNTH-BANK-26 paired δ=+0.031601 with 95% CI [-0.013832, 0.075061].

**Impact:** The paper cannot claim "real discovered direction beats strong prompting". At most it roughly ties the strongest known prompt while relying on CAL-09 prompt-conditioning.

**Minimum fix:** Use `SOUND-BUT-OVERCLAIMS` framing; if needed, run the settling same-TEST pure/prompt-conditioned grid described above.

### MINOR-1 — APE winner is authored fallback, not model-generated

**Evidence:** APE artifact has 36 model candidates and 14 authored fallbacks (`e0012_ape_candidates.json:3-4`); winner candidate 44 is `source: authored_fallback` (`e0012_ape_candidates.json:359-364`). The stochastic model generation itself is present and persisted.

**Impact:** Saying "the model-generated APE winner scored 0.5343" would be inaccurate. The correct phrase is "§5-B APE with stochastic model generation plus preregistered fallback; fallback CAL-09 won."

**Minimum fix:** State fallback provenance wherever the APE winner is discussed.

### UNVERIFIED-1 — Pure real PROBE steering effect on TEST is absent

**Evidence:** `brier_raw_pairs.jsonl` contains Stage1 channels only for `s1_steer_BTN-CAL-PROBE_18_24` (CAL-09+steer), `s1_prompt_...` (CAL-09), and `s1_baseline_...` (empty baseline). There is no empty-prompt + real PROBE L18 α24 channel.

**Impact:** Pure steering may be positive, null, or harmful; this artifact cannot decide. Prior CS pure-steering null was for the old synthetic/random L19 direction and is not evidence about this real PROBE direction.

**Minimum fix:** Score empty-prompt real PROBE@L18 α24 on the same frozen TEST items.

## Final verdict

**SOUND-BUT-OVERCLAIMS-IF-CALLED-VERIFIED-CONTROL.**

The run is sound as a LOCAL, real-direction, prompt-conditioned steering result. It is not a sound genuine positive that real steering beats strong prompting; the strongest human prompt is only numerically below and not CI-separated, and pure real steering was not measured.
