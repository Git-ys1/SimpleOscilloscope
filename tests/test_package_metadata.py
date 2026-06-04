from __future__ import annotations

import tomllib
from pathlib import Path

from pc_app.scope_app import __version__
from pc_app.scope_app.version import APP_ID, APP_NAME, APP_VERSION


def test_version_module_is_package_version_source():
    assert APP_NAME == "SimpleScope PC"
    assert APP_ID == "SimpleScopePC"
    assert APP_VERSION == "0.9.5"
    assert __version__ == APP_VERSION


def test_root_pyproject_exposes_gui_entry_point():
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))

    assert data["project"]["name"] == "simplescope-pc"
    assert data["project"]["dynamic"] == ["version"]
    assert data["project"]["gui-scripts"]["simplescope-pc"] == "scope_app.main:main"
    assert data["tool"]["setuptools"]["dynamic"]["version"] == {"attr": "scope_app.version.APP_VERSION"}
