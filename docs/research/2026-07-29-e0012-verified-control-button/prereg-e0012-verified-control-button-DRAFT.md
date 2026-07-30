# PRE-REGISTRATION SKELETON — E-0012 Verified Control Button (Calibration Axis)

**Status: DRAFT / PROPOSAL — NOT FROZEN**
**Document ID: prereg-e0012-verified-control-button-DRAFT**
**Author: Research/Design subagent (feature/45-e0012-research)**
**Date: 2026-07-29**

> ⚠️ THIS IS A PROPOSAL SKELETON. It becomes a frozen prereg ONLY after:
> (a) Owner approves at §5 (GPU program + compute + venue strategy), AND
> (b) Manager confirms no §5 item is pending, AND
> (c) An independent audit session verifies the prereg before boot.
>
> No GPU experiments may start before the prereg is frozen AND owner-approved.
> Do NOT modify frozen records (E-0005/E-0006/E-0009/E-0011) or the frozen C2b adjudicator.

---

## 0. Purpose and Relationship to Prior Work

This prereg governs the search for a **Verified Control Button** — a latent intervention that:
1. Passes the frozen behavioral adjudicator (reused verbatim from `prereg-c2b-adjudication.md §4`)
2. Beats the **bounded best-prompt baseline** with a fairly-constructed prompt comparator (see `prompt-fairness-protocol.md`)
3. Is obtained from a **non-trained, discovered** direction (to avoid Heyman-novelty collapse)
4. Produces a verdict of VERIFIED-CONTROL for at least one axis on at least one model

**Relationship to C2 claim:** C2 (NON_TRANSFER_GENERALIZED) is NOT modified. This experiment asks: "Is there a qualitatively different type of latent intervention — not naive CAA/ITI — that breaks the negative?" The C2 headline (naive off-the-shelf methods fail) stands regardless of this experiment's outcome.

**Taxonomy being evaluated:**
- **READ**: direction is representationally present (C1 facade ≥ threshold). Already established for deliberation and skepticism.
- **TRANSFER**: direction produces behavioral improvement over unsteered baseline (naive methods may achieve this). NOT currently established.
- **VERIFIED-CONTROL**: direction beats the bounded best-prompt baseline AND passes all protocol gates. This is what E-0012 searches for.

---

## 1. Research Question

**RQ-E0012:** Does any discovered, non-trained latent intervention on the Calibration (uncertainty_awareness) axis achieve VERIFIED-CONTROL — beating the bounded best-prompt baseline under the frozen C2b adjudicator with a fairly-constructed calibration-specific prompt comparator?

**Secondary RQ:** If VERIFIED-CONTROL is found, does it generalize (LOCAL / MODEL / TASK / GENERAL_CONTROL)?

---

## 2. Design Overview — Three-Stage Funnel

```
Stage 0: DEV Candidate Mining (EXPLORATORY, NO FROZEN ITEMS USED AS TEST)
    ↓ ≤ 3 promising (button, layer, α) triples
Stage 1: Frozen Positive Adjudication (PRE-REGISTERED, ONE-SHOT TEST)
    ↓ PASS / FAIL per button candidate
Stage 2: Transfer Stress Test (EXPLORATORY → classification)
    ↓ LOCAL / MODEL / TASK / GENERAL_CONTROL verdict
```

---

## 3. Button Families — Pre-Registered Candidates

The following button families are pre-registered for Stage 0 exploration. **Each must be non-trained** (direction derived by criterion independent of the behavioral outcome being adjudicated). The training/non-training status affects Heyman-novelty — see column.

| Button ID | Description | Direction derivation | Trained? | Heyman-novelty impact |
|---|---|---|---|---|
| BTN-CAL-PROBE | Linear probe direction for calibration confidence at target layer | Probe trained on synthetic (high-conf-correct, low-conf-wrong) pairs using cross-entropy on confidence logit; direction = probe weight vector | **Weakly trained** (probe trained on synthetic pairs, NOT on behavioral outcome) | LOW — probe is not outcome-optimized; PSR requires optimizing the steering direction toward a behavioral target |
| BTN-CAL-LOGIT-MARGIN | Direction derived from logit margin subspace: PCA of the diff (top-1 logit − top-2 logit) activations across calibration items | No training; direction from eigenvectors of Δlogit-margin representation matrix | **Non-trained** | NONE |
| BTN-CAL-SAE | SAE feature direction for uncertainty/confidence representation (if SAE available for target model) | Feature vector from a pre-trained SAE at target layer, selected by interpretability (feature active on uncertain outputs) | **Non-trained** (SAE pre-trained for general interpretability, not for our outcome) | LOW — SAE features are general-purpose; selecting one for calibration is a discovery step, not PSR |
| BTN-CAL-CONTRA-REEXTRACT | CAA direction re-extracted with calibration-specific contrastive pairs (high-Brier positive vs low-Brier negative examples) | Contrastive mean difference from calibration-labeled pairs | **Non-trained** (same family as CAA in C2b, but with calibration-specific pair selection) | MEDIUM — this is PSR-adjacent if the pair-selection was outcome-optimized. Must use fixed pair selection rule pre-specified in prereg, not post-hoc tuned. |
| BTN-CAL-RESIDUAL-PCA | PCA of the difference (steered_residual − unsteered_residual) at target layer, projecting onto the top-variance direction for calibration items | No training; PCA of activation differences | **Non-trained** | NONE |

