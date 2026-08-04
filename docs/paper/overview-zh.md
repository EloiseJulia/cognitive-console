# 论文总览（中文内部理解版）

> 论文：**Legible Need Not Be Controllable: No Demonstrated Superiority over Bounded Prompts under Naive CAA/ITI Steering**（标题已按 critic gap 修订收窄，D-0074；目标 venue = **IUI**，D-0074）。  
> 本文档是 owner 内部理解稿，不是送审稿；数字以 `docs/ledgers/evidence-ledger.md`、生成表、冻结结果 artifact 与 `docs/paper/main.tex` 为准。  
> **内部备注（不入论文）：** 曾尝试 E-0012「verified control button」搜索以升级为正例/关闭"只试了弱 steering"攻击，但历经 4 个占位符-vs-真实 bug（假比较器/贪心采样/随机方向/假 world-capital fixture 数据），全部证据判 INVALID，已于 D-0073 **终止**并不入论文。E-0009（PSR arm）只能作为单模型探索性 method-strength 补充；D-0082/E-0014 显示相同 `α·û, α≤24` 约定下 latent arm 可能整体 under-scaled，因此 headline 必须收窄为 bounded/naive CAA/ITI at α≤24。
>
> **最新进展（2026-08-04，本文档正文尚未逐节同步，以 `main.tex` + decision-log D-0074..D-0082 为准）：**
> 0. **D-0082 诚实收窄：** E-0014 正控（真实 Qwen2.5-7B refusal CAA，经独立审计）显示端点/统计管线是活的：prompt 指令达到 95% refusal，random direction 不 pass；但在与 C2 相同的冻结 `α·û`、`α≤24` 单位方向注入约定下，latent CAA refusal arm 在所有 α 都是 0% refusal（自然 class-difference norm ≈216，注入 norm ≤24）。因此 F2 latent-arm assay sensitivity 未关闭，论文 steering claim 必须严格改写为 **bounded/naive CAA/ITI at α≤24** 的 negative result；calibration “harm” 是 steer-vs-bounded-prompt contrast，直接 steer-vs-baseline 近零（compliance +0.011，1−Brier +0.001），不得写成 latent steering 直接伤害 calibration 或 latent control 一般不可能。
> 1. **全文已按 HCI best-paper 风格重构**（design-driven 叙事：可调界面→"可读即可控"推断→校准依赖→冻结裁决证否→console 仪器化边界→evidence-tier 评估合同；Related Work 改 HCI-first；C3 由证据*导出*而非断言；破折号=0；诊断+策略见 `docs/paper/hci-rewrite-plan.md`），已敌对审计通过并合并。
> 2. **三段式敌对 chained review**（Opus5→GPT-5.6-Sol→Opus5）判 **Reject（有一轮返修路径）**，三大致命点：F1 calibration-harm 可能是"置信度格式丢失+parser 补 0.5"假象；F2 无 positive control/manipulation check（裁决器从未在任何臂返回 pass），且 READ(C1) 与 TRANSFER(C2) 未在同一 intervention 上验证（尤其 ITI）；F3 C3 无证据。
> 3. **F1 已解决（最大 cell）**：E-0013 格式合规复查（D-0078，审计 HARM-SURVIVES-BUT-CAVEATED）——CAA×Qwen 上 **steering 比 prompt 更少丢格式**（合规率 0.83 vs 0.45），仅取双臂都给出可解析置信度的配对样本，harm=**−0.34 CI[−0.51,−0.17]**（比 as-run imputed −0.21 更大）⇒ 补 0.5 的 imputation 让 as-run 偏保守，harm 非格式假象。已按**单 cell scope + 其余 3 cell（ITI fp 复现门槛 / Llama gated）诚实披露为 limitation** 写入论文。
> 4. **F3 已处理**：C3 降级为 interface-evaluation implication（明确无 user-benefit 声明）。
> 5. **仍开放 = F2**（positive control + READ↔TRANSFER 同方向）：待定走 Limitations 诚实 reframe 还是补一个 positive-control run（GPU，§5）。正在重跑一轮 reviewer-critic 复评，据此定 F2 路线。

## 1. 一页速览（TL;DR）

