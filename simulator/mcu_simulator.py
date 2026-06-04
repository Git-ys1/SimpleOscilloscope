#!/usr/bin/env python3
"""TCP lower-computer simulator using the same text protocol as the STM32 firmware."""

from __future__ import annotations

import argparse
import math
import socketserver
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pc_app.scope_app.protocol.binary_protocol import BinaryProtocol


@dataclass
class SignalState:
    wave: str = "SINE"
    freq_hz: int = 1000
    amp_mv: int = 1200
    offset_mv: int = 1650
    rate_hz: int = 20_000
    streaming: bool = True
    sequence: int = 0
    start_time: float = time.monotonic()
    output_format: str = "BINARY"


class SimulatorHandler(socketserver.StreamRequestHandler):
    state = SignalState()
    lock = threading.Lock()
    version = "0.9.3"
    rate_min = 1
    rate_max = 20_000
    freq_min = 1
    freq_max = 5_000
    baud = 921600
    binary_block_points = 64
    binary = BinaryProtocol()

    def setup(self) -> None:
        super().setup()
        self._stop = threading.Event()
        self._tx_thread = threading.Thread(target=self._tx_loop, daemon=True)

    def handle(self) -> None:
        self._send(f"BOOT,SimpleOscilloscope,{self.version},SIMULATOR,{self.baud}\n")
        self._send_status()
        self._tx_thread.start()
        while not self._stop.is_set():
            raw = self.rfile.readline()
            if not raw:
                break
            self._handle_command(raw.decode("ascii", errors="ignore").strip())
        self._stop.set()

    def _send(self, data: str | bytes) -> None:
        try:
            if isinstance(data, str):
                data = data.encode("ascii")
            self.wfile.write(data)
            self.wfile.flush()
        except OSError:
            self._stop.set()

    def _send_status(self) -> None:
        with self.lock:
            state = self.state
            self._send(
                f"STATUS,{state.wave},{state.freq_hz},{state.amp_mv},"
                f"{state.offset_mv},{state.rate_hz},{'RUN' if state.streaming else 'STOP'}\n"
            )
            self._send(f"FORMAT,{state.output_format}\n")

    def _handle_command(self, command: str) -> None:
        if command == "PING":
            self._send(f"PONG,SimpleOscilloscope,{self.version}\n")
        elif command == "ID?":
            self._send(f"ID,SimpleOscilloscope,SIMULATOR,{self.version},TCP,BINARY_DATA\n")
        elif command == "CAP?":
            self._send(
                f"CAP,RATE_MIN={self.rate_min},RATE_MAX={self.rate_max},"
                f"FREQ_MIN={self.freq_min},FREQ_MAX={self.freq_max},"
                f"BAUD={self.baud},BLOCK={self.binary_block_points}\n"
            )
        elif command == "STATUS":
            self._send_status()
        elif command == "START":
            with self.lock:
                self.state.streaming = True
            self._send("OK,START\n")
        elif command == "STOP":
            with self.lock:
                self.state.streaming = False
            self._send("OK,STOP\n")
        elif command.startswith("SET "):
            self._handle_set(command)
        elif command:
            self._send("ERR,unknown_cmd\n")

    def _handle_set(self, command: str) -> None:
        parts = command.split()
        if len(parts) < 3:
            self._send("ERR,bad_set\n")
            return

        key, value = parts[1], parts[2]
        with self.lock:
            if key == "WAVE" and value in {"SINE", "SQUARE", "TRI", "TRIANGLE", "SAW"}:
                self.state.wave = "TRI" if value == "TRIANGLE" else value
            elif key == "FREQ":
                self.state.freq_hz = max(self.freq_min, min(self.freq_max, int(value)))
            elif key == "AMP":
                self.state.amp_mv = max(0, min(3300, int(value)))
            elif key == "OFFSET":
                self.state.offset_mv = max(0, min(3300, int(value)))
            elif key == "RATE":
                self.state.rate_hz = max(self.rate_min, min(self.rate_max, int(value)))
            elif key == "FORMAT" and value in {"ASCII", "BINARY"}:
                self.state.output_format = value
            else:
                self._send("ERR,bad_set\n")
                return
        self._send(f"OK,{key}\n")
        if key == "FORMAT":
            self._send_status()

    def _tx_loop(self) -> None:
        while not self._stop.is_set():
            with self.lock:
                state = self.state
                streaming = state.streaming
                rate_hz = state.rate_hz
                output_format = state.output_format
            if streaming:
                if output_format == "BINARY":
                    self._send_binary_block()
                else:
                    self._send_sample()
            delay_points = self.binary_block_points if output_format == "BINARY" else 1
            time.sleep(max(delay_points / max(rate_hz, 1), 0.001))

    def _send_sample(self) -> None:
        with self.lock:
            state = self.state
            state.sequence += 1
            now = time.monotonic()
            elapsed = now - state.start_time
            phase = (elapsed * state.freq_hz) % 1.0
            value_mv = self._wave_value(state, phase)
            line = (
                f"OSC,{state.sequence},{int(elapsed * 1000)},{value_mv},"
                f"{state.wave},{state.freq_hz},{state.amp_mv},{state.offset_mv}\n"
            )
        self._send(line)

    def _send_binary_block(self) -> None:
        with self.lock:
            state = self.state
            start_sequence = state.sequence + 1
            now = time.monotonic()
            values = []
            for index in range(self.binary_block_points):
                elapsed = (now - state.start_time) + (index / max(state.rate_hz, 1))
                phase = (elapsed * state.freq_hz) % 1.0
                value_mv = self._wave_value(state, phase)
                values.append(int(value_mv * 4095 / 3300))
            state.sequence += self.binary_block_points
            frame = self.binary.build_data_frame(
                sequence=start_sequence,
                sample_rate_hz=state.rate_hz,
                values_adc=np.array(values, dtype=np.uint16),
            )
        self._send(frame)

    @staticmethod
    def _wave_value(state: SignalState, phase: float) -> int:
        if state.wave == "SQUARE":
            normalized = 1.0 if phase < 0.5 else -1.0
        elif state.wave == "TRI":
            normalized = 4.0 * abs(phase - 0.5) - 1.0
        elif state.wave == "SAW":
            normalized = (2.0 * phase) - 1.0
        else:
            normalized = math.sin(2.0 * math.pi * phase)
        value = int(state.offset_mv + state.amp_mv * normalized)
        return max(0, min(3300, value))


class ThreadingTcpServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main() -> int:
    parser = argparse.ArgumentParser(description="Simple Oscilloscope MCU simulator")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    with ThreadingTcpServer((args.host, args.port), SimulatorHandler) as server:
        print(f"MCU simulator listening on tcp://{args.host}:{args.port}")
        server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