**Exclusion rule:** Any button family requiring optimization of the direction vector on behavioral outcomes (e.g., gradient-based direction search on calibration score) is classified as **TRAINED** and must be clearly labeled as PSR-family. If a trained button wins, it is reported honestly as PSR-consistent and cited against Heyman. It is NOT labeled VERIFIED-CONTROL in the novel-contribution sense.

---

## 4. Frozen Adjudicator — Reused Verbatim

The statistical decision rule is **byte-identical** to `prereg-c2b-adjudication.md §4`:

**Pass criterion for axis a:**
```
(1) 98.33% CI of mean(d_i) EXCLUDES 0 (upward)    [Bonferroni-corrected, 3 axes]
(2) Point estimate mean(d_i) ≥ δ = 0.05
(3) Coherence ratio ≤ 1.5×
```

where `d_i = steer_i − prompt_i` and `prompt_i` is from the DEV-frozen best calibration prompt (not the generic best prompt from C2b).

**Bootstrap:** paired item-cluster, B ≥ 10000, items as clusters.

**Multiplicity:** Bonferroni over 3 axes (same as C2b). If Stage 1 tests only calibration axis, use α = 0.05 / 1 (single-axis); if all 3 axes, use α = 0.05 / 3 as before.

**The pass criterion for the prompt comparator** is also pre-specified: the prompt family for the Calibration Button is the 17-candidate family from `prompt-fairness-protocol.md §3`, with DEV selection rule as specified there.

---

## 5. Prompt-Fairness Comparator — Pre-Registered

**Reference:** `prompt-fairness-protocol.md` (same-date document).

**Pre-registered rules:**
1. Prompt comparator family: ≥ 16 authored calibration-specific prompts + 1 auto-optimized prompt = 17 total candidates.
2. DEV selection: best candidate by mean `1 − Brier` on DEV pool, frozen before TEST.
3. Button α selection: DEV-frozen from pre-registered α grid `{2, 4, 6, 8, 12, 16, 24}`.
4. Both selections frozen simultaneously before any TEST item is evaluated.
5. If the auto-optimized prompt outperforms the button on DEV, button is classified TRANSFER (not VERIFIED-CONTROL).

---

## 6. Item Pool — NEW (Anti-Forking-Paths)

**Critical:** Stage 1 uses a FRESH item pool, NOT the E-0005/E-0006 calibration items.

**Pre-registered item pool source** (to be finalized before freeze):
- **Option A:** TriviaQA validation split, calibration-labeled subset, different random seed and offset from E-0006
- **Option B:** SciQ test set (multiple-choice science questions with known difficulty + calibration behavior)
- **Decision rule:** Pool source selected BEFORE Stage 0 runs and frozen in the prereg. Stage 0 DEV exploration uses the EXISTING E-0005/E-0006 DEV items (already-seen; no new TEST contamination).

**Pool size:** N=80 calibration items (uncertainty_awareness axis), consistent with E-0006 structure.
**DEV/TEST split:** ~1/3 DEV (~26 items), ~2/3 TEST (~54 items), disjoint, same deterministic split rule as E-0006.

---

## 7. Stage-by-Stage Specification

### Stage 0 (Exploratory — DEV mining only)

- **Purpose:** Identify ≤ 3 promising (button_family, layer, α) triples on DEV items.
- **Data used:** E-0005/E-0006 DEV items (already seen; no TEST contamination of new pool).
- **Output:** Ranked list of candidates by DEV `1 − Brier` improvement over best DEV prompt.
- **Candidate count reported:** ALWAYS report how many (button_family, layer, α) combinations were tried; do not selectively report only the winner (anti-forking-paths discipline).
- **Cutoff rule:** Only candidates with DEV improvement ≥ δ = 0.05 over DEV best-prompt AND coherence ≤ 1.5× proceed to Stage 1. If zero candidates pass, declare NO_BUTTON_FOUND at Stage 0.

