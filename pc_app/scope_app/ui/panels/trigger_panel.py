from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from ...core.models import TriggerConfig
from ..i18n import t


class TriggerPanel(QtWidgets.QWidget):
    trigger_requested = QtCore.Signal(TriggerConfig)
    trigger_rearm_requested = QtCore.Signal()

    def __init__(self) -> None:
        super().__init__()
        self.mode = QtWidgets.QComboBox()
        for label, value in [("自动", "Auto"), ("普通", "Normal"), ("单次", "Single")]:
            self.mode.addItem(label, value)
        self.edge = QtWidgets.QComboBox()
        self.edge.addItem("上升沿", "Rising")
        self.edge.addItem("下降沿", "Falling")
        self.source = QtWidgets.QComboBox()
        self.source.addItem("CH1", "CH1")
        self.level = QtWidgets.QDoubleSpinBox()
        self.level.setDecimals(1)
        self.level.setRange(-3300.0, 6600.0)
        self.level.setSingleStep(100.0)
        self.level.setValue(1650.0)
        self.pretrigger = QtWidgets.QComboBox()
        for percent in [0, 20, 50, 75]:
            self.pretrigger.addItem(f"{percent}%", percent / 100.0)
        self.pretrigger.setCurrentIndex(2)
        self.state = QtWidgets.QLabel("FREE")

        apply_btn = QtWidgets.QPushButton(t("apply_trigger"))
        rearm_btn = QtWidgets.QPushButton(t("rearm_single"))
        apply_btn.clicked.connect(self._apply_trigger)
        rearm_btn.clicked.connect(self.trigger_rearm_requested.emit)

        form = QtWidgets.QFormLayout()
        form.addRow(t("mode"), self.mode)
        form.addRow(t("edge"), self.edge)
        form.addRow(t("source"), self.source)
        form.addRow(f"{t('level')} mV", self.level)
        form.addRow(t("pretrigger"), self.pretrigger)
        form.addRow(t("state"), self.state)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(apply_btn)
        layout.addWidget(rearm_btn)

    def set_trigger_state(self, state: str) -> None:
        self.state.setText(state)

    def set_trigger_values(self, config: TriggerConfig) -> None:
        mode_index = self.mode.findData(config.mode)
        if mode_index >= 0:
            self.mode.setCurrentIndex(mode_index)
        edge_index = self.edge.findData(config.edge)
        if edge_index >= 0:
            self.edge.setCurrentIndex(edge_index)
        self.level.setValue(config.level_mv)
        pre_index = self.pretrigger.findData(config.pretrigger_ratio)
        if pre_index >= 0:
            self.pretrigger.setCurrentIndex(pre_index)

    def _apply_trigger(self) -> None:
        self.trigger_requested.emit(
            TriggerConfig(
                mode=str(self.mode.currentData()),
                edge=str(self.edge.currentData()),
                level_mv=self.level.value(),
                pretrigger_ratio=float(self.pretrigger.currentData()),
            )
        )
