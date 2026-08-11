# Novice-UX Contract-Application Micro-study — Final Hostile Audit Summary

## Scope and lineage

This file persists the fresh hostile audit of final implementation commit
`131ff25611579d9ae6859ee0c90f0c9ef99ed248` and V8 material identity
`microstudy-stimuli-v8-bilingual-novice-ux` /
`microstudy-contract-application-20260811-v8-novice-ux-draft`.

Before implementation, three independent synthetic novice-agents completed
blind tests: one Chinese-language novice, one English-language novice, and one
low-context novice. They are not human subjects or human-subject data, and
their feedback was used only as design inspiration; it does not demonstrate
usability, accessibility, timing, or ten-second comprehension. Implementation
proceeded only after the proposal-only construct/leakage audit returned verdict
`APPROVE`.

Any later docs-only commit that persists this summary and related governance
lineage is not a replacement implementation commit.

## Findings and closure

The hostile implementation audit reported two MAJOR findings against an
intermediate V8 state:

1. Common onboarding exposed Contract labels, weakening the intended neutral
   common/Flat boundary.
2. Edge could race session start before CSRF bootstrap readiness.

Commit `131ff25611579d9ae6859ee0c90f0c9ef99ed248` closed both findings. The final
fresh rerun found no remaining BLOCKER or MAJOR within the audited scope.

## Independently verified final scope

The final audit verified:

- the authoritative materials validator and Node checks;
- the full pytest suite and independent HTTP behavior;
- Chrome and Edge A1/D5 flows in English and Simplified Chinese;
- complete, partial, and download-failure paths;
- zoom and stress behavior;
- TTL, privacy, governance boundaries, and diff hygiene.

## Verdict

**SOUND — READY FOR OWNER-LOCAL PREVIEW; NO HUMAN DATA**

This verdict is limited to implementation readiness for owner-local preview. It
does not establish human usability or authorize recruitment, participant
contact, human-data collection, public deployment, paper evidence, a
claim/result upgrade, or Protocol Freeze.

## Open human gates

- human bilingual stable-ID semantic review;
- manual screen-reader evaluation;
- ethics determination/administration and recruitment authorization;
- owner timing work and a defensible primary-test MDE/sample-size basis;
- Protocol Freeze.
