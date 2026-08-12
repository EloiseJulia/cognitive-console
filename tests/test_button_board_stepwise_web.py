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

from cognitive_console.button_board_stepwise.analysis import (
    ExportError,
    analyze,
    load_exports,
    trial_scores,
    validate_export,
)
from cognitive_console.button_board_stepwise.server import (
    CSP,
    STATIC_DIR,
    create_server,
)
from cognitive_console.button_board_stepwise_materials import (
    EXPORT_SCHEMA_VERSION,
    MATERIAL_SCHEMA_VERSION,
    MATERIALS_VERSION,
)
from cognitive_console.microstudy.server import sign_export


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / ".runtime" / "tests-button-board-stepwise-v11"
TEST_KEY = b"stepwise-button-board-test-key-32!!"
CLIENTS: dict[str, dict] = {}
PRIVATE_KEYS = {
    "expected_answer_by_step",
    "expected_exit_answer",
    "expected_decisive_step",
    "expected_state",
    "comparison_rule",
    "required_readings",
    "required_scope_dimensions",
    "scope_correct",
    "scope_written",
    "gaa_correct",
    "strict_correct",
}


def nested_keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from nested_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from nested_keys(item)


def assert_no_private_keys(value):
    assert PRIVATE_KEYS.isdisjoint(nested_keys(value))


def request_json(base, path, body=None, *, headers=None, request_id=None):
    client = CLIENTS.setdefault(base, {"csrf": None, "capabilities": {}})
    request_headers = dict(headers or {})
    data = None
    if body is not None:
        body = dict(body)
        body.setdefault("request_id", request_id or uuid.uuid4().hex)
        data = json.dumps(body).encode()
        request_headers.update(
            {
                "Content-Type": "application/json",
                "Origin": base,
                "X-CSRF-Token": client["csrf"],
            }
        )
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
        method="POST" if data is not None else "GET",
    )
    with urllib.request.urlopen(request) as response:
        value = json.load(response)
    if path == "/api/bootstrap":
        client["csrf"] = value["csrf_token"]
    if path == "/api/start":
        client["capabilities"][value["attempt_id"]] = value["capability"]
    assert_no_private_keys(value)
    return value


@pytest.fixture
def live_server():
    shutil.rmtree(RUNTIME, ignore_errors=True)
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
        CLIENTS.pop(base, None)
        shutil.rmtree(RUNTIME, ignore_errors=True)


def welcome(base, locale="en"):
    return request_json(base, f"/api/welcome?selected_locale={locale}")


def start(base, participant="P1", locale="en"):
    return request_json(
        base,
        "/api/start",
        {"participant_code": participant, "selected_locale": locale},
    )


def answer_step(base, attempt, step, answer):
    return request_json(
        base,
        "/api/step",
        {"attempt_id": attempt, "step": int(step), "answer": answer},
    )


def advance_practice(base, attempt):
    current = request_json(base, "/api/continue", {"attempt_id": attempt})
    assert current["phase"] == "practice_step"
    for step, answer in ((1, "CONTROL"), (2, "COMPARED"), (3, "NOT_BETTER")):
        current = answer_step(base, attempt, step, answer)
    assert current["phase"] == "practice_result"
    assert "6/10" in current["feedback"] and "8/10" in current["feedback"]
    current = request_json(base, "/api/continue", {"attempt_id": attempt})
    assert current["phase"] == "formal_intro"
    return current


