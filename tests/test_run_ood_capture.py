import json
from pathlib import Path

import numpy as np
import pytest

from cognitive_console.analysis import ood
from scripts import run_ood_capture as R


def _write_cell_result(
    cell_dir: Path,
    method: str,
    model_label: str,
    delta: np.ndarray,
    *,
    include_test_fields: bool = False,
) -> None:
    item_ids = [f"{model_label}-{i:03d}" for i in range(len(delta))]
    prompts = [f"Q{i}: synthetic uncertainty prompt?" for i in range(len(delta))]
    payload = {
        "steering_method": method,
        "model": f"/frozen/{model_label}",
        "alpha_scale_by_axis": {"uncertainty_awareness": 0.7 if method == "iti" else 1.0},
        "frozen_params": {
            "n_items_by_axis": {"uncertainty_awareness": len(delta)},
            "dev_fraction": 1.0 / 3.0,
        },
        "axes": [
            {
                "axis": "uncertainty_awareness",
                "layer": 12,
                "n_test": len(delta),
                "dev_selection": {"frozen_alpha": 8.0},
                "per_item_diff": [float(x) for x in delta.tolist()],
            }
        ],
    }
    if include_test_fields:
        payload["axes"][0]["test_item_ids"] = item_ids
        payload["axes"][0]["test_item_prompts"] = prompts
    (cell_dir / "c2b_adjudication_results.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )


def _write_uncertainty_transcripts(
    cell_dir: Path,
    *,
    method: str,
    model_label: str,
    delta: np.ndarray,
    broken: str | None = None,
) -> None:
    item_ids = [f"{model_label}-{i:03d}" for i in range(len(delta))]
    prompts = [f"Q{i}: synthetic uncertainty prompt?" for i in range(len(delta))]
    prompt_outcomes = np.zeros(len(delta), dtype=np.float64)
    steer_outcomes = prompt_outcomes + np.asarray(delta, dtype=np.float64)
    root = cell_dir / "transcripts"
    root.mkdir(parents=True, exist_ok=True)
    paired = root / "paired_test_channels.jsonl"
    rows = []
    for idx, item_id in enumerate(item_ids):
        row = {
            "axis": "uncertainty_awareness",
            "item_id": item_id,
            "item_order": idx,
            "sample_index": 0,
            "method": method,
            "model": f"/frozen/{model_label}",
            "prompt_text": prompts[idx],
            "prompt_generation": "p",
            "steered_generation": "s",
            "baseline_generation": "b",
            "prompt_parse": {"axis_parse_failed": False},
            "steer_parse": {"axis_parse_failed": False},
            "baseline_parse": {"axis_parse_failed": False},
            "sample_outcomes": {"prompt": 0.0, "steer": 0.0, "baseline": 0.0},
            "final_item_outcomes": {
                "prompt": float(prompt_outcomes[idx]),
                "steer": float(steer_outcomes[idx]),
            },
        }
        if broken == "missing_prompt_text":
            row.pop("prompt_text", None)
        elif broken == "missing_final_item_outcomes":
            row.pop("final_item_outcomes", None)
        rows.append(row)
    paired.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8"
    )


def _build_arm_dir(
    tmp_path: Path,
    *,
    delta_in_results: np.ndarray,
    delta_in_transcripts: np.ndarray | None = None,
    include_test_fields: bool = False,
    broken_transcript_field: str | None = None,
) -> Path:
    arm_dir = tmp_path / "arm_full"
    arm_dir.mkdir(parents=True, exist_ok=True)
    for key in sorted(R.FROZEN_CELL_KEYS):
        method, model_label = key.split("__", 1)
        cell_dir = arm_dir / f"cell_{key}"
        cell_dir.mkdir(parents=True, exist_ok=True)
        _write_cell_result(
            cell_dir,
            method,
            model_label,
            np.asarray(delta_in_results, dtype=np.float64),
            include_test_fields=include_test_fields,
        )
        _write_uncertainty_transcripts(
            cell_dir,
            method=method,
            model_label=model_label,
            delta=np.asarray(
                delta_in_transcripts if delta_in_transcripts is not None else delta_in_results,
                dtype=np.float64,
            ),
            broken=broken_transcript_field,
        )
    return arm_dir


