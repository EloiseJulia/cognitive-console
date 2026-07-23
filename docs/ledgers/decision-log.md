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

## 2026-07-23 · D-0017 · Human GO: same-origin scale-free facade metric + CI, re-run 1.5B
- **Human decision (@EloiseJulia):** "GO" — implement the audit's recommended fair metric and re-run.
- **Metric v2 (feature/3):** facade_ratio = ⟨prompt−neutral, û⟩ / ⟨pos_pole−neutral, û⟩ (prompt's fraction
  of the neutral→pos-pole achievable range; same origin, scale-free, α-independent). Add bootstrap CI over
  the strong-prompt set + leave-one-neutral-out sensitivity band. Drop 'above null' as a headline (trivial
  high-dim bar) — keep only as a sanity note. Unit-test THIS exact computation. Keep old metric fields for
  compare but mark superseded.
- **Re-run:** Qwen2.5-1.5B fp32 CPU (weights cached), EXPLORATORY, zero paid/GPU. Then AUDIT again.
- **Honest read target:** how many axes show a real facade gap (ratio meaningfully <1 with CI not crossing 1)
  under the FAIR metric. Frozen? No.

## 2026-07-23 · D-0016 · 1.5B facade result AUDITED → mostly a metric artifact, NOT a real signal
- **Audit verdict (independent hostile, feature/3):** the headline "3/4 axes show a facade gap" is
  **(b) largely an artifact of metric construction**, should NOT move a GPU go/no-go.
- **2 BLOCKERs (both in the denominator):**
  1. **Arbitrary steering coefficient α=1** — facade_ratio is not scale-invariant; changing α makes the
     facade appear/disappear. The "gap" is denominator-dependent, not a property of prompts vs latent.
  2. **Origin mismatch** — numerator (prompt reach) measured from the NEUTRAL baseline, denominator (‖v‖)
     effectively from the NEG pole. Same-origin recompute: skepticism 0.48→0.85 (gap gone), deliberation's
     prompt exceeds ‖v‖ in absolute terms. Only uncertainty (0.71) survives a fair denominator.
- **MAJORs:** "above null / z=9–14" carries no evidential weight (random-direction projections in 1536-dim
  ≈0 by concentration → trivially passed); the headline computation itself is untested; focus layer-2
  degenerate (Cohen's-d picks shallow lexical layer). **CLEAN:** anti-circular phrasing (FIX2 real, distinct
  in kind), disjoint split, determinism, honest EXPLORATORY/valid_for_paper=false labeling.
- **Cheapest fix to make C1 trustworthy:** same-origin, scale-free reach fraction —
  facade_ratio = ⟨prompt−neutral, û⟩ / ⟨pos_pole−neutral, û⟩ (prompt's fraction of the neutral→pos-pole
  range), with bootstrap CI over strong prompts + leave-one-neutral-out sensitivity, and a unit test pinning
  THIS computation. Provenance nit: registry wall-clock (20s cache re-run) understates true 453s.
- **Decision (Manager):** C1 remains UNSUPPORTED. H1 stays 'testing'. Do NOT read a facade from this run.
  Before any bigger/GPU run, fix the metric (same-origin scale-free) + add CI/sensitivity. This is a
  METRIC design issue (Manager-owned), so I will re-scope the facade statistic, then re-run on 1.5B (free)
  to see if a real gap survives. Branch NOT merged. Frozen? No.

## 2026-07-23 · D-0015 · Human: fix facade metric, then re-run on Qwen2.5-1.5B (option A)
- **Human decision (@EloiseJulia):** "先修metric，然后A" (fix metric, then Qwen2.5-1.5B, local CPU).
- **Two metric fixes (both on feature/3):** (1) consistent statistic — measure prompt reach and latent
  reach from the SAME neutral baseline with matched estimators (mean-based primary; max as labeled upper
  bound), killing the max-vs-mean overshoot artifact. (2) **Use a DISTINCT strongest-prompt set** —
  separately authored natural strong instructions per axis (data/strongest_prompts/<axis>.jsonl), NOT
  held-out contrast-pair pos texts (those share the extraction distribution → trivially reach ~full ‖v‖;
  that pseudo-circularity is the real root of overshoot).
- **Re-run:** Qwen2.5-1.5B-Instruct, CPU, forward-only, memory-efficient load. Keep 0.5B result for compare.
  EXPLORATORY, zero paid/GPU. RAM note: needs ~10GB free (0.5B peaked 3.25GB); user to close apps.
- **Then AUDIT** the fixed metric + new run before any facade read. Frozen? No.

## 2026-07-23 · D-0014 · C1 facade pilot ran (CPU/0.5B) — NULL/inconclusive, NOT support for C1
- **Result (exploratory, feature/3-cpu-c1-facade, run id c1-facade-d963217c-0001):** per-axis facade_ratio —
  deliberation 1.161 (overshoot), skepticism −0.129 (extraction failed, ‖v‖=0.18), uncertainty 1.059
  (overshoot), focus 0.696 (only axis showing facade+above-null). 1/4 axes show the pattern → looks like NOISE.
- **Ops:** cold 399s / warm 81s (reproducible), peak RSS 3.25GB (near the 3.4GB free ceiling), pytest green,
  zero paid/GPU. Real HFActivationProvider (Qwen2.5-0.5B, CPU, forward-only) + anti-circular runner WORK
  end-to-end — plumbing/methodology validated.
- **Two independent reasons it can't read C1 (both correctable):** (1) 0.5B is ~15× below the 7–8B spec
  target; directions weak/unstable. (2) **Manager-introduced metric asymmetry:** facade_ratio compared the
  MAX held-out prompt against the MEAN latent ‖v‖ with neutral≈neg → ratio≥1 nearly structural (max≥mean),
  which manufactures the "overshoot." Fix: use consistent statistics (mean-vs-mean or max-vs-max) before any
  real read.
