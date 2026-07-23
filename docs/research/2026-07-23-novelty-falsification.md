# Novelty-Falsification Report · Non-Surjective Dual-Channel Cognitive Console

- **Date**: 2026-07-23
- **Agent**: INDEPENDENT Research / Novelty-Falsification subagent (no stake in this idea succeeding)
- **Mandate**: `AGENTS.md` §6.1 + `AI-Instruction.md` Part I §5 (Novelty Gate & Citation Verification)
- **Object under test**: `docs/charter/project-charter.md` v0.1 (DRAFT) + `开题报告_非满射双通道认知控制台.md`
- **Method**: Every factual claim is tied to a checkable URL. Citations verified against the **arXiv official export API** and primary venue pages, not AI-search prose (AI-search summaries were treated as untrusted leads and independently confirmed).
- **Stance**: Goal is to FALSIFY the claimed novelty, not support it. Construct the strongest scoop/novelty objection a skeptical CHI reviewer would make.

> **Core novelty claim being stress-tested:** *"We turn the non-surjective gap between prompt controllability and latent mechanism into a legible, operable, calibratable INTERFACE OBJECT — an interaction model + design knowledge for latent-controllability UIs, NOT another steering method or slider."*

---

## 0. Headline findings (read this first)

1. **The load-bearing theoretical citation is REAL and correctly quoted.** Mishra, Khashabi & Liu, *Steered LLM Activations are Non-Surjective*, arXiv:2604.09839 (v2), ICLR 2026 Workshops (Sci4DL, Re-Align), published 2026-04-10, is genuine. The abstract verbatim supports "activation steering pushes the residual stream off the manifold of states reachable from discrete prompts... Almost surely, no prompt can reproduce the same internal behavior induced by steering." **RQ2's theoretical basis does NOT collapse — the paper exists and says what the charter says it says.** Source: https://arxiv.org/abs/2604.09839 (verified via https://export.arxiv.org/api/query?id_list=2604.09839).

2. **BUT there is a critical over-application** (the single biggest substantive concern). Mishra proves non-surjectivity of the **internal residual-stream activation**, i.e. *no prompt reproduces the same internal state*. The charter's testable Claim **C2** ("prompt-only cannot cross a control threshold that the latent channel can") is a claim about **observable output behavior / task performance**, which is strictly weaker and NOT entailed by Mishra: two different internal states can yield the same behavior. The theoretical foundation is real but is being stretched from an internal-state result to a behavioral-reachability value proposition. This is the most exploitable gap for a hostile reviewer/auditor.

3. **All 8 audited citations VERIFIED** (title/authors/year/venue). None fabricated. Two have minor mis-framings (SemanticLens modality; RQ1 corollary status). Details in §2.

