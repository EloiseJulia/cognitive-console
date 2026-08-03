# E-0013 CAA×Qwen result audit — hostile independent report

**Scope audited:** branch `run/e0013-caaqwen-20260803` at HEAD `70af399`; artifacts in `results/E-0013-uncertainty-recheck/`; scorer/imputation code; prereg; chained-review confound.

**Question:** does the CAA×Qwen uncertainty harm survive the confidence-format/parser-imputation confound?

**Ruling:** **YES for this one CAA×Qwen cell.** Independent recomputation from `samples.jsonl` exactly reproduces the reported rates and deltas. However, the result is **one-cell robustness evidence**, not closure for ITI×Qwen, CAA×Llama, or ITI×Llama.

**Final verdict:** **HARM-SURVIVES-BUT-CAVEATED**.

## Commands run

From repo root on Windows/PowerShell:

```powershell
git --no-pager status --short --branch
git --no-pager rev-parse --short HEAD
@'
# inline Python audit script over results/E-0013-uncertainty-recheck/samples.jsonl
'@ | python -
```

The inline Python script loaded all JSONL rows, re-ran `cognitive_console.eval.scorers.parse_confidence(raw_text)`, recomputed imputed confidence and `1 - Brier`, grouped TEST rows by `(item_id, sample_index)`, recomputed item-cluster paired deltas, and ran an independent percentile paired bootstrap with `b=10000`, seed `20260723`.

## Recomputed numbers

### 1. Format-compliance counting

Code path is as claimed: `score_uncertainty_record()` sets `parsed_conf = scorers.parse_confidence(text)`, `format_compliant = parsed_conf is not None`, and `imputed_conf = parsed_conf or 0.5` before `per_item_brier` (`scripts/run_uncertainty_format_recheck.py:155-165`). The frozen adjudicator has the same imputation rule: `parse_confidence`, then `conf = 0.5` when `None` (`src/cognitive_console/experiments/adjudicate_c2b.py:471-476`). The parser itself is `parse_confidence` in `scorers.py` (`src/cognitive_console/eval/scorers.py:83-96`).

My recomputation over all 1,200 rows found:

- `parse_mismatches = 0`; stored `format_compliant` and `parse_confidence` exactly equal `parse_confidence(raw_text) is not None`.
- `score_mismatches = 0`; stored imputation and `per_item_1minus_brier` match recomputation.
- TEST rows: 795 = 53 items × 5 samples × 3 conditions.

TEST compliance:

| condition | compliant / samples | compliance | dropped | drop rate | mean imputed `1-Brier` |
|---|---:|---:|---:|---:|---:|
| prompt | 118 / 265 | 0.445283 | 147 | 0.554717 | 0.830899 |
| steer | 219 / 265 | 0.826415 | 46 | 0.173585 | 0.621411 |
| baseline | 216 / 265 | 0.815094 | 49 | 0.184906 | 0.620592 |

This exactly matches `reanalysis.json` (`results/E-0013-uncertainty-recheck/reanalysis.json:13-31`). The surprising fact is real: **steer drops the format much less than prompt**, not more. Sample evidence includes a compliant row with real raw text and parsed confidence (`samples.jsonl:70`) and a dropped row with `parse_confidence: null`, `format_compliant: false`, `imputed_confidence: 0.5` (`samples.jsonl:71`).

### 2. Compliant-only paired delta

The code restricts compliant-only to paired `(item_id, sample_index)` rows where both conditions are present and both are format-compliant (`scripts/run_uncertainty_format_recheck.py:383-386`), then averages sample-pair deltas within item before bootstrapping item means (`scripts/run_uncertainty_format_recheck.py:357-388`, `scripts/run_uncertainty_format_recheck.py:439-450`).

My recomputation:

- as-run paired TEST item count: 53.
- paired-compliant item count: 36.
- paired-compliant sample pairs: 110.
- item/sample counts among included items: 10 items with 1 pair, 3 with 2, 7 with 3, 7 with 4, 9 with 5.
- point estimate, steer − prompt: **−0.3366781481481482**.
- paired item-cluster bootstrap 95% CI: **[−0.5075485879629629, −0.16516796759259258]**.
- The CI excludes zero. Alternative bootstrap seeds (0, 1, 42, 12345) also gave wholly negative upper bounds (approximately −0.161 to −0.166).

This exactly matches `reanalysis.json` (`results/E-0013-uncertainty-recheck/reanalysis.json:40-48`). The drop from 53 to 36 items is explicitly reported there (`n_items: 36`, `n_compliant_sample_pairs: 110`, and the restriction string), so I do **not** find hidden cherry-picking.

### 3. As-run vs frozen sanity check

Recomputed as-run imputed TEST steer − prompt delta: **−0.20948830188679243**, over 53 items. `reanalysis.json` reports the same (`results/E-0013-uncertainty-recheck/reanalysis.json:36-38`). The frozen source CAA×Qwen uncertainty mean difference is **−0.22767283018867926** (`results/E-0013-uncertainty-recheck/run_manifest.json:43-44`). Difference: **+0.018184528301886826**. That is small relative to the fresh `k=5` sampling design and confirms E-0013 reproduces the frozen cell's harm rather than measuring a different effect.

### 4. Real pairs / identity

