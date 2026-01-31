@echo off
setlocal

set "script_dir=%~dp0"
set "base_dir=%CD%\"
REM set "base_dir=%script_dir%"

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

set "venv_dir=%base_dir%venv"
echo Using venv directory: %venv_dir%

if not exist "%venv_dir%" (
    echo No venv directory found, run init.bat to initialize it...
    pause
    exit /b 1
)

echo Activating venv
call "%venv_dir%\Scripts\activate.bat"
if %errorlevel% neq 0 exit /b %errorlevel%

echo Starting up
start pythonw.exe "%script_dir%main.py"

endlocal
