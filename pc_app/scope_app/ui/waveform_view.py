from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PySide6 import QtCore
from PySide6 import QtGui
from PySide6 import QtWidgets

from ..core.models import DisplayConfig, DisplayMode, TriggerConfig
from ..processing.decimation import decimate_for_display
from ..processing.record_view import RecordView, x_range_for_display
from . import theme


class WaveformView(pg.PlotWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setBackground(theme.BACKGROUND)
        self.showGrid(x=True, y=True, alpha=0.34)
        plot_item = self.getPlotItem()
        plot_item.setMenuEnabled(False)
        plot_item.hideButtons()
        plot_item.hideAxis("left")
        plot_item.hideAxis("bottom")
        self.setMouseEnabled(x=False, y=False)
        self.getViewBox().setMouseEnabled(x=False, y=False)
        self.getViewBox().setMenuEnabled(False)
        self._curve = self.plot([], [], pen=pg.mkPen(theme.CH1, width=2.2))
        self._curve.setClipToView(True)
        self._zero_line = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen(theme.GRID_MAJOR, width=1))
        self.addItem(self._zero_line)
        self._trigger_line = pg.InfiniteLine(pos=0, angle=90, pen=pg.mkPen(theme.TRIGGER, width=1.5, style=QtCore.Qt.DashLine))
        self._trigger_line.hide()
        self.addItem(self._trigger_line)
        self._trigger_marker = self._overlay_label("▼", theme.TRIGGER)
        self._trigger_marker.hide()
        self._channel_label = self._overlay_label("CH1  500 mV/div  DC  1x", theme.CH1)
        self._state_label = self._overlay_label("停止", theme.STOP)
        self._timebase_label = self._overlay_label("时基 100 ms/div  采样率 --  深度 --", theme.TEXT_MUTED)
        self._empty_label = self._overlay_label(
            "SimpleScope PC\n\n请选择数据源并连接：\n- fake://sine：无硬件演示\n- COMx：CH340 串口\n- tcp://127.0.0.1:8765：模拟器\n\n安全提示：ADC 输入仅限 0-3.3V",
            theme.TEXT_MUTED,
            align=QtCore.Qt.AlignCenter,
        )
        self.setYRange(0, 3300, padding=0.02)
        self._config = DisplayConfig()
        self._trigger_config = TriggerConfig()
        self._sample_rate_hz = 0.0
        self._record_length = 0
        self._run_state = "STOP"
        self._trigger_state = "FREE"
        self._trace_wave = "SINE"
        self._last_trigger_x_s: float | None = None

    def set_display_config(self, config: DisplayConfig) -> None:
        self._config = config
        self._update_labels()
        self._apply_ranges()

    def set_trigger_config(self, config: TriggerConfig) -> None:
        self._trigger_config = config
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
        self._state_label.setText(
            {
                "RUN": "运行",
                "RUNNING": "运行",
                "STOP": "停止",
                "STOPPED": "停止",
                "WAIT": "等待触发",
                "TRIG": "已触发",
                "ERROR": "错误",
            }.get(label, label)
        )
        self._state_label.setStyleSheet(f"color: {color}; background: transparent;")
        self._state_label.adjustSize()
        self._position_labels()

    def set_sample_context(self, sample_rate_hz: float, record_length: int) -> None:
        self._sample_rate_hz = sample_rate_hz
        self._record_length = record_length
        self._update_labels()

    def set_trace_wave(self, wave: str) -> None:
        self._trace_wave = wave.upper()

    def update_waveform(
        self,
        time_ms,
        value_mv,
        reference_time_ms: float | None = None,
        trigger_x_s: float | None = None,
    ) -> None:
        if time_ms.size == 0:
            self._curve.setData([], [])
            self._trigger_line.hide()
            self._trigger_marker.hide()
            self._empty_label.show()
            self._position_labels()
            return
        self._empty_label.hide()
        reference = float(time_ms[-1] if reference_time_ms is None else reference_time_ms)
        x = (time_ms - reference) / 1000.0
        x, y = self._trace_for_display(x, value_mv)
        self._curve.setData(x, y)
        self._set_trigger_marker(trigger_x_s)
        self._apply_ranges()
        self._position_labels()

    def update_record(self, record: RecordView) -> None:
        if record.x_s.size == 0:
            self._curve.setData([], [])
            self._trigger_line.hide()
            self._trigger_marker.hide()
            self._last_trigger_x_s = None
            self._empty_label.show()
            self._position_labels()
            return
        self._empty_label.hide()
        x, y = self._trace_for_display(record.x_s, record.y_mv)
        self._curve.setData(x, y)
        self._set_trigger_marker(record.trigger_x_s)
        self.setXRange(record.x_left_s, record.x_right_s, padding=0.0)
        self._apply_y_range()
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
        left, right = x_range_for_display(self._config, self._trigger_config)
        self.setXRange(left, right, padding=0.0)
        bottom_axis = self.getPlotItem().getAxis("bottom")
        left_axis = self.getPlotItem().getAxis("left")
        bottom_axis.setTickSpacing(major=self._config.time_per_div_s, minor=self._config.time_per_div_s / 5.0)
        self._apply_y_range()
        self._position_labels()

    def _apply_y_range(self) -> None:
        left_axis = self.getPlotItem().getAxis("left")
        if self._config.auto_range:
            self.enableAutoRange(axis="y", enable=True)
        else:
            self.enableAutoRange(axis="y", enable=False)
            half_span = max(self._config.volt_per_div_mv * 4.0, 10.0)
            self.setYRange(self._config.vertical_center_mv - half_span, self._config.vertical_center_mv + half_span, padding=0.0)
            left_axis.setTickSpacing(major=self._config.volt_per_div_mv, minor=self._config.volt_per_div_mv / 5.0)

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt API
        super().resizeEvent(event)
        self._position_labels()

    def wheelEvent(self, event) -> None:  # noqa: N802 - Qt API
        event.ignore()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802 - Qt API
        event.ignore()

    def mousePressEvent(self, event) -> None:  # noqa: N802 - Qt API
        event.ignore()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 - Qt API
        event.ignore()

    def _overlay_label(
        self,
        text: str,
        color: str,
        align: QtCore.Qt.AlignmentFlag = QtCore.Qt.AlignLeft,
    ) -> QtWidgets.QLabel:
        item = QtWidgets.QLabel(text, self.viewport())
        item.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
        item.setFont(QtGui.QFont(theme.PRIMARY_FONT, 10))
        item.setAlignment(align)
        item.setStyleSheet(f"color: {color}; background: transparent;")
        item.adjustSize()
        item.show()
        return item

    def _update_labels(self) -> None:
        self._channel_label.setText(f"CH1  {self._config.volt_per_div_mv:g} mV/div  DC  1x")
        sample = f"{self._sample_rate_hz:.0f} Sa/s" if self._sample_rate_hz > 0 else "--"
        record = f"{self._record_length} 点" if self._record_length > 0 else "--"
        mode = "滚动" if self._config.display_mode == DisplayMode.ROLL else "触发"
        self._timebase_label.setText(f"时基 {_format_time_div(self._config.time_per_div_s)}/div  采样率 {sample}  深度 {record}  {mode}")
        self._channel_label.adjustSize()
        self._timebase_label.adjustSize()
        self._position_labels()

    def _set_trigger_marker(self, trigger_x_s: float | None) -> None:
        self._last_trigger_x_s = trigger_x_s
        if trigger_x_s is None:
            self._trigger_line.hide()
            self._trigger_marker.hide()
            return
        self._trigger_line.setPos(trigger_x_s)
        self._trigger_line.show()
        self._trigger_marker.show()

    def _position_labels(self) -> None:
        if not hasattr(self, "_channel_label"):
            return
        margin = 34
        top = 46
        bottom = 24
        width = self.viewport().width()
        height = self.viewport().height()
        self._channel_label.move(margin, top)
        self._state_label.adjustSize()
        self._state_label.move(max(margin, width - margin - self._state_label.width()), top)
        self._timebase_label.move(margin, max(top, height - bottom - self._timebase_label.height()))
        self._empty_label.adjustSize()
        self._empty_label.move(
            max(0, (width - self._empty_label.width()) // 2),
            max(0, (height - self._empty_label.height()) // 2),
        )
        if self._last_trigger_x_s is not None:
            left, right = x_range_for_display(self._config, self._trigger_config)
            span = max(right - left, 1e-12)
            ratio = (self._last_trigger_x_s - left) / span
            x = int(max(0.0, min(1.0, ratio)) * width)
            self._trigger_marker.adjustSize()
            self._trigger_marker.move(x - self._trigger_marker.width() // 2, top - 18)

    def _trace_for_display(self, x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        x, y = decimate_for_display(x, y)
        if self._trace_wave == "SINE":
            x, y = _catmull_rom_interpolate(x, y)
        return x, y


def _catmull_rom_interpolate(x: np.ndarray, y: np.ndarray, samples_per_segment: int = 8) -> tuple[np.ndarray, np.ndarray]:
    if x.size < 4 or samples_per_segment <= 1:
        return x, y
    if np.any(np.diff(x) <= 0.0):
        return x, y
    if x.size * samples_per_segment > 8000:
        return x, y

    padded_y = np.concatenate(([y[0]], y, [y[-1]]))
    out_x: list[np.ndarray] = []
    out_y: list[np.ndarray] = []
    t = np.linspace(0.0, 1.0, samples_per_segment, endpoint=False)
    t2 = t * t
    t3 = t2 * t
    for index in range(x.size - 1):
        p0 = padded_y[index]
        p1 = padded_y[index + 1]
        p2 = padded_y[index + 2]
        p3 = padded_y[index + 3]
        segment_x = np.linspace(x[index], x[index + 1], samples_per_segment, endpoint=False)
        segment_y = 0.5 * (
            (2.0 * p1)
            + (-p0 + p2) * t
            + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t2
            + (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * t3
        )
        out_x.append(segment_x)
        out_y.append(segment_y)
    out_x.append(x[-1:])
    out_y.append(y[-1:])
    return np.concatenate(out_x), np.concatenate(out_y)


def _format_time_div(seconds: float) -> str:
    if seconds < 1e-3:
        return f"{seconds * 1e6:g} us"
    if seconds < 1.0:
        return f"{seconds * 1e3:g} ms"
    return f"{seconds:g} s"
