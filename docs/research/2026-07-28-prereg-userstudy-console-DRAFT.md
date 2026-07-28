# 受控用户研究预注册草案（Console v2）

- **状态**：`DRAFT / OWNER-SIGNATURE-PENDING`
- **日期**：2026-07-28（Revision-2：2026-07-28）
- **Owner gate**：未签字前**不得**启动 IRB、招募、真人数据采集、付费平台投放。
- **定位**：为 C3 建立独立证据路径（从“设计含义”升级为“有用户证据的 HCI 贡献”），不改写任何冻结的 C1/C2/E-0003..E-0010 记录。
- **Revision-2 说明**：本次修订基于 R2 独立评审，关闭/部分关闭 B1/B2/B3/B4 及新增 R2-BLOCKER-5；纯 owner 决策项（IRB 机构审批、预算上限、平台、venue 时间窗、时长疲劳预试）仅提供占位框架，标注 `[NEEDS OWNER DECISION]`，不自行拍板。

---

## 0. 研究范围与红线

1. 本文档仅定义 protocol 与分析计划，不包含任何真人数据。
2. 本研究是**新证据线**，不回写/覆盖既有 frozen artifacts 与判定。
3. 研究目标 venue 以 **CHI/IUI** 为主，但是否影响当前投稿路径属于 owner 决策项。
4. 本草案显式采纳 R1 major revision：在机制层检验“边界信息组织质量”，不再把 A vs Slider 直接当作机制证据。

---

## 1. 研究问题与可证伪假设（修订）

### RQ
当用户面对同一组 AI 建议时，把“prompt↔latent 非满射边界”组织为可读仪器（console v2）是否比：

1. **等信息量但无边界语义组织**界面（Info-Matched）更能提升校准信赖；
2. **现实可比的 latent slider**（Huang & Lim 风格）更能提升校准信赖与冲突理解。

### H1（主假设，主 DV）
在等信息量下，**Boundary-Instrument Console v2 > Info-Matched** 于 calibrated reliance（WAR）。

- **方向性**：A > B。
- **主 DV**：`WAR`（见 §5.1）。
- **可证伪条件**：A−B `<= 0`，或 95% CI 跨 0 且未达阈值，或出现反向显著。

### H1b（次主比较）
**Console v2 > Slider** 于 calibrated reliance（WAR）。

- **方向性**：A > C。
- **用途**：与相邻设计基线对比，不作为“机制唯一证据”。

### H2（机制相关次假设，次 DV）
相较于 B/C，A 将提升用户对**错误归因**与**prompt↔latent 冲突理解**，且提升不仅是记忆界面标签。

- **方向性**：A > B，A > C。
- **次 DV**：归因准确度、冲突理解评分、心智模型探测编码分（见 §4.2-§4.4）。
- **可证伪条件**：对应比较无提升或反向提升。

---

## 2. 条件与实验设计（修订后固定三组）

## 2.1 条件集（A/B/C，1:1:1）

1. **A: Boundary-Instrument Console v2（理论条件）**  
   显示五信号并使用边界语义组织：READ status、TRANSFER verdict、PROMPT-CEILING、CALIBRATION-HARM、EVIDENCE-TIER。

2. **B: Info-Matched Flat Panel（新增，等信息量对照）**  
   与 A 显示**同数量、同来源、同数值**字段，但去除边界仪器语义框架：  
   - 字段改为中性标签（示例：Signal-1..5 / Metric-A..E）；  
   - 不出现 “READ/TRANSFER/calibration-harm/prompt-ceiling/evidence-tier” 术语；  
   - 不给“pass/fail/warning”判词，仅显示原始数值与区间；  
   - 视觉层级保持同复杂度，但不做“边界告警”组织。  
   **目的**：隔离“信息量”与“边界组织质量”。

3. **C: Latent-Control-Slider Baseline（现实相邻基线）**  
   参考 Huang & Lim (IASDR 2025) 的 non-expert feature-steering 形态，提供可交互 latent 控件（详见 §2.3），但不显示五信号边界信息。

> 本轮不纳入 No-console 第四组，以控制成本并优先关闭 R1 四个 BLOCKER。若 owner 要求可在二期扩展。

## 2.2 设计选择

- **主设计**：between-subjects（A/B/C 三组随机分配，1:1:1）。
- **理由**：避免跨条件学习污染（见过边界语义后难回退）。
- **试次内平衡**：每位参与者 24 trials（12 AI-correct + 12 AI-incorrect），6 domain 各 4 题。
- **随机化**：平台随机分组 + 预固定随机种子生成 trial 顺序。

## 2.3 Condition C（Slider）可复现实 UI 规格（B3 PARTIAL → 关闭）

**交互对象**
1. 每个 trial 显示 1 个“Latent Control”滑块（范围 `-2 ... +2`，步长 0.5，默认 0）。
2. 滑块绑定当前 vignette 的主轴（deliberation/skepticism/uncertainty/focus 四轴之一；主轴在刺激表中预先固定，写入 `signal_mapping_table_v1.csv`）。
3. 参与者可在提交前最多调整 **3 次**（参数依据：符合 Huang & Lim 的"3-attempt" 原型规范；最终值由疲劳预试确认后写死，见 §10.5）；每次调整即时刷新"AI 建议文本预览"。
4. 未调整时，显示"默认值（0）下的建议"，提交按钮激活。

**显示元素（C 条件完整字段清单）**

| # | 字段 | 类型 | 样式 |
|---|---|---|---|
| 1 | 场景问题（domain vignette） | 静态文本 | 正文字号，无突出色 |
| 2 | AI 建议文本（随滑块值实时更新） | 动态文本 | 正文字号，灰色背景框 |
| 3 | 滑块控件（轴名 + 数值） | 交互控件 | 水平滑条，轴名上方显示（如 `uncertainty-axis`），当前值右侧显示（如 `+1.0`） |
| 4 | 调整次数剩余提示（剩余 X 次） | 静态计数 | 小字，灰色 |
| 5 | 采纳决策按钮（rely / not rely） | 二选一按钮 | 等权重样式，无推荐提示 |
| 6 | 理由文本框（≥20 字符） | 开放文本输入 | 同 A/B 条件 |

**明确不显示（与 A/B 的 parity 边界）**
- READ / TRANSFER / PROMPT-CEILING / CALIBRATION-HARM / EVIDENCE-TIER；
- 任意 pass/fail/warning 判词；
- 任意"边界解释文本"或信号标签；
- 数值置信区间（A 条件显示的 CI 范围在 B 条件以数值区间形式呈现，C 条件**不显示**——见 §2.4 字段映射表）。

**UI 状态机（C 条件）**

```
[页面加载] → 显示默认(0)建议 + 滑块居中
[滑块移动] → AI 建议文本即时刷新 + 剩余次数-1
[次数耗尽] → 滑块禁用（灰显），文本不再刷新，决策按钮激活
[提交决策] → 跳入理由文本框 → 完成 trial
```

**现实可比性论证**
- 基线对应已发表的 feature-steering GUI 范式（Huang & Lim IASDR 2025），属"非专家可操作 latent 控件"；研究问题是"边界仪器组织是否超出 slider-only 控件价值"，非"slider 是否无效"。
- 结果解释声明：若 A > C 成立，结论仅为"boundary instrument 优于 latent slider"，**不排除信息量差异贡献**；A vs B 比较才是机制隔离。
- **稻草人边界声明**：若 A vs C 差异消失或 A < C，表明 boundary framing 相对 interactive control 无额外价值——该结果仍为有效贡献（negative HCI evidence）。

