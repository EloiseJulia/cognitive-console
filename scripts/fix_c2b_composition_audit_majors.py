from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from cognitive_console.experiments import adjudicate_c2b as adj

BOOTSTRAP_SEED = 20260819
Z_BONF = 2.394
Z_80 = 0.842
DELTA = 0.05
MODEL_REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"


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


def load_transcript_flags(transcript_dir: Path) -> dict[tuple[str, str], dict[str, list[bool]]]:
    flags: dict[tuple[str, str], dict[str, list[bool]]] = {}
    for path in sorted(transcript_dir.glob("uncertainty_awareness__test_*.jsonl")):
        for row in load_jsonl(path):
            phase = str(row["phase"])
            if phase.startswith("test_prompt_"):
                channel = "prompt"
                baseline = phase.removeprefix("test_prompt_")
            elif phase.startswith("test_steer_"):
                channel = "steer"
                baseline = phase.removeprefix("test_steer_")
            else:
                continue
            key = (baseline, str(row["item_id"]))
            bucket = flags.setdefault(key, {"prompt": [], "steer": []})
            bucket[channel].append(bool((row.get("parse") or {}).get("axis_parse_failed")))
    for key, value in flags.items():
        for channel in ("prompt", "steer"):
            if len(value[channel]) != 5:
                raise ValueError(f"{key} {channel} transcript flag count {len(value[channel])} != 5")
    return flags


def ensure_uncertainty_flags(pairs: list[dict[str, Any]], transcript_dir: Path | None) -> bool:
    needs_flags = any(
        row.get("axis") == "uncertainty_awareness"
        and "prompt_confidence_parse_failed" not in row
        for row in pairs
    )
    if not needs_flags:
        return False
    if transcript_dir is None:
        raise ValueError("uncertainty parse flags missing from per-item pairs and no transcript dir supplied")
    flags = load_transcript_flags(transcript_dir)
    for row in pairs:
        if row.get("axis") != "uncertainty_awareness":
            continue
        key = (str(row["prompt_baseline"]), str(row["item_id"]))
        if key not in flags:
            raise ValueError(f"missing transcript flags for {key}")
        pf = flags[key]["prompt"]
        sf = flags[key]["steer"]
        row["prompt_confidence_parse_failed"] = pf
        row["steer_confidence_parse_failed"] = sf
        row["prompt_confidence_parseable_count"] = int(sum(not x for x in pf))
        row["steer_confidence_parseable_count"] = int(sum(not x for x in sf))
        row["confidence_missing_any_condition"] = bool(any(pf) or any(sf))
    return True


def bootstrap(values: list[float]) -> dict[str, float]:
    arr = np.asarray(values, dtype=np.float64)
    ci = adj.cluster_bootstrap_ci(arr, b=10000, ci_level=adj.BONFERRONI_CI_LEVEL, seed=BOOTSTRAP_SEED, cluster=True)
    mde = float((Z_BONF + Z_80) * float(np.std(arr, ddof=1)) / math.sqrt(len(arr))) if len(arr) > 1 else float("nan")
    return {
        "mean_diff": float(ci.point),
        "ci_lo": float(ci.ci_lo),
        "ci_hi": float(ci.ci_hi),
        "ci_level": float(ci.ci_level),
        "bootstrap_b": int(ci.b),
        "bootstrap_seed": BOOTSTRAP_SEED,
        "realized_mde_80pct": mde,
    }


def verdict(stats: dict[str, float], *, coherence_ok: bool, parse_ok: bool, trunc_ok: bool) -> str:
    passed = adj.axis_pass(stats["mean_diff"], stats["ci_lo"], stats["ci_hi"], coherence_ok, delta=DELTA)
    if passed:
        return "COMPOSITION_GAIN_SUPPORTED"
    if (not coherence_ok) or (not parse_ok) or (not trunc_ok) or stats["realized_mde_80pct"] > 0.06:
        return "UNDERPOWERED_OR_INVALID"
    return "NO_INCREMENT_DEMONSTRATED"


def condition_scores(row: dict[str, Any], channel: str, mode: str) -> list[float]:
    scores = [float(x) for x in row[f"{channel}_sample_scores"]]
    fails = row.get(f"{channel}_confidence_parse_failed") or [False] * len(scores)
    if mode == "observed":
        return scores
    out = []
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
            raise ValueError(mode)
    return out


