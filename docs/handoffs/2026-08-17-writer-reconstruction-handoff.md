# Writer Handoff — Narrative Reconstruction (two-population → B-frame method-first)

- **Date:** 2026-08-17
- **Author:** Writer session (paper-only; not Manager, no scheduling/merge/experiment authority)
- **Branch:** `feature/writing-reconstruction-completeness`
- **Base (clean):** `3433455` → **HEAD:** `06c8ba3` (18 commits, all paper-only, **not pushed / not merged**)
- **File touched:** `docs/paper/main.tex` only (+ this handoff). **No** table/figure/number/Method-data/Results-data artifact was edited.
- **Build:** `docs/paper/build/main.pdf`, **20 pp, 0 undefined cites/refs** on every commit.
- **Owner authorizations used this session:** (1) reframe narrative to two-population then B-frame; (2) title change to "Internal-Signal Controls"; (3) self-dispatch of hostile-audit subagents (explicit owner instruction, overriding the writer "no-subagent" default).

---

## 1. What changed (narrative reconstruction only)

**Trigger:** advisor critique — the pre-reconstruction paper effectively "set a strict self-authored gate, then concluded the slider is no good," a strawman with weak construct validity and thin community significance.

**Two moves, in order:**

### Move 1 — two-population reframe
- Central question shifted from "should you add the slider" to **"a latent slider is good *for whom*, against *which* alternative"**: everyday user (values **convenience**) vs proficient user = *can write a strong prompt* (demands **warranted quality gain**).
- Two comparators operationalize the two populations: **best-of-set prompt** (proficient ceiling→now "realistic alternative") and **average prompt** (everyday user).
- Opening scenario: two people (Alex everyday / Priya proficient). Four convenience facets named to match the parallel user-study session: **Effort / Accessibility / Discoverability / Willingness-to-use**.

### Move 2 — B-frame (center of gravity flip)
- Primary contribution is now the **evaluation method** for deciding whether a readable internal signal deserves to be an interface control; the **0/12 negative is a demonstrating case**, not the endpoint.
- Contributions reordered: **C1 = evaluation method** (design-scoped to *internal-signal controls*, beyond latent steering), **C2 = five-field record**, **C3 = worked/audited case study** (0/12 + positive control shows discrimination).
- New Discussion subsection **"What Transfers Beyond This Case"** (community significance; method outlasts the technique-specific verdict).
- Title: **"Convenient or Warranted? Evaluating Internal-Signal Controls for Everyday and Proficient Users."**

### Supporting edits
- Terminology unified: retired "contract" (→ procedure/record); "expert" → **"proficient user"** (defined = can write a strong prompt).
- Construct grounding: Zamfirescu-Pereira used for non-expert prompting difficulty (as **proxy/assumption**, not asserted fact).
- Strawman-hardening: retired "ceiling" (implied absolute upper bound) → "realistic alternative"; added a **bounded-claim** paragraph in Limitations (strong prompt is a 16-candidate bounded comparator, not an upper bound; finding is narrow; **not** evidence that latent sliders are "not worth building" or valueless for proficient users — expression cost, discoverability, continuous adjustment, composition untested).
- Positioning Summary rewritten to state novelty as **combination + unit of analysis + evidence-tier binding**, explicitly disclaiming "first comparison / first gap."
- Language-rhythm pass (split long sentences, reduced em-dash stacking; no factual change).

---

## 2. Evidence boundaries held (verified by two hostile audits)

- Frozen **0/12** model×method×axis no-pass intact; **no passing latent positive control** retained.
- **PSR / E-0009** kept **Qwen-only, single-seed, exploratory, valid_for_paper=false**; dropped from Contributions but still present, fully caveated, in Results/Abstract/Limitations; **not** folded into "the twelve."
- **deliberation** stays honest "measurement floored (64-token) / being re-measured" — **never** written as equivalence (prior equivalence claim remains rolled back at base `3433455`).
- **B1** positive control = decision-rule discrimination only, **not** latent-steering efficacy.
- **C1 (READ/facade)** and **C4 (social axis)** remain exploratory; not promoted to confirmatory core.
- **Pending items leak nothing:** average-prompt arm and user study appear only as marked pending slots / planned study with **zero data, no direction**.
- Prior-work credit intact (AxBench 0.894/0.239, Basu, Bo unscaffolded-prompt baseline); Golden Gate neutral; no "first" claims.

