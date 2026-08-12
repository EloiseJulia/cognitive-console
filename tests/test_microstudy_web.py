import base64
import contextlib
import copy
import io
import json
import os
import re
import shutil
import socket
import struct
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
    exact_sign_flip,
    load_assignments,
    load_attempt_order_manifest,
    load_exports,
    resolve_duplicates,
    validate_export,
)
from cognitive_console.microstudy.materials import material_hashes, planned_trials
from cognitive_console.microstudy.server import (
    CSP,
    STATIC_DIR,
    StudyHandler,
    create_server,
    load_or_create_key,
    sign_export,
)
import cognitive_console.microstudy.server as microstudy_server
from cognitive_console.microstudy_materials import (
    EXPORT_SCHEMA_VERSION,
    MATERIAL_SCHEMA_VERSION,
    MATERIALS_VERSION,
    SEQUENCE_SCHEMA_VERSION,
)


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / ".runtime" / "tests-v9"
TEST_KEY = b"microstudy-test-key-32-bytes-long!!"
CLIENTS: dict[str, dict] = {}


def test_verification_key_permission_paths_are_fail_closed(monkeypatch):
    shutil.rmtree(RUNTIME, ignore_errors=True)
    RUNTIME.mkdir(parents=True)

    windows_key = RUNTIME / "windows-failure.key"

    def deny_windows_acl(path):
        raise PermissionError("ACL denied")

    monkeypatch.setattr(microstudy_server, "_is_windows", lambda: True)
    monkeypatch.setattr(
        microstudy_server,
        "_restrict_windows_key_permissions",
        deny_windows_acl,
    )
    with pytest.raises(PermissionError, match="ACL denied"):
        load_or_create_key(windows_key)
    assert not windows_key.exists()

    existing_windows_key = RUNTIME / "existing-windows-failure.key"
    existing_windows_key.write_bytes(TEST_KEY)
    with pytest.raises(PermissionError, match="ACL denied"):
        load_or_create_key(existing_windows_key)
    assert not existing_windows_key.exists()

    posix_failure_key = RUNTIME / "posix-failure.key"
    monkeypatch.setattr(microstudy_server, "_is_windows", lambda: False)

    def deny_posix_mode(path, mode):
        raise PermissionError("chmod denied")

    monkeypatch.setattr(microstudy_server.os, "chmod", deny_posix_mode)
    with pytest.raises(PermissionError, match="chmod denied"):
        load_or_create_key(posix_failure_key)
    assert not posix_failure_key.exists()

    posix_key = RUNTIME / "posix.key"
    chmod_calls = []
    monkeypatch.setattr(
        microstudy_server.os,
        "chmod",
        lambda path, mode: chmod_calls.append((path, mode)),
    )
    monkeypatch.setattr(
        microstudy_server,
        "_key_mode",
        lambda path: 0o600,
    )
    assert load_or_create_key(posix_key)
    assert chmod_calls == [(posix_key, 0o600)]
    shutil.rmtree(RUNTIME, ignore_errors=True)


@pytest.mark.skipif(os.name != "nt", reason="Windows ACL verification")
def test_windows_verification_key_acl_is_current_user_only():
    shutil.rmtree(RUNTIME, ignore_errors=True)
    RUNTIME.mkdir(parents=True)
    key_path = RUNTIME / "owner-only.key"
    try:
        assert len(load_or_create_key(key_path)) == 32
        script = r"""
$path = [Environment]::GetEnvironmentVariable('KEY_PATH', 'Process')
$sid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
$sections = (
    [System.Security.AccessControl.AccessControlSections]::Access -bor
    [System.Security.AccessControl.AccessControlSections]::Owner
)
$acl = [System.Security.AccessControl.FileSecurity]::new($path, $sections)
$rules = @($acl.GetAccessRules(
    $true,
    $true,
    [System.Security.Principal.SecurityIdentifier]
))
$result = [ordered]@{
    owner = $acl.GetOwner(
        [System.Security.Principal.SecurityIdentifier]
    ).Value
    current = $sid.Value
    count = $rules.Count
    inherited = $rules[0].IsInherited
    rule_sid = $rules[0].IdentityReference.Value
}
$result | ConvertTo-Json -Compress
"""
        environment = os.environ.copy()
        environment["KEY_PATH"] = str(key_path.resolve())
        completed = subprocess.run(
            [
                "powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive",
                "-Command", script,
            ],
            capture_output=True,
            text=True,
            env=environment,
            check=True,
        )
        acl = json.loads(completed.stdout)
        assert acl == {
            "owner": acl["current"],
            "current": acl["current"],
            "count": 1,
            "inherited": False,
            "rule_sid": acl["current"],
        }
    finally:
        shutil.rmtree(RUNTIME, ignore_errors=True)


def request_json(base, path, body=None, *, headers=None):
    client = CLIENTS.setdefault(base, {"csrf": None, "capabilities": {}})
    request_headers = dict(headers or {})
    data = None
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
        f"{base}{path}",
        data=data,
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
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        request_json(base, "/api/bootstrap")
        yield base, server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=10)
        assert not thread.is_alive()
        shutil.rmtree(RUNTIME, ignore_errors=True)
        CLIENTS.pop(base, None)


def locale_materials(base, locale="en"):
    return request_json(base, f"/api/welcome?ui_language={locale}")


def start_formal_http(base, participant, sequence, locale):
    common = locale_materials(base, locale)["common"]
    start = request_json(base, "/api/start", {
        "participant_code": participant,
        "sequence": sequence,
        "ui_language": locale,
    })
    attempt = start["attempt_id"]
    request_json(base, "/api/practice", {
        "attempt_id": attempt,
        "step": "q1",
        "answer": common["q1"]["options"][0]["id"],
    })
    current = request_json(base, "/api/practice", {
        "attempt_id": attempt,
        "step": "q2",
        "answer": common["practice"]["q2_options"][0]["id"],
    })
    return attempt, common, current


