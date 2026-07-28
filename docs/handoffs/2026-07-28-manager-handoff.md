# Manager Handoff Bundle — cognitive-console — 2026-07-28

> Supersedes `2026-07-24-manager-handoff.md`. This is the primary re-entry point for the incoming Manager.
> Read this first, then `AGENTS.md` (operating constitution), then `AI-Instruction.md` (Part I/II/III), then the ledgers.
> Conflict order: Part I research red-lines > AGENTS.md > Part II/III. When in doubt and unable to decide, STOP and ask the owner.

---

## 0. One-paragraph state of the project

Core empirics are DONE, independently audited, and frozen. The paper is written, polished for IUI, de-jargoned to submission-readiness, and now **shows** a real console artifact. Since the last handoff (2026-07-24) we: (a) banked **E-0008** (Llama C1) and **E-0009** (PSR latent-recovery KILL); (b) built the social-inference exploratory axis end-to-end, ran the owner-approved **powered flagship confirmatory run** (E-0010), whose result is an **honest behavioral null on M1/M4 with the latent axis still READABLE (READ_HOLDS, AUC 0.954)** — cleanly generalizing "legibility ≠ controllability" from metacognitive axes to a social/user-model axis; (c) folded it into the paper as explicitly exploratory without touching the frozen C1/C2 headline; (d) ran a full **paper polish + de-jargon** pass (title softened, IUI UI-contract framing, submission hygiene); (e) built **console v2** (5-signal UI contract + exported paper figure). All merged to `main` via audited PRs #30–#37. HEAD ≈ `6cc830b`. No GPU running; borrowed A800 is clean.

**Current phase = paper hardening toward submission.** No unclosed BLOCKER. Remaining work is owner-gated decisions + optional polish (see §8).

---

## 1. Frozen thesis + headline (do not re-litigate)

- **Title:** *Legible Need Not Be Controllable: A Frozen Reality Check for Prompt-vs-Latent Behavioral Control in LLMs* (softened from "Is Not" to scope-guard against over-generalization; owner may veto).
- **Headline C1 (exploratory):** representational **facade** — the strongest readable prompt only reaches part of the extracted axis pole. 3/4 axes on Qwen2.5-7B (E-0003); replicated in aggregate on Llama-3-8B (E-0008) but with axis-composition heterogeneity (deliberation+skepticism invariant; uncertainty/focus flip).
- **Headline C2 (core scoped negative):** under a frozen, fairness-controlled, hostilely-audited DEV/TEST adjudicator, naive off-the-shelf CAA/ITI latent steering does **not** beat the bounded best-prompt ceiling on the adjudicated metacognitive axes; the **uncertainty axis consistently HARMS calibration** across the full {CAA,ITI}×{Qwen,Llama} 2×2 (E-0005 single cell, E-0006 generalized NON_TRANSFER).
- **Scope guard (must always accompany C2):** bounded prompt vs *naive/off-the-shelf* CAA/ITI on two 7–8B models. NOT an impossibility theorem. Pre-empt PSR / "Steer Like the LLM" (Heyman & Vandeputte) which shows *trained* steering can mimic prompting.
- **Contribution framing:** paradigm boundary (make the prompt↔latent behavioral gap an operable interface object + evaluation discipline), NOT a new steering method and NOT a baseline increment.

## 2. Evidence banked (docs/ledgers/evidence-ledger.md) — ALL FROZEN

| ID | What | Verdict / status |
|----|------|------------------|
| E-0003 | C1 facade @ Qwen2.5-7B, 3/4 axes | exploratory, valid_for_paper=false |
| E-0004 | early C2b crude-proxy | INVALID, superseded by E-0005 |
| E-0005 | C2 frozen adjudicator Qwen×CAA, 0/3 → KILL | hostile audit VALID_NEGATIVE |
| E-0006 | C2 2×2 {CAA,ITI}×{Qwen,Llama} all 0/3, uncertainty harm ×4 | VALID_ARM_EVIDENCE (core) |
| E-0007 | C2-mech off-manifold distance, 0/4 → NULL | VALID_NULL → mechanism demoted to Future Work (honest-fail) |
| E-0008 | C1 Llama-3-8B replication (3/4 aggregate, axis-heterogeneous) | audit mergeable, exploratory |
| E-0009 | PSR DEV-optimized latent-recovery arm → KILL_PLAN_D | VALID_NEGATIVE (robust to method strength), exploratory |
| **E-0010** | **social-inference axis (novice-disclosure): powered TEST behavioral honest-NULL on M1/M4 + READ_HOLDS (token-blind AUC 0.954)** | **science VALID (hostile-audited) + provenance-repaired (D-0049); exploratory, valid_for_paper=false** |

