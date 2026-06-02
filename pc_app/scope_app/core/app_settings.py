from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any

from ..app_paths import app_data_dir


@dataclass
class AppSettings:
    source: str = "fake://sine"
    baud: int = 115200
    time_per_div_s: float = 0.1
    volt_per_div_mv: float = 500.0
    trigger_mode: str = "Auto"
    trigger_level_mv: float = 1650.0
    window_width: int = 1360
    window_height: int = 820
    show_safety_on_start: bool = True
    theme: str = "Dark"
    csv_export_path: str = ""


class AppSettingsStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_settings_path()

    def load(self) -> AppSettings:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                return AppSettings()
            defaults = AppSettings()
            values: dict[str, Any] = {}
            for field in fields(AppSettings):
                values[field.name] = raw.get(field.name, getattr(defaults, field.name))
            return AppSettings(**values)
        except (OSError, ValueError, TypeError):
            return AppSettings()

    def save(self, settings: AppSettings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(asdict(settings), ensure_ascii=False, indent=2), encoding="utf-8")


def default_settings_path() -> Path:
    return app_data_dir() / "settings.json"
