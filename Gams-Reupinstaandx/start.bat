@echo off
title Gams Reup Insta and X v1.0.0
echo Dang khoi dong Web Dashboard...
echo Vui long doi giay lat...
call .\venv\Scripts\activate.bat
start http://127.0.0.1:5001
python app.py
pause
