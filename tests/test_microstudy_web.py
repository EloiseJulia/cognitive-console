import contextlib
import base64
import copy
import io
import json
import os
import shutil
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.request
import uuid
from collections import Counter
from pathlib import Path

import pytest

from cognitive_console.microstudy.analysis import (
    ExportError,
    analyze,
    apply_assignments,
    exact_sign_flip,
    load_exports,
    load_attempt_order_manifest,
    resolve_duplicates,
    validate_export,
)
from cognitive_console.microstudy.materials import material_hashes, planned_trials
from cognitive_console.microstudy.server import (
    CSP,
    STATIC_DIR,
    create_server,
    sign_export,
)

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / ".runtime" / "tests"
TEST_KEY = b"microstudy-test-key-32-bytes-long!!"
CLIENTS = {}


def request_json(base, path, body=None, *, headers=None):
    client = CLIENTS.setdefault(base, {"csrf": None, "capabilities": {}})
    data = None if body is None else json.dumps(body).encode()
    request_headers = dict(headers or {})
    if body is not None:
        body = dict(body)
        body.setdefault("request_id", uuid.uuid4().hex)
        data = json.dumps(body).encode()
        request_headers.update({
            "Content-Type": "application/json",
            "Origin": base,
            "X-CSRF-Token": client["csrf"],
        })
        attempt = body.get("attempt_id")
        if attempt in client["capabilities"]:
            request_headers["X-Study-Capability"] = client["capabilities"][attempt]
    elif path.startswith("/api/export"):
        attempt = path.split("attempt_id=", 1)[1].split("&", 1)[0]
        request_headers["X-Study-Capability"] = client["capabilities"][attempt]
    request = urllib.request.Request(
        f"{base}{path}", data=data,
        headers=request_headers,
        method="GET" if data is None else "POST",
    )
    with urllib.request.urlopen(request) as response:
        value = json.load(response)
    if path == "/api/bootstrap":
        client["csrf"] = value["csrf_token"]
    if path == "/api/start":
        client["capabilities"][value["attempt_id"]] = value["capability"]
    return value


@pytest.fixture
def live_server():
    RUNTIME.mkdir(parents=True, exist_ok=True)
    key_path = RUNTIME / "server.key"
    key_path.write_bytes(TEST_KEY)
    server = create_server("127.0.0.1", 0, key_path)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        request_json(base, "/api/bootstrap")
        yield base, server
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
        shutil.rmtree(RUNTIME, ignore_errors=True)
        CLIENTS.pop(base, None)


def locale_materials(base, locale="en"):
    return request_json(base, f"/api/welcome?ui_language={locale}")


def complete_attempt(base, participant="P001", sequence="A1", locale="en"):
    materials = locale_materials(base, locale)
    common = materials["common"]
    start = request_json(base, "/api/start", {
        "participant_code": participant, "sequence": sequence,
        "ui_language": locale,
    })
    attempt = start["attempt_id"]
    practice = common["practice"]
    request_json(base, "/api/practice", {
        "attempt_id": attempt, "step": "q1",
        "answer": practice["q1"]["options"][0]["id"],
    })
    current = request_json(base, "/api/practice", {
        "attempt_id": attempt, "step": "q2",
        "answer": practice["q2"]["options"][0]["id"],
    })
    for index in range(10):
        q2 = request_json(base, "/api/q1", {
            "attempt_id": attempt, "answer": current["q1"]["options"][0]["id"],
        })
        current = request_json(base, "/api/q2", {
            "attempt_id": attempt, "answer": q2["q2"]["options"][0]["id"],
            "hidden_ms": 0,
        })
        if index in (4, 9):
            current = request_json(base, "/api/ease", {
                "attempt_id": attempt, "block": 1 if index == 4 else 2, "answer": None,
            })
    assert current["phase"] == "diagnostic"
    request_json(base, "/api/diagnostic", {"attempt_id": attempt, "answer": None})
    request_json(base, "/api/complete", {"attempt_id": attempt})
    return request_json(base, f"/api/export?attempt_id={attempt}&format=json")


def partial_attempt(
    base, completed_trials=4, participant="P-PARTIAL", sequence="A1", locale="en"
):
    materials = locale_materials(base, locale)
    common = materials["common"]
    start = request_json(base, "/api/start", {
        "participant_code": participant, "sequence": sequence,
        "ui_language": locale,
    })
    attempt = start["attempt_id"]
    practice = common["practice"]
    request_json(base, "/api/practice", {
        "attempt_id": attempt, "step": "q1",
        "answer": practice["q1"]["options"][0]["id"],
    })
    current = request_json(base, "/api/practice", {
        "attempt_id": attempt, "step": "q2",
        "answer": practice["q2"]["options"][0]["id"],
    })
    for index in range(completed_trials):
        q2 = request_json(base, "/api/q1", {
            "attempt_id": attempt, "answer": current["q1"]["options"][0]["id"],
        })
        current = request_json(base, "/api/q2", {
            "attempt_id": attempt, "answer": q2["q2"]["options"][0]["id"],
            "hidden_ms": 0,
        })
        if index == 4:
            current = request_json(base, "/api/ease", {
                "attempt_id": attempt, "block": 1, "answer": None,
            })
    request_json(base, "/api/save-exit", {"attempt_id": attempt})
    return request_json(base, f"/api/export?attempt_id={attempt}&format=json")


