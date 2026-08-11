# Grounding the Evidence-to-Affordance Mapping

**Status:** proposal for Writer/Manager review; no manuscript source changed  
**Primary target:** `docs/paper/reconstruction-handoff-2026-08-11/reframed.tex`  
**Secondary alignment target:** `docs/paper/main.tex`

## Recommendation

Drop **Diagnostic-only / Unresolved / Unstable / Eligible** as a four-state
taxonomy. The four labels are not needed to implement the interface decision,
and the current definitions are neither mutually exclusive nor tied one-to-one
to interface actions.

Use the existing record to make two direct permission decisions:

1. **Named diagnostic visible** iff local READ is supported for the exact
   evidence tier.
2. **Active control eligible** iff READ is supported and the reported
   TRANSFER qualification rule passes for that tier.

All other information remains attached as an evidence reason, not promoted to
an affordance state. Examples are `TRANSFER not tested`, `interval spans zero`,
`estimate below the point-estimate floor`, `comparator-negative`, `coherence
criterion failed`, and `missingness limits interpretation`.

This leaves three reachable interface actions without naming a new taxonomy:

| READ | TRANSFER qualification | Interface action |
|---|---|---|
| unsupported | any result | Do not expose the named affordance. Retain the technical record for developers. |
| supported | no-pass or not evaluable | Permit a named read-only diagnostic; withhold the active control and show the reason. |
| supported | pass | The active control is eligible within the exact evidence tier; retain comparator, warning, and scope. |

“Eligible” here means only that the declared computational criteria were met.
It does not imply usability, benefit, appropriate reliance, deployment
readiness, or validation with people.

## Why the Four Labels Invite the Criticism

- **Diagnostic-only overlaps with Unresolved.** A READ-supported but
  underpowered record is both useful for diagnostic inspection and unresolved
  as behavioral evidence. A single label forces the paper to choose between
  two true descriptions.
- **Unresolved does not determine one interface action.** Unsupported READ
  should suppress the named affordance, whereas underpowered TRANSFER may still
  leave a READ-supported diagnostic visible.
- **Unstable is one failed predicate, not a distinct permission.** A coherence
  failure and a below-floor estimate both withhold the active control. The
  reason differs; the affordance decision does not.
- **Eligible already restates the qualification rule.** It needs no parallel
  taxonomy: eligibility can be read directly from READ plus the reported rule.
- **The reconstruction assigns states after seeing the profiles.** Even with a
  disclaimer, four named classes foreground the post-hoc synthesis and invite
  questions about why these four, why these boundaries, and why this
  granularity.

The simpler mapping preserves the important scientific distinctions without
turning every distinction into a UI category.

## Grounding in Existing HCI and Accountability Principles

The literature supports a direct evidence-to-action mapping, but it does not
support these exact four labels.

- Amershi et al.'s Guidelines 1 and 2 ask interfaces to make clear what an AI
  system can do and how well it can do it. Guideline 10 recommends scoping a
  service when in doubt, and Guideline 11 recommends making the reason for
  system behavior accessible. Here, those principles support withholding an
  unevidenced active control and showing the blocking reason; they do not
  require a four-state vocabulary.
- Tankelevitch et al. and Liao and Vaughan motivate connecting transparency to
  the user's task and available action. The relevant action in this paper is
  whether a named diagnostic or active control appears.
- Model Cards and Datasheets support retaining intended use, evaluation
  conditions, provenance, and scope. They ground the comparator, warning, and
  evidence-tier fields, not additional outcome categories.
- Raji et al.'s internal-audit framework supports staged, linked, versioned
  decision records. It grounds retaining predicate results and reasons through
  the lifecycle, rather than compressing them into an ornate badge.

Accordingly, the HCI story is: **show only the affordance that the current
record supports, and keep the reason and scope inspectable.**

## Separation of Computation, Interpretation, and Action

