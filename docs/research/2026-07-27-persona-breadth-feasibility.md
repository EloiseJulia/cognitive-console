# Persona breadth/focus feasibility study (idea #1)

Date: 2026-07-27  
Scope: **design + feasibility only**. No model run, no GPU use, no paid API.  
Status: candidate direction for Manager triage; not a preregistered protocol.

Repository inspection note: the requested reusable facade module is present at
`src/cognitive_console/analysis/facade.py` (not `analysis/facade.py` at repo
root). The requested brainstorm file
`docs/research/2026-07-27-implicit-user-conditioning-brainstorm.md` was not
present in this worktree.

## Executive verdict

**Recommendation: conditional GO for an owner-budget-gated L0 pilot, not for full-study investment yet.** The idea is plausible and well aligned with cognitive-console because it tests a new human-legible axis (`breadth/focus`) where prompt control may be non-surjective: a narrow persona can be legible and helpful-looking while suppressing latent solution-space breadth. The direction should be funded only as a **kill-fast pilot** whose success criteria are (i) observable persona-induced oracle-domain suppression on a tiny curated suite, and (ii) a non-degenerate, linearly readable breadth/focus direction under CAA/ITI-style extraction.

The two hardest feasibility unknowns are:

1. **Linear axis risk:** "breadth" may be an aggregate of multiple mechanisms (domain retrieval, exploration entropy, planning horizon, self-correction, style hedging), not one linearly readable residual direction.
2. **Suite validity risk:** constructing tasks where the cross-domain/oracle method is genuinely better, not merely a human label preference, is nontrivial and can easily collapse into subjective adjudication.

## Prior-art positioning and novelty claim

The strongest defensible novelty is the **conjunction**, not any component alone:

- **A. Cross-domain suppression measurement:** measure whether a narrow persona *removes* out-of-domain / more-optimal solution approaches from samples, not just whether final accuracy changes.
- **B. User mis-specification harm:** study cases where the user's chosen persona/domain is plausible but wrong or overly narrow, so the harm is caused by user-specified scope.
- **C. Latent breadth-axis fix:** test whether a latent `breadth/focus` intervention can recover cross-domain approaches without simply replacing the persona with another readable prompt.

Important differentiators:

| Work | Verified status | What it studies | Differentiation needed |
|---|---:|---|---|
| PRISM, *Expert Personas Improve LLM Alignment but Damage Accuracy*, arXiv:2603.18507 | **UNVERIFIED venue/date; arXiv URL verified by web search** | Persona routing; alignment/format benefits vs accuracy damage; avoids harmful persona use. | We must not claim "personas can hurt" as novelty. Our unit is **oracle-domain suppression / solution-space narrowing**, with latent recovery as a legibility-vs-controllability test. |
| *Persona is a Double-edged Sword*, arXiv:2408.08631 | arXiv verified; ACL 2025 status from search result, mark if cited as venue | Persona prompts can degrade zero-shot reasoning; Jekyll & Hyde mitigates via persona/neutral answer aggregation. | We need paired **domain-coverage** outcomes and mis-specified personas, not generic reasoning accuracy degradation. |
| *Principled Personas*, EMNLP 2025 | ACL Anthology/arXiv page found by search | Framework for expertise advantage, robustness, fidelity; evaluates persona prompting across tasks. | Our claim should be orthogonal: even a relevant-looking persona may suppress a better cross-domain approach. |
| *The Price of Format: Diversity Collapse in LLMs*, arXiv:2505.18949 | arXiv verified | Structured formatting can reduce output diversity. | It threatens novelty. We must show **domain-specific solution collapse** under role persona, not only generic diversity loss. |
| CAA / activation steering literature (e.g., Panickssery et al. ACL 2024, arXiv:2312.06681) | verified | Contrastive activation addition and inference-time steering. | Methodological substrate only; novelty is applying a non-surjective breadth/focus axis to persona scope-locking. |