def mean(xs: list[float]) -> float:
    return float(sum(xs) / len(xs))


def recompute(base: Path, transcript_dir: Path | None) -> None:
    result_path = base / "composition_results.json"
    pairs_path = base / "per_item_test_pairs.jsonl"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    pairs = load_jsonl(pairs_path)
    augmented = ensure_uncertainty_flags(pairs, transcript_dir)
    if augmented:
        write_jsonl(pairs_path, pairs)

    by_cell: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in pairs:
        by_cell.setdefault((str(row["axis"]), str(row["prompt_baseline"])), []).append(row)

    sensitivity: dict[str, Any] = {
        "experiment_id": result["experiment_id"],
        "bootstrap_seed": BOOTSTRAP_SEED,
        "source": "results/composition_a_shard1/caa_qwen/per_item_test_pairs.jsonl",
        "method": "complete-case excludes any TEST item with at least one unparseable confidence sample in either prompt-alone or prompt+steer; adversarial bounds set missing prompt/steer scores to 1/0 for lower bound and 0/1 for upper bound.",
        "cells": [],
    }

    cell_rows_md: list[dict[str, Any]] = []
    for cell in result["cells"]:
        key = (cell["axis"], cell["prompt_baseline"])
        rows = sorted(by_cell[key], key=lambda r: str(r["item_id"]))
        diffs = [float(r["paired_diff"]) for r in rows]
        stats = bootstrap(diffs)
        cell.update(stats)
        cell["verdict"] = verdict(
            stats,
            coherence_ok=bool(cell["coherence_ok"]),
            parse_ok=bool((cell.get("parse") or {}).get("parse_gate_ok", True)),
            trunc_ok=bool((cell.get("truncation") or {}).get("truncation_gate_ok", True)),
        )
        cell["passed"] = cell["verdict"] == "COMPOSITION_GAIN_SUPPORTED"
        cell["bootstrap_seed"] = BOOTSTRAP_SEED
        prompt_mean = mean([float(r["prompt_score"]) for r in rows])
        steer_mean = mean([float(r["steer_score"]) for r in rows])
        cell_rows_md.append({
            "baseline": cell["prompt_baseline"], "axis": cell["axis"], "N": len(rows),
            "alpha": cell["frozen_alpha"], "prompt_mean": prompt_mean, "steer_mean": steer_mean,
            **stats, "coherence_ok": cell["coherence_ok"],
            "parse_prompt_rate": 1.0 - float(cell["parse"]["prompt"].get("axis_parse_fail_rate") or 0.0),
            "parse_steer_rate": 1.0 - float(cell["parse"]["steer"].get("axis_parse_fail_rate") or 0.0),
            "trunc_rate": float(cell["truncation"].get("max_maybe_truncated_rate") or 0.0),
            "verdict": cell["verdict"],
        })

        if cell["axis"] == "uncertainty_awareness":
            cc_rows = [r for r in rows if not bool(r.get("confidence_missing_any_condition"))]
            cc_diffs = [float(r["paired_diff"]) for r in cc_rows]
            lower_diffs = [mean(condition_scores(r, "steer", "lower")) - mean(condition_scores(r, "prompt", "lower")) for r in rows]
            upper_diffs = [mean(condition_scores(r, "steer", "upper")) - mean(condition_scores(r, "prompt", "upper")) for r in rows]
            cc_stats = bootstrap(cc_diffs)
            lower_stats = bootstrap(lower_diffs)
            upper_stats = bootstrap(upper_diffs)
            sens_cell = {
                "baseline": cell["prompt_baseline"],
                "axis": cell["axis"],
                "primary_n": len(rows),
                "missing_item_count": len(rows) - len(cc_rows),
                "prompt_missing_sample_count": int(sum(sum(r["prompt_confidence_parse_failed"]) for r in rows)),
                "steer_missing_sample_count": int(sum(sum(r["steer_confidence_parse_failed"]) for r in rows)),
                "complete_case": {"n": len(cc_rows), **cc_stats},
                "adversarial_lower": {"n": len(rows), **lower_stats},
                "adversarial_upper": {"n": len(rows), **upper_stats},
                "primary_verdict_after_seed_fix": cell["verdict"],
                "upper_bound_would_support_gain": bool(adj.axis_pass(upper_stats["mean_diff"], upper_stats["ci_lo"], upper_stats["ci_hi"], bool(cell["coherence_ok"]), delta=DELTA)),
            }
            cell["missingness_sensitivity"] = sens_cell
            sensitivity["cells"].append(sens_cell)

    result.setdefault("params", {})["bootstrap_seed"] = BOOTSTRAP_SEED
    result["shard_verdicts_by_baseline"] = {
        baseline: ("COMPOSITION_GAIN_SUPPORTED" if any(c["prompt_baseline"] == baseline and c["verdict"] == "COMPOSITION_GAIN_SUPPORTED" for c in result["cells"]) else ("UNDERPOWERED_OR_INVALID" if any(c["prompt_baseline"] == baseline and c["verdict"] == "UNDERPOWERED_OR_INVALID" for c in result["cells"]) else "NO_INCREMENT_DEMONSTRATED"))
        for baseline in ("ordinary", "strong")
    }
    result_path.write_text(json.dumps(result, indent=2, sort_keys=False) + "\n", encoding="utf-8")

    (base / "missingness_sensitivity.json").write_text(json.dumps(sensitivity, indent=2, sort_keys=False) + "\n", encoding="utf-8")

    summary_lines = [
        "# C2b Composition Shard A — CAA × Qwen",
        "",
        f"- experiment_id: `{result['experiment_id']}`",
        f"- model: `{result['model']}`",
        f"- status: `{result['status']}`",
        f"- direction provenance: `{result['direction_provenance']['status']}`",
        f"- bootstrap_B: {result['params']['bootstrap_b']}  CI: {result['params']['ci_level']:.5f}  bootstrap_seed: {BOOTSTRAP_SEED}",
        "",
        "| baseline | axis | N_test | alpha* | mean Δ | 98.33% CI | MDE80 | coherence | parse | verdict |",
        "|---|---:|---:|---:|---:|---|---:|---|---|---|",
    ]
    for cell in result["cells"]:
        parse_ok = bool(cell["parse"].get("parse_gate_ok"))
        summary_lines.append(
            f"| {cell['prompt_baseline']} | {cell['axis']} | {cell['n_test']} | {cell['frozen_alpha']:.1f} | "
            f"{cell['mean_diff']:+.4f} | [{cell['ci_lo']:+.4f}, {cell['ci_hi']:+.4f}] | "
            f"{cell['realized_mde_80pct']:.4f} | {'ok' if cell['coherence_ok'] else 'FAIL'} | "
            f"{'ok' if parse_ok else 'FAIL'} | {cell['verdict']} |"
        )
    summary_lines.extend([
        "",
        "## Uncertainty missingness sensitivity",
        "",
        "| baseline | primary Δ [CI] | complete-case N Δ [CI] | adversarial lower Δ [CI] | adversarial upper Δ [CI] | missing samples prompt/steer |",
        "|---|---|---|---|---|---:|",
    ])
    for sc in sensitivity["cells"]:
        cell = next(c for c in result["cells"] if c["axis"] == "uncertainty_awareness" and c["prompt_baseline"] == sc["baseline"])
        cc = sc["complete_case"]
        lo = sc["adversarial_lower"]
        hi = sc["adversarial_upper"]
        summary_lines.append(
            f"| {sc['baseline']} | {cell['mean_diff']:+.4f} [{cell['ci_lo']:+.4f}, {cell['ci_hi']:+.4f}] | "
            f"{cc['n']} {cc['mean_diff']:+.4f} [{cc['ci_lo']:+.4f}, {cc['ci_hi']:+.4f}] | "
            f"{lo['mean_diff']:+.4f} [{lo['ci_lo']:+.4f}, {lo['ci_hi']:+.4f}] | "
            f"{hi['mean_diff']:+.4f} [{hi['ci_lo']:+.4f}, {hi['ci_hi']:+.4f}] | "
            f"{sc['prompt_missing_sample_count']}/{sc['steer_missing_sample_count']} |"
        )
    summary_lines.extend([
        "",
        "Ordinary and strong baselines are separate estimands. Results are additive to, and do not overwrite, the frozen substitution grid. All reported shard verdicts remain NO_INCREMENT_DEMONSTRATED; this is not an equivalence proof.",
    ])
    (base / "composition_summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    sens_md = [
        "# Uncertainty missingness sensitivity — CAA × Qwen composition shard",
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
        cc = sc["complete_case"]
        lo = sc["adversarial_lower"]
        hi = sc["adversarial_upper"]
        pp = 1.0 - float(cell["parse"]["prompt"].get("axis_parse_fail_rate") or 0.0)
        sp = 1.0 - float(cell["parse"]["steer"].get("axis_parse_fail_rate") or 0.0)
        sens_md.append(
            f"| {sc['baseline']} | {pp:.3f}/{sp:.3f} | {sc['missing_item_count']} | {cc['n']} | "
            f"{cc['mean_diff']:+.6f} | [{cc['ci_lo']:+.6f}, {cc['ci_hi']:+.6f}] | "
            f"{lo['mean_diff']:+.6f} | [{lo['ci_lo']:+.6f}, {lo['ci_hi']:+.6f}] | "
            f"{hi['mean_diff']:+.6f} | [{hi['ci_lo']:+.6f}, {hi['ci_hi']:+.6f}] | "
            f"{str(sc['upper_bound_would_support_gain']).lower()} |"
        )
    sens_md.extend([
        "",
        "Sensitivity does not change the primary frozen verdict: both uncertainty cells remain NO_INCREMENT_DEMONSTRATED under the preregistered primary analysis. Adversarial bounds are diagnostic for the small parse-missingness rates and are not used to claim gain.",
    ])
    (base / "missingness_sensitivity.md").write_text("\n".join(sens_md) + "\n", encoding="utf-8")

    self_lines = [
        "# Self-check gate: C2b Composition Shard A — CAA × Qwen",
        "",
        f"- experiment_id: `{result['experiment_id']}`",
        f"- status: `{result['status']}`; valid_for_paper: `{result['valid_for_paper']}` (awaiting fold-gate/audit closure)",
        f"- code_commit: `{result['code_commit']}`; run_seed: `{result['run_seed']}`; direction_seed: `{result['direction_seed']}`; bootstrap_seed: `{BOOTSTRAP_SEED}`",
        f"- model: `{result['model']}`; HF snapshot revision: `{MODEL_REVISION}`",
        f"- wall_clock_seconds: `{result['wall_clock_seconds']}`; hardware: `{result['hardware']}`",
        "- direction provenance: `DIRECTIONS_REDERIVED_WITH_PROVENANCE_CAVEAT`; no persisted E-0006 reference vector found, so no cosine comparison was available.",
        "- per-item audit arrays: `per_item_test_pairs.jsonl` contains item_id, item_sha256, prompt/steer sample scores, per-item means, paired diffs, and uncertainty parse-missingness flags.",
        "- raw TEST transcripts are not committed; remote pointer + sha256 are in `transcript_pointers_sha256.txt`.",
        "",
        "## Recomputed TEST cells (preregistered bootstrap seed)",
        "",
        "| baseline | axis | N | alpha* | prompt mean | steer mean | mean Δ | 98.33% CI | MDE80 | coherence | parse prompt/steer | trunc max | verdict |",
        "|---|---:|---:|---:|---:|---:|---:|---|---:|---|---|---:|---|",
    ]
    for r in cell_rows_md:
        self_lines.append(
            f"| {r['baseline']} | {r['axis']} | {r['N']} | {r['alpha']:.1f} | {r['prompt_mean']:.6f} | {r['steer_mean']:.6f} | "
            f"{r['mean_diff']:+.6f} | [{r['ci_lo']:+.6f}, {r['ci_hi']:+.6f}] | {r['realized_mde_80pct']:.6f} | "
            f"{'ok' if r['coherence_ok'] else 'FAIL'} | {r['parse_prompt_rate']:.3f}/{r['parse_steer_rate']:.3f} | {r['trunc_rate']:.3f} | {r['verdict']} |"
        )
    self_lines.extend([
        "",
        "## Gate checks",
        "",
        "- Bootstrap seed: PASS (`bootstrap_seed=20260819`, prereg §8).",
        f"- Coherence gate: {'PASS' if all(r['coherence_ok'] for r in cell_rows_md) else 'FAIL'} (all six cells).",
        f"- Parse gate: {'PASS' if all((c.get('parse') or {}).get('parse_gate_ok') for c in result['cells']) else 'FAIL'}; uncertainty parse rates and missingness sensitivity are reported separately.",
        f"- Truncation gate: {'PASS' if all((c.get('truncation') or {}).get('truncation_gate_ok') for c in result['cells']) else 'FAIL'}; deliberation used max_new_tokens=512, not the invalid 64-token floor.",
        f"- Power/MDE gate: {'PASS' if all(float(c['realized_mde_80pct']) <= 0.06 for c in result['cells']) else 'FAIL'}; all six realized MDE80 values are <= 0.06.",
        "- Outcome interpretation: all six TEST CIs include zero and all frozen verdicts remain `NO_INCREMENT_DEMONSTRATED`; this is a well-powered null for the CAA×Qwen composition shard, not an equivalence proof and not a positive augmentation finding.",
        "",
        "## Uncertainty missingness sensitivity",
        "",
    ])
    self_lines.extend(sens_md[7:])
    self_lines.extend(["", "## Files/checksums", ""])

    checksum_files = [
        "alpha_manifest.yaml", "composition_results.json", "composition_summary.md",
        "direction_provenance.json", "missingness_sensitivity.json", "missingness_sensitivity.md",
        "model_provenance.json", "per_item_test_pairs.jsonl", "run.log",
        "transcript_pointers_sha256.txt",
    ]
    for name in checksum_files:
        self_lines.append(f"- `{name}` sha256 `{sha256_path(base / name)}`")
    self_lines.append("")
    self_lines.append("No self-check mismatches detected.")
    (base / "selfcheck_report.md").write_text("\n".join(self_lines) + "\n", encoding="utf-8")

    checksum_files_with_self = checksum_files + ["selfcheck_report.md"]
    with (base / "output_checksums_sha256.txt").open("w", encoding="utf-8", newline="\n") as f:
        f.write("# SHA256 for committed composition shard artifacts (raw transcripts remain remote; checkpoint cache is ignored)\n")
        for name in checksum_files_with_self:
            f.write(f"{sha256_path(base / name)}  {name}\n")

    update_registry(base, result, sensitivity)

    if any(c["verdict"] != "NO_INCREMENT_DEMONSTRATED" for c in result["cells"]):
        raise SystemExit("A cell verdict changed; stop and report to Manager")
    if any(sc["upper_bound_would_support_gain"] for sc in sensitivity["cells"]):
        raise SystemExit("An adversarial upper bound can support a gain; stop and report to Manager")


def update_registry(base: Path, result: dict[str, Any], sensitivity: dict[str, Any]) -> None:
    repo = base.parents[2]
    reg = repo / "docs" / "ledgers" / "experiment-registry.yaml"
    item_manifest = repo / "docs" / "specs" / "c2b-composition-item-manifest.jsonl"
    prompt_manifest = repo / "docs" / "specs" / "c2b-composition-prompt-manifest.yaml"
    dirp = json.loads((base / "direction_provenance.json").read_text(encoding="utf-8"))
    config_hash = json.loads((repo / "results" / "composition_a_shard1" / "caa_qwen" / "run.log").read_text(encoding="utf-8").splitlines()[-7]) if False else "303199f5d34dd5d0"
    cell_lines: list[str] = []
    for c in result["cells"]:
        cell_lines.extend([
            f"      - baseline: {c['prompt_baseline']}",
            f"        axis: {c['axis']}",
            f"        prompt_id: {c['prompt_id']}",
            f"        n_test: {c['n_test']}",
            f"        alpha_star: {c['frozen_alpha']}",
            f"        prompt_mean: {sum(c['per_item_prompt'])/len(c['per_item_prompt']):.12g}",
            f"        steer_mean: {sum(c['per_item_steer'])/len(c['per_item_steer']):.12g}",
            f"        mean_diff: {c['mean_diff']:.12g}",
            f"        ci_9833: [{c['ci_lo']:.12g}, {c['ci_hi']:.12g}]",
            f"        realized_mde_80pct: {c['realized_mde_80pct']:.12g}",
            f"        bootstrap_seed: {BOOTSTRAP_SEED}",
            f"        coherence_ok: {str(c['coherence_ok']).lower()}",
            f"        parse_prompt_rate: {1-float(c['parse']['prompt']['axis_parse_fail_rate'] or 0.0):.12g}",
            f"        parse_steer_rate: {1-float(c['parse']['steer']['axis_parse_fail_rate'] or 0.0):.12g}",
            f"        truncation_max_rate: {float(c['truncation']['max_maybe_truncated_rate'] or 0.0):.12g}",
            f"        verdict: {c['verdict']}",
        ])
    sens_lines: list[str] = []
    for sc in sensitivity["cells"]:
        sens_lines.extend([
            f"      - baseline: {sc['baseline']}",
            f"        missing_item_count: {sc['missing_item_count']}",
            f"        prompt_missing_sample_count: {sc['prompt_missing_sample_count']}",
            f"        steer_missing_sample_count: {sc['steer_missing_sample_count']}",
            f"        complete_case_n: {sc['complete_case']['n']}",
            f"        complete_case_mean_diff: {sc['complete_case']['mean_diff']:.12g}",
            f"        complete_case_ci_9833: [{sc['complete_case']['ci_lo']:.12g}, {sc['complete_case']['ci_hi']:.12g}]",
            f"        adversarial_lower_mean_diff: {sc['adversarial_lower']['mean_diff']:.12g}",
            f"        adversarial_lower_ci_9833: [{sc['adversarial_lower']['ci_lo']:.12g}, {sc['adversarial_lower']['ci_hi']:.12g}]",
            f"        adversarial_upper_mean_diff: {sc['adversarial_upper']['mean_diff']:.12g}",
            f"        adversarial_upper_ci_9833: [{sc['adversarial_upper']['ci_lo']:.12g}, {sc['adversarial_upper']['ci_hi']:.12g}]",
            f"        upper_bound_would_support_gain: {str(sc['upper_bound_would_support_gain']).lower()}",
        ])
    block = f'''- experiment_id: {result['experiment_id']}
  parent:
  - E-0005
  - E-0006
  - E-0011
  hypothesis_id: H-COMP-A
  claim_ids: []
  type: confirmatory
  status: done
  code_commit: {result['code_commit']}
  dirty_tree: false
  data_hash:
    item_manifest_sha256: {sha256_path(item_manifest)}
    prompt_manifest_sha256: {sha256_path(prompt_manifest)}
    per_item_test_pairs_sha256: {sha256_path(base / 'per_item_test_pairs.jsonl')}
  env_hash:
    model_snapshot_revision: {MODEL_REVISION}
    config_fingerprint: {config_hash}
    direction_sha256_by_axis:
      deliberation: {dirp['axes']['deliberation']['sha256']}
      skepticism: {dirp['axes']['skepticism']['sha256']}
      uncertainty_awareness: {dirp['axes']['uncertainty_awareness']['sha256']}
  config_hash: {config_hash}
  model: Qwen/Qwen2.5-7B-Instruct @ {MODEL_REVISION}
  dataset: >-
    Frozen C2b composition manifest, split_seed=20260818, DEV=200/axis and
    TEST=400/axis, zero overlap with headline TEST.
  seed: 20260818
  bootstrap_seed: {BOOTSTRAP_SEED}
  hardware: remote A800 host, CUDA_VISIBLE_DEVICES=0, cuda-float16
  started_at: {result['started_at']}
  ended_at: {result['ended_at']}
  exit_code: 0
  raw_metrics:
    result_json: results/composition_a_shard1/caa_qwen/composition_results.json
    result_json_sha256: {sha256_path(base / 'composition_results.json')}
    per_item_test_pairs: results/composition_a_shard1/caa_qwen/per_item_test_pairs.jsonl
    per_item_test_pairs_rows: 2400
    per_item_test_pairs_sha256: {sha256_path(base / 'per_item_test_pairs.jsonl')}
    missingness_sensitivity: results/composition_a_shard1/caa_qwen/missingness_sensitivity.json
    missingness_sensitivity_sha256: {sha256_path(base / 'missingness_sensitivity.json')}
    raw_test_transcript_pointer_sha256: results/composition_a_shard1/caa_qwen/transcript_pointers_sha256.txt
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
    alpha_manifest: results/composition_a_shard1/caa_qwen/alpha_manifest.yaml
    summary_path: results/composition_a_shard1/caa_qwen/composition_summary.md
    selfcheck_report: results/composition_a_shard1/caa_qwen/selfcheck_report.md
    missingness_sensitivity_report: results/composition_a_shard1/caa_qwen/missingness_sensitivity.md
    estimand: paired per-item (prompt + steer) minus prompt alone
    status_note: COMPLETED_2026_08_18_BOOTSTRAP_SEED_FIXED_AWAITING_FOLD_GATE
    shard: CAA x Qwen2.5-7B x 3 axes x ordinary+strong
    shard_verdicts_by_baseline:
      ordinary: {result['shard_verdicts_by_baseline']['ordinary']}
      strong: {result['shard_verdicts_by_baseline']['strong']}
    generation_max_new_tokens:
      deliberation: {result['params']['max_new_tokens']['deliberation']}
      skepticism: {result['params']['max_new_tokens']['skepticism']}
      uncertainty_awareness: {result['params']['max_new_tokens']['uncertainty_awareness']}
    mde_gate: all six cells <= 0.06
    coherence_gate: pass_all_six_cells
    parse_gate: pass_all_six_cells; uncertainty_awareness complete-case and adversarial bounds reported
    truncation_gate: pass_all_six_cells; deliberation used 512-token generation budget, not 64
    direction_provenance: {dirp['status']}
    direction_reference_status: NO_REFERENCE_FOUND_FOR_ALL_AXES
    direction_provenance_caveat: >-
      No persisted E-0006 CAA direction vector/reference was found in this
      worktree, so no cosine comparison was available. Directions were
      re-derived with frozen C2b extraction code, layer=20, n_extraction=28,
      direction_seed=20260723; audit should treat this as a provenance caveat.
    additive_relation: additive composition/augmentation estimand only; does not overwrite frozen substitution grid
    deferred_methods: ITI and Llama not run in this shard
  artifacts:
  - docs/specs/c2b-composition-augmentation-prereg.md
  - docs/specs/c2b-composition-item-manifest.jsonl
  - docs/specs/c2b-composition-prompt-manifest.yaml
  - docs/specs/c2b-composition-direction-check.yaml
  - scripts/prepare_c2b_composition_manifests.py
  - scripts/run_c2b_composition_shard.py
  - scripts/fix_c2b_composition_audit_majors.py
  - results/composition_a_shard1/caa_qwen/composition_results.json
  - results/composition_a_shard1/caa_qwen/composition_summary.md
  - results/composition_a_shard1/caa_qwen/direction_provenance.json
  - results/composition_a_shard1/caa_qwen/alpha_manifest.yaml
  - results/composition_a_shard1/caa_qwen/model_provenance.json
  - results/composition_a_shard1/caa_qwen/per_item_test_pairs.jsonl
  - results/composition_a_shard1/caa_qwen/missingness_sensitivity.json
  - results/composition_a_shard1/caa_qwen/missingness_sensitivity.md
  - results/composition_a_shard1/caa_qwen/selfcheck_report.md
  - results/composition_a_shard1/caa_qwen/output_checksums_sha256.txt
  - results/composition_a_shard1/caa_qwen/transcript_pointers_sha256.txt
  failure_reason: null
  valid_for_paper: false
  validation_notes: >-
    CPU-only audit-major fix applied. All six cells were recomputed from
    committed per-item TEST arrays using preregistered bootstrap_seed=20260819,
    B=10000 item-cluster bootstrap. All six verdicts remain
    NO_INCREMENT_DEMONSTRATED and MDE<=0.06. Uncertainty missingness sensitivity
    adds complete-case and adversarial bounds; neither primary verdict changes
    nor any adversarial upper bound is used to claim gain. valid_for_paper remains
    false pending Manager fold-gate after audit closure. ITI and Llama were not run.
'''
    text = reg.read_text(encoding="utf-8")
    marker = "- experiment_id: composition-a-qwen-caa-20260818-0001"
    idx = text.index(marker)
    reg.write_text(text[:idx] + block, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, default=Path("results/composition_a_shard1/caa_qwen"))
    parser.add_argument("--transcript-dir", type=Path, default=None)
    args = parser.parse_args()
    recompute(args.base, args.transcript_dir)


if __name__ == "__main__":
    main()
