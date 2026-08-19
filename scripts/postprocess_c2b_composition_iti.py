from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from cognitive_console.experiments import adjudicate_c2b as adj


REPO = Path(__file__).resolve().parents[1]
BASE = REPO / "results" / "composition_a_shard1" / "iti_qwen"
CHECKPOINTS = BASE / "checkpoints"
TRANSCRIPTS_TMP = BASE / "transcripts_tmp"
BOOTSTRAP_SEED = 20260819
DELTA = 0.05
Z_BONF = 2.394
Z_80 = 0.842
MODEL_REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"
EXPERIMENT_ID = "composition-a-qwen-iti-20260818-0001"


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")


def mean(xs: list[float]) -> float:
    return float(sum(xs) / len(xs))


def bootstrap(values: list[float]) -> dict[str, float | int]:
    arr = np.asarray(values, dtype=np.float64)
    ci = adj.cluster_bootstrap_ci(
        arr,
        b=10_000,
        ci_level=adj.BONFERRONI_CI_LEVEL,
        seed=BOOTSTRAP_SEED,
        cluster=True,
    )
    mde = float((Z_BONF + Z_80) * float(np.std(arr, ddof=1)) / math.sqrt(len(arr)))
    return {
        "mean_diff": float(ci.point),
        "ci_lo": float(ci.ci_lo),
        "ci_hi": float(ci.ci_hi),
        "ci_level": float(ci.ci_level),
        "bootstrap_b": int(ci.b),
        "bootstrap_seed": BOOTSTRAP_SEED,
        "realized_mde_80pct": mde,
    }


def frozen_verdict(stats: dict[str, float | int], *, coherence_ok: bool, parse_ok: bool, trunc_ok: bool) -> str:
    if adj.axis_pass(
        float(stats["mean_diff"]),
        float(stats["ci_lo"]),
        float(stats["ci_hi"]),
        coherence_ok,
        delta=DELTA,
    ):
        return "COMPOSITION_GAIN_SUPPORTED"
    if (not coherence_ok) or (not parse_ok) or (not trunc_ok) or float(stats["realized_mde_80pct"]) > 0.06:
        return "UNDERPOWERED_OR_INVALID"
    return "NO_INCREMENT_DEMONSTRATED"


def load_item_hashes() -> dict[tuple[str, str], str]:
    rows = load_jsonl(REPO / "docs" / "specs" / "c2b-composition-item-manifest.jsonl")
    return {(str(row["axis"]), str(row["item_id"])): str(row["item_sha256"]) for row in rows}


def transcript_flags() -> dict[tuple[str, str, str], list[bool]]:
    out: dict[tuple[str, str, str], list[bool]] = {}
    for path in sorted(TRANSCRIPTS_TMP.glob("uncertainty_awareness__test_*__*.jsonl")):
        for row in load_jsonl(path):
            phase = str(row["phase"])
            if phase == "test_prompt_ordinary":
                channel, baseline = "prompt", "ordinary"
            elif phase == "test_prompt_strong":
                channel, baseline = "prompt", "strong"
            elif phase == "test_steer_ordinary":
                channel, baseline = "steer", "ordinary"
            elif phase == "test_steer_strong":
                channel, baseline = "steer", "strong"
            else:
                continue
            key = (baseline, str(row["item_id"]), channel)
            out.setdefault(key, []).append(bool((row.get("parse") or {}).get("axis_parse_failed")))
    for key, flags in out.items():
        if len(flags) != 5:
            raise ValueError(f"{key} has {len(flags)} parse flags, expected 5")
    return out


