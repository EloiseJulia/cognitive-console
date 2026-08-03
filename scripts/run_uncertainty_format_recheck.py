"""E-0013 uncertainty format-compliance recheck.

This is an additive robustness check for the frozen C2b uncertainty axis. It
reuses the E-0006 DEV-selected prompt/alpha/layer configurations and re-runs the
uncertainty items while capturing raw generations, confidence-parse success, the
frozen 0.5 imputation path, and a separate format-compliant-only reanalysis.
It does not alter the frozen C2b adjudicator or verdict.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cognitive_console.eval import c2b_tasks
from cognitive_console.eval import scorers
from cognitive_console.experiments import adjudicate_c2b as adj
from cognitive_console.experiments.adjudicate_c2b import BackendOutcomeSampler
from cognitive_console.lineage import git_commit, utcnow
from cognitive_console.steering.generate import SteerConfig, SyntheticC2bTaskBackend
from cognitive_console.steering.iti import extract_iti, sigma_scaled_alpha
from cognitive_console.steering.extract import min_layer_for_depth
from scripts import run_c1_facade as c1
from scripts import run_gpu_phase0 as p0
from scripts import run_arm_matrix as arm

AXIS = "uncertainty_awareness"
EXPERIMENT_ID = "E-0013"
CONDITIONS = ("prompt", "steer", "baseline")
DEFAULT_OUT_DIR = _REPO / "results" / "E-0013-uncertainty-recheck"
DEFAULT_FROZEN_ROOT = _REPO / "results" / "arm_full"
DEFAULT_MAX_NEW_TOKENS = 64
DEFAULT_TEMPERATURE = 0.7
DEFAULT_SEED = 20260723
DEFAULT_N_EXTRACTION = 28


@dataclass(frozen=True)
class FrozenCellConfig:
    cell_key: str
    method: str
    model_label: str
    model_id: str
    layer: int
    frozen_alpha: float
    best_prompt_id: str
    best_prompt_text: str
    neutral_prompt: str
    sigma: float
    source_result_file: str
    source_config_fingerprint: str
    source_mean_diff: float


def _sha256_text(text: str) -> str:
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest()


def _rel(path: Path) -> str:
    p = Path(path).resolve()
    try:
        return str(p.relative_to(_REPO)).replace("\\", "/")
    except ValueError:
        return str(p).replace("\\", "/")


def _cell_key(method: str, model_label: str) -> str:
    return f"{method}__{model_label}"


def _axis_rows(payload: Dict) -> List[Dict]:
    rows = payload.get("axes")
    if rows is None:
        rows = payload.get("axis_results")
    if not isinstance(rows, list):
        raise ValueError("frozen result lacks axes/axis_results list")
    return rows


def load_frozen_cell_config(frozen_root: Path, method: str, model_label: str) -> FrozenCellConfig:
    cell_key = _cell_key(method, model_label)
    path = Path(frozen_root) / f"cell_{cell_key}" / "c2b_adjudication_results.json"
    if not path.exists():
        raise FileNotFoundError(f"missing frozen E-0006 cell artifact: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    axis_rows = [r for r in _axis_rows(payload) if r.get("axis") == AXIS]
    if len(axis_rows) != 1:
        raise ValueError(f"{path}: expected exactly one {AXIS} row, got {len(axis_rows)}")
    row = axis_rows[0]
    dev = dict(row.get("dev_selection") or {})
    frozen_params = dict(payload.get("frozen_params") or {})
    if int(frozen_params.get("k_samples", adj.K_SAMPLES)) != adj.K_SAMPLES:
        raise ValueError(f"{path}: frozen k_samples mismatch: {frozen_params.get('k_samples')}")
    if str(payload.get("backend")) != "hf":
        raise ValueError(f"{path}: expected frozen hf result, got backend={payload.get('backend')!r}")
    if str(payload.get("steering_method")) != method:
        raise ValueError(f"{path}: method mismatch")

    neutral_prompt = c1.load_neutral_prompts()[0]
    c1_info = dict((payload.get("c1_layer_info") or {}).get(AXIS) or {})
    sigma = float(c1_info.get("sigma", (payload.get("alpha_scale_by_axis") or {}).get(AXIS, 1.0)))
    return FrozenCellConfig(
        cell_key=cell_key,
        method=method,
        model_label=model_label,
        model_id=str(payload.get("model") or ""),
        layer=int(row["layer"]),
        frozen_alpha=float(dev["frozen_alpha"]),
        best_prompt_id=str(dev["best_prompt_id"]),
        best_prompt_text=str(dev["best_prompt_text"]),
        neutral_prompt=str(neutral_prompt),
        sigma=sigma,
        source_result_file=_rel(path),
        source_config_fingerprint=str(payload.get("config_fingerprint", "")),
        source_mean_diff=float(row.get("mean_diff", math.nan)),
    )


def load_uncertainty_items(*, use_fixture: bool, n_items: Optional[int]) -> List[Dict]:
    if use_fixture:
        task = c2b_tasks.load_c2b_task(AXIS, use_fixture=True)
        items = list(task.items)
    else:
        items = c2b_tasks.load_uncertainty_set()
    cap = n_items if n_items is not None else adj.N_ITEMS_BY_AXIS[AXIS]
    return list(items)[: int(cap)]


def split_items(items: Sequence[Dict], seed: int) -> Dict[str, List[Dict]]:
    by_id = {str(it["id"]): it for it in items}
    split = adj.split_dev_test(list(by_id.keys()), dev_fraction=adj.DEV_FRACTION, seed=seed)
    return {
        "dev": [by_id[i] for i in split.dev_ids],
        "test": [by_id[i] for i in split.test_ids],
    }


def score_uncertainty_record(text: str, item: Dict) -> Dict[str, object]:
    parsed_conf = scorers.parse_confidence(text)
    format_compliant = parsed_conf is not None
    imputed_conf = float(parsed_conf) if parsed_conf is not None else 0.5
    correct = int(scorers.item_is_correct(item, text))
    return {
        "parse_confidence": parsed_conf,
        "format_compliant": bool(format_compliant),
        "item_is_correct": correct,
        "imputed_confidence": imputed_conf,
        "per_item_1minus_brier": scorers.per_item_brier(correct, imputed_conf),
    }


def _condition_instruction_and_alpha(cfg: FrozenCellConfig, condition: str) -> Tuple[str, float, float]:
    if condition == "prompt":
        return cfg.best_prompt_text, 0.0, 0.0
    if condition == "baseline":
        return cfg.neutral_prompt, 0.0, 0.0
    if condition == "steer":
        effective = sigma_scaled_alpha(cfg.frozen_alpha, cfg.sigma) if cfg.method == "iti" else cfg.frozen_alpha
        return cfg.neutral_prompt, cfg.frozen_alpha, effective
    raise ValueError(f"unknown condition {condition!r}")


def _call_seed(base_seed: int, item: Dict, effective_alpha: float, sample_index: int) -> int:
    sampler = BackendOutcomeSampler(SyntheticC2bTaskBackend(AXIS, [item]), seed=base_seed)
    return sampler._call_seed(AXIS, item, effective_alpha, sample_index)


def _truncate_raw(text: str, max_chars: int) -> Tuple[str, bool]:
    text = str(text)
    if max_chars <= 0 or len(text) <= max_chars:
        return text, False
    suffix = " ...[truncated]"
    return text[: max(0, max_chars - len(suffix))] + suffix, True


def _derive_hf_direction(cfg: FrozenCellConfig, model_id: str, out_dir: Path,
                         n_extraction: int, seed: int) -> Tuple[np.ndarray, Dict[str, object]]:
    from cognitive_console.activations.provider import HFActivationProvider

    device, dtype = p0._pick_device(), p0._pick_dtype()
    provider = HFActivationProvider(
        model_id,
        device=device,
        dtype=dtype,
        cache_dir=str(out_dir / "activations" / "cache"),
    )
    if cfg.method == "caa":
        direction = p0._extract_direction(provider, AXIS, cfg.layer, n_extraction, seed)
        return direction, {"direction_source": "caa_mean_difference_at_frozen_layer"}

    pairs = c1.load_axis_pairs(AXIS)
    split = c1.make_split(list(pairs.pos.keys()), n_extraction=n_extraction, seed=seed)
    ext_pos = [pairs.pos[p] for p in split.extraction_ids]
    ext_neg = [pairs.neg[p] for p in split.extraction_ids]
    candidate_layers = [ell for ell in provider.available_layers() if ell >= 1]
    iti = extract_iti(
        provider,
        axis=AXIS,
        pos_texts=ext_pos,
        neg_texts=ext_neg,
        layers=candidate_layers,
        selection="nondegenerate",
        neutral_texts=c1.load_neutral_prompts(),
        min_layer=min_layer_for_depth(max(candidate_layers), min_depth_frac=0.2),
        min_depth_frac=0.2,
        n_null=2000,
        null_seed=seed,
    )
    if int(iti.layer) != int(cfg.layer):
        raise RuntimeError(
            f"{cfg.cell_key}: rederived ITI layer {iti.layer} != frozen layer {cfg.layer}; "
            "do not run E-0013 with a non-matching direction."
        )
    if not math.isclose(float(iti.sigma), float(cfg.sigma), rel_tol=1e-6, abs_tol=1e-8):
        raise RuntimeError(
            f"{cfg.cell_key}: rederived ITI sigma {iti.sigma} != frozen sigma {cfg.sigma}; "
            "do not run E-0013 with a non-matching direction."
        )
    return iti.direction, {
        "direction_source": "iti_probe_direction_rederived_by_frozen_c2_path",
        "rederived_sigma": float(iti.sigma),
        "rederived_probe_norm": float(np.linalg.norm(iti.vector)),
    }


def _make_backend(backend: str, model_id: str, items: Sequence[Dict], seed: int):
    if backend == "synthetic":
        return SyntheticC2bTaskBackend(AXIS, items, prompt_gain=0.4, alpha_gain=0.1, threshold=0.5)
    from cognitive_console.steering.generate import SteeredHFBackend

    return SteeredHFBackend(model_id, device=p0._pick_device(), dtype=p0._pick_dtype(), seed=seed)


def generate_cell_samples(cfg: FrozenCellConfig, *, backend_name: str, model_id: str,
                          items_by_split: Dict[str, List[Dict]], splits: Sequence[str],
                          out_dir: Path, max_new_tokens: int, temperature: float,
                          seed: int, batch_size: int, raw_text_max_chars: int,
                          n_extraction: int) -> Tuple[List[Dict], Dict[str, object]]:
    all_items = [it for sp in splits for it in items_by_split[sp]]
    backend = _make_backend(backend_name, model_id, all_items, seed)
    if backend_name == "synthetic":
        direction = np.ones(8, dtype=np.float64)
        direction_meta = {"direction_source": "synthetic_offline_placeholder"}
    else:
        direction, direction_meta = _derive_hf_direction(cfg, model_id, out_dir, n_extraction, seed)

    records: List[Dict] = []
    for split_name in splits:
        for condition in CONDITIONS:
            instruction, requested_alpha, effective_alpha = _condition_instruction_and_alpha(cfg, condition)
            steer = SteerConfig(direction=direction, alpha=effective_alpha, layer=cfg.layer)
            pending: List[Tuple[Dict, int, int, str]] = []
            for item in items_by_split[split_name]:
                prompt_text = adj.format_task_input(AXIS, instruction, item)
                for sample_index in range(adj.K_SAMPLES):
                    sample_seed = _call_seed(seed, item, effective_alpha, sample_index)
                    pending.append((item, sample_index, sample_seed, prompt_text))

            for start in range(0, len(pending), max(1, int(batch_size))):
                chunk = pending[start:start + max(1, int(batch_size))]
                prompts = [p for _, _, _, p in chunk]
                seeds = [s for _, _, s, _ in chunk]
                if hasattr(backend, "generate_batch"):
                    texts = backend.generate_batch(
                        prompts,
                        steer,
                        max_new_tokens=max_new_tokens,
                        seeds=seeds,
                        do_sample=(backend_name == "hf"),
                        temperature=temperature,
                    )
                else:
                    texts = []
                    for _, _, sample_seed, prompt in chunk:
                        try:
                            text = backend.generate(
                                prompt,
                                steer,
                                max_new_tokens=max_new_tokens,
                                do_sample=(backend_name == "hf"),
                                temperature=temperature,
                                seed=sample_seed,
                            )
                        except TypeError:
                            text = backend.generate(prompt, steer, max_new_tokens=max_new_tokens)
                        texts.append(text)
                for (item, sample_index, sample_seed, prompt_text), raw in zip(chunk, texts):
                    raw_payload, raw_truncated = _truncate_raw(str(raw), raw_text_max_chars)
                    diag = score_uncertainty_record(str(raw), item)
                    records.append({
                        "experiment_id": EXPERIMENT_ID,
                        "axis": AXIS,
                        "cell": cfg.cell_key,
                        "method": cfg.method,
                        "model_label": cfg.model_label,
                        "model_id": model_id,
                        "split": split_name,
                        "condition": condition,
                        "item_id": str(item.get("id")),
                        "sample_index": int(sample_index),
                        "sample_seed": int(sample_seed),
                        "layer": int(cfg.layer),
                        "requested_alpha": float(requested_alpha),
                        "effective_alpha": float(effective_alpha),
                        "best_prompt_id": cfg.best_prompt_id if condition == "prompt" else None,
                        "instruction_sha256": _sha256_text(instruction),
                        "prompt_text_sha256": _sha256_text(prompt_text),
                        "raw_text": raw_payload,
                        "raw_text_sha256": _sha256_text(str(raw)),
                        "raw_text_truncated": bool(raw_truncated),
                        "synthetic_proxy": bool(backend_name == "synthetic"),
                        **diag,
                    })
    meta = {
        "direction": direction_meta,
        "n_records": len(records),
        "splits": list(splits),
    }
    return records, meta


def _mean_by_item(records: Sequence[Dict], value_field: str = "per_item_1minus_brier") -> Dict[str, float]:
    grouped: Dict[str, List[float]] = {}
    for r in records:
        grouped.setdefault(str(r["item_id"]), []).append(float(r[value_field]))
    return {item_id: float(np.mean(vals)) for item_id, vals in grouped.items()}


def _paired_delta(
    records: Sequence[Dict], a: str, b: str, value_field: str = "per_item_1minus_brier"
) -> Tuple[float, List[float]]:
    by_cond = {
        a: _mean_by_item([r for r in records if r["condition"] == a], value_field=value_field),
        b: _mean_by_item([r for r in records if r["condition"] == b], value_field=value_field),
    }
    ids = sorted(set(by_cond[a]) & set(by_cond[b]))
    diffs = [by_cond[a][i] - by_cond[b][i] for i in ids]
    return (float(np.mean(diffs)) if diffs else math.nan), diffs


def _ci_from_diffs(diffs: Sequence[float], bootstrap_b: int, seed: int) -> Dict[str, object]:
    if not diffs:
        return {"point": math.nan, "ci_lo": math.nan, "ci_hi": math.nan, "n_items": 0}
    ci = adj.cluster_bootstrap_ci(np.asarray(diffs, dtype=float), b=bootstrap_b,
                                  ci_level=0.95, seed=seed, cluster=True)
    return {
        "point": ci.point,
        "ci_lo": ci.ci_lo,
        "ci_hi": ci.ci_hi,
        "ci_level": ci.ci_level,
        "bootstrap_b": int(bootstrap_b),
        "n_items": len(diffs),
    }


def _compliant_pair_diffs(records: Sequence[Dict], a: str, b: str) -> Tuple[List[float], int]:
    keyed: Dict[Tuple[str, int], Dict[str, Dict]] = {}
    for r in records:
        if r["condition"] not in {a, b}:
            continue
        key = (str(r["item_id"]), int(r["sample_index"]))
        keyed.setdefault(key, {})[str(r["condition"])] = r
    by_item: Dict[str, List[float]] = {}
    n_pairs = 0
    for (item_id, _sample_index), pair in keyed.items():
        if a not in pair or b not in pair:
            continue
        if not (pair[a]["format_compliant"] and pair[b]["format_compliant"]):
            continue
        n_pairs += 1
        by_item.setdefault(item_id, []).append(
            float(pair[a]["per_item_1minus_brier"]) - float(pair[b]["per_item_1minus_brier"])
        )
    return [float(np.mean(vals)) for _, vals in sorted(by_item.items())], n_pairs


def _score_with_bound(record: Dict, *, dropped_score: float) -> float:
    if bool(record["format_compliant"]):
        return float(record["per_item_1minus_brier"])
    return float(dropped_score)


def _worst_case_bounds(records: Sequence[Dict]) -> Dict[str, object]:
    rows = []
    for steer_drop_score, prompt_drop_score, label in [
        (0.0, 1.0, "least_favorable_to_steer"),
        (1.0, 0.0, "most_favorable_to_steer"),
    ]:
        adjusted = []
        for r in records:
            if r["condition"] not in {"steer", "prompt"}:
                continue
            rr = dict(r)
            rr["bounded_score"] = _score_with_bound(
                r,
                dropped_score=steer_drop_score if r["condition"] == "steer" else prompt_drop_score,
            )
            adjusted.append(rr)
        delta, diffs = _paired_delta(adjusted, "steer", "prompt", value_field="bounded_score")
        rows.append({"variant": label, "delta": delta, "n_items": len(diffs)})
    return {"bounds": rows}


def reanalyse(records: Sequence[Dict], *, bootstrap_b: int, seed: int) -> Dict[str, object]:
    by_cell: Dict[str, Dict[str, object]] = {}
    for cell in sorted({str(r["cell"]) for r in records}):
        cell_records = [r for r in records if str(r["cell"]) == cell and str(r["split"]) == "test"]
        cond_rows: Dict[str, Dict[str, object]] = {}
        for cond in CONDITIONS:
            rs = [r for r in cell_records if r["condition"] == cond]
            compliant = sum(1 for r in rs if bool(r["format_compliant"]))
            cond_rows[cond] = {
                "n_samples": len(rs),
                "n_format_compliant": compliant,
                "format_compliance_rate": compliant / len(rs) if rs else math.nan,
                "n_format_dropped": len(rs) - compliant,
                "format_dropped_rate": (len(rs) - compliant) / len(rs) if rs else math.nan,
                "mean_frozen_imputed_1minus_brier": (
                    float(np.mean([float(r["per_item_1minus_brier"]) for r in rs])) if rs else math.nan
                ),
            }
        all_delta, all_diffs = _paired_delta(cell_records, "steer", "prompt")
        compliant_diffs, n_compliant_pairs = _compliant_pair_diffs(cell_records, "steer", "prompt")
        by_cell[cell] = {
            "conditions": cond_rows,
            "frozen_uncertainty_delta_steer_minus_prompt_as_run_imputed": {
                "point": all_delta,
                "n_items": len(all_diffs),
            },
            "format_compliant_only_delta_steer_minus_prompt": {
                **_ci_from_diffs(compliant_diffs, bootstrap_b, seed),
                "n_compliant_sample_pairs": n_compliant_pairs,
                "restriction": "paired item/sample rows where both steer and prompt parsed confidence",
            },
            "sensitivity": {
                "drop_imputed": {
                    **_ci_from_diffs(compliant_diffs, bootstrap_b, seed),
                    "equivalent_to": "format_compliant_only_delta_steer_minus_prompt",
                },
                "worst_case_imputation_bounds": _worst_case_bounds(cell_records),
            },
        }
    return {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utcnow(),
        "headline_questions": {
            "does_harm_survive_format_compliant_only": (
                "inspect each cell's format_compliant_only_delta_steer_minus_prompt CI"
            ),
            "is_format_compliance_materially_different": (
                "compare condition format_compliance_rate for steer vs prompt/baseline"
            ),
        },
        "test_split_only": by_cell,
    }


def _write_jsonl(path: Path, records: Iterable[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _write_json(path: Path, payload: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _model_identity_key(model_ref: str) -> str:
    parts = [p for p in str(model_ref).strip().replace(os.sep, "/").replace("\\", "/").split("/") if p]
    return (parts[-1] if parts else str(model_ref)).strip().lower()


def _looks_like_local_path(model_ref: str) -> bool:
    ref = str(model_ref).strip()
    return (
        ref.startswith(("/", "\\", "./", ".\\", "../", "..\\"))
        or (len(ref) >= 3 and ref[1] == ":" and ref[2] in {"/", "\\"})
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="E-0013 uncertainty format-compliance recheck")
    ap.add_argument("--backend", choices=["synthetic", "hf"], default="synthetic")
    ap.add_argument("--frozen-root", default=str(DEFAULT_FROZEN_ROOT))
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    ap.add_argument("--qwen-model", default=None,
                    help="override Qwen model path/id; default reuses frozen cell artifact model")
    ap.add_argument("--llama-model", default=None,
                    help="override Llama model path/id; default reuses frozen cell artifact model")
    ap.add_argument("--cells", nargs="*", default=sorted(arm.FROZEN_CELL_KEYS))
    ap.add_argument("--splits", nargs="*", choices=["dev", "test"], default=["dev", "test"])
    ap.add_argument("--n-items", type=int, default=None, help="synthetic/debug cap only")
    ap.add_argument("--n-extraction", type=int, default=DEFAULT_N_EXTRACTION)
    ap.add_argument("--bootstrap-b", type=int, default=adj.BOOTSTRAP_B)
    ap.add_argument("--allow-underpowered", action="store_true")
    ap.add_argument("--max-new-tokens", type=int, default=DEFAULT_MAX_NEW_TOKENS)
    ap.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--raw-text-max-chars", type=int, default=8000)
    return ap


def _validate_generation_identity(
    args, frozen_cell: Optional[FrozenCellConfig] = None, requested_model: Optional[str] = None
) -> Optional[str]:
    expected = {
        "--max-new-tokens": (args.max_new_tokens, DEFAULT_MAX_NEW_TOKENS),
        "--temperature": (args.temperature, DEFAULT_TEMPERATURE),
        "--seed": (args.seed, DEFAULT_SEED),
    }
    effective_model = requested_model or (frozen_cell.model_id if frozen_cell is not None else None)
    mismatches = [f"{k}={got!r} (expected {want!r})" for k, (got, want) in expected.items() if got != want]
    if frozen_cell is not None and effective_model is not None:
        effective_key = _model_identity_key(effective_model)
        frozen_key = _model_identity_key(frozen_cell.model_id)
        if effective_key != frozen_key:
            mismatches.append(
                f"--model identity={effective_key!r} from {effective_model!r} "
                f"(expected {frozen_key!r} from frozen {frozen_cell.model_id!r})"
            )
    if mismatches:
        raise SystemExit(
            "E-0013 must use the E-0006 generation identity; mismatches: "
            + ", ".join(mismatches)
        )
    if (
        frozen_cell is not None
        and requested_model is None
        and args.backend == "hf"
        and _looks_like_local_path(frozen_cell.model_id)
        and not Path(frozen_cell.model_id).exists()
    ):
        flag = "--qwen-model" if frozen_cell.model_label == "qwen2.5-7b" else "--llama-model"
        raise SystemExit(
            f"{frozen_cell.cell_key}: frozen E-0006 model_id {frozen_cell.model_id!r} "
            "is a local path that does not exist on this machine. "
            f"Pass {flag} with this machine's reference to the same model "
            f"(identity key {_model_identity_key(frozen_cell.model_id)!r})."
        )
    if args.bootstrap_b < adj.BOOTSTRAP_B and not args.allow_underpowered:
        raise SystemExit(
            f"--bootstrap-b {args.bootstrap_b} < frozen {adj.BOOTSTRAP_B}; "
            "pass --allow-underpowered only for synthetic smoke/debug."
        )
    if args.backend == "hf" and args.n_items is not None:
        raise SystemExit("--n-items is forbidden for hf E-0013; use the frozen full uncertainty N")
    return effective_model if frozen_cell is not None else None


def _parse_cell(cell_key: str) -> Tuple[str, str]:
    method, model_label = str(cell_key).split("__", 1)
    if method not in {"caa", "iti"}:
        raise ValueError(f"bad method in cell {cell_key!r}")
    if model_label not in {"qwen2.5-7b", "llama3-8b"}:
        raise ValueError(f"bad model label in cell {cell_key!r}")
    return method, model_label


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    _validate_generation_identity(args)
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    frozen_configs: Dict[str, FrozenCellConfig] = {}
    model_ids: Dict[str, str] = {}
    for cell_key in args.cells:
        method, model_label = _parse_cell(cell_key)
        cfg = load_frozen_cell_config(Path(args.frozen_root), method, model_label)
        override_model = args.qwen_model if model_label == "qwen2.5-7b" else args.llama_model
        model_ids[cell_key] = _validate_generation_identity(
            args, frozen_cell=cfg, requested_model=override_model
        )
        frozen_configs[cell_key] = cfg
    use_fixture = args.backend == "synthetic"
    items = load_uncertainty_items(use_fixture=use_fixture, n_items=args.n_items)
    items_by_split = split_items(items, args.seed)
    splits = list(dict.fromkeys(args.splits))
    cell_records: List[Dict] = []
    cell_meta: Dict[str, object] = {}
    started = utcnow()
    t0 = time.time()
    for cell_key in args.cells:
        cfg = frozen_configs[cell_key]
        effective_model_ref = model_ids[cell_key]
        model_id = effective_model_ref
        if args.backend == "synthetic":
            model_id = "synthetic-offline"
        print(
            f"[E-0013] cell={cell_key} backend={args.backend} model={model_id} "
            f"layer={cfg.layer} alpha={cfg.frozen_alpha} prompt={cfg.best_prompt_id}",
            flush=True,
        )
        recs, meta = generate_cell_samples(
            cfg,
            backend_name=args.backend,
            model_id=model_id,
            items_by_split=items_by_split,
            splits=splits,
            out_dir=out_dir / f"cell_{cell_key}",
            max_new_tokens=args.max_new_tokens,
            temperature=args.temperature,
            seed=args.seed,
            batch_size=args.batch_size,
            raw_text_max_chars=args.raw_text_max_chars,
            n_extraction=args.n_extraction,
        )
        cell_records.extend(recs)
        cell_meta[cell_key] = {
            "frozen_config": cfg.__dict__,
            "frozen_model_id": cfg.model_id,
            "effective_model_ref": effective_model_ref,
            "model_identity_key": _model_identity_key(effective_model_ref),
            "run_model_id": model_id,
            **meta,
        }

    samples_path = out_dir / "samples.jsonl"
    reanalysis_path = out_dir / "reanalysis.json"
    manifest_path = out_dir / "run_manifest.json"
    _write_jsonl(samples_path, cell_records)
    analysis = reanalyse(cell_records, bootstrap_b=args.bootstrap_b, seed=args.seed)
    _write_json(reanalysis_path, analysis)
    manifest = {
        "experiment_id": EXPERIMENT_ID,
        "valid_for_paper": False,
        "purpose": "uncertainty format-compliance robustness recheck; does not modify frozen E-0006",
        "backend": args.backend,
        "started_at": started,
        "ended_at": utcnow(),
        "wall_clock_seconds": time.time() - t0,
        "code_commit": git_commit(str(_REPO)),
        "generation_identity": {
            "model_by_cell": {k: v.model_id for k, v in frozen_configs.items()},
            "frozen_model_by_cell": {k: v.model_id for k, v in frozen_configs.items()},
            "effective_model_by_cell": model_ids,
            "model_identity_key_by_cell": {k: _model_identity_key(v) for k, v in model_ids.items()},
            "max_new_tokens": args.max_new_tokens,
            "temperature": args.temperature,
            "seed": args.seed,
            "k_samples": adj.K_SAMPLES,
        },
        "frozen_root": _rel(Path(args.frozen_root)),
        "cells": cell_meta,
        "artifacts": {
            "samples_jsonl": _rel(samples_path),
            "reanalysis_json": _rel(reanalysis_path),
            "run_manifest_json": _rel(manifest_path),
        },
        "synthetic_proxy": bool(args.backend == "synthetic"),
    }
    _write_json(manifest_path, manifest)
    print(f"[E-0013] wrote {_rel(samples_path)}")
    print(f"[E-0013] wrote {_rel(reanalysis_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
