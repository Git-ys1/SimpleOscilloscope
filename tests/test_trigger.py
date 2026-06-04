import numpy as np

from pc_app.scope_app.core.models import DisplayConfig, TriggerConfig
from pc_app.scope_app.processing.trigger import locate_trigger, trigger_marker_x_s, triggered_reference_time_ms


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
