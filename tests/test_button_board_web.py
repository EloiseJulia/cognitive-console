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

from cognitive_console.button_board.analysis import (
    ExportError,
    analyze,
    load_exports,
    validate_export,
    v9_compat_trial,
)
from cognitive_console.button_board.materials import q1_state_to_public
from cognitive_console.button_board.server import (
    CSP,
    STATIC_DIR,
    ButtonBoardHandler,
    create_server,
)
from cognitive_console.button_board_materials import (
    ANALYSIS_VERSION,
    EXPORT_SCHEMA_VERSION,
    MATERIAL_SCHEMA_VERSION,
    MATERIALS_VERSION,
)
from cognitive_console.microstudy.server import sign_export


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / ".runtime" / "tests-button-board-v10"
TEST_KEY = b"button-board-test-key-32-bytes!!"
CLIENTS: dict[str, dict] = {}


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


def advance_practice(base, attempt, common):
    q1 = common["q1_options"][0]["id"]
    response = request_json(
        base,
        "/api/practice",
        {"attempt_id": attempt, "step": "q1", "answer": q1},
    )
    response = request_json(
        base,
        "/api/practice",
        {
            "attempt_id": attempt,
            "step": "scope",
            "answer": response["scope_options"][0]["id"],
        },
    )
    response = request_json(
        base,
        "/api/practice",
        {
            "attempt_id": attempt,
            "step": "reason",
            "answer": response["reason_options"][0]["id"],
        },
    )
    assert response["phase"] == "formal_intro"
    return request_json(base, "/api/continue", {"attempt_id": attempt})


def complete_attempt(base, server, participant="P-COMPLETE", locale="en"):
    materials = welcome(base, locale)
    created = start(base, participant, locale)
    attempt = created["attempt_id"]
    current = advance_practice(base, attempt, materials["common"])
    for _ in range(6):
        session = server.sessions[attempt]
        slot = session["plan"][session["index"]]
        current = request_json(
            base,
            "/api/q1",
            {
                "attempt_id": attempt,
                "answer": q1_state_to_public(slot["q1_state"]),
            },
        )
        current = request_json(
            base,
            "/api/scope",
            {"attempt_id": attempt, "answer": slot["correct_scope_id"]},
        )
        current = request_json(
            base,
            "/api/reason",
            {"attempt_id": attempt, "answer": slot["correct_reason_id"]},
        )
    assert current["phase"] == "attention_q1"
    current = request_json(
        base,
        "/api/attention",
        {
            "attempt_id": attempt,
            "step": "q1",
            "answer": "board-check",
        },
    )
    current = request_json(
        base,
        "/api/attention",
        {
            "attempt_id": attempt,
            "step": "reason",
            "answer": "AC1-R-B",
        },
    )
    assert current["phase"] == "reflection"
    options = materials["common"]["reflection"]["options"]
    request_json(
        base,
        "/api/reflection",
        {
            "attempt_id": attempt,
            "helpful": options["helpful"][0]["id"],
            "confusing": options["confusing"][0]["id"],
            "amount": options["amount"][0]["id"],
        },
    )
    request_json(base, "/api/complete", {"attempt_id": attempt})
    return request_json(
        base, f"/api/export?attempt_id={attempt}&format=json"
    )


def test_server_headers_selected_locale_projection_and_no_private_keys(live_server):
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
    assert bootstrap["fallback"] is None
    assert bootstrap["auto_detect"] is False
    assert bootstrap["minimum_width_px"] == 1280
    assert set(english) == {
        "selected_locale",
        "materials_version",
        "locale_bundle_version",
        "locale_bundle_hash",
        "common",
        "practice",
        "sequence_count",
    }
    assert english["selected_locale"] == "en"
    assert chinese["selected_locale"] == "zh-Hans"
    assert english["sequence_count"] == 12
    for projection in (bootstrap, english, chinese):
        text = json.dumps(projection, ensure_ascii=False)
        for forbidden in (
            "correct_reason_id",
            "correct_scope_id",
            "q1_state",
            "paper_state",
            "reason_class",
            "scope_gate_required",
            "decisive_positive",
            "derived_keys",
        ):
            assert forbidden not in text
        assert "F1-R-A" not in text and "F2-R-A" not in text
    assert "All products, buttons" in english["common"]["disclaimer"]
    assert "本页所有产品" in chinese["common"]["disclaimer"]
    assert output.getvalue() == ""


