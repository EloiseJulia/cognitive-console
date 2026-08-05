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


def _wrap(text: str, width: int = 58) -> list[str]:
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
    return lines[:5]


def _reader_text(text: object) -> str:
    replacements = {
        "KILL_PLAN_D": "pre-registered kill/null outcome",
        "NON_TRANSFER_GENERALIZED": "generalized non-transfer result",
        "valid_for_paper=false": "exploratory, not used as confirmatory evidence",
        "not_implemented": "not implemented in this run",
        "not_run_required_before_confirmatory_claim": "human-rater calibration pending",
        "human-alpha PENDING -> not-yet-confirmatory": "not yet confirmatory",
    }
    out = str(text)
    for old, new in replacements.items():
        out = out.replace(old, new)
    return out


def _line_ops(x: float, y: float, text: str, size: int = 8) -> str:
    return (
        f"0 0 0 rg 0 0 0 RG "
        f"BT /F1 {size} Tf {x:.1f} {y:.1f} Td "
        f"({_esc(_reader_text(text))}) Tj ET\n"
    )


def _rect_ops(x: float, y: float, w: float, h: float, fill: tuple[float, float, float]) -> str:
    r, g, b = fill
    return f"{r:.3f} {g:.3f} {b:.3f} rg {x:.1f} {y:.1f} {w:.1f} {h:.1f} re f\n0 0 0 RG {x:.1f} {y:.1f} {w:.1f} {h:.1f} re S\n"


def _signal_line(label: str, body: str) -> str:
    return f"{label}: {body}"


def _card_lines(card: dict) -> list[str]:
    read = card["read_status"]
    transfer = card["transfer_verdict"]
    ceiling = card["prompt_ceiling"]
    harm = card["calibration_harm"]
    tier = card["evidence_tier"]
    lines = [
        card["headline"],
        _signal_line("READ", f"{read.get('status')} {read.get('summary', '')}"),
        _signal_line("TRANSFER", f"{transfer.get('verdict')} {transfer.get('summary', '')}"),
        _signal_line("PROMPT-CEILING", ceiling.get("summary", "n/a")),
        _signal_line("CALIBRATION-HARM", f"{harm.get('status')} {harm.get('summary', '')}"),
        _signal_line("EVIDENCE-TIER", f"{tier.get('tier')} ({'; '.join(tier.get('notes', []))})"),
    ]
    return lines


def _select_cards(cards: Iterable[dict]) -> list[dict]:
    by_axis = {card["axis"]: card for card in cards}
    return [
        by_axis["deliberation"],
        by_axis["uncertainty_awareness"],
    ]


def _content_stream(payload: dict) -> str:
    cards = _select_cards(payload["ui_contract"]["cards"])
    ops = []
    ops.append(_line_ops(44, 790, "Cognitive Console v2: five-signal UI contract", 16))
    ops.append(_line_ops(44, 772, "All numbers are read from frozen local artifacts; no humans/GPU/API/model calls.", 8))
    x0 = 44
    y0 = 520
    w = 360
    h = 224
    gap = 18
    for i, card in enumerate(cards):
        x = x0 + i * (w + gap)
        color = (1.0, 0.88, 0.88) if card["calibration_harm"].get("severity") == "red" else (0.92, 0.94, 1.0)
        ops.append(_rect_ops(x, y0, w, h, color))
        ops.append(_line_ops(x + 10, y0 + h - 18, card["label"], 11))
        y = y0 + h - 38
        for raw in _card_lines(card):
            for line in _wrap(raw):
                ops.append(_line_ops(x + 10, y, line, 7))
                y -= 10
            y -= 2
    psr = payload["ui_contract"]["psr_method_strength"]
    ops.append(_rect_ops(44, 424, 750, 62, (0.94, 0.94, 0.94)))
    ops.append(_line_ops(56, 468, "Method-strength robustness: steering still fails on TEST", 11))
    psr_bits = [
        f"{row['label']}: pass={row['passed']} Δ={_fmt(row['delta'])} CI=[{_fmt(row['ci_lo'])},{_fmt(row['ci_hi'])}]"
        for row in psr["rows"]
    ]
    ops.append(_line_ops(56, 450, f"{psr['summary']} Outcome={psr['verdict']}.", 8))
    ops.append(_line_ops(56, 436, " | ".join(psr_bits), 7))
    ops.append(_line_ops(44, 396, "Numbers derived from frozen, independently audited artifacts.", 7))
    return "".join(ops)


def write_pdf(content: str, out_path: Path) -> None:
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 842 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
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