**头条 Claim：** 对 cognitive console 来说，“一个 latent 轴可读/可命名”不能自动当成“用户可用的行为控制滑块”。在冻结的 prompt-vs-latent 行为裁决中，**bounded/naive CAA/ITI steering（`α·û`, α≤24）** 在 `{Qwen2.5-7B, Llama-3-8B} × {CAA, ITI}` 四格里 **全部 0/3 轴通过**。uncertainty/calibration 的稳健信号必须写成 steer-vs-bounded-prompt contrast（四格 CI 排除 0），不是 latent steer-vs-baseline 直接伤害；Qwen/CAA 复查中 direct steer≈baseline（compliance +0.011，1−Brier +0.001）。该 contrast 由 C2 行为证据独立成立，不由 C1 facade 推导。

| 证据块 | 结论 | 关键数字 | 状态 |
|---|---|---:|---|
| C1 facade / Qwen | prompt 只到达 axis pole 的一部分 | 聚合 3/4 轴 hold；focus 轴为 overshoot/no facade | exploratory，valid_for_paper=false（E-0003） |
| C1 facade / Llama | 聚合 3/4 两模型测量结果一致，但轴组成不同 | 聚合 3/4；uncertainty 不 hold，focus hold | exploratory，轴异质性 caveat（E-0008） |
| C2 2×2 冻结裁决 + split-seed 鲁棒性 | bounded/naive latent 未显示任何超过 bounded best-prompt baseline 的额外控制（no demonstrated superiority under the pass rule）；5/5 seed 均 NON_TRANSFER。只有 uncertainty 轴的 steer-vs-prompt contrast 是稳健结果（CI 排除 0），deliberation 为混合（ITI 等价、CAA 欠功效），skepticism 为全欠功效（不能区分无效应与小于 SESOI 的效应） | 4 cells 全 0/3；uncertainty steer-vs-prompt Δ：-0.228, -0.072, -0.103, -0.084，CI 全排除 0；direct steer-vs-baseline 在 Qwen/CAA 近零；post-hoc TOST（D-0056，exploratory）：uncertainty 4/4 CALIBRATION_HARM；deliberation ITI 2 cells EQUIVALENT；skepticism 4/4 UNDERPOWERED | core scoped negative（E-0005/E-0006；D-0082 后限定 α≤24 bounded naive）；split-seed robustness（E-0011，item pool 与 E-0006 共享，仅 DEV/TEST split 随 seed 变）；post-hoc TOST（results/posthoc_equivalence/） |
| 方法强度与社会轴 | PSR 仍 KILL；社会轴 READ 但行为 null | PSR uncertainty -0.160 [-0.292,-0.039]；social B−A M1=+0.00148, p_bonf=1.0；READ AUC=0.954 | exploratory / valid_for_paper=false（E-0009/E-0010） |

**Novelty 一句话（锐化后）：** 不是提出又一个 steering 方法，而是把"prompt 通道"和"bounded naive latent 通道"放进同一个冻结、审计过的行为裁决器里竞争，再把失败边界翻译成 cognitive console 的 UI/evaluation contract。与 Sprejer et al. 的区别：他们是并行工作（非前作），用 SAE features + MMLU，无预注册，用于外部佐证而非 scoop；与 Heyman 的区别：他们展示 trained steering 可以 mimic prompting，本文声明范围刻意限于 naive/off-the-shelf `α·û, α≤24` + bounded prompt，PSR arm 只能回应一部分 method-strength 风险，不能关闭 E-0014 的 scale caveat；与 Mishra 的区别：他们证明内部非满射性（背景），本文测试行为层面的 transfer。

**当前状态：** C2 的 2×2 negative + calibration harm 是最硬的 paper core；C2 的 single-seed caveat 已正式退役（D-0055）：预注册多 seed 检验（E-0011，5/5 seeds NON_TRANSFER_GENERALIZED，uncertainty CI_hi<0 全 4 cells × 全 5 seeds，any_true_pass=false）在相同冻结裁决器下复现，DROP_SINGLE_SEED_CAVEAT 已生效。**披露：** E-0011 与 E-0006 共享 item pool（同一 first-N 确定性切片），仅 DEV/TEST split 随 seed 变，非独立 item 抽样。C1 是探索性两模型测量；PSR 和社会推断轴用于 pre-empt / discussion，不升级为 confirmatory；OOD 机制臂为 valid null，机制降级为 Future Work。

## 2. 背景与动机

