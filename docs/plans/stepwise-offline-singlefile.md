# Slice plan — V3 stepwise 离线单文件版（无服务器/无数据库）

## 目标
Owner 的 Render 免费 Postgres 已被别的项目占满。改用**零服务器、零数据库**的采集方式：
志愿者本地打开**一个自包含 HTML 文件**完成 study，做完在本地**下载 JSON + CSV**，
把文件发回 owner；owner 用**留在仓库、不分发**的汇总脚本离线判分并汇总成表格。

## 硬约束（不可违反）
1. **逻辑指纹不变**：不改 `button_board_stepwise_materials.py` 任何逻辑字段；
   `tests/test_button_board_stepwise_materials.py` 指纹测试保持绿；
   `scripts/generate_microstudy_v11_stepwise.py --check` 保持 current。
2. **导出/前端不含答案**：分发出去的 HTML 与志愿者导出的 JSON/CSV **绝不能包含**任何
   `expected*`, `comparison_rule`, `required_readings`, `required_scope_dimensions`,
   `scope_correct`, `scope_written`, `gaa_correct`, `strict_correct`, `correctness` 等
   私有/判分字段或其取值。答案键只存在于 owner 仓库。
3. **不冒充签名版**：离线导出用**独立 schema 名** `microstudy-export-offline-stepwise-v1`，
   带 `"signed": false`；绝不复用 `microstudy-export-v8...` 名称，避免与签名版混淆/混析。
4. **四态与 A/B 与序列不变**：SUPPORTED/DIAGNOSTIC/WITHHELD/UNRESOLVED、AB1-A/B、
   BBS11-01..12 序列、每格 planned expected 全部沿用可信 python 逻辑，前端只呈现不判分。
5. **诚实边界**：文件内与文档内必须声明：示意/虚构材料、无服务器签名依赖诚实回传、
   数据为 exploratory pilot、协议未冻结、正式招募需导师/伦理定稿知情同意占位符。

## 架构（解耦式）
### 组件 1：生成器 `scripts/generate_stepwise_offline.py`（python，可信，构建期）
- 复用现有可信函数（**只读，不改**）：
  `button_board_stepwise.materials.{common_materials, locale_bundle_metadata,
  planned_trials, scene_material, question_material, material_hashes, validated_sources}`。
- 对 24 个分配格（allocation_cell 0..23）各生成一个**参与者视角题包**：
  - `allocation_cell`, `sequence_id = f"BBS11-{cell//2+1:02d}"`, `ab_variant = A(偶)/B(奇)`。
  - 6 个 slot（AB1-{variant}, F2..F6），每个 slot 含：`slot_index, position, scene_id,
    variant_id`，以及**参与者可见**的 scene（用 `scene_material(locale, scene_id)`，
    该函数返回的是 public scene，本身不含 keys — 需断言校验），
    step6 的 `scope_options` 按 `planned_trials(...)["scope_order_ids"]` 排好序。
  - **严禁**把 `planned_trials` 返回里的 `expected_*`, `scope_correct` 等 key 字段写进题包。
    只取 `slot_index/position/scene_id/scope_order_ids`，其余丢弃。
- 内联通用材料：`common`(questions 每步 prompt+options、progress、attention、reflection、
  destinations 的 id/label/description)、`demonstration`。
  - 注意 `common_materials` 已 `pop("questions")`；每步问题文案改用 `question_material(locale, step)`
    （prompt + options[{id,text}]）逐步取出内联。
  - `destinations` 顺序即 (SUPPORTED,DIAGNOSTIC,WITHHELD,UNRESOLVED) 对应 `_result_payload`。
- 内联材料完整性字段（供 owner 端交叉校验，非安全）：`materials_version`,
  `canonical_materials_hash`（来自 `material_hashes()`）, 选中 locale 的
  `locale_bundle_version/hash`, `ab_invariance_hash`。
