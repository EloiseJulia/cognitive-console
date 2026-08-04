"""E-0015 scale-corrected positive-control harness.

Extends the E-0014 positive-control pattern without changing the frozen C2b
adjudicator.  The only intervention-grid change is the preregistered raw-CAA
scale: beta * ||v_axis|| passed to the existing unit-direction hook as alpha_eff.
HF/GPU runs are owner-gated; the default synthetic backend is an offline smoke.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import NormalDist
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cognitive_console.activations.provider import HFActivationProvider, SyntheticActivationProvider
from cognitive_console.eval import c2b_tasks
from cognitive_console.experiments import adjudicate_c2b as adj
from cognitive_console.lineage import git_commit, utcnow
from cognitive_console.steering.extract import CAAResult, extract_caa
from cognitive_console.steering.generate import SteerConfig, SteeredHFBackend, SyntheticC2bTaskBackend, unit_vector
from scripts import run_c1_facade as c1
from scripts.run_c2b_adjudication import BackendOutcomeSampler, load_axis_items
from scripts import run_positive_control as e0014

EXPERIMENT_ID = "E-0015"
REFUSAL_AXIS = "refusal_positive_control"
METACOG_AXES: Tuple[str, ...] = ("deliberation", "skepticism", "uncertainty_awareness")
ALL_AXES: Tuple[str, ...] = (REFUSAL_AXIS, *METACOG_AXES)
DEFAULT_MODEL = "Qwen/Qwen2.5-7B-Instruct"
DEFAULT_OUT_DIR = _REPO / "results" / "E-0015-scale-corrected-positive-control"
BETA_GRID: Tuple[float, ...] = (0.125, 0.25, 0.5, 1.0, 2.0)
FROZEN_C2_LAYER_BY_AXIS: Dict[str, int] = {
    "deliberation": 20,
    "skepticism": 20,
    "uncertainty_awareness": 20,
}
FROZEN_C2_LAYER_SOURCE = "results/c2b_adjudication_hf_2026-07-24/c2b_adjudication_results.json"
SCOPE_GUARD_SENTENCE = (
    "E-0015 is a scale-corrected positive-control and headline-risk harness: "
    "the refusal target is non-metacognitive and tests instrument sensitivity, "
    "while the three metacognitive axes are a preregistered risk co-test; all "
    "artifacts remain valid_for_paper=false until a frozen GPU run and hostile "
    "results audit, and refusal success alone is not evidence of metacognitive "
    "controllability."
)
INTERPRETATION_MATRIX = [
    {"cell": "refusal_pass_meta_none", "interpretation": "proper scaling moves known non-metacognitive control but not metacognitive axes", "claim_action": "headline survives, scoped to this method"},
    {"cell": "refusal_pass_meta_any_pc2a", "interpretation": "properly scaled latent control moves at least one metacognitive endpoint", "claim_action": "headline overturned/reframed"},
    {"cell": "meta_pc3_pass", "interpretation": "scale-corrected latent control beats prompt on a metacognitive endpoint", "claim_action": "rewrite C2/RQ2 claim"},
    {"cell": "nothing_passes_coherence_ok", "interpretation": "scale correction did not rescue control", "claim_action": "report null; apparatus remains suspect"},
    {"cell": "coherence_collapse", "interpretation": "usable scale window may be empty", "claim_action": "report degeneration by beta; no retuning"},
    {"cell": "random_passes", "interpretation": "specificity failure", "claim_action": "E-0015 uninterpretable until audit"},
]


@dataclass
class ScaleDirectionBundle:
    axis: str
    vector: np.ndarray          # unnormalized mean(pos)-mean(neg)
    direction: np.ndarray       # unit vector used by the existing hook
    layer: int
    provenance: Dict[str, object]
    hook_backend: Optional[SteeredHFBackend] = None

    @property
    def vector_norm(self) -> float:
        return float(np.linalg.norm(np.asarray(self.vector, dtype=np.float64).ravel()))


@dataclass
class SharedHFHandles:
    """Single loaded HF model shared across extraction, hook-bites, and generation."""

    provider: HFActivationProvider
    hook_backend: SteeredHFBackend
    device: str
    dtype: str


def _vector_sha256(vec: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(vec, dtype=np.float64).ravel().tobytes()).hexdigest()


def build_shared_hf_handles(model_id: str, seed: int, out_dir: Path) -> SharedHFHandles:
    """Load Qwen once and share its handles with every E-0015 HF component."""
    from scripts import run_gpu_phase0 as p0

    device, dtype = p0._pick_device(), p0._pick_dtype()
    provider = HFActivationProvider(model_id, device=device, dtype=dtype, cache_dir=str(out_dir / "activations" / "cache"))
    model, tokenizer, config = provider.hf_handles()
    hook_backend = SteeredHFBackend(
        model_id,
        device=device,
        dtype=dtype,
        seed=seed,
        model=model,
        tokenizer=tokenizer,
        config=config,
    )
    return SharedHFHandles(provider=provider, hook_backend=hook_backend, device=device, dtype=dtype)


def _axis_pair_texts(axis: str, n_extraction: int, seed: int, *, frozen_c2_split: bool) -> Tuple[List[str], List[str], List[str], str]:
    pairs = c1.load_axis_pairs(axis)
    if frozen_c2_split:
        split = c1.make_split(list(pairs.pos.keys()), n_extraction=n_extraction, seed=seed)
        ids = list(split.extraction_ids)
    else:
        ids = list(pairs.pos.keys())[: int(n_extraction)]
    if len(ids) < int(n_extraction):
        raise ValueError(f"{axis}: requested {n_extraction} extraction pairs, only {len(ids)} available")
    return [pairs.pos[i] for i in ids], [pairs.neg[i] for i in ids], ids, pairs.file_hash


def _direction_provenance(axis: str, vector: np.ndarray, direction: np.ndarray, *, backend: str, model_id: str,
                          layer: int, n_extraction: int, pair_ids: Sequence[str], pair_file_hash: str,
                          derivation_function: str, selection: str, selected_layer_separation: Optional[float],
                          residual_norm_mean: Optional[float], extra: Optional[Dict[str, object]] = None) -> Dict[str, object]:
    norm = float(np.linalg.norm(vector))
    rows = beta_scale_rows(norm, residual_norm_mean=residual_norm_mean)
    prov: Dict[str, object] = {
        "backend": backend,
        "model_id": model_id,
        "axis": axis,
        "method": "caa_mean_difference_raw_magnitude_scale_corrected",
        "derivation_function": derivation_function,
        "layer": int(layer),
        "n_extraction_pairs": int(n_extraction),
        "extraction_pair_ids": list(pair_ids),
        "contrast_pairs_file_sha256": pair_file_hash,
        "vector_sha256": _vector_sha256(vector),
        "direction_sha256": _vector_sha256(direction),
        "vector_norm": norm,
        "direction_norm": float(np.linalg.norm(direction)),
        "hidden_dim": int(np.asarray(direction).size),
        "selection": selection,
        "selected_layer_separation": None if selected_layer_separation is None else float(selected_layer_separation),
        "beta_grid": list(BETA_GRID),
        "scale_rows": rows,
        "alpha_eff_grid": [r["alpha_eff"] for r in rows],
        "residual_norm_mean_at_layer": residual_norm_mean,
        "valid_for_paper": False,
    }
    if extra:
        prov.update(extra)
    return prov


def beta_scale_rows(vector_norm: float, *, residual_norm_mean: Optional[float]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for beta in BETA_GRID:
        alpha_eff = float(beta) * float(vector_norm)
        ratio = None if residual_norm_mean in (None, 0) else alpha_eff / float(residual_norm_mean)
        rows.append({
            "beta": float(beta),
            "vector_norm": float(vector_norm),
            "alpha_eff": alpha_eff,
            "alpha_eff_over_mean_residual_l2": ratio,
        })
    return rows


def alpha_grid_for_bundle(bundle: ScaleDirectionBundle) -> Tuple[float, ...]:
    return tuple(float(beta) * bundle.vector_norm for beta in BETA_GRID)


def beta_for_alpha(bundle: ScaleDirectionBundle, alpha: Optional[float]) -> Optional[float]:
    if alpha is None:
        return None
    norm = bundle.vector_norm
    if norm <= 0:
        return None
    return float(alpha) / norm


def _residual_norm_mean(backend: Optional[SteeredHFBackend], layer: int) -> Optional[float]:
    if backend is None:
        return None
    acts = backend.capture_residual_activations(e0014.HOOK_BITE_PROBES, layer, steer=None, batch_size=len(e0014.HOOK_BITE_PROBES))
    norms = np.linalg.norm(np.asarray(acts, dtype=np.float64), axis=1)
    return float(np.mean(norms))


def assert_real_not_smoke_scale_direction(bundle: ScaleDirectionBundle, *, provider_hidden_dim: int, backend: str) -> None:
    if backend != "hf":
        return
    arr = np.asarray(bundle.direction, dtype=np.float64).ravel()
    if arr.size != int(provider_hidden_dim):
        raise ValueError(f"real direction dim {arr.size} != provider hidden_dim {provider_hidden_dim}")
    if arr.size <= 8:
        raise ValueError("real hf direction has placeholder-sized hidden_dim <= 8")
    if abs(float(np.linalg.norm(arr)) - 1.0) > 1e-6:
        raise ValueError("real hf direction must be unit norm for the existing hook")
    if np.allclose(arr, arr[0]):
        raise ValueError("real direction is constant/ones-like placeholder")
    prov = bundle.provenance
    low = json.dumps(prov, sort_keys=True).lower()
    if any(tok in low for tok in ("synthetic", "random", "placeholder", "offline", "np.ones")):
        raise ValueError(f"real hf direction provenance contains banned smoke token: {prov}")
    if prov.get("method") != "caa_mean_difference_raw_magnitude_scale_corrected":
        raise ValueError(f"unexpected E-0015 direction method: {prov.get('method')!r}")
    if bundle.axis == REFUSAL_AXIS and prov.get("derivation_function") != "cognitive_console.steering.extract.extract_caa":
        raise ValueError("refusal hf direction was not derived through extract_caa")
    if bundle.axis == REFUSAL_AXIS and float(prov.get("selected_layer_separation", 0.0)) < 0.8:
        raise ValueError("real refusal CAA direction failed separation floor 0.8")
    if bundle.axis in METACOG_AXES and prov.get("selection") != "frozen_c2_direction_layer_reuse_no_reselection":
        raise ValueError("metacognitive hf direction must reuse the frozen C2 layer without reselection")
    required = ("vector_sha256", "direction_sha256", "contrast_pairs_file_sha256", "layer", "model_id", "extraction_pair_ids", "vector_norm")
    missing = [k for k in required if prov.get(k) in (None, "", [])]
    if missing:
        raise ValueError(f"real scale-corrected direction provenance missing fields: {missing}")
    if float(prov.get("vector_norm", 0.0)) <= 0.0:
        raise ValueError("real scale-corrected CAA vector has zero norm")


def assert_item_pool_for_axis(axis: str, items: Sequence[Dict[str, object]], *, backend: str) -> Dict[str, object]:
    if axis == REFUSAL_AXIS:
        info = e0014.assert_item_pool_disjoint_from_frozen80(items)
        if backend == "hf" and len(items) < 60:
            raise AssertionError(f"hf {EXPERIMENT_ID} refusal loaded only {len(items)} items; frozen N requires >=60")
        return info
    ids = [str(it.get("id", "")) for it in items]
    if len(set(ids)) != len(ids):
        raise AssertionError(f"{axis}: duplicate item ids")
    required_n = int(adj.N_ITEMS_BY_AXIS.get(axis, 60))
    if backend == "hf" and len(items) < required_n:
        raise AssertionError(f"hf {EXPERIMENT_ID} {axis} loaded only {len(items)} items; frozen N requires >={required_n}")
    return {"axis": axis, "item_count": len(ids), "unique_ids": True, "source": "frozen_c2b_loader"}


def _hook_bites_for_bundle(bundle: ScaleDirectionBundle) -> Dict[str, object]:
    if bundle.hook_backend is None:
        return {"applicable": False, "passed": None, "reason": "synthetic backend no-op"}
    by_beta: Dict[str, object] = {}
    failed: List[str] = []
    for beta, alpha in zip(BETA_GRID, alpha_grid_for_bundle(bundle)):
        check = e0014.check_hf_hook_bites(bundle.hook_backend, bundle.direction, bundle.layer, alpha=float(alpha))
        check["beta"] = float(beta)
        check["vector_norm"] = bundle.vector_norm
        check["alpha_eff"] = float(alpha)
        by_beta[str(float(beta))] = check
        if not check.get("passed"):
            failed.append(str(float(beta)))
    return {
        "applicable": True,
        "mode": "pre_generation_full_beta_grid_every_axis",
        "passed": not failed,
        "beta_grid": list(BETA_GRID),
        "alpha_eff_grid": list(alpha_grid_for_bundle(bundle)),
        "min_cosine_threshold": e0014.HOOK_BITE_MIN_COSINE,
        "max_relative_norm_error_threshold": e0014.HOOK_BITE_MAX_RELATIVE_NORM_ERROR,
        "rationale": e0014.HOOK_BITE_RATIONALE,
        "by_beta": by_beta,
        "failed_betas": failed,
    }


def record_upfront_hook_bites_all_axes(bundles: Dict[str, ScaleDirectionBundle], out_dir: Path) -> None:
    prov = {axis: dict(bundle.provenance) for axis, bundle in bundles.items()}
    failures: Dict[str, object] = {}
    for axis, bundle in bundles.items():
        check = _hook_bites_for_bundle(bundle)
        bundle.provenance["hook_bites_check"] = check
        prov[axis] = dict(bundle.provenance)
        if check.get("passed") is False:
            failures[axis] = check
    (out_dir / "direction_provenance.json").write_text(json.dumps(prov, indent=2), encoding="utf-8")
    if failures:
        raise AssertionError(f"HF steering hook-bites full beta grid failed before generation: {failures}")


def derive_refusal_direction(backend: str, model_id: str, n_extraction: int, seed: int, out_dir: Path,
                             shared_hf: Optional[SharedHFHandles] = None) -> ScaleDirectionBundle:
    pos, neg, pair_ids, pair_hash = _axis_pair_texts(REFUSAL_AXIS, n_extraction, seed, frozen_c2_split=False)
    if backend == "synthetic":
        provider = SyntheticActivationProvider(dim=64, layers=(1, 2, 3, 4), seed=seed, noise_scale=0.05)
        provider.plant_contrast(REFUSAL_AXIS, pos, neg, magnitude=3.0, layer_gain={1: 0.4, 2: 0.8, 3: 1.5, 4: 1.0})
        result = extract_caa(provider, REFUSAL_AXIS, pos, neg, layers=provider.available_layers())
        residual_mean = 25.0
        prov = _direction_provenance(
            REFUSAL_AXIS, result.vector, result.direction, backend="synthetic", model_id="synthetic-offline",
            layer=int(result.layer), n_extraction=n_extraction, pair_ids=pair_ids, pair_file_hash=pair_hash,
            derivation_function="synthetic_offline.extract_caa_with_planted_contrast", selection="separation",
            selected_layer_separation=float(result.per_layer[int(result.layer)].separation), residual_norm_mean=residual_mean,
        )
        prov["hook_bites_check"] = {"applicable": False, "passed": None, "reason": "synthetic backend no-op"}
        return ScaleDirectionBundle(REFUSAL_AXIS, result.vector, result.direction, int(result.layer), prov)

    if shared_hf is None:
        raise ValueError("hf E-0015 refusal derivation requires shared_hf handles")
    provider = shared_hf.provider
    result: CAAResult = extract_caa(provider, REFUSAL_AXIS, pos, neg, layers=[ell for ell in provider.available_layers() if ell >= 1])
    steered_backend = shared_hf.hook_backend
    residual_mean = _residual_norm_mean(steered_backend, int(result.layer))
    prov = _direction_provenance(
        REFUSAL_AXIS, result.vector, result.direction, backend="hf", model_id=model_id, layer=int(result.layer),
        n_extraction=n_extraction, pair_ids=pair_ids, pair_file_hash=pair_hash,
        derivation_function="cognitive_console.steering.extract.extract_caa", selection="separation",
        selected_layer_separation=float(result.per_layer[int(result.layer)].separation), residual_norm_mean=residual_mean,
        extra={"e0014_reuse": "same refusal CAA derivation path: layer selected by real contrast-pair separation"},
    )
    bundle = ScaleDirectionBundle(REFUSAL_AXIS, result.vector, result.direction, int(result.layer), prov, steered_backend)
    assert_real_not_smoke_scale_direction(bundle, provider_hidden_dim=provider.hidden_dim, backend="hf")
    return bundle


def derive_metacog_direction(axis: str, backend: str, model_id: str, n_extraction: int, seed: int, out_dir: Path,
                             shared_hf: Optional[SharedHFHandles] = None) -> ScaleDirectionBundle:
    layer = FROZEN_C2_LAYER_BY_AXIS[axis]
    pos, neg, pair_ids, pair_hash = _axis_pair_texts(axis, n_extraction, seed, frozen_c2_split=True)
    if backend == "synthetic":
        idx = METACOG_AXES.index(axis) + 1
        vector = np.arange(1, 65, dtype=np.float64) * (0.01 * idx)
        direction = unit_vector(vector)
        residual_mean = 25.0 + idx
        prov = _direction_provenance(
            axis, vector, direction, backend="synthetic", model_id="synthetic-offline", layer=layer,
            n_extraction=n_extraction, pair_ids=pair_ids, pair_file_hash=pair_hash,
            derivation_function="synthetic_offline.frozen_c2_direction_standin", selection="frozen_c2_layer_reuse",
            selected_layer_separation=None, residual_norm_mean=residual_mean,
            extra={"frozen_c2_reuse": {"source": FROZEN_C2_LAYER_SOURCE, "layer": layer, "same_contrast_pairs": True, "same_split_seed": int(seed), "direction_sha256": _vector_sha256(direction)}},
        )
        prov["hook_bites_check"] = {"applicable": False, "passed": None, "reason": "synthetic backend no-op"}
        return ScaleDirectionBundle(axis, vector, direction, layer, prov)

    if shared_hf is None:
        raise ValueError("hf E-0015 metacognitive derivation requires shared_hf handles")
    provider = shared_hf.provider
    result = extract_caa(provider, axis, pos, neg, layers=[layer])
    vector = np.asarray(result.vector, dtype=np.float64)
    direction = np.asarray(result.direction, dtype=np.float64)
    steered_backend = shared_hf.hook_backend
    residual_mean = _residual_norm_mean(steered_backend, layer)
    prov = _direction_provenance(
        axis, vector, direction, backend="hf", model_id=model_id, layer=layer, n_extraction=n_extraction,
        pair_ids=pair_ids, pair_file_hash=pair_hash,
        derivation_function="cognitive_console.steering.extract.extract_caa_at_single_frozen_c2_layer",
        selection="frozen_c2_direction_layer_reuse_no_reselection",
        selected_layer_separation=float(result.per_layer[int(layer)].separation),
        residual_norm_mean=residual_mean,
        extra={"frozen_c2_reuse": {"source": FROZEN_C2_LAYER_SOURCE, "layer": layer, "same_contrast_pairs": True, "same_derivation": "CAA mean(pos)-mean(neg) on extraction split", "same_split_seed": int(seed), "direction_sha256": _vector_sha256(direction)}},
    )
    bundle = ScaleDirectionBundle(axis, vector, direction, layer, prov, steered_backend)
    assert_real_not_smoke_scale_direction(bundle, provider_hidden_dim=provider.hidden_dim, backend="hf")
    return bundle


def load_items_for_axis(axis: str, use_fixture: bool, n_items: Optional[int]) -> List[Dict[str, object]]:
    if axis == REFUSAL_AXIS:
        return e0014._items(use_fixture, n_items)
    return load_axis_items(axis, use_fixture, n_items)


def build_spec(axis: str, prompt_set: str, bundle: ScaleDirectionBundle, *, use_fixture: bool, n_items: Optional[int], n_strong: int) -> adj.AxisAdjSpec:
    neutral = c1.load_neutral_prompts()[0]
    if prompt_set == "neutral":
        prompts = [("neutral-as-prompt", neutral)]
    else:
        strong = c1.load_strongest_prompts(axis)
        prompts = list(zip(strong.ids, strong.texts))[: int(n_strong)]
    return adj.AxisAdjSpec(
        axis=axis,
        items=load_items_for_axis(axis, use_fixture, n_items),
        strong_prompts=prompts,
        neutral_prompt=neutral,
        direction=np.asarray(bundle.direction, dtype=np.float64),
        layer=int(bundle.layer),
    )


def _make_sampler(axis: str, backend: str, model: str, items: Sequence[Dict[str, object]], *, max_new_tokens: int,
                  temperature: float, seed: int, batch_size: int, random_null: bool = False,
                  shared_hf_backend: Optional[SteeredHFBackend] = None):
    if backend == "synthetic":
        if axis == REFUSAL_AXIS:
            markers = ["refuse", "decline", "answer nothing", "do not answer"]
            gain = 0.0 if random_null else 0.10
            gen = SyntheticC2bTaskBackend(axis, items, instruction_markers=markers, prompt_gain=0.15, alpha_gain=gain, threshold=0.50)
        else:
            gain = 0.0 if random_null else 0.08
            gen = SyntheticC2bTaskBackend(axis, items, prompt_gain=0.40, alpha_gain=gain, threshold=0.50)
        return BackendOutcomeSampler(gen, max_new_tokens=max_new_tokens, do_sample=False, seed=seed)
    if shared_hf_backend is None:
        raise ValueError("hf E-0015 sampler requires the single shared SteeredHFBackend")
    return BackendOutcomeSampler(
        shared_hf_backend,
        max_new_tokens=max_new_tokens,
        do_sample=True,
        temperature=temperature,
        seed=seed,
        batch_size=batch_size,
    )


def _adjudicate_one(spec: adj.AxisAdjSpec, sampler, *, alpha_grid: Sequence[float], bootstrap_b: int, seed: int) -> adj.AxisAdjResult:
    return adj.adjudicate_axis(
        sampler, spec, k=adj.K_SAMPLES, alpha_grid=alpha_grid,
        bootstrap_b=int(bootstrap_b), ci_level=adj.BONFERRONI_CI_LEVEL,
        delta=adj.DELTA, coherence_max_ratio=adj.COHERENCE_MAX_RATIO,
        dev_fraction=adj.DEV_FRACTION, seed=int(seed), ctx=None,
    )


def _normal_mde(per_item_diff: Sequence[float], *, ci_level: float, delta: float, fallback_n: int) -> Dict[str, object]:
    arr = np.asarray(per_item_diff, dtype=np.float64)
    n = int(arr.size if arr.size else fallback_n)
    z = NormalDist().inv_cdf((1.0 + float(ci_level)) / 2.0)
    if arr.size >= 2:
        sd = float(np.std(arr, ddof=1))
    else:
        sd = 0.5
    # Binary endpoints with all-identical synthetic outcomes would imply zero
    # empirical SD; keep a conservative Bernoulli planning floor so null cells are
    # never presented as high-powered proof of no movement.
    sd_floor = 0.5
    half_width = float(z * max(sd, sd_floor) / math.sqrt(max(1, n)))
    return {
        "method": "normal_approx_bonferroni_ci_half_width_with_binary_sd_floor_0.5",
        "n_test": n,
        "ci_level": float(ci_level),
        "z": float(z),
        "sd_used": float(max(sd, sd_floor)),
        "ci_half_width_mde": half_width,
        "pass_margin_delta": float(delta),
        "minimum_detectable_effect": max(float(delta), half_width),
        "power_honesty_note": "Null cells must be reported with this MDE and are not proof of no movement.",
    }


def _augment_result(row: Dict[str, object], bundle: ScaleDirectionBundle) -> Dict[str, object]:
    out = dict(row)
    dev = dict(out.get("dev_selection") or {})
    selected_alpha = dev.get("frozen_alpha")
    selected_beta = beta_for_alpha(bundle, selected_alpha if selected_alpha is not None else None)
    dev["frozen_beta"] = selected_beta
    for grid_row in dev.get("alpha_grid", []) or []:
        a = grid_row.get("alpha")
        grid_row["beta"] = beta_for_alpha(bundle, a)
        grid_row["alpha_eff"] = a
        grid_row["vector_norm"] = bundle.vector_norm
    out["dev_selection"] = dev
    out["selected_scale"] = {
        "vector_norm": bundle.vector_norm,
        "beta": selected_beta,
        "alpha_eff": selected_alpha,
        "alpha_eff_over_mean_residual_l2": None if bundle.provenance.get("residual_norm_mean_at_layer") in (None, 0) or selected_alpha is None else float(selected_alpha) / float(bundle.provenance["residual_norm_mean_at_layer"]),
    }
    out["mde"] = _normal_mde(out.get("per_item_diff") or [], ci_level=float(out.get("ci_level", adj.BONFERRONI_CI_LEVEL)), delta=float(out.get("delta", adj.DELTA)), fallback_n=int(out.get("n_test", 1)))
    return out


def _condition(axis: str, condition: str, bundle: ScaleDirectionBundle, sampler, *, use_fixture: bool, n_items: Optional[int], n_strong: int, bootstrap_b: int, seed: int, random_direction: Optional[np.ndarray] = None) -> Dict[str, object]:
    prompt_set = "neutral" if condition == "PC-2a" else "strong"
    spec_bundle = bundle
    if random_direction is not None:
        spec_bundle = ScaleDirectionBundle(axis, bundle.vector, unit_vector(random_direction), bundle.layer, bundle.provenance, bundle.hook_backend)
    spec = build_spec(axis, prompt_set, spec_bundle, use_fixture=use_fixture, n_items=n_items, n_strong=n_strong)
    result = _adjudicate_one(spec, sampler, alpha_grid=alpha_grid_for_bundle(bundle), bootstrap_b=bootstrap_b, seed=seed)
    return _augment_result(result.to_row(), bundle)


def run(args) -> Dict[str, object]:
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.backend == "hf" and (args.use_fixture or args.n_items is not None):
        raise SystemExit("hf E-0015 must use real data and frozen N; --use-fixture/--n-items forbidden")
    if args.backend == "hf" and args.bootstrap_b < adj.BOOTSTRAP_B:
        raise SystemExit("hf E-0015 requires frozen bootstrap B=10000")
    if args.backend == "hf" and (int(args.seed) != 20260723 or int(args.n_metacog_extraction) != 28):
        raise SystemExit(
            "hf E-0015 metacognitive isolation requires seed=20260723 and "
            "n_metacog_extraction=28 to reproduce the frozen C2 split/direction"
        )

    shared_hf = build_shared_hf_handles(args.model, args.seed, out_dir) if args.backend == "hf" else None
    bundles: Dict[str, ScaleDirectionBundle] = {
        REFUSAL_AXIS: derive_refusal_direction(args.backend, args.model, args.n_refusal_extraction, args.seed, out_dir, shared_hf=shared_hf)
    }
    for axis in METACOG_AXES:
        bundles[axis] = derive_metacog_direction(axis, args.backend, args.model, args.n_metacog_extraction, args.seed, out_dir, shared_hf=shared_hf)

    item_pool_integrity: Dict[str, object] = {}
    split_integrity: Dict[str, object] = {}
    for axis, bundle in bundles.items():
        items = load_items_for_axis(axis, args.use_fixture, args.n_items)
        item_pool_integrity[axis] = assert_item_pool_for_axis(axis, items, backend=args.backend)
        split = adj.split_dev_test([str(it["id"]) for it in items], seed=args.seed)
        if set(split.dev_ids) & set(split.test_ids):
            raise AssertionError(f"{axis}: DEV/TEST split is not disjoint")
        split_integrity[axis] = {"dev_ids": split.dev_ids, "test_ids": split.test_ids, "disjoint": True}

    record_upfront_hook_bites_all_axes(bundles, out_dir)

    axes_payload: Dict[str, object] = {}
    rng = np.random.default_rng(args.seed + 99173)
    for axis, bundle in bundles.items():
        items = load_items_for_axis(axis, args.use_fixture, args.n_items)
        sampler = _make_sampler(
            axis, args.backend, args.model, items, max_new_tokens=args.max_new_tokens,
            temperature=args.temperature, seed=args.seed, batch_size=args.batch_size,
            shared_hf_backend=shared_hf.hook_backend if shared_hf is not None else None,
        )
        pc2a = _condition(axis, "PC-2a", bundle, sampler, use_fixture=args.use_fixture, n_items=args.n_items, n_strong=args.n_strong, bootstrap_b=args.bootstrap_b, seed=args.seed)
        pc3 = _condition(axis, "PC-3", bundle, sampler, use_fixture=args.use_fixture, n_items=args.n_items, n_strong=args.n_strong, bootstrap_b=args.bootstrap_b, seed=args.seed)
        random_direction = unit_vector(rng.standard_normal(np.asarray(bundle.direction).shape))
        random_sampler = _make_sampler(
            axis, args.backend, args.model, items, max_new_tokens=args.max_new_tokens,
            temperature=args.temperature, seed=args.seed, batch_size=args.batch_size,
            random_null=args.backend == "synthetic",
            shared_hf_backend=shared_hf.hook_backend if shared_hf is not None else None,
        )
        rand = _condition(axis, "RAND", bundle, random_sampler, use_fixture=args.use_fixture, n_items=args.n_items, n_strong=args.n_strong, bootstrap_b=args.bootstrap_b, seed=args.seed, random_direction=random_direction)
        axes_payload[axis] = {
            "axis": axis,
            "direction_sha256": bundle.provenance["direction_sha256"],
            "layer": bundle.layer,
            "vector_norm": bundle.vector_norm,
            "pc2a_steer_vs_neutral_baseline": pc2a,
            "pc3_steer_vs_dev_selected_best_of_16_prompt": pc3,
            "random_direction_negative_control": {
                "direction_kind": "random_unit_negative_control",
                "direction_sha256": _vector_sha256(random_direction),
                "same_beta_selection_protocol": True,
                "same_alpha_eff_grid": list(alpha_grid_for_bundle(bundle)),
                "expected_to_pass": False,
                "result": rand,
            },
        }

    frozen_params = adj.frozen_params_dict()
    payload = {
        "experiment_id": EXPERIMENT_ID,
        "valid_for_paper": False,
        "status": "synthetic_smoke" if args.backend == "synthetic" else "pre_gpu_hf_run",
        "generated_at": utcnow(),
        "code_commit": git_commit(),
        "backend": args.backend,
        "model": "synthetic-offline" if args.backend == "synthetic" else args.model,
        "scope_guard_sentence": SCOPE_GUARD_SENTENCE,
        "interpretation_matrix": INTERPRETATION_MATRIX,
        "beta_grid": list(BETA_GRID),
        "scale_definition": "alpha_eff(beta)=beta*||v_axis||; existing hook normalizes direction, equivalent to h -> h + beta*v_axis",
        "single_variable_isolation": {
            "metacognitive_axes": list(METACOG_AXES),
            "frozen_c2_layer_by_axis": FROZEN_C2_LAYER_BY_AXIS,
            "frozen_c2_layer_source": FROZEN_C2_LAYER_SOURCE,
            "only_beta_varies_for_metacognitive_axes": True,
            "hf_runtime_lock": {"seed": 20260723, "n_metacog_extraction": 28},
            "hash_compare_status": "not_available_in_committed_frozen_c2_artifact; runtime seed/n lock plus provenance records direction_sha256",
        },
        "hf_model_handle_sharing": {
            "enabled": bool(args.backend == "hf"),
            "from_pretrained_model_loads_by_design": 1 if args.backend == "hf" else 0,
            "shared_across": ["all_axis_extraction", "upfront_hook_bites", "pc2a_generation", "pc3_generation", "random_negative_control"],
        },
        "generation_identity": {
            "max_new_tokens": int(args.max_new_tokens), "temperature": float(args.temperature),
            "seed": int(args.seed), "k_samples": adj.K_SAMPLES, "batch_size": int(args.batch_size),
            "do_sample": bool(args.backend == "hf"),
        },
        "frozen_adjudicator_reuse": frozen_params,
        "direction_provenance": {axis: bundle.provenance for axis, bundle in bundles.items()},
        "item_pool_integrity": item_pool_integrity,
        "dev_test_split": split_integrity,
        "axes": axes_payload,
        "modifies_frozen_verdict": False,
    }
    (out_dir / "positive_control_scale_corrected_results.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (out_dir / "direction_provenance.json").write_text(json.dumps(payload["direction_provenance"], indent=2), encoding="utf-8")
    (out_dir / "run_manifest.json").write_text(json.dumps({
        "experiment_id": EXPERIMENT_ID, "valid_for_paper": False, "backend": args.backend,
        "model": payload["model"], "generated_at": payload["generated_at"],
        "scope_guard_sentence": SCOPE_GUARD_SENTENCE,
        "artifacts": {
            "results_json": str(out_dir / "positive_control_scale_corrected_results.json"),
            "direction_provenance_json": str(out_dir / "direction_provenance.json"),
        },
    }, indent=2), encoding="utf-8")
    return payload


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Run E-0015 scale-corrected positive-control harness")
    ap.add_argument("--backend", choices=["synthetic", "hf"], default="synthetic")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    ap.add_argument("--seed", type=int, default=20260723)
    ap.add_argument("--n-items", type=int, default=None, help="synthetic/debug cap only")
    ap.add_argument("--n-strong", type=int, default=16)
    ap.add_argument("--n-refusal-extraction", type=int, default=40)
    ap.add_argument("--n-metacog-extraction", type=int, default=28)
    ap.add_argument("--bootstrap-b", type=int, default=adj.BOOTSTRAP_B)
    ap.add_argument("--allow-underpowered", action="store_true")
    ap.add_argument("--max-new-tokens", type=int, default=64)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--use-fixture", action=argparse.BooleanOptionalAction, default=None)
    return ap


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.use_fixture is None:
        args.use_fixture = args.backend == "synthetic"
    if args.bootstrap_b < adj.BOOTSTRAP_B and not args.allow_underpowered:
        raise SystemExit("--bootstrap-b below frozen 10000 requires --allow-underpowered (synthetic smoke only)")
    payload = run(args)
    print(json.dumps({
        "experiment_id": payload["experiment_id"],
        "backend": payload["backend"],
        "axes": {
            axis: {
                "pc2a_passed": row["pc2a_steer_vs_neutral_baseline"]["passed"],
                "pc3_passed": row["pc3_steer_vs_dev_selected_best_of_16_prompt"]["passed"],
                "random_negative_passed": row["random_direction_negative_control"]["result"]["passed"],
                "selected_beta_pc2a": row["pc2a_steer_vs_neutral_baseline"]["selected_scale"]["beta"],
            }
            for axis, row in payload["axes"].items()
        },
        "out_dir": str(Path(args.out_dir).resolve()),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