Citations to verify before any paper claim: arXiv:2603.18507
<https://arxiv.org/abs/2603.18507>; arXiv:2408.08631
<https://arxiv.org/abs/2408.08631>; ACL Anthology 2025.emnlp-main.1364
<https://aclanthology.org/2025.emnlp-main.1364/> / arXiv:2508.19764
<https://arxiv.org/abs/2508.19764> for *Principled Personas*; arXiv:2505.18949
<https://arxiv.org/abs/2505.18949>; ACL Anthology 2024.acl-long.828
<https://aclanthology.org/2024.acl-long.828/> / arXiv:2312.06681
<https://arxiv.org/abs/2312.06681>.

## 1. Latent breadth-vs-focus axis construction

### 1.1 Contrast design

Use existing CAA/ITI/RepE-style tooling, but create a new axis named `breadth` or `breadth_focus`.

**Positive pole: broad/exploratory.** Prompts should encourage cross-domain search without asking for verbosity alone:

- "Before solving, enumerate substantially different solution frames from multiple domains, then choose the simplest valid one."
- "Do not stay within the obvious domain if another field offers a cleaner method."
- "Generate at least three distinct approaches: algebraic, algorithmic/computational, and analogical/operational, then solve."
- "Act as a generalist problem solver who transfers tools across domains."

**Negative pole: narrow/domain-locked.** Prompts should lock scope while preserving competence:

- "Act only as an Excel expert; solve using spreadsheet formulas and workflows."
- "You are a legal drafting specialist; answer only in contract-analysis terms."
- "Use only the concepts and tools from [persona domain]; do not consider other fields."
- "Stay within the assigned role even if another approach seems possible."

**Pairing rule:** each item should share the same base task, with only the instruction/persona differing. Pos/neg contrast pairs must not include the downstream evaluation items verbatim. Recommended L0 extraction size: 24--40 pairs, balanced across persona domains (Excel, legal, project management, education, medicine-like but avoid real medical advice, software engineering, statistics, operations research).

### 1.2 Reuse of existing extraction methods

Existing modules already support most mechanics:

- `src/cognitive_console/steering/extract.py`: CAA mean-difference extraction (`extract_caa`), per-layer Cohen's-d separation diagnostics, and non-degenerate layer selection via depth floor + positive pole reach + random-null p95 (`select_nondegenerate_layer`).
- `src/cognitive_console/steering/iti.py`: ITI-style logistic probe direction (`extract_iti`) with sigma-scaled intervention and the same non-degenerate selection interface.
- `src/cognitive_console/steering/generate.py`: HF residual capture and generation with optional residual addition (`SteeredHFBackend.capture_residual_activations`, `SteerConfig`, `generate`, `generate_batch`).
- `src/cognitive_console/analysis/facade.py`: facade-style projection metric (`analyze_axis_facade`) that tests prompt reach relative to a latent direction and random null.

### 1.3 Legibility/readability checks

The first feasibility question is not "does steering improve tasks?" but "is the axis linearly readable at all?" Proposed checks:

1. **Extraction separation:** scan layers and require positive pos/neg separation, using the CAA `layer_diagnostics` / ITI probe diagnostics.
2. **Non-degenerate positive pole:** require the broad pole displacement from neutral to clear the random-direction null p95, reusing `select_nondegenerate_layer`. This prevents selecting a shallow lexical layer that separates prompt wording but cannot support a meaningful facade read.
3. **Facade-style prompt reach:** create a held-out set of strongest human-readable breadth prompts and strongest focus/persona prompts. Measure whether those prompts project in the expected direction relative to neutral, using the same-origin projection logic from the C1 facade code path.
4. **Out-of-distribution sanity:** test whether the direction predicts held-out broad vs focus prompts from persona domains not used in extraction. A direction that only recognizes "Excel" tokens is not a breadth axis.
5. **Non-degeneracy / specificity guard:** compare against lexical controls of equal length and structure ("Act as a person named Alex..."; "Use a concise answer...") to ensure the axis is not just verbosity, confidence, or role-token formatting.

### 1.4 Biggest feasibility risk

