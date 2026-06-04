from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from ...core.models import MeasurementSnapshot
from ...core.units import format_frequency, format_voltage


class MeasurementPanel(QtWidgets.QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.labels: dict[str, QtWidgets.QLabel] = {}
        self.source = QtWidgets.QComboBox()
        self.source.addItems(["当前屏幕", "完整缓存", "最近触发记录"])

        layout = QtWidgets.QFormLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addRow("来源", self.source)
        for key, label in [
            ("vmax", "最大值"),
            ("vmin", "最小值"),
            ("vpp", "峰峰值 Vpp"),
            ("avg", "平均值"),
            ("rms_dc", "Vrms DC"),
            ("rms_ac", "Vrms AC"),
            ("freq", "频率"),
            ("period", "周期"),
            ("duty", "占空比"),
            ("points", "采样点数"),
        ]:
            value = QtWidgets.QLabel("--")
            value.setTextInteractionFlags(value.textInteractionFlags() | QtCore.Qt.TextSelectableByMouse)
            self.labels[key] = value
            layout.addRow(label, value)

    def update_measurements(self, snapshot: MeasurementSnapshot) -> None:
        self.labels["points"].setText(str(snapshot.points))
        self.labels["vmax"].setText(format_voltage(snapshot.v_max_mv))
        self.labels["vmin"].setText(format_voltage(snapshot.v_min_mv))
        self.labels["vpp"].setText(format_voltage(snapshot.v_pp_mv))
        self.labels["avg"].setText(format_voltage(snapshot.v_avg_mv))
        self.labels["rms_dc"].setText(format_voltage(snapshot.v_rms_dc_mv))
        self.labels["rms_ac"].setText(format_voltage(snapshot.v_rms_ac_mv))
        self.labels["freq"].setText(format_frequency(snapshot.frequency_hz))
        self.labels["period"].setText(f"{snapshot.period_ms:.3g} ms" if snapshot.period_ms else "--")
        self.labels["duty"].setText(f"{snapshot.duty_cycle_percent:.1f}%" if snapshot.duty_cycle_percent else "--")