### Stage 1 (Frozen Adjudication — new pool, one-shot TEST)

- **Purpose:** Pre-registered adjudication on the new item pool.
- **Button candidates:** ≤ 3 from Stage 0 (pre-specified before TEST evaluation).
- **Multiplicity correction:** If M candidates advance from Stage 0 to Stage 1, Bonferroni-correct over M × n_axes comparisons. For M=1, n_axes=1: no additional correction needed beyond the per-axis criterion.
- **TEST use:** TEST items evaluated ONCE. No re-running, no post-hoc α adjustment.
- **Output:** Per-button verdict: PASS / FAIL. Zero passes → NO_BUTTON_FOUND.

### Stage 2 (Transfer Stress — exploratory, no new frozen adjudication)

Applies only if Stage 1 produces ≥ 1 PASS.

| Transfer dimension | Classification | Protocol |
|---|---|---|
| Same model, different random seed | REPLICATED | Re-run Stage 1 on new seed; must pass again |
| Different model (Qwen → Llama) | MODEL_GENERAL | Run on Llama with same button family (re-derive direction on Llama); if passes → MODEL |
| Different task (calibration → adjacent) | TASK_GENERAL | New calibration-adjacent task (TruthfulQA → HotpotQA); if passes → TASK |
| Prompt paraphrase robustness | PROMPT_ROBUST | Best-prompt comparator replaced by 4 paraphrase variants; if still PASS → PROMPT_ROBUST |
| Difficulty/length | LOCAL vs ROBUST | Hard items vs easy items |

**Stage 2 classification rule:**
- PASSES all 5 dimensions → **GENERAL_CONTROL** (strongest claim)
- PASSES model + task → **GENERALIZING**
- PASSES only original model → **LOCAL** (model-specific console contract)
- FAILS Stage 2 seed test → **UNRELIABLE** (not deployable)

---

## 8. Success / Kill Criteria (Pre-Registered Verdicts)

| Verdict | Condition | Paper implication |
|---|---|---|
| **NO_BUTTON_FOUND** | Zero candidates pass Stage 0 cutoff OR zero buttons pass Stage 1 | Boundary theorem is the negative: VERIFIED-CONTROL tier is empty under this search. Console should NOT expose a calibration slider. The READ/TRANSFER/VERIFIED taxonomy and evaluation discipline remain as the contribution. |
| **LOCAL** | Stage 1 PASS, Stage 2 fails model transfer | VERIFIED-CONTROL for Qwen2.5-7B only. Console contract scoped to specific model. |
| **GENERALIZING** | Stage 1 PASS, Stage 2 passes model + task | VERIFIED-CONTROL generalizes across tested models and tasks. Moderate console contract. |
| **BUTTON_FOUND_BUT_UNSAFE** | Stage 1 PASS but accuracy guard fails: accuracy(steer) < 0.9 × accuracy(unsteered), OR Brier decomposition shows gaming (reliability degrades while resolution inflates) | Button improves 1−Brier via a degenerate pathway. NOT deployed as console control. Reported as a safety caveat for calibration buttons. |
| **GENERAL_CONTROL** | Stage 1 PASS + all Stage 2 dimensions pass | VERIFIED-CONTROL is a general-purpose calibration button. Strongest console contract. |

---

## 9. Safety / Side-Effect Guards

### 9.1 Accuracy Guard (pre-registered, non-negotiable)

```
accuracy(steer) ≥ 0.9 × accuracy(unsteered_baseline)
```

Evaluated on the same TEST items as the calibration adjudication. This prevents the trivial "abstain on everything" solution from passing the Brier metric.

### 9.2 Brier Decomposition (required for Stage 1)

Per-item raw (confidence, correctness) pairs MUST be stored from the outset. Brier decomposition (reliability / resolution / uncertainty per Murphy 1973) must be computed and reported. A button that improves overall Brier by increasing confidence on correct items only (without improving calibration on uncertain items) is classified BUTTON_FOUND_BUT_UNSAFE if the reliability component worsens.

### 9.3 Coherence Gate (unchanged from C2b)

Steered mean repetition/degeneracy score ≤ 1.5× unsteered baseline. Cells above this bound are DISCARDED (same as frozen C2b adjudicator §3).

