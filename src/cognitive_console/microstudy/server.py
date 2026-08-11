"""Loopback-only, memory-only micro-study server."""

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
import threading
import time
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlsplit

from .materials import (
    locale_bundle_metadata,
    material_hashes,
    planned_trials,
    validated_sources,
)

STATIC_DIR = Path(__file__).with_name("static")
DEFAULT_KEY_FILE = Path(".runtime") / "microstudy-verification.key"
CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
    "connect-src 'self'; font-src 'none'; object-src 'none'; base-uri 'none'; "
    "form-action 'none'; frame-ancestors 'none'"
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
        key = path.read_bytes()
        if len(key) < 32:
            raise ValueError("verification key file must contain at least 32 bytes")
        _restrict_key_permissions(path)
        return key
    key = secrets.token_bytes(32)
    with path.open("xb") as handle:
        handle.write(key)
    _restrict_key_permissions(path)
    return key


def _restrict_key_permissions(path: Path) -> None:
    """Best-effort owner-only permissions; failure never exposes the key to clients."""
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def common_materials(locale: str) -> dict[str, Any]:
    stimuli, sequences = validated_sources()
    if locale not in stimuli["locale_contract"]["supported"]:
        raise ValueError("unsupported locale")
    bundle = json.loads(json.dumps(stimuli["locales"][locale]))
    formal = bundle.pop("formal")
    return {
        "ui_language": locale,
        "materials_version": stimuli["materials_version"],
        **locale_bundle_metadata(locale),
        "common": bundle,
        "sequence_codes": [row["code"] for row in sequences["sequences"]],
    }


def _empty_trial(slot: dict[str, Any], item: dict[str, Any], version: str) -> dict[str, Any]:
    return {
        "slot_index": slot["slot_index"], "condition": slot["condition"],
        "item": slot["item"], "pattern": slot["pattern"],
        "content_set": slot["content_set"], "block": slot["block"],
        "position": slot["position"], "planned": True, "presented": False,
        "q1_submitted": False, "q2_submitted": False, "complete": False,
        "submitted": False, "q1": None, "q2": None, "q1_correct": None,
        "q2_correct": None, "cca_correct": None, "rt_q1_ms": None,
        "rt_q2_ms": None, "rt_total_ms": None, "hidden_ms": None,
        "source_status": item["source_status"], "source_note": item["source_note"],
        "hypothetical": item["hypothetical"], "q1_missing": True,
        "q2_missing": True, "q1_correct_missing": True,
        "q2_correct_missing": True, "cca_correct_missing": True,
        "rt_q1_missing": True, "rt_q2_missing": True,
        "rt_total_missing": True, "hidden_ms_missing": True,
        "materials_version": version,
    }


class StudyServer(ThreadingHTTPServer):
    def __init__(
        self, address: tuple[str, int], key: bytes, *,
        max_sessions: int = 100, session_ttl_seconds: float = 7200,
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
                attempt for attempt, session in self.sessions.items()
                if now - session["last_seen"] >= self.session_ttl_seconds
            ]
            for attempt in expired:
                del self.sessions[attempt]
            expired_set = set(expired)
            self.start_requests = {
                request_id: cached
                for request_id, cached in self.start_requests.items()
                if cached[1].get("attempt_id") not in expired_set
            }


