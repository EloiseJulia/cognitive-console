import json
import subprocess
import sys
from pathlib import Path

from cognitive_console.microstudy_materials import (
    SEQUENCES_PATH,
    STIMULI_PATH,
    exact_binomial_upper_tail,
    load_sources,
    route_state,
    validate_materials,
)


REPO = Path(__file__).resolve().parent.parent


def test_authoritative_sources_validate():
    report = validate_materials()
    assert report["status"] == "PASS"
    assert report["template_reuse"] == {
        "Q2-NEXT": 4,
        "Q2-BASELINE": 4,
        "Q2-COVERAGE": 2,
    }
    assert report["key_distribution"] == {"A": 2, "B": 2, "C": 3, "D": 3}
    assert report["sequence_count"] == 20
    assert report["trial_row_count"] == 200


def test_frozen_leakage_and_router_metrics():
    metrics = validate_materials()["metrics"]
    expected = {
        "oracle_template": 3,
        "loo_template": 0,
        "global_position": 3,
        "equal_length": 2,
        "negation_marker": 3,
        "modal_marker": 2,
        "read_lexical": 2,
        "single_row_q1": 8,
        "combined_oracle_cca": 2,
        "combined_loo_cca": 0,
        "router": 10,
    }
    assert {name: row["correct"] for name, row in metrics.items()} == expected
    for name, row in metrics.items():
        if name not in {"single_row_q1", "router"}:
            assert row["binomial_p_upper_vs_0_25"] >= 0.05


def test_exact_binomial_values():
    assert exact_binomial_upper_tail(3, 10) == 0.4744071960449219
    assert exact_binomial_upper_tail(2, 10) == 0.7559747695922852
    assert exact_binomial_upper_tail(0, 10) == 1.0


def test_p3_y_q2_requests_missing_scope_without_changing_q1():
    stimuli, _ = load_sources()
    item = next(item for item in stimuli["items"] if item["stimulus_id"] == "MS-P3-Y")
    template = next(
        template
        for template in stimuli["q2_templates"]
        if template["template_id"] == item["q2"]["template_id"]
    )
    assert item["q2"] == {"template_id": "Q2-NEXT", "correct_key": "C"}
    assert "scope boundary" in template["options"][2]["text"]
    assert "unavailable" in item["primitive_evidence"]["scope"]
    assert route_state(item["state_routing_inputs"]) == "Q1_WITHHELD"


def test_sources_are_json_and_cli_emits_report():
    assert STIMULI_PATH.suffix == ".json"
    assert SEQUENCES_PATH.suffix == ".json"
    completed = subprocess.run(
        [sys.executable, "scripts/validate_microstudy_materials.py"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(completed.stdout)
    assert report["status"] == "PASS"


def test_no_attention_check_or_free_text_export_fields():
    stimuli, _ = load_sources()
    export = stimuli["export_schema"]
    assert not any("attention" in field for field in export["session_fields"])
    assert export["free_text_fields"] == []
    assert {"block_1_ease", "block_2_ease"} <= set(export["session_fields"])
    assert {
        "post_task_diagnostic_presented",
        "post_task_diagnostic_submitted",
        "post_task_diagnostic_response",
        "post_task_diagnostic_correct",
    } <= set(export["session_fields"])
