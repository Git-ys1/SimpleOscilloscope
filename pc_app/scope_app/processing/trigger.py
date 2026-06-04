from __future__ import annotations

import numpy as np

from ..core.models import DisplayConfig, TriggerConfig


class TriggerMode:
    AUTO = "Auto"
    NORMAL = "Normal"
    SINGLE = "Single"


class TriggerEdge:
    RISING = "Rising"
    FALLING = "Falling"


def locate_trigger(time_ms: np.ndarray, value_mv: np.ndarray, config: TriggerConfig) -> int | None:
    hits = _trigger_hits(value_mv, config)
    if hits.size == 0:
        return None
    return int(hits[-1] + 1)


def locate_display_trigger(
    time_ms: np.ndarray,
    value_mv: np.ndarray,
    display: DisplayConfig,
    config: TriggerConfig,
) -> int | None:
    if time_ms.size < 2 or value_mv.size < 2:
        return None

    hits = _trigger_hits(value_mv, config)
    if hits.size == 0:
        return None

    indices = hits + 1
    span_ms = max(display.time_per_div_s * 10.0 * 1000.0, 0.001)
    pre = min(max(config.pretrigger_ratio, 0.0), 0.95)
    left_ms = -pre * span_ms + display.horizontal_offset_s * 1000.0
    right_ms = (1.0 - pre) * span_ms + display.horizontal_offset_s * 1000.0
    first_time = float(time_ms[0])
    last_time = float(time_ms[-1])

    full_window = []
    for index in indices.tolist():
        trigger_time = float(time_ms[index])
        if trigger_time + left_ms >= first_time and trigger_time + right_ms <= last_time:
            full_window.append(index)
    if full_window:
        return int(full_window[-1])
    return int(indices[-1])


def _trigger_hits(value_mv: np.ndarray, config: TriggerConfig) -> np.ndarray:
    level = config.level_mv
    previous = value_mv[:-1]
    current = value_mv[1:]
    if config.edge == TriggerEdge.FALLING:
        return np.where((previous > level) & (current <= level))[0]
    return np.where((previous < level) & (current >= level))[0]


def triggered_reference_time_ms(
    trigger_time_ms: float,
    display: DisplayConfig,
    trigger: TriggerConfig,
) -> float:
    _ = display, trigger
    return trigger_time_ms


def trigger_marker_x_s(reference_time_ms: float, trigger_time_ms: float) -> float:
    return (trigger_time_ms - reference_time_ms) / 1000.0
