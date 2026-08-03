# Stage C — Associate/Area Chair Meta-Review and Decision

**Role:** Associate Chair (AC), ACM IUI (primary target); CHI/CSCW considered as the reviewers did.
**Materials read (independently, not via the reviews):** `docs/paper/main.tex` (full, incl. appendix), `docs/paper/claim-map.yaml`, `docs/paper/submission-evidence-ledger.md`, `docs/paper/tables/*.tex`, `docs/paper/table-manifests/*.yaml`, `docs/paper/figure-manifests/*.yaml`, `docs/ledgers/evidence-ledger.md` rows E-0003..E-0011.
**Review panel treated as three:** R1 = Stage A senior reviewer (`A-reviewer-opus5.md`, overall 2, reject at CHI/CSCW, weak-reject at IUI), R2 = Stage B skeptic (`B-reject-gpt56sol.md`, reject, confidence 4.5/5), R3 = this AC's own reading.
**E-0012 hygiene:** I independently confirmed that no E-0012 / verified-control / settling-grid material appears in `main.tex`, the submitted tables, or the table/figure manifests. E-0012 is terminated and out of scope; **no part of this decision credits or penalizes the paper for it.** Where I say "there is no positive control," I mean *in the submitted paper*, and any future positive control must be a new, independently audited, in-paper experiment.

---

## DECISION

| Venue | Decision | Notes |
|---|---|---|
| **ACM IUI (actual target)** | **REJECT** (formally *Weak Reject*, below the line at a ~25% venue) | Closest to acceptance of the three venues. One unresolved identification problem (format-vs-calibration) sits directly on the only informative finding; without it, the paper is 8 empty cells plus 4 cells of contested signal. Realistic path to acceptance in one cycle. |
| **ACM CHI** | **REJECT** | Contribution-type mismatch: a prescriptive interface contract with zero human, design-process, or system evidence, from benchmark data about models. The authors' own `claim-map.yaml` marks C3 `has_project_evidence_row: false`, `gate_result: FLAGGED`. |
| **ACM CSCW** | **REJECT** | Strictly worse fit; no social, collaborative, organizational, or practice dimension exists in the work at all. |

**Overall AC score: 2.5 / 5 (IUI), 2 / 5 (CHI), 1.5 / 5 (CSCW). AC confidence: 4/5.**

This is not a punitive reject. The paper is more honest than most submissions I handle, and the *reason* it can be rejected so cleanly is partly that the authors disclosed the very facts (MDE table, format-drop note, `valid_for_paper=false` flags, same-pool split seeds) that a less scrupulous team would have buried. I want to say plainly to the authors: **the rigor infrastructure here is an asset, not a liability, and it is what makes a defensible resubmission achievable in one cycle.** But at a <25% venue, honest disclosure of a weakness is not a substitute for closing it.

---

## 1. Which criticisms are TRULY FATAL (for this submission, as submitted)

I find **three** fatal issues. Everything else is severe-but-fixable or overstated.

### F-1. The confidence-format confound on the only informative finding (R1 W3/T1, R2 C3/M4) — **FATAL, and the single most decisive issue**
The uncertainty outcome is `1 − (conf_i − correct_i)²`, parsed from a self-reported confidence token. The paper itself states (L229, quoting the E-0006 audit) that **"steered uncertainty outputs often dropped the required confidence format."** The paper never discloses what the parser assigns when the format is absent (0.5? 1.0? drop the item? last-number heuristic?). That single undisclosed rule can flip the interpretation of the headline from *"steering worsens calibration"* to *"steering breaks instruction-format adherence, and the scoring rule punishes that."*

I verified an aggravating asymmetry the reviewers only partly surfaced: `table-manifests/c2-delta-4cell.yaml` shows the DEV-selected uncertainty prompt for CAA×Qwen is *"Be honest about what you do not know. Flag every uncertainty and* ***tell me how confident you really are.***" — i.e., the prompt arm receives an explicit confidence-elicitation cue, while the steer-arm prompt is **never stated anywhere in the paper**. If the steer arm lacks an equivalent elicitation cue, the "calibration harm" contrast is partly a *format-elicitation* contrast by construction. This is not a nuance; it is an identification failure on the paper's headline. I note the E-0006 audit asserted "NOT parser artifact," but its stated basis is `trunc=0/empty=0` + coherence — which rules out truncation and degeneration, **not** format-drop-driven imputation. The audit does not close this.