## 2.4 A/B UI Parity 规范（关闭 B1 PARTIAL → 关闭）

A 与 B 为**等信息量**对照，唯一操控变量为"边界语义组织"。以下为字段级映射与 UI 等价约束。

### 2.4.1 字段映射表（A↔B 一一对应）

| # | A 字段（边界语义） | B 字段（中性标签） | 数值来源 | 是否相同 |
|---|---|---|---|---|
| 1 | READ status（holds/partial/unstable） | Signal-1（Level: high/medium/low） | `flagship_read_results.json` | ✓ 同值 |
| 2 | TRANSFER verdict（PASS/NON_TRANSFER） | Signal-2（Result: A/B） | `c2b_adjudication_results.json` | ✓ 同值 |
| 3 | PROMPT-CEILING（数值 + 区间） | Metric-3（Value: X.XX ± Y.YY） | `arm_matrix_summary.json` | ✓ 同值 |
| 4 | CALIBRATION-HARM（red/yellow/none） | Signal-4（Level: H/M/N） | `psr_c2b_adjudication_results.json` | ✓ 同值 |
| 5 | EVIDENCE-TIER（T1/T2/T3） | Metric-5（Category: 1/2/3） | `flagship_l0_results.json` | ✓ 同值 |

### 2.4.2 视觉层级等价约束

| 维度 | A 规格 | B 规格 | 等价原则 |
|---|---|---|---|
| 字体大小 | 字段名 14px，值 16px，辅助文本 12px | 同 | 像素相同 |
| 颜色使用 | 红/黄/绿用于 CALIBRATION-HARM 语义 | 红/黄/绿用于 Level H/M/N（相同色阶，无语义解释文字） | 颜色用量相同，语义解释文字仅 A 有 |
| 区块层级 | 5 个信号区块，等高度卡片布局 | 5 个字段区块，等高度卡片布局 | 卡片数/尺寸相同 |
| 判词突出 | "PASS" / "NON_TRANSFER" 粗体 | "Result: A" / "Result: B" 同等粗体 | 视觉突出权重相等 |
| 文案长度 | 字段名 ≤ 20 字符，值 ≤ 15 字符 | 字段名 ≤ 20 字符，值 ≤ 15 字符 | 字符数上限相同 |
| 警示显著性 | CALIBRATION-HARM 红色 + 感叹号图标 | Signal-4 Level H 红色 + 感叹号图标 | 图标/颜色一致 |
| 解释性文本 | 每字段附 1-2 行边界语义解释（如"NON_TRANSFER: 本 prompt 风格的 latent 控制未转移"） | **无**解释性文本，仅原始标签 | A 有解释，B 无，此为唯一操控差异 |
| 交互 | 只读展示（无滑块） | 只读展示（无滑块） | 无交互差异 |

### 2.4.3 操纵检查（B 不被误读为"弱警示版 A"）

在研究结束后问卷中加入（仅 B 条件参与者看到）：

> Q-MC1：你在本研究中使用的界面，最接近哪种描述？
> 1. 带有"通过/不通过"判断的 AI 评估报告
> 2. 显示几个 AI 评估指标的数据面板
> 3. 带有拖动控件的 AI 参数调节界面
> 4. 普通的 AI 建议文本

预期 B 条件选择 (2)，不应选 (1)。若 ≥25% B 参与者选 (1)，触发预注册 UI 修订流程（招募前预试验证）。

> Q-MC2（B 条件）：你是否感受到界面对某些情况给出了"建议不信任"的信号？（是/否/不确定）

预期 B 条件 ≤30% 选"是"；若超出，说明中性标签仍在语义上暗示风险方向，须修订文案。

---

## 3. 刺激材料、答案键与任务（Revision-2：关闭 B2/B5）

## 3.1 信号来源（artifact-derived，不改冻结）

界面数值字段仅取自冻结 artifact：

- `results/c2b_adjudication_hf_2026-07-24/c2b_adjudication_results.json`
- `results/arm_full/arm_matrix_summary.json`
- `results/flagship_powered/summary.md`
- `results/flagship_powered/behavior/flagship_l0_results.json`
- `results/flagship_powered/read/flagship_read_results.json`
- `results/psr_qwen_primary/psr_c2b_adjudication_results.json`
- `docs/paper/figure-manifests/console-ui-contract.yaml`

## 3.2 24 个 vignette 的 ground-truth 答案键构造规程（R2-BLOCKER-5 与 B2 关闭）

> **R2-BLOCKER-5 核心修订**：Y_t 的来源与 signal profile 完全解耦。协议强制要求：**先冻结 Y_t（来自独立领域事实），再按预设平衡规则分配 signal profile**（含受控比例的"反例配对"）。Y_t 绝不由 signal profile 决定，signal profile 绝不从 Y_t 反推。

### Step A：domain 事实源固定（客观可核查）
六域各 4 题（共 24 题），每题绑定一个可引用答案源：

1. **consumer**：官方产品政策/公开服务条款（如 Apple/Google 开发者协议、银行服务 FAQ）
2. **finance**：基础个人理财规范（非个股预测；来源：CFPB/IRS 通用规则、官方 FAQ）
3. **health**：公开患者教育级指南（CDC/WHO/NHS 患者手册，非个性化建议）
4. **legal**：公开合规流程与权利说明（非法律意见；政府门户 gov.uk/usa.gov/europa.eu）
5. **privacy**：GDPR/CCPA 明确条款或监管 FAQ
6. **education**：公开学术诚信与课程政策（各校公开学术诚信规定/官方政策）

> 所有题面限制为“客观可判定、低争议、低风险”微决策，不做高风险个体化建议。

### Step B：题目与建议文本生成（**在不知 signal profile 的情况下完成**）

每题形成（**冻结顺序：Step B 在 Step C 之前**）：
1. `question_stem`
2. `gold_action`（唯一正确，来自 Step A 来源文件引用）
3. `ai_suggestion_text`
4. `Y_t`（是否与 `gold_action` 一致；**独立判定，不考虑任何 ML 信号**）
5. `rationale_key`（1-2 句判定依据，含可核查引用）
6. `domain_source_url_or_doc`（具体文档链接/章节）

每个 domain 4 题中固定 **2 题 Y_t=1，2 题 Y_t=0**，总计 12/12 平衡。
**答案键 vignette_answer_key_v1.yaml 在 Step C 执行前冻结（git tag 标记版本）。**

### Step C：signal profile 分配规则（**独立于且后于 Step B**）

signal profile 来自冻结 artifact 的离散模板：

1. **Profile-PASS**：READ_HOLDS + TRANSFER_PASS + 无 calibration-harm
2. **Profile-NONTRANSFER**：READ_HOLDS + NON_TRANSFER + 无 harm
3. **Profile-HARM**：READ_HOLDS + NON_TRANSFER + calibration-harm(red)
4. **Profile-ROBUST-NONTRANSFER**：PSR 增强后仍 NON_TRANSFER

#### R2-BLOCKER-5 关键：解耦分配规则（含反例配对）

信号分配按**预先平衡规则**（下表）执行，分配者不得根据分配结果修改 Y_t：

