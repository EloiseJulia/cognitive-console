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

from .materials import material_hashes, planned_trials, validated_sources

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
        return key
    key = secrets.token_bytes(32)
    with path.open("xb") as handle:
        handle.write(key)
    return key


def participant_materials() -> dict[str, Any]:
    stimuli, sequences = validated_sources()
    participant = json.loads(json.dumps(stimuli["participant_materials"]))
    participant["post_task_manipulation_diagnostic"].pop("correct_key", None)
    participant["practice"]["q1"].pop("correct_key", None)
    participant["practice"]["q2"].pop("correct_key", None)
    items = [
        {
            "stimulus_id": item["stimulus_id"],
            "primitive_evidence": item["primitive_evidence"],
            "flat_order": item["flat_order"],
        }
        for item in stimuli["items"]
    ]
    templates = [
        {"template_id": row["template_id"], "text": row["text"], "options": row["options"]}
        for row in stimuli["q2_templates"]
    ]
    return {
        "materials_version": stimuli["materials_version"],
        "primitive_ids": stimuli["primitive_ids"],
        "contract_headings": stimuli["contract_headings"],
        "simulated_record_notice": stimuli["simulated_record_notice"],
        "q1": stimuli["q1"],
        "q2_templates": templates,
        "items": items,
        "participant_materials": participant,
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
    def __init__(self, address: tuple[str, int], key: bytes):
        super().__init__(address, StudyHandler)
        self.verification_key = key
        self.sessions: dict[str, dict[str, Any]] = {}
        self.session_lock = threading.RLock()


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

    def _session(self, body: dict[str, Any]) -> dict[str, Any]:
        attempt_id = body.get("attempt_id")
        if not isinstance(attempt_id, str) or attempt_id not in self.server.sessions:
            raise ValueError("unknown attempt")
        return self.server.sessions[attempt_id]

    def _trial_payload(self, session: dict[str, Any]) -> dict[str, Any]:
        index = session["index"]
        slot = session["plan"][index]
        item = session["items"][slot["item"]]
        session["trials"][index]["presented"] = True
        session["phase"] = "q1"
        session["phase_started"] = time.monotonic()
        return {
            "phase": "q1", "trial_index": index, "slot_index": slot["slot_index"],
            "block": slot["block"], "position": slot["position"],
            "condition": slot["condition"],
            "item": {
                "stimulus_id": item["stimulus_id"],
                "primitive_evidence": item["primitive_evidence"],
                "flat_order": item["flat_order"],
            },
        }

    def do_GET(self) -> None:
        parsed = urlsplit(self.path)
        path = unquote(parsed.path)
        if path == "/api/materials":
            self._json(participant_materials())
            return
        if path == "/api/export":
            query = parse_qs(parsed.query)
            attempt = query.get("attempt_id", [None])[0]
            output_format = query.get("format", ["json"])[0]
            with self.server.session_lock:
                session = self.server.sessions.get(attempt or "")
                if session is None or session["phase"] != "complete":
                    self._error(409, "export is not available")
                    return
                export = session["signed_export"]
            if output_format == "json":
                self._send(
                    (json.dumps(export, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
                    "application/json; charset=utf-8",
                )
            elif output_format == "csv":
                self._send(self._csv(export).encode("utf-8"), "text/csv; charset=utf-8")
            else:
                self._error(400, "unsupported export format")
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
        path = urlsplit(self.path).path
        try:
            body = self._body()
            with self.server.session_lock:
                handlers = {
                    "/api/start": self._start, "/api/practice": self._practice,
                    "/api/q1": self._q1, "/api/q2": self._q2,
                    "/api/ease": self._ease, "/api/diagnostic": self._diagnostic,
                    "/api/complete": self._complete,
                }
                handler = handlers.get(path)
                if handler is None:
                    self._error(404, "not found")
                    return
                self._json(handler(body))
        except ValueError as exc:
            self._error(409, str(exc))

    def _start(self, body: dict[str, Any]) -> dict[str, Any]:
        if set(body) != {"participant_code", "sequence"}:
            raise ValueError("invalid start fields")
        participant = body["participant_code"]
        sequence = body["sequence"]
        if not isinstance(participant, str) or not PARTICIPANT_RE.fullmatch(participant):
            raise ValueError("invalid participant code")
        if not isinstance(sequence, str):
            raise ValueError("invalid sequence")
        plan = planned_trials(sequence)
        stimuli, sequences = validated_sources()
        attempt = str(uuid.uuid4())
        items = {row["stimulus_id"]: row for row in stimuli["items"]}
        self.server.sessions[attempt] = {
            "attempt_id": attempt, "participant_code": participant,
            "sequence": sequence, "plan": plan, "items": items,
            "trials": [_empty_trial(slot, items[slot["item"]], stimuli["materials_version"])
                       for slot in plan],
            "phase": "practice_q1", "index": 0, "started": time.monotonic(),
            "phase_started": time.monotonic(), "practice_q1": False,
            "practice_q2": False, "ease": {1: None, 2: None},
            "ease_done": {1: False, 2: False}, "diagnostic_presented": False,
            "diagnostic_submitted": False, "diagnostic_response": None,
            "material_schema_version": stimuli["schema_version"],
            "sequence_schema_version": sequences["schema_version"],
        }
        return {"attempt_id": attempt, "phase": "practice_q1"}

    def _practice(self, body: dict[str, Any]) -> dict[str, Any]:
        if set(body) != {"attempt_id", "step", "answer"}:
            raise ValueError("invalid practice fields")
        session = self._session(body)
        practice = validated_sources()[0]["participant_materials"]["practice"]
        if body["step"] == "q1" and session["phase"] == "practice_q1":
            if body["answer"] not in {row["key"] for row in validated_sources()[0]["q1"]["options"]}:
                raise ValueError("invalid practice Q1")
            session["practice_q1"] = True
            session["phase"] = "practice_q2"
            return {"phase": "practice_q2"}
        if body["step"] == "q2" and session["phase"] == "practice_q2":
            if body["answer"] not in {row["key"] for row in practice["q2"]["options"]}:
                raise ValueError("invalid practice Q2")
            session["practice_q2"] = True
            payload = self._trial_payload(session)
            payload["feedback"] = practice["feedback"]
            return payload
        raise ValueError("invalid practice transition")

    def _q1(self, body: dict[str, Any]) -> dict[str, Any]:
        if set(body) != {"attempt_id", "answer"}:
            raise ValueError("invalid Q1 fields")
        session = self._session(body)
        if session["phase"] != "q1":
            raise ValueError("Q1 is not available")
        answer = body["answer"]
        stimuli, _ = validated_sources()
        if answer not in {row["key"] for row in stimuli["q1"]["options"]}:
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
        template = next(row for row in stimuli["q2_templates"]
                        if row["template_id"] == slot["q2_template_id"])
        return {"phase": "q2", "q2": {"text": template["text"], "options": template["options"]}}

    def _q2(self, body: dict[str, Any]) -> dict[str, Any]:
        if set(body) != {"attempt_id", "answer", "hidden_ms"}:
            raise ValueError("invalid Q2 fields")
        session = self._session(body)
        if session["phase"] != "q2":
            raise ValueError("Q2 is not available")
        hidden_ms = body["hidden_ms"]
        if type(hidden_ms) is not int or hidden_ms < 0:
            raise ValueError("invalid hidden duration")
        index = session["index"]
        trial = session["trials"][index]
        slot = session["plan"][index]
        template = next(row for row in validated_sources()[0]["q2_templates"]
                        if row["template_id"] == slot["q2_template_id"])
        answer = body["answer"]
        if answer not in {row["key"] for row in template["options"]}:
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

    def _ease(self, body: dict[str, Any]) -> dict[str, Any]:
        if set(body) != {"attempt_id", "block", "answer"}:
            raise ValueError("invalid ease fields")
        session = self._session(body)
        block = body["block"]
        if type(block) is not int or block not in (1, 2) or session["phase"] != f"ease_{block}":
            raise ValueError("invalid ease transition")
        keys = {row["key"] for row in
                validated_sources()[0]["participant_materials"]["block_ease"]["options"]}
        if body["answer"] is not None and body["answer"] not in keys:
            raise ValueError("invalid ease answer")
        session["ease"][block] = body["answer"]
        session["ease_done"][block] = True
        if block == 1:
            return self._trial_payload(session)
        session["phase"] = "diagnostic"
        session["diagnostic_presented"] = True
        return {"phase": "diagnostic"}

    def _diagnostic(self, body: dict[str, Any]) -> dict[str, Any]:
        if set(body) != {"attempt_id", "answer"}:
            raise ValueError("invalid diagnostic fields")
        session = self._session(body)
        if session["phase"] != "diagnostic":
            raise ValueError("invalid diagnostic transition")
        diagnostic = validated_sources()[0]["participant_materials"]["post_task_manipulation_diagnostic"]
        if body["answer"] is not None and body["answer"] not in {
            row["key"] for row in diagnostic["options"]
        }:
            raise ValueError("invalid diagnostic answer")
        session["diagnostic_submitted"] = body["answer"] is not None
        session["diagnostic_response"] = body["answer"]
        session["phase"] = "ready_complete"
        return {"phase": "ready_complete"}

    def _complete(self, body: dict[str, Any]) -> dict[str, Any]:
        if set(body) != {"attempt_id"}:
            raise ValueError("invalid complete fields")
        session = self._session(body)
        if session["phase"] != "ready_complete" or session["index"] != 10:
            raise ValueError("attempt cannot be completed")
        export = self._canonical_export(session)
        session["signed_export"] = sign_export(export, self.server.verification_key)
        session["phase"] = "complete"
        return {"phase": "complete", "attempt_id": session["attempt_id"]}

    def _canonical_export(self, session: dict[str, Any]) -> dict[str, Any]:
        diagnostic = validated_sources()[0]["participant_materials"]["post_task_manipulation_diagnostic"]
        response = session["diagnostic_response"]
        return {
            "export_schema_version": "microstudy-export-v2-signed",
            "material_schema_version": session["material_schema_version"],
            "sequence_schema_version": session["sequence_schema_version"],
            "material_hashes": material_hashes(),
            "attempt_id": session["attempt_id"],
            "participant_code": session["participant_code"],
            "sequence": session["sequence"], "completion_status": "complete",
            "practice_presented": True, "practice_q1_submitted": session["practice_q1"],
            "practice_q2_submitted": session["practice_q2"], "practice_complete": True,
            "post_task_diagnostic_presented": session["diagnostic_presented"],
            "post_task_diagnostic_submitted": session["diagnostic_submitted"],
            "post_task_diagnostic_response": response,
            "post_task_diagnostic_correct": (
                None if response is None else response == diagnostic["correct_key"]
            ),
            "block_1_ease": session["ease"][1], "block_2_ease": session["ease"][2],
            "mechanical_exclusion": False, "mechanical_exclusion_reason": "none",
            "trials": session["trials"],
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
) -> StudyServer:
    try:
        address = ipaddress.ip_address(host)
    except ValueError as exc:
        raise ValueError("host must be a loopback IP address") from exc
    if not address.is_loopback:
        raise ValueError("refusing non-loopback host")
    key = load_or_create_key(verification_key_file or DEFAULT_KEY_FILE)
    return StudyServer((host, port), key)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the local-only micro-study preview.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--verification-key-file", type=Path, default=DEFAULT_KEY_FILE)
    parser.add_argument("--open", action="store_true", dest="open_browser")
    args = parser.parse_args(argv)
    server = create_server(args.host, args.port, args.verification_key_file)
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
