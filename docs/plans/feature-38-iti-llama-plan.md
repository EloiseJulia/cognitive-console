# Plan · feature/38-iti-llama (ITI + Llama-3 support for frozen robustness arm)

- **Plan ID**: feature-38-iti-llama
- **Scope**: add ITI steering extraction (orthogonal to CAA), make HF provider/generator model-agnostic for Qwen/Llama chat models, wire C2b adjudication runner to choose steering method, and add CPU-only tests.
- **Hard boundaries**:
  - do not touch `src/cognitive_console/experiments/adjudicate_c2b.py` frozen §4 decision logic
  - do not edit frozen result artifacts under `results/`
  - keep existing CAA numerical behavior unchanged

## Execution slices

1. **ITI extraction module**
   - add `src/cognitive_console/steering/iti.py`
   - implement per-layer logistic-probe direction, sigma scaling metadata, and selection-compatible diagnostics
   - export ITI APIs via `src/cognitive_console/steering/__init__.py`

2. **Model-agnostic HF prompt rendering + Llama-ready checks**
   - in activation/generation HF paths, centralize user chat rendering through `apply_chat_template`
   - keep decoder-layer lookup/config-derived layer count generic (Qwen/Llama compatible)

3. **Runner wiring for method family**
   - extend `scripts/run_c2b_adjudication.py` with steering-method switch (`caa`/`iti`)
   - keep frozen adjudication rule unchanged; only change direction extraction + alpha scaling semantics for ITI
   - ensure `--model` remains fully model-id/path driven (Qwen/Llama)

4. **Tests**
   - add ITI unit tests: direction recovery on synthetic, CAA-vs-ITI orthogonality signal, sigma scaling
   - add provider/generator tests for model-agnostic chat-template/layer metadata logic
   - add runner parser/fingerprint tests for steering-method routing

5. **Validation + commit**
   - run targeted pytest for touched surfaces, then full `python -m pytest -q`
   - commit on `feature/38-iti-llama` with required trailers
