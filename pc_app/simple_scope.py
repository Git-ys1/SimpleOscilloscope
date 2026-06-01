#!/usr/bin/env python3
"""Simple oscilloscope host UI for the STM32 signal-source firmware."""

from __future__ import annotations

import argparse
import queue
import socket
import threading
import time
import tkinter as tk
from dataclasses import dataclass
from tkinter import messagebox, ttk
from typing import Optional


DEFAULT_SOURCE = "tcp://127.0.0.1:8765"
DEFAULT_BAUD = 115200
MAX_POINTS = 600


@dataclass
class OscSample:
    sequence: int
    time_ms: int
    value_mv: int
    wave: str
    frequency_hz: int
    amplitude_mv: int
    offset_mv: int


class LineEndpoint:
    def readline(self) -> bytes:
        raise NotImplementedError

    def write(self, data: bytes) -> None:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError


class TcpEndpoint(LineEndpoint):
    def __init__(self, host: str, port: int, timeout: float = 0.4) -> None:
        self._sock = socket.create_connection((host, port), timeout=3.0)
        self._sock.settimeout(timeout)
        self._file = self._sock.makefile("rwb", buffering=0)

    def readline(self) -> bytes:
        try:
            return self._file.readline()
        except socket.timeout:
            return b""

    def write(self, data: bytes) -> None:
        self._file.write(data)

    def close(self) -> None:
        try:
            self._file.close()
        finally:
            self._sock.close()


class SerialEndpoint(LineEndpoint):
    def __init__(self, port: str, baud: int) -> None:
        try:
            import serial  # type: ignore
        except ImportError as exc:
            raise RuntimeError("缺少 pyserial，请先执行 pip install -r requirements.txt") from exc

        self._serial = serial.Serial(port=port, baudrate=baud, timeout=0.4)

    def readline(self) -> bytes:
        return self._serial.readline()

    def write(self, data: bytes) -> None:
        self._serial.write(data)

    def close(self) -> None:
        self._serial.close()


def open_endpoint(source: str, baud: int) -> LineEndpoint:
    if source.startswith("tcp://"):
        target = source[len("tcp://") :]
        host, _, port_text = target.partition(":")
        return TcpEndpoint(host or "127.0.0.1", int(port_text or "8765"))
    return SerialEndpoint(source, baud)


def parse_sample(line: str) -> Optional[OscSample]:
    parts = line.strip().split(",")
    if len(parts) != 8 or parts[0] != "OSC":
        return None
    try:
        return OscSample(
            sequence=int(parts[1]),
            time_ms=int(parts[2]),
            value_mv=int(parts[3]),
            wave=parts[4],
            frequency_hz=int(parts[5]),
            amplitude_mv=int(parts[6]),
            offset_mv=int(parts[7]),
        )
    except ValueError:
        return None


