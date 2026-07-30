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
- Plus 16 prompt candidates × 26 DEV items × 3 samples = 1,248 prompt-baseline gens
- **Total Stage 0 conservative: ~9,440 generations**
- At A800 speeds (~400 gens/min with batch_size=16, max_new_tokens=64): ~24 minutes
- **Wall time: ~30–45 min (including overhead)**

**Aggressive:**
- 2 models × 6 button families × 12 layers × 10 α × 26 DEV items × 5 samples = 187,200 generations
- Plus 17 prompt candidates × 26 DEV items × 5 samples = 2,210 prompt gens
- **Total Stage 0 aggressive: ~189,400 generations**
- At A800 speeds: ~7.9 hours
- **Wall time: ~10–12 hours (including overhead, checkpointing, 2-model overhead)**

**Recommended Stage 0 scope (balanced):**
- 1 model (Qwen2.5-7B) × 4 button families × 8 layers × 7 α × 26 DEV items × 3 samples = 43,680 gens
- **Wall time: ~2–3 hours on A800 GPU1**
- This is affordable within the borrowed-A800 etiquette (E-0006 used ~25 min/cell × 4 cells = ~2 hours)

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
- **Total Stage 1 conservative: ~10,000 generations** (0.9× one C2b cell)
- **Wall time: ~20–25 min on A800**

**Aggressive (2 models, 3 buttons, all 3 axes = 3× size of C2b):**
- Button gens: 2 models × 3 buttons × (60+60+80) items × 5 samples × 7 α = 3 × 11,200 × 3 = 100,800 gens
- Prompt gens: 18 prompts × (60+60+80) items × 5 samples × 2 models = 90,000 gens
- **Total Stage 1 aggressive: ~190,800 generations** (≈ 17× E-0006)
- **Wall time: ~6–8 hours on A800**

**Recommended Stage 1 scope:**
- 1 model × 1–2 buttons × calibration axis + 1 other axis × k=5 = ~20,000–30,000 gens
- **Wall time: ~1–2 hours on A800 GPU1**
- Feasible within borrowed-A800 constraints (matches E-0006 footprint)

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

| Scenario | Stage 0 | Stage 1 | Stage 2 | Total gens | A800 GPU1 wall time |
|---|---|---|---|---|---|
| **Conservative** | 9,440 | 10,000 | 3,200 | **~22,640** | **~1.5–2 hours** |
| **Recommended** | 43,680 | 25,000 | 20,000 | **~88,680** | **~4–6 hours** |
| **Aggressive** | 189,400 | 190,800 | 80,000 | **~460,200** | **~18–22 hours** |

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
| Conservative | **YES** — 1.5–2 hours | Single GPU1 session; matches E-0006 footprint |
| Recommended | **MARGINAL** — 4–6 hours | Fits if GPU1 is consistently free; risk of interruption |
| Aggressive | **NO** — 18–22 hours | Too long for borrowed-machine etiquette; needs owner-controlled compute |

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
- Technically feasible on borrowed A800 within ~2 hours per stage
- Affordable (~$4–6 equivalent if cloud)
- Scientifically sufficient for the initial VERIFIED-CONTROL claim

The **recommended track** adds a second model and a second axis at modest additional cost and is still within borrowed-A800 etiquette for a scheduled session.

The **aggressive track** needs owner compute. If the conservative or recommended track finds a button, the aggressive track can be a follow-up robustness study.

**§5 owner-gated items before any GPU boot:**
1. Approval of Stage 0–2 GPU program
2. Selection of which A800 session to use (or cloud compute approval)
3. Confirmation of new item pool source
4. Freeze of E-0012 prereg (document 4)
