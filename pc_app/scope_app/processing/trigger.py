from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..core.models import DisplayConfig, TriggerConfig


class TriggerMode:
    AUTO = "Auto"
    NORMAL = "Normal"
    SINGLE = "Single"


class TriggerEdge:
    RISING = "Rising"
    FALLING = "Falling"


@dataclass(frozen=True)
class TriggerPoint:
    sample_index: int
    time_ms: float


def locate_trigger(time_ms: np.ndarray, value_mv: np.ndarray, config: TriggerConfig) -> int | None:
    _ = time_ms
    hits = _trigger_hits_hysteresis(value_mv, config)
    if hits.size == 0:
        return None
    return int(hits[-1] + 1)


def locate_display_trigger(
    time_ms: np.ndarray,
    value_mv: np.ndarray,
    display: DisplayConfig,
    config: TriggerConfig,
) -> int | None:
    point = locate_display_trigger_point(time_ms, value_mv, display, config)
    if point is None:
        return None
    return point.sample_index


def locate_display_trigger_point(
    time_ms: np.ndarray,
    value_mv: np.ndarray,
    display: DisplayConfig,
    config: TriggerConfig,
) -> TriggerPoint | None:
    if time_ms.size < 2 or value_mv.size < 2:
        return None

    hits = _trigger_hits_hysteresis(value_mv, config)
    if hits.size == 0:
        return None

    span_ms = max(display.time_per_div_s * 10.0 * 1000.0, 0.001)
    pre = min(max(config.pretrigger_ratio, 0.0), 0.95)
    left_ms = -pre * span_ms + display.horizontal_offset_s * 1000.0
    right_ms = (1.0 - pre) * span_ms + display.horizontal_offset_s * 1000.0
    first_time = float(time_ms[0])
    last_time = float(time_ms[-1])

    full_window: list[TriggerPoint] = []
    for hit in hits.tolist():
        trigger_time = _cross_time_ms(time_ms, value_mv, int(hit), config.level_mv)
        if trigger_time + left_ms >= first_time and trigger_time + right_ms <= last_time:
            full_window.append(TriggerPoint(sample_index=int(hit) + 1, time_ms=trigger_time))
    if full_window:
        return full_window[-1]

    hit = int(hits[-1])
    return TriggerPoint(sample_index=hit + 1, time_ms=_cross_time_ms(time_ms, value_mv, hit, config.level_mv))


def _cross_time_ms(time_ms: np.ndarray, value_mv: np.ndarray, index: int, level_mv: float) -> float:
    y0 = float(value_mv[index])
    y1 = float(value_mv[index + 1])
    x0 = float(time_ms[index])
    x1 = float(time_ms[index + 1])

    denom = y1 - y0
    if abs(denom) < 1e-12:
        return x1

    ratio = (level_mv - y0) / denom
    ratio = max(0.0, min(1.0, ratio))
    return x0 + ratio * (x1 - x0)


def _trigger_hits_hysteresis(value_mv: np.ndarray, config: TriggerConfig) -> np.ndarray:
    if value_mv.size < 2:
        return np.array([], dtype=np.int64)

    level = config.level_mv
    hysteresis = _effective_hysteresis_mv(value_mv, config)
    hits: list[int] = []

    if config.edge == TriggerEdge.FALLING:
        armed = bool(value_mv[0] >= level + hysteresis)
        for index in range(1, value_mv.size):
            previous = float(value_mv[index - 1])
            current = float(value_mv[index])
            if previous >= level + hysteresis:
                armed = True
            if armed and previous > level >= current:
                hits.append(index - 1)
                armed = False
    else:
        armed = bool(value_mv[0] <= level - hysteresis)
        for index in range(1, value_mv.size):
            previous = float(value_mv[index - 1])
            current = float(value_mv[index])
            if previous <= level - hysteresis:
                armed = True
            if armed and previous < level <= current:
                hits.append(index - 1)
                armed = False

    return np.asarray(hits, dtype=np.int64)


def _effective_hysteresis_mv(value_mv: np.ndarray, config: TriggerConfig) -> float:
    _ = value_mv
    requested = max(float(getattr(config, "hysteresis_mv", 15.0)), 0.0)
    return requested


def triggered_reference_time_ms(
    trigger_time_ms: float,
    display: DisplayConfig,
    trigger: TriggerConfig,
) -> float:
    _ = display, trigger
    return trigger_time_ms


def trigger_marker_x_s(reference_time_ms: float, trigger_time_ms: float) -> float:
    return (trigger_time_ms - reference_time_ms) / 1000.0
