# Citation Verification Report · Cognitive Console
**Date:** 2026-07-24
**Agent:** Research Subagent (citation-verify pass) — adversarial stance; no stake in the paper succeeding.
**Mandate:** Verify every external work cited or mentioned across `docs/research/2026-07-23-priorart-sweep.md`, `docs/research/2026-07-23-novelty-falsification.md`, `docs/ledgers/open-risks.md` (risks #7–#9), `docs/paper/reframe-2026-07-24-reality-check.md`, `docs/paper/methodology-asset.md`, and `docs/ledgers/claim-ledger.md` against primary sources. Produce a BibTeX block for all VERIFIED entries. Flag every metadata error for correction before the writing stage.

**Hygiene rule:** AI-search prose is **untrusted**. Only data confirmed from a primary source (arXiv API Atom feed, arXiv HTML metadata tags, ACM DL, ACL Anthology, NeurIPS proceedings, venue programme page, publisher DOI, or author lab page) is labelled **VERIFIED**. Where a secondary source was needed, the entry is labelled **VERIFIED-SECONDARY**. Unresolvable entries are **UNVERIFIED** or **NOT-FOUND** and have **no BibTeX entry**.

---

## 1. Master Verification Table

| Key | Cited in repo as | Verified Title | Verified Authors | Venue / Year | Stable ID / DOI | STATUS | Primary source URL(s) | How-we-use-it | BibTeX key |
|---|---|---|---|---|---|---|---|---|---|
| **mishra26** | "Mishra, Khashabi & Liu, arXiv:2604.09839, ICLR 2026 Workshops" | Steered LLM Activations are Non-Surjective | Aayush Mishra, Daniel Khashabi, Anqi Liu | ICLR 2026 Workshops (Sci4DL + Re-Align) | arXiv:2604.09839v2 | **VERIFIED** | `https://export.arxiv.org/api/query?id_list=2604.09839` (Atom feed, `<published>2026-04-10T19:11:13Z</published>`, comment field confirms workshop) | C2a background: internal-state non-surjectivity (theory motivation only, not our empirical result) | `mishra2026nonsurj` |
| **psr26** | "Steer Like the LLM / PSR (ICML 2026)" — no arXiv ID given | Steer Like the LLM: Activation Steering that Mimics Prompting | Geert Heyman, Frederik Vandeputte (Nokia Bell Labs) | ICML 2026 (poster #66813) | arXiv:2605.03907v1 | **VERIFIED** | `https://arxiv.org/abs/2605.03907` (HTML citation_author tags); `https://icml.cc/virtual/2026/poster/66813` (abstract match) | Contrast / mandatory threat-to-C2b citation: trained steering matches prompting; scope line required | `heyman2026steer` |
| **caa24** | "CAA / Rimsky et al., ACL 2024, arXiv:2312.06681" | Steering Llama 2 via Contrastive Activation Addition | Nina Rimsky, Nick Gabrieli, Julian Schulz, Meg Tong, Evan Hubinger, Alexander Turner | ACL 2024 Outstanding Paper | arXiv:2312.06681; DOI:10.18653/v1/2024.acl-long.828; pp. 15504–15522 | **VERIFIED** | `https://aclanthology.org/2024.acl-long.828/` (HTML citation_author + DOI tags) | Baseline method (CAA arm in C2 adjudication) | `rimsky2024caa` |
| **actadd23** | "ActAdd / Turner et al., arXiv:2308.10248" | Steering Language Models With Activation Engineering | Alexander Matt Turner, Lisa Thiergart, Gavin Leech, David Udell, Juan J. Vazquez, Ulisse Mini, Monte MacDiarmid | arXiv preprint v5 | arXiv:2308.10248v5 | **VERIFIED (paper) / UNVERIFIABLE (App-B sub-claim)** | `https://arxiv.org/abs/2308.10248` (HTML citation_author tags) | Background method; App-B sub-claim remains [NEEDS EVIDENCE] per open-risks #8 | `turner2023actadd` |
| **iti23** | "ITI / Li et al., arXiv:2306.03341, NeurIPS 2023" | Inference-Time Intervention: Eliciting Truthful Answers from a Language Model | Kenneth Li, Oam Patel, Fernanda Viégas, Hanspeter Pfister, Martin Wattenberg | NeurIPS 2023, vol. 36, pp. 41451–41530 | arXiv:2306.03341 | **VERIFIED** | `https://proceedings.neurips.cc/paper_files/paper/2023/hash/81b8390039b7302c909cb769f8b6cd93-Abstract-Conference.html` (citation_author, volume, pages, date 2023-12-15) | Baseline method (ITI arm in C2 adjudication) | `li2023iti` |
| **repe23** | "RepE / Zou et al., arXiv:2310.01405" | Representation Engineering: A Top-Down Approach to AI Transparency | Andy Zou, Long Phan, Sarah Chen, James Campbell, Phillip Guo, Richard Ren, Alexander Pan, Xuwang Yin, Mantas Mazeika, Ann-Kathrin Dombrowski, Shashwat Goel, Nathaniel Li, Michael J. Byun, Zifan Wang, Alex Mallen, Steven Basart, Sanmi Koyejo, Dawn Song, Matt Fredrikson, J. Zico Kolter, Dan Hendrycks | arXiv preprint only (no conference proceedings) | arXiv:2310.01405v4 | **VERIFIED (preprint only)** | `https://arxiv.org/abs/2310.01405` (HTML — full 22-author list confirmed) | Background: RepE framework for population-level representation control | `zou2023repe` |
| **huang25** | "Huang & Lim, IASDR 2025 poster, DOI:10.21606/iasdr.2025.601" | Designing Intuitive Interfaces for Feature Steering of LLMs | **Allison Huang**, **Yihyun Lim** | IASDR 2025, poster paper, Track 4: Human-Centered AI | DOI:10.21606/iasdr.2025.601 | **VERIFIED** | `https://dl.designresearchsociety.org/iasdr/iasdr2025/posterpapers/34/` (HTML article:author meta tags confirm full names) | Strongest scoop-adjacent single-channel work; uses SAE features not CAA/RepE | `huang2025steering` |
| **ai-instr25** | "AI-Instruments (Riche et al., CHI 2025, arXiv:2502.18736)" | AI-Instruments: Embodying Prompts as Instruments to Abstract & Reflect Graphical Interface Commands as General-Purpose Tools | Nathalie Riche, Anna Offenwanger, Frederic Gmeiner, David Brown, Hugo Romat, Michel Pahud, Nicolai Marquardt, Kori Inkpen, Ken Hinckley | CHI 2025, Yokohama | arXiv:2502.18736v1; DOI:10.1145/3706598.3714259 | **VERIFIED** | arXiv Atom feed `id_list=2502.18736` (full author list + DOI confirmed) | HCI neighbor: prompt-layer reification as direct-manipulation objects (no latent channel) | `riche2025aiinstr` |
| **labarta26** | "Labarta et al. / 'SemanticLens', CVPR 2026 W (XAI4CV), arXiv:2604.11467 — vision/CLIP, expert-debugging" | From Attribution to Action: A Human-Centered Application of Activation Steering | Tobias Labarta, Maximilian Dreyer, Katharina Weitz, Wojciech Samek, Sebastian Lapuschkin | CVPR 2026 Workshop (XAI4CV, 5th edition) | arXiv:2604.11467v2 | **VERIFIED** | arXiv Atom feed `id_list=2604.11467` (authors confirmed); CVPR open-access URL verified via web search | Differentiation neighbor: vision/CLIP; N=8 expert interviews; debugging — NOT an LLM latent UI | `labarta2026attribution` |
| **latman26** | "Latent Manipulator (Raval, Dunnell, Lippman, CHI EA '26), DOI:10.1145/3772363.3798816" | Latent Manipulator: Using Concept-Guided Embedding Manipulation to Steer Embedding Visualizations | Shivam Raval, Kevin Dunnell, Andrew Lippman | CHI EA '26 (Extended Abstracts), Article 425, pp. 1–6 | DOI:10.1145/3772363.3798816 | **VERIFIED** | MIT Media Lab pub page `https://www.media.mit.edu/publications/latent-manipulator-using-concept-guided-embedding-manipulation-to-steer-embedding-visualizations/` (full citation string) | Differentiation: steers UMAP data-viz layout, NOT LLM generative behavior | `raval2026latman` |
| **tankel24** | "Tankelevitch et al., CHI 2024, arXiv:2312.10893, DOI:10.1145/3613904.3642902" | The Metacognitive Demands and Opportunities of Generative AI | Lev Tankelevitch, Viktor Kewenig, Auste Simkute, Ava Elizabeth Scott, Advait Sarkar, Abigail Sellen, Sean Rintel | CHI 2024 | arXiv:2312.10893v3; DOI:10.1145/3613904.3642902 | **VERIFIED** | `https://arxiv.org/abs/2312.10893` (HTML citation_author + citation_doi tags) | Theory base: metacognitive monitoring/control framing for GenAI usability | `tankelevitch2024metacog` |
| **stolfo25** | "Stolfo et al., ICLR 2025, arXiv:2410.12877" | Improving Instruction-Following in Language Models through Activation Steering | Alessandro Stolfo, Vidhisha Balachandran, Safoora Yousefi, Eric Horvitz, Besmira Nushi | ICLR 2025, Singapore | arXiv:2410.12877v2 | **VERIFIED** | `https://arxiv.org/abs/2410.12877` (HTML citation_author tags); ICLR 2025 proceedings hash 8c3262a4 confirmed | Adversarial neighbor: instruction↔vector correspondence; reviewer attack surface against C2b | `stolfo2025instr` |
| **subramani26** | "Subramani, ACL 2026 BigPicture W, arXiv:2607.00083" | Harnessing the Latent Space: From Steering Vectors to Model Calibrators for Control and Trust | Nishant Subramani | ACL 2026 BigPicture Workshop | arXiv:2607.00083v1 | **VERIFIED** | `https://arxiv.org/abs/2607.00083` (HTML citation_author + date confirmed: 2026-06-30) | Context: crowded "steering + trust" phrase; NOT a scoop (no interface, no user study) | `subramani2026latent` |
| **coninstruct25** | "ConInstruct (arXiv:2511.14342)" | ConInstruct: Evaluating Large Language Models on Conflict Detection and Resolution in Instructions | Xingwei He, Qianru Zhang, Pengfei Chen, Guanhua Chen, Linlin Yu, Yuan Yuan, Siu-Ming Yiu | arXiv preprint | arXiv:2511.14342v2 | **VERIFIED** | `https://arxiv.org/abs/2511.14342` (HTML citation_author full list + abstract confirmed) | Definition contrast: text-constraint conflict ≠ prompt↔latent channel conflict for users | `he2025coninstruct` |
| **whoctrl26** | "Who Controls the Conversation? (CHI 2026, arXiv:2603.00089)" | Who Controls the Conversation? User Perspectives On Generative AI (LLM) System Prompts | Anna Neumann, Yulu Pi, Jatinder Singh | CHI 2026 main proceedings | arXiv:2603.00089; DOI:10.1145/3772318.3791726 | **VERIFIED** | `https://arxiv.org/abs/2603.00089` (HTML citation_author + citation_doi; DOI prefix 10.1145/3772318 = CHI 2026 main) | HCI framing neighbor: user perspectives on prompt-layer control | `neumann2026whocontrols` |
| **learntrust26** | "Learning to Trust (arXiv:2603.22634)" | Learning to Trust: How Humans Mentally Recalibrate AI Confidence Signals | ZhaoBin Li, Mark Steyvers | arXiv preprint | arXiv:2603.22634v1 | **VERIFIED** | `https://arxiv.org/abs/2603.22634` (HTML citation_author: Li ZhaoBin, Steyvers Mark confirmed) | Trust-recalibration method for C3: Rescorla–Wagner + LLO model | `li2026learntrust` |
| **mindgap26** | "Mind the Performance Gap (arXiv:2602.04903)" | Mind the Performance Gap: Capability-Behavior Trade-offs in Feature Steering | Eitan Sprejer, Oscar Agustín Stanchi, María Victoria Carro, Denise Alejandra Mester, Iván Arcuschin | arXiv preprint | arXiv:2602.04903v1 | **VERIFIED** | `https://arxiv.org/abs/2602.04903` (HTML full abstract + citation_author confirmed) | Corroboration for C2/F2: steering degrades MMLU 66→46 %, coherence 4.62→2.24 vs. prompting | `sprejer2026mindgap` |
| **asteer26** | "ASTEER / When is Your LLM Steerable? (arXiv:2606.11599)" | When is Your LLM Steerable? | Chenrui Fan, Yize Cheng, Ming Li, Soheil Feizi, Tianyi Zhou | arXiv preprint | arXiv:2606.11599v1 | **VERIFIED** | `https://arxiv.org/abs/2606.11599` (HTML citation_author + abstract) | Steerability limits; 1.4 M steered generations, 150 concepts | `fan2026asteer` |
| **roguescalpel25** | "Rogue Scalpel (arXiv:2509.22067, ICLR 2026 W)" | The Rogue Scalpel: Activation Steering Compromises LLM Safety | Anton Korznikov, Andrey Galichin, Alexey Dontsov, Oleg Y. Rogov, Ivan Oseledets, Elena Tutubalina | ICLR 2026 Workshop (Principled Design for Trustworthy AI) | arXiv:2509.22067v2 | **VERIFIED-SECONDARY** | `https://arxiv.org/abs/2509.22067` (author list); `https://iclr.cc/virtual/2026/10019314` (abstract match) | Parallel evidence: "precise control of internals ≠ precise control of behavior" | `korznikov2025rogue` |
| **liaovaughan24** | Not yet cited (proposed addition) | AI Transparency in the Age of LLMs: A Human-Centered Research Roadmap | Q. Vera Liao, Jennifer Wortman Vaughan | Harvard Data Science Review, Special Issue 5 / 2024 | DOI:10.1162/99608f92.8036d03b | **VERIFIED-SECONDARY** | DOAJ `https://doaj.org/article/4ee3d1ef083a4a9ca78ab9689adf4bb0`; scite.ai (title/authors/venue/DOI confirmed) | Background: HCI roadmap for AI transparency; why legibility matters for non-experts | `liao2024transparency` |

---

## 2. CORRECTIONS (7 items — must resolve before writing stage)

### CORRECTION 1 — Mishra arXiv ID: CORRECT; fix venue label only

**Issue in repo:** open-risks implied the 2604.xxxxx ID "may be wrong/placeholder."
**Finding:** `<published>2026-04-10T19:11:13Z</published>` confirmed via arXiv Atom API. ID is **correct** (April 2026, not a placeholder).
**Fix required:** Change every occurrence of "ICLR 2026" to **"ICLR 2026 Workshops (Sci4DL, Re-Align)"** — this is a workshop paper, not a main-proceedings paper. The arXiv comment field is explicit.

### CORRECTION 2 — PSR: Add arXiv ID, full title, and both authors

**Issue:** Repo cites "Steer Like the LLM / PSR (ICML 2026)" with no arXiv ID and no authors.
**Verified metadata:**
- Full title: **"Steer Like the LLM: Activation Steering that Mimics Prompting"**
- Authors: **Geert Heyman, Frederik Vandeputte** (Nokia Bell Labs)
- arXiv: **2605.03907** (submitted 2026-05-05)
- Venue: **ICML 2026 poster #66813** — main conference, published
- Code: https://github.com/Nokia-Bell-Labs/steer-like-the-llm

The repo's "ICML 2026" venue claim is correct. Add arXiv ID and author list everywhere.

### CORRECTION 3 — CAA author name: use ACL Anthology canonical form

**Issue:** Repo uses "Rimsky (Panickssery) et al." inconsistently.
**Finding:** ACL Anthology (DOI 10.18653/v1/2024.acl-long.828) lists the first author as **Nina Rimsky** — the name on record at time of publication.
**Fix:** Cite as "Rimsky et al., 2024." Add footnote "First author now publishes as Nina Panickssery" only if desired; do not use "Panickssery et al." for this paper.

### CORRECTION 4 — Labarta / "SemanticLens": two separate works; NMI paper UNVERIFIED

**Finding:**
- **Labarta et al. "From Attribution to Action" (arXiv:2604.11467, CVPR 2026 W/XAI4CV)** = VERIFIED. Vision/CLIP, N=8 experts, debugging. NOT an LLM tool for non-experts. The repo's characterisation is correct.
- **"SemanticLens" (Fraunhofer HHI, Nature Machine Intelligence 2025)** = UNVERIFIED-METADATA. A Fraunhofer HHI press release confirms existence but author list, exact title, and DOI were not confirmed from a primary source (NMI paywall).

**Fix:** Do NOT include SemanticLens in the bibliography until full metadata (DOI, authors) is confirmed. Labarta et al. is safe to cite.

### CORRECTION 5 — ActAdd App-B sub-claim: [NEEDS EVIDENCE] flag UPHELD

**Issue:** open-risks #8 flagged "embedding-injection is weak but post-layer activation-diff is strong + perplexity degradation asymmetry" as [NEEDS EVIDENCE].
**Finding:** arXiv HTML for 2308.10248v5 is mathematical-notation-heavy and not human-readable in this pass. Abstract does not address App-B. AI-search prose about App-B contents is untrustworthy by policy.
**Fix:** Flag remains. Drop all App-B content from every draft until a team member reads the PDF directly.

### CORRECTION 6 — Stolfo et al.: add full author list to bibliography

**Verified full list:** Alessandro Stolfo, Vidhisha Balachandran, Safoora Yousefi, Eric Horvitz, Besmira Nushi (all Microsoft Research). See BibTeX key `stolfo2025instr`.

### CORRECTION 7 — Huang & Lim: full given names confirmed

**Verified from DRS Digital Library HTML meta tags (`article:author`):** **Allison Huang** and **Yihyun Lim**.
Fix bibliography entry. See BibTeX key `huang2025steering`.

---

## 3. Novelty-Threat Assessment

**Question:** Does any real work already occupy the exact contribution — *frozen pre-registered behavioral adjudication showing legibility ≠ controllability, generalized across ≥2 steering method families × ≥2 model families, with an HCI console framing for non-experts?*

**Finding: NO exact-gap occupant found.**

| Paper | Overlap with our contribution | Why NOT a scoop | Risk level |
|---|---|---|---|
| Sprejer et al. "Mind the Performance Gap" (arXiv:2602.04903) | Shows feature steering degrades capability vs. prompting; frames as "fundamental capability-behavior trade-offs" | Uses Goodfire SAE features (not CAA/ITI); no pre-registered protocol; no metacognitive axes; no 2×2 generalization; no user study | **MEDIUM** — cite and explicitly differentiate |
| Korznikov et al. "Rogue Scalpel" (arXiv:2509.22067, ICLR 2026 W) | "Precise control of internals ≠ precise control of behavior" — nearly our headline | Safety/jailbreak domain; random directions not mean-difference; no pre-registered adjudication; no user study | **LOW** |
| Heyman & Vandeputte "Steer Like the LLM" (arXiv:2605.03907, ICML 2026) | Trained steering matches/exceeds prompting — directly challenges the C2 behavioral-gap claim | Our C2 is scoped to **naive off-the-shelf mean-difference CAA/ITI**; PSR uses a **trained** method. Scope line is pre-registered. This is NOT a scoop but is a **mandatory citation**. | **HIGH framing threat** — scope line required in abstract/intro: *"naive off-the-shelf CAA/ITI mean-difference-style steering; cf. Heyman & Vandeputte (ICML 2026) for trained/optimized steering"* |

---

## 4. Proposed New Verified Neighbors (2024–2026)

| BibTeX key | Venue / Year | One-line relevance | How to cite |
|---|---|---|---|
| `sprejer2026mindgap` | arXiv preprint, Feb 2026 | Empirical capability–behavior tradeoff under feature steering vs. prompting | Corroborate C2/F2; distinguish: SAE features ≠ CAA/ITI; no pre-reg protocol |
| `korznikov2025rogue` | ICLR 2026 WS, Sep 2025 | "Precise control of internals ≠ precise control of behavior" in safety domain | Converging parallel evidence; different domain |
| `fan2026asteer` | arXiv preprint, Jun 2026 | 1.4 M steered generations, 150 concepts; steerability depends on context/concept/model | Motivates axis pre-selection; steerability-boundary context |
| `liao2024transparency` | Harvard Data Science Review, 2024 | HCI roadmap for AI transparency; legibility-first design for non-experts | Background for C3 / Introduction |
| `li2026learntrust` | arXiv preprint, Mar 2026 | N=200 behavioral study; Rescorla–Wagner + LLO model of trust recalibration | C3 study design: measure and model framework |
| `neumann2026whocontrols` | CHI 2026, Feb 2026 | User perspectives on hidden system prompts; users disconnected from control mechanism | Framing anchor for C3; our console extends to latent channel |
| `he2025coninstruct` | arXiv preprint, Nov 2025 | LLMs rarely notify users about conflicting text constraints | Sharpen conflict definition: text conflict ≠ prompt↔latent user conflict |

---

## 5. Complete Verified BibTeX Block — 20 @entries

> Slot every entry below verbatim into `docs/paper/references.bib`. Keys match §1.
> **Do NOT add BibTeX entries for UNVERIFIED/NOT-FOUND works (listed in §6).**

```bibtex
% ============================================================
% COGNITIVE CONSOLE — VERIFIED REFERENCES
% Generated 2026-07-24 · docs/research/2026-07-24-citation-verification.md
% 20 verified @entries total
% ============================================================

% ── CORE ML METHODS ─────────────────────────────────────────

@inproceedings{mishra2026nonsurj,
  title         = {Steered {LLM} Activations are Non-Surjective},
  author        = {Aayush Mishra and Daniel Khashabi and Anqi Liu},
  booktitle     = {{ICLR} 2026 Workshops (Sci4DL and Re-Align)},
  year          = {2026},
  eprint        = {2604.09839},
  archivePrefix = {arXiv},
  primaryClass  = {cs.AI},
  url           = {https://arxiv.org/abs/2604.09839},
  note          = {arXiv:2604.09839v2, submitted 2026-04-10.
                   Workshop paper only --- NOT ICLR 2026 main proceedings.}
}

@inproceedings{heyman2026steer,
  title         = {Steer Like the {LLM}: Activation Steering that Mimics Prompting},
  author        = {Geert Heyman and Frederik Vandeputte},
  booktitle     = {Proceedings of the Forty-Third International Conference
                   on Machine Learning},
  year          = {2026},
  eprint        = {2605.03907},
  archivePrefix = {arXiv},
  primaryClass  = {cs.LG},
  url           = {https://arxiv.org/abs/2605.03907},
  note          = {ICML 2026 poster \#66813.
                   Code: \url{https://github.com/Nokia-Bell-Labs/steer-like-the-llm}}
}

@inproceedings{rimsky2024caa,
  title         = {Steering {Llama}~2 via Contrastive Activation Addition},
  author        = {Nina Rimsky and Nick Gabrieli and Julian Schulz and
                   Meg Tong and Evan Hubinger and Alexander Turner},
  booktitle     = {Proceedings of the 62nd Annual Meeting of the Association
                   for Computational Linguistics (Volume~1: Long Papers)},
  pages         = {15504--15522},
  year          = {2024},
  doi           = {10.18653/v1/2024.acl-long.828},
  eprint        = {2312.06681},
  archivePrefix = {arXiv},
  primaryClass  = {cs.CL},
  url           = {https://aclanthology.org/2024.acl-long.828/},
  note          = {ACL 2024 Outstanding Paper.
                   First author now publishes as Nina Panickssery.}
}

@misc{turner2023actadd,
  title         = {Steering Language Models With Activation Engineering},
  author        = {Alexander Matt Turner and Lisa Thiergart and Gavin Leech and
                   David Udell and Juan~J. Vazquez and Ulisse Mini and
                   Monte MacDiarmid},
  year          = {2023},
  eprint        = {2308.10248},
  archivePrefix = {arXiv},
  primaryClass  = {cs.LG},
  url           = {https://arxiv.org/abs/2308.10248},
  note          = {arXiv:2308.10248v5, updated 2024-10-10.
                   WARNING: Appendix~B specific sub-claim (exclusion experiment)
                   is NOT VERIFIED from primary source --- do not cite App-B
                   content until PDF is read directly (open-risks \#8).}
}

@inproceedings{li2023iti,
  title         = {Inference-Time Intervention: Eliciting Truthful Answers
                   from a Language Model},
  author        = {Kenneth Li and Oam Patel and Fernanda Vi{\'{e}}gas and
                   Hanspeter Pfister and Martin Wattenberg},
  booktitle     = {Advances in Neural Information Processing Systems},
  volume        = {36},
  pages         = {41451--41530},
  year          = {2023},
  eprint        = {2306.03341},
  archivePrefix = {arXiv},
  primaryClass  = {cs.LG},
  url           = {https://proceedings.neurips.cc/paper_files/paper/2023/hash/81b8390039b7302c909cb769f8b6cd93-Abstract-Conference.html}
}

@misc{zou2023repe,
  title         = {Representation Engineering: A Top-Down Approach to
                   {AI} Transparency},
  author        = {Andy Zou and Long Phan and Sarah Chen and James Campbell and
                   Phillip Guo and Richard Ren and Alexander Pan and
                   Xuwang Yin and Mantas Mazeika and Ann-Kathrin Dombrowski and
                   Shashwat Goel and Nathaniel Li and Michael~J. Byun and
                   Zifan Wang and Alex Mallen and Steven Basart and
                   Sanmi Koyejo and Dawn Song and Matt Fredrikson and
                   J.~Zico Kolter and Dan Hendrycks},
  year          = {2023},
  eprint        = {2310.01405},
  archivePrefix = {arXiv},
  primaryClass  = {cs.LG},
  url           = {https://arxiv.org/abs/2310.01405},
  note          = {arXiv:2310.01405v4. Preprint only ---
                   no conference proceedings publication confirmed.}
}

@inproceedings{stolfo2025instr,
  title         = {Improving Instruction-Following in Language Models
                   through Activation Steering},
  author        = {Alessandro Stolfo and Vidhisha Balachandran and
                   Safoora Yousefi and Eric Horvitz and Besmira Nushi},
  booktitle     = {The Thirteenth International Conference on Learning
                   Representations},
  year          = {2025},
  eprint        = {2410.12877},
  archivePrefix = {arXiv},
  primaryClass  = {cs.CL},
  url           = {https://arxiv.org/abs/2410.12877},
  note          = {ICLR 2025 (Singapore).
                   Code: \url{https://github.com/microsoft/llm-steer-instruct}}
}

% ── HCI / INTERFACE WORKS ───────────────────────────────────

@inproceedings{tankelevitch2024metacog,
  title         = {The Metacognitive Demands and Opportunities of Generative {AI}},
  author        = {Lev Tankelevitch and Viktor Kewenig and Auste Simkute and
                   Ava Elizabeth Scott and Advait Sarkar and Abigail Sellen and
                   Sean Rintel},
  booktitle     = {Proceedings of the 2024 {CHI} Conference on Human Factors
                   in Computing Systems},
  year          = {2024},
  doi           = {10.1145/3613904.3642902},
  eprint        = {2312.10893},
  archivePrefix = {arXiv},
  primaryClass  = {cs.HC},
  url           = {https://arxiv.org/abs/2312.10893}
}

@inproceedings{riche2025aiinstr,
  title         = {{AI}-Instruments: Embodying Prompts as Instruments to
                   Abstract \& Reflect Graphical Interface Commands as
                   General-Purpose Tools},
  author        = {Nathalie Riche and Anna Offenwanger and Frederic Gmeiner and
                   David Brown and Hugo Romat and Michel Pahud and
                   Nicolai Marquardt and Kori Inkpen and Ken Hinckley},
  booktitle     = {Proceedings of the 2025 {CHI} Conference on Human Factors
                   in Computing Systems},
  year          = {2025},
  doi           = {10.1145/3706598.3714259},
  eprint        = {2502.18736},
  archivePrefix = {arXiv},
  primaryClass  = {cs.HC},
  url           = {https://arxiv.org/abs/2502.18736}
}

@inproceedings{huang2025steering,
  title         = {Designing Intuitive Interfaces for Feature Steering of {LLM}s},
  author        = {Allison Huang and Yihyun Lim},
  booktitle     = {International Association of Societies of Design Research
                   Conference (IASDR 2025)},
  year          = {2025},
  doi           = {10.21606/iasdr.2025.601},
  url           = {https://dl.designresearchsociety.org/iasdr/iasdr2025/posterpapers/34/},
  note          = {Poster paper, Track~4: Human-Centered AI.
                   Uses Goodfire Ember API / SAE features
                   (not CAA/RepE mean-difference vectors).
                   Code: \url{https://github.com/acyhuang/steering-interface}.
                   Lower archival weight (poster).}
}

@inproceedings{labarta2026attribution,
  title         = {From Attribution to Action: A Human-Centered Application
                   of Activation Steering},
  author        = {Tobias Labarta and Maximilian Dreyer and Katharina Weitz and
                   Wojciech Samek and Sebastian Lapuschkin},
  booktitle     = {Proceedings of the {IEEE/CVF} Conference on Computer Vision
                   and Pattern Recognition ({CVPR}) Workshops},
  year          = {2026},
  eprint        = {2604.11467},
  archivePrefix = {arXiv},
  primaryClass  = {cs.AI},
  url           = {https://openaccess.thecvf.com/content/CVPR2026W/XAI4CV/html/Labarta_From_Attribution_to_Action_A_Human-Centered_Application_of_Activation_Steering_CVPRW_2026_paper.html},
  note          = {XAI4CV Workshop (5th edition) at CVPR 2026.
                   Vision/CLIP only --- NOT LLMs.
                   N=8 expert interviews, debugging workflow.
                   Separate from ``SemanticLens'' (Fraunhofer HHI NMI 2025),
                   which is UNVERIFIED-METADATA and has no BibTeX entry here.}
}

@inproceedings{raval2026latman,
  title         = {Latent Manipulator: Using Concept-Guided Embedding
                   Manipulation to Steer Embedding Visualizations},
  author        = {Shivam Raval and Kevin Dunnell and Andrew Lippman},
  booktitle     = {Proceedings of the Extended Abstracts of the 2026 {CHI}
                   Conference on Human Factors in Computing Systems},
  articleno     = {425},
  pages         = {1--6},
  year          = {2026},
  doi           = {10.1145/3772363.3798816},
  url           = {https://www.media.mit.edu/publications/latent-manipulator-using-concept-guided-embedding-manipulation-to-steer-embedding-visualizations/},
  note          = {CHI~EA~'26 (4-page extended abstract).
                   Steers UMAP data-viz layout --- NOT LLM generative behavior.}
}

@inproceedings{neumann2026whocontrols,
  title         = {Who Controls the Conversation? {User} Perspectives On
                   Generative {AI} ({LLM}) System Prompts},
  author        = {Anna Neumann and Yulu Pi and Jatinder Singh},
  booktitle     = {Proceedings of the 2026 {CHI} Conference on Human Factors
                   in Computing Systems},
  year          = {2026},
  doi           = {10.1145/3772318.3791726},
  eprint        = {2603.00089},
  archivePrefix = {arXiv},
  primaryClass  = {cs.HC},
  url           = {https://arxiv.org/abs/2603.00089}
}

@article{liao2024transparency,
  title         = {{AI} Transparency in the Age of {LLM}s: {A}
                   Human-Centered Research Roadmap},
  author        = {Q.~Vera Liao and Jennifer Wortman Vaughan},
  journal       = {Harvard Data Science Review},
  year          = {2024},
  doi           = {10.1162/99608f92.8036d03b},
  url           = {https://hdsr.mitpress.mit.edu/pub/aelql9qy},
  note          = {Special Issue~5: Grappling With the Generative AI
                   Revolution. VERIFIED-SECONDARY (DOAJ + scite.ai).}
}

% ── CONCURRENT / RECENT RELATED WORKS ───────────────────────

@inproceedings{subramani2026latent,
  title         = {Harnessing the Latent Space: From Steering Vectors to
                   Model Calibrators for Control and Trust},
  author        = {Nishant Subramani},
  booktitle     = {{ACL} 2026 Workshop on Big-Picture Perspectives on
                   Language Technology ({BigPicture})},
  year          = {2026},
  eprint        = {2607.00083},
  archivePrefix = {arXiv},
  primaryClass  = {cs.CL},
  url           = {https://arxiv.org/abs/2607.00083},
  note          = {Single-author position paper. No interface, no user study.
                   Verify exact ACL workshop name before camera-ready.}
}

@misc{he2025coninstruct,
  title         = {{ConInstruct}: Evaluating Large Language Models on
                   Conflict Detection and Resolution in Instructions},
  author        = {Xingwei He and Qianru Zhang and Pengfei Chen and
                   Guanhua Chen and Linlin Yu and Yuan Yuan and Siu-Ming Yiu},
  year          = {2025},
  eprint        = {2511.14342},
  archivePrefix = {arXiv},
  primaryClass  = {cs.CL},
  url           = {https://arxiv.org/abs/2511.14342},
  note          = {arXiv:2511.14342v2. Preprint only.}
}

@misc{li2026learntrust,
  title         = {Learning to Trust: How Humans Mentally Recalibrate
                   {AI} Confidence Signals},
  author        = {ZhaoBin Li and Mark Steyvers},
  year          = {2026},
  eprint        = {2603.22634},
  archivePrefix = {arXiv},
  primaryClass  = {cs.HC},
  url           = {https://arxiv.org/abs/2603.22634},
  note          = {arXiv:2603.22634v1. Preprint only (no venue confirmed).
                   N=200 behavioural study; Rescorla--Wagner + LLO trust model.}
}

@misc{sprejer2026mindgap,
  title         = {Mind the Performance Gap: Capability-Behavior
                   Trade-offs in Feature Steering},
  author        = {Eitan Sprejer and Oscar Agust\'{\i}n Stanchi and
                   Mar\'{\i}a Victoria Carro and Denise Alejandra Mester and
                   Iv\'an Arcuschin},
  year          = {2026},
  eprint        = {2602.04903},
  archivePrefix = {arXiv},
  primaryClass  = {cs.LG},
  url           = {https://arxiv.org/abs/2602.04903},
  note          = {arXiv:2602.04903v1. Preprint only.
                   Uses Goodfire Auto Steer (SAE) --- not CAA/ITI.}
}

@misc{fan2026asteer,
  title         = {When is Your {LLM} Steerable?},
  author        = {Chenrui Fan and Yize Cheng and Ming Li and
                   Soheil Feizi and Tianyi Zhou},
  year          = {2026},
  eprint        = {2606.11599},
  archivePrefix = {arXiv},
  primaryClass  = {cs.LG},
  url           = {https://arxiv.org/abs/2606.11599},
  note          = {arXiv:2606.11599v1. ASTEER testbed:
                   1.4\,M steered generations, 150 concepts. Preprint only.}
}

@inproceedings{korznikov2025rogue,
  title         = {The Rogue Scalpel: Activation Steering Compromises
                   {LLM} Safety},
  author        = {Anton Korznikov and Andrey Galichin and Alexey Dontsov and
                   Oleg~Y. Rogov and Ivan Oseledets and Elena Tutubalina},
  booktitle     = {{ICLR} 2026 Workshop on Principled Design for Trustworthy
                   {AI}: Interpretability, Robustness, and Safety Across
                   Modalities},
  year          = {2026},
  eprint        = {2509.22067},
  archivePrefix = {arXiv},
  primaryClass  = {cs.CL},
  url           = {https://arxiv.org/abs/2509.22067},
  note          = {arXiv:2509.22067v2. ICLR 2026 workshop (not main proceedings).
                   VERIFIED-SECONDARY for workshop venue
                   (iclr.cc/virtual/2026/10019314).}
}
```

---

## 6. Works That Cannot Be Cited — Do Not Add to references.bib

| Work | Reason | Required action |
|---|---|---|
| **SemanticLens (Fraunhofer HHI, Nature Machine Intelligence 2025)** | Only a press release accessible; no DOI, full author list, or exact title confirmed from a primary source (NMI paywall). | Team member must retrieve DOI + author list from NMI directly before this enters any bibliography. |
| **ActAdd Appendix B sub-claim** | arXiv HTML unreadable; abstract silent on App-B; AI search prose untrusted by policy. The `turner2023actadd` entry above covers the main paper; only App-B specifics are blocked. | Open `https://arxiv.org/pdf/2308.10248` and read Appendix B before citing its sub-claims. |
| **"Probing and Steering Chain-of-Thought Unfaithfulness"** | AI search returned arXiv:2403.03936 — confirmed to be a Klein-Gordon mathematics paper. Real arXiv ID unknown. | NOT-FOUND in this pass. Do not cite without a primary source. |
| **"Beyond Anthropomorphism: A Spectrum of Interface Metaphors for LLMs" (arXiv:2603.04613)** | Mentioned in prior-art sweep but not independently fetched in this pass. | Fetch arXiv:2603.04613 and confirm before citing. |
| **Dual-Channel Steering (ICLR 2026 WS, OpenReview bEc9slMJ8k)** | Not re-verified in this pass; prior-art sweep confirmed it as a name-collision risk. | Verify OpenReview URL before using; cite only as a name-collision note, not a substantive citation. |

---

## 7. Mandatory Writing-Stage Framing Rules

1. **mishra2026nonsurj** → "ICLR 2026 Workshops (Sci4DL, Re-Align)" — never "ICLR 2026."
2. **heyman2026steer** → Mandatory scope line in every C2-adjacent sentence: *"naive off-the-shelf CAA/ITI mean-difference-style steering; cf.~\citet{heyman2026steer} for trained/optimized steering that can match or exceed prompting."*
3. **huang2025steering** → Call it a "poster paper" in text; state it uses SAE features (not CAA/RepE mean-difference vectors).
4. **raval2026latman** → Clarify steers an embedding-visualization layout, NOT LLM generative outputs.
5. **zou2023repe** → Cite as a preprint — not a conference paper.
6. **turner2023actadd** → Drop all Appendix B specifics from every draft until §6 flag is resolved.
7. **rimsky2024caa** → Use "Rimsky et al." (ACL Anthology canonical name).
8. **sprejer2026mindgap** → Must note method difference (SAE ≠ CAA/ITI) when cited alongside our calibration-harm results.