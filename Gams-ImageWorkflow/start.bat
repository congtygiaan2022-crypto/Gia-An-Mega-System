@echo off
title Gams Image Workflow v1.0.0
echo Dang khoi dong Web Dashboard...
echo Vui long doi giay lat...
call .\venv\Scripts\activate.bat
start http://127.0.0.1:5000
python app.py
pause
