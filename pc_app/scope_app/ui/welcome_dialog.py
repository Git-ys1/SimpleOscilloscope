from __future__ import annotations

from PySide6 import QtCore, QtWidgets


class SafetyWelcomeDialog(QtWidgets.QDialog):
    dismissed = QtCore.Signal(bool)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("SimpleScope PC - 接线与安全提示")
        self.setModal(False)
        self.resize(560, 420)
        title = QtWidgets.QLabel("SimpleScope PC - 接线与安全提示")
        title.setStyleSheet("font-size: 16pt; font-weight: 700;")
        text = QtWidgets.QLabel(
            "当前版本默认假设：\n"
            "- MCU：STM32F103C8T6\n"
            "- ADC 输入：PA0 / ADC1_IN0\n"
            "- 串口：USART1 PA9/PA10，经 CH340 连接电脑\n"
            "- 烧录调试：ST-Link SWD，PA13/PA14\n"
            "- ADC 安全输入范围：0V ~ 3.3V\n\n"
            "严禁：\n"
            "- 直接测市电\n"
            "- 输入负电压\n"
            "- 输入超过 3.3V 的电压\n"
            "- 未加分压/保护时测高压电路\n\n"
            "如果要测超过 3.3V 或交流双极性信号，需要模拟前端：\n"
            "- 分压、偏置、限流、钳位保护、AC/DC 耦合"
        )
        text.setWordWrap(True)
        self.hide_next_time = QtWidgets.QCheckBox("不再自动显示")
        ok_btn = QtWidgets.QPushButton("I Understand")
        ok_btn.setObjectName("primaryButton")
        ok_btn.clicked.connect(self._accept)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(text, 1)
        layout.addWidget(self.hide_next_time)
        layout.addWidget(ok_btn, 0, QtCore.Qt.AlignRight)

    def _accept(self) -> None:
        self.dismissed.emit(not self.hide_next_time.isChecked())
        self.accept()
