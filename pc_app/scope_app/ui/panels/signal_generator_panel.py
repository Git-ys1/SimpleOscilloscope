from __future__ import annotations

from PySide6 import QtCore, QtWidgets


class SignalGeneratorPanel(QtWidgets.QWidget):
    signal_requested = QtCore.Signal(str, int, int, int)
    output_command_requested = QtCore.Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.wave = QtWidgets.QComboBox()
        for label, value in [
            ("SINE", "SINE"),
            ("SQUARE", "SQUARE"),
            ("TRI", "TRI"),
            ("SAW", "SAW"),
        ]:
            self.wave.addItem(label, value)
        self.frequency = QtWidgets.QSpinBox()
        self.frequency.setRange(1, 500)
        self.frequency.setValue(5)
        self.amplitude = QtWidgets.QSpinBox()
        self.amplitude.setRange(0, 3300)
        self.amplitude.setValue(1200)
        self.offset = QtWidgets.QSpinBox()
        self.offset.setRange(0, 3300)
        self.offset.setValue(1650)

        apply_btn = QtWidgets.QPushButton("Apply")
        start_btn = QtWidgets.QPushButton("Start Output")
        stop_btn = QtWidgets.QPushButton("Stop Output")

        apply_btn.clicked.connect(self._apply_signal)
        start_btn.clicked.connect(lambda: self.output_command_requested.emit("START"))
        stop_btn.clicked.connect(lambda: self.output_command_requested.emit("STOP"))

        form = QtWidgets.QFormLayout()
        form.addRow("Waveform", self.wave)
        form.addRow("Frequency", self.frequency)
        form.addRow("Amplitude mV", self.amplitude)
        form.addRow("Offset mV", self.offset)

        buttons = QtWidgets.QGridLayout()
        buttons.addWidget(apply_btn, 0, 0, 1, 2)
        buttons.addWidget(start_btn, 1, 0)
        buttons.addWidget(stop_btn, 1, 1)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(buttons)

    def _apply_signal(self) -> None:
        self.signal_requested.emit(
            str(self.wave.currentData()),
            self.frequency.value(),
            self.amplitude.value(),
            self.offset.value(),
        )
