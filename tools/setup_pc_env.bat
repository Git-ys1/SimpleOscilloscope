@echo off
setlocal
set "ROOT=%~dp0.."
set "ENV=%ROOT%\.venv"

if not exist "%ENV%\python.exe" (
  conda create -p "%ENV%" python=3.11 -y -c conda-forge
  if errorlevel 1 exit /b 1
)

set HTTP_PROXY=
set HTTPS_PROXY=
set NO_PROXY=*
"%ENV%\python.exe" -m pip install -r "%ROOT%\requirements.txt"