**Why fatal now:** every other empirical statement in the paper is an underpowered non-detection. If F-1 is unresolved, the paper has zero robust findings.

### F-2. No positive control / manipulation check → unknown assay sensitivity (R1 W2/T2, R2 C4) — **FATAL**
The paper's entire thesis is a null. A null is informative only if the instrument is shown to be able to return non-null. This adjudicator has **never returned a pass on anything**, in any cell, in any arm (12/12 fail; the PSR arm 3/3 fail; the split-seed arm 20/20 fail). Nothing in the paper distinguishes "legible but not controllable" (the claimed finding, F1 in the failure taxonomy, and the title) from "this intervention at these α on this layer was behaviorally near-inert," "the endpoints are insensitive," or "the harness is mis-targeted."

The closest existing material is not sufficient: E-0007 reports activation `norm_inflation 1.0–1.95×` (the intervention moved activations) and E-0009 reports 47/53 items changed on uncertainty at α=24 — but those are activation-level and exploratory (`valid_for_paper=false`), and neither demonstrates that the *adjudicator* can detect a behavioral improvement it should detect. Without a positive control, the title claim is not identified.

### F-3. C3 (the interface contract) is a prescription with no evidence of any kind — **FATAL at CHI/CSCW; MAJOR-not-fatal at IUI**
No user study, no formative work, no expert walkthrough, no heuristic evaluation, no cognitive walkthrough, no comparison against model cards / FactSheets / datasheets, no designer interview (n≥3 would have been cheap and ungated). The console figure is a cropped static rendering. The authors hedge extensively and correctly, and their own gate record flags it. But CHI's currency is knowledge about people, practice, or interaction, and this paper produces none. Compounding it, the confidence/reliance literature the contract implicitly relies on (Bansal, Buçinca, Zhang/Liao) repeatedly finds that adding confidence/quality signals **fails or backfires** for calibrated reliance — none of it is cited, so the contract is not merely unevidenced, it is unevidenced *against a known adverse prior*.

At IUI this is survivable if C3 is demoted from "contribution" to "implication." At CHI/CSCW it is decisive on its own.

---

## 2. Which criticisms are FIXABLE (and how expensively)

**Fixable by writing/reanalysis alone (no new compute):** protocol under-reporting (k=5, temperature=0.7, `max_new_tokens=64`, batch_size=16, item-pool provenance, bootstrap variant, coherence-ratio values, the steer-condition prompt template, the parser/imputation rule); multiplicity across the 12-cell grid and the post-hoc directionality of the harm claim; symmetric application of δ=0.05 to harms as well as wins; a pooled/random-effects per-axis estimate that addresses the 4/4 positive deliberation trend honestly; abstract/title alignment ("split-seed robust" → "stable across five re-splits of one fixed item pool"); removing C1 from the Abstract/Conclusion given `valid_for_paper=false`; adding the missing HCI/documentation lineage (Amershi, Lee & See, Bansal, Buçinca, Zhang/Liao, Mitchell model cards, Gebru datasheets, Arnold FactSheets) with a row-by-row differentiation of the contract; renaming the baseline honestly (it is a **labeled-DEV-selected benchmark-oracle prompt policy**, not "what a non-expert could already do"); dropping or heavily qualifying "fairness-controlled"; deleting the appendix; fixing the `c2-calibration-harm-4cell.yaml` manifest, which still reads `status: "stub: plotting script/table source not yet created"` while the paper advertises artifact lineage as a credibility feature (a documentation bug, not a scientific one, but a costly own-goal); publishing a verifiable anonymized pre-registration/artifact link.

**Fixable only with new compute:** the positive control / manipulation check (F-2); the format-decomposition and parser-robustness reanalysis *if* the A800 transcripts cannot be retrieved (L277 says the per-item confidence/correctness pairs are not committed but "can be retrieved or reproduced"); same-direction READ↔TRANSFER validation for the exact frozen CAA **and ITI** directions/layers; a random/scrambled-direction control; a layer sweep in the adjudicated arm; larger N to lift MDE below δ; an ordinary-user/zero-shot prompt comparator and a best-of-{1,4,8,16} budget curve; the human/designer evaluation for C3.

