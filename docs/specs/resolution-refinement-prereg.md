# FROZEN PRE-REGISTRATION — C2b Resolution Refinement

- **Status:** **FROZEN 2026-08-12, before DEV or TEST. UNRUN.**
- **Protocol ID:** `c2b-resolution-refinement-20260812`
- **DEV experiment ID:** `c2b-resolution-caa-qwen-dev-20260812`
- **TEST experiment ID:** `c2b-resolution-caa-qwen-test-20260812`
- **Human compute authorization:** A800 80GB rental approved; this document and
  implementation do not start, push, merge, or authorize any other GPU.
- **Scientific role:** additive resolution refinement for the already reported
  frozen 0/12 grid. It does **not** replace, reopen, overwrite, or re-label
  E-0005/E-0006/E-0011. It is not a re-fish for a passing cell.

## 1. Scope, rationale, and fixed primary cell

The paper already reports that the skepticism null is resolution-limited near
the declared `delta=0.05` floor and calls for evidence at that resolution.
This study asks only whether the original primary **CAA × Qwen2.5-7B-Instruct**
cell remains unresolved when the item count is increased. The same method/model
is used for both included axes:

- method: single-layer additive **CAA**
- model: `Qwen/Qwen2.5-7B-Instruct`
- model revision: `a09a35458c702b33eeacc393d103063234e8bc28`
- axes: `skepticism`, `uncertainty_awareness`

CAA × Qwen is fixed because it was the original E-0005 primary adjudication cell,
not because it had the most favorable result. No model/method choice will be
changed after seeing DEV or TEST. This is a scope/resolution evaluation, not a
novel steering method or a new novelty claim.

## 2. A-priori power calculation

Source: committed frozen-derived artifact
`results/posthoc_equivalence/posthoc_equivalence_e0006.json`. For each cell,
`SD_item = SE * sqrt(N_current)` and
`N_target = N_current * (MDE_current / 0.05)^2`; integer TEST targets are ceilings.

| Method | Model | Axis | Current TEST N | Per-item SD | Current MDE | Exact target TEST N | Ceiling |
|---|---|---:|---:|---:|---:|---:|---:|
| CAA | Qwen2.5-7B | skepticism | 40 | 0.367387 | 0.1880 | 565.504000 | **566** |
| CAA | Qwen2.5-7B | uncertainty | 53 | 0.440396 | 0.1958 | 812.757968 | **813** |
| CAA | Llama-3-8B | skepticism | 40 | 0.524280 | 0.2683 | 1151.758240 | **1152** |
| CAA | Llama-3-8B | uncertainty | 53 | 0.106748 | 0.0474 | 47.631312 | **48** |
| ITI | Qwen2.5-7B | skepticism | 40 | 0.439114 | 0.2247 | 807.841440 | **808** |
| ITI | Qwen2.5-7B | uncertainty | 53 | 0.103640 | 0.0461 | 45.054452 | **46** |
| ITI | Llama-3-8B | skepticism | 40 | 0.545379 | 0.2790 | 1245.456000 | **1246** |
| ITI | Llama-3-8B | uncertainty | 53 | 0.103574 | 0.0460 | 44.859200 | **45** |

Only the fixed CAA × Qwen row is run. Pool constraints determine the actual plan:

| Axis | Frozen IDs excluded | Fresh selected total N | DEV N | TEST N | Planned MDE |
|---|---:|---:|---:|---:|---:|
| skepticism | 60 | **757 (all remaining)** | 252 | 505 | **0.05291** |
| uncertainty | 80 | **1219** | 406 | 813 | **0.04999** |

TruthfulQA has 817 validation rows. Requiring disjointness from the frozen
60-item pool leaves only 757 total fresh rows; after the frozen one-third DEV
split, TEST is 505, so the exact 0.05 target is impossible. The best achievable
planned MDE is about 0.05291. TriviaQA is large enough to reach the target.
No sample-size increase, decrease, early stop, or stop-on-significance is allowed.

