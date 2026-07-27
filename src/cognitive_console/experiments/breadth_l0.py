
"""Minimal L0 harness for persona scope-locking / breadth axis.

This module is deliberately exploratory. It can report that breadth/focus is not
one stable linear direction: extraction and legibility return explicit failure
fields instead of forcing a layer or a positive verdict.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Protocol, Sequence

import numpy as np

from ..activations.provider import SyntheticActivationProvider
from ..metrics import random_null_baseline, same_origin_facade
from ..steering.extract import (
    LayerSelection,
    extract_caa,
    mean_difference_vector,
    min_layer_for_depth,
    select_nondegenerate_layer,
)
from ..steering.generate import GenBackend
from .adjudicate_c2b import BONFERRONI_CI_LEVEL, BootstrapCI, cluster_bootstrap_ci

_CONDITIONS = ("no_persona", "narrow_persona", "oracle_persona")
_EPS = 1e-12


@dataclass(frozen=True)
class BreadthTask:
    item_id: str
    family: str
    task_text: str
    narrow_persona: str
    narrow_domain: str
    oracle_persona: str
    oracle_domain: str
    oracle_solution: str
    oracle_domain_markers: List[str]
    persona_domain_markers: List[str]
    acceptance_criteria: List[str]
    oracle_determination: str


@dataclass(frozen=True)
class ClassifiedSample:
    sample_index: int
    text: str
    domains: List[str]
    uses_oracle_domain: bool
    uses_narrow_domain: bool
    valid: bool
    invalid_reason: str = ""


@dataclass(frozen=True)
class ItemConditionResult:
    item_id: str
    condition: str
    prompt: str
    samples: List[ClassifiedSample]

    @property
    def domain_coverage_at_k(self) -> int:
        domains = set()
        for s in self.samples:
            if s.valid:
                domains.update(s.domains)
        return len(domains)

    @property
    def oracle_reach_at_k(self) -> bool:
        return any(s.valid and s.uses_oracle_domain for s in self.samples)

    @property
    def valid_sample_count(self) -> int:
        return sum(1 for s in self.samples if s.valid)


@dataclass(frozen=True)
class PairedSuppressionResult:
    strict_suppression_rate: float
    calibrated_suppression_rate: float
    strict_item_ids: List[str]
    calibrated_item_ids: List[str]
    coverage_diff_narrow_minus_no_persona: List[float]
    coverage_bootstrap: Dict[str, float]


@dataclass(frozen=True)
class BreadthAxisResult:
    method: str
    axis: str
    selected_layer: Optional[int]
    stable_layer_found: bool
    unstable_reason: str
    separation_by_layer: Dict[str, float]
    layer_selection: Optional[Dict[str, object]]
    facade_ratio: Optional[float]
    facade_ci: Optional[List[float]]
    broad_reach: Optional[float]
    focus_reach: Optional[float]
    pole_reach: Optional[float]
    broad_null_p95: Optional[float]
    lexical_control_reach: Optional[float]
    expected_order: bool
    linearly_readable: bool
    verdict: str


@dataclass(frozen=True)
class BreadthRunResult:
    schema: str
    backend: str
    model: str
    k: int
    fingerprint: str
    coverage_guard_passed: bool
    coverage_guard: Dict[str, object]
    metrics: Dict[str, object]
    suppression: PairedSuppressionResult
    breadth_axis: BreadthAxisResult
    items: List[Dict[str, object]]

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


class DomainClassifier(Protocol):
    def classify(self, text: str, task: BreadthTask, sample_index: int = 0) -> ClassifiedSample:
        ...


def load_tasks(path: str | Path) -> List[BreadthTask]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return [BreadthTask(**row) for row in payload["items"]]


def load_contrast_pairs(path: str | Path) -> tuple[List[str], List[str]]:
    broad: Dict[str, str] = {}
    focus: Dict[str, str] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row["polarity"] == "broad":
            broad[row["pair_id"]] = row["text"]
        elif row["polarity"] == "focus":
            focus[row["pair_id"]] = row["text"]
    ids = sorted(set(broad) & set(focus))
    return [broad[i] for i in ids], [focus[i] for i in ids]


def load_readability_prompts(path: str | Path) -> Dict[str, List[str]]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def render_prompt(task: BreadthTask, condition: str, sample_index: int = 0) -> str:
    if condition == "no_persona":
        persona = "Solve the task carefully. Use the best method you can."
    elif condition == "narrow_persona":
        persona = task.narrow_persona
    elif condition == "oracle_persona":
        persona = task.oracle_persona
    else:
        raise ValueError(f"unknown condition: {condition!r}")
    return (
        f"{persona}\n"
        "Return a concise solution. If useful, name the method/domain you used.\n"
        f"Task: {task.task_text}\n"
        f"Attempt index: {sample_index}"
    )


def _marker_hit(text: str, markers: Sequence[str]) -> bool:
    """Return true only for whole-token / whole-phrase marker matches.

    Substring matching is unsafe here: e.g. "EV" matches "review" and "6"
    matches any incidental digit. Markers are escaped and wrapped in non-word
    boundaries so they must appear as a complete token or phrase.
    """
    low = text.lower()
    for marker in markers:
        m = str(marker).strip().lower()
        if not m:
            continue
        pattern = r"(?<![A-Za-z0-9_])" + re.escape(m) + r"(?![A-Za-z0-9_])"
        if re.search(pattern, low):
            return True
    return False


class RuleBasedDomainClassifier:
    """Deterministic marker classifier; replaceable by a frozen LLM judge later."""

    def __init__(self, extra_markers: Optional[Dict[str, Sequence[str]]] = None) -> None:
        self.extra_markers = {k: [m.lower() for m in v] for k, v in (extra_markers or {}).items()}

    def classify(self, text: str, task: BreadthTask, sample_index: int = 0) -> ClassifiedSample:
        low = text.lower()
        domains: List[str] = []
        oracle_domain_tokens = [task.oracle_domain, task.oracle_domain.replace("_", " ")]
        narrow_domain_tokens = [task.narrow_domain, task.narrow_domain.replace("_", " ")]
        if _marker_hit(low, list(task.oracle_domain_markers) + oracle_domain_tokens):
            domains.append(task.oracle_domain)
        if _marker_hit(low, list(task.persona_domain_markers) + narrow_domain_tokens):
            domains.append(task.narrow_domain)
        for domain, markers in self.extra_markers.items():
            if domain not in domains and _marker_hit(low, markers):
                domains.append(domain)
        invalid_reason = ""
        if not text.strip():
            invalid_reason = "empty output"
        elif len(re.findall(r"\w+", text)) < 3:
            invalid_reason = "too few tokens"
        return ClassifiedSample(
            sample_index=int(sample_index),
            text=text,
            domains=sorted(set(domains)),
            uses_oracle_domain=task.oracle_domain in domains,
            uses_narrow_domain=task.narrow_domain in domains,
            valid=(invalid_reason == ""),
            invalid_reason=invalid_reason,
        )


class LLMJudgeDomainClassifier:
    """Local-model judge seam; no paid API is called.

    The judge function may be injected directly for tests, or a local GenBackend
    can be supplied. Backend generations are expected to return a JSON object
    with at least ``domains`` and optional validity flags.
    """

    def __init__(self, judge_fn=None, backend: Optional[GenBackend] = None) -> None:
        if judge_fn is None and backend is None:
            raise ValueError("LLMJudgeDomainClassifier requires a local judge_fn or backend")
        self.judge_fn = judge_fn
        self.backend = backend

    def _prompt(self, text: str, task: BreadthTask) -> str:
        return (
            "You are a frozen domain-use judge for a synthetic task. "
            "Return ONLY compact JSON with keys domains (array), valid (bool), "
            "invalid_reason (string). Allowed domains are: "
            f"{task.oracle_domain}, {task.narrow_domain}, general_reasoning. "
            "Label a domain only if the solution uses that method/domain, not "
            "merely because it contains a numeric answer.\n"
            f"Task: {task.task_text}\n"
            f"Oracle domain: {task.oracle_domain}; method markers: {task.oracle_domain_markers}\n"
            f"Narrow domain: {task.narrow_domain}; method markers: {task.persona_domain_markers}\n"
            f"Solution text:\n{text}"
        )

    def _backend_judge(self, text: str, task: BreadthTask) -> Dict[str, object]:
        raw = self.backend.generate(self._prompt(text, task), max_new_tokens=160)  # type: ignore[union-attr]
        m = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if not m:
            return {"domains": [], "valid": False, "invalid_reason": "judge returned no JSON"}
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return {"domains": [], "valid": False, "invalid_reason": "judge returned invalid JSON"}

    def classify(self, text: str, task: BreadthTask, sample_index: int = 0) -> ClassifiedSample:
        row = (
            self.judge_fn(text=text, task=task, sample_index=sample_index)
            if self.judge_fn is not None
            else self._backend_judge(text, task)
        )
        domains = sorted({str(d) for d in row.get("domains", [])})
        valid = bool(row.get("valid", True))
        invalid_reason = str(row.get("invalid_reason", "" if valid else "judge marked invalid"))
        return ClassifiedSample(
            sample_index=int(sample_index),
            text=text,
            domains=domains,
            uses_oracle_domain=task.oracle_domain in domains,
            uses_narrow_domain=task.narrow_domain in domains,
            valid=valid,
            invalid_reason=invalid_reason,
        )


class MockBreadthBackend(GenBackend):
    """Deterministic fake generator that emits parseable domain tags."""

    def __init__(self, tasks: Sequence[BreadthTask]) -> None:
        self.tasks = {t.item_id: t for t in tasks}

    def _find_task(self, prompt: str) -> BreadthTask:
        for task in self.tasks.values():
            if task.task_text in prompt:
                return task
        raise ValueError("mock backend could not match prompt to task")

    def generate(self, prompt: str, steer=None, max_new_tokens: int = 128) -> str:
        task = self._find_task(prompt)
        m = re.search(r"Attempt index:\s*(\d+)", prompt)
        idx = int(m.group(1)) if m else 0
        if task.narrow_persona in prompt:
            domain = task.narrow_domain
            method = "in-persona workflow"
        elif task.oracle_persona in prompt:
            domain = task.oracle_domain
            method = "oracle method"
        else:
            cycle = [task.oracle_domain, task.narrow_domain, "general_reasoning"]
            domain = cycle[idx % len(cycle)]
            method = "cross-domain search" if domain == task.oracle_domain else "baseline reasoning"
        answer = task.oracle_solution if domain == task.oracle_domain else "A plausible but domain-locked answer."
        return f"DOMAIN: {domain}. METHOD: {method}. {answer}"


def sample_conditions(
    backend: GenBackend,
    classifier: DomainClassifier,
    tasks: Sequence[BreadthTask],
    k: int,
    *,
    max_new_tokens: int = 160,
) -> List[ItemConditionResult]:
    if k <= 0:
        raise ValueError("k must be positive")
    rows: List[ItemConditionResult] = []
    for task in tasks:
        for condition in _CONDITIONS:
            samples: List[ClassifiedSample] = []
            first_prompt = render_prompt(task, condition, sample_index=0)
            for i in range(k):
                prompt = render_prompt(task, condition, sample_index=i)
                text = backend.generate(prompt, max_new_tokens=max_new_tokens)
                samples.append(classifier.classify(text, task, sample_index=i))
            rows.append(ItemConditionResult(task.item_id, condition, first_prompt, samples))
    return rows


def results_by_item_condition(rows: Sequence[ItemConditionResult]) -> Dict[str, Dict[str, ItemConditionResult]]:
    out: Dict[str, Dict[str, ItemConditionResult]] = {}
    for r in rows:
        out.setdefault(r.item_id, {})[r.condition] = r
    return out


def domain_coverage_at_k(samples: Sequence[ClassifiedSample]) -> int:
    domains = set()
    for s in samples:
        if s.valid:
            domains.update(s.domains)
    return len(domains)


def oracle_suppression(rows: Sequence[ItemConditionResult], *, bootstrap_b: int = 2000, seed: int = 0) -> PairedSuppressionResult:
    by = results_by_item_condition(rows)
    strict: List[str] = []
    calibrated: List[str] = []
    coverage_diffs: List[float] = []
    for item_id, cond in sorted(by.items()):
        narrow = cond["narrow_persona"]
        no = cond["no_persona"]
        oracle = cond["oracle_persona"]
        if no.oracle_reach_at_k and not narrow.oracle_reach_at_k:
            strict.append(item_id)
        if oracle.oracle_reach_at_k and not narrow.oracle_reach_at_k:
            calibrated.append(item_id)
        coverage_diffs.append(float(narrow.domain_coverage_at_k - no.domain_coverage_at_k))
    n = max(1, len(by))
    ci: BootstrapCI = cluster_bootstrap_ci(
        np.asarray(coverage_diffs, dtype=np.float64), b=int(bootstrap_b),
        ci_level=BONFERRONI_CI_LEVEL, seed=int(seed), cluster=True,
    )
    return PairedSuppressionResult(
        strict_suppression_rate=len(strict) / n,
        calibrated_suppression_rate=len(calibrated) / n,
        strict_item_ids=strict,
        calibrated_item_ids=calibrated,
        coverage_diff_narrow_minus_no_persona=coverage_diffs,
        coverage_bootstrap=asdict(ci),
    )


def _layer_selection_to_dict(sel: LayerSelection) -> Dict[str, object]:
    return {
        "chosen": sel.chosen,
        "ranked": sel.ranked,
        "min_layer": sel.min_layer,
        "top_k": sel.top_k,
        "candidates": {str(k): asdict(v) for k, v in sorted(sel.candidates.items())},
    }


def extract_breadth_axis(
    provider,
    broad_texts: Sequence[str],
    focus_texts: Sequence[str],
    readability: Dict[str, List[str]],
    *,
    method: str = "caa",
    layers: Optional[Sequence[int]] = None,
    min_depth_frac: float = 0.2,
    n_null: int = 500,
    seed: int = 0,
) -> BreadthAxisResult:
    if method != "caa":
        raise ValueError("minimal L0 currently implements CAA extraction; ITI can reuse this seam later")
    if layers is None:
        layers = provider.available_layers()
    layers = [int(x) for x in layers]
    if not layers:
        raise ValueError("no layers")
    caa = extract_caa(provider, "breadth_focus", broad_texts, focus_texts, layers=layers)
    neutral = list(readability["neutral_prompts"])
    broad_eval = list(readability["broad_prompts"])
    focus_eval = list(readability["focus_prompts"])
    max_layer = max(layers)
    min_layer = min_layer_for_depth(max_layer, min_depth_frac=min_depth_frac)

    sep_by: Dict[int, float] = {}
    pole_by: Dict[int, float] = {}
    null_by: Dict[int, float] = {}
    dirs: Dict[int, np.ndarray] = {}
    for ell in layers:
        pos = provider.get_activations(broad_texts, ell).astype(np.float64)
        neg = provider.get_activations(focus_texts, ell).astype(np.float64)
        vec = mean_difference_vector(pos, neg)
        norm = float(np.linalg.norm(vec))
        direction = vec / (norm if norm > _EPS else 1.0)
        dirs[ell] = direction
        sep_by[ell] = caa.per_layer[ell].separation
        neutral_acts = provider.get_activations(neutral, ell).astype(np.float64)
        displacement = pos.mean(axis=0) - neutral_acts.mean(axis=0)
        pole_by[ell] = float(np.dot(displacement, direction))
        null_dist = random_null_baseline(displacement, n_samples=int(n_null), seed=int(seed) + ell)
        null_by[ell] = float(np.percentile(null_dist, 95))
    sel = select_nondegenerate_layer(sep_by, pole_by, null_by, min_layer=min_layer, top_k=3)
    if sel.chosen is None:
        return BreadthAxisResult(
            method=method, axis="breadth_focus", selected_layer=None,
            stable_layer_found=False,
            unstable_reason="no layer passed depth/separation/pole-vs-null nondegeneracy",
            separation_by_layer={str(k): float(v) for k, v in sep_by.items()},
            layer_selection=_layer_selection_to_dict(sel),
            facade_ratio=None, facade_ci=None, broad_reach=None, focus_reach=None,
            pole_reach=None, broad_null_p95=None, lexical_control_reach=None, expected_order=False,
            linearly_readable=False,
            verdict="NOT_LINEAR_OR_DEGENERATE",
        )

    ell = int(sel.chosen)
    direction = dirs[ell]
    neutral_acts = provider.get_activations(neutral, ell).astype(np.float64)
    broad_acts = provider.get_activations(broad_eval, ell).astype(np.float64)
    focus_acts = provider.get_activations(focus_eval, ell).astype(np.float64)
    lexical_controls = list(readability.get("lexical_controls", []))
    pos_acts = provider.get_activations(broad_texts, ell).astype(np.float64)
    control_acts = provider.get_activations(lexical_controls, ell).astype(np.float64) if lexical_controls else np.empty((0, provider.hidden_dim))
    neutral_proj = neutral_acts @ direction
    broad_proj = broad_acts @ direction
    focus_proj = focus_acts @ direction
    control_proj = control_acts @ direction if len(control_acts) else np.asarray([], dtype=np.float64)
    pos_proj = pos_acts @ direction
    facade = same_origin_facade(broad_proj, pos_proj, neutral_proj, n_boot=500, seed=seed)
    broad_reach = float(broad_proj.mean() - neutral_proj.mean())
    focus_reach = float(focus_proj.mean() - neutral_proj.mean())
    lexical_control_reach = float(control_proj.mean() - neutral_proj.mean()) if len(control_proj) else 0.0
    null_dist = random_null_baseline(broad_acts.mean(axis=0) - neutral_acts.mean(axis=0), n_samples=int(n_null), seed=int(seed) + 999)
    broad_null_p95 = float(np.percentile(null_dist, 95))
    expected_order = bool(broad_reach > 0.0 and focus_reach < broad_reach and facade.pole_reach > 0.0)
    specific_to_breadth = bool(broad_reach > lexical_control_reach)
    linearly_readable = bool(
        expected_order and broad_reach > broad_null_p95
        and specific_to_breadth and 0.0 < facade.facade_ratio <= 1.25
    )
    if linearly_readable:
        verdict = "LINEARLY_READABLE_L0"
    elif expected_order and broad_reach > broad_null_p95 and not specific_to_breadth:
        verdict = "READABLE_BUT_NONSPECIFIC_LEXICAL_CONTROL"
    else:
        verdict = "READABILITY_FAILED_REPORT_NOT_LINEAR"
    return BreadthAxisResult(
        method=method, axis="breadth_focus", selected_layer=ell,
        stable_layer_found=True, unstable_reason="",
        separation_by_layer={str(k): float(v) for k, v in sep_by.items()},
        layer_selection=_layer_selection_to_dict(sel),
        facade_ratio=float(facade.facade_ratio),
        facade_ci=[float(facade.ci_lo), float(facade.ci_hi)],
        broad_reach=broad_reach, focus_reach=focus_reach,
        pole_reach=float(facade.pole_reach), broad_null_p95=broad_null_p95,
        lexical_control_reach=lexical_control_reach,
        expected_order=expected_order, linearly_readable=linearly_readable,
        verdict=verdict,
    )


def build_mock_activation_provider(broad_texts: Sequence[str], focus_texts: Sequence[str], readability: Dict[str, List[str]]):
    provider = SyntheticActivationProvider(dim=96, layers=[0, 2, 4, 6, 8], seed=20260727, noise_scale=0.05)
    provider.plant_contrast(
        "breadth_focus", broad_texts, focus_texts, magnitude=5.0,
        layer_gain={0: 0.1, 2: 0.3, 4: 1.0, 6: 1.6, 8: 1.2},
    )
    layer = 6
    direction = provider.direction("breadth_focus", layer)
    # Add held-out readability signal without reusing downstream item texts.
    for text in readability["broad_prompts"]:
        provider.plant_facade("breadth_focus", text, f"VECTOR::{text}", 4.0, 0.55, layer)
    for text in readability["focus_prompts"]:
        provider.plant_facade("breadth_focus", text, f"FOCUS_VECTOR::{text}", -2.0, 1.0, layer)
    for text in readability.get("lexical_controls", []):
        provider.plant_facade("breadth_focus", text, f"CONTROL_VECTOR::{text}", 4.0, 0.1, layer)
    return provider


def coverage_guard(rows: Sequence[ItemConditionResult], tasks: Sequence[BreadthTask], k: int) -> Dict[str, object]:
    expected_items = {t.item_id for t in tasks}
    by = results_by_item_condition(rows)
    missing_items = sorted(expected_items - set(by))
    missing_conditions = []
    short_cells = []
    unclassified_valid_samples = []
    for item_id in sorted(expected_items):
        conds = by.get(item_id, {})
        for condition in _CONDITIONS:
            row = conds.get(condition)
            if row is None:
                missing_conditions.append([item_id, condition])
                continue
            if len(row.samples) != k:
                short_cells.append([item_id, condition, len(row.samples)])
            for s in row.samples:
                if s.valid and not s.domains:
                    unclassified_valid_samples.append([item_id, condition, s.sample_index])
    ok = not (missing_items or missing_conditions or short_cells or unclassified_valid_samples)
    return {
        "ok": ok,
        "expected_items": len(expected_items),
        "expected_conditions": list(_CONDITIONS),
        "k": int(k),
        "missing_items": missing_items,
        "missing_conditions": missing_conditions,
        "short_cells": short_cells,
        "unclassified_valid_samples": unclassified_valid_samples[:20],
        "n_unclassified_valid_samples": len(unclassified_valid_samples),
    }


def result_fingerprint(tasks_path: Path, pairs_path: Path, read_path: Path, *, backend: str, model: str, k: int, seed: int) -> str:
    h = hashlib.sha256()
    for path in [tasks_path, pairs_path, read_path]:
        h.update(path.read_bytes())
    h.update(json.dumps({"backend": backend, "model": model, "k": k, "seed": seed}, sort_keys=True).encode())
    return h.hexdigest()[:16]


def aggregate_metrics(rows: Sequence[ItemConditionResult]) -> Dict[str, object]:
    by_condition: Dict[str, List[ItemConditionResult]] = {c: [] for c in _CONDITIONS}
    for r in rows:
        by_condition[r.condition].append(r)
    out: Dict[str, object] = {}
    for condition, vals in by_condition.items():
        coverages = [v.domain_coverage_at_k for v in vals]
        reaches = [1.0 if v.oracle_reach_at_k else 0.0 for v in vals]
        out[condition] = {
            "mean_domain_coverage_at_k": float(np.mean(coverages)) if coverages else math.nan,
            "oracle_reach_rate_at_k": float(np.mean(reaches)) if reaches else math.nan,
            "per_item_domain_coverage_at_k": {v.item_id: v.domain_coverage_at_k for v in vals},
            "per_item_oracle_reach_at_k": {v.item_id: v.oracle_reach_at_k for v in vals},
        }
    return out


def run_mock_l0(tasks_path: Path, pairs_path: Path, read_path: Path, *, k: int = 5, seed: int = 0, model: str = "mock") -> BreadthRunResult:
    tasks = load_tasks(tasks_path)
    broad, focus = load_contrast_pairs(pairs_path)
    readability = load_readability_prompts(read_path)
    backend = MockBreadthBackend(tasks)
    classifier = RuleBasedDomainClassifier(extra_markers={"general_reasoning": ["general_reasoning", "baseline reasoning"]})
    rows = sample_conditions(backend, classifier, tasks, k)
    guard = coverage_guard(rows, tasks, k)
    if not guard["ok"]:
        raise RuntimeError(f"coverage guard failed: {guard}")
    provider = build_mock_activation_provider(broad, focus, readability)
    axis = extract_breadth_axis(provider, broad, focus, readability, seed=seed)
    suppression = oracle_suppression(rows, seed=seed, bootstrap_b=500)
    fp = result_fingerprint(tasks_path, pairs_path, read_path, backend="mock", model=model, k=k, seed=seed)
    return BreadthRunResult(
        schema="persona_breadth_l0_result_v1", backend="mock", model=model, k=int(k),
        fingerprint=fp, coverage_guard_passed=True, coverage_guard=guard,
        metrics=aggregate_metrics(rows), suppression=suppression, breadth_axis=axis,
        items=[asdict(r) for r in rows],
    )
