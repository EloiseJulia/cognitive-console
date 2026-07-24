from __future__ import annotations

import json
from pathlib import Path

import pytest

from cognitive_console.console.data_loader import build_console_payload


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


def test_c1_prefers_results_json_when_available():
    payload = build_console_payload(c2b_path=C2B_JSON, c1_path=C1_JSON, evidence_ledger_path=EVIDENCE_LEDGER)
    assert payload["c1"]["source_mode"] == "results_c1_json"
    ratios = {row["axis"]: row["ratio"] for row in payload["c1"]["rows"]}
    assert ratios["deliberation"] == pytest.approx(0.582751249943177)
    assert ratios["skepticism"] == pytest.approx(0.5476263933060945)
    assert ratios["uncertainty_awareness"] == pytest.approx(0.7131063428339024)


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
