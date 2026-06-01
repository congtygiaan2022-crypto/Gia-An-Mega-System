@echo off
cd /d "%~dp0"
pm2 start main.py --name "Gams Tool Auto Bcgame" --interpreter python
pause