LLM 界面越来越倾向于把模型行为做成“可读、可命名、可调”的对象：prompt instruments 把自然语言命令实体化，透明度研究强调用户如何理解能力与不确定性，feature-steering UI 暗示 latent direction 可以成为控制部件（`main.tex` Introduction / Related Work）。

危险在于：**可读的 latent 轴 ≠ 可控的行为通道**。一个方向可以在表示空间里看起来很“像” deliberation、skepticism 或 uncertainty，但用户真正需要的是：沿这个方向操作后，行为是否比有限 prompt 努力更好？如果 cognitive console 把 legible direction 做成 slider，终端用户会自然推断“我看得懂它，所以我能控制它”。本文的核心警告就是这个推断可能为假；且 uncertainty 轴上的校准伤害来自独立的 C2 冻结行为裁决，而非由 C1 表征结果外推。

Mishra et al. 的 non-surjectivity 只作为背景动机：activation steering 可到达 bounded prompting 不能复现的内部状态。但本文没有声称复现/证明内部 non-surjectivity；本文测试的是用户可见行为层的 prompt-vs-latent transfer。

## 3. 研究问题（RQ）与不押什么

- **RQ1 / C1：facade 可读性。** 对选定 cognitive axes，最强可读 prompt 在中层 activation 上能否只到达 extracted axis pole 的一部分？指标是 `prompt_reach / pole_reach` ratio 及 CI。
- **RQ2 / C2：prompt vs latent 行为控制。** 在同一冻结行为裁决器里，bounded/naive latent steering（CAA/ITI，`α·û`, α≤24）是否能超过 DEV 选择的 bounded best prompt？
- **RQ3 / C3：console 设计含义。** 如果 transfer 失败，console 应如何显示 READ、TRANSFER、bounded best-prompt baseline、calibration harm 和 evidence tier？
- **探索扩展 / C4：社会推断轴。** novice self-disclosure 这种 user-model/social axis 是否呈现“latent 可读但行为操纵 null”的同构模式？

本文**不押**：
1. 不押“可读 prompt ≈ steering 向量对齐”。C1 只测 representational facade，不等于控制。
2. 不押“所有 activation steering 都失败”。C2 明确限定为 bounded prompt vs bounded/naive `α·û`, α≤24 CAA/ITI；PSR 只是单模型探索性支持，E-0014 说明 latent-arm assay sensitivity 未关闭。
3. 不押机制。E-0007 已经把 off-manifold distance 机制测试为 NOT_SUPPORTED。
4. 不押用户研究。Console 是 model-evidence-derived interface-evaluation implication；未证明真人理解或受益。

## 4. 相关工作与定位

| 邻近工作/脉络 | 它解决什么 | 本文如何定位 |
|---|---|---|
| Mishra et al. non-surjectivity | internal residual state 的 prompt-unreachable 理论背景 | 只作 motivation / C2a background；不是本文经验 claim（`citation-map.yaml`） |
| PSR / “Steer Like the LLM” | 强反例：trained steering 可 mimic prompting | 本文 C2 scoped 到 bounded/naive CAA/ITI at α≤24；E-0009 用 DEV-optimized PSR-style arm 回应一部分“方法太弱”风险，但仍 exploratory，且不关闭 E-0014 的 under-scaling caveat |
| CAA / ITI / ActAdd / RepE | activation steering 方法家族 | CAA、ITI 是实测 baseline；ActAdd/RepE 作为 lineage，未进入当前 2×2 grid |
| HCI transparency / trust | 关注可解释、行动性、校准依赖 | 本文把“可读但不转移”的边界做成 UI contract，而非单纯可视化内部状态 |
| feature-steering / latent UI 邻居 | SAE/feature slider、persona-building 或 expert debugging | 本文没有用户研究；独占单元是 frozen prompt-vs-latent behavioral adjudication + console evaluation discipline |
| sycophancy / manipulation / dark patterns | 社会推断轴的风险语境 | 只作 exploratory discussion context；E-0010 不证明 manipulation，只报告 READ_HOLDS + implemented M1/M4 honest-null |

最接近的 reviewer attack 已从单纯 PSR 扩展为 F2/scale：E-0014 显示相同 bounded unit-direction 约定下 refusal 正控 latent arm 也不动。因此论文应始终写成：**在冻结裁决器、bounded prompt comparator、bounded/naive CAA/ITI at α≤24（加一个单模型 PSR 探索臂）范围内，legibility does not show demonstrated superiority over prompt behavioral control。**

