# E-0017 DRAFT preregistration — deliberation token-cap sensitivity

Status: **DRAFT / PREREGISTRATION-READY / NOT FROZEN / NOT RUN**

E-0017 is a TEST-only sensitivity companion to E-0006. It does not edit,
replace, relabel, or rerun the complete E-0006 adjudication, and it cannot turn
the frozen E-0006 `0/12` into a different historical result. Any real run
requires the normal protocol-freeze, human GPU-budget, free-GPU, and independent
audit gates.

## 1. Trigger, scope, and falsifiable question

The retained E-0006 deliberation artifacts contain per-item scored means but no
raw token IDs or exact stop reasons. The unavailable transcript side artifacts
would also have used a whitespace-word heuristic, not tokenizer IDs. Existing
evidence therefore neither supports nor rules out the criticism that
`max_new_tokens=64` mechanically prevented final answers and distorted the
prompt-versus-steer comparison.

E-0017 asks:

1. How often did generation actually stop because the token budget was
   exhausted, rather than merely produce a sequence whose count equals the cap?
2. Did a same-seed continuation beyond token 64 add or change the parsed answer
   or correctness?
3. Did increasing the cap change either condition separately, the
   steer-minus-prompt contrast, or the frozen deliberation pass diagnostic?

No other axis or claim is tested.

## 2. Frozen companion identity

The sole manipulated variable is `max_new_tokens ∈ {64,128,256}`.

Everything below is inherited from E-0006 and locked:

- four cells: CAA×Qwen2.5-7B, CAA×Llama-3-8B, ITI×Qwen2.5-7B,
  ITI×Llama-3-8B;
- deliberation only;
- the same 60-item GSM8K pool, `seed=20260723`, deterministic
  `split_dev_test`, and the same sorted 40 TEST item IDs;
- `k=5`, `temperature=0.7`, `batch_size=16`, item-major batching
  (`floor(16/5)=3` items per batch), chat rendering, per-batch seed derivation,
  per-sample seed derivation, scorer, parser, and degeneracy metric;
- extraction size `28`, the same direction derivation procedure, frozen layer,
  prompt, requested alpha, and ITI sigma scaling;
- bootstrap seed `20260723`, `B=10,000`, meaningful margin `δ=0.05`, and the
  original coherence/pass formula.

| cell | layer | requested alpha | frozen prompt |
|---|---:|---:|---|
| CAA×Qwen | 20 | 2 | `delib-strong-09` |
| CAA×Llama | 12 | 4 | `delib-strong-02` |
| ITI×Qwen | 20 | 4 | `delib-strong-09` |
| ITI×Llama | 8 | 2 | `delib-strong-02` |

At every cap, exactly three channels are generated:

1. frozen best prompt with alpha 0 (`prompt`);
2. frozen neutral prompt with frozen steer (`steer`);
3. frozen neutral prompt with alpha 0 (`baseline`, coherence only).

There is no DEV generation, prompt/alpha/layer selection, item replacement,
sample-size top-up, scorer change, exclusion tuning, or alternative seed.

### Model-checkpoint limitation and gate

E-0006 retained model labels/local paths but not immutable weight-shard hashes or
Hub revisions. E-0017 must use the same Qwen2.5-7B-Instruct and
Llama-3-8B-Instruct identities, record the effective reference and available
snapshot metadata, and pass exact 64-token reproduction. Failure of that gate is
`INVALID_64_NONREPRODUCTION`; it may not be explained away as a cap effect.

## 3. Sample plan and variables

Planned generations:

`4 cells × 3 caps × 3 channels × 40 items × 5 samples = 7,200`.

Worst-case continuation slots:

`4 × 3 × 40 × 5 × (64+128+256) = 1,075,200`.

For sample `(cell, cap, condition, item_id, sample_index)`, store:

- exact sample seed and frozen configuration identity;
- decoded continuation and its SHA-256;
- generated token IDs;
- generated count, visible pre-EOS count, padded raw continuation width;
- EOS token ID, exact stop reason, and mechanical-cap-stop flag;
- frozen parser output, answer-present/parser-failure flags, correctness, and
  degeneracy;
- frozen result path/hash/config fingerprint, direction hash, code/run identity.

## 4. Exact stop and semantic-materiality definitions

1. **Generated token count:** continuation length through the first generated
   EOS token, inclusive.
2. **Visible token count:** continuation length before that EOS.
3. **Count equals cap:** generated count equals the configured cap. This is
   descriptive only. A sequence may emit EOS at token 64.
