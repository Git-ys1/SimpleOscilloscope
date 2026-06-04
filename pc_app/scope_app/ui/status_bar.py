from __future__ import annotations

from PySide6 import QtWidgets

from ..core.models import AcquisitionStats
from . import theme


class ScopeStatusBar(QtWidgets.QStatusBar):
    def __init__(self) -> None:
        super().__init__()
        self.source = QtWidgets.QLabel("数据源: --")
        self.protocol = QtWidgets.QLabel("协议: --")
        self.run_state = QtWidgets.QLabel("STOP")
        self.sample_rate = QtWidgets.QLabel("采样率: --")
        self.fps = QtWidgets.QLabel("帧率: --")
        self.blocks = QtWidgets.QLabel("数据块: --")
        self.dropped = QtWidgets.QLabel("丢包: 0")
        self.message = QtWidgets.QLabel("")
        for label in [self.source, self.protocol, self.run_state, self.sample_rate, self.fps, self.blocks, self.dropped]:
            self.addWidget(label)
        self.addPermanentWidget(self.message, 1)

    def set_source(self, text: str) -> None:
        self.source.setText(f"数据源: {text or '--'}")

    def set_protocol(self, text: str) -> None:
        self.protocol.setText(f"协议: {text or '--'}")

    def set_run_state(self, text: str) -> None:
        state = text.upper()
        self.run_state.setText(state)
        color = {
            "RUN": theme.RUN,
            "RUNNING": theme.RUN,
            "STOP": theme.STOP,
            "STOPPED": theme.STOP,
            "WAIT": theme.WAIT,
            "TRIG": theme.TRIGGER,
            "ERROR": theme.ERROR,
        }.get(state, theme.TEXT)
        self.run_state.setStyleSheet(f"font-weight: 700; color: {color};")

    def set_stats(self, stats: AcquisitionStats) -> None:
        self.sample_rate.setText(f"采样率: {stats.sample_rate_hz:.1f} Hz")
        self.fps.setText(f"帧率: {stats.frames_per_second:.1f}")
        self.blocks.setText(f"数据块: {stats.received_blocks}")
        self.dropped.setText(f"丢包: {stats.lost_samples}")

    def set_scope_message(self, text: str) -> None:
        self.message.setText(text)
