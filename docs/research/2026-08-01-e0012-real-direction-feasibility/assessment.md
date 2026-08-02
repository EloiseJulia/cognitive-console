# E-0012 real-direction feasibility assessment (zero-GPU)

Scope: doc-only feasibility pass; no code changes, no GPU, no experiments. I treat D-0067 as the owner-decision input: E-0012 button runs are invalid because `all_directions_for_layer` used synthetic random direction factories, not the frozen §3-B real derivations (`docs/ledgers/decision-log.md:8-13`; `docs/ledgers/failure-log.md:8-12`).

## Facts verified from source

- Frozen conservative track families are `BTN-CAL-PROBE`, `BTN-CAL-LOGIT-MARGIN`, and `BTN-CAL-CONTRA-REEXTRACT` (`docs/research/2026-07-29-e0012-verified-control-button/prereg-e0012-verified-control-button-DRAFT.md:69-77`).
- Current E-0012 harness derives directions only via `all_directions_for_layer(...)` (`src/cognitive_console/experiments/e0012_harness.py:939-945`), which dispatches to synthetic factories (`src/cognitive_console/experiments/e0012_buttons.py:371-397`). The synthetic factories use `rng.standard_normal(hidden_dim)` for PROBE/LOGIT/CONTRA (`e0012_buttons.py:145-162`, `215-231`, `308-325`).
- Real derivation functions exist but are not wired into the harness: PROBE (`e0012_buttons.py:171-210`), LOGIT-MARGIN (`e0012_buttons.py:240-260`), CONTRA (`e0012_buttons.py:335-365`).
- Existing C2 machinery already has reusable real activation extraction: `HFActivationProvider.get_activations` caches pooled hidden states (`src/cognitive_console/activations/provider.py:410-468`); CAA mean-diff is `mean_difference_vector` / `extract_caa` (`src/cognitive_console/steering/extract.py:118-174`); C2 HF build path reuses these to derive real CAA directions (`scripts/run_c2b_adjudication.py:734-815`; `scripts/run_gpu_phase0.py:118-127`).
- `SteeredHFBackend` also has an activation-capture hook surface (`src/cognitive_console/steering/generate.py:470-560`) and the real generation/steering hooks used by E-0012 outcome scoring (`generate.py:578-700`; `src/cognitive_console/experiments/e0012_steer_hf.py:1-130`).

## Family-by-family feasibility

### 1) BTN-CAL-PROBE — **medium difficulty, medium risk**

**Frozen requirement.** Train a logistic probe on activations at target layer from TriviaQA-train synthetic verbal-confidence pairs: 100 high-confidence (`0.9`) + 100 low-confidence (`0.1`), labels 1/0, seed 42; direction is the probe weight vector (`prereg...DRAFT.md:101-119`).

**Exists.** Pair template construction and a real logistic-regression function exist (`e0012_buttons.py:107-210`). Activation capture can be reused through `HFActivationProvider.get_activations`.

**Must be built/wired.** The runner must load TriviaQA-train items (not the E-0012 validation fixture), instantiate a real activation provider, call `derive_probe_direction_real` for every sweep layer, persist provenance hashes, and hard-fail on HF backend if a synthetic direction is used. Also verify `scikit-learn` availability: it is imported lazily by this function, but `pyproject.toml` does not list it (`pyproject.toml:11-25`).

**Risk.** Moderate. The math is simple, but this is new data-loading/provenance plumbing inside a harness with three prior real-vs-smoke failures.

### 2) BTN-CAL-CONTRA-REEXTRACT — **low-to-medium difficulty, lowest risk**

**Frozen requirement.** Select E-0006 DEV calibration items by unsteered baseline mean(1-Brier): top-40 positive, bottom-40 negative, tie by index, fallback to top-half/bottom-half if fewer than 80; direction is `mean(pos activations)-mean(neg activations)` at target layer (`prereg...DRAFT.md:124-136`).

**Exists.** `select_contra_pairs` and `derive_contra_direction_real` are close to correct (`e0012_buttons.py:267-365`). C2 already uses the exact CAA primitive (`scripts/run_gpu_phase0.py:118-127`; `src/cognitive_console/steering/extract.py:118-174`).

**Must be built/wired.** Need a loader/adapter for E-0006 DEV items with `baseline_score` and prompt text. Current E-0012 runner never passes `e0006_dev_items` into `run_e0012_harness` (`scripts/run_e0012_verified_control.py:253-262`), so CONTRA currently cannot be real. Also clarify cardinality: C2 uncertainty has N=80 and DEV fraction 1/3 (`adjudicate_c2b.py:51-67`), so the frozen fallback may produce ~13/14 if "E-0006 DEV" means the actual DEV split, not all 80 baseline-scored items.

**Risk.** Lowest, because it most directly reuses audited C2 CAA extraction. The dead function is close, but not audit-ready until the E-0006 baseline-score artifact and fallback behavior are explicit.

### 3) BTN-CAL-LOGIT-MARGIN — **medium-to-high difficulty, highest risk**

**Frozen requirement.** Direction is the leading PCA component of top1-minus-top2 logit-margin representations across calibration items (`prereg...DRAFT.md:72-73`).

**Exists.** Only a stub-level real function calling `activation_provider.get_logit_margin_activations(...)` (`e0012_buttons.py:240-260`). No such provider method exists in `HFActivationProvider`; its public API is `get_activations(texts, layer)` (`activations/provider.py:441-468`), while `SteeredHFBackend.capture_residual_activations` captures residuals but not top1/top2 logit-conditioned representations (`generate.py:470-560`).

