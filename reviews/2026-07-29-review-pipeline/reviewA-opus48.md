# Peer Review — Reviewer A (Senior, ACM CHI/CSCW/IUI)

**Paper:** *Legible Need Not Be Controllable: A Frozen Reality Check for Prompt-vs-Latent Behavioral Control in LLMs*

**Reviewer stance:** Senior HCI/Human-AI Interaction reviewer. Top-tier venue, sub-25% acceptance. Maximally critical. Review based solely on the submitted PDF/source (main.tex, `tables/*.tex`, `figures/concept.tex`, figure captions, references.bib).

---

## TASK 1 — High-Level Assessment

**1) One-sentence summary.**
Using a frozen, pre-registered adjudication on two 7–8B instruction models, the paper reports a scoped *negative* result — naive CAA/ITI latent steering does not beat a bounded best-prompt ceiling on three metacognitive axes and actively harms uncertainty calibration — and argues (without any human data) that "cognitive consoles" should instrument the legibility/controllability boundary rather than expose legible latent directions as control sliders.

**2) Claimed contributions (as stated, Sec. 1 enumerated list).**
- (C1) An *exploratory* two-model representational-facade measurement.
- (C2) A frozen, pre-registered, fairness-controlled, audited prompt-vs-latent behavioral adjudication.
- (C3) A "generalized scoped negative with calibration harm" across the CAA/ITI × Qwen/Llama grid.
- (C4) Interface-evaluation implications for cognitive consoles (a five-signal UI "contract"), explicitly framed as "a design implication from model evidence, not a user-study claim."

**3) Actual contributions (my opinion).**
- A carefully pre-registered, multiplicity-controlled *null result* on two off-the-shelf steering methods and two mid-size models — genuine and honestly reported, but empirically thin and largely **underpowered** (TEST N = 40–53 per axis).
- One mildly interesting sub-finding: uncertainty-axis calibration *harm* whose CIs exclude zero in all four cells (Table `c2-delta-4cell`, Fig. `c2-calibration-harm`) — though its construct validity is questionable (see Task 3).
- A rhetorical/methodological framing ("frozen adjudicator", "facade ratio", "five-signal UI contract"). This is repackaging, not new empirical knowledge.
- **No validated HCI contribution.** The console is a static, cropped rendering (Fig. `fig:console`, `trim=0 390 0 35,clip`); there is no deployment, no task, no user, no usability or trust-calibration data.

**4) Main strengths.**
- Exemplary open-science hygiene: pre-registration, DEV/TEST separation, Bonferroni correction, coherence gate, item-cluster bootstrap, hostile audits, machine-generated tables/figures from frozen JSON (Sec. 3.3–3.4). This is more disciplined than most CHI submissions.
- Intellectual honesty about scope: repeated, explicit refusal to over-claim (Sec. 1, 5). The negative is not dressed as an impossibility theorem.
- A real and legible conceptual point: representational legibility ≠ behavioral controllability.

**5) Main weaknesses.**
- **Venue mismatch.** This is an ML-interpretability paper with an HCI veneer. For CHI/CSCW there is no human in the loop anywhere — no study, no participants, no interface evaluation. The "design implication" is speculation about how a hypothetical console *should* behave.
- **A null result carried by low power.** For deliberation/skepticism the CIs are wide and consistent with meaningful effects (e.g., CAA×Qwen skepticism Δ = −0.080 [−0.225, +0.045]; Llama skepticism [−0.190, +0.200]). "Does not beat the ceiling" conflates *no effect* with *cannot detect an effect*.
- **Novelty is squeezed** between Mishra (theory), Heyman (steering *can* mimic prompting), and the concurrent Sprejer et al. (same degradation pattern). The residual novelty is the framing, not the finding.
- **Construct validity of "calibration harm."** Steering *toward an uncertainty pole* and then scoring with 1−Brier may just measure "the axis does what it says," not a control pathology.
- Bloated, hedged, jargon-dense prose; a large exploratory "social-inference" dump (Sec. 6.1) explicitly labeled non-contribution — pure padding.

---

## TASK 2 — Novelty Assessment

**Is the problem new?** The *conceptual* claim (legible ≠ controllable) is not new; it is the natural corollary of non-surjectivity (Mishra et al. `mishra2026nonsurj`) and is already voiced in transparency/actionability work (Liao & Vaughan `liao2024transparency`; Tankelevitch et al. `tankelevitch2024metacog`). The *specific empirical test* (frozen prompt-vs-naive-latent adjudication on metacognitive axes) is a modest new configuration, not a new problem.