**Not fixable within this paper's scope, and that is acceptable:** frontier-scale models, trained/optimized steering families beyond the exploratory PSR arm, multi-turn interactive settings. These are legitimate scope limits *if* the title and abstract are bounded to match.

---

## 3. Is the contribution sufficiently impactful?

**For CHI/CSCW: no, and not close.** Strip the HCI prose and not one number changes — R1's observation that "removing all HCI prose would not change a single number" is correct and is the crux. The five-signal contract is a documentation/evidence-tier artifact in a genre with a decade of prior art that the paper does not cite.

**For IUI: nearly, but not as submitted.** IUI does accept model-side evaluations with intelligent-interface implications, and the strongest asset here — a frozen, pre-registered, hostile-audited prompt-vs-latent adjudicator with a machine-generated artifact lineage — is a genuine *methodological* contribution of the kind IUI values. Two things hold it below the line: (i) an instrument that has only ever returned "fail" has not been shown to discriminate, so it is not yet a credible reusable instrument; (ii) the one empirical fact it produced is confounded. Fix those two and the methodological contribution becomes real. I would then expect a genuine argument at the PC table.

**On the "expected result" objection (R1's R3, R2's M10):** I discount this more than the reviewers do. Fan, Korznikov, and Sprejer point the same way, but none of them is a *pre-registered, fairness-audited head-to-head against a tuned prompt baseline with a frozen pass rule*. "The field already suspected this" is a weak reject argument when the prior literature is anecdotal and this paper is not. Novelty is not what sinks this submission; identification is.

---

## 4. Are the reviewers overestimating any weaknesses?

Yes, in six places. I record these because the authors deserve to know which attacks I do **not** endorse, and because an unfocused rebuttal that spends its budget here will fail.

1. **R2's C2 ("the prompt baseline is a benchmark oracle") cuts less than claimed.** An oracle-selected prompt makes the comparator *stronger*, which makes the negative verdict **conservative** for the "steering does not beat prompting" direction. R2 is right that it destroys the "realistic non-expert effort" framing — that language must go — but it does not undermine the negative result itself. A rebuttal should say exactly this.
2. **R1's W7 claim that `max_new_tokens=64` invalidates deliberation is partly overstated.** Both arms share the cap, so the paired contrast remains internally valid. The real damage is to *sensitivity* (it compresses both arms toward a floor and worsens the MDE problem) — i.e., it reinforces F-2 rather than being an independent fatal flaw. It absolutely must be disclosed, and its implications for the deliberation axis argued explicitly.
3. **R2's M8 (manifest contradiction) is a documentation bug, not a scientific one.** `plot_c2_calibration_harm.py` exists and the figure derives from the frozen cell JSONs; the manifest `status` string is stale. Embarrassing given the lineage claim, trivially fixed, not evidence of number-massaging. I explicitly do not treat it as an integrity concern.
4. **R2's M6 / R1's W10 (buried positive deliberation trend) is real but small.** All four deltas are +0.015 to +0.025, i.e., well below δ=0.05 and below most cells' MDE. It warrants a pooled estimate and honest discussion, not a claim of selective reporting. I read the framing asymmetry as a reporting gap, not a rhetorical trick.
5. **R2's C6 (construct validity of the axis names) is fixable, not fatal.** The paper already states the construct bound (L148). The correct remedy is terminological discipline — say "GSM8K accuracy," "false-premise rejection rate," "parsed-confidence Brier score," and reserve "deliberation/skepticism/uncertainty" for framing — not a new validation program.
6. **R2's m2 (internal audits are not independent) is fair as a discount, not as an attack.** No reviewer should credit self-organized audits as external validation, but the audit trail is still far above the median for reproducibility.

I also want to record what both reviewers got *right* and what I independently confirmed: the MDE column (up to 0.279) genuinely renders ~8 of 12 cells informationally empty; Bonferroni is applied within-cell across 3 axes but not across the 12-cell grid; δ is applied to wins but not to harms (three of four harms lie within a factor of ~2 of δ); "split-seed robust" in the Abstract is materially stronger than what E-0011 supports and what the body concedes; and C1 appears in the Abstract and Conclusion despite both E-0003 and E-0008 carrying `valid_for_paper=false`.

