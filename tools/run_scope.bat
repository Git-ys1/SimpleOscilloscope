@echo off
setlocal
set "ROOT=%~dp0.."
set "PY=%ROOT%\.venv\python.exe"

if not exist "%PY%" (
  echo Missing local Python environment. Run tools\setup_pc_env.bat first.
  exit /b 1
)

pushd "%ROOT%\pc_app"
"%PY%" -m scope_app %*
set "ERR=%ERRORLEVEL%"
popd
exit /b %ERR%
