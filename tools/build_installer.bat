@echo off
setlocal

set "ROOT=%~dp0.."
set "PY=%ROOT%\.venv\python.exe"
set "ISCC="
set "BUILD_TMP=%ROOT%\.tmp"
set "VERSION_FILE=%BUILD_TMP%\simplescope_installer_version.txt"

if not exist "%PY%" set "PY=python"

if not exist "%BUILD_TMP%" mkdir "%BUILD_TMP%"

"%PY%" -c "import sys; sys.path.insert(0, r'%ROOT%\pc_app'); from scope_app.version import APP_VERSION; print(APP_VERSION)" > "%VERSION_FILE%"
if errorlevel 1 exit /b 1
set /p VERSION=<"%VERSION_FILE%"
if "%VERSION%"=="" (
  echo Could not read APP_VERSION.
  exit /b 1
)

if not exist "%ROOT%\dist\SimpleScopePC\SimpleScopePC.exe" (
  call "%ROOT%\tools\build_portable.bat"
  if errorlevel 1 exit /b 1
)

if not exist "%ROOT%\dist\installer" mkdir "%ROOT%\dist\installer"

where ISCC.exe >nul 2>nul
if not errorlevel 1 set "ISCC=ISCC.exe"
if "%ISCC%"=="" if exist "%ROOT%\.tools\Inno Setup 6\ISCC.exe" set "ISCC=%ROOT%\.tools\Inno Setup 6\ISCC.exe"
if "%ISCC%"=="" if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if "%ISCC%"=="" if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"

if "%ISCC%"=="" (
  echo ISCC.exe not found. Please install Inno Setup 6.
  echo Download: https://jrsoftware.org/isinfo.php
  exit /b 1
)

"%ISCC%" /DMyAppVersion=%VERSION% "%ROOT%\packaging\windows\SimpleScopePC.iss"
exit /b %ERRORLEVEL%
