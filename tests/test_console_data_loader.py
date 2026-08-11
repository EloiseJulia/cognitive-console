from __future__ import annotations

import json
from io import BytesIO
import re
from pathlib import Path

import pytest
import fitz
from pypdf import PdfReader

from cognitive_console.console.data_loader import build_console_payload, build_demo_report
from cognitive_console.console.demo import write_demo_artifacts
from docs.paper.scripts.plot_console_ui_contract import main as plot_console_ui_contract


REPO = Path(__file__).resolve().parent.parent
C2B_JSON = REPO / "results" / "c2b_adjudication_hf_2026-07-24" / "c2b_adjudication_results.json"
C1_JSON = REPO / "results" / "gpu_7b_2026-07-23" / "c1" / "c1_facade_results.json"
EVIDENCE_LEDGER = REPO / "docs" / "ledgers" / "evidence-ledger.md"
SOCIAL_BEHAVIOR_JSON = REPO / "results" / "flagship_powered" / "behavior" / "flagship_l0_results.json"
SOCIAL_READ_JSON = REPO / "results" / "flagship_powered" / "read" / "flagship_read_results.json"


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
    assert md_path.read_text(encoding="utf-8").startswith("# Console v2 UI-contract simulated demo report")


def test_ui_contract_social_card_reads_e0010_artifacts():
    payload = build_console_payload()
    behavior = _read_json(SOCIAL_BEHAVIOR_JSON)
    read = _read_json(SOCIAL_READ_JSON)

    card = next(
        row for row in payload["ui_contract"]["cards"] if row["axis"] == "social_inference_novice_disclosure"
    )
    selected = read["layer_results"][str(read["selected_layer"])]
    ba_m1 = behavior["paired_bootstrap"]["B_minus_A"]["M1"]

    assert card["headline"] == "LEGIBLE: no added control demonstrated"
    assert card["read_status"]["status"] == "HOLDS"
    assert card["read_status"]["value"] == pytest.approx(selected["token_blind"]["auc"])
    assert card["transfer_verdict"]["verdict"] == "NULL"
    assert card["transfer_verdict"]["delta"] == pytest.approx(ba_m1["point_estimate"])
    assert card["transfer_verdict"]["p_bonferroni"] == pytest.approx(ba_m1["p_bonferroni"])
    assert card["evidence_tier"]["tier"] == "exploratory"
    assert any("PENDING" in note for note in card["evidence_tier"]["notes"])


def test_ui_contract_psr_panel_reads_method_strength_artifact():
    payload = build_console_payload()
    psr = payload["ui_contract"]["psr_method_strength"]
    assert psr["evidence_id"] == "E-0009"
    assert psr["verdict"] == "KILL_PLAN_D"
    assert {row["axis"] for row in psr["rows"]} == {
        "deliberation",
        "skepticism",
        "uncertainty_awareness",
    }
    assert all(row["passed"] is False for row in psr["rows"])
    unc = next(row for row in psr["rows"] if row["axis"] == "uncertainty_awareness")
    assert unc["delta"] == pytest.approx(-0.1603479245283019)
    assert unc["ci_hi"] < 0


def test_console_ui_contract_figure_script_runs():
    out = REPO / "results" / "console_v1_demo" / "pytest-console-ui-contract.pdf"
    try:
        plot_console_ui_contract(["--out", out])
        assert out.exists()
        pdf = out.read_bytes()
        assert pdf.startswith(b"%PDF-1.4")
        assert pdf == (
            REPO / "docs" / "paper" / "figures" / "console-ui-contract.pdf"
        ).read_bytes()
        with fitz.open(stream=pdf, filetype="pdf") as document:
            page = document[0]
            assert page.rect.width == pytest.approx(504)
            assert page.rect.height == pytest.approx(260)
            content = page.get_text()
            normalized_content = " ".join(content.split())
            assert "BOUNDED PROMPT COMPARATOR" in normalized_content
            assert "PROMPT-CEILING" not in normalized_content
            for removed_label in (
                "DIAGNOSTIC-ONLY",
                "UNRESOLVED",
                "UNSTABLE",
                "ELIGIBLE",
                "EVIDENCE-SUPPORTED CONTROL",
                "WITHHELD CONTROL",
            ):
                assert removed_label not in normalized_content
            for expected in (
                "COMPUTATIONAL RECORD",
                "READ STATUS",
                "TRANSFER STATUS",
                "BLOCKING REASON",
                "INTERFACE ACTION",
                "Read-only diagnostic candidate within this evidence tier; active control withheld.",
                "Frozen 2x2 grid; mixed resolution; split-sensitivity only.",
                "Frozen 2x2 comparator result; targeted CAA x Qwen recheck.",
                "Mixed resolution: ITI exploratory equivalence; CAA underpowered.",
                "Missingness-limited: complete-case support in one cell; bounds cross zero.",
                "Near-baseline only in CAA x Qwen; other 3 cells unrechecked.",
            ):
                assert expected in normalized_content
            font_sizes = [
                span["size"]
                for block in page.get_text("dict")["blocks"]
                for line in block.get("lines", [])
                for span in line["spans"]
            ]
        assert min(font_sizes) >= 7.0
        reader = PdfReader(BytesIO(pdf))
        fonts = reader.pages[0]["/Resources"]["/Font"]
        assert fonts
        for font_ref in fonts.values():
            font = font_ref.get_object()
            if "/DescendantFonts" in font:
                font = font["/DescendantFonts"][0].get_object()
            descriptor = font["/FontDescriptor"].get_object()
            assert any(key in descriptor for key in ("/FontFile", "/FontFile2", "/FontFile3"))
    finally:
        out.unlink(missing_ok=True)
