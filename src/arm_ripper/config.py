"""Application configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class AppConfig:
    """Runtime configuration for the ripper service."""

    host: str = os.environ.get("ARM_RIPPER_HOST", "0.0.0.0")
    port: int = int(os.environ.get("ARM_RIPPER_PORT", "9090"))
    music_dir: Path = Path(os.environ.get("ARM_RIPPER_MUSIC_DIR", "./music")).resolve()
    state_file: Path = Path(os.environ.get("ARM_RIPPER_STATE_FILE", "./state.json")).resolve()
    static_dir: Path = Path(os.environ.get("ARM_RIPPER_STATIC_DIR", "./static")).resolve()
    auto_rip: bool = os.environ.get("ARM_RIPPER_AUTO_RIP", "0") == "1"
    mp3_bitrate: str = os.environ.get("ARM_RIPPER_MP3_BITRATE", "320k")
