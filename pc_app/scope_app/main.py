from __future__ import annotations

import argparse
import sys

from PySide6 import QtWidgets

from .ui.main_window import MainWindow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SimpleScope PC oscilloscope")
    parser.add_argument("--source", default="", help="COM port, tcp://host:port, or fake://sine")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--connect", action="store_true", help="Connect immediately after the UI starts")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    app = QtWidgets.QApplication(sys.argv[:1])
    app.setApplicationName("SimpleScope PC")
    app.setOrganizationName("SimpleOscilloscope")

    window = MainWindow(default_source=args.source, default_baud=args.baud)
    window.resize(1360, 800)
    window.show()
    if args.connect:
        window.connect_to_source()
    return app.exec()
