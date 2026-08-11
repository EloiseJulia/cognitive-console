"""Manifest-driven E-0013 four-cell uncertainty format/missingness analysis.

The analyzer accepts either the E-0013 ``samples.jsonl`` schema or a restored
E-0006 ``transcripts/`` directory. It fails closed on incomplete grids unless
``--allow-incomplete`` is used for an explicitly non-claim-bearing inventory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cognitive_console.eval import scorers
from cognitive_console.experiments import adjudicate_c2b as adj
from cognitive_console.lineage import git_commit, utcnow
from scripts import run_arm_matrix as arm
from scripts import run_uncertainty_format_recheck as base

DEFAULT_MANIFEST = (
    _REPO
    / "docs"
    / "research"
    / "2026-08-11-uncertainty-grid-recheck"
    / "frozen-manifest.json"
)
DEFAULT_OUT_DIR = _REPO / "results" / "E-0013-uncertainty-grid-recheck"
EXPECTED_CONDITIONS = ("prompt", "steer", "baseline")


class RecheckError(ValueError):
    """Fail-closed protocol, source, or coverage error."""


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _canonical_hash(value: object) -> str:
    raw = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _resolve(path: str | Path) -> Path:
    p = Path(path)
    return p.resolve() if p.is_absolute() else (_REPO / p).resolve()


def _rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(_REPO)).replace("\\", "/")
    except ValueError:
        return str(path.resolve()).replace("\\", "/")


def _read_json(path: Path) -> Dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RecheckError(f"{path}: expected JSON object")
    return payload


def _read_jsonl(path: Path) -> List[Dict]:
    rows: List[Dict] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RecheckError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
            if not isinstance(row, dict):
                raise RecheckError(f"{path}:{line_no}: expected JSON object")
            rows.append(row)
    return rows


def _write_json(path: Path, payload: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def _git_dirty() -> bool:
    proc = subprocess.run(
        ["git", "-C", str(_REPO), "status", "--porcelain"],
        check=True,
        capture_output=True,
        text=True,
    )
    return bool(proc.stdout.strip())


def _assert_equal(actual, expected, label: str) -> None:
    if actual != expected:
        raise RecheckError(f"{label}: expected {expected!r}, got {actual!r}")


def _assert_close(actual, expected, label: str, *, atol: float = 1e-12) -> None:
    if not math.isclose(float(actual), float(expected), rel_tol=1e-10, abs_tol=atol):
        raise RecheckError(f"{label}: expected {expected!r}, got {actual!r}")


def load_protocol(path: Path) -> Dict:
    payload = _read_json(path)
    _assert_equal(
        set(payload.get("cells", {})),
        set(arm.FROZEN_CELL_KEYS),
        "manifest four-cell identity",
    )
    analysis = dict(payload.get("analysis") or {})
    generation = dict(payload.get("generation") or {})
    _assert_equal(analysis.get("axis"), base.AXIS, "manifest axis")
    _assert_equal(analysis.get("split"), "test", "manifest headline split")
    _assert_equal(
        tuple(analysis.get("conditions") or ()),
        EXPECTED_CONDITIONS,
        "manifest conditions",
    )
    frozen_values = {
        "seed": base.DEFAULT_SEED,
        "k_samples": adj.K_SAMPLES,
        "max_new_tokens": base.DEFAULT_MAX_NEW_TOKENS,
        "temperature": base.DEFAULT_TEMPERATURE,
        "do_sample": True,
        "top_p": None,
        "batch_size": 16,
        "n_extraction": base.DEFAULT_N_EXTRACTION,
        "raw_text_max_chars": 8000,
    }
    for key, expected in frozen_values.items():
        _assert_equal(generation.get(key), expected, f"manifest generation.{key}")
    _assert_equal(
        analysis.get("bootstrap_b"), adj.BOOTSTRAP_B, "manifest bootstrap_b"
    )
    _assert_equal(
        analysis.get("bootstrap_seed"), base.DEFAULT_SEED, "manifest bootstrap_seed"
    )
    _assert_equal(
        tuple(generation.get("split_order") or ()),
        ("dev", "test"),
        "manifest generation.split_order",
    )
    _assert_equal(
        tuple(generation.get("condition_order") or ()),
        EXPECTED_CONDITIONS,
        "manifest generation.condition_order",
    )
    _assert_equal(
        generation.get("test_use_policy"),
        base.TEST_USE_POLICY,
        "manifest generation.test_use_policy",
    )
    evidence_scope = dict(payload.get("evidence_scope") or {})
    _assert_equal(
        evidence_scope.get("frozen_results_replaced"),
        False,
        "manifest frozen-results replacement guard",
    )
    _assert_equal(
        evidence_scope.get("new_scorer_result_created"),
        False,
        "manifest new-scorer-result guard",
    )
    legacy = dict(payload.get("legacy_e0013") or {})
    for path_key, hash_key in (
        ("samples_path", "samples_sha256"),
        ("reanalysis_path", "reanalysis_sha256"),
        ("run_manifest_path", "run_manifest_sha256"),
    ):
        protected = _resolve(legacy[path_key])
        _assert_equal(
            sha256_file(protected),
            legacy[hash_key],
            f"legacy E-0013 {path_key} hash",
        )
    return payload


def load_frozen_items(protocol: Dict) -> Tuple[List[Dict], Dict[str, List[Dict]], Dict]:
    generation = dict(protocol["generation"])
    spec = dict(generation["item_artifact"])
    path = _resolve(spec["path"])
    if not path.is_file():
        raise RecheckError(f"frozen item artifact missing: {path}")
    actual_sha = sha256_file(path)
    _assert_equal(actual_sha, spec["sha256"], "frozen item artifact sha256")
    items: List[Dict] = []
    for row in _read_jsonl(path):
        try:
            item = {
                "id": str(row["id"]),
                "prompt": str(row["prompt"]),
                "answer": row["answer"],
                "aliases": list(row.get("aliases") or []),
            }
        except KeyError as exc:
            raise RecheckError(f"{path}: item row missing {exc.args[0]!r}") from exc
        items.append(item)
    _assert_equal(len(items), spec["item_count"], "frozen item count")
    _assert_equal(
        _canonical_hash(items), spec["canonical_items_sha256"], "canonical item hash"
    )
    split = base.split_items(items, int(generation["seed"]))
    split_identity: Dict[str, Dict] = {}
    for name in ("dev", "test"):
        ids = [str(row["id"]) for row in split[name]]
        expected = dict(spec["splits"][name])
        _assert_equal(len(ids), expected["count"], f"{name} item count")
        _assert_equal(_canonical_hash(ids), expected["ids_sha256"], f"{name} ids hash")
        split_identity[name] = {
            "count": len(ids),
            "ids_sha256": _canonical_hash(ids),
        }
    return items, split, {
        "path": _rel(path),
        "sha256": actual_sha,
        "canonical_items_sha256": _canonical_hash(items),
        "splits": split_identity,
    }


def _axis_row(payload: Dict) -> Dict:
    rows = payload.get("axes")
    if rows is None:
        rows = payload.get("axis_results")
    matches = [row for row in (rows or []) if row.get("axis") == base.AXIS]
    if len(matches) != 1:
        raise RecheckError(
            f"expected one {base.AXIS} frozen row, found {len(matches)}"
        )
    return matches[0]


def validate_cell_manifest(
    cell_key: str, cell_spec: Dict, frozen_root: Path
) -> Tuple[base.FrozenCellConfig, Dict, Dict]:
    method, model_label = base._parse_cell(cell_key)
    cfg = base.load_frozen_cell_config(frozen_root, method, model_label)
    frozen_spec = dict(cell_spec["frozen_result"])
    frozen_path = _resolve(frozen_spec["path"])
    _assert_equal(
        frozen_path.resolve(),
        _resolve(cfg.source_result_file).resolve(),
        f"{cell_key} frozen result path",
    )
    _assert_equal(
        sha256_file(frozen_path),
        frozen_spec["sha256"],
        f"{cell_key} frozen result sha256",
    )
    expected = dict(cell_spec["expected"])
    checks = {
        "method": cfg.method,
        "model_label": cfg.model_label,
        "model_identity_key": base._model_identity_key(cfg.model_id),
        "layer": cfg.layer,
        "frozen_alpha": cfg.frozen_alpha,
        "best_prompt_id": cfg.best_prompt_id,
        "best_prompt_sha256": base._sha256_text(cfg.best_prompt_text),
        "neutral_prompt_sha256": base._sha256_text(cfg.neutral_prompt),
        "source_config_fingerprint": cfg.source_config_fingerprint,
    }
    for key, actual in checks.items():
        _assert_equal(actual, expected[key], f"{cell_key} expected.{key}")
    _assert_close(
        cfg.sigma, expected["sigma"], f"{cell_key} expected.sigma", atol=1e-10
    )
    _assert_close(
        cfg.source_mean_diff,
        expected["source_mean_diff"],
        f"{cell_key} expected.source_mean_diff",
        atol=1e-12,
    )
    return cfg, _read_json(frozen_path), {
        "path": _rel(frozen_path),
        "sha256": sha256_file(frozen_path),
        "config_fingerprint": cfg.source_config_fingerprint,
    }


def _condition_expectation(
    cfg: base.FrozenCellConfig, condition: str
) -> Tuple[str, float, float]:
    return base._condition_instruction_and_alpha(cfg, condition)


def _validate_scored_text(
    *,
    text: str,
    item: Dict,
    stored_parse,
    stored_compliant,
    stored_correct,
    stored_imputed,
    stored_score,
    label: str,
) -> Dict:
    parsed = scorers.parse_confidence(text)
    compliant = parsed is not None
    correct = int(scorers.item_is_correct(item, text))
    imputed = float(parsed) if parsed is not None else 0.5
    score = scorers.per_item_brier(correct, imputed)
    if stored_parse is None:
        _assert_equal(parsed, None, f"{label} parsed confidence")
    else:
        _assert_close(parsed, stored_parse, f"{label} parsed confidence")
    _assert_equal(bool(stored_compliant), compliant, f"{label} format compliance")
    _assert_equal(int(stored_correct), correct, f"{label} correctness")
    _assert_close(stored_imputed, imputed, f"{label} imputed confidence")
    _assert_close(stored_score, score, f"{label} 1-Brier")
    return {
        "format_compliant": compliant,
        "item_is_correct": correct,
        "parse_confidence": parsed,
        "imputed_confidence": imputed,
        "per_item_1minus_brier": score,
    }


def _load_e0013_samples(
    path: Path,
    *,
    cell_key: str,
    cfg: base.FrozenCellConfig,
    items_by_id: Dict[str, Dict],
    split_by_id: Dict[str, str],
    generation: Dict,
) -> Tuple[List[Dict], Dict]:
    rows = _read_jsonl(path)
    standardized: List[Dict] = []
    split_counts = {"dev": 0, "test": 0}
    for index, row in enumerate(rows, 1):
        label = f"{path}:{index}"
        _assert_equal(str(row.get("cell")), cell_key, f"{label} cell")
        _assert_equal(str(row.get("axis")), base.AXIS, f"{label} axis")
        _assert_equal(str(row.get("method")), cfg.method, f"{label} method")
        _assert_equal(
            str(row.get("model_label")), cfg.model_label, f"{label} model label"
        )
        _assert_equal(
            base._model_identity_key(str(row.get("model_id"))),
            base._model_identity_key(cfg.model_id),
            f"{label} model identity",
        )
        item_id = str(row.get("item_id"))
        if item_id not in items_by_id:
            raise RecheckError(f"{label}: unexpected item_id {item_id!r}")
        split = str(row.get("split"))
        _assert_equal(split, split_by_id[item_id], f"{label} split")
        split_counts[split] += 1
        condition = str(row.get("condition"))
        if condition not in EXPECTED_CONDITIONS:
            raise RecheckError(f"{label}: unexpected condition {condition!r}")
        sample_index = int(row.get("sample_index"))
        if sample_index not in range(int(generation["k_samples"])):
            raise RecheckError(f"{label}: bad sample_index {sample_index}")
        instruction, requested_alpha, effective_alpha = _condition_expectation(
            cfg, condition
        )
        prompt_text = adj.format_task_input(base.AXIS, instruction, items_by_id[item_id])
        _assert_equal(int(row.get("layer")), cfg.layer, f"{label} layer")
        _assert_close(
            row.get("requested_alpha"),
            requested_alpha,
            f"{label} requested alpha",
        )
        _assert_close(
            row.get("effective_alpha"),
            effective_alpha,
            f"{label} effective alpha",
        )
        _assert_equal(
            row.get("instruction_sha256"),
            base._sha256_text(instruction),
            f"{label} instruction hash",
        )
        _assert_equal(
            row.get("prompt_text_sha256"),
            base._sha256_text(prompt_text),
            f"{label} prompt hash",
        )
        expected_seed = base._call_seed(
            int(generation["seed"]),
            items_by_id[item_id],
            effective_alpha,
            sample_index,
        )
        _assert_equal(int(row.get("sample_seed")), expected_seed, f"{label} sample seed")
        if bool(row.get("synthetic_proxy")):
            raise RecheckError(f"{label}: synthetic row cannot support the recheck")
        if bool(row.get("raw_text_truncated")):
            raise RecheckError(f"{label}: raw text is truncated")
        text = str(row.get("raw_text", ""))
        if not text:
            raise RecheckError(f"{label}: empty raw text")
        _assert_equal(
            row.get("raw_text_sha256"),
            base._sha256_text(text),
            f"{label} raw text hash",
        )
        diag = _validate_scored_text(
            text=text,
            item=items_by_id[item_id],
            stored_parse=row.get("parse_confidence"),
            stored_compliant=row.get("format_compliant"),
            stored_correct=row.get("item_is_correct"),
            stored_imputed=row.get("imputed_confidence"),
            stored_score=row.get("per_item_1minus_brier"),
            label=label,
        )
        standardized.append(
            {
                "cell": cell_key,
                "split": split,
                "condition": condition,
                "item_id": item_id,
                "sample_index": sample_index,
                **diag,
            }
        )
    return standardized, {
        "schema": "e0013_samples_v1",
        "source_rows_total": len(rows),
        "source_rows_by_split": split_counts,
        "files": [{"path": _rel(path), "sha256": sha256_file(path), "rows": len(rows)}],
    }


def _transcript_phase_files(path: Path) -> Dict[str, Path]:
    phase_by_condition = {
        "prompt": adj.PHASE_TEST_PROMPT,
        "steer": adj.PHASE_TEST_STEER,
        "baseline": adj.PHASE_TEST_BASELINE,
    }
    files: Dict[str, Path] = {}
    for condition, phase in phase_by_condition.items():
        matches = sorted(path.glob(f"{base.AXIS}__{phase}__*.jsonl"))
        if len(matches) != 1:
            raise RecheckError(
                f"{path}: expected one {base.AXIS}/{phase} transcript, got {len(matches)}"
            )
        files[condition] = matches[0]
    return files


def _load_c2b_transcript_dir(
    path: Path,
    *,
    cell_key: str,
    cfg: base.FrozenCellConfig,
    frozen_payload: Dict,
    items_by_id: Dict[str, Dict],
    test_ids: Sequence[str],
    generation: Dict,
) -> Tuple[List[Dict], Dict]:
    files = _transcript_phase_files(path)
    standardized: List[Dict] = []
    file_meta: List[Dict] = []
    for condition, file_path in files.items():
        rows = _read_jsonl(file_path)
        file_meta.append(
            {"path": _rel(file_path), "sha256": sha256_file(file_path), "rows": len(rows)}
        )
        instruction, requested_alpha, effective_alpha = _condition_expectation(
            cfg, condition
        )
        expected_phase = {
            "prompt": adj.PHASE_TEST_PROMPT,
            "steer": adj.PHASE_TEST_STEER,
            "baseline": adj.PHASE_TEST_BASELINE,
        }[condition]
        for index, row in enumerate(rows, 1):
            label = f"{file_path}:{index}"
            _assert_equal(str(row.get("axis")), base.AXIS, f"{label} axis")
            _assert_equal(str(row.get("phase")), expected_phase, f"{label} phase")
            item_id = str(row.get("item_id"))
            if item_id not in items_by_id or item_id not in set(test_ids):
                raise RecheckError(f"{label}: unexpected TEST item {item_id!r}")
            sample_index = int(row.get("sample_index"))
            if sample_index not in range(int(generation["k_samples"])):
                raise RecheckError(f"{label}: bad sample_index {sample_index}")
            _assert_equal(int(row.get("layer")), cfg.layer, f"{label} layer")
            _assert_equal(str(row.get("instruction")), instruction, f"{label} instruction")
            _assert_close(row.get("alpha"), effective_alpha, f"{label} effective alpha")
            _assert_close(
                row.get("requested_alpha"),
                requested_alpha,
                f"{label} requested alpha",
            )
            prompt_text = adj.format_task_input(
                base.AXIS, instruction, items_by_id[item_id]
            )
            _assert_equal(str(row.get("prompt_text")), prompt_text, f"{label} prompt")
            expected_seed = base._call_seed(
                int(generation["seed"]),
                items_by_id[item_id],
                effective_alpha,
                sample_index,
            )
            _assert_equal(
                int(row.get("sample_seed")), expected_seed, f"{label} sample seed"
            )
            meta = dict(row.get("meta") or {})
            _assert_equal(meta.get("method"), cfg.method, f"{label} method")
            _assert_equal(meta.get("backend"), "hf", f"{label} backend")
            _assert_equal(
                base._model_identity_key(str(meta.get("model"))),
                base._model_identity_key(cfg.model_id),
                f"{label} model identity",
            )
            if bool(row.get("generation_truncated")):
                raise RecheckError(f"{label}: generation text is truncated")
            text = str(row.get("generation_text", ""))
            if not text:
                raise RecheckError(f"{label}: empty generation text")
            parse = dict(row.get("parse") or {})
            parsed = parse.get("parsed_confidence")
            diag = _validate_scored_text(
                text=text,
                item=items_by_id[item_id],
                stored_parse=parsed,
                stored_compliant=not bool(parse.get("axis_parse_failed")),
                stored_correct=parse.get("correctness"),
                stored_imputed=float(parsed) if parsed is not None else 0.5,
                stored_score=row.get("sample_outcome"),
                label=label,
            )
            standardized.append(
                {
                    "cell": cell_key,
                    "split": "test",
                    "condition": condition,
                    "item_id": item_id,
                    "sample_index": sample_index,
                    **diag,
                }
            )

    frozen = _axis_row(frozen_payload)
    test_order = list(test_ids)
    for condition, field in (
        ("prompt", "per_item_prompt"),
        ("steer", "per_item_steer"),
    ):
        expected_values = [float(v) for v in frozen[field]]
        observed = base._mean_by_item(
            [row for row in standardized if row["condition"] == condition]
        )
        observed_values = [observed[item_id] for item_id in test_order]
        if not np.allclose(observed_values, expected_values, atol=1e-12, rtol=1e-10):
            raise RecheckError(
                f"{cell_key}: restored {condition} transcripts do not reproduce "
                f"the frozen E-0006 per-item outcomes"
            )
    return standardized, {
        "schema": "c2b_transcript_dir_v1",
        "source_rows_total": len(standardized),
        "source_rows_by_split": {"dev": 0, "test": len(standardized)},
        "files": file_meta,
        "frozen_per_item_outcomes_reproduced": True,
    }


def _validate_coverage(
    records: Sequence[Dict], *, cell_key: str, test_ids: Sequence[str], k: int
) -> Dict:
    test_records = [row for row in records if row["split"] == "test"]
    dev_records = [row for row in records if row["split"] == "dev"]
    unexpected_split = [
        row for row in records if row["split"] not in {"dev", "test"}
    ]
    if unexpected_split:
        raise RecheckError(f"{cell_key}: unexpected split rows present")
    expected_keys = {
        (condition, item_id, sample_index)
        for condition in EXPECTED_CONDITIONS
        for item_id in test_ids
        for sample_index in range(k)
    }
    actual_keys: List[Tuple[str, str, int]] = [
        (str(row["condition"]), str(row["item_id"]), int(row["sample_index"]))
        for row in test_records
    ]
    if len(actual_keys) != len(set(actual_keys)):
        raise RecheckError(f"{cell_key}: duplicate TEST condition/item/sample rows")
    missing = sorted(expected_keys - set(actual_keys))
    extra = sorted(set(actual_keys) - expected_keys)
    if missing or extra:
        raise RecheckError(
            f"{cell_key}: incomplete TEST grid; missing={len(missing)} extra={len(extra)}"
        )
    return {
        "source_rows_total": len(records),
        "test_rows_used": len(test_records),
        "dev_rows_explicitly_not_in_headline": len(dev_records),
        "other_rows_rejected": 0,
        "expected_test_rows": len(expected_keys),
        "test_grid_complete": True,
        "test_items": len(test_ids),
        "samples_per_item_condition": k,
    }


def _complete_case_counts(records: Sequence[Dict]) -> Dict:
    keyed: Dict[Tuple[str, int], Dict[str, Dict]] = {}
    for row in records:
        if row["split"] != "test" or row["condition"] not in {"prompt", "steer"}:
            continue
        key = (str(row["item_id"]), int(row["sample_index"]))
        keyed.setdefault(key, {})[str(row["condition"])] = row
    counts = {
        "total_prompt_steer_sample_pairs": len(keyed),
        "both_compliant": 0,
        "prompt_noncompliant_only": 0,
        "steer_noncompliant_only": 0,
        "both_noncompliant": 0,
    }
    items_with_pair = set()
    all_items = {key[0] for key in keyed}
    for (item_id, _), pair in keyed.items():
        prompt_ok = bool(pair["prompt"]["format_compliant"])
        steer_ok = bool(pair["steer"]["format_compliant"])
        if prompt_ok and steer_ok:
            counts["both_compliant"] += 1
            items_with_pair.add(item_id)
        elif not prompt_ok and steer_ok:
            counts["prompt_noncompliant_only"] += 1
        elif prompt_ok and not steer_ok:
            counts["steer_noncompliant_only"] += 1
        else:
            counts["both_noncompliant"] += 1
    counts["items_with_at_least_one_complete_pair"] = len(items_with_pair)
    counts["items_with_zero_complete_pairs"] = len(all_items - items_with_pair)
    return counts


def _exact_condition_counts(cell_analysis: Dict) -> Dict:
    out: Dict[str, Dict] = {}
    for condition in EXPECTED_CONDITIONS:
        row = dict(cell_analysis["conditions"][condition])
        numerator = int(row["n_format_compliant"])
        denominator = int(row["n_samples"])
        out[condition] = {
            **row,
            "format_compliance_exact": {
                "numerator": numerator,
                "denominator": denominator,
                "fraction": f"{numerator}/{denominator}",
            },
        }
    return out


def _bounds_guard(cell_analysis: Dict) -> Dict:
    rows = cell_analysis["sensitivity"]["worst_case_imputation_bounds"]["bounds"]
    values = [float(row["delta"]) for row in rows]
    lower, upper = min(values), max(values)
    negative = upper < 0.0
    positive = lower > 0.0
    return {
        "lower": lower,
        "upper": upper,
        "spans_zero": lower <= 0.0 <= upper,
        "supports_strict_negative_sign": negative,
        "supports_strict_positive_sign": positive,
        "all_generation_sign_claim_allowed": negative or positive,
        "guard": (
            "No all-generation sign claim unless both adversarial endpoints "
            "have the same strict sign."
        ),
    }


def analyse_cell(
    records: Sequence[Dict],
    *,
    cell_key: str,
    cfg: base.FrozenCellConfig,
    coverage: Dict,
    source_meta: Dict,
    analysis_spec: Dict,
) -> Dict:
    base_analysis = base.reanalyse(
        records,
        bootstrap_b=int(analysis_spec["bootstrap_b"]),
        seed=int(analysis_spec["bootstrap_seed"]),
    )["test_split_only"][cell_key]
    base_analysis["conditions"] = _exact_condition_counts(base_analysis)
    base_analysis["sample_accounting"] = {
        **coverage,
        "complete_case": _complete_case_counts(records),
        "no_silent_exclusions": True,
    }
    base_analysis["adversarial_missingness_guard"] = _bounds_guard(base_analysis)
    base_analysis["frozen_reference"] = {
        "source_mean_diff_steer_minus_prompt": cfg.source_mean_diff,
        "replacement_policy": (
            "Reference only. This recheck does not replace or rescore E-0006."
        ),
    }
    base_analysis["source"] = source_meta
    return base_analysis


def _select_source(cell_spec: Dict) -> Tuple[Optional[Dict], List[Dict]]:
    inventory: List[Dict] = []
    selected: Optional[Dict] = None
    for candidate in cell_spec.get("sources", []):
        candidate = dict(candidate)
        path = _resolve(candidate["path"])
        kind = str(candidate["kind"])
        raw_exists = (
            path.is_dir() if kind == "c2b_transcript_dir_v1" else path.is_file()
        )
        exists = raw_exists
        row = {
            "kind": kind,
            "path": _rel(path),
            "exists": exists,
            "origin": candidate.get("origin"),
        }
        completion_identity = None
        if candidate.get("origin") == "frozen_replay":
            completion_path = path.parent / "completion.json"
            row["raw_exists"] = raw_exists
            row["completion_path"] = _rel(completion_path)
            row["completion_exists"] = completion_path.is_file()
            exists = raw_exists and completion_path.is_file()
            row["exists"] = exists
            if exists:
                completion = _read_json(completion_path)
                _assert_equal(
                    completion.get("status"),
                    "COMPLETE_PENDING_INDEPENDENT_RESULTS_AUDIT",
                    f"{completion_path} status",
                )
                sample_identity = dict(completion.get("samples_jsonl") or {})
                _assert_equal(
                    sample_identity.get("path"),
                    _rel(path),
                    f"{completion_path} samples path",
                )
                _assert_equal(
                    sample_identity.get("sha256"),
                    sha256_file(path),
                    f"{completion_path} samples hash",
                )
                run_manifest_path = path.parent / "run_manifest.json"
                run_identity = dict(completion.get("run_manifest_json") or {})
                _assert_equal(
                    run_identity.get("path"),
                    _rel(run_manifest_path),
                    f"{completion_path} run-manifest path",
                )
                _assert_equal(
                    run_identity.get("sha256"),
                    sha256_file(run_manifest_path),
                    f"{completion_path} run-manifest hash",
                )
                run_manifest = _read_json(run_manifest_path)
                evidence_scope = dict(run_manifest.get("evidence_scope") or {})
                _assert_equal(
                    evidence_scope.get("frozen_results_replaced"),
                    False,
                    f"{run_manifest_path} frozen-results guard",
                )
                _assert_equal(
                    evidence_scope.get("new_scorer_result_created"),
                    False,
                    f"{run_manifest_path} scorer-result guard",
                )
                completion_identity = {
                    "completion_path": _rel(completion_path),
                    "completion_sha256": sha256_file(completion_path),
                    "run_manifest_path": _rel(run_manifest_path),
                    "run_manifest_sha256": sha256_file(run_manifest_path),
                    "protocol_manifest_sha256": completion.get(
                        "protocol_manifest_sha256"
                    ),
                }
        if exists and kind != "c2b_transcript_dir_v1":
            actual_sha = sha256_file(path)
            row["sha256"] = actual_sha
            required_sha = candidate.get("sha256")
            if required_sha:
                _assert_equal(
                    actual_sha, required_sha, f"source sha256 for {_rel(path)}"
                )
        inventory.append(row)
        if selected is None and exists:
            selected = {
                **candidate,
                "resolved_path": path,
                "completion_identity": completion_identity,
            }
    return selected, inventory


def _legacy_reproduction(report: Dict, protocol: Dict) -> Dict:
    spec = dict(protocol["legacy_e0013"])
    path = _resolve(spec["reanalysis_path"])
    _assert_equal(
        sha256_file(path), spec["reanalysis_sha256"], "legacy E-0013 reanalysis hash"
    )
    old = _read_json(path)["test_split_only"]["caa__qwen2.5-7b"]
    new = report["cells"]["caa__qwen2.5-7b"]
    comparisons = {
        "prompt_compliance": (
            old["conditions"]["prompt"]["format_compliance_rate"],
            new["conditions"]["prompt"]["format_compliance_rate"],
        ),
        "steer_compliance": (
            old["conditions"]["steer"]["format_compliance_rate"],
            new["conditions"]["steer"]["format_compliance_rate"],
        ),
        "baseline_compliance": (
            old["conditions"]["baseline"]["format_compliance_rate"],
            new["conditions"]["baseline"]["format_compliance_rate"],
        ),
        "as_run_point": (
            old["frozen_uncertainty_delta_steer_minus_prompt_as_run_imputed"][
                "point"
            ],
            new["frozen_uncertainty_delta_steer_minus_prompt_as_run_imputed"][
                "point"
            ],
        ),
        "complete_case_point": (
            old["format_compliant_only_delta_steer_minus_prompt"]["point"],
            new["format_compliant_only_delta_steer_minus_prompt"]["point"],
        ),
        "complete_case_ci_lo": (
            old["format_compliant_only_delta_steer_minus_prompt"]["ci_lo"],
            new["format_compliant_only_delta_steer_minus_prompt"]["ci_lo"],
        ),
        "complete_case_ci_hi": (
            old["format_compliant_only_delta_steer_minus_prompt"]["ci_hi"],
            new["format_compliant_only_delta_steer_minus_prompt"]["ci_hi"],
        ),
    }
    for label, (expected, actual) in comparisons.items():
        _assert_close(actual, expected, f"legacy E-0013 reproduction {label}")
    return {
        "matches_original_one_cell_result": True,
        "original_path": _rel(path),
        "original_sha256": sha256_file(path),
        "fields_checked": sorted(comparisons),
    }


def run_analysis(protocol_path: Path, *, allow_incomplete: bool) -> Tuple[Dict, Dict]:
    protocol = load_protocol(protocol_path)
    items, split, item_identity = load_frozen_items(protocol)
    items_by_id = {str(item["id"]): item for item in items}
    split_by_id = {
        str(item["id"]): name for name, rows in split.items() for item in rows
    }
    test_ids = [str(item["id"]) for item in split["test"]]
    frozen_root = _resolve(protocol["generation"]["frozen_root"])
    generation = dict(protocol["generation"])
    analysis_spec = dict(protocol["analysis"])
    cells: Dict[str, Dict] = {}
    inventory: Dict[str, Dict] = {}
    missing: List[str] = []
    input_files: List[Dict] = [
        {"path": _rel(protocol_path), "sha256": sha256_file(protocol_path)},
        {
            "path": item_identity["path"],
            "sha256": item_identity["sha256"],
        },
    ]
    legacy = dict(protocol["legacy_e0013"])
    for path_key, hash_key in (
        ("samples_path", "samples_sha256"),
        ("reanalysis_path", "reanalysis_sha256"),
        ("run_manifest_path", "run_manifest_sha256"),
    ):
        input_files.append(
            {
                "path": _rel(_resolve(legacy[path_key])),
                "sha256": legacy[hash_key],
            }
        )

    for cell_key in sorted(arm.FROZEN_CELL_KEYS):
        cell_spec = dict(protocol["cells"][cell_key])
        cfg, frozen_payload, frozen_identity = validate_cell_manifest(
            cell_key, cell_spec, frozen_root
        )
        input_files.append(
            {
                "path": frozen_identity["path"],
                "sha256": frozen_identity["sha256"],
            }
        )
        selected, source_inventory = _select_source(cell_spec)
        inventory[cell_key] = {
            "selected": (
                {
                    "kind": selected["kind"],
                    "path": _rel(selected["resolved_path"]),
                    "origin": selected.get("origin"),
                }
                if selected
                else None
            ),
            "candidates": source_inventory,
        }
        if selected is None:
            missing.append(cell_key)
            continue
        path = Path(selected["resolved_path"])
        if selected["kind"] == "e0013_samples_v1":
            records, source_meta = _load_e0013_samples(
                path,
                cell_key=cell_key,
                cfg=cfg,
                items_by_id=items_by_id,
                split_by_id=split_by_id,
                generation=generation,
            )
        elif selected["kind"] == "c2b_transcript_dir_v1":
            records, source_meta = _load_c2b_transcript_dir(
                path,
                cell_key=cell_key,
                cfg=cfg,
                frozen_payload=frozen_payload,
                items_by_id=items_by_id,
                test_ids=test_ids,
                generation=generation,
            )
        else:
            raise RecheckError(
                f"{cell_key}: unsupported source kind {selected['kind']!r}"
            )
        source_meta["origin"] = selected.get("origin")
        source_meta["frozen_result"] = frozen_identity
        completion_identity = selected.get("completion_identity")
        if completion_identity:
            _assert_equal(
                completion_identity["protocol_manifest_sha256"],
                sha256_file(protocol_path),
                f"{cell_key} completion protocol hash",
            )
            source_meta["completion"] = completion_identity
            source_meta["files"].extend(
                [
                    {
                        "path": completion_identity["completion_path"],
                        "sha256": completion_identity["completion_sha256"],
                    },
                    {
                        "path": completion_identity["run_manifest_path"],
                        "sha256": completion_identity["run_manifest_sha256"],
                    },
                ]
            )
        source_meta["identity"] = {
            "cell": cell_key,
            "method": cfg.method,
            "model_label": cfg.model_label,
            "model_identity_key": base._model_identity_key(cfg.model_id),
            "layer": cfg.layer,
            "frozen_alpha": cfg.frozen_alpha,
            "best_prompt_id": cfg.best_prompt_id,
            "source_config_fingerprint": cfg.source_config_fingerprint,
        }
        input_files.extend(source_meta["files"])
        coverage = _validate_coverage(
            records,
            cell_key=cell_key,
            test_ids=test_ids,
            k=int(generation["k_samples"]),
        )
        cells[cell_key] = analyse_cell(
            records,
            cell_key=cell_key,
            cfg=cfg,
            coverage=coverage,
            source_meta=source_meta,
            analysis_spec=analysis_spec,
        )

    grid_complete = not missing
    complete_case_negative = {
        key: float(row["format_compliant_only_delta_steer_minus_prompt"]["ci_hi"])
        < 0.0
        for key, row in cells.items()
    }
    all_generation_negative = {
        key: bool(
            row["adversarial_missingness_guard"][
                "supports_strict_negative_sign"
            ]
        )
        for key, row in cells.items()
    }
    report = {
        "experiment_id": protocol["experiment_id"],
        "generated_at": utcnow(),
        "grid_complete": grid_complete,
        "valid_for_paper": False,
        "analysis_status": (
            "COMPLETE_PENDING_INDEPENDENT_AUDIT"
            if grid_complete
            else "INCOMPLETE_MISSING_TRANSCRIPTS_NO_GRID_CLAIM"
        ),
        "scientific_result_status": (
            "four-cell reanalysis available but not audited"
            if grid_complete
            else "no new four-cell scientific result; GPU replay remains required"
        ),
        "frozen_results_replaced": False,
        "missing_cells": missing,
        "item_identity": item_identity,
        "cells": cells,
        "grid_summary": {
            "complete_case_ci_strictly_negative_by_available_cell": complete_case_negative,
            "adversarial_bounds_strictly_negative_by_available_cell": all_generation_negative,
            "all_four_complete_case_cis_strictly_negative": (
                all(complete_case_negative.values()) if grid_complete else None
            ),
            "all_four_adversarial_bounds_strictly_negative": (
                all(all_generation_negative.values()) if grid_complete else None
            ),
            "all_generation_grid_sign_claim_allowed": (
                all(all_generation_negative.values()) if grid_complete else False
            ),
        },
        "claim_guard": (
            "Complete-case estimates are post-generation conditioned. No "
            "all-generation sign is claimable for a cell unless its adversarial "
            "missingness interval has one strict sign. No grid claim is permitted "
            "unless all four cells are present and independently audited."
        ),
    }
    if "caa__qwen2.5-7b" in cells:
        report["legacy_e0013_reproduction"] = _legacy_reproduction(report, protocol)
    availability = {
        "experiment_id": protocol["experiment_id"],
        "checked_at": report["generated_at"],
        "grid_complete": grid_complete,
        "available_cells": sorted(cells),
        "missing_cells": missing,
        "inventory": inventory,
        "remote_inventory_note": protocol.get("remote_inventory_note"),
    }
    if missing and not allow_incomplete:
        raise RecheckError(
            "four-cell analysis is incomplete; missing "
            + ", ".join(missing)
            + ". Use --allow-incomplete only to emit a non-claim-bearing inventory."
        )
    lineage = {
        "experiment_id": protocol["experiment_id"],
        "generated_at": report["generated_at"],
        "code_commit": git_commit(str(_REPO)),
        "dirty_tree": _git_dirty(),
        "dirty_tree_policy": (
            "Pre-audit CPU inventory may be dirty; any GPU replay run manifest "
            "must capture its audited code commit and dirty-tree state."
        ),
        "protocol_manifest": {
            "path": _rel(protocol_path),
            "sha256": sha256_file(protocol_path),
        },
        "input_files": sorted(
            {row["path"]: row for row in input_files}.values(),
            key=lambda row: row["path"],
        ),
        "manual_edits_allowed": False,
    }
    return {"report": report, "availability": availability}, lineage


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manifest-driven E-0013 four-cell uncertainty reanalysis"
    )
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="emit explicit partial verification/inventory; never enables a grid claim",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    protocol_path = _resolve(args.manifest)
    outputs, lineage = run_analysis(
        protocol_path, allow_incomplete=bool(args.allow_incomplete)
    )
    out_dir = _resolve(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    availability_path = out_dir / "availability.json"
    report_name = (
        "all_cell_reanalysis.json"
        if outputs["report"]["grid_complete"]
        else "partial_existing_data_verification.json"
    )
    report_path = out_dir / report_name
    lineage_path = out_dir / "lineage.json"
    _write_json(availability_path, outputs["availability"])
    _write_json(report_path, outputs["report"])
    lineage["outputs"] = [
        {"path": _rel(availability_path), "sha256": sha256_file(availability_path)},
        {"path": _rel(report_path), "sha256": sha256_file(report_path)},
    ]
    _write_json(lineage_path, lineage)
    print(f"[uncertainty-grid] wrote {_rel(availability_path)}")
    print(f"[uncertainty-grid] wrote {_rel(report_path)}")
    print(f"[uncertainty-grid] wrote {_rel(lineage_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
