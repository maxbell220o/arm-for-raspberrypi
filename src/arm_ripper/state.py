"""Thread-safe in-memory state with JSON persistence."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json
import threading
from typing import Any


class StateStore:
    """Stores drive and job status for the web UI."""

    def __init__(self, state_file: Path) -> None:
        self._state_file = state_file
        self._lock = threading.Lock()
        self._state: dict[str, Any] = {"drives": {}, "jobs": [], "library": []}
        self.load()

    def load(self) -> None:
        if not self._state_file.exists():
            return
        with self._state_file.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)
        if isinstance(loaded, dict):
            with self._lock:
                self._state.update(loaded)

    def save(self) -> None:
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        tmp_file = self._state_file.with_suffix(".tmp")
        with tmp_file.open("w", encoding="utf-8") as handle:
            json.dump(self.snapshot(), handle, indent=2, ensure_ascii=False)
        tmp_file.replace(self._state_file)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return deepcopy(self._state)

    def set_drives(self, drives: list[dict[str, Any]]) -> None:
        with self._lock:
            previous = self._state.setdefault("drives", {})
            self._state["drives"] = {
                drive["id"]: {**previous.get(drive["id"], {}), **drive}
                for drive in drives
            }

    def update_drive(self, drive_id: str, **fields: Any) -> None:
        with self._lock:
            self._state.setdefault("drives", {}).setdefault(drive_id, {}).update(fields)

    def add_job(self, job: dict[str, Any]) -> None:
        with self._lock:
            self._state.setdefault("jobs", []).insert(0, job)

    def update_job(self, job_id: str, **fields: Any) -> None:
        with self._lock:
            for job in self._state.setdefault("jobs", []):
                if job.get("id") == job_id:
                    job.update(fields)
                    break

    def add_library_album(self, album: dict[str, Any]) -> None:
        with self._lock:
            self._state.setdefault("library", []).insert(0, album)
