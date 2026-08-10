# Implementation Plan: Local Contract-Application Micro-Study

- **Plan ID:** `microstudy-contract-application-web`
- **Status:** protocol-finalization revision; implementation pending fresh hostile audit
- **Scope:** future loopback implementation only; this revision implements no web application
- **Spec:** [`../specs/microstudy-contract-application.md`](../specs/microstudy-contract-application.md)

## 1. Boundaries

No recruitment, ethics administration, pilot, data collection, public deployment, or paper edit. The DRAFT remains unfrozen and materials-only.

## 2. File plan

```text
src/cognitive_console/microstudy/
  __init__.py
  __main__.py
  server.py
  schema.py
  sequencing.py
  allocation.py
  scoring.py
  export.py
  analysis.py
  simulation.py
  static/index.html
  static/app.js
  static/styles.css
  data/stimuli.json
  data/sequences.json
  data/tutorial.json
tests/
  test_microstudy_schema.py
  test_microstudy_parity.py
  test_microstudy_leakage.py
  test_microstudy_routing.py
  test_microstudy_sequences.py
  test_microstudy_allocation.py
  test_microstudy_export.py
  test_microstudy_analysis.py
  test_microstudy_simulation.py
  test_microstudy_server.py
  test_microstudy_end_to_end.py
```

## 3. Implementation slices

### Materials

- Materialize the ten exact proposition maps, Q2 text/options/keys, Flat orders, and tutorial/practice/debrief.
- Validate exact `source_status`, `source_note`, and `hypothetical`.
- Show `Simulated evaluation record` atop every card; show no raw internal IDs.
- Keep one canonical proposition source for both renderers.

### Two-step routing and leakage

- Lock Q1 before rendering Q2; prohibit app/browser return to Q1.
- Reject state names and one-to-one state mappings in Q2 options.
- Implement the ordered five-input state router; generate and validate Q1 keys from structured inputs.
- Reject item-ID/pattern-ID hardcoding as state authority and invalidate inheritance after any tier change.
- Freeze the normalized option-only baseline and single-comparison-row+option CCA baseline.
- Compute actual chance as `1/option_count`; currently `0.25`.
- Reproduce lexical `3/10, p=0.4744`, comparison Q1 `8/10`, combined CCA `2/10, p=0.7560`.
- Require checker `10/10` and ≥2 derivation primitives.

### Treatment and parity

- Contract: semantic grouping/headings/fixed role order.
- Flat: neutral labels and exact item-specific shuffles.
- Assert every primitive×Flat-position cell count equals two.
- Enforce fixed rows, columns, word counts, viewport, and no scroll.
- DOM, CSS-token, screen-reader, and declared-permutation screenshot checks.

### Sequences and blinded allocation

- Generate `A1..D5` using block rotations `r` and `r+2 mod 5`.
- Generate and test all 200 trial rows for condition×set×pattern×position×block balance.
- Represent allocation attempts separately from sequence slots.
- Generate a random local UUID per `attempt_id`; keep `participant_code` and sequence at session level.
- Freeze duplicate handling by participant code before outcomes using owner-log order.
- Reuse slot for dropout/primary-ineligible attempts.
- Consume slot for ten-trial completion, including later mechanical exclusion; retain excluded completion in ITT sensitivity.
- Keep outcomes out of allocation state.

### Export truth table

- Pre-generate ten slots.
- Export `planned/presented/q1_submitted/q2_submitted/complete`; define `submitted==complete`.
- Cover not reached, viewed/no-Q1, Q1-only dropout, and complete.
- Primary uses complete trials only and exact `4+4+8` eligibility.
- Ten-slot sensitivity maps any missing component to incorrect.
- JSON/CSV export every slot and all listed metadata.
- Export session completion, attention/practice status, derived exclusion boolean/reason, per-slot provenance, and explicit missing flags.
- Retain every raw attempt; rebuild exclusions and omit only frozen duplicates/technical-corrupt attempts from ITT.

### Analysis and simulation

- Rebuild outcomes and mechanical exclusions from raw export plus the frozen owner assignment log.
- Freeze bootstrap `B=10000`, seed `20260810`, participant resampling, percentile `2.5/97.5`.
- Enumerate exact `2^N_eff` sign flips after reporting/removing zero ties; implement inclusive tails and no +1.
- Implement a separate reproducible MDE simulation script before protocol freeze. Inputs must include N, baseline, paired mechanism/correlation, trial count, missingness, alpha, direction, effect grid, iterations, and seed. Outputs: JSON assumptions/results plus generated table/plot.
- Independent audit must reproduce the simulation. Until then, no numerical MDE may be emitted by docs or UI.

