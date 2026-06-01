from __future__ import annotations

from PySide6 import QtWidgets


class ScopeStatusBar(QtWidgets.QStatusBar):
    def __init__(self) -> None:
        super().__init__()
        self.connection = QtWidgets.QLabel("未连接")
        self.message = QtWidgets.QLabel("")
        self.addWidget(self.connection)
        self.addPermanentWidget(self.message, 1)

    def set_connection(self, text: str) -> None:
        self.connection.setText(text)

    def set_scope_message(self, text: str) -> None:
        self.message.setText(text)
