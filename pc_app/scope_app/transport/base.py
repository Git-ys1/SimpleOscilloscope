from __future__ import annotations

from typing import Protocol


class Transport(Protocol):
    name: str

    def read(self, size: int = 512) -> bytes:
        ...

    def readline(self) -> bytes:
        ...

    def write(self, data: bytes) -> None:
        ...

    def close(self) -> None:
        ...