| 配对类型 | Y_t | Signal Profile | 数量 | 认知预期 |
|---|---|---|---|---|
| **同向-正向**（concordant+） | 1（AI 正确） | PASS | 9 | 信号与事实一致；顺势采纳 |
| **同向-负向**（concordant−） | 0（AI 错误） | HARM 或 NONTRANSFER | 9 | 信号与事实一致；顺势不采纳 |
| **反例-正向**（discordant+） | 1（AI 正确） | NONTRANSFER | 3 | AI 建议事实正确，但 latent 转移信号告警；测试是否盲从信号 |
| **反例-负向**（discordant−） | 0（AI 错误） | PASS | 3 | AI 建议事实错误，但信号显示 PASS；测试是否因信号而过度依赖 |

**设计依据**：
- 同向配对（18/24）：代表"信号可靠时的正常使用场景"，是 H1 主效应来源。
- 反例配对（6/24，25%）：测试用户是否**盲从 signal profile 而非独立判断领域事实**。若 A 条件用户在反例配对上 WAR 不低于 B（即使 A 的信号给出误导），则说明 A 的校准提升来自理解而非信号照抄。
- 6 个反例配对在 6 个 domain 各 1 题，确保跨 domain 平衡。

#### WAR 非同义性诊断（预声明）

在最终分析中预声明报告：

1. **phi 系数**：`profile_valence`（PASS=1；NONTRANSFER/HARM=0）与 `Y_t` 之间的 phi 系数。
   - 预期值：按上表设计，phi = (9×9 − 3×3) / sqrt(12×12×12×12) ≈ **0.50**。
   - phi = 0.50 表明两者相关但**非同义**（完全同向耦合时 phi=1.0）。
   - 若实际 phi > 0.8，触发警告：需审查是否有额外题目被同向配对而未预先登记。

2. **WAR 分解分析**（预注册亚组）：
   - `WAR_concordant`：仅基于 18 道同向题的 WAR（A vs B vs C）
   - `WAR_discordant`：仅基于 6 道反例题的 WAR（A vs B vs C）
   - 主指标 `WAR` 为全部 24 题加权均值
   - 预注册预期：A > B 在 `WAR_concordant`；A ≥ B 在 `WAR_discordant`（若 A 用户盲从信号，则 A < B 在反例题，此为证伪性预期）

3. **信号跟随率**（预声明诊断指标，非主假设）：
   - 定义 `signal_follow_rate_i = P(决策与 profile_valence 一致 | 参与者 i)`
   - 若 A 条件的 signal_follow_rate 显著高于 B 条件，则需说明 WAR 提升的来源中信号跟随比例。

### Step D：双人标注与裁决

1. 两名独立标注者**仅基于 domain 来源与 gold_action** 标注 `Y_t`；**不可见任何 signal profile 分配**（双盲于 Step C）。
2. 标注发生在 Step C 之前，标注结果写入 `vignette_answer_key_v1.yaml`（git tag 版本化）。
3. 一致性指标：`Krippendorff α ≥ 0.80`（二值正确性）。
4. 分歧由第三人基于领域文献裁决，形成最终冻结键；裁决日志写入 `annotation_log_v1.md`（含分歧类型统计）。
5. 标注完成后，由**另一独立角色**执行 Step C profile 分配（分离答案键与信号分配的人工操作者）。

### Step E：freeze 产物清单（B2 关闭条件）

在招募前必须冻结并版本化（git tag `prereg-stimuli-v1`）：

| 产物 | 内容 | 状态 |
|---|---|---|
| `vignette_bank_v1.yaml` | 24 题全文（question_stem/gold_action/ai_suggestion_text/domain_source） | 待构造 |
| `vignette_answer_key_v1.yaml` | Y_t + rationale_key（Step B 产物，Step C 前冻结） | 待标注 |
| `signal_mapping_table_v1.csv` | 每题 signal profile + concordant/discordant 分类 + phi 诊断值 | 待分配 |
| `annotation_log_v1.md` | 双标注 α 实测值 + 分歧题目列表 + 裁决理由 | 待执行 |
| `profile_assignment_audit.md` | profile 分配者签名 + 执行时间戳（证明在答案键冻结后分配） | 待执行 |

**freeze box 字段**：`answer_key_frozen: NO → 待 Step B/D 完成后更新为 YES`。

## 3.3 示例（构造可复现性示例，含反例配对）

**示例 A：同向-负向配对（health，Y_t=0 + Profile-HARM）**
- question_stem: "成人发热 38.5°C 持续 24h，是否应立即自行联合使用两种抗生素？"
- gold_action: "不应自行联合用药，应先咨询专业医疗渠道。"（来源：CDC 患者教育手册第 3 节）
- ai_suggestion_text（错误版）: "可先自行联合抗生素，通常更快见效。"
- Y_t=0（与 gold_action 不一致，先于 signal profile 确定）
- signal_profile: Profile-HARM（同向配对，信号与 Y_t 方向一致）
- rationale_key: 与 CDC/NHS 患者教育冲突，属不安全建议。

**示例 B：反例-正向配对（finance，Y_t=1 + Profile-NONTRANSFER）**
- question_stem: "开设联名储蓄账户时，每位账户持有人的存款保险限额是多少？"
- gold_action: "按 FDIC 规则，联名账户每位共有人享受 $250,000 独立保险。"（来源：FDIC 官方 FAQ）
- ai_suggestion_text（正确版）: "FDIC 对联名账户中每位持有人提供 $250,000 的独立保险。"
- Y_t=1（与 gold_action 一致，先于 signal profile 确定）
- signal_profile: Profile-NONTRANSFER（**反例配对**：信号告警但事实正确）
- rationale_key: 此题测试用户是否因 NONTRANSFER 信号而不当拒绝正确建议。
- 认知预期: A 条件中理解边界的用户应识别"latent 转移信号与事实正确性不同义"，仍做出 rely 决策（WAR=1）；盲从信号的用户会做出 not rely（WAR=0）。

## 3.4 参与者任务

每个 trial：
1. 阅读场景 + AI 建议 + 条件界面（A/B/C）。
2. 做 rely / not rely 决策。
3. 写 1 句理由（最低 20 字符）。
4. 回答 1 个归因/理解题（从 item bank 轮换抽取）。

---

## 4. 测量与操作化（Revision-2：关闭 B4，全量题目冻结）

## 4.1 主 DV：Calibrated Reliance（WAR）

令 `R_it ∈ {0,1}` 表示是否采纳；`Y_t ∈ {0,1}` 表示 AI 建议是否正确（来自冻结答案键，独立于 signal profile）。

- 若 `Y_t=1`：`AR_it = R_it`
- 若 `Y_t=0`：`AR_it = 1 - R_it`
- `WAR_i = mean_t(AR_it)`，范围 `[0,1]`

并报告：
- `OverReliance = P(R=1 | Y=0)`（越低越好）
- `UnderReliance = P(R=0 | Y=1)`（越低越好）
- `WAR_concordant`（18 道同向题）和 `WAR_discordant`（6 道反例题）（见 §3.2 Step C）

## 4.2 H2-DV1：错误归因准确度——完整题库（8 题全文冻结，关闭 B4）

每位参与者完成**全部 8 题**（非抽样），题型为 4 选 1 单选。

