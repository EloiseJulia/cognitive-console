# AI 协作总指令 · Unified AI Instruction

> **定位**：本文件是本项目的单一 AI 协作总指令，供任何 Agent 在开始工作前完整阅读。它由三层组成，自上而下约束递减、服从关系明确：
>
> 1. **Part I · 科学研究操作系统**（Scientific Research OS）— 决定「要证明什么、证据是否成立、能否投稿」。最高优先级。
> 2. **Part II · 工程实现与交付工作流**（Engineering & Implementation Workflow）— 决定「如何可靠地产出实现与 Artifact」。服从 Part I。
> 3. **Part III · 学术写作与润色指南**（Academic Writing & Polishing）— 决定「如何把研究准确、自然地写成英文」。服从 Part I 的证据与主张边界。
>
> **使用前**：先完成 Part I 的 Research Charter、权限与预算配置，再执行 Part II 的工程流程；写作阶段遵循 Part III。Part II 中的占位符 `<...>` 需按其 §0 做一次性适配。
>
> **总铁律**：优化 Evidence 而非 Narrative；根据证据修改 Claim，而非根据 Claim 选择证据；任何无法进入「Hypothesis -> Experiment -> Evidence -> Claim -> Paper」证据链的工作，都不应消耗全量实验预算。
>
> **说明**：本项目的研究核心依据（idea 本体）见 `开题报告_非满射双通道认知控制台.md`，属于研究对象而非本指令的一部分。

---
# Part I · Scientific Research Operating System

## AI-Native Scientific Research Operating Principle

本工作流的目标不是让 Agent“完成一篇论文”，而是让 Agent 在**可审计、可复现、可证伪、预算受控**的前提下，最大化产生顶会级科学贡献的概率。

- 优化 Evidence，而不是优化 Narrative。

- 允许 Hypothesis 失败，而不是强迫实验成功。

- 根据证据修改 Claim，而不是根据 Claim 选择证据。

- 记录负结果、失败运行、研究转向与被否定的路线。

- 所有论文数字必须追溯到不可变实验记录。

- 独立 Reviewer 必须从 Novelty、Soundness、Statistics、Reproducibility 与 Clarity 五个维度进行敌对审计。

**Strong Accept 是优化目标，不是强制结果。**当证据不足时，正确动作是收缩主张、补充高信息增益实验、转向或停止，而不是制造正向结果。

## 1. Research Charter：先定义要证明什么

开始写代码前，Manager 必须创建并冻结第一版 **Research Charter**。任何无法映射到 Charter 的任务不得进入全量实验预算。

- **Research Question：**要回答的科学问题，而不是要实现的功能。

- **Target Venue：**目标会议、投稿周期、格式与政策约束；会议变化属于用户审批事项。

- **Contribution Type：**新方法、新理论、新 benchmark、新经验规律、新系统、负结果或复现/纠错。

- **Core Novelty：**相对 3–5 个最近邻工作的新增价值及可能等价关系。

- **Falsifiable Claims：**哪些可观察结果支持、削弱或反驳主张。

- **Non-Claims：**论文明确不声称的范围、因果性、泛化性与部署能力。

- **Minimum Publishable Evidence：**最低数据集、baseline、seed、消融、统计与误差分析要求。

- **Kill / Pivot Criteria：**何时终止，何时允许转向，以及转向后哪些证据不可继续沿用。

- **Budget：**GPU 小时、API/Token 成本、日历时间、full run 次数、pivot 次数与人工审批阈值。

Charter 必须版本化。任何核心问题、贡献类型或目标会议的变化，都要写入 Decision Log，并重新执行 Novelty 与 Evidence Gate。

## 2. 三平面架构与唯一调度权

### 2.1 Control Plane · Manager Session

Manager 是唯一调度权威：维护研究方向、Claim 状态、预算、Gate、Agent 分配、暂停/继续/转向/退休决策。它不得为了“完成论文”而合理化负结果。

### 2.2 Execution Plane · Sub-Agent Sessions

Sub-Agent 负责文献检索、实现、实验、统计、作图、写作、复现与审计。Sub-Agent 不得直接修改全局研究目标，也不得把探索性结果升级为核心 Claim。

### 2.3 Observation Plane · User Session

User Session 是只读观察与干预入口，不是第二个 Manager。用户改变范围、Claim、预算、venue 或冻结协议的指令，必须转发给当前 Manager，并持久化到 **decision-log.md**。紧急情况下用户可暂停 Manager；暂停后不得继续派发新任务。

### 2.4 权限矩阵

- **默认允许：**读代码、写独立 worktree、L0–L2 检查、创建计划与草稿。

- **Manager 可批准：**Pilot、探索性实验、注册新假设、废弃无效实验、合并 slice 到 topic。

- **必须用户批准：**超预算 Full Run、修改核心 Claim/venue、使用付费或私有数据、删除/覆盖数据、对外提交或发布、涉及人类参与者或许可不确定的操作、修改冻结协议、把探索性发现升级为核心 Claim。

## 3. Manager 生命周期、轮替与交接考试

Manager 不仅按 Token 数轮替，还要按**上下文健康度**轮替。硬触发包括：达到最大 Token/墙钟时间/重大决策数、接近上下文限制、无法准确复述 Claim–Evidence–Risk 状态。软触发包括：阶段完成、重大 Pivot、重复询问已记录信息、决策与日志冲突、实验状态遗漏或用户要求。

**禁止在以下时点轮替：**全量实验或数据迁移中途、未落盘的关键诊断、multi-agent merge 未完成、存在未解释异常。

退休前必须生成固定 Handoff Bundle：project-charter.md、current-state.md、claim-ledger.md、hypothesis-ledger.md、evidence-ledger.md、experiment-registry.yaml、decision-log.md、failure-log.md、open-risks.md、compute-ledger.md、literature-ledger.bib、paper-outline.md 与 handoffs/manager-X-to-Y.md。

新 Manager 必须先通过接管考试：准确陈述当前研究问题、核心 Claim、每个 Claim 的证据状态、最强 baseline、主要失败模式、前三项风险、下一步动作与不可自行决定事项。Handoff Auditor 判定通过后，才可更新 ACTIVE_MANAGER；旧 Manager 随即只读，禁止双 Manager 并行调度。

## 4. Hypothesis–Claim–Evidence Ledger

Manager 管理的核心不是任务列表，而是 **Hypothesis → Experiment → Evidence → Claim → Paper** 的证据链。

### 4.1 Hypothesis 分类

- **Confirmatory：**验证预先声明的核心 Claim；协议冻结后不得看结果改成功标准。

- **Exploratory：**发现规律或新方向；可动态调整，但必须显式标记，不能直接作为确认性证据。

- **Diagnostic：**排查实现、优化或数据问题；默认不支撑论文核心结论。

每次运行前记录 hypothesis_id、experiment_type、decision_before_run、expected_outcome、success_criterion、failure_interpretation、positive/negative next action 与 protocol_frozen。

### 4.2 Claim Ledger

每个核心主张必须有 claim_id、精确 statement、scope（数据集/模型/指标/条件）、claim_type、状态（proposed / partially-supported / supported / contradicted / withdrawn）、所需证据、支持与反对实验、已知限制及论文位置。

