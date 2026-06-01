from __future__ import annotations

import struct
from dataclasses import dataclass

import numpy as np

from ..core.models import SampleBlock


@dataclass(frozen=True)
class BinaryFrameHeader:
    version: int
    frame_type: int
    sequence: int
    sample_rate_hz: int
    channel_count: int
    point_count: int


class BinaryProtocol:
    """Parser for the planned high-speed one-frame-many-points waveform protocol."""

    SYNC = b"\xA5\x5A"
    TYPE_DATA = 0x01
    HEADER_STRUCT = struct.Struct("<2sBBIIBH")
    CRC_STRUCT = struct.Struct("<H")

    def expected_length(self, data: bytes) -> int | None:
        if len(data) < self.HEADER_STRUCT.size:
            return None
        header = self._parse_header(data[: self.HEADER_STRUCT.size])
        payload_len = header.channel_count * header.point_count * 2
        return self.HEADER_STRUCT.size + payload_len + self.CRC_STRUCT.size

    def parse_frame(self, data: bytes, start_time_ms: float = 0.0) -> SampleBlock:
        expected = self.expected_length(data)
        if expected is None or len(data) < expected:
            raise ValueError("incomplete binary frame")
        frame = data[:expected]
        stored_crc = self.CRC_STRUCT.unpack(frame[-2:])[0]
        computed_crc = crc16_ccitt(frame[:-2])
        if stored_crc != computed_crc:
            raise ValueError(f"crc mismatch: stored=0x{stored_crc:04X} computed=0x{computed_crc:04X}")

        header = self._parse_header(frame[: self.HEADER_STRUCT.size])
        if header.frame_type != self.TYPE_DATA:
            raise ValueError(f"unsupported frame type {header.frame_type}")
        payload = frame[self.HEADER_STRUCT.size : -2]
        raw = np.frombuffer(payload, dtype="<u2").astype(np.float64)
        raw = raw.reshape((header.channel_count, header.point_count))
        values_mv = raw * (3300.0 / 4095.0)
        return SampleBlock(
            sequence=header.sequence,
            start_time_ms=start_time_ms,
            sample_rate_hz=header.sample_rate_hz,
            channel_count=header.channel_count,
            values_mv=values_mv,
        )

    def build_data_frame(
        self,
        sequence: int,
        sample_rate_hz: int,
        values_adc: np.ndarray,
        version: int = 1,
    ) -> bytes:
        values = np.asarray(values_adc, dtype=np.uint16)
        if values.ndim == 1:
            values = values.reshape((1, values.size))
        channel_count, point_count = values.shape
        header = self.HEADER_STRUCT.pack(
            self.SYNC,
            version,
            self.TYPE_DATA,
            sequence,
            sample_rate_hz,
            channel_count,
            point_count,
        )
        payload = values.astype("<u2", copy=False).tobytes()
        crc = self.CRC_STRUCT.pack(crc16_ccitt(header + payload))
        return header + payload + crc

    def _parse_header(self, data: bytes) -> BinaryFrameHeader:
        sync, version, frame_type, sequence, sample_rate_hz, channel_count, point_count = self.HEADER_STRUCT.unpack(data)
        if sync != self.SYNC:
            raise ValueError("bad binary sync")
        if version == 0:
            raise ValueError("bad binary version")
        if channel_count == 0 or point_count == 0:
            raise ValueError("empty binary frame")
        return BinaryFrameHeader(version, frame_type, sequence, sample_rate_hz, channel_count, point_count)


def crc16_ccitt(data: bytes, initial: int = 0xFFFF) -> int:
    crc = initial
    for byte in data:
        crc ^= byte << 8
        for _bit in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc
