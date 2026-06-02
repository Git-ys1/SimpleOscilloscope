from __future__ import annotations

from PySide6 import QtWidgets

from ..core.models import AcquisitionStats


class ScopeStatusBar(QtWidgets.QStatusBar):
    def __init__(self) -> None:
        super().__init__()
        self.source = QtWidgets.QLabel("Source: --")
        self.protocol = QtWidgets.QLabel("Protocol: --")
        self.run_state = QtWidgets.QLabel("STOP")
        self.sample_rate = QtWidgets.QLabel("Fs: --")
        self.fps = QtWidgets.QLabel("FPS: --")
        self.blocks = QtWidgets.QLabel("Blocks: --")
        self.dropped = QtWidgets.QLabel("Dropped: 0")
        self.message = QtWidgets.QLabel("")
        for label in [self.source, self.protocol, self.run_state, self.sample_rate, self.fps, self.blocks, self.dropped]:
            self.addWidget(label)
        self.addPermanentWidget(self.message, 1)

    def set_source(self, text: str) -> None:
        self.source.setText(f"Source: {text or '--'}")

    def set_protocol(self, text: str) -> None:
        self.protocol.setText(f"Protocol: {text or '--'}")

    def set_run_state(self, text: str) -> None:
        state = text.upper()
        self.run_state.setText(state)
        color = {
            "RUN": "#50e3a4",
            "RUNNING": "#50e3a4",
            "STOP": "#ff6b6b",
            "STOPPED": "#ff6b6b",
            "WAIT": "#ffcc66",
            "TRIG": "#ffcc66",
            "ERROR": "#ff5c8a",
        }.get(state, "#d9e2f2")
        self.run_state.setStyleSheet(f"font-weight: 700; color: {color};")

    def set_stats(self, stats: AcquisitionStats) -> None:
        self.sample_rate.setText(f"Fs: {stats.sample_rate_hz:.1f} Hz")
        self.fps.setText(f"FPS: {stats.frames_per_second:.1f}")
        self.blocks.setText(f"Blocks: {stats.received_blocks}")
        self.dropped.setText(f"Dropped: {stats.lost_samples}")

    def set_scope_message(self, text: str) -> None:
        self.message.setText(text)
