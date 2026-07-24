# PREREG — OOD Activation-Capture for H-M (off-manifold) — **FROZEN 2026-07-24**

> Status: **FROZEN 2026-07-24 (before capture)** (owner directive 2026-07-24: pre-register BEFORE capture, do not
> let the billing box pressure sloppiness; allow the hypothesis to FAIL honestly). This is a NEW independent
> pre-registration sub-item of the frozen robustness arm (prereg-robustness-mechanism-arm.md §H-M). It ADDS a
> mechanism diagnostic; it does NOT touch E-0003 / E-0005 / prereg-c2b-adjudication.md, nor the already-banked
> 2×2 H-R result (arm_full, E-0006).

## 0. Goal
Test H-M: is the calibration harm (uncertainty axis, negative in all 4 cells) explained by steering pushing
activations OFF the natural data manifold? Upgrade C2-mech from hypothesis to evidence, OR — if unsupported —
**honestly demote C2-mech to an explicit hypothesis / Future Work; do NOT concoct a different mechanism story
on the same data.**

## 1. FROZEN design (pin down BEFORE looking at any distance-vs-outcome relationship)

- **Unit of analysis:** per (cell, item). Cells = the frozen 2×2 {CAA,ITI}×{Qwen2.5-7B, Llama-3-8B (NousResearch
  identical-weights mirror)}. Reuse the SAME frozen items/seed (20260723), SAME per-model re-derived steered
  layer L and frozen α as the banked arm_full cells (read from each cell's results JSON — NOT re-chosen).
- **Reference distribution (FROZEN):** the **same-layer (L) un-intervened (baseline / no-steer) residual
  activations** of the model on the axis items — i.e. the natural on-manifold distribution at layer L. Estimated
  as mean + covariance (with numerically-stable shrinkage) from the un-intervened forward pass over the SAME
  items (baseline channel). NO steered activations enter the reference estimate (self-fit forbidden; enforced by
  the ood.py provenance guardrail: reference_split_id != evaluated_split_id).
- **Distance metric (FROZEN — pick exactly ONE):** **whitened Mahalanobis distance** of the steered residual at
  layer L to the reference distribution above. (This is the single pre-committed metric; kNN / density-logL are
  NOT used, to avoid metric-shopping.) Secondary descriptive only (NOT part of the verdict): activation-norm
  inflation ratio.
- **Per-item outcome delta (FROZEN):** the per-item calibration Δoutcome = (steered − baseline) 1−Brier on the
  uncertainty axis, taken from the banked transcripts/results (the harm signal). "Calibration harm" = negative
  Δoutcome.
- **Association test (FROZEN):** per cell, Spearman ρ between **OOD distance** and **calibration harm** (i.e.
  ρ(distance, −Δoutcome) so that positive ρ = "more off-manifold ⇒ more harm"), with item-cluster bootstrap CI
  (B≥10000), reusing ood.py's frozen machinery.

## 2. FROZEN support / KILL criteria (set BEFORE seeing results — inherited from arm prereg §H-M, pinned here)
- **SUPPORT (C2-mech hypothesis → EVIDENCE):** Spearman ρ(distance, −Δoutcome) **≥ 0.30 AND 95% bootstrap CI
  excludes 0**, in **≥3 of the 4 cells**.
- **NOT SUPPORTED (honest fail):** otherwise → **C2-mech is demoted to an explicit hypothesis / Future Work**
  in the claim-ledger and paper; we do NOT re-mine the same data for an alternative mechanism narrative. The
  behavioral results (E-0005, E-0006) are unaffected.
- The judgment rule above is frozen; it will NOT be changed after seeing the correlation.

## 3. Capture procedure (pure measurement; must NOT alter any frozen behavioral number)
- New capture script loads each model, replays the FROZEN steered generation for the uncertainty-axis items at
  the cell's frozen L and α, and records, per item: (a) baseline residual at L (reference channel), (b) steered
  residual at L, (c) the already-frozen per-item Δoutcome (from transcripts). It must NOT recompute or change
  any adjudication verdict/number — it only captures activations for the diagnostic.
- Determinism/lineage: same seed; record model id (incl. NousResearch mirror), commit, layer, α, item ids,
  reference provenance (split ids) into the OOD result provenance.

## 4. Lineage fix folded in (arm audit MAJOR)
- The experiment-registry `config_hash`/experiment_id currently omits `steering_method`, so CAA and ITI on the
  same model collide (e.g. both `c2b-adj-deac6326-0001`). Fix: add `steering_method` (and model id) to the
  registry `cfg` so every cell/experiment_id is distinct. The already-banked arm_full numbers are unaffected
  (each cell's results JSON already records `steering_method`); this fix ensures clean lineage for the OOD
  capture + any future run.

## 5. Post-capture (unchanged discipline)
- Hostile audit the capture script + OOD results: verify NOT a parser artifact, ITI/Llama genuine, reference is
  truly un-intervened same-layer (no self-fit), lineage aligned, and the ρ/CI recompute matches.
- Record verdict honestly (support → C2-mech evidence E-0007; else demote). Then WIPE the box.

## 6. Untouchable
E-0003, E-0005, prereg-c2b-adjudication.md, the frozen adjudicate_c2b §4 logic, and the banked arm_full H-R
result (E-0006) are FROZEN. This capture ADDS a diagnostic; it never edits them.