---

## 5. META-REVIEW (as it would be transmitted to authors)

This submission reports a frozen, pre-registered adjudication in which naive CAA and ITI activation steering compete against a DEV-selected 16-candidate prompt baseline on three metacognitive endpoints across Qwen2.5-7B and Llama-3-8B. All twelve method×model×axis cells fail the pre-registered pass rule; the Brier-derived uncertainty endpoint is negative with intervals excluding zero in all four cells. The authors convert this model-side negative into a five-signal "interface-evaluation contract" for cognitive consoles, explicitly without any human-subjects evidence.

All three reviewers, including me, recommend rejection, and — unusually — none of us doubts the authors' integrity. The paper publishes a post-hoc TOST table that undercuts its own framing, reports a pre-registered mechanism null as a null, declines to impute a Brier decomposition it cannot compute, and labels its split-seed arm as same-item-pool. Its numbers flow from frozen JSON through generating scripts into LaTeX. This is well above the median for submissions at this venue and the committee wants the authors to hear that clearly.

The rejection rests on three points on which the panel converged independently.

First, and decisively, the paper's only informative empirical result has an acknowledged and untested alternative explanation. The uncertainty endpoint is computed from a parsed self-reported confidence token, and the paper reports that steered outputs "often dropped the required confidence format." The parser's behavior on missing or malformed confidence is never disclosed, and the exact prompt used in the steer condition is never reported, while the supplementary manifest shows the DEV-selected prompt-arm text explicitly requests a confidence statement. The committee cannot presently distinguish "naive steering worsens calibration" from "naive steering degrades instruction-format adherence, and the scoring rule penalizes that." The prior audit's rebuttal (no truncation, no empty outputs, coherence gates passed) rules out degeneration, not format-driven imputation. Because every other cell in the grid is an underpowered non-detection, this single unresolved confound determines whether the paper has a robust finding at all.

Second, there is no positive control and no manipulation check, so the sensitivity of the adjudicator is unknown. The instrument has returned "fail" in every cell of every arm it has ever been run on. Reviewers therefore cannot separate "a legible direction failed to transfer to behavior" — the claim in the title, in the F1 failure class, and in the contract — from "the intervention was behaviorally near-inert at these strengths and layers," "the endpoints are insensitive," or "the harness is mis-targeted." A null is evidence only when the apparatus has been shown capable of returning non-null. Relatedly, R2 raised a point the committee found persuasive: the READ measurement (C1) and the TRANSFER adjudication (C2) are not established on the same intervention object. C1 projects prompts onto a contrastively extracted axis pole, while ITI directions are probe-derived and are never shown to be READ-positive under the C1 measure. For the ITI cells, the paper cannot claim that a *legible* direction failed; only that *this probe intervention* did not beat prompting. That gap sits directly under the paper's title.

Third, the interface contribution is a prescription without evidence. The five-signal contract, the F1–F5 taxonomy, and the console figure carry no user data, no designer data, no formative or participatory work, no expert walkthrough, and no comparison against the documentation genre they most resemble — model cards, FactSheets, datasheets, and the Amershi guidelines, none of which are cited. The trust-calibration literature that the contract implicitly assumes (Lee & See; Bansal; Buçinca; Zhang/Liao) is also absent, and much of it finds that adding confidence and quality signals frequently fails to improve, and sometimes worsens, calibrated reliance. The authors' own claim map records this: C3 has `has_project_evidence_row: false` and `gate_result: FLAGGED`. The hedging is thorough and honest, but hedging is not evidence. For CHI and CSCW this alone is dispositive; for IUI it means C3 must be demoted from a contribution to an implication.

