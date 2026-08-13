# Session Handoff — User-Study 打磨线 — 2026-08-13

> **给接替 session**。本 handoff 专门交接**本项目 user study 的打磨工作**。仓库是一个多 agent、多分支的大仓（还含论文/模型实验等其它线），但本线只负责 **user study（现行版本 = V3）** 的设计与 UX 打磨。除非 owner 明确要求，不要动其它线。
>
> **权威来源**：repository ledgers（docs/ledgers/*）+ 本 handoff。**session SQL todos 不权威**（里面有历史 manager 遗留的 stale 项，忽略）。

---

## 0. 一句话现状

User study 已迭代到 **V3「一步一问·开卷按钮板」**，面向普通非技术用户、生活化、零术语的小规模（**N ≈ 20**）within-subject 理解性研究，检验"论文的对照约束门槛能否被普通人理解并正确应用"。**仅 owner-local preview / DRAFT / 无人类数据**。V1、V2 是早期版本，已保留在 main 并**与 V3 并存、不混析**，除非 owner 指名否则不要碰。

---

## 1. Git / 环境（先读，避免踩坑）

- 当前分支 **main**，HEAD **`eda4762`**，`origin/main..HEAD` **ahead 117**，**未 push**。**不要 push**（对外发布是 owner/human gate）。
- **未跟踪 owner 文件**：`投稿前对照分析_Legible-Latent-Axis_2026-08-06.docx`（仓库根）。**绝不 add/edit/delete/move/commit**，除非 owner 明确命令。
- 未跟踪：`prototype-v3-demo/`（一次性可点击原型，非研究管线，可忽略/删）。
- **严重环境坑（务必记住）**：本机 `pip install -e .` 的可编辑安装指向了一个**陈旧 worktree**（`.worktrees/iti-positive-control`），所以直接 `python -m cognitive_console...` 会**加载旧代码**。**一切预览/测试/脚本一律加 `PYTHONPATH=src`（指向 main 的 src）**，否则会跑到旧包、看到旧界面（本 session 曾因此误判"改动没生效"）。可选一次性修复：在 main 根目录跑 `pip install -e .` 把包重新指回 main（会改全局环境，需谨慎）。

---

## 2. 三个并存版本（V3 是现行）

| 版本 | 模块入口 | 材料目录 | 预览端口 | 说明 |
|---|---|---|---|---|
| V1 | `cognitive_console.microstudy` | `data/microstudy_scenario_v9/` | 8876 | 场景旋钮·白话（v9.1）。早期版本，保留。 |
| V2 | `cognitive_console.button_board` | `data/microstudy_button_board_v10/` | 8878 | 按钮板·四选一（v10）。早期版本，保留。 |
| **V3（现行）** | `cognitive_console.button_board_stepwise` | `data/button_board_stepwise_v11/` | 8891 | 一步一问·开卷（**v11.3**）。**当前打磨对象**。 |

预览启动（务必 PYTHONPATH=src）：
```powershell
$env:PYTHONPATH = (Join-Path (Get-Location).Path 'src')
python -m cognitive_console.button_board_stepwise --host 127.0.0.1 --port 8891 --verification-key-file .runtime\button-board-stepwise-preview.key
```
- verification key 在 `.runtime\`（gitignored），**绝不下发/提交/暴露**。
- 停止预览：**只按精确 PID `Stop-Process -Id <PID>`**；禁止按进程名杀。

---

## 3. V3 设计要点（现行）

**框架**：普通用户整理"自己家里/手机上的按钮板"。全程生活化、零术语、**无歧义措辞**（禁"暖/高情商/智能/更强/优化"等含糊或会误读的词），全部为**明确标注的虚构/示意试用记录**。

**交互**：开卷（卡片、"你原来怎么做"、每题四选项常显）+ **一步一问**（每屏一个小问题，系统据答案自动推出去处并显示推理路径）+ **每步可回退/重选**（重选后清后续、按新答案重走；提前结束语义正确）。

**四个面向用户的"去处"（内部 key 名不变，但对论文用新术语，见 §4）**：
- 常用区（须自己选对"仅在…"范围）= SUPPORTED
- 信息牌 = DIAGNOSTIC
- 不装 = WITHHELD
- 再看看 = UNRESOLVED

**冻结判定链**（每题逐步、遇到即结束）：
1. 看情况 / 按下执行动作改变目标结果 → 看情况 → 信息牌
2. 有没有和"你原来的简单做法"在相同条件下**放一起比过** → 没有 → 再看看
3. 比下来**赢过原来做法** / 差不多或更差 → 差不多或更差 → 不装
4. 有没有把别的重要事弄坏 → 有 → 不装
5. 有没有写清只在哪些情况试过 → 没写清 → 再看看
6. 选对"仅在…"范围 → 常用区

**核心直觉（零术语教会，与论文一致）**：有反应≠更好；**要赢的是你已有的简单做法（对应论文 bounded prompt comparator），不是赢"什么都不做"**；证据不足则搁置；范围外不算；能显示≠能控制。

**关键构念控制**：
- **A/B 配对**（AB1-A / AB1-B 互斥，每人只见一版）：同物同场景同条件、唯一差别"是否赢过原来做法" → 一个 SUPPORTED、一个 WITHHELD。最强正向信号。
- 每题只给**中性原始记录**（次数/场合/现象），参与者自己推断，不给结论词。
- 1 道**注意检查**（非计分）。
- **练习 P1**：现为**引导式、一步一步的只读示范**（每屏当前一步问题；正确项绿底+"✓ 正确选择"文字标注（色盲友好，不只靠颜色）；蓝色框显示该步依据；"下一步"推进；结束显示最终去处+why，再进正式题）。用户不作答、无练习作答数据、不泄漏正式题答案。
- **无参与者代码**：start 不需输入，服务器自动生成内部标识用于去重/导出主键。

**判分**：主 GAA = 每正式题最终去处 == 冻结正确去处；Strict GAA = 去处对 + 决定性步骤/范围也对（排除蒙对）。**keys/expected 全部由结构字段自动派生，禁止手填**；participant payload/DOM/ARIA/export **不含** expected/正确答案/派生判分字段。

**版本/导出**：materials **v11.3-stepwise**；export schema **V8**（raw signed）；analysis **v2**。跨版本（V5/V6/V7/V8/V9/V11）**hardfail 不混析**。

**逻辑指纹（重要不变量）**：`cb91ebcf…b0bd`。**任何 UX-only 改动都必须保持它不变**（证明四态/正确答案/A/B/序列/keys 未动）。审计一律核验此指纹 + generator `--check` + 每题 expected 与 base 对拍。

---

## 4. 论文 reframe 对齐（2026-08）

论文已 reframe，写作 session 已收到独立交接（`docs/handoffs/user-study-writing-handoff.md`，已发出）。要点：
- 新标题：*Before You Add the Slider: A Comparator-Bound Test for Latent Controls in LLM Interfaces*。
- 论文**不用固定四态 taxonomy**，改用"**界面动作 + 阻断原因**"：`active control passes the gate` / `read-only diagnostic candidate` / `active control withheld`（reason ∈ interval-includes-zero / comparator-negative / below-floor / coherence-fails / missingness-limited）。
- 门槛 = 赢过 bounded prompt comparator（预注册候选里 DEV 选出）+ point-estimate floor δ=0.05 + CI 排零 + coherence。
- **study 内核、冻结正确答案、A/B、GAA、诚实边界均不随 reframe 改变**——已逐题核验一致。四个"去处"是**面向用户的桶**，对论文时映射到上面动作/原因（不装 与 再看看 = 同一动作 withheld、reason 不同）。
- study **内部 key 名（SUPPORTED/DIAGNOSTIC/WITHHELD/UNRESOLVED）参与者看不到**，无需改；只是文档/写作用新术语。

---

## 5. 冻结正确答案（供 owner 自测判分；勿泄漏给参与者）

| 场景 | 正确去处 | 决定性 |
|---|---|---|
| F2 | 信息牌 DIAGNOSTIC | 只显示、不改结果 |
| F3 | 不装 WITHHELD | 弄坏别的（coherence fails：约定要响的测试来电被静音） |
| AB1-A | 常用区 SUPPORTED | 赢过原办法 + 无害 + 范围写清 + 选对范围 |
| AB1-B | 不装 WITHHELD | 没赢过原办法（comparator-negative） |
| F4 | 再看看 UNRESOLVED | **没和原办法比过**（原办法 0 轮），非"范围不足" |
| F5 | 再看看 UNRESOLVED | 范围没写清 |
| F6 | 常用区 SUPPORTED | 赢过 + 无害 + 范围写清 + 选对范围 |

**判分方法**（owner 发来导出 JSON 时）：
```powershell
$env:PYTHONPATH = (Join-Path (Get-Location).Path 'src')
# python: from cognitive_console.button_board_stepwise.analysis import analyze, trial_scores, planned_trials
# plan = planned_trials(d["sequence_id"], d["ab_variant"], d["participant_code"])
# 逐题 trial_scores(trial, slot) 比对 expected_state / 决定性 / 范围；analyze([d]) 出 GAA/Strict 汇总
```
导出**不含**正确答案（防泄漏），判分靠材料私有重算。

---

## 6. 工作纪律（必须遵守）

- 每处改动：**独立 worktree** → 实现 → **独立普通 audit（owner 已指示：普通 audit 即可，不必 hostile；但科研红线仍按 AI-Instruction）** → **本地 merge 进 main（不 push）**。
- **UX-only 改动禁止改变**：逻辑指纹 `cb91ebcf…`、expected、keys、四态、A/B 操纵、序列、判分。审计须证明这些不变。
- **诚实边界（写作/汇报都守）**：本 study 只测"门槛可理解/可应用"，**不测** user benefit/信任/界面优越；材料是示意/虚构；**不与论文模型证据合并**；状态 DRAFT/未招募/无数据 → 表述用"已设计并预注册/将进行"。
- **human/owner gates（未获明确批准不得做）**：招募/接触参与者/收集 human data、owner timing pilot、伦理/IRB、协议冻结、样本量/MDE 冻结、对外发布/投稿、把 exploratory 升为 confirmatory、删除不可再生数据、暴露 verification key、动 owner DOCX。
- 输出**不要有乱码**（owner 曾指出误出现 "court" 之类无意义字符）；中文回答保持干净。

---

## 7. 决策/账本锚点

- decision-log：D-0116（V2）、D-0117（V3）、D-0118（V3 改名+回退）、D-0119（V3 精简：删铺垫/代码/去处说明区、练习改示范）、D-0120（V3 练习引导式逐步示范）。
- experiment-registry：microstudy v9.1 / button-board v10 / stepwise v11.x 各有 row，均 `valid_for_paper=false`、`ready_for_owner_local_preview_no_human_data`。
- 相关 reviews/审计摘要在 `reviews/2026-08-1*/`。

---

## 8. 可能的下一步（等 owner 指令）

- 继续按 owner 反馈做 V3 UX 打磨（保持逻辑指纹不变）。
- owner 会自己试玩并发导出 JSON → 用 §5 方法判分、给"是否正向"结论（并声明单人不代表整体）。
- 除非 owner + 伦理 gate 明确通过，**不启动**招募/human data/timing pilot/协议冻结/MDE 冻结。

*本 handoff 不做任何新科学决定，不授权 push/投稿/招募/human data/协议冻结/GPU。*