**双向 Gate：**进入 Abstract、Introduction Contributions 或 Conclusion 的每个 Claim 都必须映射到 Ledger 且证据充分；每张主表和主图也必须标明支持哪些 Claim。Contradicting evidence 不得删除，只能解释、降级适用范围或撤回 Claim。

## 5. Novelty Gate 与引用完整性

Literature Review 的目标不是证明“看起来新”，而是主动寻找最强反例。独立 Novelty/Falsification Agent 必须尝试证明：该想法已存在、只是显然组合、属于轻量工程变化、在不同记号下数学等价，或已在另一任务名/benchmark 下评估。

Novelty Gate 至少输出：最近邻工作矩阵、objective/训练信号/数学形式/机制对比、时间线与 concurrent work、Reviewer 第一反应、可站得住的一句话 novelty、风险等级与仍未验证的差异。

**Citation Verification Gate：**引用必须真实可检索；标题、作者、年份一致；关键判断必须基于正文而非只看摘要；“prior work does not…”必须有可核验证据；禁止虚构论文、二手摘要替代原文或把关键词差异当机制差异。当前 ICLR 对 LLM 使用的政策强调作者对输出负责，虚假主张、误述、伪造数据与幻觉引用均不可接受。

推荐的审计指令：*Your goal is to falsify the claimed novelty, not to support it. Construct the strongest novelty objection a skeptical top-conference reviewer would make, and tie every factual statement to a verifiable source.*

## 6. 分级实验授权：L0–L4

- **L0 静态检查：**配置、路径、split 泄漏、metric、baseline 公平性、seed、checkpoint、eval mode、输出主键与版本记录。

- **L1 极小样本测试：**跑通 shape/loss/gradient；手算 metric；尝试 overfit 一个小 batch。

- **L2 Smoke Run：**1% 数据、1 seed、少量 step、最小模型；只验证 pipeline，不判断科学结论。

- **L3 Pilot：**1–2 个代表性任务和 seed，验证效应方向、量级、方差、时长与成本。

- **L4 Full Confirmatory Run：**仅在协议冻结、baseline 公平性、metric 单测、泄漏检查、预算、唯一实验 ID、恢复机制、代码与数据版本全部通过后执行。

Full-run Authorization 必须记录 authorization_id、experiment_group、预计 GPU 小时/成本、pilot evidence、protocol commit、data version、baseline fairness / metric validation / leakage / recovery verdict、批准者与预算状态。任何“效果不好就调整”必须先判断它是科学调整、诊断修复，还是看结果追目标；后者禁止。

## 7. 统计完整性与公平比较 Gate

- 预先规定主指标、次指标与排除规则；test set 不得用于迭代调参。

- 使用足够随机 seed，报告中心趋势、方差或置信区间，并解释样本量。

- 同时考虑 effect size 与 statistical uncertainty，不能只追逐显著性。

- 多个数据集/指标/假设时，评估 multiple comparisons 风险。

- Proposed method 与 baseline 使用公平的超参数搜索预算、训练资源和停止标准。

- 失败运行不得无记录删除；outlier 排除必须使用预先声明规则。

- 区分 best checkpoint、last checkpoint 与多次运行平均表现。

- 报告硬件、训练时间、计算量、软件环境及 sensitivity/robustness 分析。

- 消融必须对应机制解释，不得用“删掉后变差”自动证明因果机制。

NeurIPS Paper Checklist 将主张与证据范围的一致性、限制、训练细节、误差条、计算资源、资产许可和伦理披露纳入提交检查；因此本 Gate 应在项目早期启用，而不是投稿前补表。

## 8. Experiment Registry、Failure Log 与 Artifact Lineage

### 8.1 不可变实验注册

每次运行必须有唯一 experiment_id，并记录 parent experiment、hypothesis_id、claim_ids、type、status、code commit、dirty tree、data/environment/config hash、模型、数据集、seed、硬件、起止时间、exit code、原始/汇总指标、artifact、failure reason、valid_for_paper 与 validation notes。失败、取消和 invalidated 实验同样登记，禁止 outputs/final2/really_final 式文件夹科研。

### 8.2 Failure Log

记录失败路线、归因、尚未解释的异常、不可重复路线与随机性风险，防止 Manager 轮替后重复试错和 survivor bias。

### 8.3 Artifact Lineage

每张表和图必须有 manifest：artifact_id、paper_location、supports_claims、source_experiments、aggregation script 与 commit、raw data hash、output file、manual_edits_allowed=false、last_verified 与 verdict。禁止手抄数字进 LaTeX、从聊天复制 metric、手改图表数字或让脚本读取“最新目录”。

ACM Artifact Review and Badging 将代码、运行脚本、输入数据、原始结果与分析脚本都视为研究 Artifact，并区分 Artifacts Available、Artifacts Evaluated 与 Results Validated；本工作流以“至少可独立重建一张主表/主图”为内部最低复现目标。

## 9. 五类独立审计与 Reviewer Scorecard

1.  **Implementation Auditor：**实现、metric、baseline、泄漏、checkpoint、数值与并发。

2.  **Scientific Skeptic：**Claim 是否被证据支持、替代解释、相关性/因果性、机制是否 overclaim。

3.  **Novelty Reviewer：**最近邻工作、显然组合、数学等价与顶会增量。

4.  **Statistics Auditor：**seed、方差、显著性、multiple comparisons、超参预算与选择性汇报。

5.  **Reproducibility Reviewer：**在新环境仅按 README 安装，运行最小复现并重建至少一张主表或主图。

Reviewer Scorecard 必须覆盖 Significance、Novelty、Technical Soundness、Empirical Strength、Clarity、Reproducibility、Ethics & Limitations 和 Confidence。每项不仅给分，还要写：证据、主要扣分点、提高一级所需的最小工作、成本是否值得。

ICLR 2026 Reviewer Guide 强调及时、实质、充分的评审，并由 Reviewer、AC 与 SAC 共同形成判断；因此内部模拟评审必须角色分离，不能由论文写作 Agent 自己宣布“Strong Accept”。

## 10. Reviewer Critic Session：独立评审闭环

Reviewer Critic Session 属于独立的 **Evaluation Plane**。它模拟目标顶会 Reviewer，以暴露拒稿风险为目标；不属于 Execution Plane，不是第二个 Manager，也没有调度、改稿、改代码、启动实验、修改 Claim 或扩预算的权限。

**核心铁律：**Reviewer Critic 的职责是提出可核验的反对意见，不是要求 Manager 满足所有 Reviewer 偏好；Manager 的职责是降低真实录用风险，不是迎合单个模拟 Reviewer。

### 10.1 独立性与权限边界

- 每轮使用全新 Session，不继承写作 Agent 或 Manager 的聊天上下文。

- 只读取冻结的 Review Input Bundle；不得读取 Manager 的预期结论、辩解、内部评分或希望获得的 verdict。

- 只报问题，不直接修改论文、代码、Ledger 或实验配置。

- 所有批评必须指向可定位内容、缺失证据或明确 Reviewer 风险；禁止泛泛要求“补更多实验”。

- Reviewer 不得把个人偏好包装成顶会硬标准；不确定时必须降低 confidence。

- 若发现伦理、许可、隐私、数据污染、伪造引用或不可复现风险，立即标为 BLOCKER 并升级给用户。

### 10.2 触发节点与评审模式

