from pathlib import Path
from uuid import uuid4

from pc_app.scope_app.core.app_settings import AppSettings, AppSettingsStore


def test_settings_missing_file_returns_defaults():
    path = _settings_path("missing")
    store = AppSettingsStore(path)
    settings = store.load()
    assert settings.source == "fake://sine"
    assert settings.show_safety_on_start is True


def test_settings_corrupt_file_does_not_crash():
    path = _settings_path("corrupt")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{bad json", encoding="utf-8")
    settings = AppSettingsStore(path).load()
    assert settings.baud == 115200


def test_settings_round_trip():
    path = _settings_path("round_trip")
    store = AppSettingsStore(path)
    store.save(AppSettings(source="COM14", show_safety_on_start=False))
    settings = store.load()
    assert settings.source == "COM14"
    assert settings.show_safety_on_start is False


def _settings_path(name: str) -> Path:
    root = Path.cwd() / "test_settings_tmp" / name / uuid4().hex
    root.mkdir(parents=True, exist_ok=True)
    return root / "settings.json"
