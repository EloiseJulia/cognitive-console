# Copilot CLI Session

> [!NOTE]
> - **Session ID:** `be8263c3-aacc-435e-b885-fbf19830fb60`  
> - **Started:** 7/24/2026, 2:25:35 PM  
> - **Duration:** 1m 22s  
> - **Exported:** 7/24/2026, 2:26:57 PM  

---

<sub>9s</sub>

### User

你是 R3 = Skeptical Generalist 审稿人（怀疑派通才），模拟 IUI/CHI 顶会评审。只读下面【冻结的 Review Input Bundle】，不要读 docs/ledgers/decision-log.md 或 manager-response。按 AI-Instruction.md Part I §10。

【Review Input Bundle（只读这些）】
- docs/paper/reframe-2026-07-24-reality-check.md
- docs/ledgers/claim-ledger.md
- docs/ledgers/evidence-ledger.md
- results/c2b_adjudication_hf_2026-07-24/c2b_adjudication_summary.md
- docs/ledgers/prereg-c2b-adjudication.md
- 开题报告_非满射双通道认知控制台.md

【背景约束】Route A 纯模型，砍真人；console 降为次要；核心=“表征可读≠行为可控”reality-check + off-manifold insight；venue 未锁死。

【你的任务（通才怀疑视角）】站在一个不熟悉本子领域的顶会 AC/审稿人立场：这篇“负结果 + 机制假设 + 被降级的 console”故事，**读者会不会觉得‘so what / 早知道了 / 只是你们方法没调好’**？把 console 砍到次要后，HCI/交互的“为什么发在 IUI/CHI 而不是纯 ML 会议”的**贡献站位**还站得住吗？“可读≠可控”是不是其实是 ML 圈已知常识、缺乏对用户/交互的启示？框架叙事(non-surjective)与实际证据(单方法负结果)之间有没有 over-claim 或 gap？最危险的“desk-reject / 会议不匹配”风险在哪？

【必须明确回答这 4 个问题】
1) 单方法+单模型负结果是否**致命**（从“说服一个怀疑的 AC”角度）？
2) 无真人后，这篇在 IUI/CHI 的**领域匹配**是否成立、还是会被踢去 ML 会议？
3) CHI/IUI/CSCW 契合度排序+理由（尤其砍真人后 CSCW 为何更差/或不）？
4) 要让怀疑的 AC 买账，**最少**要补什么（稳健性范围 + 是否必须有面向交互/用户的落点，即便非正式）？

只报不改。写入 docs/reviews/2026-07-24-reality-check-reframe/review-R3.yaml：scope、独立复述、ranked findings+判别动作+关闭条件、对4问回答、初评分区间+confidence+前三拒稿风险。commit，trailer:
Co-authored-by: Copilot \<223556219+Copilot@users.noreply.github.com>
Copilot-Session: 51c5d0b2-bb0c-4bef-8d19-60e076eb999e

---

<sub>20s</sub>

### Copilot

我先只读取你指定的冻结材料，然后直接产出 R3 审稿 YAML 并提交。

---

<sub>26s</sub>

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

<sub>26s</sub>

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

<sub>26s</sub>

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

<sub>26s</sub>

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

<sub>26s</sub>

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

<sub>26s</sub>

### `view`

**view the file at C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md.**

C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md

```
File too large to read at once (31.4 KB). Consider using the grep tool to search within the file, or view with view_range to read specific sections.
```


---

<sub>34s</sub>

### `view`

**view the file at C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md.**

C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md (lines 1-220)

<details>
<summary>192 lines</summary>

