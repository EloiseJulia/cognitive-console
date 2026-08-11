"""Offline loader for the C2b adjudication task sets (prereg §1) + deferred real loaders.

Mirrors ``eval.loaders`` (manifest + fixture, no network in tests) but for the
three FROZEN behavioral-outcome axes of the C2b adjudication:

* ``deliberation`` — GSM8K-style arithmetic accuracy.
* ``skepticism`` — false-premise rejection (multiple-choice keyed).
* ``uncertainty_awareness`` — calibration, per-item ``1 - Brier`` (decision D-0025).

``load_c2b_task(axis)`` returns the hand-authored fixture so the WHOLE
adjudication pipeline runs offline in tests. The REAL loaders (``load_gsm8k_test``
= GSM8K/MIT, ``load_skepticism_set`` = TruthfulQA/Apache-2.0, ``load_uncertainty_set``
= TriviaQA/Apache-2.0) import ``datasets`` lazily and are the A800-only path; they
raise a clear, documented error offline so nothing silently hits the network.

Real HF dataset ids are NAMESPACED (``datasets`` >= 5 rejects legacy bare ids):
``openai/gsm8k`` (main), ``truthfulqa/truthful_qa`` (multiple_choice),
``mandarjoshi/trivia_qa`` (rc.nocontext).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

AXES = ["deliberation", "skepticism", "uncertainty_awareness"]

# Fixture stem per axis (uncertainty_awareness fixture file is 'uncertainty.jsonl').
_FIXTURE_STEM = {
    "deliberation": "deliberation",
    "skepticism": "skepticism",
    "uncertainty_awareness": "uncertainty",
    "refusal_positive_control": "refusal_positive_control",
}


def default_data_root() -> Path:
    env = os.environ.get("COGNITIVE_CONSOLE_DATA_ROOT")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[3] / "data"


def _tasks_root(data_root: Optional[Path] = None) -> Path:
    root = Path(data_root) if data_root else default_data_root()
    return root / "c2b_tasks"


@dataclass
class C2bTask:
    """A loaded C2b task set: manifest + outcome items."""
    axis: str
    manifest: Dict[str, Any]
    items: List[Dict[str, Any]]
    source: str  # "fixture" | "download"

    @property
    def outcome(self) -> str:
        return self.manifest.get("outcome", "")

    @property
    def n_items_frozen(self) -> int:
        return int(self.manifest.get("n_items_frozen", len(self.items)))

    def __len__(self) -> int:
        return len(self.items)

    def __repr__(self) -> str:
        return f"C2bTask(axis={self.axis!r}, n={len(self.items)}, source={self.source!r})"


def manifest_path(axis: str, data_root: Optional[Path] = None) -> Path:
    return _tasks_root(data_root) / "manifests" / f"{axis}.yaml"


def fixture_path(axis: str, data_root: Optional[Path] = None) -> Path:
    stem = _FIXTURE_STEM.get(axis, axis)
    return _tasks_root(data_root) / "fixtures" / f"{stem}.jsonl"


def load_manifest(axis: str, data_root: Optional[Path] = None) -> Dict[str, Any]:
    path = manifest_path(axis, data_root)
    if not path.exists():
        raise FileNotFoundError(f"c2b task manifest not found: {path}")
    with open(path, "r", encoding="utf-8") as fh:
        manifest = yaml.safe_load(fh)
    if not isinstance(manifest, dict):
        raise ValueError(f"manifest {path} is not a mapping")
    for required in ("name", "axis", "outcome", "scorer", "fixture", "n_items_frozen"):
        if required not in manifest:
            raise ValueError(f"c2b manifest {axis!r} missing required field: {required}")
    if manifest.get("axis") != axis:
        raise ValueError(f"manifest 'axis' ({manifest.get('axis')!r}) != {axis!r}")
    return manifest


def load_fixture(axis: str, data_root: Optional[Path] = None) -> List[Dict[str, Any]]:
    path = fixture_path(axis, data_root)
    if not path.exists():
        raise FileNotFoundError(f"c2b fixture not found: {path}")
    items: List[Dict[str, Any]] = []
    seen: set = set()
    with open(path, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if "id" not in row or not str(row["id"]).strip():
                raise ValueError(f"{path}:{lineno} fixture row missing non-empty 'id'")
            if "prompt" not in row:
                raise ValueError(f"{path}:{lineno} fixture row missing 'prompt'")
            if row["id"] in seen:
                raise ValueError(f"{path}:{lineno} duplicate id {row['id']!r}")
            seen.add(row["id"])
            items.append(row)
    return items


def load_c2b_task(axis: str, use_fixture: bool = True,
                  data_root: Optional[Path] = None) -> C2bTask:
    """Load a C2b task set. ``use_fixture=True`` (default, offline) returns the
    hand-authored fixture; ``use_fixture=False`` routes to the deferred real
    loader (A800 only) and raises offline."""
    manifest = load_manifest(axis, data_root)
    if not use_fixture:
        return _load_real(axis, manifest)
    items = load_fixture(axis, data_root)
    return C2bTask(axis=axis, manifest=manifest, items=items, source="fixture")


def available_c2b_tasks(data_root: Optional[Path] = None) -> List[str]:
    mdir = _tasks_root(data_root) / "manifests"
    if not mdir.exists():
        return []
    # Public C2b task inventory remains the three frozen metacognitive axes;
    # E-0014 loads its positive-control axis explicitly by name.
    return sorted(p.stem for p in mdir.glob("*.yaml") if p.stem in set(AXES))


# --------------------------------------------------------------------------- #
# Real (A800-only) loaders — datasets imported LAZILY; offline they raise.
# --------------------------------------------------------------------------- #
def _load_real(axis: str, manifest: Dict[str, Any]) -> C2bTask:
    if axis == "deliberation":
        items = load_gsm8k_test()
    elif axis == "skepticism":
        items = load_skepticism_set()
    elif axis == "uncertainty_awareness":
        items = load_uncertainty_set()
    elif axis == "refusal_positive_control":
        items = load_refusal_harmless_set()
    else:
        raise ValueError(f"unknown c2b axis {axis!r}")
    return C2bTask(axis=axis, manifest=manifest, items=items, source="download")


def _require_datasets():
    try:
        import datasets  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover - offline path
        raise NotImplementedError(
            "the real C2b task loader needs the 'datasets' package + network "
            "(A800 phase only). Offline tests must use use_fixture=True. "
            "Install: pip install datasets"
        ) from exc
    return datasets


def load_gsm8k_test(
    n: Optional[int] = None,
    seed: int = 0,
    revision: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Load the real GSM8K test split as deliberation items (A800 only).

    Each item = {id, prompt, answer} where answer is the gold number parsed from
    the '#### N' delimiter. Offline this raises (datasets/network deferred)."""
    datasets = _require_datasets()
    ds = datasets.load_dataset(
        "openai/gsm8k",
        "main",
        split="test",
        revision=revision,
    )
    items: List[Dict[str, Any]] = []
    for i, row in enumerate(ds):
        gold = str(row["answer"]).split("####")[-1].strip().replace(",", "")
        items.append({"id": f"gsm8k-test-{i:05d}", "prompt": row["question"], "answer": gold})
    if n is not None:
        import numpy as np  # noqa: PLC0415
        rng = np.random.default_rng(seed)
        idx = sorted(rng.permutation(len(items))[:n].tolist())
        items = [items[j] for j in idx]
    return items