**Incremental?** Yes — substantially. The methods (CAA, ITI) are off the shelf; the models are standard; the framing is the novelty.

**Which prior work makes this vulnerable?**
- **Sprejer et al. `sprejer2026mindgap` (concurrent).** By the authors' own admission (Sec. 2.2, Table `tab:novelty-neighbors`), this reports the *same* capability/behavior degradation-vs-prompting pattern. The authors distinguish it on machinery (SAE vs CAA/ITI), task (MMLU vs metacognitive), and "registration structure." A skeptic will call these *differences of instrumentation, not of insight*. The headline scientific claim substantially pre-exists.
- **Heyman & Vandeputte `heyman2026steer`.** Directly undercuts generality: trained steering *mimics* prompting. The paper concedes this repeatedly and retreats to "naive/off-the-shelf" steering. That retreat shrinks the contribution to "one specific weak method fails to beat prompts," which is close to expected.
- **Mishra et al. `mishra2026nonsurj`.** Supplies the entire theoretical premise; the paper is an empirical footnote to it at the behavioral level.
- **Huang & Lim `huang2025steering`; Riche et al. `riche2025aiinstr`.** Own the "interface for steering / prompt-as-instrument" design space already; this paper adds no interface *artifact* beyond a static mock.

**What a skeptical reviewer would say:** "This is a negative replication of a concurrent preprint's finding, on a weaker steering family the authors themselves say can be beaten by training, with no users, submitted to a human-computer interaction venue. The 'frozen adjudicator' and 'facade ratio' are re-descriptions of standard held-out evaluation and cosine-projection ratios."

**Novelty gaps / positioning weaknesses / inflation.**
- *Inflation:* C1 is called "cross-model representational support"/"replication" but is **n=1 run per model** and *axis-heterogeneous* — uncertainty and focus flip between models (Table `c1-twomodel`; Sec. 4.1). Two single runs that disagree on half the axes is not replication.
- *Inflation:* "Generalized scoped negative" (C3) — "generalized" across a 2×2 grid of 12 comparisons with N≤53 and no cross-cell multiplicity control.
- *Positioning:* The paper leans on the HCI framing to claim novelty, but the HCI half is unvalidated.

**Classification: C — mostly incremental** (borderline C/D given the concurrent Sprejer overlap and the "naive steering" retreat).

---

## TASK 3 — Methodology Audit

Note: there is **no user study**. I audit (A) the C1 facade measurement, (B) the C2 frozen adjudication + robustness/seed arms, and (C) the exploratory arms.

### A. C1 facade measurement (Sec. 3.1, 4.1; Table `c1-twomodel`; Fig. `c1-ratio-ci`)
- **Design:** projection ratio r_a = prompt_reach / pole_reach (Eq. `facade-ratio`). "Facade? yes/no" appears to be thresholded at r<1, but no formal decision rule or hypothesis test is stated. Focus on Qwen = 2.844 ("overshoot/no facade") while r≈1.0 on Llama uncertainty is "no." The yes/no labels look post-hoc.
- **Sample size / replication:** single run per model; the authors admit each model contributes one exploratory run (Sec. 5). No seeds, no variance across runs — the reported CIs are within-run bootstrap intervals, not run-to-run stability.
- **Construct validity:** projection onto a mean-difference direction conflates magnitude with meaning; a small ratio may reflect scale/norm choices, layer choice, or prompt-embedding placement rather than a genuine "facade."
- **Threats:**
  | Threat | Severity | Likely reviewer criticism | Suggested fix |
  |---|---|---|---|
  | n=1 per model, called "replication" | High | "Two disagreeing single runs ≠ cross-model support" | Multiple seeds/prompt sets per model; report run-to-run CI |
  | Arbitrary facade threshold | High | "yes/no labels are unprincipled" | Pre-register a decision rule + null-band; test against random-direction null formally |
  | Layer cherry-picking ("chosen non-degenerate layer") | Med-High | "Layer selection is a researcher DoF" | Report full layer sweep; show robustness |
  | Ratio metric construct validity | Med | "Projection ratio ≠ legibility" | Triangulate with probe accuracy / behavioral read |

