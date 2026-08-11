# Hypothesis Ledger

> Per AI-Instruction Part I §4.1. Each run records: hypothesis_id, experiment_type
> (confirmatory/exploratory/diagnostic), decision_before_run, expected_outcome, success_criterion,
> failure_interpretation, positive/negative next action, protocol_frozen.

Status: registered | testing | supported | refuted | parked

---

## H1 (→ C1) — Semantic facade exists
- experiment_type: exploratory (Phase 0) → confirmatory after freeze
- expected_outcome: strongest-prompt projection onto CAA direction significantly < vector-only
- success_criterion: statistically significant gap, ≥2 models, ≥3 axes
- failure_interpretation: if ≈ vector-only → no ceiling → Plan D (measurement paper)
- protocol_frozen: NO
- status: partially-supported → **STRENGTHENED @7B (E-0003: 3/4 axes facade CI<1, seed-stable)**;
  EXPLORATORY (single model family Qwen2.5, valid_for_paper=false). The facade/ceiling side of the thesis
  holds; ≥2-model replication still owed for confirmatory.

## H2 (→ C2) — Prompt-unreachable region + conflict legibility
- experiment_type: exploratory (Phase 0 conflict probe) → confirmatory (controlled study)
- expected_outcome: compliance-floor task where prompt-only cannot cross threshold; panel improves
  conflict attribution & trust calibration
- success_criterion: prompt-unreachable region demonstrated AND condition C > A/B on attribution/trust
  with effect size + uncertainty
- failure_interpretation: no unreachable region → Plan B; panel no gain → downgrade RQ2 claim
- protocol_frozen: YES (behavioral-reachability sub-claim; prereg-c2b-adjudication.md, FROZEN 2026-07-23)
- status: **REFUTED-GENERALIZED (E-0005 + E-0006, D-0034/D-0039): frozen adjudication 0/3 axes across
  {CAA,ITI}×{Qwen,Llama} = all 4 cells KILL → arm NON_TRANSFER_GENERALIZED.** Latent steering does NOT reach
  behavior beyond the best-prompt ceiling on ANY method×model; hurts calibration in all 4 cells. Audited
  VALID (VALID_NEGATIVE + VALID_ARM_EVIDENCE). Reading: "prompt = strong ceiling / legibility ≠ controllability"
  holds ROBUSTLY across methods+models — no longer a single-method×single-model artifact. RQ2 confirmatory bet
  dropped → reality-check reframe (D-0035). Off-manifold mechanism (C2-mech) under pre-registered OOD test
  (prereg-ood-capture.md).

## H3 (→ C3) — Levers as boundary object across model swap
- experiment_type: exploratory / extension
- expected_outcome: lever function preserved Llama-3 → Qwen-2.5; less perceived discontinuity vs prompt
- success_criterion: lower perceived-discontinuity vs prompt folklore
- failure_interpretation: report as negative/limitation; keep as ablation
- protocol_frozen: NO
- status: registered

## H4 (→ C2 construct validation) — Incremental prompt-plus-steer value
- experiment_type: confirmatory construct validation after hostile pre-run audit
- expected_outcome: no directional result assumed; estimate whether adding the same DEV-selected bounded
  Qwen CAA steer to the DEV-selected bounded prompt improves the intended outcome.
- primary_estimand: per-axis `prompt+steer - prompt`; secondary factorial interaction =
  `(prompt+steer - prompt) - (steer - neutral)`. Interaction cannot establish utility when the primary fails.
- success_criterion: Bonferroni 98.33% item-cluster bootstrap CI lower bound > 0, point estimate ≥ 0.05,
  both-context coherence, and measurement eligibility.
- failure_interpretation: an adequately powered valid no-pass supports only a scoped no-qualifying-increment
  statement; underpowered/ineligible/invalid axes remain unresolved. The original substitution 0/12 is unchanged.
- novelty_boundary: Bo et al. already studied prompting on top of activation steering; H4 is construct
  validation, not a first-composition or composition-method novelty claim.
- historical_exposure: historical E-0012 artifacts had been inspected before H4 implementation, but E-0012
  is invalidated lineage and supplies no evidence, prior, item selection, direction, or claim support here.
- measurement_rule: shared strict parser; uncertainty requires explicit answer+confidence, skepticism an
  explicit valid option cue; missing fields score 0 and remain recorded.
- protocol_frozen: **YES — `docs/research/2026-08-11-prereg-prompt-steer-composition-FROZEN.md`; real TEST
  remains authorization-locked pending hostile audit and budget approval.**
- status: registered; no real DEV/TEST data and no evidence-ledger entry yet.
