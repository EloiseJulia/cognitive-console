# E-0015 Scale-Corrected Positive Control — Design

**Date:** 2026-08-04  
**Experiment id:** E-0015  
**Status:** DESIGN / DRAFT only. `valid_for_paper=false` until (1) frozen prereg, (2) sound GPU run, and (3) independent hostile results audit.  
**Scope:** doc-only design. This document does not change code, does not run experiments, and does not touch `main.tex`.

## 0. Why E-0015 exists

E-0014 established an uncomfortable but useful fact: the endpoint/statistics path is live for prompts, but the bounded latent convention was likely far too weak. The Qwen refusal CAA direction selected layer 27 with raw mean-difference norm `216.513`; the frozen convention in `generate.py` normalizes the direction and adds only `alpha * unit_direction`, with `alpha in {2,4,6,8,12,16,24}`. Thus the strongest E-0014 latent perturbation was only about `24/216.5 = 11%` of the direction's natural class-difference magnitude, and the smallest was below 1%. E-0014 then observed 0% refusal movement for latent steering while the prompt arm induced 95% refusal. Under the same bounded convention, the C2 metacognitive latent steer-vs-baseline effects were also near zero.

Therefore E-0014 cannot distinguish two worlds:

1. **Instrument/convention weakness:** the adjudicator never saw a properly scaled latent intervention.
2. **Substantive null:** even properly scaled latent control does not move the target or the metacognitive axes coherently.

E-0015 resolves this with a new frozen, scale-corrected preregistration. All outcomes below are pre-declared publishable; no run->tune->rerun is allowed.

## 1. Target and scope guard

### Primary positive-control target

- **Target:** refusal induction on harmless factual questions.
- **Items:** reuse the E-0014 real TriviaQA harmless pool discipline, with runtime assertion that all item ids are `triviaqa-*` and all numeric ids are `>=80`, disjoint from the frozen metacognitive `triviaqa-00000..00079` pool.
- **Direction data:** real CAA refusal/compliance contrast pairs from the E-0014 `refusal_positive_control` data path; no fixture, synthetic, random, or placeholder direction may reach the HF path.
- **Model:** `Qwen/Qwen2.5-7B-Instruct`, cached and ungated.
- **Endpoint:** deterministic binary refusal scorer, same endpoint family as E-0014; no LLM judge.
- **Scope guard:** this is a non-metacognitive target. It tests instrument/convention sensitivity, not metacognitive controllability.

### Mandatory headline-risk co-test

The exact same scale-corrected method must also be applied to the three frozen metacognitive axes:

1. `deliberation`
2. `skepticism`
3. `uncertainty_awareness`

This is not optional robustness. It directly tests whether E-0014's under-scaling threat also explains the headline C2 null.

## 2. Frozen adjudicator components retained

E-0015 changes only the latent perturbation scale grid. Everything else remains comparable to frozen C2b/E-0014:

| Component | Frozen value retained |
|---|---|
| DEV/TEST split | `DEV_FRACTION = 1/3`, fixed seed `20260723`, disjoint item ids |
| Samples | `K_SAMPLES = 5` per item |
| Endpoint decision | paired item-cluster bootstrap, `B = 10000` |
| CI | Bonferroni `0.9833333333333333` |
| Pass margin | `DELTA = 0.05` |
| Pass rule | CI excludes 0 AND mean diff >= 0.05 AND coherence gate passes |
| Coherence gate | steer degeneracy <= `1.5 * baseline + 0.02` |
| Generation identity | Qwen, `max_new_tokens=64`, temperature `0.7`, `do_sample=True`, batch size `16` |
| Prompt comparator | PC-2a neutral comparator and PC-3 best-of-16 prompt comparator, as in E-0014 |
| Random negative control | through the real hook at the same scale-selection procedure |

The scale grid replaces `ALPHA_GRID` for E-0015 only; the original bounded grid remains part of the historical C2/E-0014 record and must not be reinterpreted.

## 3. Scale correction: primary and secondary schemes

### 3.1 Primary scheme: raw-magnitude CAA dose grid

**Primary recommendation:** raw-magnitude CAA, implemented as an effective alpha grid over the unnormalized CAA mean-difference vector.

Let `v = mean(pos_activations) - mean(neg_activations)` at the selected layer and `u = v / ||v||`. Existing `SteerConfig.direction` normalizes its input, so raw-magnitude addition can be implemented without changing the hook by passing:

```text
h -> h + alpha_eff * u
alpha_eff = beta * ||v||
```

Equivalently, this is `h -> h + beta * v`.

**Frozen primary beta grid:**

```text
beta in {0.125, 0.25, 0.5, 1.0, 2.0}
```

For the E-0014 refusal direction (`||v|| = 216.513`), this yields effective alphas approximately:

```text
{27.1, 54.1, 108.3, 216.5, 433.0}
```

Rationale:

- `0.125x` brackets the previous maximum (`24`) and tests whether merely crossing the old ceiling is enough.
- `0.5x, 1x, 2x` are the principled natural class-difference magnitudes requested by the owner.
- The grid is monotone, small, predeclared, and not chosen after seeing TEST.
- DEV selects only among these frozen doses using the existing coherence gate and outcome criterion.

### 3.2 Secondary scheme: residual-norm-matched reporting, not a second confirmatory family

For interpretability, every run should record residual-norm ratios on DEV and TEST:

```text
injection_norm / median_token_residual_norm_at_layer
```

This is a **secondary descriptive calibration**, not a separate confirmatory scale search. It prevents reviewer confusion about whether `beta=1` is tiny or enormous relative to the residual stream. It should not add another run family unless the Manager/owner explicitly freezes a separate E-0016.

### 3.3 Arditi et al. reference discipline

E-0015's primary scheme is the benign addition half of the Arditi et al. refusal recipe: a difference-of-means refusal direction, added to induce refusal. Projection ablation / refusal suppression is not included because it is dual-use and outside this positive-control scope. The design uses Arditi-style addition as reference practice, while retaining this repository's frozen scorer/adjudicator.

## 4. DEV-only scale selection and TEST lock

For each axis and each direction:

1. Derive the raw CAA vector `v` on real contrast pairs only.
2. Compute the frozen beta grid and effective alphas before generation.
3. Run all cheap fail-fast guards before any generation.
4. On DEV only, evaluate each beta under the neutral steer channel.
5. Exclude any beta that fails the DEV coherence gate.
6. Select the coherent beta with the highest DEV steer outcome. Ties choose the smaller beta.
7. Freeze `(axis, layer, direction_sha256, vector_norm, beta, alpha_eff)` before TEST.
8. Run TEST once.

Forbidden:

- choosing beta after seeing TEST;
- adding a new beta after seeing any result;
- re-running with a different scale because a desired cell failed;
- dropping a pre-declared axis or comparator from the report;
- reporting only the favorable comparator.

## 5. Conditions and comparators

For each target/axis, E-0015 reports:

| Label | Comparator | Purpose |
|---|---|---|
| PC-2a | scale-corrected steer vs neutral baseline | Detect whether latent control moves the endpoint at all |
| PC-3 | scale-corrected steer vs DEV-selected best-of-16 prompt | Test the original C2-style steer-vs-prompt bar |
| RAND | random unit direction through the same hook and scale-selection protocol | Specificity / degeneracy negative control |

For metacognitive axes, the primary headline-risk flag is **PC-2a movement**. PC-3 is still reported because it is the original C2 comparator, but if a metacognitive axis moves vs baseline under proper scaling, the headline must be revised even if it does not beat the strongest prompt.

## 6. Full interpretation matrix — all cells publishable

| Refusal target | Metacognitive axes | Coherence | Interpretation | Paper consequence |
|---|---|---|---|---|
| Moves | No metacognitive axis moves vs baseline; none beats prompt | OK | Proper scaling makes the known non-metacognitive control move, but not the three metacognitive axes | Strongest F2 clearance. Headline survives and strengthens: the null is not just a weak-scale artifact. |
| Moves | At least one metacognitive axis moves vs baseline | OK | Properly scaled latent control works on metacognitive endpoints | Headline overturned. The honest paper becomes: bounded naive steering failed, but scale-corrected latent control can work. Publishable, but different claim. |
| Moves | Metacognitive axes move vs baseline and at least one beats prompt | OK | Strongest overturn: scale-corrected latent control can exceed prompt comparator | Rewrite C2/RQ framing; do not present the old non-surjective headline as confirmed. |
| Does not move | No metacognitive axis moves | OK | Scale correction did not rescue refusal or metacognitive control | Hardens the null but implicates direction/hook/target apparatus; report as failed positive-control bet, not hidden failure. |
| Does not move | Some metacognitive axis moves | OK | Refusal target was a bad control but metacognitive scaling has an effect | Headline still changes; refusal positive-control rationale fails and must be disclosed. |
| Any | Any | High-scale coherence collapse | Degeneration bound | Report beta-specific degeneration; do not tune around it. If all high scales collapse and low scales do not move, E-0015 says the usable scale window may be empty. |
| Random direction passes | Any | Any | Specificity failure | BLOCKER for interpreting E-0015 until audited; strong random may degrade coherence and should normally be caught by the coherence gate. |

Definitions:

- **Moves:** PC-2a passes the frozen rule with mean diff >= 0.05 and coherence OK.
- **Beats prompt:** PC-3 passes the same rule.
- **Coherence collapse:** no beta survives DEV coherence, or TEST coherence fails at the frozen beta; this is an outcome, not a reason to rerun.

## 7. Integrity guards

E-0015 must reuse and extend E-0014's guards, explicitly addressing the E-0012 and fp16 lessons.

### 7.1 Real-not-smoke provenance

Hard-fail on HF if any of the following occurs:

