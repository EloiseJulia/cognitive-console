# Study B —— LIVE 导出 schema 字段字典

**Schema id:** `microstudy-export-live-studyB-v1` · **`signed`: 恒为 `false`**

> 🔴 pre-freeze DRAFT。参与者 payload / DOM / ARIA / export 中 **无** `expected` /
> `correct*` / `answer_key` / `rubric` / Q 值 **键名**。汇总器逐条断言（任何此类词作为
> **键** 出现即拒收）。**模型输出文本是数据，不是答案键** —— 自由文本值（含 `output_text`）
> 不做关键词扫描。

相对时间戳（`*_at_relative`）= 距 `client_started_at` 的整数毫秒；`null` 表示该阶段未到达/未提交。

## 与离线版（`microstudy-export-offline-studyB-v1`）的差异

| 变化 | 说明 |
|---|---|
| **schema id** | `...-offline-...` → `...-live-...`。 |
| **顶层新增** | `model_id`、`params_hash`、`bridge_version`（复现用；partial 时可为 `null`）。 |
| **slider 改造** | 去掉离线的 `final_setting`；改为 `final_stop_id` + `final_output_text` + `generations`。 |
| **own_prompt 改造** | 新增 `final_output_text` + `generations`。 |
| **新产物** | 汇总器多出 `generations.csv`（一行/次生成，`output_text` 单列）。 |
| **consent 文案** | 明确"本研究会显示 AI 生成示例输出"（仍标 `studyB-consent-1.0`；见文末 caveat）。 |

其余字段（`covariates` / `probe` / `task_order` / `convenience` / `attention`）沿用离线版语义。

## 顶层字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `export_schema` | string | 必须等于 `microstudy-export-live-studyB-v1`。 |
| `signed` | bool | 恒 `false`（未签名本地回传）。 |
| `submission_id` | string | `crypto.randomUUID()`，**运行时** 生成（≥ 8 字符）。去重键。绝不烘进静态 HTML DATA。 |
| `honesty_notice` | string | 本地化诚实横幅文本（含"显示 AI 生成输出"）。 |
| `instrument_version` | string | 工具版本，如 `studyB-collector-live-0.1.0-draft`。 |
| `bridge_version` | string \| null | 桥接版本（首次成功生成时由桥接回填）。 |
| `model_id` | string \| null | 实际使用的模型 id（白名单内，如 `gpt-4o-mini`）。 |
| `params_hash` | string \| null | 冻结采样参数集的哈希（`sha256:...`），复现用。 |
| `selected_locale` | string | `en` 或 `zh-Hans`。 |
| `consent_agreed` | bool | 勾选同意并开始后为 `true`。 |
| `consent_agreed_at` | string (ISO) | 同意时间。 |
| `consent_copy_version` | string | 同意书版本标签。 |
| `client_started_at` | string (ISO) | 会话开始时间。 |
| `client_finished_at` | string (ISO) \| null | 到达导出的时间；partial 时 `null`。 |
| `completion_status` | string | `complete` 或 `partial`。 |
| `covariates` | object | AI 熟练度协变量（见下）。 |
| `probe` | object | Prompt 写作探针（见下）。 |
| `task_order` | object | 抵消 seed + 序列（见下）。 |
| `tasks` | list | 恰好 **一个** 配对主任务（见下）。 |
| `convenience` | object | 短 TLX + Likert + willingness（见下）。 |
| `attention` | object | `{ "selected_id": string\|null }` —— 原始注意力答案。 |

## `covariates`（仅协变量，不分组）

| 键 | 类型 | 说明 |
|---|---|---|
| `usage_frequency` | string | 选项 id（`never`…`daily`）。 |
| `tuned_parameters` | string | `no` / `once_twice` / `regularly`。 |
| `understands_latent_control` | string | `not_at_all`…`well`。 |
| `self_rating` | int | 自评 1–5。 |

## `probe`（不出输出、不现场判分）

| 键 | 类型 | 说明 |
|---|---|---|
| `prompt_text` | string | 参与者写的一条指令。 |
| `started_at_relative` / `committed_at_relative` | int \| null | 打开/提交的相对毫秒。 |
| `char_count` | int | 去空白后长度。 |
| `edit_count` | int | `input` 事件次数。 |

## `task_order`