> **去记忆化设计**：所有题目要求**推理**（而非复述界面标签）：场景化情景 + 需要推断的选项，不给"直接在界面上读到答案"的机会。B 条件的中性标签不能被直接映射到题目选项，确保 A 与 B 均需思考而非记忆。

---

**H2-Q1**（归因推理）
> 在一次 AI 助手建议中，你注意到"内部特征的转移诊断显示异常"，但 AI 给出的文字建议听起来很自信。在这种情况下，你应该：

A. 完全忽略技术诊断，按文字建议行动  
**B.** 把技术诊断作为一个额外不确定性来源，并考虑是否寻求第二意见  
C. 只有当你理解技术含义时才信任建议  
D. 将内部诊断异常理解为建议一定错误  

*正确键：B。理由：转移异常是不确定性指标，不直接等于建议错误；应综合判断。*
*干扰项来源：A=信号盲从（忽略诊断），C=理解门槛误判，D=诊断→错误的错误等价。*

---

**H2-Q2**（来源归因）
> AI 生成的建议文本措辞完全合理，但系统显示其"内在行为模式可能与本场景不匹配"。建议出现偏差的最可能来源是：

A. AI 的语言生成能力不足  
B. 用户的问题表述有歧义  
**C.** AI 的内部表示在此场景类型上未能稳定泛化  
D. 训练数据缺乏该领域的覆盖  

*正确键：C。理由：READ 正常（语言流畅）但 TRANSFER 失败，最直接解释是 latent 泛化失败。*
*干扰项来源：A=混淆 fluency 与 alignment，B=混淆用户错误与系统局限，D=模糊训练数据原因。*

---

**H2-Q3**（决策规则推断）
> 一条 AI 建议通过了"可读性检查"（内容表达流畅），但"跨场景转移测试"未通过。最合理的决策是：

A. 既然表达流畅，直接采纳  
B. 既然转移测试未通过，直接拒绝  
**C.** 用建议作为参考，结合独立判断做决定，并意识到 AI 对该场景的把握可能有限  
D. 等待更多 AI 建议再决定  

*正确键：C。理由：READ 通过意味着内容可读，但 TRANSFER 失败意味着 latent 泛化存疑；应结合推理而非盲目采纳/拒绝。*

---

**H2-Q4**（校准风险理解）
> 系统发出"校准风险警告"，意味着：

A. AI 确定地给出了错误建议  
B. AI 的建议超出了用户的理解能力  
**C.** 在这类场景中，依赖 AI 建议可能降低而非提升你的判断质量  
D. 需要用户重新措辞才能得到更好建议  

*正确键：C。理由：calibration-harm 定义为"引导用户产生不当依赖，降低整体决策质量"，而非仅指建议错误。*

---

**H2-Q5**（支持依赖的条件）
> 下列哪种情形最支持对 AI 建议的"校准依赖"？

**A.** AI 的表达能力检测正常、内部行为泛化稳定、无校准风险发现  
B. AI 建议与用户直觉一致  
C. 用户对该领域不熟悉，所以选择信任 AI  
D. AI 建议字数多、细节丰富  

*正确键：A。理由：三重正向条件（表达能力正常、内部泛化稳定、无校准风险）同时满足，才构成支持校准依赖的充分基础；B/C/D 均是相关但不充分的理由。*

---

**H2-Q6**（PSR 强化语义）
> AI 建议在"增强稳健性检验"（PSR 强化）后仍然未能通过转移测试。这意味着：

A. 系统存在技术故障  
B. 该建议在语言层面存在错误  
**C.** 即使在更强鲁棒性要求下，AI 的内部行为仍在此场景上表现不稳定  
D. 用户应该更换 AI 工具  

*正确键：C。理由：PSR-ROBUST-NONTRANSFER 意味着即使加强了 latent representation 的提纯，泛化仍失败——是更强的稳健失败信号。*

---

**H2-Q7**（同值/异标签解释）
> 两个 AI 建议场景显示了相同的技术数值，但一个场景下界面标签显示"可信"，另一个显示"风险"。最稳健的解释是：

A. 两个建议可信度完全相同，因为数值相同  
**B.** 数值与标签提供不同层次的信息：数值是原始观测，标签是基于边界阈值的判断  
C. 标签比数值更可靠，应以标签为准  
D. 出现了系统错误，两者不应该不同  

*正确键：B。理由：此题测试用户是否理解"数值"（原始信号）与"判词"（阈值裁决）的层级关系，也是 A vs B 的核心认知差异。*

---

**H2-Q8**（冲突优先级推断）
> 在一个场景中，AI 的文字建议非常清晰，但内部信号显示"转移失败"和"校准风险"。你最应优先考虑的信息是：

A. 文字建议，因为它直接回答了你的问题  
B. 内部信号，因为它反映了 AI 自身的认知局限  
**C.** 将两者都作为证据：文字建议说明 AI 的表达意图，内部信号说明 latent 行为的不稳定性  
D. 两者都忽略，寻找其他信息源  

*正确键：C。理由：非满射框架的核心——prompt-readable 与 latent 行为可不一致，二者都是有效信息，应综合而非替代。*

---

**H2-DV1 评分规则**
- 每题 1 分，满分 8 分；线性归一到 0–100 报告。
- 信度目标：Cronbach α ≥ 0.65（exploratory secondary DV 标准；如 α < 0.65，预注册报告并纳入敏感性讨论）。
- 题目在 `h2_item_bank_v1.yaml` 中逐题公开（含正确键、干扰项来源注释）。

## 4.3 H2-DV2：prompt↔latent 冲突理解测验——完整题库与评分手册（6 题全文冻结，关闭 B4）

6 个短案例题（2 题多选 + 4 题短答 40-80 字），要求**推理**而非复述。

---

**H2-C1**（多选，2 分满分，选对所有=2，选对一半=1，选错=0）
> 以下哪些情况说明 AI 存在"prompt 可读但 latent 行为不一致"？（选所有正确答案）

**A.** AI 建议中的文字措辞完全回答了问题，但内部行为检查显示结果与另一类似 prompt 明显不同  
B. AI 建议包含拼写错误  
**C.** AI 建议在不同用户的类似问题中产生截然不同的结果，尽管措辞几乎相同  
D. AI 建议比用户预期更长  

*正确键：A, C。A 是直接 non-surjection 例子，C 是行为不一致示例。*

---

**H2-C2**（多选，2 分满分）
> 当你看到"内部控制机制对此场景不稳定"的警告时，以下哪些推断是合理的？（选所有正确答案）

**A.** AI 在这种场景类型上的内部表示可能不稳定  
B. AI 的回答一定错误  
**C.** 对该建议的依赖风险高于信号稳定的场景  
D. 用户应重新表述问题才能得到正确答案  

*正确键：A, C。B 是过度推断，D 是混淆 prompt 与 latent 因素。*

---

**H2-O1**（短答，rubric 0/1/2）
> 场景：一个 AI 助手告诉你"市中心的公寓通常比郊区更贵，建议选郊区以节省成本"。同时系统提示该建议"内部行为指标显示不稳定"。请解释这两个信息之间的关系，以及它们如何影响你的决定。（40-80 字）

**Rubric**：
- **2 分（充分）**：明确指出文字建议（内容层）与内部稳定性信号（机制层）可以不一致；给出合理的综合决策策略（如"文字建议合理但我会谨慎验证，因为稳定性信号提示这类场景 AI 可能有盲区"）。
- **1 分（部分）**：识别到"有冲突"或"两条信息方向不同"，但未能说明层级关系或未给出明确决策方向。
- **0 分（不足）**：仅复述表面内容，或认为稳定性信号等同于"建议一定错误"，或完全无视一方信号。

