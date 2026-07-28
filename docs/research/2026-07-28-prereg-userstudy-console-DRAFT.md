# 受控用户研究预注册草案（Console v2）

- **状态**：`DRAFT / OWNER-SIGNATURE-PENDING`
- **日期**：2026-07-28
- **Owner gate**：未签字前**不得**启动 IRB、招募、真人数据采集、付费平台投放。
- **定位**：为 C3 建立独立证据路径（从“设计含义”升级为“有用户证据的 HCI 贡献”），不改写任何冻结的 C1/C2/E-0003..E-0010 记录。

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

## 2.3 Condition C（Slider）可复现实 UI 规格（关闭 BLOCKER-3）

**交互对象**
1. 每个 trial 显示 1 个“Latent Control”滑块（范围 `-2 ... +2`，步长 0.5，默认 0）。
2. 滑块绑定当前 vignette 的主轴（deliberation/skepticism/uncertainty/focus 四轴之一；主轴在刺激表中预先固定）。
3. 参与者可在提交前最多调整 3 次；每次调整即时刷新“AI 建议文本预览”。

**显示元素**
1. 场景问题（domain vignette）
2. AI 建议文本（当前滑块值下）
3. 滑块值与轴名（如 `uncertainty-axis: +1.0`）
4. 采纳决策按钮（rely / not rely）

**明确不显示**
- READ / TRANSFER / PROMPT-CEILING / CALIBRATION-HARM / EVIDENCE-TIER；
- 任意 pass/fail/warning 判词；
- 任意“边界解释文本”。

**现实可比性论证**
- 该基线对应已发表的 feature-steering GUI 范式（Huang & Lim），属于“非专家可操作 latent 控件”而非稻草人。
- 研究问题不是“Slider 是否无效”，而是“边界仪器组织是否超出 slider-only 控件价值”。

---

## 3. 刺激材料、答案键与任务（重点修订，关闭 BLOCKER-2）

## 3.1 信号来源（artifact-derived，不改冻结）

界面数值字段仅取自冻结 artifact：

- `results/c2b_adjudication_hf_2026-07-24/c2b_adjudication_results.json`
- `results/arm_full/arm_matrix_summary.json`
- `results/flagship_powered/summary.md`
- `results/flagship_powered/behavior/flagship_l0_results.json`
- `results/flagship_powered/read/flagship_read_results.json`
- `results/psr_qwen_primary/psr_c2b_adjudication_results.json`
- `docs/paper/figure-manifests/console-ui-contract.yaml`

## 3.2 24 个 vignette 的 ground-truth 答案键构造规程（freeze 前必须完成）

**目标**：给每个 trial 预先冻结 `Y_t ∈ {0,1}`（AI 建议正确/错误），用于 WAR。

### Step A：domain 事实源固定（客观可核查）
六域各 4 题（共 24 题），每题绑定一个可引用答案源：

1. consumer：官方产品政策/公开服务条款
2. finance：基础个人理财规范（非个股预测；来源如 CFPB/IRS 通用规则）
3. health：公开患者教育级指南（CDC/WHO/NHS）
4. legal：公开合规流程与权利说明（非法律意见；政府门户）
5. privacy：GDPR/CCPA 明确条款或监管 FAQ
6. education：公开学术诚信与课程政策

> 所有题面限制为“客观可判定、低争议、低风险”微决策，不做高风险个体化建议。

### Step B：题目与建议文本生成
每题形成：
1. `question_stem`
2. `gold_action`（唯一正确）
3. `ai_suggestion_text`
4. `Y_t`（是否与 `gold_action` 一致）
5. `rationale_key`（1-2 句判定依据）

每个 domain 4 题中固定 2 题 `Y_t=1`，2 题 `Y_t=0`，总计 12/12 平衡。

### Step C：ML 信号到 vignette 的映射规则（预先固定）
为每题绑定一个 signal profile（取自冻结 artifact 的离散模板）：

1. **Profile-PASS**：READ_HOLDS + TRANSFER_PASS + 无 calibration-harm  
2. **Profile-NONTRANSFER**：READ_HOLDS + NON_TRANSFER + 无 harm  
3. **Profile-HARM**：READ_HOLDS + NON_TRANSFER + calibration-harm(red)  
4. **Profile-ROBUST-NONTRANSFER**：PSR 增强后仍 NON_TRANSFER

映射约束：
1. `Y_t=1` 题仅可绑定 Profile-PASS。
2. `Y_t=0` 题仅可绑定 NONTRANSFER/HARM/ROBUST-NONTRANSFER。
3. 各 profile 在 24 题中按预设配额出现，避免单一模式主导。

> 该映射是“受控实验中的机制化信号-标签耦合”，用于测试用户是否按边界信号校准 reliance；不声称外部世界天然存在该一一对应。

### Step D：双人标注与裁决
1. 两名独立标注者仅基于 domain 来源与 gold_action 标注 `Y_t`；不可见实验条件。
2. 一致性指标：`Krippendorff α >= 0.80`（二值正确性）。
3. 分歧由第三人裁决，形成冻结答案键 `vignette_answer_key_v1.yaml`。

