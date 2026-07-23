# Open Risks (ranked)

1. **[HIGH] "This is NLP, not HCI" rejection.** Reviewers see steering mechanism as the core; HCI delta
   thin. Mitigation: interaction model + intent-expression-vacuum framing + controlled user study +
   design knowledge as moat. Owner: RQ2 framing.
2. **[HIGH] Scoop / insufficient increment.** Novelty gate rates scoop MED (charter said LOW). Huang&Lim
   (IASDR25 poster, SAE) is closest single-channel threat; Stolfo instruction-steering (ICLR25) cuts
   against C2; name-collision "Dual-Channel Steering" already coined. Mitigation: precise differentiation
   "non-surjective gap as interface object" vs "single-channel slider"; owed manual CHI'26/ACM-DL sweep.
7. **[HIGH-NEW] C2 theory over-application.** Mishra proves non-surjectivity of INTERNAL activations, not
   behavioral prompt-unreachability. C2 as written is not entailed by the cited theory — a hostile
   reviewer's sharpest attack. Mitigation: separate internal-state claim (theory-backed) from behavioral
   claim (must be empirically demonstrated, cannot be asserted from Mishra). Must fix before Charter Freeze.
8. **[MED-NEW] Citation framing errors.** SemanticLens/Labarta conflated + mis-modality (vision not LLM);
   ActAdd App-B sub-claim unverified [NEEDS EVIDENCE]. Fix before any text reuse.
3. **[HIGH] Effect fragility / mechanism.** Phase 0 may show steering changes only surface style, or
   axes non-linear/orthogonal → dual-channel "coordination" narrative collapses. Mitigation: Plan B
   (limit probe) / Plan D (measurement paper) fallbacks in Charter §8.
4. **[MED] Over-anthropomorphism / over-trust** from explanation panel. Mitigation: functional-dimension
   language; calibrated trust as first-class metric.
5. **[MED] Concurrency latency** breaks study validity. Mitigation: vLLM-Hook; cap concurrent users.
6. **[MED] Human-subjects/IRB + budget** not yet approved — blocks Formative + controlled study.
