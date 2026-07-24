# Copilot CLI Session

> [!NOTE]
> - **Session ID:** `96bb4b1c-cb6c-4a5a-904f-e44b0ee6beca`  
> - **Started:** 7/24/2026, 2:02:13 PM  
> - **Duration:** 2m 21s  
> - **Exported:** 7/24/2026, 2:04:34 PM  

---

<sub>8s</sub>

### User

你是 INDEPENDENT hostile auditor，没参与过这次实验。审计一个 C2b 仲裁的【负结果】(VERDICT=KILL_PLAN_D, 0/3 轴通过)是否是一个【有效/合格的负结果】，而不是仪器静默失败伪造出来的假 null。仓库根 C:\Users\v-elzhang\Desktop\MyFolder\cognitive console。把 summary 与既有结论当【不可信】，从原始 JSON 产物 + 源码 + 运行日志重新验证。

【要审的产物（本地）】
- results/c2b_adjudication_hf_2026-07-24/c2b_adjudication_results.json  (完整原始结果)
- results/c2b_adjudication_hf_2026-07-24/c2b_adjudication_summary.md
- results/c2b_adjudication_hf_2026-07-24/experiment-registry.yaml
- results/c2b_adjudication_hf_2026-07-24/adj2.run.log  (逐 cell 进度 + C1 重推导)
- 冻结协议：docs/ledgers/prereg-c2b-adjudication.md
- 决策逻辑源码：src/cognitive_console/experiments/adjudicate_c2b.py ；入口 scripts/run_c2b_adjudication.py

【背景（供定位，不要当结论）】在 Qwen2.5-7B-Instruct 上跑冻结仪器：per-axis N=60/60/80、k=5、α∈{2,4,6,8,12,16,24}、DEV/TEST split(1/3)、paired item-cluster bootstrap B=10000、Bonferroni CI level=1−0.05/3、δ=0.05、coherence gate ≤1.5×baseline、三档 verdict。结果：三轴 mean(d)分别 +0.015 / -0.080 / -0.228，CI 均未同时满足“排除0且点估≥0.05”，coherence 全 ok → 0/3 → KILL。

【你必须独立验证（重点是“负结果是否有效”，不是“能否翻成正”）】
1. **仪器是否真的在工作，而非静默全失败**：从 adj2.run.log 确认 11365 次生成真的发生、逐 cell DONE、无 stall watchdog 触发、无异常吞掉；C1 在 7B 上重推导 3/3 axes facade(ratio\<1, CI\<1)是否与 results 一致。
2. **verdict 数学是否忠实冻结判据**：独立从 JSON 的 per-axis mean(d)/CI/coherence 重算 pass/fail 与三档 verdict，核对 δ=0.05、Bonferroni CI level=0.98333、“CI 排除0 AND 点估≥δ AND coherence pass”。有没有把某轴误判？
3. **是不是“degenerate 输出”造出的假 null**：检查每轴 frozen α、baseline_degeneracy、各 α 的 coherence_ok 与 degeneracy；steering 是否因为把输出打崩(重复/乱码)而被 coherence gate 挡掉，导致“没信号”其实是“α 太小没敢加”？特别看：所选 frozen α 是否是被 coherence gate 逼到很小的值(delib α=2, skep α=6, unc α=8)？若更大 α 全部 coherence 失败，说明这个 CAA 方向一加就崩——这是关于“方法弱”还是“claim 假”的重要区分，请给出证据判断。
4. **outcome scorer 是否合理**：deliberation=GSM8K 正确率、skepticism=TruthfulQA-MC 命中、uncertainty=1−Brier。检查这些 per-item outcome 是否真的在 [0,1] 合理分布、不是全 0/全 1(那会让 mean(d) 恒 0 = 假 null)。看 JSON 里 dev_prompt_outcome / dev_steer_outcome / test 的 baseline vs steer 分布。
5. **身份/配对正确**：paired diff d_i 是否 test_steer 与 test_baseline 在【同一批 item】上配对相减(不是错位/跨 axis)？bootstrap 是否 resample item 簇(每簇带其 k)。
6. **是否有任何 BLOCKER 会让这个负结果不可用**（例如 seed 未固定、某轴 items 实际条数≠冻结 N、C1 层选择退化导致 direction 无意义、test set 泄漏进 DEV 选择）。

只报不修不合并。输出 ranked findings(BLOCKER/MAJOR/MINOR/UNVERIFIED)+ file:line/JSON 路径 + 证据，并给明确 verdict 之一：
(A) VALID_NEGATIVE：合格负结果，可作为 KILL→Plan D 的证据入账；
(B) INVALID_NEGATIVE：仪器/判据有缺陷，负结果不可信，需返工(说明最小返工)。
另外单独回答关键科学问题：这个负结果更支持“非满射 claim(prompt 是强天花板，naive CAA latent 打不过)”，还是仅仅说明“我们的 CAA steering 方法太弱”？给出你从数据得到的判断与不确定性。

---

<sub>17s</sub>

### Copilot

先独立重建证据链：我会并行读取协议/源码/日志与原始 JSON，并用脚本重算判据与配对完整性，再给出分级审计结论。

---

<sub>24s</sub>

### `powershell`

**List target artifact files with sizes**

<details>
<summary>Arguments</summary>

```json
{
  "description": "List target artifact files with sizes",
  "command": "Set-Location 'C:\\Users\\v-elzhang\\Desktop\\MyFolder\\cognitive console'; Get-Item 'results\\c2b_adjudication_hf_2026-07-24\\c2b_adjudication_results.json','results\\c2b_adjudication_hf_2026-07-24\\c2b_adjudication_summary.md','results\\c2b_adjudication_hf_2026-07-24\\experiment-registry.yaml','results\\c2b_adjudication_hf_2026-07-24\\adj2.run.log','docs\\ledgers\\prereg-c2b-adjudication.md','src\\cognitive_console\\experiments\\adjudicate_c2b.py','scripts\\run_c2b_adjudication.py' | Select-Object FullName,Length | Format-Table -AutoSize"
}
```

</details>

<details>
<summary>10 lines</summary>

```
FullName
--------                                                                                                               
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\results\c2b_adjudication_hf_2026-07-24\c2b_adjudication_results.…
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\results\c2b_adjudication_hf_2026-07-24\c2b_adjudication_summary.…
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\results\c2b_adjudication_hf_2026-07-24\experiment-registry.yaml  
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\results\c2b_adjudication_hf_2026-07-24\adj2.run.log              
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\docs\ledgers\prereg-c2b-adjudication.md                          
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py              
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py
<shellId: 0 completed with exit code 0>
```

</details>


---

<sub>23s</sub>

### `view`

**view the file at C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\docs\ledgers\prereg-c2b-adjudication.md.**

C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\docs\ledgers\prereg-c2b-adjudication.md

<details>
<summary>120 lines</summary>

```
1. # PRE-REGISTRATION — C2b Behavioral-Gap Adjudication (RQ2 core)
2. 
3. - **Status:** **FROZEN 2026-07-23** (owner-confirmed decision rule §4 + parameters §5). Success/kill criteria
4.   and analysis plan MUST NOT change after seeing results (owner directive, AI-Instruction Part I §7/§12).
5. - **Adjudicates:** Claim **C2b** — "on tasks with headroom, latent steering reaches a BEHAVIORAL outcome
6.   beyond the best bounded-prompt outcome." A qualified NO → pivot to Plan D (RQ1-core measurement paper).
7. - **Why re-run:** the first C2b probe (E-0004) used audit-rejected lexical/length proxies that saturated the
8.   ceiling (~0.88–1.0) — INVALID evidence. This pre-registration fixes the instrument before adjudicating.
9. 
10. ---
11. 
12. ## 1. Instrument fixes (all four axes' issues addressed)
13. 
14. 1. **Eliminate the ceiling effect** — replace saturating lexical proxies with **behavioral-OUTCOME tasks
15.    that have real headroom** and require genuine capability change, not keyword presence:
16.    - **deliberation** → GSM8K-style multi-step arithmetic/reasoning: measure **accuracy** (0–1) with headroom.
17.    - **skepticism** → false-premise / sycophancy items: measure **false-premise-rejection rate**.
18.    - **uncertainty_awareness** → calibration items (questions the model often gets wrong): elicit answer +
19.      verbalized confidence; per-item outcome = **1 − Brier = 1 − (conf_i − correct_i)²** (proper scoring rule;
20.      per-item, cluster-bootstrappable). Binned ECE reported DESCRIPTIVELY only (not in the gate). This axis
21.      gets the MOST items (noisiest metric). *[Pre-run clarification D-0025: the original wording "(1−ECE)" was
22.      a SET metric with no per-item value; replaced with per-item (1−Brier). The improper 1−|correct−conf| is
23.      rejected (L1-optimal is reporting 0/1 → rewards overconfidence, reverses the axis). Pre-run spec fix, not
24.      a post-hoc criterion change; all other criteria unchanged.]*
25. 2. **Orthogonal, NON-lexical proxy** — the measure is a TASK OUTCOME (accuracy / rejection rate / calibration),
26.    scored by a rule/answer-key (deterministic), NOT a count of words the steering vector could inject.
27. 3. **Sample sizes + clustering (upgraded per owner):** **N = 60–80 items per axis** (uncertainty/ECE = 80;
28.    deliberation & skepticism = 60), **k = 5 samples/item**. **Bootstrap resamples at the ITEM level (cluster
29.    bootstrap), NOT at the sample level** — each item (with its k samples) is one cluster.
30. 4. **DEV/TEST split to remove selection bias (owner):** split each axis's items into a DEV pool (~1/3) and a
31.    disjoint TEST pool (~2/3), drawn from the same task distribution. **α is selected AND frozen on DEV only;
32.    the best-of-16 prompt is also selected on DEV only.** Adjudication is computed on TEST with the DEV-frozen
33.    α and DEV-selected prompt — eliminating the "best-of-7 α" and "best-of-16 prompt" selection bias for BOTH
34.    channels symmetrically.
35. 5. **Alpha sweep** over a documented grid (α selection on DEV), with a **coherence gate** (§3).
36. 6. **Drop focus** — no stable CAA direction / overshoots; excluded.
37. 
38. ## 2. Design
39. - Model: Qwen2.5-7B-Instruct (GPU fp16), same C1 chosen non-degenerate layer per axis (from E-0003).
40. - Steering vector = C1's re-derived CAA unit direction at the chosen layer (same extraction/split as E-0003).
41. - Per axis, on the TEST pool, compute per-item, at the DEV-frozen α and DEV-selected best prompt:
42.   - `prompt_i` = outcome of the DEV-selected best prompt on item i (mean over k samples).
43.   - `steer_i`  = outcome of steer-only at the DEV-frozen α on item i (mean over k samples).
44.   - **paired difference** `d_i = steer_i − prompt_i`.
45. - Conflict cells (prompt vs opposing steer) reported as SECONDARY/descriptive only.
46. 
47. ## 3. Coherence gate (prevents "steering wins by breaking the model")
48. A steered cell only counts if outputs remain coherent: pre-registered check = (mean output perplexity or a
49. simple degeneracy/ repetition score) stays within a factor of the unsteered baseline (exact bound set at
50. freeze). Gains achieved only above the coherence bound are DISCARDED.
51. 
52. ## 4. PRE-REGISTERED DECISION RULE — paired, multiplicity-corrected, three-tier (FROZEN after confirm)
53. 
54. **Per-axis test (paired cluster bootstrap — replaces the biased "non-overlapping independent CIs"):**
55. For each axis a, take the per-item paired differences `d_i = steer_i − prompt_i` on the TEST pool (α and
56. prompt frozen on DEV). Do a **cluster bootstrap resampling ITEMS** (each item = one cluster carrying its k
57. samples), B ≥ 10000 resamples, to get the CI of `mean_i(d_i)`.
58. An axis **PASSES (Bonferroni-corrected)** iff:
59.   (i) the **two-sided (1 − 0.05/3) ≈ 98.33% CI of mean(d) EXCLUDES 0** (family-wise correction over 3 axes), AND
60.   (ii) the **point estimate mean(d) ≥ δ**, AND
61.   (iii) the winning steer cell passes the **coherence gate** (§3).
62. > Rationale (owner): a paired test on per-item differences is far more powerful and avoids the systematic
63. > FALSE-KILL bias of comparing two independent non-overlapping CIs. Item-level clustering respects the k-sample
64. > nesting. Bonferroni over 3 axes controls false positives.
65. 
66. **Three-tier verdict:**
67. - **≥ 2 axes PASS (corrected) → STRONG GO.** RQ2 behavioral-gap supported (exploratory-confirmatory); continue
68.   the dual-channel line.
69. - **EXACTLY 1 axis PASSES (corrected) → CONDITIONAL GO.** Run a **pre-registered REPLICATION of that one axis**
70.   on fresh items (new DEV/TEST draw, new seed), same frozen rule. If it PASSES again → a **scope-narrowed RQ2
71.   claim limited to that axis**. If it does NOT replicate → **Plan D**.
72. - **0 axes PASS → KILL → Plan D** (RQ1-core measurement/diagnostic CHI paper). C1 evidence retained; C2b
73.   reported as an honest, qualified NEGATIVE.
74. 
75. **Conflict cells:** secondary/descriptive only — reported per axis+α, NOT part of the pass/fail decision.
76. 
77. **Why not simpler:** owner directive — a FALSE KILL is irreversible (permanently discards the core selling
78. point), and "non-overlapping CIs + N=30" biases toward false kill; the paired test + larger N guard against
79. false kill, while Bonferroni + the single-axis-must-replicate rule guard against a false positive.
80. 
81. ## 5. FROZEN parameters (confirmed by owner 2026-07-23)
82. - N items/axis: **deliberation 60, skepticism 60, uncertainty 80**; k = 5 samples/item.
83. - DEV/TEST split: ~1/3 DEV (α + best-prompt selection), ~2/3 TEST (adjudication), disjoint, same distribution.
84. - α grid (selected on DEV): {2, 4, 6, 8, 12, 16, 24}.
85. - δ (meaningful margin) = **0.05** in each axis's outcome units — meaning per axis: deliberation = +0.05
86.   accuracy; skepticism = +0.05 false-premise-rejection rate; uncertainty = +0.05 in **(1−Brier)** (per-item
87.   Brier scale; ECE reported descriptively only).
88. - Coherence gate: steered mean repetition/degeneracy score ≤ **1.5×** the unsteered baseline; cells above the
89.   bound are DISCARDED.
90. - Bootstrap: cluster (item-level), B ≥ 10000, two-sided; per-axis CI at **1 − 0.05/3** (Bonferroni).
91. - Decision: paired-diff CI excludes 0 AND point ≥ δ AND coherence-gate pass; three-tier verdict as in §4.
92. 
93. ### 5a. Pre-run generation-mechanics addendum (frozen 2026-07-24, D-0031 — PRE-RUN, no results seen)
94. These fix generation COMPUTE mechanics only; they do NOT touch the §4 statistical decision rule or the §5
95. statistical parameters (N, k, δ, α grid, DEV/TEST, Bonferroni, coherence, bootstrap). Recorded pre-run so they
96. are pre-registered, not post-hoc.
97. - **max_new_tokens = 64** (was an un-frozen default 256). Justification: the three tasks have SHORT answers —
98.   GSM8K final number, TruthfulQA MC letter, TriviaQA short answer + a verbalized confidence — so 64 new tokens
99.   is ample; 256 was overkill and 4× slower. Risk noted: 64 could truncate an unusually long chain; the answer
100.   parsers key on the final answer/MC letter/confidence, which fit well within 64. If any axis shows pervasive
101.   truncation of the keyed answer in the logs, that is reported as a limitation (not a criteria change).
102. - **batch_size = 16** (batched generation; audit-verified greedy batched == single-sequence EXACT on
103.   Qwen2.5-1.5B; sampled cells deterministic per fixed batch_size, which is now in the checkpoint fingerprint).
104. - **stall_timeout = 600s** (inactivity watchdog → hard-exit on a silent GPU/driver hang, per D-0029).
105. - **N unchanged = 60/60/80, k=5** — the hardened instrument runs the full frozen N in ~25–50 min, so no N
106.   reduction is needed. seed = 20260723 (as before).
107. - **Run must checkpoint/resume** (per-cell) and run on a machine we control OR a confirmed no-driver-maintenance
108.   window (D-0029 root cause).
109. 
110. ## 6. Freeze block
111. - protocol_frozen: **YES — frozen 2026-07-23 after owner confirmation of the §4 decision rule + §5 parameters.**
112. - After freeze: tasks, outcome proxies, DEV/TEST protocol, α grid, δ, coherence bound, bootstrap/clustering,
113.   Bonferroni level, and the three-tier decision rule are LOCKED. Results may NOT change these criteria.
114. - Freeze recorded in decision-log D-0024 with the commit hash.
115. 
116. ## 6. Budget (capped)
117. - Local first: implement qualified instrument + CPU/1.5B smoke + independent audit (free).
118. - Then ONE A800 allocation (<70GB disk, wipe after) for the 7B adjudication. Adjudicate immediately against
119.   the frozen criteria. No second GPU run (beyond a triggered single-axis replication) without a fresh human decision.
120.
```

</details>


---

<sub>23s</sub>

### `view`

**view the file at C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py.**

C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py

```
File too large to read at once (42.9 KB). Consider using the grep tool to search within the file, or view with view_range to read specific sections.
```


---

<sub>23s</sub>

### `view`

**view the file at C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py.**

C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py

```
File too large to read at once (28.7 KB). Consider using the grep tool to search within the file, or view with view_range to read specific sections.
```


---

<sub>28s</sub>

### `apply_patch`

<details>
<summary>Arguments</summary>

```json
"*** Begin Patch\n*** Add File: C:/Users/v-elzhang/.copilot/session-state/96bb4b1c-cb6c-4a5a-904f-e44b0ee6beca/plan.md\n+1) 读取冻结协议、源码、运行日志与原始 JSON，建立“应然判据”与“实然产物”对照表。  \n+2) 独立重算三轴 pass/fail 与总 verdict（Bonferroni CI + δ + coherence），核对是否误判。  \n+3) 审查仪器有效性：生成次数、逐 cell 完成、watchdog/异常、C1 复算一致性。  \n+4) 审查负结果有效性：degeneracy/coherence、outcome 分布、配对与 bootstrap 聚类是否按 item。  \n+5) 输出 hostile audit：分级 findings（含证据路径）+ A/B 最终裁决 + 科学解释（非满射 vs 方法弱）。  \n*** End Patch\n"
```

</details>

```
Added 1 file(s): C:\Users\v-elzhang\.copilot\session-state\96bb4b1c-cb6c-4a5a-904f-e44b0ee6beca\plan.md
```


---

<sub>33s</sub>

### `view`

**view the file at C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\results\c2b_adjudication_hf_2026-07-24\c2b_adjudication_summary.md.**

C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\results\c2b_adjudication_hf_2026-07-24\c2b_adjudication_summary.md

<details>
<summary>23 lines</summary>

```
1. # C2b QUALIFIED Adjudication — FROZEN instrument (prereg §4/§5)
2. 
3. - verdict: **KILL_PLAN_D**
4. - model: `/root/autodl-tmp/models/Qwen2.5-7B-Instruct`   backend: `hf`   valid_for_paper: **False**
5. - run_type: **exploratory**   bootstrap_B: 10000   CI level: 0.98333 (Bonferroni 1−0.05/3)
6. - δ = 0.05   α grid: [2.0, 4.0, 6.0, 8.0, 12.0, 16.0, 24.0]
7. 
8. | axis | layer | frozen α | best prompt | n_dev | n_test | mean(d) | CI | coherence | PASS |
9. |---|---|---|---|---|---|---|---|---|---|
10. | deliberation | 20 | 2.0 | delib-strong-09 | 20 | 40 | +0.015 | [-0.040, +0.070] | ok | no |
11. | skepticism | 20 | 6.0 | skep-strong-06 | 20 | 40 | -0.080 | [-0.225, +0.045] | ok | no |
12. | uncertainty_awareness | 20 | 8.0 | unc-strong-01 | 27 | 53 | -0.228 | [-0.370, -0.092] | ok | no |
13. 
14. - axes passing (Bonferroni): **0/3** -> **KILL_PLAN_D**
15. 
16. ## Conflict cells (SECONDARY / descriptive only — NOT part of the verdict)
17. 
18. | axis | opposite α | mean conflict outcome | mean prompt-pole | latent drags down? |
19. |---|---|---|---|---|
20. | deliberation | -2.0 | 0.030 | 0.020 | False |
21. | skepticism | -6.0 | 0.775 | 0.775 | False |
22. | uncertainty_awareness | -8.0 | 0.841 | 0.848 | True |
23.
```

</details>


---

<sub>33s</sub>

### `view`

**view the file at C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\results\c2b_adjudication_hf_2026-07-24\experiment-registry.yaml.**

C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\results\c2b_adjudication_hf_2026-07-24\experiment-registry.yaml

<details>
<summary>64 lines</summary>

```
1. experiments:
2. - experiment_id: c2b-adj-deac6326-0001
3.   parent: null
4.   hypothesis_id: H2
5.   claim_ids:
6.   - C2b
7.   type: exploratory
8.   status: done
9.   code_commit: 9150cbfae6be7df695932fbf5cb9904b48cf0c75
10.   dirty_tree: null
11.   data_hash: null
12.   env_hash: null
13.   config_hash: sha256:deac6326721218c3d2decc89b5d101e06a37dccfa049e05b69d053e2169b7749
14.   model: /root/autodl-tmp/models/Qwen2.5-7B-Instruct
15.   dataset: data/c2b_tasks/* (fixtures) or deferred real loaders
16.   seed: 20260723
17.   hardware: cuda-float16
18.   started_at: '2026-07-24T05:27:18.922433+00:00'
19.   ended_at: '2026-07-24T05:56:11.182326+00:00'
20.   exit_code: 0
21.   raw_metrics: null
22.   summary_metrics:
23.     deliberation:
24.       layer: 20
25.       frozen_alpha: 2.0
26.       mean_diff: 0.015000000000000003
27.       ci_lo: -0.04
28.       ci_hi: 0.06999999999999999
29.       ci_level: 0.9833333333333333
30.       coherence_ok: true
31.       passed: false
32.     skepticism:
33.       layer: 20
34.       frozen_alpha: 6.0
35.       mean_diff: -0.08
36.       ci_lo: -0.225
37.       ci_hi: 0.045
38.       ci_level: 0.9833333333333333
39.       coherence_ok: true
40.       passed: false
41.     uncertainty_awareness:
42.       layer: 20
43.       frozen_alpha: 8.0
44.       mean_diff: -0.22767283018867926
45.       ci_lo: -0.36977938679245265
46.       ci_hi: -0.0916042641509434
47.       ci_level: 0.9833333333333333
48.       coherence_ok: true
49.       passed: false
50.     _verdict: KILL_PLAN_D
51.     _axis_passes:
52.       deliberation: false
53.       skepticism: false
54.       uncertainty_awareness: false
55.     _torch_seed: 20260723
56.   artifacts:
57.   - results/c2b_adjudication_hf_2026-07-24/c2b_adjudication_results.json
58.   failure_reason: null
59.   valid_for_paper: false
60.   validation_notes: C2b QUALIFIED adjudication implementing FROZEN prereg §4/§5 (paired
61.     ITEM-cluster bootstrap B>=10000, Bonferroni CI 1-0.05/3, delta=0.05, coherence<=1.5x,
62.     three-tier verdict). EXPLORATORY until the A800 7B run (valid_for_paper=false);
63.     this run is a exploratory on hf.
64.
```

</details>


---

<sub>33s</sub>

### `view`

**view the file at C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\results\c2b_adjudication_hf_2026-07-24\adj2.run.log.**

C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\results\c2b_adjudication_hf_2026-07-24\adj2.run.log (lines 1-220)

<details>
<summary>135 lines</summary>