class ScopeApp(tk.Tk):
    def __init__(self, source: str, baud: int) -> None:
        super().__init__()
        self.title("Simple Oscilloscope")
        self.geometry("1040x680")
        self.minsize(860, 560)

        self.source_var = tk.StringVar(value=source)
        self.baud_var = tk.StringVar(value=str(baud))
        self.wave_var = tk.StringVar(value="SINE")
        self.freq_var = tk.StringVar(value="5")
        self.amp_var = tk.StringVar(value="1200")
        self.offset_var = tk.StringVar(value="1650")
        self.rate_var = tk.StringVar(value="100")
        self.status_var = tk.StringVar(value="未连接")

        self._endpoint: Optional[LineEndpoint] = None
        self._reader_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._events: "queue.Queue[tuple[str, object]]" = queue.Queue()
        self._samples: list[OscSample] = []

        self._build_ui()
        self.after(40, self._drain_events)

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self, padding=(10, 8))
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.columnconfigure(1, weight=1)

        ttk.Label(toolbar, text="Source").grid(row=0, column=0, sticky="w")
        ttk.Entry(toolbar, textvariable=self.source_var).grid(row=0, column=1, sticky="ew", padx=(6, 10))
        ttk.Label(toolbar, text="Baud").grid(row=0, column=2, sticky="w")
        ttk.Entry(toolbar, textvariable=self.baud_var, width=8).grid(row=0, column=3, padx=(6, 10))
        ttk.Button(toolbar, text="Connect", command=self.connect).grid(row=0, column=4, padx=2)
        ttk.Button(toolbar, text="Disconnect", command=self.disconnect).grid(row=0, column=5, padx=2)
        ttk.Button(toolbar, text="Start", command=lambda: self.send_command("START")).grid(row=0, column=6, padx=2)
        ttk.Button(toolbar, text="Stop", command=lambda: self.send_command("STOP")).grid(row=0, column=7, padx=2)

        controls = ttk.Frame(self, padding=(10, 0, 10, 8))
        controls.grid(row=2, column=0, sticky="ew")

        ttk.Label(controls, text="Wave").grid(row=0, column=0, padx=(0, 4))
        ttk.Combobox(controls, textvariable=self.wave_var, values=("SINE", "SQUARE", "TRI", "SAW"), width=9, state="readonly").grid(row=0, column=1)
        ttk.Label(controls, text="Freq Hz").grid(row=0, column=2, padx=(14, 4))
        ttk.Entry(controls, textvariable=self.freq_var, width=8).grid(row=0, column=3)
        ttk.Label(controls, text="Amp mV").grid(row=0, column=4, padx=(14, 4))
        ttk.Entry(controls, textvariable=self.amp_var, width=8).grid(row=0, column=5)
        ttk.Label(controls, text="Offset mV").grid(row=0, column=6, padx=(14, 4))
        ttk.Entry(controls, textvariable=self.offset_var, width=8).grid(row=0, column=7)
        ttk.Label(controls, text="Rate Hz").grid(row=0, column=8, padx=(14, 4))
        ttk.Entry(controls, textvariable=self.rate_var, width=8).grid(row=0, column=9)
        ttk.Button(controls, text="Apply", command=self.apply_settings).grid(row=0, column=10, padx=(14, 4))
        ttk.Label(controls, textvariable=self.status_var).grid(row=0, column=11, sticky="e", padx=(18, 0))

        self.canvas = tk.Canvas(self, background="#0b1020", highlightthickness=0)
        self.canvas.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 8))
        self.canvas.bind("<Configure>", lambda _event: self._draw())

    def connect(self) -> None:
        self.disconnect()
        self._stop_event.clear()
        source = self.source_var.get().strip()
        baud = int(self.baud_var.get().strip() or DEFAULT_BAUD)

        try:
            self._endpoint = open_endpoint(source, baud)
        except Exception as exc:  # noqa: BLE001 - shown to operator
            messagebox.showerror("连接失败", str(exc))
            self.status_var.set("连接失败")
            return

        self._reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._reader_thread.start()
        self.status_var.set(f"已连接 {source}")
        self.send_command("ID?")

    def disconnect(self) -> None:
        self._stop_event.set()
        if self._endpoint is not None:
            try:
                self._endpoint.close()
            except Exception:
                pass
            self._endpoint = None
        self.status_var.set("未连接")

    def send_command(self, command: str) -> None:
        if self._endpoint is None:
            return
        try:
            self._endpoint.write((command.strip() + "\r\n").encode("ascii"))
        except Exception as exc:  # noqa: BLE001
            self._events.put(("status", f"发送失败: {exc}"))

    def apply_settings(self) -> None:
        self.send_command(f"SET WAVE {self.wave_var.get()}")
        self.send_command(f"SET FREQ {self.freq_var.get()}")
        self.send_command(f"SET AMP {self.amp_var.get()}")
        self.send_command(f"SET OFFSET {self.offset_var.get()}")
        self.send_command(f"SET RATE {self.rate_var.get()}")
        self.send_command("STATUS")

    def _reader_loop(self) -> None:
        assert self._endpoint is not None
        while not self._stop_event.is_set():
            try:
                raw = self._endpoint.readline()
            except Exception as exc:  # noqa: BLE001
                self._events.put(("status", f"读取失败: {exc}"))
                return
            if not raw:
                continue
            line = raw.decode("ascii", errors="replace").strip()
            sample = parse_sample(line)
            if sample is not None:
                self._events.put(("sample", sample))
            else:
                self._events.put(("status", line))

    def _drain_events(self) -> None:
        redraw = False
        try:
            while True:
                kind, payload = self._events.get_nowait()
                if kind == "sample":
                    self._samples.append(payload)  # type: ignore[arg-type]
                    self._samples = self._samples[-MAX_POINTS:]
                    redraw = True
                elif kind == "status":
                    self.status_var.set(str(payload))
        except queue.Empty:
            pass
        if redraw:
            self._draw()
        self.after(40, self._drain_events)

    def _draw(self) -> None:
        canvas = self.canvas
        width = max(canvas.winfo_width(), 1)
        height = max(canvas.winfo_height(), 1)
        canvas.delete("all")

        pad_l, pad_r, pad_t, pad_b = 54, 18, 22, 34
        plot_w = max(width - pad_l - pad_r, 1)
        plot_h = max(height - pad_t - pad_b, 1)

        for i in range(11):
            x = pad_l + (plot_w * i / 10)
            color = "#1b2748" if i != 0 else "#2e426f"
            canvas.create_line(x, pad_t, x, pad_t + plot_h, fill=color)
        for i in range(7):
            y = pad_t + (plot_h * i / 6)
            color = "#1b2748" if i != 3 else "#3c568c"
            canvas.create_line(pad_l, y, pad_l + plot_w, y, fill=color)

        canvas.create_text(12, pad_t, anchor="nw", text="3300 mV", fill="#9fb3d9")
        canvas.create_text(12, pad_t + plot_h - 12, anchor="nw", text="0 mV", fill="#9fb3d9")

        if len(self._samples) < 2:
            canvas.create_text(width / 2, height / 2, text="等待样本...", fill="#9fb3d9", font=("Segoe UI", 16))
            return

        points: list[float] = []
        visible = self._samples[-MAX_POINTS:]
        count = len(visible)
        for index, sample in enumerate(visible):
            x = pad_l + (plot_w * index / max(count - 1, 1))
            y = pad_t + plot_h - ((sample.value_mv / 3300.0) * plot_h)
            points.extend([x, y])

        canvas.create_line(*points, fill="#54f0b5", width=2, smooth=True)
        last = visible[-1]
        info = (
            f"{last.value_mv} mV   {last.wave}   {last.frequency_hz} Hz   "
            f"amp {last.amplitude_mv} mV   offset {last.offset_mv} mV"
        )
        canvas.create_text(pad_l + 8, pad_t + 8, anchor="nw", text=info, fill="#e7eefc", font=("Segoe UI", 11))

    def destroy(self) -> None:
        self.disconnect()
        super().destroy()


def main() -> int:
    parser = argparse.ArgumentParser(description="Simple Oscilloscope host UI")
    parser.add_argument("--source", default=DEFAULT_SOURCE, help="COM port or tcp://host:port")
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUD)
    args = parser.parse_args()

    app = ScopeApp(args.source, args.baud)
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
