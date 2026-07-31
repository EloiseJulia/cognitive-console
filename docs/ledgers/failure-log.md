# Failure Log

> Records dead ends, attributions, unexplained anomalies, non-reproducible routes, and randomness risks.
> Prevents repeat trial-and-error after Manager rotation and guards against survivor bias.

(none yet)

## 2026-07-31 · E-0012 frozen harness diverged from frozen §5-B APE sampling spec (freeze-integrity failure; caught by results audit, no bad claim shipped)
- Frozen prereg §5-B (D-0059) explicitly mandates APE candidate generation at **temperature=0.9, top_p=0.9, seed=42, do_sample** (single meta-prompt call, N_cand=50). But the frozen harness `generate_candidates_real` (`e0012_ape.py:134-156`) calls `backend.generate(meta_prompt, steer, max_new_tokens=4096)` passing **none** of these; `SteeredHFBackend.generate` defaults to `do_sample=False` (GREEDY), temperature=1.0, no top_p, seed unused. → the model-generated APE comparator was produced GREEDILY, not per the frozen stochastic procedure.
- Compounding (BLOCKER-2): the 50 candidates + padding count were never persisted; the recorded winner (candidate_id=45) is **byte-identical to authored prompt CAL-09** → greedy single-shot generation almost certainly yielded few parseable candidates that were then padded with authored prompts, so the "model-generated comparator" was substantially authored-fallback AND unauditable.
- **Consequence:** the E-0012b model-gen re-run's TRANSFER→LOCAL flip (APE k5 0.827→0.534) is almost certainly an ARTIFACT of the broken generator, NOT a real positive. Independent hostile audit verdict = **NOT-SOUND** (`reviews/2026-07-31-e0012-modelgen-audit/audit-report.md`). No positive claim was shipped — caught at the results-audit gate before any paper edit.
- **Why earlier harness audits (H-01..H-06, N-01/N-02) missed it:** those audits validated the SYNTHETIC/offline path and the frozen-diff-empty check, but the real-model generation path (`backend.generate` sampling args) was never exercised end-to-end against §5-B until this GPU run. The frozen-diff check confirmed code was unchanged since freeze — but the code was already wrong at freeze time. **Lesson: a "frozen == frozen" byte-diff does NOT prove the frozen code implements the frozen SPEC; add a spec-conformance test (assert do_sample/temperature/top_p/seed actually passed to the backend) BEFORE freezing any protocol whose parameters live in prose.** Also: always persist the full comparator candidate set + source(model|authored_fallback) + padding count, or the comparator is unauditable by construction.
- **Verified-still-solid (not affected):** DEV/TEST split integrity (0 overlap), synthetic_proxy=false on all 22,311 raw pairs, N-01 guard active, Stage1 TEST arithmetic reproducible (button DOES have a real held-out calibration effect vs the stored comparator, PROBE δ=0.144 CI[0.086,0.198]), kill-rule/verdict derivation correct, Stage0 105/105 + Bonferroni handled. The button's behavioral effect is real; what is UNSOUND is the claim it beats a FAIR prompt baseline.


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
