from __future__ import annotations

import os
import sys
from pathlib import Path

from .version import APP_ID


def app_data_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    base = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
    return base / APP_ID


def logs_dir() -> Path:
    path = app_data_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def runtime_root() -> Path:
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        return Path(bundle_root)
    return Path(__file__).resolve().parents[2]


def asset_path(*parts: str) -> Path:
    return runtime_root() / "packaging" / "assets" / Path(*parts)
