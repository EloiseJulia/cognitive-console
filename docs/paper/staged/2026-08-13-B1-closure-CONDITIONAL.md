# CONDITIONAL B1-closure write-in — PENDING pc4 audit + Manager/owner OK — NOT BLESSED

> **DO NOT apply to main.tex yet.** This adds ONE scoped diagnostic sentence to
> §"Assay Validity and Statistical Resolution" answering reviewers' B1 ("the gate is
> only ever shown to REJECT; show it can ACCEPT a real advantage and reject a null").
> Source = the audited prospective positive control(s). Apply only after: (1) pc4
> (strengthened negative arm) passes independent hostile audit; (2) Manager/owner
> approves; (3) result artifacts/lineage are reconciled onto the writing branch (or
> the sentence cites the experiment_id — numbers must trace to the committed result
> JSON, NOT be hand-invented). Markdown only; cannot compile into the paper.

## Evidence (gated candidates)
- **pc3** (branch `feature/positive-control-noisy`, commit `364ee43`) — HOSTILE-AUDIT = **SOUND**.
  Endpoint "answer in exactly two words" (whitespace token count == 2), frozen adjudicator unchanged,
  80 fresh TriviaQA items `triviaqa-00100..00179` verified DISJOINT from frozen E-0006 (sha256 match,
  empty id + text-hash intersection). POSITIVE (strong − neutral) Δ=0.600, 98.33% item-bootstrap
  CI [0.445, 0.751], per-item std 0.46, 5 distinct diffs (non-degenerate) → PASS. NEGATIVE (neutral−neutral)
  Δ=0, CI [0,0] → FAIL. `valid_for_paper=false`, PENDING integration.
- **pc4** (branch `feature/positive-control-strong-negative`, IN FLIGHT) — adds a NON-DEGENERATE noisy
  negative (same instruction, different seed → mean ≈ 0 with real per-item variance → expect FAIL),
  answering the pc3 audit's MAJOR that the [0,0] negative only rejects an EXACT null. Await its numbers + audit.

## Insertion point (main.tex, §Assay Validity)
Immediately AFTER: "Prompt endpoint liveness and random-direction sensitivity show that parts of the
pipeline respond; they do not validate the target intervention."

## Wording — VERSION A (pc3 only, if pc4 is not used)
```latex
As a prospective check that the qualification rule can \emph{qualify} a control and not only withhold one, we ran the unchanged adjudicator on a predeclared, format-following prompt effect over a pool disjoint from the tested items: it accepted a non-degenerate advantage (\(\Delta=0.60\), 98.33\% item-cluster bootstrap CI \([0.45,0.75]\)) and rejected a matched null. The qualification rule is therefore mechanically satisfiable and non-vacuous---the all-fail grid is not an artifact of an unsatisfiable gate---but this establishes neither latent-steering efficacy nor near-threshold calibration.
```

## Wording — VERSION B (pc3 + pc4 strengthened negative; PREFERRED if pc4 audits SOUND)
```latex
As a prospective check that the qualification rule can \emph{qualify} a control and not only withhold one, we ran the unchanged adjudicator on a predeclared, format-following prompt effect over a pool disjoint from the tested items. It accepted a non-degenerate advantage (\(\Delta=0.60\), 98.33\% item-cluster bootstrap CI \([0.45,0.75]\)), rejected an exact null, and also rejected a noisy same-instruction null whose per-item differences varied but averaged to zero. The qualification rule is therefore mechanically satisfiable and discriminative against both an exact and a noisy null---the all-fail grid is not an artifact of an unsatisfiable gate---but this establishes neither latent-steering efficacy nor near-threshold calibration.
```
(Fill pc4's exact negative numbers from its committed result JSON once audited.)

## Honest-scope guardrails (do not violate)
- It is a diagnostic on the DECISION MACHINERY via a benign prompt-format effect. It does NOT:
  show a latent/steering pass, change the 0/12 latent result, validate any behavioral axis, or claim
  near-threshold calibration. Keep the "neither latent-steering efficacy nor near-threshold calibration" clause.
- Do NOT frame it as "assay validated" — it is "mechanically satisfiable / non-vacuous."
- Numbers must come from the committed experiment_id result JSON (pc3 `364ee43`; pc4 commit TBD), not hand-typed guesses.

## Application preconditions checklist
1. pc4 hostile audit = SOUND (for VERSION B).
2. Manager/owner approve the write-in + wording version.
3. Lineage: the pc3 (+pc4) result JSON + experiment-registry entry present on the writing branch (reconcile
   branches) OR the sentence explicitly references the experiment_id; verify the quoted Δ/CI match the JSON.
4. After applying: `build.ps1 -Clean`; record pages/hash/undefined; then an independent claim/citation/lineage
   hostile audit of the diff.
