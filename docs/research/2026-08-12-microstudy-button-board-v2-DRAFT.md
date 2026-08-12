# DRAFT Preregistration: V2 Button-Board Gate Application Micro-Study

- **Status:** `DRAFT — NOT FROZEN — NOT AUTHORIZED FOR HUMAN DATA`
- **Date:** 2026-08-12
- **Protocol:** [`../specs/microstudy-button-board-v2.md`](../specs/microstudy-button-board-v2.md)
- **Materials:** `v10-button-board-20260812-draft`

## Design and estimand

This is a single-presentation, within-participant local task with one practice,
six formal fictional cards, one post-formal attention check, and optional
structured reflection. Each attempt receives exactly one F1/F2 material variant
plus F3–F7. There is no Contract/Flat comparison.

The primary descriptive outcomes are:

```text
GAA_rate = correct derived Q1 stamps / 6
Strict_GAA_rate = correct Q1 + decisive reason + required boundary / 6
```

The primary reporting set is completed exports passing AC1. The required
sensitivity includes every completed export regardless of AC1. AC1 response
time never excludes. No performance, response time, practice response,
reflection, or A/B outcome may define exclusion.

## Frozen-in-code material logic

The DRAFT structured source, router, generated private keys, public materials,
and balanced sequences are validated by:

```powershell
$env:PYTHONPATH = "src"
python scripts\generate_microstudy_v10.py --check
python scripts\validate_button_board_materials.py
```

Required routes are positive+exact→S, positive+missing-boundary→U,
decisive-negative→W, missing-comparison→D, mixed/thin→U, and
positive+important-other-task-harm→W. F1/F2 canonical non-manipulated fields
must hash identically. F1/F6/F7 boundary choices enter Strict GAA.

## Allocation and missingness

Allocation is success-only and balanced independently within locale over 24
cells: 12 sequences × 2 mutually exclusive variants. A participant attempt
cannot contain both F1 and F2. Partial signed exports retain all six planned
slots with missing values. This memory-only server cannot observe a closed
browser that never creates an export.

## Secondary descriptions

- four-state confusion matrix;
- reason-class accuracy;
- F1/F2 Q1 and reason distributions, without within-person pair scoring;
- F1/F7 exact-boundary and F6 missing-boundary accuracy;
- reason-correct/state-wrong and state-correct/reason-wrong proportions;
- relative Q1/boundary/reason response times;
- completion, partial completion, AC1 pass rate, and reflection distributions.

No inferential test, sample size, stopping rule, or MDE is frozen. Those require
owner/human approval before data collection.

## Export and analysis identity

Only signed
`microstudy-export-v6-button-board-bilingual-signed` products with material
schema `microstudy-button-board-v10-bilingual`, material version
`v10-button-board-20260812-draft`, and analysis version `button-board-gaa-v2`
are valid. Signature, locale hash, canonical material hash, sequence hash,
private-derivation hash, invariance hash, allocation cell, sequence, variant,
trial identity, presentation order, state transitions, and recomputed scores
must all validate. V9/V10 and V5/V6 mixtures fail closed.

## Claim boundary

Permitted future descriptions are limited to immediate comprehension and
application of fictional placement gates in the specified sample and task.
This protocol cannot establish user benefit, trust, safety, productivity,
control, real-product effects, real-world deployment fitness, latent mechanism
understanding, general population performance, or superiority over another
interface.

## Human gates

No recruitment, participant contact, ethics activity, timing work, human data,
public deployment, paper evidence, claim upgrade, or Protocol Freeze is
authorized. Human bilingual review, manual accessibility review, cognitive
interviews, usability work, privacy/retention approval, ethics/recruitment
authorization, sample-size justification, and owner approval remain open.