### Step E：freeze 产物
在招募前必须冻结并版本化：
1. `vignette_bank_v1.yaml`（24 题全文）
2. `vignette_answer_key_v1.yaml`
3. `signal_mapping_table_v1.csv`
4. `annotation_log_v1.md`（含 α 与裁决记录）

## 3.3 示例（构造可复现性示例）

**示例 trial（health）**
- question_stem: “成人发热 38.5°C 持续 24h，是否应立即自行联合使用两种抗生素？”
- gold_action: “不应自行联合用药，应先咨询专业医疗渠道。”
- ai_suggestion_text（错误版）: “可先自行联合抗生素，通常更快见效。”
- `Y_t=0`
- signal profile: Profile-HARM（READ_HOLDS + NON_TRANSFER + calibration-harm 红）
- rationale_key: 与 CDC/NHS 患者教育冲突，属于不安全建议。

## 3.4 参与者任务

每个 trial：
1. 阅读场景 + AI 建议 + 条件界面（A/B/C）。
2. 做 rely / not rely 决策。
3. 写 1 句理由（最低 20 字符）。
4. 回答 1 个归因/理解题（从 item bank 轮换抽取）。

---

## 4. 测量与操作化（修订，关闭 BLOCKER-4）

## 4.1 主 DV：Calibrated Reliance（WAR）

令 `R_it ∈ {0,1}` 表示是否采纳；`Y_t ∈ {0,1}` 表示 AI 建议是否正确。

- 若 `Y_t=1`：`AR_it = R_it`
- 若 `Y_t=0`：`AR_it = 1 - R_it`
- `WAR_i = mean_t(AR_it)`，范围 `[0,1]`

并报告：
- `OverReliance = P(R=1 | Y=0)`（越低越好）
- `UnderReliance = P(R=0 | Y=1)`（越低越好）

## 4.2 H2-DV1：错误归因准确度（8 题，应用层）

每位参与者完成 8 题场景化归因题（非记忆题），题型为 4 选 1 或 2 选 1：
1. “若 AI 建议与信号冲突，最应依据哪类信息决策？”
2. “该案例主要失败来源更可能是 transfer fail 还是 prompt 表述不足？”
3. “当 read holds 但 transfer fail 时，最合理动作是？”
4. “calibration-harm 红警示应触发何种决策调整？”
5. “哪种情形最支持继续依赖 AI？”
6. “PSR 强化仍 non-transfer 的含义是什么？”
7. “同样数值但不同标签组织，哪种解释更稳健？”
8. “冲突情景下，哪项证据优先级最高？”

评分：
- 每题 1 分，总分 0-8；线性归一到 0-100 报告。
- 题目在 freeze 文档逐题公开（含正确键与干扰项来源）。

## 4.3 H2-DV2：prompt↔latent 冲突理解测验（6 题，机制层）

6 个短案例题，要求解释“文本意图”和“latent 介入”冲突时的可预期后果。  
题型：2 题多选 + 4 题短答（40-80 字）。

短答评分 rubric（0/1/2）：
1. **0 分**：仅复述表面文本或无关回答。
2. **1 分**：识别到冲突存在，但无法指出边界含义。
3. **2 分**：明确指出“文本可读意图”与“latent 行为转移证据”可不一致，并给出合理决策策略。

编码：
- 双盲双编码员；
- 目标一致性 `Krippendorff α >= 0.80`；
- 低于阈值则触发 rubric 修订后重编码（在 freeze 前完成）。

## 4.4 H2-DV3：心智模型探测（采纳 R1 建议）

加入轻量 process measure（不延长过多时长）：

1. **Micro think-aloud probe（trial 内）**  
   在第 6/12/18/24 题后追加 1 问：“你刚才主要依据了什么信息做决定？”（40-120 字）。

2. **Post-task mental-model probe（任务后）**  
   两问自由文本：  
   - Q1: “`transfer verdict`（或等价中性字段）在你理解中表示什么？”  
   - Q2: “当 prompt 要求与 latent 信号冲突时，你认为谁更可信？为什么？”

编码维度（每维 0/1）：
1. 是否区分 prompt 通道与 latent 通道；
2. 是否提到 non-transfer/校准风险；
3. 是否给出冲突下的决策规则（而非仅凭直觉）。

总分 0-3，作为 H2 机制证据与解释变量。

## 4.5 操纵检查（manipulation check）

1. “你是否注意到界面里关于建议可靠性的结构化提示？”（是/否）
2. “请用一句话解释你看到的关键提示含义。”（自由文本，双编码）

---

## 5. 样本量与功效分析（按新增条件重算）

## 5.1 主比较与检验序列

为避免因多重主比较导致过高样本，采用预注册 gatekeeping：
1. **主检验 H1**：A vs B（机制关键比较）
2. 若 H1 成立，再检验 **H1b**：A vs C（设计相邻比较）

## 5.2 参数与 N

- 目标：`power=0.80`, `alpha=0.05`（双侧）
- 目标效应：`d=0.35`（小到中等）
- 两组比较所需可分析样本约 `~130/组`

