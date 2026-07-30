# Compute / Cost Estimate — E-0012 Verified Control Button

**Status: DRAFT / PROPOSAL — 2026-07-29**
**Author: Research/Design subagent (feature/45-e0012-research)**
**Discipline: Doc-only; no experiments; estimates based on E-0006/E-0011 benchmarks**

---

## Baseline Reference (from ledger)

From E-0006 / E-0011 benchmark data (frozen artifacts):
- **~11,365 generations per cell** (1 method × 1 model × full 3-axis adjudication: N=60/60/80, k=5, α grid=7 values, DEV+TEST)
- **A800 GPU1** (borrowed): ~20–30 min per cell at 7B fp16 with batch_size=16, max_new_tokens=64
- DEV selection: ~3–5 min per cell additional (DEV is ~1/3 of items, prompt selection = run 16 prompts × DEV items)

---

## Stage 0: DEV Candidate Mining

**Purpose:** Search over (model × layer × button-family × α) space on DEV items only to find promising button candidates that could pass the Stage 1 frozen adjudication.

**Scope:** Calibration button only (D-0057 priority).

### Stage 0 Design Parameters

| Parameter | Conservative | Aggressive |
|---|---|---|
| Models | 1 (Qwen2.5-7B) | 2 (Qwen + Llama) |
| Button families to try | 3 (probe-direction, logit-margin, SAE-feature) | 6 (above + PCA-subspace, contrastive-reextract, layer-combination) |
| Layer sweep | 5 layers (±2 around C1 optimal) | 12 layers (full middle-third of network) |
| α candidates per layer | 7 (same grid {2,4,6,8,12,16,24}) | 10 (extended grid) |
| DEV items per axis | 20 (calibration axis only, ~1/3 × 80 = 26 items) | 26 (full DEV pool) |
| k samples per item (DEV) | 3 (faster, noisier) | 5 (full k) |

### Stage 0 Generation Count Estimate

**Conservative:**
- 1 model × 3 button families × 5 layers × 7 α × 26 DEV items × 3 samples = 8,190 generations
- Plus 16 authored prompt candidates × 26 DEV items × 3 samples = 1,248 prompt-baseline gens
- **[NEW — F-05] Auto-prompt optimization (Stage 0 DEV):** N_cand=50 × 26 DEV items × k=3 = 3,900 screening gens; + winner × 26 × k=5 = 130 re-eval gens = **4,030 gens**
- **Total Stage 0 conservative: ~13,468 generations**
- At A800 speeds (~400 gens/min with batch_size=16, max_new_tokens=64): ~34 minutes
- **Wall time: ~40–55 min (including overhead)**

**Aggressive:**
- 2 models × 6 button families × 12 layers × 10 α × 26 DEV items × 5 samples = 187,200 generations
- Plus 17 prompt candidates × 26 DEV items × 5 samples = 2,210 prompt gens
- Plus auto-prompt optimization (aggressive): N_cand=50 × 26 × k=5 × 2 models = ~13,000 gens
- **Total Stage 0 aggressive: ~202,400 generations**
- At A800 speeds: ~8.5 hours
- **Wall time: ~11–13 hours (including overhead, checkpointing, 2-model overhead)**

**Recommended Stage 0 scope (balanced):**
- 1 model (Qwen2.5-7B) × 4 button families × 8 layers × 7 α × 26 DEV items × 3 samples = 43,680 gens
- Plus auto-prompt optimization: ~4,030 gens
- **Wall time: ~2.5–3.5 hours on A800 GPU1**

---

## Stage 1: Frozen Positive Adjudication

**Purpose:** Once Stage 0 identifies ≤3 promising (button, layer, α) candidates, run the FULL frozen adjudicator on a NEW item pool with a NEW DEV/TEST split. This is the single pre-registered adjudication (one-shot TEST).

**New item pool required:** Cannot reuse E-0005/E-0006 items (forking-paths prevention). A fresh draw from TriviaQA-calibration-subset or a calibration-specific task set.

### Stage 1 Design Parameters

| Parameter | Conservative | Aggressive |
|---|---|---|
| Models | 1 (Qwen2.5-7B) | 2 (Qwen + Llama) |
| Button candidates from Stage 0 | 1 (best) | 3 (top-3) |
| Item pool | Calibration axis only (N=80, k=5, same structure as C2b) | All 3 axes (N=60/60/80, k=5, full C2b structure) |
| Prompt comparator family | 17 candidates (DEV selection) | 17 candidates + auto-optimized (18 total) |
| α | 1 value (DEV-frozen) | 1 value (same) |

### Stage 1 Generation Count Estimate

