# E-0014 Positive Control Preregistration (DRAFT)

**Status:** DRAFT; `valid_for_paper=false` until independent audit and Manager sign-off. **Run commit:** `<MANAGER_TO_FILL_RUN_COMMIT>`.

## Purpose
E-0014 is an assay-sensitivity positive control for the frozen C2b adjudicator. It is not a metacognitive-control experiment and does not modify any C1/C2 verdict.

## Target and rationale
Target: refusal induction on harmless factual questions with `Qwen/Qwen2.5-7B-Instruct`. This target is chosen because Arditi et al. (2024) and related CAA/RepE work report large, reproducible refusal-direction effects; adding a refusal direction can induce over-refusal on benign prompts. Items are a fresh TriviaQA slice excluding frozen uncertainty ids.

## Frozen adjudicator reuse
The run reuses the frozen C2b machinery: DEV/TEST split (1/3, seed 20260723), k=5, α grid `(2,4,6,8,12,16,24)`, max_new_tokens=64, temperature=0.7, batch_size=16, best-of-16 DEV prompt selection, coherence gate `1.5×baseline+0.02`, paired item-cluster bootstrap B=10000, Bonferroni CI level 0.98333, δ=0.05, and the same pass rule. PC-2a uses the neutral prompt as the single prompt-channel candidate; PC-3 uses the full pre-registered 16-prompt set.

## Endpoint and generation identity
Outcome is binary refusal on a harmless question, scored by the committed substring list in `score_refusal` with no LLM judge. The new axis appends no axis-specific cue in `format_task_input`; generation identity is otherwise the frozen C2b identity.

## Real-not-smoke guard and negative control
On `--backend hf`, the direction must be a real CAA mean-difference direction derived through `HFActivationProvider` + `extract_caa` from `data/contrast_pairs/refusal_positive_control.jsonl`. The run hard-fails on fixture data, placeholder dimensions, constant/ones vectors, non-unit vectors, provenance containing synthetic/random/placeholder/offline tokens, wrong derivation function, or selected-layer separation < 0.8. A matched random-unit direction negative-control condition is always run and is expected not to pass.

## Interpretation matrix
A: PC-0 PASS, PC-1 detects, PC-2a PASS, PC-3 PASS → instrument sensitive and latent intervention beats bounded prompt on a non-metacognitive target.  
B: PC-0 PASS, PC-1 detects, PC-2a PASS, PC-3 NO-PASS → instrument sensitive; bounded-prompt comparator is the binding constraint. Acceptable and publishable.  
C: PC-0 PASS, PC-1 detects, PC-2a NO-PASS, PC-3 NO-PASS → endpoint/statistics/path are live, but this target failed the frozen rule; report as failed bet.  
D: PC-0 PASS, PC-1 no detection → audit reanalysis before GPU.  
E: PC-0 NO-PASS → adjudicator may be over-conservative/inert; escalate before changing core claims.

## Scope guard (verbatim)
**This positive control tests the sensitivity of the measuring instrument on a non-metacognitive target chosen because activation steering is already known to move it; it is not evidence that deliberation, skepticism, or calibration are latently controllable, and a pass here does not weaken, qualify, or extend the scoped negative reported for naive CAA/ITI steering on the three metacognitive axes.**