def complete_attempt(
    base,
    server,
    participant="P-COMPLETE",
    locale="en",
    wrong_scope_scene=None,
):
    materials = welcome(base, locale)
    created = start(base, participant, locale)
    attempt = created["attempt_id"]
    advance_practice(base, attempt)
    current = request_json(base, "/api/continue", {"attempt_id": attempt})
    for _ in range(6):
        session = server.sessions[attempt]
        slot = session["plan"][session["index"]]
        for step, expected in slot["expected_answer_by_step"].items():
            answer = expected
            if int(step) == 6 and slot["scene_id"] == wrong_scope_scene:
                answer = next(
                    option_id
                    for option_id in slot["scope_order_ids"]
                    if option_id != expected
                )
            current = answer_step(base, attempt, step, answer)
        assert current["phase"] == "formal_result"
        assert "correct" not in json.dumps(current).lower()
        current = request_json(base, "/api/continue", {"attempt_id": attempt})
    assert current["phase"] == "attention"
    request_json(base, "/api/attention", {"attempt_id": attempt, "answer": "INFO"})
    options = materials["common"]["reflection"]["options"]
    request_json(
        base,
        "/api/reflection",
        {
            "attempt_id": attempt,
            **{field: rows[0]["id"] for field, rows in options.items()},
        },
    )
    request_json(base, "/api/complete", {"attempt_id": attempt})
    return request_json(base, f"/api/export?attempt_id={attempt}&format=json")


def test_headers_selected_locale_step_payload_and_no_private_keys(live_server):
    base, _ = live_server
    output = io.StringIO()
    with contextlib.redirect_stderr(output):
        with urllib.request.urlopen(f"{base}/") as response:
            assert response.headers["Content-Security-Policy"] == CSP
            assert response.headers["Cache-Control"] == "no-store"
            assert response.headers.get("Access-Control-Allow-Origin") is None
        bootstrap = request_json(base, "/api/bootstrap")
        english = welcome(base, "en")
        chinese = welcome(base, "zh-Hans")
    assert bootstrap["minimum_width_px"] == 1024
    assert bootstrap["fallback"] is None and bootstrap["auto_detect"] is False
    assert english["selected_locale"] == "en"
    assert chinese["selected_locale"] == "zh-Hans"
    assert "questions" not in english["common"]
    assert english["practice"]["title"] != chinese["practice"]["title"]
    created = start(base, "PAYLOAD", "en")
    current = request_json(
        base,
        "/api/continue",
        {"attempt_id": created["attempt_id"]},
    )
    assert current["step"] == 1
    assert set(current) == {
        "phase",
        "step",
        "question",
        "options",
        "progress",
        "scene",
    }
    assert len(current["options"]) == 2
    assert current["scene"]["card"]["facts"]
    assert output.getvalue() == ""


def test_success_only_allocation_balances_sequence_and_ab_per_locale(live_server):
    base, server = live_server
    rows = [start(base, f"P-{index:02d}", "en") for index in range(24)]
    sessions = [server.sessions[row["attempt_id"]] for row in rows]
    assert Counter(row["sequence_id"] for row in sessions) == {
        f"BBS11-{index:02d}": 2 for index in range(1, 13)
    }
    assert Counter(row["ab_variant"] for row in sessions) == {"A": 12, "B": 12}
    for session in sessions:
        ids = {row["scene_id"] for row in session["plan"]}
        assert not {"AB1-A", "AB1-B"} <= ids
        assert f"AB1-{session['ab_variant']}" in ids
    assert server.locale_allocation_counts["zh-Hans"] == 0


def test_complete_signed_raw_export_and_analysis(live_server):
    base, server = live_server
    export = complete_attempt(base, server)
    assert export["schema_version"] == MATERIAL_SCHEMA_VERSION
    assert export["export_schema_version"] == EXPORT_SCHEMA_VERSION
    assert export["materials_version"] == MATERIALS_VERSION
    assert export["complete"] is True
    assert len(export["trials"]) == 6
    assert_no_private_keys(export)
    validated = validate_export(export, TEST_KEY)
    plan = server.sessions[export["attempt_id"]]["plan"]
    scores = [
        trial_scores(trial, slot)
        for trial, slot in zip(validated["trials"], plan)
    ]
    assert all(row["gaa_trial"] is True for row in scores)
    assert all(row["strict_gaa_trial"] is True for row in scores)
    summary = analyze([validated])
    assert summary["participant_count"] == 1
    assert summary["mean_gaa_rate_complete"] == 1
    assert summary["mean_strict_rate_complete"] == 1
    csv_url = (
        f"/api/export?attempt_id={export['attempt_id']}&format=csv"
    )
    request = urllib.request.Request(
        f"{base}{csv_url}",
        headers={"X-Study-Capability": CLIENTS[base]["capabilities"][export["attempt_id"]]},
    )
    with urllib.request.urlopen(request) as response:
        csv_text = response.read().decode("utf-8-sig")
    assert "step_selected_option_id" in csv_text
    assert "expected_state" not in csv_text


