
"""Run the persona breadth/scope-locking L0 harness.

CPU smoke:
    python -m scripts.run_breadth_l0 --mock --k 5

Deferred GPU L0 (do not run without Manager/human compute approval):
    python -m scripts.run_breadth_l0 --backend hf --classifier rule --judge-cross-check --model Qwen/Qwen2.5-7B-Instruct --device cuda --dtype float16 --k 5
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))

from cognitive_console.activations.provider import HFActivationProvider
from cognitive_console.experiments.breadth_l0 import (
    LLMJudgeDomainClassifier,
    RuleBasedDomainClassifier,
    aggregate_metrics,
    classifier_agreement,
    coverage_guard,
    extract_breadth_axis,
    load_contrast_pairs,
    load_readability_prompts,
    load_tasks,
    oracle_suppression,
    result_fingerprint,
    run_mock_l0,
    sample_conditions,
)
from cognitive_console.steering.generate import SteeredHFBackend

DATA_DIR = _REPO / "data" / "persona_breadth_l0"
DEFAULT_OUT = _REPO / "outputs" / "breadth_l0"
DEFAULT_MODEL = "Qwen/Qwen2.5-7B-Instruct"


def _jsonable(obj):
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if hasattr(obj, "__dataclass_fields__"):
        return asdict(obj)
    raise TypeError(type(obj).__name__)


def parse_layers(raw: str | None):
    if not raw:
        return None
    return [int(x.strip()) for x in raw.split(",") if x.strip()]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--backend", choices=["mock", "hf"], default="mock")
    ap.add_argument("--mock", action="store_true", help="Alias for --backend mock")
    ap.add_argument(
        "--classifier", choices=["rule"], default="rule",
        help="Primary domain classifier. Only deterministic marker ground truth is allowed for suppression.",
    )
    ap.add_argument(
        "--judge-cross-check", action="store_true",
        help="Run a frozen condition-blinded local LLM judge as a secondary agreement/bias cross-check. Does not define suppression.",
    )
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--dtype", default="float16")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--seed", type=int, default=20260727)
    ap.add_argument("--max-new-tokens", type=int, default=180)
    ap.add_argument("--layers", default=None, help="Comma-separated hidden-state layers for extraction")
    ap.add_argument("--tasks", type=Path, default=DATA_DIR / "tasks.json")
    ap.add_argument("--contrast-pairs", type=Path, default=DATA_DIR / "breadth_focus_contrast_pairs.jsonl")
    ap.add_argument("--readability-prompts", type=Path, default=DATA_DIR / "readability_prompts.json")
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args(argv)
    if args.mock:
        args.backend = "mock"

    args.output_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.output_dir / f"breadth_l0_{args.backend}_k{args.k}_seed{args.seed}.json"

    if args.backend == "mock":
        result = run_mock_l0(args.tasks, args.contrast_pairs, args.readability_prompts, k=args.k, seed=args.seed, model="mock-deterministic")
        out_path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
        print(f"[breadth-l0] wrote {out_path}")
        print(json.dumps({
            "backend": result.backend,
            "k": result.k,
            "fingerprint": result.fingerprint,
            "strict_suppression_rate": result.suppression.strict_suppression_rate,
            "calibrated_suppression_rate": result.suppression.calibrated_suppression_rate,
            "breadth_axis_verdict": result.breadth_axis.verdict,
            "coverage_guard_passed": result.coverage_guard_passed,
        }, indent=2))
        return 0

    tasks = load_tasks(args.tasks)
    broad, focus = load_contrast_pairs(args.contrast_pairs)
    readability = load_readability_prompts(args.readability_prompts)
    layers = parse_layers(args.layers)
    act_provider = HFActivationProvider(
        args.model, layers=layers, device=args.device, dtype=args.dtype,
        cache_dir=args.output_dir / "activation_cache", max_length=512,
    )
    axis = extract_breadth_axis(
        act_provider, broad, focus, readability,
        layers=layers, seed=args.seed, n_null=500,
    )
    gen_backend = SteeredHFBackend(
        args.model, device=args.device, dtype=args.dtype, max_length=1024, seed=args.seed,
    )
    classifier = RuleBasedDomainClassifier(extra_markers={"general_reasoning": ["general_reasoning", "general reasoning", "baseline reasoning"]})
    rows = sample_conditions(gen_backend, classifier, tasks, args.k, max_new_tokens=args.max_new_tokens)
    guard = coverage_guard(rows, tasks, args.k)
    if not guard["ok"]:
        fail_path = args.output_dir / f"breadth_l0_{args.backend}_FAILED_COVERAGE.json"
        fail_path.write_text(json.dumps({"coverage_guard": guard, "axis": asdict(axis)}, indent=2), encoding="utf-8")
        raise RuntimeError(f"coverage guard failed; wrote {fail_path}")
    suppression = oracle_suppression(rows, seed=args.seed, bootstrap_b=2000)
    secondary = LLMJudgeDomainClassifier(backend=gen_backend) if args.judge_cross_check else None
    agreement = classifier_agreement(
        rows, tasks, secondary,
        primary_classifier_name="deterministic_marker_v2",
        secondary_classifier_name="frozen_blinded_llm_judge" if secondary is not None else "none",
    )
    fp = result_fingerprint(args.tasks, args.contrast_pairs, args.readability_prompts, backend="hf", model=args.model, k=args.k, seed=args.seed)
    payload = {
        "schema": "persona_breadth_l0_result_v1",
        "backend": "hf",
        "model": args.model,
        "k": args.k,
        "fingerprint": fp,
        "classifier": "deterministic_marker_v2",
        "secondary_classifier_agreement": asdict(agreement),
        "suppression_verdict_classifier": "deterministic_marker_v2",
        "coverage_guard_passed": True,
        "coverage_guard": guard,
        "metrics": aggregate_metrics(rows),
        "suppression": asdict(suppression),
        "breadth_axis": asdict(axis),
        "items": [asdict(r) for r in rows],
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[breadth-l0] wrote {out_path}")
    print(json.dumps({
        "backend": "hf", "model": args.model, "k": args.k,
        "fingerprint": fp,
        "strict_suppression_rate": suppression.strict_suppression_rate,
        "calibrated_suppression_rate": suppression.calibrated_suppression_rate,
        "breadth_axis_verdict": axis.verdict,
        "coverage_guard_passed": True,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
