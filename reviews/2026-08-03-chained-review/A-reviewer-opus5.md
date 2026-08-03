# Hostile Review A — "Legible Need Not Be Controllable"

**Reviewer role:** senior PC member, ACM CHI / CSCW / IUI (< 25% acceptance).
**Posture:** adversarial. My job is to find every reason this paper can be rejected, not to help the authors.
**Materials read:** `docs/paper/main.tex` (full, incl. appendix, 303 lines), `claim-map.yaml`, `submission-evidence-ledger.md`, `tables/*.tex`, `table-manifests/*.yaml`, `figure-manifests/*`, `references.bib`, evidence rows E-0003..E-0011.
**Scope note:** I found **no** stray references to the terminated E-0012 / verified-control / settling-grid / comparator-strength material in the paper body, tables, or manifests (grep clean). That hygiene point is *not* a criticism; everything below is.

---

## TASK 1 — High-level assessment

### 1.1 One-sentence summary
The paper runs a pre-registered, frozen behavioral adjudication in which naive CAA and ITI activation steering compete against a 16-candidate "bounded best-prompt" baseline on three metacognitive axes across Qwen2.5-7B and Llama-3-8B, finds zero passing cells (12/12 fail) plus consistent negative effects on a Brier-based uncertainty score, and converts this negative model-side result into a prescriptive five-signal "interface-evaluation contract" for cognitive consoles — **with no users, no user study, and no user data anywhere in the paper**.

### 1.2 Claimed contributions (as stated, L55–72)
1. **C1 (explicitly exploratory):** a two-model "representational facade" precondition measurement (Table `tab:c1-twomodel`).
2. **C2 core:** a frozen, pre-registered, fairness-controlled, audited prompt-vs-latent behavioral adjudication across 2 methods × 2 models.
3. **C2 result:** failed-superiority in every tested cell + robust calibration harm on the uncertainty axis (Table `tab:c2-delta-4cell`, Fig. `fig:c2-calibration-harm`).
4. **C3:** an "interface-evaluation contract" (READ / TRANSFER / bounded-prompt comparator / calibration-harm warning / evidence tier) plus a working console instantiation (Fig. `fig:console`), explicitly *not* a user-study claim (L70–74, L245–252).

### 1.3 Actual contributions (my opinion)
- **A genuine, well-documented negative ML result of modest scope.** The pre-registration + frozen pass rule + hostile-audit discipline is real and above the median for HCI submissions. This is the paper's only defensible core.
- **One narrow empirical fact worth knowing:** on a Brier-derived uncertainty score, naive CAA/ITI at DEV-selected α degrade performance relative to a DEV-selected prompt in 4/4 cells. Even this is contaminated by a format-compliance confound the authors themselves surface (L229).
- **A rhetorical/organizational contribution:** the READ/TRANSFER/evidence-tier vocabulary and the F1–F5 failure taxonomy. This is *design rhetoric*, not design knowledge — it is asserted, not derived from data, not compared to alternatives, and not evaluated with a single human.
- **Not a contribution:** C1 (self-declared exploratory, `valid_for_paper=false` in both E-0003 and E-0008), C2-mech (pre-registered null), C4 (appendix, `valid_for_paper=false`), and the console UI (an unevaluated screenshot).

### 1.4 Main strengths
- **S1. Methodological honesty is unusually high.** The paper distinguishes failed-superiority from equivalence (L211–215), reports a post-hoc TOST table that *undercuts* its own framing, labels the split-seed arm as same-item-pool (L217, L271), reports a pre-registered mechanism null (L229), and refuses to impute a Brier decomposition (L277). Many accepted CHI papers would have hidden all five.
- **S2. Artifact lineage.** Numbers flow from frozen JSON through generating scripts into `.tex` (L185–190); the C2 and TOST tables carry auto-generation headers. This is genuinely rare.
- **S3. The framing question is the right one.** "Is a legible axis a safe control affordance?" is a real and timely question for the feature-steering-UI wave (Huang & Lim; Anthropic-style feature sliders).
- **S4. Scope discipline in prose.** The paper repeatedly refuses the impossibility-theorem reading (L51, L91, L213, L271).

