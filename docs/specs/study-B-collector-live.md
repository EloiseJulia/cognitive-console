# Spec —— Study B 半实时本地采集器（Study B Semi-Live Local Collector）

> **状态：🔴 DRAFT 规格 / 协议未冻结 / exploratory。** 伦理批准已获（owner 确认
> 2026-08-17）。**采数据前**仍必须过 §12 gate 中未清项（协议冻结 + MDE 预注册、预设
> 冻结、独立 audit、隐私方案）。协议未冻结 → 所收数据一律 **exploratory**，不得直接当
> confirmatory 去镜像模型侧 0/12。
>
> 依据：`docs/plans/study-B-protocol-draft.md`（v0.2）+ owner 决策（2026-08-17，方向 B）。
> 取代：`docs/specs/study-B-collector.md`（解耦离线版 D-0130）在**主任务**部分的"无输出"
> 设计。离线版工具保留可用；本 spec 是主任务改为**显示真实模型输出**后的新版。

---

## 0. 为什么改（背景）

解耦离线版（不显示输出）掏空了**主观便利轴**：参与者没看到滑块效果，却被问"省不省力/愿不
愿用"，数据空洞（owner 试玩暴露此问题）。方向 B：**让参与者看到两条件的真实模型输出**，
主观题才有意义。owner 已有本地 **Copilot API 代理**（`http://localhost:8313`，OpenAI 兼容，
背后 Claude/GPT/Gemini 等真模型），可本机出真实输出，**无需数据库**。

---

## 1. 核心诚实框架（owner 批准，load-bearing，不可含糊）

**A. 本 study 的"滑块" = 不透明的、冻结的"预设控件"，不是 latent steering vector。**
聊天 API 给不了潜控件。滑块每一档 = 一段**冻结的隐藏预设指令**；选档 → 该预设 + 固定任务
素材送模型生成。因此本 study 测的是 **"用滑块选一段不透明预设 prompt" vs "自己写 prompt"**。

- **能诚实成立**：它操作化了"潜滑块的**使用体验**"（不透明、省力、离散档、看不到机制），
  且"预设档 = 我们给的 curated 指令、自写 = 参与者 prompt"对上论文 best/average-prompt 两对照。
- **禁止宣称**：**不得**把它当 latent 0/12 的镜像。论文必须把"study 里的滑块"与"模型证据里
  的 steering 滑块"明确分开。写作 session 须被告知此口径。

---

## 2. 架构（半实时、本地、无数据库）

**本地桥接（thin bridge）**：一个小 Python 脚本 `scripts/run_studyB_live.py`，职责：
1. 把采集器 HTML 托管在 `http://127.0.0.1:<port>`（浏览器**同源**访问，规避 CORS——
   代理 8313 未开 CORS，`file://` 直连会被浏览器拦）。
2. 暴露**同源** `POST /api/generate`：浏览器把 `{condition, task_id, stop_id|prompt_text}`
   发给桥接；桥接在**服务端**组装最终 message（预设冻结在服务端，不暴露给参与者 view-source），
   转发给 `http://localhost:8313/v1/chat/completions`，回传 `{output_text, model, params_hash}`。
3. **不落任何数据库**；生成的输出只在内存 + 回给浏览器；结束时浏览器像离线版一样**导出一份
   JSON/参与者**（现在多含各条件的输出）。

owner 操作 = **跑一条命令、打开打印出的 `127.0.0.1:<port>` 链接**，参与者在此页面完成。

**安全边界**：桥接只监听 `127.0.0.1`（不对外）；只允许固定白名单模型 id 与固定参数（见 §4）；
只接受已知 `task_id` / `stop_id`；参与者 prompt 作为 user content 转发（正是研究对象），但桥接
**不回显预设指令文本**给前端。

---

## 3. 参与者流程（phases）

单页 SPA，顺序：

1. **Consent（已定稿，studyB-consent-1.0）**：双语；勾选同意→记 `consent_agreed` + 时间戳；
   不同意→退出、不记数据。开头明确："本研究会显示 AI 生成的示例输出;所有任务与素材为虚构。"
