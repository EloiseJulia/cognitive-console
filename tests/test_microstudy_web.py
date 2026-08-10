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


def complete_attempt(base, participant="P001", sequence="A1"):
    materials = request_json(base, "/api/materials")
    start = request_json(base, "/api/start", {
        "participant_code": participant, "sequence": sequence,
    })
    attempt = start["attempt_id"]
    practice = materials["participant_materials"]["practice"]
    request_json(base, "/api/practice", {
        "attempt_id": attempt, "step": "q1", "answer": materials["q1"]["options"][0]["key"],
    })
    current = request_json(base, "/api/practice", {
        "attempt_id": attempt, "step": "q2", "answer": practice["q2"]["options"][0]["key"],
    })
    for index in range(10):
        q2 = request_json(base, "/api/q1", {
            "attempt_id": attempt, "answer": materials["q1"]["options"][0]["key"],
        })
        current = request_json(base, "/api/q2", {
            "attempt_id": attempt, "answer": q2["q2"]["options"][0]["key"], "hidden_ms": 0,
        })
        if index in (4, 9):
            current = request_json(base, "/api/ease", {
                "attempt_id": attempt, "block": 1 if index == 4 else 2, "answer": None,
            })
    assert current["phase"] == "diagnostic"
    request_json(base, "/api/diagnostic", {"attempt_id": attempt, "answer": None})
    request_json(base, "/api/complete", {"attempt_id": attempt})
    return request_json(base, f"/api/export?attempt_id={attempt}&format=json")


