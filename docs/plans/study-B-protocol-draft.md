# Study B —— 可预注册协议草案（PREREGISTRABLE PROTOCOL DRAFT）

> **状态：🔴 DRAFT / 未冻结 / 未招募 / 无数据。** 采集真实数据前，必须先：
> ①伦理/IRB 批准 + 导师签字（owner 状态：**will_get**，尚未取得）；②知情同意定稿；
> ③本协议冻结 + 预注册 MDE；④独立 audit；⑤数据隐私/保存-删除方案。
> owner 已授权把 B 纳入 Results（confirmatory，D-0127）；样本固定 **10+10**。
>
> **不变量：** V3 gate 逻辑指纹 / 冻结答案 / 材料 v11.3 不动；B 独立工具，V3 门槛按引用嵌入。

---

## 0. 诚实的样本量现实（决定本协议的主检验选择）

固定 N=10+10。功效核算（α=.05 双侧，power=.80）：
- 组间（专家 vs 普通人）：MDE d≈**1.32**（超大）；d=0.5 时功效仅 0.19，d=0.8 仅 0.40。
- 组内（20 对）：MDE dz≈**0.66**（中大，可行）。
- **人群×对照交互**：需约 4× 样本（≈每组 30–40）；N=20 **不足以** confirmatory 检验交互。

**结论（D-0127 诚实边界）：** 主 confirmatory 检验一律放在**组内**；**人群差异/交互降为 secondary/exploratory**，报效应量 + CI，明写 underpowered。不把 n=10/10 的交互当核心 Claim。

---

## 1. 研究问题与人群

「滑块好不好」人群相对：便利（写不出强 prompt 的人）vs. 有保证的增量控制（能写出强 prompt 的人）。average/best-prompt 两对照 = 两人群真实备选的操作化。

**人群划分（客观，非自报）——prompting proficiency：**
- 入组前做 **prompt-writing 探针**：给定标准化目标，参与者自己写一条 prompt；按预注册 rubric 客观评分（可加盲评双人一致性 κ）。
- **Proficient 层** = 探针分达预注册阈值（能写出接近 best-prompt 质量的指令）；**Non-proficient 层** = 未达阈值。
- 目标每层 10 人。广义 AI 熟练度（使用频率/调参/懂 latent 控制）**只作协变量问卷**，不定义组。
- 论文人群定义同步收紧为 "someone who can write a strong prompt for the task"。

> 待定（§8）：探针任务与 rubric 细则、阈值定法（预设 cutoff / 校准锚点）、是否双盲评分。

---

## 2. 设计

**混合设计**：proficiency 层（between，2）× 对照条件（within）。
- 每位参与者在**匹配任务**上经历两/三种条件（顺序**抵消**）：
  1. **Slider 条件**：用 latent 滑块达成目标。
  2. **Own-prompt 条件**：自己写 prompt 达成同类目标（= 其真实备选；对 average-prompt 分布的每被试一次实现）。
  3. （可选）**Given-comparator 条件**：给定 best/average-prompt 产物作参照，桥接模型侧。
- 任务集配对、反事实平衡；条件与任务顺序用拉丁方/随机抵消。

---

## 3. 材料

- 沿用/改编 V3 的**示意/虚构**场景族（材料 v11.3 不改；如需新任务材料，另起独立材料集，不污染 V3）。
- 目标任务需可同时用「滑块」与「写 prompt」两条路完成，且有可评的 outcome。
- 全部材料标注 fictional/illustrative。

---

## 4. 测量（两轴；facet 名与论文对齐）

**便利轴：effort / accessibility / discoverability + willingness-to-use**
- Effort：客观（完成时间、操作步数、修改/迭代次数）+ 主观（简版 NASA-TLX / Likert）。
- Accessibility：无需自己 craft prompt 也能达成目标的完成率。
- Discoverability：能否看懂控件在做什么、怎么用。
- Willingness-to-use：滑块 vs 自己写 prompt 的选择与理由。

