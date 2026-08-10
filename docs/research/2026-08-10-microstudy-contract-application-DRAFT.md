# DRAFT Preregistration: Contract Legibility/Application Micro-Study

- **Status:** `DRAFT — NOT FROZEN — NOT AUTHORIZED FOR HUMAN DATA`
- **Date:** 2026-08-10
- **Protocol:** [`../specs/microstudy-contract-application.md`](../specs/microstudy-contract-application.md)
- **Normative materials:** [`../../data/microstudy_contract_application/stimuli.json`](../../data/microstudy_contract_application/stimuli.json), [`../../data/microstudy_contract_application/sequences.json`](../../data/microstudy_contract_application/sequences.json)

## 1. Scope and design

This exploratory formative within-participant study estimates whether a semantic-organization package changes technical GenAI users' structured application of a four-state contract to simulated records. Contract uses the exact semantic labels `READ`, `TRANSFER`, `BOUNDED PROMPT COMPARATOR`, `CALIBRATION WARNING`, and `EVIDENCE TIER` in fixed order; Flat uses exact neutral labels `Evidence A`–`Evidence E` and deterministic per-item row shuffles. Label word-count and visual differences are acknowledged parts of treatment; no filler padding is permitted. It does not test deep integration, transfer, benefit, trust, safety, productivity, deployment, or latent control.

There are ten formal trials, five per condition in two blocks, plus one different unscored practice. Q1 locks before Q2. The sole primary outcome is:

```text
CCA = 1 iff Q1 is correct AND Q2 is correct
```

The exact items, questions, answer derivation inputs, participant strings, export fields, and sequences exist only in the normative JSON. This document does not duplicate them.

## 2. Materials validation and leakage

Before any implementation or participant activity:

```powershell
python scripts\validate_microstudy_materials.py
python -m pytest -q tests\test_microstudy_materials.py
```

must pass. The validator reads JSON directly and freezes tokenization and heuristic algorithms. Required results are:

| Audit | Correct | Exact one-sided binomial p vs .25 |
|---|---:|---:|
| Oracle fixed answer per template | 3/10 | 0.4744071960449219 |
| Leave-one-item-out template frequency | 0/10 | 1.0 |
| Global best fixed position | 3/10 | 0.4744071960449219 |
| Equal-length | 2/10 | 0.7559747695922852 |
| Negation-marker | 3/10 | 0.4744071960449219 |
| Modal-marker | 2/10 | 0.7559747695922852 |
| READ-lexical | 2/10 | 0.7559747695922852 |
| Single-comparison-row Q1 | 8/10 | descriptive |
| Single-row + oracle Q2 CCA | 2/10 | 0.7559747695922852 |
| Single-row + LOO Q2 CCA | 0/10 | 1.0 |
| Normative router | 10/10 | descriptive |

All no-evidence tests use inclusive exact upper tails with no tuning. Q2 reuse is `4/4/2`; keys are `A2/B2/C3/D3`. P3-Y's next step is its genuinely missing scope boundary, not coherence; its resolved non-superiority keeps Q1 withheld.

The normative router defines TRANSFER pass as `tested && ci_low > 0 && estimate >= registered_margin`, followed by coherence pass→supported and coherence fail/unavailable→withheld. A CI crossing or touching zero is unresolved; resolved non-superiority and a positive-CI estimate below margin are withheld. Comparisons use exact JSON numbers without floating tolerance.

## 3. Participant materials and manipulation diagnostic

The exact common legend/tutorial explains the five inputs and ordered router in plain language without revealing trial answers. Practice and feedback are exact and common across conditions. The post-task format-recognition diagnostic is fixed, descriptive, and never excludes. Block ease uses `SEQ1`–`SEQ7`, appears after each block, is nullable, and is descriptive. There is no attention check and no free text.

The JSON `render_contract` is authoritative for DOM tags/classes/data attributes,
the single `primitive_evidence` text binding, Contract fixed order, Flat per-item
order, shared CSS geometry, 100% no-internal-scroll behavior, and 200% no-clipping
behavior. Current-machine headless Chrome/Edge audits execute the full flow at
`1440×900` and `1280×800`, 100%/200% zoom, check DOM geometry within `1px`,
overflow, focus, ARIA and hidden attributes, and retain dimension-checked Contract
and Flat screenshots. Pixel equality is inappropriate because labels and declared
row order differ. Manual screen-reader evaluation is `UNVERIFIED PRE-RECRUITMENT`.

## 4. Missingness, identity, and exclusions

Every export contains all ten planned slots and obeys:

```text
complete == q1_submitted && q2_submitted
q2_submitted => q1_submitted => presented => planned
submitted == complete
```

Primary available-case CCA uses complete trials only. Eligibility requires at least four complete trials per condition and eight total. The required sensitivity uses all ten planned trials and treats a missing component as incorrect.

The formal-stage `Save & Exit` creates a signed partial export with all ten slots,
nullable ease/diagnostic fields, and relative RTs, downloads JSON/CSV, and ends
without performance feedback. Silent browser abandonment produces no export and
is unobservable here; if recruitment is authorized, only the recruitment-platform
completion log can report it, and it cannot be inserted into study-export ITT.

Duplicate resolution happens first using signed `run_id` and `attempt_serial`.
Within-run ordering is lowest serial; cross-run duplicate participant codes
hard-fail without an explicit versioned owner attempt-order manifest. File order
has no authority. The preregistered first-complete/most-complete rule then applies;
assignment and other mechanical classification happen only afterward. Performance,
RT, practice, manipulation-diagnostic, and ease responses never exclude. Raw
attempts remain; missing-as-incorrect ITT omits only non-kept duplicates and
technical-corrupt attempts. Completed exports are canonical server products signed
with an owner-held HMAC-SHA256 key. No absolute timestamps, IP, UA, headers,
demographics, free text, or fingerprints are collected or persisted.

## 5. Allocation and statistics

The exact `A1..D5` generator is normative in `sequences.json`. A slot is consumed only by a finalized ten-complete-trial participant; dropout/primary-ineligible attempts reuse it; a later mechanically excluded completion consumes it.

The primary estimand is the mean participant paired Contract-minus-Flat CCA difference. Report a participant bootstrap (`B=10000`, seed `20260810`, percentile 2.5/97.5), exact one-sided sign flip, and exact two-sided sensitivity. Remove/report zero ties, enumerate all remaining sign assignments, include equality, and use no `+1`.

The available sign-binomial simulation is sensitivity-only and does not match the
primary paired sign-flip test. Primary-test MDE remains
`UNVERIFIED_NOT_ESTIMATED` before protocol freeze.

## 6. No-upgrade rule

This remains a DRAFT/materials-only protocol. It authorizes no recruitment, ethics activity, pilot, human data collection, public deployment, paper edit, or claim upgrade. Human evidence requires a separate owner decision and all applicable gates.
