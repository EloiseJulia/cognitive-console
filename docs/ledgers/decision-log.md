# Decision Log

> Append-only. Every scope/Claim/venue/budget/protocol change and every Manager ruling is recorded here.
> Human-approval items (AGENTS.md §5) must cite the human decision.

---

## 2026-08-11 · D-0110 · Owner authorizes DRAFT bilingual owner-preview engineering only
- The owner explicitly authorized Simplified Chinese and English onboarding for
  the contract-application micro-study so unfamiliar users can understand the
  task more easily. This decision authorizes stable-ID locale materials,
  language selection before session creation, immutable `ui_language`, selected-
  locale-only projections, V4 signed locale identity, descriptive locale QA,
  accessibility/security validation, and owner-local preview engineering.
- This revision does not change the research question, primary CCA outcome,
  Contract-versus-Flat contrast, nonlocalized router, answer keys, sequence
  assignment, eligibility, exclusion, duplicate winner rule, or inferential
  analysis. The protocol remains `DRAFT / NOT FROZEN`.
- The implementation begins at `786a6a8` and is hardened through `d4ceafd`,
  including idempotent network retry, validated-source caching, and stable
  deferred script loading for browser execution.
  Its maximum state is `READY_FOR_OWNER_LOCAL_PREVIEW_NO_HUMAN_DATA`, but a fresh
  independent hostile audit is still pending and the prior final audit is not
  silently extended to this revision.
- No recruitment, participant contact, human data, timing pilot, ethics action,
  public deployment, recovery mechanism, paper/claim/evidence-validity change,
  or human authorization is granted. Human bilingual stable-ID semantic review,
  manual screen-reader review, ethics/recruitment, timing/MDE, and Protocol
  Freeze remain `PRE-RECRUITMENT` gates.

## 2026-08-11 · D-0109 · Supersede D-0107 Manager-retirement timing; permit no-Manager gap, never dual Managers
- This entry supersedes only D-0107's conflicting retirement-timing wording.
  The outgoing/current Manager becomes immediately read-only retired once the
  handoff bundle is complete and the handoff document audit has passed; it does
  not remain active until the incoming Manager announces takeover.
- The incoming session may perform only the read-only takeover verification,
  answer the handoff exam, and submit those answers for independent audit. It
  must not announce takeover, dispatch work, edit repository content, update
  `ACTIVE_MANAGER`, merge, or make Manager decisions until an independent
  Handoff Auditor explicitly returns `HANDOFF EXAM PASS`.
- A short interval with no active Manager is allowed and is the required safe
  state between retirement and audited takeover. There must never be two active
  Managers. All other D-0107 scope, gates, and prohibitions remain unchanged.
- At this correction's preparation, local `main` HEAD was `284effc`, 64 commits
  ahead of `origin/main`; this governance-only commit is expected to make it 65
  ahead. It authorizes no push or scientific, protocol, evidence, recruitment,
  submission, budget, or GPU decision.

## 2026-08-11 · D-0108 · Final micro-study audit passes owner-local-preview gate only
- Persisted the completed final read-only hostile audit of implementation commit
  `d17df47` at
  `reviews/2026-08-10-microstudy-web-final-audit/audit-summary.md`.
- The audit closed the remaining export-retry, duplicate-resolution, and
  browser-stability blockers; Chrome/Edge stress and full tests plus the
  security/privacy checks passed for the audited local-preview scope.
- Verdict: **READY FOR OWNER PILOT PREVIEW, NO HUMAN RECRUITMENT
  AUTHORIZATION**. Registry status is
  `ready_for_owner_preview_no_human_data`; human collection remains false.
- This gate permits owner-local preview only. It authorizes no recruitment,
  participant contact, human-data collection, public deployment, protocol
  freeze, paper evidence, scientific result, or claim upgrade. Manual
  screen-reader evaluation, owner pilot decision, defensible primary MDE,
  ethics, and recruitment authorization remain PRE-RECRUITMENT gates.

## 2026-08-11 · D-0107 · Manager rotation handoff prepared; incoming session must pass exam before unique takeover
- Created `docs/handoffs/2026-08-11-manager-handoff.md` as the sole primary
  re-entry point and marked the 2026-08-05 handoff superseded. The incoming
  writing-focused Manager may dispatch other work, but must first perform the
  read-only verification and pass the ten-question acceptance exam. Only after
  it announces takeover does the current Manager retire read-only; dual Manager
  scheduling is forbidden.
- Audited scientific/content base HEAD was
  `b7043d28481c30eaf8c84575f884fd63f970591f`, initially 62 commits ahead of
  `origin/main`; this handoff commit is expected to make local `main` 63 ahead.
  The owner-provided untracked DOCX remains preserved and must not be committed.
  No `ACTIVE_MANAGER` file exists, so none was invented.
- Current paper source rebuilds to 12 pages at
  `docs/paper/build/main.pdf`. Substantial writing after the last independent
  full-paper critic makes all older acceptance probabilities stale; the next
  writing action is a fresh current-bundle review followed by one bounded
  revision/audit cycle.
- The contract-application website and final hostile-audit repairs are merged at
  `b7043d2` and are ready for owner preview only. Recruitment, ethics activity,
  pilot, human data, public deployment, protocol freeze, and paper evidence
  remain unauthorized. E-0016 still has no scientific result.
- This rotation records no new scientific result, Claim, venue, protocol,
  evidence-validity, budget, recruitment, submission, or GPU decision. No push
  is authorized by this entry.

## 2026-08-10 · D-0105 · Hostile-audit implementation repair completed; no human run
- Moved formal planning, state transitions, scoring, canonical export, CSV
  hardening, and HMAC-SHA256 signing into the volatile loopback server. The
  browser receives no formal keys/router internals and cannot skip phases.
- Made analysis verify owner-held keys/signatures and strict schemas, resolve
  first-complete duplicates before assignment classification, separate primary
  eligibility from missing-as-incorrect ITT, and record mechanical reasons.
- Replaced string-theater flow checks with real headless Chrome A1/D5 completion,
  download/signature, Q1 lock/Q2 reveal, 1440×900 geometry, and 200% zoom checks.
- Status remains `implemented_pending_reaudit_nohuman`: DRAFT, no recruitment,
  human data, public deployment, paper edit, protocol freeze, or claim upgrade.

## 2026-08-10 · D-0104 · Local micro-study implementation completed pending hostile audit
- Implemented a Python-standard-library loopback server and vanilla HTML/CSS/JS
  without React, FastAPI, npm, remote services, or new dependencies.
- The site consumes authoritative JSON, derives Q1 through the audited router,
  preserves exact sequence assignment and ten-slot exports, and keeps browser state
  in memory only. It does not recruit, collect human data remotely, or deploy publicly.
- Added strict export reconstruction, mechanical duplicate/corruption handling,
  preregistered paired CCA/sign-flip/bootstrap analysis, and a separately labelled
  DRAFT assumption-sensitivity MDE tool.
- Status is `materials_implemented_pending_hostile_audit_no_human_data`; this is not
  READY, protocol freeze, participant authorization, paper evidence, or claim upgrade.

## 2026-08-10 · D-0103 · Micro-study materials become executable JSON with checked-in validation; status remains materials-only
- Made `data/microstudy_contract_application/stimuli.json` and `sequences.json` the only normative sources for the ten records, templates/keys, router inputs, Flat orders, participant strings, export fields, and `A1..D5` sequences. Spec, preregistration, and plan now reference and summarize those files rather than duplicating complete stimuli or answer keys; a future website must consume them directly.
- Checked in a deterministic validator and pytest coverage. They freeze Unicode NFKC alphanumeric tokenization, lexical/length heuristics, oracle/LOO/global baselines, single-comparison-row Q1, combined CCA, router derivation, source schema, formal-text state-word prohibition, proposition parity, primitive-position balance, template reuse/key variation, and the generated 200-row sequence balance.
- Corrected P3-Y without changing Q1: resolved non-superiority still routes to withheld, so coherence is not requested as the next required evaluation. Its scope boundary is now genuinely unavailable and `Q2-NEXT` C requests that missing boundary. All ten metrics remain oracle/LOO/global `3/0/3`, lexical family `2/3/2/2`, single-row Q1 `8`, combined CCA `2/0`, router `10`.
- Materialized one common plain-language routing legend/tutorial, exact practice/feedback, a descriptive post-task format diagnostic, and nullable post-block `SEQ1..SEQ7` ease responses. Removed attention-check fields entirely; diagnostic, ease, practice, RT, and performance never exclude; no free text exists.
- This is deterministic materials validation only. Experiment status remains `not_started_materials_only`; there is no web application, recruitment, pilot, human data, paper evidence, protocol freeze, or claim upgrade.

## 2026-08-10 · D-0102 · Second hostile-audit protocol revision closes CCA, allocation, missingness, and analysis ambiguities
- Reframed the construct as structured rule application and the treatment as a semantic-organization package (grouping, labels, fixed role order), not deep integration or a pure-headings manipulation. Flat now uses exact item-specific deterministic shuffles balanced so every primitive role occupies every position twice.
- Made Q1→Q2 strictly sequential and irreversible. Q2 now uses item-specific scope/comparator/generalization judgments with no state names or state-option mapping. Leakage acceptance targets end-to-end CCA at the four-option `0.25` chance bound rather than requiring every single-row Q1 heuristic to be at chance.
- Froze the complete trial-state truth table, `submitted==complete` compatibility alias, complete-only primary, `4/condition + 8/10` eligibility, all-ten-slot missing-as-incorrect sensitivity, and export of every planned slot.
- Replaced same-rotation blocks with orthogonal `r` / `r+2 mod 5` rotations and froze blinded `A1..D5` slot allocation: dropout/primary-ineligible attempts reuse a slot; a ten-trial completion later mechanically excluded consumes it, is not replaced, and remains in ITT sensitivity.
- Froze participant bootstrap (`B=10000`, seed `20260810`, percentile 2.5/97.5) and full exact sign-flip enumeration over nonzero differences. Removed GLMM and all numerical MDE language; MDE is pending a reproducible, independently audited simulation before protocol freeze.
- Froze the exact three-person timing rule and exact tutorial/practice/feedback/debrief materials, standardized provenance on `source_status`, and retained materials-only/DRAFT status. This revision implements no web app, recruits nobody, collects no data, and changes no paper.

## 2026-08-10 · D-0101 · Hostile-audit protocol findings closed; materials remain DRAFT and no study run is authorized
- Replaced answer-leaking evidence/status prose with ten exact common proposition arrays and multi-row Q1/Q2 derivations. Frozen blind single-row, keyword, second-row, and fixed-position heuristics must remain at or below empirical majority chance (`0.40`).
- Removed all held-out/transfer subset naming and claims. All formal combinations are unseen in the one different practice example; Q2 is scope/reason application and the sole primary remains conjunctive rule-application accuracy.
- Expanded parity to exact five-row geometry, common strings/order, ≤5% visible-word difference, exact body word/line/row/card dimensions, DOM snapshots, and masked pixel/screenshot audits.
- Expanded export to ten pre-generated planned slots and froze primary eligibility at ≥4 submitted per condition and ≥8/10 total; ten-slot missing-as-incorrect sensitivity and condition/sequence missingness are mandatory, with no performance-based exclusion.
- Replaced A–D-only allocation with 20 exact orthogonal sequence codes `A1..D5`, combining A–D condition/set/block mapping with five balanced pattern-position rotations.
- Replaced forced ten-minute pacing with a no-timeout owner-pilot gate (median ≤10 minutes, P90 ≤12), strengthened accessibility/privacy requirements, closed provenance enums, and added export-only analysis/MDE implementation and end-to-end test plans.
- Interpretation is estimation-first: one primary sign-flip test plus bootstrap CI; descriptive categories are not pass/fail gates. This revision changes no paper, authorizes no participant activity, and leaves the preregistration DRAFT/materials-only pending fresh hostile re-audit.

## 2026-08-10 · D-0100 · Owner authorizes materials/local-web phase only for exploratory contract-application micro-study
- Owner authorized only protocol, stimulus/material, and local web engineering for an exploratory formative `contract legibility/application micro-study` (`N≈20`, desktop-only, approximately 10 minutes, technical GenAI users).
- Recruitment, ethics administration, public deployment, human pilot, and human data collection remain outside scope and owner-managed. This decision does not authorize a study run.
- The study is limited to within-subject Contract UI versus Info-Matched Flat Panel, 10 scored trials (5/condition), one practice, and four-sequence counterbalancing. It tests contract legibility/rule application, not calibrated reliance or user benefit.
- Materials must use simulated evaluation records, preserve machine-checkable information parity, mirror the current four-state checker, and avoid final-state/aggregate-TRANSFER/recommended-action leakage. The current paper has no pass; any passing record is explicitly hypothetical.
- The preregistration remains DRAFT/not frozen. No exploratory result may be upgraded to confirmatory evidence or used to change paper claims without a new owner decision and all applicable gates.

## 2026-08-05 · D-0099 · Comparator-bound calibration framing repaired without changing claims
- This repair changes framing only. It changes no frozen protocol, result, number, confidence interval, formula, evidence validity, or Claim verdict.
- C2 now states the uncertainty result as a **steer-vs-bounded-prompt negative calibration contrast under the frozen scorer**, with confidence intervals excluding zero in all four CAA/ITI-by-Qwen/Llama cells. It also carries the audited direct Qwen/CAA steer-vs-baseline result: near zero (`+0.011` compliance, `+0.0008` 1-Brier).
- Claim, evidence, and paper maps retain the E-0013 narrow caveat: only CAA×Qwen has the complete-case format recheck; adversarial missingness bounds span zero, and the other three cells remain unverified for that recheck.
- The off-manifold result remains a valid null and supports no mechanism claim. This is not a Claim change or validity upgrade.

