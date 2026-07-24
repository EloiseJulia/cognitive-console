import json
from pathlib import Path

import numpy as np
import pytest

from cognitive_console.analysis import ood
from scripts import run_ood_capture as R


def _write_cell_result(cell_dir: Path, method: str, model_label: str, delta: np.ndarray) -> None:
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
                "test_item_ids": item_ids,
                "test_item_prompts": prompts,
            }
        ],
    }
    (cell_dir / "c2b_adjudication_results.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )


def _build_arm_dir(tmp_path: Path, delta: np.ndarray) -> Path:
    arm_dir = tmp_path / "arm_full"
    arm_dir.mkdir(parents=True, exist_ok=True)
    for key in sorted(R.FROZEN_CELL_KEYS):
        method, model_label = key.split("__", 1)
        cell_dir = arm_dir / f"cell_{key}"
        cell_dir.mkdir(parents=True, exist_ok=True)
        _write_cell_result(cell_dir, method, model_label, delta)
    return arm_dir


def test_run_ood_capture_synthetic_signal_supports(tmp_path):
    n = 64
    x = np.linspace(0.0, 1.0, num=n)
    delta = 0.1 - 0.8 * x  # larger harm at larger x
    arm_dir = _build_arm_dir(tmp_path, delta)
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
    arm_dir = _build_arm_dir(tmp_path, delta)
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
