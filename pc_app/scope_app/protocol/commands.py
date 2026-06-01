from __future__ import annotations

from ..core.models import SignalConfig


def line(command: str) -> bytes:
    return (command.strip() + "\r\n").encode("ascii")


def set_wave(wave: str) -> bytes:
    return line(f"SET WAVE {wave.upper()}")


def set_signal(config: SignalConfig) -> list[bytes]:
    return [
        set_wave(config.wave),
        line(f"SET FREQ {config.frequency_hz}"),
        line(f"SET AMP {config.amplitude_mv}"),
        line(f"SET OFFSET {config.offset_mv}"),
        line(f"SET RATE {config.sample_rate_hz}"),
        line("STATUS"),
    ]