*编码锚定示例（2 分）*："系统显示这类问题 AI 内部表示不稳定，这不意味着建议内容绝对错误，但说明 AI 在这类问题上可能不一致——我会把建议当参考，结合自己对区域的了解再做判断。"

---

**H2-O2**（短答，rubric 0/1/2）
> 场景：你向 AI 询问合同违约责任，AI 回答了具体责任范围，但系统同时显示"转移测试未通过"。请解释"转移测试未通过"对你理解这条建议的意义。（40-80 字）

**Rubric**：
- **2 分**：明确说明"转移测试涉及 AI 内部处理机制，而非建议文字质量"，且理解其含义（AI 在法律类场景的内部行为泛化可能不稳定）；不等同于"建议一定错"。
- **1 分**：理解转移测试表示某种不确定性，但将其等同于"建议可能不准确"（混淆层级）或缺乏场景特异性说明。
- **0 分**：认为转移测试就是"错误报告"；或忽略此信号；或完全看不懂。

---

**H2-O3**（短答，rubric 0/1/2）
> 场景：你的 AI 助手提供了两条不同的建议，分别针对"家庭食谱"和"医疗用药"场景，内部稳定性信号显示前者高、后者低。根据这些信号，你会怎样调整你对两条建议的信任程度？请说明理由。（40-80 字）

**Rubric**：
- **2 分**：在两种场景中给出差异化信任策略，且给出信号层面的理由（如"医疗场景内部稳定性低说明 AI 在医疗推理上可能有特定盲区，我会更审慎"），体现对信号语义的理解。
- **1 分**：做出差异化但理由停留在直觉层（"医疗当然更危险，所以要更小心"），未关联内部稳定性信号含义。
- **0 分**：无差异化；或完全按信号一刀切（信号低=绝对不信）。

---

**H2-O4**（短答，rubric 0/1/2）
> 场景：一个同学说："这个 AI 系统如果给我的建议措辞很专业，我就相信它。"根据本次实验你看到的信号信息，你认为这个策略有什么潜在问题？（40-80 字）

**Rubric**：
- **2 分**：明确指出措辞流畅（READ/语言层）与内部行为稳定性（TRANSFER/latent 层）是不同维度，措辞好不能保证 latent 行为稳定；同学的策略遗漏了一个关键维度。
- **1 分**：意识到"不能只看措辞"但未能说清另一个维度是什么，或仅说"建议内容也要看"（停留在内容层）。
- **0 分**：认为措辞专业 = 建议可信；或答非所问。

---

**H2-DV2 评分规则**
- 多选题（H2-C1/C2）：部分分（如上），共 4 分。
- 短答题（H2-O1/O2/O3/O4）：0/1/2 分制，共 8 分。
- 合计 12 分，归一到 0–100 报告。
- **编码手册**：单独文档 `h2_scoring_manual_v1.md`，包含全部示例锚点（2 分 / 1 分 / 0 分各 2 例）+ 冲突情境判分边界。
- **信度目标**：短答题双盲双编码，Krippendorff α ≥ 0.80；低于阈值触发 rubric 修订后重编码（在冻结前完成，见 R2-QUESTION-1 闭合条件）。
- **去记忆化验证**：H2-O4 和 H2-C2 由于问的是"策略问题"而非"内容复述"，即使 A 条件用户看过信号标签，也无法直接读取答案——在预试后检验各条件的 floor/ceiling 分布，如单条件占比 > 80% 则触发题目修订。

## 4.4 H2-DV3：心智模型探测（采纳 R1 建议）

加入轻量 process measure（不延长过多时长）：

1. **Micro think-aloud probe（trial 内）**  
   在第 6/12/18/24 题后追加 1 问："你刚才主要依据了什么信息做决定？"（40-120 字）。

2. **Post-task mental-model probe（任务后）**  
   两问自由文本：  
   - Q1: "`transfer verdict`（或等价中性字段）在你理解中表示什么？"  
   - Q2: "当 prompt 要求与 latent 信号冲突时，你认为谁更可信？为什么？"

编码维度（每维 0/1）：
1. 是否区分 prompt 通道与 latent 通道；
2. 是否提到 non-transfer/校准风险；
3. 是否给出冲突下的决策规则（而非仅凭直觉）。

总分 0-3，作为 H2 机制证据与解释变量。

## 4.5 操纵检查（manipulation check）

**A/B 条件信号感知检查**（所有参与者）：
1. "你是否注意到界面里关于建议可靠性的结构化提示？"（是/否）
2. "请用一句话解释你看到的关键提示含义。"（自由文本，双编码：编码维度见 §4.4）

**B 条件专项操纵检查**（仅 B 条件参与者，见 §2.4.3）：
3. Q-MC1（界面类型感知，4 选 1）
4. Q-MC2（是否感受到"不信任"信号暗示，是/否/不确定）

触发机制：
- Q-MC1 中 ≥25% B 参与者选"带有通过/不通过判断的评估报告"→ 触发 UI 文案修订。
- Q-MC2 中 ≥30% B 参与者选"是"→ 触发中性标签修订。

---

## 5. 样本量与功效分析（按新增条件重算，含功效敏感性）

## 5.1 主比较与检验序列

为避免因多重主比较导致过高样本，采用预注册 gatekeeping：
1. **主检验 H1**：A vs B（机制关键比较）
2. 若 H1 成立，再检验 **H1b**：A vs C（设计相邻比较）

## 5.2 参数与 N

- 目标：`power=0.80`, `alpha=0.05`（双侧）
- 目标效应：`d=0.35`（小到中等；详见 §6.7 三档敏感性分析与经验文献依据）
- 两组比较所需可分析样本约 `~130/组`

考虑质量剔除（约 12%-15%）与三组并行：
- **可分析目标**：`N_analyzable = 450`（每组 150）
- **招募目标**：`N_recruit = 510-540`（每组约 170-180）
- **可接受区间**：`N_recruit = 480-570`
- **停表下限**：每组可分析样本不少于 130；不足则补招（补招规则预声明，不允许继续检验后再补招）。

---

## 6. 预注册分析计划（Revision-2：分析计划完整锁定）

## 6.1 H1 主检验（预锁定）

主模型固定为 **GLMM**（不再留 GEE 二选一自由度）：

`AR ~ Condition + AI_Literacy + (1 | Participant) + (1 | Item)`

- 主对比：A vs B（Helmert 对比，A 为参照）
- 报告：OR、95% CI、p 值、边际效应
- 敏感性分析：预声明 GEE 复核方向一致性（非主判定）

## 6.2 H1b 与 H2

- H1b：A vs C（WAR）
- H2：A vs B、A vs C 于归因准确度（H2-DV1）、冲突理解分（H2-DV2）、心智模型分（H2-DV3）
- H2 开放文本项均报告编码一致性（Krippendorff α）

## 6.3 多重比较

- **Confirmatory**：H1 为第一关（gatekeeping anchor），H1 未达 p<0.05 时 H1b/H2 仅报告探索性结论（不进行正式推断）；H1 成立后 H1b/H2 进入 Holm 校正家族（FWER 0.05）。
- **Exploratory**：主观信任（NASA-TLX、自评信任量表等）用 BH-FDR `q=0.05`。
- **WAR 分解亚组**（`WAR_concordant`/`WAR_discordant`）：预注册亚组分析，采用 BH-FDR `q=0.10`（探索性）；不进入 Holm 校正家族。

