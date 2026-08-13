"""Generate the static console UI-contract figure from frozen local artifacts.

No live model calls, humans, GPU, paid APIs, or downloaded artifacts are used.
The figure is a lightweight PDF drawn with the Python standard library so it is
rebuildable in the base test environment.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from cognitive_console.console.data_loader import build_console_payload  # noqa: E402

OUT = ROOT / "docs" / "paper" / "figures" / "console-ui-contract.pdf"
E0013 = ROOT / "results" / "E-0013-uncertainty-recheck" / "reanalysis.json"


def _fmt(value: object, digits: int = 3) -> str:
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    if isinstance(value, int):
        return str(value)
    if value is None:
        return "n/a"
    return str(value)


def _wrap(text: str, width: int = 52, max_lines: int = 2) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur: list[str] = []
    for word in words:
        candidate = " ".join(cur + [word])
        if len(candidate) > width and cur:
            lines.append(" ".join(cur))
            cur = [word]
        else:
            cur.append(word)
    if cur:
        lines.append(" ".join(cur))
    return lines[:max_lines]


def _reader_text(text: object) -> str:
    replacements = {
        "KILL_PLAN_D": "pre-registered kill/null outcome",
        "NON_TRANSFER_GENERALIZED": "generalized non-transfer result",
        "valid_for_paper=false": "exploratory, not used as confirmatory evidence",
        "not_implemented": "not implemented in this run",
        "not_run_required_before_confirmatory_claim": "human-rater calibration pending",
        "human-alpha PENDING -> not-yet-confirmatory": "not yet confirmatory",
        "calibration harm": "steer-vs-prompt calibration contrast",
        "uncertainty harm": "uncertainty steer-vs-prompt contrast",
    }
    out = str(text)
    for old, new in replacements.items():
        out = out.replace(old, new)
    return out


def _signal_line(label: str, body: str) -> tuple[str, str]:
    return label, body


def _tier_summary(card: dict) -> str:
    tier = card["evidence_tier"]["transfer_identity"]
    model = str(tier.get("model")).replace("-instruct", "")
    axis = {
        "deliberation": "delib",
        "uncertainty_awareness": "uncert",
    }.get(card["axis"], card["axis"])
    task_outcome = {
        "deliberation": "delib/binary",
        "uncertainty_awareness": "confidence/1-Brier",
    }.get(card["axis"], f"{tier.get('task')}/{tier.get('outcome')}")
    direction_status = "dir/split OK" if tier.get("complete") else "dir/split MISSING"
    return (
        f"{model}; {str(tier.get('method')).upper()}:{axis}@L{tier.get('layer')}; "
        f"{task_outcome}; C2b-v2026-07-23; DEV-prompt; {direction_status}."
    )


def _action_summary(card: dict) -> str:
    read = card["interface_action"]["read_only_diagnostic"]["eligibility"]
    active = card["interface_action"]["active_control"]["eligibility"]
    read_text = (
        "Read-only diagnostic candidate within this evidence tier"
        if read == "candidate"
        else "Read-only diagnostic candidate withheld"
    )
    active_text = (
        "active control passes the computational gate within exact tier"
        if active == "passes_computational_gate"
        else "active control withheld"
    )
    return f"{read_text}; {active_text}."


def _card_title(card: dict) -> str:
    method = str(card["evidence_tier"]["transfer_identity"].get("method")).upper()
    return f"QWEN-{method} / {card['label'].upper()}"


def _transfer_summary(card: dict) -> str:
    transfer = card["transfer_verdict"]
    return (
        f"{transfer.get('verdict')}; delta={_fmt(transfer.get('delta'))}, "
        f"CI=[{_fmt(transfer.get('ci_lo'))}, {_fmt(transfer.get('ci_hi'))}]."
    )


def _load_e0013() -> dict:
    with E0013.open(encoding="utf-8") as fh:
        return json.load(fh)


def _card_lines(card: dict, e0013: dict, grid_size: int) -> list[tuple[str, str]]:
    read = card["read_status"]
    ceiling = card["prompt_ceiling"]
    if card["axis"] == "deliberation":
        return [
            _signal_line("READ STATUS", f"{read.get('status')}; local CAA evidence only."),
            _signal_line("TRANSFER STATUS", _transfer_summary(card)),
            _signal_line(
                "BLOCKING REASON",
                "Direction/split identity is missing; interval also includes zero.",
            ),
            _signal_line(
                "GRID SCOPE NOTE",
                "ITI exploratory equivalence; CAA cells are underpowered.",
            ),
            _signal_line("BOUNDED PROMPT COMPARATOR", ceiling.get("summary", "n/a")),
            _signal_line(
                "EXACT EVIDENCE TIER",
                _tier_summary(card),
            ),
            _signal_line(
                "INTERFACE ACTION",
                _action_summary(card),
            ),
        ]

    cells = e0013["test_split_only"]
    rechecked = len(cells)
    cell = next(iter(cells.values()))
    conditions = cell["conditions"]
    direct_delta = (
        conditions["steer"]["mean_frozen_imputed_1minus_brier"]
        - conditions["baseline"]["mean_frozen_imputed_1minus_brier"]
    )
    bounds = [
        row["delta"]
        for row in cell["sensitivity"]["worst_case_imputation_bounds"]["bounds"]
    ]
    assert min(bounds) <= 0 <= max(bounds)
    assert abs(direct_delta) < 0.01
    assert "format_compliant_only_delta_steer_minus_prompt" in cell
    assert rechecked == 1 and grid_size >= rechecked
    return [
        _signal_line("READ STATUS", f"{read.get('status')}; local CAA evidence only."),
        _signal_line("TRANSFER STATUS", _transfer_summary(card)),
        _signal_line(
            "BLOCKING REASON",
            "Direction/split identity is missing; missingness bounds cross zero.",
        ),
        _signal_line(
            "GRID SCOPE NOTE",
            f"{grid_size}/{grid_size} negative under the frozen scorer as run; Qwen-CAA near baseline; "
            f"all-generation sign unidentified, {grid_size - rechecked} cells not rechecked.",
        ),
        _signal_line(
            "EXACT EVIDENCE TIER",
            _tier_summary(card),
        ),
        _signal_line(
            "INTERFACE ACTION",
            _action_summary(card),
        ),
    ]


def _select_cards(cards: Iterable[dict]) -> list[dict]:
    by_axis = {card["axis"]: card for card in cards}
    return [
        by_axis["deliberation"],
        by_axis["uncertainty_awareness"],
    ]


def write_pdf(payload: dict, out_path: Path) -> None:
    cards = _select_cards(payload["ui_contract"]["cards"])
    e0013 = _load_e0013()
    grid_size = len(payload["arm"]["cells"])
    matplotlib.rcParams["pdf.fonttype"] = 42
    matplotlib.rcParams["font.family"] = "DejaVu Sans"
    fig, ax = plt.subplots(figsize=(7, 260 / 72))
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    ax.set_xlim(0, 504)
    ax.set_ylim(0, 260)
    ax.axis("off")
    ax.text(18, 241, "COMPARATOR-BOUND CONTROL RECORD", fontsize=12, fontweight="bold", va="baseline")
    ax.text(
        18,
        228,
        "Computational status, structured reason, and record-specific action.",
        fontsize=7,
        va="baseline",
    )
    x0 = 18
    y0 = 18
    w = 230
    h = 198
    gap = 8
    for i, card in enumerate(cards):
        x = x0 + i * (w + gap)
        ax.add_patch(Rectangle((x, y0), w, h, facecolor="white", edgecolor="black", linewidth=0.8))
        ax.add_patch(
            Rectangle(
                (x, y0 + h - 42),
                w,
                42,
                facecolor="0.88",
                edgecolor="black",
                linewidth=0.8,
            )
        )
        ax.text(
            x + 8,
            y0 + h - 14,
            _reader_text(_card_title(card)),
            fontsize=9.5,
            fontweight="bold",
            va="baseline",
        )
        ax.text(
            x + 8,
            y0 + h - 31,
            "COMPUTATIONAL RECORD",
            fontsize=8.5,
            fontweight="bold",
            va="baseline",
        )
        y = y0 + h - 52
        for label, body in _card_lines(card, e0013, grid_size):
            ax.text(x + 8, y, label, fontsize=7, fontweight="bold", va="baseline")
            y -= 9
            for line in _wrap(body, width=54):
                ax.text(x + 8, y, _reader_text(line), fontsize=7, va="baseline")
                y -= 8
    out_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_time = datetime.fromisoformat(e0013["generated_at"])
    fig.savefig(
        out_path,
        format="pdf",
        dpi=72,
        metadata={
            "Creator": "plot_console_ui_contract.py",
            "CreationDate": artifact_time,
            "ModDate": artifact_time,
        },
    )
    plt.close(fig)


def main(argv: list[str] | None = None) -> Path:
    parser = argparse.ArgumentParser(description="Plot console v2 UI-contract cards from frozen artifacts.")
    parser.add_argument("--out", type=Path, default=OUT, help="Output PDF path.")
    if argv is not None:
        argv = [str(arg) for arg in argv]
    args = parser.parse_args(argv)
    payload = build_console_payload()
    write_pdf(payload, args.out)
    print(f"Wrote {args.out}")
    return args.out


if __name__ == "__main__":
    main()
