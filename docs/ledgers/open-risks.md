# Open Risks (ranked)

1. **[HIGH] "This is NLP, not HCI" rejection.** Reviewers see steering mechanism as the core; HCI delta
   thin. Mitigation: interaction model + intent-expression-vacuum framing + controlled user study +
   design knowledge as moat. Owner: RQ2 framing.
2. **[MED] Obvious-combination increment (scoop cleared to LOW).** Manual prior-art sweep (D-0006) found
   NO paper occupies the exact gap → exact-scoop = LOW. But "obvious-combination" defense stays ~MED:
   survives only if Phase-0 facade (C1) + prompt↔latent conflict (C2b) are shown empirically. Neighbors
   (Huang&Lim, AI-Instruments, Labarta, Latent Manipulator CHI-EA'26) each hold one ingredient. Rename
   "Dual-Channel Steering" (already coined) at writing stage.
9. **[HIGH-NEW] PSR / "Steer Like the LLM" (ICML 2026) attacks C2b.** Shows activation steering can be
   trained to match/exceed prompt steering behaviorally — the strongest empirical threat to the behavioral
   prompt-unreachability claim. Mitigation: C2b uses a *bounded* prompt search + reports honestly; cite +
   pre-empt PSR; frame gap as "under bounded, user-realistic prompt effort," not absolute. **Status:** now
   explicitly pre-empted in `docs/paper/reframe-2026-07-24-reality-check.md` scope line: the claim is about
   naive, bounded, off-the-shelf CAA/ITI mean-difference-style steering, not trained/optimized steering.
7. **[HIGH-NEW] C2 theory over-application.** Mishra proves non-surjectivity of INTERNAL activations, not
   behavioral prompt-unreachability. C2 as written is not entailed by the cited theory — a hostile
   reviewer's sharpest attack. Mitigation: separate internal-state claim (theory-backed) from behavioral
   claim (must be empirically demonstrated, cannot be asserted from Mishra). Must fix before Charter Freeze.
8. **[RESOLVED 2026-07-28] Citation framing errors.** **Fully resolved:** SemanticLens/Labarta is
   corrected as **two distinct works** (see docs/research/2026-07-23-novelty-falsification.md, D-0003).
   **ActAdd App-B sub-claim: VERIFIED SAFE.** Submission-polish subagent checked arXiv:2308.10248v5 via
   ar5iv HTML: the single `\cite{turner2023actadd}` in main.tex is a **general main-body claim** only —
   "activation addition...motivates the idea that interpretable latent coordinates can be operationalized
   as controls." The paper's main body explicitly demonstrates topic-steering with activation vectors;
   this claim does not depend on Appendix-B exclusion experiments. No App-B-specific claims appear
   anywhere in main.tex. The WARNING in references.bib has been updated to reflect this finding.
   **Status: CLOSED. No further action needed.**
3. **[HIGH] Effect fragility / mechanism.** Phase 0 may show steering changes only surface style, or
   axes non-linear/orthogonal → dual-channel "coordination" narrative collapses. Mitigation: Plan B
   (limit probe) / Plan D (measurement paper) fallbacks in Charter §8.
4. **[MED] Over-anthropomorphism / over-trust** from explanation panel. Mitigation: functional-dimension
   language; calibrated trust as first-class metric.
5. **[MED] Concurrency latency** breaks study validity. Mitigation: vLLM-Hook; cap concurrent users.
6. **[MED] Human-subjects/IRB + budget** not yet approved — blocks Formative + controlled study.
10. **[LOW-NEW] Framed-stance contrast style.** phase0 contrast pairs *describe* the axis stance (e.g.
    "let me reason it through" vs "let me just answer") rather than enacting terse-vs-verbose — the only way
    to length-match. Standard CAA design, but revisit whether the extracted vector captures the axis vs the
    meta-stance before S5 extraction.
11. **[LOW-NEW] Registry stale-lock.** `.lock` sidecar (O_EXCL) has no stale-lock reaping; a crashed holder
    blocks writers until timeout. Harden before heavy parallel GPU-phase writes.
12. **[LOW-NEW] Conflict-probe calibration provenance (m3).** GPU phase must register the calibration run
    that sets prompt_target/latent_target poles as its own experiment_id feeding conflict_probe, else
    landing_fraction is silently biased by mis-estimated poles.

13. **[MED-NEW] Registry auto-writer drops the schema comment block.** The experiment-registry.yaml Python writer re-serializes the YAML from data on each run and DELETES the leading commented schema block (the `# - experiment_id: ...` template that test_matches_ledger_schema parses). Silently broke the test during the A/D GPU runs (restored manually, commit bad1266). HARDEN: make the writer preserve/re-emit the schema comment header, or move the schema to a separate tracked file the test reads. Until fixed, every registry write re-breaks it.

14. **[MED-NEW] Bilingual micro-study copy lacks human semantic review.**
    Automated stable-ID/numeric/polarity/modality/scope checks cannot establish
    that English and Simplified Chinese are pragmatically equivalent or equally
    understandable. Human bilingual stable-ID review is a PRE-RECRUITMENT gate;
    until then the implementation is owner-local preview only and not study
    evidence.
15. **[MED-NEW] Prior micro-study hostile audit does not cover bilingual commits
    through `d4ceafd`.** Automated material/API/export/browser/security gates pass, but
    the prior final audit was for monolingual commit `d17df47`. A fresh
    independent hostile audit is required before any readiness claim beyond
    `READY_FOR_OWNER_LOCAL_PREVIEW_NO_HUMAN_DATA`.
