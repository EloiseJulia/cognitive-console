# C2b Composition / Augmentation Preregistration

- **Spec ID:** `c2b-composition-augmentation`
- **Dispatch:** A — prompt + steer composition, not substitution
- **Status:** `FREEZE CANDIDATE / NOT FROZEN / UNRUN / NOT AUTHORIZED TO EXECUTE`
- **Prepared:** 2026-08-18
- **Primary planned experiment id:** `composition-a-qwen-20260818-0001`
- **Parent evidence:** frozen substitution grid E-0005/E-0006/E-0011 and post-hoc TOST/MDE characterization
- **No-compute boundary:** this document registers the protocol only. It does **not** authorize GPU,
  TEST generation, α tuning, Llama execution, or paper-claim changes.

> **Authorization gate.** Execution requires Manager freeze approval plus the usual GPU/budget gate.
> The first authorized run is Qwen2.5-7B only. Llama-3-8B is a contingent extension and must return to
> Manager with signal/budget evidence before any Llama GPU run.

---

## 1. Research question and estimand

**RQ-COMP:** When a user has already given an instruction, does adding latent steering on top of that
instruction provide incremental behavioral quality?

This is an **augmentation/composition** estimand, not the headline substitution estimand. The frozen
headline grid asked whether `steer-only` beats a bounded prompt baseline. This protocol asks whether
`prompt + steer` beats the **same prompt alone** on the same item:

```text
d_i(axis, method, model, prompt_baseline) =
  outcome_i(prompt_baseline + steer(method, α*)) − outcome_i(prompt_baseline alone)
```

All inference is paired per item. Any result here is **additive** to the frozen substitution result and
does not overwrite E-0005/E-0006/E-0011. A positive composition finding would mean steering can be useful
as augmentation under a user instruction; it would not make the substitution-only headline false.

---

## 2. Frozen design matrix

| Dimension | Frozen value |
|---|---|
| Axes | `deliberation`, `skepticism`, `uncertainty_awareness` |
| Primary model | `Qwen/Qwen2.5-7B-Instruct` |
| Contingent model | `NousResearch/Meta-Llama-3-8B-Instruct` only if Manager separately approves |
| Steering methods | `CAA`, `ITI` |
| Prompt baselines | (i) ordinary/everyday-user prompt, (ii) strong best-of-set prompt |
| Intervention | `h' = h + α · s_m · u_m` at the headline-frozen layer/direction for method `m` |
| α grid | `{2, 4, 6, 8, 12, 16, 24}` |
| α policy | composition-DEV re-selection; α selected on DEV only, TEST one-shot |
| TEST statistic | paired item-cluster bootstrap, B=10000, two-sided 98.33% Bonferroni CI |
| Superiority margin | `δ = 0.05` in each axis's original outcome units |
| Target power description | pre-registered target MDE ≤ 0.06; see §7 |

### 2.1 Prompt baselines

Two prompt-alone baselines are measured for every axis × method × model cell:

1. **Ordinary / average prompt (`ordinary`)** — intended to represent an everyday user who can express
   the desired behavior but does not engineer prompts. Freeze-candidate texts:
   - deliberation: "Please think carefully before answering."
   - skepticism: "Please check the claim carefully before answering."
   - uncertainty_awareness: "Please state your confidence and mention if you are unsure."
2. **Strong best-of-set prompt (`strong`)** — the already-authored 16-prompt strong bank used by the
   headline protocol (`data/strongest_prompts/<axis>.jsonl`). The prompt identity must be frozen before
   execution using the existing headline DEV-selection convention or an already-recorded headline winner.

No prompt is optimized on TEST. If Manager changes any ordinary text or strong-prompt identity before
freeze, the changed value must be recorded here before any DEV/TEST generation.

---

## 3. Data, split, and item identity

- Use the same task families and scorers as the frozen C2b adjudicator:
  - deliberation → GSM8K-style arithmetic/reasoning accuracy.
  - skepticism → false-premise / sycophancy rejection rate.
  - uncertainty_awareness → per-item `1 − Brier`, with parseability and calibration diagnostics.
- Draw fresh item pools disjoint from the prior headline TEST rows whenever the upstream datasets allow it.
  If an axis cannot supply the target fresh N, the run is **not silently downsampled**; Manager must choose
  between reducing scope, reporting lower power, or adding an alternate frozen pool before execution.
- Split per axis with `split_seed = 20260818` into DEV and TEST:
  - DEV: 200 items/axis.
  - TEST: 400 items/axis.
  - Total target: 600 items/axis, 1800 items/model.