Supporting concerns the committee also weighed: the authors' own MDE column runs to 0.279 on a bounded [0,1] outcome, so roughly eight of twelve cells could not have detected any plausible effect, which makes "no demonstrated superiority across the grid" much weaker than the abstract implies; Bonferroni is applied across three axes within a cell but not across the twelve-cell grid, and the harm claim reads the opposite tail of a pre-registered superiority test without saying so; the δ=0.05 practical margin is applied to wins but not to harms, and three of four harms are within a factor of two of δ; "split-seed robust" in the abstract describes five re-splits of one deterministic first-N item pool, which the body itself concedes are not independent item draws; the search budgets (16 semantic prompt candidates versus 7 α values at one C1-chosen layer, never swept) do not establish the claimed "fairness control"; the comparator is a labeled-DEV-selected benchmark-oracle prompt policy and should not be described as "a realistic bounded interface-effort" without user evidence; C1 appears in the abstract and conclusion despite both underlying evidence rows being marked `valid_for_paper=false`; and the generation protocol (k, temperature, `max_new_tokens=64`, the steer-condition prompt, the parser, bootstrap variant, coherence-ratio values) is absent from the body, which by itself prevents adjudication of the central experiment.

The committee also notes several arguments it does **not** endorse, so the authors do not over-correct. The oracle-prompt objection strengthens rather than weakens the negative direction of the result — it damages the ecological framing, not the finding. The 64-token generation cap applies to both arms, so it degrades sensitivity rather than invalidating the paired contrast. The stale `status: "stub"` line in the calibration-harm figure manifest is a documentation defect, not an integrity problem. The four consistently positive deliberation deltas are all below δ and below most cells' MDE; they warrant a pooled estimate and honest discussion, not an accusation of selective reporting. And "the field already expected this" is not, in the committee's view, a strong argument against a pre-registered head-to-head; novelty is not what sinks this paper — identification is.

The committee's assessment is that a defensible resubmission is achievable in one cycle for IUI, and would require a different paper for CHI or CSCW. The minimum path is: resolve the format-versus-calibration confound with disclosed parser rules and a compliant-subset reanalysis; add a positive control and per-item behavioral change rates demonstrating that the adjudicator can return a pass when one exists; validate READ on the exact frozen CAA and ITI directions, or drop the legibility half of the thesis and retitle; disclose the full generation protocol; repair the statistical asymmetries; and either ground the contract in human data or demote it to an implication. Done well, that is a clean, honest, reusable negative-result and evaluation-instrument paper — which is a contribution the community currently lacks.

---

## 6. REBUTTAL ANALYSIS — what would most likely change my decision

Rebuttal budget is short; the authors should spend nearly all of it on **F-1**, then **F-2**, then **F-3-as-demotion**. Ranked by expected decision movement:

### Would move me most (potentially to Weak Accept / R&R at IUI)
1. **A quantitative resolution of the format confound, in the rebuttal itself.** Not a promise — numbers. Per-cell, per-condition confidence-format compliance rates (prompt arm vs steer arm), the exact parser/imputation rule, and the uncertainty deltas recomputed on the format-compliant subset only. **Either outcome helps them:** if the harm survives on compliant pairs, the headline is rescued and F-1 is closed; if it does not, the finding becomes *"naive steering breaks the confidence-elicitation format, which is what destroys the trust-relevant signal"* — a **more** interface-relevant and more publishable result than the current one, and one that maps directly onto their calibration-harm warning card. I would explicitly accept the reframed version. This is the single highest-leverage rebuttal move available. If the transcripts are retrievable, this is analysis-only and can be done inside a rebuttal window.
2. **Any credible demonstration of assay sensitivity.** A positive control at the same layers/α on a known-steerable target, or, failing that, per-item behavioral change rates per cell/axis plus a random/scrambled-direction control at matched α showing the adjudicator separates real directions from noise. If the authors can show the instrument returns a pass when it should, the negative becomes interpretable and the "inert intervention" alternative is closed. Even a partial version (change rates in the body + one small positive-control cell) would move me materially.
3. **A clean, honest retitle and rescope executed in the rebuttal.** If READ cannot be validated on the exact ITI directions, say so and retitle to a failed-superiority claim ("Naive CAA/ITI Steering Does Not Beat a Tuned Prompt Baseline on Metacognitive Endpoints") with the legibility→control thesis demoted to motivation. Authors often resist this; here it would substantially raise my confidence in the paper's calibration, because the current title is licensed only for the CAA cells at best.