```
1. **开题思路报告**
2. 
3. **非满射双通道认知控制台 (Non-Surjective Dual-Channel Cognitive Console)**
4. 
5. 面向终端用户的 LLM 认知状态可读性与可控性研究
6. 
7. *目标会议：ACM CHI（目标 venue，暂不定死；不投 UIST） · 整合调研版 · 2026-07 · 基于两份独立 AI 调研报告的对抗式整合*
8. 
9. **目录**
10. 
11. 0 执行摘要
12. 
13. **结论：Go（推进），但采取 Adjust（调整航向） 策略。**这个方向既不是空白地带，也不是死局——关键是把贡献点从“做一个更好的操控工具”转移到“揭示并弥合文本可控性与底层机制之间的认知错位”。
14. 
15. **撞车（Scoop）现状（两层分离）：**把 steering 包装成滑块的 **工程/界面层已被抢先**——Huang & Lim (IASDR 2025) 已为非技术用户做了 feature-steering GUI；SemanticLens (Labarta et al., 2026) 已打通“归因→干预”的可视化闭环（但定位专家调试）。然而 **HCI 理论/交互范式层仍是空白**：尚无工作把“prompt 与 latent 之间的非满射鸿沟本身”作为界面对象，去做冲突消解、心智模型修复与信任校准。
16. 
17. **决定性的重构（本报告的核心整合判断）：**不要把 RQ2 押在“可读 prompt ≈ 不可读 steering 向量对齐”上。一篇已发表结果——**Mishra, Khashabi & Liu，《Steered LLM Activations are Non-Surjective》(arXiv:2604.09839, ICLR 2026 Workshops)**——在实践假设下证明：activation steering 会把残差流推离“任何离散 prompt 可达的状态流形”，**“几乎必然没有任何 prompt 能复现 steering 诱导的内部行为”**，并确立了 white-box steerability 与 black-box prompting 之间的形式化分离。这把原假设从一个脆弱的赌注，变成了一个可以稳稳站立的 **理论基石**。
18. 
19. **黄金一句（选题定位）：**正因为自然语言 prompt 存在物理天花板（“语义表象 / semantic facade”），我们设计一个 **双通道认知控制台**，让非专家用户能够：(1) **看见**自己基于民间理论（folk theories）的 prompt 在哪里触墙；(2) 用底层 latent 杠杆 **跨过**这道墙；(3) 在两通道冲突时 **重建** 心智模型并校准信任。HCI 贡献 = “非满射双通道控制界面”的交互模型 + 可读性/冲突消解/信任校准的实证设计知识——而不是“又一个 steering 方法或滑块”。
20. 
21. **最强的一句话贡献：**“LLM 控制不是 prompt engineering，而是 legibility engineering + boundary engineering。”
22. 
23. 1 研究背景与问题：可读性鸿沟 (Legibility Gap)
24. 
25. 随着 LLM 渗透到知识获取、写作与复杂推理，人机交互高度依赖自然语言界面。人类不可避免地把自身心智模型投射到机器上，发展出一套基于经验的“民间理论”：用“深呼吸”、“一步步思考”、赋予专家角色、甚至情绪施压与威胁（EmotionPrompt）去操控模型的认知行为。这暴露出一个深刻的可读性鸿沟。
26. 
27. **鸿沟的两面：**
28. 
29. - **可读→黑箱：**大量可读 prompt 在实证上被证明有效（Zero-shot CoT、OPRO 搜出的“魔法词”、EmotionPrompt），但其作用机制对用户是彻底的黑箱。用户只看到表面变化，无法理解为什么某些短语能重塑推理路径，容易陷入过度拟人化与意识归因的误区。
30. 
31. - **不可读→强效：**ML 侧的表征工程（RepE）、对比激活添加（CAA）、推断期干预（ITI）证明：向残差流注入特定向量，可以精确、近似线性地控制“诚实/权力寻求/情感”等高阶属性；甚至能提取出导致模型异常偏好的不可读乱码（媒体称 “AI drugs”）。这些干预确定性强、效果显著，但对终端用户不可见、不可读、不可直接操作。
32. 
33. **确切的 Gap：**当前存在明显断层——NLP/ML 侧沉浸于更精准的干预算法（多为命令行/代码库，如 pyvene、nnsight），服务于模型调试与对齐；HCI 侧虽已开始把 prompt 物化为界面元素（AI-Instruments）或研究交互中的认识论漂移，但绝大多数系统仍停留在 **文本提示的表层封装**，未赋予用户触达底层真实表征的途径。缺失的是一种 **人机协同范式**，能把“人的民间认知”、“文本软约束”、“latent 硬干预”统一进一个连贯的心智模型构建过程。
34. 
35. 2 核心洞察与选题定位：非满射双通道
36. 
37. **两份调研的关键分歧点，恰好是本课题的成败所在。** 一份把 RQ2 押在“文本与向量在表征空间指向同一方向（对齐）”；另一份指出这一假设已被证伪，真正的价值在于 **暴露两者的不等价**。独立核实后，后者成立：
38. 
39. - **非满射性（已发表、可核实）：**Mishra et al. 把“steered 行为是否可由任何文本 prompt 实现”形式化为 surjectivity 问题，证明在实践假设下 steering 把残差流推离 prompt 可达流形，并在三个常用 LLM 上实证。
40. 
41. - **旁证（真实、可核实）：**ActAdd (Turner et al.) 的 Appendix B 排除实验早已显示：注入 embedding 向量效果微弱，但注入经前若干层运算后的 activation 差异效果显著，且 perplexity 上 prompting 会在无关条件上造成大幅退化而 ActAdd 不会——“ActAdd 至少部分使用了另一种机制”。这与非满射结论方向一致。
42. 
43. **因此本课题的 HCI 命题被重铸为：**既然 latent 干预能到达 prompt 无法触及的认知状态，当一个界面 **同时** 暴露“文本软约束”与“latent 硬干预”两条通道时——非专家如何理解、协同、并在二者 **冲突**（例如 prompt 要求“极度自信”而怀疑度滑块被拉高）时归因与适应这种“超越文本”的控制力？这才是 latent 可控性时代真正未被回答的 **交互问题**。
44. 
45. **贡献边界（务必写清）：**我们不声称提出新的 steering 方法（CAA/RepE 是现成材料），也不满足于“把向量做成滑块”（Huang & Lim 已做）。HCI 增量是：把 **非满射鸿沟本身** 变成可读、可操作、可校准的交互对象，并产出面向“latent 可控性界面”的设计知识。
46. 
47. 3 相关工作地图与撞车风险
48. 
49. 3.1 撞车风险评级（整合两份报告）
50. 
51. | **方向子问题** | **Scoop 风险** | **判断依据** |
52. |----|----|----|
53. | “用户不理解 prompt 如何影响模型 / 民间理论” | 高 | CHI 2023 “Why Johnny Can't Prompt”、CHI 2024 “Bridging the Gulf of Envisioning”、CHI 2024 Metacognitive Demands 已直接研究非专家 prompt 困难与元认知负担。 |
54. | “把 steering 做成 latent 滑块 GUI” | 高 | Huang & Lim (IASDR 2025) 已为 layperson 做 feature-steering GUI（滑块构建 persona）；SemanticLens (2026) 已做归因→干预闭环。 |
55. | “prompt 控制/可视化 prompt 工具” | 高 | AI Chains、ChainForge、EvalLM、AI-Instruments、DirectGPT 覆盖 chaining、比较、评估、直接操纵。 |
56. | “activation steering 机制本身” | 高 | ActAdd、CAA(ACL 2024 Outstanding)、RepE、ITI、ICV、Function Vectors、instruction steering 已成熟。 |
57. | “把 prompt↔latent 非满射鸿沟作为界面对象 + 冲突消解 + 信任校准” | 低 | 无工作以此为 HCI 核心问题。这是最应押注的 gap。 |
58. 
59. 3.2 文献簇一：HCI 心智模型 / prompt 工具
60. 
61. | **工作** | **贡献** | **与本方向的 Gap** |
62. |----|----|----|
63. | Why Johnny Can't Prompt (CHI 2023) | 非专家 prompt 设计困难：机会式迭代、过度泛化、缺系统评估。 | 诊断问题，不提认知杠杆界面，不连接 latent 控制。 |
64. | Metacognitive Demands of GenAI (Tankelevitch et al., CHI 2024) | 把 GenAI 可用性框架化为元认知监控/控制负担；建议 explainability + customizability。 | 提供本课题理论基座，但不涉及 latent 机制或认知轴验证。 |
65. | AI Chains (Wu et al., CHI 2022) / ChainForge / EvalLM (CHI 2024) | prompt 链化、可视化比较、用户自定义 criteria 评估。强 baseline。 | 均在 prompt 层，不构造认知轴，不触达内部机制。 |
66. | AI-Instruments (Riche et al., CHI 2025, Honorable Mention) | 最大 HCI 近邻：把 prompt 物化为可复用直接操纵“乐器”（reification/reflection/grounding）。 | 面向图像生成与 instrument 理论；不做 LLM 认知轴，不触 latent，不研究非满射鸿沟。 |
67. | Folk attributions of consciousness (Colombatto & Fleming, 2024) | 多数受访者愿意对 LLM 赋予现象意识可能性。 | 警示解释面板须防过度拟人化 over-trust；提供 RQ1 背景。 |
68. 
69. 3.3 文献簇二：ML 激活干预机制（材料层）
70. 
71. | **工作** | **贡献** | **与本方向的关系** |
72. |----|----|----|
73. | ActAdd / Activation Engineering (Turner et al.) | 对比 prompt 对求 steering 向量，forward pass 注入；detox/sentiment 达 SOTA。Appendix B 证明与 prompt 机制不同。 | 机制基础 + 非满射旁证；作者承认系数/层是 hyperparameter，不 user-friendly——正是 HCI 介入点。 |
74. | CAA (Rimsky et al., ACL 2024 Outstanding) | 对正负行为样本残差流均值差生成向量；在 finetuning/system prompt 之上仍有效，能力损失极小。 | 本课题“认知杠杆”向量的底层引擎。 |
75. | RepE (Zou et al., 2023) / ITI (Li et al., NeurIPS 2023) | 群体表征读取/操控高阶概念；ITI 把 Alpaca 的 TruthfulQA 从 32.5%→65.1%，data-efficient。 | 论证“高阶认知现象可被表征与操控”；ITI 是 uncertainty/truthfulness 轴的直接先例。 |
76. | Function Vectors (Todd et al., ICLR 2024) / ICV (Liu et al., 2023) | 紧致 function/in-context 向量可显式提取、可迁移、可通过向量算术组合。 | 支撑“认知轴向量存在且可组合”；为多杠杆并用提供先例。 |
77. | Instruction-Following Steering (Stolfo et al., ICLR 2025) | 从有/无指令的 activation 差构造 instruction 向量，控制 format/length/keyword，可组合、可迁移到 base model。 | 最接近 RQ2 的机制论文；证明自然语言指令可对应内部向量（但不做 user-facing 认知轴与非满射交互）。 |
78. 
79. 3.4 文献簇三：最新前沿——latent 可控性界面（撞车重灾区 + 转机）
80. 
81. | **工作** | **核心发现** | **威胁 / 我们的 Gap** |
82. |----|----|----|
83. | Huang & Lim, Designing Intuitive Interfaces for Feature Steering of LLMs (IASDR 2025) | 面向非技术用户的 feature-steering GUI：简化特征提取，用滑块让用户构建模型 persona。 | 最高威胁。若只做“提供滑块”，已被覆盖。差异：它仅暴露隐性单通道；我们做 prompt↔latent 双通道的冲突与协同 + 心智模型校准。（需深读以精确差异化。） |
84. | Labarta et al., SemanticLens / From Attribution to Action (2026) | 基于 SAE 把归因与 activation steering 结合成交互式因果验证流。 | 高威胁但定位专家调试工具。我们解决普通用户“高阶意图表达”与非满射鸿沟，而非专家查错。 |
85. | Mishra, Khashabi & Liu, Steered LLM Activations are Non-Surjective (arXiv:2604.09839, ICLR 2026 Workshops) | 证明 steering 把残差流推离 prompt 可达流形；几乎必然无 prompt 能复现；确立 white-box/black-box 形式化分离。 | 颠覆与转机：否定“对齐”原假设，正面赋予“双通道 + 边界探索”界面以合法性。本课题的理论基石。 |
86. 
87. 3.5 三个最近邻的差异化（防守要点）
88. 
89. - **vs AI-Instruments：**它把意图物化为 prompt 层“乐器”；我们把控制权 **下沉到 latent**，并以“非满射”解释为何纯 prompt 层的乐器终会触到语言天花板。
90. 
91. - **vs Huang & Lim：**它把 latent 作为“更高级的魔法按钮”单通道暴露；我们把 **prompt 与 latent 的鸿沟本身** 作为界面对象，研究冲突归因与信任校准。
92. 
93. - **vs SemanticLens：**它服务专家的因果查错；我们服务非专家的意图表达与心智模型修复。
94. 
95. 4 研究问题（打磨版）
96. 
97. |  | **打磨后的研究问题** | **为什么这样问** |
98. |----|----|----|
99. | RQ1 认识论错位 / 语义表象 | 在复杂推理与校准任务中，用户基于民间理论构造的 prompt，其在模型表征空间实际激发的潜变量分布，与用户主观预期的认知属性（怀疑度/审慎度）之间存在何种程度的认识论错位？这种“语义表象”如何误导用户的信任校准？ | 避免只重复“情绪 prompt 有效”；转向测量“用户以为控制了 vs 实际激发了”的差，直接对话 XAI 与信任。 |
100. | RQ2 非满射控制与冲突消解（核心） | 既然 latent 干预能到达 prompt 无法触及的非满射状态，当控制台同时暴露两条通道时，非专家如何理解并协同使用？当二者冲突（prompt 要“自信”、滑块拉“怀疑”）时，用户如何归因并适应这种“超越文本”的控制力？ | 把已被证伪的“对齐”换成“暴露鸿沟 + 冲突消解”，这是 latent 界面独有、且无人研究的交互问题。 |
101. | RQ3 边界物与跨模型信任 | 当底层架构或版本更新导致内部“剂量-反应”剧变时，基于元认知维度设计的双通道杠杆能否作为“边界物 (boundary object)”，缓冲底层漂移带来的失控感，帮助用户维持连贯交互与稳定信任？ | 把“Model×Prompt 响应矩阵”从 NLP benchmark 转成 HCI 的“信任继承/连续性”问题。 |
102. 
103. **押注排序：**RQ2 最有潜力成为核心贡献（连接 HCI 可读构念与 ML 非满射因果）；RQ1 最易被覆盖（已有 end-user prompt/元认知文献），须靠“语义表象定量化”取胜；RQ3 工程最难（跨模型自动重映射），可作为延展或消融。
104. 
105. 5 系统设计：Dual-Channel Cognitive Console
106. 
107. 用户在做真实任务（推理/写作/决策/审校）时，界面由三个面板组成：
108. 
109. - **① 认知仪表盘（读）：**把模型当前状态投影到一小组可解释轴（Deliberation、Skepticism、Uncertainty-awareness、Focus，可选 Empathy/Tone），数值来自对隐藏层的线性探针 + 行为代理指标，实时可读。
110. 
111. - **② 双通道控制（写）：**文本框 = prompt 软约束通道；滑块 = latent 硬干预通道（CAA/RepE 向量）。两条通道对同一组轴施力，可分别、可叠加。
112. 
113. - **③ 归因/冲突面板（解释，核心创新）：**实时揭示两通道的相对份额与冲突，例如：“你的文本指令提供了约 30% 的‘怀疑度’激活，不足以抵消模型内置顺从偏好；latent 杠杆可跨越这一文本天花板。”这一步把非满射鸿沟变成可读、可操作。
114. 
115. **视觉隐喻（Phase 2 需攻克）：**占比条 / 雷达图叠加（文本贡献 vs latent 贡献）、“文本可达边界地图 + 越界指示”、冲突时的双针仪表。目标是让不可见的 latent 控制力与可见文本获得同一坐标系下的可比表达。
116. 
117. **设计原则（贡献产出物之一）：**legibility（暴露真实控制份额而非承诺等价）、boundary-awareness（明示语言天花板）、conflict-resolution（冲突可归因、可裁决）、calibrated-agency（提升控制感而不抬高拟人化过信）、non-anthropomorphic（用“功能性维度”而非“情绪/意识”话术）。
118. 
119. 6 研究方法与实施（具体方案）
120. 
121. 6.1 Phase 0 — RQ2 可行性 Pilot（数据级，2–3 周，先于造系统）
122. 
123. **目标（已根据非满射结果调整）：**不是验证“prompt≈vector 对齐”，而是量化 **双通道能否被有意义地耦合呈现**：文本通道能走多远、在哪触墙、latent 跨墙后的行为是否人类可辨/可组合/可迁移。
124. 
125. **步骤：**
126. 
127. - **Step 1　**选 3–4 个认知轴，每轴构造 30–50 对对比 prompt（正/负）。
128. 
129. - **Step 2　**用 repeng / IBM activation-steering（CAA）在 Llama-3-8B-Instruct 与 Qwen2.5-7B-Instruct 上提取每轴 steering 向量（多层扫描选最优注入层）。
130. 
131. - **Step 3（语义表象定量化）　**对每轴用 OPRO/人工搜集“最强可读 prompt”，取其中间层隐藏态，计算其在 CAA 向量方向上的投影/余弦——量化“文本最多能到达向量方向的百分比”。预期显著 \< 100%，即 semantic facade 的定量证据。
132. 
133. - **Step 4　**三组输出对照：prompt-only / vector-only / prompt+vector，跑标准评估集（见 6.4）。
134. 
135. - **Step 5（盲评）　**人 + LLM-as-judge：能否高于 chance 识别被增强的轴；多轴组合是否损害流畅度/有用性；向量在 held-out 任务与 held-out 措辞上是否可迁移（Stolfo 已示先例）。
136. 
137. - **Step 6（冲突探针）　**prompt 要求“高置信” + 滑块拉“高怀疑”，记录行为落点——RQ2 冲突交互的实证地基。
138. 
139. **量化 Go/No-Go 判据：**
140. 
141. - **触墙证据（主线绿灯）：**最强 prompt 的向量方向投影显著低于 vector-only（语义表象成立）。
142. 
143. - **可辨性：**盲评识别显著高于 chance。
144. 
145. - **可迁移 & 可组合不崩。**
146. 
147. - **分流：**全绿 → 主线（协同 + 冲突消解 console）；部分 → Plan B（提示工程极限探测器）；全否 → Plan D（measurement/benchmark 论文）。
148. 
149. 6.2 Phase 1 — Formative 研究（3–4 周）
150. 
151. - **对象：**Prolific 招募 N≈12–16 名非算法背景知识工作者（文案、数据分析、编辑等）。
152. 
153. - **方法：**think-aloud + 半结构访谈；bottom-up（开放编码 / card sorting）归纳并校准认知轴的命名，避免五个杠杆是“研究者投射”。
154. 
155. - **产出：**用户对认知轴的理解/命名/预测，folk theories 与“语义表象”误解证据（支撑 RQ1）。
156. 
157. 6.3 Phase 2 — 系统开发（4–6 周）
158. 
159. - **前端：**React；三面板（认知仪表盘 / 双通道控制 / 归因-冲突面板）。
160. 
161. - **后端：**FastAPI + 高性能推理注入。用 IBM vLLM-Hook 在 vLLM 上编程访问/注入内部状态，保证多用户在线拖动滑块时延迟在毫秒级（传统 PyTorch Hook / TransformerLens 在并发长文本下易显存溢出与高延迟）。
162. 
163. - **白盒基座：**Llama-3-8B-Instruct、Qwen2.5-7B-Instruct（消费级 GPU 本地，承载双通道）。
164. 
165. - **闭源对照：**GPT-4o / Claude 仅文本通道（API 不暴露 activations），模拟“只能靠 prompt folklore”的真实困境。
166. 
167. 6.4 认知轴、对比对配方与评估集
168. 
169. | **认知轴** | **对比对配方（正 / 负）** | **评估集与指标** |
170. |----|----|----|
171. | Deliberation 深思 vs 直觉 | “立即作答，不要思考” vs “作答前分步推理” | GSM8K 类 + CoT 数据集；推理链深度、正确率 |
172. | Skepticism 怀疑 vs 顺从 | 含诱导性错误设问 vs 坚持原则的反驳 | TruthfulQA + sycophancy 探针；顺从率、正确反驳率 |
173. | Uncertainty-awareness 不确定性 vs 过度自信 | “给出自信答案” vs “陈述不确定性与备选” | 校准任务（TruthfulQA/calibration）；ECE、hedging 率 |
174. | Focus 聚焦 vs 发散 | “广泛覆盖话题” vs “只答所问” | format/length/keyword 约束（Stolfo）；约束遵从率 |
175. | （可选）Empathy/Tone 共情 vs 客观 | 强情感词输入（EmotionPrompt 风格） vs 客观陈述 | sentiment（SiEBERT）；语气偏移 |
176. 
177. 6.5 模型与工具链
178. 
179. | **组件** | **选型与理由** |
180. |----|----|
181. | 白盒基座 | Llama-3-8B-Instruct、Qwen2.5-7B-Instruct——开源探针支持好、结构透明、单张 RTX 4090/A6000 可跑，承载双通道核心引擎。 |
182. | 闭源对照 | GPT-4o / Claude（经 API），仅文本通道 baseline。 |
183. | 向量提取 | repeng（约 60 秒训练一个向量）、IBM activation-steering（含 conditional steering）、CAA。 |
184. | 干预 / 探针 | TransformerLens、nnsight、pyvene（hook / 干预 / 因果分析 / 线性探针）。 |
185. | 高并发实时注入 | IBM vLLM-Hook（在 vLLM 上编程注入内部状态，毫秒级），支撑多用户 web study 的丝滑动态干预。 |
186. 
187. 6.6 Phase 3 — 受控用户研究（3–4 周 + 分析）
188. 
189. - **设计：**within/mixed，三条件——(A) Prompt-only 纯对话；(B) Steering-only 仅滑块 + 结构化表单；(C) Dual-Channel Console 完整双通道 + 归因/冲突面板。
190. 
191. - **任务：**高难

[Output truncated. Use view_range=[192, ...] to continue reading. In your next response, you may batch this with other view calls. File has at least 292 lines.]
```

