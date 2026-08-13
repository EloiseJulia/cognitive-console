# E-0013b — Uncertainty missingness/format-compliance recheck (three unrechecked cells)

**Status:** `valid_for_paper=false`, `scientific_status=PENDING_HOSTILE_RESULT_AUDIT`
**Branch:** `feature/uncertainty-missingness-recheck`
**Type:** analysis of ALREADY-COLLECTED data — **NO new generation, NO GPU**.
**Candidate result for Manager audit — NOT blessed by this subagent.**

## 1. Question

The paper's "uncertainty favors the comparator" headline rests on all **four**
steer-vs-prompt uncertainty contrasts being negative under the frozen
0.5-confidence-imputation scorer. A reviewer flagged that a large
confidence-**parseability** asymmetry (E-0013 CAA-Qwen: parseable-confidence rate
steer 0.826 vs prompt 0.445) means the frozen scorer's 0.5 imputation could be
**systematically** scoring a condition with very different missingness — i.e. the
negative result might be a **scoring artifact**, not a behavioral finding.

E-0013 ran the complete-case vs adversarial all-generation missingness
decomposition for **only** the CAA-Qwen cell. The other **three** uncertainty
cells (ITI-Qwen, CAA-Llama, ITI-Llama) were never rechecked. This experiment
reproduces the **same** decomposition for those three cells.

## 2. Data source and method (recomputed from real artifacts)

- **Generations:** the frozen, already-collected transcripts
  `results/arm_full/cell_*/transcripts/uncertainty_awareness__test_{steer,prompt,baseline}__*.jsonl`
  (53 test items × 5 samples × 3 conditions = 265 rows/condition/cell). These are
  read **read-only** from the main checkout; **no frozen artifact was modified**.
- **format-compliant** ≡ `parse.parsed_confidence is not None` (per generation).
- **per-generation score** ≡ `sample_outcome` (the frozen 0.5-imputed per-generation 1−Brier).
- **Decomposition** = exact port of `scripts/run_uncertainty_format_recheck.py`
  (E-0013): condition parseable rates; complete-case (both steer & prompt parsed)
  paired steer−prompt point + item-cluster percentile bootstrap CI
  (`adjudicate_c2b.cluster_bootstrap_ci`, B=10000, seed=20260723, `cluster=True`);
  adversarial all-generation imputation bounds (dropped generations forced to the
  best/worst score for steer).
