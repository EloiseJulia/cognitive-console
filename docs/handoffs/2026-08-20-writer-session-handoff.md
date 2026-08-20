# Writer Session 总交接（2026-08-20）— 故事重构 + 四家 audit + ITI fold + user-study 降级

> 接续 `2026-08-19-story-reconstruction-handoff.md`（基点 b333200）。真实状态一律 `git rev-parse --short HEAD` 为准。

---

## 一、真实 git 状态（自行核验）

- worktree: `C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\.worktrees\writing-reconstruction-completeness`
- 分支: `feature/writing-reconstruction-completeness`；**真实 HEAD: `eea2f52`**
- 本轮基点 `b333200` → 24 个 commit。tracked 树 clean。
- build: `docs/paper/build.ps1 -Clean` → **25 页 / 0 undefined / 0 overfull**。
  - ⚠️ **build 卫生坑**：PaperDir 顶层偶发残留 stray `main.aux`（未跟踪），会遮蔽 `build/main.aux` 导致**假的 53 undefined-citation**。build 前若见 undefined 突增，先 `Remove-Item -Force main.aux,main.log,main.out,main.bbl,main.blg` 再 `-Clean` 重建。
- 未跟踪 `??`（勿提交）：`docs/handoffs/2026-08-18-*.md`(旧)、`docs/paper/figures/*.pptx` `*.PNG`(草图)。
- **未 push、未 merge**；外层主 checkout 在 `main`(5716cdd)，是**旧版**（差 856 行），我的成果全在 feature 分支等 Manager 过 gate 合并。

---

## 二、本 session 已完成（b333200 → eea2f52，全部 build 干净 + audit 把关）

**A. 句子级润色**（`f5e3c8f`/`21fc180`/`d5805a2`）：Abstract/Conclusion 拆长句、破折号降密、§4.1 加"naive 判据 vs 记录"对比句、§7.3 重排。

**B. HCI 故事重构**（`6ef5bea`/`ce07a29`/`75d88a5`/`17da98c`，均 audit SOUND）：主线 spine = interpretability-as-interface release decision；record 提为 design artifact + 对齐 model cards/datasheets accountability 谱系；Intro 统计细节下沉 Results；Discussion §7.1 改 design-lesson 开场。**memory: `session files/writing-direction-hci-story.md`（后续必读，勿回退防御性 rebuttal 写法）。**

**C. 三个 reviewer 防御**（`594e53e`→`49122c7`；`5188fb6`→`f0f9314`；`8926cd3`，均 audit SOUND，含返工）：
- formative 单专家 = depth-over-breadth（弃"多人没法汇总"弱论证）；
- no-user-study = **pre-deployment gate** 定位（返工消除与 planned-study 的自相矛盾）；
- anti-straw-man（真实先例 + 专家证实的信念 + anticipatory timing；软化夸大普及度措辞）。

**D. 四家族 hostile audit + 整合**（GPT venue-fit / Gemini stats / Claude honesty / Grok writing）→ 修：
- `4a2276f` 诚实精度 F1(predeclared 措辞)/F2(Abstract fully-powered scope)/F4(CI 对齐主表)；
- `10457d9` positive-control 合唱收 1+1 + legibility refrain；
- `a7b249d` **F3**：everyday-user 无账本 claim 从 Abstract/Conclusion 移除（submission BLOCKER 关闭）。

**E. sub-threshold 尝试 → 回退**（`6e1680e`→`429e5fe`）：owner 一度裁决把 Llama skepticism 改 "sub-threshold positive"，但 audit 发现**违反冻结审计的 D-0135**（"Llama must be stated underpowered/indeterminate"，MDE 0.051>δ 对 δ 仍 underpowered）→ 回退，owner 最终**维持 D-0135**。**教训：改 evidence 定性前必查 evidence-ledger 的冻结 scope 指令。**

**F. ITI×Qwen composition fold**（`790a238`，三重 gate 全过，audit=SCIENCE SOUND）：composition 升级为"CAA+ITI 在 Qwen 稳健无正增量"；ITI strong-delib 真实小负 `−0.0255[−0.046,−0.007]` 诚实写 decrement、ordinary-uncert INVALID 标 diagnostic-only。ledger E-COMPOSITION-A-ITI 行 byte-identical 追加（D-0137）。

