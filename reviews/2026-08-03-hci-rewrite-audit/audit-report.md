# HCI Rewrite Hostile Audit Report

**Scope audited:** `docs/paper/main.tex` at `feature/hci-rewrite` HEAD `f0b8239`, compared against pre-rewrite parent `4cc062e`. Binding materials read: `docs/paper/claim-map.yaml`, `docs/paper/submission-evidence-ledger.md`, `docs/paper/hci-rewrite-plan.md`, `docs/ledgers/decision-log.md` D-0076, and chained reviews A/B/C. `D-0077` was not present in this worktree's `decision-log.md`; I treated the prompt's D-0077/pending-recheck instruction as binding.

**Verdict:** **NEEDS-FIXES**. No fabrication blocker, no result-number blocker, no citation/build blocker. One MAJOR wording issue remains around the still-pending calibration-format recheck.

## Ranked findings

### MAJOR-1 — Format-compliance recheck is not framed as clearly pending

- **Evidence:** D-0076 says the format-confound GPU recheck is authorized and dispatched as Track-1, with raw-text capture, format-compliance rates, and compliant-only recomputation still to be run/audited/frozen (`docs/ledgers/decision-log.md:8-13`).
- **Paper text:** `docs/paper/main.tex:143` discloses the parser and imputation rule, but then says: "A format-compliance robustness analysis accompanies the uncertainty result (reported in the robustness pass; numbers intentionally left to the frozen post-recheck artifact)."
- **Why this matters:** The sentence does **not** claim the confound is resolved, and later caveats keep format fragility open (`main.tex:226`, `main.tex:273`). However, "accompanies" / "reported" can be read as completed rather than **in progress**. The requested gate was pending framing, not just omission of numbers.
- **Minimum fix:** State explicitly that the format-compliance recheck is pending/in progress and that no compliant-only reanalysis number is claimed in this paper version.

### MINOR-1 — Raw "zero new numeric tokens" claim is not literally true, but result-number integrity passes

- **Audit method:** Compared `HEAD^:docs/paper/main.tex` to `HEAD:docs/paper/main.tex`; after stripping citation/ref/input command contents, numeric-token counts were old=115, new=112 with increases only for existing scope/protocol tokens (`7--8B` 1→2, `16` 6→7), not new result values.
- **Evidence:** The changed files in the rewrite are only `docs/paper/main.tex` and the new plan (`git diff --name-status HEAD^ HEAD`); no `docs/paper/tables/**` or `docs/paper/figures/**` files changed. All `\input{...}` and `\label{...}` sets are preserved; refs have one addition only (`sec:design-implications`).
- **Conclusion:** No result number was changed/added/dropped in prose or tables. If the gate is interpreted as a literal token-level invariant, the prior claim was too strong; substantively, number integrity passes.

### UNVERIFIED-1 — "Registered" human-subjects protocol wording is internally supported only as a validated draft

- **Paper text:** `main.tex:66` says a controlled human-subjects protocol has been "independently reviewed and registered" while execution is owner-gated.
- **Ledger support found:** D-0053 records scientific approval of a validated draft protocol and review trail, with no IRB submission/recruitment/data collection (`docs/ledgers/decision-log.md:158-162`).
- **Assessment:** This is not an invented user study or result, and the sentence predates the rewrite. I did not verify an external/public registration artifact. Consider "validated draft protocol" if avoiding any implication of IRB/public preregistration.

## Fabrication scan

**Pass, no BLOCKER found.** I found no invented user study, participant data, interviews, personas, quotes, needs assessment, or new empirical dataset/result. The motivation is grounded in real interface/trust literature (`main.tex:47`, `main.tex:80-85`, `main.tex:232`). Human evidence is repeatedly denied/deferred (`main.tex:38`, `main.tex:63`, `main.tex:236`, `main.tex:238`, `main.tex:243`, `main.tex:275`, `main.tex:284`, `main.tex:293`). The appendix social-inference material is explicitly context-only and caveated (`main.tex:299`).

## Number-integrity section

