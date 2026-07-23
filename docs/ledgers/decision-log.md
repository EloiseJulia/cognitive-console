# Decision Log

> Append-only. Every scope/Claim/venue/budget/protocol change and every Manager ruling is recorded here.
> Human-approval items (AGENTS.md §5) must cite the human decision.

---

## 2026-07-23 · D-0001 · Session bootstrap & Charter v0.1 drafted
- **Decision (Manager, autonomous):** Established `docs/` ledger structure per AGENTS.md §8; drafted
  Research Charter v0.1 (status: proposed, NOT frozen); registered C1/C2/C3 + H1/H2/H3.
- **Rationale:** Phase-1 deliverable #1. Charter authoring is Manager's own duty (not a research action).
- **Frozen?** No. Charter freeze pending human sign-off + Charter Review (R1/R2/R3) triage.
- **Next:** dispatch (a) novelty-falsification research subagent, (b) 3 independent Charter-Review critics.

## 2026-07-23 · D-0002 · Venue = CHI (primary), UIST excluded
- **Decision (from idea/开题报告, Manager records):** Target venue CHI, not hard-locked; fallbacks IUI/DIS;
  UIST excluded. Any venue change = human-approval item.
- **Frozen?** No.

## 2026-07-23 · D-0003 · Novelty Gate completed (research subagent, commit 2ab33ff)
- **Outcome:** Report `docs/research/2026-07-23-novelty-falsification.md`. 8/8 audited citations VERIFIED,
  0 fabricated. **Mishra non-surjectivity paper (2604.09839) is REAL and accurately quoted — RQ2 basis holds.**
- **Substantive findings (Manager accepts for triage):**
  1. **[MAJOR] C2 over-applies the theory.** Mishra proves non-surjectivity of *internal activations*, NOT
     that any user-relevant *behavioral* threshold is prompt-unreachable. C2 (behavioral) is not entailed.
     → Action: reword C1/C2 to separate internal-state vs behavioral-reachability before Charter Freeze.
  2. **[MAJOR] SemanticLens/Labarta misstated** in 开题报告 — it is a vision/CLIP tool for experts
     (arXiv:2604.11467, CVPR'26 W), and "SemanticLens" (Fraunhofer, Nat.Mach.Intell.'25) is a separate work.
     → Action: correct nearest-neighbor framing.
  3. **[MED] Scoop risk = MEDIUM, not LOW** (charter §3.1 said LOW). Huang&Lim is closest single-channel
     threat (poster, SAE not CAA); Stolfo instruction-steering cuts against C2; name-collision
     "Dual-Channel Steering" already coined. Owed: manual CHI'26/ACM-DL prior-art sweep.
  4. **[MINOR] ActAdd Appendix-B sub-claim UNVERIFIED** → mark [NEEDS EVIDENCE] before it enters the paper.
- **Frozen?** No. These feed the Charter-Review triage; Charter to be revised to v0.2 after critics return.

## Pending human-approval items (NOT yet decided)

## 2026-07-23 · D-0004 · Charter Review complete; Charter revised v0.1→v0.2
- **Input:** 3 independent CHI critics (R1/R2/R3), all verdict **major-revision**, score ~2.0–3.0/5
  (→3.0–4.0 if blockers closed). Files: `docs/reviews/2026-07-23-charter/review-R{1,2,3}.yaml` +
  `manager-response.yaml`.
- **Unanimous BLOCKER (R1-F1/R2-B1/R3-1):** internal-state non-surjectivity ≠ behavioral unreachability.
- **Decision (Manager, autonomous — reworking Claim wording pre-freeze to match evidence is Part I core):**
  Revised Charter to v0.2. Split C2→C2a (internal, theory-backed) + C2b (behavioral, must be empirically
  demonstrated). Reworded RQ2. Added null baseline + effect-size threshold to C1. De-confounded study
  (added condition D = dual-channel no-panel). Operationalized calibrated trust. Corrected SemanticLens.
  Added over-trust Non-Claim. Added reasoning-gain discriminating task. Sharpened RQ1 vs RQ2.
- **Not frozen.** Charter Freeze deferred until: (a) human confirms budget/IRB/venue, (b) owed manual
  CHI'26/ACM-DL prior-art sweep run (new research task), (c) v0.2 re-reviewed.
- **Escalated to human (§5):** budget caps, IRB/human-subjects path, 16-week scope realism.

## 2026-07-23 · D-0009 · phase0-prep fixes verified & merged to main (f4a1073)
- **Verification (Manager independent light check):** re-ran `python -m pytest -q` → 64 passed; independently
  recomputed per-axis pos-longer fraction (delib 0.425, skept 0.400, uncert 0.450, focus 0.525 — all in band)
  and MAD 1.1–1.5 tokens; eyeballed sample pairs = genuine length-matched minimal contrasts. **B1 closed.**
- **Merged** feature/1-phase0-prep → main (--no-ff). Backfilled AGENTS.md §1: BUILD=`pip install -e .`,
  TEST=`python -m pytest -q`, RUN=n/a.