### B. C2 frozen adjudication + robustness + multi-seed (Sec. 3.2–3.3, 4.2–4.3; Table `c2-delta-4cell`)
- **Design (strong on paper):** DEV-selected prompt and α; disjoint TEST; paired item-cluster bootstrap (B≥10000); Bonferroni CI at 0.98333; pass rule Eq. `axis-pass` (CI excludes 0 ∧ mean≥δ=0.05 ∧ coherence≤1.5). This is commendable HARKing resistance.
- **Statistical validity / power — the core problem.** TEST N = 40 (deliberation/skepticism) or 53 (uncertainty), with a 0.98333 CI. This is **badly underpowered** to *support* a null. Evidence: skepticism CIs are enormous (CAA×Qwen [−0.225,+0.045]; Llama [−0.190,+0.200]; ITI×Qwen [−0.270,+0.060]). A δ=0.05 effect is nowhere near excluded. The paper interprets "fails to pass" as "no behavioral control," but for most cells it is "we cannot tell." **No power analysis, no equivalence test (e.g., TOST), no minimum detectable effect** is reported. A frozen *null* without a power/equivalence argument is not evidence of absence.
- **Multiplicity:** Bonferroni is applied across 3 axes *within a cell* only. The "generalized" claim aggregates 4 cells × 3 axes = 12 adjudications plus a 5-seed arm; there is **no correction across cells or seeds**, yet the negative is framed as strengthened by the grid. You cannot both (a) treat each cell as a family of 3 for correction and (b) claim grid-wide generalization without grid-wide error control.
- **Multi-seed "replication" is not independent (Sec. 4.2, 5).** The authors concede all five seeds share the same first-N deterministic GSM8K/TruthfulQA slice; only DEV/TEST membership varies. This is re-splitting one small dataset, not replication. It inflates the appearance of robustness.
- **δ=0.05 across heterogeneous outcomes.** The same margin is applied to accuracy (deliberation), false-premise rejection rate (skepticism), and 1−Brier (uncertainty) — see Table `axis-outcomes`. A 0.05 margin is not comparably "meaningful" across these three scales; this is unjustified.
- **Fairness of the comparator is asserted, not shown.** The "bounded best-prompt ceiling" is central, but the prompt search space, budget, and the α grid are pushed to a supplementary manifest (`c2-delta-4cell.yaml`) not in the paper. A reviewer cannot judge whether the prompt channel was strong or the steering fairly tuned. The whole result hinges on this and it is unauditable from the submission.
- **Ecological / external validity:** GSM8K + TruthfulQA, first-N deterministic slice (non-random → order/selection bias), 7–8B models only, single-turn, no product prompts, no real tasks or users. Generalization to deployed "cognitive consoles" is unsupported.
- **Threats table:**
  | Threat | Severity | Reviewer criticism | Fix |
  |---|---|---|---|
  | Underpowered null (N≤53, wide CIs) | **Critical** | "Absence of evidence ≠ evidence of absence" | Power/MDE analysis; TOST equivalence bounds; larger N |
  | No cross-cell/seed multiplicity control | High | "Grid-wide claim without grid-wide error control" | Correct across all 12+ tests, or reframe per-cell |
  | Non-independent seed 'replication' | High | "Re-splitting one slice is not robustness" | Independent item draws / fresh datasets |
  | Comparator fairness unauditable in paper | High | "Can't judge if prompt or steering was tuned fairly" | Put prompt/α protocol in main text |
  | δ=0.05 across 3 metrics | Med | "Margin not comparable across scales" | Per-metric justified margins |
  | Deterministic first-N slice | Med | "Selection/order bias" | Randomized sampling with seeds |

### C. Exploratory arms (PSR-style, social-inference, breadth/focus; Sec. 2.2, 6.1)
- PSR-style latent-recovery arm: single-model, single-seed (Sec. 5); the audit caveat that "the optimizer's internal search objective uses its own alpha during DEV search" (Sec. 6, end) is a genuine comparability wrinkle the authors flag but do not resolve — the "too weak method" objection is only partly pre-empted.
- Social-inference probe (Sec. 6.1): single-model, single-seed, LLM-judge-only, N=54, human calibration pending; reports nulls with M2/M3 "not implemented." This is exploratory scaffolding, not evidence, and consumes a page.
- Breadth/focus probe: N=12, "deterministic echo" re-run (not replication), classifier self-judge artifact fixed post hoc, a "reasoning-category dead-zone item." These are honest but weak and do not belong in a top-tier submission except as a one-line pointer.

