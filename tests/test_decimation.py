import numpy as np

from pc_app.scope_app.processing.decimation import decimate_for_display


def test_min_max_decimation_keeps_visible_spike():
    x = np.arange(10_000, dtype=float)
    y = np.zeros_like(x)
    y[4321] = 3300.0
    dx, dy = decimate_for_display(x, y, max_points=500)
    assert dx.size <= 500
    assert np.max(dy) == 3300.0