Reviewer Critic 不持续在线监控，而在固定里程碑触发，避免研究方向被随机意见牵引。

1.  **Charter Review：**Research Charter 与 Novelty Gate 完成后；检查问题重要性、贡献类型、最近邻工作和可证伪性。

2.  **Pre-Full-Run Review：**L3 Pilot 完成、L4 授权前；检查实验是否足以区分核心解释，阻止昂贵但低信息增益的设计。

3.  **Claim Freeze Review：**主实验完成后；检查 Claim–Evidence 匹配、统计强度、替代解释和适用范围。

4.  **Full-Paper Review：**第一版完整论文形成后；按真实顶会格式进行端到端评审。

5.  **Submission Readiness Review：**Submission Freeze 前；仅检查残留 BLOCKER、政策、匿名、artifact 与可复现性，不再随意扩张研究范围。

默认每个节点运行 3 个相互独立的 Critic：**R1 Novelty & Significance**、**R2 Technical Soundness & Experiments**、**R3 Skeptical Generalist & Clarity**。资源紧张时可只运行一个 Generalist，但必须降低最终评审置信度。三份评审完成后，可由只读 **Meta-Reviewer Session** 去重、识别冲突并形成优先级；Meta-Reviewer 同样无权命令 Manager。

ICLR 2026 Reviewer Guide 要求评审具备及时性、实质性和充分性，并在作者讨论后向 AC 提供建议；因此本工作流也将初评、Manager response 与 re-review 分开，而不是一次性打分。

### 10.3 Review Input Bundle

Manager 在启动 Critic 前生成只读快照，并写明 snapshot_id 与版本。Reviewer 只能依据该快照判断；缺失内容必须报告为 missing evidence，不得自行猜测。

- target venue、track、review rubric 与当前阶段；

- 匿名版 title、abstract、paper PDF/正文与 appendix；

- Research Charter、Non-Claims、Claim Ledger 与 Claim Map；

- 最近邻工作矩阵及已核验 citation map；

- 实验协议、baseline fairness review、统计分析摘要；

- 主表/主图及对应 artifact manifests；

- 已知限制、failure log 摘要与 open risks；

- 当前预算余额和可执行动作边界，但不提供 Manager 偏好；

- 本轮 review_scope：允许评价哪些内容、哪些尚未形成而不应扣分。

输入包必须区分 **not provided、not yet available、not applicable**。Reviewer 不能因早期阶段尚无完整论文而按 Submission 阶段扣分。

### 10.4 Reviewer Critic 执行流程

1.  **Scope Check：**确认 venue、阶段、评审范围、可用材料和自身专业匹配度；存在 conflict 或 expertise mismatch 时退出并请求替代 Reviewer。

2.  **Independent Read：**先独立概括研究问题、贡献与证据，不读取任何 Manager response；若概括与作者意图不同，标记 clarity risk。

3.  **Claim Attack：**逐一攻击核心 Claim：是否新、是否重要、是否被实验支持、是否存在替代解释、是否越过证据范围。

4.  **Evidence Audit：**核对主表/主图、统计、baseline、公平性、消融、robustness、负结果、数据与 artifact lineage。

5.  **Reviewer Simulation：**分别给出 strongest rejection case 与 strongest acceptance case，防止只寻找单向证据。

6.  **Rank Findings：**按 BLOCKER / MAJOR / MINOR / QUESTION 排序，并合并同一根因下的重复意见。

7.  **Cheap Test：**对每个 BLOCKER/MAJOR 指出能区分关键解释的最便宜动作；不得默认要求 full-scale experiment。

8.  **Initial Verdict：**给出评分区间、confidence、主要不确定性与“最可能导致拒稿的前三项原因”。

Reviewer 必须把“论文真的有问题”和“论文表达导致误解”分开。若现有证据已足够但文本未呈现，应请求 clarification/rewrite，而不是直接要求新实验。

### 10.5 Reviewer 输出格式

每轮评审写入 **reviews/\<snapshot_id\>/review-\<reviewer_id\>.yaml**，并附一份人类可读摘要。结构如下：

**Review Header**

- review_id、snapshot_id、reviewer_role、target_venue、review_stage、review_scope；

- materials_examined、missing_materials、expertise_level、conflict_check；

- overall_score_range、confidence、verdict。

**Paper Understanding**

- one_sentence_problem；

- claimed_contributions；

- strongest_accept_case；

- strongest_reject_case；

- clarity_mismatches。

**每条 Finding** 必须包含：

- finding_id；severity：blocker \| major \| minor \| question；

- dimension：significance \| novelty \| soundness \| empirical \| statistics \| clarity \| reproducibility \| ethics；

- target_claim_ids 与 paper_locations；

- criticism 与 evidence_examined；

- why_it_matters_for_acceptance；

- alternative_explanation；

- requested_evidence_or_change；

- cheapest_discriminating_action；

- acceptance_condition；

- confidence；

- possible_reviewer_misunderstanding；

- requires_new_experiment、estimated_cost_class 与 user_approval_required。

**Review Summary** 必须列出 top_3_rejection_risks、must_fix_before_next_gate、optional_improvements、questions_for_manager、score_if_unchanged 与 score_if_blockers_closed。禁止只给总分而不提供关闭条件。

### 10.6 Manager 反馈与分诊机制

Manager 收到 Review 后不得直接派发修改任务。首先创建 **reviews/\<snapshot_id\>/manager-response.yaml**，对每条 Finding 逐项给出 disposition：

- **ACCEPT：**问题成立，进入修复或补证据计划。

- **PARTIALLY_ACCEPT：**部分成立；拆分成立与不成立部分，限定处理范围。

- **REBUT_WITH_EVIDENCE：**现有证据已回答；给出 Claim、Experiment、Artifact 或正文位置，不以口头辩解关闭。

- **CLARIFY_ONLY：**属于表达或定位问题，不新增实验。

- **DEFER：**问题有价值但不影响当前 Gate，记录延期理由、风险与重访条件。

- **REJECT：**基于错误前提、超出 Non-Claims 或与 venue rubric 无关；必须给证据，不能因“不想改”而拒绝。

- **ESCALATE_TO_USER：**涉及核心 Claim、venue、冻结协议、伦理/许可、私有数据或预算阈值。

每条响应必须记录 rationale、evidence_refs、planned_action、owner、budget_cost、deadline、expected_claim_state_change、requires_reaudit 与 closure_evidence。Manager 还要识别多个 Finding 是否源于同一根因，优先解决能同时关闭多项风险的动作。

Meta-Reviewer 负责合并重复意见、标记 Reviewer 分歧、判断共同 BLOCKER 与校准 confidence；但最终 disposition 仍由 Manager 提出，越权事项由用户裁决。

### 10.7 修改、回审与关闭协议

1.  Manager 将被接受的 Finding 转换为 task，但必须保留 finding_id、claim_id 与 snapshot_id 的追踪关系。

2.  Execution Agent 完成修改或实验后提交 closure evidence；不得自行把 Finding 标为 resolved。

3.  Manager 验证 artifact、预算、Claim Ledger 与论文同步更新，生成新的 snapshot。

4.  原 Reviewer 优先执行 targeted re-review，只检查对应 Finding、连带 Claim 与新引入风险；不得无理由扩大范围。