def complete_attempt(base, participant="P001", sequence="V9-01", locale="en"):
    attempt, _, current = start_formal_http(base, participant, sequence, locale)
    for _ in range(6):
        q2 = request_json(base, "/api/q1", {
            "attempt_id": attempt,
            "answer": current["q1"]["options"][0]["id"],
        })
        response = request_json(base, "/api/q2", {
            "attempt_id": attempt,
            "answer": q2["q2"]["options"][0]["id"],
            "hidden_ms": 0,
        })
        assert response["phase"] == "preview"
        current = request_json(base, "/api/continue", {"attempt_id": attempt})
    assert current["phase"] == "ready_complete"
    request_json(base, "/api/complete", {"attempt_id": attempt})
    return request_json(base, f"/api/export?attempt_id={attempt}&format=json")


def partial_attempt(
    base,
    completed_trials=5,
    participant="P-PARTIAL",
    sequence="V9-01",
    locale="en",
):
    attempt, _, current = start_formal_http(base, participant, sequence, locale)
    for index in range(completed_trials):
        q2 = request_json(base, "/api/q1", {
            "attempt_id": attempt,
            "answer": current["q1"]["options"][0]["id"],
        })
        request_json(base, "/api/q2", {
            "attempt_id": attempt,
            "answer": q2["q2"]["options"][0]["id"],
            "hidden_ms": 0,
        })
        if index + 1 < completed_trials:
            current = request_json(base, "/api/continue", {"attempt_id": attempt})
    request_json(base, "/api/save-exit", {"attempt_id": attempt})
    return request_json(base, f"/api/export?attempt_id={attempt}&format=json")


def test_material_hashes_and_all_v9_sequences_are_deterministic():
    assert set(material_hashes()) == {
        "materials_sha256", "sequences_sha256", "source_registry_sha256"
    }
    cells = Counter()
    for number in range(1, 13):
        rows = planned_trials(f"V9-{number:02d}")
        assert len(rows) == 6
        assert len({row["ticket_code"] for row in rows}) == 6
        assert [row["slot_index"] for row in rows] == list(range(1, 7))
        assert Counter(row["condition"] for row in rows) == {"C": 3, "F": 3}
        for row in rows:
            cells[row["ticket_code"], row["condition"], row["position"]] += 1
    assert len(cells) == 72 and set(cells.values()) == {1}


def test_server_material_privacy_headers_common_policy_and_no_logging(live_server):
    base, _ = live_server
    output = io.StringIO()
    with contextlib.redirect_stderr(output):
        with urllib.request.urlopen(f"{base}/") as response:
            assert response.headers["Content-Security-Policy"] == CSP
            assert response.headers["Cache-Control"] == "no-store"
            assert response.headers.get("Access-Control-Allow-Origin") is None
        bootstrap = request_json(base, "/api/bootstrap")
        english = locale_materials(base, "en")
        chinese = locale_materials(base, "zh-Hans")
    bootstrap_text = json.dumps(bootstrap, ensure_ascii=False).lower()
    assert "ticket" not in bootstrap_text and "materials" not in bootstrap
    assert bootstrap["fallback"] is None
    assert bootstrap["auto_detect"] is False
    assert bootstrap["minimum_width_px"] == 1280
    assert set(english) == {
        "ui_language", "common", "sequence_codes",
    }
    assert english["sequence_codes"] == [f"V9-{index:02d}" for index in range(1, 13)]
    for projected, headings in (
        (english, (
            "Can the behavior be identified?",
            "How does the knob compare with direct prompting?",
            "What could weaken or limit the result?",
            "Where does this evidence apply?",
        )),
        (chinese, (
            "能否识别这种行为？", "旋钮与直接提示相比如何？",
            "哪些因素可能削弱或限制结果？", "这些证据适用于哪里？",
        )),
    ):
        encoded = json.dumps(projected, ensure_ascii=False)
        assert "contract_headings" not in encoded
        assert not any(heading in encoded for heading in headings)
        for forbidden in (
            "policy_inputs", "decisive_issue", "expected_q1", "expected_q2",
            "correct_key", "q1_key", "q2_key", "flat_order", "tickets",
            "render_contract", "export_schema", "locale_bundle_hash",
            "locale_bundle_version", "materials_version", "source_details",
            "source_id", "canonical_sha256", "hash_basis", "commit",
        ):
            assert f'"{forbidden}":' not in encoded
    with pytest.raises(urllib.error.HTTPError):
        request_json(base, "/api/materials")
    assert output.getvalue() == ""