def test_run_ood_capture_synthetic_signal_supports(tmp_path):
    n = 64
    x = np.linspace(0.0, 1.0, num=n)
    delta = 0.1 - 0.8 * x  # larger harm at larger x
    arm_dir = _build_arm_dir(tmp_path, delta_in_results=delta)
    out_dir = tmp_path / "out_signal"
    rc = R.main(
        [
            "--backend",
            "synthetic",
            "--synthetic-mode",
            "signal",
            "--bootstrap-b",
            "2000",
            "--arm-dir",
            str(arm_dir),
            "--out-dir",
            str(out_dir),
            "--seed",
            "20260723",
        ]
    )
    assert rc == 0
    payload = json.loads((out_dir / "ood_results.json").read_text(encoding="utf-8"))
    assert payload["arm_verdict"] == "SUPPORT"
    assert payload["hm_arm"]["supported"] is True
    assert payload["hm_arm"]["passed_cells"] >= 3
    assert all(float(c["spearman_rho_harm"]) >= 0.30 for c in payload["cells"])
    assert (out_dir / "summary.md").exists()


def test_run_ood_capture_synthetic_null_is_honest_fail(tmp_path):
    rng = np.random.default_rng(123)
    n = 64
    delta = rng.normal(-0.05, 0.2, size=n)
    arm_dir = _build_arm_dir(tmp_path, delta_in_results=delta)
    out_dir = tmp_path / "out_null"
    rc = R.main(
        [
            "--backend",
            "synthetic",
            "--synthetic-mode",
            "null",
            "--bootstrap-b",
            "2000",
            "--arm-dir",
            str(arm_dir),
            "--out-dir",
            str(out_dir),
            "--seed",
            "20260723",
        ]
    )
    assert rc == 0
    payload = json.loads((out_dir / "ood_results.json").read_text(encoding="utf-8"))
    assert payload["arm_verdict"] == "NOT_SUPPORTED"
    assert payload["hm_arm"]["supported"] is False
    assert payload["hm_arm"]["passed_cells"] < 3


def test_run_ood_capture_uses_transcript_items_and_delta_not_seed_fallback(tmp_path):
    n = 32
    delta_in_results = np.zeros(n, dtype=np.float64)
    delta_in_transcripts = np.linspace(-0.4, 0.2, num=n)
    arm_dir = _build_arm_dir(
        tmp_path,
        delta_in_results=delta_in_results,
        delta_in_transcripts=delta_in_transcripts,
        include_test_fields=False,
    )
    out_dir = tmp_path / "out_transcript_source"
    rc = R.main(
        [
            "--backend",
            "synthetic",
            "--synthetic-mode",
            "signal",
            "--bootstrap-b",
            "1000",
            "--arm-dir",
            str(arm_dir),
            "--out-dir",
            str(out_dir),
            "--seed",
            "20260723",
        ]
    )
    assert rc == 0
    payload = json.loads((out_dir / "ood_results.json").read_text(encoding="utf-8"))
    expected = [float(x) for x in delta_in_transcripts.tolist()]
    for cell in payload["cells"]:
        assert cell["delta_outcome"] == pytest.approx(expected)
        assert cell["item_ids"][0].startswith(cell["model_label"])


def test_run_ood_capture_hard_fails_when_transcript_fields_are_missing(tmp_path):
    n = 8
    delta = np.linspace(-0.3, 0.2, num=n)
    arm_dir = _build_arm_dir(
        tmp_path,
        delta_in_results=delta,
        broken_transcript_field="missing_final_item_outcomes",
    )
    out_dir = tmp_path / "out_bad_transcript"
    with pytest.raises(ValueError, match="final_item_outcomes"):
        R.main(
            [
                "--backend",
                "synthetic",
                "--synthetic-mode",
                "signal",
                "--bootstrap-b",
                "300",
                "--arm-dir",
                str(arm_dir),
                "--out-dir",
                str(out_dir),
                "--seed",
                "20260723",
            ]
        )


def test_ood_self_fit_guardrail_rejects_same_split_ids():
    rng = np.random.default_rng(0)
    x = rng.normal(size=(20, 16))
    with pytest.raises(ValueError, match="must differ"):
        ood.per_item_ood_stats(
            x,
            x,
            x,
            reference_id="ref",
            source_hash="sha256:test",
            reference_split_id="same",
            evaluated_split_id="same",
        )


def test_ood_self_fit_guardrail_rejects_same_content_with_renamed_split_ids():
    rng = np.random.default_rng(1)
    steered = rng.normal(size=(20, 16))
    baseline = rng.normal(size=(20, 16))
    with pytest.raises(ValueError, match="content guardrail"):
        ood.per_item_ood_stats(
            steered,
            baseline,
            steered.copy(),
            reference_id="ref",
            source_hash="sha256:test",
            reference_split_id="baseline-L17-renamed",
            evaluated_split_id="steered-L17-renamed",
        )