def test_success_only_allocation_balances_sequence_and_ab_within_locale(live_server):
    base, server = live_server
    allocations = []
    for index in range(24):
        created = start(base, f"ALLOC-{index}", "en")
        session = server.sessions[created["attempt_id"]]
        allocations.append(
            (
                session["sequence_id"],
                session["ab_variant"],
                session["allocation_block"],
                session["allocation_cell"],
            )
        )
        scene_ids = {row["scene_id"] for row in session["plan"]}
        assert len(scene_ids & {"F1", "F2"}) == 1
    assert Counter(row[0] for row in allocations) == {
        f"BB10-{index:02d}": 2 for index in range(1, 13)
    }
    assert Counter(row[1] for row in allocations) == {"F1": 12, "F2": 12}
    assert {row[2] for row in allocations} == {0}
    assert [row[3] for row in allocations] == list(range(24))
    zh = start(base, "ZH-FIRST", "zh-Hans")
    zh_session = server.sessions[zh["attempt_id"]]
    assert zh_session["sequence_id"] == "BB10-01"
    assert zh_session["ab_variant"] == "F1"
    assert zh_session["allocation_cell"] == 0


def test_complete_signed_v6_export_strict_scope_scoring_and_analysis(live_server):
    base, server = live_server
    data = complete_attempt(base, server)
    assert validate_export(data, TEST_KEY) is data
    assert data["schema_version"] == MATERIAL_SCHEMA_VERSION
    assert data["export_schema_version"] == EXPORT_SCHEMA_VERSION
    assert data["materials_version"] == MATERIALS_VERSION
    assert data["analysis_version"] == ANALYSIS_VERSION
    assert data["attention_check"]["pass"] is True
    assert all(trial["gaa_trial"] for trial in data["trials"])
    assert all(trial["strict_gaa_trial"] for trial in data["trials"])
    assert {
        trial["scene_id"]
        for trial in data["trials"]
        if trial["scope_gate_required"]
    } == {"F1", "F6", "F7"}
    text = json.dumps(data, ensure_ascii=False)
    for forbidden in (
        "correct_reason_id",
        "correct_scope_id",
        "reason_class",
        "paper_state",
        "expected",
    ):
        assert forbidden not in text
    summary = analyze([data])
    assert summary["primary_attention_pass"]["mean_gaa_rate"] == 1.0
    assert summary["primary_attention_pass"]["mean_strict_gaa_rate"] == 1.0
    assert summary["all_completers_sensitivity"]["n"] == 1
    assert v9_compat_trial(data["trials"][0]) == {
        "q1_correct": True,
        "q2_correct": True,
        "cca_correct": True,
    }
    assert summary["v9_compatibility_aliases"]["schema_reused"] is False
    assert "does not test benefit" in summary["claim_boundary"]


def test_wrong_scope_removes_strict_credit_only_on_frozen_scope_gate(live_server):
    base, server = live_server
    materials = welcome(base)
    created = start(base, "SCOPE-WRONG")
    attempt = created["attempt_id"]
    current = advance_practice(base, attempt, materials["common"])
    for _ in range(6):
        session = server.sessions[attempt]
        slot = session["plan"][session["index"]]
        current = request_json(
            base,
            "/api/q1",
            {
                "attempt_id": attempt,
                "answer": q1_state_to_public(slot["q1_state"]),
            },
        )
        wrong_scope = next(
            option_id
            for option_id in slot["scope_order_ids"]
            if option_id != slot["correct_scope_id"]
        )
        current = request_json(
            base,
            "/api/scope",
            {"attempt_id": attempt, "answer": wrong_scope},
        )
        current = request_json(
            base,
            "/api/reason",
            {"attempt_id": attempt, "answer": slot["correct_reason_id"]},
        )
    gated = [
        trial for trial in server.sessions[attempt]["trials"]
        if trial["scope_gate_required"]
    ]
    nongated = [
        trial for trial in server.sessions[attempt]["trials"]
        if not trial["scope_gate_required"]
    ]
    assert all(trial["gaa_trial"] for trial in gated + nongated)
    assert all(not trial["strict_gaa_trial"] for trial in gated)
    assert all(trial["strict_gaa_trial"] for trial in nongated)
    assert all(not trial["scope_choice_correct"] for trial in gated + nongated)


def test_partial_export_signature_tamper_wrong_key_and_v5_hardfail(live_server):
    base, server = live_server
    materials = welcome(base)
    created = start(base, "PARTIAL")
    attempt = created["attempt_id"]
    advance_practice(base, attempt, materials["common"])
    request_json(base, "/api/save-exit", {"attempt_id": attempt})
    partial = request_json(
        base, f"/api/export?attempt_id={attempt}&format=json"
    )
    assert partial["complete"] is False
    assert validate_export(partial, TEST_KEY)
    tampered = copy.deepcopy(partial)
    tampered["participant_code"] = "CHANGED"
    with pytest.raises(ExportError, match="signature"):
        validate_export(tampered, TEST_KEY)
    with pytest.raises(ExportError, match="wrong verification key"):
        validate_export(partial, b"another-key-that-is-long-enough!!")
    v5 = copy.deepcopy(partial)
    v5["export_schema_version"] = "microstudy-export-v5-scenario-bilingual-signed"
    v5 = sign_export(v5, TEST_KEY)
    with pytest.raises(ExportError, match="V5/V6"):
        validate_export(v5, TEST_KEY)