The likely failure mode is **multi-mechanism breadth**. A broad answer may require (a) higher sampling entropy, (b) retrieval of remote domains, (c) willingness to violate the persona instruction, (d) longer planning, and (e) meta-cognitive comparison. These may live in different layers/directions. If CAA/ITI finds no stable layer or if the direction only controls verbosity/diversity, the axis should be downgraded to "not linearly readable" rather than rescued with post-hoc nonlinear probes.

## 2. Cross-domain task suite design

The suite does **not** exist yet. It must be built as a tiny, curated instrument before any pilot.

### 2.1 Item definition

Each item has:

- `item_id`
- `task_text`
- `narrow_persona`: plausible user-specified domain (e.g., Excel expert)
- `oracle_domain`: the domain containing the cleaner/better approach (e.g., graph theory, dynamic programming, statistics, optimization)
- `oracle_solution`: short reference solution
- `oracle_domain_markers`: allowed concepts/methods indicating oracle-domain use
- `persona_domain_markers`: concepts/methods indicating in-persona solving
- `validity_note`: why oracle-domain is objectively better, not just different
- `rubric`: deterministic or frozen-adjudicator criteria

### 2.2 Candidate task families

1. **Spreadsheet persona vs algorithmic solution**
   - Persona: "Act as an Excel expert."
   - Oracle domains: graph algorithms, dynamic programming, combinatorial optimization.
   - Example: dependency ordering / shortest path / assignment problem described as spreadsheet columns. Excel-only formulas can solve clumsily; graph/optimization framing is cleaner.
   - Oracle source: known algorithmic result + small answer key.

2. **Legal/contracts persona vs decision theory/statistics**
   - Persona: "Act as a contract analyst."
   - Oracle domains: expected value, Bayesian updating, risk matrices.
   - Example: choose among contract clauses with uncertain penalties/probabilities. Legal analysis is plausible but expected-value computation gives the better decision.
   - Avoid real legal advice; use synthetic toy contracts.

3. **Project-manager persona vs queueing/operations research**
   - Persona: "Act as a project manager."
   - Oracle domains: critical path, queueing bottleneck analysis, linear programming.
   - Example: staffing/scheduling tradeoff where PM heuristics are plausible but CP/LP finds the optimum.

4. **Writing/communications persona vs information theory/search**
   - Persona: "Act as a communications coach."
   - Oracle domains: binary search, entropy, active learning.
   - Example: design the minimum number of yes/no questions or diagnostic prompts. Rhetorical advice is plausible but information-theoretic splitting is optimal.

5. **Tutor persona vs formal proof/counterexample**
   - Persona: "Act as a patient tutor."
   - Oracle domains: invariant/counterexample construction.
   - Example: a word problem where explanatory scaffolding tends to stay in narrative mode but invariant reasoning gives a concise solution.

6. **Open-domain creativity / Alternative Uses style**
   - Persona: "Act as a [single profession]."
   - Oracle: diversity across unrelated domains, not a single correct answer.
   - Metric: distinct approach-domains and semantic clustering; use only as secondary because adjudication is less objective.

### 2.3 Oracle solution construction

For L0, use **hand-authored synthetic microtasks** plus answer keys, not mined benchmark items. Prefer tasks whose oracle method has a short, inspectable proof of optimality (e.g., shortest path, expected value, min-cut toy, dynamic programming recurrence). For code-like tasks, reuse HumanEval+/EvalPlus style harnesses where the oracle domain is an algorithmic technique and tests can verify correctness. For open-ended tasks, use Alternative-Uses-style sampling only as a diversity stress test, not as the primary claim.

### 2.4 Harness strategy

- **Deterministic/closed tasks:** create JSONL items and a scorer that checks final answer plus oracle-domain markers. Where possible, use unit tests (EvalPlus/HumanEval+ style) to verify correctness separately from domain classification.
- **Domain classification:** frozen adjudicator labels whether a sample uses the oracle domain, persona domain, both, neither, or invalid. For L0, combine regex/domain-marker prelabels with a frozen LLM/human adjudicator spec, but no paid API unless owner-approved.
- **Paired design:** every item is sampled under `no-persona`, `narrow-persona`, and `oracle-persona`; optionally `narrow-persona + breadth steering` in the second half of L0 if extraction succeeds.

## 3. Metrics and adjudication

