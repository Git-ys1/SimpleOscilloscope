from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..core.models import DisplayConfig, MeasurementSnapshot, TriggerConfig
from .measurements import calculate_measurements
from .trigger import TriggerMode, locate_display_trigger, triggered_reference_time_ms, trigger_marker_x_s


@dataclass(frozen=True)
class ScopeFrame:
    reference_time_ms: float | None
    trigger_x_s: float | None
    trigger_state: str
    measurements: MeasurementSnapshot
    single_hold: tuple[float, float] | None


def process_scope_frame(
    time_ms: np.ndarray,
    value_mv: np.ndarray,
    display: DisplayConfig,
    trigger: TriggerConfig,
    single_hold: tuple[float, float] | None = None,
) -> ScopeFrame:
    reference = None
    marker_x = None
    trigger_state = "FREE"
    next_single_hold = single_hold

    if time_ms.size == 0:
        return ScopeFrame(None, None, "STOP", calculate_measurements(time_ms, value_mv), next_single_hold)

    if trigger.mode == TriggerMode.SINGLE and single_hold is not None:
        reference, trigger_time = single_hold
        marker_x = trigger_marker_x_s(reference, trigger_time)
        trigger_state = "TRIG"
    else:
        trigger_index = locate_display_trigger(time_ms, value_mv, display, trigger)
        if trigger_index is not None:
            trigger_time = float(time_ms[trigger_index])
            reference = triggered_reference_time_ms(trigger_time, display, trigger)
            marker_x = trigger_marker_x_s(reference, trigger_time)
            trigger_state = "TRIG"
            if trigger.mode == TriggerMode.SINGLE:
                next_single_hold = (reference, trigger_time)
        elif trigger.mode == TriggerMode.NORMAL:
            trigger_state = "WAIT"

    return ScopeFrame(
        reference_time_ms=reference,
        trigger_x_s=marker_x,
        trigger_state=trigger_state,
        measurements=calculate_measurements(time_ms, value_mv),
        single_hold=next_single_hold,
    )
