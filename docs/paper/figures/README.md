# Regenerating paper figures and tables

Run from the repository root after installing Python dependencies:

```powershell
python docs\paper\scripts\plot_c1_ratio_ci.py
python docs\paper\scripts\plot_c2_calibration_harm.py
python docs\paper\scripts\make_c2_delta_table.py
```

The scripts read only frozen JSON artifacts under `results\gpu_7b_2026-07-23\c1`, `results\arm_full`, and `results\c2b_adjudication_hf_2026-07-24`. The generated PDFs and table include are committed so the paper is both standalone and rebuildable.