### Timing, accessibility, privacy

- Materialize exact placeholder/tutorial/practice/feedback/debrief strings.
- Provide owner pilot export for exactly three people; evaluate median≤10, all≤12, zero forced timeout.
- Keep automated accessibility results separate from timing.
- Enforce loopback/no logging/no persistence/no external network and privacy-negative tests.

## 4. Acceptance matrix

| Area | Required machine proof |
|---|---|
| Materials | exact 10 items, Q2s/keys, provenance, notices, tutorial strings |
| Leakage/routing | two-step lock; generated router keys `10/10`; lexical `3/10`; comparison Q1 `8/10`; combined CCA `2/10`; exact binomial values |
| Treatment | canonical common propositions; declared package; exact Flat permutations; primitive×position=2 |
| Sequences | exact `A1..D5`; `r/r+2`; generated 200-row balance table; no repeated content |
| Allocation | outcome-blind slot ledger; UUID attempts; pre-outcome duplicate rule; reuse/consume cases |
| Export | session identity/status/exclusion; ten enriched slots; provenance; missing flags; exact eligibility |
| Analysis | raw re-derivation; complete-only primary; ITT excluding frozen duplicates/technical corrupt; exact bootstrap/sign-flip |
| Simulation | assumptions schema, deterministic artifacts, audit hook; no hard-coded MDE |
| Timing | 3-person rule: median≤10, all≤12, zero timeout; accessibility separate |
| Privacy/accessibility | loopback/no logs/storage/network; keyboard/zoom/contrast/screen-reader |

## 5. Targeted tests

```text
test_q1_locked_before_q2
test_q2_has_no_state_names_or_state_option_map
test_q2_options_are_parallel_ten_token_positive_statements
test_q2_marker_counts_and_positions_are_balanced
test_option_only_baseline_is_three_of_ten_and_nonsignificant
test_comparison_baseline_is_eight_of_ten
test_combined_baseline_is_two_of_ten_and_nonsignificant
test_router_derives_all_ten_q1_keys
test_router_priority_truth_table
test_tier_change_invalidates_inheritance
test_item_ids_are_not_state_authority
test_flat_role_position_balance_is_two
test_cross_block_rotation_is_plus_two
test_20_sequences_generate_200_balanced_rows
test_dropout_reuses_sequence_slot
test_primary_ineligible_reuses_sequence_slot
test_complete_mechanical_exclusion_consumes_slot_and_enters_itt
test_attempt_id_is_local_random_uuid
test_duplicate_resolution_freezes_before_outcomes
test_duplicate_raw_attempts_are_retained
test_analysis_rederives_mechanical_exclusion
test_itt_omits_only_duplicates_and_technical_corrupt
test_truth_table_not_reached
test_truth_table_viewed_without_q1
test_truth_table_q1_only_dropout
test_truth_table_complete
test_submitted_alias_equals_complete
test_primary_uses_complete_trials_only
test_missing_component_is_incorrect_in_ten_slot_sensitivity
test_bootstrap_exact_configuration
test_sign_flip_enumerates_nonzero_differences
test_sign_flip_inclusive_ties_no_plus_one
test_no_numeric_mde_before_simulation_artifact
test_exact_tutorial_practice_feedback_debrief
test_timing_gate_three_person_rule
```

## 6. Validation after implementation

```powershell
python -m pytest -q tests\test_microstudy_schema.py tests\test_microstudy_parity.py tests\test_microstudy_leakage.py tests\test_microstudy_routing.py tests\test_microstudy_sequences.py tests\test_microstudy_allocation.py tests\test_microstudy_export.py tests\test_microstudy_analysis.py tests\test_microstudy_simulation.py tests\test_microstudy_server.py tests\test_microstudy_end_to_end.py
python -m pytest -q
python -c "import yaml, pathlib; yaml.safe_load(pathlib.Path('docs/ledgers/experiment-registry.yaml').read_text(encoding='utf-8'))"
git diff --check
```

## 7. Definition of done

- All spec invariants are automated where feasible.
- Generated sequence and leakage artifacts are inspectable.
- Missingness and outcomes rebuild from raw export.
- Routing keys rebuild from structured inputs; exclusions rebuild from raw export plus the frozen owner log.
- MDE remains pending until independently reproducible simulation exists.
- Registry remains `not_started_materials_only`.
- No pilot/data/paper work occurs.
- Fresh independent hostile audit reports no BLOCKER before implementation or merge.
