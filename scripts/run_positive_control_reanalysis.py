"""E-0014 PC-0/PC-1 zero-GPU reanalysis of committed artifacts.

The design expected full ``results/arm_full`` transcripts, but this worktree only
commits E-0013 CAA×Qwen uncertainty samples. This script therefore computes the
PC-0 format-compliance endpoint from the available E-0013 per-sample records and
records PC-1 as unavailable rather than fabricating Llama/transcript data.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cognitive_console.experiments import adjudicate_c2b as adj
from cognitive_console.lineage import git_commit, utcnow
from scripts.run_positive_control import SCOPE_GUARD_SENTENCE

DEFAULT_SAMPLES = _REPO / "results" / "E-0013-uncertainty-recheck" / "samples.jsonl"
DEFAULT_OUT_DIR = _REPO / "results" / "E-0014-positive-control"


def _read_jsonl(path: Path) -> List[Dict[str, object]]:
    rows = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _item_means(rows: Iterable[Dict[str, object]], split: str, condition: str) -> Dict[str, float]:
    vals: Dict[str, List[float]] = defaultdict(list)
    for r in rows:
        if r.get("split") == split and r.get("condition") == condition:
            vals[str(r["item_id"])].append(1.0 if bool(r.get("format_compliant")) else 0.0)
    return {k: float(np.mean(v)) for k, v in vals.items()}


def _degeneracy_mean(rows: Iterable[Dict[str, object]], split: str, condition: str) -> Optional[float]:
    vals = [float(r["sample_degeneracy"]) for r in rows
            if r.get("split") == split and r.get("condition") == condition and "sample_degeneracy" in r]
    return float(np.mean(vals)) if vals else None


def _paired_delta(a: Dict[str, float], b: Dict[str, float], *, seed: int, bootstrap_b: int) -> Dict[str, object]:
    ids = sorted(set(a) & set(b))
    diffs = np.asarray([a[i] - b[i] for i in ids], dtype=np.float64)
    ci = adj.cluster_bootstrap_ci(diffs, b=int(bootstrap_b), ci_level=adj.BONFERRONI_CI_LEVEL, seed=seed, cluster=True)
    return {
        "point": float(ci.point), "ci_lo": float(ci.ci_lo), "ci_hi": float(ci.ci_hi),
        "ci_level": float(ci.ci_level), "bootstrap_b": int(bootstrap_b), "n_items": len(ids),
        "item_ids": ids,
    }


def reanalyse(samples_path: Path, *, bootstrap_b: int, seed: int) -> Dict[str, object]:
    rows = _read_jsonl(samples_path)
    cells = sorted({str(r.get("cell")) for r in rows})
    qwen_rows = [r for r in rows if r.get("cell") == "caa__qwen2.5-7b"]
    prompt = _item_means(qwen_rows, "test", "prompt")
    steer = _item_means(qwen_rows, "test", "steer")
    baseline = _item_means(qwen_rows, "test", "baseline")
    available = bool(prompt and steer and baseline)
    pc0 = {"status": "unavailable"}
    if available:
        steer_minus_prompt = _paired_delta(steer, prompt, seed=seed, bootstrap_b=bootstrap_b)
        steer_minus_baseline = _paired_delta(steer, baseline, seed=seed, bootstrap_b=bootstrap_b)
        baseline_minus_prompt = _paired_delta(baseline, prompt, seed=seed, bootstrap_b=bootstrap_b)
        steer_deg = _degeneracy_mean(qwen_rows, "test", "steer")
        baseline_deg = _degeneracy_mean(qwen_rows, "test", "baseline")
        pass_without_coherence = bool(adj.axis_pass(
            steer_minus_prompt["point"], steer_minus_prompt["ci_lo"], steer_minus_prompt["ci_hi"], True,
            delta=adj.DELTA,
        ))
        if steer_deg is None or baseline_deg is None:
            coherence_ok = None
            pass_rule = "not evaluated: E-0013 samples do not carry degeneracy"
        else:
            coherence_ok = bool(steer_deg <= adj.COHERENCE_MAX_RATIO * baseline_deg + adj.COHERENCE_EPS_FLOOR + 1e-12)
            pass_rule = bool(adj.axis_pass(
                steer_minus_prompt["point"], steer_minus_prompt["ci_lo"], steer_minus_prompt["ci_hi"], coherence_ok,
                delta=adj.DELTA,
            ))
        pc0 = {
            "status": "computed_from_E-0013_samples_inheriting_frozen_prompt_and_alpha",
            "full_dev_selection_available": False,
            "reason_full_dev_selection_unavailable": (
                "committed artifacts in this worktree do not include results/arm_full transcripts or all "
                "DEV prompt/alpha cells; only E-0013 selected prompt/steer/baseline samples are present"
            ),
            "endpoint": "format_compliance = parse_confidence is not None",
            "condition_rates": {
                "prompt": float(np.mean(list(prompt.values()))),
                "steer": float(np.mean(list(steer.values()))),
                "baseline": float(np.mean(list(baseline.values()))),
            },
            "steer_minus_prompt": steer_minus_prompt,
            "steer_minus_baseline": steer_minus_baseline,
            "baseline_minus_prompt": baseline_minus_prompt,
            "coherence_ok": coherence_ok,
            "pass_rule_result": pass_rule,
            "pass_rule_without_coherence_gate": pass_without_coherence,
            "delta": adj.DELTA,
        }
    params = adj.frozen_params_dict()
    params["n_items_by_axis"] = dict(params.get("n_items_by_axis", {}))
    params["n_items_by_axis"]["refusal_positive_control"] = 60
    return {
        "experiment_id": "E-0014-PC0-PC1-reanalysis",
        "valid_for_paper": False,
        "generated_at": utcnow(),
        "code_commit": git_commit(),
        "scope_guard_sentence": SCOPE_GUARD_SENTENCE,
        "artifact_availability": {
            "samples_path": str(samples_path),
            "observed_cells_in_samples": cells,
            "arm_full_transcripts_present": (_REPO / "results" / "arm_full" / "cell_caa__qwen2.5-7b" / "transcripts").exists(),
            "e0013_samples_present": samples_path.exists(),
        },
        "frozen_adjudicator_reuse": params,
        "pc0_decision_rule_endpoint_sensitivity": pc0,
        "pc1_latent_path_liveness": {
            "status": "unavailable_in_committed_artifacts",
            "reason": "No committed CAA×Llama per-sample format-compliance transcripts/samples are present in this worktree.",
            "no_fabrication": True,
        },
    }


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Reanalyse committed transcripts for E-0014 PC-0/PC-1")
    ap.add_argument("--samples", default=str(DEFAULT_SAMPLES))
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    ap.add_argument("--bootstrap-b", type=int, default=adj.BOOTSTRAP_B)
    ap.add_argument("--allow-underpowered", action="store_true")
    ap.add_argument("--seed", type=int, default=20260723)
    return ap


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.bootstrap_b < adj.BOOTSTRAP_B and not args.allow_underpowered:
        raise SystemExit("--bootstrap-b below frozen 10000 requires --allow-underpowered")
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = reanalyse(Path(args.samples), bootstrap_b=args.bootstrap_b, seed=args.seed)
    out = out_dir / "pc0_pc1_reanalysis.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({
        "out": str(out),
        "pc0_status": payload["pc0_decision_rule_endpoint_sensitivity"]["status"],
        "pc0_pass": payload["pc0_decision_rule_endpoint_sensitivity"].get("pass_rule_result"),
        "pc1_status": payload["pc1_latent_path_liveness"]["status"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
