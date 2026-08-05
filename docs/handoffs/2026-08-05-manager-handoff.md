# Manager Handoff Bundle — cognitive-console — 2026-08-05

> Supersedes `2026-07-28-manager-handoff.md`. This is the primary re-entry point for the next Manager.
> Read this file first, then `AGENTS.md`, `AI-Instruction.md`, the opening report, `docs/ledgers/decision-log.md` D-0074..D-0090, and the current paper.
> Conflict order: Part I research red-lines > AGENTS.md > Part II/III. If uncertain, stop and ask the owner.

---

## 0. One-paragraph state

The paper has moved from a chained hostile-review **REJECT** to an independently reassessed **BORDERLINE for IUI (about 30–35%)**. The current paper is an honest, scoped negative about bounded/naive single-layer additive CAA/ITI, not an impossibility claim about latent control. F1 (calibration-format confound) is addressed; F3 (unsupported console/user-benefit claim) is resolved by making the model-evidence evaluation contract the primary methodological contribution; F2 (no passing latent positive control) is no longer fatal but remains the main MAJOR risk. E-0014 and E-0015 showed that prompts move behavior while naive additive latent steering does not, even after raw-magnitude scale correction within a coherent 0.5–0.66× residual-norm ceiling. An appendix-level logit diagnostic shows the refusal direction strongly changes target first-token probability mass but still yields 0/5 scored refusals, strengthening `representational push != behavioral control`. The owner has authorized one final high-impact attempt to close F2: **E-0016 Arditi all-layer refusal-direction projection ablation**, using benign XSTest Regime B first. E-0016 implementation exists only on an isolated branch and is still at the hostile code-audit gate. No E-0016 GPU run or result exists.

## 1. Frozen paper claim and required scope guard

- **Current title:** *Legible Need Not Be Controllable: No Demonstrated Superiority over Bounded Prompts under Bounded Naive CAA/ITI Steering*.
- **Primary contribution:** a methodological evaluation contract for latent-control affordances:
  `READ / TRANSFER / bounded-prompt comparator / calibration-warning / evidence-tier`.
  The console is a reality-check instantiation over frozen audited model artifacts, **not** a user-validated benefit claim.
- **C1:** exploratory representational facade measurement. Readability is a precondition/diagnostic, not proof of control.
- **C2:** under the frozen prompt-vs-latent adjudicator, bounded/naive additive CAA/ITI (`h + alpha*u`, `alpha<=24`) shows no demonstrated superiority over bounded best prompts on the tested axes/models.
- **Required scope guard:** this is about tested bounded/naive, single-layer additive CAA/ITI on the tested 7–8B models and tasks. It is **not** a theorem that latent control is impossible, and it does not cover trained, multi-layer, projection/ablation, or other intervention families.
- **Calibration wording is delicate:** the robust negative is a **steer-vs-bounded-prompt contrast**. Direct steer-vs-baseline is near zero in the rechecked Qwen/CAA lineage (compliance +0.011; `1-Brier` +0.0008). Never say steering directly harms calibration without this qualifier.

## 2. Evidence arc since the prior handoff

| ID | Result | Paper status |
|---|---|---|
| E-0011 | Five split seeds all preserve NON_TRANSFER; strong-positive guard never triggers | Core robustness; shared item pool caveat disclosed |
| E-0012 | Attempted verified-control-button search invalidated by four real-vs-placeholder bugs | **INVALID, terminated, no paper leakage** |
| E-0013 | CAA×Qwen format-confound recheck: complete-case steer-vs-prompt calibration contrast −0.34 CI[−0.51,−0.17]; worst-case bounds straddle 0 | F1 addressed but bounded honestly |
| E-0014 | Refusal positive control under bounded unit-direction CAA: prompt refusal 95%, latent refusal 0% | Endpoint live; latent-arm sensitivity not established |
| E-0015 | Raw-magnitude scale-corrected CAA on refusal + 3 metacog axes: every latent cell NO-PASS; random uncertainty direction detected −0.24 CI[−0.36,−0.12] | Genuine scoped null; under-scaling excluded within coherent range; F2 still open |
| E-0015 diagnostic | At coherent beta=1, refusal-leading first-token mass +13.9 nats on average but 0/5 scored refusals; one +16.9 item has byte-identical completion | Appendix-level qualitative support; `valid_for_paper=false`; representational push != behavior |

### E-0015 exact honesty constraints

