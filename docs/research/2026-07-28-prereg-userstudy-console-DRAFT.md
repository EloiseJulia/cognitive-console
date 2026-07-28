# 受控用户研究预注册草案（Console v2）

- **状态**：`DRAFT / OWNER-SIGNATURE-PENDING`
- **日期**：2026-07-28
- **Owner gate**：未签字前**不得**启动 IRB、招募、真人数据采集、付费平台投放。
- **定位**：为 C3 建立独立证据路径（从“设计含义”升级为“有用户证据的 HCI 贡献”），不改写任何冻结的 C1/C2/E-0003..E-0010 记录。

---

## 0. 研究范围与红线

1. 本文档仅定义 protocol 与分析计划，不包含任何真人数据。
2. 本研究是**新证据线**，不回写/覆盖既有 frozen artifacts 与判定。
3. 研究目标 venue 以 **IUI/CHI** 为主，但是否影响当前投稿路径属于 owner 决策项。

---

## 1. 研究问题与可证伪假设

### RQ
当用户面对同一组 AI 建议时，暴露五信号边界信息的 **console v2**，是否比“latent-control-slider”基线更能帮助用户形成**校准信赖**（calibrated reliance），并更好理解 prompt↔latent 冲突来源？

### H1（主假设，主 DV）
相较于 **latent-control-slider baseline**，**console v2** 将显著提升 calibrated reliance。

- **方向性**：Console v2 > Slider。
- **主 DV**：`WAR`（Weighted Appropriateness of Reliance），定义见 §5。
- **可证伪条件**：
  - 预注册主检验中 Console−Slider 效应 `<= 0`，或
  - 95% CI 跨 0 且未达到显著性阈值，或
  - 出现反向显著（Console 更差）。

### H2（次假设，次 DV）
相较于 Slider，Console v2 将提升用户对**错误归因**与**prompt↔latent 冲突理解**。

- **方向性**：Console v2 > Slider。
- **次 DV**：归因准确度、冲突理解测验分数（见 §5）。
- **可证伪条件**：对应比较无提升或反向提升。

---

## 2. 条件与实验设计

## 2.1 条件（至少两组，含可选第三组）

1. **A: Boundary-Instrument Console v2**  
   显示五信号：READ status、TRANSFER verdict、prompt-ceiling comparison、calibration-harm warning、evidence tier。
2. **B: Latent-Control-Slider Baseline**  
   提供“latent 控制强度/方向”滑块与结果视图，但不暴露五信号边界信息（不显示 transfer verdict / calibration harm / evidence tier）。
3. **C: No-console 对照（可选，建议保留）**  
   仅看 AI 建议文本（无 latent 控件、无五信号），用于估计“任何界面提示”相对纯文本的增益。

## 2.2 设计选择

- **主设计**：`between-subjects`（A/B/C 三组随机分配，1:1:1）。
- **理由**：避免学习迁移与污染（参与者一旦见过五信号，难以回到“无边界信息”状态）。
- **试次内平衡**：每位参与者都看正确/错误 AI 建议混合 trials（见 §4），顺序随机并按 domain 分块打散。
- **随机化**：平台随机分组 + 预先固定随机种子生成 trial order 列表。

---

## 3. 刺激材料与任务

## 3.1 刺激来源（artifact-derived，冻结产物）

界面卡片与数值仅取自 frozen artifact：

- `results/c2b_adjudication_hf_2026-07-24/c2b_adjudication_results.json`
- `results/arm_full/arm_matrix_summary.json`
- `results/flagship_powered/summary.md`
- `results/flagship_powered/behavior/flagship_l0_results.json`
- `results/flagship_powered/read/flagship_read_results.json`
- `results/psr_qwen_primary/psr_c2b_adjudication_results.json`
- `docs/paper/figure-manifests/console-ui-contract.yaml`

## 3.2 关键 vignette 原型（预注册固定）

