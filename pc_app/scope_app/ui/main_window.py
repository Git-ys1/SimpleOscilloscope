from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from ..acquisition.controller import AcquisitionController
from ..core.ring_buffer import WaveformRingBuffer
from ..processing.measurements import calculate_measurements
from .control_panel import ControlPanel
from .measurement_panel import MeasurementPanel
from .status_bar import ScopeStatusBar
from .waveform_view import WaveformView


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, default_source: str, default_baud: int) -> None:
        super().__init__()
        self.setWindowTitle("SimpleScope PC 0.2.1")
        self.controller = AcquisitionController()
        self.buffer = WaveformRingBuffer()

        self.controls = ControlPanel(default_source, default_baud)
        self.waveform = WaveformView()
        self.measurements = MeasurementPanel()
        self.status = ScopeStatusBar()
        self.setStatusBar(self.status)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        splitter.addWidget(self.controls)
        splitter.addWidget(self.waveform)
        splitter.addWidget(self.measurements)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        splitter.setSizes([260, 760, 260])
        self.setCentralWidget(splitter)

        self.controls.connect_requested.connect(self._connect_config)
        self.controls.disconnect_requested.connect(self.disconnect_source)
        self.controls.command_requested.connect(self.controller.send)
        self.controls.signal_requested.connect(self.controller.apply_signal)

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(33)
        self.timer.timeout.connect(self._drain_events)
        self.timer.start()

        self._apply_theme()

    def connect_to_source(self) -> None:
        self.controls._connect()

    def disconnect_source(self) -> None:
        self.controller.disconnect()
        self.status.set_connection("Disconnected")

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt API
        self.controller.disconnect()
        super().closeEvent(event)

    def _connect_config(self, config) -> None:
        try:
            self.buffer.clear()
            self.controller.connect(config)
            self.status.set_connection(f"Connected: {config.source}")
        except Exception as exc:  # noqa: BLE001 - user-facing status
            self.status.set_connection("Connection failed")
            self.status.set_scope_message(str(exc))

    def _drain_events(self) -> None:
        redraw = False
        for kind, payload in self.controller.poll_events():
            if kind == "sample":
                self.buffer.append(payload)
                redraw = True
            elif kind == "stats":
                self.measurements.update_stats(payload)
            elif kind == "error":
                self.status.set_connection("Error")
                self.status.set_scope_message(str(payload))
            elif kind == "frame":
                self.status.set_scope_message(str(payload))
            elif kind == "state":
                self.status.set_connection(str(payload))

        if redraw:
            time_ms, value_mv, _sequence = self.buffer.arrays()
            self.waveform.update_waveform(time_ms, value_mv)
            self.measurements.update_measurements(calculate_measurements(time_ms, value_mv))

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
