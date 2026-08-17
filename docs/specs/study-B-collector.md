# Spec —— Study B 解耦式离线采集器（Study B Decoupled Offline Collector）

> **状态：🔴 DRAFT 规格 / 未冻结 / pre-ethics。** 本工具是**自测/试点**用（同 V3 自测流程），
> **采数据前**仍必须过 §7 gate（伦理/IRB + 导师签字、知情同意定稿、协议冻结 + MDE、独立
> audit、隐私方案）。**不得**在 gate 前招募/采真实 human data。
>
> 依据：`docs/plans/study-B-protocol-draft.md`（v0.2，D-0129/D-0130）。
> 架构：解耦式离线（D-0130，owner 选定方案一）——采集，不跑模型，Q 事后批量评分。

---

## 1. 目标与非目标

**目标：** 一个**自包含单文件离线 HTML** 采集器，参与者本地打开、完成、导出 JSON；owner 分发→回收→汇总（同 V3 离线工作流，零 API / 零数据库）。

**非目标（明确不做）：**
- **不跑任何模型 / 不含模型输出 / 不含答案键**（participant payload/DOM/ARIA/export 均不含 expected/正确答案）。
- **不现场算 Q**（Q = 事后批量评分实验，另登记 experiment-registry）。
- **不碰 V3**：逻辑指纹 `cb91ebcf…` / 冻结答案 / 材料 v11.3 一字不动。H4 可应用性用**现有 V3 离线工具原样**单独完成（每参与者两份导出），本采集器不重实现 V3。
- **不部署 / 不招募**（gate 前）。

---

## 2. 参与者流程（phases）

> **精简版（D-0132，owner 要求减负，约 10–15 分钟）**：主任务砍到 **1 个配对任务**；
> 协变量 + TLX 精简到 3–4 核心项；**去掉可选 reliance 模块**。核心比较（滑块 vs 自写
> prompt）与分组探针为 load-bearing，保留。任务数为 freeze 时按功效可回调的参数。

按顺序，单文件内 SPA：

1. **Consent（复用 V3 offline consent 骨架）**：双语；占位符 `(to be completed)` 留伦理/导师回填；勾选同意→记 `consent_agreed:true` + 时间戳（同意留痕入导出）。不同意→退出、不记数据。
2. **Covariate 问卷（不定义组，仅协变量；精简 3–4 项）**：使用频率 / 是否调过参数 / 是否理解 latent 控制 / 自评 Likert。
3. **Prompt-writing 探针（§1.1）**：给标准化目标 + 待处理素材（示意/虚构），参与者写**一条** prompt（自由文本）。采集：prompt 文本、开始/提交时间戳、字数、编辑次数。**不判分**（rubric 打分事后双盲）。
4. **主任务（两轴；§3/§5）——1 个配对任务**，两条件**顺序抵消**（随机 seed 记入导出）：
   - **Slider 条件**：呈现一个 latent 滑块 UI（离散档位，纯前端，**无模型输出**）。采集：最终档位、探索的档位数、开始/提交时间戳。
   - **Own-prompt 条件**：参与者写一条 prompt 达同目标。采集：prompt 文本、开始/提交时间戳、字数、编辑次数。
   - 两条件均**一次性提交、无反馈回路**（对称公平，见 D-0130）。
5. **便利/主观评分（§4 便利轴；精简）**：简版 3 项 TLX/Likert（effort / discoverability）+ willingness-to-use「滑块 vs 自己写 prompt 更愿用哪个 + 理由」。
6. **导出**：生成 JSON（+ 可选 CSV 预览），供 owner 回收。（**reliance 模块已移除**，D-0132。）

> **DRAFT 任务内容**：首版内置**1 个示意/虚构占位任务**（清晰标注 DRAFT/fictional）供自测流程；**最终任务集需另行撰写 + 审 + 冻结**，本 spec 不定稿任务文本。

---

## 3. 数据模型（导出 JSON）

**顶层 schema：** `microstudy-export-offline-studyB-v1`，`signed:false`。

