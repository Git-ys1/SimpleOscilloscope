from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from ..core.models import MeasurementSnapshot
from ..core.units import format_frequency, format_voltage
from . import theme


class MeasurementPanel(QtWidgets.QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.labels: dict[str, QtWidgets.QLabel] = {}
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(16)
        for key, label in [
            ("vpp", "峰峰值 Vpp"),
            ("vmax", "最大值"),
            ("vmin", "最小值"),
            ("avg", "平均值"),
            ("rms_dc", "RMS DC"),
            ("rms_ac", "RMS AC"),
            ("freq", "频率"),
            ("duty", "占空比"),
            ("points", "点数"),
        ]:
            item = QtWidgets.QWidget()
            item_layout = QtWidgets.QVBoxLayout(item)
            item_layout.setContentsMargins(0, 0, 0, 0)
            name = QtWidgets.QLabel(label)
            name.setStyleSheet(f"color: {theme.TEXT_MUTED}; font-size: 8pt;")
            value = QtWidgets.QLabel("--")
            value.setStyleSheet("font-weight: 600;")
            value.setTextInteractionFlags(value.textInteractionFlags() | QtCore.Qt.TextSelectableByMouse)
            self.labels[key] = value
            item_layout.addWidget(name)
            item_layout.addWidget(value)
            layout.addWidget(item)
        layout.addStretch(1)

    def update_measurements(self, snapshot: MeasurementSnapshot) -> None:
        self.labels["points"].setText(str(snapshot.points))
        self.labels["vmax"].setText(format_voltage(snapshot.v_max_mv))
        self.labels["vmin"].setText(format_voltage(snapshot.v_min_mv))
        self.labels["vpp"].setText(format_voltage(snapshot.v_pp_mv))
        self.labels["avg"].setText(format_voltage(snapshot.v_avg_mv))
        self.labels["rms_dc"].setText(format_voltage(snapshot.v_rms_dc_mv))
        self.labels["rms_ac"].setText(format_voltage(snapshot.v_rms_ac_mv))
        self.labels["freq"].setText(format_frequency(snapshot.frequency_hz))
        self.labels["duty"].setText(f"{snapshot.duty_cycle_percent:.1f}%" if snapshot.duty_cycle_percent else "--")
