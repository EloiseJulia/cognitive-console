# V3 stepwise 离线导出格式说明（JSON / CSV 字段字典）

> 适用产物：`deploy\stepwise\offline\button-board-stepwise-offline.html`
> 导出 schema：`microstudy-export-offline-stepwise-v1`（**未签名**，`signed: false`）
> 本文档说明参与者本地下载的 JSON 与 CSV 的结构与每个字段含义。

---

## 0. JSON 和 CSV 是二选一吗？

**不是二选一。** 两者由**同一次作答的同一份数据**导出，只是两种呈现：

| 文件 | 用途 | 是不是汇总必需 |
|---|---|---|
| **JSON** | 完整、权威、带嵌套结构的原始记录 | **是**。`aggregate_stepwise_offline.py` 只吃 JSON 目录 |
| **CSV** | 把 JSON 摊平成"每个 trial 一行"的表格，方便人工用 Excel 快速扫一眼 | 否，仅便于查看 |

- 完成页有两个按钮（下载未签名 JSON / 下载未签名 CSV），请让参与者**两个都点、两个都发回**。
- 若参与者只回传一个，**以 JSON 为准**——JSON 是汇总脚本的唯一输入，信息也最完整。CSV 只是人工预览用的副本。
- 两个文件互相不能替代，但内容同源；不要让参与者手动编辑其中任何一个。

> **重要边界**：JSON/CSV **都不含任何正确答案、判分结果或分数**。参与者页面也从不显示成绩。判分只发生在 owner 本地的 `aggregate_stepwise_offline.py`（复用可信判分逻辑）。这是"导出不泄漏答案"的设计基石。

---

## 1. JSON 顶层结构

一份导出是一个 JSON 对象，含 21 个顶层字段。示例（trials 只展示 1 条，实际有 6 条）：

```json
{
  "export_schema": "microstudy-export-offline-stepwise-v1",
  "signed": false,
  "submission_id": "b1720002-9458-4ffa-984c-bbea8ea320a8",
  "honesty_notice": "Fictional illustrative materials; unsigned offline return depends on honest submission. Exploratory pilot only; protocol is not frozen. One participant does not represent the population.",
  "materials_version": "v11.3-stepwise-20260813-draft",
  "canonical_materials_hash": "8352b45a...b13bdf0b",
  "locale_bundle_version": "v11.3-stepwise-20260813-draft-en",
  "locale_bundle_hash": "ee710fe2...d11f7d2",
  "ab_invariance_hash": "1202f424...36d5bd9d",
  "selected_locale": "en",
  "allocation_cell": 0,
  "sequence_id": "BBS11-01",
  "ab_variant": "A",
  "participant_label": "P-demo",
  "client_started_at": "2026-08-17T01:00:00.000Z",
  "client_finished_at": "2026-08-17T01:07:30.000Z",
  "demonstration_status": "acknowledged",
  "attention_selected_id": "INFO",
  "reflection_choice_ids": { "hardest": "STEP_5", "confusing": "NONE", "amount": "ABOUT_RIGHT", "pace": "OK" },
  "completion_status": "complete",
  "trials": [ /* 6 个 trial 对象，见 §3 */ ]
}
```

### 1.1 顶层字段字典

