# Manager Handoff Bundle — cognitive-console — 2026-08-11

> **唯一 primary re-entry。** 本文件取代
> [`2026-08-05-manager-handoff.md`](2026-08-05-manager-handoff.md)。
> Incoming Manager 先完成本文末尾接管考试并宣布接管；在此之前不得编辑、派发或改变 gate。
> 接管后，旧 Manager 立即只读退休，禁止双 Manager 并行调度。

## 0. One-paragraph state

当前主线是一篇以 IUI 为目标、writing-first 的 comparator-bound interface-evaluation-method paper：它不再把贡献写成“latent steering 普遍失败”，而是提出一个可审计 gate，要求可读 latent axis 在获得 control affordance 前，以预注册 margin、coherence 和 bounded prompt comparator 证明增量行为收益。当前 CAA/ITI×Qwen/Llama worked application 没有任何 latent arm 获得 control；不同轴的证据分辨率不同，且 calibration 只能写成 steer-vs-bounded-prompt contrast。8 月 6–7 日已经完成多轮 writing、artifact-consistency、layout、abstract 和 nearest-neighbor 修订，但这些修改之后**没有新的独立 full-paper reviewer verdict**，所以旧的 30–35%、35–50% 或其它 acceptance probability 都已 stale、不得复用。证据 ceiling 未变：无 passing latent behavioral positive control、无 user study、E-0016 无科学结果。Micro-study 网站已实现、完成 hostile-audit repair 并在 `b7043d2` 合并，但仅 **READY FOR OWNER PREVIEW**；没有 recruitment、pilot 或 human data authorization。

## 1. Frozen/current paper claim and mandatory scope guard

- **当前标题（逐字来自 `docs/paper/main.tex`）：**
  *When Does a Legible Latent Axis Earn a Control? A Comparator-Bound Evaluation Contract for Latent-Control Interfaces*
- **当前研究问题：** 一个可读 latent axis 需要什么证据，才有资格在界面中成为 control，而不只是 diagnostic？
- **主贡献：**
  1. comparative actionability criterion；
  2. five-field record：READ / TRANSFER / BOUNDED PROMPT COMPARATOR / CALIBRATION WARNING / EVIDENCE TIER；
  3. frozen CAA/ITI×Qwen/Llama worked boundary。
- **Mandatory scope guard：** 当前经验结论只适用于 tested 7–8B models/tasks 与 frozen method-specific single-layer additive CAA/ITI convention，系数 `alpha<=24`。CAA 使用 `s_CAA=1`，ITI 使用 `s_ITI=sigma_L`；这不是共同 injected-norm 上界。
- **禁止写法：** 不得写 latent control/activation steering 普遍不可能、prompt 与 latent 等价、所有 null 已被证明、或 contract 已改善用户理解/依赖/收益。
- **Coherence exact wording：** `g_steer <= 1.5*g_baseline + 0.02`；`0.02` 是 additive floor，代码中的 `1e-12` 仅为浮点比较容差。
- **READ exact boundary：** C1 是 exploratory CAA-style contrastive-direction measurement；它不能把 READ verdict 自动授予 ITI。

## 2. Paper writing and PDF state

- Source: [`../paper/main.tex`](../paper/main.tex)
- Internal map: [`../paper/overview-zh.md`](../paper/overview-zh.md)
- PDF: `docs/paper/build/main.pdf`
- Build command from repository root:

  ```powershell
  .\docs\paper\build.ps1 -Clean
  ```

- 2026-08-11 fresh rebuild: **12 pages**, **655631 bytes**, no undefined citations/references.
- Fresh-build SHA-256:
  `C9E1D804F7DE70362F5AEEB8B390C9A821A780099C38391C82EFB1B30CFD5D52`
- PDF generation is not byte-deterministic across rebuilds; after any paper-source edit, rebuild and record the newly generated hash instead of expecting this hash to persist.

### Latest independent reviewer status

- The last committed independent full-paper critic is
  [`../../reviews/2026-08-03-final-acceptance-critic/review-final-IUI.yaml`](../../reviews/2026-08-03-final-acceptance-critic/review-final-IUI.yaml):
  `MINOR-POLISH-THEN-SUBMIT`, with a then-current 35–50% estimate.