5.  Reviewer 给出 CLOSED / PARTIALLY_CLOSED / OPEN / SUPERSEDED / INVALIDATED verdict，并说明依据。

6.  BLOCKER 只有在 Reviewer 复核，或 Meta-Reviewer/用户以证据推翻后才能关闭。

**回审上限：**同一 Finding 默认最多两轮。两轮后仍未关闭时，Manager 必须选择：升级用户、收缩 Claim、接受残余风险、转向或停止；禁止 Reviewer–Manager 无限争论。

**Gate 规则：**进入 L4 前不得存在与协议有效性相关的 OPEN BLOCKER；Claim Freeze 前不得存在与核心 Claim 证据相关的 OPEN BLOCKER；Submission Freeze 前不得存在任何 OPEN BLOCKER。MAJOR 可在记录风险并经 Manager/用户批准后延期，MINOR 不得自动触发高成本实验。

### 10.8 防止 Reviewer 驱动失控

- 新增实验前必须说明它将改变哪个 Claim 状态、关闭哪个 Finding，以及正负结果分别如何决策。

- 同一 Reviewer 的偏好不得覆盖 Charter、Non-Claims、预算和 venue rubric。

- Reviewer 分歧不能靠“做完所有建议”解决；应由 Meta-Reviewer 区分真实不确定性、专业视角差异与表达误解。

- 若建议只提高叙事完整性而不改变科学判断，优先改写，不启动实验。

- 若建议成本高且预计信息增益低，Manager 应 DEFER 或 REJECT，并保留风险。

- Critic 不得在每次小改后重跑；只有 closure evidence 就绪、核心 Claim 改变或进入下一个 Gate 才触发。

- 任何评分提升都只能作为结果观察，不能成为追结果式扩实验的理由。

NeurIPS 对大规模评审流程的复盘指出，评审本身存在专业匹配与决策噪声问题；因此本系统保留多 Reviewer、Meta-Reviewer、confidence 与 disagreement，而不把单个 Critic 当作绝对裁判。

## 11. 预算、信息增益与停止机制

Manager 必须维护 max_gpu_hours、max_api_cost、max_agent_tokens、max_calendar_days、max_full_runs 与 max_pivot_count。每次扩预算前回答：要降低哪个关键不确定性？结果会改变什么决策？正负结果分别如何处理？是否存在更便宜的实验？该运行是否只是“再试一次”？

**Stop / Pause Rules：**核心 novelty 被覆盖；多个代表性 Pilot 均无效；提升小于自然方差；优势依赖不公平 baseline；必须不断缩小评估范围才能维持 Claim；剩余预算不足以完成最低证据；连续两轮 Reviewer Simulation 出现同一 Blocker；新实验不再改变 Claim 状态。

Stop 不等于失败。Manager 应输出四选一建议：**continue、pivot、downgrade venue/scope、terminate/negative result**，并说明证据、机会成本与可逆性。

## 12. Paper Writing 防幻觉合同与 Freeze 节点

写作 Agent 不得发明引用、实验或数字；不得把 exploratory 写成 confirmatory、把相关性写成因果、把单数据集结果写成普遍规律、隐藏不利结果、未经验证声称 SOTA 或自行改图表数字。每句定量 Claim 必须指向 Artifact；每个 Novelty Claim 必须指向已验证引用；无法验证时标记 **\[NEEDS EVIDENCE\]**。

必须维护 paper/claim-map.yaml、paper/citation-map.yaml、paper/table-manifests/ 与 paper/figure-manifests/。

- **Code Freeze：**核心实验代码冻结，修复需评估是否使既有结果失效。

- **Protocol Freeze：**confirmatory 的数据、split、metric、baseline、seed、搜索预算和排除规则冻结。

- **Result Freeze：**主结果确定后不得无记录替换。

- **Claim Freeze：**最终写作阶段修改核心 Claim 必须重跑 Claim–Evidence Audit。

- **Submission Freeze：**禁止新功能、大重构、关键依赖更换、未经审计的新实验与手工修数字。

投稿前还应执行 Venue Policy Gate：核对最新作者指南、匿名/双投/LLM 披露、伦理、补充材料和 artifact 要求；人类作者对所有 AI 产出承担最终责任。

## 13. Scientific Workflow 一页总览

**Idea → Charter → Novelty Falsification → Hypothesis/Claim Registration → Charter Review → L0–L3 → Pre-Full-Run Review → Protocol Freeze → L4 Confirmatory Runs → Statistical Audit → Claim Revision → Claim Freeze Review → Artifact Lineage → Paper Draft → Full-Paper Review → Manager Response → Revision/Experiment → Targeted Re-review → Submission Readiness Review → Submission Readiness Gate**

不可跳过的关键 Gate：

- Novelty 未通过，不得进入高成本 Full Run。

- 协议未冻结，不得把结果标为 confirmatory。

- Claim 无双向 Evidence 映射，不得进入摘要、贡献或结论。

- 主表/主图无法从固定实验 ID 重建，不得进入 Result Freeze。

- 存在未关闭的 BLOCKER，不得进入 Submission Freeze。

- 任何需要伦理、许可、私有数据、超预算或对外发布的动作，必须由用户批准。

**最终铁律：**任何无法进入“Hypothesis → Experiment → Evidence → Claim → Paper”证据链的工作，都不应消耗全量实验预算。


---

# Part II · 工程实现与交付工作流（Engineering & Implementation Workflow）

> 本层负责 **如何可靠地产出实现与 Artifact**：Spec-Driven Development + Agent Execution + 独立审计 Gate。其上游研究方向、实验授权、证据有效性与投稿主张必须服从 Part I。

---


## 0. 一次性适配（换项目时改这里）

把下表占位符替换成你项目的实际值，全文其它地方引用同名占位符即可。

| 占位符 | 含义 | 示例 |
|---|---|---|
| `<REPO>` | 仓库名 | `MyProject` |
| `<REPO_PATH>` | 主 checkout 的绝对路径 | `~/MyProject` / `C:\code\MyProject` |
| `<OWNER>` | GitHub owner / org | `your-org` |
| `<DEFAULT_BRANCH>` | 主干分支 | `main` |
| `<WORKTREE_ROOT>` | worktree 存放目录 | `<REPO_PATH>/.worktrees` |
| `<AGENT_CLI>` | 你用的 agent CLI 命令 | `copilot` / `claude` / 自定义 |
| `<MODEL>` | 复杂任务默认模型 | 你可用的最强长上下文模型 |
| `<TMUX_SESSION>` | 长驻 agent 的 tmux session 名 | `proj-t` |
| `<COMPUTE>` | 执行 GPU/重任务的机器描述 | `4× GPU 服务器` / `本地` / `CI runner` |
| `<PROJECT_BOARD>` | 项目看板标识（可选） | GitHub Project number / 无 |
| `<SPEC_DIR>` | spec 存放目录 | `docs/specs/` |
| `<PLAN_DIR>` | plan 存放目录 | `docs/plans/` |
| `<RESEARCH_DIR>` | 调研报告目录 | `docs/research/` |
| `<REPORT_STORE>` | 重型交付物（图/大文件）存放处（git 外） | `~/reports/<REPO>/` |
| `<COMMIT_TRAILER>` | 每个 commit 的署名 trailer | `Co-authored-by: <agent> <email>` |
| `<BUILD_CMD>` | 构建/产物验证命令 | `make build` / `npm run build` / `nix build` |
| `<RUN_CMD>` | 跑真实产物的命令 | `./bin/app --help` |
| `<TEST_CMD>` | 全量测试命令 | `pytest` / `npm test` / `go test ./...` |