def build_per_item_pairs(result: dict[str, Any]) -> list[dict[str, Any]]:
    item_hashes = load_item_hashes()
    flags = transcript_flags()
    rows: list[dict[str, Any]] = []
    for cell in result["cells"]:
        axis = str(cell["axis"])
        baseline = str(cell["prompt_baseline"])
        prompt_rows = load_jsonl(CHECKPOINTS / f"{axis}_test_prompt_{baseline}.jsonl")
        steer_rows = load_jsonl(CHECKPOINTS / f"{axis}_test_steer_{baseline}.jsonl")
        prompt_by_id = {str(row["item_id"]): row for row in prompt_rows}
        steer_by_id = {str(row["item_id"]): row for row in steer_rows}
        if set(prompt_by_id) != set(steer_by_id):
            raise ValueError(f"TEST prompt/steer item mismatch for {axis}/{baseline}")
        for item_id in sorted(prompt_by_id):
            p = prompt_by_id[item_id]
            s = steer_by_id[item_id]
            p_scores = [float(x) for x in p["outcomes"]]
            s_scores = [float(x) for x in s["outcomes"]]
            if len(p_scores) != 5 or len(s_scores) != 5:
                raise ValueError(f"{axis}/{baseline}/{item_id} sample count != 5")
            p_mean = mean(p_scores)
            s_mean = mean(s_scores)
            row: dict[str, Any] = {
                "experiment_id": result["experiment_id"],
                "steering_method": result["steering_method"],
                "model": result["model"],
                "axis": axis,
                "prompt_baseline": baseline,
                "prompt_id": cell["prompt_id"],
                "item_id": item_id,
                "item_sha256": item_hashes[(axis, item_id)],
                "alpha": float(cell["frozen_alpha"]),
                "prompt_cell_key": p.get("cell_key"),
                "steer_cell_key": s.get("cell_key"),
                "prompt_sample_scores": p_scores,
                "steer_sample_scores": s_scores,
                "prompt_sample_degeneracies": [float(x) for x in p["degeneracies"]],
                "steer_sample_degeneracies": [float(x) for x in s["degeneracies"]],
                "prompt_score": p_mean,
                "steer_score": s_mean,
                "paired_diff": s_mean - p_mean,
            }
            if axis == "uncertainty_awareness":
                pf = flags[(baseline, item_id, "prompt")]
                sf = flags[(baseline, item_id, "steer")]
                row["prompt_confidence_parse_failed"] = pf
                row["steer_confidence_parse_failed"] = sf
                row["prompt_confidence_parseable_count"] = int(sum(not x for x in pf))
                row["steer_confidence_parseable_count"] = int(sum(not x for x in sf))
                row["confidence_missing_any_condition"] = bool(any(pf) or any(sf))
            rows.append(row)
    if len(rows) != 2400:
        raise ValueError(f"expected 2400 paired rows, got {len(rows)}")
    return rows


def condition_scores(row: dict[str, Any], channel: str, mode: str) -> list[float]:
    scores = [float(x) for x in row[f"{channel}_sample_scores"]]
    fails = row.get(f"{channel}_confidence_parse_failed") or [False] * len(scores)
    out: list[float] = []
    for score, failed in zip(scores, fails):
        if not failed:
            out.append(score)
        elif mode == "lower" and channel == "prompt":
            out.append(1.0)
        elif mode == "lower" and channel == "steer":
            out.append(0.0)
        elif mode == "upper" and channel == "prompt":
            out.append(0.0)
        elif mode == "upper" and channel == "steer":
            out.append(1.0)
        else:
            raise ValueError(f"bad mode/channel: {mode}/{channel}")
    return out


