# Spec · Phase 0 — RQ2/RQ1 Feasibility Pilot (data-level)

- **Spec ID**: phase0-pilot
- **Owner (author)**: Manager
- **Status**: DRAFT (execution GATED on human approval of GPU / paid-API — AGENTS.md §5)
- **Maps to**: Charter v0.2 §7 (Min Publishable Evidence, Phase 0), Claims C1 / C2a / C2b; Hypotheses H1/H2
- **Source design**: 开题报告 §6.1 + Charter-Review v0.2 fixes (manager-response.yaml)
- **Rule**: This is the NOVELTY-GATING experiment. Its results decide main-line vs Plan B vs Plan D (§8).
  It is data-level only — NO user study, NO system build in this phase.

---

## 1. Goal

Quantify whether the two channels can be *meaningfully coupled and contrasted* for users — NOT to verify
"prompt ≈ vector alignment" (the opposite of our thesis). Concretely, produce the pre-experiment evidence
that gates C1 (semantic facade), C2a (internal non-surjectivity check), and C2b (behavioral gap +
composability/transfer), on ≥2 open white-box models.

## 2. Acceptance Criteria (what "done" means for Phase 0)

- **AC1 (axes):** 3–4 cognitive axes selected (from Deliberation / Skepticism / Uncertainty-awareness /
  Focus), each with 30–50 validated contrast pairs (pos/neg).
- **AC2 (vectors):** CAA/RepE steering vector per axis extracted on Llama-3-8B-Instruct AND
  Qwen2.5-7B-Instruct, with a layer scan selecting the best injection layer; extraction reproducible from a
  fixed script + seed + data hash (experiment-registry entry).
- **AC3 (semantic facade, C1):** for each axis, projection of the strongest human-readable prompt's
  mid-layer activation onto the CAA direction, reported against (i) vector-only and (ii) a
  **random-direction null baseline**; the facade gap must be *large* (pre-registered effect-size
  threshold), not merely <100%.
- **AC4 (discriminability):** blind eval (human + LLM-judge) can identify the boosted axis above chance;
  multi-axis composition does not destroy fluency/usefulness.
- **AC5 (transfer/compose):** vectors transfer to held-out tasks and held-out phrasings; composition of
  ≥2 axes does not collapse (per Stolfo/Todd precedent).
- **AC6 (conflict probe, C2b seed):** prompt="high confidence" + slider="high skepticism" → record the
  behavioral landing point (which channel wins, how much), the empirical seed for RQ2 conflict interaction.
- **AC7 (style-vs-substance, R2-M2):** on a reasoning-gain task (GSM8K / TruthfulQA subset), report whether
  steering changes *correctness* or only *surface style* — reported honestly either way.
- **AC8 (bounded prompt-search ceiling, C2b):** using OPRO + human best-effort at a FIXED search budget,
  measure how far prompt-only can push each axis behaviorally vs vector-only — the ceiling evidence.
- **AC9 (registry + lineage):** every run has a unique experiment_id; every reported number is
  reconstructable from a committed script (no hand-copied numbers).

## 3. Quantitative Go/No-Go (novelty gate → routing)

- **Green (main line):** strongest-prompt projection significantly below vector-only AND above null
  (C1 holds); blind-eval > chance; transfer/compose survive; a behavioral prompt-search ceiling exists on
  ≥1 task (C2b seed). → build the coordination + conflict-resolution console.
- **Partial:** facade holds but no behavioral ceiling / composition fragile → Plan B (prompt-engineering
  limit probe: hard-cutoff framing).
- **Red:** strongest prompt ≈ vector-only (no facade) OR steering only changes surface style everywhere
  → Plan D (measurement/benchmark paper on the legibility gap).

## 4. Non-Goals (Phase 0)

- NO front-end / console build (that is Phase 2).
- NO human-subjects study (Formative/controlled study are later phases; need IRB).
- NO closed-model (GPT-4o/Claude) runs unless the paid-API ceiling is approved (§5).
- NO claim of a new steering method; CAA/RepE are used as-is.
- NO confirmatory labeling — Phase 0 is exploratory until Protocol Freeze.

## 5. Tooling (proposed, from 开题 §6.5)

- Vector extraction: `repeng`, IBM `activation-steering` (CAA), optionally `pyvene`.
- Probing/intervention: TransformerLens / nnsight.
- Models: Llama-3-8B-Instruct, Qwen2.5-7B-Instruct (local GPU).
- Eval sets: GSM8K, TruthfulQA, sycophancy probes, format/length/keyword (Stolfo-style) constraints.

## 6. Execution gating (what needs human sign-off before running)

| Sub-step | Compute class | Human approval needed? |
|---|---|---|
| Axis selection + contrast-pair authoring | L0/L1 (CPU) | No — prep-able now |
| Eval-set assembly + metric unit-tests + registry scaffolding | L0/L1 (CPU) | No — prep-able now |
| CAA vector extraction + layer scan | L2/L3 (GPU) | **YES — GPU allocation (§5)** |
| Projection / facade / discriminability / transfer / conflict / OPRO ceiling | L3 (GPU) | **YES — GPU (§5)** |
| Closed-model text baseline | paid API | **YES — paid-API ceiling (§5)** |

## 7. Deliverables

- Contrast-pair datasets (per axis) + eval-set manifests.
- Extraction + analysis scripts (reproducible, seeded) → experiment-registry entries.
- Phase 0 results table/figure with artifact manifests supporting C1 / C2a / C2b seeds.
- Go/No-Go routing memo → Manager decision (main / Plan B / Plan D) + Pre-Full-Run Review trigger.