def test_material_hashes_and_all_sequences_are_deterministic():
    assert set(material_hashes()) == {"stimuli_sha256", "sequences_sha256"}
    for letter in "ABCD":
        for suffix in range(1, 6):
            rows = planned_trials(f"{letter}{suffix}")
            assert len(rows) == 10
            assert len({row["item"] for row in rows}) == 10
            assert [row["slot_index"] for row in rows] == list(range(1, 11))


def test_server_material_privacy_headers_and_no_logging(live_server):
    base, _ = live_server
    output = io.StringIO()
    with contextlib.redirect_stderr(output):
        with urllib.request.urlopen(f"{base}/") as response:
            assert response.headers["Content-Security-Policy"] == CSP
            assert response.headers["Cache-Control"] == "no-store"
            assert response.headers.get("Access-Control-Allow-Origin") is None
        bootstrap = request_json(base, "/api/bootstrap")
        materials = locale_materials(base, "zh-Hans")
    bootstrap_encoded = json.dumps(bootstrap, ensure_ascii=False).lower()
    assert "formal" not in bootstrap_encoded and "materials" not in bootstrap
    assert bootstrap["fallback"] is None and bootstrap["auto_detect"] is False
    encoded = json.dumps(materials, ensure_ascii=False).lower()
    for forbidden in (
        "expected_q1", "correct_key", "state_routing_inputs", "router",
        "validation_contract", "render_contract", "export_schema", "q1_key", "q2_key",
        "primitive_evidence", "contract_labels", "flat_labels", "q2_templates",
    ):
        assert forbidden not in encoded
    assert set(materials) == {
        "ui_language", "materials_version", "locale_bundle_version",
        "locale_bundle_hash", "common", "sequence_codes",
    }
    assert materials["ui_language"] == "zh-Hans"
    with pytest.raises(urllib.error.HTTPError):
        request_json(base, "/api/materials")
    assert output.getvalue() == ""


def test_server_strict_state_machine_and_memory_only(live_server):
    base, server = live_server
    with pytest.raises(urllib.error.HTTPError):
        request_json(
            base, "/api/start",
            {"participant_code": "P0", "sequence": "A1"},
        )
    start = request_json(base, "/api/start", {
        "participant_code": "P1", "sequence": "A1", "ui_language": "en",
    })
    attempt = start["attempt_id"]
    with pytest.raises(urllib.error.HTTPError) as exc:
        request_json(base, "/api/q1", {"attempt_id": attempt, "answer": "A"})
    assert exc.value.code == 409
    with pytest.raises(urllib.error.HTTPError):
        request_json(base, "/api/complete", {"attempt_id": attempt})
    assert attempt in server.sessions
    assert not any(RUNTIME.glob("*.json"))
    with pytest.raises(ValueError):
        create_server("0.0.0.0", 0, RUNTIME / "bad.key")


def test_locale_is_locked_and_formal_projection_is_selected_only(live_server):
    base, server = live_server
    welcome = locale_materials(base, "zh-Hans")["common"]
    start = request_json(base, "/api/start", {
        "participant_code": "ZH1", "sequence": "A1", "ui_language": "zh-Hans",
    })
    attempt = start["attempt_id"]
    practice = welcome["practice"]
    request_json(base, "/api/practice", {
        "attempt_id": attempt, "step": "q1",
        "answer": practice["q1"]["options"][0]["id"],
    })
    trial = request_json(base, "/api/practice", {
        "attempt_id": attempt, "step": "q2",
        "answer": practice["q2"]["options"][0]["id"],
    })
    assert server.sessions[attempt]["ui_language"] == "zh-Hans"
    assert set(trial) == {
        "phase", "trial_index", "slot_index", "block", "position", "card",
        "q1", "feedback",
    }
    encoded = json.dumps(trial, ensure_ascii=False)
    assert "模拟评估记录" in encoded
    assert "Simulated evaluation record" not in encoded
    for forbidden in (
        "condition", "stimulus", "primitive", "router", "correct_key",
        "expected_q1", "content_set", "pattern",
    ):
        assert forbidden not in encoded.lower()
    with pytest.raises(urllib.error.HTTPError):
        request_json(base, "/api/q1", {
            "attempt_id": attempt, "answer": trial["q1"]["options"][0]["id"],
            "ui_language": "en",
        })
    assert server.sessions[attempt]["ui_language"] == "zh-Hans"


