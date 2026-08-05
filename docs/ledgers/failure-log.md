# Failure Log

> Records dead ends, attributions, unexplained anomalies, non-reproducible routes, and randomness risks.
> Prevents repeat trial-and-error after Manager rotation and guards against survivor bias.


## 2026-08-05 · E-0016 frozen Regime-B run failed before DEV: tokenizer AddedToken was not JSON serializable
- Exact clean run commit `4def9ba59a00909d4cf2aae7dbdb1665877d6204`, exact prereg §9.2 command, physical A800 GPU 3. The single authorized attempt ran 26 seconds (upper bound 0.00722222 GPU-h) and exited 1 while `capture_environment_identity` serialized tokenizer configuration. With transformers 5.14.1, the object contained an `AddedToken`, which the frozen canonical JSON path could not serialize.
- The runner failed before direction extraction, hook-bites, DEV generation, eligibility, and TEST. Therefore DEV baseline false-refusal and runner verdict are UNVERIFIED; TEST did not run. No retry, dependency change, code modification, parameter change, or Regime A fallback was attempted.
- Frozen data preflight passed all revision/content/schema/row/canonical hashes for Paul/XSTest, AdvBench, and Alpaca; cached model revision resolved exactly. Only source-state and execution-failure lineage artifacts were produced, both `valid_for_paper=false`; no raw harmful text or harmful generation occurred. The canonical AddedToken/config-key serialization repair (schema v3) was independently audited SOUND and merged at `c094f07fa3592c2210f46caba9e69c49a5a92fad` without scientific-parameter drift. Retry is authorized under D-0095's original hard cap; it has not yet run.

