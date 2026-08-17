# Study B — Offline export schema dictionary

**Schema id:** `microstudy-export-offline-studyB-v1` · **`signed`: always `false`**

> 🔴 pre-ethics DRAFT. The participant payload / DOM / ARIA / export contain
> **no** `expected` / `correct*` / `answer_key` / Q value / rubric score. The
> aggregator asserts this (any such term appearing as a **key** is rejected).
> Free-text participant answers are data, not keys, and are not scanned.

Relative timestamps (`*_at_relative`) are integer milliseconds since
`client_started_at`. `null` means the phase was not reached / committed.

## Top-level fields

| Field | Type | Notes |
|---|---|---|
| `export_schema` | string | Must equal `microstudy-export-offline-studyB-v1`. |
| `signed` | bool | Always `false` (unsigned offline return). |
| `submission_id` | string | `crypto.randomUUID()`, generated **at runtime** (≥ 8 chars). De-dup key. Never baked into the static HTML DATA. |
| `honesty_notice` | string | Locale-resolved honesty banner text. |
| `instrument_version` | string | Tool version (e.g. `studyB-collector-offline-0.1.0-draft`). |
| `selected_locale` | string | `en` or `zh-Hans`. |
| `consent_agreed` | bool | `true` once the participant ticks consent and begins. |
| `consent_agreed_at` | string (ISO) | Timestamp of consent. |
| `consent_copy_version` | string | Version tag of the consent draft copy. |
| `client_started_at` | string (ISO) | When the session began. |
| `client_finished_at` | string (ISO) or `null` | When export was reached; `null` if partial. |
| `completion_status` | string | `complete` or `partial`. |
| `covariates` | object | AI-proficiency covariate answers (see below). |
| `probe` | object | Prompt-writing probe (see below). |
| `task_order` | object | Counterbalance seed + sequence (see below). |
| `tasks` | list | Exactly **one** paired main task (D-0132 simplified; see below). |
| `convenience` | object | Short TLX + Likert + willingness (see below). |
| `attention` | object | `{ "selected_id": string|null }` — raw attention answer. |

## `covariates` (covariate only; does NOT define groups)

| Key | Type | Notes |
|---|---|---|
| `usage_frequency` | string | Option id (`never`…`daily`). |
| `tuned_parameters` | string | Option id (`no` / `once_twice` / `regularly`). |
| `understands_latent_control` | string | Option id (`not_at_all`…`well`). |
| `self_rating` | int | Self-rated skill 1–5. |

## `probe` (prompt-writing probe — NOT scored on device)

| Key | Type | Notes |
|---|---|---|
| `prompt_text` | string | The participant's single instruction. |
| `started_at_relative` | int | ms since start when the probe opened. |
| `committed_at_relative` | int | ms since start when submitted. |
| `char_count` | int | Length of trimmed `prompt_text`. |
| `edit_count` | int | Number of `input` events (keystroke-level edits). |

## `task_order`

| Key | Type | Notes |
|---|---|---|
| `seed` | int | PRNG seed (mulberry32) that produced the presentation order and per-task condition order. Recorded for reproducibility. |
| `sequence` | list | `[{ "task_id": string, "condition_order": "slider_first"\|"prompt_first" }]`. Must match `tasks` order 1:1 (aggregator enforces). |

## `tasks[]` (the single paired main task)

The simplified collector (D-0132) records **exactly one** paired task; the
aggregator rejects exports whose `tasks` length is not 1.

| Key | Type | Notes |
|---|---|---|
| `task_id` | string | Stable task id. |
| `condition_order` | string | `slider_first` or `prompt_first`. |
| `slider` | object | Latent-slider condition (below). |
| `own_prompt` | object | Self-written-prompt condition (below). |

### `tasks[].slider`

| Key | Type | Notes |
|---|---|---|
| `final_setting` | string or `null` | Chosen discrete stop id. No "correct" setting exists. |
| `settings_explored` | int | Count of distinct stops the participant selected. |
| `started_at_relative` | int or `null` | ms since start when the condition opened. |
| `committed_at_relative` | int or `null` | ms since start when submitted (one-shot). |

### `tasks[].own_prompt`

| Key | Type | Notes |
|---|---|---|
| `prompt_text` | string | The participant's prompt for this task. |
| `char_count` | int | Length of trimmed `prompt_text`. |
| `edit_count` | int | Number of `input` events. |
| `started_at_relative` | int or `null` | ms since start when the condition opened. |
| `committed_at_relative` | int or `null` | ms since start when submitted (one-shot). |

## `convenience`

Simplified to three rating items (D-0132) plus the willingness pairing.

| Key | Type | Notes |
|---|---|---|
| `tlx_effort` | int | Short TLX effort, 1–7. |
| `likert_effort` | int | "Slider felt low-effort", 1–5. |
| `likert_discoverability` | int | "I could tell what the slider did", 1–5. |
| `willingness_choice` | string or `null` | `slider` or `own_prompt`. |
| `willingness_reason` | string | Free-text reason (may be empty). |

## Aggregator output (owner side)

- `participants.csv` — one row per participant.
- `tasks.csv` — one row per participant × task, with **empty** post-hoc Q
  placeholder columns: `q_slider_pending`, `q_own_prompt_pending`,
  `d_paired_pending`. These are filled by the separate registered scoring
  experiment, **not** by this aggregator.
- `summary.json` — accepted / skipped / warnings + `q_scoring` block
  (`computed_here: false`).

**Not present anywhere (hard contract):** `expected`, `correct*`, `answer_key`,
`rubric`, any Q value. The attention check's instructed option is **not** stored
as an answer key; the owner applies the pre-registered exclusion rule off-tool.