1. **Uncertainty card（高风险边界）**：READ 可见但 TRANSFER fail，且 calibration-harm 红色警示（含 2×2 复现语义）。
2. **Deliberation card（可读但不转移）**：READ 可见，TRANSFER fail/不显著。
3. **Social card（LEGIBLE but NOT CONTROLLABLE）**：READ_HOLDS（token-blind AUC≈0.954）但行为对比为 null（B−A M1≈0.0015）。
4. **PSR robustness marker**：强调“方法强度增强后仍未通过转移判定”。

## 3.3 用户任务（依赖/拒绝 AI 建议）

每个 trial 给定：问题场景 + AI 建议 +（按条件显示界面信息）。

参与者需要：
1. 是否采纳 AI 建议（rely / not rely）。
2. 给出简短理由。
3. 回答归因题（为什么该建议应/不应被采纳）。

## 3.4 正误 trial 结构（用于 reliance calibration）

- 每位参与者 `24` 个 trial：`12` 个 AI-正确 + `12` 个 AI-错误（先验标注冻结）。
- 覆盖 consumer/finance/health/legal/privacy/education 六类任务。
- 正确性标签由预先冻结的答案键与规范裁决流程生成（双人标注+分歧裁决，详见 freeze checklist）。

---

## 4. 测量与操作化

## 4.1 主 DV：Calibrated Reliance（WAR）

令 `R_it ∈ {0,1}` 表示参与者 `i` 在 trial `t` 是否采纳 AI 建议；`Y_t ∈ {0,1}` 表示 AI 建议是否正确。

定义 trial-level appropriateness：

- 若 `Y_t=1`（AI 正确），应采纳：`AR_it = R_it`
- 若 `Y_t=0`（AI 错误），应拒绝：`AR_it = 1 - R_it`

定义参与者层主指标：

- `WAR_i = mean_t(AR_it)`，范围 `[0,1]`，越高越好。

并报告分解指标：

- `OverReliance = P(R=1 | Y=0)`（越低越好）
- `UnderReliance = P(R=0 | Y=1)`（越低越好）

## 4.2 次 DV

1. **错误归因准确度**：多选/单选题是否正确识别失败来源（prompt ceiling、transfer fail、calibration-harm 等）。
2. **prompt↔latent 冲突理解**：场景化理解题总分（0-100）。
3. **主观信任与可控性感知**：Likert 量表（预定义条目）。
4. **可选 NASA-TLX**：认知负荷（探索性，不作为主结论 gate）。

---

## 5. 样本量与功效分析（预注册）

- **比较主轴**：A( Console v2 ) vs B( Slider )。
- **统计目标**：`power=0.80`，`alpha=0.05`（双侧），最小可解释效应定为小到中等（`d≈0.35-0.40`）。
- **估算**：
  - 两组比较在 `d=0.35` 时约需 `~128/组`；
  - `d=0.40` 时约需 `~98/组`。
- **预注册目标 N（含第三组与剔除冗余）**：
  - **主方案（三组）**：`N_target=360`（每组 120）。
  - **可接受区间**：`N=300-420`（按预算与可招募性在 owner 批准后锁定）。
- **剔除后可分析样本下限**：每组不少于 `100`；不足则补招至下限。

---

## 6. 预注册分析计划

## 6.1 主检验（H1）

- **模型**：trial-level 混合效应逻辑回归（或等价 GEE，二选一预先锁定）  
  `AR ~ Condition + (1|Participant) + (1|Item)`
- **主对比**：A vs B（Console vs Slider）。
- **判定**：效应方向为正且通过显著性阈值，报告 OR、95% CI、p 值与标准化效应量。

## 6.2 次检验（H2）

- 归因准确度、冲突理解分数：A vs B（以及 A vs C 若含 C）。
- 信任量表/NASA-TLX：报告为次级或探索性结果，不反向升级为主结论。

## 6.3 多重比较校正

- **Family-1（确认性）**：H1 与 H2 主比较，采用 Holm-Bonferroni（FWER 0.05）。
- **Family-2（探索性）**：额外量表/子维度，采用 BH-FDR `q=0.05` 并明确标注 exploratory。

## 6.4 排除规则（预先冻结）