def test_server_strict_state_machine_and_memory_only(live_server):
    base, server = live_server
    with pytest.raises(urllib.error.HTTPError):
        request_json(base, "/api/start", {
            "participant_code": "P0",
            "sequence": "V9-01",
        })
    start = request_json(base, "/api/start", {
        "participant_code": "P1",
        "sequence": "V9-01",
        "ui_language": "en",
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


def test_locale_locked_formal_projection_and_contract_flat_parity(live_server):
    base, server = live_server
    first_attempt, _, contract = start_formal_http(
        base, "ZH-C", "V9-01", "zh-Hans"
    )
    second_attempt, _, flat = start_formal_http(
        base, "ZH-F", "V9-07", "zh-Hans"
    )
    assert server.sessions[first_attempt]["ui_language"] == "zh-Hans"
    assert contract["ticket_code"] == flat["ticket_code"] == "DELIB-R"
    assert "groups" in contract["card"] and "rows" in flat["card"]
    contract_bodies = [
        fact for group in contract["card"]["groups"] for fact in group["facts"]
    ]
    flat_bodies = [row["body"] for row in flat["card"]["rows"]]
    assert sorted(contract_bodies) == sorted(flat_bodies)
    for field in ("product", "source_badge", "outputs", "q1"):
        assert contract[field] == flat[field]
    assert [len(group["facts"]) for group in contract["card"]["groups"]] == [1, 2, 2, 1]
    assert [row["label"] for row in flat["card"]["rows"]] == [
        f"证据 {letter}" for letter in "ABCDEF"
    ]
    for projection in (contract, flat):
        encoded = json.dumps(projection, ensure_ascii=False)
        assert "Illustrative" not in encoded
        assert "ILLUSTRATIVE OUTPUT" in encoded
        assert "condition" not in encoded.lower()
        for forbidden in (
            "policy_inputs", "decisive_issue", "correct_key", "q1_key", "q2_key",
            "expected_q1", "expected_q2", "Q2_DECISIVE_PAIRED_TEST",
            "source_details", "source_id", "canonical_sha256", "hash_basis",
            "commit", "locale_bundle_hash",
        ):
            assert forbidden not in encoded
        assert not re.search(
            r"\b(?:CAA|ITI|CI|MDE|Brier|Qwen|Llama)\b|"
            r"1[−-]Brier|facade ratio|residual norm|残差范数|表征比|"
            r"(?<![\w.])[+-]?\d+\.\d+",
            encoded,
            flags=re.IGNORECASE,
        )


def test_signed_v5_export_validation_tamper_wrong_key_and_csv(live_server):
    base, _ = live_server
    data = complete_attempt(base)
    assert validate_export(data, TEST_KEY) is data
    assert len(data["trials"]) == 6
    assert data["complete"] is True
    assert data["completion_status"] == "complete"
    assert data["export_schema_version"] == EXPORT_SCHEMA_VERSION
    assert data["material_schema_version"] == MATERIAL_SCHEMA_VERSION
    assert data["sequence_schema_version"] == SEQUENCE_SCHEMA_VERSION
    assert data["ui_language"] == "en"
    assert data["locale_bundle_version"].endswith("-en")
    assert len(data["locale_bundle_hash"]) == 64
    assert TEST_KEY.hex() not in json.dumps(data)
    assert not any("condition" in trial for trial in data["trials"])
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
        ("material_schema_version", "microstudy-stimuli-v8-bilingual-novice-ux"),
    ):
        altered = copy.deepcopy(data)
        altered[field] = value
        altered = sign_export(altered, TEST_KEY)
        with pytest.raises(ExportError, match="locale|language|material schema"):
            validate_export(altered, TEST_KEY)
    bad_bool = copy.deepcopy(data)
    bad_bool["practice_presented"] = 1
    with pytest.raises(ExportError, match="boolean"):
        validate_export(sign_export(bad_bool, TEST_KEY), TEST_KEY)
    impossible = copy.deepcopy(data)
    impossible["trials"][1]["presented"] = False
    with pytest.raises(ExportError, match="presented|prefix"):
        validate_export(sign_export(impossible, TEST_KEY), TEST_KEY)
    request = urllib.request.Request(
        f"{base}/api/export?attempt_id={data['attempt_id']}&format=csv",
        headers={
            "X-Study-Capability":
                CLIENTS[base]["capabilities"][data["attempt_id"]]
        },
    )
    with urllib.request.urlopen(request) as response:
        csv_bytes = response.read()
    assert csv_bytes.startswith(b"\xef\xbb\xbf")
    csv_text = csv_bytes.decode("utf-8-sig")
    assert csv_text.count("\r\n") == 7
    assert "verification_signature" in csv_text
    assert "ui_language" in csv_text and "locale_bundle_hash" in csv_text


def test_export_ready_is_frozen_retryable_and_retained(live_server):
    base, server = live_server
    data = complete_attempt(base)
    attempt = data["attempt_id"]
    now = [1_000.0]
    server.clock = lambda: now[0]
    first = request_json(base, f"/api/export?attempt_id={attempt}&format=json")
    assert server.sessions[attempt]["last_seen"] == 1_000.0
    now[0] = 1_100.0
    second = request_json(base, f"/api/export?attempt_id={attempt}&format=json")
    assert first == second == data
    assert server.sessions[attempt]["last_seen"] == 1_100.0
    now[0] = 1_200.0
    with pytest.raises(urllib.error.HTTPError) as exc:
        request_json(base, f"/api/export?attempt_id={attempt}&format=xml")
    assert exc.value.code == 400
    assert server.sessions[attempt]["last_seen"] == 1_100.0


def test_duplicate_assignment_slot_consumption_and_all_three_estimands(live_server):
    base, _ = live_server
    first = complete_attempt(base, "P-DUP", "V9-01")
    later = complete_attempt(base, "P-DUP", "V9-02", locale="zh-Hans")
    other = complete_attempt(base, "P-OTHER", "V9-12")
    kept, duplicates = resolve_duplicates([first, later, other])
    assert [row["attempt_id"] for row in kept if row["participant_code"] == "P-DUP"] == [
        first["attempt_id"]
    ]
    assignments_path = RUNTIME / "assignments.json"
    assignments_path.write_text(json.dumps({
        "schema_version": "microstudy-owner-assignment-v2",
        "assignments": [
            {"participant_code": "P-DUP", "sequence": "V9-03"},
            {"participant_code": "P-OTHER", "sequence": "V9-12"},
        ],
    }), encoding="utf-8")
    assignments = load_assignments(assignments_path)
    summary = analyze([first, later, other], [], assignments=assignments)
    assert summary["kept_attempts"] == 2
    assert summary["input_attempts"] == 3
    assert summary["eligible_primary_n"] == 1
    assert summary["eligible_available_n"] == 1
    assert len(summary["participants"]) == 2
    assert summary["primary"]["mean_difference"] is not None
    assert summary["available_case_sensitivity"]["mean_difference"] is not None
    assert summary["missing_as_incorrect_sensitivity"]["mean_difference"] is not None
    assert Counter(row["reason"] for row in summary["rejected"]) == {
        "duplicate_attempt": 1,
        "assignment_mismatch": 1,
    }
    consumed = summary["sequence_slot_consumption"]["consumed"]
    assert {row["attempt_id"] for row in consumed} == {
        first["attempt_id"], later["attempt_id"], other["attempt_id"]
    }
    assert summary["descriptive_locale_qa"]["duplicate_locale_conflict_count"] == 1


def test_signed_partial_all_slots_available_threshold_and_itt(live_server):
    base, _ = live_server
    partial = partial_attempt(base, completed_trials=5)
    assert validate_export(partial, TEST_KEY) is partial
    assert partial["complete"] is False
    assert partial["completion_status"] == "partial"
    assert len(partial["trials"]) == 6
    assert sum(row["complete"] for row in partial["trials"]) == 5
    assert all(row["planned"] for row in partial["trials"])
    summary = analyze([partial], [])
    participant = summary["participants"][0]
    assert participant["complete_c"] >= 2
    assert participant["complete_f"] >= 2
    assert participant["complete_total"] == 5
    assert participant["eligible_primary"] is False
    assert participant["eligible_available"] is True
    assert summary["eligible_primary_n"] == 0
    assert summary["eligible_available_n"] == 1
    assert summary["missing_as_incorrect_sensitivity"]["mean_difference"] is not None
    assert summary["sequence_slot_consumption"]["consumed"] == []


def test_cross_run_duplicates_require_versioned_attempt_order_manifest(live_server):
    base, _ = live_server
    first = complete_attempt(base, "P-CROSS", "V9-01")
    second = complete_attempt(base, "P-CROSS", "V9-02")
    second["run_id"] = str(uuid.uuid4())
    second = sign_export(second, TEST_KEY)
    validate_export(second, TEST_KEY)
    with pytest.raises(ExportError, match="attempt-order"):
        resolve_duplicates([second, first])
    manifest = RUNTIME / "attempt-order.json"
    manifest.write_text(json.dumps({
        "schema_version": "microstudy-attempt-order-v1",
        "attempt_order": {
            first["attempt_id"]: 1,
            second["attempt_id"]: 2,
        },
    }), encoding="utf-8")
    order = load_attempt_order_manifest(manifest)
    kept, excluded = resolve_duplicates([second, first], order)
    assert kept[0]["attempt_id"] == first["attempt_id"]
    assert excluded[0]["attempt_id"] == second["attempt_id"]
    bad = RUNTIME / "bad-attempt-order.json"
    bad.write_text(json.dumps({
        "schema_version": "microstudy-attempt-order-v1",
        "attempt_order": {first["attempt_id"]: 1, second["attempt_id"]: 1},
    }), encoding="utf-8")
    with pytest.raises(ExportError, match="unique"):
        load_attempt_order_manifest(bad)


def test_request_protection_idempotency_capacity_and_expiry():
    RUNTIME.mkdir(parents=True, exist_ok=True)
    key_path = RUNTIME / "security.key"
    key_path.write_bytes(TEST_KEY)
    server = create_server(
        "127.0.0.1", 0, key_path, max_sessions=1, session_ttl_seconds=0.05
    )
    now = [0.0]
    server.clock = lambda: now[0]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        bootstrap = request_json(base, "/api/bootstrap")
        cross_site = urllib.request.Request(
            f"{base}/api/welcome?ui_language=en",
            headers={"Origin": "https://evil.invalid"},
        )
        with pytest.raises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(cross_site)
        assert exc.value.code == 403
        for headers in (
            {
                "Content-Type": "text/plain", "Origin": base,
                "X-CSRF-Token": bootstrap["csrf_token"],
            },
            {
                "Content-Type": "application/json",
                "Origin": "https://evil.invalid",
                "X-CSRF-Token": bootstrap["csrf_token"],
            },
            {"Content-Type": "application/json"},
            {
                "Content-Type": "application/json", "Origin": base,
                "X-CSRF-Token": "wrong",
            },
            {
                "Content-Type": "application/json", "Origin": base,
                "X-CSRF-Token": bootstrap["csrf_token"], "Host": "localhost:1",
            },
        ):
            request = urllib.request.Request(
                f"{base}/api/start",
                data=json.dumps({
                    "participant_code": "SEC",
                    "sequence": "V9-01",
                    "ui_language": "en",
                    "request_id": uuid.uuid4().hex,
                }).encode(),
                headers=headers,
                method="POST",
            )
            with pytest.raises(urllib.error.HTTPError):
                urllib.request.urlopen(request)
        start_body = {
            "participant_code": "SEC",
            "sequence": "V9-01",
            "ui_language": "en",
            "request_id": uuid.uuid4().hex,
        }
        start = request_json(base, "/api/start", start_body)
        assert request_json(base, "/api/start", start_body) == start
        assert server.attempt_serial == 1 and len(server.sessions) == 1
        attempt = start["attempt_id"]
        oversized = urllib.request.Request(
            f"{base}/api/practice",
            data=b"{" + b" " * 20_000 + b"}",
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
                "attempt_id": attempt, "step": "q1", "answer": "A",
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
                "participant_code": "FLOOD",
                "sequence": "V9-02",
                "ui_language": "en",
            })
        now[0] = 0.06
        replacement = request_json(base, "/api/start", {
            "participant_code": "AFTER",
            "sequence": "V9-02",
            "ui_language": "zh-Hans",
        })
        assert replacement["attempt_id"] != attempt
        assert attempt not in server.sessions
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=10)
        CLIENTS.pop(base, None)
        shutil.rmtree(RUNTIME, ignore_errors=True)


