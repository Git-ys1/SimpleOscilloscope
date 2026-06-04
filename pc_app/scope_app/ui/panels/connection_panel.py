from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from ...core.models import ConnectionConfig, DeviceIdentity
from ...transport.scanner import list_serial_ports
from ..i18n import t


class ConnectionPanel(QtWidgets.QWidget):
    connect_requested = QtCore.Signal(ConnectionConfig)
    disconnect_requested = QtCore.Signal()
    format_requested = QtCore.Signal(str)

    def __init__(self, default_source: str, default_baud: int) -> None:
        super().__init__()
        self.source = QtWidgets.QComboBox()
        self.source.setEditable(True)
        self.source.addItems([default_source, "fake://sine", "fake://square", "fake://noise", "tcp://127.0.0.1:8765", "COM14"])
        self.source.setCurrentText(default_source)

        self.baud = QtWidgets.QSpinBox()
        self.baud.setRange(1200, 2_000_000)
        self.baud.setValue(default_baud)

        self.protocol_format = QtWidgets.QComboBox()
        self.protocol_format.addItem("BINARY", "BINARY")
        self.protocol_format.addItem("ASCII", "ASCII")

        self.protocol_status = QtWidgets.QLabel(f"{t('protocol')}: --")
        self.device_id = QtWidgets.QLabel("设备: --")
        self.device_id.setWordWrap(True)

        connect_btn = QtWidgets.QPushButton(t("connect"))
        connect_btn.setObjectName("primaryButton")
        disconnect_btn = QtWidgets.QPushButton(t("disconnect"))
        scan_btn = QtWidgets.QPushButton(t("scan_ports"))
        apply_format_btn = QtWidgets.QPushButton(t("apply_protocol"))

        connect_btn.clicked.connect(self._connect)
        disconnect_btn.clicked.connect(self.disconnect_requested.emit)
        scan_btn.clicked.connect(self.scan_ports)
        apply_format_btn.clicked.connect(lambda: self.format_requested.emit(str(self.protocol_format.currentData())))

        form = QtWidgets.QFormLayout()
        form.addRow(t("source"), self.source)
        form.addRow(t("baudrate"), self.baud)
        form.addRow(t("protocol"), self.protocol_format)

        buttons = QtWidgets.QGridLayout()
        buttons.addWidget(connect_btn, 0, 0)
        buttons.addWidget(disconnect_btn, 0, 1)
        buttons.addWidget(scan_btn, 1, 0)
        buttons.addWidget(apply_format_btn, 1, 1)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(buttons)
        layout.addWidget(self.protocol_status)
        layout.addWidget(self.device_id)

        self.scan_ports()

    def scan_ports(self) -> None:
        current = self.source.currentText()
        for port in list_serial_ports():
            if self.source.findText(port) < 0:
                self.source.addItem(port)
        self.source.setCurrentText(current)

    def set_source(self, source: str) -> None:
        self.source.setCurrentText(source)

    def set_protocol(self, protocol: str) -> None:
        protocol = protocol.upper()
        self.protocol_status.setText(f"{t('protocol')}: {protocol}")
        index = self.protocol_format.findData(protocol)
        if index >= 0:
            self.protocol_format.setCurrentIndex(index)

    def set_device_identity(self, identity: DeviceIdentity | None) -> None:
        if identity is None:
            self.device_id.setText("设备: --")
            return
        extra = f" / {identity.output}" if identity.output else ""
        self.device_id.setText(f"设备: {identity.name} {identity.version} ({identity.target}, {identity.transport}{extra})")

    def _connect(self) -> None:
        self.connect_requested.emit(ConnectionConfig(source=self.source.currentText().strip(), baud=self.baud.value()))
