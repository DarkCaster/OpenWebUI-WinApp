@echo off
set ScriptRoot=%~dp0

PowerShell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='silentlycontinue'; Clear-Content -Path '%ScriptRoot%\download-ffmpeg.ps1' -Stream 'Zone.Identifier'"
PowerShell.exe -NoProfile -ExecutionPolicy Bypass -Command "& '%ScriptRoot%\download-ffmpeg.ps1' %*"
IF %ERRORLEVEL% NEQ 0 EXIT /B %ERRORLEVEL%
