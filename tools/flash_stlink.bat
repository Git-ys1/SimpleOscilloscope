@echo off
setlocal
set "PROGRAMMER=F:\AcademicHub\STMicroelectronics\stm32cubeprogrammer\bin\STM32_Programmer_CLI.exe"
set "HEX=%~dp0..\Objects\SimpleOscilloscope.hex"

if not exist "%PROGRAMMER%" (
  echo STM32CubeProgrammer CLI not found: %PROGRAMMER%
  exit /b 1
)

if not exist "%HEX%" (
  echo HEX not found: %HEX%
  echo Run tools\build_keil.bat first.
  exit /b 1
)

"%PROGRAMMER%" -c port=SWD mode=UR reset=HWrst -w "%HEX%" -v -rst
