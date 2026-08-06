# 论文总览（中文内部理解版）

> 当前标题：**When Does a Legible Latent Axis Earn a Control? A Comparator-Bound Evaluation Contract for Latent-Control Interfaces**
> 目标 venue：IUI。本文档只同步当前论文 framing。数字以生成表、冻结 artifact、evidence ledger 和 `main.tex` 为准。

## 1. 一句话叙事

给模型属性命名并放置 slider，会形成“移动 slider 就能控制对应行为”的承诺。本文主张先设 comparator-bound evaluation gate：只有通过预注册、prompt-comparative、coherence-gated 的行为检验，界面才授予 actionability。五字段 contract 是该 gate 的 interface-facing artifact；console 是 model-evidence instantiation。主叙事先报告没有测试 cell 展示 superiority，再区分 uncertainty、deliberation 与 skepticism 的证据分辨率，不把程序性 0/12 输出写成统一 resolved null。

## 2. HCI 问题

界面一旦给 latent axis 命名并配置 slider，就会暗示该轴不仅可解释，而且能可靠改变目标行为。这一暗示可能影响 calibrated reliance。已有 HCI 文献支持“可见信号会塑造依赖判断”以及“更多 confidence/quality cues 不保证更好校准”，但本文没有访谈、形成性研究或真实用户反馈。因此用户侧问题严格写成 literature-grounded design problem，而不是需求发现。

本文的设计过程也不是虚构的迭代故事，而是：

`model evidence -> failure taxonomy -> interface-evaluation contract -> console instantiation`

## 3. 核心研究问题

**一个可读 latent axis 需要什么证据，才有资格在界面中成为 control，而不只是 diagnostic？**

这不是“steering 能否改变文本”的问题。Control 是比较性行为主张，必须说明：

1. 轴是否在指定模型和方法下可读；
2. 干预是否在目标行为上通过 TRANSFER；
3. 与 bounded prompt channel 相比是否增加控制；
4. 是否引入 calibration 或 coherence 风险；
5. 证据是否只适用于当前 model/method/axis。

## 4. 主要贡献（严格顺序）

### 4.1 Comparative actionability criterion

READ 表示某个内部方向在指定测量下可读；CONTROL 表示该干预在指定比较器、结果、margin 与 coherence 条件下通过行为检查。领域常用的 output movement 门槛不足；正确门槛是相对 bounded prompt channel 的增量行为控制。

### 4.2 Five-field evidence contract（gate 的记录格式）

合同有五个字段：

- **READ**：该轴在什么测量、模型和方向族下可读。READ 是 diagnostic precondition，不是 control evidence。
- **TRANSFER**：该干预是否在行为结果上通过冻结比较。
- **BOUNDED PROMPT COMPARATOR**：在同一预算纪律下，prompt channel 已经达到什么水平。
- **CALIBRATION WARNING**：明确区分 steer-vs-prompt 与 steer-vs-baseline。
- **EVIDENCE TIER**：绑定 model、method、axis、task、layer、protocol 和统计强度，禁止跨设置移植。

对应界面状态：

- READ 有证据、TRANSFER 未通过：可作为 diagnostic，withhold control。
- TRANSFER 欠功效或未测试：显示 unresolved/untested，不写成“不可控”。
- coherence 失败：control 被 instability 阻止。
- 只有在指定设置下通过比较性行为检查后，slider 才获得证据许可。

当前论文没有观察到最后一种状态，因为没有 latent behavioral positive control pass。

### 4.3 Fully worked artifact instantiation

论文首次完整应用五字段 contract，在 Qwen2.5-7B 和 Llama-3-8B 上对 CAA/ITI 使用同一冻结 evaluation procedure：

- prompt channel：16 个预先编写候选，只在 DEV 选；
- latent channel：method-specific 单层加法 `h'_L = h_L + alpha*s_m*u_m`，其中 `s_CAA=1`，`s_ITI=sigma_L`；两者都只在 DEV 从 `alpha in {2,4,6,8,12,16,24}` 选择系数，但 effective injected norm 不同；
- TEST：同 item 配对比较，item-cluster bootstrap；
- 三轴内 Bonferroni；
- superiority margin `delta=0.05`；
- coherence gate 使用 `g_a^S <= 1.5*g_a^0 + 0.02`；`0.02` 是 baseline 接近 0 时的 additive floor，不是纯 ratio gate。

该实验比较的是“steering 替代 bounded prompt”，不是 prompt+steer 组合。

该 application 的输出是 scoped failed-superiority：

