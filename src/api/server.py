from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from src.api.service import ApiService
from src.ui.pages import render_event_page, render_home_page, render_settlement_page


class ApiRequestHandler(BaseHTTPRequestHandler):
    api_service: ApiService

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)

        if parsed.path == "/":
            html = render_home_page(self.api_service.health(), self.api_service.events_active())
            self._respond_html(html)
            return
        if parsed.path == "/health":
            self._respond_json(self.api_service.health())
            return
        if parsed.path == "/events/active":
            self._respond_json(self.api_service.events_active())
            return
        if parsed.path == "/events/history":
            self._respond_json(self.api_service.events_history())
            return
        if parsed.path.startswith("/events/"):
            event_id = int(parsed.path.split("/")[-1])
            self._respond_json(self.api_service.event_detail(event_id))
            return
        if parsed.path == "/settlements/search":
            self._respond_json(self.api_service.settlements_search(query.get("q", [""])[0]))
            return
        if parsed.path == "/probability/current":
            settlement = query.get("settlement", [""])[0]
            payload = self.api_service.probability_current(settlement)
            if query.get("format", ["json"])[0] == "html" and payload:
                self._respond_html(render_settlement_page(payload))
                return
            self._respond_json(payload)
            return
        if parsed.path == "/probability/history":
            self._respond_json(self.api_service.probability_history(query.get("settlement", [""])[0]))
            return
        if parsed.path == "/debug/raw-events":
            self._respond_json(self.api_service.debug_raw_events())
            return
        if parsed.path == "/debug/normalized-events":
            self._respond_json(self.api_service.debug_normalized_events())
            return
        self.send_error(404)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _respond_json(self, payload: object) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _respond_html(self, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_api_server(api_service: ApiService, host: str = "127.0.0.1", port: int = 8000) -> HTTPServer:
    handler = type("ConfiguredApiRequestHandler", (ApiRequestHandler,), {"api_service": api_service})
    server = HTTPServer((host, port), handler)
    return server
