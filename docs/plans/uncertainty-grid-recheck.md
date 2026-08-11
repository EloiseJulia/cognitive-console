# E-0013 four-cell uncertainty recheck plan

## Goal

Extend the frozen E-0013 format/missingness check from CAA×Qwen to the full
CAA/ITI×Qwen/Llama grid without changing either the original E-0013 artifact or
the frozen E-0006 scorer results.

## Steps

1. Inventory local, git-history, and authorized read-only remote transcript
   locations. Reuse immutable transcripts before considering regeneration.
2. Freeze a machine-readable manifest containing the four cell identities,
   frozen result hashes, item/split identity, generation settings, source
   candidates, analysis rules, and claim guard.
3. Add a fail-closed manifest-driven analyzer for both the E-0013 sample schema
   and the E-0006 transcript-directory schema. It must expose every excluded
   row/pair, exact compliance fractions, paired complete-case estimates,
   adversarial missingness bounds, and lineage hashes.
4. Add a replay orchestrator for only the missing cells. It must use the frozen
   80-item snapshot, selected prompt/layer/alpha, seed, sampling settings, and
   isolated output directories; it must never overwrite the original E-0013
   or E-0006 artifacts. Seal a fixed TEST job plan, checkpoint complete
   fixed-composition batches, resume only exact identity matches, and forbid a
   second TEST generation after the TEST-complete seal. Before planning replay,
   validate any present recovered transcript source; valid recovery skips
   generation and invalid recovery fails closed even when gitignored. Direct HF
   execution binds the audited commit, clean tree, protocol blob/hash, exact
   argv, authorization, resolved model identity, external scratch cache, and
   A800/CUDA/float16 resource guards into the checkpoint identity.
5. Run CPU-only validation against available immutable data. If fewer than four
   cells are present, emit an explicitly incomplete artifact and no grid-level
   scientific claim.
6. Add targeted tests, run the relevant suite, review the diff, and commit.

## Non-goals

- No GPU generation in this branch before independent hostile audit.
- No prompt, alpha, layer, item, seed, scorer, or frozen-result reselection.
- No replacement of `results/arm_full/` or
  `results/E-0013-uncertainty-recheck/`.
- No all-generation sign claim when adversarial bounds include zero.