`{CAA, ITI} x {Qwen2.5-7B, Llama-3-8B}` 四格中，没有任何轴通过预注册 superiority rule。原先已观察的 frozen seed 加上随后前瞻冻结的四个新 DEV/TEST split seeds，在同一 shared item pool 上的五次 split 均得到相同 no-pass verdict；该结果检验的是 split sensitivity。

这只支持：

> 在测试的 7–8B 模型、任务和 frozen method-specific single-layer additive CAA/ITI convention（系数 `alpha<=24`）范围内，没有展示出超过 bounded best prompt 的控制优势。这里 `alpha<=24` 不是共同 injected-norm 上界：CAA 使用 unit direction，ITI 使用 `alpha*sigma_L`。

不支持：

- latent control 一般不可能；
- activation steering 等价于无效；
- trained、多层、projection、ablation 或其它方法也失败；
- prompt 与 latent channel 等价。

## 5. Results 按设计判断组织

### 5.1 READ：可读是前提，不是结论

C1 是 exploratory facade measurement。两个模型都在聚合上 3/4 轴 hold，但轴组成不同：

Facade denominator 是 same-origin positive-pole reach：`<mean(extraction-positive)-mean(neutral), u_hat>`。它不是 positive-minus-negative contrast vector 的 norm；后者只用于推导 CAA direction。分子同样从 neutral origin 测量 strongest-prompt displacement。

- deliberation、skepticism：两模型都 hold；
- uncertainty：Qwen hold，Llama 不 hold；
- focus：Llama hold，Qwen overshoot/no facade。

因此 READ 必须绑定模型和方向族。C1 测的是 contrastive CAA-style directions，不能给 ITI 继承 READ verdict。

### 5.2 TRANSFER：没有测试 cell 获得 superiority

四格全部 0/3 pass，但信息强度不相同：

- **uncertainty**：四格 frozen steer-minus-prompt CI 都低于 0；
- **deliberation**：混合，post-hoc TOST 仅有两个 ITI boundary-equivalence，CAA 欠功效；
- **skepticism**：MDE 约 0.188–0.279，远高于 `delta=0.05`，只能写 uninformative/underpowered failed-superiority，不能写无效或等价。

### 5.3 Calibration Warning：比较器不能被拿掉

最稳健的表述是 **steer-vs-bounded-prompt contrast**。在 rechecked CAA×Qwen lineage：

- direct steer-vs-baseline compliance 约 `+0.011`；
- direct steer-vs-baseline `1-Brier` 约 `+0.0008`。

所以不是“steering 直接伤害 baseline calibration”，而是 bounded prompt arm 相对 steer-near-baseline 更好。

E-0013 只复查最大 CAA×Qwen cell：

- format compliance：steer 0.826，prompt 0.445；
- paired complete-case steer-minus-prompt：`-0.34`, 95% CI `[-0.51,-0.17]`；
- adversarial missingness bounds：`[-0.478,+0.250]`，跨 0；
- 其它 3 cells 未复查。

因此 interface warning 必须同时显示：frozen-scoring negative contrast、one-cell complete-case support、all-generation missingness 未识别、no grid-wide recheck。

### 5.4 Positive-Control Boundary

E-0014：

- refusal prompt = 95%；
- bounded latent CAA (`alpha<=24`) = 0%；
- natural class-difference norm 约 216，而注入 norm 最多 24。

它证明 endpoint 活着，但暴露 bounded unit-direction scale 问题。

E-0015 使用 raw-magnitude CAA：

- refusal 和三个 metacognitive axes 全部 NO-PASS；
- coherent ceiling 约 `0.5–0.66 x residual norm`；
- 唯一约 `1.05x` 点已经 degenerate；
- random uncertainty direction `-0.24`, CI `[-0.36,-0.12]`；
- null MDE 约 0.19。

因此 under-scaling 在 coherent range 内被显著削弱，instrument 能检测变化，但仍没有 latent behavioral positive control pass。F2 仍是主要 MAJOR 风险。

### 5.5 Logit Diagnostic

E-0015 appendix diagnostic 标记为 `valid_for_paper=false`，不进入 submission evidence，也不支持任何 claim：

- coherent `beta=1` 时 refusal-leading first-token mass 平均约 `+13.9 nats`；
- 同时 `0/5` scored refusals；
- 一个 `+16.9` item 的 greedy completion byte-identical；
- proxy 包含普通或 hedged answer 也可能以其开头的 token，如 `I`。

它只提供 non-confirmatory context。不得写 “handle works”，也不得用于支持 READ、TRANSFER 或核心 negative claim。

## 6. Console 如何改变设计决策

Console 不是展示更多模型内部信息，而是决定一个 affordance 的状态。

