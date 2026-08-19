# Writer Session 交接（2026-08-19 深夜）— 句子润色 + HCI 故事重构

> 本文件接续 `2026-08-19-writer-session-handoff.md`（起点 b333200）。真实状态一律以 `git rev-parse --short HEAD` 为准，不轻信叙述。

---

## 一、真实 git 状态（务必自行核验）

- worktree: `C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\.worktrees\writing-reconstruction-completeness`
- 分支: `feature/writing-reconstruction-completeness`
- **真实 HEAD: `17da98c`**（核验：`git rev-parse --short HEAD`）
- 本 session 起点 `b333200`，共 7 个 commit（见下）。tracked 树 clean。
- 未跟踪 `??`（**不要提交**）：`docs/handoffs/2026-08-18-*.md`(旧)、`docs/paper/figures/*.pptx` `*.PNG`(草图)。
- build：`docs/paper/build.ps1 -Clean` → **24 页 / 0 undefined / 0 overfull**（7 个 underfull hbox，良性）。

---

## 二、本 session 已完成并提交（b333200 → 17da98c）

### A. 句子级润色（3 commit，纯语言 + 已 audit SOUND）
- `f5e3c8f` Abstract 拆两处超长句；8 处句尾破折号→逗号/冒号（em-dash 47→39；分号判定为学术正当用法，未大动）。
- `21fc180` Conclusion 双冒号长句拆三句。
- `d5805a2` §4.1 新增"naive 判据 vs 本记录"对比段（回应 IUI R2 MAJOR-2「读成滑块没用」）；§7.3 design-lesson 前置；§7.5 分号超长句拆分。→ 独立敌对 audit（scope-drift）判 **SOUND**。

### B. HCI 故事重构（4 commit，owner 指令，全部 audit SOUND）
owner 诉求：主线更清晰、核心贡献一眼抓住、HCI 价值更顺、去拼凑感/去"ML 硬改 HCI"感、去防御去重复、以资深 HCI 学者视角、有整体观、故事可重构。
- `6ef5bea` **Introduction 重构**：立 sticky 主线 "as interpretability matures into an interface… that release decision is this paper's subject"；record 提为 **design artifact**；把 Intro 里的统计 refinement 细节（bounded-equivalent/floored/missingness）下沉 Results；移除 formative 在 gap 段的拼贴；三 commitments 从超长句改三条清晰规则；contribution 2 对齐 model cards/datasheets 谱系。
- `ce07a29` **Related Work 强化**：record = accountability 谱系（model cards/datasheets/audit）下推到 single control affordance + release gate → "earned the right to act"；三 citation 合并无增删；formative 开头改 "this release-decision problem" 贯穿主线。
- `75d88a5` **Discussion §7.1 重构**：以 design lesson 开场（legibility ≠ license to act），positive-control 防御压缩为一句 + `\ref` 指向 Limitations §assay-validity（去与该节的重复），结尾 "an honest console says so"。
- `17da98c` §7.1 标题改为 "Legibility Is Not a License to Act"（design-oriented，配合 body；label 未改，无断链）。

### 审计与终检
- B 组两次独立敌对 audit（intro-reframe / RelatedWork+Discussion）均判 **SOUND**：零数字改动、零 caveat 删除、headline 0/12 完好、负结果未 spin、novelty 未夸大、**C3 gate 守住**（HCI 价值仍是 proposed/artifact-instantiated，不声称验证对用户有效）、formative 移除无悬空 `\ref`。
- 读者视角**整体连贯性终检**（pdftotext 通读）：主线词贯穿 8 章节无断裂；开篇无统计防御堆积；Discussion design-lesson 开场、Conclusion 首尾闭环（"earned an active role"）。

### 写作方向 memory（重要，后续 writer 必读）
`C:/Users/v-elzhang/.copilot/session-state/5c90530f-44fa-4960-b7e3-11dc8b21c85c/files/writing-direction-hci-story.md`
= owner 定的 story spine + HCI 价值主张 + 防御下沉原则 + 红线。**后续任何润色都应遵此主线，勿回退到防御性 rebuttal 写法。**

---

## 三、当前论文状态

24 页，build 干净。三核心贡献不变：(1) 评估方法 (2) 五字段资格记录（现明确定位为 affordance 层 accountability artifact）(3) 独立审计 case study（12/0 负结果 + 正对照）。主线现为"interpretability-as-interface 的 release-decision discipline"。三个 Manager 实验（E-0017f / E-0016 / E-COMPOSITION-A）已 fold，已回应 IUI 三审 assay-validity / underpowered / substitution 三攻击。

---

## 四、未完成 / 待决（同上一个 handoff，未变）

**外部/实验（Manager）**
- **E-COMPOSITION-A 的 ITI×Qwen 第二片**（Manager，~出后 writer 可 fold 成"跨两方法 composition null"）。fold 落点已勘定：正文 §4.6 "single-method, single-model (CAA on Qwen; ITI and Llama untested)" → 升级；Discussion §comparator-substitution 同步；claim-map C2 中 E-COMPOSITION-A scope 注同步；ledger 行 byte-identical 追加；数字只从 committed artifact 取。
- **user study 去留**：owner/§5 决策（IUI 头号 venue-fit 风险，formative 不能完全关此 BLOCKER）。

**owner/Manager 决策项**
- `table-mde`：主表加 MDE 列 = generated table，须改 `make_c2_delta_table.py` 重跑，属 experiment/Manager。
- 附录 B(logit)/C(novice) 压缩、Discussion design-implications 展开（后者高过度声称风险，依赖 PENDING 决策）。

**正文残留 PENDING 槽位**（勿凭空填，须真实冻结数据）：human/user、composition-discussion、method/results 各 slot。

---

## 五、铁的工作纪律（不变）

- fold 实验前自行核验三重 gate（valid_for_paper=true + ledger 有行 + audit SOUND/PASS），只凭交接文字不 fold。
- 数字只来自 committed artifact，禁手填；ledger 行 byte-identical 追加。
- 守 scope 红线：不改 headline 0/12；负结果不 spin；exploratory/underpowered 如实标；formative≠user study；不擅改 valid_for_paper；**HCI 价值不越 C3 gate**。
- 每批 commit 后 `git --no-pager log --oneline -1` 确认 subject 真变；build 期望 0 undefined/overfull。
- 结构/故事改动做完过独立敌对 audit（本 session 用 code-review agent 审 scope 漂移，均 SOUND）。
- 不 push、不 merge、不改 generated tables/figures/numbers、不动未跟踪 DOCX/PPTX/PNG。
- commit trailer：`Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>`
- LaTeX linter 报 `\textbf Unknown command` 良性，忽略。