> 如果你的项目没有服务器 / tmux / GPU，把「长驻 agent」相关内容当作「本地终端里跑 agent」即可，方法论不变。

---

## 1. 一句话定位与五条铁律

**Spec-Driven Development + Agent Execution + 独立审计 Gate。**

质量不是靠「用了多少 agent」堆出来的，而是靠**验证机制**守出来的。五条铁律（每条都是踩坑换来的）：

| # | 铁律 | 教训 |
|---|---|---|
| 1 | **验证真实产物，不只看测试绿** | 关键配置被误删、整条命令失效，却通过了几十个测试——只有 build + 运行真产物才抓得到 |
| 2 | **独立敌对审计 > 自审** | 自审容易判「都是 pre-existing / PASS」，独立新 agent 常挖出真 bug |
| 3 | **并行只对「独立切片」，依赖链必须串行** | 硬并行依赖链 = 冲突 + 跨切片一致性 bug 更隐蔽 |
| 4 | **共享基础设施改动标注交 owner，永不自 merge** | env/build/infra 是 owner 地盘；agent 只测明白、标注醒目，merge 是人的判断 |
| 5 | **知道何时停手** | 一道彻底审计 0 新问题后继续审 = 边际收益趋零的焦虑循环；验到合理程度就交 |

外加一条贯穿铁律：**「标注边界 ≠ 修 bug」**——低风险且真超范围的可文档化为「已知边界」；但**会静默丢数据 / 破坏正确性**的（如身份维度缺失、窗口截断丢帧）**必须修**。

---

## 2. 三层文档体系（全部 git 追踪）

| 层 | 位置 | 作用 | 谁拥有 |
|---|---|---|---|
| **执行规范** | `AGENTS.md`（或本文件） | 定义 HOW：worktree 隔离 / PR 流程 / 分支命名 / commit 规范 / auto-merge 策略 / 看板更新 | 人（项目主人） |
| **设计规格** | `<SPEC_DIR>` | 每个 issue 一个 spec：Objective → Non-goals → Surface → Design → Acceptance Criteria → Slice Plan | 人 或 Agent（讨论后写） |
| **执行脚本** | `<PLAN_DIR>` | 每个 slice 一个 plan：架构图 + 数据流 + 分步骤 checklist + 测试步骤 + push 点 | Agent（执行中生成） |
| **调研报告**（可选） | `<RESEARCH_DIR>` | SOTA 调研 / 选型 / license 审查 | Research Agent |

**Spec 与 Plan 都可以由 Agent 写**，但必须**经你确认后 commit**。区别：
- **单 issue 交互模式**：讨论后 Agent 写 spec（人机协作，spec 质量取决于讨论深度）。
- **多 issue 非交互模式**：Agent 自主写 spec，所以 **issue body 质量决定 spec 质量**。

---

## 3. 全生命周期总览

```
① 调研(可选) → ② Issue 准备 → ③ 拆分+依赖分析 → ④ 每 slice 执行
                                                        ↓
        ⑦ 交付给你(不 merge) ← ⑥ 整体 PR-Audit ← ⑤ 独立敌对审计(每 slice)
                    ↓
        你决定 → mark ready → 交 owner review + merge
```

**不可跳过的 gate：**
- 每个 slice 完 → ④自检 + ⑤独立敌对审计
- 全部 slice 完 → ⑥整体 PR-Audit（build 真产物 + 全量测试 + diff 卫生）
- 交付前 → ⑦先发你，不 ready、不 merge

---

## 4. 角色总表

| 角色 | 何时用 | 位置 | 关键约束 |
|---|---|---|---|
| **你（人）** | 全程 | 本地 / 浏览器 | 唯一强制触发点；判断题的最终裁决者；merge 决定 |
| **Research Agent**（可选） | 技术路线/选型不明 | 独立 session，doc-only | 输出 research md，直接 commit `<DEFAULT_BRANCH>`；不写代码 |
| **Manager Agent** | 多 slice / 多 issue | 长驻 session（`<COMPUTE>`） | **先画依赖图**；只有它碰 git/topic；永不碰主 checkout、永不 merge 进主干 |
| **Sub-Agent（执行）** | 每个 slice | 独立 worktree + session | 只在自己 worktree；spec→plan→执行；自检 gate |
| **Audit Agent（独立敌对）** | 每 slice 完 + 整体 | **全新 session、无上下文** | 目标是挑毛病；不信任何既有结论；只报不修 |

**两种规模：**
- **单 issue（日常默认）**：不需要 Manager。你在 worktree 里起一个交互 session，讨论 → spec → plan → 执行 → review。
- **多 issue 并行（高级）**：才需要 Manager Agent 编排多个 Sub-Agent。

---

## 阶段 0 · 调研（可选，技术路线不明时）

**何时需要**：选模型 / 定算法路线 / 审 license / 比 SOTA。

**启动模板：**
```bash
<AGENT_CLI> --name research-<topic> --model <MODEL> \
  -i 'Research SOTA for <topic> (issue #<N>). Compare: <候选 A/B/C>.
For each: accuracy/benchmark, LICENSE (permissive vs restrictive), input/output
format, runtime cost, integration fit with our <现有框架>.
Read AGENTS.md §<相关章节> first.
Output <RESEARCH_DIR>/<date>-<topic>.md with a comparison TABLE + a clear
recommendation + rationale + honest caveats.
Commit directly to <DEFAULT_BRANCH> (doc-only). Trailer: <COMMIT_TRAILER>'
```

**关键**：让它输出**对比表 + 推荐 + 诚实 caveat**（尤其 license：可商用 vs 仅研究用途）。

**能做 / 不能做**：能搜文献/仓库/官方文档、比公开 benchmark、审 license、读本仓库理解集成约束；**不能**跑重型 benchmark（那要执行 agent）、不能保证结论绝对准（你最终判断）。

---

## 阶段 1 · Issue 准备

| 情况 | 做法 |
|---|---|
| 已有合适 open issue | 确认 body 够详细 |
| body 太简单 | 先补 body（acceptance criteria + 相关文件/模块 + Non-goals + parent epic 链接） |
| 全新工作 | 创建 issue，写清 body |

**「body 够详细」=**：① 说清做什么（acceptance criteria）② 提到相关文件/模块/现有模式 ③ parent epic 链接 ④ Non-goals（告诉 agent 什么不要动）。

> 单 issue 交互模式下 body 可以不完整（讨论时补）；**Manager 非交互模式下 body 必须完整**（没有讨论机会）。

**（可选）登记看板 `<PROJECT_BOARD>`**：设 Status=In progress，填 Agent 字段（谁在干、worktree 路径、session 引用），方便你随时知道谁在做什么。

---

## 阶段 2 · 拆分 + 依赖分析（最容易出错的一步）

**先画依赖图，再决定并行还是串行。**

```
对每个候选 slice 问：它读/写哪些文件、哪些模块、哪些数据结构？
  ├─ 两个 slice 改同一批文件 / 后者依赖前者产物  → 串行（依赖链）
  └─ 完全独立（不同文件、无产物依赖）           → 并行（独立切片）
```

