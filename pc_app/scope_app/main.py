from __future__ import annotations

import argparse
import logging
import sys

from PySide6 import QtGui, QtWidgets

from .app_paths import asset_path, logs_dir
from .ui.main_window import MainWindow
from .version import APP_NAME, APP_ORG


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SimpleScope PC oscilloscope")
    parser.add_argument("--source", default="", help="COM port, tcp://host:port, or fake://sine")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--connect", action="store_true", help="Connect immediately after the UI starts")
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    args = build_parser().parse_args(argv)
    app = QtWidgets.QApplication(sys.argv[:1])
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_ORG)
    icon = QtGui.QIcon(str(asset_path("SimpleScopePC.ico")))
    if not icon.isNull():
        app.setWindowIcon(icon)

    window = MainWindow(default_source=args.source, default_baud=args.baud)
    if not icon.isNull():
        window.setWindowIcon(icon)
    window.resize(1360, 800)
    window.show()
    if args.connect:
        window.connect_to_source()
    return app.exec()


def configure_logging() -> None:
    try:
        logging.basicConfig(
            filename=str(logs_dir() / "simplescope-pc.log"),
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
    except OSError:
        logging.basicConfig(level=logging.INFO)

    def excepthook(exc_type, exc_value, exc_traceback):
        logging.exception("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    sys.excepthook = excepthook