```
1. 设置成功!
2. 注意：
3. 1. 仅限学术用途和加速访问github/huggingface，不承诺稳定性
4. 2. 开启加速后对访问其他资源如pip源等会*更慢*
5. ADJ2_START Fri Jul 24 13:27:18 CST 2026
6. [c2b-adj] disk pre-run: disk ok: total 0.18GB < budget 60GB (ceiling 70GB) [/root/autodl-tmp/hf_home=0.18GB].
7. [c1] system-available RAM at start: 488562 MB (watchdog floor 0 MB)
8. Loading weights:   0%|          | 0/339 [00:00<?, ?it/s]Loading weights:   0%|          | 1/339 [00:00<03:58,  1.42it/s]Loading weights:  15%|█▌        | 52/339 [00:00<00:04, 66.36it/s]Loading weights:  19%|█▉        | 66/339 [00:01<00:03, 76.46it/s]Loading weights:  26%|██▌       | 88/339 [00:01<00:02, 86.68it/s]Loading weights:  29%|██▉       | 100/339 [00:01<00:02, 92.16it/s]Loading weights:  33%|███▎      | 112/339 [00:01<00:02, 82.96it/s]Loading weights:  37%|███▋      | 124/339 [00:01<00:02, 88.42it/s]Loading weights:  40%|████      | 137/339 [00:01<00:02, 81.04it/s]Loading weights:  44%|████▍     | 150/339 [00:02<00:02, 77.60it/s]Loading weights:  51%|█████     | 172/339 [00:02<00:01, 85.90it/s]Loading weights:  55%|█████▍    | 186/339 [00:02<00:01, 96.04it/s]Loading weights:  58%|█████▊    | 197/339 [00:02<00:01, 98.52it/s]Loading weights:  61%|██████▏   | 208/339 [00:02<00:01, 85.27it/s]Loading weights:  65%|██████▍   | 220/339 [00:02<00:01, 90.15it/s]Loading weights:  69%|██████▊   | 233/339 [00:02<00:01, 81.54it/s]Loading weights:  72%|███████▏  | 245/339 [00:03<00:01, 89.56it/s]Loading weights:  76%|███████▌  | 257/339 [00:03<00:00, 95.80it/s]Loading weights:  79%|███████▉  | 269/339 [00:03<00:00, 101.36it/s]Loading weights:  83%|████████▎ | 280/339 [00:03<00:00, 83.34it/s] Loading weights:  86%|████████▌ | 292/339 [00:03<00:00, 90.86it/s]Loading weights:  90%|████████▉ | 304/339 [00:03<00:00, 96.23it/s]Loading weights:  93%|█████████▎| 316/339 [00:03<00:00, 83.55it/s]Loading weights:  97%|█████████▋| 328/339 [00:04<00:00, 89.65it/s]Loading weights: 100%|██████████| 339/339 [00:04<00:00, 84.68it/s]
9. [c1] model=/root/autodl-tmp/models/Qwen2.5-7B-Instruct hidden_dim=3584 layers=0..28 scan=[2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28]
10. [c1] axis=deliberation             layer= 20(stable) prompt_reach= 10.425 pole_reach= 17.875 ratio= 0.583 CI=[0.488,0.681] extract_ok=True seed_stable=True c1=True  (5.8s)
11. [c1] axis=skepticism               layer= 20(stable) prompt_reach= 11.491 pole_reach= 20.980 ratio= 0.548 CI=[0.434,0.670] extract_ok=True seed_stable=True c1=True  (5.1s)
12. [c1] axis=uncertainty_awareness    layer= 20(stable) prompt_reach= 15.196 pole_reach= 21.305 ratio= 0.713 CI=[0.518,0.910] extract_ok=True seed_stable=True c1=True  (5.1s)
13. Loading weights:   0%|          | 0/339 [00:00<?, ?it/s]Loading weights:   0%|          | 1/339 [00:00<04:34,  1.23it/s]Loading weights:  15%|█▌        | 52/339 [00:00<00:04, 68.43it/s]Loading weights:  20%|██        | 69/339 [00:01<00:03, 83.14it/s]Loading weights:  25%|██▌       | 85/339 [00:01<00:03, 82.83it/s]Loading weights:  29%|██▉       | 100/339 [00:01<00:03, 70.89it/s]Loading weights:  33%|███▎      | 113/339 [00:01<00:02, 78.98it/s]Loading weights:  37%|███▋      | 126/339 [00:01<00:02, 76.03it/s]Loading weights:  40%|████      | 136/339 [00:01<00:02, 80.21it/s]Loading weights:  44%|████▎     | 148/339 [00:02<00:02, 88.34it/s]Loading weights:  47%|████▋     | 160/339 [00:02<00:01, 94.53it/s]Loading weights:  51%|█████     | 172/339 [00:02<00:01, 100.11it/s]Loading weights:  54%|█████▍    | 184/339 [00:02<00:01, 103.42it/s]Loading weights:  58%|█████▊    | 196/339 [00:02<00:01, 86.20it/s] Loading weights:  61%|██████▏   | 208/339 [00:02<00:01, 93.41it/s]Loading weights:  65%|██████▍   | 220/339 [00:02<00:01, 81.58it/s]Loading weights:  68%|██████▊   | 232/339 [00:03<00:01, 88.29it/s]Loading weights:  72%|███████▏  | 244/339 [00:03<00:00, 95.12it/s]Loading weights:  76%|███████▌  | 256/339 [00:03<00:01, 82.44it/s]Loading weights:  79%|███████▉  | 268/339 [00:03<00:00, 90.26it/s]Loading weights:  83%|████████▎ | 280/339 [00:03<00:00, 81.55it/s]Loading weights:  86%|████████▌ | 292/339 [00:03<00:00, 87.98it/s]Loading weights:  90%|████████▉ | 304/339 [00:03<00:00, 94.12it/s]Loading weights:  93%|█████████▎| 316/339 [00:03<00:00, 99.58it/s]Loading weights:  97%|█████████▋| 328/339 [00:04<00:00, 84.23it/s]Loading weights: 100%|██████████| 339/339 [00:04<00:00, 82.61it/s]
14. Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
15. [c2b-adj] disk post-C1 (model loaded): disk ok: total 0.18GB < budget 60GB (ceiling 70GB) [/root/autodl-tmp/hf_home=0.18GB].
16. [c2b-adj] PLANNED generations (upper bound): deliberation=3400, skepticism=3400, uncertainty_awareness=4565  TOTAL=11365
17. [c2b-adj] budget: batch_size=16 max_new_tokens=64 -> ~711 batches; rough wall-clock ~0.40-0.79h (assuming ~2-4 s/batch on the target GPU; SANITY-CHECK before committing GPU time).
18. [c2b-adj] checkpoints: results/c2b_adjudication_hf_2026-07-24/checkpoints  (fresh=False; resume auto-skips cells whose config matches)
19. [c2b-adj] axis=deliberation phase=dev_prompt 1/16 items=20 START done=0/11365 fresh=0 elapsed=0s eta=0s
20. Loading weights:   0%|          | 0/339 [00:00<?, ?it/s]Loading weights:   0%|          | 1/339 [00:00<05:04,  1.11it/s]Loading weights:  15%|█▌        | 52/339 [00:01<00:04, 69.51it/s]Loading weights:  23%|██▎       | 79/339 [00:01<00:03, 70.43it/s]Loading weights:  29%|██▉       | 100/339 [00:01<00:03, 77.93it/s]Loading weights:  34%|███▍      | 115/339 [00:01<00:02, 78.29it/s]Loading weights:  38%|███▊      | 128/339 [00:01<00:02, 83.36it/s]Loading weights:  41%|████▏     | 140/339 [00:02<00:02, 79.27it/s]Loading weights:  45%|████▍     | 151/339 [00:02<00:02, 81.75it/s]Loading weights:  48%|████▊     | 162/339 [00:02<00:02, 87.02it/s]Loading weights:  54%|█████▍    | 184/339 [00:02<00:01, 81.88it/s]Loading weights:  58%|█████▊    | 196/339 [00:02<00:01, 88.57it/s]Loading weights:  61%|██████▏   | 208/339 [00:02<00:01, 94.18it/s]Loading weights:  65%|██████▌   | 221/339 [00:02<00:01, 86.52it/s]Loading weights:  68%|██████▊   | 232/339 [00:03<00:01, 90.10it/s]Loading weights:  72%|███████▏  | 244/339 [00:03<00:01, 94.86it/s]Loading weights:  76%|███████▌  | 256/339 [00:03<00:00, 99.05it/s]Loading weights:  79%|███████▉  | 268/339 [00:03<00:00, 86.44it/s]Loading weights:  83%|████████▎ | 280/339 [00:03<00:00, 91.89it/s]Loading weights:  86%|████████▌ | 292/339 [00:03<00:00, 97.19it/s]Loading weights:  90%|████████▉ | 304/339 [00:03<00:00, 83.54it/s]Loading weights:  94%|█████████▎| 317/339 [00:04<00:00, 92.26it/s]Loading weights:  97%|█████████▋| 328/339 [00:04<00:00, 81.17it/s]Loading weights: 100%|██████████| 339/339 [00:04<00:00, 80.73it/s]
21. [c2b-adj] axis=deliberation phase=dev_prompt 1/16 items=20 DONE done=100/11365 fresh=100 elapsed=26s eta=2947s
22. [c2b-adj] axis=deliberation phase=dev_prompt 2/16 items=20 START done=100/11365 fresh=100 elapsed=26s eta=2947s
23. [c2b-adj] axis=deliberation phase=dev_prompt 2/16 items=20 DONE done=200/11365 fresh=200 elapsed=41s eta=2309s
24. [c2b-adj] axis=deliberation phase=dev_prompt 3/16 items=20 START done=200/11365 fresh=200 elapsed=41s eta=2309s
25. [c2b-adj] axis=deliberation phase=dev_prompt 3/16 items=20 DONE done=300/11365 fresh=300 elapsed=57s eta=2087s
26. [c2b-adj] axis=deliberation phase=dev_prompt 4/16 items=20 START done=300/11365 fresh=300 elapsed=57s eta=2087s
27. [c2b-adj] axis=deliberation phase=dev_prompt 4/16 items=20 DONE done=400/11365 fresh=400 elapsed=72s eta=1971s
28. [c2b-adj] axis=deliberation phase=dev_prompt 5/16 items=20 START done=400/11365 fresh=400 elapsed=72s eta=1971s
29. [c2b-adj] axis=deliberation phase=dev_prompt 5/16 items=20 DONE done=500/11365 fresh=500 elapsed=87s eta=1892s
30. [c2b-adj] axis=deliberation phase=dev_prompt 6/16 items=20 START done=500/11365 fresh=500 elapsed=87s eta=1892s
31. [c2b-adj] axis=deliberation phase=dev_prompt 6/16 items=20 DONE done=600/11365 fresh=600 elapsed=102s eta=1835s
32. [c2b-adj] axis=deliberation phase=dev_prompt 7/16 items=20 START done=600/11365 fresh=600 elapsed=102s eta=1835s
33. [c2b-adj] axis=deliberation phase=dev_prompt 7/16 items=20 DONE done=700/11365 fresh=700 elapsed=118s eta=1791s
34. [c2b-adj] axis=deliberation phase=dev_prompt 8/16 items=20 START done=700/11365 fresh=700 elapsed=118s eta=1791s
35. [c2b-adj] axis=deliberation phase=dev_prompt 8/16 items=20 DONE done=800/11365 fresh=800 elapsed=133s eta=1753s
36. [c2b-adj] axis=deliberation phase=dev_prompt 9/16 items=20 START done=800/11365 fresh=800 elapsed=133s eta=1753s
37. [c2b-adj] axis=deliberation phase=dev_prompt 9/16 items=20 DONE done=900/11365 fresh=900 elapsed=148s eta=1721s
38. [c2b-adj] axis=deliberation phase=dev_prompt 10/16 items=20 START done=900/11365 fresh=900 elapsed=148s eta=1721s
39. [c2b-adj] axis=deliberation phase=dev_prompt 10/16 items=20 DONE done=1000/11365 fresh=1000 elapsed=163s eta=1692s
40. [c2b-adj] axis=deliberation phase=dev_prompt 11/16 items=20 START done=1000/11365 fresh=1000 elapsed=163s eta=1692s
41. [c2b-adj] axis=deliberation phase=dev_prompt 11/16 items=20 DONE done=1100/11365 fresh=1100 elapsed=179s eta=1666s
42. [c2b-adj] axis=deliberation phase=dev_prompt 12/16 items=20 START done=1100/11365 fresh=1100 elapsed=179s eta=1666s
43. [c2b-adj] axis=deliberation phase=dev_prompt 12/16 items=20 DONE done=1200/11365 fresh=1200 elapsed=194s eta=1642s
44. [c2b-adj] axis=deliberation phase=dev_prompt 13/16 items=20 START done=1200/11365 fresh=1200 elapsed=194s eta=1642s
45. [c2b-adj] axis=deliberation phase=dev_prompt 13/16 items=20 DONE done=1300/11365 fresh=1300 elapsed=209s eta=1618s
46. [c2b-adj] axis=deliberation phase=dev_prompt 14/16 items=20 START done=1300/11365 fresh=1300 elapsed=209s eta=1618s
47. [c2b-adj] axis=deliberation phase=dev_prompt 14/16 items=20 DONE done=1400/11365 fresh=1400 elapsed=224s eta=1596s
48. [c2b-adj] axis=deliberation phase=dev_prompt 15/16 items=20 START done=1400/11365 fresh=1400 elapsed=224s eta=1596s
49. [c2b-adj] axis=deliberation phase=dev_prompt 15/16 items=20 DONE done=1500/11365 fresh=1500 elapsed=240s eta=1576s
50. [c2b-adj] axis=deliberation phase=dev_prompt 16/16 items=20 START done=1500/11365 fresh=1500 elapsed=240s eta=1576s
51. [c2b-adj] axis=deliberation phase=dev_prompt 16/16 items=20 DONE done=1600/11365 fresh=1600 elapsed=255s eta=1558s
52. [c2b-adj] axis=deliberation phase=dev_baseline 1/1 items=20 START done=1600/11365 fresh=1600 elapsed=255s eta=1558s
53. [c2b-adj] axis=deliberation phase=dev_baseline 1/1 items=20 DONE done=1700/11365 fresh=1700 elapsed=270s eta=1536s
54. [c2b-adj] axis=deliberation phase=dev_alpha 1/7 items=20 START done=1700/11365 fresh=1700 elapsed=270s eta=1536s
55. [c2b-adj] axis=deliberation phase=dev_alpha 1/7 items=20 DONE done=1800/11365 fresh=1800 elapsed=285s eta=1516s
56. [c2b-adj] axis=deliberation phase=dev_alpha 2/7 items=20 START done=1800/11365 fresh=1800 elapsed=285s eta=1516s
57. [c2b-adj] axis=deliberation phase=dev_alpha 2/7 items=20 DONE done=1900/11365 fresh=1900 elapsed=301s eta=1497s
58. [c2b-adj] axis=deliberation phase=dev_alpha 3/7 items=20 START done=1900/11365 fresh=1900 elapsed=301s eta=1497s
59. [c2b-adj] axis=deliberation phase=dev_alpha 3/7 items=20 DONE done=2000/11365 fresh=2000 elapsed=316s eta=1478s
60. [c2b-adj] axis=deliberation phase=dev_alpha 4/7 items=20 START done=2000/11365 fresh=2000 elapsed=316s eta=1478s
61. [c2b-adj] axis=deliberation phase=dev_alpha 4/7 items=20 DONE done=2100/11365 fresh=2100 elapsed=331s eta=1460s
62. [c2b-adj] axis=deliberation phase=dev_alpha 5/7 items=20 START done=2100/11365 fresh=2100 elapsed=331s eta=1460s
63. [c2b-adj] axis=deliberation phase=dev_alpha 5/7 items=20 DONE done=2200/11365 fresh=2200 elapsed=346s eta=1441s
64. [c2b-adj] axis=deliberation phase=dev_alpha 6/7 items=20 START done=2200/11365 fresh=2200 elapsed=346s eta=1441s
65. [c2b-adj] axis=deliberation phase=dev_alpha 6/7 items=20 DONE done=2300/11365 fresh=2300 elapsed=361s eta=1424s
66. [c2b-adj] axis=deliberation phase=dev_alpha 7/7 items=20 START done=2300/11365 fresh=2300 elapsed=361s eta=1424s
67. [c2b-adj] axis=deliberation phase=dev_alpha 7/7 items=20 DONE done=2400/11365 fresh=2400 elapsed=376s eta=1406s
68. [c2b-adj] axis=deliberation phase=test_prompt 1/1 items=40 START done=2400/11365 fresh=2400 elapsed=376s eta=1406s
69. [c2b-adj] axis=deliberation phase=test_prompt 1/1 items=40 DONE done=2600/11365 fresh=2600 elapsed=407s eta=1372s
70. [c2b-adj] axis=deliberation phase=test_steer 1/1 items=40 START done=2600/11365 fresh=2600 elapsed=407s eta=1372s
71. [c2b-adj] axis=deliberation phase=test_steer 1/1 items=40 DONE done=2800/11365 fresh=2800 elapsed=438s eta=1338s
72. [c2b-adj] axis=deliberation phase=test_baseline 1/1 items=40 START done=2800/11365 fresh=2800 elapsed=438s eta=1338s
73. [c2b-adj] axis=deliberation phase=test_baseline 1/1 items=40 DONE done=3000/11365 fresh=3000 elapsed=467s eta=1303s
74. [c2b-adj] axis=deliberation phase=conflict 1/1 items=40 START done=3000/11365 fresh=3000 elapsed=467s eta=1303s
75. [c2b-adj] axis=deliberation phase=conflict 1/1 items=40 DONE done=3200/11365 fresh=3200 elapsed=505s eta=1288s
76. [c2b-adj] axis=deliberation phase=conflict_pole 1/1 items=40 START done=3200/11365 fresh=3200 elapsed=505s eta=1288s
77. [c2b-adj] axis=deliberation phase=conflict_pole 1/1 items=40 DONE done=3400/11365 fresh=3400 elapsed=542s eta=1270s
78. [c2b-adj] axis=skepticism phase=dev_prompt 1/16 items=20 START done=3400/11365 fresh=3400 elapsed=542s eta=1270s
79. [c2b-adj] axis=skepticism phase=dev_prompt 1/16 items=20 DONE done=3500/11365 fresh=3500 elapsed=561s eta=1261s
80. [c2b-adj] axis=skepticism phase=dev_prompt 2/16 items=20 START done=3500/11365 fresh=3500 elapsed=561s eta=1261s
81. [c2b-adj] axis=skepticism phase=dev_prompt 2/16 items=20 DONE done=3600/11365 fresh=3600 elapsed=580s eta=1252s
82. [c2b-adj] axis=skepticism phase=dev_prompt 3/16 items=20 START done=3600/11365 fresh=3600 elapsed=580s eta=1252s
83. [c2b-adj] axis=skepticism phase=dev_prompt 3/16 items=20 DONE done=3700/11365 fresh=3700 elapsed=597s eta=1237s
84. [c2b-adj] axis=skepticism phase=dev_prompt 4/16 items=20 START done=3700/11365 fresh=3700 elapsed=597s eta=1237s
85. [c2b-adj] axis=skepticism phase=dev_prompt 4/16 items=20 DONE done=3800/11365 fresh=3800 elapsed=613s eta=1221s
86. [c2b-adj] axis=skepticism phase=dev_prompt 5/16 items=20 START done=3800/11365 fresh=3800 elapsed=613s eta=1221s
87. [c2b-adj] axis=skepticism phase=dev_prompt 5/16 items=20 DONE done=3900/11365 fresh=3900 elapsed=630s eta=1205s
88. [c2b-adj] axis=skepticism phase=dev_prompt 6/16 items=20 START done=3900/11365 fresh=3900 elapsed=630s eta=1205s
89. [c2b-adj] axis=skepticism phase=dev_prompt 6/16 items=20 DONE done=4000/11365 fresh=4000 elapsed=644s eta=1187s
90. [c2b-adj] axis=skepticism phase=dev_prompt 7/16 items=20 START done=4000/11365 fresh=4000 elapsed=644s eta=1187s
91. [c2b-adj] axis=skepticism phase=dev_prompt 7/16 items=20 DONE done=4100/11365 fresh=4100 elapsed=661s eta=1171s
92. [c2b-adj] axis=skepticism phase=dev_prompt 8/16 items=20 START done=4100/11365 fresh=4100 elapsed=661s eta=1171s
93. [c2b-adj] axis=skepticism phase=dev_prompt 8/16 items=20 DONE done=4200/11365 fresh=4200 elapsed=677s eta=1155s
94. [c2b-adj] axis=skepticism phase=dev_prompt 9/16 items=20 START done=4200/11365 fresh=4200 elapsed=677s eta=1155s
95. [c2b-adj] axis=skepticism phase=dev_prompt 9/16 items=20 DONE done=4300/11365 fresh=4300 elapsed=693s eta=1139s
96. [c2b-adj] axis=skepticism phase=dev_prompt 10/16 items=20 START done=4300/11365 fresh=4300 elapsed=693s eta=1139s
97. [c2b-adj] axis=skepticism phase=dev_prompt 10/16 items=20 DONE done=4400/11365 fresh=4400 elapsed=709s eta=1123s
98. [c2b-adj] axis=skepticism phase=dev_prompt 11/16 items=20 START done=4400/11365 fresh=4400 elapsed=709s eta=1123s
99. [c2b-adj] axis=skepticism phase=dev_prompt 11/16 items=20 DONE done=4500/11365 fresh=4500 elapsed=726s eta=1107s
100. [c2b-adj] axis=skepticism phase=dev_prompt 12/16 items=20 START done=4500/11365 fresh=4500 elapsed=726s eta=1107s
101. [c2b-adj] axis=skepticism phase=dev_prompt 12/16 items=20 DONE done=4600/11365 fresh=4600 elapsed=742s eta=1091s
102. [c2b-adj] axis=skepticism phase=dev_prompt 13/16 items=20 START done=4600/11365 fresh=4600 elapsed=742s eta=1091s
103. [c2b-adj] axis=skepticism phase=dev_prompt 13/16 items=20 DONE done=4700/11365 fresh=4700 elapsed=758s eta=1075s
104. [c2b-adj] axis=skepticism phase=dev_prompt 14/16 items=20 START done=4700/11365 fresh=4700 elapsed=758s eta=1075s
105. [c2b-adj] axis=skepticism phase=dev_prompt 14/16 items=20 DONE done=4800/11365 fresh=4800 elapsed=774s eta=1059s
106. [c2b-adj] axis=skepticism phase=dev_prompt 15/16 items=20 START done=4800/11365 fresh=4800 elapsed=774s eta=1059s
107. [c2b-adj] axis=skepticism phase=dev_prompt 15/16 items=20 DONE done=4900/11365 fresh=4900 elapsed=788s eta=1040s
108. [c2b-adj] axis=skepticism phase=dev_prompt 16/16 items=20 START done=4900/11365 fresh=4900 elapsed=788s eta=1040s
109. [c2b-adj] axis=skepticism phase=dev_prompt 16/16 items=20 DONE done=5000/11365 fresh=5000 elapsed=805s eta=1024s
110. [c2b-adj] axis=skepticism phase=dev_baseline 1/1 items=20 START done=5000/11365 fresh=5000 elapsed=805s eta=1024s
111. [c2b-adj] axis=skepticism phase=dev_baseline 1/1 items=20 DONE done=5100/11365 fresh=5100 elapsed=817s eta=1004s
112. [c2b-adj] axis=skepticism phase=dev_alpha 1/7 items=20 START done=5100/11365 fresh=5100 elapsed=817s eta=1004s
113. [c2b-adj] axis=skepticism phase=dev_alpha 1/7 items=20 DONE done=5200/11365 fresh=5200 elapsed=830s eta=984s
114. [c2b-adj] axis=skepticism phase=dev_alpha 2/7 items=20 START done=5200/11365 fresh=5200 elapsed=830s eta=984s
115. [c2b-adj] axis=skepticism phase=dev_alpha 2/7 items=20 DONE done=5300/11365 fresh=5300 elapsed=842s eta=963s
116. [c2b-adj] axis=skepticism phase=dev_alpha 3/7 items=20 START done=5300/11365 fresh=5300 elapsed=842s eta=963s
117. [c2b-adj] axis=skepticism phase=dev_alpha 3/7 items=20 DONE done=5400/11365 fresh=5400 elapsed=855s eta=944s
118. [c2b-adj] axis=skepticism phase=dev_alpha 4/7 items=20 START done=5400/11365 fresh=5400 elapsed=855s eta=944s
119. [c2b-adj] axis=skepticism phase=dev_alpha 4/7 items=20 DONE done=5500/11365 fresh=5500 elapsed=869s eta=927s
120. [c2b-adj] axis=skepticism phase=dev_alpha 5/7 items=20 START done=5500/11365 fresh=5500 elapsed=869s eta=927s
121. [c2b-adj] axis=skepticism phase=dev_alpha 5/7 items=20 DONE done=5600/11365 fresh=5600 elapsed=884s eta=910s
122. [c2b-adj] axis=skepticism phase=dev_alpha 6/7 items=20 START done=5600/11365 fresh=5600 elapsed=884s eta=910s
123. [c2b-adj] axis=skepticism phase=dev_alpha 6/7 items=20 DONE done=5700/11365 fresh=5700 elapsed=899s eta=893s
124. [c2b-adj] axis=skepticism phase=dev_alpha 7/7 items=20 START done=5700/11365 fresh=5700 elapsed=899s eta=893s
125. [c2b-adj] axis=skepticism phase=dev_alpha 7/7 items=20 DONE done=5800/11365 fresh=5800 elapsed=913s eta=876s
126. [c2b-adj] axis=skepticism phase=test_prompt 1/1 items=40 START done=5800/11365 fresh=5800 elapsed=913s eta=876s
127. [c2b-adj] axis=skepticism phase=test_prompt 1/1 items=40 DONE done=6000/11365 fresh=6000 elapsed=945s eta=845s
128. [c2b-adj] axis=skepticism phase=test_steer 1/1 items=40 START done=6000/11365 fresh=6000 elapsed=945s eta=845s
129. [c2b-adj] axis=skepticism phase=test_steer 1/1 items=40 DONE done=6200/11365 fresh=6200 elapsed=965s eta=804s
130. [c2b-adj] axis=skepticism phase=test_baseline 1/1 items=40 START done=6200/11365 fresh=6200 elapsed=965s eta=804s
131. [c2b-adj] axis=skepticism phase=test_baseline 1/1 items=40 DONE done=6400/11365 fresh=6400 elapsed=982s eta=762s
132. [c2b-adj] axis=skepticism phase=conflict 1/1 items=40 START done=6400/11365 fresh=6400 elapsed=982s eta=762s
133. [c2b-adj] axis=skepticism phase=conflict 1/1 items=40 DONE done=6600/11365 fresh=6600 elapsed=1014s eta=732s
134. [c2b-adj] axis=skepticism phase=c

[Output truncated. Use view_range=[135, ...] to continue reading. In your next response, you may batch this with other view calls. File has at least 200 lines.]
```