## 3. Pinned datasets and exact disjoint sampling

| Axis | Dataset/config/split | Pinned revision | Deterministic metric |
|---|---|---|---|
| skepticism | `truthfulqa/truthful_qa`, `multiple_choice`, `validation` | `741b8276f2d1982aa3d5b832d3ee81ed3b896490` | `score_skepticism` keyed MC |
| uncertainty | `mandarjoshi/trivia_qa`, `rc.nocontext`, `validation` | `0f7faf33a3908546c6fd5b73a660e0f8ff173c2f` | per-item `1-(confidence-correct)^2` |

Exact rule, frozen with seed **20260812**:

1. Load the complete pinned validation split in upstream order.
2. Construct stable IDs using the existing loaders.
3. Exclude `truthfulqa-mc1-00000` through `truthfulqa-mc1-00059`, and
   `triviaqa-00000` through `triviaqa-00079`. These are the complete item pools
   from which every frozen 0/12 split was drawn.
4. On remaining items, use NumPy `default_rng(20260812)` (PCG64), take the first
   `N_total` positions from its permutation, sort those positions, and retain
   the corresponding upstream-order items.
5. Apply the existing `split_dev_test`: sort stable IDs, PCG64-permute with the
   same seed, assign `round(N/3)` to DEV and the rest to TEST, then sort each ID
   list. DEV and TEST ID hashes are sealed before TEST.

Any missing ID, duplicate ID, pool-size shortfall, revision drift, overlap with
the excluded set, or DEV/TEST overlap is a hard failure before scientific use.

**Asset caveat:** the repository manifests describe both datasets as
Apache-2.0, while the current Hugging Face metadata for TriviaQA reports its
license as unknown. The run may use the already approved loader, but publication
must not newly assert an Apache-2.0 TriviaQA license without separate source
verification.

## 4. Frozen estimand, comparator, and selection

For each TEST item `i`, average `k=5` sampled generations:

`d_i = steer_i - prompt_i`.

- skepticism outcome: keyed-MC `score_skepticism` in `[0,1]`
- uncertainty outcome: proper per-item `1-Brier` in `[0,1]`
- comparator: the same bounded best-of-16 authored prompt candidate set used by
  the frozen grid
- prompt selection: DEV only
- alpha selection: DEV only, grid `{2,4,6,8,12,16,24}`
- CAA direction/layer: re-derived on the pinned model using the frozen C1
  non-degenerate-layer convention; direction artifact and hash sealed at DEV
- TEST receives only the sealed prompt, alpha, layer, direction, item IDs, and
  fixed analysis code

TEST is never used for prompt, alpha, layer, item-count, scorer, or interpretation
selection.

## 5. Frozen generation and inference

- `k=5`; temperature `0.7`; sampled generation
- `max_new_tokens=64`
- authorized A800 generation batch size `32` (operational profile only; fixed in
  the execution identity and not CLI-overridable)
- paired item-cluster bootstrap, `B=10000`
- two-sided CI level `1 - 0.05/3 = 0.983333...`, retained from the frozen
  three-axis family rather than relaxed for this two-axis follow-up
- declared floor/margin `delta=0.05`
- coherence: steered mean degeneracy
  `<= 1.5 * unsteered_TEST_mean_degeneracy + 0.02`
- no judge model: only the generator loads; scoring is deterministic

The original axis-pass calculation is retained descriptively: corrected CI
excludes zero, point estimate is at least 0.05, and coherence passes. It does not
retroactively change the 0/12 grid verdict.

## 6. Missingness, parsing, and exclusions

Primary analysis is item-level ITT with **no post-hoc item deletion**:

- an unparsed skepticism MC response scores `0`
- an absent uncertainty confidence uses the frozen `0.5` uninformative value
- answer correctness uses the frozen deterministic key/alias matcher
- all generations, parse diagnostics, truncation flags, and degeneracy values
  are retained as audit artifacts

Parse-failure and truncation rates are reported descriptively by channel and
axis. No complete-case replacement may become primary. A catastrophic loader,
schema, model, or scorer failure aborts before TEST or records a failed TEST
attempt; it does not authorize changing the rule.