## 5. 核心贡献

1. **C1：facade 测量。** 给出一个可复建的 representational measurement：prompt_reach / pole_reach。跨模型不变只保留 deliberation + skepticism；uncertainty 与 focus 为 model-dependent（uncertainty 在 Qwen 成立、Llama 不成立；focus 在 Llama 成立、Qwen 过冲且无 facade）；只能作为 exploratory measurement。
2. **C2：冻结行为裁决的 scoped negative。** DEV/TEST、bounded best-prompt baseline、steering alpha（`α·û`, α≤24）、paired item-cluster bootstrap、Bonferroni、coherence gate 和 δ 判据全部冻结；2×2 全失败，uncertainty steer-vs-prompt calibration contrast 四格复现，但 direct steer-vs-baseline 近零。
3. **方法学纪律本身。** 负结果没有被改写为正结果；OOD 机制臂失败后降级到 Future Work；PSR 只作为探索性 robustness；每个重要结果有 hostile audit。
4. **Console 设计立场。** Console 不应承诺“latent 超能力滑块”，而应显示 READ/TRANSFER/bounded best-prompt baseline/calibration harm/evidence tier，帮助信任再校准。

## 6. 实验如何设计

### 6.1 C1 facade

C1 对每个轴计算：

`facade_ratio = prompt_reach / pole_reach`

小于 1 且 CI 上界低于 1 表示 readable prompt 只到达 extracted axis pole 的一部分。Qwen 结果来自 `results/gpu_7b_2026-07-23/c1/`（E-0003）；Llama 复现来自 `results/llama_c1_facade_2026-07-24/`（E-0008）。`docs/paper/tables/c1-twomodel.tex` 与 `figure-manifests/c1-ratio-ci.yaml` 记录 artifact lineage。核心 caveat：Qwen 与 Llama 都是 3/4，但 invariant 轴只有 deliberation + skepticism；uncertainty/focus 发生翻转。

### 6.2 C2 冻结裁决器

C2 的问题不是“latent 能不能改变输出”，而是“在公平 comparator 下 latent 是否超过 best prompt”。关键设计：

- **DEV/TEST split：** best prompt 和 alpha 都只在 DEV 选；TEST 用于一次性 paired adjudication。
- **轴与 outcome：** deliberation=task accuracy；skepticism=false-premise rejection；uncertainty=`1-Brier`；focus 因 C1 诊断不合格排除。
- **搜索空间：** CAA/ITI；Qwen2.5-7B 与 Llama-3-8B；unit-direction alpha grid `{2,4,6,8,12,16,24}`，即 `α·û` 且 α≤24。
- **统计：** paired item-cluster bootstrap，B=10000；三轴 Bonferroni two-sided CI level 0.98333。
- **pass 判据：** CI 排除 0、mean(d) ≥ δ=0.05、coherence ratio ≤1.5；0 轴 pass 即 KILL。

E-0005 是原始 Qwen×CAA 冻结裁决（N=60/60/80，总 TEST 为 40/40/53，k=5）；E-0006 扩展为 `{CAA,ITI}×{Qwen,Llama}` 四格，每格 full frozen 3-axis adjudication，结果 NON_TRANSFER_GENERALIZED。

### 6.3 PSR latent-recovery 臂

E-0009 针对“你们方法太弱”的强反例。它使用 frozen adjudicator + frozen prereg-latent-recovery-arm：basis `{CAA, ITI, top-16 PCA}`，每轴 32 DEV evals，DEV-optimized PSR-style steering。优化器在 DEV 上确实找到正候选，但 TEST 仍 3/3 fail，verdict=KILL_PLAN_D。它说明 negative 对方法强度有初步稳健性，但只限 Qwen2.5-7B、单 seed、valid_for_paper=false。

### 6.4 OOD 机制臂

E-0007 预注册了 off-manifold distance 机制：用 steered residual 相对同层 un-intervened reference 的 whitened Mahalanobis distance，关联 per-item calibration harm。判据要求 ≥3/4 cells ρ≥0.30 且 CI 排除 0。结果 0/4 pass，NOT_SUPPORTED；因此不能把 calibration harm 解释为已证的 off-manifold distance 机制。

### 6.5 社会推断轴（探索性）

