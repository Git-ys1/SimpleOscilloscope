# SimpleScope PC 上位机架构

SimpleScope PC 使用 `PySide6 + PyQtGraph + NumPy + pySerial`。PySide6 负责成熟的桌面窗口、Dock、菜单、对话框和状态栏；PyQtGraph 负责实时波形显示；NumPy 负责采样块、环形缓冲、降采样和测量计算；pySerial 负责 CH340 串口接入。

## 数据流

```text
Transport
  SerialTransport / TcpTransport / FakeTransport
        ↓
Protocol Decoder
  BinaryProtocol / AsciiProtocol / ProtocolStreamDecoder
        ↓
AcquisitionController
  后台线程读取数据，不阻塞 UI
        ↓
SampleFrame / SampleBlock
        ↓
WaveformRingBuffer
  NumPy 块级写入
        ↓
Processing Pipeline
  trigger / measurements / min-max decimation
        ↓
UI
  WaveformView / Dock Panels / Measurement Bar / Status Bar
        ↓
Storage
  CSV export
```

## 目录职责

- `core`：连接配置、采样模型、环形缓冲、设置持久化。
- `transport`：串口、TCP、fake 演示数据源。
- `protocol`：ASCII 命令/状态解析、二进制 DATA 帧、混合流解码。
- `acquisition`：后台采集控制器、采样统计、线程生命周期。
- `processing`：触发、测量、降采样和显示处理链。
- `ui`：主窗口 shell、示波器屏幕、Dock 面板、状态栏、安全提示。
- `storage`：CSV 等导出能力。
- `version.py`：应用名、版本号和组织名的唯一来源。
- `app_paths.py`：运行时资源、日志目录和用户设置目录解析。
- `packaging`：图标、Inno Setup 脚本和发布资产。
- `tools`：开发启动、PyInstaller 便携版、zip 和安装包构建脚本。

## UI 边界

UI 是仪表盘，不是数据源：

- UI 不直接调用 `serial.readline()`。
- UI 不直接 `struct.unpack()` 二进制采样帧。
- UI 不直接阻塞读取数据。
- Demo Mode 也走 `FakeTransport -> ProtocolStreamDecoder -> AcquisitionController`。
- MainWindow 只负责菜单、工具栏、中央屏幕、Dock、状态栏和信号连接。

## v0.9.4 触发稳定性修正

- `processing.trigger` 返回带插值时间的 `TriggerPoint`，触发参考不再被量化到下一个采样点。
- 触发命中加入默认 15 mV 迟滞，减少电平附近的小幅毛刺造成的重复触发。
- `processing.pipeline` 使用插值后的 `trigger_time_ms` 作为记录视图 reference，触发标记仍保持在屏幕中心。
- `ScopeWorkspace` 增加轻量帧保持和 holdoff，短时间内的重复触发不会立刻替换当前显示帧。

## v0.9.3 示波器屏幕修正

- `WaveformView` 禁止鼠标拖拽和滚轮缩放，避免交付演示时误把波形屏幕拉偏。
- CH1 读数、运行/触发状态、底部时基/采样率读数改为固定 QWidget overlay，不再随 PyQtGraph 数据坐标移动。
- 触发处理优先选择已经收齐后触发数据的触发点，避免最新触发刚发生时屏幕右半边没有数据。
- SINE 显示路径会做平滑插值，固件默认采样率提升到 20 kSa/s，正弦查表增加相位内插。

## v0.9.2 示波器体验结构

- 顶部工具栏：`连接`、`运行`、`停止`、`单次`、`自动设置`、`演示`、`导出`。
- 中央示波器屏幕：隐藏普通图表坐标轴，使用触发居中记录视图、CH1 角落读数、中文运行状态、触发线和触发位置标记。
- 右侧 Dock：改为 `连接 / 采集 / 显示 / 触发 / 测量 / 信号源` 页签，避免所有控件堆在一个长滚动面板中。
- 采集页签：采样率使用 `1/2/5/10/20 kSa/s + 自定义`，连接后根据 `CAP?` 返回的设备能力更新范围。
- 信号源页签：频率使用 `10/50/100/500 Hz, 1/2/5 kHz + 自定义`，默认 1 kHz。
- `processing.autoset`：根据波形估算 Vpp、中心电压、频率，选择常用 Time/div 和 Volt/div，同时设置触发电平与 50% 预触发。
- `processing.record_view`：根据 ring buffer、触发结果和显示配置生成屏幕 x/y 数据；`WaveformView` 只负责绘制。
- 状态区会在采样率低于信号频率 10 倍时显示黄色质量提示。

## v0.9.1 UI 和发布结构

- 顶部工具栏：`Connect`、`Run`、`Stop`、`Single`、`AutoSet`、`Demo`、`Export`。
- 中央示波器屏幕：深色背景、10 x 8 主网格、CH1 标签、触发线、RUN/STOP/WAIT/TRIG 状态角标、空状态提示。
- 右侧 Dock：Connection、Acquisition、Display、Trigger、Measurements、Signal Generator。
- 底部测量栏：Vpp、Vmax、Vmin、Avg、RMS DC、RMS AC、Freq、Duty、Count。
- 状态栏：Source、Protocol、状态、Fs、FPS、Blocks、Dropped、消息。
- 应用标题、About 对话框、打包脚本和发布文件名统一读取 `APP_VERSION`。
- 普通用户入口是 `dist\SimpleScopePC\SimpleScopePC.exe`、便携 zip 或 Inno 安装包；开发者入口仍支持 `tools\run_scope.bat` 和 `simplescope-pc`。

## 设置持久化

设置保存在用户目录，不写回源码文件。Windows 默认路径：

```text
%APPDATA%\SimpleScopePC\settings.json
```

配置缺失或损坏时自动恢复默认值。

日志默认写入：

```text
%APPDATA%\SimpleScopePC\logs\simplescope-pc.log
```

## 打包发布链路

```text
root pyproject.toml
  ↓ editable install / gui-script
simplescope-pc
  ↓ PyInstaller onedir
dist\SimpleScopePC\SimpleScopePC.exe
  ↓ Compress-Archive
dist\SimpleScopePC-0.9.4-win64-portable.zip
  ↓ Inno Setup
dist\installer\SimpleScopePC-0.9.4-Setup.exe
```

GitHub Actions 在 `v*` tag 上构建 Windows portable zip 并上传 Release 资产；安装包仍可由本机 Inno Setup 构建。

## 扩展路线

- CH2 和多通道 `Trace`。
- FFT / Spectrum Analyzer。
- Logic Analyzer。
- Protocol Decoder。
- USB CDC。
- 更高采样率 MCU。
- 模拟前端量程切换。
- 签名、崩溃上报和更完整的安装包 CI。
