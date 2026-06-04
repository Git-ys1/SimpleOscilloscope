from __future__ import annotations

import math
import queue
import random
import time

import numpy as np

from ..protocol.binary_protocol import BinaryProtocol


class FakeTransport:
    name = "fake"
    VERSION = "0.9.2"
    RATE_MIN = 1
    RATE_MAX = 20_000
    FREQ_MIN = 1
    FREQ_MAX = 5_000
    BAUD = 921600
    BINARY_BLOCK_POINTS = 64

    def __init__(self, source: str = "fake://sine") -> None:
        wave = source.split("://", 1)[1].upper() if "://" in source else "SINE"
        self.wave = "TRI" if wave == "TRIANGLE" else wave
        if self.wave not in {"SINE", "SQUARE", "TRI", "SAW", "NOISE", "MIXED"}:
            self.wave = "SINE"
        self.frequency_hz = 1000
        self.amplitude_mv = 1200
        self.offset_mv = 1650
        self.sample_rate_hz = 10_000
        self.streaming = True
        self.sequence = 0
        self.output_format = "BINARY"
        self._binary = BinaryProtocol()
        self.started = time.monotonic()
        self._closed = False
        self._outbox: "queue.Queue[bytes]" = queue.Queue()
        self._enqueue(f"BOOT,SimpleOscilloscope,{self.VERSION},FAKE,{self.BAUD}\n".encode("ascii"))
        self._enqueue_status()

    def _enqueue(self, data: bytes) -> None:
        self._outbox.put(data)

    def _enqueue_status(self) -> None:
        state = "RUN" if self.streaming else "STOP"
        self._enqueue(
            f"STATUS,{self.wave},{self.frequency_hz},{self.amplitude_mv},{self.offset_mv},{self.sample_rate_hz},{state}\n".encode(
                "ascii"
            )
        )
        self._enqueue(f"FORMAT,{self.output_format}\n".encode("ascii"))

    def read(self, size: int = 512) -> bytes:
        if self._closed:
            return b""
        try:
            return self._outbox.get_nowait()
        except queue.Empty:
            pass

        if self.output_format == "BINARY":
            time.sleep(max(self.BINARY_BLOCK_POINTS / max(self.sample_rate_hz, 1), 0.001))
        else:
            time.sleep(max(1.0 / max(self.sample_rate_hz, 1), 0.001))
        if not self.streaming:
            return b""
        if self.output_format == "BINARY":
            return self._sample_block()
        return self._sample_line()

    def readline(self) -> bytes:
        return self.read()

    def write(self, data: bytes) -> None:
        for raw in data.decode("ascii", errors="ignore").splitlines():
            self._handle(raw.strip())

    def close(self) -> None:
        self._closed = True

    def _handle(self, command: str) -> None:
        parts = command.split()
        if command == "PING":
            self._enqueue(f"PONG,SimpleOscilloscope,{self.VERSION}\n".encode("ascii"))
        elif command == "ID?":
            self._enqueue(f"ID,SimpleOscilloscope,FAKE,{self.VERSION},FAKE,BINARY_DATA\n".encode("ascii"))
        elif command == "CAP?":
            self._enqueue(
                (
                    f"CAP,RATE_MIN={self.RATE_MIN},RATE_MAX={self.RATE_MAX},"
                    f"FREQ_MIN={self.FREQ_MIN},FREQ_MAX={self.FREQ_MAX},"
                    f"BAUD={self.BAUD},BLOCK={self.BINARY_BLOCK_POINTS}\n"
                ).encode("ascii")
            )
        elif command == "STATUS":
            self._enqueue_status()
        elif command == "START":
            self.streaming = True
            self._enqueue(b"OK,START\n")
        elif command == "STOP":
            self.streaming = False
            self._enqueue(b"OK,STOP\n")
        elif len(parts) >= 3 and parts[0] == "SET":
            self._set_value(parts[1], parts[2])
        elif command:
            self._enqueue(b"ERR,unknown_cmd\n")

    def _set_value(self, key: str, value: str) -> None:
        try:
            if key == "WAVE":
                candidate = "TRI" if value.upper() == "TRIANGLE" else value.upper()
                if candidate not in {"SINE", "SQUARE", "TRI", "SAW", "NOISE", "MIXED"}:
                    raise ValueError
                self.wave = candidate
            elif key == "FREQ":
                self.frequency_hz = max(self.FREQ_MIN, min(self.FREQ_MAX, int(value)))
            elif key == "AMP":
                self.amplitude_mv = max(0, min(3300, int(value)))
            elif key == "OFFSET":
                self.offset_mv = max(0, min(3300, int(value)))
            elif key == "RATE":
                self.sample_rate_hz = max(self.RATE_MIN, min(self.RATE_MAX, int(value)))
            elif key == "FORMAT":
                candidate = value.upper()
                if candidate not in {"ASCII", "BINARY"}:
                    raise ValueError
                self.output_format = candidate
            else:
                raise ValueError
        except ValueError:
            self._enqueue(b"ERR,bad_set\n")
            return
        self._enqueue(f"OK,{key}\n".encode("ascii"))
        if key == "FORMAT":
            self._enqueue_status()

    def _sample_line(self) -> bytes:
        elapsed = time.monotonic() - self.started
        phase = (elapsed * self.frequency_hz) % 1.0
        value = self._value(phase)
        self.sequence += 1
        return (
            f"OSC,{self.sequence},{int(elapsed * 1000)},{value},{self.wave},"
            f"{self.frequency_hz},{self.amplitude_mv},{self.offset_mv}\n"
        ).encode("ascii")

    def _sample_block(self) -> bytes:
        start_sequence = self.sequence + 1
        now = time.monotonic()
        values = []
        for index in range(self.BINARY_BLOCK_POINTS):
            elapsed = (now - self.started) + (index / max(self.sample_rate_hz, 1))
            phase = (elapsed * self.frequency_hz) % 1.0
            value_mv = self._value(phase)
            values.append(int(value_mv * 4095 / 3300))
        self.sequence += self.BINARY_BLOCK_POINTS
        return self._binary.build_data_frame(
            sequence=start_sequence,
            sample_rate_hz=self.sample_rate_hz,
            values_adc=np.array(values, dtype=np.uint16),
        )

    def _value(self, phase: float) -> int:
        if self.wave == "SQUARE":
            normalized = 1.0 if phase < 0.5 else -1.0
        elif self.wave == "TRI":
            normalized = 4.0 * abs(phase - 0.5) - 1.0
        elif self.wave == "SAW":
            normalized = 2.0 * phase - 1.0
        elif self.wave == "NOISE":
            normalized = random.uniform(-1.0, 1.0)
        elif self.wave == "MIXED":
            harmonic = 0.35 * math.sin(6.0 * math.pi * phase)
            normalized = math.sin(2.0 * math.pi * phase) + harmonic + random.uniform(-0.08, 0.08)
            normalized = max(-1.0, min(1.0, normalized))
        else:
            normalized = math.sin(2.0 * math.pi * phase)
        return max(0, min(3300, int(self.offset_mv + self.amplitude_mv * normalized)))
