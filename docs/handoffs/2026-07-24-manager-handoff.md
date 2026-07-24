# Manager Handoff Bundle — cognitive-console — 2026-07-24

> Per AI-Instruction Part I §3. Outgoing Manager session is retiring (context saturated). This bundle lets a
> fresh Manager take over WITHOUT re-deriving anything. Read this + AGENTS.md + the ledgers, then take the
> "Acceptance Exam" at the end before updating ACTIVE_MANAGER.

---

## 0. One-paragraph state of the project
CHI/IUI-target HCI paper "Non-Surjective Dual-Channel Cognitive Console." After a pre-registered behavioral
KILL, the project was **owner-approved to reframe** to a disciplined **"reality-check" thesis: representational
**legibility ≠ behavioral controllability**. All core empirical work is DONE and independently audited; the
project is now at the **paper-writing threshold**. The remaining big fork (whether to add a minimal human
study) is deferred and owner-gated.

## 1. Frozen thesis + contribution structure (docs/paper/reframe-2026-07-24-reality-check.md)
1. **C1 — representational legibility gap ("facade") is real** (measurement). Evidence E-0003 (3/4 axes @
   Qwen2.5-7B, exploratory, single family).
2. **C2 — legibility ≠ controllability (HEADLINE reality-check).** Latent steering along the legible direction
   does NOT beat the best-prompt behavioral ceiling and HURTS calibration — **robust across 2 methods (CAA,
   ITI) × 2 models (Qwen2.5-7B, Llama-3-8B)**. Evidence E-0005 + E-0006. This CLOSES the unanimous critic
   BLOCKER (external validity).
3. **C2-mech — off-manifold account: DEMOTED to Future Work.** Pre-registered OOD distance test returned a
   VALID NULL (E-0007); honest-fail rule applied — no re-mining a different mechanism on the same data.
4. **C3 — console as boundary/limit + trust-calibration instrument** (design, SECONDARY). Built + audited
   (`src/cognitive_console/console/`), no user study yet.
- **Non-surjectivity (Mishra et al.)** = cited background/motivation only, NOT our empirical result.
- Honest scope line: single open-model families, CAA+ITI method families; a reality-check + design stance,
  NOT a general impossibility theorem.

## 2. Evidence banked (docs/ledgers/evidence-ledger.md) — ALL FROZEN, do not re-litigate
| id | claim | verdict | audit |
|---|---|---|---|
| E-0003 | C1 facade | 3/4 axes @ Qwen2.5-7B (exploratory) | prior |
| E-0005 | C2b behavioral | 0/3 KILL_PLAN_D @ Qwen/CAA | VALID_NEGATIVE |
| E-0006 | C2 arm 2×2 | ALL 4 cells 0/3 → NON_TRANSFER_GENERALIZED | VALID_ARM_EVIDENCE |
| E-0007 | C2-mech OOD | 0/4 → NOT_SUPPORTED (valid null) | VALID_NULL |
- E-0001/2 (1.5B C1) superseded by E-0003. E-0004 (crude-proxy C2b) invalid, superseded by E-0005.
- **Uncertainty-axis calibration HARM replicates in ALL 4 cells** (CI excl 0): CAA×Qwen −0.228, CAA×Llama
  −0.072, ITI×Qwen −0.103, ITI×Llama −0.084. This is the paper's most striking sub-finding; mechanism is OPEN.

## 3. Frozen protocols (NEVER change post-hoc)
- `docs/ledgers/prereg-c2b-adjudication.md` — §4 decision rule (paired item-cluster bootstrap, δ=0.05,
  Bonferroni CI 0.98333, DEV/TEST split, coherence gate ≤1.5×, three-tier verdict), N=60/60/80, k=5, α grid.
- `docs/ledgers/prereg-robustness-mechanism-arm.md` — 2×2 {CAA,ITI}×{Qwen,Llama}, H-R + H-M(ρ≥0.30) criteria.
- `docs/ledgers/prereg-ood-capture.md` — OOD capture (whitened Mahalanobis, same-layer un-intervened
  reference, honest-fail).
- Implementation of the frozen §4 math: `src/cognitive_console/experiments/adjudicate_c2b.py` (blob must stay
  identical to what produced E-0005/E-0006).

## 4. Code / build / test
- Package `cognitive_console` (src-layout). BUILD: `python -m pip install -e .`  TEST: `python -m pytest -q`
  (~320 passed / 4 skipped on main HEAD 9d735de).
- Key runners: `scripts/run_c2b_adjudication.py` (single cell), `scripts/run_arm_matrix.py` (2×2),
  `scripts/run_ood_capture.py` (H-M), `python -m cognitive_console.console` (the console).
- Steering: `steering/extract.py` (CAA), `steering/iti.py` (ITI, orthogonal), `steering/generate.py`
  (SteeredHFBackend + capture_residual_activations post-steer hook). Analysis: `analysis/ood.py`,
  `analysis/facade.py`. Prompt-optimizer baseline: `experiments/prompt_optimizer.py` (default OFF).

