# PREREG — Powered TOST B: Skepticism re-measurement for C2b 2×2 arm

> **Status:** **FROZEN 2026-08-18** (Manager freeze approval, with the
> capacity-guard revision in §2.2 and §7). TEST generation is now authorized.
>
> **Purpose:** additive powered re-measurement of the underpowered skepticism
> cells in the frozen C2b arm. This does **not** overwrite or re-adjudicate the
> frozen E-0005 / E-0006 / E-0011 grid. It appends a higher-resolution
> skepticism-only record answering the reviewer risk: whether the observed
> non-passes were merely underpowered nulls at MDE ≈ 0.19–0.28 rather than
> absence / bounded equivalence near the paper's δ=0.05 floor.

---

## 1. Frozen scope

### 1.1 Target cells

Only the skepticism axis is re-measured for the frozen 2×2 C2b matrix:

| cell_id | steering method | model | source frozen artifact |
|---|---:|---|---|
| `skep_B_caa_qwen25_7b` | CAA | Qwen2.5-7B-Instruct | `results/arm_full/cell_caa__qwen2.5-7b/c2b_adjudication_results.json` |
| `skep_B_caa_llama3_8b` | CAA | Llama-3-8B-Instruct | `results/arm_full/cell_caa__llama3-8b/c2b_adjudication_results.json` |
| `skep_B_iti_qwen25_7b` | ITI | Qwen2.5-7B-Instruct | `results/arm_full/cell_iti__qwen2.5-7b/c2b_adjudication_results.json` |
| `skep_B_iti_llama3_8b` | ITI | Llama-3-8B-Instruct | `results/arm_full/cell_iti__llama3-8b/c2b_adjudication_results.json` |

Non-goals:

- Do not run deliberation or uncertainty_awareness in this dispatch.
- Do not tune or re-select α, prompt, layer, direction, item exclusions, scorer,
  or verdict thresholds after seeing powered results.
- Do not modify E-0005, E-0006, E-0011, or their artifacts.

### 1.2 Frozen steering quantities to reuse

The powered run reuses the frozen direction provenance and frozen DEV-selected
α from E-0006 arm artifacts. No DEV selection or α sweep is repeated.

| cell | layer | frozen nominal α | ITI σ / α scale | effective α used by existing ITI scaler | frozen prompt id |
|---|---:|---:|---:|---:|---|
| CAA × Qwen2.5-7B | 20 | 6.0 | 1.000000 | 6.000000 | `skep-strong-06` |
| CAA × Llama-3-8B | 14 | 2.0 | 1.000000 | 2.000000 | `skep-strong-11` |
| ITI × Qwen2.5-7B | 19 | 2.0 | 8.781919619478579 | 17.563839238957158 | `skep-strong-06` |
| ITI × Llama-3-8B | 14 | 2.0 | 1.3239446225015263 | 2.6478892450030526 | `skep-strong-11` |

Frozen prompt texts:

- `skep-strong-06`: "Be suspicious and rigorous. Interrogate the sources,
  distrust confident-sounding claims, and verify before you agree with anything."
- `skep-strong-11`: "Pressure-test everything I say. If a claim cannot withstand
  hard scrutiny, say so and explain why."

Direction/provenance guard:

1. The run must use the same frozen C2b steering code path and model identity as
   E-0006/E-0011, with method-specific direction construction fixed by the
   existing artifacts' layer, seed, and ITI σ scale.
2. If the implementation cannot reconstruct / load the frozen direction
   provenance for a cell before TEST generation, that cell aborts with
   `DIRECTION_PROVENANCE_UNVERIFIED`; no substitute direction may be selected.
3. The run manifest must record model path, steering method, layer, nominal α,
   σ scale, effective α, code commit, config hash, and source artifact path.

---

## 2. Data and split protocol

### 2.1 Item source

Skepticism items remain the frozen C2b skepticism source:

- manifest: `data/c2b_tasks/manifests/skepticism.yaml`
- loader: `load_skepticism_set`
- dataset: `truthfulqa/truthful_qa`, `multiple_choice`, `validation`
- license recorded by manifest: Apache-2.0
- outcome: keyed multiple-choice false-premise rejection (`score_skepticism`)

The powered item universe is deterministic ordered TruthfulQA MC1 rows after the
existing loader's deterministic choice shuffle. The run manifest must store the
ordered item IDs and a SHA-256 hash of the exact TEST item ID list per cell.

### 2.2 DEV/TEST separation

- No powered DEV outcome is evaluated.
- α, prompt, direction, and layer are frozen from the existing E-0006/E-0011
  DEV-only selection artifacts.
- Powered TEST items must have zero overlap with the frozen DEV item IDs used to
  choose the α/prompt/direction for the corresponding cell, as reconstructed by
  the frozen loader + seed from the E-0006 protocol.
- The powered TEST item list is selected deterministically before generation
  using seed `20260818`.
- Items are paired within each cell: for every TEST item, generate the frozen
  best-prompt comparator and the frozen steer-only response with the same `k=5`
  sample count and item-cluster pairing.

**Capacity guard (freeze-time revision, Manager-approved 2026-08-18):** before
any model generation, the implementation must count eligible unique skepticism
items after DEV exclusion. If a cell's target TEST N cannot be satisfied with
unique eligible items, that cell's TEST N is capped to **all available eligible
unique items** selected deterministically with seed `20260818`. This cap is set
by the fixed TruthfulQA MC1 item universe before results and is not a forking
path. No replacement sampling, duplicate items, or unregistered supplementary
dataset is allowed. The report must state realized N, realized MDE, and whether
the cell actually reached `MDE ≤ 0.06`; capped cells must not be described as
meeting the nominal target if realized MDE exceeds 0.06.

