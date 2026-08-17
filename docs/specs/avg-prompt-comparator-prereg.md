# Average-Prompt Comparator Preregistration

- **status:** FROZEN UNRUN
- **owner approval:** 2026-08-17
- **experiment_id:** `AVG-PROMPT-COMPARATOR-20260817-FROZEN-UNRUN`
- **stage covered by this document:** average-prompt comparator arm for frozen C2b TEST cells.
- **stage-1 implementation commit:** `f00d5cebf493379e05f241a9ce464b9d70971cc5`
- **valid_for_paper:** `false` until Stage-2 full run, independent hostile audit, and Manager fold gate.

## Research question

For users who cannot write an expert prompt, does latent steering have incremental behavioral value relative to an ordinary prompt drawn from the frozen authored candidate set?

This arm does **not** reopen E-0005/E-0006 and does **not** replace their best-prompt verdicts. It adds a separate comparator population:

- expert population = DEV-selected best prompt (existing E-0005/E-0006 comparator);
- ordinary population = expectation over the frozen 16 candidate prompts (this arm).

## Frozen design

### Primary comparator

For each frozen TEST item in a cell, evaluate all 16 pre-authored candidate prompts and compute the **per-item mean** outcome:

`avg16_i = mean_j outcome(item_i, candidate_prompt_j)`.

The primary paired contrast is:

`d_i = steering_i - avg16_i`.

### Secondary comparators

These are reported for interpretation only and cannot change the primary verdict.

1. **drop-best-15 mean:** per-item mean after removing the frozen DEV-selected best prompt from the 16 candidates.
2. **worst-prompt lower bound:** per-item minimum outcome across the 16 candidates.

### Complete reuse of frozen best-prompt arm口径

The following are frozen and reused exactly:

| Component | Frozen value / rule |
|---|---|
| TEST items | deterministic DEV/TEST split, seed `20260723`, same item pools as E-0005/E-0006 |
| α selection | **no re-selection**; use frozen per-cell α only |
| Prompt set | **no re-selection**; use `data/strongest_prompts/{axis}.jsonl`, first/all 16 authored prompts |
| Instrument/scorer | `src/cognitive_console/experiments/adjudicate_c2b.py` + `src/cognitive_console/eval/c2b_tasks.py` |
| Direction | same CAA/ITI direction semantics and sign as frozen cell |
| Bootstrap | paired item-cluster bootstrap, `B=10000` |
| CI | Bonferroni 98.333333% (`1 - 0.05/3`) |
| Minimum effect | δ = `0.05` on the frozen per-axis outcome scale |
| Coherence gate | reuse the frozen coherence gate rule and frozen steering coherence status |
| Seed | `20260723` |
| Generation | `max_new_tokens=64` for uncertainty/skepticism; if later expanded to deliberation, use `512` for deliberation only |

### Frozen α confirmation

Initial Stage-2 scope is Qwen2.5-7B uncertainty cells:

| Cell | Frozen source | Axis | Frozen α | Layer | n_TEST | Frozen steering per-item source |
|---|---|---|---:|---:|---:|---|
| CAA × Qwen2.5-7B | `results/arm_full/cell_caa__qwen2.5-7b/c2b_adjudication_results.json` | uncertainty_awareness | 8 | 20 | 53 | committed `per_item_steer` |
| ITI × Qwen2.5-7B | `results/arm_full/cell_iti__qwen2.5-7b/c2b_adjudication_results.json` | uncertainty_awareness | 12 | 17 | 53 | committed `per_item_steer` |

If budget allows after these two cells, expand to Qwen 3 axes × CAA/ITI with the already frozen per-cell α in the same source artifacts. Llama is a later confirmation arm only and is not authorized in Stage 1.

### Pairing decision

Stage-1 code uses committed per-item steering outcomes when present. The two Qwen uncertainty source artifacts contain `per_item_steer`, `n_test=53`, frozen α, layer, and coherence fields, so Stage 2 should use `--steering-source frozen-result`. **No steering regeneration is required for the initial Qwen uncertainty cells.**

