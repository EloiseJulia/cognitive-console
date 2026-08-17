"""Latent behavioral positive-control helpers (Stolfo-style instruction vector).

This module is deliberately model-light: it contains the frozen scoring,
coherence, and bootstrap utilities for the Stage-1 DEV assay. The real HF model
loading and residual-hook generation live in ``scripts/run_latent_positive_control.py``
so the normal CPU test suite remains offline.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

import numpy as np

from . import adjudicate_c2b as adj
from ..eval.scorers import degeneracy_score

ALPHA_GRID: tuple[float, ...] = adj.ALPHA_GRID
DELTA: float = adj.DELTA
BOOTSTRAP_B: int = adj.BOOTSTRAP_B
BONFERRONI_CI_LEVEL: float = adj.BONFERRONI_CI_LEVEL
COHERENCE_MAX_RATIO: float = adj.COHERENCE_MAX_RATIO
COHERENCE_EPS_FLOOR: float = adj.COHERENCE_EPS_FLOOR
K_SAMPLES: int = 5


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def sha256_json(payload: object) -> str:
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(blob).hexdigest()


def load_protocol_items(path: str | Path) -> Dict[str, object]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    for key in ("keyword", "instruction_template", "extraction_prompts", "dev_items", "test_items"):
        if key not in data:
            raise ValueError(f"latent positive-control data missing {key!r}")
    for split in ("extraction_prompts", "dev_items", "test_items"):
        seen: set[str] = set()
        rows = data[split]
        if not isinstance(rows, list) or not rows:
            raise ValueError(f"{split} must be a non-empty list")
        for row in rows:
            if not isinstance(row, dict) or not str(row.get("id", "")).strip():
                raise ValueError(f"{split} row missing non-empty id")
            if row["id"] in seen:
                raise ValueError(f"{split} duplicate id {row['id']!r}")
            if not str(row.get("prompt", "")).strip():
                raise ValueError(f"{split} row {row['id']!r} missing prompt")
            seen.add(str(row["id"]))
    return data


def add_instruction(prompt: str, instruction_template: str, keyword: str) -> str:
    instruction = instruction_template.format(keyword=keyword)
    return str(prompt).rstrip() + instruction


def contains_keyword(text: str, keyword: str) -> int:
    """Programmatic verifier: case-insensitive whole-word keyword inclusion."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not keyword or not re.fullmatch(r"[A-Za-z0-9_'-]+", keyword):
        raise ValueError(f"unsupported keyword for whole-word verifier: {keyword!r}")
    pat = re.compile(rf"(?<![A-Za-z0-9_'-]){re.escape(keyword)}(?![A-Za-z0-9_'-])", re.I)
    return int(pat.search(text) is not None)


def tile_deterministic_scores(scores: Sequence[float], k: int = K_SAMPLES) -> np.ndarray:
    """Represent greedy deterministic generation as k identical within-item samples."""
    arr = np.asarray(scores, dtype=np.float64).reshape(-1, 1)
    if k < 1:
        raise ValueError("k must be >=1")
    return np.repeat(arr, int(k), axis=1)


def paired_item_bootstrap(a: Sequence[float], b: Sequence[float], *, seed: int = 0, k: int = K_SAMPLES):
    """Bootstrap paired mean(a-b) using the frozen C2b item-cluster routine."""
    aa = tile_deterministic_scores(a, k=k)
    bb = tile_deterministic_scores(b, k=k)
    if aa.shape != bb.shape:
        raise ValueError("paired bootstrap inputs must have same shape")
    return adj.cluster_bootstrap_ci(
        aa - bb,
        b=BOOTSTRAP_B,
        ci_level=BONFERRONI_CI_LEVEL,
        seed=int(seed),
        cluster=True,
    )


@dataclass(frozen=True)
class CellScores:
    item_ids: List[str]
    scores: List[int]
    degeneracy: List[float]
    mean_score: float
    mean_degeneracy: float

    @classmethod
    def from_texts(cls, item_ids: Sequence[str], texts: Sequence[str], keyword: str) -> "CellScores":
        if len(item_ids) != len(texts):
            raise ValueError("item_ids/texts length mismatch")
        scores = [contains_keyword(t, keyword) for t in texts]
        deg = [degeneracy_score(t) for t in texts]
        return cls(
            item_ids=[str(x) for x in item_ids],
            scores=[int(x) for x in scores],
            degeneracy=[float(x) for x in deg],
            mean_score=float(np.mean(scores)) if scores else float("nan"),
            mean_degeneracy=float(np.mean(deg)) if deg else float("nan"),
        )


@dataclass(frozen=True)
class CandidateResult:
    source_layer_idx: int
    steering_hidden_state_layer: int
    alpha: float
    steer: CellScores
    baseline_mean_degeneracy: float
    coherence_ok: bool
    steer_minus_baseline: float

    def key(self) -> tuple[float, float, int, float]:
        # Higher effect first; coherent candidates beat incoherent ones; then less
        # degeneracy and lower layer/alpha for deterministic tie-breaking.
        return (
            1.0 if self.coherence_ok else 0.0,
            self.steer_minus_baseline,
            -self.source_layer_idx,
            -self.alpha,
        )


def coherence_ok(steer_mean_degeneracy: float, baseline_mean_degeneracy: float) -> bool:
    ceiling = COHERENCE_MAX_RATIO * float(baseline_mean_degeneracy) + COHERENCE_EPS_FLOOR
    return bool(float(steer_mean_degeneracy) <= ceiling + 1e-12)


def choose_candidate(candidates: Iterable[CandidateResult]) -> CandidateResult:
    rows = list(candidates)
    if not rows:
        raise ValueError("no candidates")
    return max(rows, key=lambda r: r.key())


def make_summary_payload(
    *,
    experiment_id: str,
    model: str,
    model_revision: str | None,
    method_source_commit: str,
    data_hash: str,
    config_hash: str,
    seed: int,
    keyword: str,
    baseline: CellScores,
    prompt: CellScores,
    selected: CandidateResult,
    steer_minus_prompt_ci_seed: int,
    steer_minus_baseline_ci_seed: int,
) -> Dict[str, object]:
    primary_ci = paired_item_bootstrap(
        selected.steer.scores, baseline.scores, seed=steer_minus_baseline_ci_seed
    )
    secondary_ci = paired_item_bootstrap(
        selected.steer.scores, prompt.scores, seed=steer_minus_prompt_ci_seed
    )
    primary_pass_dev_sanity = bool(
        selected.steer_minus_baseline >= DELTA
        and selected.coherence_ok
        and selected.steer.mean_score > baseline.mean_score
    )
    payload = {
        "experiment_id": experiment_id,
        "stage": "stage1_dev_only_no_test",
        "valid_for_paper": False,
        "model": model,
        "model_revision": model_revision,
        "method": "Stolfo-style instruction steering vector: mean activation(with instruction) - mean activation(without instruction), added to one residual-stream layer.",
        "method_source": {
            "repo": "https://github.com/microsoft/llm-steer-instruct",
            "commit": method_source_commit,
            "license": "MIT",
        },
        "data_hash": data_hash,
        "config_hash": config_hash,
        "seed": int(seed),
        "keyword": keyword,
        "primary_estimand": "steer_minus_baseline",
        "secondary_estimand": "steer_minus_prompt",
        "frozen_gate": {
            "delta": DELTA,
            "bootstrap_b": BOOTSTRAP_B,
            "ci_level": BONFERRONI_CI_LEVEL,
            "coherence": f"g^S <= {COHERENCE_MAX_RATIO} * g^0 + {COHERENCE_EPS_FLOOR}",
            "bonferroni_family": "reuse C2b 1 - 0.05/3 CI level for assay-validity positive control",
        },
        "baseline": asdict(baseline),
        "prompt": asdict(prompt),
        "selected": {
            "source_layer_idx": selected.source_layer_idx,
            "steering_hidden_state_layer": selected.steering_hidden_state_layer,
            "alpha": selected.alpha,
            "steer": asdict(selected.steer),
            "coherence_ok": selected.coherence_ok,
            "baseline_mean_degeneracy": selected.baseline_mean_degeneracy,
            "steer_minus_baseline": selected.steer_minus_baseline,
        },
        "dev_effects": {
            "steer_minus_baseline": {
                "mean": primary_ci.point,
                "ci_lo": primary_ci.ci_lo,
                "ci_hi": primary_ci.ci_hi,
                "b": primary_ci.b,
                "ci_level": primary_ci.ci_level,
                "passes_dev_sanity": primary_pass_dev_sanity,
            },
            "steer_minus_prompt": {
                "mean": secondary_ci.point,
                "ci_lo": secondary_ci.ci_lo,
                "ci_hi": secondary_ci.ci_hi,
                "b": secondary_ci.b,
                "ci_level": secondary_ci.ci_level,
                "comparator_bound": True,
            },
        },
    }
    return payload
