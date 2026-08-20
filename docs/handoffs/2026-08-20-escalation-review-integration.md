# 升级 Manager：四家族全文审查整合 — 冻结协议 / ledger 域待决项（2026-08-20）

> **来源**：writer session 委派 4 个独立敌对 subagent 对 `main.tex`（HEAD `95d1ab2`，24 页，正文 9,958 词，build 干净）做全文审查并整合。数值层 **integrity=SOUND（无造假、无夸大负结果）**；问题集中在 framing 与两处**触及冻结协议 / ledger 域**的溯源缺口，**属 Manager/owner 域，特此升级**。
>
> **writer 已自行处理的部分见文末"writer 已闭环"**（2 处 integrity 修复 + 1 批安全 framing 打磨，均非改-claim）。本文件只列**需 Manager/owner 拍板或执行**的项。

---

## 0. 四家族审查一览（上下文）

| 家族 | 模型 | Verdict | 核心信息 |
|---|---|---|---|
| IUI reviewer critic | GPT-5.6-luna | **2.5/5 弱拒**(conf 0.84) | 数值可信、restraint 好；但 record→interface 映射未经人验证、ITI-READ 不对称、population 比较是合成的、无 user study |
| Evidence integrity audit | Claude-opus-4.8 | **SOUND** | 所有进入 Abstract/Results/Discussion/Conclusion 的带-ledger 数字**逐位吻合**；3 MAJOR 均为可修的溯源/精度，非 integrity 失败 |
| Writing / flow | Gemini-3-pro | 目前不像一篇连贯资深 HCI 文章 | 防御性过重、Abstract 术语超前、composition 错位、formative disclaimer 堆叠 |
| Stats / method critic | Grok-4.6 | 有条件可辩护 | Abstract 口径偏强；**最强攻击 = uncertainty 轴测量性存疑却占 4/12 分母** |

**共识**：证据本体干净，需修的是**呈现口径**与**两处溯源缺口**。

---

## 1. 【owner 决策 · 冻结协议】uncertainty 轴是否留在 12 格 headline 分母

**提出方**：stats critic (Grok) BLOCKER B2/B1；与更早的 external-review pt2 同源、第二次被点名。

**问题**：
- uncertainty = 12 格里的 4 格。其 operational outcome 是 **imputed 1−Brier**，在**条件依赖的 missingness** 下测量：conf 缺失→imputed 0.5→1−Brier 恒 =0.75；parseable rate **steer 0.826 vs prompt 0.445**（巨大差异）。
- 仅 **Qwen–CAA** 一格做了 powered exclusion-free 重测（frozen-scorer 上 fully-powered 负，−0.088 [−0.109,−0.067]）；**其余 3 格未重测**；complete-case −0.337 [−0.508,−0.165] vs all-generation bound **[−0.478,+0.250] 跨零 → 符号在无限制 missingness 下不可识别**。
- critic 的 B1：Abstract/§4.3 的 "fully powered / missingness cannot flip"（针对 Qwen–CAA 的 frozen-scorer 契约）与 "sign not identified"（针对 calibration 真值）被视为**两个不同 estimand**，同置一段读者会当矛盾。

**critic 的 ask**：把 12 格 headline 分母收缩为**有可识别 estimand 的格**（deliberation-512 + skepticism），uncertainty 改报为 **measurement warning** 而非 4/12 confirmatory no-pass。

**为何升级**：改动 12 格 / 0-of-12 headline = **修改 C2 冻结 grid 定义**（Code/Protocol Freeze），AGENTS.md 明列需 owner。writer 不擅动。

**给 owner 的四选一（writer 建议附后）**：
- **(a) 维持现状 0/12**：保留 §4.3 已有 measurement caveats（现状；stats critic 会继续攻击）。
- **(b) 采纳 critic**：headline 只数可识别格 + uncertainty 作 warning（最稳，但改 headline 叙事，牵动 Abstract/Intro/Contributions/Conclusion 多处）。
- **(c) 折中**：headline 保留 "0/12"，但在所有 headline 位置显式加 "其中 4 个 uncertainty 格为 measurement-limited" 限定（改动最小，writer 可执行）。
- **(d) 拆 estimand**：明确区分 frozen-scorer 契约结果（可保 fully-powered 负）vs calibration 真值（不可识别），消解 B1 表述张力（writer 可执行的澄清，不改 grid）。

> writer 倾向 **(c)+(d) 组合**：不动冻结 grid，但在 headline 加 measurement-limited 限定并拆清两个 estimand——既回应 critic，又不触发协议 unfreeze。请 owner 裁。

---

## 2. 【Manager 执行 · ledger】avg-prompt / novice 附录数字缺 evidence-ledger 行

**提出方**：evidence integrity audit (Claude) MAJOR-2。

**问题**：以下数字进入了 **Results §composition-on-top 前的 everyday-comparator 段 + Limitations + Appendix C**，但**没有 evidence-ledger 行**，仅由 `claim-map.yaml` 的 `PENDING_AVERAGE_PROMPT_SLOT` 追踪（branch `feature/avg-prompt-comparator@31c8d59`，`valid_for_paper=false`）：
- 平均-prompt 臂：steer−average CAA skep **+0.126 [−0.009,+0.261]**、ITI skep **+0.106 [−0.051,+0.266]**、CAA delib **+0.027 [−0.054,+0.106]**；"average 落后 best prompt 约 0.21"。
- novice 臂（Appendix C）：CAA delib/skep/uncert **+0.008 / −0.000 / −0.015**、ITI skep **−0.020**、ITI uncert nominal **+0.110 [+0.007,+0.215]**、44/53 imputation、fill 敏感度 +0.027 / −0.098 等。