### Would move me somewhat (removes reject arguments but does not create acceptance)
4. **Full protocol disclosure with an explicit argument about the 64-token cap on the deliberation axis** — including a statement of the steer-condition prompt and a defense of its comparability to the prompt arm. This is the cheapest possible fix for one of the panel's blockers and its absence is currently inexplicable.
5. **Symmetric statistics:** δ applied to harms, multiplicity corrected across 12 comparisons, harm direction labeled post-hoc, and a pooled per-axis random-effects estimate including the deliberation trend. Doing this *even though it weakens three of four harm cells* would be strong evidence of the epistemic discipline the paper claims.
6. **The missing HCI/documentation lineage plus a row-by-row differentiation of the contract from a per-axis model card.** Cheap, and it converts the panel's "unaware of its own genre" read into "aware and differentiated."
7. **An anonymized, timestamped pre-registration and artifact link.** Pre-registration is the paper's central rigor claim and is currently unverifiable; verified, it is worth a meaningful amount of reviewer goodwill.

### Would NOT move me
- Further hedging, additional caveat sentences, or restating that C3 is "not a user-study claim." The panel already credited the hedging; more of it does not create evidence.
- Arguing that a positive control is unnecessary because the coherence gate passed. It is not the same test and the committee will not accept the substitution.
- Citing the E-0006 audit's "NOT a parser artifact" line as settling F-1. Its stated basis (`trunc=0/empty=0`, coherence) does not address format-drop imputation, and the audit is internal.
- Promising the deferred human study as future work. Deferral is already stated; a promise does not change the current evidence base.
- Arguing that the result is important because the field needs negative results. True, and it is why I would welcome the resubmission — but it does not repair identification.

### Rebuttal outcomes and my likely landing point
| Rebuttal delivers | My IUI position |
|---|---|
| Format-compliance numbers + compliant-subset reanalysis + change rates/positive control + protocol disclosure | **Weak Accept / Accept-with-shepherding** |
| Format resolution only (either direction), with reframe and protocol disclosure | **Borderline**, would argue for R&R rather than reject |
| Positive control only, format confound still open | **Weak Reject** (unchanged) — the headline remains unidentified |
| Reframing, extra caveats, promises of future runs | **Reject** (unchanged) |
| Any rebuttal, for CHI/CSCW | **Reject** — no rebuttal can supply the missing human/design evidence within a cycle |

---

## 7. PRIORITIZED, ACTIONABLE FIX LIST

Decisiveness key: **[DECISIVE]** = acceptance is not achievable without it; **[NEAR-DECISIVE]** = its absence gives any single reviewer a complete reject; **[SUPPORTING]** = removes an attack, does not by itself create acceptance.

### (a) Achievable by WRITING / REPORTING / REANALYSIS ONLY — no new experiments

