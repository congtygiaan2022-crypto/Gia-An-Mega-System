@echo off
cd /d "%~dp0"
pm2 start main.py --name "Gams Fb Copyright Checker" --interpreter python
pause
