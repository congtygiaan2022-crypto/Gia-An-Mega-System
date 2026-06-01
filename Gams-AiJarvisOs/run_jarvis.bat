@echo off
cd /d "%~dp0"
title Jarvis_Dashboard
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
:start
echo Starting Jarvis v2 Web Dashboard...
python main.py --web
if %errorlevel% equ 99 (
    echo Restarting system...
    goto start
)
pause
