import contextlib
import io
import json
import shutil
import subprocess
import threading
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

import pytest

from cognitive_console.microstudy.analysis import (
    analyze,
    exact_sign_flip,
    load_exports,
    validate_export,
)
from cognitive_console.microstudy.materials import (
    material_hashes,
    planned_trials,
    validated_sources,
)
from cognitive_console.microstudy.server import CSP, STATIC_DIR, create_server


def make_export(
    sequence="A1",
    complete=10,
    participant="P001",
    attempt="123e4567-e89b-42d3-a456-426614174000",
):
    stimuli, sequences = validated_sources()
    plan = planned_trials(sequence)
    items = {row["stimulus_id"]: row for row in stimuli["items"]}
    trials = []
    for index, slot in enumerate(plan):
        item = items[slot["item"]]
        done = index < complete
        trials.append(
            {
                "slot_index": slot["slot_index"],
                "condition": slot["condition"],
                "item": slot["item"],
                "pattern": slot["pattern"],
                "content_set": slot["content_set"],
                "block": slot["block"],
                "position": slot["position"],
                "planned": True,
                "presented": done,
                "q1_submitted": done,
                "q2_submitted": done,
                "complete": done,
                "submitted": done,
                "q1": slot["q1_key"] if done else None,
                "q2": slot["q2_key"] if done else None,
                "q1_correct": True if done else None,
                "q2_correct": True if done else None,
                "cca_correct": True if done else None,
                "rt_q1_ms": 100 if done else None,
                "rt_q2_ms": 200 if done else None,
                "rt_total_ms": 300 if done else None,
                "hidden_ms": 0 if done else None,
                "source_status": item["source_status"],
                "source_note": item["source_note"],
                "hypothetical": item["hypothetical"],
                "q1_missing": not done,
                "q2_missing": not done,
                "q1_correct_missing": not done,
                "q2_correct_missing": not done,
                "cca_correct_missing": not done,
                "rt_q1_missing": not done,
                "rt_q2_missing": not done,
                "rt_total_missing": not done,
                "hidden_ms_missing": not done,
                "materials_version": stimuli["materials_version"],
            }
        )
    return {
        "export_schema_version": "microstudy-export-v1",
        "material_schema_version": stimuli["schema_version"],
        "sequence_schema_version": sequences["schema_version"],
        "material_hashes": material_hashes(),
        "attempt_id": attempt,
        "participant_code": participant,
        "sequence": sequence,
        "completion_status": "complete" if complete == 10 else "partial",
        "practice_presented": True,
        "practice_q1_submitted": True,
        "practice_q2_submitted": True,
        "practice_complete": True,
        "post_task_diagnostic_presented": complete == 10,
        "post_task_diagnostic_submitted": complete == 10,
        "post_task_diagnostic_response": "A" if complete == 10 else None,
        "post_task_diagnostic_correct": True if complete == 10 else None,
        "block_1_ease": "SEQ4" if complete >= 5 else None,
        "block_2_ease": "SEQ5" if complete == 10 else None,
        "mechanical_exclusion": False,
        "mechanical_exclusion_reason": "none",
        "trials": trials,
    }


def test_material_hashes_and_all_sequences_are_deterministic():
    assert set(material_hashes()) == {"stimuli_sha256", "sequences_sha256"}
    for letter in "ABCD":
        for suffix in range(1, 6):
            rows = planned_trials(f"{letter}{suffix}")
            assert len(rows) == 10
            assert len({row["item"] for row in rows}) == 10
            assert [row["slot_index"] for row in rows] == list(range(1, 11))
    with pytest.raises(ValueError):
        planned_trials("Z9")