## 7. TEST-once, immutability, and additive lineage

The run sequence is **preflight → DEV → TEST exactly once**. DEV is sealed by
hashes. Immediately before first TEST generation, the runner exclusively creates
the host-global marker
`/var/lib/cognitive-console/c2b-resolution-refinement/test-attempts/c2b-resolution-caa-qwen-test-20260812.json`
with `O_CREAT|O_EXCL`. This canonical path is keyed by experiment ID and is
independent of `--out-dir`, so a concurrent invocation or a later invocation
using another artifact directory fails closed. The per-output
`test/TEST_STARTED.json` records the canonical marker but is not the uniqueness
authority. TEST results are sealed separately.

Do not use `--fresh`, delete the marker, reuse the output directory, or rerun
because of significance. An operational failure after TEST starts is reported as
a failed attempt and requires a new human decision and new protocol/experiment
identity. Frozen artifacts under `results/arm_full`, `results/E-0011`, and
`results/c2b_adjudication_hf_2026-07-24` are read-only and must never be
overwritten.

## 8. Honest interpretation table

| Observed outcome | Required interpretation |
|---|---|
| Coherent estimate remains below the 0.05 floor and corrected uncertainty is correspondingly narrow; achieved MDE is near/below 0.05 | **Powered null at the declared floor:** strong structured evidence that the earlier null was under-resolved rather than an invalid assay result. Do not claim a universal true zero or impossibility theorem. |
| A coherent small effect is newly detected | Report its sign, point estimate, corrected CI, and axis honestly. If `0 < effect < 0.05`, it is detectable but still below the declared actionability floor; if `effect >= 0.05` and the frozen pass rule holds, report a new additive result without rewriting the historical 0/12. |
| Resolution remains inadequate, coherence fails, or achieved MDE exceeds plan | **Still underpowered/unresolved:** report achieved TEST N, achieved MDE, missingness/coherence diagnostics, and the limiting pool or operational cause. No favorable reinterpretation and no automatic rerun. |

## 9. Authorized A800 profile and run commands

Profile: `nvidia-a800-80gb`; profile SHA-256:
`sha256:65e4cf84a9bc58b61152b911ab87648692914b1cee75aa17e97cd5f823fad249`.
It accepts only an NVIDIA A800 name with 75–82 GiB total VRAM, requires at least
60 GiB free before load and 20 GiB after load, and rejects smaller/unapproved
cards. Disk budget/ceiling remain 60/70 GiB.

On the rented Linux A800, from a clean checkout of the committed branch:

```bash
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export CUDA_VISIBLE_DEVICES=0
export HF_HOME=/workspace/hf
export PYTHONPATH="$PWD/src:$PWD"
export OUT_DIR=/workspace/cognitive-console-runs/resolution-refinement
export EXPECTED_CODE_COMMIT="$(git rev-parse HEAD)"

python scripts/run_c2b_resolution_refinement.py \
  --phase preflight --backend hf \
  --hardware-profile nvidia-a800-80gb \
  --hf-home "$HF_HOME" --out-dir "$OUT_DIR" \
  --expected-code-commit "$EXPECTED_CODE_COMMIT"

python scripts/run_c2b_resolution_refinement.py \
  --phase dev --backend hf \
  --hardware-profile nvidia-a800-80gb \
  --hf-home "$HF_HOME" --out-dir "$OUT_DIR" \
  --expected-code-commit "$EXPECTED_CODE_COMMIT"

python scripts/run_c2b_resolution_refinement.py \
  --phase test --backend hf \
  --hardware-profile nvidia-a800-80gb \
  --hf-home "$HF_HOME" --out-dir "$OUT_DIR" \
  --expected-code-commit "$EXPECTED_CODE_COMMIT"
```

Before execution, replace the shell-derived value with, or compare it against,
the audited commit SHA communicated with this preregistration. No command in this
document has been run on GPU.
