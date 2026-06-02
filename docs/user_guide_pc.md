# SimpleScope PC 用户指南

## 安装依赖

从仓库根目录执行：

```bat
tools\setup_pc_env.bat
```

## 启动 Demo

没有硬件时可以直接运行：

```bat
tools\run_scope.bat --source fake://sine --connect
```

软件打开后也可以点击顶部工具栏的 `Demo`，它会自动切换到 `fake://sine` 并连接。当前支持：

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
tools\run_scope.bat --source COM14 --baud 115200 --connect
```

如果串口号不是 `COM14`，在右侧 `Connection 连接` 面板里点击 `Scan Ports` 后选择对应 COM 口。

## 连接 TCP 模拟器

另开一个终端启动模拟器：

```bat
python simulator\mcu_simulator.py
```

再启动上位机：

```bat
tools\run_scope.bat --source tcp://127.0.0.1:8765 --connect
```

## 看波形

中央区域是示波器屏幕：

- 左上角显示 CH1、Volt/div、耦合和探头倍率。
- 右上角显示 `RUN` / `STOP` / `WAIT` / `TRIG`。
- 底部显示 time/div、采样率和记录长度。
- 没有连接时会显示数据源选择和安全提示。

## 调整显示

在 `Display 显示` 面板里调整：

- `Time/div`：水平时基。
- `Volt/div`：垂直档位。
- `Horizontal`：水平位置。
- `Vertical`：垂直中心。
- `AutoSet`：自动调整垂直量程。
- `Grid`：显示或隐藏网格。

## 使用触发

在 `Trigger 触发` 面板里设置：

- `Mode`：Auto、Normal、Single。
- `Edge`：Rising 或 Falling。
- `Source`：当前为 CH1。
- `Level mV`：触发电平。
- `Pre-trigger`：触发点在屏幕中的位置。

`Normal` 模式未触发时会显示 `WAIT`，触发后显示 `TRIG`。

## 测量

底部测量栏和右侧 `Measurements 测量` 面板显示：

- Vmax / Vmin / Vpp / Vavg
- Vrms DC / Vrms AC
- Frequency / Period / Duty Cycle
- Sample Count

AC RMS 会先去掉平均值，避免被 1.65V 偏置污染。

## 导出 CSV

点击顶部 `Export` 或菜单 `File -> Export CSV`，选择保存路径即可导出当前环形缓冲里的波形数据。

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
