# Independent Hostile Audit — Paper Revision (feature/submission-revision @ b12fa29)

Audited diff: `main..b12fa29`. Role: read-only hostile paper-revision auditor; this report is the only committed artifact.

## Verdict

**READY-TO-MERGE.** I found **no BLOCKER, MAJOR, or UNVERIFIED findings**. The revision is honest about the negative result, keeps scope bounded to naive/off-the-shelf CAA/ITI plus explicitly exploratory PSR support, does not claim user-study/user-benefit evidence, and the newly exposed selected prompt texts trace to committed artifacts.

## Ranked findings

- **None.** No BLOCKER/MAJOR/MINOR/UNVERIFIED issue found that should block merge.

## Over-claim / scope integrity

**Pass.** I checked title, abstract, contributions, results, interface-contract section, limitations, and conclusion.

- Title is scoped: `No Demonstrated Superiority over Bounded Prompts under Naive CAA/ITI Steering` (`docs/paper/main.tex:24`).
- Abstract explicitly says no demonstrated superiority under the pre-registered pass rule, uncertainty harm is the robust part, deliberation/skepticism are underpowered non-detections and not proof of zero/equivalence, split-seed robustness is over the same item pool, PSR is exploratory, and C3 is not a user-study claim (`docs/paper/main.tex:37`).
- Contributions separate exploratory C1 from C2/C3; C2 says superiority test, not equivalence/universal non-controllability; C3 says model-evidence implication, not user-study claim (`docs/paper/main.tex:56-73`).
- Results maintain failed-superiority scope and explicitly reject universal steering claims (`docs/paper/main.tex:209-215`).
- Interface contract and vignette disclaim measured user benefit (`docs/paper/main.tex:238`, `docs/paper/main.tex:243`, `docs/paper/main.tex:248`).
- Limitations and conclusion explicitly reject impossibility theorem, prompt/latent equivalence, mechanism proof, and demonstrated user benefit (`docs/paper/main.tex:274-280`, `docs/paper/main.tex:293`).

## Prompt-text authenticity

**Pass.** The new `selected_best_prompts` entries in `docs/paper/table-manifests/c2-delta-4cell.yaml:37-123` are real.

Verification performed: parsed all 12 manifest entries; for each, checked that the source artifact exists, SHA-256 matches the manifest hash, `best_prompt_id` and `best_prompt_text` occur in the named `c2b_adjudication_results.json`, and the same id/text pair exists in the committed prompt bank.

Evidence examples:
- Manifest points CAA/Llama deliberation to `delib-strong-02` with source hash (`docs/paper/table-manifests/c2-delta-4cell.yaml:41-47`); the source JSON contains the same id/text (`results/arm_full/cell_caa__llama3-8b/c2b_adjudication_results.json:44-47`) and the bank contains the text (`data/strongest_prompts/deliberation.jsonl:2`).
- Qwen deliberation uses `delib-strong-09`, matching source JSON (`results/arm_full/cell_iti__qwen2.5-7b/c2b_adjudication_results.json:44-47`) and bank (`data/strongest_prompts/deliberation.jsonl:9`).
- Skepticism and uncertainty selected texts match committed banks (`data/strongest_prompts/skepticism.jsonl:6`, `data/strongest_prompts/skepticism.jsonl:11`, `data/strongest_prompts/uncertainty_awareness.jsonl:1`, `data/strongest_prompts/uncertainty_awareness.jsonl:9`).

## Hand-edited / fabricated number check

**Pass.** `git diff main..b12fa29 -- docs/paper/tables/ docs/paper/*.tex` shows no result-table numeric edits. The only table-file diff is wording in `failure-taxonomy.tex` (`docs/paper/tables/failure-taxonomy.tex:1-16`), not numeric result values. C2 quantitative table remains auto-generated from JSON and still states that full prompt text is in the manifest (`docs/paper/tables/c2-delta-4cell.tex:1`, `docs/paper/tables/c2-delta-4cell.tex:31`). The post-hoc equivalence table is also auto-generated and labeled exploratory/not pre-registered (`docs/paper/tables/equivalence-tost.tex:1-4`).

I reran the paper generators. Tables remained clean; the two plotted PDFs became byte-dirty due generator/PDF nondeterminism and were reverted before committing this report. This does not indicate hand-edited numbers.

## Claim-map gates

**Pass.** Claim map and paper prose are consistent.