- That review predates substantial 2026-08-05..07 rewriting, artifact repairs, title/framing changes, abstract changes, and Bo/Golden-Gate integration.
- Therefore its qualitative residual ceiling remains useful—**no user study; no passing latent positive control; bounded method scope**—but its wording verdict and probability are stale.
- The older `BORDERLINE`, 28–40%, 30–35%, chained-review reject, and any other numeric probability are also stale and **must not be quoted as the current paper score**.
- Required next action is a fresh independent reviewer pass on current `main`, not another unbounded self-polish loop.

## 3. Repository, origin, worktrees, PDF, and server snapshot

### Git

- Audited scientific/content base HEAD before this handoff commit:
  `b7043d28481c30eaf8c84575f884fd63f970591f`
- At audit time, local `main` was **62 commits ahead of `origin/main`**.
- This documentation commit makes the expected post-commit count **63 ahead**; verify with:

  ```powershell
  git rev-list --count origin/main..HEAD
  ```

- Do **not push** as part of handoff or takeover.
- Preserved untracked owner file:

  ```text
  投稿前对照分析_Legible-Latent-Axis_2026-08-06.docx
  ```

  It is user-owned input. Do not add, modify, delete, move, or commit it.
- No `ACTIVE_MANAGER` file exists; none was invented. Manager state remains pending until the incoming session passes the exam and announces takeover.

### Worktrees

There is no active implementation task to resume. The following linked worktrees/branches are historical and already merged into `main`; treat them as **obsolete/read-only until deliberately pruned**, not as active queues:

```text
.worktrees/e0016                    feature/e0016-ablation
.worktrees/e0016-addedtoken-fix     fix/e0016-addedtoken-serialization
.worktrees/e0016-freeze             docs/e0016-protocol-freeze
.worktrees/e0016-retry-lineage      run/e0016-retry-lineage
.worktrees/iui-hci-rewrite          feature/iui-hci-rewrite
.worktrees/microstudy-web           feature/microstudy-web
.worktrees/paper-abstract-gate      fix/paper-abstract-gate
.worktrees/paper-actionability-pass feature/paper-actionability-pass
.worktrees/paper-evidence-gated-rewrite feature/paper-evidence-gated-rewrite
.worktrees/paper-floatbarrier-fix   fix/paper-floatbarrier-layout
.worktrees/paper-math-layout        fix/paper-math-layout
.worktrees/paper-method-artifact-reframe feature/paper-method-artifact-reframe
.worktrees/paper-opener-cleanup     fix/paper-opener-cleanup
.worktrees/paper-preflight-surgical fix/paper-preflight-surgical
.worktrees/paper-review-polish      feature/paper-review-polish
.worktrees/paper-steering-neighbors feature/paper-steering-neighbors
```

Do not resume stale E-0012 branches or any historical session-local todo.

### Micro-study preview server