| Layer | What the paper may report | What it must not substitute |
|---|---|---|
| Computational output | READ support for the exact tier; TRANSFER estimate and interval; point-estimate-floor result; coherence result; qualification pass/no-pass when evaluable | A state label as if it were an empirical measurement |
| Evidence interpretation | Semantic label locally supported or unsupported; comparative evidence passed, did not pass, or was not evaluable; exact blocking reason | No-pass as ineffectiveness, equivalence, or general steering failure |
| Interface action | Hide the named affordance; show a read-only diagnostic; or make active control eligible within tier | Interface permission as evidence of user benefit or deployment readiness |

The reason field should remain specific. “Underpowered,” “missing,”
“comparator-negative,” and “coherence failed” are not synonyms and should not
be collapsed in prose even though they all withhold active control.

## Deterministic Check on Synthetic Records

Let `R` mean READ is supported in the exact tier. Let `Q` be the reported
qualification result when all required TRANSFER inputs are available:

`Q = (0 not in I) AND (mean_difference >= delta) AND coherence_pass`.

The interface mapping is:

`named_diagnostic = R`

`active_control_eligible = R AND transfer_evaluable AND Q`

The following records are synthetic and demonstrate only internal consistency.
They are not empirical evidence and do not validate the rule or interface.

| Record | R | TRANSFER / interval | Mean vs. `delta` | Coherence | Named diagnostic | Active control | Displayed reason |
|---|---:|---|---|---|---:|---:|---|
| S1 | 0 | not tested | n/a | n/a | no | no | READ unsupported |
| S2 | 1 | not tested | n/a | n/a | yes | no | TRANSFER not tested |
| S3 | 1 | interval spans zero | above | pass | yes | no | comparative effect unresolved at the declared interval |
| S4 | 1 | interval wholly negative | below | pass | yes | no | comparator-negative |
| S5 | 1 | interval wholly positive | below | pass | yes | no | below point-estimate floor |
| S6 | 1 | interval wholly positive | above | fail | yes | no | coherence criterion failed |
| S7 | 1 | interval wholly positive | above | pass | yes | yes | qualification passed within tier |
| S8 | 0 | interval wholly positive | above | pass | no | no | behavioral pass cannot authorize the named affordance without READ support |

This table also exposes why four formal states are unnecessary: S2--S6 have
different evidence meanings but the same active-affordance decision.

## Terminology

### Use

- `READ supported` / `READ unsupported`
- `TRANSFER pass`, `TRANSFER no-pass`, or `TRANSFER not evaluated`
- `read-only diagnostic`
- `active control withheld`
- `active control eligible within the evidence tier`
- `blocking reason`, followed by the specific predicate or evidence limit

### Remove as formal categories

- `Diagnostic-only`
- `Unresolved`
- `Unstable`
- bare `Eligible`
- `four-state mapping`, `state vocabulary`, and `formal affordance state`

“Unresolved” may remain ordinary prose when an interval, missingness analysis,
or assay question is genuinely unresolved. “Unstable” may describe a measured
coherence or layer-stability problem. Neither should be capitalized or treated
as a UI state.

## Surgical Edits for `reframed.tex`

### 1. Abstract

Replace the two sentences beginning “We then use a post hoc design mapping”
with:

> The five-field record maps those outputs directly to interface permissions:
> local READ support permits a named read-only diagnostic, while an active
> control is eligible only when READ is supported and the reported TRANSFER
> rule passes within the same evidence tier. No-pass and non-evaluable records
> retain their specific reasons rather than becoming separate affordance
> states; this mapping is a design proposal, not evidence of user benefit.

### 2. Introduction: paragraph after the three evidence profiles

Replace the paragraph beginning “The five-field record carries” with:

> The five-field record carries READ, TRANSFER, comparator, calibration
> warning, and evidence tier into the interface decision without adding a
> second outcome taxonomy. READ determines whether a named read-only diagnostic
> may be shown. READ plus a passing qualification result determines whether an
> active control is eligible within that tier. Other results withhold the
> active control while retaining the exact reason and next evaluation need.

Replace contribution 2 with:

> **A five-field decision record linking evidence to interface action.** The
> record preserves comparator, calibration warning, and scope while
> distinguishing permission to show a named diagnostic from eligibility to
> expose an active control.

