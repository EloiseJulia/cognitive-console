# DRAFT Preregistration: V3 Stepwise Open-Book Button Board

**Status:** NOT FROZEN; owner-local synthetic design only; no human data.

## Research boundary

The permitted descriptive target is accuracy when applying frozen evidence
thresholds one question at a time after short teaching while the fictional card
and “How to think” checklist remain visible. This design does not estimate benefit,
trust, safety, control, efficiency, long-term recall, interface superiority,
Contract/Flat effects, real-product effects, latent mechanisms, or population
generalization.

## Design

- Within-participant: six formal fictional cards.
- Between-attempt material sensitivity: mutually exclusive AB1-A/B, allocated
  1:1 within locale and fixed in the same balanced slot.
- One read-only worked example before formal trials. It uses the separate P1
  fictional card and shows each applicable question, demonstrated choice,
  cited card sentence(s), explanation, and final destination. It collects no
  practice response and proceeds directly to the first formal item after one
  acknowledgement.
- AC1 after formal trials; excluded from GAA, Strict, and step accuracy.
- Structured optional reflection; no free text.
- Twelve balanced six-slot orders; successful starts cycle through 24
  sequence-by-variant cells independently per locale.
- Start requires only the selected locale. The server generates a random
  non-personal `attempt_id`; no participant code, name, contact detail, or free
  text is requested.
- Within a scenario, participants may reopen the immediately previous step or
  any answered-step summary. Reopening removes that step and all later answers;
  the replacement answer alone determines the new continuation or early exit.

## Frozen routes and outcomes

The participant state is derived only from the final surviving route. GAA compares
that state with the independently machine-derived state. Strict additionally
requires the exact machine-derived path and decisive exit answer. A wrong scope
option after reaching Step 6 yields participant state S but fails Strict.

Primary descriptive summaries:

1. GAA count/rate over answered formal trials;
2. Strict count/rate over answered formal trials.

Secondary summaries:

- expected-state by participant-state confusion;
- decisive-exit accuracy;
- displayed-step accuracy and reach;
- state-correct but non-Strict proportion;
- Step 6 exact and per-dimension scope choices;
- AB1 state and Step 3 distributions;
- relative per-step response times as descriptions only;
- completion, exit location, and AC1 rate;
- all-completer, all-answerer, and AC1-pass sensitivity views.

No speed/ability conclusion or reaction-time exclusion is permitted.
No backtrack count is exported or analyzed in V11.2. Discarded answers are not
part of GAA, Strict, step accuracy, or the signed raw path.

## Missingness and exclusion

Partial signed exports retain submitted raw steps and leave later steps absent.
No imputation or cross-version backfill is allowed. AC1 failure is not a primary
exclusion; any AC1-pass analysis must be paired with all-completer results.
No participant code is collected. The server-generated UUID `attempt_id`, with
`run_id`, is the export identity; duplicate export identities fail closed.
V9, V10, and V11 exports cannot be mixed.

## Materials and derivation

All cards are rendered from the V11.2 typed fact registry. D-0118 changes only
the participant-visible bilingual skin to ordinary object names and explicit
one-sentence target definitions. The comparison schema
contains an existing/new method map for paired and single-method records.
Expected answers, exit, decisive step, state, GAA, and Strict are not material
inputs. Public files and raw exports contain no private derivation keys.
The P1 worked-example projection is derived from the unchanged P1 route but
contains no response controls. The signed export records only
`demonstration_status: acknowledged`, never a practice choice, path, timing, or
score. The separate four-destination explanation block is absent; the sticky
panel retains the six-question checklist, and all formal question options,
routes, keys, and scoring remain unchanged.

F4 explicitly reports 0 original-method rounds, 10 new-button rounds, and no
round using the original method. Its complete three-dimension scope remains
present, so its derived result remains NOT_COMPARED/U rather than SCOPE_MISSING.

## Claim mapping

Allowed:

> Accuracy, in the specified sample, under short teaching and continuously
> visible reference material, when applying frozen evidence thresholds one
> question at a time.

Not allowed: V3 benefit, V3 superiority over V1/V2, lower burden, causal UI
advantage, real product efficacy, general reasoning ability, or evidence about
Contract/Flat or latent steering. Before data, all numeric card values are
design inputs and the interface is illustrative rather than empirical.

## Gates before human data

Ethics/IRB applicability; recruitment/compensation; privacy/retention/deletion;
owner bilingual approval; two independent structural reviews; cognitive and
usability interviews; matched-condition, priority-contact, and missing-scope
comprehension; over-teaching and ceiling/floor checks; timing and sample-size
basis; manual screen-reader/color/keyboard/zoom review; and Protocol Freeze.
Any exploratory-to-confirmatory upgrade requires human approval.