</details>


---

<sub>33s</sub>

### `rg`

**def |class |delta|bonf|bootstrap|coherence|degener|verdict|paired|cluster|seed|alpha|CI|confidence|watchdog|stall**

"def |class |delta|bonf|bootstrap|coherence|degener|verdict|paired|cluster|seed|alpha|CI|confidence|watchdog|stall" (src\cognitive_console\experiments\adjudicate_c2b.py)

<details>
<summary>6 matches</summary>

```
Output too large to read at once (41.5 KB). Saved to: C:\Users\V-ELZH~1\AppData\Local\Temp\copilot-tool-output-1784872967330-1.txt
Consider using tools like rg (for searching), head/tail (for viewing start/end), view with view_range (for specific sections), or jq (for JSON) to examine portions of the output.

Preview (first 500 chars):
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:6:BEHAVIORAL outcome beyond the best bounded-prompt outcome" — with a paired,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:16:* coherence ≤ 1.5× baseline         -> ``COHERENCE_MAX_RATIO`` + gate       (§3/§5)
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:17:* cluster bo
```

</details>


---

<sub>33s</sub>

### `rg`

**adjudicat|seed|alpha|stall|max_new_tokens|batch_size|run|resume**

"adjudicat|seed|alpha|stall|max_new_tokens|batch_size|run|resume" (scripts\run_c2b_adjudication.py)

<details>
<summary>103 matches</summary>

```
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:1:"""C2b QUALIFIED adjudication runner — FROZEN instrument (prereg §4/§5).
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:3:Runs the pre-registered, three-tier C2b behavioral-gap adjudication:
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:16:  that layer on the RUN's model (never hardcoded), reuses the disk guard, and runs
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:17:  the adjudication with sampled (k=5) generation.
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:19:EVERYTHING is EXPLORATORY until the A800 7B run: valid_for_paper=false, honest
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:47:from cognitive_console.experiments import adjudicate_c2b as adj
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:48:from cognitive_console.experiments.adjudicate_c2b import (
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:59:from scripts import run_c1_facade as c1
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:60:from scripts import run_gpu_phase0 as p0
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:78:    """Stable hash of everything that affects generated outcomes, so a resumed run
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:79:    only reuses checkpoints from an IDENTICAL config (seed/model/N/items/gen knobs).
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:80:    Changing max_new_tokens, temperature, seed, model, or the item set invalidates
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:81:    resume (fresh generations), keeping the frozen verdict faithful."""
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:83:        "seed": int(args.seed),
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:86:        "max_new_tokens": int(args.max_new_tokens),
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:88:        # batch_size changes the chunk composition, hence each chunk's derived
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:89:        # batch_seed and RNG stream, hence the sampled outcomes — so it MUST be in
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:94:        "batch_size": int(args.batch_size),
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:97:        "alpha_grid": list(adj.ALPHA_GRID),
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:128:def watchdog_should_abort(last_activity_ts: float, stall_timeout: float,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:130:    """Pure, testable stall decision: True iff more than ``stall_timeout`` seconds
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:131:    have elapsed since ``last_activity_ts``. ``stall_timeout <= 0`` disables the
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:132:    watchdog (never aborts). The runner (never the test) turns True into os._exit.
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:137:    if stall_timeout is None or float(stall_timeout) <= 0:
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:140:    return (ref - float(last_activity_ts)) > float(stall_timeout)
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:145:    has completed for longer than ``stall_timeout`` seconds. Off when timeout<=0.
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:148:    actually calling ``os._exit``; the runner uses the default hard-exit."""
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:150:    def __init__(self, progress, stall_timeout: float,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:153:        self.stall_timeout = float(stall_timeout)
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:157:            self.check_interval = min(30.0, max(1.0, self.stall_timeout / 10.0))
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:163:        if self.stall_timeout <= 0:
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:166:            target=self._run, name="c2b-stall-watchdog", daemon=True)
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:173:    def _run(self) -> None:
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:178:            if watchdog_should_abort(last, self.stall_timeout):
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:180:                self._on_abort(self.stall_timeout, idle)
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:184:    def _default_abort(stall_timeout: float, idle: float) -> None:
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:186:               f"{idle:.0f}s (> --stall-timeout {stall_timeout:.0f}s). This is the "
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:190:               f"CHECKPOINTED per-cell; re-run the SAME command (no --fresh) to "
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:237:                   seed: int, out_dir: Path) -> (List[AxisAdjSpec], Dict):  # noqa
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:239:    per axis on THIS model (prereg §2; never hardcoded). Reuses run_c1_facade +
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:240:    run_gpu_phase0._extract_direction."""
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:245:    c1_payload = c1.run(
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:246:        model=model, axes=axes, scan_step=2, n_extraction=n_extraction, seed=seed,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:259:        direction = p0._extract_direction(provider, axis, layer, n_extraction, seed)
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:277:                                          alpha_gain=0.1, threshold=0.5)
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:282:def hf_sampler_factory(model: str, max_new_tokens: int, temperature: float,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:283:                       seed: int, batch_size: int):
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:286:    backend = SteeredHFBackend(model, device=device, dtype=dtype, seed=seed)
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:289:        return BackendOutcomeSampler(backend, max_new_tokens=max_new_tokens,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:291:                                     seed=seed, batch_size=batch_size)
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:302:    json_path = out_dir / "c2b_adjudication_results.json"
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:311:    lines.append(f"- run_type: **{meta.get('run_type')}**   "
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:314:    lines.append(f"- δ = {report.frozen_params['delta']}   α grid: {report.frozen_params['alpha_grid']}")
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:323:            f"| {r.axis} | {r.layer} | {ds.get('frozen_alpha')} | "
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:331:                     "items (new DEV/TEST draw, new seed) is REQUIRED before any claim (prereg §4).")
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:339:            lines.append(f"| {r.axis} | {cf['alpha_opposite']} | "
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:342:    summary_path = out_dir / "c2b_adjudication_summary.md"
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:349:             meta: Dict, seed: int) -> str:
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:353:        "kind": "c2b_qualified_adjudication",
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:358:        "seed": seed,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:359:        "torch_seed": seed,  # base torch seed; per-(item,sample) seeds derived from it
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:365:            "frozen_alpha": r.dev_selection.get("frozen_alpha"),
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:375:    summary_metrics["_torch_seed"] = seed
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:378:    run_type = str(meta.get("run_type", "exploratory"))
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:382:        type=run_type, status="done", code_commit=git_commit(str(_REPO)),
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:385:        seed=seed, hardware=str(meta.get("hardware")),
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:390:            "C2b QUALIFIED adjudication implementing FROZEN prereg §4/§5 "
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:393:            + ("EXPLORATORY until the A800 7B run (valid_for_paper=false); this run "
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:394:               "is a " + run_type + " on " + str(meta.get("backend")) + ".")
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:399:        artifact_id="c2b-qualified-adjudication-table", supports_claims=["C2b"],
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:400:        source_experiments=[exp_id], aggregation_script="scripts/run_c2b_adjudication.py",
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:404:    write_manifest(str(out_dir / "c2b_adjudication_table.manifest.yaml"), manifest)
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:412:    ap = argparse.ArgumentParser(description="C2b QUALIFIED adjudication (FROZEN prereg §4/§5)")
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:428:                         "default: the confirmatory run HARD-FAILS if underpowered.")
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:436:                         "The chunk = batch_size//k items generated in one batch.")
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:441:    ap.add_argument("--seed", type=int, default=20260723)
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:442:    ap.add_argument("--stall-timeout", type=float, default=600.0,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:464:                f"(prereg §5). The confirmatory run requires B>=10000. Pass "
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:465:                f"--allow-underpowered to override for a smoke/debug run only.")
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:468:              f"confirmatory adjudication.", flush=True)
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:471:        _REPO / "results" / f"c2b_adjudication_{args.backend}_{date.today().isoformat()}")
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:490:        print(f"[c2b-adj] disk pre-run: {usage0.message}", flush=True)
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:493:            args.n_extraction, args.seed, out_dir)
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:498:        sampler_for_axis = hf_sampler_factory(model, args.max_new_tokens,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:499:                                              args.temperature, args.seed,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:500:                                              args.batch_size)
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:505:    # the run's size is visible BEFORE committing GPU time (sanity-check knob). ---
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:507:        specs, k=adj.K_SAMPLES, alpha_grid=adj.ALPHA_GRID,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:512:    n_batches = -(-total_plan // max(1, args.batch_size))  # ceil
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:515:    print(f"[c2b-adj] budget: batch_size={args.batch_size} "
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:516:          f"max_new_tokens={args.max_new_tokens} -> ~{n_batches} batches; "
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:524:    checkpoint = CheckpointStore(ckpt_dir, fingerprint, seed=args.seed,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:527:    run_ctx = RunContext(checkpoint=checkpoint, progress=progress)
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:529:          f"(fresh={args.fresh}; resume auto-skips cells whose config matches)",
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:536:    watchdog = InactivityWatchdog(progress, args.stall_timeout).start()
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:538:        report = adj.adjudicate(
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:539:            sampler_for_axis, specs, k=adj.K_SAMPLES, alpha_grid=adj.ALPHA_GRID,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:542:            dev_fraction=adj.DEV_FRACTION, seed=args.seed, ctx=run_ctx)
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:550:              f"re-run the SAME command (without --fresh) to RESUME.", flush=True)
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:558:        "model": model, "hardware": hardware, "run_type": "exploratory",
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:560:        "prereg": "docs/ledgers/prereg-c2b-adjudication.md (FROZEN 2026-07-23)",
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:567:    exp_id = register(report, out_dir, json_path, meta, args.seed)
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py:573:        print(f"[c2b-adj] disk post-run: {usage1.message}", flush=True)
```

</details>


---

<sub>52s</sub>

### Copilot

进入关键核查阶段：我将直接解析 JSON/日志做独立重算，并抓取源码关键行定位判据实现。

---

<sub>54s</sub>

### `view`

**view the file at C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\results\c2b_adjudication_hf_2026-07-24\adj2.run.log.**

C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\results\c2b_adjudication_hf_2026-07-24\adj2.run.log (lines 135-320)

<details>
<summary>66 lines</summary>

```
135. [c2b-adj] axis=skepticism phase=conflict_pole 1/1 items=40 DONE done=6800/11365 fresh=6800 elapsed=1046s eta=702s
136. [c2b-adj] axis=uncertainty_awareness phase=dev_prompt 1/16 items=27 START done=6800/11365 fresh=6800 elapsed=1046s eta=702s
137. [c2b-adj] axis=uncertainty_awareness phase=dev_prompt 1/16 items=27 DONE done=6935/11365 fresh=6935 elapsed=1064s eta=680s
138. [c2b-adj] axis=uncertainty_awareness phase=dev_prompt 2/16 items=27 START done=6935/11365 fresh=6935 elapsed=1064s eta=680s
139. [c2b-adj] axis=uncertainty_awareness phase=dev_prompt 2/16 items=27 DONE done=7070/11365 fresh=7070 elapsed=1083s eta=658s
140. [c2b-adj] axis=uncertainty_awareness phase=dev_prompt 3/16 items=27 START done=7070/11365 fresh=7070 elapsed=1083s eta=658s
141. [c2b-adj] axis=uncertainty_awareness phase=dev_prompt 3/16 items=27 DONE done=7205/11365 fresh=7205 elapsed=1101s eta=636s
142. [c2b-adj] axis=uncertainty_awareness phase=dev_prompt 4/16 items=27 START done=7205/11365 fresh=7205 elapsed=1101s eta=636s
143. [c2b-adj] axis=uncertainty_awareness phase=dev_prompt 4/16 items=27 DONE done=7340/11365 fresh=7340 elapsed=1120s eta=614s
144. [c2b-adj] axis=uncertainty_awareness phase=dev_prompt 5/16 items=27 START done=7340/11365 fresh=7340 elapsed=1120s eta=614s
145. [c2b-adj] axis=uncertainty_awareness phase=dev_prompt 5/16 items=27 DONE done=7475/11365 fresh=7475 elapsed=1138s eta=592s
146. [c2b-adj] axis=uncertainty_awareness phase=dev_prompt 6/16 items=27 START done=7475/11365 fresh=7475 elapsed=1138s eta=592s
147. [c2b-adj] axis=uncertainty_awareness phase=dev_prompt 6/16 items=27 DONE done=7610/11365 fresh=7610 elapsed=1157s eta=571s
148. [c2b-adj] axis=uncertainty_awareness phase=dev_prompt 7/16 items=27 START done=7610/11365 fresh=7610 elapsed=1157s eta=571s
149. [c2b-adj] axis=uncertainty_awareness phase=dev_prompt 7/16 items=27 DONE done=7745/11365 fresh=7745 elapsed=1176s eta=549s
150. [c2b-adj] axis=uncertainty_awareness phase=dev_prompt 8/16 items=27 START done=7745/11365 fresh=7745 elapsed=1176s eta=549s
151. [c2b-adj] axis=uncertainty_awareness phase=dev_prompt 8/16 items=27 DONE done=7880/11365 fresh=7880 elapsed=1194s eta=528s
152. [c2b-adj] axis=uncertainty_awareness phase=dev_prompt 9/16 items=27 START done=7880/11365 fresh=7880 elapsed=1194s eta=528s
153. [c2b-adj] axis=uncertainty_awareness phase=dev_prompt 9/16 items=27 DONE done=8015/11365 fresh=8015 elapsed=1213s eta=507s
154. [c2b-adj] axis=uncertainty_awareness phase=dev_prompt 10/16 items=27 START done=8015/11365 fresh=8015 elapsed=1213s eta=507s
155. [c2b-adj] axis=uncertainty_awareness phase=dev_prompt 10/16 items=27 DONE done=8150/11365 fresh=8150 elapsed=1231s eta=486s
156. [c2b-adj] axis=uncertainty_awareness phase=dev_prompt 11/16 items=27 START done=8150/11365 fresh=8150 elapsed=1231s eta=486s
157. [c2b-adj] axis=uncertainty_awareness phase=dev_prompt 11/16 items=27 DONE done=8285/11365 fresh=8285 elapsed=1250s eta=465s
158. [c2b-adj] axis=uncertainty_awareness phase=dev_prompt 12/16 items=27 START done=8285/11365 fresh=8285 elapsed=1250s eta=465s
159. [c2b-adj] axis=uncertainty_awareness phase=dev_prompt 12/16 items=27 DONE done=8420/11365 fresh=8420 elapsed=1268s eta=444s
160. [c2b-adj] axis=uncertainty_awareness phase=dev_prompt 13/16 items=27 START done=8420/11365 fresh=8420 elapsed=1268s eta=444s
161. [c2b-adj] axis=uncertainty_awareness phase=dev_prompt 13/16 items=27 DONE done=8555/11365 fresh=8555 elapsed=1287s eta=423s
162. [c2b-adj] axis=uncertainty_awareness phase=dev_prompt 14/16 items=27 START done=8555/11365 fresh=8555 elapsed=1287s eta=423s
163. [c2b-adj] axis=uncertainty_awareness phase=dev_prompt 14/16 items=27 DONE done=8690/11365 fresh=8690 elapsed=1305s eta=402s
164. [c2b-adj] axis=uncertainty_awareness phase=dev_prompt 15/16 items=27 START done=8690/11365 fresh=8690 elapsed=1305s eta=402s
165. [c2b-adj] axis=uncertainty_awareness phase=dev_prompt 15/16 items=27 DONE done=8825/11365 fresh=8825 elapsed=1324s eta=381s
166. [c2b-adj] axis=uncertainty_awareness phase=dev_prompt 16/16 items=27 START done=8825/11365 fresh=8825 elapsed=1324s eta=381s
167. [c2b-adj] axis=uncertainty_awareness phase=dev_prompt 16/16 items=27 DONE done=8960/11365 fresh=8960 elapsed=1342s eta=360s
168. [c2b-adj] axis=uncertainty_awareness phase=dev_baseline 1/1 items=27 START done=8960/11365 fresh=8960 elapsed=1342s eta=360s
169. [c2b-adj] axis=uncertainty_awareness phase=dev_baseline 1/1 items=27 DONE done=9095/11365 fresh=9095 elapsed=1360s eta=340s
170. [c2b-adj] axis=uncertainty_awareness phase=dev_alpha 1/7 items=27 START done=9095/11365 fresh=9095 elapsed=1360s eta=340s
171. [c2b-adj] axis=uncertainty_awareness phase=dev_alpha 1/7 items=27 DONE done=9230/11365 fresh=9230 elapsed=1379s eta=319s
172. [c2b-adj] axis=uncertainty_awareness phase=dev_alpha 2/7 items=27 START done=9230/11365 fresh=9230 elapsed=1379s eta=319s
173. [c2b-adj] axis=uncertainty_awareness phase=dev_alpha 2/7 items=27 DONE done=9365/11365 fresh=9365 elapsed=1397s eta=298s
174. [c2b-adj] axis=uncertainty_awareness phase=dev_alpha 3/7 items=27 START done=9365/11365 fresh=9365 elapsed=1397s eta=298s
175. [c2b-adj] axis=uncertainty_awareness phase=dev_alpha 3/7 items=27 DONE done=9500/11365 fresh=9500 elapsed=1415s eta=278s
176. [c2b-adj] axis=uncertainty_awareness phase=dev_alpha 4/7 items=27 START done=9500/11365 fresh=9500 elapsed=1415s eta=278s
177. [c2b-adj] axis=uncertainty_awareness phase=dev_alpha 4/7 items=27 DONE done=9635/11365 fresh=9635 elapsed=1434s eta=257s
178. [c2b-adj] axis=uncertainty_awareness phase=dev_alpha 5/7 items=27 START done=9635/11365 fresh=9635 elapsed=1434s eta=257s
179. [c2b-adj] axis=uncertainty_awareness phase=dev_alpha 5/7 items=27 DONE done=9770/11365 fresh=9770 elapsed=1452s eta=237s
180. [c2b-adj] axis=uncertainty_awareness phase=dev_alpha 6/7 items=27 START done=9770/11365 fresh=9770 elapsed=1452s eta=237s
181. [c2b-adj] axis=uncertainty_awareness phase=dev_alpha 6/7 items=27 DONE done=9905/11365 fresh=9905 elapsed=1470s eta=217s
182. [c2b-adj] axis=uncertainty_awareness phase=dev_alpha 7/7 items=27 START done=9905/11365 fresh=9905 elapsed=1470s eta=217s
183. [c2b-adj] axis=uncertainty_awareness phase=dev_alpha 7/7 items=27 DONE done=10040/11365 fresh=10040 elapsed=1488s eta=196s
184. [c2b-adj] axis=uncertainty_awareness phase=test_prompt 1/1 items=53 START done=10040/11365 fresh=10040 elapsed=1488s eta=196s
185. [c2b-adj] axis=uncertainty_awareness phase=test_prompt 1/1 items=53 DONE done=10305/11365 fresh=10305 elapsed=1525s eta=157s
186. [c2b-adj] axis=uncertainty_awareness phase=test_steer 1/1 items=53 START done=10305/11365 fresh=10305 elapsed=1525s eta=157s
187. [c2b-adj] axis=uncertainty_awareness phase=test_steer 1/1 items=53 DONE done=10570/11365 fresh=10570 elapsed=1556s eta=117s
188. [c2b-adj] axis=uncertainty_awareness phase=test_baseline 1/1 items=53 START done=10570/11365 fresh=10570 elapsed=1556s eta=117s
189. [c2b-adj] axis=uncertainty_awareness phase=test_baseline 1/1 items=53 DONE done=10835/11365 fresh=10835 elapsed=1588s eta=78s
190. [c2b-adj] axis=uncertainty_awareness phase=conflict 1/1 items=53 START done=10835/11365 fresh=10835 elapsed=1588s eta=78s
191. [c2b-adj] axis=uncertainty_awareness phase=conflict 1/1 items=53 DONE done=11100/11365 fresh=11100 elapsed=1625s eta=39s
192. [c2b-adj] axis=uncertainty_awareness phase=conflict_pole 1/1 items=53 START done=11100/11365 fresh=11100 elapsed=1625s eta=39s
193. [c2b-adj] axis=uncertainty_awareness phase=conflict_pole 1/1 items=53 DONE done=11365/11365 fresh=11365 elapsed=1666s eta=0s
194. [c2b-adj] disk post-run: disk ok: total 0.18GB < budget 60GB (ceiling 70GB) [/root/autodl-tmp/hf_home=0.18GB].
195. 
196. [c2b-adj] VERDICT: KILL_PLAN_D  (axes passing: 0/3)
197. [c2b-adj] wrote results/c2b_adjudication_hf_2026-07-24/c2b_adjudication_results.json  (exp c2b-adj-deac6326-0001)  wall=1732.3s
198. ADJ2_EXIT_RC=0
199. ADJ2_END Fri Jul 24 13:56:12 CST 2026
200.
```

</details>


---

<sub>54s</sub>

### `rg`

**STALL|stall|watchdog|Traceback|ERROR|Exception|ABORT|RuntimeError|hard-exit|DONE done=11365|ADJ2_END|PLANNED generations**

"STALL|stall|watchdog|Traceback|ERROR|Exception|ABORT|RuntimeError|hard-exit|DONE done=11365|ADJ2_END|PLANNED generations" (results\c2b_adjudication_hf_2026-07-24\adj2.run.log)

```
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\results\c2b_adjudication_hf_2026-07-24\adj2.run.log:7:[c1] system-available RAM at start: 488562 MB (watchdog floor 0 MB)
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\results\c2b_adjudication_hf_2026-07-24\adj2.run.log:16:[c2b-adj] PLANNED generations (upper bound): deliberation=3400, skepticism=3400, uncertainty_awareness=4565  TOTAL=11365
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\results\c2b_adjudication_hf_2026-07-24\adj2.run.log:193:[c2b-adj] axis=uncertainty_awareness phase=conflict_pole 1/1 items=53 DONE done=11365/11365 fresh=11365 elapsed=1666s eta=0s
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\results\c2b_adjudication_hf_2026-07-24\adj2.run.log:199:ADJ2_END Fri Jul 24 13:56:12 CST 2026
```


---

<sub>54s</sub>

### `rg`

**DELTA|CI_LEVEL|BONFERRONI|COHERENCE_MAX_RATIO|BOOTSTRAP_B|ALPHA_GRID|DEV_FRACTION|K_SAMPLES|KILL_PLAN_D|CONDITIONAL_GO|STRONG_GO|pass|paired|cluster|bootstrap|resample|degeneracy|coherence|frozen_alpha**

"DELTA|CI_LEVEL|BONFERRONI|COHERENCE_MAX_RATIO|BOOTSTRAP_B|ALPHA_GRID|DEV_FRACTION|K_SAMPLES|KILL_PLAN_D|CONDITIONAL_GO|STRONG_GO|pass|paired|cluster|bootstrap|resample|degeneracy|coherence|frozen_alpha" (src\cognitive_console\experiments\adjudicate_c2b.py)

<details>
<summary>6 matches</summary>

```
Output too large to read at once (26.1 KB). Saved to: C:\Users\V-ELZH~1\AppData\Local\Temp\copilot-tool-output-1784872986556-2.txt
Consider using tools like rg (for searching), head/tail (for viewing start/end), view with view_range (for specific sections), or jq (for JSON) to examine portions of the output.

Preview (first 500 chars):
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:6:BEHAVIORAL outcome beyond the best bounded-prompt outcome" — with a paired,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:12:* α grid {2,4,6,8,12,16,24}         -> ``ALPHA_GRID``                       (§5)
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:13:* δ = 0.05
```

</details>


---

<sub>54s</sub>

### `view`

**view the file at C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py.**

C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py (lines 1-280)

<details>
<summary>280 lines</summary>

