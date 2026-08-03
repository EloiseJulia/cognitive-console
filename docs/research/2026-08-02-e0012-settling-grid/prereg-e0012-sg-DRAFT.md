# E-0012-SG settling grid mini-prereg (DRAFT)

Run commit: `<MANAGER_TO_FILL_RUN_COMMIT>`

## Purpose

E-0012-SG is a frozen descriptive robustness run that closes the E-0012 A-lite audit's UNVERIFIED-1: pure real BTN-CAL-PROBE steering on TEST was not measured. The run settles whether the same real probe direction has value by itself and whether it adds value when paired with the strongest known prompts.

## Frozen grid

Evaluate exactly six conditions on the frozen E-0012 TEST split, with no selection or tuning:

| prompt | steering |
|---|---|
| empty string | none (alpha=0) |
| empty string | real BTN-CAL-PROBE layer=18 alpha=24.0 |
| CAL-09 from `data/e0012_prompts/calibration_prompts.yaml` | none (alpha=0) |
| CAL-09 | real BTN-CAL-PROBE layer=18 alpha=24.0 |
| SYNTH-BANK-26 from `_SYNTHETIC_APE_CANDIDATES[26]` | none (alpha=0) |
| SYNTH-BANK-26 | real BTN-CAL-PROBE layer=18 alpha=24.0 |

## Metric and split

Use TEST only: pool_seed=12, offset=500, split_seed=42, 53 TEST items, and assert 0 DEV overlap. Score mean(1-Brier) at k=5 via the same E-0012 harness raw-pair path and sampler settings as the verified control run: max_new_tokens=256, do_sample=True, temperature=0.7, seed=42, fp16 CUDA for HF.

## Same-direction assertion

The steered cells must derive BTN-CAL-PROBE at layer 18 through `derive_probe_direction_real` with real activation provider, TriviaQA-train probe pairs, and seed=42. Before scoring, the freshly derived `vector_sha256` must exactly match the A-lite `real_probe@layer18` value in `results/E-0012/direction_provenance.json`. A mismatch aborts the run.

## Pre-stated readouts

Report descriptive paired deltas with cluster bootstrap 95% CIs:

- pure-steering effect: empty+probe − empty
- CAL-09-conditioned steering effect: CAL-09+probe − CAL-09
- SYNTH-BANK-26-conditioned steering effect: SYNTH-BANK-26+probe − SYNTH-BANK-26
- strongest steering-vs-prompt readout: best steered config − best prompt-only config

## Anti-forking paths and status

All six cells are evaluated once on the frozen TEST items. No DEV scoring, prompt search, alpha/layer tuning, condition dropping, or post-hoc winner selection is allowed. This is descriptive robustness evidence; `valid_for_paper` remains false until the GPU artifact is audited and Manager/owner sign-off occurs.