def test_session_ttl_renews_only_after_successful_authenticated_requests():
    RUNTIME.mkdir(parents=True, exist_ok=True)
    key_path = RUNTIME / "ttl.key"
    key_path.write_bytes(TEST_KEY)
    server = create_server("127.0.0.1", 0, key_path, session_ttl_seconds=1_000)
    now = [100.0]
    server.clock = lambda: now[0]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"

    def rejected(path, body, *, headers=None, status=409):
        request_headers = {
            "Content-Type": "application/json",
            "Origin": base,
            "X-CSRF-Token": CLIENTS[base]["csrf"],
            "X-Study-Capability": start["capability"],
        }
        request_headers.update(headers or {})
        request = urllib.request.Request(
            f"{base}{path}",
            data=json.dumps(body).encode(),
            headers=request_headers,
            method="POST",
        )
        with pytest.raises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(request)
        assert exc.value.code == status

    try:
        request_json(base, "/api/bootstrap")
        common = locale_materials(base)["common"]
        start = request_json(base, "/api/start", {
            "participant_code": "TTL",
            "sequence": "V9-01",
            "ui_language": "en",
        })
        attempt = start["attempt_id"]
        session = server.sessions[attempt]
        now[0] = 110.0
        rejected("/api/practice", {
            "attempt_id": attempt,
            "step": "q1",
            "request_id": "invalidpayload001",
        })
        assert session["last_seen"] == 100.0
        successful = {
            "attempt_id": attempt,
            "step": "q1",
            "answer": common["q1"]["options"][0]["id"],
            "request_id": "successfulreq001",
        }
        now[0] = 130.0
        assert request_json(base, "/api/practice", successful)["phase"] == "practice_q2"
        assert session["last_seen"] == 130.0
        now[0] = 140.0
        assert request_json(base, "/api/practice", successful)["phase"] == "practice_q2"
        assert session["last_seen"] == 140.0
        now[0] = 150.0
        rejected("/api/practice", {**successful, "answer": "different"})
        assert session["last_seen"] == 140.0
        next_step = {
            "attempt_id": attempt,
            "step": "q2",
            "answer": common["practice"]["q2_options"][0]["id"],
            "request_id": "protectedrequest1",
        }
        for current_time, headers, status in (
            (160.0, {"X-Study-Capability": "wrong"}, 409),
            (170.0, {"X-CSRF-Token": "wrong"}, 403),
            (180.0, {"Origin": "https://evil.invalid"}, 403),
        ):
            now[0] = current_time
            rejected("/api/practice", next_step, headers=headers, status=status)
            assert session["last_seen"] == 140.0
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=10)
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
                "participant_code": participant,
                "sequence": "V9-01",
                "ui_language": "en",
            })
            observed.append((start["run_id"], start["attempt_serial"]))
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=10)
            CLIENTS.pop(base, None)
    assert observed[0][0] != observed[1][0]
    assert observed[0][1] == observed[1][1] == 1
    shutil.rmtree(RUNTIME, ignore_errors=True)