### 3.1 Primary metrics

Let `k` be samples per condition per item.

1. **Domain Coverage@k**  
   Number of distinct valid approach-domains represented among the `k` samples. Report per item and averaged by condition. This captures solution-space narrowing even when final accuracy is unchanged.

2. **Oracle-domain reach@k**  
   Indicator that at least one of the `k` samples uses the known oracle domain.

3. **Oracle-domain suppression rate**  
   Fraction of items where `no-persona` reaches the oracle domain but `narrow-persona` does not, or where `oracle-persona` reaches it and `narrow-persona` does not under the same `k`. Two definitions should be reported:
   - strict: `no-persona` reaches oracle and `narrow-persona` never reaches oracle;
   - calibrated: `oracle-persona` reaches oracle and `narrow-persona` never reaches oracle.

4. **Mis-specification harm rate**  
   Fraction of items where narrow-persona is plausible but produces lower oracle-domain reach or lower task score than no-persona.

5. **Breadth rescue rate** (only if a direction is linearly readable)  
   Fraction of suppressed items where `narrow-persona + breadth steering` restores oracle-domain reach without increasing invalid/degenerate outputs beyond the coherence gate.

### 3.2 Fair paired adjudication

Reuse the frozen-adjudicator pattern from `src/cognitive_console/experiments/adjudicate_c2b.py`:

- Split any item set into DEV/TEST before choosing alpha or prompt variants.
- Freeze `k`, decoding temperature, sample seeds, alpha grid, domain labels, domain-marker lexicons, and adjudication rubric before TEST.
- Use item-clustered paired comparisons: compare narrow vs no-persona vs oracle-persona on the same item and sample budget.
- Keep `oracle-persona` as a calibration arm, not the treatment of interest.
- Add coherence/degeneracy flags: empty answers, repetitive text, refusal, failure to answer, or pure prompt-instruction discussion.

No hand-typed numbers should enter paper artifacts; all future counts must be generated from persisted JSONL/JSON results and registered experiment IDs.

## 4. Smallest L0 pilot

### 4.1 Purpose

Minimum decisive probe:

- **P1:** Does a plausible but narrow persona suppress oracle-domain solutions at all?
- **P2:** Is a `breadth/focus` latent direction extractable and linearly readable under existing CAA/ITI tooling?

Do **not** attempt to prove the full research claim in L0.

### 4.2 Proposed L0 design

- **Model:** `Qwen/Qwen2.5-7B-Instruct` on a single 24GB GPU, matching prior local exploratory infrastructure. If budget is extremely tight, first smoke on `Qwen/Qwen2.5-1.5B-Instruct`, but the decision-quality L0 should use 7B because prior registry entries used it for C2b-style work.
- **Items:** 12 curated cross-domain items total, 2 per task family. DEV/TEST split only for steering alpha if a breadth direction is extracted; suppression measurement can be descriptive on all 12 but should be labeled exploratory.
- **Extraction pairs:** 32 contrast pairs for breadth/focus, plus 8 held-out prompt pairs for readability checks.
- **Conditions:** `no-persona`, `narrow-persona`, `oracle-persona`; if axis passes readability, add `narrow-persona + breadth steer`.
- **Samples:** `k=5` per condition per item at temperature 0.7, fixed seeds. This is the smallest useful value for Coverage@k / reach@k; `k=1` cannot measure suppression of a sampled solution space.
- **Generation budget:** without steering: 12 items × 3 conditions × 5 = 180 generations. With breadth steer: +60 generations. Extraction/readability adds activation captures over roughly 80 prompts across scanned layers, not many generations.
- **Decision thresholds (exploratory):** fund full protocol only if at least 3/12 items show strict oracle suppression under narrow persona, and breadth extraction finds a non-degenerate layer with held-out broad-vs-focus projection in the expected direction. These are not paper thresholds.

### 4.3 Cost estimate (owner-budget-gated; do not run)

Use repo's recent run ledger as calibration:

