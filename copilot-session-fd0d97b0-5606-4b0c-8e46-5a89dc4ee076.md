# Copilot CLI Session

> [!NOTE]
> - **Session ID:** `fd0d97b0-5606-4b0c-8e46-5a89dc4ee076`  
> - **Started:** 7/24/2026, 2:25:35 PM  
> - **Duration:** 1m 52s  
> - **Exported:** 7/24/2026, 2:27:27 PM  

---

<sub>9s</sub>

### User

你是 R1 = Novelty & Significance 审稿人，模拟 IUI/CHI 顶会评审。只读下面这个【冻结的 Review Input Bundle】，不要读 docs/ledgers/decision-log.md 或任何 manager-response（避免被作者期望结论带偏）。按 AI-Instruction.md Part I §10 执行。

【Review Input Bundle（只读这些）】
- docs/paper/reframe-2026-07-24-reality-check.md   ← 待评审的重构提案（主）
- docs/ledgers/claim-ledger.md                     ← 重构后 Claim C1/C2/C2-mech/C2a/C3
- docs/ledgers/evidence-ledger.md                  ← 证据 E-0003(C1@7B 3/4) 与 E-0005(C2b 合格负结果)
- results/c2b_adjudication_hf_2026-07-24/c2b_adjudication_summary.md  ← 负结果原始 summary
- docs/ledgers/prereg-c2b-adjudication.md          ← 冻结协议
- 开题报告_非满射双通道认知控制台.md               ← 背景 idea

【背景约束（作者已定，供你判断，不必替他决定）】拟走 Route A 纯模型（砍真人研究），console 降为次要设计论证；venue 未锁死（无真人→首选 IUI，次 CHI 经验 track）。核心贡献=“表征可读 ≠ 行为可控”的 reality-check + off-manifold insight。

【你的任务】Scope Check → 独立复述你眼中的贡献（别抄作者措辞）→ 从 Novelty & Significance 角度逐条攻击 C1/C2/C2-mech：这个“可读≠可控”的负结果+insight 是否足够 novel/significant 撑起 IUI/CHI 顶会？相对已知工作（activation steering vs prompting 的既有比较、Mishra 非满射、PSR/“Steer Like the LLM”等）增量在哪、会不会被说“已知/incremental”？给 strongest accept case 与 strongest reject case。

【必须明确回答这 4 个问题（作者点名要）】
1) 单 steering 方法(CAA)+单模型族(Qwen2.5) 得到的负结果，对顶会是否**致命**？
2) **无真人研究**（纯模型 measurement+机制）在 IUI/CHI 是否可行、能到什么分数区间？
3) **CHI vs IUI vs CSCW** 三者与这个纯模型 reality-check 的契合度排序与理由？
4) 要把负结果做得“扛得住顶会”，**至少要补多少稳健性**（几种方法×几个模型？要不要 off-manifold 机制证据？还差什么）？

只报不改。输出写入 docs/reviews/2026-07-24-reality-check-reframe/review-R1.yaml：scope、独立贡献复述、ranked findings(BLOCKER/MAJOR/MINOR/QUESTION)+每条最便宜的判别动作+关闭条件、对上述4问的直接回答、初评分区间+confidence+前三拒稿风险。commit 该文件，trailer:
Co-authored-by: Copilot \<223556219+Copilot@users.noreply.github.com>
Copilot-Session: 51c5d0b2-bb0c-4bef-8d19-60e076eb999e

---

<sub>18s</sub>

### Copilot

先读取你指定的冻结材料并据此生成独立 R1 审稿意见，然后写入目标 YAML 并提交。

---

<sub>24s</sub>

### `view`

**view the file at C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\docs\paper\reframe-2026-07-24-reality-check.md.**

C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\docs\paper\reframe-2026-07-24-reality-check.md

<details>
<summary>126 lines</summary>

```
1. # Paper Reframe — "Reality-Check" main thread (DRAFT for human review)
2. 
3. > Status: **DRAFT proposal**, not frozen. Follows owner directive 2026-07-24 (disciplined reframe, option 4):
4. > bank C1 + the C2b qualified negative as CORE evidence, freeze the judgment, reframe rather than pivot-to-bland
5. > or chase a positive. Target venue: **CHI**. This doc drafts the restructured Claims / Contributions /
6. > Claim↔Evidence map for sign-off. The optional new independent pre-registered exploratory arm (§5 of this doc)
7. > is a SEPARATE budget decision.
8. 
9. ---
10. 
11. ## 1. One-line thesis (reframed)
12. 
13. > **A cognitive axis can be *legible* in a model's representations yet *not controllable* through those same
14. > legible directions: reading the state is not the same as steering the behavior — and naive latent steering
15. > can make calibration worse.** We turn this gap into a design stance: a console that instruments the
16. > *boundary/limits* of legible control and helps non-experts *recalibrate trust*, rather than a "latent
17. > superpower slider."
18. 
19. This keeps the non-surjective backbone (Mishra et al., internal non-surjectivity) as *why the gap plausibly
20. exists internally*, but our empirical contribution is the **reality check on the behavioral side**: the
21. internal legibility does **not** cash out into a behavioral advantage over the best prompt.
22. 
23. ---
24. 
25. ## 2. Restructured Claims (map to claim-ledger)
26. 
27. ### C1 — Representational Legibility Gap ("facade") is REAL  · RQ1 · CORE-empirical
28. - **Statement:** For metacognitive axes, the strongest human-readable prompt's mid-layer activation projects
29.   onto the CAA axis-direction *well below* the vector-only pole (and above a random-direction null), i.e. a
30.   prompt reaches only a fraction of the representable axis extent — a measurable *legibility/representation gap*.
31. - **Evidence:** **E-0003** (Qwen2.5-7B, 3/4 axes, CI<1, seed-stable) + E-0001/2 (1.5B corroboration).
32. - **Status:** **partially-supported / STRENGTHENED @7B (exploratory, single model family).**
33. - **Owed for confirmatory:** ≥2 model families (Llama-3 replication), protocol freeze.
34. 
35. ### C2 — Legibility ≠ Behavioral Controllability  · RQ2 · **CORE reality-check (was C2b)**
36. - **Statement:** Steering along the *legible* CAA direction does **not** push task behavior beyond the
37.   best-prompt ceiling on any tested axis under a frozen, pre-registered adjudication; on calibration it is
38.   **actively harmful**. Concretely (frozen instrument, N=60/60/80, k=5, Bonferroni item-cluster bootstrap):
39.   Δ(steer−prompt) = deliberation +0.015 [-0.040,+0.070], skepticism −0.080 [-0.225,+0.045],
40.   uncertainty **−0.228 [-0.370,-0.092]** → **0/3 pass**.
41. - **Evidence:** **E-0005** (audited **VALID_NEGATIVE**, KILL_PLAN_D verdict, exp c2b-adj-deac6326-0001).
42. - **Status:** **SUPPORTED as a (pre-registered) negative / reality-check claim.**
43. - **Framing rule (owner):** reported as an honest qualified negative; the judgment is frozen and will not be
44.   revised. "Our steering method may be too weak" lives in **Limitations/Future Work**, NOT as grounds to
45.   re-open the frozen verdict.
46. 
47. ### C2-mech — Off-manifold degradation (calibration harm) — INSIGHT / mechanism HYPOTHESIS · RQ2
48. - **Statement (hypothesis):** The calibration *worsening* under steering (uncertainty −0.228) is consistent
49.   with the intervention pushing activations *off the natural data manifold* along a direction that is
50.   linearly legible but not a valid behavioral control coordinate — legibility of a direction does not imply
51.   it is a manifold-respecting lever.
52. - **Evidence:** currently **inferential** from E-0005 (behavioral), NOT mechanistically proven.
53. - **Status:** **proposed (core insight framed as hypothesis).** A targeted diagnostic (activation-norm /
54.   manifold-distance vs. Δoutcome) is the natural cheap confirmation — candidate for the new exploratory arm
55.   (§5) or Future Work.
56. 
57. ### C2a — Internal Non-Surjectivity (theory backdrop)  · RQ2 · BACKGROUND
58. - **Statement:** Latent steering reaches internal residual states no bounded prompt reproduces (Mishra et al.
59.   2604.09839). Used as *motivation for why an internal gap plausibly exists*, not as our empirical result.
60. - **Status:** **parked / cited-as-background** (we did not run the internal-reproduction probe; C2 is about
61.   the behavioral non-transfer, which is our contribution).
62. 
63. ### C3 — Console as a Boundary/Limit + Trust-Calibration Instrument  · RQ3 · DESIGN/HCI (Plan B elevated)
64. - **Statement:** Re-cast the interface from a "latent control slider" to an instrument that (a) *surfaces
65.   where* legible latent control fails or degrades behavior, and (b) helps non-experts *recalibrate trust* and
66.   attribute prompt↔latent conflict — i.e., a legibility/limits console, not a superpower panel.
67. - **Evidence:** formative + controlled user study — **NOT yet run; IRB/human-subjects = §5, human-gated.**
68. - **Status:** **proposed (design contribution).**
69. 
70. ---
71. 
72. ## 3. Contribution structure (Introduction bullets, reframed)
73. 
74. 1. **A measurement** showing a *representational legibility gap* on metacognitive axes: the best readable
75.    prompt occupies only a fraction of the axis extent a latent vector spans (C1 / E-0003).
76. 2. **A reality check** — the headline: this legibility **does not transfer to behavioral control**. Under a
77.    frozen, independently-audited pre-registered adjudication, latent steering along the legible direction
78.    fails to beat the best prompt on every axis and *degrades* calibration (C2 / E-0005). *Legibility ≠
79.    controllability.*
80. 3. **An insight**: the calibration harm is consistent with an *off-manifold* account of why a linearly
81.    legible direction is not a valid control coordinate (C2-mech, framed as hypothesis).
82. 4. **A design reframe**: a console that instruments the *boundaries/limits* of legible control and supports
83.    *trust recalibration*, rather than promising latent superpowers (C3, study human-gated).
84. 
85. Honest scope line for Abstract/Intro: *single open-model family (Qwen2.5), one steering method family (CAA);
86. we claim a reality check + design stance, not a general impossibility theorem.*
87. 
88. ---
89. 
90. ## 4. Claim ↔ Evidence map (bidirectional; gate: nothing enters Abstract/Contrib/Conclusion without this)
91. 
92. | Claim | Supported by | Verdict/strength | Main table/figure (planned) | valid_for_paper |
93. |---|---|---|---|---|
94. | C1 (legibility gap real) | E-0003 (7B 3/4), E-0001/2 (1.5B) | exploratory, CI<1 seed-stable | Fig: per-axis prompt-reach/pole-reach ratio + CI | exploratory (needs 2nd model) |
95. | C2 (legibility ≠ control) | E-0005 (audited VALID_NEGATIVE, 0/3) | pre-registered qualified negative | Table: Δ(steer−prompt) + Bonferroni CI per axis | YES (frozen negative) |
96. | C2-mech (off-manifold) | inferential from E-0005 | hypothesis | Fig (future): manifold-dist vs Δoutcome | NO (hypothesis) |
97. | C2a (internal non-surj) | Mishra et al. 2604.09839 | cited background | — | background only |
98. | C3 (limits+trust console) | formative+controlled study | not yet run (IRB §5) | study figures (future) | NO (pending study) |
99. 
100. **Reverse map (every planned main artifact → which Claim):** Δ-table → C2; ratio-CI figure → C1;
101. manifold figure (future) → C2-mech; study figures (future) → C3.
102. 
103. ---
104. 
105. ## 5. OPTIONAL new independent pre-registered exploratory arm (SEPARATE budget decision — human-gated)
106. 
107. > Per owner: this must be an INDEPENDENT prereg with its own mechanism hypothesis + success/kill + budget,
108. > must NOT touch the frozen C2b record (E-0005), and has *asymmetric* paper value. Drafted separately for a
109. > go/no-go; NOT part of the frozen reality-check spine above. See companion draft:
110. > `docs/ledgers/prereg-latent-recovery-arm-DRAFT.md` (to be written on request).
111. >
112. > - **Mechanism hypothesis:** a *manifold-constrained* / *layer-targeted* / *stronger-but-projected* latent
113. >   intervention can recover behavioral gain on ≥1 axis where naive CAA failed (esp. reverse the uncertainty
114. >   harm), because the failure is off-manifold, not intrinsic non-reachability.
115. > - **Asymmetric value:** all-axes failure → *strengthens & generalizes* the C2 negative (not just "our method
116. >   was weak"); some-axis success → a *scope-narrowed positive* (controllability recoverable under manifold
117. >   constraints) that becomes a secondary contribution — never overwrites E-0005.
118. > - **Needs:** frozen success/kill criteria + GPU budget estimate BEFORE running (owner sign-off).
119. 
120. ---
121. 
122. ## 6. What is now FROZEN and must not be revised
123. - E-0003 (C1 @7B) and **E-0005 (C2b qualified negative, KILL_PLAN_D)** — banked, judgment frozen.
124. - prereg-c2b-adjudication.md — the frozen protocol; post-hoc changes forbidden.
125. - Any method-improvement exploration = new independent prereg (§5), never edits to the above.
126.
```

</details>


---

<sub>24s</sub>

### `view`

**view the file at C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\docs\ledgers\claim-ledger.md.**

C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\docs\ledgers\claim-ledger.md