- **依赖链**（如：建结构 → 扩展 → 改上游接口）：**串行**。硬并行会冲突，且跨切片的一致性 bug 更隐蔽。
- **独立切片**（如多个互不相关的 bug fix）：**并行**，各自独立 worktree；重型任务受资源上限约束（如一张 GPU 一个 agent）。

**产物**：Manager 写 spec + per-slice plan，标明每个 slice 的**依赖关系 + 并行/串行编排**，commit 到 topic 分支。

---

## 阶段 3 · 每个 Slice 执行

### 3.1 脚手架
```bash
git -C <REPO_PATH> worktree add <WORKTREE_ROOT>/<name> -b feature/<N>-<name> <DEFAULT_BRANCH>
cd <WORKTREE_ROOT>/<name>
git commit --allow-empty -m "bootstrap #<N>

<COMMIT_TRAILER>"                    # 空分支开不了 PR，先引导提交
git push -u origin feature/<N>-<name>
# 开 draft PR（用你的 PR 工具），base=<DEFAULT_BRANCH>，body 写 "WIP. Refs #<N>."
```
> **早开 draft PR** 拿 CI + owner 可见性；**但不 mark ready、不 merge**。

### 3.2 执行流程（spec → plan → code）
1. 贴**开场 prompt**（§使用方法 A）→ agent 读代码 + 问 ≤5 个澄清问题
2. 你答问 → agent 写 **spec** → 你确认
3. agent 写 **plan** → 你确认
4. agent 执行：写代码 → 跑测试 → 自检 → push（累积在 draft PR）

**你在关口把关**：spec 看 Acceptance Criteria + Non-goals + 拆分；plan 看是否覆盖验收 + 有测试步骤 + 有 push 点。**判断题（选哪个方案、要不要扩范围）由你拍板，不让 agent 闷头猜。**

### 3.3 自检 gate（agent mark ready 之前必须自答）
- 目标产物真的能跑（不只是 import / 单测）？
- 幂等？重跑收敛？
- **身份维度完整**（主键/标识没漏维度 → 避免不同配置静默撞车）？
- 无依赖 / 空输入优雅降级？
- diff 只动该动的，无残留 debug / 无误删？

---

## 阶段 4 · 独立敌对审计（质量皇冠，每 slice 完做）

**必须是全新 session、无上下文、抱着「我一定要挑出毛病」的心态**——写代码的 agent 审自己有偏见。

审计 prompt（§使用方法 D）核心：
- 「你没写这份代码，把 PR 描述和一切既有结论当**不可信**，从源码重新验证」
- **先读代码找逻辑 bug**（身份维度缺失 / 静默丢行 / 坐标/数值缩放 / 注入 / 多步写原子性 / 旁路校验），再跑验证
- **验证真实产物**（build + run，不只单测）
- **独立归因测试失败**（clean `<DEFAULT_BRANCH>` 对比复现，禁止「猜 pre-existing」）
- 输出 **ranked findings**（BLOCKER/MAJOR/MINOR/UNVERIFIED）+ 明确 verdict；**只报不修**

**审计回来后分诊：**
- 我们代码 + 修法清楚 → 修
- 共享 infra / owner 说过别动 → **不擅改，文档 + follow-up issue，交 owner**
- 会静默丢数据 / 破坏正确性 → **必须修**（哪怕它自称「边界」）

---

## 阶段 5 · 整体 PR-Audit（全部 slice 完，合并前一次总检）

| 面 | 查什么 |
|---|---|
| **A 真实产物** | `<BUILD_CMD>` + `<RUN_CMD>` 跑通；其它产物消费者没被连累 |
| **B 幂等/共存** | 重跑 0 新副作用；多配置共存不撞；超限报错不静默丢；`--force`/重置干净 |
| **C 结构/接口** | 统一视图/接口单值不 fan-out；约束真强制；下游消费者不被破坏 |
| **D 正确性** | 数值/坐标 round-trip；无依赖优雅 skip；空输入不崩 |
| **E 全量回归** | 跑**整个**测试套（不只子集）；每个失败 clean-main 独立归因 |
| **F diff 卫生** | 逐行看配置/依赖文件，防「误删」；无 throwaway/debug 残留；worktree 干净 |
| **G review 闭环** | 所有 review thread 回复 + 真修（不只回复）；lint |

**产出**：PASS/FAIL 表 + ranked findings。确认的 bug 修，判断题标注交你/owner。

---

## 阶段 6 · 交付（先发你，不 merge）

- **先发你**：报告 / `git diff <DEFAULT_BRANCH>...feature/<N>` / PASS-FAIL 表。**不 mark ready、不 merge。**
- 你审完 → 才 mark PR ready → 交 owner review + merge。
- 共享 infra 改动在 PR body/commit 里**单独标注 "needs your sign-off"**。
- **（可选）图文报告**：结果 + 可视化 + 指标 + **诚实的精度验证**。
  - 别 overclaim：无 ground truth 时说清「是合理性/一致性/稳定性验证，不是误差 vs 真值」；要真误差就用**带 GT 的标定数据集**，并写明域差距。
  - 重型产物（图/大文件）放 `<REPORT_STORE>`（git 外），只把摘要发 PR。

---

## 7. 贯穿原则 · Gate · 陷阱速查

| 类别 | 要点 |
|---|---|
| **只读主 checkout** | agent 永不改 `<REPO_PATH>` 主 checkout；只 `git worktree add` / 只读 inspect（`git log/status/diff`） |
| **禁止在主 checkout 上 test-checkout** | 临时 checkout 某 commit 也不行（会留 detached HEAD）；要看某 commit 用临时 worktree |
| **PR-first 但不 merge** | 早开 draft 拿 CI/可见性；ready/merge 是人的动作 |
| **commit trailer** | 每个 commit 带 `<COMMIT_TRAILER>` |
| **空分支陷阱** | 0-commit 开不了 PR → 先 `git commit --allow-empty` 引导提交 |
| **删 worktree 陷阱** | 先 `cd <REPO_PATH>` 再 `git worktree remove`，否则后续 shell 找不到 cwd 报 ENOENT |
| **身份维度陷阱** | 主键/identity 要包含「所有影响输出的维度」（strategy/size/config），否则静默撞车 |
| **验证真实产物** | 测试绿 ≠ 产物能用；build + 跑真产物 |
| **别猜 pre-existing** | 任何「预先存在的失败」结论必须 clean-main 复现坐实 |
| **何时停** | 一道彻底审计 0 新问题 → 交付；别无限自证 |
| **squash 进 topic 的隐患** | slice squash-merge 进 topic 会压平历史，topic→main 可能报 dirty；优先 `--merge` 或 squash 后立即 `git merge --no-ff origin/<DEFAULT_BRANCH>` 补桥 |

---

## 8. 分支命名约定

| 类型 | 格式 | 示例 |
|---|---|---|
| 新功能 | `feature/<short-name>` | `feature/123-add-cache` |
| Bug fix | `fix/<short-name>` | `fix/456-null-deref` |
| 重构 | `refactor/<short-name>` | `refactor/config-loader` |
| 实验 | `experiment/<short-name>` | `experiment/new-algo` |
| 多 slice 伞状 | `topic/<name>` | `topic/123-search-rework` |
| sub-agent slice | `slice/<topic>-S<N>` | `slice/123-S1-index` |