- `use_fixture=True` or fixture-schema item ids;
- item ids are not real TriviaQA ids or violate the `id >= 80` disjointness rule for refusal;
- direction dimension is placeholder-sized or not equal to provider hidden dim;
- direction is constant, all-ones-like, random, synthetic, offline, or placeholder by provenance;
- derivation function is not real `extract_caa` over real contrast pairs;
- selected-layer separation is below the preregistered floor `0.8`;
- vector norm, direction hash, contrast-pair hash, layer, pair ids, model id, dtype, and seed are not written before generation.

### 7.2 fp16-robust hook-bites — full grid, upfront

Before any generation, for every axis and every beta in the frozen grid:

```text
capture steered - unsteered residuals on fixed probe prompts
assert cosine(delta, u) >= 0.99
assert relative_norm_error <= 0.05
```

The check must run over the **full scale grid**, not one convenient scale, and must run **before** any expensive generation. This directly encodes the 2026-08-04 failure-log lesson: fp16 cosine around `0.998` at small alpha is a working hook, not a failure; cosine `0.99` plus relative norm `0.05` catches dead hooks without aborting valid fp16 runs.

### 7.3 Runtime split and item-pool guards

- DEV and TEST ids must be disjoint at runtime.
- Refusal items must be `triviaqa-00080` or higher.
- Metacognitive axes must use their frozen loaders/splits and must not silently substitute fixtures.
- All loaded data source hashes must be in the manifest.

### 7.4 Random-direction negative control

For each axis, draw one random unit direction with the frozen seed offset and run it through the same hook and beta-selection protocol. It may become incoherent at high scale; that is exactly why the coherence gate must be reported at every beta. If the random direction passes coherently, E-0015 is not interpretable without audit.

### 7.5 Degeneracy and completeness reporting

For every beta, report:

- DEV outcome;
- DEV degeneracy;
- DEV coherence OK/fail;
- selected beta and alpha_eff;
- TEST outcome, CI, pass flag;
- TEST degeneracy and coherence;
- refusal/metacognitive endpoint base rates;
- random-direction counterpart.

No pre-declared cell may be omitted from the final report.

## 8. Cost estimate on A800

Throughput anchor from prior Qwen runs is approximately 7 generations/s at 64 new tokens, but direction derivation, model loading, manifests, and guard checks dominate wall time. Estimates below include overhead.

Assume beta grid size 5, k=5, best-of-16 prompts, baseline, selected TEST cells, and one random-direction negative control per axis.

| Version | Axes | Approx generations | Estimated A800 GPU-hours | Sign-off |
|---|---:|---:|---:|---|
| Minimal viable | refusal + `uncertainty_awareness` | ~8k-9k | ~1.5-2.5 h | Needs Manager/owner confirmation that minimal is acceptable; it does **not** fully clear the mandatory 3-axis headline-risk co-test. |
| Full recommended | refusal + deliberation + skepticism + uncertainty_awareness | ~15k-18k | ~3-6 h | Should get explicit owner GPU sign-off before freezing/running because it exceeds the E-0014 budget and directly risks overturning the headline. |

The full version is scientifically preferred because the owner-critical co-test names all three metacognitive axes. Minimal is only a budget triage option and must be labelled incomplete for headline-risk clearance.

## 9. Novelty/falsification honesty

E-0015 is a **confirmatory instrument-sensitivity test**, not a fishing expedition. The target, scale grid, pass rule, interpretation matrix, and cost are frozen before TEST. The experiment is valuable precisely because it can falsify the current paper's headline.

How a skeptical reviewer reads outcomes:

- **Refusal moves, metacognitive axes do not:** credible evidence that the instrument can detect properly scaled latent control on a known target; remaining null on metacognition is more informative.
- **Refusal and metacognitive axes move:** the old headline was scale-limited. This is not a failure; it is a stronger, different paper about scale-corrected control and the limits of bounded naive steering.
- **Nothing moves:** either CAA addition is still not the right intervention or the apparatus is too brittle; report honestly and downgrade any assay-sensitivity claim.
- **Only random moves or coherence collapses:** the method lacks specificity or enters degeneration; do not claim controllability.

The preregistered interpretation prevents goalpost-moving: every possible cell changes a claim state, and none authorizes hiding a negative or inconvenient result.

## 10. Open decisions for Manager before freeze

1. **Run scope:** freeze full E-0015 now (recommended) or explicitly approve a minimal refusal+uncertainty-only triage run with incomplete headline-risk coverage.
2. **Movement definition:** approve PC-2a steer-vs-baseline pass as the primary metacognitive movement criterion, with PC-3 steer-vs-prompt as a stricter secondary comparator.
3. **Scale grid:** approve `{0.125, 0.25, 0.5, 1.0, 2.0} * ||v||` as the primary raw-magnitude grid.
4. **Secondary norm reporting:** require residual-norm ratio logging for every beta without making it a second scale-search family.
5. **Audit gate:** require hostile code audit before GPU and hostile results audit before `valid_for_paper=true`.
