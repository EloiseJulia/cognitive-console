"""Faithful PSR-style DEV-optimized steering for Workstream D.

This module is deliberately upstream of the frozen C2b adjudicator.  It builds a
low-dimensional natural-activation basis, searches seeded candidate directions
on DEV only, and returns one frozen vector/config/alpha candidate for TEST.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from ..eval import scorers as _scorers
from ..experiments import adjudicate_c2b as adj
from .generate import GenBackend, SteerConfig, SteeredHFBackend, unit_vector

_EPS = 1e-12


@dataclass(frozen=True)
class PSRConfig:
    """Frozen knobs for the preregistered faithful-PSR primary method."""

    basis_rank: int = 16
    candidate_budget: int = 32
    optimizer_seed: int = 20260723
    coherence_lambda: float = 1.0
    covariance_source: str = "natural_and_extraction_activations"
    alpha_grid: Tuple[float, ...] = adj.ALPHA_GRID
    schedule_support: Tuple[int, int, int] = (-1, 0, 1)
    schedule_candidates: Tuple[Tuple[float, float, float], ...] = (
        (0.0, 1.0, 0.0),
        (0.25, 0.5, 0.25),
        (0.5, 0.5, 0.0),
        (0.0, 0.5, 0.5),
    )

    def to_dict(self) -> Dict[str, object]:
        out = asdict(self)
        out["alpha_grid"] = [float(x) for x in self.alpha_grid]
        out["schedule_support"] = [int(x) for x in self.schedule_support]
        out["schedule_candidates"] = [[float(v) for v in row] for row in self.schedule_candidates]
        return out


@dataclass(frozen=True)
class PSRBasis:
    axis: str
    layer: int
    basis: np.ndarray
    labels: List[str]
    diagnostics: Dict[str, object] = field(default_factory=dict)

    @property
    def dim(self) -> int:
        return int(self.basis.shape[1])

    @property
    def n_basis(self) -> int:
        return int(self.basis.shape[0])


@dataclass(frozen=True)
class PSRCandidate:
    coefficients: List[float]
    schedule_weights: List[float]
    direction: List[float]
    alpha: float
    dev_score: float
    dev_outcome: float
    dev_degeneracy: float
    baseline_degeneracy: float
    coherence_penalty: float
    coherence_ratio: float
    candidate_index: int


@dataclass(frozen=True)
class PSRResult:
    axis: str
    model: str
    backend: str
    layer: int
    schedule_layers: List[int]
    schedule_weights: List[float]
    direction: List[float]
    alpha: float
    selected_dev_score: float
    selected_dev_outcome: float
    selected_dev_degeneracy: float
    baseline_degeneracy: float
    evaluations_used: int
    candidate_budget: int
    item_ids_dev: List[str]
    item_ids_forbidden_test: List[str]
    config: Dict[str, object]
    basis_labels: List[str]
    basis_diagnostics: Dict[str, object]
    candidate: PSRCandidate

    def direction_array(self) -> np.ndarray:
        return np.asarray(self.direction, dtype=np.float64)

    def to_dict(self) -> Dict[str, object]:
        out = asdict(self)
        out["direction_sha256"] = _array_hash(self.direction_array())
        return out


def _array_hash(arr: np.ndarray) -> str:
    a = np.asarray(arr, dtype=np.float64)
    return hashlib.sha256(a.tobytes()).hexdigest()


def canonical_json_hash(payload: Dict[str, object], n: int = 16) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:n]


def _stable_sign(v: np.ndarray) -> np.ndarray:
    idx = int(np.argmax(np.abs(v)))
    return -v if v[idx] < 0 else v


def _orthonormalize(vectors: Sequence[np.ndarray], labels: Sequence[str]) -> Tuple[np.ndarray, List[str]]:
    rows: List[np.ndarray] = []
    out_labels: List[str] = []
    for v, label in zip(vectors, labels):
        x = np.asarray(v, dtype=np.float64).ravel()
        if not rows:
            residual = x
        else:
            residual = x - sum(float(np.dot(x, b)) * b for b in rows)
        norm = float(np.linalg.norm(residual))
        if norm <= _EPS:
            continue
        rows.append(_stable_sign(residual / norm))
        out_labels.append(str(label))
    if not rows:
        raise ValueError("PSR basis collapsed: no non-zero independent vectors")
    return np.vstack(rows), out_labels


def top_pca_directions(activations: np.ndarray, rank: int) -> np.ndarray:
    """Top principal directions of centered activations with deterministic signs."""
    x = np.asarray(activations, dtype=np.float64)
    if x.ndim != 2:
        raise ValueError("activations must be 2-D [n, d]")
    if len(x) < 2:
        raise ValueError("need at least two activation rows for PCA")
    centered = x - x.mean(axis=0, keepdims=True)
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    pcs = vt[: max(0, min(int(rank), vt.shape[0]))]
    return np.vstack([_stable_sign(row) for row in pcs]) if len(pcs) else np.empty((0, x.shape[1]))


def build_psr_basis(
    *,
    axis: str,
    layer: int,
    caa_direction: np.ndarray,
    iti_direction: np.ndarray,
    natural_activations: np.ndarray,
    r: int = 16,
) -> PSRBasis:
    """Build the fixed basis {CAA, ITI, top-r PCA(natural/extraction activations)}."""
    caa = unit_vector(caa_direction)
    iti = unit_vector(iti_direction)
    pcs = top_pca_directions(natural_activations, int(r))
    vectors: List[np.ndarray] = [caa, iti] + [row for row in pcs]
    labels = ["caa", "iti"] + [f"pca_{i+1}" for i in range(len(pcs))]
    basis, kept = _orthonormalize(vectors, labels)
    return PSRBasis(
        axis=str(axis),
        layer=int(layer),
        basis=basis,
        labels=kept,
        diagnostics={
            "requested_pca_rank": int(r),
            "activation_rows": int(np.asarray(natural_activations).shape[0]),
            "activation_dim": int(np.asarray(natural_activations).shape[1]),
            "kept_basis_vectors": int(len(kept)),
            "basis_labels": kept,
            "basis_vector_hashes": {
                label: _array_hash(row) for label, row in zip(kept, basis)
            },
        },
    )


def direction_from_coefficients(basis: PSRBasis, coefficients: Sequence[float]) -> np.ndarray:
    coeff = np.asarray(coefficients, dtype=np.float64).ravel()
    if coeff.shape[0] != basis.n_basis:
        raise ValueError(f"coefficient length {coeff.shape[0]} != basis size {basis.n_basis}")
    v = coeff @ basis.basis
    return unit_vector(v)


def local_schedule_layers(center_layer: int, num_hidden_layers: Optional[int] = None) -> List[int]:
    """Fixed local support {L-1,L,L+1}, clipped to valid hidden-state layers."""
    layers = [int(center_layer) - 1, int(center_layer), int(center_layer) + 1]
    out = []
    for ell in layers:
        if ell < 1:
            continue
        if num_hidden_layers is not None and ell > int(num_hidden_layers):
            continue
        out.append(int(ell))
    if not out:
        raise ValueError("empty PSR schedule after clipping")
    return out


def normalize_schedule_weights(weights: Sequence[float], n_layers: int) -> List[float]:
    w = np.asarray(weights, dtype=np.float64).ravel()
    if len(w) == 3 and int(n_layers) != 3:
        # Clip edge weights consistently with local_schedule_layers.
        if int(n_layers) == 2:
            w = w[1:] if w[0] != 0.0 else w[:2]
        else:
            w = w[: int(n_layers)]
    if len(w) != int(n_layers):
        raise ValueError(f"schedule weight length {len(w)} != number of layers {n_layers}")
    if np.any(w < -_EPS):
        raise ValueError("PSR schedule weights must be non-negative")
    s = float(w.sum())
    if s <= _EPS:
        raise ValueError("PSR schedule weights must sum to a positive value")
    return [float(x) for x in (w / s)]


def normalize_schedule_weights_for_layers(
    center_layer: int, layers: Sequence[int], weights: Sequence[float]
) -> List[float]:
    """Map raw {-1,0,+1} weights onto possibly edge-clipped schedule layers."""
    raw = list(np.asarray(weights, dtype=np.float64).ravel())
    if len(raw) != 3:
        return normalize_schedule_weights(raw, len(layers))
    by_offset = {-1: raw[0], 0: raw[1], 1: raw[2]}
    clipped = [by_offset[int(ell) - int(center_layer)] for ell in layers]
    return normalize_schedule_weights(clipped, len(clipped))


class ScheduledSteeredHFBackend(SteeredHFBackend):
    """HF backend extension that applies the same unit direction at {L-1,L,L+1}."""

    def _register_schedule_hooks(self, direction: np.ndarray, alpha: float,
                                 layers: Sequence[int], weights: Sequence[float]):
        self._ensure_loaded()
        n = int(self._config.num_hidden_layers)
        handles = []
        for ell, weight in zip(layers, weights):
            ell = int(ell)
            if not (1 <= ell <= n):
                raise ValueError(f"PSR schedule layer {ell} out of range 1..{n}")
            steer = SteerConfig(direction=direction, alpha=float(alpha) * float(weight), layer=ell)
            handles.append(self._layers[ell - 1].register_forward_hook(self._make_hook(steer)))
        return handles

    def generate_scheduled(self, prompt: str, direction: np.ndarray, alpha: float,
                           layers: Sequence[int], weights: Sequence[float],
                           max_new_tokens: int = 128, do_sample: bool = False,
                           temperature: float = 1.0, seed: Optional[int] = None) -> str:
        import torch

        self._ensure_loaded()
        self._seed_torch(seed if seed is not None else self.seed)
        text = self._render_user_chat_prompt(self._tokenizer, prompt, self.model_name)
        enc = self._tokenizer(text, return_tensors="pt", truncation=True, max_length=self.max_length)
        enc = {k: v.to(self.device) for k, v in enc.items()}
        input_len = enc["input_ids"].shape[1]
        handles = [] if abs(float(alpha)) <= _EPS else self._register_schedule_hooks(direction, alpha, layers, weights)
        try:
            kwargs = dict(max_new_tokens=int(max_new_tokens), do_sample=bool(do_sample),
                          pad_token_id=self._tokenizer.pad_token_id)
            if do_sample:
                kwargs["temperature"] = float(temperature)
            with torch.no_grad():
                out = self._model.generate(**enc, **kwargs)
        finally:
            for h in reversed(handles):
                h.remove()
        return self._tokenizer.decode(out[0][input_len:], skip_special_tokens=True)

    def generate_batch_scheduled(self, prompts: Sequence[str], direction: np.ndarray,
                                 alpha: float, layers: Sequence[int], weights: Sequence[float],
                                 max_new_tokens: int = 128, seeds: Optional[Sequence[int]] = None,
                                 do_sample: bool = False, temperature: float = 1.0) -> List[str]:
        import torch

        self._ensure_loaded()
        prompts = list(prompts)
        if not prompts:
            return []
        if do_sample:
            key = "|".join(str(int(s)) for s in seeds) if seeds else str(self.seed)
            batch_seed = int(hashlib.sha256(key.encode("utf-8")).hexdigest(), 16) % (2 ** 31)
            self._seed_torch(batch_seed)
        texts = [self._render_user_chat_prompt(self._tokenizer, p, self.model_name) for p in prompts]
        self._tokenizer.padding_side = "left"
        enc = self._tokenizer(texts, return_tensors="pt", padding=True, truncation=True,
                              max_length=self.max_length)
        enc = {k: v.to(self.device) for k, v in enc.items()}
        input_len = enc["input_ids"].shape[1]
        handles = [] if abs(float(alpha)) <= _EPS else self._register_schedule_hooks(direction, alpha, layers, weights)
        try:
            kwargs = dict(max_new_tokens=int(max_new_tokens), do_sample=bool(do_sample),
                          pad_token_id=self._tokenizer.pad_token_id)
            if do_sample:
                kwargs["temperature"] = float(temperature)
            with torch.no_grad():
                out = self._model.generate(**enc, **kwargs)
        finally:
            for h in reversed(handles):
                h.remove()
        new = out[:, input_len:]
        return [self._tokenizer.decode(row, skip_special_tokens=True) for row in new]


class PSROutcomeSampler(adj.OutcomeSampler):
    """Outcome sampler that applies a frozen PSR direction and local schedule."""

    def __init__(
        self,
        gen_backend: GenBackend,
        *,
        schedule_by_axis: Dict[str, Tuple[Sequence[int], Sequence[float]]],
        max_new_tokens: int = 64,
        do_sample: bool = True,
        temperature: float = 0.7,
        seed: int = 0,
        batch_size: int = 1,
        generation_observer=None,
    ) -> None:
        self.gen = gen_backend
        self.schedule_by_axis = {
            str(a): ([int(x) for x in layers], [float(w) for w in weights])
            for a, (layers, weights) in schedule_by_axis.items()
        }
        self.max_new_tokens = int(max_new_tokens)
        self.do_sample = bool(do_sample)
        self.temperature = float(temperature)
        self.seed = int(seed)
        self.batch_size = max(1, int(batch_size))
        self.generation_observer = generation_observer

    @property
    def supports_batch(self) -> bool:
        return self.batch_size > 1 and (
            hasattr(self.gen, "generate_batch_scheduled") or hasattr(self.gen, "generate_batch")
        )

    def _call_seed(self, axis: str, item: Dict, alpha: float, j: int) -> int:
        key = f"psr|{self.seed}|{axis}|{item.get('id')}|{float(alpha):.6f}|{j}"
        return int(hashlib.sha256(key.encode("utf-8")).hexdigest(), 16) % (2 ** 31)

    def _schedule(self, axis: str, layer: int) -> Tuple[List[int], List[float]]:
        if axis in self.schedule_by_axis:
            return self.schedule_by_axis[axis]
        return [int(layer)], [1.0]

    def _generate_one(self, prompt: str, direction: np.ndarray, alpha: float,
                      layers: Sequence[int], weights: Sequence[float], seed: int) -> str:
        if hasattr(self.gen, "generate_scheduled"):
            return self.gen.generate_scheduled(
                prompt, direction, alpha, layers, weights, self.max_new_tokens,
                do_sample=self.do_sample, temperature=self.temperature, seed=seed,
            )
        if len(layers) == 1 or isinstance(self.gen.__class__.__name__, str):
            steer = SteerConfig(direction=direction, alpha=float(alpha) * float(sum(weights)), layer=int(layers[0]))
            try:
                return self.gen.generate(prompt, steer, self.max_new_tokens,
                                         do_sample=self.do_sample, temperature=self.temperature, seed=seed)
            except TypeError:
                return self.gen.generate(prompt, steer, self.max_new_tokens)
        raise TypeError("backend does not support scheduled PSR generation")

    def sample(self, axis: str, item: Dict, instruction: str, alpha: float,
               k: int, direction: np.ndarray, layer: int) -> adj.SampleBatch:
        text_input = adj.format_task_input(axis, instruction, item)
        layers, weights = self._schedule(axis, layer)
        outs: List[float] = []
        degs: List[float] = []
        for j in range(int(k)):
            out = self._generate_one(
                text_input, direction, alpha, layers, weights,
                self._call_seed(axis, item, alpha, j),
            )
            score = adj.score_sample_outcome(axis, item, out)
            deg = _scorers.degeneracy_score(out)
            outs.append(score)
            degs.append(deg)
            if self.generation_observer is not None:
                self.generation_observer(
                    axis=axis,
                    item=item,
                    instruction=instruction,
                    alpha=float(alpha),
                    layer=int(layer),
                    sample_index=int(j),
                    sample_seed=int(self._call_seed(axis, item, alpha, j)),
                    prompt_text=text_input,
                    generation_text=str(out),
                    outcome=float(score),
                    degeneracy=float(deg),
                    max_new_tokens=int(self.max_new_tokens),
                )
        return adj.SampleBatch(outcomes=outs, degeneracies=degs)

    def sample_batch(self, axis: str, items: Sequence[Dict], instruction: str,
                     alpha: float, k: int, direction: np.ndarray,
                     layer: int) -> List[adj.SampleBatch]:
        items = list(items)
        if not self.supports_batch:
            return [self.sample(axis, it, instruction, alpha, k, direction, layer) for it in items]
        layers, weights = self._schedule(axis, layer)
        prompts: List[str] = []
        seeds: List[int] = []
        owner: List[int] = []
        owner_sample_index: List[int] = []
        for ii, it in enumerate(items):
            text_input = adj.format_task_input(axis, instruction, it)
            for j in range(int(k)):
                prompts.append(text_input)
                seeds.append(self._call_seed(axis, it, alpha, j))
                owner.append(ii)
                owner_sample_index.append(j)
        if hasattr(self.gen, "generate_batch_scheduled"):
            texts = self.gen.generate_batch_scheduled(
                prompts, direction, alpha, layers, weights, self.max_new_tokens,
                seeds=seeds, do_sample=self.do_sample, temperature=self.temperature,
            )
        else:
            steer = SteerConfig(direction=direction, alpha=float(alpha) * float(sum(weights)), layer=int(layers[0]))
            texts = self.gen.generate_batch(
                prompts, steer, self.max_new_tokens, seeds=seeds,
                do_sample=self.do_sample, temperature=self.temperature,
            )
        batches: List[adj.SampleBatch] = []
        for ii, it in enumerate(items):
            outs: List[float] = []
            degs: List[float] = []
            for idx, own in enumerate(owner):
                if own == ii:
                    score = adj.score_sample_outcome(axis, it, texts[idx])
                    deg = _scorers.degeneracy_score(texts[idx])
                    outs.append(score)
                    degs.append(deg)
                    if self.generation_observer is not None:
                        self.generation_observer(
                            axis=axis,
                            item=it,
                            instruction=instruction,
                            alpha=float(alpha),
                            layer=int(layer),
                            sample_index=int(owner_sample_index[idx]),
                            sample_seed=int(seeds[idx]),
                            prompt_text=str(prompts[idx]),
                            generation_text=str(texts[idx]),
                            outcome=float(score),
                            degeneracy=float(deg),
                            max_new_tokens=int(self.max_new_tokens),
                        )
            batches.append(adj.SampleBatch(outcomes=outs, degeneracies=degs))
        return batches


def _candidate_coefficients(rng: np.random.Generator, n_basis: int, budget: int) -> List[np.ndarray]:
    coeffs: List[np.ndarray] = []
    for idx in range(min(2, n_basis)):
        c = np.zeros(n_basis, dtype=np.float64)
        c[idx] = 1.0
        coeffs.append(c)
    while len(coeffs) < int(budget):
        c = rng.normal(size=n_basis)
        c /= max(float(np.linalg.norm(c)), _EPS)
        coeffs.append(c)
    return coeffs[: int(budget)]


def _candidate_tuples(
    rng: np.random.Generator,
    n_basis: int,
    budget: int,
    alpha_grid: Sequence[float],
    schedule_candidates: Sequence[Sequence[float]],
) -> List[Tuple[np.ndarray, float, List[float]]]:
    """Return budget-capped (coefficients, alpha, schedule) DEV evaluations.

    Per the frozen cost model, ONE candidate evaluation is exactly one complete
    DEV pass for one (direction coefficients, alpha, local schedule) tuple.
    """
    if int(budget) <= 0:
        raise ValueError("PSR candidate budget must be positive")
    alphas = [float(a) for a in alpha_grid]
    if not alphas:
        raise ValueError("PSR alpha grid must be non-empty")
    if not schedule_candidates:
        raise ValueError("PSR schedule candidates must be non-empty")

    out: List[Tuple[np.ndarray, float, List[float]]] = []
    special = _candidate_coefficients(rng, n_basis, min(2, int(budget)))
    for i, coeff in enumerate(special):
        out.append((coeff, alphas[i % len(alphas)], list(schedule_candidates[i % len(schedule_candidates)])))
    while len(out) < int(budget):
        coeff = rng.normal(size=n_basis)
        coeff /= max(float(np.linalg.norm(coeff)), _EPS)
        i = len(out)
        out.append((coeff, alphas[i % len(alphas)], list(schedule_candidates[i % len(schedule_candidates)])))
    return out


def optimize_psr_on_dev(
    *,
    axis: str,
    model: str,
    backend: str,
    basis: PSRBasis,
    sampler_factory,
    dev_items: Sequence[Dict],
    forbidden_test_items: Sequence[Dict],
    neutral_prompt: str,
    config: PSRConfig,
    k: int = adj.K_SAMPLES,
    num_hidden_layers: Optional[int] = None,
) -> PSRResult:
    """Seeded deterministic DEV-only PSR optimization.

    `forbidden_test_items` is never sampled; it is carried only so tests and
    provenance can prove the DEV/TEST split was known and disjoint.
    """
    dev_items = list(dev_items)
    forbidden_test_items = list(forbidden_test_items)
    dev_ids = [str(it["id"]) for it in dev_items]
    test_ids = [str(it["id"]) for it in forbidden_test_items]
    overlap = set(dev_ids) & set(test_ids)
    if overlap:
        raise ValueError(f"DEV/TEST overlap in PSR optimization: {sorted(overlap)[:5]}")

    rng = np.random.default_rng(int(config.optimizer_seed))
    schedule_layers = local_schedule_layers(basis.layer, num_hidden_layers=num_hidden_layers)
    schedule_candidates = [
        normalize_schedule_weights_for_layers(basis.layer, schedule_layers, row)
        for row in config.schedule_candidates
    ]
    candidates = _candidate_tuples(
        rng,
        basis.n_basis,
        int(config.candidate_budget),
        config.alpha_grid,
        schedule_candidates,
    )
    baseline_sampler = sampler_factory({axis: (schedule_layers, schedule_candidates[0])})
    _, base_deg, _ = adj._channel_item_outcomes(
        baseline_sampler, axis, dev_items, neutral_prompt, 0.0, k,
        basis.basis[0], basis.layer, phase="psr_dev_baseline", cell_key="alpha=0",
    )
    baseline_degeneracy = float(base_deg.mean())

    best: Optional[PSRCandidate] = None
    evals_used = 0
    for idx, (coeff, alpha, sched) in enumerate(candidates):
        if evals_used >= int(config.candidate_budget):
            break
        direction = direction_from_coefficients(basis, coeff)
        sampler = sampler_factory({axis: (schedule_layers, sched)})
        evals_used += 1
        outs, degs, _ = adj._channel_item_outcomes(
            sampler, axis, dev_items, neutral_prompt, float(alpha), k,
            direction, basis.layer, phase="psr_dev_alpha",
            cell_key=f"cand={idx}|alpha={float(alpha)}",
        )
        outcome = float(outs.mean())
        degeneracy = float(degs.mean())
        if baseline_degeneracy > _EPS:
            ratio = degeneracy / baseline_degeneracy
        else:
            ratio = 0.0 if degeneracy <= _EPS else float("inf")
        penalty = max(0.0, ratio - float(adj.COHERENCE_MAX_RATIO))
        score = outcome - float(config.coherence_lambda) * penalty
        cand = PSRCandidate(
            coefficients=[float(x) for x in coeff],
            schedule_weights=[float(x) for x in sched],
            direction=[float(x) for x in direction],
            alpha=float(alpha),
            dev_score=float(score),
            dev_outcome=outcome,
            dev_degeneracy=degeneracy,
            baseline_degeneracy=baseline_degeneracy,
            coherence_penalty=float(penalty),
            coherence_ratio=float(ratio),
            candidate_index=int(idx),
        )
        if best is None or cand.dev_score > best.dev_score:
            best = cand
    if best is None:
        raise RuntimeError("PSR optimizer evaluated no candidates")
    if evals_used > int(config.candidate_budget):
        raise RuntimeError("PSR optimizer exceeded candidate budget")

    return PSRResult(
        axis=str(axis),
        model=str(model),
        backend=str(backend),
        layer=int(basis.layer),
        schedule_layers=[int(x) for x in schedule_layers],
        schedule_weights=[float(x) for x in best.schedule_weights],
        direction=[float(x) for x in best.direction],
        alpha=float(best.alpha),
        selected_dev_score=float(best.dev_score),
        selected_dev_outcome=float(best.dev_outcome),
        selected_dev_degeneracy=float(best.dev_degeneracy),
        baseline_degeneracy=float(baseline_degeneracy),
        evaluations_used=int(evals_used),
        candidate_budget=int(config.candidate_budget),
        item_ids_dev=dev_ids,
        item_ids_forbidden_test=test_ids,
        config=config.to_dict(),
        basis_labels=list(basis.labels),
        basis_diagnostics=dict(basis.diagnostics),
        candidate=best,
    )


def psr_provenance_payload(
    *,
    model: str,
    backend: str,
    seed: int,
    psr_results: Dict[str, PSRResult],
    adjudication_params: Dict[str, object],
    item_ids_by_axis: Dict[str, Sequence[str]],
    extra: Optional[Dict[str, object]] = None,
) -> Dict[str, object]:
    return {
        "steering_method": "psr",
        "model": str(model),
        "backend": str(backend),
        "seed": int(seed),
        "psr_optimization": {axis: row.to_dict() for axis, row in sorted(psr_results.items())},
        "adjudication_params": adjudication_params,
        "coverage": {axis: [str(x) for x in ids] for axis, ids in sorted(item_ids_by_axis.items())},
        **(extra or {}),
    }


def validate_psr_coverage(
    *,
    result_payload: Dict[str, object],
    expected_fingerprint: str,
    expected_axes: Sequence[str],
    expected_item_ids_by_axis: Dict[str, Sequence[str]],
    expected_k: int = adj.K_SAMPLES,
) -> None:
    """Fail closed if a PSR verdict cannot be tied to complete expected coverage."""
    if result_payload.get("steering_method") != "psr":
        raise ValueError("result is not a PSR steering-method payload")
    if str(result_payload.get("config_fingerprint", "")) != str(expected_fingerprint):
        raise ValueError("PSR config_fingerprint mismatch")
    axes_rows = result_payload.get("axes")
    if not isinstance(axes_rows, list):
        raise ValueError("PSR result missing axes rows")
    by_axis = {str(row.get("axis")): row for row in axes_rows}
    expected_set = {str(a) for a in expected_axes}
    if set(by_axis) != expected_set:
        raise ValueError(f"PSR axis coverage mismatch: expected={sorted(expected_set)} got={sorted(by_axis)}")
    for axis in sorted(expected_set):
        row = by_axis[axis]
        expected_ids = [str(x) for x in expected_item_ids_by_axis[axis]]
        n_total = len(expected_ids)
        n_dev = int(round(adj.DEV_FRACTION * n_total))
        n_dev = max(1, min(n_dev, n_total - 1))
        n_test = n_total - n_dev
        if int(row.get("k", -1)) != int(expected_k):
            raise ValueError(f"{axis}: k mismatch")
        if int(row.get("n_dev", -1)) != n_dev or int(row.get("n_test", -1)) != n_test:
            raise ValueError(f"{axis}: DEV/TEST count mismatch")
        dev_sel = row.get("dev_selection") or {}
        alpha = dev_sel.get("frozen_alpha")
        if alpha is None or float(alpha) not in {float(x) for x in adj.ALPHA_GRID}:
            raise ValueError(f"{axis}: frozen alpha missing or outside frozen grid")
        if len(row.get("per_item_prompt") or []) != n_test:
            raise ValueError(f"{axis}: incomplete prompt TEST coverage")
        if len(row.get("per_item_steer") or []) != n_test:
            raise ValueError(f"{axis}: incomplete steer TEST coverage")
        if len(row.get("per_item_diff") or []) != n_test:
            raise ValueError(f"{axis}: incomplete paired TEST coverage")
    provenance = result_payload.get("psr_provenance") or {}
    opt = provenance.get("psr_optimization") or {}
    if set(map(str, opt.keys())) != expected_set:
        raise ValueError("PSR optimization provenance axis mismatch")
    for axis in expected_set:
        row = opt[axis]
        if str(row.get("axis")) != axis:
            raise ValueError(f"{axis}: PSR optimization axis mismatch")
        evaluations_used = int(row.get("evaluations_used", 0))
        candidate_budget = int(row.get("candidate_budget", 0))
        if candidate_budget > 32:
            raise ValueError(f"{axis}: PSR candidate budget exceeds frozen cap")
        if evaluations_used > candidate_budget:
            raise ValueError(f"{axis}: PSR optimizer exceeded budget")
        if evaluations_used > 32:
            raise ValueError(f"{axis}: PSR optimizer exceeded frozen <=32 evaluations")
        candidate = row.get("candidate") or {}
        if float(candidate.get("alpha", -1.0)) not in {float(x) for x in adj.ALPHA_GRID}:
            raise ValueError(f"{axis}: PSR optimizer candidate alpha outside frozen grid")
        config = row.get("config") or {}
        if float(config.get("coherence_lambda", -1.0)) != 1.0:
            raise ValueError(f"{axis}: PSR coherence lambda must be frozen at 1.0")
