"""Linux optical-drive detection and tray control."""

from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any


SYS_BLOCK = Path("/sys/block")


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return None


def discover_drives() -> list[dict[str, Any]]:
    """Discover Linux optical drives, usually exposed as /dev/sr*."""

    drives: list[dict[str, Any]] = []
    for block_device in sorted(SYS_BLOCK.glob("sr*")):
        device = f"/dev/{block_device.name}"
        vendor = _read_text(block_device / "device/vendor") or "Unbekannt"
        model = _read_text(block_device / "device/model") or block_device.name
        removable = _read_text(block_device / "removable") == "1"
        status = "bereit" if Path(device).exists() else "nicht verfügbar"
        drives.append(
            {
                "id": block_device.name,
                "device": device,
                "vendor": vendor,
                "model": model,
                "removable": removable,
                "status": status,
            }
        )
    return drives


def run_eject(device: str, close: bool = False) -> subprocess.CompletedProcess[str]:
    """Open or close a drive tray with the Linux eject command."""

    command = ["eject", "-t", device] if close else ["eject", device]
    return subprocess.run(command, check=True, text=True, capture_output=True)