**Conservative (1 model, 1 button, calibration axis only):**
- Button gens: 1 model × 1 button × 80 items (TEST + DEV) × 5 samples × 7 α (DEV sweep) = 2,800 gens
- Prompt gens: 17 prompts × 80 items × 5 samples = 6,800 gens (DEV + TEST)
- Unsteered baseline: 80 items × 5 samples = 400 gens
- **[NEW — F-05] Auto-prompt optimization (Stage 1 new pool DEV re-run):** N_cand=50 × 26 new DEV items × k=3 = 3,900 screening gens; + winner re-eval k=5 = 130 gens = **4,030 gens**
  - *(Rationale: the auto-optimized prompt is re-derived on Stage 1's new pool DEV for distribution symmetry — see prereg §5-B. The final winner is one of the 17 candidates in the 6,800-gen prompt budget above; the 4,030 gens here cover the screening phase before the winner is known.)*
- **[NEW — F-05] Brier raw storage:** per-item (confidence, correctness) pairs — no additional gens (stored from existing runs; data collection requirement, not additional GPU compute)
- **Total Stage 1 conservative: ~14,030 generations** (vs original ~10,000)
- **Wall time: ~35–40 min on A800**

**Aggressive (2 models, 3 buttons, all 3 axes = 3× size of C2b):**
- Button gens: 2 models × 3 buttons × (60+60+80) items × 5 samples × 7 α = 3 × 11,200 × 3 = 100,800 gens
- Prompt gens: 18 prompts × (60+60+80) items × 5 samples × 2 models = 90,000 gens
- Auto-prompt optimization: ~8,060 gens (2 models)
- **Total Stage 1 aggressive: ~198,860 generations** (≈ 17× E-0006)
- **Wall time: ~6–8 hours on A800**

**Recommended Stage 1 scope:**
- 1 model × 1–2 buttons × calibration axis + 1 other axis × k=5 = ~20,000–30,000 gens + ~4,030 gens auto-prompt
- **Wall time: ~1.5–2.5 hours on A800 GPU1**
- Feasible within borrowed-A800 constraints

---

## Stage 2: Transfer Stress Test

**Purpose:** Classify the button as LOCAL / MODEL / TASK / GENERAL_CONTROL by testing generalization.

### Stage 2 Transfer Dimensions

| Dimension | Test | Conservative | Aggressive |
|---|---|---|---|
| **Model** | Qwen → Llama-3-8B (same button family) | 1 new model cell | 2 new model cells (+ Mistral-7B if available) |
| **Task** | Calibration task → adjacent task (e.g., TruthfulQA → HotpotQA confidence) | 1 new task | 3 new tasks |
| **Prompt family** | Original prompt → paraphrase set (4 variants) | 4 paraphrase variants | 8 variants |
| **Context length** | Short items → medium items (>200 word context) | +1 item pool | +2 item pools |
| **Difficulty** | Easy items → hard items (lower baseline accuracy) | 1 hard subset | 2 difficulty bins |

### Stage 2 Generation Count Estimate (Calibration Button only)

**Conservative (model transfer + 1 task + paraphrases):**
- Model transfer: 1 new model × N=80 × k=5 = 400 button gens + 400 baseline gens
- Task transfer: 1 new task × N=80 × k=5 = 400 button gens + 400 baseline gens
- Paraphrase stress: 4 prompt variants × N=80 × k=5 = 1,600 gens
- **Total Stage 2 conservative: ~3,200 generations**
- **Wall time: ~8–15 min on A800**

**Aggressive (full 5-dimension stress):**
- All dimensions: ~50,000–80,000 generations
- **Wall time: ~3–4 hours on A800**

---

## Summary: Total Generation Counts and Wall Times

> ⚠️ **Revised 2026-07-30 (F-05):** Auto-prompt optimization cost added to Stage 0 and Stage 1. See revision log below.

| Scenario | Stage 0 | Stage 1 | Stage 2 | Total gens | A800 GPU1 wall time |
|---|---|---|---|---|---|
| **Conservative** | 13,468 | 14,030 | 3,200 | **~30,698** | **~2.0–2.5 hours** |
| **Recommended** | 47,710 | 29,030 | 20,000 | **~96,740** | **~4.5–7 hours** |
| **Aggressive** | 202,400 | 198,860 | 80,000 | **~481,260** | **~20–24 hours** |

**Conservative track vs original estimate:**
- Original: ~22,640 gens / ~1.5–2h
- Revised: ~30,698 gens / **~2.0–2.5h**
- Delta: +8,058 gens (~36% increase in gens; ~25–30 min additional wall time)
- **Assessment:** Conservative track remains within borrowed-A800 etiquette at the boundary (~2–2.5h). The original ~2h estimate understated the cost by omitting auto-prompt screening. No §5 budget escalation is required for this revision; however, Manager should flag to owner that the actual session is more likely to run ~2.0–2.5h than the originally stated ~1.5h.

---

## A800 Feasibility Assessment

### Borrowed A800 Etiquette Constraints (from D-0049, RUN_ON_A800.md)
- GPU1 only (CUDA_VISIBLE_DEVICES=1), scope ~/cc_l0
- NEVER shutdown the machine
- PUSH the exact run commit BEFORE cleanup
- Stop if no free GPU (GPU0 occupied)
- Full session: E-0006 used ~4 cells × 25 min ≈ 2 hours; E-0011 used ~4 seeds × ~4 cells × 25 min ≈ 8 hours

### Verdict

| Scenario | Fits A800 (borrowed)? | Comment |
|---|---|---|
| Conservative | **YES (boundary)** — ~2.0–2.5 hours | Single GPU1 session; at the ~2h etiquette boundary after auto-prompt cost added; marginally within borrowed-A800 constraints |
| Recommended | **MARGINAL** — ~4.5–7 hours | Fits if GPU1 is consistently free; risk of interruption |
| Aggressive | **NO** — 20–24 hours | Too long for borrowed-machine etiquette; needs owner-controlled compute |

**D-0057 ruling confirms:** the GPU search program is §5-gated. The conservative track is within borrowed-A800 etiquette IF the owner approves GPU boot. The recommended and aggressive tracks likely require owner-controlled compute or a cloud instance.

---

## Budget Estimate (GPU Hours and Cost)

| Scenario | A800 GPU-hours | Approximate cost (cloud A100/A800 ~$2–3/hr) |
|---|---|---|
| Conservative | ~2 GPU-hours | **~$4–6** |
| Recommended | ~5–6 GPU-hours | **~$10–18** |
| Aggressive | ~20+ GPU-hours | **~$40–60+** |

**These are very modest costs** compared to the research value. The binding constraint is not money but the borrowed-A800 etiquette and the §5 owner-gating requirement.

---

## Critical Dependency: New Item Pool Construction

Stage 1 requires a **new item pool** (forking-paths prevention). The current calibration item pool (TriviaQA / TruthfulQA subsets from E-0005/E-0006) CANNOT be reused for the Stage 1 adjudication — Stage 0 will be run against DEV items that overlap with this pool.

**Recommendation:** Stage 0 uses the EXISTING E-0005/E-0006 DEV items (already seen in earlier analyses) for exploration. Stage 1 uses a FRESH item draw from:
- TriviaQA validation set (different split)
- OR a new calibration-specific dataset (e.g., SciQ, ARC-Challenge with calibration labeling)
- Pool size: N=80 calibration items, N=60 skepticism items (if expanding to skepticism axis)

The new item pool must be documented and frozen BEFORE any Stage 1 generation begins. This is an E-0012-specific prereg requirement.

---

## Summary Recommendation to Owner

The **conservative track** (Stage 0 DEV mining → Stage 1 adjudication → Stage 2 transfer, calibration axis, Qwen2.5-7B primary) is:
- Technically feasible on borrowed A800 within ~2.0–2.5 hours total (revised upward from original ~1.5–2h estimate after auto-prompt cost added)
- Affordable (~$4–6 equivalent if cloud; revised estimate adds <$2)
- Scientifically sufficient for the initial VERIFIED-CONTROL claim

The **recommended track** adds a second model and a second axis at modest additional cost and is still within borrowed-A800 etiquette for a scheduled session.

The **aggressive track** needs owner compute. If the conservative or recommended track finds a button, the aggressive track can be a follow-up robustness study.

**§5 owner-gated items before any GPU boot:**
1. Approval of Stage 0–2 GPU program
2. Selection of which A800 session to use (or cloud compute approval)
3. Confirmation of new item pool source
4. Freeze of E-0012 prereg (document 4)

---

## Revision Log — 2026-07-30 (F-05)

**Responding to pre-run critic review finding F-05** (MAJOR: auto-optimized prompt Stage 1 re-optimization cost omitted from conservative estimate).

**Changes made:**
- Added "Auto-prompt optimization" rows to Stage 0 and Stage 1 generation counts (APE-variant: N_cand=50 × ≤26 DEV items × k=3 = 3,900 screening gens; + winner k=5 re-eval = 130 gens; ≈ 4,030 gens per stage).
- Added note that Brier raw storage (per-item confidence/correctness pairs) has zero additional GPU compute cost — it is a data collection and storage requirement only.
- Updated summary table: conservative total revised from ~22,640 to ~30,698 gens; wall time revised from ~1.5–2h to ~2.0–2.5h.
- Updated A800 Feasibility table: conservative track re-labeled "YES (boundary)" at ~2.0–2.5h.
- Updated Summary Recommendation: conservative track wall time corrected.

**Assessment**: The revised conservative track (~2.0–2.5h) remains within borrowed-A800 etiquette at its boundary. The additional cost (~8,058 gens / ~25–30 min) does not cross the threshold requiring §5 budget re-escalation. Manager should inform owner of the revised estimate before GPU session scheduling.
