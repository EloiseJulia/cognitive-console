# Failure Log

> Records dead ends, attributions, unexplained anomalies, non-reproducible routes, and randomness risks.
> Prevents repeat trial-and-error after Manager rotation and guards against survivor bias.

(none yet)

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
