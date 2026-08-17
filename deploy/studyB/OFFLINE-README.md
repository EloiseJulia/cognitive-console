# Study B — Offline collector: owner README (distribution / return / post-hoc Q)

> **Status: 🔴 pre-ethics DRAFT self-test tool.** Not deployed, not for
> recruitment. Before collecting any real human data you MUST pass the spec §7
> gate: ethics/IRB + advisor sign-off, finalized consent (fill the
> `(to be completed)` placeholders), protocol freeze + pre-registered MDE,
> independent audit, and a privacy / retention–deletion plan. The owner
> "recruiting themselves" does **not** waive any of these.

This tool implements the **decoupled** offline design (protocol §3.0, D-0130):
the single-file HTML **collects** written prompts, chosen slider settings,
effort telemetry, questionnaires and the prompt-writing probe, then exports
JSON. It **never runs a model**, shows **no model output**, and carries **no
answer key and no task-quality (Q) value** on the participant side. `Q` is a
**separate post-hoc batch-scoring experiment**, registered independently.

## Files

| File | Role |
|---|---|
| `deploy/studyB/offline/studyB-collector-offline.html` | Self-contained participant SPA (generated). |
| `scripts/generate_studyB_offline.py` | Rebuilds the HTML from source (DRAFT tasks live here). |
| `scripts/aggregate_studyB_offline.py` | Owner-side validator + aggregator (no Q, no scoring). |
| `deploy/studyB/OFFLINE-EXPORT-SCHEMA.md` | Export field dictionary. |

## Rebuild the HTML

```powershell
python scripts\generate_studyB_offline.py
# optional custom path:
python scripts\generate_studyB_offline.py --output deploy\studyB\offline\studyB-collector-offline.html
```

The generator runs a forbidden-term self-check (rejects any
`expected` / `answer_key` / `rubric` / `ground_truth` / `correct_answer` …
leaking into the HTML) and a read-back check.

## Participant flow (what the HTML does)

1. **Consent** (bilingual, draft with `(to be completed)` placeholders). Ticking
   the box records `consent_agreed:true` + timestamp; declining exits with no data.
2. **Covariate questionnaire** — general AI proficiency (covariate ONLY; does
   not define any group).
3. **Prompt-writing probe** — write ONE instruction. Text / timing / char count /
   edit count are recorded. **Not scored on device** (rubric scoring is post-hoc,
   double-blind, off-tool).
4. **Main tasks** — each paired task has two conditions (**slider** and
   **own-prompt**) in a **counterbalanced** order recorded with a seed. Both
   conditions are **one-shot, no model output, no feedback loop** (symmetry, so
   "slider has feedback, prompt has none" does not confound the comparison).
5. **Convenience ratings** — short NASA-TLX + Likert + willingness (slider vs.
   own prompt, with a free-text reason).
6. **Optional reliance/confidence.**
7. **Attention check**, then **export** (JSON required; CSV preview optional).

> The bundled tasks are **DRAFT / fictional placeholders** only to exercise the
> flow. The **final task set must be authored separately, reviewed, and frozen**
> before recruitment (see `scripts/generate_studyB_offline.py` → `TASKS`).

## Distribution & return

- Send participants the single HTML file (or host it as a static file). It works
  fully offline; nothing is uploaded.
- Ask each participant to **download the JSON** and return it (e.g. via the
  channel your ethics plan specifies). Files are **unsigned**; honest return is
  assumed (same trust model as the V3 offline workflow).
- The filename is `studyB-offline-<first 8 chars of submission_id>.json`.

## Aggregation (owner side)

```powershell
python scripts\aggregate_studyB_offline.py <folder-of-json> --out-dir <out-folder>
```

Outputs:

- `participants.csv` — one row per participant (covariates, probe metadata,
  convenience ratings, effort, reliance, attention answer).
- `tasks.csv` — one row per participant × task (prompt/setting/effort per
  condition) **plus empty Q placeholder columns** (`q_slider_pending`,
  `q_own_prompt_pending`, `d_paired_pending`) for post-hoc scoring.
- `summary.json` — accepted / skipped / warnings + a `q_scoring` block stating Q
  is not computed here.

The aggregator **validates** each file (schema, `signed:false`, valid
`submission_id`, no answer-key/rubric/Q keys, complete field set, monotonic
timestamps, task-order agreement), **de-duplicates by `submission_id`** (first
wins; repeats are skipped), and **never computes Q, never scores, never judges a
direction**. CSVs use `utf-8-sig` (BOM) and `'`-prefix injection protection.

## Post-hoc Q scoring (separate experiment — NOT this tool)

`Q(slider)` and `Q(own_prompt)` are produced by a **separate** batch-scoring
experiment that feeds the collected slider settings + prompts to a model under a
**fixed** code commit / seed / model / direction / rubric, registered in
`experiment-registry`. Rubric scoring is double-blind to condition/group. Fill
the empty placeholder columns in `tasks.csv` from that experiment's artifacts —
**do not hand-enter numbers**. The paired difference `D_i = Q(slider) −
Q(own_prompt)` (protocol §5, H1) is computed downstream, not here.

## Honesty boundary

Fictional/illustrative; exploratory pilot; protocol not frozen; one participant
does not represent any population; **this tool draws no user-benefit
conclusion.** Applicability (H4) uses the existing V3 offline tool as-is — this
collector does **not** reimplement or touch V3 fingerprint / frozen answers /
materials v11.3.