- Ephemeral snapshot at handoff: `http://127.0.0.1:8876/` returned HTTP 200.
- PID at handoff: `37600`.
- Command line:

  ```powershell
  python -m cognitive_console.microstudy --host 127.0.0.1 --port 8876 `
    --verification-key-file .runtime\microstudy-preview.key
  ```

- PID/port are ephemeral facts. Recheck before relying on them; never kill by process name.

## 4. Evidence arc and immutable wording

| Evidence | What it supports | Mandatory limit |
|---|---|---|
| E-0013 | CAA×Qwen complete-case format recheck remains negative: about `-0.337`, CI `[-0.508,-0.165]` | Post-generation conditioned; adversarial bounds `[-0.478,+0.250]` cross zero; other 3 cells unverified |
| E-0014 | Refusal endpoint live: prompt refusal about 95.5%; bounded latent CAA 0% | Not a passing latent positive control; natural direction norm about 216 vs injection up to 24 |
| E-0015 | Raw-magnitude CAA weakens under-scaling within coherent range; pipeline detects random-direction movement | All latent arms NO-PASS; coherent ceiling about `0.5–0.66×||h||`; near `1.05×` point degenerate; null MDE about 0.19 |
| E-0015 logit diagnostic | First-token refusal-leading mass shifts (`~+13.9` nats at coherent beta=1) | `0/5` scored refusals; proxy includes ordinary starts such as `I`; `valid_for_paper=false`; supports no claim |
| E-0016 | Attempt 1 lineage and audited serialization repair only | **No DEV, TEST, scientific result, paper evidence, or positive-control pass** |

### Calibration wording

- Safe wording: **steer-vs-bounded-prompt negative calibration contrast under the frozen scorer**.
- Direct Qwen/CAA steer-vs-baseline is near zero: compliance `+0.011`, `1-Brier +0.0008`.
- Never collapse this into “steering directly harms baseline calibration.”
- E-0013 mitigates but does not identify the all-generation effect: complete-case support and worst-case bounds must travel together.

### Positive-control ceiling

- Endpoint responsiveness and assay sensitivity are not the same.
- E-0014 shows the endpoint responds to prompting, not that the latent arm can pass.
- E-0015 shows substantial coherent perturbation and detectable behavioral movement, but still no passing latent behavioral positive control.
- Therefore the evidence ceiling is unchanged: the paper may present a scoped qualification boundary, not a universal null.

## 5. E-0016 run, budget, GPU, and failure lineage

- Protocol: [`../research/2026-08-04-ablation-positive-control/prereg-e0016-FROZEN.md`](../research/2026-08-04-ablation-positive-control/prereg-e0016-FROZEN.md)
- Exact retry run/code commit: `c094f07fa3592c2210f46caba9e69c49a5a92fad`.
- Attempt 1 failed before direction extraction, hook-bites, DEV, eligibility, and TEST because tokenizer `AddedToken` was not JSON serializable.
- Attempt 1 consumed at most `0.00722222` A800 GPU-hours.
- Owner-approved hard cap remains 3 A800 GPU-hours; remaining cap is at most `2.99277778`.
- Retry remains authorized only under the unchanged benign Regime-B protocol, but it is now lower priority than the writing pass.
- No harmful generation, Regime A, or raw harmful text is authorized.
- If DEV baseline false-refusal is `<0.25`, the run must emit `INVALID_REGIME_B_UNDERPOWERED` and stop before TEST.
- A real retry still requires exact clean commit, free-GPU recheck, lineage persistence, and independent hostile results audit before any paper use.

### Free-GPU snapshot (ephemeral, 2026-08-11)

Remote A800 snapshot showed no fully unused device:

```text
GPU0 58734/81920 MiB, util 0%
GPU1 28982/81920 MiB, util 2%
GPU2 11690/81920 MiB, util 2%
GPU3 57271/81920 MiB, util 100%
```

Other users had active allocations/processes. Do not infer that low utilization means free; re-run `nvidia-smi`, inspect processes, and avoid interference. No E-0016 process was running.

## 6. Newly verified nearest neighbors and citation redlines

### Bo et al., UIST 2026

- Verified paper: *Steerable Chatbots: Exploring Personalization Control Interfaces via LLM Activation Steering*.
- Exact role: SELECT/CALIBRATE/LEARN personalization interfaces, Gemma-2-9B-IT, exploratory within-subject `n=14`, including an **unscaffolded PROMPT baseline** and heterogeneous preference findings.
- Safe contrast: Bo supplies exploratory user evidence about steering-interface designs; this paper supplies a per-affordance, preregistered, comparator-bound model-evidence qualification gate.
- Redlines:
  - do not claim Bo lacks a prompt baseline;
  - do not claim this paper is the first steering interface;
  - do not inherit Bo’s user evidence;
  - do not imply blanket superiority in Bo.

### Golden Gate Claude

- Verified official Anthropic 2024 research demonstration: 24-hour Claude 3 Sonnet feature-amplification demo, explicitly distinct from role-play/system prompting.
- Safe role: neutral public motivation that internal-feature amplification became visible.
- Redlines:
  - not a product claim;
  - not evidence of behavioral superiority, user benefit, or our tested SAE scope;
  - say only that the public demonstration did not state a matched prompt-comparator qualification.

### Goodfire

- Goodfire is intentionally omitted from the paper’s direct narrative/citation set.
- Do not add vendor/platform claims, or use it as a shortcut for Huang/Bo/Sprejer, without a fresh primary-source verification and a concrete argumentative need.

## 7. Micro-study website and protocol state

- Merge/base commit: `b7043d28481c30eaf8c84575f884fd63f970591f`.
- Implementation plus hostile-audit repairs are merged.
- Operational label: **READY FOR OWNER PREVIEW ONLY**.
- The preregistration remains **DRAFT / NOT FROZEN**.
- There is **no recruitment authorization, no public deployment, no timing pilot authorization, and no human data**.
- Ethics, recruitment, participant contact, assignment roster, and any actual run are owner responsibilities and human-gated.
- Construct: structured application of a four-state contract under Contract UI vs information-matched Flat Panel; not calibrated reliance, trust, benefit, or latent-control effectiveness.
- Primary: `CCA = 1 iff Q1 correct AND Q2 correct`.
- Primary paired sign-flip MDE remains `UNVERIFIED_NOT_ESTIMATED`.
- The implemented sign-binomial MDE tool is **DRAFT assumption sensitivity only** and cannot justify recruitment/sample size.
- Manual screen-reader evaluation remains `UNVERIFIED PRE-RECRUITMENT`.

### Preview/run commands

Current live preview:

```text
http://127.0.0.1:8876/
```

Documented owner-preview launch:

```powershell
python -m cognitive_console.microstudy --host 127.0.0.1 --port 8765 `
  --verification-key-file .runtime\microstudy-verification.key `
  --max-sessions 100 --session-ttl-seconds 7200 --open
