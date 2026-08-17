# Simulated-Novice Prompt Comparator: Corpus License Gate

Status: **PASS for exploratory use**. `valid_for_paper=false`; anchor calibration gate is **NOT passed**.

## Selected corpus

- Corpus: `OpenAssistant/oasst1` (OASST1), data collected until 2023-04-12.
- License: **Apache-2.0**.
- Sources checked 2026-08-17:
  - Hugging Face README front matter: `license: apache-2.0`, <https://huggingface.co/datasets/OpenAssistant/oasst1/raw/main/README.md>.
  - Hugging Face LICENSE is Apache License 2.0, including grants to reproduce, prepare derivative works, publicly display, sublicense, and distribute, <https://huggingface.co/datasets/OpenAssistant/oasst1/raw/main/LICENSE>.
  - Dataset card describes OASST1 as a human-generated, human-annotated assistant-style conversation corpus, <https://huggingface.co/datasets/OpenAssistant/oasst1>.

## Why not Dolly

`databricks/databricks-dolly-15k` was checked but not selected. Its card says the dataset is CC BY-SA 3.0 and supports synthetic data generation, but ShareAlike introduces avoidable redistribution obligations for derivative prompt artifacts. OASST1 Apache-2.0 is clearer for few-shot style anchoring and artifact redistribution.

## Persisted few-shot examples

The exact few-shot texts and source IDs are persisted in:

`data/novice_prompt_sources/oasst1_fewshot_20260817.json`

They are used only to anchor novice/non-expert wording style. They are not task content, not human-anchor calibration, and not evidence that AI-generated novice prompts match real novice prompts.
