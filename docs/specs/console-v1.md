# Spec · console-v1 (reality-check instrument)

- **Spec ID**: console-v1
- **Status**: DRAFT→IMPLEMENTED (feature/37-console)
- **定位**: 边界/极限仪器 + 信任校准，不是 latent 超能力滑块。
- **数据来源**:  
  - `results/c2b_adjudication_hf_2026-07-24/c2b_adjudication_results.json`（C2 主证据）  
  - `results/gpu_7b_2026-07-23/c1/c1_facade_results.json`（E-0003 对应 C1）  
  - 退化回退：`docs/ledgers/evidence-ledger.md`（仅当本地 C1 JSON 缺失）

## 1. 目标与用户

- **目标**：把 reality-check 结果变成可走查的最小研究 console，支持后续最小真人走查或方法学资产演示。
- **用户**：研究者、审稿型读者、方法学演示受众（非工程开发者也可读）。

## 2. 必须可视化的四件事

1. **双通道对照**：Prompt 通道 vs Latent(steering) 通道，在同一轴上并排展示。
2. **C1 可读性鸿沟（facade）**：每轴 `prompt_reach / pole_reach` 比值与 CI（优先来自 7B C1 JSON；回退时明确来源）。
3. **C2 行为非转移 + 冲突**：每轴 `Δ(steer-prompt)`、Bonferroni CI、pass/fail；突出 `uncertainty=-0.228` 的负向结果。
4. **边界/信任校准面板**：把结果翻译成“何时不该信任 latent 控制”的明确提示，尤其 uncertainty 轴红色告警。

## 3. 技术栈与选择理由

- **Python 标准库 HTTP server + 原生 HTML/CSS/JS（无前端框架）**
  - 依赖最小、可离线、可快速审计；
  - 数值在服务端直接读取冻结 artifact，保证 lineage；
  - 前端仅负责渲染与颜色编码，避免复杂构建链。

## 4. 验收标准

- 本地一条命令可启动并打开 console 页面。
- 页面展示四类信息且所有数值来自 artifact 文件读取（非硬编码）。
- C2 表中 uncertainty 轴明确显示负向 `Δ` 与红色边界警示。
- 提供 README 启动说明。
- 有最小单测覆盖：数据加载成功、映射取值来自文件而非常量。