```

Key path is owner-held and gitignored. The current ephemeral preview uses:

```text
.runtime\microstudy-preview.key
```

Analysis:

```powershell
python -m cognitive_console.microstudy.analysis analyze export1.json export2.json `
  --verification-key-file .runtime\microstudy-verification.key `
  --assignments frozen-owner-assignments.csv `
  --attempt-order-manifest frozen-attempt-order.json `
  --json-out microstudy-summary.json --csv-out microstudy-participants.csv
```

DRAFT sensitivity only:

```powershell
python -m cognitive_console.microstudy.analysis mde --n 20 `
  --json-out microstudy-mde-DRAFT.json
```

The attempt-order manifest is required only when a participant code spans server run IDs. Never expose or commit the key, exports, assignments, or participant-linked files.

## 8. Writing-focused priorities

1. **Fresh current-paper reviewer pass.** Freeze current `main` bundle and ask a new independent IUI reviewer to identify only current high-confidence blockers/majors.
2. **Triage before editing.** Write a bounded Manager disposition: accept/rebut/clarify/defer/reject; explicitly cap the revision scope.
3. **Prose and claim-lineage pass.** Prioritize title/abstract/introduction/related-work/conclusion consistency, citation redlines, claim-map/evidence-ledger alignment, and removal of stale internal-review language.
4. **Compile after every paper-source update.** No batch of `.tex`, `.bib`, figure/table source, or paper YAML edits is complete without `.\docs\paper\build.ps1 -Clean`.
5. **Micro-study only when owner directs.** Default is preview-only; do not drift into recruitment, data collection, protocol freeze, or paper integration.
6. **E-0016 lower priority.** Do not spend GPU merely because budget remains. Resume only if the owner/Manager decides its expected information gain exceeds writing work and all run gates remain satisfied.

## 9. Do-not-repeat lessons

1. **Audit scope creep:** reviewers do not own the roadmap. Triage findings and cap re-review to closure conditions; avoid endless audit expansion.
2. **Reference internal notes:** paper prose must cite public/verifiable sources or artifacts, not handoffs, decision logs, reviewer probabilities, or internal labels.
3. **Stale PDF:** never report title/page count/hash from memory; rebuild after every paper-source edit.
4. **Generated artifact edits:** do not hand-edit generated tables, figures, or numeric LaTeX. Change source artifact/generator, regenerate, and audit lineage.
5. **Comparator framing:** always name bounded prompt comparator; never translate steer-vs-prompt into steer-vs-baseline harm.
6. **ITI scaling exactness:** `h'_L=h_L+alpha*s_m*u_m`, `s_CAA=1`, `s_ITI=sigma_L`; `alpha<=24` is not a shared norm cap.
7. **Coherence exactness:** `g_steer <= 1.5*g_baseline + 0.02`; do not simplify to a pure `1.5×` rule.
8. **Evidence-state exactness:** failed, underpowered, unstable, untested, diagnostic-only, and withheld-control are distinct interface states.
9. **Citation novelty:** Bo and Golden Gate narrow the novelty claim; they are not decorative citations.
10. **No scientific resurrection:** E-0016 attempt 1 is an infrastructure failure, not a null, pilot, or partial result.

## 10. Stale state, branches, and tasks not to resume

