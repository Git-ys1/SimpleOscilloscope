from __future__ import annotations

from typing import Protocol


class ProtocolParser(Protocol):
    def parse_line(self, line: str) -> object | None:
        ...
