@echo off
setlocal

set "ROOT=%~dp0.."
set "PY=%ROOT%\.venv\python.exe"
set "DIST=%ROOT%\dist"
set "APPDIR=%DIST%\SimpleScopePC"
set "BUILD_TMP=%ROOT%\.tmp"
set "VERSION_FILE=%BUILD_TMP%\simplescope_zip_version.txt"

if not exist "%PY%" set "PY=python"

if not exist "%APPDIR%\SimpleScopePC.exe" (
  echo Missing portable app. Run tools\build_portable.bat first.
  exit /b 1
)

if not exist "%BUILD_TMP%" mkdir "%BUILD_TMP%"

"%PY%" -c "import sys; sys.path.insert(0, r'%ROOT%\pc_app'); from scope_app.version import APP_VERSION; print(APP_VERSION)" > "%VERSION_FILE%"
if errorlevel 1 exit /b 1
set /p VERSION=<"%VERSION_FILE%"
if "%VERSION%"=="" (
  echo Could not read APP_VERSION.
  exit /b 1
)
set "ZIP=%DIST%\SimpleScopePC-%VERSION%-win64-portable.zip"

if exist "%ZIP%" del "%ZIP%"

powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -Path '%APPDIR%\*' -DestinationPath '%ZIP%' -Force"
if errorlevel 1 exit /b 1

echo Created %ZIP%
exit /b 0