def test_wrong_supported_scope_keeps_gaa_and_removes_strict(live_server):
    base, server = live_server
    export = complete_attempt(
        base,
        server,
        participant="WRONG-SCOPE",
        wrong_scope_scene="F6",
    )
    validated = validate_export(export, TEST_KEY)
    plan = server.sessions[export["attempt_id"]]["plan"]
    scored = {
        trial["scene_id"]: trial_scores(trial, slot)
        for trial, slot in zip(validated["trials"], plan)
    }
    assert scored["F6"]["gaa_trial"] is True
    assert scored["F6"]["path_exact"] is False
    assert scored["F6"]["decisive_read_correct"] is False
    assert scored["F6"]["strict_gaa_trial"] is False
    assert all(
        row["strict_gaa_trial"] is True
        for scene_id, row in scored.items()
        if scene_id != "F6"
    )
    summary = analyze([validated])
    assert summary["mean_gaa_rate_complete"] == 1
    assert summary["mean_strict_rate_complete"] == pytest.approx(5 / 6)


def test_same_state_wrong_decisive_path_gets_gaa_not_strict(live_server):
    base, server = live_server
    materials = welcome(base)
    created = start(base, "ALT-WITHHELD")
    attempt = created["attempt_id"]
    advance_practice(base, attempt)
    request_json(base, "/api/continue", {"attempt_id": attempt})
    while True:
        session = server.sessions[attempt]
        slot = session["plan"][session["index"]]
        if slot["scene_id"] == "F3":
            for step, answer in ((1, "CONTROL"), (2, "COMPARED"), (3, "NOT_BETTER")):
                current = answer_step(base, attempt, step, answer)
        else:
            for step, answer in slot["expected_answer_by_step"].items():
                current = answer_step(base, attempt, step, answer)
        current = request_json(base, "/api/continue", {"attempt_id": attempt})
        if current["phase"] == "attention":
            break
    request_json(base, "/api/attention", {"attempt_id": attempt, "answer": "INFO"})
    options = materials["common"]["reflection"]["options"]
    request_json(
        base,
        "/api/reflection",
        {"attempt_id": attempt, **{key: rows[0]["id"] for key, rows in options.items()}},
    )
    request_json(base, "/api/complete", {"attempt_id": attempt})
    export = request_json(base, f"/api/export?attempt_id={attempt}&format=json")
    trial = next(row for row in export["trials"] if row["scene_id"] == "F3")
    slot = next(row for row in server.sessions[attempt]["plan"] if row["scene_id"] == "F3")
    score = trial_scores(trial, slot)
    assert trial["participant_derived_state"] == "WITHHELD"
    assert score["gaa_trial"] is True
    assert score["strict_gaa_trial"] is False


def test_early_exit_hides_later_steps_and_attention_is_not_formal(live_server):
    base, server = live_server
    created = start(base, "EARLY")
    attempt = created["attempt_id"]
    response = request_json(base, "/api/continue", {"attempt_id": attempt})
    response = answer_step(base, attempt, 1, "INFO")
    assert response["phase"] == "practice_result"
    assert [row["step"] for row in response["path"]] == [1]
    trial = server.sessions[attempt]["practice_trial"]
    assert trial["step_presented"] == [1]
    assert trial["participant_derived_state"] == "DIAGNOSTIC"


