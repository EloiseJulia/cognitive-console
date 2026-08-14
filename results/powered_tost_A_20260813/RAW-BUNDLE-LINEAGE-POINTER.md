# Experiment A (powered-tost-A) — raw-bundle lineage pointer

The paper's Experiment A numbers (Results skepticism/deliberation/uncertainty
paragraphs, `tab:axis-actions`, and the Abstract's "refined CAA cells" clause)
are folded from experiment **powered-tost-A** (protocol `powered-tost-A-20260813`).

## What lives on THIS (writing) branch
- `docs/specs/powered-tost-A-prereg.md` — frozen pre-registration.
- `results/powered_tost_A_20260813/test/cells/A{1,2,3,4}/sealed/powered_tost_A_result.json`
  — sealed per-cell TEST results: strict verdict, Δ, 98.33% CI, 90% TOST CI,
  achieved MDE, coherence, DEV-selected α, direction SHA, TEST-once marker.
- `results/powered_tost_A_20260813/experiment-registry.yaml`,
  `.../c1_read/experiment-registry.yaml` — registry rows.

## What lives on `feature/powered-tost-a` @ `cd1b14c` (full auditable raw bundle)
The complete per-item raw bundle — `work/transcripts/*.jsonl` (all_generations,
paired_test_channels, per-channel), `work/checkpoints/*`, `SEALED.json`,
`TEST_STARTED.json`, DEV sealed selection, per-cell SHA-256 manifests, and the
`nvidia-a800-80gb` hardware profile — is committed on the experiment branch
`feature/powered-tost-a` (commit chain `c8b8eb4` A1 → `637e8a8` A2 → `cae10cc` A3
→ `f1a537d` A4 → `cd1b14c` registry/C1). These ~250k lines are intentionally kept
off the submission branch per AGENTS.md REPORT_STORE policy (large artifacts stay
out of the PDF branch) but remain permanently committed and independently
auditable there.

## Audit status
Independent hostile correctness audit `audit-powered-tost` = **SOUND**: all four
cells recomputed from the committed raw artifacts on `feature/powered-tost-a`,
matching the sealed result JSONs to the digit; no BLOCKER/MAJOR. This is the
lineage-completeness fix that the earlier resolution-refinement run lacked (its
raw bundle was lost and could not be re-audited).

## Verified verdicts (see sealed JSONs)
| Cell | Model·Method·Axis | N | Δ [98.33% CI] | 90% TOST CI | MDE | Verdict |
|---|---|---:|---|---|---:|---|
| A1 | Qwen·CAA·deliberation | 150 | +0.021 [0.000,0.048] | [0.005,0.040] | 0.039 | EQUIVALENT |
| A2 | Llama·CAA·deliberation | 150 | +0.007 [−0.008,0.021] | [−0.004,0.016] | 0.036 | EQUIVALENT |
| A3 | Qwen·CAA·skepticism | 505 | −0.014 [−0.049,0.021] | [−0.038,0.010] | 0.053 | EQUIVALENT (bounded; MDE>δ) |
| A4 | Qwen·CAA·uncertainty | 813 | −0.088 [−0.120,−0.058] | [−0.109,−0.067] | 0.050 | NEGATIVE-CONTRAST |

**Scope:** additive; single CAA cell per axis at frozen E-0005 layers; does not
power the ITI or other-model cells; no latent arm passed; the frozen 0/12 grid
and E-0005/6/11 are unchanged.