2. **Covariate 问卷（仅协变量、不定义组；3–4 项）**：使用频率 / 是否调过参数 / 是否理解 latent
   控制 / 自评 Likert。
3. **Prompt-writing 探针（分组用，客观）**：标准化目标 + 虚构素材，写**一条** prompt。采集
   文本 / 时间戳 / 字数 / 编辑次数。**不现场判分**（rubric 事后双盲）。探针**不出模型输出**
   （分组探针测"会不会写强 prompt"，不需看输出）。
4. **主任务（1 个配对任务）**，两条件**顺序抵消**（随机 seed 记入导出）：
   - **Slider 条件**：离散档滑块 UI；参与者选一档 → **调 `/api/generate` 出真实输出并显示**。
     采集：最终档位、探索档数、每次生成的 stop_id + 输出、时间戳。
   - **Own-prompt 条件**：参与者写一条 prompt → **调 `/api/generate` 出真实输出并显示**。
     采集：prompt 文本、输出、时间戳、字数、编辑次数。
   - **对称公平**：同模型、同参数、同 base 素材；各自可生成（允许滑块换档重生成、prompt 重写
     重生成，次数记录）；两条件呈现顺序抵消。
5. **便利/主观评分（现在有意义，因为看过两边输出）**：
   - 客观（已在采）：操作用时、探索档数、prompt 编辑/字数、生成次数。
   - 主观：TLX effort、"设滑块省力"、"仅凭标签能预期滑块作用"（discoverability）、
     **willingness「看过两边结果后，这类任务更愿用滑块还是自己写 prompt」+ 理由**。
6. **Attention check**：instructed-response（"Purple"），只记原始选择，排除规则 owner 事后应用。
7. **导出**：生成一份 JSON（含各条件输出、模型/参数、行为、主观、注意力）。

---

## 4. 模型与可复现（冻结项 D）

- **模型白名单**：桥接只允许固定 id；默认 `gpt-4o-mini`（快、稳）。冻结时锁定单一 id。
- **参数固定**：`temperature=0`、固定 `max_tokens`（如 512）、无 top_p 变动；参数集计 `params_hash`
  写入导出，供复现。
- 导出记录：`model_id`、`params_hash`、每次生成的 `created`/usage（若代理返回）。
- **注意**：即便 `temperature=0`，代理/上游可能非严格确定;导出保存**实际返回的输出文本**，
  事后 Q 以**保存的输出**为准，不重新生成。

---

## 5. 滑块预设冻结与公平性（冻结项 E，研究者自由度，必须审计）

- 每个任务的滑块 = N 个离散档；每档 = 一段**冻结的、通用的单维风格预设**（如语气/正式度：
  s1 非常随意 … s5 正式）。
- **公平性硬约束（审计须逐条核验）**：预设**只做通用风格位移**，**严禁编码任务的具体要求**
  （如"≤40 字/纯素/不用感叹号"这类**任务成功条件**不得写进预设）——否则滑块靠作弊取胜。
  自写条件同样只给 base 素材 + 目标，参与者自己决定"怎么做"。
- 预设文本 + base 素材 + 目标一并**冻结 + 预注册**；改动须重走 audit。
- 预设**不回显**给参与者（模拟潜控件的不透明性），但**记录**参与者选了哪个 stop_id。

---

## 6. 质量两层，分开（C，不混）

- **客观 Q（warranted control 主张）**：仍是**事后** rubric 批量评分**保存的输出**（slider 输出、
  own-prompt 输出），单独登记 experiment-registry。**不靠参与者判、不现场算。** 导出的
  `q_*_pending` 占位列由该实验回填。
- **用户主观偏好/便利（新有意义那块）**：参与者看过两边输出后现场作答，直接入导出。
- 两者**并列保存、互不替代**。论文里 Q = 质量证据，主观 = 便利/偏好证据。

---

## 7. 数据模型（导出 JSON，新增字段）

在离线版 schema 基础上（`microstudy-export-offline-studyB-v1` → 新 schema id
`microstudy-export-live-studyB-v1`）：

