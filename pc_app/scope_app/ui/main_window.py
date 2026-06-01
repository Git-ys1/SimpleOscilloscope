from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from .. import __version__
from ..acquisition.controller import AcquisitionController
from ..core.models import DisplayConfig, TriggerConfig
from ..core.ring_buffer import WaveformRingBuffer
from ..processing.measurements import calculate_measurements
from ..processing.trigger import TriggerMode, locate_trigger, triggered_reference_time_ms, trigger_marker_x_s
from ..storage.export_csv import export_csv
from .control_panel import ControlPanel
from .measurement_panel import MeasurementPanel
from .status_bar import ScopeStatusBar
from .waveform_view import WaveformView


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, default_source: str, default_baud: int) -> None:
        super().__init__()
        self.setWindowTitle(f"SimpleScope PC v{__version__}")
        self.setMinimumSize(980, 600)
        self.controller = AcquisitionController()
        self.buffer = WaveformRingBuffer()
        self.display_config = DisplayConfig()
        self.trigger_config = TriggerConfig()
        self.single_hold: tuple[float, float] | None = None
        self.paused = False

        self.controls = ControlPanel(default_source, default_baud)
        self.waveform = WaveformView()
        self.measurements = MeasurementPanel()
        self.status = ScopeStatusBar()
        self.setStatusBar(self.status)

        control_scroll = self._scroll_area(self.controls, minimum_width=320)
        measurement_scroll = self._scroll_area(self.measurements, minimum_width=240)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        splitter.addWidget(control_scroll)
        splitter.addWidget(self.waveform)
        splitter.addWidget(measurement_scroll)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        splitter.setSizes([330, 820, 260])
        self.setCentralWidget(splitter)

        self.controls.connect_requested.connect(self._connect_config)
        self.controls.disconnect_requested.connect(self.disconnect_source)
        self.controls.command_requested.connect(self.controller.send)
        self.controls.format_requested.connect(self._set_protocol_format)
        self.controls.signal_requested.connect(self.controller.apply_signal)
        self.controls.display_requested.connect(self._set_display_config)
        self.controls.pause_requested.connect(self._set_paused)
        self.controls.clear_requested.connect(self._clear_buffer)
        self.controls.export_requested.connect(self._export_csv)
        self.controls.auto_scale_requested.connect(self._auto_scale)
        self.controls.trigger_requested.connect(self._set_trigger_config)
        self.controls.trigger_rearm_requested.connect(self._rearm_single)

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(33)
        self.timer.timeout.connect(self._drain_events)
        self.timer.start()

        self._apply_theme()
        self.waveform.set_display_config(self.display_config)

    def connect_to_source(self) -> None:
        self.controls._connect()

    def disconnect_source(self) -> None:
        self.controller.disconnect()
        self.status.set_connection("未连接")

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt API
        self.controller.disconnect()
        super().closeEvent(event)

    def _connect_config(self, config) -> None:
        try:
            self.buffer.clear()
            self.controller.connect(config)
            self.status.set_connection(f"已连接：{config.source}")
        except Exception as exc:  # noqa: BLE001 - user-facing status
            self.status.set_connection("连接失败")
            self.status.set_scope_message(str(exc))

    def _drain_events(self) -> None:
        redraw = False
        for kind, payload in self.controller.poll_events():
            if kind == "sample":
                if self.paused:
                    continue
                self.buffer.append(payload)
                redraw = True
            elif kind == "block":
                if self.paused:
                    continue
                self.buffer.append_block(payload)
                redraw = True
            elif kind == "stats":
                self.measurements.update_stats(payload)
            elif kind == "error":
                self.status.set_connection("错误")
                self.status.set_scope_message(str(payload))
            elif kind == "frame":
                self.status.set_scope_message(str(payload))
            elif kind == "state":
                self.status.set_connection(str(payload))

        if redraw:
            self._refresh_display()

    def _set_display_config(self, config: DisplayConfig) -> None:
        self.display_config = config
        self.waveform.set_display_config(config)
        self._refresh_display(force=True)

    def _set_protocol_format(self, output_format: str) -> None:
        self.buffer.clear()
        self.single_hold = None
        self.waveform.update_waveform(*self.buffer.arrays()[:2])
        self.controller.send(f"SET FORMAT {output_format}")
        label = "二进制" if output_format == "BINARY" else "文本"
        self.status.set_scope_message(f"已请求切换为{label}数据格式")

    def _set_paused(self, paused: bool) -> None:
        was_paused = self.paused
        self.paused = paused
        if paused:
            self.status.set_scope_message("显示已暂停，暂停期间的采样不会回放")
            return

        if was_paused:
            self.buffer.clear()
            self.single_hold = None
            self.waveform.update_waveform(*self.buffer.arrays()[:2])
            self.measurements.update_measurements(calculate_measurements(*self.buffer.arrays()[:2]))
            self.status.set_scope_message("显示已继续，已丢弃暂停期间样本")
            return

        self.status.set_scope_message("显示运行中")

    def _clear_buffer(self) -> None:
        self.buffer.clear()
        self.waveform.update_waveform(*self.buffer.arrays()[:2])
        self.measurements.update_measurements(calculate_measurements(*self.buffer.arrays()[:2]))
        self.single_hold = None
        self.status.set_scope_message("缓冲已清空")

    def _auto_scale(self) -> None:
        time_ms, value_mv, _sequence = self.buffer.arrays()
        config = self.waveform.auto_scale_voltage(value_mv)
        self.display_config = config
        self.controls.set_display_values(config)
        self.waveform.update_waveform(time_ms, value_mv)
        self.status.set_scope_message("垂直量程已自动调整")

    def _set_trigger_config(self, config: TriggerConfig) -> None:
        self.trigger_config = config
        self.single_hold = None
        self.status.set_scope_message(
            f"触发：{self._trigger_mode_label(config.mode)} {self._trigger_edge_label(config.edge)} "
            f"@ {config.level_mv:.1f} mV，预触发 {config.pretrigger_ratio:.0%}"
        )
        self._refresh_display(force=True)

    def _rearm_single(self) -> None:
        self.single_hold = None
        self.status.set_scope_message("单次触发已重新武装")

    def _refresh_display(self, force: bool = False) -> None:
        if self.paused and not force:
            return
        time_ms, value_mv, _sequence = self.buffer.arrays()
        reference = None
        marker_x = None

        if self.trigger_config.mode == TriggerMode.SINGLE and self.single_hold is not None:
            reference, trigger_time = self.single_hold
            marker_x = trigger_marker_x_s(reference, trigger_time)
        else:
            trigger_index = locate_trigger(time_ms, value_mv, self.trigger_config)
            if trigger_index is not None:
                trigger_time = float(time_ms[trigger_index])
                reference = triggered_reference_time_ms(trigger_time, self.display_config, self.trigger_config)
                marker_x = trigger_marker_x_s(reference, trigger_time)
                if self.trigger_config.mode == TriggerMode.SINGLE:
                    self.single_hold = (reference, trigger_time)
                    self.status.set_scope_message("单次触发已捕获")
            elif self.trigger_config.mode == TriggerMode.NORMAL:
                self.status.set_scope_message("等待触发")
                return

        self.waveform.update_waveform(time_ms, value_mv, reference, marker_x)
        self.measurements.update_measurements(calculate_measurements(time_ms, value_mv))

    def _export_csv(self) -> None:
        time_ms, value_mv, _sequence = self.buffer.arrays()
        if time_ms.size == 0:
            self.status.set_scope_message("没有可导出的采样")
            return
        path, _filter = QtWidgets.QFileDialog.getSaveFileName(self, "导出波形 CSV", "waveform.csv", "CSV Files (*.csv)")
        if not path:
            return
        try:
            export_csv(path, time_ms, value_mv)
            self.status.set_scope_message(f"已导出 {path}")
        except Exception as exc:  # noqa: BLE001
            self.status.set_scope_message(f"导出失败：{exc}")

    def _scroll_area(self, widget: QtWidgets.QWidget, minimum_width: int) -> QtWidgets.QScrollArea:
        area = QtWidgets.QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QtWidgets.QFrame.NoFrame)
        area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        area.setWidget(widget)
        area.setMinimumWidth(minimum_width)
        return area

    def _trigger_mode_label(self, mode: str) -> str:
        return {"Auto": "自动", "Normal": "普通", "Single": "单次"}.get(mode, mode)

    def _trigger_edge_label(self, edge: str) -> str:
        return {"Rising": "上升沿", "Falling": "下降沿"}.get(edge, edge)

    def _apply_theme(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background: #101624;
                color: #d9e2f2;
                font-family: Segoe UI, Microsoft YaHei, sans-serif;
                font-size: 10pt;
            }
            QGroupBox {
                border: 1px solid #29344f;
                border-radius: 6px;
                margin-top: 10px;
                padding: 8px;
                font-weight: 600;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
            QLineEdit, QComboBox, QSpinBox {
                background: #0b1020;
                border: 1px solid #34405f;
                border-radius: 4px;
                padding: 4px 6px;
            }
            QPushButton {
                background: #1d2a44;
                border: 1px solid #415477;
                border-radius: 5px;
                padding: 6px 8px;
            }
            QPushButton:hover {
                background: #253858;
            }
            QStatusBar {
                background: #0b1020;
                border-top: 1px solid #29344f;
            }
            """
        )
