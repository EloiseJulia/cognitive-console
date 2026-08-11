# Paper Reconstruction Handoff (2026-08-11)

This directory transfers the reconstructed manuscript and its evidence controls back into the full `cognitive-console` repository. It is intentionally isolated from the repository's current `docs/paper/main.tex`, `references.bib`, generated tables, figures, and artifact lineage.

## Important Status

- **Canonical prose source:** `pipeline/CONDITIONAL_PAPER.md`
- **Front matter and ACM template:** `pipeline/iui_conditional.template.tex`
- **Generated output:** `reframed.tex` (do not edit as the primary source)
- **Current rendered baseline:** `reframed.pdf` (16 pages, 26 cited references, clean build on 2026-08-11)
- **Bibliography used by the generated TeX:** `reframed-references.bib`
- **Venue conflict requiring human adjudication:** this handoff uses an anonymous IUI-style `acmart` template, while the repository constitution currently names CHI as the target venue. Do not replace the repository's primary manuscript or change venue claims without the required human gate.

## Why This Handoff Exists

The reconstruction reframes the paper around a real interface trajectory:

1. Bo et al. prototype user-facing activation-steering controls.
2. Golden Gate Claude publicly demonstrates interaction with an internally modified model.
3. The paper asks what evidence should support turning a named latent direction into a product-facing control.
4. The reported qualification rule and the post hoc four-state design mapping are explicitly separated.

The handoff preserves strict boundaries: the prompt comparator is DEV-selected from a preregistered bounded candidate set; the assay has no passing latent behavioral positive control; the four-state mapping is not a preregistered or validated rubric; and human/prompt-plus-steer results remain pending.

## Package Contents

### Manuscript outputs

- `reframed.tex` — generated TeX snapshot.
- `reframed-references.bib` — bibliography snapshot used by the generated TeX.
- `reframed.pdf` — visual baseline for comparison after integration.

### Canonical writing pipeline

- `pipeline/CONDITIONAL_PAPER.md` — canonical manuscript body.
- `pipeline/iui_conditional.template.tex` — title, abstract, template, and front matter.
- `pipeline/conditional_to_latex.lua` — Pandoc conversion filter.
- `pipeline/BUILD.md` — original build notes.
- `build.ps1` — handoff-local portable build command.

### Evidence and claim controls

- `pipeline/FACT_LEDGER.md`
- `pipeline/CLAIM_GRAPH.md`
- `pipeline/OPEN_ITEMS.md`
- `pipeline/citation_audit.md`
- `pipeline/WRITING_GUARDRAILS.md`
- `pipeline/NOVELTY_DEFENSE.md`
- `pipeline/CONDITIONAL_ASSEMBLY_AUDIT.md`

### Pending-study and adjudication controls

- `pipeline/HUMAN_STUDY_PENDING.md`
- `pipeline/PROMPT_STEER_PENDING.md`
- `pipeline/AUTHOR_ADJUDICATION_2026-08-11.md`
- `pipeline/CONFLICT_DECISIONS.md`

### Source tracking

- `pipeline/SOURCE_REGISTRY.yml`
- `pipeline/SOURCE_MANIFEST.json`

Some source-registry paths describe the reconstruction workspace and may need remapping to this repository's real artifacts.

## Build

From this handoff directory in PowerShell:

```powershell
.\build.ps1
```

Requirements:

- Pandoc available on `PATH`, or at the default local path used by the script.
- MiKTeX with `pdflatex` and `bibtex`.

The script regenerates `reframed.tex` from the Markdown source and compiles `reframed.pdf`.

## Integration Order

Do not overwrite `docs/paper/main.tex` immediately. Integrate in this order:

1. **Map evidence to real repo artifacts.** Reconcile `FACT_LEDGER.md`, `SOURCE_REGISTRY.yml`, and `SOURCE_MANIFEST.json` with `results/`, experiment IDs, code commits, data hashes, generated tables, and figures.
2. **Resolve missing method facts.** Exact checkpoints, layers, hooks, wrappers, item denominators, exclusions, seeds, degradation scorer, and freeze chronology must come from code/artifacts rather than prose inference.
3. **Recompute claim-bearing values.** Replace manuscript-attested values with script-generated outputs and update the claim/evidence ledgers.
4. **Integrate pending branches.** Populate the human-study and prompt-plus-steer packets regardless of whether results are positive, null, mixed, adverse, invalid, or delayed.
5. **Re-run narrative selection.** Update claims, Introduction, title, abstract, Results, Discussion, Limitations, and Conclusion after branch integration.
6. **Adjudicate venue/template.** Reconcile the handoff's IUI template with the repository's current CHI target through the human approval gate.
7. **Promote deliberately.** Only after evidence audit and venue adjudication should content move into `docs/paper/main.tex` and `docs/paper/references.bib`.

## Writing Invariants

Follow `pipeline/WRITING_GUARDRAILS.md`. In particular:

- Use READ evidence / TRANSFER evidence / CONTROL permission.
- Use the formal states *Diagnostic-only*, *Unresolved*, *Unstable*, and *Eligible*.
- Distinguish evidence profiles, affordance states, and evidence tiers.
- Distinguish the preregistered bounded candidate set from the DEV-selected prompt comparator.
- The reported qualification rule produces the 0/12 classification.
- The four-state mapping is a separate post hoc design synthesis and does not produce or validate 0/12.
- Do not claim comparator fairness/global optimality, assay validation, inter-rater validation, general steering failure, or human benefit without new evidence.

## Recommended First Action in the Full Repo

Create a fresh evidence-integration branch. Have an independent agent map every `FL-*` fact and `C-*` claim to existing repository artifacts before changing the primary manuscript. Treat mismatches as audit findings, not as instructions to make the code agree with the paper.
