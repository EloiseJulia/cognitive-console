"""Generate the C1 facade-ratio figure from frozen JSON artifacts."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "results" / "gpu_7b_2026-07-23" / "c1" / "c1_facade_results.json"
OUT = ROOT / "docs" / "paper" / "figures" / "c1-ratio-ci.pdf"

LABELS = {
    "deliberation": "Deliberation",
    "skepticism": "Skepticism",
    "uncertainty_awareness": "Uncertainty",
    "focus": "Focus\n(non-facade)",
}


def main() -> None:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    axes = data["axes"]
    names = [a["axis"] for a in axes]
    ratios = [a["facade_ratio"] for a in axes]
    los = [a["facade_ratio_ci_lo"] for a in axes]
    his = [a["facade_ratio_ci_hi"] for a in axes]
    null_ratios = [a["pole_null_p95"] / a["pole_reach"] for a in axes]
    colors = ["#2b8cbe" if a.get("facade_gap_holds_ci") else "#d95f0e" for a in axes]

    x = list(range(len(axes)))
    yerr = [[r - lo for r, lo in zip(ratios, los)], [hi - r for r, hi in zip(ratios, his)]]

    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    ax.errorbar(x, ratios, yerr=yerr, fmt="none", ecolor="#1f1f1f", capsize=4, lw=1.4, zorder=2)
    ax.scatter(x, ratios, s=70, c=colors, edgecolor="black", linewidth=0.6, zorder=3, label="Prompt / pole ratio")
    ax.scatter(x, null_ratios, s=54, marker="D", c="#777777", edgecolor="black", linewidth=0.4, zorder=3, label="Random-null p95 / pole")
    ax.axhline(1.0, color="#7f0000", lw=1.0, ls="--", label="ratio = 1")
    ax.set_xticks(x, [LABELS.get(n, n.replace("_", " ")) for n in names])
    ax.set_ylabel("facade ratio = prompt_reach / pole_reach")
    ax.set_title("C1 representational facade ratios (Qwen2.5-7B, exploratory)")
    ax.set_ylim(0, max(max(his), 1.0) * 1.15)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.text(0.99, 0.97, "Numbers derived from frozen C1 facade artifact", transform=ax.transAxes,
            ha="right", va="top", fontsize=7)
    fig.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        OUT,
        bbox_inches="tight",
        metadata={"CreationDate": None, "ModDate": None},
    )


if __name__ == "__main__":
    main()
