"""Loopback-only, volatile V9 scenario micro-study server."""

from __future__ import annotations

import argparse
import csv
import hashlib
import hmac
import io
import ipaddress
import json
import mimetypes
import os
import re
import secrets
import stat
import subprocess
import threading
import time
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlsplit

from cognitive_console.microstudy_materials import EXPORT_SCHEMA_VERSION

from .materials import (
    locale_bundle_metadata,
    material_hashes,
    planned_trials,
    validated_sources,
)

STATIC_DIR = Path(__file__).with_name("static")
DEFAULT_KEY_FILE = Path(".runtime") / "microstudy-v9-verification.key"
CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
    "connect-src 'self'; font-src 'none'; media-src 'none'; object-src 'none'; "
    "base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
)
PARTICIPANT_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def canonical_bytes(data: dict[str, Any]) -> bytes:
    unsigned = {key: value for key, value in data.items() if key != "verification"}
    return json.dumps(
        unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def request_bytes(data: dict[str, Any]) -> bytes:
    return json.dumps(
        data, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def sign_export(data: dict[str, Any], key: bytes) -> dict[str, Any]:
    signed = dict(data)
    signed["verification"] = {
        "algorithm": "HMAC-SHA256",
        "key_id": hashlib.sha256(key).hexdigest()[:16],
        "signature": hmac.new(key, canonical_bytes(data), hashlib.sha256).hexdigest(),
    }
    return signed


def load_or_create_key(path: Path) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.is_symlink() or not path.is_file():
            raise ValueError("verification key path must be a regular file")
        try:
            _restrict_key_permissions(path)
            key = path.read_bytes()
            if len(key) < 32:
                raise ValueError(
                    "verification key file must contain at least 32 bytes"
                )
        except BaseException:
            _remove_failed_key(path)
            raise
        return key
    key = secrets.token_bytes(32)
    created = False
    try:
        with path.open("xb") as handle:
            created = True
            handle.write(key)
            handle.flush()
            os.fsync(handle.fileno())
        _restrict_key_permissions(path)
    except BaseException:
        if created:
            _remove_failed_key(path)
        raise
    return key


def _remove_failed_key(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    except OSError as cleanup_error:
        raise RuntimeError(
            "verification key permission setup failed and cleanup failed"
        ) from cleanup_error


def _restrict_key_permissions(path: Path) -> None:
    if _is_windows():
        _restrict_windows_key_permissions(path)
    else:
        _restrict_posix_key_permissions(path)


def _is_windows() -> bool:
    return os.name == "nt"


def _restrict_posix_key_permissions(path: Path) -> None:
    os.chmod(path, 0o600)
    if _key_mode(path) != 0o600:
        raise PermissionError("verification key mode is not 0600")


def _key_mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


def _restrict_windows_key_permissions(path: Path) -> None:
    identity = subprocess.run(
        ["whoami.exe", "/user", "/fo", "csv", "/nh"],
        capture_output=True,
        text=True,
        check=False,
    )
    if identity.returncode:
        raise PermissionError("could not identify the current Windows user")
    try:
        _, sid = next(csv.reader([identity.stdout.strip()]))
    except (StopIteration, ValueError) as exc:
        raise PermissionError("could not parse the current Windows user SID") from exc
    for arguments in (
        [str(path), "/reset"],
        [str(path), "/setowner", f"*{sid}"],
        [str(path), "/inheritance:r", "/grant:r", f"*{sid}:(F)"],
    ):
        completed = subprocess.run(
            ["icacls.exe", *arguments],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode:
            detail = (completed.stderr or completed.stdout).strip()
            raise PermissionError(
                "could not restrict verification key to the current Windows user"
                + (f": {detail}" if detail else "")
            )

    script = r"""
$ErrorActionPreference = 'Stop'
$path = [Environment]::GetEnvironmentVariable(
    'COGNITIVE_CONSOLE_VERIFICATION_KEY_PATH', 'Process'
)
$sid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
$sections = (
    [System.Security.AccessControl.AccessControlSections]::Access -bor
    [System.Security.AccessControl.AccessControlSections]::Owner
)
$verified = [System.Security.AccessControl.FileSecurity]::new($path, $sections)
$rules = @($verified.GetAccessRules(
    $true,
    $true,
    [System.Security.Principal.SecurityIdentifier]
))
if ($verified.GetOwner(
        [System.Security.Principal.SecurityIdentifier]
    ).Value -ne $sid.Value) {
    throw 'verification key owner mismatch'
}
if ($rules.Count -ne 1) {
    throw 'verification key has additional access rules'
}
$verifiedRule = $rules[0]
if ($verifiedRule.IsInherited) {
    throw 'verification key still inherits permissions'
}
if ($verifiedRule.IdentityReference.Value -ne $sid.Value) {
    throw 'verification key access rule is not current-user-only'
}
if ($verifiedRule.AccessControlType -ne
        [System.Security.AccessControl.AccessControlType]::Allow) {
    throw 'verification key access rule is not allow'
}
if (($verifiedRule.FileSystemRights -band
        [System.Security.AccessControl.FileSystemRights]::FullControl) -ne
        [System.Security.AccessControl.FileSystemRights]::FullControl) {
    throw 'verification key current-user rule is not full control'
}
"""
    environment = os.environ.copy()
    environment["COGNITIVE_CONSOLE_VERIFICATION_KEY_PATH"] = str(path.resolve())
    completed = subprocess.run(
        [
            "powershell.exe",
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            script,
        ],
        capture_output=True,
        text=True,
        env=environment,
        check=False,
    )
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        raise PermissionError(
            "could not verify current-user-only Windows key permissions"
            + (f": {detail}" if detail else "")
        )


def common_materials(locale: str) -> dict[str, Any]:
    materials, sequences = validated_sources()
    if locale not in materials["locale_contract"]["supported"]:
        raise ValueError("unsupported locale")
    bundle = json.loads(json.dumps(materials["locales"][locale]))
    bundle.pop("tickets")
    bundle.pop("contract_headings")
    return {
        "ui_language": locale,
        "materials_version": materials["materials_version"],
        **locale_bundle_metadata(locale),
        "common": bundle,
        "sequence_codes": [row["code"] for row in sequences["sequences"]],
    }


def _empty_trial(slot: dict[str, Any], version: str) -> dict[str, Any]:
    return {
        "slot_index": slot["slot_index"],
        "ticket_code": slot["ticket_code"],
        "position": slot["position"],
        "planned": True,
        "presented": False,
        "q1_submitted": False,
        "q2_submitted": False,
        "complete": False,
        "submitted": False,
        "q1": None,
        "q2": None,
        "q1_correct": None,
        "q2_correct": None,
        "cca_correct": None,
        "rt_q1_ms": None,
        "rt_q2_ms": None,
        "rt_total_ms": None,
        "hidden_ms": None,
        "q1_missing": True,
        "q2_missing": True,
        "q1_correct_missing": True,
        "q2_correct_missing": True,
        "cca_correct_missing": True,
        "rt_q1_missing": True,
        "rt_q2_missing": True,
        "rt_total_missing": True,
        "hidden_ms_missing": True,
        "materials_version": version,
    }


class StudyServer(ThreadingHTTPServer):
    def __init__(
        self,
        address: tuple[str, int],
        key: bytes,
        *,
        max_sessions: int = 100,
        session_ttl_seconds: float = 7200,
    ):
        super().__init__(address, StudyHandler)
        self.verification_key = key
        self.sessions: dict[str, dict[str, Any]] = {}
        self.session_lock = threading.RLock()
        self.max_sessions = max_sessions
        self.session_ttl_seconds = session_ttl_seconds
        self.clock = time.monotonic
        self.run_id = str(uuid.uuid4())
        self.attempt_serial = 0
        self.csrf_token = secrets.token_urlsafe(32)
        self.start_requests: dict[str, tuple[bytes, dict[str, Any]]] = {}

    @property
    def origin(self) -> str:
        return f"http://{self.server_address[0]}:{self.server_port}"

    @property
    def allowed_host(self) -> str:
        return f"{self.server_address[0]}:{self.server_port}"

    def cleanup_expired(self) -> None:
        now = self.clock()
        with self.session_lock:
            expired = [
                attempt_id
                for attempt_id, session in self.sessions.items()
                if now - session["last_seen"] >= self.session_ttl_seconds
            ]
            for attempt_id in expired:
                del self.sessions[attempt_id]
            expired_set = set(expired)
            self.start_requests = {
                request_id: cached
                for request_id, cached in self.start_requests.items()
                if cached[1].get("attempt_id") not in expired_set
            }


class StudyHandler(BaseHTTPRequestHandler):
    server: StudyServer
    server_version = "MicrostudyV9Local"
    sys_version = ""

    def log_message(self, format: str, *args: object) -> None:
        return

    def _headers(self, status: int, content_type: str, length: int) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("Content-Security-Policy", CSP)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.end_headers()

    def _send(self, body: bytes, content_type: str, status: int = 200) -> None:
        self._headers(status, content_type, len(body))
        self.wfile.write(body)

    def _json(self, value: Any, status: int = 200) -> None:
        self._send(
            json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
            "application/json; charset=utf-8",
            status,
        )

    def _error(self, status: int, message: str) -> None:
        self._json({"error": message}, status)

    def _body(self) -> dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 16_384:
                raise ValueError("invalid request body")
            value = json.loads(self.rfile.read(length))
            if not isinstance(value, dict):
                raise ValueError("JSON object required")
            return value
        except (ValueError, json.JSONDecodeError):
            raise ValueError("invalid JSON request") from None

    def _request_origin_ok(self, *, post: bool) -> bool:
        if self.headers.get("Host") != self.server.allowed_host:
            return False
        origin = self.headers.get("Origin")
        if origin is not None and origin != self.server.origin:
            return False
        if self.headers.get("Sec-Fetch-Site") == "cross-site":
            return False
        if post:
            return (
                self.headers.get_content_type() == "application/json"
                and origin == self.server.origin
                and hmac.compare_digest(
                    self.headers.get("X-CSRF-Token", ""),
                    self.server.csrf_token,
                )
            )
        return True

    def _request_id(self, body: dict[str, Any]) -> str:
        request_id = body.get("request_id")
        if (
            not isinstance(request_id, str)
            or not re.fullmatch(r"[A-Za-z0-9_-]{16,128}", request_id)
        ):
            raise ValueError("invalid request_id")
        return request_id

    def _session(self, body: dict[str, Any]) -> dict[str, Any]:
        attempt_id = body.get("attempt_id")
        if not isinstance(attempt_id, str) or attempt_id not in self.server.sessions:
            raise ValueError("unknown attempt")
        session = self.server.sessions[attempt_id]
        capability = self.headers.get("X-Study-Capability", "")
        if not hmac.compare_digest(capability, session["capability"]):
            raise ValueError("invalid session capability")
        return session

    def _ticket_payload(self, session: dict[str, Any]) -> dict[str, Any]:
        index = session["index"]
        slot = session["plan"][index]
        materials, _ = validated_sources()
        locale_bundle = materials["locales"][session["ui_language"]]
        ticket = next(
            row
            for row in locale_bundle["tickets"]
            if row["ticket_code"] == slot["ticket_code"]
        )
        common = session["common"]
        facts = ticket["facts"]
        if slot["condition"] == "C":
            sizes = (1, 2, 2, 1)
            groups = []
            cursor = 0
            for heading, size in zip(locale_bundle["contract_headings"], sizes):
                groups.append(
                    {"heading": heading, "facts": facts[cursor:cursor + size]}
                )
                cursor += size
            card = {"aria_label": ticket["title"], "groups": groups}
        else:
            card = {
                "aria_label": ticket["title"],
                "rows": [
                    {
                        "label": common["flat_labels"][display_position],
                        "body": facts[fact_position],
                    }
                    for display_position, fact_position in enumerate(
                        ticket["flat_order"]
                    )
                ],
            }
        trial = session["trials"][index]
        trial["presented"] = True
        session["phase"] = "q1"
        session["phase_started"] = time.monotonic()
        return {
            "phase": "q1",
            "trial_index": index,
            "slot_index": slot["slot_index"],
            "position": slot["position"],
            "ticket_code": slot["ticket_code"],
            "product": {
                "title": ticket["title"],
                "context": ticket["context"],
                "knob": ticket["knob"],
                "knob_note": common["knob_unavailable"],
            },
            "source_badge": ticket["source_badge"],
            "outputs": [
                {
                    "badge": common["badges"]["illustrative_output"],
                    "text": text,
                }
                for text in ticket["outputs"]
            ],
            "source_details_label": common["source_details"],
            "source_details": ticket["source_details"],
            "card": card,
            "q1": common["q1"],
        }

    def do_GET(self) -> None:
        self.server.cleanup_expired()
        if not self._request_origin_ok(post=False):
            self._error(403, "request origin rejected")
            return
        parsed = urlsplit(self.path)
        path = unquote(parsed.path)
        if path == "/api/bootstrap":
            materials, _ = validated_sources()
            self._json(
                {
                    "csrf_token": self.server.csrf_token,
                    "languages": [
                        {
                            "id": locale,
                            "label": materials["locales"][locale]["language_name"],
                        }
                        for locale in materials["locale_contract"]["supported"]
                    ],
                    "fallback": materials["locale_contract"]["fallback"],
                    "auto_detect": materials["locale_contract"]["auto_detect"],
                    "minimum_width_px": materials["nonlocalized"]["render_contract"][
                        "desktop_minimum_width_px"
                    ],
                }
            )
            return
        if path == "/api/welcome":
            query = parse_qs(parsed.query, keep_blank_values=True)
            if set(query) != {"ui_language"} or len(query["ui_language"]) != 1:
                self._error(400, "exact ui_language is required")
                return
            try:
                self._json(common_materials(query["ui_language"][0]))
            except ValueError as exc:
                self._error(400, str(exc))
            return
        if path == "/api/export":
            query = parse_qs(parsed.query)
            if set(query) != {"attempt_id", "format"}:
                self._error(400, "exact export query is required")
                return
            attempt_id = query["attempt_id"][0]
            output_format = query["format"][0]
            with self.server.session_lock:
                session = self.server.sessions.get(attempt_id)
                capability = self.headers.get("X-Study-Capability", "")
                if (
                    session is None
                    or session["phase"] != "export_ready"
                    or not hmac.compare_digest(capability, session["capability"])
                ):
                    self._error(409, "export is not available")
                    return
                if output_format not in {"json", "csv"}:
                    self._error(400, "unsupported export format")
                    return
                export = session["signed_export"]
            if output_format == "json":
                self._send(
                    (
                        json.dumps(export, ensure_ascii=False, indent=2) + "\n"
                    ).encode("utf-8"),
                    "application/json; charset=utf-8",
                )
            else:
                self._send(
                    b"\xef\xbb\xbf" + self._csv(export).encode("utf-8"),
                    "text/csv; charset=utf-8",
                )
            with session["lock"]:
                session["last_seen"] = self.server.clock()
            return
        relative = "index.html" if path in {"", "/"} else path.lstrip("/")
        candidate = (STATIC_DIR / relative).resolve()
        try:
            candidate.relative_to(STATIC_DIR.resolve())
        except ValueError:
            self._error(404, "not found")
            return
        if not candidate.is_file():
            self._error(404, "not found")
            return
        mime = (
            "application/javascript"
            if candidate.suffix in {".js", ".mjs"}
            else mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        )
        if mime.startswith("text/") or mime == "application/javascript":
            mime += "; charset=utf-8"
        self._send(candidate.read_bytes(), mime)

    def do_POST(self) -> None:
        self.server.cleanup_expired()
        if not self._request_origin_ok(post=True):
            self._error(403, "request origin rejected")
            return
        path = urlsplit(self.path).path
        try:
            body = self._body()
            handlers = {
                "/api/start": self._start,
                "/api/practice": self._practice,
                "/api/q1": self._q1,
                "/api/q2": self._q2,
                "/api/continue": self._continue,
                "/api/complete": self._complete,
                "/api/save-exit": self._save_exit,
            }
            handler = handlers.get(path)
            if handler is None:
                self._error(404, "not found")
                return
            request_id = self._request_id(body)
            if path == "/api/start":
                with self.server.session_lock:
                    cached = self.server.start_requests.get(request_id)
                    if cached is not None:
                        if cached[0] != request_bytes(body):
                            raise ValueError("request_id reuse with different payload")
                        self._json(cached[1])
                        return
                    result = handler(body)
                    self.server.start_requests[request_id] = (
                        request_bytes(body),
                        result,
                    )
            else:
                with self.server.session_lock:
                    session = self._session(body)
                with session["lock"]:
                    cached = session["requests"].get((path, request_id))
                    if cached is not None:
                        if cached[0] != request_bytes(body):
                            raise ValueError("request_id reuse with different payload")
                        session["last_seen"] = self.server.clock()
                        self._json(cached[1])
                        return
                    result = handler(body, session=session)
                    session["requests"][(path, request_id)] = (
                        request_bytes(body),
                        result,
                    )
                    session["last_seen"] = self.server.clock()
            self._json(result)
        except ValueError as exc:
            self._error(409, str(exc))

    def _start(self, body: dict[str, Any]) -> dict[str, Any]:
        if set(body) != {
            "participant_code", "sequence", "ui_language", "request_id"
        }:
            raise ValueError("invalid start fields")
        participant = body["participant_code"]
        sequence = body["sequence"]
        ui_language = body["ui_language"]
        if not isinstance(participant, str) or not PARTICIPANT_RE.fullmatch(participant):
            raise ValueError("invalid participant code")
        if not isinstance(sequence, str):
            raise ValueError("invalid sequence")
        plan = planned_trials(sequence)
        materials, sequences = validated_sources()
        if (
            not isinstance(ui_language, str)
            or ui_language not in materials["locale_contract"]["supported"]
        ):
            raise ValueError("invalid ui_language")
        if len(self.server.sessions) >= self.server.max_sessions:
            raise ValueError("session capacity reached")
        attempt_id = str(uuid.uuid4())
        capability = secrets.token_urlsafe(32)
        self.server.attempt_serial += 1
        locale_meta = locale_bundle_metadata(ui_language)
        common = json.loads(json.dumps(materials["locales"][ui_language]))
        common.pop("tickets")
        common.pop("contract_headings")
        self.server.sessions[attempt_id] = {
            "attempt_id": attempt_id,
            "participant_code": participant,
            "run_id": self.server.run_id,
            "attempt_serial": self.server.attempt_serial,
            "capability": capability,
            "lock": threading.RLock(),
            "requests": {},
            "sequence": sequence,
            "plan": plan,
            "ui_language": ui_language,
            **locale_meta,
            "common": common,
            "trials": [
                _empty_trial(slot, materials["materials_version"]) for slot in plan
            ],
            "phase": "practice_q1",
            "index": 0,
            "started": time.monotonic(),
            "phase_started": time.monotonic(),
            "practice_q1": False,
            "practice_q2": False,
            "material_schema_version": materials["schema_version"],
            "sequence_schema_version": sequences["schema_version"],
            "last_seen": self.server.clock(),
        }
        return {
            "attempt_id": attempt_id,
            "phase": "practice_q1",
            "capability": capability,
            "run_id": self.server.run_id,
            "attempt_serial": self.server.attempt_serial,
            "ui_language": ui_language,
        }

    def _practice(
        self, body: dict[str, Any], *, session: dict[str, Any]
    ) -> dict[str, Any]:
        if set(body) != {"attempt_id", "step", "answer", "request_id"}:
            raise ValueError("invalid practice fields")
        practice = session["common"]["practice"]
        if body["step"] == "q1" and session["phase"] == "practice_q1":
            if body["answer"] not in {
                row["id"] for row in session["common"]["q1"]["options"]
            }:
                raise ValueError("invalid practice Q1")
            session["practice_q1"] = True
            session["phase"] = "practice_q2"
            return {"phase": "practice_q2"}
        if body["step"] == "q2" and session["phase"] == "practice_q2":
            if body["answer"] not in {
                row["id"] for row in practice["q2_options"]
            }:
                raise ValueError("invalid practice Q2")
            session["practice_q2"] = True
            payload = self._ticket_payload(session)
            payload["feedback"] = practice["feedback"]
            return payload
        raise ValueError("invalid practice transition")

    def _q1(self, body: dict[str, Any], *, session: dict[str, Any]) -> dict[str, Any]:
        if set(body) != {"attempt_id", "answer", "request_id"}:
            raise ValueError("invalid Q1 fields")
        if session["phase"] != "q1":
            raise ValueError("Q1 is not available")
        answer = body["answer"]
        if answer not in {row["id"] for row in session["common"]["q1"]["options"]}:
            raise ValueError("invalid Q1 answer")
        index = session["index"]
        trial = session["trials"][index]
        slot = session["plan"][index]
        trial["q1"] = answer
        trial["q1_submitted"] = True
        trial["q1_correct"] = answer == slot["q1_key"]
        trial["rt_q1_ms"] = max(
            0, round((time.monotonic() - session["phase_started"]) * 1000)
        )
        for field in ("q1_missing", "q1_correct_missing", "rt_q1_missing"):
            trial[field] = False
        session["phase"] = "q2"
        session["phase_started"] = time.monotonic()
        return {"phase": "q2", "q2": session["common"]["q2"]}

    def _q2(self, body: dict[str, Any], *, session: dict[str, Any]) -> dict[str, Any]:
        if set(body) != {"attempt_id", "answer", "hidden_ms", "request_id"}:
            raise ValueError("invalid Q2 fields")
        if session["phase"] != "q2":
            raise ValueError("Q2 is not available")
        hidden_ms = body["hidden_ms"]
        if type(hidden_ms) is not int or hidden_ms < 0:
            raise ValueError("invalid hidden duration")
        answer = body["answer"]
        if answer not in {row["id"] for row in session["common"]["q2"]["options"]}:
            raise ValueError("invalid Q2 answer")
        index = session["index"]
        trial = session["trials"][index]
        slot = session["plan"][index]
        trial.update(
            {
                "q2": answer,
                "q2_submitted": True,
                "complete": True,
                "submitted": True,
                "q2_correct": answer == slot["q2_key"],
                "cca_correct": trial["q1_correct"] and answer == slot["q2_key"],
                "rt_q2_ms": max(
                    0,
                    round((time.monotonic() - session["phase_started"]) * 1000),
                ),
                "hidden_ms": hidden_ms,
            }
        )
        trial["rt_total_ms"] = trial["rt_q1_ms"] + trial["rt_q2_ms"]
        for field in (
            "q2_missing", "q2_correct_missing", "cca_correct_missing",
            "rt_q2_missing", "rt_total_missing", "hidden_ms_missing",
        ):
            trial[field] = False
        session["phase"] = "preview"
        return {"phase": "preview"}

    def _continue(
        self, body: dict[str, Any], *, session: dict[str, Any]
    ) -> dict[str, Any]:
        if set(body) != {"attempt_id", "request_id"}:
            raise ValueError("invalid continue fields")
        if session["phase"] != "preview":
            raise ValueError("preview continuation is not available")
        session["index"] += 1
        if session["index"] == 6:
            session["phase"] = "ready_complete"
            return {"phase": "ready_complete"}
        return self._ticket_payload(session)

    def _complete(
        self, body: dict[str, Any], *, session: dict[str, Any]
    ) -> dict[str, Any]:
        if set(body) != {"attempt_id", "request_id"}:
            raise ValueError("invalid complete fields")
        if session["phase"] != "ready_complete" or session["index"] != 6:
            raise ValueError("attempt cannot be completed")
        export = self._canonical_export(session, complete=True)
        session["signed_export"] = sign_export(export, self.server.verification_key)
        session["phase"] = "export_ready"
        return {
            "phase": "export_ready",
            "attempt_id": session["attempt_id"],
            "complete": True,
        }

    def _save_exit(
        self, body: dict[str, Any], *, session: dict[str, Any]
    ) -> dict[str, Any]:
        if set(body) != {"attempt_id", "request_id"}:
            raise ValueError("invalid save-exit fields")
        if session["phase"] not in {"q1", "q2", "preview", "ready_complete"}:
            raise ValueError("save and exit is available only during formal tickets")
        export = self._canonical_export(session, complete=False)
        session["signed_export"] = sign_export(export, self.server.verification_key)
        session["phase"] = "export_ready"
        return {
            "phase": "export_ready",
            "attempt_id": session["attempt_id"],
            "complete": False,
        }

    def _canonical_export(
        self, session: dict[str, Any], *, complete: bool
    ) -> dict[str, Any]:
        return {
            "export_schema_version": EXPORT_SCHEMA_VERSION,
            "material_schema_version": session["material_schema_version"],
            "sequence_schema_version": session["sequence_schema_version"],
            "material_hashes": material_hashes(),
            "attempt_id": session["attempt_id"],
            "run_id": session["run_id"],
            "attempt_serial": session["attempt_serial"],
            "participant_code": session["participant_code"],
            "sequence": session["sequence"],
            "ui_language": session["ui_language"],
            "locale_bundle_version": session["locale_bundle_version"],
            "locale_bundle_hash": session["locale_bundle_hash"],
            "completion_status": "complete" if complete else "partial",
            "complete": complete,
            "practice_presented": True,
            "practice_q1_submitted": session["practice_q1"],
            "practice_q2_submitted": session["practice_q2"],
            "practice_complete": session["practice_q1"] and session["practice_q2"],
            "mechanical_exclusion": False,
            "mechanical_exclusion_reason": "none",
            "trials": json.loads(json.dumps(session["trials"])),
        }

    @staticmethod
    def _csv(export: dict[str, Any]) -> str:
        def safe(value: Any) -> str:
            if value is None:
                return ""
            text = (
                json.dumps(value, ensure_ascii=False, separators=(",", ":"))
                if isinstance(value, (dict, list))
                else str(value)
            )
            return "'" + text if text.startswith(("=", "+", "-", "@")) else text

        session_fields = [
            key for key in export if key not in {"trials", "verification"}
        ]
        trial_fields = list(export["trials"][0])
        fields = session_fields + [
            "verification_algorithm", "verification_key_id",
            "verification_signature",
        ] + trial_fields
        output = io.StringIO(newline="")
        writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\r\n")
        writer.writeheader()
        for trial in export["trials"]:
            row = {
                key: safe(value)
                for key, value in export.items()
                if key not in {"trials", "verification"}
            }
            row.update(
                {
                    "verification_algorithm": export["verification"]["algorithm"],
                    "verification_key_id": export["verification"]["key_id"],
                    "verification_signature": export["verification"]["signature"],
                }
            )
            row.update({key: safe(value) for key, value in trial.items()})
            writer.writerow(row)
        return output.getvalue()


def create_server(
    host: str = "127.0.0.1",
    port: int = 8877,
    verification_key_file: Path | None = None,
    *,
    max_sessions: int = 100,
    session_ttl_seconds: float = 7200,
) -> StudyServer:
    try:
        address = ipaddress.ip_address(host)
    except ValueError as exc:
        raise ValueError("host must be a loopback IP address") from exc
    if not address.is_loopback:
        raise ValueError("refusing non-loopback host")
    key = load_or_create_key(verification_key_file or DEFAULT_KEY_FILE)
    if max_sessions < 1 or session_ttl_seconds <= 0:
        raise ValueError("session limits must be positive")
    return StudyServer(
        (host, port),
        key,
        max_sessions=max_sessions,
        session_ttl_seconds=session_ttl_seconds,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the V9 owner-local scenario preview."
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8877)
    parser.add_argument(
        "--verification-key-file", type=Path, default=DEFAULT_KEY_FILE
    )
    parser.add_argument("--open", action="store_true", dest="open_browser")
    parser.add_argument("--max-sessions", type=int, default=100)
    parser.add_argument("--session-ttl-seconds", type=float, default=7200)
    args = parser.parse_args(argv)
    server = create_server(
        args.host,
        args.port,
        args.verification_key_file,
        max_sessions=args.max_sessions,
        session_ttl_seconds=args.session_ttl_seconds,
    )
    url = f"http://{args.host}:{server.server_port}/"
    print(f"Local V9 study preview: {url}")
    print(f"Verification key: {args.verification_key_file}")
    if args.open_browser:
        threading.Timer(0.2, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