### 9.4 Non-Calibration Axis Protection

If the Calibration Button is applied to DEV items from the deliberation or skepticism axes, it must NOT degrade those axes beyond δ = −0.05 (i.e., the button should be axis-specific, not a general degrader). This is a cross-axis coherence check, reported but NOT part of the pass/fail criterion.

---

## 10. Forking-Paths Prevention

| Forking-path risk | Prevention |
|---|---|
| Cherry-picking the best button family post-hoc | Report ALL candidates tried in Stage 0, with DEV scores |
| Adjusting Stage 1 analysis after seeing TEST | Pre-specify analysis script BEFORE Stage 1 runs; code commit hash in prereg |
| Re-running Stage 1 after a FAIL | Stage 1 is ONE-SHOT. No second attempt without a new freeze and owner approval |
| Changing the prompt comparator after seeing button performance | Prompt family authored and frozen before ANY Stage 0/1 gens; no post-hoc additions |
| Adding new axes post-hoc | Only axes specified in Stage 0 scope are allowed in Stage 1 |
| Outcome-driven item pool selection | Pool source selected and frozen before Stage 0 |

---

## 11. Expected Timeline (once owner approves §5)

| Step | Duration | Notes |
|---|---|---|
| Finalize item pool source | 1–2 days | Human + Manager decision |
| Author 16+ prompt family | 1 day | Human-authored (prompt-fairness protocol) |
| Freeze E-0012 prereg | 1 day | After Manager + owner approval; independent audit |
| Stage 0 GPU run (DEV mining) | 2–3 hours on A800 | Conservative track |
| Stage 0 analysis + candidate selection | 1 day | Doc-only analysis; candidates frozen |
| Stage 1 GPU run (new pool adjudication) | 2–3 hours on A800 | Conservative track |
| Stage 1 independent hostile audit | 1–2 days | Before any verdict is acted on |
| Stage 2 (if PASS) | 1–4 hours on A800 | Depending on transfer scope |
| Paper integration | 2–3 days | After verified result |

**Total wall time from owner approval to paper-ready result: ~1–2 weeks** (conservative).

---

## 12. Owner-Gated Items (§5 items — NONE of these may proceed autonomously)

1. **GPU program approval** (Stage 0–2 boot) — requires explicit owner §5 sign-off
2. **Compute platform selection** — borrowed A800 (if approved) vs cloud instance (requires budget approval)
3. **New item pool source selection** — owner must confirm the pool is appropriate
4. **Venue strategy** — does a verified positive change the target venue? (owner decision)
5. **Pre-registered prompt family authorship** — requires human-authored prompts (not auto-generated; maintains prompt-fairness integrity)

---

## 13. What the Paper Gains from Each Verdict

| Verdict | Paper value | Novelty impact |
|---|---|---|
| NO_BUTTON_FOUND | Strengthens boundary theorem: VERIFIED-CONTROL is hard to achieve even with targeted search. "We searched and the tier is empty for calibration." | High value for the evaluation-discipline contribution |
| LOCAL | First verified positive: console CAN expose a calibration slider for this model. New READ/TRANSFER/VERIFIED classification is empirically populated. | High novelty for taxonomy + positive example |
| GENERALIZING or GENERAL_CONTROL | Console design has an evidence-based calibration control across models/tasks. Significant positive finding. | Highest novelty; directly upgrades the paper's affirmative contribution |
| BUTTON_FOUND_BUT_UNSAFE | New safety finding: calibration buttons can pass behavioral metrics via degenerate pathways. Brier decomposition is the necessary safeguard. | Medium novelty; important safety caveat |

---

## 14. Freeze Checklist (for Manager + Owner, when ready)

- [ ] Item pool source specified, frozen, documented
- [ ] Prompt comparator family (≥ 16 prompts) authored and committed
- [ ] Button families and exclusion rule confirmed
- [ ] Stage 0 scope (model × layer × family × α) confirmed
- [ ] New DEV/TEST split rule for Stage 1 pool confirmed
- [ ] Analysis script committed to branch before Stage 1 runs
- [ ] Commit hash recorded in freeze block
- [ ] Independent audit of prereg completed
- [ ] Owner §5 GPU approval obtained
- [ ] Status changed from DRAFT to FROZEN

---

*This prereg skeleton was produced in a doc-only, zero-GPU, non-gated research/design pass per D-0057. No experiments were run, no frozen records were modified, no TEST data was accessed.*
