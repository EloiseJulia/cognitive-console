# HCI Editorial Rewrite Plan — `docs/paper/main.tex`

**Scope:** narrative, logic, and prose only. No number, table, figure, citation, claim-map gate, or
scope caveat is changed. Target venue: ACM IUI (CHI/CSCW-style narration discipline).
**Branch:** `feature/hci-rewrite` (worktree `.worktrees/hci-rewrite`).

---

## 0. What I internalized before touching the text

**(1) How UIST/CHI/CSCW best papers are written.** They start from a tension the reader can feel in
their own hands, not from a literature gap. The reader is put inside a situation ("here is a thing
interfaces are now doing, and here is the inference it invites") before any method appears. There is
a designerly through-line: the design problem determines what gets measured, the measurement result
comes back and changes the design reasoning, and the closing move is a piece of transferable
knowledge rather than a summary of the system. Insight beats feature-listing: a best paper is
remembered for one idea, not for five components. Limitations are stated early, plainly, and in the
authors' own voice, because credibility is part of the argument.

**(2) How HCI papers build a narrative.** Four load-bearing beams: a real design problem, an
analysis insight that a designer could not have guessed, an account of where the human/AI division
of labour actually sits, and a transferable insight other researchers can reuse. Each beam has to be
*earned*: a design problem is grounded in artifacts that exist or in cited prior findings, never in
invented user needs; the insight has to be traceable to evidence; the transferable part has to be
stated as a contract or a discipline, not as a slogan.

**(3) How HCI narration differs from AI/systems narration.** In an ML paper, motivation is a
formality and the contribution is the artifact plus the number. In an HCI paper, motivation and
implication carry a large share of the argument, and the contribution is *knowledge*, not a system
dump. Method sections are written so the reader can judge validity, not so the reader can reimplement
line by line. Negative results are publishable when the question was worth asking and the instrument
is described honestly. Hedging is respected, but hedging is not evidence, and hedge density is a
readability cost that reviewers charge against clarity.

---

## 1. DIAGNOSIS of the submitted paper

### 1.1 Narrative problems

- **No felt tension.** The Introduction opened on a literature roll-call ("Prompt instruments reify
  ...; transparency work asks ...; feature-steering interfaces suggest ..."). The reader learns what
  fields exist before learning what is at stake. The interesting move (interfaces are starting to
  render model cognition as *nameable and adjustable*, which quietly licenses "readable therefore
  controllable") was present but buried as a subordinate clause.
- **Enumeration instead of a spine.** The paper reads as a list of assets: C1, C2, the robustness
  arm, the PSR arm, the split-seed arm, the off-manifold null, a taxonomy, a contract, a console
  figure, an appendix. Every asset is announced; nothing accumulates. There is no sentence-level
  chain that carries the reader from the design problem to the measurement choice to the verdict to
  the design consequence.
- **The HCI frame is a jacket, not a skeleton** (Reviewer A: "removing all HCI prose would not
  change a single number"). §1, §6 and §8 spoke HCI; §3–§5 spoke ML evaluation; the join was
  asserted rather than argued. Nothing in the Method section explained *why an interface question
  forces this particular comparator*, which is exactly the sentence that would have made the join
  real.
- **The contract arrives as a bullet list, not as reasoning.** The five signals were stated as a
  specification. A reader could not see which piece of evidence forces which signal, so the section
  read as a prescription (the "design implications drawn from data" pattern HCI has criticized for
  fifteen years).
- **Venue-pitch inflation at the end of §1.** The paragraph claiming relevance "across HCI,
  fairness, and AI safety communities" is marketing, not argument, and reviewers flagged it as
  contribution inflation (Stage B m1). It also undercuts the paper's main asset, which is restraint.

### 1.2 Logic problems

- **The motivating inference is never made concrete.** "Legible therefore controllable" is asserted
  as an appealing inference but never tied to a specific interface act (turning an axis into a
  slider, labelling a card green) until the vignette in §6, which is late.
- **The comparator's role is under-motivated.** The bounded best-prompt baseline is the intellectual
  core of the design: without it, "steering changes behaviour" is trivially true and uninformative.
  The submitted text explained the mechanics of DEV selection before explaining why an interface
  question demands a comparator at all.
- **Setup/headline confusion.** C1 was introduced with the same rhetorical weight as C2, so the
  reader had to be told repeatedly that it is exploratory instead of being able to see it is setup.
- **Discussion repeats Results.** The Heyman boundary, the Sprejer corroboration and the scope
  paragraph appear in Intro, Related Work, and Discussion in near-identical wording.

### 1.3 HCI-style gaps

- Trust-calibration literature was cited in a single defensive clause rather than being used to
  reason. The six added references (Amershi; Lee & See; Bansal; Buçinca; Mitchell; Gebru) were
  parked in one sentence each and one long `\cite{...}` pile-up.
- Related Work was ordered ML-first (non-surjectivity → steering lineage → HCI), so an HCI reader
  meets the interfaces they care about last.
- The failure taxonomy (F1–F5) was described but never used as a design vocabulary in the running
  argument.

### 1.4 AI-generated-text tells

- `Our thesis is that ...`; `This paper makes two evidence-bearing contributions and one design
  implication:` followed by mechanical scaffolding.
- Uniform paragraph geometry: nearly every paragraph is 3–5 sentences and closes with a templated
  summary line ("This lineage is what permits ...", "Together, these controls make ...").
- Over-hedged parallelism, repeated to the point of tic: "It is not X, nor Y. It is Z." occurs ~6
  times; "not an impossibility theorem" is restated in four sections in nearly identical words.
- Drumbeat vocabulary: *frozen* (~30×), *bounded* (~25×), *pre-registered pass rule* (~10×),
  *no demonstrated superiority* used as a fixed phrase rather than as English.
- Formulaic connectors: *Thus*, *Therefore*, *Moreover*, *Together*, *Finally* opening consecutive
  paragraphs.
- Em-dashes used as an all-purpose joint.
- Hedge stacking inside single sentences, which reviewers scored as a clarity cost (Clarity 3/5).

---

## 2. REWRITE STRATEGY

**One spine, stated once and never abandoned:**

> Interfaces are starting to render a model's cognitive state as something you can name and move.
> That is a design act with an implied promise. We test the promise with a frozen adjudication that
> makes the prompt channel and the latent channel compete on the same items. In the tested setting
> the promise does not hold, and the trust-relevant axis is actively damaged. So a console's job is
> to instrument the legibility/control boundary rather than to hide it behind a slider.

**Moves applied section by section:**

1. **Lead with the artifact, not the literature.** Every section now opens on a concrete thing (an
   interface act, a card, a table, a failure) and reaches for citations second.
2. **Make the comparator the idea.** The Method opens by arguing *why* an interface question forces a
   comparator, then gives the mechanics. This is what welds §3–§5 to §1 and §6.
3. **Demote C1 structurally, not by repetition.** C1 is introduced as setup ("what we had to
   establish before the real test") so its exploratory status is carried by position as well as by
   the required labels, which are all retained.
4. **Derive the contract instead of specifying it.** §6 now walks evidence → failure class → signal,
   so each of the five signals is visibly forced by something in the tables, and the honest gap
   (no user evidence) is the section's own argument rather than a disclaimer bolted on.
5. **Use the trust literature to reason.** Lee & See, Bansal, Buçinca, and Amershi now carry the
   argument that exposed signals can backfire, which is the reason the contract is framed as an
   evaluation discipline and an open hypothesis rather than a user benefit. Mitchell and Gebru carry
   the genre comparison (documentation artifacts) and the differentiation of the per-affordance unit.
6. **Rhythm.** Deliberate variation: short declaratives to open and to land, longer sentences for
   protocol detail. Paragraph lengths now range from one sentence to eight. Templated closers,
   formulaic connectors, and the "It is not X. It is Y." tic are cut. Repeated caveats are stated
   once per section in the section's own words, not re-pasted.
7. **Em-dashes minimized** throughout, replaced by commas, periods, and parentheses.
8. **No new claims.** Every scope guard from `claim-map.yaml` survives: C1 exploratory and
   axis-heterogeneous, C2 as a scoped *failed-superiority* negative (not equivalence) with robust
   uncertainty harm and underpowered deliberation/skepticism non-detections, split seeds over the
   same item pool, C3 as an interface-evaluation implication with no user-study claim, C4 appendix
   exploratory, C2-mech as a reported null. "Not an impossibility theorem", "underpowered
   non-detection is not equivalence", and "human study deferred" all remain.
9. **Calibration-harm framing untouched in substance.** The format-compliance recheck is still
   described as in progress, the parser and the conf→0.5 imputation rule (and the resulting 0.75
   score) remain disclosed, and the format-fragility caveat from the E-0006 audit is preserved. No
   sentence in the rewrite claims the confound is resolved.
10. **Over-claim removed, not added.** The "of interest across HCI, fairness, and AI safety
    communities" pitch is replaced by a grounded, cited statement about why degraded calibration
    cues are a design risk.

**Invariants enforced during editing:** no numeric value typed into prose; all `\input`, `\ref`,
`\label`, `\cite` keys preserved; all 30 bibliography keys still referenced at least as before; the
LaTeX build must produce a PDF.
