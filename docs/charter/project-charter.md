# Research Charter · Non-Surjective Dual-Channel Cognitive Console

- **Charter Version**: v0.1 (DRAFT — pending human confirmation)
- **Status**: proposed (NOT frozen). Freeze occurs only after human sign-off + Charter Review (R1/R2/R3) triage closed.
- **Author (Manager)**: manager-cognitive-console
- **Date**: 2026-07-23
- **Source of truth (idea)**: `开题报告_非满射双通道认知控制台.md`
- **Governing rules**: `AGENTS.md`, `AI-Instruction.md` Part I

> Any change to Research Question / Contribution Type / Core Novelty / Target Venue after freeze
> requires: (1) human approval (AGENTS.md §5), (2) a Decision Log entry, (3) re-running the
> Novelty Gate and Evidence Gate. Contradicting evidence is never deleted — only explained,
> scope-narrowed, or the Claim is withdrawn.

---

## 1. Research Question

**Primary (RQ2 — core):** When a single interface simultaneously exposes a *text soft-constraint
channel* (prompt) and a *latent hard-intervention channel* (CAA/RepE steering vectors) acting on the
same small set of interpretable cognitive axes, how do non-expert users understand, coordinate, and
— when the two channels **conflict** (e.g. prompt demands "confident" while the skepticism slider is
pulled high) — attribute and adapt to a control capability that provably *exceeds what any prompt can
reach*?

**Supporting:**
- **RQ1 (epistemic mismatch / semantic facade):** To what degree does the latent distribution a
  folk-theory prompt actually activates diverge from the cognitive attribute the user *believes* they
  are controlling, and how does this "semantic facade" mis-calibrate trust?
- **RQ3 (boundary object / cross-model trust):** Can metacognitive-axis dual-channel levers act as a
  *boundary object* that buffers users against internal dose-response drift when the backing model
  changes (Llama-3 → Qwen-2.5), preserving coherent interaction and calibrated trust?

**Betting order:** RQ2 = core contribution; RQ1 = must win via *quantified semantic facade* (else
covered by existing end-user-prompt/metacognition work); RQ3 = extension/ablation (hardest to engineer).

## 2. Target Venue

- **Primary:** ACM **CHI** (target venue, not hard-locked). Full paper.
- **Fallbacks (framing-compatible):** IUI (★★★★), DIS (★★★, design-probe/critical route).
- **Explicitly excluded:** UIST.
- **Constraint:** Any venue change is a **human-approval** item (AGENTS.md §5) → Decision Log + re-run
  Novelty/Evidence Gate. CHI requires: theoretical framing (non-surjectivity / boundary object /
  epistemic calibration) + system + controlled study + qualitative design knowledge.

## 3. Contribution Type

Primary: **new interaction paradigm + system + empirical design knowledge** (HCI).
Secondary: **new empirical regularity** (quantified "semantic facade" / non-surjective gap as a
user-facing, measurable phenomenon). NOT a new steering method; NOT a new ML benchmark of steering.

## 4. Core Novelty (vs 3–5 nearest neighbors)

| Nearest neighbor | What they do | Our delta |
|---|---|---|
| AI-Instruments (Riche et al., CHI 2025) | Reify prompts as reusable direct-manipulation "instruments" (image gen). | We push control **down to latent**; use non-surjectivity to explain why prompt-layer instruments hit a language ceiling. |
| Huang & Lim (IASDR 2025) | Layperson feature-steering GUI (sliders build persona). | We treat the **prompt↔latent gap itself** as the interface object → conflict attribution + trust calibration, not a single latent channel. |
| SemanticLens (Labarta et al., 2026) | SAE attribution→action causal-verification loop. | Positioned for **expert debugging**; we serve non-experts' intent expression + mental-model repair. |
| Metacognitive Demands (Tankelevitch et al., CHI 2024) | Frames GenAI usability as metacognitive monitoring/control burden. | Provides our theory base; we operationalize + validate cognitive axes + latent legibility. |
| Mishra et al. (ICLR 2026 WS) | *Proves* steering is non-surjective vs prompt-reachable manifold. | Our **theoretical foundation** — legitimizes dual-channel + boundary exploration as an interaction problem. |

**One-sentence novelty (defensible):** We turn the *non-surjective gap* between prompt controllability
and latent mechanism into a legible, operable, calibratable interface object — producing an interaction
model + design knowledge for latent-controllability UIs, not another steering method or slider.

## 5. Falsifiable Claims (proposed — registered in claim-ledger.md)

