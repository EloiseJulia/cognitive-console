# PRE-REGISTRATION — E-0017 Prompt + Steer Composition Construct Validation

- **Protocol ID:** `E-0017-prompt-steer-composition-v1`
- **Status:** **FROZEN BEFORE REAL DEV/TEST, 2026-08-11; hostile-audit
  repairs synchronized before any real execution.**
- **Execution gate:** CPU/synthetic validation only until a fresh hostile audit
  returns `PASS`. Real TEST additionally requires a one-use authorization file
  tied to the DEV selection hash, protocol commit, audit verdict, and approved
  compute budget.
- Synthetic execution is `SMOKE_ONLY`: it may validate plumbing but may not
  emit a scientific verdict, confirmatory registry row, C2 claim manifest, or
  evidence/claim upgrade.
- **Scientific role:** construct validation for the current paper. This is not a
  composition-method novelty claim.
- **Prior-work boundary:** Bo et al. already tested prompting on top of activation
  steering in their interface work. We therefore do **not** claim first
  prompt-plus-steer composition. The purpose here is to answer whether our
  substitution-only worked application measures the deployed-control construct.
- **Historical exposure disclosure:** the team had already inspected historical
  E-0012 branches/artifacts while diagnosing comparator and operational failures.
  Those branches are invalidated historical lineage. E-0012 supplies no evidence,
  effect-size prior, item selection, direction, result, or claim support for
  E-0017; the disclosure records researcher exposure rather than evidence.
- **Preservation rule:** the frozen substitution result remains exactly
  **0/12**. This protocol creates a new experiment and must not modify, relabel,
  or overwrite the C2 preregistration, runners, artifacts, or verdicts.

## 1. Construct question and smallest high-information matrix

The prior C2 application asks whether steering can replace a bounded prompt. A
deployed slider commonly acts on top of a user prompt. The new question is:

> After selecting a bounded prompt without TEST access, does adding the same
> bounded CAA intervention provide incremental behavioral value over that prompt?

The confirmatory matrix is deliberately the smallest matrix that identifies this
construct:

- model: `Qwen/Qwen2.5-7B-Instruct`;
- exact revision:
  `a09a35458c702b33eeacc393d103063234e8bc28`;
- method: single-layer unit-direction CAA;
- axes/tasks: deliberation/GSM8K, skepticism/TruthfulQA MC1, and uncertainty
  awareness/TriviaQA `rc.nocontext`;
- CAA extraction, layer rule, prompt candidates, alpha grid, scorers, generation
  settings, and coherence metric reuse the frozen C2 implementation.

This one method-model cell is chosen because it is the canonical E-0005/E-0006
cell and all three Qwen CAA axes have local exploratory READ support. Adding ITI
would mix in a direction family without corresponding READ evidence; adding
Llama would test generalization rather than identify the composition construct.
Any ITI/Llama replication requires a separate preregistration. Results here are
scoped to Qwen CAA.

## 2. Four conditions per axis

Every selected TEST item receives all four conditions with `k=5` sampled
generations:

| ID | Prompt channel | Latent channel |
|---|---|---|
| `N` | frozen neutral instruction | no steer |
| `P` | DEV-selected bounded prompt | no steer |
| `S` | frozen neutral instruction | DEV-selected CAA steer |
| `PS` | the same DEV-selected prompt | the same CAA steer |

