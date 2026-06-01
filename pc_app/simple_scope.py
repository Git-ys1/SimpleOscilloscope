#!/usr/bin/env python3
"""Compatibility launcher for the modular SimpleScope PC application."""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from scope_app.main import main as qt_main

    return qt_main(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