- All E-0012 result/modelgen/settling-grid branches and tasks are invalidated historical lineage.
- Old paper worktrees are merged snapshots, not active revision queues.
- Old E-0016 worktrees are lineage snapshots; the only valid retry pin is `c094f07...`, and no run should start from a worktree merely because it exists.
- The old 2026-08-05 handoff’s E-0016 pre-fix queue, 14-page PDF, title, audit status, GPU-budget-pending wording, and 30–35% estimate are obsolete.
- Session-local SQL todos from older Managers are not authoritative. Repository ledgers and this handoff are.
- Do not resume stale Reviewer findings without checking whether current `main` already closed them.

## 11. Human-only decisions and hard gates

Incoming Manager must stop and ask the owner before:

- changing core Claim/RQ/venue;
- external submission/public release;
- recruitment, ethics/IRB activity, owner timing pilot, participant contact, or human data collection;
- freezing or changing the DRAFT micro-study protocol;
- changing any frozen protocol;
- exceeding E-0016’s remaining GPU cap or using paid/private resources;
- authorizing harmful generation or Regime A;
- upgrading exploratory/micro-study evidence to confirmatory/core paper evidence;
- deleting/overwriting irreplaceable data;
- committing or otherwise taking ownership of the untracked DOCX.

Internal writing work, isolated worktrees, independent reviews/audits, ledger synchronization, and audited merges to local `main` remain Manager-controlled.

## 12. Exact next dependency graph

```text
Acceptance exam + read-only verification
  -> announce unique Manager takeover
  -> freeze current-paper review bundle at exact HEAD/PDF hash
  -> fresh independent IUI reviewer pass
  -> Manager bounded triage/disposition
  -> isolated writer worktree for accepted findings only
  -> build PDF after every paper-source edit
  -> independent claim/citation/artifact-lineage hostile audit
  -> if SOUND: merge to local main
  -> rebuild PDF on main + record title/pages/hash
  -> one targeted closure re-review if required
  -> stop; external submission remains owner-gated

Owner directs micro-study preview
  -> recheck server/key/privacy state
  -> owner-only preview
  -> STOP (no recruitment/data)

Owner/Manager explicitly reprioritizes E-0016
  -> verify clean c094f07 pin + protocol + remaining budget
  -> recheck truly free GPU and other-user processes
  -> DEV eligibility
     -> <0.25: INVALID_REGIME_B_UNDERPOWERED + stop/ask owner
     -> >=0.25: one TEST run within cap
  -> persist lineage
  -> independent hostile results audit
  -> only audited valid evidence may enter a future paper decision
```

Avoid endless review loops: a fresh review gets one bounded revision cycle plus, if needed, one targeted closure re-review. New unrelated asks are triaged separately, not appended opportunistically.

## 13. Acceptance exam — answer all 10 before acting

1. State the current exact paper title, research question, three contributions, and mandatory method/model/task scope guard.
2. Why must calibration be described as steer-vs-bounded-prompt? Give the direct Qwen/CAA steer-vs-baseline numbers and E-0013 missingness limit.
3. What did E-0014 and E-0015 establish, and why is there still no passing latent behavioral positive control?
4. Why can the E-0015 logit diagnostic not support READ, TRANSFER, or “the handle works”?
5. What exactly happened in E-0016 attempt 1, what budget remains, and which scientific results exist?
6. What is the current micro-study authorization boundary, and which DRAFT/MDE/accessibility items remain unverified?
7. What are the current Git base, expected origin-ahead count after the handoff commit, untracked owner file, obsolete-worktree rule, PDF path/pages, and ephemeral preview URL/PID?
8. State the Bo UIST 2026 and Golden Gate citation redlines, and explain why Goodfire remains omitted.
9. Which actions are human-only, and what must happen to the old Manager immediately after takeover?
10. Recite the immediate writing dependency chain and the rule that prevents endless audit expansion.

**Pass condition:** answer from repository evidence, verify mutable facts, then announce:
“我已通过接管考试并成为唯一 Manager；旧 Manager 现只读退休。”

---

## Incoming Manager Startup Prompt（完整复制粘贴）

