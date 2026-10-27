@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp002_INSTALL_LEROBOT.ps1"
echo.
pause