```
1. """C2b behavioral-gap ADJUDICATION harness — implements prereg §4 EXACTLY.
2. 
3. FROZEN spec: ``docs/ledgers/prereg-c2b-adjudication.md`` (§1 instrument, §2 design,
4. §4 decision rule, §5 parameters). This module implements the FROZEN, qualified
5. adjudication of Claim C2b — "on tasks with headroom, latent steering reaches a
6. BEHAVIORAL outcome beyond the best bounded-prompt outcome" — with a paired,
7. multiplicity-corrected, three-tier decision rule. The criteria are LOCKED; this
8. code implements them, it does NOT invent thresholds.
9. 
10. Frozen-criterion -> code map
11. ----------------------------
12. * α grid {2,4,6,8,12,16,24}         -> ``ALPHA_GRID``                       (§5)
13. * δ = 0.05                          -> ``DELTA``                            (§5)
14. * N: delib 60 / skep 60 / unc 80    -> ``N_ITEMS_BY_AXIS``                  (§5)
15. * k = 5 samples/item                -> ``K_SAMPLES``                        (§5)
16. * coherence ≤ 1.5× baseline         -> ``COHERENCE_MAX_RATIO`` + gate       (§3/§5)
17. * cluster bootstrap, B ≥ 10000      -> ``cluster_bootstrap_ci`` (item-level) (§4/§5)
18. * per-axis CI at 1 − 0.05/3         -> ``BONFERRONI_CI_LEVEL``              (§4/§5)
19. * DEV ~1/3 selects+freezes α+prompt  -> ``split_dev_test`` + ``select_on_dev`` (§2/§4)
20. * TEST ~2/3 paired d_i=steer−prompt  -> ``adjudicate_axis`` (frozen α+prompt)  (§2/§4)
21. * pass iff CI excl 0 AND mean≥δ AND coherence -> ``axis_pass``               (§4)
22. * ≥2 / 1 / 0 axes pass -> STRONG_GO / CONDITIONAL_GO / KILL_PLAN_D -> ``three_tier_verdict`` (§4)
23. * conflict cells SECONDARY/descriptive only -> ``AxisAdjResult.conflict``   (§4)
24. 
25. Model-independent: all generation goes through a ``GenBackend`` (real
26. ``SteeredHFBackend`` on the A800, ``SyntheticC2bTaskBackend`` offline) and the
27. deterministic answer-key scorers in ``eval.scorers``. No torch here.
28. """
29. 
30. from __future__ import annotations
31. 
32. import abc
33. import hashlib
34. import json
35. import time
36. from dataclasses import dataclass, field, asdict
37. from pathlib import Path
38. from typing import Callable, Dict, List, Optional, Sequence, Tuple
39. 
40. import numpy as np
41. 
42. from ..eval import scorers as _scorers
43. from ..steering.generate import GenBackend, SteerConfig
44. 
45. # --------------------------------------------------------------------------- #
46. # FROZEN parameters (prereg §5 — LOCKED, do not change after freeze 2026-07-23)
47. # --------------------------------------------------------------------------- #
48. ALPHA_GRID: Tuple[float, ...] = (2.0, 4.0, 6.0, 8.0, 12.0, 16.0, 24.0)
49. DELTA: float = 0.05
50. K_SAMPLES: int = 5
51. N_ITEMS_BY_AXIS: Dict[str, int] = {
52.     "deliberation": 60,
53.     "skepticism": 60,
54.     "uncertainty_awareness": 80,
55. }
56. COHERENCE_MAX_RATIO: float = 1.5
57. # Small additive floor on the degeneracy-scale so the gate ceiling does NOT
58. # collapse to an exact "== 0" test when the unsteered baseline degeneracy is 0
59. # (a mildly-repetitive-but-coherent cell must not be spuriously discarded). The
60. # gate stays conservative: ceiling = 1.5 * baseline + COHERENCE_EPS_FLOOR.
61. COHERENCE_EPS_FLOOR: float = 0.02  # on the [0,1] degeneracy-score scale
62. BOOTSTRAP_B: int = 10000
63. FAMILYWISE_ALPHA: float = 0.05
64. N_AXES: int = 3
65. BONFERRONI_CI_LEVEL: float = 1.0 - FAMILYWISE_ALPHA / N_AXES  # ≈ 0.98333...
66. DEV_FRACTION: float = 1.0 / 3.0
67. 
68. VERDICT_STRONG_GO = "STRONG_GO"
69. VERDICT_CONDITIONAL_GO = "CONDITIONAL_GO"
70. VERDICT_KILL = "KILL_PLAN_D"
71. 
72. # Which per-item outcome the paired bootstrap consumes per axis.
73. BINARY_OUTCOME_AXES = {"deliberation", "skepticism"}
74. CALIBRATION_OUTCOME_AXES = {"uncertainty_awareness"}
75. 
76. 
77. # --------------------------------------------------------------------------- #
78. # Run mechanics: progress logging + checkpointing (FIX 1/2 — NOT the decision
79. # rule). These only affect observability/resumability, never the frozen §4 math.
80. # --------------------------------------------------------------------------- #
81. # Phase labels used for progress lines AND checkpoint file names (<axis>_<phase>).
82. PHASE_DEV_PROMPT = "dev_prompt"
83. PHASE_DEV_BASELINE = "dev_baseline"
84. PHASE_DEV_ALPHA = "dev_alpha"
85. PHASE_TEST_PROMPT = "test_prompt"
86. PHASE_TEST_STEER = "test_steer"
87. PHASE_TEST_BASELINE = "test_baseline"
88. PHASE_CONFLICT = "conflict"
89. PHASE_CONFLICT_POLE = "conflict_pole"
90. 
91. 
92. class ProgressTracker:
93.     """Flushed per-cell progress logging with a running count + wall-clock ETA.
94. 
95.     A "cell" is one ``_channel_item_outcomes`` call (axis × channel × prompt|alpha
96.     over its items). ``total_planned`` is the up-front planned generation count so
97.     a run's size is visible immediately. Every line is printed with ``flush=True``
98.     (the prior tqdm ``\\r`` never reached the logfile — D-0029)."""
99. 
100.     def __init__(self, total_planned: int):
101.         self.total = int(total_planned)
102.         self.done = 0
103.         self.fresh = 0
104.         self.t0 = time.time()
105.         # Monotonic-ish wall-clock of the last observed progress. An external
106.         # inactivity watchdog (runner) reads this to detect a SILENT hang (e.g. a
107.         # host-driver reload that spins at 100% CPU with NO exception — D-0029).
108.         self.last_activity = self.t0
109. 
110.     def heartbeat(self) -> None:
111.         self.last_activity = time.time()
112. 
113.     def _elapsed(self) -> float:
114.         return time.time() - self.t0
115. 
116.     def _eta(self) -> float:
117.         el = self._elapsed()
118.         if self.done <= 0 or el <= 0:
119.             return 0.0
120.         rate = self.done / el
121.         return (self.total - self.done) / rate if rate > 0 else 0.0
122. 
123.     def add(self, n: int, fresh: bool = True) -> None:
124.         self.done += int(n)
125.         if fresh:
126.             self.fresh += int(n)
127.         self.last_activity = time.time()
128. 
129.     def _line(self, axis, phase, idx, total, items, tag):
130.         print(
131.             f"[c2b-adj] axis={axis} phase={phase} {idx}/{total} items={items} {tag} "
132.             f"done={self.done}/{self.total} fresh={self.fresh} "
133.             f"elapsed={self._elapsed():.0f}s eta={self._eta():.0f}s",
134.             flush=True,
135.         )
136. 
137.     def cell_start(self, axis, phase, idx, total, items):
138.         self.last_activity = time.time()
139.         self._line(axis, phase, idx, total, items, "START")
140. 
141.     def cell_end(self, axis, phase, idx, total, items):
142.         self.last_activity = time.time()
143.         self._line(axis, phase, idx, total, items, "DONE")
144. 
145. 
146. class CheckpointStore:
147.     """Append-only per-(axis,phase) JSONL of per-item k-sample outcomes (FIX 2).
148. 
149.     Each generation cell's per-item result is flushed to
150.     ``<ckpt_dir>/<axis>_<phase>.jsonl`` as one JSON line keyed by
151.     ``(axis, phase, cell_key, item_id)`` (``cell_key`` encodes the prompt_id or
152.     alpha), carrying the frozen ``seed`` and the ``config`` fingerprint. On
153.     startup, lines whose ``config`` matches the current run are loaded so already
154.     computed cells are SKIPPED and only the missing ones are generated. Because
155.     the final adjudication reads the same per-item outcomes, a resumed run yields
156.     the IDENTICAL frozen-criteria verdict. ``fresh=True`` ignores/clears prior
157.     checkpoints."""
158. 
159.     def __init__(self, ckpt_dir, config_fingerprint: str, seed: int,
160.                  fresh: bool = False):
161.         self.dir = Path(ckpt_dir)
162.         self.dir.mkdir(parents=True, exist_ok=True)
163.         self.fp = str(config_fingerprint)
164.         self.seed = int(seed)
165.         self._cache: Dict[Tuple[str, str, str, str], Tuple[List[float], List[float]]] = {}
166.         self._handles: Dict[str, object] = {}
167.         if fresh:
168.             for f in self.dir.glob("*.jsonl"):
169.                 try:
170.                     f.unlink()
171.                 except OSError:
172.                     pass
173.         else:
174.             self._load()
175.         try:
176.             (self.dir / "config_fingerprint.txt").write_text(self.fp, encoding="utf-8")
177.         except OSError:
178.             pass
179. 
180.     def _load(self) -> None:
181.         for f in sorted(self.dir.glob("*.jsonl")):
182.             try:
183.                 lines = f.read_text(encoding="utf-8").splitlines()
184.             except OSError:
185.                 continue
186.             for line in lines:
187.                 line = line.strip()
188.                 if not line:
189.                     continue
190.                 try:
191.                     rec = json.loads(line)
192.                 except json.JSONDecodeError:
193.                     continue
194.                 if rec.get("config") != self.fp:
195.                     continue  # different run config -> not resumable, ignore
196.                 key = (rec["axis"], rec["phase"], rec["cell_key"], str(rec["item_id"]))
197.                 # MINOR-2: duplicate lines for the same key (e.g. a cell re-run
198.                 # after a crash+resume) are load-order LAST-WINS — iterating files
199.                 # sorted and lines in append order means the most recently written
200.                 # record for a key overwrites earlier ones, which is the correct
201.                 # resume semantics. No explicit dedup needed.
202.                 self._cache[key] = (rec["outcomes"], rec["degeneracies"])
203. 
204.     def get(self, axis, phase, cell_key, item_id):
205.         return self._cache.get((axis, phase, cell_key, str(item_id)))
206. 
207.     def _handle(self, axis, phase):
208.         fn = self.dir / f"{axis}_{phase}.jsonl"
209.         h = self._handles.get(str(fn))
210.         if h is None:
211.             h = open(fn, "a", encoding="utf-8")
212.             self._handles[str(fn)] = h
213.         return h
214. 
215.     def put(self, axis, phase, cell_key, item_id, outcomes, degeneracies,
216.             alpha, instruction) -> None:
217.         rec = {
218.             "config": self.fp, "seed": self.seed,
219.             "axis": axis, "phase": phase, "cell_key": cell_key,
220.             "item_id": str(item_id), "alpha": float(alpha),
221.             "outcomes": [float(x) for x in outcomes],
222.             "degeneracies": [float(x) for x in degeneracies],
223.         }
224.         h = self._handle(axis, phase)
225.         h.write(json.dumps(rec) + "\n")
226.         h.flush()
227.         self._cache[(axis, phase, cell_key, str(item_id))] = (rec["outcomes"], rec["degeneracies"])
228. 
229.     def close(self) -> None:
230.         for h in self._handles.values():
231.             try:
232.                 h.close()
233.             except OSError:
234.                 pass
235.         self._handles.clear()
236. 
237. 
238. @dataclass
239. class RunContext:
240.     """Optional run-mechanics carrier threaded through the frozen adjudication.
241. 
242.     ``None`` everywhere => the offline/no-torch default: no progress logging, no
243.     checkpointing, per-item generation (unchanged behaviour, tests stay green)."""
244.     checkpoint: Optional[CheckpointStore] = None
245.     progress: Optional[ProgressTracker] = None
246. 
247. 
248. def _split_sizes(n: int, dev_fraction: float = DEV_FRACTION) -> Tuple[int, int]:
249.     """DEV/TEST sizes matching ``split_dev_test`` (for up-front budget planning)."""
250.     n_dev = int(round(dev_fraction * n))
251.     n_dev = max(1, min(n_dev, n - 1))
252.     return n_dev, n - n_dev
253. 
254. 
255. def plan_generation_counts(
256.     specs: Sequence["AxisAdjSpec"], *, k: int = K_SAMPLES,
257.     alpha_grid: Sequence[float] = ALPHA_GRID, dev_fraction: float = DEV_FRACTION,
258. ) -> Tuple[Dict[str, int], int]:
259.     """Up-front UPPER-BOUND planned generation count per axis + total (FIX 4).
260. 
261.     Per axis (all cells run):
262.       DEV  = k * n_dev * (n_strong_prompts + 1 baseline + len(alpha_grid))
263.       TEST = k * n_test * (prompt + steer + baseline + conflict + conflict_pole)
264.     This is the worst case (an axis with no gated alpha runs fewer cells)."""
265.     per_axis: Dict[str, int] = {}
266.     total = 0
267.     for spec in specs:
268.         n = len(spec.items)
269.         n_dev, n_test = _split_sizes(n, dev_fraction)
270.         n_strong = len(spec.strong_prompts)
271.         dev = k * n_dev * (n_strong + 1 + len(alpha_grid))
272.         test = k * n_test * (1 + 1 + 1 + 1 + 1)
273.         cnt = dev + test
274.         per_axis[spec.axis] = cnt
275.         total += cnt
276.     return per_axis, total
277. 
278. 
279. # --------------------------------------------------------------------------- #
280. # DEV/TEST split (prereg §2/§4 — ~1/3 DEV selection, disjoint ~2/3 TEST)
```

</details>


---

<sub>54s</sub>

### `view`

**view the file at C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py.**

C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py (lines 281-620)

<details>
<summary>340 lines</summary>

```
281. # --------------------------------------------------------------------------- #
282. @dataclass(frozen=True)
283. class DevTestSplit:
284.     dev_ids: List[str]
285.     test_ids: List[str]
286. 
287.     def __post_init__(self):
288.         overlap = set(self.dev_ids) & set(self.test_ids)
289.         if overlap:
290.             raise ValueError(f"DEV/TEST leakage: {sorted(overlap)}")
291. 
292. 
293. def split_dev_test(item_ids: Sequence[str], dev_fraction: float = DEV_FRACTION,
294.                    seed: int = 0) -> DevTestSplit:
295.     """Disjoint DEV (~dev_fraction) / TEST split with a fixed seed (deterministic).
296. 
297.     DEV is used ONLY to select+freeze the best-of-16 prompt and the best α; TEST
298.     is the disjoint adjudication pool. At least one item goes to each side.
299.     """
300.     ids = sorted(str(i) for i in item_ids)
301.     n = len(ids)
302.     if n < 2:
303.         raise ValueError("need at least 2 items to form a DEV/TEST split")
304.     rng = np.random.default_rng(seed)
305.     order = rng.permutation(n)
306.     shuffled = [ids[i] for i in order]
307.     n_dev = int(round(dev_fraction * n))
308.     n_dev = max(1, min(n_dev, n - 1))
309.     dev = sorted(shuffled[:n_dev])
310.     test = sorted(shuffled[n_dev:])
311.     return DevTestSplit(dev_ids=dev, test_ids=test)
312. 
313. 
314. # --------------------------------------------------------------------------- #
315. # Paired ITEM-cluster bootstrap (prereg §4 — resample ITEMS, each carries its k)
316. # --------------------------------------------------------------------------- #
317. @dataclass(frozen=True)
318. class BootstrapCI:
319.     point: float
320.     ci_lo: float
321.     ci_hi: float
322.     ci_level: float
323.     b: int
324.     cluster: bool
325. 
326.     def excludes_zero(self) -> bool:
327.         return ci_excludes_zero(self.ci_lo, self.ci_hi)
328. 
329. 
330. def ci_excludes_zero(ci_lo: float, ci_hi: float) -> bool:
331.     """True iff 0 is NOT in the closed interval [ci_lo, ci_hi]."""
332.     return not (ci_lo <= 0.0 <= ci_hi)
333. 
334. 
335. def cluster_bootstrap_ci(
336.     item_samples,
337.     b: int = BOOTSTRAP_B,
338.     ci_level: float = BONFERRONI_CI_LEVEL,
339.     seed: int = 0,
340.     cluster: bool = True,
341. ) -> BootstrapCI:
342.     """Two-sided percentile bootstrap CI of the mean of per-item paired diffs.
343. 
344.     ``item_samples`` is either a 1-D array of per-item diffs ``d_i`` (one value
345.     per item / cluster) or a 2-D ``[n_items, k]`` array of per-sample values whose
346.     row means are the per-item diffs. Frozen behaviour (§4):
347. 
348.     * ``cluster=True`` (the pre-registered mode): resample ITEMS with replacement
349.       (each item carries ALL its k samples), statistic = mean over resampled items
350.       of their row means. This respects the k-sample nesting.
351.     * ``cluster=False`` (for the audit test only): pool all n*k sample values and
352.       resample at the SAMPLE level, breaking the item clustering — used to
353.       demonstrate the two give different CIs when k>1.
354. 
355.     Returns the point estimate (identical for both modes with balanced k) and the
356.     percentile CI at ``ci_level`` (default the Bonferroni 1 − 0.05/3).
357.     """
358.     arr = np.asarray(item_samples, dtype=np.float64)
359.     if arr.ndim == 1:
360.         arr = arr[:, None]
361.     if arr.ndim != 2:
362.         raise ValueError("item_samples must be 1-D [n] or 2-D [n, k]")
363.     n, k = arr.shape
364.     if n < 1:
365.         raise ValueError("need at least one item")
366.     if b < 1:
367.         raise ValueError("b (bootstrap resamples) must be >= 1")
368.     if not (0.0 < ci_level < 1.0):
369.         raise ValueError("ci_level must be in (0, 1)")
370.     rng = np.random.default_rng(seed)
371.     row_means = arr.mean(axis=1)  # per-item diff d_i
372. 
373.     if cluster:
374.         idx = rng.integers(0, n, size=(b, n))
375.         boot = row_means[idx].mean(axis=1)
376.         point = float(row_means.mean())
377.     else:
378.         flat = arr.reshape(-1)
379.         m = flat.size
380.         idx = rng.integers(0, m, size=(b, m))
381.         boot = flat[idx].mean(axis=1)
382.         point = float(flat.mean())
383. 
384.     lo_pct = 100.0 * (1.0 - ci_level) / 2.0
385.     hi_pct = 100.0 * (1.0 + ci_level) / 2.0
386.     ci_lo = float(np.percentile(boot, lo_pct))
387.     ci_hi = float(np.percentile(boot, hi_pct))
388.     return BootstrapCI(point=point, ci_lo=ci_lo, ci_hi=ci_hi,
389.                        ci_level=ci_level, b=int(b), cluster=cluster)
390. 
391. 
392. # --------------------------------------------------------------------------- #
393. # Per-axis pass rule + three-tier verdict (prereg §4)
394. # --------------------------------------------------------------------------- #
395. def axis_pass(mean_d: float, ci_lo: float, ci_hi: float, coherence_ok: bool,
396.               delta: float = DELTA) -> bool:
397.     """An axis PASSES (Bonferroni-corrected) iff ALL of (§4):
398.     (i) the CI of mean(d) EXCLUDES 0, (ii) mean(d) >= δ, (iii) coherence gate ok."""
399.     return bool(ci_excludes_zero(ci_lo, ci_hi) and (mean_d >= delta) and coherence_ok)
400. 
401. 
402. def three_tier_verdict(axis_passes: Dict[str, bool]) -> str:
403.     """Map the per-axis pass flags to the frozen three-tier verdict (§4):
404.     ≥2 pass -> STRONG_GO; exactly 1 -> CONDITIONAL_GO (single-axis replication
405.     required); 0 -> KILL_PLAN_D."""
406.     n_pass = sum(1 for v in axis_passes.values() if v)
407.     if n_pass >= 2:
408.         return VERDICT_STRONG_GO
409.     if n_pass == 1:
410.         return VERDICT_CONDITIONAL_GO
411.     return VERDICT_KILL
412. 
413. 
414. # --------------------------------------------------------------------------- #
415. # Outcome sampler seam (model-independent)
416. # --------------------------------------------------------------------------- #
417. @dataclass
418. class SampleBatch:
419.     """k per-sample outcomes in [0,1] plus their degeneracy scores for one cell."""
420.     outcomes: List[float]
421.     degeneracies: List[float]
422. 
423.     def mean_outcome(self) -> float:
424.         return float(np.mean(self.outcomes))
425. 
426.     def mean_degeneracy(self) -> float:
427.         return float(np.mean(self.degeneracies))
428. 
429. 
430. class OutcomeSampler(abc.ABC):
431.     """Produces k scored samples for one (item, channel) cell — the deferred seam."""
432. 
433.     @abc.abstractmethod
434.     def sample(self, axis: str, item: Dict, instruction: str, alpha: float,
435.                k: int, direction: np.ndarray, layer: int) -> SampleBatch:
436.         """Return a SampleBatch of k outcome+degeneracy scores for the cell."""
437. 
438.     def sample_batch(self, axis: str, items: Sequence[Dict], instruction: str,
439.                      alpha: float, k: int, direction: np.ndarray,
440.                      layer: int) -> List[SampleBatch]:
441.         """Score a CHUNK of items sharing (instruction, alpha). Default loops
442.         ``sample``; batched backends override to generate the whole chunk in one
443.         padded GPU batch (FIX 3). Returns one SampleBatch per item, in order."""
444.         return [self.sample(axis, it, instruction, alpha, k, direction, layer)
445.                 for it in items]
446. 
447. 
448. def format_task_input(axis: str, instruction: str, item: Dict) -> str:
449.     """Build the model input: instruction + task question (+ MC options / answer
450.     format cue). The instruction is the DEV-selected best prompt (prompt channel)
451.     or the neutral prompt (steer channel)."""
452.     q = str(item.get("prompt", "")).strip()
453.     lines = [instruction.strip(), q]
454.     choices = item.get("choices")
455.     if choices:
456.         opts = "\n".join(f"{ell}) {txt}" for ell, txt in choices.items())
457.         lines.append("Options:\n" + opts + "\n\nAnswer with the letter of the best option.")
458.     if axis == "deliberation":
459.         lines.append("Give the final numeric answer.")
460.     elif axis == "uncertainty_awareness":
461.         lines.append('End with: Answer: <your answer>. Confidence: <0-100>%.')
462.     return "\n\n".join(ln for ln in lines if ln)
463. 
464. 
465. def score_sample_outcome(axis: str, item: Dict, text: str) -> float:
466.     """Per-sample OUTCOME in [0,1] via the frozen answer-key scorers (§1)."""
467.     if axis == "deliberation":
468.         return float(_scorers.score_deliberation(text, item))
469.     if axis == "skepticism":
470.         return float(_scorers.score_skepticism(text, item))
471.     if axis == "uncertainty_awareness":
472.         correct = _scorers.item_is_correct(item, text)
473.         conf = _scorers.parse_confidence(text)
474.         if conf is None:
475.             conf = 0.5  # no stated confidence -> maximally uninformative prior
476.         return _scorers.per_item_brier(correct, conf)
477.     raise ValueError(f"unknown axis {axis!r}")
478. 
479. 
480. class BackendOutcomeSampler(OutcomeSampler):
481.     """Wires a ``GenBackend`` + the frozen scorers into the adjudication harness.
482. 
483.     For each of k samples it generates a response to the formatted task input
484.     (steered at ``alpha`` on ``layer`` along ``direction``) and scores the outcome
485.     with the answer-key scorer plus a degeneracy score for the coherence gate.
486.     Sampling (``do_sample``) is used when k>1 so the k samples vary; with a greedy
487.     backend (or the synthetic offline backend) the k samples may coincide.
488.     """
489. 
490.     def __init__(self, gen_backend: GenBackend, max_new_tokens: int = 256,
491.                  do_sample: bool = True, temperature: float = 0.7,
492.                  seed: int = 0, batch_size: int = 1):
493.         if not isinstance(gen_backend, GenBackend):
494.             raise TypeError("gen_backend must be a GenBackend")
495.         self.gen = gen_backend
496.         self.max_new_tokens = int(max_new_tokens)
497.         self.do_sample = bool(do_sample)
498.         self.temperature = float(temperature)
499.         self.seed = int(seed)
500.         self.batch_size = max(1, int(batch_size))
501. 
502.     @property
503.     def supports_batch(self) -> bool:
504.         """True iff the wrapped backend can generate a padded batch (FIX 3)."""
505.         return self.batch_size > 1 and hasattr(self.gen, "generate_batch")
506. 
507.     def _call_seed(self, axis: str, item: Dict, alpha: float, j: int) -> int:
508.         """Deterministic per-(item, sample-index) torch seed derived from the run
509.         seed, so re-runs reproduce every sampled generation (item-clustered)."""
510.         key = f"{self.seed}|{axis}|{item.get('id')}|{float(alpha):.6f}|{j}"
511.         return int(hashlib.sha256(key.encode("utf-8")).hexdigest(), 16) % (2 ** 31)
512. 
513.     def sample_batch(self, axis: str, items: Sequence[Dict], instruction: str,
514.                      alpha: float, k: int, direction: np.ndarray,
515.                      layer: int) -> List[SampleBatch]:
516.         """Generate a whole chunk (all items × k samples) in ONE padded GPU batch
517.         when the backend supports it (FIX 3); else fall back to per-item ``sample``.
518. 
519.         The caller sizes the chunk so ``len(items) * k <= batch_size``. Per-row
520.         seeds are the SAME per-(item,sample) seeds as the unbatched path, so the
521.         batch is deterministic for its (fixed) composition."""
522.         items = list(items)
523.         if not self.supports_batch:
524.             return [self.sample(axis, it, instruction, alpha, k, direction, layer)
525.                     for it in items]
526.         steer = SteerConfig(direction=direction, alpha=float(alpha), layer=int(layer))
527.         prompts: List[str] = []
528.         seeds: List[int] = []
529.         owner: List[int] = []
530.         for ii, it in enumerate(items):
531.             text_input = format_task_input(axis, instruction, it)
532.             for j in range(int(k)):
533.                 prompts.append(text_input)
534.                 seeds.append(self._call_seed(axis, it, alpha, j))
535.                 owner.append(ii)
536.         texts = self.gen.generate_batch(
537.             prompts, steer, self.max_new_tokens, seeds=seeds,
538.             do_sample=self.do_sample, temperature=self.temperature)
539.         batches: List[SampleBatch] = []
540.         for ii, it in enumerate(items):
541.             outs: List[float] = []
542.             degs: List[float] = []
543.             for idx, own in enumerate(owner):
544.                 if own == ii:
545.                     outs.append(score_sample_outcome(axis, it, texts[idx]))
546.                     degs.append(_scorers.degeneracy_score(texts[idx]))
547.             batches.append(SampleBatch(outcomes=outs, degeneracies=degs))
548.         return batches
549. 
550.     def sample(self, axis: str, item: Dict, instruction: str, alpha: float,
551.                k: int, direction: np.ndarray, layer: int) -> SampleBatch:
552.         text_input = format_task_input(axis, instruction, item)
553.         steer = SteerConfig(direction=direction, alpha=float(alpha), layer=int(layer))
554.         outcomes: List[float] = []
555.         degens: List[float] = []
556.         for j in range(int(k)):
557.             call_seed = self._call_seed(axis, item, alpha, j)
558.             try:
559.                 out = self.gen.generate(text_input, steer, self.max_new_tokens,
560.                                         do_sample=self.do_sample,
561.                                         temperature=self.temperature, seed=call_seed)
562.             except TypeError:
563.                 # Synthetic/deterministic backends ignore sampling/seed kwargs.
564.                 out = self.gen.generate(text_input, steer, self.max_new_tokens)
565.             outcomes.append(score_sample_outcome(axis, item, out))
566.             degens.append(_scorers.degeneracy_score(out))
567.         return SampleBatch(outcomes=outcomes, degeneracies=degens)
568. 
569. 
570. # --------------------------------------------------------------------------- #
571. # Per-axis adjudication
572. # --------------------------------------------------------------------------- #
573. @dataclass
574. class AxisAdjSpec:
575.     """Per-axis inputs to the adjudication (prereg §2)."""
576.     axis: str
577.     items: List[Dict]                        # each: id, prompt/question, answer key
578.     strong_prompts: List[Tuple[str, str]]    # up to 16 (prompt_id, instruction)
579.     neutral_prompt: str                      # steer-channel instruction
580.     direction: np.ndarray                    # unit CAA direction (C1 re-derived)
581.     layer: int                               # C1 chosen non-degenerate layer
582. 
583. 
584. @dataclass
585. class DevSelection:
586.     """What DEV froze: the best-of-16 prompt and the coherence-gated best α."""
587.     best_prompt_id: str
588.     best_prompt_text: str
589.     dev_prompt_outcome: float
590.     frozen_alpha: Optional[float]
591.     dev_steer_outcome: Optional[float]
592.     baseline_degeneracy: float
593.     alpha_grid: List[Dict[str, object]]      # per-α: outcome, degeneracy, coherence_ok
594.     any_alpha_passes_gate: bool
595. 
596. 
597. def _channel_item_outcomes(
598.     sampler: OutcomeSampler, axis: str, items: Sequence[Dict], instruction: str,
599.     alpha: float, k: int, direction: np.ndarray, layer: int,
600.     *, ctx: Optional[RunContext] = None, phase: str = "", cell_key: str = "",
601.     cell_idx: int = 1, cell_total: int = 1,
602. ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
603.     """Return (per_item_outcome[n], per_item_degeneracy[n], per_sample_outcomes[n,k]).
604. 
605.     Run mechanics (FIX 1/2/3, do NOT affect the frozen math):
606.     * CHECKPOINT: skip items already in ``ctx.checkpoint`` for this
607.       (axis, phase, cell_key); flush each fresh item's k-sample outcome to disk.
608.     * BATCH: with a batch-capable sampler, generate items in FIXED-composition
609.       chunks of ``batch_size // k`` items. Chunking is cache-INDEPENDENT: a chunk
610.       is reused only if ALL its items are cached, otherwise the whole chunk is
611.       regenerated with the identical composition (so a resumed sampled run
612.       reproduces a fresh run's outputs -> identical verdict). Non-batched samplers
613.       use 1-item chunks == the per-cell granularity ("lose at most one cell").
614.     * PROGRESS: flushed START/DONE lines with a running count + ETA.
615.     """
616.     items = list(items)
617.     n = len(items)
618.     outs: List[Optional[float]] = [None] * n
619.     degs: List[Optional[float]] = [None] * n
620.     mat: List[Optional[List[float]]] = [None] * n
```