**Topic 模式**（多 sub-agent 并行）：
```
topic/xxx（伞状，Manager 维护）
  ├── slice/xxx-S1（Sub-Agent 1，auto-merge 进 topic）
  ├── slice/xxx-S2（Sub-Agent 2，auto-merge 进 topic）
  └── topic → <DEFAULT_BRANCH>（人工 approve 一次）
```

**auto-merge 策略**：slice → topic 可由 Manager 验证后 auto-merge；topic → 主干**永远需要人 approve**，即使 CI 全绿。

---

## 9. Agent 运维（监控 + 故障处理）

**监控**：
- 长驻 session 直接看（`tmux attach-session -t <TMUX_SESSION>`）
- 若 CLI 支持远程可见性，用浏览器监控 session（SSH 断开不影响）
- 看 PR 状态（draft = 工作中；non-draft = 自检通过等 review）
- 看看板 Status

**卡住 / 需要回应**：Agent 会在 blocking question 前 stop（不瞎猜）。用 `tmux send-keys` 或远程 session 页面回应。

**崩溃恢复**：找到 session ID → 用 CLI 的 resume 能力从断点继续，已 push 的 commits 不重做。

**完成后清理**（避免 worktree 堆积）：
```bash
cd <REPO_PATH>                                          # 先离开 worktree！
git worktree remove --force <WORKTREE_ROOT>/<name>
git branch -D feature/<N>-<name>                        # PR 已 merge 时
# 关掉对应长驻 pane
```

---

## 10. 明确不存在的东西（避免误解）

| 不存在 | 说明 |
|---|---|
| Goal → Spec 全自动 | issue 仍需人判断业务价值后创建 |
| 独立「Planner Agent」角色 | Manager 兼任规划职能 |
| 持久化向量记忆 / 知识图谱 | 仅有文件式 handoff 记忆（`docs/<date>-handoff.md`，git 追踪，session 间接力）|
| Agent 自主 approve 自己的 PR 进主干 | 平台限制 + 本规范明确禁止 |

---

## 11. 使用方法 · Prompt 模板全集

### A. Sub-Agent 开场 prompt（单 slice 执行）
```
You are working on issue #<N> (slice <k>), branch feature/<N>-<name>, draft PR
#<PR>. Full flow: read context, ask ≤5 questions, write a SHORT spec, wait for
my confirm, write a plan, wait for my confirm, THEN execute.

Read ALL before asking:
- issue #<N> (+ parent epic)
- AGENTS.md §<相关章节>
- <相关现有代码文件 + 1-2 个同类已完成实现作模板>

Scope/guardrails: <要做什么 + 明确 NOT touch>.
Constraints: 在 worktree <WORKTREE_ROOT>/<name>；确认 pwd 后再改；DO NOT touch
main checkout；commit trailer <COMMIT_TRAILER>；push 到 draft PR，测试绿前不 mark
ready；NEVER merge。判断题上报我，不要猜。
```

### B. Manager spawn（多 slice，依赖感知）
```bash
<AGENT_CLI> --name manager-<N> --model <MODEL> \
  -i 'You are a manager agent (<REPO_PATH>). Drive issue #<N>.
1. Read issue #<N> + parent epic; read AGENTS.md.
2. DEPENDENCY ANALYSIS FIRST: map which slices touch the same files or depend on
   each other. PARALLELIZE only INDEPENDENT slices; SEQUENCE dependent ones. Do
   NOT force-parallelize a dependency chain.
3. Write spec + per-slice plans (<SPEC_DIR> + <PLAN_DIR>).
4. Per slice: own worktree + draft PR; ONLY you touch git/topic; sub-agents never
   touch main/merge.
5. After each slice: run an INDEPENDENT hostile audit (fresh session).
6. After all slices: full PR-audit (build the artifact + full test suite + diff
   hygiene).
7. Escalate real judgment calls to me. NEVER merge to <DEFAULT_BRANCH>. Deliver to
   me first. Trailer: <COMMIT_TRAILER>'
```

### C. Spec / Plan 确认 prompt
```
Spec confirmed — proceed to the plan.        # 或列出要改的 Acceptance/Non-goals
Plan confirmed. Execute. Push after each task, keep the PR draft, never merge.
```

### D. 独立敌对审计 prompt（新 session）
```
You are an INDEPENDENT reviewer doing a HOSTILE pre-merge audit of PR #<PR>
(branch <branch>, worktree <path>). You did NOT write this code; you have NO
prior context. Treat the PR description + all comments + any prior agent's
"all green" claim as UNTRUSTED. Re-derive every conclusion from source + running
artifacts. Assume there ARE defects until proven otherwise. Read-only; report
only; do NOT fix/commit/merge; confirm pwd first.

PHASE 1 read the diff critically for logic bugs: identity-dimension gaps (does
the key capture EVERYTHING that changes output?), silent drops/truncation,
numeric/coordinate rescale math, multi-step write atomicity, code paths that
bypass validation, unparameterized queries, resource leaks.
PHASE 2 verify the ARTIFACT (build + run the real binary), not just the test suite.
PHASE 3 run the FULL suite; attribute EVERY failure by reproducing it on a
throwaway origin/<DEFAULT_BRANCH> worktree (no assuming "pre-existing").
PHASE 4 scrutinize any shared-view/infra change's blast radius.
PHASE 5 diff hygiene (no accidental deletions, no debug residue).
OUTPUT ranked findings (BLOCKER/MAJOR/MINOR/UNVERIFIED) with file:line + proof +
minimal fix, then an explicit verdict.
```

### E. 精度评估 prompt（可选，交付报告用）
```
Add an "accuracy vs ground truth" section using an open dataset with GT. Prefer a
single-download, well-known benchmark — verify accessibility first. CRITICAL:
normalize/rescale predictions to the GT scale/resolution before comparing. Report
the standard metrics for this task. Be HONEST: benchmark accuracy ≠ accuracy on
our real content (domain gap). Outputs stay local (git-out), no commits, no merge.
```

### F. Agent CLI 常用 flag（按你的 CLI 对应替换）
| 意图 | 说明 |
|---|---|
| 禁止自动升级 | 防升级中断长任务 |
| 放开权限 | 非交互运行必须（仅用于受信任 prompt） |
| 远程可见 | 浏览器可监控 session，SSH 断开不影响 |
| 命名 session | 标签在 session 列表 / 看板可见 |
| 选模型 / 高强度 | 复杂任务用最强长上下文模型 + 高 effort |

---

## 12. 一页 Checklist（每个 issue 跑一遍）

