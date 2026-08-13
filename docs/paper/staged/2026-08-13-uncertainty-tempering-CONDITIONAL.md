# CONDITIONAL uncertainty-claim tempering — PENDING E-0013b AUDIT — NOT BLESSED

> **DO NOT apply to main.tex yet.** These edits temper the paper's uncertainty claim IF
> the E-0013b uncertainty-missingness recheck (branch `feature/uncertainty-missingness-recheck`,
> commit `e41a3a6`) passes an independent hostile audit (`audit-e0013b` in flight) AND the
> Manager makes the claim-call. E-0013b is currently `valid_for_paper=false`,
> `PENDING_HOSTILE_RESULT_AUDIT`. The exact tempering LEVEL (moderate vs strong) is set by the
> audit's recommendation. This file is prose only; it cannot compile into the paper.

## The finding (gated candidate, unaudited)
E-0013b rechecked the 3 uncertainty cells E-0013 never did, reproducing E-0013 bit-for-bit and
the arm_full grid mean_diff for all 4 cells. Result:
- In **3 of 4** cells STEERING SUPPRESSES parseable-confidence (steer 0.000–0.155 vs prompt 0.44–0.51),
  the **opposite** direction to E-0013's CAA-Qwen (steer 0.826 vs prompt 0.445). So the as-run negative
  delta is dominated by the frozen scorer's 0.5-imputation of the higher-missingness condition, and the
  missingness direction is not even consistent across cells.
- Complete-case harm survives in **only 1 of 4** cells (CAA-Qwen n=33; CAA-Llama UNDEFINED, 0 parseable
  steer; ITI-Llama −0.026 CI[−0.234,+0.186] excludes 0 = null; ITI-Qwen −0.349 but only 4 items/6 pairs).
- **All 4** cells' adversarial all-generation bounds cross zero.
Verdict (candidate): "uncertainty favors the comparator / four uniformly negative" is NOT robust —
plausibly a missingness/scoring artifact.

## What in the current paper this touches (must change if applied)
Two current statements become inaccurate once E-0013b lands:
1. Results §"Uncertainty produces a comparator-specific warning": *"All four steer-minus-prompt
   contrasts were negative under the frozen scorer."* — true as-run, but now known missingness-dominated.
2. axis-actions table Uncertainty row: *"...while the one-cell recheck is missingness-limited and
   **three cells remain unrechecked**"* — the "three cells unrechecked" clause is now FALSE.
3. Abstract: *"uncertainty favors the comparator under the frozen scorer, though its all-generation
   interpretation remains open."* — needs to reflect that the negative is missingness-dominated in ALL four cells.

---

## MODERATE tempering (default; if audit = SOUND and the negative is "missingness-dominated, not identified")

### Results §"Uncertainty produces a comparator-specific warning"
REPLACE:
> All four steer-minus-prompt contrasts were negative under the frozen scorer. The Qwen--CAA recheck retains a negative complete-case contrast, while its all-generation bounds cross zero.
WITH:
> All four steer-minus-prompt contrasts were negative under the frozen scorer as run, but this as-run sign is dominated by missingness: steering changes the parseable-confidence rate in every cell, and the frozen scorer imputes missing confidences. Under a complete-case decomposition the comparator disadvantage survives in only one of the four cells (CAA--Qwen), is undefined in one (CAA--Llama, no parseable steered confidences), and is null in another (ITI--Llama); in all four cells the adversarial all-generation bounds cross zero. The uncertainty contrast is therefore missingness-limited and its sign is not identified.

### axis-actions table, Uncertainty row
REPLACE the "structured evidence" cell:
> TRANSFER no-pass; frozen contrasts are comparator-negative, while the one-cell recheck is missingness-limited and three cells remain unrechecked
WITH:
> TRANSFER no-pass; the as-run comparator-negative is missingness-dominated across all four cells (complete-case harm survives only in CAA--Qwen; adversarial bounds cross zero everywhere)
REPLACE the "Next evaluation" cell:
> Repair measurement and retain the comparator-specific warning.
WITH:
> Repair the confidence-parseability confound before any comparator claim; treat the uncertainty sign as unidentified.

### Abstract
REPLACE:
> and uncertainty favors the comparator under the frozen scorer, though its all-generation interpretation remains open.
WITH:
> and the uncertainty contrast is missingness-limited under the frozen scorer, with its sign unidentified across all four cells.

### §5.4 / worked record / scenario
- Where the text says the other cells "did not receive this recheck," update to state they WERE rechecked and behaved oppositely; keep the CAA--Qwen complete-case −0.337 as the single surviving complete-case cell (with its all-generation bound still crossing zero).
- Worked Qwen--CAA record CALIBRATION WARNING: keep, but note it is the only cell with complete-case harm and that the effect is not identified under missingness.

## STRONG tempering (if audit says the confound is fatal to any comparator claim)
Demote uncertainty from a "comparator-negative" profile to a "measurement-confounded, sign-unidentified"
profile: drop "favors the comparator" everywhere; state the uncertainty axis is a measurement-repair case,
not a behavioral comparator finding; keep it only as a worked example of the CALIBRATION WARNING field
catching a scoring confound (which arguably STRENGTHENS the contract's value — the record surfaced a
confound that a naive Δ display would have shipped as a behavioral result).

## Note on framing upside (non-defensive)
Either tempering is a net positive for the paper's honesty AND arguably for its thesis: the five-field
CALIBRATION WARNING field is exactly what caught this confound. If audited sound, present it as the
contract working as intended, not as a retreat.

## Application preconditions
1. `audit-e0013b` returns SOUND (recompute confirmed; no bug/leakage). 2. Manager claim-call on tempering
level. 3. E-0013b lineage committed + registered (done on its branch, valid_for_paper flips only per Manager).
4. After applying: rebuild, re-record hash/undefined-cites, update claim-map/evidence-ledger, independent
claim/citation audit of the diff.
