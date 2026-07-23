# Claim Ledger

> Every Claim entering Abstract / Introduction-Contributions / Conclusion MUST map here with sufficient
> evidence. Every main table/figure MUST state which Claims it supports. Contradicting evidence is never
> deleted — only explained, scope-narrowed, or the Claim withdrawn. (AI-Instruction Part I §4.2)

Status values: proposed | partially-supported | supported | contradicted | withdrawn

---

## C1 — Semantic Facade (RQ1)
- **Statement:** For chosen cognitive axes, the strongest human-readable prompt's mid-layer activation
  projects onto the CAA vector direction far below vector-only AND far above a random-direction null
  baseline, with a pre-registered meaningfully large gap.
- **Scope:** Llama-3-8B-Instruct, Qwen2.5-7B-Instruct; axes = Deliberation/Skepticism/Uncertainty/Focus.
- **Type:** empirical regularity (diagnostic → confirmatory after protocol freeze)
- **Status:** partially-supported (EXPLORATORY, 1.5B, STRENGTHENED D-0019/E-0002) — 2/4 axes hold under a
  non-degenerate layer rule + 16 prompts/axis + 3 seeds + top-k robustness: deliberation 0.658 [0.567,0.750],
  uncertainty 0.687 [0.590,0.782] (CI<1, seed-stable, multi-layer). skepticism 0.887 borderline (layer-fragile).
  focus UNSTABLE at 1.5B (no non-degenerate direction — real negative). NOT confirmatory (small model, unfrozen).
- **Required evidence:** projection/cosine of strongest-prompt vs CAA vector vs random null; blind-eval.
- **Known limits:** projection is a linear proxy; axis may be non-linear/multi-mechanism.
- **Paper location:** TBD

## C2a — Internal-State Non-Surjectivity (RQ2, theory-backed)
- **Statement:** Latent steering reaches internal residual states that no prompt in a bounded search
  reproduces.
- **Scope:** internal activations; ≥2 open models. **Basis:** Mishra et al. (2604.09839).
- **Type:** theory-supported empirical check
- **Status:** proposed
- **Falsified if:** a bounded prompt search reproduces the steered internal state.

## C2b — Behavioral Gap + Conflict Resolution (RQ2, CORE — empirical, NOT from theory)
- **Statement:** On compliance-floor tasks, a bounded prompt search (OPRO + human best-effort, fixed
  budget) cannot cross a behavioral control threshold the latent channel crosses; AND the dual-channel +
  attribution panel lets non-experts attribute & resolve prompt↔latent conflict better than prompt-only,
  steering-only, OR dual-channel-without-panel (condition D).
- **Scope:** 4-condition controlled study; open white-box models.
- **Type:** interaction paradigm + empirical (confirmatory core)
- **Status:** proposed (v0.2: separated from C2a; de-confounded via condition D after R2-B1/R2-B2)
- **Required evidence:** bounded-prompt-search ceiling demonstrated; attribution accuracy + trust
  calibration gain of C vs A/B/D with effect size + uncertainty.
- **Known limits:** depends on C1; risk steering changes only surface style (tested via reasoning task).
  **Threat (PSR/"Steer Like the LLM", ICML 2026):** steering can be trained to match/exceed prompt
  behaviorally → C2b must frame the gap under a *bounded, user-realistic prompt search*, not absolute, and
  cite/pre-empt PSR.
- **Paper location:** TBD

## C3 — Boundary Object / Cross-Model Trust (RQ3, extension)
- **Statement:** Metacognitive-axis levers preserve perceived control/continuity across a backend model
  swap better than prompt folklore.
- **Scope:** Llama-3 → Qwen-2.5 swap; same axis levers.
- **Type:** empirical (exploratory → extension)
- **Status:** proposed
- **Known limits:** cross-model automatic re-mapping is the hardest engineering piece.
- **Paper location:** TBD
