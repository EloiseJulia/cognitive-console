"""Generate the C2 uncertainty calibration-harm figure from frozen 2x2 arm JSON artifacts."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[3]
ARM_DIR = ROOT / "results" / "arm_full"
SUMMARY = ARM_DIR / "arm_matrix_summary.json"
OUT = ROOT / "docs" / "paper" / "figures" / "c2-calibration-harm.pdf"

METHOD_LABEL = {"caa": "CAA", "iti": "ITI"}
MODEL_LABEL = {"qwen2.5-7b": "Qwen2.5-7B", "llama3-8b": "Llama-3-8B"}
COLORS = {"caa": "#756bb1", "iti": "#31a354"}


def load_rows():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    rows = []
    for cell in summary["cells"]:
        result_path = ARM_DIR / f"cell_{cell['cell_key']}" / "c2b_adjudication_results.json"
        result = json.loads(result_path.read_text(encoding="utf-8"))
        axis = next(a for a in result["axes"] if a["axis"] == "uncertainty_awareness")
        rows.append({
            "cell_key": cell["cell_key"],
            "method": cell["method"],
            "model": cell["model_label"],
            "mean": axis["mean_diff"],
            "lo": axis["ci_lo"],
            "hi": axis["ci_hi"],
            "passed": axis["passed"],
            "ci_excludes_zero": axis["ci_hi"] < 0 or axis["ci_lo"] > 0,
            "ci_level": axis["ci_level"],
        })
    return rows


def main() -> None:
    rows = load_rows()
    x = list(range(len(rows)))
    means = [r["mean"] for r in rows]
    yerr = [[r["mean"] - r["lo"] for r in rows], [r["hi"] - r["mean"] for r in rows]]
    labels = [f"{METHOD_LABEL.get(r['method'], r['method'].upper())}\n{MODEL_LABEL.get(r['model'], r['model'])}" for r in rows]
    colors = [COLORS.get(r["method"], "#636363") for r in rows]

    fig, ax = plt.subplots(figsize=(6.5, 3.4))
    ax.axhline(0, color="#7f0000", lw=1.0, ls="--", label="no change")
    ax.errorbar(x, means, yerr=yerr, fmt="none", ecolor="#1f1f1f", capsize=4, lw=1.4, zorder=2)
    ax.scatter(x, means, s=72, c=colors, edgecolor="black", linewidth=0.6, zorder=3)
    for i, r in enumerate(rows):
        if r["ci_excludes_zero"]:
            ax.text(i, r["hi"] + 0.015, "CI excludes 0", ha="center", va="bottom", fontsize=7, rotation=0)
    ax.set_xticks(x, labels)
    ax.set_ylabel("TEST paired Δ in uncertainty (steer − prompt; 1 − Brier)")
    ax.set_title("C2 calibration harm across CAA/ITI × Qwen/Llama")
    ax.grid(axis="y", alpha=0.25)
    ax.text(0.99, 0.03, "Numbers derived from frozen robustness-arm artifacts", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=7)
    fig.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, bbox_inches="tight")


if __name__ == "__main__":
    main()
