# Plan · official-style ITI × TruthfulQA positive control

- **Branch:** `feature/iti-truthfulqa-positive-control`
- **Base:** `22a248abe6dfc429fc5d2979a99d2d204d697db9`
- **Owner authorization:** 2026-08-11, local/CPU implementation plus future A800 use.
- **Scope:** implement and freeze a comparator-bound behavioral positive-control
  harness without running real-model DEV or TEST.

## Hard boundaries

- Do not modify `scripts/run_c2b_adjudication.py`,
  `src/cognitive_console/experiments/adjudicate_c2b.py`, existing positive-control
  runners, or any existing result artifact.
- Do not download large model weights, contact a remote GPU, inspect real DEV/TEST
  outputs, or create scientific evidence.
- Synthetic and tiny in-memory model runs are pipeline tests only and remain
  `valid_for_paper=false`.
- The frozen 0/12 CAA/ITI grid is immutable and remains the paper's reported
  tested-grid result.

## Execution slices

1. Add a fixed 16-prompt truthfulness comparator bank.
2. Add official-style attention-head activation collection, top-head probe
   selection, center-of-mass directions, sigma scaling, last-token `o_proj`
   input hooks, matched random controls, and hook-bites.
3. Add pinned TruthfulQA identities, exact two-fold/inner-DEV splits, strict local
   truth/informativeness judge parsing, and behavioral `Truthful ∧ Informative`
   scoring.
4. Add the experiment harness with canonical config identity, disk guard,
   checkpoint/resume, DEV-only eligibility, TEST-once lock, missingness,
   truncation, coherence, random-control, and paired bootstrap gates.
5. Add the CLI, registry entry, preregistration, and targeted tests.
6. Run targeted pytest plus synthetic and tiny-model CPU smoke. Verify
   implementation/protocol parity, then mark the preregistration FROZEN and
   commit with the required trailers.

## Hostile-audit repair

Commit `d63c5d3` was rejected before GPU/DEV/TEST. The repair slice freezes the
effective generation config, persists and fingerprints complete fold configs,
adds schema-v2 signed global TEST authorization over both DEV lineage roots,
forces/monitors dedicated caches under non-overridable disk limits, records and
re-verifies complete runtime/artifact provenance, stabilizes judge resume
identity, isolates synthetic smoke status, freezes exact PCG64 algorithms, and
adds adversarial tests plus code-only GPU preflight assertions.