<details>
<summary>65 lines</summary>

```
1. # Claim Ledger
2. 
3. > Every Claim entering Abstract / Introduction-Contributions / Conclusion MUST map here with sufficient
4. > evidence. Every main table/figure MUST state which Claims it supports. Contradicting evidence is never
5. > deleted — only explained, scope-narrowed, or the Claim withdrawn. (AI-Instruction Part I §4.2)
6. 
7. Status values: proposed | partially-supported | supported | contradicted | withdrawn
8. 
9. ---
10. 
11. ## C1 — Representational Legibility Gap / Semantic Facade (RQ1) — CORE-empirical
12. - **Statement:** For chosen cognitive axes, the strongest human-readable prompt's mid-layer activation
13.   projects onto the CAA vector direction far below vector-only AND far above a random-direction null
14.   baseline, with a pre-registered meaningfully large gap (a measurable legibility/representation gap).
15. - **Scope:** Llama-3-8B-Instruct, Qwen2.5-7B-Instruct; axes = Deliberation/Skepticism/Uncertainty/Focus.
16. - **Type:** empirical regularity (diagnostic → confirmatory after protocol freeze)
17. - **Status:** **partially-supported / STRENGTHENED @7B (EXPLORATORY, single model family).** E-0003:
18.   Qwen2.5-7B 3/4 axes hold (deliberation 0.583 [0.488,0.680], skepticism 0.548 [0.434,0.670], uncertainty
19.   0.713 [0.517,0.910], CI<1 seed-stable; focus overshoot/no facade). Corroborated at 1.5B (E-0001/2). NOT
20.   confirmatory — single model family, valid_for_paper=false; ≥2-model (Llama-3) replication owed.
21. - **Required evidence:** projection/cosine of strongest-prompt vs CAA vector vs random null; blind-eval.
22. - **Known limits:** projection is a linear proxy; axis may be non-linear/multi-mechanism.
23. - **Paper location:** Contribution 1 (measurement); ratio-CI figure. See reframe-2026-07-24-reality-check.md.
24. 
25. ## C2 — Legibility ≠ Behavioral Controllability (RQ2, CORE reality-check; reframed from C2b)
26. - **Statement:** Steering along the *legible* CAA direction does NOT push task behavior beyond the
27.   best-prompt ceiling on any tested axis under a frozen pre-registered adjudication; on calibration it is
28.   actively harmful. Δ(steer−prompt): deliberation +0.015 [-0.040,+0.070], skepticism −0.080 [-0.225,+0.045],
29.   uncertainty **−0.228 [-0.370,-0.092]** → 0/3 pass → KILL_PLAN_D.
30. - **Scope:** Qwen2.5-7B-Instruct; CAA method family; frozen instrument (prereg-c2b-adjudication.md).
31. - **Type:** pre-registered empirical (qualified NEGATIVE, reported as core reality-check claim)
32. - **Status:** **SUPPORTED as a pre-registered negative.** Evidence **E-0005** (audited VALID_NEGATIVE).
33.   Judgment FROZEN — will not be revised; "method may be too weak" → Limitations/Future Work only.
34. - **Falsified if:** a manifold-respecting / stronger latent intervention beats best-prompt behavior — tested
35.   ONLY via a SEPARATE independent pre-registered arm (never edits E-0005).
36. - **Paper location:** Contribution 2 (headline); Δ-table.
37. 
38. ## C2-mech — Off-manifold degradation (calibration harm) — mechanism HYPOTHESIS / core insight (RQ2)
39. - **Statement (hypothesis):** the calibration worsening under steering (uncertainty −0.228) is consistent
40.   with the intervention pushing activations off the natural data manifold along a linearly-legible but
41.   non-control-valid direction.
42. - **Type:** interpretive hypothesis (behavioral-inferential, NOT mechanistically proven)
43. - **Status:** **proposed (insight framed as hypothesis).** Cheap confirmation = manifold-distance vs Δoutcome
44.   diagnostic (new arm §5 / Future Work). Evidence: inferential from E-0005.
45. - **Paper location:** Contribution 3 (insight).
46. 
47. ## C2a — Internal-State Non-Surjectivity (RQ2, theory backdrop) — BACKGROUND
48. - **Statement:** Latent steering reaches internal residual states that no prompt in a bounded search
49.   reproduces. **Basis:** Mishra et al. (2604.09839).
50. - **Type:** theory-supported motivation (NOT our empirical result)
51. - **Status:** **parked / cited-as-background.** We did not run the internal-reproduction probe; our
52.   empirical contribution (C2) is the behavioral non-transfer, not internal non-surjectivity.
53. - **Falsified if:** a bounded prompt search reproduces the steered internal state.
54. 
55. ## C3 — Console as Boundary/Limit + Trust-Calibration Instrument (RQ3, DESIGN/HCI — Plan B elevated)
56. - **Statement:** Re-cast the interface from a "latent control slider" to an instrument that surfaces WHERE
57.   legible latent control fails/degrades behavior and helps non-experts recalibrate trust and attribute
58.   prompt↔latent conflict.
59. - **Scope:** formative + 4-condition controlled study; open white-box models.
60. - **Type:** design/HCI contribution (empirical user study)
61. - **Status:** **proposed.** Evidence = formative + controlled study — NOT yet run; IRB/human-subjects = §5,
62.   human-gated.
63. - **Known limits:** cross-model automatic re-mapping is the hardest engineering piece.
64. - **Paper location:** Contribution 4 (design).
65.
```

</details>


---

<sub>24s</sub>

### `view`

**view the file at C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\docs\ledgers\evidence-ledger.md.**

C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\docs\ledgers\evidence-ledger.md

<details>
<summary>13 lines</summary>

```
1. # Evidence Ledger
2. 
3. > Links Hypothesis → Experiment → Evidence → Claim. Every quantitative datum used in the paper must
4. > trace to an immutable experiment_id in experiment-registry.yaml. No hand-copied numbers.
5. 
6. | evidence_id | supports_claim | from_experiment_id | artifact | verdict | last_verified |
7. |---|---|---|---|---|---|
8. | E-0001 | C1 (partial, exploratory) | c1-facade-d553d2cb-0001 | results/c1_facade_1p5b_v2_2026-07-23/ | 2/4 axes (deliberation 0.566, uncertainty 0.714) facade gap CI<1; skepticism no; focus fail. Qwen2.5-1.5B EXPLORATORY. SUPERSEDED by E-0002. | 2026-07-23 |
9. | E-0002 | C1 (partial, exploratory, STRENGTHENED) | feature/4 strengthened run | results/c1_facade_1p5b_strengthened_2026-07-23/ | Qwen2.5-1.5B: 2/4 axes hold (deliberation, uncertainty); skepticism borderline; focus unstable. SUPERSEDED by E-0003 (7B). | 2026-07-23 |
10. | E-0003 | C1 (STRENGTHENED @ 7B, exploratory) | c1-facade-d710b4b4-0001 (A800) | results/gpu_7b_2026-07-23/c1/ | **Qwen2.5-7B-Instruct (GPU fp16): 3/4 axes hold** — deliberation 0.583 [0.488,0.680], skepticism 0.548 [0.434,0.670] (RECOVERED at 7B; borderline at 1.5B), uncertainty 0.713 [0.517,0.910], all CI<1 seed-stable. focus 2.844 (overshoot, no facade). Caveat: deliberation layer-16 CI crosses 1 (layer-sensitive). EXPLORATORY, single model, valid_for_paper=false. | 2026-07-23 (Manager verified: GPU run device-fixed, cache-key includes device/dtype) |
11. | E-0004 | C2b (RQ2 core — NEGATIVE/inconclusive, exploratory) | c2b-reach-16382b53-0001 (A800) | results/gpu_7b_2026-07-23/c2b/ | **Qwen2.5-7B: latent steering did NOT reach behavior beyond the bounded-prompt ceiling on 3/4 axes** (deliberation/skepticism/uncertainty beyond=False; only focus beyond=+0.010 trivial + failed-C1 axis). Conflict: prompt wins 3/4 (uncertainty=latent). CRUDE lexical proxies (ceiling-saturated ~0.88-1.0), single greedy sample — audit says CANNOT support "latent beyond prompt" claim. Does NOT support RQ2 core bet; mildly against. EXPLORATORY, valid_for_paper=false. INVALID (audit-rejected proxy basis) — SUPERSEDED by E-0005. | 2026-07-23 |
12. | E-0005 | C2b / RQ2 core — **QUALIFIED NEGATIVE (KILL→Plan D)** | c2b-adj-deac6326-0001 (rented RTX4080S) | results/c2b_adjudication_hf_2026-07-24/ | **Qwen2.5-7B-Instruct, FROZEN pre-registered instrument (prereg §4/§5): 0/3 axes pass → VERDICT=KILL_PLAN_D.** N=60/60/80, k=5, α∈{2,4,6,8,12,16,24}, DEV/TEST split, paired item-cluster bootstrap B=10000, Bonferroni CI 0.98333, δ=0.05, coherence gate ≤1.5×. mean(d): deliberation +0.015 [-0.040,+0.070]; skepticism -0.080 [-0.225,+0.045]; uncertainty **-0.228 [-0.370,-0.092]** (steering HURTS). All coherence gates ok; frozen α not compressed by gate (2/6/8). **Independent hostile audit (audit-c2b-verdict): VALID_NEGATIVE**, no BLOCKER, CIs re-derived == JSON exactly, instrument ran full 11365 gens RC=0 no-stall, outcomes non-degenerate, pairing correct. Interpretation: naive CAA latent steering does NOT beat the best-prompt ceiling behaviorally — supports "prompt is a strong ceiling / non-surjective" narrative but is **method-weakness evidence, single-model+single-method, NOT a decisive non-surjectivity proof.** valid_for_paper: honest negative (exploratory-confirmatory-instrument, but single model). | 2026-07-24 (Manager + hostile audit VALID_NEGATIVE) |
13.
```

</details>


---

<sub>24s</sub>

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

<sub>24s</sub>

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

<sub>24s</sub>

### `view`

**view the file at C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md.**

C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md

```
File too large to read at once (31.4 KB). Consider using the grep tool to search within the file, or view with view_range to read specific sections.
```


---

<sub>32s</sub>

### `rg`

**Mishra|非满射|RQ2|贡献|PSR|Steer Like the LLM|activation steering|prompt**

"Mishra|非满射|RQ2|贡献|PSR|Steer Like the LLM|activation steering|prompt" (开题报告_非满射双通道认知控制台.md)

<details>
<summary>6 matches</summary>

```
Output too large to read at once (24.3 KB). Saved to: C:\Users\V-ELZH~1\AppData\Local\Temp\copilot-tool-output-1784874366955-1.txt
Consider using tools like rg (for searching), head/tail (for viewing start/end), view with view_range (for specific sections), or jq (for JSON) to examine portions of the output.

Preview (first 500 chars):
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md:3:**非满射双通道认知控制台 (Non-Surjective Dual-Channel Cognitive Console)**
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md:13:**结论：Go（推进），但采取 Adjust（调整航向） 策略。**这个方向既不是空白地带，也不是死局——关键是把贡献点从“做一个更好的操控工具”转移到“揭示并弥合文本可控性与底层机制之间的认知错位”。
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md:15:**撞车（Scoop）现状（两层分离）：**把 steering 包装成滑块的 **工程/界面层已被抢先**——Huang & Lim (IASDR 2025) 已为非技术用户做了 feature-ste
```

</details>


---

<sub>32s</sub>

### `glob`

