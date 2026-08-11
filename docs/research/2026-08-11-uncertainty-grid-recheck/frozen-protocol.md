# E-0013 four-cell uncertainty format/missingness recheck

**Status:** FROZEN by the owner's 2026-08-11 task authorization, pending
independent hostile code audit before any GPU use.

**Relationship to prior evidence:** additive recheck only. The audited
CAA×Qwen E-0013 files and all four frozen E-0006 scoring files are immutable
inputs and remain the authoritative original results.

## Transcript inventory

The committed repository contains the audited CAA×Qwen E-0013
`samples.jsonl`. It contains no corresponding E-0013 samples for the other
three cells. The frozen arm summary records that E-0006 transcript directories
existed at arm-run time, but they are absent from the committed tree, git
history, the current authorized A800 checkout, the wider `~/cc_l0` tree, and
the original `/root/autodl-tmp/cc/repo` path on that host. This inventory does
not establish that no offline backup exists; the analyzer therefore retains a
source adapter for restored E-0006 transcript directories.

## Frozen source identity

- Cells: CAA×Qwen2.5-7B, ITI×Qwen2.5-7B, CAA×Llama-3-8B,
  ITI×Llama-3-8B.
- Axis: `uncertainty_awareness`.
- Items: the committed E-0006 80-item snapshot in
  `data/e0006_uncertainty_baseline/e0006_uncertainty_baseline.jsonl`.
- Split seed: `20260723`; DEV=27, TEST=53.
- Samples: `k=5`.
- Generation: sampled decoding exactly once per frozen job with
  `max_new_tokens=64`, `temperature=0.7`, `top_p=None`, `batch_size=16`.
- Direction extraction: `n_extraction=28`.
- Per-cell prompt, layer, requested alpha, ITI sigma, model identity, source
  fingerprint, and source-result hash are fixed by the checked-in manifest and
  the corresponding `results/arm_full/cell_*/c2b_adjudication_results.json`.

The committed E-0006 item snapshot, rather than a fresh network dataset load,
is mandatory for replay. This prevents dataset-version or row-order drift.

## Analysis

The headline split is TEST only. For each cell and each of prompt, steer, and
baseline, report exact format-compliance numerator/denominator and rate.
Report the original `conf=0.5` imputed steer-minus-prompt estimate only as a
fresh recheck value, never as a replacement for E-0006. The primary
format-confound stress test is paired complete-case analysis:

1. pair by `(item_id, sample_index)`;
2. retain a pair only when both prompt and steer confidence parse;
3. average retained pair differences within item;
4. average equally across retained items;
5. compute the frozen E-0013 95% item-cluster percentile bootstrap with
   `B=10000`, seed `20260723`.

Every exclusion is counted by reason. Missing rows, duplicate keys, unexpected
items, truncated generations, parse/score disagreement, source-identity
mismatch, or incomplete condition grids are hard failures, not exclusions.

Pre-specified sensitivities are (a) the original `conf=0.5` imputation,
(b) drop-imputed/paired-complete-case, and (c) adversarial `[0,1]` assignments
to noncompliant prompt/steer outcomes. An all-generation sign may be stated for
a cell only if both adversarial endpoints have the same strict sign. A
complete-case sign alone is not an all-generation sign.

## Missing-cell replay

Replay only cells without recoverable transcripts. Each cell runs in its own
new directory and must use the manifest-pinned items, split, prompt, layer,
alpha, seed, model-family identity, and generation settings. CAA/ITI directions
are re-derived through the frozen C2 path. ITI uses the frozen sigma for the
effective intervention; a small cross-environment re-derivation tolerance is
an identity check only and cannot change alpha, selection, or scoring.

The replay produces raw generation text solely to measure confidence-format
presence/missingness and the pre-specified sensitivities. It does not reselect
anything, revise any E-0006 decision, or become a new frozen scorer result.

DEV rows are generated first only to reproduce the additive E-0013 artifact
shape; they do not select or tune anything. TEST then uses a frozen job plan
whose `(cell, condition, item_id, sample_index, sample_seed)` hash is sealed
before generation. Completed fixed-composition batches are append-only
checkpoints. Resume reuses a batch only when its complete identity and content
hashes validate. Once `test_complete.json` exists, a missing TEST checkpoint is
a hard failure rather than permission to run TEST again. A crash before a batch
checkpoint commits may repeat only that interrupted batch; the failure is
retained and no completed TEST batch is regenerated.

## Failure and lineage rules

- Existing complete outputs are never overwritten.
- A failed replay writes immutable failure history plus a latest failure marker
  and leaves checkpoints for exact-command resume; it is never treated as a
  source unless a separately hashed completion marker is later written.
- The original E-0013 samples/reanalysis/run manifest and all four frozen
  E-0006 result files are hash-checked before and after every replay cell.
- Analysis fails closed unless all expected TEST rows are present. An explicit
  `--allow-incomplete` mode may emit inventory/verification artifacts, but it
  must set `grid_complete=false`, `valid_for_paper=false`, and make no grid
  claim.
- Every input and output file is SHA-256 hashed. The report records source
  schema, source path, frozen-result path/hash, manifest hash, code commit, row
  counts, and source model/method identities.
- GPU execution requires an explicit audited commit SHA, a clean code/protocol
  tree, and the exact same command on resume.
- GPU execution remains blocked until an independent hostile audit approves
  the protocol and runner.

## Post-audit execution

From the audited commit at repository root:

```text
python scripts/run_uncertainty_grid_replay.py --execute --expected-code-commit <AUDITED_SHA> --qwen-model Qwen/Qwen2.5-7B-Instruct --llama-model meta-llama/Meta-Llama-3-8B-Instruct
```

The default plan generates only the three absent cells; CAA×Qwen remains the
immutable original E-0013 source. The plan is 3,600 generations in 234 fixed
batches. At 2–4 seconds/batch plus model loading and direction derivation, the
pre-run estimate is approximately 0.3–0.7 sequential A800 GPU-hours, excluding
queue/download time.
