import numpy as np

from pc_app.scope_app.ui.waveform_view import _catmull_rom_interpolate


def test_sine_display_interpolation_adds_points_without_moving_endpoints():
    x = np.linspace(0.0, 0.001, 6)
    y = 1650.0 + 1200.0 * np.sin(2.0 * np.pi * 1000.0 * x)

    smooth_x, smooth_y = _catmull_rom_interpolate(x, y, samples_per_segment=8)

    assert smooth_x.size > x.size
    assert smooth_x[0] == x[0]
    assert smooth_x[-1] == x[-1]
    assert smooth_y[0] == y[0]
    assert smooth_y[-1] == y[-1]