</details>


---

<sub>57s</sub>

### `powershell`

**Audit JSON/log with independent recomputation**

<details>
<summary>Arguments</summary>

```json
{
  "description": "Audit JSON/log with independent recomputation",
  "command": "Set-Location 'C:\\Users\\v-elzhang\\Desktop\\MyFolder\\cognitive console'; @'\nimport json, re, statistics, math\nfrom pathlib import Path\np = Path('results/c2b_adjudication_hf_2026-07-24/c2b_adjudication_results.json')\nlogp = Path('results/c2b_adjudication_hf_2026-07-24/adj2.run.log')\nobj = json.loads(p.read_text(encoding='utf-8'))\nprint('TOP_KEYS', sorted(obj.keys()))\nprint('VERDICT', obj.get('verdict'))\nprint('FROZEN', obj.get('frozen_params'))\naxes = obj.get('axis_results', [])\nprint('N_AXES', len(axes))\nfor a in axes:\n    axis=a.get('axis')\n    test=a.get('test_adjudication',{})\n    md=test.get('mean_diff'); ci=test.get('ci95') or test.get('ci') or {}\n    coh=test.get('coherence_ok')\n    print('AXIS',axis,'mean_diff',md,'ci',ci,'coh',coh,'passed_reported',test.get('passed'))\n\n# recompute pass/fail from prereg rule\nfp=obj.get('frozen_params',{})\ndelta=fp.get('delta',0.05)\nci_level=fp.get('ci_level')\n# support fallback nested\nif ci_level is None:\n    ci_level = obj.get('ci_level')\nprint('DELTA',delta,'CI_LEVEL',ci_level)\n\naxis_recalc={}\nfor a in axes:\n    axis=a['axis']; t=a['test_adjudication']\n    ci=t.get('ci95') or t.get('ci')\n    lo=ci.get('lo'); hi=ci.get('hi')\n    md=float(t.get('mean_diff'))\n    coh=bool(t.get('coherence_ok'))\n    ci_excl_zero=(lo>0) or (hi<0)\n    passed = ci_excl_zero and (md>=float(delta)) and coh\n    axis_recalc[axis]=passed\n    print('RECALC',axis,{'ci_excl_zero':ci_excl_zero,'md>=delta':md>=float(delta),'coh':coh,'passed':passed})\n\nnpass=sum(axis_recalc.values())\nif npass>=2: v='STRONG_GO'\nelif npass==1: v='CONDITIONAL_GO'\nelse: v='KILL_PLAN_D'\nprint('RECALC_VERDICT',v,'NPASS',npass)\n\n# inspect outcome arrays distributions and pairing sizes\nfor a in axes:\n    axis=a['axis']\n    t=a['test_adjudication']\n    for k in ['test_prompt_outcome','test_steer_outcome','test_baseline_outcome','dev_prompt_outcome','dev_steer_outcome','dev_baseline_outcome']:\n        arr=t.get(k)\n        if arr is None:\n            arr=a.get('dev_selection',{}).get(k)\n        if isinstance(arr,list) and arr:\n            mn=min(arr); mx=max(arr)\n            mean=sum(arr)/len(arr)\n            uniq=len(set(round(float(x),6) for x in arr))\n            all01=all((0<=float(x)<=1) for x in arr)\n            print('DIST',axis,k,'n',len(arr),'min',mn,'max',mx,'mean',round(mean,6),'uniq',uniq,'all01',all01,'all0',all(float(x)==0 for x in arr),'all1',all(float(x)==1 for x in arr))\n\n    # paired diff check\n    d=t.get('paired_diffs') or t.get('d_items') or t.get('d')\n    p=t.get('test_prompt_outcome'); s=t.get('test_steer_outcome')\n    if isinstance(p,list) and isinstance(s,list):\n        print('PAIRLEN',axis,'prompt',len(p),'steer',len(s),'equal',len(p)==len(s))\n        if len(p)==len(s):\n            calc=[float(si)-float(pi) for si,pi in zip(s,p)]\n            m=sum(calc)/len(calc)\n            print('PAIR_MEAN_CHECK',axis,'from_arrays',round(m,12),'reported',t.get('mean_diff'),'max_abs_d',round(max(abs(x) for x in calc),6))\n\n    # alpha/coherence landscape\n    dev=a.get('dev_selection',{})\n    alpha_grid=dev.get('alpha_grid_eval') or dev.get('alpha_grid') or []\n    if isinstance(alpha_grid,list) and alpha_grid:\n        rows=[]\n        for r in alpha_grid:\n            if isinstance(r,dict):\n                rows.append((r.get('alpha'), r.get('mean_outcome'), r.get('degeneracy'), r.get('coherence_ok')))\n        print('ALPHA_ROWS',axis,'count',len(rows))\n        for rr in rows:\n            print('ALPHA',axis,rr)\n    print('FROZEN_ALPHA',axis,dev.get('frozen_alpha'),'BEST_PROMPT',dev.get('best_prompt'))\n    print('BASE_DEGEN',axis,dev.get('baseline_degeneracy'))\n\n# log checks\nlog=logp.read_text(encoding='utf-8', errors='ignore')\nnum_done=len(re.findall(r'\\\\bDONE\\\\b',log))\nnum_start=len(re.findall(r'\\\\bSTART\\\\b',log))\nstall_hits=len(re.findall(r'stall|watchdog|ABORT|hard-exit',log,re.I))\nprint('LOG_COUNTS',{'START':num_start,'DONE':num_done,'stallish_terms':stall_hits})\nfor pat in ['PLANNED generations','TOTAL=11365','done=11365/11365','verdict=KILL_PLAN_D','ADJ2_END']:\n    m=re.search(pat,log)\n    print('LOG_HAS',pat,bool(m))\n\n# print final 20 non-empty lines for end status\nlines=[ln for ln in log.splitlines() if ln.strip()]\nprint('LOG_TAIL')\nfor ln in lines[-25:]:\n    print(ln)\n'@ | python -"
}
```

</details>

<details>
<summary>39 lines</summary>

```
TOP_KEYS ['axes', 'axis_passes', 'backend', 'c1_layer_info', 'frozen_params', 'generated_at', 'hardware', 'model', 'platform', 'prereg', 'protocol_frozen', 'run_type', 'started_at', 'use_fixture', 'valid_for_paper', 'verdict', 'wall_clock_seconds']
VERDICT KILL_PLAN_D
FROZEN {'alpha_grid': [2.0, 4.0, 6.0, 8.0, 12.0, 16.0, 24.0], 'delta': 0.05, 'k_samples': 5, 'n_items_by_axis': {'deliberation': 60, 'skepticism': 60, 'uncertainty_awareness': 80}, 'coherence_max_ratio': 1.5, 'coherence_eps_floor': 0.02, 'bootstrap_b': 10000, 'familywise_alpha': 0.05, 'n_axes': 3, 'bonferroni_ci_level': 0.9833333333333333, 'dev_fraction': 0.3333333333333333, 'bootstrap': 'paired item-cluster (resample items, each carries its k)', 'decision': 'CI excludes 0 AND mean(d) >= delta AND coherence gate pass', 'verdict_rule': '>=2 pass STRONG_GO; ==1 CONDITIONAL_GO; 0 KILL_PLAN_D', 'prereg': 'docs/ledgers/prereg-c2b-adjudication.md (FROZEN 2026-07-23)'}
N_AXES 0
DELTA 0.05 CI_LEVEL None
RECALC_VERDICT KILL_PLAN_D NPASS 0
LOG_COUNTS {'START': 0, 'DONE': 0, 'stallish_terms': 1}
LOG_HAS PLANNED generations True
LOG_HAS TOTAL=11365 True
LOG_HAS done=11365/11365 True
LOG_HAS verdict=KILL_PLAN_D False
LOG_HAS ADJ2_END True
LOG_TAIL
[c2b-adj] axis=uncertainty_awareness phase=dev_alpha 3/7 items=27 START done=9365/11365 fresh=9365 elapsed=1397s eta=298s
[c2b-adj] axis=uncertainty_awareness phase=dev_alpha 3/7 items=27 DONE done=9500/11365 fresh=9500 elapsed=1415s eta=278s
[c2b-adj] axis=uncertainty_awareness phase=dev_alpha 4/7 items=27 START done=9500/11365 fresh=9500 elapsed=1415s eta=278s
[c2b-adj] axis=uncertainty_awareness phase=dev_alpha 4/7 items=27 DONE done=9635/11365 fresh=9635 elapsed=1434s eta=257s
[c2b-adj] axis=uncertainty_awareness phase=dev_alpha 5/7 items=27 START done=9635/11365 fresh=9635 elapsed=1434s eta=257s
[c2b-adj] axis=uncertainty_awareness phase=dev_alpha 5/7 items=27 DONE done=9770/11365 fresh=9770 elapsed=1452s eta=237s
[c2b-adj] axis=uncertainty_awareness phase=dev_alpha 6/7 items=27 START done=9770/11365 fresh=9770 elapsed=1452s eta=237s
[c2b-adj] axis=uncertainty_awareness phase=dev_alpha 6/7 items=27 DONE done=9905/11365 fresh=9905 elapsed=1470s eta=217s
[c2b-adj] axis=uncertainty_awareness phase=dev_alpha 7/7 items=27 START done=9905/11365 fresh=9905 elapsed=1470s eta=217s
[c2b-adj] axis=uncertainty_awareness phase=dev_alpha 7/7 items=27 DONE done=10040/11365 fresh=10040 elapsed=1488s eta=196s
[c2b-adj] axis=uncertainty_awareness phase=test_prompt 1/1 items=53 START done=10040/11365 fresh=10040 elapsed=1488s eta=196s
[c2b-adj] axis=uncertainty_awareness phase=test_prompt 1/1 items=53 DONE done=10305/11365 fresh=10305 elapsed=1525s eta=157s
[c2b-adj] axis=uncertainty_awareness phase=test_steer 1/1 items=53 START done=10305/11365 fresh=10305 elapsed=1525s eta=157s
[c2b-adj] axis=uncertainty_awareness phase=test_steer 1/1 items=53 DONE done=10570/11365 fresh=10570 elapsed=1556s eta=117s
[c2b-adj] axis=uncertainty_awareness phase=test_baseline 1/1 items=53 START done=10570/11365 fresh=10570 elapsed=1556s eta=117s
[c2b-adj] axis=uncertainty_awareness phase=test_baseline 1/1 items=53 DONE done=10835/11365 fresh=10835 elapsed=1588s eta=78s
[c2b-adj] axis=uncertainty_awareness phase=conflict 1/1 items=53 START done=10835/11365 fresh=10835 elapsed=1588s eta=78s
[c2b-adj] axis=uncertainty_awareness phase=conflict 1/1 items=53 DONE done=11100/11365 fresh=11100 elapsed=1625s eta=39s
[c2b-adj] axis=uncertainty_awareness phase=conflict_pole 1/1 items=53 START done=11100/11365 fresh=11100 elapsed=1625s eta=39s
[c2b-adj] axis=uncertainty_awareness phase=conflict_pole 1/1 items=53 DONE done=11365/11365 fresh=11365 elapsed=1666s eta=0s
[c2b-adj] disk post-run: disk ok: total 0.18GB < budget 60GB (ceiling 70GB) [/root/autodl-tmp/hf_home=0.18GB].
[c2b-adj] VERDICT: KILL_PLAN_D  (axes passing: 0/3)
[c2b-adj] wrote results/c2b_adjudication_hf_2026-07-24/c2b_adjudication_results.json  (exp c2b-adj-deac6326-0001)  wall=1732.3s
ADJ2_EXIT_RC=0
ADJ2_END Fri Jul 24 13:56:12 CST 2026
<shellId: 1 completed with exit code 0>
```

</details>


---

<sub>55s</sub>

### `powershell`

**Get exact file lengths**

<details>
<summary>Arguments</summary>

```json
{
  "description": "Get exact file lengths",
  "command": "Set-Location 'C:\\Users\\v-elzhang\\Desktop\\MyFolder\\cognitive console'; Get-Item 'results\\c2b_adjudication_hf_2026-07-24\\c2b_adjudication_results.json','results\\c2b_adjudication_hf_2026-07-24\\adj2.run.log','src\\cognitive_console\\experiments\\adjudicate_c2b.py','scripts\\run_c2b_adjudication.py' | Select-Object Name,Length | Format-List"
}
```

</details>

<details>
<summary>9 lines</summary>

```
Name   : c2b_adjudication_results.json
Length : 15841

Name   : adj2.run.log
Length : 28188

Name   : adjudicate_c2b.py
Length : 43886

Name   : run_c2b_adjudication.py
Length : 29437
<shellId: 2 completed with exit code 0>
```

</details>


---

<sub>1m 0s</sub>

### `view`

**view the file at C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\results\c2b_adjudication_hf_2026-07-24\c2b_adjudication_results.json.**

C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\results\c2b_adjudication_hf_2026-07-24\c2b_adjudication_results.json

<details>
<summary>718 lines</summary>

