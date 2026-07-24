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
8. **[MED-NEW] Citation framing errors.** **Partly resolved from existing docs:** SemanticLens/Labarta is
   corrected as **two distinct works**: Labarta et al. "From Attribution to Action" is documented in
   `docs/research/2026-07-23-novelty-falsification.md` and D-0003 as a **vision/CLIP, expert-debugging**
   tool (not an LLM latent UI for non-experts), while "SemanticLens" is a separate Fraunhofer HHI
   Nat.Mach.Intell.'25 artifact. **Still open:** ActAdd Appendix-B sub-claim remains **[NEEDS EVIDENCE]**;
   the available docs only verify that the specific exclusion-experiment claim was *not* checked at the
   section level, so do not cite App-B specifics until the primary PDF/appendix is read.
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
