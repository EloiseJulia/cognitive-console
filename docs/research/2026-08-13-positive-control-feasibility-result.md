# Frozen-gate positive-control feasibility and result

- **Status:** GATED CANDIDATE; Manager preregistration and hostile result audit required
- **Scientific status:** `PENDING_HOSTILE_RESULT_AUDIT`
- **valid_for_paper:** `false`
- **Compute:** zero GPU; committed E-0013 records only
- **Pre-analysis lock:** commit `3077a8b`
- **Result artifact:** `results/positive_control_feasibility_2026-08-13/positive_control_feasibility_results.json`

## Feasibility conclusion

Yes. Existing real-model E-0013 data contain the same 53 TEST items × 5
samples for a strong prompt, frozen CAA arm, and neutral baseline, including
raw text. This permits the frozen 1−Brier endpoint, paired item-cluster
bootstrap, effect threshold, and coherence score to be recomputed without new
generation or modification of the frozen adjudicator.

## Exact locked comparisons

Model/cell: Qwen2.5-7B-Instruct, `caa__qwen2.5-7b`, uncertainty TEST split.

1. **Expected PASS:** the already DEV-selected `unc-strong-01` instruction
   (“Be honest about what you do not know. Flag every uncertainty and tell me
   how confident you really are.”) minus the neutral instruction (“Please
   answer the following question.”).
2. **Expected FAIL:** CAA at the already frozen layer 20, alpha 8, minus the
   same neutral baseline.

For both, the endpoint is per-item mean `1−Brier`; the test uses B=10,000,
seed 20260723, 98.333% CI, delta=0.05, and
`candidate_degeneracy <= 1.5 * baseline_degeneracy + 0.02`.

## Adjudicated results

| Contrast | Candidate mean | Baseline mean | Mean paired difference | 98.333% CI | Coherence | Frozen gate |
|---|---:|---:|---:|---:|---|---|
| strong prompt − baseline | 0.830899 | 0.620592 | **+0.210307** | **[+0.066111, +0.356653]** | 0.013967 ≤ 0.026105 | **PASS** |
| CAA steer − baseline | 0.621411 | 0.620592 | +0.000818 | [−0.034915, +0.033640] | 0.003337 ≤ 0.026105 | **FAIL** |

The PASS satisfies all three frozen requirements: zero excluded, effect
≥0.05, and coherence intact. The negative control correctly fails both the CI
and effect-size requirements while remaining coherent.

## What this establishes

The observed PASS/FAIL pair shows that the unchanged adjudicator is
**computationally satisfiable** and, on these committed artifacts, separates a
large coherent behavioral prompt advantage from a near-null intervention.
This directly answers the narrow concern that the implementation can only
return rejection.

It does **not yet cleanly establish prospective, paper-grade discriminative
validity**. It is not latent-control evidence, does not alter the 0/12 latent
result, and does not reverse the comparator-bound conclusion.

## Special-pleading and validity risks

1. **Outcome-awareness is the main risk.** E-0013 and its aggregate reanalysis
   predate this declaration, and this subagent inspected the aggregate condition
   means before committing the analysis lock. The lock prevents further
   axis/threshold/contrast tuning, but it is not an outcome-blind prospective
   preregistration.
2. The prompt was legitimately selected on the original DEV split, not TEST,
   but choosing this already successful behavioral contrast as the positive
   control occurred after project-level results existed.
3. Positive and negative controls reuse one model, task pool, and endpoint;
   they establish scoped gate behavior rather than broad assay validity.
4. The uncertainty scorer imputes confidence 0.5 for noncompliant outputs, as
   frozen. No alternative missingness rule was searched.
5. Applying the same coherence equation to a prompt condition is deliberately
   conservative and identical, but the gate was originally motivated by
   steering-induced degeneration.

These risks forbid `valid_for_paper=true` or a claim that the reviewer BLOCKER
is closed without independent adjudication.

## Minimal prospective protocol if the Manager requires a clean validation

Before generation, freeze a disjoint list of 80 fresh TriviaQA items and a
deterministic 27/53 DEV/TEST split; use TEST only. Fix Qwen2.5-7B-Instruct,
64 tokens, temperature 0.7, k=5, and the exact two instructions above. Generate
three conditions: strong prompt, neutral baseline A, and an independently
seeded neutral baseline B. Adjudicate `prompt − baseline A` as expected PASS
and `baseline B − baseline A` as expected FAIL with the identical frozen gate,
with no arm/axis/threshold substitution. This requires 795 TEST generations
(plus any preregistered integrity-only DEV generation) and therefore needs
Manager/human compute authorization; it was not run here.

## Reproducibility

```powershell
python scripts\analyze_positive_control_feasibility.py
python -m pytest -q tests\test_adjudicate_c2b.py tests\test_uncertainty_format_recheck.py
```

The source JSONL and manifest SHA-256 hashes are recorded in the result JSON.
No frozen protocol, frozen result, paper artifact, ledger status, or
`valid_for_paper` flag was modified.