**Pass, no BLOCKER found.** Generated quantitative artifacts remain inputs, not hand-edited tables: `main.tex:177`, `main.tex:200`, `main.tex:205`, `main.tex:211`, `main.tex:230`. The paper states no hand-transcribed result values and manifest lineage (`main.tex:183`, `main.tex:185`). Result claims remain qualitative/scoped; detailed values stay in generated tables/figures. No table/figure files changed in this rewrite.

## Over-claim section

**Mostly pass.** I did not find reintroduced equivalence, universal latent-control failure, user-benefit claim, or resolved-confound claim.

- Abstract preserves failed-superiority and non-equivalence caveats: `main.tex:38` says no demonstrated superiority, underpowered non-detections, same-item-pool split seeds, exploratory PSR, C1 setup, no user-study claim.
- Contributions explicitly reject equivalence/universal control readings: `main.tex:60-63`.
- C2 result text says failed-superiority and "nothing universal" (`main.tex:207`) and underpowered non-detection rather than equivalence (`main.tex:209`).
- Conclusion rejects universal steering limits, mechanism proof, and user benefit (`main.tex:293`).
- The prior "across HCI, fairness, and AI safety communities" pitch is not replaced by a new broad-community pitch; the replacement is trust-calibration risk grounded in citations (`main.tex:53`, `main.tex:232`).

Exception: MAJOR-1 above; the calibration-format recheck must be explicitly pending.

## Gate-integrity section

**Pass except MAJOR-1 pending-framing issue.**

- **C1:** exploratory setup, not control/confirmatory claim (`main.tex:60`, `main.tex:129`, `main.tex:202`, `main.tex:266`).
- **C2:** scoped to naive/off-the-shelf CAA/ITI and bounded prompts; not equivalence or impossibility theorem (`main.tex:51`, `main.tex:61-62`, `main.tex:207`, `main.tex:269-270`, `main.tex:291-293`). Split-seed same-item-pool caveat is present (`main.tex:213`, `main.tex:269`, `main.tex:291`). Underpowered non-detection caveat is present (`main.tex:38`, `main.tex:209`, `main.tex:291`).
- **C3:** interface-evaluation implication only, no user benefit/study (`main.tex:63`, `main.tex:236`, `main.tex:238`, `main.tex:275`, `main.tex:284`, `main.tex:293`).
- **C4:** appendix-only/context-only, valid_for_paper=false, M2/M3 not implemented, human-alpha pending (`main.tex:296-299`).
- **C2-mech:** off-manifold mechanism remains open/null/future work (`main.tex:226`, `main.tex:272`, `main.tex:293`).

## Calibration-harm pending check

Parser/imputation disclosure is present: k/temp/max_new_tokens/protocol and parser/conf=0.5→0.75 are disclosed at `main.tex:141-143`; bootstrap/multiplicity/δ are disclosed at `main.tex:147-176`. The paper does not say the format confound is resolved (`main.tex:226`, `main.tex:273`). But it also does not plainly say the recheck is pending; see MAJOR-1.

## Citations

**Pass.** Citation extraction found 30 unique cited keys and 30 bibliography entries; no uncited bib entries and no missing bib entries. No citation key was dropped versus `HEAD^`. Required new HCI/documentation keys are cited and present: `amershi2019guidelines`, `lee2004trust`, `bansal2019beyond`, `bucinca2021trust`, `mitchell2019modelcards`, `gebru2021datasheets` (`main.tex:47`, `main.tex:83`, `main.tex:85`, `main.tex:232`). Usage is contextually appropriate: trust/actionability/reliance for Amershi/Lee/Bansal/Bućinca, documentation/scope genre for Mitchell/Gebru.

## Build

**Pass.** Ran `docs\paper\build.ps1` successfully (exit code 0). `docs\paper\build\main.pdf` produced **12 pages**. Log scan found no undefined references or undefined citations; only the expected ACM reference-format warning.

## Final verdict

**NEEDS-FIXES** before merge: fix MAJOR-1 by making the format-compliance recheck explicitly pending/in-progress. After that wording fix, I see no blocker to merge from fabrication, number integrity, over-claim, gate, citation, or build checks.


