"""Public-deployment tests for the V11 stepwise study.

These exercise the deployment-only code paths added on top of the unchanged
study logic: the public server mode, durable persistence of signed exports,
and the owner-only admin download endpoint. Study logic, expected answers,
routing, and scoring are untouched (see the logic-fingerprint test).
"""

import contextlib
import socket
import threading
import urllib.error
import urllib.request

import pytest

from cognitive_console.button_board_stepwise.server import create_server
from cognitive_console.button_board_stepwise.storage import (
    InMemoryExportStore,
    create_store,
)
from test_button_board_stepwise_web import (
    CLIENTS,
    PRIVATE_KEYS,
    complete_attempt,
    nested_keys,
    request_json,
)

KEY = b"deploy-test-verification-key-32bytes!!"
ADMIN_TOKEN = "admin-secret-token"


def _free_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


@contextlib.contextmanager
def public_server(storage=None, admin_token=ADMIN_TOKEN):
    port = _free_port()
    origin = f"http://127.0.0.1:{port}"
    server = create_server(
        "127.0.0.1",
        port,
        public_origin=origin,
        verification_key=KEY,
        storage=storage,
        admin_token=admin_token,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        request_json(origin, "/api/bootstrap")
        yield origin, server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=10)
        assert not thread.is_alive()
        CLIENTS.pop(origin, None)


def _raw_get(base, path, headers=None):
    request = urllib.request.Request(f"{base}{path}", headers=headers or {})
    with urllib.request.urlopen(request) as response:
        return response.status, response.read()


# --- unit: storage -----------------------------------------------------------


def test_inmemory_store_is_idempotent_by_attempt_id():
    store = InMemoryExportStore()
    store.save_attempt(
        "a1", run_id="r", completion_status="partial", complete=False,
        signed_export={"attempt_id": "a1", "n": 1},
    )
    store.save_attempt(
        "a1", run_id="r", completion_status="complete", complete=True,
        signed_export={"attempt_id": "a1", "n": 2},
    )
    rows = store.all_attempts()
    assert len(rows) == 1
    assert rows[0]["complete"] is True
    assert rows[0]["completion_status"] == "complete"
    assert rows[0]["signed_export"]["n"] == 2


def test_store_returns_copies_not_references():
    store = InMemoryExportStore()
    payload = {"attempt_id": "a1", "trials": [{"x": 1}]}
    store.save_attempt(
        "a1", run_id="r", completion_status="complete", complete=True,
        signed_export=payload,
    )
    payload["trials"][0]["x"] = 999
    assert store.all_attempts()[0]["signed_export"]["trials"][0]["x"] == 1


def test_create_store_none_is_volatile():
    assert create_store(None) is None
    assert create_store("") is None


# --- unit: create_server validation -----------------------------------------


def test_public_mode_requires_key_and_admin_and_valid_origin():
    with pytest.raises(ValueError):
        create_server(
            "127.0.0.1", 0, public_origin="not-a-url",
            verification_key=KEY, admin_token=ADMIN_TOKEN,
        )
    with pytest.raises(ValueError):
        create_server(
            "127.0.0.1", 0, public_origin="https://x.test",
            verification_key=b"short", admin_token=ADMIN_TOKEN,
        )
    with pytest.raises(ValueError):
        create_server(
            "127.0.0.1", 0, public_origin="https://x.test",
            verification_key=KEY, admin_token="",
        )


def test_loopback_mode_still_refuses_nonloopback_bind():
    with pytest.raises(ValueError):
        create_server("0.0.0.0", 0)


def test_public_origin_trailing_slash_is_normalized():
    server = create_server(
        "127.0.0.1", 0, public_origin="https://study.test/",
        verification_key=KEY, admin_token=ADMIN_TOKEN,
    )
    try:
        assert server.origin == "https://study.test"
        assert server.allowed_host == "study.test"
    finally:
        server.server_close()


# --- integration: public flow, persistence, admin ----------------------------


def test_healthz_is_open_without_origin_or_token():
    with public_server() as (base, _):
        status, body = _raw_get(base, "/healthz")
        assert status == 200
        assert body.strip() == b"ok"


def test_completed_attempt_is_persisted_and_downloadable_by_admin():
    store = InMemoryExportStore()
    with public_server(storage=store) as (base, server):
        export = complete_attempt(base, server)
        attempt_id = export["attempt_id"]

    rows = store.all_attempts()
    assert len(rows) == 1
    assert rows[0]["attempt_id"] == attempt_id
    assert rows[0]["complete"] is True
    persisted = rows[0]["signed_export"]
    assert persisted["verification"]["algorithm"] == "HMAC-SHA256"
    # persisted export must equal what the participant received
    assert persisted["verification"]["signature"] == export["verification"]["signature"]
    # and must never carry private scoring material
    assert PRIVATE_KEYS.isdisjoint(nested_keys(persisted))


def test_admin_export_json_returns_all_attempts():
    store = InMemoryExportStore()
    with public_server(storage=store) as (base, server):
        complete_attempt(base, server)
        status, body = _raw_get(
            base, "/admin/export?format=json", {"X-Admin-Token": ADMIN_TOKEN}
        )
    assert status == 200
    import json

    payload = json.loads(body)
    assert payload["count"] == 1
    assert len(payload["attempts"]) == 1
    assert PRIVATE_KEYS.isdisjoint(nested_keys(payload))


def test_admin_export_csv_has_header_and_rows():
    store = InMemoryExportStore()
    with public_server(storage=store) as (base, server):
        complete_attempt(base, server)
        status, body = _raw_get(
            base, "/admin/export?format=csv", {"X-Admin-Token": ADMIN_TOKEN}
        )
    assert status == 200
    text = body.decode("utf-8-sig")
    lines = [line for line in text.split("\r\n") if line]
    assert lines[0].startswith("schema_version")
    # six planned trials => six data rows for one attempt
    assert len(lines) == 7


def test_admin_export_rejects_missing_or_wrong_token():
    store = InMemoryExportStore()
    with public_server(storage=store) as (base, _):
        for headers in ({}, {"X-Admin-Token": "wrong"}):
            with pytest.raises(urllib.error.HTTPError) as exc:
                _raw_get(base, "/admin/export?format=json", headers)
            assert exc.value.code == 403


def test_admin_export_409_when_persistence_disabled():
    with public_server(storage=None) as (base, _):
        with pytest.raises(urllib.error.HTTPError) as exc:
            _raw_get(base, "/admin/export?format=json", {"X-Admin-Token": ADMIN_TOKEN})
        assert exc.value.code == 409