---

## 3. Audit trail (self-dispatched, per owner instruction)

1. **Full hostile audit** of `3433455..dc3ac16` → **BLOCKED** (1 BLOCKER: exploratory PSR folded into the confirmatory "twelve" headline; +2 MAJOR, +3 MINOR). All fixed in `719aeef`.
2. **Targeted re-audit** `dc3ac16..719aeef` → **MERGEABLE** (all 5 closed, no regressions).
3. **B-frame hostile audit** `d8b0d70..acc52b9` → **PASS-WITH-MINORS**. F1/F2 (method generalization in indicative "applies to any interface"), F3 (Abstract gap-claim), F4 (B1 caveat) fixed in `248aefd`; novelty positioning strengthened in `06c8ba3`.

Negative result confirmed **not** diluted; body confirmed **not** contradicting the method-first framing.

---

## 4. Open risks (structural — cannot be closed by wording; need data/decisions)

These are honestly recorded, not papered over:
1. **Construct validity of the two-population operationalization** (best=proficient realistic alternative; average=novice proxy) — both are asserted/assumption, validated only by the pending user study.
2. **Assay insensitivity** — no passing latent positive control ⇒ cannot separate "steering weak" vs "assay weak"; the negative is technique-scoped.
3. **Promissory / contribution-inflation risk** — the everyday-user half rests on a planned study + pending arm; a reviewer may read C1 (proposed method) elevated above C2 (the one supported result) as "selling a null as a win." Mitigated by honest B1/scope caveats, not eliminated.
4. **Method-generalization is an argument, not a tested result** — only run on latent steering.

Top-3 hostile CHI/IUI rejection risks (from B-frame audit): (i) primary contribution is an unvalidated generalization; (ii) gap-claim novelty vs AxBench/Basu/model-cards/Bo; (iii) proposed framework elevated above the one solid empirical result.

---

## 5. Three to-dos for the Manager

### TODO-1 — Ledger sync (Manager ledger-maintenance duty; **do not** ask the writer to edit ledgers)
`claim-map.yaml` / `claim-ledger.md` **C3** still reads "latent-control affordances," but the paper now frames the method for **internal-signal controls (any technique)**. Text side already downgraded the generalization to an **asserted design argument** (not validated). Sync C3 to record the internal-signal generalization as **asserted design scope, valid_for_paper=false-as-validated**, so ledger ↔ manuscript match. Owner has already approved the framing direction (title instruction); the ledger write itself is Manager's.

### TODO-2 — Data fold into pending slots (needs owner fold-gate; artifacts on a separate branch)
- **average-prompt comparator arm:** branch `feature/avg-prompt-comparator @ 4a59d8b`, `valid_for_paper=false`, prereg `docs/specs/avg-prompt-comparator-prereg.md`, two hostile audits clean. Qwen-only (Llama arm not run). Writer independently verified artifacts are readable from the writing worktree and re-derived CAA-skepticism numbers.
  - **Fold cautions (writer-verified):** (a) deliberation `avg−best` must use the **512-token repair** like-for-like value **−0.012**, NOT the handoff's `+0.828` (that field is `avg512_minus_frozen_best64` = a 64-token floor artifact); (b) `secondary_drop_best15` **PASSES** in CAA skepticism (+0.138, CI [+0.0003,+0.278]) — must be reported honestly as secondary/fragile/single-cell, **never** as "steering helps everyday users"; (c) uncertainty cells are missingness-limited (fmt≈0.456); (d) ITI deliberation @512 is **coherence-FAIL** (deg 0.1975>0.163) → invalid artifact, **not** real harm; (e) **no primary avg16 cell has a CI excluding zero** — do not claim significant everyday-user gain; Qwen-only, no cross-model.
  - Slots ready in `main.tex`: `PENDING_AVERAGE_PROMPT_SLOT` (Method + Results).
- **User study (10 proficient / 10 everyday):** owned by a parallel session; **zero human data**, prereg DRAFT, no recruitment/ethics authorization. Slot ready: `PENDING_USER_STUDY_SLOT`. Owner still to decide (user-study Q4) whether B (user-study data) is in scope before the submission deadline — that decision gates whether that session invests full protocol-freeze + power calc.
- **Reminder:** folding either dataset into the manuscript is an owner fold-gate action (valid_for_paper=false + exploratory→confirmatory concerns). Writer will not fold without that gate.

