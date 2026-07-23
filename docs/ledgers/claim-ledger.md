# Claim Ledger

> Every Claim entering Abstract / Introduction-Contributions / Conclusion MUST map here with sufficient
> evidence. Every main table/figure MUST state which Claims it supports. Contradicting evidence is never
> deleted — only explained, scope-narrowed, or the Claim withdrawn. (AI-Instruction Part I §4.2)

Status values: proposed | partially-supported | supported | contradicted | withdrawn

---

## C1 — Semantic Facade (RQ1)
- **Statement:** For chosen cognitive axes, the strongest human-readable prompt's mid-layer activation
  projects onto the CAA vector direction significantly below vector-only (projection ≪ 100%).
- **Scope:** Llama-3-8B-Instruct, Qwen2.5-7B-Instruct; axes = Deliberation/Skepticism/Uncertainty/Focus.
- **Type:** empirical regularity (diagnostic → confirmatory after protocol freeze)
- **Status:** proposed
- **Required evidence:** projection/cosine of strongest-prompt activation vs CAA vector; blind-eval.
- **Supporting experiments:** (none yet)
- **Opposing experiments:** (none yet)
- **Known limits:** projection is a linear proxy; axis may be non-linear/multi-mechanism.
- **Paper location:** TBD

## C2 — Non-Surjective Control + Conflict Resolution (RQ2, CORE)
- **Statement:** On compliance-floor tasks, prompt-only cannot cross a control threshold the latent
  channel can; and the dual-channel + attribution panel lets non-experts attribute & resolve
  prompt↔latent conflict better than prompt-only or steering-only.
- **Scope:** 3-condition controlled study; open white-box models.
- **Type:** interaction paradigm + empirical (confirmatory core)
- **Status:** proposed
- **Required evidence:** prompt-unreachable region demonstrated; attribution accuracy + trust-calibration
  gain of condition C vs A/B with effect size + uncertainty.
- **Known limits:** depends on C1 holding; risk that steering only changes surface style.
- **Paper location:** TBD

## C3 — Boundary Object / Cross-Model Trust (RQ3, extension)
- **Statement:** Metacognitive-axis levers preserve perceived control/continuity across a backend model
  swap better than prompt folklore.
- **Scope:** Llama-3 → Qwen-2.5 swap; same axis levers.
- **Type:** empirical (exploratory → extension)
- **Status:** proposed
- **Known limits:** cross-model automatic re-mapping is the hardest engineering piece.
- **Paper location:** TBD