```
1. {
2.   "verdict": "KILL_PLAN_D",
3.   "axis_passes": {
4.     "deliberation": false,
5.     "skepticism": false,
6.     "uncertainty_awareness": false
7.   },
8.   "frozen_params": {
9.     "alpha_grid": [
10.       2.0,
11.       4.0,
12.       6.0,
13.       8.0,
14.       12.0,
15.       16.0,
16.       24.0
17.     ],
18.     "delta": 0.05,
19.     "k_samples": 5,
20.     "n_items_by_axis": {
21.       "deliberation": 60,
22.       "skepticism": 60,
23.       "uncertainty_awareness": 80
24.     },
25.     "coherence_max_ratio": 1.5,
26.     "coherence_eps_floor": 0.02,
27.     "bootstrap_b": 10000,
28.     "familywise_alpha": 0.05,
29.     "n_axes": 3,
30.     "bonferroni_ci_level": 0.9833333333333333,
31.     "dev_fraction": 0.3333333333333333,
32.     "bootstrap": "paired item-cluster (resample items, each carries its k)",
33.     "decision": "CI excludes 0 AND mean(d) >= delta AND coherence gate pass",
34.     "verdict_rule": ">=2 pass STRONG_GO; ==1 CONDITIONAL_GO; 0 KILL_PLAN_D",
35.     "prereg": "docs/ledgers/prereg-c2b-adjudication.md (FROZEN 2026-07-23)"
36.   },
37.   "axes": [
38.     {
39.       "axis": "deliberation",
40.       "layer": 20,
41.       "n_dev": 20,
42.       "n_test": 40,
43.       "k": 5,
44.       "dev_selection": {
45.         "best_prompt_id": "delib-strong-09",
46.         "best_prompt_text": "Think slowly and rigorously. Enumerate the considerations, compare them, and let a conclusion emerge from that analysis.",
47.         "dev_prompt_outcome": 0.06,
48.         "frozen_alpha": 2.0,
49.         "dev_steer_outcome": 0.1,
50.         "baseline_degeneracy": 0.027361333359291244,
51.         "alpha_grid": [
52.           {
53.             "alpha": 2.0,
54.             "dev_steer_outcome": 0.1,
55.             "degeneracy": 0.030131742564638055,
56.             "coherence_ok": true
57.           },
58.           {
59.             "alpha": 4.0,
60.             "dev_steer_outcome": 0.06999999999999999,
61.             "degeneracy": 0.033649947110964445,
62.             "coherence_ok": true
63.           },
64.           {
65.             "alpha": 6.0,
66.             "dev_steer_outcome": 0.06999999999999999,
67.             "degeneracy": 0.029512056256522312,
68.             "coherence_ok": true
69.           },
70.           {
71.             "alpha": 8.0,
72.             "dev_steer_outcome": 0.06,
73.             "degeneracy": 0.03566521296564354,
74.             "coherence_ok": true
75.           },
76.           {
77.             "alpha": 12.0,
78.             "dev_steer_outcome": 0.04,
79.             "degeneracy": 0.036096827998987266,
80.             "coherence_ok": true
81.           },
82.           {
83.             "alpha": 16.0,
84.             "dev_steer_outcome": 0.05,
85.             "degeneracy": 0.034208495182016296,
86.             "coherence_ok": true
87.           },
88.           {
89.             "alpha": 24.0,
90.             "dev_steer_outcome": 0.06,
91.             "degeneracy": 0.03815809664695778,
92.             "coherence_ok": true
93.           }
94.         ],
95.         "any_alpha_passes_gate": true
96.       },
97.       "per_item_prompt": [
98.         0.0,
99.         0.0,
100.         0.6,
101.         0.0,
102.         0.0,
103.         0.0,
104.         0.0,
105.         0.0,
106.         0.0,
107.         0.0,
108.         0.0,
109.         0.0,
110.         0.2,
111.         0.0,
112.         0.0,
113.         0.0,
114.         0.0,
115.         0.0,
116.         0.0,
117.         0.0,
118.         0.0,
119.         0.0,
120.         0.0,
121.         0.0,
122.         0.0,
123.         0.0,
124.         0.0,
125.         0.0,
126.         0.0,
127.         0.0,
128.         0.0,
129.         0.0,
130.         0.0,
131.         0.0,
132.         0.0,
133.         0.0,
134.         0.0,
135.         0.0,
136.         0.0,
137.         0.0
138.       ],
139.       "per_item_steer": [
140.         0.0,
141.         0.0,
142.         0.0,
143.         0.0,
144.         0.0,
145.         0.0,
146.         0.0,
147.         0.0,
148.         0.0,
149.         0.0,
150.         0.0,
151.         0.0,
152.         0.4,
153.         0.0,
154.         0.0,
155.         0.0,
156.         0.0,
157.         0.0,
158.         0.0,
159.         0.0,
160.         0.0,
161.         0.0,
162.         0.0,
163.         0.0,
164.         0.0,
165.         0.0,
166.         0.0,
167.         0.0,
168.         0.0,
169.         0.0,
170.         0.0,
171.         0.0,
172.         0.0,
173.         0.2,
174.         0.0,
175.         0.6,
176.         0.2,
177.         0.0,
178.         0.0,
179.         0.0
180.       ],
181.       "per_item_diff": [
182.         0.0,
183.         0.0,
184.         -0.6,
185.         0.0,
186.         0.0,
187.         0.0,
188.         0.0,
189.         0.0,
190.         0.0,
191.         0.0,
192.         0.0,
193.         0.0,
194.         0.2,
195.         0.0,
196.         0.0,
197.         0.0,
198.         0.0,
199.         0.0,
200.         0.0,
201.         0.0,
202.         0.0,
203.         0.0,
204.         0.0,
205.         0.0,
206.         0.0,
207.         0.0,
208.         0.0,
209.         0.0,
210.         0.0,
211.         0.0,
212.         0.0,
213.         0.0,
214.         0.0,
215.         0.2,
216.         0.0,
217.         0.6,
218.         0.2,
219.         0.0,
220.         0.0,
221.         0.0
222.       ],
223.       "mean_diff": 0.015000000000000003,
224.       "ci_lo": -0.04,
225.       "ci_hi": 0.06999999999999999,
226.       "ci_level": 0.9833333333333333,
227.       "bootstrap_b": 10000,
228.       "coherence_ok": true,
229.       "test_steer_degeneracy": 0.029027809038202585,
230.       "test_baseline_degeneracy": 0.03036284888642584,
231.       "delta": 0.05,
232.       "passed": false,
233.       "conflict": {
234.         "note": "SECONDARY/descriptive only \u2014 NOT part of the verdict (prereg \u00a74).",
235.         "alpha_opposite": -2.0,
236.         "mean_conflict_outcome": 0.03,
237.         "mean_prompt_pole_outcome": 0.02,
238.         "latent_drags_down": false
239.       },
240.       "descriptive": {}
241.     },
242.     {
243.       "axis": "skepticism",
244.       "layer": 20,
245.       "n_dev": 20,
246.       "n_test": 40,
247.       "k": 5,
248.       "dev_selection": {
249.         "best_prompt_id": "skep-strong-06",
250.         "best_prompt_text": "Be suspicious and rigorous. Interrogate the sources, distrust confident-sounding claims, and verify before you agree with anything.",
251.         "dev_prompt_outcome": 0.55,
252.         "frozen_alpha": 6.0,
253.         "dev_steer_outcome": 0.45999999999999996,
254.         "baseline_degeneracy": 0.0011819967266775777,
255.         "alpha_grid": [
256.           {
257.             "alpha": 2.0,
258.             "dev_steer_outcome": 0.45,
259.             "degeneracy": 0.0009973813420621944,
260.             "coherence_ok": true
261.           },
262.           {
263.             "alpha": 4.0,
264.             "dev_steer_outcome": 0.45,
265.             "degeneracy": 0.0006099166301009218,
266.             "coherence_ok": true
267.           },
268.           {
269.             "alpha": 6.0,
270.             "dev_steer_outcome": 0.45999999999999996,
271.             "degeneracy": 0.0009855217558721607,
272.             "coherence_ok": true
273.           },
274.           {
275.             "alpha": 8.0,
276.             "dev_steer_outcome": 0.45,
277.             "degeneracy": 0.0014531555962191967,
278.             "coherence_ok": true
279.           },
280.           {
281.             "alpha": 12.0,
282.             "dev_steer_outcome": 0.45,
283.             "degeneracy": 0.0010108510777825698,
284.             "coherence_ok": true
285.           },
286.           {
287.             "alpha": 16.0,
288.             "dev_steer_outcome": 0.45,
289.             "degeneracy": 0.0021061540918196507,
290.             "coherence_ok": true
291.           },
292.           {
293.             "alpha": 24.0,
294.             "dev_steer_outcome": 0.45,
295.             "degeneracy": 0.0018254114546373077,
296.             "coherence_ok": true
297.           }
298.         ],
299.         "any_alpha_passes_gate": true
300.       },
301.       "per_item_prompt": [
302.         1.0,
303.         1.0,
304.         1.0,
305.         1.0,
306.         1.0,
307.         1.0,
308.         1.0,
309.         0.8,
310.         0.0,
311.         1.0,
312.         1.0,
313.         1.0,
314.         1.0,
315.         0.0,
316.         1.0,
317.         1.0,
318.         1.0,
319.         0.8,
320.         1.0,
321.         0.0,
322.         1.0,
323.         1.0,
324.         1.0,
325.         0.0,
326.         1.0,
327.         0.8,
328.         0.4,
329.         1.0,
330.         1.0,
331.         1.0,
332.         1.0,
333.         1.0,
334.         0.0,
335.         1.0,
336.         0.2,
337.         1.0,
338.         1.0,
339.         0.0,
340.         0.0,
341.         1.0
342.       ],
343.       "per_item_steer": [
344.         1.0,
345.         1.0,
346.         1.0,
347.         1.0,
348.         1.0,
349.         1.0,
350.         1.0,
351.         1.0,
352.         0.0,
353.         1.0,
354.         1.0,
355.         0.0,
356.         1.0,
357.         0.0,
358.         1.0,
359.         1.0,
360.         0.0,
361.         1.0,
362.         1.0,
363.         0.0,
364.         0.0,
365.         1.0,
366.         1.0,
367.         0.0,
368.         1.0,
369.         1.0,
370.         0.0,
371.         1.0,
372.         0.0,
373.         1.0,
374.         1.0,
375.         1.0,
376.         0.0,
377.         1.0,
378.         0.0,
379.         0.6,
380.         1.0,
381.         1.0,
382.         0.2,
383.         1.0
384.       ],
385.       "per_item_diff": [
386.         0.0,
387.         0.0,
388.         0.0,
389.         0.0,
390.         0.0,
391.         0.0,
392.         0.0,
393.         0.19999999999999996,
394.         0.0,
395.         0.0,
396.         0.0,
397.         -1.0,
398.         0.0,
399.         0.0,
400.         0.0,
401.         0.0,
402.         -1.0,
403.         0.19999999999999996,
404.         0.0,
405.         0.0,
406.         -1.0,
407.         0.0,
408.         0.0,
409.         0.0,
410.         0.0,
411.         0.19999999999999996,
412.         -0.4,
413.         0.0,
414.         -1.0,
415.         0.0,
416.         0.0,
417.         0.0,
418.         0.0,
419.         0.0,
420.         -0.2,
421.         -0.4,
422.         0.0,
423.         1.0,
424.         0.2,
425.         0.0
426.       ],
427.       "mean_diff": -0.08,
428.       "ci_lo": -0.225,
429.       "ci_hi": 0.045,
430.       "ci_level": 0.9833333333333333,
431.       "bootstrap_b": 10000,
432.       "coherence_ok": true,
433.       "test_steer_degeneracy": 0.0013307646057646072,
434.       "test_baseline_degeneracy": 0.001508878376525436,
435.       "delta": 0.05,
436.       "passed": false,
437.       "conflict": {
438.         "note": "SECONDARY/descriptive only \u2014 NOT part of the verdict (prereg \u00a74).",
439.         "alpha_opposite": -6.0,
440.         "mean_conflict_outcome": 0.775,
441.         "mean_prompt_pole_outcome": 0.775,
442.         "latent_drags_down": false
443.       },
444.       "descriptive": {}
445.     },
446.     {
447.       "axis": "uncertainty_awareness",
448.       "layer": 20,
449.       "n_dev": 27,
450.       "n_test": 53,
451.       "k": 5,
452.       "dev_selection": {
453.         "best_prompt_id": "unc-strong-01",
454.         "best_prompt_text": "Be honest about what you do not know. Flag every uncertainty and tell me how confident you really are.",
455.         "dev_prompt_outcome": 0.8294785185185184,
456.         "frozen_alpha": 8.0,
457.         "dev_steer_outcome": 0.5629629629629629,
458.         "baseline_degeneracy": 0.009584693074124987,
459.         "alpha_grid": [
460.           {
461.             "alpha": 2.0,
462.             "dev_steer_outcome": 0.5373703703703703,
463.             "degeneracy": 0.0045380278238505945,
464.             "coherence_ok": true
465.           },
466.           {
467.             "alpha": 4.0,
468.             "dev_steer_outcome": 0.5370881481481482,
469.             "degeneracy": 0.004649663154766579,
470.             "coherence_ok": true
471.           },
472.           {
473.             "alpha": 6.0,
474.             "dev_steer_outcome": 0.5324214814814815,
475.             "degeneracy": 0.0031480217203036795,
476.             "coherence_ok": true
477.           },
478.           {
479.             "alpha": 8.0,
480.             "dev_steer_outcome": 0.5629629629629629,
481.             "degeneracy": 0.003061252573031836,
482.             "coherence_ok": true
483.           },
484.           {
485.             "alpha": 12.0,
486.             "dev_steer_outcome": 0.5085466666666666,
487.             "degeneracy": 0.004599265761640202,
488.             "coherence_ok": true
489.           },
490.           {
491.             "alpha": 16.0,
492.             "dev_steer_outcome": 0.5599585185185185,
493.             "degeneracy": 0.004421362358385246,
494.             "coherence_ok": true
495.           },
496.           {
497.             "alpha": 24.0,
498.             "dev_steer_outcome": 0.5453148148148148,
499.             "degeneracy": 0.00409204909204909,
500.             "coherence_ok": true
501.           }
502.         ],
503.         "any_alpha_passes_gate": true
504.       },
505.       "per_item_prompt": [
506.         0.844,
507.         0.75,
508.         0.884,
509.         0.8,
510.         0.8,
511.         0.9435,
512.         0.75,
513.         0.8,
514.         1.0,
515.         0.9974999999999999,
516.         0.992,
517.         0.75,
518.         0.942,
519.         0.9480000000000001,
520.         0.75,
521.         0.75,
522.         0.75,
523.         0.75,
524.         0.75,
525.         0.75,
526.         0.992,
527.         0.976,
528.         0.62702,
529.         0.79902,
530.         0.8480000000000001,
531.         0.9,
532.         0.8,
533.         0.974,
534.         0.982,
535.         0.75,
536.         0.95,
537.         0.7995,
538.         0.9995,
539.         0.75,
540.         1.0,
541.         0.9495000000000001,
542.         0.8955,
543.         0.792,
544.         0.75,
545.         0.85,
546.         1.0,
547.         0.75,
548.         0.782,
549.         0.85,
550.         0.792,
551.         0.95,
552.         0.85,
553.         0.9400000000000001,
554.         0.75,
555.         0.75,
556.         0.897,
557.         0.75,
558.         0.792
559.       ],
560.       "per_item_steer": [
561.         1.0,
562.         0.5195000000000001,
563.         0.09750000000000003,
564.         0.0,
565.         0.0,
566.         0.9974999999999999,
567.         0.019500000000000007,
568.         1.0,
569.         1.0,
570.         1.0,
571.         0.0,
572.         0.998,
573.         0.09750000000000003,
574.         0.999,
575.         1.0,
576.         0.458,
577.         0.9494999999999999,
578.         0.75,
579.         0.9,
580.         0.8985,
581.         0.0,
582.         0.09750000000000003,
583.         1.0,
584.         0.15,
585.         1.0,
586.         0.09750000000000003,
587.         1.0,
588.         0.9974999999999999,
589.         0.0,
590.         0.75,
591.         0.6,
592.         0.85,
593.         1.0,
594.         1.0,
595.         0.019500000000000007,
596.         0.9984999999999999,
597.         1.0,
598.         0.45,
599.         0.75,
600.         0.07800000000000003,
601.         0.0,
602.         0.0,
603.         0.65238,
604.         0.36950000000000005,
605.         0.9490000000000001,
606.         0.2775,
607.         1.0,
608.         1.0,
609.         0.75,
610.         0.75,
611.         1.0,
612.         1.0,
613.         0.6
614.       ],
615.       "per_item_diff": [
616.         0.15600000000000003,
617.         -0.23049999999999993,
618.         -0.7865,
619.         -0.8,
620.         -0.8,
621.         0.05399999999999994,
622.         -0.7305,
623.         0.19999999999999996,
624.         0.0,
625.         0.0025000000000000577,
626.         -0.992,
627.         0.248,
628.         -0.8444999999999999,
629.         0.050999999999999934,
630.         0.25,
631.         -0.292,
632.         0.1994999999999999,
633.         0.0,
634.         0.15000000000000002,
635.         0.14849999999999997,
636.         -0.992,
637.         -0.8785,
638.         0.37298,
639.         -0.6490199999999999,
640.         0.1519999999999999,
641.         -0.8025,
642.         0.19999999999999996,
643.         0.023499999999999965,
644.         -0.982,
645.         0.0,
646.         -0.35,
647.         0.05049999999999999,
648.         0.0004999999999999449,
649.         0.25,
650.         -0.9805,
651.         0.04899999999999982,
652.         0.10450000000000004,
653.         -0.342,
654.         0.0,
655.         -0.7719999999999999,
656.         -1.0,
657.         -0.75,
658.         -0.12962000000000007,
659.         -0.4804999999999999,
660.         0.15700000000000003,
661.         -0.6724999999999999,
662.         0.15000000000000002,
663.         0.05999999999999994,
664.         0.0,
665.         0.0,
666.         0.10299999999999998,
667.         0.25,
668.         -0.19200000000000006
669.       ],
670.       "mean_diff": -0.22767283018867926,
671.       "ci_lo": -0.36977938679245265,
672.       "ci_hi": -0.0916042641509434,
673.       "ci_level": 0.9833333333333333,
674.       "bootstrap_b": 10000,
675.       "coherence_ok": true,
676.       "test_steer_degeneracy": 0.004970281050632619,
677.       "test_baseline_degeneracy": 0.004764594672282605,
678.       "delta": 0.05,
679.       "passed": false,
680.       "conflict": {
681.         "note": "SECONDARY/descriptive only \u2014 NOT part of the verdict (prereg \u00a74).",
682.         "alpha_opposite": -8.0,
683.         "mean_conflict_outcome": 0.8414901886792452,
684.         "mean_prompt_pole_outcome": 0.8478875471698113,
685.         "latent_drags_down": true
686.       },
687.       "descriptive": {
688.         "set_ece_note": "Per-item outcome is the PROPER 1 - Brier = 1 - (conf - correct)**2 (decision D-0025; delta on this scale); the binned set ECE is DESCRIPTIVE only and is NOT part of the gate."
689.       }
690.     }
691.   ],
692.   "model": "/root/autodl-tmp/models/Qwen2.5-7B-Instruct",
693.   "hardware": "cuda-float16",
694.   "run_type": "exploratory",
695.   "valid_for_paper": false,
696.   "protocol_frozen": true,
697.   "prereg": "docs/ledgers/prereg-c2b-adjudication.md (FROZEN 2026-07-23)",
698.   "started_at": "2026-07-24T05:27:18.922433+00:00",
699.   "generated_at": "2026-07-24T05:56:11.177359+00:00",
700.   "wall_clock_seconds": 1732.25,
701.   "platform": "Linux-5.15.0-78-generic-x86_64-with-glibc2.35",
702.   "use_fixture": false,
703.   "backend": "hf",
704.   "c1_layer_info": {
705.     "deliberation": {
706.       "chosen_layer": 20,
707.       "stable_layer_found": true
708.     },
709.     "skepticism": {
710.       "chosen_layer": 20,
711.       "stable_layer_found": true
712.     },
713.     "uncertainty_awareness": {
714.       "chosen_layer": 20,
715.       "stable_layer_found": true
716.     }
717.   }
718. }
```

</details>


---

<sub>1m 3s</sub>

### `view` — Failed

**view the file at C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\results\c2b_adjudication_hf_2026-07-24\checkpoints.**

C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\results\c2b_adjudication_hf_2026-07-24\checkpoints

```
Path does not exist
```


---

<sub>1m 4s</sub>

### `view`

**view the file at C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\results\c2b_adjudication_hf_2026-07-24.**

C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\results\c2b_adjudication_hf_2026-07-24

<details>
<summary>6 lines</summary>

```
adj2.run.log
c1
c2b_adjudication_results.json
c2b_adjudication_summary.md
c2b_adjudication_table.manifest.yaml
experiment-registry.yaml
```

</details>


---

<sub>1m 16s</sub>

### `rg`

