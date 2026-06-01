# SimpleScope PC

`SimpleScope PC` 是本项目的上位机应用。v0.2.1 起，它从 Tkinter 单脚本升级为 `PySide6 + PyQtGraph + NumPy + pySerial` 的分层桌面应用。

## 分层目标

- Transport：串口、TCP、`fake://` 本地假数据源。
- Protocol：兼容当前 `OSC,...` ASCII 协议，预留高速二进制协议。
- Acquisition：后台读取、状态机、接收统计、丢样统计。
- Waveform Model：NumPy 环形缓冲。
- Processing：测量、显示降采样、后续触发和滤波。
- UI：主窗口、波形视图、控制面板、测量面板、状态栏。

## 启动

从仓库根目录执行：

```bat
tools\setup_pc_env.bat
tools\run_scope.bat --source fake://sine --connect
```

连接真实 CH340 串口：

```bat
tools\run_scope.bat --source COM14 --baud 115200 --connect
```

连接 TCP 下位机模拟器：

```bat
python simulator\mcu_simulator.py
tools\run_scope.bat --source tcp://127.0.0.1:8765 --connect
```