4. **Mechanical cap stop:** no generated EOS occurred and generation consumed
   exactly `max_new_tokens`.
5. **Parser failure / final-answer absence:**
   `parse_final_number(decoded_continuation) is None`.
6. **Operational semantic-truncation evidence:** a 64-token mechanical stop is
   an exact token prefix of its same-cell, same-condition, same-item,
   same-sample-seed 128/256 continuation, and the added continuation does at
   least one of:
   - adds a parseable final answer;
   - changes the parsed final answer;
   - changes correctness from 0→1 or 1→0.

Mechanical stopping or count-at-cap alone is never called semantic truncation.
Prefix mismatch is a reproducibility failure, not semantic evidence.

## 5. Estimands and inference

The cluster unit is TEST item; each item carries its five samples.

For each cell, cap `t`, and condition `c`:

- mechanical-cap-stop rate;
- count-equals-cap rate and token-count distribution;
- parser-failure and final-answer-presence rates;
- accuracy and mean degeneracy;
- accuracy among mechanical stops and non-stops, with their difference marked
  association-only and non-causal.

Item-paired estimands:

- `D_t = accuracy_steer,t - accuracy_prompt,t`;
- `E_c,t = accuracy_c,t - accuracy_c,64`, for
  `c∈{prompt,steer}`, `t∈{128,256}`;
- `I_t = E_steer,t - E_prompt,t = D_t - D_64`;
- steer-minus-prompt mechanical-cap-stop rate;
- among paired 64 mechanical stops: exact-prefix rate, continuation-added
  answer, answer change, correctness recovery, correctness loss, and the union
  operational-semantic-evidence rate.

Inference:

- paired item-cluster percentile bootstrap, `B=10,000`;
- `D_t` and `I_t`: two-sided 98.33% CI, preserving the original per-axis
  Bonferroni confidence level;
- condition-specific `E_c,t` and diagnostic rates: two-sided 95% CI;
- meaningful nonzero effect: `|point| >= 0.05` **and** CI excludes zero;
- equivalence/stability: `ci_lo > -0.05` **and** `ci_hi < +0.05`;
- non-significance is not equivalence.

The frozen coherence diagnostic is recomputed at every cap:

`mean_degeneracy_steer <= 1.5 * mean_degeneracy_baseline + 0.02`.

The original deliberation pass formula is applied as a companion diagnostic:
98.33% CI excludes zero, point estimate `>=0.05`, and coherence passes.

Fixed-N planning references from frozen 64-token item differences:

| cell | N TEST | observed SD | normal-approx. two-sided 80% MDE |
|---|---:|---:|---:|
| CAA×Qwen | 40 | 0.146 | 0.065 |
| CAA×Llama | 40 | 0.137 | 0.061 |
| ITI×Qwen | 40 | 0.076 | 0.034 |
| ITI×Llama | 40 | 0.131 | 0.058 |

These are planning references only. No top-up is permitted.

## 6. Mandatory gates and TEST-once procedure

### 6.1 Before generation

The runner must fail closed unless:

1. this status line has been changed to `FROZEN` in a committed preregistration;
2. the operator passes `--confirm-frozen-test-once`;
3. the git tree is clean and the code commit is recorded;
4. all frozen result hashes are readable and the arm summary still encodes
   exactly `0/12`;
5. the output directory is dedicated and is not within `results/arm_full`;
6. frozen caps, seed, temperature, batch size, extraction size, bootstrap count,
   prompts, layers, alphas, items, and scorer identities match;
7. human GPU/budget approval and a confirmed idle GPU exist;
8. total guarded disk is below the hard ceiling and free space is at least
   5 GiB.

### 6.2 Generation and checkpoints

- Checkpoints are written atomically after each original fixed-composition
  generation batch, never after an arbitrary row.
- A checkpoint contains the exact expected ordered job-plan hash, run/config
  identity, direction hash, records, completion state, and final sample-file
  hash.
- Resume accepts only an exact ordered prefix ending at a fixed batch boundary.
  It skips complete batches and regenerates only the first incomplete batch,
  preserving the original batch seed/composition.
- Complete sample files and checkpoints must agree byte-for-hash and record for
  record. Corrupt, duplicate, reordered, rescored, or identity-mismatched
  records fail closed.
- No checkpoint or partial outcome may guide a rerun, parameter change, or
  selective exclusion.
- Disk guards run before generation and after direction/cell milestones.

### 6.3 Analyze TEST once