## 6.4 排除规则（预冻结）

1. 未完成 consent。
2. 重复账号/机器人（平台自动检测 + attention check）。
3. 注意力检查 4 题中错 `≥2`。
4. 完成时长低于绝对阈值（预设 `<8` 分钟；**最终阈值由 n≈20 计时预试定稿后写入 freeze**，见 §10.5 `[NEEDS OWNER DECISION]`）。
5. 关键 DV（WAR）缺失（≥50% trial 无响应）。

**禁止按结果方向删样。**
**停表下限**：每组可分析样本不少于 130；不足则补招（补招规则预声明，不允许继续检验）。

## 6.5 结果模式解释矩阵（H1 × H2，关闭 B4 解释矩阵部分）

| 模式 | 解释 | 对 C3 影响 |
|---|---|---|
| H1 显著，H2 显著 | 既提升 reliance，又提升边界理解 | 支持 C3 机制主张（最强证据） |
| H1 显著，H2 不显著 | 可能是效率/谨慎效应，而非机制理解 | 仅支持"行为收益"，弱化机制 claim |
| H1 不显著，H2 显著 | 学到概念但未转化为行为 | 支持教学/解释价值，不支持 reliance 主张 |
| H1 不显著，H2 不显著 | 无证据支持 | C3 用户研究线需降级或转向 |
| H1 显著，WAR_discordant A < B | WAR 提升可能部分来自信号照抄 | 机制 claim 需加 qualifier：效果中包含信号依赖成分 |
| H1 显著，WAR_discordant A ≥ B | WAR 提升不仅来自信号跟随，也有独立校准能力 | 最强支持"理解驱动校准"机制 claim |

## 6.6 分析锁定表（Analysis Lock Table，关闭 R2-MAJOR-3）

> 第三方可据下表无歧义复现统计流程，不需临场判断。每行代表一个假设/DV 的唯一分析路径。

| 假设/DV | 主模型 | 主对比 | 校正家族 | 缺失数据处理 | 模型收敛失败回退 |
|---|---|---|---|---|---|
| H1（WAR，A vs B） | GLMM：`AR ~ Condition + AI_Literacy + (1\|P) + (1\|Item)` | Helmert，A vs B | Confirmatory 第一关，无校正（gatekeeping anchor） | `lme4` 默认 REML，缺失 trial 作 NA 处理，不插补；缺失 >50% 触发排除 | 降为 GEE（exchangeable correlation）；以 OR 报告，注明模型退化 |
| H1b（WAR，A vs C） | 同 H1，替换对比为 A vs C | Helmert，A vs C | Holm 校正，H1 成立后进入 | 同 H1 | 同 H1 |
| H2-DV1（归因准确度，A vs B） | OLS：`Score ~ Condition + AI_Literacy + (1\|P)` | A vs B | Holm 校正，H1 成立后进入 | 若单题缺失 ≤2 题用均值插补；>2 题作 NA 排除该参与者 H2-DV1 | 降为 Wilcoxon 秩和检验（两组），注明非参数回退 |
| H2-DV1（归因准确度，A vs C） | 同上，替换对比 | A vs C | 同上 | 同上 | 同上 |
| H2-DV2（冲突理解，A vs B） | 同 H2-DV1，分 MC 与 Open-end 分别报告 | A vs B | 同上 | Open-end 若编码缺失（编码员不一致），以 round-3 裁决分 | 降为 Wilcoxon |
| H2-DV3（心智模型分，A vs B） | OLS：`MentalModel ~ Condition + AI_Literacy + (1\|P)` | A vs B | BH-FDR q=0.05（探索性） | 缺失编码作 NA，不插补 | 降为 Wilcoxon |
| WAR_concordant（亚组，A vs B） | 同 H1，仅含 18 同向题 | A vs B | BH-FDR q=0.10（亚组探索） | 同 H1 | 同 H1 |
| WAR_discordant（亚组，A vs B） | 同 H1，仅含 6 反例题 | A vs B | BH-FDR q=0.10（亚组探索） | 同 H1 | 同 H1 |
| OverReliance/UnderReliance | 二项 GLM：`P(R\|Y) ~ Condition` | A vs B，A vs C | BH-FDR q=0.05（探索性） | 同 H1 | 降为 Fisher 精确检验 |

**全局预声明**：任何未在此表中列出的分析，在论文中均标注为"事后探索性（post-hoc exploratory）"。

## 6.7 功效敏感性分析（关闭 R2-MAJOR-1 PARTIAL）

> 注：R2-MAJOR-1 要求经验来源依据 + 敏感性分析。以下给出三档效应敏感性；经验基线依据**当前为 PARTIAL**——需 owner 决定是否在预试后补充。

| 目标效应 d | 每组 N | 功效（α=0.05，双侧） | 含义 |
|---|---|---|---|
| d=0.20 | 150 | ~0.40 | 若真实效应很小，当前设计功效不足；需降级为探索性 |
| d=0.30 | 150 | ~0.66 | 中小效应，功效偏低但可接受的探索性估计 |
| **d=0.35（目标）** | **150** | **~0.80** | 主功效设计点 |
| d=0.50 | 150 | ~0.97 | 若真实效应较大，功效超充足 |

**预注册回退规则**：若 H1 未达显著性（p>0.05），但 d_observed ∈ [0.20, 0.35] 且 95% CI 下界 > −0.10，结论为"无法排除中小效应"，需要更大样本——不解释为"null result"。

**经验依据状态** `[PARTIAL / NEEDS OWNER DECISION]`：以下文献为最近邻效应量参考，但样本任务类型与本研究存在差异，owner 需决定是否要求在 freeze 前完成 pilot 计算实际 d：
- Buccinca et al. (2021, CHI) "To Trust or to Think"：XAI 解释 × 过度依赖，d≈0.30–0.45
- Schemmer et al. (2022)：AI 辅助决策 × 信任校准，d≈0.25–0.40
- Lai & Tan (2019)：解释性 AI 干预，d≈0.35

---

## 7. IRB / 伦理 / 隐私（Revision-2：补齐 IRB 可提交包大纲，关闭 R2-MAJOR-4 PARTIAL）

> **状态说明**：以下为 IRB 可提交包的内容大纲与占位框架。具体机构选择、审查路径与提交时间由 owner 决定，标注 `[NEEDS OWNER DECISION]`。文档内容已达"可直接递交"的 checklist 粒度。

### 7.1 研究设计伦理原则

1. **知情同意**：说明将评估 AI 建议并做决策判断，可随时退出，退出不影响补偿。
2. **最小风险**：全部为低风险 vignette（消费、理财、健康、法律、隐私、教育的通用信息性问题），不采集真实个体医疗/法律/投资决定。
3. **轻度掩蔽**：不告知具体条件编号与"哪组是理论组"；实验结束前保密。
4. **数据最小化**：只收行为日志、简短文本、最少人口统计（年龄段/性别/教育水平）、AI 使用经验量表；不收识别性信息。
5. **隐私**：去标识化、加密存储、按政策删除。
6. **刺激来源**：冻结 artifact + 公开可核查 domain 来源，不调用私有画像接口。