---

## TASK 4 — Evidence vs Claims

| # | Claim (location) | Supporting evidence | Adequate? | Reviewer concern |
|---|---|---|---|---|
| 1 | "naive latent steering does not beat the bounded best-prompt ceiling on any adjudicated axis" (Abstract; Sec. 4.2) | Table `c2-delta-4cell`: all cells fail pass rule | **Partly** | Failure driven by low power for deliberation/skepticism (wide CIs); this is non-detection, not demonstrated non-transfer |
| 2 | "the uncertainty axis consistently harms calibration in all four cells; all four CIs exclude zero, all negative" (Abstract; Sec. 4.3) | Fig. `c2-calibration-harm`; Table rows: −0.228, −0.072, −0.103, −0.084, CIs exclude 0 | **Yes (statistically)** | But construct-validity confound: steering toward "uncertainty" pole mechanically inflates hedging → worse 1−Brier by design, not a "control" pathology |
| 3 | "pre-registered negative replicates across five seeds" (Abstract; Sec. 4.2) | 5-seed arm, all cells fail | **No** | Seeds share one item pool; only split varies. Not independent replication (authors concede) |
| 4 | "cross-model representational support for deliberation and skepticism" (Abstract; C1; Sec. 4.1) | Table `c1-twomodel` two rows agree | **No** | n=1 run/model; other two axes flip; "support" over-reads two single runs |
| 5 | PSR arm "provides preliminary evidence the negative is not merely a consequence of naive directions" (Abstract; Sec. 2.2) | single-model/single-seed DEV-optimized arm returns null | **Weak** | Single run; α-comparability caveat (Sec. 6) leaves "too weak" objection open |
| 6 | "generalized scoped negative" across grid (C3) | 2×2×3 all fail | **Overstated** | "Generalized" from 12 underpowered, non-jointly-corrected tests |
| 7 | Design implications: consoles should surface READ/TRANSFER/ceiling/harm/tier (C4; Sec. 5) | Fig. `fig:console` static mock; failure taxonomy Table `failure-taxonomy` | **No (as HCI claim)** | Zero user data; utility, comprehension, and trust-calibration benefit are asserted. Ironic for a trust-calibration paper |
| 8 | Work "potentially of interest across HCI, fairness, and AI safety" (Sec. 1) | rhetorical | **No** | Reach claim with no fairness/safety experiment |
| 9 | Console values "read from frozen, independently audited artifacts rather than hand-entered" (Sec. 5) | pipeline description | **Unverifiable from PDF** | Artifacts are supplementary; anonymized submission gives reviewer no access |
| 10 | Social axis "legible in latent space while feared manipulation channel is absent at power" (Sec. 6.1) | N=54, LLM-judge-only null | **No** | Explicitly not a contribution; underpowered; human calibration pending |

**Bottom line:** the only claim that clears its own bar is #2 (statistical calibration harm), and even that has a construct confound. Claims #1, #3, #4, #6 exceed their evidence; #7 (the HCI/design contribution) has no supporting data at all.

---

## TASK 5 — CHI/CSCW Contribution Test

Using Wobbrock & Kientz's contribution types:

- **Empirical:** Present but weak — a mostly-underpowered null on 2 models/2 methods with no humans. Contributes little *human-centered* empirical knowledge. **Insufficient for CHI/CSCW.**
- **Methodological:** The "frozen adjudicator" is competent held-out evaluation with multiplicity control — solid ML practice but not a novel HCI method, and offers no method for studying *people*. **Weak for HCI venues.**
- **Theoretical:** "Legible ≠ controllable" is a corollary of cited theory (Mishra), not a new theory. **Not a contribution.**
- **Artifact/Design:** A five-signal UI "contract" and a static, cropped console mock (Fig. `fig:console`). No implemented, evaluated, or deployed system; no design process; no users. **Fails the CHI design-contribution bar.**
- **Systems:** No system contribution — the console is a rendering.
- **Dataset/Opinion:** N/A.