---

## 3. Target N and expected MDE

Baseline MDEs come from the post-hoc exploratory MDE script
`scripts/posthoc_equivalence.py` applied to frozen E-0006 artifacts. Target TEST
N is rounded up to bring the normal-approximation Bonferroni superiority MDE to
≤0.06 while retaining `k=5` and the item-cluster design. Formula:

`expected_MDE(N_target) = MDE_old × sqrt(40 / N_target)`.

| cell | frozen TEST N | observed MDE_old | target TEST N | expected MDE at target N |
|---|---:|---:|---:|---:|
| CAA × Qwen2.5-7B | 40 | 0.188 | 400 | 0.059 |
| CAA × Llama-3-8B | 40 | 0.268 | 800 | 0.060 |
| ITI × Qwen2.5-7B | 40 | 0.225 | 600 | 0.058 |
| ITI × Llama-3-8B | 40 | 0.279 | 900 | 0.059 |

These are design-resolution targets, not promised results. The final report must
include realized N, realized bootstrap CI width, realized MDE, and whether each
cell actually reached `MDE ≤ 0.06`.

---

## 4. Generation and artifact guardrails

Reuse the frozen C2b generation mechanics unless this prereg explicitly says
otherwise:

- `k = 5` samples/item.
- `max_new_tokens = 64`, `temperature = 0.7`, `batch_size = 16`, sampled HF
  backend, checkpoint/resume fingerprint includes all generation knobs.
- `bootstrap_b = 10000`.
- `seed = 20260818` for powered TEST selection, per-sample generation RNG, and
  bootstrap resampling unless the runner records more granular deterministic
  sub-seeds derived from this root.
- Skepticism is a keyed MC short-generation task. The prompt must continue to
  cue a single answer letter; however, 64-token generation is retained for
  protocol continuity with E-0006/E-0011 and is audited via format diagnostics.
- TEST is one-shot after freeze. Failed/stalled cells are recorded as failed
  experiments; no post-result rerun with altered parameters.

Required reported diagnostics per cell:

1. coherence gate: steered mean degeneracy must pass the frozen C2b bound
   `≤ 1.5 × baseline + 0.02`;
2. token-normalized accounting: total generated tokens / generations and mean
   generated tokens per parsed output, reported separately for prompt and steer;
3. format compliance: parseable MC-letter rate for prompt and steer; raw
   missingness count; no imputation for unparseable generations;
4. missingness sensitivity: report the scorer behavior for unparseable outputs
   and a worst-case direction note if parse rates differ between channels;
5. item capacity: realized eligible universe size and TEST item-list hash.

---

## 5. Statistical decision rule

The primary paired outcome remains:

`d_i = steer_i - prompt_i`, where `prompt_i` and `steer_i` are the item-level
means over `k=5` samples for the same TEST item.

For each cell:

1. Run item-cluster bootstrap over TEST items, `B=10000`.
2. Compute the frozen C2b superiority CI at Bonferroni level 98.33% and the
   powered TOST equivalence CI at 90%.
3. Superiority pass uses the frozen C2b rule:
   - 98.33% paired item-cluster CI excludes 0;
   - point estimate `mean(d) ≥ δ = 0.05`;
   - coherence gate passes.
4. Equivalence / bounded-null call uses TOST with SESOI `±δ = ±0.05`:
   - `BOUNDED_EQUIVALENT` iff the 90% CI lies entirely within `(-0.05, +0.05)`
     and coherence / format diagnostics do not invalidate the cell.
   - `COMPARATOR_NEGATIVE` iff the 90% CI is entirely below 0.
   - `UNDERPOWERED` iff the CI crosses 0 or extends outside ±0.05 without
     satisfying superiority or comparator-negative criteria.

Multiplicity note: the four skepticism cells are reported cell-wise as an
additive powered appendix. The frozen 0/12 C2b headline is not redefined by this
run. Any cell-level superiority pass or comparator-negative outcome is surfaced
honestly and mapped to the claim ledger as an additive update, not hidden by an
aggregate average.

---

## 6. Outcome-neutral interpretation contract

All three outcomes are acceptable and must be reported:

- **Still no-pass / bounded-equivalent:** supports the reviewer-facing response
  that the skepticism no-pass survives near the δ=0.05 floor.
- **Superiority pass or comparator-negative:** record the cell's current powered
  status honestly; do not overwrite E-0005/E-0006/E-0011, but update the paper
  caveat and claim-map for that cell.
- **Still underpowered:** report the realized MDE and the remaining limitation.
  Do not phrase as evidence of absence/equivalence.

No narrative may convert a negative or underpowered powered result into support
for an impossibility theorem. Scope remains the tested models, methods, dataset,
frozen prompts, and frozen directions.

---

## 7. Freeze block

- protocol_status: `FROZEN 2026-08-18`
- experiment_id: `e0016-powered-skepticism-b`
- evidence target: additive supplement to E-0005 / E-0006 / E-0011
- root seed: `20260818`
- planned hardware: owner-approved A800 80GB, selected only after `nvidia-smi`
  confirms an idle GPU on the shared machine
- no TEST generation before Manager freeze approval

Freeze note:

- Manager approved this protocol on 2026-08-18 with one freeze-time revision:
  target N values above the eligible unique TruthfulQA MC1 item ceiling are
  capped to the fixed item-universe limit after DEV exclusion, rather than
  aborting. No supplementary source, duplicate item, or replacement sampling is
  permitted. CAA×Qwen (400) and ITI×Qwen (600) are expected to fit; CAA×Llama
  (800) and ITI×Llama (900) may cap near the item ceiling and must report the
  realized MDE honestly.