def test_concurrent_q1_same_request_is_exactly_once(live_server):
    base, server = live_server
    attempt, _, current = start_formal_http(base, "RACE", "V9-01", "en")
    request_id = uuid.uuid4().hex
    payload = json.dumps({
        "attempt_id": attempt,
        "answer": current["q1"]["options"][0]["id"],
        "request_id": request_id,
    }).encode()
    headers = {
        "Content-Type": "application/json",
        "Origin": base,
        "X-CSRF-Token": CLIENTS[base]["csrf"],
        "X-Study-Capability": CLIENTS[base]["capabilities"][attempt],
    }
    results = []
    barrier = threading.Barrier(3)

    def send():
        barrier.wait()
        request = urllib.request.Request(
            f"{base}/api/q1", data=payload, headers=headers, method="POST"
        )
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
        "attempt_id": attempt,
        "answer": current["q1"]["options"][1]["id"],
        "request_id": request_id,
    }).encode()
    with pytest.raises(urllib.error.HTTPError):
        urllib.request.urlopen(urllib.request.Request(
            f"{base}/api/q1", data=altered, headers=headers, method="POST"
        ))
    assert session["phase"] == "q2"


def test_load_exports_rejects_corrupt_unsigned_unknown_and_conflicting(live_server):
    base, _ = live_server
    data = complete_attempt(base)
    RUNTIME.mkdir(parents=True, exist_ok=True)
    good = RUNTIME / "good.json"
    unsigned = RUNTIME / "unsigned.json"
    unknown = RUNTIME / "unknown.json"
    corrupt = RUNTIME / "corrupt.json"
    conflict = RUNTIME / "conflict.json"
    good.write_text(json.dumps(data), encoding="utf-8")
    unsigned.write_text(json.dumps({
        key: value for key, value in data.items() if key != "verification"
    }), encoding="utf-8")
    value = copy.deepcopy(data)
    value["attempt_id"] = str(uuid.uuid4())
    value["unexpected"] = True
    unknown.write_text(json.dumps(sign_export(value, TEST_KEY)), encoding="utf-8")
    corrupt.write_text("{", encoding="utf-8")
    valid, rejected = load_exports([good, good, unsigned, unknown, corrupt], TEST_KEY)
    assert len(valid) == 1
    assert Counter(row["reason"] for row in rejected) == {
        "technical_corrupt": 1,
        "signature_invalid": 1,
        "unknown_field": 1,
    }
    changed = copy.deepcopy(data)
    changed["participant_code"] = "CONFLICT"
    conflict.write_text(json.dumps(sign_export(changed, TEST_KEY)), encoding="utf-8")
    with pytest.raises(ExportError, match="conflicting payload or signature"):
        load_exports([good, conflict], TEST_KEY)


def test_load_exports_hard_fails_v4_v5_and_v8_v9_mixing(live_server):
    base, _ = live_server
    current = complete_attempt(base)
    RUNTIME.mkdir(parents=True, exist_ok=True)
    current_path = RUNTIME / "current.json"
    current_path.write_text(json.dumps(current), encoding="utf-8")
    legacy_export = copy.deepcopy(current)
    legacy_export["attempt_id"] = str(uuid.uuid4())
    legacy_export["export_schema_version"] = "microstudy-export-v4-bilingual-signed"
    legacy_export_path = RUNTIME / "legacy-export.json"
    legacy_export_path.write_text(
        json.dumps(sign_export(legacy_export, TEST_KEY)), encoding="utf-8"
    )
    with pytest.raises(ExportError, match="V4/V5"):
        load_exports([current_path, legacy_export_path], TEST_KEY)
    legacy_material = copy.deepcopy(current)
    legacy_material["attempt_id"] = str(uuid.uuid4())
    legacy_material["material_schema_version"] = (
        "microstudy-stimuli-v8-bilingual-novice-ux"
    )
    legacy_material_path = RUNTIME / "legacy-material.json"
    legacy_material_path.write_text(
        json.dumps(sign_export(legacy_material, TEST_KEY)), encoding="utf-8"
    )
    with pytest.raises(ExportError, match="V8/V9"):
        load_exports([current_path, legacy_material_path], TEST_KEY)


def test_static_dom_accessibility_and_no_semantic_carriers():
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    css = (STATIC_DIR / "study.css").read_text(encoding="utf-8")
    js = (STATIC_DIR / "study.js").read_text(encoding="utf-8")
    combined = html + css + js
    for forbidden in (
        "localStorage", "sessionStorage", "indexedDB", "document.cookie",
        "serviceWorker", "data-condition", "data-ticket", "data-state",
        "data-answer", "data-correct", "navigator.language",
        "navigator.languages", "location.search",
    ):
        assert forbidden not in combined
    for forbidden_class in (
        "class: \"pass", "class: \"fail", "class: \"supported",
        "class: \"withheld", "class: \"pending", "class: \"adjustable",
        "class: \"recommend", "class: \"correct",
    ):
        assert forbidden_class not in js
    assert '<html lang="und">' in html
    assert 'id="desktop-blocker" role="alert"' in html
    assert html.count('data-action="choose-language"') == 2
    assert "cardData.aria_label" in js
    assert "document.documentElement.lang = app.locale" in js
    assert "heading.focus()" in js
    assert js.count('document.addEventListener("click"') == 1
    assert "correct_key" not in js and "q1_key" not in js and "q2_key" not in js
    assert 'role: "status"' in js and 'role: "alert"' in js
    assert '"aria-invalid", "true"' in js
    assert "showModal()" in js and 'addEventListener("cancel"' in js
    assert "bootstrapReady" in js and "welcomeReady" in js
    assert 'typeof response.capability !== "string"' in js
    assert "Microsoft YaHei" in css and "overflow-wrap: anywhere" in css
    assert "focus-visible" in css and "prefers-reduced-motion" in css
    assert "dialog::backdrop" in css and ".locked-summary" in css


