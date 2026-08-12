"""Loopback-only, volatile V10 button-board owner-preview server."""

from __future__ import annotations

import argparse
import csv
import hmac
import io
import ipaddress
import json
import mimetypes
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

from cognitive_console.button_board_materials import (
    ANALYSIS_VERSION,
    EXPORT_SCHEMA_VERSION,
    LOCALES,
    MATERIAL_SCHEMA_VERSION,
    MATERIALS_VERSION,
    SEQUENCE_SCHEMA_VERSION,
)
from cognitive_console.microstudy.server import (
    CSP,
    load_or_create_key,
    request_bytes,
    sign_export,
)

from .materials import (
    common_materials,
    locale_bundle_metadata,
    material_hashes,
    planned_trials,
    q1_public_to_state,
    q1_state_to_public,
    stable_option_order,
    validated_sources,
)


STATIC_DIR = Path(__file__).with_name("static")
DEFAULT_KEY_FILE = Path(".runtime") / "button-board-v10-verification.key"
PARTICIPANT_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
PRIVATE_FIELD_RE = re.compile(
    r"(expected|correct_reason|correct_scope|q1_state|paper_state|reason_class|"
    r"scope_gate|quality_status|read_status|decisive_)",
    re.IGNORECASE,
)


def _ordered_rows(rows: list[dict[str, Any]], ids: list[str]) -> list[dict[str, Any]]:
    by_id = {row["id"]: row for row in rows}
    if set(by_id) != set(ids):
        raise ValueError("option order does not match public options")
    return [by_id[option_id] for option_id in ids]


def _empty_trial(slot: dict[str, Any]) -> dict[str, Any]:
    return {
        "slot_index": slot["slot_index"],
        "scene_id": slot["scene_id"],
        "position": slot["position"],
        "planned": True,
        "presented": False,
        "q1_selected": None,
        "q1_correct": None,
        "q1_locked_at": None,
        "scope_selected": None,
        "scope_choice_correct": None,
        "scope_gate_required": slot["scope_gate_required"],
        "reason_selected": None,
        "reason_choice_correct": None,
        "reason_correct": None,
        "gaa_trial": None,
        "strict_gaa_trial": None,
        "q1_submitted": False,
        "scope_submitted": False,
        "reason_submitted": False,
        "complete": False,
        "presented_q1_order": list(slot["q1_order"]),
        "presented_scope_order": [],
        "presented_reason_order": [],
        "relative_rt_q1": None,
        "relative_rt_scope": None,
        "relative_rt_reason": None,
        "materials_version": MATERIALS_VERSION,
    }


class ButtonBoardServer(ThreadingHTTPServer):
    def __init__(
        self,
        address: tuple[str, int],
        key: bytes,
        *,
        max_sessions: int = 100,
        session_ttl_seconds: float = 7200,
    ):
        super().__init__(address, ButtonBoardHandler)
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
        self.locale_allocation_counts = {locale: 0 for locale in LOCALES}

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