- C1 remains exploratory/setup: claim-map requires exploratory/scoped use (`docs/paper/claim-map.yaml:2-10`); paper labels it setup/diagnostic and exploratory (`docs/paper/main.tex:56-61`, `docs/paper/main.tex:202-204`, `docs/paper/main.tex:293`).
- C2 is the frozen core with E-0005/E-0006/E-0011 and exploratory E-0009 only (`docs/paper/claim-map.yaml:11-21`); paper does not upgrade PSR over the frozen headline (`docs/paper/main.tex:263`, `docs/paper/main.tex:274`, `docs/paper/main.tex:293`).
- C3 has no standalone evidence row and is allowed only as interface-evaluation implication (`docs/paper/claim-map.yaml:40-48`); paper repeatedly states no user-study/user-benefit claim (`docs/paper/main.tex:70`, `docs/paper/main.tex:238`, `docs/paper/main.tex:280`).
- C4 remains discussion-only exploratory and not in Abstract/Contributions/Conclusion (`docs/paper/claim-map.yaml:49-67`; paper discussion at `docs/paper/main.tex:258-261`).
- C2-mech remains null/future work, not a positive claim (`docs/paper/claim-map.yaml:22-30`; paper at `docs/paper/main.tex:228`, `docs/paper/main.tex:276`, `docs/paper/main.tex:286`).

## Five-seed wording

**Pass.** Headline uses qualify the seeds as DEV/TEST split seeds over the same item pool:

- Abstract: `five DEV/TEST split seeds over the same item pool` (`docs/paper/main.tex:37`).
- Results: same-pool and not independent item draws (`docs/paper/main.tex:215`).
- Limitations/conclusion: same-pool wording and split-membership caveat (`docs/paper/main.tex:274`, `docs/paper/main.tex:293`).

## E-0012 leak check

**Pass with intended exclusion-note exception.** Grep for `E-0012|verified-control|settling-grid|comparator-strength` over paper body, manifests, and submission ledger found no paper-body or manifest leaks. The only match is the intended exclusion note in `docs/paper/submission-evidence-ledger.md:3`, and ledger rows contain only E-0003..E-0011 (`docs/paper/submission-evidence-ledger.md:7-15`). Decision provenance confirms E-0012 termination/invalidity and venue authorization (`docs/ledgers/decision-log.md:8-17`).

## LaTeX well-formedness

**Pass.** Ran `docs\paper\build.ps1 -Clean` with MiKTeX/pdflatex+bibtex; exit code 0 and produced `docs\paper\build\main.pdf`. Static inspection also found table inputs, labels, refs, and figure includes consistent (`docs/paper/main.tex:179`, `202`, `207`, `213`, `232`, `245-250`, `298`).

## Gap completeness (10/10)

1. Scope wording fixed: title/abstract/contributions use no-demonstrated-superiority and naive/off-the-shelf CAA/ITI (`docs/paper/main.tex:24`, `37`, `68-70`).
2. Split-seed language fixed: same item pool caveat appears in abstract/results/limitations/conclusion (`docs/paper/main.tex:37`, `215`, `274`, `293`).
3. C3 reframed as interface-evaluation contract with UI vignette and no user-benefit claim (`docs/paper/main.tex:70`, `238`, `243`).
4. Calibration harm foregrounded and mechanism demoted/open (`docs/paper/main.tex:69`, `211`, `226-228`, `276`).
5. Bounded-prompt reconstruction added with prompt text/source hashes (`docs/paper/table-manifests/c2-delta-4cell.yaml:37-123`) and 16-prompt budget rationale (`docs/paper/main.tex:145`).
6. Novelty one-liner added against nearest neighbors (`docs/paper/main.tex:103`).
7. Construct-validity limits added for axis outcomes and 1-Brier (`docs/paper/main.tex:147`, `278`).
8. Format/parser-disruption caveat added: no trunc/empty collapse, format fragility plausible (`docs/paper/main.tex:228`).
9. Submission-filtered ledger added and excludes invalid E-0012 rows except exclusion note (`docs/paper/submission-evidence-ledger.md:1-15`).
10. C4 trimmed/discussion-only and C1 reframed as setup measurement (`docs/paper/main.tex:56-61`, `258-261`).

## Validation commands

- `python docs\paper\scripts\make_c1_twomodel_table.py; python docs\paper\scripts\make_c2_delta_table.py; python docs\paper\scripts\plot_c1_ratio_ci.py; python docs\paper\scripts\plot_c2_calibration_harm.py; python docs\paper\scripts\plot_console_ui_contract.py` — completed; console UI PDF written; PDF plot byte diffs reverted as non-report artifacts.
- `python -m pytest tests/test_console_data_loader.py tests/test_posthoc_equivalence.py -q` — passed: 76 passed, 2 skipped, 1 PytestRemovedIn10Warning.
- `docs\paper\build.ps1 -Clean` — passed, produced `docs\paper\build\main.pdf`.
