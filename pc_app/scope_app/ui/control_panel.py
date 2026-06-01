from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from ..core.models import ConnectionConfig, DisplayConfig, SignalConfig
from ..transport.scanner import list_serial_ports


class ControlPanel(QtWidgets.QWidget):
    connect_requested = QtCore.Signal(ConnectionConfig)
    disconnect_requested = QtCore.Signal()
    command_requested = QtCore.Signal(str)
    signal_requested = QtCore.Signal(SignalConfig)
    display_requested = QtCore.Signal(DisplayConfig)
    pause_requested = QtCore.Signal(bool)
    clear_requested = QtCore.Signal()
    export_requested = QtCore.Signal()
    auto_scale_requested = QtCore.Signal()

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

        self.time_div = QtWidgets.QDoubleSpinBox()
        self.time_div.setDecimals(3)
        self.time_div.setRange(0.001, 10.0)
        self.time_div.setSingleStep(0.05)
        self.time_div.setValue(0.1)
        self.volt_div = QtWidgets.QDoubleSpinBox()
        self.volt_div.setDecimals(1)
        self.volt_div.setRange(1.0, 3300.0)
        self.volt_div.setSingleStep(50.0)
        self.volt_div.setValue(500.0)
        self.h_offset = QtWidgets.QDoubleSpinBox()
        self.h_offset.setDecimals(3)
        self.h_offset.setRange(-1000.0, 1000.0)
        self.h_offset.setSingleStep(0.05)
        self.h_offset.setValue(0.0)
        self.v_center = QtWidgets.QDoubleSpinBox()
        self.v_center.setDecimals(1)
        self.v_center.setRange(-3300.0, 6600.0)
        self.v_center.setSingleStep(100.0)
        self.v_center.setValue(1650.0)
        self.auto_range = QtWidgets.QCheckBox("Auto range")
        self.auto_range.setChecked(True)

        connect_btn = QtWidgets.QPushButton("Connect")
        disconnect_btn = QtWidgets.QPushButton("Disconnect")
        start_btn = QtWidgets.QPushButton("Start")
        stop_btn = QtWidgets.QPushButton("Stop")
        apply_btn = QtWidgets.QPushButton("Apply Signal")
        apply_display_btn = QtWidgets.QPushButton("Apply Display")
        pause_btn = QtWidgets.QPushButton("Pause / Resume")
        clear_btn = QtWidgets.QPushButton("Clear Buffer")
        export_btn = QtWidgets.QPushButton("Export CSV")
        autoscale_btn = QtWidgets.QPushButton("Auto Scale Now")

        connect_btn.clicked.connect(self._connect)
        disconnect_btn.clicked.connect(self.disconnect_requested.emit)
        start_btn.clicked.connect(lambda: self.command_requested.emit("START"))
        stop_btn.clicked.connect(lambda: self.command_requested.emit("STOP"))
        apply_btn.clicked.connect(self._apply_signal)
        apply_display_btn.clicked.connect(self._apply_display)
        pause_btn.setCheckable(True)
        pause_btn.toggled.connect(self.pause_requested.emit)
        clear_btn.clicked.connect(self.clear_requested.emit)
        export_btn.clicked.connect(self.export_requested.emit)
        autoscale_btn.clicked.connect(self.auto_scale_requested.emit)

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

        display_form = QtWidgets.QFormLayout()
        display_form.addRow("Time / div (s)", self.time_div)
        display_form.addRow("Volt / div (mV)", self.volt_div)
        display_form.addRow("H Offset (s)", self.h_offset)
        display_form.addRow("V Center (mV)", self.v_center)
        display_form.addRow("", self.auto_range)
        layout.addWidget(self._section("Display", display_form))
        layout.addWidget(apply_display_btn)
        layout.addWidget(autoscale_btn)
        layout.addWidget(pause_btn)
        layout.addWidget(clear_btn)
        layout.addWidget(export_btn)
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

    def _apply_display(self) -> None:
        self.display_requested.emit(
            DisplayConfig(
                time_per_div_s=self.time_div.value(),
                volt_per_div_mv=self.volt_div.value(),
                horizontal_offset_s=self.h_offset.value(),
                vertical_center_mv=self.v_center.value(),
                auto_range=self.auto_range.isChecked(),
            )
        )

    def set_display_values(self, config: DisplayConfig) -> None:
        self.time_div.setValue(config.time_per_div_s)
        self.volt_div.setValue(config.volt_per_div_mv)
        self.h_offset.setValue(config.horizontal_offset_s)
        self.v_center.setValue(config.vertical_center_mv)
        self.auto_range.setChecked(config.auto_range)
