# PREREG — Latent Recovery Arm (Workstream D) — DRAFT / INERT

> Status: **DRAFT — NOT FROZEN, NOT AUTHORIZED TO RUN.** This document is an independent proposed pre-registration for Manager review and owner sign-off. It is **inert** until the owner explicitly approves (AGENTS.md §5) both protocol freeze and any hourly-billed GPU spend. No experiment, GPU provisioning, TEST generation, or frozen-record edit is authorized by this draft.
>
> Purpose: add a new, stronger/principled latent-steering arm that directly answers the PSR / "Steer Like the LLM" ICML 2026 risk (open-risks #9): trained/optimized steering may match or exceed prompting behaviorally. This arm tests whether behavioral gain can be recovered on at least one axis where naive mean-difference CAA/ITI failed.
>
> Separation rule: this arm **never edits, reinterprets, or overwrites** E-0005, E-0006, E-0007, `docs/ledgers/prereg-c2b-adjudication.md`, `docs/ledgers/prereg-robustness-mechanism-arm.md`, or the frozen adjudicator math in `src/cognitive_console/experiments/adjudicate_c2b.py` §4. It only adds a new steering-vector-production step and new arm records.

---

## 1. Mechanism hypothesis and selected method (pre-data)

### H-D (latent recovery under stronger/principled intervention)

The prior negative is method-specific in an important way: naive CAA/ITI directions are extracted from mean-difference or discriminative contrast geometry, not from the downstream behavioral objective. Therefore, CAA/ITI may be sub-optimal control coordinates even when a stronger trained/optimized intervention could recover behavioral control. A positive result would be consistent with PSR-style evidence that optimized steering can match/exceed prompting; a negative result would strengthen C2 by showing that the failure is robust even to method strength.

### Chosen method: **PSR-MC — DEV-optimized, manifold-constrained steering**

This prereg chooses **one** method to avoid method fishing. PSR-MC combines the two principled ideas that are relevant to the known failure mode:

1. **PSR-style optimized/trained steering vector.** Instead of using `mean(pos) - mean(neg)` (CAA) or a logistic probe direction (ITI), learn the intervention to maximize the frozen behavioral objective on DEV. This is the direct response to open-risks #9: if PSR's threat is real for this setting, a behavior-optimized latent intervention is the arm most likely to reveal it.
2. **Manifold-constrained / projected intervention.** The learned direction is constrained to a natural activation subspace/ellipsoid estimated from DEV/extraction activations. This is an intervention-design constraint, not a re-mining of the E-0007 mechanism. E-0007 already returned a valid null for the *distance-correlation explanation* of calibration harm; PSR-MC does **not** retest or reinterpret that nulled mechanism. It simply avoids unconstrained off-distribution residual additions as a conservative design choice, motivated by the observed calibration harm.

### Exact optimization/constraining plan

For each axis and model, before touching TEST:

- **Data allowed for optimization:** only the frozen DEV split from the C2b adjudicator for that axis, plus existing extraction/contrast activations needed to define the activation basis and covariance. TEST items and TEST generations are never used for vector training, hyperparameter selection, prompt selection, layer selection, or early stopping.
- **Layer:** use the already documented non-degenerate layer-selection machinery from the existing CAA/ITI extraction path. Candidate layers and the final layer must be selected on extraction/DEV diagnostics only. If layer/token scheduling is implemented, it is part of PSR-MC, not a separate method: a fixed 3-layer local schedule `{L-1, L, L+1}` with non-negative weights constrained to sum to 1, selected on DEV only; no additional layer search on TEST.
- **Parameterization:** learn a single unit direction per axis/model in a fixed low-dimensional residual basis: `{CAA direction, ITI direction, top PCA directions of natural/extraction activations}`. The PCA basis size is fixed before running (recommended `r=16`; Manager may lower for engineering cost before freeze). This is principled because it lets the behavior objective rotate away from naive CAA/ITI while keeping the search in a natural activation subspace.
- **Objective optimized on DEV only:** maximize DEV mean paired behavioral difference against the DEV-selected best prompt under the same task outcomes as the frozen adjudicator, with penalties for coherence-gate violations and for leaving the natural activation ellipsoid. A concrete objective is:

  `J(theta, alpha) = mean_DEV(outcome_steer(theta, alpha) - outcome_best_prompt) - lambda_coh * max(0, coherence_ratio - 1.5) - lambda_manifold * max(0, mahalanobis(theta) - tau)`

  where `tau` is a precomputed natural-activation ellipsoid threshold (e.g., 95th percentile on DEV/extraction activations) and `lambda_*` are fixed before any run. The objective is evaluated only on DEV.
- **Hyperparameter selection:** choose vector coefficients and optional local schedule weights only by DEV objective. The final adjudicated strength must come from the frozen alpha grid `{2,4,6,8,12,16,24}` via the unchanged DEV selection path; no continuous strength tuning or TEST-time strength adjustment is allowed. The final TEST run receives exactly one frozen vector/config/alpha per axis.
- **TEST use:** after DEV selection is frozen, run the unchanged adjudicator on TEST once per cell. No TEST-driven adjustment, reranking, alpha change, axis subset, or mechanism re-mining is allowed.

---

## 2. Frozen adjudicator reuse (byte-identical decision math)

The adjudicator is reused **exactly** as in the frozen C2b preregistration:

- same outcomes: deliberation accuracy, skepticism false-premise-rejection rate, uncertainty `1 - Brier`;
- same DEV/TEST split protocol, with DEV for selection and TEST for adjudication;
- same N per axis: deliberation `N=60`, skepticism `N=60`, uncertainty `N=80`;
- same `k=5` samples per item;
- same paired item-cluster bootstrap with `B >= 10000`;
- same Bonferroni two-sided CI level `1 - 0.05/3 = 0.98333...`;
- same meaningful margin `delta = 0.05`;
- same coherence gate: steered degeneracy/repetition score must be `<= 1.5x` unsteered baseline;
- same per-axis pass condition: corrected CI excludes 0, point estimate `>= delta`, and coherence gate passes;
- same three-tier verdict inside a cell: `STRONG_GO`, `CONDITIONAL_GO`, `KILL_PLAN_D`.

**Implementation constraint:** `src/cognitive_console/experiments/adjudicate_c2b.py` §4 must remain byte-identical. The only permitted change for this arm is upstream production of the steered direction/config passed into generation. The run may add wrapper scripts, metadata, config fingerprints, and completeness/provenance checks, but it must not alter the frozen decision math.

---

## 3. Frozen success and kill criteria (pre-data)

If the owner freezes this prereg, the following criteria become immutable for this arm.

### Success criterion — latent recovery

**At least one axis significantly beats the frozen best prompt under the frozen adjudicator and passes the coherence gate.** Formally, in any authorized PSR-MC cell, an axis passes iff the unchanged per-axis rule reports a pass: paired TEST mean difference `steer - prompt` has Bonferroni-corrected `98.33%` CI excluding 0, point estimate `>= 0.05`, and coherence ratio within the frozen gate.

Interpretation of success is intentionally asymmetric and scope-narrowed:

- any-axis success becomes a **scope-narrowed POSITIVE secondary contribution**: behavioral controllability is recoverable under a trained/manifold-constrained method for `{method, model, axis}`;
- this is **consistent with PSR** and directly addresses open-risks #9;
- it **never overwrites** E-0005/E-0006. Those remain valid negatives for naive CAA/ITI under their frozen protocols;
- if Qwen succeeds and the Llama confirmation does not, the positive is model-scoped rather than generalized.

### Kill criterion — robust-to-method-strength negative

If all authorized primary PSR-MC axes fail under the frozen adjudicator, with valid runs and no instrument invalidation, then C2's negative upgrades to a stronger version:

> Legible-direction steering fails across naive CAA/ITI and a stronger DEV-optimized, manifold-constrained steering method; the behavioral non-transfer result is robust to method strength under the tested budget/model scope.

This all-fail outcome is more general than E-0006, but still honest about scope: it does not prove absolute impossibility of all future steering methods, larger models, larger training budgets, or non-residual interventions.

### Invalid-cell rule

A cell with generation stall, incomplete TEST coverage, corrupted provenance, extraction collapse, or coherence degeneracy across all selectable strengths is marked **INVALID**, not positive or negative. INVALID cells must be rerun under the same frozen config or reported as unresolved; they cannot be counted toward success or kill.

---

## 4. Smallest decisive model/cell design

### Primary design (owner approval required before GPU)

- **Model:** Qwen2.5-7B-Instruct first.
- **Method:** PSR-MC only.
- **Axes:** all three frozen axes: deliberation, skepticism, uncertainty_awareness.
- **Cell count:** one full frozen cell = 11,365 adjudication generations after DEV vector/config selection.

Justification: Qwen2.5-7B is the exact model for E-0005 and one cell of E-0006, so it is the cleanest counterfactual against the original CAA failure. One method avoids method fishing; all three axes preserve the frozen adjudicator and allow recovery on the axis where the method truly helps.

### Conditional confirmation

If the Qwen primary cell has at least one passing axis, run **one matching confirmation cell** on Llama-3-8B-Instruct / NousResearch identical-weights mirror, with the same PSR-MC protocol and frozen adjudicator. This confirmation tests whether recovery is model-family-specific or broader. It is not required to preserve the Qwen-scoped positive, but it is required before writing a generalized recovery claim.

### No automatic expansion

No second optimizer family, larger model, expanded alpha grid, new axis, post-hoc mechanism probe, or extra confirmation run is allowed without a new prereg/owner decision.

---

## 5. GPU budget estimate and provisioning gate

Known baseline from prior arm: each frozen adjudication cell requires **11,365 generations**; the 2x2 robustness arm ran on a rented RTX4080S-class box. Prior prereg estimated about **~29 min generation + ~4 min load per cell**, with full 4-cell GPU session around **4-6 hours** including downloads/diagnostics.

### Primary Qwen PSR-MC cell

- Frozen adjudication: `1 * 11,365 = 11,365` generations, roughly **0.55-0.8 GPU-hours** including model load/checkpoint overhead on RTX4080S/4090-class hardware.
- DEV optimization overhead: proposed cap `<= 32` candidate vector/config evaluations per axis on DEV only. DEV item counts are approximately 20/20/27, `k=5`, so a full DEV candidate pass is about `100 + 100 + 135 = 335` generations. `32 * 335 = 10,720` additional DEV generations, roughly **0.5-0.8 GPU-hours**.
- Activation extraction/PCA/covariance overhead: model forward passes only; estimate **0.2-0.5 GPU-hours**.
- Re-provision/download/smoke/checkpoint overhead because the box is currently wiped: estimate **0.8-1.5 GPU-hours**.

**Primary total:** approximately **2.1-3.6 GPU-hours**, assuming one RTX4080S/4090-class hourly-billed box and no driver stalls.

### Conditional Llama confirmation (only if Qwen shows signal)

- Same adjudication + DEV optimization order of magnitude: **1.2-2.1 GPU-hours** incremental if model is already provisioned; **2.0-3.2 GPU-hours** if Llama download/setup is cold.

### Dollar estimate

Hourly-billed RTX4080S/4090 spot/on-demand pricing varies. Using an explicit assumption of **US$0.50-1.00/hour** (roughly low single-digit RMB/hour to ~7 RMB/hour):

- Primary Qwen only: **~2.1-3.6 h = US$1-4** compute, plus cushion for failed provisioning; conservatively budget **US$5-10**.
- Primary + conditional Llama confirmation: **~4.1-6.8 h = US$2-7** compute; conservatively budget **US$10-20**.

These estimates exclude AI-agent/engineering credits. Any GPU provisioning is owner-gated because the current rented box is wiped and must be re-provisioned on an hourly-billed machine.

---

## 6. Completeness, provenance, and recurring-bug guard

The runner/aggregation for this arm must be hardened before any run:

- validate **complete coverage** for every required axis, split, item, `k=5` sample, selected alpha/config, and TEST paired comparison;
- refuse verdict aggregation from counts or file existence alone;
- include `steering_method = psr_mc` and the full optimization config in both `config_fingerprint` and the minted `experiment_id`/registry metadata: basis definition, PCA rank, covariance source, layer/schedule, optimizer seed, candidate budget, objective weights, alpha/strength, selected DEV score, coherence penalty, manifold threshold, model id, backend, batch size, seed, item ids, and prompt optimizer state if enabled;
- verify that existing checkpoints/transcripts are reusable only when the full fingerprint matches;
- emit raw transcripts and per-item outcomes so a hostile audit can recompute the exact frozen adjudicator verdict;
- make aggregation fail closed if a method/model/fingerprint mismatch is detected.

This guard is required because E-0006's audit found a lineage weakness: same-model experiment IDs could collide across steering methods even though result JSON recorded the method. Workstream D must not allow fabricated or stale verdicts from counts/file-presence shortcuts.

---

## 7. Honest-fail and frozen-record separation

- **No re-mining:** if PSR-MC fails, do not search for a different mechanism, post-hoc axis subset, alternate confidence parser, alternate bootstrap, or new off-manifold statistic on the same data.
- **No reinterpretation of E-0007:** E-0007 remains a valid null for the distance-correlation mechanism. PSR-MC's manifold constraint is a design choice, not evidence that distance caused calibration harm.
- **No frozen-record edits:** E-0005/E-0006/E-0007 and the frozen adjudicator remain intact regardless of this arm's outcome.
- **No TEST tuning:** any TEST-informed change creates a new exploratory record and cannot support the frozen success criterion.
- **Owner gate:** this prereg remains inert until Manager review and owner sign-off for protocol freeze and GPU spend.

---

## 8. Open design questions for Manager before owner sign-off

1. Freeze PSR-MC as the only method, or split it into two separate methods (PSR-optimized unconstrained vs manifold-constrained PSR) with an explicit multiplicity/interpretation plan?
2. Freeze PCA basis rank (`r=16` recommended) and optimizer budget (`32` candidates/axis recommended), or lower them for cost/overfit control?
3. Should Llama confirmation be mandatory for any paper-visible positive, or only for generalized positive wording?
4. Should the PSR-MC objective optimize against the DEV-selected best prompt directly, or optimize absolute DEV outcome with the prompt ceiling used only by the frozen TEST adjudicator?
5. What exact manifold threshold (`tau`, e.g., 95th percentile) and penalty weights should be frozen before implementation?