def test_signed_export_validation_tamper_wrong_key_and_csv(live_server):
    base, _ = live_server
    data = complete_attempt(base)
    assert validate_export(data, TEST_KEY) is data
    assert len(data["trials"]) == 10
    assert data["verification"]["algorithm"] == "HMAC-SHA256"
    assert TEST_KEY.hex() not in json.dumps(data)
    assert data["complete"] is True
    assert data["run_id"] and data["attempt_serial"] >= 1
    assert data["export_schema_version"] == "microstudy-export-v4-bilingual-signed"
    assert data["ui_language"] == "en"
    assert data["locale_bundle_version"].endswith("-en")
    assert len(data["locale_bundle_hash"]) == 64
    tampered = copy.deepcopy(data)
    tampered["participant_code"] = "FORGED"
    with pytest.raises(ExportError, match="signature"):
        validate_export(tampered, TEST_KEY)
    with pytest.raises(ExportError, match="key"):
        validate_export(data, b"x" * 32)
    for field, value in (
        ("ui_language", "fr"),
        ("locale_bundle_version", "wrong"),
        ("locale_bundle_hash", "0" * 64),
    ):
        altered = copy.deepcopy(data)
        altered[field] = value
        altered = sign_export(altered, TEST_KEY)
        with pytest.raises(ExportError, match="locale|language"):
            validate_export(altered, TEST_KEY)
    bad_bool = copy.deepcopy(data)
    bad_bool["practice_presented"] = 1
    bad_bool = sign_export(bad_bool, TEST_KEY)
    with pytest.raises(ExportError, match="boolean"):
        validate_export(bad_bool, TEST_KEY)
    impossible_prefix = copy.deepcopy(data)
    impossible_prefix["trials"][1]["presented"] = False
    impossible_prefix = sign_export(impossible_prefix, TEST_KEY)
    with pytest.raises(ExportError, match="impossible"):
        validate_export(impossible_prefix, TEST_KEY)
    request = urllib.request.Request(
        f"{base}/api/export?attempt_id={data['attempt_id']}&format=csv",
        headers={"X-Study-Capability": CLIENTS[base]["capabilities"][data["attempt_id"]]},
    )
    with urllib.request.urlopen(request) as response:
        csv_bytes = response.read()
    assert csv_bytes.startswith(b"\xef\xbb\xbf")
    csv_text = csv_bytes.decode("utf-8-sig")
    assert csv_text.count("\r\n") == 11
    assert "verification_signature" in csv_text
    assert "ui_language" in csv_text and "locale_bundle_hash" in csv_text


def test_export_ready_is_frozen_retryable_and_retained(live_server):
    base, server = live_server
    data = complete_attempt(base)
    attempt = data["attempt_id"]
    assert server.sessions[attempt]["phase"] == "export_ready"
    first = request_json(base, f"/api/export?attempt_id={attempt}&format=json")
    second = request_json(base, f"/api/export?attempt_id={attempt}&format=json")
    assert first == second == data
    assert server.sessions[attempt]["signed_export"] == data


def test_duplicate_first_complete_then_assignment_and_itt(live_server):
    base, _ = live_server
    first = complete_attempt(base, "P-DUP", "A1")
    later = complete_attempt(base, "P-DUP", "B1", locale="zh-Hans")
    other = complete_attempt(base, "P-OTHER", "D5")
    kept, duplicates = resolve_duplicates([first, later, other])
    assert [row["attempt_id"] for row in kept if row["participant_code"] == "P-DUP"] == [
        first["attempt_id"]
    ]
    assignments = RUNTIME / "assignments.json"
    assignments.write_text(json.dumps({"P-DUP": "D1", "P-OTHER": "D5"}), encoding="utf-8")
    classified, mechanical = apply_assignments(kept, assignments)
    summary = analyze(classified, duplicates, mechanical, duplicates_resolved=True)
    assert summary["kept_attempts"] == 2
    assert summary["input_attempts"] == 3
    assert summary["eligible_primary_n"] == 1
    assert len(summary["participants"]) == 2
    assert summary["missing_as_incorrect_sensitivity"]["mean_difference"] is not None
    assert Counter(row["reason"] for row in summary["rejected"]) == {
        "duplicate_attempt": 1, "sequence_mismatch": 1,
    }
    assert summary["descriptive_locale_qa"] == {
        "kept_counts": {"en": 2},
        "duplicate_locale_conflict_count": 1,
        "duplicate_locale_conflicts": [{
            "participant_code": "P-DUP",
            "excluded_ui_language": "zh-Hans",
            "kept_ui_language": "en",
        }],
        "analysis_role": (
            "descriptive QA only; locale is not used for eligibility, "
            "exclusion, assignment, duplicate winner selection, outcomes, "
            "bootstrap, sign-flip tests, or stratification"
        ),
    }


def test_signed_partial_strict_schema_and_primary_threshold(live_server):
    base, _ = live_server
    partial = partial_attempt(base, completed_trials=9)
    assert validate_export(partial, TEST_KEY) is partial
    assert partial["complete"] is False
    assert partial["completion_status"] == "partial"
    assert len(partial["trials"]) == 10
    assert sum(row["complete"] for row in partial["trials"]) == 9
    summary = analyze([partial], [], duplicates_resolved=True)
    participant = summary["participants"][0]
    assert participant["complete_contract"] >= 4
    assert participant["complete_flat"] >= 4
    assert participant["eligible_primary"] is True
    assert summary["missing_as_incorrect_sensitivity"]["mean_difference"] is not None


def test_cross_run_duplicates_require_explicit_manifest(live_server):
    base, _ = live_server
    first = complete_attempt(base, "P-CROSS", "A1")
    second = complete_attempt(base, "P-CROSS", "B1")
    second["run_id"] = str(uuid.uuid4())
    second = sign_export(second, TEST_KEY)
    validate_export(second, TEST_KEY)
    with pytest.raises(ExportError, match="attempt-order"):
        resolve_duplicates([second, first])
    manifest = RUNTIME / "attempt-order.json"
    manifest.write_text(json.dumps({
        "schema_version": "microstudy-attempt-order-v1",
        "attempt_order": {first["attempt_id"]: 1, second["attempt_id"]: 2},
    }), encoding="utf-8")
    order = load_attempt_order_manifest(manifest)
    kept, excluded = resolve_duplicates([second, first], order)
    assert kept[0]["attempt_id"] == first["attempt_id"]
    assert excluded[0]["attempt_id"] == second["attempt_id"]