**Must be built.** Define the exact representation matrix: likely last-token residual activations for calibration prompts, weighted/sliced by top1-top2 margin, or paired activations under top-token alternatives. Then implement a logits+hidden-state capture method and PCA provenance. This is genuinely new code and needs a fresh mini-spec/audit before GPU.

**Risk.** Highest. The prereg wording is underspecified relative to current APIs, so implementation risks protocol drift unless the owner/Manager freezes a precise operational definition.

## Reusability verdict

Option A is **not** a full rebuild. About 60-70% can reuse audited C2/HF infrastructure:

- activation capture and cache: reusable (`activations/provider.py:410-468`);
- CAA mean-diff direction math: reusable (`steering/extract.py:118-174`);
- real steering/generation and raw Brier pair path: reusable (`e0012_steer_hf.py:1-130`; `e0012_brier.py:156-275`);
- Stage0/Stage1 adjudication grid and outcome scoring: existing but must be gated against synthetic directions (`e0012_harness.py:939-985`).

New/higher-risk parts are: TriviaQA-train loader for PROBE, E-0006 baseline-score artifact adapter for CONTRA, a real logit-margin representation API, direction provenance persistence, and hard-fail tests that reject any `notes`/factory path containing "SYNTHETIC" on `backend=hf`.

## GPU-hour estimate (A800, Qwen2.5-7B fp16)

**Direction derivation only (estimate).** Because `HFActivationProvider` caches all layers per text in one forward (`activations/provider.py:410-468`), the 5-layer sweep does not multiply forward count. Approximate unique forward passes:

- PROBE: 200 TriviaQA-train synthetic-pair prompts.
- CONTRA: 27-80 E-0006 items depending on fallback interpretation.
- LOGIT-MARGIN: likely 80 calibration items, plus logits capture overhead.

At short-prompt forward-only cost, I estimate **0.2-0.6 GPU-hours** including model load, cache writes, and provenance export; use **0.5-1.0h** if logit-margin needs custom logits+hidden-state passes and audit reruns.

**E-0012 rerun itself (fact + estimate).** Prior conservative estimates were ~2.0-2.5h (`compute-cost-estimate.md:135-145`, `170-178`), but actual fp16 runs recorded ~3.45-3.53h (`results/E-0012/e0012_results.json:132`; `docs/ledgers/experiment-registry.yaml:1042-1060`), and D-0064 cleared a v3 rerun as ~5-6h (`decision-log.md:28-33`). Therefore budget **3.5-6.0 GPU-hours** for the rerun.

**Total Option A compute.** **~4.0-7.0 A800 GPU-hours** after implementation/audit, assuming no failed GPU runs. Add a contingency run if the logit-margin spec changes or a hard-fail catches provenance drift.

## Real-not-smoke pre-run checklist

Before any GPU rerun, require all of:

1. HF backend hard-fails if `all_directions_for_layer` / `derive_direction_synthetic` is used; persisted direction records must say `real_probe`, `real_caa_mean_diff`, or `real_logit_margin_pca`, never "SYNTHETIC".
2. Direction provenance artifact per family/layer: source item IDs, source split, model/dtype/device, layer, hidden dim, vector norm, derivation hash, and code commit.
3. PROBE: verify exactly 100/100 TriviaQA-train items, no validation/E-0012/E-0006 overlap, labels are verbal-confidence labels only.
4. CONTRA: verify E-0006 DEV baseline scores are real unsteered k=5 mean(1-Brier), tie rule/fallback cardinality, and no E-0012 TEST data is used.
5. LOGIT-MARGIN: freeze exact representation definition and add a unit/integration test that exercises real logits and PCA, not random matrices.
6. Outcome sampler remains real: `SteeredHFTextCapableSampler` and `BrierRawStore.synthetic_proxy=false` guard (`e0012_steer_hf.py:1-130`; `e0012_brier.py:156-275`).
7. DEV/TEST data are real TriviaQA Option A, N=80, 27/53 split, disjoint from E-0006 as recorded (`eval/e0012_triviaqa.py:1-30`; `experiment-registry.yaml:1039-1064`).
8. APE sampling uses frozen stochastic params and candidate persistence, not greedy/unpersisted fallback (D-0064).
9. Stage0 search count is exactly 105 and Stage1 prompt/steer channel semantics are explicitly audited; prior CS audit found v3 "steer" was prompt-conditioned, not pure steering (`reviews/2026-08-01-e0012-cs-reconcile-audit/audit-report.md:31-57`).
10. Coherence/degeneracy gates use real generated text and record raw degeneracy, including zero-baseline/infinity cases (`adjudicate_c2b.py:780-860`).

## Bottom line for A-vs-B

**Recommendation input, not final decision:** Option A is technically feasible but not "just rerun." It is a bounded **~1-2 engineering days + hostile audit + ~4-7 A800 GPU-hours** if the owner accepts a precise logit-margin operationalization. Feasibility confidence: **medium (0.65)**. CONTRA is low-risk and C2-reusable; PROBE is moderate; LOGIT-MARGIN is the main uncertainty. Given three freeze-integrity bugs, I would only choose A if E-0012 is still strategically important enough to justify a strict real-not-smoke gate; otherwise B remains the lower-risk paper path.
