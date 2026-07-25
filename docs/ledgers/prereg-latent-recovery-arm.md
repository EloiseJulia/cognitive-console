# PREREG — Latent Recovery Arm (Workstream D) — FROZEN (Option 1)

> Status: **FROZEN 2026-07-24 (owner-approved, decision D-0041).** Owner selected **Option 1 (faithful PSR primary; manifold variant optional secondary only)** and authorized the **Qwen primary-arm GPU budget (~2.0–3.4 GPU-h, ~US$5–10)**; the conditional Llama confirmation arm is NOT yet authorized (revisit only if the Qwen primary shows signal). The frozen success/kill criteria, primary method, adjudicator reuse, and DEV/TEST discipline below are now IMMUTABLE for this arm. Implementation + run are authorized under the approved budget, but require the owner to physically provision (boot) the hourly-billed GPU box before any spend. This arm never edits or reinterprets the frozen records below.
>
> Purpose: add a new, stronger/principled latent-steering arm that directly answers the PSR / "Steer Like the LLM" ICML 2026 risk (open-risks #9): trained/optimized steering may match or exceed prompting behaviorally. This arm tests whether behavioral gain can be recovered on at least one axis where naive mean-difference CAA/ITI failed.
>
> Separation rule: this arm **never edits, reinterprets, or overwrites** E-0005, E-0006, E-0007, `docs/ledgers/prereg-c2b-adjudication.md`, `docs/ledgers/prereg-robustness-mechanism-arm.md`, or the frozen adjudicator math in `src/cognitive_console/experiments/adjudicate_c2b.py` §4. It only adds a new steering-vector-production step and new arm records.

---

## OWNER DECISION BOX (before freeze)

**PRE-RUN PARAMETER FREEZE (Manager D-0042, 2026-07-25, before any data):** `lambda_coh = 1.0` in the DEV objective `J` (previously unspecified numerically). Coherence is already a hard TEST pass gate (<=1.5x) in the frozen adjudicator, so this weight only shapes DEV candidate selection; frozen + fingerprinted before any TEST run.

**FROZEN DECISION (D-0041, owner-approved 2026-07-24): Option 1 selected** — faithful PSR primary; manifold variant optional secondary only. The table below is retained for the record.

| Option | Primary method | Claim-level consequence if it fails | Recommendation |
|---|---|---|---|
| **1** | **Faithful PSR-style DEV-optimized steering vector** (no explicit Mahalanobis/manifold penalty) | Cleanly upgrades C2 to **robust to method strength** within tested scope, because the strongest direct PSR-style threat was fairly tested. | **RECOMMENDED** |
| 2 | Fused PSR + manifold-constrained primary (old PSR-MC) | Failure is ambiguous: a reviewer can argue PSR was handicapped by the constraint, so C2 cannot fairly upgrade to robust-to-method-strength. | Not recommended |
| 3 | Faithful PSR primary + manifold-constrained secondary/ablation | Same primary verdict as Option 1; secondary manifold result has separate interpretation and cannot affect primary success/kill. | Acceptable if budget/engineering allow |

Short rationale: fusing PSR optimization with a manifold constraint undermines this arm's core value. The direct answer to open-risks #9 is a faithful behavior-optimized PSR-style vector. The original scientific motivation for a manifold penalty is also weak as a primary design choice because E-0007 already nulled the off-manifold distance-correlation mechanism. The natural-activation basis provides implicit regularization, while the frozen coherence gate guards degeneracy.

---

## 1. Mechanism hypothesis and primary method (pre-data)

### H-D (latent recovery under stronger/principled intervention)

The prior negative is method-specific in an important way: naive CAA/ITI directions are extracted from mean-difference or discriminative contrast geometry, not from the downstream behavioral objective. Therefore, CAA/ITI may be sub-optimal control coordinates even when a stronger trained/optimized intervention could recover behavioral control. A positive result would be consistent with PSR-style evidence that optimized steering can match/exceed prompting; a negative result would strengthen C2 by showing that the failure is robust even to method strength.

### PRIMARY method: **faithful PSR-style DEV-optimized steering vector**

This prereg chooses **one frozen primary method** to avoid method fishing: a faithful PSR-style behavior-optimized latent intervention. It learns the steering vector/configuration to maximize the behavioral objective on DEV, rather than using a mean-difference (CAA) or logistic-probe (ITI) direction.

Why this is principled and targets the known failure:

- **Direct engagement with PSR/open-risk #9:** the method optimizes the intervention for behavior, which is exactly the empirical threat raised by PSR-style trained steering.
- **Genuine strength increase over CAA/ITI:** the vector is parameterized in a basis that includes the CAA direction and ITI direction, so those nulled methods are recoverable special cases on DEV. The learned vector can rotate away from them only if DEV behavior supports it.
- **Implicit regularization without handicapping PSR:** the basis is built from natural/extraction activations, which constrains the search to a plausible residual subspace without adding an explicit Mahalanobis penalty that could be criticized as suppressing PSR's strength.
- **Degeneracy protection remains frozen and fair:** the unchanged coherence gate (`<= 1.5x`) prevents wins obtained by breaking the model; no extra primary manifold penalty is needed.

### Exact optimization plan

For each axis and model, before touching TEST:

- **Data allowed for optimization:** only the frozen DEV split from the C2b adjudicator for that axis, plus existing extraction/contrast activations needed to define the activation basis. TEST items and TEST generations are never used for vector training, hyperparameter selection, prompt selection, layer selection, or early stopping.
- **Layer/token schedule:** use the already documented non-degenerate layer-selection machinery from the existing CAA/ITI extraction path. Candidate layers and the final layer/schedule must be selected on extraction/DEV diagnostics only. If scheduling is implemented, it remains part of the single primary method: fixed local support `{L-1, L, L+1}` with non-negative weights constrained to sum to 1, selected on DEV only; it is not a separate fishing knob.
- **Parameterization:** learn a single unit direction per axis/model in a fixed low-dimensional natural-activation basis: `{CAA direction, ITI direction, top-r PCA directions of natural/extraction activations}`. **Recommended frozen default: `r=16`.** Cheaper fallback: `r=8`, which lowers engineering/optimization cost but weakens the fairness of the PSR-strength test and should be recorded as a scope limitation if chosen.
- **Objective optimized on DEV only:** maximize absolute DEV behavioral outcome under the same task outcomes as the frozen adjudicator, with the frozen coherence penalty only. The vector is **not** trained to beat a specific DEV-selected prompt, avoiding overfit to one prompt's idiosyncrasies. A concrete objective is:

  `J(theta, alpha) = mean_DEV(outcome_steer(theta, alpha)) - lambda_coh * max(0, coherence_ratio - 1.5)`

  where `lambda_coh` is fixed before any run. The steer-vs-prompt paired comparison is performed only later by the frozen TEST adjudicator.
- **Optimizer budget:** recommended frozen cap **`<= 32` DEV candidate evaluations per axis**. Candidate evaluation includes vector coefficients, fixed-grid alpha choice, and optional `{L-1,L,L+1}` schedule weights. The optimizer seed and candidate generator must be frozen and fingerprinted.
- **Hyperparameter/strength selection:** choose vector coefficients and optional local schedule weights only by DEV objective. The final adjudicated strength must come from the frozen alpha grid `{2,4,6,8,12,16,24}` via the unchanged DEV selection path; no continuous strength tuning or TEST-time strength adjustment is allowed. The final TEST run receives exactly one frozen vector/config/alpha per axis.
- **TEST use:** after DEV selection is frozen, run the unchanged adjudicator on TEST once per cell. No TEST-driven adjustment, reranking, alpha change, axis subset, or mechanism re-mining is allowed.

---

## 2. Optional secondary manifold variant (not part of primary verdict)

A manifold-constrained/projected variant may be run only as an **OPTIONAL SECONDARY / ablation** or future-work item. It is **not required**, does **not** count toward the frozen primary success or kill verdict, and has its own separate interpretation: it asks whether an extra natural-manifold constraint changes behavior after the faithful PSR primary has already adjudicated the method-strength threat. It must explicitly **not** reinterpret, retest, or revive E-0007; E-0007 remains a valid null for the off-manifold distance-correlation mechanism.

---

## 3. Frozen adjudicator reuse (byte-identical decision math)

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

**Implementation constraint:** `src/cognitive_console/experiments/adjudicate_c2b.py` §4 must remain byte-identical. The only permitted change for this arm is upstream production of the PSR steering direction/config passed into generation. The run may add wrapper scripts, metadata, config fingerprints, and completeness/provenance checks, but it must not alter the frozen decision math.

---

## 4. Frozen success and kill criteria (pre-data)

If the owner freezes this prereg, the following criteria become immutable for the **primary faithful-PSR method only**.

### Success criterion — latent recovery

**At least one axis significantly beats the frozen best prompt under the frozen adjudicator and passes the coherence gate.** Formally, in any authorized primary PSR cell, an axis passes iff the unchanged per-axis rule reports a pass: paired TEST mean difference `steer - prompt` has Bonferroni-corrected `98.33%` CI excluding 0, point estimate `>= 0.05`, and coherence ratio within the frozen gate.

Interpretation of success is intentionally asymmetric and scope-narrowed:

- any-axis success becomes a **scope-narrowed POSITIVE secondary contribution**: behavioral controllability is recoverable under faithful PSR-style optimized steering for `{model, axis}`;
- this is **consistent with PSR** and directly addresses open-risks #9;
- it **never overwrites** E-0005/E-0006. Those remain valid negatives for naive CAA/ITI under their frozen protocols;
- if Qwen succeeds and the Llama confirmation does not run or does not pass, the positive is Qwen-scoped rather than generalized.

### Kill criterion — robust-to-method-strength negative

If all authorized primary faithful-PSR axes fail under the frozen adjudicator, with valid runs and no instrument invalidation, then C2's negative upgrades to a stronger version:

> Legible-direction steering fails across naive CAA/ITI and a faithful PSR-style DEV-optimized steering vector; the behavioral non-transfer result is robust to method strength under the tested budget/model scope.

This all-fail outcome is more general than E-0006, but still honest about scope: it does not prove absolute impossibility of all future steering methods, larger models, larger training budgets, non-residual interventions, or private/closed-model interventions.

### Invalid-cell rule

A cell with generation stall, incomplete TEST coverage, corrupted provenance, extraction collapse, or coherence degeneracy across all selectable strengths is marked **INVALID**, not positive or negative. INVALID cells must be rerun under the same frozen config or reported as unresolved; they cannot be counted toward success or kill.

---

## 5. Smallest decisive model/cell design

### Primary design (owner approval required before GPU)

- **Model:** Qwen2.5-7B-Instruct first.
- **Method:** faithful PSR-style DEV-optimized steering vector only (`steering_method = psr`).
- **Axes:** all three frozen axes: deliberation, skepticism, uncertainty_awareness.
- **Cell count:** one full frozen cell = 11,365 adjudication generations after DEV vector/config selection.

Justification: Qwen2.5-7B is the exact model for E-0005 and one cell of E-0006, so it is the cleanest counterfactual against the original CAA failure. One primary method avoids method fishing; all three axes preserve the frozen adjudicator and allow recovery on the axis where the method truly helps.

### Conditional confirmation

If the Qwen primary cell has at least one passing axis, run **one matching confirmation cell** on Llama-3-8B-Instruct / NousResearch identical-weights mirror, with the same faithful-PSR protocol and frozen adjudicator. This confirmation is **mandatory for any GENERALIZED positive wording** across model families, but optional for a Qwen-scoped positive. If Llama is not run or does not pass, the positive remains Qwen-scoped.

### No automatic expansion

No second optimizer family, larger model, expanded alpha grid, new axis, post-hoc mechanism probe, optional manifold ablation, or extra confirmation run is allowed without a new prereg/owner decision.

---

## 6. GPU budget estimate and provisioning gate

Known baseline from prior arm: each frozen adjudication cell requires **11,365 generations**; the 2x2 robustness arm ran on a rented RTX4080S-class box. Prior prereg estimated about **~29 min generation + ~4 min load per cell**, with full 4-cell GPU session around **4-6 hours** including downloads/diagnostics.

### Primary Qwen faithful-PSR cell

- Frozen adjudication: `1 * 11,365 = 11,365` generations, roughly **0.55-0.8 GPU-hours** including model load/checkpoint overhead on RTX4080S/4090-class hardware.
- DEV optimization overhead: recommended cap `<= 32` candidate vector/config evaluations per axis on DEV only. DEV item counts are approximately 20/20/27, `k=5`, so a full DEV candidate pass is about `100 + 100 + 135 = 335` generations. `32 * 335 = 10,720` additional DEV generations, roughly **0.5-0.8 GPU-hours**.
- Activation extraction/PCA basis overhead: model forward passes only; estimate **0.1-0.3 GPU-hours**. No Mahalanobis/manifold penalty machinery is part of the primary.
- Re-provision/download/smoke/checkpoint overhead because the box is currently wiped: estimate **0.8-1.5 GPU-hours**.

**Primary total:** approximately **2.0-3.4 GPU-hours**, assuming one RTX4080S/4090-class hourly-billed box and no driver stalls.

### Conditional Llama confirmation (only if Qwen shows signal)

- Same adjudication + DEV optimization order of magnitude: **1.1-2.0 GPU-hours** incremental if model is already provisioned; **1.9-3.0 GPU-hours** if Llama download/setup is cold.

### Dollar estimate

Hourly-billed RTX4080S/4090 spot/on-demand pricing varies. Using an explicit assumption of **US$0.50-1.00/hour** (roughly low single-digit RMB/hour to ~7 RMB/hour):

- Primary Qwen only: **~2.0-3.4 h = US$1-4** compute, plus cushion for failed provisioning; conservatively budget **US$5-10**.
- Primary + conditional Llama confirmation: **~3.9-6.4 h = US$2-7** compute; conservatively budget **US$10-20**.

These estimates exclude AI-agent/engineering credits. Any GPU provisioning is owner-gated because the current rented box is wiped and must be re-provisioned on an hourly-billed machine.

---

## 7. Completeness, provenance, and recurring-bug guard

The runner/aggregation for this arm must be hardened before any run:

- validate **complete coverage** for every required axis, split, item, `k=5` sample, selected alpha/config, and TEST paired comparison;
- refuse verdict aggregation from counts or file existence alone;
- include `steering_method = psr` and the full optimization config in both `config_fingerprint` and the minted `experiment_id`/registry metadata: basis definition, PCA rank, layer/schedule, optimizer seed, candidate budget, objective/coherence weight, alpha/strength, selected DEV score, model id, backend, batch size, seed, item ids, and prompt optimizer state if enabled;
- verify that existing checkpoints/transcripts are reusable only when the full fingerprint matches;
- emit raw transcripts and per-item outcomes so a hostile audit can recompute the exact frozen adjudicator verdict;
- make aggregation fail closed if a method/model/fingerprint mismatch is detected.

This guard is required because E-0006's audit found a lineage weakness: same-model experiment IDs could collide across steering methods even though result JSON recorded the method. Workstream D must not allow fabricated or stale verdicts from counts/file-presence shortcuts.

---

## 8. Honest-fail and frozen-record separation

- **No re-mining:** if faithful PSR fails, do not search for a different mechanism, post-hoc axis subset, alternate confidence parser, alternate bootstrap, manifold-constrained rescue, or new off-manifold statistic on the same data.
- **No reinterpretation of E-0007:** E-0007 remains a valid null for the distance-correlation mechanism. Any optional manifold ablation is a separate design ablation, not evidence that distance caused calibration harm.
- **No frozen-record edits:** E-0005/E-0006/E-0007 and the frozen adjudicator remain intact regardless of this arm's outcome.
- **No TEST tuning:** any TEST-informed change creates a new exploratory record and cannot support the frozen success criterion.
- **Owner gate:** this prereg remains inert until Manager review and owner sign-off for protocol freeze and GPU spend.