def test_request_protection_idempotency_capacity_and_expiry():
    RUNTIME.mkdir(parents=True, exist_ok=True)
    key_path = RUNTIME / "security.key"
    key_path.write_bytes(TEST_KEY)
    server = create_server(
        "127.0.0.1", 0, key_path, max_sessions=1, session_ttl_seconds=0.05
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        bootstrap = request_json(base, "/api/bootstrap")
        assert "csrf_token" in bootstrap and "correct_key" not in json.dumps(bootstrap)
        cross_site_get = urllib.request.Request(
            f"{base}/api/welcome?ui_language=en",
            headers={"Origin": "https://evil.invalid"},
        )
        with pytest.raises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(cross_site_get)
        assert exc.value.code == 403
        for headers in (
            {
                "Content-Type": "text/plain", "Origin": base,
                "X-CSRF-Token": bootstrap["csrf_token"],
            },
            {
                "Content-Type": "application/json", "Origin": "https://evil.invalid",
                "X-CSRF-Token": bootstrap["csrf_token"],
            },
            {"Content-Type": "application/json"},
            {"Content-Type": "application/json", "Origin": base, "X-CSRF-Token": "wrong"},
            {
                "Content-Type": "application/json", "Origin": base,
                "X-CSRF-Token": bootstrap["csrf_token"], "Host": "localhost:1",
            },
        ):
            request = urllib.request.Request(
                f"{base}/api/start",
                data=json.dumps({
                    "participant_code": "SEC", "sequence": "A1",
                    "ui_language": "en", "request_id": uuid.uuid4().hex,
                }).encode(),
                headers=headers, method="POST",
            )
            with pytest.raises(urllib.error.HTTPError):
                urllib.request.urlopen(request)
        start = request_json(base, "/api/start", {
            "participant_code": "SEC", "sequence": "A1", "ui_language": "en",
        })
        attempt = start["attempt_id"]
        oversized = urllib.request.Request(
            f"{base}/api/practice", data=b"{" + b" " * 20_000 + b"}",
            headers={
                "Content-Type": "application/json", "Origin": base,
                "X-CSRF-Token": bootstrap["csrf_token"],
                "X-Study-Capability": start["capability"],
            },
            method="POST",
        )
        with pytest.raises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(oversized)
        assert exc.value.code == 409
        missing_capability = urllib.request.Request(
            f"{base}/api/practice",
            data=json.dumps({
                "attempt_id": attempt, "step": "q1", "answer": "Q1_A",
                "request_id": uuid.uuid4().hex,
            }).encode(),
            headers={
                "Content-Type": "application/json", "Origin": base,
                "X-CSRF-Token": bootstrap["csrf_token"],
            },
            method="POST",
        )
        with pytest.raises(urllib.error.HTTPError):
            urllib.request.urlopen(missing_capability)
        with pytest.raises(urllib.error.HTTPError):
            request_json(base, "/api/start", {
                "participant_code": "FLOOD", "sequence": "A2", "ui_language": "en",
            })
        time.sleep(0.07)
        replacement = request_json(base, "/api/start", {
            "participant_code": "AFTER", "sequence": "A2", "ui_language": "zh-Hans",
        })
        assert replacement["attempt_id"] != attempt
        assert attempt not in server.sessions
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
        CLIENTS.pop(base, None)
        shutil.rmtree(RUNTIME, ignore_errors=True)


def test_server_restart_changes_run_id_and_resets_serial():
    RUNTIME.mkdir(parents=True, exist_ok=True)
    key_path = RUNTIME / "restart.key"
    key_path.write_bytes(TEST_KEY)
    observed = []
    for participant in ("R1", "R2"):
        server = create_server("127.0.0.1", 0, key_path)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            request_json(base, "/api/bootstrap")
            start = request_json(base, "/api/start", {
                "participant_code": participant, "sequence": "A1",
                "ui_language": "en",
            })
            observed.append((start["run_id"], start["attempt_serial"]))
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
            CLIENTS.pop(base, None)
    assert observed[0][0] != observed[1][0]
    assert observed[0][1] == observed[1][1] == 1
    shutil.rmtree(RUNTIME, ignore_errors=True)


def test_concurrent_q1_same_request_is_exactly_once(live_server):
    base, server = live_server
    materials = locale_materials(base, "en")["common"]
    start = request_json(base, "/api/start", {
        "participant_code": "RACE", "sequence": "A1", "ui_language": "en",
    })
    attempt = start["attempt_id"]
    practice = materials["practice"]
    request_json(base, "/api/practice", {
        "attempt_id": attempt, "step": "q1",
        "answer": practice["q1"]["options"][0]["id"],
    })
    current = request_json(base, "/api/practice", {
        "attempt_id": attempt, "step": "q2",
        "answer": practice["q2"]["options"][0]["id"],
    })
    request_id = uuid.uuid4().hex
    payload = json.dumps({
        "attempt_id": attempt, "answer": current["q1"]["options"][0]["id"],
        "request_id": request_id,
    }).encode()
    headers = {
        "Content-Type": "application/json", "Origin": base,
        "X-CSRF-Token": CLIENTS[base]["csrf"],
        "X-Study-Capability": CLIENTS[base]["capabilities"][attempt],
    }
    results = []
    barrier = threading.Barrier(3)

    def send():
        barrier.wait()
        request = urllib.request.Request(f"{base}/api/q1", data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(request) as response:
            results.append(json.load(response))

    workers = [threading.Thread(target=send) for _ in range(2)]
    for worker in workers:
        worker.start()
    barrier.wait()
    for worker in workers:
        worker.join()
    assert results[0] == results[1]
    session = server.sessions[attempt]
    assert session["phase"] == "q2"
    assert session["trials"][0]["q1_submitted"] is True
    assert len([key for key in session["requests"] if key[0] == "/api/q1"]) == 1
    altered = json.dumps({
        "attempt_id": attempt, "answer": current["q1"]["options"][1]["id"],
        "request_id": request_id,
    }).encode()
    with pytest.raises(urllib.error.HTTPError):
        urllib.request.urlopen(urllib.request.Request(
            f"{base}/api/q1", data=altered, headers=headers, method="POST"
        ))
    assert session["phase"] == "q2"


def test_load_exports_rejects_corrupt_unsigned_and_unknown_fields(live_server):
    base, _ = live_server
    data = complete_attempt(base)
    RUNTIME.mkdir(parents=True, exist_ok=True)
    good = RUNTIME / "good.json"
    unsigned = RUNTIME / "unsigned.json"
    unknown = RUNTIME / "unknown.json"
    corrupt = RUNTIME / "corrupt.json"
    good.write_text(json.dumps(data), encoding="utf-8")
    unsigned.write_text(json.dumps({k: v for k, v in data.items() if k != "verification"}), encoding="utf-8")
    value = copy.deepcopy(data)
    value["attempt_id"] = str(uuid.uuid4())
    value["unexpected"] = True
    unknown.write_text(json.dumps(sign_export(value, TEST_KEY)), encoding="utf-8")
    corrupt.write_text("{", encoding="utf-8")
    valid, rejected = load_exports([good, unsigned, unknown, corrupt], TEST_KEY)
    assert len(valid) == 1
    assert Counter(row["reason"] for row in rejected) == {
        "technical_corrupt": 3,
    }


def test_load_exports_deduplicates_same_path_and_identical_copy(live_server):
    base, _ = live_server
    data = complete_attempt(base)
    RUNTIME.mkdir(parents=True, exist_ok=True)
    original = RUNTIME / "attempt.json"
    copied = RUNTIME / "attempt-copy.json"
    encoded = json.dumps(data, sort_keys=True)
    original.write_text(encoded, encoding="utf-8")
    copied.write_text(encoded, encoding="utf-8")
    valid, rejected = load_exports([original, original, copied], TEST_KEY)
    assert len(valid) == 1
    assert rejected == []


def test_load_exports_hard_fails_v3_v4_mixing(live_server):
    base, _ = live_server
    current = complete_attempt(base)
    legacy = copy.deepcopy(current)
    legacy["attempt_id"] = str(uuid.uuid4())
    legacy["export_schema_version"] = "microstudy-export-v3-signed"
    legacy = sign_export(legacy, TEST_KEY)
    RUNTIME.mkdir(parents=True, exist_ok=True)
    current_path = RUNTIME / "current.json"
    legacy_path = RUNTIME / "legacy.json"
    current_path.write_text(json.dumps(current), encoding="utf-8")
    legacy_path.write_text(json.dumps(legacy), encoding="utf-8")
    with pytest.raises(ExportError, match="v3/v4"):
        load_exports([current_path, legacy_path], TEST_KEY)


def test_load_exports_hard_fails_attempt_id_conflict(live_server):
    base, _ = live_server
    data = complete_attempt(base)
    conflicting = copy.deepcopy(data)
    conflicting["participant_code"] = "CONFLICT"
    conflicting = sign_export(conflicting, TEST_KEY)
    RUNTIME.mkdir(parents=True, exist_ok=True)
    first = RUNTIME / "first.json"
    second = RUNTIME / "second.json"
    first.write_text(json.dumps(data), encoding="utf-8")
    second.write_text(json.dumps(conflicting), encoding="utf-8")
    with pytest.raises(ExportError, match="conflicting payload or signature"):
        load_exports([first, second], TEST_KEY)
    signature_conflict = copy.deepcopy(data)
    signature_conflict["verification"]["signature"] = "0" * 64
    second.write_text(json.dumps(signature_conflict), encoding="utf-8")
    with pytest.raises(ExportError, match="conflicting payload or signature"):
        load_exports([first, second], TEST_KEY)


def test_static_dom_accessibility_and_no_semantic_attributes():
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    css = (STATIC_DIR / "study.css").read_text(encoding="utf-8")
    js = (STATIC_DIR / "study.js").read_text(encoding="utf-8")
    combined = html + css + js
    for forbidden in (
        "localStorage", "sessionStorage", "indexedDB", "document.cookie",
        "serviceWorker", "data-condition", "data-stimulus-id", "data-evidence-id",
        "navigator.language", "navigator.languages", "location.search",
    ):
        assert forbidden not in combined
    assert '<html lang="und">' in html
    assert "请选择语言 / Choose a language" in html
    assert 'id="language-gate"' in html
    assert 'id="participant-code"' not in html
    assert "cardData.aria_label" in js
    assert "document.documentElement.lang = app.locale" in js
    assert "heading.focus()" in js
    assert js.count('document.addEventListener("click"') == 1
    assert "correct_key" not in js and "q1_key" not in js and "q2_key" not in js
    assert "Microsoft YaHei" in css and "overflow-wrap:anywhere" in css
    assert "focus-visible" in css and "prefers-reduced-motion" in css


def test_exact_sign_flip_ties_and_equality():
    assert exact_sign_flip([0, 0]) == {"n_eff": 0, "ties": 2, "p": 1.0}
    assert exact_sign_flip([0.2, 0.2])["p"] == 0.25


def _free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def test_real_chrome_edge_full_partial_isolated_server_gate():
    pytest.importorskip("websocket")
    from browser_cdp import CDP

    candidates = {
        "edge": Path(os.environ.get(
            "EDGE_PATH", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        )),
        "chrome": Path(os.environ.get(
            "CHROME_PATH", r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        )),
    }
    browsers = {name: path for name, path in candidates.items() if path.exists()}
    assert browsers, "Chrome or Edge is required for the real-browser gate"
    RUNTIME.mkdir(parents=True, exist_ok=True)
    downloads = RUNTIME / "downloads"
    screenshots = RUNTIME / "screenshots"
    downloads.mkdir(exist_ok=True)
    screenshots.mkdir(exist_ok=True)

    @contextlib.contextmanager
    def isolated_server(label):
        key_path = RUNTIME / f"{label}-{uuid.uuid4().hex}.key"
        key_path.write_bytes(TEST_KEY)
        server = create_server("127.0.0.1", 0, key_path)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        deadline = time.time() + 10
        while True:
            try:
                with urllib.request.urlopen(f"{base}/api/bootstrap") as response:
                    assert response.status == 200
                break
            except OSError:
                if time.time() > deadline:
                    pytest.fail(f"{label} server readiness timed out")
                time.sleep(0.05)
        try:
            yield base, server
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=10)
            assert not thread.is_alive()
            CLIENTS.pop(base, None)

    @contextlib.contextmanager
    def browser_process(name, executable):
        port = _free_port()
        profile = RUNTIME / f"{name}-profile-{uuid.uuid4().hex}"
        profile.mkdir()
        stderr_path = RUNTIME / f"{name}-{uuid.uuid4().hex}.stderr.txt"
        stderr_handle = stderr_path.open("w+", encoding="utf-8")
        process = subprocess.Popen([
            str(executable), "--headless=new", "--no-sandbox", "--disable-gpu",
            "--no-first-run", "--disable-features=msEdgeFirstRunExperience",
            "--no-default-browser-check", "--remote-allow-origins=*",
            f"--remote-debugging-port={port}", f"--user-data-dir={profile.resolve()}",
            "about:blank",
        ], stdout=subprocess.DEVNULL, stderr=stderr_handle)
        deadline = time.time() + 15
        while True:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version"):
                    break
            except OSError:
                if time.time() > deadline:
                    stderr_handle.flush()
                    pytest.fail(
                        f"{name} CDP failed (exit={process.poll()}): "
                        f"{stderr_path.read_text(encoding='utf-8')}"
                    )
                time.sleep(0.1)
        try:
            yield port
        finally:
            try:
                control = CDP.new_page(port, "about:blank")
                control.call("Browser.close")
                control.socket.close()
            except Exception:
                if process.poll() is None:
                    process.terminate()
            if process.poll() is None:
                process.wait(timeout=10)
            stderr_handle.close()

    def press(cdp, key, code, virtual_key):
        params = {
            "key": key, "code": code, "windowsVirtualKeyCode": virtual_key,
            "text": "\r" if key == "Enter" else (key if key == " " else ""),
        }
        cdp.call("Input.dispatchKeyEvent", {"type": "keyDown", **params})
        cdp.call("Input.dispatchKeyEvent", {"type": "keyUp", **params})

    def start_formal(cdp, participant, sequence, locale="en", keyboard=False):
        cdp.wait(
            "window.MicrostudyTest"
            " && document.querySelector('[data-action=\"choose-language\"]')"
        )
        if keyboard:
            cdp.eval(
                f"document.querySelector('[data-locale=\"{locale}\"]').focus()"
            )
            press(cdp, "Enter", "Enter", 13)
        else:
            cdp.eval(
                f"document.querySelector('[data-locale=\"{locale}\"]').click()"
            )
        cdp.wait("document.querySelector('#sequence option')")
        assert cdp.eval("document.documentElement.lang") == locale
        assert cdp.eval("!document.querySelector('#language-gate')")
        cdp.eval(
            f"document.querySelector('#participant-code').value={json.dumps(participant)};"
            "document.querySelector('#participant-code').focus();"
            f"document.querySelector('#sequence').value={json.dumps(sequence)};"
        )
        if keyboard:
            press(cdp, "Tab", "Tab", 9)
            press(cdp, "Tab", "Tab", 9)
            assert cdp.eval("document.activeElement.id") == "start-button"
            press(cdp, "Enter", "Enter", 13)
        else:
            cdp.eval("document.querySelector('#start-button').click()")
        cdp.wait("document.querySelector('[data-action=\"show-practice\"]')")
        cdp.click("show-practice")
        cdp.choose_and_click("practice-q1", "practice-q1")
        cdp.choose_and_click("practice-q2", "practice-q2")
        cdp.wait("document.querySelector('[data-action=\"begin-formal\"]')")
        cdp.click("begin-formal")

    def finish_formal(
        cdp, locale, audit_geometry=False, screenshot_prefix=None
    ):
        captured = set()
        for index in range(10):
            cdp.wait(
                "document.querySelector('[data-action=\"formal-q1\"]')"
                " && !document.querySelector('[data-action=\"formal-q1\"]').disabled"
            )
            if audit_geometry:
                audit = cdp.eval("""(() => {
                  const card=document.querySelector('.evidence-card');
                  const rows=[...document.querySelectorAll('.evidence-row')];
                  const labels=rows.map(r=>r.querySelector('.evidence-label').innerText);
                  const forbidden=[...document.querySelectorAll('*')].flatMap(node =>
                    [...node.attributes].map(a=>a.name)).filter(name =>
                    /condition|stimulus|evidence-id|answer|correct|router/i.test(name));
                  return {
                    aria:card.getAttribute('aria-label'), labels,
                    cardWidth:card.getBoundingClientRect().width,
                    cardOverflow:card.scrollWidth>card.clientWidth,
                    documentOverflow:document.documentElement.scrollWidth>
                      document.documentElement.clientWidth,
                    rowHeights:rows.map(r=>r.getBoundingClientRect().height),
                    labelWidths:rows.map(r=>r.querySelector('dt').getBoundingClientRect().width),
                    bodyWidths:rows.map(r=>r.querySelector('dd').getBoundingClientRect().width),
                    labelFonts:rows.map(r=>parseFloat(getComputedStyle(r.querySelector('dt')).fontSize)),
                    bodyFonts:rows.map(r=>parseFloat(getComputedStyle(r.querySelector('dd')).fontSize)),
                    forbidden, saveVisible:!document.querySelector('#save-exit-button').hidden
                  };
                })()""")
                expected_aria = "证据面板" if locale == "zh-Hans" else "Evidence panel"
                assert audit["aria"] == expected_aria and audit["saveVisible"]
                assert not audit["cardOverflow"] and not audit["documentOverflow"]
                assert audit["cardWidth"] <= 961
                assert all(value >= 71 for value in audit["rowHeights"])
                assert all(abs(value - 240) <= 1 for value in audit["labelWidths"])
                assert all(abs(value - 648) <= 1 for value in audit["bodyWidths"])
                assert audit["labelFonts"] == [14] * 5
                assert audit["bodyFonts"] == [16] * 5
                assert not audit["forbidden"]
                condition = (
                    "flat"
                    if audit["labels"][0].startswith(("Evidence ", "证据 "))
                    else "contract"
                )
                if condition not in captured:
                    result = cdp.call("Page.captureScreenshot", {
                        "format": "png", "captureBeyondViewport": False,
                    })
                    content = base64.b64decode(result["data"])
                    path = screenshots / f"{screenshot_prefix}-{condition}.png"
                    path.write_bytes(content)
                    assert content[:8] == b"\x89PNG\r\n\x1a\n" and len(content) > 5000
                    captured.add(condition)
            cdp.choose_and_click("formal-q1", "formal-q1")
            cdp.choose_and_click("formal-q2", "formal-q2")
            if index in (4, 9):
                cdp.wait("document.querySelector('[data-action=\"ease-skip\"]')")
                cdp.click("ease-skip")
        cdp.wait("document.querySelector('[data-action=\"diagnostic-skip\"]')")
        cdp.click("diagnostic-skip")
        cdp.wait("document.querySelector('[data-action=\"download-json\"]')")
        assert cdp.eval("document.querySelector('[data-action=\"download-csv\"]') !== null")
        assert cdp.eval("document.querySelector('[data-action=\"finish\"]') !== null")
        if audit_geometry:
            assert captured == {"contract", "flat"}
            body = cdp.eval("document.body.innerText")
            if locale == "en":
                assert "模拟评估记录" not in body
            else:
                assert "Simulated evaluation record" not in body

    def assert_manual_downloads(cdp, server):
        before_json = len(list(downloads.glob("*.json")))
        before_csv = len(list(downloads.glob("*.csv")))
        time.sleep(0.2)
        assert len(list(downloads.glob("*.json"))) == before_json
        assert len(list(downloads.glob("*.csv"))) == before_csv
        attempt = next(iter(server.sessions))
        capability = server.sessions[attempt]["capability"]
        server.sessions[attempt]["capability"] = "temporarily-invalid"
        cdp.click("download-json")
        cdp.wait("document.querySelector('#stage-error').textContent.length > 0")
        assert cdp.eval(
            "document.querySelector('#stage-error').getAttribute('role') === 'alert'"
            " && document.querySelector('[data-action=\"download-json\"]') !== null"
            " && document.querySelector('[data-action=\"download-csv\"]') !== null"
        )
        server.sessions[attempt]["capability"] = capability
        cdp.click("download-json")
        cdp.click("download-csv")
        deadline = time.time() + 10
        while (
            len(list(downloads.glob("*.json"))) <= before_json
            or len(list(downloads.glob("*.csv"))) <= before_csv
        ):
            if time.time() > deadline:
                pytest.fail("manual browser downloads did not complete")
            time.sleep(0.1)

    geometry_cases = [
        ("A1", "en", 1280, 800, 1), ("D5", "zh-Hans", 1280, 800, 2),
        ("A1", "zh-Hans", 1440, 900, 2), ("D5", "en", 1440, 900, 1),
    ]
    stress_iterations = int(os.environ.get("MICROSTUDY_BROWSER_STRESS_ITERATIONS", "1"))
    try:
        for browser_name, executable in browsers.items():
            with browser_process(browser_name, executable) as port:
                for case_index, (sequence, locale, width, height, zoom) in enumerate(geometry_cases):
                    label = f"{browser_name}-{locale}-{sequence}-{width}-z{zoom}"
                    with isolated_server(label) as (base, server):
                        cdp = CDP.new_page(port, f"{base}/")
                        try:
                            cdp.call("Browser.setDownloadBehavior", {
                                "behavior": "allow", "downloadPath": str(downloads),
                            })
                            cdp.call("Emulation.setDeviceMetricsOverride", {
                                "width": width, "height": height,
                                "deviceScaleFactor": 1, "mobile": False,
                            })
                            cdp.call("Emulation.setPageScaleFactor", {"pageScaleFactor": zoom})
                            start_formal(
                                cdp, f"G{case_index}{browser_name[0]}",
                                sequence, locale, True,
                            )
                            finish_formal(cdp, locale, True, label)
                            assert_manual_downloads(cdp, server)
                        finally:
                            cdp.close()
                label = f"{browser_name}-refresh-language-reset"
                with isolated_server(label) as (base, server):
                    cdp = CDP.new_page(port, f"{base}/")
                    try:
                        cdp.wait(
                            "window.MicrostudyTest"
                            " && document.querySelector('[data-locale=\"en\"]')"
                        )
                        cdp.click("choose-language")
                        cdp.wait("document.documentElement.lang === 'zh-Hans'")
                        cdp.click("switch-language")
                        cdp.wait("document.documentElement.lang === 'en'")
                        start_button = "document.querySelector('#start-button')"
                        cdp.eval(
                            "document.querySelector('#participant-code').value='REFRESH';"
                            "document.querySelector('#sequence').value='A1';"
                            f"{start_button}.click()"
                        )
                        cdp.wait(
                            "document.querySelector('[data-action=\"show-practice\"]')"
                        )
                        attempt = next(iter(server.sessions))
                        cdp.call("Page.reload", {"ignoreCache": True})
                        cdp.wait(
                            "window.MicrostudyTest"
                            " && document.querySelector('#language-gate')"
                        )
                        assert cdp.eval("document.documentElement.lang") == "und"
                        assert cdp.eval("!document.querySelector('#participant-code')")
                        assert attempt in server.sessions
                    finally:
                        cdp.close()
                for iteration in range(stress_iterations):
                    sequence = "A1" if iteration % 2 == 0 else "D5"
                    locale = "en" if iteration % 2 == 0 else "zh-Hans"
                    label = f"{browser_name}-stress-full-{iteration}"
                    with isolated_server(label) as (base, _):
                        cdp = CDP.new_page(port, f"{base}/")
                        try:
                            cdp.call("Browser.setDownloadBehavior", {
                                "behavior": "allow", "downloadPath": str(downloads),
                            })
                            start_formal(
                                cdp, f"SF{iteration}{browser_name[0]}",
                                sequence, locale,
                            )
                            finish_formal(cdp, locale)
                        finally:
                            cdp.close()
                    label = f"{browser_name}-stress-partial-{iteration}"
                    with isolated_server(label) as (base, server):
                        cdp = CDP.new_page(port, f"{base}/")
                        try:
                            cdp.call("Browser.setDownloadBehavior", {
                                "behavior": "allow", "downloadPath": str(downloads),
                            })
                            start_formal(
                                cdp, f"SP{iteration}{browser_name[0]}",
                                sequence, locale,
                            )
                            cdp.wait("!document.querySelector('#save-exit-button').hidden")
                            attempt = next(iter(server.sessions))
                            cdp.click("save-exit")
                            cdp.wait(
                                "document.querySelector('[data-action=\"download-json\"]')"
                            )
                            time.sleep(0.2)
                            assert not list(downloads.glob(f"microstudy-{attempt}.*"))
                            assert cdp.eval(
                                "document.querySelector('[data-action=\"download-json\"]') !== null"
                            )
                            assert cdp.eval(
                                "document.querySelector('[data-action=\"download-json\"]') !== null"
                                " && document.querySelector('[data-action=\"download-csv\"]') !== null"
                            )
                            assert server.sessions[attempt]["phase"] == "export_ready"
                            assert_manual_downloads(cdp, server)
                            cdp.click("finish")
                            cdp.wait(
                                "!document.querySelector('[data-action=\"download-json\"]')"
                            )
                            assert attempt in server.sessions
                        finally:
                            cdp.close()
        assert len(list(screenshots.glob("*.png"))) == len(browsers) * 8
        validated = [
            validate_export(json.loads(path.read_text(encoding="utf-8")), TEST_KEY)
            for path in downloads.glob("*.json")
        ]
        assert any(data["complete"] is False for data in validated)
        assert any(data["complete"] is True for data in validated)
    finally:
        shutil.rmtree(RUNTIME, ignore_errors=True)