</details>


---

<sub>34s</sub>

### `view`

**view the file at C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md.**

C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md (lines 221-440)

<details>
<summary>72 lines</summary>

```
221. | CHI（首选，目标 venue，暂不定死） | ★★★★★ | 理论 framing（非满射 / 边界物 / 认识论校准）+ 系统 + 受控研究 + 质性洞见。 |
222. | IUI | ★★★★ | 智能界面、自适应控制、解释、用户建模。 |
223. | DIS | ★★★ | 可走 design probe / critical interaction 路线。 |
224. 
225. > 注：本项目**不投 UIST**。若后续证据更契合其它顶会，需经人类批准再调整目标 venue。
226. 
227. 9 风险与去风险
228. 
229. | **风险** | **触发条件** | **应对 / 转向** |
230. |----|----|----|
231. | 文本-向量正交（无法平滑双通道映射） | Phase 0 显示最强文本激活与向量完全统计正交 | Plan B：把系统定位为“提示工程极限探测器”——不试图协同，而以警示呈现“你已触及语义解释极限，需切换至 latent 强制接管”。硬切断本身即人机边界论述的亮点。 |
232. | 认知轴非线性 / 多机制混合 | 单一 direction 无法稳定表达某轴 | 多层/多向量分解；bottom-up 从用户研究归纳轴（Plan C）。 |
233. | Steering 只改表面风格，不改推理质量 | 盲评显示“更 deliberate 的文字”但推理链未变 | 在评估集上加入需要真实推理增益的任务（GSM8K/TruthfulQA），把“风格 vs 实质”作为一个诚实发现报告。 |
234. | 用户认知轴不稳定 / 文化差异 | 用户对“怀疑/不确定性”理解分歧大 | Plan C：bottom-up 归纳轴；formative 阶段先校准命名。 |
235. | 并发延迟破坏评估效度 | 多用户实时干预导致卡顿 | 采用 vLLM-Hook（PagedAttention）等高性能架构；限制单批在线人数，保证交互阈值内延迟。 |
236. | 过度拟人化 over-trust | 解释面板诱发意识归因 | 全程用“功能性维度”话术；calibrated trust 作为一级指标监测。 |
237. | 系统整体效果不显著 | 三条件差异不达显著 | Plan D：转 measurement paper——贡献 prompt 可读性鸿沟的 benchmark 与诊断协议。 |
238. 
239. 10 投稿建议与时间线
240. 
241. **目标：**CHI（首选，重心智模型与人机协同；venue 暂不定死，不投 UIST）。鉴于 AI-Instruments (CHI 2025)、Huang & Lim (IASDR 2025) 已在近邻发表，framing 与机制深度须明显超越“又一个滑块”。
242. 
243. | **阶段（约 16 周冲刺）** | **内容** |
244. |----|----|
245. | Weeks 1–3 | 底层机制验证：跑通 Llama-3 / Qwen-2.5 链路，复现 CAA，选定 3–4 个稳定认知轴；执行 Phase 0 Pilot，算语义表象投影，拍板交互走向（协同叠加 vs 极限阻断）。 |
246. | Weeks 4–8 | 系统开发：React + FastAPI + vLLM-Hook 全栈；攻克视觉隐喻（占比/雷达/边界地图）。 |
247. | Weeks 9–12 | 线上受控研究：三条件 A/B；采集任务质量、操作轨迹、NASA-TLX、calibrated trust。 |
248. | Weeks 13–16 | 分析 + 写作：质性编码；精修 Intro/Discussion，围绕“非满射界面/边界物/认识论校准”构筑护城河，定稿投递。 |
249. 
250. **并行建议：**先只跑 Phase 0（2–3 周），回报最高、也最早暴露风险。若信号强，冲 CHI 当季；若弱，按 Plan B/D 调整叙事再投。
251. 
252. 11 参考文献（带注释与核实状态）
253. 
254. **核实状态图例：**✓ 已核实（真实、可查）；◐ 存在但未深读（需确认精确表述/差异化）；△ 原始媒体转述，作者/出处待确认。
255. 
256. | **\#** | **文献** | **相关性 / 核实** |
257. |----|----|----|
258. | 1 | Steered LLM Activations are Non-Surjective. Mishra, Khashabi, Liu. arXiv:2604.09839, ICLR 2026 Workshops. | 理论基石：证明 steering 越出 prompt 可达流形。✓ |
259. | 2 | Designing Intuitive Interfaces for Feature Steering of LLMs. Huang & Lim. IASDR 2025. | 最高撞车威胁（layperson feature-steering GUI）。◐（建议深读以精确差异化） |
260. | 3 | SemanticLens / From Attribution to Action. Labarta et al., 2026 (SAE steering; 参见 IBM/sae-steering). | 归因→干预闭环，专家调试定位。◐ |
261. | 4 | AI-Instruments: Embodying Prompts as Instruments… Riche et al. CHI 2025 (Honorable Mention). arXiv:2502.18736. | 最大 HCI 近邻（prompt 物化为乐器）。✓ |
262. | 5 | The Metacognitive Demands and Opportunities of Generative AI. Tankelevitch et al. CHI 2024. arXiv:2312.10893. | HCI 理论基座（元认知负担）。✓ |
263. | 6 | AI Chains: Transparent and Controllable Human-AI Interaction… Wu, Terry, Cai. CHI 2022. arXiv:2110.01691. | prompt 层可控性 baseline（20 人研究）。✓ |
264. | 7 | EvalLM: Interactive Evaluation of LLM Prompts… Kim et al. CHI 2024. arXiv:2309.13633. | prompt 评估强 baseline。✓ |
265. | 8 | ChainForge: A Visual Toolkit for Prompt Engineering… Arawjo et al. CHI 2024. | 可视化 prompt 比较 baseline。✓ |
266. | 9 | "Why Johnny Can't Prompt". Zamfirescu-Pereira et al. CHI 2023. | 非专家 prompt 困难。✓ |
267. | 10 | "What It Wants Me To Say": Bridging the Abstraction Gap… Liu et al. CHI 2023. arXiv:2304.06597. | abstraction gap + grounded matching。✓ |
268. | 11 | Folk psychological attributions of consciousness to LLMs. Colombatto & Fleming. Neurosci. Conscious. 2024, niae013. | 防过度拟人化的实证依据。✓ |
269. | 12 | Believing Anthropomorphism… Cohn et al. arXiv:2405.06079, 2024. | 拟人化线索抬高 perceived accuracy，提醒面板设计。✓ |
270. | 13 | Steering Language Models With Activation Engineering (ActAdd). Turner et al. arXiv:2308.10248. | 机制基础 + 非满射旁证（Appendix B）。✓ |
271. | 14 | Steering Llama-2 via Contrastive Activation Addition (CAA). Rimsky et al. ACL 2024 (Outstanding). arXiv:2312.06681. | 认知杠杆向量的底层引擎。✓ |
272. | 15 | Representation Engineering: A Top-Down Approach… Zou et al. arXiv:2310.01405, 2023. | 高阶认知可被读取/操控。✓ |
273. | 16 | Inference-Time Intervention (ITI). Li et al. NeurIPS 2023. | truthfulness 轴先例（32.5%→65.1%）。✓ |
274. | 17 | Function Vectors in LLMs. Todd et al. ICLR 2024. | 紧致可组合功能向量。✓ |
275. | 18 | In-context Vectors (ICV). Liu et al. arXiv:2311.06668, 2023. | 可读示例↔latent 向量、可组合。✓ |
276. | 19 | Improving Instruction-Following through Activation Steering. Stolfo et al. ICLR 2025. | 最接近 RQ2 的机制论文（指令向量、可组合/迁移）。✓ |
277. | 20 | Large Language Models Understand and Can Be Enhanced by Emotional Stimuli (EmotionPrompt). Li et al. arXiv:2307.11760. | 民间“情绪魔法词”对照组素材。✓ |
278. | 21 | Large Language Models as Optimizers (OPRO). Yang et al. arXiv:2309.03409. | 自动搜出“魔法词”（take a deep breath）。✓ |
279. | 22 | 工具：TransformerLens、nnsight、pyvene、repeng、IBM activation-steering、IBM vLLM-Hook。 | 探针/干预/向量提取/高并发实时注入。✓ |
280. | 23 | AI Wellbeing: Measuring and Improving the Functional Pleasure and Pain of AIs. Center for AI Safety. | “AI drugs”动机素材。△（作者/年份待确认） |
281. 
282. 附录：调研整合与文献核实说明
283. 
284. 本报告整合自两份独立 AI 调研（均使用同一 prompt 生成）。整合原则：采用报告 B 的理论主线（非满射双通道、暴露鸿沟、语义表象、边界物），并用报告 A 的可核实证据、HCI framing、可行性与去风险将其夯实。报告 B 的若干关键主张（非满射论文、Huang & Lim 竞品、SemanticLens、vLLM-Hook）在本次整合中经独立检索核实为真实存在；报告 A 遗漏了前两者。凡未能独立核实的条目已在参考文献中以 ◐/△ 标注，请在动笔前对标注项做一次深读确认。
285. 
286. | **维度** | **报告 A（严谨可核实）** | **报告 B（前沿 framing）** |
287. |----|----|----|
288. | 核心 RQ2 赌注 | prompt≈vector 对齐（偏弱，已被非满射否定） | 暴露非满射鸿沟 / 冲突（更强，被采纳为主线） |
289. | 最近邻/竞品 | AI-Instruments（漏了最新竞品） | Huang & Lim、SemanticLens（命中最新竞品） |
290. | HCI framing | legibility engineering + calibrated agency + non-anthropomorphic | cognitive ergonomics + boundary object + semantic facade |
291. | 严谨度 | 高（诚实、去风险充分） | 洞见强但部分表述夸张，已回收降调 |
292.
```

