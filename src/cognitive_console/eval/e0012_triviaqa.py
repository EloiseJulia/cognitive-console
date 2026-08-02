"""E-0012 TriviaQA validation-split loader — Option A calibration subset.

Pre-registered parameters (must NOT be changed after prereg freeze):
  source  : TriviaQA validation split (mandarjoshi/trivia_qa, rc.nocontext)
  N       : 80 calibration items
  seed    : 12   ← different from E-0006 (seed=0)
  offset  : 500  ← skip first 500 items so there is zero overlap with E-0006 pool
  split_seed : 42  ← DEV/TEST split seed for this pool

The offset + seed combination guarantees the E-0012 pool is disjoint from any
E-0006 items that were sampled at seed=0 from the same validation split.

Offline (no GPU / no network) the module provides ``load_e0012_triviaqa_fixture``
which returns the bundled JSONL fixture at data/e0012_pool/triviaqa_e0012.jsonl.
Real loading (A800 only) routes through ``load_e0012_triviaqa_real`` which calls
the HuggingFace ``datasets`` API.
"""

from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# Pre-registered sampling parameters — FROZEN at prereg freeze
E0012_POOL_N: int = 80
E0012_POOL_SEED: int = 12          # differs from E-0006 (seed=0)
E0012_POOL_OFFSET: int = 500       # skip first 500 val items
E0012_SPLIT_SEED: int = 42         # DEV/TEST split seed
E0012_POOL_ID: str = "e0012-triviaqa-v1"
E0006_BASELINE_ITEM_COUNT: int = 80
E0006_BASELINE_SCHEMA_VERSION: str = "e0006-uncertainty-baseline-v1"


def default_data_root() -> Path:
    env = os.environ.get("COGNITIVE_CONSOLE_DATA_ROOT")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[3] / "data"


def fixture_path(data_root: Optional[Path] = None) -> Path:
    root = Path(data_root) if data_root else default_data_root()
    return root / "e0012_pool" / "triviaqa_e0012.jsonl"


