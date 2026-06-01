from __future__ import annotations

from typing import Protocol


class Transport(Protocol):
    name: str

    def readline(self) -> bytes:
        ...

    def write(self, data: bytes) -> None:
        ...

    def close(self) -> None:
        ...