- DEV and TEST are zero-overlap at item-id/hash level. The manifest must include item IDs, text hashes,
  split labels, axis, and source dataset revision.
- DEV may be used **only** to select α for each axis × method × prompt-baseline × model cell and to enforce
  the coherence eligibility rule. TEST is generated once after α is frozen.

---

## 4. Steering, α selection, and frozen directions

The composition arm reuses the headline-frozen directions and layers. It does not re-extract directions
unless the implementation cannot recover the frozen direction artifact; in that case execution stops and
returns to Manager.

For each axis × method × prompt-baseline × model:

1. Generate DEV `prompt alone`.
2. Generate DEV `prompt + steer` for every α in `{2,4,6,8,12,16,24}`.
3. Exclude α values failing the coherence gate (§8).
4. Select `α*` on DEV by highest mean paired improvement over prompt alone; ties choose the smaller α.
5. Freeze `α*` in the run manifest before any TEST generation.
6. Generate TEST `prompt alone` and TEST `prompt + steer` exactly once using `α*`.

Substitution α values from E-0005/E-0006 are not reused because α optimality can change under prompt
composition. This mirrors the 512-DEV lesson: do not import a short-output or substitution-tuned setting
into a different estimand.

---

## 5. Generation settings

| Axis | `max_new_tokens` | Rationale |
|---|---:|---|
| deliberation | 512 | Avoids the 64-token floor that can structurally suppress GSM8K reasoning. |
| skepticism | 192 | Allows rejection plus explanation; truncation tracked. |
| uncertainty_awareness | 192 | Allows answer + numeric confidence + brief caveat; truncation and parseability tracked. |

Shared settings unless the existing frozen runner requires an equivalent field name:

- `k = 5` samples/item/condition.
- `temperature = 0.7`, `do_sample = true`, fixed canonical item/sample order.
- `batch_size` may be implementation-tuned for memory but must be recorded in the config hash.
- Generation seeds derive deterministically from `run_seed = 20260818`, axis, method, model,
  prompt-baseline, condition, item id, sample index, and α. Identity keys must include all of those fields
  to prevent cache collisions.

---

## 6. Outcomes and scoring

Primary outcome units are exactly the frozen C2b units:

- deliberation: accuracy in `[0,1]`.
- skepticism: false-premise rejection rate in `[0,1]`.
- uncertainty_awareness: `1 − (confidence − correct)^2` in `[0,1]`.

The uncertainty arm must additionally report:

- token-normalized score summaries;
- format-compliance rate;
- parseable-confidence rate;
- missingness by condition;
- complete-case and adversarial missingness-bound sensitivity.

No missingness imputation may create a positive primary result. If parseability or differential missingness
exceeds the thresholds in §9, the affected uncertainty cell is reported as missingness-limited or invalid,
not as a pass.

---

## 7. Target N and MDE

The target is **MDE ≤ 0.06** for the paired superiority estimand. This protocol therefore targets
`N_TEST = 400` items/axis/model with `k=5`. Using the same normal-approximation convention as the post-hoc
TOST/MDE table (`z_98.33% ≈ 2.394`, `z_80% ≈ 0.842`), this design reaches MDE ≤ 0.06 when the empirical
item-level paired-difference SD is ≤ approximately 0.37:

```text
MDE_80% ≈ (2.394 + 0.842) · SD_item_diff / sqrt(N_TEST)
```

After TEST, the report must publish the realized MDE per cell/axis. If realized MDE exceeds 0.06, the
result is explicitly labeled **underpowered for the preregistered MDE target**. There is no post-TEST
top-up without a new preregistration.

---

## 8. Adjudication and decision rule

Reuse the frozen C2b adjudicator logic unless a field name must be adapted for `prompt + steer`:

1. For each axis × method × model × prompt-baseline, compute paired per-item differences
   `d_i = outcome_i(prompt + steer) − outcome_i(prompt alone)` on TEST.
2. Bootstrap items as clusters (`B = 10000`, `bootstrap_seed = 20260819`).
3. Use the two-sided `1 − 0.05/3 = 98.33%` CI for Bonferroni correction over the three axes within each
   method × model × prompt-baseline family.
4. A cell **PASSES** iff:
   - CI excludes 0 with lower bound > 0;
   - `mean(d_i) ≥ δ = 0.05`;
   - the winning α passes the coherence gate;
   - missingness/format gates pass.

Decision labels are per prompt-baseline:

- **COMPOSITION_GAIN_SUPPORTED:** at least one method has ≥1 axis PASS and the exact axes/methods are named.
- **NO_INCREMENT_DEMONSTRATED:** all axes fail while realized MDE ≤ 0.06 for the relevant cell family.
- **UNDERPOWERED_OR_INVALID:** MDE target not met, coherence fails, or missingness gates fail.

No aggregate "slider works" claim is allowed unless both ordinary and strong baselines are reported
separately. Ordinary-baseline gains and strong-baseline gains answer different reviewer concerns.

---

## 9. Coherence, missingness, and exclusion rules

- **Coherence:** reuse the C2b degeneracy/repetition gate: steered degeneracy ≤ `1.5×` prompt-alone baseline
  for the same axis/model/prompt-baseline, with the same epsilon/floor convention as the frozen adjudicator.
  α values failing on DEV are ineligible; TEST cells failing coherence are invalid.
- **Truncation:** deliberation outputs truncated before an answer are missing; pervasive truncation invalidates
  the axis rather than justifying post-hoc length changes.
- **Format and parseability:** uncertainty confidence must be parseable under the pre-run parser. Maximum
  missingness: 2% absolute per condition or 1% differential between prompt-alone and prompt+steer. Above this,
  report missingness-limited plus adversarial bounds; do not impute a pass.
- **No silent exclusions:** every item removed from primary analysis must have a pre-registered exclusion
  code (`duplicate`, `source_unavailable`, `parser_invalid_pre_generation`, `generation_missing`,
  `truncated_answer`, `coherence_fail`, `format_missing`). Exclusions are counted in the manifest.
- **No TEST peeking:** after TEST generation starts, α, prompt text, item pool, parser, coherence threshold,
  N, bootstrap seed, and pass rule are locked.

---

## 10. Outcome-neutral reporting contract

All three outcomes are publishable and must be reported honestly:

1. **CI includes 0:** adding steering to a user prompt shows no detectable incremental gain. This strengthens
   the negative boundary result for the tested slider composition regime.
2. **CI lower bound > 0 and mean ≥ δ:** steering has value as augmentation for the named axis/method/model/
   prompt-baseline. This is a new additive finding and does not erase the frozen substitution conclusion.
3. **Underpowered/invalid:** report realized MDE, invalidity reason, and the cheapest discriminating next step.

This protocol must not be tuned to "make the experiment succeed." Negative, positive, and underpowered
outcomes all preserve the paper's evidence discipline.

---

## 11. Artifact lineage

Required artifacts before any paper use:

- preregistration: this file at its freeze commit;
- experiment-registry entry: `composition-a-qwen-20260818-0001`;
- frozen item manifest with hashes and DEV/TEST labels;
- frozen prompt manifest with ordinary texts and strong prompt IDs;
- α-selection DEV report with no TEST metrics;
- TEST results JSON containing per-item paired outcomes and missingness codes;
- adjudication summary with bootstrap CIs, MDE, coherence, and format gates;
- independent hostile audit before claim-ledger/evidence-ledger promotion.

Manual table/prose numbers are forbidden; any paper table must be generated from the TEST JSON and manifest.

---

## 12. Compute estimate for Manager approval

Approximate generation count per model:

- Prompt-alone ordinary + strong for all items: `2 × 1800 × 5 = 18,000`.
- DEV α sweep: `2 methods × 2 baselines × 7 α × 600 DEV items × 5 = 84,000`.
- TEST selected α: `2 methods × 2 baselines × 1200 TEST items × 5 = 24,000`.
- **Total:** about **126,000 generations/model**, plus direction loading/extraction checks.

Because deliberation uses 512 generated tokens and the other axes use 192, cost is much higher than the
64-token headline run. Conservative estimate:

- **Qwen-only:** ~18–30 GPU-hours on an A800/4090-class 24–80 GB box, depending on batching and cache reuse.
- **Qwen + Llama:** ~40–70 GPU-hours total including model loading, Llama lower throughput, and audit reruns.

These are estimates for approval only. No GPU is authorized by this preregistration.

---

## 13. Freeze checklist

Before execution, Manager must confirm:

- [ ] ordinary prompt texts frozen or edited and frozen;
- [ ] strong prompt IDs frozen for each axis;
- [ ] direction artifacts and layers recoverable for Qwen CAA/ITI;
- [ ] fresh item pools can satisfy 600 items/axis with DEV/TEST zero overlap;
- [ ] GPU budget approved for Qwen-only;
- [ ] Llama explicitly deferred unless Manager later approves;
- [ ] implementation/audit plan exists before any TEST run;
- [ ] this document's freeze commit is recorded in the registry.