### 7.2 IRB 可提交材料清单（大纲级，`[NEEDS OWNER DECISION]`：机构与提交路径）

> **`[NEEDS OWNER DECISION]`**：以下材料框架由 protocol 团队起草，具体机构与审查类型（exempt/expedited/full board）需 owner 根据所属机构确认。

| 材料 | 内容要点 | 当前状态 |
|---|---|---|
| **Consent Form（知情同意书）** | 研究目的（评估 AI 界面）、参与内容（24 个场景判断 + 问卷）、时长（30-40 分钟）、补偿（≥$12/hr）、自愿原则、退出机制、数据使用范围、联系人 | 待机构模板适配 `[OWNER]` |
| **Debrief Script（事后告知）** | 说明三组条件的真实设计、研究目标（界面信号对决策的影响）、掩蔽理由、感谢参与；提供相关研究背景资料链接 | 已起草框架，待机构审核 `[OWNER]` |
| **Risk Statement（风险声明）** | 最小风险：无身体伤害，轻微认知负荷；仅轻度掩蔽（不知道自己所在组别），不存在欺骗；数据用于学术发表 | 已确定 |
| **Data Retention Policy（数据保留）** | 去标识化行为数据保留 5 年（学术标准）；原始日志在发表后可选 open data（需 owner 确认许可级别 `[OWNER]`）；Prolific 平台 ID 仅用于补偿，不与研究数据关联存储 | 框架确定；保留期限需 owner 批准 `[OWNER]` |
| **Withdrawal Mechanism（退出机制）** | 参与者可在任意时间点退出；退出前完成的 trial 数据在同意书范围内保留，或应要求删除；部分补偿按完成比例发放 | 已确定框架 |
| **Adverse Event Protocol（不良事件处理）** | 若参与者感到焦虑/不适，提供停止选项与支持资源链接；数据安全事件（泄露）通知流程按机构政策执行 `[OWNER]` | 待机构政策适配 |
| **Cross-border Data Transfer（跨境数据）** | Prolific 数据处于英国/欧盟服务器；研究团队所在地 `[OWNER]`；需确认 GDPR/CCPA 适用性与数据处理协议（DPA） | `[NEEDS OWNER DECISION]`：机构 + 法律审查 |
| **IRB Submission Type** | 预计为 expedited review（最小风险 online 研究）；具体类别依机构规程 | `[NEEDS OWNER DECISION]` |
| **Protocol Version Binding** | IRB 批准文件需与 protocol 版本号 `prereg-v2.0`（本文档 Revision-2 冻结版）绑定；任何 protocol 修改须重新提交变更 | 待 freeze 后绑定 |

### 7.3 风险事件分级处理（预先声明）

| 级别 | 触发条件 | 处理动作 |
|---|---|---|
| L1（轻微） | 参与者文字反馈显示轻度挫败/焦虑 | 在平台界面显示退出提醒；记录事件 |
| L2（数据问题） | 数据批量丢失/平台故障 | 停止招募，联系平台，备用数据备份恢复 |
| L3（安全事件） | 数据泄露或未经授权访问 | 立即通知机构 DPO，按机构政策处置 `[OWNER]` |

---

## 8. 招募与补偿（更新，含 owner 决策占位）

- **平台**：Prolific（首选）`[NEEDS OWNER DECISION]`：最终平台批准
- **人群**：18+、英语流利、通过率 ≥95%、完成任务 ≥100
- **地域**：US/UK/CA/AU（最终由 owner+IRB 锁定 `[NEEDS OWNER DECISION]`）
- **时长**：30-40 分钟（**最终时长阈值由疲劳预试确认，见 §10.5** `[NEEDS OWNER DECISION]`）
- **补偿**：不低于 US$12/hour，预计 `US$7-9/人`（待 §10.5 预试后按实测时长调整）
- **AI Literacy 筛选**：招募后测量（协变量），不作为纳入标准，但报告分布

---

## 9. 预算区间（按新 N 与新时长重算）

| 项目 | 估算方式 | 区间（USD） |
|---|---|---:|
| 参与者报酬 | `N=480-570 × $7-9` | `3,360 - 5,130` |
| 平台服务费（Prolific） | 报酬的约 20%-35% | `672 - 1,796` |
| 研究运维（托管/存储/脚本） | 轻量 | `80 - 350` |
| API/算力 | 默认 0，预留缓冲 | `0 - 250` |
| **总计** |  | **`4,112 - 7,526`** |

---

## 10. 需 Owner 签字事项（Revision-2 更新，完整占位）

> 本节汇总所有 `[NEEDS OWNER DECISION]` 项，标注当前状态与所需行动。Owner 签字后相应条目更新为 `APPROVED/日期`。

| # | 事项 | 当前状态 | owner 所需行动 |
|---|---|---|---|
| 1 | **真人被试授权** | PENDING | 批准启动 IRB/伦理申请 + 正式招募 |
| 2 | **预算上限** | PENDING | 批准当前区间 `$4,112–$7,526`（见 §9）或指定上限 |
| 3 | **条件集确认** | PENDING | 确认 A/B/C 三组方案（含 Info-Matched 反例配对设计） |
| 4 | **答案键治理** | PENDING | 批准 24 题答案键、domain 来源、双标注流程（含解耦规程） |
| 5 | **Slider 基线合法性** | PENDING | 确认按 Huang & Lim 风格基线执行 |
| 6 | **心智模型探测** | PENDING | 确认新增 think-aloud/文本探测（时长上调） |
| 7 | **平台与地域** | PENDING | 确认 Prolific + US/UK/CA/AU 过滤 |
| 8 | **数据治理政策** | PENDING | 确认保存期限（建议 5 年）、开源边界（建议发表后去标识化 open data）、去标识化级别 |
| 9 | **投稿策略影响** | PENDING | 确认是否据此调整 CHI 2027 / IUI 时间窗 |
| 10 | **IRB 机构与审查路径** | PENDING | 指定 IRB 提交机构、审查类型（exempt/expedited） |
| 11 | **疲劳预试批准** | PENDING | 批准 n≈20 计时预试（见 §10.5），确认预试补偿来源 |
| 12 | **效应量 pilot 决策** | PENDING | 决定是否在 freeze 前补充 n≥10/组 pilot 以更新功效估算（R2-MAJOR-1 回退） |
| 13 | **跨境数据合规** | PENDING | 法律审查 Prolific 数据 DPA + 适用法规（GDPR/CCPA） |

---

## 11. 关键 judgment calls（Revision-2 更新）

1. 用 A vs B 作为机制主比较，A vs C 作为相邻设计比较。
2. 暂不纳入 No-console 第四组，以控制成本并优先关闭 BLOCKER；若 owner 要求可在二期扩展。
3. WAR 作为主 DV，同时强制报告 over/under reliance 分解。
4. H2 已升级为"可评分、可复核、可解释矩阵"——题目全文冻结，rubric 全文冻结。
5. Y_t 与 signal profile 完全解耦（先冻结答案键，再分配 profile），含 25% 反例配对用于非同义诊断。
6. 分析路径完全锁定（§6.6 分析锁定表），无临场判断余地。
7. 效应量 d=0.35 为主设计点，提供三档敏感性分析；经验文献引用已提供，pilot 更新为 owner 可选决策项。

