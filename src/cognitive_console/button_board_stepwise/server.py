"""Loopback-only, volatile V11 stepwise owner-preview server."""

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

from cognitive_console.button_board_stepwise_materials import (
    ANALYSIS_VERSION,
    EXPORT_SCHEMA_VERSION,
    LOCALES,
    MATERIAL_SCHEMA_VERSION,
    MATERIALS_VERSION,
    SEQUENCE_SCHEMA_VERSION,
    route_participant,
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
    question_material,
    scene_material,
    stable_option_order,
    validated_sources,
)


STATIC_DIR = Path(__file__).with_name("static")
DEFAULT_KEY_FILE = Path(".runtime") / "button-board-stepwise-v11-verification.key"
PARTICIPANT_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
PRIVATE_FIELD_RE = re.compile(
    r"(expected|comparison_rule|required_readings|required_scope_dimensions|"
    r"scope_correct|scope_written|decisive_step|gaa_correct|strict_correct|"
    r"correctness|^nature$|^compared$|^better$|^harm$)",
    re.IGNORECASE,
)
EXPORTED_TRIAL_FIELDS = (
    "slot_index",
    "scene_id",
    "variant_id",
    "position",
    "planned",
    "presented",
    "step_presented",
    "step_selected_option_id",
    "step_presented_option_order",
    "step_shown_at_relative",
    "step_answered_at_relative",
    "participant_exit_step",
    "participant_derived_state",
    "scope_selected_id",
    "completion_status",
    "materials_version",
)


def _ordered_rows(rows: list[dict[str, Any]], ids: list[str]) -> list[dict[str, Any]]:
    by_id = {row["id"]: row for row in rows}
    if set(by_id) != set(ids):
        raise ValueError("option order does not match public options")
    return [by_id[row_id] for row_id in ids]


def _empty_trial(slot: dict[str, Any]) -> dict[str, Any]:
    return {
        "slot_index": slot["slot_index"],
        "scene_id": slot["scene_id"],
        "variant_id": (
            slot["scene_id"].split("-", 1)[1]
            if slot["scene_id"].startswith("AB1-")
            else None
        ),
        "position": slot["position"],
        "planned": True,
        "presented": False,
        "step_presented": [],
        "step_selected_option_id": [],
        "step_presented_option_order": [],
        "step_shown_at_relative": [],
        "step_answered_at_relative": [],
        "participant_exit_step": None,
        "participant_derived_state": None,
        "scope_selected_id": None,
        "completion_status": "not_started",
        "materials_version": MATERIALS_VERSION,
    }


class StepwiseServer(ThreadingHTTPServer):
    def __init__(
        self,
        address: tuple[str, int],
        key: bytes,
        *,
        max_sessions: int = 100,
        session_ttl_seconds: float = 7200,
    ):
        super().__init__(address, StepwiseHandler)
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


