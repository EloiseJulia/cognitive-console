# 64-token deliberation artifact audit

Date: 2026-08-11
Scope: E-0006 `arm_full`, deliberation only, CAA/ITI × Qwen/Llama.

## Finding

The retained artifacts **cannot establish** exact generated-token counts, the
fraction mechanically stopped by `max_new_tokens=64`, parser-failure rates,
condition differences in truncation, or the truncation–correctness relationship.
Therefore the reviewer claim that the 64-token cap severely distorted
deliberation is **not supported by the retained evidence, but it is also not
ruled out**.

This is an unresolved construct-validity sensitivity, not grounds to alter the
frozen E-0006 `0/12` record.

## What exists

- Four frozen result JSON files under `results/arm_full/cell_*/`.
- Each deliberation row retains 40 TEST item means for prompt and steer, but not
  raw generations or per-sample parse status.
- The arm summary says transcript directories existed at run time. The bank
  commit explicitly gitignored `results/arm_full/**/transcripts/`, checkpoints,
  and C1 caches.
- A later artifact, `results/E-0014-positive-control/pc0_pc1_reanalysis.json`,
  records `arm_full_transcripts_present: false`.
- Read-only inspection of both remote copies under `~/cc_l0/repo` and
  `~/cc_l0/e0016-run-20260805` found the frozen JSON/manifests but no
  `arm_full/**/transcripts/*.jsonl`.

The frozen deliberation TEST means are:

| cell | prompt accuracy | steer accuracy | steer−prompt | 98.33% CI | PASS |
|---|---:|---:|---:|---:|---|
| CAA×Qwen | 0.020 | 0.035 | +0.015 | [-0.040, +0.070] | no |
| CAA×Llama | 0.015 | 0.040 | +0.025 | [-0.030, +0.075] | no |
| ITI×Qwen | 0.020 | 0.040 | +0.020 | [0.000, +0.055] | no |
| ITI×Llama | 0.015 | 0.030 | +0.015 | [-0.040, +0.060] | no |

These nonzero accuracies prove that some generations contained a parseable,
correct numeric answer. A zero score, however, conflates an incorrect numeric
answer with no parseable final number, so it cannot recover parser failures.

## Why the old transcript schema would still be inadequate for exact counting

At the banked code path, transcripts stored decoded generation text and:

```python
maybe_truncated = len(text.split()) >= max_new_tokens
```

That is a whitespace-word heuristic, not a tokenizer count or stop reason.
Generation decoded continuation IDs with `skip_special_tokens=True`; EOS and
batch padding were discarded. Retokenizing decoded text later would therefore
not reconstruct exact original sequence lengths or distinguish:

1. exactly 64 generated tokens ending in EOS;
2. exactly 64 tokens stopped by the token budget; and
3. semantic truncation, which neither count establishes by itself.

The evidence-ledger statement `trunc=0/empty=0` is thus insufficient to answer
the present criticism without its raw transcript artifact and exact definition.

## Minimum resolving action

The historical config fingerprints prove the first-60 ordered GSM8K index-ID
pool and its sorted 40-ID TEST split, but E-0006 did not retain a dataset
revision or item-payload hash. The outcome-blind recovery and exact IDs are
recorded in `e0006-item-identity.json`; the payload is honestly labelled a
revision-pinned reconstruction until the 64-token outcome reproduction gate
passes.

After an independent re-audit recommends `FREEZE`, run the DRAFT E-0017
companion. It captures token IDs/EOS reasons, verifies exact 64-token per-item
and aggregate reproduction, and performs one sealed analysis. Exact model
revisions plus config/tokenizer/generation-config/all-shard hashes, one
UUID-selected idle A800 in float16 with no CPU fallback, structured owner and
audited-commit authorization, a host-global canonical-attempt registry,
fixed-batch checkpoints, max-T familywise inference, item-cluster continuation
CIs, and raw/spec/output seals fail closed. It does not reselect DEV settings
or replace E-0006.

The registry path is fixed under `/var/lib/cognitive-console/host-control` by
E-0017 + audited commit, not by authorization or output path.
Repository/results/frozen-tree redirection is forbidden. `LOCKED` seals never
adopt an existing analysis artifact, and `None→number` frozen-parser
transitions count as semantic materiality.

The frozen source is additionally pinned to repository `results/arm_full` and
the preregistered SHA-256 values of its arm summary plus four cell results,
verified before JSON loading and repeated in authorization. Stop/non-stop
accuracy is item-conditional with item-cluster 95% CIs, not sample-pooled.

Independent audit is required before any paper wording changes.