@pytest.fixture
def live_server():
    server = create_server("127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_server_loopback_headers_mime_and_no_logging(live_server):
    output = io.StringIO()
    with contextlib.redirect_stderr(output):
        with urllib.request.urlopen(f"{live_server}/") as response:
            assert response.status == 200
            assert response.headers["Content-Security-Policy"] == CSP
            assert response.headers["Cache-Control"] == "no-store"
            assert response.headers["Content-Type"].startswith("text/html")
        with urllib.request.urlopen(f"{live_server}/study.js") as response:
            assert response.headers["Content-Type"].startswith(("text/javascript", "application/javascript"))
        with urllib.request.urlopen(f"{live_server}/study_core.mjs") as response:
            assert response.headers["Content-Type"].startswith("application/javascript")
        with urllib.request.urlopen(f"{live_server}/api/sequence/A1") as response:
            assert len(json.load(response)) == 10
    assert output.getvalue() == ""


def test_server_rejects_nonloopback_and_traversal(live_server):
    with pytest.raises(ValueError):
        create_server("0.0.0.0", 0)
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(f"{live_server}/..%2f..%2fpyproject.toml")
    assert exc.value.code == 404


def test_static_integrity_privacy_accessibility_and_geometry():
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    css = (STATIC_DIR / "study.css").read_text(encoding="utf-8")
    js = (STATIC_DIR / "study.js").read_text(encoding="utf-8")
    core = (STATIC_DIR / "study_core.mjs").read_text(encoding="utf-8")
    combined = html + css + js + core
    for forbidden in (
        "localStorage", "sessionStorage", "indexedDB", "document.cookie",
        "serviceWorker", "http://", "https://", "@import",
    ):
        assert forbidden not in combined
    assert 'aria-live="polite"' in html
    assert "focus-visible" in css
    assert "prefers-reduced-motion" in css
    assert "--card-max-width: 960px" in css
    assert "--label-width: 240px" in css
    assert "--body-width: 648px" in css
    assert "--row-min-height: 72px" in css
    assert "q1Start" in js and "q2Start" in js
    assert "lock(\"formal-q1\")" in js
    assert "crypto.randomUUID()" in js
    assert "new Blob" in js
    assert "/^[=+\\-@]/" in core
    assert "primitive_evidence[evidenceId]" in js
    assert "item.flat_order" in js
    assert "q1_key" not in html


def test_javascript_state_machine_when_node_available():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node is unavailable")
    subprocess.run(
        [node, "tests/microstudy_js_test.mjs"],
        cwd=Path(__file__).resolve().parents[1],
        check=True,
        capture_output=True,
        text=True,
    )


def test_export_strict_validation_and_analysis():
    data = make_export()
    assert validate_export(data) is data
    summary = analyze([data], [])
    assert summary["eligible_primary_n"] == 1
    assert summary["primary"]["mean_difference"] == 0
    assert summary["primary"]["exact_one_sided_sign_flip"]["ties"] == 1
    assert summary["missing_as_incorrect_sensitivity"]["mean_difference"] == 0


def test_partial_duplicate_corrupt_and_wrong_hash(tmp_path):
    complete = make_export(attempt="123e4567-e89b-42d3-a456-426614174001")
    partial = make_export(
        complete=8,
        attempt="123e4567-e89b-42d3-a456-426614174002",
        participant="P001",
    )
    wrong_hash = make_export(
        attempt="123e4567-e89b-42d3-a456-426614174003",
        participant="P002",
    )
    wrong_hash["material_hashes"]["stimuli_sha256"] = "0" * 64
    paths = []
    for name, value in (("complete.json", complete), ("partial.json", partial), ("bad.json", wrong_hash)):
        path = tmp_path / name
        path.write_text(json.dumps(value), encoding="utf-8")
        paths.append(path)
    corrupt = tmp_path / "corrupt.json"
    corrupt.write_text("{", encoding="utf-8")
    paths.append(corrupt)
    valid, rejected = load_exports(paths)
    summary = analyze(valid, rejected)
    assert summary["kept_attempts"] == 1
    assert Counter(row["reason"] for row in summary["rejected"]) == {
        "technical_corrupt": 1,
        "materials_version_mismatch": 1,
        "duplicate_attempt": 1,
    }


def test_exact_sign_flip_ties_and_equality():
    assert exact_sign_flip([0, 0]) == {"n_eff": 0, "ties": 2, "p": 1.0}
    result = exact_sign_flip([0.2, 0.2])
    assert result["n_eff"] == 2
    assert result["p"] == 0.25