剔除仅基于以下客观规则：

1. 未完成知情同意。
2. 重复参与/机器人/非目标地域账号（按平台防作弊规则）。
3. 注意力检查失败超过阈值（预设 2 题中错 ≥2）。
4. 完成时长低于预设下界（如 `<` 中位数 1/3）且伴随低质量文本。
5. 关键 DV 缺失（因中途退出）。

**禁止**按结果方向进行主观删样。

## 6.5 停表规则

- 固定样本设计；不做中途显著性窥视与可选停止。
- 仅允许质量监控（完成率、设备异常）；不看条件效应。
- 达到目标可分析样本即停。

---

## 7. IRB / 伦理 / 隐私

1. **知情同意**：明确说明将看到 AI 建议并做决策判断，随时可退出。
2. **最小风险**：低风险任务域；避免真实高风险个体医疗/法律/投资决策。
3. **无未披露欺骗**：不使用对参与者有实质影响的隐瞒式欺骗；若需轻度掩蔽研究假设，须在 consent 文案与 debrief 中合规说明。
4. **数据最小化**：只收研究所需行为数据与最少人口统计；不采集敏感身份信息。
5. **隐私与存储**：去标识化、加密存储、仅研究团队访问、按政策定期删除。
6. **模型边界**：使用白盒开源模型与冻结 artifact 生成刺激，不调用私有闭源个人画像接口。

---

## 8. 招募与补偿

- **平台**：Prolific（首选）。
- **人群**：18+，英语流利，历史通过率 ≥95%，完成任务数 ≥100。
- **地域**：英语主导地区（如 US/UK/CA/AU，最终由 owner 与 IRB 文案锁定）。
- **时长**：约 25-35 分钟。
- **补偿目标**：按不低于 US$12/hour 支付；预计 `US$6-8/人`（含基础奖励，不含平台费）。

---

## 9. 预算区间（草案）

| 项目 | 估算方式 | 区间（USD） |
|---|---|---:|
| 参与者报酬 | `N=300-420 × $6-8` | `1,800 - 3,360` |
| 平台服务费（Prolific） | 按报酬的约 20%-35% | `360 - 1,176` |
| 研究运维（托管/存储/脚本） | 轻量 | `50 - 300` |
| API/算力 | 刺激基于冻结 artifact，默认 0；预留缓冲 | `0 - 200` |
| **总计** |  | **`2,210 - 5,036`** |

> 若缩为两组（A/B）且 `N≈260-320`，总预算可进一步下降；若增加预试与复现实验，预算上沿上移。

---

## 10. 需 Owner 签字事项（执行前必需）

1. **真人被试授权**：是否启动 IRB/伦理流程与正式招募。
2. **预算上限**：本研究可用总预算与超支容忍度。
3. **平台与样本人群**：Prolific 过滤条件、地域范围、补偿标准。
4. **是否含第三组（No-console）**：科学增益 vs 成本取舍。
5. **是否影响当前投稿策略**：IUI/CHI 路线与时间窗口是否因此调整。
6. **数据治理政策**：数据保存期限、开放数据级别、可复现材料公开边界。

---

## 11. 关键设计 judgment calls（供 Manager/Owner 决策）

1. **Between-subjects 而非 within-subjects**：优先避免“看过五信号后不可逆学习效应”。
2. **保留 No-console 第三组**：增加可解释性（界面提示增益分解），但成本上升约 30%-50%。
3. **主 DV 选 WAR**：直接度量“该信时信、该疑时疑”，避免仅用主观 trust 分数。
4. **刺激完全 artifact-derived**：保障 lineage 与可审计性，避免在线生成引入不可控噪音。
5. **先固定 correctness answer key 再招募**：避免后验改标签造成研究者自由度。

---

## 12. Freeze Box（待签字）

- owner_signoff: **NO**
- irb_or_ethics_clearance: **NO**
- protocol_frozen: **NO**
- recruitment_authorized: **NO**
- budget_authorized_usd: **N/A**
- data_collection_start: **BLOCKED (owner-signature-pending)**

