"""Generate the static console UI-contract figure from frozen local artifacts.

No live model calls, humans, GPU, paid APIs, or downloaded artifacts are used.
The figure is a lightweight PDF drawn with the Python standard library so it is
rebuildable in the base test environment.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from cognitive_console.console.data_loader import build_console_payload  # noqa: E402

OUT = ROOT / "docs" / "paper" / "figures" / "console-ui-contract.pdf"


def _esc(text: object) -> str:
    return str(text).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


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
        "LEGIBLE: no added control demonstrated": "WITHHELD CONTROL / diagnostic retained",
    }
    out = str(text)
    for old, new in replacements.items():
        out = out.replace(old, new)
    return out


def _line_ops(
    x: float,
    y: float,
    text: str,
    size: float = 8,
    *,
    font: str = "F1",
) -> str:
    return (
        f"0 0 0 rg 0 0 0 RG "
        f"BT /{font} {size:.1f} Tf {x:.1f} {y:.1f} Td "
        f"({_esc(_reader_text(text))}) Tj ET\n"
    )


def _rect_ops(x: float, y: float, w: float, h: float, fill: tuple[float, float, float]) -> str:
    r, g, b = fill
    return f"{r:.3f} {g:.3f} {b:.3f} rg {x:.1f} {y:.1f} {w:.1f} {h:.1f} re f\n0 0 0 RG {x:.1f} {y:.1f} {w:.1f} {h:.1f} re S\n"


def _signal_line(label: str, body: str) -> tuple[str, str]:
    return label, body


def _next_action(card: dict) -> str:
    transfer = card["transfer_verdict"]
    if transfer.get("passed"):
        return "Restrict actionability to this exact evidence tier."
    if transfer.get("verdict") == "FAIL":
        return "WITHHOLD CONTROL; retain diagnostic evidence."
    return "UNRESOLVED; do not present an actionable control."


def _transfer_summary(card: dict) -> str:
    transfer = card["transfer_verdict"]
    if card["axis"] == "deliberation":
        return f"{transfer.get('verdict')}; full-grid resolution is mixed."
    replications = card["calibration_harm"].get("arm_replications", [])
    if card["axis"] == "uncertainty_awareness" and replications:
        negative = sum(1 for row in replications if row.get("robust_harm"))
        return (
            f"{transfer.get('verdict')}; {negative}/{len(replications)} "
            "frozen contrasts comparator-negative."
        )
    return f"{transfer.get('verdict')}; {transfer.get('summary', '')}"


def _warning_summary(card: dict) -> str:
    warning = card["calibration_harm"]
    if card["axis"] == "uncertainty_awareness":
        return (
            "Steer - bounded prompt: "
            f"delta={warning.get('delta'):.3f}, "
            f"CI [{warning.get('ci_lo'):.3f}, {warning.get('ci_hi'):.3f}]."
        )
    return "No resolved comparator-negative calibration contrast for this axis."


def _card_lines(card: dict) -> list[tuple[str, str]]:
    read = card["read_status"]
    ceiling = card["prompt_ceiling"]
    tier = card["evidence_tier"]
    return [
        _signal_line("READ", f"{read.get('status')} / {read.get('summary', '')}"),
        _signal_line("TRANSFER", _transfer_summary(card)),
        _signal_line("BOUNDED PROMPT COMPARATOR", ceiling.get("summary", "n/a")),
        _signal_line("CALIBRATION WARNING", _warning_summary(card)),
        _signal_line(
            "EVIDENCE TIER / NEXT ACTION",
            f"READ {tier.get('tier')}; TRANSFER frozen; {_next_action(card)}",
        ),
    ]


def _select_cards(cards: Iterable[dict]) -> list[dict]:
    by_axis = {card["axis"]: card for card in cards}
    return [
        by_axis["deliberation"],
        by_axis["uncertainty_awareness"],
    ]


def _content_stream(payload: dict) -> str:
    cards = _select_cards(payload["ui_contract"]["cards"])
    ops = []
    ops.append(_line_ops(18, 211, "COMPARATOR-BOUND CONTROL RECORD", 12, font="F2"))
    ops.append(_line_ops(18, 198, "Artifact-derived interface states; no user-effect claim.", 7))
    x0 = 18
    y0 = 18
    w = 230
    h = 168
    gap = 8
    for i, card in enumerate(cards):
        x = x0 + i * (w + gap)
        ops.append(_rect_ops(x, y0, w, h, (1.0, 1.0, 1.0)))
        ops.append(_rect_ops(x, y0 + h - 33, w, 33, (0.88, 0.88, 0.88)))
        ops.append(_line_ops(x + 8, y0 + h - 14, card["label"].upper(), 9.5, font="F2"))
        ops.append(_line_ops(x + 8, y0 + h - 27, card["headline"], 7.5, font="F2"))
        y = y0 + h - 47
        for label, body in _card_lines(card):
            ops.append(_line_ops(x + 8, y, label, 7, font="F2"))
            y -= 9
            for line in _wrap(body):
                ops.append(_line_ops(x + 8, y, line, 7))
                y -= 8
            y -= 3
    return "".join(ops)


def write_pdf(content: str, out_path: Path) -> None:
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 504 230] /Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> /Contents 6 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
    ]
    stream = content.encode("utf-8")
    objects.append(b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"endstream")
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for idx, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{idx} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("ascii"))
    for off in offsets[1:]:
        pdf.extend(f"{off:010d} 00000 n \n".encode("ascii"))
    pdf.extend(f"trailer << /Root 1 0 R /Size {len(objects) + 1} >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii"))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(pdf)


def main(argv: list[str] | None = None) -> Path:
    parser = argparse.ArgumentParser(description="Plot console v2 UI-contract cards from frozen artifacts.")
    parser.add_argument("--out", type=Path, default=OUT, help="Output PDF path.")
    if argv is not None:
        argv = [str(arg) for arg in argv]
    args = parser.parse_args(argv)
    payload = build_console_payload()
    write_pdf(_content_stream(payload), args.out)
    print(f"Wrote {args.out}")
    return args.out


if __name__ == "__main__":
    main()