## 5. Decision log high points (docs/ledgers/decision-log.md, D-0001..D-0040)
- D-0034 C2b KILL→reality-check; D-0035 Route A pure-model + venue IUI>CHI>CSCW + 2 must-adds;
  D-0036 critic triage (unanimous external-validity BLOCKER); D-0037 froze robustness arm + budget +
  pre-granted GPU; D-0038 Llama gated → NousResearch identical-weights mirror; D-0039 arm =
  NON_TRANSFER_GENERALIZED (E-0006); D-0040 OOD valid null (E-0007) → C2-mech demoted.

## 6. Owner (@EloiseJulia) standing preferences (also in stored memories)
- Respond in **Chinese**.
- **Pre-register frozen success/kill BEFORE running; never change judgment after seeing results; report
  qualified negatives honestly; allow the hypothesis to fail.** Method-improvement = a SEPARATE independent
  prereg; never touch frozen records.
- Report ALL preregistered conditions (no cherry-picking / HARKing).
- Frame contribution by the paradigm shift, not incremental delta over the best baseline.
- Scope claims precisely (failure MODE vs base rate; conditional not absolute).
- Large/confirmatory runs: cautious, budget-controlled, verify-then-scale, owner sign-off. GPU for the arm
  was pre-granted (D-0037) — that authorization covered the completed arm; NEW spend needs a fresh OK.
- Wants the Manager to ALSO provide top-venue research insight (idea polishing), not just scheduling.

## 7. Hard-won operational lessons (save the next Manager pain)
- **Every hostile audit here has caught a real, result-corrupting bug (≈9/9).** Audits before merge are
  non-negotiable. Recurring bug class: **fabricatable verdicts** (aggregation/resume/guard trusting counts or
  file-existence instead of validating completeness + config-fingerprint/provenance) — appeared in OOD arm
  verdict, matrix resume, prompt-opt fingerprint. Always check this.
- **Activation capture ≠ generation:** `output_hidden_states[layer]` does NOT reflect a forward-hook return;
  capture post-steer via a dedicated hook on block[L-1] registered AFTER the steer hook. Capture on the BASE
  transformer (skip lm_head) + batch, or you OOM. Verify on real GPU: steered−baseline == α·dir.
- **Rented AutoDL box:** parallel HF downloads throttle each other — download models SEQUENTIALLY, single
  clean process, `HF_ENDPOINT=hf-mirror`, `HF_HUB_DISABLE_XET=1`, `HF_HUB_ENABLE_HF_TRANSFER=1`, NO
  restart-supervisor. Drive via paramiko inline (`@'...'@ | python -`); GPU-busy makes SSH sluggish → use
  short probes, not long blocking reads. Llama-3-8B is HF-gated → NousResearch identical-weights mirror.
- Frozen-instrument runs are deterministic (same seed) → cell1 of the arm reproduced E-0005 byte-for-byte;
  use that as a sanity anchor for any re-run.

## 8. Immediate next steps for the incoming Manager
1. **Enter the writing stage (AI-Instruction Part III).** Build the paper outline + claim-map + citation-map
   under `docs/paper/`; enforce the Claim↔Evidence bidirectional gate (nothing into Abstract/Contributions/
   Conclusion without an evidence row). Main artifacts: Δ-table (4 cells) → C2; ratio-CI figure → C1.
2. **Resolve the R3-B1 human-anchor fork** (owner-gated, §5): (a) minimal 8-12-person walkthrough → CHI/CSCW
   eligible, breaks pure-model; (b) pure-model methodology-asset (`docs/paper/methodology-asset.md` already
   drafted) → IUI ceiling. Owner said DECIDE AFTER arm results (now available). Present the choice.
3. Optionally add the cheap writing-only critic asks (nearest-neighbor novelty table; C1 heterogeneity
   caveats; scope-guard language) from the reframe critics (R1/R2 findings).
4. Do NOT spend GPU/paid API, submit externally, change core Claim/venue, or touch frozen records without
   owner approval (AGENTS.md §5).

## 9. Ledger/dir map (all git-tracked except large artifacts, which are gitignored)
`docs/charter/`, `docs/research/`, `docs/specs/`, `docs/plans/`, `docs/ledgers/` (charter/claim/hypothesis/
evidence/experiment-registry/decision-log/failure-log/open-risks/compute + the 3 preregs), `docs/reviews/`,
`docs/paper/` (reframe, methodology-asset, claim/citation maps to build), `docs/handoffs/` (this file).
Results: `results/arm_full/` (small JSONs tracked; transcripts/checkpoints/c1 gitignored),
`results/ood_capture/`, `results/c2b_adjudication_hf_2026-07-24/`.

## 10. Acceptance exam (incoming Manager must answer before taking over)
1. What is the headline claim, and what 2×2 evidence makes it robust? (→ C2; E-0006 NON_TRANSFER_GENERALIZED)
2. Which records are FROZEN and must never be re-run/re-judged? (→ E-0003/E-0005/E-0006/E-0007 + 3 preregs +
   adjudicate_c2b §4)
3. Why is C2-mech NOT a contribution? (→ E-0007 valid null; honest-fail; no re-mining)
4. What must precede ANY GPU/paid/submission/venue/claim change? (→ owner approval, AGENTS.md §5)
5. What is the recurring bug class every audit must check? (→ fabricatable verdicts: validate completeness +
   fingerprint/provenance, never trust counts/file-existence)
6. Venue policy? (→ IUI-first pure-model; CHI/CSCW require the minimal human study)
