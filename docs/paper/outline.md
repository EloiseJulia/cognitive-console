# Paper Outline — IUI-first pure-model reality-check route

Status: writing scaffold, not paper freeze. Route follows D-0035/D-0036/D-0041: **IUI-first if no human study**, with CHI as secondary empirical-track option and CSCW only if a human/collaboration study returns. This supersedes the stale CHI-first line in `docs/paper/reframe-2026-07-24-reality-check.md` without editing that frozen/history document.

## Working title
Legible Need Not Be Controllable: A Frozen Reality Check for Prompt-vs-Latent Behavioral Control in LLMs

## Novelty unit
A frozen, fairness-controlled, independently-audited behavioral adjudication showing that representational legibility does **not** transfer to control, generalized across 2 steering methods × 2 model families, with a replicated negative steer-vs-bounded-prompt uncertainty contrast.

## Abstract (claims carried: C1 scoped; C2 headline; C3 interface-evaluation implication only)
- Problem: HCI tools increasingly promise readable controls over LLM behavior, but a readable cognitive axis may not be a usable control primitive.
- Background: Mishra et al.'s non-surjectivity result motivates a prompt/latent gap at the internal-state level; we do **not** claim that result as our own behavioral finding.
- Evidence: C1 shows an exploratory representational facade on 3/4 axes in Qwen2.5-7B: deliberation, skepticism, and uncertainty; focus overshoots and is not a facade.
- Headline: C2 shows that naive/off-the-shelf CAA and ITI steering fail to beat the best bounded prompt in all 4 method×model cells, and uncertainty calibration is harmed in all 4 cells.
- Design stance: a cognitive console should instrument limits and failure modes of legible control, not promise a latent superpower slider.
- Scope: bounded prompt effort, frozen adjudicator, Qwen2.5-7B and Llama-3-8B, CAA/ITI only. Not an impossibility theorem; PSR-style trained steering is a planned direct response, not a completed result.

## 1. Introduction (claims carried: C1, C2, C3 as implication)
1. **Motivation.** End users can describe desired model states in language, while steering methods expose latent directions. The HCI question is whether readable directions are safe or effective controls.
2. **The non-surjectivity motivation.** Cite Mishra et al. as background for internal activation non-surjectivity. State explicitly: internal non-surjectivity does not entail behavioral prompt failure.
3. **The empirical reality check.** Introduce the frozen prompt-vs-latent adjudicator: best prompt and alpha selected on DEV, paired TEST comparison, item-cluster bootstrap, Bonferroni CI, coherence gate.
4. **Four contribution bullets, corrected to current evidence:**
   - **Measurement contribution (C1):** an exploratory representational-facade measurement on Qwen2.5-7B, where readable prompts reach only a fraction of the extracted axis pole for 3/4 axes; Llama replication is owed.
   - **Headline empirical contribution (C2):** a generalized negative result: across {CAA, ITI} × {Qwen2.5-7B, Llama-3-8B}, latent steering does not beat the bounded best-prompt ceiling on any tested axis, and calibration is harmed in all four cells.
   - **Methodology contribution (C2 support):** a reusable frozen adjudication protocol for fair prompt-vs-latent behavioral comparison.
   - **Design implication (C3):** console designs should surface boundary conditions and trust-calibration warnings; no user-study credit is claimed yet.
5. **Non-claims.** We do not claim universal impossibility of latent steering, a mechanism proof for the comparator-bound calibration contrast, empirical user-study results, or that Mishra is our empirical result.

## 2. Related Work (claims carried: C2a background; novelty contrast; no empirical claims)

### 2.1 Non-surjectivity and prompt/latent mismatch
- Mishra et al.: internal residual-state non-surjectivity; use as motivation only.
- PSR / "Steer Like the LLM": trained steering can match/exceed prompting; use as the strongest threat. The frozen latent-recovery arm is planned as a direct response, with no results yet.

### 2.2 Activation steering lineage
- CAA and ActAdd provide mean-difference/activation-addition steering material; CAA is a tested family in C2.
- ITI provides the second tested family in the robustness arm; exact bibliographic details need verification before final references.
- RepE and related steering methods define adjacent stronger/alternative interventions; not tested in the current C2 grid.