- **Decision (Manager):** treat pilot as plumbing/methods validation ONLY; H1 stays 'testing' (underpowered);
  do NOT read the facade hypothesis from this. Present hardware fork to human (bigger CPU model vs real
  7–8B on A800/cloud vs pause). Branch NOT merged pending human direction (also has an audited-test rewrite).
- **Frozen?** No.

## 2026-07-23 · D-0013 · Human GO: run C1 facade on CPU (small model, exploratory, no spend)
- **Human decision (@EloiseJulia):** "GO" — run C1 facade locally on CPU. Avoid A800 unless unavoidable.
- **Machine:** 31.7GB RAM (3.8GB free now), C: 196GB free, T1000 unusable (1.3GB free). → CPU + small model.
- **Manager plan:** implement subagent on feature/3-cpu-c1-facade — implement real CPU HFActivationProvider
  (forward-only, fp32, last-token pooling, activation cache, HF_HOME), install CPU-only torch, download
  Qwen2.5-0.5B-Instruct (Apache-2.0, no license gate), run an ANTI-CIRCULAR C1 facade protocol:
  disjoint extraction/probe split, neutral baseline for prompt shift, ‖v‖ as latent reference.
- **Labeling:** run is EXPLORATORY (protocol NOT frozen; thresholds placeholder; valid_for_paper=false).
  Purpose = does a facade signal plausibly exist + does the pipeline run on real activations. Then AUDIT.
- **Cost:** zero API, zero A800, zero paid — local CPU pilot (L3). Frozen? No.

## 2026-07-23 · D-0012 · phase0-analysis fixes verified & merged to main
- **Verification (Manager independent):** re-ran pytest → 111 passed; independently probed B1 (anti-aligned
  facade now `not c1_supported`, via the fail-without-guard test) and M1 (identical green inputs:
  max_facade_ratio 0.85→main_line, 0.95→plan_d — the 0.9 gate is now a real independent trigger). **B1 closed.**
- **Merged** feature/2-phase0-analysis → main (--no-ff). Phase 0 analysis pipeline (activation seam, CAA
  extraction, facade C1, routing, conflict harness, lineage/manifest) is code-complete + offline-tested;
  GPU forward pass cleanly stubbed (HFActivationProvider/BehaviorBackend) — plugs into whatever backend later.
- **Deferred (m3, logged open-risks):** GPU phase must register the conflict-probe calibration (prompt_target/
  latent_target poles) as its own experiment_id feeding the harness, else landing_fraction is silently biased.
- **Frozen?** No. All Phase-0 code/data ready on CPU; execution still blocked on human GPU/API/IRB (§5).

## 2026-07-23 · D-0011 · phase0-analysis audit (merge-after-fixes); dispatching fixes
- **Audit (independent hostile, branch feature/2-phase0-analysis):** core math verified CLEAN — CAA
  orientation (pos−neg, not swapped), fair unit-vector null, Cohen's-d layer scan (non-circular), tautology
  guards, no-torch stub, registry lock, manifest/lineage all ✔. But:
  - **[BLOCKER B1] Facade scores an ANTI-ALIGNED prompt as C1-supported.** `facade_gap_holds` has only an
    upper bound and `prompt_above_null` uses |projection|, so a prompt with negative projection (wrong
    direction — evidence AGAINST a facade) counts as supported → inflates facade_support_fraction → can flip
    RED/PARTIAL → GREEN. Corrupts the C1 evidence the pipeline exists to produce. Green suite missed it (no
    negative-projection test). Fix: `0.0 < facade_ratio <= max_facade_ratio` + failing-without-guard test.
  - **[MAJOR M1] Dead `no_facade_ratio` routing threshold** — subsumed by `not facade_holds`; a
    "pre-registered" gate that never fires, and `test_red_no_facade_routes_plan_d` is actually driven by a
    different condition (false confidence). Fix intent + isolate the test.
  - **[MINOR m1] conflict clipping** discards overshoot/wrong-side C2b signal → keep raw unclipped fraction.
  - **[MINOR m2] id mint outside registry lock** → move inside / retry.
  - **[MINOR m3] conflict calibration-pole provenance** → GPU-phase must register calibration as its own
    experiment_id feeding prompt_target/latent_target (logged to open-risks, deferred).
- **Manager triage:** FIX B1+M1+m1+m2 now (cheap, our code); DEFER m3 to GPU phase (open-risks). Re-verify → merge.
- **Frozen?** No. Branch NOT merged until B1 closed.

## 2026-07-23 · D-0010 · Human approved: write Phase 0 analysis code ahead (CPU, no spend)
- **Human decision (@EloiseJulia, via ask_user):** "继续停在 CPU 阶段：让我把 Phase 0 分析脚本
  （facade/冲突探针的纯代码部分）先写好待命."
- **Manager execution choice:** implement subagent on new branch feature/2-phase0-analysis. Write the
  GPU-independent analysis pipeline behind an `ActivationProvider` abstraction (real HF/GPU impl stubbed;
  `SyntheticActivationProvider` with injectable planted signal for offline unit tests): CAA mean-diff
  extraction + layer scan, facade projection analysis (C1), conflict-probe harness (C2b seed), Go/No-Go
  routing (spec §3), all registry-integrated + reproducible. torch kept optional/lazy so pytest runs w/o it.
- **Scope:** code + tests only. NO model load, NO GPU, NO downloads, NO paid API. Merge only after audit.
- **Frozen?** No.

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
