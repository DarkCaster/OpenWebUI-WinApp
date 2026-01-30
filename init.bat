@echo off
setlocal enabledelayedexpansion

set "script_dir=%~dp0"
set "base_dir=%CD%\"
REM set "base_dir=%script_dir%"

REM This value will be used with UV to install corresponding python version, may be overriden by params.bat
set "USE_PYTHON_VER=3.11"

if exist "%script_dir%params.bat" (
    echo Loading %script_dir%params.bat
    call "%script_dir%params.bat"
)

if exist "%base_dir%params.bat" (
    echo Loading %base_dir%params.bat
    call "%base_dir%params.bat"
)

set "py_dir=%base_dir%py_dist"
echo Using Python base directory: %py_dir%

echo Installing and upgrading python distribution and venv using UV
set "UV_COMPILE_BYTECODE=0"
set "UV_PYTHON_INSTALL_REGISTRY=0"
set "UV_PYTHON_BIN_DIR=%py_dir%\python_bin"
set "UV_PYTHON_INSTALL_DIR=%py_dir%\dists"
set "UV_TOOL_BIN_DIR=%py_dir%\tool_bin"
set "UV_TOOL_DIR=%py_dir%\tool"
set "UV_CACHE_DIR=%py_dir%\cache"
set "UV_LINK_MODE=copy"

uv python install --upgrade %USE_PYTHON_VER%
if %errorlevel% neq 0 exit /b %errorlevel%

set "venv_dir=%base_dir%venv"
echo Using venv directory: %venv_dir%

if not exist "%venv_dir%" (
    uv venv "%venv_dir%"
    if %errorlevel% neq 0 exit /b %errorlevel%
)

echo Activating venv
call "%venv_dir%\Scripts\activate.bat"

echo Installing package-requirements
uv pip install --upgrade -r "%script_dir%requirements.txt"
if %errorlevel% neq 0 exit /b %errorlevel%

echo Cleaning up cache
RMDIR /S /Q "%py_dir%\cache"

echo Install complete
endlocal
pause