- 语言：默认双语可切换或单一 `en`+`zh-Hans` 都内联；MVP 至少支持 `zh-Hans` 与 `en` 切换。
- 输出：单个 `dist/stepwise-offline/button-board-stepwise-offline.html`，
  把 CSS（复用 `static/study.css` 观感）、runtime JS、内联 JSON 数据全部打进一个文件。
- 输出后**自检**：读回生成的 HTML，断言不含任何 §约束2 的 blocked 关键词/取值（大小写不敏感），
  否则报错退出（fail-closed）。

### 组件 2：前端运行时（HTML 内联 JS，参与者端，不判分）
流程复刻 server 有状态流：
`欢迎/知情同意 gate → demonstration 确认 → 6 次 formal trial(逐步) → attention → reflection → 完成`
- **知情同意**：复用当前 study.js 的 `CONSENT_COPY` 双语草案 + gate（勾选才能开始）。
- **分配**：加载时从 24 格随机选 1（或让参与者输入 1..24 的编号映射 cell=编号-1；MVP 用随机 + 记录）。
- **逐步逻辑**：移植 `route_participant`（6 步确定性状态机）到 JS：
  - step1 INFO→DIAGNOSTIC(done) / CONTROL→next
  - step2 NOT_COMPARED→UNRESOLVED(done) / COMPARED→next
  - step3 NOT_BETTER→WITHHELD(done) / BETTER→next
  - step4 HARM→WITHHELD(done) / NO_HARM→next
  - step5 SCOPE_MISSING→UNRESOLVED(done) / SCOPE_WRITTEN→next
  - step6 任意 scope id→SUPPORTED(done)
  - 到达 done 显示对应 destination（四态文案）。允许 revise（回退改答，与 server `_revise_step` 等价：截断该步及之后记录）。
- **记录**（每 trial，字段名对齐 `EXPORTED_TRIAL_FIELDS` 以便 owner 端复用判分）：
  `slot_index, scene_id, variant_id(AB1 取 A/B 否则 null), position, planned=true, presented,
   step_presented[], step_selected_option_id[], step_presented_option_order[],
   step_shown_at_relative[](ms 相对开始), step_answered_at_relative[], participant_exit_step,
   participant_derived_state, scope_selected_id, completion_status`。
- attention（step1 问题重放，记 `attention_selected_id`）、reflection（hardest/confusing/amount/pace）、
  demonstration_status='acknowledged'。
- **完成即导出**：提供「下载 JSON」「下载 CSV」两个按钮（用户要求两者都要）。
  - JSON = 组件3 定义的 offline schema（含 assignment、材料完整性、trials[]、reflection、attention、
    demonstration_status、participant_label(可选自填昵称/编号)、client_started_at ISO、
    `export_schema="microstudy-export-offline-stepwise-v1"`, `signed:false`, honesty banner 文本）。
  - CSV = 每 trial 一行的人类可读表（slot_index, scene_id, 四态结果, 逐步答案, 用时ms 等），
    **不含答案键**。BOM + `'` 前缀防注入（对齐 server `_csv` 的安全处理）。

### 组件 3：离线导出 schema `microstudy-export-offline-stepwise-v1`
```
{
  "export_schema": "microstudy-export-offline-stepwise-v1",
  "signed": false,
  "honesty_notice": "示意/虚构材料；无服务器签名；exploratory pilot；协议未冻结。",
  "materials_version": "...", "canonical_materials_hash": "...",
  "locale_bundle_version": "...", "locale_bundle_hash": "...", "ab_invariance_hash": "...",
  "selected_locale": "zh-Hans|en",
  "allocation_cell": 0..23, "sequence_id": "BBS11-XX", "ab_variant": "A|B",
  "participant_label": "自填字符串或空",
  "client_started_at": "ISO8601", "client_finished_at": "ISO8601",
  "demonstration_status": "acknowledged",
  "attention_selected_id": "INFO|CONTROL|null",
  "reflection_choice_ids": {"hardest":..,"confusing":..,"amount":..,"pace":..},
  "completion_status": "complete|partial",
  "trials": [ { EXPORTED_TRIAL_FIELDS 对齐的对象 } x6 ]
}
```

