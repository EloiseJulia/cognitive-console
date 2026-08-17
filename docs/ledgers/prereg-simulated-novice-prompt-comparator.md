# Preregistration: Simulated-Novice Prompt Comparator Arm

- **experiment_id:** `NOVICE-PROMPT-COMPARATOR-20260817-FROZEN`
- **type:** exploratory bridge
- **valid_for_paper:** `false`
- **anchor calibration gate:** **NOT passed**
- **freeze time:** 2026-08-17 before prompt-set generation and before any novice-comparator outcomes.

## Scope

Replace the weak `avg16` ordinary-user proxy with AI-generated novice-style prompts for the existing C2b comparator infrastructure. This arm is only a bridge until real novice prompts are collected/calibrated.

## Corpus and license gate

Few-shot style anchors use `OpenAssistant/oasst1` only:

- license: Apache-2.0
- dataset URL: <https://huggingface.co/datasets/OpenAssistant/oasst1>
- exact examples: `data/novice_prompt_sources/oasst1_fewshot_20260817.json`
- license memo: `docs/research/2026-08-17-novice-prompt-corpus-license.md`

No Johnny / CC BY-NC examples are used.

## Frozen generation protocol

- Generator model: `Qwen/Qwen2.5-7B-Instruct`
- Generator revision: `a09a35458c702b33eeacc393d103063234e8bc28`
- Temperature: `0.8`
- Top-p: `0.9`
- Max new tokens for prompt generation: `96`
- Seed: `20260817`
- Prompts per axis: `16`
- Axes: `deliberation`, `skepticism`, `uncertainty_awareness`
- Generation instruction: persisted verbatim in `novice_prompt_set.json` by `scripts/generate_novice_prompt_set.py`

## Frozen comparator protocol

For every Qwen2.5-7B cell:

- TEST items: frozen C2b items and seed `20260723`
- α: frozen per-cell α from existing Qwen C2b artifacts; no re-selection
- Instrument/scorers: frozen `adjudicate_c2b` scorer path
- Bootstrap: paired item-cluster `B=10000`
- CI: Bonferroni `98.333...%`
- δ: `0.05`
- coherence gate: same frozen gate; if coherence fails, the cell is `invalid/coherence_failed`
- k: `5`
- prompt comparator: per-TEST-item mean over the 16 generated novice-style prompts
- deliberation: `max_new_tokens >= 512`; use already repaired 512-token steering side for deliberation
- frozen E-0005/E-0006/E-0011 artifacts are read-only and must not be overwritten

## Threat and interpretation

This arm cannot support Abstract/Contributions confirmatory claims. Required note in every result artifact:

> Anchor calibration gate NOT passed; exploratory only; threat: AI-generated novice prompts are not validated against real novices.