- 顶层新增：`model_id`、`params_hash`、`bridge_version`。
- `tasks[].slider` 新增：`generations: [{stop_id, output_text, at_relative, usage?}]`、`final_stop_id`、
  `final_output_text`。
- `tasks[].own_prompt` 新增：`generations: [{prompt_text, output_text, at_relative, usage?}]`、
  `final_output_text`。
- 其余（covariates / probe / convenience / attention / task_order / consent）沿用离线版语义。
- **硬契约不变**：payload / DOM / ARIA / export **不含** `expected` / `correct*` / `answer_key` /
  `rubric` / 任何 Q 值。**模型输出文本是数据，不是答案键**；aggregator 断言这些**键名**不出现
  （自由文本值不扫描）。

---

## 8. Aggregator（owner 端汇总，扩展）

新增/沿用 `scripts/aggregate_studyB_live.py`（或扩展现有，保持自包含、不 import V3）：
- `participants.csv`：一行/人（沿用 + `model_id`）。
- `tasks.csv`：一行/人×任务，含滑块最终档、生成次数、own-prompt 字数/编辑，**空** `q_slider_pending`
  / `q_own_prompt_pending` / `d_paired_pending`（事后评分回填）。
- `generations.csv`（新）：一行/次生成，含 `condition, stop_id|prompt_char_count, output_char_count`，
  供事后 Q 评分实验取 `output_text`。**输出文本单列保存**（可能长）。
- `summary.json`：accepted/skipped/warnings + `q_scoring.computed_here=false` + `model_id`。
- 断言：schema 校验、去重（`submission_id`）、无答案键键名、标量守卫（沿用离线版 MAJOR-1 修复）。

---

## 9. 对称/公平（fairness）

同模型、同参数、同 base 素材；两条件各 one-shot 可重生成（次数记录、对称）；呈现顺序 seed 抵消；
滑块预设不编码任务成功条件（§5）。

---

## 10. 诚实边界与隐私

- 任务/素材虚构；输出为示例;**不作 user-benefit 结论**;单人不代表整体;协议未冻结 → exploratory。
- 全本地：推理走 `127.0.0.1` → `localhost:8313`；不落库；每人一份 JSON。
- 输出来自 Copilot 模型经 owner 代理，仅虚构任务、本地小 pilot；ToS 由 owner 知悉。
- 诚实横幅更新：显示"本研究会显示 AI 生成示例输出"。

---

## 11. 交付物

- `scripts/run_studyB_live.py`：本地桥接（托管 HTML + `/api/generate` 代理 + 冻结预设/参数/白名单）。
- `scripts/generate_studyB_live.py`：生成单页采集器 HTML（半实时版；含 fetch `/api/generate`）。
- `scripts/aggregate_studyB_live.py`：汇总器（+ generations.csv）。
- `tests/test_studyB_live.py`：结构/去重/无答案键/标量守卫/schema/预设不泄漏/白名单等测试。
- `deploy/studyB/live/OFFLINE→LIVE-README.md`、`LIVE-EXPORT-SCHEMA.md`。
- 更新 `docs/plans/study-B-protocol-draft.md` §3.0；记 decision-log。

---

## 12. 硬 gate（未清项，采数据前必须）

- [x] 伦理批准 + 导师签字（owner 确认 2026-08-17）。
- [x] 知情同意定稿（studyB-consent-1.0）。
- [ ] **协议冻结 + MDE 预注册**（未做 → 数据 exploratory）。
- [ ] **滑块预设 + 任务集冻结 + 独立 audit**（§5）。
- [ ] 隐私/数据保存方案落实（本地加密、2 年内删除，已写入 consent）。
- [ ] 本 spec 实现的独立 audit（§13）。

---

## 13. 工作流

独立 worktree → implement subagent 按本 spec 建 → 独立 audit（核验：无答案键、预设不编码任务
成功条件、白名单/参数冻结、schema、去重、桥接只监听本地、对称性）→ 本地 merge 进 main（不 push）。