- Coherent perturbation ceiling is about **0.5–0.66× residual-stream norm**, not 1×.
- The only about 1.05× point (refusal beta=2) is degenerate.
- MDE is about 0.19, so nulls do not prove effects smaller than the registered margin are absent.
- The first-token logit proxy counts tokens such as `I` that can start ordinary/hedged answers; `+13.9` must always be bound to `0/5 scored refusals` and never presented as “handle works”.

## 3. Current paper state

- Main paper: `docs/paper/main.tex`.
- Chinese internal map: `docs/paper/overview-zh.md`.
- Build: `docs/paper/build.ps1 -Clean`.
- Latest audited build: **14 pages**, zero em-dash, no undefined cites/refs.
- Latest critic: **BORDERLINE**, IUI acceptance estimate **30–35%**.
- Most likely rejection reason: no passing latent positive control plus no user study.
- F1 addressed; F3 resolved; F2 is MAJOR, not fatal.
- Actual external submission remains owner §5. The Manager must not submit.

## 4. E-0016 — exact handoff state

### Owner decisions already made

- D-0088: GO on a genuinely different positive-control method: Arditi-style refusal-direction projection ablation.
- D-0089: **Regime B first**:
  - Generation only on benign XSTest-safe prompts.
  - DEV baseline false-refusal must be `>=0.25`.
  - If below 0.25: emit `INVALID_REGIME_B_UNDERPOWERED`, stop, and ask the owner whether to escalate.
  - Harmful Regime A generation is **not authorized**. It requires a fresh owner safety/licensing decision.
- Harmful prompts may be used only for **forward-pass activation extraction** for the refusal direction; no harmful generation and no raw harmful text committed.

### Design

- `docs/research/2026-08-04-ablation-positive-control/design.md`
- `docs/research/2026-08-04-ablation-positive-control/prereg-e0016-DRAFT.md`
- Design commit on main: `728a0d7`.
- Pass rule: refusal-rate reduction `>=0.25`, paired bootstrap CI excludes 0 positively, coherence passes, random-direction ablation does not pass.
- Scope guard: a pass establishes assay sensitivity to a known-effective **non-metacognitive, different-method** latent intervention. It does not validate metacognitive control or naive additive CAA/ITI and does not weaken the scoped negative.

### Implementation

- Worktree: `.worktrees/e0016`
- Branch: `feature/e0016-ablation`
- Commit: `c1c4d90`
- Reported local state: full tests pass; synthetic smoke `PASS`.
- Defaults:
  - XSTest: `Paul/XSTest:train`, safe subset.
  - Harmful contrast: llm-attacks canonical AdvBench raw CSV, forward-pass only.
  - Harmless contrast: `tatsu-lab/alpaca:train:instruction`.
  - Gated `walledai/*` sources hard-failed.
- Dataset availability checked on A800:
  - `Paul/XSTest` available, 450 rows.
  - `natolambert/xstest-v2-copy` available.
  - `walledai/XSTest` and `walledai/AdvBench` gated.

### Audit/gate state

- A fresh background audit was launched as `audit-e0016-code` immediately before retirement.
- **No verdict was recovered into the repository before handoff.**
- A new Manager may not be able to read the old runtime agent. If the result is unavailable, launch a fresh hostile audit of `main...feature/e0016-ablation`.
- Do not merge, freeze, or run GPU until:
  1. all audit BLOCKER/MAJOR findings are closed;
  2. the branch is re-audited SOUND;
  3. prereg is frozen with exact run commit/command;
  4. owner approves the benign Regime-B GPU budget.

### High-risk audit checklist

1. All-layer hook exactly implements `h <- h - (h dot r_hat) r_hat` at every block/token/forward and cleans hooks in `finally`.
2. Upfront ablation hook-bites verifies the component is removed at every layer and is non-vacuous; dtype-calibrated fp16 tolerance.
3. One shared HF model handle only.
4. Harmful prompts are forward-pass-only and never written raw; generation is XSTest-safe only.
5. DEV eligibility stops before TEST when false-refusal `<0.25`.
6. TEST selection has no leakage; pass rule and random-direction specificity are exact.
7. Real-not-smoke/data guards have non-vacuous tests.

## 5. A800 state and etiquette