class StudyHandler(BaseHTTPRequestHandler):
    server: StudyServer
    server_version = "MicrostudyLocal"
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
            "application/json; charset=utf-8", status,
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
                    self.headers.get("X-CSRF-Token", ""), self.server.csrf_token
                )
            )
        return True

    def _request_id(self, body: dict[str, Any]) -> str:
        request_id = body.get("request_id")
        if not isinstance(request_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{16,128}", request_id):
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

    def _trial_payload(self, session: dict[str, Any]) -> dict[str, Any]:
        index = session["index"]
        slot = session["plan"][index]
        item = session["items"][slot["item"]]
        stimuli, _ = validated_sources()
        formal = stimuli["locales"][session["ui_language"]]["formal"]
        localized_item = next(
            row for row in formal["items"] if row["id"] == slot["item"]
        )
        if slot["condition"] == "Contract":
            order = stimuli["nonlocalized"]["primitive_ids"]
            labels = [
                formal["contract_labels"][primitive_id] for primitive_id in order
            ]
        else:
            order = item["flat_order"]
            labels = formal["flat_labels"]
        session["trials"][index]["presented"] = True
        session["phase"] = "q1"
        session["phase_started"] = time.monotonic()
        return {
            "phase": "q1", "trial_index": index, "slot_index": slot["slot_index"],
            "block": slot["block"], "position": slot["position"],
            "card": {
                "notice": formal["notice"],
                "aria_label": formal["evidence_panel_aria"],
                "rows": [
                    {
                        "label": label,
                        "body": localized_item["primitive_evidence"][primitive_id],
                    }
                    for label, primitive_id in zip(labels, order)
                ],
            },
            "q1": formal["q1"],
        }

    def do_GET(self) -> None:
        self.server.cleanup_expired()
        if not self._request_origin_ok(post=False):
            self._error(403, "request origin rejected")
            return
        parsed = urlsplit(self.path)
        path = unquote(parsed.path)
        if path == "/api/bootstrap":
            stimuli, _ = validated_sources()
            self._json({
                "csrf_token": self.server.csrf_token,
                "languages": [
                    {
                        "id": locale,
                        "label": stimuli["locales"][locale]["language_name"],
                    }
                    for locale in stimuli["locale_contract"]["supported"]
                ],
                "fallback": stimuli["locale_contract"]["fallback"],
                "auto_detect": stimuli["locale_contract"]["auto_detect"],
            })
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
            attempt = query.get("attempt_id", [None])[0]
            output_format = query.get("format", ["json"])[0]
            with self.server.session_lock:
                session = self.server.sessions.get(attempt or "")
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
                    (json.dumps(export, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
                    "application/json; charset=utf-8",
                )
            elif output_format == "csv":
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
                "/api/start": self._start, "/api/practice": self._practice,
                "/api/q1": self._q1, "/api/q2": self._q2,
                "/api/ease": self._ease, "/api/diagnostic": self._diagnostic,
                "/api/complete": self._complete, "/api/save-exit": self._save_exit,
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
                    self.server.start_requests[request_id] = (request_bytes(body), result)
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
                    session["requests"][(path, request_id)] = (request_bytes(body), result)
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
        stimuli, sequences = validated_sources()
        if (
            not isinstance(ui_language, str)
            or ui_language not in stimuli["locale_contract"]["supported"]
        ):
            raise ValueError("invalid ui_language")
        if len(self.server.sessions) >= self.server.max_sessions:
            raise ValueError("session capacity reached")
        attempt = str(uuid.uuid4())
        capability = secrets.token_urlsafe(32)
        self.server.attempt_serial += 1
        items = {
            row["stimulus_id"]: row
            for row in stimuli["nonlocalized"]["items"]
        }
        locale_meta = locale_bundle_metadata(ui_language)
        self.server.sessions[attempt] = {
            "attempt_id": attempt, "participant_code": participant,
            "run_id": self.server.run_id, "attempt_serial": self.server.attempt_serial,
            "capability": capability, "lock": threading.RLock(), "requests": {},
            "sequence": sequence, "plan": plan, "items": items,
            "ui_language": ui_language, **locale_meta,
            "trials": [_empty_trial(slot, items[slot["item"]], stimuli["materials_version"])
                       for slot in plan],
            "phase": "practice_q1", "index": 0, "started": time.monotonic(),
            "phase_started": time.monotonic(), "practice_q1": False,
            "practice_q2": False, "ease": {1: None, 2: None},
            "ease_done": {1: False, 2: False}, "diagnostic_presented": False,
            "diagnostic_submitted": False, "diagnostic_response": None,
            "material_schema_version": stimuli["schema_version"],
            "sequence_schema_version": sequences["schema_version"],
            "last_seen": self.server.clock(),
        }
        return {
            "attempt_id": attempt, "phase": "practice_q1",
            "capability": capability, "run_id": self.server.run_id,
            "attempt_serial": self.server.attempt_serial,
            "ui_language": ui_language,
        }

    def _practice(self, body: dict[str, Any], *, session: dict[str, Any]) -> dict[str, Any]:
        if set(body) != {"attempt_id", "step", "answer", "request_id"}:
            raise ValueError("invalid practice fields")
        stimuli, _ = validated_sources()
        practice = stimuli["locales"][session["ui_language"]]["practice"]
        if body["step"] == "q1" and session["phase"] == "practice_q1":
            if body["answer"] not in {
                row["id"] for row in practice["q1"]["options"]
            }:
                raise ValueError("invalid practice Q1")
            session["practice_q1"] = True
            session["phase"] = "practice_q2"
            return {"phase": "practice_q2"}
        if body["step"] == "q2" and session["phase"] == "practice_q2":
            if body["answer"] not in {
                row["id"] for row in practice["q2"]["options"]
            }:
                raise ValueError("invalid practice Q2")
            session["practice_q2"] = True
            payload = self._trial_payload(session)
            payload["feedback"] = practice["feedback"]
            return payload
        raise ValueError("invalid practice transition")

    def _q1(self, body: dict[str, Any], *, session: dict[str, Any]) -> dict[str, Any]:
        if set(body) != {"attempt_id", "answer", "request_id"}:
            raise ValueError("invalid Q1 fields")
        if session["phase"] != "q1":
            raise ValueError("Q1 is not available")
        answer = body["answer"]
        stimuli, _ = validated_sources()
        formal = stimuli["locales"][session["ui_language"]]["formal"]
        if answer not in {row["id"] for row in formal["q1"]["options"]}:
            raise ValueError("invalid Q1 answer")
        index = session["index"]
        trial = session["trials"][index]
        slot = session["plan"][index]
        trial["q1"] = answer
        trial["q1_submitted"] = True
        trial["q1_correct"] = answer == slot["q1_key"]
        trial["rt_q1_ms"] = max(0, round((time.monotonic() - session["phase_started"]) * 1000))
        for field in ("q1_missing", "q1_correct_missing", "rt_q1_missing"):
            trial[field] = False
        session["phase"] = "q2"
        session["phase_started"] = time.monotonic()
        template = next(
            row for row in formal["q2_templates"]
            if row["id"] == slot["q2_template_id"]
        )
        return {"phase": "q2", "q2": template}

    def _q2(self, body: dict[str, Any], *, session: dict[str, Any]) -> dict[str, Any]:
        if set(body) != {"attempt_id", "answer", "hidden_ms", "request_id"}:
            raise ValueError("invalid Q2 fields")
        if session["phase"] != "q2":
            raise ValueError("Q2 is not available")
        hidden_ms = body["hidden_ms"]
        if type(hidden_ms) is not int or hidden_ms < 0:
            raise ValueError("invalid hidden duration")
        index = session["index"]
        trial = session["trials"][index]
        slot = session["plan"][index]
        stimuli, _ = validated_sources()
        template = next(
            row for row in stimuli["locales"][session["ui_language"]]["formal"]["q2_templates"]
            if row["id"] == slot["q2_template_id"]
        )
        answer = body["answer"]
        if answer not in {row["id"] for row in template["options"]}:
            raise ValueError("invalid Q2 answer")
        trial.update({
            "q2": answer, "q2_submitted": True, "complete": True, "submitted": True,
            "q2_correct": answer == slot["q2_key"],
            "cca_correct": trial["q1_correct"] and answer == slot["q2_key"],
            "rt_q2_ms": max(0, round((time.monotonic() - session["phase_started"]) * 1000)),
            "hidden_ms": hidden_ms,
        })
        trial["rt_total_ms"] = trial["rt_q1_ms"] + trial["rt_q2_ms"]
        for field in ("q2_missing", "q2_correct_missing", "cca_correct_missing",
                      "rt_q2_missing", "rt_total_missing", "hidden_ms_missing"):
            trial[field] = False
        session["index"] += 1
        if session["index"] in {5, 10}:
            block = session["index"] // 5
            session["phase"] = f"ease_{block}"
            return {"phase": "ease", "block": block}
        return self._trial_payload(session)

    def _ease(self, body: dict[str, Any], *, session: dict[str, Any]) -> dict[str, Any]:
        if set(body) != {"attempt_id", "block", "answer", "request_id"}:
            raise ValueError("invalid ease fields")
        block = body["block"]
        if type(block) is not int or block not in (1, 2) or session["phase"] != f"ease_{block}":
            raise ValueError("invalid ease transition")
        keys = {
            row["id"]
            for row in validated_sources()[0]["locales"][session["ui_language"]][
                "ease"
            ]["options"]
        }
        if body["answer"] is not None and body["answer"] not in keys:
            raise ValueError("invalid ease answer")
        session["ease"][block] = body["answer"]
        session["ease_done"][block] = True
        if block == 1:
            return self._trial_payload(session)
        session["phase"] = "diagnostic"
        session["diagnostic_presented"] = True
        return {"phase": "diagnostic"}

    def _diagnostic(self, body: dict[str, Any], *, session: dict[str, Any]) -> dict[str, Any]:
        if set(body) != {"attempt_id", "answer", "request_id"}:
            raise ValueError("invalid diagnostic fields")
        if session["phase"] != "diagnostic":
            raise ValueError("invalid diagnostic transition")
        diagnostic = validated_sources()[0]["locales"][session["ui_language"]][
            "diagnostic"
        ]
        if body["answer"] is not None and body["answer"] not in {
            row["id"] for row in diagnostic["options"]
        }:
            raise ValueError("invalid diagnostic answer")
        session["diagnostic_submitted"] = body["answer"] is not None
        session["diagnostic_response"] = body["answer"]
        session["phase"] = "ready_complete"
        return {"phase": "ready_complete"}

    def _complete(self, body: dict[str, Any], *, session: dict[str, Any]) -> dict[str, Any]:
        if set(body) != {"attempt_id", "request_id"}:
            raise ValueError("invalid complete fields")
        if session["phase"] != "ready_complete" or session["index"] != 10:
            raise ValueError("attempt cannot be completed")
        export = self._canonical_export(session, complete=True)
        session["signed_export"] = sign_export(export, self.server.verification_key)
        session["phase"] = "export_ready"
        return {
            "phase": "export_ready", "attempt_id": session["attempt_id"],
            "complete": True,
        }

    def _save_exit(self, body: dict[str, Any], *, session: dict[str, Any]) -> dict[str, Any]:
        if set(body) != {"attempt_id", "request_id"}:
            raise ValueError("invalid save-exit fields")
        if session["phase"] not in {"q1", "q2", "ease_1", "ease_2", "diagnostic", "ready_complete"}:
            raise ValueError("save and exit is available only during the formal study")
        export = self._canonical_export(session, complete=False)
        session["signed_export"] = sign_export(export, self.server.verification_key)
        session["phase"] = "export_ready"
        return {
            "phase": "export_ready", "attempt_id": session["attempt_id"],
            "complete": False,
        }

    def _canonical_export(self, session: dict[str, Any], *, complete: bool) -> dict[str, Any]:
        stimuli, _ = validated_sources()
        diagnostic_key = stimuli["nonlocalized"]["answer_keys"]["diagnostic"]
        response = session["diagnostic_response"]
        return {
            "export_schema_version": "microstudy-export-v4-bilingual-signed",
            "material_schema_version": session["material_schema_version"],
            "sequence_schema_version": session["sequence_schema_version"],
            "material_hashes": material_hashes(),
            "attempt_id": session["attempt_id"],
            "run_id": session["run_id"], "attempt_serial": session["attempt_serial"],
            "participant_code": session["participant_code"],
            "sequence": session["sequence"],
            "ui_language": session["ui_language"],
            "locale_bundle_version": session["locale_bundle_version"],
            "locale_bundle_hash": session["locale_bundle_hash"],
            "completion_status": "complete" if complete else "partial",
            "complete": complete,
            "practice_presented": True, "practice_q1_submitted": session["practice_q1"],
            "practice_q2_submitted": session["practice_q2"], "practice_complete": True,
            "post_task_diagnostic_presented": session["diagnostic_presented"],
            "post_task_diagnostic_submitted": session["diagnostic_submitted"],
            "post_task_diagnostic_response": response,
            "post_task_diagnostic_correct": (
                None if response is None else response == diagnostic_key
            ),
            "block_1_ease": session["ease"][1], "block_2_ease": session["ease"][2],
            "mechanical_exclusion": False, "mechanical_exclusion_reason": "none",
            "trials": json.loads(json.dumps(session["trials"])),
        }

    @staticmethod
    def _csv(export: dict[str, Any]) -> str:
        def safe(value: Any) -> str:
            if value is None:
                return ""
            text = json.dumps(value, ensure_ascii=False, separators=(",", ":")) \
                if isinstance(value, (dict, list)) else str(value)
            return "'" + text if text.startswith(("=", "+", "-", "@")) else text

        session_fields = [key for key in export if key not in {"trials", "verification"}]
        trial_fields = list(export["trials"][0])
        fields = session_fields + ["verification_algorithm", "verification_key_id",
                                   "verification_signature"] + trial_fields
        output = io.StringIO(newline="")
        writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\r\n")
        writer.writeheader()
        for trial in export["trials"]:
            row = {key: safe(value) for key, value in export.items()
                   if key not in {"trials", "verification"}}
            row.update({
                "verification_algorithm": export["verification"]["algorithm"],
                "verification_key_id": export["verification"]["key_id"],
                "verification_signature": export["verification"]["signature"],
            })
            row.update({key: safe(value) for key, value in trial.items()})
            writer.writerow(row)
        return output.getvalue()


def create_server(
    host: str = "127.0.0.1", port: int = 8765,
    verification_key_file: Path | None = None,
    *, max_sessions: int = 100, session_ttl_seconds: float = 7200,
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
        (host, port), key, max_sessions=max_sessions,
        session_ttl_seconds=session_ttl_seconds,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the local-only micro-study preview.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--verification-key-file", type=Path, default=DEFAULT_KEY_FILE)
    parser.add_argument("--open", action="store_true", dest="open_browser")
    parser.add_argument("--max-sessions", type=int, default=100)
    parser.add_argument("--session-ttl-seconds", type=float, default=7200)
    args = parser.parse_args(argv)
    server = create_server(
        args.host, args.port, args.verification_key_file,
        max_sessions=args.max_sessions, session_ttl_seconds=args.session_ttl_seconds,
    )
    url = f"http://{args.host}:{server.server_port}/"
    print(f"Local study preview: {url}")
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
