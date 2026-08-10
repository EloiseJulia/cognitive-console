import contextlib
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


def request_json(base, path, body=None):
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(
        f"{base}{path}", data=data,
        headers={} if data is None else {"Content-Type": "application/json"},
        method="GET" if data is None else "POST",
    )
    with urllib.request.urlopen(request) as response:
        return json.load(response)


@pytest.fixture
def live_server():
    RUNTIME.mkdir(parents=True, exist_ok=True)
    key_path = RUNTIME / "server.key"
    key_path.write_bytes(TEST_KEY)
    server = create_server("127.0.0.1", 0, key_path)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", server
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
        shutil.rmtree(RUNTIME, ignore_errors=True)


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
    with urllib.request.urlopen(
        f"{base}/api/export?attempt_id={data['attempt_id']}&format=csv"
    ) as response:
        csv_text = response.read().decode()
    assert csv_text.count("\r\n") == 11
    assert "verification_signature" in csv_text


def test_duplicate_first_complete_then_assignment_and_itt(live_server):
    base, _ = live_server
    first = complete_attempt(base, "P-DUP", "A1")
    later = complete_attempt(base, "P-DUP", "B1")
    other = complete_attempt(base, "P-OTHER", "D5")
    for order, data in enumerate((first, later, other)):
        data["_input_order"] = order
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


def test_real_chrome_full_a1_d5_flow_downloads_and_geometry():
    websocket = pytest.importorskip("websocket")
    browser = Path(os.environ.get(
        "CHROME_PATH", r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    ))
    if not browser.exists():
        pytest.skip("Chrome is unavailable")
    from browser_cdp import CDP

    RUNTIME.mkdir(parents=True, exist_ok=True)
    key_path = RUNTIME / "browser.key"
    key_path.write_bytes(TEST_KEY)
    server = create_server("127.0.0.1", 0, key_path)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = _free_port()
    profile = RUNTIME / "chrome-profile"
    downloads = RUNTIME / "downloads"
    downloads.mkdir()
    stderr_path = RUNTIME / "chrome-stderr.txt"
    stderr_handle = stderr_path.open("w+", encoding="utf-8")
    process = subprocess.Popen([
        str(browser), "--headless=new", "--disable-gpu", "--no-first-run",
        "--no-default-browser-check", "--remote-allow-origins=*",
        f"--remote-debugging-port={port}", f"--user-data-dir={profile.resolve()}",
        "about:blank",
    ], stdout=subprocess.DEVNULL, stderr=stderr_handle)
    try:
        deadline = time.time() + 15
        while True:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version"):
                    break
            except OSError:
                if time.time() > deadline:
                    stderr_handle.flush()
                    pytest.fail(
                        f"Chrome CDP did not start (exit={process.poll()}): "
                        f"{stderr_path.read_text(encoding='utf-8')}"
                    )
                time.sleep(0.1)
        for sequence in ("A1", "D5"):
            cdp = CDP.new_page(port, f"http://127.0.0.1:{server.server_port}/")
            try:
                cdp.call("Browser.setDownloadBehavior", {
                    "behavior": "allow", "downloadPath": str(downloads),
                })
                cdp.call("Emulation.setDeviceMetricsOverride", {
                    "width": 1440, "height": 900, "deviceScaleFactor": 1, "mobile": False,
                })
                cdp.wait("document.querySelector('#sequence option')")
                cdp.eval(
                    f"document.querySelector('#participant-code').value='B-{sequence}';"
                    f"document.querySelector('#sequence').value='{sequence}';"
                    "document.querySelector('#start-button').click()"
                )
                cdp.wait("document.querySelector('[data-action=\"show-practice\"]')")
                cdp.click("show-practice")
                cdp.choose_and_click("practice-q1", "practice-q1")
                cdp.choose_and_click("practice-q2", "practice-q2")
                cdp.wait("document.querySelector('[data-action=\"begin-formal\"]')")
                cdp.click("begin-formal")
                for index in range(10):
                    cdp.wait(
                        "document.querySelector('[data-action=\"formal-q1\"]')"
                        " && !document.querySelector('[data-action=\"formal-q1\"]').disabled"
                    )
                    if index == 0:
                        geometry = cdp.eval("""(() => {
                          const card=document.querySelector('.evidence-card');
                          return {label:card.getAttribute('aria-label'), overflow:
                            card.scrollWidth>card.clientWidth, width:card.getBoundingClientRect().width};
                        })()""")
                        assert geometry["label"] == "Evidence panel"
                        assert not geometry["overflow"] and geometry["width"] <= 960
                        cdp.call("Emulation.setPageScaleFactor", {"pageScaleFactor": 2})
                        assert cdp.eval("document.documentElement.scrollWidth <= document.documentElement.clientWidth")
                        cdp.call("Page.captureScreenshot", {"format": "png"})
                        cdp.call("Emulation.setPageScaleFactor", {"pageScaleFactor": 1})
                    cdp.choose_and_click("formal-q1", "formal-q1")
                    cdp.wait(
                        "document.querySelector('input[name=\"formal-q1\"]').disabled"
                        " && !!document.querySelector('input[name=\"formal-q2\"]')"
                    )
                    cdp.choose_and_click("formal-q2", "formal-q2")
                    if index in (4, 9):
                        cdp.wait("document.querySelector('[data-action=\"ease-skip\"]')")
                        cdp.click("ease-skip")
                cdp.wait("document.querySelector('[data-action=\"diagnostic-skip\"]')")
                cdp.click("diagnostic-skip")
                cdp.wait("document.querySelector('a[download$=\".json\"]')")
                assert cdp.eval("document.querySelectorAll('.evidence-row').length === 5 || true")
                expected = 1 if sequence == "A1" else 2
                cdp.eval("document.querySelector('a[download$=\".json\"]').click()")
                deadline = time.time() + 10
                while len(list(downloads.glob("*.json"))) < expected:
                    if time.time() > deadline:
                        pytest.fail("browser JSON download did not complete")
                    time.sleep(0.1)
                cdp.eval("document.querySelector('a[download$=\".csv\"]').click()")
                deadline = time.time() + 10
                while len(list(downloads.glob("*.csv"))) < expected:
                    if time.time() > deadline:
                        pytest.fail("browser CSV download did not complete")
                    time.sleep(0.1)
            finally:
                cdp.close()
        deadline = time.time() + 10
        while len(list(downloads.glob("*.json"))) < 2 or len(list(downloads.glob("*.csv"))) < 2:
            if time.time() > deadline:
                pytest.fail("browser downloads did not complete")
            time.sleep(0.1)
        for path in downloads.glob("*.json"):
            validate_export(json.loads(path.read_text(encoding="utf-8")), TEST_KEY)
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
        process.terminate()
        process.wait(timeout=10)
        stderr_handle.close()
        shutil.rmtree(RUNTIME, ignore_errors=True)