def test_partial_signature_tamper_wrong_key_and_cross_version_hardfail(live_server):
    base, _ = live_server
    created = start(base, "PARTIAL")
    attempt = created["attempt_id"]
    advance_practice(base, attempt)
    request_json(base, "/api/continue", {"attempt_id": attempt})
    request_json(base, "/api/save-exit", {"attempt_id": attempt})
    partial = request_json(base, f"/api/export?attempt_id={attempt}&format=json")
    assert partial["complete"] is False
    assert validate_export(partial, TEST_KEY)
    tampered = copy.deepcopy(partial)
    tampered["participant_code"] = "CHANGED"
    with pytest.raises(ExportError, match="signature"):
        validate_export(tampered, TEST_KEY)
    with pytest.raises(ExportError, match="wrong verification key"):
        validate_export(partial, b"another-key-that-is-long-enough!!")
    for old_version in (
        "microstudy-export-v5-scenario-bilingual-signed",
        "microstudy-export-v7-button-board-raw-signed",
        "microstudy-export-v9-invented",
    ):
        old = copy.deepcopy(partial)
        old["export_schema_version"] = old_version
        old = sign_export(old, TEST_KEY)
        with pytest.raises(ExportError, match="V5/V6/V7/V9/V11"):
            validate_export(old, TEST_KEY)
    leaked = copy.deepcopy(partial)
    leaked["trials"][0]["expected_state"] = "SUPPORTED"
    leaked = sign_export(leaked, TEST_KEY)
    with pytest.raises(ExportError, match="private or score-derived"):
        validate_export(leaked, TEST_KEY)


def test_request_security_idempotency_capacity_and_memory_only(live_server):
    base, server = live_server
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(
            urllib.request.Request(
                f"{base}/api/bootstrap",
                headers={"Host": "evil.example"},
            )
        )
    assert exc.value.code == 403
    csrf = CLIENTS[base]["csrf"]
    body = json.dumps(
        {
            "participant_code": "BAD-ORIGIN",
            "selected_locale": "en",
            "request_id": uuid.uuid4().hex,
        }
    ).encode()
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(
            urllib.request.Request(
                f"{base}/api/start",
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "Origin": "http://evil.example",
                    "X-CSRF-Token": csrf,
                },
                method="POST",
            )
        )
    assert exc.value.code == 403
    request_id = uuid.uuid4().hex
    first = request_json(
        base,
        "/api/start",
        {"participant_code": "IDEMP", "selected_locale": "en"},
        request_id=request_id,
    )
    second = request_json(
        base,
        "/api/start",
        {"participant_code": "IDEMP", "selected_locale": "en"},
        request_id=request_id,
    )
    assert first == second
    assert server.attempt_serial == 1
    attempt = first["attempt_id"]
    capability = CLIENTS[base]["capabilities"][attempt]
    CLIENTS[base]["capabilities"][attempt] = "wrong"
    with pytest.raises(urllib.error.HTTPError):
        request_json(base, "/api/continue", {"attempt_id": attempt})
    CLIENTS[base]["capabilities"][attempt] = capability
    assert not any(RUNTIME.glob("*.json"))
    with pytest.raises(ValueError, match="loopback"):
        create_server("0.0.0.0", 0, RUNTIME / "bad.key")

    tiny_key = RUNTIME / "capacity.key"
    tiny_key.write_bytes(TEST_KEY)
    tiny = create_server("127.0.0.1", 0, tiny_key, max_sessions=1)
    thread = threading.Thread(target=tiny.serve_forever, daemon=True)
    thread.start()
    tiny_base = f"http://127.0.0.1:{tiny.server_port}"
    try:
        request_json(tiny_base, "/api/bootstrap")
        start(tiny_base, "ONE")
        with pytest.raises(urllib.error.HTTPError):
            start(tiny_base, "TWO")
    finally:
        tiny.shutdown()
        tiny.server_close()
        thread.join(10)
        CLIENTS.pop(tiny_base, None)