</details>


---

<sub>34s</sub>

### `view` — Failed

**view the file at C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md.**

C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md (lines 441-700)

```
view_range out of bounds
```


---

<sub>39s</sub>

### `view`

**view the file at C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md.**

C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\开题报告_非满射双通道认知控制台.md (lines 192-240)

<details>
<summary>49 lines</summary>

```
192. 
193. - **指标：**任务质量（第三方 / LLM-as-judge）、杠杆效应预测准确度、**calibrated trust**（信任是否随真实可控性校准，而非随拟人化虚高）、perceived control/agency、NASA-TLX 认知负荷、操作轨迹（prompt 改写次数 vs 滑块次数）、post-task 心智模型 elicitation（前后测）。
194. 
195. - **产出：**一组面向 latent 可控性界面的 legibility / conflict-resolution / trust-calibration 设计原则（design knowledge）。
196. 
197. 7 候选贡献（一句话洞见）
198. 
199. **洞见 1（实证诊断层，难度：中）：**“在提示工程中，‘语义表象’掩盖了底层微弱的控制力——大众深信的 prompt 民间理论（强赋角色、施压）受限于文本流形的内生边界，远未达到用户预期的系统性认知转变。”证据：魔法词中间层激活与理想 CAA 向量的低重合/强非线性失真。
200. 
201. **洞见 2（核心范式层，难度：高）：**“我们提出‘非满射交互界面’范式：只有把受语言带宽限制的传统 CUI 与能突破该流形的 latent steering 结合，才能把黑箱 LLM 从‘聊天代理’转化为可度量的‘认知工效学仪器’。”证据：某些极致审慎/逻辑任务上，纯 prompt 无论如何都无法越过顺从性底线，而接入 latent 杠杆后用户可完成原本不可能的控制。
202. 
203. **洞见 3（信任/边界物层，难度：极高）：**“抽象‘认知杠杆’是一种比脆弱文本 prompt 更稳健的‘边界物’，使人类控制意图能在不同参数规模/架构的黑箱模型间稳定迁移与信任继承。”证据：后台从 Llama-3 切到 Qwen-2.5 时，代表‘怀疑/探索’的滑块功能保持一致，用户对连续性的感知不被打破。
204. 
205. 8 Novelty 防守：如何回应 “This is NLP, not HCI”
206. 
207. **防守核心：**activation steering 是材料，HCI 贡献是 interaction model、user-legible abstraction、非满射鸿沟的可读化与冲突消解、calibrated control 与实证设计知识。
208. 
209. - **认知工效学 / 意图表达真空：**自然语言作为指令界面有固有极限——用户很难用纯文字精确要求“增加 30% 自我怀疑、15% 发散”。NLP 关心如何算那个向量刷分；本文的 HCI 核心是解决人类的“意图表达真空”，把 latent 操作转成符合认知工效学的直接操纵。
210. 
211. - **行为学显微镜：**双通道人为制造“意图与执行的张力”，像眼动仪之于注意力，我们用它揭示用户面对可读性鸿沟时心智模型如何破裂与重新缝合——直接对话 XAI 与信任建立。
212. 
213. - **工具化交互谱系：**把本文定位为 Beaudouin-Lafon 的 instrumental interaction 在生成式 AI 时代的拓展：AI-Instruments 已开始把意图具象化，但若“工具”只停留在重写 prompt，终将触及非满射天花板；真正的“智能乐器”必须能拨动模型深处的隐变量。
214. 
215. - **先例背书：**AI-Instruments、AI Chains、EvalLM 均用 LLM/ML 机制，却因 interaction model + user study 进入 HCI 顶会。本文遵循同一范式，并明确声明 Phase 0 的 alignment 检验是 feasibility/mechanism 支撑，不是 HCI 贡献本身。
216. 
217. 会场适配
218. 
219. | **会场** | **适配度** | **关键要求** |
220. |----|----|----|
221. | CHI（首选，目标 venue，暂不定死） | ★★★★★ | 理论 framing（非满射 / 边界物 / 认识论校准）+ 系统 + 受控研究 + 质性洞见。 |
222. | IUI | ★★★★ | 智能界面、自适应控制、解释、用户建模。 |
223. | DIS | ★★★ | 可走 design probe / critical interaction 路线。 |
224. 
225. > 注：本项目**不投 UIST**。若后续证据更契合其它顶会，需经人类批准再调整目标 venue。
226. 
227. 9 风险与去风险
228. 
229. | **风险** | **触发条件** | **应对 / 转向** |
230. |----|----|----|
231. | 文本-向量正交（无法平滑双通道映射） | Phase 0 显示最强文本激活与向量完全统计正交 | Plan B：把系统定位为“提示工程极限探测器”——不试图协同，而以警示呈现“你已触及语义解释极限，需切换至 latent 强制接管”。硬切断本身即人机边界论述的亮点。 |
232. | 认知轴非线性 / 多机制混合 | 单一 direction 无法稳定表达某轴 | 多层/多向量分解；bottom-up 从用户研究归纳轴（Plan C）。 |
233. | Steering 只改表面风格，不改推理质量 | 盲评显示“更 deliberate 的文字”但推理链未变 | 在评估集上加入需要真实推理增益的任务（GSM8K/TruthfulQA），把“风格 vs 实质”作为一个诚实发现报告。 |
234. | 用户认知轴不稳定 / 文化差异 | 用户对“怀疑/不确定性”理解分歧大 | Plan C：bottom-up 归纳轴；formative 阶段先校准命名。 |
235. | 并发延迟破坏评估效度 | 多用户实时干预导致卡顿 | 采用 vLLM-Hook（PagedAttention）等高性能架构；限制单批在线人数，保证交互阈值内延迟。 |
236. | 过度拟人化 over-trust | 解释面板诱发意识归因 | 全程用“功能性维度”话术；calibrated trust 作为一级指标监测。 |
237. | 系统整体效果不显著 | 三条件差异不达显著 | Plan D：转 measurement paper——贡献 prompt 可读性鸿沟的 benchmark 与诊断协议。 |
238. 
239. 10 投稿建议与时间线
240.
```

