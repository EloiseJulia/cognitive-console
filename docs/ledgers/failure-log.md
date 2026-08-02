# Failure Log

> Records dead ends, attributions, unexplained anomalies, non-reproducible routes, and randomness risks.
> Prevents repeat trial-and-error after Manager rotation and guards against survivor bias.

(none yet)

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
