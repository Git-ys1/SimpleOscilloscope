from __future__ import annotations

import numpy as np
import pyqtgraph as pg

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

    def update_waveform(self, time_ms: np.ndarray, value_mv: np.ndarray) -> None:
        if time_ms.size == 0:
            self._curve.setData([], [])
            return
        x = (time_ms - time_ms[-1]) / 1000.0
        x, y = decimate_for_display(x, value_mv)
        self._curve.setData(x, y)
        self.setXRange(float(x[0]), 0.0, padding=0.01)