**Strongest category:** methodological/empirical *from an ML standpoint*. **For CHI/CSCW/IUI specifically, the strongest category is Design — and it is unvalidated.** None of the categories reach the bar for a sub-25% HCI venue. This paper's natural home is an interpretability/ML venue or workshop (NeurIPS/ICLR interp workshop, or the venues where Mishra/Sprejer/Heyman appear), not CHI/CSCW.

---

## TASK 6 — Three Simulated Reviewers

### Reviewer A — Constructive but critical
- **Strengths:** Unusually rigorous pre-registration and artifact lineage; honest, well-scoped negative; a genuinely useful conceptual distinction (legibility vs controllability); the calibration-harm sub-finding is practically relevant.
- **Weaknesses:** No user study for an HCI venue; the design contribution is speculative; the null is underpowered; C1 over-labeled as replication; heavy hedging makes the actual contribution hard to locate.
- **Questions:** (1) Why CHI rather than an interp venue? (2) What is the minimum detectable effect at N=40–53, and can you provide equivalence bounds? (3) Can you show even a small formative study that the five-signal card improves calibrated reliance?

### Reviewer B — Methodology-focused skeptic
- **Strengths:** DEV/TEST discipline, paired bootstrap, Bonferroni, coherence gate — the internal-validity scaffolding is good.
- **Weaknesses:** A frozen *null* with no power/equivalence analysis is uninterpretable as "non-transfer"; multiplicity is controlled within a cell but the paper claims grid-wide generalization without joint error control; the 5-seed "replication" re-splits one deterministic slice (not independent); the comparator's prompt/α protocol — the linchpin of "fairness" — is not in the paper; δ=0.05 is applied across three incommensurate outcome metrics; C1 facade thresholds look post-hoc; calibration "harm" may be a definitional artifact of steering toward an uncertainty pole scored by 1−Brier.
- **Questions:** (1) Provide TOST/equivalence tests per cell. (2) Report the full prompt search space and α grid in the main text. (3) Rerun seeds on *independent* item draws. (4) Decompose the Brier harm into reliability vs resolution vs base-rate to rule out the "axis does what it says" confound.

### Reviewer C — Novelty-focused skeptic
- **Strengths:** Clear framing; tidy neighbor table (`tab:novelty-neighbors`).
- **Weaknesses:** The scientific finding substantially overlaps concurrent Sprejer et al.; Heyman shows steering *can* mimic prompting, so the negative is confined to a weak method the community already expects to lose; Mishra supplies the whole premise. The residual novelty is the HCI framing, which is unvalidated. "Frozen adjudicator"/"facade ratio" rename standard practices. C1 "cross-model support" from n=1×2 is inflated.
- **Questions:** (1) What survives if Sprejer is treated as prior, not concurrent? (2) What is the contribution beyond "naive CAA/ITI < prompts on 7–8B," given Heyman? (3) Remove the unvalidated console — what novel, defensible claim remains?

---

## TASK 7 — Meta-Review (Associate Chair)

**Summary of discussion.** All three reviewers credit the methodological hygiene and the honesty of a well-scoped negative, and all three converge on the same fatal pattern for this venue: **there is no human anywhere in the paper.** For CHI/CSCW/IUI, the design contribution (the five-signal console "contract") is asserted from model evidence with zero user data — a critical gap, and a self-undermining one for a paper whose thesis is trust *calibration*. Reviewer B additionally establishes that the empirical core is an **underpowered null** presented as evidence of absence, with non-independent "replication" and an unauditable comparator. Reviewer C establishes that the scientific finding is largely pre-empted by concurrent (Sprejer) and adjacent (Heyman, Mishra) work, leaving mainly framing.

**Likely outcome.** **Reject** at CHI/CSCW; possible **weak reject / major-revision** at IUI only if reframed. The paper is well-executed *as an ML-interpretability note* but does not clear the human-centered contribution bar of a top HCI venue.

**Major concerns (must-fix).**
1. No user study / no validated design contribution — the central problem for this venue.
2. Underpowered null lacking equivalence/power analysis; "non-transfer" over-read from non-detection.
3. Non-independent multi-seed "replication"; no grid-wide multiplicity control despite grid-wide claim.
4. Novelty pre-empted by concurrent/adjacent work; contribution reduces to framing.
5. Construct-validity confound in the calibration-harm headline.
6. Comparator fairness (prompt/α protocol) not in the paper; unauditable.