论文用明确标注为 illustrative 的设计师场景说明这一点：Maya 为 policy-analysis writing assistant 设计 uncertainty slider。她依次读取 five fields 后，将 slider 改为 diagnostic trace + bounded-prompt/latent comparator view。该场景不是观察、participant 数据或 user-benefit 证据。

以 Qwen uncertainty axis 为例：

1. exploratory READ 可以支持 diagnostic label；
2. TRANSFER 未通过，所以 slider 被 withheld；
3. card 显示 bounded prompt comparator；
4. calibration warning 明确 steer-vs-prompt，并附 steer≈baseline caveat；
5. evidence tier 标注 Qwen、CAA、single-layer additive、当前 task/protocol；
6. CAA 的 READ 不能自动赋给 ITI，Qwen 的结果不能自动赋给 Llama。

这是 evidence-derived design decision，不是用户偏好或 benefit evidence。

## 7. Discussion 的可迁移知识

1. **Legibility is diagnostic.** 可读轴可用于 inspection/debugging，即使尚未获得 control 资格。
2. **Control is comparative.** 需要 outcome、comparator、margin 和 coherence，而不是“输出变了”。
3. **Negative evidence is an interface state.** failed、underpowered、unstable、untested 应分别显示。
4. **Calibration contrast must name the baseline.** steer-vs-prompt 与 steer-vs-baseline 回答不同问题。
5. **Evidence tiers prevent substitution.** model、method、axis 任一变化都产生新的评估义务。

## 8. 规范性目标与待验证假设

本文的规范性目标是避免仅凭 legibility 呈现 actionability。“减少 misleading affordance 或 over-trust”是待验证的 HCI hypothesis，不是本文结果。本文没有证明：

- warning card 改善 calibrated reliance；
- 用户能正确理解 TRANSFER 或 evidence tier；
- console 提升决策质量；
- latent information 应被隐藏。

真人研究必须另外验证这些问题，且不能预设更多 warning 一定有益。

## 9. Scope and Conditions of the Contract

- 第一段集中声明：无 user study，因此 comprehensibility、usability、reliance effects 未测试；正文其它位置不重复这一完整免责声明；
- 无 passing latent behavioral positive control；
- C1 exploratory，单模型单 run，轴组成异质；
- ITI 没有对应 READ validation；
- F1 只复查 CAA×Qwen complete cases，adversarial bounds 跨 0，其余三格未复查；
- skepticism 严重欠功效，deliberation 混合；
- headline 只限 tested bounded naive CAA/ITI、7–8B models/tasks 和 frozen method-specific single-layer additive convention（coefficient `alpha<=24`；CAA `s=1`，ITI `s=sigma_L`）；
- E-0015 scale correction 只覆盖 Qwen single-layer CAA；
- split-seed robustness 共用 item pool；
- Bonferroni 是 cell 内三轴，不是全 12-cell family；
- 64-token cap 可能限制 deliberation；
- 未测试 prompt+steer composition；
- off-manifold mechanism prereg 返回 valid null，机制未知。

后续各条统一采用正面 scope 写法：“contract applies to Y; beyond Y needs new evidence/re-evaluation”。四条不可删除事实是：adversarial missingness bounds 跨 0；其它三格未 format-recheck；skepticism 欠功效；无 user study（仅第一段完整陈述）。

## 10. Conclusion 边界

结论首要主张是方法：五字段 contract 决定界面可以诚实支持什么状态。tested grid 的 no-pass 是 worked instantiation 的输出：

- READ-positive 可以显示为 diagnostic；
- 没有 comparative TRANSFER evidence 时，不应把轴包装为 slider；
- comparator 和 calibration contrast 必须可见；
- negative、underpowered、unstable、untested 都应成为明确界面状态；
- model、method 或 axis 改变后必须重新评估。

## 11. 证据速查

| Evidence | 作用 | 当前允许表述 |
|---|---|---|
| E-0003 / E-0008 | C1 READ setup | exploratory two-model aggregate support with axis heterogeneity |
| E-0005 / E-0006 | C2 frozen adjudication | scoped failed-superiority; uncertainty frozen steer-vs-prompt contrast |
| E-0011 | split robustness | 5 split seeds, same item pool, no pass |
| E-0013 | format recheck | CAA×Qwen complete-case contrast survives; adversarial bounds span zero |
| E-0014 | bounded refusal positive control | endpoint live; bounded latent arm 0%; scale concern exposed |
| E-0015 | scale-corrected positive control | no pass within coherent range; instrument sensitive; F2 still open |
| E-0015 diagnostic | appendix support | +13.9 nats always bound to 0/5 refusals and proxy caveat |