```text
你是 cognitive-console 的唯一 Incoming Manager。用中文工作。你的主焦点是论文写作与投稿前证据一致性，但也可以按依赖图调度其它任务。你本人只做调度、gate、triage、账本与决策，不亲自改代码、论文正文、实验脚本或结果；每个具体编辑、研究、实验都派给全新的独立 subagent。每个结果与每次 pre-merge 都必须由另一个全新、无上下文、敌对、只报不修的 audit/reviewer subagent 独立检查。

禁止双 Manager：你只有在通过接管考试并明确宣布接管后才成为唯一 Manager；宣布后，旧 Manager 立即只读退休，不再派发、编辑、合并或决策。

你的第一阶段只有“接管考试 + 只读核验”，不得编辑、commit、push、派发任务或运行实验：

按以下顺序完整阅读：
1. docs/handoffs/2026-08-11-manager-handoff.md（唯一 primary re-entry）
2. AGENTS.md
3. AI-Instruction.md Part I，尤其 §2–§5、§8–§10、§13，以及 Manager rotation/acceptance exam
4. docs/ledgers/decision-log.md 的 D-0074..latest
5. docs/ledgers/claim-ledger.md
6. docs/ledgers/evidence-ledger.md
7. docs/ledgers/experiment-registry.yaml 中 E-0013/E-0014/E-0015/E-0015-logit/E-0016/microstudy
8. docs/ledgers/failure-log.md、open-risks.md、compute-ledger.md
9. docs/paper/main.tex、overview-zh.md、claim-map.yaml、citation-map.yaml、references.bib、submission-evidence-ledger.md
10. docs/specs/microstudy-contract-application.md
11. docs/research/2026-08-10-microstudy-contract-application-DRAFT.md
12. docs/plans/microstudy-contract-application-web.md
13. README.md 的 Local micro-study preview
14. docs/research/2026-08-04-ablation-positive-control/design.md 与 prereg-e0016-FROZEN.md
15. results/E-0016-regime-b-confirmatory 的 failure lineage（只读）

随后只读核验：
- git status、HEAD、origin/main..HEAD ahead count、recent log、worktree list；
- 保留未跟踪的“投稿前对照分析_Legible-Latent-Axis_2026-08-06.docx”，不得 add/edit/delete/commit；
- 从 main.tex 抽取精确标题；
- 运行 .\docs\paper\build.ps1 -Clean，核对 docs/paper/build/main.pdf 的页数、hash、undefined cite/ref；
- 核对 http://127.0.0.1:8876/ 与 PID（它们是 ephemeral）；
- 核对 micro-study merged at b7043d2，仅 READY FOR OWNER PREVIEW，无 recruitment/data authorization；
- 核对 E-0016 只有 pre-DEV infrastructure failure + serialization repair，无科学结果；
- 若检查远程 GPU，只做 nvidia-smi 只读检查，不干扰他人进程。

然后逐题回答 handoff §13 的 10 道接管考试。答案必须包含 current claim/scope、calibration comparator、E0013/14/15/logit/E0016、microstudy gate、Git/PDF/server、Bo/Golden/Goodfire、human-only gates、writing dependency graph。回答完成后明确宣布：
“我已通过接管考试并成为唯一 Manager；旧 Manager 现只读退休。”

接管前不得做任何编辑。接管后也不得 push、对外投稿/发布、招募/接触参与者、收集 human data、启动 owner timing pilot、暴露 verification key、改变/冻结 microstudy protocol、改变 frozen protocol、超 GPU 预算、运行 harmful Regime A，除非对应 owner/human gate 已明确通过。用户提供 DOCX 永远保持 untracked，除非用户另有明确命令。

所有论文 source 更新后都必须立即运行：
.\docs\paper\build.ps1 -Clean
不得用 stale PDF；不得手改 generated tables/figures/numbers。

接管后的立即 writing workflow 固定为：
1. 在 current main/PDF exact snapshot 上派一个全新的独立 IUI reviewer；
2. 你做 bounded triage，逐项 ACCEPT/REBUT/CLARIFY/DEFER/REJECT，限制为一个 revision cycle；
3. 为接受项创建隔离 worktree，派 writer subagent，只改授权范围；
4. 每次 paper source edit 后编译 PDF；
5. 派全新的 claim/citation/artifact-lineage hostile auditor；
6. SOUND 后才合并 local main；
7. main 上重建 PDF；
8. 仅在 closure condition 需要时做一次 targeted re-review，然后停止。

不要让 reviewer 无限扩张审计范围；reviewer 不能拥有 roadmap。Micro-study 默认只做 owner preview，只有 owner 指令才调度；E-0016 优先级低于当前 writing pass，不能因为还有预算就自动运行。
```

*Prepared on 2026-08-11. This handoff makes no new scientific decision and authorizes no push, submission, recruitment, human data, protocol change, or GPU run.*
