# Manual Prior-Art Sweep · Non-Surjective Dual-Channel Cognitive Console

- **Date**: 2026-07-23
- **Agent**: INDEPENDENT Research subagent (no stake in the idea succeeding). Adversarial stance: *assume someone already published our idea and try to find them.*
- **Mandate**: `AGENTS.md` §6.1 + `AI-Instruction.md` Part I §5. Runs the **OWED MANUAL PRIOR-ART SWEEP** that the first novelty pass (`docs/research/2026-07-23-novelty-falsification.md`) explicitly deferred (it rated scoop **MEDIUM** and said a manual CHI / ACM DL / arXiv sweep was still owed — a gating task before Charter Freeze, per charter §4/§0).
- **Object under test**: the core novelty claim — *"We turn the non-surjective gap between prompt controllability and latent mechanism into a legible, operable, calibratable INTERFACE OBJECT — surfacing how much of an intended cognitive shift a prompt actually reaches, what the latent channel adds, and how a non-expert attributes, adjudicates, and re-calibrates trust when the two channels CONFLICT."*
- **Method / hygiene**: web_search returns **LLM-generated prose treated as UNTRUSTED leads**. Only artifacts confirmed against a primary source (arXiv abstract/HTML, ACM DL DOI, venue program page, author page, or the curated CHI'26 preprint list) are given a verdict. Where I could only see a title, I mark **UNVERIFIED-LEAD**. I distinguish *keyword overlap* from *mechanism/framing overlap*.
- **Relationship to first pass**: does NOT repeat it. First pass audited the 8 charter citations and scanned concurrent ML work. This pass does the manual **HCI-venue** sweep (CHI'26 program + CHI EA'26 + IUI/DIS + OpenReview/ICML) it deferred, and re-examines named near-neighbors for follow-up/concurrent work that closes our gap.

---

## 0. Headline (read first)

1. **No paper occupies our exact gap was found.** After a manual sweep of the CHI'26 accepted-paper / preprint corpus, CHI EA'26, IUI/DIS, ICML/ICLR/OpenReview, and ACM DL–indexed venues, **no artifact makes the prompt↔latent *divergence itself* an operable interface object with conflict attribution + trust re-calibration for non-experts.** The exact-gap **SCOOP risk is downgraded MEDIUM → LOW.**
2. **The "obvious combination" novelty risk is NOT a scoop and remains ~MEDIUM.** Huang & Lim (single latent channel + laypeople), AI-Instruments (prompt-only reification), Labarta (vision + experts), and now **Latent Manipulator (CHI EA'26)** each hold *one ingredient*; none combine them into our framing. The defense survives only if RQ1 facade-quantification and RQ2 prompt↔latent conflict are shown empirically (unchanged from first pass).
3. **The single most dangerous *newly surfaced* paper is "Steer Like the LLM" / PSR (ICML 2026).** It empirically argues activation steering can be trained to **match or exceed prompt steering behaviorally**. It is *not* a scoop (ML method, no interface, no users) but it directly attacks the load-bearing C2b behavioral-gap rhetoric — the same soft spot the first pass flagged (internal-state non-surjectivity ≠ behavioral unreachability). Must be cited and pre-empted.
4. **Recurrent tell:** every AI-search that was asked to describe "prompt-latent gap as an operable interface for non-expert trust/conflict" returned fluent prose calling it *"a cutting-edge active research area"* but could cite **only glossary pages (emergentmind topic pages), awesome-lists, and generic ML steering method papers** — never a built-and-studied HCI system. Soft corroboration that the interface-object gap is unoccupied.

---

## 1. Search log (auditable / reproducible)

All queries run 2026-07-23 via web_search (Bing-backed) + web_fetch on primary sources. Search targets map to the six mandated targets.

| # | Query (paraphrased) | Target | Primary sources actually opened/verified |
|---|---|---|---|
| Q1 | interface bridging prompt controllability & latent activation steering, dual-channel console for end users | T1,T2 | IBM/activation-steering (GitHub), arXiv:2606.08454, 2505.22572, aclanthology 2026.findings-acl.226 |
| Q2 | non-expert activation-steering interface user study, slider, prompt conflict, CHI/UIST/IUI | T2,T3 | arXiv:2606.11599 (ASTEER), icml.cc/virtual/2026/poster/66813 (PSR), arXiv:2605.10664 |
| Q3 | conflict resolution between text instruction & steering vector surfaced to users | T3 | neurips.cc/virtual/2025/133851, arXiv:2511.14342 (ConInstruct), microsoft/llm-steer-instruct |
| Q4 | trust calibration / mental-model repair for latent control by laypeople | T4 | arXiv:2603.22634 (Learning to Trust) |
| Q5 | "semantic facade" / how far a prompt reaches / projection onto steering direction surfaced to users | T5 | (no real artifact; only prompt-eng blog prose) |
| Q6 | CHI 2026 papers: LLM steering vectors, non-expert control panel, latent legibility | T6 | arXiv:2602.01654, chi2026.acm.org/authors/papers, **dbuschek CHI'26 preprint collection (manually scanned)** |
| Q7 | Huang & Lim feature-steering follow-up 2026, dual-channel prompt+latent user study | T6, near-nbr | dl.designresearchsociety IASDR2025/34, **arXiv:2602.04903 (Mind the Performance Gap, body read via ar5iv)** |
| Q8 | AI-Instruments / Riche direct-manipulation latent-steering follow-up CHI'26 attribution panel | T6, near-nbr | arXiv:2502.18736, chi2026.acm.org/accepted-panels, **media.mit.edu Latent Manipulator (CHI EA'26)** |
| Q9 | IUI 2026 / DIS 2025 activation-steering interface end users, representation engineering user study | T6 | dblp IUI 2025, sigchi.org/events/iui-2026, arXiv:2606.08682, 2606.04160 |
| Q10 | prompt-latent gap operable interface object, non-expert conflict, recalibrate trust, slider, OpenReview 2026 | T1–T5 | (no real artifact; emergentmind glossary + awesome-lists only) |

**Sources hit (venue-level):** ACM DL (DOI 10.1145/3772363.3798816), CHI'26 program & accepted-panels, CHI EA'26, D. Buschek CHI'26 preprint collection (full manual scan of the "Text/NLP", "Explainability/Perception", "Design Tools", "Co-creating", "Bots & Agents", "Infovis" sections), ICML 2026 virtual, NeurIPS 2025 virtual, arXiv listings, IASDR 2025 (DRS DL), dblp IUI, aclanthology.

---

## 2. Candidate table (verdicts + URLs)

Verdict key — **SCOOP** (occupies our exact gap) · **PARTIAL-OVERLAP** (shares ingredients, leaves framing open) · **NOT-A-SCOOP** (different problem) · **UNVERIFIED-LEAD** (title-level only).

| Candidate | Venue / Year | URL | What it does | Verdict |
|---|---|---|---|---|
| **Latent Manipulator** (Raval, Dunnell, Lippman) | **CHI EA'26** (poster/EA) | https://doi.org/10.1145/3772363.3798816 · https://www.media.mit.edu/publications/latent-manipulator-using-concept-guided-embedding-manipulation-to-steer-embedding-visualizations/ | Concept-guided manipulation of **embedding VISUALIZATIONS**: user types a concept → concept vector → re-weights embeddings → new UMAP map; slider amplifies/suppresses a concept to reorganize a *document corpus* view (e.g. CHI papers by method). | **NOT-A-SCOOP.** Steers a **data-viz projection**, not LLM generation/behavior. No prompt channel, no prompt↔latent conflict, no trust re-calibration, not about model control. Closest CHI'26 use of "latent + concept vector + slider" → **cite to differentiate**. |
| **Steer Like the LLM / Prompt Steering Replacement (PSR)** | **ICML 2026** (poster 66813) | https://icml.cc/virtual/2026/poster/66813 | Trains activation-steering coefficients to **imitate prompt steering**; reports PSR "achieves performance close to or exceeding prompt steering while maintaining interpretability" (persona + instruction-following). | **NOT-A-SCOOP** (ML method, no UI/users) **but THEORY-DANGEROUS**: argues steering≈prompting behaviorally → attacks C2b "prompts hit a wall the slider crosses." **Most dangerous newly-surfaced paper.** |
| **Mind the Performance Gap: Capability-Behavior Trade-offs in Feature Steering** | arXiv 2026 (2602.04903) | https://arxiv.org/abs/2602.04903 | LLM-judge (Likert-criteria) eval showing feature steering shifts *behavior* while degrading *capability/coherence* vs prompting. | **NOT-A-SCOOP** (ML eval, no interface). **PARTIAL** relevance: empirically supports our "steering changes surface style, not reasoning" kill-criterion + facade framing → cite. |
| **When is Your LLM Steerable? (ASTEER)** | arXiv 2026 (2606.11599) | https://arxiv.org/abs/2606.11599 | Steerability testbed, 1.4M steered generations / 150 traits; predicts steering success from initial state. | **NOT-A-SCOOP** (ML testbed). Useful baseline/axis-selection reference. |
| **Prompt-Activation Duality** | arXiv 2026 (2605.10664) | https://arxiv.org/abs/2605.10664 | Improves activation steering via attention-level interventions. | **NOT-A-SCOOP** (ML method). Keyword "duality" ≠ our framing. |
| **ConInstruct: Evaluating LLMs on Conflict Detection & Resolution** | arXiv 2025 (2511.14342) | https://arxiv.org/abs/2511.14342 | Benchmark: do LLMs detect/resolve **conflicting constraints within an instruction**; note they rarely surface conflict to users. | **NOT-A-SCOOP.** Conflict is *text-constraint vs text-constraint*, model-internal — NOT prompt-channel vs latent-vector surfaced to a human. Different "conflict." Cite to sharpen our conflict definition. |
| **Who is In Charge? Dissecting Role Conflicts in LLM Instruction Hierarchy** | NeurIPS 2025 | https://neurips.cc/virtual/2025/133851 | How models resolve system-vs-user instruction conflicts internally; steering can amplify compliance. | **NOT-A-SCOOP** (ML/interp, no UI). System↔user prompt conflict ≠ prompt↔latent conflict for users. |
| **Learning to Trust: How Humans Mentally Recalibrate AI Confidence Signals** | arXiv 2026 (2603.22634) | https://arxiv.org/html/2603.22634v1 | Behavioral study + Rescorla–Wagner model of laypeople recalibrating trust in AI **confidence signals** over exposure. | **NOT-A-SCOOP** (no steering / no latent). **PARTIAL** — a trust-recalibration *method/measure* we can borrow for our calibrated-trust metric. |
| **Who Controls the Conversation? User Perspectives on LLM System Prompts** | CHI'26 preprint (2603.00089) | https://arxiv.org/abs/2603.00089 | Users' perceptions of/control over **system prompts**. | **NOT-A-SCOOP.** Prompt-layer control perceptions; no latent channel. **PARTIAL** framing neighbor on "who controls." |
| **Beyond Anthropomorphism: A Spectrum of Interface Metaphors for LLMs** | CHI'26 preprint (2603.04613) | https://arxiv.org/abs/2603.04613 | Design metaphors for LLM interfaces. | **NOT-A-SCOOP.** Framing-adjacent (boundary-object/metaphor), no steering/latent. |
| **Steering Vector Fields** | arXiv 2026 (2602.01654) | https://arxiv.org/abs/2602.01654 | Context-dependent steering directions (ML robustness). | **NOT-A-SCOOP** (ML method). |
| **Textual Steering Vectors Improve Visual Understanding in MLLMs** | ACL 2026 (2026.acl-long.1861) | https://aclanthology.org/2026.acl-long.1861/ | Cross-modal steering-vector method. | **NOT-A-SCOOP** (ML method). |
| **Expert-Aware Refusal Steering** (2606.04160), **Activation Steering Induces Emergent Misalignment** (2606.08682), **INNSteer** (2606.08454), **Fusion Steering** (2505.22572), **RISER** (2026.findings-acl.226) | arXiv/ACL 2025–26 | see IDs | Steering *methods*/safety analyses. | **NOT-A-SCOOP** (ML material, no interface). Corpus context only. |
| "Dual-Channel Steering" (prompt vs Text-to-LoRA) | ICLR 2026 WS | https://openreview.net/pdf?id=bEc9slMJ8k | (from first pass) name-collision, ensemble reasoning method. | **NOT-A-SCOOP** but **name collision** → rename our paradigm. |

---

## 3. Closest 3 works & precise differentiation

1. **Huang & Lim, "Designing Intuitive Interfaces for Feature Steering of LLMs" (IASDR 2025 poster)** — *still the strongest scoop-adjacent work.* They give **laypeople** a slider GUI over **SAE features** (Goodfire Ember, Llama-3.1-8B) to build personas, with formative+summative testing. **Our delta:** they expose a **single latent channel** — no text-prompt channel co-present, no prompt↔latent conflict, no quantified "what fraction of the intended shift the prompt reaches" (semantic facade), no trust re-calibration on disagreement. If our study degrades to "we put a prompt box next to their sliders," we are an obvious combination. This is the empirical burden, unchanged from first pass; the manual sweep found **no follow-up by them** that adds the prompt channel or conflict.

2. **Latent Manipulator (Raval, Dunnell, Lippman, CHI EA'26)** — *the newest, most surface-similar HCI artifact.* Same vocabulary (latent, concept vector, slider, "steer"), a real CHI-family venue, MIT Media Lab. **Our delta:** it steers an **embedding-visualization layout of a document corpus** for sensemaking — it does **not control an LLM's generative behavior**, has **no prompt channel**, no conflict, no trust calibration, no non-surjectivity framing. Keyword overlap only; different problem class (data viz vs behavior control). Must cite to pre-empt "isn't this Latent Manipulator?"

3. **"Steer Like the LLM" / PSR (ICML 2026)** — *the most dangerous newly-surfaced paper for our core claim.* Not a scoop (no UI/users), but it operationalizes the exact counter-thesis to RQ2/C2b: activation steering trained to **mimic prompting** reaches **"performance close to or exceeding prompt steering."** A CHI reviewer can weaponize it (as with Stolfo) to say "the behavioral gap you sell is closable — steering and prompting converge." **Differentiation:** our claim must be scoped to (a) *internal-state* non-surjectivity (Mishra, proven) + (b) a *specific empirically-demonstrated behavioral compliance-floor region* under a *bounded* prompt search — NOT a general "prompts can't do what sliders do." PSR strengthens, not weakens, the first pass's demand to fix the internal-vs-behavioral wording.

---

## 4. Final scoop verdict

- **Exact-gap SCOOP (someone built prompt↔latent-divergence-as-operable-interface-object with conflict attribution + trust re-calibration for non-experts): LOW.** Downgraded from the first pass's MEDIUM. Justification: a genuine manual sweep of the CHI'26 program + preprint corpus, CHI EA'26, IUI/DIS, ICML/ICLR/OpenReview, and ACM DL returned **zero** artifacts occupying the gap; the nearest HCI works each hold exactly one ingredient; AI-search could not name a single real system despite repeated adversarial prompting.
- **Overall "obvious-combination" novelty risk (a defensibility risk, NOT a scoop): MEDIUM (unchanged).** The ingredients are all published; the paper lives or dies on empirically exhibiting (i) a quantified semantic facade surfaced to users and (ii) genuine prompt↔latent conflict phenomena non-experts must resolve.
- **Single most dangerous paper:** for *scoop* — **none found** (nearest scoop-adjacent = Huang & Lim, IASDR'25). For the *core claim* — **"Steer Like the LLM" / PSR (ICML 2026)**, which threatens the C2b behavioral-gap thesis by showing steering can be trained to match prompting.

---

## 5. Recommendation to the Manager

**PROCEED, with a narrowed framing.** Concretely:

1. **Anchor novelty on the triad, not on any single lever:** (prompt↔latent *conflict attribution*) + (*quantified* semantic-facade surfaced to users) + (*trust re-calibration on disagreement*), for **non-experts**. Drop any framing reducible to "layperson steering sliders" (Huang & Lim) or "latent slider" (Latent Manipulator).
2. **Fix the load-bearing wording BEFORE freeze** (reinforced by PSR): separate *internal-state* non-surjectivity (Mishra, proven) from *behavioral* unreachability (C2b, must be empirically shown on a bounded-prompt-search compliance floor). Do not lean the headline on "prompts can't reach it."
3. **Rename "Dual-Channel Steering"** — collides with ICLR'26 WS term; risks reviewer déjà vu.
4. **Add to `citation-map` / related work (must cite to differentiate):** Latent Manipulator (CHI EA'26), PSR/"Steer Like the LLM" (ICML'26), Mind the Performance Gap (2602.04903), ConInstruct (2511.14342), Who is In Charge? (NeurIPS'25), Learning to Trust (2603.22634), Who Controls the Conversation? (CHI'26).
5. **This gating task is satisfiable:** the owed manual sweep is done; scoop clears to LOW. Recommend marking charter §0 gate (2) "owed prior-art sweep" **CLEARED** in the next Manager decision-log entry, contingent on the wording fixes above.

---

## 6. Honest caveats & queries I could NOT run

1. **CHI'26 program is only ~complete via preprints.** Not every accepted CHI'26 paper has a public preprint; the D. Buschek collection is curated/subjective and may miss a paper whose authors did not tag "CHI 2026" on arXiv. A non-preprinted CHI'26 paper occupying our gap cannot be fully excluded. **Residual risk: low but nonzero.**
2. **No authenticated ACM DL full-text search.** I verified specific DOIs (e.g., Latent Manipulator) but could not run a broad boolean full-text ACM DL query behind the paywall; relied on venue programs + Google/Bing indexing. A paper indexed only in ACM DL full text (not title/abstract) could be missed.
3. **UIST 2025 not exhaustively swept** (charter excludes UIST as a venue, but a UIST paper could still *scoop* us). I did not open the full UIST'25 program; first pass + this pass surfaced none, but this is an acknowledged gap.
4. **arXiv export API returned HTTP 429** during this session, so a few abstracts were verified via ar5iv/venue pages/author pages instead of the canonical API. Titles/venues cross-checked, but re-confirm via arXiv API before these enter the paper's bibliography (esp. 2602.04903, 2606.11599, 2605.10664 — body-level claims only spot-checked).
5. **Several web_search bodies were LLM hallucination** (e.g., invented "trust steering slider"/"steering dashboard" papers citing only glossary pages; a fabricated "ASTEER user study"). All such prose was discarded; only primary-source-confirmed artifacts appear above. Treat any candidate here without an opened primary URL as **UNVERIFIED-LEAD**.
6. **DIS 2025 / IUI 2026 checked only at program/CFP level**, not full proceedings scan; no candidate surfaced, but coverage is shallower than for CHI.
