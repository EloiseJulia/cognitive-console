"""Build the canonical E-0006 uncertainty baseline artifact for E-0012 CONTRA.

This is a GPU/HF pre-step, not a fixture generator.  It reconstructs the exact
E-0006 uncertainty_awareness calibration item set via the frozen C2b loader,
runs the model unsteered with an empty prompt at k=5, and writes:

  data/e0006_uncertainty_baseline/e0006_uncertainty_baseline.jsonl
  data/e0006_uncertainty_baseline/e0006_uncertainty_baseline.manifest.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cognitive_console.eval import scorers
from cognitive_console.eval.e0012_triviaqa import (
    E0006_BASELINE_CONDITION,
    E0006_BASELINE_ITEM_COUNT,
    E0006_BASELINE_SCHEMA_VERSION,
    E0006_FROZEN_GENERATION_IDENTITY,
    E0006_FROZEN_MAX_NEW_TOKENS,
    E0006_FROZEN_MODEL,
    E0006_FROZEN_SEED,
    E0006_FROZEN_TEMPERATURE,
)
from cognitive_console.experiments import adjudicate_c2b as adj
from cognitive_console.experiments.e0012_steer_hf import SteeredHFTextCapableSampler
from cognitive_console.steering.generate import SteeredHFBackend
from scripts.run_c2b_adjudication import load_axis_items


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return "UNKNOWN"


def _manifest_path(jsonl_path: Path) -> Path:
    return jsonl_path.with_name(jsonl_path.stem + ".manifest.json")


def load_frozen_e0006_uncertainty_items() -> List[Dict[str, Any]]:
    """Reuse the exact E-0006 C2b uncertainty loader and frozen 80-item cap."""
    items = load_axis_items("uncertainty_awareness", use_fixture=False, n_items=None)
    if len(items) != E0006_BASELINE_ITEM_COUNT:
        raise RuntimeError(
            "Frozen E-0006 uncertainty loader did not return exactly "
            f"{E0006_BASELINE_ITEM_COUNT} items (got {len(items)})"
        )
    ids = [str(it.get("id")) for it in items]
    if len(set(ids)) != len(ids):
        raise RuntimeError("Frozen E-0006 uncertainty loader returned duplicate item ids")
    return items


def build_baseline_rows(
    *,
    model_name: str,
    dtype: str,
    device: str,
    seed: int,
    max_new_tokens: int,
    temperature: float,
) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    items = load_frozen_e0006_uncertainty_items()
    backend = SteeredHFBackend(model_name=model_name, dtype=dtype, device=device, seed=seed)
    sampler = SteeredHFTextCapableSampler(
        backend,
        max_new_tokens=max_new_tokens,
        do_sample=True,
        temperature=temperature,
        seed=seed,
    )
    # alpha=0 is unsteered, but the backend still normalizes the vector; use any
    # non-zero vector with the correct hidden dimension.
    neutral_direction = np.ones(int(backend.hidden_dim), dtype=np.float32)
    neutral_layer = 1
    rows: List[Dict[str, Any]] = []
    for item_index, item in enumerate(items):
        batch, texts = sampler.sample_with_texts(
            "uncertainty_awareness",
            item,
            instruction="",
            alpha=0.0,
            k=adj.K_SAMPLES,
            direction=neutral_direction,
            layer=neutral_layer,
        )
        raw_pairs: List[Dict[str, Any]] = []
        one_minus_briers: List[float] = []
        for sample_index, text in enumerate(texts):
            conf: Optional[float] = scorers.parse_confidence(text)
            correct = int(scorers.item_is_correct(item, text))
            if conf is None:
                conf = float(batch.outcomes[sample_index])
            brier = (float(conf) - float(correct)) ** 2
            one_minus_briers.append(1.0 - brier)
            raw_pairs.append(
                {
                    "sample_index": sample_index,
                    "confidence": float(conf),
                    "correctness": correct,
                    "one_minus_brier": float(1.0 - brier),
                    "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                    "synthetic_proxy": False,
                }
            )
        rows.append(
            {
                "item_index": item_index,
                "id": str(item.get("id")),
                "prompt": str(item.get("prompt", "")),
                "answer": item.get("answer"),
                "aliases": list(item.get("aliases", []) or []),
                "baseline_score": float(np.mean(one_minus_briers)),
                "raw_pairs": raw_pairs,
            }
        )
    lineage = {
        "source_experiment_id": "E-0006-C2b-uncertainty-awareness",
        "source_run_commit": "UNKNOWN_NOT_PERSISTED_IN_SAVED_RESULTS",
        "source_axis": "uncertainty_awareness",
        "source_item_loader": "scripts.run_c2b_adjudication.load_axis_items(axis='uncertainty_awareness', use_fixture=False, n_items=None)",
        "source_split": "full_frozen_80_calibration_items",
        "condition": E0006_BASELINE_CONDITION,
        "k": adj.K_SAMPLES,
        "synthetic_proxy": False,
        "item_count": E0006_BASELINE_ITEM_COUNT,
        "model": model_name,
        "dtype": dtype,
        "device": device,
        "code_commit": _git_commit(),
        "max_new_tokens": int(max_new_tokens),
        "temperature": float(temperature),
        "seed": int(seed),
        "e0006_generation_identity": {
            "model": model_name,
            "max_new_tokens": int(max_new_tokens),
            "temperature": float(temperature),
            "seed": int(seed),
        },
    }
    return rows, lineage


def write_artifact(rows: List[Dict[str, Any]], lineage: Dict[str, Any], jsonl_path: Path) -> None:
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    jsonl_path.write_text(text, encoding="utf-8")
    artifact_sha = hashlib.sha256(jsonl_path.read_bytes()).hexdigest()
    manifest = {
        "schema_version": E0006_BASELINE_SCHEMA_VERSION,
        "lineage": lineage,
        "item_ids": [str(row["id"]) for row in rows],
        "artifact_sha256": artifact_sha,
    }
    _manifest_path(jsonl_path).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", default=E0006_FROZEN_MODEL)
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="cuda")
    p.add_argument("--seed", type=int, default=E0006_FROZEN_SEED)
    p.add_argument("--max-new-tokens", type=int, default=E0006_FROZEN_MAX_NEW_TOKENS)
    p.add_argument("--temperature", type=float, default=E0006_FROZEN_TEMPERATURE)
    p.add_argument(
        "--output",
        type=Path,
        default=Path("data/e0006_uncertainty_baseline/e0006_uncertainty_baseline.jsonl"),
    )
    args = p.parse_args()
    requested_identity = {
        "model": args.model,
        "max_new_tokens": int(args.max_new_tokens),
        "temperature": float(args.temperature),
        "seed": int(args.seed),
    }
    if requested_identity != E0006_FROZEN_GENERATION_IDENTITY:
        raise SystemExit(
            "E-0006 baseline builder is frozen to generation identity "
            f"{E0006_FROZEN_GENERATION_IDENTITY}; got {requested_identity}"
        )
    rows, lineage = build_baseline_rows(
        model_name=args.model,
        dtype=args.dtype,
        device=args.device,
        seed=args.seed,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
    )
    write_artifact(rows, lineage, args.output)
    print(f"wrote {args.output} ({len(rows)} rows)")
    print(f"wrote {_manifest_path(args.output)}")


if __name__ == "__main__":
    main()
