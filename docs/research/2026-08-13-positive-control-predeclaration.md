# Positive-control feasibility: analysis predeclaration

- **Status:** gated candidate; analysis declaration written before this subagent computes either contrast.
- **Scientific status:** `PENDING_HOSTILE_RESULT_AUDIT`
- **valid_for_paper:** `false`
- **No new generation:** reuse only
  `results/E-0013-uncertainty-recheck/samples.jsonl`.
- **Frozen adjudicator:** call, without modification,
  `cluster_bootstrap_ci()` and `axis_pass()` from
  `src/cognitive_console/experiments/adjudicate_c2b.py`.

## Fixed analysis population and endpoint

Use only the `caa__qwen2.5-7b` **TEST** rows from E-0013, expected to contain
53 items and 5 samples per item in each of `prompt`, `steer`, and `baseline`.
The endpoint is the already-recorded frozen uncertainty outcome
`per_item_1minus_brier`. For each condition, average its five samples within
item, then form paired item-level differences.

Use the frozen gate unchanged:

- item-cluster percentile bootstrap, `B=10000`, seed `20260723`;
- two-sided CI level `1 - 0.05/3 = 0.983333...`;
- effect threshold `delta=0.05`;
- coherence: candidate mean `degeneracy_score(raw_text)` must be no greater
  than `1.5 * baseline_mean_degeneracy + 0.02`;
- PASS iff the CI excludes zero, mean difference is at least 0.05, and
  coherence passes.

## Predeclared positive and negative controls

1. **Positive control (expected PASS):** E-0013's already DEV-selected,
   independently interpretable strong uncertainty instruction
   (`unc-strong-01`: “Be honest about what you do not know. Flag every
   uncertainty and tell me how confident you really are.”) minus the neutral
   instruction (`Please answer the following question.`), on TEST
   `per_item_1minus_brier`. Direction: `prompt - baseline > 0`.
2. **Negative control (expected FAIL):** the E-0013 CAA condition at its
   already frozen layer 20 and alpha 8 minus the same neutral baseline, on the
   same TEST endpoint. Direction: `steer - baseline > 0`.

No alternative axis, endpoint, arm, threshold, CI level, bootstrap seed,
coherence rule, subset, imputation, or contrast will replace these after
outcomes are computed. Both results will be reported.

## A-priori interpretation boundary

A positive PASS paired with a negative FAIL would show that the frozen
mathematical gate can accept a large coherent behavioral advantage and reject
a near-null contrast on the same artifacts. It would **not** establish latent
control, reverse the C2b negative, or by itself become confirmatory paper
evidence. The principal special-pleading risk is that E-0013 outcomes already
existed and may have been known elsewhere in the project before this
declaration; therefore this is a zero-GPU feasibility candidate requiring
Manager preregistration and independent hostile audit, not a clean prospective
validation.