def _subsample(items: List[Dict[str, Any]], n: Optional[int], seed: int) -> List[Dict[str, Any]]:
    if n is None:
        return items
    import numpy as np  # noqa: PLC0415
    rng = np.random.default_rng(seed)
    idx = sorted(rng.permutation(len(items))[:n].tolist())
    return [items[j] for j in idx]


def parse_skepticism_rows(rows: Any, seed: int = 0) -> List[Dict[str, Any]]:
    """Build keyed-MC skepticism items from REAL TruthfulQA multiple_choice rows.

    Pure (no network/datasets): ``rows`` is any iterable of dicts with the real
    columns ``question`` + ``mc1_targets`` where ``mc1_targets = {choices: list[str],
    labels: list[int]}`` (exactly one label == 1 = correct / misconception-rejecting
    option, the label == 0 choices are the false-premise/misconception options).
    Choice order is deterministically shuffled (seeded) so the keyed option is not
    always first (TruthfulQA lists the correct answer first)."""
    import numpy as np  # noqa: PLC0415
    items: List[Dict[str, Any]] = []
    for i, row in enumerate(rows):
        mc1 = row["mc1_targets"]
        texts = list(mc1["choices"])
        labels = list(mc1["labels"])
        if not texts or 1 not in labels:
            continue
        correct_idx = labels.index(1)
        rng = np.random.default_rng(seed + i)
        order = rng.permutation(len(texts)).tolist()
        letters = [chr(ord("A") + j) for j in range(len(texts))]
        choices = {letters[pos]: texts[src] for pos, src in enumerate(order)}
        answer_letter = letters[order.index(correct_idx)]
        items.append({
            "id": f"truthfulqa-mc1-{i:05d}",
            "prompt": row["question"],
            "choices": choices,
            "answer_letter": answer_letter,
            "correct_answer": texts[correct_idx],
        })
    return items