| 键 | 类型 | 说明 |
|---|---|---|
| `seed` | int | mulberry32 种子（决定呈现顺序与每任务条件顺序）。 |
| `sequence` | list | `[{ "task_id", "condition_order": "slider_first"\|"prompt_first" }]`；须与 `tasks` 1:1（汇总器强制）。 |

## `tasks[]`（唯一配对主任务）

汇总器拒绝 `tasks` 长度 ≠ 1 的导出。

| 键 | 类型 | 说明 |
|---|---|---|
| `task_id` | string | 稳定任务 id。 |
| `condition_order` | string | `slider_first` 或 `prompt_first`。 |
| `slider` | object | 滑块条件（下）。 |
| `own_prompt` | object | 自写 prompt 条件（下）。 |

### `tasks[].slider`

| 键 | 类型 | 说明 |
|---|---|---|
| `final_stop_id` | string \| null | 最终提交的档位 id（无"正确档"）。 |
| `final_output_text` | string \| null | 最终采纳档位对应的模型输出（**数据**）。 |
| `settings_explored` | int | 参与者点选过的不同档位数。 |
| `generations` | list | 每次生成一项：`[{ "stop_id", "output_text", "at_relative" }]`。 |
| `started_at_relative` / `committed_at_relative` | int \| null | 打开/提交的相对毫秒。 |

### `tasks[].own_prompt`

| 键 | 类型 | 说明 |
|---|---|---|
| `prompt_text` | string | 参与者最终 prompt。 |
| `char_count` | int | 去空白后长度。 |
| `edit_count` | int | `input` 事件次数。 |
| `final_output_text` | string \| null | 最终 prompt 对应的模型输出（**数据**）。 |
| `generations` | list | 每次生成一项：`[{ "prompt_text", "output_text", "at_relative" }]`。 |
| `started_at_relative` / `committed_at_relative` | int \| null | 打开/提交的相对毫秒。 |

## `convenience`

| 键 | 类型 | 说明 |
|---|---|---|
| `tlx_effort` | int | 短 TLX effort，1–7。 |
| `likert_effort` | int | "滑块很省力"，1–5。 |
| `likert_discoverability` | int | "我能看出滑块在做什么"，1–5。 |
| `willingness_choice` | string \| null | 看过两边输出后：`slider` 或 `own_prompt`。 |
| `willingness_reason` | string | 自由文本理由（可空）。 |

## 汇总器产物（owner 侧）

- `participants.csv` —— 一行/人（含 `model_id` / `params_hash` / `bridge_version`）。
- `tasks.csv` —— 一行/人×任务；含 **空** 事后 Q 占位列 `q_slider_pending` /
  `q_own_prompt_pending` / `d_paired_pending`（由独立注册的评分实验回填，**非** 本汇总器）。
- `generations.csv` —— **一行/次生成**：`condition`、`stop_id`（slider）或 `prompt_char_count`
  （own_prompt）、`output_char_count`、`at_relative`、`output_text`（单列）。
- `summary.json` —— accepted / skipped / warnings + `q_scoring.computed_here=false` + `model_id`。

## 硬契约（任何地方都不出现）

`expected`、`correct*`、`answer_key`、`rubric`、任何 Q 值 **键名**。注意力检查的指定项
**不** 作为答案键存储；排除规则由 owner 事后按预注册应用。**`output_text` 是数据不是答案键**：
它是模型生成的文本，用于事后独立 Q 评分，不参与参与者侧的任何"判分"。

## 公平性（预设，spec §5/§9）

两条件送 **同一 base 素材 + 同目标**；差异只在控制方式（滑块冻结预设 vs 参与者 prompt）。
滑块预设 **只做通用风格位移**，**严禁编码任务成功条件**；预设文本只存服务端桥接、不入本 export、
不回显前端。单测 `test_bridge_presets_do_not_encode_task_success_conditions` 对此做 forbidden-
substring 断言。

## Caveat（judgment call，待 owner 确认）

`consent_copy_version` 仍标 `studyB-consent-1.0`，但 live 版正文比离线版多了"本研究会显示 AI
生成示例输出"等措辞（离线版写的是"不显示任何生成结果"）。这是按 spec §3.1 的 live 语义调整；
若 owner 认为文案实质变更应 **另起版本号**（如 `studyB-consent-1.0-live`），请告知，可一处改常量。