class ButtonBoardHandler(BaseHTTPRequestHandler):
    server: ButtonBoardServer
    server_version = "ButtonBoardV10Local"
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
        encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        if PRIVATE_FIELD_RE.search(encoded):
            raise RuntimeError("private answer material reached participant projection")
        self._send(encoded.encode("utf-8"), "application/json; charset=utf-8", status)

    def _error(self, status: int, message: str) -> None:
        self._send(
            json.dumps({"error": message}, separators=(",", ":")).encode("utf-8"),
            "application/json; charset=utf-8",
            status,
        )

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

    def _elapsed(self, session: dict[str, Any]) -> int:
        return max(0, round((time.monotonic() - session["started"]) * 1000))

    def _phase_elapsed(self, session: dict[str, Any]) -> int:
        return max(0, round((time.monotonic() - session["phase_started"]) * 1000))

    def _q1_options(
        self, session: dict[str, Any], order: list[str]
    ) -> list[dict[str, str]]:
        rows = session["common"]["q1_options"]
        return _ordered_rows(rows, order)

    def _practice_payload(self, session: dict[str, Any]) -> dict[str, Any]:
        scene = session["practice"]
        order = session["practice_q1_order"]
        return {
            "phase": "practice_q1",
            "progress": session["common"]["progress"]["practice"],
            "title": scene["title"],
            "record": scene["record"],
            "q1_options": self._q1_options(session, order),
        }

    def _formal_payload(self, session: dict[str, Any]) -> dict[str, Any]:
        index = session["index"]
        slot = session["plan"][index]
        materials, _, _ = validated_sources()
        scene = materials["locales"][session["selected_locale"]]["scenes"][
            slot["scene_id"]
        ]
        trial = session["trials"][index]
        trial["presented"] = True
        session["phase"] = "formal_q1"
        session["phase_started"] = time.monotonic()
        return {
            "phase": "formal_q1",
            "trial_index": index,
            "progress": session["common"]["progress"]["formal"].replace(
                "{current}", str(index + 1)
            ),
            "title": scene["title"],
            "record": scene["record"],
            "q1_options": self._q1_options(session, slot["q1_order"]),
        }

    def _scope_payload(
        self, session: dict[str, Any], *, practice: bool
    ) -> dict[str, Any]:
        if practice:
            rows = session["practice"]["scope_options"]
            order = session["practice_scope_order"]
        else:
            slot = session["plan"][session["index"]]
            materials, _, _ = validated_sources()
            rows = materials["locales"][session["selected_locale"]]["scenes"][
                slot["scene_id"]
            ]["scope_options"]
            order = slot["scope_order_ids"]
            session["trials"][session["index"]]["presented_scope_order"] = list(order)
        return {
            "phase": "practice_scope" if practice else "formal_scope",
            "scope_options": _ordered_rows(rows, order),
        }

    def _reason_payload(
        self, session: dict[str, Any], *, practice: bool
    ) -> dict[str, Any]:
        if practice:
            rows = session["practice"]["reason_options"]
            order = session["practice_reason_order"]
        else:
            slot = session["plan"][session["index"]]
            materials, _, _ = validated_sources()
            rows = materials["locales"][session["selected_locale"]]["scenes"][
                slot["scene_id"]
            ]["reason_options"]
            order = slot["reason_order_ids"]
            session["trials"][session["index"]]["presented_reason_order"] = list(order)
        return {
            "phase": "practice_reason" if practice else "formal_reason",
            "reason_options": _ordered_rows(rows, order),
        }

    def _attention_payload(self, session: dict[str, Any]) -> dict[str, Any]:
        session["phase"] = "attention_q1"
        session["phase_started"] = time.monotonic()
        order = session["attention_q1_order"]
        return {
            "phase": "attention_q1",
            "progress": session["common"]["progress"]["attention"],
            "instruction": session["common"]["attention"]["instruction"],
            "q1_options": self._q1_options(session, order),
        }

    def do_GET(self) -> None:
        self.server.cleanup_expired()
        if not self._request_origin_ok(post=False):
            self._error(403, "request origin rejected")
            return
        parsed = urlsplit(self.path)
        path = unquote(parsed.path)
        if path == "/api/bootstrap":
            materials, _, _ = validated_sources()
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
                    "fallback": None,
                    "auto_detect": False,
                    "minimum_width_px": materials["render_contract"][
                        "desktop_minimum_width_px"
                    ],
                }
            )
            return
        if path == "/api/welcome":
            query = parse_qs(parsed.query, keep_blank_values=True)
            if set(query) != {"selected_locale"} or len(
                query["selected_locale"]
            ) != 1:
                self._error(400, "exact selected_locale is required")
                return
            try:
                self._json(common_materials(query["selected_locale"][0]))
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
                "/api/continue": self._continue,
                "/api/q1": self._q1,
                "/api/scope": self._scope,
                "/api/reason": self._reason,
                "/api/attention": self._attention,
                "/api/reflection": self._reflection,
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
        if set(body) != {"participant_code", "selected_locale", "request_id"}:
            raise ValueError("invalid start fields")
        participant = body["participant_code"]
        locale = body["selected_locale"]
        if not isinstance(participant, str) or not PARTICIPANT_RE.fullmatch(participant):
            raise ValueError("invalid participant code")
        if locale not in LOCALES:
            raise ValueError("invalid selected locale")
        if len(self.server.sessions) >= self.server.max_sessions:
            raise ValueError("session capacity reached")
        allocation_serial = self.server.locale_allocation_counts[locale]
        allocation_cell = allocation_serial % 24
        allocation_block = allocation_serial // 24
        sequence_id = f"BB10-{allocation_cell // 2 + 1:02d}"
        ab_variant = "F1" if allocation_cell % 2 == 0 else "F2"
        plan = planned_trials(sequence_id, ab_variant, participant)
        materials, sequences, keys = validated_sources()
        common_payload = common_materials(locale)
        hashes = material_hashes()
        practice = materials["locales"][locale]["practice"]
        practice_scope = stable_option_order(
            practice["scope_options"],
            participant,
            "P1",
            hashes["canonical_materials_hash"],
            "scope",
        )
        practice_reason = stable_option_order(
            practice["reason_options"],
            participant,
            "P1",
            hashes["canonical_materials_hash"],
            "reason",
        )
        q1_ids = list(plan[0]["q1_order"])
        rotate = int(
            hashlib_sha256_int(
                f"{participant}\0P1\0{hashes['canonical_materials_hash']}"
            )
            % 4
        )
        practice_q1_order = q1_ids[rotate:] + q1_ids[:rotate]
        attention_q1_order = list(reversed(practice_q1_order))
        attention_reasons = stable_option_order(
            common_payload["common"]["attention"]["reason_options"],
            participant,
            "AC1",
            hashes["canonical_materials_hash"],
            "reason",
        )
        attempt_id = str(uuid.uuid4())
        capability = secrets.token_urlsafe(32)
        self.server.attempt_serial += 1
        now = time.monotonic()
        session = {
            "attempt_id": attempt_id,
            "participant_code": participant,
            "run_id": self.server.run_id,
            "attempt_serial": self.server.attempt_serial,
            "capability": capability,
            "lock": threading.RLock(),
            "requests": {},
            "selected_locale": locale,
            **locale_bundle_metadata(locale),
            "common": common_payload["common"],
            "practice": practice,
            "practice_q1_order": practice_q1_order,
            "practice_scope_order": [row["id"] for row in practice_scope],
            "practice_reason_order": [row["id"] for row in practice_reason],
            "attention_q1_order": attention_q1_order,
            "attention_reason_order": [row["id"] for row in attention_reasons],
            "sequence_id": sequence_id,
            "ab_variant": ab_variant,
            "allocation_block": allocation_block,
            "allocation_cell": allocation_cell,
            "plan": plan,
            "trials": [_empty_trial(slot) for slot in plan],
            "phase": "practice_q1",
            "index": 0,
            "started": now,
            "phase_started": now,
            "last_seen": self.server.clock(),
            "practice_status": {
                "q1_selected": None,
                "scope_selected": None,
                "reason_selected": None,
                "complete": False,
            },
            "attention": {
                "q1_selected": None,
                "reason_selected": None,
                "pass": None,
            },
            "reflection": {
                "helpful": None,
                "confusing": None,
                "amount": None,
            },
            "material_schema_version": materials["schema_version"],
            "sequence_schema_version": sequences["schema_version"],
            "ab_invariance_hash": keys["ab_invariance_hash"],
        }
        self.server.sessions[attempt_id] = session
        self.server.locale_allocation_counts[locale] += 1
        return {
            "attempt_id": attempt_id,
            "phase": "practice_q1",
            "capability": capability,
            "run_id": self.server.run_id,
            "attempt_serial": self.server.attempt_serial,
            "selected_locale": locale,
        }

    def _practice(
        self, body: dict[str, Any], *, session: dict[str, Any]
    ) -> dict[str, Any]:
        if set(body) != {"attempt_id", "step", "answer", "request_id"}:
            raise ValueError("invalid practice fields")
        answer = body["answer"]
        step = body["step"]
        if step == "q1" and session["phase"] == "practice_q1":
            state = q1_public_to_state(answer)
            session["practice_status"]["q1_selected"] = state
            session["phase"] = "practice_scope"
            session["phase_started"] = time.monotonic()
            return self._scope_payload(session, practice=True)
        if step == "scope" and session["phase"] == "practice_scope":
            if answer not in {row["id"] for row in session["practice"]["scope_options"]}:
                raise ValueError("invalid practice scope")
            session["practice_status"]["scope_selected"] = answer
            session["phase"] = "practice_reason"
            session["phase_started"] = time.monotonic()
            return self._reason_payload(session, practice=True)
        if step == "reason" and session["phase"] == "practice_reason":
            if answer not in {row["id"] for row in session["practice"]["reason_options"]}:
                raise ValueError("invalid practice reason")
            session["practice_status"]["reason_selected"] = answer
            session["practice_status"]["complete"] = True
            session["phase"] = "formal_intro"
            return {
                "phase": "formal_intro",
                "feedback": session["practice"]["feedback"],
            }
        raise ValueError("invalid practice transition")

    def _continue(
        self, body: dict[str, Any], *, session: dict[str, Any]
    ) -> dict[str, Any]:
        if set(body) != {"attempt_id", "request_id"}:
            raise ValueError("invalid continue fields")
        if session["phase"] != "formal_intro":
            raise ValueError("formal continuation is not available")
        return self._formal_payload(session)

    def _q1(self, body: dict[str, Any], *, session: dict[str, Any]) -> dict[str, Any]:
        if set(body) != {"attempt_id", "answer", "request_id"}:
            raise ValueError("invalid Q1 fields")
        if session["phase"] != "formal_q1":
            raise ValueError("Q1 is not available")
        state = q1_public_to_state(body["answer"])
        index = session["index"]
        trial = session["trials"][index]
        slot = session["plan"][index]
        trial.update(
            {
                "q1_selected": state,
                "q1_correct": state == slot["q1_state"],
                "gaa_trial": state == slot["q1_state"],
                "q1_submitted": True,
                "q1_locked_at": self._elapsed(session),
                "relative_rt_q1": self._phase_elapsed(session),
            }
        )
        session["phase"] = "formal_scope"
        session["phase_started"] = time.monotonic()
        return self._scope_payload(session, practice=False)

    def _scope(
        self, body: dict[str, Any], *, session: dict[str, Any]
    ) -> dict[str, Any]:
        if set(body) != {"attempt_id", "answer", "request_id"}:
            raise ValueError("invalid scope fields")
        if session["phase"] != "formal_scope":
            raise ValueError("scope question is not available")
        index = session["index"]
        trial = session["trials"][index]
        slot = session["plan"][index]
        answer = body["answer"]
        if answer not in set(slot["scope_order_ids"]):
            raise ValueError("invalid scope answer")
        trial.update(
            {
                "scope_selected": answer,
                "scope_choice_correct": answer == slot["correct_scope_id"],
                "scope_submitted": True,
                "relative_rt_scope": self._phase_elapsed(session),
            }
        )
        session["phase"] = "formal_reason"
        session["phase_started"] = time.monotonic()
        return self._reason_payload(session, practice=False)

    def _reason(
        self, body: dict[str, Any], *, session: dict[str, Any]
    ) -> dict[str, Any]:
        if set(body) != {"attempt_id", "answer", "request_id"}:
            raise ValueError("invalid reason fields")
        if session["phase"] != "formal_reason":
            raise ValueError("reason question is not available")
        index = session["index"]
        trial = session["trials"][index]
        slot = session["plan"][index]
        answer = body["answer"]
        if answer not in set(slot["reason_order_ids"]):
            raise ValueError("invalid reason answer")
        reason_choice_correct = answer == slot["correct_reason_id"]
        scope_gate_correct = (
            bool(trial["scope_choice_correct"])
            if slot["scope_gate_required"]
            else True
        )
        reason_correct = reason_choice_correct and scope_gate_correct
        trial.update(
            {
                "reason_selected": answer,
                "reason_choice_correct": reason_choice_correct,
                "reason_correct": reason_correct,
                "reason_submitted": True,
                "strict_gaa_trial": bool(trial["q1_correct"]) and reason_correct,
                "complete": True,
                "relative_rt_reason": self._phase_elapsed(session),
            }
        )
        session["index"] += 1
        if session["index"] == 6:
            return self._attention_payload(session)
        return self._formal_payload(session)

    def _attention(
        self, body: dict[str, Any], *, session: dict[str, Any]
    ) -> dict[str, Any]:
        if set(body) != {"attempt_id", "step", "answer", "request_id"}:
            raise ValueError("invalid attention fields")
        step, answer = body["step"], body["answer"]
        _, _, keys = validated_sources()
        if step == "q1" and session["phase"] == "attention_q1":
            session["attention"]["q1_selected"] = q1_public_to_state(answer)
            session["phase"] = "attention_reason"
            session["phase_started"] = time.monotonic()
            rows = session["common"]["attention"]["reason_options"]
            return {
                "phase": "attention_reason",
                "reason_options": _ordered_rows(
                    rows, session["attention_reason_order"]
                ),
            }
        if step == "reason" and session["phase"] == "attention_reason":
            valid = {
                row["id"] for row in session["common"]["attention"]["reason_options"]
            }
            if answer not in valid:
                raise ValueError("invalid attention reason")
            session["attention"]["reason_selected"] = answer
            session["attention"]["pass"] = (
                session["attention"]["q1_selected"]
                == keys["attention"]["q1_state"]
                and answer == keys["attention"]["correct_reason_id"]
            )
            session["phase"] = "reflection"
            return {"phase": "reflection"}
        raise ValueError("invalid attention transition")

    def _reflection(
        self, body: dict[str, Any], *, session: dict[str, Any]
    ) -> dict[str, Any]:
        if set(body) != {
            "attempt_id", "helpful", "confusing", "amount", "request_id"
        }:
            raise ValueError("invalid reflection fields")
        if session["phase"] != "reflection":
            raise ValueError("reflection is not available")
        options = session["common"]["reflection"]["options"]
        for field in ("helpful", "confusing", "amount"):
            if body[field] not in {row["id"] for row in options[field]}:
                raise ValueError(f"invalid reflection {field}")
            session["reflection"][field] = body[field]
        session["phase"] = "ready_complete"
        return {"phase": "ready_complete"}

    def _complete(
        self, body: dict[str, Any], *, session: dict[str, Any]
    ) -> dict[str, Any]:
        if set(body) != {"attempt_id", "request_id"}:
            raise ValueError("invalid complete fields")
        if session["phase"] != "ready_complete" or not all(
            row["complete"] for row in session["trials"]
        ):
            raise ValueError("attempt cannot be completed")
        export = self._canonical_export(session, complete=True)
        session["signed_export"] = sign_export(export, self.server.verification_key)
        session["phase"] = "export_ready"
        return {"phase": "export_ready", "attempt_id": session["attempt_id"], "complete": True}

    def _save_exit(
        self, body: dict[str, Any], *, session: dict[str, Any]
    ) -> dict[str, Any]:
        if set(body) != {"attempt_id", "request_id"}:
            raise ValueError("invalid save-exit fields")
        if session["phase"] not in {
            "formal_q1", "formal_scope", "formal_reason", "attention_q1",
            "attention_reason", "reflection", "ready_complete",
        }:
            raise ValueError("partial export is not available in this phase")
        export = self._canonical_export(session, complete=False)
        session["signed_export"] = sign_export(export, self.server.verification_key)
        session["phase"] = "export_ready"
        return {"phase": "export_ready", "attempt_id": session["attempt_id"], "complete": False}

    def _canonical_export(
        self, session: dict[str, Any], *, complete: bool
    ) -> dict[str, Any]:
        return {
            "schema_version": MATERIAL_SCHEMA_VERSION,
            "export_schema_version": EXPORT_SCHEMA_VERSION,
            "sequence_schema_version": SEQUENCE_SCHEMA_VERSION,
            "materials_version": MATERIALS_VERSION,
            "analysis_version": ANALYSIS_VERSION,
            **material_hashes(),
            "ab_invariance_hash": session["ab_invariance_hash"],
            "attempt_id": session["attempt_id"],
            "run_id": session["run_id"],
            "attempt_serial": session["attempt_serial"],
            "participant_code": session["participant_code"],
            "selected_locale": session["selected_locale"],
            "locale_bundle_version": session["locale_bundle_version"],
            "locale_bundle_hash": session["locale_bundle_hash"],
            "sequence_id": session["sequence_id"],
            "ab_variant": session["ab_variant"],
            "allocation_block": session["allocation_block"],
            "allocation_cell": session["allocation_cell"],
            "completion_status": "complete" if complete else "partial",
            "complete": complete,
            "practice_status": json.loads(json.dumps(session["practice_status"])),
            "attention_check": json.loads(json.dumps(session["attention"])),
            "reflection": json.loads(json.dumps(session["reflection"])),
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


def hashlib_sha256_int(value: str) -> int:
    import hashlib

    return int(hashlib.sha256(value.encode("utf-8")).hexdigest(), 16)


def create_server(
    host: str = "127.0.0.1",
    port: int = 8878,
    verification_key_file: Path | None = None,
    *,
    max_sessions: int = 100,
    session_ttl_seconds: float = 7200,
) -> ButtonBoardServer:
    try:
        address = ipaddress.ip_address(host)
    except ValueError as exc:
        raise ValueError("host must be a loopback IP address") from exc
    if not address.is_loopback:
        raise ValueError("refusing non-loopback host")
    if max_sessions < 1 or session_ttl_seconds <= 0:
        raise ValueError("session limits must be positive")
    key = load_or_create_key(verification_key_file or DEFAULT_KEY_FILE)
    return ButtonBoardServer(
        (host, port),
        key,
        max_sessions=max_sessions,
        session_ttl_seconds=session_ttl_seconds,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the V10 button-board owner-local preview."
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8878)
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
    print(f"Local V10 button-board preview: {url}")
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