- C1-style Llama-3-8B facade run: ~87.6 s on RTX 4090 D for activation-heavy C1 extraction/facade before registry postprocessing failed, with metrics written.
- Qwen2.5-7B C2b adjudication/PSR run: ~3730 s (~1.04 h) on RTX 4090 D 24GB for a much larger frozen adjudication arm.

The L0 pilot is much smaller than the C2b run: ~240 generations plus activation captures, versus many prompt/alpha/sample cells. Conservative estimate:

- **GPU time:** 0.5--1.5 hours on a 24GB 4090-class GPU, depending on batching and max_new_tokens.
- **Direct dollar cost:** $0 if using already-approved local/borrowed GPU; otherwise owner-budget-gated. If rented, estimate roughly **$1--$5** at common spot/on-demand 4090/A10-class hourly rates, but exact provider pricing must be approved before use.
- **Paid API:** $0 planned; no paid API required.

Because AGENTS.md treats GPU/compute escalation as human-approved, Manager must obtain owner approval before running this L0.

## 5. Reuse map

### Reusable as-is

- `src/cognitive_console/steering/extract.py`: CAA extraction, layer diagnostics, non-degenerate layer selection.
- `src/cognitive_console/steering/iti.py`: ITI probe extraction and sigma-scaled alpha interpretation.
- `src/cognitive_console/steering/generate.py`: residual capture, steering injection, single and batched generation through `SteeredHFBackend`.
- `src/cognitive_console/analysis/facade.py`: facade/readability projection structure for held-out broad/focus prompts.
- `src/cognitive_console/experiments/adjudicate_c2b.py`: paired DEV/TEST, frozen prompt/alpha selection, k-sample item-clustered adjudication pattern, checkpoint/progress architecture.
- `scripts/run_c1_facade.py`: data loading, neutral-origin projection, bootstrap/leave-one-out style reporting patterns.
- Existing registry/manifest/lineage patterns for future run logging.

### Build new

- `data/breadth_focus_contrast_pairs/*.jsonl` or equivalent: broad vs narrow paired extraction data.
- `data/cross_domain_scope_lock/*.jsonl`: curated cross-domain items with oracle domains and rubrics.
- Domain taxonomy and marker lexicons: oracle/persona/both/neither labels.
- A scorer/adjudicator for Domain Coverage@k, oracle-domain reach, and suppression rate.
- A runner, likely `scripts/run_persona_breadth_l0.py`, that wires extraction + readability + paired condition sampling + JSON artifacts.
- Tests for leakage: extraction prompts must not duplicate task-suite items; persona-domain markers must not trivially reveal oracle labels.
- A preregistration ledger if L0 graduates beyond exploratory.

### Maybe reuse with adaptation

- C2b `BackendOutcomeSampler`: useful for k-sample generation/checkpointing, but outcome scoring must be replaced with domain-coverage adjudication rather than answer-key score.
- C1 facade table: useful for `breadth_prompt_reach / breadth_pole_reach`, but the axis needs held-out broad/focus prompts and lexical controls.

## 6. Kill criteria and go/no-go

### Kill criteria

Kill or heavily pivot this direction if any of the following happen in L0:

1. Narrow personas do not suppress oracle-domain reach on at least a small visible subset of items.
2. Suppression appears only as generic output diversity/format collapse, with no domain-specific oracle loss.
3. The breadth/focus direction has no non-degenerate layer, fails held-out broad/focus prompts, or mostly tracks length/verbosity/persona tokens.
4. The cross-domain suite cannot produce objective oracle superiority without subjective labels.
5. Breadth steering restores oracle domains only by causing incoherence, instruction violation that users would reject, or broad but incorrect answers.

### Go recommendation

**GO for L0 only.** The research direction is worth a low-cost pilot because it is tightly connected to non-surjectivity and could add a new console axis that is more user-facing than the current cognitive-control axes. It is not yet ready for a full protocol because both the latent-axis and benchmark-validity risks are high.

A clean L0 success would justify a novelty/audit pass focused on whether this is distinguishable from PRISM/persona-harm and diversity-collapse prior work. A failed L0 is still informative: it would say persona scope-locking may be real behaviorally but not linearly controllable, which supports the broader legibility != controllability theme without becoming a new core claim.