def test_exact_sign_flip_ties_and_equality():
    assert exact_sign_flip([0, 0]) == {"n_eff": 0, "ties": 2, "p": 1.0}
    assert exact_sign_flip([0.2, 0.2])["p"] == 0.25
    assert exact_sign_flip([0.2, -0.2], two_sided=True)["p"] == 1.0


def _free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def test_real_chrome_edge_v9_complete_partial_download_zoom_and_stress():
    pytest.importorskip("websocket")
    from browser_cdp import CDP

    candidates = {
        "edge": Path(os.environ.get(
            "EDGE_PATH",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        )),
        "chrome": Path(os.environ.get(
            "CHROME_PATH",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        )),
    }
    browsers = {name: path for name, path in candidates.items() if path.exists()}
    assert set(browsers) == {"chrome", "edge"}, "Chrome and Edge are required"
    RUNTIME.mkdir(parents=True, exist_ok=True)
    downloads = RUNTIME / "downloads"
    screenshots = RUNTIME / "screenshots"
    downloads.mkdir()
    screenshots.mkdir()

    def remove_runtime():
        deadline = time.monotonic() + 30
        last_error = None
        cleanup_root = Path("\\\\?\\" + str(RUNTIME.resolve()))
        while RUNTIME.exists():
            for current, directories, files in os.walk(
                cleanup_root, topdown=False
            ):
                current_path = Path(current)
                for filename in files:
                    try:
                        (current_path / filename).unlink(missing_ok=True)
                    except OSError as exc:
                        last_error = exc
                for dirname in directories:
                    path = current_path / dirname
                    try:
                        if path.is_symlink() or path.is_junction():
                            path.unlink(missing_ok=True)
                        else:
                            path.rmdir()
                    except FileNotFoundError:
                        pass
                    except OSError as exc:
                        last_error = exc
            try:
                cleanup_root.rmdir()
            except FileNotFoundError:
                return
            except OSError as exc:
                last_error = exc
            if time.monotonic() >= deadline:
                raise AssertionError(f"runtime cleanup failed: {last_error}")
            time.sleep(0.05)

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
    def delayed_bootstrap_server(label):
        release = threading.Event()
        request_started = threading.Event()
        release_observed = threading.Event()
        response_sent = threading.Event()

        class DelayedBootstrapHandler(StudyHandler):
            def do_GET(self):
                if self.path == "/api/bootstrap":
                    request_started.set()
                    release.wait()
                    release_observed.set()
                super().do_GET()
                if self.path == "/api/bootstrap":
                    response_sent.set()

        key_path = RUNTIME / f"{label}-{uuid.uuid4().hex}.key"
        key_path.write_bytes(TEST_KEY)
        server = create_server("127.0.0.1", 0, key_path)
        server.RequestHandlerClass = DelayedBootstrapHandler
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            yield (
                base, server, release, request_started, release_observed,
                response_sent,
            )
        finally:
            release.set()
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
            str(executable),
            "--headless=new",
            "--no-sandbox",
            "--disable-gpu",
            "--disable-extensions",
            "--disable-component-update",
            "--disable-background-networking",
            "--no-first-run",
            "--disable-features=msEdgeFirstRunExperience",
            "--no-default-browser-check",
            "--remote-allow-origins=*",
            f"--remote-debugging-port={port}",
            f"--user-data-dir={profile.resolve()}",
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
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.terminate()
                    process.wait(timeout=10)
            subprocess.run(
                [
                    "powershell.exe", "-NoProfile", "-NonInteractive",
                    "-Command",
                    "$profile=$env:V9_PROFILE; "
                    "Get-CimInstance Win32_Process | "
                    "Where-Object {$_.CommandLine -and "
                    "$_.CommandLine.Contains($profile)} | "
                    "ForEach-Object {Stop-Process -Id $_.ProcessId "
                    "-Force -ErrorAction SilentlyContinue}",
                ],
                env={**os.environ, "V9_PROFILE": str(profile.resolve())},
                capture_output=True,
                text=True,
                timeout=20,
                check=True,
            )
            stderr_handle.close()

    def press(cdp, key, code, virtual_key):
        down = {
            "key": key,
            "code": code,
            "windowsVirtualKeyCode": virtual_key,
            "text": "\r" if key == "Enter" else (key if key == " " else ""),
        }
        up = {
            "key": key,
            "code": code,
            "windowsVirtualKeyCode": virtual_key,
        }
        cdp.call("Input.dispatchKeyEvent", {"type": "keyDown", **down})
        cdp.call("Input.dispatchKeyEvent", {"type": "keyUp", **up})

    def open_page(port, base, *, width=1280, height=800, zoom=1):
        cdp = CDP.new_page(port, "about:blank")
        cdp.call("Emulation.setDeviceMetricsOverride", {
            "width": width,
            "height": height,
            "deviceScaleFactor": 1,
            "mobile": False,
        })
        cdp.call("Emulation.setPageScaleFactor", {"pageScaleFactor": zoom})
        cdp.call("Page.navigate", {"url": f"{base}/"})
        return cdp

    def start_browser_formal(
        cdp, participant, sequence, locale, *, keyboard=False, server=None
    ):
        cdp.wait(
            "window.MicrostudyTest"
            f" && document.querySelector('[data-locale=\"{locale}\"]')"
            f" && !document.querySelector('[data-locale=\"{locale}\"]').disabled"
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
        cdp.wait(
            "document.querySelector('#sequence option')"
            " && !document.querySelector('#start-button').disabled"
        )
        assert cdp.eval("document.documentElement.lang") == locale
        welcome_text = cdp.eval("document.querySelector('#start').innerText")
        assert ("6 formal tickets" in welcome_text) == (locale == "en")
        assert ("6 张正式工单" in welcome_text) == (locale == "zh-Hans")
        cdp.eval(
            f"document.querySelector('#participant-code').value={json.dumps(participant)};"
            f"document.querySelector('#sequence').value={json.dumps(sequence)};"
            "document.querySelector('#participant-code').focus();"
        )
        if keyboard:
            press(cdp, "Tab", "Tab", 9)
            press(cdp, "Tab", "Tab", 9)
            assert cdp.eval("document.activeElement.id") == "start-button"
            press(cdp, "Enter", "Enter", 13)
        else:
            cdp.click("start")
        cdp.wait("document.querySelector('[data-action=\"show-practice\"]')")
        assert cdp.eval("document.querySelectorAll('.policy-list li').length") == 4
        briefing = cdp.eval("document.querySelector('#stage').innerText")
        contract_headings = (
            ["Can the behavior be identified?",
             "How does the knob compare with direct prompting?",
             "What could weaken or limit the result?",
             "Where does this evidence apply?"]
            if locale == "en"
            else ["能否识别这种行为？", "旋钮与直接提示相比如何？",
                  "哪些因素可能削弱或限制结果？", "这些证据适用于哪里？"]
        )
        assert not any(value in briefing for value in contract_headings)
        if server is not None:
            assert server.attempt_serial == 1 and len(server.sessions) == 1
        cdp.click("show-practice")
        cdp.wait("document.querySelectorAll('.evidence-row').length === 6")
        assert cdp.eval("!document.querySelector('#practice-knob').disabled")
        assert cdp.eval("document.querySelectorAll('.audio-actions button').length") == 2
        cdp.choose_and_click("practice-q1", "practice-q1")
        cdp.wait("document.querySelector('.locked-summary[role=\"status\"]')")
        cdp.choose_and_click("practice-q2", "practice-q2")
        cdp.wait("document.querySelector('[data-action=\"begin-formal\"]')")
        cdp.click("begin-formal")

    def finish_browser_formal(
        cdp, locale, *, audit_geometry=False, screenshot_prefix=None, server=None
    ):
        captured = set()
        for index in range(6):
            cdp.wait(
                "document.querySelector('[data-action=\"formal-q1\"]')"
                " && !document.querySelector('[data-action=\"formal-q1\"]').disabled"
            )
            if audit_geometry:
                audit = cdp.eval("""(() => {
                  const card=document.querySelector('.evidence-card');
                  const groups=[...document.querySelectorAll('.evidence-group')];
                  const rows=[...document.querySelectorAll('.evidence-row')];
                  const badges=[...document.querySelectorAll('.badge')].map(n=>n.innerText);
                  const attrs=[...document.querySelectorAll('*')].flatMap(node =>
                    [...node.attributes].map(a=>a.name)).filter(name =>
                    /condition|ticket|state|answer|correct|role-id|group-id/i.test(name));
                  const classes=[...document.querySelectorAll('*')].flatMap(node =>
                    [...node.classList]).filter(name =>
                    /supported|withheld|pending|adjustable|correct|recommend|pass|fail/i.test(name));
                  const visible=[...document.querySelectorAll('#stage *')].filter(node =>
                    getComputedStyle(node).display!=='none' && getComputedStyle(node).visibility!=='hidden');
                  return {
                    groupSizes:groups.map(g=>g.querySelectorAll('li').length),
                    rowCount:rows.length,
                    badges,
                    outputs:document.querySelectorAll('.output-card').length,
                    knobDisabled:document.querySelector('#ticket-knob').disabled,
                    knobFilter:getComputedStyle(document.querySelector('#ticket-knob')).filter,
                    sourceDetailsCount:document.querySelectorAll('.source-details').length,
                    sourceFields:[...document.querySelectorAll('*')].flatMap(node =>
                      [...node.attributes].map(a=>`${a.name}=${a.value}`)).filter(value =>
                      /source_id|canonical_sha256|hash_basis|commit|source-details/i.test(value)),
                    stageText:document.querySelector('#stage').innerText,
                    stageHtml:document.querySelector('#stage').innerHTML,
                    attrs,classes,
                    horizontalOverflow:document.documentElement.scrollWidth>
                      document.documentElement.clientWidth,
                    cardOverflow:card.scrollWidth>card.clientWidth,
                    clipped:visible.filter(node =>
                      node.clientWidth>0 && node.scrollWidth>node.clientWidth+1
                      && !['CODE','P'].includes(node.tagName)
                    ).map(node => ({
                      tag:node.tagName,id:node.id,className:node.className,
                      clientWidth:node.clientWidth,scrollWidth:node.scrollWidth,
                      text:node.textContent.slice(0,120)
                    })),
                    h1Count:document.querySelectorAll('#stage h1').length,
                    choiceCount:document.querySelectorAll('input[name="formal-q1"]').length
                  };
                })()""")
                condition = "contract" if audit["groupSizes"] else "flat"
                assert audit["groupSizes"] in ([], [1, 2, 2, 1])
                assert audit["rowCount"] in (0, 6)
                assert audit["outputs"] == 2
                assert len(audit["badges"]) == 3
                assert audit["badges"][0] in {"SOURCE-BACKED", "SIMULATED"}
                assert audit["badges"][1:] == ["ILLUSTRATIVE OUTPUT"] * 2
                assert audit["knobDisabled"] and audit["knobFilter"] != "none"
                assert audit["sourceDetailsCount"] == 0
                assert not audit["sourceFields"]
                assert not re.search(
                    r"\b(?:CAA|ITI|CI|MDE|Brier|Qwen|Llama)\b|"
                    r"1[−-]Brier|facade ratio|residual norm|残差范数|表征比|"
                    r"(?<![\w.])[+-]?\d+\.\d+",
                    audit["stageText"],
                    flags=re.IGNORECASE,
                )
                assert not re.search(
                    r"source_id|canonical_sha256|hash_basis|commit|source-details",
                    audit["stageHtml"],
                    flags=re.IGNORECASE,
                )
                assert not audit["attrs"] and not audit["classes"]
                assert not audit["horizontalOverflow"] and not audit["cardOverflow"]
                assert not audit["clipped"], (
                    screenshot_prefix,
                    json.dumps(audit["clipped"], ensure_ascii=False),
                )
                assert audit["h1Count"] == 1 and audit["choiceCount"] == 4
                if condition not in captured:
                    result = cdp.call("Page.captureScreenshot", {
                        "format": "png", "captureBeyondViewport": False,
                    })
                    content = base64.b64decode(result["data"])
                    width, height = struct.unpack(">II", content[16:24])
                    expected = cdp.eval(
                        "({w:window.innerWidth,h:window.innerHeight})"
                    )
                    assert (width, height) == (expected["w"], expected["h"])
                    path = screenshots / f"{screenshot_prefix}-{condition}.png"
                    path.write_bytes(content)
                    assert len(content) > 5000
                    captured.add(condition)
            if server is not None and index == 0:
                attempt = next(iter(server.sessions))
                before = len(server.sessions[attempt]["requests"])
                cdp.click("formal-q1")
                cdp.wait(
                    "document.querySelector('#formal-q1-error').textContent.length > 0"
                )
                assert len(server.sessions[attempt]["requests"]) == before
            cdp.choose_and_click("formal-q1", "formal-q1")
            cdp.wait(
                "document.querySelector('.locked-summary[role=\"status\"]')"
                " && document.querySelector('#q2-heading')"
            )
            locked = cdp.eval("""(() => ({
              text:document.querySelector('.locked-summary').innerText,
              focus:document.activeElement.id,
              q1Button:document.querySelector('[data-action="formal-q1"]')
            }))()""")
            assert locked["focus"] == "q2-heading" and locked["q1Button"] is None
            assert ("cannot be changed" in locked["text"]) == (locale == "en")
            cdp.choose_and_click("formal-q2", "formal-q2")
            cdp.wait("document.querySelector('.decision-preview')")
            preview = cdp.eval("document.querySelector('.decision-preview').innerText")
            assert ("not correctness feedback" in preview) == (locale == "en")
            assert ("不提供正误反馈" in preview) == (locale == "zh-Hans")
            cdp.click("continue-preview")
        cdp.wait("document.querySelector('[data-action=\"download-json\"]')")
        assert captured == ({"contract", "flat"} if audit_geometry else captured)
        assert cdp.eval("document.querySelector('[data-action=\"download-csv\"]') !== null")

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
            "Boolean(document.querySelector('#stage-error').getAttribute('role') === 'alert'"
            " && document.querySelector('[data-action=\"download-json\"]')"
            " && document.querySelector('[data-action=\"download-csv\"]'))"
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
        ("V9-01", "en", 1280, 800, 1),
        ("V9-12", "zh-Hans", 1280, 800, 2),
        ("V9-01", "zh-Hans", 1440, 900, 2),
        ("V9-12", "en", 1440, 900, 1),
    ]
    stress_iterations = int(os.environ.get(
        "MICROSTUDY_BROWSER_STRESS_ITERATIONS", "1"
    ))
    try:
        for browser_name, executable in browsers.items():
            with browser_process(browser_name, executable) as port:
                with delayed_bootstrap_server(
                    f"{browser_name}-bootstrap"
                ) as (
                    base, _, release, request_started, release_observed,
                    response_sent,
                ):
                    cdp = open_page(port, base)
                    try:
                        assert request_started.wait(timeout=10)
                        cdp.wait(
                            "window.MicrostudyTest"
                            " && document.querySelector('[data-locale=\"en\"]')"
                        )
                        assert cdp.eval(
                            "document.querySelector('[data-locale=\"en\"]').disabled"
                        )
                        release.set()
                        assert release_observed.wait(timeout=10)
                        assert response_sent.wait(timeout=10)
                        cdp.wait(
                            "!document.querySelector('[data-locale=\"en\"]').disabled"
                        )
                    finally:
                        release.set()
                        cdp.close()
                for case_index, (
                    sequence, locale, width, height, zoom
                ) in enumerate(geometry_cases):
                    label = f"{browser_name}-{locale}-{sequence}-{width}-z{zoom}"
                    with isolated_server(label) as (base, server):
                        cdp = open_page(
                            port, base, width=width, height=height, zoom=zoom
                        )
                        try:
                            cdp.call("Browser.setDownloadBehavior", {
                                "behavior": "allow",
                                "downloadPath": str(downloads),
                            })
                            start_browser_formal(
                                cdp,
                                f"G{case_index}{browser_name[0]}",
                                sequence,
                                locale,
                                keyboard=True,
                                server=server,
                            )
                            finish_browser_formal(
                                cdp,
                                locale,
                                audit_geometry=True,
                                screenshot_prefix=label,
                                server=server,
                            )
                            assert_manual_downloads(cdp, server)
                        finally:
                            cdp.close()
                with isolated_server(
                    f"{browser_name}-desktop-block"
                ) as (base, _):
                    cdp = open_page(port, base, width=1279)
                    try:
                        cdp.wait("window.MicrostudyTest")
                        assert cdp.eval(
                            "getComputedStyle(document.querySelector('#desktop-blocker')).display"
                            " !== 'none' && getComputedStyle(document.querySelector('#app')).display"
                            " === 'none'"
                        )
                    finally:
                        cdp.close()
                for iteration in range(stress_iterations):
                    sequence = "V9-01" if iteration % 2 == 0 else "V9-12"
                    locale = "en" if iteration % 2 == 0 else "zh-Hans"
                    label = f"{browser_name}-stress-partial-{iteration}"
                    with isolated_server(label) as (base, server):
                        cdp = open_page(port, base)
                        try:
                            cdp.call("Browser.setDownloadBehavior", {
                                "behavior": "allow",
                                "downloadPath": str(downloads),
                            })
                            start_browser_formal(
                                cdp, f"SP{iteration}{browser_name[0]}",
                                sequence, locale,
                            )
                            cdp.wait("!document.querySelector('#save-exit-button').hidden")
                            attempt = next(iter(server.sessions))
                            before = len(server.sessions[attempt]["requests"])
                            cdp.click("save-exit")
                            cdp.wait("document.querySelector('#save-exit-dialog').open")
                            assert cdp.eval(
                                "document.activeElement.dataset.action"
                            ) == "cancel-save-exit"
                            cdp.click("cancel-save-exit")
                            cdp.wait("!document.querySelector('#save-exit-dialog').open")
                            assert len(server.sessions[attempt]["requests"]) == before
                            assert server.sessions[attempt]["phase"] == "q1"
                            cdp.click("save-exit")
                            cdp.wait("document.querySelector('#save-exit-dialog').open")
                            cdp.click("confirm-save-exit")
                            cdp.wait(
                                "document.querySelector('[data-action=\"download-json\"]')"
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
        remove_runtime()
    assert not RUNTIME.exists()