**G. 通读连贯性梳理**（`649be2d`）：修 §5 everyday-user status 与 §4.6 矛盾、§7.3 composition fold 同步。

**H. 外部 review 响应**（`a1ac38c`→`147154c`）：pt2 uncertainty measurement-validity 分层（Qwen-CAA 稳健 vs 3 cell measurement-limited，audit 返工修归因越界）、pt3 reproducibility artifact-vs-raw 区分。**pt1 ITI delib 512 重测升级 Manager**（见 §四）。

**I. user study 降级**（`eea2f52`，owner 决策 2026-08-20，audit SOUND）：不做 user study → 全文 ~11 处 "planned/preregistered study" 降级为 **future work / open direction**（§Planned Evaluation 改标题 "Future Work: ..."）。红线守住：未声称"不需要 user study"，convenience 仍是真实必要的开放问题。定位现为 **pre-deployment computational method paper**。

---

## 三、当前论文状态

25 页 build 干净。三核心贡献：(1) 评估方法 (2) 五字段资格记录（accountability artifact 定位）(3) 独立审计 case study（12/0 + 正对照）。四实验全部 fold：E-0017f 正对照 / powered skepticism（Qwen bounded-equiv，Llama underpowered per D-0135）/ composition CAA / composition ITI。主线一条线贯穿，诚实红线处处守住。

---

## 四、Pending（交 Manager / owner）

**Manager（owner 已于 2026-08-20 派发跑）**
- **点1：ITI×{Qwen,Llama} deliberation 512-token 重测** — 详见 `docs/handoffs/2026-08-20-escalation-iti-delib-remeasure.md`。镜像 CAA 的 E-DELIB512 协议、additive、三重 gate。**出后交 writer fold**，落点已在该 escalation doc 勘定（§4.3 deliberation 段 + table axis-actions + claim-map C2 + ledger 追加）。

**owner/Manager 决策**
- uncertainty 是否移出 12 格分母（改 frozen grid 定义 = 冻结协议）——外部 review 点2 提出，writer 未动，标记待决。
- 何时走 **Submission Readiness**（critic 五节点 + freeze）。

**残留 PENDING 槽位（source 注释，勿凭空填）**：human/composition-discussion 已 FOLDED/DROPPED 标注；其余按需。

---

## 五、Reference 状态（2026-08-20 核查）

- 论文用 `\bibliography{reframed-references}`（reframed-references.bib，39 条目）。**`references.bib`（旧，19897 字节）未被使用**，是遗留 orphan 文件，可清理。
- **26 个 \cite key 全部在 bib 内，0 undefined**（build 时的 undefined 是 bibtex-pass 卫生噪声）。
- **13 个 bib orphan（有条目、正文未引用）**。其中 **trust/reliance calibration 组可能是真实遗漏**（lee2004trust、schemmer2023appropriate、bansal2019beyond、li2026learntrust）——论文反复讲 reliance/over-trust/calibration warning 却未引这条 HCI 经典线。steering 组（subramani2026latent 的 steering→calibrator、korznikov2025rogue）亦可能相关。manipulation/dark-patterns/sycophancy 组弱相关。**是否补引属内容/领域判断，待 owner 检查决定；writer 未擅自加 cite。**

---

## 六、铁的工作纪律（不变）

- **改 evidence 定性前必查 evidence-ledger 的冻结 D-xxxx scope 指令**（本轮 sub-threshold 血泪教训）。
- fold 前自核三重 gate（valid_for_paper + ledger 行 + audit SOUND）；ledger 行 `git show <src>:...` byte-identical 追加。
- 数字只来自 committed artifact；守 scope 红线（0/12、exploratory/additive、负结果不 spin、C3 gate、formative≠user study）。
- 结构/evidence 改动做完过独立敌对 audit（本轮用 code-review + general-purpose 多家族）。
- 每 commit 后 `git --no-pager log --oneline -1` 确认；build 期望 0 undef/overfull（注意 stray aux 坑）。
- **只在本 worktree 动，DO NOT touch 主 checkout**；不 push、不 merge、不改 generated tables/figures。
- commit trailer: `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>`
