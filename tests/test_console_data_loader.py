from __future__ import annotations

import json
from pathlib import Path

import pytest

from cognitive_console.console.data_loader import build_console_payload, build_demo_report
from cognitive_console.console.demo import write_demo_artifacts


REPO = Path(__file__).resolve().parent.parent
C2B_JSON = REPO / "results" / "c2b_adjudication_hf_2026-07-24" / "c2b_adjudication_results.json"
C1_JSON = REPO / "results" / "gpu_7b_2026-07-23" / "c1" / "c1_facade_results.json"
EVIDENCE_LEDGER = REPO / "docs" / "ledgers" / "evidence-ledger.md"


def _read_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def test_loader_reads_real_numbers_from_json():
    c2 = _read_json(C2B_JSON)
    payload = build_console_payload()
    assert payload["c2"]["source_mode"] == "results_c2b_json"
    unc_json = next(row for row in c2["axes"] if row["axis"] == "uncertainty_awareness")
    unc_payload = next(row for row in payload["c2"]["rows"] if row["axis"] == "uncertainty_awareness")
    assert unc_payload["mean_diff"] == pytest.approx(unc_json["mean_diff"])
    assert unc_payload["ci_lo"] == pytest.approx(unc_json["ci_lo"])
    assert unc_payload["ci_hi"] == pytest.approx(unc_json["ci_hi"])


def test_loader_is_not_hardcoded_for_c2_values(tmp_path: Path):
    c2 = _read_json(C2B_JSON)
    patched = dict(c2)
    patched["axes"] = [dict(x) for x in c2["axes"]]
    for row in patched["axes"]:
        if row["axis"] == "uncertainty_awareness":
            row["mean_diff"] = -0.123456
            row["ci_lo"] = -0.2
            row["ci_hi"] = -0.1
    fake = tmp_path / "c2b_adjudication_results.json"
    fake.write_text(json.dumps(patched), encoding="utf-8")

    payload = build_console_payload(c2b_path=fake, c1_path=C1_JSON, evidence_ledger_path=EVIDENCE_LEDGER)
    unc_payload = next(row for row in payload["c2"]["rows"] if row["axis"] == "uncertainty_awareness")
    assert unc_payload["mean_diff"] == pytest.approx(-0.123456)
    assert unc_payload["ci_lo"] == pytest.approx(-0.2)
    assert unc_payload["ci_hi"] == pytest.approx(-0.1)


def test_c2_fallback_to_evidence_ledger_when_results_missing(tmp_path: Path):
    missing_c2 = tmp_path / "missing_c2b_adjudication_results.json"

    payload = build_console_payload(
        c2b_path=missing_c2,
        c1_path=C1_JSON,
        evidence_ledger_path=EVIDENCE_LEDGER,
    )

    assert payload["c2"]["source_mode"] == "evidence_ledger_e0005_fallback"
    assert payload["verdict"] == "KILL_PLAN_D"
    rows = {row["axis"]: row for row in payload["c2"]["rows"]}
    assert rows["deliberation"]["mean_diff"] == pytest.approx(0.015)
    assert rows["skepticism"]["mean_diff"] == pytest.approx(-0.080)
    assert rows["uncertainty_awareness"]["mean_diff"] == pytest.approx(-0.228)
    assert rows["uncertainty_awareness"]["ci_lo"] == pytest.approx(-0.370)
    assert rows["uncertainty_awareness"]["ci_hi"] == pytest.approx(-0.092)
    assert rows["uncertainty_awareness"]["source"] == "evidence_ledger_e0005_fallback"


def test_c1_prefers_results_json_when_available():
    c1 = _read_json(C1_JSON)
    payload = build_console_payload(c2b_path=C2B_JSON, c1_path=C1_JSON, evidence_ledger_path=EVIDENCE_LEDGER)
    assert payload["c1"]["source_mode"] == "results_c1_json"
    ratios = {row["axis"]: row["ratio"] for row in payload["c1"]["rows"]}
    source_ratios = {row["axis"]: row["facade_ratio"] for row in c1["axes"]}
    assert ratios["deliberation"] == pytest.approx(source_ratios["deliberation"])
    assert ratios["skepticism"] == pytest.approx(source_ratios["skepticism"])
    assert ratios["uncertainty_awareness"] == pytest.approx(source_ratios["uncertainty_awareness"])


