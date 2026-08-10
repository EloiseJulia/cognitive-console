# cognitive-console

## Reality-check console v2 (UI-contract reality-check instrument)

This repository includes a minimal local console that visualizes frozen real artifacts for trust calibration, not a latent "superpower slider": dual-channel prompt-vs-latent comparison, C1 facade ratio+CI, C2 Δ(steer−prompt)+Bonferroni CI with uncertainty harm boundary warning, and five-signal latent-control affordance cards.

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
- `results\llama_c1_facade_2026-07-24\c1_facade_results.json` for the Llama C1 replication panel.
- `results\c2b_adjudication_hf_2026-07-24\c2b_adjudication_results.json` for C2 Qwen/CAA adjudication.
- `results\arm_full\arm_matrix_summary.json` plus cell `c2b_adjudication_results.json` files for E-0006 2×2 uncertainty-harm replication.
- `results\flagship_powered\behavior\flagship_l0_results.json` and `results\flagship_powered\read\flagship_read_results.json` for E-0010 social-inference READ=HOLDS / TRANSFER=NULL.
- `results\psr_qwen_primary\psr_c2b_adjudication_results.json` for the E-0009 PSR method-strength robustness marker.
- `docs\ledgers\evidence-ledger.md` only as an explicitly labeled fallback if a local C1/arm artifact is absent.

Generate the no-human simulated demo artifact with:

```powershell
python -m cognitive_console.console.demo
```

This writes `results\console_v1_demo\console_v1_demo_report.json` and `.md`.

Generate the paper-ready static UI-contract figure with:

```powershell
python docs\paper\scripts\plot_console_ui_contract.py
```

This writes `docs\paper\figures\console-ui-contract.pdf` from the same frozen artifacts.

## Local micro-study preview

The loopback-only contract-application preview is for owner-led future use after
applicable approvals. It does not recruit people or collect data remotely.

```powershell
python -m cognitive_console.microstudy --host 127.0.0.1 --port 8765 `
  --verification-key-file .runtime\microstudy-verification.key --open
```

Assign an anonymous code and an exact sequence (`A1`–`D5`). Session state stays
only in server memory; shutdown discards it. Completed JSON/CSV exports are
server-generated and HMAC-SHA256 signed. Keep the owner verification key private.

```powershell
python -m cognitive_console.microstudy.analysis analyze export1.json export2.json `
  --verification-key-file .runtime\microstudy-verification.key `
  --assignments frozen-owner-assignments.csv `
  --json-out microstudy-summary.json --csv-out microstudy-participants.csv
python -m cognitive_console.microstudy.analysis mde --n 20 `
  --json-out microstudy-mde-DRAFT.json
```

Analysis rejects unsigned, forged, tampered, wrong-key, wrong-hash, and
schema-invalid exports. It remains explicitly DRAFT, not paper evidence.