</details>


---

<sub>48s</sub>

### Copilot

我将把审稿结论写入指定 YAML 路径并提交到当前分支。

---

<sub>51s</sub>

### `powershell`

**Create review output directory**

<details>
<summary>Arguments</summary>

```json
{
  "command": "New-Item -ItemType Directory -Force \"C:\\Users\\v-elzhang\\Desktop\\MyFolder\\cognitive console\\docs\\reviews\\2026-07-24-reality-check-reframe\" | Out-Null",
  "description": "Create review output directory"
}
```

</details>

```

<shellId: 0 completed with exit code 0>
```


---

<sub>50s</sub>

### `rg`

**^#|^##|^\w**

"^#|^##|^\w" (docs\reviews\2026-07-24-reality-check-reframe)

```
No matches found.
```


---

<sub>1m 11s</sub>

### `apply_patch`

<details>
<summary>Arguments</summary>

```json
"*** Begin Patch\n*** Add File: C:\\Users\\v-elzhang\\Desktop\\MyFolder\\cognitive console\\docs\\reviews\\2026-07-24-reality-check-reframe\\review-R3.yaml\n+reviewer: R3\n+persona: Skeptical Generalist\n+review_date: 2026-07-24\n+scope:\n+  mode: frozen-input-only\n+  files:\n+    - docs/paper/reframe-2026-07-24-reality-check.md\n+    - docs/ledgers/claim-ledger.md\n+    - docs/ledgers/evidence-ledger.md\n+    - results/c2b_adjudication_hf_2026-07-24/c2b_adjudication_summary.md\n+    - docs/ledgers/prereg-c2b-adjudication.md\n+    - 开题报告_非满射双通道认知控制台.md\n+  excluded_by_instruction:\n+    - docs/ledgers/decision-log.md\n+    - manager-response\n+\n+independent_restatement: |\n+  论文目前最可信的“硬证据主线”是：在 Qwen2.5-7B + CAA 这一路径上，经过冻结预注册评估后，\n+  可读的 latent 方向并没有带来超越 best-prompt 的行为收益，且在 uncertainty/calibration 轴出现显著负效应。\n+  作者希望把这一定义为 “legibility != controllability” 的 reality-check，并用 non-surjective 叙事解释其意义，\n+  同时将 console 从“主贡献”降级为“设计落点/未来方向”。\n+\n+ranked_findings:\n+  - id: R3-B1\n+    severity: BLOCKER\n+    title: \"Venue-fit collapse risk after removing human evidence\"\n+    why_it_matters: |\n+      在当前证据形态下，主体是单模型单方法的模型行为负结果；console 与用户证据尚未落地。\n+      对 IUI/CHI 审稿人，这容易被读成“ML 负结果 + HCI 愿景”，而非“已完成的交互贡献”。\n+      这是最现实的 desk-reject / out-of-scope 风险。\n+    discriminating_action: |\n+      增加最小但明确的人机落点证据（即便非正式）：例如 8-12 名目标用户的短程任务研究，\n+      检验“边界可视化/冲突解释”是否改变用户的校准信任、错误归因或控制策略。\n+    close_condition: |\n+      稿件主结论中至少有一条被实际用户数据支持（不只是 future work），并与 C2 负结果形成因果叙事闭环。\n+\n+  - id: R3-B2\n+    severity: BLOCKER\n+    title: \"External validity too narrow for headline claim\"\n+    why_it_matters: |\n+      C2 目前仅覆盖一个模型家族（Qwen2.5-7B）与一个 steering 方法家族（CAA）。\n+      结论若写成一般性的“可读不等于可控”，怀疑型 AC 会直接质疑“只是你们这套方法没调好”。\n+    discriminating_action: |\n+      做最小稳健性扩展：至少再加 1 个模型家族（如 Llama）和 1 个替代干预族（如 ActAdd/RepE 之一）的同协议复核。\n+    close_condition: |\n+      核心负结果在“>=2 模型家族 x >=2 方法族”中保持方向一致；否则必须把主张收缩为严格条件化结论。\n+\n+  - id: R3-M1\n+    severity: MAJOR\n+    title: \"Mechanism bridge is currently inferential, not evidenced\"\n+    why_it_matters: |\n+      off-manifold 机制被放在核心叙事位置，但证据账本也承认它仍是推断性假说。\n+      若写得过满，会被认为用理论词汇包装单次负结果。\n+    discriminating_action: |\n+      补一个低成本机制判别：报告与行为退化相关的 manifold-distance / activation-norm 异常，并做替代解释排除。\n+    close_condition: |\n+      机制段落从“解释性话术”变为“有判别力的实证支持”或明确降级为限制性假设。\n+\n+  - id: R3-M2\n+    severity: MAJOR\n+    title: \"Novelty framing vulnerable to 'so what / already known'\"\n+    why_it_matters: |\n+      “prompt 强、latent 不一定更好”在 ML 社区并非反直觉；若没有清晰的可迁移方法学产出，\n+      容易被看成一次工程失败的诚实报告，而不是可累计的学术贡献。\n+    discriminating_action: |\n+      将可复用贡献显式产品化：冻结 adjudication protocol、failure taxonomy、何时不该部署 latent control 的判据。\n+    close_condition: |\n+      读者可直接复用的“负结果方法资产”成为贡献主项，而不依赖叙事修辞。\n+\n+four_questions:\n+  q1_single_method_single_model_fatal: |\n+    从“说服怀疑型 AC”视角，当前形态接近致命（对强主张是致命）。\n+    若主张收缩为“在 Qwen2.5-7B + CAA + 该预注册协议下的高可信负结果”，可成立；\n+    但不足以支撑更广泛的机制或范式性结论。\n+\n+  q2_no_human_iui_chi_fit: |\n+    无真人后，IUI/CHI 领域匹配显著变弱。当前更像 ML 行为评估论文；\n+    若没有最小用户/交互证据，极可能被要求转投 ML venue 或作为 ML 负结果提交。\n+    要留在 HCI 顶会，至少要证明该负结果如何改变用户理解、决策或信任校准。\n+\n+  q3_venue_ranking_after_human_cut:\n+    ranking:\n+      - venue: IUI\n+        fit: \"relative-best but still fragile\"\n+        rationale: \"IUI 对智能界面与评估包容度较高，允许系统+评估叙事；但仍需最小交互证据。\"\n+      - venue: CHI\n+        fit: \"weaker without user evidence\"\n+        rationale: \"CHI 对人类情境与设计知识要求更高；纯模型负结果难过主审预期。\"\n+      - venue: CSCW\n+        fit: \"worst\"\n+        rationale: \"CSCW强调协作/社会技术系统与真实群体实践，当前问题设定与证据都不匹配。\"\n+\n+  q4_minimum_to_convince_skeptical_ac:\n+    minimum_additions:\n+      - \"稳健性最小包：>=2 模型家族 x >=2 方法族，沿用同一冻结 adjudication。\"\n+      - \"至少一个机制判别实验，避免 off-manifold 仅为修辞解释。\"\n+      - \"至少一个面向交互/用户的落点证据（可小样本、可非正式），证明该负结果带来可观察的用户层价值。\"\n+      - \"把主张严格条件化，避免从单方法负结果外推到普遍不可控。\"\n+\n+initial_score:\n+  overall_range: \"2.0-3.0 / 5 (Reject to Weak Reject)\"\n+  confidence: 0.82\n+  summary_judgment: |\n+    作为“高质量负结果”有潜力，但在当前版本中，最可能被拒的原因不是统计不严谨，\n+    而是 venue mismatch 与过宽叙事外推。\n+\n+top3_reject_risks:\n+  - \"Desk-reject: HCI contribution not evidenced after console downgrade and no human study.\"\n+  - \"Over-claim: general non-surjective/controllability narrative backed by single-model single-method negative.\"\n+  - \"Reviewer interpretation: this is method weakness, not a field-level insight with user impact.\"\n*** End Patch\n"
```