1. Generate all 36 cell×cap×condition sample files.
2. Revalidate all 7,200 records and confirm frozen source hashes are unchanged.
3. Seal the complete raw-input manifest and analysis specification in
   `test_once_analysis.json`.
4. Run the predeclared analysis once.
5. Mark the seal complete with hashes of `analysis.json`, `analysis.md`, and
   `run_manifest.json`.

A crash after the seal may resume only against the identical sealed raw hash.
If `analysis.json` already exists, post-processing resumes from it without
recomputing or re-peeking. A completed seal is immutable; rerunning the command
only verifies and reports the existing outputs.

### 6.4 Reproduction and completeness gates

- **64 reproduction:** for every cell, all 40 prompt and all 40 steer per-item
  correctness means must exactly match E-0006; the 64-token point estimate,
  98.33% CI, and companion pass value must also reproduce.
- **Prefix:** every paired longer continuation for a 64 mechanical stop must
  contain the exact 64-token prefix.
- **Coverage:** every planned identity appears exactly once; no post-generation
  exclusion is allowed. Missing/corrupt coverage invalidates the affected cell.

## 7. Predeclared outcome branches

Per cell, evaluated in this order:

1. **INVALID_64_NONREPRODUCTION** — any 64 reproduction gate fails.
2. **DISTORTION_AFFECTS_STEER_VS_PROMPT_COMPARISON** — either longer cap changes
   the companion pass status, or any `I_t` is meaningful nonzero.
3. **CAP_MATERIAL_BUT_COMPARISON_STABLE** — at least one `E_c,t` is meaningful
   nonzero, both interaction CIs are strictly within `±0.05`, and pass status is
   unchanged.
4. **NO_MEANINGFUL_CAP_EFFECT_DEMONSTRATED** — all four `E_c,t` CIs and both
   interaction CIs are strictly within `±0.05`.
5. **INCONCLUSIVE_FIXED_N** — all remaining valid cases.

Conservative overall priority across cells:

`INVALID > DISTORTION > INCONCLUSIVE > CAP_MATERIAL_STABLE > NO_MEANINGFUL`.

Mechanical-stop frequency and operational semantic-materiality are always
reported separately; neither alone determines the comparison branch.

## 8. Artifacts and interpretation limits

Expected immutable artifacts:

- `run_config.json`, `run_state.json`;
- four direction manifests;
- 36 sample JSONL files and 36 fixed-batch checkpoint wrappers;
- `test_once_analysis.json`;
- `analysis.json`, `analysis.md`, `run_manifest.json`.

`run_manifest.json` records frozen hashes, test-item hash, implementation-file
hashes, code commit, model references/available metadata, direction hashes,
disk checks, raw/checkpoint hashes, analysis specification, and TEST-once seal.

All outputs start `valid_for_paper=false`. Independent hostile results audit is
required before any paper, claim-ledger, or evidence-ledger change. The frozen
E-0006 `0/12` remains the original result in every branch.

## 9. Exact future GPU command and compute estimate

CPU-only inventory command (requires the real task dependency/cache but performs
no generation):

```bash
python scripts/run_deliberation_token_sensitivity.py --dry-run \
  --qwen-model Qwen/Qwen2.5-7B-Instruct \
  --llama-model meta-llama/Meta-Llama-3-8B-Instruct
```

Exact GPU command, **only after this preregistration is committed as FROZEN,
human GPU/budget approval is recorded, and the selected GPU is confirmed idle**:

```bash
export HF_HOME="$HOME/cc_l0/hf_home"
export TRANSFORMERS_OFFLINE=1
export CUDA_VISIBLE_DEVICES=<confirmed-free-gpu-index>
python scripts/run_deliberation_token_sensitivity.py \
  --confirm-frozen-test-once \
  --frozen-root results/arm_full \
  --out-dir results/E-0017-deliberation-token-sensitivity \
  --qwen-model Qwen/Qwen2.5-7B-Instruct \
  --llama-model meta-llama/Meta-Llama-3-8B-Instruct \
  --hf-home "$HF_HOME" \
  --disk-budget-gb 60 \
  --disk-ceiling-gb 70 \
  --min-free-gb 5
```

Compute estimate: 7,200 continuations, at most 1,075,200 continuation-token
slots, four direction/model passes. The frozen E-0006 cells took approximately
29–33 minutes each while doing substantially more DEV/all-axis generation at a
64-token cap. Allow **1–3 GPU-hours** for E-0017 because its average cap is
longer and EOS behavior/hardware dominate. This estimate is not authorization.