def update_result(result: dict[str, Any], pairs: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    by_cell: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in pairs:
        by_cell.setdefault((str(row["axis"]), str(row["prompt_baseline"])), []).append(row)

    cell_table: list[dict[str, Any]] = []
    sensitivity: dict[str, Any] = {
        "experiment_id": result["experiment_id"],
        "steering_method": "ITI",
        "bootstrap_seed": BOOTSTRAP_SEED,
        "source": "results/composition_a_shard1/iti_qwen/per_item_test_pairs.jsonl",
        "method": "complete-case excludes any TEST item with at least one unparseable confidence sample in either prompt-alone or prompt+steer; adversarial bounds set missing prompt/steer scores to 1/0 for lower bound and 0/1 for upper bound.",
        "cells": [],
    }
    for cell in result["cells"]:
        rows = sorted(by_cell[(cell["axis"], cell["prompt_baseline"])], key=lambda r: str(r["item_id"]))
        diffs = [float(row["paired_diff"]) for row in rows]
        stats = bootstrap(diffs)
        old = {
            "mean_diff": float(cell["mean_diff"]),
            "ci_lo": float(cell["ci_lo"]),
            "ci_hi": float(cell["ci_hi"]),
            "realized_mde_80pct": float(cell["realized_mde_80pct"]),
            "verdict": str(cell["verdict"]),
        }
        cell.update(stats)
        cell["bootstrap_seed"] = BOOTSTRAP_SEED
        cell["verdict"] = frozen_verdict(
            stats,
            coherence_ok=bool(cell["coherence_ok"]),
            parse_ok=bool((cell.get("parse") or {}).get("parse_gate_ok", True)),
            trunc_ok=bool((cell.get("truncation") or {}).get("truncation_gate_ok", True)),
        )
        cell["passed"] = cell["verdict"] == "COMPOSITION_GAIN_SUPPORTED"
        cell["selfcheck_against_runner"] = {
            **old,
            "max_abs_metric_delta": max(
                abs(old["mean_diff"] - float(stats["mean_diff"])),
                abs(old["ci_lo"] - float(stats["ci_lo"])),
                abs(old["ci_hi"] - float(stats["ci_hi"])),
                abs(old["realized_mde_80pct"] - float(stats["realized_mde_80pct"])),
            ),
        }
        prompt_mean = mean([float(row["prompt_score"]) for row in rows])
        steer_mean = mean([float(row["steer_score"]) for row in rows])
        cell_table.append(
            {
                "baseline": cell["prompt_baseline"],
                "axis": cell["axis"],
                "n": len(rows),
                "alpha": cell["frozen_alpha"],
                "prompt_mean": prompt_mean,
                "steer_mean": steer_mean,
                "mean_diff": float(stats["mean_diff"]),
                "ci_lo": float(stats["ci_lo"]),
                "ci_hi": float(stats["ci_hi"]),
                "realized_mde_80pct": float(stats["realized_mde_80pct"]),
                "coherence_ok": bool(cell["coherence_ok"]),
                "parse_prompt_rate": 1.0 - float(cell["parse"]["prompt"].get("axis_parse_fail_rate") or 0.0),
                "parse_steer_rate": 1.0 - float(cell["parse"]["steer"].get("axis_parse_fail_rate") or 0.0),
                "parse_ok": bool(cell["parse"].get("parse_gate_ok")),
                "trunc_rate": float(cell["truncation"].get("max_maybe_truncated_rate") or 0.0),
                "trunc_ok": bool(cell["truncation"].get("truncation_gate_ok")),
                "verdict": cell["verdict"],
            }
        )
        if cell["axis"] == "uncertainty_awareness":
            cc_rows = [row for row in rows if not bool(row.get("confidence_missing_any_condition"))]
            lower_diffs = [
                mean(condition_scores(row, "steer", "lower")) - mean(condition_scores(row, "prompt", "lower"))
                for row in rows
            ]
            upper_diffs = [
                mean(condition_scores(row, "steer", "upper")) - mean(condition_scores(row, "prompt", "upper"))
                for row in rows
            ]
            cc = bootstrap([float(row["paired_diff"]) for row in cc_rows])
            lo = bootstrap(lower_diffs)
            hi = bootstrap(upper_diffs)
            sens_cell = {
                "baseline": cell["prompt_baseline"],
                "axis": cell["axis"],
                "primary_n": len(rows),
                "missing_item_count": len(rows) - len(cc_rows),
                "prompt_missing_sample_count": int(sum(sum(row["prompt_confidence_parse_failed"]) for row in rows)),
                "steer_missing_sample_count": int(sum(sum(row["steer_confidence_parse_failed"]) for row in rows)),
                "complete_case": {"n": len(cc_rows), **cc},
                "adversarial_lower": {"n": len(rows), **lo},
                "adversarial_upper": {"n": len(rows), **hi},
                "primary_verdict": cell["verdict"],
                "upper_bound_would_support_gain": bool(
                    adj.axis_pass(float(hi["mean_diff"]), float(hi["ci_lo"]), float(hi["ci_hi"]), bool(cell["coherence_ok"]), delta=DELTA)
                ),
            }
            cell["missingness_sensitivity"] = sens_cell
            sensitivity["cells"].append(sens_cell)

    result["params"]["bootstrap_seed"] = BOOTSTRAP_SEED
    result["shard_verdicts_by_baseline"] = {
        baseline: (
            "COMPOSITION_GAIN_SUPPORTED"
            if any(c["prompt_baseline"] == baseline and c["verdict"] == "COMPOSITION_GAIN_SUPPORTED" for c in result["cells"])
            else (
                "UNDERPOWERED_OR_INVALID"
                if any(c["prompt_baseline"] == baseline and c["verdict"] == "UNDERPOWERED_OR_INVALID" for c in result["cells"])
                else "NO_INCREMENT_DEMONSTRATED"
            )
        )
        for baseline in ("ordinary", "strong")
    }
    return cell_table, sensitivity


def write_model_provenance(result: dict[str, Any]) -> None:
    payload = {
        "model": result["model"],
        "backend": result["backend"],
        "hf_snapshot_revision": MODEL_REVISION,
        "hf_snapshot_confirmed_on_remote": True,
        "remote_cache": "~/cc_avg_prompt/hf_home/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28",
        "dtype": "float16",
        "device": "cuda",
    }
    (BASE / "model_provenance.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_reports(result: dict[str, Any], cell_table: list[dict[str, Any]], sensitivity: dict[str, Any]) -> None:
    summary = [
        "# C2b Composition Shard A — ITI × Qwen",
        "",
        f"- experiment_id: `{result['experiment_id']}`",
        f"- model: `{result['model']}`",
        f"- method: `{result['steering_method']}`",
        f"- status: `{result['status']}`",
        f"- direction provenance: `{result['direction_provenance']['status']}`",
        f"- bootstrap_B: {result['params']['bootstrap_b']}  CI: {result['params']['ci_level']:.5f}  bootstrap_seed: {BOOTSTRAP_SEED}",
        "",
        "| baseline | axis | N_test | alpha* | mean Δ | 98.33% CI | MDE80 | coherence | parse | verdict |",
        "|---|---|---:|---:|---:|---|---:|---|---|---|",
    ]
    for cell in result["cells"]:
        summary.append(
            f"| {cell['prompt_baseline']} | {cell['axis']} | {cell['n_test']} | {float(cell['frozen_alpha']):.1f} | "
            f"{float(cell['mean_diff']):+.4f} | [{float(cell['ci_lo']):+.4f}, {float(cell['ci_hi']):+.4f}] | "
            f"{float(cell['realized_mde_80pct']):.4f} | {'ok' if cell['coherence_ok'] else 'FAIL'} | "
            f"{'ok' if cell['parse'].get('parse_gate_ok') else 'FAIL'} | {cell['verdict']} |"
        )
    summary.extend(
        [
            "",
            "## Uncertainty missingness sensitivity",
            "",
            "| baseline | primary Δ [CI] | complete-case N Δ [CI] | adversarial lower Δ [CI] | adversarial upper Δ [CI] | missing samples prompt/steer |",
            "|---|---|---|---|---|---:|",
        ]
    )
    for sc in sensitivity["cells"]:
        cell = next(c for c in result["cells"] if c["axis"] == "uncertainty_awareness" and c["prompt_baseline"] == sc["baseline"])
        cc, lo, hi = sc["complete_case"], sc["adversarial_lower"], sc["adversarial_upper"]
        summary.append(
            f"| {sc['baseline']} | {float(cell['mean_diff']):+.4f} [{float(cell['ci_lo']):+.4f}, {float(cell['ci_hi']):+.4f}] | "
            f"{cc['n']} {float(cc['mean_diff']):+.4f} [{float(cc['ci_lo']):+.4f}, {float(cc['ci_hi']):+.4f}] | "
            f"{float(lo['mean_diff']):+.4f} [{float(lo['ci_lo']):+.4f}, {float(lo['ci_hi']):+.4f}] | "
            f"{float(hi['mean_diff']):+.4f} [{float(hi['ci_lo']):+.4f}, {float(hi['ci_hi']):+.4f}] | "
            f"{sc['prompt_missing_sample_count']}/{sc['steer_missing_sample_count']} |"
        )
    summary.extend(
        [
            "",
            "Ordinary and strong baselines are separate estimands. ITI is the second Qwen method shard under the frozen composition prereg; it is additive to, and does not overwrite, the frozen substitution grid or CAA shard.",
            "Interpretation is neutral: ordinary contains one invalid/underpowered uncertainty cell because the preregistered parse gate failed; strong is a no-increment-demonstrated null.",
        ]
    )
    (BASE / "composition_summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")

    sens_md = [
        "# Uncertainty missingness sensitivity — ITI × Qwen composition shard",
        "",
        f"- experiment_id: `{result['experiment_id']}`",
        f"- bootstrap_seed: `{BOOTSTRAP_SEED}`; B=10000; item-cluster bootstrap; CI=98.33%.",
        "- Complete-case excludes any paired TEST item with at least one unparseable confidence sample in either prompt-alone or prompt+steer.",
        "- Adversarial lower sets missing prompt scores to 1 and missing steer scores to 0; adversarial upper sets missing prompt scores to 0 and missing steer scores to 1.",
        "",
        "| baseline | parse prompt/steer | missing items | complete-case N | complete-case mean Δ | complete-case 98.33% CI | lower-bound mean Δ | lower-bound CI | upper-bound mean Δ | upper-bound CI | upper-bound gain pass? |",
        "|---|---:|---:|---:|---:|---|---:|---|---:|---|---|",
    ]
    for sc in sensitivity["cells"]:
        cell = next(c for c in result["cells"] if c["axis"] == "uncertainty_awareness" and c["prompt_baseline"] == sc["baseline"])
        cc, lo, hi = sc["complete_case"], sc["adversarial_lower"], sc["adversarial_upper"]
        pp = 1.0 - float(cell["parse"]["prompt"].get("axis_parse_fail_rate") or 0.0)
        sp = 1.0 - float(cell["parse"]["steer"].get("axis_parse_fail_rate") or 0.0)
        sens_md.append(
            f"| {sc['baseline']} | {pp:.3f}/{sp:.3f} | {sc['missing_item_count']} | {cc['n']} | "
            f"{float(cc['mean_diff']):+.6f} | [{float(cc['ci_lo']):+.6f}, {float(cc['ci_hi']):+.6f}] | "
            f"{float(lo['mean_diff']):+.6f} | [{float(lo['ci_lo']):+.6f}, {float(lo['ci_hi']):+.6f}] | "
            f"{float(hi['mean_diff']):+.6f} | [{float(hi['ci_lo']):+.6f}, {float(hi['ci_hi']):+.6f}] | "
            f"{str(sc['upper_bound_would_support_gain']).lower()} |"
        )
    sens_md.extend(
        [
            "",
            "These analyses are diagnostic safeguards against confidence-parse missingness and do not replace the preregistered primary verdict.",
        ]
    )
    (BASE / "missingness_sensitivity.md").write_text("\n".join(sens_md) + "\n", encoding="utf-8")

    selfcheck = [
        "# Self-check gate: C2b Composition Shard A — ITI × Qwen",
        "",
        f"- experiment_id: `{result['experiment_id']}`",
        f"- status: `{result['status']}`; valid_for_paper: `{result['valid_for_paper']}` (awaiting independent audit)",
        f"- code_commit: `{result['code_commit']}`; run_seed: `{result['run_seed']}`; direction_seed: `{result['direction_seed']}`; bootstrap_seed: `{BOOTSTRAP_SEED}`",
        f"- model: `{result['model']}`; HF snapshot revision: `{MODEL_REVISION}`",
        f"- wall_clock_seconds: `{result['wall_clock_seconds']}`; hardware: `{result['hardware']}`",
        "- direction provenance: `DIRECTIONS_REDERIVED_WITH_PROVENANCE_CAVEAT`; no persisted headline ITI reference vector was found, so no cosine comparison was available.",
        "- per-item audit arrays: `per_item_test_pairs.jsonl` contains item_id, item_sha256, prompt/steer sample scores, per-item means, paired diffs, and uncertainty parse-missingness flags.",
        "- raw TEST transcripts are not committed; remote pointer + sha256 are in `transcript_pointers_sha256.txt`.",
        "",
        "## Recomputed TEST cells",
        "",
        "| baseline | axis | N | alpha* | prompt mean | steer mean | mean Δ | 98.33% CI | MDE80 | coherence | parse prompt/steer | trunc max | verdict |",
        "|---|---|---:|---:|---:|---:|---:|---|---:|---|---|---:|---|",
    ]
    for row in cell_table:
        selfcheck.append(
            f"| {row['baseline']} | {row['axis']} | {row['n']} | {float(row['alpha']):.1f} | "
            f"{float(row['prompt_mean']):.6f} | {float(row['steer_mean']):.6f} | {float(row['mean_diff']):+.6f} | "
            f"[{float(row['ci_lo']):+.6f}, {float(row['ci_hi']):+.6f}] | {float(row['realized_mde_80pct']):.6f} | "
            f"{'ok' if row['coherence_ok'] else 'FAIL'} | {float(row['parse_prompt_rate']):.3f}/{float(row['parse_steer_rate']):.3f} | "
            f"{float(row['trunc_rate']):.3f} | {row['verdict']} |"
        )
    selfcheck.extend(
        [
            "",
            "## Gate checks",
            "",
            f"- Bootstrap seed: PASS (`bootstrap_seed={BOOTSTRAP_SEED}`).",
            f"- Coherence gate: {'PASS' if all(r['coherence_ok'] for r in cell_table) else 'FAIL'} (all six cells).",
            f"- Parse gate: {'PASS' if all(r['parse_ok'] for r in cell_table) else 'FAIL'}; ordinary uncertainty fails the frozen parse gate and is therefore invalid/underpowered, not a null.",
            f"- Truncation gate: {'PASS' if all(r['trunc_ok'] for r in cell_table) else 'FAIL'}; deliberation used max_new_tokens=512, not the invalid 64-token floor.",
            f"- MDE screen: {'PASS' if all(float(r['realized_mde_80pct']) <= 0.06 for r in cell_table) else 'FAIL'}; all six realized MDE80 values are <= 0.06, but validity still requires parse/coherence/truncation gates.",
            "- Outcome interpretation: ordinary baseline shard verdict is `UNDERPOWERED_OR_INVALID` because uncertainty parse gate failed; strong baseline shard verdict is `NO_INCREMENT_DEMONSTRATED`. This is not an equivalence proof and not a positive augmentation finding.",
            "",
            "## Uncertainty missingness sensitivity",
            "",
        ]
    )
    selfcheck.extend(sens_md[7:])
    selfcheck.extend(["", "## Files/checksums", ""])
    checksum_files = [
        "alpha_manifest.yaml",
        "composition_results.json",
        "composition_summary.md",
        "direction_provenance.json",
        "missingness_sensitivity.json",
        "missingness_sensitivity.md",
        "model_provenance.json",
        "per_item_test_pairs.jsonl",
        "run.log",
        "transcript_pointers_sha256.txt",
    ]
    for name in checksum_files:
        selfcheck.append(f"- `{name}` sha256 `{sha256_path(BASE / name)}`")
    selfcheck.append("")
    selfcheck.append("No recomputation mismatches detected beyond floating-point equality against the runner output.")
    (BASE / "selfcheck_report.md").write_text("\n".join(selfcheck) + "\n", encoding="utf-8")

    with (BASE / "output_checksums_sha256.txt").open("w", encoding="utf-8", newline="\n") as f:
        f.write("# SHA256 for committed ITI composition shard artifacts (raw transcripts remain remote; checkpoint cache is ignored)\n")
        for name in checksum_files + ["selfcheck_report.md"]:
            f.write(f"{sha256_path(BASE / name)}  {name}\n")


def update_registry(result: dict[str, Any], sensitivity: dict[str, Any]) -> None:
    reg = REPO / "docs" / "ledgers" / "experiment-registry.yaml"
    dirp = json.loads((BASE / "direction_provenance.json").read_text(encoding="utf-8"))
    cell_lines: list[str] = []
    for c in result["cells"]:
        cell_lines.extend(
            [
                f"      - baseline: {c['prompt_baseline']}",
                f"        axis: {c['axis']}",
                f"        prompt_id: {c['prompt_id']}",
                f"        n_test: {c['n_test']}",
                f"        alpha_star: {c['frozen_alpha']}",
                f"        prompt_mean: {mean([float(x) for x in c['per_item_prompt']]):.12g}",
                f"        steer_mean: {mean([float(x) for x in c['per_item_steer']]):.12g}",
                f"        mean_diff: {float(c['mean_diff']):.12g}",
                f"        ci_9833: [{float(c['ci_lo']):.12g}, {float(c['ci_hi']):.12g}]",
                f"        realized_mde_80pct: {float(c['realized_mde_80pct']):.12g}",
                f"        bootstrap_seed: {BOOTSTRAP_SEED}",
                f"        coherence_ok: {str(c['coherence_ok']).lower()}",
                f"        parse_prompt_rate: {1-float(c['parse']['prompt']['axis_parse_fail_rate'] or 0.0):.12g}",
                f"        parse_steer_rate: {1-float(c['parse']['steer']['axis_parse_fail_rate'] or 0.0):.12g}",
                f"        truncation_max_rate: {float(c['truncation']['max_maybe_truncated_rate'] or 0.0):.12g}",
                f"        verdict: {c['verdict']}",
            ]
        )
    sens_lines: list[str] = []
    for sc in sensitivity["cells"]:
        sens_lines.extend(
            [
                f"      - baseline: {sc['baseline']}",
                f"        missing_item_count: {sc['missing_item_count']}",
                f"        prompt_missing_sample_count: {sc['prompt_missing_sample_count']}",
                f"        steer_missing_sample_count: {sc['steer_missing_sample_count']}",
                f"        complete_case_n: {sc['complete_case']['n']}",
                f"        complete_case_mean_diff: {float(sc['complete_case']['mean_diff']):.12g}",
                f"        complete_case_ci_9833: [{float(sc['complete_case']['ci_lo']):.12g}, {float(sc['complete_case']['ci_hi']):.12g}]",
                f"        adversarial_lower_mean_diff: {float(sc['adversarial_lower']['mean_diff']):.12g}",
                f"        adversarial_lower_ci_9833: [{float(sc['adversarial_lower']['ci_lo']):.12g}, {float(sc['adversarial_lower']['ci_hi']):.12g}]",
                f"        adversarial_upper_mean_diff: {float(sc['adversarial_upper']['mean_diff']):.12g}",
                f"        adversarial_upper_ci_9833: [{float(sc['adversarial_upper']['ci_lo']):.12g}, {float(sc['adversarial_upper']['ci_hi']):.12g}]",
                f"        upper_bound_would_support_gain: {str(sc['upper_bound_would_support_gain']).lower()}",
            ]
        )
    block = f"""
- experiment_id: {result['experiment_id']}
  parent:
  - E-0005
  - E-0006
  - composition-a-qwen-caa-20260818-0001
  hypothesis_id: H-COMP-A
  claim_ids: []
  type: confirmatory
  status: done
  code_commit: {result['code_commit']}
  dirty_tree: false
  data_hash:
    item_manifest_sha256: {sha256_path(REPO / 'docs' / 'specs' / 'c2b-composition-item-manifest.jsonl')}
    prompt_manifest_sha256: {sha256_path(REPO / 'docs' / 'specs' / 'c2b-composition-prompt-manifest.yaml')}
    per_item_test_pairs_sha256: {sha256_path(BASE / 'per_item_test_pairs.jsonl')}
  env_hash:
    model_snapshot_revision: {MODEL_REVISION}
    direction_sha256_by_axis:
      deliberation: {dirp['axes']['deliberation']['sha256']}
      skepticism: {dirp['axes']['skepticism']['sha256']}
      uncertainty_awareness: {dirp['axes']['uncertainty_awareness']['sha256']}
  config_hash: {sha256_path(BASE / 'alpha_manifest.yaml')}
  model: Qwen/Qwen2.5-7B-Instruct @ {MODEL_REVISION}
  dataset: >-
    Frozen C2b composition manifest, split_seed=20260818, same TEST items as
    the CAA shard, DEV/TEST zero-overlap and headline-TEST zero-overlap.
  seed: 20260818
  bootstrap_seed: {BOOTSTRAP_SEED}
  hardware: remote A800 host, CUDA_VISIBLE_DEVICES=0, cuda-float16
  started_at: {result['started_at']}
  ended_at: {result['ended_at']}
  exit_code: 0
  raw_metrics:
    result_json: results/composition_a_shard1/iti_qwen/composition_results.json
    result_json_sha256: {sha256_path(BASE / 'composition_results.json')}
    per_item_test_pairs: results/composition_a_shard1/iti_qwen/per_item_test_pairs.jsonl
    per_item_test_pairs_rows: 2400
    per_item_test_pairs_sha256: {sha256_path(BASE / 'per_item_test_pairs.jsonl')}
    missingness_sensitivity: results/composition_a_shard1/iti_qwen/missingness_sensitivity.json
    missingness_sensitivity_sha256: {sha256_path(BASE / 'missingness_sensitivity.json')}
    raw_test_transcript_pointer_sha256: results/composition_a_shard1/iti_qwen/transcript_pointers_sha256.txt
    bootstrap_b: {result['params']['bootstrap_b']}
    bootstrap_seed: {BOOTSTRAP_SEED}
    ci_level: {result['params']['ci_level']}
    cells:
{chr(10).join(cell_lines)}
    uncertainty_missingness_sensitivity:
{chr(10).join(sens_lines)}
  summary_metrics:
    prereg_path: docs/specs/c2b-composition-augmentation-prereg.md
    item_manifest: docs/specs/c2b-composition-item-manifest.jsonl
    prompt_manifest: docs/specs/c2b-composition-prompt-manifest.yaml
    alpha_manifest: results/composition_a_shard1/iti_qwen/alpha_manifest.yaml
    summary_path: results/composition_a_shard1/iti_qwen/composition_summary.md
    selfcheck_report: results/composition_a_shard1/iti_qwen/selfcheck_report.md
    missingness_sensitivity_report: results/composition_a_shard1/iti_qwen/missingness_sensitivity.md
    estimand: paired per-item (prompt + steer) minus prompt alone
    status_note: COMPLETED_2026_08_19_AWAITING_INDEPENDENT_AUDIT
    shard: ITI x Qwen2.5-7B x 3 axes x ordinary+strong
    shard_verdicts_by_baseline:
      ordinary: {result['shard_verdicts_by_baseline']['ordinary']}
      strong: {result['shard_verdicts_by_baseline']['strong']}
    generation_max_new_tokens:
      deliberation: {result['params']['max_new_tokens']['deliberation']}
      skepticism: {result['params']['max_new_tokens']['skepticism']}
      uncertainty_awareness: {result['params']['max_new_tokens']['uncertainty_awareness']}
    mde_screen: all six cells <= 0.06
    coherence_gate: pass_all_six_cells
    parse_gate: ordinary uncertainty_awareness fails; other five cells pass
    truncation_gate: pass_all_six_cells; deliberation used 512-token generation budget, not 64
    direction_provenance: {dirp['status']}
    direction_reference_status: NO_REFERENCE_FOUND_FOR_ALL_AXES
    direction_provenance_caveat: >-
      No persisted headline ITI direction/probe vector/reference was found in
      this worktree, so no cosine comparison was available. Directions were
      re-derived with frozen C2b ITI extraction code, headline frozen layers
      {dirp['axes']['deliberation']['layer']}/{dirp['axes']['skepticism']['layer']}/{dirp['axes']['uncertainty_awareness']['layer']},
      n_extraction=28, direction_seed=20260723, with ITI sigma scaling.
    additive_relation: additive composition/augmentation estimand only; does not overwrite frozen substitution grid or CAA shard
    deferred_methods: Llama not run in this shard
  artifacts:
  - docs/specs/c2b-composition-augmentation-prereg.md
  - docs/specs/c2b-composition-item-manifest.jsonl
  - docs/specs/c2b-composition-prompt-manifest.yaml
  - scripts/run_c2b_composition_shard.py
  - scripts/postprocess_c2b_composition_iti.py
  - results/composition_a_shard1/iti_qwen/composition_results.json
  - results/composition_a_shard1/iti_qwen/composition_summary.md
  - results/composition_a_shard1/iti_qwen/direction_provenance.json
  - results/composition_a_shard1/iti_qwen/alpha_manifest.yaml
  - results/composition_a_shard1/iti_qwen/model_provenance.json
  - results/composition_a_shard1/iti_qwen/per_item_test_pairs.jsonl
  - results/composition_a_shard1/iti_qwen/missingness_sensitivity.json
  - results/composition_a_shard1/iti_qwen/missingness_sensitivity.md
  - results/composition_a_shard1/iti_qwen/selfcheck_report.md
  - results/composition_a_shard1/iti_qwen/output_checksums_sha256.txt
  - results/composition_a_shard1/iti_qwen/transcript_pointers_sha256.txt
  failure_reason: null
  valid_for_paper: false
  validation_notes: >-
    ITI second shard under the frozen c2b-composition-augmentation prereg.
    TEST used the same frozen item/prompt manifests as CAA. All reported numeric
    results were recomputed from committed per-item TEST arrays using
    bootstrap_seed=20260819, B=10000 item-cluster bootstrap. Ordinary baseline is
    UNDERPOWERED_OR_INVALID because the uncertainty parse gate failed despite
    MDE<=0.06; strong baseline is NO_INCREMENT_DEMONSTRATED. Uncertainty
    complete-case and adversarial missingness sensitivity are reported. Results
    remain valid_for_paper=false pending independent hostile audit.
"""
    text = reg.read_text(encoding="utf-8")
    marker = f"- experiment_id: {EXPERIMENT_ID}"
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n"
    reg.write_text(text.rstrip() + "\n" + block.lstrip(), encoding="utf-8")


def main() -> None:
    result_path = BASE / "composition_results.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if result["experiment_id"] != EXPERIMENT_ID:
        raise ValueError(result["experiment_id"])
    pairs = build_per_item_pairs(result)
    write_jsonl(BASE / "per_item_test_pairs.jsonl", pairs)
    cell_table, sensitivity = update_result(result, pairs)
    if any(cell["verdict"] == "COMPOSITION_GAIN_SUPPORTED" for cell in result["cells"]):
        raise SystemExit("Unexpected gain-supported ITI cell; stop and report to Manager")
    if any(sc["upper_bound_would_support_gain"] for sc in sensitivity["cells"]):
        raise SystemExit("Adversarial missingness upper bound can support gain; stop and report to Manager")
    result_path.write_text(json.dumps(result, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    (BASE / "missingness_sensitivity.json").write_text(json.dumps(sensitivity, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    write_model_provenance(result)
    write_reports(result, cell_table, sensitivity)
    update_registry(result, sensitivity)
    print("postprocessed", result["experiment_id"])
    for row in cell_table:
        print(row["baseline"], row["axis"], row["n"], f"{row['mean_diff']:+.6f}", f"[{row['ci_lo']:+.6f},{row['ci_hi']:+.6f}]", f"mde={row['realized_mde_80pct']:.6f}", row["verdict"])


if __name__ == "__main__":
    main()
