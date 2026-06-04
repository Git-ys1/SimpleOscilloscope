from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..core.models import DisplayConfig, DisplayMode, TriggerConfig


@dataclass(frozen=True)
class RecordView:
    x_s: np.ndarray
    y_mv: np.ndarray
    trigger_x_s: float | None
    x_left_s: float
    x_right_s: float


def build_record_view(
    time_ms: np.ndarray,
    value_mv: np.ndarray,
    display: DisplayConfig,
    trigger: TriggerConfig,
    reference_time_ms: float | None,
    trigger_x_s: float | None,
) -> RecordView:
    left, right = x_range_for_display(display, trigger)
    if time_ms.size == 0:
        return RecordView(
            x_s=np.array([], dtype=np.float64),
            y_mv=np.array([], dtype=np.float64),
            trigger_x_s=None,
            x_left_s=left,
            x_right_s=right,
        )

    if display.display_mode == DisplayMode.ROLL:
        reference = float(time_ms[-1] if reference_time_ms is None else reference_time_ms)
    else:
        reference = float(time_ms[-1] if reference_time_ms is None else reference_time_ms)
    x_s = (time_ms.astype(np.float64) - reference) / 1000.0
    visible = (x_s >= left) & (x_s <= right)
    if not np.any(visible):
        visible = np.ones_like(x_s, dtype=bool)
    return RecordView(
        x_s=x_s[visible],
        y_mv=value_mv.astype(np.float64)[visible],
        trigger_x_s=trigger_x_s,
        x_left_s=left,
        x_right_s=right,
    )


def x_range_for_display(display: DisplayConfig, trigger: TriggerConfig) -> tuple[float, float]:
    span = max(display.time_per_div_s * 10.0, 0.000001)
    if display.display_mode == DisplayMode.ROLL:
        right = display.horizontal_offset_s
        return right - span, right
    pre = min(max(trigger.pretrigger_ratio, 0.0), 0.95)
    return (-pre * span) + display.horizontal_offset_s, ((1.0 - pre) * span) + display.horizontal_offset_s
