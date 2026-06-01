# Simple Oscilloscope 串口协议

默认串口参数：`115200 8N1`。固件当前使用 `USART1 PA9/PA10`，如果 CH340 接在别的串口引脚，需要后续按实物接线调整固件。

## 上行数据

固件启动：

```text
BOOT,SimpleOscilloscope,0.1.0,STM32F103C8T6,115200
STATUS,SINE,5,1200,1650,100,RUN
```

样本帧：

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
```