### 3. Related Work

Replace “keep its control affordance *Diagnostic-only*” with “keep the
representation read-only and withhold an active control.”

At the end of the documentation/audit paragraph, add:

> These precedents justify traceability and scope; they do not supply or
> validate a four-category affordance taxonomy.

### 4. Five-Field Qualification Record

Replace the paragraph defining four formal states with:

> The record drives two interface permissions. Local READ support permits a
> named read-only diagnostic for the exact model, method, direction, layer,
> task, and protocol. An active control is eligible only when READ is supported
> and the reported TRANSFER qualification rule passes in that same tier.
> Untested, underpowered, missing, comparator-negative, below-floor, and
> coherence-failing records all withhold active control, but the record retains
> the distinct reason because it changes interpretation and the next
> evaluation step. This permission mapping is author-proposed and has not been
> evaluated with users.

Replace Figure `fig:evidence-flow` with a compact generated flow:

1. `READ supported?`
2. If no: `Do not expose named affordance`.
3. If yes: `Show named read-only diagnostic`.
4. `Reported TRANSFER rule passes?`
5. If no/not evaluable: `Withhold active control; display reason`.
6. If yes: `Active control eligible within evidence tier`.

Use this caption:

> **Direct evidence-to-action mapping.** READ support permits a named
> read-only diagnostic. Active control additionally requires a passing
> TRANSFER qualification in the same evidence tier. Other records withhold
> active control and retain the predicate or evidence limit that blocked
> qualification.

### 5. Reported Qualification Rule

Delete the paragraph that distinguishes the cell taxonomy from the four-state
vocabulary. Replace it with:

> The rule returns pass or no-pass only when its required inputs are
> available. A missing or unevaluable input withholds active-control
> eligibility without turning absence of evidence into a scientific failure.
> The record retains interval status, point-estimate-floor status, coherence,
> power, and missingness as separate reasons.

### 6. Results table `tab:axis-states`

Rename the table to `tab:axis-actions`. Change the third column heading from
“Proposed affordance state (reason)” to “Interface decision and next
evaluation.”

Use these entries:

- **Skepticism:** “Active control withheld; collect evidence with resolution
  near the declared 0.05 floor.”
- **Deliberation:** “Active control withheld; run a targeted confirmatory test
  rather than treating the mixed profile as equivalence.”
- **Uncertainty:** “Active control withheld; repair measurement and retain the
  comparator-specific missingness warning.”

Do not call all three `Unresolved`. Their common interface decision and
different evidentiary reasons are the point.

### 7. Interface-Facing Qualification Record

Rename “From Evaluation Output to Affordance State” to “From Evaluation Output
to Interface Action.”

Replace its opening two paragraphs with:

> The qualification record prevents three substitutions in interface
> reasoning. Internal READ must not substitute for behavioral TRANSFER;
> absolute change must not substitute for comparison with the declared
> alternative; and one evidence tier must not substitute for another. The
> record therefore controls two visible permissions rather than assigning a
> formal state: whether a named diagnostic may appear and whether it may be
> active.
>
> The computational outputs do not establish that this presentation is
> understandable or beneficial. The mapping below is a worked design
> application of the reported record.

Replace the worked-record interpretation with:

> For this record, local READ support permits a named read-only uncertainty
> diagnostic. The TRANSFER rule does not qualify the active control, so the
> slider remains withheld. The diagnostic displays the comparator and the
> missingness limitation rather than replacing them with an `Unresolved`
> badge.

In the illustrative scenario, replace “The trace names the *Unresolved*
state” with “The trace names the blocking reason.”

### 8. Discussion

Replace “The three no-pass stories then point to three actions” and its
following sentences with:

> The three no-pass stories do not require three control states. They lead to
> the same affordance decision—no active control—while changing what the
> record explains and what evaluation comes next. Skepticism requests more
> resolution; deliberation calls for a better-targeted test; uncertainty calls
> for measurement repair and a comparator-specific warning.

In “Qualification Is a Versioned Lifecycle,” describe updates as changes to
the record and permissions, not transitions among named states.

