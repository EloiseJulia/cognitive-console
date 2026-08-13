# User-Study Design Requirements (advisory) — 2026-08-13

> **Status: ADVISORY, not paper content.** Distilled from the 4-family IUI reviewer panel
> so the forthcoming N≈20 study is designed to actually move the IUI decision. Human study
> is owner/human-gated; this note prescribes *what the study must measure*, not authorization.
> No results may enter the paper until real data + analysis + independent audit + Manager gate.

## The single hard red line (all four reviewers, GPT most explicit)
**The study MUST be a decision-quality / decision-calibration study, NOT a preference or
usability-only study.** GPT verbatim: *"A preference/usability-only N≈20 study would not cross
the bar."* Karny et al. is the cautionary precedent: their transparency UI raised subjective
trust/helpfulness but did **not** change behavioral outcomes — so "users liked it / found it
clear" is explicitly NOT sufficient evidence for IUI here.

## What the study must show (the load-bearing claim it closes)
Does the **five-field record** change how a person makes the **release decision**
(grant vs withhold an active latent control) — correctly — compared with a simpler display?

## Required design elements
1. **Task = a decision, not a rating.** Participants (designers, or informed proxies) decide
   GRANT / WITHHOLD an active control for each item, given the evidence.
2. **Manipulation = evidence display.** Full five-field comparator-bound record
   **vs** a simpler baseline display — e.g. a pass/fail badge, or an effect-only Δ / a
   method-level score (AxBench-style). At least one head-to-head baseline is required.
3. **Balanced items.** Include cases that SHOULD be granted and cases that SHOULD be withheld
   (ground-truth from the frozen adjudicator), so decision *accuracy* is measurable — not just
   a floor of all-withhold. (This depends on having at least one "should-grant" case; see the
   positive-control work in flight — without a passing case, the grant arm is hard to construct.)
4. **Primary DVs (decision quality, in priority order):**
   - Correct grant/withhold decision rate (accuracy vs adjudicator ground truth).
   - Calibrated reliance: over-trust in active controls (granting when evidence does not warrant).
   - Comprehension of the *comparator-vs-baseline* distinction (steer-vs-prompt not steer-vs-baseline)
     and of the evidence tier (non-transfer across model/method/axis).
5. **Secondary (allowed, NOT sufficient alone):** perceived helpfulness, clarity, preference —
   report but never as the headline.
6. **Honest nulls.** Preregister; report null/mixed/adverse outcomes. A well-powered-for-its-size
   null on decision quality is still reportable; a preference win alone is not the contribution.

## Scope / honesty constraints to preserve in any write-up
- Frame as a **formative / decision-quality** study at N≈20 (small; state power limits; do not
  over-generalize). It validates the *interface leg*, not the *assay* (positive control is separate).
- Keep it **substitution-scoped** unless a prompt-plus-steer (composition) condition is added —
  the reviewers flagged the slider is normally compositional; a composition arm would strengthen
  external validity but is optional.
- Do not let the study's subjective measures back-fill the model-evidence claims.

## Integration checklist (Writer, on receipt of real data)
- [ ] Confirm the study measures decision quality/calibration (not preference-only). If not, flag to owner BEFORE writing.
- [ ] Confirm ground-truth items + baseline display exist (balanced grant/withhold).
- [ ] Numbers only from committed analysis artifacts; register in evidence-ledger; valid_for_paper only after audit.
- [ ] Update CCS (then "Empirical studies in HCI" becomes accurate), abstract, contributions, §6, and the M2 reviewer thread.
- [ ] Do not claim comprehension/benefit beyond what the DVs support.

## Cross-refs
- Reviewer threads: rev2 panel (Opus/GPT/Gemini/Grok) MAJOR "interface un-evaluated"; Gemini scored 4/5 *conditional on this study*.
- Related in-flight: positive-control feasibility (branch feature/positive-control-feasibility) — needed for a "should-grant" case; uncertainty missingness recheck (branch feature/uncertainty-missingness-recheck).