- **C1 (semantic facade, RQ1):** For chosen cognitive axes, the strongest human-readable prompt's
  mid-layer activation projects onto the CAA vector direction *significantly below* vector-only
  (projection ≪ 100%). *Falsified if* strongest prompt reaches ≈ vector-only (no ceiling).
- **C2 (non-surjective control + conflict, RQ2):** On tasks with a compliance floor, prompt-only
  cannot cross a control threshold that the latent channel can; and the dual-channel + attribution
  panel lets non-experts correctly attribute & resolve prompt↔latent conflict better than prompt-only
  or steering-only baselines. *Falsified if* no task shows a prompt-unreachable region, OR the
  attribution panel yields no measurable attribution/trust-calibration gain.
- **C3 (boundary object, RQ3):** Metacognitive-axis levers preserve perceived control/continuity across
  a backend model swap better than prompt folklore. *Falsified if* users perceive equal/greater
  discontinuity with levers.

## 6. Non-Claims

- We do NOT claim a new steering/representation-engineering method.
- We do NOT claim prompt ≈ steering-vector equivalence/alignment (we claim the opposite — non-surjectivity).
- We do NOT claim causal identification of internal mechanisms beyond linear-probe/projection evidence.
- We do NOT claim generalization beyond the tested open white-box models (Llama-3-8B-Instruct,
  Qwen2.5-7B-Instruct) and the specific cognitive axes/tasks studied.
- We do NOT claim production deployment readiness or safety guarantees.

## 7. Minimum Publishable Evidence

- **Phase 0 pilot (data-level):** 3–4 stable cognitive axes; per-axis 30–50 contrast pairs; CAA vectors
  on ≥2 open models; quantified semantic-facade projection; blind-eval discriminability > chance;
  transferability + composability checks; conflict-probe behavioral landing points.
- **Formative (RQ1):** N≈12–16 non-expert knowledge workers; think-aloud + bottom-up axis naming.
- **Controlled study (RQ2, main):** within/mixed 3-condition (A prompt-only / B steering-only /
  C dual-channel console); measures: task quality (3rd-party/LLM-judge), lever-effect prediction
  accuracy, **calibrated trust**, perceived control, NASA-TLX, operation traces, pre/post mental-model.
- **Stats:** pre-registered primary metric, adequate seeds/participants, effect size + uncertainty,
  multiple-comparison control, fair baseline budgets, artifact-reconstructable main tables/figures.

## 8. Kill / Pivot Criteria

- **Semantic facade absent** (strongest prompt ≈ vector-only, C1 falsified) → Plan D: measurement/
  benchmark paper on the prompt-legibility gap.
- **Text–vector fully orthogonal** (no smooth dual-channel mapping) → Plan B: "prompt-engineering limit
  probe" — hard cutoff framing ("you've hit the semantic ceiling; switch to latent takeover").
- **Axis non-linear / multi-mechanism** → multi-layer/multi-vector decomposition; Plan C bottom-up
  axis induction from user study.
- **Steering changes only surface style, not reasoning** → report honestly as a finding; add
  reasoning-gain tasks (GSM8K/TruthfulQA).
- **3-condition study not significant** → Plan D measurement paper (legibility-gap benchmark + protocol).
- **Novelty covered** by concurrent work → human-approval pivot decision (continue/pivot/downgrade/terminate).

## 9. Budget (proposed caps — to be confirmed by human)

| Resource | Proposed cap | Notes |
|---|---|---|
| GPU hours | TBD (human sign-off before any L4 full run) | Local Windows; GPU for steering/interp is a §5 escalation item. |
| API / token cost (paid) | TBD (paid/private API = §5 escalation) | GPT-4o/Claude text-only baseline = closed-model control. |
| Calendar | ~16-week sprint (per 开题报告 §10) | Phase 0 first (2–3 wks, highest ROI, earliest risk exposure). |
| max_full_runs | TBD | L4 only after Protocol Freeze + Pre-Full-Run Review. |
| max_pivot_count | 2 before mandatory human review | Two same BLOCKERs across audit/critic rounds → escalate. |
| Human subjects | IRB/ethics = §5 escalation | Formative + controlled study need approval before recruiting. |

**Compute/paid/GPU/human-subjects items are NOT authorized by Manager — they require human approval.**

## 10. Open items to confirm with human (before freeze)

1. Budget caps (GPU hours, paid-API ceiling, max full runs).
2. Human-subjects approval path (Prolific recruiting, IRB status) — needed for Formative + controlled study.
3. Venue lock timing (keep CHI primary; confirm fallback ordering).
