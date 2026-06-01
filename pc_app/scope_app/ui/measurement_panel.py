from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from ..core.models import AcquisitionStats, MeasurementSnapshot
from ..core.units import format_frequency, format_voltage


class MeasurementPanel(QtWidgets.QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.labels: dict[str, QtWidgets.QLabel] = {}
        layout = QtWidgets.QFormLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        for key, label in [
            ("points", "Points"),
            ("vmax", "Vmax"),
            ("vmin", "Vmin"),
            ("vpp", "Vpp"),
            ("avg", "Average"),
            ("rms", "RMS"),
            ("freq", "Measured Freq"),
            ("rate", "Rx Rate"),
            ("lost", "Lost Samples"),
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
        self.labels["rms"].setText(format_voltage(snapshot.v_rms_mv))
        self.labels["freq"].setText(format_frequency(snapshot.frequency_hz))

    def update_stats(self, stats: AcquisitionStats) -> None:
        self.labels["rate"].setText(format_frequency(stats.sample_rate_hz))
        self.labels["lost"].setText(str(stats.lost_samples))
