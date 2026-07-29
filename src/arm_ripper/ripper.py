"""Background CD ripping worker for Linux/Raspberry Pi."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
import subprocess
import threading
import uuid
from typing import Any

from .config import AppConfig
from .state import StateStore

_SAFE_NAME = re.compile(r"[^A-Za-z0-9._ -]+")


def safe_name(value: str) -> str:
    cleaned = _SAFE_NAME.sub("_", value).strip(" ._")
    return cleaned or "Unbekannt"


class RipManager:
    """Starts one ripping job per drive and publishes status updates."""

    def __init__(self, config: AppConfig, state: StateStore) -> None:
        self.config = config
        self.state = state
        self._running: dict[str, threading.Thread] = {}
        self._lock = threading.Lock()

    def start(self, drive: dict[str, Any]) -> dict[str, Any]:
        drive_id = drive["id"]
        with self._lock:
            existing = self._running.get(drive_id)
            if existing and existing.is_alive():
                raise RuntimeError(f"Laufwerk {drive_id} rippt bereits")
            job = {
                "id": uuid.uuid4().hex,
                "drive_id": drive_id,
                "device": drive["device"],
                "status": "wartet",
                "progress": 0,
                "current_track": None,
                "started_at": datetime.now(timezone.utc).isoformat(),
            }
            thread = threading.Thread(target=self._run_job, args=(job,), daemon=True)
            self._running[drive_id] = thread
            self.state.add_job(job)
            self.state.update_drive(drive_id, status="wartet", current_job=job["id"])
            self.state.save()
            thread.start()
            return job

    def _run_job(self, job: dict[str, Any]) -> None:
        device = job["device"]
        drive_id = job["drive_id"]
        output_dir = self.config.music_dir / f"rip-{job['id']}"
        output_dir.mkdir(parents=True, exist_ok=True)
        try:
            self._update(job, status="rippt", progress=5, current_track="CD wird gelesen")
            command = [
                "abcde",
                "-d",
                device,
                "-o",
                f"mp3:-b {self.config.mp3_bitrate}",
                "-N",
                "-x",
            ]
            result = subprocess.run(
                command,
                cwd=output_dir,
                check=True,
                text=True,
                capture_output=True,
            )
            self._update(job, status="fertig", progress=100, current_track=None, log=result.stdout[-4000:])
            self.state.add_library_album({"job_id": job["id"], "path": str(output_dir), "created_at": datetime.now(timezone.utc).isoformat()})
            self.state.update_drive(drive_id, status="fertig", current_job=None)
            subprocess.run(["eject", device], check=False, text=True, capture_output=True)
        except FileNotFoundError as exc:
            self._fail(job, f"Benötigtes Linux-Programm fehlt: {exc.filename}")
        except subprocess.CalledProcessError as exc:
            message = (exc.stderr or exc.stdout or str(exc))[-4000:]
            self._fail(job, message)
        finally:
            self.state.save()

    def _update(self, job: dict[str, Any], **fields: Any) -> None:
        job.update(fields)
        self.state.update_job(job["id"], **fields)
        self.state.update_drive(job["drive_id"], status=job.get("status"), progress=job.get("progress"), current_track=job.get("current_track"))
        self.state.save()

    def _fail(self, job: dict[str, Any], error: str) -> None:
        self._update(job, status="fehler", error=error, progress=job.get("progress", 0))
        self.state.update_drive(job["drive_id"], status="fehler", error=error, current_job=None)
