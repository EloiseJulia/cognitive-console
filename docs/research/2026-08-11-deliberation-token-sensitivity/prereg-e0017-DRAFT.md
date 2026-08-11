# E-0017 DRAFT preregistration — deliberation token-cap sensitivity

Status: **DRAFT / AUDIT-READY / NOT FROZEN / NOT RUN**

E-0017 is a reconstructed-TEST-index sensitivity companion to E-0006. It does not edit,
replace, relabel, or rerun the complete E-0006 adjudication, and it cannot turn
the frozen E-0006 `0/12` into a different historical result. Any real run
requires an independent `FREEZE_RECOMMENDED` re-audit of the exact run commit,
an owner authorization bound to that commit and one GPU UUID, and the runtime
gates below.

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
2. Did a same-seed continuation beyond token 64 add an explicit/terminal final
   answer, change the frozen parser number, or change correctness?
3. Did increasing the cap change either condition separately, the
   steer-minus-prompt contrast, or the frozen deliberation pass diagnostic?

No other axis or claim is tested.

## 2. Frozen companion identity

The sole manipulated variable is `max_new_tokens ∈ {64,128,256}`.

Everything below is inherited from E-0006 and locked:

- four cells: CAA×Qwen2.5-7B, CAA×Llama-3-8B, ITI×Qwen2.5-7B,
  ITI×Llama-3-8B;
- deliberation only;
- the recovered historical ordered index-ID pool
  `gsm8k-test-00000`…`00059`, `seed=20260723`, deterministic
  `split_dev_test`, and the fingerprint-proven sorted 40 TEST index IDs;
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

### Item-identity recovery and limitation

Historical commit `d20ccedf3756f267a4b9325abd2623c4e7c46335`
included every axis item-ID set in the run fingerprint. Reconstructing the
first 60 GSM8K index IDs and all other recorded arguments reproduces all four
retained source fingerprints exactly. The ordered pool and 40 TEST IDs are
locked in `e0006-item-identity.json`.

E-0006 did **not** record a dataset revision or item-payload hash. E-0017 pins
the GSM8K revision current at the historical run,
`740312add88f781978c0658806c59bc2815b9866`, and labels the payload
**reconstructed**. It must not claim unconditionally that the historical item
bytes were preserved. Exact 64-token per-item outcome reproduction is the
mandatory empirical compatibility gate.

### Model-checkpoint identity and gate

The only accepted repositories and full revisions are:

- `Qwen/Qwen2.5-7B-Instruct@a09a35458c702b33eeacc393d103063234e8bc28`;
- the E-0006 access mirror
  `NousResearch/Meta-Llama-3-8B-Instruct@53346005fb0ef11d3b6a83b12c895cca40156b6c`.

Runtime resolution is offline and revision-exact. The runner hashes
`config.json`, `generation_config.json`, all tokenizer/special-token files, the
safetensors index, and every weight shard. It rejects local paths, aliases,
same-basename substitutions, unsafe shard paths, missing shards, and any
run-config/checkpoint resume drift. Failure of the 64-token reproduction gate
is `INVALID_64_NONREPRODUCTION`; it may not be explained away as a cap effect.

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
- frozen parser output/number-present/failure flags; an independent
  `explicit_or_terminal_final_answer_present` flag; correctness and degeneracy;
- frozen result path/hash/config fingerprint, direction hash, code/run identity.

## 4. Exact stop and semantic-materiality definitions

1. **Generated token count:** continuation length through the first generated
   EOS token, inclusive.
2. **Visible token count:** continuation length before that EOS.
3. **Count equals cap:** generated count equals the configured cap. This is
   descriptive only. A sequence may emit EOS at token 64.
4. **Mechanical cap stop:** no generated EOS occurred and generation consumed
   exactly `max_new_tokens`.
5. **Frozen-parser number present/failure:**
   `parse_final_number(decoded_continuation) is not None/None`. Because the
   frozen parser falls back to the last number anywhere in the text, parser
   success is never labelled “final answer present.”
6. **Explicit-or-terminal final answer present:** a numeric value occurs in an
   explicit answer cue/box or as the terminal numeric answer at the end of the
   decoded continuation. This diagnostic is independent of the frozen parser.
7. **Operational semantic-truncation evidence:** a 64-token mechanical stop is
   an exact token prefix of its same-cell, same-condition, same-item,
   same-sample-seed 128/256 continuation, and the added continuation does at
   least one of:
   - adds an explicit-or-terminal final answer;
   - changes the frozen parser number;
   - changes correctness from 0→1 or 1→0.

