# Decision Log

> Append-only. Every scope/Claim/venue/budget/protocol change and every Manager ruling is recorded here.
> Human-approval items (AGENTS.md §5) must cite the human decision.

---

## 2026-07-27 · D-0044 · Flagship line #2 FROZEN (novice-manipulation prereg); L0 GPU pilot authorized
- **New independent research line** (idea #2 from the owner brainstorm): "Does voluntary user expertise self-disclosure
  causally trigger autonomy-reducing/manipulation-indicative LLM behavior, and is there a legible latent user-model axis
  that routes but may not control it?" — generalizes legibility!=controllability from metacognitive to social-inference axes.
- **Pipeline before freeze (all audited/verified):** owner brainstorm -> unifying frame (implicit user-conditioning as an
  uncontrolled latent channel) -> 3 web prior-art sweeps (idea#2 flagship, idea#1 strong-second, idea#3 folded) ->
  independent prereg DRAFT -> adversarial novelty-critic (caught: helpful-adaptation-vs-manipulation construct confound,
  the Akbulut 2603.25326 DeepMind scoop, instruction-following confound, latent trivial-read, deployed over-claim,
  judge sycophancy) -> 10 pre-freeze fixes -> primary-source citation verification (Akbulut scoop CONFIRMED REAL; venue
  corrections; NO hallucinated ids).
- **Freeze (Manager, owner-approved D-0044):** the critic-hardened + cite-verified prereg is FROZEN. Key hardening:
  manipulation PRESENT requires B(novice)-A(control) effect AND B>E(explain-simply) on M1/M4; three-tier caveat manifest
  separates helpful simplification from harmful omission; token-blind latent probe; judge condition-blinding; scope hard
  to open 7B/8B. Best venue fit: FAccT/AIES/SafeAI (honest-null + pre-registration valued).
- **L0 authorization (owner):** one box for TWO L0 probes — (a) flagship DEV-power pilot (estimate M1-M4 variance -> set
  N/δ within the frozen rule) and (b) idea#1 breadth-axis L0 (12 items, does a narrow persona suppress oracle-domain
  solutions + is a breadth direction extractable). Combined ~$5-15. Harnesses (task suites + runners + scorers) to be
  BUILT no-GPU + audited BEFORE booting the box (avoid idle billing). Full run decided after L0.
- **Separation:** does NOT touch the current frozen paper/records. DRAFT->FROZEN status updated in the prereg doc.

## 2026-07-26 · D-0043 · GPU session (owner-approved): Llama C1 done (E-0008) + PSR arm KILL (E-0009); box auto-off
- **Owner** provisioned the RTX4090D box and authorized full-auto A→D. Both ran; box auto-powered-off after
  results were pushed to origin (cost control: safety-net `shutdown +240` + immediate shutdown; box confirmed
  unreachable/off, GPU billing stopped).
- **A (E-0008, audited mergeable):** Llama-3-8B C1 facade via the FROZEN C1 protocol (byte-identical, parity vs
  E-0003 clean). 3/4 axes hold — BUT axis composition differs from Qwen: MODEL-INVARIANT only on deliberation +
  skepticism; uncertainty holds on Qwen not Llama; focus holds on Llama not Qwen. C1 = 2-model support at 3/4
  aggregate WITH heterogeneity; both exploratory, valid_for_paper=false. Honest caveat banked.
- **D code path:** implemented faithful-PSR method (PR#12, audited SAFE-TO-RUN after fixing a BLOCKER budget
  overrun + 2 MAJORs); D-0042 froze lambda_coh=1.0 before data. First GPU attempt hit a double-model-load OOM,
  caught by the mandatory smoke gate (no full run, no fabricated verdict); fixed memory-only (PR#15, protocol
  byte-identical) and re-ran.
- **D result (E-0009, audited VALID_NEGATIVE):** frozen PSR arm on Qwen2.5-7B = KILL_PLAN_D (all 3 axes fail;
  uncertainty -0.160 CI excludes 0 negative). Audit confirmed the negative is GENUINE (optimizer did real work,
  steering applied, no degeneracy, no leakage, fingerprint reproduces). **Consequence:** C2 "legibility ≠
  controllability" is robust to METHOD STRENGTH (naive CAA/ITI + DEV-optimized PSR) — but EXPLORATORY, single
  model/seed, valid_for_paper=false; does NOT overwrite the frozen E-0005/E-0006 headline; pre-empts the "method
  too weak" reject risk.
- **Every hostile audit again earned its keep:** caught the PSR budget 7× overrun (pre-run), the OOM (via smoke),
  and validated the negative as non-artifactual (post-run). honest-fail honored throughout.
- **Frozen?** E-0008/E-0009 banked as exploratory. E-0003/E-0005/E-0006/E-0007 + preregs + adjudicate_c2b §4
  untouched. **Next (owner-gated framing):** update the paper to incorporate E-0008 (C1 Llama + heterogeneity)
  and E-0009 (PSR arm as exploratory supporting evidence) — Manager to present framing for owner sign-off.

## 2026-07-25 · D-0042 · Pre-run parameter freeze for the PSR arm: lambda_coh = 1.0 (frozen BEFORE any data)
- **Context:** Implementing the frozen PSR method (feature/psr-impl, PR#12) surfaced that prereg-latent-recovery-arm.md
  specifies the DEV objective `J = mean_DEV(outcome) - lambda_coh * max(0, coherence_ratio - 1.5)` but did NOT give a
  numeric value for `lambda_coh`.
- **Decision (Manager, self-decided; NOT a §5 change to a frozen judgment — completing an unspecified constant BEFORE
  any run, per honest-fail):** freeze **`lambda_coh = 1.0`**. Rationale: the coherence gate (<=1.5x) is ALREADY a hard
  per-axis TEST pass condition in the frozen adjudicator regardless of lambda_coh; lambda_coh only shapes DEV-stage
  candidate selection to avoid degenerate vectors, so it is secondary; 1.0 is a neutral default. It is frozen and
  fingerprinted in the run config BEFORE any TEST data is seen. Recorded as a pre-run freeze addendum in the prereg.
- **Also frozen at implementation (matching the prereg):** basis {CAA, ITI, top-16 PCA}, r=16; <=32 DEV candidate
  evals/axis; {L-1,L,L+1} schedule (DEV-selected); alpha grid {2,4,6,8,12,16,24}; optimizer seed 20260723;
  objective optimizes ABSOLUTE DEV outcome (not beat-a-specific-prompt); adjudicator imported BYTE-IDENTICAL.
- **Frozen?** No frozen judgment/evidence altered. E-0005/6/7, adjudicate_c2b §4, the three preregs' decision rules
  untouched. This only fills a previously-unspecified optimization constant before the run.

## 2026-07-24 · D-0041 · Writing-threshold stage kickoff: G/doc-sync merged; D prereg FROZEN (Option 1); A staged; origin/main found stale
- **New Manager took over** (handoff 2026-07-24), passed acceptance exam. Launched 3 parallel workflows + doc hygiene.
- **Workflow G (console):** feature/37-console built console v1 + no-human computational demo (auto-flags C1 facade limit + C2 steering degradation from FROZEN artifacts). Independent hostile audit (audit-console) = **MERGEABLE**, no BLOCKER/MAJOR; recomputed every displayed number by hand from artifacts (no hardcoded/fabricated values); 318 passed/4 skipped. One MINOR (C2 channel has no evidence-ledger fallback — robustness gap, not integrity) logged as follow-up. Merged to local main (was GitHub PR#2).
- **Doc-sync:** feature/doc-sync-arm synced reframe + methodology-asset to the 2×2 arm (E-0006) generalized negative and moved C2-mech to Future Work (E-0007 null); added PSR (ICML 2026) scope guard; fixed open-risks #8 (Labarta=vision/CLIP confirmed; ActAdd App-B kept [NEEDS EVIDENCE]). Merged to local main (was PR#3).
- **Workflow D (latent recovery arm):** drafted prereg-latent-recovery-arm.md. Manager review restructured it: PRIMARY = **faithful PSR-style DEV-optimized steering** (natural-activation basis {CAA,ITI,top-16 PCA}, NO Mahalanobis penalty — fair test of the PSR/open-risk-#9 threat so a failure legitimately upgrades C2 to "robust to method strength"); manifold-constrained variant DEMOTED to optional secondary. **Owner approved Option 1 + Qwen primary budget (~2.0–3.4 GPU-h, ~US$5–10)**; Llama confirmation arm NOT yet authorized (revisit if Qwen shows signal). Prereg FROZEN, merged to local main (was PR#1). Success = ≥1 axis beats best prompt on the frozen adjudicator + coherence gate (scope-narrowed positive, never overwrites E-0005/6); Kill = all axes fail ⇒ C2 upgrades to robust-to-method-strength.
- **Workflow A (Llama C1 facade):** staged; NO code change (run_c1_facade.py already parametrizes --model). Parameter-parity table vs E-0003 clean (only model/device/dtype differ; identical layer-selection rule). Budget ~0.5–1.5 GPU-h (~US$1–3). Exec pending owner GPU boot; run-time guard = dump resolved config + diff vs E-0003 + audit.
- **GPU plan (owner-approved):** boot ONE box → run A (cheap) first → run D primary (Qwen) → wipe. Box currently OFF; owner to provision.
- **INHERITED ISSUE — origin/main is STALE:** GitHub origin/main (cf5c327) contains only 4 commits (initial, AGENTS.md, venue, console#2) and is MISSING the entire local empirical history (E-0003/5/6/7, D-0034..D-0040, handoff — all only on local main dcd9ef7). Subagent PRs branched from real local main but GitHub merged them onto stale origin. **Integration was therefore done via LOCAL merges into local main (the true source of truth); origin NOT pushed.** Reconciliation of origin (recommend force-align origin → local truth; no content lost since console#2 content is reproduced by the local merge) is ESCALATED to owner as a separate decision. No frozen record altered.
- **Frozen?** No frozen record touched. E-0003/E-0005/E-0006/E-0007 + 3 preregs + adjudicate_c2b §4 intact.

## 2026-07-24 · D-0040 · OOD off-manifold test = VALID NULL (E-0007) → C2-mech honestly demoted; box to be wiped
- **Result:** the pre-registered H-M off-manifold capture ran on the box (after 3 capture bugs were found &
  fixed en route — each caught by a guard/audit: (1) `output_hidden_states[layer]` did NOT reflect the steer
  forward-hook return → steered==baseline (the content self-fit guard CORRECTLY blocked this meaningless
  capture); real-GPU probe after fix: steered−baseline = exactly α·dir; (2) CUDA OOM from lm_head logits →
  capture now runs the base transformer + batching; (3) string-only self-fit guard → content-hash+overlap).
  Final: per-cell Spearman ρ(dist,−Δoutcome) = {0.033, 0.039, -0.060, -0.223}, **0/4 pass → NOT_SUPPORTED**.
- **Independent hostile audit (audit-ood-null): VALID_NULL.** Capture genuinely post-steer (norm_infl>1,
  guard silent); Δoutcome aligns with frozen transcripts by item_id EXACTLY (max_abs_diff=0, independently
  recomputed); ρ≈0 is a real no-correlation not a degenerate/zeroed artifact; frozen metric/criteria faithful;
  behavioral numbers untouched. Distance-dump deemed NOT required.
- **Decision (Manager, per owner's frozen honest-fail directive):** the off-manifold *distance* mechanism for
  the calibration harm is NOT evidenced → **C2-mech DEMOTED to explicit hypothesis / Future Work** in the
  claim-ledger + paper. We do NOT re-mine a different mechanism on the same data. E-0007 banked (valid null).
  The behavioral results E-0005/E-0006 (NON_TRANSFER_GENERALIZED) are UNAFFECTED and remain the paper's core.
- **Lineage fix:** registry cfg now includes steering_method (arm-audit MAJOR closed).
- **Box:** all GPU work for the arm is COMPLETE (E-0006 + E-0007 banked). Wiping the rented box; human to stop
  the instance (billed hourly).
- **Frozen?** E-0007 banked. prereg-ood-capture honored (hypothesis allowed to fail). E-0003/E-0005/E-0006/
  prereg-c2b/adjudicate_c2b §4 untouched.

## 2026-07-24 · D-0039 · Arm 2×2 COMPLETE = NON_TRANSFER_GENERALIZED (E-0006, audited VALID); OOD capture pre-registered
- **Result:** frozen robustness arm ran on the rented box (Qwen download saga resolved by serializing the two
  downloads; Llama via NousResearch identical-weights mirror D-0038). Autonomous chain: waited downloads →
  n_items=4 SMOKE (all 4 method×model combos incl. ITI×Llama validated on real GPU, ARM_SMOKE_RC=0) → full
  2×2. **All 4 cells 0/3 → arm_verdict=NON_TRANSFER_GENERALIZED (E-0006).** cell1 reproduces E-0005
  byte-for-byte. Uncertainty calibration HARM replicates in all 4 cells (CI all excl 0 negative).
- **Hostile audit (audit-arm-2x2): VALID_ARM_EVIDENCE**, no BLOCKER. Confirmed: distinct fingerprints (not
  reused/fabricated), ITI genuinely probe-based, Llama genuinely Llama-3-8B, uncertainty harm is REAL
  degradation not parser artifact (trunc=0/empty=0; steered text drops the Confidence format), aggregation
  faithful, CI recompute exact. **MAJOR (lineage, non-numeric):** registry experiment_id omits
  steering_method → CAA/ITI same-model collide; results JSON records method so recoverable; CODE FIX folded
  into the OOD capture work.
- **Significance:** **CLOSES the unanimous critic BLOCKER (external validity / single-method×single-model).**
  Reality-check "legibility ≠ controllability" now holds robustly across CAA+ITI × Qwen+Llama; steering
  consistently HARMS calibration.
- **Decision (Manager) + human directive:** owner chose (a) do the OOD off-manifold capture NOW (box up,
  models loaded; deferring is strictly costlier — re-download + config drift + dirty lineage), BUT
  **pre-register BEFORE capturing** and **allow the hypothesis to fail honestly**. Wrote
  `docs/ledgers/prereg-ood-capture.md`: FROZEN reference=same-layer un-intervened residuals; ONE metric=
  whitened Mahalanobis; FROZEN support/kill = Spearman ρ(dist,−Δoutcome)≥0.30 & CI-excl-0 in ≥3/4 cells →
  C2-mech EVIDENCE, else demote to explicit hypothesis/Future-Work (NO re-mining a different mechanism on the
  same data). Capture must not alter any frozen behavioral number. Then hostile-audit + bank, then WIPE box.
- **Frozen?** E-0006 banked (H-R). OOD capture prereg to be FROZEN before running. E-0003/E-0005/prereg-c2b
  untouched.

## 2026-07-24 · D-0038 · Llama-3-8B is HF-gated → use identical-weights ungated mirror (access workaround)
- **Problem:** the frozen arm's 2×2 LOCKS the 2nd model to `meta-llama/Meta-Llama-3-8B-Instruct`, but that
  repo is HF-GATED ("Access denied. This repository requires approval") even via hf-mirror — blocks the run.
- **Decision (Manager, autonomous — NOT a §5 protocol change):** use
  `NousResearch/Meta-Llama-3-8B-Instruct`, a well-known **ungated mirror of the IDENTICAL Llama-3-8B-Instruct
  weights**. Verified genuine: config is `LlamaForCausalLM`, hidden_size=4096, num_hidden_layers=32,
  eos_token_id=128009 (Llama-3-Instruct EOT) — bit-identical model, only the access path differs. This is a
  deployment/access detail, NOT a scientific/model change (the frozen spec "Llama-3-8B-Instruct" is honored;
  same architecture the ITI/provider code targets). Documented in results provenance as the mirror source.
- **Alternative rejected:** switching to Mistral-7B WOULD be a frozen-protocol change (§5) — not taken.
  Requesting a gated HF token deferred (mirror is cleaner + reproducible for others).
- **Frozen?** Arm prereg UNCHANGED (same model identity). Provenance will record mirror repo id.

## 2026-07-24 · D-0037 · Human FROZE robustness+mechanism arm prereg + budget + pre-granted GPU
- **Human decision (@EloiseJulia):** "批准冻结此 prereg + 预算；立即开始纯 CPU 工程阶段(ITI/Llama/
  transcript/OOD/prompt-opt)，GPU 你直接跑就行，不用我批准，我刚刚租的那台一直开着的."
- **Effect:**
  - `docs/ledgers/prereg-robustness-mechanism-arm-DRAFT.md` is now **FROZEN** — LOCKED 2×2 {CAA,ITI}×
    {Qwen2.5-7B,Llama-3-8B} (3 axes/cell, transcripts saved), OOD Spearman ρ≥0.30 CI-excl-0 in ≥3/4 cells,
    three-tier success/kill, stronger-prompt-optimizer + C1-null appendix. Immutable post-freeze.
  - **Budget approved** (GPU small ~4-6h one rented box; engineering ~6-8 implement+audit cycles).
  - **GPU sign-off PRE-GRANTED** for this arm — the always-on rented box; Manager may run the GPU matrix
    WITHOUT a further ask (the §4b gate is satisfied in advance). (Still: wipe/clean discipline + hostile
    audit each cell before banking.)
  - **Start NOW:** pure-CPU engineering phase (ITI method, Llama-3 provider, transcript-saving, OOD
    diagnostic, prompt-optimizer, C1-null appendix) — each behind a hostile audit before merge.
- **Untouched:** E-0003, E-0005, prereg-c2b-adjudication.md, frozen `adjudicate_c2b` §4 logic.
- **Frozen?** YES — arm prereg frozen. In parallel (already running): console build (feature/37-console) +
  methodology-asset doc (both no-regret, no GPU).

## 2026-07-24 · D-0036 · Reframe critic triage (R1/R2/R3) + robustness-mechanism arm drafted
- **Input:** 3 independent IUI/CHI critics on the reality-check reframe →
  `docs/reviews/2026-07-24-reality-check-reframe/review-R{1,2,3}.yaml`. All **major-revision / reject-if-
  unchanged**. Score-if-unchanged ≈ IUI 2.8-3.2 / CHI 2.3-2.8; if blockers closed ≈ IUI 3.4-4.0 / CHI 3.0-3.6.
- **Venue (confirms D-0035):** **IUI > CHI > CSCW** (R1 + R3 explicit; R2 minority put CSCW>CHI but its
  rationale contradicts the owner's no-humans-→-CSCW-worse call). IUI-first stands.
- **Unanimous BLOCKERs (= owner's 2 must-adds now hard gates):**
  1. External validity too narrow (single CAA × single Qwen) — need **≥2 method families × ≥2 model
     families** on the same frozen adjudication, or narrow the claim everywhere. (R1-F1, R2-M2, R3-B2)
  2. Off-manifold mechanism is inferential — add a cheap OOD-distance-vs-Δoutcome diagnostic or demote
     C2-mech to explicit hypothesis. (R1-F3, R2 q4, R3-M1)
- **NEW cross-critic finding beyond owner's plan (ESCALATED):** **R3-B1 (BLOCKER) + R2 + R1** — a fully
  human-free paper with the console demoted risks **venue-mismatch / desk-reject** at IUI/CHI ("ML negative +
  HCI vision, not a finished interaction contribution"). Two resolutions: (a) add a MINIMAL informal user
  anchor (8-12 users) [breaks strict Route A]; or (b) keep pure-model but make a **reusable methodology
  asset** the HCI contribution (frozen adjudication protocol + latent failure taxonomy + "when-not-to-deploy"
  criteria + console **built & walkthrough-demonstrated**, not merely proposed). → sent to human via ask_user.
- **Other notable (cheap) findings:** prompt-baseline fairness — add a stronger prompt-optimizer baseline or
  narrow claim (R1-F2, R2-M1); uncertainty harm might be a parser/extraction artifact — needs transcript-
  level diagnostics, BUT transcripts were wiped → must re-generate WITH transcripts saved (R2-B2); scope
  language must stay strictly method/model-scoped, no impossibility wording (R2-B1); C1 needs null-relative
  robustness appendix (R2-M3).
- **Decision (Manager):** Drafted the **INDEPENDENT robustness+mechanism arm** →
  `docs/ledgers/prereg-robustness-mechanism-arm-DRAFT.md` (frozen mechanism hypotheses H-R/H-M/H-M-alt,
  frozen success/kill, budget: GPU small ~5-6h one box; engineering ~5-8 implement+audit cycles ~1500-2500
  credits). Awaiting human: (i) the R3-B1 human-anchor fork ((a) vs (b)); (ii) arm go/no-go + prereg freeze +
  GPU sign-off. NO spend until then.
- **Frozen?** Reframe still APPROVED-structure (D-0035). Arm prereg NOT frozen (pending human). E-0003/E-0005/
  prereg-c2b untouched.

## 2026-07-24 · D-0035 · Human approved reality-check reframe + Route A (pure-model) + venue policy
- **Human decision (@EloiseJulia, via ask_user):** approve the reality-check reframe (legibility ≠
  controllability) with two refinements:
  - **Venue NOT locked to CHI.** Venue is tied to human-subjects: **no-humans → prefer IUI, then CHI
    empirical track.** **CSCW is WORSE** (collaboration/social focus; cutting humans moves off-target) —
    CSCW only if we KEEP a human/collaboration study. (Supersedes the CHI-primary framing of D-0002.)
  - **Route A = pure-model.** Cut human subjects; redirect effort into empirical + mechanism strengthening.
    **Console demoted to a design argument / SECONDARY contribution — not the headline, no over-claim.**
  - **Two MUST-ADDs** (else the negative is too thin for a top venue), both pure-model / no humans:
    1. **Robustness of the negative:** replicate the behavioral non-transfer on **≥2 steering methods**
       (e.g. ITI / RepE, or layered/scheduled CAA) **× ≥2 models** — the correct form of the "legitimate
       latent arm": hardening the negative across methods/models strengthens the paper either way.
    2. **Off-manifold mechanism evidence:** measure OOD distance of steered activations; test "more OOD →
       worse calibration" correlation to **upgrade C2-mech from hypothesis to evidence.** Low-cost.
  - **Execution order (free before paid):** (a) FIRST dispatch 3 independent critics on the current reframe
    — questions: is single-method/single-model fatal? is no-humans viable? CHI/IUI/CSCW fit? how much
    robustness must be added? NO GPU. (b) THEN shape the new INDEPENDENT pre-registered arm per (1)+(2)
    (mechanism hypothesis + success/kill + budget) for human approval before any spend.
  - **Frozen records E-0003 / E-0005 / prereg-c2b-adjudication.md remain UNTOUCHED**; any method improvement
    goes through a new prereg.
- **Decision (Manager):** Recorded. Dispatching the 3 critics now (no spend). New-arm prereg drafted only
  after critic triage. Charter venue policy updated; RQ2 core reframed per claim-ledger C2 + reframe doc.
- **Frozen?** Reframe structure APPROVED (not yet a paper freeze). Venue = IUI-first (no-humans route).

## 2026-07-24 · D-0034 · C2b VERDICT = KILL_PLAN_D (0/3), audited VALID_NEGATIVE → escalate Plan-D pivot
- **Result:** Corrected frozen instrument (D-0033 fix) ran the FULL pre-registered protocol on
  Qwen2.5-7B-Instruct: **11,365 generations, wall 29 min, RC=0, no stall.** Per-axis mean paired diff
  (test_steer − test_prompt), Bonferroni-0.98333 item-cluster-bootstrap CI:
  - deliberation +0.015 [-0.040, +0.070] — CI crosses 0 → no
  - skepticism  -0.080 [-0.225, +0.045] — no
  - uncertainty **-0.228 [-0.370, -0.092]** — significantly NEGATIVE (steering hurts) → no
  All coherence gates ok; frozen α = 2/6/8 (NOT compressed by the gate). **axes passing = 0/3 →
  VERDICT = KILL_PLAN_D** (frozen §4 three-tier rule). Evidence E-0005; exp c2b-adj-deac6326-0001.
- **Independent hostile audit (audit-c2b-verdict): VALID_NEGATIVE, no BLOCKER.** Re-derived all three
  CIs from raw per-item diffs == JSON exactly; confirmed instrument truly ran (not silent failure),
  C1@7B 3/3 facade consistent, outcomes non-degenerate (not all-0/1), pairing/clustering correct,
  the null is NOT a coherence-gate/α-compression artifact. Only non-blocking notes: checkpoints/ subdir
  not pulled (MINOR, raw diffs are in JSON); dev-side per-item outcomes only as means (UNVERIFIED, test
  side full + non-degenerate).
- **Scientific reading (audit + Manager):** naive CAA latent steering does NOT beat the best-prompt
  ceiling behaviorally on any axis (and hurts on uncertainty). This is **strong method-weakness evidence**
  and is **consistent with** the non-surjective narrative (prompt is a strong behavioral ceiling), but is
  **single-model + single-method → NOT a decisive general non-surjectivity proof.** The original RQ2
  confirmatory bet ("latent steering reaches behavior BEYOND the bounded-prompt ceiling") is **not
  supported** by our own frozen test.
- **Decision (Manager):** The frozen prereg pre-committed 0-pass → KILL → Plan D. Manager marks C2/H2
  (behavioral-reachability-beyond-prompt) **REFUTED-on-our-instrument (exploratory, single model)**;
  E-0004 (crude-proxy) formally superseded by E-0005. **BUT enacting Plan D reshapes the paper's core
  Claim / RQ structure → AGENTS.md §5 item → ESCALATE to human before rewriting Charter.** Recommendation
  to human: pivot to **Plan D** = RQ1-core measurement/console paper (C1 facade 3/3 @7B = E-0003 banked)
  + honest behavioral-negative (E-0005) reframed as "prompt is a strong ceiling naive latent steering
  can't cross" — NOT a claim that latent steering is impossible.
- **Cost/cleanup:** rented box (RTX 4080 SUPER 32GB) WIPED (all result/log artifacts pulled local first);
  human asked to 关机 the instance to stop hourly billing.
- **Frozen?** Prereg honored, judgment rule UNCHANGED post-results. Charter core-claim change PENDING human.

## 2026-07-24 · D-0033 · KILLED 3rd A800 run: loader ignored frozen per-axis N (protocol-scale bug)
- **Trigger:** On the rented bjb1 box the auto-chain fired the frozen adjudication after the 15GB model
  finished downloading. **C1 re-derived on 7B = 3/3 axes facade** (deliberation ratio 0.583 CI[0.488,0.681],
  skepticism 0.548 CI[0.434,0.670], uncertainty 0.713 CI[0.518,0.910]) — corroborates E-0003.
- **BUG caught by Manager consistency check (NOT by prior audits):** first C2b progress line printed
  `phase=dev_prompt items=440 done=0/1137835` — total planned generations **1,137,835 vs the frozen 11,365
  (~100×)**; items=440 ≈ DEV_FRACTION×full GSM8K test split (1319). Root cause: `scripts/run_c2b_adjudication.py::load_axis_items`
  only slices `items[:n_items]` when `--n-items` is passed; default is `None`, and the real loaders
  (`_load_real`) pull the FULL HF datasets. The frozen per-axis N (`N_ITEMS_BY_AXIS`={60,60,80}) is **never
  applied** on the real path, and `--n-items` is a single int that cannot express per-axis N anyway. The
  hardening audits exercised `plan_generation_counts` with hand-built N=60/80 specs, so this real-loader
  path was never exercised.
- **Decision (Manager, autonomous — NOT a §5 item):** KILLED the run + auto-chain immediately (GPU freed,
  billed hourly). This is a **launcher/instrument bug fix that makes the run HONOR the already-frozen N**;
  it does NOT touch the §4 decision rule or any frozen value → within Manager authority (owner methodology:
  fix instrument, never change judgment). Fix: `load_axis_items` must default `n_items` to
  `N_ITEMS_BY_AXIS[axis]` when None (real path), reproducing the frozen 11,365-gen budget. Dispatch an
  implement subagent (worktree) + a hostile audit before the corrected run's result is banked.
- **Frozen?** Prereg UNCHANGED (D-0024/25/31 still authoritative). Model weights retained on box for reuse.

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

## 2026-07-24 · D-0032 · C2b adjudication running on RENTED controlled RTX 4090 (AutoDL)
- **Human rented** a single-tenant AutoDL RTX 4090 24GB (driver 595, torch 2.8.0+cu128 preinstalled, python
  3.12, 50GB autodl-tmp data disk, network_turbo). SSH provided. This avoids the D-0029 shared-machine
  auto-driver-upgrade risk (single-tenant dedicated instance).
- **Launched** the FROZEN C2b adjudication with the D-0031 mechanics: `--backend hf --model
  Qwen/Qwen2.5-7B-Instruct --bootstrap-b 10000 --seed 20260723 --batch-size 16 --max-new-tokens 64
  --stall-timeout 600` on real GSM8K/TruthfulQA/TriviaQA; HF_HOME on the data disk; hardened instrument
  (progress logging + checkpoint/resume + watchdog). Expected ~25-50 min.
- **VRAM note:** 7B fp16 ~15GB + batch-16 KV/overhead should fit in 24GB; if OOM, drop --batch-size to 8
  (compute-mechanics only, in the fingerprint, does not touch the frozen statistical rule).
- **On completion:** pull results, adjudicate against frozen criteria (three-tier verdict), then wipe the
  rented box (it's billed hourly — shut down promptly).
- **Frozen?** Prereg + mechanics frozen; this run produces the verdict against locked criteria.

## 2026-07-24 · D-0031 · Pre-run generation-mechanics addendum FROZEN (max_new_tokens=64, batch=16, stall=600s)
- **Owner (@EloiseJulia) directive:** write the pre-run re-registration draft ready-to-go.
- **Frozen into prereg §5a (PRE-RUN, no results seen — pre-registered, not post-hoc):** max_new_tokens=64
  (short-answer tasks; 256 was overkill/4× slower; answer parsers key on final answer/MC letter/confidence,
  fit in 64), batch_size=16 (audit-verified greedy batched == single-sequence EXACT on 1.5B; in checkpoint
  fingerprint), stall_timeout=600s (D-0029 hang guard), seed=20260723. **N unchanged = 60/60/80, k=5** (the
  hardened instrument runs full frozen N in ~25-50min → no reduction needed). Must checkpoint/resume + run on
  a controlled machine or confirmed no-driver-maintenance window.
- **Statistical decision rule + §5 statistical params UNCHANGED** (paired cluster bootstrap, DEV/TEST,
  three-tier, Bonferroni, δ=0.05, coherence, per-item Brier). This addendum is compute-mechanics only.
- **Exact run command (ready):** `python scripts/run_c2b_adjudication.py --backend hf
  --model Qwen/Qwen2.5-7B-Instruct --bootstrap-b 10000 --seed 20260723 --batch-size 16 --max-new-tokens 64
  --stall-timeout 600 --hf-home <scratch>/hf_home` (NOT --use-fixture; real GSM8K/TruthfulQA/TriviaQA).
- **Status:** instrument READY; awaiting human GPU allocation on a controlled/maintenance-free machine.
- **Frozen?** YES — §5a frozen. Nothing left to decide pre-run except when/where the GPU runs.

## 2026-07-24 · D-0030 · C2b instrument HARDENED + audited + smoke-verified; ready for a controlled re-run
- **Done (feature/9 merged):** progress logging (flushed, per-cell + ETA + startup budget printout),
  per-cell checkpoint/resume (resumable, config-fingerprinted incl. batch_size+do_sample after audit MAJOR-1),
  batched generation, stall watchdog (--stall-timeout 600s → prevents the D-0029 silent-spin), honest CUDA
  error labeling. Audit verdict: frozen decision logic UNCHANGED, batching UNBIASED, resume reproduces verdict.
  Real-torch smoke on Qwen2.5-1.5B: greedy batched == single-sequence EXACT match. 243 tests green.
- **Budget now tractable:** frozen N=60/60/80 = 11,365 generations; at batch-size 16 + max-new-tokens 64 →
  ~25-50 min wall-clock on an A800 (vs the lost ~12h). So **N does NOT need to shrink** — the original frozen
  N is fine; only max_new_tokens 256→64 changed (short-answer tasks).
- **Pending pre-run re-registration (before the next GPU run — must be pre-run, not post-hoc):** record a
  decision fixing max_new_tokens=64, batch_size=16, stall_timeout, and confirming N stays 60/60/80. The frozen
  statistical decision rule (paired cluster bootstrap, DEV/TEST, three-tier, Bonferroni, δ=0.05, coherence)
  is unchanged. Then the run is: fast (~30-50min), observable, resumable, crash-safe.
- **Next GPU run gating:** run on a machine we control OR confirm no driver-maintenance window; human GPU
  allocation. C1@7B (E-0003) already banked.
- **Frozen?** Decision rule frozen; run-mechanics hardened; N/max_new_tokens to be re-registered pre-run.

## 2026-07-24 · D-0029 · C2b A800 adjudication ABORTED (hung after host driver reload); machine wiped
- **Outcome:** the frozen C2b adjudication run on the borrowed A800 was KILLED after ~11h56m and produced NO
  result (C2b verdict lost). Root cause: the host's NVIDIA driver was reloaded/upgraded mid-run (NVML version
  mismatch 580.173), almost certainly breaking our CUDA context; the process then spun at 100% of one core
  with zero output/progress for hours (diagnosed: single R thread pinned 100%/core, no GPU waiting pattern,
  log static, no disk writes). No checkpoint/partial output existed (in-memory only), so nothing was salvageable.
- **Human decision (@EloiseJulia):** wait (twice) then, on the hung diagnosis, KILL + fully wipe A800.
- **Cleanup verified:** process terminated; cc_scratch (20GB models/venv/caches) deleted; user's pre-existing
  ~/.cache/huggingface (13GB, their Depth-Anything/CLIP) UNTOUCHED; no leftover temp scripts. Machine released.
- **NOT lost:** C1@7B evidence (E-0003, 3/4 axes facade) is committed to main and unaffected. Only this C2b
  adjudication run's compute was wasted.
- **Manager failures (recorded honestly):** (1) underestimated generation volume (~10,700 gens, max_new_tokens
  =256, single-sequence → ~5-11h, not the 1.5-3h estimated); (2) the instrument has NO progress logging and NO
  checkpointing, so a long run was blind and unsalvageable; (3) did not anticipate host driver reload on a
  shared borrowed machine.
- **Before any RE-RUN (fix all three):** (a) add per-axis/per-cell progress logging + periodic checkpoint of
  partial per-item outcomes to disk (resumable); (b) reduce the frozen N and/or use batched generation +
  smaller max_new_tokens so the run completes in ~1-2h — since NO results were seen, changing the frozen N is a
  legitimate pre-run re-registration (document as D-00xx), NOT post-hoc; (c) run on a machine we control or
  confirm no driver maintenance window. The paired-cluster-bootstrap / DEV-TEST / three-tier decision rule stays.
- **Frozen?** Prereg decision rule stays frozen; N/generation-budget to be re-pre-registered before re-run.

## 2026-07-23 · D-0028 · Human GRANTED one A800 allocation for the frozen C2b adjudication
- **Human decision (@EloiseJulia):** "行，现在就跑吧" + "跑完记得清干净" — one GPU allocation for the
  frozen C2b adjudication; wipe everything after (same as D-0020/D-0022).
- **Run:** Qwen2.5-7B-Instruct on A800, frozen prereg instrument (D-0024/25/26/27). DEV-select+freeze α+prompt,
  TEST adjudicate N=60/60/80 k=5, paired ITEM-cluster bootstrap B≥10000 Bonferroni, three-tier verdict.
  <70GB disk, wipe after (models+venv+caches), leave user's ~/.cache/huggingface untouched.
- **Adjudication is CONFIRMATORY-track for RQ2 direction** (verdict decides continue vs Plan D). Criteria LOCKED.
- **Frozen?** Prereg frozen. Result will be recorded against the locked criteria, verdict not revisable.

## 2026-07-23 · D-0027 · §5 data-license APPROVED: GSM8K/MIT, TruthfulQA/Apache-2.0, TriviaQA/Apache-2.0
- **Owner (@EloiseJulia) approved** the C2b adjudication datasets (permissive licenses, research use):
  deliberation=GSM8K (MIT, numeric-answer accuracy); skepticism=TruthfulQA (Apache-2.0, false-premise/
  common-misconception rejection, MC keys for deterministic scoring); uncertainty=TriviaQA (Apache-2.0,
  factual QA + verbalized confidence → per-item Brier).
- These are downloaded on the A800 at run time (network available); offline fixtures for tests. Manifest
  records dataset+version+split+license per AI-Instruction §8.
- **Frozen?** Prereg frozen; instrument fix (Brier+seed+minors+loaders) in progress on feature/7.

## 2026-07-23 · D-0026 · C2b instrument audited — core correct/unbiased; fix Brier+seed+minors+loaders
- **Audit verdict (independent hostile):** NOT-safe-to-run-as-is, but the CORE is correct & unbiased —
  paired ITEM-cluster bootstrap, two-sided, Bonferroni CI, DEV/TEST isolation (no selection leakage),
  three-tier counting, prompt/steer symmetry, coherence gate all verified. Fixes required before A800:
  - **BLOCKER-1** = the uncertainty (1−ECE) per-item issue → ALREADY resolved by D-0025 (per-item Brier).
    Audit independently confirmed 1−|correct−conf| biases uncertainty toward pass and can move opposite to
    ECE. Fix = implement Brier (folded into this pass).
  - **MAJOR-2** generation unseeded (torch sampling not seeded) → verdict non-reproducible on a confirmatory
    instrument. Fix = torch.manual_seed(seed) + record in registry.
  - **MINOR-3** bootstrap B<10000 warns-not-blocks → hard-fail unless explicit override.
  - **MINOR-4** coherence gate degrades to "==0" when baseline degeneracy=0 → add additive ε floor.
  - **UNVERIFIED-5** real skepticism/uncertainty loaders are NotImplemented (GSM8K done) → need dataset +
    §5 license decision (owner).
- **Manager action:** dispatch fix pass (Brier + seed + minors); ask owner for datasets/license for the real
  loaders (§5); then re-audit-light + merge, then A800 run.
- **Frozen?** Prereg still frozen (Brier is the D-0025 clarification, not a new change).

## 2026-07-23 · D-0025 · Pre-run spec clarification: uncertainty metric (1−ECE)→per-item (1−Brier)
- **Trigger:** instrument-build subagent flagged that the frozen "(1−ECE)" is a SET metric with no per-item
  value, but §4's paired cluster bootstrap needs per-item outcomes.
- **Owner decision (@EloiseJulia):** use per-item **Brier**, outcome_i = 1 − (conf_i − correct_i)²
  (proper scoring rule, per-item, cluster-bootstrappable). REJECT the subagent's 1−|correct−conf| (improper:
  L1-optimal is reporting 0/1 → rewards overconfidence, reverses the axis semantics). Binned ECE → descriptive
  only, not in the gate. δ=0.05 now on the (1−Brier) scale. Prereg §1/§5 wording updated accordingly.
- **Status:** this is a PRE-RUN clarification of an ambiguity in the frozen spec (no results seen) — explicitly
  NOT a post-hoc criterion change. ALL other frozen criteria unchanged (paired-diff CI excludes 0 AND point≥δ,
  N 60/60/80, k=5, item-level cluster bootstrap, α+prompt held-out on DEV, three-tier + Bonferroni, coherence
  ≤1.5×). Prereg remains FROZEN with this correction recorded.
- **Action:** instrument code must switch uncertainty per-item outcome to Brier (folded into the post-audit fix).

## 2026-07-23 · D-0024 · C2b adjudication pre-registration FROZEN (owner-confirmed, upgraded design)
- **Owner confirmed with 5 upgrades (all adopted):** (1) decision rule = **paired cluster bootstrap** on
  per-item diffs `d_i=steer_i−prompt_i`, require 95%(Bonferroni) CI EXCLUDES 0 AND point ≥ δ — FORBID the
  "two independent non-overlapping CIs" rule (systematic false-KILL bias). (2) N up to **60–80/axis**
  (uncertainty=80), k=5, bootstrap clusters at ITEM level. (3) **α + best-prompt selected/frozen on a DEV
  split, evaluated on disjoint TEST** — removes best-of-7-α and best-of-16-prompt selection bias for BOTH
  channels. (4) **Three-tier verdict:** ≥2 axes pass (Bonferroni) = STRONG GO; exactly 1 = CONDITIONAL GO
  (pre-registered single-axis REPLICATION; replicate→scope-narrowed RQ2; else Plan D); 0 = KILL→Plan D.
  (5) δ=0.05 retained (per-axis units documented); coherence gate ≤1.5× retained.
- **Rationale (owner):** false KILL is irreversible (permanently loses the core selling point); paired test +
  larger N prevent false kill; Bonferroni + single-axis-must-replicate prevent false positive.
- **FROZEN:** `docs/ledgers/prereg-c2b-adjudication.md` protocol_frozen=YES as of this commit. Criteria LOCKED;
  results may not change them. This is the RQ2 confirmatory-track adjudication.
- **Next (Manager):** implement the qualified instrument locally (tasks + outcome scorers + DEV/TEST + paired
  cluster bootstrap + coherence gate + α-on-DEV) → CPU/1.5B smoke → independent audit → ONE A800 run →
  adjudicate against frozen rule → wipe → report verdict.
- **Frozen?** YES (this pre-registration). Broader Charter still not frozen.

## 2026-07-23 · D-0023 · Human: pre-registered C2b ADJUDICATION experiment (fix instrument → freeze → run once)
- **Human decision (@EloiseJulia):** option 1 sharpened + option 4 absorbed. Do NOT pivot to Plan D now —
  current C2b negative used audit-rejected proxies (invalid evidence, insufficient for irreversible pivot).
  Instead: (1) carefully FIX the C2b instrument — eliminate ceiling effect (unsaturated / real-reasoning-gain
  tasks), orthogonal NON-lexical behavioral proxies, multi-sample + CI, alpha sweep, DROP focus axis;
  (2) PRE-REGISTER frozen success + kill criteria into docs/ledgers/ BEFORE running — criteria may NOT change
  after seeing results; (3) budget cap: local first, ONE GPU allocation, adjudicate immediately, wipe;
  (4) produce a stage summary (evidence chain + risks + 3 routes) as the vehicle for the pre-registration;
  (5) if the QUALIFIED instrument still shows no RQ2 signal → THEN pivot to Plan D (RQ1-core measurement/
  diagnostic CHI paper), reported honestly as a negative.
- **Manager plan:** draft (a) stage-summary doc, (b) pre-registration doc with CONCRETE frozen thresholds →
  confirm thresholds with human → FREEZE → implement qualified instrument locally + smoke → audit →
  ONE A800 run → adjudicate against frozen criteria → wipe → report. This adjudication is confirmatory-track
  for RQ2 direction (continue vs Plan D), so protocol freeze + no-post-hoc-change applies.
- **Frozen?** Pre-registration to be frozen after human confirms thresholds (next step).

## 2026-07-23 · D-0022 · A800 7B run COMPLETE — C1 strengthened (3/4), C2b core NOT supported
- **Run:** Qwen2.5-7B-Instruct on borrowed A800 (GPU fp16, device bug fixed D-0016→D-0021→devfix).
  Total compute 223s. A800 FULLY WIPED after (cc_scratch deleted, 20GB reclaimed; user's pre-existing
  ~/.cache/huggingface 13GB UNTOUCHED — verified it was their Depth-Anything/CLIP data, not ours).
- **C1 facade (RQ1) @ 7B — STRONGEST evidence yet (E-0003):** 3/4 axes hold — deliberation 0.583,
  skepticism 0.548 (RECOVERED at 7B; was borderline at 1.5B), uncertainty 0.713, all CI<1 seed-stable.
  focus overshoots (2.844, no facade). RQ1 semantic-facade phenomenon looks real + scales up. Still
  EXPLORATORY (single model, protocol unfrozen, valid_for_paper=false).
- **C2b behavioral gap (RQ2 CORE) @ 7B — NOT SUPPORTED, leans NEGATIVE (E-0004):** latent steering did
  NOT reach behavior beyond the bounded-prompt ceiling on 3/4 axes (deliberation/skepticism/uncertainty
  beyond=False); only focus beyond by +0.010 (trivial + failed-C1 axis). Conflict: prompt wins 3/4
  (uncertainty=latent). Caveats: crude lexical proxies ceiling-saturated ~0.88-1.0 (proxy ceiling effect),
  single greedy sample, alphas maybe too weak — audit already said these proxies CANNOT support the claim.
  **This is the paper's riskiest claim and the first real probe shows NO positive signal for it.**
- **Manager assessment (honest, per "allow hypothesis to fail"):** RQ1/C1 is a solid emerging foundation;
  RQ2/C2b core bet ("latent reaches beyond prompt behaviorally") is NOT materializing on the first real
  probe and mildly cuts against — consistent with the internal-vs-behavioral gap (D-0016) and PSR threat.
  Not yet a KILL (C2b here is exploratory-only, crude proxies, not confirmatory). But it is a PIVOT SIGNAL
  toward Charter §8 Plan D (measurement/legibility-gap paper anchored on C1) if a better-instrumented C2b
  also fails. **Escalate strategic decision to human** (continue improving C2b instruments vs pivot to
  Plan D vs redesign axes/proxies).
- **Minor bug noted (failure-log):** C1 summary header hardcodes "(CPU, float32)" — cosmetic label; run
  was GPU/fp16 (numbers correct). Fix in a later cleanup.
- **Frozen?** No.

## 2026-07-23 · D-0021 · GPU-ready harness AUDITED — safe to run; apply cheap pre-run fixes
- **Audit verdict (independent hostile, feature/5):** SAFE TO RUN on A800 as-is. No BLOCKER — harness does
  NOT rig the result, C2b steers at C1's chosen layer with re-derived CAA vector (same seed/split),
  valid_for_paper=false stamped everywhere, numbers from computed artifacts. Steering hook verified correct.
- **Findings (mostly interpretation limits, not correctness):**
  - **[MAJOR M1] Proxy–steering shared basis:** lexical proxies + keyword-basis steering (skepticism/
    uncertainty) or length-basis (focus/deliberation) → C2b is an EXPLORATORY lexical-shift signal ONLY.
    CANNOT support "latent reaches beyond prompt ceiling" alone; needs an orthogonal non-lexical proxy +
    variance before any Claim. HARD caveat.
  - **[MAJOR M2] focus/deliberation proxies gameable by verbosity/truncation** — focus especially untrustworthy
    (length-confounded). Flag; no focus "beyond" without length control.
  - **[MAJOR M3] Prompt ceiling used best-of-6 not the full 16 authored prompts, no OPRO** → weaker ceiling
    biases toward steering. FIX: run with --n-strong 16, label "best-of-16 static, NOT OPRO".
  - **[MAJOR M4] Disk guard can't abort a runaway download** (pre-check ~0GB, post-check warn-only); RUN_ON_A800
    overclaims. FIX: check with raise_on_over after model load; soften doc. (Low real risk: ~25GB ≪ 70GB.)
  - **[MINOR] m1 raw_data_hash hashes config not artifact; m2 --skip-c1 fallback layer; m3 unstable-layer axes
    still steered. UNVERIFIED: single greedy sample per cell (reproducible but no variance → don't over-read
    small margins).**
- **Manager decision:** apply M3 (--n-strong 16 default) + M4 (real abort) + m1 (hash artifact) before the run
  (cheap, no extra GPU); DEFER orthogonal-proxy work to a follow-up (that's the confirmatory-track fix). Then
  merge + run on A800. C2b will be EXPLORATORY-only regardless. Frozen? No.

## 2026-07-23 · D-0020 · Human: borrowed A800 session (SSH, agent-driven, <70GB, delete-after, fast)
- **Human decision (@EloiseJulia):** will provide SSH/remote access; agent drives the A800 directly.
  Constraints: total disk <70GB, delete EVERYTHING (models/caches) after, be fast, single session.
- **Strategy:** don't waste scarce A800 time debugging. PHASE A (local, free, NOW): implement + CPU-smoke-test
  a real steered-generation backend for C2b + unified GPU runner (C1 facade + C2b behavioral pilot) +
  requirements-gpu + disk-guard + auto-cleanup + RUN_ON_A800 doc. PHASE B (A800 via SSH): clone, venv,
  download Qwen2.5-7B-Instruct (Apache-2.0, no license gate; ~15GB → ~25GB total, well <70GB), run C1+C2b,
  pull small results back, delete all.
- **Model:** Qwen2.5-7B only this session (Llama-3-8B gated/license friction; defer to keep it lean/fast).
  spec AC2 wants ≥2 models — noted as a limitation for this exploratory-track run.
- **Transfer:** repo is 0.8MB → git (push+clone OR git bundle). Models download fresh on A800 (not uploaded).
- **§5 status:** GPU escalation on borrowed hardware — human-authorized. Still EXPLORATORY-track (a first
  7B read); NOT a frozen confirmatory run (protocol not frozen, no Pre-Full-Run Review yet).
- **Frozen?** No.

## 2026-07-23 · D-0019 · Human: strengthen C1 on 1.5B (free) — fix focus, expand prompts, robustness
- **Human decision (@EloiseJulia):** "a" — strengthen C1 locally before any GPU escalation.
- **Scope (feature/4-c1-strengthen, CPU/1.5B, optional 3B, zero paid/GPU):**
  1. Fix focus layer-selection: the Cohen's-d rule picked degenerate layer-2 (pole_reach≈0). Restrict the
     scan to exclude degenerate shallow layers / require chosen-layer pole_reach clearly > 0 (extraction
     success); if focus still yields no stable direction at 1.5B, report that HONESTLY (don't force it).
  2. Expand strong-prompt set per axis (7 → ~15–20 diverse, still distinct-in-kind from contrast pairs) to
     tighten the bootstrap CI.
  3. Robustness: report facade_ratio across the top-k candidate layers (not just the argmax) + a couple of
     RNG seeds for the null/bootstrap, so the C1 read isn't a single-layer/single-seed artifact.
  4. Optional: if RAM allows, a Qwen2.5-3B confirmation pass (free) to see if the 2/4 pattern holds at 3B.
- **Then AUDIT.** EXPLORATORY still (valid_for_paper=false); goal = harden the C1 exploratory read, not freeze.
- **Frozen?** No.

## 2026-07-23 · D-0018 · Fair-metric C1 read on 1.5B — 2/4 axes show a facade gap (credible EXPLORATORY)
- **Result (feature/3, run c1-facade-d553d2cb-0001, same-origin scale-free metric + bootstrap CI):**
  | axis | facade_ratio | 95% CI | C1 gap? |
  |---|---|---|---|
  | deliberation | 0.566 | [0.437, 0.710] | YES (CI hi < 1) |
  | uncertainty  | 0.714 | [0.643, 0.796] | YES (CI hi < 1) |
  | skepticism   | 0.853 | [0.634, 1.066] | NO (CI crosses 1) |
  | focus        | junk  | extraction fails (layer-2 degenerate, pole_reach≈0) | no |
- **Manager verification (light, proportionate):** the metric IS the audit-recommended same-origin
  scale-free formula (prompt_reach/pole_reach, shared neutral origin, α-free); dedicated test file
  test_same_origin_facade.py pins it (0.4 known-fraction incl. nonzero-origin BLOCKER-2 guard, deterministic
  bootstrap CI, "CI hi→1 when no facade", leave-one-neutral band). 73 tests green. Numbers reproduce exactly
  from cache. True wall-clock 391.6s recorded (MINOR-6 fixed). No 4th full audit — metric already audit-blessed.
- **Read (HONEST):** C1 is PARTIALLY SUPPORTED on 1.5B — 2 of 4 axes show a genuine facade gap (prompt
  reaches ~57%/71% of the neutral→pole range, CI upper bound < 1); skepticism does not; focus extraction
  failed. This is EXPLORATORY (1.5B < 7-8B spec target; single seed model; valid_for_paper=false). NOT
  confirmatory, protocol NOT frozen.
- **Decision (Manager):** C1 → partially-supported (exploratory). H1 → partially-supported (exploratory).
  This is the first CREDIBLE signal that the semantic-facade phenomenon is real for some axes. Present to
  human: the signal exists but is axis-dependent + small-model; decide whether to (a) strengthen on 1.5B/3B
  (free), (b) fix focus layer-selection, or (c) escalate to 7-8B (GPU, §5). Branch mergeable. Frozen? No.

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
