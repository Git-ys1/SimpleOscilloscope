from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from ...core.models import TriggerConfig


class TriggerPanel(QtWidgets.QWidget):
    trigger_requested = QtCore.Signal(TriggerConfig)
    trigger_rearm_requested = QtCore.Signal()

    def __init__(self) -> None:
        super().__init__()
        self.mode = QtWidgets.QComboBox()
        for label, value in [("Auto", "Auto"), ("Normal", "Normal"), ("Single", "Single")]:
            self.mode.addItem(label, value)
        self.edge = QtWidgets.QComboBox()
        self.edge.addItem("Rising", "Rising")
        self.edge.addItem("Falling", "Falling")
        self.source = QtWidgets.QComboBox()
        self.source.addItem("CH1", "CH1")
        self.level = QtWidgets.QDoubleSpinBox()
        self.level.setDecimals(1)
        self.level.setRange(-3300.0, 6600.0)
        self.level.setSingleStep(100.0)
        self.level.setValue(1650.0)
        self.pretrigger = QtWidgets.QComboBox()
        for percent in [0, 25, 50, 75]:
            self.pretrigger.addItem(f"{percent}%", percent / 100.0)
        self.pretrigger.setCurrentIndex(1)
        self.state = QtWidgets.QLabel("FREE")

        apply_btn = QtWidgets.QPushButton("Apply Trigger")
        rearm_btn = QtWidgets.QPushButton("Re-arm Single")
        apply_btn.clicked.connect(self._apply_trigger)
        rearm_btn.clicked.connect(self.trigger_rearm_requested.emit)

        form = QtWidgets.QFormLayout()
        form.addRow("Mode", self.mode)
        form.addRow("Edge", self.edge)
        form.addRow("Source", self.source)
        form.addRow("Level mV", self.level)
        form.addRow("Pre-trigger", self.pretrigger)
        form.addRow("State", self.state)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(apply_btn)
        layout.addWidget(rearm_btn)

    def set_trigger_state(self, state: str) -> None:
        self.state.setText(state)

    def _apply_trigger(self) -> None:
        self.trigger_requested.emit(
            TriggerConfig(
                mode=str(self.mode.currentData()),
                edge=str(self.edge.currentData()),
                level_mv=self.level.value(),
                pretrigger_ratio=float(self.pretrigger.currentData()),
            )
        )