- Host: `elzhang@10.172.211.158`; SSH key: `$HOME\.ssh\cc_a800`.
- Workspace: `~/cc_l0/repo`; venv `~/cc_l0/venv`; HF cache `~/cc_l0/hf_home`.
- Qwen2.5-7B cached. `Paul/XSTest`, GSM8K, TruthfulQA, TriviaQA were cached/verified during this session. Alpaca/AdvBench may still need pre-cache/check.
- Prior constitution said GPU1-only. The owner later explicitly said “找空的就能跑”; treat this as permission to use any **free** GPU, but never interfere with another user’s process. Check all GPUs first.
- Never shutdown. Push exact run commit/results before cleanup. No GPU was running at retirement.

## 6. Failure lessons that must survive Manager rotation

1. E-0012 had four distinct placeholder-vs-real bugs: synthetic comparator, wrong APE sampling, random directions labeled real, fake fixture data. Runtime provenance guards are mandatory.
2. Guard correctness matters: an fp16-miscalibrated hook-bites threshold wasted about 1.5 GPU-h. Run every cheap fail-closed guard upfront before generation and calibrate across the full parameter grid.
3. Share one HF model handle; duplicated 7B loads nearly caused OOM in E-0015.
4. Save transcripts/logits when mechanism interpretation matters.
5. Negative results are publishable; never tune after TEST to force a pass.
6. Raw harmful prompts/outputs must never be committed or published.

## 7. Stale state to ignore

The session-local SQL todos `ws1-signoff`, `ws2a-guardrails`, `e0012-fetch`, and `e0012-results-audit` are historical leftovers. Do **not** resume them. E-0012 is terminated and invalid. Repository ledgers supersede session SQL.

Historical branch `feature/46-e0012-results` and several `run/e0012-*` branches are stale. Do not merge them.

## 8. Immediate next steps for incoming Manager

1. Pass the acceptance exam in §10 and announce takeover.
2. Recover or repeat hostile code audit for `feature/e0016-ablation`.
3. Triage findings; send fixes to a fresh implement subagent; re-audit.
4. If SOUND, merge harness, freeze `prereg-e0016-FROZEN.md`, register exact run commit/command.
5. Ask owner for Regime-B GPU budget sign-off. Do not assume D-0089 is GPU approval.
6. Pre-cache/check `Paul/XSTest`, Alpaca, and the local hashed AdvBench source.
7. Run DEV eligibility only. If `<0.25`, stop and ask owner before harmful Regime A.
8. If eligible, run TEST once, push artifacts, hostile results audit, then integrate only if valid.
9. Re-run a final reviewer-critic after any passing E-0016 result.
10. External IUI submission remains owner-gated.

## 9. Key file map

```text
docs/handoffs/2026-08-05-manager-handoff.md  <- primary re-entry
docs/paper/main.tex                          <- current 14-page paper
docs/paper/overview-zh.md                    <- owner internal map
docs/ledgers/decision-log.md                 <- D-0074..D-0090 current arc
docs/ledgers/failure-log.md                  <- placeholder/guard lessons
docs/ledgers/experiment-registry.yaml        <- experiment lineage
docs/research/2026-08-04-ablation-positive-control/
  design.md
  prereg-e0016-DRAFT.md
scripts/run_e0016_ablation_positive_control.py  <- branch only until audit/merge
results/E-0015-scale-corrected-positive-control/
results/E-0015-logit-delta/
```

## 10. Acceptance exam

The incoming Manager must answer these before executing:

1. What exactly is the current C2 claim and its mandatory scope guard? Why is “latent control is impossible” forbidden?
2. Why is the calibration result a steer-vs-prompt contrast rather than direct steering harm? Give the direct Qwen/CAA numbers.
3. What did E-0015 establish, and what did it fail to establish? State the coherent perturbation ceiling and MDE caveats.
4. Why does the logit diagnostic strengthen `READ != CONTROL` without proving a working behavioral handle?
5. What is F2’s current status after E-0015, and why can E-0016 close it without threatening the headline?
6. What exactly did the owner authorize for E-0016, and what remains prohibited/gated?
7. What are the E-0016 branch/worktree/commit and current audit state?
8. Name the runtime guards that must pass before any GPU generation.
9. What stale SQL/branches must not be resumed?
10. What are the A800 etiquette and run-lineage requirements?

**On passing:** announce takeover in-session. Do not merge E-0016, freeze its prereg, or use GPU until the listed gates are satisfied.

---

*Prepared by outgoing Manager on 2026-08-05. Main was clean at handoff preparation; pre-handoff HEAD `1d7d7a7`. No GPU running. E-0016 remained isolated and unaudited for merge.*