- **CI level:** primary **0.9833** (the frozen grid's Bonferroni 1−0.05/3 level);
  also reported at **0.95** (the level E-0013's recheck code actually used) as the
  reproduction anchor. Point estimates and bounds are CI-level-independent.

### Two independent validations (both pass)

1. **Method reproduction (exact):** running this decomposition on **E-0013's own**
   `samples.jsonl` reproduces `results/E-0013-uncertainty-recheck/reanalysis.json`
   **bit-for-bit** (`all_match = true`), including the bootstrap CI.
2. **Provenance:** the transcript-derived **as-run** 0.5-imputed steer−prompt delta
   reproduces the frozen grid `mean_diff` for **all four** cells to |diff| ≤ 4×10⁻⁵
   (caa-qwen −0.22767, iti-qwen −0.10276, caa-llama −0.07153, iti-llama −0.08402),
   confirming the transcripts are the true basis of the frozen grid claim.

> Note: E-0013 **re-generated** its samples (its log shows model loading, 166 s
> wall-clock), so decomposing the frozen transcripts is *more* faithful to the
> paper's actual grid than E-0013's re-run. The CAA-Qwen transcript numbers below
> agree directionally with E-0013 but are not bit-identical, as expected.

## 3. Per-cell results

Parseable = fraction of generations with a parseable `Confidence: X%`. Complete-case
= paired steer−prompt on item/sample rows where **both** conditions parsed.
Adversarial bounds = [least-favorable-to-steer, most-favorable-to-steer] imputation
of dropped (non-parseable) generations.

| Cell | parseable steer | parseable prompt | complete-case Δ (steer−prompt) | CI (0.9833) | excl 0? | n item-clusters / pairs | adversarial bounds | cross 0? |
|---|---|---|---|---|---|---|---|---|
| **ITI-Qwen** | **0.045** | 0.438 | −0.3488 | [−0.5875, −0.0588] | yes* | 4 / 6 | [−0.959, +0.558] | **yes** |
| **CAA-Llama** | **0.000** | 0.506 | **UNDEFINED** | — | — | 0 / 0 | [−0.945, +0.549] | **yes** |
| **ITI-Llama** | 0.155 | 0.506 | −0.0259 | [−0.234, +0.186] | **no** | 17 / 23 | [−0.842, +0.498] | **yes** |
| CAA-Qwen (E-0013 anchor, from transcripts) | 0.815 | 0.438 | −0.4432 | [−0.654, −0.220] | yes | 33 / 109 | [−0.507, +0.240] | yes |

\* ITI-Qwen's complete-case CI excludes zero but rests on only **4 items / 6
sample-pairs of 265** — uninterpretably underpowered; not a usable behavioral estimate.

At the 0.95 anchor level the complete-case verdicts are unchanged (ITI-Qwen
[−0.575, −0.123] excl 0; ITI-Llama [−0.202, +0.145] includes 0).

## 4. Robustness verdict

**The grid-wide "uncertainty favors the comparator" claim is NOT robust — it is
plausibly a missingness/scoring artifact.**

1. **All four cells' adversarial all-generation imputation bounds cross zero**
   (CAA-Qwen [−0.478, +0.250] per E-0013; the three here [−0.959, +0.558],
   [−0.945, +0.549], [−0.842, +0.498]). The sign of every cell's effect is
   determined by the **unobserved** confidence of dropped generations.
2. **In all three rechecked cells the steer condition is the high-missingness
   condition** (parseable 0.000–0.155 vs 0.44–0.51 for prompt). So ~85–100% of
   steer generations receive the frozen 0.5 imputation, and the negative as-run
   delta is dominated by imputed, not observed, confidence behavior. This is the
   **opposite** compliance direction to CAA-Qwen (where steering *raised*
   parseability), so the "four uniformly negative cells" headline masks
   qualitatively different — even opposite — compliance mechanics.
3. **The complete-case (both-parsed) analysis fails to deliver a robust negative in
   any of the three new cells:** CAA-Llama is UNDEFINED (0 parseable steer
   generations), ITI-Llama is NULL (CI comfortably includes 0), and ITI-Qwen is
   nominally significant but rests on 4 items / 6 pairs. Only **CAA-Qwen** retains a
   defensible complete-case harm (n=33 clusters). Thus **1 of 4** cells survives the
   decomposition as a clean behavioral negative.

**Bottom line for the paper claim:** the "uncertainty harm is uniform across the
2×2 grid" narrative does not survive the missingness decomposition. Three of four
cells offer no clean (complete-case) behavioral evidence of harm, and all four are
sign-unpinned under adversarial imputation because steering massively changes
confidence-format compliance. This is a MAJOR/BLOCKER-class concern to escalate.

## 5. Verified vs UNVERIFIED

- **All four cells VERIFIED** from real on-disk frozen per-generation transcripts.
  Nothing was fabricated. CAA-Llama's complete-case is reported **UNDEFINED**
  (0 parseable steer generations), which is a *computed structural result*, not
  missing data.
- No cell was UNVERIFIED: the raw per-generation confidence/format-compliance data
  exists on disk for every cell.

## 6. Reproduce

```
python scripts/run_uncertainty_missingness_recheck.py \
  --main-repo "C:\Users\v-elzhang\Desktop\MyFolder\cognitive console"
```

Writes `results/E-0013b-uncertainty-missingness/reanalysis.json`.

## 7. Caveats / scope

- Adversarial bounds are deliberately extreme (best/worst-case imputation); they
  establish only that the sign is **not identified** by the observed data, not a
  best estimate of the true effect.
- Complete-case is a "both-parsed" restriction; it can itself be biased if
  parseability correlates with item difficulty (selection). It is reported as one
  leg of the decomposition, exactly as E-0013 framed it — not as ground truth.
- This is exploratory and **not blessed**. It must pass an independent hostile
  result audit before any paper use.