- All rows: `synthetic_proxy=False` (1,200 / 1,200), non-empty `raw_text` (1,200 / 1,200), and `raw_text_sha256` present (1,200 / 1,200). Examples: `samples.jsonl:70-71`.
- Manifest records `backend: hf`, `synthetic_proxy: false`, and one cell with `n_records: 1200` (`results/E-0013-uncertainty-recheck/run_manifest.json:3-4`, `results/E-0013-uncertainty-recheck/run_manifest.json:53-65`).
- Generation identity is `max_new_tokens=64`, `temperature=0.7`, `seed=20260723`, `k_samples=5` (`results/E-0013-uncertainty-recheck/run_manifest.json:23-26`), matching prereg (`docs/research/2026-08-03-uncertainty-format-recheck/prereg-e0013-DRAFT.md:22-24`).
- Effective model is `Qwen/Qwen2.5-7B-Instruct`, identity key `qwen2.5-7b-instruct`, matching the frozen model-family key (`results/E-0013-uncertainty-recheck/run_manifest.json:17-21`, `results/E-0013-uncertainty-recheck/run_manifest.json:46-49`). The run log also states the CAA×Qwen HF run with layer 20, alpha 8.0, prompt `unc-strong-01` (`results/E-0013-uncertainty-recheck/run_e0013_caaqwen.log:2`).
- CAA direction is recorded as `caa_mean_difference_at_frozen_layer` (`results/E-0013-uncertainty-recheck/run_manifest.json:50-51`), and the runner derives CAA via `_extract_direction` at the frozen layer (`scripts/run_uncertainty_format_recheck.py:204-206`).

### 5. Worst-case bounds

I recomputed the adversarial imputation bounds and matched `reanalysis.json`:

- least favorable to steer: **−0.4783562264150944** over 53 items.
- most favorable to steer: **+0.2499456603773585** over 53 items.

These are reported, not hidden (`results/E-0013-uncertainty-recheck/reanalysis.json:60-70`). The +0.250 bound means a mathematically adversarial assignment of all missing confidence scores can flip the sign. I do **not** view that as the principled headline, because it assigns extreme scores to missing outputs rather than using observed parsed confidences. The principled readout for the parser-imputation confound is the pre-stated paired-compliant analysis, but the worst-case bound must remain disclosed as an adversarial sensitivity caveat.

### 6. Scope honesty

The prereg names four cells (`docs/research/2026-08-03-uncertainty-format-recheck/prereg-e0013-DRAFT.md:13-18`), but this artifact contains only `caa__qwen2.5-7b` (`results/E-0013-uncertainty-recheck/run_manifest.json:50-56`; `results/E-0013-uncertainty-recheck/run_e0013_caaqwen.log:2`). Therefore E-0013 closes the format-confound objection only for **CAA×Qwen**, the largest-effect cell. It does **not** recheck ITI×Qwen, CAA×Llama, or ITI×Llama; those blocked cells must be explicitly disclosed as limitations.

## Ranked findings

### BLOCKER

None for the narrow claim: **CAA×Qwen harm survives among paired format-compliant generations**.

### MAJOR-1 — Scope must not be generalized beyond one cell

- **Evidence:** prereg planned four cells (`prereg-e0013-DRAFT.md:13-18`), but manifest/log contain only `caa__qwen2.5-7b` (`run_manifest.json:50-56`, `run_e0013_caaqwen.log:2`).
- **Impact:** A paper/result summary that says the E-0013 recheck resolves the format confound for the uncertainty result globally would be unsound.
- **Minimum fix in claims:** state exactly: “In the largest CAA×Qwen cell, harm survives on paired format-compliant generations; other cells were not rechecked.”

### MAJOR-2 — Compliant-only is a valid confound stress test, not an unbiased full-population estimand

- **Evidence:** the restriction conditions on post-generation compliance (`scripts/run_uncertainty_format_recheck.py:383-386`) and drops 17/53 TEST items from the paired-compliant item set.
- **Assessment:** This can introduce selection/collider bias if compliance is affected by condition and item difficulty. It should not be sold as the unbiased treatment effect among all possible generations.
- **Why it still answers the fatal confound:** the original worry was “steer looks harmful because it drops confidence more and gets imputed.” Here steer is **more** compliant than prompt (0.826 vs 0.445), and after removing imputed pairs entirely the harm is larger (−0.337 vs −0.209) with CI excluding zero. Thus parser/imputation is not the source of the CAA×Qwen harm.

### MINOR-1 — Worst-case sensitivity can flip sign and must remain visible

- **Evidence:** most-favorable-to-steer bound is +0.249946 (`reanalysis.json:67-70`).
- **Impact:** This is an adversarial extreme, not the main readout, but hiding it would overstate certainty.
- **Required disclosure:** keep both the compliant-only result and the worst-case bound in any paper/ledger summary.

### UNVERIFIED

I did not rerun the HF generation or load the GPU model. This audit recomputed the result from the captured `samples.jsonl`, checked code paths and manifest identity, and verified all recorded raw-text/parser/imputation fields internally.

## Final answer to the audit question

**Does the harm survive the format confound?** For **CAA×Qwen only**, yes. The result is not a confidence-format/parser-imputation artifact: steer is less likely to drop confidence format than prompt, and the paired format-compliant-only delta is more negative and statistically excludes zero.

**Final VERDICT:** **HARM-SURVIVES-BUT-CAVEATED**.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