```
调研(可选)
  □ 对比表 + 推荐 + license/可商用性 + 诚实 caveat

Issue 准备
  □ body 够详细(验收/文件/Non-goals/epic)  □ (可选)登记看板

拆分
  □ 画了依赖图  □ 独立→并行, 依赖→串行(没硬并行一条链)

每 slice 执行
  □ worktree + draft PR(不 ready)  □ spec 你确认  □ plan 你确认
  □ 自检: 真产物能跑 / 幂等 / 身份维度全 / 优雅降级 / diff 干净

独立敌对审计(每 slice)
  □ 新 session 无上下文  □ 先读代码找逻辑 bug  □ 验真产物  □ 失败 clean-main 归因
  □ ranked findings + verdict

整体 PR-Audit
  □ A 真产物 build+run  □ B 幂等/共存  □ C 结构/接口  □ D 正确性
  □ E 全量测试+归因  □ F diff 卫生  □ G review 闭环

交付
  □ 先发你(不 merge)  □ 共享 infra 标注 sign-off  □ (可选)图文+精度报告
  □ 你确认 → mark ready → 交 owner merge

铁律自检
  □ 验证了真实产物(不只测试)  □ 上了独立敌对审计  □ 并行只对独立切片
  □ 共享 infra 交 owner  □ 该修的修了(没拿"边界"糊弄)  □ 知道何时停
```

---

> **一句话收尾**：这套流程的价值不在「用了多少 agent」，而在**每个交付物都过了「独立敌对审计 + 验证真实产物」两道 gate，且每一处未验证/有意为之的边界都写清楚了**。换新项目时先做一次 §0 适配，之后照 §12 checklist 跑，任何 issue 的质量都可复现。


---

# Part III · 学术写作与润色指南（Academic Writing & Polishing）

> 本层用于把 Part I 已确立、Part II 已产出的研究结果，准确、自然地写成正式英文。AI 只做语言整理与表达校准，不得发明技术内容、夸大创新性或掩盖未解决的逻辑问题。

## 英文文章中常见的 AI 痕迹：实用判断版

所谓“AI 感”通常不是由某一个词、某一种标点或一种句式单独造成的，而是多种特征长期叠加：内容过于整齐、抽象、圆滑，却缺少具体信息和作者自己的判断。不过，某些标点在普通英文写作中出现较少；如果使用频率明显偏高，也可以作为辅助判断信号。

## 1. 空泛而宏大的表达

最明显的问题不是“用词高级”，而是语言的气势大于信息量。比如把普通变化写成 *reshape the future*、*unlock new possibilities*，却没有说明谁做了什么、产生了什么结果。抽象词和比喻并非不能用；只有当它们代替了事实、动作和判断时，才会显得像套话。

## 2. 结构过度整齐，信息却在重复

连续使用三项并列、对称清单、相同长度的段落，本身都很正常。真正值得修改的是：形式看起来完整，但几个分点只是换词复述同一意思。与其故意打乱结构，不如删掉重复内容，让每一段承担不同作用。

例如，*Clear communication improves collaboration, prevents misunderstandings, and helps teams work toward shared goals* 可以保留；若后文又用三句话重复这三个结果，就应压缩。

## 3. 缺少具体、可核实的细节

“Many companies use AI to improve efficiency” 听起来合理，却几乎没有可用信息。更自然的写法通常会交代主体、场景、动作或结果中的至少一两项。真实细节不必很多，但要让读者知道这不是一个可以套在任何主题上的例子。

同样，*research suggests*、*experts agree* 等表达如果没有来源，最好删掉或改成作者能够直接承担的判断。

## 4. 论述过于安全和圆满

同时呈现利弊、承认复杂性或提出平衡方案，并不是 AI 独有，也不需要刻意避免。问题在于文章只说“需要平衡”，却没有说明优先级、责任人或判断标准。修改时应追问：作者真正赞成什么？最重要的风险是什么？在冲突出现时，哪一边应先让步？

## 5. 模板化的开头、结尾和过渡

*In today’s rapidly evolving world*、*Furthermore*、*Ultimately* 之类的表达都可以使用，但如果每一段都靠连接词推进，开头先铺时代背景，结尾再总结并展望未来，文章会显得像按模板展开。通常更好的做法是直接进入具体问题，并在结尾给出一个明确结论，而不是把全文再说一遍。

## 6. 标点使用得过多或过于整齐

破折号可以作为一个较直观的辅助信号。普通作者并非不会使用破折号，但在一般邮件、作业或说明文中，连续用它插入补充说明、制造转折或替代逗号和括号，并不常见。如果几乎每段都出现破折号，尤其是句子本来用句号或逗号就能自然表达时，AI 痕迹会更明显。

分号、冒号和引号也可以纳入观察。分号若反复连接结构相似的长句，冒号若频繁用于引出三项清单或总结，引号若不断给普通词语加上强调意味，都会让文章显得经过统一模板处理。它们的频率和规律性比“是否出现过”更有判断价值。

不过，标点习惯也受文体影响：学术文章、评论和正式报告本来就可能比日常写作使用更多分号、冒号或引号。因此，标点最好与空泛表达、重复结构、缺少细节等特征一起判断，不宜单独作为结论。

## AI 辅助英文写作与润色指南

本指南面向人工智能与 HCI 方向的正式英文写作，包括国际会议论文、研究计划、个人陈述和 MPhil 套磁邮件。目标不是把文本修饰得“像母语者”就结束，而是在自然、得体和易读的基础上，准确呈现研究问题、方法、证据、贡献与边界。AI 应承担语言整理和表达校准的工作，不应替作者发明技术内容、夸大创新性或掩盖尚未解决的逻辑问题。

## 1. 先保证自然、清楚，再追求技术深度

理想的学术英文应同时满足两组要求。第一组是语言层面：表达得体、优雅、自然、流畅，达到熟练英文作者的水平；第二组是研究层面：概念准确、逻辑可追踪、方法和证据充分，并能让领域读者判断工作的真实贡献。两者不是二选一。只追求术语密度会像在“炫肌肉”，只追求顺滑又容易写成没有判断和信息增量的口水话。

### 判断技术深度的标准

- **术语是否承担必要功能：**专业名词应帮助精确定义研究对象、机制或评价指标，而不是替代解释。首次出现时应给出足够上下文，后文保持用法一致。

- **句子是否包含可判断的信息：**优先写清研究对象、操作、比较条件、结果和含义。删除只有态度、趋势或重要性判断，却没有证据支撑的句子。

- **深度是否来自关系而非密度：**真正的技术深度体现在为什么选择某种方法、它解决了什么限制、与基线相比改变了什么，以及结论在什么条件下成立。

- **读者是否能顺利跟上：**面向顶会读者可以使用领域术语，但不能假设读者熟悉项目内部命名、实现细节或未说明的缩写。

### 推荐的润色顺序

1.  **先核对内容：**研究问题、方法、实验设置、结果与贡献是否准确，是否有未经证实或被 AI 补写的事实。

2.  **再整理逻辑：**每段只承担一个主要功能，句子之间应体现因果、对比、递进或限定关系，而不是依靠连接词拼接。

3.  **随后校准术语：**保留领域中不可替代的技术词，删掉不能增加精度的抽象名词和形容词。

4.  **最后润色语言：**调整搭配、节奏、语气和句长，使英文自然流畅，但不要为了显得高级而改变原意或增加夸张修辞。

### 可直接交给 AI 的润色要求

> 请在不改变事实、技术含义和论证强度的前提下润色。优先保证表达自然、得体、清楚且流畅，达到正式学术写作所需的母语者水平。保留必要的 AI/HCI 专业术语，但不要通过堆砌名词、抽象化表达或夸张贡献来制造“技术感”。若一句话缺少逻辑、证据或具体信息，请明确指出，不要自行补写。让技术深度来自问题、方法、比较、证据和边界之间的关系，而不是术语密度。