**def adjudicate_axis|def select_on_dev|def adjudicate\(|per_item_prompt|per_item_steer|per_item_diff|test_items|dev_items|split_dev_test|alpha_grid|coherence_ok|baseline_degeneracy|any_alpha_passes_gate|axis_passes|three_tier_verdict**

"def adjudicate_axis|def select_on_dev|def adjudicate\(|per_item_prompt|per_item_steer|per_item_diff|test_items|dev_items|split_dev_test|alpha_grid|coherence_ok|baseline_degeneracy|any_alpha_passes_gate|axis_passes|three_tier_verdict" (src\cognitive_console\experiments\adjudicate_c2b.py)

<details>
<summary>75 matches</summary>

```
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:19:* DEV ~1/3 selects+freezes α+prompt  -> ``split_dev_test`` + ``select_on_dev`` (§2/§4)
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:22:* ≥2 / 1 / 0 axes pass -> STRONG_GO / CONDITIONAL_GO / KILL_PLAN_D -> ``three_tier_verdict`` (§4)
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:249:    """DEV/TEST sizes matching ``split_dev_test`` (for up-front budget planning)."""
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:257:    alpha_grid: Sequence[float] = ALPHA_GRID, dev_fraction: float = DEV_FRACTION,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:262:      DEV  = k * n_dev * (n_strong_prompts + 1 baseline + len(alpha_grid))
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:271:        dev = k * n_dev * (n_strong + 1 + len(alpha_grid))
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:293:def split_dev_test(item_ids: Sequence[str], dev_fraction: float = DEV_FRACTION,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:395:def axis_pass(mean_d: float, ci_lo: float, ci_hi: float, coherence_ok: bool,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:399:    return bool(ci_excludes_zero(ci_lo, ci_hi) and (mean_d >= delta) and coherence_ok)
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:402:def three_tier_verdict(axis_passes: Dict[str, bool]) -> str:
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:406:    n_pass = sum(1 for v in axis_passes.values() if v)
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:592:    baseline_degeneracy: float
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:593:    alpha_grid: List[Dict[str, object]]      # per-α: outcome, degeneracy, coherence_ok
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:594:    any_alpha_passes_gate: bool
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:672:def select_on_dev(
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:673:    sampler: OutcomeSampler, spec: AxisAdjSpec, dev_items: Sequence[Dict],
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:674:    k: int = K_SAMPLES, alpha_grid: Sequence[float] = ALPHA_GRID,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:691:            sampler, spec.axis, dev_items, ptext, 0.0, k, spec.direction, spec.layer,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:700:        sampler, spec.axis, dev_items, spec.neutral_prompt, 0.0, k, spec.direction,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:703:    baseline_degeneracy = float(base_deg.mean())
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:704:    gate_ceiling = coherence_max_ratio * baseline_degeneracy + COHERENCE_EPS_FLOOR
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:710:    n_alpha = len(alpha_grid)
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:711:    for ai, a in enumerate(alpha_grid):
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:713:            sampler, spec.axis, dev_items, spec.neutral_prompt, float(a), k,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:718:        coherence_ok = steer_deg <= gate_ceiling + 1e-12
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:721:            "degeneracy": steer_deg, "coherence_ok": coherence_ok,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:723:        if coherence_ok and (best_steer_out is None or steer_out > best_steer_out):
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:730:        dev_steer_outcome=best_steer_out, baseline_degeneracy=baseline_degeneracy,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:731:        alpha_grid=grid_rows, any_alpha_passes_gate=frozen_alpha is not None,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:744:    per_item_prompt: List[float]
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:745:    per_item_steer: List[float]
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:746:    per_item_diff: List[float]
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:752:    coherence_ok: bool
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:754:    test_baseline_degeneracy: float
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:765:def adjudicate_axis(
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:767:    k: int = K_SAMPLES, alpha_grid: Sequence[float] = ALPHA_GRID,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:786:    split = split_dev_test(ids, dev_fraction=dev_fraction, seed=seed)
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:787:    dev_items = [by_id[i] for i in split.dev_ids]
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:788:    test_items = [by_id[i] for i in split.test_ids]
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:790:    dev_sel = select_on_dev(sampler, spec, dev_items, k=k, alpha_grid=alpha_grid,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:798:        n_test = len(test_items)
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:800:            sampler, spec.axis, test_items, dev_sel.best_prompt_text, 0.0, k,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:804:            axis=spec.axis, layer=int(spec.layer), n_dev=len(dev_items), n_test=n_test,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:806:            per_item_prompt=[float(x) for x in prompt_out],
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:807:            per_item_steer=[], per_item_diff=[],
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:809:            ci_level=ci_level, bootstrap_b=int(bootstrap_b), coherence_ok=False,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:811:            test_baseline_degeneracy=dev_sel.baseline_degeneracy,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:819:        sampler, spec.axis, test_items, dev_sel.best_prompt_text, 0.0, k,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:823:        sampler, spec.axis, test_items, spec.neutral_prompt, frozen_alpha, k,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:827:        sampler, spec.axis, test_items, spec.neutral_prompt, 0.0, k,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:831:    per_item_diff = steer_out - prompt_out
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:832:    ci = cluster_bootstrap_ci(per_item_diff, b=bootstrap_b, ci_level=ci_level,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:837:    coherence_ok = (test_steer_deg
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:840:    passed = axis_pass(ci.point, ci.ci_lo, ci.ci_hi, coherence_ok, delta=delta)
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:842:    conflict = _conflict_cell(sampler, spec, test_items, dev_sel.best_prompt_id,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:844:    descriptive = _descriptive(spec.axis, test_items, prompt_mat, steer_mat)
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:847:        axis=spec.axis, layer=int(spec.layer), n_dev=len(dev_items),
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:848:        n_test=len(test_items), k=int(k), dev_selection=asdict(dev_sel),
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:849:        per_item_prompt=[float(x) for x in prompt_out],
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:850:        per_item_steer=[float(x) for x in steer_out],
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:851:        per_item_diff=[float(x) for x in per_item_diff],
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:853:        bootstrap_b=int(bootstrap_b), coherence_ok=coherence_ok,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:855:        test_baseline_degeneracy=test_baseline_deg,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:860:def _conflict_cell(sampler: OutcomeSampler, spec: AxisAdjSpec, test_items: Sequence[Dict],
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:867:        sampler, spec.axis, test_items, best_prompt_text, -float(frozen_alpha), k,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:871:        sampler, spec.axis, test_items, best_prompt_text, 0.0, k,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:883:def _descriptive(axis: str, test_items: Sequence[Dict],
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:903:    axis_passes: Dict[str, bool]
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:910:            "axis_passes": self.axis_passes,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:918:        "alpha_grid": list(ALPHA_GRID),
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:936:def adjudicate(
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:939:    k: int = K_SAMPLES, alpha_grid: Sequence[float] = ALPHA_GRID,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:955:            sampler, spec, k=k, alpha_grid=alpha_grid, bootstrap_b=bootstrap_b,
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:960:    verdict = three_tier_verdict(passes)
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py:961:    return AdjudicationReport(axis_results=results, axis_passes=passes,
```

</details>


---

<sub>1m 16s</sub>

### `view`

**view the file at C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py.**

C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\src\cognitive_console\experiments\adjudicate_c2b.py (lines 620-980)

<details>
<summary>344 lines</summary>

```
620.     mat: List[Optional[List[float]]] = [None] * n
621. 
622.     ckpt = ctx.checkpoint if ctx is not None else None
623.     prog = ctx.progress if ctx is not None else None
624. 
625.     supports_batch = bool(getattr(sampler, "supports_batch", False))
626.     if supports_batch:
627.         items_per_batch = max(1, int(getattr(sampler, "batch_size", 1)) // max(1, int(k)))
628.     else:
629.         items_per_batch = 1
630. 
631.     if prog is not None:
632.         prog.cell_start(axis, phase, cell_idx, cell_total, n)
633. 
634.     for start in range(0, n, items_per_batch):
635.         chunk_idx = list(range(start, min(start + items_per_batch, n)))
636.         chunk_items = [items[i] for i in chunk_idx]
637. 
638.         cached = None
639.         if ckpt is not None:
640.             got = [ckpt.get(axis, phase, cell_key, str(it["id"])) for it in chunk_items]
641.             if all(g is not None for g in got):
642.                 cached = got  # whole chunk resumable -> skip generation
643. 
644.         if cached is not None:
645.             for local, i in enumerate(chunk_idx):
646.                 o, d = cached[local]
647.                 outs[i] = float(np.mean(o))
648.                 degs[i] = float(np.mean(d))
649.                 mat[i] = list(o)
650.             if prog is not None:
651.                 prog.add(len(chunk_idx) * int(k), fresh=False)
652.         else:
653.             batches = sampler.sample_batch(axis, chunk_items, instruction, alpha,
654.                                            k, direction, layer)
655.             for local, i in enumerate(chunk_idx):
656.                 b = batches[local]
657.                 outs[i] = b.mean_outcome()
658.                 degs[i] = b.mean_degeneracy()
659.                 mat[i] = list(b.outcomes)
660.                 if ckpt is not None:
661.                     ckpt.put(axis, phase, cell_key, str(chunk_items[local]["id"]),
662.                              b.outcomes, b.degeneracies, alpha, instruction)
663.             if prog is not None:
664.                 prog.add(len(chunk_idx) * int(k), fresh=True)
665. 
666.     if prog is not None:
667.         prog.cell_end(axis, phase, cell_idx, cell_total, n)
668. 
669.     return np.asarray(outs, dtype=float), np.asarray(degs, dtype=float), np.asarray(mat, dtype=float)
670. 
671. 
672. def select_on_dev(
673.     sampler: OutcomeSampler, spec: AxisAdjSpec, dev_items: Sequence[Dict],
674.     k: int = K_SAMPLES, alpha_grid: Sequence[float] = ALPHA_GRID,
675.     coherence_max_ratio: float = COHERENCE_MAX_RATIO,
676.     ctx: Optional[RunContext] = None,
677. ) -> DevSelection:
678.     """Select+FREEZE, ON DEV ONLY, the best-of-16 prompt and the best coherence-
679.     gated α (prereg §4 step 2). No TEST item is touched here (no leakage).
680. 
681.     * best prompt = the strong prompt with the highest DEV prompt-channel outcome.
682.     * baseline degeneracy = unsteered (α=0) neutral-prompt mean degeneracy on DEV.
683.     * α selection = among grid α whose DEV steer-only mean degeneracy ≤ 1.5× the
684.       baseline (coherence gate), pick the one with the highest DEV steer outcome.
685.     """
686.     # --- best-of-16 prompt (DEV prompt channel, unsteered) ---
687.     best_pid, best_ptext, best_pout = None, None, -np.inf
688.     n_prompts = len(spec.strong_prompts)
689.     for pi, (pid, ptext) in enumerate(spec.strong_prompts):
690.         outs, _, _ = _channel_item_outcomes(
691.             sampler, spec.axis, dev_items, ptext, 0.0, k, spec.direction, spec.layer,
692.             ctx=ctx, phase=PHASE_DEV_PROMPT, cell_key=f"prompt={pid}|alpha=0",
693.             cell_idx=pi + 1, cell_total=n_prompts)
694.         val = float(outs.mean())
695.         if val > best_pout:
696.             best_pid, best_ptext, best_pout = pid, ptext, val
697. 
698.     # --- unsteered baseline degeneracy (neutral prompt, α=0) on DEV ---
699.     _, base_deg, _ = _channel_item_outcomes(
700.         sampler, spec.axis, dev_items, spec.neutral_prompt, 0.0, k, spec.direction,
701.         spec.layer, ctx=ctx, phase=PHASE_DEV_BASELINE, cell_key="alpha=0",
702.         cell_idx=1, cell_total=1)
703.     baseline_degeneracy = float(base_deg.mean())
704.     gate_ceiling = coherence_max_ratio * baseline_degeneracy + COHERENCE_EPS_FLOOR
705. 
706.     # --- α grid on DEV steer-only (neutral prompt, coherence-gated) ---
707.     grid_rows: List[Dict[str, object]] = []
708.     frozen_alpha: Optional[float] = None
709.     best_steer_out: Optional[float] = None
710.     n_alpha = len(alpha_grid)
711.     for ai, a in enumerate(alpha_grid):
712.         outs, degs, _ = _channel_item_outcomes(
713.             sampler, spec.axis, dev_items, spec.neutral_prompt, float(a), k,
714.             spec.direction, spec.layer, ctx=ctx, phase=PHASE_DEV_ALPHA,
715.             cell_key=f"alpha={float(a)}", cell_idx=ai + 1, cell_total=n_alpha)
716.         steer_out = float(outs.mean())
717.         steer_deg = float(degs.mean())
718.         coherence_ok = steer_deg <= gate_ceiling + 1e-12
719.         grid_rows.append({
720.             "alpha": float(a), "dev_steer_outcome": steer_out,
721.             "degeneracy": steer_deg, "coherence_ok": coherence_ok,
722.         })
723.         if coherence_ok and (best_steer_out is None or steer_out > best_steer_out):
724.             best_steer_out = steer_out
725.             frozen_alpha = float(a)
726. 
727.     return DevSelection(
728.         best_prompt_id=str(best_pid), best_prompt_text=str(best_ptext),
729.         dev_prompt_outcome=float(best_pout), frozen_alpha=frozen_alpha,
730.         dev_steer_outcome=best_steer_out, baseline_degeneracy=baseline_degeneracy,
731.         alpha_grid=grid_rows, any_alpha_passes_gate=frozen_alpha is not None,
732.     )
733. 
734. 
735. @dataclass
736. class AxisAdjResult:
737.     axis: str
738.     layer: int
739.     n_dev: int
740.     n_test: int
741.     k: int
742.     dev_selection: Dict[str, object]
743.     # TEST (frozen prompt + frozen α)
744.     per_item_prompt: List[float]
745.     per_item_steer: List[float]
746.     per_item_diff: List[float]
747.     mean_diff: float
748.     ci_lo: float
749.     ci_hi: float
750.     ci_level: float
751.     bootstrap_b: int
752.     coherence_ok: bool
753.     test_steer_degeneracy: float
754.     test_baseline_degeneracy: float
755.     delta: float
756.     passed: bool
757.     # SECONDARY / descriptive
758.     conflict: Dict[str, object]
759.     descriptive: Dict[str, object]
760. 
761.     def to_row(self) -> Dict[str, object]:
762.         return asdict(self)
763. 
764. 
765. def adjudicate_axis(
766.     sampler: OutcomeSampler, spec: AxisAdjSpec, *,
767.     k: int = K_SAMPLES, alpha_grid: Sequence[float] = ALPHA_GRID,
768.     bootstrap_b: int = BOOTSTRAP_B, ci_level: float = BONFERRONI_CI_LEVEL,
769.     delta: float = DELTA, coherence_max_ratio: float = COHERENCE_MAX_RATIO,
770.     dev_fraction: float = DEV_FRACTION, seed: int = 0,
771.     ctx: Optional[RunContext] = None,
772. ) -> AxisAdjResult:
773.     """Full FROZEN adjudication for ONE axis (prereg §4 steps 1-7).
774. 
775.     1. DEV/TEST split (disjoint, fixed seed).
776.     2. DEV: freeze best-of-16 prompt + best coherence-gated α.
777.     3. TEST: per item, prompt_i (frozen prompt, α=0) & steer_i (frozen α),
778.        paired diff d_i = steer_i − prompt_i (k-sample means).
779.     4. Paired ITEM-cluster bootstrap CI of mean(d) at the Bonferroni level.
780.     5. Coherence gate on the winning steer cell (TEST).
781.     6. Axis pass iff CI excludes 0 AND mean(d) ≥ δ AND coherence ok.
782.     7. Conflict cell computed as SECONDARY/descriptive only.
783.     """
784.     ids = [str(it["id"]) for it in spec.items]
785.     by_id = {str(it["id"]): it for it in spec.items}
786.     split = split_dev_test(ids, dev_fraction=dev_fraction, seed=seed)
787.     dev_items = [by_id[i] for i in split.dev_ids]
788.     test_items = [by_id[i] for i in split.test_ids]
789. 
790.     dev_sel = select_on_dev(sampler, spec, dev_items, k=k, alpha_grid=alpha_grid,
791.                             coherence_max_ratio=coherence_max_ratio, ctx=ctx)
792. 
793.     frozen_alpha = dev_sel.frozen_alpha
794.     prompt_cell = f"prompt={dev_sel.best_prompt_id}|alpha=0"
795.     # If NO α cleared the DEV coherence gate, the axis has no valid steer cell:
796.     # it cannot pass (§4 iii). Report an honest non-pass with an empty steer cell.
797.     if frozen_alpha is None:
798.         n_test = len(test_items)
799.         prompt_out, _, _ = _channel_item_outcomes(
800.             sampler, spec.axis, test_items, dev_sel.best_prompt_text, 0.0, k,
801.             spec.direction, spec.layer, ctx=ctx, phase=PHASE_TEST_PROMPT,
802.             cell_key=prompt_cell)
803.         return AxisAdjResult(
804.             axis=spec.axis, layer=int(spec.layer), n_dev=len(dev_items), n_test=n_test,
805.             k=int(k), dev_selection=asdict(dev_sel),
806.             per_item_prompt=[float(x) for x in prompt_out],
807.             per_item_steer=[], per_item_diff=[],
808.             mean_diff=float("nan"), ci_lo=float("nan"), ci_hi=float("nan"),
809.             ci_level=ci_level, bootstrap_b=int(bootstrap_b), coherence_ok=False,
810.             test_steer_degeneracy=float("nan"),
811.             test_baseline_degeneracy=dev_sel.baseline_degeneracy,
812.             delta=delta, passed=False,
813.             conflict={"note": "no coherence-gated α; conflict not computed"},
814.             descriptive={"reason": "no α cleared the DEV coherence gate"},
815.         )
816. 
817.     # --- TEST: prompt channel (frozen prompt, α=0) & steer channel (frozen α) ---
818.     prompt_out, _, prompt_mat = _channel_item_outcomes(
819.         sampler, spec.axis, test_items, dev_sel.best_prompt_text, 0.0, k,
820.         spec.direction, spec.layer, ctx=ctx, phase=PHASE_TEST_PROMPT,
821.         cell_key=prompt_cell)
822.     steer_out, steer_deg, steer_mat = _channel_item_outcomes(
823.         sampler, spec.axis, test_items, spec.neutral_prompt, frozen_alpha, k,
824.         spec.direction, spec.layer, ctx=ctx, phase=PHASE_TEST_STEER,
825.         cell_key=f"alpha={float(frozen_alpha)}")
826.     _, base_deg_test, _ = _channel_item_outcomes(
827.         sampler, spec.axis, test_items, spec.neutral_prompt, 0.0, k,
828.         spec.direction, spec.layer, ctx=ctx, phase=PHASE_TEST_BASELINE,
829.         cell_key="alpha=0")
830. 
831.     per_item_diff = steer_out - prompt_out
832.     ci = cluster_bootstrap_ci(per_item_diff, b=bootstrap_b, ci_level=ci_level,
833.                               seed=seed, cluster=True)
834. 
835.     test_baseline_deg = float(base_deg_test.mean())
836.     test_steer_deg = float(steer_deg.mean())
837.     coherence_ok = (test_steer_deg
838.                     <= coherence_max_ratio * test_baseline_deg + COHERENCE_EPS_FLOOR + 1e-12)
839. 
840.     passed = axis_pass(ci.point, ci.ci_lo, ci.ci_hi, coherence_ok, delta=delta)
841. 
842.     conflict = _conflict_cell(sampler, spec, test_items, dev_sel.best_prompt_id,
843.                               dev_sel.best_prompt_text, frozen_alpha, k, ctx=ctx)
844.     descriptive = _descriptive(spec.axis, test_items, prompt_mat, steer_mat)
845. 
846.     return AxisAdjResult(
847.         axis=spec.axis, layer=int(spec.layer), n_dev=len(dev_items),
848.         n_test=len(test_items), k=int(k), dev_selection=asdict(dev_sel),
849.         per_item_prompt=[float(x) for x in prompt_out],
850.         per_item_steer=[float(x) for x in steer_out],
851.         per_item_diff=[float(x) for x in per_item_diff],
852.         mean_diff=ci.point, ci_lo=ci.ci_lo, ci_hi=ci.ci_hi, ci_level=ci.ci_level,
853.         bootstrap_b=int(bootstrap_b), coherence_ok=coherence_ok,
854.         test_steer_degeneracy=test_steer_deg,
855.         test_baseline_degeneracy=test_baseline_deg,
856.         delta=delta, passed=passed, conflict=conflict, descriptive=descriptive,
857.     )
858. 
859. 
860. def _conflict_cell(sampler: OutcomeSampler, spec: AxisAdjSpec, test_items: Sequence[Dict],
861.                    best_prompt_id: str, best_prompt_text: str, frozen_alpha: float,
862.                    k: int, ctx: Optional[RunContext] = None) -> Dict[str, object]:
863.     """SECONDARY/descriptive only (§4): best pro-axis prompt UP vs latent steer the
864.     OPPOSITE way (−α). Reports which channel the behavior lands nearer. NOT part of
865.     the pass/fail verdict."""
866.     conf_out, _, _ = _channel_item_outcomes(
867.         sampler, spec.axis, test_items, best_prompt_text, -float(frozen_alpha), k,
868.         spec.direction, spec.layer, ctx=ctx, phase=PHASE_CONFLICT,
869.         cell_key=f"prompt={best_prompt_id}|alpha={-float(frozen_alpha)}")
870.     prompt_pole, _, _ = _channel_item_outcomes(
871.         sampler, spec.axis, test_items, best_prompt_text, 0.0, k,
872.         spec.direction, spec.layer, ctx=ctx, phase=PHASE_CONFLICT_POLE,
873.         cell_key=f"prompt={best_prompt_id}|alpha=0")
874.     return {
875.         "note": "SECONDARY/descriptive only — NOT part of the verdict (prereg §4).",
876.         "alpha_opposite": -float(frozen_alpha),
877.         "mean_conflict_outcome": float(conf_out.mean()),
878.         "mean_prompt_pole_outcome": float(prompt_pole.mean()),
879.         "latent_drags_down": float(conf_out.mean()) < float(prompt_pole.mean()),
880.     }
881. 
882. 
883. def _descriptive(axis: str, test_items: Sequence[Dict],
884.                  prompt_mat: np.ndarray, steer_mat: np.ndarray) -> Dict[str, object]:
885.     """Descriptive extras (e.g. binned set ECE for uncertainty) reported alongside
886.     the frozen per-item outcome — never used in the verdict."""
887.     d: Dict[str, object] = {}
888.     if axis in CALIBRATION_OUTCOME_AXES:
889.         d["set_ece_note"] = (
890.             "Per-item outcome is the PROPER 1 - Brier = 1 - (conf - correct)**2 "
891.             "(decision D-0025; delta on this scale); the binned set ECE is "
892.             "DESCRIPTIVE only and is NOT part of the gate."
893.         )
894.     return d
895. 
896. 
897. # --------------------------------------------------------------------------- #
898. # Whole-adjudication driver (all axes -> three-tier verdict)
899. # --------------------------------------------------------------------------- #
900. @dataclass
901. class AdjudicationReport:
902.     axis_results: List[AxisAdjResult]
903.     axis_passes: Dict[str, bool]
904.     verdict: str
905.     frozen_params: Dict[str, object]
906. 
907.     def to_dict(self) -> Dict[str, object]:
908.         return {
909.             "verdict": self.verdict,
910.             "axis_passes": self.axis_passes,
911.             "frozen_params": self.frozen_params,
912.             "axes": [r.to_row() for r in self.axis_results],
913.         }
914. 
915. 
916. def frozen_params_dict() -> Dict[str, object]:
917.     return {
918.         "alpha_grid": list(ALPHA_GRID),
919.         "delta": DELTA,
920.         "k_samples": K_SAMPLES,
921.         "n_items_by_axis": dict(N_ITEMS_BY_AXIS),
922.         "coherence_max_ratio": COHERENCE_MAX_RATIO,
923.         "coherence_eps_floor": COHERENCE_EPS_FLOOR,
924.         "bootstrap_b": BOOTSTRAP_B,
925.         "familywise_alpha": FAMILYWISE_ALPHA,
926.         "n_axes": N_AXES,
927.         "bonferroni_ci_level": BONFERRONI_CI_LEVEL,
928.         "dev_fraction": DEV_FRACTION,
929.         "bootstrap": "paired item-cluster (resample items, each carries its k)",
930.         "decision": "CI excludes 0 AND mean(d) >= delta AND coherence gate pass",
931.         "verdict_rule": ">=2 pass STRONG_GO; ==1 CONDITIONAL_GO; 0 KILL_PLAN_D",
932.         "prereg": "docs/ledgers/prereg-c2b-adjudication.md (FROZEN 2026-07-23)",
933.     }
934. 
935. 
936. def adjudicate(
937.     sampler_for_axis: Callable[[str], OutcomeSampler],
938.     specs: Sequence[AxisAdjSpec], *,
939.     k: int = K_SAMPLES, alpha_grid: Sequence[float] = ALPHA_GRID,
940.     bootstrap_b: int = BOOTSTRAP_B, ci_level: float = BONFERRONI_CI_LEVEL,
941.     delta: float = DELTA, coherence_max_ratio: float = COHERENCE_MAX_RATIO,
942.     dev_fraction: float = DEV_FRACTION, seed: int = 0,
943.     ctx: Optional[RunContext] = None,
944. ) -> AdjudicationReport:
945.     """Run the FROZEN adjudication over all axis specs and emit the three-tier
946.     verdict (§4). ``sampler_for_axis`` returns the OutcomeSampler for an axis (one
947.     shared real backend, or a per-axis synthetic backend in tests). ``ctx`` is the
948.     optional run-mechanics carrier (progress + checkpoint); ``None`` => unchanged
949.     offline behaviour."""
950.     results: List[AxisAdjResult] = []
951.     passes: Dict[str, bool] = {}
952.     for spec in specs:
953.         sampler = sampler_for_axis(spec.axis)
954.         res = adjudicate_axis(
955.             sampler, spec, k=k, alpha_grid=alpha_grid, bootstrap_b=bootstrap_b,
956.             ci_level=ci_level, delta=delta, coherence_max_ratio=coherence_max_ratio,
957.             dev_fraction=dev_fraction, seed=seed, ctx=ctx)
958.         results.append(res)
959.         passes[spec.axis] = res.passed
960.     verdict = three_tier_verdict(passes)
961.     return AdjudicationReport(axis_results=results, axis_passes=passes,
962.                               verdict=verdict, frozen_params=frozen_params_dict())
963.
```

</details>


---

<sub>1m 16s</sub>

### `view`

**view the file at C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py.**

C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py (lines 120-240)

<details>
<summary>121 lines</summary>

```
120. def _looks_like_cuda_error(exc: BaseException) -> bool:
121.     """Only call an error 'likely CUDA/driver' if its text actually looks like one
122.     (MINOR-1): a plain RuntimeError from unrelated code would otherwise be
123.     mislabeled as a GPU fault, misdirecting triage."""
124.     msg = f"{type(exc).__name__}: {exc}".lower()
125.     return any(tok in msg for tok in _CUDA_TOKENS)
126. 
127. 
128. def watchdog_should_abort(last_activity_ts: float, stall_timeout: float,
129.                           now: Optional[float] = None) -> bool:
130.     """Pure, testable stall decision: True iff more than ``stall_timeout`` seconds
131.     have elapsed since ``last_activity_ts``. ``stall_timeout <= 0`` disables the
132.     watchdog (never aborts). The runner (never the test) turns True into os._exit.
133. 
134.     This targets the D-0029 failure mode: a SILENT 100%-CPU spin after a host
135.     driver reload that raises NO exception, so ``except (RuntimeError, MemoryError)``
136.     never fires and the process holds a borrowed GPU forever."""
137.     if stall_timeout is None or float(stall_timeout) <= 0:
138.         return False
139.     ref = time.time() if now is None else float(now)
140.     return (ref - float(last_activity_ts)) > float(stall_timeout)
141. 
142. 
143. class InactivityWatchdog:
144.     """Background daemon thread that hard-exits the process if no generation cell
145.     has completed for longer than ``stall_timeout`` seconds. Off when timeout<=0.
146. 
147.     The abort action is injected (``on_abort``) so tests can assert firing without
148.     actually calling ``os._exit``; the runner uses the default hard-exit."""
149. 
150.     def __init__(self, progress, stall_timeout: float,
151.                  check_interval: Optional[float] = None, on_abort=None):
152.         self.progress = progress
153.         self.stall_timeout = float(stall_timeout)
154.         if check_interval is not None:
155.             self.check_interval = float(check_interval)
156.         else:
157.             self.check_interval = min(30.0, max(1.0, self.stall_timeout / 10.0))
158.         self._on_abort = on_abort if on_abort is not None else self._default_abort
159.         self._thread = None
160.         self._stop = threading.Event()
161. 
162.     def start(self) -> "InactivityWatchdog":
163.         if self.stall_timeout <= 0:
164.             return self  # disabled
165.         self._thread = threading.Thread(
166.             target=self._run, name="c2b-stall-watchdog", daemon=True)
167.         self._thread.start()
168.         return self
169. 
170.     def stop(self) -> None:
171.         self._stop.set()
172. 
173.     def _run(self) -> None:
174.         while not self._stop.wait(self.check_interval):
175.             last = getattr(self.progress, "last_activity", None)
176.             if last is None:
177.                 continue
178.             if watchdog_should_abort(last, self.stall_timeout):
179.                 idle = time.time() - float(last)
180.                 self._on_abort(self.stall_timeout, idle)
181.                 return
182. 
183.     @staticmethod
184.     def _default_abort(stall_timeout: float, idle: float) -> None:
185.         msg = (f"\n[c2b-adj] FATAL STALL: no generation cell completed for "
186.                f"{idle:.0f}s (> --stall-timeout {stall_timeout:.0f}s). This is the "
187.                f"D-0029 silent-hang mode (100% CPU spin, NO exception raised, e.g. "
188.                f"after a host driver reload). Hard-exiting non-zero so the process "
189.                f"does NOT spin forever holding a borrowed GPU. Partial results are "
190.                f"CHECKPOINTED per-cell; re-run the SAME command (no --fresh) to "
191.                f"RESUME.\n")
192.         sys.stderr.write(msg)
193.         sys.stderr.flush()
194.         sys.stdout.flush()
195.         os._exit(3)
196. 
197. 
198. # --------------------------------------------------------------------------- #
199. # Spec construction
200. # --------------------------------------------------------------------------- #
201. def load_axis_items(axis: str, use_fixture: bool, n_items: Optional[int]) -> List[Dict]:
202.     """Load items for one axis with frozen per-axis caps by default.
203. 
204.     If ``n_items`` is provided, it explicitly overrides the cap. Otherwise we use
205.     the frozen preregistered per-axis default from ``adj.N_ITEMS_BY_AXIS`` when
206.     available. Unknown axes keep the legacy uncapped behavior.
207.     """
208.     task = c2b_tasks.load_c2b_task(axis, use_fixture=use_fixture)
209.     items = list(task.items)
210.     cap = n_items if n_items is not None else adj.N_ITEMS_BY_AXIS.get(axis)
211.     if cap is not None:
212.         items = items[:cap]
213.     return items
214. 
215. 
216. def build_strong_prompts(axis: str, n_strong: int) -> List:
217.     strong = c1.load_strongest_prompts(axis)
218.     return list(zip(strong.ids, strong.texts))[:n_strong]
219. 
220. 
221. def build_specs_synthetic(axes: List[str], use_fixture: bool,
222.                           n_items: Optional[int], n_strong: int) -> List[AxisAdjSpec]:
223.     """Offline specs — direction/layer are placeholders the synthetic backend ignores."""
224.     specs = []
225.     neutral = c1.load_neutral_prompts()[0]
226.     for axis in axes:
227.         items = load_axis_items(axis, use_fixture, n_items)
228.         specs.append(AxisAdjSpec(
229.             axis=axis, items=items, strong_prompts=build_strong_prompts(axis, n_strong),
230.             neutral_prompt=neutral, direction=np.ones(8), layer=3,
231.         ))
232.     return specs
233. 
234. 
235. def build_specs_hf(axes: List[str], model: str, use_fixture: bool,
236.                    n_items: Optional[int], n_strong: int, n_extraction: int,
237.                    seed: int, out_dir: Path) -> (List[AxisAdjSpec], Dict):  # noqa
238.     """Real specs: RE-DERIVE the C1 chosen non-degenerate layer + CAA unit direction
239.     per axis on THIS model (prereg §2; never hardcoded). Reuses run_c1_facade +
240.     run_gpu_phase0._extract_direction."""
```

</details>


---

<sub>1m 16s</sub>

### `view`

**view the file at C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py.**

C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\scripts\run_c2b_adjudication.py (lines 412-575)

<details>
<summary>164 lines</summary>

```
412.     ap = argparse.ArgumentParser(description="C2b QUALIFIED adjudication (FROZEN prereg §4/§5)")
413.     ap.add_argument("--backend", choices=["synthetic", "hf"], default="synthetic",
414.                     help="synthetic = offline no-torch pipeline smoke; hf = real model")
415.     ap.add_argument("--model", default=None,
416.                     help="HF model id (default: 7B for hf; ignored for synthetic)")
417.     ap.add_argument("--axes", nargs="*", default=ADJ_AXES)
418.     ap.add_argument("--use-fixture", action="store_true",
419.                     help="use the bundled OFFLINE task fixtures (default for synthetic; "
420.                          "also the CPU/1.5B smoke). Omit on the A800 for the real loaders.")
421.     ap.add_argument("--n-items", type=int, default=None,
422.                     help="cap items/axis (default: frozen per-axis N; explicit value overrides)")
423.     ap.add_argument("--n-strong", type=int, default=DEFAULT_N_STRONG)
424.     ap.add_argument("--n-extraction", type=int, default=28)
425.     ap.add_argument("--bootstrap-b", type=int, default=adj.BOOTSTRAP_B)
426.     ap.add_argument("--allow-underpowered", action="store_true",
427.                     help="permit --bootstrap-b < frozen 10000 (prereg §5). OFF by "
428.                          "default: the confirmatory run HARD-FAILS if underpowered.")
429.     ap.add_argument("--max-new-tokens", type=int, default=64,
430.                     help="max new tokens per generation (default 64: these tasks "
431.                          "have SHORT answers — a number / MC letter / short answer "
432.                          "+ confidence; the prior 256 was overkill, D-0029). Tunable.")
433.     ap.add_argument("--batch-size", type=int, default=16,
434.                     help="padded GPU batch size for generation (hf backend). Cuts "
435.                          "wall-clock several-fold vs one-sequence-at-a-time (FIX 3). "
436.                          "The chunk = batch_size//k items generated in one batch.")
437.     ap.add_argument("--fresh", action="store_true",
438.                     help="ignore/clear any existing checkpoints and start over "
439.                          "(default: RESUME from out_dir/checkpoints if config matches).")
440.     ap.add_argument("--temperature", type=float, default=0.7)
441.     ap.add_argument("--seed", type=int, default=20260723)
442.     ap.add_argument("--stall-timeout", type=float, default=600.0,
443.                     help="inactivity watchdog (MINOR-1): hard-exit non-zero if no "
444.                          "generation cell completes for this many seconds, to break "
445.                          "the D-0029 SILENT 100%%-CPU spin (no exception raised). "
446.                          "0 = disabled.")
447.     ap.add_argument("--disk-budget-gb", type=float, default=60.0)
448.     ap.add_argument("--disk-ceiling-gb", type=float, default=70.0)
449.     ap.add_argument("--hf-home", default=None)
450.     ap.add_argument("--venv", default=None)
451.     ap.add_argument("--out-dir", default=None)
452.     return ap
453. 
454. 
455. def main(argv: Optional[List[str]] = None) -> int:
456.     ap = build_parser()
457.     args = ap.parse_args(argv)
458.     axes = list(args.axes)
459. 
460.     if args.bootstrap_b < 10000:
461.         if not args.allow_underpowered:
462.             raise SystemExit(
463.                 f"[c2b-adj] FATAL: --bootstrap-b {args.bootstrap_b} < frozen 10000 "
464.                 f"(prereg §5). The confirmatory run requires B>=10000. Pass "
465.                 f"--allow-underpowered to override for a smoke/debug run only.")
466.         print(f"[c2b-adj] WARNING: --bootstrap-b {args.bootstrap_b} < frozen 10000 "
467.               f"(prereg §5) but --allow-underpowered was passed; NOT valid for the "
468.               f"confirmatory adjudication.", flush=True)
469. 
470.     out_dir = Path(args.out_dir) if args.out_dir else (
471.         _REPO / "results" / f"c2b_adjudication_{args.backend}_{date.today().isoformat()}")
472.     out_dir = out_dir.resolve()
473.     out_dir.mkdir(parents=True, exist_ok=True)
474. 
475.     t_start = time.time()
476.     started_at = utcnow()
477. 
478.     if args.backend == "synthetic":
479.         use_fixture = True  # synthetic backend only makes sense on the offline fixtures
480.         specs = build_specs_synthetic(axes, use_fixture, args.n_items, args.n_strong)
481.         sampler_for_axis = synthetic_sampler_factory(use_fixture, args.n_items)
482.         model = "synthetic-offline"
483.         hardware = "cpu-offline"
484.         meta_extra: Dict = {"backend": "synthetic",
485.                             "note": "offline no-torch pipeline smoke on fixtures"}
486.     else:
487.         model = args.model or DEFAULT_MODEL
488.         guard_paths = default_guard_paths(args.hf_home, args.venv)
489.         usage0 = check_disk_budget(guard_paths, args.disk_budget_gb, args.disk_ceiling_gb)
490.         print(f"[c2b-adj] disk pre-run: {usage0.message}", flush=True)
491.         specs, hf_meta = build_specs_hf(
492.             axes, model, args.use_fixture, args.n_items, args.n_strong,
493.             args.n_extraction, args.seed, out_dir)
494.         # abort before spending on generation if the model download blew the budget
495.         usage_mid = check_disk_budget(guard_paths, args.disk_budget_gb,
496.                                       args.disk_ceiling_gb, raise_on_over=True)
497.         print(f"[c2b-adj] disk post-C1 (model loaded): {usage_mid.message}", flush=True)
498.         sampler_for_axis = hf_sampler_factory(model, args.max_new_tokens,
499.                                               args.temperature, args.seed,
500.                                               args.batch_size)
501.         hardware = f"{p0._pick_device()}-{p0._pick_dtype()}"
502.         meta_extra = {"backend": "hf", **hf_meta}
503. 
504.     # --- FIX 4: up-front PLANNED generation count + rough wall-clock budget so
505.     # the run's size is visible BEFORE committing GPU time (sanity-check knob). ---
506.     per_axis_plan, total_plan = plan_generation_counts(
507.         specs, k=adj.K_SAMPLES, alpha_grid=adj.ALPHA_GRID,
508.         dev_fraction=adj.DEV_FRACTION)
509.     plan_str = ", ".join(f"{a}={c}" for a, c in per_axis_plan.items())
510.     print(f"[c2b-adj] PLANNED generations (upper bound): {plan_str}  "
511.           f"TOTAL={total_plan}", flush=True)
512.     n_batches = -(-total_plan // max(1, args.batch_size))  # ceil
513.     lo_h = n_batches * 2.0 / 3600.0
514.     hi_h = n_batches * 4.0 / 3600.0
515.     print(f"[c2b-adj] budget: batch_size={args.batch_size} "
516.           f"max_new_tokens={args.max_new_tokens} -> ~{n_batches} batches; "
517.           f"rough wall-clock ~{lo_h:.2f}-{hi_h:.2f}h "
518.           f"(assuming ~2-4 s/batch on the target GPU; SANITY-CHECK before "
519.           f"committing GPU time).", flush=True)
520. 
521.     # --- FIX 1/2: progress tracker + resumable checkpoint store ---
522.     fingerprint = _config_fingerprint(args, model, specs)
523.     ckpt_dir = out_dir / "checkpoints"
524.     checkpoint = CheckpointStore(ckpt_dir, fingerprint, seed=args.seed,
525.                                  fresh=args.fresh)
526.     progress = ProgressTracker(total_planned=total_plan)
527.     run_ctx = RunContext(checkpoint=checkpoint, progress=progress)
528.     print(f"[c2b-adj] checkpoints: {_rel(ckpt_dir)}  "
529.           f"(fresh={args.fresh}; resume auto-skips cells whose config matches)",
530.           flush=True)
531. 
532.     # --- FIX 5 + MINOR-1: a CUDA/driver error (e.g. driver reload) must NOT spin
533.     # forever; checkpoints are flushed per-cell, so we log clearly and EXIT
534.     # non-zero. A background inactivity watchdog also breaks the D-0029 SILENT
535.     # hang (100% CPU spin, NO exception) that the except below cannot catch. ---
536.     watchdog = InactivityWatchdog(progress, args.stall_timeout).start()
537.     try:
538.         report = adj.adjudicate(
539.             sampler_for_axis, specs, k=adj.K_SAMPLES, alpha_grid=adj.ALPHA_GRID,
540.             bootstrap_b=args.bootstrap_b, ci_level=adj.BONFERRONI_CI_LEVEL,
541.             delta=adj.DELTA, coherence_max_ratio=adj.COHERENCE_MAX_RATIO,
542.             dev_fraction=adj.DEV_FRACTION, seed=args.seed, ctx=run_ctx)
543.     except (RuntimeError, MemoryError) as exc:
544.         checkpoint.close()
545.         label = ("likely CUDA/driver" if _looks_like_cuda_error(exc)
546.                  else "generic error")
547.         print(f"\n[c2b-adj] FATAL generation error ({label}): "
548.               f"{type(exc).__name__}: {exc}", flush=True)
549.         print(f"[c2b-adj] partial results are CHECKPOINTED at {_rel(ckpt_dir)} — "
550.               f"re-run the SAME command (without --fresh) to RESUME.", flush=True)
551.         return 2
552.     finally:
553.         watchdog.stop()
554.         checkpoint.close()
555. 
556.     wall = time.time() - t_start
557.     meta = {
558.         "model": model, "hardware": hardware, "run_type": "exploratory",
559.         "valid_for_paper": False, "protocol_frozen": True,
560.         "prereg": "docs/ledgers/prereg-c2b-adjudication.md (FROZEN 2026-07-23)",
561.         "started_at": started_at, "generated_at": utcnow(),
562.         "wall_clock_seconds": round(wall, 2), "platform": platform.platform(),
563.         "use_fixture": bool(args.use_fixture) or args.backend == "synthetic",
564.         **meta_extra,
565.     }
566.     json_path = write_results(report, out_dir, meta)
567.     exp_id = register(report, out_dir, json_path, meta, args.seed)
568. 
569.     if args.backend == "hf":
570.         guard_paths = default_guard_paths(args.hf_home, args.venv)
571.         usage1 = check_disk_budget(guard_paths, args.disk_budget_gb,
572.                                    args.disk_ceiling_gb, raise_on_over=False)
573.         print(f"[c2b-adj] disk post-run: {usage1.message}", flush=True)
574. 
575.     print(f"\n[c2b-adj] VERDICT: {report.verdict}  "
```

</details>


---

<sub>1m 17s</sub>

### `powershell`

**Independent recomputation from JSON structure**

<details>
<summary>Arguments</summary>

```json
{
  "description": "Independent recomputation from JSON structure",
  "command": "Set-Location 'C:\\Users\\v-elzhang\\Desktop\\MyFolder\\cognitive console'; @'\nimport json, math\nfrom pathlib import Path\np=Path('results/c2b_adjudication_hf_2026-07-24/c2b_adjudication_results.json')\no=json.loads(p.read_text(encoding='utf-8'))\naxes=o['axes']\nfp=o['frozen_params']\ndelta=fp['delta']\nci_level=fp['bonferroni_ci_level']\nprint('ci_level',ci_level,'expected',1-0.05/3,'delta',delta)\nrecalc={}\nfor a in axes:\n    nm=a['axis']; lo=a['ci_lo']; hi=a['ci_hi']; md=a['mean_diff']; coh=a['coherence_ok']\n    ci_excl = not (lo<=0<=hi)\n    passed = ci_excl and (md>=delta) and coh\n    recalc[nm]=passed\n    # consistency of per-item arrays\n    pp=a['per_item_prompt']; ps=a['per_item_steer']; pd=a['per_item_diff']\n    assert len(pp)==len(ps)==len(pd)==a['n_test']\n    maxerr=max(abs((s-p)-d) for s,p,d in zip(ps,pp,pd))\n    meand=sum(pd)/len(pd)\n    print(nm,'pass_reported',a['passed'],'pass_recalc',passed,'ci_excl',ci_excl,'mean>=delta',md>=delta,'coh',coh,'max_pair_err',maxerr,'mean_from_diff',meand)\n    # distribution checks\n    def stat(arr):\n        uniq=len({round(float(x),6) for x in arr})\n        return (len(arr), min(arr), max(arr), sum(arr)/len(arr), uniq, all(0<=x<=1 for x in arr), all(x==0 for x in arr), all(x==1 for x in arr))\n    print('  prompt_stats',stat(pp))\n    print('  steer_stats ',stat(ps))\n    # degeneracy gate at test\n    ratio = a['test_steer_degeneracy'] / max(a['test_baseline_degeneracy'],1e-12)\n    print('  test_deg_ratio',ratio,'gate<=',fp['coherence_max_ratio'],'+eps floor logic in code')\n    dev=a['dev_selection']\n    base=dev['baseline_degeneracy']; eps=fp['coherence_eps_floor']; gate=fp['coherence_max_ratio']*base+eps\n    print('  dev_base_deg',base,'gate_ceiling',gate,'frozen_alpha',dev['frozen_alpha'])\n    for row in dev['alpha_grid']:\n        print('    alpha',row['alpha'],'coh',row['coherence_ok'],'deg',row['degeneracy'],'<=gate',row['degeneracy']<=gate,'dev_out',row['dev_steer_outcome'])\n\nnpass=sum(1 for v in recalc.values() if v)\nver='STRONG_GO' if npass>=2 else ('CONDITIONAL_GO' if npass==1 else 'KILL_PLAN_D')\nprint('recalc_axis_passes',recalc)\nprint('reported_axis_passes',o['axis_passes'])\nprint('recalc_verdict',ver,'reported',o['verdict'])\n\n# c1 check from run log lines already but validate stable_layer_found true for all axes\nprint('c1_layer_info',o.get('c1_layer_info'))\n'@ | python -"
}
```

</details>

<details>
<summary>42 lines</summary>

```
ci_level 0.9833333333333333 expected 0.9833333333333333 delta 0.05
deliberation pass_reported False pass_recalc False ci_excl False mean>=delta False coh True max_pair_err 0.0 mean_from_diff 0.015000000000000003
  prompt_stats (40, 0.0, 0.6, 0.02, 3, True, False, False)
  steer_stats  (40, 0.0, 0.6, 0.034999999999999996, 4, True, False, False)
  test_deg_ratio 0.9560304814209939 gate<= 1.5 +eps floor logic in code
  dev_base_deg 0.027361333359291244 gate_ceiling 0.06104200003893687 frozen_alpha 2.0
    alpha 2.0 coh True deg 0.030131742564638055 <=gate True dev_out 0.1
    alpha 4.0 coh True deg 0.033649947110964445 <=gate True dev_out 0.06999999999999999
    alpha 6.0 coh True deg 0.029512056256522312 <=gate True dev_out 0.06999999999999999
    alpha 8.0 coh True deg 0.03566521296564354 <=gate True dev_out 0.06
    alpha 12.0 coh True deg 0.036096827998987266 <=gate True dev_out 0.04
    alpha 16.0 coh True deg 0.034208495182016296 <=gate True dev_out 0.05
    alpha 24.0 coh True deg 0.03815809664695778 <=gate True dev_out 0.06
skepticism pass_reported False pass_recalc False ci_excl False mean>=delta False coh True max_pair_err 0.0 mean_from_diff -0.08
  prompt_stats (40, 0.0, 1.0, 0.775, 5, True, False, False)
  steer_stats  (40, 0.0, 1.0, 0.6950000000000001, 4, True, False, False)
  test_deg_ratio 0.881956177825956 gate<= 1.5 +eps floor logic in code
  dev_base_deg 0.0011819967266775777 gate_ceiling 0.021772995090016366 frozen_alpha 6.0
    alpha 2.0 coh True deg 0.0009973813420621944 <=gate True dev_out 0.45
    alpha 4.0 coh True deg 0.0006099166301009218 <=gate True dev_out 0.45
    alpha 6.0 coh True deg 0.0009855217558721607 <=gate True dev_out 0.45999999999999996
    alpha 8.0 coh True deg 0.0014531555962191967 <=gate True dev_out 0.45
    alpha 12.0 coh True deg 0.0010108510777825698 <=gate True dev_out 0.45
    alpha 16.0 coh True deg 0.0021061540918196507 <=gate True dev_out 0.45
    alpha 24.0 coh True deg 0.0018254114546373077 <=gate True dev_out 0.45
uncertainty_awareness pass_reported False pass_recalc False ci_excl True mean>=delta False coh True max_pair_err 0.0 mean_from_diff -0.22767283018867926
  prompt_stats (53, 0.62702, 1.0, 0.8478875471698113, 27, True, False, False)
  steer_stats  (53, 0.0, 1.0, 0.6202147169811321, 23, True, False, False)
  test_deg_ratio 1.0431697536721365 gate<= 1.5 +eps floor logic in code
  dev_base_deg 0.009584693074124987 gate_ceiling 0.03437703961118748 frozen_alpha 8.0
    alpha 2.0 coh True deg 0.0045380278238505945 <=gate True dev_out 0.5373703703703703
    alpha 4.0 coh True deg 0.004649663154766579 <=gate True dev_out 0.5370881481481482
    alpha 6.0 coh True deg 0.0031480217203036795 <=gate True dev_out 0.5324214814814815
    alpha 8.0 coh True deg 0.003061252573031836 <=gate True dev_out 0.5629629629629629
    alpha 12.0 coh True deg 0.004599265761640202 <=gate True dev_out 0.5085466666666666
    alpha 16.0 coh True deg 0.004421362358385246 <=gate True dev_out 0.5599585185185185
    alpha 24.0 coh True deg 0.00409204909204909 <=gate True dev_out 0.5453148148148148
recalc_axis_passes {'deliberation': False, 'skepticism': False, 'uncertainty_awareness': False}
reported_axis_passes {'deliberation': False, 'skepticism': False, 'uncertainty_awareness': False}
recalc_verdict KILL_PLAN_D reported KILL_PLAN_D
c1_layer_info {'deliberation': {'chosen_layer': 20, 'stable_layer_found': True}, 'skepticism': {'chosen_layer': 20, 'stable_layer_found': True}, 'uncertainty_awareness': {'chosen_layer': 20, 'stable_layer_found': True}}
<shellId: 3 completed with exit code 0>
```

</details>


---

<sub>1m 30s</sub>

### `powershell`

**Recompute bootstrap CIs and parse log progress rigorously**

<details>
<summary>Arguments</summary>

```json
{
  "description": "Recompute bootstrap CIs and parse log progress rigorously",
  "command": "Set-Location 'C:\\Users\\v-elzhang\\Desktop\\MyFolder\\cognitive console'; @'\nimport json, re\nimport numpy as np\nfrom pathlib import Path\njp=Path('results/c2b_adjudication_hf_2026-07-24/c2b_adjudication_results.json')\nlg=Path('results/c2b_adjudication_hf_2026-07-24/adj2.run.log')\no=json.loads(jp.read_text(encoding='utf-8'))\nseed=20260723\nB=o['frozen_params']['bootstrap_b']\nci_level=o['frozen_params']['bonferroni_ci_level']\nlo_pct=100*(1-ci_level)/2\nhi_pct=100*(1+ci_level)/2\nrng=np.random.default_rng(seed)\nprint('BOOT_PARAMS',B,ci_level,lo_pct,hi_pct)\nfor ax in o['axes']:\n    d=np.array(ax['per_item_diff'],dtype=float)\n    n=d.size\n    idx=rng.integers(0,n,size=(B,n))\n    boot=d[idx].mean(axis=1)\n    lo=float(np.percentile(boot,lo_pct)); hi=float(np.percentile(boot,hi_pct)); pt=float(d.mean())\n    print(ax['axis'],'reported',ax['mean_diff'],ax['ci_lo'],ax['ci_hi'],'recalc',pt,lo,hi,'exact_match',abs(pt-ax['mean_diff'])<1e-12 and abs(lo-ax['ci_lo'])<1e-12 and abs(hi-ax['ci_hi'])<1e-12)\n\ntext=lg.read_text(encoding='utf-8',errors='ignore')\nstart_lines=re.findall(r'\\[c2b-adj\\].* START done=\\d+/11365',text)\ndone_lines=re.findall(r'\\[c2b-adj\\].* DONE done=\\d+/11365',text)\ntracebacks=re.findall(r'Traceback|Exception|FATAL STALL|FATAL generation error',text)\nprint('LOG_START_LINES',len(start_lines))\nprint('LOG_DONE_LINES',len(done_lines))\nprint('LOG_FATAL_OR_EXC',tracebacks)\n# parse done counters monotonic and final\ncounters=[int(m.group(1)) for m in re.finditer(r'DONE done=(\\d+)/11365',text)]\nprint('DONE_COUNTERS_FIRST_LAST',counters[:3],counters[-3:])\nmono=all(counters[i]>=counters[i-1] for i in range(1,len(counters)))\nprint('DONE_MONOTONIC',mono,'FINAL',counters[-1] if counters else None)\nprint('HAS_EXIT0', 'ADJ2_EXIT_RC=0' in text)\nprint('HAS_VERDICT_LINE', '[c2b-adj] VERDICT: KILL_PLAN_D  (axes passing: 0/3)' in text)\nprint('HAS_WROTE_JSON', 'c2b_adjudication_results.json' in text)\n'@ | python -"
}
```

</details>

<details>
<summary>13 lines</summary>

```
BOOT_PARAMS 10000 0.9833333333333333 0.8333333333333359 99.16666666666667
deliberation reported 0.015000000000000003 -0.04 0.06999999999999999 recalc 0.015000000000000003 -0.04 0.06999999999999999 exact_match True
skepticism reported -0.08 -0.225 0.045 recalc -0.08 -0.225 0.05499999999999998 exact_match False
uncertainty_awareness reported -0.22767283018867926 -0.36977938679245265 -0.0916042641509434 recalc -0.22767283018867926 -0.3757639716981132 -0.0901602075471698 exact_match False
LOG_START_LINES 87
LOG_DONE_LINES 87
LOG_FATAL_OR_EXC []
DONE_COUNTERS_FIRST_LAST [100, 200, 300] [10835, 11100, 11365]
DONE_MONOTONIC True FINAL 11365
HAS_EXIT0 True
HAS_VERDICT_LINE True
HAS_WROTE_JSON True
<shellId: 4 completed with exit code 0>
```

</details>


---

<sub>1m 39s</sub>

### `powershell`

**Recompute axis CIs with per-axis seed reset**

<details>
<summary>Arguments</summary>

```json
{
  "description": "Recompute axis CIs with per-axis seed reset",
  "command": "Set-Location 'C:\\Users\\v-elzhang\\Desktop\\MyFolder\\cognitive console'; @'\nimport json\nimport numpy as np\nfrom pathlib import Path\no=json.loads(Path('results/c2b_adjudication_hf_2026-07-24/c2b_adjudication_results.json').read_text(encoding='utf-8'))\nseed=20260723\nB=o['frozen_params']['bootstrap_b']\nci_level=o['frozen_params']['bonferroni_ci_level']\nlo_pct=100*(1-ci_level)/2\nhi_pct=100*(1+ci_level)/2\nfor ax in o['axes']:\n    d=np.array(ax['per_item_diff'],dtype=float)\n    n=d.size\n    rng=np.random.default_rng(seed)\n    idx=rng.integers(0,n,size=(B,n))\n    boot=d[idx].mean(axis=1)\n    lo=float(np.percentile(boot,lo_pct)); hi=float(np.percentile(boot,hi_pct)); pt=float(d.mean())\n    print(ax['axis'],pt,lo,hi,'match',abs(lo-ax['ci_lo'])<1e-12 and abs(hi-ax['ci_hi'])<1e-12)\n'@ | python -"
}
```

</details>

```
deliberation 0.015000000000000003 -0.04 0.06999999999999999 match True
skepticism -0.08 -0.225 0.045 match True
uncertainty_awareness -0.22767283018867926 -0.36977938679245265 -0.0916042641509434 match True
<shellId: 5 completed with exit code 0>
```


---

<sub>1m 42s</sub>

### `view`

**view the file at C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\results\c2b_adjudication_hf_2026-07-24\c1.**

C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\results\c2b_adjudication_hf_2026-07-24\c1

```
activations
```


---

<sub>1m 43s</sub>

### `view`

**view the file at C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\results\c2b_adjudication_hf_2026-07-24\c1\activations.**

C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\results\c2b_adjudication_hf_2026-07-24\c1\activations

<details>
<summary>5 lines</summary>

```diff

diff --git a/C:/Users/v-elzhang/Desktop/MyFolder/cognitive console/results/c2b_adjudication_hf_2026-07-24/c1/activations b/C:/Users/v-elzhang/Desktop/MyFolder/cognitive console/results/c2b_adjudication_hf_2026-07-24/c1/activations
index 0000000..0000000 100644
--- a/C:/Users/v-elzhang/Desktop/MyFolder/cognitive console/results/c2b_adjudication_hf_2026-07-24/c1/activations
+++ b/C:/Users/v-elzhang/Desktop/MyFolder/cognitive console/results/c2b_adjudication_hf_2026-07-24/c1/activations
@@ -1,0 +1,0 @@
```

</details>


---

<sub>1m 48s</sub>

### `powershell`

**List c1 output files recursively**

<details>
<summary>Arguments</summary>

```json
{
  "description": "List c1 output files recursively",
  "command": "Set-Location 'C:\\Users\\v-elzhang\\Desktop\\MyFolder\\cognitive console'; Get-ChildItem 'results\\c2b_adjudication_hf_2026-07-24\\c1' -Recurse | Select-Object FullName,Length,Mode | Format-Table -AutoSize"
}
```

</details>

```
FullName                                                                                                    Length Mode
--------                                                                                                    ------ ----
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\results\c2b_adjudication_hf_2026-07-24\c1\activations      0 -a-…
<shellId: 6 completed with exit code 0>
```


---

<sub>2m 21s</sub>

### Copilot

**结论：A) `VALID_NEGATIVE`。** 这个 0/3→`KILL_PLAN_D` 是**合格负结果**，我未发现会让结果失效的 BLOCKER（未见“静默失败伪造 null”迹象）。