### TODO-3 — Merge decision
Both audits clear (BLOCKED→MERGEABLE; PASS-WITH-MINORS→fixed). Merging `feature/writing-reconstruction-completeness` into `main` is a Manager scheduling action (project allows AI self-merge post-audit). Writer does **not** push/merge.

---

## 6. Untracked files present in worktree (NOT committed by writer — do not touch without owner)
`docs/paper/figures/*.pptx`, `Slide{1-4}.PNG` — owner-provided, untracked; writer left them untouched per session rules.

---

## 7. Quick verification for the next agent
```
git -C "<worktree>" --no-pager diff 3433455..HEAD -- docs/paper/main.tex   # full reconstruction diff
git -C "<worktree>" --no-pager log --oneline 3433455..HEAD
# rebuild: docs/paper/build.ps1 -Clean ; expect 21pp, 0 undefined
```

---

## 8. Update 2026-08-17 (post-fold + reviewer pass), HEAD 980a93f

### Done since the original handoff
- **avg-prompt + novice everyday-user comparators FOLDED** (owner GO): Results §"The Everyday-User Comparator" + Appendix "Exploratory Novice-Style Prompt Comparator". Both Qwen-only, valid_for_paper=false, audited MERGEABLE. deliberation uses like-for-like −0.012 (NOT +0.828 floor artifact); novice ITI-uncertainty quarantined as 0.75-imputation artifact.
- **δ-independence claim CORRECTED** (commit 980a93f, fixing an earlier wrong 83536a0). The reviewer's "lowering δ qualifies no cell" is FALSE: ITI×Qwen deliberation has ci_low=+0.000625 (interval clears zero), fails only because mean 0.020<δ. Paper now states: robust negatives (uncertainty powered −0.088, 90%CI[−0.109,−0.067]) are threshold-independent; the one threshold-sensitive cell is the 64-token-floored deliberation, whose marginal positive is an artifact. **Do not reintroduce the flat "any δ → 0/12" claim.**

### Open to-dos (need Manager / experiment / parallel session)
1. **Latent positive control (Stolfo-style), highest priority** — solves the §7.2 assay-validity gap (no passing latent positive control ⇒ cannot separate "truly inactionable" from "assay-limited"). Prereg-style dispatch prompt already drafted for Manager. Not runnable by writer (needs GPU + prereg + audit).
2. **delib-512 hostile audit** — data received on `feature/delib-512 @ 0bcf372` (code_commit 0af4b569) and INDEPENDENTLY VERIFIED by writer, but both cells are `valid_for_paper=False; scientific_status=PENDING_HOSTILE_RESULT_AUDIT`, no ledger E-row. Writer will NOT fold until audit closes. Verified numbers:
   - D1 Qwen·CAA·L20: mean −0.0387, Bonf98.33% [−0.0827,0.000], TOST90 [−0.068,−0.012], N150, MDE 0.0386, frozen_α2→dev_α16, coherence ok, acc steer 0.841/prompt 0.880, UNDERPOWERED.
   - D2 Llama·CAA·L12: mean −0.0240, Bonf98.33% [−0.080,+0.0293], TOST90 [−0.0627,+0.0133], N150, MDE 0.0363, frozen_α2=dev_α2, coherence ok, acc steer 0.685/prompt 0.709, UNDERPOWERED.
   - Fold cautions when audit closes: only 2 of 4 deliberation cells (CAA only; ITI not re-measured); α is 512-DEV re-selected (D1 2→16), so it is an independent re-measure not "just longer tokens"; additive, does NOT overwrite frozen 64-token 0/12 grid; report as UNDERPOWERED, direction slightly negative, still no-pass — do not claim equivalence or significance.
3. **Ledger C3 sync** (internal-signal generalization = asserted design scope) — Manager ledger duty, still open.
4. **Merge** `feature/writing-reconstruction-completeness` into main — both reconstruction audits clear; Manager scheduling action.
5. **User study** data → `PENDING_USER_STUDY_SLOT` (parallel session).

### Commit range this session
`3433455..980a93f` on `feature/writing-reconstruction-completeness` (unmerged, unpushed). Build: 21pp, 0 undefined.
