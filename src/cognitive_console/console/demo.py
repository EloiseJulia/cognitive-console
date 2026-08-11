from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Tuple

from .data_loader import build_console_payload, build_demo_report


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _fmt(x: object) -> str:
    return f"{x:.3f}" if isinstance(x, float) else str(x)


def write_demo_artifacts(out_dir: Path | None = None) -> Tuple[Path, Path]:
    root = _repo_root()
    out_dir = out_dir or (root / "results" / "console_v1_demo")
    out_dir.mkdir(parents=True, exist_ok=True)

    report = build_demo_report(build_console_payload())
    json_path = out_dir / "console_v1_demo_report.json"
    md_path = out_dir / "console_v1_demo_report.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Console v2 UI-contract simulated demo report",
        "",
        "No human labels, GPU, paid APIs, model downloads, or live model calls were used. The flags below are computed from frozen local artifacts.",
        "",
        "## C1 facade-limit flags",
    ]
    for row in report["facade_limit_flags"]:
        lines.append(
            f"- {row['axis']}: ratio={_fmt(row['ratio'])}, CI=[{_fmt(row['ci_lo'])}, {_fmt(row['ci_hi'])}], source={row['source']}"
        )
    lines.extend(["", "## C1 non-facade / overshoot flags"])
    for row in report["facade_non_flags"]:
        lines.append(
            f"- {row['axis']}: ratio={_fmt(row['ratio'])}, CI=[{_fmt(row['ci_lo'])}, {_fmt(row['ci_hi'])}], source={row['source']}"
        )
    lines.extend(["", "## C2 steering degradation or adjudication-fail flags"])
    for row in report["steering_degradation_flags"]:
        lines.append(
            f"- {row['axis']}: Δ={_fmt(row['mean_diff'])}, CI=[{_fmt(row['ci_lo'])}, {_fmt(row['ci_hi'])}], pass={row['passed']}, robust={row['robust']}"
        )
    lines.extend(["", "## E-0006 2×2 uncertainty harm replication flags"])
    for row in report["arm_uncertainty_harm_flags"]:
        lines.append(
            f"- {row['method']}×{row['model_label']}: Δ={_fmt(row['mean_diff'])}, CI=[{_fmt(row['ci_lo'])}, {_fmt(row['ci_hi'])}]"
        )
    lines.extend(["", "## E-0010 legible-but-not-controllable social-axis flags"])
    for row in report["social_legible_but_not_controllable_flags"]:
        read = row["read_status"]
        transfer = row["transfer_verdict"]
        lines.append(
            f"- {row['label']}: {row['interface_action']['summary']}; "
            f"blocking_reason={row['blocking_reason']['summary']}; "
            f"READ={read['status']} token-blind AUC={_fmt(read['value'])}; "
            f"TRANSFER={transfer['verdict']} B−A M1={_fmt(transfer['delta'])}, "
            f"CI=[{_fmt(transfer['ci_lo'])}, {_fmt(transfer['ci_hi'])}], p_bonf={_fmt(transfer['p_bonferroni'])}; "
            f"sources={row['source_files']}"
        )
    lines.extend(["", "## E-0009 PSR method-strength robustness flags"])
    for row in report["psr_method_strength_fail_flags"]:
        lines.append(
            f"- {row['label']}: pass={row['passed']}, Δ={_fmt(row['delta'])}, CI=[{_fmt(row['ci_lo'])}, {_fmt(row['ci_hi'])}], source={row['source']}"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def parse_args(argv: Tuple[str, ...] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate console v1 simulated demo artifacts.")
    parser.add_argument("--out-dir", type=Path, default=None, help="Output directory (default: results\\console_v1_demo).")
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    json_path, md_path = write_demo_artifacts(args.out_dir)
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