def test_failed_requests_do_not_renew_ttl():
    shutil.rmtree(RUNTIME, ignore_errors=True)
    RUNTIME.mkdir(parents=True, exist_ok=True)
    key_path = RUNTIME / "ttl.key"
    key_path.write_bytes(TEST_KEY)
    server = create_server(
        "127.0.0.1",
        0,
        key_path,
        session_ttl_seconds=0.08,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        request_json(base, "/api/bootstrap")
        created = start(base, "TTL")
        attempt = created["attempt_id"]
        original = server.sessions[attempt]["last_seen"]
        time.sleep(0.04)
        with pytest.raises(urllib.error.HTTPError):
            answer_step(base, attempt, 3, "BETTER")
        assert server.sessions[attempt]["last_seen"] == original
        time.sleep(0.06)
        request_json(base, "/api/bootstrap")
        assert attempt not in server.sessions
    finally:
        server.shutdown()
        server.server_close()
        thread.join(10)
        CLIENTS.pop(base, None)
        shutil.rmtree(RUNTIME, ignore_errors=True)


def test_load_exports_rejects_duplicates_and_mixed_versions(live_server):
    base, server = live_server
    data = complete_attempt(base, server, "LOAD-1")
    first = RUNTIME / "one.json"
    second = RUNTIME / "two.json"
    first.write_text(json.dumps(data), encoding="utf-8")
    second.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ExportError, match="duplicate export"):
        load_exports([first, second], TEST_KEY)
    mixed = copy.deepcopy(data)
    mixed["export_schema_version"] = "microstudy-export-v7-button-board-raw-signed"
    mixed = sign_export(mixed, TEST_KEY)
    second.write_text(json.dumps(mixed), encoding="utf-8")
    with pytest.raises(ExportError, match="V5/V6/V7/V9/V11"):
        load_exports([first, second], TEST_KEY)


def test_static_open_book_aria_privacy_keyboard_and_desktop_contract():
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    js = (STATIC_DIR / "study.js").read_text(encoding="utf-8")
    css = (STATIC_DIR / "study.css").read_text(encoding="utf-8")
    assert 'lang="und"' in html
    assert "data-locale" in html and "disabled" in html
    assert "study-layout" in css and "300px" in css
    assert "position: sticky" in css
    assert "scope-segments" in css and "grid-template-columns" in css
    assert "focus-visible" in css and "prefers-reduced-motion" in css
    assert "@media (max-width: 1023px)" in css
    assert "showModal()" in js
    assert "localStorage" not in js and "sessionStorage" not in js
    assert "performance.now" not in js
    assert "innerHTML" not in js
    assert "expected_state" not in html.lower()


