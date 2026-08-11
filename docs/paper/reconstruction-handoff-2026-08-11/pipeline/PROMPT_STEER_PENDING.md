# Prompt + Steer Pending Integration Packet

## Status

- Planned completion: **on or before 2026-08-20**.
- Current evidence date: **2026-08-11**.
- Current state: **protocol frozen; no real DEV/TEST result**.
- Protocol:
  `docs/research/2026-08-11-prereg-prompt-steer-composition-FROZEN.md`.
- No result direction is assumed.

## Construct Question

The current worked application compares steering **instead of** the bounded prompt. A deployed control often operates **on top of** a user prompt. This pending study tests whether the substitution result survives, changes, or becomes irrelevant under composition.

## Outcome Branches

| Branch | Trigger | Required narrative action |
|---|---|---|
| P-A Added value | prompt+steer exceeds the bounded prompt under the declared rule | Reframe substitution-only no-pass as an incomplete construct test; report scoped composition evidence. |
| P-B No added value | prompt+steer does not qualify under an adequately powered/valid test | Report the scoped result with assay-validity and comparator caveats; do not generalize to all composition methods. |
| P-C Trade-off / mixed | target outcome improves but coherence/calibration or axes differ | Foreground trade-off and differentiated evidence states. |
| P-D Incomplete / invalid | implementation, power, missingness, or scorer prevents inference | Retain substitution-only scope and mark composition unresolved. |
| P-E Delayed | no frozen result by submission | Submit model-only fallback or delay; do not imply composition evidence. |

## Protocol — Frozen, Execution Pending

| Field | Pending value |
|---|---|
| Preregistration / registry | `E-0017-prompt-steer-composition-v1`; H4 registered; real data absent; Bo et al. prior composition work rules out a composition-novelty claim |
| Model, method, axis, layer | Qwen2.5-7B exact revision; CAA; 3 C2 axes; C2 extraction/layer rule |
| User/base prompt | Existing 16 bounded candidates; DEV selects one per axis |
| Added steering intervention | Same DEV-selected CAA direction/layer/alpha in `S` and `PS` |
| Prompt-only comparator | `P`: DEV-selected bounded prompt, unsteered |
| Steering-only comparator | `S`: neutral prompt plus the selected steer |
| Neutral/baseline condition | `N`: frozen neutral prompt, no steer |
| Selection budget and DEV rule | N=96/axis; prompt best-of-16; alpha grid 7; all selection DEV-only |
| TEST freeze and access control | Fresh TEST outside original C2 pool; sealed IDs; one-use audited authorization |
| Outcome, margin, coherence rule | Frozen C2 outcomes; primary `PS-P`; delta=.05; two-context 1.5x+0.02 |
| Missing/failure handling | Shared strict parser; uncertainty needs explicit answer+confidence, skepticism an explicit valid option cue; failures score 0 and remain recorded; token-level cap metadata; checkpoint resume |
| Multiplicity and uncertainty | Item-cluster B=10000; 98.33% Bonferroni primary and interaction families; interaction is secondary and cannot establish utility when `PS-P` fails |
| Operational freeze | Backend/attempt separation; immutable DEV/TEST seals; TEST HEAD exactly equals DEV; explicit HF model/tokenizer/dataset caches; fixed 60/70 GiB guards, 600 s watchdog, one retry, persisted physical-generation hard cap |

Synthetic execution is `SMOKE_ONLY`: it cannot create a scientific verdict,
confirmatory registry entry, C2 claim manifest, or evidence claim.

Historical E-0012 artifacts were previously inspected, but they are invalidated
lineage and contribute no evidence, prior, item choice, direction, or result to
this protocol. The disclosure records exposure only.

## Results — Keep Empty Until Frozen

| Result ID | Cell / estimand | N | Estimate | Interval | Verdict | Status |
|---|---|---:|---:|---|---|---|
| P-F1 | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` | NO RESULT |
| P-F2 | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` | NO RESULT |
| P-F3 | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` | NO RESULT |

## Required Integration Audit

When results arrive, update:

1. source registry and fact ledger;
2. construct-validity assessment;
3. claim graph and evidence inventory;
4. Arc A/B/C ranking and narrative contract;
5. Method, Results, Discussion, Limitations, Abstract, and Title;
6. the “slider” language throughout the paper;
7. final caveat and number lint.
