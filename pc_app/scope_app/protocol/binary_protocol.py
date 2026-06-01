from __future__ import annotations


class BinaryProtocol:
    """Reserved parser shell for the high-speed binary waveform protocol."""

    SYNC = b"\xA5\x5A"

    def parse_bytes(self, data: bytes) -> list[object]:
        raise NotImplementedError("BinaryProtocol will be implemented in v0.5.x firmware work.")