Hard-abort fallback: if a selected frozen source lacks per-item outcomes or the reconstructed TEST split length mismatches the committed array, the runner must stop. The only allowed fallback is same-run frozen-α steering regeneration with a validity check that the regenerated steering aggregate matches the frozen best-prompt arm within tolerance; it must not overwrite or replace E-0005/E-0006.

## Symmetric outcome interpretation

Both outcomes are publishable and must be reported without directional cherry-picking:

- **steer ≥ average but < best:** ordinary-user partial rehabilitation plus expert-prompt negative result; strongest two-population interpretation.
- **steer < average:** steering has no incremental value even relative to ordinary prompts; stronger negative result.

No result can be used to claim "latent control is impossible"; scope is limited to this model/method/task/instrument budget.

## Persistence and lineage requirements

Stage-2 runs must persist:

1. full 16-candidate prompt set with prompt IDs and text;
2. per-item outcome for each of the 16 candidate prompts;
3. raw generation text for every candidate sample;
4. format-compliance / parse-failure diagnostics;
5. per-item paired steering source and comparator values;
6. bootstrap result artifacts and registry entry;
7. actual GPU ID, wall-clock, and estimated GPU-hours.

This explicitly repairs the E-0006 transcript-lineage gap for the new comparator arm.

## Input hashes

Prompt files:

- `data/strongest_prompts/deliberation.jsonl`: `sha256:e7d0f09bf3bee479f867c959a01057a8b8c690d543cac61b554ca42db88f1de9`
- `data/strongest_prompts/skepticism.jsonl`: `sha256:e5cb3d79330a522afd09bc541d4b10e1e8e2417bc1eb67d00ed0e1fa19ebbcf1`
- `data/strongest_prompts/uncertainty_awareness.jsonl`: `sha256:9d1a7aebf69069f39caa1a4dc6c504526eb153704c532d830d5c8fc842091d60`

C2b manifests:

- `data/c2b_tasks/manifests/deliberation.yaml`: `sha256:b154598b35006844cf2e74c3a9f6f351e6cd12cd88a619ab9bf8515381911c25`
- `data/c2b_tasks/manifests/skepticism.yaml`: `sha256:e4a1d474a3b3f35629418a6c165baa10e770a5f1da3021e7bc8bf4fd430de577`
- `data/c2b_tasks/manifests/uncertainty_awareness.yaml`: `sha256:5ff49c53c2a6edd387f10c97c07064f9883bf6d6f8b942beacf73e93e1deef4d`

Frozen steering sources:

- CAA × Qwen2.5-7B: `sha256:33f242faf921f4a5de49b9620b6a5507415a157d21f9688dce6616d32cda1800`
- ITI × Qwen2.5-7B: `sha256:e168392f4c44d29467791883da122d27b470ce0770bc81c8b5d705119bc6647e`

Model:

- Qwen2.5-7B-Instruct model ID: `Qwen/Qwen2.5-7B-Instruct`
- frozen revision: `a09a35458c702b33eeacc393d103063234e8bc28`

## Stage-1 smoke only

Stage 1 permits synthetic/CPU smoke and at most tiny GPU smoke. It explicitly forbids real TEST generation. Stage-1 smoke artifact from implementation validation:

- `results/avg_prompt_smoke_stage1/avg_prompt_comparator_results.json`
- backend `synthetic`, `n_items=6`, `n_strong=4`, `bootstrap_b=200`, `allow_underpowered=true`
- format-compliance recorded from transcript side-output; `valid_for_paper=false`

## Stage-2 gate before real generation

Do not run true TEST generation until Manager sends "阶段2 GO" and verifies:

1. this prereg is frozen and committed;
2. code commit is pushed or otherwise recoverable on A800;
3. A800 `nvidia-smi` confirms an actually free GPU; no other user's GPU/process/files are touched;
4. venv and model cache are rebuilt under the agent's own home/workspace;
5. source frozen result JSON hashes match this prereg;
6. planned command uses `--steering-source frozen-result` for the two Qwen uncertainty cells;
7. `--save-transcripts` remains enabled;
8. `valid_for_paper=false` remains until post-run hostile audit and Manager fold gate.