Mechanical stopping or count-at-cap alone is never called semantic truncation.
Prefix mismatch is a reproducibility failure, not semantic evidence.

## 5. Estimands and inference

The cluster unit is TEST item; each item carries its five samples.

For each cell, cap `t`, and condition `c`:

- mechanical-cap-stop rate;
- count-equals-cap rate and token-count distribution;
- frozen-parser failure/number-presence rates and independent
  explicit-or-terminal-final-answer-presence rate;
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
  explicit/terminal answer, frozen-parser-number change, correctness recovery,
  correctness loss, and the union operational-semantic-evidence rate.

Inference:

- `D_t` and the original coherence/pass formula remain companion diagnostics
  with their historical 98.33% interval; they do not trigger the overall branch.
- The primary frozen multiplicity family contains all 24
  `E_c,t`/`I_t` estimands: four cells ×
  (`E_prompt,128`, `E_steer,128`, `I_128`,
  `E_prompt,256`, `E_steer,256`, `I_256`).
- Joint item-cluster bootstrap max-T simultaneous 95% CIs, `B=10,000`, resample
  the same 40 item IDs jointly across the complete family. Overall and per-cell
  branches use only these familywise intervals.
- Diagnostic rates use item-cluster 95% CIs. Continuation-conditional rates
  average per-item rates among items with at least one 64-token mechanical stop;
  if none exist, point and CI are explicitly undefined with
  `zero_denominator=true`.
- meaningful nonzero effect: `|point| >= 0.05` **and** CI excludes zero;
- equivalence/stability: `ci_lo > -0.05` **and** `ci_hi < +0.05`;
- non-significance is not equivalence.

The frozen coherence diagnostic is recomputed at every cap but is descriptive
for E-0017 branch selection:

`mean_degeneracy_steer <= 1.5 * mean_degeneracy_baseline + 0.02`.

The original deliberation pass formula is applied only as a companion diagnostic:
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
2. an external structured authorization file records:
   - an independent hostile auditor, distinct from the owner, with verdict
     `FREEZE_RECOMMENDED`;
   - the exact 40-hex audited run commit equal to clean `HEAD`;
   - owner `EloiseJulia` authorization, expiry, a ≤3 A800-GPU-hour cap, exact
     GPU UUID/name, designated hostname, canonical output directory, and
     host-global attempt-registry path;
   - the current frozen prereg hash, item-identity hash, dataset revision, and
     exact model revisions;
   `authorization-template.json` is schema documentation only and is rejected
   by the runner until independently/owner populated outside the repository;
3. the operator passes `--confirm-frozen-test-once`;
4. all frozen result hashes are readable and the arm summary still encodes
   exactly `0/12`;
5. the output directory is the sole authorized canonical directory, dedicated,
   and not within `results/arm_full`;
6. frozen caps, seed, temperature, batch size, extraction size, bootstrap count,
   prompts, layers, alphas, recovered index IDs, and scorer identities match;
7. `CUDA_VISIBLE_DEVICES` contains exactly the authorized UUID,
   `CUDA_DEVICE_ORDER=PCI_BUS_ID`, `TRANSFORMERS_OFFLINE=1`, `nvidia-smi`
   observes that exact A800 twice with zero compute processes, 0% utilization
   and ≤512 MiB used, torch exposes exactly one CUDA device, and every floating
   model parameter is `torch.float16` on `cuda:0`; CPU fallback is forbidden;
8. total guarded disk is below the hard ceiling and free space is at least
   5 GiB.

Threat model: these checks prevent accidental fallback, alias substitution,
cooperative duplicate attempts, and cross-directory peeking/retry. They cannot
prevent a privileged external process from starting after the final idle
observation; the designated host must therefore remain administratively
controlled for the attempt. The external authorization file is a trusted
control-plane artifact; the runner verifies its complete binding but does not
cryptographically authenticate the human/auditor identities.

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
- A host-global locked registry, outside every result directory, authorizes one
  canonical attempt. It atomically transitions `STARTED → FAILED` or
  `STARTED → COMPLETE`; same-directory crash resume is allowed under the same
  authorization and run-config hash, while cross-output-directory retries and
  reauthorization drift are rejected.
- The owner GPU-hour cap is checked before and after every fixed generation
  batch and direction/cell milestone.
- Disk guards run before generation and after direction/cell milestones.

### 6.3 Analyze TEST once

