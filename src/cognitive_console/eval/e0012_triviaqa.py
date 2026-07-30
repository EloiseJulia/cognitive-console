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
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# Pre-registered sampling parameters — FROZEN at prereg freeze
E0012_POOL_N: int = 80
E0012_POOL_SEED: int = 12          # differs from E-0006 (seed=0)
E0012_POOL_OFFSET: int = 500       # skip first 500 val items
E0012_SPLIT_SEED: int = 42         # DEV/TEST split seed
E0012_POOL_ID: str = "e0012-triviaqa-v1"


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
