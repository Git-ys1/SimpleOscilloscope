from __future__ import annotations

import numpy as np
import pyqtgraph as pg

from ..core.models import DisplayConfig
from ..processing.decimation import decimate_for_display


class WaveformView(pg.PlotWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setBackground("#0b1020")
        self.showGrid(x=True, y=True, alpha=0.28)
        self.setLabel("left", "Voltage", units="mV")
        self.setLabel("bottom", "Time", units="s")
        self.getPlotItem().setMenuEnabled(False)
        self.getPlotItem().hideButtons()
        self._curve = self.plot([], [], pen=pg.mkPen("#50e3a4", width=2))
        self._zero_line = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen("#526386", width=1))
        self.addItem(self._zero_line)
        self.setYRange(0, 3300, padding=0.02)
        self._config = DisplayConfig()

    def set_display_config(self, config: DisplayConfig) -> None:
        self._config = config
        self._apply_ranges()

    def update_waveform(self, time_ms: np.ndarray, value_mv: np.ndarray) -> None:
        if time_ms.size == 0:
            self._curve.setData([], [])
            return
        x = (time_ms - time_ms[-1]) / 1000.0
        x, y = decimate_for_display(x, value_mv)
        self._curve.setData(x, y)
        self._apply_ranges()

    def auto_scale_voltage(self, value_mv: np.ndarray) -> DisplayConfig:
        if value_mv.size == 0:
            return self._config
        v_min = float(np.min(value_mv))
        v_max = float(np.max(value_mv))
        span = max(v_max - v_min, 100.0)
        center = (v_max + v_min) / 2.0
        per_div = max(span / 6.0, 10.0)
        config = DisplayConfig(
            time_per_div_s=self._config.time_per_div_s,
            volt_per_div_mv=per_div,
            horizontal_offset_s=self._config.horizontal_offset_s,
            vertical_center_mv=center,
            auto_range=False,
        )
        self.set_display_config(config)
        return config

    def _apply_ranges(self) -> None:
        time_span = max(self._config.time_per_div_s * 10.0, 0.001)
        right = self._config.horizontal_offset_s
        self.setXRange(right - time_span, right, padding=0.0)
        if self._config.auto_range:
            self.enableAutoRange(axis="y", enable=True)
        else:
            self.enableAutoRange(axis="y", enable=False)
            half_span = max(self._config.volt_per_div_mv * 4.0, 10.0)
            self.setYRange(self._config.vertical_center_mv - half_span, self._config.vertical_center_mv + half_span, padding=0.0)
