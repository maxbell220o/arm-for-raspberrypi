"""Small stdlib HTTP server for the Raspberry Pi ripper UI."""

from __future__ import annotations

from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import unquote

from .config import AppConfig
from .drives import discover_drives, run_eject
from .ripper import RipManager
from .state import StateStore


class RipperRequestHandler(SimpleHTTPRequestHandler):
    """Serves static files and JSON API endpoints."""

    config: AppConfig
    state: StateStore
    ripper: RipManager

    def __init__(self, *args, directory: str | None = None, **kwargs) -> None:
        super().__init__(*args, directory=directory or str(self.config.static_dir), **kwargs)

    def do_GET(self) -> None:
        if self.path == "/api/status":
            self._refresh_drives()
            self._json(self.state.snapshot())
            return
        if self.path == "/api/drives":
            self._refresh_drives()
            self._json(list(self.state.snapshot().get("drives", {}).values()))
            return
        if self.path == "/api/jobs":
            self._json(self.state.snapshot().get("jobs", []))
            return
        if self.path == "/api/library":
            self._json(self.state.snapshot().get("library", []))
            return
        super().do_GET()

    def do_POST(self) -> None:
        parts = [unquote(part) for part in self.path.split("/") if part]
        if len(parts) == 4 and parts[:2] == ["api", "drives"]:
            drive_id, action = parts[2], parts[3]
            self._refresh_drives()
            drives = self.state.snapshot().get("drives", {})
            drive = drives.get(drive_id)
            if not drive:
                self._json({"error": "Laufwerk nicht gefunden"}, HTTPStatus.NOT_FOUND)
                return
            try:
                if action == "open":
                    run_eject(drive["device"], close=False)
                    self.state.update_drive(drive_id, status="geöffnet")
                    self.state.save()
                    self._json({"ok": True})
                    return
                if action == "close":
                    run_eject(drive["device"], close=True)
                    self.state.update_drive(drive_id, status="geschlossen")
                    self.state.save()
                    self._json({"ok": True})
                    return
                if action == "rip":
                    self._json(self.ripper.start(drive), HTTPStatus.ACCEPTED)
                    return
            except Exception as exc:  # noqa: BLE001 - surface command/job errors to the UI
                self._json({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)
                return
        self._json({"error": "Unbekannter Endpunkt"}, HTTPStatus.NOT_FOUND)

    def _refresh_drives(self) -> None:
        self.state.set_drives(discover_drives())
        self.state.save()

    def _json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def create_server(config: AppConfig) -> ThreadingHTTPServer:
    config.music_dir.mkdir(parents=True, exist_ok=True)
    config.static_dir.mkdir(parents=True, exist_ok=True)
    state = StateStore(config.state_file)
    ripper = RipManager(config, state)
    RipperRequestHandler.config = config
    RipperRequestHandler.state = state
    RipperRequestHandler.ripper = ripper
    return ThreadingHTTPServer((config.host, config.port), RipperRequestHandler)


def main() -> None:
    config = AppConfig()
    server = create_server(config)
    print(f"Web-UI läuft auf http://{config.host}:{config.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
