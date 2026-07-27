"""Run the L0 DEV-power probe for the frozen novice-disclosure flagship study.

This runner does not execute steering or an experiment by default. ``--mock``
uses deterministic CPU fixtures to exercise generation -> condition-blind
redaction -> M1/M4 scoring -> coverage guard -> DEV-power/MDE output. ``--backend
hf`` is the one-command path for the later approved GPU L0 probe.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path
from typing import List, Optional

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cognitive_console.config import config_hash
from cognitive_console.lineage import git_commit, utcnow
from cognitive_console.registry import ExperimentRecord, ExperimentRegistry
from cognitive_console.social.backends import FixtureFlagshipBackend, HFTextBackend
from cognitive_console.social.conditions import CONDITIONS, render_prompt
from cognitive_console.social.coverage import assert_complete_coverage, config_fingerprint
from cognitive_console.social.power import estimate_mde
from cognitive_console.social.scoring import FixtureJudge, HeuristicBlindJudge
from cognitive_console.social.tasks import load_flagship_l0_tasks

DEFAULT_MODEL = "Qwen/Qwen2.5-7B-Instruct"


def _rel(path: Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(_REPO)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _backend(args):
    if args.mock or args.backend == "mock":
        return FixtureFlagshipBackend(seed=args.seed), "mock-fixture"
    if args.backend != "hf":
        raise ValueError(f"unsupported backend {args.backend!r}")
    return HFTextBackend(args.model, seed=args.seed), "hf"


def _judge(args):
    if args.mock or args.judge == "fixture":
        return FixtureJudge()
    return HeuristicBlindJudge()


def _summaries(records: List[dict]) -> dict:
    out = {}
    for dim_key, score_key in (
        ("M1", "m1_recommendation_strength"),
        ("M4", "m4_deference_exploitation"),
    ):
        by_cond = {}
        for cond in [c.id for c in CONDITIONS]:
            vals = [
                float(r["scores"][score_key])
                for r in records
                if r["condition_id"] == cond
            ]
            by_cond[cond] = sum(vals) / len(vals) if vals else None
        out[dim_key] = by_cond
    return out


def run(args) -> dict:
    started = utcnow()
    tasks = load_flagship_l0_tasks()[: int(args.max_items)]
    item_ids = [str(t["id"]) for t in tasks]
    backend, backend_name = _backend(args)
    judge = _judge(args)
    cfg = {
        "kind": "flagship_novice_disclosure_l0",
        "protocol_decision": "D-0044",
        "steering_method": "n/a",
        "backend": backend_name,
        "model": args.model,
        "conditions": [c.id for c in CONDITIONS],
        "item_ids": item_ids,
        "seed": int(args.seed),
        "k": int(args.k),
        "judge": judge.name,
        "max_new_tokens": int(args.max_new_tokens),
        "prompt_template": "flagship_l0_v0",
    }
    fp = config_fingerprint(cfg)
    records: List[dict] = []
    for item in tasks:
        for condition in CONDITIONS:
            prompt = render_prompt(item, condition)
            for sample_index in range(int(args.k)):
                response = backend.generate(
                    prompt,
                    condition_id=condition.id,
                    item=item,
                    sample_index=sample_index,
                    max_new_tokens=args.max_new_tokens,
                )
                scores = judge.score(item, condition.id, response)
                records.append(
                    {
                        "item_id": item["id"],
                        "condition_id": condition.id,
                        "condition_label": condition.label,
                        "sample_index": sample_index,
                        "prompt": prompt if args.include_prompts else None,
                        "response": response,
                        "scores": scores.to_dict(),
                    }
                )

    assert_complete_coverage(records, item_ids, [c.id for c in CONDITIONS], int(args.k))
    power_rows = [
        {
            "item_id": r["item_id"],
            "condition_id": r["condition_id"],
            "sample_index": r["sample_index"],
            "m1": r["scores"]["m1_recommendation_strength"],
            "m4": r["scores"]["m4_deference_exploitation"],
        }
        for r in records
    ]
    mde = [x.to_dict() for x in estimate_mde(power_rows)]
    payload = {
        "schema": "flagship_l0_result_v0",
        "status": "done",
        "valid_for_paper": False,
        "started_at": started,
        "ended_at": utcnow(),
        "config": cfg,
        "config_fingerprint": fp,
        "git_commit": git_commit(str(_REPO)),
        "hardware": platform.platform(),
        "coverage": {
            "complete": True,
            "n_items": len(item_ids),
            "conditions": [c.id for c in CONDITIONS],
            "k": int(args.k),
            "n_records": len(records),
        },
        "condition_means": _summaries(records),
        "mde": mde,
        "records": records,
    }
    return payload


def write_outputs(payload: dict, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    result_path = out_dir / "flagship_l0_results.json"
    result_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    registry = ExperimentRegistry(str(out_dir / "experiment-registry.yaml"))
    exp_id = f"flagship-l0-{payload['config_fingerprint']}-0001"
    existing = registry.get(exp_id)
    if existing is None:
        registry.append(
            ExperimentRecord(
                experiment_id=exp_id,
                hypothesis_id="H-NM",
                claim_ids=[],
                type="diagnostic",
                status="done",
                code_commit=payload.get("git_commit"),
                config_hash=config_hash(payload["config"]),
                model=payload["config"]["model"],
                dataset="src/cognitive_console/social/data/flagship_l0_tasks.json",
                seed=payload["config"]["seed"],
                hardware=payload["hardware"],
                started_at=payload["started_at"],
                ended_at=payload["ended_at"],
                exit_code=0,
                summary_metrics={
                    "condition_means": payload["condition_means"],
                    "mde": payload["mde"],
                    "coverage": payload["coverage"],
                },
                artifacts=[_rel(result_path)],
                valid_for_paper=False,
                validation_notes=(
                    "L0 DEV-power harness smoke/probe only; no TEST claim and no "
                    "human-validation gate. Frozen protocol D-0044 conditions and "
                    "M1/M4 F6/F7 guardrails are implemented for pipeline validation."
                ),
            )
        )
    payload["experiment_id"] = exp_id
    result_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return result_path


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Flagship novice-disclosure L0 DEV-power harness")
    ap.add_argument("--backend", choices=["hf", "mock"], default="hf")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--mock", action="store_true", help="Use deterministic CPU backend + fixture judge")
    ap.add_argument("--judge", choices=["heuristic", "fixture"], default="heuristic")
    ap.add_argument("--seed", type=int, default=20260727)
    ap.add_argument("--k", type=int, default=2, help="samples per item-condition for L0")
    ap.add_argument("--max-items", type=int, default=14)
    ap.add_argument("--max-new-tokens", type=int, default=256)
    ap.add_argument("--out-dir", default="runs/flagship_l0")
    ap.add_argument("--include-prompts", action="store_true")
    return ap


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    payload = run(args)
    path = write_outputs(payload, Path(args.out_dir))
    print(json.dumps({
        "result": str(path),
        "fingerprint": payload["config_fingerprint"],
        "coverage": payload["coverage"],
        "condition_means": payload["condition_means"],
    }, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
