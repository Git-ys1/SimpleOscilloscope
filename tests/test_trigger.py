import numpy as np
import pytest

from pc_app.scope_app.core.models import DisplayConfig, TriggerConfig
from pc_app.scope_app.processing.pipeline import process_scope_frame
from pc_app.scope_app.processing.record_view import RecordView
from pc_app.scope_app.processing.trigger import (
    locate_display_trigger,
    locate_display_trigger_point,
    locate_trigger,
    trigger_marker_x_s,
    triggered_reference_time_ms,
)
from pc_app.scope_app.ui.scope_workspace import ScopeWorkspace


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
    value_mv = 1200.0 * np.sin(2.0 * np.pi * 1000.0 * (time_ms / 1000.0))

    index = locate_display_trigger(time_ms, value_mv, display, trigger)

    assert index is not None
    assert time_ms[index] + 2.5 <= time_ms[-1]
    assert time_ms[index] > time_ms[-1] - 4.0


def test_display_trigger_uses_interpolated_crossing_time():
    display = DisplayConfig(time_per_div_s=0.001, horizontal_offset_s=0.0)
    trigger = TriggerConfig(edge="Rising", level_mv=1650.0, pretrigger_ratio=0.0)
    time_ms = np.array([0.0, 0.05, 0.10], dtype=float)
    value_mv = np.array([1600.0, 1700.0, 1800.0], dtype=float)

    point = locate_display_trigger_point(time_ms, value_mv, display, trigger)

    assert point is not None
    assert point.sample_index == 1
    assert point.time_ms == pytest.approx(0.025)


def test_trigger_hysteresis_rejects_level_chatter():
    display = DisplayConfig(time_per_div_s=0.001, horizontal_offset_s=0.0)
    trigger = TriggerConfig(edge="Rising", level_mv=1650.0, hysteresis_mv=15.0)
    time_ms = np.array([0.0, 0.05, 0.10, 0.15], dtype=float)
    value_mv = np.array([1642.0, 1654.0, 1646.0, 1656.0], dtype=float)

    assert locate_display_trigger_point(time_ms, value_mv, display, trigger) is None


def test_pipeline_reference_uses_interpolated_trigger_time():
    display = DisplayConfig(time_per_div_s=0.001, horizontal_offset_s=0.0)
    trigger = TriggerConfig(edge="Rising", level_mv=1650.0, pretrigger_ratio=0.0)
    time_ms = np.array([0.0, 0.05, 0.10], dtype=float)
    value_mv = np.array([1600.0, 1700.0, 1800.0], dtype=float)

    frame = process_scope_frame(time_ms, value_mv, display, trigger)

    assert frame.trigger_state == "TRIG"
    assert frame.trigger_time_ms == pytest.approx(0.025)
    assert frame.reference_time_ms == pytest.approx(0.025)


def test_workspace_trigger_holdoff_reuses_previous_record():
    old_record = RecordView(
        x_s=np.array([0.0]),
        y_mv=np.array([1.0]),
        trigger_x_s=0.0,
        x_left_s=-0.001,
        x_right_s=0.001,
    )
    new_record = RecordView(
        x_s=np.array([0.0]),
        y_mv=np.array([2.0]),
        trigger_x_s=0.0,
        x_left_s=-0.001,
        x_right_s=0.001,
    )
    workspace = ScopeWorkspace.__new__(ScopeWorkspace)
    workspace.trigger_config = TriggerConfig(holdoff_ms=0.5)
    workspace.display_hold_record = old_record
    workspace.display_hold_trigger_time_ms = 10.0

    assert workspace._held_or_new_record(new_record, 10.25, force=False) is old_record
    assert workspace._held_or_new_record(new_record, 10.75, force=False) is new_record