def test_c1_fallback_to_evidence_ledger_when_results_missing(tmp_path: Path):
    c2 = _read_json(C2B_JSON)
    c2.pop("c1", None)
    fake_c2 = tmp_path / "c2b_no_c1.json"
    fake_c2.write_text(json.dumps(c2), encoding="utf-8")
    missing_c1 = tmp_path / "missing_c1.json"

    payload = build_console_payload(
        c2b_path=fake_c2,
        c1_path=missing_c1,
        evidence_ledger_path=EVIDENCE_LEDGER,
    )
    assert payload["c1"]["source_mode"] == "evidence_ledger_fallback"
    ratios = {row["axis"]: row["ratio"] for row in payload["c1"]["rows"]}
    assert ratios["deliberation"] == pytest.approx(0.583)
    assert ratios["skepticism"] == pytest.approx(0.548)
    assert ratios["uncertainty_awareness"] == pytest.approx(0.713)


def test_payload_maps_four_required_views():
    payload = build_console_payload()
    assert "channels" in payload
    assert "c1" in payload and payload["c1"]["rows"]
    assert "c2" in payload and payload["c2"]["rows"]
    assert "trust_calibration" in payload and payload["trust_calibration"]
    unc_note = next(x for x in payload["trust_calibration"] if x["axis"] == "uncertainty_awareness")
    assert unc_note["severity"] == "red"
    assert "worsen calibration" in unc_note["title"].lower()


def test_arm_payload_reads_uncertainty_harm_from_cell_files():
    payload = build_console_payload()
    assert payload["arm"]["source_mode"] == "results_arm_full_json"
    assert payload["arm"]["arm_verdict"] == "NON_TRANSFER_GENERALIZED"
    cells = {cell["cell_key"]: cell for cell in payload["arm"]["cells"]}
    for cell_key, cell in cells.items():
        cell_json = _read_json(REPO / "results" / "arm_full" / f"cell_{cell_key}" / "c2b_adjudication_results.json")
        unc_json = next(row for row in cell_json["axes"] if row["axis"] == "uncertainty_awareness")
        unc_payload = next(row for row in cell["axes"] if row["axis"] == "uncertainty_awareness")
        assert unc_payload["mean_diff"] == pytest.approx(unc_json["mean_diff"])
        assert unc_payload["ci_hi"] == pytest.approx(unc_json["ci_hi"])
        assert unc_payload["robust_degradation_flag"] is True


def test_simulated_demo_flags_match_frozen_artifacts(tmp_path: Path):
    payload = build_console_payload()
    report = build_demo_report(payload)

    assert report["summary"]["facade_limit_axes"] == [
        "deliberation",
        "skepticism",
        "uncertainty_awareness",
    ]
    assert report["facade_non_flags"][0]["axis"] == "focus"

    c2 = _read_json(C2B_JSON)
    expected_degrade_or_fail = [row["axis"] for row in c2["axes"] if row["mean_diff"] < 0 or not row["passed"]]
    assert report["summary"]["steering_degradation_or_fail_axes"] == expected_degrade_or_fail
    unc = next(row for row in report["steering_degradation_flags"] if row["axis"] == "uncertainty_awareness")
    unc_json = next(row for row in c2["axes"] if row["axis"] == "uncertainty_awareness")
    assert unc["mean_diff"] == pytest.approx(unc_json["mean_diff"])
    assert unc["robust"] is True

    assert set(report["summary"]["robust_uncertainty_harm_cells"]) == {
        "caa__qwen2.5-7b",
        "caa__llama3-8b",
        "iti__qwen2.5-7b",
        "iti__llama3-8b",
    }

    json_path, md_path = write_demo_artifacts(tmp_path)
    written = _read_json(json_path)
    assert written["summary"] == report["summary"]
    assert md_path.read_text(encoding="utf-8").startswith("# Console v1 simulated demo report")
