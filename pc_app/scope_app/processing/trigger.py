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
    if time_ms.size < 2 or value_mv.size < 2:
        return None

    level = config.level_mv
    previous = value_mv[:-1]
    current = value_mv[1:]
    if config.edge == TriggerEdge.FALLING:
        hits = np.where((previous > level) & (current <= level))[0]
    else:
        hits = np.where((previous < level) & (current >= level))[0]

    if hits.size == 0:
        return None
    return int(hits[-1] + 1)


def triggered_reference_time_ms(
    trigger_time_ms: float,
    display: DisplayConfig,
    trigger: TriggerConfig,
) -> float:
    _ = display, trigger
    return trigger_time_ms


def trigger_marker_x_s(reference_time_ms: float, trigger_time_ms: float) -> float:
    return (trigger_time_ms - reference_time_ms) / 1000.0
