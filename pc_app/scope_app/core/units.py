from __future__ import annotations


def mv_to_v(value_mv: float) -> float:
    return value_mv / 1000.0


def format_voltage(value_mv: float) -> str:
    if abs(value_mv) >= 1000.0:
        return f"{value_mv / 1000.0:.3f} V"
    return f"{value_mv:.1f} mV"


def format_frequency(value_hz: float) -> str:
    if value_hz >= 1000.0:
        return f"{value_hz / 1000.0:.3f} kHz"
    return f"{value_hz:.2f} Hz"