The intervention is
\(h'_L=h_L+\alpha\hat u\), using the DEV-frozen layer, unit direction, and
\(\alpha\in\{2,4,6,8,12,16,24\}\). `S` and `PS` use exactly the same direction,
layer, and alpha.

## 3. Hypotheses and estimands

For axis \(a\), item \(i\), condition \(c\), and sample \(j\), let

\[
\bar y_{iac}=\frac{1}{5}\sum_{j=1}^{5}y_{iacj}.
\]

### H4-P — primary incremental slider value

\[
\Delta^{P}_{ia}=\bar y_{ia,PS}-\bar y_{ia,P}.
\]

The axis qualifies only when the item-cluster bootstrap interval excludes zero
from above, the point estimate is at least `delta=0.05`, and both relevant
coherence checks pass. This directly answers incremental slider value over the
prompt.

### H4-I — factorial interaction / additivity

\[
I_{ia}=(\bar y_{ia,PS}-\bar y_{ia,P})
       -(\bar y_{ia,S}-\bar y_{ia,N}).
\]

- positive interaction: steering helps more on top of the prompt;
- negative interaction: prompt and steer interfere;
- interaction near zero: additivity remains compatible with the data.

Interaction is a registered secondary estimand, not a novelty claim and not a
license to call a slider useful when H4-P fails.

### Additional reported estimands

- prompt main effect: `P - N`;
- steer effect at neutral: `S - N`;
- axis-local 90% bootstrap intervals for equivalence context within
  `[-0.05,+0.05]`.

The equivalence interval is descriptive and axis-local. It does not create a
familywise cross-axis equivalence claim.

## 4. Items, prior-TEST protection, and deterministic pools

- seeds:
  - composition pool/selection/generation/bootstrap base seed: `20260811`;
  - original C2 split reconstruction seed: `20260723`.
- Original C2 TEST items are excluded from both new DEV and new TEST.
- Original C2 DEV items may be reused **only in new DEV**.
- New TEST items are outside the entire original first-N C2 pool
  (`60/60/80`) and are therefore fresh relative to C2.
- All remaining items are deterministically permuted by the frozen seed and
  axis name.
- New DEV has exactly `96` items per axis: original C2 DEV items plus a
  deterministic fresh fill.
- Before any DEV outcomes are generated, a maximum TEST reservoir is sealed:
  - deliberation: `384`;
  - skepticism: `680`;
  - uncertainty awareness: `1024`.
- The powered TEST set is the first `N_TEST` IDs in that sealed reservoir.
  Outcomes never affect which TEST IDs enter.
- The DEV artifact records every DEV/reservoir ID and a content hash. TEST
  reconstructs and verifies the pool byte-for-byte before generation.

No real TEST generation is permitted during selection, power planning, code
debugging, or audit.

## 5. DEV-only selection and eligibility

### 5.1 Bounded prompt

Evaluate the existing 16 separately authored prompt candidates on DEV, unsteered.
Candidates receive identical task-format cues and sampling settings. A candidate
is eligible only if:

- transcript coverage is 100%;
- parsed-answer rate is at least 95% for deliberation and skepticism;
- stated-confidence parse rate is at least 80% for uncertainty awareness;
- truncation rate is at most 5%.

Select the eligible candidate with highest mean DEV outcome. Ties are resolved
by lexicographically smaller prompt ID.

### 5.2 Same steer for `S` and `PS`

For every frozen alpha, evaluate both `S` and `PS` on DEV. An alpha is eligible
only if:

1. `S` passes measurement eligibility;
2. `PS` passes measurement eligibility;
3. `deg(S) <= 1.5*deg(N) + 0.02`;
4. `deg(PS) <= 1.5*deg(P) + 0.02`.

Among eligible alphas, select the alpha with the largest DEV mean `PS-P`.
Ties select the lower alpha. This deliberately gives the proposed slider a fair
DEV-only chance to add value over the prompt rather than selecting alpha for the
substitution estimand.

If no prompt or alpha is eligible, that axis is `DEV_INELIGIBLE` and its TEST is
not run.

## 6. Power and minimum detectable effect

The primary family contains three H4-P axis tests. It retains the frozen C2
two-sided Bonferroni confidence level:

\[
1-0.05/3=0.98333.
\]

Power planning uses the selected DEV `PS-P` item differences, without TEST. For
each axis:

1. compute `SD_DEV`;
2. set `SD_plan = max(SD_DEV, SD_prior)`;
3. use the E-0006 CAA×Qwen prior floors:
   - deliberation `0.1459715462`;
   - skepticism `0.3673885667`;
   - uncertainty `0.4403960139`;
4. calculate

\[
N^*=1.20\left[
\frac{(2.3944+0.8416)SD_{plan}}{0.05}
\right]^2;
\]

5. round upward to a multiple of eight and apply the frozen minimum/cap:

| Axis | Minimum TEST N | Maximum TEST N |
|---|---:|---:|
| deliberation | 128 | 384 |
| skepticism | 256 | 680 |
| uncertainty awareness | 256 | 1024 |

The factor `1.20` protects against DEV variance optimism. If required N exceeds
the cap or available fresh reservoir, the axis is `POWER_INELIGIBLE`; no TEST is
run and no no-added-value conclusion is allowed for that axis.

After TEST, achieved MDE is reported using the observed TEST SD. A failed
superiority test with achieved MDE above `0.05` is `INCONCLUSIVE_POWER`, not a
null.

## 7. Outcomes and scoring

The exact frozen C2 outcomes remain:

- deliberation: keyed final-answer accuracy;
- skepticism: keyed false-premise/truthful-option accuracy;
- uncertainty awareness:
  `1 - Brier = 1 - (confidence - correctness)^2`.

The task formatter requests a final answer/letter/confidence. A single shared,
fail-closed parser is used by scoring and diagnostics:

- uncertainty requires both an explicit `Answer:` field and a valid explicit
  `Confidence:` field; if either is absent, the sample outcome is `0`, the parse
  fails, and the missing field(s) remain recorded;
- skepticism MC requires an explicit valid answer/option/choice cue or a leading
  option marker. Arbitrary characters elsewhere in prose never select an option;
- no row is dropped or repaired with a fallback parser.

Raw parse diagnostics and exact token-level termination metadata are retained
per condition.

## 8. Missingness, failures, and exclusions

- No generated row, item, condition, or failed run is silently deleted.
- Checkpoints are append-only per item/condition/config and resume only under an
  identical config fingerprint.
- A GPU/driver failure leaves the TEST authorization in resumable `failed`
  state; resuming the same out-dir/config is allowed, but starting another TEST
  is not.
- Missing uncertainty answer or confidence is scored `0`, counted as a parse
  failure, and recorded in `missing_fields`.
- Missing skepticism option or deliberation final answer is scored incorrect
  and counted as a parse failure.
- Any absent generation record, duplicate identity after de-duplication,
  non-finite score, item mismatch, or incomplete `5 x 4 x N` coverage invalidates
  the axis.
- H4-P measurement eligibility on TEST requires `P` and `PS` to meet the
  preregistered parse/truncation thresholds.
- Factorial interaction interpretation additionally requires `N` and `S` to
  meet those thresholds.
- No post-TEST outlier exclusion or alternative parser is permitted. A new
  parser requires a separately preregistered sensitivity analysis and cannot
  replace this result.

## 9. Coherence

The primary pass requires both:

- `deg(S) <= 1.5*deg(N) + 0.02`;
- `deg(PS) <= 1.5*deg(P) + 0.02`.

The additive floor and degeneracy implementation are reused unchanged from C2.
A target gain that fails either comparison is `COHERENCE_FAIL`, not added value.

## 10. Statistical analysis and multiplicity

- Resampling unit: TEST item; all five samples remain inside the item cluster.
- Bootstrap: percentile item-cluster bootstrap, `B=10000`.
- H4-P family: three axes, two-sided 98.33% intervals.
- H4-I family: three axes, separately corrected two-sided 98.33% intervals.
- `P-N` and `S-N`: descriptive 95% intervals.
- Axis primary pass:
  1. H4-P 98.33% CI lower bound `>0`;
  2. mean H4-P `>=0.05`;
  3. both coherence gates pass;
  4. primary measurement eligibility passes.
- Interaction classes:
  - lower bound `>0`: `SYNERGISTIC`;
  - upper bound `<0`: `ANTAGONISTIC`;
  - 90% interval entirely within `[-0.05,+0.05]`:
    `ADDITIVE_WITHIN_DELTA`;
  - otherwise `INTERACTION_UNRESOLVED`.

No alpha, prompt, axis, model, method, scorer, missingness rule, or narrative
branch may be changed after TEST starts.

## 11. Overall branches and mandatory narrative consequences

### Positive

- **Trigger:** all three eligible axes pass H4-P.
- **Verdict:** `POSITIVE`.
- **Narrative:** the substitution 0/12 result remains true but is an incomplete
  construct test for deployed prompt-plus-slider use. Report scoped composition
  added value for Qwen CAA. Do not claim composition novelty, universal synergy,
  or transfer to ITI/Llama.

### Mixed

- **Trigger:** at least one, but not all, eligible axes pass; or target gain is
  accompanied by axis-dependent interaction, coherence, or measurement limits.
- **Verdict:** `MIXED`.
- **Narrative:** foreground axis-specific complementarity/interference and
  differentiated interface states. Do not collapse to “slider works.”

### Qualified null / no qualifying increment

- **Trigger:** no axis passes; all three axes are valid; all achieved primary
  MDEs are `<=0.05`.
- **Verdict:** `QUALIFIED_NULL`.
- **Narrative:** no qualifying incremental value was demonstrated for the tested
  Qwen CAA prompt-plus-steer composition. Preserve assay/comparator/method/model
  scope. Failed superiority is not universal equivalence.

Per-axis 90% intervals inside `[-0.05,+0.05]` may be called axis-local
equivalence context, but not a cross-axis or universal equivalence result.

### Inconclusive

- **Trigger:** no pass and at least one axis is underpowered, DEV-ineligible, or
  omitted by its cap.
- **Verdict:** `INCONCLUSIVE`.
- **Narrative:** composition remains unresolved. The substitution-only result
  cannot be extended to composition.

### Invalid

- **Trigger:** no valid axis, TEST identity/coverage failure, authorization
  violation, model revision mismatch, scorer/config mismatch, or unrecoverable
  missingness/coherence failure.
- **Verdict:** `INVALID`.
- **Narrative:** retain the substitution-only scope and report no composition
  result. Do not repair by inspecting TEST and rerunning under altered rules.

## 12. TEST-once and authorization

DEV writes an immutable backend-specific sealed bundle:

- `backend-hf/dev/sealed/dev_selection.json`;
- `backend-hf/dev/sealed/directions.npz` and SHA-256;
- `backend-hf/dev/sealed/test_authorization.template.json`;
- `backend-hf/dev/sealed/SEAL.json`.

Mutable checkpoints and cache state live separately under
`backend-hf/dev/attempts/attempt-0001/`. Synthetic and HF backends never share
artifact directories.

The external authorization must match:

- protocol ID;
- DEV selection hash;
- DEV protocol commit;
- hostile audit verdict `PASS`;
- budget status `approved`;
- non-empty authorization ID, authorizer, and timestamp;
- `max_test_starts=1`.

The runner atomically consumes the authorization into a `.used.json` sidecar.
Only an interrupted/failed run with the same selection hash, authorization-file
hash, out-dir, and checkpoint fingerprint may resume. A completed TEST cannot be
generated again. TEST finalization publishes one immutable directory containing
the result, authorization-consumption record, experiment record, seal, and—for
real HF only—the C2 manifest. Publication is one directory rename; rerunning a
completed command verifies the seal and repairs/deduplicates the registry mirror
without generating.

## 13. Lineage, identity, and operational guards

- Real DEV and TEST require a clean committed tree. Commit, source hashes, and
  effective config are checked at both phase start and phase end.
- TEST `HEAD` must equal the DEV commit exactly; a post-DEV code/docs commit is
  not permitted. Any source/protocol change requires a new DEV out-dir.
- Config identity includes protocol, model/revision, method, axes, item IDs and
  hashes, prompt texts, neutral prompt, direction/layer, generation settings,
  seeds, selection, alpha, TEST N, and bootstrap settings.
- The resolved model revision must equal the frozen revision.
- `--hf-home` controls `HF_HOME`, hub/transformers cache, dataset cache, and the
  activation cache; model, tokenizer, and dataset loaders receive those paths
  explicitly. The resolved cache layout is fingerprinted.
- Disk guard is frozen and non-overridable: 60 GiB soft budget, 70 GiB hard
  ceiling, checked before and after real phases.
- Stall watchdog is frozen and non-overridable at 600 seconds.
- Retry budget is frozen at one retry per backend call with identical seeds.
  Physical generation attempts are persisted across resumes and hard-capped at
  `2 ×` the logical generation budget.
- Each HF record stores exact generated token IDs/count, finish reason, EOS-token
  membership, and token-derived max-length status. Word count and transcript-log
  character truncation never diagnose a generation cap.
- Generated result and manifest remain `valid_for_paper=false` and `pending`
  until an independent hostile result/statistics/lineage audit.
- No paper result text, claim-ledger upgrade, or evidence-ledger entry is written
  before audited data exist.

## 14. Frozen commands and compute estimate

Real DEV after implementation audit:

```powershell
python -m scripts.run_prompt_steer_composition `
  --phase dev `
  --backend hf `
  --out-dir results\E-0017-prompt-steer-composition
```

After hostile DEV audit, budget approval, and completion of
`results\E-0017-prompt-steer-composition\backend-hf\test_authorization.json`:

```powershell
python -m scripts.run_prompt_steer_composition `
  --phase test `
  --backend hf `
  --out-dir results\E-0017-prompt-steer-composition `
  --selection-json results\E-0017-prompt-steer-composition\backend-hf\dev\sealed\dev_selection.json `
  --test-authorization-file results\E-0017-prompt-steer-composition\backend-hf\test_authorization.json
```

Worst-case planned generations:

- DEV: `3 * 96 * 5 * (16 + 1 + 2*7) = 44,640`;
- TEST at all caps:
  `4 * 5 * (384 + 680 + 1024) = 41,760`;
- total maximum: `86,400` logical generations;
- exact padded-batch count at batch size 16 and `k=5` (three items / 15
  generations per batch, including partial final batches):
  - DEV: `2,976`;
  - TEST at all caps: `2,788`;
  - total: **`5,764`**.
- frozen one-retry hard ceiling: `172,800` physical generation attempts.

Using the existing 2–4 seconds/batch range, partial batches, extraction/loading,
and the frozen retry allowance, budget **4.5–13.5 A800 GPU-hours** and under
60 GiB planned disk. This widened range is an estimate, not authorization.
