# Flagship Citation Verification Report
## Novice-Manipulation Prereg — Pre-Freeze Verification

- **Document status:** VERIFICATION COMPLETE (not yet frozen)
- **Verification date:** 2026-07-27
- **Verifier:** Research Citation-Verification Subagent
- **Sources used:** arXiv abstract/HTML pages (primary), ACL Anthology, DeepMind blog, OpenReview, web search
- **Owner rule applied:** real/recent/verifiable only; NEVER fabricate metadata; UNVERIFIED/NOT-FOUND marked explicitly.
- **Documents checked:** `docs/research/2026-07-27-prereg-novice-manipulation-DRAFT.md` and `docs/research/2026-07-27-implicit-user-conditioning-brainstorm.md`

---

## 1. Citation Verification Table

| Key | Claimed in prereg/brainstorm | VERIFIED metadata (primary source) | Status | Primary-source URL |
|---|---|---|---|---|
| **Akbulut et al. 2026** | "Evaluating Language Models for Harmful Manipulation," arXiv:2603.25326, Google DeepMind, N>10,000, health/finance/policy, explicit-vs-emergent | Title EXACT ✓; Authors: Canfer Akbulut, Rasmi Elasmar, Abhishek Roy (+9 co-authors); Affiliation: Google DeepMind (most) + Google (Roy) ✓; N=10,101 ✓; Domains: public policy, finance, health ✓; Locales: US, UK, India ✓; Conditions: "explicit steering" vs "non-explicit steering" vs baseline (NOT "emergent" — minor language note; prereg differentiation table says "explicit-prompt or no-explicit-prompt" which IS accurate); arXiv ID 2603.25326 = March 2026 ✓ REAL; Venue: Google DeepMind preprint + blog (deepmind.google); no external peer-review venue confirmed | **VERIFIED** ✓ (with note: "emergent" is not the paper's term; use "non-explicit") | https://arxiv.org/abs/2603.25326 · https://deepmind.google/blog/protecting-people-from-harmful-manipulation/ |
| **ExPerT 2607.01242** | arXiv:2607.01242, ACL 2026, expertise adaptation, N=40, −65.7% error, +17.5% satisfaction | Title: "ExPerT: Personalizing LLM Responses to Users' Domain Expertise via Query-Wise Semantic and Keystroke Behavioral Cues" ✓; Authors: Yeji Park, Jiwon Tark, Taesik Gong ✓; ACL 2026 long paper ✓; ACL Anthology: 2026.acl-long.959; DOI: 10.18653/v1/2026.acl-long.959; N=40, 1270 queries ✓; −65.7% error (MAE 0.398 vs 1.162) ✓; +17.52% satisfaction ✓; Oral presentation + SAC Highlight Award | **VERIFIED** ✓ | https://arxiv.org/abs/2607.01242 · https://aclanthology.org/2026.acl-long.959/ |
| **Williams et al. 2411.02306** | "On Targeted Manipulation and Deception when Optimizing LLMs for User Feedback," arXiv:2411.02306, NeurIPS 2024 workshop | Title EXACT ✓; Authors: Marcus Williams, Micah Carroll, Adhyyan Narang, Constantin Weisser, Brendan Murphy, Anca Dragan ✓; Venue: NeurIPS 2024 SoLaR Workshop (Socially Responsible Language Modelling Research) ✓; Note: workshop version has slightly different title "Targeted Manipulation and Deception Emerge in LLMs Trained on User Feedback"; arXiv v3 = Feb 2025 revision; 2% susceptibility threshold ✓ | **VERIFIED** ✓ (venue name corrected: NeurIPS 2024 SoLaR Workshop) | https://arxiv.org/abs/2411.02306 · https://mlanthology.org/neuripsw/2024/williams2024neuripsw-targeted/ |
| **DarkBench 2503.10728** | "DarkBench: Benchmarking Dark Patterns in Large Language Models," arXiv:2503.10728, ICLR 2025 (oral); 6 categories incl. brand bias, user retention, sycophancy, anthropomorphism, harmful generation, sneaking | Title EXACT ✓; Authors: Esben Kran, Hieu Minh "Jord" Nguyen, Akash Kundu, Sami Jawhar, Jinsuk Park, Mateusz Maria Jurewicz ✓; 660 prompts ✓; 6 categories EXACT ✓; ICLR 2025 oral ✓; OpenReview: odjMSBSWRt | **VERIFIED** ✓ | https://arxiv.org/abs/2503.10728 · https://openreview.net/forum?id=odjMSBSWRt |
| **Sharma et al. 2310.13548** | "Towards Understanding Sycophancy in Language Models," arXiv:2310.13548, ICLR 2024 | Title EXACT ✓; Authors: Mrinank Sharma, Meg Tong, Tomasz Korbak, David Duvenaud, Amanda Askell, Samuel R. Bowman, Newton Cheng, Esin Durmus, Zac Hatfield-Dodds, Scott R. Johnston, Shauna Kravec, Timothy Maxwell, Sam McCandlish, Kamal Ndousse, Oliver Rausch, Nicholas Schiefer, Da Yan, Miranda Zhang, Ethan Perez ✓; ICLR 2024 ✓ | **VERIFIED** ✓ | https://arxiv.org/abs/2310.13548 · https://proceedings.iclr.cc/paper_files/paper/2024/hash/0105f7972202c1d4fb817da9f21a9663-Abstract-Conference.html |
| **AI Sandbagging 2406.07358** | "AI Sandbagging: Language Models can Strategically Underperform on Evaluations," arXiv:2406.07358, "2024" | Title EXACT ✓; Authors: Teun van der Weij, Felix Hofstätter, Ollie Jaffe, Samuel F. Brown, Francis Rhys Ward ✓; **VENUE CORRECTION: ICLR 2025** (main conference), NOT just "2024"; also presented at NeurIPS 2024 SoLaR Workshop | **CORRECTED** ⚠️ (venue: ICLR 2025, not "2024") | https://arxiv.org/abs/2406.07358 · https://proceedings.iclr.cc/paper_files/paper/2025/hash/b5e5753b0a0e440a6d8dc7e143617cec-Abstract-Conference.html |
| **ELEPHANT 2505.13995** | "Measuring and understanding social sycophancy in LLMs," arXiv:2505.13995, "2025" | Title: "ELEPHANT: Measuring and understanding social sycophancy in LLMs" ✓; Authors: Myra Cheng, Sunny Yu, Cinoo Lee, Pranav Khadpe, Lujain Ibrahim, Dan Jurafsky ✓; **VENUE CORRECTION: ICLR 2026** (OpenReview confirmed), NOT unvenued "2025"; arXiv DOI field 10.1126/science.aec8352 refers to a *separate* related Science 2026 paper by overlapping authors ("Sycophantic AI Decreases Prosocial Intentions and Promotes Dependence"), NOT the ELEPHANT paper | **CORRECTED** ⚠️ (venue: ICLR 2026; Science DOI is a related different paper) | https://arxiv.org/abs/2505.13995 · https://openreview.net/forum?id=igbRHKEiAs |
| **"Who's Asking?" 2510.12925** | arXiv:2510.12925, persona-robustness QA study | Full title: "Who's Asking? Evaluating LLM Robustness to Inquiry Personas in Factual Question Answering" ✓; Authors: Nil-Jana Akpinar, Chia-Jung Lee, Vanessa Murdock, Pietro Perona ✓; Submitted 2025-10-14; No confirmed peer-reviewed venue (arXiv preprint) | **VERIFIED** ✓ (arXiv preprint; no published venue confirmed) | https://arxiv.org/abs/2510.12925 |
| **Gao & Kreiss 2509.04373** | "Gao & Kreiss, EMNLP 2025, arXiv:2509.04373" (brainstorm only — NOT cited in prereg draft) | **CONTENT MISMATCH**: Title is "Measuring Bias or Measuring the Task: Understanding the Brittle Nature of LLM Gender Biases" — this is about gender bias evaluation METHODOLOGY, not manipulation/novice users. Authors: Bufan Gao, Elisa Kreiss ✓; Venue: EMNLP 2025 ✓. Used correctly in brainstorm as methodological confound warning for Direction C (social register), NOT cited in prereg draft. | **CORRECTED** ⚠️ (paper exists, ID/venue correct; content is gender-bias methodology — correctly used as confound warning in brainstorm only) | https://arxiv.org/abs/2509.04373 |
| **LatentQA / Choi et al. Transluce 2025** | "LatentQA / Choi et al. Transluce 2025 (transluce.org/user-modeling)" — marked UNVERIFIED in both docs | Page confirmed real ✓; Title: "Scalably Extracting Latent Representations of Users"; Authors: Dami Choi, Vincent Huang, Sarah Schwettmann, Jacob Steinhardt ✓; URL: https://transluce.org/user-modeling ✓; **No arXiv ID or stable DOI found** — research post/technical report; datasets+code on HuggingFace. Underlying LatentQA decoder: Alexander Pan, Lijie Chen, Jacob Steinhardt, arXiv:2412.08686 | **PARTIALLY VERIFIED** ⚠️ (research is real, authors confirmed; no arXiv ID or DOI; cite as technical report/web resource with URL + access date) | https://transluce.org/user-modeling · https://arxiv.org/abs/2412.08686 (underlying LatentQA method) |

---

## 2. VERIFIED BibTeX Block

```bibtex
%% ============================================================
%% VERIFIED CITATIONS — 2026-07-27 pre-freeze verification
%% EloiseJulia/cognitive-console prereg: novice-manipulation
%% All metadata confirmed against primary sources.
%% ============================================================

%% [CRITICAL] VERIFIED — Google DeepMind
@misc{akbulut2026harmful,
  title        = {Evaluating Language Models for Harmful Manipulation},
  author       = {Canfer Akbulut and Rasmi Elasmar and Abhishek Roy and Anthony Payne
                  and Priyanka Suresh and Lujain Ibrahim and Seliem El-Sayed
                  and Charvi Rastogi and Ashyana Kachra and Will Hawkins
                  and Kristian Lum and Laura Weidinger},
  year         = {2026},
  eprint       = {2603.25326},
  archivePrefix= {arXiv},
  primaryClass = {cs.CL},
  url          = {https://arxiv.org/abs/2603.25326},
  note         = {Google DeepMind. N=10{,}101 participants, three domains (public policy,
                  finance, health), three locales (US, UK, India); explicit-steering vs
                  non-explicit-steering vs baseline conditions.}
}

%% VERIFIED — ACL 2026 long paper (oral, SAC Highlight Award)
@inproceedings{park2026expert,
  title        = {ExPerT: Personalizing {LLM} Responses to Users' Domain Expertise
                  via Query-Wise Semantic and Keystroke Behavioral Cues},
  author       = {Yeji Park and Jiwon Tark and Taesik Gong},
  booktitle    = {Proceedings of the 64th Annual Meeting of the Association for
                  Computational Linguistics (Volume 1: Long Papers)},
  year         = {2026},
  pages        = {20928--20963},
  doi          = {10.18653/v1/2026.acl-long.959},
  url          = {https://aclanthology.org/2026.acl-long.959/}
}

%% VERIFIED — NeurIPS 2024 SoLaR Workshop
%% Note: workshop title slightly differs: "Targeted Manipulation and Deception
%% Emerge in LLMs Trained on User Feedback"; arXiv uses "Optimizing" version.
@misc{williams2024targeted,
  title        = {On Targeted Manipulation and Deception when Optimizing {LLM}s
                  for User Feedback},
  author       = {Marcus Williams and Micah Carroll and Adhyyan Narang
                  and Constantin Weisser and Brendan Murphy and Anca Dragan},
  year         = {2024},
  eprint       = {2411.02306},
  archivePrefix= {arXiv},
  primaryClass = {cs.LG},
  url          = {https://arxiv.org/abs/2411.02306},
  note         = {NeurIPS 2024 SoLaR (Socially Responsible Language Modelling Research)
                  Workshop. Workshop proceedings: mlanthology.org/neuripsw/2024/williams2024neuripsw-targeted/}
}

%% VERIFIED — ICLR 2025 oral
@inproceedings{kran2025darkbench,
  title        = {{DarkBench}: Benchmarking Dark Patterns in Large Language Models},
  author       = {Esben Kran and Hieu Minh {``Jord''} Nguyen and Akash Kundu
                  and Sami Jawhar and Jinsuk Park and Mateusz Maria Jurewicz},
  booktitle    = {The Thirteenth International Conference on Learning Representations
                  (ICLR 2025)},
  year         = {2025},
  url          = {https://openreview.net/forum?id=odjMSBSWRt},
  note         = {Oral presentation. 660 prompts, 6 categories: brand bias, user retention,
                  sycophancy, anthropomorphism, harmful generation, sneaking.}
}

%% VERIFIED — ICLR 2024
@inproceedings{sharma2024sycophancy,
  title        = {Towards Understanding Sycophancy in Language Models},
  author       = {Mrinank Sharma and Meg Tong and Tomasz Korbak and David Duvenaud
                  and Amanda Askell and Samuel R. Bowman and Newton Cheng
                  and Esin Durmus and Zac Hatfield-Dodds and Scott R. Johnston
                  and Shauna Kravec and Timothy Maxwell and Sam McCandlish
                  and Kamal Ndousse and Oliver Rausch and Nicholas Schiefer
                  and Da Yan and Miranda Zhang and Ethan Perez},
  booktitle    = {The Twelfth International Conference on Learning Representations
                  (ICLR 2024)},
  year         = {2024},
  url          = {https://arxiv.org/abs/2310.13548}
}

%% CORRECTED venue: ICLR 2025 (prereg said only "2024")
@inproceedings{vanderweij2025sandbagging,
  title        = {{AI} Sandbagging: Language Models can Strategically Underperform
                  on Evaluations},
  author       = {Teun van der Weij and Felix Hofst{\"a}tter and Ollie Jaffe
                  and Samuel F. Brown and Francis Rhys Ward},
  booktitle    = {The Thirteenth International Conference on Learning Representations
                  (ICLR 2025)},
  year         = {2025},
  url          = {https://arxiv.org/abs/2406.07358}
}

%% CORRECTED venue: ICLR 2026 (prereg said only "2025")
@inproceedings{cheng2026elephant,
  title        = {{ELEPHANT}: Measuring and understanding social sycophancy in {LLM}s},
  author       = {Myra Cheng and Sunny Yu and Cinoo Lee and Pranav Khadpe
                  and Lujain Ibrahim and Dan Jurafsky},
  booktitle    = {The Fourteenth International Conference on Learning Representations
                  (ICLR 2026)},
  year         = {2026},
  url          = {https://arxiv.org/abs/2505.13995},
  note         = {OpenReview: igbRHKEiAs. Note: DOI 10.1126/science.aec8352 visible in
                  arXiv record refers to a separate related Science 2026 paper by
                  overlapping authors, not ELEPHANT itself.}
}

%% VERIFIED — arXiv preprint; no confirmed peer-reviewed venue
@misc{akpinar2025whosasking,
  title        = {Who's Asking? {E}valuating {LLM} Robustness to Inquiry Personas
                  in Factual Question Answering},
  author       = {Nil-Jana Akpinar and Chia-Jung Lee and Vanessa Murdock and Pietro Perona},
  year         = {2025},
  eprint       = {2510.12925},
  archivePrefix= {arXiv},
  primaryClass = {cs.CL},
  url          = {https://arxiv.org/abs/2510.12925}
}

%% CORRECTED: paper exists, content is gender-bias eval methodology (EMNLP 2025)
%% Used ONLY as design-confound warning in brainstorm (Direction C). NOT cited in prereg.
@inproceedings{gao2025bias,
  title        = {Measuring Bias or Measuring the Task: Understanding the Brittle Nature
                  of {LLM} Gender Biases},
  author       = {Bufan Gao and Elisa Kreiss},
  booktitle    = {Proceedings of the 2025 Conference on Empirical Methods in Natural
                  Language Processing (EMNLP 2025)},
  year         = {2025},
  url          = {https://arxiv.org/abs/2509.04373},
  note         = {Gender bias evaluation methodology paper; not about manipulation or novice
                  users. Cited only in brainstorm as methodological confound warning for
                  Direction C (social-register cueing). Do NOT use as manipulation citation.}
}

%% PARTIALLY VERIFIED — Transluce technical report (no arXiv ID or DOI)
%% Cite as web resource with access date.
@techreport{choi2025latentusers,
  title        = {Scalably Extracting Latent Representations of Users},
  author       = {Dami Choi and Vincent Huang and Sarah Schwettmann and Jacob Steinhardt},
  institution  = {Transluce AI},
  year         = {2025},
  url          = {https://transluce.org/user-modeling},
  note         = {Datasets and model checkpoints: https://huggingface.co/collections/Transluce/scalably-extracting-latent-representations-of-users;
                  code: https://github.com/TransluceAI/observatory.
                  Uses LatentQA decoder (Pan, Chen, Steinhardt, arXiv:2412.08686).
                  No stable arXiv ID or journal DOI confirmed as of 2026-07-27.}
}

%% Underlying LatentQA method (referenced by Choi et al. above)
@misc{pan2024latentqa,
  title        = {{LatentQA}: Teaching {LLMs} to Decode Activations Into Natural Language},
  author       = {Alexander Pan and Lijie Chen and Jacob Steinhardt},
  year         = {2024},
  eprint       = {2412.08686},
  archivePrefix= {arXiv},
  primaryClass = {cs.LG},
  url          = {https://arxiv.org/abs/2412.08686}
}
```

---

## 3. CORRECTIONS / NOT-FOUND Section

### 3.1 CORRECTIONS (IDs correct; metadata needs update in prereg/brainstorm)

| Citation | Issue | Correction |
|---|---|---|
| **Akbulut et al. 2603.25326** | Prereg says "explicit-vs-emergent manipulation." The paper uses "explicit steering" vs "non-explicit steering" (not "emergent"). The prereg's own differentiation table says "explicit-prompt or no-explicit-prompt" which IS accurate. | Minor: replace any "emergent" characterization with "non-explicit steering" when quoting the paper directly. Also: no external peer-review venue confirmed; cite as Google DeepMind preprint 2026 until venue announced. |
| **AI Sandbagging 2406.07358** | Prereg/brainstorm cites as just "2024." | Correct venue: **ICLR 2025** (main conference). Update BibTeX accordingly. |
| **ELEPHANT 2505.13995** | Prereg/brainstorm cites as just "2025" without venue. | Correct venue: **ICLR 2026** (confirmed via OpenReview). Note: DOI 10.1126/science.aec8352 in the arXiv record refers to a *separate* related Science 2026 paper ("Sycophantic AI Decreases Prosocial Intentions and Promotes Dependence") by an overlapping author group, NOT the ELEPHANT benchmark paper. Do not confuse the two. |
| **Gao & Kreiss 2509.04373** | Brainstorm lists as "Minimal-pair gender confound" without title; someone reading the brainstorm might mistake this for a manipulation-related paper. | Paper is about gender bias EVALUATION METHODOLOGY — correctly used in brainstorm as a design confound warning for Direction C, not as a manipulation citation. Confirm it is NOT cited in the prereg draft (grep confirmed: absent from prereg). Title should be stated explicitly whenever referenced. |

### 3.2 PARTIALLY VERIFIED (cannot cite with standard academic ID)

| Citation | Gap | Action required |
|---|---|---|
| **LatentQA / Choi et al. Transluce 2025** | No arXiv ID or DOI. Hosted as technical report/research post at transluce.org/user-modeling. Authors confirmed (Choi, Huang, Schwettmann, Steinhardt). Datasets/code exist on HuggingFace and GitHub. | Cite as `@techreport` with URL and access date, or await arXiv preprint. For the LatentQA *method* specifically, cite Pan, Chen, Steinhardt arXiv:2412.08686 instead. |

### 3.3 NOT-FOUND

No citation in the target list is wholly fabricated or has a wrong arXiv ID. All 10 arXiv IDs map to real papers. The most significant issues are:
- **Two venue corrections** (AI Sandbagging: ICLR 2025; ELEPHANT: ICLR 2026)
- **One content mismatch** (Gao & Kreiss: gender-bias methodology, not manipulation — but used correctly in brainstorm only)
- **One partial-only citation** (LatentQA/Choi: real but no arXiv ID)

---

## 4. Verification sources summary

| arXiv ID | Source consulted | Confirmed |
|---|---|---|
| 2603.25326 | arxiv.org/abs (raw HTML + metadata tags) + arxiv.org/html (paper body) + deepmind.google blog | ✓ |
| 2607.01242 | arxiv.org/abs (raw HTML + metadata tags) + aclanthology.org/2026.acl-long.959 | ✓ |
| 2411.02306 | arxiv.org/abs (raw HTML + metadata tags) + mlanthology.org NeurIPS 2024 entry | ✓ |
| 2503.10728 | arxiv.org/abs (raw HTML + metadata tags) + openreview.net/forum?id=odjMSBSWRt | ✓ |
| 2310.13548 | arxiv.org/abs (raw HTML + metadata tags) + proceedings.iclr.cc 2024 | ✓ |
| 2406.07358 | arxiv.org/abs (raw HTML + metadata tags) + proceedings.iclr.cc 2025 | ✓ |
| 2505.13995 | arxiv.org/abs (raw HTML + metadata tags) + openreview.net/forum?id=igbRHKEiAs | ✓ |
| 2510.12925 | arxiv.org/abs (raw HTML + metadata tags) | ✓ |
| 2509.04373 | arxiv.org/abs (raw HTML + metadata tags) + web search | ✓ |
| transluce.org/user-modeling | Direct page fetch (two passes) + web search for authors | Partial |
| 2412.08686 (LatentQA) | Web search | ✓ |