## 2026-08-04 · E-0014 positive control: fp16-miscalibrated hook-bites integrity guard aborted a completed GPU run, wasting ~1.5 GPU-h (no results written)
- The E-0014 hook-bites guard (proves the steering hook actually perturbs activations) was fixed once already (absolute-L2 1e-3 → dtype-robust cosine≥0.999 + rel-norm≤0.05, per the code audit's BLOCKER-1). But `0.999` cosine is STILL too strict for fp16 at the DEV-selected small alpha (α=2): measured per-probe cosine ≈0.998, rel-norm-error ≈0.0016. fp16 quantization noise is ~constant in absolute terms, so cosine of (steered−unsteered) vs û degrades as alpha shrinks; the fixed α=4 check passed but the post-hoc frozen-α=2 check failed all 4 probes on cosine alone despite near-perfect magnitude.
- **Two compounding faults:** (1) integrity-guard threshold mis-calibrated for the run's own dtype/alpha regime; (2) the frozen-α hook-bites check ran AFTER all generation (~3400 gens), so its failure discarded the entire completed run because the results write came after the assertion. Net: full GPU budget spent, zero artifacts.
- **Lessons (repository-wide):** (a) Calibrate integrity-guard tolerances to the ACTUAL run dtype AND the full parameter regime (here every candidate alpha, not just one), not a single convenient value; the magnitude/relative check (rel-norm) is the tight quantitative guard, cosine should only reject gross direction errors (floor 0.99, not 0.999). (b) Run ALL cheap fail-closed integrity guards (real-not-smoke, hook-bites across the whole alpha grid, item-pool disjointness) UPFRONT, before any expensive generation, so a guard failure costs seconds not GPU-hours; never place a fail-closed assertion after the compute it is meant to protect, and/or write results before non-safety assertions. (c) A guard that flags a demonstrably-correct operation (hook bites at rel-norm 0.16%) is itself a bug to fix, distinct from a guard catching real smoke — verify which before relaxing, and document the measured separation (working≈0.998/0.002 vs dead≈0/1) so relaxation is not goalpost-moving.
- **Blast radius:** none on results/claims — no E-0014 number was produced or entered the paper; the paper's audited BORDERLINE state is unchanged. Cost only: ~1.5 GPU-h on A800 GPU1. Fix: recalibrate cosine floor to 0.99 + validate hook-bites over the full ALPHA_GRID upfront (fail-fast) → re-audit → re-run.

## 2026-08-02 · E-0012 4th placeholder bug: ran on a fake world-capital fixture (use_fixture=True hardcoded), not real TriviaQA — ENTIRE E-0012 line invalid
- `run_e0012_verified_control.py:148` + `run_e0012_settling_grid.py:87` hardcode `load_e0012_pool(use_fixture=True)`; the committed `data/e0012_pool/triviaqa_e0012.jsonl` is 80 templated `"What is the name of a world capital city? (n)"` rows with arbitrary cyclic gold answers. Non-unique prompts + arbitrary labels → ~94% scored-wrong → the ~6% "accuracy" that pervaded every E-0012 result. The prereg said "TriviaQA Option A"; the code loaded the offline placeholder.
- This is the FOURTH placeholder-vs-real bug in E-0012 (1: F-01 synthetic APE comparator; 2: greedy APE sampling vs frozen §5-B; 3: random Gaussian directions vs real probe/CAA; 4: fixture data vs real TriviaQA). Each was caught ONLY after a GPU run, by the results audit — never by pre-run code audits, because the pre-run audits validated wiring/consistency/tests but did not assert that the RUN-TIME DATA/DIRECTION/SAMPLING were real (not smoke) end-to-end. The E-0006 baseline builder (correctly `use_fixture=False`) masked this: my overlap check compared real-E-0006 items vs the FAKE-E-0012 fixture and got overlap=0 for the wrong reason.
- **Root-cause lesson (repository-wide):** for ANY confirmatory experiment, add a RUN-TIME real-data assertion analogous to the N-01 synthetic_proxy guard and the real-direction provenance guard: on the real (hf/GPU) backend, HARD-FAIL if the item pool is a fixture (`use_fixture=True` / fixture-schema / placeholder ids) — the same class of guard for DATA that we belatedly added for DIRECTIONS. A prereg naming a real dataset does not prove the code loads it; assert the loaded item source (dataset id + split + item-source hash) at run time, on the real backend, before scoring. Prefer failing closed on any smoke/fixture/placeholder on real runs.
- **Blast radius:** confined to E-0012 (its two runners). C1/C2 (E-0003..E-0011) use `run_c2b_adjudication.py`/`run_arm_matrix.py` which take `use_fixture` from args and recorded `"use_fixture": false` on the real runs → REAL data, UNAFFECTED. Manager recommends abandoning E-0012 (D-0072).


## 2026-08-01 · E-0012 button directions were RANDOM Gaussian placeholders, not the frozen §5-A real probe/CAA/PCA directions (3rd freeze-integrity bug; whole button side invalid)
- `e0012_buttons.py::derive_probe_direction_synthetic` (and the CONTRA/LOGIT-MARGIN synthetic siblings) return `rng.standard_normal(hidden_dim)` — a seeded random Gaussian unit vector, documented as an offline-smoke stand-in. `all_directions_for_layer` (the ONLY direction path in `e0012_harness.py:943` and the CS script) dispatches to these synthetic factories. The real-GPU CAA/probe derivations exist in e0012_buttons.py but are DEAD CODE, never wired into the runner.
- Frozen prereg §5-A/§3-B specified REAL directions (trained probe on activation pairs; CAA mean-diff; logit-margin PCA). So every E-0012 GPU run steered along random vectors → the entire button/steering side is INVALID as a test of RQ-E0012.
- **Why 5+ prior audits (H-01..H-06, F-01, v3, CS-code) missed it:** they verified wiring/consistency/sampling/persistence and that CS==v3 used the SAME direction factory — but none checked that the direction was a REAL derived vector vs a random placeholder, because the factory name (`all_directions_for_layer`) and the ButtonDirection.notes ("Real GPU CAA mean-diff…" on the DEAD real function) masked it. Only the CS reconciliation audit's direction rebuild surfaced the "SYNTHETIC random stand-in" note. **Lesson: for any steering/intervention experiment, add a test asserting the intervention VECTOR is the real pre-registered derivation (e.g. probe/CAA computed from real activations with a checkable provenance hash), not a random/smoke placeholder, BEFORE the GPU run — and treat a "synthetic/smoke" direction factory as a HARD-FAIL on real (hf) backends, exactly like the N-01 synthetic_proxy guard for outcomes.** The E-0012 harness was built entirely with offline placeholders (synthetic candidates, greedy generation, random directions) and the real derivations were never wired for GPU; the frozen prereg described the real experiment, the code ran the smoke version.
- **Blast radius:** confined to E-0012 (e0012_buttons.py factory). C1/C2 frozen headline (E-0003..E-0011) uses a different, independently-audited real-CAA/ITI codepath (E-0007 verified steered−baseline==α·dir on real GPU) and is UNAFFECTED. The CS human-prompt evidence is direction-independent and remains sound.


## 2026-07-31 · E-0012 frozen harness diverged from frozen §5-B APE sampling spec (freeze-integrity failure; caught by results audit, no bad claim shipped)
- Frozen prereg §5-B (D-0059) mandates APE candidate generation at **temperature=0.9, top_p=0.9, seed=42, do_sample** (single meta-prompt call, N_cand=50). But the frozen harness `generate_candidates_real` (`e0012_ape.py`) called `backend.generate(meta_prompt, steer, max_new_tokens=4096)` passing **none** of these; `SteeredHFBackend.generate` defaults to `do_sample=False` (GREEDY). → the model-generated APE comparator (E-0012b) was produced GREEDILY, not per the frozen stochastic procedure. Compounded by non-persistence of candidates (winner=authored CAL-09 fallback).
- **Consequence:** E-0012b TRANSFER→LOCAL flip was an artifact; audit NOT-SOUND. No positive claim shipped — caught at the results-audit gate. Fixed in track A (D-0064); sound v3 re-run (D-0065) still gives LOCAL vs the frozen comparator, but audit ruled SOUND-BUT-OVERCLAIMS (a human prompt @0.827 beats the button @0.697).
- **Why earlier harness audits (H-01..H-06) missed it:** they validated the offline/synthetic path + a frozen-diff-empty check; the real-model generation sampling path was never exercised end-to-end vs §5-B until the GPU run. **Lesson: a "frozen==frozen" byte-diff does NOT prove the frozen code implements the frozen SPEC — add a spec-conformance test (assert do_sample/temperature/top_p/seed actually reach the backend) BEFORE freezing any protocol whose parameters live in prose. Always persist the full comparator candidate set + source(model|authored_fallback) + padding count, or the comparator is unauditable by construction.** (Both lessons now enforced by tests added in D-0064.)


## 2026-07-26 · PSR arm first GPU attempt: double-model-load CUDA OOM (caught by smoke gate, no bad verdict)
- `run_psr_arm.py` loaded TWO Qwen2.5-7B copies (basis-extraction provider + steered-generation backend) → ~30GB
  > 24GB VRAM → CUDA OOM before PSR DEV evals. The MANDATORY GPU smoke gate caught it; the full arm did NOT run
  and NO verdict was fabricated (recorded honestly as `not_run_invalid_smoke`, PR#14, closed as superseded).
- Steering mechanism itself verified correct at smoke (steered−baseline == α·dir, cos=0.99998).
- Fix (PR#15, D-0043): share ONE HF model instance across extraction+generation+adjudication; peak VRAM ~15-17GB;
  protocol byte-identical. Re-run succeeded → E-0009. **Lesson:** for single-GPU steering runs, always share one
  model handle across extraction + steered-generation; add a smoke that asserts peak VRAM / single model load.

## 2026-07-23 · 1.5B facade_ratio is denominator-dependent (metric artifact, audit D-0016)
- The v0 "fixed" facade_ratio = prompt_reach(from neutral) / ‖v‖(α=1, from neg pole) is NOT scale-invariant
  and mixes origins → produces ratio<1 partly by construction. Under a same-origin scale-free denominator
  (neutral→pos-pole range), the "3/4 facade" collapses to ~1/4 (only uncertainty survives).
- **Do-not-repeat:** never report facade_ratio against ‖v‖ with an arbitrary α; always use a same-origin,
  scale-free reach fraction with a CI + neutral-set sensitivity, and unit-test THAT exact computation.
- "above null" in high-dim is a trivial bar (random projections ≈0); it is NOT evidence of a real gap.

## 2026-07-24 · C2b A800 adjudication hung + lost 11h56m (D-0029)
- The frozen C2b run on the borrowed A800 ran ~12h and was killed with NO output. Host NVIDIA driver was
  reloaded mid-run (NVML mismatch) → broken CUDA context → process spun 100%/one-core, zero progress.
- No checkpoint/partial output (in-memory only) → 11h56m of compute unsalvageable.
- **Do-not-repeat:** never launch a multi-hour generation run without (1) per-cell progress logging, (2)
  periodic disk checkpointing of partial per-item outcomes (resumable), (3) a bounded generation budget
  (batched generation / smaller max_new_tokens / smaller N) sized to finish in ~1-2h, (4) awareness that a
  shared/borrowed host may have driver maintenance. Estimate generation count BEFORE launching (~10,700 gens
  at max_new_tokens=256 single-sequence was ~5-12h, not the 1.5-3h assumed).

## 2026-07-23 · C1 facade pilot (CPU/Qwen2.5-0.5B) — underpowered + metric asymmetry
- **Route:** extract CAA vectors + measure semantic facade on Qwen2.5-0.5B-Instruct, CPU, forward-only.
- **Failure modes observed:**
  - `skepticism` CAA extraction FAILED at 0.5B: ‖v‖=0.18, no separable pos/neg direction, defaulted to layer 2
    with a wrong-way shift. Small model cannot resolve this axis.
  - 2/4 axes "overshoot" (facade_ratio ≥ 1) — NOT a real prompts-beat-steering finding; caused by comparing
    the MAX held-out prompt to the MEAN latent ‖v‖ with neutral≈neg (max≥mean makes ratio≥1 structural).
- **Attribution:** (1) 0.5B ~15× below the 7–8B spec target → weak/unstable directions; (2) Manager metric
  design flaw (max-vs-mean asymmetry). Both correctable.
- **Lesson / do-not-repeat:** before the next facade read, (a) use a model ≥ a few B (ideally 7–8B), and
  (b) fix the facade statistic to consistent estimators (mean-vs-mean, and/or compare max-prompt to max-latent).
  Do not interpret facade_ratio from the 0.5B run as evidence for or against C1.
