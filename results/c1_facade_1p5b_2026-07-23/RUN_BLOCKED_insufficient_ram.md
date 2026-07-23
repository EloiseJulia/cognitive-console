# C1 Facade Re-run on Qwen2.5-1.5B-Instruct — BLOCKED (insufficient free RAM)

- **Status**: BLOCKED — could not run. NOT started (no model forward completed).
- **Type**: EXPLORATORY, valid_for_paper: false.
- **Model**: `Qwen/Qwen2.5-1.5B-Instruct` (Apache-2.0), CPU, float32, low_cpu_mem_usage=True.
- **Reason**: insufficient free RAM for the 1.5B float32 load — the user needs to close apps.

## Evidence (watchdog-guarded load-only probe, 2026-07-23)

The load was attempted in a self-monitoring child process with a hard abort floor
of 500 MB system-available RAM to avoid thrashing the machine.

| metric | value |
|---|---|
| machine total RAM | 32.48 GB |
| system available at probe START | 7.70 GB (≈8 GB free; rest used by other apps) |
| peak process RSS reached | **7.59 GB** (still climbing) |
| progress when aborted | ~75% of weight loading |
| system available at abort | **333 MB** (< 500 MB floor) |
| outcome | watchdog hard-aborted before swap-thrash |

Qwen2.5-1.5B has ~1.54B parameters; in float32 the weights alone are ~6.2 GB, and
the `from_pretrained` materialization pushed RSS past 7.6 GB with a quarter of the
weights still to load. With only ~8 GB physically free, completing the load (plus
runtime + forward-pass activations) would exceed available RAM and page heavily
into swap, degrading the whole machine. float32 is mandated and a silent fallback
to 0.5B is disallowed, so there is no in-RAM path here.

## What is ready

The metric fixes are complete, committed, and offline-tested GREEN
(`python -m pytest -q`), independent of the model:

- **FIX 1** — consistent estimators from the same neutral baseline:
  `latent_reach = ||v||`; PRIMARY `prompt_reach_mean` (mean over the strongest-prompt
  set of `project_scalar(act, û) − neutral_proj`); `prompt_reach_max` kept only as a
  labelled upper bound; signed `facade_ratio_mean` (headline) and `facade_ratio_max`.
- **FIX 2** — a SEPARATELY-authored strongest-prompt set
  (`data/strongest_prompts/*.jsonl`, 7 forceful natural instructions per axis),
  distinct in kind from the contrast pairs, with a leakage guard in
  `tests/test_leakage.py`.

Default model + out-dir in `scripts/run_c1_facade.py` already target the 1.5B run.

## To unblock (needs the user)

Close memory-heavy apps to free ≈10 GB, then from the worktree root run:

    python -m scripts.run_c1_facade

The activation disk cache and the (now-downloaded) HF model weights will be reused.