class StepwiseHandler(BaseHTTPRequestHandler):
    server: StepwiseServer
    server_version = "ButtonBoardStepwiseV11Local"
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
        def assert_public_keys(item: Any) -> None:
            if isinstance(item, dict):
                for key, child in item.items():
                    if PRIVATE_FIELD_RE.search(key):
                        raise RuntimeError(
                            "private derivation material reached participant projection"
                        )
                    assert_public_keys(child)
            elif isinstance(item, list):
                for child in item:
                    assert_public_keys(child)

        assert_public_keys(value)
        encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
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
        if not hmac.compare_digest(
            self.headers.get("X-Study-Capability", ""),
            session["capability"],
        ):
            raise ValueError("invalid session capability")
        return session

    @staticmethod
    def _elapsed(session: dict[str, Any]) -> int:
        return max(0, round((time.monotonic() - session["started"]) * 1000))

    def _current_trial(self, session: dict[str, Any]) -> dict[str, Any]:
        if session["mode"] == "practice":
            return session["practice_trial"]
        return session["trials"][session["index"]]

    def _current_scene_id(self, session: dict[str, Any]) -> str:
        return "P1" if session["mode"] == "practice" else session["plan"][session["index"]]["scene_id"]

    def _question_payload(self, session: dict[str, Any], step: int) -> dict[str, Any]:
        locale = session["selected_locale"]
        scene_id = self._current_scene_id(session)
        question = question_material(locale, step)
        if step == 6:
            public_scene = (
                session["practice"]
                if session["mode"] == "practice"
                else scene_material(locale, scene_id)
            )
            order = (
                session["practice_scope_order"]
                if session["mode"] == "practice"
                else session["plan"][session["index"]]["scope_order_ids"]
            )
            options = _ordered_rows(public_scene["scope_options"], order)
        else:
            options = question["options"]
        trial = self._current_trial(session)
        if step in trial["step_presented"]:
            raise ValueError("step was already presented")
        trial["step_presented"].append(step)
        trial["step_presented_option_order"].append([row["id"] for row in options])
        trial["step_shown_at_relative"].append(self._elapsed(session))
        trial["completion_status"] = "in_progress"
        return {
            "phase": "practice_step" if session["mode"] == "practice" else "formal_step",
            "step": step,
            "question": question["prompt"],
            "options": options,
            "path": self._public_path(session),
        }

    def _trial_payload(self, session: dict[str, Any]) -> dict[str, Any]:
        locale = session["selected_locale"]
        if session["mode"] == "practice":
            scene = session["practice"]
            progress = session["common"]["progress"]["practice"]
        else:
            scene = scene_material(locale, self._current_scene_id(session))
            progress = session["common"]["progress"]["formal"].replace(
                "{current}", str(session["index"] + 1)
            )
        trial = self._current_trial(session)
        trial["presented"] = True
        question = self._question_payload(session, 1)
        return {
            **question,
            "progress": progress,
            "scene": scene,
        }

    def _result_payload(
        self,
        session: dict[str, Any],
        state: str,
    ) -> dict[str, Any]:
        destination = next(
            row
            for row, private in zip(
                session["common"]["destinations"],
                ("SUPPORTED", "DIAGNOSTIC", "WITHHELD", "UNRESOLVED"),
            )
            if private == state
        )
        path = self._public_path(session)
        response = {
            "phase": (
                "practice_result"
                if session["mode"] == "practice"
                else "formal_result"
            ),
            "destination": {
                "id": destination["id"],
                "label": destination["label"],
                "description": destination["description"],
            },
            "path": path,
            "has_next_formal": session["mode"] == "formal" and session["index"] < 5,
        }
        if session["mode"] == "practice":
            response["feedback"] = session["practice"]["feedback"]
        return response

    def _public_path(self, session: dict[str, Any]) -> list[dict[str, Any]]:
        trial = self._current_trial(session)
        path = []
        for step, answer in zip(
            trial["step_presented"],
            trial["step_selected_option_id"],
        ):
            question = question_material(session["selected_locale"], step)
            rows = (
                (
                    session["practice"]["scope_options"]
                    if session["mode"] == "practice"
                    else scene_material(
                        session["selected_locale"], self._current_scene_id(session)
                    )["scope_options"]
                )
                if step == 6
                else question["options"]
            )
            label = next(row["text"] for row in rows if row["id"] == answer)
            path.append({"step": step, "answer_id": answer, "answer_text": label})
        return path

    def _attention_payload(self, session: dict[str, Any]) -> dict[str, Any]:
        session["phase"] = "attention"
        question = question_material(session["selected_locale"], 1)
        return {
            "phase": "attention",
            "progress": session["common"]["progress"]["attention"],
            "heading": session["common"]["attention"]["heading"],
            "instruction": session["common"]["attention"]["instruction"],
            "step": 1,
            "question": question["prompt"],
            "options": question["options"],
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
                    "minimum_width_px": materials["render_contract"]["desktop_minimum_width_px"],
                }
            )
            return
        if path == "/api/welcome":
            query = parse_qs(parsed.query, keep_blank_values=True)
            if set(query) != {"selected_locale"} or len(query["selected_locale"]) != 1:
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
                if (
                    session is None
                    or session["phase"] != "export_ready"
                    or not hmac.compare_digest(
                        self.headers.get("X-Study-Capability", ""),
                        session["capability"],
                    )
                ):
                    self._error(409, "export is not available")
                    return
                if output_format not in {"json", "csv"}:
                    self._error(400, "unsupported export format")
                    return
                export = session["signed_export"]
            if output_format == "json":
                body = (json.dumps(export, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
                self._send(body, "application/json; charset=utf-8")
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
                "/api/continue": self._continue,
                "/api/step": self._step,
                "/api/revise-step": self._revise_step,
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
        sequence_id = f"BBS11-{allocation_cell // 2 + 1:02d}"
        ab_variant = "A" if allocation_cell % 2 == 0 else "B"
        plan = planned_trials(sequence_id, ab_variant, participant)
        materials, sequences, keys = validated_sources()
        common_payload = common_materials(locale)
        canonical_hash = material_hashes()["canonical_materials_hash"]
        practice = materials["locales"][locale]["practice"]
        practice_scope = stable_option_order(
            practice["scope_options"],
            participant,
            "P1",
            canonical_hash,
            "scope",
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
            "practice_scope_order": [row["id"] for row in practice_scope],
            "practice_trial": {
                **_empty_trial(
                    {
                        "slot_index": 0,
                        "scene_id": "P1",
                        "position": 0,
                    }
                ),
                "planned": False,
            },
            "sequence_id": sequence_id,
            "ab_variant": ab_variant,
            "allocation_block": allocation_block,
            "allocation_cell": allocation_cell,
            "plan": plan,
            "trials": [_empty_trial(slot) for slot in plan],
            "mode": "practice",
            "phase": "practice_ready",
            "index": 0,
            "started": now,
            "last_seen": self.server.clock(),
            "attention_selected_id": None,
            "reflection": {
                "hardest": None,
                "confusing": None,
                "amount": None,
                "pace": None,
            },
            "material_schema_version": materials["schema_version"],
            "sequence_schema_version": sequences["schema_version"],
            "ab_invariance_hash": keys["ab_invariance_hash"],
        }
        self.server.sessions[attempt_id] = session
        self.server.locale_allocation_counts[locale] += 1
        return {
            "attempt_id": attempt_id,
            "phase": "practice_ready",
            "capability": capability,
            "run_id": self.server.run_id,
            "attempt_serial": self.server.attempt_serial,
            "selected_locale": locale,
        }

    def _continue(
        self,
        body: dict[str, Any],
        *,
        session: dict[str, Any],
    ) -> dict[str, Any]:
        if set(body) != {"attempt_id", "request_id"}:
            raise ValueError("invalid continue fields")
        if session["phase"] == "practice_ready":
            session["mode"] = "practice"
            session["phase"] = "practice_step"
            return self._trial_payload(session)
        if session["phase"] == "practice_result":
            session["mode"] = "formal"
            session["phase"] = "formal_intro"
            return {"phase": "formal_intro"}
        if session["phase"] == "formal_intro":
            session["phase"] = "formal_step"
            return self._trial_payload(session)
        if session["phase"] == "formal_result":
            session["index"] += 1
            if session["index"] >= 6:
                return self._attention_payload(session)
            session["phase"] = "formal_step"
            return self._trial_payload(session)
        raise ValueError("continue is not available")

    def _step(
        self,
        body: dict[str, Any],
        *,
        session: dict[str, Any],
    ) -> dict[str, Any]:
        if set(body) != {"attempt_id", "step", "answer", "request_id"}:
            raise ValueError("invalid step fields")
        if session["phase"] not in {"practice_step", "formal_step"}:
            raise ValueError("step answer is not available")
        trial = self._current_trial(session)
        step = body["step"]
        answer = body["answer"]
        if type(step) is not int or not trial["step_presented"] or step != trial["step_presented"][-1]:
            raise ValueError("invalid current step")
        if len(trial["step_selected_option_id"]) + 1 != len(trial["step_presented"]):
            raise ValueError("current step was already answered")
        option_order = trial["step_presented_option_order"][-1]
        if answer not in option_order:
            raise ValueError("invalid step answer")
        trial["step_selected_option_id"].append(answer)
        trial["step_answered_at_relative"].append(self._elapsed(session))
        if step == 6:
            trial["scope_selected_id"] = answer
        path = [
            {"step": shown, "answer": selected}
            for shown, selected in zip(
                trial["step_presented"],
                trial["step_selected_option_id"],
            )
        ]
        route = route_participant(path)
        if route["done"]:
            trial["participant_exit_step"] = step
            trial["participant_derived_state"] = route["state"]
            trial["completion_status"] = "complete"
            session["phase"] = (
                "practice_result" if session["mode"] == "practice" else "formal_result"
            )
            return self._result_payload(session, route["state"])
        next_step = route["next_step"]
        return self._question_payload(session, next_step)

    def _revise_step(
        self,
        body: dict[str, Any],
        *,
        session: dict[str, Any],
    ) -> dict[str, Any]:
        if set(body) != {"attempt_id", "step", "request_id"}:
            raise ValueError("invalid revise-step fields")
        if session["phase"] not in {
            "practice_step",
            "practice_result",
            "formal_step",
            "formal_result",
        }:
            raise ValueError("step revision is not available")
        trial = self._current_trial(session)
        step = body["step"]
        if type(step) is not int or step not in trial["step_presented"]:
            raise ValueError("invalid revision step")
        index = trial["step_presented"].index(step)
        if index >= len(trial["step_selected_option_id"]):
            raise ValueError("only answered steps can be revised")
        for field in (
            "step_presented",
            "step_presented_option_order",
            "step_shown_at_relative",
        ):
            del trial[field][index:]
        for field in ("step_selected_option_id", "step_answered_at_relative"):
            del trial[field][index:]
        trial["participant_exit_step"] = None
        trial["participant_derived_state"] = None
        trial["scope_selected_id"] = None
        trial["completion_status"] = "in_progress"
        session["phase"] = (
            "practice_step" if session["mode"] == "practice" else "formal_step"
        )
        return self._question_payload(session, step)

    def _attention(
        self,
        body: dict[str, Any],
        *,
        session: dict[str, Any],
    ) -> dict[str, Any]:
        if set(body) != {"attempt_id", "answer", "request_id"}:
            raise ValueError("invalid attention fields")
        if session["phase"] != "attention":
            raise ValueError("attention check is not available")
        valid = {row["id"] for row in question_material(session["selected_locale"], 1)["options"]}
        if body["answer"] not in valid:
            raise ValueError("invalid attention answer")
        session["attention_selected_id"] = body["answer"]
        session["phase"] = "reflection"
        return {"phase": "reflection"}

    def _reflection(
        self,
        body: dict[str, Any],
        *,
        session: dict[str, Any],
    ) -> dict[str, Any]:
        expected = {"attempt_id", "hardest", "confusing", "amount", "pace", "request_id"}
        if set(body) != expected:
            raise ValueError("invalid reflection fields")
        if session["phase"] != "reflection":
            raise ValueError("reflection is not available")
        options = session["common"]["reflection"]["options"]
        for field in ("hardest", "confusing", "amount", "pace"):
            if body[field] not in {row["id"] for row in options[field]}:
                raise ValueError(f"invalid reflection {field}")
            session["reflection"][field] = body[field]
        session["phase"] = "ready_complete"
        return {"phase": "ready_complete"}

    def _complete(
        self,
        body: dict[str, Any],
        *,
        session: dict[str, Any],
    ) -> dict[str, Any]:
        if set(body) != {"attempt_id", "request_id"}:
            raise ValueError("invalid complete fields")
        if session["phase"] != "ready_complete" or not all(
            row["completion_status"] == "complete" for row in session["trials"]
        ):
            raise ValueError("attempt cannot be completed")
        export = self._canonical_export(session, complete=True)
        session["signed_export"] = sign_export(export, self.server.verification_key)
        session["phase"] = "export_ready"
        return {"phase": "export_ready", "attempt_id": session["attempt_id"], "complete": True}

    def _save_exit(
        self,
        body: dict[str, Any],
        *,
        session: dict[str, Any],
    ) -> dict[str, Any]:
        if set(body) != {"attempt_id", "request_id"}:
            raise ValueError("invalid save-exit fields")
        if session["phase"] not in {
            "formal_step",
            "formal_result",
            "attention",
            "reflection",
            "ready_complete",
        }:
            raise ValueError("partial export is not available in this phase")
        export = self._canonical_export(session, complete=False)
        session["signed_export"] = sign_export(export, self.server.verification_key)
        session["phase"] = "export_ready"
        return {"phase": "export_ready", "attempt_id": session["attempt_id"], "complete": False}

    def _canonical_export(
        self,
        session: dict[str, Any],
        *,
        complete: bool,
    ) -> dict[str, Any]:
        trials = [
            {
                field: json.loads(json.dumps(trial[field]))
                for field in EXPORTED_TRIAL_FIELDS
            }
            for trial in session["trials"]
        ]
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
            "practice_status": {
                field: json.loads(json.dumps(session["practice_trial"][field]))
                for field in (
                    "step_presented",
                    "step_selected_option_id",
                    "participant_exit_step",
                    "participant_derived_state",
                    "scope_selected_id",
                    "completion_status",
                )
            },
            "attention_selected_id": session["attention_selected_id"],
            "reflection_choice_ids": json.loads(json.dumps(session["reflection"])),
            "trials": trials,
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

        session_fields = [key for key in export if key not in {"trials", "verification"}]
        trial_fields = list(export["trials"][0])
        fields = session_fields + [
            "verification_algorithm",
            "verification_key_id",
            "verification_signature",
            *trial_fields,
        ]
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
    port: int = 8891,
    verification_key_file: Path | None = None,
    *,
    max_sessions: int = 100,
    session_ttl_seconds: float = 7200,
) -> StepwiseServer:
    try:
        address = ipaddress.ip_address(host)
    except ValueError as exc:
        raise ValueError("host must be a loopback IP address") from exc
    if not address.is_loopback:
        raise ValueError("refusing non-loopback host")
    if max_sessions < 1 or session_ttl_seconds <= 0:
        raise ValueError("session limits must be positive")
    key = load_or_create_key(verification_key_file or DEFAULT_KEY_FILE)
    return StepwiseServer(
        (host, port),
        key,
        max_sessions=max_sessions,
        session_ttl_seconds=session_ttl_seconds,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the V11 stepwise button-board owner-local preview."
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8891)
    parser.add_argument("--verification-key-file", type=Path, default=DEFAULT_KEY_FILE)
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
    print(f"Local V11 stepwise button-board preview: {url}")
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
