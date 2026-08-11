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
the original `/root/autodl-tmp/cc/repo` path on that host. No trusted original
per-file transcript hashes exist. Therefore recovered transcripts are disabled
by default: a discovered unregistered directory hard-fails and cannot skip
replay. A future protocol may register a source only by freezing the exact
relative path, size, and SHA-256 of every original transcript file.

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

The plan stage inventories every declared recovered-transcript location before
planning generation, including gitignored directories. A transcript source is
eligible only when every original file path, size, and SHA-256 is predeclared
in the protocol and matches exactly before semantic parsing. Score-only or
per-item equivalence—including a format-present `confidence=0.5` substitution
that preserves a `0.75` score—cannot establish provenance. Because this
protocol has no trusted E-0006 transcript hashes, any discovered candidate is a
hard failure; absence mandates replay. Each cell runs in its own new directory
and must use the manifest-pinned items, exact DEV/TEST key sets, split, prompt,
layer, alpha, seed, model identity, and generation settings.
CAA/ITI directions are re-derived through the frozen C2 path. ITI uses the
frozen sigma for the effective intervention; a small cross-environment
re-derivation tolerance is an identity check only and cannot change alpha,
selection, or scoring.

The Qwen and Llama Hugging Face repositories are pinned to the exact revisions
and mandatory audited model-hash source record in `frozen-manifest.json`.
E-0006 used `NousResearch/Meta-Llama-3-8B-Instruct` under decision D-0038,
not the gated `meta-llama` repository. The arm result files retain only the
local runtime path, while D-0038/D-0039, the experiment registry, and the
E-0006-era Llama metadata identify the NousResearch source and record all four
shard hashes. The pinned NousResearch revision predates E-0006 and matches
those hashes exactly. Its ten required runtime files are byte-identical to the
corresponding gated upstream files; that equivalence is documented but does
not permit a silent source-identity swap.
Caller-supplied or optional content hashes are forbidden. The runner requires
the exact frozen path/size/SHA-256 inventory and aggregate for all root
Transformers weight shards, weight index, `config.json`,
`generation_config.json`, tokenizer files, and `chat_template.jinja` when
present. Model identity also binds the exact effective chat-template bytes used
by `apply_chat_template`. Pinned snapshots must be pre-staged in the explicit
cache; the replay runner is local-files-only and never downloads weights. A
matching basename, revision alone, or partial cache is never model identity.
The authorized A800 Qwen cache matches. No pinned NousResearch Llama snapshot
exists anywhere in the authorized read-only home/cache inventory. The host's
two gated-upstream documentation files are irrelevant and cannot substitute.
CAA×Llama and ITI×Llama therefore fail until the exact NousResearch snapshot is
staged and independently re-verified. ITI×Qwen remains independently eligible.

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
- Direct HF execution requires the tracked protocol manifest, the exact audited
  code SHA, a clean tree, and the manifest authorization ID. Checkpoints and
  seals bind those values, the manifest Git blob/SHA-256, exact argv, resolved
  model identity, scratch/cache paths, and CUDA/software/GPU identity. Older
  checkpoint schemas are rejected.
- Activation cache is stored only in an explicit scratch directory outside the
  repository. Its atomic seal binds the command/model/device/dtype plus every
  cache key, relative path, byte size, and SHA-256. The runner validates the
  exact inventory before every direction derivation/resume, permits only new
  entries created by that derivation, and reseals atomically before any
  checkpoint reuse. Changed, deleted, injected, malformed, or unsealed entries
  hard-fail and are retained by the failure wrapper.
- Before and between cells/batches, execution hard-checks CUDA, float16, an
  A800 device name, free disk, scratch size, activation-cache size, and the
  explicit HF-cache budget. GPU/software/disk lineage is recorded.
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
- GPU execution rechecks the audited commit, clean tree, manifest, authorization,
  model content, and protected artifacts before and after every cell.
- GPU execution remains blocked until an independent hostile audit approves
  the protocol and runner.

## Post-audit execution

From the audited commit at repository root:

```text
python scripts/run_uncertainty_grid_replay.py --execute --expected-code-commit <AUDITED_REPAIR_SHA> --authorization owner-2026-08-11-e0013-grid-recheck-after-hostile-audit --scratch-root <EXTERNAL_SCRATCH_ROOT> --hf-cache-dir <EXTERNAL_HF_CACHE> --qwen-model Qwen/Qwen2.5-7B-Instruct --qwen-revision a09a35458c702b33eeacc393d103063234e8bc28 --llama-model NousResearch/Meta-Llama-3-8B-Instruct --llama-revision 53346005fb0ef11d3b6a83b12c895cca40156b6c
```

The default plan targets only the three absent cells; CAA×Qwen remains the
immutable original E-0013 source. The plan is 3,600 generations in 234 fixed
batches. The two Llama cells are presently environment-blocked. After the
required code audit, ITI×Qwen can be selected independently with
`--cells iti__qwen2.5-7b`; this protocol change does not authorize executing it
in the current repair task. After exact NousResearch cache staging, the full
pre-run estimate remains approximately 0.3–0.7 sequential A800 GPU-hours,
excluding queue/download time.
