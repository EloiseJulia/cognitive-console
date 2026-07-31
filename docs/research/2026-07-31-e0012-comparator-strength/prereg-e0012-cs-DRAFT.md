# E-0012-CS Comparator-Strength Check — DRAFT Mini-Prereg

**Status:** FROZEN (D-0066, 2026-07-31). Protocol committed before the single GPU run.
**Experiment ID:** E-0012-CS.
**Run commit:** `264b475` (main, post-merge of feature/e0012-comparator-strength; code audited READY-TO-FREEZE-AND-RUN, zero drift to frozen src). The GPU run executes at this code state (the freeze-doc commit that pins this line adds only this prose; code is byte-identical).
**valid_for_paper:** `false` until independent audit plus Manager/owner sign-off.

## Purpose

E-0012-CS is a one-shot, self-critical robustness measurement for E-0012. Its purpose is to settle the v3-audit MINOR-1 comparator-strength gap: the previous human-authored synthetic-bank winner identity was not persisted, and the paper must know whether the strongest available human-authored calibration prompt beats the E-0012 button on the frozen held-out TEST split. This check can only weaken a positive verified-control claim; it cannot upgrade one.

## Frozen conditions

Evaluate every condition below with no filtering, selection, tuning, paraphrasing, replacement, or early stopping:

1. **Synthetic-bank human prompts:** the frozen first 30 prompts from `_SYNTHETIC_APE_CANDIDATES`, IDs `SYNTH-BANK-00` through `SYNTH-BANK-29`.
2. **Calibration YAML prompts:** all 18 prompts in `data/e0012_prompts/calibration_prompts.yaml`, including `CAL-09`.
3. **Baseline:** unsteered, no system prompt.
4. **Button:** `BTN-CAL-PROBE` at `layer=19`, `alpha=24.0`, no system prompt, using the same harness direction derivation for that family/layer.

Total: 30 + 18 + 1 + 1 = **50 conditions**.

## Frozen evaluation

- Data: the same frozen E-0012 TriviaQA pool and split helpers as E-0012 (`pool_seed=12`, `offset=500`, `split_seed=42`), yielding **27 DEV / 53 TEST**.
- Evaluation split: **TEST only** (53 items). DEV is loaded only to verify disjoint split identity; no condition is selected or tuned on DEV.
- Metric: mean `1-Brier`, using the existing E-0012 harness sampler/scoring path.
- Samples: `k=5` samples per item for every condition.
- Seed: `42`.
- Real run backend: HF on CUDA with fp16; raw GPU `(confidence, correctness)` pairs must be persisted with `synthetic_proxy=false`.
- Smoke backend: synthetic offline path is wiring-only and is not paper-valid.

## Pre-stated descriptive decision rule

Report the maximum human-prompt TEST score across the 30 synthetic-bank prompts and 18 calibration-YAML prompts, and report it side-by-side with the button TEST score. If `max_human_prompt_TEST_score ≥ button_TEST_score`, this confirms that a human prompt beats or matches the button on held-out data, which **weakens** any verified-control claim. This is descriptive robustness evidence only; no new threshold or adjudication tier is introduced here.

## Anti-forking-paths commitments

All 50 conditions are evaluated exactly once on TEST. There is no prompt selection, prompt rewriting, α/layer search, reranking, early stopping, failed-condition dropping, or post-hoc thresholding. The output must persist every stable condition ID, full prompt text or button spec, per-condition TEST mean `1-Brier`, the maximum condition, best synthetic-bank prompt, `CAL-09`, button, baseline, and raw-pair JSONL path.

## Paper validity gate

E-0012-CS is exploratory-robustness evidence. It remains `valid_for_paper=false` in the script output. Paper use requires independent hostile audit plus Manager/owner sign-off after the single GPU run artifact is produced.
