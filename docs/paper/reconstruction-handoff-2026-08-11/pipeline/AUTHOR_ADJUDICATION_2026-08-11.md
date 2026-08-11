# Author Adjudication — 2026-08-11

## Evidence Access

- The reconstruction may rely on the legacy manuscript for current experimental facts.
- The supplied package does not include the primary result directories, frozen configs, generated tables, or audit artifacts referenced by the manuscript.
- Accordingly, legacy facts are **author-attested manuscript facts**, not independently artifact-verified facts.

## Comparator Language

The available provenance is insufficient to support these descriptions:

- blind;
- fair;
- globally best / global-best;
- exhaustive;
- budget-optimal.

The strongest permitted description is:

> a preregistered, DEV-selected, bounded prompt comparator

“DEV-selected” describes the reported selection procedure. It must not be expanded into “TEST-blind” without logs or primary artifacts.

## Validation Boundaries

- No passing latent behavioral positive control exists.
- No human evidence establishes that the record or interface mapping improves comprehension, decision quality, reliance, usability, or benefit.

Therefore the paper must not claim:

- completed assay validation;
- validated manipulation sensitivity for a known-positive latent control;
- inter-rater validation;
- validated necessity or sufficiency of the five fields.

## C3 Core-Claim Restructuring Approval

The human owner explicitly approved deleting *Diagnostic-only*, *Unresolved*,
*Unstable*, and *Eligible* as a formal taxonomy. The canonical mapping is:

> computational result → structured evidence or blocking reason →
> record-specific interface eligibility and action

Canonical action language is:

- `read-only diagnostic candidate within this evidence tier`;
- `active control withheld`;
- `active control passes the computational gate within this evidence tier`.

READ unsupported/not evaluated, TRANSFER not tested/not evaluable/no-pass/pass,
interval includes zero, comparator-negative, below-floor, coherence failure,
and missingness-limited remain distinct statuses or reasons. The 0/12 result
must not be converted into one withheld scientific state. The approved
uncertainty walkthrough withholds or pauses the slider for that Qwen–CAA record
while retaining the read-only diagnostic as a candidate.

## Safest Current Positioning

> A preregistered, executable qualification procedure using a DEV-selected bounded comparator, together with a worked application that carries computational results into structured reasons and record-specific interface actions.

The worked application is a scoped procedural classification. It is not a validated assay, a demonstrated HCI benefit, a deployment-readiness judgment, or a general verdict on latent steering.

## Pending Evidence

- Human study: expected on or before 2026-08-20; direction unknown.
- Prompt+steer composition: expected on or before 2026-08-20; direction unknown.

Both trigger pre-submission claim and narrative re-audit.