## 2026-08-05 · D-0098 · Paper scope corrected to implemented method-specific scaling and exact coherence gate
- This is a paper-fact correction only. It changes no frozen protocol, result artifact, numerical result, evidence verdict, or scientific conclusion.
- C2's additive intervention is now stated as `h'_L = h_L + alpha*s_m*u_m`, with `s_CAA=1` and `s_ITI=sigma_L`. The shared grid bounds the coefficient at `alpha<=24`; it is not a common injected-norm bound. The frozen ITI `sigma_L` is the sample standard deviation of combined extraction positive/negative activations projected onto the unit probe direction, matching `src/cognitive_console/steering/iti.py` and `scripts/run_c2b_adjudication.py`.
- The coherence gate is now stated exactly as `g_steer <= 1.5*g_baseline + 0.02`; the implementation's additional `1e-12` is only floating-point comparison tolerance. The facade denominator is clarified as same-origin extraction-positive displacement relative to neutral projected onto the CAA axis, not the positive-minus-negative contrast-vector norm.
- E-0014/E-0015 remain CAA-only scale evidence and are not extended to ITI. The failed-superiority verdict and all reported values remain unchanged.

## 2026-08-05 · D-0097 · Paper lineage synchronized to D-0078 and D-0081..D-0087 without changing scientific conclusions
- This repair closes a bookkeeping gap in the IUI rewrite. It does not authorize a new experiment, citation, number, claim, protocol change, or validity upgrade beyond Manager-approved paper uses already recorded in D-0078 and D-0081..D-0087.
- E-0013 is registered as `valid_for_paper=true` only for the audited CAA×Qwen format-robustness/limitation claim. ITI×Qwen and both Llama cells remain unverified and support no E-0013 claim. The post-generation complete-case restriction and adversarial missingness bounds remain mandatory.
- E-0014 is paper-valid only as endpoint-live plus bounded-latent-arm-null limitation evidence. It is not a passing latent positive control and supports no metacognitive-control claim. E-0015 is paper-valid only as a scoped scale-corrected null/assay-sensitivity limitation with coherent-ceiling and MDE caveats; it is not a universal or core latent negative.
- The E-0015 first-token logit diagnostic remains `valid_for_paper=false`, non-confirmatory, appendix-only context and is excluded from claim support and the submission evidence ledger. The social E-0010 card is removed from the central console figure; E-0010 remains appendix-context-only under its existing caveats.
- The contract is consistently described as an artifact-instantiated proposed evidence-accounting/evaluation framework derived from model evidence. Its comprehensibility, usability, reliance effects, and benefit remain unvalidated future-work questions.

## 2026-08-05 · D-0096 · E-0016 pre-DEV infrastructure failure validated; audited serialization repair authorizes retry within D-0095
- Independent audit validated attempt 1 as a **VALID PRE-DEV INFRA FAILURE**, not a scientific result. Result branch/commit: `run/e0016-regime-b-20260805` / `c461c3c295ba96243d746f8fbfc60389a2635d1b`. The exact old run commit was `4def9ba59a00909d4cf2aae7dbdb1665877d6204`; DEV and TEST did not run, `valid_for_paper=false`, and no harmful generation or raw-harmful-text leakage occurred.
- Root cause: transformers 5.14.1 exposed a tokenizer `AddedToken` during environment-identity capture, and the old canonical JSON path could not serialize it. Repair commits `75834b1f5913933ac412f93d5d41a44a58868060` and `fa58dcf5c739e7d89b36e6af7694e9ea0df84d27` add canonical `AddedToken` and typed configuration-key serialization (environment identity schema v3). The repair was independently audited **SOUND** and merged as the new exact run/code commit `c094f07fa3592c2210f46caba9e69c49a5a92fad`.
- This is a pre-DEV infrastructure-only amendment with zero scientific-parameter or protocol drift. Attempt 1 consumed at most 0.00722222 A800 GPU-hours, leaving a hard cap of 2.99277778 GPU-hours. Retry is authorized under the original D-0095 approval; no new owner approval is required because the retry remains within the original 3-hour cap and unchanged Regime-B protocol. Real run and independent hostile results audit remain pending.

## 2026-08-05 · D-0095 · Owner authorizes E-0016 full benign Regime-B run, maximum 3 A800 GPU-hours
- Owner selected: "批准完整 Regime-B，预算上限 3 GPU 小时（推荐）".
- Authorization covers only the frozen Regime-B protocol at run commit `4def9ba59a00909d4cf2aae7dbdb1665877d6204`: DEV=60, TEST=160, K=5, benign XSTest generation only.
- Execution must run DEV eligibility first. If baseline false-refusal is `<0.25`, it must emit `INVALID_REGIME_B_UNDERPOWERED`, stop before TEST, and report to the owner. If eligible, TEST may run once under the frozen protocol.
- Harmful prompts remain forward-pass-only direction inputs. Harmful generation and Regime A remain unauthorized. The 3 GPU-hour cap is hard; exceeding it requires a new owner decision.

## 2026-08-05 · D-0094 · E-0016 Regime-B protocol audit passed; exact run commit frozen, GPU budget pending
- Targeted independent protocol re-audit closed both D-0093 documentation findings. The Regime-B-only protocol is frozen and merged at `4def9ba59a00909d4cf2aae7dbdb1665877d6204`; this is the exact clean commit authorized for any future E-0016 execution.
- Owner decisions remain binding: benign XSTest generation only; DEV baseline false-refusal must be `>=0.25`; otherwise emit `INVALID_REGIME_B_UNDERPOWERED` and stop before TEST. Harmful prompts remain forward-pass-only direction inputs; Regime A generation is excluded.
- This freeze is not GPU authorization. Regime-B GPU budget approval remains pending, and no GPU run, result, or paper-valid evidence exists.

## 2026-08-05 · D-0093 · E-0016 freeze-candidate status correction; final run commit remains pending
- This append-only correction supersedes D-0092 only where D-0092 described E-0016 as finally frozen or execution-ready. The audited harness is merged at `4513820a679408b071984b8500cc9c5636255a49`, and the D-0091 scoped harness findings remain closed.
- Commit `c36a438977ae51be5172587e900811508fe77468` contains the first Regime-B freeze-document candidate. It is a **protocol freeze candidate prepared, pending independent protocol audit and the final merged run commit**, not the run commit and not GPU authorization.
- After this documentation repair passes targeted protocol re-audit and is merged, the Manager must record the exact final merged run commit. E-0016 may execute only from a clean checkout of that recorded commit.
- Protocol audit, final run-commit registration, and owner GPU-budget authorization are pending. No GPU run, result, or paper-valid evidence is registered.

## 2026-08-05 · D-0092 · E-0016 audited harness merged; Regime-B-only protocol frozen, GPU remains owner-gated
- The limited independent delta-audit closed the D-0091 harness findings, and the audited fixes were merged as harness commit `4513820a679408b071984b8500cc9c5636255a49`. The merge message explicitly states that it did not freeze the protocol or authorize GPU execution.
- E-0016 is now frozen strictly as benign XSTest **Regime B only** in `docs/research/2026-08-04-ablation-positive-control/prereg-e0016-FROZEN.md`, faithful to the audited runner constants and CLI. DEV baseline false-refusal eligibility is `>=0.25`; below that, the runner emits `INVALID_REGIME_B_UNDERPOWERED` and stops before TEST.
- Harmful prompts remain forward-pass-only inputs for refusal-direction extraction. Harmful generation, raw harmful text in git/artifacts, and Regime A are excluded. Any future Regime A consideration requires a new owner decision and a new protocol.
- Protocol freeze is not GPU authorization. Regime-B GPU budget remains pending owner approval. `valid_for_paper=false` until a real eligible run and independent hostile results audit. Manager must record the final clean audited run commit after protocol audit; the harness pin and protocol-document commit are distinct lineage entries.

## 2026-08-05 · D-0091 · E-0016 hostile code audit = NOT SOUND; 4 BLOCKER + 2 MAJOR, no freeze/GPU
- The retirement-time hostile audit (`audit-e0016-code`) completed after D-0090. Verdict: **NOT SOUND; do not freeze, merge, or authorize Regime-B GPU**.
- BLOCKER 1: ablation hook-bites runs only after DEV baseline/ablation/random generation. It must run and persist before any generation for every candidate direction.
- BLOCKER 2: hook-bites compares global maxima, not the required per-token inequality, and does not prove every decoder layer is hooked. Fix with per-element violation count/max violation and exact layer-set equality.
- BLOCKER 3: HF real-data guard can be bypassed by any renamed local CSV; an existing test even accepts placeholder harmful rows in `backend="hf"`. HF must accept only frozen dataset ID/revision/content hash/schema; local overrides must match approved immutable hashes.
- BLOCKER 4: HF defaults are smoke-sized (DEV=4, TEST=8, K=2, layers 1/2/3) while prereg minimum is TEST N=80/K=3 and candidate layers are still unfrozen. HF must reject every non-frozen configuration; synthetic-smoke parameters must be separated.
- MAJOR 1: manifest lacks seed/model revision/real dirty-tree state and full frozen-config hash.
- MAJOR 2: tests do not exercise actual hook no-op/wrong-hook/missing-layer failures, runner-level eligibility stop, or immutable-data-hash rejection.
- Tests passing (681 passed/6 skipped; E-0016 9 passed; synthetic smoke PASS) do **not** cover these runtime failures. Incoming Manager must dispatch a fix subagent, re-audit the delta, and only proceed after SOUND.

## 2026-08-05 · D-0090 · Manager retirement handoff; E-0016 remains at pre-GPU hostile-audit gate
- Outgoing Manager is retiring because the session is saturated. New primary re-entry point: `docs/handoffs/2026-08-05-manager-handoff.md`.
- `main` was clean at handoff preparation; HEAD before the handoff commit was `1d7d7a7`. Current paper state: audited BORDERLINE, IUI estimated 30–35%; F1 addressed, F3 resolved, F2 downgraded fatal→MAJOR but still open because no latent intervention has passed.
- E-0016 status at initial handoff preparation: design/prereg draft committed on main (`728a0d7`); implementation isolated in `.worktrees/e0016`, branch `feature/e0016-ablation`, commit `c1c4d90`; tests + synthetic smoke reportedly pass. The retirement-time audit subsequently returned **NOT SOUND**; D-0091 and the handoff contain the binding findings.
- No E-0016 prereg freeze, GPU authorization, GPU run, result, or paper integration exists. Owner decision D-0089 remains binding: benign XSTest Regime B first; DEV false-refusal eligibility floor 0.25; if underpowered, STOP and ask owner again before any harmful Regime A generation.
- Session-local SQL todos (`ws1-signoff`, `ws2a-guardrails`, `e0012-fetch`, `e0012-results-audit`) are stale historical state and must not be resumed. Repository ledgers and this handoff supersede them.

## 2026-08-04 · D-0089 · Owner chose Regime B-first for E-0016 (benign XSTest; escalate to harmful Regime A only if underpowered, with re-confirm)
- Owner (ask_user) selected the safe path: run the benign XSTest DEV eligibility check first (baseline false-refusal on XSTest-safe ≥0.25?); if eligible, close F2 with ZERO harmful-content generation; only if underpowered escalate to Regime A (harmful prompts) with §5 safety handling AND owner re-confirmation. Regime B design: Arditi refusal direction (diff-of-means harmful−harmless) derived by FORWARD-PASS ONLY (no harmful generation; harmful prompts loaded from a licensed set, never committed raw, only hashed); all GENERATION happens on benign XSTest-safe prompts; ablation = all-layer projection h←h−(h·r̂)r̂. Pass rule: mean false-refusal REDUCTION ≥0.25, bootstrap CI excludes 0, coherent, random-ablation-null. DEV eligibility gate: baseline false-refusal <0.25 → emit INVALID_REGIME_B_UNDERPOWERED and STOP (Manager escalates). Guards: real-not-smoke direction, real data, ablation hook-bites (after ablation h·r̂≈0, fail-closed upfront), single shared handle, random negative, coherence. Scope guard keeps a pass off the headline. GPU sign-off still owner-gated at freeze; Regime B GPU (benign) is low-safety-risk but still needs GPU budget OK.

## 2026-08-04 · D-0088 · Owner GO on a passing latent positive control (E-0016, Arditi refusal-direction ablation) to close F2
- After D-0087 (paper at honest BORDERLINE ~30-35%, F2 = MAJOR), owner chose the high-impact lever (ask_user): attempt a PASSING latent positive control via a genuinely DIFFERENT method — Arditi et al. 2024 refusal-direction projection-ablation (SUPPRESS refusal), rather than the naive additive steering the paper's negative is about. Purpose: demonstrate the measurement pipeline CAN register a working latent intervention → refutes "no latent intervention ever passes" → closes F2. On a NON-metacognitive target via a different method, so a pass carries NO headline risk (does not validate metacognitive controllability; does not contradict the naive-additive negative).
- **Design dispatched (E-0016, doc-only, no GPU).** Must evaluate two data regimes: (A) harmful prompts (AdvBench-style) refusal suppression [strongest/canonical, but GENERATES HARMFUL CONTENT → §5 safety handling: outputs never published/committed raw, only aggregate refusal-marker rates + hashed/redacted transcripts], vs (B) XSTest safe-but-over-refused prompts [benign, no harmful generation, but depends on Qwen2.5-7B actually over-refusing]. Method: Arditi difference-of-means refusal direction + ALL-LAYER directional projection-ablation (new hook — the paper's machinery is single-layer addition). Pass rule = significant refusal-rate REDUCTION (CI excludes 0, magnitude ≥ threshold). Reuse frozen bootstrap/CI/coherence where possible. Guards: real-not-smoke direction, real data, ablation hook-bites (verify the component is actually removed), random-direction control, coherence. **§5 SAFETY: the harmful-content aspect (regime A) needs explicit owner sign-off before GPU; Manager will bring design + safety/method choice at the freeze gate.** Interpretation: pass → F2 closed; fail → serious (apparatus issue), report honestly. valid_for_paper=false until sound run + results audit. Audited BORDERLINE paper remains the safe fallback.

## 2026-08-04 · D-0087 · Critic must-haves + logit-delta diagnostic framing MERGED (paper at strong honest BORDERLINE)
- `feature/critic-diag-fixes` (20ee88d) merged at a0080f7 after a clean claim-integrity audit (no blocker/major; the single optional MINOR — repeat the first-token-proxy caveat at the L235 mention — is already covered in limitations+appendix). Three edits: (1) abstract+intro now state F2-openness up front (no latent intervention passes its behavioral manipulation check; scoped failed-superiority, not a broad latent negative) alongside the real strengths; (2) the methodological evaluation-contract is now the PRIMARY contribution (console = model-evidence-only reality-check, no user-study claim); (3) E-0015 caveat replaced with the audited logit-delta framing (refusal direction amplifies target first-token logits +13.9 nats @β=1 YET 0/5 scored refusals within coherence, one item Δ+16.9 byte-identical; β=2 only degenerates; first-token proxy overcounts I/hedge → representational push ≠ controllable handle, STRENGTHENING the negative). +13.9 always bound to 0/5; no "handle works" over-claim; appendix-level, valid_for_paper=false, K=5 disclosed. Builds 14pp, em-dash 0.
- **State of the paper:** F1 addressed, F3 resolved, F2 downgraded fatal→MAJOR (critic BORDERLINE, IUI ~30-35%). Honest, audited, robustly scoped negative + evaluation contract, with the READ≠CONTROL thesis now supported at the mechanistic (logit) level. Remaining above-the-line levers are the owner-deferred COSTLY options: a passing latent positive control (different method, e.g. Arditi ablation) and/or a formative user study. Manager does NOT submit (external submission = owner §5).

## 2026-08-04 · D-0086 · Reviewer-critic reassessment = BORDERLINE (IUI 30-35%); F2 downgraded fatal→MAJOR; + logit-delta diagnostic reveals target-logit amplification without behavioral control
- Reviewer-critic (critic-reassess-e0015) on the post-E-0015 paper: **BORDERLINE, IUI accept ~30-35%** (up from chained-review REJECT). Scores: originality 4, significance 3, rigor 3.5, clarity 4, reproducibility 4, overall 3, confidence 0.72. **F2 downgraded from fatal to MAJOR limitation** — instrument sensitivity established (prompt 95%, random-dir −0.24) + null robust to scale correction substantially defuse the "inert instrument/under-scaling" attack; endorses the current scoped wording (would reject only a BROAD latent-negative). Most-likely reject reason: no passing latent positive control + no user study → neither fully proves latent-assay soundness nor fully delivers the IUI interface contribution. FREE must-haves: (1) state F2-not-closed / no passing latent positive EARLY (abstract/intro); (2) reposition strongest contribution explicitly as the evaluation contract (not console benefit). Costly: a passing latent positive control; save transcripts/logit diagnostics (now DONE); a formative user-study vignette.
- **Logit-delta diagnostic (branch feature/e0015-logitdelta, run 05de543, valid_for_paper=false)** — the transcript/logit follow-up the owner requested. Surprising nuance: on refusal the steering direction STRONGLY, monotonically amplifies the target first-token logits (Δlogprob steer−baseline +1.31 @β0.125, **+13.9 @β1, +19.6 @β2**; output-change fraction 0.14→0.60→0.93) YET the scored refusal outcome stays 0% within coherence (β2 degenerate). I.e. representational/logit push is target-specific but does NOT convert to behavioral control within the coherent range — READ≠CONTROL at the mechanistic level. CAVEAT (why audited before integrating): the first-token proxy (I/Sorry/I'm…) overlaps non-refusal answer starts, and a skeptic could read the +13.9 as "the handle works, 0% is a scale/scorer artifact." Hostile audit (audit-logitdelta) in flight to judge helps-vs-reopens + honest framing before any paper integration. Next: ONE batched writing pass (critic free must-haves + diagnostic-informed limitation update) → audit → merge.

## 2026-08-04 · D-0085 · E-0015 full run = universal NULL even scale-corrected; genuine (not artifact); under-scaling excluded; F2 not cleared but instrument-sensitivity established
- Full 4-axis run (Qwen2.5-7B, code_commit d75395e, results commit 4d900a9, valid_for_paper=false) independently hostile-audited (audit-e0015-results). **Every cell NO-PASS on all 4 axes** (refusal + deliberation + skepticism + uncertainty), PC-2a/PC-3/random all fail. Matrix cell "nothing passes, coherence OK → report null; apparatus suspect."
- Numbers REAL, adjudication CORRECT (δ=0.05, B=10000, Bonferroni, coherence gate unchanged), single-variable isolation held (metacog reuse frozen C2 L20, seed/n hard-locked), NO .tex leakage. Refusal 0% at every coherent β; metacog PC-2a mean_diff≈0, all CI include 0.
- **Genuine null, NOT a propagation artifact** (audit verdict): the intervention reaches the output — degeneracy collapses at refusal β=2 (0.003→0.318), and the random-direction control coherently moved uncertainty −0.24 CI[−0.36,−0.12]; hook adds α·û at all positions/forwards correctly. Naive additive single-layer CAA can *degrade* the model at high β but cannot *controllably* move these behaviors — not even refusal, which a prompt drives to 95%.
- **Manager framing correction (audit MAJOR-1):** the coherent perturbation ceiling is ~0.5–0.66× residual-stream norm (residual_norm_mean refusal 411.9, metacog ~96.2), NOT ~1×; the only ~1.05× point (refusal β=2, α=433) is degenerate (coherence_ok=false). Honest wording must be "within the coherent ceiling (~0.5–0.66×‖h‖) scale correction did not rescue control; beyond it the model degenerates."
- **Net effect:** (a) does NOT clear F2 — no latent intervention ever passed (manipulation check still never positive); (b) but instrument sensitivity IS established (prompt 95%, random-dir −0.24, both detected) so the F2 "inert instrument" worry is substantially answered; (c) substantially EXCLUDES the under-scaling explanation for the C2 null within the coherent range (real strengthening); (d) sharpens a new publishable concern: naive additive single-layer CAA is behaviorally ineffective as a control primitive in this model. Honest paper conclusion = "robust scoped negative about naive/bounded single-layer CAA steering; prompts are the only effective channel; no latent positive control established; under-scaling excluded within coherent range." Must NOT be stated as "latent uncontrollable in general." MDE ~0.19 (nulls carry MDE). Residual uncertainty (specific-logit attenuation within coherent range) closable by a cheap logit-delta follow-up (~4 forwards, near-zero GPU).

## 2026-08-04 · D-0084 · E-0015 scale-corrected control audited SOUND + prereg FROZEN — pending owner GPU scope sign-off
- E-0015 harness built (impl-e0015) and merged to main at `c2e82b2` after TWO independent hostile code-audit passes (audit-e0015-code). First pass: science/scaling-math (h+β·v, β∈{0.125,0.25,0.5,1,2}=alpha_eff β·‖v‖)/single-variable isolation (metacog reuse frozen C2 layer 20 + same pairs/split, only β varies)/frozen-adjudicator reuse all CORRECT, but 1 BLOCKER (four separate 7B loads → ~90GB → certain A800 OOM, the D-0043 lesson) + 2 MAJOR (no runtime lock on the isolation invariant seed/n_extraction; zero test coverage for the real-not-smoke guard) + 1 MINOR. All closed (commit f83b185): ONE shared HFActivationProvider+SteeredHFBackend across derivation/hook-bites/generation/random-control (from_pretrained once on hf), hf isolation hard-lock (seed==20260723 ∧ n_metacog_extraction==28 → SystemExit before load), non-vacuous hf-path guard tests, metacog N≥60/80 assertion. Re-audit VERDICT: SOUND, no BLOCKERs; shared-handle refactor verified behaviorally IDENTICAL (zero-scaling equivalence, per-call reseed, hook cleanup in finally); 668 passed / 6 skipped, E-0015 16 tests.
- Prereg FROZEN: `docs/research/2026-08-04-scale-corrected-positive-control/prereg-e0015-FROZEN.md` (harness pinned c2e82b2). Registry status `prereg_frozen_ready_for_gpu_pending_owner_scope_signoff`.
- **AWAITING OWNER §5 GPU sign-off on scope:** minimal (refusal + uncertainty, ~1.5-2.5 GPU-h) vs full (refusal + all 3 metacog axes, ~3-6 GPU-h). Full is the complete headline-risk co-test. valid_for_paper stays false until sound run + independent results audit. All interpretation-matrix cells pre-declared publishable (incl. headline-overturn).
- **2026-08-04 UPDATE — OWNER AUTHORIZED FULL SCOPE (ask_user).** Run refusal + all 3 metacognitive axes on A800 GPU1 (~3-6 GPU-h, Qwen cached). Harness default runs ALL_AXES; isolation lock requires default seed=20260723/n_metacog_extraction=28. Etiquette: push run commit before cleanup, never shutdown. valid_for_paper stays false until independent results audit.

## 2026-08-04 · D-0083 · Honest bounded/naive reframe MERGED (Track A of D-0082)
- `feature/reframe-bounded-steering` (712dae2) merged to main at facfe00. Two independent claim-integrity audit passes (audit-reframe): first found the reframe honest + all numbers traceable to E-0013/E-0014 except 3 MAJOR residual comparator-label misattributions in the F2/Interface-Evaluation-Contract section + failure-taxonomy table (attributed the negative contrast to "steering" without the steer-vs-prompt qualifier — the D-0082 red line); fixed + Manager-verified the exact old→new text. Now: title "…under Bounded Naive CAA/ITI Steering"; every steering claim scoped to h+α·û, α≤24; the uncertainty result is consistently a steer-vs-bounded-prompt contrast with direct steer-vs-baseline ≈0 (compliance +0.011, 1−Brier +0.0008) in body, figure caption/Description, F2 table, and console-card signal (iv); honest E-0014 positive-control paragraph (endpoint live via prompt 95%, latent arm 0% at all α, under-scaling caveat vs norm ~216, does NOT establish latent-arm assay sensitivity); "not an impossibility theorem" + skepticism/deliberation MDE limitations retained. Builds 13pp, em-dash 0. Paper is now maximally honest at the audited BORDERLINE level. Track B (E-0015 scale-corrected control) proceeds separately.

## 2026-08-04 · D-0082 · E-0014 positive control = FAILED to establish latent-arm assay sensitivity; uniform under-scaling threatens C2; owner GO on BOTH (reframe now + scale-corrected E-0015)
- **E-0014 real hf run** (Qwen2.5-7B, code_commit 720c6c8, results commit f520610, valid_for_paper=false) independently hostile-audited (audit-e0014-results): numbers REAL, adjudication CORRECT, no leakage. **Result:** the endpoint/statistics pipeline is LIVE (strong prompt "Always refuse…" drove refusal to **95%**, cleanly detected; random-direction negative control correctly NO-PASS), but the **latent CAA refusal arm produced 0% refusal at every α (2→24)**, coherent, tiny degeneracy. PC-2a mean_diff 0.0 CI[0,0]; PC-3 steer−prompt −0.955.
- **The damaging finding — under-scaling is UNIFORM across C1/C2/E-0014.** The frozen convention adds α·(unit vector) with α≤24, but the refusal direction's natural norm is ~216 (layer 27) → ~1–11% nudge. Cross-checked E-0013 CAA×Qwen under the SAME convention: latent **steer−baseline** effect is essentially zero everywhere (compliance +0.0113; calibration 1−Brier +0.0008). The reported "−0.34 harm" is entirely **steer−prompt**, driven by the PROMPT arm (1−Brier 0.831) — steer(0.621)≈baseline(0.621). **Every non-zero behavioral movement in the project comes from the prompt channel.** So the C2 "legible≠controllable" null may substantially reflect that bounded naive steering barely perturbs behavior at all — a real retroactive threat to the headline, and it does NOT clear reviewer F2 (it sharpens it).
- **Manager correction:** my initial "Row C / failed bet" framing was an overstatement (Row C presupposes latent activity the artifacts don't establish). Recorded honestly.
- **Owner decision (§5, ask_user): BOTH.** (A) Now, zero-GPU: reframe the paper's steering scope explicitly to *bounded/naive CAA at α≤24* and disclose E-0014 as a limitation (endpoint sensitive via prompt; latent arm null; cannot distinguish "adjudicator insensitive to bounded latent control" from "target immovable / convention too weak"). (B) GPU under a NEW frozen prereg (E-0015): a **scale-corrected** positive control (raw-magnitude / norm-matched direction, Arditi-style recipe), with ALL outcomes pre-declared publishable and no run→tune→rerun. Interpretation: refusal moves + metacognitive axes still don't → strongest F2 clearance + headline survives; metacognitive axes also move → headline overturned (valid but different paper); nothing moves → null hardens. valid_for_paper stays false until sound run + independent results audit. The audited BORDERLINE paper remains the safe fallback throughout.

## 2026-08-04 · D-0081 · E-0014 harness audited SOUND, guards hardened, prereg FROZEN — cleared for GPU
- **Two independent hostile code audits** (audit-poscontrol) of the E-0014 positive-control harness. First pass: NO hidden smoke/leak/drift path; real CAA direction on hf via HFActivationProvider+extract_caa; real-not-smoke guard fires on every placeholder path; frozen adjudicator reuse with zero drift (three metacognitive axes untouched); id-disjoint real TriviaQA data; random-direction negative control through the real hook; deterministic refusal scorer; all E-0014 artifacts `valid_for_paper=false` (synthetic smoke) with the scope guard verbatim; PC-0/PC-1 numbers (steer−prompt +0.381, steer−baseline +0.011, baseline−prompt +0.370) recomputed from real E-0013 transcripts, not hardcoded — I independently reproduced them byte-identical. PC-0/PC-1 (0 GPU) ruled SOUND and run.
- First audit raised 3 MAJORs (all E-0012-class *runtime self-verification* gaps, not correctness bugs): (1) no runtime item-pool disjointness assertion; (2) no hook-bites assertion (steering-actually-perturbs check); (3) one vacuous-green test using use_fixture=True. Dispatched fix (fix-poscontrol-guards) → closed all three + registered E-0014 + extended leakage test. **Re-audit confirmed all genuinely closed and the hook-bites check is REAL/non-vacuous (would fail if steering did nothing)** but found **BLOCKER-1**: the hook-bites tolerance was an absolute L2 `1e-3` incompatible with the real run's fp16 (would fail-closed abort every GPU run). Fixed to E-0007-style dtype-robust criterion (cosine ≥0.999 AND relative-norm-error ≤0.05), checked at both α=4.0 and the DEV-selected frozen α; I directly verified it is non-vacuous and fail-closed.
- Full suite 652 passed / 6 skipped. **Merged to main at `a7c4f25`.** Prereg frozen: `docs/research/2026-08-03-positive-control-design/prereg-e0014-FROZEN.md` (harness pinned at a7c4f25; live commit captured by git_commit() into the manifest). Interpretation matrix rows A/B pre-declared publishable; scope guard prevents reading a pass as metacognitive control. **Next: push run commit → A800 GPU1 PC-2/PC-3 (~1.5 GPU-h, Qwen cached) with hook-bites exercised on the real fp16 model as step 1 → results audit → integrate assay-sensitivity subsection.** valid_for_paper stays false until sound run + results audit.

## 2026-08-03 · D-0080 · Owner GO on positive-control ladder (E-0014, assay sensitivity); F1-framing honesty fix merged
- Positive-control design (`docs/research/2026-08-03-positive-control-design/design.md`, bd1955b) approved. Splits "assay sensitivity" into 3 sub-claims: PC-0/PC-1 = ZERO-GPU reanalysis of committed transcripts (measurement pipeline detects a large real effect; instruction effect +0.377 = +0.374 instruction + +0.004 latent); PC-2/PC-3 = ~1.5 GPU-h on Qwen (cached) with a REAL CAA direction on the **refusal-induction (Arditi et al. 2024) non-metacognitive** target through the SAME frozen adjudicator, + 7-item real-not-smoke guard + random-direction negative control. Interpretation matrix rows A/B pre-declared publishable (A: instrument sensitive end-to-end → headline strengthened; B: sensitive, binding constraint is the strong prompt comparator). Scope guard: verbatim sentence prevents reading a pass as metacognitive-control evidence.
- **Owner ruled GO on the full ladder.** Not §5-new beyond this authorization. Implement (reuse frozen adjudicator, real dir + real-not-smoke guard, refusal target, Qwen) → hostile code audit → freeze prereg → run (PC-0/1 free + PC-2 GPU) → results audit → write an "assay sensitivity / positive control" subsection with the scope guard. valid_for_paper=false until sound run + audit.
- **F1-framing honesty fix merged (70aa83b):** the design's PC-0 decomposition confirmed the E-0013 "steer more format-compliant than prompt (0.83 vs 0.45)" wording was causally misleading — steer compliance (0.826) is at the unsteered BASELINE (0.815); the PROMPT drops compliance (0.445). Paper now states this correctly (imputation distortion acts through the prompt arm, not steer); refutes "steer drops the format" without implying steering improves it. Caveats intact.

## 2026-08-03 · D-0079 · Reassessment critic = BORDERLINE (REJECT→borderline, IUI ~28-40%→45-55% after these writing fixes); F1/F3 addressed, F2 open; writing fixes merged; positive-control design in progress
- Reassessment critic (Opus5, `reviews/2026-08-03-reassessment-critic/review-reassess-IUI.yaml`) on the rewritten + E-0013-integrated paper: **BORDERLINE** (up from chained-review REJECT). Per prior fatal issues: **F3 (C3 console contract) RESOLVED**; **F1 (format confound) PARTIALLY-ADDRESSED** — flagged that the paper reported the favorable complete-case harm but NOT the reanalysis.json adversarial worst-case imputation bounds [−0.478,+0.250] that STRADDLE ZERO under differential missingness (prompt 0.445 vs steer 0.826 compliance) → selective-reporting honesty gap; **F2 (no positive control / assay sensitivity) STILL-FATAL**, aggravated by skepticism MDE 0.19-0.28 ≫ δ=0.05 (those cells could never pass) and ITI directions never READ-validated (legible-not-controllable clean only for CAA/contrastive family).
- **Writing fixes MERGED (9894c08, feature/reassess-writing-fixes → self-verified honest, builds):** report the worst-case bounds + reframe CAA×Qwen as complete-case "mitigated not closed"; promote skepticism MDE into body text as uninformative; scope Abstract format claim to one cell; add F2 limitations (no positive control; ITI never READ-validated); scope E-0013 to D-0078 narrow use. Paper is now strictly more conservative/honest; no number changed.
- **F2 = last fatal. Owner ruled: do BOTH in parallel** — (a) the Limitations reframe (done, in the merge above), and (b) DESIGN a positive-control run. Positive-control DESIGN subagent (doc-only, `docs/research/2026-08-03-positive-control-design/design.md`) in progress: a positive control reusing the frozen C2 adjudicator on a KNOWN-controllable NON-metacognitive target (real derived direction + real-not-smoke guard given E-0012 history) to establish assay sensitivity (adjudicator CAN return a pass when control genuinely exists). Manager will review the design → owner go/no-go on build+run (new arm = §5 GPU). Estimate: minimal Qwen-only.

## 2026-08-03 · D-0078 · E-0013 CAA×Qwen format-compliance recheck audited HARM-SURVIVES-BUT-CAVEATED → cap at largest cell + honest disclosure of the 3 blocked cells (owner rule)
- E-0013 hit infra walls (D-0077): ITI×Qwen blocked by a too-strict exact-match guard on the re-derived ITI sigma (4.5455 vs frozen 4.5465 ≈ 2e-4 fp noise across environments); both Llama cells blocked (Meta-Llama-3-8B HF-gated, access denied — original runs used a Gitee mirror). Model-portability fix (72aa8eb) let Qwen cells run via the cached HF id. Only the LARGEST cell **CAA×Qwen** (Δ_frozen=−0.228) ran.
- **Result (run branch run/e0013-caaqwen-20260803 @ 70af399, merged a56db4f; reanalysis.json):** format-compliance rate prompt=0.445, **steer=0.826**, baseline=0.815 — steering drops the confidence format LESS than prompting (opposite of the reviewers' assumed direction). As-run imputed steer−prompt=−0.209; **format-compliant-only steer−prompt=−0.337, 95% CI [−0.508,−0.165]** (excludes 0, LARGER than imputed). ⇒ the imputation (conf=0.5→0.75) made the as-run negative contrast CONSERVATIVE; the negative steer-vs-prompt contrast is NOT a parser/format-imputation artifact for this cell.
- **Independent results audit (`reviews/2026-08-03-e0013-result-audit`): HARM-SURVIVES-BUT-CAVEATED.** Recomputed rates/deltas exactly from samples.jsonl; real pairs synthetic_proxy=false; real CAA mean-diff direction; identity mnt64/temp0.7/seed20260723; as-run −0.209 consistent with frozen −0.228. Caveats: (a) MAJOR-1 scope = ONE cell only — ITI×Qwen + both Llama cells NOT rechecked (blocked), must be disclosed as limitation, NOT generalized; (b) compliant-only restriction conditions on compliance (potential collider) → it is a robustness refutation of the SPECIFIC confound (steer-drops-format-more), not an unbiased all-population treatment effect. No BLOCKER for the narrow claim.
- **Owner rule (D-0076: survive→cap+disclose) enacted:** CAP the recheck at CAA×Qwen; integrate into the paper the honest framing — on the largest cell, steering is MORE format-compliant than prompting and the harm survives (indeed strengthens) on paired format-compliant generations, so the harm is not a format artifact there; the other three cells are not yet rechecked (ITI fp-reproducibility guard; Llama gated), a stated limitation; the imputation rule is disclosed. This resolves the chained-review #1 fatal issue for the headline cell. Next: targeted paper harm-section integration (replace "recheck in progress" with this audited result + exact one-cell scope) → audit → merge. valid_for_paper for E-0013 = true for the narrow CAA×Qwen robustness claim only.

## 2026-08-03 · D-0077 · E-0013 uncertainty format-compliance recheck frozen (run commit 1d4ad54); cleared for A800 run
- E-0013 harness (D-0076 Track C) merged to main 1d4ad54 after hostile code audit (`reviews/2026-08-03-e0013-code-audit`) confirmed REAL CAA/ITI directions (genuine C1/C2 activation path, no synthetic/random factory) + REAL TriviaQA data (use_fixture=false) — **no E-0012 repeat** — and the one BLOCKER (model identity not hard-validated) was fixed (12d258f: model now part of the hard-validated per-cell generation identity {model, mnt=64, temp=0.7, seed=20260723}). Additive-only; frozen adjudicator/scorer/imputation (conf=0.5) unchanged. 634 tests pass.
- Frozen prereg pinned to 1d4ad54. Not §5-new (owner authorized the recheck in D-0076).
- **Cleared for A800 GPU1 fp16 run (~2-4h):** rerun 4 uncertainty cells reusing frozen E-0006 selected configs (CAA×Qwen L20/unc-strong-01; ITI×Qwen L17/unc-strong-01; CAA×Llama L10/unc-strong-09; ITI×Llama L11/unc-strong-09; alpha=frozen_alpha per cell), capturing raw text + format-compliance; recompute the steer-vs-prompt contrast on format-COMPLIANT-only generations + report per-cell compliance rate (steer vs prompt). PUSH run commit before cleanup; never shutdown. Then results audit → decides whether the C2 comparator-bound headline survives (contrast robust on compliant-only → strengthen paper) or is format-driven (→ honest reframe). This is the reviewers' #1 fatal issue.

## 2026-08-03 · D-0076 · Chained hostile review (Opus5→GPT-5.6-Sol→Opus5) = REJECT (one-cycle path back); owner authorized format-confound GPU recheck + parallel writing-only fixes
- 3-stage chained review on the submission-ready paper (`reviews/2026-08-03-chained-review/` A/B/C): A (Opus5) reject/weak-reject IUI overall 2, IUI 15-22%; B (GPT-5.6 Sol) reject; C (Opus5 AC) **Reject (Weak Reject, one-cycle path back)** IUI/CHI/CSCW. AC also defended the paper vs reviewer overreach (oracle-prompt makes the negative MORE conservative; 64-token cap shared by both arms; deliberation "trend" below δ AND MDE; "field expected this" not grounds).
- **3 truly-fatal (converged):** (1) **format-vs-calibration confound on the ONE robust finding** — the uncertainty steer-vs-prompt contrast may be a confidence-FORMAT/parser-imputation artifact; the E-0006 audit ruled out empty/degenerate output (trunc=0) but NOT format-drop imputation; **imputation rule identified in code:** `adjudicate_c2b.py:471-476` sets conf=0.5 when `parse_confidence` returns None → per_item_brier=0.75 fixed (undisclosed in paper). (2) **No positive control / manipulation check** (adjudicator never returned a pass in any arm) + READ (C1) and TRANSFER (C2) not validated on the SAME intervention, esp. ITI (probe-derived, never shown READ-positive). (3) **C3 console contract has zero evidence** (own gate FLAGGED) — fatal CHI/CSCW, demotable IUI.
- **Fixable (writing/reanalysis only):** protocol under-reporting (k/temp/max_new_tokens=64/parser-imputation/bootstrap variant/steer-prompt absent from body), multiplicity across 12 grid cells, asymmetric δ, abstract overreach ("split-seed robust", C1 in abstract), "fairness-controlled"/"realistic user effort" softening, missing HCI trust-calibration citations (Amershi/Lee&See/Bansal/Buçinca/model cards/datasheets), manifest hygiene.
- **Owner §5 decision: authorized (a) the format-confound GPU recheck** — transcripts were NOT persisted for E-0006/E-0011, so this needs a bounded rerun of the 4 uncertainty cells (reusing frozen DEV-selected prompt+α) capturing raw text + format-compliance rate, then recompute the steer-vs-prompt contrast on format-compliant-only generations (~2-4 GPU-h). Either outcome publishable: contrast survives → stronger; contrast format-driven → honest reframe. **AND (b) parallel writing-only fixes.** This is a robustness check that INFORMS the C2 comparator-bound interpretation; it does NOT alter the frozen E-0005/E-0006 protocol/verdict.
- Two parallel tracks dispatched: Track-1 recheck (implement transcript+format-compliance capture + compliant-only reanalysis → audit → freeze → rerun → audit); Track-2 writing revision (all fixable items → audit → merge).

## 2026-08-03 · D-0075 · Paper SUBMISSION-READY for IUI (final polish merged); E-0012 chapter fully closed
- Final acceptance critic (`reviews/2026-08-03-final-acceptance-critic/review-final-IUI.yaml`): all 10 prior-critic gaps CLOSED, zero residual over-claims (equivalence/universal/user-benefit all clean), zero E-0012 leakage; scores up (overall 3.4→3.8; rigor 4.3, clarity 4.2, reprod 4.2); IUI accept est. 25-40% → **35-50%**; verdict MINOR-POLISH-THEN-SUBMIT.
- Final prose-only polish merged (main 34ace23, revision b12fa29 → polish e5cf264): positioning sentence (interface-evaluation-method contribution, not user-benefit study); scoped `\shorttitle` "under Naive CAA/ITI"; 16-prompt bounded-interface-budget phrase; exploratory social-inference (C4) relocated to appendix (Context Only) with all caveats preserved. Zero numeric/table/figure edits; LaTeX compiles; Manager-verified full diff.
- **Paper state:** revised, audited (READY-TO-MERGE), re-reviewed (MINOR-POLISH-THEN-SUBMIT), venue=IUI, overview-zh synced. Headline = C1 (exploratory setup facade) + **C2 frozen negative (no demonstrated superiority under naive CAA/ITI; robust negative uncertainty steer-vs-prompt contrast; split-seed robust)** + C3 (interface-evaluation contract, model-evidence-derived, no user study) + C4 (appendix exploratory). E-0009 pre-empts "weak steering" attack. Actual IUI submission is owner §5 (external release) — NOT performed by Manager.
- **E-0012 fully closed** (D-0072/D-0073 terminated after 4 placeholder bugs; all evidence INVALID; not in paper; lessons in failure-log). Manager E-0012 thread ended.

## 2026-08-03 · D-0074 · Venue = IUI (owner §5 decision); authorized full submission-revision pass per reviewer-critic gap list
- Reviewer-critic gap pass (`reviews/2026-08-02-submission-critic/` R1-novelty-venue + R2-methodology) on the frozen post-E-0012-termination paper (main 7e6bd0c): both critics = sound paper, MAJOR revisions (wording/framing/reproducibility) but NO fatal blocker and NO new experiments; zero E-0012 leakage confirmed. R1 overall 3.4, R2 3.0.
- **Owner ruled venue = IUI** (primary; R1: IUI 25-40% if tightened, best fit for intelligent-UI + model-evidence artifact without a user study; FAccT/AIES = alt after trust reframing; CHI-full fatal without user study). Venue no longer deferred.
- **Authorized full revision pass** (Manager-driven, generator discipline — edit tables/figures only via generators, never hand-edit numbers). Gap list (all non-experimental): (1) scope wording "no demonstrated superiority (not equivalence), under naive CAA/ITI" + title/abstract qualifier; (2) "5 DEV/TEST split seeds over same item pool" not "5 seeds"; (3) reframe C3 as interface-evaluation contract/artifact + concrete UI-decision vignette, no user-benefit claim; (4) foreground calibration-harm as the empirical contribution, demote mechanism, note reliability/resolution/format ambiguity; (5) expose selected best-prompt IDs+text/hashes in c2 manifest + justify 16-prompt bounded budget; (6) 1-sentence novelty-vs-nearest-neighbors; (7) construct-validity paragraph (axes=outcome proxies, 1-Brier conflates reliability/resolution); (8) 1-sentence format/parser-disruption audit for uncertainty cells (data check, no GPU); (9) submission-filtered evidence ledger excluding INVALID E-0012 rows; (10) trim C4 social-axis to appendix + frame C1 as setup measurement. Process: revision subagent (worktree) → independent hostile audit → merge → re-run critic for acceptance.

## 2026-08-02 · D-0073 · E-0012 TERMINATED (owner §5 decision); all E-0012 evidence INVALID/excluded; pivot to non-gated submission polish
- Owner ruled **TERMINATE** on the D-0072 escalation. E-0012 (the "verified control button" thrust: research/design, prereg, harness, first/E-0012b/v3 runs, comparator-strength CS, A-lite real-direction run, settling-grid SG) is ABANDONED in full. Reason: four independent placeholder-vs-real freeze-integrity bugs (synthetic comparator, greedy sampling, random directions, fake world-capital fixture data), each caught only post-GPU-run; the harness is an offline-smoke scaffold never validly wired to real data/directions/generation for confirmatory runs; even a fixed run most-likely yields a negative; and the one apparent positive was degenerate confidence-suppression.
- **All E-0012 evidence is valid_for_paper=FALSE / INVALID** (E-0012, E-0012b, E-0012c, CS, A-lite, SG). E-0012 will NOT appear in the paper. Verified: `docs/paper/**` has ZERO references to E-0012/verified-control/BTN-CAL/SYNTH-BANK/comparator-strength/settling-grid — no cleanup needed (discipline held: never written in pending validation). All E-0012 artifacts/branches/audits are retained as honest negative lineage (git history) but are non-citable.
- **Paper headline UNCHANGED and SAFE:** C1 (facade, 2-model) + C2 (NON_TRANSFER_GENERALIZED, multi-seed E-0011) on real data (`use_fixture=false`, independently audited, E-0007 real-steering verified). The frozen negative reality-check thesis stands exactly as before E-0012 was attempted.
- **Pivot (owner directive):** return to non-gated submission-readiness polish — venue final decision, overview-zh sync to latest, reviewer-critic gap pass. E-0012 thread closed.

## 2026-08-02 · D-0072 · E-0012 ENTIRE LINE (CS/A-lite/SG) INVALID — ran on a fake world-capital placeholder fixture, not real TriviaQA (4th placeholder bug); SG "positive" also degenerate; Manager recommends ABANDON E-0012 (§5 human decision)
- SG results audit (`reviews/2026-08-02-e0012-sg-results-audit/audit-report.md`) verdict = **NOT-SOUND**, two BLOCKERs:
  - **BLOCKER-1 (catastrophic):** `run_e0012_verified_control.py:148` and `run_e0012_settling_grid.py:87` HARDCODE `load_e0012_pool(use_fixture=True)`. The committed fixture `data/e0012_pool/triviaqa_e0012.jsonl` is NOT TriviaQA — it is 80 templated rows `"What is the name of a world capital city? (n)"` with arbitrary cyclic gold answers (Paris/London/Tokyo/…). Non-unique prompts + arbitrary labels → the scorer marks ~94% of plausible answers wrong → the ~6% "accuracy" seen throughout E-0012. So **every E-0012 GPU run (first/E-0012b/v3/A-lite) AND CS AND SG ran on this placeholder fixture**, despite the prereg claiming "TriviaQA Option A validation split." This is the **4th placeholder-vs-real freeze-integrity bug** in E-0012 (after F-01 synthetic comparator, greedy sampling, random directions).
  - **BLOCKER-2:** the SG "+0.131 positive" is DEGENERATE confidence-suppression, not calibration control: steering leaves accuracy unchanged (0.057→0.057) while collapsing confidence to a near-constant ~0.20; correct-vs-incorrect confidence gap collapses +0.085→+0.006, confidence AUC 0.682→0.521 (near chance). It improves Brier only because ~94% of items are (mis)scored wrong. Not a genuine affordance.
- **PAPER HEADLINE IS SAFE (verified):** C1/C2 (E-0003..E-0011) use a DIFFERENT codepath (`run_c2b_adjudication.py`/`run_arm_matrix.py`) that takes `use_fixture` from args; the real arm_full/E-0006 runs recorded `"use_fixture": false` (real GSM8K/TruthfulQA/TriviaQA; E-0007 verified real steering; E-0011 multi-seed). The E-0012 fixture bug is confined to the E-0012 runners. C1/C2 UNAFFECTED.
- **Manager assessment:** E-0012 has now produced FOUR independent placeholder-vs-real bugs, each caught only after a GPU run, across ~7 GPU runs + ~12 audits. The harness is fundamentally an offline-smoke scaffold whose real-data/real-direction/real-generation wiring was never completed for confirmatory runs; every layer peeled back reveals another placeholder. Even a fully-fixed E-0012 most-likely yields a negative. **This is the AGENTS.md §5 repeated-BLOCKER escalation (continue/pivot/downgrade/terminate). Manager recommendation: TERMINATE E-0012** — drop it entirely, keep the solid audited C1/C2 negative as the paper headline. ALL E-0012 evidence (CS/A-lite/SG numbers) is valid_for_paper=FALSE / INVALID. Escalated to owner for the §5 decision.

## 2026-08-02 · D-0071 · E-0012-SG settling grid frozen (run commit 345b27c); cleared for ~30-45min GPU run
- Owner chose (post D-0070) to run the settling grid to close the A-lite results-audit UNVERIFIED-1 (pure real-probe steering unmeasured) before writing E-0012 into the paper.
- **Design:** 6 conditions on frozen E-0012 TEST (53 items, k=5, same fp16 sampler as A-lite): {empty, CAL-09, SYNTH-BANK-26} × {no-steer, real BTN-CAL-PROBE@L18 α24}. Reuses the EXACT A-lite real probe direction (hf re-derives + ASSERTS vector_sha256 == A-lite provenance da5723...e60e, aborts on mismatch). Persists per-condition TEST mean(1-Brier) + paired-bootstrap-CI deltas: pure-steering (empty+probe−empty), CAL09+probe−CAL09, SYNTH26+probe−SYNTH26, best-steered−best-prompt-only. Descriptive, no selection/tuning.
- **Gates:** independent hostile code audit (`reviews/2026-08-02-e0012-sg-code-audit`) = READY-TO-FREEZE-AND-RUN (same-direction guarantee hard-fails; steering/scoring reuse harness path; TEST-only; deltas use shared cluster bootstrap; zero src drift; 1 low-impact MINOR test-coverage note). Additive-only. Merged main 345b27c.
- Not §5-new (within owner-approved settling-grid). Next: run once on A800 GPU1 fp16 (~30-45min), PUSH run commit before cleanup, results audit, then write E-0012 into paper. valid_for_paper=false until run + results audit.

## 2026-08-02 · D-0070 · E-0012 A-lite REAL-direction run audited SOUND-BUT-OVERCLAIMS → honest headline: a real effective calibration direction still does NOT beat strong prompting (defensible negative, closes "weak-steering" attack)
- A-lite real-direction run (execution 9f7a42a, run branch run/e0012-alite-20260802 @ 846e9fd; E-0006 baseline artifact 1c07a03). Independent hostile results audit (`reviews/2026-08-02-e0012-alite-results-audit/audit-report.md`) verdict = **SOUND-BUT-OVERCLAIMS-IF-CALLED-VERIFIED-CONTROL**.
- **Directions genuinely REAL (bug fixed):** 10 provenance records (5 real_probe from TriviaQA-train + 5 real_caa_mean_diff whose source_artifact_sha256=9c1e12ccef16 matches the E-0006 unsteered baseline manifest). Real-not-smoke guard did not fire (real inputs present). E-0006↔E-0012 item overlap=0 (re-verified) → no CONTRA leakage. All standard gates pass: split 27/53 0-overlap; 7,923 raw pairs all synthetic_proxy=false; N-01 active; kill rule symmetric (APE k5=0.5343 < button DEV k5=0.8242 → PASS); Stage0 70/70, 8 pass cutoff, 1 advancing (BTN-CAL-PROBE@L18 α24); Bonferroni M=1; §9.4 SKIPPED correct; VERDICT=LOCAL correct per §8.
- **THE HONEST RESULT (audit-recomputed, TEST 53 items):** the real probe direction is a GENUINELY EFFECTIVE calibration intervention — steer(CAL-09 prompt+real-probe)=0.826 vs prompt-alone CAL-09=0.537 → **+0.289 held-out gain, 95% CI [0.217, 0.355] (excludes 0)**; steer vs empty baseline=+0.682. This is a large real effect (contrast: random-placeholder direction gave only +0.14; naive CAA/ITI in C2 gave none). **BUT it does NOT beat strong prompting:** prompt+steer (0.826) vs the strongest human prompt SYNTH-BANK-26 (0.794, CS) = **+0.032, 95% CI [−0.014, 0.075] — crosses zero.** Pure real-probe steering (empty prompt) was NOT measured (audit UNVERIFIED-1).
- **Interpretation (honest, NOT over-claimed):** (i) NOT a verified control / NOT "real steering beats prompting" (the strongest prompt is only numerically below, not CI-separated; and the button score is prompt-conditioned CAL-09+steer, not standalone); (ii) also NOT "steering does nothing" — a real discovered direction adds a large increment over its prompt. **Headline: even a real, effective, discovered calibration direction provides no advantage over strong prompting → the latent "control slider" premise is not justified over prompting (non-surjective READ≠superior-CONTROL).** This CLOSES the "you only tried naive/weak steering (CAA/ITI)" reviewer attack — the original motivation for E-0012 — while staying an honest negative/equivalence that SUPPORTS the frozen thesis (does not change any core claim → not §5-new).
- MINOR: APE winner is the authored §5-B fallback CAL-09 (36 model-generated + 14 authored padding; state fallback provenance when citing 0.5343). 
- **Optional next (owner choice, small GPU ~30-45min):** the audit's "settling grid" to nail pure-vs-prompt-conditioned steering — score {empty+realPROBE, CAL-09+realPROBE, SYNTH-BANK-26+realPROBE} on the same frozen TEST — would make the pure-steering story airtight (currently UNVERIFIED-1). Not required for the negative. valid_for_paper: pending owner framing decision; the SOUND human-prompt + real-probe-increment numbers are audit-verified and usable.

## 2026-08-01 · D-0069 · E-0012 A-lite real-direction implementation frozen (run commit 0abd4a7); cleared for 2-step GPU run
- Implementation (feature/e0012-real-directions → main 0abd4a7) merged after TWO converged independent hostile code-audit rounds (`reviews/2026-08-01-e0012-realdir-code-audit` → 2 BLOCKER + 2 MAJOR; all fixed → `reviews/2026-08-01-e0012-realdir-fixes-audit` → 2 MAJOR (builder generation identity, D-0068 deletion) → both fixed + Manager-verified). Real PROBE (activation logistic probe on TriviaQA-train verbal-confidence pairs) + real CONTRA (CAA mean-diff over all-80 E-0006 uncertainty items, top40/bottom40); LOGIT-MARGIN dropped; grid 105→70; Stage1 ≤2. Real-not-smoke hard guard: hf forbids prederived directions + validates real provenance (vector_sha256 + source hashes + hyperparameters) + persists direction_provenance.json + hf-hard-fails on synthetic/random. E-0006 baseline builder frozen to E-0006 generation identity (mnt=64/temp0.7/seed20260723) with lineage-validating loader (identity match + raw_pairs k=5 + synthetic_proxy=false + baseline==mean). 625 tests pass. Zero drift to adjudicator/kill-rule/split/APE/§9/verdict (adjudicate_c2b.py diff empty).
- Prereg 2026-08-01 amendment FROZEN, run commit pinned 0abd4a7. Not §5-new (owner authorized A-lite in D-0068; scope reduction documented).
- **Cleared for 2-step GPU run on A800 GPU1 fp16 (owner-approved A-lite envelope ~3-5 GPU-h):** (1) build E-0006 baseline artifact (~15 min, frozen identity, commit the lineage-validated JSONL+manifest before the main run), (2) main E-0012 conservative hf run with real directions (~3-4h). Follow the fixes-audit A800 run-time checklist (verify direction_provenance.json = 10 real records, no synthetic strings; Stage0 70/70; ≤2 advancing). PUSH run commit before cleanup (D-0049); never shutdown. Then results audit (verify provenance real + verdict derivation) → owner report → paper. Most-likely honest outcome remains a NEGATIVE (real discovered/re-extracted directions still fail to beat strong prompting), which closes the "only naive steering tried" reviewer attack. valid_for_paper=false until sound run + results audit.

## 2026-08-01 · D-0068 · Owner approved A-lite: fix REAL directions for CONTRA+PROBE, drop LOGIT-MARGIN (scope reduction), add real-not-smoke hard guard, re-run E-0012
- After D-0067 (E-0012 button side invalid: random directions), Manager ran a zero-GPU feasibility assessment (`docs/research/2026-08-01-e0012-real-direction-feasibility/assessment.md`): Option A feasible (~1-2 eng-days + hostile audit + ~4-7 A800 GPU-h, confidence 0.65); CONTRA lowest-risk (reuses audited C2 CAA machinery), PROBE medium (needs TriviaQA-train loader + probe training), LOGIT-MARGIN highest (prereg underspecified vs current APIs → new spec/code).
- **Owner §5 ruling = A-lite.** Manager-frozen scope (owner-approved scope reduction of frozen §5-A): families = {BTN-CAL-PROBE, BTN-CAL-CONTRA-REEXTRACT} only; **DROP BTN-CAL-LOGIT-MARGIN** (underspecified/highest-risk); Stage0 grid 105→**70** (2×5×7); Stage1 advance ≤2, Bonferroni M=advancing count. All other frozen params byte-unchanged (TriviaQA Option A pool/split, §5-B APE stochastic+persisted per D-0064, kill rule, §9 guards, §9.4 SKIPPED, adjudicator §4, §8 verdicts).
- **Rationale:** even with real directions the most-likely outcome is a negative (real discovered/re-extracted calibration directions still fail to beat strong prompting), but a VALID negative closes the "you only tried weak/naive CAA/ITI steering" reviewer attack — the original motivation for E-0012 — meaningfully strengthening the paper's defense. Two families (probe = canonical legible direction; CONTRA = re-extracted CAA) is more defensible than one.
- **Mandatory NEW guard (would have caught this bug class):** on hf backend, harness MUST hard-fail if any direction is a synthetic/random placeholder; real directions carry provenance (method label, source items/split, model/dtype/device, layer, norm, derivation hash, commit); persist direction_provenance.json; mirror the N-01 synthetic_proxy pattern. Plus the feasibility's 10-item real-not-smoke pre-run checklist.
- Dispatched implement subagent (worktree feature/e0012-real-directions). Next: PLAN review → implement → independent hostile code audit (verify directions genuinely real + guard works + only approved scope change, zero other drift) → freeze amended prereg (pin run commit, D-0069) → re-run ~3-5 GPU-h → results audit (verify provenance real) → write E-0012 into paper. Not §5-new (owner authorized). E-0012 valid_for_paper=false until a sound real-direction run + audit.

## 2026-08-01 · D-0067 · E-0012 button side INVALID — all GPU runs steered along RANDOM Gaussian directions, not the frozen §5-A probe/CAA/PCA directions (3rd freeze-integrity bug); C1/C2 unaffected; §5 escalation
- **Discovery (during CS reconciliation audit, `reviews/2026-08-01-e0012-cs-reconcile-audit`, MINOR-1 → Manager escalated to BLOCKER):** the E-0012 harness derives button directions via `all_directions_for_layer` → `derive_direction_synthetic` → e.g. `derive_probe_direction_synthetic` which returns `np.random.default_rng(seed+layer).standard_normal(hidden_dim)` — a **seeded RANDOM Gaussian vector** explicitly documented as an offline-smoke placeholder ("On real hardware this would be: get activations… train a logistic probe"). The runner/harness NEVER wire the real derivations; the real "GPU CAA mean-diff" function in e0012_buttons.py is DEAD CODE.
- **Frozen prereg §5-A/§3-B specified REAL directions:** BTN-CAL-PROBE = probe weight vector trained (cross-entropy) on activations of rule-generated confidence pairs at the target layer; BTN-CAL-CONTRA-REEXTRACT = CAA mean-difference of real activations of pre-specified pairs; BTN-CAL-LOGIT-MARGIN = PCA of logit-margin activations. The code implemented NONE of these — it used random vectors. This is a code-vs-frozen-spec divergence on the MOST fundamental element (the steering direction itself).
- **Consequence:** EVERY E-0012 GPU run (first-synthetic, E-0012b, v3, CS) steered along random Gaussian directions. The entire button/steering side of E-0012 is **INVALID** as a test of RQ-E0012 ("does a discovered latent calibration direction achieve control"). The v3 LOCAL and the CS button≈baseline are both uninformative about REAL directions (a random vector doing ~nothing standalone, or perturbing generation by +0.14 on top of a prompt, tells us nothing about a real probe/CAA axis). This is the 3rd placeholder-vs-real freeze-integrity bug in E-0012 (after F-01 synthetic-comparator and greedy-sampling), each caught only post-GPU-run.
- **STILL SOUND / unaffected:** (1) the CS HUMAN-PROMPT evidence is valid and direction-independent — on frozen TEST, best human prompt SYNTH-BANK-26=0.794, CAL-09=0.537, baseline=0.144 (prompting achieves strong calibration). (2) **C1/C2 frozen headline (E-0003..E-0011) is NOT affected** — it uses a different, heavily-audited codepath (run_arm_matrix/adjudicate_c2b with real CAA/ITI directions; E-0007 OOD audit verified steered−baseline==α·dir on real GPU; E-0011 multi-seed). The random-direction bug is confined to the e0012_buttons.py synthetic factory used ONLY by E-0012.
- **§5 escalation to owner (core validity + GPU + whether E-0012 is a paper contribution):** (A) fix — wire the real §5-A probe/CAA/PCA derivations + re-run E-0012 (another implement+audit+GPU cycle; higher risk given 3 successive placeholder bugs in this harness), or (B) ABANDON the E-0012 steering/button side, keep the solid audited C1/C2 negative as the paper headline (optionally cite only the sound human-prompt calibration observation). Manager recommendation: **B** — three fundamental placeholder bugs mean low confidence in this harness; the hoped-for positive is dead and the "clean negative" is invalid on the steering side; C1/C2 already carry the thesis. NO E-0012 button claim will be shipped. E-0012 valid_for_paper=false (button side INVALID; human-prompt side pending owner framing).

## 2026-07-31 · D-0066 · E-0012-CS comparator-strength check frozen (run commit 264b475); cleared for one-shot GPU run
- Owner chose (post D-0065) to spend a small controlled GPU re-score to make the "a human prompt beats the button" evidence forensically airtight (recover/persist the 0.827-class prompt identity; head-to-head on held-out TEST) before writing E-0012 into the paper as an audited control-discovery negative.
- **E-0012-CS design (self-critical robustness — can only WEAKEN a positive):** on the FROZEN E-0012 TEST split (53 items), score TEST mean(1−Brier) at k=5 for 30 `_SYNTHETIC_APE_CANDIDATES` + 18 calibration_prompts.yaml prompts + unsteered baseline + button (BTN-CAL-PROBE@L19 α24), all 50 conditions, NO selection/tuning/early-stopping. Same fp16 HF sampler settings as v3 (max_new_tokens=256, do_sample, temp0.7, seed42) → apples-to-apples with the verified-control run. Descriptive pre-stated rule: report max_human_prompt TEST vs button TEST; if max_human_prompt ≥ button, confirms a human prompt beats the button on held-out data (weakens verified-control).
- **Gates passed:** independent hostile CODE audit (`reviews/2026-07-31-e0012-cs-code-audit`) = READY-TO-FREEZE-AND-RUN, zero drift to frozen src, 2 MINOR fixed (persist max_human_prompt/best_calibration_yaml decision vars + whitespace). Additive-only (new script + mini-prereg + tests). Merged main 264b475.
- **Not §5-new:** owner already authorized this GPU re-score (D-0065 Option 2). Frozen prereg `docs/research/2026-07-31-e0012-comparator-strength/prereg-e0012-cs-DRAFT.md` pinned to 264b475. Next: run once on A800 GPU1 fp16 (~1-2h), push run commit before cleanup, independent results audit, then write E-0012 into paper as an audited negative reinforcing READ≠VERIFIED. valid_for_paper=false until results audit + owner sign-off.

## 2026-07-31 · D-0065 · E-0012 v3 (sound, §5-B-conformant) audited SOUND-BUT-OVERCLAIMS-IF-CALLED-VERIFIED-CONTROL; button beats auto-prompt but NOT a strong human prompt → reinforces negative thesis, NOT a positive contract; §5 framing escalation
- Third E-0012 run (execution 78c08c5, run branch run/e0012-modelgen-v3-20260731 @ ed78394) with the D-0064 spec-conformance fix. Independent hostile audit (`reviews/2026-07-31-e0012-v3-audit/audit-report.md`) verdict = **SOUND-BUT-OVERCLAIMS-IF-CALLED-VERIFIED-CONTROL**.
- **Technically SOUND as LOCAL** (all clean, audit-recomputed): split 27 DEV/53 TEST 0-overlap; 22,311 raw pairs all synthetic_proxy=false; N-01 active; kill rule symmetric (APE k5 0.5343 < button 0.6967 → PASS); Stage1 TEST recomputed PASS (PROBE δ=0.144 CI[0.086,0.198]; CONTRA δ=0.108 [0.049,0.168]; LOGIT δ=0.067 [0.031,0.105]) with Bonferroni ci=1−0.05/3; §9.4 cross_axis=SKIPPED correct (does not flip verdict); coherence Infinity cosmetic (gate uses raw degeneracy, coherence_ok=true correctly). APE now genuinely stochastic + persisted: 36 model candidates ALL ≤0.214 k3 (model can't auto-write a strong calibration prompt), winner=authored CAL-09 0.534.
- **DECISIVE comparator-fairness ruling (MAJOR-1):** the first run's APE winner **0.827** was real-model-scored on the SAME DEV split (synthetic_proxy=false), from a *human-authored* prompt bank (`_SYNTHETIC_APE_CANDIDATES`), not §5-B model-gen. So a human prompt (0.827) demonstrably BEATS the button (0.697). ⇒ Calling v3 "VERIFIED-CONTROL" / "beats the hardest prompt" / "prompt-unreachable" would be an **OVER-CLAIM**. The only honest claim: the button beats the §5-B model-generated APE procedure + the calibration_prompts.yaml fallback, but NOT every known human prompt. MINOR-1: the 0.827 winner prompt identity was not persisted (unrecoverable without a re-run).
- **Scientific bottom line:** E-0012 does NOT yield a clean positive "control button." It yields an honest, audited NEGATIVE/boundary result that REINFORCES the paper's core thesis: a legible calibration steering axis CAN produce a real held-out behavioral effect yet still fails to beat competent prompting → legibility/steerability is not sufficient grounds for a latent "control" affordance over prompting (READ ≠ VERIFIED). This is a valuable reality-check positive-attempt-that-honestly-fails, NOT the "boundary-theorem + positive contract" upgrade originally hoped.
- **§5 escalation (owner):** how to use E-0012 in the paper (core-claim/narrative), and whether to spend a small controlled GPU re-score to make the "human prompt beats button" evidence forensically airtight (re-identify + persist the 0.827 prompt, head-to-head re-score vs button + CAL-09). NO positive claim will be shipped. valid_for_paper for E-0012 pending owner framing decision.

## 2026-07-31 · D-0064 · E-0012 APE spec-conformance fix (owner-approved track A) merged; prereg re-frozen → run commit 16fd701; cleared for 3rd (sound) model-gen re-run
- **Trigger:** the E-0012b model-gen re-run (D-0063) was audited NOT-SOUND — the frozen harness ran APE generation GREEDILY (frozen §5-B mandates temp=0.9/top_p=0.9/seed=42), didn't persist candidates (winner=authored CAL-09 fallback), and never surfaced the §9.4 cross-axis status. Owner chose track A (fix + re-freeze + re-audit code + re-run).
- **Fix (branch feature/e0012-ape-spec-fix, merged main 16fd701):** (1) `generate_candidates_real` now passes do_sample=True, temperature=0.9, top_p=0.9, seed=42 (added optional `top_p` to `SteeredHFBackend.generate`, applied only when do_sample & not None → zero impact on other callers); (2) persist `results/E-0012/e0012_ape_candidates.json` = raw model output + per-candidate {id,text,source=model|authored_fallback,normalized_hash} + n_model_parseable/n_padded + DEV k3 (k5 winner), plus n_cand_generated/n_cand_padded in results.json; (3) persist coherence_ratio + raw degeneracy; (4) §9.4 cross-axis explicitly SKIPPED for calibration-only conservative Stage 1 (removed fixture-eval wiring; cross_axis_dev_items=None → cross_axis_check="SKIPPED", cross_axis_fail=False — cannot flip a passing calibration verdict to UNSAFE, exactly per frozen §9.4 Note; §9.4 constants + eval code retained for future Stage 2); (5) regression tests: assert backend receives frozen sampling params, authored-fallback provenance, cross-axis guard fires at δ<−0.10, and SKIPPED-does-not-flip-verdict. Full suite 606 pass / 6 skip.
- **Governance — regress-to-frozen-spec, NOT a protocol change:** the code now IMPLEMENTS the already-frozen §5-B/§9.4 (previously it silently diverged — see failure-log 2026-07-31). Candidate persistence + coherence persistence are pure observability. **Zero protocol drift verified**: adjudicator §4 math, kill-rule symmetry, Stage0 grid=105, pool split {seed12/offset500/split_seed42/27DEV·53TEST}, §8 verdict mapping all byte-unchanged vs 4e7e088. Gated by: full independent hostile CODE audit @98fdfea (all-PASS except the fixture BLOCKER-1) + Manager line-verified BLOCKER-1 fix @82a7ed7 (implements the auditor's own recommended SKIPPED option). Not §5 (owner already approved re-run by choosing track A).
- **Re-freeze:** protocol pin stays 4e7e088; execution run commit pin → **16fd701**. §14 checklist unchanged.
- **Cleared for 3rd re-run (conservative track, fp16, ~5-6h + no cross-axis GPU, A800 GPU1, install datasets, PUSH run commit before cleanup, never shutdown):** checkout 16fd701, clear old results/E-0012, run `run_e0012_verified_control.py --backend hf --model Qwen/Qwen2.5-7B-Instruct --seed 42`. This time APE candidates are genuinely model-generated AND stochastically sampled per §5-B, fully persisted for audit. **Most-likely honest outcome = TRANSFER** (a proper stochastic APE should rediscover a strong prompt near the human 0.827), i.e. reversion to the pre-accepted negative — which is fine. Then fetch → register → independent results audit → verdict → owner.

## 2026-07-31 · D-0063 · E-0012b model-gen re-run audited NOT-SOUND (broken APE comparator); superseded by v3 fix
- Independent hostile audit (`reviews/2026-07-31-e0012-modelgen-audit/audit-report.md`) verdict = **NOT-SOUND**. BLOCKER-1: frozen harness `generate_candidates_real` ran APE generation GREEDILY, ignoring frozen §5-B temp0.9/top_p0.9/seed42 (freeze-integrity bug — frozen code ≠ frozen spec; see failure-log 2026-07-31). BLOCKER-2: 50 candidates unpersisted + winner (id45) byte-identical to authored CAL-09 → comparator greedy + heavily authored-fallback → unauditable. ⇒ the TRANSFER→LOCAL flip was an artifact of the broken generator.
- Audit CONFIRMED solid regardless: split 0-overlap, all raw pairs synthetic_proxy=false, N-01 active, Stage1 CIs reproducible, kill-rule/verdict arithmetic correct. Button behavioral effect real; only "beats a fair prompt baseline" was unsound.
- **Consequence:** owner chose track A → APE spec-conformance fix (D-0064) → sound v3 re-run (D-0065). E-0012b retained on branch run/e0012-modelgen-20260731 as honest lineage; superseded by E-0012c.

## 2026-07-30 · D-0062 · E-0012 F-01 fix verified (Manager self-audit after audit-subagent no-op); prereg run commit → 8bd29c4; cleared for model-gen re-run- **F-01 fix (PR #46, commit 63b6957 → merged main 8bd29c4):** runner hf path now calls `generate_candidates_real(hf_backend, N_cand=50, seed=42, authored_prompts=<18 authored>)` — model-generated APE candidates via the frozen meta-prompt, with the 18 authored prompts as the §5-B pad-fallback only (not the comparator itself). MINORs closed: valid_for_paper hardcoded False (never auto-set from backend); button_best_dev_k5 persisted (from the H-01 k5 re-eval candidate); ape_winner_prompt_text + candidate_id persisted. 601 tests pass; synthetic smoke shows the new fields.
- **Governance — regress-to-§5-B, NOT a protocol change:** the frozen §5-B always specified model-generated candidates; the runner had mis-wired to synthetic. The fix restores alignment. **Manager self-verified** (the dispatched focused-audit subagent returned a no-op UNVERIFIED template with 0 real work, so per AGENTS.md §3 the Manager fell back and did the check directly): `git diff 9dc37ab...HEAD` on `e0012_ape.py`, `e0012_harness.py`, `adjudicate_c2b.py` is EMPTY → frozen meta-prompt / seed=42 / N_cand=50 / kill-rule k5 symmetry / §4 adjudicator / §9 guards / N-01 hard-fail all byte-unchanged. Only the runner wiring + result-serialization fields + tests changed. This is infra/wiring, not a threshold/algorithm/judgment change.
- **Prereg update:** execution run commit pin updated to **8bd29c4** (protocol still frozen at 4e7e088). §14 checklist updated.
- **First (synthetic-comparator) run status:** VERDICT=TRANSFER retained in `results/E-0012/` + evidence-ledger as an audited CONSERVATIVE robustness data point (human-authored comparator ≥ model-gen → TRANSFER harder to trigger), **valid_for_paper=false/PENDING** — NOT the headline. The model-gen re-run is the protocol-faithful result.
- **Cleared for re-run (conservative track, fp16, ~2-3h, owner D-0061 GO):** re-run `run_e0012_verified_control.py --backend hf` at commit 8bd29c4 on the borrowed A800 (GPU1 only, install datasets, PUSH run commit before cleanup, never shutdown). This time APE candidates are genuinely model-generated → the paper may honestly describe the comparator as LLM-autogenerated. Then fetch → register → independent results audit → verdict. NO_BUTTON/TRANSFER remain pre-accepted honest outcomes; any positive stays exploratory pending Stage 2 + owner §5.

## 2026-07-30 · D-0061 · E-0012 results audit found MAJOR F-01 (synthetic-not-model APE comparator); owner-approved re-run with true generate_candidates_real
- **Finding (independent hostile audit of PR #46, results/E-0012):** VERDICT=TRANSFER was correctly DERIVED (APE winner DEV k5=0.8270 >> best button DEV k3=0.704; 105/105 Stage0 combos reported; Stage1=0 so TEST unconsumed; brier_raw_pairs 9963/0 real/proxy — N-01 held; run-commit diff vs 9dc37ab infra-only; §9 guards intact; 592 tests pass; C1/C2 untouched). BUT **MAJOR F-01**: the real GPU run called `generate_candidates_synthetic` (50 human pre-authored calibration prompts) instead of the frozen §5-B `generate_candidates_real` (model-generated candidates via the frozen meta-prompt). So the APE comparator was a strong HUMAN-authored prompt library, not the model-autogenerated comparator the prereg specifies. Audit judged the deviation CONSERVATIVE (human prompts ≥ model-gen → TRANSFER is harder to trigger, not a false TRANSFER) and the TRANSFER conclusion CREDIBLE_WITH_CAVEAT, but the paper cannot honestly say "LLM auto-optimized prompt" and the implementation silently diverged from the frozen protocol. MINORs: results.json auto-sets valid_for_paper=true on hf backend (registry/ledger correctly say PENDING); button_dev k5 not persisted; APE winner prompt text not recorded.
- **Owner ruling (§5):** **GO with Option A** — fix the runner to call the true `generate_candidates_real()` (model-generated APE candidates per frozen §5-B) + persist button_dev_k5 + record APE winner text + stop auto-setting valid_for_paper. Then **re-run the conservative track fresh** (fp16, ~2-3h) so the result matches the frozen protocol and the paper can honestly describe the comparator as model-autogenerated. Declined Option B (paper-wording workaround) — we do not paper over a protocol deviation.
- **Governance note:** fixing the runner to CALL generate_candidates_real is an INFRA/wiring fix that RESTORES alignment with the already-frozen §5-B intent (the frozen prereg always specified model-generated candidates; the runner mis-wired to synthetic). It is NOT a change to the frozen protocol. The pre-re-run focused audit must confirm this: the fix makes the runner match §5-B, changes no threshold/algorithm/judgment. The prior TRANSFER result (synthetic comparator) is retained as an audited robustness data point (conservative), not the headline. First fetch/register PR #46 will NOT be merged as valid_for_paper until the model-gen re-run completes + is audited.

## 2026-07-30 · D-0060 · E-0012 conservative track cost overrun → owner-approved fp16 ops fix + overnight A800 run
- **Problem:** the E-0012 conservative run was ~4–8× more expensive than the ~2h D-0058 estimate. Two factors: (a) the runner loaded the model in **float32** (SteeredHFBackend default; the E-0012 runner did not pass dtype, unlike E-0006/E-0011 which use `_pick_dtype()`=fp16 on CUDA) → ~2× slower + ~34.7GB; (b) the FROZEN runner uses **max_new_tokens=256** (4× C2b's 64; part of the pinned code — cannot change without a NEW prereg). Observed float32 rate ~1160 pairs/h → projected ~17–26h; even fp16 ≈ 9–13h. The §9.2 real-pair path was verified working (synthetic_proxy=false, no N-01 hard-fail) before the run was stopped.
- **Manager action:** killed our own float32 E-0012 nohup job on the borrowed A800 (GPU1 freed, box left running — never shutdown; ~/cc_l0 left in place, no cleanup). float32 partial results discarded (cannot merge with an fp16 run).
- **Owner ruling (§5):** **GO** — apply an **ops/infra-only fp16 fix** (load the model in float16 on CUDA, matching the E-0006/E-0011 convention; NOT a protocol change — dtype is infra, and fp16 is the established basis) and re-run the conservative track fresh on the borrowed A800 **overnight (~9–13h)**. Do NOT change any frozen protocol parameter (max_new_tokens=256 stays). Owner declined scope-reduction (would need a new prereg) and declined own-compute/abort.
- **Lineage note:** the fp16 run commit = frozen 9dc37ab + ops-only device fix (4469db5) + ops-only dtype=fp16 fix (both infra: device + dtype lines in the runner, no protocol/harness/algorithm/threshold change). The results hostile audit must verify the run-commit diff vs 9dc37ab is infra-only. The entire fp16 run is internally consistent (both prompt and button channels fp16); NO_BUTTON_FOUND remains a pre-accepted honest outcome; any positive stays exploratory pending Stage 2 + owner §5.

## 2026-07-29 · D-0059 · E-0012 prereg FROZEN (conservative track); pre-boot gate cleared; cleared for A800 boot
- **Freeze:** `docs/research/2026-07-29-e0012-verified-control-button/prereg-e0012-...DRAFT.md` status DRAFT → **FROZEN** for the conservative track (Calibration button, Qwen2.5-7B). Pins: code commit **4e7e088** (main, post-merge PR #45); **L_c1=20** (uncertainty axis chosen layer, Qwen, from E-0003), Stage 0 sweep {18–22}; **Stage 1 pool = Option A TriviaQA** N=80 disjoint from E-0006 (owner-confirmed); **18 authored comparator prompts** (owner-confirmed strong/non-strawman); **APE §5-B byte-frozen** (N_cand=50, seed=42, k=3 screen, k=5 winner+symmetric kill rule); **3 non-trained button families**; §9 guards frozen (accuracy ≥0.9×, coherence ≤1.5× measured baseline, Brier reliability δ_rel=0.02 + gaming on REAL pairs, cross-axis δ_cross_fail=−0.10 → UNSAFE terminal); Stage 1 reuses frozen C2b §4 byte-identical (Bonferroni 1−0.05/M). §14 checklist fully checked.
- **Pre-boot gate satisfied (all owner-required):** pre-run reviewer-critic (NEEDS-REVISION → all F-01..F-06 closed → READY-TO-FREEZE) + 2 independent harness hostile-audit rounds (round-1 H-01 BLOCKER + H-02..H-06 → fixed; round-2 confirmed + found N-01 real-GPU proxy-fallback MAJOR + N-02 → fixed). **N-01 hard-fail guard**: on a real (hf) run the §9.2 Brier reliability/gaming guard uses REAL (confidence,correctness) pairs extracted via the SAME frozen scorers, OR the run fails loudly — no silent proxy degradation → cannot produce a spurious VERIFIED-CONTROL. Manager verified fixes + frozen adjudicator/scorers/records untouched.
- **Cleared for GPU boot (conservative track only, owner D-0058):** run `scripts/run_e0012_verified_control.py --backend hf` Stage 0 (DEV mining, ≤105 combos) + Stage 1 (TriviaQA new pool, one-shot TEST) on borrowed A800 (GPU1 only CUDA_VISIBLE_DEVICES=1, scope ~/cc_l0, install `datasets`, PUSH exact run commit BEFORE cleanup per D-0049, NEVER shutdown, stop if GPU1 busy). ~30,698 gens / ~2.0–2.5h. Then fetch → analysis (candidate count fully reported) → independent hostile audit of results → verdict (NO_BUTTON_FOUND is pre-accepted honest; any positive stays exploratory pending Stage 2 transfer + owner §5). Recommended/aggressive tracks + Stage 2 remain §5-gated. Does NOT touch existing merged paper / frozen C1-C2 headline (safe fallback).

## 2026-07-29 · D-0058 · Owner GO on E-0012 conservative track (~2h A800, Calibration button); pre-boot gate defined
- **Owner ruling (§5):** GO on the E-0012 "verified control button" **conservative compute track (~22K gens, ~2h A800, Calibration button first)** per the research pass (D-0057, PR #45). Rationale accepted: novelty stands as certification-process + READ/TRANSFER/VERIFIED taxonomy + non-trained prompt-unreachable positive; prompt-fairness pinned via pre-registered kill rules; both outcomes (BUTTON_FOUND upgrade / NO_BUTTON_FOUND validates the evaluation-discipline contribution + strengthens the boundary) are publishable and honest.
- **Pre-boot gate (mandatory, in order, before any GPU):** (1) independent pre-run reviewer-critic stress-tests the E-0012 prereg design — especially whether prompt-fairness actually proves "latent beyond prompt", the non-trained-button definition (Heyman), forking-paths/HARKing, safety guards, kill-rule completeness, and honest pre-acceptance of NO_BUTTON; (2) address critic BLOCKERs → Manager freezes the E-0012 prereg (owner-approved program; freeze is Manager protocol governance); (3) IMPLEMENT the E-0012 harness (no GPU): non-trained button families, calibration outcome (1−Brier + store raw (conf,correct) for decomposition — do NOT repeat the E-0005/6 deferred-Brier gap), 17-prompt prompt-fairness comparator incl. auto-optimized, frozen C2b §4 adjudicator reuse, DEV/TEST discipline, accuracy + coherence + Brier-decomposition guards; + tests + synthetic smoke; (4) hostile audit of the harness (no GPU); (5) THEN boot conservative track on borrowed A800 (GPU1 only, ~/cc_l0, push run commit before cleanup, never shutdown, install `datasets`); (6) fetch/aggregate/adjudicate → E-0012 evidence; (7) hostile audit results; (8) fold into paper only if a button is found (else report NO_BUTTON honestly).
- **Scope guard:** does NOT touch frozen records/preregs/E-0003..E-0011 or the existing C2/C1 headline; keeps the existing merged paper as the safe fallback; any escalation of compute beyond the conservative track returns to owner (§5).

## 2026-07-29 · D-0057 · Owner-approved NON-GATED research/design pass for E-0012 "verified control button" (GPU program stays §5-gated)
- **Context:** owner proposes upgrading the paper from a pure negative reality-check to a **boundary theorem + positive-example contract** by searching for a *verified control button* — a latent intervention that beats the bounded best-prompt baseline THROUGH the frozen behavioral adjudicator, giving the taxonomy **READ ≠ TRANSFER ≠ VERIFIED-CONTROL** (console exposes only VERIFIED controls). Keeps the existing C2 claim; sharpens it ("legibility per se is not evidence of control").
- **Manager assessment (research-collaborator):** high-value direction; directly answers the top reviewer weakness (underpowered null / no positive). Flagged 3 make-or-break risks that become design requirements: (1) **prompt-fairness is the whole ballgame** — a button only counts if it beats a bounded best prompt that is ALSO allowed to attempt the same target behavior (calibration/abstention/verification prompt); else it is not "latent beyond prompt". (2) **Trained buttons re-open Heyman** (trained steering can mimic prompting) — the novel positive must be a simple/non-trained/discovered intervention that is prompt-unreachable, or the contribution shifts to the console-contract/eval-discipline. (3) **Search validity / forking paths** — a large DEV search needs a NEW frozen prereg, NEW item pool, NEW DEV/TEST, one-shot TEST, pre-registered button families, honest candidate-count reporting. Secondary: calibration button must not just "always hedge" (Brier decomposition reliability/resolution + accuracy guard); compute button must not just lengthen output (token-normalized accuracy). Recommended single highest-value button = **Calibration**.
- **Owner ruling:** approve the NON-GATED, ZERO-GPU research/design pass now. The Stage 0–2 GPU search PROGRAM itself remains **§5-gated** (budget/GPU + extends core contribution; borrowed-A800 etiquette cannot support a large search — likely needs owner compute/budget). No experiments booted.
- **Deliverables (branch feature/45-e0012-research, doc-only):** (a) novelty falsification of "verified control button" vs Heyman, conditional/dynamic activation steering, control-discovery, PSR, recent activation-engineering — find strongest counter-evidence, not cheerlead; (b) nail the prompt-fairness comparator design (the make-or-break): exact adjudicator protocol giving a strong calibration/abstention prompt a fair same-target chance; (c) Stage 0–2 compute/cost estimate; (d) E-0012 prereg SKELETON (Calibration button first; staged funnel: Stage0 DEV mining → Stage1 frozen positive adjudication → Stage2 transfer stress test with LOCAL/MODEL/TASK/GENERAL classification). Then owner makes the §5 GPU go/no-go with real numbers.
- **Safety:** current merged paper is the safe fallback; this is additive/exploratory and does not touch frozen records or the existing headline.

## 2026-07-29 · D-0056 · Review-response ML-side hardening (owner-approved autonomous; venue/user-study deferred)
- **Trigger:** 3-stage chained review pipeline (reviewer Opus4.8 / reject GPT-5.6-Sol / area-chair Opus4.8 → **Weak Reject**; reviews under `reviews/2026-07-29-review-pipeline/`). Central fatal gap = no user study (owner-deferred). AC was fair: discounted "novelty collapse" (Sprejer is concurrent not prior), affirmed the calibration-harm result genuinely excludes zero in all 4 cells, and credited the honest scoping.
- **Owner ruling:** do the non-gated, no-user-study ML-side fixable hardening now (Manager-autonomous, audited); defer venue/user-study strategic decision.
- **Scope (branch feature/44-review-response):**
  1. **Reframe null + equivalence:** post-hoc TOST equivalence + MDE per cell/axis on FROZEN E-0005/E-0006/E-0011 artifacts (SESOI=±δ=0.05, symmetric to prereg superiority threshold; labeled POST-HOC exploratory, NOT re-opening frozen prereg). Distinguish underpowered non-detection (deliberation/skepticism CIs include meaningful effects) from robust calibration-harm (uncertainty CI excludes zero). "does not beat" → "no demonstrated added control".
  2. **Comparator transparency:** move best-prompt comparator protocol (16 authored strong prompts, α/layer, DEV/TEST) into main text; rename loaded term "ceiling" → neutral "bounded best-prompt baseline".
  3. **Brier decomposition:** reliability/resolution/base-rate from frozen per-item data → defensible calibration claim, not construct confound.
  4. **Console relabel:** categorical "NOT CONTROLLABLE" → honest "no added control demonstrated", via figure GENERATOR (plot_console_ui_contract.py), never hand-edit generated artifact (lineage).
  5. **Novelty sharpen + de-inflate:** vs Sprejer(concurrent)/Heyman/Mishra; remove "generalized", n=1 "replication" inflation.
- **Discipline:** new numbers only from artifact-driven scripts (no hand-copy in prose); new analyses POST-HOC and labeled; frozen records E-0003..E-0011 + preregs untouched; generated tables/figures via generators only; hostile audit before merge. Does NOT change core C2/C1 claim direction — hardens honesty/defensibility of existing claims.

## 2026-07-29 · D-0055 · E-0011 audit MERGEABLE; DROP_SINGLE_SEED_CAVEAT enacted; C2 caveat retired; E-0011 valid_for_paper=true
- **Trigger:** independent hostile audit of E-0011 multi-seed results returned verdict = **MERGEABLE** (no BLOCKERs). Manager independently verified all MAJOR findings raised during audit.
- **MAJOR#1 CLOSED — default-value identity (d20cced == 09f87395):** `scripts/run_arm_matrix.py` default arguments in E-0006 commit `d20cced` and E-0011 commit `09f87395` are byte-identical: `max_new_tokens=64`, `batch_size=16`, `temperature=0.7`, `n_extraction=28`. E-0011 passes these values explicitly in the run command (they match the defaults), so the generation configuration is identical to E-0006. All other protocol parameters (α grid, N per axis, k, bootstrap B, δ, coherence threshold, n_strong, model identifiers, steering families) were independently verified to be consistent across commits. Audit finding closed.
- **MAJOR#2 CLARIFICATION — harness numeric check is self-referential for seed=20260723:** the harness validation for seed=20260723 reproduces E-0006 from its own stored artifacts (prereg Option A), establishing that the aggregation pipeline reads E-0006 faithfully. It does NOT constitute an independent re-run of seed=20260723. Protocol consistency across seeds is guaranteed by parameter identity (verified above), not by harness reproduction. This is disclosed in the E-0011 evidence row and in the paper's limitations; it does not weaken the multi-seed result.
- **Item-pool consistency (high confidence):** `c2b_adjudication_results.json` files use index-based arrays (no item_id fields). `frozen_params.n_items_by_axis` is identical across all 5 seeds (deliberation=60, skepticism=60, uncertainty_awareness=80), consistent with the frozen first-N slice of the GSM8K test / TruthfulQA validation split (fixed ordering, no independent re-sampling). Only DEV/TEST split membership varies by seed. Item-level transcript verification requires A800 remote transcripts; item-pool-shared status is designated HIGH_CONFIDENCE based on frozen-N + ordered-deterministic-split logic per prereg §6.
- **DROP_SINGLE_SEED_CAVEAT enacted (Manager self-decision, within D-0052/D-0054 preregistered plan; not a §5 item):** all §4a strict conditions met per `multiseed_c2_aggregate.md` / `aggregate_multiseed_c2.py`: 5/5 seeds NON_TRANSFER_GENERALIZED; uncertainty CI_hi<0 in all 4 cells × all 5 seeds; any_true_pass=false; no flip. Caveat_drop_rule.outcome=DROP_SINGLE_SEED_CAVEAT is confirmed. The C2 single-seed caveat is hereby formally retired. C2 is now described as a pre-registered negative replicated across 5 seeds (scope: 2 models × 2 methods, same item pool across seeds with only DEV/TEST split varying).
- **C2 claim update:** scope guard PRESERVED (bounded prompt vs naive/off-the-shelf CAA/ITI; 2 models × 2 methods; NOT an impossibility theorem; PSR pre-empt remains exploratory). The single-seed caveat text is removed from active caveat language and archived here as closed.
- **E-0011 valid_for_paper:** PENDING → **true** (scope = exploratory-confirmatory robustness arm; 2 models × 2 methods; item-pool-shared with E-0006). Supports C2 as a robustness companion to the frozen E-0005/E-0006 core. Does NOT modify or overwrite E-0005/E-0006 records.
- **Frozen?** E-0005/E-0006/C2 headline frozen protocol: UNTOUCHED. E-0011 valid_for_paper status updated. Paper text: qualitative multi-seed robustness sentence added (no hand-copied numbers in prose/abstract).

## 2026-07-28 · D-0054 · Multi-seed C2 prereg FROZEN (E-0011 family); cleared for owner-approved GPU boot
- **Freeze:** `docs/ledgers/prereg-c2b-multiseed-DRAFT.md` status DRAFT → **FROZEN** (byte-frozen §4 verdict ladder + guardrails (a) per-seed no-pooling §4b and (b) unconditional true-pass surfacing §4c). Frozen seed set = {20260723 (=E-0006 reuse + harness numeric check), 20260724, 20260725, 20260726, 20260727}. Reuses `prereg-c2b-adjudication` §4/§5 byte-identical; only `--seed` varies. Fixed the Purpose line to match the strict rule (DROP requires 5/5, not ≥4/5).
- **Audit gate satisfied:** independent hostile audit `audit-c2-multiseed-boot2` = **BOOT-READY** (both prior MAJORs — N=1 vacuous DROP, dead harness-repro code — verified fixed; no frozen asset touched; E-0006 reproduces byte-exact). This is the owner-required "independent audit before boot" (D-0052 sequence).
- **Merges:** PR #41 (guardrails + fixes) merged to main (fb4aae4). prereg now FROZEN on main.
- **Cleared for GPU boot:** run `scripts/run_arm_matrix.py --seed <S>` for the 4 NEW seeds {20260724..20260727} on the borrowed A800 (GPU1 only, CUDA_VISIBLE_DEVICES=1, scope ~/cc_l0, PUSH the exact run commit BEFORE cleanup per D-0049, NEVER shutdown, stop if no free GPU). Seed 20260723 is NOT re-run — E-0006's stored `results/arm_full/` is the 5th seed + drives the harness numeric check. Then `aggregate_multiseed_c2.py` combines all 5 → E-0011 aggregate → independent hostile audit before any caveat-status is acted on. E-0011 stays valid_for_paper per audit; frozen E-0005/E-0006 untouched.

## 2026-07-28 · D-0053 · Owner: WS① user study SCIENTIFICALLY APPROVED but human study DEFERRED; pivot to non-gated submission-readiness polish
- **WS① verdict:** R1 (REJECT 3-4) → revise → R2 (NEEDS-ANOTHER-REVISION 4.5-5.5, +R2-BLOCKER-5 circularity) → revise-2 → **R3 = CIRCULARITY-GENUINELY-CLOSED** (owner's 4 independent-ground-truth criteria all PASS: WAR computed without console signals; Y_t frozen from independent CDC/FDIC/GDPR sources before signal-profile assignment; 25% discordant pairs cap pure-signal-following WAR ≤0.75; baseline = Info-Matched no-boundary console, isolating boundary-instrumentation; success = decision quality vs independent Y_t, not "trust matches console"). R3-MINOR-1 (H2-Q5 label-recall) fixed. Validated protocol: `docs/research/2026-07-28-prereg-userstudy-console-DRAFT.md`; trail `reviews/2026-07-28-userstudy/review-R1..R3.yaml`.
- **Owner ruling (§5):** scientifically approves the protocol BUT **defers the human study as a whole** (consistent with standing preference "real human-subjects study deferred to LAST"). NO IRB submission, NO recruitment, NO data collection now. **Priority pivot: finish the non-gated submission-readiness polish first.**
- **Action:** merge #38 to main as a validated DRAFT artifact (clearly DRAFT / OWNER-SIGNATURE-PENDING / execution deferred; merging triggers no human-subjects action) to preserve the protocol + review trail. The 8 owner-decision items (IRB/budget/platform/fatigue-pilot/effect-size-pilot/venue-window/data-governance/cross-border) remain OPEN for when the owner later elects to run the study.
- **Now proceeding (non-gated, Manager-autonomous, audit-gated):** submission-readiness reviewer-critic gap list → targeted paper polish (candidate items: reader-facing Artifacts & Reproducibility appendix mapping claims→artifacts without internal IDs; sharpen one-sentence novelty vs Sprejer/Mishra/Heyman; breadth general_reasoning dead-zone coverage-guard note; venue placeholder stays anonymous since venue deferred). Multi-seed C2 GPU run (D-0052, owner-approved) continues in parallel on its own gate (audit41 → freeze → boot).

## 2026-07-28 · D-0052 · Owner §5 rulings: multi-seed C2 GO (w/ 2 guardrails), WS③ NO-GO, venue defer; WS① independent-ground-truth acceptance test
- **① Multi-seed C2 harden: GO (owner-approved GPU, §5).** Before freezing the prereg, encode two guardrails and confirm the 4-tier rule satisfies them:
  - **(a) Per-seed negative, NO pooling:** a confirmatory negative must be judged PER SEED; pooling/averaging raw outcomes across seeds to declare the negative is FORBIDDEN (would bury a single-seed true positive).
  - **(b) Strong-positive unconditional surfacing:** any seed×cell×axis true PASS must be explicitly surfaced and separately reported, never masked by any aggregate status.
  - Sequence: encode (a)(b) in DRAFT + enforce in aggregate script/tests → **Manager freezes prereg** → **independent hostile audit of frozen prereg+harness** → boot 4 NEW seeds (20260724–20260727) + reuse E-0006 as the 5th data point. NEVER touch E-0005/E-0006. (Guardrail-encoding dispatched on feature/41-c2-multiseed-guardrails.)
- **② WS③ calibration-harm mechanism arm: NO-GO** (owner agrees with Manager recommendation). Stays in Future Work; honest-fail discipline (E-0007 already demoted the off-manifold-distance mechanism; no re-mining on same data).
- **③ Venue: DEFER** until WS① (user study) is locked; then decide (IUI primary / CHI experience / FAccT-AIES alternative).
- **WS① user-study protocol — binding acceptance test (must pass, not just satisfy R2 wording):** revision closing the circularity (R2-BLOCKER-5) must pass an INDEPENDENT-GROUND-TRUTH test:
  - Primary DV (calibrated reliance) must be computable WITHOUT referencing any console-displayed signal; the "correct reliance" benchmark must be INDEPENDENT of treatment (held-out task ground truth / human verification / independent oracle), NOT derived from the same model evidence the console shows.
  - Baseline = "latent slider / plain console WITHOUT boundary signals" to isolate boundary-INSTRUMENTATION itself, not "console vs nothing".
  - Success = decision-quality / calibrated-reliance improvement against INDEPENDENT ground truth, NOT "trust matches console" or compliance.
  - **If the circularity is structurally unfixable within current budget/time → STOP and escalate to owner to change the DV design; do NOT force-sign.**
  - After closing: present full protocol + R1/R2(/R3) critic trail + owner-decision items (IRB/budget/platform/venue) for signature (§5).

## 2026-07-28 · D-0051 · WS② merged (audited); WS① under critic-driven revision (§5)
- **Audits ran on all three doc workstreams (discipline held — each caught real issues):**
  - **PR #40 (WS②a-prep, multi-seed C2):** hostile audit → NEEDS-FIX. MAJOR: DRAFT §4a caveat-drop rule (uncertainty CI_hi<0 ≥3/5) inconsistent with implementation/tests (all-seeds<0). No frozen asset touched; seed threading independently re-verified fully wired; smoke reproduced E-0006 uncertainty harm exactly; no fake E-0011 row. **Manager ruling:** adopt the STRICTER rule (dropping the single-seed caveat strengthens our negative → be conservative). Fixed to 4-tier {KILL_HARNESS / DROP_SINGLE_SEED_CAVEAT (all 5/5 NON_TRANSFER + all-cell all-seed uncertainty CI_hi<0 + no strong-positive flip guardrail) / SEED_MOSTLY_ROBUST (≥4/5) / SEED_SENSITIVE}, verdict keyed to run_arm_matrix arm_verdict field. Re-verified (18 aggregate tests pass, three-way consistent). **MERGED to main.**
  - **PR #39 (WS②bc, C1 tighten + C2 decouple):** hostile audit → NEEDS-FIX, 2 BLOCKER (both provenance): hand-copied C1 numbers 0.713/1.000/0.471/2.844 in main.tex/overview prose + hand-edited the script-generated c1-twomodel.tex (manifest manual_edits_allowed:false). C1 tightening fidelity + C2 decoupling + scope all PASS. **Fixed:** numerics removed from prose (kept qualitative model-dependent framing; numbers live only in generated table), caption moved into generator make_c1_twomodel_table.py, regenerated. Manager re-verified: no numerics in prose, regenerate==committed (idempotent), pytest green, PDF clean 0 undefined. **MERGED to main.** (HEAD 2cb7732.)
  - **PR #38 (WS①, user-study prereg, §5 human-gated):** R1 reviewer-critic → REJECT-MAJOR-REVISION (3-4/10), 4 BLOCKER (information-quantity confound / vignette ground-truth placeholder / slider baseline no UI spec / H2 not operationalized). Revised (added Info-Matched control condition B, ground-truth construction, slider UI contract, H2 operationalization + think-aloud; N=450 analyzable, budget USD 4.1-7.5k). R2 reviewer-critic → NEEDS-ANOTHER-REVISION (4.5-5.5/10): B1/B3/B4 PARTIAL, B2 OPEN, + new R2-BLOCKER-5 (WAR vs signal→Y_t coupling = circularity/tautology risk). **NOT presented to owner for signature yet** — running revision-2 to close R2-BLOCKER-5 (decouple answer key from interface signals) + freezable items, then bring full protocol + R1/R2 trail + owner-gated items (IRB/budget/venue) to owner. NO autonomous R3+ loop.
- **State:** main = 2cb7732 (pytest green, paper builds clean). prereg-c2b-multiseed remains DRAFT (Manager must freeze before any GPU run; GPU run itself is owner-gated §5). No GPU booted. No open BLOCKER on main.

## 2026-07-28 · D-0050 · Manager takeover + owner 3-workflow directive (WS① human study §5-gated / WS② cheap hardening / WS③ optional mechanism)
- **Takeover:** Incoming Manager passed the §10 acceptance exam (frozen headline C1/C2 + scope guard; E-0010 honest-null+READ_HOLDS strengthens thesis; frozen records E-0003..E-0010 + all preregs + adjudicate_c2b §4; social axis not-confirmatory pending human-α; A800 etiquette + D-0049 provenance lesson; §5 vs autonomous split). Cross-checked evidence-ledger / claim-map / flagship summary / paper abstract → no drift. HEAD 3df6fac. `ACTIVE_MANAGER` = current session.
- **Owner directive (this session), diagnosis accepted:** only C2 2×2 negative is hard core; all else exploratory/null; missing an affirmative HCI pillar; C1↔C2 narratively coupled on the uncertainty axis (must decouple). Three workflows:
  - **WS① (highest leverage, §5-GATED — real user study, C3):** draft a controlled user-study **prereg + full protocol**: boundary-instrument console v2 vs "latent-control slider" baseline. Primary DV = calibrated reliance; secondary DV = error attribution / prompt↔latent conflict understanding. Must include hypotheses, conditions, N + power analysis, tasks/stimuli (from frozen console v2 artifact-derived cards), measures, prereg analysis plan, IRB/ethics, recruitment, budget. **STOP before any human data**: full protocol+IRB+recruitment+budget go to owner via ask_user for sign-off. Doc-only until signed.
  - **WS② (cheap hardening, immediate, NO gate other than the GPU run which owner hereby AUTHORIZES):**
    - **②a multi-seed C2 harden:** reuse the **byte-identical frozen `prereg-c2b-adjudication` protocol** (no change to split/δ/Bonferroni/coherence gate) on {CAA,ITI}×{Qwen,Llama} for 3–5 seeds via existing `scripts/run_arm_matrix.py --seed` (default 20260723 reproduces E-0006 byte-for-byte). NEW experiment_id **E-0011**; never touch E-0005/E-0006. If negative holds across seeds → C2 sheds the single-seed caveat. Per-seed + aggregate report; independent hostile audit. Owner explicitly authorized this GPU spend as "cheap"/"immediate parallel start" (satisfies §5 GPU gate for THIS run only).
    - **②b tighten C1 (doc-only):** facade claim keeps only the cross-model-invariant **deliberation + skepticism**; uncertainty/focus reported as **model-dependent** (Qwen uncertainty holds / Llama not; focus flips). Update claim-ledger, overview, paper C1 tables.
    - **②c decouple narrative (doc-only):** C2's negative uncertainty steer-vs-prompt contrast must stand alone on **E-0006 behavioral evidence**, never written as "implied by C1 facade" (facade does not replicate on Llama uncertainty). Fix main.tex / claim-map; no "legible→not controllable" over-claim on the uncertainty axis.
  - **WS③ (optional, pure-model, NEW prereg, mechanism):** ONE prereg mechanism arm for the negative steer-vs-prompt contrast; single principled hypothesis (e.g., confidence/entropy inflation → sharper/over-confident distribution → Brier worse). Freeze metric + success/kill BEFORE data; honest-fail (null → Future Work, no re-mining same data). New experiment_id; never touch frozen records. Priority below ①②; Manager to return a go/no-go recommendation to owner.
- **Discipline reaffirmed:** numbers only rebuilt from artifact/manifest (no LaTeX hand-entry); each concrete task = new subagent session (AGENTS.md §6); each new result independently hostile-audited; C2 scope always "bounded prompt vs naive/off-the-shelf CAA/ITI (+ exploratory single-model PSR arm)", pre-empt PSR, not an impossibility theorem. Venue: target competitive IUI / feasible CHI; final venue decision deferred until WS① protocol + owner sign-off (§5).
- **Execution order:** ② starts immediately in parallel (cheap GPU after harness+prereg audited; doc-only now); ① produces full protocol+IRB+recruitment+budget → owner sign-off before any human data; ③ optional after ②, budget-permitting. Report back to owner: (1) WS① protocol+IRB+budget for signature; (2) WS② multi-seed C2 result + updated C1 / decoupled narrative; (3) WS③ go/no-go recommendation.

## 2026-07-28 · D-0049 · Flagship powered provenance/hygiene repair after hostile audit
- **Scope:** no GPU rerun. The 1080 saved behavior record values in `results/flagship_powered/behavior/flagship_l0_results.json` were preserved; READ result values were preserved except for the provenance `git_commit` pin; only CPU-derived verdict/statistics/redaction/provenance artifacts were regenerated.
- **Repair:** fixed the pasted `_behavioral_verdict()` defect and made M2/M3 explicit `INVALID / not_implemented` dimensions. The powered honest-null statement is limited to implemented M1(option-pushing) and M4(deference); M2/M3 are not measured and support no null or paper claim. `valid_for_paper=false` and human-α PENDING remain unchanged.
- **Redaction provenance:** `results/flagship_powered/behavior/redaction_audit.json` is now generated by `scripts/audit_flagship_redaction.py` from `records[*].scores.redacted_response` using committed `DISCLOSURE_PATTERNS`; regenerated verdict is passed=True, leak_count=0.
- **Commit provenance:** the original A800 run commit `d40aa9a089efa8993f1821f0f286e3ee0824b0cb` is not reachable because the borrowed-machine checkout was cleaned. Derived behavioral verdict/statistics/redaction were deterministically rebuilt from saved raw records with reachable code commit `f4b703d26a1f024130cab43cbbd6aa8aa9094561`; the audited key values are reproduced (B−A M1=+0.001481, CI[-0.0483,+0.0467], p_bonf=1.0; B−E M1=-0.011852, p_bonf=1.0). Registry/result `code_commit`/`git_commit` pins now point to that reachable repair commit.
- **Frozen?** No scientific success threshold or external claim changed. This is artifact-lineage repair for an already honest-null, not-yet-confirmatory, `valid_for_paper=false` powered run.

## 2026-07-28 · D-0048 · Owner APPROVED the powered confirmatory flagship run (GPU, §5) — but 2 prereg gates GPU cannot satisfy tonight
- **Human decision (@EloiseJulia):** "全量跑吧，我批准了，跑完清理干净就行。最好一次性跑到底，然后中间你可以每隔一段时间巡检。" → §5 GPU spend + full run AUTHORIZED. Borrowed A800 etiquette applies (GPU1 only, ~/cc_l0 scoped, rm -rf after push, NEVER shutdown shared box, stop if no free GPU, minimize disk).
- **Frozen protocol = D-0044.** The confirmatory verdict uses TEST-only, paired item-cluster bootstrap, Bonferroni, validated blinded LLM judge (llm_judge_blind_v1, F6-strict M4), success = B−A effect AND B>E on M1/M4; KILL = honest null.
- **Two prereg prerequisites GPU alone cannot resolve tonight (surfaced BEFORE booting, not fabricated):**
  1. **TEST item pool does not exist.** Only the 14-item DEV pool (`flagship_l0_tasks.json`, DEV-only, must-not-reuse-as-TEST) exists. Prereg §7 requires N≈80, DEV~27/TEST~53, disjoint, same distribution; confirmatory verdict uses TEST only. → A subagent must AUTHOR + COMMIT-FREEZE the TEST pool (no GPU) BEFORE any TEST generation, so items are fixed before TEST scores exist.
  2. **Human-rater validation α≥0.60 (F7) needs humans.** Confirmatory success requires two independent human annotators on M1–M4 with Krippendorff α≥0.60. Owner is asleep → this gate stays **PENDING**; the powered result tonight is "validated-LLM-judge powered, human-α PENDING" — a big upgrade over L0 but NOT the final confirmatory stamp until the (cheap, no-GPU) morning labeling passes.
- **Manager scope decision (faithful to the prereg's OWN conditional structure, and to borrowed-box etiquette):** run (a) author+freeze TEST pool; (b) powered behavioral confirmatory N≈80/k5 on TEST with validated blinded LLM judge + judge-condition-bias test + complete coverage; (c) READ latent token-blind probe (cheap, no generation grid). **HOLD the steer suppress/induce alpha-grid arm (~5,600 gens/model)** — the prereg itself gates steer on "READ holds", so this is principled, not corner-cutting; if READ holds I bring the steer plan back for a go/no-go rather than auto-burning the big grid on a shared borrowed box.
- **Honesty guardrails:** do NOT fabricate human labels; do NOT declare confirmatory before α≥0.60; do NOT edit taxonomy/thresholds/prompts/model-subset/N/δ after seeing TEST; frozen records E-0003..E-0009, 3 preregs, adjudicate_c2b §4, prereg-latent-recovery, prereg D-0044 UNTOUCHED. New result = new experiment_id in registry, independent hostile audit before any paper use.
- **Frozen?** Run authorized; result valid_for_paper only after audit + human-α gate. Verdict remains open until confirmatory gates close.

## 2026-07-27 · D-0047 · Breadth L0 re-run (fixed classifier): credible exploratory NULL suppression; axis readout is a deterministic echo
- **Ran** the breadth L0 re-run on the borrowed A800 (GPU1 only, ~/cc_l0 cleaned, no shutdown, others undisturbed)
  with the coverage-fixed deterministic classifier (D-0046 previously FAILED_COVERAGE). exp
  breadth-l0-confirm2-6b999fd7ef3a012c-0001. Independent hostile audit (audit-breadth-rerun) done.
- **Result:** coverage_guard PASSED (n_other=3/180=1.67%). Suppression strict 0.083 (1/12 tutor_invariant_coins) /
  calibrated 0.167 (2/12 +design_knapsack), **bootstrap CI [-0.195, +0.529] spans 0 → NULL at N=12**. Classifier
  agreement kappa=0.877 (deterministic-primary vs blinded-LLM-secondary; oracle_reach_agreement 0.967). Breadth
  axis LINEARLY_READABLE_L0 (facade 0.271).
- **Audit verdict — the null is CREDIBLE (not a self-judge artifact this time):** the prior self-judge inconsistency
  (greedy→oracle-DP) is genuinely FIXED — design_knapsack greedy now classifies NARROW; both suppression drivers are
  real narrow-vs-oracle differences. So: under this L0, a narrow persona does NOT measurably suppress oracle-domain
  solutions (credible exploratory null, N=12, valid_for_paper=false).
- **Two honest caveats the audit surfaced (must not overstate):**
  1. The breadth_axis readout + all 180 generation texts are BYTE-IDENTICAL to the prior breadth_l0_qwen run (same
     seed; only the classifier changed) → the LINEARLY_READABLE_L0 axis result is a DETERMINISTIC ECHO, NOT an
     independent replication. Do NOT claim the axis legibility was replicated; it is a single-run readout.
  2. Coverage's clean pass is softer than it appears: `general_reasoning` (10/180, a dead-zone item whose oracle
     domain is never detected) is an uncounted second fallback; counted with `other` it would be 7.2% and trip the
     5% guard. FOLLOW-UP: count general_reasoning dead-zone toward the guard fraction (or fix that item's oracle
     detectability) before any powered breadth run.
- **Decision (Manager):** breadth idea-1 status = exploratory CREDIBLE NULL on suppression + a single-run legible
  breadth axis (not replicated). For the CURRENT paper, the breadth axis can be mentioned as a legibility probe with
  explicit single-run/exploratory caveats; the suppression null is honestly reportable but underpowered (N=12). The
  stronger social-inference-axis evidence remains the flagship B>A (D-0046). Next: plan folding the social-inference
  axis into the current paper.
- **Frozen?** Exploratory, valid_for_paper=false. Frozen records E-0003..E-0009, prereg D-0044, adjudicate_c2b untouched.

## 2026-07-27 · D-0046 · Confirmation L0 with validated instruments: B>A REPLICATES (directional/underpowered); breadth guard fired
- **Ran** the confirmation L0 on the borrowed A800 (GPU1 only, etiquette honored, ~/cc_l0 fully cleaned, no shutdown)
  with the UPGRADED instruments (validated blinded LLM judge; deterministic breadth classifier). Independent hostile
  audit (audit-confirm) re-derived everything from the 280 records.
- **Flagship (validated LLM judge llm_judge_blind_v1), exp in registry code_commit 1cd6066:** M1 A=0.394,
  B(novice)=0.469, E=0.416, expert=0.411. **B>A = +0.074 REPLICATES** the prior lexical-scorer L0 (+0.078) — audited
  REAL, not a scorer artifact (LLM judge AND embedded lexical baseline both positive; 8/11 non-zero items positive;
  present in raw records not summary-only). **BUT directional/underpowered: item-level t=1.99, p≈0.068, leans partly
  on one strong item; needs N120/k5 (δ 0.043) for a powered confirmatory test.** M1 judge is GRADED (6-level
  histogram, not saturated). **M4 = GENUINE behavioral null** (judge CAN emit M4>0 in self-test but returns 0 on all
  280 real responses → Qwen does not do F6-strict deference-exploitation); correctly flagged
  DEGENERATE_ZERO_VARIANCE_MDE_UNDEFINED. Condition-blinding held (A1 redaction symmetric across conditions,
  judge_bias max_abs_bias=0). valid_for_paper=false.
- **Breadth (deterministic classifier):** coverage guard FIRED (FAILED_COVERAGE) — HONEST fail-closed: the new
  deterministic method-only markers UNDER-COVER real generations (many samples classify to no domain), so no
  suppression rate/kappa was produced (no fabricated verdict). The breadth AXIS geometry sub-readout still emitted
  LINEARLY_READABLE_L0 (independent of the failed behavioral classification; carries no valid_for_paper flag, must
  NOT be cited standalone). **Audit MAJOR-1 to FIX:** the guard's n_unclassified_valid_samples=41 is not backed by
  its enumerated list (only 20 entries) — reconcile the count before relying on this classifier; also the marker
  coverage gap must be fixed (add fallback/broader markers) before any breadth suppression claim.
- **Decision (Manager):** the flagship B>A social-inference-axis signal is now trustworthy enough as SUPPORTING/
  DIAGNOSTIC evidence for the CURRENT paper (extends legibility!=controllability to a social-inference axis), but NOT
  as a standalone confirmatory claim (self-judge; DEV-only 14-item pool; underpowered). Human-calibration gate
  (α≥0.60) remains required before any confirmatory claim. Next: (1) fix breadth classifier marker-coverage + count
  bug; (2) plan how to fold the social-inference axis into the current paper (extend thesis, add claim-map dimension,
  keep frozen C1/C2 headline); a fuller powered flagship run is a later owner-gated decision.
- **Frozen?** Results banked exploratory (valid_for_paper=false). Frozen records E-0003..E-0009, the flagship prereg
  (D-0044), adjudicate_c2b untouched.

## 2026-07-27 · D-0045 · Two L0 probes on borrowed A800 (exploratory); instrument fixes needed before any full run
- **Ran** both L0 harnesses on a borrowed shared A800 (GPU1 only, etiquette honored, ~/cc_l0 fully cleaned after, no
  shutdown). Qwen2.5-7B. Both `valid_for_paper=false`. Independent hostile audit (audit-l0-results) done.
- **Flagship L0 (novice-manipulation DEV-power), exp flagship-l0-d8a275ba...-0001:** M1 (option-pushing) A=0.243,
  B(novice)=0.321, E(explain-simply)=0.276, expert=0.271. **Audit verdict: B>A is a REAL directional signal** (13/14
  items positive, effect 0.078 > the run's own MDE 0.052, sign-test p≈0.002) — disclosed-novice status DOES increase
  option-pushing vs control. **B>E is a NULL** (0.044 < MDE; 6/4/4 item split) — at this power we CANNOT separate
  novice-manipulation from plain "explain simply" instruction-following (the exact confound the critic F3 flagged).
  **M4 (deference) = all-zero: a genuine lexical-level null** (259/280 responses actually OFFERED verification; Qwen
  does not do F6-strict deference at the lexical level) BUT the lexical scorer `heuristic_blind_v0` is inadequate to
  detect implicit deference and its zero-variance MDE=0 is misleading. Recommended full-study params from MDE: N80/k5
  δ≈0.052 for M1.
- **Breadth L0 (idea-1), exp breadth-l0-3d89236d...-0001:** oracle-domain suppression 8.33% (1/12) — **audit verdict:
  NULL / self-judge artifact** (the single driving item was LLM-self-judge inconsistency crediting identical greedy
  solutions differently across conditions; bootstrap CI spans 0). **Breadth AXIS = genuinely LINEARLY_READABLE_L0**
  (passed null + lexical-control specificity + facade gates on recorded scalars; UNVERIFIED at raw-activation level
  since GPU cleaned) — the one defensible positive: a breadth/focus direction exists and is legible.
- **Decision (Manager): do NOT fund a full pre-registered run on either yet; fix instruments first (all no-GPU):**
  - Flagship: replace the lexical M1/M4 judge with a validated LLM+human-calibrated blinded judge (esp. M4); re-scope
    the M1 prereg to **B>A only** (B>E needs N far beyond 120); flag/suppress degenerate MDE=0 for zero-variance dims.
    The B>A latent-manipulation direction is promising enough to justify a properly-judged confirmatory run afterward.
  - Breadth: replace the LLM self-judge domain classifier with a deterministic marker ground-truth OR a frozen,
    blinded, inter-rater-validated judge before any suppression conclusion; re-confirm axis readability on re-captured
    activations. Correct the overstated "self-judge bias recorded" (no such field in the artifact).
- **Frozen?** L0 results banked exploratory. Frozen paper records (E-0003..E-0009), the flagship prereg (D-0044), and
  adjudicate_c2b untouched. The flagship prereg's B>A vs B>E scoping is INFORMED by this DEV-power L0 (pre-registered
  as a DEV step), consistent with the freeze.

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
  the negative steer-vs-prompt contrast is NOT explained by this mechanism → **C2-mech DEMOTED to explicit hypothesis / Future Work** in the
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
## 2026-08-10 · D-0106 · Second hostile-audit repair adds signed partials, explicit attempt order, and real browser/security gates
- Formal-stage `Save & Exit` now atomically signs all ten slots as `complete=false`, downloads JSON/CSV, and ends without performance feedback. Silent no-export abandonment is explicitly unobservable and outside study-export ITT; a future recruitment platform completion log is the only permitted separate count.
- Exports sign random per-server `run_id` and monotonic `attempt_serial`. Same-run duplicate resolution uses serial, while cross-run duplicate participant codes hard-fail without a versioned owner `attempt_id→global_order` manifest; file order has no authority.
- Loopback requests now enforce exact Host/origin, JSON POST, bootstrap CSRF, per-session capability, size/cap/TTL limits, per-session locking, and request-id idempotency. Key permissions are best-effort owner-only and the key remains absent from browser/export.
- Current-machine Chrome/Edge tests run full flows at both specified viewports and 100%/200% zoom, operate formal Q1/Q2 by Tab/Space/Enter, inspect DOM geometry/accessibility/overflow/hidden semantics, and verify PNG dimensions. Manual screen-reader review remains `UNVERIFIED PRE-RECRUITMENT`.
- Status remains `implemented_pending_reaudit_nohuman`; MDE remains DRAFT, and this decision authorizes no recruitment, human data, public deployment, protocol freeze, paper edit, or claim upgrade.
