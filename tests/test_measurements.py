import numpy as np

from pc_app.scope_app.processing.measurements import calculate_measurements


def test_measurement_snapshot_basic_values():
    time_ms = np.array([0, 1, 2, 3], dtype=float)
    value_mv = np.array([1000, 2000, 3000, 2000], dtype=float)
    snapshot = calculate_measurements(time_ms, value_mv)
    assert snapshot.points == 4
    assert snapshot.v_min_mv == 1000
    assert snapshot.v_max_mv == 3000
    assert snapshot.v_pp_mv == 2000