### 组件 4：汇总脚本 `scripts/aggregate_stepwise_offline.py`（python，可信，owner 端，不分发）
- 输入：一个目录（含多份志愿者 offline JSON）+ `--out-dir`。
- 校验（fail-closed）：
  - `export_schema == "microstudy-export-offline-stepwise-v1"`；拒绝签名版 v8 混入。
  - `canonical_materials_hash == material_hashes()["canonical_materials_hash"]`、
    `materials_version == MATERIALS_VERSION`、locale/ab_invariance 一致；不一致的文件跳过并计入报告。
  - `allocation_cell→sequence_id/ab_variant` 自洽。
- 判分：对每份 export，`plan = materials.planned_trials(sequence_id, ab_variant, ordering_seed)`。
  - **注意 ordering_seed**：server 用 `attempt_id`（影响 step6 scope **呈现顺序**，不影响判分正确性，
    因为 `trial_scores` 只看 id 不看顺序）。汇总只需判分 → 用任意稳定 seed（如
    `f"{allocation_cell}"`）即可；scope 判分用 `slot["scope_correct"]` 对 `scope_selected_id`。
  - 重建 trial dict：用记录的 `step_presented/step_selected_option_id` 经 `route_participant`
    推导 `participant_derived_state/participant_exit_step`，与记录值一致性校验（不一致计告警）。
  - 调 `analysis.trial_scores(trial, slot)` 得 gaa/path_exact/decisive/strict。
  - scope 正确性用 `slot["scope_correct"]`（该 key 只在 owner 仓库，安全）。
- 输出：
  - `participants.csv`：每人一行（label, cell, seq, ab, locale, completion, answered_trials,
    gaa_count, gaa_rate, strict_count, strict_rate, attention_pass）。
  - `per_trial.csv`：每 trial 一行（含四态期望/实际、gaa/strict、逐步对错、用时）。
  - `summary.json`：镜像 `analysis.analyze()` 的聚合（mean_gaa_rate_complete 等）+ 跳过/告警清单。
- **单人不代表整体**、exploratory 声明打印在 stdout 头部。

## 测试 `tests/test_button_board_stepwise_offline.py`
1. `test_generated_html_contains_no_answer_keys`：跑生成器→读 HTML→断言不含 blocked 关键词，
   且不含任一 slot 的 expected 取值（从 keys 反查每个 expected_answer/ state / scope_correct 的字符串不出现在 HTML）。
2. `test_generated_html_has_24_packets_and_integrity_fields`：解析内联 JSON，24 格齐全、
   canonical_materials_hash 与 `material_hashes()` 一致。
3. `test_aggregate_scores_perfect_path`：构造一份"完美路径"offline JSON（每 trial 走到 expected 出口），
   汇总得 gaa_rate==1.0；构造一份已知错误路径，得对应低分。
4. `test_aggregate_rejects_signed_v8_and_hash_mismatch`：签名版/改过 hash 的文件被跳过并报告。
5. `test_route_port_parity`（可选）：若有 JS 测试环境（node），对随机路径比对 JS route 与 python route。
6. 指纹测试仍绿（不新增，跑既有）。

## 交付物清单
- `scripts/generate_stepwise_offline.py`
- `scripts/aggregate_stepwise_offline.py`
- `dist/stepwise-offline/button-board-stepwise-offline.html`（生成产物，可入 git 方便 owner 直接发）
- `tests/test_button_board_stepwise_offline.py`
- `deploy/stepwise/OFFLINE-README.md`（owner 操作：如何生成/分发/收集/汇总 + 诚实边界与 gate 提醒）
- `docs/plans/stepwise-offline-singlefile.md`（本文件）

## Gate（合并前）
- 全测试绿（含既有 V3 42 + 新离线测试）；指纹绿；generator --check current。
- 生成 HTML 自检无答案泄漏。
- 独立 audit（敌对、只读）：重点核验①无答案泄漏②判分与 server 判分对拍③schema 不冒充签名版
  ④指纹/materials 未被改动。
- 本地 merge 进 main，**不 push**。