def load_e0012_triviaqa_fixture(data_root: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Load the bundled offline fixture for E-0012 (offline/test path).

    Returns N=80 calibration items: {id, prompt, answer, aliases}.
    Raises FileNotFoundError if the fixture has not been generated yet.
    """
    path = fixture_path(data_root)
    if not path.exists():
        raise FileNotFoundError(
            f"E-0012 fixture not found: {path}\n"
            "Generate it with: python scripts/run_e0012_verified_control.py --generate-fixture"
        )
    items: List[Dict[str, Any]] = []
    seen: set = set()
    with open(path, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row["id"] in seen:
                raise ValueError(f"duplicate id at line {lineno}: {row['id']!r}")
            seen.add(row["id"])
            items.append(row)
    if len(items) != E0012_POOL_N:
        raise ValueError(f"fixture has {len(items)} items; expected {E0012_POOL_N}")
    return items


def load_e0012_triviaqa_real(data_root: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Load the REAL E-0012 TriviaQA pool from HuggingFace (A800 only).

    Downloads the validation split of mandarjoshi/trivia_qa (rc.nocontext),
    skips the first E0012_POOL_OFFSET items, then takes a seeded random sample
    of E0012_POOL_N items from the remainder.  The seed/offset guarantee
    disjointness from the E-0006 pool (seed=0, no offset).
    """
    try:
        import datasets  # noqa: PLC0415
    except ImportError as exc:
        raise NotImplementedError(
            "load_e0012_triviaqa_real needs the 'datasets' package + network (A800). "
            "Offline tests must use load_e0012_triviaqa_fixture(). "
            "Install: pip install datasets"
        ) from exc
    import numpy as np  # noqa: PLC0415

    from cognitive_console.eval.c2b_tasks import parse_uncertainty_rows

    ds = datasets.load_dataset("mandarjoshi/trivia_qa", "rc.nocontext", split="validation")
    # Skip first offset items to guarantee non-overlap with E-0006 pool
    remaining = list(ds)[E0012_POOL_OFFSET:]
    all_items = parse_uncertainty_rows(remaining)
    # Re-index ids to be unique to this pool
    all_items = [
        {**it, "id": f"e0012-triviaqa-{i:05d}"}
        for i, it in enumerate(all_items)
    ]
    if len(all_items) < E0012_POOL_N:
        raise ValueError(
            f"Only {len(all_items)} items available after offset={E0012_POOL_OFFSET}; "
            f"need {E0012_POOL_N}."
        )
    rng = np.random.default_rng(E0012_POOL_SEED)
    idx = sorted(rng.permutation(len(all_items))[:E0012_POOL_N].tolist())
    items = [all_items[i] for i in idx]
    return items


def load_triviaqa_train_for_probe(
    n: int = 200,
    seed: int = 42,
) -> List[Dict[str, Any]]:
    """Load deterministic TriviaQA-train items for BTN-CAL-PROBE derivation."""
    try:
        import datasets  # noqa: PLC0415
    except ImportError as exc:
        raise NotImplementedError(
            "load_triviaqa_train_for_probe needs the 'datasets' package + network (A800)."
        ) from exc
    import numpy as np  # noqa: PLC0415

    from cognitive_console.eval.c2b_tasks import parse_uncertainty_rows

    ds = datasets.load_dataset("mandarjoshi/trivia_qa", "rc.nocontext", split="train")
    items = parse_uncertainty_rows(ds)
    items = [{**it, "id": f"triviaqa-train-{i:05d}"} for i, it in enumerate(items)]
    if len(items) < n:
        raise ValueError(f"TriviaQA-train has {len(items)} parsed items; need {n}")
    rng = np.random.default_rng(seed)
    idx = sorted(rng.permutation(len(items))[:n].tolist())
    return [items[i] for i in idx]


def _canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def canonical_e0006_baseline_hash(payload: Dict[str, Any]) -> str:
    """Hash canonical E-0006 baseline artifact content, excluding self hash."""
    copy = json.loads(json.dumps(payload))
    copy.pop("artifact_sha256", None)
    return hashlib.sha256(_canonical_json_bytes(copy)).hexdigest()


def make_e0006_baseline_artifact(
    *,
    source_experiment_id: str,
    source_run_commit: str,
    items: List[Dict[str, Any]],
    source_split: str = "E-0006 uncertainty_awareness all-80",
    condition: str = "unsteered",
    k: int = 5,
    synthetic_proxy: bool = False,
) -> Dict[str, Any]:
    """Create the canonical all-80 E-0006 baseline-score artifact."""
    artifact = {
        "schema_version": E0006_BASELINE_SCHEMA_VERSION,
        "lineage": {
            "source_experiment_id": source_experiment_id,
            "source_run_commit": source_run_commit,
            "source_axis": "uncertainty_awareness",
            "source_split": source_split,
            "condition": condition,
            "k": int(k),
            "synthetic_proxy": bool(synthetic_proxy),
            "item_count": len(items),
        },
        "items": items,
    }
    artifact["artifact_sha256"] = canonical_e0006_baseline_hash(artifact)
    return artifact


def validate_e0006_baseline_artifact(payload: Dict[str, Any]) -> str:
    """Validate canonical E-0006 baseline artifact and return its sha256."""
    if payload.get("schema_version") != E0006_BASELINE_SCHEMA_VERSION:
        raise ValueError("E-0006 baseline artifact has wrong or missing schema_version")
    expected_hash = payload.get("artifact_sha256")
    actual_hash = canonical_e0006_baseline_hash(payload)
    if expected_hash != actual_hash:
        raise ValueError(
            f"E-0006 baseline artifact hash mismatch: expected {expected_hash!r}, "
            f"computed {actual_hash!r}"
        )
    lineage = payload.get("lineage")
    if not isinstance(lineage, dict):
        raise ValueError("E-0006 baseline artifact missing lineage object")
    required_lineage = {
        "source_experiment_id",
        "source_run_commit",
        "source_axis",
        "source_split",
        "condition",
        "k",
        "synthetic_proxy",
        "item_count",
    }
    missing = required_lineage - set(lineage)
    if missing:
        raise ValueError(f"E-0006 baseline artifact lineage missing: {sorted(missing)}")
    if lineage["source_axis"] != "uncertainty_awareness":
        raise ValueError("E-0006 baseline artifact must be uncertainty_awareness")
    if lineage["condition"] != "unsteered":
        raise ValueError("E-0006 baseline artifact condition must be unsteered")
    if int(lineage["k"]) != 5:
        raise ValueError("E-0006 baseline artifact must have k=5")
    if bool(lineage["synthetic_proxy"]):
        raise ValueError("E-0006 baseline artifact must be real-model synthetic_proxy=false")
    if int(lineage["item_count"]) != E0006_BASELINE_ITEM_COUNT:
        raise ValueError("E-0006 baseline artifact lineage item_count must be 80")
    items = payload.get("items")
    if not isinstance(items, list) or len(items) != E0006_BASELINE_ITEM_COUNT:
        raise ValueError("E-0006 baseline artifact must contain exactly 80 items")
    seen: set[str] = set()
    for i, row in enumerate(items):
        if not isinstance(row, dict):
            raise ValueError(f"E-0006 baseline item {i} is not an object")
        missing_item = {"id", "prompt", "answer", "baseline_score", "item_index"} - set(row)
        if missing_item:
            raise ValueError(f"E-0006 baseline item {i} missing: {sorted(missing_item)}")
        if int(row["item_index"]) != i:
            raise ValueError(f"E-0006 baseline item_index mismatch at row {i}")
        item_id = str(row["id"])
        if item_id in seen:
            raise ValueError(f"E-0006 baseline duplicate item id: {item_id!r}")
        seen.add(item_id)
        score = float(row["baseline_score"])
        if not (0.0 <= score <= 1.0):
            raise ValueError(f"E-0006 baseline_score out of range for {item_id!r}")
    return actual_hash


def load_e0006_dev_baseline_scores(path: Path) -> List[Dict[str, Any]]:
    """Load canonical all-80 E-0006 baseline-scored calibration artifact.

    Despite the historical function name, this now follows Manager D-0068:
    rank the FULL E-0006 uncertainty_awareness set (80 items), not the DEV split.
    The artifact must carry lineage, condition=unsteered, k=5, synthetic_proxy=false,
    exactly 80 item ids, and a valid canonical artifact hash.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"E-0006 baseline-score artifact not found: {path}. "
            "Build/provide the canonical all-80 real E-0006 unsteered k=5 artifact."
        )
    raw_bytes = path.read_bytes()
    payload = json.loads(raw_bytes.decode("utf-8"))
    artifact_sha = validate_e0006_baseline_artifact(payload)
    file_sha = hashlib.sha256(raw_bytes).hexdigest()
    items = []
    for row in payload["items"]:
        item = dict(row)
        item["baseline_score"] = float(item["baseline_score"])
        item.setdefault("aliases", [])
        item["source_artifact_sha256"] = file_sha
        item["canonical_artifact_sha256"] = artifact_sha
        item["source_experiment_id"] = payload["lineage"]["source_experiment_id"]
        item["source_run_commit"] = payload["lineage"]["source_run_commit"]
        items.append(item)
    return items


def save_fixture(items: List[Dict[str, Any]], data_root: Optional[Path] = None) -> Path:
    """Write items to the fixture file for offline reuse."""
    path = fixture_path(data_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for it in items:
            fh.write(json.dumps(it, ensure_ascii=False) + "\n")
    return path


def load_e0012_pool(
    use_fixture: bool = True,
    data_root: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """Unified loader: fixture offline, real on A800."""
    if use_fixture:
        return load_e0012_triviaqa_fixture(data_root)
    return load_e0012_triviaqa_real(data_root)