def partial_attempt(base, completed_trials=4, participant="P-PARTIAL", sequence="A1"):
    materials = request_json(base, "/api/materials")
    start = request_json(base, "/api/start", {
        "participant_code": participant, "sequence": sequence,
    })
    attempt = start["attempt_id"]
    practice = materials["participant_materials"]["practice"]
    request_json(base, "/api/practice", {
        "attempt_id": attempt, "step": "q1", "answer": materials["q1"]["options"][0]["key"],
    })
    request_json(base, "/api/practice", {
        "attempt_id": attempt, "step": "q2", "answer": practice["q2"]["options"][0]["key"],
    })
    for index in range(completed_trials):
        q2 = request_json(base, "/api/q1", {
            "attempt_id": attempt, "answer": materials["q1"]["options"][0]["key"],
        })
        request_json(base, "/api/q2", {
            "attempt_id": attempt, "answer": q2["q2"]["options"][0]["key"], "hidden_ms": 0,
        })
        if index == 4:
            request_json(base, "/api/ease", {
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
        materials = request_json(base, "/api/materials")
    encoded = json.dumps(materials).lower()
    for forbidden in (
        "expected_q1", "correct_key", "state_routing_inputs", "router",
        "validation_contract", "render_contract", "export_schema", "q1_key", "q2_key",
    ):
        assert forbidden not in encoded
    assert set(materials) == {
        "materials_version", "primitive_ids", "contract_headings",
        "simulated_record_notice", "q1", "q2_templates", "items",
        "participant_materials", "sequence_codes",
    }
    assert output.getvalue() == ""


def test_server_strict_state_machine_and_memory_only(live_server):
    base, server = live_server
    start = request_json(base, "/api/start", {"participant_code": "P1", "sequence": "A1"})
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


def test_signed_export_validation_tamper_wrong_key_and_csv(live_server):
    base, _ = live_server
    data = complete_attempt(base)
    assert validate_export(data, TEST_KEY) is data
    assert len(data["trials"]) == 10
    assert data["verification"]["algorithm"] == "HMAC-SHA256"
    assert TEST_KEY.hex() not in json.dumps(data)
    assert data["complete"] is True
    assert data["run_id"] and data["attempt_serial"] >= 1
    tampered = copy.deepcopy(data)
    tampered["participant_code"] = "FORGED"
    with pytest.raises(ExportError, match="signature"):
        validate_export(tampered, TEST_KEY)
    with pytest.raises(ExportError, match="key"):
        validate_export(data, b"x" * 32)
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
        csv_text = response.read().decode()
    assert csv_text.count("\r\n") == 11
    assert "verification_signature" in csv_text


def test_duplicate_first_complete_then_assignment_and_itt(live_server):
    base, _ = live_server
    first = complete_attempt(base, "P-DUP", "A1")
    later = complete_attempt(base, "P-DUP", "B1")
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
            f"{base}/api/materials", headers={"Origin": "https://evil.invalid"}
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
                    "participant_code": "SEC", "sequence": "A1", "request_id": uuid.uuid4().hex,
                }).encode(),
                headers=headers, method="POST",
            )
            with pytest.raises(urllib.error.HTTPError):
                urllib.request.urlopen(request)
        start = request_json(base, "/api/start", {"participant_code": "SEC", "sequence": "A1"})
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
            request_json(base, "/api/start", {"participant_code": "FLOOD", "sequence": "A2"})
        time.sleep(0.07)
        replacement = request_json(base, "/api/start", {
            "participant_code": "AFTER", "sequence": "A2",
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
    materials = request_json(base, "/api/materials")
    start = request_json(base, "/api/start", {"participant_code": "RACE", "sequence": "A1"})
    attempt = start["attempt_id"]
    practice = materials["participant_materials"]["practice"]
    request_json(base, "/api/practice", {
        "attempt_id": attempt, "step": "q1", "answer": materials["q1"]["options"][0]["key"],
    })
    request_json(base, "/api/practice", {
        "attempt_id": attempt, "step": "q2", "answer": practice["q2"]["options"][0]["key"],
    })
    request_id = uuid.uuid4().hex
    payload = json.dumps({
        "attempt_id": attempt, "answer": materials["q1"]["options"][0]["key"],
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
        "attempt_id": attempt, "answer": materials["q1"]["options"][1]["key"],
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
    value["unexpected"] = True
    unknown.write_text(json.dumps(sign_export(value, TEST_KEY)), encoding="utf-8")
    corrupt.write_text("{", encoding="utf-8")
    valid, rejected = load_exports([good, unsigned, unknown, corrupt], TEST_KEY)
    assert len(valid) == 1
    assert Counter(row["reason"] for row in rejected) == {
        "technical_corrupt": 3,
    }


def test_static_dom_accessibility_and_no_semantic_attributes():
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    css = (STATIC_DIR / "study.css").read_text(encoding="utf-8")
    js = (STATIC_DIR / "study.js").read_text(encoding="utf-8")
    combined = html + css + js
    for forbidden in (
        "localStorage", "sessionStorage", "indexedDB", "document.cookie",
        "serviceWorker", "data-condition", "data-stimulus-id", "data-evidence-id",
    ):
        assert forbidden not in combined
    assert '<section id="stage" class="panel" tabindex="-1"' in html
    assert '"aria-label": "Evidence panel"' in js
    assert js.count('document.addEventListener("click"') == 1
    assert "correct_key" not in js and "q1_key" not in js and "q2_key" not in js
    assert "focus-visible" in css and "prefers-reduced-motion" in css


def test_exact_sign_flip_ties_and_equality():
    assert exact_sign_flip([0, 0]) == {"n_eff": 0, "ties": 2, "p": 1.0}
    assert exact_sign_flip([0.2, 0.2])["p"] == 0.25


def _free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def test_real_chrome_edge_full_flow_keyboard_geometry_and_screenshots():
    websocket = pytest.importorskip("websocket")
    from browser_cdp import CDP

    browser_candidates = {
        "edge": Path(os.environ.get(
            "EDGE_PATH", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        )),
        "chrome": Path(os.environ.get(
            "CHROME_PATH", r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        )),
    }
    browsers = {name: path for name, path in browser_candidates.items() if path.exists()}
    assert browsers, "Chrome or Edge is required for the real-browser gate"

    RUNTIME.mkdir(parents=True, exist_ok=True)
    key_path = RUNTIME / "browser.key"
    key_path.write_bytes(TEST_KEY)
    server = create_server("127.0.0.1", 0, key_path)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    downloads = RUNTIME / "downloads"
    downloads.mkdir()
    screenshots = RUNTIME / "screenshots"
    screenshots.mkdir()

    def press(cdp, key, code, virtual_key):
        cdp.call("Input.dispatchKeyEvent", {
            "type": "keyDown", "key": key, "code": code,
            "windowsVirtualKeyCode": virtual_key,
            "text": "\r" if key == "Enter" else (key if key == " " else ""),
        })
        cdp.call("Input.dispatchKeyEvent", {
            "type": "keyUp", "key": key, "code": code,
            "windowsVirtualKeyCode": virtual_key,
        })

    def screenshot(cdp, path, width, height):
        result = cdp.call("Page.captureScreenshot", {
            "format": "png", "captureBeyondViewport": False,
        })
        content = base64.b64decode(result["data"])
        path.write_bytes(content)
        assert path.exists() and path.stat().st_size > 5000
        assert content[:8] == b"\x89PNG\r\n\x1a\n"
        assert int.from_bytes(content[16:20], "big") == width
        assert int.from_bytes(content[20:24], "big") == height

    processes = []
    try:
        flow_number = 0
        for browser_name, browser in browsers.items():
            port = _free_port()
            profile = RUNTIME / f"{browser_name}-profile-{uuid.uuid4().hex}"
            profile.mkdir()
            stderr_path = RUNTIME / f"{browser_name}-stderr.txt"
            stderr_handle = stderr_path.open("w+", encoding="utf-8")
            process = subprocess.Popen([
                str(browser), "--headless=new", "--no-sandbox", "--disable-gpu",
                "--no-first-run", "--disable-features=msEdgeFirstRunExperience",
                "--no-default-browser-check", "--remote-allow-origins=*",
                f"--remote-debugging-port={port}", f"--user-data-dir={profile.resolve()}",
                "about:blank",
            ], stdout=subprocess.DEVNULL, stderr=stderr_handle)
            processes.append((process, stderr_handle, port))
            deadline = time.time() + 15
            while True:
                try:
                    with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version"):
                        break
                except OSError:
                    if time.time() > deadline:
                        stderr_handle.flush()
                        pytest.fail(
                            f"{browser_name} CDP failed (exit={process.poll()}): "
                            f"{stderr_path.read_text(encoding='utf-8')}"
                        )
                    time.sleep(0.1)
            for width, height in ((1280, 800), (1440, 900)):
                for zoom in (1, 2):
                    flow_number += 1
                    cdp = CDP.new_page(port, f"http://127.0.0.1:{server.server_port}/")
                    try:
                        cdp.call("Browser.setDownloadBehavior", {
                            "behavior": "allow", "downloadPath": str(downloads),
                        })
                        cdp.call("Emulation.setDeviceMetricsOverride", {
                            "width": width, "height": height,
                            "deviceScaleFactor": 1, "mobile": False,
                        })
                        cdp.call("Emulation.setPageScaleFactor", {"pageScaleFactor": zoom})
                        cdp.wait("document.querySelector('#sequence option')")
                        cdp.eval(
                            f"document.querySelector('#participant-code').value='B{flow_number}';"
                            "document.querySelector('#participant-code').focus();"
                            "document.querySelector('#sequence').value='A1';"
                        )
                        press(cdp, "Tab", "Tab", 9)
                        press(cdp, "Tab", "Tab", 9)
                        assert cdp.eval("document.activeElement.id") == "start-button"
                        press(cdp, "Enter", "Enter", 13)
                        cdp.wait("document.querySelector('[data-action=\"show-practice\"]')")
                        cdp.click("show-practice")
                        cdp.choose_and_click("practice-q1", "practice-q1")
                        cdp.choose_and_click("practice-q2", "practice-q2")
                        cdp.wait("document.querySelector('[data-action=\"begin-formal\"]')")
                        cdp.click("begin-formal")
                        captured = set()
                        for index in range(10):
                            cdp.wait(
                                "document.querySelector('[data-action=\"formal-q1\"]')"
                                " && !document.querySelector('[data-action=\"formal-q1\"]').disabled"
                            )
                            audit = cdp.eval("""(() => {
                              const card=document.querySelector('.evidence-card');
                              const rows=[...document.querySelectorAll('.evidence-row')];
                              const labels=rows.map(r=>r.querySelector('.evidence-label').innerText);
                              const forbidden=[...document.querySelectorAll('*')].flatMap(node =>
                                [...node.attributes].map(a=>a.name)).filter(name =>
                                /condition|stimulus|evidence-id|answer|correct|router/i.test(name));
                              const tabbable=[...document.querySelectorAll(
                                'button:not([disabled]),input:not([disabled]),select:not([disabled]),[tabindex="0"]'
                              )].map(node=>node.id||node.dataset.action||node.name);
                              return {
                                aria:card.getAttribute('aria-label'), rows:rows.length, labels,
                                cardWidth:card.getBoundingClientRect().width,
                                cardOverflow:card.scrollWidth>card.clientWidth,
                                documentOverflow:document.documentElement.scrollWidth>
                                  document.documentElement.clientWidth,
                                rowHeights:rows.map(r=>r.getBoundingClientRect().height),
                                labelWidths:rows.map(r=>r.querySelector('dt').getBoundingClientRect().width),
                                bodyWidths:rows.map(r=>r.querySelector('dd').getBoundingClientRect().width),
                                labelFonts:rows.map(r=>parseFloat(getComputedStyle(r.querySelector('dt')).fontSize)),
                                bodyFonts:rows.map(r=>parseFloat(getComputedStyle(r.querySelector('dd')).fontSize)),
                                forbidden, tabbable,
                                saveVisible:!document.querySelector('#save-exit-button').hidden
                              };
                            })()""")
                            assert audit["aria"] == "Evidence panel"
                            assert audit["rows"] == 5 and audit["saveVisible"]
                            assert not audit["cardOverflow"] and not audit["documentOverflow"]
                            assert audit["cardWidth"] <= 961
                            assert all(value >= 71 for value in audit["rowHeights"])
                            assert all(abs(value - 240) <= 1 for value in audit["labelWidths"])
                            assert all(abs(value - 648) <= 1 for value in audit["bodyWidths"])
                            assert audit["labelFonts"] == [14] * 5
                            assert audit["bodyFonts"] == [16] * 5
                            assert not audit["forbidden"]
                            assert "formal-q1" in audit["tabbable"]
                            condition = "flat" if audit["labels"][0].startswith("Evidence ") else "contract"
                            if condition not in captured:
                                screenshot(
                                    cdp,
                                    screenshots / (
                                        f"{browser_name}-{width}x{height}-z{zoom}-{condition}.png"
                                    ),
                                    width, height,
                                )
                                captured.add(condition)
                            press(cdp, "Tab", "Tab", 9)
                            assert cdp.eval("document.activeElement.name") == "formal-q1"
                            press(cdp, " ", "Space", 32)
                            press(cdp, "Tab", "Tab", 9)
                            assert cdp.eval("document.activeElement.dataset.action") == "formal-q1"
                            press(cdp, "Enter", "Enter", 13)
                            cdp.wait("document.activeElement?.name === 'formal-q2'")
                            press(cdp, " ", "Space", 32)
                            press(cdp, "Tab", "Tab", 9)
                            assert cdp.eval("document.activeElement.dataset.action") == "formal-q2"
                            press(cdp, "Enter", "Enter", 13)
                            if index in (4, 9):
                                cdp.wait("document.querySelector('[data-action=\"ease-skip\"]')")
                                cdp.click("ease-skip")
                        assert captured == {"contract", "flat"}
                        cdp.wait("document.querySelector('[data-action=\"diagnostic-skip\"]')")
                        cdp.click("diagnostic-skip")
                        cdp.wait("document.querySelector('[data-action=\"download-json\"]')")
                        before_json = len(list(downloads.glob("*.json")))
                        before_csv = len(list(downloads.glob("*.csv")))
                        cdp.click("download-json")
                        cdp.click("download-csv")
                        deadline = time.time() + 10
                        while (
                            len(list(downloads.glob("*.json"))) <= before_json
                            or len(list(downloads.glob("*.csv"))) <= before_csv
                        ):
                            if time.time() > deadline:
                                pytest.fail("browser downloads did not complete")
                            time.sleep(0.1)
                    finally:
                        cdp.close()
            if browser_name == next(iter(browsers)):
                cdp = CDP.new_page(port, f"http://127.0.0.1:{server.server_port}/")
                try:
                    cdp.call("Browser.setDownloadBehavior", {
                        "behavior": "allow", "downloadPath": str(downloads),
                    })
                    cdp.wait("document.querySelector('#sequence option')")
                    cdp.eval(
                        "document.querySelector('#participant-code').value='BPARTIAL';"
                        "document.querySelector('#sequence').value='A1';"
                        "document.querySelector('#start-button').click()"
                    )
                    cdp.wait("document.querySelector('[data-action=\"show-practice\"]')")
                    cdp.click("show-practice")
                    cdp.choose_and_click("practice-q1", "practice-q1")
                    cdp.choose_and_click("practice-q2", "practice-q2")
                    cdp.wait("document.querySelector('[data-action=\"begin-formal\"]')")
                    cdp.click("begin-formal")
                    cdp.wait("!document.querySelector('#save-exit-button').hidden")
                    before_json = len(list(downloads.glob("*.json")))
                    before_csv = len(list(downloads.glob("*.csv")))
                    cdp.eval("document.querySelector('#save-exit-button').click()")
                    cdp.wait("document.body.innerText.includes('Session ended')")
                    deadline = time.time() + 10
                    while (
                        len(list(downloads.glob("*.json"))) <= before_json
                        or len(list(downloads.glob("*.csv"))) <= before_csv
                    ):
                        if time.time() > deadline:
                            pytest.fail("partial browser downloads did not complete")
                        time.sleep(0.1)
                    assert "performance feedback" in cdp.eval("document.body.innerText").lower()
                finally:
                    cdp.close()
            control = CDP.new_page(port, "about:blank")
            control.call("Browser.close")
            control.socket.close()
            if process.poll() is None:
                process.wait(timeout=10)
            stderr_handle.close()
            processes.remove((process, stderr_handle, port))
        assert len(list(screenshots.glob("*.png"))) == len(browsers) * 8
        validated = [
            validate_export(json.loads(path.read_text(encoding="utf-8")), TEST_KEY)
            for path in downloads.glob("*.json")
        ]
        assert any(data["complete"] is False and len(data["trials"]) == 10 for data in validated)
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
        for process, stderr_handle, port in processes:
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
        shutil.rmtree(RUNTIME, ignore_errors=True)