def _free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def test_real_chrome_edge_en_zh_100_200_keyboard_aria_complete_partial():
    pytest.importorskip("websocket")
    from browser_cdp import CDP

    candidates = {
        "edge": Path(
            os.environ.get(
                "EDGE_PATH",
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            )
        ),
        "chrome": Path(
            os.environ.get(
                "CHROME_PATH",
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            )
        ),
    }
    browsers = {name: path for name, path in candidates.items() if path.exists()}
    assert set(browsers) == {"chrome", "edge"}, "Chrome and Edge are required"
    shutil.rmtree(RUNTIME, ignore_errors=True)
    RUNTIME.mkdir(parents=True, exist_ok=True)

    @contextlib.contextmanager
    def browser_process(name, executable):
        port = _free_port()
        profile = RUNTIME / f"{name}-profile-{uuid.uuid4().hex}"
        profile.mkdir()
        process = subprocess.Popen(
            [
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
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        deadline = time.time() + 15
        while True:
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version").close()
                break
            except OSError:
                if time.time() > deadline:
                    pytest.fail(f"{name} CDP startup failed")
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
            shutil.rmtree(profile, ignore_errors=True)

    @contextlib.contextmanager
    def isolated_server(label):
        key_path = RUNTIME / f"{label}-{uuid.uuid4().hex}.key"
        key_path.write_bytes(TEST_KEY)
        server = create_server("127.0.0.1", 0, key_path)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            urllib.request.urlopen(f"{base}/api/bootstrap").close()
            yield base, server
        finally:
            server.shutdown()
            server.server_close()
            thread.join(10)
            key_path.unlink(missing_ok=True)

    def open_page(port, base, width=1440, height=900, zoom=1):
        cdp = CDP.new_page(port, "about:blank")
        cdp.call(
            "Emulation.setDeviceMetricsOverride",
            {
                "width": width,
                "height": height,
                "deviceScaleFactor": 1,
                "mobile": False,
            },
        )
        cdp.call("Emulation.setPageScaleFactor", {"pageScaleFactor": zoom})
        cdp.call("Page.navigate", {"url": f"{base}/"})
        return cdp

    def click_answer(cdp, value, *, keyboard=False):
        cdp.wait(f'document.querySelector(\'input[name="step-answer"][value="{value}"]\')')
        selector = f'document.querySelector(\'input[name="step-answer"][value="{value}"]\')'
        if keyboard:
            cdp.eval(f"{selector}.focus(); {selector}.click()")
            assert cdp.eval("document.activeElement.name") == "step-answer"
            cdp.eval("document.querySelector('[data-action=\"submit-step\"]').focus()")
            cdp.call(
                "Input.dispatchKeyEvent",
                {
                    "type": "keyDown",
                    "key": "Enter",
                    "code": "Enter",
                    "windowsVirtualKeyCode": 13,
                    "text": "\r",
                },
            )
            cdp.call(
                "Input.dispatchKeyEvent",
                {
                    "type": "keyUp",
                    "key": "Enter",
                    "code": "Enter",
                    "windowsVirtualKeyCode": 13,
                },
            )
        else:
            cdp.eval(
                f"{selector}.checked=true;"
                "document.querySelector('[data-action=\"submit-step\"]').click()"
            )

    cases = [
        ("en", 1),
        ("en", 2),
        ("zh-Hans", 1),
        ("zh-Hans", 2),
    ]
    try:
        for browser_name, executable in browsers.items():
            with browser_process(browser_name, executable) as port:
                for case_index, (locale, zoom) in enumerate(cases):
                    with isolated_server(f"{browser_name}-{locale}-{zoom}") as (base, server):
                        cdp = open_page(port, base, zoom=zoom)
                        try:
                            cdp.wait(
                                "window.StepwiseButtonBoardTest && window.StepwiseButtonBoardTest.ready"
                            )
                            cdp.eval(
                                f'document.querySelector(\'[data-locale="{locale}"]\').click()'
                            )
                            cdp.wait("document.querySelector('#participant-code')")
                            assert cdp.eval("document.documentElement.lang") == locale
                            cdp.eval(
                                "document.querySelector('#participant-code').value="
                                + json.dumps(f"{browser_name[0]}-{case_index}")
                            )
                            cdp.click("start")
                            cdp.wait("document.querySelector('[data-action=\"show-practice\"]')")
                            cdp.click("show-practice")
                            for index, answer in enumerate(("CONTROL", "COMPARED", "NOT_BETTER")):
                                click_answer(cdp, answer, keyboard=index == 0)
                            cdp.wait(
                                "document.querySelector('[data-action=\"continue-after-result\"]')"
                            )
                            cdp.click("continue-after-result")
                            cdp.wait("document.querySelector('[data-action=\"begin-formal\"]')")
                            cdp.click("begin-formal")
                            for trial_index in range(6):
                                cdp.wait(
                                    "window.StepwiseButtonBoardTest.currentStep === 1"
                                )
                                attempt = next(iter(server.sessions))
                                session = server.sessions[attempt]
                                slot = session["plan"][session["index"]]
                                for step, answer in slot["expected_answer_by_step"].items():
                                    cdp.wait(
                                        f"window.StepwiseButtonBoardTest.currentStep === {int(step)}"
                                    )
                                    audit = cdp.eval(
                                        """(() => {
                                          const card=document.querySelector('.record-card');
                                          const question=document.querySelector('.question-card');
                                          const aside=document.querySelector('.reference-panel');
                                          const html=document.querySelector('#stage').outerHTML;
                                          const rect=aside?.getBoundingClientRect();
                                          const choices=[...document.querySelectorAll('.choice')]
                                            .map(node=>node.getBoundingClientRect().height);
                                          return {
                                            card:Boolean(card), question:Boolean(question),
                                            aside:Boolean(aside), asideWidth:rect?.width,
                                            questions:document.querySelectorAll('.question-card').length,
                                            choiceHeights:choices,
                                            overflow:document.documentElement.scrollWidth >
                                              document.documentElement.clientWidth,
                                            private:/expected_state|comparison_rule|scope_correct|gaa_correct/i.test(html),
                                            activeTag:document.activeElement?.tagName,
                                          };
                                        })()"""
                                    )
                                    assert audit["card"] and audit["question"] and audit["aside"]
                                    assert audit["questions"] == 1
                                    assert audit["asideWidth"] == pytest.approx(300, abs=1)
                                    assert not audit["overflow"] and not audit["private"]
                                    assert audit["activeTag"] in {"H1", "H2"}
                                    if int(step) == 6:
                                        assert max(audit["choiceHeights"]) - min(
                                            audit["choiceHeights"]
                                        ) <= 1
                                    click_answer(
                                        cdp,
                                        answer,
                                        keyboard=(
                                            (trial_index == 0 and int(step) == 1)
                                            or int(step) == 6
                                        ),
                                    )
                                cdp.wait(
                                    "document.querySelector('[data-action=\"continue-after-result\"]')"
                                )
                                assert cdp.eval(
                                    "document.querySelector('.result-card').innerText.includes("
                                    "window.StepwiseButtonBoardTest.materials.common.labels.result)"
                                )
                                cdp.click("continue-after-result")
                            cdp.wait("document.querySelector('[data-action=\"submit-attention\"]')")
                            cdp.eval(
                                "document.querySelector('input[name=\"attention-answer\"][value=\"INFO\"]').checked=true;"
                                "document.querySelector('[data-action=\"submit-attention\"]').click()"
                            )
                            cdp.wait("document.querySelector('[data-action=\"submit-reflection\"]')")
                            cdp.click("submit-reflection")
                            cdp.wait("document.querySelector('[data-action=\"download-json\"]')")
                            attempt = next(iter(server.sessions))
                            assert server.sessions[attempt]["phase"] == "export_ready"
                            assert cdp.eval(
                                "!/expected_state|comparison_rule|scope_correct|gaa_correct/i.test("
                                "document.querySelector('#stage').outerHTML)"
                            )
                        finally:
                            cdp.close()
                with isolated_server(f"{browser_name}-partial") as (base, server):
                    cdp = open_page(port, base)
                    try:
                        cdp.wait(
                            "window.StepwiseButtonBoardTest && window.StepwiseButtonBoardTest.ready"
                        )
                        cdp.eval("document.querySelector('[data-locale=\"en\"]').click()")
                        cdp.wait("document.querySelector('#participant-code')")
                        cdp.eval("document.querySelector('#participant-code').value='partial-browser'")
                        cdp.click("start")
                        cdp.wait("document.querySelector('[data-action=\"show-practice\"]')")
                        cdp.click("show-practice")
                        for answer in ("CONTROL", "COMPARED", "NOT_BETTER"):
                            click_answer(cdp, answer)
                        cdp.wait("document.querySelector('[data-action=\"continue-after-result\"]')")
                        cdp.click("continue-after-result")
                        cdp.wait("document.querySelector('[data-action=\"begin-formal\"]')")
                        cdp.click("begin-formal")
                        cdp.wait("document.querySelector('#save-exit-button:not([hidden])')")
                        cdp.click("save-exit")
                        cdp.wait("document.querySelector('#save-exit-dialog[open]')")
                        cdp.click("confirm-save-exit")
                        cdp.wait("document.querySelector('[data-action=\"download-json\"]')")
                        attempt = next(iter(server.sessions))
                        assert server.sessions[attempt]["signed_export"]["complete"] is False
                    finally:
                        cdp.close()
                with isolated_server(f"{browser_name}-desktop") as (base, _):
                    cdp = open_page(port, base, width=1023, height=800)
                    try:
                        cdp.wait("window.StepwiseButtonBoardTest")
                        assert cdp.eval(
                            "getComputedStyle(document.querySelector('#desktop-blocker')).display"
                            " !== 'none' && getComputedStyle(document.querySelector('#app')).display"
                            " === 'none'"
                        )
                    finally:
                        cdp.close()
    finally:
        shutil.rmtree(RUNTIME, ignore_errors=True)