1. Generate all 36 cell×cap×condition sample files.
2. Revalidate all 7,200 records and confirm frozen source hashes are unchanged.
3. Seal the complete raw-input manifest and the 24-estimand max-T analysis
   specification in
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
2. **DISTORTION_AFFECTS_STEER_VS_PROMPT_COMPARISON** — any `I_t` is meaningful
   nonzero under its simultaneous max-T familywise CI.
3. **CAP_MATERIAL_BUT_COMPARISON_STABLE** — at least one `E_c,t` is meaningful
   nonzero and all interaction simultaneous CIs are strictly within `±0.05`.
4. **NO_MEANINGFUL_CAP_EFFECT_DEMONSTRATED** — all four `E_c,t` CIs and both
   interaction CIs for that cell are strictly within `±0.05`.
5. **INCONCLUSIVE_FIXED_N** — all remaining valid cases.

Conservative overall priority across cells:

`INVALID_64_NONREPRODUCTION >
DISTORTION_AFFECTS_STEER_VS_PROMPT_COMPARISON > INCONCLUSIVE_FIXED_N >
CAP_MATERIAL_BUT_COMPARISON_STABLE >
NO_MEANINGFUL_CAP_EFFECT_DEMONSTRATED`.

Mechanical-stop frequency and operational semantic-materiality are always
reported separately; neither alone determines the comparison branch.

## 8. Artifacts and interpretation limits

Expected immutable artifacts:

- `run_config.json`, `run_state.json`, plus the host-global canonical-attempt
  registry;
- four direction manifests;
- 36 sample JSONL files and 36 fixed-batch checkpoint wrappers;
- `test_once_analysis.json`;
- `analysis.json`, `analysis.md`, `run_manifest.json`.

`run_manifest.json` records authorization/audited-commit identity, frozen
hashes, reconstructed item identity and pinned dataset revision, exact
model/config/tokenizer/generation-config/weight-shard hashes, A800 UUID/idle and
float16 runtime checks, direction hashes, disk checks, raw/checkpoint hashes,
analysis specification, and TEST-once seal. The global `COMPLETE` record binds
the sealed raw/spec hashes and final analysis/manifest hashes.

All outputs start `valid_for_paper=false`. Independent hostile results audit is
required before any paper, claim-ledger, or evidence-ledger change. The frozen
E-0006 `0/12` remains the original result in every branch.

## 9. Exact future GPU command and compute estimate

CPU-only inventory command (requires the real task dependency/cache but performs
no generation):

```bash
python scripts/run_deliberation_token_sensitivity.py --dry-run \
  --qwen-model Qwen/Qwen2.5-7B-Instruct \
  --qwen-revision a09a35458c702b33eeacc393d103063234e8bc28 \
  --llama-model NousResearch/Meta-Llama-3-8B-Instruct \
  --llama-revision 53346005fb0ef11d3b6a83b12c895cca40156b6c
```

Exact GPU command, **only after this preregistration is committed as FROZEN,
human GPU/budget approval is recorded, and the selected GPU is confirmed idle**:

```bash
export HF_HOME="$HOME/cc_l0/hf_home"
export TRANSFORMERS_OFFLINE=1
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export CUDA_VISIBLE_DEVICES=<owner-approved-GPU-UUID>
python scripts/run_deliberation_token_sensitivity.py \
  --confirm-frozen-test-once \
  --authorization-file "$HOME/cc_l0/control/e0017-authorization.json" \
  --frozen-root results/arm_full \
  --out-dir results/E-0017-deliberation-token-sensitivity \
  --qwen-model Qwen/Qwen2.5-7B-Instruct \
  --qwen-revision a09a35458c702b33eeacc393d103063234e8bc28 \
  --llama-model NousResearch/Meta-Llama-3-8B-Instruct \
  --llama-revision 53346005fb0ef11d3b6a83b12c895cca40156b6c \
  --hf-home "$HF_HOME" \
  --disk-budget-gb 60 \
  --disk-ceiling-gb 70 \
  --min-free-gb 5
```

Compute estimate: 7,200 continuations, at most 1,075,200 continuation-token
slots, four direction/model passes, plus full SHA-256 reads of both model
snapshots before generation. The frozen E-0006 cells took approximately
29–33 minutes each while doing substantially more DEV/all-axis generation at a
64-token cap. Allow **1–3 GPU-hours** for E-0017 because its average cap is
longer and EOS behavior/hardware dominate. This estimate is not authorization.
