@echo off
setlocal

set "ROOT=%~dp0.."
set "PY=%ROOT%\.venv\python.exe"
set "BUILD_TMP=%ROOT%\.tmp"
set "EXTRA_BINARIES="

if not exist "%PY%" set "PY=python"

pushd "%ROOT%"

if not exist "%BUILD_TMP%" mkdir "%BUILD_TMP%"

if exist "%ROOT%\.venv\Library\bin\ffi-8.dll" set "EXTRA_BINARIES=%EXTRA_BINARIES% --add-binary .venv\Library\bin\ffi-8.dll;."
if exist "%ROOT%\.venv\Library\bin\libcrypto-3-x64.dll" set "EXTRA_BINARIES=%EXTRA_BINARIES% --add-binary .venv\Library\bin\libcrypto-3-x64.dll;."
if exist "%ROOT%\.venv\Library\bin\libssl-3-x64.dll" set "EXTRA_BINARIES=%EXTRA_BINARIES% --add-binary .venv\Library\bin\libssl-3-x64.dll;."
if exist "%ROOT%\.venv\Library\bin\libexpat.dll" set "EXTRA_BINARIES=%EXTRA_BINARIES% --add-binary .venv\Library\bin\libexpat.dll;."

"%PY%" -c "import os, pathlib, runpy, sys, tempfile; tmp = pathlib.Path('.tmp').resolve(); tmp.mkdir(exist_ok=True); os.environ['TMPDIR'] = str(tmp); os.environ['TMP'] = str(tmp); os.environ['TEMP'] = str(tmp); tempfile.tempdir = str(tmp); sys.argv = ['pip', 'install', '-e', '.[dev]']; runpy.run_module('pip', run_name='__main__')"
if errorlevel 1 (
  popd
  exit /b 1
)

if exist build rmdir /s /q build
if exist dist\SimpleScopePC rmdir /s /q dist\SimpleScopePC

"%PY%" -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --windowed ^
  --onedir ^
  --name SimpleScopePC ^
  --paths pc_app ^
  --icon packaging\assets\SimpleScopePC.ico ^
  --add-data "README.md;." ^
  --add-data "docs;docs" ^
  --add-data "packaging\assets;packaging\assets" ^
  %EXTRA_BINARIES% ^
  pc_app\simple_scope.py

if errorlevel 1 (
  popd
  exit /b 1
)

echo Portable app created: dist\SimpleScopePC\SimpleScopePC.exe
popd
exit /b 0
