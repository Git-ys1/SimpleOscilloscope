from __future__ import annotations

import math
import queue
import time


class FakeTransport:
    name = "fake"

    def __init__(self, source: str = "fake://sine") -> None:
        wave = source.split("://", 1)[1].upper() if "://" in source else "SINE"
        self.wave = "TRI" if wave == "TRIANGLE" else wave
        if self.wave not in {"SINE", "SQUARE", "TRI", "SAW"}:
            self.wave = "SINE"
        self.frequency_hz = 5
        self.amplitude_mv = 1200
        self.offset_mv = 1650
        self.sample_rate_hz = 200
        self.streaming = True
        self.sequence = 0
        self.started = time.monotonic()
        self._closed = False
        self._outbox: "queue.Queue[bytes]" = queue.Queue()
        self._enqueue(b"BOOT,SimpleOscilloscope,0.2.1,FAKE,115200\n")
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

    def readline(self) -> bytes:
        if self._closed:
            return b""
        try:
            return self._outbox.get_nowait()
        except queue.Empty:
            pass

        time.sleep(max(1.0 / max(self.sample_rate_hz, 1), 0.001))
        if not self.streaming:
            return b""
        return self._sample_line()

    def write(self, data: bytes) -> None:
        for raw in data.decode("ascii", errors="ignore").splitlines():
            self._handle(raw.strip())

    def close(self) -> None:
        self._closed = True

    def _handle(self, command: str) -> None:
        parts = command.split()
        if command == "PING":
            self._enqueue(b"PONG,SimpleOscilloscope,0.2.1\n")
        elif command == "ID?":
            self._enqueue(b"ID,SimpleOscilloscope,FAKE,0.2.1,TCP\n")
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
                if candidate not in {"SINE", "SQUARE", "TRI", "SAW"}:
                    raise ValueError
                self.wave = candidate
            elif key == "FREQ":
                self.frequency_hz = max(1, min(500, int(value)))
            elif key == "AMP":
                self.amplitude_mv = max(0, min(3300, int(value)))
            elif key == "OFFSET":
                self.offset_mv = max(0, min(3300, int(value)))
            elif key == "RATE":
                self.sample_rate_hz = max(1, min(5000, int(value)))
            else:
                raise ValueError
        except ValueError:
            self._enqueue(b"ERR,bad_set\n")
            return
        self._enqueue(f"OK,{key}\n".encode("ascii"))

    def _sample_line(self) -> bytes:
        elapsed = time.monotonic() - self.started
        phase = (elapsed * self.frequency_hz) % 1.0
        value = self._value(phase)
        self.sequence += 1
        return (
            f"OSC,{self.sequence},{int(elapsed * 1000)},{value},{self.wave},"
            f"{self.frequency_hz},{self.amplitude_mv},{self.offset_mv}\n"
        ).encode("ascii")

    def _value(self, phase: float) -> int:
        if self.wave == "SQUARE":
            normalized = 1.0 if phase < 0.5 else -1.0
        elif self.wave == "TRI":
            normalized = 4.0 * abs(phase - 0.5) - 1.0
        elif self.wave == "SAW":
            normalized = 2.0 * phase - 1.0
        else:
            normalized = math.sin(2.0 * math.pi * phase)
        return max(0, min(3300, int(self.offset_mv + self.amplitude_mv * normalized)))