### 2.3 HCI/control-interface neighbors
- AI-Instruments: prompt-layer direct manipulation, no latent channel.
- Huang & Lim: layperson feature-steering sliders, but single latent channel and no prompt-vs-latent adjudication.
- Labarta / From Attribution to Action: vision/CLIP expert debugging, not an LLM cognitive-axis console.
- Latent Manipulator: concept-guided embedding-visualization manipulation, not LLM generation/control.

### Nearest-neighbor novelty contrast table (R1-F4)

Citation hygiene rule for this table: use only works verified in `docs/research/2026-07-24-citation-verification.md`; BibTeX keys match `docs/paper/references.bib`.

| prior work (year; cite key) | what THEY test | what WE uniquely adjudicate |
|---|---|---|
| Sprejer et al., *Mind the Performance Gap* (2026; `sprejer2026mindgap`) | Closest empirical neighbor: feature steering can induce capability--behavior trade-offs and degradation relative to prompting | External context for the C2 comparator-bound contrast, not a scoop: Goodfire SAE features, MMLU, no pre-registration, no CAA/ITI 2×2 model grid, no HCI legibility-console framing |
| Mishra et al., *Steered LLM Activations are Non-Surjective* (2026 workshop; `mishra2026nonsurj`) | Internal residual-state non-surjectivity under activation steering | A behavioral prompt-vs-latent transfer test under frozen DEV/TEST adjudication; Mishra is background, not our result |
| Heyman & Vandeputte, *Steer Like the LLM* (2026; `heyman2026steer`) | Trained steering that mimics prompting | Naive/bounded off-the-shelf CAA/ITI failure; PSR is a threat and planned response, not covered by C2 |
| Rimsky et al. CAA + Li et al. ITI (2024/2023; `rimsky2024caa`, `li2023iti`) | Activation steering methods | Whether those legible directions beat the best prompt on task outcomes, with fairness controls and hostile audits |
| Fan et al. ASTEER + Korznikov et al. Rogue Scalpel (2026; `fan2026asteer`, `korznikov2025rogue`) | Steerability limits and safety-domain steering failures | Metacognitive-axis prompt-vs-latent adjudication, not a broad benchmark or safety attack |
| Huang & Lim (2025; `huang2025steering`) | Layperson GUI for SAE feature steering/persona building | Prompt-vs-latent behavioral non-transfer and interface-evaluation implications; no human-study claim in this route |
| Riche et al., Labarta et al., Raval et al. (2025/2026; `riche2025aiinstr`, `labarta2026attribution`, `raval2026latman`) | Prompt instruments, expert vision/CLIP steering, and embedding-visualization manipulation | LLM behavioral control and a comparator-bound negative calibration contrast; Labarta is vision/CLIP and Latent Manipulator steers visualizations, not LLM generations |
## 3. Methods (claims carried: C1 measurement; C2 adjudication)

### 3.1 C1 facade measurement
- Model/artifact: Qwen2.5-7B-Instruct exploratory run, `results/gpu_7b_2026-07-23/c1/`, experiment `c1-facade-d710b4b4-0001`.
- Metric: same-origin, scale-free `facade_ratio = prompt_reach / pole_reach` at a non-degenerate layer.
- C1 validity guard: exploratory only; Llama replication pending (Workstream A); no blind user evaluation claimed.

### 3.2 Frozen behavioral adjudicator
- Source protocol: `docs/ledgers/prereg-c2b-adjudication.md`.
- Outcomes: deliberation accuracy, skepticism false-premise rejection, uncertainty `(1 - Brier)`.
- Fairness: DEV selects best prompt and alpha; TEST adjudicates paired steer-prompt differences.
- Steering scale: `h'=h+alpha*s_m*u_m`, with `s_CAA=1`, `s_ITI=sigma_L`; the shared grid bounds the coefficient at `alpha<=24`, not ITI's injected norm.
- Statistics: item-cluster bootstrap, B≥10000, Bonferroni 98.33% CI, δ=0.05, coherence gate `g_steer <= 1.5*g_baseline + 0.02`.

### 3.3 Steering families and models
- CAA × Qwen2.5-7B begins with E-0005; robustness arm E-0006 extends to CAA/ITI × Qwen/Llama.
- Llama uses the NousResearch identical-weights mirror per D-0038; record this as provenance.

### 3.4 Audit and provenance
- State that C2 evidence is independently hostile-audited: E-0005 VALID_NEGATIVE, E-0006 VALID_ARM_EVIDENCE, E-0007 VALID_NULL.
- All paper numbers must trace through manifests, not manual transcription.

## 4. Results (claims carried: C1 scoped; C2 headline)

### 4.1 RQ1: representational facade exists on 3/4 Qwen axes, exploratory
- Main figure: ratio-CI figure from `results/gpu_7b_2026-07-23/c1/c1_facade_results.json`.
- Current result: deliberation 0.583 [0.488, 0.680], skepticism 0.548 [0.434, 0.670], uncertainty 0.713 [0.517, 0.910] have CI upper < 1; focus is 2.844 [2.061, 3.549] and is not a facade.
- **C1 heterogeneity caveats (R1-F6):** focus overshoots/no-facade; deliberation at layer 16 crosses 1 (`0.946 [0.847, 1.050]`), showing layer sensitivity; C1 remains exploratory and single-model pending Llama.

### 4.2 RQ2: legibility does not transfer to behavioral control
- Main table: 4-cell Δ-table from `results/arm_full/arm_matrix_summary.json` plus each cell's `c2b_adjudication_results.json`.
- Report each cell as 0/3 axes pass: CAA×Qwen, CAA×Llama, ITI×Qwen, ITI×Llama all `KILL_PLAN_D`; arm verdict `NON_TRANSFER_GENERALIZED`.
- Include per-axis Δ columns with Bonferroni CI and pass/fail; do not hand-enter final camera-ready values outside the artifact pipeline.

### 4.3 Steer-vs-bounded-prompt negative calibration contrast in all four cells
- Main/stub figure: calibration-harm-across-4-cells.
- Required values from E-0006: CAA×Qwen −0.228, CAA×Llama −0.072, ITI×Qwen −0.103, ITI×Llama −0.084; all CIs exclude 0 negatively.
- Interpretation: naive CAA/ITI steering is not just null for uncertainty; it worsens calibration in all tested method×model cells.

### 4.4 Mechanism test failed cleanly
- E-0007 tested off-manifold distance as an explanation and returned VALID_NULL: 0/4 cells pass.
- This appears only as limitation/future-work context, not as a mechanism contribution.

## 5. Interface-evaluation contract (claims carried: C3 interface-evaluation implication only)
- Replace "latent control slider" framing with a limits instrument: show when legible directions fail, when calibration is harmed, and when prompt-only is safer.
- Console outputs should be framed as adjudication and trust-calibration aids, not proof of hidden user control.
- No empirical HCI/user-study credit is claimed on the pure-model route.

## 6. Limitations (claims carried: scope constraints)
- C1 is exploratory and Qwen-only at 7B; Llama C1 replication is owed.
- C2 covers bounded prompt effort and naive/off-the-shelf CAA/ITI only; it is not an impossibility theorem.
- PSR-style trained/optimized steering is a known threat and planned direct-response arm; no result yet.
- Mechanism is open after E-0007; off-manifold distance did not explain the harm.
- Human study is deferred and owner-gated; pure-model IUI route may still face venue-fit risk.

## 7. Future Work (claims carried: C2-mech hypothesis; C3 possible empirical route)
- Run the frozen latent-recovery arm (`prereg-latent-recovery-arm.md`) to test faithful PSR-style DEV-optimized steering.
- Run Llama C1 facade replication (Workstream A) before promoting C1 beyond exploratory.
- Design and preregister a human study only if owner approves the venue fork.
- Investigate mechanisms behind the negative steer-vs-bounded-prompt contrast in a new preregistered package; do not re-mine E-0007 data.

## 8. Conclusion (claims carried: C1 scoped; C2 headline; C3 implication)
- Repeat only evidence-backed claims: exploratory legibility facade, generalized C2 non-transfer across tested cells, the four-cell steer-vs-bounded-prompt negative calibration contrast under the frozen scorer, and the interface-evaluation implication. Keep direct Qwen/CAA steer-vs-baseline near zero (+0.011 compliance, +0.0008 1-Brier).
- Do not conclude that all steering fails, that prompts are behaviorally non-surjective in general, or that users empirically benefit from the console.