| 字段 | 类型 | 含义 | 备注 / 汇总器校验 |
|---|---|---|---|
| `export_schema` | string | 导出格式名，固定 `microstudy-export-offline-stepwise-v1` | 汇总器拒绝任何其它值（尤其拒绝签名版 `microstudy-export-v8...`） |
| `signed` | bool | 是否数字签名。离线版恒为 `false` | 汇总器要求必须是 `false`；真实性靠诚实回传 |
| `submission_id` | string(UUID) | 每次开始作答时浏览器本地随机生成的一次性提交 ID，仅用于区分不同提交、去重 | 汇总器要求存在；**同一 ID 只计一次**，重复的记入 skipped，避免同一文件被重复回传而虚增人数 |
| `honesty_notice` | string | 诚实边界声明（虚构材料 / 未签名 / exploratory / 单人不代表整体） | 随所选语言变化 |
| `materials_version` | string | 材料版本，如 `v11.3-...` | 必须与 owner 端当前材料一致，否则拒收 |
| `canonical_materials_hash` | string(hex) | 材料规范内容哈希 | 与 owner 端 `material_hashes()` 对不上则拒收（防止用旧材料混析） |
| `locale_bundle_version` | string | 所选语言包版本 | 与该 locale 元数据不符则拒收 |
| `locale_bundle_hash` | string(hex) | 所选语言包内容哈希 | 同上 |
| `ab_invariance_hash` | string(hex) | A/B 不变性校验哈希 | 与 owner 端 keys 不符则拒收 |
| `selected_locale` | string | 参与者所选语言，`en` 或 `zh-Hans` | |
| `allocation_cell` | int(0–23) | 本次随机分配到的实验格编号 | 决定 `sequence_id` 与 `ab_variant`；汇总器校验三者自洽 |
| `sequence_id` | string | 题目序列 ID，`BBS11-{cell//2+1:02d}`（如 `BBS11-01`） | 必须与 `allocation_cell` 推导一致 |
| `ab_variant` | string | A/B 操纵臂，`A`（偶数格）或 `B`（奇数格） | 同上 |
| `participant_label` | string | 参与者自填的编号/昵称（可留空，不填真实姓名） | 仅便于你辨认，不参与判分 |
| `client_started_at` | string(ISO8601) | 参与者点击"开始"的本地时间 | 参与者本机时钟，仅供参考 |
| `client_finished_at` | string(ISO8601) | 完成反思、进入下载页的本地时间 | 同上；`finished - started` 约等于总时长 |
| `demonstration_status` | string | 是否看过示范，恒为 `acknowledged`（示范页必须点"我已读完"才能进正式题） | |
| `attention_selected_id` | string/null | 注意力检查题所选选项 id（`INFO` / `CONTROL`）；未作答为 `null` | 汇总器据此算 `attention_pass`（选 `INFO` 视为通过） |
| `reflection_choice_ids` | object | 可选结构化反思的四个下拉选择，见 §2 | 可全为 `null`（参与者可不选） |
| `completion_status` | string | 整份提交状态：`complete`（6 题全做完）或 `partial` | 由各 trial 状态推导 |
| `trials` | array | 6 个 trial 对象，每个对应一个场景，见 §3 | 长度必须为 6 |

---

## 2. `reflection_choice_ids`（可选反思）

四个下拉，每个值为该下拉的选项 id 或 `null`（未选）：

| 键 | 含义 |
|---|---|
| `hardest` | 参与者觉得最难的一步 |
| `confusing` | 觉得困惑的地方 |
| `amount` | 信息量是否合适 |
| `pace` | 节奏是否合适 |

> 具体可选值由语言包定义，仅作主观反馈，不参与判分。

---

## 3. `trials[]` —— 每个场景一条（共 6 条）

每个 trial 记录参与者在一个场景里逐步作答的完整轨迹。字段与顺序：

```json
{
  "slot_index": 1,
  "scene_id": "AB1-A",
  "variant_id": "A",
  "position": 1,
  "planned": true,
  "presented": true,
  "step_presented": [1, 2, 3, 4, 5, 6],
  "step_selected_option_id": ["CONTROL", "COMPARED", "BETTER", "NO_HARM", "SCOPE_WRITTEN", "ab1-s-m4"],
  "step_presented_option_order": [
    ["INFO", "CONTROL"],
    ["COMPARED", "NOT_COMPARED"],
    ["BETTER", "NOT_BETTER"],
    ["HARM", "NO_HARM"],
    ["SCOPE_WRITTEN", "SCOPE_MISSING"],
    ["ab1-s-r9", "ab1-s-m4", "ab1-s-k2"]
  ],
  "step_shown_at_relative": [1000, 2000, 3000, 4000, 5000, 6000],
  "step_answered_at_relative": [1400, 2400, 3400, 4400, 5400, 6400],
  "participant_exit_step": 6,
  "participant_derived_state": "SUPPORTED",
  "scope_selected_id": "ab1-s-m4",
  "completion_status": "complete",
  "materials_version": "v11.3-stepwise-20260813-draft"
}
```

### 3.1 trial 字段字典