- **New caveats logged to open-risks (not blocking):** (i) framed-stance contrast style *describes* the axis
  stance rather than enacting it — standard CAA design but revisit before S5 extraction; (ii) registry
  `.lock` sidecar has no stale-lock reaping — harden before heavy parallel writes.
- **Frozen?** No. Phase-0 DATA/scaffolding ready; execution still blocked on human GPU/API/IRB (§5).

## 2026-07-23 · D-0008 · Phase0-prep audit (merge-after-fixes); dispatching fixes
- **Audit (independent hostile, branch feature/1-phase0-prep):** metric/registry CODE verified correct
  (projection math, null baseline, single-process atomicity, schema, labels all ✔). But:
  - **[BLOCKER B1] Length confound in contrast pairs.** pos vs neg are 100% rank-correlated with length
    (pos longer for deliberation/skepticism/uncertainty; shorter for focus). A CAA mean-diff vector would
    encode verbosity, not the axis → kills C1 validity; realizes R2 style-vs-substance threat in the DATA.
  - **[MAJOR M1] Leakage test is theater** — id prefixes disjoint by construction → vacuous; no content check.
  - **[MAJOR M2] Registry cross-process TOCTOU race** — parallel appenders silently drop runs (breaks the
    exact parallel-subagent workflow the registry exists for; shared experiment-registry.yaml).
  - **[MINOR m1] schema test one-directional; [MINOR m2] zero-vector inf z.**
- **Manager triage (all = our code + clear fix → FIX, no owner sign-off needed):** dispatch a fix subagent
  on the same branch to re-author length-matched minimal-contrast pairs + add length-monotonicity test;
  add content-level leakage check; add cross-process file lock to registry; fix m1/m2. Re-audit/verify → merge.
- **Frozen?** No. Branch NOT merged until B1 closed + re-verify green.

## 2026-07-23 · D-0007 · Human approved: dispatch S1–S4 PREP slices (CPU, no spend)
- **Human decision (@EloiseJulia, via ask_user):** dispatch S1–S4 PREP now (select axes + author contrast
  pairs + assemble eval sets + build registry), CPU/zero-cost.
- **Manager execution choice:** ONE implement subagent in a single worktree `feature/1-phase0-prep`
  (avoids 3 parallel agents racing to create the Python skeleton → merge conflicts; also cheaper).
  Establishes minimal Python skeleton + pytest → will backfill BUILD/RUN/TEST into AGENTS.md §1.
- **Scope:** data-level authoring + scaffolding ONLY. NO GPU, NO model runs, NO paid API, NO user study.
- **Frozen?** No. Merge to main only after independent audit (阶段4) passes.

## 2026-07-23 · D-0006 · Prior-art sweep complete; owed-sweep gate CLEARED (contingent)
- **Input:** `docs/research/2026-07-23-priorart-sweep.md` (commit 2ac2c60). Manual sweep of CHI'26 program +
  preprints, CHI EA'26, IUI/DIS, ICML/ICLR/OpenReview, ACM DL.
- **Outcome:** **Exact-gap scoop MED → LOW** — no artifact makes the prompt↔latent divergence an operable
  interface object with conflict attribution + trust recalibration for non-experts. "Obvious-combination"
  risk stays ~MED (survives only if Phase-0 facade + conflict shown empirically).
- **New threat surfaced:** "Steer Like the LLM" / PSR (ICML 2026) argues activation steering can be trained
  to MATCH/EXCEED prompt steering behaviorally → directly attacks C2b behavioral-gap rhetoric. Not a scoop
  (no UI/users). Must cite + pre-empt. New look-alikes to cite: Latent Manipulator (CHI EA'26), ASTEER.
- **Decision (Manager, autonomous):** Charter §0 owed-sweep gate marked **CLEARED**, contingent on: (a)
  internal-vs-behavioral wording fixed — DONE in v0.2; (b) cite PSR + new neighbors — logged to open-risks
  + claim-ledger; (c) rename "Dual-Channel Steering" — DEFERRED to writing stage.
- **Frozen?** No. Charter Freeze still pending human budget/IRB + a Freeze re-review.

## 2026-07-23 · D-0005 · Human approved: proceed to prior-art sweep + Phase 0 spec/plan
- **Human decision (@EloiseJulia, via ask_user):** "批准：先做 prior-art sweep + 出 Phase 0 spec/plan
  （暂不跑需花钱/GPU 的实验）."
- **Authorized (no spend):** (a) dispatch research subagent for manual CHI'26/ACM-DL/arXiv prior-art
  sweep; (b) Manager writes Phase 0 spec (docs/specs/) + plan (docs/plans/), data-level, no L4/GPU/paid API.
- **Still gated on human (§5, NOT yet given):** GPU hours, paid-API ceiling, IRB/human-subjects, any L4 run.
- **Frozen?** No. Charter Freeze still deferred pending sweep + budget/IRB + re-review.

## Earlier pending human-approval items (NOT yet decided)
- Budget caps (GPU hours, paid-API ceiling, max_full_runs).
- Human-subjects/IRB path for Formative + controlled study.
- Any L4 full run, paid/private API, GPU allocation, external submission.
