"""E-0014 positive-control runner for the frozen C2b adjudicator.

Runs refusal induction on harmless questions through the same frozen adjudicator
machinery used by C2b. The HF path derives a real CAA mean-difference direction
with HFActivationProvider + extract_caa and hard-fails on synthetic/random/
placeholder direction provenance. The synthetic backend is for offline smoke only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

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
from cognitive_console.steering.generate import SyntheticC2bTaskBackend
from scripts import run_c1_facade as c1
from scripts.run_c2b_adjudication import BackendOutcomeSampler, hf_sampler_factory

AXIS = "refusal_positive_control"
DEFAULT_MODEL = "Qwen/Qwen2.5-7B-Instruct"
DEFAULT_OUT_DIR = _REPO / "results" / "E-0014-positive-control"
SCOPE_GUARD_SENTENCE = (
    "This positive control tests the sensitivity of the measuring instrument on a "
    "non-metacognitive target chosen because activation steering is already known "
    "to move it; it is not evidence that deliberation, skepticism, or calibration "
    "are latently controllable, and a pass here does not weaken, qualify, or extend "
    "the scoped negative reported for naive CAA/ITI steering on the three "
    "metacognitive axes."
)


@dataclass
class DirectionBundle:
    direction: np.ndarray
    layer: int
    provenance: Dict[str, object]


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _vector_sha256(vec: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(vec, dtype=np.float64).ravel().tobytes()).hexdigest()


def _load_pair_texts(n_extraction: int) -> Tuple[List[str], List[str], List[str], str]:
    pairs = c1.load_axis_pairs(AXIS)
    ids = list(pairs.pos.keys())[: int(n_extraction)]
    if len(ids) < int(n_extraction):
        raise ValueError(f"{AXIS}: requested {n_extraction} extraction pairs, only {len(ids)} available")
    return [pairs.pos[i] for i in ids], [pairs.neg[i] for i in ids], ids, pairs.file_hash


def _direction_provenance(result: CAAResult, *, backend: str, model_id: str, n_extraction: int,
                          pair_ids: Sequence[str], pair_file_hash: str,
                          derivation_function: str) -> Dict[str, object]:
    return {
        "backend": backend,
        "model_id": model_id,
        "axis": AXIS,
        "method": "caa_mean_difference",
        "derivation_function": derivation_function,
        "layer": int(result.layer),
        "n_extraction_pairs": int(n_extraction),
        "extraction_pair_ids": list(pair_ids),
        "contrast_pairs_file_sha256": pair_file_hash,
        "direction_sha256": _vector_sha256(result.direction),
        "vector_norm": float(np.linalg.norm(result.vector)),
        "direction_norm": float(np.linalg.norm(result.direction)),
        "hidden_dim": int(np.asarray(result.direction).size),
        "selection": result.selection,
        "selected_layer_separation": float(result.per_layer[int(result.layer)].separation),
        "per_layer": {str(k): asdict(v) for k, v in sorted(result.per_layer.items())},
    }


def assert_real_not_smoke_direction(direction: np.ndarray, provenance: Dict[str, object], *,
                                    provider_hidden_dim: int, backend: str) -> None:
    """Hard-fail on HF when a direction is synthetic/random/placeholder/non-real."""
    if backend != "hf":
        return
    arr = np.asarray(direction, dtype=np.float64).ravel()
    if arr.size != int(provider_hidden_dim):
        raise ValueError(f"real direction dim {arr.size} != provider hidden_dim {provider_hidden_dim}")
    if arr.size <= 8:
        raise ValueError("real hf direction has placeholder-sized hidden_dim <= 8")
    norm = float(np.linalg.norm(arr))
    if not np.isfinite(norm) or abs(norm - 1.0) > 1e-6:
        raise ValueError(f"real direction must be unit norm; got {norm}")
    if np.allclose(arr, arr[0]):
        raise ValueError("real direction is constant/ones-like placeholder")
    low = json.dumps(provenance, sort_keys=True).lower()
    banned = ("synthetic", "random", "placeholder", "offline", "np.ones")
    if any(tok in low for tok in banned):
        raise ValueError(f"real hf direction provenance contains banned smoke token: {provenance}")
    if provenance.get("method") != "caa_mean_difference":
        raise ValueError(f"unexpected real direction method: {provenance.get('method')!r}")
    if provenance.get("derivation_function") != "cognitive_console.steering.extract.extract_caa":
        raise ValueError("hf direction was not derived through extract_caa")
    if float(provenance.get("selected_layer_separation", 0.0)) < 0.8:
        raise ValueError("real CAA direction failed separation floor 0.8")


def derive_direction(backend: str, model_id: str, n_extraction: int, seed: int,
                     out_dir: Path) -> DirectionBundle:
    pos, neg, pair_ids, pair_hash = _load_pair_texts(n_extraction)
    if backend == "synthetic":
        provider = SyntheticActivationProvider(dim=64, layers=(1, 2, 3, 4), seed=seed, noise_scale=0.05)
        provider.plant_contrast(AXIS, pos, neg, magnitude=3.0, layer_gain={1: 0.4, 2: 0.8, 3: 1.5, 4: 1.0})
        result = extract_caa(provider, AXIS, pos, neg, layers=provider.available_layers())
        prov = _direction_provenance(
            result, backend="synthetic", model_id="synthetic-offline", n_extraction=n_extraction,
            pair_ids=pair_ids, pair_file_hash=pair_hash,
            derivation_function="synthetic_offline.extract_caa_with_planted_contrast",
        )
        return DirectionBundle(result.direction, int(result.layer), prov)

    from scripts import run_gpu_phase0 as p0
    device, dtype = p0._pick_device(), p0._pick_dtype()
    provider = HFActivationProvider(model_id, device=device, dtype=dtype,
                                    cache_dir=str(out_dir / "activations" / "cache"))
    candidate_layers = [ell for ell in provider.available_layers() if ell >= 1]
    result = extract_caa(provider, AXIS, pos, neg, layers=candidate_layers)
    prov = _direction_provenance(
        result, backend="hf", model_id=model_id, n_extraction=n_extraction,
        pair_ids=pair_ids, pair_file_hash=pair_hash,
        derivation_function="cognitive_console.steering.extract.extract_caa",
    )
    assert_real_not_smoke_direction(result.direction, prov, provider_hidden_dim=provider.hidden_dim, backend="hf")
    return DirectionBundle(result.direction, int(result.layer), prov)


def _strong_prompts(n: int) -> List[Tuple[str, str]]:
    strong = c1.load_strongest_prompts(AXIS)
    return list(zip(strong.ids, strong.texts))[: int(n)]


def _items(use_fixture: bool, n_items: Optional[int]) -> List[Dict[str, object]]:
    task = c2b_tasks.load_c2b_task(AXIS, use_fixture=use_fixture)
    items = list(task.items)
    cap = n_items if n_items is not None else 60
    return items[: int(cap)]


def build_spec(prompt_set: str, direction: np.ndarray, layer: int, *, use_fixture: bool,
               n_items: Optional[int], n_strong: int) -> adj.AxisAdjSpec:
    neutral = c1.load_neutral_prompts()[0]
    prompts = [("neutral-as-prompt", neutral)] if prompt_set == "neutral" else _strong_prompts(n_strong)
    return adj.AxisAdjSpec(
        axis=AXIS,
        items=_items(use_fixture, n_items),
        strong_prompts=prompts,
        neutral_prompt=neutral,
        direction=np.asarray(direction, dtype=np.float64),
        layer=int(layer),
    )


def _make_sampler(backend: str, model: str, items: Sequence[Dict[str, object]], *,
                  max_new_tokens: int, temperature: float, seed: int, batch_size: int):
    if backend == "synthetic":
        gen = SyntheticC2bTaskBackend(
            AXIS, items, instruction_markers=["refuse", "decline", "answer nothing", "do not answer"],
            prompt_gain=0.15, alpha_gain=0.10, threshold=0.50,
        )
        return BackendOutcomeSampler(gen, max_new_tokens=max_new_tokens, do_sample=False, seed=seed)
    return hf_sampler_factory(model, max_new_tokens, temperature, seed, batch_size)(AXIS)


def _decomposition(result: adj.AxisAdjResult) -> Dict[str, object]:
    return {
        "steer_minus_prompt": {
            "point": float(result.mean_diff), "ci_lo": float(result.ci_lo), "ci_hi": float(result.ci_hi),
            "passed": bool(result.passed), "coherence_ok": bool(result.coherence_ok),
        },
        "steer_minus_baseline": "computed by PC-2a neutral-prompt comparator result",
        "baseline_minus_prompt": "derive from PC-2a/PC-3 paired manifests if needed; frozen verdict uses steer_minus_prompt only",
    }


def _adjudicate_one(spec: adj.AxisAdjSpec, sampler, *, bootstrap_b: int, seed: int) -> adj.AxisAdjResult:
    return adj.adjudicate_axis(
        sampler, spec, k=adj.K_SAMPLES, alpha_grid=adj.ALPHA_GRID,
        bootstrap_b=int(bootstrap_b), ci_level=adj.BONFERRONI_CI_LEVEL,
        delta=adj.DELTA, coherence_max_ratio=adj.COHERENCE_MAX_RATIO,
        dev_fraction=adj.DEV_FRACTION, seed=int(seed), ctx=None,
    )


def run(args) -> Dict[str, object]:
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.backend == "hf" and (args.use_fixture or args.n_items is not None):
        raise SystemExit("hf E-0014 must use real data and frozen N=60; --use-fixture/--n-items forbidden")
    if args.backend == "hf" and args.bootstrap_b < adj.BOOTSTRAP_B:
        raise SystemExit("hf E-0014 requires frozen bootstrap B=10000")

    bundle = derive_direction(args.backend, args.model, args.n_extraction, args.seed, out_dir)
    spec_pc2a = build_spec("neutral", bundle.direction, bundle.layer, use_fixture=args.use_fixture,
                           n_items=args.n_items, n_strong=args.n_strong)
    spec_pc3 = build_spec("strong", bundle.direction, bundle.layer, use_fixture=args.use_fixture,
                          n_items=args.n_items, n_strong=args.n_strong)
    ids_dev_test = adj.split_dev_test([str(it["id"]) for it in spec_pc3.items], seed=args.seed)
    if set(ids_dev_test.dev_ids) & set(ids_dev_test.test_ids):
        raise AssertionError("DEV/TEST split is not disjoint")

    sampler = _make_sampler(args.backend, args.model, spec_pc3.items, max_new_tokens=args.max_new_tokens,
                            temperature=args.temperature, seed=args.seed, batch_size=args.batch_size)
    pc2a = _adjudicate_one(spec_pc2a, sampler, bootstrap_b=args.bootstrap_b, seed=args.seed)
    pc3 = _adjudicate_one(spec_pc3, sampler, bootstrap_b=args.bootstrap_b, seed=args.seed)

    rng = np.random.default_rng(args.seed + 99173)
    random_direction = rng.standard_normal(np.asarray(bundle.direction).shape)
    random_direction = random_direction / float(np.linalg.norm(random_direction))
    spec_random = build_spec("strong", random_direction, bundle.layer, use_fixture=args.use_fixture,
                             n_items=args.n_items, n_strong=args.n_strong)
    if args.backend == "synthetic":
        # Offline smoke cannot make the generic SyntheticC2bTaskBackend inspect
        # vector geometry, so use an explicit null-effect sampler for the matched
        # random-direction negative control. The HF path below uses the actual
        # random direction through the real steering hook.
        null_gen = SyntheticC2bTaskBackend(
            AXIS, spec_pc3.items, instruction_markers=["refuse", "decline", "answer nothing", "do not answer"],
            prompt_gain=0.15, alpha_gain=0.0, threshold=0.50,
        )
        random_sampler = BackendOutcomeSampler(null_gen, max_new_tokens=args.max_new_tokens, do_sample=False, seed=args.seed)
    else:
        random_sampler = sampler
    random_result = _adjudicate_one(spec_random, random_sampler, bootstrap_b=args.bootstrap_b, seed=args.seed)

    frozen_params = adj.frozen_params_dict()
    frozen_params["n_items_by_axis"] = dict(frozen_params.get("n_items_by_axis", {}))
    frozen_params["n_items_by_axis"][AXIS] = 60
    payload = {
        "experiment_id": "E-0014",
        "valid_for_paper": False,
        "generated_at": utcnow(),
        "code_commit": git_commit(),
        "backend": args.backend,
        "model": "synthetic-offline" if args.backend == "synthetic" else args.model,
        "axis": AXIS,
        "scope_guard_sentence": SCOPE_GUARD_SENTENCE,
        "generation_identity": {
            "max_new_tokens": int(args.max_new_tokens), "temperature": float(args.temperature),
            "seed": int(args.seed), "k_samples": adj.K_SAMPLES, "batch_size": int(args.batch_size),
            "do_sample": bool(args.backend == "hf"),
        },
        "frozen_adjudicator_reuse": frozen_params,
        "direction_provenance": bundle.provenance,
        "dev_test_split": {"dev_ids": ids_dev_test.dev_ids, "test_ids": ids_dev_test.test_ids, "disjoint": True},
        "pc2a_steer_vs_neutral_baseline": pc2a.to_row(),
        "pc3_steer_vs_best_of_n_prompt": pc3.to_row(),
        "random_direction_negative_control": {
            "direction_kind": "random_unit_negative_control",
            "direction_sha256": _vector_sha256(random_direction),
            "expected_to_pass": False,
            "result": random_result.to_row(),
        },
        "decomposition": {"pc2a": _decomposition(pc2a), "pc3": _decomposition(pc3)},
        "modifies_frozen_verdict": False,
    }
    (out_dir / "positive_control_results.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (out_dir / "direction_provenance.json").write_text(json.dumps(bundle.provenance, indent=2), encoding="utf-8")
    (out_dir / "run_manifest.json").write_text(json.dumps({
        "experiment_id": "E-0014", "valid_for_paper": False, "backend": args.backend,
        "model": payload["model"], "generated_at": payload["generated_at"],
        "scope_guard_sentence": SCOPE_GUARD_SENTENCE,
        "artifacts": {"positive_control_results_json": str(out_dir / "positive_control_results.json"),
                      "direction_provenance_json": str(out_dir / "direction_provenance.json")},
    }, indent=2), encoding="utf-8")
    return payload


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Run E-0014 positive-control refusal induction")
    ap.add_argument("--backend", choices=["synthetic", "hf"], default="synthetic")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    ap.add_argument("--seed", type=int, default=20260723)
    ap.add_argument("--n-items", type=int, default=None, help="synthetic/debug cap only")
    ap.add_argument("--n-strong", type=int, default=16)
    ap.add_argument("--n-extraction", type=int, default=40)
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
        "pc2a_passed": payload["pc2a_steer_vs_neutral_baseline"]["passed"],
        "pc3_passed": payload["pc3_steer_vs_best_of_n_prompt"]["passed"],
        "random_negative_passed": payload["random_direction_negative_control"]["result"]["passed"],
        "out_dir": str(Path(args.out_dir).resolve()),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
