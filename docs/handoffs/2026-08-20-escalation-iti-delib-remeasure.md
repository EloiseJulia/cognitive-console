# 升级 Manager：ITI deliberation 512-token 重测（点1）— 2026-08-20

> **[RESOLVED 2026-08-20] Manager 已交付实验并 fold 完成。** ITI delib-512 fold-gate 三门通过（D-0140, `feature/iti-delib512@7362689`；ledger 行 E-DELIB512-ITI-REMEASURE；独立 audit `reviews/2026-08-20-iti-delib512-audit/` = **Numbers SOUND**，lineage BLOCKER seal!=committed 已 CLOSED，seal==committed 验证）。writer 已按下方 fold 落点全部同步进 `main.tex`（build 干净，0 undefined/0 overfull，26pp）。数值：I1 Qwen ITI **−0.033 UNDERPOWERED（小负）**、I2 Llama ITI **+0.005 EQUIVALENT（近零）**；四格 deliberation-512 现对称完整，审稿人"为何只补 CAA"已消除。诚实红线守住（小负写小负、近零写 equivalent、不 spin、不改 frozen 0/12）。

---

> 来源：owner 转来一份外部 AI review，三点批评经 writer 逐条核实**全部属实**、且与内部四家族 audit 吻合。点2/3 writer 已做表述强化（见下）；**点1 只能靠新实验关闭，属 Manager/实验域，特此升级。**

## 请求（点1，actionable）
补 **ITI×{Qwen2.5-7B, Llama-3-8B} deliberation** 的 **512-token 重测**，对齐已完成的 CAA 协议 **E-DELIB512-REMEASURE**：
- 512-token budget（脱离 64-token GSM8K 触底）；
- 512-token DEV 上**重选 α**（64-token α 在长度下无效，非 frozen）；
- **additive**：不覆盖 frozen 0/12 grid，不改 E-0005/E-0006/E-0011；
- 走三重 gate（valid_for_paper + ledger 行 + 独立 audit SOUND）后交 writer fold。

## 为什么必要
- 现状：`main.tex` §4.3 明说 "the two ITI deliberation cells were not re-measured and remain 64-token--floored placeholders"；表 2（tab:c2-delta-4cell）ITI×Qwen/Llama deliberation 就是 floored 值。
- CAA 两 cell 已 512 重测（E-DELIB512-REMEASURE，D-?），**ITI 两 cell 没有** → 不对称的真实 gap，审稿人会问"为何只补 CAA"。
- 这是四家 audit + 外部 review 共同点名的、唯一**无法靠写作关闭**的洞。

## fold 落点（重测完成后，writer 执行）
1. `main.tex` §4.3 deliberation 段 "two ITI deliberation cells were not re-measured..." → 升级为实测结果（诚实标 sign/power，对齐 CAA 写法）。
2. Table `tab:axis-actions` deliberation 行的 "re-measure ITI" next-evaluation → 更新。
3. `claim-map.yaml` C2 scope 的 deliberation 描述 + supporting_evidence_ids。
4. ledger 行 byte-identical 追加。

## writer 已并行完成（点2/3 表述强化，不需 Manager）
- **点2**（uncertainty measurement-validity）：§4.3 uncertainty 段新增分层——Qwen–CAA 是 fully-powered exclusion-free 稳健负（missingness 无法翻转），其余 3 cell 是 measurement-limited no-pass（0.5-imputation + parseable-rate 差异），应读作 measurement-limited 而非 clean negative。**注意**：审稿人建议的"把 uncertainty 移出 12 格分母"触及 frozen grid 定义（冻结协议），**需 owner/Manager 决策**，writer 未动。
- **点3**（reproducibility 区分）：§Method 开头前置区分 artifact-level（committed JSON→表/图，无 GPU，强）vs raw-generation rerun（model revision hash 未记录，有限），指向 Limitations。hash 已无法补记。

## 待 owner/Manager 决策项
- 是否把 uncertainty 的其余 3 cell（或整轴）在 headline 计数上标注为 measurement-limited（改 0/12 分母表述 = 冻结协议，需正式决策，勿擅动）。