**必含顶层字段（草案）：**
- `export_schema`, `signed`, `submission_id`(浏览器 `crypto.randomUUID()`，运行时生成、≥8 字符、去重用), `honesty_notice`, `instrument_version`, `selected_locale`
- `consent_agreed`(bool), `consent_agreed_at`(ISO), `consent_copy_version`
- `client_started_at`, `client_finished_at`, `completion_status`("complete"|"partial")
- `covariates`(obj：AI 熟练度问卷答案)
- `probe`(obj：`prompt_text`, `started_at_relative`, `committed_at_relative`, `char_count`, `edit_count`)
- `task_order`(obj：抵消序列 + seed)
- `tasks`(list，**精简版含 1 元素**，每元素)：`task_id`, `condition_order`("slider_first"|"prompt_first"),
  - `slider`：`final_setting`, `settings_explored`(int), `started_at_relative`, `committed_at_relative`
  - `own_prompt`：`prompt_text`, `char_count`, `edit_count`, `started_at_relative`, `committed_at_relative`
- `convenience`(obj：精简 3 项 TLX/Likert + willingness + 理由文本)
- `attention`(注意力检查答案，用于预注册排除)

> **精简版移除 `reliance` 字段（D-0132）。** aggregator 字段集断言随之收紧为不含 reliance。

**不含（硬契约，aggregator 强制断言）：** 任何 `expected` / `correct*` / `answer_key` / Q 值 / rubric 分。探针与任务本就无烘焙答案。

---

## 4. Aggregator（owner 端，Python，`scripts/aggregate_studyB_offline.py`）

- 读入目录下 `*.json`，逐份**校验**：schema 正确、`signed:false`、submission_id 有效、**无私钥/无答案键断言**（复用 V3 `_assert_no_private_keys` 风格）、字段集完整、时间戳单调。
- **按 submission_id 去重**（首份计入，重复记 skipped）。
- 产出：`participants.csv`（每参与者一行：covariates、probe 元数据、便利评分、effort 埋点汇总）+ `tasks.csv`（每任务两条件的 prompt/设置/effort）+ `summary.json`（accepted/skipped/warnings + 待事后填的 Q 占位列）。
- **不算 Q、不判分、不判正向**。Q 由事后批量评分实验填入（另登记）。
- 复用 CSV 注入防护（`_safe` 前缀 `'`）、`utf-8-sig`、诚实横幅。

---

## 5. 诚实与不变量（audit 必核）

- participant 端（payload/DOM/ARIA/export）**零答案键 / 零 Q / 零 expected**。
- **V3 指纹/答案/材料 v11.3 未被本工具触碰**（本工具不 import 也不改 V3 材料判分逻辑；H4 用现有 V3 工具原样）。
- submission_id 运行时生成、非烘焙、去重有效。
- 诚实横幅：fictional/illustrative + exploratory pilot + protocol 未冻结 + 单人不代表整体 + **本文无 user-benefit 结论**。
- consent 占位符 `(to be completed)` 未回填时工具可自测，但**导出标记 pre-ethics / DRAFT**。

---

## 6. 交付物

- `deploy/studyB/offline/studyB-collector-offline.html`（自包含单文件；或由生成器 `scripts/generate_studyB_offline.py` 组装）
- `scripts/aggregate_studyB_offline.py`
- `tests/test_studyB_offline.py`（校验 + 去重 + 无答案键 + 时间戳单调 + 完整/部分完成）
- `deploy/studyB/OFFLINE-README.md`（owner 分发/回收/事后 Q 评分说明）
- `deploy/studyB/OFFLINE-EXPORT-SCHEMA.md`（字段字典，同 V3 风格）

## 7. 硬 gate（不豁免）

采真实数据前：伦理/IRB + 导师签字、consent 定稿(回填占位符)、协议冻结 + MDE 预注册、独立 audit、隐私/保存-删除方案。本工具在 gate 前仅供 owner 自测。

## 8. 工作流

worktree `feature/studyB-collector` → implement subagent 按本 spec 实现 → 独立敌对 audit（核 §5 不变量 + 无答案键 + 无 Q + V3 未触）→ 本地 no-ff merge 进 main（**不 push**）。