| # | Fix | Effort | Decisive? |
|---|---|---|---|
| **A1** | **Disclose the confidence parser and imputation rule verbatim** (what is scored when the confidence field is missing/malformed: dropped, 0.5, 1.0, last-number heuristic), and **disclose the exact steer-condition prompt template** alongside the prompt-arm template. State whether both arms received equivalent output-format instructions. | 0.5 day | **[DECISIVE]** — this is the precondition for evaluating the headline at all. |
| **A2** | **Format-decomposition reanalysis on existing transcripts** *(analysis-only if the A800 transcripts are retrievable; see B1 otherwise)*: per-cell, per-condition format-compliance rates; uncertainty deltas recomputed on format-compliant pairs only; both versions reported side by side. Report the Murphy reliability/resolution decomposition if the per-item (confidence, correctness) pairs come back with the transcripts. | 2–3 days | **[DECISIVE]** |
| **A3** | **Full generation-protocol disclosure in the body:** k=5, temperature=0.7, `max_new_tokens=64`, batch_size=16, stop criteria, item-pool provenance and first-N slicing, coherence-ratio values per cell, bootstrap variant (percentile vs BCa) and B. Argue explicitly what a 64-token cap implies for the deliberation axis; consider demoting that axis. | 1 day | **[NEAR-DECISIVE]** — its absence alone justifies reject at an archival venue. |
| **A4** | **Repair the statistical asymmetries:** apply δ=0.05 symmetrically to harms (and report that 3/4 harm cells then become borderline); correct multiplicity across all 12 grid comparisons; explicitly label the harm claim as the post-hoc opposite tail of a pre-registered superiority test; report a pooled per-axis random-effects estimate covering the 4/4 positive deliberation trend. | 1–2 days | **[NEAR-DECISIVE]** |
| **A5** | **Rewrite abstract, title framing, and contribution list to match the body.** Remove C1 from Abstract/Conclusion (both rows are `valid_for_paper=false`); replace "split-seed robust" with "stable across five DEV/TEST re-splits of one fixed item pool"; state up front that ~8/12 cells are informationally empty (MDE up to 0.279); drop "fairness-controlled" or downgrade to "matched DEV-selection discipline (budgets not matched)"; retitle away from the general modal claim if READ cannot be validated on ITI (see B3). | 1 day | **[NEAR-DECISIVE]** |
| **A6** | **Rename the comparator honestly:** it is a labeled-DEV-selected benchmark-oracle prompt policy, not "a realistic bounded interface-effort" or "what a non-expert already has." Note explicitly that this makes the negative *conservative* — this converts R2's C2 from an attack into a strength. | 0.5 day | **[SUPPORTING]**, high value per unit effort |
| **A7** | **Demote C3 from contribution to implication** (if B6 is not run): remove the contract from the Abstract contribution list, compress §6 to a short "implications for evaluating latent-control interfaces," move or shrink the console figure, remove "working console instantiation" from the contribution language. | 1 day | **[DECISIVE for IUI]** if B6 is not run |
| **A8** | **Add and differentiate the missing literature:** Amershi et al. (Guidelines for Human-AI Interaction), Lee & See, Bansal et al., Buçinca et al., Zhang/Liao, Mitchell et al. (model cards), Gebru et al. (datasheets), Arnold et al. (FactSheets). Include a row-by-row table showing what the five-signal contract adds beyond a per-axis model card, and engage the finding that confidence signals often fail to improve calibrated reliance. | 0.5–1 day | **[SUPPORTING]**, but it neutralizes the cleanest reject argument at any HCI venue |
| **A9** | **Terminological discipline on constructs:** use "GSM8K accuracy," "false-premise rejection rate," "parsed-confidence Brier score" in Results and Claims; reserve deliberation/skepticism/uncertainty for framing with an explicit statement that no convergent/discriminant validation was performed. | 0.5 day | **[SUPPORTING]** |
| **A10** | **Housekeeping:** regenerate `figure-manifests/c2-calibration-harm-4cell.yaml` (it still reads `status: "stub: plotting script/table source not yet created"` while the paper sells artifact lineage); publish an anonymized, timestamped pre-registration + artifact link including the per-item confidence/correctness pairs; delete the appendix social-inference study (`valid_for_paper=false`, LLM-judge-only, M2/M3 unimplemented); reduce hedging density ~30%; show the console figure uncropped or explain the crop. | 1 day | **[SUPPORTING]** |

**If the authors can do only three things in (a): A1, A2, A3.**

### (b) REQUIRING NEW COMPUTE / EXPERIMENTS

