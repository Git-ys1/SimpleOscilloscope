from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from ..core.models import ConnectionConfig, SignalConfig
from ..transport.scanner import list_serial_ports


class ControlPanel(QtWidgets.QWidget):
    connect_requested = QtCore.Signal(ConnectionConfig)
    disconnect_requested = QtCore.Signal()
    command_requested = QtCore.Signal(str)
    signal_requested = QtCore.Signal(SignalConfig)

    def __init__(self, default_source: str, default_baud: int) -> None:
        super().__init__()
        self.source = QtWidgets.QComboBox()
        self.source.setEditable(True)
        self.source.addItems([default_source, "fake://sine", "tcp://127.0.0.1:8765", "COM14"])
        for port in list_serial_ports():
            if self.source.findText(port) < 0:
                self.source.addItem(port)
        self.source.setCurrentText(default_source)

        self.baud = QtWidgets.QSpinBox()
        self.baud.setRange(1200, 2_000_000)
        self.baud.setValue(default_baud)

        self.wave = QtWidgets.QComboBox()
        self.wave.addItems(["SINE", "SQUARE", "TRI", "SAW"])
        self.frequency = QtWidgets.QSpinBox()
        self.frequency.setRange(1, 500)
        self.frequency.setValue(5)
        self.amplitude = QtWidgets.QSpinBox()
        self.amplitude.setRange(0, 3300)
        self.amplitude.setValue(1200)
        self.offset = QtWidgets.QSpinBox()
        self.offset.setRange(0, 3300)
        self.offset.setValue(1650)
        self.rate = QtWidgets.QSpinBox()
        self.rate.setRange(1, 5000)
        self.rate.setValue(100)

        connect_btn = QtWidgets.QPushButton("Connect")
        disconnect_btn = QtWidgets.QPushButton("Disconnect")
        start_btn = QtWidgets.QPushButton("Start")
        stop_btn = QtWidgets.QPushButton("Stop")
        apply_btn = QtWidgets.QPushButton("Apply Signal")

        connect_btn.clicked.connect(self._connect)
        disconnect_btn.clicked.connect(self.disconnect_requested.emit)
        start_btn.clicked.connect(lambda: self.command_requested.emit("START"))
        stop_btn.clicked.connect(lambda: self.command_requested.emit("STOP"))
        apply_btn.clicked.connect(self._apply_signal)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        connection_form = QtWidgets.QFormLayout()
        connection_form.addRow("Source", self.source)
        connection_form.addRow("Baud", self.baud)
        layout.addWidget(self._section("Connection", connection_form))

        buttons = QtWidgets.QGridLayout()
        buttons.addWidget(connect_btn, 0, 0)
        buttons.addWidget(disconnect_btn, 0, 1)
        buttons.addWidget(start_btn, 1, 0)
        buttons.addWidget(stop_btn, 1, 1)
        layout.addLayout(buttons)

        signal_form = QtWidgets.QFormLayout()
        signal_form.addRow("Wave", self.wave)
        signal_form.addRow("Frequency Hz", self.frequency)
        signal_form.addRow("Amplitude mV", self.amplitude)
        signal_form.addRow("Offset mV", self.offset)
        signal_form.addRow("Rate Hz", self.rate)
        layout.addWidget(self._section("Signal Source", signal_form))
        layout.addWidget(apply_btn)
        layout.addStretch(1)

    def _section(self, title: str, form: QtWidgets.QFormLayout) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox(title)
        group.setLayout(form)
        return group

    def _connect(self) -> None:
        self.connect_requested.emit(ConnectionConfig(source=self.source.currentText().strip(), baud=self.baud.value()))

    def _apply_signal(self) -> None:
        self.signal_requested.emit(
            SignalConfig(
                wave=self.wave.currentText(),
                frequency_hz=self.frequency.value(),
                amplitude_mv=self.amplitude.value(),
                offset_mv=self.offset.value(),
                sample_rate_hz=self.rate.value(),
            )
        )
