# SimpleScope PC

`SimpleScope PC` 是本项目的上位机应用。v0.2.1 起，它从 Tkinter 单脚本升级为 `PySide6 + PyQtGraph + NumPy + pySerial` 的分层桌面应用。v0.9.1 起，普通用户优先使用 Windows 便携版或安装包，开发者仍可从仓库根目录通过 `tools\run_scope.bat` 或 `simplescope-pc` 启动。v0.9.3 起，界面切换到锁定画布的中文示波器面板，读数固定悬浮，并支持触发居中显示、1 kHz 测试信号、20 kSa/s 默认采样和采样质量提示。v0.9.5 起，交付 README、截图和发布验证材料按课程提交要求整理。

## 分层目标

- Transport：串口、TCP、`fake://` 本地假数据源。
- Protocol：ASCII 命令/状态解析、混合流解码，以及高速二进制采样块协议。
- Acquisition：后台读取、状态机、接收统计、丢样统计。
- Waveform Model：NumPy 环形缓冲。
- Processing：测量、显示降采样、后续触发和滤波。
- UI：主窗口、波形视图、控制面板、测量面板、状态栏。

## 当前示波器操作

v0.3.0 起，上位机具备基础示波器显示控制：

- `Time / div`：设置水平时基。
- `Volt / div`：设置垂直量程。
- `水平位置`：移动触发记录在屏幕中的水平位置。
- `垂直中心`：设置 CH1 居中电压。
- `自动设置`：自动估算时基、垂直档位和触发电平。
- `暂停 / 继续`：暂停期间样本不会进入显示缓冲，恢复后从新数据继续，避免长时间线段回放。
- `清空缓存`：清空当前波形缓存。
- `导出 CSV`：导出当前环形缓冲里的波形数据。

v0.4.0 起，加入触发系统：

- `模式`：`Auto` 持续刷新，`Normal` 等待触发，`Single` 捕获一次后保持。
- `边沿`：上升沿或下降沿。
- `电平 mV`：触发电平。
- `预触发`：触发点在屏幕内的位置，默认 50%。
- `重装单次`：重新武装单次触发。

v0.5.0 起，上位机数据层支持采样块；v0.6.0 起，常用操作界面中文化，控制区和测量区使用可滚动侧栏，避免窗口高度不足时控件不可见；v0.7.0 起，固件、模拟器、`fake://` 和上位机采集链路默认使用二进制采样块：

- `SampleBlock`：表示一帧多点、多通道数据。
- `RecordConfig`：预留采样率、记录长度、触发位置。
- `BinaryProtocol`：构建和解析高速二进制 DATA 帧。
- `ProtocolStreamDecoder`：在同一串口/TCP 流中自动识别 ASCII 行和二进制帧。
- `WaveformRingBuffer.append_block()`：支持把采样块写入现有显示缓冲。
- `SET FORMAT ASCII` / `SET FORMAT BINARY`：保留现场切换和调试入口。

## 普通用户启动

从发布页下载：

- `SimpleScopePC-0.9.5-win64-portable.zip`：解压后运行 `SimpleScopePC.exe`。
- `SimpleScopePC-0.9.5-Setup.exe`：安装后从开始菜单启动。

## 开发者启动

从仓库根目录执行：

```bat
tools\setup_pc_env.bat
.venv\python.exe -m pip install -e .[dev]
tools\run_scope.bat --source fake://sine --connect
```

安装 editable 包后也可以执行：

```bat
simplescope-pc --source fake://sine --connect
```

连接真实 CH340 串口：

```bat
tools\run_scope.bat --source COM14 --baud 921600 --connect
```

连接 TCP 下位机模拟器时，上位机入口仍然不变，只是先另开终端启动模拟器：

```bat
python simulator\mcu_simulator.py
tools\run_scope.bat --source tcp://127.0.0.1:8765 --connect
```

## 打包

```bat
tools\build_portable.bat
tools\package_portable_zip.bat
tools\build_installer.bat
```

产物：

- `dist\SimpleScopePC\SimpleScopePC.exe`
- `dist\SimpleScopePC-0.9.5-win64-portable.zip`
- `dist\installer\SimpleScopePC-0.9.5-Setup.exe`

安装包构建需要本机已安装 Inno Setup。
