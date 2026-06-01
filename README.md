# SimpleOscilloscope

简易示波器/信号源项目，目标硬件为 `STM32F103C8T6` 最小系统板。仓库包含：

- Keil 固件工程：STM32 通过串口持续输出模拟波形采样帧，并在 `PA8/TIM1_CH1` 输出同一波形的 PWM 占空比版本。
- Python 上位机：`PySide6 + PyQtGraph + NumPy + pySerial` 模块化桌面应用，通过 CH340 串口、TCP 模拟器或 `fake://` 本地假数据源读取采样帧并绘制波形。
- 下位机模拟器：用同一协议模拟单片机，方便没有板子时调试上位机。

## 快速开始

编译固件：

```bat
tools\build_keil.bat
```

生成文件：

```text
Objects\SimpleOscilloscope.hex
```

烧录到 ST-Link 连接的板子：

```bat
tools\flash_stlink.bat
```

启动模拟器：

```bat
python simulator\mcu_simulator.py
```

初始化上位机本地 Python 3.11 环境：

```bat
tools\setup_pc_env.bat
```

启动上位机连接内置假数据源：

```bat
tools\run_scope.bat --source fake://sine --connect
```

启动上位机连接 TCP 模拟器：

```bat
tools\run_scope.bat --source tcp://127.0.0.1:8765 --connect
```

启动上位机连接 CH340 串口：

```bat
tools\run_scope.bat --source COM14 --baud 115200 --connect
```

兼容入口仍保留：

```bat
.venv\python.exe pc_app\simple_scope.py --source COM14 --baud 115200
```

## 固件结构

- `user/inc`：项目头文件。
- `user/src`：主程序、串口协议、波形发生器、板级初始化。
- `RTE/Device/STM32F103C8`：Keil/CMSIS 启动文件和系统时钟文件。
- `docs/protocol.md`：串口协议说明。

## 上位机结构

- `pc_app/scope_app/core`：采样模型、连接配置、NumPy 环形缓冲、单位格式化。
- `pc_app/scope_app/transport`：串口、TCP、`fake://` 本地数据源。
- `pc_app/scope_app/protocol`：当前 ASCII 协议解析、命令封装，以及后续二进制协议预留。
- `pc_app/scope_app/acquisition`：采集控制器、后台读取线程、接收统计。
- `pc_app/scope_app/processing`：测量、显示降采样、触发预留。
- `pc_app/scope_app/ui`：PySide6 主窗口、PyQtGraph 波形视图、控制面板、测量面板、状态栏。

运行测试：

```bat
.venv\python.exe -m pytest -q
```

## 当前硬件假设

- MCU：STM32F103C8T6。
- 调试/烧录：ST-Link，STM32CubeProgrammer CLI 路径为 `F:\AcademicHub\STMicroelectronics\stm32cubeprogrammer\bin\STM32_Programmer_CLI.exe`。
- 串口：固件第一版使用 `USART1 PA9/PA10 @ 115200`。如果最小系统板上的 CH340 实际接到 `USART2 PA2/PA3`，需要在 `user/src/board.c` 和 `user/src/uart.c` 切换引脚和外设。
