from __future__ import annotations

from dataclasses import replace

from ..core.models import ErrorFrame, SampleBlock
from .ascii_protocol import AsciiProtocol
from .binary_protocol import BinaryProtocol


class ProtocolStreamDecoder:
    """Decode mixed ASCII control lines and binary DATA frames from one byte stream."""

    MAX_BUFFER = 8192

    def __init__(self) -> None:
        self._ascii = AsciiProtocol()
        self._binary = BinaryProtocol()
        self._buffer = bytearray()

    def feed(self, data: bytes) -> list[object]:
        if not data:
            return []
        self._buffer.extend(data)
        events: list[object] = []

        while self._buffer:
            if self._buffer.startswith(self._binary.SYNC):
                event = self._try_decode_binary()
                if event is None:
                    break
                events.append(event)
                continue

            newline_index = self._buffer.find(b"\n")
            sync_index = self._buffer.find(self._binary.SYNC)
            if newline_index >= 0 and (sync_index < 0 or newline_index < sync_index):
                line_bytes = bytes(self._buffer[: newline_index + 1])
                del self._buffer[: newline_index + 1]
                event = self._ascii.parse_line(line_bytes.decode("ascii", errors="replace"))
                if event is not None:
                    events.append(event)
                continue

            if sync_index > 0:
                del self._buffer[:sync_index]
                continue

            if len(self._buffer) > self.MAX_BUFFER:
                self._buffer.clear()
                events.append(ErrorFrame("stream_buffer_overflow"))
            break

        return events

    def _try_decode_binary(self) -> object | None:
        try:
            expected = self._binary.expected_length(bytes(self._buffer))
        except ValueError as exc:
            del self._buffer[0]
            return ErrorFrame(f"binary:{exc}")

        if expected is None or len(self._buffer) < expected:
            return None

        frame = bytes(self._buffer[:expected])
        del self._buffer[:expected]
        try:
            block = self._binary.parse_frame(frame)
        except ValueError as exc:
            return ErrorFrame(f"binary:{exc}")

        return self._with_synthetic_time(block)

    @staticmethod
    def _with_synthetic_time(block: SampleBlock) -> SampleBlock:
        if block.sample_rate_hz <= 0:
            return block
        start_time_ms = max(0.0, (float(block.sequence) - 1.0) * 1000.0 / float(block.sample_rate_hz))
        return replace(block, start_time_ms=start_time_ms)