| # | Fix | Effort | Decisive? |
|---|---|---|---|
| **B1** | **Regenerate the uncertainty-arm transcripts** if the A800 transcripts cannot be retrieved, so that A2 (format compliance + compliant-subset reanalysis + Brier decomposition) becomes possible. Same frozen protocol, uncertainty axis only, 4 cells. | ~1 GPU-day | **[DECISIVE]** — this is the compute-side fallback for the single most decisive fix. |
| **B2** | **Positive control / manipulation check.** A pre-registered, independently audited run at the same layers and α scale on a target the literature agrees is steerable (e.g., refusal rate, sentiment, or an explicit format-following target), demonstrating the adjudicator returns a **pass** when a controllable effect exists. Pair it with a random/scrambled-direction negative control at matched α, and report per-item behavioral change rates for all adjudicated cells. Must be a fresh, in-paper, pre-registered experiment. | 2–4 GPU-days + preregistration | **[DECISIVE]** — without it, the paper's central null is uninterpretable and the title is unlicensed. |
| **B3** | **Same-direction READ↔TRANSFER validation.** Run the C1 facade/READ measurement on the **exact frozen CAA and ITI directions and layers** used in C2, per model, per axis; then test whether direction-level READ magnitude predicts TRANSFER outcome. Without this, the ITI cells cannot support a legibility→control claim and the title must change (A5). | 1–2 GPU-days | **[DECISIVE for the title/thesis]**; if not run, A5's retitle becomes mandatory. |
| **B4** | **Power repair on the informative axes.** Increase TEST N (items are cheap relative to GPU time already spent) so MDE < δ = 0.05 in the cells that carry claims; restrict grid-level negative language to cells meeting that bar; report prospective power. | 2–3 GPU-days | **[NEAR-DECISIVE]** for any statement framed as a *generalized* negative; not required if claims are restricted to the adequately powered cells. |
| **B5** | **Comparator-adequacy and budget characterization.** Best-of-{1,4,8,16} prompt-budget curves, a zero-shot/default-prompt arm, a random-prompt lower bound, plus a DEV-side α-grid density and layer sweep for at least one cell (F4 in the paper's own taxonomy is currently an uncontrolled confound in the paper's own study). Report DEV→TEST shrinkage for the selected prompt and selected α. | 2–3 GPU-days | **[SUPPORTING]**, but it is what would let "fairness-controlled" be re-earned rather than deleted |
| **B6** | **Human/designer evidence for C3.** Minimum viable: a structured expert walkthrough or heuristic evaluation with 8–12 designers/ML practitioners rating comprehensibility and actionability of the five contract signals against a model-card baseline, reported as formative. Full version for CHI/CSCW: a controlled study of whether TRANSFER/calibration-harm signals improve calibrated reliance. Ethics/owner-gated. | 1–2 weeks (formative); one cycle (controlled) | **[NOT decisive for IUI]** if A7 is done; **[DECISIVE for CHI/CSCW]** — and the controlled version is a different paper. |

### Minimum defensible resubmission path

- **To IUI (one cycle, realistic):** A1 + A2 (or B1→A2) + A3 + A4 + A5 + A6 + A7 + A8 + **B2**, and either **B3** or the retitle in A5. That is roughly 1 week of writing/reanalysis plus 3–6 GPU-days. The resulting paper — a disclosed, sensitivity-validated, honestly-scoped negative result plus a reusable adjudication instrument that has been *shown to discriminate* — is one I would expect to argue for at the PC table.
- **To CHI/CSCW:** all of the above **plus B6 executed as a real study**. That is a different paper and approximately one full cycle of additional work. I would not advise it; the work's centre of gravity is an evaluation instrument, and IUI (or an ML venue) is the right home until human evidence exists.

---

## 8. AC SUMMARY

| Item | Verdict |
|---|---|
| **IUI** | **Reject** (formally Weak Reject; below the line). Strong one-cycle path to acceptance. |
| **CHI** | **Reject.** |
| **CSCW** | **Reject.** |
| **Truly fatal** | (1) Confidence-format confound on the only informative finding, with an undisclosed parser rule and an undisclosed steer-condition prompt against a confidence-eliciting prompt-arm text; (2) no positive control → unknown assay sensitivity for a paper whose entire thesis is a null (aggravated by READ/TRANSFER not being established on the same intervention, especially ITI); (3) C3 asserted with zero evidence of any kind — fatal at CHI/CSCW, demotable at IUI. |
| **Fixable** | Everything else: protocol under-reporting, multiplicity and asymmetric δ, abstract/title overreach, "fairness-controlled" and "realistic user effort" language, C1 in the abstract, missing HCI/documentation literature, power scoping, manifest hygiene, the appendix. Most of it is writing and reanalysis, not compute. |
| **Reviewers overestimate** | The oracle-baseline objection (it makes the negative conservative), the 64-token cap as an independent invalidator (it degrades sensitivity, both arms share it), the stale manifest as an integrity issue, the "buried" deliberation trend (all below δ and below MDE), construct-validity as fatal rather than terminological, and "the field already expected this" as a rejection ground. |
| **Single most decisive fix** | **A1 + A2: disclose the confidence parser/imputation rule and the steer-condition prompt, then re-run the uncertainty analysis restricted to format-compliant generations (retrieving or regenerating transcripts via B1 if needed).** Whichever way it comes out, the paper gains a defensible headline — either "steering genuinely worsens calibration" or the more interface-relevant "naive steering destroys the confidence-elicitation format that trust-relevant signals depend on." As submitted, the paper cannot tell the reader which is true, and that is why it cannot be accepted. |

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
