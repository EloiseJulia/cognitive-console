# Plan · Phase 0 — Feasibility Pilot execution

- **Plan ID**: phase0-pilot-plan
- **Spec**: docs/specs/phase0-pilot.md
- **Status**: DRAFT (only the CPU/prep slices are runnable now; GPU/API slices GATED on human §5 approval)
- **Author**: Manager

> Slices marked [GPU] or [API] are BLOCKED until the human approves GPU hours / paid-API ceiling.
> Slices marked [PREP] are data-level, CPU-only, and can proceed now without spend.

## Slice dependency graph

```
S1 axis-selection [PREP] ─┬─> S2 contrast-pairs [PREP] ─┐
S3 eval-sets [PREP] ──────┘                             │
S4 registry+metric-tests [PREP] ────────────────────────┼─> S5 vector-extraction [GPU] ─┐
                                                          │                               │
                                                          └───────────────────────────────┼─> S6 facade+null [GPU]
                                                                                          ├─> S7 discriminability/transfer/compose [GPU]
                                                                                          ├─> S8 conflict-probe [GPU]
                                                                                          ├─> S9 style-vs-substance reasoning task [GPU]
                                                                                          └─> S10 OPRO bounded-search ceiling [GPU/API]
                                                                                                    │
                                                                                                    └─> S11 Go/No-Go routing memo → Manager decision
```

Parallelism: S1–S4 are independent PREP slices (parallel, separate worktrees). S5 depends on S1/S2/S3/S4.
S6–S10 depend on S5 and are mostly parallel (share the extracted vectors). S11 aggregates.

## Slices

| id | title | class | depends_on | acceptance | approval |
|---|---|---|---|---|---|
| S1 | Select 3–4 cognitive axes (top-down + note bottom-up risk) | PREP | — | AC1 (axes fixed) | none |
| S2 | Author 30–50 contrast pairs/axis (pos/neg), reviewed | PREP | S1 | AC1 (pairs) | none |
| S3 | Assemble eval sets (GSM8K/TruthfulQA/sycophancy/format) + manifests | PREP | — | AC7 sets ready | none |
| S4 | Experiment-registry scaffolding + metric unit-tests + leakage checks (L0) | PREP | — | AC9 | none |
| S5 | Extract CAA vectors + layer scan, ≥2 models, seeded/reproducible | GPU | S1–S4 | AC2 | **human GPU** |
| S6 | Facade projection vs vector-only vs random null; effect-size | GPU | S5 | AC3 | **human GPU** |
| S7 | Blind-eval discriminability + transfer + composition | GPU | S5 | AC4/AC5 | **human GPU** |
| S8 | Conflict probe (prompt vs slider) behavioral landing | GPU | S5 | AC6 | **human GPU** |
| S9 | Style-vs-substance on reasoning-gain task | GPU | S5 | AC7 | **human GPU** |
| S10 | OPRO + human bounded prompt-search ceiling | GPU/API | S5 | AC8 | **human GPU/API** |
| S11 | Go/No-Go routing memo → main / Plan B / Plan D | analysis | S6–S10 | §3 routing | none (Manager) |

## Immediate next actions (no spend)

1. Manager dispatches S1–S4 as PREP implement subagents (separate worktrees) — but ONLY after the owed
   prior-art sweep returns and Charter Freeze re-review passes (avoid building on an un-frozen protocol).
2. Before any GPU slice (S5+): obtain human GPU-hours approval, then Pre-Full-Run Review (R1/R2/R3) on the
   frozen Phase-0 protocol (Charter §gates: no L4 without protocol freeze + fair-baseline + leakage check).

## Open protocol questions to resolve before freeze (for Pre-Full-Run Review)

- Exact effect-size threshold for the facade gap (C1) and the behavioral-ceiling threshold (C2b).
- Fixed OPRO search budget (defines "bounded" prompt search fairly).
- Which mid-layer(s) to report projection at; layer-scan selection rule.
- Blind-eval judge protocol + inter-rater / LLM-judge fairness.