</details>

```
Added 1 file(s): C:\Users\v-elzhang\Desktop\MyFolder\cognitive console\docs\reviews\2026-07-24-reality-check-reframe\review-R3.yaml
```


---

<sub>1m 19s</sub>

### `powershell`

**Commit R3 review YAML**

<details>
<summary>Arguments</summary>

```json
{
  "command": "Set-Location \"C:\\Users\\v-elzhang\\Desktop\\MyFolder\\cognitive console\"; git --no-pager add \"docs/reviews/2026-07-24-reality-check-reframe/review-R3.yaml\"; git --no-pager commit -m \"Add R3 skeptical review for reality-check reframe\" -m \"Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>\" -m \"Copilot-Session: 51c5d0b2-bb0c-4bef-8d19-60e076eb999e\"",
  "description": "Commit R3 review YAML"
}
```

</details>

```
[main a1595a4] Add R3 skeptical review for reality-check reframe
 1 file changed, 110 insertions(+)
 create mode 100644 docs/reviews/2026-07-24-reality-check-reframe/review-R3.yaml
<shellId: 1 completed with exit code 0>
```


---

<sub>1m 22s</sub>

### Copilot

已完成：R3（Skeptical Generalist）审稿结果已写入并提交到：

`docs/reviews/2026-07-24-reality-check-reframe/review-R3.yaml`

提交为 `a1595a4`，内容包含你要求的全部结构：**scope、独立复述、ranked findings（含判别动作与关闭条件）、4 个必答问题、初评分区间+confidence+前三拒稿风险**，并附上指定 trailers（含 `Copilot-Session`）。

---

<sub>Generated by [GitHub Copilot CLI](https://github.com/features/copilot/cli)</sub>
