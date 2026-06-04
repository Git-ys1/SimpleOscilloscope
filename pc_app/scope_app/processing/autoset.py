from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..core.models import DisplayConfig, MeasurementSnapshot, TriggerConfig
from .measurements import calculate_measurements


TIME_DIVS_S = (
    1e-6,
    2e-6,
    5e-6,
    10e-6,
    20e-6,
    50e-6,
    100e-6,
    200e-6,
    500e-6,
    1e-3,
    2e-3,
    5e-3,
    10e-3,
    20e-3,
    50e-3,
    100e-3,
    200e-3,
    500e-3,
    1.0,
)

VOLT_DIVS_MV = (1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000)


@dataclass(frozen=True)
class AutoSetResult:
    display: DisplayConfig
    trigger: TriggerConfig
    measurements: MeasurementSnapshot


def autoset_from_waveform(time_s: np.ndarray, voltage_mv: np.ndarray) -> AutoSetResult:
    time_ms = np.asarray(time_s, dtype=np.float64) * 1000.0
    voltage = np.asarray(voltage_mv, dtype=np.float64)
    measurements = calculate_measurements(time_ms, voltage)
    if voltage.size == 0:
        return AutoSetResult(DisplayConfig(), TriggerConfig(), measurements)

    vpp = max(measurements.v_pp_mv, 50.0)
    center = (measurements.v_max_mv + measurements.v_min_mv) / 2.0
    volt_div = _ceil_common(vpp / 6.0, VOLT_DIVS_MV)
    time_div = _time_div_for_frequency(measurements.frequency_hz)
    trigger = TriggerConfig(mode="Auto", edge="Rising", level_mv=center, pretrigger_ratio=0.5)
    display = DisplayConfig(
        time_per_div_s=time_div,
        volt_per_div_mv=volt_div,
        horizontal_offset_s=0.0,
        vertical_center_mv=center,
        auto_range=False,
    )
    return AutoSetResult(display, trigger, measurements)


def _time_div_for_frequency(frequency_hz: float) -> float:
    if frequency_hz <= 0.0:
        return 0.1
    target = (1.0 / frequency_hz) / 5.0
    return float(_ceil_common(target, TIME_DIVS_S))


def _ceil_common(value: float, choices: tuple[float | int, ...]) -> float:
    for choice in choices:
        if float(choice) >= value * 0.999999:
            return float(choice)
    return float(choices[-1])
