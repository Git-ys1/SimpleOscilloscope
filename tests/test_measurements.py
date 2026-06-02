import numpy as np
import pytest

from pc_app.scope_app.processing.measurements import calculate_measurements


def test_measurement_snapshot_basic_values():
    time_ms = np.array([0, 1, 2, 3], dtype=float)
    value_mv = np.array([1000, 2000, 3000, 2000], dtype=float)
    snapshot = calculate_measurements(time_ms, value_mv)
    assert snapshot.points == 4
    assert snapshot.v_min_mv == 1000
    assert snapshot.v_max_mv == 3000
    assert snapshot.v_pp_mv == 2000


def test_rms_dc_and_ac_are_separated_for_biased_sine():
    time_ms = np.linspace(0, 1000, 1000, endpoint=False)
    value_mv = 1650.0 + 1000.0 * np.sin(2.0 * np.pi * 5.0 * time_ms / 1000.0)
    snapshot = calculate_measurements(time_ms, value_mv)
    assert snapshot.v_rms_dc_mv > 1600.0
    assert snapshot.v_rms_ac_mv == pytest.approx(1000.0 / np.sqrt(2.0), rel=0.02)


def test_square_wave_duty_cycle_is_estimated():
    time_ms = np.arange(0, 1000, dtype=float)
    value_mv = np.where((time_ms % 100) < 25, 3000.0, 1000.0)
    snapshot = calculate_measurements(time_ms, value_mv)
    assert snapshot.duty_cycle_percent == pytest.approx(25.0, abs=1.0)
    assert snapshot.period_ms == pytest.approx(100.0, rel=0.05)
