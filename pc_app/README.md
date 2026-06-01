# SimpleScope PC

`SimpleScope PC` 是本项目的上位机应用。v0.2.1 起，它从 Tkinter 单脚本升级为 `PySide6 + PyQtGraph + NumPy + pySerial` 的分层桌面应用。

## 分层目标

- Transport：串口、TCP、`fake://` 本地假数据源。
- Protocol：兼容当前 `OSC,...` ASCII 协议，预留高速二进制协议。
- Acquisition：后台读取、状态机、接收统计、丢样统计。
- Waveform Model：NumPy 环形缓冲。
- Processing：测量、显示降采样、后续触发和滤波。
- UI：主窗口、波形视图、控制面板、测量面板、状态栏。

## 当前示波器操作

v0.3.0 起，上位机具备基础示波器显示控制：

- `Time / div`：设置水平时基。
- `Volt / div`：设置垂直量程。
- `H Offset`：水平位置。
- `V Center`：垂直中心。
- `Auto range` / `Auto Scale Now`：自动量程。
- `Pause / Resume`：暂停或恢复显示刷新，采集缓冲仍可继续接收。
- `Clear Buffer`：清空当前波形缓存。
- `Export CSV`：导出当前环形缓冲里的波形数据。

v0.4.0 起，加入触发系统：

- `Mode`：`Auto` 持续刷新，`Normal` 等待触发，`Single` 捕获一次后保持。
- `Edge`：上升沿或下降沿。
- `Level mV`：触发电平。
- `Pre-trigger %`：触发点在屏幕内的预触发位置。
- `Re-arm Single`：重新武装单次触发。

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
