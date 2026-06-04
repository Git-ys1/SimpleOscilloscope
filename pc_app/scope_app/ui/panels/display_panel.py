from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from ...core.models import DisplayConfig, DisplayMode
from ..i18n import t


class DisplayPanel(QtWidgets.QWidget):
    display_requested = QtCore.Signal(DisplayConfig)
    auto_scale_requested = QtCore.Signal()
    grid_changed = QtCore.Signal(bool)

    def __init__(self) -> None:
        super().__init__()
        self.mode = QtWidgets.QComboBox()
        for label, value in [
            (DisplayMode.TRIGGERED, DisplayMode.TRIGGERED),
            (DisplayMode.ROLL, DisplayMode.ROLL),
            (DisplayMode.STOPPED, DisplayMode.STOPPED),
        ]:
            self.mode.addItem(label, value)
        self.time_div = QtWidgets.QDoubleSpinBox()
        self.time_div.setDecimals(6)
        self.time_div.setRange(0.000001, 10.0)
        self.time_div.setSingleStep(0.0001)
        self.time_div.setValue(0.0002)
        self.volt_div = QtWidgets.QDoubleSpinBox()
        self.volt_div.setDecimals(1)
        self.volt_div.setRange(1.0, 3300.0)
        self.volt_div.setSingleStep(50.0)
        self.volt_div.setValue(500.0)
        self.h_offset = QtWidgets.QDoubleSpinBox()
        self.h_offset.setDecimals(3)
        self.h_offset.setRange(-1000.0, 1000.0)
        self.h_offset.setSingleStep(0.05)
        self.v_center = QtWidgets.QDoubleSpinBox()
        self.v_center.setDecimals(1)
        self.v_center.setRange(-3300.0, 6600.0)
        self.v_center.setSingleStep(100.0)
        self.v_center.setValue(1650.0)
        self.auto_range = QtWidgets.QCheckBox(t("auto_range"))
        self.auto_range.setChecked(False)
        self.grid = QtWidgets.QCheckBox(t("grid"))
        self.grid.setChecked(True)
        self.theme = QtWidgets.QComboBox()
        self.theme.addItems(["深色", "浅色 预留"])
        self.theme.setCurrentText("深色")
        self.theme.setEnabled(False)

        apply_btn = QtWidgets.QPushButton(t("apply_display"))
        autoscale_btn = QtWidgets.QPushButton(t("autoset"))
        fit_btn = QtWidgets.QPushButton(t("fit_to_screen"))

        apply_btn.clicked.connect(self._apply_display)
        autoscale_btn.clicked.connect(self.auto_scale_requested.emit)
        fit_btn.clicked.connect(self.auto_scale_requested.emit)
        self.grid.toggled.connect(self.grid_changed.emit)

        form = QtWidgets.QFormLayout()
        form.addRow("显示模式", self.mode)
        form.addRow("Time/div", self.time_div)
        form.addRow("Volt/div", self.volt_div)
        form.addRow(t("horizontal"), self.h_offset)
        form.addRow(t("vertical"), self.v_center)
        form.addRow("", self.auto_range)
        form.addRow("", self.grid)
        form.addRow(t("theme"), self.theme)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(apply_btn)
        layout.addWidget(autoscale_btn)
        layout.addWidget(fit_btn)

    def set_display_values(self, config: DisplayConfig) -> None:
        self.time_div.setValue(config.time_per_div_s)
        self.volt_div.setValue(config.volt_per_div_mv)
        self.h_offset.setValue(config.horizontal_offset_s)
        self.v_center.setValue(config.vertical_center_mv)
        self.auto_range.setChecked(config.auto_range)
        index = self.mode.findData(config.display_mode)
        if index >= 0:
            self.mode.setCurrentIndex(index)

    def _apply_display(self) -> None:
        self.display_requested.emit(
            DisplayConfig(
                time_per_div_s=self.time_div.value(),
                volt_per_div_mv=self.volt_div.value(),
                horizontal_offset_s=self.h_offset.value(),
                vertical_center_mv=self.v_center.value(),
                auto_range=self.auto_range.isChecked(),
                display_mode=str(self.mode.currentData()),
            )
        )
