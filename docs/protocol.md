# Simple Oscilloscope 串口协议

默认串口参数：`115200 8N1`。固件当前使用 `USART1 PA9/PA10`，如果 CH340 接在别的串口引脚，需要后续按实物接线调整固件。

## 上行数据

固件启动：

```text
BOOT,SimpleOscilloscope,0.7.0,STM32F103C8T6,115200
STATUS,SINE,5,1200,1650,100,RUN
FORMAT,BINARY
```

v0.7.0 起，固件默认使用二进制采样块。ASCII 样本帧仍可通过 `SET FORMAT ASCII` 切回，用于串口助手排查：

```text
OSC,<seq>,<time_ms>,<value_mv>,<wave>,<freq_hz>,<amp_mv>,<offset_mv>
```

示例：

```text
OSC,42,420,2301,SINE,5,1200,1650
```

## 下行命令

每条命令以 `\r\n` 或 `\n` 结尾。

```text
PING
ID?
STATUS
START
STOP
SET WAVE SINE
SET WAVE SQUARE
SET WAVE TRI
SET WAVE SAW
SET FREQ 10
SET AMP 1200
SET OFFSET 1650
SET RATE 100
SET FORMAT BINARY
SET FORMAT ASCII
```

固件 v0.7.0 的采样率命令会被限制在 `1..1000 Hz`。

## 高速二进制数据帧

v0.7.0 起，固件、TCP 模拟器、`fake://` 数据源和上位机默认使用“一帧多点”的二进制 DATA 帧。命令、`BOOT`、`STATUS`、`FORMAT`、`OK`、`ERR` 仍走 ASCII 行，方便人工调试。

帧结构，小端序：

| 字段 | 字节数 | 说明 |
| --- | ---: | --- |
| Sync | 2 | 固定 `0xA5 0x5A` |
| Version | 1 | 当前建议 `1` |
| Type | 1 | `0x01` 表示 DATA |
| Sequence | 4 | 数据块序号 |
| SampleRateHz | 4 | 采样率 |
| ChannelCount | 1 | 通道数 |
| PointCount | 2 | 每通道点数 |
| Payload | N | `uint16` ADC 原始值数组，按通道排列 |
| CRC16 | 2 | 对 CRC 前所有字节计算 CCITT-FALSE |

上位机会把 `uint16 ADC` 按 `0..4095 -> 0..3300mV` 转换并写入波形环形缓冲。
