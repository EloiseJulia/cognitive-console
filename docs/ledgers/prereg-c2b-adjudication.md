# PRE-REGISTRATION — C2b Behavioral-Gap Adjudication (RQ2 core)

- **Status:** DRAFT — thresholds pending human confirmation, then FROZEN. Once FROZEN, the success/kill
  criteria and analysis plan MUST NOT change after seeing results (owner directive, AI-Instruction Part I §7/§12).
- **Adjudicates:** Claim **C2b** — "on tasks with headroom, latent steering reaches a BEHAVIORAL outcome
  beyond the best bounded-prompt outcome." A qualified NO → pivot to Plan D (RQ1-core measurement paper).
- **Why re-run:** the first C2b probe (E-0004) used audit-rejected lexical/length proxies that saturated the
  ceiling (~0.88–1.0) — INVALID evidence. This pre-registration fixes the instrument before adjudicating.

---

## 1. Instrument fixes (all four axes' issues addressed)

1. **Eliminate the ceiling effect** — replace saturating lexical proxies with **behavioral-OUTCOME tasks
   that have real headroom** and require genuine capability change, not keyword presence:
   - **deliberation** → GSM8K-style multi-step arithmetic/reasoning: measure **accuracy** (0–1) with headroom.
   - **skepticism** → false-premise / sycophancy items: measure **false-premise-rejection rate**.
   - **uncertainty_awareness** → calibration items (questions the model often gets wrong): measure **ECE**
     (expected calibration error) or appropriate-hedging-on-wrong-answers rate.
2. **Orthogonal, NON-lexical proxy** — the measure is a TASK OUTCOME (accuracy / rejection rate / calibration),
   NOT a count of words the steering vector could trivially inject. Scoring is done by a rule/answer-key
   (deterministic), not by keyword counting on the steered text.
3. **Multi-sample + CI** — N≥20 items per axis; for stochastic decoding, k≥5 samples per item; report
   mean + **bootstrap 95% CI** for every cell (prompt-ceiling, steer-only per alpha, conflict).
4. **Alpha sweep** — sweep α over a documented grid (e.g. {2,4,6,8,12,16,24}); report the outcome-vs-α curve
   AND a **coherence gate** (see §3) so "gains" from degenerate text are excluded.
5. **Drop focus** — focus has no stable CAA direction / overshoots; excluded from this adjudication.

Bounded-prompt ceiling = best outcome over the full 16 authored strong prompts per axis (labeled "best-of-16
static, NOT OPRO — a conservative under-estimate of prompt reach"). Optionally add a small OPRO-style
paraphrase expansion if cheap; otherwise document the limitation.

## 2. Design
- Model: Qwen2.5-7B-Instruct (GPU fp16), same C1 chosen non-degenerate layer per axis (from E-0003).
- Cells per axis: (a) prompt-ceiling = best-of-16 strong prompts; (b) steer-only at each α; (c) conflict
  (prompt pushes one way, steer opposes). Each cell: N items × k samples → mean + bootstrap CI.
- Steering vector = C1's re-derived CAA unit direction at the chosen layer (same extraction/split as E-0003).

## 3. Coherence gate (prevents "steering wins by breaking the model")
A steered cell only counts if outputs remain coherent: pre-registered check = (mean output perplexity or a
simple degeneracy/ repetition score) stays within a factor of the unsteered baseline (exact bound set at
freeze). Gains achieved only above the coherence bound are DISCARDED.

## 4. PRE-REGISTERED SUCCESS / KILL CRITERIA  (fill numbers, then FREEZE — do not change after results)

Let, per axis a, `prompt_best(a)` = best-of-16 prompt outcome (with CI), and `steer_best(a)` = best coherent
steer-only outcome over the α sweep (with CI). Define a MEANINGFUL margin δ (pre-registered), e.g. δ = 0.05
in outcome units (or a standardized effect size — set at freeze).

- **RQ2 SIGNAL EXISTS (SUCCESS → continue the dual-channel line):** on **≥1** of {deliberation, skepticism,
  uncertainty}, `steer_best(a) − prompt_best(a) ≥ δ` with **non-overlapping 95% CIs**, AND the winning cell
  passes the coherence gate. (Report all three axes regardless.)
- **QUALIFIED NULL (KILL → pivot to Plan D):** on **NONE** of the three axes does steer exceed the prompt
  ceiling by δ with non-overlapping CIs under the coherence gate. → RQ2 core behavioral-gap claim is reported
  as an honest NEGATIVE; pivot to Plan D (RQ1-core measurement/diagnostic CHI paper). C1 evidence retained.
- **Conflict (secondary, descriptive only, NOT a success gate):** report which channel wins the conflict cell
  per axis + α; informative but does not by itself decide the adjudication.

**Proposed numbers to freeze (Manager draft — pending human confirm):**
- N items/axis = 30; k samples/item = 5 (greedy for accuracy tasks + 5 sampled for calibration where noted).
- α grid = {2, 4, 6, 8, 12, 16, 24}.
- δ (meaningful margin) = **0.05** outcome units (accuracy / rejection-rate / (1−ECE)).
- Coherence bound = steered mean repetition/degeneracy score ≤ 1.5× unsteered baseline (else cell discarded).
- Decision uses **non-overlapping 95% bootstrap CIs** AND margin ≥ δ.

## 5. Budget (capped)
- Local first: implement qualified instrument + CPU/1.5B smoke + independent audit (free).
- Then ONE A800 allocation (<70GB disk, wipe after) for the 7B adjudication. Adjudicate immediately against
  the frozen criteria. No second GPU run without a fresh human decision.

## 6. Freeze block
- protocol_frozen: **NO (pending human confirmation of §4 numbers)** → set to YES + date + commit hash on freeze.
- After freeze: instrument, tasks, proxy definitions, α grid, δ, coherence bound, and decision rule are LOCKED.
