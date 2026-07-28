from __future__ import annotations

import argparse
import json
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Tuple

from .data_loader import build_console_payload, build_demo_report


def _render_html() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Reality-check Console v2</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 0; background: #0f1220; color: #e9ecf7; }
    .wrap { max-width: 1100px; margin: 0 auto; padding: 24px; }
    .panel { background: #171b2f; border: 1px solid #2e3558; border-radius: 12px; padding: 16px; margin-bottom: 16px; }
    h1, h2, h3 { margin-top: 0; }
    table { width: 100%; border-collapse: collapse; margin-top: 8px; }
    th, td { border-bottom: 1px solid #2e3558; padding: 8px; text-align: left; }
    .muted { color: #aab2d5; font-size: 13px; }
    .ok { color: #79e07d; font-weight: 700; }
    .fail { color: #ffbd66; font-weight: 700; }
    .warn { color: #ff6b6b; font-weight: 700; }
    .badge { display: inline-block; margin-left: 8px; padding: 2px 8px; border-radius: 999px; font-size: 12px; border: 1px solid #445083; color: #c7d0fa; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 10px; }
    .card { border-radius: 10px; padding: 12px; border: 1px solid #2e3558; background: #13172a; }
    .card.red { border-color: #a33; background: #2a1616; }
    .card.amber { border-color: #8f6d2d; background: #2a2516; }
    .mini { font-size: 12px; color: #aab2d5; }
    .signal { margin: 6px 0; padding-top: 6px; border-top: 1px solid #2e3558; }
    .headline { font-weight: 800; color: #ffffff; margin-bottom: 8px; }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Dual-channel Cognitive Console v2</h1>
    <div class="muted" id="positioning"></div>
    <div class="panel">
      <h2>0) UI contract: latent-control affordance cards</h2>
      <div class="muted">Each card exposes five artifact-derived signals: READ, TRANSFER, PROMPT-CEILING, CALIBRATION-HARM, EVIDENCE-TIER.</div>
      <div class="grid" id="ui-contract-grid"></div>
    </div>
    <div class="panel">
      <h2>1) Dual-channel comparison (Prompt vs Latent)</h2>
      <div class="muted">Boundary instrument: compare behavior outcomes instead of assuming latent superiority.</div>
      <table id="channels-table">
        <thead><tr><th>Axis</th><th>Prompt mean</th><th>Latent mean</th><th>Δ(steer-prompt)</th></tr></thead>
        <tbody></tbody>
      </table>
    </div>
    <div class="panel">
      <h2>2) C1 legibility gap ratio + CI<span class="badge" id="c1-source"></span></h2>
      <table id="c1-table">
        <thead><tr><th>Axis</th><th>Prompt reach</th><th>Pole reach</th><th>Ratio</th><th>CI</th><th>Facade CI&lt;1</th></tr></thead>
        <tbody></tbody>
      </table>
    </div>
    <div class="panel">
      <h2>3) C2 transfer check: Δ(steer−prompt) + Bonferroni CI<span class="badge" id="c2-source"></span></h2>
      <div class="muted">Uncertainty boundary warning appears in red when latent control degrades calibration.</div>
      <table id="c2-table">
        <thead><tr><th>Axis</th><th>Δ(steer-prompt)</th><th>CI</th><th>Pass/Fail</th></tr></thead>
        <tbody></tbody>
      </table>
    </div>
    <div class="panel">
      <h2>4) Trust-calibration panel: when not to trust latent control</h2>
      <div class="grid" id="trust-grid"></div>
    </div>
    <div class="panel">
      <h2>5) Simulated demo: automatic failure-signature localization</h2>
      <div class="muted">No human labels or model calls: flags are computed from frozen artifacts.</div>
      <div class="grid" id="demo-grid"></div>
    </div>
    <div class="panel">
      <h2>E-0006 robustness arm (2×2)</h2>
      <div class="muted" id="arm-verdict"></div>
      <table id="arm-table">
        <thead><tr><th>Cell</th><th>Uncertainty Δ</th><th>CI</th><th>Robust harm?</th></tr></thead>
        <tbody></tbody>
      </table>
    </div>
    <div class="panel">
      <h2>E-0009 PSR method-strength robustness</h2>
      <div class="muted" id="psr-summary"></div>
      <table id="psr-table">
        <thead><tr><th>Axis</th><th>Δ</th><th>CI</th><th>Pass?</th></tr></thead>
        <tbody></tbody>
      </table>
    </div>
    <div class="muted" id="provenance"></div>
  </div>
  <script>
    const n = (x, digits=3) => (typeof x === "number" ? x.toFixed(digits) : "n/a");
    const yesNo = (flag) => flag ? "<span class='ok'>yes</span>" : "<span class='fail'>no</span>";
    fetch("/api/data")
      .then((resp) => resp.json())
      .then((data) => {
        document.getElementById("positioning").textContent = data.positioning;
        document.getElementById("c1-source").textContent = data.c1.source_mode;
        document.getElementById("c2-source").textContent = data.c2.source_mode;
        document.getElementById("provenance").textContent =
          `C2 source (${data.c2.source_mode}): ${data.provenance.c2b_results} | C1 source (${data.c1.source_mode}): ${data.provenance.c1_results} | arm source (${data.arm.source_mode}): ${data.provenance.arm_summary} | social: ${data.provenance.social_behavior}, ${data.provenance.social_read} | PSR: ${data.provenance.psr_results} | fallback: ${data.provenance.evidence_ledger_fallback}`;

        const cardGrid = document.getElementById("ui-contract-grid");
        data.ui_contract.cards.forEach((card) => {
          const div = document.createElement("div");
          const isRed = card.calibration_harm && card.calibration_harm.severity === "red";
          const isSocial = card.axis === "social_inference_novice_disclosure";
          div.className = isRed ? "card red" : (isSocial ? "card amber" : "card");
          div.innerHTML = `
            <h3>${card.label}</h3>
            <div class="headline">${card.headline}</div>
            <div class="signal"><b>READ</b>: ${card.read_status.status} ${card.read_status.summary || ""}</div>
            <div class="signal"><b>TRANSFER</b>: ${card.transfer_verdict.verdict} ${card.transfer_verdict.summary || ""}</div>
            <div class="signal"><b>PROMPT-CEILING</b>: ${card.prompt_ceiling.summary || "n/a"}</div>
            <div class="signal"><b>CALIBRATION-HARM</b>: ${card.calibration_harm.status} ${card.calibration_harm.summary || ""}</div>
            <div class="signal"><b>EVIDENCE-TIER</b>: ${card.evidence_tier.tier}<div class="mini">${(card.evidence_tier.notes || []).join("; ")}</div></div>
            <div class="mini">Evidence: ${(card.evidence_ids || []).join(", ")}</div>`;
          cardGrid.appendChild(div);
        });

        const chBody = document.querySelector("#channels-table tbody");
        data.c2.rows.forEach((r) => {
          const tr = document.createElement("tr");
          tr.innerHTML = `<td>${r.label}</td><td>${n(r.prompt_mean)}</td><td>${n(r.steer_mean)}</td><td>${n(r.mean_diff)}</td>`;
          chBody.appendChild(tr);
        });

        const c1Body = document.querySelector("#c1-table tbody");
        data.c1.rows.forEach((r) => {
          const tr = document.createElement("tr");
          tr.innerHTML = `<td>${r.label}</td><td>${n(r.prompt_reach)}</td><td>${n(r.pole_reach)}</td><td>${n(r.ratio)}</td><td>[${n(r.ci_lo)}, ${n(r.ci_hi)}]</td><td>${yesNo(r.holds_ci)}</td>`;
          c1Body.appendChild(tr);
        });

        const c2Body = document.querySelector("#c2-table tbody");
        data.c2.rows.forEach((r) => {
          const tr = document.createElement("tr");
          const isCritical = r.axis === "uncertainty_awareness" && (typeof r.mean_diff === "number") && r.mean_diff < 0;
          const valueClass = isCritical ? "warn" : "";
          const passTag = r.passed ? "<span class='ok'>pass</span>" : "<span class='fail'>fail</span>";
          tr.innerHTML = `<td>${r.label}</td><td class="${valueClass}">${n(r.mean_diff)}</td><td>[${n(r.ci_lo)}, ${n(r.ci_hi)}]</td><td>${passTag}</td>`;
          c2Body.appendChild(tr);
        });

        const trust = document.getElementById("trust-grid");
        data.trust_calibration.forEach((r) => {
          const div = document.createElement("div");
          const cls = r.severity === "red" ? "card red" : "card amber";
          div.className = cls;
          div.innerHTML = `<h3>${r.title}</h3><div>${r.body}</div>`;
          trust.appendChild(div);
        });

        const armBody = document.querySelector("#arm-table tbody");
        document.getElementById("arm-verdict").textContent =
          `Source=${data.arm.source_mode}; verdict=${data.arm.arm_verdict}; zero-pass cells=${data.arm.zero_pass_cells}/${data.arm.n_cells}`;
        data.arm.cells.forEach((cell) => {
          const unc = (cell.axes || []).find((r) => r.axis === "uncertainty_awareness");
          const tr = document.createElement("tr");
          const harm = unc && unc.robust_degradation_flag;
          tr.innerHTML = `<td>${cell.method} × ${cell.model_label}<div class="mini">${cell.cell_key}</div></td><td class="${harm ? "warn" : ""}">${n(unc && unc.mean_diff)}</td><td>[${n(unc && unc.ci_lo)}, ${n(unc && unc.ci_hi)}]</td><td>${yesNo(harm)}</td>`;
          armBody.appendChild(tr);
        });

        const psr = data.ui_contract.psr_method_strength;
        document.getElementById("psr-summary").textContent = `${psr.summary} verdict=${psr.verdict}; source=${psr.source_mode}`;
        const psrBody = document.querySelector("#psr-table tbody");
        psr.rows.forEach((r) => {
          const tr = document.createElement("tr");
          tr.innerHTML = `<td>${r.label}</td><td>${n(r.delta)}</td><td>[${n(r.ci_lo)}, ${n(r.ci_hi)}]</td><td>${yesNo(r.passed)}</td>`;
          psrBody.appendChild(tr);
        });

        return fetch("/api/demo");
      })
      .then((resp) => resp.json())
      .then((demo) => {
        const grid = document.getElementById("demo-grid");
        const mk = (title, items, fmt) => {
          const div = document.createElement("div");
          div.className = "card amber";
          div.innerHTML = `<h3>${title}</h3>` + items.map(fmt).join("");
          grid.appendChild(div);
        };
        mk("C1 facade-limit flags", demo.facade_limit_flags, (r) =>
          `<div>${r.label}: ratio=${n(r.ratio)} CI=[${n(r.ci_lo)}, ${n(r.ci_hi)}]</div>`);
        mk("C2 steering degradation/fail flags", demo.steering_degradation_flags, (r) =>
          `<div>${r.label}: Δ=${n(r.mean_diff)} CI=[${n(r.ci_lo)}, ${n(r.ci_hi)}], pass=${r.passed}</div>`);
        mk("2×2 uncertainty harm replication", demo.arm_uncertainty_harm_flags, (r) =>
          `<div>${r.method}×${r.model_label}: Δ=${n(r.mean_diff)} CI=[${n(r.ci_lo)}, ${n(r.ci_hi)}]</div>`);
      })
      .catch((err) => {
        document.body.innerHTML = `<pre>Failed to load console data: ${err}</pre>`;
      });
  </script>
</body>
</html>
"""


class _ConsoleHandler(BaseHTTPRequestHandler):
    def _send(self, status: HTTPStatus, body: bytes, content_type: str) -> None:
        self.send_response(status.value)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/api/data":
            payload = build_console_payload()
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self._send(HTTPStatus.OK, body, "application/json; charset=utf-8")
            return
        if self.path == "/api/demo":
            payload = build_console_payload()
            body = json.dumps(build_demo_report(payload), ensure_ascii=False).encode("utf-8")
            self._send(HTTPStatus.OK, body, "application/json; charset=utf-8")
            return
        if self.path in ("/", "/index.html"):
            html = _render_html().encode("utf-8")
            self._send(HTTPStatus.OK, html, "text/html; charset=utf-8")
            return
        self._send(HTTPStatus.NOT_FOUND, b"not found", "text/plain; charset=utf-8")

    def log_message(self, format: str, *args: object) -> None:
        return


def run_server(host: str, port: int, open_browser: bool = False) -> None:
    httpd = ThreadingHTTPServer((host, port), _ConsoleHandler)
    url = f"http://{host}:{port}"
    print(f"Console running at {url}")
    if open_browser:
        webbrowser.open(url)
    httpd.serve_forever()


def parse_args(argv: Tuple[str, ...] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run reality-check console v1.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1).")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000).")
    parser.add_argument("--open", action="store_true", help="Open the console URL in the default browser.")
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    run_server(args.host, args.port, open_browser=args.open)
