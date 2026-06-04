from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from ...core.models import AcquisitionStats, DeviceCapabilities
from ..i18n import t


class AcquisitionPanel(QtWidgets.QWidget):
    command_requested = QtCore.Signal(str)
    single_requested = QtCore.Signal()
    clear_requested = QtCore.Signal()
    sample_rate_requested = QtCore.Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self.capabilities = DeviceCapabilities()
        self.sample_rate_preset = QtWidgets.QComboBox()
        for label, value in [
            ("1 kSa/s", 1_000),
            ("2 kSa/s", 2_000),
            ("5 kSa/s", 5_000),
            ("10 kSa/s", 10_000),
            ("20 kSa/s", 20_000),
            (t("custom"), 0),
        ]:
            self.sample_rate_preset.addItem(label, value)
        self.sample_rate_preset.setCurrentIndex(4)
        self.sample_rate_preset.currentIndexChanged.connect(self._apply_rate_preset)

        self.sample_rate = QtWidgets.QSpinBox()
        self.sample_rate.setRange(self.capabilities.rate_min, self.capabilities.rate_max)
        self.sample_rate.setValue(20_000)
        self.record_length = QtWidgets.QSpinBox()
        self.record_length.setRange(128, 200_000)
        self.record_length.setSingleStep(128)
        self.record_length.setValue(4096)
        self.channel_ch1 = QtWidgets.QCheckBox("CH1")
        self.channel_ch1.setChecked(True)
        self.channel_ch2 = QtWidgets.QCheckBox("CH2 预留")
        self.channel_ch2.setEnabled(False)
        self.actual_rate = QtWidgets.QLabel("--")
        self.block_count = QtWidgets.QLabel("--")
        self.block_points = QtWidgets.QLabel(str(self.capabilities.block_points))
        self.dropped = QtWidgets.QLabel("--")
        self.rx_rate = QtWidgets.QLabel("--")

        run_btn = QtWidgets.QPushButton(t("run"))
        run_btn.setObjectName("primaryButton")
        stop_btn = QtWidgets.QPushButton(t("stop"))
        single_btn = QtWidgets.QPushButton(t("single"))
        clear_btn = QtWidgets.QPushButton(t("clear_buffer"))
        apply_rate_btn = QtWidgets.QPushButton(t("apply_sample_rate"))

        run_btn.clicked.connect(lambda: self.command_requested.emit("START"))
        stop_btn.clicked.connect(lambda: self.command_requested.emit("STOP"))
        single_btn.clicked.connect(self.single_requested.emit)
        clear_btn.clicked.connect(self.clear_requested.emit)
        apply_rate_btn.clicked.connect(lambda: self.sample_rate_requested.emit(self.sample_rate.value()))

        buttons = QtWidgets.QGridLayout()
        buttons.addWidget(run_btn, 0, 0)
        buttons.addWidget(stop_btn, 0, 1)
        buttons.addWidget(single_btn, 1, 0)
        buttons.addWidget(clear_btn, 1, 1)

        form = QtWidgets.QFormLayout()
        form.addRow(t("preset"), self.sample_rate_preset)
        form.addRow(t("sample_rate"), self.sample_rate)
        form.addRow(t("record_length"), self.record_length)
        form.addRow(t("channel_enable"), self.channel_ch1)
        form.addRow("", self.channel_ch2)
        form.addRow(t("actual_fs"), self.actual_rate)
        form.addRow(t("blocks"), self.block_count)
        form.addRow(t("block_points"), self.block_points)
        form.addRow(t("rx_fps"), self.rx_rate)
        form.addRow(t("dropped"), self.dropped)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(buttons)
        layout.addLayout(form)
        layout.addWidget(apply_rate_btn)

    def set_stats(self, stats: AcquisitionStats) -> None:
        self.actual_rate.setText(f"{stats.sample_rate_hz:.1f} Hz")
        self.block_count.setText(str(stats.received_blocks))
        self.rx_rate.setText(f"{stats.frames_per_second:.1f} fps")
        self.dropped.setText(str(stats.lost_samples))

    def set_sample_rate(self, sample_rate_hz: int) -> None:
        self.sample_rate.setValue(sample_rate_hz)

    def set_capabilities(self, capabilities: DeviceCapabilities) -> None:
        self.capabilities = capabilities
        self.sample_rate.setRange(capabilities.rate_min, capabilities.rate_max)
        self.block_points.setText(str(capabilities.block_points))
        for index in range(self.sample_rate_preset.count()):
            value = int(self.sample_rate_preset.itemData(index))
            enabled = value == 0 or capabilities.rate_min <= value <= capabilities.rate_max
            self.sample_rate_preset.model().item(index).setEnabled(enabled)

    def _apply_rate_preset(self) -> None:
        value = int(self.sample_rate_preset.currentData())
        if value > 0:
            self.sample_rate.setValue(value)
