# License Gate — Latent Behavioral Positive Control (Stage-1)

- **Gate owner/date:** owner-approved Stage-1, 2026-08-17.
- **Decision:** **CLEAR for Stage-1 DEV/smoke**. No TEST or paper-valid claim is authorized by this document.

## Assets checked

| Asset | Use in this branch | Source checked | License / terms | Gate result |
|---|---|---|---|---|
| Stolfo et al. `microsoft/llm-steer-instruct` | Method/code reference for instruction-vector extraction and residual-stream addition; no vendored third-party source committed | GitHub repo README and `LICENSE.txt`, main commit `9dac937ef6fc3e483b1efc13863deeb03ec38dbe` | MIT License. README states the project is licensed under MIT and may be modified/adapted; `LICENSE.txt` grants use/copy/modify/merge/publish/distribute/sublicense/sell with notice retention. | **Allowed** with attribution/license notice if code is copied. Current branch faithfully reimplements the method and cites the repo; no source file copied. |
| Stolfo et al. official repo runtime code/data | Owner-approved rerun E-0017b directly executed the official repo clone (`utils/model_utils.py`, `utils/generation_utils.py`, `keywords/*`, `ifeval_scripts/*`, `data/keywords/ifeval_single_keyword_include.jsonl`) | Same repo/commit plus file headers | Repo-level MIT license; bundled `ifeval_scripts/evaluation_main.py` carries Google Research Apache-2.0 header. | **Allowed for internal Stage-1 DEV** with MIT/Apache attribution. No official source is vendored in this project commit; only generated DEV artifacts are stored. |
| Qwen/Qwen2.5-7B-Instruct | Primary model for DEV assay | Hugging Face model API and `LICENSE`, revision `a09a35458c702b33eeacc393d103063234e8bc28` | Apache-2.0 (`license: apache-2.0` in model card/API; raw `LICENSE` is Apache License 2.0). | **Allowed** for this internal research run subject to Apache-2.0 attribution/notice obligations. |
| microsoft/Phi-3-mini-4k-instruct | Owner-approved non-gated official positive-control DEV after Gemma access block | Hugging Face model API and raw `LICENSE`, revision `f39ac1d28e925b323eae81227eaba4464caced4e` | MIT (`license:mit`; raw `LICENSE` is Microsoft MIT License). API reports `gated:false`. | **Allowed** for internal Stage-1 DEV with MIT notice retention. |
| `data/latent_positive_control/keyword_blue_items.json` | Extraction/DEV/sealed TEST prompts for keyword-inclusion positive control | Self-authored in this repository | No external dataset content; repository-owned prompts. | **Allowed**. Hash: `sha256:2c6d946433edd555d504dc2c8ab7e75fee01eb6f589728b47687ea889b594d91`. |

## Non-use / deferred assets

- Initial E-0017 self-authored Stage-1 did not use IFEval. Owner later approved E-0017b to directly execute the official Stolfo repo and its included IFEval-style keyword data. If Stage-2 copies official code/data into this repository (rather than executing a clone), retain the MIT notice and the Apache-2.0 notices from bundled IFEval scripts.

## Source anchors

- `https://github.com/microsoft/llm-steer-instruct` README: describes the ICLR 2025 paper, the method (paired inputs with/without instruction; add vector to residual stream), and says the project is MIT licensed.
- `https://raw.githubusercontent.com/microsoft/llm-steer-instruct/main/LICENSE.txt`: MIT License, Microsoft Corporation.
- `https://huggingface.co/api/models/Qwen/Qwen2.5-7B-Instruct`: reports model sha `a09a35458c702b33eeacc393d103063234e8bc28` and `license: apache-2.0`.
- `https://huggingface.co/Qwen/Qwen2.5-7B-Instruct/raw/main/LICENSE`: Apache License 2.0 text.
- `https://huggingface.co/api/models/microsoft/Phi-3-mini-4k-instruct`: reports model sha `f39ac1d28e925b323eae81227eaba4464caced4e`, `license:mit`, and `gated:false`.
- `https://huggingface.co/microsoft/Phi-3-mini-4k-instruct/raw/main/LICENSE`: Microsoft MIT License text.
