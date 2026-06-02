from __future__ import annotations

import numpy as np

from ..core.models import MeasurementSnapshot


def calculate_measurements(time_ms: np.ndarray, value_mv: np.ndarray) -> MeasurementSnapshot:
    if value_mv.size == 0:
        return MeasurementSnapshot(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    v_min = float(np.min(value_mv))
    v_max = float(np.max(value_mv))
    v_avg = float(np.mean(value_mv))
    centered = value_mv - v_avg
    v_rms_dc = float(np.sqrt(np.mean(np.square(value_mv))))
    v_rms_ac = float(np.sqrt(np.mean(np.square(centered))))
    frequency = estimate_frequency_hz(time_ms, centered)
    period_ms = 1000.0 / frequency if frequency > 0.0 else 0.0
    duty_cycle = estimate_duty_cycle_percent(time_ms, value_mv)
    return MeasurementSnapshot(
        points=int(value_mv.size),
        v_min_mv=v_min,
        v_max_mv=v_max,
        v_pp_mv=v_max - v_min,
        v_avg_mv=v_avg,
        v_rms_dc_mv=v_rms_dc,
        v_rms_ac_mv=v_rms_ac,
        frequency_hz=frequency,
        period_ms=period_ms,
        duty_cycle_percent=duty_cycle,
    )


def estimate_frequency_hz(time_ms: np.ndarray, centered_value: np.ndarray) -> float:
    if time_ms.size < 4:
        return 0.0
    hysteresis = max(float(np.ptp(centered_value)) * 0.08, 1.0)
    rising_crossings: list[float] = []
    armed = centered_value[0] < -hysteresis
    for i in range(1, centered_value.size):
        prev = centered_value[i - 1]
        cur = centered_value[i]
        if cur < -hysteresis:
            armed = True
        if armed and prev < 0.0 <= cur and cur >= hysteresis:
            dt = time_ms[i] - time_ms[i - 1]
            if dt <= 0:
                continue
            ratio = -prev / (cur - prev) if cur != prev else 0.0
            rising_crossings.append(float(time_ms[i - 1] + ratio * dt))
            armed = False
    if len(rising_crossings) < 2:
        return 0.0
    periods_ms = np.diff(np.array(rising_crossings, dtype=np.float64))
    periods_ms = periods_ms[periods_ms > 0.0]
    if periods_ms.size == 0:
        return 0.0
    return float(1000.0 / np.mean(periods_ms))


def estimate_duty_cycle_percent(time_ms: np.ndarray, value_mv: np.ndarray) -> float:
    if time_ms.size < 2 or value_mv.size < 2:
        return 0.0
    threshold = (float(np.min(value_mv)) + float(np.max(value_mv))) / 2.0
    durations = np.diff(time_ms.astype(np.float64))
    valid = durations > 0.0
    if not np.any(valid):
        return 0.0
    high = value_mv[:-1] >= threshold
    high_time = float(np.sum(durations[valid & high]))
    total_time = float(np.sum(durations[valid]))
    return (high_time / total_time) * 100.0 if total_time > 0.0 else 0.0