**有保证的增量控制轴（写作 session 已定：不塌进对象层 δ gate）**
- **主要 = 用户在环任务表现（+ effort / reliance）**：真实用户带自己 prompt + 滑块能否拿到更好结果 / 更省力 / 更校准依赖。
- **可选 secondary（桥接 0/12）**：同一 steer-vs-prompt 的对象层对比。
- **尺度警告：δ=0.05 是对象尺度 release bar，不照搬**；本协议按 power 预注册自己的 MDE（组内 dz）。

> 判分/正确答案边界同 V3：任何正确答案/门槛判定只在 owner 端离线判分，绝不进参与者端 payload/DOM/ARIA/export。

---

## 5. 假设（中性、可证伪、无预设方向；主检验组内）

**主（confirmatory，组内，powered dz≈0.66）：**
- **H1（增量控制，proficient 层内）**：proficient 用户的「滑块 − 自己 prompt」在用户在环 quality 指标上的差是否为零 / 未达实质阈值。H0：差=0。*（对应模型侧 0/12 的真人版。）*
- **H2（便利，non-proficient 层内）**：non-proficient 用户的「滑块 − 真实备选」在 effort/accessibility 上是否更省力/可及。H0：无差异。

**次（exploratory，underpowered，仅报效应量+CI）：**
- **H3（人群×对照交互）**：上述效应是否随 proficiency 层不同。**明写 N=20 对交互 underpowered**，不作 confirmatory 主张。
- **H4（可应用性，V3 门槛模块）**：两层应用对照约束门槛的正确率是否不同。

> owner 口述的「专家因不满足X觉得不好用、普通人觉得方便但写不出好 prompt」仅作可能情形，不写死为待证实结论。

---

## 6. 分析计划

- **主分析**：H1/H2 组内配对检验（或等价混合模型的组内对比）；报 dz + 95% CI + 精确 p。
- **次分析**：H3 交互项估计 + CI，标注 underpowered；H4 应用性描述 + CI。
- **协变量**：广义 AI 熟练度问卷、任务/条件顺序。
- **排除规则（预注册）**：注意力检查失败、探针无效作答、未完成、明显作弊/AI 代填等 → 预先写死。
- **随机化/seed**：条件与任务顺序随机的 seed 预注册；分层入组规则预注册。
- **多重比较**：主假设仅 H1/H2 两个，预注册校正法。
- **停止规则**：固定 N=20，不做数据依赖的加样（避免 optional stopping）。
- **混合方法**：报每参与者级数据 + 探针分 + 结构化/开放反思的质性归纳（CHI 重视）。

---

## 7. 诚实边界与 gate

- 🔴 **采数据前**必须：伦理/IRB + 导师签字（未取得）、知情同意定稿、协议冻结 + MDE、独立 audit、隐私/保存-删除方案。owner「自己招募」**不豁免**上述任何一项。
- 材料示意/虚构；数据 = 预注册小样本研究；**主张范围严格按 §0/§5**：两个组内强结论可站住，人群交互只作 exploratory。
- 不与论文模型证据合并计算；V3 指纹/答案/材料不动。
- 论文口径：便利/增量控制评价为 confirmatory-but-small（预注册、报效应量+CI），交互 underpowered 明示；保留「本文不作超出证据的 benefit 结论」事实底线。

---

## 8. 仍待 owner 拍板 / 定稿的细则

1. **claim 框架确认**：接受 §0/§5 的「组内主检验 + 交互降级」诚实框架？（我已按此起草；这是唯一挡住主估计量定稿的点。）
2. **prompt-writing 探针**任务、rubric、分层阈值、是否双盲评分。
3. **用户在环 quality 指标**的具体操作化（任务成功怎么量）。
4. 是否纳入 given-comparator 第三条件（桥接模型侧）。
5. 任务材料是改编 V3 还是新建独立集。
6. 知情同意占位符的真实值（年龄门槛、研究者身份、保存期、补偿、伦理号）——由导师/伦理定。

---

## 9. 下一步（本 session）

1. owner 确认 §8.1 诚实框架 → 我把主估计量、探针 rubric、任务集、双语知情同意、离线工具（沿用 V3「导出不含答案 + 离线判分」架构）细化为可冻结版本。
2. 走 worktree → 实现工具 → 独立 audit → 本地 merge。
3. **协议冻结 / MDE 预注册 / 招募 / 采数据一律暂停在伦理批准之后**，等 owner 明示。
