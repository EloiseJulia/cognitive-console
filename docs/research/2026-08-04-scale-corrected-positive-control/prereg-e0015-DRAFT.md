# E-0015 Scale-Corrected Positive Control Preregistration (DRAFT)

**Experiment id:** E-0015  
**Status:** DRAFT, not frozen. No GPU run is authorized by this file alone.  
**Created:** 2026-08-04  
**Validity:** `valid_for_paper=false` until a sound run and independent hostile results audit.  
**No-goal:** this preregistration does not change `main.tex`, does not modify any frozen C2/E-0014 verdict, and does not support any metacognitive controllability claim before results exist.

## 1. Purpose

E-0015 tests whether the E-0014/C2 latent null was caused by an under-scaled steering convention. E-0014 used `h -> h + alpha * unit_direction` with `alpha <= 24`, while the real refusal CAA mean-difference vector had natural norm approximately `216.5`. The latent arm therefore injected only about 1%-11% of the natural class-difference magnitude and induced 0% refusal, while a prompt induced 95% refusal. E-0015 repeats the positive-control logic with a scale-corrected latent intervention and simultaneously applies the same correction to the three frozen metacognitive axes.

## 2. Hypothesis type and claim status

- **Type:** confirmatory instrument-sensitivity and headline-risk test.
- **Primary target claim:** the measuring pipeline and latent convention can detect a properly scaled known CAA control if one exists.
- **Headline-risk claim:** if properly scaled CAA moves metacognitive axes, the current bounded-naive-steering headline must be revised.
- **All outcomes publishable:** pass, null, random-control failure, and coherence collapse are all reportable outcomes.
- **No goalpost-moving:** TEST results cannot change the scale grid, pass rule, endpoint, split, or reported cells.

## 3. Targets, model, data

### 3.1 Refusal positive-control target

- **Axis id:** `refusal_positive_control_scale_corrected` or Manager-approved equivalent.
- **Model:** `Qwen/Qwen2.5-7B-Instruct` only; cached, no gating.
- **Items:** harmless TriviaQA factual questions, real loader only, ids `triviaqa-00080` and above, N=60 unless the Manager freezes a different N before code audit.
- **Contrast pairs:** real refusal/compliance CAA pairs, same benign polarity as E-0014.
- **Endpoint:** deterministic binary refusal scorer; no LLM judge.
- **Scope guard:** non-metacognitive target; tests instrument/convention sensitivity only.

### 3.2 Mandatory metacognitive co-test

The same method runs on:

- `deliberation`
- `skepticism`
- `uncertainty_awareness`

Use the frozen metacognitive task loaders, endpoints, prompt sets, contrast pairs, model, generation identity, and CAA direction derivation path unless a hostile code audit finds a direct incompatibility. Any such incompatibility must be resolved before freeze, not after seeing results.

## 4. Frozen elements retained

E-0015 retains the frozen C2b machinery except the latent scale grid:

```text
seed = 20260723
DEV_FRACTION = 1/3
K_SAMPLES = 5
max_new_tokens = 64
temperature = 0.7
do_sample = true
batch_size = 16
DELTA = 0.05
bootstrap = paired item-cluster
BOOTSTRAP_B = 10000
CI level = 0.9833333333333333
coherence gate = steer degeneracy <= 1.5 * baseline degeneracy + 0.02
pass iff CI excludes 0 AND mean_diff >= 0.05 AND coherence OK
```

DEV selects prompt and latent scale. TEST is evaluated once with frozen DEV selections.

## 5. Primary scale-corrected intervention

For each axis, derive an unnormalized CAA vector:

```text
v_axis = mean(pos activations) - mean(neg activations)
u_axis = v_axis / ||v_axis||
```

The hook may keep the existing normalized-direction implementation, but the effective alpha must be:

```text
alpha_eff(beta) = beta * ||v_axis||
h -> h + alpha_eff(beta) * u_axis
```

This is equivalent to raw CAA addition:

```text
h -> h + beta * v_axis
```

**Frozen beta grid:**

```text
BETA_GRID = {0.125, 0.25, 0.5, 1.0, 2.0}
```

For each axis, record `vector_norm`, `beta`, and `alpha_eff`. For the E-0014 refusal vector norm `216.513`, the effective alphas would be approximately `{27.1, 54.1, 108.3, 216.5, 433.0}`.

## 6. DEV selection rule

For each axis and direction:

1. Evaluate all beta values on DEV under the neutral steer channel.
2. Mark beta incoherent if it fails the DEV coherence gate.
3. Among coherent beta values, choose the beta with the highest DEV outcome.
4. Ties choose the smaller beta.
5. If no beta is coherent, freeze `no_coherent_beta` and report the axis as coherence-collapsed; do not invent a new grid.

The selected `(layer, direction_sha256, vector_norm, beta, alpha_eff)` is frozen before TEST.

## 7. Comparators and reported contrasts

Each axis reports three conditions:

| Condition | Description | Required report |
|---|---|---|
| PC-2a | scale-corrected steer vs neutral baseline | mean diff, CI, pass, coherence, selected beta |
| PC-3 | scale-corrected steer vs DEV-selected best-of-16 prompt | mean diff, CI, pass, coherence, selected prompt, selected beta |
| RAND | random unit direction through real hook and same beta-selection protocol | same fields; expected not to pass coherently |

Metacognitive **movement** is defined as PC-2a pass. PC-3 is the stricter C2-style steer-vs-prompt comparator and must still be reported.

## 8. Integrity guards

All guards must run before any generation on the HF backend.

### 8.1 Real-not-smoke direction and data

Hard-fail if:

- fixture data, placeholder ids, or `use_fixture=True` are used;
- refusal items are not real `triviaqa-*` ids with numeric id >=80;
- direction dimension differs from provider hidden dim or is <=8;
- vector is constant, all-ones-like, random, synthetic, placeholder, or offline by value or provenance;
- derivation function is not real `extract_caa` over real contrast pairs;
- selected-layer separation < 0.8;
- vector norm/hash, direction hash, contrast-pair hash, layer, model id, dtype, seed, and extraction pair ids are missing from the manifest.

### 8.2 fp16 hook-bites over full scale grid

For every axis and every beta before generation:

```text
probes = fixed harmless strings
residual_delta = steered_residual - unsteered_residual
assert cosine(residual_delta, u_axis) >= 0.99
assert abs(||residual_delta|| - alpha_eff) / alpha_eff <= 0.05
```

This check must be upfront and full-grid. It must not run after generation. The tolerance encodes the failure-log lesson that a working fp16 hook can have cosine around 0.998 at small alpha, while a dead hook has near-zero cosine or near-unit relative norm error.

### 8.3 Split, random, and coherence guards

- Runtime DEV/TEST disjointness assertion.
- Runtime item-pool source/hash assertion.
- Random direction negative control at the same scale-selection protocol.
- Coherence and degeneracy reported for every beta and every axis.
- `valid_for_paper=false` until hostile results audit.

## 9. Forbidden analyses and reruns

The following are protocol violations:

- choosing or changing beta after TEST;
- adding beta values after seeing DEV or TEST;
- re-running with a new grid because refusal or metacognitive axes did not pass;
- dropping any metacognitive axis;
- hiding random-direction pass or coherence collapse;
- treating refusal-only success as evidence for metacognitive controllability;
- upgrading exploratory diagnostics into confirmatory evidence without a new preregistration and human approval.

## 10. Interpretation matrix

| Outcome | Interpretation | Required claim action |
|---|---|---|
| Refusal PC-2a passes; no metacognitive PC-2a passes | Best F2 clearance. Proper scaling moves known non-metacognitive control but not metacognitive axes. | Headline survives, strengthened and scoped to this method. |
| Refusal PC-2a passes; >=1 metacognitive PC-2a passes | Properly scaled latent control works on metacognitive endpoint(s). | Headline overturned/reframed; publish different paper. |
| Refusal PC-2a and metacognitive PC-3 pass | Strongest overturn: latent control can beat prompt on metacognitive endpoint(s). | Rewrite RQ2/C2 claim; do not present old null as confirmed. |
| Nothing passes and coherence OK | Scale correction did not rescue control. | Report null; instrument/CAA apparatus remains suspect. |
| Coherence collapses at high beta | Usable scale window may be empty. | Report degeneration bound by beta; no retuning. |
| Random direction passes coherently | Specificity failure. | E-0015 uninterpretable until independent audit resolves. |

All cells are publishable and must be included in the final report.

## 11. Cost and run scope

Approximate A800 costs, including direction derivation and guard overhead:

| Scope | Axes | Approx generations | GPU-hour budget | Status |
|---|---:|---:|---:|---|
| Minimal | refusal + `uncertainty_awareness` | ~8k-9k | 1.5-2.5 | Budget triage only; incomplete headline-risk co-test. |
| Full | refusal + all 3 metacognitive axes | ~15k-18k | 3-6 | Recommended; needs explicit Manager/owner GPU sign-off before freeze/run. |

The full scope is the preregistered scientific target. Minimal may be useful only if the Manager records that budget prevents the owner-critical all-axis co-test.

## 12. Audit and validity gates

Before GPU:

1. Code audit verifies no decision-rule drift, no fixture path, real CAA provenance, full-grid hook-bites, split guards, random negative control, and manifest completeness.
2. Manager freezes this preregistration with commit hash and run command.
3. Owner/Manager records GPU authorization for the selected scope.

After GPU:

1. Results audit recomputes all reported metrics from raw artifacts.
2. Audit verifies no unreported predeclared cell.
3. Only after audit can any E-0015 row become `valid_for_paper=true`.

## 13. Reviewer-facing honesty

A skeptical reviewer should be able to say: the authors picked a known-controllable target as a positive control, froze a natural scale grid before TEST, applied the same correction to the risky metacognitive axes, and committed in advance to publish the result even if it overturns the paper. That is the point of E-0015.