考虑质量剔除（约 12%-15%）与三组并行：
- **可分析目标**：`N_analyzable = 450`（每组 150）
- **招募目标**：`N_recruit = 510-540`（每组约 170-180）
- **可接受区间**：`N_recruit = 480-570`
- **停表下限**：每组可分析样本不少于 130；不足则补招。

---

## 6. 预注册分析计划（修订）

## 6.1 H1 主检验（预锁定）

主模型固定为 **GLMM**（不再留 GEE 二选一自由度）：

`AR ~ Condition + AI_Literacy + (1 | Participant) + (1 | Item)`

- 主对比：A vs B
- 报告：OR、95% CI、p 值、边际效应
- 敏感性分析：预声明 GEE 复核方向一致性（非主判定）

## 6.2 H1b 与 H2

- H1b：A vs C（WAR）
- H2：A vs B、A vs C 于归因准确度、冲突理解分、心智模型分
- H2 开放文本项均报告编码一致性（Krippendorff α）

## 6.3 多重比较

- Confirmatory：H1 为第一关；H1b/H2 为后续关，Holm 校正控制 FWER 0.05。
- Exploratory：主观信任、NASA-TLX 等用 BH-FDR `q=0.05`。

## 6.4 排除规则（预冻结）

1. 未完成 consent。
2. 重复账号/机器人。
3. 注意力检查 4 题中错 `>=2`。
4. 完成时长低于绝对阈值（预设 `<8` 分钟；由小规模可用性预试定稿后写入 freeze）。
5. 关键 DV 缺失。

禁止按结果方向删样。

## 6.5 结果模式解释矩阵（H1 × H2）

| 模式 | 解释 | 对 C3 影响 |
|---|---|---|
| H1 显著，H2 显著 | 既提升 reliance，又提升边界理解 | 支持 C3 机制主张 |
| H1 显著，H2 不显著 | 可能是效率/谨慎效应，而非机制理解 | 仅支持“行为收益”，弱化机制 claim |
| H1 不显著，H2 显著 | 学到概念但未转化为行为 | 支持教学/解释价值，不支持 reliance 主张 |
| H1 不显著，H2 不显著 | 无证据支持 | C3 用户研究线需降级或转向 |

---

## 7. IRB / 伦理 / 隐私

1. 知情同意：说明将评估 AI 建议并做决策判断，可随时退出。
2. 最小风险：全部为低风险 vignette，不采集真实个体医疗/法律/投资决定。
3. 轻度掩蔽：不告知具体条件编号与“哪组是理论组”；事后 debrief 说明。
4. 数据最小化：只收行为日志、简短文本、最少人口统计、AI 使用经验。
5. 隐私：去标识化、加密存储、按政策删除。
6. 刺激来源：冻结 artifact + 公开可核查 domain 来源，不调用私有画像接口。

---

## 8. 招募与补偿（更新）

- 平台：Prolific（首选）
- 人群：18+、英语流利、通过率 >=95%、完成任务 >=100
- 地域：US/UK/CA/AU（最终由 owner+IRB 锁定）
- 时长：30-40 分钟（加入心智模型探测后上调）
- 补偿：不低于 US$12/hour，预计 `US$7-9/人`

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

## 10. 需 Owner 签字事项（更新）

1. **真人被试授权**：是否启动 IRB/伦理与正式招募。
2. **预算上限**：是否批准新预算区间（`$4,112-$7,526`）。
3. **条件集确认**：是否批准 A/B/C（三组，含新增 Info-Matched）。
4. **答案键治理**：24 题答案键、domain 来源、双标注流程是否接受。
5. **Slider 基线合法性**：是否按 Huang & Lim 风格基线执行。
6. **心智模型探测**：是否同意新增 think-aloud/文本探测（时长上调）。
7. **平台与样本过滤**：地域、补偿、AI literacy 协变量采集范围。
8. **数据治理政策**：保存期限、开源边界、去标识化级别。
9. **投稿策略影响**：是否据此调整 CHI/IUI 时间窗。

---

## 11. 关键 judgment calls（当前版本）

1. 用 A vs B 作为机制主比较，A vs C 作为相邻设计比较。
2. 暂不扩第四组（No-console），先关闭 BLOCKER 并控制成本。
3. WAR 作为主 DV，同时强制报告 over/under reliance 分解。
4. 把 H2 从“命名”升级为“可评分、可复核、可解释矩阵”。
5. 通过 process measure（micro think-aloud + mental-model probe）直接测 non-surjection 理解，而非仅测行为结果。

---

## 12. Freeze Box（待签字，仍未冻结）

- owner_signoff: **NO**
- irb_or_ethics_clearance: **NO**
- protocol_frozen: **NO**
- recruitment_authorized: **NO**
- budget_authorized_usd: **N/A**
- answer_key_frozen: **NO**
- slider_ui_spec_frozen: **NO**
- h2_item_bank_frozen: **NO**
- data_collection_start: **BLOCKED (owner-signature-pending)**
