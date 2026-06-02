from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from ...core.models import AcquisitionStats


class AcquisitionPanel(QtWidgets.QWidget):
    command_requested = QtCore.Signal(str)
    single_requested = QtCore.Signal()
    clear_requested = QtCore.Signal()
    sample_rate_requested = QtCore.Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self.sample_rate = QtWidgets.QSpinBox()
        self.sample_rate.setRange(1, 1000)
        self.sample_rate.setValue(100)
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
        self.dropped = QtWidgets.QLabel("--")
        self.rx_rate = QtWidgets.QLabel("--")

        run_btn = QtWidgets.QPushButton("Run")
        run_btn.setObjectName("primaryButton")
        stop_btn = QtWidgets.QPushButton("Stop")
        single_btn = QtWidgets.QPushButton("Single")
        clear_btn = QtWidgets.QPushButton("Clear Buffer")
        apply_rate_btn = QtWidgets.QPushButton("Apply Sample Rate")

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
        form.addRow("Sample Rate", self.sample_rate)
        form.addRow("Record Length", self.record_length)
        form.addRow("Channel Enable", self.channel_ch1)
        form.addRow("", self.channel_ch2)
        form.addRow("Actual Fs", self.actual_rate)
        form.addRow("Blocks", self.block_count)
        form.addRow("Rx FPS", self.rx_rate)
        form.addRow("Dropped", self.dropped)

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
