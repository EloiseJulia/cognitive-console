# License Gate — Latent Behavioral Positive Control (Stage-1)

- **Gate owner/date:** owner-approved Stage-1, 2026-08-17.
- **Decision:** **CLEAR for Stage-1 DEV/smoke**. No TEST or paper-valid claim is authorized by this document.

## Assets checked

| Asset | Use in this branch | Source checked | License / terms | Gate result |
|---|---|---|---|---|
| Stolfo et al. `microsoft/llm-steer-instruct` | Method/code reference for instruction-vector extraction and residual-stream addition; no vendored third-party source committed | GitHub repo README and `LICENSE.txt`, main commit `9dac937ef6fc3e483b1efc13863deeb03ec38dbe` | MIT License. README states the project is licensed under MIT and may be modified/adapted; `LICENSE.txt` grants use/copy/modify/merge/publish/distribute/sublicense/sell with notice retention. | **Allowed** with attribution/license notice if code is copied. Current branch faithfully reimplements the method and cites the repo; no source file copied. |
| Qwen/Qwen2.5-7B-Instruct | Primary model for DEV assay | Hugging Face model API and `LICENSE`, revision `a09a35458c702b33eeacc393d103063234e8bc28` | Apache-2.0 (`license: apache-2.0` in model card/API; raw `LICENSE` is Apache License 2.0). | **Allowed** for this internal research run subject to Apache-2.0 attribution/notice obligations. |
| `data/latent_positive_control/keyword_blue_items.json` | Extraction/DEV/sealed TEST prompts for keyword-inclusion positive control | Self-authored in this repository | No external dataset content; repository-owned prompts. | **Allowed**. Hash: `sha256:2c6d946433edd555d504dc2c8ab7e75fee01eb6f589728b47687ea889b594d91`. |

## Non-use / deferred assets

- IFEval / Google Research evaluation data is **not used** in Stage-1. This avoids adding an external data-license dependency for the DEV sanity run.
- `llm-steer-instruct` was inspected as a method reference. If Stage-2 copies code or data from that repo, retain the MIT notice and re-run this gate.

## Source anchors

- `https://github.com/microsoft/llm-steer-instruct` README: describes the ICLR 2025 paper, the method (paired inputs with/without instruction; add vector to residual stream), and says the project is MIT licensed.
- `https://raw.githubusercontent.com/microsoft/llm-steer-instruct/main/LICENSE.txt`: MIT License, Microsoft Corporation.
- `https://huggingface.co/api/models/Qwen/Qwen2.5-7B-Instruct`: reports model sha `a09a35458c702b33eeacc393d103063234e8bc28` and `license: apache-2.0`.
- `https://huggingface.co/Qwen/Qwen2.5-7B-Instruct/raw/main/LICENSE`: Apache License 2.0 text.