**违反**：evidence-ledger 门 "每个定量数字须溯源到不可变 experiment_id；禁止手抄"。对比：其他 exploratory `valid_for_paper=false` 项（E-0009 PSR、E-0010 social axis）**都有** ledger 行。

**给 Manager 的 ask（二选一）**：
- **(a)** 为**平均-prompt 臂**与**novice 臂**各补一条 evidence-ledger 行（experiment_id、code commit、artifact hash、seed、audit verdict、`valid_for_paper=false/exploratory`）——补齐 Artifact Lineage 门；或
- **(b)** 指示 writer 把这些数字降为**纯定性**表述（去掉 CI/点估计），仅保留 "steering 不稳定优于 ordinary/novice prompt" 的方向性结论。

**严重度**：数字已诚实标 exploratory/single-run/Qwen-only，属**溯源缺口非 integrity 失败**；但 **submission freeze 的 Artifact Lineage 门**要求闭合。

---

## 3. 【Manager 执行 · ledger】random-direction 诊断值未在 E-0015 ledger

**提出方**：evidence integrity audit UNVERIFIED-1。

**问题**：§7.2 assay-validity 写 "a random uncertainty direction shifts the measured outcome by **−0.24, 95% CI [−0.36,−0.12]**"。E-0015 ledger 行确认 "detects a random uncertainty movement, MDE near 0.19"，但**未记该 −0.24 [−0.36,−0.12] 数值**——可能在 artifact JSON 里，但**无法对 ledger 文本核对**。

**给 Manager 的 ask**：在 **E-0015 行补录** −0.24 [−0.36,−0.12] 及其源 artifact 路径，或确认/更正该值。

**严重度**：diagnostic supporting-context（非 claim-bearing），最低severity；但同属 Artifact Lineage 闭合。

---

## 4. 【framing · 需方向】ITI–READ 不对称（IUI critic MAJOR-2）

**问题**：Method 规定 active control 过 gate 需 "READ supported **且** TRANSFER pass"；但 READ 仅用 **exploratory CAA-style directions** 评估、明标 CAA-specific / 不 transfer 到 ITI。**故所有 ITI 控件按本文自己的规则天然无 READ 证据**，不可能 qualify。headline "12 格皆不 qualify" 因此**混淆了 "TRANSFER no-pass" 与 "READ 缺失"**。

**待决**：
- **(a) writer 可执行的澄清**：明说 12 格**全部在 TRANSFER 层 no-pass**（与 READ 无关），READ 仅作 CAA-family exploratory precondition，ITI 的阻断理由是 TRANSFER 而非缺 READ；或
- **(b) owner/Manager 决策**：是否补 **ITI-specific READ 评估**（新实验，Manager 域），使 12 格对称。

> writer 建议 (a)（纯表述澄清，不需新实验）。若 owner 要 (b)，属新实验升级。

---

## 5. 【owner 范围决策】Method 深 ML 细节移附录 / 人类验证

- writing+IUI critic：main text 的 CUDA float16、HF hidden-state hook、Mahalanobis 等**打断 HCI 声音**，建议移附录。**writer 可在 owner 点头后执行**（纯搬移，不动证据）。
- IUI critic 反复强调 record→interface 映射**未经人验证**是最大弱点。**user study 已由 owner 于 2026-08-20 决定不做**；此项无新动作，仅确认 framing 维持 "pre-deployment quality gate" 定位。

---

## writer 已闭环（无需 Manager，仅告知）

**2 处 integrity 修复（commit `2370513`）**：
- Results：steer-vs-baseline 近零诊断(+0.011/+0.0008) 从误挂 PSR 格 → 明确归 naive Qwen–CAA（消除跨方法 evidence migration）。
- `tab:axis-actions` skepticism 行陈旧（pre-E-0016）→ 同步为 Qwen CAA+ITI bounded-equivalent、Llama underpowered。

**1 批安全 framing 打磨（commit `95d1ab2`，均非改-claim、方向保守）**：
- Abstract 精度：`dead assay`→`unsatisfiable bar`、归功两个 PC、`fully powered` 收窄到 Qwen–CAA 单格、`artifact`→`does not survive at-length`（顺带解决 evidence MAJOR-3/MINOR-1 + stats M3）。
- 删 Intro 重复的 "gate can say yes"；composition 提升为独立 §subsection 并修 3 处交叉引用；formative disclaimer 5→1；清 AI 痕迹（`(below)`、tricolon）。

**状态**：build 干净（0 undefined/0 overfull，24 页，正文 9,958 词 <10k）；全部 branch-local 未 push/merge。

---

## 请 Manager 回给 writer 的决策清单

1. **item 1**：owner 对 uncertainty-in-denominator 选 (a)/(b)/(c)/(d)？（writer 建议 c+d）
2. **item 2**：Manager 补 ledger 行（a）还是让 writer 降定性（b）？
3. **item 3**：Manager 补录 E-0015 的 −0.24 值？
4. **item 4**：writer 澄清表述（a）即可，还是 owner 要 ITI-READ 新实验（b）？
5. **item 5**：owner 是否批准把 Method 深 ML 细节移附录？

> writer 待此清单回复后继续；在 owner/Manager 未定 item 1/2 前，**不动 headline 分母、不手填未溯源数字**。