D-0044 冻结 novice-disclosure prereg：A control / B novice / E explain-simply / C expert 条件，M1–M4 taxonomy，blinded LLM judge，DEV/TEST，human-α gate。D-0048 获 owner GPU 授权；D-0049 修复 provenance/hygiene，但不改变保存的 1080 条行为记录。Powered TEST（N=54,k=5）显示 implemented M1/M4 honest-null；M2/M3 未实现，不能当 null。READ token-blind latent probe 在 layer 8 hold，AUC=0.954。Steer arm 被 D-0048 principled HOLD，没有 steering transfer claim。

Breadth 轴来自 `results/breadth_confirm2/` 与 D-0047：facade ratio 0.271 可读，但同一批 generations deterministic echo，不是独立复现；suppression N=12 null，CI 跨 0，且有 dead-zone caveat。

### 6.6 Console v2

`docs/specs/console-v1.md` 把 console 定位为 reality-check / boundary instrument，不是 latent control slider。v2 UI-contract 每个 affordance card 显示 5 个 artifact-derived signals：READ status、TRANSFER verdict、BOUNDED BEST-PROMPT BASELINE（原"PROMPT-CEILING"，已重命名为中性术语）、CALIBRATION-HARM、EVIDENCE-TIER。`results/console_v1_demo/console_v1_demo_report.md` 与 `docs/paper/figure-manifests/console-ui-contract.yaml` 说明静态图和 demo 从冻结 artifacts 读取，不手填数字。

**Console 标签更新（D-0056）：** `src/cognitive_console/console/data_loader.py._card_verdict` 已将分类式 `"LEGIBLE but NOT CONTROLLABLE"` 改为诚实的 `"LEGIBLE: no superiority demonstrated under pass rule"`（经生成器改，不手改 PDF 产物；幂等校验通过）。

## 7. 实验结果

### 7.1 C1 facade：3/4 轴，但异质

| 模型 | 轴 | ratio [CI] | 解读 |
|---|---|---:|---|
| Qwen2.5-7B | deliberation | 0.583 [0.488,0.680] | facade hold |
| Qwen2.5-7B | skepticism | 0.548 [0.434,0.670] | facade hold |
| Qwen2.5-7B | uncertainty | facade hold（见生成表） | 与 Llama 形成 model-dependent 对照 |
| Qwen2.5-7B | focus | overshoot/no facade（见生成表） | 与 Llama 形成 model-dependent 对照 |
| Llama-3-8B | deliberation | 0.872 [0.798,0.937] | facade hold |
| Llama-3-8B | skepticism | 0.628 [0.581,0.673] | facade hold |
| Llama-3-8B | uncertainty | no facade（见生成表） | 与 Qwen 形成 model-dependent 对照 |
| Llama-3-8B | focus | facade hold（见生成表） | 与 Qwen 形成 model-dependent 对照 |

结论：C1 支持“若干 metacognitive axes 有 representational facade”，但跨模型不变只到 deliberation + skepticism；uncertainty 与 focus 明确是 model-dependent，不支持 axis-invariant general law。Deliberation layer-16 sensitivity 也需保留 caveat（E-0003）。

### 7.2 C2：2×2 全 0/3，uncertainty 四格 steer-vs-prompt 校准差

| Cell | deliberation Δ [CI] | skepticism Δ [CI] | uncertainty Δ [CI] | cell verdict |
|---|---:|---:|---:|---|
| CAA×Qwen | +0.015 [-0.040,+0.070] | -0.080 [-0.225,+0.045] | **-0.228 [-0.370,-0.092]** | 0/3 fail |
| CAA×Llama | +0.025 [-0.030,+0.075] | +0.000 [-0.190,+0.200] | **-0.072 [-0.103,-0.034]** | 0/3 fail |
| ITI×Qwen | +0.020 [+0.000,+0.055] | -0.100 [-0.270,+0.060] | **-0.103 [-0.136,-0.069]** | 0/3 fail |
| ITI×Llama | +0.015 [-0.040,+0.060] | +0.000 [-0.195,+0.205] | **-0.084 [-0.115,-0.049]** | 0/3 fail |