**What must be fixed before acceptance.** Either (a) add a real, pre-registered human-subjects evaluation showing the boundary-instrumenting console improves calibrated reliance/decision quality (turning C4 into an actual HCI contribution), or (b) move the paper to an interpretability venue and drop the HCI framing. Additionally: add power/equivalence analysis, independent-draw replication, joint multiplicity control, decompose the Brier harm, and surface the comparator protocol in the main text.

---

## TASK 8 — Final Scores (1–5; 5 = best)

| Dimension | Score | Justification |
|---|---|---|
| Originality | **2.5** | Concept is a corollary of cited theory; finding overlaps concurrent Sprejer; residual novelty is unvalidated framing |
| Significance | **2** | Scoped null on 2 small models/2 naive methods, no users; limited reach for HCI |
| Methodological Rigor | **3** | Excellent pre-registration/lineage, but underpowered null, non-independent seeds, no equivalence test, unauditable comparator |
| Technical Quality | **3** | Competent, careful pipeline; construct-validity and power gaps |
| Clarity | **3** | Precise but over-hedged, jargon-dense; contribution buried; large non-contribution digression (Sec. 6.1) |
| Reproducibility | **3.5** | Frozen JSON + generated tables/figures is strong; but full model-run pipeline not reproducible from PDF, artifacts supplementary/anonymized |
| **Overall Recommendation** | **2 (Reject / Weak Reject for CHI)** | Good ML note, not a top-tier HCI contribution as submitted |
| **Reviewer Confidence** | **4 / 5** | High familiarity with steering, interpretability, and HCI methodology; some judgments rest on supplementary material not in the PDF |

---

## TASK 9 — Acceptance Probability

- **CHI: ~7–10%.** Fatal absence of any human-subjects work at a venue that expects a human-centered contribution; the design claim is explicitly non-empirical; the empirical core is an ML null. Rigor and honesty earn it a hearing but not acceptance.
- **CSCW: ~8–12%.** Same core problem; CSCW's collaborative/social framing is even less served (no social, organizational, or collaborative dimension despite the abandoned social-inference probe).
- **IUI: ~18–25%.** IUI is more tolerant of systems/model-leaning intelligent-interface papers; if reframed as an evaluation methodology for latent-control affordances with at least a formative user check, it could become borderline. As currently submitted (no user), still below the line.

**Why:** the work is methodologically respectable but sits in the wrong community. The scientific finding is incremental and partly pre-empted; the HCI contribution is unvalidated. Top HCI venues reject "should-be-an-interpretability-paper" submissions even when technically clean.

---

## TASK 10 — Revision Roadmap (2 weeks; top 10 by impact)

1. **Add a formative human-subjects evaluation** (even n≈15–20, pre-registered) showing the five-signal console improves calibrated reliance vs a slider baseline — converts C4 from assertion to an actual CHI contribution. *(Highest impact; likely > 2 weeks, but decisive.)*
2. **Add power / equivalence analysis (TOST) per cell** and report minimum detectable effects, so the null means "no meaningful effect" rather than "underpowered." Reframe all "does not beat" language accordingly.
3. **Sharpen novelty vs Sprejer/Heyman/Mishra:** state in one paragraph exactly what survives if Sprejer is prior and Heyman bounds the claim; cut contribution-inflation words ("generalized", "replication" for n=1).
4. **Fix the "replication" claim:** either run seeds on *independent* item draws or downgrade the 5-seed language to "split-robustness within one pool" (currently buried).
5. **Add grid-wide multiplicity control** (or explicitly restrict claims to per-cell) to make "generalized negative" statistically legitimate.
6. **Resolve the calibration-harm confound:** decompose 1−Brier (reliability/resolution/base-rate) and show the harm is not the mechanical result of steering toward an uncertainty pole.
7. **Move the comparator protocol into the main text:** prompt search space, budget, α grid — the "fairness" claim is currently unauditable from the PDF.
8. **Cut the social-inference and breadth/focus digressions (Sec. 6.1)** to a single sentence + pointer; they are self-declared non-contributions and dilute the paper.
9. **Replace the cropped console mock (Fig. `fig:console`, `trim=... clip`) with an honest, uncropped figure**, and clearly label it a non-evaluated design artifact.
10. **Retarget or reframe for venue:** if no user study is feasible, reposition to an interpretability venue; if staying at IUI, foreground the evaluation-methodology contribution and add at least a lightweight user check.

---

*End of Reviewer A review.*