### 1.5 Main weaknesses (ranked; details in Tasks 3–4)
- **W1 (fatal for CHI/CSCW).** The HCI contribution is a *contract asserted from model evidence*, with zero human data, zero formative work, zero expert walkthrough, zero heuristic evaluation. The authors' own `claim-map.yaml` marks C3 `has_project_evidence_row: false` and `gate_result: FLAGGED`. A venue whose currency is human-centered knowledge is being asked to accept a design prescription with no design evidence of any kind — not even a cognitive walkthrough or a designer interview (n≥3 would have been cheap).
- **W2 (fatal for the headline).** **No manipulation check / positive control.** For deliberation and skepticism the point estimates are ±0.000–0.025 with CIs that are near-degenerate on Llama skepticism (+0.000 [−0.190,+0.205]). Nothing in the paper demonstrates that the steering pipeline *did anything at all* on those axes. A null that is indistinguishable from "intervention inert" is not evidence about controllability; it is evidence about the harness. The authors report per-item change rates nowhere in the body (E-0009 reports 47/53 changed for uncertainty only — and E-0009 is exploratory and `valid_for_paper=false`).
- **W3 (fatal for construct validity of the single robust finding).** The uncertainty outcome is 1 − (conf − correct)², and the E-0006 audit found that **steered outputs "often dropped the required Confidence format"** (L229). The paper never states what the parser assigns when the format is missing. If a missing/failed confidence string maps to any default (0.5, 1.0, drop, or last-token heuristic), then "calibration harm" is partly or wholly **instruction-format degradation**, i.e., a well-known and unsurprising steering side effect, not a calibration finding. This single undisclosed parser rule can invert the paper's headline interpretation. **BLOCKER.**
- **W4 (severe).** **Power is catastrophic and the paper's own TOST table proves it.** MDE_sup ranges from 0.039 to **0.279** (`equivalence-tost.tex`). Skepticism on Llama requires a true effect of ~0.27 on a bounded [0,1] rate before this design could detect it. Declaring "no demonstrated superiority" across a grid where 8/12 cells cannot detect anything short of an enormous effect is close to vacuous. N_test = 40 items (deliberation, skepticism) and 53 (uncertainty).
- **W5 (severe).** **"Fairness-controlled" is asserted, not demonstrated.** The prompt channel searches 16 candidates; the latent channel searches 7 α values on a single pre-chosen layer (L146). That is an asymmetric search budget (16 vs 7), a single-hyperparameter latent search vs a semantic search, and a layer chosen from *C1 diagnostics on the same models*. DEV pools are N=20/20/27. Selecting a winner among 16 candidates on 20 binary-outcome items is selection noise, not tuning. The paper's fairness claim (L146, "symmetric DEV-only selection") is a definitional sleight of hand: same *data* ≠ same *budget*, and the paper never runs the obvious sensitivity check (e.g., 2nd-best-prompt or random-prompt comparator).
- **W6 (severe).** **Ecological validity is essentially zero for an HCI venue.** The tasks are GSM8K and TruthfulQA slices (disclosed only in passing, L217). No console task, no realistic user query distribution, no interactive session, no multi-turn use. Nothing in the study touches the setting the design implications are about.
- **W7 (severe).** **Under-reporting of the experimental protocol in the paper.** The body never reports: k (samples per item), decoding temperature, `max_new_tokens`, item-pool provenance beyond one clause, coherence-ratio values, per-cell change rates, or the confidence-parsing rule. From the ledger, generation used `max_new_tokens=64, temperature=0.7, k=5`. **A 64-token generation cap on GSM8K makes "deliberation" nearly unmeasurable** — the model is structurally prevented from deliberating. If true, the deliberation axis is invalid by construction, and the reviewer cannot tell from the paper alone. Either way this is a reporting failure that a top-tier PC will not forgive.
- **W8 (moderate–severe).** **Contribution inflation in the framing.** Title and abstract promise "Legible Need Not Be Controllable"; the evidence supports "in 12 tiny cells on two 7–8B open models with two off-the-shelf steering recipes at 64-token generations, we could not detect superiority, and one Brier-based score got worse." The gap between the aphoristic title and the delivered evidence is exactly what reviewers punish.
- **W9 (moderate).** **Positioning against HCI literature is thin.** `references.bib` contains **no** Amershi et al. (Guidelines for Human-AI Interaction), no Lee & See, no Bansal, no Buçinca (cognitive forcing), no Zhang/Liao/Bellamy trust-calibration studies, no Mitchell model cards, no Gebru datasheets, no Yang et al. on design-implication practice. The proposed "contract" is a documentation/evidence-tier artifact — a direct descendant of model cards/FactSheets/AI guidelines — and the paper does not acknowledge, cite, or differentiate from any of them. This is the single easiest reject argument for a CHI AC.
- **W10 (moderate).** **Internal inconsistency between the headline and the data.** Deliberation deltas are positive in **all four** cells (+0.015, +0.025, +0.020, +0.015), and the TOST 90% CI for ITI×Qwen deliberation is **[+0.005, +0.040] — strictly positive**. A consistent small positive effect across 4/4 cells is at minimum worth a pooled/meta-analytic test; the paper instead files it under "underpowered non-detection" and, for two cells, under "equivalence." A skeptical reviewer will read this as selective framing: the negative uncertainty effects are elevated to a headline finding, while a directionally consistent positive deliberation trend is dismissed.
- **W11 (moderate).** **Asymmetric application of the meaningful margin δ = 0.05.** A *win* requires |Δ| ≥ 0.05; a *harm* is claimed with Δ = −0.072, −0.084, −0.103 (three of four cells within a factor of two of δ, and CAA×Llama's TOST CI is [−0.095,−0.047], straddling δ). The paper applies a practical-significance filter to gains but not to losses. If δ is the threshold for "practical control," it must also be the threshold for "practical harm."
- **W12 (moderate).** **Multiplicity is corrected within cell, not across the grid.** Bonferroni is over 3 axes (Eq. `eq:bonferroni-ci`), yet the calibration-harm claim is a joint statement over 12 cell×axis comparisons. The harm claim is also **directionally post-hoc**: the pre-registration tested superiority; harm is a reading of the other tail of the same interval. The paper should say so explicitly and it does not.
- **W13 (moderate).** **"Split-seed robust" is close to circular.** Five seeds re-split the *same* item pool (L217, L271; E-0011 explicitly: "NOT independent item draws"), and seed 20260723 is a *reuse* of the E-0006 artifact, with the harness check acknowledged as self-referential (E-0011, MAJOR#2). The paper discloses this honestly but still uses the word "robust" and puts it in the Abstract and Conclusion. Re-splitting 60–80 fixed items five ways demonstrates split stability, not sampling robustness — and reviewers will read "split-seed robust" in the abstract as more than it is.
- **W14 (minor–moderate).** **Reproducibility is claimed but not demonstrable at review time.** "Supplementary material" and "supplementary archive" are referenced repeatedly (L138, L185–190) with no anonymized URL, no DOI, no OSF/AsPredicted registration link for a paper whose central selling point is *pre-registration*. A pre-registration claim with no verifiable timestamped registration is, to a hostile reviewer, an unverifiable claim. Additionally, the per-item confidence/correctness pairs — the data needed to check the calibration headline — are explicitly **not committed** (L277).
- **W15 (minor).** The appendix (L294+) reports an entire additional experiment (novice-disclosure, N=54, LLM-judge-only, human-α pending, `valid_for_paper=false`) that supports no claim. It reads as CV-padding and gives reviewers a free target.
- **W16 (minor).** Figure `fig:console` is a `trim=0 390 0 35,clip` crop of a screenshot. Cropping the artifact that instantiates the paper's fourth contribution invites the question of what was cropped out.

---

## TASK 2 — Novelty assessment

### Is the problem truly new?
**No.** "Interpretable ≠ controllable" and "steering degrades capability" are, as of this submission, actively converging results:
- Sprejer et al. (`sprejer2026mindgap`) report capability–behavior trade-offs under feature steering — the paper concedes this is the "closest empirical neighbor" and calls it concurrent corroboration (`tab:novelty-neighbors`).
- Fan et al. (`fan2026asteer`, "When is Your LLM Steerable?") already establishes conditionality/limits of steerability.
- Korznikov et al. (`korznikov2025rogue`) already establishes that steering causes collateral damage.
- Mishra et al. (`mishra2026nonsurj`) already supplies the prompt/latent gap at the representation level.
- Heyman & Vandeputte (`heyman2026steer`) already shows the *positive* case (trained steering mimics prompting), which the paper concedes bounds its claim.

So the conceptual payload — "naive steering may not beat prompting and may hurt" — is already in the air from at least four directions. What is new is *this particular adjudication protocol* and the HCI framing.

### Is the contribution incremental?
**Yes, substantially.** Strip the framing and the delta over prior work is: (a) a different steering family pair (CAA/ITI instead of SAE features), (b) different tasks (GSM8K/TruthfulQA instead of MMLU), (c) pre-registration, (d) an HCI vocabulary layered on top. (a) and (b) are parameter swaps. (c) is process rigor, not a finding. (d) is unevaluated.

### Which prior work makes this work most vulnerable?
1. **Heyman & Vandeputte.** If trained steering mimics prompting, the paper's negative reduces to "we used weak methods." The authors anticipate this with the PSR-style arm — but that arm is **single-model, single-seed, `valid_for_paper=false`, exploratory** (E-0009), so it does not actually close the objection; it only signals awareness of it. A reviewer will say: the one experiment that could rebut the strongest counter-argument was run at exploratory grade.
2. **Sprejer et al.** Concurrency is arguable; if the PC deems it prior, the empirical novelty collapses to the pre-registration and the axis choice.
3. **Fan et al. / Korznikov et al.** Both already predict this outcome; the paper therefore confirms an expectation rather than overturning one. Negative results earn top-tier acceptance when they *falsify a widely-held belief*. This one falsifies a belief the steering literature was already abandoning.
4. **Huang & Lim (`huang2025steering`).** The nearest HCI neighbor — an actual layperson steering interface with actual design work. The present paper has a console figure and no users, which makes the HCI comparison unflattering.
5. **Model cards / FactSheets / Amershi guidelines (uncited).** The "contract" is a documentation-and-evidence-tier proposal in a genre with a decade of prior art. Not citing it looks either careless or convenient.

### Novelty gaps
- No new mechanism, no new method, no new measure with demonstrated validity, no new interface technique, no new empirical phenomenon that prior work did not anticipate.
- The "facade ratio" (Eq. `eq:facade-ratio`) is a new *quantity*, but it is exploratory, has no validation, is axis-inconsistent across two models (uncertainty and focus swap status — Table `tab:c1-twomodel`), and is explicitly excluded from the contribution.

### Positioning weaknesses
- The paper's own novelty table (`tab:novelty-neighbors`) is defensive: five of seven rows are "we are not X." Reviewers read defensive novelty tables as an admission.
- The differentiator claimed most often is *the protocol* ("frozen, pre-registered, fairness-controlled"). Protocol rigor is a hygiene expectation at top venues, not a contribution slot.
- The HCI framing is bolted on: Sections 1, 6 (Interface-Evaluation Contract), and 8 do HCI; Sections 3–5 do ML evaluation. Removing all HCI prose would not change a single number.

### Contribution inflation
- **Abstract L37–41:** "This negative verdict is split-seed robust" — over-strong given same-pool re-splits (W13).
- **Abstract:** "consistently harmed in all four method–model cells" — true of the metric, unproven as *calibration* (W3).
- **L74:** "a working console instantiation" is listed alongside evidence-derived contributions; an unevaluated UI is not a systems contribution at CHI.
- **Title.** "Legible Need Not Be Controllable" asserts a general possibility claim licensed only by 12 underpowered cells.

### Verdict
**C — Mostly incremental.** (Borderline C/D for CHI and CSCW; C for IUI.) The rigor is above average; the novelty is below the bar.

---

## TASK 3 — Methodology audit

There is **exactly one** study (C2, with C1 as a setup measurement and two exploratory arms). There is **no** user study, so recruitment, participant diversity, and human sample size are **N/A but disqualifying** for CHI/CSCW's core contribution types.

### 3.1 Study design
- **Design:** within-item paired comparison, DEV/TEST split, 2 methods × 2 models × 3 axes = 12 pre-registered cells, item-cluster bootstrap (B ≥ 10,000), Bonferroni across 3 axes, δ = 0.05, coherence gate ≤ 1.5×.
- **Positives:** paired design, disjoint TEST, pre-registered pass rule, frozen outcomes, coherence gate.
- **Negatives:** no positive control; no manipulation check; no second comparator (e.g., unsteered no-prompt control, random-direction steering control); single layer per model; single sampling seed; no ablation of α beyond the DEV pick; no human quality judgment of outputs.

**The missing arm that matters most:** a *random-direction* or *scrambled-direction* steering control at matched α. Without it, "steering does not beat prompting" is not separable from "additive residual perturbation at these α is behaviorally near-inert except for format damage."

### 3.2 Recruitment / participant diversity / sample size
- **Human participants:** none. Deferred and owner-gated (L74, L279).
- **Item sample size:** DEV 20/20/27, TEST 40/40/53. This is small even by ML standards and tiny for claims framed as design guidance.
- **Model diversity:** two 7–8B open instruct models. No frontier model (GPT/Claude/Gemini class), no MoE, no >13B, no base models, no reasoning-tuned models. Every commercially deployed "cognitive console" targets exactly the model class not tested.
- **Task diversity:** two benchmarks. No open-ended generation, no dialogue, no domain tasks.

### 3.3 Statistical validity
| Issue | Detail | Severity |
|---|---|---|
| Power | MDE_sup 0.039–0.279 (`equivalence-tost.tex`); 8/12 cells cannot detect < 0.07 | **BLOCKER** for any generalized negative framing |
| Multiplicity | Bonferroni over 3 axes only; 12 comparisons in the grid; harm claim is joint over 4 cells | MAJOR |
| Directionality | Superiority was pre-registered; harm is the other tail, read post hoc | MAJOR |
| Asymmetric δ | δ applied to wins, not to harms | MAJOR |
| Bootstrap validity | Item-cluster bootstrap with 40 clusters at a 98.33% level; tail coverage at B=10k with 40 clusters is fragile (BCa vs percentile not stated) | MAJOR |
| Selection noise | Best-of-16 on 20 binary DEV items; winner's-curse regression not quantified | MAJOR |
| Seeds | One generation seed; five *split* seeds on the same items | MAJOR |
| TOST | Post-hoc, SESOI = pre-reg δ chosen for convenience not for interface relevance; no justification that 0.05 on 1−Brier is meaningful to a user | MAJOR |
| Positive deliberation trend | 4/4 positive, one strictly positive TOST CI, no pooled analysis | MAJOR |

### 3.4 Confounds
1. **Format compliance vs calibration** (W3). The dominant confound. Steering degrades instruction-format adherence; the uncertainty score depends on parsing a confidence token. Unresolved.
2. **Generation length cap** (W7). If `max_new_tokens=64`, deliberation on GSM8K is truncation-limited; steering effects and prompt effects are both compressed toward a floor. Confounds the deliberation null completely.
3. **Layer selection from C1.** The intervention layer is derived from C1 extraction diagnostics (L146) — an analysis conducted on the same models with the same axis definitions. Any C1 pathology (e.g., the focus-axis overshoot, the Llama uncertainty non-facade) propagates into C2's layer choice, and there is no layer sweep in the adjudicated arm (the paper even lists layer sensitivity as failure class F4 in `tab:failure-taxonomy` — i.e., the paper names the confound it did not control).
4. **α range coupling to coherence gate.** DEV-selected α are small (2–12). The paper says the gate "did not drive the present verdict" (L237) but never reports whether higher α were *available* and rejected on DEV outcome or on coherence. If the DEV objective systematically preferred small, near-inert α, the negative is partly a selection artifact.
5. **Prompt/steer asymmetry in what is being compared.** The prompt condition changes the input; the steer condition changes hidden states *and* the prompt condition is absent (or is it the same base prompt? — the paper never states the steer condition's prompt). This is a first-order specification gap: **is steering applied on top of the neutral prompt, the best prompt, or a bare task prompt?** L162–L170 do not say. Without this, `d_i = steer_i − prompt_i` is uninterpretable.

### 3.5 Ecological validity
- **Severity: BLOCKER for CHI/CSCW, MAJOR for IUI.** No user, no interface task, no realistic query distribution, no session, benchmark items only, 64-token outputs. The paper's design implications concern console UIs; the evidence concerns GSM8K accuracy under residual-stream perturbation.

### 3.6 Construct validity
- "Deliberation" := GSM8K accuracy. Accuracy is an *outcome* of deliberation at best; under a short generation cap it is mostly arithmetic recall. **Severe.**
- "Skepticism" := false-premise rejection on TruthfulQA-derived items. TruthfulQA is a misconception benchmark, not a false-premise benchmark; the mapping is asserted, not validated. **Severe.**
- "Uncertainty" := 1 − Brier over a self-reported confidence token. Self-reported verbalized confidence in a 7B instruct model is a notoriously unreliable instrument; the paper acknowledges the decomposition problem (L148, L277) but still headlines the metric.
- "Facade ratio" (C1): a projection ratio with no validation against any independent criterion; the two-model measurement disagrees on 2/4 axes.
- The paper deserves partial credit for stating the construct bound explicitly (L148) — but stating a validity limit does not repair it, and the abstract still says "calibration."

### 3.7 Internal validity
- Reasonable within the harness (paired items, disjoint splits, audited pairing, byte-exact reproduction of cell 1). The threats are the confounds above, not sloppy execution.
- Unaddressed: no blinding of the outcome parser to condition; no inter-rater or human spot-check of parsed outcomes; the coherence gate's own thresholds (≤1.5×) are unvalidated.

### 3.8 External validity
- Two models, one family size band, two steering recipes, two benchmarks, one language, one prompt-authoring team, one layer per model. The paper says this (L273) and then writes an abstract and title that read much broader.

### 3.9 Threat register

| # | Threat | Severity | Reviewer criticism | Suggested fix |
|---|---|---|---|---|
| T1 | Confidence-format degradation drives the "calibration harm" | **BLOCKER** | "Your one robust finding may be a parser story." | Report the parsing rule; report % format-compliant per condition/cell; re-run the uncertainty analysis restricted to format-compliant generations; report both. |
| T2 | No manipulation check / positive control | **BLOCKER** | "You cannot distinguish 'no control' from 'no intervention.'" | Report per-item output-change rates and effect on a known-steerable target (e.g., refusal/sentiment) at the same α. |
| T3 | Power (MDE up to 0.279) | **BLOCKER** | "8/12 cells could not have detected anything." | Increase N (items are cheap relative to GPU time already spent); report power curves; restrict claims to cells with MDE < δ. |
| T4 | Generation cap / decoding params unreported | **BLOCKER (reporting)** | "You didn't tell me how you generated." | Report k, temperature, max_new_tokens, stop criteria, batch effects in the body. |
| T5 | Steer-condition prompt unspecified | **BLOCKER (reporting)** | "What exactly is d_i differencing?" | State the exact prompt used in the steer condition and justify it. |
| T6 | No user study for a design-implications paper | **BLOCKER for CHI/CSCW** | "This is an ML paper with an HCI abstract." | Run at minimum a designer/expert walkthrough (n=8–12) of the console contract; or retarget venue. |
| T7 | Ecological validity (benchmarks, not console use) | MAJOR | "Nothing here resembles console usage." | Add an interactive-task arm, or bound the claim to benchmark settings in the title. |
| T8 | Construct validity of all three axes | MAJOR | "Accuracy is not deliberation." | Validate axis outcomes against human ratings on a subsample; report agreement. |
| T9 | Asymmetric search budget (16 prompts vs 7 α) | MAJOR | "Your 'fairness control' is not fair." | Match effective budget; report sensitivity to prompt-budget size (best-of-4/8/16) and to α-grid density. |
| T10 | Layer chosen from C1, never swept in C2 | MAJOR | "F4 in your own taxonomy is an uncontrolled confound in your own study." | Layer sweep on DEV for at least one cell. |
| T11 | Multiplicity/directionality of the harm claim | MAJOR | "Harm was not the pre-registered hypothesis." | Label the harm claim post-hoc-directional; correct across 12 comparisons. |
| T12 | Asymmetric δ | MAJOR | "0.05 matters for wins but not losses?" | Apply δ symmetrically; three of four harms then become borderline. |
| T13 | Same-item-pool "robustness" | MAJOR | "Re-splitting is not replication." | Draw independent item pools; or rename to "split-stability." |
| T14 | Positive deliberation trend not analyzed | MAJOR | "You buried a 4/4 consistent positive." | Pre-specified or clearly-labelled pooled random-effects analysis across cells. |
| T15 | No verifiable pre-registration artifact | MAJOR | "Pre-registration is your main claim to rigor and I can't see it." | Anonymous OSF/AsPredicted link with timestamps. |
| T16 | Uncited documentation/guidelines lineage | MAJOR (positioning) | "This is a model card with new labels." | Cite and differentiate from model cards, FactSheets, datasheets, Amershi guidelines. |
| T17 | Console figure unevaluated and cropped | MINOR | "Why the crop?" | Full figure + design rationale + at least a walkthrough. |
| T18 | Appendix experiment adds risk, not value | MINOR | "Why is a `valid_for_paper=false` study in my PDF?" | Delete or move entirely to supplement. |
| T19 | C1 axis inconsistency across models | MINOR–MAJOR | "Your precondition measure doesn't replicate." | Either drop C1 or treat the disagreement as the finding. |
| T20 | Bootstrap method (percentile vs BCa) unstated at 98.33% with 40 clusters | MINOR | "Tail coverage?" | State method; report coverage simulation. |

---

## TASK 4 — Evidence vs claims

| # | Claim (location) | Supporting evidence | Adequate? | Reviewer concern |
|---|---|---|---|---|
| 1 | "latent steering showed no demonstrated superiority… on any adjudicated axis" (Abstract L37; L51; L209) | Table `tab:c2-delta-4cell`, 12/12 fail (E-0005/E-0006) | **Partially** | Literally true under the pass rule, but with MDE up to 0.279 it is near-tautological. Also unfalsifiable-by-design without a positive control (T2). |
| 2 | "uncertainty calibration is consistently harmed in all four cells" (Abstract; L224–227; Conclusion L290) | 4/4 negative CIs excluding 0 | **No** | (a) format-compliance confound acknowledged at L229 but unresolved (T1); (b) harm direction is post-hoc relative to the pre-registered superiority test; (c) δ not applied to harms — 3/4 harms are near δ; (d) 12-comparison multiplicity uncorrected. The paper's *only* robust finding rests on the metric most vulnerable to a parsing artifact. |
| 3 | "split-seed robust across five DEV/TEST split seeds" (Abstract; L217; L271; Conclusion) | E-0011 | **Partially** | Same item pool, seed 20260723 is artifact reuse, harness check self-referential (E-0011 MAJOR#2). Honest caveat present in the body, but "robust" in the *abstract* over-sells; a reader skimming the abstract is misled. |
| 4 | "fairness-controlled" adjudication (Abstract; L51; L146) | Design description only | **No** | No empirical demonstration of comparator adequacy: no prompt-budget sensitivity, no expert-prompt upper bound, no random-prompt lower bound. 16 vs 7 asymmetry (T9). |
| 5 | "bounded 16-candidate best-prompt baseline" is a realistic non-expert interface effort (L146) | Assertion | **No** | This is an *empirical claim about users* made without users. What do non-experts actually try? Unknown. This directly undermines the interface framing: the baseline that anchors the whole comparison is an unvalidated model of user behavior. |
| 6 | "deliberation/skepticism are underpowered non-detections, not equivalence" (L211–215) | TOST table | **Yes** | Correct and commendable — but it concedes that 8/12 cells carry no information, which the abstract does not make equally salient. |
| 7 | C1 facade pattern with cross-model support on deliberation/skepticism (Abstract; L204; Conclusion) | Table `tab:c1-twomodel` (E-0003, E-0008) | **No** | Both rows are `valid_for_paper=false` in the ledger; single run each; 2/4 axes flip; no null-model comparison shown numerically in the table (the random-null appears only in the figure prose, L138). "Cross-model support" on 2/4 axes from n=1 run per model is not support. Should not appear in the Abstract or Conclusion at all. |
| 8 | PSR-style arm "pre-empts the 'your method was too weak' objection" (L91, L259, Abstract) | E-0009 | **No** | E-0009 is single-model, single-seed, `valid_for_paper=false`, exploratory. The paper's own Abstract calls it "preliminary evidence" — but it is used rhetorically to close the field's strongest counter-argument (Heyman & Vandeputte). It cannot bear that weight. |
| 9 | Interface-evaluation contract (C3) as a contribution (Abstract; L70–74; §6 L231–252; Conclusion) | **None** — `claim-map.yaml`: `has_project_evidence_row: false`, `gate_result: FLAGGED` | **No** | The paper's fourth contribution has zero evidence of any kind: no user data, no designer data, no comparison to model cards/FactSheets, no evaluation of whether the five signals are comprehensible, sufficient, or actionable. The hedging (L70–74, L245–252) is thorough but hedging is not evidence. **For CHI/CSCW this alone is decisive.** |
| 10 | F1–F5 failure taxonomy (`tab:failure-taxonomy`) | Mixed: F1/F2 from C2; F3 "not triggered"; F4 "supported in scope"; F5 from the C1 focus overshoot | **No** | F3 is admittedly not observed. F4 has *no* layer-sweep evidence in the paper. F5 rests on a single exploratory C1 number (2.844) whose model-pair partner disagrees. Three of five taxonomy rows are asserted, and the taxonomy is a headline artifact (Table in §6). |
| 11 | "working console instantiation" (L74, Fig. `fig:console`) | Cropped screenshot | **No** | No architecture, no implementation detail, no usage, no evaluation, no availability. Not a systems contribution. |
| 12 | "independently audited" (Abstract, L185) | Hostile audit sessions in the ledgers | **Unverifiable at review** | Internal self-organized audits are not external validation; no auditor identity, protocol, or report is available to reviewers. Presenting it as a credibility feature in the abstract without a checkable artifact is a rhetorical move a reviewer will discount to zero. |
| 13 | Appendix C4 social-inference null (L294+) | E-0010, `valid_for_paper=false`, LLM-judge only, human-α pending | **No** | Correctly labeled, but its presence implies a breadth of evidence the paper does not have. |
| 14 | "Mechanism remains open" (L229, L275) | E-0007 pre-registered null | **Yes** | Genuinely well handled. |

**Places where claims most exceed evidence (ranked):** #9 (C3 contract), #2 (calibration harm as *calibration*), #7 (C1 in abstract/conclusion), #4/#5 (fairness + realistic-user-effort claims), #8 (PSR arm as objection-closer), #10 (taxonomy), #3 (word "robust" in abstract).

---

## TASK 5 — CHI/CSCW contribution test

Using Wobbrock & Kientz's contribution taxonomy:

| Type | Present? | Assessment |
|---|---|---|
| **Empirical** | Partially | Real, pre-registered, audited — but on *models*, not people. CHI/CSCW empirical contributions are overwhelmingly about human behavior, human-AI interaction outcomes, or socio-technical practice. A model benchmark is empirical for ICML/EMNLP; at CHI it is *formative material* for an empirical contribution that was never run. Strength: **moderate but venue-misaligned.** |
| **Methodological** | Partially | The frozen adjudicator (DEV-only symmetric selection, paired item-cluster bootstrap, coherence gate, pass rule) is a reusable evaluation instrument, and it is the paper's best claim to a contribution. Weakened by: comparator not validated (T9), no positive control (T2), instrument never used by anyone but the authors, and no demonstration that it discriminates (it has only ever returned "fail"). **An instrument that has never returned a positive verdict has not been shown to be sensitive.** Strength: **moderate.** |
| **Theoretical** | Weak/absent | No new theory. The theoretical scaffolding (non-surjectivity) is imported from a workshop paper and explicitly not tested (C2a: "background citation only" in `claim-map.yaml`). Strength: **weak.** |
| **Design** | Asserted only | The five-signal contract, F1–F5 taxonomy, and console are design *proposals*. No design process reported (no formative study, no ideation, no alternatives considered, no rationale trace), no evaluation, no comparison to existing documentation regimes. This is "design implications drawn from data" — the exact practice CHI has been criticizing for fifteen years — with the aggravating factor that the data are not about humans. Strength: **weak; possibly negative** (an unevaluated prescription can mislead). |
| **Systems** | Absent | One cropped screenshot; no architecture, no novel technique, no availability, no performance/usage account. Strength: **absent.** |
| **Dataset/Artifact** | Partially | Frozen JSON + manifests + generation scripts are a real artifact contribution, but no accessible link at review time, and the per-item confidence/correctness data (needed to check the headline) are explicitly not committed (L277). Strength: **weak-moderate, unverifiable.** |

**Strongest category:** *methodological* (the frozen adjudication protocol), followed by *empirical* (the negative result itself).

**Is it strong enough for CHI/CSCW?** **No.** The strongest contribution is an evaluation protocol for model interventions — a contribution that belongs at ICML/NeurIPS/EMNLP or, at a stretch, IUI. The HCI-facing contribution (C3) is the weakest part of the paper by the authors' own gate. CHI and CSCW reviewers will apply a simple test — *what do we now know about people, practice, or interaction that we did not know before?* — and the answer is **nothing**. CSCW is a worse fit still: there is no collaboration, no social context, no group, no organization, no practice study.

**Is it strong enough for IUI?** Closer. IUI accepts model-side evaluations with interface implications more readily. But IUI still expects the interface claim to be substantiated at least by a system + walkthrough or a small study, and IUI reviewers are ML-literate enough to press hard on power, positive controls, and the format confound.

---

## TASK 6 — Three simulated reviewers

### Reviewer A — constructive but critical (expertise: human-AI interaction, trust calibration)
**Strengths**
- Asks a genuinely important question for the current feature-steering-UI moment.
- Exceptional epistemic hygiene: pre-registration, frozen pass rule, explicit failed-superiority ≠ equivalence (L211), pre-registered mechanism null reported as a null (L229), refusal to impute Brier decomposition (L277). I would like more CHI papers to be written this way.
- The F1–F5 taxonomy and the READ/TRANSFER/evidence-tier vocabulary are usable and would be a nice addition to the community's vocabulary *if grounded*.
- The UI-decision vignette (L244) is the most CHI-legible passage in the paper and shows the authors know what the interface argument should look like.

**Weaknesses**
- The paper is an ML evaluation paper wearing an HCI jacket. Sections 3–5 are ML; sections 1, 6, 8 are HCI; the join is asserted.
- Every design implication is a hypothesis. "A console should surface READ status" presumes users can interpret READ status — a claim about human cognition with zero support. Prior work (Buçinca, Bansal, Zhang — all uncited) suggests that adding confidence/quality signals frequently *fails* to improve calibrated reliance and can backfire. The contract could plausibly harm users; the paper cannot tell.
- The abstract oversells three things relative to the body: "split-seed robust," "calibration harmed," "cross-model representational support."
- C1 should not be in the abstract or conclusion at all given `valid_for_paper=false`.

**Questions**
1. In the steer condition, what prompt was in the context window — the neutral task prompt, or the DEV-selected best prompt? The definition of `d_i` (Eq. `eq:paired-diff`) is unclear without this.
2. What fraction of steered generations emitted a parseable confidence token vs prompt generations, per cell? What value is imputed on parse failure?
3. Why are the deliberation deltas positive in 4/4 cells, and what does a pooled estimate look like?
4. Has any human — designer, developer, or end user — ever looked at the console in Fig. 3 and reacted? Even n=5 informal feedback would change my read of §6.
5. How do the five contract signals differ from a per-axis model card / FactSheet row?

---

### Reviewer B — methodology skeptic (expertise: experimental design, statistics, LLM evaluation)
**Strengths**
- Paired design, disjoint DEV/TEST, cluster bootstrap, Bonferroni, meaningful margin, and a pre-registered verdict rule. The bones are right.
- The TOST table is the most useful table in the paper and the authors deserve credit for publishing a table that weakens their own narrative.
- Byte-for-byte reproduction of cell 1 across two arms (E-0005 → E-0006) is a real reproducibility check.

**Weaknesses**
- **I cannot evaluate the central experiment from the paper.** k, temperature, max generation length, the steer-condition prompt, the confidence parser, and the coherence-ratio values are all absent from the body. This alone is a reject at a venue with an archival record.
- **No positive control.** Every conclusion in the paper is of the form "we did not observe X." Without demonstrating that the apparatus can observe *any* effect it should observe, the null is uninformative. For a paper whose entire thesis is a null, this is disqualifying.
- **Power.** The authors' own MDE column runs to 0.279 on a [0,1] outcome. Eight of twelve cells are informationally empty. A "generalized negative across the grid" built from eight empty cells and four cells whose only signal is on a confound-prone metric is not a generalized negative.
- **The harm claim is directionally post-hoc and multiplicity-uncorrected across cells**, and δ is applied asymmetrically. Apply δ = 0.05 symmetrically and CAA×Llama (−0.072, TOST [−0.095,−0.047]) and ITI×Llama (−0.084) become "harm below or near the pre-registered practical margin." Only CAA×Qwen (−0.228) is unambiguously large — and that is the single cell with the widest CI and the largest MDE (0.196), i.e., the noisiest cell.
- **"Fairness-controlled" is not established.** 16 prompt candidates vs 7 α values on one fixed layer. And the α grid's top values (16, 24) were apparently rarely selected (selected α ∈ {2,4,6,8,12}) — was the DEV objective preferring near-inert interventions?
- **Selection on 20 DEV items.** Best-of-16 on 20 binary items is a coin-flip tournament. The paper should report the DEV→TEST shrinkage for the selected prompt and the selected α.
- **"Split-seed robust" is re-splitting the same 60–80 items five times.** That estimates split variance, nothing more. The ledger says this plainly (E-0011: "NOT independent item draws"); the abstract does not.
- The bootstrap at 98.33% with 40 clusters: percentile or BCa? Coverage at that tail with 40 clusters is not automatic.

**Questions**
1. Provide the per-cell format-compliance rate and re-run the uncertainty analysis on compliant subsets only.
2. Provide a random-direction steering control at matched α and a no-intervention control.
3. What are `max_new_tokens`, k, and temperature, and how does GSM8K accuracy behave at that cap without any intervention?
4. Report DEV and TEST outcomes for the selected prompt and selected α side by side (shrinkage check).
5. Report a pooled random-effects estimate per axis across the four cells.
6. Provide the pre-registration artifact with a verifiable timestamp.

---

### Reviewer C — novelty skeptic (expertise: interpretability, activation steering, positioning)
**Strengths**
- Correctly identifies Heyman & Vandeputte as the boundary condition rather than burying it (L91, L259). Honest.
- The nearest-neighbor table (`tab:novelty-neighbors`) is a good practice.

**Weaknesses**
- **The finding is what the field already expects.** Fan et al. (steerability is conditional), Korznikov et al. (steering damages behavior), Sprejer et al. (feature steering trades off capability), and a broad practitioner consensus that CAA at fixed α on a fixed layer is fragile — all point the same way. Confirming an expectation with 12 underpowered cells on 7–8B models is not a top-tier contribution.
- **The claim is scoped down to the point of near-triviality.** By the time the authors have excluded trained steering, optimized steering, multi-layer schedules, RepE variants, larger models, other tasks, other axes, and other layers (L273), what remains is: "default-recipe CAA/ITI at DEV-picked α on one layer of two 7–8B models did not beat a 16-prompt baseline on two benchmarks." Nobody would have bet otherwise.
- **The PSR-style rebuttal arm is exploratory-grade** (single model, single seed, `valid_for_paper=false`), yet is deployed against the strongest counter-argument in both the abstract and discussion. That is exactly the kind of asymmetric evidence-weighting the paper elsewhere polices in itself.
- **The HCI framing does not create novelty; it relocates it.** "Show provenance and evidence tiers in the UI" is model cards (Mitchell et al.), FactSheets (Arnold et al.), datasheets (Gebru et al.), and Amershi et al.'s guidelines G11 ("make clear why the system did what it did") — none cited. The contract is a repackaging with new labels.
- **C1 does not replicate compositionally** (uncertainty and focus swap; Table `tab:c1-twomodel`), which is a *negative* result about the paper's own measurement instrument, presented as "aggregate support."
- **Title asserts more than the paper proves.** "Legible Need Not Be Controllable" is a general modal claim; the subtitle rescues it, but titles travel and subtitles do not.

**Questions**
1. What would this paper have concluded if a cell *had* passed? Has the adjudicator ever produced a positive verdict on anything?
2. How does the contract differ, concretely and row-by-row, from a model card with per-axis rows?
3. Why should the community update its beliefs given Sprejer, Fan, and Korznikov?
4. Why 7–8B models when the consoles you are designing for are built on frontier models with entirely different representational geometry?

---

## TASK 7 — Meta-review (Associate Chair)

### Summary of the discussion
All three reviewers agree that this is an *unusually honest* paper with real methodological discipline: pre-registration, a frozen pass rule, published nulls, an explicitly reported post-hoc TOST that weakens the authors' own framing, and machine-generated tables. Nobody suspects misconduct or number-massaging; if anything the authors are more conservative in the body than in the abstract.

The disagreement is only about *whether honesty about a thin result is enough*. R1 sees a valuable reality check with a misaligned venue and an ungrounded design section. R2 concludes the central experiment cannot support any conclusion, positive or negative, without a positive control, adequate power, and disclosure of decoding/parsing details. R3 concludes that even a perfectly executed version of this study would be confirming what the interpretability community already believes, and that the HCI "contract" is prior art in new clothing.

The three positions converge on a single structural diagnosis: **the paper's evidence is model-side, its claimed contribution is interface-side, and the bridge between them is entirely rhetorical.** The authors know this — `claim-map.yaml` marks C3 with `has_project_evidence_row: false` and `gate_result: FLAGGED` — and they hedge extensively (L70–74, L245–252). But at a < 25% venue, "we hedged" is not an argument for acceptance; it is an argument that the contribution was correctly identified as unsupported.

A secondary concern surfaced by R2 is potentially fatal in its own right and is not resolved by hedging: the paper's single robust empirical finding — calibration harm — has an acknowledged alternative explanation (steered outputs dropping the required confidence format, L229) that the paper does not test, and the parsing rule that would settle it is not reported. If that confound explains the effect, the paper has no robust finding at all: eight cells are underpowered non-detections and four are a format-degradation artifact.

### Likely outcome
- **CHI: reject.** Contribution type mismatch (no human/practice knowledge), design implications without design evidence, ecological validity ~0.
- **CSCW: reject** (worse fit; no social/collaborative dimension whatsoever).
- **IUI: borderline reject → weak reject.** Plausible R2R/major-revision territory if the format confound is resolved and the console gains any evaluation; as submitted, below the line.

### Major concerns (must-fix, in order)
1. **M1 (BLOCKER).** Resolve the confidence-format confound on the uncertainty axis. Report format-compliance rates per condition/cell and the imputation rule; re-run restricted to compliant generations. Until then the calibration claim cannot stand in the abstract, title, or conclusion.
2. **M2 (BLOCKER).** Add a positive control / manipulation check demonstrating the steering apparatus produces detectable effects at the tested α on a known-steerable behavior, plus per-item change rates for the adjudicated cells.
3. **M3 (BLOCKER).** Report the full generation protocol in the body: k, temperature, `max_new_tokens`, stop criteria, item provenance, the steer-condition prompt, the parser, coherence-ratio values.
4. **M4 (BLOCKER for CHI/CSCW; MAJOR for IUI).** Ground the interface contribution in *some* human data — even a 10–14 participant designer/practitioner walkthrough of the contract cards, or an expert heuristic evaluation. Otherwise demote §6 from a contribution to a short "implications for future interface evaluation" subsection and remove C3 from the abstract's contribution list.
5. **M5 (MAJOR).** Fix the statistical asymmetries: apply δ symmetrically to harms, correct multiplicity across the 12 grid comparisons, label the harm direction as post-hoc, report a pooled per-axis estimate (including the 4/4 positive deliberation trend), and state the bootstrap variant.
6. **M6 (MAJOR).** Rewrite the abstract to match the body: remove "robust" for the same-pool split-seed arm, remove C1 (`valid_for_paper=false`) entirely, and describe 8/12 cells as uninformative rather than as part of a "generalized" negative.
7. **M7 (MAJOR).** Fix positioning: cite and differentiate from model cards, FactSheets, datasheets, Amershi et al.'s guidelines, and the trust-calibration literature (Lee & See; Bansal; Buçinca; Zhang/Liao). Without this, the contract reads as unaware of its own genre.
8. **M8 (MAJOR).** Provide a verifiable anonymized artifact + pre-registration link. A pre-registration claim that reviewers cannot check earns zero credit.

### What would make this acceptable
At **IUI**: M1 + M2 + M3 + M5 + M6 + M8, with §6 demoted, would likely put the paper at borderline-accept — a clean, well-scoped, well-audited negative result with a modest interface framing.
At **CHI/CSCW**: the above **plus M4 executed as a real study** (either a designer-facing evaluation of the contract, or an end-user study of whether TRANSFER/calibration-harm signals improve calibrated reliance). That is a different paper and roughly one full cycle of work.

---

## TASK 8 — Final scores

Scale: 1 = very poor, 2 = poor, 3 = acceptable, 4 = good, 5 = excellent.

| Dimension | Score | Justification |
|---|---|---|
| **Originality** | **2** | Confirms an expectation the interpretability community already holds (Fan, Korznikov, Sprejer); the HCI contract has substantial uncited prior art (model cards, FactSheets, Amershi guidelines). Protocol rigor is not originality. |
| **Significance** | **2** | If the format confound holds, significance approaches zero. If it does not, the finding is a bounded caution about default-recipe steering on 7–8B models — useful, narrow, and unlikely to change practice at frontier scale. |
| **Methodological rigor** | **3** | Split: pre-registration, freezing, pairing, audits, and honest nulls are 4-level work; missing positive control, catastrophic power, unreported decoding/parsing, and asymmetric δ are 2-level failures. Net 3. |
| **Technical quality** | **3** | Execution appears careful and internally consistent (byte-exact cell reproduction). Design gaps, not execution errors, are the problem. |
| **Clarity** | **3** | Well organized and scrupulously scoped in prose, but heavy hedging density hurts readability, key protocol details are missing, and the abstract does not match the body's own caveats. |
| **Reproducibility** | **3** | Manifests, generating scripts, and frozen JSON are genuinely good practice; but no accessible artifact/pre-registration link at review time, GPU-side transcripts and per-item confidence/correctness pairs not committed (L277), and the body omits parameters needed to re-run. |
| **Overall recommendation** | **2 — Reject** (CHI/CSCW); **2.5 — Weak reject / borderline** (IUI) | Structural mismatch between evidence and claimed contribution, plus an unresolved confound on the only robust finding. |
| **Reviewer confidence** | **4 / 5** | High expertise in activation steering, LLM evaluation methodology, and HCI evaluation; I read the full paper, all tables, the claim map, and the evidence ledger. Confidence is not 5 only because the missing protocol details (parser, decoding params, steer-condition prompt) prevent me from fully adjudicating the calibration-harm confound from the submitted materials. |

---

## TASK 9 — Acceptance probability

| Venue | Probability | Reasoning |
|---|---|---|
| **CHI** | **4–7%** | CHI's dominant contribution types are empirical (human), design, and systems. This paper offers none of the three with evidence. The "design implications from non-human data" pattern has been explicitly criticized in the CHI community for over a decade, and here the data are not even about people. Add the absent HCI positioning (no Amershi, no Buçinca, no Lee & See, no model cards) and at least one AC will read the contract as unaware prior art. The pre-registration rigor buys goodwill but is not what CHI trades in. A committed champion could push it to borderline, but 2R+ would need to be persuaded that a benchmark null licenses interface prescriptions. |
| **CSCW** | **2–4%** | Strictly worse fit than CHI. CSCW requires a social, collaborative, organizational, or practice dimension. There is none — no collaboration, no group, no practice, no field site, no situated use. Desk-reject risk is non-trivial. |
| **IUI (actual target)** | **15–22%** | IUI regularly accepts model-side evaluations with intelligent-interface implications, is more tolerant of "system + implications" without a full user study, and has an audience that will appreciate the pre-registered negative. Against acceptance: IUI reviewers are ML-competent and will press hard on (a) the missing positive control, (b) MDE up to 0.279, (c) the format-vs-calibration confound, (d) two 7–8B models only, (e) 64-token generations if disclosed, and (f) the unevaluated console. IUI is also increasingly competitive (~25%) and has a strong recent stream of steering/interpretability-interface work. Realistically: weak-reject with one reviewer arguing for R2R. If M1/M2/M3 are fixed before submission, this rises to **~35%**. |

**Why the ceiling is where it is:** the paper's single most defensible asset — a rigorously frozen negative — is undermined by three independent facts: eight of twelve cells cannot detect meaningful effects, the four informative cells depend on a metric with an acknowledged and untested alternative explanation, and no evidence exists that the apparatus can detect an effect when one is present. A reviewer who notices any *one* of these can write a complete rejection.

---

## TASK 10 — Two-week revision roadmap (ranked by impact per unit effort)

| # | Fix | Effort | Impact | Notes |
|---|---|---|---|---|
| **1** | **Resolve the calibration-vs-format confound.** Report per-cell confidence-format compliance rates for prompt vs steer; state the parser's imputation rule explicitly; re-run the uncertainty analysis on format-compliant items only and report both versions. | 2–3 days (analysis on existing transcripts; no new GPU if transcripts are retrievable) | **Highest.** Either rescues the paper's only robust finding or converts it into a still-publishable and arguably more interesting finding ("naive steering breaks instruction-format adherence, which is what destroys the calibration signal"). Both outcomes beat the status quo. |
| **2** | **Add a positive control / manipulation check.** Report per-item output-change rates per cell/axis, plus one known-steerable target (e.g., refusal rate or sentiment) at the same layers/α showing the apparatus produces a detectable effect. | 2–3 days incl. a short GPU run | **Very high.** Converts "we detected nothing" into "the apparatus detects effects; it did not detect this one." Without it, R2's objection is fatal and unanswerable. |
| **3** | **Full protocol disclosure in the body.** k, temperature, `max_new_tokens`, stop criteria, item pool provenance and slicing, the exact steer-condition prompt, the parser spec, coherence-ratio values, bootstrap variant. If `max_new_tokens=64`, address head-on what that implies for the deliberation axis (and consider dropping or re-running that axis). | 1 day writing (+ optional re-run) | **Very high, near-zero cost.** Removes an easy structural reject. |
| **4** | **Rewrite the abstract, title framing, and contribution list to match the body.** Remove C1 from the abstract/conclusion; replace "split-seed robust" with "stable across five DEV/TEST re-splits of the same item pool"; state up front that 8/12 cells are underpowered; demote C3 from "contribution" to "implication." | 1 day | **High, zero cost.** Most reviewers form their verdict from the abstract; the current abstract promises what the body then retracts. |
| **5** | **Fix statistical asymmetries.** Apply δ symmetrically to harms; correct multiplicity across the 12 grid comparisons; explicitly label the harm direction as post-hoc; report a pooled per-axis random-effects estimate (and address the 4/4 positive deliberation trend head-on). | 1–2 days | **High.** Pre-empts the sharpest R2 attacks and demonstrates that the authors' honesty extends to results that cut against them. |
| **6** | **Add HCI positioning and differentiation.** One paragraph + 8–12 citations: model cards, FactSheets, datasheets, Amershi et al.'s guidelines, Lee & See, Bansal, Buçinca, Zhang/Liao. Explicitly state what the contract adds beyond a per-axis model card. | 0.5 day | **High, near-zero cost.** Neutralizes R3's cleanest reject argument. |
| **7** | **Ground §6 with the cheapest possible human data.** A 60-minute expert walkthrough with 8–12 designers/ML-practitioners rating comprehensibility and actionability of the five contract signals, or a structured heuristic evaluation with 3–5 evaluators. Report it as formative, not confirmatory. | 4–6 days incl. recruiting; **owner/ethics-gated — may be infeasible in 2 weeks** | **High if feasible.** This is the only fix that moves CHI/CSCW probability at all. If ethics gating blocks it, do #8 instead. |
| **8** | **If #7 is blocked: restructure the paper as a methods/negative-result contribution.** Demote §6 to a one-page "implications for evaluating latent-control interfaces," delete the console figure or move it to supplement, remove "contract" from the title and contribution list, and lean the framing entirely on the frozen adjudicator as a reusable instrument. | 1–2 days | **High for IUI.** Aligning claims to evidence is worth more than an extra experiment when the mismatch is the primary objection. |
| **9** | **Publish a verifiable artifact + pre-registration.** Anonymized OSF/AsPredicted link with timestamps, anonymized repo with frozen JSON, manifests, scripts, and — critically — the per-item confidence/correctness pairs. | 1 day | **Moderate–high.** Pre-registration is the paper's headline rigor claim; unverifiable, it earns nothing. Also raises the Reproducibility score by a full point. |
| **10** | **Delete or fully relegate the appendix social-inference study** (`valid_for_paper=false`, LLM-judge-only, human-α pending) and trim the hedging density by ~30%. Add a comparator-adequacy sensitivity check (best-of-4 / best-of-8 / best-of-16 prompt budgets, and a random-prompt lower bound) if any DEV data permit it without new GPU. | 1–2 days | **Moderate.** Removes free targets, improves clarity, and directly answers "your fairness control is not fair." |

**If only three things can be done:** #1, #2, #3. Those three convert an unanswerable methodological objection into an answerable one and are worth more than any amount of additional framing.

---

## Bottom line

A conscientious, well-audited, honestly reported paper about a thin and expected negative result, whose claimed HCI contribution has — by the authors' own gate record — no evidence of any kind, and whose single robust empirical finding rests on a metric with an acknowledged, untested alternative explanation. **Reject at CHI/CSCW; weak reject at IUI**, with a realistic path to IUI acceptance in one cycle if the format confound, the missing positive control, and the protocol under-reporting are fixed and the interface claim is either grounded or demoted.
