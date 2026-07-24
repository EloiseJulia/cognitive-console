# cognitive-console

## Reality-check console v1 (boundary/limit instrument)

This repository includes a minimal local console that visualizes frozen real artifacts for trust calibration, not a latent "superpower slider": dual-channel prompt-vs-latent comparison, C1 facade ratio+CI, C2 Δ(steer−prompt)+Bonferroni CI with uncertainty harm boundary warning, and a "when not to trust latent control" panel.

Start with:

```bash
python -m pip install -e . && python -m cognitive_console.console --host 127.0.0.1 --port 8000 --open
```

On Windows PowerShell from the repo root:

```powershell
python -m pip install -e .; python -m cognitive_console.console --host 127.0.0.1 --port 8000 --open
```

This opens <http://127.0.0.1:8000>. The console reads numbers from frozen local artifacts:

- `results\gpu_7b_2026-07-23\c1\c1_facade_results.json` for C1 facade ratios and CIs.
- `results\c2b_adjudication_hf_2026-07-24\c2b_adjudication_results.json` for C2 Qwen/CAA adjudication.
- `results\arm_full\arm_matrix_summary.json` plus cell `c2b_adjudication_results.json` files for E-0006 2×2 uncertainty-harm replication.
- `docs\ledgers\evidence-ledger.md` only as an explicitly labeled fallback if a local C1/arm artifact is absent.

Generate the no-human simulated demo artifact with:

```powershell
python -m cognitive_console.console.demo
```

This writes `results\console_v1_demo\console_v1_demo_report.json` and `.md`.