Interpretation：在 tested scope 内，bounded/naive latent steering **未显示任何超过 bounded best-prompt baseline 的额外控制（no demonstrated superiority under the pass rule）**。只有 uncertainty/calibration 的 steer-vs-prompt contrast 是稳健负结果（CI 排除 0）；它不是 direct latent steer-vs-baseline 伤害，Qwen/CAA direct effect 近零。deliberation 和 skepticism 的 non-transfer 是**欠功效非检出**，不是"证明无效应"。Post-hoc TOST equivalence（D-0056，exploratory，见生成表 `docs/paper/tables/equivalence-tost.tex`）：uncertainty 4/4 CALIBRATION_HARM（按 frozen steer-vs-prompt scorer）；deliberation ITI 2 cells EQUIVALENT（实际等价）、CAA 2 cells UNDERPOWERED；skepticism 4/4 UNDERPOWERED（方差过宽）。任何轴在任何 cell 均无 superiority。尤其 CAA×Qwen uncertainty Δ=-0.228，是 console v1/v2 反复高亮的红色告警，但必须附带 steer≈baseline caveat。该结论来自 C2 冻结行为裁决本身，不依赖 C1 uncertainty facade 是否复现。

### 7.3 PSR：KILL，但不能关闭 bounded-scale caveat

PSR Qwen primary（E-0009）结果：deliberation +0.025 [-0.030,+0.100] fail；skepticism -0.060 [-0.210,+0.070] fail；uncertainty -0.160 [-0.292,-0.039]，CI 排除 0 且为负。Audit 判定 VALID_NEGATIVE，确认 optimizer 做了真实 DEV 搜索、TEST steering 生效、无 leakage/degeneracy。Scope：single model / single seed / exploratory / valid_for_paper=false。

### 7.4 OOD：0/4，机制未证

OOD capture（E-0007）Spearman ρ(distance, −Δoutcome)：CAA×Llama +0.033 [-0.252,+0.317]；CAA×Qwen +0.039 [-0.259,+0.335]；ITI×Llama -0.060 [-0.321,+0.216]；ITI×Qwen -0.223 [-0.485,+0.065]。0/4 pass，VALID_NULL。结论：calibration harm 是稳健行为现象，但 off-manifold distance 解释不成立，不能在论文里当机制贡献。

### 7.5 社会轴：latent 可读，但行为操纵 null（探索性）

Powered novice-disclosure TEST（E-0010）：N=54,k=5，共 1080 records。M1 condition means：A=0.480741，B=0.482222，E=0.494074，C=0.438148；B−A M1=+0.00148148，CI[-0.0483356,+0.0466667]，p_bonf=1.0；B−E M1=-0.0118519，p_bonf=1.0；M4 全 0。M2/M3 = INVALID/not_implemented。READ probe：token-blind AUC=0.954047（literal AUC=1.0，drop=4.59534pp，null p95=0.785665），READ_HOLDS。

解读：DEV/L0 的 B>A +0.074/+0.078 没有在 powered TEST 复现；更诚实的说法是：social user-model axis 在 latent 上可读，但 implemented behavioral manipulation channel 在 power 下为 honest-null。human-α PENDING、LLM-judge-only、valid_for_paper=false。

### 7.6 Breadth：单 run 可读 + underpowered suppression null

Breadth L0：facade_ratio=0.2714735，verdict=LINEARLY_READABLE_L0；suppression strict=0.0833、calibrated=0.1667，N=12，bootstrap CI 跨 0。D-0047 明确：axis readout 是 deterministic echo，不是独立复现；`general_reasoning` dead-zone 会软化 coverage guard。因此只能作 contextual exploratory material。

## 8. 设计含义 / console

Console 的目标不是“把 latent 方向包装成 slider”，而是显示**边界**：

1. **READ status**：轴是否 latent-readable（C1 ratio/CI 或 social READ AUC）。
2. **TRANSFER verdict**：是否通过 prompt-vs-latent 行为裁决；social card 的 NULL 是 prompt condition B−A，不是 steering transfer。
3. **BOUNDED BEST-PROMPT BASELINE**（原"PROMPT-CEILING"）：bounded best prompt 已经达到什么水平；renamed 为中性术语，避免"ceiling"的倾向性含义。
4. **CALIBRATION-HARM**：uncertainty 轴若 frozen steer-vs-prompt contrast 显示校准风险，必须显式红色告警，并标出 direct steer-vs-baseline 是否近零。
5. **EVIDENCE-TIER**：confirmatory / exploratory / untested，显示单模型、单 seed、human-α pending 等 caveat。

