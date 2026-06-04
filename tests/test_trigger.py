import numpy as np

from pc_app.scope_app.core.models import DisplayConfig, TriggerConfig
from pc_app.scope_app.processing.trigger import locate_display_trigger, locate_trigger, trigger_marker_x_s, triggered_reference_time_ms


def test_locate_rising_trigger():
    time_ms = np.array([0, 1, 2, 3], dtype=float)
    value_mv = np.array([1000, 1200, 1800, 2200], dtype=float)
    index = locate_trigger(time_ms, value_mv, TriggerConfig(edge="Rising", level_mv=1650))
    assert index == 2


def test_locate_falling_trigger():
    time_ms = np.array([0, 1, 2, 3], dtype=float)
    value_mv = np.array([2200, 1800, 1200, 1000], dtype=float)
    index = locate_trigger(time_ms, value_mv, TriggerConfig(edge="Falling", level_mv=1650))
    assert index == 2


def test_trigger_reference_places_marker_at_pretrigger_position():
    display = DisplayConfig(time_per_div_s=0.1, horizontal_offset_s=0.0)
    trigger = TriggerConfig(pretrigger_ratio=0.25)
    reference = triggered_reference_time_ms(1000.0, display, trigger)
    assert trigger_marker_x_s(reference, 1000.0) == 0.0


def test_display_trigger_keeps_post_trigger_samples_available():
    display = DisplayConfig(time_per_div_s=0.0005, horizontal_offset_s=0.0)
    trigger = TriggerConfig(edge="Rising", level_mv=0.0, pretrigger_ratio=0.5)
    sample_rate = 20_000.0
    time_ms = np.arange(0.0, 12.0, 1000.0 / sample_rate)
    value_mv = np.sin(2.0 * np.pi * 1000.0 * (time_ms / 1000.0))

    index = locate_display_trigger(time_ms, value_mv, display, trigger)

    assert index is not None
    assert time_ms[index] + 2.5 <= time_ms[-1]
    assert time_ms[index] > time_ms[-1] - 4.0
