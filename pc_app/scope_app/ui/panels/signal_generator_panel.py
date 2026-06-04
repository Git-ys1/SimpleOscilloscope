from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from ...core.models import DeviceCapabilities
from ..i18n import t


class SignalGeneratorPanel(QtWidgets.QWidget):
    signal_requested = QtCore.Signal(str, int, int, int)
    output_command_requested = QtCore.Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.capabilities = DeviceCapabilities()
        self.wave = QtWidgets.QComboBox()
        for label, value in [
            ("正弦", "SINE"),
            ("方波", "SQUARE"),
            ("三角", "TRI"),
            ("锯齿", "SAW"),
        ]:
            self.wave.addItem(label, value)
        self.frequency_preset = QtWidgets.QComboBox()
        for label, value in [
            ("10 Hz", 10),
            ("50 Hz", 50),
            ("100 Hz", 100),
            ("500 Hz", 500),
            ("1 kHz", 1_000),
            ("2 kHz", 2_000),
            ("5 kHz", 5_000),
            (t("custom"), 0),
        ]:
            self.frequency_preset.addItem(label, value)
        self.frequency_preset.setCurrentIndex(4)
        self.frequency_preset.currentIndexChanged.connect(self._apply_frequency_preset)
        self.frequency = QtWidgets.QSpinBox()
        self.frequency.setRange(self.capabilities.freq_min, self.capabilities.freq_max)
        self.frequency.setValue(1000)
        self.amplitude = QtWidgets.QSpinBox()
        self.amplitude.setRange(0, 3300)
        self.amplitude.setValue(1200)
        self.offset = QtWidgets.QSpinBox()
        self.offset.setRange(0, 3300)
        self.offset.setValue(1650)

        apply_btn = QtWidgets.QPushButton(t("apply"))
        start_btn = QtWidgets.QPushButton(t("start_output"))
        stop_btn = QtWidgets.QPushButton(t("stop_output"))

        apply_btn.clicked.connect(self._apply_signal)
        start_btn.clicked.connect(lambda: self.output_command_requested.emit("START"))
        stop_btn.clicked.connect(lambda: self.output_command_requested.emit("STOP"))

        form = QtWidgets.QFormLayout()
        form.addRow(t("waveform"), self.wave)
        form.addRow(t("preset"), self.frequency_preset)
        form.addRow(t("frequency"), self.frequency)
        form.addRow(f"{t('amplitude')} mV", self.amplitude)
        form.addRow(f"{t('offset')} mV", self.offset)

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

    def set_capabilities(self, capabilities: DeviceCapabilities) -> None:
        self.capabilities = capabilities
        self.frequency.setRange(capabilities.freq_min, capabilities.freq_max)
        for index in range(self.frequency_preset.count()):
            value = int(self.frequency_preset.itemData(index))
            enabled = value == 0 or capabilities.freq_min <= value <= capabilities.freq_max
            self.frequency_preset.model().item(index).setEnabled(enabled)

    def _apply_frequency_preset(self) -> None:
        value = int(self.frequency_preset.currentData())
        if value > 0:
            self.frequency.setValue(value)