def parse_uncertainty_rows(rows: Any) -> List[Dict[str, Any]]:
    """Build calibration items from REAL TriviaQA rc.nocontext rows.

    Pure (no network/datasets): ``rows`` is any iterable of dicts with the real
    columns ``question`` + ``answer`` where ``answer = {value: str, aliases: list[str],
    normalized_aliases: list[str]}``. Gold = ``answer['value']``; the union of
    aliases + normalized_aliases is kept (de-duped, case-insensitive) so downstream
    matching is alias-insensitive."""
    items: List[Dict[str, Any]] = []
    for i, row in enumerate(rows):
        ans = row.get("answer", {}) or {}
        gold = str(ans.get("value", "")).strip()
        if not gold:
            continue
        alias_src = list(ans.get("aliases", []) or []) + list(ans.get("normalized_aliases", []) or [])
        seen_alias: set = set()
        aliases: List[str] = []
        for a in alias_src:
            a = str(a).strip()
            if a and a.lower() not in seen_alias:
                seen_alias.add(a.lower())
                aliases.append(a)
        items.append({
            "id": f"triviaqa-{i:05d}",
            "prompt": row["question"],
            "answer": gold,
            "aliases": aliases,
        })
    return items


def load_skepticism_set(n: Optional[int] = None, seed: int = 0) -> List[Dict[str, Any]]:
    """Load the real false-premise skepticism set from TruthfulQA (A800 only).

    Dataset: ``truthfulqa/truthful_qa`` config ``multiple_choice`` (Apache-2.0). TruthfulQA
    questions are built around common misconceptions / false beliefs; the MC1
    target block marks exactly ONE correct answer (``labels`` has a single 1),
    which is the option that REJECTS the false/common-misconception premise. We
    frame each row as a keyed multiple-choice item so scoring is DETERMINISTIC
    (``score_skepticism`` on ``choices`` + ``answer_letter``).

    Choice order is deterministically SHUFFLED (seeded) so the keyed option is not
    always in the same position (TruthfulQA lists the correct answer first).
    Offline this raises (datasets/network deferred)."""
    datasets = _require_datasets()
    ds = datasets.load_dataset("truthfulqa/truthful_qa", "multiple_choice", split="validation")
    items = parse_skepticism_rows(ds, seed=seed)
    return _subsample(items, n, seed)


def load_uncertainty_set(n: Optional[int] = None, seed: int = 0) -> List[Dict[str, Any]]:
    """Load the real calibration/uncertainty factual-QA set from TriviaQA (A800).

    Dataset: ``mandarjoshi/trivia_qa`` config ``rc.nocontext`` (Apache-2.0) — factual
    short-answer trivia questions with a gold answer (and aliases), NO context
    passage, so the model must answer from parametric knowledge and gets a
    non-trivial fraction wrong (calibration needs both correct and incorrect
    answers to have signal). Each item = {id, prompt, answer, aliases} where
    ``answer`` is the gold value; ``item_is_correct`` matches the gold string /
    aliases (case/alias/punctuation-insensitive), and the per-item outcome is the
    PROPER ``1 - Brier`` over the elicited answer + verbalized confidence (decision
    D-0025). Offline this raises."""
    datasets = _require_datasets()
    ds = datasets.load_dataset("mandarjoshi/trivia_qa", "rc.nocontext", split="validation")
    items = parse_uncertainty_rows(ds)
    return _subsample(items, n, seed)


def load_refusal_harmless_set(n: Optional[int] = None, seed: int = 20260804) -> List[Dict[str, Any]]:
    """Load harmless factual questions for E-0014 refusal induction (A800 only).

    Source is the existing TriviaQA validation loader. We exclude the first 80
    ``triviaqa-00000``..``triviaqa-00079`` ids used by the frozen uncertainty
    pool, then take a deterministic shuffled slice so PC-2/PC-3 are id-disjoint
    from C2/E-0013. No answers are needed by the refusal scorer, but retaining
    them preserves provenance and auditability.
    """
    items = load_uncertainty_set(n=None, seed=0)
    filtered = [it for it in items if not str(it.get("id", "")).startswith("triviaqa-")
                or int(str(it["id"]).split("-")[-1]) >= 80]
    return _subsample(filtered, n, seed) if n is not None else _subsample(filtered, 60, seed)