def test_request_security_idempotency_capacity_ttl_and_memory_only(live_server):
    base, server = live_server
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(
            urllib.request.Request(
                f"{base}/api/bootstrap", headers={"Host": "evil.example"}
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
        request_json(
            base,
            "/api/practice",
            {
                "attempt_id": attempt,
                "step": "q1",
                "answer": "board-use",
            },
        )
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
        "127.0.0.1", 0, key_path, session_ttl_seconds=0.08
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
            request_json(
                base,
                "/api/q1",
                {"attempt_id": attempt, "answer": "board-use"},
            )
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


def test_load_exports_rejects_duplicates_and_mixed_schema(live_server):
    base, server = live_server
    data = complete_attempt(base, server, "LOAD-1")
    first = RUNTIME / "one.json"
    second = RUNTIME / "two.json"
    first.write_text(json.dumps(data), encoding="utf-8")
    second.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ExportError, match="duplicate export"):
        load_exports([first, second], TEST_KEY)
    mixed = copy.deepcopy(data)
    mixed["export_schema_version"] = "microstudy-export-v5-scenario-bilingual-signed"
    mixed = sign_export(mixed, TEST_KEY)
    second.write_text(json.dumps(mixed), encoding="utf-8")
    with pytest.raises(ExportError, match="V5/V6"):
        load_exports([first, second], TEST_KEY)


def test_static_dom_aria_privacy_keyboard_and_desktop_contract():
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    js = (STATIC_DIR / "study.js").read_text(encoding="utf-8")
    css = (STATIC_DIR / "study.css").read_text(encoding="utf-8")
    assert 'lang="und"' in html
    assert "data-locale" in html and "disabled" in html
    assert "fiction-banner" in html and "fiction-notice" in css
    assert "board-grid" in css and "repeat(4" in css
    assert "background: #ffffff" in css
    assert "focus-visible" in css and "prefers-reduced-motion" in css
    assert "@media (max-width: 1279px)" in css
    assert "showModal()" in js and "role: \"status\"" in js
    assert "performance.now" not in js
    assert "localStorage" not in js and "sessionStorage" not in js
    assert "expected" not in html.lower()
    for forbidden in (
        "correct_reason_id",
        "correct_scope_id",
        "q1_state",
        "paper_state",
        "reason_class",
        "scope_gate_required",
    ):
        assert forbidden not in html


def _free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def test_real_chrome_edge_button_board_en_zh_zoom_keyboard_and_desktop_gate():
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

    def press(cdp, key, code, virtual_key):
        down = {
            "key": key,
            "code": code,
            "windowsVirtualKeyCode": virtual_key,
            "text": "\r" if key == "Enter" else (key if key == " " else ""),
        }
        cdp.call("Input.dispatchKeyEvent", {"type": "keyDown", **down})
        cdp.call(
            "Input.dispatchKeyEvent",
            {
                "type": "keyUp",
                "key": key,
                "code": code,
                "windowsVirtualKeyCode": virtual_key,
            },
        )

    def open_page(port, base, width, height, zoom):
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

    def choose_first(cdp, name, action, *, keyboard=False):
        cdp.wait(f'document.querySelector(\'input[name="{name}"]\')')
        if keyboard:
            cdp.eval(
                "new Promise(resolve => requestAnimationFrame("
                "() => requestAnimationFrame(resolve)))"
            )
            cdp.eval(f'document.querySelector(\'input[name="{name}"]\').focus()')
            cdp.wait(
                f'document.activeElement === document.querySelector(\'input[name="{name}"]\')'
            )
            for _ in range(3):
                press(cdp, " ", "Space", 32)
                time.sleep(0.15)
                if cdp.eval(
                    f'document.querySelector(\'input[name="{name}"]\').checked'
                ):
                    break
            assert cdp.eval(
                f'document.querySelector(\'input[name="{name}"]\').checked'
            )
            cdp.eval(f'document.querySelector(\'[data-action="{action}"]\').focus()')
            press(cdp, "Enter", "Enter", 13)
        else:
            cdp.eval(
                f'document.querySelector(\'input[name="{name}"]\').checked=true;'
                f'document.querySelector(\'[data-action="{action}"]\').click()'
            )

    cases = [("en", 1280, 800, 1), ("zh-Hans", 1440, 900, 2)]
    try:
        for browser_name, executable in browsers.items():
            with browser_process(browser_name, executable) as port:
                for case_index, (locale, width, height, zoom) in enumerate(cases):
                    with isolated_server(f"{browser_name}-{locale}") as (base, server):
                        cdp = open_page(port, base, width, height, zoom)
                        try:
                            cdp.wait(
                                "window.ButtonBoardTest && window.ButtonBoardTest.ready"
                            )
                            cdp.eval(
                                f'document.querySelector(\'[data-locale="{locale}"]\').focus()'
                            )
                            press(cdp, "Enter", "Enter", 13)
                            cdp.wait("document.querySelector('#participant-code')")
                            assert cdp.eval("document.documentElement.lang") == locale
                            cdp.eval(
                                "document.querySelector('#participant-code').value="
                                + json.dumps(f"B{case_index}{browser_name[0]}")
                            )
                            cdp.eval(
                                "document.querySelector('[data-action=\"start\"]').focus()"
                            )
                            press(cdp, "Enter", "Enter", 13)
                            cdp.wait(
                                "document.querySelector('[data-action=\"show-practice\"]')"
                            )
                            cdp.click("show-practice")
                            choose_first(cdp, "practice-q1", "practice-q1", keyboard=True)
                            choose_first(cdp, "practice-scope", "practice-scope")
                            choose_first(cdp, "practice-reason", "practice-reason")
                            cdp.wait(
                                "document.querySelector('[data-action=\"begin-formal\"]')"
                            )
                            cdp.click("begin-formal")
                            for trial_index in range(6):
                                cdp.wait(
                                    "document.querySelector('[data-action=\"formal-q1\"]')"
                                )
                                audit = cdp.eval(
                                    """(() => {
                                      const cells=[...document.querySelectorAll('.board-choice')];
                                      const rects=cells.map(n=>n.getBoundingClientRect());
                                      const html=document.querySelector('#stage').outerHTML;
                                      return {
                                        count:cells.length,
                                        widths:rects.map(r=>r.width),
                                        heights:rects.map(r=>r.height),
                                        overflow:document.documentElement.scrollWidth>
                                          document.documentElement.clientWidth,
                                        h1:document.querySelectorAll('#stage h1').length,
                                        private:new RegExp(
                                          'expected|correct_reason_id|correct_scope_id|q1_state|'
                                          +'paper_state|reason_class|scope_gate_required','i'
                                        ).test(html),
                                        aria:[...document.querySelectorAll('#stage [aria-label]')]
                                          .map(n=>n.getAttribute('aria-label')).join(' ')
                                      };
                                    })()"""
                                )
                                assert audit["count"] == 4
                                assert max(audit["widths"]) - min(audit["widths"]) <= 1
                                assert max(audit["heights"]) - min(audit["heights"]) <= 1
                                assert not audit["overflow"] and audit["h1"] == 1
                                assert not audit["private"]
                                choose_first(
                                    cdp,
                                    "formal-q1",
                                    "formal-q1",
                                    keyboard=trial_index == 0,
                                )
                                cdp.wait(
                                    "document.querySelector('.locked-summary[role=\"status\"]')"
                                )
                                choose_first(cdp, "formal-scope", "formal-scope")
                                choose_first(cdp, "formal-reason", "formal-reason")
                            cdp.wait(
                                "document.querySelector('[data-action=\"attention-q1\"]')"
                            )
                            cdp.eval(
                                "document.querySelector('input[name=\"attention-q1\"][value=\"board-check\"]').checked=true;"
                                "document.querySelector('[data-action=\"attention-q1\"]').click()"
                            )
                            cdp.wait(
                                "document.querySelector('[data-action=\"attention-reason\"]')"
                            )
                            choose_first(
                                cdp, "attention-reason", "attention-reason"
                            )
                            cdp.wait(
                                "document.querySelector('[data-action=\"reflection\"]')"
                            )
                            cdp.click("reflection")
                            cdp.wait(
                                "document.querySelector('[data-action=\"download-json\"]')"
                            )
                            assert len(server.sessions) == 1
                            attempt = next(iter(server.sessions))
                            assert server.sessions[attempt]["phase"] == "export_ready"
                        finally:
                            cdp.close()
                with isolated_server(f"{browser_name}-desktop") as (base, _):
                    cdp = open_page(port, base, 1279, 800, 1)
                    try:
                        cdp.wait("window.ButtonBoardTest")
                        assert cdp.eval(
                            "getComputedStyle(document.querySelector('#desktop-blocker')).display"
                            " !== 'none' && getComputedStyle(document.querySelector('#app')).display"
                            " === 'none'"
                        )
                    finally:
                        cdp.close()
    finally:
        shutil.rmtree(RUNTIME, ignore_errors=True)
