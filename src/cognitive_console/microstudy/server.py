"""Minimal loopback-only static server."""

from __future__ import annotations

import argparse
import ipaddress
import json
import mimetypes
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

from .materials import material_hashes, planned_trials, validated_sources

STATIC_DIR = Path(__file__).with_name("static")
CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
    "connect-src 'self'; font-src 'none'; object-src 'none'; base-uri 'none'; "
    "form-action 'none'; frame-ancestors 'none'"
)


class StudyHandler(BaseHTTPRequestHandler):
    server_version = "MicrostudyLocal"
    sys_version = ""

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send(self, body: bytes, content_type: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Content-Security-Policy", CSP)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = unquote(urlsplit(self.path).path)
        if path == "/api/materials":
            stimuli, sequences = validated_sources()
            body = json.dumps(
                {
                    "stimuli": stimuli,
                    "sequences": sequences,
                    "material_hashes": material_hashes(),
                },
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode()
            self._send(body, "application/json; charset=utf-8")
            return
        if path.startswith("/api/sequence/"):
            code = path.rsplit("/", 1)[-1]
            try:
                rows = planned_trials(code)
            except ValueError:
                self.send_error(404)
                return
            self._send(
                json.dumps(rows, separators=(",", ":")).encode(),
                "application/json; charset=utf-8",
            )
            return
        relative = "index.html" if path in {"", "/"} else path.lstrip("/")
        candidate = (STATIC_DIR / relative).resolve()
        try:
            candidate.relative_to(STATIC_DIR.resolve())
        except ValueError:
            self.send_error(404)
            return
        if not candidate.is_file():
            self.send_error(404)
            return
        mime = (
            "application/javascript"
            if candidate.suffix in {".js", ".mjs"}
            else mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        )
        if mime.startswith("text/") or mime in {"application/javascript"}:
            mime += "; charset=utf-8"
        self._send(candidate.read_bytes(), mime)


def create_server(host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    try:
        address = ipaddress.ip_address(host)
    except ValueError as exc:
        raise ValueError("host must be a loopback IP address") from exc
    if not address.is_loopback:
        raise ValueError("refusing non-loopback host")
    return ThreadingHTTPServer((host, port), StudyHandler)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the local-only micro-study preview.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open", action="store_true", dest="open_browser")
    args = parser.parse_args(argv)
    server = create_server(args.host, args.port)
    url = f"http://{args.host}:{server.server_port}/"
    print(f"Local study preview: {url}")
    if args.open_browser:
        threading.Timer(0.2, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0