4. **Scoop risk: MEDIUM** (the charter's own 3.1 table rates the core gap "低/LOW" — I disagree; it is at least MED). The individual ingredients are all taken and there are direct name-collisions; the specific *framing* (gap-as-object + prompt↔latent conflict + quantified semantic facade + non-experts) is not yet occupied. See §3–§4.

---

## 1. Nearest-neighbor matrix (≥5 works)

Delta column states the *precise* differentiator and, critically, whether we are an **obvious combination / trivial variation / mathematically equivalent / already-evaluated-under-another-name**.

| # | Work (verified) | Objective | Mechanism | Interaction model | Precise delta / falsification angle |
|---|---|---|---|---|---|
| 1 | **AI-Instruments** — Riche, Offenwanger, Gmeiner et al., CHI 2025, arXiv:2502.18736 | Reify prompts into reusable direct-manipulation "instruments" for AI-assisted design | Pure prompt-layer; LLM suggests/varies instruments | Direct manipulation of prompt objects (reification / reflection / grounding); image gen; N=12 | **Delta:** they stay entirely at the prompt layer; we push control to latent and use non-surjectivity to argue *why* prompt-layer instruments hit a ceiling. **Risk:** reviewer says our "attribution panel" is AI-Instruments' reflection principle re-skinned. Delta is real (latent channel + facade) but the *interaction philosophy* is a recognizable descendant. |
| 2 | **Huang & Lim** — *Designing Intuitive Interfaces for Feature Steering of LLMs*, IASDR 2025 (poster paper, DOI 10.21606/iasdr.2025.601) | Make feature steering usable by laypeople | SAE features via **Goodfire Ember API** (Llama 3.1 8B) — NOT CAA/RepE | Simplified GUI, slider-driven **persona building**; 2-phase user-centered design + formative/summative testing | **Highest single-channel threat.** They already did "layperson steering sliders + user study." **Our only defensible delta:** they expose a *single latent channel* (no prompt-vs-latent conflict, no quantified "what % of the intended direction a prompt reaches", no trust re-calibration on disagreement). If our study collapses to "we added a prompt box next to their sliders," we are an **obvious combination**. Mitigant: it is a *poster* (lower archival weight) and uses SAE features not steering vectors. |
| 3 | **From Attribution to Action / SemanticLens** — Labarta et al. (Fraunhofer HHI), CVPR 2026 Workshop (XAI4CV), arXiv:2604.11467 (v2) | Make XAI explanations actionable via steering | SAE-based attribution + activation steering, web tool | Expert **debugging**; semi-structured interviews **N=8 on CLIP** | **Charter mis-frames this** (see §2): it is a **vision/VLM** tool for **experts**, not an LLM cognitive-axis tool. Delta is genuinely large (modality + expert-vs-nonexpert + debugging-vs-intent-expression). *This reduces scoop risk but the charter must correct the "SemanticLens = LLM latent UI" implication.* Also note the "trust grounded in observed responses" finding (6/8) partially pre-empts our RQ1 trust angle. |
| 4 | **The Metacognitive Demands of Generative AI** — Tankelevitch, Kewenig, Simkute et al., CHI 2024, arXiv:2312.10893, DOI 10.1145/3613904.3642902 | Frame GenAI usability as metacognitive monitoring/control burden | Conceptual/theory (psychology lens) | No system; recommends explainability + customizability | **Delta:** this is our theory base, not a competitor. **Risk:** reviewer says our contribution is "an instantiation of Tankelevitch's already-published recommendation to add explainability + customizability" — i.e. predicted, not novel. We must show the *latent* legibility + conflict phenomena are non-obvious beyond the framework. |
| 5 | **CAA** — Rimsky (Panickssery), Gabrieli, Schulz et al., *Steering Llama 2 via Contrastive Activation Addition*, ACL 2024 (Outstanding Paper), arXiv:2312.06681 | Steer high-level behaviors (sycophancy, truthfulness) | Mean-difference contrastive activation vector added to residual stream | None (method paper, CLI) | **Delta:** pure material/engine; we make no steering-method claim. No novelty conflict — but also gives us no HCI credit; it is the "this is NLP not HCI" attack surface. |
| 6 | **ActAdd / Activation Engineering** — Turner, Thiergart, Leech et al., arXiv:2308.10248 | Inference-time output control | Contrast-pair steering vector | None | **Delta:** material + non-surjectivity side-evidence. The charter's specific "Appendix B exclusion experiment" claim is **UNVERIFIED at the section level** (see §2). |
| 7 | **Instruction-Following via Activation Steering** — Stolfo et al., ICLR 2025, arXiv:2410.12877 (`microsoft/llm-steer-instruct`) | Improve instruction following | Instruction steering vectors (with/without-instruction diff), composable, transfer to base models | None | **Delta / danger:** this is the closest *mechanism* paper to RQ2 — it already shows natural-language instructions correspond to composable internal vectors and that steering does things prompts encode. A reviewer can use it to *attack* our "prompt can't reach it" story ("Stolfo shows instruction↔vector correspondence — so how non-surjective is it behaviorally?"). Cuts against C2. |
| 8 | **Harnessing the Latent Space: From Steering Vectors to Model Calibrators for Control and Trust** — Subramani, ACL 2026 BigPicture Workshop, arXiv:2607.00083 | "Steering for control + latent calibrators for trust" | Steering vectors + latent-space calibrators | None (position/summary paper, single author, ML) | **Concurrent (2026-06-30).** Same *theme words* ("steering", "control", "trust") but no interface, no user study, no non-expert framing, no prompt↔latent conflict. Not a scoop of the interface-object contribution, but shows "steering+trust" is now a crowded phrase. |

---

## 2. Citation-verification table

Verdict key: **VERIFIED** (exists; title/authors/year/venue match; core claim supported by primary text) · **MISSTATED** (exists but charter mischaracterizes it) · **UNVERIFIABLE** (could not confirm a specific sub-claim) · **LIKELY-FABRICATED**.

| Citation (as used in charter/开题) | Verdict | Evidence (checkable URL) | Notes |
|---|---|---|---|
| **Mishra, Khashabi & Liu, "Steered LLM Activations are Non-Surjective", arXiv:2604.09839, ICLR 2026 Workshops** | **VERIFIED** | https://arxiv.org/abs/2604.09839 · API: https://export.arxiv.org/api/query?id_list=2604.09839 | v2, published 2026-04-10, comment "ICLR 2026 Workshops (Sci4DL, Re-Align)". Authors exact: Aayush Mishra, Daniel Khashabi, Anqi Liu. Abstract verbatim confirms the non-surjectivity/off-manifold/"no prompt can reproduce the same internal behavior" claim. **Caveat (not a citation error, an application error): claim is about internal activations, not output behavior — see §0.2 & §5 RQ2.** |
| **AI-Instruments (Riche et al., CHI 2025, arXiv:2502.18736)** | **VERIFIED** | https://arxiv.org/abs/2502.18736 | v1 2025-02-26; comment confirms "To appear in Proceedings of the 2025 ACM CHI". First author Nathalie Riche. Charter's "Riche et al." and characterization accurate. |
| **Huang & Lim, "Designing Intuitive Interfaces for Feature Steering of LLMs" (IASDR 2025)** | **VERIFIED** (with weight caveat) | https://dl.designresearchsociety.org/iasdr/iasdr2025/posterpapers/34/ · DOI https://doi.org/10.21606/iasdr.2025.601 | Confirmed real, IASDR 2025 **poster paper**, Track 4 Human-Centered AI. Uses Goodfire Ember API / Llama 3.1 8B; persona use case; code `github.com/acyhuang/steering-interface`. Charter should label it a *poster* (lower archival standing) and note it steers **SAE features**, not CAA/RepE vectors. |
| **SemanticLens / "From Attribution to Action" (Labarta et al., 2026)** | **MISSTATED** (paper real; framing wrong) | https://arxiv.org/abs/2604.11467 · CVPR: https://openaccess.thecvf.com/content/CVPR2026W/XAI4CV/html/Labarta_From_Attribution_to_Action_A_Human-Centered_Application_of_Activation_Steering_CVPRW_2026_paper.html | *From Attribution to Action* (arXiv:2604.11467, CVPR 2026 W, N=8 expert interviews) is about **vision models (CLIP)**, not LLMs. "SemanticLens" is a *separate* Fraunhofer HHI artifact (Nature Machine Intelligence 2025: https://www.hhi.fraunhofer.de/en/press/news/2025/nature-machine-intelligence-publishes-fraunhofer-hhi-study-on-semanticlens.html). Charter bundles two works under one label and implies an LLM latent-UI competitor. Correct before freeze. |
| **Tankelevitch et al., "Metacognitive Demands...", CHI 2024, arXiv:2312.10893** | **VERIFIED** | https://arxiv.org/abs/2312.10893 · DOI 10.1145/3613904.3642902 | Full title "The Metacognitive Demands and Opportunities of Generative AI"; journal_ref "CHI 2024". Authors/venue exact. |
| **CAA (Rimsky et al., ACL 2024)** | **VERIFIED** | https://aclanthology.org/2024.acl-long.828/ · arXiv:2312.06681 | Title "Steering Llama 2 via Contrastive Activation Addition"; ACL 2024 long paper 15504–15522; Outstanding Paper. Note first author is now often listed as Nina Panickssery (née Rimsky) — cite consistently. |
| **ActAdd (Turner et al., arXiv:2308.10248)** | **VERIFIED** (paper) / **UNVERIFIABLE** (Appendix B sub-claim) | https://arxiv.org/abs/2308.10248 | Title "Steering Language Models With Activation Engineering", Turner et al., v5. The paper is real. The 开题's specific claim about *"Appendix B exclusion experiment showing embedding-injection is weak but post-layer activation-diff is strong + perplexity degradation asymmetry"* was **NOT verified against the paper body** in this pass — flag as [NEEDS EVIDENCE] before it appears in the paper. |
| **Stolfo et al. instruction steering (ICLR 2025)** | **VERIFIED** | https://arxiv.org/abs/2410.12877 · https://proceedings.iclr.cc/paper_files/paper/2025/... | Title "Improving Instruction-Following in Language Models through Activation Steering"; ICLR 2025; code `microsoft/llm-steer-instruct`. Composability + base-model transfer confirmed. |

**No fabricated citations found.** The most epistemically important line: the Mishra paper — flagged in the mandate as "if not real, whole RQ2 basis collapses" — **is real and accurately quoted.** (See §0.2 for the real, subtler risk.)

---

## 3. Concurrent / very-recent work scan (2025–2026) — the scoop we most fear

Searched for anyone already treating the prompt↔latent gap / conflict resolution / dual-channel latent UI for non-experts as an *interface object*. Verified items only:

| Work | Verdict on scoop | Evidence |
|---|---|---|
| **"Dual-Channel Steering: Combining Explicit Prompting and Implicit Parameter Modulation for Reasoning Diversity"** (ICLR 2026 "Latent & Implicit Thinking" workshop) | **Name-collision, NOT a substantive scoop.** Uses the *exact* term "Dual-Channel Steering" but the two channels are prompt vs **Text-to-LoRA parameter modulation**, and the objective is **ensemble reasoning accuracy via majority vote** — an ML method, no interface, no users, no conflict-attribution, no trust. **Risk: naming confusion + reviewer déjà vu.** Consider renaming our paradigm. | https://iclr.cc/virtual/2026/10016667 · https://openreview.net/pdf?id=bEc9slMJ8k |
| **Harnessing the Latent Space (Subramani, ACL 2026 W, arXiv:2607.00083)** | Theme overlap ("steering + trust"), no interface/user study. Not a scoop. | https://arxiv.org/abs/2607.00083 |
| **From Attribution to Action (Labarta, CVPR 2026 W, arXiv:2604.11467)** | Closest *interactive steering + trust + user study*, but **vision/expert**. Partial pre-emption of the "trust grounded in observed responses" finding; different modality/population. | https://arxiv.org/abs/2604.11467 |
| **"Prompt-Activation Duality: Improving Activation Steering via Attention-Level Interventions" (arXiv:2605.10664)** | Surfaced in search; **title-level only, not independently verified in this pass.** Title implies an ML steering-method paper (attention-level interventions), not an HCI interface. Flag as a lead to verify, not a confirmed neighbor. | https://arxiv.org/abs/2605.10664 (unconfirmed content) |

> ⚠️ **Search-hygiene note:** Several AI-search summaries fabricated CHI/UIST 2025–26 papers and a "Kang et al. 2026" quote that I could not tie to any real artifact. Those were discarded. Only arXiv-API/venue-confirmed items appear above. The absence of a confirmed HCI-venue prompt↔latent-gap-as-object paper is *encouraging but not proof of clear field* — a targeted ACM DL / CHI'26 program sweep is still owed before Protocol Freeze (CHI'26 program: https://programs.sigchi.org/chi/2026/program).

---

## 4. Strongest scoop / novelty objection (steel-manned CHI reviewer)

> *"This is an obvious combination of published parts. Huang & Lim (IASDR 2025) already gave laypeople steering sliders with a user study. Labarta et al. (CVPR 2026 W) already built an interactive attribution→steering tool, ran it with users, and reported that trust gets grounded in observed responses. AI-Instruments (CHI 2025) already reified control as direct-manipulation interface objects. Tankelevitch et al. (CHI 2024) already told us GenAI usability is a metacognitive problem needing explainability + customizability. The authors bolt a prompt box next to Huang & Lim's sliders, add Labarta's attribution panel (now for text instead of CLIP), wrap it in Tankelevitch's framing, and cite Mishra for theoretical gravitas. Worse, 'dual-channel steering' is already a coined term (ICLR 2026 W). Where is the non-obvious interaction insight that could not be predicted from these five papers? And the cited theoretical foundation (Mishra) proves non-surjectivity of internal activations, not that any user-relevant behavior is unreachable by prompting — so even the headline 'prompts hit a wall the sliders cross' is not established by the theory you lean on."*

**Most defensible rebuttal (one sentence):** *No prior system makes the **prompt↔latent divergence itself** the operable interface object — surfacing, in one coordinate system, how much of an intended cognitive shift a user's own prompt actually reaches, what the latent channel adds beyond it, and how a non-expert attributes, adjudicates, and re-calibrates trust when the two channels **conflict** — a phenomenon none of Huang & Lim (single latent channel), Labarta (single channel, vision, experts), or AI-Instruments (prompt-only) studies.* This survives **only if** the empirical facade-quantification (RQ1) and the prompt↔latent conflict behavior (RQ2) are shown to be real and non-trivial; otherwise it degrades to "we added a second slider."

---

## 5. Per-RQ risk rating

| RQ | Risk | Justification | Cheapest de-risking move |
|---|---|---|---|
| **RQ1 — semantic facade / epistemic mismatch** | **MED–HIGH** | The *phenomenon* (a readable prompt under-reaches a steering direction) is close to a corollary of Mishra + ActAdd, and end-user prompt-misunderstanding is heavily covered (Why Johnny Can't Prompt; Tankelevitch). Novelty rests entirely on operationalizing it as a **user-facing, trust-mis-calibrating measure** — the charter itself flags RQ1 as most coverable. | Pre-register the "semantic facade" as a *quantified projection metric surfaced to users* and show it changes trust behavior — not just that the projection is <100% (which is near-assumed). |
| **RQ2 — non-surjective control + conflict resolution (CORE)** | **MED** | Strongest, least-occupied framing (no one studies non-expert attribution when prompt & latent conflict). **But** the theoretical foundation is over-applied: Mishra = internal-state non-surjectivity; C2 = behavioral unreachability. Stolfo (instruction↔vector correspondence) can be weaponized against the behavioral gap. | (a) Re-word C2/theory link to separate "internal-state" (proven) from "behavioral/task" (to be empirically demonstrated, not assumed). (b) Empirically exhibit at least one task with a genuine prompt-unreachable *behavioral* region (compliance floor). |
| **RQ3 — boundary object / cross-model trust** | **MED–HIGH (feasibility, not scoop)** | Novelty is fairly clear (few study latent-lever trust continuity across a backend swap). Risk is engineering (cross-model dose-response re-mapping) and study power, not being scooped. | Keep as extension/ablation as charter already scopes; do not let it gate the main contribution. |

**Overall scoop risk: MEDIUM.** (Charter §3.1 rates the core gap "LOW"; downgrade-to-honest is MED given the density of adjacent 2025–26 work and the name collision.)

---

## 6. Honest caveats / still-unverified differences

1. **Internal-state vs behavioral non-surjectivity (highest priority).** Mishra is real and correctly quoted, but it does not entail the console's behavioral value proposition. Every place the charter/开题 slides from "no prompt reproduces the internal state" to "prompt can't achieve the outcome, the slider can" is an **unearned inference** an auditor will flag. Fix wording before Charter Freeze.
2. **Huang & Lim delta is thin on paper.** Until we can point to the *specific* interaction phenomena (conflict attribution, facade quantification) that they demonstrably do not have, the "obvious combination" charge lands. This is the biggest empirical burden.
3. **SemanticLens/Labarta framing must be corrected** — it is vision + experts, and "SemanticLens" ≠ "From Attribution to Action." Do not let the paper imply an LLM latent-UI competitor was pre-empted (it reduces our threat, so honesty helps us).
4. **ActAdd Appendix B side-evidence is [NEEDS EVIDENCE].** The specific exclusion-experiment claim was not verified at the section level; do not cite specifics until read in the primary PDF.
5. **Field-clear claim is not proven.** No confirmed HCI-venue prompt↔latent-gap-as-object paper was found, but AI search hallucinated several, and a manual ACM DL / CHI'26 sweep has not been done. Treat "gap is open" as *provisional*.
6. **"Dual-channel" naming.** A published ICLR 2026 workshop paper owns "Dual-Channel Steering" for a different (ML ensemble) meaning. Consider a distinct name to avoid reviewer confusion and self-inflicted prior-art collision.

---

## 7. Verdict for the Manager

- **Citation integrity:** PASS (8/8 exist; 0 fabricated; 1 misstated framing [Labarta], 1 sub-claim unverified [ActAdd App. B], 1 weight caveat [Huang & Lim poster]).
- **Theoretical foundation (Mishra):** REAL and accurately quoted — RQ2 does **not** collapse — **but over-applied** from internal-state to behavioral reachability. Requires charter wording fix, not abandonment.
- **Novelty:** Defensible but **MED** scoop risk, not LOW. Survives only if RQ1 facade-quantification and RQ2 conflict phenomena are empirically real and non-trivial. Recommend: (i) fix the internal-vs-behavioral wording, (ii) correct the Labarta framing, (iii) rename "dual-channel", (iv) run the owed manual CHI'26/ACM-DL prior-art sweep, before Charter Freeze.