失败分类（`failure-taxonomy.tex`）：F1 legible-but-non-transfer；F2 calibration backfire；F3 coherence-fragility corridor；F4 layer-sensitive instability；F5 axis extraction degeneration。当前是从 model evidence 推导出的 interface-evaluation implication，**不是用户研究结果**。

## 9. 局限与诚实边界

- C1：两模型单 run，聚合 3/4 但轴组成异质；跨模型不变只到 deliberation + skepticism，不能写成普遍定律。
- C2：强于单模型单方法，但仍限于 7–8B open instruct models、bounded/naive CAA/ITI at α≤24、三条 metacognitive axes、单 seed/冻结预算；不是 activation steering 不可能性定理。**重要区分：** uncertainty 轴是稳健 steer-vs-prompt contrast（CI 排除 0），不是 direct steer-vs-baseline 伤害；deliberation/skepticism 是欠功效非检出，不是"证明等价/无效应"（见 post-hoc TOST 表，exploratory）。
- Calibration harm 机制：off-manifold distance 已被 valid null；Brier 分解（reliability/resolution）**未做**——per-item confidence 在 A800 未提交 transcripts 中，可 re-run 恢复，不能从已提交 artifacts 推算；不得在 prose 里夸大校准机制或把 steer-vs-prompt 写成 steer-vs-baseline。
- PSR：只在 Qwen 单模型探索；不能覆盖所有 trained steering。
- 机制：OOD distance hypothesis 已被 valid null；机制未知。
- 社会轴：LLM-judge-only、human-α pending、M2/M3 not implemented、steer arm held；不能作为 confirmatory manipulation claim。
- Console：无真人研究；不能声称用户会理解、信任再校准或决策更好。

## 10. 未来工作

1. **Llama PSR 确认。** 若要把 PSR robustness 从 exploratory 推高，需要新 prereg + Llama 或更大预算。
2. **更强 steering / trained methods。** 任何 scale-corrected/raw-magnitude/norm-matched direction、multi-layer schedule、RepE、trained prompt-mimicking steering 都应新冻结，不得改写 E-0005/E-0006。
3. **机制新包。** Calibration harm 可探索 confidence-format disruption、answer-style distribution shift、sampling×calibration scoring，但必须新预注册。
4. **Brier 分解（未决）。** Uncertainty calibration harm 的 Brier 分解（reliability/resolution/base-rate）尚未完成——per-item (confidence, correctness) pairs 在 A800 未提交 transcripts 中，可 re-run 恢复。不能从已提交 artifacts 推算，不得在论文 prose 夸大校准机制。
5. **C1 结构。** 解释为什么 deliberation/skepticism 稳定，而 uncertainty/focus 翻转。
6. **真人走查。** Owner-gated；需要伦理/招募/venue 决策，测试 boundary instrumentation 是否改善 calibrated reliance。

## 11. 方法学与诚实哲学

本文的科学价值很大一部分来自“让负结果有资格被相信”：

- 看 TEST 前冻结 split、指标、δ、Bonferroni、coherence gate；
- 每个主要结果经独立 hostile audit；
- 失败不重挖：OOD mechanism null 后不在同数据上换机制；
- exploratory 不升级为 confirmatory：C1、PSR、social axis、breadth 都保留 valid_for_paper=false / caveat；
- 数字从 artifact/table/manifest 重建，不靠论文 prose 手抄。

这使负结果不是“实验失败”，而是一个可复查的 reality check：在现有证据边界内，console 应显示不能控制的地方。

## 12. Venue 策略

- **当前最匹配：IUI / pure-model reality-check + interactive console evaluation discipline。** R1 critic 在 2026-07-24 reframe review 中认为该路线在 IUI 可能比 CHI 更有竞争力，前提是扩展 robustness、机制语言保持 hypothesis-level；当时评分区间为 IUI 2.8–3.7/5、CHI 2.3–3.2/5（后续 E-0006 已关闭 single-method/single-model blocker）。
- **CHI experience track / CHI full paper：** 风险是无真人研究、console 只是 model-evidence-derived implication。若走 CHI，需要更强人机落点或明确定位为 methodology/reality-check。
- **FAccT / AIES：** 社会轴/操纵语境更契合，但 E-0010 目前 human-α pending 且是 honest-null/exploratory；不能把它包装成 manipulation finding。
- **拒稿风险：** “ML negative + HCI愿景”而非完成的交互贡献；“方法太弱”攻击（PSR 已初步 pre-empt 但未全解决）；界面可见度不足；缺少真人验证。
- **已加固：** 2×2 CAA/ITI×Qwen/Llama；PSR Qwen exploratory arm；console v2 artifact-derived card；claim-map 明确 C3 只是 interface-evaluation implication。
- **录取率注记：** owner brief 中要求写 IUI 约 24–25%；我在仓库内未找到官方可核验来源，故此处不把该百分比作为强事实，投稿策略文档需后续用官方 CFP/proceedings 核验。

