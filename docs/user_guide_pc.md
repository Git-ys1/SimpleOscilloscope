# SimpleScope PC 用户指南

## 下载和安装

V0.9.1 起，普通用户优先使用发布页里的 Windows 包，不需要安装 Python。V0.9.3 起，示波器界面改为锁定画布的中文页签控制面板，默认支持 1 kHz 测试信号和 20 kSa/s 采样。V0.9.4 起，触发算法加入迟滞、线性插值和轻量帧保持，减少稳定波形左右漂移：

- `SimpleScopePC-0.9.4-win64-portable.zip`：便携版，解压后运行 `SimpleScopePC.exe`。
- `SimpleScopePC-0.9.4-Setup.exe`：安装版，按向导安装后从开始菜单启动。

源码仓库仍保留开发者入口，适合调试、二次开发和本地验证。

## 开发者安装依赖

从仓库根目录执行：

```bat
tools\setup_pc_env.bat
.venv\python.exe -m pip install -e .[dev]
```

## 启动 Demo

没有硬件时可以直接运行：

```bat
tools\run_scope.bat --source fake://sine --connect
```

也可以使用安装后的命令行入口：

```bat
simplescope-pc --source fake://sine --connect
```

软件打开后也可以点击顶部工具栏的 `演示`，它会自动切换到 `fake://sine` 并连接。当前支持：

- `fake://sine`
- `fake://square`
- `fake://triangle`
- `fake://noise`
- `fake://mixed`

## 连接真机

1. 用 ST-Link 烧录固件。
2. 用 CH340 连接 `USART1 PA9/PA10`。
3. 启动上位机：

```bat
tools\run_scope.bat --source COM14 --baud 921600 --connect
```

或：

```bat
simplescope-pc --source COM14 --baud 921600 --connect
```

如果串口号不是 `COM14`，在右侧 `连接` 页签里点击 `扫描串口` 后选择对应 COM 口。

## 连接 TCP 模拟器

另开一个终端启动模拟器：

```bat
python simulator\mcu_simulator.py
```

再启动上位机：

```bat
tools\run_scope.bat --source tcp://127.0.0.1:8765 --connect
```

便携版或安装版也可以在窗口右侧 `连接` 页签里把数据源改为 `tcp://127.0.0.1:8765` 后连接。

## 打包命令

维护者在仓库根目录执行：

```bat
tools\build_portable.bat
tools\package_portable_zip.bat
tools\build_installer.bat
```

产物默认输出到：

- `dist\SimpleScopePC\SimpleScopePC.exe`
- `dist\SimpleScopePC-0.9.4-win64-portable.zip`
- `dist\installer\SimpleScopePC-0.9.4-Setup.exe`

安装包构建需要本机已安装 Inno Setup。

## 看波形

中央区域是示波器屏幕：

- 左上角显示 CH1、Volt/div、耦合和探头倍率。
- 右上角显示 `运行` / `停止` / `等待触发` / `已触发`。
- 底部显示时基、采样率和记录长度。
- 画布默认锁定，鼠标拖拽或滚轮不会拉动画面；读数是固定悬浮层，不随波形坐标移动。
- 触发显示使用迟滞和过电平插值，稳定周期波形会尽量锁在同一水平位置。
- 没有连接时会显示数据源选择和安全提示。

## 调整显示

在 `显示` 页签里调整：

- `Time/div`：水平时基。
- `Volt/div`：垂直档位。
- `水平位置`：移动触发记录。
- `垂直中心`：设置波形中心。
- `自动设置`：自动调整时基、垂直档位和触发电平。
- `网格`：显示或隐藏网格。

## 使用触发

在 `触发` 页签里设置：

- `模式`：Auto、Normal、Single。
- `边沿`：上升沿或下降沿。
- `数据源`：当前为 CH1。
- `电平 mV`：触发电平。
- `预触发`：触发点在屏幕中的位置，默认 50%。

`Normal` 模式未触发时会显示 `等待触发`，触发后显示 `已触发`。

## 测量

底部测量栏和右侧 `测量` 页签显示：

- Vmax / Vmin / Vpp / Vavg
- Vrms DC / Vrms AC
- 频率 / 周期 / 占空比
- 采样点数

AC RMS 会先去掉平均值，避免被 1.65V 偏置污染。

## 导出 CSV

点击顶部 `导出` 或菜单 `文件 -> 导出 CSV`，选择保存路径即可导出当前环形缓冲里的波形数据。

## 安全接线

当前硬件默认假设：

- MCU：STM32F103C8T6
- ADC 输入：PA0 / ADC1_IN0
- 串口：USART1 PA9/PA10，经 CH340 连接电脑
- 烧录调试：ST-Link SWD，PA13/PA14
- ADC 安全输入范围：0V ~ 3.3V

严禁：

- 直接测市电
- 输入负电压
- 输入超过 3.3V 的电压
- 未加分压/保护时测高压电路

如果要测超过 3.3V 或交流双极性信号，需要模拟前端：分压、偏置、限流、钳位保护、AC/DC 耦合。