**E-0010 key numbers (from `results/flagship_powered/`):** N=54 TEST items, k=5 (1080 records). B−A M1 (option-pushing) = +0.00148, CI[-0.0483,+0.0467], p_bonf=1.0; B−E M1 = -0.0119, p_bonf=1.0; M4 (deference) = 0 (genuine null; judge self-test emits 1.0). M2/M3 = INVALID/not_implemented (support no claim). READ: layer 8, literal AUC 1.0, token-blind AUC 0.954 (drop 4.6pp, > null p95 0.786) → READ_HOLDS. Steer arm deliberately HELD; human-α calibration PENDING; LLM-judge-only; single-model/single-seed.

## 3. Frozen protocols (NEVER change post-hoc; any method change = NEW independent prereg)

- `docs/ledgers/prereg-c2b-adjudication.md` + `adjudicate_c2b.py` §4 judgment logic (byte-frozen).
- `docs/ledgers/prereg-robustness-mechanism-arm.md` (E-0006).
- `docs/ledgers/prereg-ood-capture.md` (E-0007).
- prereg-latent-recovery-arm Option 1 (D-0041/D-0042 → E-0009).
- `docs/research/2026-07-27-prereg-novice-manipulation-DRAFT.md` = FROZEN flagship prereg (D-0044): conditions A/B/E/C, M1–M4 taxonomy, blinded LLM judge (llm_judge_blind_v1, F6-strict M4), DEV/TEST discipline, success=B−A effect AND B>E, KILL=honest null, human-α≥0.60 gate.
- Frozen records E-0003..E-0010 and their result artifacts are immutable.

## 4. Code / build / test (verified)

- Package: `cognitive_console` (src-layout, Python 3.12). Install: `python -m pip install -e .`
- Tests: **`python -m pytest -q`** → 364 passed, 4 skipped (verified this session).
- Paper build: **`docs/paper/build.ps1 -Clean`** (MiKTeX pdflatex+bibtex) → `docs/paper/build/main.pdf`, ~7.5 body pages / 9 with refs, 0 undefined refs/cites.
- Console: `python -m cognitive_console.console --host 127.0.0.1 --port 8000 --open`; simulated demo report via `cognitive_console.console.demo`.
- Console paper figure: `python docs/paper/scripts/plot_console_ui_contract.py` regenerates `docs/paper/figures/console-ui-contract.pdf` bit-identical from frozen artifacts.

## 5. Decisions this cycle (docs/ledgers/decision-log.md, D-0041..D-0049)

- **D-0043** owner-approved GPU: ran Llama C1 (E-0008) + PSR arm (E-0009).
- **D-0044** flagship novice-disclosure prereg FROZEN (critic-hardened 10 fixes; Akbulut 2603.25326 scoop confirmed real).
- **D-0045/46/47** L0/confirm probes on borrowed A800: fixed instruments (validated LLM judge, deterministic breadth classifier); flagship DEV B>A directional but underpowered; breadth credible null + deterministic-echo caveat.
- **D-0048** owner-approved the **powered confirmatory flagship run** (GPU). Flagged 2 prereg gates GPU can't satisfy overnight: TEST pool had to be authored+frozen; human-α needs humans → PENDING. Steer arm HELD per READ-gate.
- **D-0049** provenance/hygiene repair after hostile audit of the powered run (fixed corrupted verdict fn, relabeled M2/M3, script-generated redaction audit, re-pinned reachable code_commit f4b703d because original A800 run commit d40aa9a was lost to borrowed-box cleanup). Values reproduced bit-exact from saved records.

## 6. PRs merged this session (all hostile-audited before merge)

- **#30** fold social-inference axis into paper (exploratory).
- **#31** D-0044 powered flagship behavior + READ run (honest-null M1/M4, READ_HOLDS) + provenance repair.
- **#32** update paper to powered null + READ_HOLDS (retire directional-B>A story honestly).
- **#33** IUI-target surgical polish (title softened; abstract de-jargoned; social axis demoted to Discussion-only; C3 folded into C2-derived evaluation discipline; added 5-signal console UI-contract paragraph; plain-novelty sentence; C2 CI footnote; figure Descriptions + CCS/keywords).
- **#34** console v2 (5-signal affordance cards + social "LEGIBLE but NOT CONTROLLABLE" card + PSR panel + exported figure; 364 tests).
- **#35** fold console figure into paper Design Implications.
- **#36** submission-readiness de-jargon (compiled PDF + all figures scrubbed of internal IDs/paths/tokens; lineage kept in YAML).
- **#37** de-dup console figure evidence-tier phrasing (NIT).
- Plus direct-to-main: E-0010 evidence entry; D-0048/D-0049; **`docs/paper/overview-zh.md`** (Chinese internal overview for owner, commit 6cc830b).

## 7. Owner (@EloiseJulia) standing preferences (also in stored memories)