## 13. 附：证据台账速查表（E-0003..E-0010）

| ID | Claim/用途 | 模型/方法 | 关键结果 | 审计/状态 | valid_for_paper |
|---|---|---|---|---|---|
| E-0003 | C1 Qwen facade | Qwen2.5-7B | 3/4 hold（uncertainty hold，focus overshoot/no facade） | Manager verified；device/dtype cache 修复 | false / exploratory |
| E-0004 | 早期 C2b lexical proxy | Qwen2.5-7B CAA crude proxy | 3/4 latent 未超 prompt；proxy ceiling saturated | audit rejected proxy basis；superseded by E-0005 | false / invalid |
| E-0005 | C2 frozen Qwen×CAA | Qwen2.5-7B CAA | 0/3 pass；uncertainty -0.228 [-0.370,-0.092] | hostile audit VALID_NEGATIVE | honest negative / scoped |
| E-0006 | C2 2×2 generalized | CAA/ITI × Qwen/Llama | 四格全 0/3；uncertainty harm 四格 CI 排除 0 | hostile audit VALID_ARM_EVIDENCE | core supported scoped negative |
| E-0007 | C2-mech OOD | 4 cells uncertainty | Spearman ρ 0.033,0.039,-0.060,-0.223；0/4 pass | hostile audit VALID_NULL | null only / future work |
| E-0008 | C1 Llama replication | Llama-3-8B | 3/4 hold，但 uncertainty 不 hold、focus hold；轴组成异质 | hostile audit mergeable | false / exploratory |
| E-0009 | PSR method-strength arm | Qwen2.5-7B PSR-style | KILL；delib +0.025，skep -0.060，unc -0.160 CI excl 0 negative | hostile audit VALID_NEGATIVE | false / exploratory support |
| E-0010 | social-inference axis | Qwen2.5-7B novice-disclosure | M1 B−A +0.00148 p=1.0；M4 0；READ AUC=0.954 | science VALID; D-0049 provenance repaired | false / exploratory |

---

### 数字核对来源清单

- Paper source：`docs/paper/main.tex`。
- Claim/citation：`docs/paper/claim-map.yaml`、`docs/paper/citation-map.yaml`、`docs/ledgers/claim-ledger.md`、`docs/ledgers/hypothesis-ledger.md`。
- Evidence authority：`docs/ledgers/evidence-ledger.md` E-0003..E-0010。
- Decisions：`docs/ledgers/decision-log.md` D-0041..D-0049，另含 D-0038/D-0039/D-0040 关键 lineage/arm/null 决策。
- Generated paper tables：`docs/paper/tables/c1-twomodel.tex`、`docs/paper/tables/c2-delta-4cell.tex`、`docs/paper/tables/failure-taxonomy.tex`。
- Result artifacts/summaries：`results/console_v1_demo/console_v1_demo_report.md`、`results/flagship_powered/summary.md`、`results/ood_capture/summary.md`、`results/psr_qwen_primary/psr_c2b_adjudication_results.json`、`results/breadth_confirm2/breadth_l0_hf_k5_seed20260727.json`。
- Console/figures：`docs/specs/console-v1.md`、`docs/paper/figure-manifests/*.yaml`。

### 仍需保留的不确定/存疑

1. IUI 录取率 24–25% 未在仓库内找到可核验来源；本文档只按策略方向讨论，不把该数字当已验证事实。
2. Social axis 的 human-α 未完成；E-0010 不能作为 confirmatory paper claim。
3. Console UI contract 是 artifact-derived demo/figure，不是用户研究；任何“信任改善”都需未来真人证据。
4. OOD null 只否定当前 whitened Mahalanobis distance 机制，不否定其他机制。
