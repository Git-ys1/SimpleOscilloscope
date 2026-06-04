import numpy as np
import pytest

from pc_app.scope_app.core.models import DisplayConfig, TriggerConfig
from pc_app.scope_app.processing.autoset import autoset_from_waveform
from pc_app.scope_app.processing.record_view import build_record_view, x_range_for_display


def test_autoset_uses_scope_timebase_for_1khz_waveform():
    time_s = np.arange(0.0, 0.01, 1.0 / 20_000.0)
    voltage_mv = 1650.0 + 1200.0 * np.sin(2.0 * np.pi * 1000.0 * time_s)

    result = autoset_from_waveform(time_s, voltage_mv)

    assert result.measurements.frequency_hz == pytest.approx(1000.0, rel=0.03)
    assert result.display.time_per_div_s == pytest.approx(200e-6)
    assert result.display.auto_range is False
    assert result.trigger.level_mv == pytest.approx(1650.0, abs=5.0)
    assert result.trigger.pretrigger_ratio == 0.5


def test_triggered_record_view_is_centered_around_trigger():
    display = DisplayConfig(time_per_div_s=0.001, horizontal_offset_s=0.0)
    trigger = TriggerConfig(pretrigger_ratio=0.5)
    time_ms = np.linspace(95.0, 105.0, 1001)
    value_mv = np.full_like(time_ms, 1650.0)

    record = build_record_view(time_ms, value_mv, display, trigger, reference_time_ms=100.0, trigger_x_s=0.0)

    assert x_range_for_display(display, trigger) == pytest.approx((-0.005, 0.005))
    assert record.x_left_s == pytest.approx(-0.005)
    assert record.x_right_s == pytest.approx(0.005)
    assert np.min(record.x_s) >= -0.005
    assert np.max(record.x_s) <= 0.005
    assert record.trigger_x_s == 0.0