- Communicate in **Chinese**.
- The brainstormed ideas (persona-breadth, novice-disclosure, register) **enrich the CURRENT paper, not a next paper**.
- Real human-subjects study is deferred to LAST; current phase is pure-model.
- Internal PR self-merge into `main` is authorized AFTER an independent hostile audit passes gate (Manager decides). This is a repo-specific exemption from "never self-merge".
- Honest-fail discipline: never re-mine mechanism on the same data after a null; never dress exploratory as confirmatory.
- Borrowed A800 etiquette (STRICT): host 10.172.211.158 user elzhang; GPU 1 ONLY (`CUDA_VISIBLE_DEVICES=1`); scope to `~/cc_l0/`; `rm -rf ~/cc_l0` after pushing results; NEVER shutdown (shared); stop if no free GPU; minimize disk. Fast HF download (~31 MB/s). **Push the exact run commit BEFORE cleanup** (else lineage breaks — see D-0049).
- §5 escalation (owner decides): core Claim/RQ/venue change; GPU/paid-API/budget; human-subjects/IRB/privacy/licensing; external submission/release; changing any frozen protocol/record; upgrading exploratory→confirmatory; deleting irreproducible data.

## 8. Immediate next steps for the incoming Manager

**Owner-gated decisions currently OPEN (do not execute without owner sign-off):**
1. **Steer induce/suppress arm go/no-go (GPU §5).** READ_HOLDS satisfies the prereg's steer gate, but behavioral baseline is null (nothing to suppress); only the "induce" direction (can +α·u_naive manufacture manipulation?) has scientific value, at ~5,600 gens/model on a borrowed box. **Manager recommendation: HOLD** — write the clean null+READ story instead. Bring options if owner asks.
2. **Human-α labeling for the social axis (no GPU).** Two independent annotators on M1–M4, Krippendorff α≥0.60, to close the confirmatory gate. Prepare a labeling sheet for the owner when asked.
3. **Final venue (§5).** IUI primary (full-paper acceptance ~24–25% in 2023–25), CHI experience track secondary, **FAccT/AIES a genuine alternative** (prereg-heavy honest negatives + safety fit; no user study expected). Biggest reject risk at any HCI venue: "no user study / interface unevaluated" — partially mitigated by the console instantiation.

**Non-gated optional polish (Manager can do, audit-gated):**
- Venue placeholder in the PDF still reads `Conference'17, Washington DC` (sigconf default) — fine while anonymous; set when venue is fixed.
- `general_reasoning` dead-zone must be counted toward the breadth coverage guard BEFORE any powered breadth run.
- Consider a short "Artifacts & Reproducibility" appendix (reader-facing) that maps claims→artifacts without leaking internal IDs into the body.
- Optional: submission-readiness gap checklist; sharpen the one-sentence novelty vs Sprejer/Mishra further if desired.

## 9. Ledger / dir map

```
docs/handoffs/       ← THIS FILE (2026-07-28) + startup prompt; prior 2026-07-24 bundle
docs/ledgers/        decision-log.md (D-0001..D-0049), evidence-ledger.md (E-0003..E-0010),
                     claim-ledger.md, hypothesis-ledger.md, experiment-registry.yaml,
                     open-risks.md, prereg-*.md (FROZEN)
docs/research/       novelty/SOTA/prereg drafts (incl. FROZEN flagship prereg 2026-07-27)
docs/paper/          main.tex, claim-map.yaml, citation-map.yaml, references.bib,
                     build.ps1, overview-zh.md (Chinese overview), figures/, tables/,
                     figure-manifests/, table-manifests/, scripts/
docs/specs/          console-v1.md, phase0-pilot.md
src/cognitive_console/  package incl. console/ (server, data_loader, demo), social/, experiments/
results/             frozen artifacts (flagship_powered/, arm_full/, psr_qwen_primary/,
                     ood_capture/, llama_c1_facade_*, c2b_adjudication_*, breadth_confirm2/, console_v1_demo/)
tests/               pytest suite (364 tests)
```

## 10. Acceptance exam (incoming Manager must answer before updating ACTIVE_MANAGER)

1. What is the frozen headline (C1 + C2), and what is the exact scope guard that must always accompany C2? Why does PSR / Heyman & Vandeputte force that guard?
2. What is the E-0010 result in one honest sentence, and why does a behavioral NULL + READ_HOLDS *strengthen* rather than weaken the paper's thesis?
3. Which records/protocols are frozen and must never be modified? Name at least the preregs, adjudicator, and the E-IDs.
4. Why is the flagship social-axis result NOT confirmatory yet, and what exactly is PENDING to make it so (no GPU needed)?
5. What is the borrowed-A800 etiquette, and what specific provenance mistake (D-0049) must never be repeated?
6. Which current items are §5 owner-gated vs Manager-autonomous? Give the steer-arm and internal-PR-merge examples.

**On passing:** update `ACTIVE_MANAGER` (state it in-session; this project has no separate marker file — announce takeover to the owner), then proceed. Do NOT boot GPU or take any §5 action without owner approval.

---

*Prepared by outgoing Manager (context near saturation) 2026-07-28. HEAD ≈ 6cc830b. No GPU running; A800 clean; no open BLOCKER.*
