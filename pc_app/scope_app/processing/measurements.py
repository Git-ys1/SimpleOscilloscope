from __future__ import annotations

import numpy as np

from ..core.models import MeasurementSnapshot


def calculate_measurements(time_ms: np.ndarray, value_mv: np.ndarray) -> MeasurementSnapshot:
    if value_mv.size == 0:
        return MeasurementSnapshot(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    v_min = float(np.min(value_mv))
    v_max = float(np.max(value_mv))
    v_avg = float(np.mean(value_mv))
    centered = value_mv - v_avg
    v_rms = float(np.sqrt(np.mean(np.square(value_mv))))
    frequency = estimate_frequency_hz(time_ms, centered)
    return MeasurementSnapshot(
        points=int(value_mv.size),
        v_min_mv=v_min,
        v_max_mv=v_max,
        v_pp_mv=v_max - v_min,
        v_avg_mv=v_avg,
        v_rms_mv=v_rms,
        frequency_hz=frequency,
    )


def estimate_frequency_hz(time_ms: np.ndarray, centered_value: np.ndarray) -> float:
    if time_ms.size < 4:
        return 0.0
    rising_crossings: list[float] = []
    for i in range(1, centered_value.size):
        prev = centered_value[i - 1]
        cur = centered_value[i]
        if prev < 0.0 <= cur:
            dt = time_ms[i] - time_ms[i - 1]
            if dt <= 0:
                continue
            ratio = -prev / (cur - prev) if cur != prev else 0.0
            rising_crossings.append(float(time_ms[i - 1] + ratio * dt))
    if len(rising_crossings) < 2:
        return 0.0
    periods_ms = np.diff(np.array(rising_crossings, dtype=np.float64))
    periods_ms = periods_ms[periods_ms > 0.0]
    if periods_ms.size == 0:
        return 0.0
    return float(1000.0 / np.mean(periods_ms))