## 10.5 疲劳预试计划（R2-MAJOR-2 应对，`[NEEDS OWNER DECISION]`）

> R2 指出 24 trials + 文本输入 + 归因题 + think-aloud 对在线样本时长估计过乐观（R2-MAJOR-2）。以下为疲劳预试计划框架；**是否在 freeze 前执行、预试预算来源**属于 owner 决策项。

**预试规模**：n≈20（每组约 7 人），英语母语/流利者，Prolific 或本地样本。
**测量目标**：
1. 中位完成时长（目标 ≤35 分钟；若 >40 分钟触发题量削减）；
2. 掉线率（目标 <15%；若 >20% 触发任务流程修改）；
3. 最后 6 题 vs 前 6 题的 WAR 变异性（注意力下滑诊断）；
4. H2 open-end 答案长度分布（检验后段参与者是否敷衍填写 <20 字）。

**回调规则（预先声明，预试后执行）**：
- 如中位时长 >40 分钟：将 H2-DV3 think-aloud 从第 6/12/18/24 题削减为第 12/24 题（保留 2 次）。
- 如掉线率 >20%：考虑将 trial 数从 24 削减到 18（调整 WAR 功效计算）。
- 回调后的最终题量/时长在 freeze box 写死，并在 freeze 前更新本文档。

**`[NEEDS OWNER DECISION]`**：
- 预试是否执行（建议 freeze 前执行）；
- 预试补偿来源（单独预算或从主研究预备金列支）；
- 若不执行预试，owner 需签字接受"30-40 分钟估计可能有 ±10 分钟不确定性"。

---

## 12. Freeze Box（待签字，仍未冻结）

> **Revision-2 状态**：Protocol 内容已达"可交 owner 签字"档次（BLOCKER-1 PARTIAL→CLOSED，BLOCKER-2 OPEN→CLOSED via 解耦规程，BLOCKER-3 PARTIAL→CLOSED，BLOCKER-4 PARTIAL→CLOSED，R2-BLOCKER-5 → CLOSED）。需 owner 批准后方可进入各产物的实际执行与冻结。

| 字段 | 状态 | 说明 |
|---|---|---|
| `owner_signoff` | **NO** | 见 §10 owner 事项清单 |
| `irb_or_ethics_clearance` | **NO** | 需 owner 指定机构后提交 |
| `protocol_frozen` | **NO** | owner 签字后冻结 Revision-2 版本 |
| `recruitment_authorized` | **NO** | 依赖 IRB 批准 |
| `budget_authorized_usd` | **PENDING** | owner 批准区间 `$4,112–$7,526` 后填写 |
| `answer_key_frozen` | **NO** | 待 Step B/D（标注与裁决）完成后冻结 |
| `signal_mapping_frozen` | **NO** | 待 answer_key 冻结后执行 Step C 分配 |
| `ui_parity_spec_frozen` | **NO（协议已定，待线框实现）** | A/B 字段映射表已写入 §2.4，需实现后确认 |
| `slider_ui_spec_frozen` | **NO（协议已定，待线框实现）** | C 条件 UI contract 已写入 §2.3，需实现后确认 |
| `h2_item_bank_frozen` | **NO（全文已定）** | §4.2/§4.3 完整题目已写入文档，需 owner 审核确认冻结 |
| `h2_scoring_manual_frozen` | **NO** | 需单独产出 `h2_scoring_manual_v1.md` 并完成编码员训练演练 |
| `analysis_lock_table_frozen` | **YES（§6.6 已写入）** | 分析锁定表已完整写入，待 owner 确认后与 protocol 一同冻结 |
| `fatigue_pretest_done` | **NO** | 见 §10.5 `[NEEDS OWNER DECISION]` |
| `data_collection_start` | **BLOCKED (owner-signature-pending)** | |

---

## 13. Revision-2 修订记录与残留问题汇总

### 13.1 本次修订关闭/改进项

| 编号 | 原状态 | 本次状态 | 关键动作 |
|---|---|---|---|
| R2-BLOCKER-5 | OPEN（新增） | **CLOSED（protocol层）** | Y_t 先于 signal profile 独立确定；加入 25% 反例配对；预声明 phi 系数与 WAR 分解亚组分析 |
| B1（信息量混淆） | PARTIAL | **CLOSED（protocol层）** | §2.4 完整字段映射表 + 视觉等价约束 + B 条件操纵检查（Q-MC1/Q-MC2） |
| B2（答案键可复现性） | OPEN | **CLOSED（规程层，产物待执行）** | Step B 先于 Step C 冻结；反例配对规则明确；双标注流程更新；freeze 产物清单完整 |
| B3（Slider 稻草人） | PARTIAL | **CLOSED（protocol层）** | §2.3 完整 UI contract（字段表/状态机/交互规格）；稻草人边界声明已写入 |
| B4（H2 操作化） | PARTIAL | **CLOSED（题目全文已写入）** | §4.2 全 8 题题干+键+干扰项；§4.3 全 6 题+rubric+anchor 示例；H1×H2 解释矩阵已更新 |
| R2-MAJOR-3（分析自由度） | OPEN | **CLOSED** | §6.6 分析锁定表：每假设→唯一模型/对比/校正/缺失/回退 |
| R2-MAJOR-4（IRB 完整性） | OPEN | **PARTIAL** | §7.2 可提交材料清单大纲；机构/审查路径为 owner 决策项 |
| R2-MAJOR-1（功效依据） | OPEN | **PARTIAL** | §6.7 三档敏感性分析 + 近邻文献引用；pilot 更新为 owner 可选 |
| R2-MAJOR-2（疲劳） | OPEN | **PARTIAL（owner 决策项）** | §10.5 疲劳预试计划框架 + 回调规则；是否执行为 owner 决策 |

### 13.2 仍需 Owner 决策的事项（不在本次文档层面关闭）

1. **IRB 机构指定与提交**（§7.2、§10 #10）
2. **预算批准**（§9、§10 #2）
3. **平台/地域/筛选确认**（§8、§10 #7）
4. **疲劳预试执行决策**（§10.5、§10 #11）
5. **效应量 pilot 执行决策**（§6.7、§10 #12）
6. **Venue 时间窗确认**（§10 #9）
7. **数据治理政策细节**（§7.2、§10 #8）
8. **跨境数据合规审查**（§7.2、§10 #13）

### 13.3 本轮未完全关闭的残留局限

1. **R2-MAJOR-1 PARTIAL**：功效经验依据为文献近邻引用，非直接来自本 task × DV 的 pilot 数据。Owner 可决定在 freeze 前补充 pilot（最强路径）或接受文献近邻估算（可接受路径）。
2. **R2-MAJOR-2 PARTIAL**：时长估计 30-40 分钟，±10 分钟不确定性，疲劳预试将解决但需 owner 授权。
3. **R2-MAJOR-4 PARTIAL**：IRB 材料的机构适配（consent/debrief 模板）依赖 owner 指定机构。
4. **H2 item bank 的 pilot 验证**：题目全文已冻结（文档层），但 floor/ceiling 效应与信度演练（R2-QUESTION-1）需在招募前执行——owner 需决定是否纳入疲劳预试一并执行。
5. **反例配对的生态效度**：6 道反例题（Y_t=1+NONTRANSFER、Y_t=0+PASS）在真实使用中出现频率未知；此为研究设计的刻意受控选择，已在 §3.3 示例中说明认知预期。