| 字段 | 类型 | 含义 |
|---|---|---|
| `slot_index` | int | 该 trial 在本序列中的槽位序号 |
| `scene_id` | string | 场景 ID（如 `AB1-A`）；A/B 场景以 `AB1-` 开头 |
| `variant_id` | string/null | A/B 场景的变体标识（`A`/`B`）；非 A/B 场景为 `null` |
| `position` | int | 该场景在参与者实际作答顺序中的位置（1–6） |
| `planned` | bool | 是否为计划内题目（恒 `true`） |
| `presented` | bool | 是否真正呈现给了参与者 |
| `step_presented` | int[] | 实际呈现过的步骤号序列（按呈现顺序，1–6） |
| `step_selected_option_id` | string[] | 每一步所选选项 id，与 `step_presented` 一一对应（见 §3.2） |
| `step_presented_option_order` | string[][] | 每一步选项**呈现顺序**的 id 列表（用于排除呈现顺序对作答的影响） |
| `step_shown_at_relative` | int[] | 每一步呈现时刻（相对开始的毫秒数） |
| `step_answered_at_relative` | int[] | 每一步作答时刻（相对开始的毫秒数）；相邻差值≈该步用时 |
| `participant_exit_step` | int/null | 参与者最终在哪一步得出结论并退出（1–6） |
| `participant_derived_state` | string | 由参与者作答**路径确定性推导**出的最终状态（见 §3.3）；不是"对错" |
| `scope_selected_id` | string/null | 仅当走到第 6 步时，所选的 scope 选项 id；否则 `null` |
| `completion_status` | string | 该 trial 状态：`not_started` / `in_progress` / `complete` |
| `materials_version` | string | 冗余记录材料版本，便于逐 trial 溯源 |

### 3.2 各步选项 id 含义

前 5 步是二选一的判断，第 6 步是场景相关的 scope 选择：

| 步骤 | 可选 id | 含义（口径） |
|---|---|---|
| step 1 | `INFO` / `CONTROL` | 这是"信息牌"性质，还是"可控动作"性质 |
| step 2 | `COMPARED` / `NOT_COMPARED` | 是否做过（有界的）比较 |
| step 3 | `BETTER` / `NOT_BETTER` | 是否确有更优 |
| step 4 | `NO_HARM` / `HARM` | 是否无害 |
| step 5 | `SCOPE_WRITTEN` / `SCOPE_MISSING` | 适用范围是否写清 |
| step 6 | 场景专属 scope 选项 id（如 `ab1-s-m4`） | 具体选定的适用范围 |

> 注意：`SCOPE_WRITTEN` 是**合法的参与者选项 id**，不是答案泄漏。

### 3.3 `participant_derived_state`（四态 → 四个"去处"）

由作答路径**确定性**推导（前端只呈现、不判分）。四态与界面"去处"、以及论文口径的映射：

| 状态 | 界面去处 | 触发条件（路径） |
|---|---|---|
| `DIAGNOSTIC` | 信息牌 | step1 选 `INFO` 即退出 |
| `UNRESOLVED` | 再看看 | step2 选 `NOT_COMPARED`，或 step5 选 `SCOPE_MISSING` |
| `WITHHELD` | 不装 | step3 选 `NOT_BETTER`，或 step4 选 `HARM` |
| `SUPPORTED` | 常用区 | 一路通过走到 step6 |

> 这只是"参与者选择路径的落点"，**不代表对错**。是否达到门槛由 owner 端汇总脚本用冻结的正确答案判分（GAA / Strict），参与者与导出中都看不到。

---

## 4. CSV 说明

CSV 是把上面 JSON **摊平成每个 trial 一行**的表格（共 6 行数据行）：

- 前若干列是会话级字段（`export_schema`、`signed`、`submission_id`、`selected_locale`、`allocation_cell`、`sequence_id`、`ab_variant`、`participant_label`、`completion_status`），在每一行重复。
- 其后是该 trial 的全部字段（同 §3.1，数组类字段以 JSON 文本形式放在单元格里）。
- 文件为 **UTF-8 BOM**（Excel 直接双击不乱码）；可能触发公式的单元格加了 `'` 前缀防注入。

CSV **不是**汇总输入，仅供人工预览。正式汇总永远以 JSON 目录为输入。

---

## 5. 汇总产物（owner 端，供对照）

`aggregate_stepwise_offline.py` 读入一批 JSON，输出：

- `participants.csv`：每位参与者一行（含 `submission_id`、GAA/Strict 通过率、注意力是否通过等）。
- `per_trial.csv`：每个 trial 一行（含参考状态、参与者状态、逐步匹配、时长等）。
- `summary.json`：与可信 `analysis.analyze()` 对齐的聚合，外加 `accepted_files` / `skipped_files` / `warnings`。

> 边界重申：数据为**未签名 exploratory pilot**，真实性依赖诚实回传；协议未冻结；单人不代表整体；材料为虚构示意。正式招募或采集 human data 前，须由导师/伦理定稿知情同意占位符并冻结协议。
