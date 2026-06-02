from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PySide6 import QtCore

from ..core.models import DisplayConfig
from ..processing.decimation import decimate_for_display
from . import theme


class WaveformView(pg.PlotWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setBackground(theme.BACKGROUND)
        self.showGrid(x=True, y=True, alpha=0.34)
        self.setLabel("left", "电压", units="mV")
        self.setLabel("bottom", "时间", units="s")
        self.getPlotItem().setMenuEnabled(False)
        self.getPlotItem().hideButtons()
        self._curve = self.plot([], [], pen=pg.mkPen(theme.CH1, width=2))
        self._zero_line = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen(theme.GRID_MAJOR, width=1))
        self.addItem(self._zero_line)
        self._trigger_line = pg.InfiniteLine(pos=0, angle=90, pen=pg.mkPen(theme.TRIGGER, width=1.5, style=QtCore.Qt.DashLine))
        self._trigger_line.hide()
        self.addItem(self._trigger_line)
        self._channel_label = self._text_item("CH1  500 mV/div  DC  1x", theme.CH1, anchor=(0, 0))
        self._state_label = self._text_item("STOP", theme.STOP, anchor=(1, 0))
        self._timebase_label = self._text_item("100 ms/div  Fs: --  Record: --", theme.TEXT_MUTED, anchor=(0, 1))
        self._empty_label = self._text_item(
            "SimpleScope PC\n\n请选择数据源并连接：\n- fake://sine：无硬件演示\n- COMx：CH340 串口\n- tcp://127.0.0.1:8765：模拟器\n\n安全提示：ADC 输入仅限 0-3.3V",
            theme.TEXT_MUTED,
            anchor=(0.5, 0.5),
        )
        self.setYRange(0, 3300, padding=0.02)
        self._config = DisplayConfig()
        self._sample_rate_hz = 0.0
        self._record_length = 0
        self._run_state = "STOP"
        self._trigger_state = "FREE"

    def set_display_config(self, config: DisplayConfig) -> None:
        self._config = config
        self._update_labels()
        self._apply_ranges()

    def set_status(self, run_state: str, trigger_state: str | None = None) -> None:
        self._run_state = run_state.upper()
        if trigger_state:
            self._trigger_state = trigger_state.upper()
        label = self._trigger_state if self._trigger_state in {"WAIT", "TRIG"} else self._run_state
        color = {
            "RUN": theme.RUN,
            "RUNNING": theme.RUN,
            "STOP": theme.STOP,
            "STOPPED": theme.STOP,
            "WAIT": theme.WAIT,
            "TRIG": theme.TRIGGER,
            "ERROR": theme.ERROR,
        }.get(label, theme.TEXT)
        self._state_label.setText(label)
        self._state_label.setColor(color)

    def set_sample_context(self, sample_rate_hz: float, record_length: int) -> None:
        self._sample_rate_hz = sample_rate_hz
        self._record_length = record_length
        self._update_labels()

    def update_waveform(
        self,
        time_ms: np.ndarray,
        value_mv: np.ndarray,
        reference_time_ms: float | None = None,
        trigger_x_s: float | None = None,
    ) -> None:
        if time_ms.size == 0:
            self._curve.setData([], [])
            self._trigger_line.hide()
            self._empty_label.show()
            self._position_labels()
            return
        self._empty_label.hide()
        reference = float(time_ms[-1] if reference_time_ms is None else reference_time_ms)
        x = (time_ms - reference) / 1000.0
        x, y = decimate_for_display(x, value_mv)
        self._curve.setData(x, y)
        if trigger_x_s is None:
            self._trigger_line.hide()
        else:
            self._trigger_line.setPos(trigger_x_s)
            self._trigger_line.show()
        self._apply_ranges()
        self._position_labels()

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
        bottom_axis = self.getPlotItem().getAxis("bottom")
        left_axis = self.getPlotItem().getAxis("left")
        bottom_axis.setTickSpacing(major=self._config.time_per_div_s, minor=self._config.time_per_div_s / 5.0)
        if self._config.auto_range:
            self.enableAutoRange(axis="y", enable=True)
        else:
            self.enableAutoRange(axis="y", enable=False)
            half_span = max(self._config.volt_per_div_mv * 4.0, 10.0)
            self.setYRange(self._config.vertical_center_mv - half_span, self._config.vertical_center_mv + half_span, padding=0.0)
            left_axis.setTickSpacing(major=self._config.volt_per_div_mv, minor=self._config.volt_per_div_mv / 5.0)
        self._position_labels()

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt API
        super().resizeEvent(event)
        self._position_labels()

    def _text_item(self, text: str, color: str, anchor: tuple[float, float]) -> pg.TextItem:
        item = pg.TextItem(text=text, color=color, anchor=anchor)
        self.addItem(item)
        return item

    def _update_labels(self) -> None:
        self._channel_label.setText(f"CH1  {self._config.volt_per_div_mv:g} mV/div  DC  1x")
        sample = f"Fs: {self._sample_rate_hz:.0f} Hz" if self._sample_rate_hz > 0 else "Fs: --"
        record = f"Record: {self._record_length}" if self._record_length > 0 else "Record: --"
        self._timebase_label.setText(f"{self._config.time_per_div_s:g} s/div  {sample}  {record}")

    def _position_labels(self) -> None:
        if not hasattr(self, "_channel_label"):
            return
        plot_item = self.getPlotItem()
        if plot_item is None:
            return
        view = plot_item.vb.viewRange()
        (x_min, x_max), (y_min, y_max) = view
        x_margin = (x_max - x_min) * 0.018
        y_margin = (y_max - y_min) * 0.045
        self._channel_label.setPos(x_min + x_margin, y_max - y_margin)
        self._state_label.setPos(x_max - x_margin, y_max - y_margin)
        self._timebase_label.setPos(x_min + x_margin, y_min + y_margin)
        self._empty_label.setPos((x_min + x_max) / 2.0, (y_min + y_max) / 2.0)
