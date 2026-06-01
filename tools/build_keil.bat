@echo off
setlocal
set "UVISION=D:\Work\Keil5\UV4\uVision.com"
set "PROJECT=%~dp0..\SimpleOscilloscope.uvprojx"
set "LOG=%~dp0..\build_keil.log"

if not exist "%UVISION%" (
  echo Keil command line entry not found: %UVISION%
  exit /b 1
)

pushd "%~dp0.."
"%UVISION%" -b SimpleOscilloscope.uvprojx -t Firmware -o build_keil.log
set "ERR=%ERRORLEVEL%"
popd
exit /b %ERR%