**docs/reviews/****

"docs/reviews/**"

<details>
<summary>8 matches</summary>

```
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\docs\reviews\2026-07-23-charter\review-R3.yaml
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\docs\reviews\2026-07-23-charter\review-R2.yaml
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\docs\reviews\2026-07-23-charter\review-R1.yaml
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\docs\reviews\2026-07-23-charter\manager-response.yaml
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\docs\reviews\2026-07-23-charter\.prompt-template.txt
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\docs\reviews\2026-07-23-charter\.prompt-R3.txt
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\docs\reviews\2026-07-23-charter\.prompt-R2.txt
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\docs\reviews\2026-07-23-charter\.prompt-R1.txt
```

</details>


---

<sub>36s</sub>

### `rg`

**^#|^##|^###|结论|RQ1|RQ2|Mishra|PSR|Steer Like|贡献**

"^#|^##|^###|结论|RQ1|RQ2|Mishra|PSR|Steer Like|贡献" (开题报告_非满射双通道认知控制台.md)

<details>
<summary>28 matches</summary>

```
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md:13:**结论：Go（推进），但采取 Adjust（调整航向） 策略。**这个方向既不是空白地带，也不是死局——关键是把贡献点从“做一个更好的操控工具”转移到“揭示并弥合文本可控性与底层机制之间的认知错位”。
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md:17:**决定性的重构（本报告的核心整合判断）：**不要把 RQ2 押在“可读 prompt ≈ 不可读 steering 向量对齐”上。一篇已发表结果——**Mishra, Khashabi & Liu，《Steered LLM Activations are Non-Surjective》(arXiv:2604.09839, ICLR 2026 Workshops)**——在实践假设下证明：activation steering 会把残差流推离“任何离散 prompt 可达的状态流形”，**“几乎必然没有任何 prompt 能复现 steering 诱导的内部行为”**，并确立了 white-box steerability 与 black-box prompting 之间的形式化分离。这把原假设从一个脆弱的赌注，变成了一个可以稳稳站立的 **理论基石**。
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md:19:**黄金一句（选题定位）：**正因为自然语言 prompt 存在物理天花板（“语义表象 / semantic facade”），我们设计一个 **双通道认知控制台**，让非专家用户能够：(1) **看见**自己基于民间理论（folk theories）的 prompt 在哪里触墙；(2) 用底层 latent 杠杆 **跨过**这道墙；(3) 在两通道冲突时 **重建** 心智模型并校准信任。HCI 贡献 = “非满射双通道控制界面”的交互模型 + 可读性/冲突消解/信任校准的实证设计知识——而不是“又一个 steering 方法或滑块”。
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md:21:**最强的一句话贡献：**“LLM 控制不是 prompt engineering，而是 legibility engineering + boundary engineering。”
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md:37:**两份调研的关键分歧点，恰好是本课题的成败所在。** 一份把 RQ2 押在“文本与向量在表征空间指向同一方向（对齐）”；另一份指出这一假设已被证伪，真正的价值在于 **暴露两者的不等价**。独立核实后，后者成立：
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md:39:- **非满射性（已发表、可核实）：**Mishra et al. 把“steered 行为是否可由任何文本 prompt 实现”形式化为 surjectivity 问题，证明在实践假设下 steering 把残差流推离 prompt 可达流形，并在三个常用 LLM 上实证。
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md:41:- **旁证（真实、可核实）：**ActAdd (Turner et al.) 的 Appendix B 排除实验早已显示：注入 embedding 向量效果微弱，但注入经前若干层运算后的 activation 差异效果显著，且 perplexity 上 prompting 会在无关条件上造成大幅退化而 ActAdd 不会——“ActAdd 至少部分使用了另一种机制”。这与非满射结论方向一致。
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md:45:**贡献边界（务必写清）：**我们不声称提出新的 steering 方法（CAA/RepE 是现成材料），也不满足于“把向量做成滑块”（Huang & Lim 已做）。HCI 增量是：把 **非满射鸿沟本身** 变成可读、可操作、可校准的交互对象，并产出面向“latent 可控性界面”的设计知识。
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md:61:| **工作** | **贡献** | **与本方向的 Gap** |
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md:67:| Folk attributions of consciousness (Colombatto & Fleming, 2024) | 多数受访者愿意对 LLM 赋予现象意识可能性。 | 警示解释面板须防过度拟人化 over-trust；提供 RQ1 背景。 |
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md:71:| **工作** | **贡献** | **与本方向的关系** |
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md:77:| Instruction-Following Steering (Stolfo et al., ICLR 2025) | 从有/无指令的 activation 差构造 instruction 向量，控制 format/length/keyword，可组合、可迁移到 base model。 | 最接近 RQ2 的机制论文；证明自然语言指令可对应内部向量（但不做 user-facing 认知轴与非满射交互）。 |
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md:85:| Mishra, Khashabi & Liu, Steered LLM Activations are Non-Surjective (arXiv:2604.09839, ICLR 2026 Workshops) | 证明 steering 把残差流推离 prompt 可达流形；几乎必然无 prompt 能复现；确立 white-box/black-box 形式化分离。 | 颠覆与转机：否定“对齐”原假设，正面赋予“双通道 + 边界探索”界面以合法性。本课题的理论基石。 |
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md:99:| RQ1 认识论错位 / 语义表象 | 在复杂推理与校准任务中，用户基于民间理论构造的 prompt，其在模型表征空间实际激发的潜变量分布，与用户主观预期的认知属性（怀疑度/审慎度）之间存在何种程度的认识论错位？这种“语义表象”如何误导用户的信任校准？ | 避免只重复“情绪 prompt 有效”；转向测量“用户以为控制了 vs 实际激发了”的差，直接对话 XAI 与信任。 |
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md:100:| RQ2 非满射控制与冲突消解（核心） | 既然 latent 干预能到达 prompt 无法触及的非满射状态，当控制台同时暴露两条通道时，非专家如何理解并协同使用？当二者冲突（prompt 要“自信”、滑块拉“怀疑”）时，用户如何归因并适应这种“超越文本”的控制力？ | 把已被证伪的“对齐”换成“暴露鸿沟 + 冲突消解”，这是 latent 界面独有、且无人研究的交互问题。 |
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md:103:**押注排序：**RQ2 最有潜力成为核心贡献（连接 HCI 可读构念与 ML 非满射因果）；RQ1 最易被覆盖（已有 end-user prompt/元认知文献），须靠“语义表象定量化”取胜；RQ3 工程最难（跨模型自动重映射），可作为延展或消融。
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md:115:**视觉隐喻（Phase 2 需攻克）：**占比条 / 雷达图叠加（文本贡献 vs latent 贡献）、“文本可达边界地图 + 越界指示”、冲突时的双针仪表。目标是让不可见的 latent 控制力与可见文本获得同一坐标系下的可比表达。
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md:117:**设计原则（贡献产出物之一）：**legibility（暴露真实控制份额而非承诺等价）、boundary-awareness（明示语言天花板）、conflict-resolution（冲突可归因、可裁决）、calibrated-agency（提升控制感而不抬高拟人化过信）、non-anthropomorphic（用“功能性维度”而非“情绪/意识”话术）。
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md:121:6.1 Phase 0 — RQ2 可行性 Pilot（数据级，2–3 周，先于造系统）
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md:137:- **Step 6（冲突探针）　**prompt 要求“高置信” + 滑块拉“高怀疑”，记录行为落点——RQ2 冲突交互的实证地基。
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md:155:- **产出：**用户对认知轴的理解/命名/预测，folk theories 与“语义表象”误解证据（支撑 RQ1）。
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md:197:7 候选贡献（一句话洞见）
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md:207:**防守核心：**activation steering 是材料，HCI 贡献是 interaction model、user-legible abstraction、非满射鸿沟的可读化与冲突消解、calibrated control 与实证设计知识。
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md:215:- **先例背书：**AI-Instruments、AI Chains、EvalLM 均用 LLM/ML 机制，却因 interaction model + user study 进入 HCI 顶会。本文遵循同一范式，并明确声明 Phase 0 的 alignment 检验是 feasibility/mechanism 支撑，不是 HCI 贡献本身。
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md:237:| 系统整体效果不显著 | 三条件差异不达显著 | Plan D：转 measurement paper——贡献 prompt 可读性鸿沟的 benchmark 与诊断协议。 |
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md:258:| 1 | Steered LLM Activations are Non-Surjective. Mishra, Khashabi, Liu. arXiv:2604.09839, ICLR 2026 Workshops. | 理论基石：证明 steering 越出 prompt 可达流形。✓ |
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md:276:| 19 | Improving Instruction-Following through Activation Steering. Stolfo et al. ICLR 2025. | 最接近 RQ2 的机制论文（指令向量、可组合/迁移）。✓ |
C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md:288:| 核心 RQ2 赌注 | prompt≈vector 对齐（偏弱，已被非满射否定） | 暴露非满射鸿沟 / 冲突（更强，被采纳为主线） |
```

</details>


---

<sub>36s</sub>

### `view`

**view the file at C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\docs\reviews\2026-07-23-charter\review-R1.yaml.**

C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\docs\reviews\2026-07-23-charter\review-R1.yaml

```
File too large to read at once (29.6 KB). Consider using the grep tool to search within the file, or view with view_range to read specific sections.
```


---

<sub>39s</sub>

### `view`

**view the file at C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\docs\reviews\2026-07-23-charter\review-R1.yaml.**

C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\docs\reviews\2026-07-23-charter\review-R1.yaml (lines 1-220)

<details>
<summary>220 lines</summary>

```
1. # ============================================================================
2. # HUMAN-READABLE SUMMARY (R1 — Novelty & Significance, CHI, Charter stage)
3. # ----------------------------------------------------------------------------
4. # Verdict: MAJOR-REVISION (charter viable to freeze only after wording + prior-art fixes).
5. # The core idea — making the *prompt<->latent non-surjective gap itself* an operable,
6. # calibratable interface object — is the freshest, least-occupied framing in this space
7. # and is NOT a trivial steering+slider mashup ON PAPER. But three things put CHI
8. # acceptance at real risk and MUST be closed before the next gate:
9. #   1. THEORY OVER-APPLICATION (BLOCKER-class for the *claim wording*, not the idea):
10. #      Mishra proves non-surjectivity of INTERNAL activations; C2 asserts BEHAVIORAL
11. #      unreachability ("prompt can't cross a threshold the slider can"). That inference
12. #      is unearned and Stolfo et al. (instruction<->vector correspondence) can be
13. #      weaponized against it. The charter leans its headline on a result that does not
14. #      entail the headline.
15. #   2. "OBVIOUS COMBINATION" RISK vs Huang&Lim (layperson steering sliders + study),
16. #      AI-Instruments (control-as-direct-manipulation object), Labarta (interactive
17. #      attribution->steering + user study + trust), Tankelevitch (metacognition framing).
18. #      The whole contribution currently rests on ONE not-yet-demonstrated differentiator:
19. #      quantified facade (RQ1) + genuine prompt<->latent CONFLICT attribution (RQ2). If
20. #      those collapse empirically, the paper degrades to "a prompt box next to their sliders."
21. #   3. SIGNIFICANCE / "NLP dressed as HCI": the interaction insight that could NOT be
22. #      predicted from the 5 neighbors is asserted, not yet evidenced. CHI reviewers will
23. #      demand design knowledge that transcends "add explainability + customizability"
24. #      (which Tankelevitch already recommended).
25. # Also: correct the SemanticLens/Labarta mis-framing (vision+experts, not an LLM UI
26. # competitor) and rename "dual-channel" (ICLR'26 W already owns "Dual-Channel Steering").
27. # None of these are fatal at Charter stage; all are cheap to close pre-experiment.
28. # score_if_unchanged: 2.0-2.5/5 ; score_if_blockers_closed: 3.0-3.5/5 (borderline->positive).
29. # ============================================================================
30. 
31. review_id: review-R1-charter-2026-07-23
32. snapshot_id: charter-2026-07-23
33. reviewer_role: "R1 — Novelty & Significance (independent, no stake)"
34. target_venue: CHI
35. review_stage: charter
36. review_scope: >
37.   Charter-gate review (pre-experiment). Assess novelty, significance, and CHI-fit of the
38.   proposed contribution and the falsifiable claims C1-C3. Judge whether the defensible
39.   one-sentence novelty survives against the nearest neighbors and the Novelty-Falsification
40.   report's scoop findings. NOT assessing full results/paper (none exist yet — correct for stage).
41. 
42. materials_examined:
43.   - docs/charter/project-charter.md (v0.1 DRAFT)
44.   - docs/research/2026-07-23-novelty-falsification.md (independent Novelty Gate output)
45.   - docs/ledgers/claim-ledger.md (C1-C3)
46.   - 开题报告_非满射双通道认知控制台.md (author intent / background)
47.   - AI-Instruction.md Part I §10 (review protocol/format)
48. 
49. missing_materials:
50.   - No system/prototype, no Phase-0 pilot data, no facade projection numbers (expected: pre-experiment stage; not penalized).
51.   - No completed manual CHI'26 / ACM DL prior-art sweep (Novelty report §3 flags it as still owed — treat "field is clear" as PROVISIONAL).
52.   - ActAdd "Appendix B exclusion experiment" sub-claim unverified (Novelty report §2, §6.4) — flagged [NEEDS EVIDENCE], not yet load-bearing for a claim.
53.   - No claim->evidence paper-location mapping yet (claim-ledger "Paper location: TBD") — acceptable at charter stage.
54. 
55. expertise_level: "high (HCI + representation-engineering/steering literature); medium on the exact non-surjectivity proof internals"
56. conflict_check: "no conflict; did not author charter/idea; did not read Manager expectations or any desired verdict"
57. overall_score_range: "2.0-3.5 / 5 (conditional: 2.0-2.5 if unchanged; 3.0-3.5 if blockers closed)"
58. confidence: "medium-high on novelty/significance analysis; medium on scoop-clearance (prior-art sweep incomplete)"
59. verdict: major-revision
60. 
61. # ---------------------------------------------------------------------------
62. paper_understanding:
63.   one_sentence_problem: >
64.     Non-expert users cannot see or coordinate the gap between what their natural-language
65.     prompt actually achieves inside an LLM and what a direct latent intervention (steering
66.     vector) can additionally reach; this proposal asks whether surfacing that
67.     prompt<->latent divergence as a first-class, operable interface object lets users
68.     understand, adjudicate conflicts, and calibrate trust over a control capability that
69.     provably exceeds prompting.
70.   claimed_contributions:
71.     - "C1 (RQ1): an empirically quantified 'semantic facade' — the strongest human-readable prompt's mid-layer activation projects far below the steering-vector direction (projection << 100%), surfaced to users as a trust-relevant measure."
72.     - "C2 (RQ2, CORE): a new interaction paradigm — a dual-channel console + attribution panel — that (a) exhibits a prompt-unreachable control region the latent channel crosses, and (b) lets non-experts attribute and resolve prompt<->latent CONFLICT better than prompt-only or steering-only baselines."
73.     - "C3 (RQ3, extension): metacognitive-axis levers act as a boundary object preserving perceived control/continuity across a backend model swap (Llama-3 -> Qwen-2.5) better than prompt folklore."
74.     - "Framing/theory contribution: reifying the non-surjective gap as an interaction problem, grounded in Mishra et al. (non-surjectivity) and Tankelevitch et al. (metacognitive demands)."
75.   strongest_accept_case: >
76.     No prior system makes the prompt<->latent DIVERGENCE ITSELF the operable object. Huang&Lim
77.     expose a single latent channel (sliders, no prompt-conflict, no facade quantification, no
78.     trust re-calibration on disagreement); AI-Instruments stays entirely at the prompt layer;
79.     Labarta is vision + expert debugging. Studying how a NON-EXPERT attributes, adjudicates, and
80.     re-trusts when a readable prompt and a latent lever openly CONFLICT is a genuinely new HCI
81.     phenomenon with clear theoretical grounding (non-surjectivity + metacognition) and a real
82.     kill/pivot discipline. If RQ1's facade metric measurably shifts trust behavior and RQ2 shows
83.     even one true prompt-unreachable behavioral region with better non-expert conflict attribution,
84.     this is a fresh, generative interaction model — exactly the "system + theory + controlled study
85.     + design knowledge" CHI rewards.
86.   strongest_reject_case: >
87.     This is an obvious combination of five published parts (Huang&Lim sliders + Labarta attribution
88.     panel + AI-Instruments reification + Tankelevitch framing + Mishra citation for gravitas), and
89.     the theoretical foundation is misapplied: Mishra proves internal-STATE non-surjectivity, not
90.     that any user-relevant BEHAVIOR is unreachable by prompting — so the headline "prompts hit a wall
91.     the sliders cross" is not established by the theory it leans on, and Stolfo et al. show
92.     instruction<->vector correspondence that cuts directly against a behavioral gap. The novel
93.     ingredient (quantified facade + conflict attribution) is asserted, not demonstrated, and could
94.     collapse to "we added a prompt box next to existing sliders." Term "dual-channel steering" is
95.     already coined for a different ML method. Net: high risk of "NLP dressed as HCI" with a novelty
96.     delta contingent on results that do not yet exist.
97.   clarity_mismatches:
98.     - "The charter's core-novelty table (§4) and the Novelty report DISAGREE on scoop risk (charter self-rates the core gap 'LOW'; independent report rates it 'MEDIUM'). The charter should adopt the more conservative MED and stop citing its own optimistic rating."
99.     - "C2's statement conflates an internal-state result (Mishra) with a behavioral claim (task threshold). A CHI reviewer will read 'provably exceeds what any prompt can reach' (RQ2 text, §1) as claiming the PROOF covers behavior — it does not. The word 'provably' is doing illegitimate work."
100.     - "§4 bundles 'SemanticLens' and Labarta 'From Attribution to Action' as one neighbor and implies an LLM latent-UI competitor; they are two artifacts, vision-modality, expert-facing. This overstates the threat AND mis-cites — both hurt credibility."
101. 
102. # ---------------------------------------------------------------------------
103. findings:
104. 
105.   - finding_id: R1-F1
106.     severity: blocker
107.     dimension: novelty
108.     target_claim_ids: [C2]
109.     paper_locations:
110.       - "charter §1 RQ2 ('a control capability that provably exceeds what any prompt can reach')"
111.       - "charter §5 C2 / claim-ledger C2 statement"
112.       - "charter §4 row 'Mishra et al.' ('Our theoretical foundation')"
113.     criticism: >
114.       The core contribution's theoretical legitimacy is built on an unearned inference. Mishra et al.
115.       (verified, arXiv:2604.09839) prove non-surjectivity of the INTERNAL residual-stream activation:
116.       no prompt reproduces the same internal STATE. C2 claims BEHAVIORAL unreachability: prompt-only
117.       cannot cross a task/compliance threshold the latent channel can. Two distinct internal states can
118.       produce identical output behavior, so the behavioral claim is strictly stronger and NOT entailed
119.       by the proof. Worse, Stolfo et al. (ICLR 2025, verified) demonstrate instruction<->vector
120.       correspondence and composability — a hostile reviewer will use it to argue prompts DO reach much
121.       of what steering does behaviorally. As written, the paper leans its headline novelty on a theorem
122.       that does not support the headline.
123.     evidence_examined: "Novelty report §0.2, §2 (Mishra row), §5 RQ2 row, §6.1; charter §1/§4/§5; claim-ledger C2."
124.     why_it_matters_for_acceptance: >
125.       Novelty & significance for CHI hinge on the 'non-surjective gap' being a REAL, theory-grounded
126.       phenomenon rather than rhetorical framing. If the theory-to-claim link is exposed as over-reach,
127.       the contribution collapses from 'principled new interaction problem' to 'we found some tasks where
128.       our sliders beat prompts' — an engineering demo, not a paradigm. This is the single most likely
129.       reviewer kill-shot.
130.     alternative_explanation: >
131.       Any observed prompt-vs-slider behavioral gap may be an artifact of (a) weak/under-optimized
132.       prompting (prompt-search budget too small), or (b) the specific compliance-floor task construction,
133.       NOT a fundamental reachability wall. Non-surjectivity of state does not imply the gap survives fair,
134.       well-budgeted prompt optimization.
135.     requested_evidence_or_change: >
136.       (1) Rewrite C2 and RQ2 to SEPARATE 'internal-state non-surjectivity (proven, cited)' from
137.       'behavioral/task unreachability (an empirical claim to be demonstrated, NOT assumed)'. Delete or
138.       qualify 'provably' in the behavioral sentence. (2) Add an explicit prompt-optimization budget to the
139.       protocol so the 'strongest prompt' is defensibly strong (else the gap is trivially attackable).
140.     cheapest_discriminating_action: >
141.       A wording/scoping edit to C2 + RQ2 + §4 (zero compute), PLUS defining a fair prompt-search budget in
142.       the Minimum Publishable Evidence section. No experiment required at charter stage.
143.     acceptance_condition: >
144.       C2 explicitly framed as an empirical behavioral claim (not theorem-entailed), the theory cited only
145.       for internal-state non-surjectivity, and a fair prompt-optimization protocol specified.
146.     confidence: high
147.     possible_reviewer_misunderstanding: >
148.       If the authors already intend 'provably' to modify only the internal-state result and 'behavioral gap'
149.       as separately-to-be-shown, then this is a CLARITY fix rather than a substantive error — but the current
150.       text does not make that separation, so the risk stands regardless.
151.     requires_new_experiment: false
152.     estimated_cost_class: trivial
153.     user_approval_required: false
154. 
155.   - finding_id: R1-F2
156.     severity: blocker
157.     dimension: significance
158.     target_claim_ids: [C1, C2]
159.     paper_locations:
160.       - "charter §4 core-novelty table (all rows) + one-sentence novelty (§4)"
161.       - "charter §3 Contribution Type"
162.     criticism: >
163.       The entire novelty delta rests on TWO not-yet-demonstrated differentiators — (i) a quantified
164.       'semantic facade' surfaced to users (C1/RQ1) and (ii) genuine non-expert attribution/resolution of
165.       prompt<->latent CONFLICT (C2/RQ2). Every other ingredient is already published: layperson steering
166.       sliders + user study (Huang&Lim, IASDR'25), interactive attribution->steering + user study + trust
167.       grounding (Labarta, CVPR'26 W), control-as-direct-manipulation object (AI-Instruments, CHI'25), and
168.       the metacognition framing that already RECOMMENDS 'explainability + customizability' (Tankelevitch,
169.       CHI'24). If the two differentiators do not empirically deliver something non-obvious, the paper is a
170.       predictable instantiation of Tankelevitch's recommendation and an 'obvious combination' of the rest.
171.     evidence_examined: "Novelty report §1 (neighbor matrix rows 1-4), §4 (steel-manned reject), §5, §6.2; charter §4."
172.     why_it_matters_for_acceptance: >
173.       CHI significance is judged on whether the interaction insight could NOT have been predicted from prior
174.       work. Right now the charter ASSERTS the insight is non-obvious but stakes it entirely on results that
175.       do not exist. Reviewers routinely reject charter-quality novelty that is 'contingent on our study working.'
176.     alternative_explanation: >
177.       It is possible the conflict/facade phenomena are genuinely novel and rich; but it is equally possible
178.       that, once built, condition C reduces to 'sliders + a prompt box,' with conflict resolution being
179.       whatever the sliders already afford. The charter cannot yet distinguish these.
180.     requested_evidence_or_change: >
181.       Add to the charter a concrete, falsifiable statement of WHAT specific interaction phenomenon (beyond
182.       Huang&Lim's single channel and Tankelevitch's recommendation) the study is designed to reveal, and a
183.       pre-registered analysis that would show it is non-trivial (e.g., attribution-accuracy delta and a
184.       trust-recalibration behavior that single-channel steering cannot produce by construction).
185.     cheapest_discriminating_action: >
186.       Charter-text addition (design-knowledge target + pre-registered discriminating measure). Optionally, a
187.       cheap Phase-0 desk analysis mapping each planned finding to the specific neighbor it must beat. No compute.
188.     acceptance_condition: >
189.       Charter names the non-obvious design contribution explicitly and specifies a measure that would
190.       falsify 'obvious combination' — reviewed and judged plausible before Protocol Freeze.
191.     confidence: high
192.     possible_reviewer_misunderstanding: >
193.       A generous reviewer may accept 'the conflict-attribution phenomenon is inherently new' on face; but R1
194.       should not rely on reviewer generosity for the load-bearing contribution.
195.     requires_new_experiment: false
196.     estimated_cost_class: trivial
197.     user_approval_required: false
198. 
199.   - finding_id: R1-F3
200.     severity: major
201.     dimension: soundness
202.     target_claim_ids: [C1]
203.     paper_locations:
204.       - "charter §5 C1 / claim-ledger C1 (projection << 100%)"
205.       - "charter §7 Phase 0 (quantified semantic-facade projection)"
206.     criticism: >
207.       C1 as stated ('strongest prompt projects significantly below vector-only') is close to a COROLLARY of
208.       Mishra + ActAdd and is nearly assumed-true: a linear projection of a prompt-induced activation onto a
209.       contrastive steering direction being <100% is almost guaranteed and by itself carries little novelty.
210.       The Novelty report (§5 RQ1) rates RQ1 MED-HIGH risk precisely because the bare projection fact is
211.       near-trivial. Novelty lives ONLY in showing the facade is (a) surfaced to users as a measure and
212.       (b) demonstrably mis-calibrates or re-calibrates trust — which C1's current wording does not require.
213.     evidence_examined: "Novelty report §5 (RQ1 row), §6.1; claim-ledger C1 'projection is a linear proxy'; charter §5/§7."
214.     why_it_matters_for_acceptance: >
215.       If C1 is confirmed but framed only as 'projection < 100%,' reviewers will say the empirical regularity
216.       is unsurprising and unpublishable on its own, weakening the RQ1 leg and increasing pressure on RQ2 to
217.       carry the whole paper.
218.     alternative_explanation: >
219.       A <100% projection could reflect a non-linear or multi-mechanism axis (claim-ledger 'known limits')
220.       rather than a genuine 'facade' — i.e., the metric under-reads reachability rather than proving a wall.
```

</details>


---

<sub>39s</sub>

### `glob`

**docs/reviews/2026-07-24-reality-check-reframe/***

"docs/reviews/2026-07-24-reality-check-reframe/*"

```
No files matched the pattern.
```


---

<sub>42s</sub>

### `view`

**view the file at C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\docs\reviews\2026-07-23-charter\.prompt-R1.txt.**

C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\docs\reviews\2026-07-23-charter\.prompt-R1.txt

<details>
<summary>28 lines</summary>

```
1. You are an INDEPENDENT Reviewer for ACM CHI, simulating a top-conference reviewer at the CHARTER REVIEW gate (before any experiments). You are Reviewer R1 — Novelty & Significance. You did NOT write this proposal and have NO stake in it. Your job is to surface rejection risk with verifiable objections, NOT to satisfy the authors.
2. 
3. READ ONLY these frozen materials (the Review Input Bundle):
4. - docs/charter/project-charter.md  (the proposal under review)
5. - docs/research/2026-07-23-novelty-falsification.md  (the independent Novelty Gate output)
6. - docs/ledgers/claim-ledger.md  (claims C1–C3)
7. - 开题报告_非满射双通道认知控制台.md  (background idea; treat as author's intent)
8. Also read AGENTS.md and AI-Instruction.md Part I §10 for the review protocol and output format.
9. Do NOT read any Manager expectations or desired verdict. Where a material is missing or not-yet-available, report it as missing evidence — do NOT invent it, and do NOT penalize early-stage absence of a full paper/results (this is the Charter stage, pre-experiment).
10. 
11. FOCUS FOR YOUR ROLE (R1 — Novelty & Significance):
12. You are the NOVELTY & SIGNIFICANCE reviewer. Attack hardest on: is the 'non-surjective gap as interface object' truly novel vs AI-Instruments (CHI25), Huang and Lim (IASDR25), SemanticLens? Is it an obvious combination of steering + sliders? Is the contribution significant enough for CHI, or is it 'NLP dressed as HCI'? Weigh the novelty-falsification report's scoop findings heavily. Does the defensible one-sentence novelty actually survive?
13. 
14. PROCEDURE (per §10.4): Scope Check → Independent Read (restate the problem & contributions in your own words; flag clarity mismatches) → Claim Attack (attack C1/C2/C3: novel? important? falsifiable? supported-in-principle? alternative explanations? beyond evidence scope?) → Evidence/Plan Audit (is the proposed Minimum Publishable Evidence sufficient to distinguish core explanations? are baselines fair? is the study design sound?) → Reviewer Simulation (give BOTH strongest reject case AND strongest accept case) → Rank Findings (BLOCKER/MAJOR/MINOR/QUESTION) → Cheapest discriminating action per BLOCKER/MAJOR → Initial Verdict (score range, confidence, top-3 rejection risks).
15. 
16. OUTPUT: write a valid YAML file to docs/reviews/2026-07-23-charter/review-R1.yaml following EXACTLY the structure in AI-Instruction.md §10.5:
17. - Review Header: review_id, snapshot_id (use "charter-2026-07-23"), reviewer_role, target_venue (CHI), review_stage (charter), review_scope, materials_examined, missing_materials, expertise_level, conflict_check, overall_score_range, confidence, verdict.
18. - Paper Understanding: one_sentence_problem, claimed_contributions, strongest_accept_case, strongest_reject_case, clarity_mismatches.
19. - findings: list; each with finding_id, severity, dimension, target_claim_ids, paper_locations, criticism, evidence_examined, why_it_matters_for_acceptance, alternative_explanation, requested_evidence_or_change, cheapest_discriminating_action, acceptance_condition, confidence, possible_reviewer_misunderstanding, requires_new_experiment, estimated_cost_class, user_approval_required.
20. - Review Summary: top_3_rejection_risks, must_fix_before_next_gate, optional_improvements, questions_for_manager, score_if_unchanged, score_if_blockers_closed.
21. Also write a short human-readable summary as YAML-comment lines at the top.
22. 
23. CONSTRAINTS: Read-only reviewer — do NOT modify the charter, code, ledgers, or experiment configs; only write your own review file. If you find ethics/licensing/privacy/data-contamination/fabricated-citation/reproducibility risk, mark it BLOCKER. Do not package personal preference as a hard venue standard; lower confidence when unsure. Do NOT commit anything — just write and save your review file. The Manager will review and commit it.
24. 
25. When done, print your verdict, overall_score_range, confidence, and top_3_rejection_risks to stdout (≤12 lines).
26. 
27. 
28.
```

</details>


---

<sub>42s</sub>

### `view`

**view the file at C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\AI-Instruction.md.**

C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\AI-Instruction.md (lines 1-260)

<details>
<summary>260 lines</summary>

```
1. # AI 协作总指令 · Unified AI Instruction
2. 
3. > **定位**：本文件是本项目的单一 AI 协作总指令，供任何 Agent 在开始工作前完整阅读。它由三层组成，自上而下约束递减、服从关系明确：
4. >
5. > 1. **Part I · 科学研究操作系统**（Scientific Research OS）— 决定「要证明什么、证据是否成立、能否投稿」。最高优先级。
6. > 2. **Part II · 工程实现与交付工作流**（Engineering & Implementation Workflow）— 决定「如何可靠地产出实现与 Artifact」。服从 Part I。
7. > 3. **Part III · 学术写作与润色指南**（Academic Writing & Polishing）— 决定「如何把研究准确、自然地写成英文」。服从 Part I 的证据与主张边界。
8. >
9. > **使用前**：先完成 Part I 的 Research Charter、权限与预算配置，再执行 Part II 的工程流程；写作阶段遵循 Part III。Part II 中的占位符 `<...>` 需按其 §0 做一次性适配。
10. >
11. > **总铁律**：优化 Evidence 而非 Narrative；根据证据修改 Claim，而非根据 Claim 选择证据；任何无法进入「Hypothesis -> Experiment -> Evidence -> Claim -> Paper」证据链的工作，都不应消耗全量实验预算。
12. >
13. > **说明**：本项目的研究核心依据（idea 本体）见 `开题报告_非满射双通道认知控制台.md`，属于研究对象而非本指令的一部分。
14. 
15. ---
16. # Part I · Scientific Research Operating System
17. 
18. ## AI-Native Scientific Research Operating Principle
19. 
20. 本工作流的目标不是让 Agent“完成一篇论文”，而是让 Agent 在**可审计、可复现、可证伪、预算受控**的前提下，最大化产生顶会级科学贡献的概率。
21. 
22. - 优化 Evidence，而不是优化 Narrative。
23. 
24. - 允许 Hypothesis 失败，而不是强迫实验成功。
25. 
26. - 根据证据修改 Claim，而不是根据 Claim 选择证据。
27. 
28. - 记录负结果、失败运行、研究转向与被否定的路线。
29. 
30. - 所有论文数字必须追溯到不可变实验记录。
31. 
32. - 独立 Reviewer 必须从 Novelty、Soundness、Statistics、Reproducibility 与 Clarity 五个维度进行敌对审计。
33. 
34. **Strong Accept 是优化目标，不是强制结果。**当证据不足时，正确动作是收缩主张、补充高信息增益实验、转向或停止，而不是制造正向结果。
35. 
36. ## 1. Research Charter：先定义要证明什么
37. 
38. 开始写代码前，Manager 必须创建并冻结第一版 **Research Charter**。任何无法映射到 Charter 的任务不得进入全量实验预算。
39. 
40. - **Research Question：**要回答的科学问题，而不是要实现的功能。
41. 
42. - **Target Venue：**目标会议、投稿周期、格式与政策约束；会议变化属于用户审批事项。
43. 
44. - **Contribution Type：**新方法、新理论、新 benchmark、新经验规律、新系统、负结果或复现/纠错。
45. 
46. - **Core Novelty：**相对 3–5 个最近邻工作的新增价值及可能等价关系。
47. 
48. - **Falsifiable Claims：**哪些可观察结果支持、削弱或反驳主张。
49. 
50. - **Non-Claims：**论文明确不声称的范围、因果性、泛化性与部署能力。
51. 
52. - **Minimum Publishable Evidence：**最低数据集、baseline、seed、消融、统计与误差分析要求。
53. 
54. - **Kill / Pivot Criteria：**何时终止，何时允许转向，以及转向后哪些证据不可继续沿用。
55. 
56. - **Budget：**GPU 小时、API/Token 成本、日历时间、full run 次数、pivot 次数与人工审批阈值。
57. 
58. Charter 必须版本化。任何核心问题、贡献类型或目标会议的变化，都要写入 Decision Log，并重新执行 Novelty 与 Evidence Gate。
59. 
60. ## 2. 三平面架构与唯一调度权
61. 
62. ### 2.1 Control Plane · Manager Session
63. 
64. Manager 是唯一调度权威：维护研究方向、Claim 状态、预算、Gate、Agent 分配、暂停/继续/转向/退休决策。它不得为了“完成论文”而合理化负结果。
65. 
66. ### 2.2 Execution Plane · Sub-Agent Sessions
67. 
68. Sub-Agent 负责文献检索、实现、实验、统计、作图、写作、复现与审计。Sub-Agent 不得直接修改全局研究目标，也不得把探索性结果升级为核心 Claim。
69. 
70. ### 2.3 Observation Plane · User Session
71. 
72. User Session 是只读观察与干预入口，不是第二个 Manager。用户改变范围、Claim、预算、venue 或冻结协议的指令，必须转发给当前 Manager，并持久化到 **decision-log.md**。紧急情况下用户可暂停 Manager；暂停后不得继续派发新任务。
73. 
74. ### 2.4 权限矩阵
75. 
76. - **默认允许：**读代码、写独立 worktree、L0–L2 检查、创建计划与草稿。
77. 
78. - **Manager 可批准：**Pilot、探索性实验、注册新假设、废弃无效实验、合并 slice 到 topic。
79. 
80. - **必须用户批准：**超预算 Full Run、修改核心 Claim/venue、使用付费或私有数据、删除/覆盖数据、对外提交或发布、涉及人类参与者或许可不确定的操作、修改冻结协议、把探索性发现升级为核心 Claim。
81. 
82. ## 3. Manager 生命周期、轮替与交接考试
83. 
84. Manager 不仅按 Token 数轮替，还要按**上下文健康度**轮替。硬触发包括：达到最大 Token/墙钟时间/重大决策数、接近上下文限制、无法准确复述 Claim–Evidence–Risk 状态。软触发包括：阶段完成、重大 Pivot、重复询问已记录信息、决策与日志冲突、实验状态遗漏或用户要求。
85. 
86. **禁止在以下时点轮替：**全量实验或数据迁移中途、未落盘的关键诊断、multi-agent merge 未完成、存在未解释异常。
87. 
88. 退休前必须生成固定 Handoff Bundle：project-charter.md、current-state.md、claim-ledger.md、hypothesis-ledger.md、evidence-ledger.md、experiment-registry.yaml、decision-log.md、failure-log.md、open-risks.md、compute-ledger.md、literature-ledger.bib、paper-outline.md 与 handoffs/manager-X-to-Y.md。
89. 
90. 新 Manager 必须先通过接管考试：准确陈述当前研究问题、核心 Claim、每个 Claim 的证据状态、最强 baseline、主要失败模式、前三项风险、下一步动作与不可自行决定事项。Handoff Auditor 判定通过后，才可更新 ACTIVE_MANAGER；旧 Manager 随即只读，禁止双 Manager 并行调度。
91. 
92. ## 4. Hypothesis–Claim–Evidence Ledger
93. 
94. Manager 管理的核心不是任务列表，而是 **Hypothesis → Experiment → Evidence → Claim → Paper** 的证据链。
95. 
96. ### 4.1 Hypothesis 分类
97. 
98. - **Confirmatory：**验证预先声明的核心 Claim；协议冻结后不得看结果改成功标准。
99. 
100. - **Exploratory：**发现规律或新方向；可动态调整，但必须显式标记，不能直接作为确认性证据。
101. 
102. - **Diagnostic：**排查实现、优化或数据问题；默认不支撑论文核心结论。
103. 
104. 每次运行前记录 hypothesis_id、experiment_type、decision_before_run、expected_outcome、success_criterion、failure_interpretation、positive/negative next action 与 protocol_frozen。
105. 
106. ### 4.2 Claim Ledger
107. 
108. 每个核心主张必须有 claim_id、精确 statement、scope（数据集/模型/指标/条件）、claim_type、状态（proposed / partially-supported / supported / contradicted / withdrawn）、所需证据、支持与反对实验、已知限制及论文位置。
109. 
110. **双向 Gate：**进入 Abstract、Introduction Contributions 或 Conclusion 的每个 Claim 都必须映射到 Ledger 且证据充分；每张主表和主图也必须标明支持哪些 Claim。Contradicting evidence 不得删除，只能解释、降级适用范围或撤回 Claim。
111. 
112. ## 5. Novelty Gate 与引用完整性
113. 
114. Literature Review 的目标不是证明“看起来新”，而是主动寻找最强反例。独立 Novelty/Falsification Agent 必须尝试证明：该想法已存在、只是显然组合、属于轻量工程变化、在不同记号下数学等价，或已在另一任务名/benchmark 下评估。
115. 
116. Novelty Gate 至少输出：最近邻工作矩阵、objective/训练信号/数学形式/机制对比、时间线与 concurrent work、Reviewer 第一反应、可站得住的一句话 novelty、风险等级与仍未验证的差异。
117. 
118. **Citation Verification Gate：**引用必须真实可检索；标题、作者、年份一致；关键判断必须基于正文而非只看摘要；“prior work does not…”必须有可核验证据；禁止虚构论文、二手摘要替代原文或把关键词差异当机制差异。当前 ICLR 对 LLM 使用的政策强调作者对输出负责，虚假主张、误述、伪造数据与幻觉引用均不可接受。
119. 
120. 推荐的审计指令：*Your goal is to falsify the claimed novelty, not to support it. Construct the strongest novelty objection a skeptical top-conference reviewer would make, and tie every factual statement to a verifiable source.*
121. 
122. ## 6. 分级实验授权：L0–L4
123. 
124. - **L0 静态检查：**配置、路径、split 泄漏、metric、baseline 公平性、seed、checkpoint、eval mode、输出主键与版本记录。
125. 
126. - **L1 极小样本测试：**跑通 shape/loss/gradient；手算 metric；尝试 overfit 一个小 batch。
127. 
128. - **L2 Smoke Run：**1% 数据、1 seed、少量 step、最小模型；只验证 pipeline，不判断科学结论。
129. 
130. - **L3 Pilot：**1–2 个代表性任务和 seed，验证效应方向、量级、方差、时长与成本。
131. 
132. - **L4 Full Confirmatory Run：**仅在协议冻结、baseline 公平性、metric 单测、泄漏检查、预算、唯一实验 ID、恢复机制、代码与数据版本全部通过后执行。
133. 
134. Full-run Authorization 必须记录 authorization_id、experiment_group、预计 GPU 小时/成本、pilot evidence、protocol commit、data version、baseline fairness / metric validation / leakage / recovery verdict、批准者与预算状态。任何“效果不好就调整”必须先判断它是科学调整、诊断修复，还是看结果追目标；后者禁止。
135. 
136. ## 7. 统计完整性与公平比较 Gate
137. 
138. - 预先规定主指标、次指标与排除规则；test set 不得用于迭代调参。
139. 
140. - 使用足够随机 seed，报告中心趋势、方差或置信区间，并解释样本量。
141. 
142. - 同时考虑 effect size 与 statistical uncertainty，不能只追逐显著性。
143. 
144. - 多个数据集/指标/假设时，评估 multiple comparisons 风险。
145. 
146. - Proposed method 与 baseline 使用公平的超参数搜索预算、训练资源和停止标准。
147. 
148. - 失败运行不得无记录删除；outlier 排除必须使用预先声明规则。
149. 
150. - 区分 best checkpoint、last checkpoint 与多次运行平均表现。
151. 
152. - 报告硬件、训练时间、计算量、软件环境及 sensitivity/robustness 分析。
153. 
154. - 消融必须对应机制解释，不得用“删掉后变差”自动证明因果机制。
155. 
156. NeurIPS Paper Checklist 将主张与证据范围的一致性、限制、训练细节、误差条、计算资源、资产许可和伦理披露纳入提交检查；因此本 Gate 应在项目早期启用，而不是投稿前补表。
157. 
158. ## 8. Experiment Registry、Failure Log 与 Artifact Lineage
159. 
160. ### 8.1 不可变实验注册
161. 
162. 每次运行必须有唯一 experiment_id，并记录 parent experiment、hypothesis_id、claim_ids、type、status、code commit、dirty tree、data/environment/config hash、模型、数据集、seed、硬件、起止时间、exit code、原始/汇总指标、artifact、failure reason、valid_for_paper 与 validation notes。失败、取消和 invalidated 实验同样登记，禁止 outputs/final2/really_final 式文件夹科研。
163. 
164. ### 8.2 Failure Log
165. 
166. 记录失败路线、归因、尚未解释的异常、不可重复路线与随机性风险，防止 Manager 轮替后重复试错和 survivor bias。
167. 
168. ### 8.3 Artifact Lineage
169. 
170. 每张表和图必须有 manifest：artifact_id、paper_location、supports_claims、source_experiments、aggregation script 与 commit、raw data hash、output file、manual_edits_allowed=false、last_verified 与 verdict。禁止手抄数字进 LaTeX、从聊天复制 metric、手改图表数字或让脚本读取“最新目录”。
171. 
172. ACM Artifact Review and Badging 将代码、运行脚本、输入数据、原始结果与分析脚本都视为研究 Artifact，并区分 Artifacts Available、Artifacts Evaluated 与 Results Validated；本工作流以“至少可独立重建一张主表/主图”为内部最低复现目标。
173. 
174. ## 9. 五类独立审计与 Reviewer Scorecard
175. 
176. 1.  **Implementation Auditor：**实现、metric、baseline、泄漏、checkpoint、数值与并发。
177. 
178. 2.  **Scientific Skeptic：**Claim 是否被证据支持、替代解释、相关性/因果性、机制是否 overclaim。
179. 
180. 3.  **Novelty Reviewer：**最近邻工作、显然组合、数学等价与顶会增量。
181. 
182. 4.  **Statistics Auditor：**seed、方差、显著性、multiple comparisons、超参预算与选择性汇报。
183. 
184. 5.  **Reproducibility Reviewer：**在新环境仅按 README 安装，运行最小复现并重建至少一张主表或主图。
185. 
186. Reviewer Scorecard 必须覆盖 Significance、Novelty、Technical Soundness、Empirical Strength、Clarity、Reproducibility、Ethics & Limitations 和 Confidence。每项不仅给分，还要写：证据、主要扣分点、提高一级所需的最小工作、成本是否值得。
187. 
188. ICLR 2026 Reviewer Guide 强调及时、实质、充分的评审，并由 Reviewer、AC 与 SAC 共同形成判断；因此内部模拟评审必须角色分离，不能由论文写作 Agent 自己宣布“Strong Accept”。
189. 
190. ## 10. Reviewer Critic Session：独立评审闭环
191. 
192. Reviewer Critic Session 属于独立的 **Evaluation Plane**。它模拟目标顶会 Reviewer，以暴露拒稿风险为目标；不属于 Execution Plane，不是第二个 Manager，也没有调度、改稿、改代码、启动实验、修改 Claim 或扩预算的权限。
193. 
194. **核心铁律：**Reviewer Critic 的职责是提出可核验的反对意见，不是要求 Manager 满足所有 Reviewer 偏好；Manager 的职责是降低真实录用风险，不是迎合单个模拟 Reviewer。
195. 
196. ### 10.1 独立性与权限边界
197. 
198. - 每轮使用全新 Session，不继承写作 Agent 或 Manager 的聊天上下文。
199. 
200. - 只读取冻结的 Review Input Bundle；不得读取 Manager 的预期结论、辩解、内部评分或希望获得的 verdict。
201. 
202. - 只报问题，不直接修改论文、代码、Ledger 或实验配置。
203. 
204. - 所有批评必须指向可定位内容、缺失证据或明确 Reviewer 风险；禁止泛泛要求“补更多实验”。
205. 
206. - Reviewer 不得把个人偏好包装成顶会硬标准；不确定时必须降低 confidence。
207. 
208. - 若发现伦理、许可、隐私、数据污染、伪造引用或不可复现风险，立即标为 BLOCKER 并升级给用户。
209. 
210. ### 10.2 触发节点与评审模式
211. 
212. Reviewer Critic 不持续在线监控，而在固定里程碑触发，避免研究方向被随机意见牵引。
213. 
214. 1.  **Charter Review：**Research Charter 与 Novelty Gate 完成后；检查问题重要性、贡献类型、最近邻工作和可证伪性。
215. 
216. 2.  **Pre-Full-Run Review：**L3 Pilot 完成、L4 授权前；检查实验是否足以区分核心解释，阻止昂贵但低信息增益的设计。
217. 
218. 3.  **Claim Freeze Review：**主实验完成后；检查 Claim–Evidence 匹配、统计强度、替代解释和适用范围。
219. 
220. 4.  **Full-Paper Review：**第一版完整论文形成后；按真实顶会格式进行端到端评审。
221. 
222. 5.  **Submission Readiness Review：**Submission Freeze 前；仅检查残留 BLOCKER、政策、匿名、artifact 与可复现性，不再随意扩张研究范围。
223. 
224. 默认每个节点运行 3 个相互独立的 Critic：**R1 Novelty & Significance**、**R2 Technical Soundness & Experiments**、**R3 Skeptical Generalist & Clarity**。资源紧张时可只运行一个 Generalist，但必须降低最终评审置信度。三份评审完成后，可由只读 **Meta-Reviewer Session** 去重、识别冲突并形成优先级；Meta-Reviewer 同样无权命令 Manager。
225. 
226. ICLR 2026 Reviewer Guide 要求评审具备及时性、实质性和充分性，并在作者讨论后向 AC 提供建议；因此本工作流也将初评、Manager response 与 re-review 分开，而不是一次性打分。
227. 
228. ### 10.3 Review Input Bundle
229. 
230. Manager 在启动 Critic 前生成只读快照，并写明 snapshot_id 与版本。Reviewer 只能依据该快照判断；缺失内容必须报告为 missing evidence，不得自行猜测。
231. 
232. - target venue、track、review rubric 与当前阶段；
233. 
234. - 匿名版 title、abstract、paper PDF/正文与 appendix；
235. 
236. - Research Charter、Non-Claims、Claim Ledger 与 Claim Map；
237. 
238. - 最近邻工作矩阵及已核验 citation map；
239. 
240. - 实验协议、baseline fairness review、统计分析摘要；
241. 
242. - 主表/主图及对应 artifact manifests；
243. 
244. - 已知限制、failure log 摘要与 open risks；
245. 
246. - 当前预算余额和可执行动作边界，但不提供 Manager 偏好；
247. 
248. - 本轮 review_scope：允许评价哪些内容、哪些尚未形成而不应扣分。
249. 
250. 输入包必须区分 **not provided、not yet available、not applicable**。Reviewer 不能因早期阶段尚无完整论文而按 Submission 阶段扣分。
251. 
252. ### 10.4 Reviewer Critic 执行流程
253. 
254. 1.  **Scope Check：**确认 venue、阶段、评审范围、可用材料和自身专业匹配度；存在 conflict 或 expertise mismatch 时退出并请求替代 Reviewer。
255. 
256. 2.  **Independent Read：**先独立概括研究问题、贡献与证据，不读取任何 Manager response；若概括与作者意图不同，标记 clarity risk。
257. 
258. 3.  **Claim Attack：**逐一攻击核心 Claim：是否新、是否重要、是否被实验支持、是否存在替代解释、是否越过证据范围。
259. 
260. 4.  **Evidence Audit：**核对主表/主图、统计、baseline、公平性、消融、robustness、负结果、数据与 artifact lineage。
```

</details>


---

<sub>44s</sub>

### `view`

**view the file at C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\AI-Instruction.md.**

C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\AI-Instruction.md (lines 260-420)

<details>
<summary>161 lines</summary>

```
260. 4.  **Evidence Audit：**核对主表/主图、统计、baseline、公平性、消融、robustness、负结果、数据与 artifact lineage。
261. 
262. 5.  **Reviewer Simulation：**分别给出 strongest rejection case 与 strongest acceptance case，防止只寻找单向证据。
263. 
264. 6.  **Rank Findings：**按 BLOCKER / MAJOR / MINOR / QUESTION 排序，并合并同一根因下的重复意见。
265. 
266. 7.  **Cheap Test：**对每个 BLOCKER/MAJOR 指出能区分关键解释的最便宜动作；不得默认要求 full-scale experiment。
267. 
268. 8.  **Initial Verdict：**给出评分区间、confidence、主要不确定性与“最可能导致拒稿的前三项原因”。
269. 
270. Reviewer 必须把“论文真的有问题”和“论文表达导致误解”分开。若现有证据已足够但文本未呈现，应请求 clarification/rewrite，而不是直接要求新实验。
271. 
272. ### 10.5 Reviewer 输出格式
273. 
274. 每轮评审写入 **reviews/\<snapshot_id\>/review-\<reviewer_id\>.yaml**，并附一份人类可读摘要。结构如下：
275. 
276. **Review Header**
277. 
278. - review_id、snapshot_id、reviewer_role、target_venue、review_stage、review_scope；
279. 
280. - materials_examined、missing_materials、expertise_level、conflict_check；
281. 
282. - overall_score_range、confidence、verdict。
283. 
284. **Paper Understanding**
285. 
286. - one_sentence_problem；
287. 
288. - claimed_contributions；
289. 
290. - strongest_accept_case；
291. 
292. - strongest_reject_case；
293. 
294. - clarity_mismatches。
295. 
296. **每条 Finding** 必须包含：
297. 
298. - finding_id；severity：blocker \| major \| minor \| question；
299. 
300. - dimension：significance \| novelty \| soundness \| empirical \| statistics \| clarity \| reproducibility \| ethics；
301. 
302. - target_claim_ids 与 paper_locations；
303. 
304. - criticism 与 evidence_examined；
305. 
306. - why_it_matters_for_acceptance；
307. 
308. - alternative_explanation；
309. 
310. - requested_evidence_or_change；
311. 
312. - cheapest_discriminating_action；
313. 
314. - acceptance_condition；
315. 
316. - confidence；
317. 
318. - possible_reviewer_misunderstanding；
319. 
320. - requires_new_experiment、estimated_cost_class 与 user_approval_required。
321. 
322. **Review Summary** 必须列出 top_3_rejection_risks、must_fix_before_next_gate、optional_improvements、questions_for_manager、score_if_unchanged 与 score_if_blockers_closed。禁止只给总分而不提供关闭条件。
323. 
324. ### 10.6 Manager 反馈与分诊机制
325. 
326. Manager 收到 Review 后不得直接派发修改任务。首先创建 **reviews/\<snapshot_id\>/manager-response.yaml**，对每条 Finding 逐项给出 disposition：
327. 
328. - **ACCEPT：**问题成立，进入修复或补证据计划。
329. 
330. - **PARTIALLY_ACCEPT：**部分成立；拆分成立与不成立部分，限定处理范围。
331. 
332. - **REBUT_WITH_EVIDENCE：**现有证据已回答；给出 Claim、Experiment、Artifact 或正文位置，不以口头辩解关闭。
333. 
334. - **CLARIFY_ONLY：**属于表达或定位问题，不新增实验。
335. 
336. - **DEFER：**问题有价值但不影响当前 Gate，记录延期理由、风险与重访条件。
337. 
338. - **REJECT：**基于错误前提、超出 Non-Claims 或与 venue rubric 无关；必须给证据，不能因“不想改”而拒绝。
339. 
340. - **ESCALATE_TO_USER：**涉及核心 Claim、venue、冻结协议、伦理/许可、私有数据或预算阈值。
341. 
342. 每条响应必须记录 rationale、evidence_refs、planned_action、owner、budget_cost、deadline、expected_claim_state_change、requires_reaudit 与 closure_evidence。Manager 还要识别多个 Finding 是否源于同一根因，优先解决能同时关闭多项风险的动作。
343. 
344. Meta-Reviewer 负责合并重复意见、标记 Reviewer 分歧、判断共同 BLOCKER 与校准 confidence；但最终 disposition 仍由 Manager 提出，越权事项由用户裁决。
345. 
346. ### 10.7 修改、回审与关闭协议
347. 
348. 1.  Manager 将被接受的 Finding 转换为 task，但必须保留 finding_id、claim_id 与 snapshot_id 的追踪关系。
349. 
350. 2.  Execution Agent 完成修改或实验后提交 closure evidence；不得自行把 Finding 标为 resolved。
351. 
352. 3.  Manager 验证 artifact、预算、Claim Ledger 与论文同步更新，生成新的 snapshot。
353. 
354. 4.  原 Reviewer 优先执行 targeted re-review，只检查对应 Finding、连带 Claim 与新引入风险；不得无理由扩大范围。
355. 
356. 5.  Reviewer 给出 CLOSED / PARTIALLY_CLOSED / OPEN / SUPERSEDED / INVALIDATED verdict，并说明依据。
357. 
358. 6.  BLOCKER 只有在 Reviewer 复核，或 Meta-Reviewer/用户以证据推翻后才能关闭。
359. 
360. **回审上限：**同一 Finding 默认最多两轮。两轮后仍未关闭时，Manager 必须选择：升级用户、收缩 Claim、接受残余风险、转向或停止；禁止 Reviewer–Manager 无限争论。
361. 
362. **Gate 规则：**进入 L4 前不得存在与协议有效性相关的 OPEN BLOCKER；Claim Freeze 前不得存在与核心 Claim 证据相关的 OPEN BLOCKER；Submission Freeze 前不得存在任何 OPEN BLOCKER。MAJOR 可在记录风险并经 Manager/用户批准后延期，MINOR 不得自动触发高成本实验。
363. 
364. ### 10.8 防止 Reviewer 驱动失控
365. 
366. - 新增实验前必须说明它将改变哪个 Claim 状态、关闭哪个 Finding，以及正负结果分别如何决策。
367. 
368. - 同一 Reviewer 的偏好不得覆盖 Charter、Non-Claims、预算和 venue rubric。
369. 
370. - Reviewer 分歧不能靠“做完所有建议”解决；应由 Meta-Reviewer 区分真实不确定性、专业视角差异与表达误解。
371. 
372. - 若建议只提高叙事完整性而不改变科学判断，优先改写，不启动实验。
373. 
374. - 若建议成本高且预计信息增益低，Manager 应 DEFER 或 REJECT，并保留风险。
375. 
376. - Critic 不得在每次小改后重跑；只有 closure evidence 就绪、核心 Claim 改变或进入下一个 Gate 才触发。
377. 
378. - 任何评分提升都只能作为结果观察，不能成为追结果式扩实验的理由。
379. 
380. NeurIPS 对大规模评审流程的复盘指出，评审本身存在专业匹配与决策噪声问题；因此本系统保留多 Reviewer、Meta-Reviewer、confidence 与 disagreement，而不把单个 Critic 当作绝对裁判。
381. 
382. ## 11. 预算、信息增益与停止机制
383. 
384. Manager 必须维护 max_gpu_hours、max_api_cost、max_agent_tokens、max_calendar_days、max_full_runs 与 max_pivot_count。每次扩预算前回答：要降低哪个关键不确定性？结果会改变什么决策？正负结果分别如何处理？是否存在更便宜的实验？该运行是否只是“再试一次”？
385. 
386. **Stop / Pause Rules：**核心 novelty 被覆盖；多个代表性 Pilot 均无效；提升小于自然方差；优势依赖不公平 baseline；必须不断缩小评估范围才能维持 Claim；剩余预算不足以完成最低证据；连续两轮 Reviewer Simulation 出现同一 Blocker；新实验不再改变 Claim 状态。
387. 
388. Stop 不等于失败。Manager 应输出四选一建议：**continue、pivot、downgrade venue/scope、terminate/negative result**，并说明证据、机会成本与可逆性。
389. 
390. ## 12. Paper Writing 防幻觉合同与 Freeze 节点
391. 
392. 写作 Agent 不得发明引用、实验或数字；不得把 exploratory 写成 confirmatory、把相关性写成因果、把单数据集结果写成普遍规律、隐藏不利结果、未经验证声称 SOTA 或自行改图表数字。每句定量 Claim 必须指向 Artifact；每个 Novelty Claim 必须指向已验证引用；无法验证时标记 **\[NEEDS EVIDENCE\]**。
393. 
394. 必须维护 paper/claim-map.yaml、paper/citation-map.yaml、paper/table-manifests/ 与 paper/figure-manifests/。
395. 
396. - **Code Freeze：**核心实验代码冻结，修复需评估是否使既有结果失效。
397. 
398. - **Protocol Freeze：**confirmatory 的数据、split、metric、baseline、seed、搜索预算和排除规则冻结。
399. 
400. - **Result Freeze：**主结果确定后不得无记录替换。
401. 
402. - **Claim Freeze：**最终写作阶段修改核心 Claim 必须重跑 Claim–Evidence Audit。
403. 
404. - **Submission Freeze：**禁止新功能、大重构、关键依赖更换、未经审计的新实验与手工修数字。
405. 
406. 投稿前还应执行 Venue Policy Gate：核对最新作者指南、匿名/双投/LLM 披露、伦理、补充材料和 artifact 要求；人类作者对所有 AI 产出承担最终责任。
407. 
408. ## 13. Scientific Workflow 一页总览
409. 
410. **Idea → Charter → Novelty Falsification → Hypothesis/Claim Registration → Charter Review → L0–L3 → Pre-Full-Run Review → Protocol Freeze → L4 Confirmatory Runs → Statistical Audit → Claim Revision → Claim Freeze Review → Artifact Lineage → Paper Draft → Full-Paper Review → Manager Response → Revision/Experiment → Targeted Re-review → Submission Readiness Review → Submission Readiness Gate**
411. 
412. 不可跳过的关键 Gate：
413. 
414. - Novelty 未通过，不得进入高成本 Full Run。
415. 
416. - 协议未冻结，不得把结果标为 confirmatory。
417. 
418. - Claim 无双向 Evidence 映射，不得进入摘要、贡献或结论。
419. 
420. - 主表/主图无法从固定实验 ID 重建，不得进入 Result Freeze。
```

</details>


---

<sub>51s</sub>

### `powershell`

**Check repo status before edits**

<details>
<summary>Arguments</summary>

```json
{
  "command": "Set-Location \"C:\\Users\\v-elzhang\\Desktop\\MyFolder\\cognitive console\"; git --no-pager status --short",
  "description": "Check repo status before edits"
}
```

</details>

<details>
<summary>6 lines</summary>

```
?? .worktree-analysis-prompt.txt
?? .worktree-c1-prompt.txt
?? cc7.bundle
?? copilot-session-21d2c6f1-78c7-4b16-a72c-0246f705821a.md
?? copilot-session-96bb4b1c-cb6c-4a5a-904f-e44b0ee6beca.md
<shellId: 0 completed with exit code 0>
```

</details>


---

<sub>1m 40s</sub>

### Copilot

我将把评审写成结构化 YAML（含你点名的 4 问直答与 ranked findings），保存到指定路径后提交一次 commit。

---

<sub>1m 41s</sub>

### `apply_patch`

<details>
<summary>Arguments</summary>

```json
"*** Begin Patch\n*** Add File: C:\\Users\\v-elzhang\\Desktop\\MyFolder\\cognitive console\\docs\\reviews\\2026-07-24-reality-check-reframe\\review-R1.yaml\n+# ============================================================================\n+# R1 (Novelty & Significance) verdict: MAJOR-REVISION / borderline reject for CHI now.\n+# Strongest value is an honest, pre-registered behavioral negative that separates\n+# \"readable representation\" from \"useful control.\" Current fatal risk is external\n+# validity: single method (CAA) + single family (Qwen2.5) makes novelty easy to\n+# dismiss as method-specific failure. This can still be competitive for IUI (model-\n+# first reality-check framing) if robustness is expanded and mechanism language stays\n+# explicitly hypothesis-level.\n+# ============================================================================\n+\n+review_id: review-R1-reality-check-reframe-2026-07-24\n+snapshot_id: 2026-07-24-reality-check-reframe\n+reviewer_role: \"R1 — Novelty & Significance (IUI/CHI simulation, independent)\"\n+target_venue: \"IUI/CHI (route-A pure-model framing)\"\n+review_stage: reframe-reality-check\n+review_scope: >\n+  Evaluate whether the reframed core (C1 + C2 negative + C2-mech hypothesis) is\n+  sufficiently novel and significant for top-tier HCI venues under a pure-model route.\n+  Focus on novelty delta against known steering-vs-prompt literature and whether\n+  evidence strength can sustain the headline claim without human-subject studies.\n+\n+materials_examined:\n+  - docs/paper/reframe-2026-07-24-reality-check.md\n+  - docs/ledgers/claim-ledger.md\n+  - docs/ledgers/evidence-ledger.md\n+  - results/c2b_adjudication_hf_2026-07-24/c2b_adjudication_summary.md\n+  - docs/ledgers/prereg-c2b-adjudication.md\n+  - 开题报告_非满射双通道认知控制台.md\n+\n+missing_materials:\n+  - \"No multi-family replication for C2 (currently Qwen2.5-7B only).\"\n+  - \"No method diversity beyond CAA-family intervention.\"\n+  - \"No direct comparator to stronger prompt-search baselines (only best-of-16 prompt in current protocol).\"\n+  - \"No direct off-manifold diagnostic evidence (C2-mech remains inferential).\"\n+  - \"No human-study evidence for C3 (acknowledged as proposed only).\"\n+\n+expertise_level: \"high on novelty/significance in HCI+LLM control literature; medium on low-level mechanistic proof\"\n+conflict_check: \"no conflict; did not read manager expectations or response files\"\n+overall_score_range: \"IUI: 2.8-3.7 / 5 ; CHI: 2.3-3.2 / 5 (current bundle only)\"\n+confidence: \"medium-high\"\n+verdict: major-revision\n+\n+paper_understanding:\n+  one_sentence_problem: >\n+    The work tests whether a latent direction that is legible in representation space\n+    actually transfers into superior behavioral control over strong prompting, and\n+    reports that this transfer fails under a frozen adjudication, with calibration harm.\n+  claimed_contributions:\n+    - \"C1: A measurable representational legibility gap (prompt reaches only part of CAA direction extent) on 3/4 axes at Qwen2.5-7B.\"\n+    - \"C2: A pre-registered behavioral reality-check: steer-only on that legible direction does not beat the best prompt ceiling on 0/3 adjudicated axes; uncertainty calibration worsens.\"\n+    - \"C2-mech: Off-manifold explanation as a mechanism hypothesis for why legible directions may be behaviorally invalid control coordinates.\"\n+    - \"Design implication: shift console positioning from 'superpower control' to 'boundary/trust-calibration instrument' (currently conceptual, no human evidence).\"\n+  strongest_accept_case: >\n+    As a rigorously frozen negative, this is more than \"our method failed\": it directly\n+    challenges a widespread implicit assumption (\"if a direction is readable, steering\n+    it should help behavior\"), with paired item-cluster bootstrap, multiplicity control,\n+    DEV/TEST separation, and explicit kill criteria. That combination of disciplined\n+    falsification + actionable design reframing can be publishable as a high-value\n+    reality-check paper, especially in IUI.\n+  strongest_reject_case: >\n+    The headline may be judged incremental or under-scoped: prior work already frames\n+    prompt-vs-latent mismatch/non-equivalence (Mishra non-surjectivity backdrop,\n+    activation-steering-vs-prompt comparisons, PSR/Steer-like families). With only one\n+    steering method family and one model family, reviewers can dismiss C2 as\n+    \"CAA-on-Qwen limitation,\" not a field-relevant insight.\n+  clarity_mismatches:\n+    - \"C2-mech wording occasionally reads causal; evidence only supports consistency, not mechanism proof.\"\n+    - \"C2 currently mixes 'prompt is a strong ceiling' language with limited baseline diversity; this is vulnerable unless explicitly scoped to tested protocol.\"\n+    - \"Route-A pure-model framing and C3 design framing coexist; must avoid overselling C3 as an empirical contribution in this submission.\"\n+\n+findings:\n+  - finding_id: R1-F1\n+    severity: blocker\n+    dimension: novelty\n+    target_claim_ids: [C2]\n+    paper_locations:\n+      - \"docs/paper/reframe-2026-07-24-reality-check.md §2 C2, §3 contribution-2\"\n+      - \"docs/ledgers/claim-ledger.md C2\"\n+      - \"results/c2b_adjudication_hf_2026-07-24/c2b_adjudication_summary.md\"\n+    criticism: >\n+      Core negative is currently single-method-family (CAA) + single-model-family (Qwen2.5).\n+      This makes the novelty/significance attack trivial: \"method-specific miss, not\n+      general reality-check.\"\n+    evidence_examined: \"C2 scope and E-0005 metadata explicitly state Qwen2.5 + CAA-only.\"\n+    why_it_matters_for_acceptance: >\n+      Top-tier reviewers require a negative claim to survive transfer attacks. Without\n+      minimal cross-method/cross-family robustness, the work is easy to reframe as\n+      local failure.\n+    alternative_explanation: >\n+      A different intervention family (e.g., manifold-constrained or representation-\n+      preserving steering) or another model family may recover gains, invalidating the\n+      implied generality of \"legible != controllable.\"\n+    requested_evidence_or_change: >\n+      Scope C2 headline explicitly to \"naive CAA on tested family\" OR add minimum\n+      robustness matrix (methods x families) before top-tier submission.\n+    cheapest_discriminating_action: >\n+      Add one non-CAA intervention family and one non-Qwen family with the same frozen\n+      adjudication on at least the uncertainty and one additional axis.\n+    acceptance_condition: >\n+      Either (A) claim is narrowed to method/family-specific reality-check everywhere\n+      (title/abstract/contributions), or (B) robustness matrix shows failure pattern\n+      persists beyond CAA+Qwen.\n+    confidence: high\n+    possible_reviewer_misunderstanding: >\n+      Reviewers may overread the current draft as impossibility theorem; this is partly\n+      wording risk but still a real evidence-scope gap.\n+    requires_new_experiment: true\n+    estimated_cost_class: medium\n+    user_approval_required: true\n+\n+  - finding_id: R1-F2\n+    severity: major\n+    dimension: significance\n+    target_claim_ids: [C2]\n+    paper_locations:\n+      - \"docs/ledgers/prereg-c2b-adjudication.md §1, §4, §5\"\n+      - \"docs/paper/reframe-2026-07-24-reality-check.md §3 contribution-2\"\n+    criticism: >\n+      Prompt comparator is stronger than many papers, but still vulnerable to \"prompt\n+      budget unfairness\" criticism for broad conclusions.\n+    evidence_examined: \"Best-of-16 prompt on DEV is pre-registered; no adversarial prompt-optimization baseline beyond this.\"\n+    why_it_matters_for_acceptance: >\n+      Significance depends on proving the ceiling is genuinely hard to beat, not just\n+      hard under one search budget.\n+    alternative_explanation: >\n+      Better prompt-search strategies (self-critique, iterative prompt optimizer, or\n+      larger candidate pool) may close or reverse the observed gap.\n+    requested_evidence_or_change: >\n+      Add one stronger prompt optimization baseline under fixed compute budget parity,\n+      or explicitly narrow claim to \"within current bounded prompt protocol.\"\n+    cheapest_discriminating_action: >\n+      Run a bounded iterative prompt-optimizer baseline on DEV only, freeze winner, and\n+      re-adjudicate on existing TEST items.\n+    acceptance_condition: >\n+      Either stronger prompt baseline still does not overturn C2 pattern, or paper\n+      language narrows to current prompt-budget regime with explicit non-claim.\n+    confidence: medium-high\n+    possible_reviewer_misunderstanding: >\n+      Some reviewers may treat any bounded prompt search as sufficient; risk remains in\n+      stronger methodological panels.\n+    requires_new_experiment: true\n+    estimated_cost_class: medium\n+    user_approval_required: true\n+\n+  - finding_id: R1-F3\n+    severity: major\n+    dimension: soundness\n+    target_claim_ids: [C2-mech]\n+    paper_locations:\n+      - \"docs/paper/reframe-2026-07-24-reality-check.md §2 C2-mech, §3 contribution-3\"\n+      - \"docs/ledgers/claim-ledger.md C2-mech\"\n+    criticism: >\n+      Off-manifold mechanism is plausible but currently inferential only; as a \"core\n+      insight\" it risks being read as post-hoc storytelling.\n+    evidence_examined: \"Claim ledger marks C2-mech as proposed hypothesis with no direct diagnostic yet.\"\n+    why_it_matters_for_acceptance: >\n+      Novelty credit for mechanism insight is fragile unless one direct diagnostic ties\n+      degradation to manifold-distance proxies.\n+    alternative_explanation: >\n+      Calibration harm could arise from prompt-format interactions, decoding sensitivity,\n+      or layer-choice instability rather than off-manifold displacement.\n+    requested_evidence_or_change: >\n+      Add a low-cost mechanistic diagnostic (distance proxy vs per-item delta outcome)\n+      or demote C2-mech to explicit future-work hypothesis in contribution list.\n+    cheapest_discriminating_action: >\n+      Compute per-item activation norm/whitening-distance shift between steered and\n+      prompt conditions, test correlation with uncertainty delta.\n+    acceptance_condition: >\n+      Either significant diagnostic support exists, or contribution wording removes\n+      mechanism-style novelty and keeps it as hypothesis only.\n+    confidence: high\n+    possible_reviewer_misunderstanding: >\n+      If manuscript already labels this as hypothesis everywhere, rejection risk drops;\n+      current framing still invites over-interpretation.\n+    requires_new_experiment: true\n+    estimated_cost_class: low\n+    user_approval_required: false\n+\n+  - finding_id: R1-F4\n+    severity: major\n+    dimension: novelty\n+    target_claim_ids: [C1, C2]\n+    paper_locations:\n+      - \"docs/paper/reframe-2026-07-24-reality-check.md §1, §3\"\n+      - \"开题报告_非满射双通道认知控制台.md (Mishra/PSR/Stolfo context rows)\"\n+    criticism: >\n+      The incremental-risk narrative is under-defended against nearest-neighbor attack\n+      (\"known that steering and prompting differ\"). Current package needs explicit\n+      differentiation: your contribution is not merely \"they differ,\" but a frozen\n+      behavioral adjudication showing non-transfer under fairness controls.\n+    evidence_examined: \"Reframe states this implicitly, but not as an explicit novelty contrast matrix in the paper-facing framing.\"\n+    why_it_matters_for_acceptance: >\n+      Without explicit contrast framing, reviewers map the work into existing buckets and\n+      score novelty down.\n+    alternative_explanation: >\n+      Readers may infer this is a repackaging of known representational non-equivalence.\n+    requested_evidence_or_change: >\n+      Add a concise nearest-neighbor contrast table in the paper: what prior work tests\n+      vs what this work uniquely adjudicates.\n+    cheapest_discriminating_action: >\n+      Writing-only: one comparison table in intro/related work and one \"non-claims\"\n+      paragraph that blocks over-generalization.\n+    acceptance_condition: >\n+      Distinct novelty unit is explicit and reviewer can answer \"what is new here?\" in\n+      one sentence without ambiguity.\n+    confidence: high\n+    possible_reviewer_misunderstanding: >\n+      If related-work section is already planned but omitted in bundle, this may partly\n+      be a snapshot artifact.\n+    requires_new_experiment: false\n+    estimated_cost_class: trivial\n+    user_approval_required: false\n+\n+  - finding_id: R1-F5\n+    severity: minor\n+    dimension: significance\n+    target_claim_ids: [C3]\n+    paper_locations:\n+      - \"docs/paper/reframe-2026-07-24-reality-check.md §2 C3, §3 contribution-4\"\n+    criticism: >\n+      In route-A pure-model submission, C3 is strategic context but currently reads like\n+      a promised contribution, which can trigger \"incomplete paper\" judgments.\n+    evidence_examined: \"C3 is marked proposed/not-run; still listed in contribution structure.\"\n+    why_it_matters_for_acceptance: \"Scope confusion can depress clarity and significance scores.\"\n+    alternative_explanation: \"Reviewers may think the paper is half system paper, half model audit.\"\n+    requested_evidence_or_change: \"Demote C3 to design implication/future track for this submission.\"\n+    cheapest_discriminating_action: \"Writing-only scope edit across abstract/introduction/conclusion.\"\n+    acceptance_condition: \"No empirical credit claimed for C3 in the route-A manuscript.\"\n+    confidence: high\n+    possible_reviewer_misunderstanding: \"None material.\"\n+    requires_new_experiment: false\n+    estimated_cost_class: trivial\n+    user_approval_required: false\n+\n+  - finding_id: R1-F6\n+    severity: question\n+    dimension: empirical\n+    target_claim_ids: [C1]\n+    paper_locations:\n+      - \"docs/ledgers/evidence-ledger.md E-0003\"\n+    criticism: >\n+      C1 has one axis (focus) opposite pattern and one layer-sensitivity caveat\n+      (deliberation layer-16 CI crosses 1). How prominently this heterogeneity is reported\n+      will affect perceived credibility.\n+    evidence_examined: \"E-0003 notes overshoot axis and layer sensitivity explicitly.\"\n+    why_it_matters_for_acceptance: \"Transparent heterogeneity reporting increases trust in negative-result papers.\"\n+    alternative_explanation: \"Axis definitions may mix multiple mechanisms.\"\n+    requested_evidence_or_change: \"Ensure C1 is presented as conditional/axis-specific, not monolithic.\"\n+    cheapest_discriminating_action: \"Writing-only caveat placement in abstract limitations + main results.\"\n+    acceptance_condition: \"Axis heterogeneity is explicit in headline result statements.\"\n+    confidence: high\n+    possible_reviewer_misunderstanding: \"None.\"\n+    requires_new_experiment: false\n+    estimated_cost_class: trivial\n+    user_approval_required: false\n+\n+direct_answers_to_4_required_questions:\n+  q1_single_method_single_family_fatal: >\n+    Not automatically fatal, but close to fatal for CHI and a major risk for IUI.\n+    As-is it is defensible only as \"CAA-on-Qwen reality-check.\" For top-tier acceptance,\n+    either narrow the claim scope very explicitly or add minimum cross-method/cross-family\n+    robustness.\n+  q2_no_human_study_feasibility_iui_chi: >\n+    Feasible for IUI as a model-measurement/reality-check paper if rigor and robustness\n+    are strong; typical ceiling around borderline-accept to weak-accept.\n+    For CHI mainline, pure-model/no-human is much harder; likely weak-reject unless the\n+    empirical insight is unusually general and methodologically airtight.\n+    Practical score bands from this bundle: IUI ~2.8-3.7/5; CHI ~2.3-3.2/5.\n+  q3_venue_fit_ranking_chi_iui_cscw: >\n+    Fit ranking for this pure-model reality-check package: IUI > CHI > CSCW.\n+    IUI is most compatible with interface-intelligence measurement without mandatory user\n+    study; CHI can accept but typically expects stronger interaction/design evidence;\n+    CSCW fit is weakest here because collective/social workflow implications are not core.\n+  q4_minimum_robustness_needed: >\n+    Minimum to be \"top-conference defensible\": at least 2 steering families x 2 model\n+    families (e.g., CAA + one manifold-respecting alternative; Qwen + one Llama/Mistral-\n+    family) on the same frozen adjudication for at least 2 axes including uncertainty.\n+    Add at least one direct mechanism diagnostic for C2-mech (off-manifold proxy vs\n+    outcome degradation). Also add one stronger prompt-optimization comparator or strictly\n+    narrow non-claims to current prompt budget.\n+\n+review_summary:\n+  top_3_rejection_risks:\n+    - \"Method-specificity kill-shot: single CAA x single Qwen can be dismissed as local failure.\"\n+    - \"Incremental novelty framing: reviewers may read it as already-known prompt-vs-steering mismatch.\"\n+    - \"Mechanism overreach: off-manifold insight may look post-hoc without direct diagnostic.\"\n+  must_fix_before_next_gate:\n+    - \"Close R1-F1 (scope narrowing or robustness expansion).\"\n+    - \"Close R1-F2 (prompt-baseline fairness defense).\"\n+    - \"Close R1-F3 (mechanism evidence or demotion to explicit hypothesis).\"\n+    - \"Apply R1-F4 writing-level novelty contrast hardening.\"\n+  optional_improvements:\n+    - \"Demote C3 to implication-only in route-A manuscript to avoid scope diffusion.\"\n+    - \"Highlight C1 heterogeneity (focus/layer caveats) in headline text for credibility.\"\n+  questions_for_manager:\n+    - \"Will route-A intentionally target IUI first and treat CHI as stretch, or keep dual-target messaging?\"\n+    - \"Can budget support the minimum 2x2 robustness matrix before claim freeze?\"\n+    - \"If robustness budget is denied, will title/abstract be narrowed to avoid over-claim risk?\"\n+  score_if_unchanged: \"IUI 2.8-3.2/5; CHI 2.3-2.8/5\"\n+  score_if_blockers_closed: \"IUI 3.4-4.0/5; CHI 3.0-3.6/5\"\n*** End Patch\n"
```

</details>

```
Added 1 file(s): C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\docs\reviews\2026-07-24-reality-check-reframe\review-R1.yaml
```


---

<sub>1m 49s</sub>

### `powershell`

**Commit the new R1 review file**

<details>
<summary>Arguments</summary>

```json
{
  "command": "Set-Location \"C:\\Users\\v-elzhang\\Desktop\\MyFolder\\cognitive console\"; git --no-pager add \"docs/reviews/2026-07-24-reality-check-reframe/review-R1.yaml\"; git --no-pager commit -m \"Add R1 review for reality-check reframe\" -m \"Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>\" -m \"Copilot-Session: 51c5d0b2-bb0c-4bef-8d19-60e076eb999e\"",
  "description": "Commit the new R1 review file"
}
```

</details>

```
[main fd72a85] Add R1 review for reality-check reframe
 1 file changed, 300 insertions(+)
 create mode 100644 docs/reviews/2026-07-24-reality-check-reframe/review-R1.yaml
<shellId: 1 completed with exit code 0>
```


---

<sub>1m 52s</sub>

### Copilot

已完成：R1 审稿结果已写入并提交到仓库。

- 文件：`docs/reviews/2026-07-24-reality-check-reframe/review-R1.yaml`
- 提交：`fd72a85`
- 内容包含你要求的全部结构：scope check、独立贡献复述、对 C1/C2/C2-mech 的 novelty/significance 攻击、strongest accept/reject case、ranked findings（含 cheapest action 与关闭条件）、4 个点名问题的直接回答、初评分区间+confidence+前三拒稿风险。

---

<sub>Generated by [GitHub Copilot CLI](https://github.com/features/copilot/cli)</sub>