1. **BLOCKER: 无**
2. **MINOR — 可追溯性缺口（不影响本次 verdict）**：日志声明有 per-cell checkpoint（`adj2.run.log:18`），但交付目录里无 `checkpoints/`，使得外部审计无法直接复盘 dev 侧每 item×k 的原始样本轨迹（仅能依赖最终 JSON + 源码逻辑）。
3. **UNVERIFIED（数据包粒度限制）**：`dev_prompt_outcome/dev_steer_outcome` 在 JSON 仅给均值（如 `axes[*].dev_selection`），dev 侧“是否全 0/1”无法直接逐 item 验证；但 test 侧分布与源码均不支持“恒零假 null”。

**关键核验证据（独立重算）**  
- **仪器在工作**：`adj2.run.log` 有完整 cell 进度，从 `done=0` 到 `done=11365/11365`（`16,19-193`），结束 `ADJ2_EXIT_RC=0`（`198`），无 stall/fatal/traceback（`194-199`）。  
- **C1 重推导一致**：`adj2.run.log:10-12` 三轴 ratio 分别 `0.583/0.548/0.713` 且 CI 上界均 `<1`，与结果里 layer=20/stable (`c2b_adjudication_results.json` `c1_layer_info`)一致。  
- **verdict 数学忠实**：源码 pass 规则与三档判决严格实现冻结判据（`adjudicate_c2b.py:395-411,832-840,960-962`）；我从 JSON `axes[*].per_item_diff` 以 `B=10000, ci=0.983333, seed=20260723` 重算三轴 CI 与 `mean_diff`，与 `axes[*].ci_lo/ci_hi/mean_diff` **完全一致**；重算 axis passes 与 `axis_passes` 一致，verdict 仍 `KILL_PLAN_D`。  
- **不是 coherence gate 把 α“压小”造成假 null**：三轴 `dev_selection.alpha_grid[*].coherence_ok` 全为 `true`，且 degeneracy 全远低于门限；冻结 α 是因 dev outcome 最优，不是被 gate 逼到最小（delib α=2, skep α=6, unc α=8）。  
- **outcome scorer/分布非退化**：test 侧 `per_item_prompt/per_item_steer` 全在 `[0,1]`，且都非全 0/全 1：  
  - deliberation 有 `{0,0.2,0.4,0.6}` 等值；  
  - skepticism 在 `{0,0.2,0.4,0.6,0.8,1}`附近离散；  
  - uncertainty 为连续混合（含 0、0.0975、0.75、1.0 等）。  
  因此不符合“输出塌缩导致恒零差值”的假 null 形态。  
- **配对/聚类正确**：同一 `test_items` 同时生成 prompt 与 steer，再做 `per_item_diff = steer - prompt`（`adjudicate_c2b.py:787-832`）；JSON 中逐元素满足 `steer_i-prompt_i==diff_i`。bootstrap 为 item-level resample（`335-376`；调用点 `832-833`）。

**科学判断（你问的核心）**  
这次负结果**更直接支持“当前 CAA steering 方法太弱”**（在三轴均未超 prompt，且 uncertainty 轴显著负向），同时也**与“非满射鸿沟”叙事相容**（latent 方向可控不等于任务 outcome 可提升）。但仅凭这一次（单模型+单方法族）还不足以单独证明一般性的非满射定理；它是强有力的**方法失败证据**，也是对 non-surjective claim 的**支持性但非决定性**证据。

---

<sub>Generated by [GitHub Copilot CLI](https://github.com/features/copilot/cli)</sub>