### 9. Limitations

Replace the sentence beginning “The four-state mapping was synthesized” with:

> The direct permission mapping is an author-proposed design recommendation,
> not a demonstrated human decision rule. The study does not establish that
> people understand the diagnostic, its blocking reason, or the conditions
> under which an active control becomes eligible.

Do not propose independent state assignment as a necessary validation target;
there is no longer a discretionary state assignment to reproduce.

### 10. Conclusion

Replace the final interpretive sentences with:

> The record preserves what the aggregate conceals: underpowered, mixed, and
> measurement-limited evidence require different explanations and next
> studies, even when they produce the same immediate interface decision.
> Local READ evidence may support a named read-only diagnostic. Active control
> remains withheld unless the reported comparative rule passes within the
> exact evidence tier.

### 11. Appendix Checklist

Replace “Issue a provisional state” with:

> **Apply interface permissions.** If READ is unsupported, do not expose the
> named affordance. If READ is supported, a named read-only diagnostic may be
> shown. Add active control only when the reported TRANSFER qualification rule
> passes in the same evidence tier. Attach the comparator, warning, scope, and
> any blocking reason.

## Alignment Edits for `main.tex`

The current paper uses a somewhat better action-oriented vocabulary
(`withheld-control` and `evidence-supported control`) but still presents four
labels as a taxonomy. Apply the same simplification:

- Abstract: replace the four-state list with the two permission decisions.
- “From Interface Risk to Evaluation Contract”: replace “The gate
  distinguishes four labels” with the direct mapping.
- “From Candidate Axis to Interface State”: rename to “From Candidate Axis to
  Interface Action” and replace the five branches with the compact flow above.
- “Interface-Evaluation Contract in Use”: describe `active control withheld`
  as an action and keep underpowered, missing, comparator-negative, and
  coherence-failing as reasons.
- “Evidence Tier and Versioned Affordance Lifecycle”: remove state-transition
  language; say that a model, method, direction, task, or version change creates
  a new record whose permissions must be recomputed.
- Conclusion: replace “diagnostic, unresolved, and withheld-control states”
  with “read-only diagnostics, withheld active controls, and their recorded
  reasons.”
- Regenerate `figures/concept.tex` and any dependent figure manifests rather
  than hand-editing generated artifacts.

## Claim Boundary

This proposal claims only that the simpler mapping is mechanically determined
by the existing READ precondition and reported qualification rule, and that it
reduces unnecessary category boundaries. It does not claim preregistration of
the mapping, independent reliability, empirical validation, user
comprehension, calibrated reliance, usability, benefit, or deployment safety.

## Sources Consulted

- Current manuscript: `docs/paper/main.tex`
- Reconstruction manuscript and pipeline:
  `docs/paper/reconstruction-handoff-2026-08-11/`
- Claim and citation maps: `docs/paper/claim-map.yaml`,
  `docs/paper/citation-map.yaml`
- Nearest-neighbor reviews:
  `docs/research/2026-07-23-novelty-falsification.md`,
  `docs/research/2026-07-23-priorart-sweep.md`, and
  `docs/paper/reconstruction-handoff-2026-08-11/pipeline/NOVELTY_DEFENSE.md`
- Amershi et al., *Guidelines for Human-AI Interaction*, CHI 2019,
  DOI: `10.1145/3290605.3300233`
- Mitchell et al., *Model Cards for Model Reporting*, FAT* 2019,
  DOI: `10.1145/3287560.3287596`
- Gebru et al., *Datasheets for Datasets*, CACM 2021,
  DOI: `10.1145/3458723`
- Raji et al., *Closing the AI Accountability Gap*, FAT* 2020,
  DOI: `10.1145/3351095.3372873`
- Tankelevitch et al., *The Metacognitive Demands and Opportunities of
  Generative AI*, CHI 2024, DOI: `10.1145/3613904.3642902`
- Liao and Vaughan, *AI Transparency in the Age of LLMs*, HDSR 2024,
  DOI: `10.1162/99608f92.8036d03b`
